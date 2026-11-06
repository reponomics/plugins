"""Offline refresh/check integration against a committed source and HTTP fixture."""
from __future__ import annotations

import contextlib
import copy
import datetime as dt
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import criteria_download as download
import criteria_sync as sync


def criterion_id(section: str) -> str:
    return f"osps_ac_01_0{section[-1]}" if section.startswith("baseline-") else "example"


class ApplicationClient:
    def __init__(self, answer="Met", description="Publish the policy."):
        self.answer, self.description = answer, description

    def get(self, url, content_type):
        if url.endswith("robots.txt"):
            return b"User-agent: *\nAllow: /\n", {}
        section = url.rsplit("/", 1)[-1]
        name = criterion_id(section)
        label = f"OSPS-AC-01.0{section[-1]}" if section.startswith("baseline-") else name
        body = f'''<!doctype html><html lang="en"><body>
<div class="criterion-data" id="{name}" data-status="{self.answer}">
<div class="criteria-radio">
<input type="radio" name="project[{name}_status]" value="Met">
<input type="radio" name="project[{name}_status]" value="Unmet">
<input type="radio" name="project[{name}_status]" value="N/A">
<input type="radio" name="project[{name}_status]" value="?">
</div><div class="criteria-desc">{self.description} <sup>[{label}]</sup>
<div class="details-text" id="{name}_details_text">Explain the policy.</div></div>
<div class="justification-markdown">The project answer is {self.answer}.</div>
</div></body></html>'''
        return body.encode(), {}


class CriteriaSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.repo = self.directory / "upstream"
        self.repo.mkdir()
        self.snapshot = self.directory / "snapshot"
        self.catalog = self.directory / "plugin" / "criteria.json"
        self.receipt = sync.verification_path(self.catalog)
        self.git("init", "-q")
        self.git("config", "user.name", "Test Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.create_source()
        self.observed_at = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).isoformat()
        self.download()
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stderr = contextlib.redirect_stderr(io.StringIO())
        self.stdout.__enter__()
        self.stderr.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def create_source(self):
        metal, baseline, locale = {}, {}, {}
        for section in sync.SECTIONS:
            level = {"passing": "0", "silver": "1", "gold": "2"}.get(section, section)
            name = criterion_id(section)
            meta = {"category": "MUST", "na_allowed": True, "met_url_required": False}
            if section.startswith("baseline-"):
                meta["original_id"] = f"OSPS-AC-01.0{section[-1]}"
            (baseline if section.startswith("baseline-") else metal)[level] = {"General": {"Controls": {name: meta}}}
            locale[level] = {name: {"description": "Publish the policy.", "details": "Explain the policy."}}
        for relative, value in (("criteria/criteria.yml", metal),
                                ("criteria/baseline_criteria.yml", baseline),
                                ("config/locales/en.yml", {"en": {"criteria": locale}})):
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(value, sort_keys=False))
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Fixture")

    def download(self, client=None):
        with patch.object(download, "now", return_value=self.observed_at):
            return download.download_snapshot(self.snapshot, client or ApplicationClient())

    def refresh(self):
        return sync.refresh(self.repo, self.snapshot, self.catalog)

    def main(self, command):
        return sync.main([command, "--badge-repo", str(self.repo),
                          "--snapshot", str(self.snapshot), "--catalog", str(self.catalog)])

    def test_refresh_publishes_matching_catalog_and_bound_receipt(self):
        self.assertEqual(self.refresh(), 0)
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt["catalog_sha256"], download.digest(self.catalog.read_bytes()))
        self.assertEqual(receipt["repository"]["commit"], self.git("rev-parse", "HEAD"))
        self.assertEqual(receipt["website"]["downloaded_at"], self.observed_at)
        self.assertEqual(set(receipt["pages"]), set(sync.SECTIONS))
        self.assertEqual(sync.check(self.repo, self.snapshot, self.catalog), 0)
        self.assertEqual(json.loads((self.snapshot / "report.json").read_text())["status"], "match")

    def test_disagreement_leaves_catalog_and_receipt_unchanged(self):
        self.refresh()
        before = self.catalog.read_bytes(), self.receipt.read_bytes()
        self.download(ApplicationClient(description="Publish the updated policy."))
        self.assertEqual(self.refresh(), 1)
        self.assertEqual((self.catalog.read_bytes(), self.receipt.read_bytes()), before)
        report = json.loads((self.snapshot / "report.json").read_text())
        self.assertEqual(report["status"], "different")
        self.assertTrue(all(item["field"] == "description" for item in report["differences"]))
        self.assertEqual(self.main("check"), 1)

    def test_incomplete_snapshot_leaves_catalog_and_receipt_unchanged(self):
        self.refresh()
        before = self.catalog.read_bytes(), self.receipt.read_bytes()
        manifest_path = self.snapshot / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        del manifest["pages"]["gold"]
        manifest_path.write_text(json.dumps(manifest))
        self.assertEqual(self.main("refresh"), 1)
        self.assertEqual((self.catalog.read_bytes(), self.receipt.read_bytes()), before)

    def test_noop_retains_receipt_but_report_tracks_new_observation(self):
        self.refresh()
        before = self.catalog.read_bytes(), self.receipt.read_bytes()
        previous = json.loads(before[1])
        self.observed_at = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).isoformat()
        manifest = self.download(ApplicationClient(answer="Unmet"))
        self.assertNotEqual(previous["pages"]["passing"]["sha256"], manifest["pages"]["passing"]["sha256"])
        self.assertEqual(self.refresh(), 0)
        self.assertEqual((self.catalog.read_bytes(), self.receipt.read_bytes()), before)
        report = json.loads((self.snapshot / "report.json").read_text())
        self.assertEqual(report["website_observed_at"], self.observed_at)
        self.assertEqual(report["website_semantic_sha256"], previous["website_semantic_sha256"])
        self.assertEqual(sync.check(self.repo, self.snapshot, self.catalog), 0)

    def test_changed_repository_detected_even_when_visible_content_agrees(self):
        self.refresh()
        path = self.repo / "criteria/criteria.yml"
        path.write_text(path.read_text().replace("category: MUST", "category: SHOULD", 1))
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Change category")
        self.assertEqual(sync.check(self.repo, self.snapshot, self.catalog), 1)

    def test_receipt_checksum_detects_catalog_edit(self):
        self.refresh()
        self.catalog.write_bytes(self.catalog.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "checksum"):
            sync.check(self.repo, self.snapshot, self.catalog)

    def test_invalid_receipt_provenance_rejected_and_refresh_repairs(self):
        self.refresh()
        valid = json.loads(self.receipt.read_text())
        mutations = [
            lambda r: r.update(website=None),
            lambda r: r["website"].update(base_url="https://other.example"),
            lambda r: r["website"].update(project_id=2),
            lambda r: r["website"].update(project_id=True),
            lambda r: r["website"].update(downloaded_at="2026-01-01"),
            lambda r: r["website"].update(downloaded_at="invalid"),
            lambda r: r["website"].update(downloaded_at=(dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()),
            lambda r: r["pages"].pop("gold"),
            lambda r: r["pages"]["passing"].update(url="https://other.example/passing"),
            lambda r: r["pages"]["passing"].update(sha256="invalid"),
            lambda r: r["pages"].update(passing=None),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                changed = copy.deepcopy(valid)
                mutate(changed)
                self.receipt.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    sync.check(self.repo, self.snapshot, self.catalog)
                self.assertEqual(self.refresh(), 0)
                self.assertEqual(json.loads(self.receipt.read_text()), valid)

    def test_cli_yaml_error_is_recorded_and_next_success_clears_it(self):
        self.refresh()
        before = self.catalog.read_bytes(), self.receipt.read_bytes()
        path = self.repo / "criteria/criteria.yml"
        good = path.read_text()
        path.write_text("[invalid yaml\n")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Malformed source")
        self.assertEqual(self.main("refresh"), 1)
        error_path = self.snapshot / "last-error.json"
        error = json.loads(error_path.read_text())
        self.assertEqual(error["command"], "refresh")
        self.assertEqual(error["status"], "error")
        self.assertIn("expected", error["error"])
        self.assertEqual((self.catalog.read_bytes(), self.receipt.read_bytes()), before)
        path.write_text(good)
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Repair source")
        self.assertEqual(self.main("refresh"), 0)
        self.assertFalse(error_path.exists())


if __name__ == "__main__":
    unittest.main()
