"""Check distributable workflow templates, without executing hosted services."""

from pathlib import Path
import re
import unittest

import yaml


SKILLS = Path(__file__).resolve().parents[2] / "plugins/badge-buddy/skills"
ENGINEERING_SKILLS = ("coverage-baseline", "static-analysis")


class EngineeringTemplateTests(unittest.TestCase):
    def test_workflows_pin_actions_and_keep_default_permissions_read_only(self) -> None:
        for skill in ENGINEERING_SKILLS:
            templates = list((SKILLS / skill / "assets/templates/workflows").glob("*.yml"))
            self.assertTrue(templates, f"No workflow example for {skill}")
            for path in templates:
                with self.subTest(template=path.name):
                    text = path.read_text()
                    workflow = yaml.safe_load(text)
                    permissions = workflow["permissions"]
                    self.assertIsInstance(permissions, dict)
                    self.assertTrue(all(value in ("read", "none") for value in permissions.values()))
                    # PyYAML's YAML 1.1 loader interprets the 'on' key as True.
                    events = workflow.get("on", workflow.get(True, {}))
                    self.assertNotIn("pull_request_target", events)
                    self.assertNotIn("workflow_run", events)
                    actions = re.findall(r"^\s*-?\s*uses:\s*(.+)$", text, re.MULTILINE)
                    self.assertTrue(actions)
                    for action in actions:
                        self.assertRegex(action, r"^[\w.-]+/[\w./-]+@[a-f0-9]{40}\s+# v\d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
