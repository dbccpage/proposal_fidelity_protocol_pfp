"""Pure text, section, and locator operations for governance repairs."""

from __future__ import annotations

import hashlib
from typing import Iterable, Sequence

from ...domain.governance_digest.records import EditLocator

_MODES = frozenset({"replace", "insert_before", "insert_after"})


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def line_spans(text: str) -> list[tuple[int, int, str]]:
    """Each line as (start, end_exclusive, content_without_newline)."""
    spans: list[tuple[int, int, str]] = []
    start = 0
    length = len(text)
    while start <= length:
        end = text.find("\n", start)
        if end == -1:
            if start < length or not spans:
                spans.append((start, length, text[start:length]))
            break
        spans.append((start, end + 1, text[start:end]))
        start = end + 1
        if start == length:
            break
    return spans


def _heading_rank(content: str) -> int:
    rank = 0
    for ch in content:
        if ch == "#":
            rank += 1
        else:
            break
    if rank == 0 or rank > 6 or not content[rank:rank + 1].isspace():
        return 0
    return rank


def section_slice(text: str, section_id: str) -> str | None:
    """Bytes from the heading that contains ``section_id`` up to the next heading of equal or higher rank."""
    spans = line_spans(text)
    start_i = None
    rank = 0
    for index, (_, _, content) in enumerate(spans):
        level = _heading_rank(content)
        if level and section_id in content:
            start_i = index
            rank = level
            break
    if start_i is None:
        return None
    end_offset = len(text)
    for index in range(start_i + 1, len(spans)):
        level = _heading_rank(spans[index][2])
        if level and level <= rank:
            end_offset = spans[index][0]
            break
    return text[spans[start_i][0] : end_offset]


def table_block(text: str) -> str | None:
    """The first pipe-table whose rows mention an anti-pattern column."""
    lines = text.splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("|"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    for block in blocks:
        joined = "\n".join(block)
        if "Anti-Pattern" in joined or "anti-pattern" in joined.lower():
            return joined + "\n"
    return None


def pattern_id_in_table(table: str, pattern_id: str) -> bool:
    needle = f"`{pattern_id}`"
    for line in table.splitlines():
        if line.startswith("|") and needle in line:
            return True
    return False


def measure(text: str, *, edit_kind: str, target_section: str, locator: EditLocator, replacement_text: str) -> str:
    """Fingerprint of the span this repair watches. Distinct from the whole-file hash."""
    if edit_kind == "cite_pattern":
        section = section_slice(text, target_section)
        if section is None:
            return sha256_text("missing-section\n" + target_section)
        return sha256_text(section)
    if edit_kind == "insert_invariant":
        if locator.new_heading and locator.new_heading in text:
            section = section_slice(text, target_section)
            if section is None:
                return sha256_text("missing-new-section\n" + target_section)
            return sha256_text(section)
        if text.count(locator.anchor_text) == 1:
            return sha256_text("absent\n" + locator.anchor_text)
        return sha256_text("unlocated\n" + locator.anchor_text)
    if edit_kind == "skill_table_row":
        table = table_block(text)
        if table is None:
            return sha256_text("missing-table\n" + target_section)
        return sha256_text(table)
    if edit_kind == "replace_link":
        old_n = text.count(locator.old_text) if locator.old_text else 0
        new_n = text.count(replacement_text) if replacement_text else 0
        if old_n == 1 and new_n == 0:
            return sha256_text("pre\n" + locator.old_text)
        if old_n == 0 and new_n == 1:
            return sha256_text("post\n" + replacement_text)
        return sha256_text(f"drift\n{old_n}\n{new_n}\n" + locator.old_text)
    return sha256_text("unknown-kind\n" + edit_kind)


def locator_span(text: str, locator: EditLocator, replacement_text: str) -> tuple[int, int] | str:
    """Half-open range on ``text`` that the edit occupies. A string is an unapplied reason."""
    if locator.mode not in _MODES:
        return "unknown_locator"
    if locator.mode == "replace":
        if not locator.old_text:
            return "missing_locator"
        count = text.count(locator.old_text)
        if count != 1:
            return "ambiguous_locator" if count else "missing_locator"
        start = text.find(locator.old_text)
        return start, start + len(locator.old_text)
    if not locator.anchor_text:
        return "missing_locator"
    count = text.count(locator.anchor_text)
    if count != 1:
        return "ambiguous_locator" if count else "missing_locator"
    if locator.new_heading and locator.new_heading in text:
        return "heading_already_present"
    start = text.find(locator.anchor_text)
    if locator.mode == "insert_before":
        return start, start
    return start + len(locator.anchor_text), start + len(locator.anchor_text)


def _overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    start, end = left
    other_start, other_end = right
    if start == end and other_start == other_end:
        return start == other_start
    if start == end:
        return other_start <= start < other_end
    if other_start == other_end:
        return start <= other_start < end
    return start < other_end and other_start < end


def ranges_conflict(ranges: Sequence[tuple[int, int]]) -> bool:
    ordered = list(ranges)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if _overlap(left, right):
                return True
    return False


def apply_edits(
    text: str, edits: Iterable[tuple[EditLocator, str]]
) -> tuple[str | None, str]:
    """Apply every edit to one snapshot. Overlap or a bad locator leaves the text unused."""
    materialized = list(edits)
    spans: list[tuple[int, int, str]] = []
    for locator, replacement in materialized:
        found = locator_span(text, locator, replacement)
        if isinstance(found, str):
            return None, found
        spans.append((found[0], found[1], replacement))
    if ranges_conflict([(start, end) for start, end, _ in spans]):
        return None, "conflicting_edits"
    pieces: list[str] = []
    cursor = 0
    for start, end, replacement in sorted(spans, key=lambda item: (item[0], item[1])):
        pieces.append(text[cursor:start])
        pieces.append(replacement)
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces), ""


