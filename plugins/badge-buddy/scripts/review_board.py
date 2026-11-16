#!/usr/bin/env python3
"""Render an explicit draft as a passive local board, without BadgeApp access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import webbrowser

from ossf_review.board import write_board
from ossf_review.criteria import CriteriaCatalog, SECTION_NAMES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, required=True, help="existing flat draft JSON"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="local HTML destination"
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="selected BadgeApp project ID or local label",
    )
    parser.add_argument("--section", choices=SECTION_NAMES, required=True)
    parser.add_argument("--view", choices=("overview", "all"), default="all")
    parser.add_argument(
        "--open", action="store_true", help="open the local board in a browser"
    )
    return parser


def _check_project_identity(document: dict, project_id: str) -> None:
    """Do not label a registered project's draft as another numeric project."""
    recorded = document.get("id")
    if not project_id.isdecimal() or recorded is None:
        return
    if (
        isinstance(recorded, bool)
        or not isinstance(recorded, (str, int))
        or not str(recorded).isdecimal()
        or int(recorded) != int(project_id)
    ):
        raise ValueError("The draft id does not match the selected project ID.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = args.input.resolve()
        destination = args.output.resolve()
        if source == destination:
            raise ValueError("The board output must not replace the input draft.")
        document = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("The input draft must be a JSON object.")
        _check_project_identity(document, args.project_id)
        write_board(
            document,
            destination,
            project_id=args.project_id,
            section=args.section,
            catalog=CriteriaCatalog(),
        )
        url = destination.as_uri() + f"#view={args.view}"
        if args.open:
            webbrowser.open(url)
        print(
            json.dumps(
                {"output": str(destination), "url": url, "section": args.section}
            )
        )
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Could not render review board: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
