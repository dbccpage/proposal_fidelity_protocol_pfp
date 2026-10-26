"""Shared helpers for the PFP typed-contract tests (path loading and YAML-vs-model parity).

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import sys
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml
from pydantic import BaseModel


def pfp_root() -> Path:
    """The current PFP package, independent of documentation placement."""
    return Path(__file__).resolve().parents[2]


def load_module(relative_path: str, name: str) -> ModuleType:
    path = (pfp_root() / relative_path).resolve()
    if not path.is_relative_to(pfp_root()):
        raise ValueError("TEST_MODULE_PATH_ESCAPE")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_yaml(relative_path: str) -> Any:
    root = pfp_root() / "infrastructure" / "yaml"
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("TEST_RESOURCE_PATH_ESCAPE")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _find_key(node: Any, key: str) -> Any:
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            found = _find_key(value, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_key(value, key)
            if found is not None:
                return found
    return None


def parity_problems(defs: dict[str, Any], models: dict[str, type]) -> list[str]:
    """Compare YAML ``$defs`` with Pydantic classes. Returns a list of mismatches."""
    problems: list[str] = []
    for name, cls in models.items():
        if name not in defs:
            problems.append(f"{name}: missing from YAML")
            continue
        spec = defs[name]
        if isinstance(cls, type) and issubclass(cls, Enum):
            if [m.value for m in cls] != list(spec["enum"]):
                problems.append(f"{name}: enum values differ")
            continue
        assert issubclass(cls, BaseModel)
        fields = cls.model_fields
        props = spec["properties"]
        if set(props) != set(fields):
            problems.append(f"{name}: property names differ {sorted(set(props) ^ set(fields))}")
            continue
        required_model = {k for k, f in fields.items() if f.is_required()}
        if set(spec.get("required", [])) != required_model:
            problems.append(f"{name}: required set differs")
        if (
            spec.get("additionalProperties") is not False
            or cls.model_config.get("extra") != "forbid"
        ):
            problems.append(f"{name}: additionalProperties/extra mismatch")
        schema_props = cls.model_json_schema()["properties"]
        for prop, pspec in props.items():
            if "const" in pspec and _find_key(schema_props[prop], "const") != pspec["const"]:
                problems.append(f"{name}.{prop}: const differs")
            if "pattern" in pspec and _find_key(schema_props[prop], "pattern") != pspec["pattern"]:
                problems.append(f"{name}.{prop}: pattern differs")
            for bound in ("minLength", "maxLength", "minimum", "maximum"):
                if bound in pspec and _find_key(schema_props[prop], bound) != pspec[bound]:
                    problems.append(f"{name}.{prop}: {bound} differs")
    extra = set(defs) - set(models)
    if extra:
        problems.append(f"YAML defs without a model: {sorted(extra)}")
    return problems
