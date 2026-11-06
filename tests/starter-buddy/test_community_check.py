from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "starter-buddy"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import community_check  # noqa: E402


class CommunityCheckTests(unittest.TestCase):
    def test_empty_repository_reports_missing_without_inventing_score(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = community_check.inventory(Path(temporary_directory))

        self.assertIsNone(result["score_projection"])
        self.assertEqual(result["local"]["counts"]["missing"], 7)
        self.assertEqual(result["local"]["optional_items"]["support"]["status"], "missing")
        self.assertFalse(result["local"]["validation_errors"])

    def test_complete_candidate_set_uses_supported_locations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
            (root / "docs").mkdir()
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            (root / ".github" / "CODE_OF_CONDUCT.md").write_text("Be kind.\n", encoding="utf-8")
            (root / "docs" / "CONTRIBUTING.md").write_text("Run the tests.\n", encoding="utf-8")
            (root / "SECURITY.md").write_text("Report issues privately.\n", encoding="utf-8")
            (root / "docs" / "SUPPORT.md").write_text("Ask in Discussions.\n", encoding="utf-8")
            (root / "LICENSE").write_text("Maintainer-selected license text.\n", encoding="utf-8")
            (root / ".github" / "ISSUE_TEMPLATE" / "bug.yml").write_text(
                "name: Bug report\ndescription: Tell us what happened\nbody:\n  - type: textarea\n    attributes:\n      label: What happened?\n",
                encoding="utf-8",
            )
            (root / ".github" / "ISSUE_TEMPLATE" / "config.yml").write_text(
                "blank_issues_enabled: true\n",
                encoding="utf-8",
            )
            (root / ".github" / "pull_request_template.md").write_text(
                "## What changed?\n",
                encoding="utf-8",
            )

            result = community_check.inventory(root)

        items = result["local"]["items"]
        self.assertEqual(items["code_of_conduct"]["selected"], ".github/CODE_OF_CONDUCT.md")
        self.assertEqual(items["contributing"]["selected"], "docs/CONTRIBUTING.md")
        self.assertEqual(items["license"]["status"], "candidate")
        self.assertEqual(items["issue_templates"]["status"], "candidate")
        self.assertEqual(items["issue_templates"]["chooser_config"]["status"], "candidate")
        self.assertFalse(items["issue_templates"]["chooser_config"]["required_for_checklist"])
        self.assertEqual(items["pull_request_template"]["status"], "present")
        self.assertEqual(result["local"]["optional_items"]["support"]["selected"], "docs/SUPPORT.md")
        self.assertFalse(result["local"]["validation_errors"])

    def test_higher_precedence_duplicate_is_selected_but_only_warned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".github").mkdir()
            (root / "README.md").write_text("# Root\n", encoding="utf-8")
            (root / ".github" / "README.md").write_text("# GitHub\n", encoding="utf-8")

            result = community_check.inventory(root)
            with redirect_stdout(io.StringIO()):
                exit_code = community_check.main(["--repo", str(root), "--fail-on-invalid"])

        self.assertEqual(result["local"]["items"]["readme"]["selected"], ".github/README.md")
        self.assertTrue(result["local"]["warnings"])
        self.assertFalse(result["local"]["validation_errors"])
        self.assertEqual(exit_code, 0)

    def test_backup_and_draft_filenames_are_not_canonical_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.backup.md").write_text("# Old readme\n", encoding="utf-8")
            (root / "SECURITY.draft.md").write_text("Draft policy\n", encoding="utf-8")
            (root / "LICENSE.old.md").write_text("Old license\n", encoding="utf-8")

            result = community_check.inventory(root)

        self.assertEqual(result["local"]["items"]["readme"]["status"], "missing")
        self.assertEqual(result["local"]["items"]["security"]["status"], "missing")
        self.assertEqual(result["local"]["items"]["license"]["status"], "missing")

    def test_issue_form_inventory_does_not_claim_yaml_validation(self) -> None:
        forms = {
            "indentless": "name: Bug report\ndescription: Report a problem\nbody:\n- type: textarea\n  attributes:\n    label: What happened?\n",
            "id_first": "name: Bug report\ndescription: Report a problem\nbody:\n  - id: details\n    type: textarea\n    attributes:\n      label: What happened?\n",
            "missing_fields": "name: Bug report\n",
            "scalar_body": "name: Bug report\ndescription: Report a problem\nbody: text\n",
            "malformed": "body: [\n",
            "markdown_only": "body:\n  - type: markdown\n    attributes:\n      value: Information\n",
        }
        for name, content in forms.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                form = root / ".github/ISSUE_TEMPLATE/bug.yml"
                form.parent.mkdir(parents=True)
                form.write_text(content, encoding="utf-8")
                result = community_check.inventory(root)
                candidate = result["local"]["items"]["issue_templates"]["all_candidates"][0]
                self.assertTrue(candidate["checklist_candidate"])
                self.assertEqual("presence_only", candidate["validation_scope"])
                self.assertEqual([], candidate["validation_problems"])
                with redirect_stdout(io.StringIO()) as output:
                    exit_code = community_check.main(["--repo", str(root), "--fail-on-invalid"])
                self.assertEqual(0, exit_code)
                self.assertIn("not parsed or validated", output.getvalue())

    def test_markdown_issue_template_requires_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            directory = root / ".github" / "ISSUE_TEMPLATE"
            directory.mkdir(parents=True)
            (directory / "question.md").write_text("# Question\n", encoding="utf-8")

            result = community_check.inventory(root)

        candidate = result["local"]["items"]["issue_templates"]["all_candidates"][0]
        self.assertFalse(candidate["checklist_candidate"])
        self.assertEqual(candidate["validation_problems"], ["name (more than 3 characters)", "about"])

    def test_config_is_optional_but_exact_filename_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            directory = root / ".github" / "ISSUE_TEMPLATE"
            directory.mkdir(parents=True)
            (directory / "bug.yml").write_text(
                "name: Bug report\ndescription: Tell us what happened\nbody:\n  - type: textarea\n    attributes:\n      label: What happened?\n",
                encoding="utf-8",
            )
            result_without_config = community_check.inventory(root)
            (directory / "config.yaml").write_text("blank_issues_enabled: true\n", encoding="utf-8")
            result_with_alternate = community_check.inventory(root)

        self.assertEqual(
            result_without_config["local"]["items"]["issue_templates"]["chooser_config"]["status"],
            "missing_optional",
        )
        self.assertEqual(result_without_config["local"]["items"]["issue_templates"]["status"], "candidate")
        self.assertEqual(
            result_with_alternate["local"]["items"]["issue_templates"]["chooser_config"]["status"],
            "unrecognized_name",
        )
        self.assertTrue(any("config.yml" in warning for warning in result_with_alternate["local"]["warnings"]))

    def test_unresolved_placeholder_is_a_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "SECURITY.md").write_text("Use {{SECURITY_REPORTING_ROUTE}}.\n", encoding="utf-8")

            result = community_check.inventory(root)

        self.assertIn("SECURITY.md contains unresolved template placeholders", result["local"]["validation_errors"][0])

    def test_generic_placeholder_text_only_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text("{% raw %}{{ page.title }}{% endraw %}\nTODO list\n", encoding="utf-8")

            result = community_check.inventory(root)

        self.assertTrue(result["local"]["warnings"])
        self.assertFalse(result["local"]["validation_errors"])

    def test_yaml_form_is_preserved_but_markdown_long_extension_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            directory = root / ".github" / "ISSUE_TEMPLATE"
            directory.mkdir(parents=True)
            (directory / "bug.yaml").write_text(
                "name: Bug report\ndescription: Tell us what happened\nbody:\n  - type: textarea\n    attributes:\n      label: What happened?\n",
                encoding="utf-8",
            )
            (directory / "feature.markdown").write_text(
                "---\nname: Feature request\nabout: Suggest an idea\n---\n",
                encoding="utf-8",
            )

            result = community_check.inventory(root)

        item = result["local"]["items"]["issue_templates"]
        self.assertEqual(item["status"], "candidate")
        self.assertEqual(
            [candidate["validation_problems"] for candidate in item["all_candidates"]],
            [[], ["extension .markdown (use .md)"]],
        )

    def test_empty_issue_form_still_reports_missing_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            form = root / ".github/ISSUE_TEMPLATE/empty.yml"
            form.parent.mkdir(parents=True)
            form.write_text("  \n", encoding="utf-8")
            result = community_check.inventory(root)
            candidate = result["local"]["items"]["issue_templates"]["all_candidates"][0]
            self.assertFalse(candidate["checklist_candidate"])
            self.assertEqual(["nonempty content"], candidate["validation_problems"])
            with redirect_stdout(io.StringIO()):
                exit_code = community_check.main(["--repo", str(root), "--fail-on-invalid"])
            self.assertEqual(1, exit_code)

    def test_pull_request_template_preserves_location_precedence_and_formats(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "docs").mkdir()
            (root / "pull_request_template.md").write_text("Root template\n", encoding="utf-8")
            (root / "docs" / "pull_request_template.md").write_text("Docs template\n", encoding="utf-8")
            (root / ".github").mkdir()
            (root / ".github" / "pull_request_template.rst").write_text(
                "Unsupported template\n", encoding="utf-8"
            )

            result = community_check.inventory(root)

        item = result["local"]["items"]["pull_request_template"]
        self.assertEqual(item["selected"], "pull_request_template.md")
        self.assertNotIn(".github/pull_request_template.rst", item["candidates"])

    def test_license_outside_root_is_not_detected_and_is_warned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".github").mkdir()
            (root / "docs").mkdir()
            (root / ".github" / "LICENSE.md").write_text("License copy\n", encoding="utf-8")
            (root / "docs" / "LICENSE.txt").write_text("License copy\n", encoding="utf-8")

            result = community_check.inventory(root)

        self.assertEqual(result["local"]["items"]["license"]["status"], "missing")
        self.assertEqual(len(result["local"]["warnings"]), 2)
        self.assertTrue(all("not an auto-detectable repository license" in warning for warning in result["local"]["warnings"]))

    def test_remote_profile_preserves_api_limitations(self) -> None:
        profile = {
            "health_percentage": 87,
            "description": "Policy checks",
            "content_reports_enabled": False,
            "files": {"readme": {"url": "example"}, "pull_request_template": {"url": "example"}},
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = community_check.inventory(Path(temporary_directory), profile)

        remote = result["remote"]
        self.assertEqual(remote["health_percentage"], 87)
        self.assertFalse(remote["content_reports_enabled"])
        self.assertIsNone(remote["files"]["security"])
        self.assertTrue(any("SECURITY" in limitation for limitation in remote["limitations"]))

    def test_cli_reads_profile_from_standard_input_and_emits_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            profile = io.StringIO(json.dumps({"health_percentage": 100, "files": {}}))
            output = io.StringIO()
            previous_stdin = sys.stdin
            try:
                sys.stdin = profile
                with redirect_stdout(output):
                    exit_code = community_check.main(
                        ["--repo", temporary_directory, "--profile-json", "-", "--json"]
                    )
            finally:
                sys.stdin = previous_stdin

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue())["remote"]["health_percentage"], 100)

    def test_cli_reports_invalid_profile_as_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            profile_path = Path(temporary_directory) / "profile.json"
            profile_path.write_text("not JSON", encoding="utf-8")
            error_output = io.StringIO()
            with redirect_stderr(error_output):
                exit_code = community_check.main(
                    ["--repo", temporary_directory, "--profile-json", str(profile_path)]
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("could not read Community Profile JSON", error_output.getvalue())


if __name__ == "__main__":
    unittest.main()
