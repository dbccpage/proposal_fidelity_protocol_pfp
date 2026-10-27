"""Concrete infrastructure prime descent coordinator adapter for Adversary Swarm.

Wires the native Rust core_wdp::prime_algos PrimeDescentCoordinator via the OEOS
process seam in core_symbol_game. Every execution returns a typed
PrimeDescentReceiptV1 over the Result monad; if no host is bound or available,
returns honest NOT_MEASURED.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from operations.domain.rop.result import Err, Ok, Refusal, Result
from pfp.ffi import RustSymbolGameHost, get_default_host

from ..domain.evidence import (
    MeasurementStatus,
    PrimeDescentReceiptV1,
    parse_exact_rational,
)
from ..domain.network import Network
from ..domain.ports import PrimeDescentPort

_LOCUS = "adversary.infrastructure.prime_descent_adapter"
_BACKEND = "rust_exact_core_prime_algos"


class PrimeDescentAdapter(PrimeDescentPort):
    """Native Rust PrimeDescentCoordinator adapter."""

    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host

    def get_host(self) -> RustSymbolGameHost | None:
        if self._host is not None:
            return self._host
        try:
            return get_default_host()
        except (FileNotFoundError, OSError, RuntimeError, ValueError):
            return None

    def execute_descent(
        self,
        *,
        run_id: str,
        carrier_network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any] | Sequence[int],
        max_steps: int = 64,
        grant: Mapping[str, Any] | None = None,
    ) -> Result[PrimeDescentReceiptV1, Refusal]:
        """Execute prime descent coordination through native Rust FFI."""
        node_idx = {n: i for i, n in enumerate(carrier_network.nodes)}
        num_vertices = len(carrier_network.nodes)

        carrier_edges = [
            {"tail": node_idx[u], "head": node_idx[v], "weight": 1}
            for u, v in carrier_network.edges
        ]
        carrier_faces = [
            [node_idx[u], node_idx[v], node_idx[w]]
            for u, v, w in carrier_network.faces
            if u in node_idx and v in node_idx and w in node_idx
        ]

        carrier_wire = {
            "num_vertices": num_vertices,
            "edges": carrier_edges,
            "faces": carrier_faces,
        }

        try:
            raw_values = (
                [initial_cochain.get(edge, 0) for edge in carrier_network.edges]
                if isinstance(initial_cochain, Mapping) else list(initial_cochain)
            )
            if len(raw_values) != len(carrier_network.edges):
                raise ValueError("cochain length differs from edge count")
            parsed_values = [parse_exact_rational(value) for value in raw_values]
            if any(value.denominator != 1 for value in parsed_values):
                raise ValueError("cochain values must be exact integers")
            if type(max_steps) is not int or max_steps < 0:
                raise ValueError("max_steps must be a non-negative exact integer")
            omega_vals = [value.numerator for value in parsed_values]
        except (ValueError, TypeError) as exc:
            return Ok(PrimeDescentReceiptV1.not_measured(
                f"INEXACT_CARRIER_COCHAIN: {exc}", backend=_BACKEND, run_id=run_id,
            ))

        host = self.get_host()
        if host is None:
            return Ok(
                PrimeDescentReceiptV1.not_measured(
                    "NATIVE_HOST_UNAVAILABLE: the core_symbol_game host binary is not built",
                    backend=_BACKEND,
                    run_id=run_id,
                )
            )

        res = host.prime_descent(
            run_id=run_id,
            carrier=carrier_wire,
            omega=omega_vals,
            max_steps=max_steps,
            grant=grant,
        )
        if not res.is_ok:
            return Err(res.unwrap_err())

        data = res.unwrap()
        if data.get("success") is not True or type(data.get("result")) is not dict:
            return Ok(
                PrimeDescentReceiptV1.not_measured(
                    f"NATIVE_DESCENT_REFUSED: {data.get('error')!r}",
                    backend=_BACKEND,
                    run_id=run_id,
                )
            )

        payload = dict(data["result"])
        try:
            phi1 = parse_exact_rational(payload["phi1"])
            gamma2 = parse_exact_rational(payload["gamma2"])
        except (KeyError, ValueError, TypeError) as exc:
            return Ok(
                PrimeDescentReceiptV1.not_measured(
                    f"MALFORMED_NATIVE_OUTCOME: failed to parse rational defects: {exc}",
                    backend=_BACKEND,
                    run_id=run_id,
                )
            )

        try:
            if payload.get("run_id") != run_id:
                raise ValueError("native run identity mismatch")
            if payload.get("authority_effect") != "None":
                raise ValueError("native authority effect must be None")
            if payload.get("terminal_status") != "DIAGNOSTIC_ONLY" or payload.get("laws_passed") is not False:
                raise ValueError("unverified terminalization or law-check claim")
            receipt = PrimeDescentReceiptV1(
                status=MeasurementStatus.MEASURED,
                backend=_BACKEND,
                run_id=run_id,
                letters=payload["letters"],
                terminal_status=payload["terminal_status"],
                phi1=phi1,
                gamma2=gamma2,
                b1_over_q=payload["b1_over_q"],
                laws_passed=False,
                authority_effect="None",
                reason="Prime 002 law/terminalization integration is unavailable",
            )
        except (KeyError, ValueError, TypeError) as exc:
            return Ok(PrimeDescentReceiptV1.not_measured(
                f"MALFORMED_NATIVE_OUTCOME: {exc}", backend=_BACKEND, run_id=run_id,
            ))
        return Ok(receipt)


__all__ = ["PrimeDescentAdapter"]
