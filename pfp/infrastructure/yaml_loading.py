"""Fail-closed YAML 1.2 strict loader infrastructure adapter.

AuthorityEffect: None.
"""

from __future__ import annotations

from ..domain.shared_kernel.yaml_strict import (
    FORBIDDEN_UNQUOTED_BOOLEANS,
    StrictYamlError,
    StrictYamlLoader,
    strict_yaml_load,
    strict_yaml_load_all,
)

__all__ = [
    "FORBIDDEN_UNQUOTED_BOOLEANS",
    "StrictYamlError",
    "StrictYamlLoader",
    "strict_yaml_load",
    "strict_yaml_load_all",
]
