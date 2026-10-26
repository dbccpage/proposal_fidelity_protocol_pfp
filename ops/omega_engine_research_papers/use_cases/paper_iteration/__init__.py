"""Paper iteration use cases (Clean Arch-lite).

Contains paper sweep execution, obstruction tracing, symbol game flow, and proof obligation bridging.
"""

# ruff: noqa: E402, F403 -- bind public module identities before imports.

from __future__ import annotations

import sys

_PARENT_IDENTITIES = (
    "omega_engine_research_papers.use_cases",
)
_PACKAGE_IDENTITIES = tuple(
    f"{parent_identity}.paper_iteration" for parent_identity in _PARENT_IDENTITIES
)

if __name__ in _PACKAGE_IDENTITIES:
    _this_package = sys.modules[__name__]
    _loaded_parent_name = __name__.rsplit(".", 1)[0]
    _this_parent = sys.modules.get(_loaded_parent_name)
    if _this_parent is None:
        raise RuntimeError("PAPER_ITERATION_PARENT_IDENTITY_MISSING")
    for _parent_identity in _PARENT_IDENTITIES:
        _existing_parent = sys.modules.get(_parent_identity)
        if _existing_parent is not None and _existing_parent is not _this_parent:
            raise RuntimeError("PAPER_ITERATION_PARENT_IDENTITY_CONFLICT")
        sys.modules[_parent_identity] = _this_parent
    for _package_identity in _PACKAGE_IDENTITIES:
        _existing_package = sys.modules.get(_package_identity)
        if _existing_package is not None and _existing_package is not _this_package:
            raise RuntimeError("PAPER_ITERATION_PACKAGE_IDENTITY_CONFLICT")
        sys.modules[_package_identity] = _this_package

from .duration_profile import *
from .engine import *
from .packetization import *
from .paper_obstruction_trace import *
from .paper_repair_tent_v1 import *
from .paper_repair_tent_verifier_v1 import *
from .paper_replay import *
from .paper_resolution import *
from .proof_obligation_bridge import *
from .rip_papers_policy import *
from .symbol_game_flow import *

if __name__ in _PACKAGE_IDENTITIES:
    for _parent_identity in _PARENT_IDENTITIES:
        _parent_module = sys.modules[_parent_identity]
        _existing_child = getattr(_parent_module, "paper_iteration", None)
        if _existing_child is not None and _existing_child is not _this_package:
            raise RuntimeError("PAPER_ITERATION_PARENT_CHILD_IDENTITY_CONFLICT")
        setattr(_parent_module, "paper_iteration", _this_package)
    _loaded_prefix = f"{__name__}."
    for _module_name, _module in tuple(sys.modules.items()):
        if not _module_name.startswith(_loaded_prefix):
            continue
        _relative_name = _module_name[len(_loaded_prefix) :]
        for _package_identity in _PACKAGE_IDENTITIES:
            _alias_name = f"{_package_identity}.{_relative_name}"
            _existing_module = sys.modules.get(_alias_name)
            if _existing_module is not None and _existing_module is not _module:
                raise RuntimeError("PAPER_ITERATION_MODULE_IDENTITY_CONFLICT")
            sys.modules[_alias_name] = _module
