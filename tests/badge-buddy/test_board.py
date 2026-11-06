from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
from typing import ClassVar
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2] / "plugins" / "badge-buddy"
SCRIPT_ROOT = REPOSITORY_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from ossf_review.board import (  # noqa: E402
    build_board_payload,
    plain_text,
    render_board,
    review_path,
    write_board,
)
from ossf_review.criteria import CriteriaCatalog  # noqa: E402


class PassiveBoardTests(unittest.TestCase):
    catalog: ClassVar[CriteriaCatalog]

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = CriteriaCatalog()

    def test_payload_groups_canonical_statuses_into_buckets(self) -> None:
        payload = build_board_payload(
            {
                "description_good_status": "Met",
                "description_good_justification": "Repository evidence.",
                "interact_status": "Unmet",
                "sites_https_status": "N/A",
                "sites_https_justification": "No project website exists.",
            },
            project_id="31",
            section="passing",
            catalog=self.catalog,
        )

        counts = {bucket["key"]: bucket["count"] for bucket in payload["buckets"]}
        ordered_ids = [criterion.id for criterion in self.catalog.section("passing")]
        self.assertEqual(ordered_ids, [criterion["id"] for criterion in payload["criteria"]])
        self.assertEqual(len(ordered_ids), payload["total"])
        self.assertEqual({"needs_input", "unmet", "na", "met"}, set(counts))
        classified_ids = [
            identifier
            for bucket in payload["buckets"]
            for identifier in bucket["criterionIds"]
        ]
        self.assertCountEqual(ordered_ids, classified_ids)
        self.assertEqual(payload["total"], sum(counts.values()))
        self.assertEqual(1, counts["met"])
        self.assertEqual(1, counts["unmet"])
        self.assertEqual(1, counts["na"])
        self.assertEqual(payload["total"] - 3, counts["needs_input"])
        self.assertEqual("Met", payload["answers"]["description_good"]["status"])

    def test_criterion_html_preserves_readable_text(self) -> None:
        cases = (
            ("", ""),
            ("  Plain\n text\t here  ", "Plain text here"),
            ("<p>A &amp; B</p><p>Next<br>line</p>", "A & B Next line"),
            ('Use <a href="https://example.com">public</a> evidence.', "Use public evidence."),
            ("<ul><li>One</li><li><em>Two</em></li></ul>", "One Two"),
        )
        for markup, expected in cases:
            with self.subTest(markup=markup):
                self.assertEqual(expected, plain_text(markup))

    def test_future_and_obsolete_criteria_retain_order_and_visible_labels(self) -> None:
        source = json.loads(self.catalog.asset_path.read_text())
        original_ids = [row["id"] for row in source["sections"]["passing"]]
        source["sections"]["passing"][0]["future"] = True
        source["sections"]["passing"][1]["obsolete"] = True
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / "criteria.json"
            asset.write_text(json.dumps(source))
            payload = build_board_payload(
                {}, project_id="31", section="passing", catalog=CriteriaCatalog(asset)
            )
        self.assertEqual(original_ids, [row["id"] for row in payload["criteria"]])
        self.assertTrue(payload["criteria"][0]["description"].startswith("(Future criterion) "))
        self.assertTrue(payload["criteria"][1]["description"].startswith("(Obsolete criterion) "))
        self.assertEqual(len(original_ids), payload["total"])

    def test_board_embeds_bundled_styles_and_script(self) -> None:
        payload = build_board_payload(
            {"description_good_status": "Met"},
            project_id="31",
            section="passing",
            catalog=self.catalog,
        )
        markup = render_board(payload)
        for filename in ("review.css", "review.js"):
            with self.subTest(asset=filename):
                asset = REPOSITORY_ROOT / "assets" / "review" / filename
                self.assertIn(asset.read_text(encoding="utf-8"), markup)

    def test_embedded_json_cannot_close_its_script_element(self) -> None:
        payload = build_board_payload(
            {
                "description_good_status": "Met",
                "description_good_justification": "</script><script>alert(1)</script>",
            },
            project_id="31",
            section="passing",
            catalog=self.catalog,
        )
        markup = render_board(payload)

        self.assertNotIn("</script><script>alert(1)</script>", markup)
        self.assertIn("\\u003c/script\\u003e", markup)

    def test_review_paths_are_stable_and_write_uses_explicit_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = review_path(temp_dir, "31", "passing")
            second = review_path(temp_dir, "31", "passing")
            other = review_path(temp_dir, "31", "silver")
            self.assertEqual(first, second)
            self.assertNotEqual(first, other)

            destination = Path(temp_dir) / "board.html"
            returned = write_board(
                {"description_good_status": "Unmet"},
                destination,
                project_id="31",
                section="passing",
                catalog=self.catalog,
            )
            self.assertEqual(destination, returned)
            self.assertEqual(["board.html"], [item.name for item in destination.parent.iterdir()])
            self.assertIn(
                '"description_good":{"status":"Unmet"',
                destination.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
