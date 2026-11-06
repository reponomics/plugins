"""Small, durable JSON store for OpenSSF badge assessments."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
import copy
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
from typing import Any, Callable, Iterator
from urllib.parse import urlsplit

from .fields import normalize_assessment_fields

try:  # ``fcntl`` supplies cross-process locking on supported POSIX hosts.
    import fcntl
except ImportError:  # pragma: no cover - exercised only on non-POSIX hosts.
    fcntl = None  # type: ignore[assignment]


SCHEMA_VERSION = 1
REGISTRY_FILENAME = "registry.json"
ASSESSMENT_FILENAME = ".bestpractices.json"
UNREGISTERED_PREFIX = "unregistered:"

_SCP_REMOTE = re.compile(
    r"^(?:git@)?github\.com:(?P<path>[^?#]+)$",
    flags=re.IGNORECASE,
)
_THREAD_LOCKS: dict[str, threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()
_SAFE_KEY_CHARACTER = re.compile(r"[^a-z0-9._-]+")
_SAFE_KEY = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def normalize_github_remote(remote: str) -> str:
    """Return a lowercase ``github.com/owner/repo`` comparison and registry key.

    This is not GitHub's repository ID or the repository's display name.
    Use ``github_repository_url`` when the owner/repository spelling matters.
    """

    return github_repository_url(remote).removeprefix("https://").lower()


def github_repository_url(remote: str) -> str:
    """Convert a supported GitHub remote to HTTPS, preserving owner/repo case."""

    if not isinstance(remote, str):
        raise TypeError("GitHub remote must be a string")

    value = remote.strip()
    if not value:
        raise ValueError("GitHub remote must not be empty")

    repository_path = _github_remote_path(value).strip().strip("/")
    if repository_path.lower().endswith(".git"):
        repository_path = repository_path[:-4]
    repository_path = repository_path.rstrip("/")

    parts = repository_path.split("/")
    if (
        len(parts) != 2
        or not all(parts)
        or any(part in {".", ".."} for part in parts)
        or any(character.isspace() for character in repository_path)
    ):
        raise ValueError("GitHub remote must identify exactly one owner/repository")

    owner, repository = parts
    return f"https://github.com/{owner}/{repository}"


def _github_remote_path(value: str) -> str:
    match = _SCP_REMOTE.fullmatch(value)
    if match:
        return match.group("path")
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {"http", "https", "ssh", "git"}:
            raise ValueError(f"unsupported GitHub remote scheme: {parsed.scheme!r}")
        if (parsed.hostname or "").lower() != "github.com":
            raise ValueError("remote host must be github.com")
        if parsed.query or parsed.fragment:
            raise ValueError("GitHub remote must not contain a query or fragment")
        return parsed.path
    prefix = "github.com/"
    if not value.lower().startswith(prefix):
        raise ValueError("remote must be an HTTP(S), SSH, git@, or github.com remote")
    return value[len(prefix) :]


def _thread_lock(path: Path) -> threading.RLock:
    key = str(path.absolute())
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    """Serialize read-modify-write operations across threads and processes."""

    lock = _thread_lock(path)
    with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a+b") as lock_file:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    """Write a JSON object using a same-directory atomic replacement."""

    serialized = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        if path.exists():
            os.fchmod(descriptor, stat.S_IMODE(path.stat().st_mode))
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
            temporary_file.write(serialized)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value


def normalize_project_id(value: int | str) -> str:
    """Validate and normalize a numeric badge ID without changing storage."""

    if isinstance(value, bool):
        raise ValueError("project id must be numeric")
    text = str(value).strip()
    if not text.isdecimal():
        raise ValueError("project id must be numeric")
    return str(int(text))


def _load_assessment(path: Path) -> dict[str, Any]:
    return normalize_assessment_fields(_load_json_object(path))


def _safe_local_key(local_directory: str) -> str:
    basename = Path(local_directory).name.lower()
    key = _SAFE_KEY_CHARACTER.sub("-", basename).strip("-._")
    return key or "project"


def _unregistered_key(value: str) -> str | None:
    if not value.startswith(UNREGISTERED_PREFIX):
        return None
    key = value.removeprefix(UNREGISTERED_PREFIX)
    if not key or not _SAFE_KEY.fullmatch(key):
        raise ValueError("invalid unregistered project identifier")
    return key


def _merge_objects(current: dict[str, Any], updates: Mapping[str, Any]) -> None:
    for key, new_value in updates.items():
        old_value = current.get(key)
        if isinstance(old_value, dict) and isinstance(new_value, Mapping):
            _merge_objects(old_value, new_value)
        else:
            current[key] = copy.deepcopy(new_value)


def answer_groups(document: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for field, value in document.items():
        if field.endswith(("_status", "_justification")):
            key = ("criterion", field.rpartition("_")[0])
        else:
            key = ("metadata", field)
        groups.setdefault(key, {})[field] = value
    return groups


def _merge_local_draft(
    current: dict[str, Any], draft: Mapping[str, Any], resolved_fields: set[str],
) -> tuple[dict[str, Any], dict[str, tuple[Any, Any]]]:
    """Keep conflicting answer pairs together until explicitly resolved."""
    existing_groups = answer_groups(current)
    pending: dict[str, Any] = {}
    conflicts: dict[str, tuple[Any, Any]] = {}
    for key, answer in answer_groups(draft).items():
        existing = existing_groups.get(key, {})
        differences = {
            field: (existing.get(field), value)
            for field, value in answer.items()
            if field not in existing or existing[field] != value
        }
        if differences.keys() <= resolved_fields:
            continue
        if existing.keys() & differences.keys():
            pending.update(answer)
            conflicts.update(differences)
        else:
            current.update(answer)
    return pending, conflicts


class DataStore:
    """Persistent registry and canonical assessment storage.

    A single lock serializes registry and assessment read-modify-write cycles.
    Atomic replacement prevents readers from observing partially written JSON;
    locking additionally prevents concurrent unrelated updates from being lost.
    """

    def __init__(self, data_dir: str | os.PathLike[str]) -> None:
        self.data_dir = Path(data_dir).expanduser().resolve(strict=False)
        self.registry_path = self.data_dir / REGISTRY_FILENAME
        self.projects_dir = self.data_dir / "projects"
        self._lock_path = self.data_dir / ".storage.lock"
        self.assessment_file: Path | None = None

        self.data_dir.mkdir(parents=True, exist_ok=True)
        with _exclusive_lock(self._lock_path):
            if not self.registry_path.exists():
                _atomic_write_json(self.registry_path, self._empty_registry())
            else:
                self._read_registry_unlocked()

    @staticmethod
    def _empty_registry() -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "by_id": {},
            "by_remote": {},
            "unregistered": {},
        }

    def _read_registry_unlocked(self) -> dict[str, Any]:
        registry = _load_json_object(self.registry_path)
        if registry.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported registry schema_version: "
                f"{registry.get('schema_version')!r}"
            )
        for key in ("by_id", "by_remote", "unregistered"):
            if not isinstance(registry.get(key), dict):
                raise ValueError(f"registry field {key!r} must be an object")
        return registry

    def use_assessment_file(self, path: str | os.PathLike[str]) -> None:
        """Use this existing working file for this invocation's assessment operations."""
        selected = Path(path).expanduser().resolve(strict=True)
        _load_assessment(selected)
        self.assessment_file = selected

    def _assessment_path(self, project_id: int | str) -> Path:
        if self.assessment_file is not None:
            return self.assessment_file
        if isinstance(project_id, str):
            key = _unregistered_key(project_id)
            if key is not None:
                return self.data_dir / "unregistered" / key / ASSESSMENT_FILENAME
        return self.projects_dir / normalize_project_id(project_id) / ASSESSMENT_FILENAME

    def save_public_snapshot(
        self, project_id: int | str, remote: str, document: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Save website data separately from the selected working assessment."""
        identifier = normalize_project_id(project_id)
        snapshot = {
            "project_id": identifier,
            "remote": normalize_github_remote(remote),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "document": dict(document),
        }
        path = self.projects_dir / identifier / "public.json"
        with _exclusive_lock(self._lock_path):
            _atomic_write_json(path, snapshot)
        return snapshot

    def load_public_snapshot(
        self, project_id: int | str, remote: str,
    ) -> dict[str, Any] | None:
        """Read the last successful fetch, only for the same project and origin."""
        identifier = normalize_project_id(project_id)
        path = self.projects_dir / identifier / "public.json"
        with _exclusive_lock(self._lock_path):
            if not path.exists():
                return None
            snapshot = _load_json_object(path)
        if (
            snapshot.get("project_id") != identifier
            or snapshot.get("remote") != normalize_github_remote(remote)
        ):
            return None
        if not isinstance(snapshot.get("document"), dict) or not isinstance(
            snapshot.get("fetched_at"), str
        ):
            raise ValueError("invalid public snapshot; run status to refresh it")
        return snapshot

    def register_project(self, project_id: int | str, remote: str) -> str:
        """Register or update a bijective numeric-id-to-remote mapping."""

        identifier = normalize_project_id(project_id)
        normalized_remote = normalize_github_remote(remote)
        with _exclusive_lock(self._lock_path):
            registry = self._read_registry_unlocked()

            previous_remote = registry["by_id"].get(identifier)
            if previous_remote and previous_remote != normalized_remote:
                registry["by_remote"].pop(previous_remote, None)

            previous_identifier = registry["by_remote"].get(normalized_remote)
            if previous_identifier and previous_identifier != identifier:
                registry["by_id"].pop(previous_identifier, None)

            registry["by_id"][identifier] = normalized_remote
            registry["by_remote"][normalized_remote] = identifier
            _atomic_write_json(self.registry_path, registry)

            assessment_path = self._assessment_path(identifier)
            if not assessment_path.exists():
                _atomic_write_json(assessment_path, {})
        return identifier

    def resolve_project_id(self, remote: str) -> str | None:
        """Resolve any supported GitHub remote spelling to a registered id."""

        normalized_remote = normalize_github_remote(remote)
        with _exclusive_lock(self._lock_path):
            registry = self._read_registry_unlocked()
            identifier = registry["by_remote"].get(normalized_remote)
        return str(identifier) if identifier is not None else None

    def load_assessment(self, project_id: int | str) -> dict[str, Any]:
        """Load a registered project's canonical assessment object."""

        path = self._assessment_path(project_id)
        with _exclusive_lock(self._lock_path):
            if not path.exists():
                return {}
            return _load_assessment(path)

    def save_assessment(
        self,
        project_id: int | str,
        assessment: Mapping[str, Any],
    ) -> None:
        """Replace a project's canonical assessment atomically."""

        if not isinstance(assessment, Mapping):
            raise TypeError("assessment must be a mapping")
        path = self._assessment_path(project_id)
        with _exclusive_lock(self._lock_path):
            _atomic_write_json(path, copy.deepcopy(normalize_assessment_fields(assessment)))

    def update_assessment(
        self,
        project_id: int | str,
        updates: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Merge criterion updates without losing concurrent unrelated fields."""

        if not isinstance(updates, Mapping):
            raise TypeError("updates must be a mapping")
        path = self._assessment_path(project_id)
        with _exclusive_lock(self._lock_path):
            current = _load_assessment(path) if path.exists() else {}
            _merge_objects(current, normalize_assessment_fields(updates))
            _atomic_write_json(path, current)
            return copy.deepcopy(current)

    def transform_assessment(
        self,
        project_id: int | str,
        transform: Callable[[dict[str, Any]], Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Atomically transform the latest assessment under the store lock."""

        if not callable(transform):
            raise TypeError("transform must be callable")
        path = self._assessment_path(project_id)
        with _exclusive_lock(self._lock_path):
            current = _load_assessment(path) if path.exists() else {}
            transformed = transform(copy.deepcopy(current))
            if not isinstance(transformed, Mapping):
                raise TypeError("assessment transform must return a mapping")
            result = copy.deepcopy(normalize_assessment_fields(transformed))
            _atomic_write_json(path, result)
            return copy.deepcopy(result)

    def create_unregistered(
        self,
        local_project_directory: str | os.PathLike[str],
        remote: str | None = None,
        project_name: str | None = None,
    ) -> dict[str, str | None]:
        """Create or replace a minimal record for a project with no badge id."""

        local_directory = str(
            Path(local_project_directory).expanduser().resolve(strict=False)
        )
        with _exclusive_lock(self._lock_path):
            registry = self._read_registry_unlocked()
            existing = registry["unregistered"].get(local_directory)
            if isinstance(existing, Mapping) and isinstance(
                existing.get("storage_key"), str
            ):
                storage_key = existing["storage_key"]
            else:
                base_key = _safe_local_key(local_directory)
                occupied = {
                    item.get("storage_key")
                    for item in registry["unregistered"].values()
                    if isinstance(item, Mapping)
                }
                storage_key = base_key
                counter = 2
                while storage_key in occupied:
                    storage_key = f"{base_key}-{counter}"
                    counter += 1

            record: dict[str, str | None] = {
                "local_project_directory": local_directory,
                "remote": normalize_github_remote(remote) if remote else None,
                "project_name": project_name or Path(local_directory).name,
                "storage_key": storage_key,
            }
            registry["unregistered"][local_directory] = record
            _atomic_write_json(self.registry_path, registry)
            assessment_path = self._assessment_path(f"{UNREGISTERED_PREFIX}{storage_key}")
            if not assessment_path.exists():
                _atomic_write_json(assessment_path, {})
        return copy.deepcopy(record)

    def load_unregistered(
        self,
        local_project_directory: str | os.PathLike[str],
    ) -> dict[str, str | None] | None:
        """Load a minimal unregistered-project record by local directory."""

        local_directory = str(
            Path(local_project_directory).expanduser().resolve(strict=False)
        )
        with _exclusive_lock(self._lock_path):
            registry = self._read_registry_unlocked()
            record = registry["unregistered"].get(local_directory)
        return copy.deepcopy(record) if record is not None else None

    def handoff_unregistered(
        self,
        local_project_directory: str | os.PathLike[str],
        project_id: int | str,
        *,
        resolved_fields: set[str] | None = None,
    ) -> tuple[dict[str, Any], dict[str, tuple[Any, Any]]]:
        """Transfer a local draft; retain disagreements for an explicit apply.

        Acknowledgements must follow a successful write of those fields. Write
        the destination before pruning the draft so interrupted handoffs can retry.
        """
        if self.assessment_file is not None:
            return self.load_assessment(project_id), {}
        local_directory = str(Path(local_project_directory).expanduser().resolve())
        identifier = normalize_project_id(project_id)
        with _exclusive_lock(self._lock_path):
            registry = self._read_registry_unlocked()
            destination = self._assessment_path(identifier)
            current = _load_assessment(destination) if destination.exists() else {}
            record = registry["unregistered"].get(local_directory)
            if record is None:
                return current, {}
            if record.get("remote") != registry["by_id"].get(identifier):
                raise ValueError("local assessment remote does not match the registered project")
            source = self._assessment_path(f"{UNREGISTERED_PREFIX}{record['storage_key']}")
            draft = _load_assessment(source) if source.exists() else {}
            pending, conflicts = _merge_local_draft(current, draft, resolved_fields or set())
            _atomic_write_json(destination, current)
            if pending:
                _atomic_write_json(source, pending)
            else:
                source.unlink(missing_ok=True)
                del registry["unregistered"][local_directory]
                _atomic_write_json(self.registry_path, registry)
            return current, conflicts

    def unregistered_identifier(
        self,
        local_project_directory: str | os.PathLike[str],
    ) -> str | None:
        """Return the server/storage identifier for an unregistered record."""

        record = self.load_unregistered(local_project_directory)
        if record is None:
            return None
        storage_key = record.get("storage_key")
        if not isinstance(storage_key, str) or not _SAFE_KEY.fullmatch(storage_key):
            raise ValueError("unregistered record has an invalid storage_key")
        return f"{UNREGISTERED_PREFIX}{storage_key}"
