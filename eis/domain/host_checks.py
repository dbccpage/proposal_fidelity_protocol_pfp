"""Pure host checks over a candidate payload.

These checks read the payload only. They never read a detector's matches, which
is what lets a sensor built on them supply a Signal 2 that is independent of
Signal 1 (see `danger_signals`).

- `strict_json` parses the payload as strict JSON: duplicate keys and
  non-finite numbers are refused, like any other syntax error. The refusal
  carries the character span of the fault (the syntax error position, the
  duplicate key, or the non-finite constant).
- `protected_field_spans` gives the character span of every host-only key
  token, found by a small JSON lexer over the raw text, so a Signal 1 match on
  the same token can be refused as the same evidence counted twice.
- `protected_field_loci` lists every key that only the host may fill: the
  functional values (phi, gamma, xi), verdict labels (verified, certified) and
  the authority label. Keys are compared after lower-casing and removing
  underscores, the normalisation used by
  `pfp.domain.demos.refuse_model_functionals`, which raises
  on the first such key; this check reports all of them.
- `persona_authority_leak_loci` is the Python-only PERSONA_AUTHORITY_LEAK
  check. The native pharmacy (`core_prompt_civilization::pharmacy`) does not
  implement it, so it is kept here as a separately named check: a string that
  names an unauthorised persona (for example "system administrator") while no
  granted role name appears in the same string. Matching uses Python's Unicode
  `str.lower`.
"""

from __future__ import annotations

import json
from typing import Any

from eis.domain.definitions_loader import (
    load_screening_vocabulary,
)

_vocab = load_screening_vocabulary()

PROTECTED_FIELD_KEYS = frozenset(_vocab["protected_field_keys"])

UNAUTHORIZED_PERSONA_MARKERS: tuple[str, ...] = tuple(_vocab["unauthorized_persona_markers"])


class MalformedPayload(ValueError):
    """The payload is not strict JSON. `spans` locate the fault in the text."""

    code = "MALFORMED_PAYLOAD"

    def __init__(self, detail: str, spans: tuple[tuple[int, int], ...] = ()) -> None:
        super().__init__(detail)
        self.detail = detail
        self.spans = spans


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MalformedPayload(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise MalformedPayload(f"non-finite JSON number {value}")


_PUNCTUATION = frozenset("{}[]:,")
_NON_FINITE = frozenset({"NaN", "Infinity", "-Infinity"})


def _tokens(content: str) -> list[tuple[str, int, int]]:
    """(kind, start, end) lexical tokens: "str", "punct" or "lit"."""
    tokens: list[tuple[str, int, int]] = []
    index, size = 0, len(content)
    while index < size:
        char = content[index]
        if char in " \t\r\n":
            index += 1
        elif char == '"':
            cursor = index + 1
            while cursor < size and content[cursor] != '"':
                cursor += 2 if content[cursor] == "\\" else 1
            end = min(cursor + 1, size)
            tokens.append(("str", index, end))
            index = end
        elif char in _PUNCTUATION:
            tokens.append(("punct", index, index + 1))
            index += 1
        else:
            cursor = index
            while cursor < size and content[cursor] not in _PUNCTUATION and content[cursor] not in ' "\t\r\n':
                cursor += 1
            tokens.append(("lit", index, cursor))
            index = cursor
    return tokens


def _key_tokens(content: str) -> list[tuple[str | None, int, int, int]]:
    """(decoded key or None, start, end, object depth id) for every object key token."""
    tokens = _tokens(content)
    keys: list[tuple[str | None, int, int, int]] = []
    stack: list[int] = []
    objects = 0
    for position, (kind, start, end) in enumerate(tokens):
        if kind == "punct":
            char = content[start]
            if char in "{[":
                objects += 1
                stack.append(objects if char == "{" else -objects)
            elif char in "}]" and stack:
                stack.pop()
            continue
        if kind != "str" or not stack or stack[-1] < 0:
            continue
        following = tokens[position + 1] if position + 1 < len(tokens) else None
        if following is None or following[0] != "punct" or content[following[1]] != ":":
            continue
        try:
            key = json.loads(content[start:end])
        except json.JSONDecodeError:
            key = None
        keys.append((key if type(key) is str else None, start, end, stack[-1]))
    return keys


def _fault_spans(content: str) -> tuple[tuple[int, int], ...]:
    """Spans of duplicate keys and non-finite constants in otherwise lexable JSON."""
    spans: list[tuple[int, int]] = []
    seen: set[tuple[int, str]] = set()
    for key, start, end, owner in _key_tokens(content):
        if key is None:
            continue
        if (owner, key) in seen:
            spans.append((start, end))
        seen.add((owner, key))
    for kind, start, end in _tokens(content):
        if kind == "lit" and content[start:end] in _NON_FINITE:
            spans.append((start, end))
    return tuple(sorted(spans))


def strict_json(content: str) -> Any:
    """Parse strict JSON or raise `MalformedPayload` with the fault's span."""
    if type(content) is not str:
        raise TypeError("content must be an exact str")
    try:
        return json.loads(content, object_pairs_hook=_pairs, parse_constant=_constant)
    except MalformedPayload as exc:
        raise MalformedPayload(exc.detail, _fault_spans(content)) from exc
    except json.JSONDecodeError as exc:
        spans: tuple[tuple[int, int], ...] = ()
        if content:
            position = min(max(exc.pos, 0), len(content) - 1)
            spans = ((position, position + 1),)
        raise MalformedPayload(str(exc), spans) from exc


def _normalised(key: str) -> str:
    return key.lower().replace("_", "")


def protected_field_spans(content: str) -> tuple[tuple[int, int], ...]:
    """Character spans of every host-only key token (quotes included) in strict JSON text."""
    if type(content) is not str:
        raise TypeError("content must be an exact str")
    return tuple(
        (start, end)
        for key, start, end, _owner in _key_tokens(content)
        if key is not None and _normalised(key) in PROTECTED_FIELD_KEYS
    )


def protected_field_loci(value: Any, path: str = "") -> tuple[str, ...]:
    """JSON-pointer paths of every host-only key in a parsed payload."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            here = f"{path}/{key}"
            if _normalised(str(key)) in PROTECTED_FIELD_KEYS:
                found.append(here)
            found.extend(protected_field_loci(item, here))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(protected_field_loci(item, f"{path}/{index}"))
    return tuple(found)


def _strings(value: Any, path: str, out: list[tuple[str, str]]) -> None:
    if isinstance(value, str):
        out.append((path, value))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _strings(item, f"{path}/{index}", out)
    elif isinstance(value, dict):
        for key, item in value.items():
            _strings(item, f"{path}/{key}", out)


def persona_authority_leak_loci(
    candidate: Any, granted_persona_roles: tuple[str, ...]
) -> tuple[str, ...]:
    """Paths of strings naming an unauthorised persona with no granted role present."""
    if type(granted_persona_roles) is not tuple or any(
        type(role) is not str for role in granted_persona_roles
    ):
        raise TypeError("granted_persona_roles must be a tuple of str")
    strings: list[tuple[str, str]] = []
    _strings(candidate, "", strings)
    loci = []
    for path, text in strings:
        lower = text.lower()
        if any(marker in lower for marker in UNAUTHORIZED_PERSONA_MARKERS) and not any(
            role in lower for role in granted_persona_roles
        ):
            loci.append(path)
    return tuple(loci)


__all__ = [
    "MalformedPayload",
    "PROTECTED_FIELD_KEYS",
    "UNAUTHORIZED_PERSONA_MARKERS",
    "persona_authority_leak_loci",
    "protected_field_loci",
    "protected_field_spans",
    "strict_json",
]
