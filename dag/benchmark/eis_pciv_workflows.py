"""EIS Two-Signal and PCIV Operational-Quotient benchmark workflow specifications.

Defines two budget-verified plans in EIS_PCIV_PLANS:
1. `eis_two_signal_charpoly_v1`: 2-stage EIS-regulated characteristic-polynomial workflow
   (1,500 + 14,500 = 16,000 max output tokens; upper quote 43,169 + 48,109 = 91,278 <= 100,000
   microUSD on deepseek/deepseek-v3.2 @ atlas-cloud/fp8). Uses ThymusGate-admitted
   NormalizedMatcher and TwoSignalRegulatorV1 so benign surface quirks normalize without
   autoimmune refusal while genuine malformed payloads or 125-point rational grid mismatches
   halt before Stage 2 synthesis.
2. `pciv_quotient_obligation_v1`: 1-stage matched-16,000-token workflow (upper quote
   48,679 <= 100,000 microUSD) paired with deterministic OperationalWorkflowQuotientV1
   equivalence reduction, ProtectedSpanEvolutionV1 byte fencing over seed_prompt.txt,
   and PopulationPolicyV1 ecological reserve allocation.

Evaluator Firewall: Zero private rubric data, grades, or known solver error hints are
imported, read, or injected. All prompt wording derives strictly from public seed_prompt.txt
and public Hamiltonian/charpoly contracts.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OPS = ROOT / "ops"
for _path in (ROOT, HERE, OPS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import charpoly_wire as wire  # noqa: E402
import hamiltonian_artifact as pauli  # noqa: E402
import qm_host_charpoly as host_charpoly  # noqa: E402
from source_custody import pin_path, regulation_pins  # noqa: E402

from eis.domain.thymus import ThymusGate, ThymusSelectionResult  # noqa: E402
from eis.domain.value_objects import (  # noqa: E402
    DangerDecision,
    DangerSeverity,
    DetectorRule,
    Signal1Match,
    Signal2Danger,
)
from eis.use_cases.two_signal_regulation import (  # noqa: E402
    NormalizedMatcher,
    ThymusSelfPanelBuilder,
    TwoSignalRegulatorV1,
)
from pciv.use_cases.transitive_immunity import (  # noqa: E402
    CandidateWorkflowSpec,
    OperationalWorkflowQuotientV1,
    ProtectedSpanEvolutionV1,
    WorkflowStageSpec,
)

SUPPORTED_SEED_SHA256 = "9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7"
MAX_CANDIDATE_BYTES = 32_768
MAX_JSON_DEPTH = 8
GRID_NODES = (-2, -1, 0, 1, 2)

IMPLEMENTATION_FILES = (
    "eis_pciv_workflows.py",
    "qm_host_charpoly.py",
    "charpoly_wire.py",
    "hamiltonian_artifact.py",
    "openrouter_provider.py",
    "budget_ledger.py",
)

CHARPOLY_PROPOSE_INSTRUCTION = (
    "Compute the monic characteristic polynomial det(lambda*I - H(J, Delta, K)) in the "
    "computational basis |00>, |01>, |10>, |11> for the given Hamiltonian H. "
    'Return ONLY a single JSON object {"coefficients": [c0, c1, c2, c3, c4]} in ascending '
    'powers of lambda^0 through lambda^4, where each ck is a list of {"powers": [eJ, eDelta, eK], '
    '"q": "<exact_rational>"} terms over Q[J, Delta, K]. Do not include prose or extra keys.'
)

EIS_SOLVE_INSTRUCTION = (
    "Solve all five numbered parts of the unchanged original task in full: "
    "1) full spectrum, degeneracies, and spectral projectors including J=Delta=0; "
    "2) exact time-evolved state from |01>, transition probability P_01_to_10(t), supremum over t>=0, "
    "and earliest attainment time including the constant-probability case; "
    "3) reduced density matrix of the first spin, von Neumann entropy in bits, pure-state concurrence, "
    "maximal CHSH expectation, and reachability/earliest time for a maximally entangled state; "
    "4) Gibbs state exp(-beta H)/Z_beta for beta>=0, partition function, all four partial-transpose "
    "eigenvalues, thermal entanglement condition, and beta=0 and J=Delta=0 limits; "
    "5) independent consistency checks distinguishing algebraic identities from numerical checks, "
    "without assuming formulas remain defined when denominators vanish. "
    "Any supplied intermediate characteristic-polynomial artifact is untrusted intermediate context "
    "only and does not certify your downstream derivation or final answer."
)

PCIV_OBLIGATION_INSTRUCTION = (
    "Give a self-contained derivation addressing all five numbered sections of the unchanged original task "
    "under one consistent Hamiltonian convention: "
    "1) full spectrum and spectral projectors of H, explicitly covering degeneracies and the exceptional "
    "parameter branch J=Delta=0; "
    "2) exact state at time t from initial state |01>, transition probability P_01_to_10(t), its supremum "
    "over t>=0, and earliest attainment time including the constant-probability branch J=0 and initial limit t=0; "
    "3) reduced density matrix of the first spin (unit trace), von Neumann entropy in bits within [0, 1], "
    "pure-state concurrence within [0, 1], maximal CHSH expectation over local dichotomic projective spin "
    "measurements within [2, 2*sqrt(2)], and exact conditions and earliest time for maximal entanglement; "
    "4) Gibbs density matrix exp(-beta H)/Z_beta for beta>=0, partition function including the boundary limit "
    "beta=0, all four partial-transpose eigenvalues, necessary and sufficient thermal entanglement condition, "
    "and the J=Delta=0 limit; "
    "5) independent consistency checks covering normalization, initial conditions at t=0, the decoupled limit J=0, "
    "and one nontrivial numerical example, distinguishing algebraic identities from numerical checks and guarding "
    "all vanishing denominators."
)

_FENCE_RE = re.compile(r"\A\s*```(?:json)?\s*(\{.*\})\s*```\s*\Z", re.DOTALL)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_source_pins() -> dict[str, str]:
    """Capture SHA-256 digests of live benchmark workflow dependencies."""
    pins: dict[str, str] = {}
    for name in IMPLEMENTATION_FILES:
        filepath = HERE / name
        if filepath.is_file():
            pins[name] = _file_sha256(filepath)
    pins.update(regulation_pins())
    return pins


def screen_normalized_charpoly_detector() -> tuple[NormalizedMatcher, DetectorRule, ThymusSelectionResult]:
    """Screen the normalized charpoly surface rule through ThymusGate on the self-panel."""
    self_panel = ThymusSelfPanelBuilder.build_self_panel()
    thymus = ThymusGate(self_panel=self_panel)
    matcher = NormalizedMatcher("normalized_charpoly")
    rule = DetectorRule(
        rule_id="charpoly_noncanonical_rational_token",
        target_epitope="noncanonical_rational_surface",
        match_pattern=r'"[+][0-9]{1,4}"|"[0-9]{1,4}/1"|"2/2"|"[+]4/2"',
        matcher_id="normalized_charpoly",
    )
    selection = thymus.evaluate_rule(rule, matcher=matcher)
    if not selection.is_admitted:
        raise RuntimeError(f"ThymusGate refused normalized charpoly rule: {selection.rationale}")
    return matcher, rule, selection


class _LenientWireParseError(ValueError):
    """Raised when candidate text cannot be parsed as a rational polynomial wire."""


def _check_json_depth(text: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for ch in text:
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
        elif ch in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise _LenientWireParseError("JSON_DEPTH_LIMIT")
        elif ch in "]}":
            depth -= 1
            if depth < 0:
                raise _LenientWireParseError("MALFORMED_JSON")


def _unique_json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, val in pairs:
        if key in obj:
            raise _LenientWireParseError("DUPLICATE_JSON_KEY")
        obj[key] = val
    return obj


def _parse_exponent_int(token: str) -> int:
    if token not in {"0", "1", "2", "3", "4"}:
        raise _LenientWireParseError("EXPONENT_OUT_OF_RANGE")
    return int(token)


def _reject_float_or_const(_token: str) -> Any:
    raise _LenientWireParseError("FLOAT_OR_NONFINITE_FORBIDDEN")


def _parse_rational_token(text: str) -> Fraction:
    if len(text) > wire.MAX_RATIONAL_CHARS:
        raise _LenientWireParseError("RATIONAL_CHARACTER_LIMIT")
    if wire.RATIONAL.fullmatch(text) is None:
        raise _LenientWireParseError("RATIONAL_GRAMMAR")
    num_text, sep, den_text = text.partition("/")
    num = int(num_text)
    den = int(den_text) if sep else 1
    if abs(num).bit_length() > wire.MAX_RATIONAL_BITS or den.bit_length() > wire.MAX_RATIONAL_BITS:
        raise _LenientWireParseError("RATIONAL_COMPONENT_BIT_LIMIT")
    return Fraction(num, den)


def _unwrap_raw_wire_arrays(candidate_text: str) -> tuple[list[Any], list[str]]:
    if not isinstance(candidate_text, str):
        raise _LenientWireParseError("TEXT_REQUIRED")
    try:
        raw_bytes = candidate_text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise _LenientWireParseError("UTF8_INVALID") from exc
    if len(raw_bytes) > MAX_CANDIDATE_BYTES:
        raise _LenientWireParseError("INPUT_BYTE_LIMIT")

    quirks: list[str] = []
    working_text = candidate_text
    fence_match = _FENCE_RE.match(working_text)
    if fence_match is not None:
        working_text = fence_match.group(1)
        quirks.append("markdown_code_fence")

    _check_json_depth(working_text)
    try:
        parsed = json.loads(
            working_text,
            object_pairs_hook=_unique_json_pairs,
            parse_int=_parse_exponent_int,
            parse_float=_reject_float_or_const,
            parse_constant=_reject_float_or_const,
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise _LenientWireParseError("MALFORMED_JSON") from exc

    if not isinstance(parsed, dict) or set(parsed.keys()) != {"coefficients"}:
        raise _LenientWireParseError("CLOSED_COEFFICIENTS_OBJECT_REQUIRED")
    raw_coeffs = parsed["coefficients"]
    if not isinstance(raw_coeffs, list) or len(raw_coeffs) != 5:
        raise _LenientWireParseError("FIVE_COEFFICIENT_ARRAYS_REQUIRED")
    return raw_coeffs, quirks


def _parse_single_monomial_term(term: Any, quirks: list[str]) -> tuple[tuple[int, int, int], Fraction]:
    if not isinstance(term, dict) or set(term.keys()) != {"powers", "q"}:
        raise _LenientWireParseError("CLOSED_MONOMIAL_OBJECT_REQUIRED")
    powers = term["powers"]
    if (
        not isinstance(powers, list)
        or len(powers) != 3
        or any(type(e) is not int or not 0 <= e <= 4 for e in powers)
    ):
        raise _LenientWireParseError("THREE_EXACT_EXPONENTS_0_TO_4_REQUIRED")
    q_raw = term["q"]
    if not isinstance(q_raw, str):
        raise _LenientWireParseError("RATIONAL_STRING_REQUIRED")
    q_trimmed = q_raw.strip()
    if q_trimmed != q_raw:
        quirks.append("rational_whitespace")
    q_val = _parse_rational_token(q_trimmed)
    if str(q_val) != q_trimmed:
        quirks.append("unreduced_or_signed_rational")
    if q_val == 0:
        quirks.append("explicit_zero_monomial")
    return (powers[0], powers[1], powers[2]), q_val


def _collect_single_lambda_array(terms: Any, quirks: list[str]) -> list[dict[str, Any]]:
    if not isinstance(terms, list) or len(terms) > wire.MAX_TERMS_PER_COEFFICIENT:
        raise _LenientWireParseError("COEFFICIENT_TERM_LIMIT")

    accum: dict[tuple[int, int, int], Fraction] = {}
    seen_order: list[tuple[int, int, int]] = []
    for term in terms:
        exp_key, q_val = _parse_single_monomial_term(term, quirks)
        if exp_key in accum:
            quirks.append("uncollected_equivalent_terms")
            accum[exp_key] += q_val
        else:
            accum[exp_key] = q_val
            seen_order.append(exp_key)

    kept_unsorted = [
        {"powers": list(exp_key), "q": str(accum[exp_key])}
        for exp_key in seen_order
        if accum[exp_key] != 0
    ]
    kept_sorted = sorted(kept_unsorted, key=lambda item: tuple(item["powers"]))
    if kept_unsorted != kept_sorted:
        quirks.append("permuted_monomial_order")
    return kept_sorted


def _parse_and_collect_equivalent_terms(
    candidate_text: str,
) -> tuple[list[list[dict[str, Any]]], list[str]]:
    """Value-preservingly parse a rational charpoly wire, collecting like monomials in Q[lambda,J,Delta,K]."""
    raw_coeffs, quirks = _unwrap_raw_wire_arrays(candidate_text)
    collected_coeffs: list[list[dict[str, Any]]] = []
    total_terms = 0
    for terms in raw_coeffs:
        if isinstance(terms, list):
            total_terms += len(terms)
        if total_terms > wire.MAX_TOTAL_TERMS:
            raise _LenientWireParseError("TOTAL_TERM_LIMIT")
        collected_coeffs.append(_collect_single_lambda_array(terms, quirks))

    canonical_str = json.dumps({"coefficients": collected_coeffs}, sort_keys=True, separators=(",", ":"))
    if candidate_text != canonical_str and not quirks:
        quirks.append("noncanonical_json_whitespace")

    return collected_coeffs, list(dict.fromkeys(quirks))


def _eval_wire_polynomial(
    coefficients: list[list[dict[str, Any]]],
    lam: int,
    j_val: int,
    d_val: int,
    k_val: int,
) -> Fraction:
    total = Fraction(0)
    lam_frac = Fraction(lam)
    j_frac = Fraction(j_val)
    d_frac = Fraction(d_val)
    k_frac = Fraction(k_val)

    for lam_power, terms in enumerate(coefficients):
        coeff_sum = Fraction(0)
        for term in terms:
            e_j, e_d, e_k = term["powers"]
            q_val = Fraction(term["q"])
            coeff_sum += q_val * (j_frac**e_j) * (d_frac**e_d) * (k_frac**e_k)
        total += coeff_sum * (lam_frac**lam_power)
    return total


def _verify_on_125_point_grid(
    coefficients: list[list[dict[str, Any]]],
    seed_hash: str,
) -> tuple[int, dict[str, Any] | None]:
    """Compare candidate polynomial against exact det(lambda*I - H(J,Delta,K)) over {-2,-1,0,1,2}^3."""
    matrices = host_charpoly.admit_public_matrices(seed_hash)
    mismatch_count = 0
    first_witness: dict[str, Any] | None = None

    for j_val in GRID_NODES:
        for d_val in GRID_NODES:
            for k_val in GRID_NODES:
                point_mismatch = False
                for lam_val in GRID_NODES:
                    char_mat = [
                        [
                            (Fraction(lam_val) if r == c else Fraction(0))
                            - (
                                matrices["constant"][r][c]
                                + Fraction(j_val) * matrices["J"][r][c]
                                + Fraction(d_val) * matrices["Delta"][r][c]
                                + Fraction(k_val) * matrices["K"][r][c]
                            )
                            for c in range(4)
                        ]
                        for r in range(4)
                    ]
                    expected_det = host_charpoly.eval_scalar_det_4x4(char_mat)
                    claimed_det = _eval_wire_polynomial(coefficients, lam_val, j_val, d_val, k_val)
                    if claimed_det != expected_det:
                        point_mismatch = True
                        if first_witness is None:
                            first_witness = {
                                "parameters": {"J": j_val, "Delta": d_val, "K": k_val},
                                "lambda": lam_val,
                                "claimed": str(claimed_det),
                                "expected": str(expected_det),
                            }
                        break
                if point_mismatch:
                    mismatch_count += 1

    return mismatch_count, first_witness


def evaluate_eis_charpoly_stage(
    candidate_text: str,
    seed_hash: str = SUPPORTED_SEED_SHA256,
) -> dict[str, Any]:
    """Evaluate Stage 1 charpoly proposal under the EIS Matzinger Two-Signal Danger Gate."""
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ValueError(f"Unsupported seed hash: {seed_hash}")

    matcher, thymus_rule, thymus_selection = screen_normalized_charpoly_detector()
    regulator = TwoSignalRegulatorV1()
    raw_bytes = candidate_text.encode("utf-8", errors="replace") if isinstance(candidate_text, str) else b""

    try:
        collected_coeffs, surface_quirks = _parse_and_collect_equivalent_terms(candidate_text)
    except _LenientWireParseError as exc:
        parse_code = str(exc)
        danger = Signal2Danger(
            danger_type="MALFORMED_PAYLOAD",
            severity=DangerSeverity.HIGH,
            defect_count=1,
            evidence_digest="sha256:" + hashlib.sha256(b"host-malformed-payload:" + raw_bytes).hexdigest(),
            observer_id="HOST",
        )
        s1_matches = matcher.match_antigen(candidate_text if isinstance(candidate_text, str) else "", (thymus_rule,))
        outcome = regulator.evaluate(
            content=candidate_text if isinstance(candidate_text, str) else "",
            matches=s1_matches,
            danger=danger,
            detector_id=matcher.matcher_id,
            offsets_are_content=False,
        )
        return {
            "accepted": False,
            "status": "eis_two_signal_refused",
            "disposition": outcome.decision.value,
            "two_signal_decision": outcome.decision.value,
            "danger_type": danger.danger_type,
            "danger_observer": danger.observer_id,
            "refusal_code": parse_code,
            "surface_quirks": [],
            "normalized_json": None,
            "eis_charpoly_context": None,
            "thymus_admitted": thymus_selection.is_admitted,
            "final_answer_certified": False,
        }

    # Check total parameter degree bounds and exact 125-point rational grid agreement
    degree_exceeded = any(
        sum(term["powers"]) > host_charpoly.DEGREE_BOUND_PER_VARIABLE
        for terms in collected_coeffs
        for term in terms
    )
    mismatch_count, mismatch_witness = _verify_on_125_point_grid(collected_coeffs, seed_hash)
    certified_compact = host_charpoly.build_certified_context(seed_hash, compact=True)
    host_derived = host_charpoly.derive_host_charpoly(seed_hash)

    surface_matches = tuple(
        Signal1Match(
            epitope_name=quirk,
            pattern_matched=quirk,
            confidence=1.0,
            offset=0,
            detector_id="surface_wire_scanner",
            matched_locus=quirk,
            match_signature=quirk,
        )
        for quirk in surface_quirks
    )

    if degree_exceeded or mismatch_count > 0 or collected_coeffs != host_derived["normalized_coefficients"]:
        defect_total = max(mismatch_count, 1)
        danger = Signal2Danger(
            danger_type="REPLAY_FAILURE",
            severity=DangerSeverity.CRITICAL,
            defect_count=defect_total,
            evidence_digest="sha256:" + hashlib.sha256(b"host-grid-replay-failure:" + raw_bytes).hexdigest(),
            observer_id="HOST",
        )
        outcome = regulator.evaluate(
            content=candidate_text,
            matches=surface_matches,
            danger=danger,
            detector_id="surface_wire_scanner",
            offsets_are_content=False,
        )
        return {
            "accepted": False,
            "status": "eis_two_signal_refused",
            "disposition": outcome.decision.value,
            "two_signal_decision": outcome.decision.value,
            "danger_type": danger.danger_type,
            "danger_observer": danger.observer_id,
            "refusal_code": "DEGREE_LIMIT_EXCEEDED" if degree_exceeded else "REFUTED_ON_125_POINT_GRID",
            "grid_mismatch_count": mismatch_count,
            "grid_witness": mismatch_witness,
            "surface_quirks": surface_quirks,
            "normalized_json": None,
            "eis_charpoly_context": None,
            "thymus_admitted": thymus_selection.is_admitted,
            "final_answer_certified": False,
        }

    # Candidate represents the exact characteristic polynomial; pass collected form through charpoly_wire
    wire_receipt = wire.normalize_candidate(
        json.dumps({"coefficients": collected_coeffs}, separators=(",", ":"))
    )
    if not wire_receipt["accepted"] or wire_receipt["normalized_json"] is None:
        raise ValueError("Internal invariant failure: verified charpoly rejected by charpoly_wire")
    normalized_json = wire_receipt["normalized_json"]

    # Confirm ThymusGate-admitted NormalizedMatcher produces zero autoimmune hits on normalized wire
    autoimmune_hits = matcher.match_antigen(normalized_json, (thymus_rule,))
    if autoimmune_hits:
        raise ValueError("Unexpected autoimmune hit on canonical normalized charpoly wire")

    outcome = regulator.evaluate(
        content=candidate_text,
        matches=surface_matches,
        danger=None,
        detector_id="surface_wire_scanner",
        offsets_are_content=False,
    )

    disposition = (
        "DIAGNOSTIC_NORMALIZED"
        if outcome.decision is DangerDecision.DIAGNOSTIC_ONLY
        else outcome.decision.value
    )
    status = "DIAGNOSTIC_NORMALIZED" if disposition == "DIAGNOSTIC_NORMALIZED" else "CERTIFIED_IDENTITY"

    solver_context_obj = {
        "schema": "pfp.eis-two-signal.charpoly-context.v1",
        "seed_sha256": seed_hash,
        "disposition": disposition,
        "normalized_coefficients": json.loads(normalized_json)["coefficients"],
        "certified_intermediate_context": certified_compact,
        "limitations": {
            "final_answer_certified": False,
            "scope": "intermediate_characteristic_polynomial_det(lambda*I - H)_only",
        },
    }

    return {
        "accepted": True,
        "status": status,
        "disposition": disposition,
        "two_signal_decision": outcome.decision.value,
        "danger_type": None,
        "danger_observer": None,
        "refusal_code": None,
        "surface_quirks": surface_quirks,
        "normalized_json": normalized_json,
        "normalized_sha256": wire_receipt["normalized_sha256"],
        "eis_charpoly_context": json.dumps(solver_context_obj, sort_keys=True, separators=(",", ":")),
        "thymus_admitted": thymus_selection.is_admitted,
        "grid_points_verified": 125,
        "final_answer_certified": False,
    }


def build_pciv_quotient_artifact(seed_hash: str = SUPPORTED_SEED_SHA256) -> dict[str, Any]:
    """Run OperationalWorkflowQuotientV1 over a 6-candidate population and fence seed_prompt.txt."""
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ValueError(f"Unsupported seed hash: {seed_hash}")

    seed_bytes = (HERE / "seed_prompt.txt").read_bytes()
    actual_seed_sha = hashlib.sha256(seed_bytes).hexdigest()
    if actual_seed_sha != seed_hash:
        raise ValueError(f"Frozen seed SHA-256 mismatch: expected {seed_hash}, got {actual_seed_sha}")

    # Byte-fence seed_prompt.txt inside a governed template and verify post-mutation integrity
    fencer = ProtectedSpanEvolutionV1()
    initial_prefix = b"[GOVERNED_OBLIGATION_HEADER v1]\n"
    updated_prefix = b"[GOVERNED_OBLIGATION_HEADER v1.1: verify all 5 sections and parameter branches]\n"
    suffix = b"\n[END_IMMUTABLE_TASK_SEED]"
    fenced_initial = fencer.create_fenced_template(
        prefix_bytes=initial_prefix,
        seed_bytes=seed_bytes,
        suffix_bytes=suffix,
    )
    fenced_evolved = fencer.mutate_governed_span(
        fenced_initial,
        edit_start_byte=0,
        edit_end_byte=len(initial_prefix),
        replacement_bytes=updated_prefix,
    )

    # Construct 6-candidate workflow population:
    # - 2 idempotent-duplicate pipelines collapse
    # - noncommuting (normalize -> check) vs (check -> normalize) remain distinct
    op_seed_to_wire = WorkflowStageSpec(
        op_kind="extract_public_wire",
        input_colour="Seed",
        output_colour="Wire",
        instruction_or_checker_id="pauli_public_wire_v1",
        idempotent=False,
    )
    op_normalize = WorkflowStageSpec(
        op_kind="charpoly_wire_normalize",
        input_colour="Wire",
        output_colour="Wire",
        instruction_or_checker_id="charpoly_wire_normalize_v1",
        idempotent=True,
    )
    op_check = WorkflowStageSpec(
        op_kind="two_signal_grid_check",
        input_colour="Wire",
        output_colour="Wire",
        instruction_or_checker_id="eis_two_signal_grid_125_v1",
        idempotent=False,
    )
    op_solve_from_wire = WorkflowStageSpec(
        op_kind="obligation_synthesize",
        input_colour="Wire",
        output_colour="Answer",
        instruction_or_checker_id="pciv_obligation_solve_v1",
        idempotent=False,
    )
    op_direct_solve = WorkflowStageSpec(
        op_kind="direct_solve",
        input_colour="Seed",
        output_colour="Answer",
        instruction_or_checker_id="direct_seed_baseline_v1",
        idempotent=False,
    )

    population = (
        CandidateWorkflowSpec(
            "wf_normalize_then_check",
            (op_seed_to_wire, op_normalize, op_check, op_solve_from_wire),
            obligation_pass_fraction=Fraction(5, 5),
            byte_or_token_cost=1200,
        ),
        CandidateWorkflowSpec(
            "wf_normalize_dup_then_check",
            (op_seed_to_wire, op_normalize, op_normalize, op_check, op_solve_from_wire),
            obligation_pass_fraction=Fraction(5, 5),
            byte_or_token_cost=1380,
        ),
        CandidateWorkflowSpec(
            "wf_check_then_normalize",
            (op_seed_to_wire, op_check, op_normalize, op_solve_from_wire),
            obligation_pass_fraction=Fraction(4, 5),
            byte_or_token_cost=1260,
        ),
        CandidateWorkflowSpec(
            "wf_check_then_normalize_dup",
            (op_seed_to_wire, op_check, op_normalize, op_normalize, op_solve_from_wire),
            obligation_pass_fraction=Fraction(4, 5),
            byte_or_token_cost=1420,
        ),
        CandidateWorkflowSpec(
            "wf_unmeasured_wire_probe",
            (op_seed_to_wire, op_normalize, op_solve_from_wire),
            obligation_pass_fraction=None,
            byte_or_token_cost=950,
        ),
        CandidateWorkflowSpec(
            "wf_direct_seed_baseline",
            (op_direct_solve,),
            obligation_pass_fraction=Fraction(3, 5),
            byte_or_token_cost=450,
            is_baseline=True,
        ),
    )

    quotient_engine = OperationalWorkflowQuotientV1()
    report = quotient_engine.evaluate(population, reserve_cap=10)
    rep_by_id = {rep.workflow.workflow_id: rep for rep in report.representatives}

    return {
        "schema": "pfp.pciv-operational-quotient.v1",
        "seed_sha256": seed_hash,
        "input_candidate_count": len(population),
        "surviving_representative_count": len(report.representatives),
        "collapsed_duplicate_count": len(report.collapsed_duplicates),
        "collapsed_duplicate_ids": [d.workflow_id for d in report.collapsed_duplicates],
        "representatives": [
            {
                "workflow_id": rep.workflow.workflow_id,
                "canonical_stage_count": len(rep.canonical_stages),
                "canonical_trace_sha256": rep.canonical_trace_sha256,
                "collapsed_member_ids": list(rep.collapsed_member_ids),
            }
            for rep in report.representatives
        ],
        "noncommuting_traces_distinct": (
            rep_by_id["wf_normalize_then_check"].canonical_trace_sha256
            != rep_by_id["wf_check_then_normalize"].canonical_trace_sha256
        ),
        "reserve_quotas_cap10": report.reserve_allocation.reserve_quotas,
        "pareto_fronts": [list(front) for front in report.reserve_allocation.pareto_fronts],
        "reserve_buckets": {k: list(v) for k, v in report.reserve_allocation.buckets.items()},
        "protected_seed_fence": {
            "seed_sha256": fenced_evolved.seed_sha256,
            "seed_byte_length": len(fenced_evolved.seed_bytes),
            "span_start_byte": fenced_evolved.seed_span.start_byte,
            "span_end_byte": fenced_evolved.seed_span.end_byte,
            "verified_byte_identical": (
                fenced_evolved.composite_bytes[
                    fenced_evolved.seed_span.start_byte : fenced_evolved.seed_span.end_byte
                ]
                == seed_bytes
            ),
        },
        "limitations": {
            "final_answer_certified": False,
            "scope": "pre_dispatch_workflow_quotient_and_seed_fence_only",
        },
    }


def public_charpoly_input_context(seed_hash: str = SUPPORTED_SEED_SHA256) -> dict[str, Any]:
    """Build public Hamiltonian matrix context for Stage 1 charpoly proposal."""
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ValueError(f"Unsupported seed hash: {seed_hash}")
    matrix_artifact = pauli.public_input_artifact(seed_hash)
    return {
        "schema": "pfp.eis-charpoly.public-input.v1",
        "seed_sha256": seed_hash,
        "basis": ["00", "01", "10", "11"],
        "parameters": ["J", "Delta", "K"],
        "public_hamiltonian_matrices": matrix_artifact["coefficient_matrices"],
        "wire_format": {
            "required_keys": ["coefficients"],
            "lambda_powers_ascending": [0, 1, 2, 3, 4],
            "term_schema": {"powers": "[eJ, eDelta, eK] in 0..4", "q": "signed integer or fraction string"},
        },
    }


def execute_eis_pciv_plan(
    plan_id: str,
    provider: Any,
    *,
    seed_hash: str = SUPPORTED_SEED_SHA256,
    max_output_tokens: int = 16000,
) -> dict[str, Any]:
    """Execute one of EIS_PCIV_PLANS against an offline or mock Provider port without global side effects."""
    if plan_id not in EIS_PCIV_PLANS:
        raise ValueError(f"Unknown EIS/PCIV plan: {plan_id!r}")
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ValueError(f"Unsupported seed hash: {seed_hash}")

    spec = EIS_PCIV_PLANS[plan_id]
    for filename, expected_sha in spec["source_pins"].items():
        if _file_sha256(pin_path(filename)) != expected_sha:
            raise ValueError(f"Source pin changed for {filename}")

    seed_bytes = (HERE / "seed_prompt.txt").read_bytes()
    if hashlib.sha256(seed_bytes).hexdigest() != seed_hash:
        raise ValueError("Frozen seed_prompt.txt bytes do not match seed_hash")
    seed_text = seed_bytes.decode("utf-8")

    artifacts: dict[str, str] = {}
    if plan_id == "pciv_quotient_obligation_v1":
        quotient_art = build_pciv_quotient_artifact(seed_hash)
        artifacts["pciv_quotient_context"] = json.dumps(quotient_art, sort_keys=True, separators=(",", ":"))

    calls: list[dict[str, Any]] = []
    stage_checks: list[dict[str, Any]] = []
    total_quoted_microusd = 0
    status = "offline_fixture_completed" if getattr(provider, "offline", False) else "completed"

    for stage in spec["stages"]:
        messages = [
            {"role": "system", "content": stage["instruction"]},
            {"role": "user", "content": seed_text},
        ]
        if plan_id == "eis_two_signal_charpoly_v1" and stage["id"] == "charpoly_propose":
            pub_ctx = public_charpoly_input_context(seed_hash)
            messages.append(
                {
                    "role": "user",
                    "content": "Public affine Hamiltonian contract:\n"
                    + json.dumps(pub_ctx, sort_keys=True, separators=(",", ":")),
                }
            )
        for vis_name in stage["visible_artifacts"]:
            messages.append(
                {
                    "role": "user",
                    "content": "Untrusted intermediate context follows. It is not the answer key.\n"
                    + artifacts[vis_name],
                }
            )

        req_tokens = min(max_output_tokens, stage["max_output_tokens"])
        request = {
            "messages": messages,
            "max_output_tokens": req_tokens,
            "tools": [],
            "retries": 0,
        }
        quote = provider.upper_quote(request)
        total_quoted_microusd += quote
        reply = provider.complete(request)
        calls.append(
            {
                "stage_id": stage["id"],
                "request": request,
                "quote_microusd": quote,
                "response_text": reply.text,
            }
        )
        artifacts[stage["id"]] = reply.text

        if plan_id == "eis_two_signal_charpoly_v1" and stage["id"] == "charpoly_propose":
            gate_res = evaluate_eis_charpoly_stage(reply.text, seed_hash)
            stage_checks.append(gate_res)
            if not gate_res["accepted"]:
                status = "eis_two_signal_refused"
                break
            artifacts["eis_charpoly_context"] = gate_res["eis_charpoly_context"]

    return {
        "plan_id": plan_id,
        "seed_sha256": seed_hash,
        "status": status,
        "paid_calls_executed": len(calls),
        "total_quoted_microusd": total_quoted_microusd,
        "calls": calls,
        "stage_checks": stage_checks,
        "answer_text": artifacts.get("solve"),
        "final_answer_certified": False,
    }


EIS_PCIV_PLANS: dict[str, dict[str, Any]] = {
    "eis_two_signal_charpoly_v1": {
        "plan_id": "eis_two_signal_charpoly_v1",
        "version": "1.0",
        "max_paid_calls": 2,
        "max_output_tokens": 16000,
        "max_total_output_tokens": 16000,
        "answer_stage": "solve",
        "checked": True,
        "stages": [
            {
                "id": "charpoly_propose",
                "instruction": CHARPOLY_PROPOSE_INSTRUCTION,
                "max_output_tokens": 1500,
                "visible_artifacts": [],
            },
            {
                "id": "solve",
                "instruction": EIS_SOLVE_INSTRUCTION,
                "max_output_tokens": 14500,
                "visible_artifacts": ["charpoly_propose", "eis_charpoly_context"],
            },
        ],
        "scope": (
            "2-stage EIS Matzinger two-signal characteristic-polynomial workflow: "
            "Thymus-admitted NormalizedMatcher tolerates benign rational/monomial formatting "
            "variations via value-preserving normalization while Host Signal 2 halts malformed "
            "or 125-point-grid-refuted polynomials before Stage 2 synthesis. "
            "Final QM answer is not certified."
        ),
        "source_pins": {},
    },
    "pciv_quotient_obligation_v1": {
        "plan_id": "pciv_quotient_obligation_v1",
        "version": "1.0",
        "max_paid_calls": 1,
        "max_output_tokens": 16000,
        "max_total_output_tokens": 16000,
        "answer_stage": "solve",
        "checked": True,
        "stages": [
            {
                "id": "solve",
                "instruction": PCIV_OBLIGATION_INSTRUCTION,
                "max_output_tokens": 16000,
                "visible_artifacts": ["pciv_quotient_context"],
            },
        ],
        "scope": (
            "1-stage matched-16,000-token obligation-framed workflow selected via "
            "PCIV OperationalWorkflowQuotientV1 equivalence reduction and ProtectedSpanEvolutionV1 "
            "seed byte fencing over public seed_prompt.txt obligations only. "
            "Final QM answer is not certified."
        ),
        "source_pins": {},
    },
}

_LIVE_SOURCE_PINS = prepare_source_pins()
for _spec in EIS_PCIV_PLANS.values():
    _spec["source_pins"] = deepcopy(_LIVE_SOURCE_PINS)

__all__ = [
    "CHARPOLY_PROPOSE_INSTRUCTION",
    "EIS_PCIV_PLANS",
    "EIS_SOLVE_INSTRUCTION",
    "PCIV_OBLIGATION_INSTRUCTION",
    "SUPPORTED_SEED_SHA256",
    "build_pciv_quotient_artifact",
    "evaluate_eis_charpoly_stage",
    "execute_eis_pciv_plan",
    "prepare_source_pins",
    "public_charpoly_input_context",
    "screen_normalized_charpoly_detector",
]
