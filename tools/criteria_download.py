"""Bounded, anonymous downloads and reproducible application-page snapshots."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any
import urllib.error
import urllib.request
import urllib.robotparser

from criteria_site import BASE_URL, SECTIONS, parse_application

USER_AGENT = "badge-buddy-criteria-maintenance/1.0"
MAX_BYTES = 4 * 1024 * 1024


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        raise ValueError(f"unexpected redirect from {req.full_url} to {newurl}")


class Downloader:
    """At most one request per second, with bounded retries and body sizes."""

    def __init__(self) -> None:
        self.opener = urllib.request.build_opener(NoRedirects())
        self.last_request = 0.0

    def _pause(self) -> None:
        time.sleep(max(0, 1.0 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()

    def get(self, url: str, content_type: str) -> tuple[bytes, dict[str, str]]:
        for attempt in range(3):
            self._pause()
            try:
                return self._get_once(url, content_type)
            except urllib.error.HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise
                delay = _retry_delay(error.headers.get("Retry-After"), attempt)
                time.sleep(delay)
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        raise AssertionError("unreachable retry state")

    def _get_once(self, url: str, content_type: str) -> tuple[bytes, dict[str, str]]:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": content_type})
        with self.opener.open(request, timeout=30) as response:
            if response.status != 200 or response.headers.get_content_type() != content_type:
                raise ValueError(f"{url}: unexpected HTTP status or content type")
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError(f"{url}: response exceeds {MAX_BYTES} bytes")
            headers = {key: response.headers[key] for key in ("ETag", "Last-Modified") if key in response.headers}
            return data, headers


def _retry_delay(value: str | None, attempt: int) -> float:
    # Respect a server-requested long pause by stopping this run, not retrying
    # earlier than requested or blocking a maintainer process indefinitely.
    delay = float(value) if value and value.isdigit() else float(2 ** attempt)
    if value and not value.isdigit():
        from email.utils import parsedate_to_datetime
        retry_at = parsedate_to_datetime(value)
        delay = max(0, (retry_at - dt.datetime.now(dt.timezone.utc)).total_seconds())
    if delay > 60:
        raise ValueError(f"server requested retry after {value}; retry maintenance later")
    return delay


def download_snapshot(destination: Path, downloader: Downloader | None = None) -> dict[str, Any]:
    client = downloader or Downloader()
    robots_url = BASE_URL + "/robots.txt"
    robots_data, _ = client.get(robots_url, "text/plain")
    robots = urllib.robotparser.RobotFileParser(robots_url)
    robots.parse(robots_data.decode("utf-8").splitlines())
    pages, files = {}, {}
    for section in SECTIONS:
        url = f"{BASE_URL}/en/projects/1/{section}"
        if not robots.can_fetch(USER_AGENT, url):
            raise ValueError(f"robots.txt does not permit downloading {url}")
        data, headers = client.get(url, "text/html")
        parse_application(data.decode("utf-8"))
        sha = digest(data)
        filename = f"{section}-{sha}.html"
        files[filename] = data
        pages[section] = {"url": url, "file": filename, "sha256": sha, "headers": headers}
    manifest = {
        "schema_version": 1, "downloaded_at": now(), "base_url": BASE_URL,
        "project_id": 1, "robots": {"url": robots_url, "sha256": digest(robots_data)}, "pages": pages,
    }
    # Content-addressed files make the manifest the sole atomic publication
    # point. An interrupted download never invalidates the previous snapshot.
    for filename, data in files.items():
        path = destination / filename
        atomic_write(path, data)
    _write_notices(destination)
    atomic_write(destination / "manifest.json", json_bytes(manifest))
    return manifest


def _write_notices(destination: Path) -> None:
    # Snapshots may accompany CI reports as downloadable evidence.
    root = Path(__file__).resolve().parents[1]
    plugin = root / "plugins/badge-buddy"
    atomic_write(destination / "THIRD_PARTY_NOTICES.md", (root / "THIRD_PARTY_NOTICES.md").read_bytes())
    license_path = plugin / "assets/examples/badgeapp/CDLA-Permissive-2.0.txt"
    atomic_write(destination / license_path.name, license_path.read_bytes())
    atomic_write(destination / "README.txt", (
        "Public bestpractices.dev application snapshots for criteria verification.\n"
        "Source URLs and observation metadata are in manifest.json.\n"
        "Credit: David A. Wheeler and the OpenSSF Best Practices badge contributors.\n"
        "Public entry data: CDLA-Permissive-2.0 (license enclosed).\n"
        "Criteria and software notices: THIRD_PARTY_NOTICES.md.\n"
    ).encode())


def read_snapshot(directory: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest.get("schema_version") != 1 or manifest.get("base_url") != BASE_URL:
        raise ValueError("unsupported snapshot manifest or application origin")
    if set(manifest.get("pages", {})) != set(SECTIONS) or manifest.get("project_id") != 1:
        raise ValueError("snapshot must contain all six public application sections")
    _check_timestamp(manifest["downloaded_at"])
    pages = {section: _read_page(directory, section, manifest["pages"][section]) for section in SECTIONS}
    return manifest, pages


def _check_timestamp(value: str) -> None:
    timestamp = dt.datetime.fromisoformat(value)
    if timestamp.tzinfo is None or timestamp > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        raise ValueError("snapshot timestamp must be a valid past UTC observation")


def _read_page(directory: Path, section: str, entry: dict[str, Any]) -> list[dict[str, Any]]:
    sha = entry["sha256"]
    filename = entry["file"]
    if re.fullmatch(r"[0-9a-f]{64}", sha) is None or filename != f"{section}-{sha}.html":
        raise ValueError(f"{section}: invalid snapshot filename or checksum")
    if entry["url"] != f"{BASE_URL}/en/projects/1/{section}":
        raise ValueError(f"{section}: snapshot has unexpected source URL")
    data = (directory / filename).read_bytes()
    if digest(data) != sha:
        raise ValueError(f"{section}: snapshot checksum mismatch; download again")
    return parse_application(data.decode("utf-8"))
