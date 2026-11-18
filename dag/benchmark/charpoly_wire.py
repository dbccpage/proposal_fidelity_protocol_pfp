"""Historical import name for the WF52 charpoly normalizer.

``from dag.benchmark import charpoly_wire`` is what the two-signal tests say.
The implementation lives in ``workflows/wf52_finite_qm_benchmark/charpoly_wire.py``.
This module loads that file and re-exports its public names.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "workflows"
    / "wf52_finite_qm_benchmark"
    / "charpoly_wire.py"
)


def _load():
    if not _SOURCE.is_file():
        raise ImportError(f"WF52 charpoly wire is absent: {_SOURCE}")
    spec = importlib.util.spec_from_file_location("_wf52_charpoly_wire", _SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"WF52 charpoly wire could not be loaded: {_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_module = _load()
WireRefusal = _module.WireRefusal
normalize_candidate = _module.normalize_candidate
