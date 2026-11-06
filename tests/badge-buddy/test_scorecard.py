"""Behavioral tests for published Scorecard snapshots and imported diagnostics."""

from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from typing import Any
import urllib.error


REPOSITORY_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "badge-buddy"
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import scorecard as controller  # noqa: E402


def result_document(
    scores: dict[str, int | None] | None = None,
    *,
    reported: float | None = 4.2,
) -> dict[str, Any]:
    """An upstream document whose aggregate need not match the selected checks."""
    if scores is None:
        scores = {"License": 10, "Signed-Releases": -1}
    return {
        "date": "2026-09-01T00:00:00Z",
        "repo": {"name": "github.com/example/project", "commit": "a" * 40},
        "scorecard": {"version": "v5.5.0", "commit": "b" * 40},
        "score": reported,
        "checks": [
            {"name": name, "score": score, "reason": f"{name} reason", "details": None}
            for name, score in scores.items()
        ],
    }


class FakeResponse:
    def __init__(self, payload: str | bytes) -> None:
        self.payload = payload.encode("utf-8") if isinstance(payload, str) else payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: Any) -> None:
        return None


class ControllerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name)
        self.stderr = ""

    def run_command(
        self, argv: list[str], *, stdin: str = "", **dependencies: Any,
    ) -> tuple[int, dict[str, Any]]:
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(sys, "stdout", output), patch.object(sys, "stderr", errors):
            with patch.object(sys, "stdin", io.StringIO(stdin)):
                try:
                    code = controller.main(argv, **dependencies)
                except SystemExit as error:
                    code = error.code
        self.stderr = errors.getvalue()
        return code, json.loads(output.getvalue()) if output.getvalue().strip() else {}

    def write_document(self, document: Any, name: str = "input.json") -> Path:
        path = self.root / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def explain(self, document: Any) -> tuple[int, dict[str, Any]]:
        return self.run_command(["explain", "--input", str(self.write_document(document))])

    def fetch_document(
        self, document: dict[str, Any], name: str = "snapshot.json",
    ) -> tuple[int, dict[str, Any], Path]:
        destination = self.root / name
        code, payload = self.run_command(
            ["fetch", "--repo", "example/project", "--output", str(destination)],
            opener=lambda *args, **kwargs: FakeResponse(json.dumps(document)),
        )
        return code, payload, destination

    def compare_documents(
        self, before: dict[str, Any], after: dict[str, Any], *, published: bool = True,
    ) -> tuple[int, dict[str, Any]]:
        if published:
            before_code, _, before_path = self.fetch_document(before, "before.json")
            after_code, _, after_path = self.fetch_document(after, "after.json")
            self.assertEqual(0, before_code, self.stderr)
            self.assertEqual(0, after_code, self.stderr)
        else:
            before_path = self.write_document(before, "before.json")
            after_path = self.write_document(after, "after.json")
        return self.run_command(
            ["diff", "--before", str(before_path), "--after", str(after_path)]
        )

    def assert_clean_error(self, code: int) -> None:
        self.assertEqual(2, code)
        self.assertTrue(self.stderr.strip())
        self.assertNotIn("Traceback", self.stderr)


class ImportTest(ControllerTestCase):
    def test_import_preserves_reported_score_and_unknown_check_evidence(self) -> None:
        document = result_document({"Future-Upstream-Check": 10}, reported=4.2)
        document["checks"][0].update({
            "reason": "new scanner evidence",
            "details": ["Warn: dependency not pinned: build.yml:12"],
            "documentation": {"url": "https://example.org/check", "short": "A new check"},
            "annotations": ["example evidence"],
        })
        code, payload = self.explain(document)

        self.assertEqual(0, code, self.stderr)
        self.assertEqual(1, payload["schema_version"])
        self.assertEqual("explained", payload["state"])
        self.assertEqual(4.2, payload["reported_score"])
        row = payload["checks"][0]
        self.assertEqual("Future-Upstream-Check", row["name"])
        self.assertEqual(10, row["score"])
        self.assertTrue(row["conclusive"])
        for key in ("reason", "details", "documentation", "annotations"):
            self.assertEqual(document["checks"][0][key], row[key])
        self.assertEqual("file", payload["provenance"]["source"])
        self.assertTrue(payload["coverage_notes"])

    def test_import_exposes_identity_without_inventing_it(self) -> None:
        document = result_document()
        code, payload = self.explain(document)
        self.assertEqual(0, code, self.stderr)
        expected = {
            "repo": document["repo"]["name"],
            "commit": document["repo"]["commit"],
            "date": document["date"],
            "scorecard_version": document["scorecard"]["version"],
            "scorecard_commit": document["scorecard"]["commit"],
        }
        for key, value in expected.items():
            self.assertEqual(value, payload[key])

    def test_inconclusive_and_missing_aggregate_are_not_recomputed(self) -> None:
        for reported in (None, -1):
            with self.subTest(reported=reported):
                code, payload = self.explain(result_document(reported=reported))
                self.assertEqual(0, code, self.stderr)
                self.assertIsNone(payload["reported_score"])
                row = next(row for row in payload["checks"] if row["name"] == "Signed-Releases")
                self.assertIsNone(row["score"])
                self.assertFalse(row["conclusive"])
                self.assertEqual(["Signed-Releases"], payload["checks_excluded"])
        document = result_document({"License": 10})
        del document["score"]
        code, payload = self.explain(document)
        self.assertEqual(0, code, self.stderr)
        self.assertIsNone(payload["reported_score"])

    def test_optional_check_evidence_is_normalized(self) -> None:
        document = result_document({"License": 0, "Signed-Releases": -1})
        document["checks"][1]["documentation"] = None
        code, payload = self.explain(document)
        self.assertEqual(0, code, self.stderr)
        for row in payload["checks"]:
            self.assertEqual([], row["details"])
            self.assertEqual({}, row["documentation"])
        self.assertEqual(0, payload["checks"][0]["score"])
        self.assertTrue(payload["checks"][0]["conclusive"])

    def test_local_json_import_is_explicitly_diagnostic(self) -> None:
        document = result_document({"License": 10})
        document["repo"]["name"] = "file:///tmp/project"
        code, payload = self.explain(document)
        self.assertEqual(0, code, self.stderr)
        self.assertEqual("file:///tmp/project", payload["repo"])
        notes = " ".join(payload["coverage_notes"]).lower()
        self.assertIn("local", notes)
        self.assertIn("publish", notes)
        self.assertIn("publication has not been verified", notes)

    def test_stdin_accepts_raw_upstream_json(self) -> None:
        code, payload = self.run_command(
            ["explain", "--input", "-"], stdin=json.dumps(result_document()),
        )
        self.assertEqual(0, code, self.stderr)
        self.assertEqual(4.2, payload["reported_score"])

    def test_malformed_documents_fail_without_a_traceback(self) -> None:
        invalid = [None, [], {}, {"checks": []}, {"checks": "License"}]
        for field, value in (
            ("repo", []), ("repo", "example/project"), ("scorecard", []),
            ("date", []), ("date", "not-a-date"),
        ):
            document = result_document()
            document[field] = value
            invalid.append(document)
        for field, value in (
            ("repo", {"name": ""}), ("repo", {"name": 7}),
            ("repo", {"name": "github.com/example/project", "commit": []}),
            ("scorecard", {"version": 7}), ("scorecard", {"commit": []}),
        ):
            document = result_document()
            document[field] = value
            invalid.append(document)
        for document in invalid:
            with self.subTest(document=document):
                code, _ = self.explain(document)
                self.assert_clean_error(code)

    def test_invalid_check_scores_are_rejected_without_coercion(self) -> None:
        for score in (None, True, False, "5", [], {}, 1.5, -2, 11, float("nan"), float("inf")):
            with self.subTest(score=score):
                document = result_document()
                document["checks"][0]["score"] = score
                code, _ = self.explain(document)
                self.assert_clean_error(code)
        document = result_document()
        del document["checks"][0]["score"]
        code, _ = self.explain(document)
        self.assert_clean_error(code)

    def test_invalid_reported_scores_are_rejected_without_coercion(self) -> None:
        for score in (True, False, "5", [], {}, -0.5, -2, 11, 10**400, float("nan"), float("inf")):
            with self.subTest(score=score):
                document = result_document()
                document["score"] = score
                code, _ = self.explain(document)
                self.assert_clean_error(code)

    def test_malformed_check_evidence_is_rejected(self) -> None:
        for field, value in (
            ("name", ""), ("name", "   "), ("name", 7), ("name", None),
            ("details", "one string"), ("details", [7]), ("documentation", []),
            ("documentation", {"url": 7}), ("annotations", "one string"), ("annotations", [7]),
            ("reason", []),
        ):
            with self.subTest(field=field, value=value):
                document = result_document()
                document["checks"][0][field] = value
                code, _ = self.explain(document)
                self.assert_clean_error(code)
        for entry in (None, [], "License", {"score": 5}):
            with self.subTest(entry=entry):
                document = result_document()
                document["checks"] = [entry]
                code, _ = self.explain(document)
                self.assert_clean_error(code)

    def test_duplicate_check_names_are_rejected(self) -> None:
        document = result_document()
        document["checks"].append(copy.deepcopy(document["checks"][0]))
        code, _ = self.explain(document)
        self.assert_clean_error(code)
        self.assertIn("duplicate", self.stderr.lower())

    def test_bad_json_and_missing_files_fail_cleanly(self) -> None:
        path = self.root / "bad.json"
        path.write_text("{", encoding="utf-8")
        for target in (path, self.root / "missing.json"):
            with self.subTest(target=target):
                code, _ = self.run_command(["explain", "--input", str(target)])
                self.assert_clean_error(code)

    def test_malformed_snapshot_metadata_cannot_claim_api_provenance(self) -> None:
        for metadata in (
            None, [], {}, {"schema_version": 2, "provenance": {}},
            {"schema_version": True, "provenance": {}},
            {"schema_version": 1, "provenance": []},
            {"schema_version": 1, "provenance": {"source": "invented"}},
        ):
            with self.subTest(metadata=metadata):
                document = result_document()
                document["_ossf_scorecard"] = metadata
                code, _ = self.explain(document)
                self.assert_clean_error(code)
                self.assertIn("_ossf_scorecard", self.stderr)


class PublicApiTest(ControllerTestCase):
    def test_fetch_reads_public_endpoint_and_uses_only_upstream_score(self) -> None:
        requests: list[tuple[Any, int]] = []

        def opener(request: Any, timeout: int = 0) -> FakeResponse:
            requests.append((request, timeout))
            return FakeResponse(json.dumps(result_document({"License": 10}, reported=4.2)))

        code, payload = self.run_command(["fetch", "--repo", "example/project"], opener=opener)
        self.assertEqual(0, code, self.stderr)
        self.assertEqual("fetched", payload["state"])
        self.assertEqual(1, payload["schema_version"])
        self.assertEqual(4.2, payload["reported_score"])
        self.assertEqual("api", payload["provenance"]["source"])
        self.assertEqual(1, len(requests))
        request, timeout = requests[0]
        self.assertEqual("https://api.scorecard.dev/projects/github.com/example/project", request.full_url)
        self.assertEqual("GET", request.get_method())
        self.assertGreater(timeout, 0)
        self.assertIsNone(request.get_header("Authorization"))

    def test_saved_snapshot_retains_all_upstream_data_and_survives_reload(self) -> None:
        document = result_document()
        document["future_metadata"] = {"nested": ["preserve", 42]}
        document["checks"][0]["future_evidence"] = ["retain this too"]
        code, fetched, destination = self.fetch_document(document, "nested/baseline.json")
        self.assertEqual(0, code, self.stderr)
        saved = json.loads(destination.read_text(encoding="utf-8"))
        for key, value in document.items():
            self.assertEqual(value, saved[key])
        self.assertEqual(1, saved["_ossf_scorecard"]["schema_version"])
        self.assertEqual("api", saved["_ossf_scorecard"]["provenance"]["source"])
        code, imported = self.run_command(["explain", "--input", str(destination)])
        self.assertEqual(0, code, self.stderr)
        for key in ("reported_score", "repo", "commit", "date", "provenance", "coverage_notes"):
            self.assertEqual(fetched[key], imported[key])
        self.assertIn("publish", " ".join(imported["coverage_notes"]).lower())

    def test_supported_repository_forms_select_correct_endpoint(self) -> None:
        for spelling, normalized in (
            ("example/project", "github.com/example/project"),
            ("github.com/example/project", "github.com/example/project"),
            ("https://github.com/example/project/", "github.com/example/project"),
            ("https://github.com/example/project.git", "github.com/example/project"),
            ("https://github.com/example/project.git/", "github.com/example/project"),
            ("https://gitlab.com/group/project.git", "gitlab.com/group/project"),
            ("gitlab.com/group/subgroup/project", "gitlab.com/group/subgroup/project"),
            ("https://gitlab.com/group/subgroup/project", "gitlab.com/group/subgroup/project"),
            ("https://gitlab.com/group/subgroup/project.git", "gitlab.com/group/subgroup/project"),
            ("https://gitlab.com/group.git/subgroup/project.git", "gitlab.com/group.git/subgroup/project"),
        ):
            with self.subTest(spelling=spelling):
                def opener(request: Any, timeout: int = 0) -> FakeResponse:
                    self.assertEqual("https://api.scorecard.dev/projects/" + normalized, request.full_url)
                    document = result_document()
                    document["repo"]["name"] = normalized
                    return FakeResponse(json.dumps(document))
                code, payload = self.run_command(["fetch", "--repo", spelling], opener=opener)
                self.assertEqual(0, code, self.stderr)
                self.assertEqual(normalized, payload["repo"])

    def test_invalid_repository_forms_do_not_make_network_requests(self) -> None:
        for repo in (
            "project", "github.com/example/project/issues", "https://example.org/a/b",
            "https://github.com/example/project?token=secret",
            "https://github.com/example/project#readme",
            "https://user:secret@github.com/example/project", "file:///tmp/project",
            "github.com/example/../project", "github.com/example/project extra",
            "https://github.com/example/.git", "https://gitlab.com/group/.git",
            "https://gitlab.com/fdroid/fdroidclient/-/issues/1",
            "https://gitlab.com/fdroid/fdroidclient/-/tree/main",
            "https://gitlab.com/group/subgroup/project/-/merge_requests/1",
            "https://gitlab.com/group/subgroup/project/-/",
        ):
            with self.subTest(repo=repo):
                opener = Mock()
                code, _ = self.run_command(["fetch", "--repo", repo], opener=opener)
                self.assert_clean_error(code)
                opener.assert_not_called()

    def test_publication_notes_follow_the_forge_through_snapshot_reload(self) -> None:
        for host in ("github.com", "gitlab.com"):
            with self.subTest(host=host):
                document = result_document()
                document["repo"]["name"] = f"{host}/example/project"
                destination = self.root / f"{host}.json"
                code, fetched = self.run_command(
                    ["fetch", "--repo", f"https://{host}/example/project.git", "--output", str(destination)],
                    opener=lambda *args, **kwargs: FakeResponse(json.dumps(document)),
                )
                self.assertEqual(0, code, self.stderr)
                code, imported = self.run_command(["explain", "--input", str(destination)])
                self.assertEqual(0, code, self.stderr)
                self.assertEqual(fetched["coverage_notes"], imported["coverage_notes"])
                notes = " ".join(imported["coverage_notes"])
                self.assertIn("API date and commit", notes)
                if host == "gitlab.com":
                    self.assertIn("existing API results", notes)
                    self.assertIn("limited to GitHub", notes)
                    self.assertIn("#using-a-gitlab-repository", notes)
                    self.assertNotIn("Action", notes)
                    self.assertNotIn("publish_results", notes)
                else:
                    self.assertIn("Action publishing run", notes)

    def test_gitlab_missing_result_does_not_recommend_github_action_setup(self) -> None:
        def opener(request: Any, timeout: int = 0) -> FakeResponse:
            self.assertEqual(
                "https://api.scorecard.dev/projects/gitlab.com/group/subgroup/project",
                request.full_url,
            )
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, io.BytesIO())

        code, _ = self.run_command(
            ["fetch", "--repo", "https://gitlab.com/group/subgroup/project.git"], opener=opener,
        )
        self.assert_clean_error(code)
        self.assertIn("no published Scorecard result", self.stderr)
        self.assertIn("import upstream diagnostic JSON", self.stderr)
        self.assertIn("#using-a-gitlab-repository", self.stderr)
        self.assertNotIn("Action", self.stderr)
        self.assertNotIn("publish_results", self.stderr)

    def test_api_identity_mismatch_is_not_saved_as_requested_repository(self) -> None:
        document = result_document()
        document["repo"]["name"] = "github.com/someone/else"
        code, _, destination = self.fetch_document(document)
        self.assert_clean_error(code)
        self.assertFalse(destination.exists())
        self.assertIn("github.com/someone/else", self.stderr)
        self.assertIn("github.com/example/project", self.stderr)

    def test_http_failures_distinguish_missing_publication_from_transient_failure(self) -> None:
        for status in (404, 429, 500, 503):
            with self.subTest(status=status):
                def opener(request: Any, timeout: int = 0) -> FakeResponse:
                    raise urllib.error.HTTPError(request.full_url, status, "error", {}, io.BytesIO())
                code, _ = self.run_command(["fetch", "--repo", "example/project"], opener=opener)
                self.assert_clean_error(code)
                if status == 404:
                    self.assertIn("publish", self.stderr.lower())
                    self.assertIn("Action", self.stderr)
                else:
                    self.assertIn(str(status), self.stderr)
                    self.assertNotIn("no published", self.stderr.lower())

    def test_network_and_malformed_api_failures_are_actionable(self) -> None:
        for failure in (urllib.error.URLError("unreachable"), TimeoutError("timed out")):
            with self.subTest(failure=failure):
                def opener(*args: Any, **kwargs: Any) -> FakeResponse:
                    raise failure
                code, _ = self.run_command(["fetch", "--repo", "example/project"], opener=opener)
                self.assert_clean_error(code)
        for response in ("not json", "{}", "[]", b"\xff"):
            with self.subTest(response=response):
                code, _ = self.run_command(
                    ["fetch", "--repo", "example/project"],
                    opener=lambda *args, **kwargs: FakeResponse(response),
                )
                self.assert_clean_error(code)

    def test_output_write_failure_returns_a_clean_error(self) -> None:
        blocker = self.root / "file"
        blocker.write_text("not a directory", encoding="utf-8")
        code, _, _ = self.fetch_document(result_document(), "file/result.json")
        self.assert_clean_error(code)


class ComparisonTest(ControllerTestCase):
    def test_published_comparison_reports_provided_aggregate_delta(self) -> None:
        before = result_document({"License": 5, "Signed-Releases": -1}, reported=4.2)
        after = result_document({"License": 10, "Signed-Releases": -1}, reported=4.7)
        after["repo"]["commit"] = "c" * 40
        after["date"] = "2026-09-02T00:00:00Z"
        code, payload = self.compare_documents(before, after)
        self.assertEqual(0, code, self.stderr)
        self.assertEqual("diff_computed", payload["state"])
        self.assertTrue(payload["comparable"])
        self.assertAlmostEqual(0.5, payload["reported_score_delta"])
        self.assertEqual(["License"], [row["check"] for row in payload["changed"]])
        row = payload["changed"][0]
        self.assertEqual(5, row["before"])
        self.assertEqual(10, row["after"])
        self.assertEqual(5, row["delta"])
        self.assertEqual("scored", row["before_state"])
        self.assertEqual("scored", row["after_state"])
        self.assertEqual("c" * 40, payload["after"]["commit"])

    def test_missing_reported_scores_have_no_aggregate_delta(self) -> None:
        before = result_document(reported=None)
        after = result_document(reported=8.0)
        code, payload = self.compare_documents(before, after)
        self.assertEqual(0, code, self.stderr)
        self.assertIsNone(payload["reported_score_delta"])

    def test_changed_version_or_scanner_commit_blocks_aggregate_comparison(self) -> None:
        for field, value in (("version", "v6.0.0"), ("commit", "d" * 40)):
            with self.subTest(field=field):
                before = result_document(reported=4.2)
                after = result_document(reported=5.0)
                after["scorecard"][field] = value
                code, payload = self.compare_documents(before, after)
                self.assertEqual(0, code, self.stderr)
                self.assertFalse(payload["comparable"])
                self.assertIsNone(payload["reported_score_delta"])
                self.assertTrue(payload["notes"])

    def test_unidentified_development_builds_are_not_comparable(self) -> None:
        for engine in ({"version": "devel"}, {"version": "devel", "commit": "unknown"}):
            with self.subTest(engine=engine):
                before, after = result_document(), result_document(reported=5.0)
                for document in (before, after):
                    document["scorecard"] = engine
                code, payload = self.compare_documents(before, after, published=False)
                self.assertEqual(0, code, self.stderr)
                self.assertFalse(payload["comparable"])
                self.assertIsNone(payload["reported_score_delta"])

    def test_named_versions_without_hashes_can_be_compared(self) -> None:
        before, after = result_document(), result_document()
        for document in (before, after):
            del document["scorecard"]["commit"]
        code, payload = self.compare_documents(before, after)
        self.assertEqual(0, code, self.stderr)
        self.assertTrue(payload["comparable"])

    def test_matching_development_hashes_identify_comparable_scanner_builds(self) -> None:
        before, after = result_document(), result_document()
        for document in (before, after):
            document["scorecard"]["version"] = "devel"
        code, payload = self.compare_documents(before, after)
        self.assertEqual(0, code, self.stderr)
        self.assertTrue(payload["comparable"])

    def test_older_result_does_not_claim_post_change_verification(self) -> None:
        before, after = result_document(), result_document(reported=5.0)
        after["date"] = "2026-08-01T00:00:00Z"
        code, payload = self.compare_documents(before, after)
        self.assertEqual(0, code, self.stderr)
        self.assertIsNone(payload["reported_score_delta"])
        self.assertTrue(payload["notes"])

    def test_same_snapshot_reports_that_new_verification_is_pending(self) -> None:
        code, payload = self.compare_documents(result_document(), result_document())
        self.assertEqual(0, code, self.stderr)
        self.assertEqual([], payload["changed"])
        self.assertTrue(payload["notes"])

    def test_imported_and_published_results_do_not_imply_an_aggregate_delta(self) -> None:
        code, _, before_path = self.fetch_document(result_document())
        self.assertEqual(0, code, self.stderr)
        after_path = self.write_document(result_document(reported=5.0))
        code, payload = self.run_command(
            ["diff", "--before", str(before_path), "--after", str(after_path)]
        )
        self.assertEqual(0, code, self.stderr)
        self.assertFalse(payload["comparable"])
        self.assertIsNone(payload["reported_score_delta"])
        self.assertTrue(payload["notes"])

    def test_imported_diagnostics_compare_with_explicit_evidence_limits(self) -> None:
        for repo in ("github.com/example/project", "file:///tmp/project"):
            with self.subTest(repo=repo):
                before, after = result_document(), result_document(reported=5.0)
                before["repo"]["name"] = after["repo"]["name"] = repo
                code, payload = self.compare_documents(before, after, published=False)
                self.assertEqual(0, code, self.stderr)
                self.assertTrue(payload["comparable"])
                self.assertAlmostEqual(0.8, payload["reported_score_delta"])
                self.assertIn("import", " ".join(payload["notes"]).lower())

    def test_changed_check_coverage_distinguishes_absent_from_inconclusive(self) -> None:
        before = result_document({"License": 10, "Signed-Releases": -1})
        after = result_document({"License": 10, "New-Check": 0})
        code, payload = self.compare_documents(before, after)
        self.assertEqual(0, code, self.stderr)
        self.assertFalse(payload["comparable"])
        self.assertIsNone(payload["reported_score_delta"])
        changes = {row["check"]: row for row in payload["changed"]}
        self.assertEqual("absent", changes["New-Check"]["before_state"])
        self.assertEqual("scored", changes["New-Check"]["after_state"])
        self.assertEqual("inconclusive", changes["Signed-Releases"]["before_state"])
        self.assertEqual("absent", changes["Signed-Releases"]["after_state"])
        for row in changes.values():
            self.assertIsNone(row["delta"])
        self.assertTrue(payload["notes"])

    def test_inconclusive_transition_is_not_reported_as_numerical_improvement(self) -> None:
        before = result_document({"Signed-Releases": -1})
        after = result_document({"Signed-Releases": 0})
        code, payload = self.compare_documents(before, after)
        self.assertEqual(0, code, self.stderr)
        self.assertFalse(payload["comparable"])
        self.assertIsNone(payload["reported_score_delta"])
        row = payload["changed"][0]
        self.assertIsNone(row["before"])
        self.assertEqual(0, row["after"])
        self.assertIsNone(row["delta"])
        self.assertEqual("inconclusive", row["before_state"])

    def test_changed_evidence_is_visible_even_when_score_does_not_change(self) -> None:
        for field, value in (
            ("reason", "different failure"),
            ("details", ["new.yml:9"]),
            ("documentation", {"url": "https://example.org/updated-check"}),
            ("annotations", ["new context"]),
        ):
            with self.subTest(field=field):
                before, after = result_document(), result_document()
                after["checks"][0][field] = value
                code, payload = self.compare_documents(before, after)
                self.assertEqual(0, code, self.stderr)
                self.assertEqual(["License"], [row["check"] for row in payload["changed"]])
                self.assertEqual(0, payload["changed"][0]["delta"])
                self.assertEqual(after["checks"][0]["reason"], payload["changed"][0]["reason_after"])
                self.assertEqual(value, payload["changed"][0][f"{field}_after"])

    def test_cross_repository_diagnostics_do_not_imply_a_badge_delta(self) -> None:
        before, after = result_document(), result_document(reported=5.0)
        after["repo"]["name"] = "github.com/another/project"
        code, payload = self.compare_documents(before, after, published=False)
        self.assertEqual(0, code, self.stderr)
        self.assertFalse(payload["comparable"])
        self.assertIsNone(payload["reported_score_delta"])
        self.assertIn("repo", " ".join(payload["notes"]).lower())

    def test_case_equivalent_github_results_compare_without_changing_metadata(self) -> None:
        before, after = result_document(), result_document(reported=5.0)
        before["repo"]["name"] = "github.com/Example/Project"
        after["date"] = "2026-09-02T00:00:00Z"
        after["repo"]["commit"] = "c" * 40
        code, payload = self.compare_documents(before, after)

        self.assertEqual(0, code, self.stderr)
        self.assertTrue(payload["comparable"])
        self.assertAlmostEqual(0.8, payload["reported_score_delta"])
        for label, original in (("before", before), ("after", after)):
            self.assertEqual(original["repo"]["name"], payload[label]["repo"])
            saved = json.loads((self.root / f"{label}.json").read_text(encoding="utf-8"))
            self.assertEqual(original["repo"], saved["repo"])

    def test_explicit_github_import_identities_share_normalization(self) -> None:
        for identity in (
            "https://GitHub.com/Example/Project.git",
            "ssh://git@github.com/Example/Project.git",
            "git@github.com:Example/Project.git",
        ):
            with self.subTest(identity=identity):
                before, after = result_document(), result_document(reported=5.0)
                before["repo"]["name"] = identity
                code, payload = self.compare_documents(before, after, published=False)
                self.assertEqual(0, code, self.stderr)
                self.assertTrue(payload["comparable"])
                self.assertAlmostEqual(0.8, payload["reported_score_delta"])
                self.assertEqual(identity, payload["before"]["repo"])

    def test_non_github_import_identities_retain_exact_comparison(self) -> None:
        for old_name, new_name in (
            ("file:///tmp/Project", "file:///tmp/project"),
            ("Example/Project", "example/project"),
            ("example/project", "github.com/example/project"),
            ("https://example.org/Example/Project", "https://example.org/example/project"),
            ("gitlab.com/Example/Project", "gitlab.com/example/project"),
            ("github.com/Example/Project", "github.com/Example/Other"),
        ):
            with self.subTest(before=old_name, after=new_name):
                before, after = result_document(), result_document(reported=5.0)
                before["repo"]["name"], after["repo"]["name"] = old_name, new_name
                code, payload = self.compare_documents(before, after, published=False)
                self.assertEqual(0, code, self.stderr)
                self.assertFalse(payload["comparable"])
                self.assertIsNone(payload["reported_score_delta"])
                self.assertEqual(old_name, payload["before"]["repo"])
                self.assertEqual(new_name, payload["after"]["repo"])

    def test_stdin_can_supply_one_side_but_not_both(self) -> None:
        before = self.write_document(result_document())
        code, payload = self.run_command(
            ["diff", "--before", str(before), "--after", "-"],
            stdin=json.dumps(result_document()),
        )
        self.assertEqual(0, code, self.stderr)
        self.assertEqual([], payload["changed"])
        code, _ = self.run_command(
            ["diff", "--before", "-", "--after", "-"], stdin=json.dumps(result_document()),
        )
        self.assert_clean_error(code)


class CommandSurfaceTest(ControllerTestCase):
    def test_controller_can_be_executed_directly(self) -> None:
        completed = subprocess.run(
            [str(REPOSITORY_ROOT / "scripts" / "scorecard.py"), "--help"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        for command in ("fetch", "explain", "diff"):
            self.assertIn(command, completed.stdout)

    def test_required_inputs_and_unsupported_acquisition_options_fail_cleanly(self) -> None:
        for argv in (
            [], ["fetch"], ["explain"], ["diff", "--before", "missing.json"],
            ["fetch", "--repo", "example/project", "--checks", "License"],
            ["fetch", "--local", "."],
        ):
            with self.subTest(argv=argv):
                code, _ = self.run_command(argv)
                self.assert_clean_error(code)


if __name__ == "__main__":
    unittest.main()
