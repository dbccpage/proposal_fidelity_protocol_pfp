"""Infrastructure layer for Prompt Civilization.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .cas import ContentAddressedStorageV1
    from .event_log import DurableEventLogV1, PromptCivEventV1
    from .genealogy_adapter import FileCemeteryAdapter, FileGenealogyAdapter
    from .matching import PromptPatternMatcherV1
    from .persistence import PromptCivProjectionEngineV1
    from .prompt_ecology.telemetry import JsonlTelemetrySource, SqliteMetabolismStore

__all__ = ['ContentAddressedStorageV1', 'DurableEventLogV1', 'FileCemeteryAdapter', 'FileGenealogyAdapter', 'JsonlTelemetrySource', 'PromptCivEventV1', 'PromptCivProjectionEngineV1', 'PromptPatternMatcherV1', 'SqliteMetabolismStore']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ContentAddressedStorageV1': ('.cas', 'ContentAddressedStorageV1'),
    'DurableEventLogV1': ('.event_log', 'DurableEventLogV1'),
    'PromptCivEventV1': ('.event_log', 'PromptCivEventV1'),
    'FileCemeteryAdapter': ('.genealogy_adapter', 'FileCemeteryAdapter'),
    'FileGenealogyAdapter': ('.genealogy_adapter', 'FileGenealogyAdapter'),
    'PromptPatternMatcherV1': ('.matching', 'PromptPatternMatcherV1'),
    'PromptCivProjectionEngineV1': ('.persistence', 'PromptCivProjectionEngineV1'),
    'JsonlTelemetrySource': ('.prompt_ecology.telemetry', 'JsonlTelemetrySource'),
    'SqliteMetabolismStore': ('.prompt_ecology.telemetry', 'SqliteMetabolismStore'),
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
