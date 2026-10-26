"""Unavailable sister contexts must not turn failures into empty results."""

from __future__ import annotations

import builtins
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_with_missing_sister(name: str) -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "domain" / "bridge" / f"{name}.py"
    full_name = f"omega_engine_pfp.domain.bridge.{name}"
    spec = importlib.util.spec_from_file_location(full_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "omega_engine_pfp.domain.bridge"
    original_import = builtins.__import__

    def blocked_import(import_name: str, *args: object, **kwargs: object):
        if (
            import_name.startswith("omega_engine_woland.stage")
            or import_name.startswith("omega_engine_epistemic_immune_system")
            or "ast_cochain" in import_name
        ):
            raise ImportError("simulated missing sister context")
        return original_import(import_name, *args, **kwargs)

    try:
        builtins.__import__ = blocked_import
        spec.loader.exec_module(module)
    finally:
        builtins.__import__ = original_import
    return module


def test_missing_ast_bridge_refuses_on_use() -> None:
    module = _load_with_missing_sister("ast_cochain_extractor")
    with pytest.raises(module.BridgeUnavailableError, match="simulated missing sister context"):
        module.ASTCochainExtractor()
    with pytest.raises(module.BridgeUnavailableError, match="simulated missing sister context"):
        list(module.DEFAULT_CLEAN_ARCH_LAYERS)


def test_missing_pharmacy_bridge_refuses_on_use() -> None:
    module = _load_with_missing_sister("pharmacy_seeder")
    with pytest.raises(module.BridgeUnavailableError, match="simulated missing sister context"):
        module.PharmacySeeder()
    with pytest.raises(module.BridgeUnavailableError, match="simulated missing sister context"):
        list(module.DEFAULT_ANTIBODY_TEMPLATES)
