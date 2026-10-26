"""Explicit resource context for the relocated research tests."""
import os
from pathlib import Path

from omega_engine_operations.domain.level_engine_context import (
    configure_context,
)
from omega_engine_pfp.infrastructure.tower_research.level_engine.context import installed_context


def _path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


repository = _path("LEVEL_ENGINE_WORKSPACE")
configure_context(installed_context(
    repository_root=repository,
    vendor_root=_path("LEVEL_ENGINE_VENDOR"),
    output_root=_path("LEVEL_ENGINE_OUTPUT"),
    lean_root=_path("LEVEL_ENGINE_LEAN_ROOT") or (repository / "lean4/research_programs/level_engine" if repository else None),
))
from omega_engine_operations.infrastructure.level_engine_ports import bind_vendor_import_scope  # noqa: E402

bind_vendor_import_scope()
