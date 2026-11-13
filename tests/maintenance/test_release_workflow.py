"""Keep publication bound to verified source and independent of live criteria."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]


class ReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = yaml.safe_load(
            (ROOT / ".github/workflows/release.yml").read_text()
        )
        cls.scan = yaml.safe_load(
            (ROOT / ".github/workflows/dependency-scan.yml").read_text()
        )

    def dependencies(self, job):
        needs = self.release["jobs"][job].get("needs", [])
        return {needs} if isinstance(needs, str) else set(needs)

    def test_criteria_cannot_gate_publication(self):
        pending = list(self.dependencies("publish"))
        required = set()
        while pending:
            job = pending.pop()
            if job not in required:
                required.add(job)
                pending.extend(self.dependencies(job))
        self.assertEqual({"validate", "checks", "scan"}, required)
        self.assertNotIn("criteria", required)
        self.assertTrue(self.release["jobs"]["criteria"]["continue-on-error"])

    def test_only_approved_main_publication_can_write(self):
        self.assertEqual({"contents": "read"}, self.release["permissions"])
        publish = self.release["jobs"]["publish"]
        self.assertEqual("release", publish["environment"])
        for condition in (
            "github.event_name == 'push'",
            "github.ref == 'refs/heads/main'",
            "vars.RELEASE_REPOSITORY == github.repository",
        ):
            self.assertIn(condition, publish["if"])
        for name, job in self.release["jobs"].items():
            permissions = job.get("permissions", self.release["permissions"])
            self.assertEqual(
                "write" if name == "publish" else "read", permissions["contents"]
            )

    def test_checks_scan_and_publisher_use_the_same_event_commit(self):
        for workflow in (self.release, self.scan):
            for job in workflow["jobs"].values():
                for step in job.get("steps", []):
                    if step.get("uses", "").startswith("actions/checkout@"):
                        self.assertEqual("${{ github.sha }}", step["with"]["ref"])
                        self.assertFalse(step["with"]["persist-credentials"])
        events = self.scan.get("on", self.scan.get(True))
        self.assertNotIn("inputs", events["workflow_call"])
        self.assertEqual(
            "${{ github.sha }}", self.scan["jobs"]["scan"]["env"]["SCAN_COMMIT"]
        )
        publish_steps = self.release["jobs"]["publish"]["steps"]
        download = next(
            step
            for step in publish_steps
            if step.get("uses", "").startswith("actions/download-artifact@")
        )
        self.assertEqual(
            "${{ needs.scan.outputs.artifact-id }}", download["with"]["artifact-ids"]
        )

    def test_criteria_failures_report_warnings_without_failing(self):
        steps = self.release["jobs"]["criteria"]["steps"]
        report = next(
            step for step in steps if step.get("name") == "Report advisory outcome"
        )
        for download, comparison, warning in (
            ("success", "success", False),
            ("failure", "skipped", True),
            ("success", "failure", True),
        ):
            with (
                self.subTest(download=download, comparison=comparison),
                tempfile.TemporaryDirectory() as temp,
            ):
                summary = Path(temp) / "summary.md"
                result = subprocess.run(
                    [
                        "bash",
                        "--noprofile",
                        "--norc",
                        "-eo",
                        "pipefail",
                        "-c",
                        report["run"],
                    ],
                    env={
                        **os.environ,
                        "DOWNLOAD": download,
                        "COMPARISON": comparison,
                        "GITHUB_STEP_SUMMARY": str(summary),
                    },
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(warning, "::warning::" in result.stdout)
                self.assertIn("advisory", summary.read_text())

    def test_local_release_checks_do_not_contact_live_criteria(self):
        result = subprocess.run(
            ["make", "--dry-run", "release-check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("unittest", result.stdout)
        self.assertNotIn("criteria_sync.py", result.stdout)
        self.assertNotIn("download-criteria", result.stdout)


if __name__ == "__main__":
    unittest.main()
