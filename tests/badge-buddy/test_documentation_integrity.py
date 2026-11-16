"""Check local document references and CLI example syntax, not agent behavior."""

from __future__ import annotations

from pathlib import Path
import json
import re
import shlex
import sys
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "badge-buddy"
SKILLS_ROOT = PLUGIN_ROOT / "skills"


class DocumentationIntegrityTest(unittest.TestCase):
    def test_raw_references_do_not_require_claude_substitution(self) -> None:
        for path in SKILLS_ROOT.glob("*/references/**/*.md"):
            with self.subTest(path=str(path.relative_to(SKILLS_ROOT))):
                self.assertNotRegex(path.read_text(), r"\$\{CLAUDE_[A-Z_]+\}")

    def test_skill_permission_rules_have_no_command_template_placeholders(self) -> None:
        for path in SKILLS_ROOT.glob("*/SKILL.md"):
            frontmatter = path.read_text().split("---", 2)[1]
            with self.subTest(path=path.parent.name):
                self.assertNotIn("<controller-path>", frontmatter)
                self.assertNotIn("<scorecard-controller>", frontmatter)

    def test_scorecard_documented_commands_parse(self) -> None:
        # Parse the examples without executing commands or making requests.
        scripts = str(PLUGIN_ROOT / "scripts")
        sys.path.insert(0, scripts)
        self.addCleanup(sys.path.remove, scripts)
        import scorecard

        parser = scorecard.build_parser()
        examples = []
        for path in sorted((SKILLS_ROOT / "ossf-scorecard").rglob("*.md")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith('"<scorecard-controller>" '):
                    examples.append((path, line))
        self.assertTrue(examples, "No Scorecard command examples found")
        for path, line in examples:
            with self.subTest(path=path.name, command=line):
                parser.parse_args(shlex.split(line)[1:])

    def test_registered_mcp_is_pinned_and_uses_stdio(self) -> None:
        config = json.loads((PLUGIN_ROOT / ".mcp.json").read_text())
        server = config["mcpServers"]["bestpractices"]
        self.assertEqual("uvx", server["command"])
        self.assertEqual(
            ["--from", "best-practices-mcp==0.5.0", "bestpractices-mcp"], server["args"]
        )
        self.assertNotIn("env", server)

    def test_board_documented_command_parses(self) -> None:
        scripts = str(PLUGIN_ROOT / "scripts")
        sys.path.insert(0, scripts)
        self.addCleanup(sys.path.remove, scripts)
        import review_board

        guide = SKILLS_ROOT / "ossf-bp-badges/references/application.md"
        example = next(
            line
            for line in guide.read_text().splitlines()
            if line.startswith('python3 "<board-renderer>"')
        )
        args = review_board.build_parser().parse_args(shlex.split(example)[2:])
        self.assertEqual("baseline-1", args.section)
        self.assertEqual("all", args.view)


if __name__ == "__main__":
    unittest.main()
