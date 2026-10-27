"""Check an executor's output against the payload schema of the sub-colour it emits.

The schemas live in the canon (``SUBCOLOUR_SCHEMAS``). This checks the JSON Schema subset
they use: ``type``, ``properties``, ``required``, ``additionalProperties``, ``items``,
``enum``, ``const`` and ``pattern``. A plain colour such as ``Audit`` has no schema and
every value passes.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from functools import cache

from operads.canon import SUBCOLOUR_SCHEMAS

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


@cache
def schema_for(port: str) -> dict | None:
    text = SUBCOLOUR_SCHEMAS.get(port)
    return None if text is None else json.loads(text)


def _type_ok(value: object, kind: str) -> bool:
    if kind == "integer":
        return type(value) is int
    if kind == "number":
        return type(value) in (int, float)
    return type(value) is _TYPES[kind]


def _scalar_problem(schema: dict, value: object, where: str) -> str | None:
    if "const" in schema and value != schema["const"]:
        return f"{where}: expected {schema['const']!r}"
    if "enum" in schema and value not in schema["enum"]:
        return f"{where}: {value!r} is not one of {schema['enum']}"
    if "type" in schema and not _type_ok(value, schema["type"]):
        return f"{where}: expected {schema['type']}, got {type(value).__name__}"
    if "pattern" in schema and (type(value) is not str or re.search(schema["pattern"], value) is None):
        return f"{where}: does not match {schema['pattern']}"
    return None


def _object_problem(schema: dict, value: dict, where: str) -> str | None:
    properties = schema.get("properties", {})
    missing = [name for name in schema.get("required", ()) if name not in value]
    if missing:
        return f"{where}: missing {missing[0]!r}"
    extra = schema.get("additionalProperties", True)
    for name, item in value.items():
        if name in properties:
            found = problem(properties[name], item, f"{where}.{name}")
        elif extra is False:
            found = f"{where}: unexpected {name!r}"
        else:
            found = problem(extra, item, f"{where}.{name}") if type(extra) is dict else None
        if found:
            return found
    return None


def problem(schema: dict, value: object, where: str = "$") -> str | None:
    """The first way ``value`` breaks ``schema``, or None."""
    if found := _scalar_problem(schema, value, where):
        return found
    if type(value) is list and "items" in schema:
        for index, item in enumerate(value):
            if found := problem(schema["items"], item, f"{where}[{index}]"):
                return found
    if type(value) is dict:
        return _object_problem(schema, value, where)
    return None


def output_problem(port: str, value: object) -> str | None:
    """Why ``value`` may not travel on wire ``port``, or None."""
    schema = schema_for(port)
    return None if schema is None else problem(schema, value)
