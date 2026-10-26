from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .command import Command
    from .command_status import CommandStatus
    from .command_verdict import CommandVerdict

__all__ = ['Command', 'CommandStatus', 'CommandVerdict']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'Command': ('.command', 'Command'),
    'CommandStatus': ('.command_status', 'CommandStatus'),
    'CommandVerdict': ('.command_verdict', 'CommandVerdict'),
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
