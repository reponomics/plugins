#!/usr/bin/env python3
"""Download, compare, and refresh the shipped criteria catalog (maintainers only)."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml

from criteria_download import atomic_write, digest, download_snapshot, json_bytes, now, read_snapshot
from criteria_site import BASE_URL, REPOSITORY_ONLY_FIELDS, SECTIONS, VISIBLE_FIELDS, compare_sections
from criteria_source import build_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "plugins/badge-buddy/assets/criteria/criteria.json"
SNAPSHOT = ROOT / ".cache/criteria/site"


def read_catalog(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if payload.get("schema_version") != 1 or set(payload.get("sections", {})) != set(SECTIONS):
        raise ValueError(f"{path}: expected a complete version 1 criteria catalog")
    for section, records in payload["sections"].items():
        ids = [record["id"] for record in records]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError(f"{section}: empty section or duplicate IDs")
    return payload


def verification_path(catalog: Path) -> Path:
    return catalog.with_name("verification.json")


def compare(catalog: dict[str, Any], snapshot: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest, pages = read_snapshot(snapshot)
    differences = compare_sections(catalog, pages)
    semantic_sha = digest(json.dumps(pages, sort_keys=True, ensure_ascii=False).encode())
    report = {
        "schema_version": 1, "checked_at": now(), "status": "different" if differences else "match",
        "repository": catalog["source"], "website_observed_at": manifest["downloaded_at"],
        "website_semantic_sha256": semantic_sha,
        "checked_fields": ["ids_and_order", *VISIBLE_FIELDS],
        "repository_only_fields": list(REPOSITORY_ONLY_FIELDS),
        "section_counts": {name: len(pages[name]) for name in SECTIONS}, "differences": differences,
    }
    atomic_write(snapshot / "report.json", json_bytes(report))
    receipt = {
        "schema_version": 1, "repository": catalog["source"],
        "website": {key: manifest[key] for key in ("base_url", "project_id", "downloaded_at")},
        "pages": {section: {key: page[key] for key in ("url", "sha256")} for section, page in manifest["pages"].items()},
        "website_semantic_sha256": semantic_sha,
        "checked_fields": report["checked_fields"], "repository_only_fields": report["repository_only_fields"],
    }
    return report, receipt


def _print_report(report: dict[str, Any], snapshot: Path) -> bool:
    if report["differences"]:
        print(f"Application comparison: {len(report['differences'])} differences; see {snapshot / 'report.json'}", file=sys.stderr)
        for item in report["differences"][:20]:
            print(f"  {item['section']}:{item.get('id', '*')}: {item['field']}", file=sys.stderr)
        return False
    counts = ", ".join(f"{name}={count}" for name, count in report["section_counts"].items())
    print(f"Application comparison matches ({counts}).")
    return True


def refresh(badge_repo: Path, snapshot: Path, catalog_path: Path = CATALOG) -> int:
    candidate = build_catalog(badge_repo)
    atomic_write(snapshot / "candidate.json", json_bytes(candidate))
    report, receipt = compare(candidate, snapshot)
    if not _print_report(report, snapshot):
        return 1
    serialized = json_bytes(candidate)
    receipt["catalog_sha256"] = digest(serialized)
    target = verification_path(catalog_path)
    if _unchanged(catalog_path, serialized, target, receipt):
        print("Bundled catalog and verification are unchanged.")
        return 0
    # Never publish a candidate before all extraction and comparison succeeds.
    # The receipt binds the bytes; an interrupted two-file update is detectable
    # by check/release-check and can be repaired by rerunning this command.
    atomic_write(catalog_path, serialized)
    atomic_write(target, json_bytes(receipt))
    print(f"Refreshed {catalog_path} and {target.name}.")
    return 0


def _unchanged(catalog: Path, serialized: bytes, target: Path, receipt: dict[str, Any]) -> bool:
    if not catalog.exists() or catalog.read_bytes() != serialized or not target.exists():
        return False
    try:
        previous = json.loads(target.read_text())
        _validate_provenance(previous)
    except (ValueError, OSError):
        return False
    # Keep the last accepted observation on no-op refreshes. A fresh local/CI
    # report still records each verification without weekly timestamp-only PRs.
    keys = ("schema_version", "catalog_sha256", "repository", "website_semantic_sha256",
            "checked_fields", "repository_only_fields")
    return all(previous.get(key) == receipt[key] for key in keys)


def check(badge_repo: Path, snapshot: Path, catalog_path: Path = CATALOG) -> int:
    shipped = read_catalog(catalog_path)
    candidate = build_catalog(badge_repo)
    report, receipt = compare(shipped, snapshot)
    site_matches = _print_report(report, snapshot)
    if candidate != shipped:
        print("Bundled catalog differs from the selected repository checkout; run refresh-criteria.", file=sys.stderr)
        return 1
    _check_receipt(catalog_path, receipt)
    return 0 if site_matches else 1


def _validate_provenance(receipt: Any) -> None:
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 1:
        raise ValueError("unsupported catalog verification receipt")
    website = receipt.get("website")
    if (not isinstance(website, dict) or website.get("base_url") != BASE_URL
            or type(website.get("project_id")) is not int or website.get("project_id") != 1):
        raise ValueError("catalog verification has an invalid application origin or project")
    observed_at = website.get("downloaded_at")
    if not isinstance(observed_at, str):
        raise ValueError("catalog verification has no website observation timestamp")
    timestamp = dt.datetime.fromisoformat(observed_at)
    if timestamp.utcoffset() != dt.timedelta(0) or timestamp > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        raise ValueError("catalog verification timestamp must be a past UTC observation")
    _validate_page_provenance(receipt.get("pages"))


def _validate_page_provenance(pages: Any) -> None:
    if not isinstance(pages, dict) or set(pages) != set(SECTIONS):
        raise ValueError("catalog verification must describe all six application pages")
    for section, page in pages.items():
        if not isinstance(page, dict) or page.get("url") != f"{BASE_URL}/en/projects/1/{section}":
            raise ValueError(f"{section}: invalid catalog verification page URL")
        sha = page.get("sha256")
        if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{64}", sha) is None:
            raise ValueError(f"{section}: invalid catalog verification page checksum")


def _check_receipt(catalog_path: Path, receipt: dict[str, Any]) -> None:
    saved = json.loads(verification_path(catalog_path).read_text())
    _validate_provenance(saved)
    if saved.get("catalog_sha256") != digest(catalog_path.read_bytes()):
        raise ValueError("catalog verification checksum differs; run refresh-criteria")
    keys = ("schema_version", "repository", "website_semantic_sha256", "checked_fields", "repository_only_fields")
    if any(saved.get(key) != receipt[key] for key in keys):
        raise ValueError("catalog verification does not describe these inputs; run refresh-criteria")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("download", "compare", "refresh", "check"))
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--badge-repo", type=Path, default=ROOT.parent / "best-practices-badge")
    args = parser.parse_args(argv)
    try:
        result = _run(args)
        (args.snapshot / "last-error.json").unlink(missing_ok=True)
        return result
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        atomic_write(args.snapshot / "last-error.json", json_bytes({"status": "error", "command": args.command, "at": now(), "error": str(error)}))
        print(f"Criteria {args.command} failed: {error}", file=sys.stderr)
        return 1


def _run(args: argparse.Namespace) -> int:
    if args.command == "download":
        manifest = download_snapshot(args.snapshot)
        print(f"Downloaded {len(manifest['pages'])} application pages to {args.snapshot}.")
        return 0
    if args.command == "compare":
        report, _ = compare(read_catalog(args.catalog), args.snapshot)
        return 0 if _print_report(report, args.snapshot) else 1
    if args.command == "refresh":
        return refresh(args.badge_repo, args.snapshot, args.catalog)
    return check(args.badge_repo, args.snapshot, args.catalog)


if __name__ == "__main__":
    raise SystemExit(main())
