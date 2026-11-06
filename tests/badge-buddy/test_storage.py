"""Tests for the OpenSSF review persistent storage layer."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "plugins" / "badge-buddy" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from ossf_review.storage import (  # noqa: E402
    DataStore,
    github_repository_url,
    normalize_github_remote,
)
from ossf_review import storage  # noqa: E402


class NormalizeGithubRemoteTest(unittest.TestCase):
    def test_supported_spellings_have_one_identity(self) -> None:
        remotes = (
            "https://github.com/OpenSSF/Best-Practices-Badge.git",
            "https://github.com/OpenSSF/Best-Practices-Badge/",
            "http://github.com/OpenSSF/Best-Practices-Badge/",
            "ssh://git@github.com/OpenSSF/Best-Practices-Badge.git",
            "git@github.com:OpenSSF/Best-Practices-Badge.git",
            "github.com/OpenSSF/Best-Practices-Badge",
        )

        identities = {normalize_github_remote(remote) for remote in remotes}

        self.assertEqual(
            {"github.com/openssf/best-practices-badge"},
            identities,
        )
        self.assertEqual(
            {"https://github.com/OpenSSF/Best-Practices-Badge"},
            {github_repository_url(remote) for remote in remotes},
        )

    def test_preserved_url_and_lowercase_key_remain_distinct(self) -> None:
        remote = "ssh://git@GitHub.com/Reponomics/PolicyChecks.git"
        self.assertEqual(
            "https://github.com/Reponomics/PolicyChecks", github_repository_url(remote)
        )
        self.assertEqual("github.com/reponomics/policychecks", normalize_github_remote(remote))

    def test_non_repository_remote_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_github_remote("https://gitlab.com/OpenSSF/project")
        with self.assertRaises(ValueError):
            normalize_github_remote("https://github.com/OpenSSF/project/issues")


class DataStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.data_dir = Path(self.temporary_directory.name) / "review-data"
        self.store = DataStore(self.data_dir)

    def test_public_snapshot_is_separate_from_selected_assessment_and_bound_to_origin(self) -> None:
        working = self.data_dir / "working.json"
        working.write_text('{"description_good_justification": "Private draft"}')
        self.store.use_assessment_file(working)
        document = {"description_good_status": "Met"}
        snapshot = self.store.save_public_snapshot(31, "git@github.com:Example/Project.git", document)
        reloaded = DataStore(self.data_dir)
        self.assertEqual(snapshot, reloaded.load_public_snapshot(
            31, "https://github.com/example/project"
        ))
        self.assertIsNone(reloaded.load_public_snapshot(31, "https://github.com/example/other"))
        self.assertIsNone(reloaded.load_public_snapshot(32, "https://github.com/example/project"))
        self.assertEqual({"description_good_justification": "Private draft"}, json.loads(working.read_text()))
        self.assertFalse((self.data_dir / "projects/31/.bestpractices.json").exists())

    def test_registry_roundtrip_and_reverse_lookup(self) -> None:
        identifier = self.store.register_project(
            14356,
            "git@github.com:Reponomics/PolicyChecks.git",
        )

        self.assertEqual("14356", identifier)
        self.assertEqual(
            "14356",
            self.store.resolve_project_id(
                "https://github.com/reponomics/policychecks/"
            ),
        )
        registry = json.loads(
            (self.data_dir / "registry.json").read_text(encoding="utf-8")
        )
        self.assertEqual(1, registry["schema_version"])
        self.assertEqual(
            "github.com/reponomics/policychecks",
            registry["by_id"]["14356"],
        )
        self.assertEqual(
            "14356",
            registry["by_remote"]["github.com/reponomics/policychecks"],
        )
        self.assertEqual({}, registry["unregistered"])
        self.assertEqual(
            {},
            json.loads(
                (
                    self.data_dir / "projects" / "14356" / ".bestpractices.json"
                ).read_text(encoding="utf-8")
            ),
        )

    def test_updating_mapping_removes_stale_forward_and_reverse_entries(self) -> None:
        self.store.register_project(1, "https://github.com/example/old")
        self.store.register_project(1, "https://github.com/example/new")

        self.assertIsNone(
            self.store.resolve_project_id("https://github.com/example/old")
        )
        self.assertEqual(
            "1",
            self.store.resolve_project_id("git@github.com:example/new.git"),
        )

    def test_assessment_save_and_nested_merge(self) -> None:
        self.store.register_project(7, "https://github.com/example/project")
        self.store.save_assessment(
            7,
            {
                "description_good_status": "Met",
                "criteria": {
                    "description_good": {
                        "status": "Met",
                        "justification": "README",
                    }
                },
            },
        )

        result = self.store.update_assessment(
            7,
            {
                "contribution_status": "Unmet",
                "criteria": {"description_good": {"status": "Unmet"}},
            },
        )

        self.assertEqual("Met", result["description_good_status"])
        self.assertEqual("Unmet", result["contribution_status"])
        self.assertEqual(
            {
                "status": "Unmet",
                "justification": "README",
            },
            result["criteria"]["description_good"],
        )
        self.assertEqual(result, self.store.load_assessment(7))

    def test_concurrent_unrelated_updates_are_merged(self) -> None:
        self.store.register_project(9, "https://github.com/example/concurrent")
        stores = [DataStore(self.data_dir) for _ in range(8)]

        with ThreadPoolExecutor(max_workers=len(stores)) as executor:
            futures = [
                executor.submit(
                    store.update_assessment,
                    9,
                    {f"criterion_{index}_status": "Met"},
                )
                for index, store in enumerate(stores)
            ]
            for future in futures:
                future.result()

        assessment = self.store.load_assessment(9)
        self.assertEqual(
            {f"criterion_{index}_status" for index in range(len(stores))},
            set(assessment),
        )

    def test_unregistered_record_roundtrip(self) -> None:
        local_project = Path(self.temporary_directory.name) / "local-project"

        record = self.store.create_unregistered(
            local_project,
            remote="ssh://git@github.com/Example/Local.git",
            project_name="Local Project",
        )

        self.assertEqual(
            str(local_project.resolve()), record["local_project_directory"]
        )
        self.assertEqual("github.com/example/local", record["remote"])
        self.assertEqual("Local Project", record["project_name"])
        self.assertEqual("local-project", record["storage_key"])
        self.assertEqual(record, self.store.load_unregistered(local_project))
        identifier = self.store.unregistered_identifier(local_project)
        self.assertEqual("unregistered:local-project", identifier)
        self.assertEqual({}, self.store.load_assessment(identifier))
        self.store.update_assessment(
            identifier,
            {"description_good_status": "Met"},
        )
        self.assertEqual(
            {"description_good_status": "Met"},
            json.loads(
                (
                    self.data_dir
                    / "unregistered"
                    / "local-project"
                    / ".bestpractices.json"
                ).read_text(encoding="utf-8")
            ),
        )
        self.assertIsNone(
            self.store.load_unregistered(
                Path(self.temporary_directory.name) / "unknown"
            )
        )

    def test_unregistered_safe_keys_avoid_local_name_collisions(self) -> None:
        first = Path(self.temporary_directory.name) / "one" / "same name"
        second = Path(self.temporary_directory.name) / "two" / "same name"

        first_record = self.store.create_unregistered(first)
        second_record = self.store.create_unregistered(second)

        self.assertEqual("same-name", first_record["storage_key"])
        self.assertEqual("same-name-2", second_record["storage_key"])

    def test_local_handoff_retries_after_destination_or_registry_write_failure(self) -> None:
        local_directory = Path(self.temporary_directory.name) / "local-project"
        draft = {"description_good_status": "?", "description_good_justification": "Partial notes."}
        original_write = storage._atomic_write_json
        for fail_registry in (False, True):
            with self.subTest(fail_registry=fail_registry):
                store = DataStore(self.data_dir / str(fail_registry))
                store.create_unregistered(local_directory, remote="github.com/example/project")
                local_id = store.unregistered_identifier(local_directory)
                store.save_assessment(local_id, draft)
                store.register_project("31", "github.com/example/project")
                failed_path = (store.registry_path if fail_registry else
                               store.projects_dir / "31" / storage.ASSESSMENT_FILENAME)

                def fail_write(path, value):
                    if path == failed_path:
                        raise OSError("simulated write failure")
                    original_write(path, value)

                with patch.object(storage, "_atomic_write_json", side_effect=fail_write):
                    with self.assertRaises(OSError):
                        store.handoff_unregistered(local_directory, "31")
                preserved_id = "31" if fail_registry else local_id
                self.assertEqual(draft, store.load_assessment(preserved_id))
                self.assertIsNotNone(store.load_unregistered(local_directory))
                self.assertEqual((draft, {}), store.handoff_unregistered(local_directory, "31"))
                self.assertIsNone(store.load_unregistered(local_directory))
                self.assertEqual({}, store.load_assessment(local_id))

    def test_transform_assessment_receives_current_values(self) -> None:
        self.store.register_project(11, "https://github.com/example/transform")
        self.store.save_assessment(11, {"one_status": "Met"})

        result = self.store.transform_assessment(
            11,
            lambda current: {**current, "two_status": "Unmet"},
        )

        self.assertEqual(
            {"one_status": "Met", "two_status": "Unmet"},
            result,
        )


if __name__ == "__main__":
    unittest.main()
