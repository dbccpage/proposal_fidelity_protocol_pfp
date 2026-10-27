"""Strict canonical encoding and domain-separated digests for lab artifacts.

Pure Domain implementation with zero external infrastructure dependencies.
AuthorityEffect: None.
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from ..exceptions import CanonicalizationError

# Typed wire marker. Not an RFC 8785 / JCS format name.
CANONICAL_MARKER = "core-canonical-v1"


@dataclass(frozen=True, slots=True)
class _FrozenValue:
    """Internal tagged value that cannot collide with a user sequence."""

    tag: str
    items: tuple[Any, ...]


_COMPOUND_TAGS = frozenset(
    {
        "bytes",
        "dataclass",
        "entry",
        "enum",
        "field",
        "float",
        "fraction",
        "frozenset",
        "list",
        "mapping",
        "set",
        "tuple",
    }
)


def _declared_slots(cls: type[Any]) -> frozenset[str]:
    names: set[str] = set()
    for base in cls.__mro__:
        slots = base.__dict__.get("__slots__", ())
        if isinstance(slots, str):
            names.add(slots)
        else:
            names.update(slots)
    return frozenset(names)


def _validate_enum_instance(value: enum.Enum) -> None:
    state = getattr(value, "__dict__", None)
    expected_keys = {"_value_", "_name_", "__objclass__", "_sort_order_"}
    if type(state) is not dict or set(state) != expected_keys:
        raise CanonicalizationError(
            "enum members with undeclared instance state are not canonical"
        )
    if (
        state["_value_"] is not value.value
        or state["_name_"] != value.name
        or state["__objclass__"] is not type(value)
        or type(state["_sort_order_"]) is not int
    ):
        raise CanonicalizationError("enum bookkeeping state is inconsistent")
    canonical_members = list(type(value))
    if value not in canonical_members or state[
        "_sort_order_"
    ] != canonical_members.index(value):
        raise CanonicalizationError("enum sort order is not canonical")
    allowed_slots = expected_keys | {"__dict__", "__weakref__"}
    if any(
        slot not in allowed_slots and hasattr(value, slot)
        for slot in _declared_slots(type(value))
    ):
        raise CanonicalizationError(
            "enum members with undeclared slot state are not canonical"
        )


def _validate_dataclass_instance(value: Any) -> tuple[dataclasses.Field[Any], ...]:
    fields = tuple(dataclasses.fields(value))
    declared_names = {field.name for field in fields}
    state = getattr(value, "__dict__", None)
    if state is not None and (
        type(state) is not dict or not set(state).issubset(declared_names)
    ):
        raise CanonicalizationError("dataclass has undeclared instance attributes")
    allowed_slots = declared_names | {"__dict__", "__weakref__"}
    if any(
        slot not in allowed_slots and hasattr(value, slot)
        for slot in _declared_slots(type(value))
    ):
        raise CanonicalizationError("dataclass has undeclared slot attributes")
    return fields


def freeze(value: Any) -> Any:
    """Convert supported values to an immutable, deterministically ordered form.

    Unlike the older research packet helper, this function never falls back to
    ``str(value)``.  An unknown object therefore fails closed instead of gaining
    a process-dependent identity.
    """

    if type(value) is _FrozenValue:
        _validate_compound(value)
        return value
    if isinstance(value, _FrozenValue):
        raise CanonicalizationError("subclasses of the frozen wire node are refused")
    if isinstance(value, enum.Enum):
        _validate_enum_instance(value)
        return _FrozenValue(
            "enum",
            (
                type(value).__module__,
                type(value).__qualname__,
                value.name,
                freeze(value.value),
            ),
        )
    if value is None or type(value) in {str, bool, int}:
        return value
    if type(value) is float:
        raise CanonicalizationError(
            "float values are forbidden in exact rational arithmetic"
        )
    if type(value) is Fraction:
        return _FrozenValue("fraction", (value.numerator, value.denominator))
    if type(value) is bytes:
        return _FrozenValue("bytes", (value.hex(),))
    exact_builtin_families = (
        str,
        bool,
        int,
        float,
        bytes,
        list,
        tuple,
        set,
        frozenset,
        dict,
        Fraction,
    )
    if (
        isinstance(value, exact_builtin_families)
        and type(value) not in exact_builtin_families
    ):
        raise CanonicalizationError(
            f"subclasses of {type(value).__mro__[1].__qualname__} are refused"
        )
    if dataclasses.is_dataclass(value):
        fields = _validate_dataclass_instance(value)
        return _FrozenValue(
            "dataclass",
            (
                type(value).__module__,
                type(value).__qualname__,
                *(
                    _FrozenValue(
                        "field",
                        (field.name, freeze(getattr(value, field.name))),
                    )
                    for field in fields
                ),
            ),
        )
    if type(value) is dict:
        items: list[_FrozenValue] = []
        for key, item in value.items():
            if type(key) is not str:
                raise CanonicalizationError(
                    "canonical mapping keys must be exact strings"
                )
            items.append(_FrozenValue("entry", (key, freeze(item))))
        return _FrozenValue(
            "mapping",
            (
                type(value).__module__,
                type(value).__qualname__,
                *sorted(items, key=lambda entry: str(entry.items[0])),
            ),
        )
    if type(value) is list:
        return _FrozenValue("list", tuple(freeze(item) for item in value))
    if type(value) is tuple:
        return _FrozenValue("tuple", tuple(freeze(item) for item in value))
    if type(value) is set:
        frozen = [freeze(item) for item in value]
        return _FrozenValue(
            "set",
            tuple(sorted(frozen, key=lambda item: canonical_json(item))),
        )
    if type(value) is frozenset:
        frozen = [freeze(item) for item in value]
        return _FrozenValue(
            "frozenset",
            tuple(sorted(frozen, key=lambda item: canonical_json(item))),
        )
    raise CanonicalizationError(
        f"unsupported canonical value: {type(value).__module__}.{type(value).__qualname__}"
    )


def thaw(value: Any) -> Any:
    """Return a JSON-friendly view of a value produced by :func:`freeze`."""

    if not isinstance(value, _FrozenValue):
        return value
    if value.tag == "mapping":
        return {str(entry.items[0]): thaw(entry.items[1]) for entry in value.items[2:]}
    if value.tag == "list":
        return [thaw(item) for item in value.items]
    if value.tag == "tuple":
        return {"$tuple": [thaw(item) for item in value.items]}
    if value.tag == "set":
        return {"$set": [thaw(item) for item in value.items]}
    if value.tag == "frozenset":
        return {"$frozenset": [thaw(item) for item in value.items]}
    if value.tag == "float":
        return {"$float_hex": value.items[0]}
    if value.tag == "fraction":
        return {"$fraction": [value.items[0], value.items[1]]}
    if value.tag == "bytes":
        return {"$bytes_hex": value.items[0]}
    if value.tag == "enum":
        return {
            "$enum": [
                value.items[0],
                value.items[1],
                value.items[2],
                thaw(value.items[3]),
            ]
        }
    if value.tag == "field":
        return [value.items[0], thaw(value.items[1])]
    if value.tag == "entry":
        return [value.items[0], thaw(value.items[1])]
    if value.tag == "dataclass":
        return {
            "$dataclass": [value.items[0], value.items[1]],
            "fields": [thaw(item) for item in value.items[2:]],
        }
    raise CanonicalizationError(f"unknown frozen tag: {value.tag}")


def _wire(value: Any) -> Any:
    """Return an injectively tagged JSON tree for digest computation."""

    value = freeze(value)
    if isinstance(value, _FrozenValue):
        body = [_wire(item) for item in value.items]
        return [CANONICAL_MARKER, value.tag, body]
    if value is None:
        return [CANONICAL_MARKER, "null", None]
    if isinstance(value, bool):
        return [CANONICAL_MARKER, "bool", value]
    if isinstance(value, int):
        return [CANONICAL_MARKER, "int", str(value)]
    if isinstance(value, str):
        return [CANONICAL_MARKER, "string", value]
    raise CanonicalizationError("frozen value escaped the canonical type algebra")


def canonical_wire(value: Any) -> Any:
    """Return the injective JSON-native representation used by digests."""

    return _wire(value)


def _require_tagged_strings(
    value: _FrozenValue,
    count: int,
    label: str,
) -> None:
    if len(value.items) < count or any(
        not isinstance(item, str) or not item for item in value.items[:count]
    ):
        raise CanonicalizationError(f"canonical {label} identity is invalid")


def _validate_compound(value: _FrozenValue) -> None:
    """Require a compound node to be in the image of :func:`freeze`."""

    tag = value.tag
    items = value.items
    if tag in {"list", "tuple"}:
        return
    if tag in {"set", "frozenset"}:
        encodings = [canonical_json(item) for item in items]
        if encodings != sorted(encodings) or len(encodings) != len(set(encodings)):
            raise CanonicalizationError(
                f"canonical {tag} items must be unique and ordered"
            )
        return
    if tag == "float":
        raise CanonicalizationError(
            "float values are forbidden in exact rational arithmetic"
        )
    if tag == "fraction":
        if (
            len(items) != 2
            or type(items[0]) is not int
            or type(items[1]) is not int
            or items[1] <= 0
        ):
            raise CanonicalizationError("canonical fraction payload is invalid")
        normalized = Fraction(items[0], items[1])
        if (normalized.numerator, normalized.denominator) != items:
            raise CanonicalizationError("canonical fraction payload is not normalized")
        return
    if tag == "bytes":
        if len(items) != 1 or not isinstance(items[0], str):
            raise CanonicalizationError("canonical bytes payload is invalid")
        try:
            decoded = bytes.fromhex(items[0])
        except ValueError as exc:
            raise CanonicalizationError("canonical bytes payload is invalid") from exc
        if decoded.hex() != items[0]:
            raise CanonicalizationError("canonical bytes payload is not normalized")
        return
    if tag == "enum":
        if len(items) != 4:
            raise CanonicalizationError("canonical enum payload is invalid")
        _require_tagged_strings(value, 3, "enum")
        return
    if tag in {"field", "entry"}:
        if len(items) != 2 or not isinstance(items[0], str):
            raise CanonicalizationError(f"canonical {tag} payload is invalid")
        if tag == "field" and not items[0]:
            raise CanonicalizationError("canonical field name is invalid")
        return
    if tag == "dataclass":
        _require_tagged_strings(value, 2, "dataclass")
        fields = items[2:]
        if any(
            not isinstance(item, _FrozenValue) or item.tag != "field" for item in fields
        ):
            raise CanonicalizationError("canonical dataclass fields are invalid")
        names = [str(item.items[0]) for item in fields]
        if len(names) != len(set(names)):
            raise CanonicalizationError("canonical dataclass fields are duplicated")
        return
    if tag == "mapping":
        _require_tagged_strings(value, 2, "mapping")
        if items[:2] != ("builtins", "dict"):
            raise CanonicalizationError(
                "canonical mapping type must be the exact built-in dict"
            )
        entries = items[2:]
        if any(
            not isinstance(item, _FrozenValue) or item.tag != "entry"
            for item in entries
        ):
            raise CanonicalizationError("canonical mapping entries are invalid")
        keys = [str(item.items[0]) for item in entries]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise CanonicalizationError(
                "canonical mapping keys must be unique and ordered"
            )
        return
    raise CanonicalizationError(f"unknown frozen tag: {tag}")


def canonical_unwire(value: Any) -> Any:
    """Parse and validate a value produced by :func:`canonical_wire`.

    The parser accepts only the closed canonical type algebra.  In particular,
    an attacker cannot smuggle a new internal ``_FrozenValue`` tag through a
    packet transport and have it participate in identity computation.
    """

    if not isinstance(value, list) or len(value) != 3:
        raise CanonicalizationError("canonical wire node must be a three-item array")
    marker, tag, body = value
    if marker != CANONICAL_MARKER or not isinstance(tag, str):
        raise CanonicalizationError("canonical wire marker or tag is invalid")
    if tag == "null":
        if body is not None:
            raise CanonicalizationError("canonical null has a non-null body")
        return None
    if tag == "bool":
        if not isinstance(body, bool):
            raise CanonicalizationError("canonical bool body is invalid")
        return body
    if tag == "int":
        if not isinstance(body, str):
            raise CanonicalizationError("canonical int body is invalid")
        try:
            parsed = int(body)
        except ValueError as exc:
            raise CanonicalizationError("canonical int body is invalid") from exc
        if str(parsed) != body:
            raise CanonicalizationError("canonical int is not minimally encoded")
        return parsed
    if tag == "string":
        if not isinstance(body, str):
            raise CanonicalizationError("canonical string body is invalid")
        return body
    if tag not in _COMPOUND_TAGS:
        raise CanonicalizationError(f"unknown canonical wire tag: {tag}")
    if not isinstance(body, list):
        raise CanonicalizationError("canonical compound body must be an array")
    frozen = _FrozenValue(tag, tuple(canonical_unwire(item) for item in body))
    _validate_compound(frozen)
    return frozen


def _serde_json_text(text: str) -> str:
    """Match ``serde_json::to_vec`` for U+2028 and U+2029.

    The packet id hashes those characters as raw UTF-8. If an encoder wrote
    ``\\u2028`` or ``\\u2029``, rewrite that escape. A literal backslash
    followed by ``u2028`` stays escaped, because that backslash is itself
    escaped.
    """

    if "\\u2028" not in text and "\\u2029" not in text:
        return text
    pieces: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] != "\\":
            pieces.append(text[index])
            index += 1
            continue
        end = index
        while end < length and text[end] == "\\":
            end += 1
        pairs = (end - index) // 2
        if pairs:
            pieces.append("\\" * (pairs * 2))
        if (end - index) % 2 == 0:
            index = end
            continue
        if text.startswith(("u2028", "u2029"), end):
            pieces.append("\u2028" if text[end + 4] == "8" else "\u2029")
            index = end + 5
            continue
        pieces.append("\\")
        index = end
    return "".join(pieces)


def canonical_json(value: Any) -> str:
    """Seal a value as compact ``core-canonical-v1`` JSON.

    The bytes are the tagged wire ``[marker, tag, body]`` with no whitespace.
    This is the packet sealer. It is not RFC 8785: the tree holds only arrays,
    strings, null, and booleans, so object key order and JCS number rules do
    not apply. Integers travel as decimal strings inside their tags.
    U+2028 and U+2029 stay raw, the same text ``serde_json`` hashes for the
    packet id.
    """

    return _serde_json_text(
        json.dumps(
            _wire(value),
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


def canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def domain_digest(domain: str, value: Any) -> str:
    """SHA-256 digest with an explicit, length-delimited domain separator."""

    if not domain:
        raise CanonicalizationError("digest domain must be non-empty")
    domain_bytes = domain.encode("utf-8")
    payload = canonical_bytes(value)
    framed = (
        len(domain_bytes).to_bytes(4, "big")
        + domain_bytes
        + len(payload).to_bytes(8, "big")
        + payload
    )
    return hashlib.sha256(framed).hexdigest()


__all__ = [
    "CANONICAL_MARKER",
    "CanonicalizationError",
    "canonical_bytes",
    "canonical_json",
    "canonical_unwire",
    "canonical_wire",
    "domain_digest",
    "freeze",
    "thaw",
]
