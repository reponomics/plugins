"""Regression checks for preserving answers across Baseline field spellings."""

import contextlib
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins/badge-buddy/scripts"
sys.path.insert(0, str(SCRIPTS))

import ossf
from ossf_review.board import build_board_payload
from ossf_review.criteria import CriteriaCatalog
from ossf_review.storage import DataStore
from ossf_review.submission import build_fill_script, build_proposal_urls
from ossf_review.sync import synchronize_project


DISPLAY = "OSPS-AC-01.01"
CANONICAL = "osps_ac_01_01"
REMOTE = "https://github.com/example/project"


class BaselineAliasesTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.repo = self.root / "repo"
        subprocess.run(
            ["git", "init", "-q", str(self.repo)], check=True, capture_output=True
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "add", "origin", REMOTE],
            check=True,
            capture_output=True,
        )
        self.store = DataStore(self.root / "data")
        self.store.register_project("31", REMOTE)
        self.catalog = CriteriaCatalog()

    def seed(self, document, *, repository_backed=False):
        # Model existing files, including ones saved before normalization existed.
        path = (
            self.root / "working.json"
            if repository_backed
            else self.root / "data/projects/31/.bestpractices.json"
        )
        path.write_text(json.dumps(document))
        if repository_backed:
            self.store.use_assessment_file(path)
        return path

    def client(self, fields):
        return Mock(
            fetch_project=Mock(return_value={"id": 31, "repo_url": REMOTE, **fields})
        )

    def test_refresh_preserves_display_answers_and_reports_canonical_conflicts(self):
        for repository_backed in (False, True):
            with self.subTest(repository_backed=repository_backed):
                local = {
                    f"{DISPLAY}_status": "Unmet",
                    f"{DISPLAY}_justification": "Deliberate local answer",
                    "name": "Keep metadata",
                }
                path = self.seed(local, repository_backed=repository_backed)
                result = synchronize_project(
                    self.store,
                    self.repo,
                    project_id="31",
                    client=self.client(
                        {
                            f"{DISPLAY}_status": "Met",
                            f"{DISPLAY}_justification": "Website answer",
                        }
                    ),
                )
                self.assertEqual("Unmet", result.assessment[f"{CANONICAL}_status"])
                self.assertEqual(
                    "Deliberate local answer",
                    result.assessment[f"{CANONICAL}_justification"],
                )
                self.assertEqual("Keep metadata", result.assessment["name"])
                self.assertEqual(
                    {f"{CANONICAL}_status", f"{CANONICAL}_justification"},
                    {item.field for item in result.conflicts},
                )
                self.assertEqual(result.assessment, json.loads(path.read_text()))
                self.assertNotIn(f"{DISPLAY}_status", result.assessment)

    def test_unknown_and_empty_wording_are_not_initialized_from_website(self):
        self.seed({f"{DISPLAY}_status": "?", f"{DISPLAY}_justification": ""})
        result = synchronize_project(
            self.store,
            self.repo,
            client=self.client(
                {
                    f"{CANONICAL}_status": "Met",
                    f"{CANONICAL}_justification": "Website answer",
                }
            ),
        )
        self.assertEqual(
            {f"{CANONICAL}_status": "?", f"{CANONICAL}_justification": ""},
            result.assessment,
        )
        self.assertEqual(2, len(result.conflicts))

    def test_justification_only_apply_cannot_clear_required_na_wording(self):
        path = self.seed(
            {
                f"{DISPLAY}_status": "N/A",
                f"{DISPLAY}_justification": "Not applicable here",
            },
            repository_backed=True,
        )
        output, errors = StringIO(), StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = ossf.main(
                [
                    "--repo",
                    str(self.repo),
                    "--data-dir",
                    str(self.root / "data"),
                    "--assessment-file",
                    str(path),
                    "apply",
                    "--section",
                    "baseline-1",
                    "--json",
                    json.dumps({f"{CANONICAL}_justification": ""}),
                ]
            )
        self.assertNotEqual(0, code)
        self.assertIn("requires an N/A justification", errors.getvalue())
        self.assertEqual(
            "Not applicable here",
            self.store.load_assessment("31")[f"{CANONICAL}_justification"],
        )

    def test_canonical_update_replaces_display_answer_without_resurrecting_it(self):
        path = self.seed(
            {f"{DISPLAY}_status": "Unmet", f"{DISPLAY}_justification": "Old wording"}
        )
        result = self.store.update_assessment(
            "31", {f"{CANONICAL}_status": "?", f"{CANONICAL}_justification": ""}
        )
        expected = {f"{CANONICAL}_status": "?", f"{CANONICAL}_justification": ""}
        self.assertEqual(expected, result)
        self.assertEqual(expected, json.loads(path.read_text()))

    def test_conflicting_aliases_fail_without_overwriting_input_in_either_order(self):
        pairs = [(f"{DISPLAY}_status", "Unmet"), (f"{CANONICAL}_status", "Met")]
        for entries in (pairs, list(reversed(pairs))):
            with self.subTest(entries=entries):
                path = self.seed(dict(entries))
                before = path.read_bytes()
                with self.assertRaisesRegex(ValueError, "conflicting aliases"):
                    synchronize_project(self.store, self.repo, client=self.client({}))
                self.assertEqual(before, path.read_bytes())
                with self.assertRaisesRegex(ValueError, "conflicting aliases"):
                    self.catalog.classify_flat(dict(entries))

    def test_conflicting_website_aliases_leave_assessment_and_snapshot_unchanged(self):
        path = self.seed({f"{CANONICAL}_status": "Unmet"})
        snapshot = self.store.save_public_snapshot(
            "31", REMOTE, {f"{CANONICAL}_status": "Unmet"}
        )
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "conflicting aliases"):
            synchronize_project(
                self.store,
                self.repo,
                client=self.client(
                    {
                        f"{DISPLAY}_status": "Unmet",
                        f"{CANONICAL}_status": "Met",
                    }
                ),
            )
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(snapshot, self.store.load_public_snapshot("31", REMOTE))

    def test_equal_aliases_collapse_and_metadata_survives(self):
        self.seed(
            {
                f"{DISPLAY}_status": "Met",
                f"{CANONICAL}_status": "Met",
                "custom": {"keep": True},
            }
        )
        result = self.store.transform_assessment("31", lambda current: current)
        self.assertEqual(
            {f"{CANONICAL}_status": "Met", "custom": {"keep": True}}, result
        )

    def test_local_draft_handoff_recognizes_same_answer_across_aliases(self):
        record = self.store.create_unregistered(self.repo, remote=REMOTE)
        draft_path = (
            self.root
            / "data/unregistered"
            / record["storage_key"]
            / ".bestpractices.json"
        )
        draft_path.write_text(
            json.dumps(
                {
                    f"{DISPLAY}_status": "Unmet",
                    f"{DISPLAY}_justification": "Local draft",
                }
            )
        )
        self.seed(
            {
                f"{CANONICAL}_status": "Met",
                f"{CANONICAL}_justification": "Registered answer",
            }
        )
        assessment, conflicts = self.store.handoff_unregistered(self.repo, "31")
        self.assertEqual("Met", assessment[f"{CANONICAL}_status"])
        self.assertIn(f"{CANONICAL}_status", conflicts)
        self.assertEqual(
            "Unmet", json.loads(draft_path.read_text())[f"{CANONICAL}_status"]
        )

    def test_display_answers_use_canonical_fields_in_both_transfer_methods_and_board(
        self,
    ):
        document = {
            f"{DISPLAY}_status": "Met",
            f"{DISPLAY}_justification": "MFA enabled",
        }
        plan = build_proposal_urls(
            document, self.catalog, section="baseline-1", project_id="31"
        )
        self.assertEqual(
            {
                f"{CANONICAL}_status": ["Met"],
                f"{CANONICAL}_justification": ["MFA enabled"],
            },
            parse_qs(urlsplit(plan.urls[0]).query),
        )
        script, ids = build_fill_script(document, self.catalog, section="baseline-1")
        self.assertEqual((CANONICAL,), ids)
        self.assertIn(f'"{CANONICAL}"', script)
        self.assertNotIn(DISPLAY, script)
        board = build_board_payload(
            document, project_id="31", section="baseline-1", catalog=self.catalog
        )
        self.assertEqual(
            {"status": "Met", "justification": "MFA enabled"},
            board["answers"][CANONICAL],
        )


if __name__ == "__main__":
    unittest.main()
