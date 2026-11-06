"""Guard against silently turning unresolved packages or failed OSV runs into a pass."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import scan_dependencies as scan


class DependencyScanTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        self.root = Path(temp.name)
        os.chdir(self.root)
        Path("requirements-dev.txt").write_text("Parent==2.0\n")
        Path("package-lock.json").write_text(
            json.dumps(
                {
                    "packages": {
                        "": {"name": "root"},
                        "node_modules/@tool/compile": {"version": "3.0.0", "dev": True},
                    }
                }
            )
        )
        self.expected = {
            ("PyPI", "parent", "2.0"),
            ("PyPI", "child-lib", "1.0"),
            ("npm", "@tool/compile", "3.0.0"),
        }

    def test_transitives_and_dev_dependencies_reach_the_scanner(self):
        def resolve(command, **_):
            self.assertTrue(
                {"--dry-run", "--only-binary=:all:", "--ignore-installed"}
                <= set(command)
            )
            deps = [("Parent", "2.0"), ("Child_Lib", "1.0")]
            (self.root / "pip-report.json").write_text(
                json.dumps(
                    {
                        "install": [
                            {"metadata": {"name": n, "version": v}} for n, v in deps
                        ]
                    }
                )
            )

        with patch.object(subprocess, "run", side_effect=resolve):
            resolved = scan.resolve_python(self.root)
        self.assertEqual(resolved | scan.locked_npm(), self.expected)
        self.assertEqual(
            (self.root / "requirements.txt").read_text(),
            "child-lib==1.0\nparent==2.0\n",
        )

    def test_requirements_cannot_enable_source_builds_or_change_indexes(self):
        Path("requirements-dev.txt").write_text("--no-binary=:all:\nParent==2.0\n")
        with patch.object(subprocess, "run") as run, self.assertRaises(ValueError):
            scan.resolve_python(self.root)
        run.assert_not_called()

    def result(self, packages, ids=()):
        return {
            "results": [
                {
                    "packages": [
                        {
                            "package": {"ecosystem": e, "name": n, "version": v},
                            "vulnerabilities": [{"id": id_} for id_ in ids],
                        }
                        for e, n, v in packages
                    ]
                }
            ]
        }

    def test_missing_transitive_is_not_a_clean_scan(self):
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            scan.audit_result(
                0,
                self.result(self.expected - {("PyPI", "child-lib", "1.0")}),
                self.expected,
            )

    def test_findings_cannot_be_mistaken_for_a_clean_scan(self):
        dirty = self.result(self.expected, ["OSV-test"])
        self.assertEqual(scan.audit_result(1, dirty, self.expected), ["OSV-test"])
        with self.assertRaisesRegex(ValueError, "disagree"):
            scan.audit_result(0, dirty, self.expected)

    def test_scanner_operational_error_is_not_a_finding(self):
        with (
            patch.object(
                subprocess,
                "check_output",
                return_value=f"osv-scanner version: {scan.VERSION}",
            ),
            patch.object(scan, "resolve_python", return_value=set()),
            patch.object(
                subprocess, "run", return_value=subprocess.CompletedProcess([], 127)
            ),
            self.assertRaisesRegex(ValueError, "operational error \\(exit 127\\)"),
        ):
            scan.scan("osv-scanner", self.root, self.root / "absent-report.json")
