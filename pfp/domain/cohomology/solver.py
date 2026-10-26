"""Sovereign Cohomology Solver interface.

Dispatches challenge cases (C011..C020) to an injected CohomologySolverPort.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..ports.cohomology_port import CohomologySolverPort, get_default_cohomology_solver


def detect_challenge(case: Mapping[str, Any]) -> str:
    """Detect challenge ID (c011..c020) from payload schema or explicit declaration."""
    if "challenge" in case or "challenge_id" in case:
        cid = str(case.get("challenge", case.get("challenge_id"))).lower()
        return f"c{int(cid):03d}" if cid.isdigit() else cid

    if "filtration" in case and isinstance(case["filtration"], str):
        return "c020"
    if "dh" in case or "horizontal_maps" in case or "double_complex" in case:
        return "c020"
    if "X" in case and "Y" in case:
        return "c016"
    if "lattice" in case or "plaquette" in case:
        return "c017"
    if "flow" in case or ("delta0" in case and "faces" in case):
        return "c014"
    if "filtration" in case and isinstance(case["filtration"], (list, tuple)):
        return "c015"
    if "partial2" in case or "target_b" in case or ("mode" in case and str(case.get("mode")).upper() in ("Q", "Z")):
        return "c019"
    if "restrictions" in case or "stalk_dims_v" in case:
        return "c012"
    if "maximal_simplices" in case or ("simplices" in case and "betti" in str(case)):
        return "c013"
    if "signs" in case:
        return "c018"

    return "c011"


def solve(
    case: Mapping[str, Any],
    solver: CohomologySolverPort | None = None,
) -> dict[str, Any]:
    """Unified entrypoint dispatching case payload to the appropriate native solver via domain port."""
    if solver is None:
        solver = get_default_cohomology_solver()
    return solver.solve(case)
