"""The only operation allowed to publish a draft must fail closed."""

from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import finalize_release as finalize


class FinalizationTests(unittest.TestCase):
    def setUp(self):
        self.repo = "fixture/plugins"
        self.tag = "release-buddy--v1.0.0"
        self.base = f"repos/{self.repo}"
        self.settings_enabled = True
        self.writes = []
        self.plugin = {
            "tag": self.tag,
            "object": "1" * 40,
            "head": "2" * 40,
            "name": "release-buddy",
            "version": "1.0.0",
            "prerelease": False,
        }
        hashes = dict.fromkeys(finalize.release.ASSETS, "sha256:" + "a" * 64)
        self.receipt = {**self.plugin, "draft_id": 12, "assets": hashes}
        self.record = {
            "id": 12,
            "tag_name": self.tag,
            "name": "release-buddy 1.0.0",
            "target_commitish": self.plugin["head"],
            "prerelease": False,
            "assets": [
                {"name": k, "digest": v, "state": "uploaded"} for k, v in hashes.items()
            ],
            "body": "Reviewed notes",
            "html_url": "https://example.invalid/release",
            "draft": True,
            "immutable": False,
        }
        for module, name, kwargs in [
            (finalize, "load_receipt", {"return_value": self.receipt}),
            (finalize.release, "verify_tag", {"return_value": self.plugin}),
            (finalize.release, "check_remote_ref", {}),
            (finalize.release, "release_notes", {"return_value": "Reviewed notes\n"}),
            (finalize.release, "run", {}),
            (finalize.release, "api", {"side_effect": self.api}),
        ]:
            self.enter_patch(module, name, kwargs)

    def enter_patch(self, module, name, kwargs):
        patch = mock.patch.object(module, name, **kwargs)
        patch.start()
        self.addCleanup(patch.stop)

    def api(self, endpoint, *args):
        if endpoint.endswith("/actions/variables/RELEASE_REPOSITORY"):
            return {"value": self.repo}
        if endpoint.endswith("/actions/variables/RELEASE_ALLOWED_SIGNERS"):
            return {"value": "public fixture key"}
        if endpoint.endswith("/immutable-releases"):
            return {"enabled": self.settings_enabled}
        self.assertEqual(endpoint, self.base + "/releases/12")
        if args:
            self.assertIn("PATCH", args)
            self.assertIn("draft=false", args)
            self.writes.append(endpoint)
            self.record.update(draft=False, immutable=True)
        return self.record.copy()

    def finish(self):
        finalize.finalize(self.repo, self.tag, "1234")

    def test_publish_and_retry_preserve_same_verified_release(self):
        self.finish()
        self.finish()
        self.assertEqual(self.writes, [self.base + "/releases/12"])
        finalize.release.run.assert_called_with(
            "gh", "release", "verify", self.tag, "--repo", self.repo
        )

    def test_changed_asset_is_rejected_before_publication(self):
        self.record["assets"][0]["digest"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(ValueError, "assets"):
            self.finish()
        self.assertFalse(self.writes)

    def test_disabled_immutability_leaves_draft_intact(self):
        self.settings_enabled = False
        with self.assertRaisesRegex(ValueError, "immutability"):
            self.finish()
        self.assertFalse(self.writes)

    def test_retagged_object_at_same_commit_is_rejected(self):
        self.receipt["object"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "signed tag"):
            self.finish()
        self.assertFalse(self.writes)


class PreparationRunTests(unittest.TestCase):
    repo = "fixture/plugins"
    tag = "release-buddy--v1.0.0"

    def test_short_ref_named_main_cannot_supply_an_off_branch_receipt(self):
        run = {
            "path": ".github/workflows/release.yml",
            "event": "workflow_dispatch",
            "head_branch": "main",
            "display_title": f"Prepare {self.tag}",
            "conclusion": "success",
            "status": "completed",
            "head_sha": "3" * 40,
        }
        with mock.patch.object(
            finalize.release, "api", side_effect=[run, {"status": "diverged"}]
        ):
            with self.assertRaisesRegex(ValueError, "workflow commit"):
                finalize.load_receipt(self.repo, "1", self.tag, Path("unused"))

    def test_another_workflow_or_failed_run_cannot_supply_evidence(self):
        good = {
            "path": ".github/workflows/release.yml",
            "event": "workflow_dispatch",
            "head_branch": "main",
            "display_title": "Prepare " + self.tag,
            "conclusion": "success",
            "status": "completed",
        }
        for key, value in (
            ("path", "other.yml"),
            ("conclusion", "failure"),
            ("head_branch", "feature"),
            ("display_title", "Prepare other--v1.0.0"),
            ("event", "pull_request"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                finalize.check_run({**good, key: value}, self.tag)
