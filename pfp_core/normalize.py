"""Deterministic Signal-1 normalization for candidate code (no model call).

A ``DIAGNOSTIC_OR_NORMALIZE`` disposition means a rule matched but no host
check failed. For formatting drift the host can often repair the candidate
itself, at zero model cost, if the repair provably does not change what the
code means. This module does that for Python source and nothing else.

Each step is applied only if it is value-preserving in a checkable sense:

* ``strip_bom``, ``crlf_to_lf``: byte-level, applied before parsing.
* ``unwrap_markdown_fence``: removes one outer ```` ```python ... ``` ````
  wrapper. The fence is not Python, so there is no AST to compare; the step is
  taken only when the original does not parse and the unwrapped body does.
* ``strip_trailing_whitespace``: taken only when the code parses both before
  and after and ``ast.dump`` is identical. Trailing spaces inside a
  triple-quoted string change its value, change the AST, and are refused.

What this is not: a patch repair, a semantic fix, or a diff canonicalizer.
The 2026-11-10 charpoly pilot refused on ``RATIONAL_NONCANONICAL`` and, after
the offline normalizer, still on ``NONMONIC_LEADING_COEFFICIENT``
(``dag/WORK_PRIORITY.md``): that failure is in the candidate's algebra, and no
formatting step can salvage it.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
import re

_FENCE = re.compile(r'\A\s*```[A-Za-z0-9_+-]*[ \t]*\n(?P<body>.*?)\n```[ \t]*\s*\Z', re.S)


@dataclass(frozen=True)
class Normalized:
    text: str
    steps: tuple[str, ...] = ()
    refused: tuple[str, ...] = field(default_factory=tuple)

    @property
    def parses(self) -> bool:
        return _parse(self.text) is not None


def _parse(text: str) -> ast.AST | None:
    try:
        return ast.parse(text)
    except (SyntaxError, ValueError):
        return None


def normalize_python(text: str) -> Normalized:
    """Apply the value-preserving steps above; return the text and what was done."""
    if not isinstance(text, str):
        raise TypeError('candidate text must be str')
    steps: list[str] = []
    refused: list[str] = []
    if text.startswith('﻿'):
        text = text[1:]
        steps.append('strip_bom')
    if '\r\n' in text or '\r' in text:
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        steps.append('crlf_to_lf')
    if _parse(text) is None:
        m = _FENCE.match(text)
        if m and _parse(m.group('body')) is not None:
            text = m.group('body') + '\n'
            steps.append('unwrap_markdown_fence')
    before = _parse(text)
    stripped = '\n'.join(line.rstrip(' \t') for line in text.split('\n'))
    if stripped != text:
        after = _parse(stripped)
        if before is not None and after is not None and ast.dump(before) == ast.dump(after):
            text = stripped
            steps.append('strip_trailing_whitespace')
        else:
            refused.append('NORMALIZATION_NOT_VALUE_PRESERVING:strip_trailing_whitespace')
    return Normalized(text, tuple(steps), tuple(refused))
