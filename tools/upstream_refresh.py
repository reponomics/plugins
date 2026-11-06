#!/usr/bin/env python3
"""Local upstream checkout, provenance, and catalog change summaries.

Automation-reference review dates are maintained by reviewers, never by refresh.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "plugins" / "badge-buddy" / "assets" / "criteria" / "criteria.json"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
NOTICES_PIN = re.compile(r"at commit `([0-9a-f]{40})`")
COMPARED_FIELDS = (
    "display_id",
    "future",
    "obsolete",
    "category",
    "description",
    "details",
    "na_allowed",
    "na_justification_required",
    "met_justification_required",
    "met_url_required",
)


def catalog_commit(path: Path) -> str:
    commit = json.loads(path.read_text(encoding="utf-8"))["source"]["commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit(f"{path}: source.commit is not a full SHA: {commit!r}")
    return commit


def rewrite_pins(commit: str) -> list[str]:
    messages: list[str] = []

    notices = NOTICES.read_text(encoding="utf-8")
    match = NOTICES_PIN.search(notices)
    if match is None:
        raise SystemExit(f"{NOTICES}: no pinned commit found")
    if match.group(1) != commit:
        NOTICES.write_text(NOTICES_PIN.sub(f"at commit `{commit}`", notices, count=1), encoding="utf-8")
        messages.append(f"{NOTICES.name}: {match.group(1)[:8]} -> {commit[:8]}")

    return messages or ["pins already match the catalog"]


def load_sections(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    return {
        section: {record["id"]: record for record in records}
        for section, records in catalog["sections"].items()
    }


def _changed_fields(section: str, before: dict, after: dict) -> list[str]:
    changed = []
    for cid in after:
        if cid not in before:
            continue
        fields = [field for field in COMPARED_FIELDS if before[cid].get(field) != after[cid].get(field)]
        if fields:
            changed.append(f"`{cid}` ({section}: {', '.join(fields)})")
    return changed


def _section_changes(section: str, before: dict, after: dict) -> dict[str, list[str]]:
    before_order = [cid for cid in before if cid in after]
    after_order = [cid for cid in after if cid in before]
    return {
        "Added": [f"`{cid}` ({section})" for cid in after if cid not in before],
        "Removed": [f"`{cid}` ({section})" for cid in before if cid not in after],
        "Changed fields": _changed_fields(section, before, after),
        "Reordered sections": [section] if before_order != after_order else [],
    }


def _summary_block(title: str, items: list[str]) -> list[str]:
    if not items:
        return ["", f"**{title}:** none"]
    return ["", f"**{title} ({len(items)}):**", ""] + [f"- {item}" for item in items]


def summarize(old_path: Path, new_path: Path) -> str:
    old, new = load_sections(old_path), load_sections(new_path)
    lines = ["## Catalog changes", "", "| Section | Before | After |", "|---|---|---|"]
    changes: dict[str, list[str]] = {"Added": [], "Removed": [], "Changed fields": [], "Reordered sections": []}
    for section in sorted(set(old) | set(new)):
        before, after = old.get(section, {}), new.get(section, {})
        lines.append(f"| {section} | {len(before)} | {len(after)} |")
        for title, items in _section_changes(section, before, after).items():
            changes[title].extend(items)
    for title, items in changes.items():
        lines.extend(_summary_block(title, items))
    return "\n".join(lines) + "\n"


def run(*args: str, cwd: Path = ROOT) -> str:
    """Run without a shell, preserving errors for the caller."""
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE)
    if result.returncode:
        print(result.stdout, file=sys.stderr, end="")
        result.check_returncode()
    return result.stdout.strip()


def checkout(destination: Path, ref: str) -> None:
    """Create a new detached checkout; never reset an existing local repository."""
    if destination.exists():
        raise ValueError(f"Checkout destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    run("git", "init", str(destination))
    run("git", "-C", str(destination), "remote", "add", "origin",
        "https://github.com/ossf/best-practices-badge.git")
    run("git", "-C", str(destination), "fetch", "--depth=1", "origin", ref)
    run("git", "-C", str(destination), "checkout", "--detach", "FETCH_HEAD")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pins = commands.add_parser("pins", help="update catalog provenance; preserve human review dates")
    pins.add_argument("--catalog", type=Path, default=CATALOG)
    summary = commands.add_parser("summary", help="summarize catalog changes")
    summary.add_argument("--old", type=Path, required=True)
    summary.add_argument("--new", type=Path, default=CATALOG)
    clone = commands.add_parser("checkout", help="create upstream checkout at the catalog pin or an explicit ref")
    clone.add_argument("--destination", type=Path, required=True)
    clone.add_argument("--ref", help="defaults to the bundled catalog source commit")
    args = parser.parse_args(argv)
    try:
        if args.command == "pins":
            print("\n".join(rewrite_pins(catalog_commit(args.catalog))))
        elif args.command == "summary":
            print(summarize(args.old, args.new), end="")
        else:
            checkout(args.destination.resolve(), args.ref or catalog_commit(CATALOG))
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"upstream refresh: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
