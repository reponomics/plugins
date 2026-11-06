"""Spec-pinned expectations for the bundled Best Practices criteria.

These totals come from the upstream commit recorded in THIRD_PARTY_NOTICES.md,
not from the generated JSON under test. `make check-criteria` independently
verifies the bundle against an upstream clone; update the totals when its pin
changes.
"""

from __future__ import annotations


EXPECTED_SECTION_TOTALS: dict[str, int] = {
    "passing": 67,
    "silver": 55,
    "gold": 23,
    "baseline-1": 24,
    "baseline-2": 19,
    "baseline-3": 21,
}
