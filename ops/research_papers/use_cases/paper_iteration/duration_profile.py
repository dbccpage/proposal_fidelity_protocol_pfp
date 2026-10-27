"""Generic duration-residual profile over the exact rational cochain Crucible.

The GTOC paper ``010_gtoc_witnessed_succession_and_duration.md`` (section 6.3)
classifies a finite duration 1-cochain ``tau`` into exactly one of four paper
labels:

* ``Exact`` -- a displayed potential ``T`` satisfies ``tau = d0 T`` and the
  declared faces close or the ``d1 d0 = 0`` contract holds;
* ``ClosedNonExact`` -- every declared face closes and a global period
  ``z in ker d1 \\ image d0`` is exhibited with ``<tau, z> != 0``;
* ``ActiveClosureFailure`` -- some declared face has ``(d1 tau)(F) != 0`` and
  no potential is displayed or the ``d1 d0 = 0`` contract holds;
* ``ExactnessUndetermined`` -- no preceding machine condition is met, including
  conflicting potential/face receipts without a ``d1 d0 = 0`` contract.

the finite-cochain obstruction solver decides its own exhaustive four-way solver verdict
over the explicit coefficient domain ``Q``. On valid complexes, its three
cochain verdicts map directly to the first three paper classes. An
``invalid_complex`` verdict is not itself a paper class: this adapter inspects
the retained potential and face receipts and applies the section-6.3 machine
conditions before using ``ExactnessUndetermined``. It rewrites no exact
arithmetic and mints no authority.

Honesty fences carried by this adapter:

* It classifies ONE finite rational carrier and ONE displayed 1-cochain. It
  does NOT cover arbitrary ordered abelian coefficient groups and does NOT prove
  the universal PL-GTOC-15 statement.
* ``ExactnessUndetermined`` is the honest "the packet cannot license a
  cohomological classification" route (paper section 6.7). It is NEVER a claim
  of nonexactness -- paper section 6.3: "A missing potential receipt is never a
  proof of nonexactness."
* Every receipt carries ``authority_effect = "none"``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Any, Mapping, Sequence

try:
    from core_discrete_deformation_algebra import FiniteCochainComplex
except ImportError:
    class FiniteCochainComplex:
        pass

try:
    from core_solvers.finite_cochain_obstruction_solver import (
        CochainAnalysis,
        Verdict,
        analyze_finite_cochain,
    )
except ImportError:
    class CochainAnalysis:
        pass
    class Verdict(str, Enum):
        SUCCESS = "SUCCESS"
        FAIL = "FAIL"
        EXACT_REPAIR = "EXACT_REPAIR"
        CLOSED_NON_EXACT = "CLOSED_NON_EXACT"
        CLOSED_RESIDUAL = "CLOSED_RESIDUAL"
        ACTIVE_CLOSURE_FAILURE = "ACTIVE_CLOSURE_FAILURE"
        CURVATURE = "CURVATURE"
        INVALID_COMPLEX = "INVALID_COMPLEX"
    def analyze_finite_cochain(*args: Any, **kwargs: Any) -> Any:
        return None

DURATION_PROFILE_SCHEMA = "core.duration_residual_profile.v1"
DURATION_PROFILE_ADAPTER_ID = "core-python:duration-residual-profile.v1"


class DurationClass(str, Enum):
    """The four paper duration classes of section 6.3 (exhaustive, disjoint)."""

    EXACT = "Exact"
    CLOSED_NON_EXACT = "ClosedNonExact"
    ACTIVE_CLOSURE_FAILURE = "ActiveClosureFailure"
    EXACTNESS_UNDETERMINED = "ExactnessUndetermined"


# Direct map for a valid cochain complex. INVALID_COMPLEX requires the retained
# potential and face receipts, so a raw verdict alone is intentionally refused.
_VERDICT_TO_CLASS: dict[Verdict, DurationClass] = {
    Verdict.EXACT_REPAIR: DurationClass.EXACT,
    Verdict.CLOSED_RESIDUAL: DurationClass.CLOSED_NON_EXACT,
    Verdict.CURVATURE: DurationClass.ACTIVE_CLOSURE_FAILURE,
}

# Paper section 6.3 machine condition for each duration class.
PAPER_CONDITIONS: dict[DurationClass, str] = {
    DurationClass.EXACT: (
        "a displayed potential T satisfies tau = d0 T, and either every declared "
        "face closes or the cochain contract supplies d1 d0 = 0"
    ),
    DurationClass.CLOSED_NON_EXACT: (
        "every declared local face closes, and a global period "
        "z in ker(d1) \\ image(d0) is exhibited with <tau, z> != 0"
    ),
    DurationClass.ACTIVE_CLOSURE_FAILURE: (
        "some declared local face has (d1 tau)(F) != 0, under a supplied "
        "d1 d0 = 0 contract or with no displayed potential receipt"
    ),
    DurationClass.EXACTNESS_UNDETERMINED: (
        "no preceding machine condition is met, including conflicting potential "
        "and face receipts without a d1 d0 = 0 contract"
    ),
}

# Why the specific Crucible verdict routes to this paper class, plus the honesty
# fence attached to the class.
_VALID_RATIONALE: dict[DurationClass, str] = {
    DurationClass.EXACT: (
        "Crucible verdict exact_repair: d1(tau) = 0 and an exact rational "
        "potential alpha with d0(alpha) = tau was witnessed, so duration is "
        "removable into an endpoint potential (paper Theorem 6.1)."
    ),
    DurationClass.CLOSED_NON_EXACT: (
        "Crucible verdict closed_residual: d1(tau) = 0 but tau is not in "
        "image(d0); the returned residual representative witnesses a nonzero "
        "class of ker(d1)/image(d0), i.e. a retained global cohomological "
        "period. This is not a proof that no potential exists on any richer "
        "carrier -- only that none exists on THIS displayed carrier."
    ),
    DurationClass.ACTIVE_CLOSURE_FAILURE: (
        "Crucible verdict curvature: the complex is valid (d1 d0 = 0) but "
        "d1(tau) != 0, a local composition defect on a declared face."
    ),
}


class DurationProfileError(ValueError):
    """Typed refusal for inputs the adapter cannot faithfully classify."""


def classify_verdict(verdict: Verdict) -> DurationClass:
    """Map one valid-complex Crucible verdict to a paper duration class.

    ``INVALID_COMPLEX`` requires a full :class:`CochainAnalysis`; a raw verdict
    would discard the potential/face distinction required by paper section 6.3.
    """

    if not isinstance(verdict, Verdict):
        raise DurationProfileError(
            f"expected a Crucible Verdict, received {type(verdict).__name__}"
        )
    if verdict is Verdict.INVALID_COMPLEX:
        raise DurationProfileError(
            "invalid_complex requires a full CochainAnalysis to apply "
            "the paper machine conditions"
        )
    return _VERDICT_TO_CLASS[verdict]


def _classify_analysis(analysis: CochainAnalysis) -> DurationClass:
    if analysis.verdict is not Verdict.INVALID_COMPLEX:
        return classify_verdict(analysis.verdict)

    faces_close = all(value == 0 for value in analysis.closure_defect)
    potential_displayed = analysis.primitive_witness is not None
    if faces_close and potential_displayed:
        return DurationClass.EXACT
    if not faces_close and not potential_displayed:
        return DurationClass.ACTIVE_CLOSURE_FAILURE
    return DurationClass.EXACTNESS_UNDETERMINED


def _rationale(
    analysis: CochainAnalysis, duration_class: DurationClass
) -> str:
    if analysis.verdict is not Verdict.INVALID_COMPLEX:
        return _VALID_RATIONALE[duration_class]
    if duration_class is DurationClass.EXACT:
        return (
            "Crucible verdict invalid_complex: d1 d0 != 0, but an exact rational "
            "potential is displayed and every declared face closes. This meets "
            "the local Exact machine condition of paper section 6.3; the invalid "
            "ambient complex licenses no cohomological reading under section 6.7."
        )
    if duration_class is DurationClass.ACTIVE_CLOSURE_FAILURE:
        return (
            "Crucible verdict invalid_complex: d1 d0 != 0, but d1(tau) != 0 "
            "and no potential is displayed. This meets the local "
            "ActiveClosureFailure machine condition of paper section 6.3; the "
            "invalid ambient complex licenses no cohomological reading."
        )
    return (
        "Crucible verdict invalid_complex: d1 d0 != 0 and the retained local "
        "receipts conflict or establish no preceding section-6.3 machine "
        "condition. ExactnessUndetermined is an honest cannot-license route; "
        "it is NEVER a claim of nonexactness."
    )


@dataclass(frozen=True)
class DurationProfileReceipt:
    """Hash-bound duration classification of one finite carrier; evidence only."""

    duration_class: DurationClass
    crucible_verdict: Verdict
    paper_condition: str
    rationale: str
    crucible_evidence_sha256: str
    coefficient_domain: str
    cochain_contract_valid: bool
    cohomological_reading_licensed: bool
    closure_defect: tuple[str, ...]
    residual_representative: tuple[str, ...] | None
    primitive_witness: tuple[str, ...] | None
    period_witness: tuple[str, ...] | None
    period_boundary_defect: tuple[str, ...] | None
    period_pairing: str | None
    period_is_boundary: bool | None
    authority_effect: str = "none"
    schema_version: str = DURATION_PROFILE_SCHEMA
    adapter_id: str = DURATION_PROFILE_ADAPTER_ID

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "authority_effect": self.authority_effect,
            "duration_class": self.duration_class.value,
            "crucible_verdict": self.crucible_verdict.value,
            "paper_condition": self.paper_condition,
            "coefficient_domain": self.coefficient_domain,
            "cochain_contract_valid": self.cochain_contract_valid,
            "cohomological_reading_licensed": (
                self.cohomological_reading_licensed
            ),
            "rationale": self.rationale,
            "crucible_evidence_sha256": self.crucible_evidence_sha256,
            "closure_defect": list(self.closure_defect),
            "residual_representative": (
                None
                if self.residual_representative is None
                else list(self.residual_representative)
            ),
            "primitive_witness": (
                None
                if self.primitive_witness is None
                else list(self.primitive_witness)
            ),
            "period_witness": (
                None if self.period_witness is None else list(self.period_witness)
            ),
            "period_boundary_defect": (
                None
                if self.period_boundary_defect is None
                else list(self.period_boundary_defect)
            ),
            "period_pairing": self.period_pairing,
            "period_is_boundary": self.period_is_boundary,
        }

    @property
    def profile_sha256(self) -> str:
        canonical = json.dumps(
            self.canonical_payload(), separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def _fraction_text(value: Any) -> str:
    return f"{value.numerator}/{value.denominator}"


def profile_from_analysis(analysis: CochainAnalysis) -> DurationProfileReceipt:
    """Adapt one exact :class:`CochainAnalysis` to a duration profile receipt."""

    if not isinstance(analysis, CochainAnalysis):
        raise DurationProfileError(
            f"expected a CochainAnalysis, received {type(analysis).__name__}"
        )
    duration_class = _classify_analysis(analysis)
    cochain_contract_valid = analysis.verdict is not Verdict.INVALID_COMPLEX
    return DurationProfileReceipt(
        duration_class=duration_class,
        crucible_verdict=analysis.verdict,
        paper_condition=PAPER_CONDITIONS[duration_class],
        rationale=_rationale(analysis, duration_class),
        crucible_evidence_sha256=analysis.evidence_sha256,
        coefficient_domain=analysis.coefficient_domain,
        cochain_contract_valid=cochain_contract_valid,
        cohomological_reading_licensed=cochain_contract_valid,
        closure_defect=tuple(_fraction_text(v) for v in analysis.closure_defect),
        residual_representative=(
            None
            if analysis.residual_representative is None
            else tuple(_fraction_text(v) for v in analysis.residual_representative)
        ),
        primitive_witness=(
            None
            if analysis.primitive_witness is None
            else tuple(_fraction_text(v) for v in analysis.primitive_witness)
        ),
        period_witness=(
            None
            if analysis.period_witness is None
            else tuple(_fraction_text(v) for v in analysis.period_witness)
        ),
        period_boundary_defect=(
            None
            if analysis.period_boundary_defect is None
            else tuple(
                _fraction_text(v) for v in analysis.period_boundary_defect
            )
        ),
        period_pairing=(
            None
            if analysis.period_pairing is None
            else _fraction_text(analysis.period_pairing)
        ),
        period_is_boundary=analysis.period_is_boundary,
    )


def profile_from_problem(
    dimensions: tuple[int, int, int],
    d0: Sequence[Sequence[int | str]],
    d1: Sequence[Sequence[int | str]],
    beta: Sequence[int | str],
) -> DurationProfileReceipt:
    """Classify a declared finite cochain problem end-to-end.

    Malformed carriers surface as :class:`DurationProfileError` rather than a
    forced label, matching the paper's refusal-first discipline.
    """

    try:
        complex_ = FiniteCochainComplex.from_rows(dimensions=dimensions, d0=d0, d1=d1)
        analysis = analyze_finite_cochain(complex_, beta)
    except (KeyError, TypeError, ValueError) as error:
        raise DurationProfileError(f"invalid finite cochain problem: {error}") from error
    return profile_from_analysis(analysis)


def profile_from_cochain_problem(problem: Mapping[str, Any]) -> DurationProfileReceipt:
    """Classify a ``cochain_problem`` mapping (dimensions/d0/d1/beta)."""

    try:
        dimensions = tuple(problem["dimensions"])
        d0 = problem["d0"]
        d1 = problem["d1"]
        beta = problem["beta"]
    except (KeyError, TypeError) as error:
        raise DurationProfileError(f"invalid cochain problem mapping: {error}") from error
    return profile_from_problem(dimensions, d0, d1, beta)


FIXTURES = {
    "Exact": {
        "dimensions": (3, 3, 1),
        "d0": ((-1, 1, 0), (0, -1, 1), (-1, 0, 1)),
        "d1": ((1, 1, -1),),
        "beta": (1, 2, 3),
        "reading": (
            "Filled triangle; tau=(1,2,3) is d0 of the endpoint potential "
            "T=(-3,-2,0) (up to a constant), so duration telescopes (Theorem 6.1)."
        ),
    },
    "ClosedNonExact": {
        "dimensions": (3, 3, 0),
        "d0": ((-1, 1, 0), (0, -1, 1), (1, 0, -1)),
        "d1": (),
        "beta": (1, 1, 1),
        "reading": (
            "Hollow 3-cycle; every face closes (no 2-cells) but the loop period "
            "z has <tau,z>=3!=0, a retained global cohomological period."
        ),
    },
    "ActiveClosureFailure": {
        "dimensions": (3, 3, 1),
        "d0": ((-1, 1, 0), (0, -1, 1), (-1, 0, 1)),
        "d1": ((1, 1, -1),),
        "beta": (1, 2, 4),
        "reading": (
            "Filled triangle with tau=(1,2,4); (d1 tau)(F)=-1!=0 under a valid "
            "d1 d0=0 contract: a local composition defect on the declared face."
        ),
    },
    "ExactnessUndetermined": {
        "dimensions": (2, 2, 1),
        "d0": ((-1, 1), (-1, 1)),
        "d1": ((1, 1),),
        "beta": (1, 1),
        "reading": (
            "d1 d0 != 0 while tau has both a rational potential and a nonzero "
            "face defect. The conflicting receipts have no d1 d0=0 contract, so "
            "section 6.3 routes to undetermined, never to nonexactness."
        ),
    },
}


def _fixture_record(name: str, spec: dict) -> dict:
    """Run one carrier through the exact Crucible + duration-profile adapter."""

    profile = profile_from_problem(
        spec["dimensions"], spec["d0"], spec["d1"], spec["beta"]
    )
    return {
        "class_requested": name,
        "dimensions": list(spec["dimensions"]),
        "coefficient_carrier": "Q (exact rationals)",
        "integer_input_embedding": all(
            isinstance(value, int) and not isinstance(value, bool)
            for key in ("d0", "d1", "beta")
            for row in (spec[key] if key != "beta" else (spec[key],))
            for value in row
        ),
        "d0": [list(row) for row in spec["d0"]],
        "d1": [list(row) for row in spec["d1"]],
        "duration_1_cochain_tau": list(spec["beta"]),
        "d1_d0_is_zero": profile.cochain_contract_valid,
        "cohomological_reading_licensed": (
            profile.cohomological_reading_licensed
        ),
        "potential_witness": (
            None
            if profile.primitive_witness is None
            else list(profile.primitive_witness)
        ),
        "closure_defect": list(profile.closure_defect),
        "residual_witness": (
            None
            if profile.residual_representative is None
            else list(profile.residual_representative)
        ),
        "period_witness": (
            None if profile.period_witness is None else list(profile.period_witness)
        ),
        "period_boundary_defect": (
            None
            if profile.period_boundary_defect is None
            else list(profile.period_boundary_defect)
        ),
        "period_pairing": profile.period_pairing,
        "period_is_boundary": profile.period_is_boundary,
        "solver_verdict": profile.crucible_verdict.value,
        "paper_profile_verdict": profile.duration_class.value,
        "matches_requested_class": profile.duration_class.value == name,
        "paper_condition": profile.paper_condition,
        "evidence_sha256": profile.crucible_evidence_sha256,
        "profile_sha256": profile.profile_sha256,
        "reading": spec["reading"],
        "completeness_limit": (
            "one rational carrier, one displayed tau; classification is exact "
            "for THIS Q-linear carrier only and does not quantify over arbitrary "
            "ordered abelian coefficient groups or all finite carriers."
        ),
        "unsupported_generalization": (
            "does not establish the universal PL-GTOC-15 statement that duration "
            "exactness/residual is mechanized for every admissible packet."
        ),
        "authority_effect": "none",
    }


def _bounded_search_record() -> dict:
    """Deterministic exhaustive search of tau over a declared finite box."""

    lo, hi = -2, 2
    spec = FIXTURES["Exact"]
    order = "lexicographic ascending over (tau0, tau1, tau2)"
    tally: dict[str, int] = {
        "Exact": 0,
        "ClosedNonExact": 0,
        "ActiveClosureFailure": 0,
        "ExactnessUndetermined": 0,
    }
    examples: dict[str, list] = {key: None for key in tally}
    enumerated = 0
    for a in range(lo, hi + 1):
        for b in range(lo, hi + 1):
            for c in range(lo, hi + 1):
                beta = (a, b, c)
                profile = profile_from_problem(
                    spec["dimensions"], spec["d0"], spec["d1"], beta
                )
                label = profile.duration_class.value
                tally[label] += 1
                enumerated += 1
                if examples[label] is None:
                    examples[label] = list(beta)
    return {
        "coefficient_domain": "Q",
        "searched_input_lattice": "Z^3 embedded canonically in Q^3",
        "carrier": "Exact filled triangle, dimensions (3,3,1)",
        "search_space": f"tau in [{lo},{hi}]^3 over Z",
        "enumeration_order": order,
        "declared_bound": {"lo": lo, "hi": hi, "cardinality": (hi - lo + 1) ** 3},
        "enumerated_count": enumerated,
        "class_tally": tally,
        "first_example_per_class": examples,
        "exhaustion_claim": (
            "This bounded sweep is exhaustive of the declared box only. It proves "
            "no universal statement; classes absent from the tally are absent "
            "from THIS box, not from all finite carriers."
        ),
        "authority_effect": "none",
    }


def _invalid_complex_branch_audit() -> dict:
    """Exercise every section-6.3 receipt combination on one invalid carrier."""

    carrier = {
        "dimensions": (2, 2, 1),
        "d0": ((-1, 1), (-1, 1)),
        "d1": ((1, 1),),
    }
    cases = {
        "closed_with_potential": {
            "beta": (0, 0),
            "expected": "Exact",
        },
        "nonclosed_without_potential": {
            "beta": (1, 0),
            "expected": "ActiveClosureFailure",
        },
        "nonclosed_with_potential": {
            "beta": (1, 1),
            "expected": "ExactnessUndetermined",
        },
        "closed_without_potential": {
            "beta": (1, -1),
            "expected": "ExactnessUndetermined",
        },
    }
    results = {}
    for name, case in cases.items():
        profile = profile_from_problem(
            carrier["dimensions"], carrier["d0"], carrier["d1"], case["beta"]
        )
        results[name] = {
            "tau": list(case["beta"]),
            "solver_verdict": profile.crucible_verdict.value,
            "potential_displayed": profile.primitive_witness is not None,
            "faces_close": all(value == "0/1" for value in profile.closure_defect),
            "paper_profile_verdict": profile.duration_class.value,
            "expected_profile_verdict": case["expected"],
            "matches_expected": profile.duration_class.value == case["expected"],
            "cohomological_reading_licensed": (
                profile.cohomological_reading_licensed
            ),
            "profile_sha256": profile.profile_sha256,
        }
    return {
        "coefficient_domain": "Q",
        "carrier": {
            "dimensions": list(carrier["dimensions"]),
            "d0": [list(row) for row in carrier["d0"]],
            "d1": [list(row) for row in carrier["d1"]],
            "d1_d0_is_zero": False,
        },
        "cases": results,
        "all_branches_match": all(
            result["matches_expected"] for result in results.values()
        ),
        "cohomological_reading_licensed": False,
        "scope_note": (
            "This finite branch audit checks the local section-6.3 routing only; "
            "the invalid carrier licenses no section-6.7 cohomological reading."
        ),
        "authority_effect": "none",
    }


def _spectral_hodge_record() -> dict:
    """Live l2 degree-1 spectral (Hodge-Laplacian) diagnostic on the Exact carrier."""

    from core_solvers.q_obstruction_solver import QObstructionInputDegree1, QObstructionSolver
    from core_solvers.topology.solver_hodge_primal_dual_decomp import solve_spectral_hodge

    spec = FIXTURES["Exact"]
    c1 = spec["dimensions"][1]
    result = solve_spectral_hodge(
        QObstructionInputDegree1.from_rows(
            d0=[[float(v) for v in row] for row in spec["d0"]],
            d1=[[float(v) for v in row] for row in spec["d1"]],
            defect_potential=[[0.0 for _ in range(c1)] for _ in range(c1)],
        ),
        QObstructionSolver(),
    )
    payload = result.value.canonical_payload()
    return {
        "matrix_carrier": "degree-1 Hodge Laplacian of the Exact filled triangle",
        "tolerance": QObstructionSolver().tolerance,
        "converged": result.diagnostics.converged,
        "residual_inf_norm": payload["residual_inf_norm"],
        "dim": payload["dim"],
        "spectral_gap": payload["spectral_gap"],
        "eigenvalues": payload["eigenvalues"],
        "evidence_sha256": result.value.evidence_sha256,
        "exact_to_float_loss": (
            "exact rational cochain data is cast to IEEE floats for the spectral "
            "pass; eigenvalues/residuals are floating diagnostics."
        ),
        "why_diagnostic_not_proof": (
            "an l2 spectral gap is not an exact cohomological classification of "
            "PL-GTOC-15; the exact Crucible verdict is the load-bearing evidence, "
            "not this float spectrum."
        ),
        "authority_effect": "none",
    }


__all__ = [
    "DURATION_PROFILE_ADAPTER_ID",
    "DURATION_PROFILE_SCHEMA",
    "DurationClass",
    "DurationProfileError",
    "DurationProfileReceipt",
    "PAPER_CONDITIONS",
    "FIXTURES",
    "_fixture_record",
    "_bounded_search_record",
    "_invalid_complex_branch_audit",
    "_spectral_hodge_record",
    "classify_verdict",
    "profile_from_analysis",
    "profile_from_cochain_problem",
    "profile_from_problem",
]

