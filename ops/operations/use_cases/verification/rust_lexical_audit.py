"""Shared, bounded Rust lexical triage; this is not a compiler or Rust AST.

Offsets and newlines are preserved when masking comments and literals. Only
plain ``cfg(test)`` and ``test`` attributes are classified as test items; feature
expressions, macro expansion, inferred traits and data flow require review.
AuthorityEffect: None.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterator

SKIP_DIRS = frozenset({".git", "target", "node_modules", "__pycache__"})
RAW_STRING = re.compile(r'(?:br|cr|r)(#*)"')
CHAR_LITERAL = re.compile(r"'(?:[^'\\\r\n]|\\(?:u\{[0-9a-fA-F_]+\}|x[0-9a-fA-F]{2}|[^\r\n]))'")
ENUM = re.compile(
    r"(?P<attrs>(?:#\s*\[[^\]]*\]\s*)*)(?P<decl>\b(?:pub(?:\s*\([^)]*\))?\s+)?enum\s+(?P<name>[A-Za-z_]\w*))"
)
DERIVE = re.compile(r"#\s*\[\s*derive\s*\(([^)]*)\)\s*\]")
TEST_ATTRIBUTE = re.compile(r"#\s*\[\s*(?:cfg\s*\(\s*test\s*\)|test)\s*\]")


def rust_files(root: Path) -> list[Path]:
    """Enumerate deterministically, pruning caches, and never accept a bad root."""
    if root.is_file():
        if root.suffix != ".rs":
            raise ValueError(f"Expected a Rust file or directory: {root}")
        return [root]
    if not root.is_dir():
        raise ValueError(f"Rust audit root does not exist or is not a directory: {root}")

    def on_error(error: OSError) -> None:
        raise error

    files = []
    for directory, dirs, names in os.walk(root, onerror=on_error, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
        files.extend(Path(directory) / name for name in sorted(names) if name.endswith(".rs"))
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def mask_non_code(text: str) -> str:
    """Blank nested comments and Rust strings/chars without consuming lifetimes."""
    output = list(text)
    length = len(text)
    index = 0

    def blank(start: int, end: int) -> None:
        for offset in range(start, end):
            if output[offset] not in "\r\n":
                output[offset] = " "

    while index < length:
        start = index
        if text.startswith("//", index):
            newline = text.find("\n", index)
            index = length if newline < 0 else newline
        elif text.startswith("/*", index):
            index += 2
            depth = 1
            while index < length and depth:
                if text.startswith("/*", index):
                    depth += 1
                    index += 2
                elif text.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
        else:
            raw = (
                RAW_STRING.match(text, index)
                if index == 0 or not (text[index - 1].isalnum() or text[index - 1] == "_")
                else None
            )
            if raw:
                end_token = '"' + raw.group(1)
                end = text.find(end_token, raw.end())
                index = length if end < 0 else end + len(end_token)
            elif text[index] == '"':
                index += 1
                while index < length:
                    if text[index] == "\\":
                        index = min(index + 2, length)
                    elif text[index] == '"':
                        index += 1
                        break
                    else:
                        index += 1
            elif text[index] == "'" and (char := CHAR_LITERAL.match(text, index)):
                index = char.end()
            else:
                index += 1
                continue
        blank(start, index)
    return "".join(output)


def enum_declarations(code: str) -> Iterator[dict]:
    """Yield declaration offsets and exact derive names, not substring matches."""
    for match in ENUM.finditer(code):
        attrs = match.group("attrs")
        traits = {
            trait.strip().split("::")[-1]
            for derive in DERIVE.finditer(attrs)
            for trait in derive.group(1).split(",")
            if trait.strip()
        }
        yield {
            "name": match.group("name"),
            "offset": match.start("decl"),
            "line": code.count("\n", 0, match.start("decl")) + 1,
            "public": match.group("decl").startswith("pub"),
            "derives": attrs.strip(),
            "traits": traits,
        }


def test_item_spans(code: str) -> list[tuple[int, int]]:
    """Find brace-scoped simple test items in already masked source."""
    spans = []
    for attribute in TEST_ATTRIBUTE.finditer(code):
        index = attribute.end()
        # Skip further attributes, whose bracket contents may contain braces.
        while True:
            while index < len(code) and code[index].isspace():
                index += 1
            if not re.match(r"#\s*\[", code[index:]):
                break
            index = code.index("[", index) + 1
            depth = 1
            while index < len(code) and depth:
                depth += (code[index] == "[") - (code[index] == "]")
                index += 1
        parens = brackets = 0
        while index < len(code):
            char = code[index]
            if char == "(":
                parens += 1
            elif char == ")":
                parens -= 1
            elif char == "[":
                brackets += 1
            elif char == "]":
                brackets -= 1
            elif char == ";" and parens == brackets == 0:
                spans.append((attribute.start(), index + 1))
                break
            elif char == "{" and parens == brackets == 0:
                depth = 1
                index += 1
                while index < len(code) and depth:
                    depth += (code[index] == "{") - (code[index] == "}")
                    index += 1
                spans.append((attribute.start(), index))
                break
            index += 1
    return spans


def in_test_span(offset: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= offset < end for start, end in spans)
