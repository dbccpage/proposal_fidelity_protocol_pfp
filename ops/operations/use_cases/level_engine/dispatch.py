"""Explicit composition and subprocess arguments for Level Engine operations."""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from operations.domain.level_engine_context import (
    LevelEngineOperationPorts,
    LevelEngineResourcesPort,
    configure_context,
    current_context,
)

MODULES = {"gate", "bootstrap", "bind", "vendor", "lift_check", "preflight_draft", "reach_replay", "reach_ledger_check", "inject", "lean_gen", "lean_audit", "lean_build"}
_PORTS = {"gate", "bootstrap", "bind", "reach_replay", "reach_ledger_check"}
_ENTRY = "operations.infrastructure.level_engine_ports"

def run(name: str, argv: list[str] | None = None, context: LevelEngineResourcesPort | None = None,
        ports: LevelEngineOperationPorts | None = None) -> int:
    if name not in MODULES:
        raise ValueError("UNKNOWN_LEVEL_ENGINE_OPERATION")
    context = context or current_context()
    configure_context(context)
    module = importlib.import_module(__package__ + "." + name)
    if name.startswith("lean_"):
        return int(module.main(argv or [], context=context))
    if name in _PORTS:
        if ports is None:
            raise ValueError("LEVEL_ENGINE_PORTS_REQUIRED")
        return int(module.main(argv or [], ports))
    return int(module.main(argv or []))


def environment(context: LevelEngineResourcesPort | None = None) -> dict[str, str]:
    ctx = context or current_context()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    for key, value in (("WORKSPACE",ctx.repository_root),("VENDOR",ctx.vendor_root),("OUTPUT",ctx.output_root),("LEAN_ROOT",ctx.lean_root)):
        if value is not None:
            env["LEVEL_ENGINE_" + key] = str(value)
        else:
            env.pop("LEVEL_ENGINE_" + key, None)
    return env


def command(name: str, args: Sequence[str] = (), context: LevelEngineResourcesPort | None = None) -> list[str]:
    ctx = context or current_context()
    result = [sys.executable, "-B", "-m", _ENTRY]
    for key, value in (("workspace",ctx.repository_root),("vendor",ctx.vendor_root),("output-dir",ctx.output_root),("lean-root",ctx.lean_root)):
        if value is not None:
            result += ["--" + key, str(value)]
    return result + [name, *args]


def main(argv: list[str] | None = None, *,
         context_factory: Callable[..., LevelEngineResourcesPort] | None = None,
         ports_factory: Callable[[], LevelEngineOperationPorts] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("workspace", "vendor", "output-dir", "lean-root"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("operation", choices=sorted(MODULES))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if context_factory is None or ports_factory is None:
            raise ValueError("LEVEL_ENGINE_PORTS_REQUIRED")
        ctx = context_factory(repository_root=args.workspace, vendor_root=args.vendor,
                              output_root=args.output_dir, lean_root=args.lean_root)
        configure_context(ctx)
        return run(args.operation, args.arguments, ctx, ports_factory())
    except (ValueError, RuntimeError, OSError) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
