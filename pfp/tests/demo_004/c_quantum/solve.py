"""C021 Frozen Solver: Q40-R Stabilizer Challenge Deliverable.

Exposes `def solve(case: dict) -> dict` returning canonical wire JSON certificates
certifying exact ground-state energies, degeneracies, signed decompositions, or witnesses.
Delegates to the native Rust stabilizer through explicit outer composition.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "omega_engine_pfp").is_dir())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

if __package__ in (None, ""):
    __package__ = "omega_engine_pfp.tests.demo_004.c_quantum"

from omega_engine_pfp.infrastructure.adapters.stabilizer_rust_adapter import (
    StabilizerRustAdapter,
)

from .swarm.q40_solver import (
    Q40StabilizerSolver,
)

_STABILIZER = StabilizerRustAdapter()

_SOLVER: Q40StabilizerSolver | None = None


def get_solver() -> Q40StabilizerSolver:
    global _SOLVER
    if _SOLVER is None:
        _SOLVER = Q40StabilizerSolver()
    return _SOLVER


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Frozen solver entrypoint executing C021 stabilizer solution."""
    solver = get_solver()
    cert = solver.solve(case)
    return cert.to_canonical_dict()


if __name__ == "__main__":
    import json
    import sys

    # Support stdin/stdout json piping
    raw_input = sys.stdin.read()
    if raw_input.strip():
        req = json.loads(raw_input)
        out = solve(req, port=_STABILIZER)
        print(json.dumps(out, indent=2, sort_keys=True))
