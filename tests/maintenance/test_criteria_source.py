"""Source extraction tests use committed synthetic clones, without networking."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from criteria_source import build_catalog  # noqa: E402


class CriteriaSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.metal = {
            level: {"General": {"Controls": {"shared": {"category": "MUST"}}}}
            for level in ("0", "1", "2")
        }
        self.baseline = {
            f"baseline-{n}": {"General": {"Controls": {f"osps_ac_01_0{n}": {
                "category": "MUST", "original_id": f"OSPS-AC-01.0{n}",
                "description": "YAML source is not the rendered translation",
                "details": "Also not rendered", "met_url_required": False,
            }}}} for n in (1, 2, 3)
        }
        self.locale = {"en": {"criteria": {
            **{level: {"shared": {"description": f"Level {level}"}}
               for level in ("0", "1", "2")},
            **{f"baseline-{n}": {f"osps_ac_01_0{n}": {
                "description": f"Baseline {n}", "details": "English details"
            }} for n in (1, 2, 3)},
        }}}
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Test Fixture")
        self.write_and_commit()

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], check=True,
            text=True, capture_output=True,
        ).stdout.strip()

    def write_and_commit(self) -> None:
        for name, data in (
            ("criteria/criteria.yml", self.metal),
            ("criteria/baseline_criteria.yml", self.baseline),
            ("config/locales/en.yml", self.locale),
        ):
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Fixture", "--allow-empty")

    def test_locale_and_explicit_false_and_provenance(self) -> None:
        catalog = build_catalog(self.repo)
        self.assertEqual(catalog["source"]["commit"], self.git("rev-parse", "HEAD"))
        baseline = catalog["sections"]["baseline-1"][0]
        self.assertEqual(baseline["description"], "Baseline 1")
        self.assertEqual(baseline["details"], "English details")
        self.assertEqual(baseline["display_id"], "OSPS-AC-01.01")
        self.assertIs(baseline["met_url_required"], False)
        self.assertIs(baseline["na_allowed"], False)

    def test_description_must_exist_at_current_level(self) -> None:
        del self.locale["en"]["criteria"]["1"]["shared"]["description"]
        self.write_and_commit()
        with self.assertRaisesRegex(ValueError, "no locale description at this level"):
            build_catalog(self.repo)

    def test_details_fallback_only_visits_levels_defining_criterion(self) -> None:
        locale = self.locale["en"]["criteria"]
        locale["0"]["shared"]["details"] = "Passing details"
        locale["1"]["shared"]["details"] = "Unused translation"
        self.metal["1"]["General"]["Controls"] = {"other": {"category": "SHOULD"}}
        locale["1"]["other"] = {"description": "Other"}
        self.write_and_commit()
        record = build_catalog(self.repo)["sections"]["gold"][0]
        self.assertEqual(record["details"], "Passing details")

    def test_empty_details_do_not_fall_back(self) -> None:
        locale = self.locale["en"]["criteria"]
        locale["0"]["shared"]["details"] = "Passing details"
        locale["1"]["shared"]["details"] = ""
        self.write_and_commit()
        self.assertIsNone(build_catalog(self.repo)["sections"]["silver"][0]["details"])

    def test_lifecycle_records_keep_position_and_labels(self) -> None:
        records = self.metal["0"]["General"]["Controls"]
        records["shared"]["future"] = True
        records["last"] = {"category": "SUGGESTED", "obsolete": True}
        self.locale["en"]["criteria"]["0"]["last"] = {"description": "Last"}
        self.write_and_commit()
        output = build_catalog(self.repo)["sections"]["passing"]
        self.assertEqual([r["id"] for r in output], ["shared", "last"])
        self.assertIs(output[0]["future"], True)
        self.assertIs(output[1]["obsolete"], True)

    def test_invalid_boolean_category_and_id_are_rejected(self) -> None:
        meta = self.metal["0"]["General"]["Controls"]["shared"]
        for bad in ("false", 0, None):
            with self.subTest(value=bad):
                meta["met_url_required"] = bad
                self.write_and_commit()
                with self.assertRaisesRegex(ValueError, "must be a boolean"):
                    build_catalog(self.repo)
        meta.pop("met_url_required")
        meta["category"] = "MAYBE"
        self.write_and_commit()
        with self.assertRaisesRegex(ValueError, "invalid category"):
            build_catalog(self.repo)
        meta["category"] = "MUST"
        self.metal["0"]["General"]["Controls"]["bad/id"] = {"category": "MUST"}
        self.write_and_commit()
        with self.assertRaisesRegex(ValueError, "invalid criterion ID"):
            build_catalog(self.repo)

    def test_duplicate_ids_across_groups_rejected(self) -> None:
        self.metal["0"]["Other"] = {"Other": {"shared": {"category": "MUST"}}}
        self.write_and_commit()
        with self.assertRaisesRegex(ValueError, "duplicate criterion"):
            build_catalog(self.repo)

    def test_duplicate_yaml_keys_rejected(self) -> None:
        path = self.repo / "criteria/baseline_criteria.yml"
        path.write_text(path.read_text() + "baseline-1: {}\n")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Duplicate")
        with self.assertRaisesRegex(ValueError, "duplicate YAML key"):
            build_catalog(self.repo)

    def test_ordered_maps_reject_duplicates(self) -> None:
        path = self.repo / "criteria/criteria.yml"
        path.write_text("!!omap\n- '0': {}\n- '0': {}\n")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Duplicate omap")
        with self.assertRaisesRegex(ValueError, "duplicate YAML key"):
            build_catalog(self.repo)

    def test_ordered_maps_preserve_criterion_order(self) -> None:
        self.locale["en"]["criteria"]["0"]["first"] = {"description": "First"}
        self.write_and_commit()
        path = self.repo / "criteria/criteria.yml"
        path.write_text(
            "!!omap\n- '0':\n    General:\n      Controls: !!omap\n"
            "      - first: {category: MUST}\n      - shared: {category: MUST}\n"
            "- '1': {General: {Controls: {shared: {category: MUST}}}}\n"
            "- '2': {General: {Controls: {shared: {category: MUST}}}}\n"
        )
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Ordered map")
        self.assertEqual(
            [r["id"] for r in build_catalog(self.repo)["sections"]["passing"]],
            ["first", "shared"],
        )

    def test_mismatched_baseline_display_id_rejected(self) -> None:
        self.baseline["baseline-1"]["General"]["Controls"]["osps_ac_01_01"]["original_id"] = "OSPS-AC-99.99"
        self.write_and_commit()
        with self.assertRaisesRegex(ValueError, "original_id disagrees"):
            build_catalog(self.repo)

    def test_modified_checkout_rejected_even_if_changes_are_staged(self) -> None:
        path = self.repo / "criteria/criteria.yml"
        path.write_text(path.read_text() + "\n# changed\n")
        with self.assertRaisesRegex(ValueError, "tracked changes"):
            build_catalog(self.repo)
        self.git("add", ".")
        with self.assertRaisesRegex(ValueError, "tracked changes"):
            build_catalog(self.repo)

    def test_untracked_source_cannot_claim_head_provenance(self) -> None:
        self.git("rm", "--cached", "config/locales/en.yml")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "Untrack input")
        with self.assertRaises(subprocess.CalledProcessError):
            build_catalog(self.repo)

    def test_missing_section_rejected(self) -> None:
        del self.baseline["baseline-3"]
        self.write_and_commit()
        with self.assertRaisesRegex(ValueError, "exactly three"):
            build_catalog(self.repo)


if __name__ == "__main__":
    unittest.main()
