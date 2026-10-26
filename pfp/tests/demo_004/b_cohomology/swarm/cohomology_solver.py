"""Legacy C011 façade over the shared solver and certificate-checking ports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Sequence

from omega_engine_pfp.domain.cohomology.certificate_checker import check_certificate
from omega_engine_pfp.domain.cohomology.solver import solve
from omega_engine_pfp.domain.ports.cohomology_port import CohomologySolverPort


def _wire(value: Fraction) -> str:
    return str(value)


@dataclass(frozen=True)
class CohomologyCertificate:
    """Preserve the owning solver's complete result, including refusal evidence."""

    payload: Mapping[str, Any]
    independent_verified: bool

    @property
    def status(self) -> str:
        return str(self.payload.get("status", "UNKNOWN"))

    @property
    def native_verified(self) -> bool:
        outcome = self.payload.get("native_outcome", {})
        result = outcome.get("result", {}) if isinstance(outcome, Mapping) else {}
        return self.status == "SOLVED" and result.get("certificate_verified") is True

    @property
    def phi1(self) -> Fraction:
        return Fraction(self.payload["phi1"])

    def to_canonical_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    def to_json(self) -> str:
        return json.dumps(self.to_canonical_dict(), sort_keys=True)


class CohomologySolver:
    """Compatibility API; it owns no solver, host crossing, or proofreading verdict."""

    def __init__(
        self,
        host: Any = None,
        proofreader: Any = None,
        *,
        solver: CohomologySolverPort | None = None,
    ) -> None:
        self._solver = solver
        self._legacy_host = host
        self._legacy_proofreader = proofreader

    def solve(self, case: Mapping[str, Any], budget_tokens: int = 1000) -> CohomologyCertificate:
        request = {**case, "challenge": "c011"}
        # Host/proofreader injection used to create a second execution path outside
        # the shared port. Require composition at the port instead.
        if self._legacy_host is not None or self._legacy_proofreader is not None:
            result = {
                "status": "UNKNOWN",
                "refusal": "EXECUTION_UNAVAILABLE",
                "detail": "Inject the owning CohomologySolverPort; direct host execution is unavailable.",
            }
        else:
            try:
                result = solve(request, solver=self._solver)
            except RuntimeError as exc:
                result = {
                    "status": "UNKNOWN",
                    "refusal": "EXECUTION_UNAVAILABLE",
                    "detail": str(exc),
                }
        checked = check_certificate(request, result)
        return CohomologyCertificate(payload=result, independent_verified=checked.passed)


def verify_independent_certificate(
    nodes: Sequence[str],
    edges: Sequence[tuple[str, str]],
    claims: Mapping[tuple[str, str], Fraction],
    weights: Mapping[tuple[str, str], Fraction],
    potential: Mapping[str, Fraction],
    repair: Mapping[str, Fraction],
    dual: Mapping[str, Fraction],
    phi1: Fraction,
) -> tuple[bool, Fraction]:
    """Compatibility wire conversion; the shared checker owns the proof checks."""
    case = {
        "challenge": "c011",
        "nodes": list(nodes),
        "edges": [list(edge) for edge in edges],
        "claims": {f"{u}->{v}": _wire(value) for (u, v), value in claims.items()},
        "weights": {f"{u}->{v}": _wire(value) for (u, v), value in weights.items()},
    }
    result = {
        "status": "SOLVED",
        "phi1": _wire(phi1),
        "potential": {key: _wire(value) for key, value in potential.items()},
        "repair": {key: _wire(value) for key, value in repair.items()},
        "dual": {key: _wire(value) for key, value in dual.items()},
    }
    checked = check_certificate(case, result)
    return checked.passed, Fraction(0) if checked.passed else Fraction(-1)
