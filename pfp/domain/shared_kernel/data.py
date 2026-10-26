"""Shared Kernel: Generic Data containers and payload representations."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Self

from ..exceptions import InvariantViolationError


def _freeze_val(val: Any) -> Any:
    if isinstance(val, (dict, Mapping, MappingProxyType)):
        if any(type(key) is not str for key in val):
            raise InvariantViolationError(
                "DataRecord mapping keys must be exact strings"
            )
        return MappingProxyType({key: _freeze_val(value) for key, value in val.items()})
    if isinstance(val, (list, tuple)):
        return tuple(_freeze_val(v) for v in val)
    if isinstance(val, (set, frozenset)):
        raise InvariantViolationError("DataRecord does not accept unordered set values")
    if val is None or type(val) in (str, int, bool):
        return val
    if type(val) is float and math.isfinite(val):
        return val
    raise InvariantViolationError(
        f"DataRecord values must be strict JSON data, got {type(val).__name__}"
    )


def _unfreeze_val(val: Any) -> Any:
    if isinstance(val, (dict, Mapping, MappingProxyType)):
        return {k: _unfreeze_val(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [_unfreeze_val(v) for v in val]
    return val


def _hash_val(val: Any) -> int:
    if isinstance(val, (dict, Mapping, MappingProxyType)):
        return hash(tuple(sorted((k, _hash_val(v)) for k, v in val.items())))
    elif isinstance(val, (list, tuple)):
        return hash(tuple(_hash_val(v) for v in val))
    return hash(val)


@dataclass(frozen=True, slots=True, eq=False)
class DataRecord:
    """Recursively immutable, hashable dictionary wrapper Value Object."""

    data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.data, (dict, Mapping, MappingProxyType)):
            raise InvariantViolationError(
                f"DataRecord must contain a dictionary/mapping, got {type(self.data).__name__}"
            )
        object.__setattr__(self, "data", _freeze_val(self.data))

    @classmethod
    def from_mapping(cls: type[Self], mapping: Mapping[str, Any] | Self) -> Self:
        if isinstance(mapping, cls):
            return mapping
        if not isinstance(mapping, (dict, Mapping, MappingProxyType)):
            raise InvariantViolationError(
                f"DataRecord.from_mapping requires a mapping, got {type(mapping).__name__}"
            )
        return cls(mapping)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return _unfreeze_val(self.data)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DataRecord) or type(other) is not type(self):
            return False
        return _unfreeze_val(self.data) == _unfreeze_val(other.data)

    def __hash__(self) -> int:
        return hash((type(self), _hash_val(self.data)))
