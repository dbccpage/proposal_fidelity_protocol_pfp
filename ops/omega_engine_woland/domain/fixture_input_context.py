"""Bounded, detached JSON input for scripted fixture carriers. AuthorityEffect: None."""

from __future__ import annotations

import json
import math
from typing import Any

MAX_FIXTURE_INPUT_CONTEXT_BYTES = 262_144
MAX_FIXTURE_INPUT_CONTEXT_DEPTH = 32


class FixtureInputContextError(ValueError):
    """The supplied fixture input cannot be retained without coercion."""

    code = "INVALID_FIXTURE_INPUT_CONTEXT"


class _ContextCopy:
    def __init__(self) -> None:
        self.remaining = MAX_FIXTURE_INPUT_CONTEXT_BYTES
        self.active: set[int] = set()

    def spend(self, size: int) -> None:
        self.remaining -= size
        if self.remaining < 0:
            raise FixtureInputContextError("fixture input context exceeds its JSON byte limit")

    def scalar(self, value: Any) -> Any:
        if type(value) is str and len(value) > self.remaining:
            raise FixtureInputContextError("fixture input context exceeds its JSON byte limit")
        if type(value) is int and value.bit_length() > self.remaining * 4:
            raise FixtureInputContextError("fixture input context exceeds its JSON byte limit")
        if type(value) is float and not math.isfinite(value):
            raise FixtureInputContextError("fixture input context requires finite JSON numbers")
        try:
            encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (ValueError, UnicodeError) as exc:
            raise FixtureInputContextError("fixture input context is not UTF-8 JSON encodable") from exc
        self.spend(len(encoded))
        return value

    def copy(self, value: Any, depth: int = 0) -> Any:
        if type(value) in (str, int, float, bool, type(None)):
            return self.scalar(value)
        if type(value) not in (dict, list):
            raise FixtureInputContextError("fixture input context requires exact JSON value types")
        if depth >= MAX_FIXTURE_INPUT_CONTEXT_DEPTH:
            raise FixtureInputContextError("fixture input context exceeds its nesting limit")
        if id(value) in self.active:
            raise FixtureInputContextError("fixture input context must not contain cycles")
        self.active.add(id(value))
        try:
            self.spend(2 + max(0, len(value) - 1))
            if type(value) is dict:
                return self.object(value, depth)
            return [self.copy(item, depth + 1) for item in value]
        finally:
            self.active.remove(id(value))

    def object(self, value: dict[str, Any], depth: int) -> dict[str, Any]:
        detached = {}
        for key, item in value.items():
            if type(key) is not str:
                raise FixtureInputContextError("fixture input context requires exact string keys")
            self.scalar(key)
            self.spend(1)
            detached[key] = self.copy(item, depth + 1)
        return detached


def detach_fixture_input_context(value: Any) -> dict[str, Any]:
    """Copy exact JSON; root counts as depth one and size is compact UTF-8 JSON."""
    if type(value) is not dict:
        raise FixtureInputContextError("fixture input context must be an exact JSON object")
    try:
        return _ContextCopy().copy(value)
    except RuntimeError as exc:
        raise FixtureInputContextError("fixture input context changed during validation") from exc
