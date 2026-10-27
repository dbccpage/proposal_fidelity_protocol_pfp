"""Composition root for Level Engine operations. AuthorityEffect: None."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from operations.domain.level_engine_context import (
    LevelEngineOperationPorts,
    configure_vendor_import_scope,
)

_PORTS: LevelEngineOperationPorts | None = None


@dataclass(frozen=True)
class LevelEnginePorts:
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


def bind_vendor_import_scope() -> None:
    from pfp.infrastructure.tower_research.level_engine.vendor_loading import (
        vendor_import_scope,
    )

    configure_vendor_import_scope(vendor_import_scope)


def ports() -> LevelEngineOperationPorts:
    global _PORTS
    if _PORTS is None:
        _PORTS = _load_ports()
    return _PORTS


class _Lazy:
    """Load one outward adapter on first use, after the resource context exists."""

    def __init__(self, loader: Callable[[], Any]) -> None:
        self._loader = loader
        self._value: Any = None
        self._loaded = False

    def _get(self) -> Any:
        if not self._loaded:
            self._value = self._loader()
            self._loaded = True
        return self._value

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get(), name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._get()(*args, **kwargs)


def _load_ports() -> LevelEnginePorts:
    bind_vendor_import_scope()
    from pfp.infrastructure.adapters.mssn_research.loader import checker, entry
    from pfp.infrastructure.tower_research.level_engine.vendor_loading import (
        vendor_import_scope,
    )
    from pfp.infrastructure.tower_research.reach.cli import main as reach_main
    from pfp.infrastructure.tower_research.reach.resources import registry
    from pfp.infrastructure.tower_research.reach.stage_registry import (
        table_bytes,
    )

    def load_bundles() -> Any:
        from pfp.infrastructure.tower_research.level_engine.outward import bundles

        return bundles

    def load_reach() -> Any:
        from pfp.infrastructure.tower_research.level_engine.outward import reach

        return reach

    def load_ladder() -> Any:
        from pfp.infrastructure.tower_research.level_engine.outward.lift import (
            ladder_document,
        )

        return ladder_document

    def load_registrations() -> Any:
        from pfp.infrastructure.tower_research.level_engine.outward.qlevels import (
            registrations,
        )

        return registrations

    return LevelEnginePorts(
        bundles=_Lazy(load_bundles),
        reach=_Lazy(load_reach),
        ladder_document=_Lazy(load_ladder),
        registrations=_Lazy(load_registrations),
        reach_main=reach_main,
        registry=registry,
        stage_table_bytes=table_bytes,
        checker=checker,
        checker_entry=entry,
        vendor_import_scope=vendor_import_scope,
    )


def main(argv: list[str] | None = None) -> int:
    from operations.use_cases.level_engine.dispatch import main as dispatch_main
    from pfp.infrastructure.tower_research.level_engine.context import installed_context

    return dispatch_main(argv, context_factory=installed_context, ports_factory=ports)


if __name__ == "__main__":
    raise SystemExit(main())
