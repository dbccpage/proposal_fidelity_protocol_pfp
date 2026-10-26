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
    / "omega_engine_woland/tests/pilots/evidence/pfp_ownership_migration_20261012"
    / "frozen_sources/omega_engine_symbol_game/infrastructure/adapters")
_HASHES = {
    "pfp_derivation": "74e1c7df658d2cfad48882fb4f1a6c16c1e839bd3cb2ca1f51e60632f94cdf72",
    "pfp_experiment": "21ff2df08a06fc745f4045687c507c02ae530ed42d42f39dd443cf14eb38ec95",
}
_IMPORTS = {
    "omega_engine_providers.domain.types": "omega_engine_woland.domain.providers.types",
    "omega_engine_providers.infrastructure.budget_ledger": "omega_engine_woland.infrastructure.providers.budget_ledger",
    "omega_engine_providers.infrastructure.openai_compat": "omega_engine_woland.infrastructure.providers.openai_compat",
    "omega_engine_providers.infrastructure.openrouter_deadline": "omega_engine_woland.infrastructure.providers.openrouter_deadline",
    "omega_engine_providers.infrastructure.openrouter_experiment_deadline": "omega_engine_woland.infrastructure.providers.openrouter_experiment_deadline",
    "omega_engine_providers.infrastructure.wire": "omega_engine_woland.infrastructure.providers.wire",
    "omega_engine_symbol_game.use_cases.pfp_derivation_loops": "omega_engine_pfp.use_cases.pfp_derivation_loops",
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
            return import_module("omega_engine_pfp.infrastructure.adapters.pfp_evidence")
        return builtins.__import__(_IMPORTS.get(module, module), globals, locals, fromlist, level)

    module = ModuleType("omega_engine_pfp.tests._historical_" + name)
    module.__file__ = str(path)
    module.__package__ = "omega_engine_pfp.tests"
    module.__dict__["__builtins__"] = {**vars(builtins), "__import__": historical_import}
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    module.dispatch_deadline = _offline_only
    return module


historical_derivation = _load("pfp_derivation")
historical_experiment = _load("pfp_experiment", derivation=historical_derivation)
