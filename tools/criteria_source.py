"""Build a release candidate from a clean BadgeApp checkout (maintenance only).

Definitions and ordering come from criteria/*.yml; English descriptions and
shared details follow app/models/criteria.rb's locale lookup. Website agreement
is checked by the separate sync command before publishing this candidate.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
from typing import Any

import yaml

UPSTREAM_REPOSITORY = "https://github.com/ossf/best-practices-badge"
METAL_LEVELS = {"0": "passing", "1": "silver", "2": "gold"}
BASELINE_SECTIONS = ("baseline-1", "baseline-2", "baseline-3")
FLAG_FIELDS = (
    "na_allowed", "na_justification_required",
    "met_justification_required", "met_url_required",
)
LIFECYCLE_FIELDS = ("future", "obsolete")
INPUT_PATHS = (
    "criteria/criteria.yml", "criteria/baseline_criteria.yml", "config/locales/en.yml",
)


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys instead of silently losing definitions."""

    def construct_mapping(self, node: Any, deep: bool = False) -> dict:
        self.flatten_mapping(node)
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise ValueError(f"duplicate YAML key: {key!r}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return yaml.load(stream, Loader=UniqueKeyLoader)


def _pairs(node: Any) -> list[tuple[Any, Any]]:
    """Read ordinary mappings and ordered YAML maps without losing order."""
    if isinstance(node, dict):
        return list(node.items())
    if not isinstance(node, list):
        raise ValueError(f"expected mapping, got {type(node).__name__}")
    pairs = []
    seen = set()
    for item in node:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError(f"invalid ordered-map entry: {item!r}")
        key, value = item
        if key in seen:
            raise ValueError(f"duplicate YAML key: {key!r}")
        seen.add(key)
        pairs.append((key, value))
    return pairs


def _criterion_pairs(groups: Any):
    for _, subgroups in _pairs(groups):
        for _, criteria in _pairs(subgroups):
            yield from _pairs(criteria)


def _level_records(level: Any, groups: Any) -> dict[str, dict]:
    records = {}
    for criterion_id, meta in _criterion_pairs(groups):
        if not isinstance(criterion_id, str) or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_]*", criterion_id
        ):
            raise ValueError(f"invalid criterion ID: {criterion_id!r}")
        if criterion_id in records:
            raise ValueError(f"duplicate criterion {level}:{criterion_id}")
        if not isinstance(meta, dict):
            raise ValueError(f"invalid definition {level}:{criterion_id}")
        records[criterion_id] = meta
    if not records:
        raise ValueError(f"empty criteria level: {level}")
    return records


def _definitions(document: Any) -> dict[str, dict[str, dict]]:
    levels = {}
    for level, groups in _pairs(document):
        if level == "_metadata":
            continue
        if str(level) in levels:
            raise ValueError(f"duplicate normalized level: {level!r}")
        levels[str(level)] = _level_records(level, groups)
    return levels


def _text(value: Any, context: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{context}: expected text")
    return value.strip() or None


def _boolean(meta: dict, field: str, context: str) -> bool:
    value = meta.get(field, False)
    if type(value) is not bool:
        raise ValueError(f"{context}: {field} must be a boolean")
    return value


def _level_number(level: str) -> int:
    return int(level.removeprefix("baseline-"))


def _locale_fields(locale: dict, level: str, criterion_id: str) -> dict:
    level_text = locale.get(level, {})
    if not isinstance(level_text, dict):
        raise ValueError(f"{level}: invalid locale criteria mapping")
    fields = level_text.get(criterion_id, {})
    if not isinstance(fields, dict):
        raise ValueError(f"{level}:{criterion_id}: invalid locale fields")
    return fields


def _details(level: str, criterion_id: str, levels: dict, locale: dict) -> str | None:
    # Criteria#get_text_if_exists searches the reversed definition-level list,
    # skipping levels above the current one. Only levels defining the criterion
    # participate, and an existing empty translation stops the search.
    for candidate, definitions in reversed(list(levels.items())):
        if criterion_id not in definitions or _level_number(candidate) > _level_number(level):
            continue
        fields = _locale_fields(locale, candidate, criterion_id)
        if fields.get("details") is not None:
            return _text(fields["details"], f"{candidate}:{criterion_id}:details")
    return None


def _display_id(criterion_id: str, meta: dict) -> str:
    parts = criterion_id.split("_")
    if len(parts) != 4 or parts[0] != "osps":
        raise ValueError(f"unexpected Baseline ID: {criterion_id}")
    computed = f"OSPS-{parts[1].upper()}-{parts[2]}.{parts[3]}"
    original = _text(meta.get("original_id"), f"{criterion_id}:original_id")
    if original != computed:
        raise ValueError(f"{criterion_id}: original_id disagrees with application display ID")
    return original


def _record(level: str, criterion_id: str, meta: dict, levels: dict, locale: dict) -> dict:
    context = f"{level}:{criterion_id}"
    category = meta.get("category")
    if not isinstance(category, str) or category not in {"MUST", "SHOULD", "SUGGESTED"}:
        raise ValueError(f"{context}: invalid category {category!r}")
    fields = _locale_fields(locale, level, criterion_id)
    description = _text(fields.get("description"), context + ":description")
    if description is None:
        raise ValueError(f"{context}: no locale description at this level")
    record = {"id": criterion_id}
    if level in BASELINE_SECTIONS:
        record["display_id"] = _display_id(criterion_id, meta)
    record.update(category=category, description=description,
                  details=_details(level, criterion_id, levels, locale))
    for field in FLAG_FIELDS:
        record[field] = _boolean(meta, field, context)
    # The public application renders these entries in place, with lifecycle
    # labels. Keep their order, and preserve active-state metadata when present.
    for field in LIFECYCLE_FIELDS:
        if _boolean(meta, field, context):
            record[field] = True
    return record


def _clean_commit(badge_repo: Path) -> str:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(badge_repo), *args], check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    commit = git("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("expected a full upstream commit ID")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("upstream checkout has tracked changes; use a clean checkout")
    for relative in INPUT_PATHS:
        git("ls-files", "--error-unmatch", "--", relative)
        path = badge_repo / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"expected regular tracked source file: {relative}")
        if git("hash-object", "--", relative) != git("rev-parse", f"HEAD:{relative}"):
            raise ValueError(f"upstream source differs from HEAD: {relative}")
    return commit


def build_catalog(badge_repo: Path) -> dict[str, Any]:
    """Return a validated candidate with the exact commit of its source inputs."""
    badge_repo = badge_repo.resolve()
    commit = _clean_commit(badge_repo)
    metal = _definitions(_load(badge_repo / INPUT_PATHS[0]))
    baseline = _definitions(_load(badge_repo / INPUT_PATHS[1]))
    if set(metal) != set(METAL_LEVELS) or set(baseline) != set(BASELINE_SECTIONS):
        raise ValueError("expected exactly three Metal and three Baseline levels")
    levels = metal | baseline
    document = _load(badge_repo / INPUT_PATHS[2])
    if not isinstance(document, dict) or not isinstance(document.get("en"), dict):
        raise ValueError("expected an English locale mapping")
    locale = document["en"].get("criteria")
    if not isinstance(locale, dict):
        raise ValueError("expected English criteria translations")
    sections = {}
    for level, records in levels.items():
        section = METAL_LEVELS.get(level, level)
        sections[section] = [
            _record(level, criterion_id, meta, levels, locale)
            for criterion_id, meta in records.items()
        ]
    if _clean_commit(badge_repo) != commit:
        raise ValueError("upstream checkout changed during catalog generation")
    return {
        "schema_version": 1,
        "source": {"repository": UPSTREAM_REPOSITORY, "commit": commit},
        "sections": sections,
    }
