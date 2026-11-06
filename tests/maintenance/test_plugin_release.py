"""Release policy, real signed Git objects and fail-closed draft preparation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import plugin_release as release


class GitFixture(unittest.TestCase):
    tag = "alpha--v1.0.0"

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.addCleanup(os.chdir, Path.cwd())
        os.chdir(self.repo)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Release fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "tag.gpgsign", "false")
        self.allow = self.root / "allowed_signers"
        self.manifest("1.0.0")
        self.write(
            ".claude-plugin/marketplace.json",
            json.dumps({"plugins": [{"name": "alpha", "source": "./plugins/alpha"}]}),
        )
        self.base = self.commit()
        self.git("update-ref", "refs/remotes/origin/main", self.base)

    @staticmethod
    def git(*args):
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.PIPE
        ).strip()

    @staticmethod
    def write(path, contents):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contents)

    def manifest(self, version, name="alpha"):
        self.write(
            f"plugins/{name}/.claude-plugin/plugin.json",
            json.dumps({"name": name, "version": version}),
        )
        self.write(
            f"docs/release-notes/{name}/{version}.md",
            "User-facing changes from this release.\n",
        )

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def key(self, name="release"):
        key = self.root / name
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)], check=True
        )
        return key

    def sign(self, tag=None):
        key = self.key()
        self.allow.write_text(
            'maintainer namespaces="git" ' + key.with_suffix(".pub").read_text()
        )
        self.git(
            "-c",
            "gpg.format=ssh",
            "-c",
            f"user.signingkey={key}",
            "tag",
            "-sm",
            "Release",
            tag or self.tag,
        )

    def test_initial_version_can_decrease_in_new_repo_only(self):
        self.manifest("0.1.0")
        self.commit()
        self.assertEqual(release.plan(self.base)["plugins"][0]["tag"], "alpha--v0.1.0")
        self.git("tag", "alpha--v0.4.0", self.base)
        with self.assertRaisesRegex(ValueError, "must increase"):
            release.plan(self.base)

    def test_version_rules_and_notes(self):
        self.manifest("1.0.0+metadata")
        self.commit()
        with self.assertRaisesRegex(ValueError, "must increase"):
            release.plan(self.base)
        self.manifest("1.1.0-beta.01")
        self.commit()
        with self.assertRaisesRegex(ValueError, "leading zeroes"):
            release.plan(self.base)
        self.manifest("1.1.0-beta.2")
        self.commit()
        self.assertTrue(release.plan(self.base)["plugins"][0]["prerelease"])
        path = Path("docs/release-notes/alpha/1.1.0-beta.2.md")
        path.unlink()
        self.commit()
        with self.assertRaisesRegex(ValueError, "missing regular reviewed"):
            release.plan(self.base)
        self.assertLess(
            release._precedence("1.1.0-beta.2"), release._precedence("1.1.0-beta.11")
        )
        self.assertLess(
            release._precedence("1.1.0-beta.11"), release._precedence("1.1.0")
        )

    def test_criteria_require_badge_version_change(self):
        self.write(
            ".claude-plugin/marketplace.json",
            json.dumps(
                {
                    "plugins": [
                        {"name": "badge-buddy", "source": "./plugins/badge-buddy"}
                    ]
                }
            ),
        )
        self.manifest("0.1.0", "badge-buddy")
        base = self.commit()
        self.write("plugins/badge-buddy/assets/criteria/criteria.json", "{}")
        self.commit()
        with self.assertRaisesRegex(ValueError, "without a plugin version bump"):
            release.plan(base)
        self.manifest("0.1.1", "badge-buddy")
        self.commit()
        self.assertEqual(release.plan(base)["plugins"][0]["tag"], "badge-buddy--v0.1.1")

    def test_signed_tag_verified_against_allowed_key_only(self):
        self.sign()
        result = release.verify_tag(self.tag, self.allow)
        self.assertEqual(result["head"], self.base)
        self.assertEqual(result["object"], self.git("rev-parse", self.tag))
        self.assertNotEqual(result["object"], result["head"])
        self.allow.write_text(
            "other " + self.key("other").with_suffix(".pub").read_text()
        )
        with self.assertRaises(subprocess.CalledProcessError):
            release.verify_tag(self.tag, self.allow)

    def test_tag_delimiter_inside_a_valid_prerelease_identifier(self):
        version = "1.0.1-alpha--v2"
        self.manifest(version)
        self.git("update-ref", "refs/remotes/origin/main", self.commit())
        tag = f"alpha--v{version}"
        self.sign(tag)
        self.assertEqual(release.verify_tag(tag, self.allow)["version"], version)

    def test_annotated_but_unsigned_and_lightweight_refused(self):
        self.allow.touch()
        self.git("tag", self.tag)
        with self.assertRaisesRegex(ValueError, "annotated"):
            release.verify_tag(self.tag, self.allow)
        self.git("tag", "-fam", "Unsigned", self.tag)
        with self.assertRaises(subprocess.CalledProcessError):
            release.verify_tag(self.tag, self.allow)

    def test_relocated_tag_object_and_wrong_version_refused(self):
        self.sign("alpha--v1.2.3")
        with self.assertRaisesRegex(ValueError, "manifest"):
            release.verify_tag("alpha--v1.2.3", self.allow)
        self.git(
            "update-ref",
            "refs/tags/" + self.tag,
            self.git("rev-parse", "alpha--v1.2.3"),
        )
        with self.assertRaisesRegex(ValueError, "signed tag name"):
            release.verify_tag(self.tag, self.allow)

    def test_later_main_commit_inheriting_a_version_is_not_a_decision(self):
        self.write("unrelated", "work")
        self.git("update-ref", "refs/remotes/origin/main", self.commit())
        self.sign()
        with self.assertRaisesRegex(ValueError, "version decision"):
            release.verify_tag(self.tag, self.allow)

    def test_adding_first_notes_for_initial_public_version_is_a_decision(self):
        notes = Path("docs/release-notes/alpha/1.0.0.md")
        notes.unlink()
        self.commit()
        notes.write_text("Reviewed first public release.\n")
        head = self.commit()
        self.git("update-ref", "refs/remotes/origin/main", head)
        self.sign()
        self.assertEqual(release.verify_tag(self.tag, self.allow)["head"], head)

    def test_unmerged_commit_is_not_a_release(self):
        self.write("unmerged", "work")
        self.commit()
        self.sign()
        with self.assertRaisesRegex(ValueError, "not reachable"):
            release.verify_tag(self.tag, self.allow)


class DraftTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.evidence = Path(temp.name)
        self.digests = {}
        for file in release.ASSETS:
            payload = f"an example {file}\n".encode()
            (self.evidence / file).write_bytes(payload)
            self.digests[file] = "sha256:" + hashlib.sha256(payload).hexdigest()
        self.plugin = {
            "name": "alpha",
            "version": "1.0.0-beta.1",
            "tag": "alpha--v1.0.0-beta.1",
            "head": "a" * 40,
            "object": "b" * 40,
            "prerelease": True,
        }
        self.existing = False
        self.remote_object = self.plugin["object"]
        self.uploads = []
        self.calls = []
        self.pending = None
        self.asset_digests = self.digests.copy()
        api = patch.object(release, "api", side_effect=self.github)
        self.addCleanup(api.stop)
        api.start()
        notes = patch.object(release, "release_notes", return_value="Reviewed notes.\n")
        self.addCleanup(notes.stop)
        notes.start()

    def github(self, endpoint, *args, **_kwargs):
        self.calls.append((endpoint, args))
        if "/git/ref/tags/" in endpoint:
            return {"object": {"sha": self.remote_object, "type": "tag"}}
        if "/releases/tags/" in endpoint:
            return {"immutable": True} if self.existing else None
        if endpoint == "graphql":
            return {"data": {"repository": {"release": self.pending}}}
        if endpoint.endswith("/releases") and "--input" in args:
            self.created = json.loads(Path(args[-1]).read_text())
            return {"id": 12, "draft": True, "tag_name": self.plugin["tag"]}
        if endpoint.startswith(
            "https://uploads.github.com/repos/example/plugins/releases/12/assets?name="
        ):
            name = endpoint.split("=")[1]
            self.assertEqual(Path(args[-1]), self.evidence / name)
            self.uploads.append(name)
            return {"digest": self.asset_digests[name], "state": "uploaded"}
        self.fail(f"Unexpected API mutation or endpoint: {endpoint} {args}")

    def draft(self):
        return release.prepare_draft("example/plugins", self.plugin, self.evidence)

    def test_prepares_only_unpublished_draft_with_reviewed_notes_and_evidence(self):
        receipt = self.draft()
        self.assertEqual(
            self.created,
            {
                "tag_name": self.plugin["tag"],
                "name": "alpha 1.0.0-beta.1",
                "body": "Reviewed notes.\n",
                "target_commitish": self.plugin["head"],
                "draft": True,
                "prerelease": True,
                "make_latest": "false",
            },
        )
        self.assertEqual(self.uploads, list(release.ASSETS))
        self.assertEqual(receipt["assets"], self.digests)
        self.assertEqual(receipt["object"], self.plugin["object"])
        self.assertEqual(receipt["draft_id"], 12)

    def test_existing_release_or_draft_never_modified(self):
        self.existing = True
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.draft()
        self.existing = False
        self.pending = {"id": 123}
        with self.assertRaisesRegex(ValueError, "existing draft"):
            self.draft()
        self.assertFalse(self.uploads)

    def test_changed_remote_object_or_bad_evidence_prevents_draft(self):
        self.remote_object = self.plugin["head"]
        with self.assertRaisesRegex(ValueError, "tag object changed"):
            self.draft()
        self.remote_object = self.plugin["object"]
        (self.evidence / "extra").touch()
        with self.assertRaisesRegex(ValueError, "expected exactly"):
            self.draft()
        self.assertFalse(self.uploads)

    def test_mismatched_upload_digest_stops_after_first_upload(self):
        self.asset_digests[release.ASSETS[0]] = "sha256:bad"
        with self.assertRaisesRegex(ValueError, "leave draft unpublished"):
            self.draft()
        self.assertEqual(self.uploads, [release.ASSETS[0]])


if __name__ == "__main__":
    unittest.main()
