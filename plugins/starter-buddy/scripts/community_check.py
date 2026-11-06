#!/usr/bin/env python3
"""Inventory likely GitHub Community Standards files without changing a repository.

The checker deliberately avoids calculating GitHub's health percentage. GitHub's
visible rows, REST fields, and percentage buckets are not a documented one-to-one
mapping. Local license files are candidates until GitHub recognizes their text.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


SCHEMA_VERSION = 1
SHARED_LOCATIONS = (Path(".github"), Path("."), Path("docs"))
COMMUNITY_FILE_STEMS = {
    "readme": ("readme",),
    "code_of_conduct": ("code_of_conduct", "code-of-conduct"),
    "contributing": ("contributing",),
    "security": ("security",),
}
OPTIONAL_COMMUNITY_FILE_STEMS = {
    "support": ("support",),
}
LICENSE_STEMS = ("license", "licence", "copying")
TEXT_SUFFIXES = {"", ".md", ".markdown", ".txt", ".rst", ".adoc", ".asciidoc"}
PULL_REQUEST_STEMS = ("pull_request_template", "pull-request-template")
PULL_REQUEST_SUFFIXES = {".md", ".txt"}
ISSUE_FORM_SUFFIXES = {".yml", ".yaml"}
ISSUE_MARKDOWN_SUFFIXES = {".md"}
UNSUPPORTED_ISSUE_SUFFIXES = {".markdown"}
TEMPLATE_PLACEHOLDERS = {
    "CODE_OF_CONDUCT_REFERENCE",
    "CONTRIBUTION_POSTURE",
    "DEVELOPMENT_SETUP",
    "DISCLOSURE_EXPECTATIONS",
    "PROJECT_NAME",
    "SECURITY_REPORTING_ROUTE",
    "SECURITY_POLICY_REFERENCE",
    "SUPPORTED_VERSIONS",
    "SUPPORT_EXPECTATIONS",
    "SUPPORT_ROUTES",
    "TEST_COMMANDS",
}
GENERIC_PLACEHOLDER_PATTERNS = (
    re.compile(r"\{\{[^{}\n]+\}\}"),
    re.compile(r"\bCHANGEME\b", re.IGNORECASE),
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\[INSERT[^\]\n]*\]", re.IGNORECASE),
)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_nonempty(path: Path) -> bool:
    try:
        return bool(path.read_text(encoding="utf-8").strip())
    except (OSError, UnicodeError):
        return False


def _matches_stem(path: Path, stems: Iterable[str]) -> bool:
    return path.stem.casefold() in stems


def _find_community_files(root: Path, stems: Iterable[str]) -> list[Path]:
    matches: list[Path] = []
    for relative_dir in SHARED_LOCATIONS:
        directory = root / relative_dir
        if not directory.is_dir():
            continue
        matches.extend(
            sorted(
                (
                    path
                    for path in directory.iterdir()
                    if path.is_file()
                    and path.suffix.casefold() in TEXT_SUFFIXES
                    and _matches_stem(path, stems)
                ),
                key=lambda path: path.name.casefold(),
            )
        )
    return matches


def _frontmatter_keys(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    keys: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return keys
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$", line)
        if match:
            keys[match.group(1)] = (match.group(2) or "").strip().strip("'\"")
    return {}


def _markdown_issue_template_problems(text: str) -> list[str]:
    frontmatter = _frontmatter_keys(text)
    problems: list[str] = []
    if len(frontmatter.get("name", "")) <= 3:
        problems.append("name (more than 3 characters)")
    if not frontmatter.get("about"):
        problems.append("about")
    return problems


def _inspect_issue_template(path: Path, root: Path) -> dict[str, Any]:
    suffix = path.suffix.casefold()
    if suffix in UNSUPPORTED_ISSUE_SUFFIXES:
        return {
            "path": _relative(path, root),
            "kind": "unsupported_extension",
            "checklist_candidate": False,
            "validation_scope": "filename_only",
            "validation_problems": [f"extension {suffix} (use .md)"],
        }

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        text = ""

    if suffix in ISSUE_FORM_SUFFIXES:
        kind = "issue_form"
        # Inventory only. YAML parsing belongs to an ordinary external parser.
        problems = [] if text.strip() else ["nonempty content"]
        validation_scope = "presence_only"
    else:
        kind = "markdown_template"
        problems = _markdown_issue_template_problems(text)
        validation_scope = "frontmatter_only"

    return {
        "path": _relative(path, root),
        "kind": kind,
        "checklist_candidate": bool(text.strip()) and not problems,
        "validation_scope": validation_scope,
        "validation_problems": problems,
    }


def _issue_template_details(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    directory = root / ".github" / "ISSUE_TEMPLATE"
    templates: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not directory.is_dir():
        return templates, warnings

    for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
        suffix = path.suffix.casefold()
        if not path.is_file() or path.name.casefold() in {"config.yml", "config.yaml"}:
            continue
        if suffix not in ISSUE_FORM_SUFFIXES | ISSUE_MARKDOWN_SUFFIXES | UNSUPPORTED_ISSUE_SUFFIXES:
            continue
        item = _inspect_issue_template(path, root)
        templates.append(item)
        if not item["checklist_candidate"]:
            warnings.append(
                f"{item['path']} is not a valid issue-template candidate; fix: "
                + ", ".join(item["validation_problems"] or ["nonempty content"])
            )
    return templates, warnings


def _pull_request_templates_in(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []

    single = [
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.casefold() in PULL_REQUEST_SUFFIXES
        and _matches_stem(path, PULL_REQUEST_STEMS)
    ]
    multiple_directory = directory / "PULL_REQUEST_TEMPLATE"
    multiple = (
        [
            path
            for path in multiple_directory.iterdir()
            if path.is_file() and path.suffix.casefold() in PULL_REQUEST_SUFFIXES
        ]
        if multiple_directory.is_dir()
        else []
    )
    return sorted(single + multiple, key=lambda path: path.name.casefold())


def _pull_request_templates(root: Path) -> list[Path]:
    matches: list[Path] = []
    for relative_dir in SHARED_LOCATIONS:
        matches.extend(_pull_request_templates_in(root / relative_dir))
    return matches


def _issue_chooser_config(root: Path) -> tuple[dict[str, Any], list[Path], list[str]]:
    directory = root / ".github" / "ISSUE_TEMPLATE"
    documented = directory / "config.yml"
    alternate = directory / "config.yaml"
    scanned = [path for path in (documented, alternate) if path.is_file()]
    warnings: list[str] = []

    if documented.is_file():
        status = "candidate" if _is_nonempty(documented) else "invalid"
        selected = _relative(documented, root)
    elif alternate.is_file():
        status = "unrecognized_name"
        selected = _relative(alternate, root)
        warnings.append(
            f"{selected} may not configure the issue chooser; GitHub documents the exact filename config.yml."
        )
    else:
        status = "missing_optional"
        selected = None

    return {
        "status": status,
        "selected": selected,
        "required_for_checklist": False,
    }, scanned, warnings


def _placeholder_findings(paths: Iterable[Path], root: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        known = sorted(
            f"{{{{{name}}}}}"
            for name in TEMPLATE_PLACEHOLDERS
            if re.search(r"\{\{\s*" + re.escape(name) + r"\s*\}\}", text)
        )
        generic = sorted(
            {
                match.group(0)
                for pattern in GENERIC_PLACEHOLDER_PATTERNS
                for match in pattern.finditer(text)
                if match.group(0) not in known
            }
        )
        relative = _relative(path, root)
        if known:
            errors.append(f"{relative} contains unresolved template placeholders: {', '.join(known)}")
        if generic:
            warnings.append(f"{relative} contains text worth reviewing: {', '.join(generic)}")
    return warnings, errors


def _file_item(paths: list[Path], root: Path, *, candidate: bool = False) -> dict[str, Any]:
    nonempty = [path for path in paths if _is_nonempty(path)]
    if nonempty:
        status = "candidate" if candidate else "present"
    elif paths:
        status = "invalid"
    else:
        status = "missing"
    return {
        "status": status,
        "selected": _relative(nonempty[0], root) if nonempty else None,
        "candidates": [_relative(path, root) for path in paths],
    }


def _collect_named_items(
    root: Path,
    stems_by_key: dict[str, tuple[str, ...]],
    *,
    label_prefix: str = "",
) -> tuple[dict[str, Any], list[Path], list[str]]:
    items: dict[str, Any] = {}
    scanned_paths: list[Path] = []
    warnings: list[str] = []
    for key, stems in stems_by_key.items():
        paths = _find_community_files(root, stems)
        item = _file_item(paths, root)
        items[key] = item
        scanned_paths.extend(paths)
        if len(paths) > 1:
            label = f"{label_prefix}{key.replace('_', ' ')}"
            warnings.append(
                f"Multiple {label} candidates found; GitHub precedence selects "
                f"{item['selected'] or item['candidates'][0]}."
            )
    return items, scanned_paths, warnings


def _license_paths_in(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return [
        path
        for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold())
        if path.is_file()
        and path.suffix.casefold() in TEXT_SUFFIXES
        and _matches_stem(path, LICENSE_STEMS)
    ]


def _license_details(root: Path) -> tuple[dict[str, Any], list[Path], list[str]]:
    paths = _license_paths_in(root)
    misplaced: list[Path] = []
    for relative_dir in (Path(".github"), Path("docs")):
        misplaced.extend(_license_paths_in(root / relative_dir))
    warnings = [
        f"{_relative(path, root)} is not an auto-detectable repository license; put the selected license at the root."
        for path in misplaced
    ]
    return _file_item(paths, root, candidate=True), paths + misplaced, warnings


def _issue_details(root: Path) -> tuple[dict[str, Any], list[Path], list[str], list[str]]:
    templates, validation_errors = _issue_template_details(root)
    chooser_config, chooser_paths, chooser_warnings = _issue_chooser_config(root)
    candidate_templates = [item for item in templates if item["checklist_candidate"]]
    item = {
        "status": "candidate" if candidate_templates else ("invalid" if templates else "missing"),
        "checklist_candidates": candidate_templates,
        "all_candidates": templates,
        "chooser_config": chooser_config,
    }
    scanned_paths = [root / template["path"] for template in templates] + chooser_paths
    if chooser_config["status"] == "invalid":
        validation_errors.append(".github/ISSUE_TEMPLATE/config.yml is empty.")
    return item, scanned_paths, chooser_warnings, validation_errors


def _invalid_file_errors(items: dict[str, Any], *, label_prefix: str = "") -> list[str]:
    return [
        f"{label_prefix}{key.replace('_', ' ').title()} candidates are empty or structurally incomplete."
        for key, item in items.items()
        if item.get("status") == "invalid"
    ]


def _item_counts(items: dict[str, Any]) -> dict[str, int]:
    counts = {status: 0 for status in ("present", "candidate", "missing", "invalid")}
    for item in items.values():
        status = item.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def _load_profile(path: str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        if path == "-":
            value = json.load(sys.stdin)
        else:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read Community Profile JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("Community Profile JSON must be an object")
    if value.get("message") and "health_percentage" not in value:
        raise ValueError(f"GitHub returned an error: {value['message']}")
    return value


def _remote_summary(profile: dict[str, Any] | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    files = profile.get("files") if isinstance(profile.get("files"), dict) else {}
    return {
        "health_percentage": profile.get("health_percentage"),
        "description_present": bool(profile.get("description")),
        "content_reports_enabled": profile.get("content_reports_enabled"),
        "files": {
            "readme": bool(files.get("readme")),
            "code_of_conduct": bool(files.get("code_of_conduct_file") or files.get("code_of_conduct")),
            "contributing": bool(files.get("contributing")),
            "license": bool(files.get("license")),
            "issue_template": bool(files.get("issue_template")),
            "pull_request_template": bool(files.get("pull_request_template")),
            "security": None,
        },
        "limitations": [
            "The REST files object does not expose the SECURITY row.",
            "The REST issue_template field may not reflect issue forms or inherited defaults.",
            "Use Insights > Community Standards for final visible-row verification.",
        ],
    }


def inventory(root: Path, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"repository path is not a directory: {root}")

    items, scanned_paths, warnings = _collect_named_items(root, COMMUNITY_FILE_STEMS)
    optional_items, optional_paths, optional_warnings = _collect_named_items(
        root, OPTIONAL_COMMUNITY_FILE_STEMS, label_prefix="optional "
    )
    scanned_paths.extend(optional_paths)
    warnings.extend(optional_warnings)

    items["license"], license_paths, license_warnings = _license_details(root)
    scanned_paths.extend(license_paths)
    warnings.extend(license_warnings)
    items["issue_templates"], issue_paths, issue_warnings, validation_errors = _issue_details(root)
    scanned_paths.extend(issue_paths)
    warnings.extend(issue_warnings)
    pr_paths = _pull_request_templates(root)
    items["pull_request_template"] = _file_item(pr_paths, root)
    scanned_paths.extend(pr_paths)

    placeholder_warnings, placeholder_errors = _placeholder_findings(scanned_paths, root)
    warnings.extend(placeholder_warnings)
    validation_errors.extend(placeholder_errors)
    validation_errors.extend(_invalid_file_errors(items))
    validation_errors.extend(_invalid_file_errors(optional_items, label_prefix="Optional "))

    return {
        "schema_version": SCHEMA_VERSION,
        "repository": str(root),
        "local": {
            "items": items,
            "optional_items": optional_items,
            "counts": _item_counts(items),
            "warnings": warnings,
            "validation_errors": validation_errors,
            "note": (
                "Issue-form YAML is inventoried, not parsed or validated. "
                "Local findings are candidates until GitHub recognizes them on the default branch."
            ),
        },
        "remote": _remote_summary(profile),
        "score_projection": None,
    }


def _human_item_lines(result: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key, item in result["local"]["items"].items():
        status = item["status"]
        selected = item.get("selected")
        if key == "issue_templates":
            selected = ", ".join(entry["path"] for entry in item["checklist_candidates"])
        detail = f" — {selected}" if selected else ""
        lines.append(f"{key.replace('_', ' ').title()}: {status}{detail}")
    for key, item in result["local"]["optional_items"].items():
        selected = item.get("selected")
        detail = f" — {selected}" if selected else ""
        lines.append(f"Optional {key.replace('_', ' ').title()}: {item['status']}{detail}")
    return lines


def _human_remote_lines(remote: dict[str, Any] | None) -> list[str]:
    if not remote:
        return []
    return [
        "",
        f"GitHub-reported health: {remote['health_percentage']}",
        f"Repository description present: {remote['description_present']}",
        f"Reported content enabled: {remote['content_reports_enabled']}",
    ]


def _human_finding_lines(title: str, findings: list[str]) -> list[str]:
    return ["", f"{title}:", *(f"- {finding}" for finding in findings)] if findings else []


def _human_report(result: dict[str, Any]) -> str:
    lines = ["Community Standards inventory", "", *_human_item_lines(result)]
    lines.extend(_human_remote_lines(result.get("remote")))
    lines.extend(_human_finding_lines("Warnings", result["local"]["warnings"]))
    lines.extend(_human_finding_lines("Validation errors", result["local"]["validation_errors"]))
    lines.extend(["", result["local"]["note"]])
    return "\n".join(lines)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inventory likely GitHub Community Standards files without changing the repository."
    )
    parser.add_argument("--repo", default=".", help="Repository directory (default: current directory).")
    parser.add_argument(
        "--profile-json",
        help="Optional GitHub Community Profile JSON file, or '-' to read it from standard input.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--fail-on-invalid",
        action="store_true",
        help="Exit 1 for invalid candidates or unresolved placeholders; missing files remain an audit result.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = inventory(Path(args.repo), _load_profile(args.profile_json))
    except ValueError as error:
        print(f"community-check: {error}", file=sys.stderr)
        return 2

    if args.json:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(_human_report(result))

    return 1 if args.fail_on_invalid and result["local"]["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
