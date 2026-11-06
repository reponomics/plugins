"""Build human-review submission artifacts from the canonical assessment.

Both builders encode the BadgeApp automation semantics distilled in
the ossf-bp-badges skill's ``references/application.md``: proposal URLs are upstream's
primary automation path (one-shot, section-isolated; the logged-in human reviews the
highlighted proposals and saves). Proposal URLs can fill blank justifications
or replace existing wording with matching overrides. The console fill script
offers another way to transfer wording changes or answers too long for a URL.

Neither artifact writes to bestpractices.dev. A proposal URL renders
highlights in the edit form until the human saves; the fill script fills form
fields in the user's own browser session and never submits.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import urlencode

from .criteria import CriteriaCatalog, Criterion


PRODUCTION_BASE_URL = "https://www.bestpractices.dev"
STAGING_BASE_URL = "https://staging.bestpractices.dev"
# Proposal URLs carry criterion justifications in their query string and may
# be opened in the user's browser, so their origin is restricted to the sites
# the badge authority operates. Nothing else is accepted, at any layer.
ALLOWED_BASE_URLS: tuple[str, ...] = (PRODUCTION_BASE_URL, STAGING_BASE_URL)
# Upstream documents no URL length limit, but real hosting/CDN stacks reject
# request lines around 8 KB, and a URL near that size failed in field use.
# 6,000 bytes leaves headroom for the request line and proxy quirks.
DEFAULT_MAX_URL_BYTES = 6000
# Upstream silently ignores an overrides parameter beyond these caps.
OVERRIDES_MAX_CHARS = 10_000
OVERRIDES_MAX_PATTERNS = 1_000

_PROPOSABLE_STATUSES = frozenset({"Met", "Unmet", "N/A"})


@dataclass(frozen=True, slots=True)
class ProposalPlan:
    """Proposal URLs plus an account of every answer that was not proposed."""

    urls: tuple[str, ...]
    proposed: tuple[str, ...]
    skipped_unknown: tuple[str, ...]
    dropped_no_op: tuple[str, ...]
    dropped_justification_only: tuple[str, ...]
    oversize: tuple[str, ...] = ()


def _justification_text(value: Any) -> str:
    """Preserve Markdown-significant whitespace in comparisons and submissions."""

    return value if isinstance(value, str) else ""


def _section_answers(
    assessment: Mapping[str, Any],
    catalog: CriteriaCatalog,
    section: str,
) -> list[tuple[Criterion, dict[str, Any]]]:
    answers = catalog.classify_flat(assessment)[section]
    return [
        (criterion, answers[criterion.id])
        for criterion in catalog.section(section)
        if criterion.id in answers
    ]


def _live_value(
    public_document: Mapping[str, Any],
    criterion: Criterion,
    suffix: str,
) -> Any:
    """Read a live field tolerating the baseline display-id readback form."""

    for key in (f"{criterion.id}_{suffix}", f"{criterion.display_id}_{suffix}"):
        if key in public_document:
            return public_document[key]
    return None


def wording_only_criteria(
    assessment: Mapping[str, Any],
    catalog: CriteriaCatalog,
    *,
    section: str,
    public_document: Mapping[str, Any],
) -> tuple[str, ...]:
    """Criteria whose live status matches but whose wording differs.

    This is the fill script's default scope. Proposal URLs can also carry
    these changes, with matching overrides when replacing existing wording.
    The badge site's own detectives commonly produce these entries:
    matching statuses with thin justifications that omit evidence URLs.
    """

    answers = catalog.classify_flat(assessment)[section]
    selected: list[str] = []
    for criterion in catalog.section(section):
        answer = answers.get(criterion.id, {})
        status = answer.get("status")
        if not isinstance(status, str) or status not in _PROPOSABLE_STATUSES:
            continue
        live_status = _live_value(public_document, criterion, "status")
        if not (isinstance(live_status, str) and live_status.strip() == status):
            continue
        justification = _justification_text(answer.get("justification"))
        live_justification = _justification_text(
            _live_value(public_document, criterion, "justification")
        )
        if "justification" in answer and justification != live_justification:
            selected.append(criterion.id)
    return tuple(selected)


def validate_overrides(overrides: str) -> None:
    """Reject overrides values upstream would silently ignore."""

    if len(overrides) > OVERRIDES_MAX_CHARS:
        raise ValueError(
            "overrides exceeds upstream's 10,000-character cap and would be "
            "silently ignored"
        )
    if overrides.count(",") + 1 > OVERRIDES_MAX_PATTERNS:
        raise ValueError(
            "overrides exceeds upstream's 1,000-pattern cap and would be "
            "silently ignored"
        )


def validate_base_url(value: str) -> str:
    """Return the normalized badge-site base URL, or raise ``ValueError``.

    Only the production and staging badge sites are accepted; a trailing
    slash is tolerated, any other scheme, host, path, or port is not.
    """

    candidate = value.strip().rstrip("/")
    if candidate in ALLOWED_BASE_URLS:
        return candidate
    raise ValueError(
        "base URL must be one of "
        + ", ".join(ALLOWED_BASE_URLS)
        + f"; got {value!r}"
    )


def build_proposal_urls(
    assessment: Mapping[str, Any],
    catalog: CriteriaCatalog,
    *,
    section: str,
    project_id: str,
    base_url: str = PRODUCTION_BASE_URL,
    overrides: str | None = None,
    reanalyze: bool = False,
    max_url_bytes: int = DEFAULT_MAX_URL_BYTES,
    public_document: Mapping[str, Any] | None = None,
) -> ProposalPlan:
    """Build official automation-proposal URL(s) for one section.

    ``?`` and missing statuses are never emitted. The checked upstream
    controller ignores unknown URL statuses, despite older documentation
    describing them as resets.

    When the public document is available, unchanged answers are omitted.
    Wording-only changes can fill blank text; replacing existing text needs
    an override. Without overrides those changes are reported separately.
    Supplied override patterns are passed through for the site to match;
    inclusion in ``proposed`` means encoded in a URL, not applied by the site.
    """

    if not project_id:
        raise ValueError("project_id is required")
    if overrides:
        validate_overrides(overrides)

    base = validate_base_url(base_url)
    prefix = f"{base}/en/projects/{int(project_id)}/{section}/edit?"

    common: list[tuple[str, str]] = []
    if overrides:
        common.append(("overrides", overrides))
    if reanalyze:
        common.append(("reanalyze", "1"))

    proposed: list[str] = []
    skipped_unknown: list[str] = []
    dropped_no_op: list[str] = []
    dropped_justification_only: list[str] = []
    oversize: list[str] = []
    live = public_document or {}
    # Each entry keeps one criterion's status and justification together:
    # upstream couples the pair, so chunking must never split them.
    criterion_pairs: list[tuple[str, list[tuple[str, str]]]] = []

    answers = catalog.classify_flat(assessment)[section]
    for criterion in catalog.section(section):
        answer = answers.get(criterion.id, {})
        status = answer.get("status")
        if not isinstance(status, str) or status not in _PROPOSABLE_STATUSES:
            skipped_unknown.append(criterion.id)
            continue
        justification = _justification_text(answer.get("justification"))

        live_status = _live_value(live, criterion, "status")
        if isinstance(live_status, str) and live_status.strip() == status:
            live_justification = _justification_text(
                _live_value(live, criterion, "justification")
            )
            if "justification" not in answer or justification == live_justification:
                dropped_no_op.append(criterion.id)
                continue
            if live_justification.strip() and not overrides:
                dropped_justification_only.append(criterion.id)
                continue

        pairs = [(f"{criterion.id}_status", status)]
        if "justification" in answer:
            pairs.append((f"{criterion.id}_justification", justification))
        criterion_pairs.append((criterion.id, pairs))

    urls: list[str] = []
    batch: list[tuple[str, str]] = []

    def flush() -> None:
        if batch:
            urls.append(prefix + urlencode(common + batch))
            batch.clear()

    for criterion_id, pairs in criterion_pairs:
        alone = prefix + urlencode(common + pairs)
        if len(alone.encode("utf-8")) > max_url_bytes:
            # Never emit an oversize URL: the coupled pair cannot be split,
            # so the justification must shrink or travel by fill script.
            oversize.append(criterion_id)
            continue
        candidate = prefix + urlencode(common + batch + pairs)
        if batch and len(candidate.encode("utf-8")) > max_url_bytes:
            flush()
        batch.extend(pairs)
        proposed.append(criterion_id)
    flush()

    return ProposalPlan(
        urls=tuple(urls),
        proposed=tuple(proposed),
        skipped_unknown=tuple(skipped_unknown),
        dropped_no_op=tuple(dropped_no_op),
        dropped_justification_only=tuple(dropped_justification_only),
        oversize=tuple(oversize),
    )


def build_fill_script(
    assessment: Mapping[str, Any],
    catalog: CriteriaCatalog,
    *,
    section: str,
    criteria: Sequence[str] | None = None,
) -> tuple[str, tuple[str, ...]]:
    """Emit a console script that fills the edit form without saving it.

    The script targets the project EDIT page for *section*, sets each status
    radio and justification textarea, dispatches change/input events so the
    live percentage updates, and returns a JSON report
    ``{filled, missingStatus, missingJustification}``. Saving remains a
    deliberate, human action; the script has no submit behavior.

    When *criteria* is given, only those criterion ids are emitted; the
    write's blast radius is exactly the requested subset. ``None`` means
    every answered criterion in the section.
    """

    selected = None if criteria is None else set(criteria)
    answers: dict[str, dict[str, str]] = {}
    for criterion, answer in _section_answers(assessment, catalog, section):
        if selected is not None and criterion.id not in selected:
            continue
        status = answer.get("status")
        if not isinstance(status, str) or status not in _PROPOSABLE_STATUSES:
            continue
        answers[criterion.id] = {"status": status}
        if "justification" in answer:
            answers[criterion.id]["justification"] = _justification_text(
                answer["justification"]
            )

    payload = json.dumps(answers, indent=2, ensure_ascii=False, sort_keys=True)
    script = (
        "(() => {\n"
        f"  const answers = {payload};\n"
        "  const report = { filled: [], missingStatus: [],"
        " missingJustification: [] };\n"
        "  const fire = (el, type) =>"
        " el.dispatchEvent(new Event(type, { bubbles: true }));\n"
        "  for (const [cid, a] of Object.entries(answers)) {\n"
        "    const radios = document.querySelectorAll(\n"
        "      `input[type=radio][name=\"project[${cid}_status]\"]`);\n"
        "    let hit = false;\n"
        "    for (const r of radios) {\n"
        "      if (r.value === a.status ||\n"
        "          r.value.toLowerCase() === a.status.toLowerCase()) {\n"
        "        r.checked = true; fire(r, 'click'); fire(r, 'change');"
        " hit = true;\n"
        "      }\n"
        "    }\n"
        "    if (hit) report.filled.push(cid);\n"
        "    else report.missingStatus.push(`${cid}=${a.status}`);\n"
        "    if (!Object.hasOwn(a, 'justification')) continue;\n"
        "    const ta = document.querySelector(\n"
        "      `textarea[name=\"project[${cid}_justification]\"]`);\n"
        "    if (ta) { ta.value = a.justification; fire(ta, 'input');"
        " fire(ta, 'change'); }\n"
        "    else report.missingJustification.push(cid);\n"
        "  }\n"
        "  return report;\n"
        "})()\n"
    )
    return script, tuple(sorted(answers))
