"""Transport for the native cohomology operations currently exposed by the host.

C011 has a native L1 operation. The remaining challenge solvers are unavailable
through this port and must not manufacture mathematical certificates. A C011
answer is SOLVED only when the host reports ``certificate_verified: true``;
an unverified certificate is the typed refusal ``NATIVE_CERTIFICATE_NOT_VERIFIED``.
AuthorityEffect: None.
"""
from __future__ import annotations

from typing import Any, Mapping

from ...domain.cohomology.solver import detect_challenge
from ...domain.cohomology.validation import exact_fraction, parse_c011_case, scope_violation
from ...domain.ports.cohomology_port import CohomologySolverPort
from ...ffi import RustSymbolGameHost, get_default_host


def _unknown(reason: str, detail: str) -> dict[str, Any]:
    return {"status": "UNKNOWN", "refusal": reason, "detail": detail}


class RustCohomologySolverAdapter(CohomologySolverPort):
    """Validate wire shapes, invoke the existing host, and retain its outcome."""

    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host

    @property
    def host(self) -> RustSymbolGameHost:
        if self._host is None:
            self._host = get_default_host()
        return self._host

    def solve(self, case: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(case, Mapping):
            return _unknown("MALFORMED_INPUT", "case must be an object")
        cid = detect_challenge(case)
        if cid.isdigit():
            cid = f"c{int(cid):03d}"
        normalized = dict(case, challenge=cid)
        if cid in {"c011", "c012"}:
            try:
                witness = scope_violation(normalized)
            except (ValueError, TypeError, KeyError) as exc:
                return _unknown("MALFORMED_INPUT", str(exc))
            if witness is not None:
                return {"status": "OUT_OF_SCOPE", "witness": witness}
        if cid != "c011":
            return _unknown("NATIVE_OPERATION_UNAVAILABLE", f"No certified native solver is exposed for {cid}")
        return self._solve_c011(normalized)

    def _solve_c011(self, case: Mapping[str, Any]) -> dict[str, Any]:
        nodes, edges, claims, weights = parse_c011_case(case)
        keys = [f"{u}->{v}" for u, v in edges]
        indices = {node: i for i, node in enumerate(nodes)}
        matrix = [["0"] * len(nodes) for _ in edges]
        for row, (u, v) in zip(matrix, edges):
            row[indices[u]] = "-1"
            row[indices[v]] = "1"
        try:
            result = self.host.exact_solve_l1_primal_dual(
                matrix,
                [str(claims.get(key, 0)) for key in keys],
                [str(weights.get(key, 1)) for key in keys],
            )
        except Exception as exc:
            return _unknown("NATIVE_EXECUTION_UNAVAILABLE", f"{type(exc).__name__}: {exc}")
        if result.is_err:
            refusal = result.unwrap_err()
            return _unknown(str(getattr(refusal, "code", "NATIVE_REFUSAL")), str(getattr(refusal, "message", refusal)))
        outcome = result.unwrap()
        if isinstance(outcome, Mapping) and outcome.get("success") is False:
            # The seam returns a dispatched native refusal as Ok; keep its detail.
            return dict(
                _unknown("NATIVE_REFUSAL", str(outcome.get("error"))),
                native_outcome=outcome,
            )
        try:
            if not isinstance(outcome, Mapping) or not isinstance(outcome.get("result"), Mapping):
                raise ValueError("Native outcome must contain a result object")
            payload = outcome["result"]
            verified = payload["certificate_verified"]
            if type(verified) is not bool:
                raise ValueError("certificate_verified must be a Boolean")
            if verified is not True:
                # omega_functional rejected the host's own certificate: the
                # numbers are not a solution and must not be reported as one.
                return dict(
                    _unknown(
                        "NATIVE_CERTIFICATE_NOT_VERIFIED",
                        "omega_functional did not verify the primal-dual certificate",
                    ),
                    native_outcome=outcome,
                )
            alpha, residual, dual = payload["alpha"], payload["residual"], payload["dual_witness"]
            if any(not isinstance(vector, (list, tuple)) for vector in (alpha, residual, dual)):
                raise ValueError("Native L1 witnesses must be vectors")
            if len(alpha) != len(nodes) or len(residual) != len(edges) or len(dual) != len(edges):
                raise ValueError("Native L1 witness dimensions do not match the input")
            solution = {
                "status": "SOLVED",
                "phi1": str(exact_fraction(payload["phi1"])),
                "potential": {node: str(exact_fraction(value)) for node, value in zip(nodes, alpha)},
                "repair": {key: str(exact_fraction(value)) for key, value in zip(keys, residual)},
                "dual": {key: str(exact_fraction(value)) for key, value in zip(keys, dual)},
                "native_outcome": outcome,
            }
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            return dict(_unknown("INVALID_NATIVE_RESPONSE", str(exc)), native_outcome=outcome)
        return solution
