"""Catalog provenance matches notices; cited documents appear in the manual review inventory."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "badge-buddy"
CATALOG = PLUGIN / "assets" / "criteria" / "criteria.json"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
REFERENCE = ROOT / "docs" / "criteria-maintenance.md"
REVIEW_PATHS = ROOT / "upstream-review-paths.txt"
CITED = re.compile(r"(?:(?:docs|criteria)/)?[\w.-]+\.(?:md|py|yml)")


class UpstreamPinTest(unittest.TestCase):
    def test_catalog_provenance_matches_notices(self) -> None:
        commit = json.loads(CATALOG.read_text(encoding="utf-8"))["source"]["commit"]
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertIn(f"at commit `{commit}`", NOTICES.read_text(encoding="utf-8"))

    def test_every_cited_upstream_document_is_in_review_inventory(self) -> None:
        review_paths = [
            line.strip()
            for line in REVIEW_PATHS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        cited: set[str] = set()
        for line in REFERENCE.read_text(encoding="utf-8").splitlines():
            if not line.startswith("Source:"):
                continue
            for token in CITED.findall(line):
                path = token if "/" in token else f"docs/{token}"
                if path.startswith(("docs/", "criteria/")):
                    cited.add(path)
        self.assertTrue(cited, "the reference cites no upstream files")
        for path in sorted(cited):
            with self.subTest(path=path):
                self.assertTrue(
                    any(path == p or (p.endswith("/") and path.startswith(p)) for p in review_paths),
                    f"{path} is cited by the reference but not listed in {REVIEW_PATHS.name}",
                )


if __name__ == "__main__":
    unittest.main()
