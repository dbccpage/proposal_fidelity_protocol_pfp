"""Infrastructure adapter implementing IWitnessVerificationPort.

AuthorityEffect: None.
Clean Architecture Layer: Infrastructure Adapter.
Provides dual-mode acceleration:
1. PyO3 in-process C-extension bridge if compiled (omega_witness_rs).
2. Pure Python exact rational reference fallback when C-extension is unavailable.
Strictly converts process failures, syntax errors, and float violations into Err(Refusal).
"""

from __future__ import annotations

import hashlib
import logging

from omega_engine_operations.domain.ports.witness_port import (
    CochainComplex,
    ExactRational,
    FloatForbiddenError,
    IWitnessVerificationPort,
    WitnessVerificationRequest,
    WitnessVerificationResult,
)
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

from .ffi import load_native_witness_module

logger = logging.getLogger(__name__)


def _compute_sha256(content: str | bytes) -> str:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(raw).hexdigest()


_COMPLEX_LOCUS = "witness_adapter._verify_complex_witness"


def _complex_refusal(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code=code, message=message, locus=_COMPLEX_LOCUS))


def _parse_degree_text(degree_k_val: str) -> Result[ExactRational, Refusal]:
    try:
        return Ok(ExactRational.from_str(degree_k_val))
    except Exception as exc:
        return _complex_refusal(
            "INVALID_DEGREE_K",
            f"Invalid degree_k rational string '{degree_k_val}': {exc}",
        )


def _parse_degree_bound(degree_k_val: object) -> Result[ExactRational, Refusal]:
    if degree_k_val is None:
        return Ok(ExactRational(1, 1))
    if type(degree_k_val) is int:
        return Ok(ExactRational(degree_k_val, 1))
    if isinstance(degree_k_val, ExactRational):
        return Ok(degree_k_val)
    if isinstance(degree_k_val, str):
        return _parse_degree_text(degree_k_val)
    return _complex_refusal(
        "INVALID_DEGREE_K",
        f"Unsupported degree_k type: {type(degree_k_val).__name__}",
    )


def _ambiguous_c0_basis(
    request: WitnessVerificationRequest, c0_dim: int
) -> Err[Refusal] | None:
    if len(request.boundary_cochains) != c0_dim:
        return None
    if all(str(index) in request.boundary_cochains for index in range(c0_dim)):
        return None
    return _complex_refusal(
        "AMBIGUOUS_C0_BASIS",
        (
            "Complex witness cochains must use every numeric basis key "
            f"from 0 through {max(c0_dim - 1, 0)}"
        ),
    )


def _string_matrix(rows: tuple[tuple[ExactRational, ...], ...]) -> list[list[str]]:
    return [[entry.to_string() for entry in row] for row in rows]


def _reference_chain_law_holds(complex_obj: CochainComplex, c0_dim: int, c1_dim: int) -> bool:
    """Return whether every entry of d1 composed with d0 is zero."""
    for d1_row in complex_obj.d1:
        for c_idx in range(c0_dim):
            comp_val = ExactRational(0, 1)
            for k_idx in range(c1_dim):
                comp_val = comp_val + (d1_row[k_idx] * complex_obj.d0[k_idx][c_idx])
            if not comp_val.is_zero:
                return False
    return True


def _reference_cycle(
    complex_obj: CochainComplex,
    x_vec: list[ExactRational],
    c0_dim: int,
    c1_dim: int,
) -> tuple[list[ExactRational], bool]:
    y_vec: list[ExactRational] = []
    is_cycle = True
    for i in range(c1_dim):
        y_i = ExactRational(0, 1)
        for j in range(c0_dim):
            y_i = y_i + (complex_obj.d0[i][j] * x_vec[j])
        y_vec.append(y_i)
        if not y_i.is_zero:
            is_cycle = False
    return y_vec, is_cycle


def _reference_l1_norm(x_vec: list[ExactRational]) -> ExactRational:
    l1_norm = ExactRational(0, 1)
    for val in x_vec:
        abs_val = ExactRational(abs(val.numerator), val.denominator)
        l1_norm = l1_norm + abs_val
    return l1_norm


def _complex_digest_payload(
    request: WitnessVerificationRequest,
    c0_dim: int,
    c1_dim: int,
    c2_dim: int,
    k_rat: ExactRational,
    valid_suffix: str,
) -> str:
    normalized_items = sorted(
        (key, value.to_string()) for key, value in request.boundary_cochains.items()
    )
    joined = ";".join(f"{key}={value}" for key, value in normalized_items)
    return (
        f"{request.carrier_hash}:complex={c0_dim},{c1_dim},{c2_dim}:"
        + joined
        + f":k={k_rat.to_string()}:{valid_suffix}"
    )


def _dimension_mismatch_result(
    request: WitnessVerificationRequest,
    c0_dim: int,
    c1_dim: int,
    c2_dim: int,
    k_rat: ExactRational,
    actual_dim: int,
) -> Ok[WitnessVerificationResult]:
    payload = _complex_digest_payload(
        request, c0_dim, c1_dim, c2_dim, k_rat, "valid=false"
    )
    return Ok(
        WitnessVerificationResult(
            is_valid=False,
            residual_digest=_compute_sha256(payload),
            details={
                "engine": "python_reference",
                "mode": "complex_exact_rational",
                "is_valid": False,
                "dimension_mismatch": True,
                "expected_c0_dim": c0_dim,
                "actual_dim": actual_dim,
                "is_cycle": False,
                "is_complex_valid": True,
                "norm_valid": False,
                "carrier_hash": request.carrier_hash,
            },
            authority_effect="None",
        )
    )


def _reference_complex_value(
    request: WitnessVerificationRequest,
    complex_obj: CochainComplex,
    k_rat: ExactRational,
) -> Ok[WitnessVerificationResult]:
    c0_dim = complex_obj.c0_dim
    c1_dim = complex_obj.c1_dim
    c2_dim = complex_obj.c2_dim
    actual_dim = len(request.boundary_cochains)
    if actual_dim != c0_dim:
        return _dimension_mismatch_result(
            request, c0_dim, c1_dim, c2_dim, k_rat, actual_dim
        )
    x_vec = [request.boundary_cochains[str(index)] for index in range(c0_dim)]
    is_complex_valid = _reference_chain_law_holds(complex_obj, c0_dim, c1_dim)
    y_vec, is_cycle = _reference_cycle(complex_obj, x_vec, c0_dim, c1_dim)
    l1_norm = _reference_l1_norm(x_vec)
    norm_valid = l1_norm.numerator * k_rat.denominator <= k_rat.numerator * l1_norm.denominator
    is_valid = is_complex_valid and is_cycle and norm_valid
    digest_payload = _complex_digest_payload(
        request,
        c0_dim,
        c1_dim,
        c2_dim,
        k_rat,
        f"valid={str(is_valid).lower()}",
    )
    return Ok(
        WitnessVerificationResult(
            is_valid=is_valid,
            residual_digest=_compute_sha256(digest_payload),
            details={
                "engine": "python_reference",
                "mode": "complex_exact_rational",
                "c0_dim": c0_dim,
                "c1_dim": c1_dim,
                "c2_dim": c2_dim,
                "is_complex_valid": is_complex_valid,
                "is_cycle": is_cycle,
                "cycle_residual": [y.to_string() for y in y_vec],
                "l1_norm": l1_norm.to_string(),
                "degree_k": k_rat.to_string(),
                "norm_valid": norm_valid,
                "is_valid": is_valid,
                "carrier_hash": request.carrier_hash,
            },
            authority_effect="None",
        )
    )


class RustWitnessAdapter(IWitnessVerificationPort):
    """Production adapter bridging Python to the Rust exact witness kernel."""

    def __init__(self, force_fallback: bool = False) -> None:
        self._force_fallback = force_fallback
        self._native_module = None if force_fallback else load_native_witness_module()

    @property
    def is_pyo3_accelerated(self) -> bool:
        return self._native_module is not None and not self._force_fallback

    def verify_witness(
        self,
        request: WitnessVerificationRequest,
    ) -> Result[WitnessVerificationResult, Refusal]:
        """Evaluate witness under PyO3 or fail-closed pure reference implementation."""
        # 1. Authority effect check
        if request.authority_effect != "None":
            return Err(
                Refusal(
                    code="AUTHORITY_ELEVATION_FORBIDDEN",
                    message="Witness verification strictly requires authority_effect == 'None'",
                    locus="witness_adapter.verify_witness",
                )
            )

        # 2. Reject floats across the input boundary
        for edge, rational in request.boundary_cochains.items():
            if isinstance(rational, float):
                return Err(
                    Refusal(
                        code="FLOAT_FORBIDDEN",
                        message=f"Floating-point value {rational} forbidden in exact rational witness",
                        locus=f"boundary_cochains.{edge}",
                    )
                )

        # 3. Route based on complex presence
        if request.complex is not None:
            return self._verify_complex_witness(request)
        return self._verify_flux_witness(request)

    def _verify_flux_witness(
        self,
        request: WitnessVerificationRequest,
    ) -> Result[WitnessVerificationResult, Refusal]:
        """Evaluate 1D boundary cochains flux closure (sum(c_i) == 0)."""
        # PyO3 acceleration
        if self.is_pyo3_accelerated and hasattr(self._native_module, "verify_exact_rational_witness_py"):
            try:
                raw_cochains = {k: v.to_string() for k, v in request.boundary_cochains.items()}
                native_res = self._native_module.verify_exact_rational_witness_py(
                    raw_cochains, request.carrier_hash
                )
                if native_res.get("authority_effect") != "None":
                    return Err(
                        Refusal(
                            code="AUTHORITY_CEILING_VIOLATED",
                            message="Native outcome declared authority effect other than None",
                            locus="witness_adapter._verify_flux_witness",
                        )
                    )
                return Ok(
                    WitnessVerificationResult(
                        is_valid=bool(native_res["is_valid"]),
                        residual_digest=str(native_res["residual_digest"]),
                        details=dict(native_res.get("details", {})),
                        authority_effect="None",
                    )
                )
            except (ValueError, TypeError, RuntimeError) as exc:
                logger.error("Native PyO3 flux verification error: %s", exc, exc_info=True)
                return Err(
                    Refusal(
                        code="NATIVE_EXECUTION_FAILED",
                        message=f"PyO3 native flux verification failed: {exc}",
                        locus="witness_adapter._verify_flux_witness",
                    )
                )
            except Exception as exc:
                logger.error("Unexpected exception in PyO3 native execution: %s", exc, exc_info=True)
                return Err(
                    Refusal(
                        code="NATIVE_EXECUTION_FAILED",
                        message=f"Unexpected native PyO3 failure: {exc}",
                        locus="witness_adapter._verify_flux_witness",
                    )
                )

        # Pure Reference Evaluation (Fail-Closed Reference Model)
        try:
            total_flux = ExactRational(0, 1)
            for rational in request.boundary_cochains.values():
                total_flux = total_flux + rational

            is_valid = total_flux.is_zero

            normalized_items = sorted(
                (k, v.to_string()) for k, v in request.boundary_cochains.items()
            )
            digest_payload = f"{request.carrier_hash}:" + ";".join(
                f"{k}={v}" for k, v in normalized_items
            )
            residual_digest = _compute_sha256(digest_payload)

            details = {
                "edge_count": len(request.boundary_cochains),
                "total_flux": total_flux.to_string(),
                "is_closed": is_valid,
                "carrier_hash": request.carrier_hash,
                "engine": "python_reference",
                "mode": "flux_exact_rational",
            }

            return Ok(
                WitnessVerificationResult(
                    is_valid=is_valid,
                    residual_digest=residual_digest,
                    details=details,
                    authority_effect="None",
                )
            )
        except ZeroDivisionError:
            return Err(
                Refusal(
                    code="DIVISION_BY_ZERO",
                    message="Zero denominator encountered during rational witness evaluation",
                    locus="witness_adapter._verify_flux_witness",
                )
            )
        except FloatForbiddenError as exc:
            return Err(
                Refusal(
                    code="FLOAT_FORBIDDEN",
                    message=str(exc),
                    locus="witness_adapter._verify_flux_witness",
                )
            )
        except Exception as exc:
            return Err(
                Refusal(
                    code="WITNESS_VERIFICATION_FAILED",
                    message=f"Internal evaluation error: {exc}",
                    locus="witness_adapter._verify_flux_witness",
                )
            )

    def _native_complex_ready(self) -> bool:
        return self.is_pyo3_accelerated and hasattr(
            self._native_module, "verify_exact_rational_complex_py"
        )

    def _verify_complex_native(
        self,
        request: WitnessVerificationRequest,
        complex_obj: CochainComplex,
        k_rat: ExactRational,
    ) -> Result[WitnessVerificationResult, Refusal]:
        try:
            raw_cochains = {
                key: value.to_string() for key, value in request.boundary_cochains.items()
            }
            native_res = self._native_module.verify_exact_rational_complex_py(
                raw_cochains,
                request.carrier_hash,
                complex_obj.c0_dim,
                complex_obj.c1_dim,
                complex_obj.c2_dim,
                _string_matrix(complex_obj.d0),
                _string_matrix(complex_obj.d1),
                k_rat.to_string(),
            )
            if native_res.get("authority_effect") != "None":
                return _complex_refusal(
                    "AUTHORITY_CEILING_VIOLATED",
                    "Native outcome declared authority effect other than None",
                )
            return Ok(
                WitnessVerificationResult(
                    is_valid=bool(native_res["is_valid"]),
                    residual_digest=str(native_res["residual_digest"]),
                    details=dict(native_res.get("details", {})),
                    authority_effect="None",
                )
            )
        except (ValueError, TypeError, RuntimeError) as exc:
            logger.error("Native PyO3 complex verification error: %s", exc, exc_info=True)
            return _complex_refusal(
                "NATIVE_EXECUTION_FAILED",
                f"PyO3 native complex verification failed: {exc}",
            )
        except Exception as exc:
            logger.error(
                "Unexpected exception in native PyO3 complex verification: %s",
                exc,
                exc_info=True,
            )
            return _complex_refusal(
                "NATIVE_EXECUTION_FAILED",
                f"Unexpected native PyO3 failure: {exc}",
            )

    def _verify_complex_reference(
        self,
        request: WitnessVerificationRequest,
        complex_obj: CochainComplex,
        k_rat: ExactRational,
    ) -> Result[WitnessVerificationResult, Refusal]:
        try:
            return _reference_complex_value(request, complex_obj, k_rat)
        except ZeroDivisionError:
            return _complex_refusal(
                "DIVISION_BY_ZERO",
                "Zero denominator encountered during rational complex verification",
            )
        except FloatForbiddenError as exc:
            return _complex_refusal("FLOAT_FORBIDDEN", str(exc))
        except Exception as exc:
            return _complex_refusal(
                "WITNESS_VERIFICATION_FAILED",
                f"Internal complex evaluation error: {exc}",
            )

    def _verify_complex_witness(
        self,
        request: WitnessVerificationRequest,
    ) -> Result[WitnessVerificationResult, Refusal]:
        """Evaluate candidate cycle d0*x=0, chain law d1*d0=0, and norm ||x||_1 <= k."""
        complex_obj = request.complex
        assert complex_obj is not None
        parsed = _parse_degree_bound(getattr(request, "degree_k", None))
        if parsed.is_err:
            return parsed
        basis_refusal = _ambiguous_c0_basis(request, complex_obj.c0_dim)
        if basis_refusal is not None:
            return basis_refusal
        k_rat = parsed.unwrap()
        if self._native_complex_ready():
            return self._verify_complex_native(request, complex_obj, k_rat)
        return self._verify_complex_reference(request, complex_obj, k_rat)
