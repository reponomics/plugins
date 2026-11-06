"""Render the canonical assessment as a passive, self-refreshing review board."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from typing import Any, Iterator, Mapping

try:  # ``fcntl`` supplies cross-process locking on supported POSIX hosts.
    import fcntl
except ImportError:  # pragma: no cover - exercised only on non-POSIX hosts.
    fcntl = None  # type: ignore[assignment]

from .criteria import CriteriaCatalog, Criterion


REFRESH_SECONDS = 5
_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "review"
_LIVE_ROOT = Path(tempfile.gettempdir()) / "ossf-best-practices-review"
_VALID_STATUSES = {"Met", "Unmet", "N/A", "?"}
_THREAD_LOCKS: dict[str, threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()
_BUCKETS = (
    (
        "needs_input",
        "Not yet answered",
        "Read the criteria that do not have an answer yet.",
    ),
    (
        "unmet",
        "Unmet",
        "Criteria marked Unmet. Explore what would help meet them.",
    ),
    (
        "na",
        "N/A answers",
        "Criteria marked as not applicable to this project.",
    ),
    (
        "met",
        "Met answers",
        "Criteria marked Met. Review the answers and supporting information.",
    ),
)


def review_path(data_dir: str | Path, project_id: str, section: str) -> Path:
    """Return a stable temporary path without exposing private storage details."""

    identity = f"{Path(data_dir).expanduser().resolve(strict=False)}\0{project_id}"
    digest = sha256(identity.encode()).hexdigest()[:12]
    safe_id = re.sub(r"[^a-zA-Z0-9._-]+", "-", project_id).strip("-._")
    return _LIVE_ROOT / f"{safe_id or 'project'}-{digest}-{section}.html"


@contextmanager
def board_refresh_lock(
    data_dir: str | Path,
    project_id: str,
) -> Iterator[None]:
    """Serialize canonical reload-and-render cycles for one project."""

    sample = review_path(data_dir, project_id, "passing")
    lock_path = sample.with_name(f".{sample.stem.rsplit('-', 1)[0]}.lock")
    lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    key = str(lock_path.absolute())
    with _THREAD_LOCKS_GUARD:
        thread_lock = _THREAD_LOCKS.setdefault(key, threading.RLock())
    with thread_lock, lock_path.open("a+b") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def build_board_payload(
    document: Mapping[str, Any],
    *,
    project_id: str,
    section: str,
    catalog: CriteriaCatalog,
) -> dict[str, Any]:
    """Project one canonical flat assessment into display-only browser data."""

    responses = catalog.classify_flat(document)[section]
    criteria = catalog.section(section)
    answers = {
        criterion.id: _answer(responses.get(criterion.id, {}))
        for criterion in criteria
    }
    bucket_ids = {key: [] for key, _label, _description in _BUCKETS}
    for criterion in criteria:
        bucket_ids[_bucket_key(answers[criterion.id]["status"])].append(criterion.id)

    normalized_criteria = [_criterion_payload(criterion) for criterion in criteria]
    payload: dict[str, Any] = {
        "projectId": project_id,
        "section": section,
        "generatedAt": datetime.now(UTC).isoformat(),
        "refreshSeconds": REFRESH_SECONDS,
        "criteria": normalized_criteria,
        "answers": answers,
        "buckets": [
            {
                "key": key,
                "label": label,
                "description": description,
                "count": len(bucket_ids[key]),
                "criterionIds": bucket_ids[key],
            }
            for key, label, description in _BUCKETS
        ],
        "total": len(criteria),
    }
    return payload


def render_board(payload: Mapping[str, Any]) -> str:
    """Embed assets and assessment data in one local, self-contained document."""

    template = (_ASSET_DIR / "index.html").read_text(encoding="utf-8")
    stylesheet = (_ASSET_DIR / "review.css").read_text(encoding="utf-8")
    script = (_ASSET_DIR / "review.js").read_text(encoding="utf-8")
    serialized = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    serialized = serialized.replace("<", "\\u003c").replace(">", "\\u003e")
    return (
        template.replace("{{REVIEW_CSS}}", stylesheet)
        .replace("{{ASSESSMENT_JSON}}", serialized)
        .replace("{{REVIEW_SCRIPT}}", script)
    )


def write_board(
    document: Mapping[str, Any],
    output_path: str | Path,
    *,
    project_id: str,
    section: str,
    catalog: CriteriaCatalog,
) -> Path:
    """Atomically replace a passive review document at an explicit path."""

    destination = Path(output_path)
    payload = build_board_payload(
        document,
        project_id=project_id,
        section=section,
        catalog=catalog,
    )
    markup = render_board(payload)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(markup)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def _answer(response: Mapping[str, Any]) -> dict[str, str]:
    raw_status = response.get("status", "?")
    status = str(raw_status).strip() if raw_status is not None else "?"
    if status not in _VALID_STATUSES:
        status = "?"
    raw_justification = response.get("justification", "")
    justification = "" if raw_justification is None else str(raw_justification)
    return {"status": status, "justification": justification}


def _bucket_key(status: str) -> str:
    return {"Met": "met", "Unmet": "unmet", "N/A": "na"}.get(
        status, "needs_input"
    )


def _criterion_payload(criterion: Criterion) -> dict[str, Any]:
    labels = []
    if criterion.future:
        labels.append("(Future criterion)")
    elif criterion.obsolete:
        labels.append("(Obsolete criterion)")
    description = " ".join([*labels, plain_text(criterion.description)])
    return {
        "id": criterion.id,
        "displayId": criterion.display_id,
        "category": criterion.category,
        "description": description,
        "details": plain_text(criterion.details or ""),
        "naAllowed": criterion.na_allowed,
        "naJustificationRequired": criterion.na_justification_required,
        "metJustificationRequired": criterion.met_justification_required,
        "metUrlRequired": criterion.met_url_required,
    }


class _TextExtractor(HTMLParser):
    _BREAK_TAGS = {
        "br",
        "dd",
        "div",
        "dt",
        "li",
        "ol",
        "p",
        "tr",
        "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in self._BREAK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._BREAK_TAGS:
            self.parts.append(" ")


def plain_text(value: str) -> str:
    """Return readable text from the small HTML fragments in upstream criteria."""

    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()
