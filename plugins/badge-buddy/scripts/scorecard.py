#!/usr/bin/env python3
"""Retrieve, inspect, and compare Scorecard results.

The controller reads published API results or supplied JSON. It preserves
scores and findings without running the scanner or calculating scores.
Agent-facing workflow guidance lives in skills/ossf-scorecard/SKILL.md.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    sys.exit(
        "Badge Buddy requires Python 3.11 or newer; "
        f"this command is running Python {sys.version_info[0]}.{sys.version_info[1]}. "
        "Run it with Python 3.11+ or put that interpreter first on PATH as python3."
    )

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from ossf_review.storage import normalize_github_remote


PUBLIC_API_BASE = "https://api.scorecard.dev/projects"
VIEWER_BASE = "https://scorecard.dev/viewer/?uri="
USER_AGENT = "badge-buddy-scorecard/1 (+https://github.com/reponomics/plugins)"
API_TIMEOUT_SECONDS = 30
GITLAB_GUIDANCE = "https://github.com/ossf/scorecard#using-a-gitlab-repository"


class CommandError(Exception):
    """A user-correctable input or acquisition problem."""


def object_field(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CommandError(f"{label} must be a JSON object")
    return value


def text_field(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise CommandError(f"{label} must be a string")
    return value


def optional_text(value: Any, label: str) -> str:
    return "" if value is None else text_field(value, label)


def optional_object(value: Any, label: str) -> Mapping[str, Any]:
    return {} if value is None else object_field(value, label)


def string_list(value: Any, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise CommandError(f"{label} must be an array of strings or null")
    return tuple(value)


def reported_score(value: Any) -> float | None:
    if value is None:
        return None
    if type(value) not in (int, float):
        raise CommandError("reported score must be a finite number or null")
    if value == -1:
        return None
    if not 0 <= value <= 10:
        raise CommandError("reported score must be between 0 and 10, or -1 for inconclusive")
    return float(value)


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CommandError("result date must be an ISO 8601 date or timestamp") from error
    return date.replace(tzinfo=date.tzinfo or timezone.utc)


@dataclass(frozen=True)
class CheckResult:
    name: str
    score: int
    reason: str
    details: tuple[str, ...]
    documentation: Mapping[str, str]
    annotations: tuple[str, ...]

    @classmethod
    def parse(cls, value: Any) -> CheckResult:
        entry = object_field(value, "check entry")
        name = text_field(entry.get("name"), "check name")
        if not name.strip():
            raise CommandError("check name must not be empty")
        score = entry.get("score")
        if type(score) is not int or not -1 <= score <= 10:
            raise CommandError(f"{name}: score must be an integer from -1 to 10")
        documentation = optional_object(entry.get("documentation"), f"{name} documentation")
        return cls(
            name=name,
            score=score,
            reason=optional_text(entry.get("reason"), f"{name} reason"),
            details=string_list(entry.get("details"), f"{name} details"),
            documentation={
                key: text_field(documentation[key], f"{name} documentation {key}")
                for key in ("url", "short")
                if documentation.get(key) is not None
            },
            annotations=string_list(entry.get("annotations"), f"{name} annotations"),
        )

    @property
    def state(self) -> str:
        return "inconclusive" if self.score < 0 else "scored"

    @property
    def value(self) -> int | None:
        return self.score if self.score >= 0 else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.value,
            "conclusive": self.score >= 0,
            "reason": self.reason,
            "details": list(self.details),
            "documentation": dict(self.documentation),
            "annotations": list(self.annotations),
        }


@dataclass(frozen=True)
class Result:
    repo: str
    commit: str
    date: str
    scorecard_version: str
    scorecard_commit: str
    checks: tuple[CheckResult, ...]
    reported_score: float | None
    document: Mapping[str, Any]
    provenance: Mapping[str, Any]

    @classmethod
    def parse(cls, value: Any, *, provenance: Mapping[str, Any]) -> Result:
        document = object_field(value, "Scorecard result")
        repo = object_field(document.get("repo"), "result repo")
        name = text_field(repo.get("name"), "result repo.name")
        if not name.strip():
            raise CommandError("result repo.name must not be empty")
        engine = optional_object(document.get("scorecard"), "result scorecard")
        entries = document.get("checks")
        if not isinstance(entries, list) or not entries:
            raise CommandError("Scorecard result must contain a non-empty checks array; import Scorecard JSON, not SARIF")
        checks = tuple(sorted(
            (CheckResult.parse(entry) for entry in entries),
            key=lambda check: check.name,
        ))
        if len({check.name for check in checks}) != len(checks):
            raise CommandError("Scorecard result contains duplicate check names")
        date = optional_text(document.get("date"), "result date")
        parse_date(date)
        return cls(
            repo=name,
            commit=optional_text(repo.get("commit"), "result repo.commit"),
            date=date,
            scorecard_version=optional_text(engine.get("version"), "result scorecard.version"),
            scorecard_commit=optional_text(engine.get("commit"), "result scorecard.commit"),
            checks=checks,
            reported_score=reported_score(document.get("score")),
            document=document,
            provenance=dict(provenance),
        )

    @property
    def source(self) -> str:
        return "api" if self.provenance.get("source") == "api" else "import"

    def summary(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "commit": self.commit,
            "date": self.date,
            "scorecard_version": self.scorecard_version,
            "scorecard_commit": self.scorecard_commit,
            "reported_score": self.reported_score,
            "check_names": [check.name for check in self.checks],
            "checks_excluded": [check.name for check in self.checks if check.score < 0],
            "provenance": dict(self.provenance),
            "coverage_notes": coverage_notes(self),
        }


def coverage_notes(result: Result) -> list[str]:
    if result.source == "api":
        notes = api_coverage_notes(result.repo)
    else:
        notes = [
            "Imported result: publication has not been verified. Scanner credentials and "
            "acquisition conditions are unknown; use the API to verify a published badge."
        ]
    if result.repo.startswith("file://") or result.provenance.get("mode") == "local":
        notes.append("Local checkout analysis has limited coverage and is not comparable to a published repository scan.")
    if result.provenance.get("checks_requested"):
        notes.append("Only a subset of checks was requested for this imported result.")
    if not result.date or not result.commit:
        notes.append("The scan date or repository commit is missing; freshness cannot be verified from this result alone.")
    if result.reported_score is None:
        notes.append("Upstream supplied no conclusive aggregate score; none is calculated here.")
    if any(check.score < 0 for check in result.checks):
        notes.append("Inconclusive checks are unscored, not zero. A change in scored coverage can change the reported aggregate.")
    return notes


def api_coverage_notes(repo: str) -> list[str]:
    notes = [
        "Published API snapshot: fetching it does not run Scorecard. Verify that a newer "
        "API date and commit reflect the intended remote changes before claiming the badge updated."
    ]
    if normalize_repo(repo).startswith("gitlab.com/"):
        notes.append(
            "For GitLab, V1 reads existing API results; implementation and publication setup "
            f"guidance is limited to GitHub. For GitLab diagnostics, consult {GITLAB_GUIDANCE}."
        )
    else:
        notes.append("For GitHub, verify the Action publishing run and its resulting API record.")
    return notes


def saved_provenance(value: Any) -> dict[str, Any]:
    metadata = object_field(value, "_ossf_scorecard metadata")
    if type(metadata.get("schema_version")) is not int or metadata["schema_version"] != 1:
        raise CommandError("invalid _ossf_scorecard metadata: expected schema_version 1")
    provenance = object_field(metadata.get("provenance"), "_ossf_scorecard provenance")
    if provenance.get("source") not in ("api", "file", "cli"):
        raise CommandError("invalid _ossf_scorecard provenance source")
    # Older snapshots may contain CLI metadata. It is evidence about an import,
    # never an instruction to execute a binary or to acquire credentials.
    if "mode" in provenance and provenance["mode"] not in ("local", "repo"):
        raise CommandError("invalid _ossf_scorecard provenance mode")
    return dict(provenance)


def read_result_file(path: str) -> Result:
    origin = "<stdin>" if path == "-" else str(Path(path).expanduser())
    try:
        raw = sys.stdin.read() if path == "-" else Path(origin).read_text(encoding="utf-8")
        document = json.loads(raw)
    except (OSError, ValueError) as error:
        raise CommandError(f"could not read Scorecard JSON from {origin}: {error}") from error
    provenance: dict[str, Any] = {"source": "file", "origin": origin}
    if isinstance(document, Mapping) and "_ossf_scorecard" in document:
        provenance = saved_provenance(document["_ossf_scorecard"])
    return Result.parse(document, provenance=provenance)


def normalize_repo(repo: str) -> str:
    """Normalize public API repository identities without accepting URL suffixes."""
    trimmed = repo.strip().rstrip("/")
    if trimmed.count("/") == 1 and ":" not in trimmed:
        trimmed = f"github.com/{trimmed}"
    parsed = urllib.parse.urlsplit(trimmed if "://" in trimmed else f"https://{trimmed}")
    if parsed.scheme not in ("http", "https") or parsed.netloc.lower() not in ("github.com", "gitlab.com"):
        raise CommandError("use owner/repo or a public github.com or gitlab.com repository URL")
    if parsed.query or parsed.fragment or "?" in trimmed or "#" in trimmed:
        raise CommandError("repository URLs must not contain a query or fragment")
    return "/".join([parsed.netloc.lower(), *repository_path_parts(parsed)])


def repository_path_parts(parsed: urllib.parse.SplitResult) -> list[str]:
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2 or (parsed.netloc.lower() == "github.com" and len(parts) != 2):
        raise CommandError("use a repository URL, not a branch, file, or issue URL")
    if parsed.netloc.lower() == "gitlab.com" and "-" in parts:
        raise CommandError("use a GitLab repository URL, not a UI route containing /-/")
    parts[-1] = parts[-1].removesuffix(".git")
    if any(part in (".", "..") or not re.fullmatch(r"[A-Za-z0-9_.-]+", part) for part in parts):
        raise CommandError("repository path contains an invalid owner, group, or repository name")
    return parts


def missing_publication_message(normalized: str) -> str:
    message = f"{normalized} has no published Scorecard result at this endpoint. "
    if normalized.startswith("gitlab.com/"):
        return (
            message + "V1 supports reading existing GitLab API results, but implementation "
            "and publication setup guidance is limited to GitHub. You can import upstream "
            f"diagnostic JSON; consult {GITLAB_GUIDANCE} for GitLab scanning guidance. "
            "A diagnostic scan alone does not establish public publication."
        )
    return (
        message + "Inspect the official Scorecard Action workflow and publish_results setting. "
        "If publication is authorized, configure it or check the publishing run and allow for ingestion. "
        "A diagnostic scan alone does not publish results."
    )


def fetch_public_api(repo: str, *, opener: Any = urllib.request.urlopen) -> Result:
    normalized = normalize_repo(repo)
    url = f"{PUBLIC_API_BASE}/{normalized}"
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}, method="GET")
    try:
        with opener(request, timeout=API_TIMEOUT_SECONDS) as response:
            document = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise CommandError(missing_publication_message(normalized)) from error
        if error.code == 429:
            raise CommandError("public Scorecard API is rate-limited (429); wait before retrying") from error
        raise CommandError(f"public Scorecard API returned HTTP {error.code}; this does not establish a missing result") from error
    except (urllib.error.URLError, OSError) as error:
        raise CommandError(f"could not reach the public Scorecard API: {error}") from error
    except ValueError as error:
        raise CommandError(f"public Scorecard API returned invalid JSON: {error}") from error
    result = Result.parse(document, provenance={"source": "api", "origin": url, "viewer": f"{VIEWER_BASE}{normalized}"})
    if normalize_repo(result.repo).casefold() != normalized.casefold():
        raise CommandError(f"public Scorecard API returned a result for {result.repo}, not {normalized}")
    return result


def write_snapshot(result: Result, destination: Path) -> None:
    document = dict(result.document)
    document["_ossf_scorecard"] = {"schema_version": 1, "provenance": dict(result.provenance)}
    path = destination.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def engine_comparable(before: Result, after: Result) -> bool:
    if before.scorecard_version != after.scorecard_version:
        return False
    if before.scorecard_commit != after.scorecard_commit:
        return False
    unidentified = ("", "devel", "unknown")
    return (
        before.scorecard_commit.strip().lower() not in unidentified
        or before.scorecard_version.strip().lower() not in unidentified
    )


def comparison_repo_identity(repo: str) -> str:
    """Normalize explicit GitHub identities without reinterpreting import paths."""
    try:
        return normalize_github_remote(repo)
    except ValueError:
        return repo


def comparison_barriers(before: Result, after: Result) -> list[str]:
    barriers = []
    if comparison_repo_identity(before.repo) != comparison_repo_identity(after.repo):
        barriers.append("Repository identity differs; these results cannot verify a change to one project.")
    if not engine_comparable(before, after):
        barriers.append("Scorecard version or engine commit differs or is unknown; scoring behavior may differ.")
    if before.source != after.source:
        barriers.append("A published API snapshot and an imported diagnostic have different acquisition sources.")
    barriers.extend(coverage_barriers(before, after))
    before_date, after_date = parse_date(before.date), parse_date(after.date)
    if before_date and after_date and after_date < before_date:
        barriers.append("The after result is older than the before result; it cannot verify newer publication.")
    return barriers


def coverage_barriers(before: Result, after: Result) -> list[str]:
    barriers = []
    before_names = {check.name for check in before.checks}
    after_names = {check.name for check in after.checks}
    if before_names != after_names:
        barriers.append("The check set differs; aggregate scores cover different checks.")
    before_scored = {check.name for check in before.checks if check.score >= 0}
    after_scored = {check.name for check in after.checks if check.score >= 0}
    if before_scored != after_scored:
        barriers.append("Scored coverage changed: checks entered or left the inconclusive set.")
    return barriers


def check_change(name: str, old: CheckResult | None, new: CheckResult | None) -> dict[str, Any]:
    old_score, new_score = old.value if old else None, new.value if new else None
    return {
        "check": name,
        "before": old_score,
        "after": new_score,
        "before_state": old.state if old else "absent",
        "after_state": new.state if new else "absent",
        "delta": new_score - old_score if old_score is not None and new_score is not None else None,
        "reason_after": new.reason if new else "check absent from the later run",
        "details_after": list(new.details) if new else [],
        "documentation_after": dict(new.documentation) if new else {},
        "annotations_after": list(new.annotations) if new else [],
    }


def comparison_notes(before: Result, after: Result, barriers: list[str]) -> list[str]:
    notes = list(barriers)
    if before.source == "import" or after.source == "import":
        notes.append("Imported credentials and acquisition conditions are unverified; matching structure alone does not prove equivalent scans.")
    if before.commit == after.commit and before.date == after.date:
        notes.append("Both results identify the same snapshot; this does not verify a newer publishing run.")
    if barriers:
        notes.append("The aggregate delta is withheld; inspect individual check changes and both reported scores.")
    else:
        notes.append("Matching repository, engine and coverage permit a reported-score comparison; they do not prove the edits caused a change.")
    return notes


def compare(before: Result, after: Result) -> dict[str, Any]:
    """Compare reported observations; comparability is structural, not causal."""
    barriers = comparison_barriers(before, after)
    old = {check.name: check for check in before.checks}
    new = {check.name: check for check in after.checks}
    score_delta = None
    if not barriers and before.reported_score is not None and after.reported_score is not None:
        score_delta = round(after.reported_score - before.reported_score, 10)
    return {
        "before": before.summary(),
        "after": after.summary(),
        "comparable": not barriers,
        "reported_score_delta": score_delta,
        "changed": [
            check_change(name, old.get(name), new.get(name))
            for name in sorted(old.keys() | new.keys())
            if old.get(name) != new.get(name)
        ],
        "notes": comparison_notes(before, after, barriers),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Retrieve and inspect upstream OpenSSF Scorecard results.")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="read the latest published API result; does not run a scan")
    fetch.add_argument("--repo", required=True, help="owner/repo or public GitHub/GitLab repository URL")
    fetch.add_argument("--output", type=Path, help="save the upstream JSON with acquisition metadata for later use")
    explain = commands.add_parser("explain", help="inspect findings in upstream JSON or a saved API snapshot")
    explain.add_argument("--input", required=True, help="Scorecard JSON file, or - for standard input")
    diff = commands.add_parser("diff", help="compare checks and reported scores in two saved results")
    diff.add_argument("--before", required=True, help="earlier Scorecard JSON file, or -")
    diff.add_argument("--after", required=True, help="later Scorecard JSON file, or -")
    return parser


def result_payload(result: Result, state: str) -> dict[str, Any]:
    return {
        **result.summary(),
        "checks": [check.as_dict() for check in result.checks],
        "state": state,
    }


def execute_command(args: argparse.Namespace, *, opener: Any) -> dict[str, Any]:
    if args.command == "diff":
        if args.before == "-" and args.after == "-":
            raise CommandError("only one of --before and --after may read standard input")
        payload = compare(read_result_file(args.before), read_result_file(args.after))
        return {**payload, "state": "diff_computed"}
    if args.command == "explain":
        return result_payload(read_result_file(args.input), "explained")
    result = fetch_public_api(args.repo, opener=opener)
    payload = result_payload(result, "fetched")
    if args.output is not None:
        write_snapshot(result, args.output)
    payload["output"] = str(args.output) if args.output is not None else None
    return payload


def main(argv: Sequence[str] | None = None, *, opener: Any = urllib.request.urlopen) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = execute_command(args, opener=opener)
        payload["schema_version"] = 1
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (CommandError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
