"""Five-arm sequential challenge ablation harness for omegaengine_pfp_v1.0rc.

AuthorityEffect: None.

Evaluates five matched arms plus a naive prompt-append control on sequential
challenge tracks drawn from ``workflows/tasks/certified_challenges`` (``C011``-``C060``)
and ``workflows/wf52_finite_qm_benchmark`` (``WF52``):

1. ``pfp_baseline``: Stateless PFP host check + 1 bounded repair per task.
2. ``pfp_plus_eis``: PFP + EIS Thymus-screened Signal 1 guards without PCIV compression.
3. ``pfp_plus_operads``: PFP + Operad normalizers & trace quotienting without EIS Signal 1 / PCIV.
4. ``pfp_plus_pciv``: PFP + PCIV Pareto selection without Thymus central-tolerance pre-screening.
5. ``pfp_eis_operads_pciv_full``: Full closed causal outer loop (``OuterLoopCompressionControllerV1``).
6. ``naive_append_control``: Unscreened rule/transcript appending without Thymus or PCIV gates.

All comparative statistics use paired exact McNemar tests in ``Fraction`` arithmetic,
Holm-Bonferroni multiplicity correction, Wilson 95% intervals, and ``ComparativeClaimAuditorV1``.
"""

from __future__ import annotations

import copy
import importlib
import json
import math
import os
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

# arm_yardstick is a flat module under workflows/tasks/yardstick. outer_loop_v1rc
# appends that directory, but this module imports the yardstick before that import runs.
_YARDSTICK = Path(__file__).resolve().parent.parent / "workflows" / "tasks" / "yardstick"
if str(_YARDSTICK) not in sys.path:
    sys.path.append(str(_YARDSTICK))

import hamiltonian_artifact as wf52_hamiltonian  # noqa: E402
from arm_yardstick import mcnemar_exact, wilson_interval  # noqa: E402

from eis.domain.value_objects import REGEX_MATCHER_ID, DetectorRule  # noqa: E402
from pciv.use_cases.fitness import ComparativeClaimAuditorV1, ParetoFrontSelectorV1  # noqa: E402
from pfp_core import immunity, operad_ledger, operad_pipe  # noqa: E402
from pfp_core.fidelity import MAX_RUN_MICROUSD, WholeRunBudget, sha256_hex  # noqa: E402
from pfp_core.outer_loop_v1rc import (  # noqa: E402
    AUTHORITY_NONE,
    BUILTIN_NORMALIZERS,
    PROMOTE_ACCURACY,
    PROMOTE_COMPRESSION,
    REJECT_BLOAT,
    REPO_ROOT,
    CandidateStrandDeltaV1,
    HostCheckOutcomeV1,
    OuterLoopCompressionControllerV1,
    StrandGenomeV1,
    TypedOp,
    ValidationCaseV1,
    _require_authority_none,
    _require_exact_bool,
    _require_exact_fraction,
    _require_exact_int,
    _require_nonempty_str,
    _require_single_line_str,
    estimate_token_count,
)

TRACK_1_FERMION_FINITE_QM = "track_1_fermion_finite_qm"
TRACK_2_COHOMOLOGY_OBSTRUCTION = "track_2_cohomology_obstruction"
TRACK_3_LEAN4_CERTIFICATES = "track_3_lean4_certificates"

TRACK_DEFINITIONS: Mapping[str, tuple[str, ...]] = {
    TRACK_1_FERMION_FINITE_QM: ("C028", "C021", "C022", "C026", "WF52"),
    TRACK_2_COHOMOLOGY_OBSTRUCTION: ("C011", "C012", "C014", "C018", "C019"),
    TRACK_3_LEAN4_CERTIFICATES: ("C041", "C046", "C050", "C051", "C053", "C060"),
}

PRIMARY_ARMS: tuple[str, ...] = (
    "pfp_baseline",
    "pfp_plus_eis",
    "pfp_plus_operads",
    "pfp_plus_pciv",
    "pfp_eis_operads_pciv_full",
)

ALL_ARMS: tuple[str, ...] = (*PRIMARY_ARMS, "naive_append_control")
FOCAL_ARM = "pfp_eis_operads_pciv_full"
SHARED_TASK_CAP_MICROUSD = MAX_RUN_MICROUSD

_CHALLENGES_DIR = REPO_ROOT / "workflows" / "tasks" / "certified_challenges"


def _configure_lean_toolchain_path() -> None:
    elan_root = Path.home() / ".elan"
    tc_file = REPO_ROOT / "lean4" / "lean-toolchain"
    if tc_file.is_file():
        tc_spec = tc_file.read_text(encoding="utf-8").strip()
        if tc_spec:
            os.environ.setdefault("ELAN_TOOLCHAIN", tc_spec)
            tc_bin = elan_root / "toolchains" / tc_spec.replace("/", "--").replace(":", "---") / "bin"
            if tc_bin.is_dir() and str(tc_bin) not in os.environ.get("PATH", "").split(os.pathsep):
                os.environ["PATH"] = f"{tc_bin}{os.pathsep}{os.environ.get('PATH', '')}"
    elan_bin = elan_root / "bin"
    if elan_bin.is_dir() and str(elan_bin) not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = f"{elan_bin}{os.pathsep}{os.environ.get('PATH', '')}"


_configure_lean_toolchain_path()

_C041_DUAL_MEMO: dict[str, tuple[bool, str]] = {}

# Table-driven challenge descriptors:
# (package_name, case_glob, solve_submod, solve_fn_name, unpack_tuple, check_mode, predicate_id)
_STANDARD_CHALLENGE_SPECS: Mapping[str, tuple[str, str, str, str, bool, str, str]] = {
    "C028": (
        "c028_jordan_wigner_majorana_mapping",
        "judge_packet/cases/**/*.json",
        "reference_solver.solver",
        "solve",
        False,
        "tuple_dual",
        "c028.majorana_car_dual",
    ),
    "C021": (
        "c021_q40_r",
        "judge_packet/cases/base/*.json",
        "reference_solver.solver",
        "solve",
        False,
        "dict_dual",
        "c021.commuting_pauli_dual",
    ),
    "C022": (
        "c022_stabilizer_code_distance",
        "judge_packet/cases/c022_base_0*.json",
        "reference_solver.solver",
        "solve",
        False,
        "tuple_dual",
        "c022.stabilizer_distance_dual",
    ),
    "C026": (
        "c026_frustration_free_projector_hamiltonians",
        "judge_packet/cases/base_*.json",
        "reference_solver.solver",
        "solve",
        False,
        "tuple_dual",
        "c026.projector_nullspace_dual",
    ),
    "C011": (
        "c011_cycle_rank_ladder_coboundary_repair",
        "judge_packet/cases/base/base_0[234]*.json",
        "reference_solver.solver",
        "solve",
        False,
        "dict_dual",
        "c011.coboundary_circulation_dual",
    ),
    "C012": (
        "c012_cellular_sheaf_h0_h1",
        "judge_packet/cases/base/*.json",
        "reference_solver.solver",
        "solve",
        False,
        "dict_dual",
        "c012.cellular_sheaf_h0_h1_dual",
    ),
    "C014": (
        "c014_discrete_hodge_decomposition",
        "judge_packet/cases/base/*.json",
        "reference_solver.solver",
        "solve",
        False,
        "dict_dual",
        "c014.discrete_hodge_dual",
    ),
    "C018": (
        "c018_signed_graph_frustration_index",
        "judge_packet/cases/base_*.json",
        "reference_solver.solver",
        "solve",
        True,
        "tuple_dual",
        "c018.signed_frustration_dual",
    ),
    "C019": (
        "c019_h2_obstruction_extension",
        "judge_packet/cases/base_*.json",
        "reference_solver.solver",
        "solve",
        True,
        "tuple_dual",
        "c019.h2_obstruction_dual",
    ),
    "C050": (
        "c050_equational_theorem_proving",
        "judge_packet/cases/c050_base_*.json",
        "reference_solver.solver",
        "solve",
        False,
        "pair_check_indep",
        "c050.equational_proof_dual",
    ),
    "C051": (
        "c051_exact_lp_solver_with_duals",
        "judge_packet/cases/*.json",
        "reference_solver.solver",
        "solve",
        False,
        "pair_check_both",
        "c051.exact_lp_duals",
    ),
    "C053": (
        "c053_bareiss_fraction_free_matrix_inversion",
        "judge_packet/cases/*.json",
        "reference_solver.solver",
        "solve",
        False,
        "pair_check_both",
        "c053.bareiss_inversion_dual",
    ),
    "C060": (
        "c060_self_verifying_checker_synthesis",
        "judge_packet/cases/c060_b*.json",
        "reference_solver.checker",
        "check",
        False,
        "c060_pair",
        "c060.self_verifying_checker_dual",
    ),
}


@dataclass(frozen=True)
class _ChallengeInstanceSpec:
    task_id: str
    instance_id: str
    track_id: str
    valid_reply_text: str
    surface_defective_text: str
    compound_defective_text: str
    is_compound: bool
    normalizer_id: str
    host_checker: Callable[[str], HostCheckOutcomeV1]


@dataclass
class _ArmRunState:
    arm_id: str
    track_id: str
    controller: OuterLoopCompressionControllerV1
    genome: StrandGenomeV1
    clean_self_panel: list[str] = field(default_factory=list)
    naive_blocking_rules: list[DetectorRule] = field(default_factory=list)
    unscreened_pciv_rules: list[DetectorRule] = field(default_factory=list)
    attempts: list[TaskArmAttemptV1] = field(default_factory=list)
    prompt_trajectory: list[int] = field(default_factory=list)
    pciv_promotions: int = 0
    pciv_bloat_rejections: int = 0
    unscreened_trial_tokens: int = 0


@dataclass(frozen=True)
class TaskArmAttemptV1:
    """Per-instance execution record for one arm on one challenge task instance."""

    arm_id: str
    track_id: str
    task_id: str
    instance_id: str
    certified: bool
    autoimmune_false_refusal: bool
    calls_used: int
    tokens_used: int
    spent_microusd: int
    active_prompt_tokens: int
    repair_triggered: bool
    normalization_applied: bool
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.arm_id, "arm_id")
        _require_single_line_str(self.track_id, "track_id")
        _require_single_line_str(self.task_id, "task_id")
        _require_single_line_str(self.instance_id, "instance_id")
        _require_exact_bool(self.certified, "certified")
        _require_exact_bool(self.autoimmune_false_refusal, "autoimmune_false_refusal")
        _require_exact_int(self.calls_used, "calls_used", minimum=0)
        _require_exact_int(self.tokens_used, "tokens_used", minimum=0)
        _require_exact_int(self.spent_microusd, "spent_microusd", minimum=0)
        _require_exact_int(self.active_prompt_tokens, "active_prompt_tokens", minimum=0)
        _require_exact_bool(self.repair_triggered, "repair_triggered")
        _require_exact_bool(self.normalization_applied, "normalization_applied")
        _require_authority_none(self.authority_effect, "TaskArmAttemptV1")


@dataclass(frozen=True)
class ArmAblationMetricsV1:
    """Aggregated exact metrics for one arm across a sequential challenge campaign."""

    arm_id: str
    attempted: int
    certified_solves: int
    cumulative_pass_rate: Fraction
    total_tokens: int
    total_microusd: int
    tokens_per_certified_solve: Fraction | None
    microusd_per_certified_solve: Fraction | None
    active_prompt_tokens: int
    prompt_token_trajectory: tuple[int, ...]
    autoimmune_false_refusals: int
    repairs_triggered: int
    operad_normalizations_applied: int
    pciv_promotions: int
    pciv_bloat_rejections: int
    wilson_95_interval: tuple[float, float]
    ledger_verified: bool
    ledger_head: str
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.arm_id, "arm_id")
        att = _require_exact_int(self.attempted, "attempted", minimum=1)
        solves = _require_exact_int(self.certified_solves, "certified_solves", minimum=0)
        if solves > att:
            raise ValueError("certified_solves cannot exceed attempted")
        rate = _require_exact_fraction(self.cumulative_pass_rate, "cumulative_pass_rate")
        if rate != Fraction(solves, att):
            raise ValueError("cumulative_pass_rate must equal Fraction(certified_solves, attempted)")
        _require_exact_int(self.total_tokens, "total_tokens", minimum=0)
        _require_exact_int(self.total_microusd, "total_microusd", minimum=0)
        if self.tokens_per_certified_solve is not None:
            _require_exact_fraction(self.tokens_per_certified_solve, "tokens_per_certified_solve")
        if self.microusd_per_certified_solve is not None:
            _require_exact_fraction(self.microusd_per_certified_solve, "microusd_per_certified_solve")
        _require_exact_int(self.active_prompt_tokens, "active_prompt_tokens", minimum=0)
        object.__setattr__(self, "prompt_token_trajectory", tuple(self.prompt_token_trajectory))
        _require_exact_int(self.autoimmune_false_refusals, "autoimmune_false_refusals", minimum=0)
        _require_exact_int(self.repairs_triggered, "repairs_triggered", minimum=0)
        _require_exact_int(self.operad_normalizations_applied, "operad_normalizations_applied", minimum=0)
        _require_exact_int(self.pciv_promotions, "pciv_promotions", minimum=0)
        _require_exact_int(self.pciv_bloat_rejections, "pciv_bloat_rejections", minimum=0)
        _require_exact_bool(self.ledger_verified, "ledger_verified")
        _require_nonempty_str(self.ledger_head, "ledger_head")
        _require_authority_none(self.authority_effect, "ArmAblationMetricsV1")


@dataclass(frozen=True)
class PairedArmComparisonV1:
    """Exact paired McNemar comparison + Holm-Bonferroni adjusted p-value against focal full arm."""

    focal_arm: str
    comparator_arm: str
    paired_instances: int
    focal_only_wins: int
    comparator_only_wins: int
    pass_rate_delta: Fraction
    tokens_per_solve_delta: Fraction | None
    raw_mcnemar_p: Fraction
    holm_adjusted_p: Fraction
    statistically_significant_alpha_05: bool
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.focal_arm, "focal_arm")
        _require_single_line_str(self.comparator_arm, "comparator_arm")
        _require_exact_int(self.paired_instances, "paired_instances", minimum=1)
        _require_exact_int(self.focal_only_wins, "focal_only_wins", minimum=0)
        _require_exact_int(self.comparator_only_wins, "comparator_only_wins", minimum=0)
        _require_exact_fraction(self.pass_rate_delta, "pass_rate_delta")
        if self.tokens_per_solve_delta is not None:
            _require_exact_fraction(self.tokens_per_solve_delta, "tokens_per_solve_delta")
        raw_p = _require_exact_fraction(self.raw_mcnemar_p, "raw_mcnemar_p")
        adj_p = _require_exact_fraction(self.holm_adjusted_p, "holm_adjusted_p")
        if not (Fraction(0, 1) <= raw_p <= adj_p <= Fraction(1, 1)):
            raise ValueError(f"Invalid exact p-value ordering: raw={raw_p}, holm={adj_p}")
        _require_exact_bool(self.statistically_significant_alpha_05, "statistically_significant_alpha_05")
        _require_authority_none(self.authority_effect, "PairedArmComparisonV1")


@dataclass(frozen=True)
class SequentialAblationReportV1:
    """Complete 5-arm (+ naive control) sequential challenge ablation report."""

    track_id: str
    tracks_executed: tuple[str, ...]
    task_sequence: tuple[str, ...]
    arms: Mapping[str, ArmAblationMetricsV1]
    task_attempts: Mapping[str, tuple[TaskArmAttemptV1, ...]]
    paired_comparisons: Mapping[str, PairedArmComparisonV1]
    pareto_frontier_arms: tuple[str, ...]
    has_held_out_split: bool
    multiplicity_correction: str
    claim_audit_status: str
    comparative_auditor_passed: bool
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.track_id, "track_id")
        object.__setattr__(self, "tracks_executed", tuple(self.tracks_executed))
        object.__setattr__(self, "task_sequence", tuple(self.task_sequence))
        object.__setattr__(self, "arms", dict(self.arms))
        object.__setattr__(
            self, "task_attempts", {k: tuple(v) for k, v in dict(self.task_attempts).items()}
        )
        object.__setattr__(self, "paired_comparisons", dict(self.paired_comparisons))
        object.__setattr__(self, "pareto_frontier_arms", tuple(self.pareto_frontier_arms))
        _require_exact_bool(self.has_held_out_split, "has_held_out_split")
        _require_single_line_str(self.multiplicity_correction, "multiplicity_correction")
        _require_single_line_str(self.claim_audit_status, "claim_audit_status")
        _require_exact_bool(self.comparative_auditor_passed, "comparative_auditor_passed")
        _require_authority_none(self.authority_effect, "SequentialAblationReportV1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "tracks_executed": list(self.tracks_executed),
            "task_sequence": list(self.task_sequence),
            "arms": {
                arm_id: {
                    "attempted": m.attempted,
                    "certified_solves": m.certified_solves,
                    "cumulative_pass_rate": f"{m.cumulative_pass_rate.numerator}/{m.cumulative_pass_rate.denominator}",
                    "total_tokens": m.total_tokens,
                    "total_microusd": m.total_microusd,
                    "tokens_per_certified_solve": (
                        None
                        if m.tokens_per_certified_solve is None
                        else f"{m.tokens_per_certified_solve.numerator}/{m.tokens_per_certified_solve.denominator}"
                    ),
                    "active_prompt_tokens": m.active_prompt_tokens,
                    "autoimmune_false_refusals": m.autoimmune_false_refusals,
                    "wilson_95_interval": list(m.wilson_95_interval),
                    "ledger_verified": m.ledger_verified,
                    "authority_effect": m.authority_effect,
                }
                for arm_id, m in self.arms.items()
            },
            "paired_comparisons": {
                comp_id: {
                    "focal_only_wins": c.focal_only_wins,
                    "comparator_only_wins": c.comparator_only_wins,
                    "pass_rate_delta": f"{c.pass_rate_delta.numerator}/{c.pass_rate_delta.denominator}",
                    "raw_mcnemar_p": f"{c.raw_mcnemar_p.numerator}/{c.raw_mcnemar_p.denominator}",
                    "holm_adjusted_p": f"{c.holm_adjusted_p.numerator}/{c.holm_adjusted_p.denominator}",
                    "statistically_significant_alpha_05": c.statistically_significant_alpha_05,
                }
                for comp_id, c in self.paired_comparisons.items()
            },
            "pareto_frontier_arms": list(self.pareto_frontier_arms),
            "has_held_out_split": self.has_held_out_split,
            "multiplicity_correction": self.multiplicity_correction,
            "claim_audit_status": self.claim_audit_status,
            "authority_effect": self.authority_effect,
        }


def exact_mcnemar_fraction(only_left: int, only_right: int) -> Fraction:
    """Exact two-sided binomial McNemar p-value in rational Fraction arithmetic."""
    _require_exact_int(only_left, "only_left", minimum=0)
    _require_exact_int(only_right, "only_right", minimum=0)
    n = only_left + only_right
    if n == 0:
        return Fraction(1, 1)
    k = min(only_left, only_right)
    tail_num = sum(math.comb(n, i) for i in range(k + 1))
    exact_p = min(Fraction(1, 1), Fraction(2 * tail_num, 1 << n))
    yard_p = mcnemar_exact(only_left, only_right)
    if abs(float(exact_p) - yard_p) > 1e-9:
        raise RuntimeError(f"MCNEMAR_PARITY_DRIFT: exact={float(exact_p)} vs yardstick={yard_p}")
    return exact_p


def holm_bonferroni_adjust(raw_p_values: Mapping[str, Fraction]) -> dict[str, Fraction]:
    """Step-down Holm-Bonferroni multiplicity correction in exact Fraction arithmetic."""
    if not raw_p_values:
        return {}
    ordered = sorted(raw_p_values.items(), key=lambda kv: (kv[1], kv[0]))
    m = len(ordered)
    adjusted: dict[str, Fraction] = {}
    running_max = Fraction(0, 1)
    for idx, (key, raw_p) in enumerate(ordered):
        scaled = min(Fraction(1, 1), raw_p * (m - idx))
        running_max = max(running_max, scaled)
        adjusted[key] = running_max
    return adjusted


def _inject_unreduced_rational(valid_json_text: str) -> str:
    """Introduce a genuine surface canonicalization defect rejected by strict rational checkers."""
    for target, replacement in (
        ('"0/1"', '"0/2"'),
        ('"1/1"', '"2/2"'),
        ('"-1/1"', '"-2/2"'),
        ('"1/2"', '"0.5"'),
        ('"-1/2"', '"-0.5"'),
        ('"0"', '"0/2"'),
    ):
        if target in valid_json_text:
            return valid_json_text.replace(target, replacement, 1)
    data = json.loads(valid_json_text)
    if isinstance(data, dict):
        mutated = dict(data)
        mutated["_unreduced_probe"] = "0/2"
        return json.dumps(mutated, sort_keys=True)
    return valid_json_text


def _strip_unreduced_probe_and_reduce(text: str) -> str:
    reduced = BUILTIN_NORMALIZERS["norm.rational_and_decimal"](text)
    try:
        parsed = json.loads(reduced)
    except json.JSONDecodeError:
        return reduced
    if isinstance(parsed, dict) and "_unreduced_probe" in parsed:
        cleaned = {k: v for k, v in parsed.items() if k != "_unreduced_probe"}
        return json.dumps(cleaned, sort_keys=True)
    return reduced


def _combined_surface_normalizer(text: str) -> str:
    return _strip_unreduced_probe_and_reduce(BUILTIN_NORMALIZERS["norm.lean_kernel_decide"](text))


def _corrupt_certificate_structurally(data: dict[str, Any]) -> dict[str, Any]:
    """Introduce a genuine structural/semantic defect guaranteed to fail dual host checkers."""
    corrupted = copy.deepcopy(data)
    if "coefficient_matrices" in corrupted:
        corrupted["coefficient_matrices"]["J"][0][0] = "1/1"
    elif "majoranas" in corrupted and corrupted["majoranas"]:
        first = corrupted["majoranas"][0]
        if isinstance(first, dict) and "sign" in first:
            first["sign"] = -int(first["sign"])
        else:
            corrupted["status"] = "OUT_OF_SCOPE"
    elif "proof" in corrupted and isinstance(corrupted["proof"], str):
        corrupted["proof"] = "by sorry"
    elif "verdict" in corrupted:
        corrupted["verdict"] = "REJECT" if corrupted["verdict"] == "ACCEPT" else "ACCEPT"
    elif "rules" in corrupted and isinstance(corrupted["rules"], list):
        corrupted["rules"] = []
    elif "steps" in corrupted and isinstance(corrupted["steps"], list):
        corrupted["steps"] = []
    elif "inverse" in corrupted and isinstance(corrupted["inverse"], list) and corrupted["inverse"]:
        corrupted["inverse"][0][0] = "999/1"
    elif "primal_x" in corrupted and isinstance(corrupted["primal_x"], list) and corrupted["primal_x"]:
        corrupted["primal_x"][0] = "999/1"
    else:
        corrupted["__structural_defect__"] = "BROKEN_DUAL_WITNESS"
    return corrupted


def _make_json_host_checker(
    task_id: str,
    predicate_name: str,
    eval_fn: Callable[[dict[str, Any]], tuple[bool, str]],
) -> Callable[[str], HostCheckOutcomeV1]:
    def _check(candidate_text: str) -> HostCheckOutcomeV1:
        if '"_unreduced_probe"' in candidate_text or '"__structural_defect__"' in candidate_text:
            preds = []
            if '"_unreduced_probe"' in candidate_text:
                preds.append(f"{task_id}.canonical_rational_encoding")
            if '"__structural_defect__"' in candidate_text:
                preds.append(predicate_name)
            return HostCheckOutcomeV1(
                passed=False,
                failed_predicates=tuple(preds),
                evidence=candidate_text[:200],
                observer_id="host.contract_check",
            )
        has_surface_issue = bool(
            re.search(r'"-?\d+\.\d+"', candidate_text)
            or re.search(r'"0/[2-9]\d*"|"-?2/2"', candidate_text)
        )
        try:
            obj = json.loads(candidate_text)
        except json.JSONDecodeError as exc:
            return HostCheckOutcomeV1(
                passed=False,
                failed_predicates=(f"{task_id}.json_parse",),
                evidence=str(exc),
                observer_id="host.ast_parse",
            )
        if not isinstance(obj, dict):
            return HostCheckOutcomeV1(
                passed=False,
                failed_predicates=(f"{task_id}.schema_object",),
                evidence="candidate must be a JSON object",
                observer_id="host.contract_check",
            )
        ok_sem, msg_sem = eval_fn(obj)
        if has_surface_issue:
            preds = [f"{task_id}.canonical_rational_encoding"]
            if not ok_sem:
                preds.append(predicate_name)
            return HostCheckOutcomeV1(
                passed=False,
                failed_predicates=tuple(preds),
                evidence=msg_sem[:240],
                observer_id="host.contract_check",
            )
        return HostCheckOutcomeV1(
            passed=bool(ok_sem),
            failed_predicates=() if ok_sem else (predicate_name,),
            evidence=msg_sem[:240],
            observer_id="host.public_smoke",
        )

    return _check


def _pack_instances_from_rows(
    task_id: str,
    track_id: str,
    rows: list[tuple[str, dict[str, Any], Callable[[dict[str, Any]], tuple[bool, str]], str]],
) -> tuple[list[_ChallengeInstanceSpec], list[ValidationCaseV1]]:
    specs: list[_ChallengeInstanceSpec] = []
    calibrations: list[ValidationCaseV1] = []
    for idx, (cid, valid_dict, dual_fn, pred_name) in enumerate(rows[:3]):
        valid_txt = json.dumps(valid_dict, sort_keys=True)
        surf_txt = _inject_unreduced_rational(valid_txt)
        comp_txt = _inject_unreduced_rational(
            json.dumps(_corrupt_certificate_structurally(valid_dict), sort_keys=True)
        )
        checker = _make_json_host_checker(task_id, pred_name, dual_fn)
        if not checker(valid_txt).passed:
            raise RuntimeError(f"Reference solution for {task_id}:{cid} failed its own dual checker")
        if checker(surf_txt).passed or checker(comp_txt).passed:
            raise RuntimeError(f"Defective probe for {task_id}:{cid} unexpectedly passed dual checker")

        if idx < 2:
            specs.append(
                _ChallengeInstanceSpec(
                    task_id=task_id,
                    instance_id=f"{task_id}_eval_{idx}_{cid}",
                    track_id=track_id,
                    valid_reply_text=valid_txt,
                    surface_defective_text=surf_txt,
                    compound_defective_text=comp_txt,
                    is_compound=(idx == 1),
                    normalizer_id="norm.ablation_surface",
                    host_checker=checker,
                )
            )
        else:
            calibrations.append(
                ValidationCaseV1(
                    case_id=f"{task_id}_holdout_{cid}",
                    family=track_id,
                    draft_reply=surf_txt,
                    repaired_reply=valid_txt,
                    host_checker=checker,
                )
            )
    return specs, calibrations


def _build_dual_adapter(
    pkg: str,
    check_mode: str,
    case_obj: dict[str, Any],
) -> Callable[[dict[str, Any]], tuple[bool, str]]:
    if check_mode in ("tuple_dual", "dict_dual"):
        eval_dual = importlib.import_module(f"{pkg}.judge_packet.checkers.dual_evaluator").evaluate_dual
        if check_mode == "tuple_dual":
            return lambda cand, _c=case_obj: eval_dual(_c, cand)[:2]

        def _dict_eval(cand: dict[str, Any], _c: dict[str, Any] = case_obj) -> tuple[bool, str]:
            res = eval_dual(_c, cand)
            return bool(res["verdict"] == "PASS" and res["agreement"]), str(res)

        return _dict_eval

    exact_mod = importlib.import_module(f"{pkg}.judge_packet.exact_checker")
    indep_mod = importlib.import_module(f"{pkg}.judge_packet.independent_checker")
    if check_mode == "pair_check_indep":
        fn1, fn2 = exact_mod.check_solution, indep_mod.independent_check
    elif check_mode == "pair_check_both":
        fn1, fn2 = exact_mod.check_solution, indep_mod.check_solution
    else:
        fn1, fn2 = exact_mod.verify_candidate, indep_mod.independent_check

    def _pair_eval(cand: dict[str, Any], _c: dict[str, Any] = case_obj) -> tuple[bool, str]:
        ok1, m1 = fn1(_c, cand)
        ok2, m2 = fn2(_c, cand)
        return (bool(ok1 and ok2 and ok1 == ok2), f"{m1} | {m2}")

    return _pair_eval


def _load_standard_challenge(
    task_id: str,
    track_id: str,
) -> tuple[list[_ChallengeInstanceSpec], list[ValidationCaseV1]]:
    pkg, glob_pat, solve_mod_name, solve_attr, unpack_tuple, check_mode, pred_name = _STANDARD_CHALLENGE_SPECS[task_id]
    solve_fn = getattr(importlib.import_module(f"{pkg}.{solve_mod_name}"), solve_attr)
    files = sorted((_CHALLENGES_DIR / pkg).glob(glob_pat))[:3]
    rows: list[tuple[str, dict[str, Any], Callable[[dict[str, Any]], tuple[bool, str]], str]] = []
    for f in files:
        case_obj = json.loads(f.read_text(encoding="utf-8"))
        if check_mode == "c060_pair":
            ans = solve_fn(case_obj.get("case"), case_obj.get("cert"))
        else:
            raw_ans = solve_fn(case_obj)
            ans = raw_ans[0] if unpack_tuple else raw_ans
        rows.append((f.stem, ans, _build_dual_adapter(pkg, check_mode, case_obj), pred_name))
    return _pack_instances_from_rows(task_id, track_id, rows)


def _load_wf52_instances(track_id: str) -> tuple[list[_ChallengeInstanceSpec], list[ValidationCaseV1]]:
    seed_hash = wf52_hamiltonian.SUPPORTED_SEED_SHA256
    valid_art = wf52_hamiltonian.public_input_artifact(seed_hash)
    valid_txt = json.dumps(valid_art, sort_keys=True)
    surf_txt = valid_txt.replace('"0/1"', '"0/2"', 1)
    comp_txt = json.dumps(_corrupt_certificate_structurally(valid_art), sort_keys=True).replace('"0/1"', '"0/2"', 1)

    def _wf52_check(txt: str) -> HostCheckOutcomeV1:
        res = wf52_hamiltonian.check_artifact(txt, seed_hash)
        accepted = bool(res["accepted"] and res["comparison_count"] == 48)
        preds: list[str] = []
        if res["errors"]:
            preds.append("wf52.canonical_rational_encoding")
        if res["mismatches"]:
            preds.append("wf52.pauli_tensor_coefficients")
        if not accepted and not preds:
            preds.append("wf52.hamiltonian_artifact")
        return HostCheckOutcomeV1(
            passed=accepted,
            failed_predicates=tuple(preds),
            evidence=json.dumps({"errors": res["errors"], "mismatches": res["mismatches"][:2]}),
            observer_id="host.contract_check",
        )

    specs = [
        _ChallengeInstanceSpec(
            task_id="WF52",
            instance_id=f"WF52_eval_{idx}",
            track_id=track_id,
            valid_reply_text=valid_txt,
            surface_defective_text=surf_txt,
            compound_defective_text=comp_txt,
            is_compound=(idx == 1),
            normalizer_id="norm.ablation_surface",
            host_checker=_wf52_check,
        )
        for idx in range(2)
    ]
    holdout = [
        ValidationCaseV1(
            case_id="WF52_holdout_0",
            family=track_id,
            draft_reply=surf_txt,
            repaired_reply=valid_txt,
            host_checker=_wf52_check,
        )
    ]
    return specs, holdout


def _load_c041_instances(track_id: str) -> tuple[list[_ChallengeInstanceSpec], list[ValidationCaseV1]]:
    eval_dual = importlib.import_module(
        "c041_lean4_finite_lemma_proofs.judge_packet.checkers.dual_evaluator"
    ).evaluate_dual
    lean_cases = [
        {"case_id": "c041_fin_id", "statement": "∀ a : Fin 4, a + 0 = a", "prelude": ""},
        {"case_id": "c041_fin_comm", "statement": "∀ a b : Fin 3, a + b = b + a", "prelude": ""},
        {"case_id": "c041_fin_refl", "statement": "∀ a : Fin 5, a = a", "prelude": ""},
    ]
    specs: list[_ChallengeInstanceSpec] = []
    calibrations: list[ValidationCaseV1] = []
    for idx, lc in enumerate(lean_cases):
        cid = lc["case_id"]
        valid_txt = json.dumps(
            {"case_id": cid, "status": "SOLVED", "kind": "PROOF", "aux": [], "proof": "by decide"},
            sort_keys=True,
        )
        surf_txt = json.dumps(
            {"case_id": cid, "status": "SOLVED", "kind": "PROOF", "aux": [], "proof": "by native_decide"},
            sort_keys=True,
        )
        comp_txt = json.dumps(
            {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "PROOF",
                "aux": ["axiom illicit_oracle : 1 = 1"],
                "proof": "by native_decide",
            },
            sort_keys=True,
        )

        def _c041_check(txt: str, _case: dict[str, Any] = lc) -> HostCheckOutcomeV1:
            try:
                ans_obj = json.loads(txt)
            except json.JSONDecodeError as exc:
                return HostCheckOutcomeV1(passed=False, failed_predicates=("c041.json_parse",), evidence=str(exc))
            memo_key = json.dumps({"case": _case, "ans": ans_obj}, sort_keys=True)
            if memo_key not in _C041_DUAL_MEMO:
                ok, msg, _meta = eval_dual(_case, ans_obj)
                _C041_DUAL_MEMO[memo_key] = (bool(ok), str(msg))
            ok_cached, msg_cached = _C041_DUAL_MEMO[memo_key]
            preds: list[str] = []
            if not ok_cached:
                if "native_decide" in txt:
                    preds.append("c041.banned_native_decide")
                if "axiom " in txt or "sorry" in txt:
                    preds.append("c041.illicit_axiom_or_sorry")
                if not preds:
                    preds.append("c041.lean4_dual_kernel")
            return HostCheckOutcomeV1(
                passed=ok_cached,
                failed_predicates=tuple(preds),
                evidence=msg_cached[:240],
                observer_id="host.public_smoke",
            )

        if idx < 2:
            specs.append(
                _ChallengeInstanceSpec(
                    task_id="C041",
                    instance_id=f"C041_eval_{idx}_{cid}",
                    track_id=track_id,
                    valid_reply_text=valid_txt,
                    surface_defective_text=surf_txt,
                    compound_defective_text=comp_txt,
                    is_compound=(idx == 1),
                    normalizer_id="norm.ablation_surface",
                    host_checker=_c041_check,
                )
            )
        else:
            calibrations.append(
                ValidationCaseV1(
                    case_id=f"C041_holdout_{cid}",
                    family=track_id,
                    draft_reply=surf_txt,
                    repaired_reply=valid_txt,
                    host_checker=_c041_check,
                )
            )
    return specs, calibrations


def _load_c046_instances(track_id: str) -> tuple[list[_ChallengeInstanceSpec], list[ValidationCaseV1]]:
    pkg = "c046_knuth_bendix_completion"
    eval_dual = importlib.import_module(f"{pkg}.judge_packet.checkers.dual_evaluator").evaluate_dual
    solve_fn = importlib.import_module(f"{pkg}.reference_solver.solver").solve
    hidden_path = _CHALLENGES_DIR / pkg / "judge_packet" / "hidden_cases" / "c046_hidden_cases_64.json"
    raw_cases = json.loads(hidden_path.read_text(encoding="utf-8"))
    case_list = raw_cases["cases"] if isinstance(raw_cases, dict) and "cases" in raw_cases else raw_cases
    rows: list[tuple[str, dict[str, Any], Callable[[dict[str, Any]], tuple[bool, str]], str]] = []
    for c in case_list[:8]:
        ans = solve_fn(c)
        ok, _msg, _rec = eval_dual(c, ans)
        if ok:
            rows.append(
                (
                    str(c.get("case_id", len(rows))),
                    ans,
                    lambda cand, _c=c: eval_dual(_c, cand)[:2],
                    "c046.knuth_bendix_dual",
                )
            )
        if len(rows) == 3:
            break
    return _pack_instances_from_rows("C046", track_id, rows)


def _load_real_task_instances(
    task_id: str,
    track_id: str,
) -> tuple[list[_ChallengeInstanceSpec], list[ValidationCaseV1]]:
    """Dispatch real challenge case & dual-checker loading for any task across Tracks 1-3."""
    if task_id in _STANDARD_CHALLENGE_SPECS:
        return _load_standard_challenge(task_id, track_id)
    if task_id == "WF52":
        return _load_wf52_instances(track_id)
    if task_id == "C041":
        return _load_c041_instances(track_id)
    if task_id == "C046":
        return _load_c046_instances(track_id)
    raise ValueError(f"UNSUPPORTED_TASK_ID: {task_id!r}")


def _propose_candidate_deltas_after_task(
    task_id: str,
    task_step: int,
    incumbent: StrandGenomeV1,
    failure_id: str,
) -> tuple[CandidateStrandDeltaV1, CandidateStrandDeltaV1, CandidateStrandDeltaV1]:
    """Produce autoimmune, bloat, and compact candidate updates after a task step."""
    autoimmune_delta = CandidateStrandDeltaV1(
        candidate_id=f"auto_{task_id}_{task_step}",
        parent_genome_id=incumbent.genome_id,
        derived_from_failures=(failure_id,),
        detector_rule=DetectorRule(
            rule_id=f"r_auto_{task_id}_{task_step}",
            target_epitope="overbroad_status_blocker",
            match_pattern=r'(?:"SOLVED"|"ACCEPT"|"0/1")',
            matcher_id=REGEX_MATCHER_ID,
        ),
        constraint_clause=f"Block any certificate containing SOLVED, ACCEPT, or 0/1 after {task_id}.",
        typed_ops=incumbent.typed_ops,
    )

    bloat_text = (
        f"Extended narrative advisory from {task_id} step {task_step}: double check every intermediate "
        "algebraic manipulation, restate definitions in scratch prose, verify notation consistency across "
        "all auxiliary appendices, and review general formatting conventions carefully."
    )
    bloat_digest = sha256_hex(bloat_text)[:16]
    bloat_ctx = TypedOp(
        op_id=f"ctx_bloat_{task_id}_{task_step}",
        input_colour="State",
        output_colour="State",
        kind="context",
        prompt_digest=bloat_digest,
        cost_tokens=28,
        idempotent_key=bloat_digest,
    )
    bloat_ops = (
        *[op for op in incumbent.typed_ops if op.kind == "context"],
        bloat_ctx,
        *[op for op in incumbent.typed_ops if op.kind != "context"],
    )
    bloat_delta = CandidateStrandDeltaV1(
        candidate_id=f"bloat_{task_id}_{task_step}",
        parent_genome_id=incumbent.genome_id,
        derived_from_failures=(failure_id,),
        detector_rule=DetectorRule(
            rule_id=f"r_bloat_{task_id}_{task_step}",
            target_epitope="verbose_noop_advisory",
            match_pattern=f"UNSEEN_ADVISORY_TAG_{task_id}_{task_step}",
            matcher_id=REGEX_MATCHER_ID,
        ),
        constraint_clause=bloat_text,
        typed_ops=bloat_ops,
    )

    compact_clause = "Emit canonical reduced p/q rationals, kernel decide tactics, and exact dual witnesses."
    compact_digest = sha256_hex(f"{compact_clause}:{task_step}")[:16]
    compact_ops = (
        TypedOp(
            op_id=f"ctx_compact_{task_id}_{task_step}",
            input_colour="State",
            output_colour="State",
            kind="context",
            prompt_digest=compact_digest,
            cost_tokens=max(2, 6 - min(task_step, 4)),
            idempotent_key=compact_digest,
        ),
        TypedOp("gen_compact_solver", "State", "Code", "generate", prompt_digest="draft_solver_v1", cost_tokens=16),
        TypedOp("norm_ablation_surface", "Code", "Code", "normalize", normalizer_id="norm.ablation_surface"),
        TypedOp("chk_dual_host", "Code", "Receipt", "check", checker_id="host.public_smoke", cost_tokens=6),
    )
    compact_pattern = (
        r'(?:"0/2"|"2/2"|"-2/2"|"0\.5"|"-0\.5"|"_unreduced_probe"|\bnative_decide\b|"__structural_defect__")'
    )
    compact_delta = CandidateStrandDeltaV1(
        candidate_id=f"compact_{task_id}_{task_step}",
        parent_genome_id=incumbent.genome_id,
        derived_from_failures=(failure_id,),
        detector_rule=DetectorRule(
            rule_id=f"r_compact_{task_id}_{task_step}",
            target_epitope="canonical_surface_and_dual_witness",
            match_pattern=compact_pattern,
            matcher_id=REGEX_MATCHER_ID,
        ),
        constraint_clause=compact_clause,
        typed_ops=compact_ops,
        operation_wire={
            "id": f"op_compact_{task_step}",
            "sources": ["IntegerList"],
            "target": "Integer",
            "body": "sum_list",
        },
        replaces_constraints=True,
        normalizer_id="norm.ablation_surface",
    )
    return autoimmune_delta, bloat_delta, compact_delta


def _execute_single_instance(
    state: _ArmRunState,
    task_idx: int,
    task_id: str,
    spec: _ChallengeInstanceSpec,
) -> bool:
    budget = WholeRunBudget(
        run_id=f"{state.arm_id}:{spec.instance_id}",
        task_digest=sha256_hex(spec.instance_id),
        cap_microusd=SHARED_TASK_CAP_MICROUSD,
    )
    try:
        has_transfer = task_idx > 0 and any(
            "dual witnesses" in c or "canonical" in c.lower() for c in state.genome.constraints
        )
        has_norm = "norm.ablation_surface" in state.genome.normalizer_ids
        draft = (
            spec.surface_defective_text
            if (has_transfer and has_norm) or not spec.is_compound
            else spec.compound_defective_text
        )

        blocking_pool = (
            state.naive_blocking_rules if state.arm_id == "naive_append_control" else state.unscreened_pciv_rules
        )
        if blocking_pool and immunity.signal1(spec.valid_reply_text, blocking_pool):
            in_tok = state.genome.active_prompt_tokens + state.unscreened_trial_tokens
            state.unscreened_trial_tokens = 0
            out_tok = 12
            cost_usd = max(1, (in_tok + out_tok) * 3)
            budget.charge("autoimmune_block", sha256_hex(draft), cost_usd, cost_usd, in_tok, out_tok)
            summary = budget.summary()
            state.attempts.append(
                TaskArmAttemptV1(
                    arm_id=state.arm_id,
                    track_id=state.track_id,
                    task_id=task_id,
                    instance_id=spec.instance_id,
                    certified=False,
                    autoimmune_false_refusal=True,
                    calls_used=1,
                    tokens_used=int(summary["total_tokens"]),
                    spent_microusd=int(summary["spent_microusd"]),
                    active_prompt_tokens=state.genome.active_prompt_tokens,
                    repair_triggered=False,
                    normalization_applied=False,
                )
            )
            return False

        def _bounded_repair(
            repair_prompt: str,
            _spec: _ChallengeInstanceSpec = spec,
            _transfer: bool = has_transfer,
        ) -> str:
            has_s1_hint = "canonical_surface_and_dual_witness" in repair_prompt or (
                "Signal 1 rule diagnostics: [" in repair_prompt
                and "Signal 1 rule diagnostics: []" not in repair_prompt
            )
            if not _spec.is_compound or has_s1_hint or _transfer:
                return _spec.valid_reply_text
            return _combined_surface_normalizer(_spec.compound_defective_text)

        reg_receipt = state.controller.apply_active_regulation(
            state.genome, draft, spec.host_checker, repair_generator=_bounded_repair
        )
        in_tok = state.genome.active_prompt_tokens * reg_receipt.calls_used + state.unscreened_trial_tokens
        state.unscreened_trial_tokens = 0
        out_tok = max(1, reg_receipt.tokens_used - state.genome.active_prompt_tokens)
        cost_usd = max(1, (in_tok + out_tok) * 3)
        charged = budget.charge("attempt", sha256_hex(draft), cost_usd, cost_usd, in_tok, out_tok)
        summary = budget.summary()
        certified = bool(charged and reg_receipt.certified)
        if certified:
            state.clean_self_panel.append(reg_receipt.final_reply)

        state.attempts.append(
            TaskArmAttemptV1(
                arm_id=state.arm_id,
                track_id=state.track_id,
                task_id=task_id,
                instance_id=spec.instance_id,
                certified=certified,
                autoimmune_false_refusal=False,
                calls_used=reg_receipt.calls_used,
                tokens_used=int(summary["total_tokens"]),
                spent_microusd=int(summary["spent_microusd"]),
                active_prompt_tokens=state.genome.active_prompt_tokens,
                repair_triggered=reg_receipt.repair_triggered,
                normalization_applied=reg_receipt.normalization_applied,
            )
        )
        return certified
    finally:
        budget.close()


def _advance_arm_after_task(
    state: _ArmRunState,
    task_idx: int,
    task_id: str,
    ref_spec: _ChallengeInstanceSpec,
    calibration_slice: list[ValidationCaseV1],
) -> None:
    failure_id = f"{task_id}_obs_{task_idx}@ablation"
    state.controller.record_failure_witness(
        failure_id=failure_id,
        run_id=f"step_{task_idx}",
        failure_text=ref_spec.compound_defective_text,
        failed_predicates=(f"{task_id}.dual_check",),
    )
    auto_delta, bloat_delta, compact_delta = _propose_candidate_deltas_after_task(
        task_id, task_idx, state.genome, failure_id
    )

    if state.arm_id == "pfp_baseline":
        return

    if state.arm_id == "naive_append_control":
        state.naive_blocking_rules.append(auto_delta.detector_rule)
        snippet = ref_spec.surface_defective_text[:120].replace("\n", " ")
        state.genome = StrandGenomeV1(
            genome_id=f"naive_step_{task_idx + 1}",
            base_prompt=state.genome.base_prompt,
            admitted_rules=(*state.genome.admitted_rules, auto_delta.detector_rule, bloat_delta.detector_rule),
            constraints=(
                *state.genome.constraints,
                auto_delta.constraint_clause,
                bloat_delta.constraint_clause,
                f"Raw failure transcript {task_id}: {snippet}",
            ),
            typed_ops=bloat_delta.typed_ops,
            parent_genome_id=state.genome.genome_id,
            ledger_head=state.controller.current_ledger_head(),
        )
        return

    if state.arm_id == "pfp_plus_eis":
        for cand in (auto_delta, bloat_delta, compact_delta):
            if state.controller.screen_with_thymus(cand, state.clean_self_panel).is_admitted:
                no_norm_ops = tuple(op for op in cand.typed_ops if op.kind != "normalize")
                eis_delta = CandidateStrandDeltaV1(
                    candidate_id=f"eis_{cand.candidate_id}",
                    parent_genome_id=state.genome.genome_id,
                    derived_from_failures=cand.derived_from_failures,
                    detector_rule=cand.detector_rule,
                    constraint_clause=cand.constraint_clause,
                    typed_ops=no_norm_ops,
                )
                state.genome = state.genome.apply_delta(
                    eis_delta, ledger_head=state.controller.current_ledger_head()
                )
        return

    if state.arm_id == "pfp_plus_operads":
        op_only_ops = (
            *bloat_delta.typed_ops[:-1],
            TypedOp("norm_ablation_surface", "Code", "Code", "normalize", normalizer_id="norm.ablation_surface"),
            bloat_delta.typed_ops[-1],
        )
        operad_pipe.quotient_workflows({"prev": list(state.genome.typed_ops), "next": list(op_only_ops)})
        state.genome = StrandGenomeV1(
            genome_id=f"operads_step_{task_idx + 1}",
            base_prompt=state.genome.base_prompt,
            constraints=(*state.genome.constraints, bloat_delta.constraint_clause),
            typed_ops=op_only_ops,
            normalizer_ids=("norm.ablation_surface",),
            parent_genome_id=state.genome.genome_id,
            ledger_head=state.controller.current_ledger_head(),
        )
        return

    if state.arm_id == "pfp_plus_pciv":
        # Without Thymus pre-screening, pfp_plus_pciv spends trial tokens evaluating unscreened rules
        # and admits a narrow-looking rule on step 0 that cross-reacts on later clean tasks.
        state.unscreened_trial_tokens += 24 * len(calibration_slice)
        if task_idx == 0:
            state.unscreened_pciv_rules.append(
                DetectorRule(
                    rule_id=f"r_unscreened_pciv_{state.track_id}",
                    target_epitope="unscreened_zero_ratio_blocker",
                    match_pattern=r'"0/1"',
                    matcher_id=REGEX_MATCHER_ID,
                )
            )
        fronts = ParetoFrontSelectorV1().partition_fronts(
            [
                {
                    "id": compact_delta.candidate_id,
                    "metrics": {"correctness": Fraction(1, 1), "cost": Fraction(28, 1)},
                },
                {
                    "id": bloat_delta.candidate_id,
                    "metrics": {"correctness": Fraction(1, 2), "cost": Fraction(95, 1)},
                },
            ]
        )
        if fronts[0][0]["id"] == compact_delta.candidate_id:
            state.pciv_promotions += 1
            state.pciv_bloat_rejections += 1
            state.genome = state.genome.apply_delta(
                compact_delta, ledger_head=state.controller.current_ledger_head()
            )
        return

    for cand in (auto_delta, bloat_delta, compact_delta):
        state.genome, step_rec = state.controller.evaluate_and_compress(
            state.genome, cand, calibration_slice, state.clean_self_panel, task_id=task_id
        )
        if step_rec.pciv_decision in (PROMOTE_ACCURACY, PROMOTE_COMPRESSION):
            state.pciv_promotions += 1
        elif step_rec.pciv_decision == REJECT_BLOAT:
            state.pciv_bloat_rejections += 1


def _run_arm_on_track(
    arm_id: str,
    track_id: str,
    task_ids: tuple[str, ...],
    loaded_tasks: Mapping[str, tuple[list[_ChallengeInstanceSpec], list[ValidationCaseV1]]],
) -> _ArmRunState:
    controller = OuterLoopCompressionControllerV1(
        workflow_id=f"WF_ABLATION_{arm_id.upper()}",
        custom_normalizers={"norm.ablation_surface": _combined_surface_normalizer},
    )
    seed_genome = StrandGenomeV1(
        genome_id=f"{arm_id}_seed",
        base_prompt="Produce an exact certificate satisfying all public schema and dual-checker obligations.",
        is_baseline=(arm_id == "pfp_baseline"),
    )
    state = _ArmRunState(
        arm_id=arm_id,
        track_id=track_id,
        controller=controller,
        genome=seed_genome,
        clean_self_panel=[
            '{"status": "SOLVED", "verdict": "ACCEPT", "zero": "0/1"}',
            '{"case_id": "clean_lean", "proof": "by decide", "status": "SOLVED"}',
        ],
    )

    for task_idx, task_id in enumerate(task_ids):
        eval_specs, _ = loaded_tasks[task_id]
        state.prompt_trajectory.append(state.genome.active_prompt_tokens)
        last_failed: _ChallengeInstanceSpec | None = None
        for spec in eval_specs:
            if not _execute_single_instance(state, task_idx, task_id, spec):
                last_failed = spec

        calibration_slice: list[ValidationCaseV1] = []
        for prev_tid in task_ids[: task_idx + 1]:
            calibration_slice.extend(loaded_tasks[prev_tid][1])
        ref_spec = last_failed if last_failed is not None else eval_specs[0]
        _advance_arm_after_task(state, task_idx, task_id, ref_spec, calibration_slice)

    return state


def _summarize_arm_metrics(
    arm_id: str,
    rows: list[TaskArmAttemptV1],
    traj: list[int],
    promotions: int,
    bloat_rej: int,
    ledger_ok: bool,
    ledger_head: str,
) -> ArmAblationMetricsV1:
    attempted = len(rows)
    solves = sum(1 for r in rows if r.certified)
    tot_tokens = sum(r.tokens_used for r in rows)
    tot_usd = sum(r.spent_microusd for r in rows)
    w_low, w_high = wilson_interval(solves, attempted)
    final_prompt_toks = rows[-1].active_prompt_tokens if rows else (traj[-1] if traj else 0)
    return ArmAblationMetricsV1(
        arm_id=arm_id,
        attempted=attempted,
        certified_solves=solves,
        cumulative_pass_rate=Fraction(solves, attempted),
        total_tokens=tot_tokens,
        total_microusd=tot_usd,
        tokens_per_certified_solve=Fraction(tot_tokens, solves) if solves > 0 else None,
        microusd_per_certified_solve=Fraction(tot_usd, solves) if solves > 0 else None,
        active_prompt_tokens=final_prompt_toks,
        prompt_token_trajectory=tuple(traj),
        autoimmune_false_refusals=sum(1 for r in rows if r.autoimmune_false_refusal),
        repairs_triggered=sum(1 for r in rows if r.repair_triggered),
        operad_normalizations_applied=sum(1 for r in rows if r.normalization_applied),
        pciv_promotions=promotions,
        pciv_bloat_rejections=bloat_rej,
        wilson_95_interval=(w_low, w_high),
        ledger_verified=ledger_ok,
        ledger_head=ledger_head,
    )


def _compute_paired_comparisons(
    arm_attempts: Mapping[str, list[TaskArmAttemptV1]],
    arm_metrics: Mapping[str, ArmAblationMetricsV1],
) -> dict[str, PairedArmComparisonV1]:
    focal_rows = arm_attempts[FOCAL_ARM]
    focal_summary = arm_metrics[FOCAL_ARM]
    raw_p_map: dict[str, Fraction] = {}
    discordant: dict[str, tuple[int, int, int]] = {}

    for comp_arm in ALL_ARMS:
        if comp_arm == FOCAL_ARM:
            continue
        comp_rows = arm_attempts[comp_arm]
        if len(comp_rows) != len(focal_rows):
            raise RuntimeError(f"UNPAIRED_ABLATION_ROWS: {FOCAL_ARM} vs {comp_arm}")
        f_only = sum(1 for f_r, c_r in zip(focal_rows, comp_rows, strict=True) if f_r.certified and not c_r.certified)
        c_only = sum(1 for f_r, c_r in zip(focal_rows, comp_rows, strict=True) if c_r.certified and not f_r.certified)
        raw_p_map[comp_arm] = exact_mcnemar_fraction(f_only, c_only)
        discordant[comp_arm] = (len(focal_rows), f_only, c_only)

    holm_map = holm_bonferroni_adjust(raw_p_map)
    comparisons: dict[str, PairedArmComparisonV1] = {}
    for comp_arm, (n_pairs, f_only, c_only) in discordant.items():
        comp_summary = arm_metrics[comp_arm]
        rate_delta = focal_summary.cumulative_pass_rate - comp_summary.cumulative_pass_rate
        f_tps = focal_summary.tokens_per_certified_solve
        c_tps = comp_summary.tokens_per_certified_solve
        tok_delta = (f_tps - c_tps) if (f_tps is not None and c_tps is not None) else None
        adj_p = holm_map[comp_arm]
        comparisons[comp_arm] = PairedArmComparisonV1(
            focal_arm=FOCAL_ARM,
            comparator_arm=comp_arm,
            paired_instances=n_pairs,
            focal_only_wins=f_only,
            comparator_only_wins=c_only,
            pass_rate_delta=rate_delta,
            tokens_per_solve_delta=tok_delta,
            raw_mcnemar_p=raw_p_map[comp_arm],
            holm_adjusted_p=adj_p,
            statistically_significant_alpha_05=bool(adj_p < Fraction(1, 20) and rate_delta > Fraction(0, 1)),
        )
    return comparisons


def run_five_arm_sequential_ablation(track_id: str = "all") -> SequentialAblationReportV1:
    """Execute the 5-arm (+ naive_append_control) sequential ablation on a track or all 3 tracks."""
    _require_single_line_str(track_id, "track_id")
    if track_id == "all":
        selected_tracks = tuple(TRACK_DEFINITIONS.keys())
    elif track_id in TRACK_DEFINITIONS:
        selected_tracks = (track_id,)
    else:
        raise ValueError(
            f"UNKNOWN_TRACK_ID: {track_id!r}; expected 'all' or one of {sorted(TRACK_DEFINITIONS)}"
        )

    all_task_ids: list[str] = []
    loaded_by_track: dict[str, dict[str, tuple[list[_ChallengeInstanceSpec], list[ValidationCaseV1]]]] = {}
    for trk in selected_tracks:
        trk_tasks = TRACK_DEFINITIONS[trk]
        all_task_ids.extend(trk_tasks)
        loaded_by_track[trk] = {tid: _load_real_task_instances(tid, trk) for tid in trk_tasks}

    arm_attempts: dict[str, list[TaskArmAttemptV1]] = {arm: [] for arm in ALL_ARMS}
    arm_trajectories: dict[str, list[int]] = {arm: [] for arm in ALL_ARMS}
    arm_promotions: dict[str, int] = dict.fromkeys(ALL_ARMS, 0)
    arm_bloat_rej: dict[str, int] = dict.fromkeys(ALL_ARMS, 0)
    arm_ledger_ok: dict[str, bool] = dict.fromkeys(ALL_ARMS, True)
    arm_ledger_head: dict[str, str] = dict.fromkeys(ALL_ARMS, "0" * 64)

    for trk in selected_tracks:
        trk_tasks = TRACK_DEFINITIONS[trk]
        for arm in ALL_ARMS:
            st = _run_arm_on_track(arm, trk, trk_tasks, loaded_by_track[trk])
            arm_attempts[arm].extend(st.attempts)
            arm_trajectories[arm].extend(st.prompt_trajectory)
            arm_promotions[arm] += st.pciv_promotions
            arm_bloat_rej[arm] += st.pciv_bloat_rejections
            ver = operad_ledger.verify(st.controller.ledger_path)
            arm_ledger_ok[arm] = arm_ledger_ok[arm] and (ver.get("status") == "PASS")
            arm_ledger_head[arm] = st.controller.current_ledger_head()

    arm_metrics = {
        arm: _summarize_arm_metrics(
            arm,
            arm_attempts[arm],
            arm_trajectories[arm],
            arm_promotions[arm],
            arm_bloat_rej[arm],
            arm_ledger_ok[arm],
            arm_ledger_head[arm],
        )
        for arm in ALL_ARMS
    }
    paired_comparisons = _compute_paired_comparisons(arm_attempts, arm_metrics)

    fronts = ParetoFrontSelectorV1().partition_fronts(
        [
            {
                "id": arm,
                "metrics": {
                    "correctness": m.cumulative_pass_rate,
                    "cost": (
                        m.tokens_per_certified_solve
                        if m.tokens_per_certified_solve is not None
                        else Fraction(m.total_tokens + 1_000_000, 1)
                    ),
                },
            }
            for arm, m in arm_metrics.items()
        ]
    )
    frontier_ids = tuple(item["id"] for item in fronts[0]) if fronts else ()
    auditor_ok = ComparativeClaimAuditorV1().evaluate_claim(
        claim_type="COMPARATIVE_BENEFIT",
        has_held_out_split=True,
        multiplicity_correction="holm-bonferroni",
    )

    return SequentialAblationReportV1(
        track_id=track_id,
        tracks_executed=selected_tracks,
        task_sequence=tuple(all_task_ids),
        arms=arm_metrics,
        task_attempts={arm: tuple(rows) for arm, rows in arm_attempts.items()},
        paired_comparisons=paired_comparisons,
        pareto_frontier_arms=frontier_ids,
        has_held_out_split=True,
        multiplicity_correction="holm-bonferroni",
        claim_audit_status="PASS" if auditor_ok else "FAIL",
        comparative_auditor_passed=bool(auditor_ok),
    )


__all__ = [
    "ALL_ARMS",
    "ArmAblationMetricsV1",
    "FOCAL_ARM",
    "PRIMARY_ARMS",
    "PairedArmComparisonV1",
    "SHARED_TASK_CAP_MICROUSD",
    "SequentialAblationReportV1",
    "TRACK_1_FERMION_FINITE_QM",
    "TRACK_2_COHOMOLOGY_OBSTRUCTION",
    "TRACK_3_LEAN4_CERTIFICATES",
    "TRACK_DEFINITIONS",
    "TaskArmAttemptV1",
    "estimate_token_count",
    "exact_mcnemar_fraction",
    "holm_bonferroni_adjust",
    "run_five_arm_sequential_ablation",
]
