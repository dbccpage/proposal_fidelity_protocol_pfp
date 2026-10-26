"""Intelligence Metabolism application policies. AuthorityEffect: None."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .digest import DailyDigestGenerator
    from .episode import EpisodeSegmenter
    from .motifs import MotifMiner

__all__ = ['DailyDigestGenerator', 'EpisodeSegmenter', 'MotifMiner']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'DailyDigestGenerator': ('.digest', 'DailyDigestGenerator'),
    'EpisodeSegmenter': ('.episode', 'EpisodeSegmenter'),
    'MotifMiner': ('.motifs', 'MotifMiner'),
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
