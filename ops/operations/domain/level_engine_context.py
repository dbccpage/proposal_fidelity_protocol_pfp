"""Injected research resources; no discovery, filesystem or vendor adapter here.

AuthorityEffect: None. The concrete resource adapter belongs to PFP infrastructure.
"""

from __future__ import annotations

import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable, Protocol


class ContextRefusal(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


class LevelEngineResourcesPort(Protocol):
    @property
    def runtime_root(self) -> Path: ...

    @property
    def evidence_root(self) -> Path: ...

    @property
    def governance_root(self) -> Path: ...

    @property
    def repository_root(self) -> Path | None: ...

    @property
    def vendor_root(self) -> Path | None: ...

    @property
    def output_root(self) -> Path | None: ...

    @property
    def lean_root(self) -> Path | None: ...

    @property
    def reach_root(self) -> Path | None: ...

    def resource(self, relative: str) -> Path: ...
    def source(self, relative: str) -> Path: ...
    def historical_path(self, relative: str) -> Path: ...
    def current_path(self, relative: str) -> Path: ...
    def governance_path(self, relative: str) -> Path: ...
    def lean_path(self, relative: str) -> Path: ...
    def require_repository(self) -> Path: ...
    def require_vendor(self) -> Path: ...


class LevelEngineOperationPorts(Protocol):
    bundles: Any
    reach: Any
    ladder_document: Callable[..., Any]
    registrations: Callable[..., Any]
    reach_main: Callable[..., int]
    registry: Callable[..., Any]
    stage_table_bytes: Callable[[], bytes]
    checker: Callable[..., Any]
    checker_entry: Callable[..., Any]
    vendor_import_scope: Callable[..., Any]


_CONTEXT: ContextVar[LevelEngineResourcesPort | None] = ContextVar("level_engine_context", default=None)
_VENDOR_IMPORT_SCOPE: ContextVar[Callable[..., Any] | None] = ContextVar(
    "level_engine_vendor_import_scope",
    default=None,
)


def configure_context(context: LevelEngineResourcesPort) -> None:
    """Preserve the existing refusal to rebind a loaded research runtime."""
    previous = _CONTEXT.get()
    prefix = "operations.use_cases.level_engine.research_engine."
    if previous is not None and previous != context and any(name.startswith(prefix) for name in sys.modules):
        raise ContextRefusal("LEVEL_ENGINE_CONTEXT_BOUND", "start a separate process to change research resource roots")
    _CONTEXT.set(context)


def current_context() -> LevelEngineResourcesPort:
    context = _CONTEXT.get()
    if context is None:
        raise ContextRefusal("LEVEL_ENGINE_CONTEXT_REQUIRED", "inject resources before loading the research runtime")
    return context


def configure_vendor_import_scope(scope: Callable[..., Any]) -> None:
    """Record the evidence-root importer used by sealed loads and tree replay."""
    _VENDOR_IMPORT_SCOPE.set(scope)


def vendor_import_scope() -> Callable[..., Any]:
    scope = _VENDOR_IMPORT_SCOPE.get()
    if scope is None:
        raise ContextRefusal(
            "VENDOR_IMPORT_SCOPE_REQUIRED",
            "inject the vendor import scope before loading sealed evidence",
        )
    return scope
