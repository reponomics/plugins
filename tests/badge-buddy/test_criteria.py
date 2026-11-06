from __future__ import annotations

from pathlib import Path
import sys
from typing import ClassVar
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "badge-buddy"
SCRIPT_ROOT = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from ossf_review.criteria import CriteriaCatalog  # noqa: E402
from spec_pins import EXPECTED_SECTION_TOTALS  # noqa: E402


class CriteriaCatalogTests(unittest.TestCase):
    catalog: ClassVar[CriteriaCatalog]

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = CriteriaCatalog()

    def test_current_section_counts(self) -> None:
        self.assertEqual(
            {
                name: len(self.catalog.section(name))
                for name in EXPECTED_SECTION_TOTALS
            },
            EXPECTED_SECTION_TOTALS,
        )

    def test_flat_responses_are_bucketed_and_baseline_aliases_merge(self) -> None:
        result = self.catalog.classify_flat(
            {
                "name": "Example",
                "description_good_status": "Met",
                "OSPS-AC-01.01_status": "?",
                "osps_ac_01_01_justification": "Needs review",
                "not_a_criterion_status": "Met",
            }
        )
        self.assertEqual(result["passing"]["description_good"], {"status": "Met"})
        self.assertEqual(
            result["baseline-1"]["osps_ac_01_01"],
            {"status": "?", "justification": "Needs review"},
        )
        self.assertNotIn("not_a_criterion", result["passing"])


if __name__ == "__main__":
    unittest.main()
