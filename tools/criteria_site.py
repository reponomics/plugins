"""Extract and compare the criterion definitions visible in public app HTML.

Maintainer-only code. Project answers, result icons, and justifications are
deliberately outside the selected definition elements.
"""

from __future__ import annotations

import copy
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, Tag


BASE_URL = "https://www.bestpractices.dev"
SECTIONS = ("passing", "silver", "gold", "baseline-1", "baseline-2", "baseline-3")
VISIBLE_FIELDS = (
    "display_id", "description", "description_links", "details", "details_links",
    "na_allowed", "met_url_required", "future", "obsolete",
)
REPOSITORY_ONLY_FIELDS = ("category", "met_justification_required", "na_justification_required")
ID_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*")


def normalized_text(fragment: str | None) -> dict[str, Any]:
    """Compare readable text and link targets without incidental HTML styling."""
    soup = BeautifulSoup(fragment or "", "html.parser")
    for node in soup.find_all(string=lambda value: isinstance(value, Comment)):
        node.extract()
    for node in soup.select("script, style"):
        node.decompose()
    # Preserve word boundaries at block breaks without splitting inline words.
    for node in soup.find_all(["br", "p", "li", "div", "dt", "dd", "tr"]):
        node.insert_before(" ")
        node.insert_after(" ")
    return {
        "text": " ".join(soup.get_text().split()),
        "links": [
            {"text": " ".join(link.get_text().split()),
             "href": urljoin(BASE_URL + "/", str(link["href"]))}
            for link in soup.find_all("a", href=True)
        ],
    }


def _one(parent: Tag | BeautifulSoup, selector: str, context: str) -> Tag:
    found = parent.select(selector)
    if len(found) != 1:
        raise ValueError(f"{context}: expected one {selector}, found {len(found)}")
    return found[0]


def _description(row: Tag, criterion_id: str) -> dict[str, Any]:
    description = _one(row, ".criteria-desc", criterion_id)
    labels = description.find_all("sup", recursive=False)
    if len(labels) != 1:
        raise ValueError(f"{criterion_id}: expected one displayed criterion ID")
    label = labels[0]
    match = re.fullmatch(r"\[([^\[\]]+)\]", label.get_text(strip=True))
    if match is None:
        raise ValueError(f"{criterion_id}: invalid displayed ID")
    fragments = []
    for child in description.contents:
        if child is label:
            break
        fragments.append(str(child))
    normalized = normalized_text("".join(fragments))
    text = normalized["text"]
    future, obsolete = text.startswith("(Future criterion)"), text.startswith("(Obsolete criterion)")
    text = re.sub(r"^\((?:Future|Obsolete) criterion\)\s*", "", text)
    url_required = text.endswith("(URL required)")
    if url_required:
        text = text[:-len("(URL required)")].rstrip()
    if not text or "translation missing:" in text.lower():
        raise ValueError(f"{criterion_id}: missing criterion description")
    return {
        "display_id": match.group(1), "description": text,
        "description_links": normalized["links"], "met_url_required": url_required,
        "future": future, "obsolete": obsolete,
    }


def _details(row: Tag, criterion_id: str) -> dict[str, Any]:
    nodes = row.select(".criteria-desc .details-text")
    if len(nodes) > 1:
        raise ValueError(f"{criterion_id}: duplicate details blocks")
    fragment = nodes[0].decode_contents() if nodes else ""
    if nodes and nodes[0].get("id") != f"{criterion_id}_details_text":
        raise ValueError(f"{criterion_id}: details ID does not match")
    normalized = normalized_text(fragment)
    if "translation missing:" in normalized["text"].lower():
        raise ValueError(f"{criterion_id}: missing details translation")
    return {"details": normalized["text"], "details_links": normalized["links"]}


def parse_application(html: str) -> list[dict[str, Any]]:
    """Extract ordered definitions from an anonymous English project view."""
    # The app contains overlapping anchor/div markup. Use browser-compatible
    # HTML5 recovery so those closures cannot detach a description from its row.
    soup = BeautifulSoup(html, "html5lib")
    language = str(soup.html.get("lang", "")) if soup.html else ""
    if language != "en":
        raise ValueError("application snapshot must declare English (lang=en)")
    rows = soup.select(".criterion-data")
    if not rows:
        raise ValueError("application page contains no criteria")
    records = [_parse_row(row) for row in rows]
    identifiers = [record["id"] for record in records]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("application page contains duplicate criterion IDs")
    return records


def _parse_row(row: Tag) -> dict[str, Any]:
    criterion_id = str(row.get("id", ""))
    if ID_PATTERN.fullmatch(criterion_id) is None:
        raise ValueError(f"invalid application criterion ID: {criterion_id!r}")
    radios = row.select('.criteria-radio input[type="radio"]')
    names = {radio.get("name") for radio in radios}
    values = [radio.get("value") for radio in radios]
    if names != {f"project[{criterion_id}_status]"}:
        raise ValueError(f"{criterion_id}: response field names do not match")
    if not {"Met", "Unmet"}.issubset(values) or len(values) != len(set(values)):
        raise ValueError(f"{criterion_id}: missing or duplicate response options")
    if set(values) - {"Met", "Unmet", "N/A", "?"}:
        raise ValueError(f"{criterion_id}: unexpected response option")
    return {
        "id": criterion_id, **_description(row, criterion_id),
        **_details(row, criterion_id), "na_allowed": "N/A" in values,
    }


def visible_record(record: dict[str, Any]) -> dict[str, Any]:
    description = normalized_text(record["description"])
    details = normalized_text(record.get("details"))
    return {
        "id": record["id"], "display_id": record.get("display_id", record["id"]),
        "description": description["text"], "description_links": description["links"],
        "details": details["text"], "details_links": details["links"],
        **{field: record.get(field, False) for field in
           ("na_allowed", "met_url_required", "future", "obsolete")},
    }


def compare_sections(catalog: dict[str, Any], pages: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Return explicit differences, never merge or silently prefer a source."""
    if set(catalog["sections"]) != set(SECTIONS) or set(pages) != set(SECTIONS):
        raise ValueError("comparison requires all six sections")
    differences = []
    for section in SECTIONS:
        expected = [visible_record(record) for record in catalog["sections"][section]]
        differences.extend(_compare_section(section, expected, pages[section]))
    return differences


def _compare_section(section: str, expected: list[dict[str, Any]], observed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    differences = []
    expected_ids, observed_ids = [item["id"] for item in expected], [item["id"] for item in observed]
    if expected_ids != observed_ids:
        differences.append({"section": section, "field": "ids_and_order", "catalog": expected_ids, "website": observed_ids})
    by_id = {item["id"]: item for item in observed}
    for record in expected:
        actual = by_id.get(record["id"])
        if actual is None:
            continue
        differences.extend(
            {"section": section, "id": record["id"], "field": field,
             "catalog": copy.deepcopy(record[field]), "website": copy.deepcopy(actual[field])}
            for field in VISIBLE_FIELDS if record[field] != actual[field]
        )
    return differences
