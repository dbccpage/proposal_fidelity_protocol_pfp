from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .domain_event import DomainEvent
    from .event_recorder import EventRecorder
    from .event_stream import EventStream

__all__ = ['DomainEvent', 'EventRecorder', 'EventStream']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'DomainEvent': ('.domain_event', 'DomainEvent'),
    'EventRecorder': ('.event_recorder', 'EventRecorder'),
    'EventStream': ('.event_stream', 'EventStream'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
