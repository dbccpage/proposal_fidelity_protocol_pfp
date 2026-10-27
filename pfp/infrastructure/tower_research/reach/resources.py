"""Versioned receiving-side resources. Historical bytes remain immutable."""
from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

_CHECKER_SOURCE_OWNERS = {
    "symbol_game.infrastructure.tower_research.reach": "symbol_game",
    "pfp.infrastructure.tower_research.reach": "pfp",
}


def _active_checker_pin() -> dict[str, Any]:
    from operations.domain.level_engine_context import (
        ContextRefusal,
        current_context,
    )

    from ..level_engine.context import installed_context
    try:
        context = current_context()
    except ContextRefusal as exc:
        if exc.code != "LEVEL_ENGINE_CONTEXT_REQUIRED":
            raise
        context = installed_context()
    try:
        pins = json.loads(context.governance_path("PINS.json").read_bytes())
        result: dict[str, Any] = pins["relocation"]["active_checker_registry"]
        return result
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError("RR-PIN: active checker registry pin unavailable") from exc


def _verify_active_checkers(raw: bytes, result: dict[str, Any]) -> None:
    from pfp.domain.tower.registry import STAGES
    pin = _active_checker_pin()
    resource_package = pin.get("resource_package")
    owner = _CHECKER_SOURCE_OWNERS.get(resource_package) if isinstance(resource_package, str) else None
    if (pin.get("version") != 2 or owner is None
            or pin.get("resource_path") != "data/v2/registry/checkers.json"
            or pin.get("sha256") != hashlib.sha256(raw).hexdigest()):
        raise ValueError("RR-PIN: active checker registry digest or identity differs")
    checkers = result.get("checkers")
    expected = {f"stage_{stage.level:03d}": stage.level for stage in STAGES}
    if (result.get("schema") != "mssn.checker-registry.v2"
            or result.get("registry_version") != 2 or not isinstance(checkers, dict)
            or set(checkers) != set(expected)):
        raise ValueError("RR-PIN: active checker registry stage closure differs")
    for name, level in expected.items():
        entry = checkers[name]
        # The pin names the registry's source owner, not its present installation.
        # Receipt verification still resolves the original commit/path/hash.
        path = f"{owner}/infrastructure/adapters/mssn_research/checkers/{name}.py"
        if (not isinstance(entry, dict) or entry.get("id") != name
                or type(entry.get("level")) is not int or entry["level"] != level
                or entry.get("path") != path):
            raise ValueError("RR-PIN: active checker key, stage, or path differs")


def reach_root(version: str = "v1") -> Path:
    if version not in {"v1", "v2"}:
        raise ValueError("UNSUPPORTED_REACH_VERSION")
    path = Path(str(files(__package__).joinpath("data", version)))
    if not path.is_dir():
        raise ValueError("REACH_RESOURCES_UNAVAILABLE")
    return path


def registry(name: str, version: str = "v2") -> dict[str, Any]:
    if name not in {"checkers", "stage_registry", "carriers"}:
        raise ValueError("UNKNOWN_REACH_REGISTRY")
    raw = (reach_root(version) / "registry" / f"{name}.json").read_bytes()
    result: dict[str, Any] = json.loads(raw)
    if name == "checkers" and version == "v2":
        _verify_active_checkers(raw, result)
    return result
