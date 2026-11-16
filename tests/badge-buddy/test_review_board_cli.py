"""Exercise the standalone offline board entry point through real files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/badge-buddy/scripts/review_board.py"


class ReviewBoardCliTest(unittest.TestCase):
    def test_all_six_levels_render_without_modifying_input(self):
        with tempfile.TemporaryDirectory(prefix="badge board ") as directory:
            root = Path(directory)
            draft = root / "draft.json"
            original = (
                '{"description_good_status":"Met","OSPS-AC-01.01_status":"Met"}\n'
            )
            draft.write_text(original)
            for level in (
                "passing",
                "silver",
                "gold",
                "baseline-1",
                "baseline-2",
                "baseline-3",
            ):
                with self.subTest(level=level):
                    output = root / f"{level}.html"
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "--input",
                            str(draft),
                            "--output",
                            str(output),
                            "--project-id",
                            "31",
                            "--section",
                            level,
                        ],
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    self.assertEqual(
                        output.resolve().as_uri() + "#view=all",
                        json.loads(result.stdout)["url"],
                    )
                    self.assertIn(f'"section":"{level}"', output.read_text())
                    self.assertEqual(original, draft.read_text())

    def test_invalid_input_and_same_destination_fail_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "draft.json"
            for contents, output in (
                ("[]", root / "board.html"),
                ("{}", source),
                ("bad json", root / "board.html"),
            ):
                with self.subTest(contents=contents):
                    source.write_text(contents)
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "--input",
                            str(source),
                            "--output",
                            str(output),
                            "--project-id",
                            "31",
                            "--section",
                            "baseline-1",
                        ],
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(1, result.returncode)
                    self.assertEqual(contents, source.read_text())
                    if output != source:
                        self.assertFalse(output.exists())

    def test_project_mismatch_does_not_create_or_replace_board(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "draft.json"
            source.write_text('{"id": 32, "description_good_status": "Met"}')
            output = root / "board.html"
            for existing in (False, True):
                if existing:
                    output.write_text("previous preview")
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--input",
                        str(source),
                        "--output",
                        str(output),
                        "--project-id",
                        "31",
                        "--section",
                        "passing",
                    ],
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("does not match", result.stderr)
                if existing:
                    self.assertEqual("previous preview", output.read_text())
                else:
                    self.assertFalse(output.exists())

    def test_matching_numeric_id_and_local_label_can_render(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "draft.json"
            source.write_text('{"id": 31}')
            for selected in ("31", "Local draft"):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--input",
                        str(source),
                        "--output",
                        str(root / "board.html"),
                        "--project-id",
                        selected,
                        "--section",
                        "passing",
                    ],
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)
