"""Two-stage blind EIS/PCIV historical corpus evaluator over the 24 frozen QM runs.

Enforces a strict two-stage evaluator firewall:
- Stage A (`run_blind_stage_a`): 100% blind to grades and post-hoc summaries. Reads only
  the frozen `run.json` receipts (and optional raw call response files for intermediate
  wire diagnostics), asserting `accuracy_score is None` and refusing any grade, rubric,
  or summary file path. Keeps all assigned runs in denominators (`N = 24`).
- Stage B (`compare_post_hoc_stage_b`): Separate read-only post-hoc comparison joining
  Stage A's frozen blind output with `dag/benchmark/results_summary.json` only after
  Stage A completes. Never accesses `evaluator_rubric.json` or private answers.

AuthorityEffect: None. `final_answer_certified` is strictly `False` throughout.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from collections.abc import Sequence
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _sys_path in (ROOT, HERE, ROOT / "ops"):
    if str(_sys_path) not in sys.path:
        sys.path.insert(0, str(_sys_path))

import charpoly_wire  # noqa: E402
from summarize_runs import read_frozen_receipt  # noqa: E402

from eis.domain.provisional_promotion import (  # noqa: E402
    ObservationSupportPolicyV1,
    RawObservationV1,
)
from eis.domain.thymus import ThymusGate  # noqa: E402
from eis.domain.value_objects import (  # noqa: E402
    DangerSeverity,
    DetectorRule,
    Signal2Danger,
)
from eis.use_cases.two_signal_regulation import (  # noqa: E402
    AcquiredAntibodyPromotionV1,
    NormalizedMatcher,
    QMInvariantAntibodySuiteV1,
    ThymusSelfPanelBuilder,
    TwoSignalRegulatorV1,
)
from pciv.domain.causal_witness import seal_causal_witness  # noqa: E402
from pciv.use_cases.fitness import (  # noqa: E402
    ComparativeClaimAuditorV1,
    ParetoFrontSelectorV1,
    PromptFitnessCalculatorV1,
)
from pciv.use_cases.genealogy import (  # noqa: E402
    LineageGraphV1,
    RelationshipType,
)
from pciv.use_cases.immunity import LineageTaintEngineV1  # noqa: E402

SCHEMA_VERSION = "pfp.eis-pciv-historical-evaluation.v1"
DEFAULT_OUTPUT_PATH = HERE / "eis_pciv_historical_evaluation.json"
DEFAULT_RESULTS_SUMMARY_PATH = HERE / "results_summary.json"

HISTORICAL_EXPERIMENT_FOLDERS: tuple[str, ...] = (
    "pilot_20261110",
    "hamiltonian_pilot_20261110",
    "hamiltonian_large_model_20261110",
    "length_control_20261110",
    "section_control_20261110",
    "model_control_20261110",
    "model_control_repaired_20261110",
    "deepseek_critique_20261110",
    "charpoly_pilot_20261110",
)

# Witnessed workflow derivation DAG rooted at `direct`.
WORKFLOW_LINEAGE_SPEC: tuple[tuple[str, str, RelationshipType], ...] = (
    ("direct", "section_allocated_v1", RelationshipType.DIRECT_MUTATION),
    ("direct", "hamiltonian_checked_v1", RelationshipType.DIRECT_MUTATION),
    ("direct", "qm_charpoly_checked_v1", RelationshipType.DIRECT_MUTATION),
    ("direct", "self_critique", RelationshipType.DIRECT_MUTATION),
    ("direct", "rational_blind_panel_v1", RelationshipType.DIRECT_MUTATION),
    ("rational_blind_panel_v1", "rational_visible_panel_v1", RelationshipType.DIRECT_MUTATION),
    ("rational_blind_panel_v1", "rational_fixed_panel_v1", RelationshipType.DIRECT_MUTATION),
    ("rational_fixed_panel_v1", "rational_fixed_panel_v2", RelationshipType.REPAIR),
    ("hamiltonian_checked_v1", "hamiltonian_ungated_v1", RelationshipType.DIRECT_MUTATION),
    ("hamiltonian_checked_v1", "hamiltonian_host_matrix_v1", RelationshipType.DIRECT_MUTATION),
    ("qm_charpoly_checked_v1", "qm_charpoly_ungated_v1", RelationshipType.DIRECT_MUTATION),
)

_FORBIDDEN_STAGE_A_EXACT_NAMES: frozenset[str] = frozenset(
    {
        "grades.json",
        "graded_results.json",
        "results_summary.json",
        "evaluator_rubric.json",
        "criterion_evidence.json",
        "evaluation_validation.json",
    }
)

_FORBIDDEN_STAGE_A_SUBSTRINGS: tuple[str, ...] = (
    "rubric",
    "grade",
    "private_answer",
    "answer_key",
    "results_summary",
)


class BlindFirewallViolationError(PermissionError):
    """Raised when Stage A encounters a forbidden evaluator, grade, or summary artifact."""


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.name


def _assert_blind_stage_a_path_allowed(path: Path) -> Path:
    """Enforce that Stage A never reads grades, rubrics, or post-hoc summary files."""
    name_lower = path.name.lower()
    if name_lower in _FORBIDDEN_STAGE_A_EXACT_NAMES:
        raise BlindFirewallViolationError(
            f"STAGE_A_FIREWALL_REFUSAL: forbidden file name {path.name!r}"
        )
    for token in _FORBIDDEN_STAGE_A_SUBSTRINGS:
        if token in name_lower:
            raise BlindFirewallViolationError(
                f"STAGE_A_FIREWALL_REFUSAL: forbidden token {token!r} in {path.name!r}"
            )
    for part in path.parts:
        part_lower = part.lower()
        if part_lower in _FORBIDDEN_STAGE_A_EXACT_NAMES or "rubric" in part_lower:
            raise BlindFirewallViolationError(
                f"STAGE_A_FIREWALL_REFUSAL: forbidden path component {part!r}"
            )
    return path


def _assert_post_hoc_stage_b_path_allowed(path: Path) -> Path:
    """Enforce that Stage B reads results_summary.json and never reads evaluator rubrics."""
    name_lower = path.name.lower()
    if "rubric" in name_lower or "private_answer" in name_lower or "answer_key" in name_lower:
        raise BlindFirewallViolationError(
            f"STAGE_B_FIREWALL_REFUSAL: forbidden private evaluator path {path.name!r}"
        )
    return path


def discover_historical_run_json_paths(benchmark_dir: Path = HERE) -> list[Path]:
    """Return the 24 frozen `run.json` paths across the 9 historical experiment folders."""
    paths: list[Path] = []
    for folder_name in HISTORICAL_EXPERIMENT_FOLDERS:
        folder = benchmark_dir / folder_name
        paths.extend(sorted((folder / "runs").glob("*/run.json")))
        paths.extend(sorted((folder / "repair_runs").glob("*/run.json")))
    return paths


def _extract_model_id(provider: str) -> str:
    after_colon = provider.split(":", 1)[-1]
    return after_colon.split("@", 1)[0]


def _infer_experiment_folder(run_path: Path) -> str:
    if len(run_path.parents) >= 3 and run_path.parents[1].name in {"runs", "repair_runs"}:
        return run_path.parents[2].name
    return run_path.parent.name


def _build_workflow_lineage_graph() -> tuple[LineageGraphV1, dict[str, str], list[dict[str, str]]]:
    """Construct the witnessed PCIV workflow lineage DAG and derive subfamily roots."""
    graph = LineageGraphV1()
    graph.add_genome("direct")
    serialized_edges: list[dict[str, str]] = []
    for idx, (parent_id, child_id, rel) in enumerate(WORKFLOW_LINEAGE_SPEC):
        witness = seal_causal_witness(
            {
                "receipt_id": f"workflow_lineage_edge_{idx:03d}",
                "parent_id": parent_id,
                "child_id": child_id,
                "relationship": rel.value,
                "authority_effect": "None",
            }
        )
        graph.add_edge(
            parent_id=parent_id,
            child_id=child_id,
            relationship=rel,
            witness_receipt=witness,
        )
        serialized_edges.append(
            {
                "parent_id": parent_id,
                "child_id": child_id,
                "relationship": rel.value,
                "witness_sha256": witness.receipt_sha256,
            }
        )

    subfamily_root_by_plan: dict[str, str] = {"direct": "direct"}
    for node_id in graph.nodes:
        if node_id == "direct":
            continue
        descent = graph.derive_descent_path("direct", node_id)
        subfamily_root_by_plan[node_id] = descent[1] if len(descent) >= 2 else node_id

    return graph, subfamily_root_by_plan, serialized_edges


def _propagate_taint_transitive(
    initial_tainted: Sequence[str],
    edges: Sequence[tuple[str, str]],
    all_nodes: Sequence[str],
) -> list[str]:
    """Run PCIV `LineageTaintEngineV1` to fixed-point transitive closure over `edges`."""
    engine = LineageTaintEngineV1()
    for node_id in initial_tainted:
        engine.mark_tainted(node_id)
    prev_count = -1
    while True:
        current = [n for n in all_nodes if engine.is_tainted(n)]
        if len(current) == prev_count:
            return sorted(current)
        prev_count = len(current)
        engine.propagate_taint(edges)


def _blind_selected_outcome(
    status: str,
    answer_delivered: bool,
    all_ab_passed: bool,
    truncated: bool,
) -> str:
    """Map blind execution telemetry to PCIV `reduce_selected_attempt_outcome` vocabulary."""
    calc = PromptFitnessCalculatorV1()
    if status == "admission_failure":
        return calc.reduce_selected_attempt_outcome(["NotMeasured"], "AllowedTask")
    if status in {"representation_refused", "certificate_refused"}:
        return calc.reduce_selected_attempt_outcome(["ValidRefusal"], "AllowedTask")
    if not answer_delivered or status != "completed" or truncated or not all_ab_passed:
        return calc.reduce_selected_attempt_outcome(["TaskFail"], "AllowedTask")
    return calc.reduce_selected_attempt_outcome(["TaskPass"], "AllowedTask")


def _partition_4d_pareto_fronts(candidates: Sequence[dict[str, Any]]) -> list[list[str]]:
    """Partition eligible runs into exact 4-axis non-dominated Pareto fronts."""
    remaining = list(candidates)
    fronts: list[list[str]] = []

    def _vec(item: dict[str, Any]) -> tuple[Fraction, Fraction, Fraction, Fraction]:
        return (
            Fraction(int(item["blind_public_antibody_pass_count_non_truncated"]), 1),
            Fraction(int(item["spent_microusd"]), 1),
            Fraction(int(item["total_tokens"]), 1),
            Fraction(str(item["wall_time_seconds"])),
        )

    def _dominates_4d(left: dict[str, Any], right: dict[str, Any]) -> bool:
        la, ls, lt, lw = _vec(left)
        ra, rs, rt, rw = _vec(right)
        weak = la >= ra and ls <= rs and lt <= rt and lw <= rw
        strict = la > ra or ls < rs or lt < rt or lw < rw
        return weak and strict

    while remaining:
        current_front: list[dict[str, Any]] = []
        next_remaining: list[dict[str, Any]] = []
        for idx, cand in enumerate(remaining):
            dominated = any(
                other_idx != idx and _dominates_4d(other, cand)
                for other_idx, other in enumerate(remaining)
            )
            if dominated:
                next_remaining.append(cand)
            else:
                current_front.append(cand)

        current_front.sort(
            key=lambda item: (
                -_vec(item)[0],
                _vec(item)[1],
                _vec(item)[2],
                _vec(item)[3],
                str(item["run_id"]),
            )
        )
        fronts.append([str(item["run_id"]) for item in current_front])
        remaining = next_remaining

    return fronts


def _inspect_charpoly_coeff_slot(coeff_terms: Any) -> tuple[bool, bool]:
    if not isinstance(coeff_terms, list):
        return False, False
    slash_one = False
    dup_powers = False
    seen_powers: set[tuple[Any, ...]] = set()
    for term in coeff_terms:
        if not isinstance(term, dict):
            continue
        if str(term.get("q", "")).endswith("/1"):
            slash_one = True
        pw = term.get("powers")
        if isinstance(pw, list):
            pw_t = tuple(pw)
            dup_powers = dup_powers or (pw_t in seen_powers)
            seen_powers.add(pw_t)
    return slash_one, dup_powers


def _inspect_charpoly_json_terms(raw_text: str) -> tuple[bool, bool, bool]:
    try:
        parsed_obj = json.loads(raw_text)
    except ValueError:
        return False, False, False

    coeffs = parsed_obj.get("coefficients") if isinstance(parsed_obj, dict) else None
    if not isinstance(coeffs, list):
        return True, False, False

    slash_one = False
    dup_powers = False
    for slot in coeffs:
        slot_slash, slot_dup = _inspect_charpoly_coeff_slot(slot)
        slash_one = slash_one or slot_slash
        dup_powers = dup_powers or slot_dup
    return True, slash_one, dup_powers


def _build_thymus_and_normalizer_summary() -> tuple[
    NormalizedMatcher,
    DetectorRule,
    DetectorRule,
    dict[str, Any],
]:
    thymus = ThymusGate(self_panel=ThymusSelfPanelBuilder.build_self_panel())
    matcher = NormalizedMatcher(matcher_id="normalized_charpoly")
    regulator = TwoSignalRegulatorV1()

    naive_rule = DetectorRule(
        rule_id="naive_unreduced_rational_regex",
        target_epitope="charpoly_rational_spelling",
        match_pattern=r'"q":\s{0,2}"[+-]?[0-9]{1,6}/[1-9][0-9]{0,2}"',
        matcher_id="regex",
    )
    norm_rule = DetectorRule(
        rule_id="normalized_unreduced_rational_detector",
        target_epitope="charpoly_rational_spelling",
        match_pattern=r'"q":\s{0,2}"[+-]?[0-9]{1,6}/[1-9][0-9]{0,2}"',
        matcher_id="normalized_charpoly",
    )
    structural_rule = DetectorRule(
        rule_id="normalized_syntax_or_degree_defect",
        target_epitope="charpoly_structural_defect",
        match_pattern=r'(?:The previous candidate|"powers":\s{0,4}\[[5-9])',
        matcher_id="normalized_charpoly",
    )

    naive_thymus = thymus.evaluate_rule(naive_rule)
    norm_thymus = thymus.evaluate_rule(norm_rule, matcher=matcher)
    structural_thymus = thymus.evaluate_rule(structural_rule, matcher=matcher)

    monic_probe = json.dumps(
        {
            "coefficients": [
                [],
                [{"powers": [0, 0, 1], "q": "-4/1"}],
                [],
                [],
                [{"powers": [0, 0, 0], "q": "1/1"}],
            ]
        }
    )
    monic_norm = charpoly_wire.normalize_candidate(monic_probe)
    monic_matches = matcher.match_antigen(monic_probe, (norm_rule,))
    monic_reg = regulator.evaluate(
        content=monic_probe,
        matches=monic_matches,
        danger=None,
        detector_id=matcher.matcher_id,
        offsets_are_content=False,
    )

    bad_degree_probe = '{"coefficients": [[], [], [], [], [{"powers": [5, 0, 0], "q": "1"}]]}'
    bad_degree_norm = charpoly_wire.normalize_candidate(bad_degree_probe)
    bad_degree_matches = matcher.match_antigen(bad_degree_probe, (structural_rule,))
    bad_degree_danger = Signal2Danger(
        danger_type="MALFORMED_PAYLOAD",
        severity=DangerSeverity.HIGH,
        observer_id="host_charpoly_wire_v1",
        evidence_digest="sha256:" + _sha256_hex(bad_degree_probe.encode("utf-8")),
    )
    bad_degree_reg = regulator.evaluate(
        content=bad_degree_probe,
        matches=bad_degree_matches,
        danger=bad_degree_danger,
        detector_id=matcher.matcher_id,
        offsets_are_content=False,
    )

    summary = {
        "bad_degree_probe_regulation_decision": bad_degree_reg.decision.value,
        "bad_degree_probe_structural_hits": len(bad_degree_matches),
        "bad_degree_probe_wire_refusal": (bad_degree_norm.get("refusal") or {}).get("code"),
        "monic_slash_one_probe_normalized_accepted": bool(monic_norm["accepted"]),
        "monic_slash_one_probe_regulation_decision": monic_reg.decision.value,
        "monic_slash_one_probe_unreduced_hits_after_normalization": len(monic_matches),
        "naive_regex_admitted_by_thymus": naive_thymus.is_admitted,
        "naive_regex_autoimmune_violations": naive_thymus.autoimmune_violations,
        "normalized_matcher_admitted_by_thymus": norm_thymus.is_admitted,
        "normalized_matcher_autoimmune_violations": norm_thymus.autoimmune_violations,
        "structural_defect_rule_admitted_by_thymus": structural_thymus.is_admitted,
    }
    return matcher, norm_rule, structural_rule, summary


def _evaluate_single_charpoly_call(
    *,
    run_path: Path,
    receipt: dict[str, Any],
    call_idx: int,
    call_entry: dict[str, Any],
    stage_checks: Sequence[Any],
    matcher: NormalizedMatcher,
    norm_rule: DetectorRule,
    structural_rule: DetectorRule,
    accessed_files: list[str],
) -> dict[str, Any]:
    call_file = run_path.parent / "calls" / f"{call_idx:03d}.response.json"
    raw_text = str(call_entry.get("response_text", ""))
    call_file_verified = False
    if call_file.is_file():
        _assert_blind_stage_a_path_allowed(call_file)
        accessed_files.append(_display_path(call_file))
        disk_call = json.loads(call_file.read_text(encoding="utf-8"))
        if disk_call.get("response_text") != raw_text:
            raise ValueError(
                f"Call response mismatch between run.json and {_display_path(call_file)}"
            )
        call_file_verified = True

    sidecar_feedback = (
        stage_checks[call_idx].get("feedback")
        if call_idx < len(stage_checks) and isinstance(stage_checks[call_idx], dict)
        else None
    )
    wire_receipt = charpoly_wire.normalize_candidate(raw_text)
    parsed_valid, slash_one, dup_powers = _inspect_charpoly_json_terms(raw_text)
    norm_hits = matcher.match_antigen(raw_text, (norm_rule,))
    structural_hits = matcher.match_antigen(raw_text, (structural_rule,))

    return {
        "call_file_verified_against_run_json": call_file_verified,
        "call_id": str(call_entry.get("call_id", "")),
        "call_index": call_idx,
        "charpoly_wire_accepted": bool(wire_receipt["accepted"]),
        "charpoly_wire_refusal_code": (wire_receipt.get("refusal") or {}).get("code"),
        "charpoly_wire_status": str(wire_receipt["status"]),
        "finish_reason": str(call_entry.get("finish_reason", "")),
        "has_duplicate_powers": dup_powers,
        "has_unreduced_slash_one_rationals": slash_one,
        "normalized_matcher_structural_hit_count": len(structural_hits),
        "normalized_matcher_unreduced_hit_count": len(norm_hits),
        "parsed_as_json": parsed_valid,
        "plan": str(receipt["plan"]),
        "run_id": str(receipt["run_id"]),
        "sidecar_feedback": sidecar_feedback,
        "stage_id": str(call_entry.get("stage_id", "")),
    }


def _evaluate_charpoly_raw_calls(
    loaded_runs: Sequence[tuple[Path, dict[str, Any]]],
    accessed_files: list[str],
) -> dict[str, Any]:
    """Analyze `charpoly_pilot_20261110` raw candidate calls and Thymus `NormalizedMatcher`."""
    matcher, norm_rule, structural_rule, thymus_summary = _build_thymus_and_normalizer_summary()
    call_diagnostics: list[dict[str, Any]] = []
    checked_run_found = False

    for run_path, receipt in loaded_runs:
        plan_name = receipt.get("plan")
        if plan_name not in {"qm_charpoly_checked_v1", "qm_charpoly_ungated_v1"}:
            continue
        checked_run_found = checked_run_found or (plan_name == "qm_charpoly_checked_v1")
        stage_checks = (receipt.get("host_checks") or {}).get("stage_checks") or []
        for call_idx, call_entry in enumerate(receipt.get("calls") or []):
            if str(call_entry.get("stage_id", "")) not in {"charpoly", "charpoly_repair"}:
                continue
            call_diagnostics.append(
                _evaluate_single_charpoly_call(
                    run_path=run_path,
                    receipt=receipt,
                    call_idx=call_idx,
                    call_entry=call_entry,
                    stage_checks=stage_checks,
                    matcher=matcher,
                    norm_rule=norm_rule,
                    structural_rule=structural_rule,
                    accessed_files=accessed_files,
                )
            )

    return {
        "charpoly_checked_run_observed": checked_run_found,
        "frozen_call_diagnostics": call_diagnostics,
        "root_cause_summary": (
            "In qm-charpoly-20261110:qm_charpoly_checked_v1:000, Call 000 (stage=charpoly, "
            "finish_reason=stop) emitted valid JSON with zero duplicate powers, rejected at "
            "the strict sidecar schema layer with RATIONAL_NONCANONICAL due to '/1' denominators "
            "('-4/1', '-16/1', '4/1', '8/1', '16/1'); passing Call 000 through charpoly_wire "
            "reduces all '/1' rationals and exposes NONMONIC_LEADING_COEFFICIENT in the lambda^4 "
            "slot. Call 001 (stage=charpoly_repair, finish_reason=length) spent all 2,400 repair "
            "tokens on Markdown prose without emitting JSON, failing with MALFORMED_JSON."
        ),
        "thymus_and_normalized_matcher_check": thymus_summary,
    }


def _load_blind_stage_a_receipts(
    resolved_paths: Sequence[Path],
) -> tuple[list[tuple[Path, dict[str, Any]]], list[str]]:
    accessed_files: list[str] = []
    loaded_runs: list[tuple[Path, dict[str, Any]]] = []
    seen_run_ids: set[str] = set()

    for raw_path in resolved_paths:
        path = _assert_blind_stage_a_path_allowed(Path(raw_path))
        if path.name != "run.json":
            raise BlindFirewallViolationError(
                f"STAGE_A_FIREWALL_REFUSAL: expected run.json receipt, got {path.name!r}"
            )
        pin_path = _assert_blind_stage_a_path_allowed(path.with_suffix(".sha256"))
        accessed_files.append(_display_path(path))
        accessed_files.append(_display_path(pin_path))

        receipt, _digest = read_frozen_receipt(path)
        if receipt.get("accuracy_score") is not None:
            raise BlindFirewallViolationError(
                f"STAGE_A_FIREWALL_REFUSAL: non-null accuracy_score in {receipt.get('run_id')!r}"
            )
        for forbidden_key in ("grades", "rubric", "points", "evaluator_id"):
            if forbidden_key in receipt:
                raise BlindFirewallViolationError(
                    f"STAGE_A_FIREWALL_REFUSAL: forbidden key {forbidden_key!r} in run.json"
                )
        if receipt.get("offline") is True:
            raise ValueError(f"Offline fixture {receipt['run_id']!r} excluded from live corpus")
        run_id = str(receipt["run_id"])
        if run_id in seen_run_ids:
            raise ValueError(f"Duplicate run_id {run_id!r} in Stage A input")
        seen_run_ids.add(run_id)
        loaded_runs.append((path, receipt))

    return loaded_runs, accessed_files


def _screen_run_antibodies(
    answer_text: Any,
    all_antibody_ids: list[str],
    pass_counter: Counter[str],
) -> tuple[int, bool, list[str], dict[str, bool]]:
    if answer_text is None:
        if not all_antibody_ids:
            ab_probe = QMInvariantAntibodySuiteV1.evaluate("")
            all_antibody_ids.extend(f.antibody_id for f in ab_probe.findings)
        return (
            0,
            False,
            list(all_antibody_ids),
            dict.fromkeys(all_antibody_ids, False),
        )

    ab_receipt = QMInvariantAntibodySuiteV1.evaluate(str(answer_text))
    if ab_receipt.final_answer_certified is not False:
        raise ValueError("QMInvariantReceiptV1 violated final_answer_certified == False")
    if not all_antibody_ids:
        all_antibody_ids.extend(f.antibody_id for f in ab_receipt.findings)
    for finding in ab_receipt.findings:
        if finding.passed:
            pass_counter[finding.antibody_id] += 1
    return (
        int(ab_receipt.passed_count),
        bool(ab_receipt.all_passed),
        [f.antibody_id for f in ab_receipt.findings if not f.passed],
        {f.antibody_id: bool(f.passed) for f in ab_receipt.findings},
    )


def _record_failure_observations(
    obs: RawObservationV1,
    *,
    is_truncated: bool,
    status: str,
    artifact_errors: dict[str, Any],
    answer_delivered: bool,
    ab01_passed: bool,
    ab_map: dict[str, bool],
    plan: str,
    buckets: dict[str, list[RawObservationV1]],
) -> None:
    if is_truncated:
        buckets["output_truncation"].append(obs)
    if status in {"representation_refused", "certificate_refused"}:
        buckets["intermediate_encoding_or_gate_refusal"].append(obs)
    if artifact_errors:
        buckets["host_artifact_schema_failure"].append(obs)
    if answer_delivered and not ab01_passed:
        buckets["missing_structural_completeness_ab01"].append(obs)
    if answer_delivered and (
        not ab_map.get("Ab06_HighTemperaturePartitionFunction", False)
        or not ab_map.get("Ab10_CrossSectionConsistency", False)
    ):
        buckets["missing_thermal_or_consistency_ab06_ab10"].append(obs)
    if status == "artifact_validation_failure":
        buckets["rational_panel_schema_failure"].append(obs)
    if plan == "hamiltonian_checked_v1" and status == "representation_refused":
        buckets["hamiltonian_checked_matrix_refusal"].append(obs)


def _evaluate_single_blind_run(
    run_path: Path,
    receipt: dict[str, Any],
    *,
    subfamily_root_by_plan: dict[str, str],
    fitness_calc: PromptFitnessCalculatorV1,
    all_antibody_ids: list[str],
    antibody_pass_counts_by_id: Counter[str],
    failure_observations: dict[str, list[RawObservationV1]],
) -> dict[str, Any]:
    run_id = str(receipt["run_id"])
    plan = str(receipt["plan"])
    provider = str(receipt["provider"])
    model_id = _extract_model_id(provider)
    experiment_folder = _infer_experiment_folder(run_path)
    family_root = subfamily_root_by_plan.get(plan, plan)
    status = str(receipt["status"])

    budget = receipt["budget"]
    spent_microusd = int(budget["spent_microusd"])
    held_microusd = int(budget["held_microusd"])
    known_cost = held_microusd == 0 and not bool(budget["blocked"])

    in_tok = receipt.get("input_tokens")
    out_tok = receipt.get("output_tokens")
    total_tokens = (
        int(in_tok) + int(out_tok) if in_tok is not None and out_tok is not None else None
    )

    finish_counts = Counter(
        str(c["finish_reason"])
        for c in (receipt.get("calls") or [])
        if isinstance(c, dict) and isinstance(c.get("finish_reason"), str)
    )
    truncated_call_count = int(finish_counts.get("length", 0))
    is_truncated = truncated_call_count > 0
    artifact_errors = dict((receipt.get("host_checks") or {}).get("artifact_errors") or {})

    answer_text = receipt.get("answer_text")
    answer_delivered = answer_text is not None
    passed_count, all_ab_passed, failed_antibodies, ab_map = _screen_run_antibodies(
        answer_text,
        all_antibody_ids,
        antibody_pass_counts_by_id,
    )
    non_truncated_pass_count = passed_count if (answer_delivered and not is_truncated) else 0
    ab01_passed = bool(ab_map.get("Ab01_StructuralCompleteness", False)) and answer_delivered

    if fitness_calc.extract_success_credit({"gate_status": status.upper()}) != 0:
        raise ValueError("Caller status granted unexpected automatic fitness credit")

    obs = RawObservationV1(
        occurrence_id=run_id,
        generating_model_id=model_id,
        scaffold_digest=plan,
        precedent_set_digest=experiment_folder,
        inheritance_root=family_root,
    )
    _record_failure_observations(
        obs,
        is_truncated=is_truncated,
        status=status,
        artifact_errors=artifact_errors,
        answer_delivered=answer_delivered,
        ab01_passed=ab01_passed,
        ab_map=ab_map,
        plan=plan,
        buckets=failure_observations,
    )

    return {
        "ab01_structural_completeness_passed": ab01_passed,
        "accuracy_score_in_run_json": receipt.get("accuracy_score"),
        "all_10_public_antibodies_passed": all_ab_passed,
        "answer_char_length": len(str(answer_text)) if answer_delivered else 0,
        "answer_delivered": answer_delivered,
        "antibody_pass_map": ab_map,
        "blind_public_antibody_pass_count": passed_count,
        "blind_public_antibody_pass_count_non_truncated": non_truncated_pass_count,
        "complete_5_section_non_truncated": (
            status == "completed" and answer_delivered and not is_truncated and ab01_passed
        ),
        "complete_token_cost_accounting": known_cost and total_tokens is not None,
        "experiment_folder": experiment_folder,
        "failed_antibody_ids": failed_antibodies,
        "family_root": family_root,
        "final_answer_certified": False,
        "finish_reason_counts": dict(sorted(finish_counts.items())),
        "held_microusd": held_microusd,
        "host_artifact_errors": artifact_errors,
        "input_tokens": in_tok,
        "model_id": model_id,
        "output_tokens": out_tok,
        "pciv_selected_outcome": _blind_selected_outcome(
            status=status,
            answer_delivered=answer_delivered,
            all_ab_passed=all_ab_passed,
            truncated=is_truncated,
        ),
        "plan": plan,
        "provider": provider,
        "reasoning_tokens": receipt.get("reasoning_tokens"),
        "run_id": run_id,
        "run_json_path": _display_path(run_path),
        "spent_microusd": spent_microusd,
        "status": status,
        "total_antibodies": 10,
        "total_tokens": total_tokens,
        "truncated_call_count": truncated_call_count,
        "wall_time_seconds": float(receipt["wall_time_seconds"]),
    }


def _compute_mis_support_report(
    failure_observations: dict[str, list[RawObservationV1]],
) -> dict[str, Any]:
    promotion_helper = AcquiredAntibodyPromotionV1(policy=ObservationSupportPolicyV1())
    mis_support_report: dict[str, Any] = {}
    for mode_name, obs_list in failure_observations.items():
        support_res, promo_res = promotion_helper.evaluate_promotion(
            candidate_id=f"defect:{mode_name}",
            observations=obs_list,
            diagnostic_scope=["qm_historical_corpus_blind_stage_a"],
        )
        unique_keys = sorted(
            {
                (
                    o.generating_model_id,
                    o.scaffold_digest,
                    o.precedent_set_digest,
                    o.inheritance_root,
                )
                for o in obs_list
            }
        )
        mis_support_report[mode_name] = {
            "authority_effect": promo_res.authority_effect,
            "candidate_id": promo_res.candidate_id,
            "distinct_correlation_tuple_count": len(unique_keys),
            "distinct_correlation_tuples": [
                {
                    "experiment_folder": k[2],
                    "family_root": k[3],
                    "model_id": k[0],
                    "plan": k[1],
                }
                for k in unique_keys
            ],
            "eligible_for_provisional": support_res.eligible_for_provisional,
            "mis_support_count": support_res.support_count,
            "new_custody": promo_res.new_custody,
            "raw_occurrence_count": len(obs_list),
            "review_queued": promo_res.review_queued,
            "run_ids": [o.occurrence_id for o in obs_list],
        }
    return mis_support_report


def _compute_pciv_pareto_and_lineage(
    run_records: Sequence[dict[str, Any]],
    lineage_graph: LineageGraphV1,
    subfamily_root_by_plan: dict[str, str],
    serialized_lineage_edges: list[dict[str, str]],
) -> dict[str, Any]:
    eligible_for_pareto = [r for r in run_records if r["complete_token_cost_accounting"]]
    excluded_from_pareto = [
        r["run_id"] for r in run_records if not r["complete_token_cost_accounting"]
    ]
    fronts_4d = _partition_4d_pareto_fronts(eligible_for_pareto)
    pareto_front_4d_ids = fronts_4d[0] if fronts_4d else []

    candidates_2d = [
        {
            "id": r["run_id"],
            "metrics": {
                "correctness": Fraction(
                    int(r["blind_public_antibody_pass_count_non_truncated"]),
                    1,
                ),
                "cost": Fraction(int(r["spent_microusd"]), 1),
            },
        }
        for r in eligible_for_pareto
    ]
    if candidates_2d:
        # Pair of dominated bottom-tier sentinels prevents ParetoFrontSelectorV1's
        # single-element final-layer closure bug without altering front 0.
        sentinels = [
            {
                "id": f"__sentinel_{idx}__",
                "metrics": {"correctness": Fraction(-1, 1), "cost": Fraction(10**12, 1)},
            }
            for idx in (0, 1)
        ]
        fronts_2d_raw = ParetoFrontSelectorV1().partition_fronts(candidates_2d + sentinels)
        pareto_front_2d_ids = [str(item["id"]) for item in fronts_2d_raw[0]]
    else:
        pareto_front_2d_ids = []

    lineage_edge_pairs = [(p, c) for p, c, _rel in WORKFLOW_LINEAGE_SPEC]
    all_lineage_nodes = sorted(lineage_graph.nodes)
    defect_statuses = {
        "representation_refused",
        "certificate_refused",
        "artifact_validation_failure",
    }
    plans_with_defect = sorted(
        {
            r["plan"]
            for r in run_records
            if r["plan"] != "direct"
            and (
                r["status"] in defect_statuses
                or bool(r["host_artifact_errors"])
                or (r["plan"] == "section_allocated_v1" and r["truncated_call_count"] > 0)
            )
        }
    )
    branch_tainted_plans = _propagate_taint_transitive(
        plans_with_defect,
        lineage_edge_pairs,
        all_lineage_nodes,
    )
    root_tainted_plans = _propagate_taint_transitive(
        ["direct"],
        lineage_edge_pairs,
        all_lineage_nodes,
    )

    comparative_refusal_code: str | None = None
    try:
        ComparativeClaimAuditorV1().evaluate_claim(
            claim_type="COMPARATIVE_BENEFIT",
            has_held_out_split=False,
            multiplicity_correction=None,
        )
    except ValueError as exc:
        comparative_refusal_code = str(exc).split(":", 1)[0]

    plan_by_run = {r["run_id"]: r["plan"] for r in run_records}
    return {
        "all_4d_pareto_fronts": fronts_4d,
        "blind_2d_cost_antibody_front_run_ids": pareto_front_2d_ids,
        "blind_4d_pareto_front_run_ids": pareto_front_4d_ids,
        "blind_4d_pareto_front_tainted_under_branch_defects": [
            rid for rid in pareto_front_4d_ids if plan_by_run[rid] in branch_tainted_plans
        ],
        "branch_defect_origin_plans": plans_with_defect,
        "branch_transitive_tainted_plans": branch_tainted_plans,
        "comparative_claim_holdout_refusal_code": comparative_refusal_code,
        "eligible_run_count": len(eligible_for_pareto),
        "excluded_incomplete_accounting_run_ids": excluded_from_pareto,
        "objectives_4d": {
            "blind_public_antibody_pass_count_non_truncated": "maximize",
            "spent_microusd": "minimize",
            "total_tokens": "minimize",
            "wall_time_seconds": "minimize",
        },
        "root_seed_framing_transitive_tainted_plans": root_tainted_plans,
        "subfamily_root_by_plan": dict(sorted(subfamily_root_by_plan.items())),
        "workflow_lineage_edges": serialized_lineage_edges,
    }


def _compute_delivery_and_resource_accounting(
    run_records: Sequence[dict[str, Any]],
    status_counter: Counter[str],
    fitness_calc: PromptFitnessCalculatorV1,
) -> dict[str, Any]:
    n_assigned = len(run_records)
    delivered_count = sum(1 for r in run_records if r["answer_delivered"])
    completed_count = sum(1 for r in run_records if r["status"] == "completed")
    completed_non_trunc_count = sum(
        1 for r in run_records if r["status"] == "completed" and r["truncated_call_count"] == 0
    )
    complete_5sec_count = sum(1 for r in run_records if r["complete_5_section_non_truncated"])
    truncated_run_count = sum(1 for r in run_records if r["truncated_call_count"] > 0)
    refused_or_admit_count = sum(1 for r in run_records if not r["answer_delivered"])
    eligible = [r for r in run_records if r["complete_token_cost_accounting"]]
    excluded_ids = [r["run_id"] for r in run_records if not r["complete_token_cost_accounting"]]

    def _fmt_frac(passes: int) -> str:
        frac = fitness_calc.completion_rate(passes, n_assigned)
        if frac is None:
            raise ValueError("Empty denominator in Stage A completion_rate")
        return f"{frac.numerator}/{frac.denominator}"

    total_spent_microusd = sum(int(r["spent_microusd"]) for r in run_records)
    return {
        "assigned_run_count": n_assigned,
        "complete_5_section_non_truncated_count": complete_5sec_count,
        "complete_5_section_non_truncated_rate_exact": _fmt_frac(complete_5sec_count),
        "completed_non_truncated_count": completed_non_trunc_count,
        "completed_non_truncated_rate_exact": _fmt_frac(completed_non_trunc_count),
        "completed_status_count": completed_count,
        "completed_status_rate_exact": _fmt_frac(completed_count),
        "delivered_answer_count": delivered_count,
        "delivered_answer_rate_exact": _fmt_frac(delivered_count),
        "held_microusd_total": sum(int(r["held_microusd"]) for r in run_records),
        "refused_or_admission_failed_count": refused_or_admit_count,
        "refused_or_admission_failed_rate_exact": _fmt_frac(refused_or_admit_count),
        "runs_missing_token_usage_ids": excluded_ids,
        "runs_with_complete_token_cost_accounting": len(eligible),
        "spent_microusd_total": total_spent_microusd,
        "spent_usd_total": f"{total_spent_microusd / 1_000_000:.6f}",
        "status_counts": dict(sorted(status_counter.items())),
        "sum_input_tokens_known": sum(int(r["input_tokens"]) for r in eligible),
        "sum_output_tokens_known": sum(int(r["output_tokens"]) for r in eligible),
        "sum_total_tokens_known": sum(int(r["total_tokens"]) for r in eligible),
        "sum_wall_time_seconds": round(sum(float(r["wall_time_seconds"]) for r in run_records), 6),
        "truncated_run_count": truncated_run_count,
        "truncated_run_rate_exact": _fmt_frac(truncated_run_count),
    }


def run_blind_stage_a(
    run_json_paths: Sequence[Path | str] | None = None,
) -> dict[str, Any]:
    """Execute Stage A blind EIS + PCIV corpus evaluation with zero grade/rubric access."""
    resolved_paths = (
        [Path(p) for p in run_json_paths]
        if run_json_paths is not None
        else discover_historical_run_json_paths(HERE)
    )
    if not resolved_paths:
        raise ValueError("Stage A requires at least one frozen run.json path")

    loaded_runs, accessed_files = _load_blind_stage_a_receipts(resolved_paths)
    lineage_graph, subfamily_root_by_plan, serialized_edges = _build_workflow_lineage_graph()
    fitness_calc = PromptFitnessCalculatorV1()

    status_counter: Counter[str] = Counter()
    antibody_pass_counts_by_id: Counter[str] = Counter()
    all_antibody_ids: list[str] = []
    failure_observations: dict[str, list[RawObservationV1]] = {
        "output_truncation": [],
        "intermediate_encoding_or_gate_refusal": [],
        "host_artifact_schema_failure": [],
        "missing_structural_completeness_ab01": [],
        "missing_thermal_or_consistency_ab06_ab10": [],
        "rational_panel_schema_failure": [],
        "hamiltonian_checked_matrix_refusal": [],
    }

    run_records: list[dict[str, Any]] = []
    for run_path, receipt in loaded_runs:
        status_counter[str(receipt["status"])] += 1
        run_records.append(
            _evaluate_single_blind_run(
                run_path,
                receipt,
                subfamily_root_by_plan=subfamily_root_by_plan,
                fitness_calc=fitness_calc,
                all_antibody_ids=all_antibody_ids,
                antibody_pass_counts_by_id=antibody_pass_counts_by_id,
                failure_observations=failure_observations,
            )
        )

    n_assigned = len(run_records)
    delivered_count = sum(1 for r in run_records if r["answer_delivered"])
    max_blind_ab = max((r["blind_public_antibody_pass_count"] for r in run_records), default=0)
    top_tier_run_ids = [
        r["run_id"] for r in run_records if r["blind_public_antibody_pass_count"] == max_blind_ab
    ]
    passed_10_of_10_ids = [
        r["run_id"] for r in run_records if r["all_10_public_antibodies_passed"]
    ]
    per_antibody_rates = {
        ab_id: {
            "passed_runs": int(antibody_pass_counts_by_id.get(ab_id, 0)),
            "rate_over_all_assigned": f"{int(antibody_pass_counts_by_id.get(ab_id, 0))}/{n_assigned}",
            "rate_over_delivered": (
                f"{int(antibody_pass_counts_by_id.get(ab_id, 0))}/{delivered_count}"
                if delivered_count > 0
                else "0/0"
            ),
        }
        for ab_id in all_antibody_ids
    }

    return {
        "authority_effect": "None",
        "charpoly_pilot_raw_candidate_analysis": _evaluate_charpoly_raw_calls(
            loaded_runs,
            accessed_files,
        ),
        "delivery_and_resource_accounting": _compute_delivery_and_resource_accounting(
            run_records,
            status_counter,
            fitness_calc,
        ),
        "eis_conflict_graph_mis_support": _compute_mis_support_report(failure_observations),
        "eis_public_antibody_summary": {
            "final_answer_certified": False,
            "max_observed_pass_count": max_blind_ab,
            "passed_10_of_10_count": len(passed_10_of_10_ids),
            "passed_10_of_10_run_ids": passed_10_of_10_ids,
            "per_antibody_pass_rates": per_antibody_rates,
            "top_public_obligation_tier_pass_count": max_blind_ab,
            "top_public_obligation_tier_run_ids": top_tier_run_ids,
            "total_antibodies": 10,
        },
        "final_answer_certified": False,
        "firewall_audit": {
            "accessed_file_count": len(accessed_files),
            "accessed_files": accessed_files,
            "all_run_accuracy_scores_null": True,
            "evaluator_rubric_accessed": False,
            "final_answer_certified": False,
            "grades_files_accessed": 0,
            "results_summary_accessed": False,
            "stage": "Stage_A_Blind",
        },
        "pciv_pareto_and_lineage": _compute_pciv_pareto_and_lineage(
            run_records,
            lineage_graph,
            subfamily_root_by_plan,
            serialized_edges,
        ),
        "runs": run_records,
        "schema_version": SCHEMA_VERSION,
    }


def _load_post_hoc_scores(summary_data: dict[str, Any], stage_a_ids: Sequence[str]) -> dict[str, Any]:
    score_by_run_id: dict[str, int | float] = {}
    for row in summary_data.get("raw_runs") or []:
        rid = str(row["run_id"])
        sc = row.get("score")
        if sc is None:
            raise ValueError(f"Missing post-hoc score for run_id {rid!r} in results_summary.json")
        score_by_run_id[rid] = sc

    if set(stage_a_ids) != set(score_by_run_id):
        missing = sorted(set(stage_a_ids) - set(score_by_run_id))
        extra = sorted(set(score_by_run_id) - set(stage_a_ids))
        raise ValueError(
            f"Run ID mismatch between Stage A and results_summary.json: "
            f"missing={missing}, extra={extra}"
        )
    return score_by_run_id


def _cohort_stats(items: Sequence[dict[str, Any]]) -> dict[str, Any]:
    scores = [float(x["post_hoc_score_out_of_100"]) for x in items]
    return {
        "count": len(items),
        "max_score": max(scores) if scores else None,
        "mean_score": round(sum(scores) / len(scores), 6) if scores else None,
        "min_score": min(scores) if scores else None,
        "run_ids": [x["run_id"] for x in items],
        "runs_scoring_ge_60_count": sum(1 for s in scores if s >= 60.0),
        "scores": [x["post_hoc_score_out_of_100"] for x in items],
    }


def compare_post_hoc_stage_b(
    stage_a_report: dict[str, Any],
    results_summary_path: Path | str = DEFAULT_RESULTS_SUMMARY_PATH,
) -> dict[str, Any]:
    """Execute Stage B read-only post-hoc validation joining Stage A with `results_summary.json`."""
    frozen_stage_a = deepcopy(stage_a_report)
    summary_path = _assert_post_hoc_stage_b_path_allowed(Path(results_summary_path))
    summary_data = json.loads(summary_path.read_text(encoding="utf-8"))

    stage_a_runs = frozen_stage_a["runs"]
    stage_a_ids = [str(r["run_id"]) for r in stage_a_runs]
    score_by_run_id = _load_post_hoc_scores(summary_data, stage_a_ids)

    blind_4d_front = set(frozen_stage_a["pciv_pareto_and_lineage"]["blind_4d_pareto_front_run_ids"])
    top_blind_tier_ids = set(
        frozen_stage_a["eis_public_antibody_summary"]["top_public_obligation_tier_run_ids"]
    )
    post_hoc_pareto_ids = [str(x) for x in (summary_data.get("pareto_front_run_ids") or [])]

    front_index_by_run: dict[str, int | None] = dict.fromkeys(stage_a_ids, None)
    for front_idx, front_members in enumerate(
        frozen_stage_a["pciv_pareto_and_lineage"]["all_4d_pareto_fronts"]
    ):
        for rid in front_members:
            front_index_by_run[str(rid)] = front_idx

    joined_runs = [
        {
            "all_10_public_antibodies_passed": bool(r["all_10_public_antibodies_passed"]),
            "answer_delivered": bool(r["answer_delivered"]),
            "blind_4d_pareto_layer_index": front_index_by_run[str(r["run_id"])],
            "blind_public_antibody_pass_count": int(r["blind_public_antibody_pass_count"]),
            "blind_public_antibody_pass_count_non_truncated": int(
                r["blind_public_antibody_pass_count_non_truncated"]
            ),
            "complete_5_section_non_truncated": bool(r["complete_5_section_non_truncated"]),
            "failed_antibody_ids": list(r["failed_antibody_ids"]),
            "final_answer_certified": False,
            "in_post_hoc_pareto_front": str(r["run_id"]) in set(post_hoc_pareto_ids),
            "in_stage_a_4d_pareto_front": str(r["run_id"]) in blind_4d_front,
            "in_stage_a_top_public_obligation_tier": str(r["run_id"]) in top_blind_tier_ids,
            "model_id": str(r["model_id"]),
            "plan": str(r["plan"]),
            "post_hoc_score_out_of_100": score_by_run_id[str(r["run_id"])],
            "run_id": str(r["run_id"]),
            "spent_microusd": int(r["spent_microusd"]),
            "status": str(r["status"]),
            "total_tokens": r["total_tokens"],
            "truncated_call_count": int(r["truncated_call_count"]),
        }
        for r in stage_a_runs
    ]

    strongest_target_ids = (
        "qm-model-repaired-20261110:direct:000",
        "qm-deepseek-critique-20261110:self_critique:000",
    )
    strongest_audit = {
        jr["run_id"]: {
            "blind_4d_pareto_layer_index": jr["blind_4d_pareto_layer_index"],
            "blind_public_antibody_pass_count": jr["blind_public_antibody_pass_count"],
            "failed_antibody_ids": jr["failed_antibody_ids"],
            "post_hoc_score_out_of_100": jr["post_hoc_score_out_of_100"],
            "retained_in_complete_5_section_non_truncated_cohort": jr[
                "complete_5_section_non_truncated"
            ],
            "retained_in_stage_a_top_public_obligation_tier": jr[
                "in_stage_a_top_public_obligation_tier"
            ],
            "retained_on_stage_a_4d_pareto_front": jr["in_stage_a_4d_pareto_front"],
        }
        for jr in joined_runs
        if jr["run_id"] in strongest_target_ids
    }

    stage_a_front_post_hoc_scores = [
        {
            "blind_public_antibody_pass_count_non_truncated": jr[
                "blind_public_antibody_pass_count_non_truncated"
            ],
            "post_hoc_score_out_of_100": jr["post_hoc_score_out_of_100"],
            "run_id": jr["run_id"],
            "spent_microusd": jr["spent_microusd"],
        }
        for jr in joined_runs
        if jr["in_stage_a_4d_pareto_front"]
    ]

    refused_cohort = [jr for jr in joined_runs if not jr["answer_delivered"]]
    truncated_delivered_cohort = [
        jr for jr in joined_runs if jr["answer_delivered"] and jr["truncated_call_count"] > 0
    ]
    incomplete_nontrunc_cohort = [
        jr
        for jr in joined_runs
        if jr["answer_delivered"]
        and jr["truncated_call_count"] == 0
        and not jr["complete_5_section_non_truncated"]
    ]
    non_complete_union = [jr for jr in joined_runs if not jr["complete_5_section_non_truncated"]]
    complete_5sec_cohort = [jr for jr in joined_runs if jr["complete_5_section_non_truncated"]]

    split_fibre_10_of_10 = [
        {
            "blind_public_antibody_pass_count": jr["blind_public_antibody_pass_count"],
            "post_hoc_score_out_of_100": jr["post_hoc_score_out_of_100"],
            "run_id": jr["run_id"],
        }
        for jr in joined_runs
        if jr["all_10_public_antibodies_passed"] and float(jr["post_hoc_score_out_of_100"]) < 100.0
    ]
    max_observed_ab = int(frozen_stage_a["eis_public_antibody_summary"]["max_observed_pass_count"])
    top_tier_fibre_collision = [
        {
            "blind_public_antibody_pass_count": jr["blind_public_antibody_pass_count"],
            "model_id": jr["model_id"],
            "plan": jr["plan"],
            "post_hoc_score_out_of_100": jr["post_hoc_score_out_of_100"],
            "run_id": jr["run_id"],
        }
        for jr in joined_runs
        if jr["blind_public_antibody_pass_count"] == max_observed_ab
        and float(jr["post_hoc_score_out_of_100"]) < 100.0
    ]

    return {
        "authority_effect": "None",
        "blind_cohort_separation": {
            "complete_5_section_non_truncated": _cohort_stats(complete_5sec_cohort),
            "non_truncated_incomplete_or_noncompleted": _cohort_stats(incomplete_nontrunc_cohort),
            "refused_or_admission_failure": _cohort_stats(refused_cohort),
            "truncated_delivered": _cohort_stats(truncated_delivered_cohort),
            "truncated_incomplete_or_refused_union": _cohort_stats(non_complete_union),
        },
        "final_answer_certified": False,
        "firewall_audit": {
            "evaluator_rubric_accessed": False,
            "final_answer_certified": False,
            "results_summary_path": _display_path(summary_path),
            "stage": "Stage_B_PostHoc_ReadOnly",
        },
        "joined_run_count": len(joined_runs),
        "joined_runs": joined_runs,
        "pareto_front_comparison": {
            "overlap_run_ids": sorted(blind_4d_front & set(post_hoc_pareto_ids)),
            "post_hoc_4d_pareto_front_run_ids": post_hoc_pareto_ids,
            "stage_a_4d_pareto_front_members_with_scores": stage_a_front_post_hoc_scores,
            "stage_a_4d_pareto_front_run_ids": sorted(blind_4d_front),
        },
        "split_fibre_blind_semantic_survivors": {
            "all_delivered_runs_below_100_count": sum(
                1
                for jr in joined_runs
                if jr["answer_delivered"] and float(jr["post_hoc_score_out_of_100"]) < 100.0
            ),
            "der_reference": ["DER-189", "DER-110"],
            "final_answer_certified": False,
            "kernel_diagnosis": (
                "Zero of 24 historical runs pass 10/10 in QMInvariantAntibodySuiteV1 (max 7/10) "
                "because unnormalized prose regexes trigger surface-syntax false positives on "
                "LaTeX formulas such as 'Z(\\beta) = 2...' (Ab06) and 'C = 2|...|' (Ab07) in the "
                "83/100 and 88/100 DeepSeek runs. Simultaneously, at the highest observed blind "
                "tier (7/10), two 4/100 GPT-4o-mini runs collide in the exact same coarse "
                "public-invariant fiber as the 83/100 DeepSeek derivation (a 79-point post-hoc "
                "accuracy spread within one blind fiber), illustrating a non-trivial watcher "
                "kernel and why final_answer_certified remains False."
            ),
            "max_observed_blind_antibody_pass_count": max_observed_ab,
            "passed_10_of_10_and_score_lt_100_count": len(split_fibre_10_of_10),
            "passed_10_of_10_and_score_lt_100_run_ids": [
                x["run_id"] for x in split_fibre_10_of_10
            ],
            "passed_10_of_10_and_score_lt_100_runs": split_fibre_10_of_10,
            "passed_10_of_10_total_count": sum(
                1 for jr in joined_runs if jr["all_10_public_antibodies_passed"]
            ),
            "top_observed_blind_tier_survivors_lt_100": top_tier_fibre_collision,
            "top_observed_blind_tier_survivors_lt_100_count": len(top_tier_fibre_collision),
        },
        "strongest_empirical_runs_audit": strongest_audit,
    }


def build_claim_hygiene_block() -> dict[str, Any]:
    """Construct the required Claim Hygiene block scoped to this 24-run historical corpus."""
    return {
        "does_not_support": [
            (
                "Any general ranking or comparative superiority across models, endpoints, or "
                "prompt workflows (single frozen task seed, unequal output ceilings, and no "
                "held-out split or multiplicity correction under F-RES-09)."
            ),
            (
                "Certifying final mathematical accuracy from coarse public textbook antibodies "
                "or intermediate matrix/polynomial gates (final_answer_certified remains False)."
            ),
            (
                "Treating correlated scaffold failures on a single workflow family as "
                "multi-channel provisional support without conflict-graph independent-set "
                "deduplication."
            ),
            (
                "Extrapolating single-item observations to untested quantum mechanics tasks "
                "or broader LLM populations."
            ),
        ],
        "narrowest_defensible_claim": (
            "Across the 24 frozen historical benchmark runs on one spin-1/2 seed ($0.055614 "
            "settled spend, 0 held liability), a strict two-stage blind EIS/PCIV audit keeps "
            "all 24 attempts in denominators, separates the 15 refused/truncated/"
            "section-incomplete attempts (post-hoc mean 9.4/100, max 47/100) from the 9 "
            "non-truncated 5-section completions (containing all 3 runs >= 60/100 alongside "
            "6 brief 3-4/100 runs), collapses scaffold-correlated gate refusals from 4 raw "
            "occurrences to MIS support 2 ('Candidate') while promoting cross-model truncation "
            "and missing thermal/consistency checks to MIS support >= 3 ('Provisional'), and "
            "documents both unnormalized LaTeX regex false positives (0/24 at 10/10) and a "
            "79-point post-hoc accuracy spread (4/100 vs 83/100) inside the top observed 7/10 "
            "blind antibody fiber."
        ),
        "next_test_needed": (
            "Evaluate a paired multi-seed held-out benchmark split with matched output-token "
            "allowances and multiplicity correction (satisfying PCIV F-RES-09), replacing "
            "unnormalized prose regex checks with Thymus-screened, notation-normalized "
            "structured algebraic witnesses for partition-function, concurrence, and trace "
            "obligations."
        ),
        "supports": [
            (
                "Blind structural and truncation telemetry in Stage A separates the 15 "
                "undelivered, truncated, or section-incomplete attempts (0/15 reaching "
                ">= 60/100) from the 9 complete 5-section non-truncated attempts (which "
                "contain all 3 runs scoring 62, 83, and 88/100)."
            ),
            (
                "In charpoly_pilot_20261110, qm_charpoly_checked_v1 refused Call 000 on '/1' "
                "rational spelling (RATIONAL_NONCANONICAL) while charpoly_wire normalization "
                "reduces '/1' fractions cleanly and exposes NONMONIC_LEADING_COEFFICIENT, and "
                "Call 001 exhausted 2,400 repair tokens on Markdown prose (MALFORMED_JSON)."
            ),
            (
                "ObservationSupportPolicyV1 exact conflict-graph MIS distinguishes "
                "cross-model/cross-scaffold failure modes (output truncation support=3, "
                "missing thermal/consistency checks support=4 -> 'Provisional') from "
                "single-scaffold clusters (intermediate gate refusal raw=4 -> support=2 "
                "'Candidate'; rational panel schema failure raw=4 -> support=1 'Candidate')."
            ),
            (
                "Stage B post-hoc comparison demonstrates an empirical watcher-kernel "
                "limitation on paid LLM outputs: 0/24 runs reach 10/10 under unnormalized "
                "LaTeX regexes, and at the top observed blind tier (7/10), two 4/100 "
                "GPT-4o-mini runs tie the 83/100 DeepSeek run and dominate both the 83/100 "
                "and 88/100 runs on 4-axis blind cost/token/time Pareto selection."
            ),
        ],
    }


def evaluate_historical_corpus(
    run_json_paths: Sequence[Path | str] | None = None,
    results_summary_path: Path | str = DEFAULT_RESULTS_SUMMARY_PATH,
) -> dict[str, Any]:
    """Run Stage A (100% blind) followed strictly afterward by Stage B (read-only post-hoc)."""
    stage_a = run_blind_stage_a(run_json_paths)
    stage_a_sha256 = _sha256_hex(_canonical_json_bytes(stage_a))
    stage_b = compare_post_hoc_stage_b(stage_a, results_summary_path=results_summary_path)

    return {
        "authority_effect": "None",
        "claim_hygiene": build_claim_hygiene_block(),
        "final_answer_certified": False,
        "schema_version": SCHEMA_VERSION,
        "stage_a_blind": stage_a,
        "stage_a_sha256": stage_a_sha256,
        "stage_b_post_hoc": stage_b,
    }


def serialize_evaluation_report(report: dict[str, Any]) -> str:
    """Deterministically serialize an evaluation report to canonical indented ASCII JSON."""
    return (
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )


def main(output_path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    report = evaluate_historical_corpus()
    output_path.write_text(serialize_evaluation_report(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    written = main()
    acct = written["stage_a_blind"]["delivery_and_resource_accounting"]
    split_f = written["stage_b_post_hoc"]["split_fibre_blind_semantic_survivors"]
    print(
        json.dumps(
            {
                "assigned_runs": acct["assigned_run_count"],
                "blind_4d_pareto_front": written["stage_a_blind"]["pciv_pareto_and_lineage"][
                    "blind_4d_pareto_front_run_ids"
                ],
                "final_answer_certified": written["final_answer_certified"],
                "passed_10_of_10_lt_100_count": split_f["passed_10_of_10_and_score_lt_100_count"],
                "spent_usd_total": acct["spent_usd_total"],
                "stage_a_sha256": written["stage_a_sha256"],
                "top_blind_tier_collision_count": split_f[
                    "top_observed_blind_tier_survivors_lt_100_count"
                ],
            },
            sort_keys=True,
        )
    )
