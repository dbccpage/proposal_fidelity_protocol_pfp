"""Closed field sets, checked at every depth.

AuthorityEffect: None.

A spec is one of:

- a scalar tag: ``"str"``, ``"int"``, ``"bool"``, ``"digest"``, ``"commit"``,
  ``"rational"`` or ``"any"`` (any canonical JSON value; used for payloads);
- ``Enum(values)``, ``ListOf(spec)``, ``Nullable(spec)``;
- ``Obj(fields, optional)``: a closed object. Every key must be declared, and
  every non-optional key must be present.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

from .canonical import COMMIT_RE, DIGEST_RE, is_canonical_rational


@dataclass(frozen=True)
class Enum:
    values: frozenset[str]


@dataclass(frozen=True)
class ListOf:
    item: "Spec"
    min_len: int = 0


@dataclass(frozen=True)
class Nullable:
    inner: "Spec"


@dataclass(frozen=True)
class Obj:
    fields: dict[str, "Spec"]
    optional: frozenset[str] = field(default_factory=frozenset)


Spec = Union[str, Enum, ListOf, Nullable, Obj]


class SchemaError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


# Codes used for the three schema failure kinds; callers may remap them.
UNKNOWN = "RR-UNKNOWN-FIELD"
SCHEMA = "RR-SCHEMA"
PIN = "RR-PIN"


def validate(value: Any, spec: Spec, path: str = "$", codes: dict[str, str] | None = None) -> None:
    """Raise ``SchemaError`` at the first departure from ``spec``."""
    names = {"unknown": UNKNOWN, "schema": SCHEMA, "pin": PIN}
    if codes:
        names.update(codes)

    def fail(kind: str, detail: str) -> None:
        raise SchemaError(names[kind], f"{detail} at {path}")

    if isinstance(spec, Nullable):
        if value is None:
            return
        validate(value, spec.inner, path, codes)
        return
    if isinstance(spec, Enum):
        if not isinstance(value, str) or value not in spec.values:
            fail("schema", f"value {value!r} not in {sorted(spec.values)}")
        return
    if isinstance(spec, ListOf):
        if not isinstance(value, list):
            fail("schema", "expected a list")
        if len(value) < spec.min_len:
            fail("schema", f"expected at least {spec.min_len} items")
        for index, item in enumerate(value):
            validate(item, spec.item, f"{path}[{index}]", codes)
        return
    if isinstance(spec, Obj):
        if not isinstance(value, dict):
            fail("schema", "expected an object")
        for key in sorted(value):
            if key not in spec.fields:
                raise SchemaError(names["unknown"], f"undeclared field {key!r} at {path}")
        for key in sorted(spec.fields):
            if key not in value:
                if key in spec.optional:
                    continue
                raise SchemaError(names["schema"], f"missing field {key!r} at {path}")
            validate(value[key], spec.fields[key], f"{path}.{key}", codes)
        return
    if spec == "any":
        return
    if spec == "str":
        if not isinstance(value, str):
            fail("schema", "expected a string")
        return
    if spec == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            fail("schema", "expected an integer")
        return
    if spec == "bool":
        if not isinstance(value, bool):
            fail("schema", "expected a boolean")
        return
    if spec == "digest":
        if not isinstance(value, str) or not DIGEST_RE.match(value):
            fail("pin", f"malformed digest {value!r}")
        return
    if spec == "commit":
        if not isinstance(value, str) or not COMMIT_RE.match(value):
            fail("pin", f"malformed git id {value!r}")
        return
    if spec == "rational":
        if not isinstance(value, str) or not is_canonical_rational(value):
            fail("schema", f"expected a canonical num/den rational, got {value!r}")
        return
    raise AssertionError(f"unknown spec {spec!r}")
