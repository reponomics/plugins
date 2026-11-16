"""Normalize GitHub repository identifiers for the Scorecard helper."""

import re
from urllib.parse import urlsplit

_SCP_REMOTE = re.compile(
    r"^(?:git@)?github\.com:(?P<path>[^?#]+)$", flags=re.IGNORECASE
)


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
