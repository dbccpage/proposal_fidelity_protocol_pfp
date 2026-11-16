"""Comprehensive behavioral & statistical test suite for PFP v1.0rc M1.1.

AuthorityEffect: None.

Tests:
1. ``pfp_core.outer_loop_v1rc``: causal 5-stage outer loop, Thymus central tolerance
   (0 false refusals), Operad trace quotienting, SPLIT_OVERLAP fence, PCIV strict
   Pareto accuracy & compression gates, active regulation without authority escalation,
   and native Rust ``pfp_operad`` hash-chained ledger verification.
2. ``pfp_core.funnel_v1rc``: 1,024-candidate Tier 1 workflow permutation & trace quotient,
   Tier 2 ``Opus 5.5 xhigh`` hidden-probe / gauge / exclusion falsification + Thymus + PCIV
   conservation law, and Tier 3 ``Fable 5.2`` derivation packet routing.
3. ``pfp_core.sequential_ablation_v1rc``: 5-arm + ``naive_append_control`` sequential
   challenge ablation across all 3 tracks (16 tasks: ``C011``-``C060`` + ``WF52``) with
   paired exact McNemar ``Fraction`` p-values, Holm-Bonferroni correction, and
   ``ComparativeClaimAuditorV1`` validation.
"""

from __future__ import annotations

import re
from fractions import Fraction

import pytest

from eis.domain.value_objects import REGEX_MATCHER_ID, DetectorRule
from pfp_core import operad_ledger
from pfp_core.funnel_v1rc import (
    Tier1ProposalGeneratorV1,
    Tier2OpusFalsifierGateV1,
    Tier3FableDerivationRouterV1,
    generate_python_workflow_permutations,
    route_tier3_fable_derivations,
    run_tier2_opus_xhigh_gate,
    verify_lean4_snippet,
)
from pfp_core.outer_loop_v1rc import (
    COLLAPSE_QUOTIENT,
    GENESIS_LEDGER_HEAD,
    PROMOTE_ACCURACY,
    PROMOTE_COMPRESSION,
    REJECT_AUTOIMMUNE,
    REJECT_BLOAT,
    REJECT_REGRESSION,
    CandidateStrandDeltaV1,
    HostCheckOutcomeV1,
    OuterLoopCompressionControllerV1,
    StrandGenomeV1,
    TypedOp,
    ValidationCaseV1,
)
from pfp_core.sequential_ablation_v1rc import (
    ALL_ARMS,
    FOCAL_ARM,
    PRIMARY_ARMS,
    TRACK_1_FERMION_FINITE_QM,
    TRACK_2_COHOMOLOGY_OBSTRUCTION,
    TRACK_3_LEAN4_CERTIFICATES,
    SequentialAblationReportV1,
    exact_mcnemar_fraction,
    holm_bonferroni_adjust,
    run_five_arm_sequential_ablation,
)

FORBIDDEN_PROMOTIONAL_PATTERN = re.compile(
    r"\b(novel|breakthrough|revolutionary|unprecedented|seamless|bulletproof|state-of-the-art)\b",
    re.IGNORECASE,
)


def _canonical_rational_checker(candidate_text: str) -> HostCheckOutcomeV1:
    has_float = bool(re.search(r'"-?\d+\.\d+"', candidate_text))
    has_unreduced = bool(re.search(r'"(?:0/[2-9]\d*|2/4|-2/4|2/2)"', candidate_text))
    has_valid = ('"1/2"' in candidate_text) or ('"0/1"' in candidate_text) or ("by decide" in candidate_text)
    passed = has_valid and (not has_float) and (not has_unreduced) and ("native_decide" not in candidate_text)
    preds: list[str] = []
    if has_float:
        preds.append("float_literal_in_exact_path")
    if has_unreduced:
        preds.append("unreduced_rational_string")
    if "native_decide" in candidate_text:
        preds.append("lean4_banned_native_decide")
    if not passed and not preds:
        preds.append("missing_canonical_witness")
    return HostCheckOutcomeV1(passed=passed, failed_predicates=tuple(preds), evidence=candidate_text[:160])


@pytest.fixture(scope="module")
def full_ablation_report() -> SequentialAblationReportV1:
    """Execute the full 3-track, 16-task, 6-arm sequential ablation once for behavioral & statistical checks."""
    return run_five_arm_sequential_ablation("all")


def test_obstruction_extraction_synthesizes_safe_detectors_and_rejects_invalid_contracts() -> None:
    ctrl = OuterLoopCompressionControllerV1()
    inc = StrandGenomeV1(genome_id="seed_obs")

    lean_cand = ctrl.extract_obstruction_candidate(
        "c041_case",
        "theorem bad : 1 + 1 = 2 := by native_decide",
        ("lean4.banned_native_decide",),
        inc,
    )
    assert lean_cand.normalizer_id == "norm.lean_kernel_decide"
    assert lean_cand.authority_effect == "None"

    car_cand = ctrl.extract_obstruction_candidate(
        "c028_case",
        '{"majorana": "SIGN_DROP"}',
        ("c028.majorana_car_anticommutator",),
        inc,
    )
    assert car_cand.operation_wire is not None
    assert car_cand.operation_wire["body"] == "sum_list"

    cob_cand = ctrl.extract_obstruction_candidate(
        "c011_case",
        '{"residual": "UNBALANCED_CYCLE"}',
        ("c011.coboundary_circulation",),
        inc,
    )
    assert cob_cand.normalizer_id == "norm.rational_reduce"

    with pytest.raises(ValueError, match="NO_HOST_OBSTRUCTION"):
        ctrl.extract_obstruction_candidate("c_none", "draft", (), inc)

    with pytest.raises(TypeError, match="exact bool"):
        HostCheckOutcomeV1(passed=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="AUTHORITY_ESCALATION"):
        StrandGenomeV1(genome_id="bad_auth", authority_effect="Gate")


def test_thymus_gate_purges_autoimmune_candidate_with_zero_false_refusals_and_taints_lineage() -> None:
    ctrl = OuterLoopCompressionControllerV1()
    inc = StrandGenomeV1(genome_id="inc_clean")
    clean_panel = [
        '{"status": "SOLVED", "coeff": "1/2", "zero": "0/1"}',
        "theorem finite_ok : 1 + 1 = 2 := by decide",
    ]
    val_slice = [
        ValidationCaseV1(
            case_id="holdout_1",
            draft_reply='{"coeff": "0.5"}',
            host_checker=_canonical_rational_checker,
        )
    ]

    overbroad = CandidateStrandDeltaV1(
        candidate_id="cand_autoimmune",
        parent_genome_id=inc.genome_id,
        derived_from_failures=("train_fail_1@r0",),
        detector_rule=DetectorRule(
            rule_id="r_overbroad",
            target_epitope="self_reactive_solved",
            match_pattern=r"SOLVED",
            matcher_id=REGEX_MATCHER_ID,
        ),
        constraint_clause="Never emit SOLVED in output.",
        typed_ops=inc.typed_ops,
    )

    adopted, receipt = ctrl.evaluate_and_compress(inc, overbroad, val_slice, clean_panel)
    assert adopted == inc
    assert receipt.pciv_decision == REJECT_AUTOIMMUNE
    assert receipt.thymus_admitted is False
    assert receipt.autoimmune_violations >= 1
    assert "cand_autoimmune" in ctrl.tainted_genomes


def test_operad_quotient_collapses_reordered_and_duplicate_context_stages_before_trial() -> None:
    ctrl = OuterLoopCompressionControllerV1()
    ctx_a = TypedOp("ctx_a", "State", "State", "context", prompt_digest="da", cost_tokens=5, idempotent_key="da")
    ctx_b = TypedOp("ctx_b", "State", "State", "context", prompt_digest="db", cost_tokens=5, idempotent_key="db")
    gen = TypedOp("gen", "State", "Code", "generate", prompt_digest="g1", cost_tokens=12)
    chk = TypedOp("chk", "Code", "Receipt", "check", checker_id="host.public_smoke", cost_tokens=4)

    inc = StrandGenomeV1(genome_id="inc_ab", typed_ops=(ctx_a, ctx_b, gen, chk))
    clean_panel = ['{"status": "SOLVED", "coeff": "1/2"}']
    val_slice = [ValidationCaseV1(case_id="hold_q1", baseline_passed=True, treated_passed=True)]

    reordered_and_dup = CandidateStrandDeltaV1(
        candidate_id="cand_ba_dup",
        parent_genome_id="inc_ab",
        derived_from_failures=("obs_q@0",),
        detector_rule=DetectorRule("r_safe_q", "noop_q", "NEVER_HITS_CLEAN_PANEL"),
        constraint_clause="Equivalent reordered context pipeline.",
        typed_ops=(ctx_b, ctx_a, ctx_b, gen, chk),
    )

    adopted, receipt = ctrl.evaluate_and_compress(inc, reordered_and_dup, val_slice, clean_panel)
    assert adopted == inc
    assert receipt.pciv_decision == COLLAPSE_QUOTIENT
    assert receipt.quotient_collapsed is True
    assert receipt.baseline_tokens == 0
    assert receipt.treated_tokens == 0


def test_split_overlap_fence_rejects_held_out_case_overlapping_derived_failures() -> None:
    ctrl = OuterLoopCompressionControllerV1()
    inc = StrandGenomeV1(genome_id="inc_split")
    cand = ctrl.extract_obstruction_candidate(
        "leaked_case_42",
        '{"coeff": "0.5"}',
        ("float_literal_in_exact_path",),
        inc,
    )
    overlapping_slice = [
        ValidationCaseV1(
            case_id="leaked_case_42",
            draft_reply='{"coeff": "0.5"}',
            host_checker=_canonical_rational_checker,
        )
    ]
    with pytest.raises(ValueError, match="SPLIT_OVERLAP"):
        ctrl.evaluate_and_compress(inc, cand, overlapping_slice, ['{"coeff": "1/2"}'])


def test_pciv_pareto_accuracy_compression_bloat_regression_and_rust_ledger_chain() -> None:
    ctrl = OuterLoopCompressionControllerV1()
    inc = StrandGenomeV1(
        genome_id="seed_v1",
        constraints=(
            "Verbose legacy instruction alpha beta gamma delta epsilon zeta eta theta iota kappa lambda.",
            "Second verbose legacy clause mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega.",
        ),
        is_baseline=True,
    )
    clean_panel = ['{"status": "SOLVED", "coeff": "1/2"}']
    val_slice = [
        ValidationCaseV1(
            case_id="holdout_rat_1",
            family="rational",
            draft_reply='{"coeff": "0.5"}',
            host_checker=_canonical_rational_checker,
        ),
        ValidationCaseV1(
            case_id="holdout_rat_2",
            family="rational",
            draft_reply='{"coeff": "2/4"}',
            host_checker=_canonical_rational_checker,
        ),
    ]

    # 1. Accuracy promotion: repairs both held-out cases from 0/2 -> 2/2 and records Rust ledger admission.
    acc_cand = ctrl.extract_obstruction_candidate(
        "train_rat_0",
        '{"coeff": "0.5"}',
        ("float_literal_in_exact_path",),
        inc,
    )
    promoted, r_acc = ctrl.evaluate_and_compress(inc, acc_cand, val_slice, clean_panel)
    assert r_acc.pciv_decision == PROMOTE_ACCURACY
    assert r_acc.baseline_pass_rate == Fraction(0, 1)
    assert r_acc.treated_pass_rate == Fraction(1, 1)
    assert r_acc.ledger_head != GENESIS_LEDGER_HEAD
    assert promoted.genome_id == acc_cand.candidate_id

    # 2. Pure Pareto compression: consolidates verbose legacy constraints at equal 2/2 pass rate & fewer tokens.
    slim_ops = (
        TypedOp("ctx_slim", "State", "State", "context", prompt_digest="slim1", cost_tokens=2, idempotent_key="slim1"),
        *promoted.typed_ops[1:],
    )
    comp_cand = CandidateStrandDeltaV1(
        candidate_id="cand_slim_macro",
        parent_genome_id=promoted.genome_id,
        derived_from_failures=("train_comp_1@r0",),
        detector_rule=DetectorRule("r_slim", "canonical_rat", r'"-?\d{1,3}\.\d{1,3}"'),
        constraint_clause="Emit canonical p/q.",
        typed_ops=slim_ops,
        replaces_constraints=True,
        normalizer_id="norm.rational_and_decimal",
    )
    compressed, r_comp = ctrl.evaluate_and_compress(promoted, comp_cand, val_slice, clean_panel)
    assert r_comp.pciv_decision == PROMOTE_COMPRESSION
    assert r_comp.treated_pass_rate == r_comp.baseline_pass_rate == Fraction(1, 1)
    assert r_comp.treated_tokens < r_comp.baseline_tokens
    assert compressed.active_prompt_tokens < promoted.active_prompt_tokens

    # 3. Bloat rejection: adds 30-token context overhead without improving 2/2 pass rate.
    bloated_ops = (
        TypedOp("ctx_heavy", "State", "State", "context", prompt_digest="hvy", cost_tokens=40, idempotent_key="hvy"),
        *compressed.typed_ops,
    )
    bloat_cand = CandidateStrandDeltaV1(
        candidate_id="cand_verbose_bloat",
        parent_genome_id=compressed.genome_id,
        derived_from_failures=("train_bloat_2@r0",),
        detector_rule=DetectorRule("r_bloat", "noop", "NEVER_OCCURS_TOKEN"),
        constraint_clause="Long redundant prose instruction adding prompt overhead with zero accuracy benefit.",
        typed_ops=bloated_ops,
        normalizer_id="norm.rational_and_decimal",
    )
    after_bloat, r_bloat = ctrl.evaluate_and_compress(compressed, bloat_cand, val_slice, clean_panel)
    assert r_bloat.pciv_decision == REJECT_BLOAT
    assert after_bloat == compressed

    # 4. Regression rejection: candidate drops pass rate on a held-out case.
    reg_slice = [
        ValidationCaseV1(
            case_id="holdout_reg_1",
            family="rational",
            baseline_passed=True,
            treated_passed=False,
            baseline_tokens=30,
            treated_tokens=20,
        )
    ]
    reg_ops = (
        TypedOp("ctx_reg", "State", "State", "context", prompt_digest="reg1", cost_tokens=3, idempotent_key="reg1"),
        *compressed.typed_ops[1:],
    )
    reg_cand = CandidateStrandDeltaV1(
        candidate_id="cand_regressing",
        parent_genome_id=compressed.genome_id,
        derived_from_failures=("train_reg_3@r0",),
        detector_rule=DetectorRule("r_reg", "noop_reg", "NEVER_OCCURS_REG"),
        constraint_clause="Broken shortcut.",
        typed_ops=reg_ops,
    )
    after_reg, r_reg = ctrl.evaluate_and_compress(compressed, reg_cand, reg_slice, clean_panel)
    assert r_reg.pciv_decision == REJECT_REGRESSION
    assert r_reg.clean_panel_hits == 1
    assert after_reg == compressed

    verify_out = operad_ledger.verify(ctrl.ledger_path)
    assert verify_out["status"] == "PASS"


def test_active_regulation_never_blocks_host_certified_answer_and_enriches_repair() -> None:
    ctrl = OuterLoopCompressionControllerV1()
    rule = DetectorRule("r_warn", "advisory_marker", r"ADVISORY_FLAG")
    genome = StrandGenomeV1(
        genome_id="reg_genome",
        admitted_rules=(rule,),
        constraints=("Check advisory marker carefully.",),
        rule_constraints={"r_warn": "Replace ADVISORY_FLAG with canonical rational 1/2."},
    )

    # Host-certified reply containing Signal 1 match MUST still be certified (AuthorityEffect: None).
    valid_with_flag = '{"coeff": "1/2", "note": "ADVISORY_FLAG"}'
    rec_pass = ctrl.apply_active_regulation(genome, valid_with_flag, _canonical_rational_checker)
    assert rec_pass.certified is True
    assert rec_pass.repair_triggered is False
    assert rec_pass.matched_rule_ids == ("r_warn",)
    assert rec_pass.authority_effect == "None"

    # Host-failing reply triggers 1 bounded repair with BOTH host predicate and Signal 1 diagnostics.
    seen_prompts: list[str] = []

    def _repair_gen(prompt: str) -> str:
        seen_prompts.append(prompt)
        return '{"coeff": "1/2"}'

    rec_rep = ctrl.apply_active_regulation(
        genome,
        '{"coeff": "0.5", "note": "ADVISORY_FLAG"}',
        _canonical_rational_checker,
        repair_generator=_repair_gen,
    )
    assert rec_rep.certified is True
    assert rec_rep.repair_triggered is True
    assert rec_rep.calls_used == 2
    assert len(seen_prompts) == 1
    assert "float_literal_in_exact_path" in seen_prompts[0]
    assert "r_warn (advisory_marker)" in seen_prompts[0]


def test_tier1_generates_1024_permutations_with_quotient_collapse_and_boundary_fences() -> None:
    gen = Tier1ProposalGeneratorV1()
    batch = gen.generate(max_depth=4, target_count=1024)
    assert batch.total_generated == 1024
    assert 0 < batch.unique_quotient_classes < batch.total_generated
    assert batch.quotient_reduction_ratio == Fraction(1024 - batch.unique_quotient_classes, 1024)
    assert batch.quotient_reduction_ratio > Fraction(1, 2)
    assert len(batch.class_representatives) == batch.unique_quotient_classes
    assert batch.authority_effect == "None"

    # Also verify depth=1 and custom seed_ops enumeration.
    unary_batch = generate_python_workflow_permutations(max_depth=1, target_count=12)
    assert unary_batch.total_generated == 12
    assert unary_batch.unique_quotient_classes == 6

    seeds = (
        TypedOp("s_ctx", "State", "State", "context", prompt_digest="sd", cost_tokens=2, idempotent_key="sd"),
        TypedOp("s_gen", "State", "Code", "generate", prompt_digest="sg", cost_tokens=8),
    )
    seed_batch = generate_python_workflow_permutations(seed_ops=seeds, max_depth=3, target_count=5)
    assert seed_batch.total_generated == 5

    with pytest.raises(TypeError, match="exact int"):
        generate_python_workflow_permutations(max_depth=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="EMPTY_SEED_OPS"):
        generate_python_workflow_permutations(seed_ops=())
    with pytest.raises(ValueError, match="exceeds finite Tier 1 cap"):
        generate_python_workflow_permutations(target_count=20_001)


def test_tier2_opus_xhigh_gate_and_tier3_fable_router_preserve_zero_false_refusals() -> None:
    batch = generate_python_workflow_permutations(max_depth=4, target_count=256)
    clean_panel = [
        '{"status": "SOLVED", "coeff": "1/2", "zero": "0/1"}',
        "theorem clean_fin : 1 + 1 = 2 := by decide",
    ]
    val_cases = [
        ValidationCaseV1(
            case_id="funnel_val_rat",
            family="rational",
            draft_reply='{"coeff": "0.5"}',
            host_checker=_canonical_rational_checker,
        ),
        ValidationCaseV1(
            case_id="funnel_val_lean",
            family="lean4",
            draft_reply="theorem t : 1 + 1 = 2 := by native_decide",
            host_checker=_canonical_rational_checker,
        ),
    ]

    gate = Tier2OpusFalsifierGateV1()
    report = gate.evaluate(batch, clean_panel, val_cases)

    assert report.tier1_input_count == batch.unique_quotient_classes
    assert report.total_generated_before_quotient == 256
    assert report.killed_by_falsifier > 0
    assert report.killed_by_thymus > 0
    assert report.killed_by_pciv_bloat > 0
    assert len(report.survivors) > 0
    assert (
        report.killed_by_falsifier
        + report.killed_by_thymus
        + report.killed_by_pciv_bloat
        + len(report.withheld_without_replay)
        + len(report.survivors)
        == report.tier1_input_count
    )
    # Defective Lean 4 candidates (sorry & false Fin 4 claim) must be killed in Tier 2.
    assert "lean_cand_bad_sorry" in report.killed_lean4_proposals
    assert "lean_cand_bad_false_claim" in report.killed_lean4_proposals
    assert report.retest_plan is not None
    assert len(report.retest_settlements) > 0
    assert all(s.autoimmune_violations == 0 for s in report.survivors)

    trusted = batch.lean4_candidates[0]
    assert verify_lean4_snippet(trusted.lean_source) == (True, (), "LEAN_KERNEL_VERIFIED")
    assert verify_lean4_snippet("theorem ok_check : 2 + 2 = 4 := by decide")[0] is False

    router = Tier3FableDerivationRouterV1()
    packets = router.route(report)
    assert len(packets) == len(report.survivors)
    for pkt in packets:
        assert pkt.authority_effect == "None"
        assert pkt.rust_receipt_status == "PASS"
        assert len(pkt.rust_receipt_sha256) == 64
        assert pkt.lean4_verified and pkt.lean4_axioms == ()
        assert pkt.lean4_theorem_name == f"survivor_{pkt.rust_receipt_sha256}"
        assert pkt.atlas_claim_id is None and pkt.dag_node_id is None
        assert FORBIDDEN_PROMOTIONAL_PATTERN.search(pkt.prose_summary) is None

    # Direct function entrypoints match facade behavior.
    assert len(route_tier3_fable_derivations(run_tier2_opus_xhigh_gate(batch, clean_panel, val_cases))) == len(packets)


def test_five_arm_sequential_ablation_proves_pareto_dominance_and_statistical_rigor(
    full_ablation_report: SequentialAblationReportV1,
) -> None:
    rep = full_ablation_report
    assert rep.tracks_executed == (
        TRACK_1_FERMION_FINITE_QM,
        TRACK_2_COHOMOLOGY_OBSTRUCTION,
        TRACK_3_LEAN4_CERTIFICATES,
    )
    assert len(rep.task_sequence) == 16
    assert set(rep.arms.keys()) == set(ALL_ARMS)
    assert rep.has_held_out_split is True
    assert rep.multiplicity_correction == "holm-bonferroni"
    assert rep.claim_audit_status == "PASS"
    assert rep.comparative_auditor_passed is True
    assert rep.authority_effect == "None"

    focal = rep.arms[FOCAL_ARM]
    baseline = rep.arms["pfp_baseline"]
    eis_only = rep.arms["pfp_plus_eis"]
    operads_only = rep.arms["pfp_plus_operads"]
    pciv_only = rep.arms["pfp_plus_pciv"]
    naive = rep.arms["naive_append_control"]

    # 1. Focal full outer loop achieves highest cumulative pass rate & 0 autoimmune false refusals.
    for arm_id in PRIMARY_ARMS:
        assert focal.cumulative_pass_rate >= rep.arms[arm_id].cumulative_pass_rate
    assert focal.cumulative_pass_rate > baseline.cumulative_pass_rate
    assert focal.cumulative_pass_rate > operads_only.cumulative_pass_rate
    assert focal.cumulative_pass_rate > pciv_only.cumulative_pass_rate
    assert focal.cumulative_pass_rate > naive.cumulative_pass_rate
    assert focal.autoimmune_false_refusals == 0
    assert naive.autoimmune_false_refusals > 0
    assert pciv_only.autoimmune_false_refusals > 0

    # 2. Focal full outer loop achieves strictly lowest tokens_per_certified_solve & sole Pareto frontier win.
    assert focal.tokens_per_certified_solve is not None
    for other_id in ALL_ARMS:
        if other_id == FOCAL_ARM:
            continue
        other_tps = rep.arms[other_id].tokens_per_certified_solve
        assert other_tps is not None
        assert focal.tokens_per_certified_solve < other_tps
    assert rep.pareto_frontier_arms == (FOCAL_ARM,)

    # 3. Prompt token compression prevents linear prompt bloat seen in pfp_plus_eis and naive_append_control.
    assert focal.active_prompt_tokens < eis_only.active_prompt_tokens
    assert focal.active_prompt_tokens < operads_only.active_prompt_tokens
    assert eis_only.active_prompt_tokens < naive.active_prompt_tokens

    # 4. Exact rational McNemar + Holm-Bonferroni significance & Rust ledger integrity across all arms.
    assert all(m.ledger_verified is True for m in rep.arms.values())
    assert rep.paired_comparisons["pfp_baseline"].statistically_significant_alpha_05 is True
    assert rep.paired_comparisons["pfp_baseline"].holm_adjusted_p < Fraction(1, 20)
    assert rep.paired_comparisons["pfp_plus_operads"].statistically_significant_alpha_05 is True
    assert rep.paired_comparisons["naive_append_control"].statistically_significant_alpha_05 is True
    assert isinstance(rep.to_dict()["arms"][FOCAL_ARM]["cumulative_pass_rate"], str)


def test_single_track_execution_and_exact_mcnemar_holm_edge_cases() -> None:
    single = run_five_arm_sequential_ablation(TRACK_2_COHOMOLOGY_OBSTRUCTION)
    assert single.tracks_executed == (TRACK_2_COHOMOLOGY_OBSTRUCTION,)
    assert single.task_sequence == ("C011", "C012", "C014", "C018", "C019")
    assert single.arms[FOCAL_ARM].autoimmune_false_refusals == 0

    with pytest.raises(ValueError, match="UNKNOWN_TRACK_ID"):
        run_five_arm_sequential_ablation("nonexistent_track")

    assert exact_mcnemar_fraction(0, 0) == Fraction(1, 1)
    assert exact_mcnemar_fraction(10, 0) == Fraction(1, 512)
    adj = holm_bonferroni_adjust(
        {"a": Fraction(1, 100), "b": Fraction(3, 100), "c": Fraction(4, 10)}
    )
    assert adj["a"] == Fraction(3, 100)
    assert adj["b"] == Fraction(6, 100)
    assert adj["c"] == Fraction(4, 10)
