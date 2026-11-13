"""Release planning, exact Git commit binding and fail-closed native publication."""

from __future__ import annotations

import hashlib
import io
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

    def test_initial_version_can_decrease_in_new_repo_only(self):
        self.manifest("0.1.0")
        self.commit()
        self.assertEqual(release.plan(self.base)["plugins"][0]["tag"], "alpha--v0.1.0")
        self.git("tag", "alpha--v0.1.0", "HEAD")
        self.assertEqual(release.plan(self.base)["plugins"][0]["tag"], "alpha--v0.1.0")
        self.git("tag", "alpha--v0.4.0", self.base)
        self.write("later-work", "This is not the exact tagged release commit.")
        self.commit()
        with self.assertRaisesRegex(ValueError, "must increase"):
            release.plan(self.base)

    def test_initial_reset_rerun_survives_later_release_tags(self):
        self.manifest("0.1.0")
        first_head = self.commit()
        first_plan = release.plan(self.base, first_head)
        self.git("tag", "alpha--v0.1.0", first_head)
        self.manifest("0.2.0")
        later_head = self.commit()
        self.git("tag", "alpha--v0.2.0", later_head)
        self.assertEqual(release.plan(self.base, first_head), first_plan)
        self.manifest("0.0.5")
        decrease_head = self.commit()
        with self.assertRaisesRegex(ValueError, "must increase"):
            release.plan(later_head, decrease_head)

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

    def test_first_notes_without_version_change_and_idempotent_tag(self):
        notes = Path("docs/release-notes/alpha/1.0.0.md")
        notes.unlink()
        base = self.commit()
        notes.write_text("Reviewed initial public release.\n")
        head = self.commit()
        self.assertEqual(release.plan(base, head)["plugins"][0]["tag"], self.tag)
        self.git("tag", self.tag, head)
        self.assertEqual(len(release.plan(base, head)["plugins"]), 1)
        self.git("tag", "-f", self.tag, base)
        self.assertEqual(release.plan(base, head)["plugins"], [])

    def test_changed_existing_notes_do_not_release_again(self):
        Path("docs/release-notes/alpha/1.0.0.md").write_text("Edited text.\n")
        self.commit()
        self.assertEqual(release.plan(self.base)["plugins"], [])

    def test_exact_checkout_accepts_historical_main_when_main_advances(self):
        self.write("later", "work")
        self.git("update-ref", "refs/remotes/origin/main", self.commit())
        self.git("checkout", "--detach", self.base)
        release.check_checkout("empty", self.base)
        for head in ("HEAD", self.base[:12], "f" * 40, self.base.upper()):
            with (
                self.subTest(head=head),
                self.assertRaisesRegex(ValueError, "full event SHA"),
            ):
                release.check_checkout("empty", head)

    def test_checkout_requires_main_ancestry_and_event_base_ancestry(self):
        self.write("later", "work")
        head = self.commit()
        with self.assertRaisesRegex(ValueError, "origin/main"):
            release.check_checkout(self.base, head)
        self.git("update-ref", "refs/remotes/origin/main", head)
        self.git("checkout", "--detach", self.base)
        with self.assertRaisesRegex(ValueError, "event base"):
            release.check_checkout(head, self.base)


SCOPE = (
    "# Dependency scan\n\nCommit: `{head}`\n\n"
    "Scanned at {timestamp} using OSV-Scanner 2.7.0; Python 3.13.0 on Linux x86_64.\n\n"
    "Scope: repository maintainer tooling in the root npm lockfile (including dev dependencies) "
    "and requirements-dev.txt, including transitive wheels resolved for this platform at scan time. "
    "This is not a scan of consumers' dependencies, sample workflows, action implementations, "
    "pre-commit hook environments, or host system packages. Results cover known OSV advisories.\n\n"
    "Compared 1 distinct ecosystem/name/version coordinates.\n\n"
    "PASS: no known vulnerabilities found.\n"
)


def write_evidence(directory, head, timestamp="2026-11-13T00:00:00+00:00"):
    report = {
        "results": [
            {
                "packages": [
                    {
                        "package": {
                            "ecosystem": "npm",
                            "name": "example",
                            "version": "1.0.0",
                        }
                    }
                ]
            }
        ]
    }
    (directory / "osv-results.json").write_text(json.dumps(report))
    (directory / "scan-scope.md").write_text(
        SCOPE.format(head=head, timestamp=timestamp)
    )
    return release.evidence_digests(directory)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.evidence = Path(temp.name)
        self.plugin = {
            "name": "alpha",
            "version": "1.0.0-beta.1",
            "tag": "alpha--v1.0.0-beta.1",
            "head": "a" * 40,
            "prerelease": True,
        }
        self.hashes = write_evidence(self.evidence, self.plugin["head"])
        self.original_bytes = {
            name: (self.evidence / name).read_bytes() for name in release.ASSETS
        }
        self.ref = None
        self.record = None
        self.foreign_draft = False
        self.upload_bad_digest = False
        self.bad_draft = None
        self.immutable_enabled = True
        self.calls, self.writes = [], []
        for name, kwargs in (
            ("check_checkout", {}),
            ("plan", {"return_value": {"plugins": [self.plugin]}}),
            ("release_notes", {"return_value": "Reviewed notes.\n"}),
            ("api", {"side_effect": self.github}),
            ("run", {"side_effect": self.command}),
        ):
            mock = patch.object(release, name, **kwargs)
            mock.start()
            self.addCleanup(mock.stop)

    def command(self, *args, **kwargs):
        if args[:3] == ("gh", "release", "download"):
            directory = Path(args[args.index("--dir") + 1])
            for name, payload in self.original_bytes.items():
                (directory / name).write_bytes(payload)
        return subprocess.CompletedProcess(args, 0, "", "")

    def github(self, endpoint, *args, **kwargs):
        self.calls.append((endpoint, args))
        if "--method" in args:
            self.writes.append((endpoint, args))
        if "/git/ref/tags/" in endpoint:
            return self.ref
        if endpoint.endswith("/git/refs"):
            self.assertIn("sha=" + self.plugin["head"], args)
            self.assertIn("ref=refs/tags/" + self.plugin["tag"], args)
            self.ref = {"object": {"type": "commit", "sha": self.plugin["head"]}}
            return self.ref
        if "/releases/tags/" in endpoint:
            return self.record
        if endpoint == "graphql":
            return {
                "data": {
                    "repository": {
                        "release": {"id": "foreign"} if self.foreign_draft else None
                    }
                }
            }
        if endpoint.endswith("/releases"):
            payload = json.loads(Path(args[-1]).read_text())
            self.record = {
                **payload,
                "id": 12,
                "assets": [],
                "html_url": "https://example.invalid/release",
            }
            return self.record.copy()
        if endpoint.startswith("https://uploads.github.com/"):
            name = endpoint.split("=")[1]
            digest = (
                "sha256:" + "f" * 64 if self.upload_bad_digest else self.hashes[name]
            )
            asset = {"name": name, "digest": digest, "state": "uploaded"}
            self.record["assets"].append(asset)
            return asset
        if endpoint.endswith("/releases/12"):
            if "PATCH" in args:
                self.assertIn("draft=false", args)
                self.record.update(draft=False, immutable=self.immutable_enabled)
            record = self.record.copy()
            if self.bad_draft and record["draft"]:
                record.update(self.bad_draft)
            return record
        self.fail(f"Unexpected API request: {endpoint} {args}")

    def publish(self):
        release.publish("b" * 40, self.plugin["head"], "example/plugins", self.evidence)

    def test_unsigned_lightweight_tag_and_immutable_release_at_exact_commit(self):
        self.publish()
        self.assertEqual(
            self.ref["object"], {"sha": self.plugin["head"], "type": "commit"}
        )
        self.assertEqual(self.record["target_commitish"], self.plugin["head"])
        self.assertTrue(self.record["immutable"])
        self.assertFalse(self.record["draft"])
        release.run.assert_called_with(
            "gh", "release", "verify", self.plugin["tag"], "--repo", "example/plugins"
        )
        release.plan.assert_called_with("b" * 40, self.plugin["head"])
        self.assertFalse(
            any("immutable-releases" in endpoint for endpoint, _ in self.calls)
        )

    def test_immutable_rerun_uses_original_assets_not_new_scan_timestamps(self):
        self.publish()
        mutations = list(self.writes)
        write_evidence(self.evidence, self.plugin["head"], "2026-11-14T00:00:00+00:00")
        self.assertNotEqual(self.hashes, release.evidence_digests(self.evidence))
        self.publish()
        self.assertEqual(self.writes, mutations)

    def test_conflicting_commit_and_annotated_tag_refused_before_writes(self):
        for object_type, sha in (("commit", "c" * 40), ("tag", self.plugin["head"])):
            self.ref = {"object": {"type": object_type, "sha": sha}}
            with (
                self.subTest(kind=object_type),
                self.assertRaisesRegex(ValueError, "conflicts"),
            ):
                self.publish()
        self.assertEqual(self.writes, [])

    def test_existing_exact_lightweight_tag_is_preserved(self):
        self.ref = {"object": {"type": "commit", "sha": self.plugin["head"]}}
        self.publish()
        self.assertFalse(
            any(endpoint.endswith("/git/refs") for endpoint, _ in self.writes)
        )

    def test_foreign_draft_refused_without_mutation(self):
        self.foreign_draft = True
        with self.assertRaisesRegex(ValueError, "existing draft"):
            self.publish()
        self.assertEqual(self.writes, [])
        self.record = {"draft": True}
        with self.assertRaisesRegex(ValueError, "existing draft"):
            self.publish()
        self.assertEqual(self.writes, [])

    def test_upload_digest_mismatch_leaves_unpublished_draft(self):
        self.upload_bad_digest = True
        with self.assertRaisesRegex(ValueError, "leave draft unpublished"):
            self.publish()
        self.assertTrue(self.record["draft"])
        self.assertEqual(len(self.record["assets"]), 1)
        self.assertFalse(any("PATCH" in args for _, args in self.writes))

    def test_draft_metadata_notes_and_asset_changes_block_publication(self):
        for change in (
            {"id": 13},
            {"target_commitish": "c" * 40},
            {"body": "foreign notes"},
            {"assets": []},
        ):
            with self.subTest(change=change):
                self.record, self.ref, self.writes = None, None, []
                self.bad_draft = change
                with self.assertRaises(ValueError):
                    self.publish()
                self.assertFalse(any("PATCH" in args for _, args in self.writes))

    def test_missing_immutability_fails_after_publication(self):
        self.immutable_enabled = False
        with self.assertRaisesRegex(ValueError, "did not confirm an immutable"):
            self.publish()
        self.assertFalse(self.record["draft"])
        self.assertFalse(
            any(
                call.args[:3] == ("gh", "release", "verify")
                for call in release.run.call_args_list
            )
        )

    def test_immutable_retry_accepts_edited_display_fields(self):
        self.publish()
        writes = list(self.writes)
        self.record.update(
            body="Edited displayed release notes.",
            name="New display title",
            prerelease=False,
        )
        self.publish()
        self.assertEqual(writes, self.writes)
        release.run.assert_called_with(
            "gh", "release", "verify", self.plugin["tag"], "--repo", "example/plugins"
        )

    def test_published_release_with_changed_subject_or_bytes_is_not_accepted(self):
        self.publish()
        writes = list(self.writes)
        for field, wrong in (
            ("tag_name", "alpha--v9.0.0"),
            ("target_commitish", "c" * 40),
        ):
            original = self.record[field]
            self.record[field] = wrong
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(ValueError, "subject"),
            ):
                self.publish()
            self.record[field] = original
        self.record["assets"][0]["digest"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(ValueError, "bytes do not match"):
            self.publish()
        self.assertEqual(writes, self.writes)

    def test_editorial_scan_scope_changes_do_not_block_publication(self):
        scope = (
            "# Maintainer dependency evidence\n\n"
            f"Commit: `{self.plugin['head']}`\n\n"
            "Scanned yesterday with an updated scanner on a new platform.\n\n"
            "Scope: repository maintainer tooling; see scanner documentation.\n\n"
            "Compared packages using the scanner's inventory validation.\n\n"
            "PASS: no known vulnerabilities found.\n"
        )
        (self.evidence / "scan-scope.md").write_text(scope)
        self.hashes = release.evidence_digests(self.evidence)
        self.publish()
        self.assertFalse(self.record["draft"])

    def test_malformed_evidence_prevents_all_mutation(self):
        for content in (
            "{}",
            "[]",
            '{"results": []}',
            '{"results": [{"packages": []}]}',
            "not json",
        ):
            with self.subTest(content=content):
                (self.evidence / "osv-results.json").write_text(content)
                with self.assertRaises(ValueError):
                    self.publish()
                self.assertEqual(self.writes, [])

    def test_scan_failure_wrong_or_duplicate_commit_prevents_mutation(self):
        scope = (self.evidence / "scan-scope.md").read_text()
        for bad in (
            scope.replace(self.plugin["head"], "c" * 40),
            scope.replace("PASS:", "BLOCKED:"),
            scope + "INCOMPLETE: failure\n",
            scope + f"Commit: `{self.plugin['head']}`\n",
            scope.replace("PASS: no known vulnerabilities found.\n", ""),
        ):
            with self.subTest(scope=bad):
                (self.evidence / "scan-scope.md").write_text(bad)
                with self.assertRaisesRegex(ValueError, "commit.*PASS"):
                    self.publish()
                self.assertEqual(self.writes, [])

    def test_vulnerabilities_and_extra_artifacts_prevent_mutation(self):
        report = json.loads((self.evidence / "osv-results.json").read_text())
        report["results"][0]["packages"][0]["vulnerabilities"] = [
            {"id": "GHSA-example"}
        ]
        (self.evidence / "osv-results.json").write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "vulnerabilities"):
            self.publish()
        write_evidence(self.evidence, self.plugin["head"])
        (self.evidence / "unexpected").touch()
        with self.assertRaisesRegex(ValueError, "expected exactly"):
            self.publish()
        self.assertEqual(self.writes, [])


if __name__ == "__main__":
    unittest.main()
