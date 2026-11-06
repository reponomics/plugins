"""Resolve projects and synchronize read-only OpenSSF assessment sources."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .fields import normalize_assessment_fields

from .storage import (
    DataStore, answer_groups, github_repository_url, normalize_github_remote, normalize_project_id,
)


DEFAULT_BASE_URL = "https://www.bestpractices.dev"
DEFAULT_USER_AGENT = "badge-buddy/1 (+https://github.com/reponomics/plugins)"
MAX_RESPONSE_BYTES = 5_000_000
MAX_LOOKUP_PAGES = 10
PROJECT_METADATA_FIELDS = {
    "name",
    "description",
    "license",
    "implementation_languages",
}


class ProjectResolutionError(RuntimeError):
    """Raised when a repository cannot be resolved safely."""


class UnregisteredProjectError(ProjectResolutionError):
    """Raised when no badge entry exists and explicit opt-in was not given."""


@dataclass(frozen=True, slots=True)
class RepositoryIdentity:
    root: Path
    remote: str
    project_name: str
    url: str


@dataclass(frozen=True, slots=True)
class ProjectResolution:
    identifier: str
    project_id: str | None
    registered: bool
    repository: RepositoryIdentity


@dataclass(frozen=True, slots=True)
class SyncConflict:
    field: str
    preserved: Any
    incoming: Any
    source: str


@dataclass(frozen=True, slots=True)
class SyncResult:
    resolution: ProjectResolution
    assessment: dict[str, Any]
    conflicts: tuple[SyncConflict, ...]
    repository_file: Path | None
    public_loaded: bool
    public_document: Mapping[str, Any] = field(default_factory=dict)
    public_fetched_at: str | None = None


def write_assessment_file(path: Path, assessment: Mapping[str, Any]) -> None:
    """Atomically export an assessment to an explicitly selected path."""

    serialized = (
        json.dumps(
            dict(assessment),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    if path.exists() and path.is_dir():
        raise IsADirectoryError(path)
    if not path.parent.is_dir():
        raise FileNotFoundError(path.parent)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _git_value(
    repository: Path,
    *arguments: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    command = ["git", "-C", str(repository), *arguments]
    try:
        completed = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ProjectResolutionError(
            f"could not run {' '.join(command)}: {error}"
        ) from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git failed"
        raise ProjectResolutionError(f"{' '.join(command)}: {detail}")
    value = completed.stdout.strip()
    if not value:
        raise ProjectResolutionError(f"{' '.join(command)} returned no value")
    return value


def discover_repository(
    repository: str | Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> RepositoryIdentity:
    """Derive repository root and normalized origin using ``git -C``."""

    requested = Path(repository).expanduser().resolve(strict=False)
    root = Path(
        _git_value(requested, "rev-parse", "--show-toplevel", runner=runner)
    ).resolve(strict=False)
    origin = _git_value(root, "remote", "get-url", "origin", runner=runner)
    try:
        normalized_remote = normalize_github_remote(origin)
    except (TypeError, ValueError) as error:
        raise ProjectResolutionError(
            f"unsupported origin remote {origin!r}: {error}"
        ) from error
    return RepositoryIdentity(
        root=root,
        remote=normalized_remote,
        project_name=root.name,
        url=github_repository_url(origin),
    )


class BestPracticesClient:
    """Polite sequential client for public bestpractices.dev JSON reads."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        minimum_interval: float = 1.0,
        timeout: float = 20.0,
        opener: Callable[..., Any] = urlopen,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if minimum_interval < 0:
            raise ValueError("minimum_interval must not be negative")
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.minimum_interval = minimum_interval
        self.timeout = timeout
        self._opener = opener
        self._clock = clock
        self._sleeper = sleeper
        self._last_request_started: float | None = None

    def _wait(self) -> None:
        if self._last_request_started is None:
            return
        remaining = self.minimum_interval - (self._clock() - self._last_request_started)
        if remaining > 0:
            self._sleeper(remaining)

    def _get_json(self, path: str, query: Mapping[str, str] | None = None) -> Any:
        suffix = f"?{urlencode(query)}" if query else ""
        request = Request(
            f"{self.base_url}{path}{suffix}",
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
            method="GET",
        )
        self._wait()
        self._last_request_started = self._clock()
        try:
            with self._opener(request, timeout=self.timeout) as response:
                payload = response.read(MAX_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise ProjectResolutionError(
                f"public API read failed for {request.full_url}: {error}"
            ) from error
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ProjectResolutionError("public API response exceeded the size limit")
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProjectResolutionError(
                f"public API returned invalid JSON for {request.full_url}"
            ) from error

    def lookup_project_id(self, remote: str) -> str | None:
        """Find one exact GitHub repository match using case-insensitive search.

        BadgeApp's ``url`` query is case-sensitive; ``pq`` retrieves a wider
        case-insensitive candidate set. Inspect all pages and verify repository
        keys locally before accepting a unique numeric BadgeApp project ID.
        """

        repository_url = github_repository_url(remote)
        normalized_remote = normalize_github_remote(remote)
        identifiers: set[str] = set()
        # Older badge entries may store an HTTP URL for the same GitHub repo.
        for prefix in (repository_url, repository_url.replace("https://", "http://", 1)):
            for candidate in self._lookup_candidates(prefix):
                identifier = _matching_project_id(candidate, normalized_remote)
                if identifier is not None:
                    identifiers.add(identifier)

        if len(identifiers) > 1:
            choices = ", ".join(sorted(identifiers, key=int))
            raise ProjectResolutionError(
                f"repository lookup returned multiple project ids: {choices}; "
                "pass --project-id to select the intended entry"
            )
        return next(iter(identifiers), None)

    def _lookup_candidates(self, prefix: str) -> Iterator[Any]:
        for page in range(1, MAX_LOOKUP_PAGES + 1):
            payload = self._get_json(
                "/projects.json",
                {"pq": prefix, "sort": "id", "sort_direction": "asc", "page": str(page)},
            )
            if not isinstance(payload, list):
                raise ProjectResolutionError("project lookup did not return a JSON array")
            if not payload:
                return
            yield from payload
        raise ProjectResolutionError(
            "repository lookup is incomplete: search page limit reached; "
            "pass --project-id to select the known badge entry"
        )

    def fetch_project(self, project_id: int | str) -> dict[str, Any]:
        """Read one project's public JSON representation."""

        identifier = str(project_id)
        if not identifier.isdecimal():
            raise ValueError("public project id must be numeric")
        payload = self._get_json(f"/projects/{int(identifier)}.json")
        if not isinstance(payload, dict):
            raise ProjectResolutionError(
                "public project response was not a JSON object"
            )
        return payload


def _matching_project_id(candidate: Any, normalized_remote: str) -> str | None:
    if not isinstance(candidate, Mapping):
        raise ProjectResolutionError("project lookup contains a non-object entry")
    # A matching homepage must not override a different repository URL.
    remote = candidate.get("repo_url") or candidate.get("homepage_url")
    if not _remote_matches(remote, normalized_remote):
        return None
    identifier = candidate.get("id")
    if isinstance(identifier, bool) or not str(identifier).isdecimal():
        raise ProjectResolutionError("matching badge entry has an invalid project id")
    return str(int(identifier))


def _remote_matches(value: Any, normalized_remote: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        return normalize_github_remote(value) == normalized_remote
    except (TypeError, ValueError):
        return False


def resolve_project(
    store: DataStore,
    repository: str | Path,
    *,
    project_id: int | str | None = None,
    client: BestPracticesClient | None = None,
    allow_unregistered: bool = False,
) -> ProjectResolution:
    """Reuse a verified association or select an online candidate to validate."""

    identity = discover_repository(repository)
    registered_id = store.resolve_project_id(identity.remote)
    identifier: str | None
    if project_id is not None:
        identifier = normalize_project_id(project_id)
        if client is None and identifier != registered_id:
            raise ProjectResolutionError(
                "project id is not verified for this repository; run status online "
                f"with --project-id {identifier} before using local commands"
            )
    else:
        identifier = registered_id
        if identifier is None and client is not None:
            identifier = client.lookup_project_id(identity.url)

    if identifier is not None:
        identifier = normalize_project_id(identifier)
        return ProjectResolution(
            identifier=identifier,
            project_id=identifier,
            registered=True,
            repository=identity,
        )

    if not allow_unregistered:
        raise UnregisteredProjectError(
            "no exact bestpractices.dev project entry was found; register the "
            "project or explicitly pass --allow-unregistered for a local-only review"
        )

    store.create_unregistered(
        identity.root,
        remote=identity.remote,
        project_name=identity.project_name,
    )
    unregistered_identifier = store.unregistered_identifier(identity.root)
    if unregistered_identifier is None:  # Defensive: creation must establish it.
        raise ProjectResolutionError("failed to create the unregistered project record")
    return ProjectResolution(
        identifier=unregistered_identifier,
        project_id=None,
        registered=False,
        repository=identity,
    )


def load_repository_assessment(
    repository_root: str | Path,
) -> tuple[Path | None, dict[str, Any]]:
    """Load the first supported repository assessment location, if present."""

    root = Path(repository_root)
    for candidate in (
        root / ".bestpractices.json",
        root / ".project.d" / "bestpractices.json",
    ):
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProjectResolutionError(
                f"invalid repository assessment {candidate}: {error}"
            ) from error
        if not isinstance(payload, dict):
            raise ProjectResolutionError(
                f"repository assessment {candidate} must contain a JSON object"
            )
        return candidate, payload
    return None, {}


def _assessment_fields(document: Mapping[str, Any]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for key, value in normalize_assessment_fields(document).items():
        if (
            key in PROJECT_METADATA_FIELDS
            or key.endswith("_status")
            or key.endswith("_justification")
        ):
            selected[key] = value
    return selected


def _observe_source(
    current: dict[str, Any],
    incoming_document: Mapping[str, Any],
    source: str,
    conflicts: list[SyncConflict],
) -> None:
    """Initialize absent answers; report differences without changing existing ones."""
    existing_groups = answer_groups(current)
    for key, incoming in answer_groups(_assessment_fields(incoming_document)).items():
        if key not in existing_groups:
            current.update(incoming)
            continue
        existing = existing_groups[key]
        for field, value in incoming.items():
            if field not in existing or existing[field] != value:
                conflicts.append(SyncConflict(field, existing.get(field), value, source))


def handoff_local_assessment(
    store: DataStore,
    resolution: ProjectResolution,
    *,
    resolved_fields: set[str] | None = None,
) -> tuple[dict[str, Any], tuple[SyncConflict, ...]]:
    assessment, conflicts = store.handoff_unregistered(
        resolution.repository.root, resolution.identifier, resolved_fields=resolved_fields,
    )
    return assessment, tuple(
        SyncConflict(field, preserved, incoming, "local_draft")
        for field, (preserved, incoming) in sorted(conflicts.items())
    )


def _public_snapshot(
    store: DataStore,
    resolution: ProjectResolution,
    public_document: Mapping[str, Any],
    *,
    refreshed: bool,
) -> dict[str, Any] | None:
    if not resolution.registered:
        return None
    if refreshed:
        return store.save_public_snapshot(
            resolution.identifier, resolution.repository.remote, public_document,
        )
    return store.load_public_snapshot(
        resolution.identifier, resolution.repository.remote,
    )


def synchronize_project(
    store: DataStore,
    repository: str | Path,
    *,
    project_id: int | str | None = None,
    client: BestPracticesClient | None = None,
    allow_unregistered: bool = False,
    user_updates: Mapping[str, Any] | None = None,
) -> SyncResult:
    """Read external sources without replacing existing local answers.

    Public data initialize wholly absent answers in the selected working file. Existing
    status/justification pairs remain intact, including question marks and empty
    wording. Differences are returned for the main agent to reconcile. Explicit
    current-session ``user_updates`` are applied last. Without a client, the saved
    public snapshot is returned for comparisons but never merged again.
    """

    repository_file, _ = load_repository_assessment(discover_repository(repository).root)
    if repository_file is not None and store.assessment_file is None:
        raise ProjectResolutionError(
            "the repository has an assessment; select --assessment-file with a "
            "temporary working copy, or the repository file for authorized direct edits"
        )

    resolution = resolve_project(
        store,
        repository,
        project_id=project_id,
        client=client,
        allow_unregistered=allow_unregistered,
    )
    public_document: dict[str, Any] = {}
    if resolution.registered and client is not None:
        public_document = client.fetch_project(resolution.project_id or "")
        # Match lookup's homepage fallback without allowing it to override a
        # populated repository URL. Missing identity cannot verify an entry.
        remote = public_document.get("repo_url") or public_document.get("homepage_url")
        if not _remote_matches(remote, resolution.repository.remote):
            raise ProjectResolutionError(
                "public project repository identity does not match the repository origin; "
                "the entry must identify this repository in repo_url or, when absent, homepage_url"
            )
        store.register_project(resolution.identifier, resolution.repository.remote)

    conflicts: list[SyncConflict] = []
    if resolution.registered:
        _, local_conflicts = handoff_local_assessment(store, resolution)
        conflicts.extend(local_conflicts)

    def observe_latest(current: dict[str, Any]) -> dict[str, Any]:
        if public_document:
            _observe_source(current, public_document, "public API", conflicts)
        return current

    assessment = store.transform_assessment(resolution.identifier, observe_latest)
    if user_updates:
        assessment = store.update_assessment(resolution.identifier, user_updates)
        if resolution.registered:
            assessment, local_conflicts = handoff_local_assessment(
                store, resolution, resolved_fields=set(user_updates),
            )
            conflicts = [item for item in conflicts if item.source != "local_draft"]
            conflicts.extend(local_conflicts)
    # Cached website data supports comparisons but must not reintroduce conflicts
    # for answers deliberately edited since the last online status command.
    public_loaded = client is not None and resolution.registered
    snapshot = _public_snapshot(
        store, resolution, public_document, refreshed=public_loaded,
    )
    if snapshot is not None:
        public_document = snapshot["document"]
    return SyncResult(
        resolution=resolution,
        assessment=assessment,
        conflicts=tuple(conflicts),
        repository_file=repository_file,
        public_loaded=public_loaded,
        public_document=public_document,
        public_fetched_at=snapshot["fetched_at"] if snapshot else None,
    )
