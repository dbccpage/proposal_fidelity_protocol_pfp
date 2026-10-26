"""Fail-closed YAML 1.2 strict loader with duplicate key and boolean coercion defenses.

Pure domain implementation with zero infrastructure dependencies.
AuthorityEffect: None.
"""

from __future__ import annotations

import collections.abc
from typing import Any, Iterator

import yaml

FORBIDDEN_UNQUOTED_BOOLEANS = frozenset(
    {
        "yes",
        "no",
        "on",
        "off",
        "y",
        "n",
        "Yes",
        "No",
        "On",
        "Off",
        "Y",
        "N",
        "YES",
        "NO",
        "ON",
        "OFF",
    }
)


class StrictYamlError(ValueError, yaml.YAMLError):
    """Raised when strict YAML invariants (no duplicate keys, no YAML 1.1 boolean coercion) are violated."""


class StrictYamlLoader(yaml.SafeLoader):
    """Fail-closed YAML loader enforcing strict YAML 1.2 scalar and mapping invariants."""


def _construct_strict_mapping(
    loader: StrictYamlLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    if isinstance(node, yaml.MappingNode):
        loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, collections.abc.Hashable):
            line = getattr(key_node.start_mark, "line", 0) + 1
            col = getattr(key_node.start_mark, "column", 0) + 1
            raise StrictYamlError(
                f"Unhashable key of type {type(key).__name__} at line {line}, col {col}"
            )
        if key in mapping:
            line = getattr(key_node.start_mark, "line", 0) + 1
            col = getattr(key_node.start_mark, "column", 0) + 1
            raise StrictYamlError(
                f"DUPLICATE_KEY_REJECTED: Duplicate key {key!r} detected in YAML mapping at line {line}, column {col}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


def _construct_strict_bool(loader: StrictYamlLoader, node: yaml.ScalarNode) -> bool:
    val = loader.construct_scalar(node)
    if val in FORBIDDEN_UNQUOTED_BOOLEANS or val.lower() in {
        "yes",
        "no",
        "on",
        "off",
        "y",
        "n",
    }:
        line = getattr(node.start_mark, "line", 0) + 1
        col = getattr(node.start_mark, "column", 0) + 1
        raise StrictYamlError(
            f"UNQUOTED_BOOLEAN_REJECTED: Unquoted YAML 1.1 boolean scalar {val!r} at line {line}, column {col} is forbidden; "
            f"use explicit 'true'/'false' for booleans or quote it as a string"
        )
    val_lower = val.lower()
    if val_lower not in loader.bool_values:
        line = getattr(node.start_mark, "line", 0) + 1
        col = getattr(node.start_mark, "column", 0) + 1
        raise StrictYamlError(
            f"Invalid boolean scalar {val!r} at line {line}, column {col}"
        )
    return loader.bool_values[val_lower]


StrictYamlLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_strict_mapping,
)
StrictYamlLoader.add_constructor(
    "tag:yaml.org,2002:bool",
    _construct_strict_bool,
)


def strict_yaml_load(stream: str | bytes | Any) -> Any:
    """Load a single YAML document using StrictYamlLoader."""
    if isinstance(stream, str):
        stream = stream.lstrip("\ufeff")
    return yaml.load(stream, Loader=StrictYamlLoader)


def strict_yaml_load_all(stream: str | bytes | Any) -> Iterator[Any]:
    """Load multiple YAML documents using StrictYamlLoader."""
    if isinstance(stream, str):
        stream = stream.lstrip("\ufeff")
    return yaml.load_all(stream, Loader=StrictYamlLoader)


__all__ = [
    "FORBIDDEN_UNQUOTED_BOOLEANS",
    "StrictYamlError",
    "StrictYamlLoader",
    "strict_yaml_load",
    "strict_yaml_load_all",
]
