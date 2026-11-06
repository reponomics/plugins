"""Canonical names for flat assessment fields shared by all local operations."""

from collections.abc import Mapping
import re
from typing import Any


_DISPLAY_FIELD = re.compile(r"OSPS-([A-Z]+)-(\d+)\.(\d+)_(status|justification)")


def normalize_assessment_fields(document: Mapping[str, Any]) -> dict[str, Any]:
    """Collapse Baseline display aliases without silently choosing between answers.

    Equal aliases are harmless duplicates; conflicting aliases require the caller
    to resolve the input. Preserve all other fields and values, including metadata,
    unknown answers, and deliberately empty justifications.
    """
    normalized: dict[str, Any] = {}
    for field, value in document.items():
        if not isinstance(field, str):
            raise ValueError("assessment field names must be strings")
        match = _DISPLAY_FIELD.fullmatch(field)
        canonical = "osps_" + "_".join(match.groups()).lower() if match else field
        if canonical in normalized and normalized[canonical] != value:
            raise ValueError(
                f"conflicting aliases for {canonical}; resolve the assessment fields"
            )
        normalized[canonical] = value
    return normalized
