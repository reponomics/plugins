"""Source-pinned OpenSSF Best Practices criteria catalog.

The runtime deliberately reads a bundled JSON snapshot rather than parsing the
upstream YAML.  This keeps the review tools dependency-free while retaining the
criterion order and source text captured from the BadgeApp repository.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from .fields import normalize_assessment_fields


SECTION_NAMES = (
    "passing",
    "silver",
    "gold",
    "baseline-1",
    "baseline-2",
    "baseline-3",
)

_DEFAULT_ASSET = (
    Path(__file__).resolve().parents[2] / "assets" / "criteria" / "criteria.json"
)


@dataclass(frozen=True, slots=True)
class Criterion:
    """One criterion in its official section order."""

    id: str
    display_id: str
    category: str
    description: str
    details: str | None
    na_allowed: bool
    na_justification_required: bool
    met_justification_required: bool
    met_url_required: bool
    future: bool = False
    obsolete: bool = False

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "Criterion":
        criterion_id = _required_text(record, "id")
        category = _required_text(record, "category")
        if category not in {"MUST", "SHOULD", "SUGGESTED"}:
            raise ValueError(
                f"criterion {criterion_id!r} has invalid category {category!r}"
            )

        details = record.get("details")
        if details is not None and not isinstance(details, str):
            raise ValueError(f"criterion {criterion_id!r} has non-text details")

        return cls(
            id=criterion_id,
            display_id=_optional_text(record, "display_id") or criterion_id,
            category=category,
            description=_required_text(record, "description"),
            details=details,
            na_allowed=_boolean(record, "na_allowed"),
            na_justification_required=_boolean(record, "na_justification_required"),
            met_justification_required=_boolean(record, "met_justification_required"),
            met_url_required=_boolean(record, "met_url_required"),
            future=_boolean(record, "future"),
            obsolete=_boolean(record, "obsolete"),
        )


class CriteriaCatalog:
    """Ordered criteria plus helpers for flat ``.bestpractices.json`` data."""

    section_names = SECTION_NAMES

    def __init__(self, asset_path: str | Path | None = None) -> None:
        self.asset_path = Path(asset_path) if asset_path is not None else _DEFAULT_ASSET
        with self.asset_path.open(encoding="utf-8") as stream:
            payload = json.load(stream)

        if payload.get("schema_version") != 1:
            raise ValueError("unsupported criteria asset schema")
        sections = payload.get("sections")
        if not isinstance(sections, dict):
            raise ValueError("criteria asset has no sections object")

        self.source = payload.get("source", {})
        self._sections: dict[str, tuple[Criterion, ...]] = {}
        self._by_id: dict[str, list[tuple[str, Criterion]]] = {}
        self._field_index: dict[str, list[tuple[str, str, str]]] = {}

        for section_name in SECTION_NAMES:
            records = sections.get(section_name)
            if not isinstance(records, list):
                raise ValueError(f"criteria asset is missing section {section_name!r}")
            criteria = tuple(Criterion.from_record(record) for record in records)
            self._sections[section_name] = criteria
            for criterion in criteria:
                self._register(section_name, criterion)

        unexpected = set(sections).difference(SECTION_NAMES)
        if unexpected:
            names = ", ".join(sorted(unexpected))
            raise ValueError(f"criteria asset has unexpected sections: {names}")

    def _register(self, section: str, criterion: Criterion) -> None:
        for alias in {criterion.id, criterion.display_id}:
            targets = self._by_id.setdefault(alias, [])
            targets.append((section, criterion))
            self._field_index.setdefault(f"{alias}_status", []).append(
                (section, criterion.id, "status")
            )
            self._field_index.setdefault(f"{alias}_justification", []).append(
                (section, criterion.id, "justification")
            )

    def section(self, name: str) -> tuple[Criterion, ...]:
        """Return a section in the order defined by the authoritative source."""

        try:
            return self._sections[name]
        except KeyError as exc:
            choices = ", ".join(SECTION_NAMES)
            raise KeyError(
                f"unknown criteria section {name!r}; choose {choices}"
            ) from exc

    def get_criteria(self, name: str) -> tuple[Criterion, ...]:
        """Compatibility alias for :meth:`section`."""

        return self.section(name)

    def list_criteria(self, name: str) -> tuple[Criterion, ...]:
        """Compatibility alias for :meth:`section`."""

        return self.section(name)

    def get(self, criterion_id: str, section: str | None = None) -> Criterion:
        """Look up a criterion by ID, optionally disambiguating its section.

        Some metal criteria recur at higher badge levels.  An unqualified lookup
        of such an ID is ambiguous and therefore rejected rather than silently
        choosing one level's category or wording.
        """

        try:
            matches = self._by_id[criterion_id]
        except KeyError as exc:
            raise KeyError(f"unknown criterion {criterion_id!r}") from exc
        if section is not None:
            for candidate_section, criterion in matches:
                if candidate_section == section:
                    return criterion
            raise KeyError(f"criterion {criterion_id!r} is not in section {section!r}")
        if len(matches) != 1:
            choices = ", ".join(candidate_section for candidate_section, _ in matches)
            raise KeyError(
                f"criterion {criterion_id!r} occurs in multiple sections: {choices}"
            )
        return matches[0][1]

    def classify_flat(
        self, document: Mapping[str, Any]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Bucket recognized flat response fields by criteria section.

        Unrelated project metadata is ignored.  Only criteria represented in the
        input are added to a section bucket; callers that need a complete review
        can iterate :meth:`section` and treat missing answers as unresolved.
        Baseline fields are accepted in either internal underscore form or their
        public ``OSPS-XX-00.00`` display form.
        """

        if not isinstance(document, Mapping):
            raise TypeError("flat criteria data must be a mapping")

        buckets: dict[str, dict[str, dict[str, Any]]] = {
            name: {} for name in SECTION_NAMES
        }
        for field_name, value in normalize_assessment_fields(document).items():
            targets = self._field_index.get(field_name)
            if targets is None:
                continue
            for section, criterion_id, response_field in targets:
                answer = buckets[section].setdefault(criterion_id, {})
                answer[response_field] = value
        return buckets

    def bucket_flat(
        self, document: Mapping[str, Any]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Compatibility alias for :meth:`classify_flat`."""

        return self.classify_flat(document)


def _required_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"criterion record has invalid {field!r}")
    return value


def _optional_text(record: Mapping[str, Any], field: str) -> str | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"criterion record has invalid {field!r}")
    return value


def _boolean(record: Mapping[str, Any], field: str) -> bool:
    value = record.get(field, False)
    if not isinstance(value, bool):
        raise ValueError(f"criterion record has non-boolean {field!r}")
    return value
