"""Application verification fixtures contain no downloaded project responses."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from criteria_site import compare_sections, normalized_text, parse_application, SECTIONS  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def catalog_records() -> list[dict]:
    return [
        {"id": "alpha", "category": "MUST", "description":
         'The project MUST publish a security policy at <a href="https://www.bestpractices.dev/en/help">this address</a>.',
         "details": '<div>Use public documentation.</div><div>See <a href="https://example.org/guide">the guide</a>.</div>',
         "na_allowed": True, "met_url_required": True},
        {"id": "require_2FA", "category": "MUST", "description": "Require multi-factor authentication.",
         "details": None, "future": True},
        {"id": "osps_ac_01_01", "display_id": "OSPS-AC-01.01", "category": "MUST",
         "description": "Preserve a historical control.", "details": None,
         "na_allowed": True, "obsolete": True},
    ]


class ApplicationParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (FIXTURES / "application.html").read_text()

    def test_application_recovers_overlapping_markup_and_order(self) -> None:
        rows = parse_application(self.html)
        self.assertEqual([row["id"] for row in rows], ["alpha", "require_2FA", "osps_ac_01_01"])
        alpha, future, obsolete = rows
        self.assertEqual(alpha["description"], "The project MUST publish a security policy at this address.")
        self.assertEqual(alpha["details"], "Use public documentation. See the guide.")
        self.assertEqual(alpha["description_links"], [{"text": "this address", "href": "https://www.bestpractices.dev/en/help"}])
        self.assertEqual(alpha["details_links"], [{"text": "the guide", "href": "https://example.org/guide"}])
        self.assertTrue(alpha["na_allowed"])
        self.assertTrue(alpha["met_url_required"])
        self.assertTrue(future["future"])
        self.assertFalse(future["na_allowed"])
        self.assertFalse(future["met_url_required"])
        self.assertEqual(future["details"], "")
        self.assertTrue(obsolete["obsolete"])
        self.assertEqual(obsolete["display_id"], "OSPS-AC-01.01")

    def test_project_answers_results_and_warnings_do_not_change_definitions(self) -> None:
        changed = self.html.replace('data-status="Met"', 'data-status="Unmet"')
        changed = changed.replace('value="Met" checked', 'value="Met"')
        changed = changed.replace('value="Unmet">', 'value="Unmet" checked>')
        changed = changed.replace("Project-specific response", "Different response")
        changed = changed.replace("criterion-passing", "criterion-failing")
        changed = changed.replace('src="check.png" alt="Passing"', 'src="failure.png" alt="Failing"')
        changed = changed.replace("project URL", "another project URL")
        changed = changed.replace("https://example.org/project-answer", "https://different.example/evidence")
        changed = changed.replace("A project-specific warning.", "A different project-specific warning.")
        self.assertEqual(parse_application(self.html), parse_application(changed))
        self.assertNotIn("project-answer", str(parse_application(changed)))

    def test_criteria_list_annotations_are_not_an_application_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "no criteria"):
            parse_application((FIXTURES / "criteria-list.html").read_text())
        changed = self.html.replace("</body>", '<aside>{N/A justification} {Met URL}</aside></body>')
        self.assertEqual(parse_application(self.html), parse_application(changed))

    def test_missing_criterion_structure_rejected(self) -> None:
        mutations = {
            "description": ('class="criteria-desc"', 'class="missing-description"'),
            "row ID": ('id="alpha"', 'id=""'),
            "display ID": ('<sup>[alpha]</sup>', ''),
            "invalid display ID": ('<sup>[alpha]</sup>', '<sup>alpha</sup>'),
            "status field": ('name="project[alpha_status]"', 'name="wrong"'),
            "Met option": ('value="Met" checked', 'value="Unexpected" checked'),
            "all options": ('class="criteria-radio"', 'class="not-radio"'),
            "empty description": ('The project MUST publish a <strong>security</strong> policy at <a href="/en/help">this address</a>.', ''),
            "missing translation": ('The project MUST publish', 'translation missing: criteria.alpha MUST publish'),
            "details ID": ('id="alpha_details_text"', 'id="wrong_details_text"'),
        }
        for label, (before, after) in mutations.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                parse_application(self.html.replace(before, after, 1))

    def test_duplicate_rows_options_and_details_rejected(self) -> None:
        duplicate_row = self.html.replace('id="require_2FA"', 'id="alpha"').replace('project[require_2FA_status]', 'project[alpha_status]')
        with self.assertRaisesRegex(ValueError, "duplicate criterion IDs"):
            parse_application(duplicate_row)
        duplicate_option = self.html.replace('value="Unmet"', 'value="Met"', 1)
        with self.assertRaises(ValueError):
            parse_application(duplicate_option)
        duplicate_details = self.html.replace('<button>Details</button>', '<button>Details</button><div class="details-text" id="alpha_details_text">Duplicate</div>')
        with self.assertRaisesRegex(ValueError, "duplicate details"):
            parse_application(duplicate_details)

    def test_wrong_locale_and_login_pages_rejected(self) -> None:
        for language in ('lang="fr"', 'lang="en-US"', ''):
            with self.subTest(language=language), self.assertRaisesRegex(ValueError, "English"):
                parse_application(self.html.replace('lang="en"', language))
        with self.assertRaisesRegex(ValueError, "no criteria"):
            parse_application('<html lang="en"><body><h1>Sign in</h1><input name="password"></body></html>')

    def test_formatting_normalization_keeps_word_boundaries_and_links(self) -> None:
        normalized = normalized_text('re<strong>use</strong><br>safe<p>content &amp; links</p><!-- hidden --><script>bad()</script><style>body{}</style>')
        self.assertEqual(normalized, {"text": "reuse safe content & links", "links": []})


class ApplicationComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        rows = parse_application((FIXTURES / "application.html").read_text())
        self.catalog = {"sections": {section: copy.deepcopy(catalog_records()) for section in SECTIONS}}
        self.pages = {section: copy.deepcopy(rows) for section in SECTIONS}

    def test_matching_text_flags_lifecycle_links_and_order(self) -> None:
        self.assertEqual(compare_sections(self.catalog, self.pages), [])

    def test_false_and_absent_flags_are_equivalent(self) -> None:
        for section in SECTIONS:
            for record in self.catalog["sections"][section]:
                for field in ("future", "obsolete", "na_allowed", "met_url_required"):
                    record.setdefault(field, False)
        self.assertEqual(compare_sections(self.catalog, self.pages), [])

    def test_repository_only_fields_are_not_claimed_as_verified(self) -> None:
        for record in self.catalog["sections"]["passing"]:
            record.update(category="SHOULD", na_justification_required=True, met_justification_required=True)
        self.assertEqual(compare_sections(self.catalog, self.pages), [])

    def test_all_six_sections_are_required(self) -> None:
        del self.pages["gold"]
        with self.assertRaisesRegex(ValueError, "all six sections"):
            compare_sections(self.catalog, self.pages)
        del self.catalog["sections"]["gold"]
        with self.assertRaisesRegex(ValueError, "all six sections"):
            compare_sections(self.catalog, self.pages)

    def test_changed_order_and_missing_entries_are_reported(self) -> None:
        self.pages["passing"].reverse()
        self.pages["gold"].pop()
        differences = compare_sections(self.catalog, self.pages)
        self.assertEqual([(d["section"], d["field"]) for d in differences], [("passing", "ids_and_order"), ("gold", "ids_and_order")])

    def test_link_target_change_is_detected_without_wording_change(self) -> None:
        self.pages["passing"][0]["description_links"][0]["href"] = "https://different.example/help"
        self.pages["silver"][0]["details_links"][0]["href"] = "https://different.example/guide"
        differences = compare_sections(self.catalog, self.pages)
        self.assertEqual([(d["section"], d["field"]) for d in differences], [("passing", "description_links"), ("silver", "details_links")])

    def test_flags_display_id_and_missing_details_detected(self) -> None:
        self.pages["passing"][0]["met_url_required"] = False
        self.pages["silver"][0]["na_allowed"] = False
        self.pages["gold"][1]["future"] = False
        self.pages["baseline-1"][2]["display_id"] = "OSPS-AC-99.99"
        self.pages["baseline-2"][0]["details"] = ""
        self.pages["baseline-3"][2]["obsolete"] = False
        self.assertEqual([d["field"] for d in compare_sections(self.catalog, self.pages)], ["met_url_required", "na_allowed", "future", "display_id", "details", "obsolete"])


if __name__ == "__main__":
    unittest.main()
