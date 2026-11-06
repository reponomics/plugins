#!/usr/bin/env python3
"""Operate an OpenSSF Best Practices assessment without exposing storage paths."""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    sys.exit(
        "Badge Buddy requires Python 3.11 or newer; "
        f"this command is running Python {sys.version_info[0]}.{sys.version_info[1]}. "
        "Run it with Python 3.11+ or put that interpreter first on PATH as python3."
    )

import argparse
from collections.abc import Callable, Mapping, Sequence
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
import webbrowser


from ossf_review.board import board_refresh_lock, review_path, write_board
from ossf_review.criteria import CriteriaCatalog, Criterion, SECTION_NAMES
from ossf_review.fields import normalize_assessment_fields
from ossf_review.storage import DataStore
from ossf_review.submission import (
    ALLOWED_BASE_URLS,
    DEFAULT_MAX_URL_BYTES,
    PRODUCTION_BASE_URL,
    STAGING_BASE_URL,
    build_fill_script,
    build_proposal_urls,
    validate_base_url,
    wording_only_criteria,
)
from ossf_review.sync import (
    BestPracticesClient,
    PROJECT_METADATA_FIELDS,
    ProjectResolutionError,
    SyncConflict,
    SyncResult,
    UnregisteredProjectError,
    discover_repository,
    handoff_local_assessment,
    synchronize_project,
    write_assessment_file,
)


REGISTRATION_URL = "https://www.bestpractices.dev/projects/new"
VALID_STATUSES = {"Met", "Unmet", "N/A", "?"}

# Advisory only: a justification is public form text in the project's own
# voice. These phrases indicate assessment narration leaking into the form
# (see skills/ossf-bp-badges/references/justification-style.md). Patterns are
# deliberately narrow — criteria themselves legitimately use words such as
# "review" and "unreviewable".
_STYLE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(expression, re.IGNORECASE), reason)
    for expression, reason in (
        (
            r"\bmaintainer\s+(?:says|said|states|stated|confirms|confirmed|reports|reported|asserts|asserted)\b",
            "the project authors the form; state the fact without sourcing narration",
        ),
        (
            r"\b(?:per|according\s+to)\s+the\s+maintainer\b",
            "the project authors the form; state the fact without sourcing narration",
        ),
        (
            r"\bthe\s+user\s+(?:says|said|states|stated|confirms|confirmed)\b",
            "the project authors the form; state the fact without sourcing narration",
        ),
        (r"\bthis\s+(?:session|conversation)\b", "process history does not belong on the form"),
        (r"\bclaude\b", "the assistant is not part of the public record"),
        (r"\bcorrected\s+after\b", "process history does not belong on the form"),
        (
            r"\b(?:first|second|third|prior|previous)\s+review\b",
            "review-round history does not belong on the form",
        ),
        (r"\breview\s+round\b", "review-round history does not belong on the form"),
        (
            r"\bno\s+direct\s+evidence\b",
            "if evidence is insufficient, leave the status '?' instead of hedging",
        ),
        (
            r"\bcould\s+not\s+(?:be\s+)?verif\w+\b",
            "if evidence is insufficient, leave the status '?' instead of hedging",
        ),
        (r"\bevidence\s+plane\b", "plane classification lives in the conversation, not the form"),
        (
            r"\bcorrects?\s+(?:a|the|our)\s+(?:previous|earlier|prior)\b",
            "the form states current truth; correction history does not belong on it",
        ),
        (
            r"\b(?:previously|earlier)\s+(?:stated|recorded|marked|listed|answered)\b",
            "the form states current truth; correction history does not belong on it",
        ),
        (
            r"\bupdated\s+to\s+reflect\b",
            "the form states current truth; correction history does not belong on it",
        ),
        (
            r"\bhas\s+been\s+(?:revised|corrected)\b",
            "the form states current truth; correction history does not belong on it",
        ),
    )
)
_STYLE_LENGTH_LIMIT = 700


def _style_warnings(updates: Mapping[str, Any]) -> list[dict[str, str]]:
    """Flag justification text that reads as assessment narration."""

    warnings: list[dict[str, str]] = []
    for field, value in updates.items():
        if not field.endswith("_justification") or not isinstance(value, str):
            continue
        for pattern, reason in _STYLE_PATTERNS:
            match = pattern.search(value)
            if match:
                warnings.append(
                    {"field": field, "matched": match.group(0), "reason": reason}
                )
        if len(value) > _STYLE_LENGTH_LIMIT:
            warnings.append(
                {
                    "field": field,
                    "matched": f"{len(value)} characters",
                    "reason": (
                        "very long for form text; state the conclusion and the "
                        "decisive evidence, keep the analysis in the conversation"
                    ),
                }
            )
    return warnings


class CommandError(RuntimeError):
    """A deterministic, user-facing command failure."""


def _assert_badge_site_url(url: str) -> None:
    """Refuse to hand the browser anything but an https badge-site URL.

    The base URL is validated when the plan is built; this re-check guards the
    exact string that reaches ``webbrowser.open`` so no later transformation
    can widen it.
    """

    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if parsed.scheme != "https" or origin not in ALLOWED_BASE_URLS:
        raise CommandError(f"refusing to open a URL outside the badge site: {url}")


def _path_from_argument_or_environment(
    explicit: Path | None,
    environment_name: str,
    *,
    fallback: Path | None = None,
) -> Path:
    if explicit is not None:
        selected = explicit
    else:
        configured = os.environ.get(environment_name)
        if configured:
            selected = Path(configured)
        elif fallback is not None:
            selected = fallback
        else:
            raise CommandError(
                f"{environment_name} is unavailable; pass the corresponding command option"
            )
    if environment_name == "CLAUDE_PLUGIN_DATA" and selected.expanduser().resolve(
        strict=False
    ) == Path.cwd().resolve(strict=False):
        raise CommandError(
            "private plugin data must not resolve to the current working directory"
        )
    return selected


def _add_resolution_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-id", help="numeric badge id to verify with online status, or reuse locally"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="use the selected working assessment without reading the public API",
    )
    parser.add_argument(
        "--allow-unregistered",
        action="store_true",
        help="use a local-only record after the maintainer explicitly defers registration",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        help="project repository (default: CLAUDE_PROJECT_DIR or current directory)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="private plugin state root (default: CLAUDE_PLUGIN_DATA)",
    )
    parser.add_argument(
        "--assessment-file",
        type=Path,
        help="existing working assessment file (required when the repository has an assessment)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser(
        "status",
        help="refresh the public snapshot and report project status (use at session start)",
    )
    _add_resolution_arguments(status)

    apply_updates = commands.add_parser(
        "apply",
        help="apply confirmed fields to the working assessment",
    )
    _add_resolution_arguments(apply_updates)
    apply_updates.add_argument(
        "--section",
        choices=SECTION_NAMES,
        required=True,
        help="criteria section whose requirements validate this update",
    )
    apply_updates.add_argument(
        "--review-response",
        choices=sorted(VALID_STATUSES),
        help="validate justification-only preview edits for this response without setting it",
    )
    input_group = apply_updates.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input",
        metavar="PATH",
        help="JSON object to apply, or - to read it from standard input",
    )
    input_group.add_argument(
        "--json",
        dest="json_object",
        help="JSON object to apply directly",
    )

    review = commands.add_parser(
        "review",
        help="open a passive local review record",
    )
    _add_resolution_arguments(review)
    review.add_argument("--section", choices=SECTION_NAMES, default="passing")
    review.add_argument("--view", choices=("overview", "all"), default="overview")
    review.add_argument("--no-browser", action="store_true")

    export = commands.add_parser(
        "export",
        help="write the working assessment to an explicit path",
    )
    _add_resolution_arguments(export)
    export.add_argument("--output", type=Path, required=True)

    propose = commands.add_parser(
        "propose",
        help=(
            "emit official automation-proposal URL(s) that the "
            "user reviews and saves on bestpractices.dev"
        ),
    )
    _add_resolution_arguments(propose)
    propose.add_argument("--section", choices=SECTION_NAMES, required=True)
    propose.add_argument(
        "--overrides",
        help=(
            "forwarded verbatim to the badge site's overrides parameter "
            "(comma-separated fnmatch globs the SITE may apply over existing "
            "answers); it does not filter which fields are proposed locally"
        ),
    )
    propose.add_argument(
        "--reanalyze",
        action="store_true",
        help="also re-run the badge site's own detectives on page load",
    )
    propose.add_argument(
        "--base-url",
        default=PRODUCTION_BASE_URL,
        help=(
            "badge site base URL; only the production and staging badge "
            "sites are accepted"
        ),
    )
    propose.add_argument(
        "--staging",
        action="store_true",
        help=f"shortcut for --base-url {STAGING_BASE_URL}",
    )
    propose.add_argument(
        "--max-url-bytes",
        type=int,
        default=DEFAULT_MAX_URL_BYTES,
        help="practical chunking threshold; upstream documents no limit",
    )
    propose.add_argument(
        "--open",
        dest="open_first",
        action="store_true",
        help="open the first proposal URL in the browser",
    )

    fill_script = commands.add_parser(
        "fill-script",
        help=(
            "write a console script that fills the edit form "
            "for one section without saving it"
        ),
    )
    _add_resolution_arguments(fill_script)
    fill_script.add_argument("--section", choices=SECTION_NAMES, required=True)
    fill_script.add_argument("--output", type=Path, required=True)
    scope = fill_script.add_mutually_exclusive_group()
    scope.add_argument(
        "--changed-only",
        action="store_true",
        help=(
            "emit only fields whose wording differs from the saved public snapshot "
            "while the status matches (default; run status first)"
        ),
    )
    scope.add_argument(
        "--criteria",
        metavar="IDS",
        help=(
            "comma-separated criterion ids (or display ids) to include, "
            "validated against --section"
        ),
    )
    scope.add_argument(
        "--all",
        dest="all_fields",
        action="store_true",
        help="emit every answered criterion in the section",
    )
    return parser


def _runtime_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    repository = _path_from_argument_or_environment(
        args.repo,
        "CLAUDE_PROJECT_DIR",
        fallback=Path.cwd(),
    )
    data_dir = _path_from_argument_or_environment(
        args.data_dir,
        "CLAUDE_PLUGIN_DATA",
    )
    return repository, data_dir


def _synchronize(
    args: argparse.Namespace,
    *,
    store_factory: Callable[[Path], Any],
    client_factory: Callable[[], Any],
) -> tuple[Any, SyncResult, Path]:
    repository, data_dir = _runtime_paths(args)
    store = store_factory(data_dir)
    if args.assessment_file is not None:
        store.use_assessment_file(args.assessment_file)
    client = client_factory() if args.command == "status" and not args.offline else None
    result = synchronize_project(
        store,
        repository,
        project_id=args.project_id,
        client=client,
        allow_unregistered=args.allow_unregistered,
    )
    return store, result, data_dir


def _status_counts(
    catalog: CriteriaCatalog,
    assessment: Mapping[str, Any],
) -> dict[str, dict[str, int]]:
    classified = catalog.classify_flat(assessment)
    result: dict[str, dict[str, int]] = {}
    for section in SECTION_NAMES:
        counts = {
            "total": 0,
            "met": 0,
            "unmet": 0,
            "not_applicable": 0,
            "unknown": 0,
            "evidence_gaps": 0,
        }
        answers = classified[section]
        for criterion in catalog.section(section):
            counts["total"] += 1
            answer = answers.get(criterion.id, {})
            status = answer.get("status", "?")
            if status == "Met":
                counts["met"] += 1
                justification = answer.get("justification")
                if criterion.met_justification_required and not _has_required_justification(
                    justification
                ):
                    counts["evidence_gaps"] += 1
                elif criterion.met_url_required and not _has_evidence_url(
                    justification
                ):
                    counts["evidence_gaps"] += 1
            elif status == "Unmet":
                counts["unmet"] += 1
            elif status == "N/A":
                counts["not_applicable"] += 1
                if criterion.na_justification_required and not _has_required_justification(
                    answer.get("justification")
                ):
                    counts["evidence_gaps"] += 1
            else:
                counts["unknown"] += 1
        decided = counts["total"] - counts["unknown"]
        counts["decided"] = decided
        counts["decided_percent"] = int(round(100 * decided / counts["total"], 1))
        result[section] = counts
    return result


def _has_required_justification(value: Any) -> bool:
    # Match justification_good? in the catalog's pinned BadgeApp project.rb:
    # count characters without stripping; only the exact '// ' prefix is a comment.
    return isinstance(value, str) and not value.startswith("// ") and len(value) >= 5


def _has_evidence_url(value: Any) -> bool:
    # Match contains_url?'s deliberately permissive rule, not URL reachability.
    return (
        isinstance(value, str)
        and not value.startswith("// ")
        and re.search(r"https?://[^/. ]+\.[^ ]", value) is not None
    )


def _conflict_record(conflict: SyncConflict) -> dict[str, Any]:
    source = {
        "public API": "public_api", "local_draft": "local_draft",
    }.get(conflict.source, "repository")
    return {
        "field": conflict.field,
        "preserved": conflict.preserved,
        "incoming": conflict.incoming,
        "source": source,
    }


def _public_snapshot_metadata(result: SyncResult) -> dict[str, Any]:
    return {
        "source": "live" if result.public_loaded else (
            "cached" if result.public_fetched_at else "none"
        ),
        "fetched_at": result.public_fetched_at,
    }


def _status_payload(
    result: SyncResult,
    catalog: CriteriaCatalog,
) -> dict[str, Any]:
    resolution = result.resolution
    return {
        "schema_version": 1,
        "state": "registered" if resolution.registered else "unregistered",
        "project": {
            "identifier": resolution.identifier,
            "project_id": resolution.project_id,
            "registered": resolution.registered,
            "remote": resolution.repository.remote,
            "repository_url": resolution.repository.url,
            "name": resolution.repository.project_name,
        },
        "sources": {
            "public_loaded": result.public_loaded,
            "public_snapshot": _public_snapshot_metadata(result),
            "repository_backed": result.repository_file is not None,
        },
        "conflicts": [_conflict_record(item) for item in result.conflicts],
        "sections": _status_counts(catalog, result.assessment),
        "wording_only_updates": _wording_only_by_section(result, catalog),
        "assessment": result.assessment,
    }


def _wording_only_by_section(
    result: SyncResult,
    catalog: CriteriaCatalog,
) -> dict[str, list[str]]:
    """Sections where the public snapshot matches statuses but wording differs.

    Show edits that can use a fill script, or a proposal URL with overrides
    when replacing existing wording.
    """

    if not result.public_document:
        return {}
    updates: dict[str, list[str]] = {}
    for section in SECTION_NAMES:
        identifiers = wording_only_criteria(
            result.assessment,
            catalog,
            section=section,
            public_document=result.public_document,
        )
        if identifiers:
            updates[section] = list(identifiers)
    return updates


def _registration_payload(repository: Path, *, offline: bool) -> dict[str, Any]:
    identity = discover_repository(repository)
    return {
        "schema_version": 1,
        "state": "registry_miss" if offline else "registration_required",
        "project": {
            "identifier": None,
            "project_id": None,
            "registered": False,
            "remote": identity.remote,
            "repository_url": identity.url,
            "name": identity.project_name,
        },
        "registration_url": REGISTRATION_URL,
        "unregistered_available": True,
        "next_step": (
            "Run status online to look up and verify the project; "
            "supply --project-id on that command if known."
            if offline else "Register the project, or use --allow-unregistered."
        ),
    }


def _load_updates(args: argparse.Namespace) -> dict[str, Any]:
    if args.json_object is not None:
        source = args.json_object
        label = "--json"
    elif args.input == "-":
        source = sys.stdin.read()
        label = "standard input"
    else:
        path = Path(args.input)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise CommandError(
                f"could not read update input {path}: {error}"
            ) from error
        label = str(path)
    try:
        value = json.loads(source)
    except json.JSONDecodeError as error:
        raise CommandError(f"invalid JSON from {label}: {error}") from error
    if not isinstance(value, dict):
        raise CommandError("assessment updates must be one flat JSON object")
    return value


def _canonical_update_key(
    catalog: CriteriaCatalog,
    field: str,
    section: str,
) -> tuple[str, Criterion]:
    classified = catalog.classify_flat({field: None})
    suffix = "status" if field.endswith("_status") else "justification"
    criterion_ids = set(classified[section])
    if not criterion_ids:
        if not any(classified.values()):
            raise CommandError(f"unknown assessment field: {field}")
        raise CommandError(f"assessment field {field!r} is not in section {section!r}")
    if len(criterion_ids) != 1:
        raise CommandError(f"ambiguous assessment field in section {section!r}: {field}")
    criterion_id = next(iter(criterion_ids))
    return f"{criterion_id}_{suffix}", catalog.get(criterion_id, section)


def _validated_updates(
    catalog: CriteriaCatalog,
    current: Mapping[str, Any],
    proposed: Mapping[str, Any],
    *,
    section: str,
    review_response: str | None = None,
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    affected: dict[str, Criterion] = {}
    for raw_field, value in proposed.items():
        if not isinstance(raw_field, str):
            raise CommandError("assessment field names must be strings")
        if review_response is not None and not raw_field.endswith("_justification"):
            raise CommandError("--review-response accepts only justification fields")
        if raw_field in PROJECT_METADATA_FIELDS:
            if not isinstance(value, str):
                raise CommandError(f"{raw_field} must be a string")
            normalized[raw_field] = value
            continue
        if not (raw_field.endswith("_status") or raw_field.endswith("_justification")):
            raise CommandError(f"unknown assessment field: {raw_field}")
        field, criterion = _canonical_update_key(catalog, raw_field, section)
        if field.endswith("_justification") and not isinstance(value, str):
            raise CommandError(f"{field} must be a string")
        if field in normalized and normalized[field] != value:
            raise CommandError(f"conflicting aliases were supplied for {field}")
        normalized[field] = value
        affected.setdefault(criterion.id, criterion)

    effective = normalize_assessment_fields(current)
    effective.update(normalized)
    for criterion_id, criterion in affected.items():
        status_field = f"{criterion_id}_status"
        status = review_response if review_response is not None else effective.get(status_field)
        justification = effective.get(f"{criterion_id}_justification")
        valid_status = isinstance(status, str) and status in VALID_STATUSES
        if status_field in normalized and not valid_status:
            choices = ", ".join(sorted(VALID_STATUSES))
            raise CommandError(f"{status_field} must be one of: {choices}")
        if not valid_status:
            continue
        if status == "N/A" and not criterion.na_allowed:
            raise CommandError(f"{status_field} does not allow N/A")
        if (
            status == "N/A"
            and criterion.na_justification_required
            and not _has_required_justification(justification)
        ):
            raise CommandError(f"{status_field} requires an N/A justification")
        if (
            status == "Met"
            and criterion.met_justification_required
            and not _has_required_justification(justification)
        ):
            raise CommandError(
                f"{status_field} requires evidence or a justification"
            )
        if (
            status == "Met"
            and criterion.met_url_required
            and not _has_evidence_url(justification)
        ):
            raise CommandError(f"{status_field} requires a public evidence URL")
    return normalized


def _print_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True))


def _refresh_open_boards(
    store: Any,
    result: SyncResult,
    catalog: CriteriaCatalog,
    data_dir: Path,
) -> None:
    """Best-effort refresh existing boards from the latest canonical state."""

    identifier = result.resolution.identifier
    try:
        with board_refresh_lock(data_dir, identifier):
            assessment = store.load_assessment(identifier)
            for section in SECTION_NAMES:
                output = review_path(data_dir, identifier, section)
                if output.exists():
                    write_board(
                        assessment,
                        output,
                        project_id=identifier,
                        section=section,
                        catalog=catalog,
                    )
    except Exception as error:  # The passive projection is never canonical.
        print(f"warning: passive review board refresh failed: {error}", file=sys.stderr)


def _open_review(
    result: SyncResult,
    catalog: CriteriaCatalog,
    data_dir: Path,
    section: str,
    browser_open: Callable[[str], Any],
    *,
    view: str,
    no_browser: bool,
) -> str:
    output = review_path(data_dir, result.resolution.identifier, section)
    write_board(
        result.assessment,
        output,
        project_id=result.resolution.identifier,
        section=section,
        catalog=catalog,
    )
    url = output.as_uri()
    if view == "all":
        url += "#view=all"
    if not no_browser:
        browser_open(url)
    return url


def main(
    argv: Sequence[str] | None = None,
    *,
    store_factory: Callable[[Path], Any] = DataStore,
    client_factory: Callable[[], Any] = BestPracticesClient,
    catalog_factory: Callable[[], CriteriaCatalog] = CriteriaCatalog,
    browser_open: Callable[[str], Any] = webbrowser.open,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output = None
    try:
        repository, data_dir = _runtime_paths(args)
        catalog = catalog_factory()
        try:
            store, result, _data_dir = _synchronize(
                args,
                store_factory=store_factory,
                client_factory=client_factory,
            )
        except UnregisteredProjectError:
            payload = _registration_payload(
                repository, offline=args.offline or args.command != "status",
            )
            _print_json(payload)
            return 0 if args.command == "status" else 3

        if args.command == "status":
            _refresh_open_boards(store, result, catalog, data_dir)
            _print_json(_status_payload(result, catalog))
            return 0

        if args.command == "apply":
            proposed = _load_updates(args)
            updates = _validated_updates(
                catalog,
                result.assessment,
                proposed,
                section=args.section,
                review_response=args.review_response,
            )
            assessment = store.update_assessment(
                result.resolution.identifier,
                updates,
            )
            updated_fields = set(updates)
            conflicts = result.conflicts
            if result.resolution.registered:
                assessment, local_conflicts = handoff_local_assessment(
                    store, result.resolution, resolved_fields=updated_fields,
                )
                conflicts = tuple(
                    item for item in conflicts if item.source != "local_draft"
                ) + local_conflicts
            result = SyncResult(
                resolution=result.resolution,
                assessment=assessment,
                conflicts=tuple(
                    item
                    for item in conflicts
                    if item.source == "local_draft" or item.field not in updated_fields
                ),
                repository_file=result.repository_file,
                public_loaded=result.public_loaded,
                public_document=result.public_document,
                public_fetched_at=result.public_fetched_at,
            )
            _refresh_open_boards(store, result, catalog, data_dir)
            payload = _status_payload(result, catalog)
            payload["style_warnings"] = _style_warnings(updates)
            _print_json(payload)
            return 0

        conflict_records = [_conflict_record(item) for item in result.conflicts]

        if args.command == "review":
            url = _open_review(
                result,
                catalog,
                data_dir,
                args.section,
                browser_open,
                view=args.view,
                no_browser=args.no_browser,
            )
            _print_json(
                {
                    "schema_version": 1,
                    "state": "review_written",
                    "conflicts": conflict_records,
                    "project_id": result.resolution.project_id,
                    "section": args.section,
                    "url": url,
                }
            )
            return 0

        if args.command in {"export", "fill-script"}:
            output = args.output.expanduser().resolve(strict=False)
            private_root = data_dir.expanduser().resolve(strict=False)
            if output == private_root or private_root in output.parents:
                raise CommandError(
                    f"{args.command} output must be outside CLAUDE_PLUGIN_DATA"
                )

        if args.command == "export":
            assert output is not None
            _refresh_open_boards(store, result, catalog, data_dir)
            write_assessment_file(output, result.assessment)
            _print_json(
                {
                    "schema_version": 1,
                    "state": "assessment_exported",
                    "conflicts": conflict_records,
                    "output": str(output),
                    "project_id": result.resolution.project_id,
                }
            )
            return 0
        if args.command == "propose":
            if result.resolution.project_id is None:
                raise CommandError(
                    "propose requires a registered bestpractices.dev project; "
                    "register the project or pass --project-id"
                )
            try:
                base_url = validate_base_url(
                    STAGING_BASE_URL if args.staging else args.base_url
                )
            except ValueError as error:
                raise CommandError(str(error)) from error
            plan = build_proposal_urls(
                result.assessment,
                catalog,
                section=args.section,
                project_id=result.resolution.project_id,
                base_url=base_url,
                overrides=args.overrides,
                reanalyze=args.reanalyze,
                max_url_bytes=args.max_url_bytes,
                public_document=result.public_document,
            )
            notes = [
                "Proposals are one-shot: nothing is stored until the "
                "form is saved. Review the highlighted fields, then save or "
                "explicitly ask the assistant to click Save."
            ]
            if args.overrides:
                notes.append(
                    "The site decides which overrides match. To replace existing wording, "
                    "match its justification field or paired status field; an emitted "
                    "URL does not confirm that the site will apply every field."
                )
            if len(plan.urls) > 1:
                notes.append(
                    "Multiple URLs: open URL 1, review, click 'Save (and "
                    "continue)', then open the next URL; unsaved proposals "
                    "are lost."
                )
            if plan.dropped_justification_only:
                notes.append(
                    "Existing wording is preserved by default when the status matches. "
                    "Use fill-script for these edits, or --overrides with the site's "
                    "field-matching rules and review the result."
                )
            if plan.oversize:
                notes.append(
                    "Some justifications exceed --max-url-bytes even in a "
                    "URL of their own and were not emitted; shorten the "
                    "wording, or send them via fill-script --criteria."
                )
            if args.open_first and plan.urls:
                _assert_badge_site_url(plan.urls[0])
                browser_open(plan.urls[0])
            _print_json(
                {
                    "schema_version": 1,
                    "state": "proposals_ready",
                    "public_snapshot": _public_snapshot_metadata(result),
                    "conflicts": conflict_records,
                    "section": args.section,
                    "project_id": result.resolution.project_id,
                    "urls": list(plan.urls),
                    "proposed": list(plan.proposed),
                    "skipped_unknown": list(plan.skipped_unknown),
                    "dropped_no_op": list(plan.dropped_no_op),
                    "dropped_justification_only": list(
                        plan.dropped_justification_only
                    ),
                    "oversize": list(plan.oversize),
                    "notes": notes,
                }
            )
            return 0
        if args.command == "fill-script":
            assert output is not None
            selected: list[str] | None
            if args.criteria:
                requested = [
                    item.strip() for item in args.criteria.split(",") if item.strip()
                ]
                if not requested:
                    raise CommandError("--criteria was supplied without ids")
                selected = []
                for raw_id in requested:
                    try:
                        criterion = catalog.get(raw_id, args.section)
                    except KeyError as error:
                        raise CommandError(
                            f"--criteria: {error.args[0]}"
                        ) from error
                    selected.append(criterion.id)
                scope_mode = "criteria"
            elif args.all_fields:
                selected = None
                scope_mode = "all"
            else:
                # Changed-only needs a saved comparison; never silently widen it.
                if not result.public_document:
                    raise CommandError(
                        "no public snapshot is available, so --changed-only cannot compute the "
                        "wording-only set; run status online, or pass --criteria <ids> or --all to "
                        "choose fields explicitly"
                    )
                selected = list(
                    wording_only_criteria(
                        result.assessment,
                        catalog,
                        section=args.section,
                        public_document=result.public_document,
                    )
                )
                scope_mode = "changed-only"
                if not selected:
                    _print_json(
                        {
                            "schema_version": 1,
                            "state": "fill_script_not_needed",
                            "public_snapshot": _public_snapshot_metadata(result),
                            "conflicts": conflict_records,
                            "section": args.section,
                            "scope": scope_mode,
                            "criteria": [],
                            "notes": [
                                "No wording-only changes relative to the saved public "
                                "snapshot; status changes may still need a proposal."
                            ],
                        }
                    )
                    return 0
            script, filled = build_fill_script(
                result.assessment,
                catalog,
                section=args.section,
                criteria=selected,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(script, encoding="utf-8")
            _print_json(
                {
                    "schema_version": 1,
                    "state": "fill_script_written",
                    "public_snapshot": _public_snapshot_metadata(result),
                    "conflicts": conflict_records,
                    "section": args.section,
                    "scope": scope_mode,
                    "output": str(output),
                    "criteria": list(filled),
                    "notes": [
                        "Paste the script into the browser console on the "
                        "project's EDIT page for this section; it fills the "
                        "form fields and never saves. The user can save, or "
                        "explicitly ask the assistant to click Save."
                    ],
                }
            )
            return 0
        raise AssertionError(f"unhandled command: {args.command}")
    except (CommandError, ProjectResolutionError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
