"""Prompt-to-Cochain execution and evaluation domain model.

Architecture Review 16 §3–§4.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_pfp.domain.ports.prompt_cochain_port import PromptCochainHost


def _decode_u32_bigint_limbs(sign_val: Any, digits: Sequence[Any]) -> int:
    if type(sign_val) is not int:
        raise TypeError("Bigint sign must be an exact integer")
    if sign_val not in {-1, 0, 1}:
        raise ValueError("Bigint sign must be -1, 0 or 1")
    total = 0
    for i, digit in enumerate(digits):
        if type(digit) is not int:
            raise TypeError("Bigint limbs must be exact uint32 integers")
        if not 0 <= digit < 2**32:
            raise ValueError("Bigint limb is outside the uint32 range")
        total += digit << (32 * i)
    if sign_val == 0 and total != 0:
        raise ValueError("Zero bigint sign cannot accompany a nonzero magnitude")
    return sign_val * total


def _parse_bigint(val: Any) -> int:
    """Parse a num_bigint BigInt serialized as [sign, [u32_digits]] or exact int/str."""
    match val:
        case bool():
            raise TypeError(f"Invalid bigint type: bool ({val!r}) not allowed")
        case float():
            raise TypeError(f"Invalid bigint type: float ({val!r}) not allowed")
        case int():
            return val
        case str() as s:
            stripped = s.strip()
            if not re.fullmatch(r"[+-]?\d+", stripped):
                raise ValueError(f"Invalid bigint string: {val!r}")
            return int(stripped)
        case [sign, list() | tuple() as digits]:
            return _decode_u32_bigint_limbs(sign, digits)
        case [single]:
            return _parse_bigint(single)
        case _:
            raise TypeError(
                f"Invalid bigint type or value: {type(val).__name__} ({val!r})"
            )


def _parse_fraction_str(raw: str) -> Fraction:
    s = raw.strip()
    if "/" not in s:
        if re.fullmatch(r"[+-]?\d+", s):
            return Fraction(int(s), 1)
        raise ValueError(
            f"Invalid rational string format (floats and non-integers not allowed): {raw!r}"
        )
    parts = s.split("/")
    if (
        len(parts) == 2
        and re.fullmatch(r"[+-]?\d+", parts[0].strip())
        and re.fullmatch(r"[+-]?\d+", parts[1].strip())
    ):
        numer = int(parts[0].strip())
        denom = int(parts[1].strip())
        if denom == 0:
            raise ZeroDivisionError(f"Denominator cannot be zero: {raw!r}")
        return Fraction(numer, denom)
    raise ValueError(
        f"Invalid rational string format (floats and non-integers not allowed): {raw!r}"
    )


def _parse_fraction(val: Any) -> Fraction:
    """Parse a rational value into an exact Python Fraction fail-closed."""
    match val:
        case bool():
            raise TypeError(f"Invalid rational type: bool ({val!r}) not allowed")
        case float():
            raise TypeError(f"Invalid rational type: float ({val!r}) not allowed")
        case Fraction():
            return val
        case int():
            return Fraction(val, 1)
        case str() as s:
            return _parse_fraction_str(s)
        case [n_raw, d_raw]:
            numer = _parse_bigint(n_raw)
            denom = _parse_bigint(d_raw)
            if denom == 0:
                raise ZeroDivisionError(
                    f"Denominator cannot be zero in rational tuple: {val!r}"
                )
            return Fraction(numer, denom)
        case {"numer": n_raw, "denom": d_raw}:
            numer = _parse_bigint(n_raw)
            denom = _parse_bigint(d_raw)
            if denom == 0:
                raise ZeroDivisionError(
                    f"Denominator cannot be zero in rational dict: {val!r}"
                )
            return Fraction(numer, denom)
        case _:
            raise TypeError(
                f"Unsupported rational value type or format: {type(val).__name__} ({val!r})"
            )


def _fraction_to_wire(val: Any) -> str:
    """Format a rational value as an exact rational string for wire transfer."""
    frac = _parse_fraction(val)
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


@dataclass(frozen=True)
class PromptCellComplex:
    """Oriented finite cell complex C^0 = Q^V -> C^1 = Q^E -> C^2 = Q^F."""

    v_count: int
    e_count: int
    f_count: int
    d0_matrix: tuple[tuple[Fraction, ...], ...]
    d1_matrix: tuple[tuple[Fraction, ...], ...] = ()
    source_bytes_hash: str | None = None

    def __post_init__(self) -> None:
        if self.v_count < 0 or self.e_count < 0 or self.f_count < 0:
            raise ValueError("Cell complex dimensions must be non-negative")
        if len(self.d0_matrix) != self.e_count:
            raise ValueError(
                f"d0 matrix row count {len(self.d0_matrix)} != e_count {self.e_count}"
            )
        for r, row in enumerate(self.d0_matrix):
            if len(row) != self.v_count:
                raise ValueError(
                    f"d0 matrix row {r} length {len(row)} != v_count {self.v_count}"
                )
        if self.f_count > 0:
            if len(self.d1_matrix) != self.f_count:
                raise ValueError(
                    f"d1 matrix row count {len(self.d1_matrix)} != f_count {self.f_count}"
                )
            for r, row in enumerate(self.d1_matrix):
                if len(row) != self.e_count:
                    raise ValueError(
                        f"d1 matrix row {r} length {len(row)} != e_count {self.e_count}"
                    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to wire dictionary for RustSymbolGameHost invocation."""
        d0_wire = [[_fraction_to_wire(x) for x in row] for row in self.d0_matrix]
        d1_wire = [[_fraction_to_wire(x) for x in row] for row in self.d1_matrix]
        return {
            "c0_dim": self.v_count,
            "c1_dim": self.e_count,
            "c2_dim": self.f_count,
            "d0": d0_wire,
            "d1": d1_wire,
            "source_bytes_hash": self.source_bytes_hash,
        }

    @classmethod
    def from_oriented_graph(
        cls,
        vertices: Sequence[str],
        edges: Sequence[tuple[str, str]],
        faces: Sequence[Sequence[tuple[int, int | Fraction]]] | None = None,
        source_bytes: str | None = None,
    ) -> PromptCellComplex:
        """Construct incidence using distinct names and typed exact coefficients.

        Wire rational strings are parsed at the wire boundary, not implicitly
        converted here. Loops and repeated/cancelling terms remain permitted.
        """
        if any(type(vertex) is not str for vertex in vertices) or len(set(vertices)) != len(vertices):
            raise ValueError("GRAPH_VERTEX_NAMES_MUST_BE_DISTINCT_STRINGS")
        v_idx = {v: i for i, v in enumerate(vertices)}
        v_count = len(vertices)
        e_count = len(edges)

        d0_raw = [[Fraction(0) for _ in range(v_count)] for _ in range(e_count)]
        for e_i, (u, v) in enumerate(edges):
            u_i = v_idx[u]
            v_i = v_idx[v]
            d0_raw[e_i][u_i] -= Fraction(1)
            d0_raw[e_i][v_i] += Fraction(1)

        d0_matrix = tuple(tuple(row) for row in d0_raw)

        if faces is None or len(faces) == 0:
            f_count = 0
            d1_matrix: tuple[tuple[Fraction, ...], ...] = ()
        else:
            f_count = len(faces)
            d1_raw = [[Fraction(0) for _ in range(e_count)] for _ in range(f_count)]
            for f_i, boundary in enumerate(faces):
                for e_i, coeff in boundary:
                    if type(e_i) is not int or not 0 <= e_i < e_count:
                        raise ValueError("GRAPH_FACE_EDGE_INDEX_INVALID")
                    if type(coeff) not in (int, Fraction):
                        raise ValueError("GRAPH_FACE_COEFFICIENT_MUST_BE_EXACT")
                    d1_raw[f_i][e_i] += Fraction(coeff)
            d1_matrix = tuple(tuple(row) for row in d1_raw)

        sb_hash = (
            hashlib.sha256(source_bytes.encode("utf-8")).hexdigest()
            if source_bytes is not None
            else None
        )

        return cls(
            v_count=v_count,
            e_count=e_count,
            f_count=f_count,
            d0_matrix=d0_matrix,
            d1_matrix=d1_matrix,
            source_bytes_hash=sb_hash,
        )


@dataclass(frozen=True)
class PrimeTriadContext:
    """Triad execution context binding Primes 000, 001, and 002."""

    source_bytes: str | None = None
    expected_source_hash: str | None = None
    protected_answers: dict[str, str] = field(default_factory=dict)
    candidate_answers: dict[str, str] | None = None
    remaining_budget: int = 64

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source_bytes": self.source_bytes,
            "expected_source_hash": self.expected_source_hash,
            "protected_answers": self.protected_answers,
            "remaining_budget": self.remaining_budget,
        }
        if self.candidate_answers is not None:
            payload["candidate_answers"] = self.candidate_answers
        return payload


@dataclass(frozen=True)
class ExactCoboundary:
    """Disposition: Phi_1 = 0 and Gamma_2 = 0. Edge data is an exact coboundary c = d_0 a."""

    phi1: Fraction
    gamma2: Fraction
    potential: tuple[Fraction, ...]
    dual_witness: tuple[Fraction, ...]
    defect_vector: tuple[Fraction, ...]
    receipt: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClosedNonExactClass:
    """Disposition: Phi_1 > 0 and Gamma_2 = 0. Coherent topological residual."""

    phi1: Fraction
    gamma2: Fraction
    potential: tuple[Fraction, ...]
    dual_witness: tuple[Fraction, ...]
    defect_vector: tuple[Fraction, ...]
    cohomology_class_vec: tuple[Fraction, ...] = ()
    receipt: dict[str, Any] = field(default_factory=dict)

    @property
    def cohomology_class(self) -> tuple[Fraction, ...]:
        if self.cohomology_class_vec:
            return self.cohomology_class_vec
        return self.potential


@dataclass(frozen=True)
class NonClosedEdgeData:
    """Disposition: Gamma_2 > 0. Edge data does not close on boundaries (local defect)."""

    gamma2: Fraction
    phi1: Fraction | None
    defect_vector: tuple[Fraction, ...]
    receipt: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CochainRefusal:
    """Disposition: Refusal due to inadmissible profile, chain law defect, or budget exhaustion."""

    reason: str
    detail: str
    receipt: dict[str, Any] = field(default_factory=dict)

    @property
    def code(self) -> str:
        return self.reason

    @property
    def message(self) -> str:
        return self.detail


CochainDisposition = (
    ExactCoboundary | ClosedNonExactClass | NonClosedEdgeData | CochainRefusal
)


def _native_fraction(res_val: dict[str, Any], field: str) -> Fraction:
    try:
        return _parse_fraction(res_val[field])
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{field}: {exc}") from exc


def _native_vector(res_val: dict[str, Any], field: str) -> tuple[Fraction, ...]:
    raw = res_val[field]
    if not isinstance(raw, (list, tuple)):
        raise TypeError(f"{field}: expected a rational vector")
    try:
        return tuple(_parse_fraction(x) for x in raw)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{field}: {exc}") from exc


def _decode_exact_coboundary(res_val: dict[str, Any]) -> ExactCoboundary:
    residual_field = (
        "dual_witness"
        if "residual" not in res_val and "dual_witness" in res_val
        else "residual"
    )
    return ExactCoboundary(
        phi1=_native_fraction(res_val, "phi1"),
        gamma2=_native_fraction(res_val, "gamma2"),
        potential=_native_vector(res_val, "potential"),
        dual_witness=_native_vector(res_val, residual_field),
        defect_vector=(),
        receipt=res_val,
    )


def _decode_closed_non_exact(res_val: dict[str, Any]) -> ClosedNonExactClass:
    return ClosedNonExactClass(
        phi1=_native_fraction(res_val, "phi1"),
        gamma2=_native_fraction(res_val, "gamma2"),
        potential=(),
        dual_witness=_native_vector(res_val, "dual_witness"),
        defect_vector=(),
        cohomology_class_vec=_native_vector(res_val, "cohomology_class"),
        receipt=res_val,
    )


def _decode_non_closed(res_val: dict[str, Any]) -> NonClosedEdgeData:
    return NonClosedEdgeData(
        gamma2=_native_fraction(res_val, "gamma2"),
        phi1=_native_fraction(res_val, "phi1"),
        defect_vector=_native_vector(res_val, "face_defect"),
        receipt=res_val,
    )


def _decode_refusal(
    res_val: dict[str, Any],
    details: dict[str, Any],
) -> CochainRefusal:
    reason = (
        res_val.get("code")
        or details.get("reason")
        or res_val.get("reason", "UNKNOWN_REFUSAL")
    )
    detail = (
        res_val.get("message")
        or details.get("detail")
        or res_val.get("detail", "")
    )
    return CochainRefusal(
        reason=str(reason),
        detail=str(detail),
        receipt=res_val,
    )


def evaluate_prompt_cochain(
    *,
    complex: PromptCellComplex | Mapping[str, Any],
    cochain: Sequence[Any],
    primal_potential: Sequence[Any] | None = None,
    dual_witness: Sequence[Any] | None = None,
    triad_context: PrimeTriadContext | Mapping[str, Any] | None = None,
    host: PromptCochainHost,
) -> CochainDisposition:
    """Evaluate through an injected transport port.

    An omitted primal potential or dual witness is a refusal. An explicit
    empty sequence stays an empty witness and is forwarded.
    """
    if host is None:
        raise TypeError("Prompt cochain evaluation requires an injected host")
    target_host = host
    complex_dict: dict[str, Any] = (
        complex.to_dict() if hasattr(complex, "to_dict") else dict(complex)
    )
    cochain_wire = [_fraction_to_wire(x) for x in cochain]
    if primal_potential is None or dual_witness is None:
        omitted = [
            name
            for name, value in (
                ("primal_potential", primal_potential),
                ("dual_witness", dual_witness),
            )
            if value is None
        ]
        return CochainRefusal(
            reason="OMITTED_COCHAIN_WITNESS",
            detail="omitted " + ", ".join(omitted),
            receipt={"omitted": omitted},
        )
    potential_wire = [_fraction_to_wire(x) for x in primal_potential]
    dual_wire = [_fraction_to_wire(x) for x in dual_witness]
    triad_dict: dict[str, Any] | None = (
        triad_context.to_dict()
        if hasattr(triad_context, "to_dict")
        else (dict(triad_context) if triad_context is not None else None)
    )

    invoke_res = target_host.evaluate_prompt_cochain(
        complex=complex_dict,
        cochain=cochain_wire,
        primal_potential=potential_wire,
        dual_witness=dual_wire,
        triad_context=triad_dict,
    )
    if invoke_res.is_err:
        refusal = invoke_res.unwrap_err()
        return CochainRefusal(
            reason=getattr(refusal, "code", "HOST_ERROR"),
            detail=getattr(refusal, "message", str(refusal)),
            receipt={"raw_refusal": str(refusal)},
        )

    val = invoke_res.unwrap()
    res_val = val.get("result", val) if isinstance(val, dict) else {}
    if not isinstance(res_val, dict):
        return CochainRefusal(
            reason="MALFORMED_NATIVE_REPLY",
            detail="result: expected a disposition object",
            receipt=val,
        )

    details = (
        res_val.get("details", {})
        if isinstance(res_val.get("details"), dict)
        else {}
    )
    try:
        match res_val.get("disposition"):
            case "ExactCoboundary":
                return _decode_exact_coboundary(res_val)
            case "ClosedNonExactClass":
                return _decode_closed_non_exact(res_val)
            case "NonClosedEdgeData":
                return _decode_non_closed(res_val)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return CochainRefusal(
            reason="MALFORMED_NATIVE_REPLY",
            detail=f"{res_val['disposition']}: {exc}",
            receipt=res_val,
        )

    if res_val.get("disposition") == "Refusal":
        return _decode_refusal(res_val, details)
    if isinstance(val, dict) and val.get("error"):
        return CochainRefusal(
            reason="HOST_ERROR",
            detail=str(val.get("error")),
            receipt=val,
        )
    return CochainRefusal(
        reason="UNRECOGNIZED_DISPOSITION",
        detail=f"Dispatched outcome was {val}",
        receipt=val if isinstance(val, dict) else {"raw": str(val)},
    )
