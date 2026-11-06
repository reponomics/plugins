from __future__ import annotations

from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit


PLUGIN_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "release-buddy"


class DocumentationIntegrityTests(unittest.TestCase):
    def test_documented_local_paths_exist(self) -> None:
        documents = sorted(PLUGIN_ROOT.rglob("*.md"))
        self.assertTrue(documents)
        for document in documents:
            text = document.read_text(encoding="utf-8")
            references = [
                (PLUGIN_ROOT, target)
                for target in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^`\s]+)", text)
            ]
            if document.name == "SKILL.md":
                references.extend(
                    (document.parent, target)
                    for target in re.findall(r"`(references/[^`]+\.md)`", text)
                )
            references.extend(
                (document.parent, target)
                for target in re.findall(r"\]\(([^)]+)\)", text)
                if not urlsplit(target).scheme
                and not target.startswith("#")
                and "{{" not in target
            )
            for base, target in references:
                with self.subTest(document=str(document), reference=target):
                    path = (base / target.split("#", 1)[0]).resolve()
                    self.assertTrue(path.is_relative_to(PLUGIN_ROOT.resolve()), target)
                    self.assertTrue(path.is_file(), target)


if __name__ == "__main__":
    unittest.main()
