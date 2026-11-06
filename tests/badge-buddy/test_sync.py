"""Tests for project resolution and read-only assessment synchronization."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "plugins" / "badge-buddy" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from ossf_review.storage import DataStore  # noqa: E402
from ossf_review.sync import (  # noqa: E402
    BestPracticesClient,
    ProjectResolutionError,
    UnregisteredProjectError,
    discover_repository,
    load_repository_assessment,
    resolve_project,
    SyncConflict,
    synchronize_project,
)


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._stream = BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *unused: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)


class FakePublicClient:
    def __init__(
        self,
        *,
        project_id: str | None = None,
        project: dict[str, object] | None = None,
    ) -> None:
        self.project_id = project_id
        self.project = project or {}
        self.lookup_calls: list[str] = []
        self.fetch_calls: list[str] = []

    def lookup_project_id(self, remote: str) -> str | None:
        self.lookup_calls.append(remote)
        return self.project_id

    def fetch_project(self, project_id: str) -> dict[str, object]:
        self.fetch_calls.append(project_id)
        return dict(self.project)


class SyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.repository = self.root / "repo"
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
                "git@github.com:Example/Project.git",
            ],
            check=True,
            capture_output=True,
        )
        self.store = DataStore(self.root / "data")

    def test_invalid_refresh_preserves_snapshot_and_local_answers(self) -> None:
        document = {"repo_url": "https://github.com/example/project", "interact_status": "Met"}
        client = FakePublicClient(project_id="31", project=document)
        synchronize_project(self.store, self.repository, client=client)
        original = self.store.load_public_snapshot("31", "https://github.com/example/project")
        self.store.update_assessment("31", {"interact_status": "?"})
        client.project = {"repo_url": "https://github.com/example/other"}
        with self.assertRaises(ProjectResolutionError):
            synchronize_project(self.store, self.repository, client=client)
        self.assertEqual(original, self.store.load_public_snapshot(
            "31", "https://github.com/example/project"
        ))
        with patch.object(client, "fetch_project", side_effect=ProjectResolutionError("unavailable")):
            with self.assertRaises(ProjectResolutionError):
                synchronize_project(self.store, self.repository, client=client)
        offline = synchronize_project(DataStore(self.root / "data"), self.repository)
        self.assertEqual(document, offline.public_document)
        self.assertEqual("?", offline.assessment["interact_status"])
        self.assertEqual((), offline.conflicts)
        self.assertFalse(offline.public_loaded)
        self.assertEqual(original["fetched_at"], offline.public_fetched_at)

    def test_discovers_root_and_normalizes_origin_via_git_c(self) -> None:
        nested = self.repository / "nested"
        nested.mkdir()

        identity = discover_repository(nested)

        self.assertEqual(self.repository.resolve(), identity.root)
        self.assertEqual("github.com/example/project", identity.remote)
        self.assertEqual("https://github.com/Example/Project", identity.url)
        self.assertEqual("repo", identity.project_name)

    def test_registry_is_consulted_before_public_lookup(self) -> None:
        self.store.register_project(42, "https://github.com/example/project")
        client = FakePublicClient(project_id="99")

        resolution = resolve_project(self.store, self.repository, client=client)

        self.assertEqual("42", resolution.identifier)
        self.assertEqual([], client.lookup_calls)

    def test_public_lookup_is_registered_only_after_synchronization_validates_it(self) -> None:
        client = FakePublicClient(
            project_id="77", project={"repo_url": "https://github.com/Example/Project"},
        )

        resolution = resolve_project(self.store, self.repository, client=client)

        self.assertTrue(resolution.registered)
        self.assertEqual("77", resolution.project_id)
        self.assertEqual(["https://github.com/Example/Project"], client.lookup_calls)
        self.assertIsNone(self.store.resolve_project_id("github.com/example/project"))
        result = synchronize_project(self.store, self.repository, client=client)
        self.assertEqual("77", result.resolution.project_id)
        self.assertEqual(
            "77",
            self.store.resolve_project_id("https://github.com/example/project"),
        )

    def test_rejected_project_selection_preserves_mappings_and_assessments(self) -> None:
        bad_identity = {
            "mismatch": {"repo_url": "https://github.com/example/other"},
            "homepage_mismatch": {"repo_url": "", "homepage_url": "https://github.com/example/other"},
            "homepage_cannot_override_repo": {
                "repo_url": "https://github.com/example/other",
                "homepage_url": "https://github.com/example/project",
            },
            "missing_identity": {},
            "unverifiable_identity": {"homepage_url": "https://example.org"},
        }
        for failure in (*bad_identity, "fetch", "discovery"):
            with self.subTest(failure=failure):
                store = DataStore(self.root / failure)
                first_remote = ("github.com/example/old" if failure == "discovery"
                                else "github.com/example/project")
                store.register_project("1", first_remote)
                store.register_project("2", "github.com/example/other")
                for identifier, status in (("1", "Met"), ("2", "Unmet")):
                    store.save_assessment(identifier, {"description_good_status": status})
                original_registry = store.registry_path.read_bytes()
                client = FakePublicClient(
                    project_id="2", project=bad_identity.get(failure, bad_identity["mismatch"]),
                )
                if failure == "fetch":
                    client.fetch_project = Mock(
                        side_effect=ProjectResolutionError("public fetch failed")
                    )
                with self.assertRaises(ProjectResolutionError):
                    synchronize_project(
                        store, self.repository, client=client,
                        project_id=None if failure == "discovery" else "2",
                    )
                self.assertEqual(original_registry, store.registry_path.read_bytes())
                self.assertEqual("1", store.resolve_project_id(first_remote))
                self.assertEqual("2", store.resolve_project_id("github.com/example/other"))
                self.assertEqual({"description_good_status": "Met"}, store.load_assessment("1"))
                self.assertEqual({"description_good_status": "Unmet"}, store.load_assessment("2"))

                # A verified selection can still deliberately replace a mapping.
                verified = FakePublicClient(project={"repo_url": "https://github.com/Example/Project"})
                result = synchronize_project(store, self.repository, project_id="2", client=verified)
                self.assertEqual("2", result.resolution.project_id)
                self.assertEqual("2", store.resolve_project_id("github.com/example/project"))
                self.assertIsNone(store.resolve_project_id("github.com/example/other"))
                self.assertEqual({"description_good_status": "Unmet"}, result.assessment)

    def test_online_status_accepts_matching_homepage_only_identity(self) -> None:
        client = FakePublicClient(project_id="77", project={
            "repo_url": "", "homepage_url": "https://github.com/EXAMPLE/Project",
        })
        result = synchronize_project(self.store, self.repository, client=client)
        self.assertEqual("77", result.resolution.project_id)
        self.assertEqual("77", self.store.resolve_project_id("github.com/example/project"))
        self.assertEqual(["77"], client.fetch_calls)

    def test_unregistered_requires_explicit_opt_in_and_gets_own_file(self) -> None:
        with self.assertRaises(UnregisteredProjectError):
            resolve_project(self.store, self.repository)

        resolution = resolve_project(
            self.store,
            self.repository,
            allow_unregistered=True,
        )

        self.assertFalse(resolution.registered)
        self.assertTrue(resolution.identifier.startswith("unregistered:"))
        record = self.store.load_unregistered(self.repository)
        self.assertIsNotNone(record)
        assessment_path = (
            self.root
            / "data"
            / "unregistered"
            / str(record["storage_key"])
            / ".bestpractices.json"
        )
        self.assertTrue(assessment_path.is_file())

    def test_case_variant_discovery_syncs_once_and_reuses_numeric_registration(self) -> None:
        document = {
            "id": 14356,
            "repo_url": "https://github.com/EXAMPLE/Project",
            "description_good_status": "Met",
        }
        responses = iter(([document], [], [], document))
        urls = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            urls.append(request.full_url)
            return FakeResponse(next(responses))

        client = BestPracticesClient(opener=opener, minimum_interval=0)
        result = synchronize_project(self.store, self.repository, client=client)
        self.assertEqual("14356", result.resolution.project_id)
        self.assertEqual("Met", result.assessment["description_good_status"])
        self.assertEqual("https://github.com/Example/Project", result.resolution.repository.url)
        self.assertEqual("14356", self.store.resolve_project_id("github.com/example/project"))
        self.assertEqual(4, len(urls))

        cached = FakePublicClient(project=document)
        repeated = synchronize_project(self.store, self.repository, client=cached)
        self.assertEqual("14356", repeated.resolution.project_id)
        self.assertEqual([], cached.lookup_calls)
        self.assertEqual(["14356"], cached.fetch_calls)

    def test_registration_carries_local_answers_and_partial_evidence(self) -> None:
        draft = {
            "description_good_status": "Met",
            "description_good_justification": "First paragraph.\n\nSecond paragraph.\n",
            "contribution_status": "?",
            "contribution_justification": "Draft instructions, still investigating.",
            "sites_https_justification": "",
        }
        for route in ("discovery", "explicit", "cached"):
            with self.subTest(route=route):
                store = DataStore(self.root / route)
                local = resolve_project(store, self.repository, allow_unregistered=True)
                store.save_assessment(local.identifier, draft)
                if route == "cached":
                    store.register_project("77", "github.com/example/project")
                    store.save_assessment("77", {"maintained_status": "Met"})
                client = FakePublicClient(project_id="77", project={
                    "repo_url": "https://github.com/example/project",
                    "description_good_status": "?",
                    "interact_status": "Met",
                })
                result = synchronize_project(
                    store, self.repository, client=client,
                    project_id="77" if route == "explicit" else None,
                )
                expected = {**draft, "interact_status": "Met"}
                if route == "cached":
                    expected["maintained_status"] = "Met"
                self.assertEqual(expected, result.assessment)
                self.assertEqual((SyncConflict(
                    "description_good_status", "Met", "?", "public API",
                ),), result.conflicts)
                self.assertIsNone(store.load_unregistered(self.repository))
                self.assertEqual({}, store.load_assessment(local.identifier))
                self.assertEqual(expected, synchronize_project(
                    store, self.repository, client=client,
                ).assessment)

    def test_failed_public_validation_leaves_local_draft_available(self) -> None:
        local = resolve_project(self.store, self.repository, allow_unregistered=True)
        draft = {"description_good_status": "Met"}
        self.store.save_assessment(local.identifier, draft)
        client = FakePublicClient(project={"repo_url": "https://github.com/other/repo"})
        with self.assertRaises(ProjectResolutionError):
            synchronize_project(self.store, self.repository, project_id="77", client=client)
        self.assertEqual(draft, self.store.load_assessment(local.identifier))
        self.assertIsNotNone(self.store.load_unregistered(self.repository))

    def test_root_repository_assessment_wins_location_selection(self) -> None:
        root_file = self.repository / ".bestpractices.json"
        root_file.write_text('{"root_status": "Met"}', encoding="utf-8")
        fallback = self.repository / ".project.d" / "bestpractices.json"
        fallback.parent.mkdir()
        fallback.write_text('{"fallback_status": "Met"}', encoding="utf-8")

        selected, assessment = load_repository_assessment(self.repository)

        self.assertEqual(root_file, selected)
        self.assertEqual({"root_status": "Met"}, assessment)

    def test_sync_preserves_real_plugin_values_and_reports_conflicts(self) -> None:
        self.store.register_project(8, "https://github.com/example/project")
        self.store.save_assessment(
            8,
            {
                "description_good_status": "Met",
                "description_good_justification": "Current user evidence",
            },
        )
        client = FakePublicClient(
            project={
                "repo_url": "https://github.com/example/project",
                "description_good_status": "Unmet",
                "description_good_justification": "Public explanation",
                "contribution_status": "Met",
                "OSPS-AC-01.01_status": "Met",
                "badge_percentage_0": 99,
            }
        )

        result = synchronize_project(self.store, self.repository, client=client)

        self.assertEqual("Met", result.assessment["description_good_status"])
        self.assertEqual(
            "Current user evidence",
            result.assessment["description_good_justification"],
        )
        self.assertEqual("Met", result.assessment["contribution_status"])
        self.assertEqual("Met", result.assessment["osps_ac_01_01_status"])
        self.assertNotIn("badge_percentage_0", result.assessment)
        self.assertEqual((
            SyncConflict("description_good_status", "Met", "Unmet", "public API"),
            SyncConflict("description_good_justification", "Current user evidence",
                         "Public explanation", "public API"),
        ), result.conflicts)

    def test_cleared_answers_survive_later_reads_until_explicitly_reconciled(self) -> None:
        public = {
            "description_good_status": "Met",
            "description_good_justification": "Previous explanation",
        }
        client = FakePublicClient(project_id="12", project={
            "repo_url": "https://github.com/example/project", **public,
        })
        synchronize_project(self.store, self.repository, client=client)
        correction = {
            "description_good_status": "?",
            "description_good_justification": "",
        }
        self.store.update_assessment("12", correction)
        result = synchronize_project(self.store, self.repository, client=client)
        self.assertEqual(correction, result.assessment)
        self.assertEqual(correction, self.store.load_assessment("12"))
        self.assertEqual(tuple(
            SyncConflict(field, correction[field], value, "public API")
            for field, value in public.items()
        ), result.conflicts)

        synchronize_project(self.store, self.repository, client=client, user_updates=public)
        reconciled = synchronize_project(self.store, self.repository, client=client)
        self.assertEqual(public, reconciled.assessment)
        self.assertEqual((), reconciled.conflicts)

    def test_import_initializes_absent_answers_without_combining_partial_answers(self) -> None:
        self.store.register_project("12", "github.com/example/project")
        local = {"description_good_justification": "Local unfinished explanation"}
        self.store.save_assessment("12", local)
        new_answer = {
            "contribution_status": "?",
            "contribution_justification": "Public unfinished explanation",
        }
        client = FakePublicClient(project={
            "repo_url": "https://github.com/example/project",
            **new_answer,
            "description_good_status": "Met",
            "description_good_justification": "",
        })
        result = synchronize_project(self.store, self.repository, client=client)
        self.assertEqual({**local, **new_answer}, result.assessment)
        self.assertEqual((
            SyncConflict("description_good_status", None, "Met", "public API"),
            SyncConflict("description_good_justification", local["description_good_justification"],
                         "", "public API"),
        ), result.conflicts)

    def test_current_session_user_updates_always_win(self) -> None:
        self.store.register_project(12, "https://github.com/example/project")
        repository_file = self.repository / ".bestpractices.json"
        repository_file.write_text(
            json.dumps({"description_good_status": "Met"}),
            encoding="utf-8",
        )
        self.store.use_assessment_file(repository_file)
        client = FakePublicClient(
            project={
                "repo_url": "https://github.com/example/project",
                "description_good_status": "Unmet",
            }
        )

        result = synchronize_project(
            self.store,
            self.repository,
            client=client,
            user_updates={
                "description_good_status": "Unmet",
                "description_good_justification": "User corrected this now",
            },
        )

        self.assertEqual("Unmet", result.assessment["description_good_status"])
        self.assertEqual(
            "User corrected this now",
            result.assessment["description_good_justification"],
        )
        self.assertEqual(
            result.assessment,
            json.loads(repository_file.read_text(encoding="utf-8")),
        )


class BestPracticesClientTest(unittest.TestCase):
    def lookup_client(self, responses: list[object]):
        pending = iter(responses)
        requests = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            requests.append(parse_qs(urlsplit(request.full_url).query))
            response = next(pending)
            if isinstance(response, Exception):
                raise response
            return FakeResponse(response)

        return BestPracticesClient(opener=opener, minimum_interval=0), requests

    def test_filtered_lookup_and_fetch_are_sequential_and_identified(self) -> None:
        requests = []
        responses = iter(
            (
                [
                    {
                        "id": 5,
                        "repo_url": "https://github.com/Example/Project.git",
                    },
                    {"id": 9, "repo_url": "https://github.com/other/project"},
                ],
                [],
                [],
                {"id": 5, "description_good_status": "Met"},
            )
        )
        sleeps: list[float] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            requests.append((request, timeout))
            return FakeResponse(next(responses))

        client = BestPracticesClient(
            opener=opener,
            clock=lambda: 0.0,
            sleeper=sleeps.append,
        )

        identifier = client.lookup_project_id("github.com/example/project")
        project = client.fetch_project(identifier or "")

        self.assertEqual("5", identifier)
        self.assertEqual("Met", project["description_good_status"])
        self.assertEqual([1.0, 1.0, 1.0], sleeps)
        self.assertEqual(4, len(requests))
        first_request = requests[0][0]
        self.assertEqual("GET", first_request.get_method())
        self.assertIn(
            "pq=https%3A%2F%2Fgithub.com%2Fexample%2Fproject", first_request.full_url
        )
        self.assertEqual(
            "badge-buddy/1 (+https://github.com/reponomics/plugins)",
            first_request.get_header("User-agent"),
        )

    def test_case_insensitive_candidates_are_exactly_filtered_across_pages(self) -> None:
        stored = "https://github.com/Reponomics/PolicyChecks"
        client, requests = self.lookup_client([
            [
                {"id": 10, "repo_url": stored + "-tools"},
                {"id": 11, "homepage_url": stored, "repo_url": "https://github.com/other/repo"},
            ],
            [{"id": 14356, "repo_url": stored}],
            [{"id": "14356", "repo_url": stored + ".git"}],
            [],
            [],
        ])
        self.assertEqual("14356", client.lookup_project_id("git@github.com:reponomics/policychecks.git"))
        self.assertEqual(["1", "2", "3", "4", "1"], [q["page"][0] for q in requests])
        self.assertEqual("https://github.com/reponomics/policychecks", requests[0]["pq"][0])
        self.assertTrue(all(q["sort"] == ["id"] and q["sort_direction"] == ["asc"] for q in requests))

    def test_different_case_entries_are_ambiguous_even_on_later_pages(self) -> None:
        client, _ = self.lookup_client([
            [{"id": 1, "repo_url": "https://github.com/example/project"}],
            [{"id": 2, "repo_url": "https://github.com/Example/Project"}],
            [], [],
        ])
        with self.assertRaisesRegex(ProjectResolutionError, "multiple project ids: 1, 2"):
            client.lookup_project_id("github.com/example/project")

    def test_http_entry_is_found_without_contacting_the_repository(self) -> None:
        client, requests = self.lookup_client([
            [], [{"id": 1, "repo_url": "http://github.com/Example/Project"}], [],
        ])
        self.assertEqual("1", client.lookup_project_id("github.com/example/project"))
        self.assertEqual("http://github.com/example/project", requests[1]["pq"][0])

    def test_homepage_only_registration_is_supported(self) -> None:
        client, _ = self.lookup_client([
            [{"id": 1, "repo_url": "", "homepage_url": "https://github.com/Example/Project"}], [], [],
        ])
        self.assertEqual("1", client.lookup_project_id("github.com/example/project"))

    def test_complete_empty_search_returns_no_match(self) -> None:
        client, requests = self.lookup_client([[], []])
        self.assertIsNone(client.lookup_project_id("github.com/example/project"))
        self.assertEqual(2, len(requests))

    def test_page_limit_never_accepts_a_partial_unique_match(self) -> None:
        client, _ = self.lookup_client([
            [{"id": 1, "repo_url": "https://github.com/example/project"}],
            [{"id": 2, "repo_url": "https://github.com/example/project-tools"}],
        ])
        with patch("ossf_review.sync.MAX_LOOKUP_PAGES", 2):
            with self.assertRaisesRegex(ProjectResolutionError, "incomplete.*--project-id"):
                client.lookup_project_id("github.com/example/project")

    def test_failed_later_page_is_not_a_successful_or_empty_lookup(self) -> None:
        client, _ = self.lookup_client([
            [{"id": 1, "repo_url": "https://github.com/example/project"}], URLError("offline"),
        ])
        with self.assertRaisesRegex(ProjectResolutionError, "public API read failed"):
            client.lookup_project_id("github.com/example/project")

    def test_malformed_results_do_not_become_registration_absence(self) -> None:
        for payload in ({"error": "bad response"}, ["invalid"], [{"id": True, "repo_url": "https://github.com/example/project"}]):
            with self.subTest(payload=payload):
                client, _ = self.lookup_client([payload])
                with self.assertRaises(ProjectResolutionError):
                    client.lookup_project_id("github.com/example/project")


if __name__ == "__main__":
    unittest.main()
