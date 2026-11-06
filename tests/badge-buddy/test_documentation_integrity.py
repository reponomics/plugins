"""Check local document references and CLI example syntax, not agent behavior."""

from __future__ import annotations

from pathlib import Path
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
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

    def test_documented_status_works_without_claude_shell_variables(self) -> None:
        with tempfile.TemporaryDirectory(prefix="badge paths ") as directory:
            root = Path(directory)
            installed = root / "plugin cache" / "badge-buddy" / "test version"
            shutil.copytree(PLUGIN_ROOT, installed, ignore=shutil.ignore_patterns("__pycache__"))
            repository = root / "user project"
            data_dir = root / "private plugin data"
            subprocess.run(["git", "init", "-q", str(repository)], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(repository), "remote", "add", "origin", "https://github.com/example/review.git"],
                check=True, capture_output=True,
            )
            # Seed the association from a prior online session without network access.
            data_dir.mkdir()
            (data_dir / "registry.json").write_text(json.dumps({
                "schema_version": 1,
                "by_id": {"31": "github.com/example/review"},
                "by_remote": {"github.com/example/review": "31"},
                "unregistered": {},
            }))
            skill = installed / "skills/ossf-bp-badges/SKILL.md"
            # Model the documented host substitution in SKILL.md only. The
            # subsequent reference read and Bash process get no such expansion.
            rendered = skill.read_text().replace("${CLAUDE_PLUGIN_DATA}", str(data_dir))
            controller_link = re.search(r"\[the controller\]\(([^)]+)\)", rendered)
            self.assertIsNotNone(controller_link)
            controller = (skill.parent / controller_link[1]).resolve()
            status_line = next(line for line in rendered.splitlines() if line.startswith('"<controller-path>"'))
            reference = skill.parent / "references/application.md"
            reference_line = next(line for line in reference.read_text().splitlines() if line.startswith('"<controller-path>"'))
            environment = {key: value for key, value in os.environ.items() if not key.startswith("CLAUDE_")}
            # Run the entrypoint, then resume using the raw reference template.
            for line in (status_line, reference_line):
                substitutions = {
                    "<controller-path>": str(controller),
                    "<project-root>": str(repository),
                    "<plugin-data>": str(data_dir),
                }
                arguments = [substitutions.get(arg, arg) for arg in shlex.split(line)]
                command = shlex.join([*arguments, "--project-id", "31", "--offline"])
                result = subprocess.run(
                    ["bash", "-c", command], cwd=repository, env=environment,
                    capture_output=True, text=True, check=True,
                )
                self.assertEqual("registered", json.loads(result.stdout)["state"])
            self.assertTrue((data_dir / "registry.json").is_file())
            self.assertFalse((repository / "registry.json").exists())
            self.assertFalse((installed / "registry.json").exists())


if __name__ == "__main__":
    unittest.main()
