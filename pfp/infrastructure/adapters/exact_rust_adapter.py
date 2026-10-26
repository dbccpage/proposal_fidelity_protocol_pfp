"""Native Rust exact arithmetic & linear algebra adapter.

Bridges the Symbol Game domain ports to omega_engine/crates_rs native implementations
(specifically omega_linear_algebra, omega_homology, omega_holonomy, omega_functional),
providing exact rational linear algebra. Digests use the sorted-key compact ASCII JSON
profile of ``domain/exact/digest.py``, which is not RFC 8785 and refuses floats.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from ...domain.exact.errors import ExactError
from ...domain.exact.poly import Poly
from ...domain.exact.q import Q
from ...domain.ports.exact_ports import (
    ExactDigestPort,
    ExactFunctionalPort,
    ExactHolonomyPort,
    ExactHomologyPort,
    ExactLinearAlgebraPort,
    ExactPharmacyPort,
    Matrix,
)
from ...domain.value_objects.functional_receipt import FunctionalReceipt


def _to_canonical_exact_str(q: Q) -> str:
    if q.den == 1:
        return str(q.num)
    return f"{q.num}/{q.den}"


def _from_canonical_exact_str(s: str) -> Q:
    if "/" in s:
        p, q = s.split("/", 1)
        return Q(int(p), int(q))
    return Q(int(s), 1)


def _matrix_wire(matrix: Matrix) -> list[list[str]]:
    return [[_to_canonical_exact_str(x) for x in row] for row in matrix]


def _as_fraction(value: object) -> object:
    """Domain ``Q`` becomes ``Fraction``; anything else is left for the builder to judge."""
    return Fraction(value.num, value.den) if isinstance(value, Q) else value


class RustExactEngineAdapter(
    ExactLinearAlgebraPort,
    ExactDigestPort,
    ExactHomologyPort,
    ExactHolonomyPort,
    ExactFunctionalPort,
    ExactPharmacyPort,
):
    """Adapter delegating exact mathematical operations to omega_engine/crates_rs."""

    def __init__(self, host: Any | None = None) -> None:
        self._host = host
        self._host_absent_reason = ""
        if self._host is None:
            from ...ffi import get_default_host

            try:
                self._host = get_default_host()
            except FileNotFoundError as exc:
                # A binary that is not built is a state, not a defect: every call
                # needing the host refuses with this reason. Any other exception
                # is a defect and propagates instead of becoming a silent None.
                self._host_absent_reason = str(exc)

    @property
    def has_native_host(self) -> bool:
        return self._host is not None

    def _ensure_host(self) -> Any:
        if self._host is None:
            reason = f" ({self._host_absent_reason})" if self._host_absent_reason else ""
            raise ExactError(
                "HOST_UNAVAILABLE",
                f"Native Rust host required for exact operations{reason}",
            )
        return self._host

    # -- ExactLinearAlgebraPort (omega_linear_algebra) ------------------------
    def determinant(self, matrix: Matrix) -> Q:
        host = self._ensure_host()
        wire = _matrix_wire(matrix)
        outcome = host.exact_determinant(wire)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return _from_canonical_exact_str(val["result"]["determinant"])
            raise ExactError("NATIVE_LINALG_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    def characteristic_polynomial(self, matrix: Matrix) -> Poly:
        host = self._ensure_host()
        wire = _matrix_wire(matrix)
        outcome = host.exact_char_poly(wire)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                coeffs = [_from_canonical_exact_str(c) for c in val["result"]["coeffs"]]
                return Poly(coeffs)
            raise ExactError("NATIVE_LINALG_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    def rank(self, matrix: Matrix) -> int:
        host = self._ensure_host()
        wire = _matrix_wire(matrix)
        outcome = host.exact_rank(wire)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return int(val["result"]["rank"])
            raise ExactError("NATIVE_LINALG_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    def is_positive_definite(self, matrix: Matrix) -> bool:
        host = self._ensure_host()
        wire = _matrix_wire(matrix)
        outcome = host.exact_is_positive_definite(wire)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return bool(val["result"]["is_positive_definite"])
            raise ExactError("NATIVE_LINALG_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    def leading_minors(self, matrix: Matrix) -> tuple[Q, ...]:
        host = self._ensure_host()
        wire = _matrix_wire(matrix)
        outcome = host.exact_leading_minors(wire)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return tuple(_from_canonical_exact_str(m) for m in val["result"]["leading_minors"])
            raise ExactError("NATIVE_LINALG_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    # -- ExactDigestPort (sorted-key compact ASCII JSON; not RFC 8785) --------
    def canonical_json(self, value: object) -> bytes:
        from ...domain.exact.digest import canonical_json as domain_canonical_json

        return domain_canonical_json(value)

    def sha256(self, data: bytes) -> bytes:
        return hashlib.sha256(data).digest()

    def digest_of(self, value: object) -> bytes:
        return self.sha256(self.canonical_json(value))

    # -- ExactHomologyPort (omega_homology) -----------------------------------
    def compute_betti_numbers(self, complex_descriptor: object) -> list[int]:
        raise NotImplementedError("omega_homology delegation")

    def verify_boundary_law(self, complex_descriptor: object) -> bool:
        # Anything but a simplex list used to return True unchecked: a verdict
        # of "lawful" for an object nobody looked at.
        if not isinstance(complex_descriptor, (list, tuple)):
            raise ExactError(
                "INVALID_COMPLEX_DESCRIPTOR",
                f"boundary law needs a simplex list, got {type(complex_descriptor).__name__}",
            )
        report = self.verify_simplicial_boundary_law(complex_descriptor)
        return bool(report.get("boundary_law_verified", False))

    def verify_boundary_closed(self, faces: Sequence[Sequence[tuple[int, int, int]]]) -> bool:
        host = self._ensure_host()
        outcome = host.exact_verify_boundary_closed(faces)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return bool(val["result"]["boundary_closed"])
            raise ExactError("NATIVE_HOMOLOGY_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    def verify_simplicial_boundary_law(
        self, simplices: Sequence[Sequence[int]]
    ) -> Mapping[str, Any]:
        host = self._ensure_host()
        outcome = host.exact_verify_simplicial_boundary_law(simplices)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return val["result"]
            raise ExactError("NATIVE_HOMOLOGY_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    # -- ExactHolonomyPort (omega_holonomy) -----------------------------------
    def path_holonomy(self, connection: object, path: Sequence[str]) -> object:
        raise NotImplementedError("omega_holonomy delegation")

    def loop_curvature(self, connection: object, loop: Sequence[str]) -> object:
        raise NotImplementedError("omega_holonomy delegation")

    def ordered_loop_product(
        self,
        tables: Sequence[Sequence[Sequence[Q]]],
        word: Sequence[tuple[int, bool]],
    ) -> Sequence[Sequence[Q]]:
        host = self._ensure_host()
        tables_wire = [_matrix_wire(t) for t in tables]
        outcome = host.exact_ordered_loop_product(tables_wire, word)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                raw_prod = val["result"]["product"]
                return tuple(tuple(_from_canonical_exact_str(c) for c in row) for row in raw_prod)
            raise ExactError("NATIVE_HOLONOMY_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    def is_ordered_closure(
        self,
        tables: Sequence[Sequence[Sequence[Q]]],
        word: Sequence[tuple[int, bool]],
    ) -> bool:
        host = self._ensure_host()
        tables_wire = [_matrix_wire(t) for t in tables]
        outcome = host.exact_is_ordered_closure(tables_wire, word)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return bool(val["result"]["is_closure"])
            raise ExactError("NATIVE_HOLONOMY_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    # -- ExactFunctionalPort (omega_functional) -------------------------------
    def evaluate(
        self,
        d0: Sequence[Sequence[Fraction]],
        d1: Sequence[Sequence[Fraction]],
        residual: Sequence[Fraction],
    ) -> FunctionalReceipt:
        """Phi1, Gamma2 and the class from omega_functional; Python computes none of them."""
        from omega_engine_operating_system.adapters.rust_host.theory_requests import (
            exact_wire,
            functional_evaluate_payload,
        )

        host = self._ensure_host()
        built = functional_evaluate_payload(
            [[_as_fraction(x) for x in row] for row in d0],
            [[_as_fraction(x) for x in row] for row in d1],
            [_as_fraction(x) for x in residual],
        )
        if built.is_err:
            refusal = built.unwrap_err()
            raise ExactError(refusal.code, refusal.message)
        outcome = host.functional_evaluate(built.unwrap())
        if not outcome.is_ok:
            raise ExactError("FFI_CROSSING_FAILED", str(outcome.unwrap_err()))
        record = outcome.unwrap()
        if not record.get("success"):
            error = str(record.get("error"))
            raise ExactError(error.split(":", 1)[0], error)
        wire = record["result"]

        def exact(text: str) -> Fraction:
            return Fraction(exact_wire(text))

        return FunctionalReceipt(
            input_digest=wire["input_digest"],
            phi1=exact(wire["phi1"]),
            gamma2=exact(wire["gamma2"]),
            diagnostic_class=wire["diagnostic_class"],
            dual_witness=tuple(exact(v) for v in wire["dual_witness"]),
            primal_residual=tuple(exact(v) for v in wire["primal_residual"]),
            second_stage_repairs=wire["second_stage_repairs"],
            authority_effect=wire["authority_effect"],
        )

    def verify_phi1_certificate(self, certificate: object) -> bool:
        raise NotImplementedError("omega_functional delegation")

    def verify_gamma2_certificate(self, certificate: object) -> bool:
        raise NotImplementedError("omega_functional delegation")

    # -- ExactPharmacyPort (omega_prompt_civilization) -----------------------
    def pharmacy_detect(
        self, candidate_json: str, context: str = ""
    ) -> Mapping[str, Any]:
        """Runs the 12 failure-class detector battery on a candidate turn."""
        host = self._ensure_host()
        ctx_payload = {"prompt": context} if context else None
        outcome = host.pharmacy_detect(candidate_json, context=ctx_payload)
        if not outcome.is_ok:
            refusal = outcome.unwrap_err()
            raise ExactError("FFI_CROSSING_FAILED", str(refusal))
        record = outcome.unwrap()
        if not record.get("success"):
            error = str(record.get("error"))
            raise ExactError(error.split(":", 1)[0], error)
        return record.get("result", {})

    # -- Retraction Turn Machine & Loop (omega_symbol_game::epics) ------------
    def retraction_turn(
        self,
        before: Mapping[str, int],
        after: Mapping[str, int],
        candidate: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """Dispatch single retraction turn descent validation to native Rust host."""
        host = self._ensure_host()
        payload: dict[str, Any] = {"before": dict(before), "after": dict(after)}
        if candidate is not None:
            payload["candidate"] = dict(candidate)
        outcome = host.invoke("retraction_turn", payload)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return val["result"]
            raise ExactError("NATIVE_RETRACTION_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))

    def retraction_loop(
        self,
        intake: Mapping[str, int],
        candidates: Sequence[Mapping[str, Any]],
        open_obligations: int = 0,
    ) -> Mapping[str, Any]:
        """Dispatch multi-turn retraction loop to native Rust 7-act engine."""
        host = self._ensure_host()
        payload = {
            "intake": dict(intake),
            "candidates": [dict(c) for c in candidates],
            "open_obligations": open_obligations,
        }
        outcome = host.invoke("retraction_loop", payload)
        if hasattr(outcome, "is_ok") and outcome.is_ok:
            val = outcome.unwrap()
            if val.get("success") and val.get("result"):
                return val["result"]
            raise ExactError("NATIVE_RETRACTION_REFUSAL", str(val.get("error")))
        raise ExactError("FFI_CROSSING_FAILED", str(outcome))


__all__ = ["RustExactEngineAdapter"]
