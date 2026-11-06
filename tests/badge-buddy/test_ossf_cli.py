"""Tests for the shared OpenSSF plugin command boundary."""

from __future__ import annotations

import contextlib
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, unquote, urlparse


REPOSITORY_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "badge-buddy"
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import ossf  # noqa: E402
from ossf_review.criteria import CriteriaCatalog  # noqa: E402
from ossf_review.storage import DataStore  # noqa: E402
from ossf_review.submission import (  # noqa: E402
    build_fill_script,
    build_proposal_urls,
    validate_base_url,
    wording_only_criteria,
)
from spec_pins import EXPECTED_SECTION_TOTALS  # noqa: E402


class MissingProjectClient:
    def lookup_project_id(self, remote: str) -> None:
        self.remote = remote
        return None


class PublicProjectClient:
    """Serve a canned public project document for synchronization."""

    def __init__(self, document: dict[str, object]) -> None:
        document.setdefault("repo_url", "https://github.com/example/review")
        self.document = document

    def lookup_project_id(self, remote: str) -> str:
        return "31"

    def fetch_project(self, project_id: object) -> dict[str, object]:
        return dict(self.document)


class OssfCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.repository = self.root / "repo"
        self.data_dir = self.root / "plugin-data"
        subprocess.run(
            ["git", "init", "-q", str(self.repository)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repository),
                "remote",
                "add",
                "origin",
                "https://github.com/example/review.git",
            ],
            check=True,
            capture_output=True,
        )

    def run_command(
        self,
        *arguments: str,
        client_factory=MissingProjectClient,
        stdin: str | None = None,
        browser_open=None,
    ) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        input_stream = StringIO(stdin) if stdin is not None else None
        stdin_context = (
            patch.object(sys, "stdin", input_stream)
            if input_stream is not None
            else contextlib.nullcontext()
        )
        with (
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
            stdin_context,
        ):
            result = ossf.main(
                [
                    "--repo",
                    str(self.repository),
                    "--data-dir",
                    str(self.data_dir),
                    *arguments,
                ],
                client_factory=client_factory,
                **({"browser_open": browser_open} if browser_open is not None else {}),
            )
        return result, stdout.getvalue(), stderr.getvalue()

    def register_verified_project(self) -> None:
        """Seed the association established by a prior successful online status."""
        DataStore(self.data_dir).register_project("31", "github.com/example/review")

    def test_session_commands_use_saved_snapshot_without_network(self) -> None:
        document = {
            "repo_url": "https://github.com/example/review",
            "description_good_status": "Met",
            "description_good_justification": "Original description.",
        }
        client = PublicProjectClient(document)
        with patch.object(client, "fetch_project", wraps=client.fetch_project) as fetch:
            code, stdout, error = self.run_command("status", client_factory=lambda: client)
        self.assertEqual((0, ""), (code, error))
        fetch.assert_called_once_with("31")
        initial = json.loads(stdout)
        baseline = initial["sources"]["public_snapshot"]
        self.assertEqual("live", baseline["source"])
        self.assertIsNotNone(baseline["fetched_at"])
        updates = {"description_good_justification": "Revised description."}
        commands = (
            ("apply", "--section", "passing", "--json", json.dumps(updates)),
            ("review", "--no-browser"),
            ("export", "--output", str(self.root / "export.json")),
            ("propose", "--section", "passing"),
            ("fill-script", "--section", "passing", "--output", str(self.root / "fill.js")),
        )
        def no_client():
            self.fail("Only status should create a network client")
        # Each command constructs a new DataStore, as separate CLI processes do.
        for command in commands:
            with self.subTest(command=command[0]):
                code, stdout, error = self.run_command(*command, client_factory=no_client)
                self.assertEqual((0, ""), (code, error))
                payload = json.loads(stdout)
                self.assertEqual([], payload["conflicts"])
                if command[0] == "apply":
                    cached = payload["sources"]["public_snapshot"]
                elif command[0] in ("propose", "fill-script"):
                    cached = payload["public_snapshot"]
                else:
                    continue
                self.assertEqual({**baseline, "source": "cached"}, cached)
        self.assertEqual(["description_good"], payload["criteria"])
        self.assertEqual("Revised description.", json.loads(
            (self.root / "export.json").read_text()
        )["description_good_justification"])

        document["description_good_justification"] = "Updated on the website."
        code, stdout, error = self.run_command("status", client_factory=lambda: client)
        self.assertEqual((0, ""), (code, error))
        refreshed = json.loads(stdout)
        self.assertEqual("Revised description.", refreshed["assessment"][
            "description_good_justification"
        ])
        self.assertEqual("Updated on the website.", refreshed["conflicts"][0]["incoming"])
        self.assertEqual("live", refreshed["sources"]["public_snapshot"]["source"])
        snapshot = DataStore(self.data_dir).load_public_snapshot(
            "31", "https://github.com/example/review"
        )
        self.assertEqual(document, snapshot["document"])

    def test_local_registry_miss_requests_status_without_network(self) -> None:
        def no_client():
            self.fail("Local commands must not look up a project")
        code, stdout, error = self.run_command(
            "apply", "--section", "passing", "--json", "{}", client_factory=no_client,
        )
        self.assertEqual((3, ""), (code, error))
        payload = json.loads(stdout)
        self.assertEqual("registry_miss", payload["state"])
        self.assertIn("Run status", payload["next_step"])

    def test_explicit_offline_id_cannot_establish_a_repository_association(self) -> None:
        code, stdout, error = self.run_command("status", "--offline", "--project-id", "31")
        self.assertEqual((2, ""), (code, stdout))
        self.assertIn("run status online", error)
        self.assertIsNone(DataStore(self.data_dir).resolve_project_id("github.com/example/review"))
        self.assertEqual([], list(self.data_dir.rglob(".bestpractices.json")))

    def test_local_commands_cannot_rebind_a_verified_project(self) -> None:
        self.register_verified_project()
        store = DataStore(self.data_dir)
        store.register_project("32", "github.com/example/other")
        store.save_assessment("32", {"description_good_status": "Met"})
        before = {path: path.read_bytes() for path in self.data_dir.rglob("*.json")}
        output = self.root / "should-not-exist.json"
        commands = (
            ("status", "--offline"),
            ("apply", "--section", "passing", "--json", '{"description_good_status":"Unmet"}'),
            ("review", "--no-browser"),
            ("export", "--output", str(output)),
            ("propose", "--section", "passing"),
            ("fill-script", "--section", "passing", "--all", "--output", str(output)),
        )
        for command in commands:
            with self.subTest(command=command[0]):
                code, stdout, error = self.run_command(
                    *command, "--project-id", "32",
                    client_factory=lambda: self.fail("local commands must not access the network"),
                )
                self.assertEqual((2, ""), (code, stdout))
                self.assertIn("run status online", error)
                self.assertEqual(before, {
                    path: path.read_bytes() for path in self.data_dir.rglob("*.json")
                })
                self.assertFalse(output.exists())

    def test_status_is_machine_readable_and_does_not_expose_private_paths(self) -> None:
        self.register_verified_project()
        result, stdout, stderr = self.run_command(
            "status",
            "--project-id",
            "31",
            "--offline",
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("registered", payload["state"])
        self.assertEqual("31", payload["project"]["project_id"])
        self.assertEqual(
            EXPECTED_SECTION_TOTALS["passing"],
            payload["sections"]["passing"]["total"],
        )
        self.assertEqual(
            EXPECTED_SECTION_TOTALS["passing"],
            payload["sections"]["passing"]["unknown"],
        )
        self.assertEqual({}, payload["assessment"])
        self.assertNotIn(str(self.data_dir), stdout)
        self.assertNotIn(str(self.repository), stdout)

    def test_environment_paths_support_installed_plugin_invocation(self) -> None:
        self.register_verified_project()
        with patch.dict(
            os.environ,
            {
                "CLAUDE_PLUGIN_DATA": str(self.data_dir),
                "CLAUDE_PROJECT_DIR": str(self.repository),
            },
            clear=False,
        ):
            stdout = StringIO()
            with contextlib.redirect_stdout(stdout):
                result = ossf.main(["status", "--project-id", "31", "--offline"])

        self.assertEqual(0, result)
        self.assertEqual("31", json.loads(stdout.getvalue())["project"]["project_id"])

    def test_missing_plugin_data_fails_instead_of_creating_a_second_store(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            stderr = StringIO()
            with contextlib.redirect_stderr(stderr):
                result = ossf.main(
                    [
                        "--repo",
                        str(self.repository),
                        "status",
                        "--project-id",
                        "31",
                        "--offline",
                    ]
                )

        self.assertEqual(2, result)
        self.assertIn("CLAUDE_PLUGIN_DATA is unavailable", stderr.getvalue())

    def test_registry_miss_reports_registration_without_creating_a_sidecar(
        self,
    ) -> None:
        client = MissingProjectClient()
        result, stdout, stderr = self.run_command(
            "status",
            client_factory=lambda: client,
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("registration_required", payload["state"])
        self.assertEqual(
            "github.com/example/review",
            payload["project"]["remote"],
        )
        self.assertEqual(ossf.REGISTRATION_URL, payload["registration_url"])
        self.assertFalse((self.data_dir / "unregistered").exists())

    def test_offline_registry_miss_is_not_claimed_as_absent_registration(self) -> None:
        result, stdout, _stderr = self.run_command("status", "--offline")

        self.assertEqual(0, result)
        self.assertEqual("registry_miss", json.loads(stdout)["state"])

    def test_unregistered_sidecar_requires_explicit_command_opt_in(self) -> None:
        result, stdout, stderr = self.run_command(
            "status",
            "--allow-unregistered",
            client_factory=MissingProjectClient,
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("unregistered", payload["state"])
        self.assertIsNone(payload["project"]["project_id"])
        self.assertTrue((self.data_dir / "unregistered").is_dir())

    def test_local_handoff_conflicts_are_resolved_by_explicit_apply(self) -> None:
        draft_answer = {
            "description_good_status": "Met",
            "description_good_justification": "Local description evidence.",
        }
        for chosen_status, include_justification in (("Met", False), ("Met", True), ("Unmet", True)):
            with self.subTest(chosen_status=chosen_status, include_justification=include_justification):
                store = DataStore(self.data_dir)
                store.create_unregistered(self.repository, remote="github.com/example/review")
                local_id = store.unregistered_identifier(self.repository)
                store.save_assessment(local_id, {
                    **draft_answer,
                    "contribution_status": "?",
                    "contribution_justification": "Unfinished contribution notes.",
                })
                store.register_project("31", "github.com/example/review")
                store.save_assessment("31", {"description_good_status": "Unmet"})
                code, stdout, stderr = self.run_command("status", "--offline")
                self.assertEqual(0, code, stderr)
                result = json.loads(stdout)
                self.assertEqual("Unmet", result["assessment"]["description_good_status"])
                self.assertNotIn("description_good_justification", result["assessment"])
                self.assertEqual("Unfinished contribution notes.",
                                 result["assessment"]["contribution_justification"])
                self.assertEqual(draft_answer, store.load_assessment(local_id))
                self.assertEqual({
                    ("description_good_status", "Unmet", "Met", "local_draft"),
                    ("description_good_justification", None, "Local description evidence.", "local_draft"),
                }, {(c["field"], c["preserved"], c["incoming"], c["source"])
                    for c in result["conflicts"]})
                selected = {"description_good_status": chosen_status}
                if include_justification:
                    selected["description_good_justification"] = "User-selected explanation."
                code, stdout, stderr = self.run_command(
                    "apply", "--section", "passing", "--offline", "--json", json.dumps(selected),
                )
                self.assertEqual(0, code, stderr)
                self.assertEqual([], json.loads(stdout)["conflicts"])
                self.assertIsNone(store.load_unregistered(self.repository))
                self.assertEqual({}, store.load_assessment(local_id))
                code, stdout, stderr = self.run_command("status", "--offline")
                self.assertEqual(0, code, stderr)
                result = json.loads(stdout)
                self.assertEqual([], result["conflicts"])
                for field, value in selected.items():
                    self.assertEqual(value, result["assessment"][field])

        # When statuses agree, choosing the registered justification alone
        # resolves the disagreement; repeating the status is unnecessary.
        store.create_unregistered(self.repository, remote="github.com/example/review")
        local_id = store.unregistered_identifier(self.repository)
        store.save_assessment(local_id, {
            "description_good_status": "Unmet",
            "description_good_justification": "Different local explanation.",
        })
        code, stdout, stderr = self.run_command(
            "apply", "--section", "passing", "--offline", "--json",
            json.dumps({"description_good_justification": "User-selected explanation."}),
        )
        self.assertEqual(0, code, stderr)
        self.assertEqual([], json.loads(stdout)["conflicts"])
        self.assertIsNone(store.load_unregistered(self.repository))
        self.assertEqual({}, store.load_assessment(local_id))

    def test_selected_file_drives_updates_and_outputs_without_a_private_answer_copy(self) -> None:
        repository_file = self.repository / ".bestpractices.json"
        original = {"description_good_status": "Unmet", "interact_status": "N/A"}
        repository_file.write_text(json.dumps(original))
        repository_file.chmod(0o644)
        original_bytes = repository_file.read_bytes()
        working = self.root / "working.json"
        working.write_bytes(original_bytes)
        prefix = ("--assessment-file", str(working))
        code, _, error = self.run_command(*prefix, "status", "--allow-unregistered", "--offline")
        self.assertEqual((0, ""), (code, error))
        self.assertEqual([], list(self.data_dir.rglob(".bestpractices.json")))
        code, _, error = self.run_command(
            *prefix, "status", "--project-id", "31",
            client_factory=lambda: PublicProjectClient({}),
        )
        self.assertEqual((0, ""), (code, error))
        code, stdout, error = self.run_command(
            *prefix, "review", "--section", "passing", "--project-id", "31",
            "--view", "all", "--offline", "--no-browser",
        )
        self.assertEqual((0, ""), (code, error))
        board_url = urlparse(json.loads(stdout)["url"])
        self.assertEqual("view=all", board_url.fragment)
        board_path = Path(unquote(board_url.path))
        self.addCleanup(board_path.unlink, missing_ok=True)
        self.assertIn('"description_good":{"status":"Unmet"', board_path.read_text())
        self.assertEqual(original_bytes, repository_file.read_bytes())
        self.assertEqual([], list(self.data_dir.rglob(".bestpractices.json")))
        code, stdout, error = self.run_command(
            *prefix, "apply", "--section", "passing", "--offline", "--json",
            json.dumps({"description_good_status": "Met"}),
        )
        self.assertEqual((0, ""), (code, error))
        expected = {**original, "description_good_status": "Met"}
        self.assertEqual(expected, json.loads(stdout)["assessment"])
        self.assertEqual(expected, json.loads(working.read_text()))
        self.assertIn('"description_good":{"status":"Met"', board_path.read_text())

        exported = self.root / "export.json"
        script = self.root / "fill.js"
        for command in (("status",), ("export", "--output", str(exported)),
                        ("propose", "--section", "passing"),
                        ("fill-script", "--section", "passing", "--all", "--output", str(script))):
            with self.subTest(command=command[0]):
                code, stdout, error = self.run_command(*prefix, *command, "--offline")
                self.assertEqual((0, ""), (code, error))
                payload = json.loads(stdout)
                if command[0] == "status":
                    self.assertEqual(expected, payload["assessment"])
                elif command[0] == "propose":
                    query = parse_qs(urlparse(payload["urls"][0]).query)
                    self.assertEqual(["Met"], query["description_good_status"])
        self.assertEqual(expected, json.loads(exported.read_text()))
        answers, _ = json.JSONDecoder().raw_decode(script.read_text().split("const answers = ", 1)[1])
        self.assertEqual("Met", answers["description_good"]["status"])
        self.assertEqual(original_bytes, repository_file.read_bytes())
        self.assertEqual([], list(self.data_dir.rglob(".bestpractices.json")))

        # Supplying the repository path explicitly supports authorized direct edits.
        code, _, error = self.run_command(
            "--assessment-file", str(repository_file), "apply", "--section", "passing",
            "--offline", "--json", json.dumps({"description_good_status": "Met"}),
        )
        self.assertEqual((0, ""), (code, error))
        self.assertEqual(expected, json.loads(repository_file.read_text()))
        self.assertEqual(0o644, repository_file.stat().st_mode & 0o777)
        self.assertEqual([], list(self.data_dir.rglob(".bestpractices.json")))

    def test_apply_reads_stdin_and_normalizes_baseline_display_fields(self) -> None:
        self.register_verified_project()
        result, stdout, stderr = self.run_command(
            "apply",
            "--section",
            "baseline-1",
            "--project-id",
            "31",
            "--offline",
            "--input",
            "-",
            stdin=json.dumps({"OSPS-AC-01.01_status": "Unmet"}),
        )

        assessment = json.loads(stdout)["assessment"]
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("Unmet", assessment["osps_ac_01_01_status"])
        self.assertNotIn("OSPS-AC-01.01_status", assessment)

    def test_apply_rejects_unknown_fields_and_missing_required_evidence(self) -> None:
        self.register_verified_project()
        result, _stdout, stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps({"invented_status": "Met"}),
        )
        self.assertEqual(2, result)
        self.assertIn("unknown assessment field", stderr)

        result, _stdout, stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps({"contribution_status": "Met"}),
        )
        self.assertEqual(2, result)
        self.assertIn("requires a public evidence URL", stderr)

        result, stdout, stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "contribution_status": "Met",
                    "contribution_justification": "https://example.com/contributing",
                }
            ),
        )
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("Met", json.loads(stdout)["assessment"]["contribution_status"])

    def test_required_evidence_matches_upstream_for_apply_and_status(self) -> None:
        # BadgeApp project.rb: justification_good? and contains_url?. Exercise
        # real commands, including insufficient evidence loaded from storage.
        text_cases = (
            ("", False),
            ("yes", False),
            ("abcd", False),
            ("abcde", True),
            ("\u00e9\u00e9\u00e9\u00e9", False),
            ("\u00e9\u00e9\u00e9\u00e9\u00e9", True),
            ("// Pending confirmation", False),
            ("//note", True),  # Only the exact '// ' prefix is a comment.
            ("Tool runs before release.", True),
        )
        url_cases = (
            ("https://", False),
            ("https://localhost/guide", False),
            ("https://example.", False),
            ("// https://example.com/guide", False),
            ("See https://example.com/guide.", True),
            ("<https://example.com/guide>", True),
            ("[guide](http://example.com/guide)", True),
        )
        store = DataStore(self.data_dir)
        store.register_project("31", "github.com/example/review")
        for section, criterion, status, cases in (
            ("passing", "static_analysis", "Met", text_cases),
            ("gold", "dynamic_analysis", "N/A", text_cases),
            ("passing", "contribution", "Met", url_cases),
            ("passing", "description_good", "Met", (("yes", True),)),
            ("passing", "static_analysis", "Unmet", (("", True),)),
        ):
            for justification, sufficient in cases:
                with self.subTest(criterion=criterion, status=status, text=justification):
                    assessment = {
                        f"{criterion}_status": status,
                        f"{criterion}_justification": justification,
                    }
                    store.save_assessment("31", assessment)
                    code, stdout, stderr = self.run_command("status", "--offline")
                    self.assertEqual(0, code, stderr)
                    self.assertEqual(
                        0 if sufficient else 1,
                        json.loads(stdout)["sections"][section]["evidence_gaps"],
                    )

                    store.save_assessment("31", {})
                    code, stdout, stderr = self.run_command(
                        "apply", "--section", section, "--offline",
                        "--json", json.dumps(assessment),
                    )
                    self.assertEqual(0 if sufficient else 2, code, stderr)
                    self.assertEqual(
                        assessment if sufficient else {}, store.load_assessment("31")
                    )

    def test_apply_validates_repeated_fields_against_the_selected_section(self) -> None:
        self.register_verified_project()
        result, stdout, stderr = self.run_command(
            "apply",
            "--section",
            "gold",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "dynamic_analysis_status": "N/A",
                    "dynamic_analysis_justification": "No major production releases.",
                }
            ),
        )

        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("N/A", json.loads(stdout)["assessment"]["dynamic_analysis_status"])

        result, _stdout, stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps({"dynamic_analysis_status": "N/A"}),
        )

        self.assertEqual(2, result)
        self.assertIn("does not allow N/A", stderr)

        result, stdout, stderr = self.run_command(
            "apply",
            "--section",
            "silver",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "hardening_status": "Met",
                    "hardening_justification": "Confirmed hardening mechanisms.",
                }
            ),
        )

        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("Met", json.loads(stdout)["assessment"]["hardening_status"])

    def test_preview_revision_keeps_response_until_wording_is_approved(self) -> None:
        store = DataStore(self.data_dir)
        store.register_project("31", "github.com/example/review")
        original = {
            "release_notes_status": "Met",
            "release_notes_justification": "See https://example.com/releases.",
        }
        store.save_assessment("31", original)
        working = self.root / "preview.json"
        working.write_text(json.dumps(original), encoding="utf-8")
        wording = {"release_notes_justification": "No releases have been published."}
        arguments = ("--assessment-file", str(working), "apply", "--section", "passing", "--offline")

        code, _stdout, stderr = self.run_command(*arguments, "--json", json.dumps(wording))
        self.assertEqual(2, code)
        self.assertIn("requires a public evidence URL", stderr)
        self.assertEqual(original, json.loads(working.read_text(encoding="utf-8")))

        code, stdout, stderr = self.run_command(
            *arguments, "--review-response", "N/A", "--json", json.dumps(wording),
        )
        self.assertEqual(0, code, stderr)
        provisional = original | wording
        self.assertEqual(provisional, json.loads(stdout)["assessment"])
        self.assertEqual(provisional, json.loads(working.read_text(encoding="utf-8")))
        self.assertEqual(original, store.load_assessment("31"))

        code, _stdout, stderr = self.run_command(
            *arguments, "--json", json.dumps({"release_notes_status": "Met"}),
        )
        self.assertEqual(2, code)
        self.assertIn("requires a public evidence URL", stderr)
        code, stdout, stderr = self.run_command(
            *arguments, "--json", json.dumps({"release_notes_status": "N/A"}),
        )
        self.assertEqual(0, code, stderr)
        approved = provisional | {"release_notes_status": "N/A"}
        self.assertEqual(approved, json.loads(stdout)["assessment"])
        self.assertEqual(original, store.load_assessment("31"))

        code, stdout, stderr = self.run_command(
            "apply", "--section", "passing", "--offline", "--json", json.dumps(approved),
        )
        self.assertEqual(0, code, stderr)
        self.assertEqual(approved, store.load_assessment("31"))

    def test_cancel_preview_revision_restores_board_and_export_uses_settled_answers(self) -> None:
        original = {
            "release_notes_status": "Met",
            "release_notes_justification": "See https://example.com/releases.",
        }
        provisional = original | {"release_notes_justification": "No releases have been published."}
        store = DataStore(self.data_dir)
        store.register_project("31", "github.com/example/review")
        store.save_assessment("31", original)
        working = self.root / "preview.json"
        working.write_text(json.dumps(provisional), encoding="utf-8")
        exported = self.root / "export.json"
        code, _stdout, stderr = self.run_command(
            "export", "--offline", "--output", str(exported),
        )
        self.assertEqual(0, code, stderr)
        self.assertEqual(original, json.loads(exported.read_text(encoding="utf-8")))
        self.assertEqual(provisional, json.loads(working.read_text(encoding="utf-8")))

        review = ("review", "--section", "passing", "--offline", "--no-browser")
        code, stdout, stderr = self.run_command("--assessment-file", str(working), *review)
        self.assertEqual(0, code, stderr)
        url = json.loads(stdout)["url"]
        board_path = Path(unquote(urlparse(url).path))
        self.addCleanup(board_path.unlink, missing_ok=True)

        def displayed_answer() -> dict[str, str]:
            markup = board_path.read_text(encoding="utf-8")
            embedded = markup.split('<script id="assessment-data" type="application/json">', 1)[1]
            return json.loads(embedded.split("</script>", 1)[0])["answers"]["release_notes"]

        self.assertEqual(
            {"status": "Met", "justification": provisional["release_notes_justification"]},
            displayed_answer(),
        )
        working.unlink()
        code, stdout, stderr = self.run_command(*review)
        self.assertEqual(0, code, stderr)
        self.assertEqual(url, json.loads(stdout)["url"])
        self.assertEqual(
            {"status": "Met", "justification": original["release_notes_justification"]},
            displayed_answer(),
        )

    def test_preview_revision_rejects_status_fields_and_invalid_destination_wording(self) -> None:
        self.register_verified_project()
        for proposed, response, error in (
            ({"release_notes_status": "N/A"}, "N/A", "only justification fields"),
            ({"name": "Example"}, "N/A", "only justification fields"),
            ({"release_notes_justification": ""}, "N/A", "requires an N/A justification"),
            ({"release_notes_justification": "No releases yet."}, "Met", "requires a public evidence URL"),
            ({"contribution_justification": "No contributions."}, "N/A", "does not allow N/A"),
            ({"release_notes_justification": 5}, "N/A", "must be a string"),
            ({"invented_justification": "No releases yet."}, "N/A", "unknown assessment field"),
        ):
            with self.subTest(proposed=proposed, response=response):
                code, _stdout, stderr = self.run_command(
                    "apply", "--section", "passing", "--project-id", "31", "--offline",
                    "--review-response", response, "--json", json.dumps(proposed),
                )
                self.assertEqual(2, code)
                self.assertIn(error, stderr)
                self.assertEqual({}, DataStore(self.data_dir).load_assessment("31"))

    def test_apply_rejects_a_field_outside_the_selected_section(self) -> None:
        self.register_verified_project()
        result, _stdout, stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps({"achieve_silver_status": "Met"}),
        )

        self.assertEqual(2, result)
        self.assertIn("is not in section 'passing'", stderr)

    def test_repository_assessment_requires_working_file_selection_before_writes(self) -> None:
        repository_file = self.repository / ".bestpractices.json"
        original = '{"description_good_status": "Unmet"}\n'
        repository_file.write_text(original)
        code, _, error = self.run_command("status", "--project-id", "31", "--offline")
        self.assertEqual(2, code)
        self.assertIn("--assessment-file", error)
        self.assertEqual(original, repository_file.read_text())
        store = DataStore(self.data_dir)
        self.assertIsNone(store.resolve_project_id("github.com/example/review"))
        self.assertEqual([], list(self.data_dir.rglob(".bestpractices.json")))
        for name, content in (("missing.json", None), ("invalid.json", "[]")):
            with self.subTest(name=name):
                working = self.root / name
                if content is not None:
                    working.write_text(content)
                code, _, _ = self.run_command(
                    "--assessment-file", str(working), "status", "--project-id", "31", "--offline",
                )
                self.assertEqual(2, code)
                self.assertEqual(original, repository_file.read_text())
                self.assertEqual([], list(self.data_dir.rglob(".bestpractices.json")))

    def test_export_writes_the_canonical_document_to_an_explicit_path(self) -> None:
        self.register_verified_project()
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps({"description_good_status": "Met"}),
        )
        output = self.repository / ".bestpractices.json"

        result, stdout, stderr = self.run_command(
            "export",
            "--project-id",
            "31",
            "--offline",
            "--output",
            str(output),
        )

        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("assessment_exported", json.loads(stdout)["state"])
        self.assertEqual(
            {"description_good_status": "Met"},
            json.loads(output.read_text(encoding="utf-8")),
        )

    def test_review_writes_a_board_and_apply_refreshes_it(self) -> None:
        self.register_verified_project()
        result, stdout, stderr = self.run_command(
            "review",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--no-browser",
        )

        payload = json.loads(stdout)
        board_path = Path(unquote(urlparse(payload["url"]).path))
        self.addCleanup(board_path.unlink, missing_ok=True)
        self.assertTrue(board_path.is_file())
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("review_written", payload["state"])
        self.assertEqual("", urlparse(payload["url"]).fragment)

        result, _stdout, stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps({"description_good_status": "Met"}),
        )

        refreshed_markup = board_path.read_text(encoding="utf-8")
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertIn(
            '"description_good":{"status":"Met"',
            refreshed_markup,
        )

    def test_apply_succeeds_when_passive_board_refresh_fails(self) -> None:
        self.register_verified_project()
        result, stdout, _stderr = self.run_command(
            "review",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--no-browser",
        )
        board_path = Path(unquote(urlparse(json.loads(stdout)["url"]).path))
        self.addCleanup(board_path.unlink, missing_ok=True)
        self.assertEqual(0, result)

        with patch.object(ossf, "write_board", side_effect=OSError("display unavailable")):
            result, stdout, stderr = self.run_command(
                "apply",
                "--section",
                "passing",
                "--project-id",
                "31",
                "--offline",
                "--json",
                json.dumps({"description_good_status": "Met"}),
            )

        self.assertEqual(0, result)
        self.assertEqual("Met", json.loads(stdout)["assessment"]["description_good_status"])
        self.assertIn("warning: passive review board refresh failed", stderr)

        result, stdout, stderr = self.run_command(
            "status",
            "--project-id",
            "31",
            "--offline",
        )
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("Met", json.loads(stdout)["assessment"]["description_good_status"])

    def test_board_refresh_reloads_canonical_state_instead_of_stale_sync(self) -> None:
        self.register_verified_project()
        result, stdout, _stderr = self.run_command(
            "review",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--no-browser",
        )
        payload = json.loads(stdout)
        board_path = Path(unquote(urlparse(payload["url"]).path))
        self.addCleanup(board_path.unlink, missing_ok=True)
        self.assertEqual(0, result)

        store = DataStore(self.data_dir)
        stale_result = ossf._synchronize(
            ossf.build_parser().parse_args(
                [
                    "--repo",
                    str(self.repository),
                    "--data-dir",
                    str(self.data_dir),
                    "status",
                    "--project-id",
                    "31",
                    "--offline",
                ]
            ),
            store_factory=DataStore,
            client_factory=MissingProjectClient,
        )[1]
        store.update_assessment("31", {"description_good_status": "Met"})

        ossf._refresh_open_boards(
            store,
            stale_result,
            ossf.CriteriaCatalog(),
            self.data_dir,
        )

        self.assertIn(
            '"description_good":{"status":"Met"',
            board_path.read_text(encoding="utf-8"),
        )

    def test_apply_flags_assessment_narration_in_justifications(self) -> None:
        self.register_verified_project()
        result, stdout, stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "contribution_status": "Met",
                    "contribution_justification": (
                        "There is no direct evidence for this, but the "
                        "maintainer says the process is followed; this "
                        "corrects a previous statement: "
                        "https://example.com/contributing"
                    ),
                }
            ),
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        # Advisory only: the update is applied despite the warnings.
        self.assertEqual("Met", payload["assessment"]["contribution_status"])
        warned_fields = {item["field"] for item in payload["style_warnings"]}
        self.assertEqual({"contribution_justification"}, warned_fields)
        matched = {item["matched"].lower() for item in payload["style_warnings"]}
        self.assertIn("no direct evidence", matched)
        self.assertIn("maintainer says", matched)
        self.assertIn("corrects a previous", matched)

    def test_apply_does_not_flag_form_voice_or_criterion_vocabulary(self) -> None:
        self.register_verified_project()
        result, stdout, _stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "contribution_status": "Met",
                    "contribution_justification": (
                        # "unreviewable"/"review" are legitimate criterion
                        # vocabulary and must not trip the narration patterns.
                        "Contribution instructions require review of any "
                        "unreviewable artifacts: https://example.com/contributing"
                    ),
                }
            ),
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual([], payload["style_warnings"])

    def test_apply_flags_overlong_justifications_without_blocking(self) -> None:
        self.register_verified_project()
        result, stdout, _stderr = self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "contribution_status": "Met",
                    "contribution_justification": (
                        "https://example.com/contributing " + "detail " * 150
                    ),
                }
            ),
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual("Met", payload["assessment"]["contribution_status"])
        reasons = " ".join(item["reason"] for item in payload["style_warnings"])
        self.assertIn("very long", reasons)

    def test_propose_emits_reviewable_urls_and_skips_unknown_statuses(self) -> None:
        self.register_verified_project()
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "description_good_status": "Met",
                    "contribution_status": "Met",
                    "contribution_justification": "https://example.com/contributing",
                }
            ),
        )

        result, stdout, stderr = self.run_command(
            "propose",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("proposals_ready", payload["state"])
        self.assertEqual(1, len(payload["urls"]))
        url = payload["urls"][0]
        self.assertTrue(
            url.startswith("https://www.bestpractices.dev/en/projects/31/passing/edit?")
        )
        self.assertIn("description_good_status=Met", url)
        self.assertIn("contribution_status=Met", url)
        self.assertIn("contribution_justification=https%3A%2F%2F", url)
        self.assertEqual(
            ["contribution", "description_good"],
            sorted(payload["proposed"]),
        )
        # Unknown statuses offer no answer for the proposal URL to transfer.
        self.assertNotIn("interact_status", url)
        self.assertIn("interact", payload["skipped_unknown"])

    def test_submission_preserves_markdown_and_detects_formatting_changes(self) -> None:
        justification = (
            "The project uses [documented practices][guide].\n\n"
            "[guide]: https://example.com/guide\n\n"
            "- Build the project.\n- Run the checks.\n\n"
            "    make check\n\n"
            "Results are published.  \nSee the guide.\n"
        )
        assessment = {
            "description_good_status": "Met",
            "description_good_justification": justification,
        }
        catalog = CriteriaCatalog()
        plan = build_proposal_urls(
            assessment, catalog, section="passing", project_id="31"
        )
        query = parse_qs(urlparse(plan.urls[0]).query)
        self.assertEqual([justification], query["description_good_justification"])

        live = dict(assessment)
        live["description_good_justification"] = " ".join(justification.split())
        selected = wording_only_criteria(
            assessment, catalog, section="passing", public_document=live
        )
        self.assertEqual(("description_good",), selected)
        plan = build_proposal_urls(
            assessment, catalog, section="passing", project_id="31", public_document=live
        )
        self.assertEqual(selected, plan.dropped_justification_only)
        self.assertEqual((), plan.dropped_no_op)

        script, included = build_fill_script(
            assessment, catalog, section="passing", criteria=selected
        )
        self.assertEqual(selected, included)
        payload, _ = json.JSONDecoder().raw_decode(script.split("const answers = ", 1)[1])
        self.assertEqual(justification, payload["description_good"]["justification"])

    def test_proposal_fills_blank_justification_without_changing_status(self) -> None:
        assessment = {
            "description_good_status": "Met",
            "description_good_justification": "README describes the project.",
        }
        for blank in (None, "", "  \n"):
            with self.subTest(blank=blank):
                plan = build_proposal_urls(
                    assessment, CriteriaCatalog(), section="passing", project_id="31",
                    public_document={
                        "description_good_status": "Met",
                        "description_good_justification": blank,
                    },
                )
                self.assertEqual(("description_good",), plan.proposed)
                self.assertEqual((), plan.dropped_justification_only)
                query = parse_qs(urlparse(plan.urls[0]).query)
                self.assertEqual(["Met"], query["description_good_status"])
                self.assertEqual(
                    [assessment["description_good_justification"]],
                    query["description_good_justification"],
                )
                self.assertNotIn("overrides", query)

    def test_wording_proposals_leave_override_matching_to_the_site(self) -> None:
        live = {
            "description_good_status": "Met",
            "description_good_justification": "Old wording.",
        }
        for overrides in (
            "description_good_justification", "description_good_status", "*",
            "description_*", "unrelated_*",
        ):
            for wording in ("New wording.", ""):
                with self.subTest(overrides=overrides, wording=wording):
                    plan = build_proposal_urls(
                        {**live, "description_good_justification": wording},
                        CriteriaCatalog(), section="passing", project_id="31",
                        public_document=live, overrides=overrides,
                    )
                    self.assertEqual(("description_good",), plan.proposed)
                    self.assertEqual((), plan.dropped_justification_only)
                    query = parse_qs(urlparse(plan.urls[0]).query, keep_blank_values=True)
                    self.assertEqual([overrides], query["overrides"])
                    self.assertEqual(["Met"], query["description_good_status"])
                    self.assertEqual([wording], query["description_good_justification"])

    def test_overrides_do_not_emit_unchanged_answers_or_unknown_statuses(self) -> None:
        assessment = {
            "description_good_status": "Met",
            "description_good_justification": "Existing wording.",
            "interact_status": "?",
            "interact_justification": "Unfinished wording.",
        }
        plan = build_proposal_urls(
            assessment, CriteriaCatalog(), section="passing", project_id="31",
            public_document=assessment, overrides="*",
        )
        self.assertEqual((), plan.urls)
        self.assertEqual(("description_good",), plan.dropped_no_op)
        self.assertIn("interact", plan.skipped_unknown)

    def test_submission_distinguishes_cleared_and_omitted_justifications(self) -> None:
        catalog = CriteriaCatalog()
        assessment = {
            "description_good_status": "Met",
            "description_good_justification": "",
            "interact_status": "Met",
            "contribution_status": "?",
            "contribution_justification": "Work in progress.",
        }
        live = {
            "description_good_status": "Met",
            "description_good_justification": "Old description.",
            "interact_status": "Met",
            "interact_justification": "Keep this explanation.",
            "contribution_status": "Met",
        }
        selected = wording_only_criteria(
            assessment, catalog, section="passing", public_document=live
        )
        self.assertEqual(("description_good",), selected)
        plan = build_proposal_urls(
            assessment, catalog, section="passing", project_id="31", public_document=live
        )
        self.assertEqual(selected, plan.dropped_justification_only)
        self.assertEqual(("interact",), plan.dropped_no_op)
        self.assertIn("contribution", plan.skipped_unknown)
        self.assertEqual((), plan.urls)

        plan = build_proposal_urls(
            assessment, catalog, section="passing", project_id="31"
        )
        query = parse_qs(urlparse(plan.urls[0]).query, keep_blank_values=True)
        self.assertEqual([""], query["description_good_justification"])
        self.assertNotIn("interact_justification", query)
        self.assertNotIn("contribution_status", query)

        script, included = build_fill_script(assessment, catalog, section="passing")
        payload, _ = json.JSONDecoder().raw_decode(script.split("const answers = ", 1)[1])
        self.assertEqual(("description_good", "interact"), included)
        self.assertEqual(
            {
                "description_good": {"status": "Met", "justification": ""},
                "interact": {"status": "Met"},
            },
            payload,
        )

        # Exercise separate controller invocations against unchanged public data.
        client_factory = lambda: PublicProjectClient(live)
        self.run_command("status", client_factory=client_factory)
        code, _, error = self.run_command(
            "apply", "--section", "passing", "--input", "-",
            stdin=json.dumps({"description_good_justification": ""}),
            client_factory=client_factory,
        )
        self.assertEqual((0, ""), (code, error))
        output = self.root / "clear-wording.js"
        for command in (("status",), ("propose", "--section", "passing"),
                        ("fill-script", "--section", "passing", "--output", str(output))):
            with self.subTest(command=command[0]):
                code, stdout, error = self.run_command(*command, client_factory=client_factory)
                self.assertEqual((0, ""), (code, error))
                response = json.loads(stdout)
                if command[0] == "status":
                    self.assertIn({
                        "field": "description_good_justification", "preserved": "",
                        "incoming": live["description_good_justification"], "source": "public_api",
                    }, response["conflicts"])
                else:
                    self.assertEqual([], response["conflicts"])
        self.assertEqual(["description_good"], response["criteria"])
        payload, _ = json.JSONDecoder().raw_decode(
            output.read_text().split("const answers = ", 1)[1]
        )
        self.assertEqual({"description_good": {"status": "Met", "justification": ""}}, payload)

    def test_propose_requires_a_registered_project(self) -> None:
        result, _stdout, stderr = self.run_command(
            "propose",
            "--section",
            "passing",
            "--offline",
            "--allow-unregistered",
        )

        self.assertEqual(2, result)
        self.assertIn("requires a registered", stderr)

    def _record_one_answer(self) -> None:
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps({"description_good_status": "Met"}),
        )

    def test_propose_rejects_a_base_url_outside_the_badge_site(self) -> None:
        self.register_verified_project()
        self._record_one_answer()
        for hostile in (
            "https://attacker.example",
            "https://www.bestpractices.dev.attacker.example",
            "http://www.bestpractices.dev",
            "https://www.bestpractices.dev:8443",
            "https://www.bestpractices.dev/evil",
            "file:///tmp",
        ):
            with self.subTest(base_url=hostile):
                result, stdout, stderr = self.run_command(
                    "propose",
                    "--section",
                    "passing",
                    "--project-id",
                    "31",
                    "--offline",
                    "--base-url",
                    hostile,
                )
                self.assertEqual(2, result)
                self.assertEqual("", stdout)
                self.assertIn("base URL must be one of", stderr)
                self.assertIn("https://www.bestpractices.dev", stderr)

    def test_propose_accepts_the_staging_site_with_a_trailing_slash(self) -> None:
        self.register_verified_project()
        self._record_one_answer()
        result, stdout, _stderr = self.run_command(
            "propose",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--base-url",
            "https://staging.bestpractices.dev/",
        )
        self.assertEqual(0, result)
        payload = json.loads(stdout)
        self.assertTrue(
            payload["urls"][0].startswith(
                "https://staging.bestpractices.dev/en/projects/31/passing/edit?"
            )
        )

    def test_propose_open_hands_the_browser_only_badge_site_urls(self) -> None:
        self.register_verified_project()
        self._record_one_answer()
        opened: list[str] = []
        result, stdout, _stderr = self.run_command(
            "propose",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--open",
            browser_open=opened.append,
        )
        self.assertEqual(0, result)
        payload = json.loads(stdout)
        self.assertEqual([payload["urls"][0]], opened)
        self.assertTrue(
            opened[0].startswith("https://www.bestpractices.dev/en/projects/31/")
        )

    def test_browser_guard_refuses_anything_but_https_badge_site_urls(self) -> None:
        ossf._assert_badge_site_url("https://www.bestpractices.dev/en/projects/31/passing/edit?x=1")
        ossf._assert_badge_site_url("https://staging.bestpractices.dev/en/projects/31/silver/edit?")
        for url in (
            "http://www.bestpractices.dev/en/projects/31/passing/edit?",
            "https://attacker.example/en/projects/31/passing/edit?",
            "https://www.bestpractices.dev@attacker.example/",
            "file:///tmp/edit.html",
        ):
            with self.subTest(url=url), self.assertRaises(ossf.CommandError):
                ossf._assert_badge_site_url(url)

    def test_validate_base_url_normalizes_only_the_allowed_sites(self) -> None:
        self.assertEqual(
            "https://www.bestpractices.dev", validate_base_url("https://www.bestpractices.dev/")
        )
        self.assertEqual(
            "https://staging.bestpractices.dev",
            validate_base_url("  https://staging.bestpractices.dev  "),
        )
        with self.assertRaises(ValueError):
            validate_base_url("https://bestpractices.dev")

    def test_propose_drops_no_ops_and_reports_justification_only_changes(
        self,
    ) -> None:
        client = PublicProjectClient(
            {
                "repo_url": "https://github.com/example/review",
                "description_good_status": "Met",
                "description_good_justification": "README opening paragraph.",
                "interact_status": "Met",
                "interact_justification": "README covers interaction.",
            }
        )
        self.run_command("status", client_factory=lambda: client)
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "description_good_status": "Met",
                    "description_good_justification": "A better wording.",
                    "maintained_status": "Met",
                }
            ),
        )

        result, stdout, stderr = self.run_command(
            "propose",
            "--section",
            "passing",
            "--project-id",
            "31",
            client_factory=lambda: client,
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual(["maintained"], payload["proposed"])
        self.assertEqual(["interact"], payload["dropped_no_op"])
        self.assertEqual(
            ["description_good"],
            payload["dropped_justification_only"],
        )
        self.assertTrue(
            any("fill-script" in note for note in payload["notes"])
        )

    def test_propose_chunks_urls_without_splitting_a_criterion(self) -> None:
        self.register_verified_project()
        justification = "https://example.com/evidence " + "x" * 120
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "description_good_status": "Met",
                    "description_good_justification": justification,
                    "interact_status": "Met",
                    "interact_justification": justification,
                    "maintained_status": "Met",
                    "maintained_justification": justification,
                }
            ),
        )

        result, stdout, _stderr = self.run_command(
            "propose",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--max-url-bytes",
            "300",
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertGreater(len(payload["urls"]), 1)
        for url in payload["urls"]:
            # A criterion's status and justification are coupled upstream and
            # must always travel in the same URL.
            for criterion in ("description_good", "interact", "maintained"):
                has_status = f"{criterion}_status=" in url
                has_justification = f"{criterion}_justification=" in url
                self.assertEqual(has_status, has_justification)
        self.assertTrue(any("Save (and" in note for note in payload["notes"]))

    def test_propose_reports_oversize_criteria_instead_of_emitting_them(
        self,
    ) -> None:
        self.register_verified_project()
        long_justification = "https://example.com/evidence " + "detail " * 60
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "description_good_status": "Met",
                    "description_good_justification": long_justification,
                    "interact_status": "Met",
                }
            ),
        )

        result, stdout, _stderr = self.run_command(
            "propose",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--max-url-bytes",
            "300",
        )

        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual(["description_good"], payload["oversize"])
        self.assertEqual(["interact"], payload["proposed"])
        for url in payload["urls"]:
            self.assertNotIn("description_good", url)
            self.assertLessEqual(len(url.encode("utf-8")), 300)
        self.assertTrue(
            any("fill-script --criteria" in note for note in payload["notes"])
        )

    def test_propose_rejects_overrides_upstream_would_ignore(self) -> None:
        self.register_verified_project()
        result, _stdout, stderr = self.run_command(
            "propose",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--overrides",
            "x" * 10_001,
        )

        self.assertEqual(2, result)
        self.assertIn("overrides", stderr)

    def test_fill_script_writes_selected_answers_and_refuses_private_storage(
        self,
    ) -> None:
        self.register_verified_project()
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "description_good_status": "Met",
                    "description_good_justification": "README opening paragraph.",
                }
            ),
        )
        output = self.root / "fill.js"

        result, stdout, stderr = self.run_command(
            "fill-script",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--all",
            "--output",
            str(output),
        )

        payload = json.loads(stdout)
        script = output.read_text(encoding="utf-8")
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("fill_script_written", payload["state"])
        self.assertEqual("all", payload["scope"])
        self.assertEqual(["description_good"], payload["criteria"])
        self.assertIn("description_good", script)

        result, _stdout, stderr = self.run_command(
            "fill-script",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--all",
            "--output",
            str(self.data_dir / "fill.js"),
        )
        self.assertEqual(2, result)
        self.assertIn("outside CLAUDE_PLUGIN_DATA", stderr)

    def test_fill_script_changed_only_is_default_and_requires_live_entry(
        self,
    ) -> None:
        self.register_verified_project()
        result, _stdout, stderr = self.run_command(
            "fill-script",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--output",
            str(self.root / "fill.js"),
        )

        self.assertEqual(2, result)
        self.assertIn("--changed-only cannot compute", stderr)
        self.assertIn("--criteria", stderr)
        self.assertIn("--all", stderr)
        self.assertFalse((self.root / "fill.js").exists())

    def test_fill_script_changed_only_targets_wording_diffs_only(self) -> None:
        client = PublicProjectClient(
            {
                "repo_url": "https://github.com/example/review",
                "description_good_status": "Met",
                "description_good_justification": "Same wording.",
                "interact_status": "Met",
                "interact_justification": "Thin bot wording without a URL.",
                "maintained_status": "Unmet",
            }
        )
        self.run_command("status", client_factory=lambda: client)
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "description_good_status": "Met",
                    "description_good_justification": "Same wording.",
                    "interact_status": "Met",
                    "interact_justification": (
                        "Obtain, feedback, and contribution paths are in the "
                        "README: https://example.com#readme"
                    ),
                    "maintained_status": "Met",
                }
            ),
        )
        output = self.root / "fill.js"

        result, stdout, stderr = self.run_command(
            "fill-script",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--output",
            str(output),
            client_factory=lambda: client,
        )

        payload = json.loads(stdout)
        script = output.read_text(encoding="utf-8")
        self.assertEqual(0, result)
        self.assertEqual("", stderr)
        self.assertEqual("changed-only", payload["scope"])
        # Only the wording-only diff: not the in-sync criterion, and not the
        # status-divergent one (that belongs to propose, or to a deliberate
        # --criteria choice — never to a silent full-section write).
        self.assertEqual(["interact"], payload["criteria"])
        self.assertIn("interact", script)
        self.assertNotIn("maintained", script)
        self.assertNotIn("description_good", script)

    def test_fill_script_criteria_selects_an_explicit_validated_subset(
        self,
    ) -> None:
        self.register_verified_project()
        self.run_command(
            "apply",
            "--section",
            "baseline-1",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "osps_ac_01_01_status": "Unmet",
                    "osps_ac_01_01_justification": "MFA is not yet enforced.",
                    "osps_vm_02_01_status": "Met",
                    "osps_vm_02_01_justification": (
                        "Security contacts are in SECURITY.md: "
                        "https://example.com/SECURITY.md"
                    ),
                }
            ),
        )
        output = self.root / "fill.js"

        result, stdout, _stderr = self.run_command(
            "fill-script",
            "--section",
            "baseline-1",
            "--project-id",
            "31",
            "--offline",
            "--criteria",
            "OSPS-AC-01.01",
            "--output",
            str(output),
        )

        payload = json.loads(stdout)
        script = output.read_text(encoding="utf-8")
        self.assertEqual(0, result)
        self.assertEqual("criteria", payload["scope"])
        self.assertEqual(["osps_ac_01_01"], payload["criteria"])
        self.assertIn("osps_ac_01_01", script)
        self.assertNotIn("osps_vm_02_01", script)

        result, _stdout, stderr = self.run_command(
            "fill-script",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--criteria",
            "achieve_silver",
            "--output",
            str(output),
        )
        self.assertEqual(2, result)
        self.assertIn("--criteria", stderr)

    def test_status_reports_wording_only_updates_against_live_entry(self) -> None:
        self.register_verified_project()
        client = PublicProjectClient(
            {
                "repo_url": "https://github.com/example/review",
                "interact_status": "Met",
                "interact_justification": "Thin bot wording without a URL.",
            }
        )
        self.run_command(
            "apply",
            "--section",
            "passing",
            "--project-id",
            "31",
            "--offline",
            "--json",
            json.dumps(
                {
                    "interact_status": "Met",
                    "interact_justification": (
                        "Obtain, feedback, and contribution paths are in the "
                        "README: https://example.com#readme"
                    ),
                }
            ),
        )

        result, stdout, _stderr = self.run_command(
            "status",
            "--project-id",
            "31",
            client_factory=lambda: client,
        )
        payload = json.loads(stdout)
        self.assertEqual(0, result)
        self.assertEqual({"passing": ["interact"]}, payload["wording_only_updates"])

        result, stdout, _stderr = self.run_command(
            "status",
            "--project-id",
            "31",
            "--offline",
        )
        self.assertEqual(0, result)
        payload = json.loads(stdout)
        self.assertEqual({"passing": ["interact"]}, payload["wording_only_updates"])
        self.assertEqual("cached", payload["sources"]["public_snapshot"]["source"])
        self.assertFalse(payload["sources"]["public_loaded"])

    def test_review_opens_only_the_generated_file_url(self) -> None:
        self.register_verified_project()
        for view, fragment in ((None, ""), ("overview", ""), ("all", "view=all")):
            for no_browser in (False, True):
                with self.subTest(view=view, no_browser=no_browser):
                    opened: list[str] = []
                    arguments = [] if view is None else ["--view", view]
                    if no_browser:
                        arguments.append("--no-browser")
                    result, stdout, stderr = self.run_command(
                        "review",
                        "--section",
                        "silver",
                        "--project-id",
                        "31",
                        "--offline",
                        *arguments,
                        browser_open=opened.append,
                    )

                    payload = json.loads(stdout)
                    board_url = urlparse(payload["url"])
                    board_path = Path(unquote(board_url.path))
                    self.addCleanup(board_path.unlink, missing_ok=True)
                    self.assertEqual((0, ""), (result, stderr))
                    self.assertEqual("review_written", payload["state"])
                    self.assertEqual([] if no_browser else [payload["url"]], opened)
                    self.assertEqual("file", board_url.scheme)
                    self.assertEqual(fragment, board_url.fragment)
                    self.assertEqual("silver", payload["section"])
                    self.assertTrue(board_path.is_file())

    def test_review_rejects_unknown_views_and_retired_preview_command(self) -> None:
        for arguments in (("review", "--view", "missing"), ("preview",)):
            with self.subTest(arguments=arguments):
                with (
                    contextlib.redirect_stderr(StringIO()),
                    self.assertRaises(SystemExit) as raised,
                ):
                    ossf.build_parser().parse_args(arguments)
                self.assertEqual(2, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
