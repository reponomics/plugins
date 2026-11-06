"""Offline checks for catalog changes, review provenance, and local checkouts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("upstream_refresh", ROOT / "tools/upstream_refresh.py")
assert SPEC and SPEC.loader
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)


class RefreshTest(unittest.TestCase):
    def test_summary_tracks_display_id_order_and_flags(self):
        before = {"sections": {"passing": [
            {"id": "a", "display_id": "1", "met_url_required": False},
            {"id": "b", "display_id": "2"}]}}
        after = {"sections": {"passing": [
            {"id": "b", "display_id": "2"},
            {"id": "a", "display_id": "3", "met_url_required": True, "future": True, "obsolete": True}]}}
        with tempfile.TemporaryDirectory() as directory:
            old, new = Path(directory) / "old.json", Path(directory) / "new.json"
            old.write_text(json.dumps(before))
            new.write_text(json.dumps(after))
            result = refresh.summarize(old, new)
        self.assertIn("display_id, future, obsolete, met_url_required", result)
        self.assertIn("**Reordered sections (1):**\n\n- passing", result)

    def test_pins_preserve_human_review_record(self):
        with tempfile.TemporaryDirectory() as directory:
            notice, reference = Path(directory) / "notice.md", Path(directory) / "reference.md"
            notice.write_text("at commit `" + "a" * 40 + "`")
            reference.write_text("commit " + "a" * 40 + ", read on 2020-01-01")
            with patch.object(refresh, "NOTICES", notice):
                refresh.rewrite_pins("b" * 40)
            self.assertIn("b" * 40, notice.read_text())
            self.assertEqual("commit " + "a" * 40 + ", read on 2020-01-01", reference.read_text())

    def test_checkout_never_resets_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(refresh, "run") as run:
            with self.assertRaisesRegex(ValueError, "already exists"):
                refresh.checkout(Path(directory), "production")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
