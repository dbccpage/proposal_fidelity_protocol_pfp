"""Pinned, offline-only v1 fixture writers; current execution is tested separately.

Compile retained source bytes without rewriting snapshots or installing legacy
package aliases. Only import ownership is relocated in this private namespace.
"""

import builtins
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import ModuleType


_SOURCE = (Path(__file__).resolve().parents[2]
    / "adversary/tests/pilots/evidence/pfp_ownership_migration_20261012"
    / "frozen_sources/symbol_game/infrastructure/adapters")
_HASHES = {
    "pfp_derivation": "74e1c7df658d2cfad48882fb4f1a6c16c1e839bd3cb2ca1f51e60632f94cdf72",
    "pfp_experiment": "21ff2df08a06fc745f4045687c507c02ae530ed42d42f39dd443cf14eb38ec95",
}
_IMPORTS = {
    "providers.domain.types": "adversary.domain.providers.types",
    "providers.infrastructure.budget_ledger": "adversary.infrastructure.providers.budget_ledger",
    "providers.infrastructure.openai_compat": "adversary.infrastructure.providers.openai_compat",
    "providers.infrastructure.openrouter_deadline": "adversary.infrastructure.providers.openrouter_deadline",
    "providers.infrastructure.openrouter_experiment_deadline": "adversary.infrastructure.providers.openrouter_experiment_deadline",
    "providers.infrastructure.wire": "adversary.infrastructure.providers.wire",
    "symbol_game.use_cases.pfp_derivation_loops": "pfp.use_cases.pfp_derivation_loops",
}


def _offline_only(*args, **kwargs):
    raise AssertionError("historical fixture writer requires an explicit synthetic transport")


def _load(name, *, derivation=None):
    path = _SOURCE / (name + ".py")
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != _HASHES[name]:
        raise AssertionError("historical PO035 adapter source bytes changed")

    def historical_import(module, globals=None, locals=None, fromlist=(), level=0):
        if level == 1 and module == "pfp_derivation":
            return derivation
        if level == 1 and module == "pfp_evidence":
            return import_module("pfp.infrastructure.adapters.pfp_evidence")
        return builtins.__import__(_IMPORTS.get(module, module), globals, locals, fromlist, level)

    module = ModuleType("pfp.tests._historical_" + name)
    module.__file__ = str(path)
    module.__package__ = "pfp.tests"
    module.__dict__["__builtins__"] = {**vars(builtins), "__import__": historical_import}
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    module.dispatch_deadline = _offline_only
    return module


historical_derivation = _load("pfp_derivation")
historical_experiment = _load("pfp_experiment", derivation=historical_derivation)
