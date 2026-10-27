"""Exact Quantum Stabilizer Tableau Solver for C021 (Q40-R).

Exposes an explicit native Rust stabilizer composition:
1. `pfp.domain.quantum.stabilizer_solver`
2. `pfp.domain.quantum.certificate_checker`
3. `pfp.infrastructure.quantum.dense_checker`

Complete native outcomes are retained; no swarm authorization is implied.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from pfp.domain.ports.stabilizer_port import StabilizerPort
from pfp.domain.quantum.certificate_checker import check_certificate
from pfp.domain.quantum.stabilizer_solver import solve as domain_solve
from pfp.infrastructure.adapters.stabilizer_rust_adapter import (
    StabilizerRustAdapter,
)
from pfp.infrastructure.quantum.dense_checker import verify_dense_spectrum


@dataclass(frozen=True)
class Q40Certificate:
    case_id: str
    status: str  # "SOLVED", "OUT_OF_SCOPE", "UNKNOWN"
    energy: list[int] | None
    degeneracy: int | None
    basis: list[str]
    decomposition: list[dict[str, Any]]
    minimizers: list[int]
    witness: list[str] | None
    refusal_code: str | None
    algebraic_verified: bool
    dense_verified: bool

    def to_canonical_dict(self) -> dict[str, Any]:
        """Converts to exact C021 wire JSON format."""
        if self.status == "SOLVED":
            assert self.energy is not None
            assert self.degeneracy is not None
            return {
                "id": self.case_id,
                "status": "SOLVED",
                "energy": list(self.energy),
                "degeneracy": self.degeneracy,
                "basis": list(self.basis),
                "decomposition": [
                    {
                        "id": d["id"],
                        "mask": d["mask"],
                        "phase": d["phase"],
                    }
                    for d in self.decomposition
                ],
                "minimizers": list(self.minimizers),
            }
        elif self.status == "OUT_OF_SCOPE":
            assert self.witness is not None
            return {
                "id": self.case_id,
                "status": "OUT_OF_SCOPE",
                "witness": sorted(list(self.witness)),
            }
        else:
            return {
                "id": self.case_id,
                "status": "UNKNOWN",
                "refusal_code": str(self.refusal_code or "UNKNOWN"),
            }


class Q40StabilizerSolver:
    """Native result transport with an optional secondary numerical spectrum check."""

    def __init__(self, stabilizer: StabilizerPort | None = None) -> None:
        self._stabilizer = stabilizer if stabilizer is not None else StabilizerRustAdapter()

    @property
    def native_outcomes(self) -> tuple[Mapping[str, Any], ...]:
        return self._stabilizer.native_outcomes

    def validate_case(self, case: Mapping[str, Any]) -> str | None:
        result = domain_solve(case, port=self._stabilizer)
        return result.get("refusal_code") if result.get("status") == "UNKNOWN" else None

    def solve(self, case: Mapping[str, Any]) -> Q40Certificate:
        result = domain_solve(case, port=self._stabilizer)
        case_id = str(case.get("id") or case.get("case_id") or "unnamed")
        status = result.get("status", "UNKNOWN")
        verified = check_certificate(case, result, port=self._stabilizer)
        algebraic_ok = verified.get("verdict") == "PASS"
        dense_ok = False
        if status == "SOLVED" and algebraic_ok:
            dense = verify_dense_spectrum(case, result)
            if dense.get("dense_check") == "FAILED":
                return self._refused(case_id, "SECONDARY_NUMERIC_DISAGREEMENT")
            dense_ok = dense.get("dense_check") == "PASSED"
        if status not in ("SOLVED", "OUT_OF_SCOPE") or not algebraic_ok:
            return self._refused(
                case_id,
                result.get("refusal_code")
                or verified.get("refusal_code")
                or "CERTIFICATE_CHECK_FAILED",
            )
        return Q40Certificate(
            case_id=case_id,
            status=status,
            energy=list(result["energy"]) if status == "SOLVED" else None,
            degeneracy=result["degeneracy"] if status == "SOLVED" else None,
            basis=list(result["basis"]) if status == "SOLVED" else [],
            decomposition=list(result["decomposition"]) if status == "SOLVED" else [],
            minimizers=list(result["minimizers"]) if status == "SOLVED" else [],
            witness=list(result["witness"]) if status == "OUT_OF_SCOPE" else None,
            refusal_code=None,
            algebraic_verified=algebraic_ok,
            dense_verified=dense_ok,
        )

    @staticmethod
    def _refused(case_id: str, code: str) -> Q40Certificate:
        return Q40Certificate(
            case_id=case_id,
            status="UNKNOWN",
            energy=None,
            degeneracy=None,
            basis=[],
            decomposition=[],
            minimizers=[],
            witness=None,
            refusal_code=code,
            algebraic_verified=False,
            dense_verified=False,
        )
