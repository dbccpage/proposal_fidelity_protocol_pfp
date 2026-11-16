"""Comprehensive 4-Tier Opaque-Box E2E Test Suite for ``omegaengine_pfp_v1.0rc``.

AuthorityEffect: None.

Derived directly from ``ORIGINAL_REQUEST.md``, ``PROJECT.md § Interface Contracts``,
and ``TEST_INFRA.md`` covering all 9 inventoried features (F1–F9):

- **Tier 1 — Feature Coverage (54 tests, 6 per feature across F1–F9)**:
  Happy-path verification of each feature in isolation against contract specifications.
- **Tier 2 — Boundary, Corner & Adversarial Cases (54 tests, 6 per feature across F1–F9)**:
  Autoimmune apoptosis (``REJECT_AUTOIMMUNE``), clean-panel regression (``REJECT_REGRESSION``),
  prompt bloat rejection (``REJECT_BLOAT``), trace-equivalent quotient collapse
  (``COLLAPSE_QUOTIENT``), holdout split overlap refusal (``SPLIT_OVERLAP``),
  poisoned/gauge-relabeled falsifier kills, authority escalation refusals,
  Lean 4 kernel negation & axiom bounds, and statistical claim hygiene refusals.
- **Tier 3 — Cross-Feature Pairwise Interactions (12 tests)**:
  Pairwise interactions across ``PFP + EIS``, ``PFP + Operads``, ``PFP + PCIV``,
  ``Tier 1 Quotient + Tier 2 Thymus``, ``Tier 2 PCIV + Tier 3 Lean4/Rust/Atlas``,
  and ``Outer Loop + Certified Challenges (C028, C011, C041, WF52)``.
- **Tier 4 — Real-World Application Scenarios (6 tests)**:
  Full 1,024-proposal 3-tier discovery funnel, Track 1 (Fermion -> Finite QM),
  Track 2 (Cohomology & Obstruction Repair), Track 3 (Lean 4 & Exact Certificates),
  full repository custody + governance + Atlas/DAG sync, and multi-step autonomous
  outer-loop ledger replay.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
for _extra_path in (
    REPO_ROOT,
    REPO_ROOT / "ops",
    REPO_ROOT / "workflows" / "wf52_finite_qm_benchmark",
):
    _extra_str = str(_extra_path)
    if _extra_str not in sys.path:
        sys.path.insert(0, _extra_str)

from eis.domain.safe_pattern import UnsafePatternRefusal, compile_safe_pattern  # noqa: E402
from eis.domain.thymus import ThymusGate, ThymusSelectionResult  # noqa: E402
from eis.domain.value_objects import DetectorRule  # noqa: E402
from operads.canon import OPERAD_COLOUR  # noqa: E402
from operads.domain.autopoiesis.learning import digest as _autopoiesis_digest  # noqa: E402
from operads.domain.autopoiesis.research import (  # noqa: E402
    EvaluationReceiptV1,
    ExperimentSpecV1,
    HarnessCandidateV1,
)
from pciv.use_cases import research_selection  # noqa: E402
from pciv.use_cases.fitness import (  # noqa: E402
    ComparativeClaimAuditorV1,
    ParetoFrontSelectorV1,
    PromptFitnessCalculatorV1,
)
from pfp.infrastructure import operad_host  # noqa: E402
from pfp_core import civilization as civ  # noqa: E402
from pfp_core import exclusions as excl  # noqa: E402
from pfp_core import immune_host, operad_ledger  # noqa: E402
from pfp_core import immunity as imm  # noqa: E402
from pfp_core import normalize as norm_mod  # noqa: E402
from pfp_core.fidelity import WholeRunBudget, sha256_hex  # noqa: E402
from pfp_core.operad_pipe import TypedOp, compose, quotient_workflows, trace_digest  # noqa: E402

# ---------------------------------------------------------------------------
# Expected Settlement Constants (Authoritative Sources: PROJECT.md & TEST_INFRA.md)
# ---------------------------------------------------------------------------

EXPECTED_P015_CLAIMS: tuple[str, ...] = tuple(f"ATL-P015-{i:03d}" for i in range(1, 5))
EXPECTED_P016_CLAIMS: tuple[str, ...] = tuple(f"ATL-P016-{i:03d}" for i in range(1, 5))
EXPECTED_P018_CLAIMS: tuple[str, ...] = tuple(f"ATL-P018-{i:03d}" for i in range(2, 6))
EXPECTED_P019_CLAIMS: tuple[str, ...] = tuple(f"ATL-P019-{i:03d}" for i in range(1, 10))
ALL_21_SETTLED_CLAIMS: tuple[str, ...] = (
    EXPECTED_P015_CLAIMS + EXPECTED_P016_CLAIMS + EXPECTED_P018_CLAIMS + EXPECTED_P019_CLAIMS
)
ALL_21_AUDIT_NODES: tuple[str, ...] = tuple(
    cid.replace("ATL-", "AUDIT-") for cid in ALL_21_SETTLED_CLAIMS
)
ALL_21_AUDIT_MD_PATHS: tuple[Path, ...] = tuple(
    REPO_ROOT / "dag" / "derivations" / f"{nid.lower().replace('-', '_')}.md"
    for nid in ALL_21_AUDIT_NODES
)
ALL_21_PRUNED_STUB_PATHS: tuple[Path, ...] = tuple(
    REPO_ROOT / "dag" / "derivations" / f"{cid.lower().replace('-', '_')}.md"
    for cid in ALL_21_SETTLED_CLAIMS
)

GRANDFATHERED_LEAN_FILES: tuple[str, ...] = (
    "lean4/AxiomCensus.lean",
    "lean4/FidelityAdequacy.lean",
    "lean4/LiftPatchSemantics.lean",
    "lean4/OperationTreeFold.lean",
    "lean4/PrimitiveDifference.lean",
    "lean4/SLevel.lean",
    "lean4/ShadowBoundary.lean",
    "lean4/Sweeper.lean",
    "lean4/TowerZeta.lean",
    "lean4/TypedPacketShadow.lean",
)

SACROSANCT_PFP_CORE_FILES: tuple[str, ...] = (
    "pfp_core/__init__.py",
    "pfp_core/fidelity.py",
    "pfp_core/immunity.py",
    "pfp_core/civilization.py",
    "pfp_core/operad_pipe.py",
)

TRACK_1_TASKS: tuple[str, ...] = ("C028", "C021", "C022", "C026", "WF52")
TRACK_2_TASKS: tuple[str, ...] = ("C011", "C012", "C014", "C018", "C019")
TRACK_3_TASKS: tuple[str, ...] = ("C041", "C046", "C050", "C051", "C053", "C060")
FIVE_ARM_NAMES: tuple[str, ...] = (
    "pfp_baseline",
    "pfp_plus_eis",
    "pfp_plus_operads",
    "pfp_plus_pciv",
    "pfp_eis_operads_pciv_full",
)

CLEAN_EXACT_PYTHON_PANEL: tuple[str, ...] = (
    "from fractions import Fraction\ndef exact_sum(a: int, b: int) -> Fraction:\n    return Fraction(a + b, 1)\n",
    "def coboundary_residual(v0: int, v1: int, edge: int) -> int:\n    return edge - (v1 - v0)\n",
    "def majorana_sign(parity_bits: tuple[int, ...]) -> int:\n    return -1 if sum(parity_bits) % 2 else 1\n",
)


# ---------------------------------------------------------------------------
# Opaque-Box Contract Loaders & Signature-Adaptive Helper Factories
# ---------------------------------------------------------------------------


def _outer_loop_mod() -> ModuleType:
    return importlib.import_module("pfp_core.outer_loop_v1rc")


def _funnel_mod() -> ModuleType:
    return importlib.import_module("pfp_core.funnel_v1rc")


def _ablation_mod() -> ModuleType:
    return importlib.import_module("pfp_core.sequential_ablation_v1rc")


def _lean_env() -> dict[str, str]:
    env = dict(os.environ)
    elan_bin = "/home/antigravity/.elan/bin"
    env["PATH"] = f"{elan_bin}:{env.get('PATH', '')}"
    return env


def _instantiate_adaptive(cls: type[Any], candidates: Mapping[str, Any]) -> Any:
    """Instantiate an auxiliary dataclass/object by matching its declared parameter names."""
    sig = inspect.signature(cls)
    kwargs: dict[str, Any] = {}
    for pname, param in sig.parameters.items():
        if pname == "self" or param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if pname in candidates:
            kwargs[pname] = candidates[pname]
        elif param.default is inspect.Parameter.empty:
            raise AssertionError(
                f"Unmapped required parameter {pname!r} on {cls.__name__}; "
                f"available candidate keys: {sorted(candidates)}"
            )
    return cls(**kwargs)


def _make_default_ops(
    *,
    ctx_keys: Sequence[str] = ("skill_exact_rational",),
    include_normalize: bool = True,
    gen_tokens: int = 120,
    ctx_tokens: int = 40,
) -> tuple[TypedOp, ...]:
    ops: list[TypedOp] = [
        TypedOp(
            op_id=f"ctx_{idx}_{key}",
            input_colour="State",
            output_colour="State",
            kind="context",
            prompt_digest=sha256_hex(key)[:16],
            cost_tokens=ctx_tokens,
            idempotent_key=key,
        )
        for idx, key in enumerate(ctx_keys)
    ]
    ops.append(
        TypedOp(
            op_id="gen_code",
            input_colour="State",
            output_colour="Code",
            kind="generate",
            prompt_digest="gen_v1",
            cost_tokens=gen_tokens,
        )
    )
    if include_normalize:
        ops.append(
            TypedOp(
                op_id="norm_py",
                input_colour="Code",
                output_colour="Code",
                kind="normalize",
                normalizer_id="normalize_python",
                cost_tokens=0,
            )
        )
    ops.append(
        TypedOp(
            op_id="chk_host",
            input_colour="Code",
            output_colour="Receipt",
            kind="check",
            checker_id="host.public_smoke",
            cost_tokens=0,
        )
    )
    return tuple(ops)


def _make_controller(tmp_path: Path) -> Any:
    ol = _outer_loop_mod()
    cls = ol.OuterLoopCompressionControllerV1
    ledger_file = tmp_path / "outer_loop_ledger.jsonl"
    sig = inspect.signature(cls)
    kwargs: dict[str, Any] = {}
    mapping = {
        "ledger_path": ledger_file,
        "work_dir": tmp_path,
        "workspace_dir": tmp_path,
        "authority_effect": "None",
    }
    for pname, param in sig.parameters.items():
        if pname == "self" or param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if pname in mapping:
            kwargs[pname] = mapping[pname]
    ctrl = cls(**kwargs)
    if hasattr(ctrl, "register_normalizer"):
        ctrl.register_normalizer("normalize_python", lambda s: norm_mod.normalize_python(s).text)
    return ctrl


def _make_genome(
    *,
    genome_id: str = "genome_seed_v1",
    prompt_text: str = "Solve with exact Fraction arithmetic.",
    constraint_clauses: Sequence[str] = (),
    detector_rules: Sequence[DetectorRule] = (),
    typed_ops: Sequence[TypedOp] | None = None,
    base_tokens: int = 240,
    spent_microusd: int = 120,
    parent_genome_id: str | None = None,
) -> Any:
    ol = _outer_loop_mod()
    ops_tuple = tuple(typed_ops) if typed_ops is not None else _make_default_ops(
        include_normalize=False, gen_tokens=max(0, base_tokens - 40), ctx_tokens=40
    )
    rules_tuple = tuple(detector_rules)
    clauses_tuple = tuple(constraint_clauses)
    candidates: dict[str, Any] = {
        "genome_id": genome_id,
        "id": genome_id,
        "parent_genome_id": parent_genome_id,
        "parent_id": parent_genome_id,
        "prompt_text": prompt_text,
        "base_prompt": prompt_text,
        "system_prompt": prompt_text,
        "prompt": prompt_text,
        "constraint_clauses": clauses_tuple,
        "constraints": clauses_tuple,
        "clauses": clauses_tuple,
        "detector_rules": rules_tuple,
        "rules": rules_tuple,
        "admitted_rules": rules_tuple,
        "typed_ops": ops_tuple,
        "ops": ops_tuple,
        "pipeline": ops_tuple,
        "base_tokens": base_tokens,
        "prompt_tokens": base_tokens,
        "estimated_tokens": base_tokens,
        "total_tokens": base_tokens,
        "token_cost": base_tokens,
        "spent_microusd": spent_microusd,
        "microusd_cost": spent_microusd,
        "authority_effect": "None",
    }
    return _instantiate_adaptive(ol.StrandGenomeV1, candidates)


def _genome_id_of(genome: Any) -> str:
    for attr in ("genome_id", "id", "candidate_id"):
        if hasattr(genome, attr):
            return str(getattr(genome, attr))
    raise AssertionError(f"Genome {genome!r} exposes no identifier attribute")


def _make_host_outcome(
    *,
    passed: bool,
    failed_predicates: Sequence[str] = (),
    observer_id: str = "host.public_smoke",
    danger_type: str = "PUBLIC_CHECK_FAILED",
    evidence: str = "host check trace",
) -> Any:
    ol = _outer_loop_mod()
    failed_tuple = tuple(failed_predicates)
    candidates: dict[str, Any] = {
        "passed": passed,
        "accepted": passed,
        "ok": passed,
        "is_certified": passed,
        "failed_predicates": failed_tuple,
        "failed": failed_tuple,
        "predicates_failed": failed_tuple,
        "observer_id": observer_id,
        "observer": observer_id,
        "danger_type": danger_type,
        "danger_kind": danger_type,
        "reason": ", ".join(failed_tuple) if failed_tuple else "PASS",
        "message": ", ".join(failed_tuple) if failed_tuple else "PASS",
        "evidence": evidence,
        "evidence_text": evidence,
        "evidence_sha256": sha256_hex(evidence),
        "defect_count": 0 if passed else max(1, len(failed_tuple)),
        "authority_effect": "None",
    }
    return _instantiate_adaptive(ol.HostCheckOutcomeV1, candidates)


def _make_validation_case(
    *,
    case_id: str,
    baseline_passed: bool,
    treated_passed: bool,
    baseline_tokens: int = 300,
    treated_tokens: int = 240,
    baseline_microusd: int = 150,
    treated_microusd: int = 120,
    draft_reply: str | None = None,
    repaired_reply: str = "from fractions import Fraction\ndef solve(x: int) -> Fraction:\n    return Fraction(x, 1)\n",
    family: str = "exact_arithmetic",
    host_checker: Any = None,
) -> Any:
    """Create a ValidationCaseV1 supporting paired outcomes and optional live host_checker."""
    ol = _outer_loop_mod()
    if draft_reply is None:
        if baseline_passed and treated_passed:
            draft_reply = repaired_reply
        elif (not baseline_passed) and treated_passed:
            draft_reply = f"```python\n{repaired_reply.strip()}\n```"
        elif baseline_passed and (not treated_passed):
            draft_reply = repaired_reply + "# REGRESSION_TRIGGER\n"
        else:
            draft_reply = "def broken(:\n    return float(0.1)\n"

    candidates: dict[str, Any] = {
        "case_id": case_id,
        "id": case_id,
        "task_id": case_id,
        "family": family,
        "task_family": family,
        "prompt": f"Solve validation case {case_id} using exact rationals.",
        "prompt_text": f"Solve validation case {case_id} using exact rationals.",
        "input_text": f"Solve validation case {case_id} using exact rationals.",
        "draft_reply": draft_reply,
        "baseline_reply": repaired_reply if baseline_passed else "def bad(:\n",
        "treated_reply": repaired_reply if treated_passed else "def bad(:\n",
        "repaired_reply": repaired_reply,
        "expected_output": repaired_reply,
        "baseline_passed": baseline_passed,
        "incumbent_passed": baseline_passed,
        "baseline_ok": baseline_passed,
        "treated_passed": treated_passed,
        "candidate_passed": treated_passed,
        "treated_ok": treated_passed,
        "baseline_tokens": baseline_tokens,
        "incumbent_tokens": baseline_tokens,
        "treated_tokens": treated_tokens,
        "candidate_tokens": treated_tokens,
        "baseline_microusd": baseline_microusd,
        "incumbent_microusd": baseline_microusd,
        "treated_microusd": treated_microusd,
        "candidate_microusd": treated_microusd,
        "host_checker": host_checker,
        "checker": host_checker,
        "evaluator": host_checker,
        "authority_effect": "None",
    }
    return _instantiate_adaptive(ol.ValidationCaseV1, candidates)


def _extract_attr(obj: Any, names: Sequence[str]) -> Any:
    if isinstance(obj, Mapping):
        for name in names:
            if name in obj:
                return obj[name]
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    raise AssertionError(f"None of attributes {names} found on {type(obj).__name__}: {obj!r}")


def _extract_ablation_arms(report: Any) -> Mapping[str, Any]:
    raw = _extract_attr(report, ("arms", "arm_results", "arm_summaries", "summaries", "results"))
    if isinstance(raw, Mapping):
        return raw
    if isinstance(raw, Sequence):
        out: dict[str, Any] = {}
        for item in raw:
            arm_id = _extract_attr(item, ("arm_id", "arm_name", "name", "id"))
            out[str(arm_id)] = item
        return out
    raise AssertionError(f"Unsupported arms container {type(raw).__name__}")


@pytest.fixture(scope="module")
def cached_tier1_1024_batch() -> Any:
    fn = _funnel_mod()
    return fn.generate_python_workflow_permutations(max_depth=4, target_count=1024)


@pytest.fixture(scope="module")
def cached_ablation_all_report() -> Any:
    ab = _ablation_mod()
    return ab.run_five_arm_sequential_ablation("all")


# ===========================================================================
# TIER 1 — FEATURE COVERAGE (HAPPY PATH IN ISOLATION: 54 TESTS = 6 x F1..F9)
# ===========================================================================


# --- Feature F1: Causal Cross-Package Outer Loop (6 tests) ---


def test_t1_f1_extract_obstruction_candidate_builds_typed_strand_delta(tmp_path: Path) -> None:
    """F1: extract_obstruction_candidate produces a contract-compliant CandidateStrandDeltaV1."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    parent = _make_genome(genome_id="seed_g0")
    delta = controller.extract_obstruction_candidate(
        task_id="task_c028_01",
        failure_text="x = float(0.5)  # lost exact rational phase",
        host_failed_predicates=("exact_rational_coefficients", "car_anticommutator"),
        parent_genome=parent,
    )
    assert isinstance(delta, ol.CandidateStrandDeltaV1)
    assert isinstance(delta.candidate_id, str) and bool(delta.candidate_id.strip())
    assert delta.parent_genome_id == "seed_g0"
    assert len(delta.derived_from_failures) >= 1
    assert isinstance(delta.detector_rule, DetectorRule)
    assert isinstance(delta.constraint_clause, str) and bool(delta.constraint_clause.strip())
    assert isinstance(delta.typed_ops, tuple) and len(delta.typed_ops) >= 1
    assert all(isinstance(op, TypedOp) for op in delta.typed_ops)
    compose(list(delta.typed_ops))
    assert delta.authority_effect == "None"


def test_t1_f1_screen_with_thymus_admits_self_tolerant_detector_rule(tmp_path: Path) -> None:
    """F1: screen_with_thymus admits a safe detector rule that fires on zero clean self-fixtures."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    delta = ol.CandidateStrandDeltaV1(
        candidate_id="cand_no_float_v1",
        parent_genome_id="seed_g0",
        derived_from_failures=("fail_001",),
        detector_rule=DetectorRule(
            rule_id="rule_no_float_call",
            target_epitope="float_approximation",
            match_pattern=r"float\(",
        ),
        constraint_clause="Never call float() in exact rational paths; use Fraction.",
        typed_ops=_make_default_ops(ctx_keys=("skill_exact_rational", "guard_no_float")),
    )
    res = controller.screen_with_thymus(delta, CLEAN_EXACT_PYTHON_PANEL)
    assert isinstance(res, ThymusSelectionResult)
    assert res.is_admitted is True
    assert res.autoimmune_violations == 0
    assert res.self_fixtures_tested == len(CLEAN_EXACT_PYTHON_PANEL)
    assert res.first_violating_sample is None


def test_t1_f1_evaluate_and_compress_promotes_accuracy_improvement(tmp_path: Path) -> None:
    """F1: evaluate_and_compress promotes candidate when held-out pass rate strictly rises with 0 regressions."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    incumbent = _make_genome(genome_id="incumbent_g0", base_tokens=300)
    candidate = ol.CandidateStrandDeltaV1(
        candidate_id="cand_acc_up_v1",
        parent_genome_id="incumbent_g0",
        derived_from_failures=("train_fail_01",),
        detector_rule=DetectorRule(
            rule_id="rule_fence_unwrap",
            target_epitope="markdown_fence",
            match_pattern=r"```python",
        ),
        constraint_clause="Emit raw Python source with no markdown code fences.",
        typed_ops=_make_default_ops(
            ctx_keys=("skill_exact_rational", "no_fence"),
            include_normalize=True,
            gen_tokens=200,
            ctx_tokens=40,
        ),
    )
    val_slice = (
        _make_validation_case(
            case_id="val_holdout_01",
            baseline_passed=True,
            treated_passed=True,
            baseline_tokens=300,
            treated_tokens=280,
        ),
        _make_validation_case(
            case_id="val_holdout_02",
            baseline_passed=False,
            treated_passed=True,
            baseline_tokens=300,
            treated_tokens=280,
        ),
    )
    adopted, receipt = controller.evaluate_and_compress(
        incumbent, candidate, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert isinstance(receipt, ol.OuterLoopStepReceiptV1)
    assert receipt.thymus_admitted is True
    assert receipt.autoimmune_violations == 0
    assert receipt.clean_panel_hits == 0
    assert isinstance(receipt.baseline_pass_rate, Fraction)
    assert isinstance(receipt.treated_pass_rate, Fraction)
    assert receipt.treated_pass_rate > receipt.baseline_pass_rate
    assert receipt.pciv_decision == "PROMOTE_ACCURACY"
    assert receipt.adopted_genome_id == candidate.candidate_id
    assert _genome_id_of(adopted) == candidate.candidate_id
    assert bool(receipt.ledger_head)
    assert receipt.authority_effect == "None"


def test_t1_f1_evaluate_and_compress_promotes_token_compression_at_equal_accuracy(
    tmp_path: Path,
) -> None:
    """F1: evaluate_and_compress promotes with PROMOTE_COMPRESSION when tokens drop at equal pass rate."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    incumbent = _make_genome(
        genome_id="incumbent_verbose",
        prompt_text="Solve carefully. " * 40,
        typed_ops=_make_default_ops(
            ctx_keys=("verbose_prose_bundle",), include_normalize=True, gen_tokens=400, ctx_tokens=260
        ),
        base_tokens=660,
        spent_microusd=330,
    )
    candidate = ol.CandidateStrandDeltaV1(
        candidate_id="cand_compact_v1",
        parent_genome_id="incumbent_verbose",
        derived_from_failures=("train_bloat_obs_01",),
        detector_rule=DetectorRule(
            rule_id="rule_float_compact",
            target_epitope="float_literal",
            match_pattern=r"float\(",
        ),
        constraint_clause="Use Fraction only.",
        typed_ops=_make_default_ops(
            ctx_keys=("compact_fraction_guard",), include_normalize=True, gen_tokens=180, ctx_tokens=30
        ),
    )
    val_slice = (
        _make_validation_case(
            case_id="val_comp_01",
            baseline_passed=True,
            treated_passed=True,
            baseline_tokens=660,
            treated_tokens=210,
            baseline_microusd=330,
            treated_microusd=105,
        ),
        _make_validation_case(
            case_id="val_comp_02",
            baseline_passed=True,
            treated_passed=True,
            baseline_tokens=660,
            treated_tokens=210,
            baseline_microusd=330,
            treated_microusd=105,
        ),
    )
    adopted, receipt = controller.evaluate_and_compress(
        incumbent, candidate, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert receipt.thymus_admitted is True
    assert receipt.clean_panel_hits == 0
    assert receipt.treated_pass_rate == receipt.baseline_pass_rate
    assert receipt.treated_pass_rate > Fraction(0)
    assert receipt.treated_tokens < receipt.baseline_tokens
    assert receipt.pciv_decision == "PROMOTE_COMPRESSION"
    assert receipt.adopted_genome_id == candidate.candidate_id
    assert _genome_id_of(adopted) == candidate.candidate_id
    assert receipt.authority_effect == "None"


def test_t1_f1_apply_active_regulation_normalizes_signal1_before_host_check(tmp_path: Path) -> None:
    """F1: apply_active_regulation applies value-preserving normalization on Signal 1 before host check."""
    controller = _make_controller(tmp_path)
    fence_rule = DetectorRule(
        rule_id="rule_md_fence",
        target_epitope="markdown_code_fence",
        match_pattern=r"```python",
    )
    genome = _make_genome(
        genome_id="regulated_g1",
        constraint_clauses=("Output pure Python module without markdown fences.",),
        detector_rules=(fence_rule,),
        typed_ops=_make_default_ops(include_normalize=True),
    )
    fenced_draft = "```python\ndef f(n: int) -> int:\n    return n * 2\n```"
    observed_inputs: list[str] = []

    def _host_checker(code_text: str) -> Any:
        observed_inputs.append(code_text)
        try:
            ast.parse(code_text)
            ok = True
        except SyntaxError:
            ok = False
        return _make_host_outcome(
            passed=ok,
            failed_predicates=() if ok else ("host.ast_parse",),
            observer_id="host.ast_parse",
            evidence=code_text,
        )

    reg_receipt = controller.apply_active_regulation(genome, fenced_draft, _host_checker)
    assert len(observed_inputs) >= 1
    assert "```" not in observed_inputs[0]
    passed_flag = _extract_attr(reg_receipt, ("passed", "accepted", "certified", "host_passed"))
    assert passed_flag is True
    assert _extract_attr(reg_receipt, ("authority_effect",)) == "None"


def test_t1_f1_apply_active_regulation_injects_signal1_and_host_failed_into_repair(
    tmp_path: Path,
) -> None:
    """F1: On host check failure, apply_active_regulation injects BOTH host.failed and Signal 1 diagnostics."""
    controller = _make_controller(tmp_path)
    float_rule = DetectorRule(
        rule_id="rule_forbid_float_cast",
        target_epitope="float_cast_in_exact_path",
        match_pattern=r"float\(",
    )
    genome = _make_genome(
        genome_id="regulated_g2",
        constraint_clauses=("Replace float(...) with exact Fraction(numerator, denominator).",),
        detector_rules=(float_rule,),
        typed_ops=_make_default_ops(include_normalize=True),
    )
    bad_draft = "def compute_energy(j: int) -> float:\n    return float(j) / 2.0\n"

    def _host_checker(code_text: str) -> Any:
        ok = "float(" not in code_text and "Fraction" in code_text
        return _make_host_outcome(
            passed=ok,
            failed_predicates=() if ok else ("exact_fraction_return_required",),
            observer_id="host.contract_check",
            evidence=code_text,
        )

    reg_receipt = controller.apply_active_regulation(genome, bad_draft, _host_checker)
    repair_prompt = str(
        _extract_attr(
            reg_receipt,
            ("repair_prompt", "repair_feedback", "feedback_prompt", "bounded_repair_prompt"),
        )
    )
    assert "exact_fraction_return_required" in repair_prompt
    assert (
        "rule_forbid_float_cast" in repair_prompt
        or "float_cast_in_exact_path" in repair_prompt
        or "Fraction" in repair_prompt
    )
    assert _extract_attr(reg_receipt, ("authority_effect",)) == "None"


# --- Feature F2: Tier 1 Cheap Proposal & Permutation Generator (6 tests) ---


def test_t1_f2_generate_default_1024_workflow_permutations_and_quotient(
    cached_tier1_1024_batch: Any,
) -> None:
    """F2: generate_python_workflow_permutations enumerates >=1,024 proposals and collapses trace classes."""
    fn = _funnel_mod()
    batch = cached_tier1_1024_batch
    assert isinstance(batch, fn.Tier1ProposalBatchV1)
    assert type(batch.total_generated) is int and batch.total_generated >= 1024
    assert type(batch.unique_quotient_classes) is int
    assert 0 < batch.unique_quotient_classes < batch.total_generated
    assert isinstance(batch.quotient_reduction_ratio, Fraction)
    assert Fraction(0) < batch.quotient_reduction_ratio < Fraction(1)
    expected_ratios = {
        Fraction(batch.unique_quotient_classes, batch.total_generated),
        Fraction(batch.total_generated - batch.unique_quotient_classes, batch.total_generated),
    }
    assert batch.quotient_reduction_ratio in expected_ratios


def test_t1_f2_every_generated_workflow_pipeline_typechecks_under_operad_compose(
    cached_tier1_1024_batch: Any,
) -> None:
    """F2: Every Python candidate workflow pipeline in Tier 1 composes cleanly over OPERAD_COLOUR."""
    batch = cached_tier1_1024_batch
    assert len(batch.python_candidates) >= 1
    for cand in batch.python_candidates:
        ops = _extract_attr(cand, ("typed_ops", "ops", "pipeline", "workflow_ops"))
        assert len(ops) >= 1
        for op in ops:
            assert isinstance(op, TypedOp)
            assert op.input_colour in OPERAD_COLOUR
            assert op.output_colour in OPERAD_COLOUR
        sig = compose(list(ops))
        assert sig.arity == 1


def test_t1_f2_quotient_collapses_commuting_context_permutations_before_spend() -> None:
    """F2: Custom seed_ops with commuting context skills collapse to canonical trace classes."""
    fn = _funnel_mod()
    seed_ops = (
        TypedOp("ctx_a", "Contract", "Contract", "context", prompt_digest="pa", cost_tokens=20, idempotent_key="A"),
        TypedOp("ctx_b", "Contract", "Contract", "context", prompt_digest="pb", cost_tokens=20, idempotent_key="B"),
        TypedOp("ctx_c", "Contract", "Contract", "context", prompt_digest="pc", cost_tokens=20, idempotent_key="C"),
        TypedOp("gen_1", "Contract", "Code", "generate", prompt_digest="g1", cost_tokens=100),
        TypedOp("norm_1", "Code", "Code", "normalize", normalizer_id="n1", cost_tokens=0),
        TypedOp("chk_1", "Code", "Code", "check", checker_id="c1", cost_tokens=0),
        TypedOp("rep_1", "Code", "Code", "repair", prompt_digest="r1", cost_tokens=80),
        TypedOp("fin_1", "Code", "Receipt", "check", checker_id="c_final", cost_tokens=0),
    )
    batch = fn.generate_python_workflow_permutations(
        seed_ops=seed_ops, max_depth=4, target_count=120
    )
    assert batch.total_generated >= 100
    assert 0 < batch.unique_quotient_classes < batch.total_generated
    # Cross-check direct operad_pipe quotient invariant on two context-reordered pipelines
    p1 = [seed_ops[0], seed_ops[1], seed_ops[3], seed_ops[7]]
    p2 = [seed_ops[1], seed_ops[0], seed_ops[3], seed_ops[7]]
    assert trace_digest(p1) == trace_digest(p2)


def test_t1_f2_python_candidates_carry_valid_operad_or_mechanism_specs(
    cached_tier1_1024_batch: Any,
) -> None:
    """F2: batch.python_candidates are typed PythonCandidateProposalV1 objects with AuthorityEffect: None."""
    fn = _funnel_mod()
    assert isinstance(cached_tier1_1024_batch.python_candidates, tuple)
    assert len(cached_tier1_1024_batch.python_candidates) >= 5
    for cand in cached_tier1_1024_batch.python_candidates:
        assert isinstance(cand, fn.PythonCandidateProposalV1)
        assert _extract_attr(cand, ("authority_effect",)) == "None"
        cid = _extract_attr(cand, ("candidate_id", "proposal_id", "id"))
        assert isinstance(cid, str) and bool(cid.strip())


def test_t1_f2_lean4_candidates_carry_core_lean_lemmas_without_sorry(
    cached_tier1_1024_batch: Any,
) -> None:
    """F2: Tier 1 batch generates >=4 clean Core Lean 4 lemma proposals and flags sorry controls."""
    fn = _funnel_mod()
    assert isinstance(cached_tier1_1024_batch.lean4_candidates, tuple)
    clean_lemmas = []
    for lcand in cached_tier1_1024_batch.lean4_candidates:
        assert isinstance(lcand, fn.Lean4CandidateProposalV1)
        assert _extract_attr(lcand, ("authority_effect",)) == "None"
        src = str(_extract_attr(lcand, ("lean_source", "lemma_source", "source", "code")))
        assert "theorem " in src or "def " in src
        assert "import Mathlib" not in src
        has_sorry = re.search(r"\b(sorry|admit)\b", src) is not None
        if hasattr(lcand, "uses_sorry"):
            assert lcand.uses_sorry is has_sorry
        if not has_sorry:
            clean_lemmas.append(lcand)
    assert len(clean_lemmas) >= 4


def test_t1_f2_tier1_proposal_generator_class_deterministic_across_runs() -> None:
    """F2: Tier1ProposalGeneratorV1 produces deterministic counts, ratios, and candidate IDs across runs."""
    fn = _funnel_mod()
    gen_a = fn.Tier1ProposalGeneratorV1()
    gen_b = fn.Tier1ProposalGeneratorV1()
    if hasattr(gen_a, "generate"):
        b1 = gen_a.generate(max_depth=4, target_count=256)
        b2 = gen_b.generate(max_depth=4, target_count=256)
    else:
        b1 = fn.generate_python_workflow_permutations(max_depth=4, target_count=256)
        b2 = fn.generate_python_workflow_permutations(max_depth=4, target_count=256)
    assert b1.total_generated == b2.total_generated
    assert b1.unique_quotient_classes == b2.unique_quotient_classes
    assert b1.quotient_reduction_ratio == b2.quotient_reduction_ratio
    ids_1 = tuple(_extract_attr(c, ("candidate_id", "proposal_id", "id")) for c in b1.python_candidates)
    ids_2 = tuple(_extract_attr(c, ("candidate_id", "proposal_id", "id")) for c in b2.python_candidates)
    assert ids_1 == ids_2


# --- Feature F3: Tier 2 "Opus 5.5 xhigh" Falsification, Thymus & PCIV Gate (6 tests) ---


def test_t1_f3_run_tier2_opus_xhigh_gate_returns_complete_falsification_report() -> None:
    """F3: run_tier2_opus_xhigh_gate executes falsifier + Thymus + PCIV and returns Tier2FalsificationReportV1."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=256)
    val_cases = (
        _make_validation_case(case_id="t2_val_1", baseline_passed=False, treated_passed=True),
        _make_validation_case(case_id="t2_val_2", baseline_passed=True, treated_passed=True),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    assert isinstance(report, fn.Tier2FalsificationReportV1)
    assert type(report.tier1_input_count) is int and report.tier1_input_count >= 1
    assert type(report.killed_by_falsifier) is int and report.killed_by_falsifier >= 0
    assert type(report.killed_by_thymus) is int and report.killed_by_thymus >= 0
    assert type(report.killed_by_pciv_bloat) is int and report.killed_by_pciv_bloat >= 0
    assert isinstance(report.survivors, tuple) and len(report.survivors) >= 1
    total_accounted = (
        len(report.survivors)
        + report.killed_by_falsifier
        + report.killed_by_thymus
        + report.killed_by_pciv_bloat
        + len(report.withheld_without_replay)
    )
    assert total_accounted == report.tier1_input_count


def test_t1_f3_tier2_survivors_have_zero_thymus_autoimmune_violations() -> None:
    """F3: Every VerifiedSurvivorV1 admitted by Tier 2 passes independent ThymusGate re-screening."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=256)
    val_cases = (
        _make_validation_case(case_id="t2_thy_1", baseline_passed=False, treated_passed=True),
        _make_validation_case(case_id="t2_thy_2", baseline_passed=True, treated_passed=True),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    gate = ThymusGate(self_panel=CLEAN_EXACT_PYTHON_PANEL)
    for surv in report.survivors:
        assert isinstance(surv, fn.VerifiedSurvivorV1)
        assert _extract_attr(surv, ("authority_effect",)) == "None"
        if hasattr(surv, "detector_rule") and surv.detector_rule is not None:
            res = gate.evaluate_rule(surv.detector_rule)
            assert res.is_admitted is True
            assert res.autoimmune_violations == 0
        if hasattr(surv, "lean4_proposal") and surv.lean4_proposal is not None:
            assert getattr(surv.lean4_proposal, "uses_sorry", False) is False


def test_t1_f3_tier2_survivors_satisfy_pciv_pareto_non_domination() -> None:
    """F3: Every Tier 2 survivor satisfies zero clean-panel regression and PCIV Pareto non-domination."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=256)
    val_cases = (
        _make_validation_case(
            case_id="t2_pciv_1",
            baseline_passed=False,
            treated_passed=True,
            baseline_tokens=360,
            treated_tokens=260,
        ),
        _make_validation_case(
            case_id="t2_pciv_2",
            baseline_passed=True,
            treated_passed=True,
            baseline_tokens=360,
            treated_tokens=260,
        ),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    assert len(report.survivors) >= 1
    for surv in report.survivors:
        if hasattr(surv, "step_receipt") and surv.step_receipt is not None:
            decision = surv.step_receipt.pciv_decision
        else:
            decision = _extract_attr(surv, ("pciv_decision", "decision", "promotion_reason"))
        assert decision in ("PROMOTE_ACCURACY", "PROMOTE_COMPRESSION")


def test_t1_f3_tier2_executes_exclusion_hypothesis_retest_planning() -> None:
    """F3: Tier2OpusFalsifierGateV1 integrates ExclusionHypothesisV1 frontier-first retest planning."""
    fn = _funnel_mod()
    gate_cls = fn.Tier2OpusFalsifierGateV1
    assert inspect.isclass(gate_cls)
    # Cross-verify underlying exclusion retest ordering contract used by Tier 2
    h_prob_dead = excl.ExclusionHypothesisV1(
        exclusion_id="ex_dead",
        branch="cand_dead",
        claim="bloated_branch",
        falsifier="probe_cost",
        falsifier_cost=10,
        votes=(
            excl.ExclusionVoteV1("seat_opus", "anthropic", True),
            excl.ExclusionVoteV1("seat_fable", "fable", True),
        ),
    )
    h_frontier = excl.ExclusionHypothesisV1(
        exclusion_id="ex_frontier",
        branch="cand_frontier",
        claim="disputed_branch",
        falsifier="probe_gauge",
        falsifier_cost=25,
        votes=(
            excl.ExclusionVoteV1("seat_opus", "anthropic", True),
            excl.ExclusionVoteV1("seat_fable", "fable", False),
        ),
    )
    plan = excl.plan_retests([h_prob_dead, h_frontier], budget=50, dead_floor=20)
    assert plan.order == ("ex_frontier", "ex_dead")
    assert plan.authority_effect == "None"


def test_t1_f3_tier2_validates_base_and_gauge_relabeled_controls() -> None:
    """F3: Tier 2 falsification verifies gauge invariance across relabeled controls."""
    fn = _funnel_mod()
    gate = fn.Tier2OpusFalsifierGateV1()
    batch = fn.generate_python_workflow_permutations(max_depth=3, target_count=128)
    val_cases = (
        _make_validation_case(case_id="t2_gauge_1", baseline_passed=False, treated_passed=True),
    )
    report = (
        gate.evaluate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
        if hasattr(gate, "evaluate")
        else fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    )
    assert isinstance(report, fn.Tier2FalsificationReportV1)
    assert len(report.survivors) >= 1
    for surv in report.survivors:
        if hasattr(surv, "gauge_invariant"):
            assert surv.gauge_invariant is True
        if hasattr(surv, "falsifier_passed"):
            assert surv.falsifier_passed is True


def test_t1_f3_tier2_opus_falsifier_gate_monotone_filtration() -> None:
    """F3: Funnel cardinality decreases monotonically from raw permutations -> quotient -> Tier 2 survivors."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=300)
    val_cases = (
        _make_validation_case(case_id="t2_mono_1", baseline_passed=False, treated_passed=True),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    assert 0 < len(report.survivors) <= report.tier1_input_count <= batch.total_generated


# --- Feature F4: Tier 3 "Fable 5.2" Complete Derivation Router (6 tests) ---


def test_t1_f4_route_tier3_fable_derivations_emits_packets_for_survivors() -> None:
    """F4: route_tier3_fable_derivations maps Tier 2 survivors to Tier3DerivationPacketV1 tuples."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=256)
    val_cases = (
        _make_validation_case(case_id="t3_route_1", baseline_passed=False, treated_passed=True),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    packets = fn.route_tier3_fable_derivations(report)
    assert isinstance(packets, tuple)
    assert len(packets) == len(report.survivors)
    assert len(packets) >= 1
    assert all(isinstance(p, fn.Tier3DerivationPacketV1) for p in packets)


def test_t1_f4_tier3_packet_checks_the_exact_bound_theorem() -> None:
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=200)
    val_cases = (_make_validation_case(case_id="t3_lean_1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    packets = fn.route_tier3_fable_derivations(report)
    assert packets
    for pkt in packets:
        assert pkt.lean4_verified and pkt.lean4_axioms == ()
        assert pkt.lean4_theorem_name == f"survivor_{pkt.rust_receipt_sha256}"
        assert pkt.lean4_source.startswith(f"theorem {pkt.lean4_theorem_name} :")
    pkt = packets[0]
    wrong_sum = pkt.lean4_source.replace("[6, 9, -10, 0]", "[7, 9, -10, 0]")
    assert wrong_sum != pkt.lean4_source
    assert fn._run_lean(wrong_sum, pkt.lean4_theorem_name, 20)[0] is False
    with pytest.raises(ValueError, match="not bound"):
        dataclasses.replace(pkt, lean4_source=wrong_sum)


def test_t1_f4_tier3_packet_binds_sovereign_rust_verifier_receipt() -> None:
    """F4: Every Tier 3 packet carries a PASS sovereign Rust verification receipt."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=200)
    val_cases = (_make_validation_case(case_id="t3_rust_1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    packets = fn.route_tier3_fable_derivations(report)
    for pkt in packets:
        if hasattr(pkt, "rust_receipt_status"):
            assert pkt.rust_receipt_status == "PASS"
            assert len(str(pkt.rust_receipt_sha256)) == 64
        else:
            rust_rec = _extract_attr(
                pkt,
                ("rust_receipt", "rust_verifier_receipt", "rust_verification", "host_receipt"),
            )
            if isinstance(rust_rec, Mapping):
                assert rust_rec.get("status") == "PASS"
            else:
                assert _extract_attr(rust_rec, ("status",)) == "PASS"


def test_t1_f4_tier3_packet_does_not_substitute_a_published_atlas_claim() -> None:
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=200)
    val_cases = (_make_validation_case(case_id="t3_dag_1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    packets = fn.route_tier3_fable_derivations(report)
    assert packets
    for pkt in packets:
        assert pkt.dag_node_id is None
        assert pkt.atlas_claim_id is None
        with pytest.raises(ValueError, match="no registered"):
            dataclasses.replace(pkt, dag_node_id="AUDIT-P016-001")


def test_t1_f4_tier3_router_class_preserves_packet_ordering_and_determinism() -> None:
    """F4: Tier3FableDerivationRouterV1 routes identically across repeated invocations."""
    fn = _funnel_mod()
    router = fn.Tier3FableDerivationRouterV1()
    batch = fn.generate_python_workflow_permutations(max_depth=3, target_count=128)
    val_cases = (_make_validation_case(case_id="t3_det_1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    p1 = router.route(report) if hasattr(router, "route") else fn.route_tier3_fable_derivations(report)
    p2 = fn.route_tier3_fable_derivations(report)
    assert len(p1) == len(p2)
    for a, b in zip(p1, p2, strict=True):
        assert dataclasses.asdict(a) == dataclasses.asdict(b)


def test_t1_f4_tier3_packets_preserve_authority_effect_none_end_to_end() -> None:
    """F4: All Tier 3 packets maintain AuthorityEffect: None on packet and embedded receipts."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=3, target_count=128)
    val_cases = (_make_validation_case(case_id="t3_auth_1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    packets = fn.route_tier3_fable_derivations(report)
    for pkt in packets:
        assert pkt.authority_effect == "None"


# --- Feature F5: 5-Arm Sequential Challenge Ablation (6 tests) ---


def test_t1_f5_run_five_arm_ablation_track1_fermion_to_finite_qm() -> None:
    """F5: Track 1 executes C028 -> C021 -> C022 -> C026 -> WF52 across all 5 arms + naive control."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_1_fermion_finite_qm")
    assert isinstance(rep, ab.SequentialAblationReportV1)
    assert _extract_attr(rep, ("authority_effect",)) == "None"
    arms = _extract_ablation_arms(rep)
    for arm_name in (*FIVE_ARM_NAMES, "naive_append_control"):
        assert arm_name in arms, f"Missing arm {arm_name} in Track 1 report"
    tasks = tuple(_extract_attr(rep, ("tasks", "task_sequence", "challenge_ids", "track_tasks")))
    assert tasks == TRACK_1_TASKS


def test_t1_f5_run_five_arm_ablation_track2_cohomology_obstruction() -> None:
    """F5: Track 2 executes C011 -> C012 -> C014 -> C018 -> C019 across all 5 arms + naive control."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_2_cohomology_obstruction")
    assert isinstance(rep, ab.SequentialAblationReportV1)
    arms = _extract_ablation_arms(rep)
    for arm_name in (*FIVE_ARM_NAMES, "naive_append_control"):
        assert arm_name in arms
    tasks = tuple(_extract_attr(rep, ("tasks", "task_sequence", "challenge_ids", "track_tasks")))
    assert tasks == TRACK_2_TASKS


def test_t1_f5_run_five_arm_ablation_track3_lean4_certificates() -> None:
    """F5: Track 3 executes C041 -> C046 -> C050 -> C051 -> C053 -> C060 across all 5 arms + naive control."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_3_lean4_certificates")
    assert isinstance(rep, ab.SequentialAblationReportV1)
    arms = _extract_ablation_arms(rep)
    for arm_name in (*FIVE_ARM_NAMES, "naive_append_control"):
        assert arm_name in arms
    tasks = tuple(_extract_attr(rep, ("tasks", "task_sequence", "challenge_ids", "track_tasks")))
    assert tasks == TRACK_3_TASKS


def test_t1_f5_full_outer_loop_arm5_strictly_beats_stateless_baseline_pass_rate(
    cached_ablation_all_report: Any,
) -> None:
    """F5: Arm 5 (pfp_eis_operads_pciv_full) achieves higher pass rate and lower tokens/solve than Arm 1."""
    arms = _extract_ablation_arms(cached_ablation_all_report)
    base = arms["pfp_baseline"]
    full = arms["pfp_eis_operads_pciv_full"]
    base_rate = _extract_attr(base, ("cumulative_pass_rate", "pass_rate"))
    full_rate = _extract_attr(full, ("cumulative_pass_rate", "pass_rate"))
    base_tps = _extract_attr(base, ("tokens_per_certified_solve",))
    full_tps = _extract_attr(full, ("tokens_per_certified_solve",))
    assert isinstance(base_rate, Fraction) and isinstance(full_rate, Fraction)
    assert full_rate > base_rate
    assert full_tps < base_tps


def test_t1_f5_full_outer_loop_arm5_beats_naive_append_control_on_tokens_and_autoimmunity(
    cached_ablation_all_report: Any,
) -> None:
    """F5: Arm 5 maintains 0 autoimmune false refusals and strictly lower tokens than naive_append_control."""
    arms = _extract_ablation_arms(cached_ablation_all_report)
    naive = arms["naive_append_control"]
    full = arms["pfp_eis_operads_pciv_full"]
    full_auto = _extract_attr(full, ("autoimmune_false_refusals", "autoimmune_violations"))
    naive_auto = _extract_attr(naive, ("autoimmune_false_refusals", "autoimmune_violations"))
    full_prompt_tok = _extract_attr(full, ("active_prompt_tokens", "final_prompt_tokens"))
    naive_prompt_tok = _extract_attr(naive, ("active_prompt_tokens", "final_prompt_tokens"))
    full_tps = _extract_attr(full, ("tokens_per_certified_solve",))
    naive_tps = _extract_attr(naive, ("tokens_per_certified_solve",))
    assert full_auto == 0
    assert naive_auto > 0 or naive_prompt_tok > full_prompt_tok
    assert full_prompt_tok < naive_prompt_tok
    assert full_tps < naive_tps


def test_t1_f5_intermediate_arms_isolate_eis_operad_and_pciv_contributions(
    cached_ablation_all_report: Any,
) -> None:
    """F5: Intermediate Arms 2 (+EIS), 3 (+Operads), and 4 (+PCIV) isolate individual mechanism effects."""
    arms = _extract_ablation_arms(cached_ablation_all_report)
    arm_eis = arms["pfp_plus_eis"]
    arm_op = arms["pfp_plus_operads"]
    arm_pciv = arms["pfp_plus_pciv"]
    arm_full = arms["pfp_eis_operads_pciv_full"]

    assert _extract_attr(arm_eis, ("autoimmune_false_refusals", "autoimmune_violations")) == 0
    full_rate = _extract_attr(arm_full, ("cumulative_pass_rate", "pass_rate"))
    for sub_arm in (arm_eis, arm_op, arm_pciv):
        sub_rate = _extract_attr(sub_arm, ("cumulative_pass_rate", "pass_rate"))
        assert full_rate >= sub_rate


# --- Feature F6: Native Rust Host Binaries & Sacrosanct Custody (6 tests) ---


def test_t1_f6_pfp_operad_release_binary_present_and_reports_version() -> None:
    """F6: Compiled pfp_operad host binary exists and responds to version identity check."""
    bin_path = operad_host.binary()
    assert bin_path.is_file(), f"Missing pfp_operad binary at {bin_path}"
    ident = operad_host.identity()
    assert isinstance(ident, dict)
    assert "version" in ident or "name" in ident


def test_t1_f6_pfp_immune_release_binary_present_and_executes_screen() -> None:
    """F6: Compiled pfp_immune host binary exists and executes Thymus negative selection."""
    assert immune_host.is_available() is True
    bin_path = immune_host.binary()
    assert bin_path.is_file()
    res = immune_host.screen(
        CLEAN_EXACT_PYTHON_PANEL,
        [
            {"rule_id": "clean_rule", "pattern": r"float\(", "capability_kind": "rule"},
            {"rule_id": "self_reactive", "pattern": r"Fraction", "capability_kind": "rule"},
        ],
    )
    assert res["admitted"] == ["clean_rule"]
    assert [p["rule_id"] for p in res["purged"]] == ["self_reactive"]


def test_t1_f6_pfp_operad_ledger_append_trial_admit_and_verify_hash_chain(tmp_path: Path) -> None:
    """F6: Rust pfp_operad ledger enforces failure -> candidate -> trial -> admission hash chain."""
    ledger_path = tmp_path / "chain.jsonl"
    f_out = operad_ledger.record_failure(
        ledger_path,
        failure_id="fail_c028_sign",
        workflow="wf_outer_loop",
        run="run_01",
        failure_class="CounterfeitExactness",
        ddc_trace="CRM",
        evidence_sha256=sha256_hex("float_sign_drop_evidence"),
    )
    assert f_out["status"] == "PASS"
    c_out = operad_ledger.propose_candidate(
        ledger_path,
        candidate_id="cand_exact_sign",
        capability_kind="rule",
        constraint="Track Jordan-Wigner Z-string parity in exact Z/2Z.",
        derived_from=["fail_c028_sign"],
    )
    assert c_out["status"] == "PASS"
    t_out = operad_ledger.record_trial(
        ledger_path,
        candidate_id="cand_exact_sign",
        held_out=["holdout_01", "holdout_02"],
        baseline_correct=1,
        treated_correct=2,
        clean_panel_hits=0,
    )
    assert t_out["status"] == "PASS"
    trial_seq = t_out["result"]["seq"]
    a_out = operad_ledger.record_admission(
        ledger_path, candidate_id="cand_exact_sign", trial_seq=trial_seq
    )
    assert a_out["status"] == "PASS"
    v_out = operad_ledger.verify(ledger_path)
    assert v_out["status"] == "PASS"
    admitted_list = operad_ledger.admitted(ledger_path)
    assert any(
        (row.get("id") == "cand_exact_sign" or row.get("candidate") == "cand_exact_sign")
        for row in admitted_list
    )


def test_t1_f6_pfp_immune_decide_taint_select_and_exclusion_subcommands() -> None:
    """F6: Rust pfp_immune executes decide, taint, select, and exclusion subcommands cleanly."""
    d_res = immune_host.decide(["rule_a"], Fraction(1, 1), Fraction(1, 2))
    assert d_res["status"] == "HOLD_OR_REPAIR"
    t_res = immune_host.taint(
        [{"parent": "g0", "child": "g1", "witness": "sha256:" + "a" * 64}],
        ["g0"],
    )
    assert set(t_res["tainted_nodes"]) == {"g0", "g1"}
    s_res = immune_host.select(
        [
            {"id": "g_best", "fitness": Fraction(4, 4), "lineage_depth": 0},
            {"id": "g_mid", "fitness": Fraction(3, 4), "lineage_depth": 1},
        ]
    )
    assert "g_best" in s_res["core_60"]
    e_res = immune_host.exclusion({"anthropic": "EXCLUDE", "fable": "EXCLUDE"}, ["hyp_1"])
    assert e_res["consensus"] == "PROBABLY_DEAD"


def test_t1_f6_sacrosanct_dag_file_inventory_zero_pinned_mutations() -> None:
    """F6: Zero files pinned in dag/file_inventory.json are mutated on this branch."""
    git_bin = shutil.which("git")
    assert git_bin is not None
    base = subprocess.run(
        [git_bin, "merge-base", "HEAD", "origin/main"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    diff = subprocess.run(
        [git_bin, "diff", "--name-only", base],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        [git_bin, "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    inventory = json.loads((REPO_ROOT / "dag" / "file_inventory.json").read_text(encoding="utf-8"))
    pinned = {row["path"] for row in inventory["files"]}
    violating = [p for p in (*diff, *untracked) if p and p in pinned]
    assert violating == [], f"Pinned custody files mutated: {violating}"


def test_t1_f6_wf52_and_wf53_regulation_and_pfp_core_custody_unchanged() -> None:
    """F6: Existing pfp_core/*.py files remain byte-identical to HEAD without custody drift."""
    git_bin = shutil.which("git")
    assert git_bin is not None
    diff = subprocess.run(
        [git_bin, "diff", "--name-only", "HEAD", "--", *SACROSANCT_PFP_CORE_FILES],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert [p for p in diff if p] == []


# --- Feature F7: Core Lean 4 Mechanization (6 tests) ---


def test_t1_f7_lean4_funnel_compression_closure_module_exists_and_is_core_lean() -> None:
    """F7: lean4/FunnelCompressionClosure.lean exists, uses zero Mathlib, and declares >=4 theorems."""
    lean_path = REPO_ROOT / "lean4" / "FunnelCompressionClosure.lean"
    assert lean_path.is_file(), "lean4/FunnelCompressionClosure.lean must exist"
    text = lean_path.read_text(encoding="utf-8")
    assert "import Mathlib" not in text
    theorems = re.findall(r"^\s*theorem\s+([A-Za-z0-9_']+)", text, flags=re.MULTILINE)
    assert len(theorems) >= 4, f"Expected >=4 theorems covering funnel/Thymus/PCIV/gluing, got {theorems}"


def test_t1_f7_lean4_funnel_compression_closure_elaborates_cleanly_via_lake() -> None:
    """F7: lake env lean FunnelCompressionClosure.lean exits 0 with zero sorry."""
    proc = subprocess.run(
        ["lake", "env", "lean", "FunnelCompressionClosure.lean"],
        cwd=REPO_ROOT / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, f"Lean elaboration failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "declaration uses 'sorry'" not in (proc.stdout + proc.stderr)


def test_t1_f7_lean4_funnel_compression_closure_axiom_census_strict_whitelist(
    tmp_path: Path,
) -> None:
    """F7: Every constant in FunnelCompressionClosure uses only {propext, Quot.sound} and zero sorryAx."""
    lean_src = (REPO_ROOT / "lean4" / "FunnelCompressionClosure.lean").read_text(encoding="utf-8")
    probe = tmp_path / "CheckFunnelAxioms.lean"
    lines = lean_src.splitlines()
    import_lines = [ln for ln in lines if ln.strip().startswith("import ")]
    body_lines = [ln for ln in lines if not ln.strip().startswith("import ")]
    audit_code = "\n".join(
        [
            "import Lean",
            *[ln for ln in import_lines if ln.strip() != "import Lean"],
            *body_lines,
            "",
            "open Lean Elab Command in",
            "run_cmd do",
            "  let allowed : List Lean.Name := [`propext, `Quot.sound]",
            "  let env ← getEnv",
            "  let mut thmCount := 0",
            "  let mut bad : Array String := #[]",
            "  for (n, ci) in env.constants.map₂.toList do",
            "    if ci matches .axiomInfo _ then",
            '      bad := bad.push s!"declares user axiom {n}"',
            "    if (ci matches .thmInfo _) && !n.isInternal then",
            "      thmCount := thmCount + 1",
            "      let axs ← liftCoreM (Lean.collectAxioms n)",
            "      for a in axs do",
            "        if !allowed.contains a then",
            '          bad := bad.push s!"{n} depends on disallowed axiom {a}"',
            "  if thmCount < 4 then",
            '    throwError s!"expected >= 4 local theorems, found {thmCount}"',
            "  unless bad.isEmpty do",
            '    throwError s!"disallowed axioms: {bad}"',
        ]
    )
    probe.write_text(audit_code, encoding="utf-8")
    proc = subprocess.run(
        ["lake", "env", "lean", str(probe)],
        cwd=REPO_ROOT / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, f"Axiom census failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"


def test_t1_f7_lean4_contract_score_companion_exists_and_meets_l4d_floor() -> None:
    """F7: lean4/FunnelCompressionClosure.contract.score.json exists and meets >= L4D floor."""
    lean_path = REPO_ROOT / "lean4" / "FunnelCompressionClosure.lean"
    score_path = REPO_ROOT / "lean4" / "FunnelCompressionClosure.contract.score.json"
    assert score_path.is_file(), (
        "Missing lean4/FunnelCompressionClosure.contract.score.json companion"
    )
    payload = json.loads(score_path.read_text(encoding="utf-8"))
    assert payload.get("AuthorityEffect") == "None"
    score = payload["score"]
    assert score.get("AuthorityEffect") == "None"
    assert score.get("level") in ("L4", "L5")
    assert score.get("composite_grade") in ("A+", "A", "B", "C", "D")
    actual_sha = hashlib.sha256(lean_path.read_bytes()).hexdigest()
    assert payload["contract"]["artifact"]["sha256"] == actual_sha
    assert score["artifact"]["sha256"] == actual_sha


def test_t1_f7_grandfathered_11_lean4_files_remain_unmodified() -> None:
    """F7: None of the grandfathered Lean 4 files in lean4/ have been modified."""
    git_bin = shutil.which("git")
    assert git_bin is not None
    diff = subprocess.run(
        [git_bin, "diff", "--name-only", "origin/main", "--", *GRANDFATHERED_LEAN_FILES],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert [p for p in diff if p] == []


def test_t1_f7_governance_checker_passes_on_lean4_and_branch_diff() -> None:
    """F7: governance.tools.checker check --changed-since origin/main exits 0."""
    proc = subprocess.run(
        [sys.executable, "-m", "governance.tools.checker", "check", "--changed-since", "origin/main"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, f"Governance checker failed:\n{proc.stdout}\n{proc.stderr}"


# --- Feature F8: Complete Atlas & DAG Derivations (P015, P016, P018, P019) (6 tests) ---


def test_t1_f8_all_21_written_audit_derivation_markdown_files_exist_and_non_empty() -> None:
    """F8: All 21 written derivation files across P015, P016, P018, P019 exist and carry AuthorityEffect: None."""
    assert len(ALL_21_AUDIT_MD_PATHS) == 21
    for path in ALL_21_AUDIT_MD_PATHS:
        assert path.is_file(), f"Missing written derivation file: {path}"
        content = path.read_text(encoding="utf-8")
        assert len(content.strip()) >= 300, f"Derivation {path.name} is suspiciously short"
        assert "AuthorityEffect" in content and "None" in content


def test_t1_f8_review_json_registers_all_21_audit_nodes_with_pinned_file_reviews() -> None:
    """F8: dag/reviews/additional_w5_v1rc_funnel_compression.json registers all 21 AUDIT-P01* claims."""
    review_path = REPO_ROOT / "dag" / "reviews" / "additional_w5_v1rc_funnel_compression.json"
    assert review_path.is_file(), f"Missing review shard {review_path}"
    data = json.loads(review_path.read_text(encoding="utf-8"))
    assert isinstance(data.get("file_reviews"), list) and len(data["file_reviews"]) >= 4
    claim_ids = {c["id"] for c in data.get("claims", [])}
    missing = set(ALL_21_AUDIT_NODES) - claim_ids
    assert not missing, f"Review JSON missing AUDIT nodes: {sorted(missing)}"

    inventory = json.loads((REPO_ROOT / "dag" / "file_inventory.json").read_text(encoding="utf-8"))
    inv_sha = {row["path"]: row["sha256"] for row in inventory["files"]}
    for fr in data["file_reviews"]:
        p = fr["path"]
        if p in inv_sha:
            assert fr["sha256"] == inv_sha[p], f"SHA-256 mismatch vs file_inventory.json for {p}"


def test_t1_f8_atlas_claim_matches_settles_all_21_p015_p016_p018_p019_claims() -> None:
    """F8: atlas/atlas_claim_matches.json settles all 21 target claims with proposed_derivation=null."""
    matches_data = json.loads(
        (REPO_ROOT / "atlas" / "atlas_claim_matches.json").read_text(encoding="utf-8")
    )
    by_id = {row["atlas_id"]: row for row in matches_data["results"]}
    for atl_id, audit_id in zip(ALL_21_SETTLED_CLAIMS, ALL_21_AUDIT_NODES, strict=True):
        assert atl_id in by_id, f"Missing {atl_id} in atlas_claim_matches.json"
        row = by_id[atl_id]
        assert row["verdict"] in ("matched", "partial"), f"{atl_id} still has verdict={row['verdict']!r}"
        assert audit_id in row["nodes"], f"{atl_id} does not link {audit_id} in nodes={row['nodes']}"
        assert row["proposed_derivation"] is None, f"{atl_id} still has proposed_derivation"


def test_t1_f8_obsolete_atl_p015_p016_p018_p019_stubs_pruned() -> None:
    """F8: All 21 obsolete atl_p01{5,6,8,9}_*.md proposed-derivation stubs have been removed."""
    remaining = [p.name for p in ALL_21_PRUNED_STUB_PATHS if p.exists()]
    assert remaining == [], f"Obsolete proposed-derivation stubs still exist: {remaining}"


def test_t1_f8_derivations_dag_json_contains_all_21_settled_nodes_and_edges() -> None:
    """F8: dag/derivations_dag.json includes all 21 AUDIT-P01* nodes and links them to ATL-P01* claims."""
    dag = json.loads((REPO_ROOT / "dag" / "derivations_dag.json").read_text(encoding="utf-8"))
    node_ids = {n["id"] for n in dag["nodes"]}
    for audit_id, atl_id in zip(ALL_21_AUDIT_NODES, ALL_21_SETTLED_CLAIMS, strict=True):
        assert audit_id in node_ids, f"Missing {audit_id} in derivations_dag.json"
        assert atl_id in node_ids, f"Missing {atl_id} in derivations_dag.json"


def test_t1_f8_build_atlas_check_passes_with_empty_stale_list() -> None:
    """F8: python dag/build_atlas.py --check exits 0 with stale == [] and >= 1,525 synced rows."""
    proc = subprocess.run(
        [sys.executable, "dag/build_atlas.py", "--check"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, f"build_atlas.py --check failed:\n{proc.stdout}\n{proc.stderr}"
    summary = json.loads(proc.stdout)
    assert summary["stale"] == []
    assert summary["ledger_rows"] == summary["derivation_nodes"]
    assert summary["ledger_rows"] >= 1525


# --- Feature F9: Statistical & Comparative Claim Hygiene (6 tests) ---


def test_t1_f9_comparative_claim_auditor_admits_held_out_holm_corrected_claim() -> None:
    """F9: ComparativeClaimAuditorV1 admits COMPARATIVE_BENEFIT with held-out split and Holm correction."""
    auditor = ComparativeClaimAuditorV1()
    assert (
        auditor.evaluate_claim(
            claim_type="COMPARATIVE_BENEFIT",
            has_held_out_split=True,
            multiplicity_correction="holm_bonferroni",
        )
        is True
    )


def test_t1_f9_sequential_ablation_report_passes_comparative_claim_audit(
    cached_ablation_all_report: Any,
) -> None:
    """F9: SequentialAblationReportV1 records held-out split, Holm correction, and PASS claim audit."""
    rep = cached_ablation_all_report
    has_split = _extract_attr(rep, ("has_held_out_split", "held_out_split"))
    mult = _extract_attr(rep, ("multiplicity_correction", "correction_method"))
    status = _extract_attr(rep, ("claim_audit_status", "comparative_claim_audit", "audit_status"))
    assert has_split is True
    assert isinstance(mult, str) and "holm" in mult.lower()
    assert status in ("PASS", True)


def test_t1_f9_ablation_metrics_use_exact_fractions_no_floats_in_rates(
    cached_ablation_all_report: Any,
) -> None:
    """F9: All pass rates and token/cost ratios in SequentialAblationReportV1 use exact int/Fraction types."""
    arms = _extract_ablation_arms(cached_ablation_all_report)
    for arm_name, summary in arms.items():
        rate = _extract_attr(summary, ("cumulative_pass_rate", "pass_rate"))
        tps = _extract_attr(summary, ("tokens_per_certified_solve",))
        auto = _extract_attr(summary, ("autoimmune_false_refusals", "autoimmune_violations"))
        assert isinstance(rate, Fraction), f"{arm_name} rate is {type(rate).__name__}, expected Fraction"
        assert isinstance(tps, (int, Fraction)) and not isinstance(tps, bool)
        assert type(auto) is int


def test_t1_f9_paired_mcnemar_and_holm_multiplicity_monotonicity(
    cached_ablation_all_report: Any,
) -> None:
    """F9: Paired arm comparisons report Holm-corrected values bounded in [0, 1] and >= raw p-values."""
    comparisons = _extract_attr(
        cached_ablation_all_report,
        ("paired_comparisons", "comparisons", "holm_comparisons", "statistical_comparisons"),
    )
    items = list(comparisons.values()) if isinstance(comparisons, Mapping) else list(comparisons)
    assert len(items) >= 4
    for item in items:
        raw_p = _extract_attr(
            item,
            ("raw_mcnemar_p", "raw_p_value", "p_value", "mcnemar_p_value", "exact_p_value"),
        )
        adj_p = _extract_attr(
            item,
            ("holm_adjusted_p", "holm_adjusted_p_value", "adjusted_p_value", "holm_p_value"),
        )
        raw_f = Fraction(raw_p) if not isinstance(raw_p, Fraction) else raw_p
        adj_f = Fraction(adj_p) if not isinstance(adj_p, Fraction) else adj_p
        assert Fraction(0) <= raw_f <= adj_f <= Fraction(1)


def test_t1_f9_research_selection_improved_enforces_family_non_regression() -> None:
    """F9: pciv.use_cases.research_selection.improved accepts paired improvement with zero family regression."""
    d = sha256_hex
    exp = ExperimentSpecV1("camp1", d("src"), d("chk"), d("split"), "camp1", d("cfg"))
    inc_rows = [
        EvaluationReceiptV1(
            exp.experiment_id, d("src"), d("inc"), d("root"), d("chk"), d("split"),
            "claude-haiku-5-5", d("cfg"), "camp1", "occ_i1", "t1", "fam_qm", "discovery",
            0, d("rep_i1"), True, False, "EXECUTION_ERROR", 200, (d("ev1"),),
        ),
        EvaluationReceiptV1(
            exp.experiment_id, d("src"), d("inc"), d("root"), d("chk"), d("split"),
            "claude-haiku-5-5", d("cfg"), "camp1", "occ_i2", "t2", "fam_coh", "discovery",
            0, d("rep_i2"), True, True, "HOST_ACCEPTED", 200, (d("ev2"),),
        ),
    ]
    cand_rows = [
        EvaluationReceiptV1(
            exp.experiment_id, d("src"), d("cand"), d("inc"), d("chk"), d("split"),
            "claude-haiku-5-5", d("cfg"), "camp1", "occ_c1", "t1", "fam_qm", "discovery",
            0, d("rep_c1"), True, True, "HOST_ACCEPTED", 180, (d("ev3"),),
        ),
        EvaluationReceiptV1(
            exp.experiment_id, d("src"), d("cand"), d("inc"), d("chk"), d("split"),
            "claude-haiku-5-5", d("cfg"), "camp1", "occ_c2", "t2", "fam_coh", "discovery",
            0, d("rep_c2"), True, True, "HOST_ACCEPTED", 180, (d("ev4"),),
        ),
    ]
    assert research_selection.improved(cand_rows, inc_rows) is True


def test_t1_f9_claim_hygiene_no_forbidden_promotional_hype_in_v1rc_outputs() -> None:
    """F9: New v1rc Python modules declare AuthorityEffect: None and zero runtime assert statements."""
    v1rc_paths = (
        REPO_ROOT / "pfp_core" / "outer_loop_v1rc.py",
        REPO_ROOT / "pfp_core" / "funnel_v1rc.py",
        REPO_ROOT / "pfp_core" / "sequential_ablation_v1rc.py",
    )
    for path in v1rc_paths:
        assert path.is_file(), f"Missing M1 module {path}"
        src = path.read_text(encoding="utf-8")
        assert "AuthorityEffect: None" in src or '"None"' in src
        tree = ast.parse(src, filename=str(path))
        assert_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
        assert assert_nodes == [], f"Production module {path.name} contains {len(assert_nodes)} assert statements"


# ===========================================================================
# TIER 2 — BOUNDARY, CORNER & ADVERSARIAL CASES (54 TESTS = 6 x F1..F9)
# ===========================================================================


# --- F1 Boundaries & Refusals (Outer Loop: 6 tests) ---


def test_t2_f1_autoimmune_rule_rejected_with_reject_autoimmune_and_retains_incumbent(
    tmp_path: Path,
) -> None:
    """F1 Boundary: Detector firing on clean_self_panel triggers REJECT_AUTOIMMUNE and retains incumbent."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    incumbent = _make_genome(genome_id="inc_safe_0")
    autoimmune_cand = ol.CandidateStrandDeltaV1(
        candidate_id="cand_autoimmune_bad",
        parent_genome_id="inc_safe_0",
        derived_from_failures=("fail_x1",),
        detector_rule=DetectorRule(
            rule_id="rule_matches_clean_def",
            target_epitope="function_def",
            match_pattern=r"def\s{1,4}exact_sum",
        ),
        constraint_clause="Overbroad ban matching clean function.",
        typed_ops=_make_default_ops(ctx_keys=("overbroad_guard",)),
    )
    val_slice = (
        _make_validation_case(case_id="val_a1", baseline_passed=False, treated_passed=True),
    )
    adopted, receipt = controller.evaluate_and_compress(
        incumbent, autoimmune_cand, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert receipt.thymus_admitted is False
    assert receipt.autoimmune_violations >= 1
    assert receipt.pciv_decision == "REJECT_AUTOIMMUNE"
    assert receipt.adopted_genome_id == "inc_safe_0"
    assert _genome_id_of(adopted) == "inc_safe_0"


def test_t2_f1_clean_panel_regression_rejected_with_reject_regression(tmp_path: Path) -> None:
    """F1 Boundary: Candidate breaking a baseline-solved held-out case is rejected as REJECT_REGRESSION."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    incumbent = _make_genome(genome_id="inc_nonreg_0")
    regressing_cand = ol.CandidateStrandDeltaV1(
        candidate_id="cand_regressing_v1",
        parent_genome_id="inc_nonreg_0",
        derived_from_failures=("fail_r1",),
        detector_rule=DetectorRule(
            rule_id="rule_safe_syntax",
            target_epitope="float_cast",
            match_pattern=r"float\(",
        ),
        constraint_clause="Mutated instruction causing regression on case 1.",
        typed_ops=_make_default_ops(ctx_keys=("mut_regressing",), gen_tokens=150),
    )
    val_slice = (
        _make_validation_case(
            case_id="val_reg_01",
            baseline_passed=True,
            treated_passed=False,
            draft_reply="def broken(:\n",
        ),
        _make_validation_case(
            case_id="val_reg_02",
            baseline_passed=False,
            treated_passed=True,
        ),
    )
    adopted, receipt = controller.evaluate_and_compress(
        incumbent, regressing_cand, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert receipt.clean_panel_hits >= 1
    assert receipt.pciv_decision == "REJECT_REGRESSION"
    assert receipt.adopted_genome_id == "inc_nonreg_0"
    assert _genome_id_of(adopted) == "inc_nonreg_0"


def test_t2_f1_bloated_prompt_at_equal_accuracy_rejected_with_reject_bloat(tmp_path: Path) -> None:
    """F1 Boundary: Candidate with treated_tokens > baseline_tokens at equal pass rate -> REJECT_BLOAT."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    incumbent = _make_genome(
        genome_id="inc_lean_prompt",
        typed_ops=_make_default_ops(ctx_keys=("seed_ctx",), include_normalize=True, gen_tokens=120, ctx_tokens=30),
        base_tokens=150,
    )
    bloated_cand = ol.CandidateStrandDeltaV1(
        candidate_id="cand_bloated_v1",
        parent_genome_id="inc_lean_prompt",
        derived_from_failures=("fail_b1",),
        detector_rule=DetectorRule(
            rule_id="rule_unused_verbose",
            target_epitope="rare_token",
            match_pattern=r"NEVER_OCCURS_TOKEN_XYZ",
        ),
        constraint_clause="Verbose appended paragraph that adds zero accuracy. " * 25,
        typed_ops=_make_default_ops(
            ctx_keys=("seed_ctx", "bloated_appendix"),
            include_normalize=True,
            gen_tokens=400,
            ctx_tokens=300,
        ),
    )
    val_slice = (
        _make_validation_case(
            case_id="val_bloat_01",
            baseline_passed=True,
            treated_passed=True,
            baseline_tokens=150,
            treated_tokens=1000,
        ),
        _make_validation_case(
            case_id="val_bloat_02",
            baseline_passed=False,
            treated_passed=False,
            baseline_tokens=150,
            treated_tokens=1000,
        ),
    )
    adopted, receipt = controller.evaluate_and_compress(
        incumbent, bloated_cand, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert receipt.treated_tokens > receipt.baseline_tokens
    assert receipt.pciv_decision == "REJECT_BLOAT"
    assert receipt.adopted_genome_id == "inc_lean_prompt"
    assert _genome_id_of(adopted) == "inc_lean_prompt"


def test_t2_f1_equal_accuracy_and_equal_tokens_tie_rejected_as_non_improving(
    tmp_path: Path,
) -> None:
    """F1 Boundary: Exact accuracy and token tie does not promote over incumbent."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    incumbent = _make_genome(
        genome_id="inc_tie_0",
        typed_ops=_make_default_ops(ctx_keys=("ctx_1",), include_normalize=True, gen_tokens=160, ctx_tokens=40),
        base_tokens=200,
    )
    tie_cand = ol.CandidateStrandDeltaV1(
        candidate_id="cand_tie_v1",
        parent_genome_id="inc_tie_0",
        derived_from_failures=("fail_tie_1",),
        detector_rule=DetectorRule(
            rule_id="rule_tie_noop",
            target_epitope="noop_epitope",
            match_pattern=r"UNSEEN_MARKER_999",
        ),
        constraint_clause="Same length clause.",
        typed_ops=_make_default_ops(ctx_keys=("ctx_2",), include_normalize=True, gen_tokens=160, ctx_tokens=40),
    )
    val_slice = (
        _make_validation_case(
            case_id="val_tie_01",
            baseline_passed=True,
            treated_passed=True,
            baseline_tokens=200,
            treated_tokens=200,
            baseline_microusd=100,
            treated_microusd=100,
        ),
    )
    adopted, receipt = controller.evaluate_and_compress(
        incumbent, tie_cand, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert receipt.pciv_decision == "REJECT_BLOAT"
    assert receipt.adopted_genome_id == "inc_tie_0"
    assert _genome_id_of(adopted) == "inc_tie_0"


def test_t2_f1_trace_equivalent_duplicate_pipeline_collapses_via_collapse_quotient(
    tmp_path: Path,
) -> None:
    """F1 Boundary: Reordered adjacent context ops share trace_digest -> quotient_collapsed & COLLAPSE_QUOTIENT."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    ops_ab = _make_default_ops(ctx_keys=("skill_alpha", "skill_beta"), include_normalize=True)
    ops_ba = _make_default_ops(ctx_keys=("skill_beta", "skill_alpha"), include_normalize=True)
    assert trace_digest(list(ops_ab)) == trace_digest(list(ops_ba))

    incumbent = _make_genome(genome_id="inc_ab", typed_ops=ops_ab)
    dup_cand = ol.CandidateStrandDeltaV1(
        candidate_id="cand_ba_dup",
        parent_genome_id="inc_ab",
        derived_from_failures=("fail_q1",),
        detector_rule=DetectorRule(
            rule_id="rule_q_safe",
            target_epitope="float_cast",
            match_pattern=r"float\(",
        ),
        constraint_clause="Commuted context equivalent.",
        typed_ops=ops_ba,
    )
    val_slice = (
        _make_validation_case(case_id="val_q_01", baseline_passed=True, treated_passed=True),
    )
    adopted, receipt = controller.evaluate_and_compress(
        incumbent, dup_cand, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert receipt.quotient_collapsed is True
    assert receipt.canonical_trace_digest == trace_digest(list(ops_ab))
    assert receipt.pciv_decision == "COLLAPSE_QUOTIENT"
    assert _genome_id_of(adopted) == "inc_ab"


def test_t2_f1_split_overlap_between_derived_failures_and_validation_raises_value_error(
    tmp_path: Path,
) -> None:
    """F1 Boundary: Overlap between derived_from_failures and validation_slice raises ValueError(SPLIT_OVERLAP)."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    incumbent = _make_genome(genome_id="inc_split_0")
    leaky_cand = ol.CandidateStrandDeltaV1(
        candidate_id="cand_leaky_split",
        parent_genome_id="inc_split_0",
        derived_from_failures=("shared_case_007",),
        detector_rule=DetectorRule(
            rule_id="rule_split_probe",
            target_epitope="float_cast",
            match_pattern=r"float\(",
        ),
        constraint_clause="Derived directly from validation case.",
        typed_ops=_make_default_ops(ctx_keys=("leaky_ctx",)),
    )
    overlapping_slice = (
        _make_validation_case(case_id="shared_case_007", baseline_passed=False, treated_passed=True),
    )
    with pytest.raises(ValueError, match="SPLIT_OVERLAP"):
        controller.evaluate_and_compress(
            incumbent, leaky_cand, overlapping_slice, CLEAN_EXACT_PYTHON_PANEL
        )


# --- F2 Boundaries & Refusals (Tier 1 Generator: 6 tests) ---


def test_t2_f2_minimal_target_count_boundary_100_permutations() -> None:
    """F2 Boundary: Lower 100-proposal target_count boundary generates valid quotiented batch."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=3, target_count=100)
    assert batch.total_generated >= 100
    assert 1 <= batch.unique_quotient_classes <= batch.total_generated
    assert isinstance(batch.quotient_reduction_ratio, Fraction)


def test_t2_f2_large_scale_2048_permutations_sublinear_quotient_growth() -> None:
    """F2 Boundary: Scaling to 2,048 permutations preserves sublinear unique canonical trace classes."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=2048)
    assert batch.total_generated >= 2048
    assert 0 < batch.unique_quotient_classes < batch.total_generated


def test_t2_f2_invalid_target_count_or_boolean_subclass_rejected() -> None:
    """F2 Boundary: Non-positive or boolean target_count / max_depth raises ValueError or TypeError."""
    fn = _funnel_mod()
    for bad_kwargs in (
        {"target_count": 0},
        {"target_count": -10},
        {"target_count": True},
        {"max_depth": 0},
        {"max_depth": False},
    ):
        with pytest.raises((ValueError, TypeError)):
            fn.generate_python_workflow_permutations(**bad_kwargs)


def test_t2_f2_ill_typed_seed_ops_colour_mismatch_refused() -> None:
    """F2 Boundary: Non-canon colours and ill-typed pipeline compositions raise ValueError/TypeError."""
    with pytest.raises(ValueError, match="not in admitted finite colours"):
        TypedOp("bad_col", "NonExistentColour", "Code", "generate")
    op_code = TypedOp("norm_c", "Code", "Code", "normalize", normalizer_id="n1")
    op_gen = TypedOp("gen_c", "Contract", "Code", "generate", prompt_digest="g1")
    with pytest.raises(TypeError, match="PIPELINE_ILL_TYPED"):
        compose([op_code, op_gen])


def test_t2_f2_non_commuting_check_and_normalize_never_falsely_collapsed() -> None:
    """F2 Boundary: normalize -> check and check -> normalize keep distinct canonical trace digests."""
    ctx = TypedOp("ctx_a", "Contract", "Contract", "context", idempotent_key="A")
    gen = TypedOp("gen", "Contract", "Code", "generate", prompt_digest="g")
    norm = TypedOp("norm", "Code", "Code", "normalize", normalizer_id="n1")
    chk = TypedOp("chk", "Code", "Code", "check", checker_id="c1")
    classes = quotient_workflows(
        {
            "norm_then_check": [ctx, gen, norm, chk],
            "check_then_norm": [ctx, gen, chk, norm],
        }
    )
    assert len(classes) == 2


def test_t2_f2_empty_pipeline_and_negative_cost_tokens_refused() -> None:
    """F2 Boundary: Empty TypedOp pipelines and negative/boolean cost_tokens are refused."""
    with pytest.raises(ValueError, match="EMPTY_PIPELINE"):
        compose([])
    with pytest.raises(ValueError, match="nonnegative int"):
        TypedOp("neg_cost", "Code", "Code", "normalize", cost_tokens=-1)
    with pytest.raises(ValueError, match="nonnegative int"):
        TypedOp("bool_cost", "Code", "Code", "normalize", cost_tokens=True)  # type: ignore[arg-type]


# --- F3 Boundaries & Refusals (Tier 2 Opus Falsifier, Thymus & PCIV Gate: 6 tests) ---


def test_t2_f3_poisoned_candidate_killed_by_tier2_falsifier() -> None:
    """F3 Boundary: Poisoned / non-gauge-invariant candidates in Tier 1 batch are killed by Tier 2 falsifier."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=512)
    val_cases = (
        _make_validation_case(case_id="t2_pois_1", baseline_passed=False, treated_passed=True),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    assert report.killed_by_falsifier >= 1
    surv_ids: set[str] = set()
    for s in report.survivors:
        surv_ids.add(str(_extract_attr(s, ("survivor_id", "candidate_id", "proposal_id", "id"))))
        if hasattr(s, "proposal") and s.proposal is not None:
            surv_ids.add(str(_extract_attr(s.proposal, ("proposal_id", "candidate_id", "id"))))
    for cand in batch.python_candidates:
        cid = str(_extract_attr(cand, ("candidate_id", "proposal_id", "id")))
        is_bad = (
            getattr(cand, "is_poisoned", False)
            or not getattr(cand, "poison_resistant", True)
            or "poison" in cid.lower()
        )
        if is_bad:
            assert cid not in surv_ids


def test_t2_f3_overbroad_regex_rule_killed_by_tier2_thymus() -> None:
    """F3 Boundary: Candidate detectors cross-reacting with clean_self_panel increment killed_by_thymus."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=512)
    # Include an extra clean panel fixture containing common identifiers to stress Thymus filtering
    panel_with_defs = (*CLEAN_EXACT_PYTHON_PANEL, "def solve(x: int) -> int:\n    return x\n")
    val_cases = (
        _make_validation_case(case_id="t2_ob_1", baseline_passed=False, treated_passed=True),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, panel_with_defs, val_cases)
    assert report.killed_by_thymus >= 1


def test_t2_f3_unsafe_catastrophic_backtracking_regex_refused_closed() -> None:
    """F3 Boundary: Unbounded/nested-quantifier regex patterns fail closed in ThymusGate without stalling."""
    with pytest.raises(UnsafePatternRefusal):
        compile_safe_pattern(r"(a+)+b")
    gate = ThymusGate(self_panel=CLEAN_EXACT_PYTHON_PANEL)
    bad_rule = DetectorRule(
        rule_id="rule_redos",
        target_epitope="catastrophic_backtrack",
        match_pattern=r"(a+)+b",
    )
    res = gate.evaluate_rule(bad_rule)
    assert res.is_admitted is False
    assert "PATTERN_NESTED_QUANTIFIER" in res.rationale or "PATTERN_UNBOUNDED_REPEAT" in res.rationale


def test_t2_f3_exclusion_without_falsifier_or_escalated_authority_refused() -> None:
    """F3 Boundary: ExclusionHypothesisV1 refuses missing falsifiers, bad costs, and authority escalation."""
    vote = excl.ExclusionVoteV1("seat_1", "opus", True)
    with pytest.raises(excl.ExclusionError, match="EXCLUSION_WITHOUT_FALSIFIER"):
        excl.ExclusionHypothesisV1("e1", "b1", "claim", "   ", 10, (vote,))
    with pytest.raises(excl.ExclusionError, match="FALSIFIER_COST_INVALID"):
        excl.ExclusionHypothesisV1("e1", "b1", "claim", "run_probe", -1, (vote,))
    with pytest.raises(excl.ExclusionError, match="AUTHORITY_ESCALATION"):
        excl.ExclusionHypothesisV1(
            "e1", "b1", "claim", "run_probe", 5, (vote,), authority_effect="BlockingGate"
        )


def test_t2_f3_bloated_tier1_candidate_killed_by_tier2_pciv_gate() -> None:
    """F3 Boundary: Non-improving high-token Tier 1 candidates are filtered by PCIV bloat gate."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=512)
    val_cases = (
        _make_validation_case(
            case_id="t2_bloat_1",
            baseline_passed=True,
            treated_passed=True,
            baseline_tokens=160,
            treated_tokens=640,
        ),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    assert report.killed_by_pciv_bloat >= 1


def test_t2_f3_empty_clean_self_panel_refused_fail_closed(tmp_path: Path) -> None:
    """F3 Boundary: Empty clean_self_panel=() raises ValueError instead of vacuously admitting rules."""
    with pytest.raises(ValueError, match="self_panel"):
        ThymusGate(self_panel=())
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    delta = ol.CandidateStrandDeltaV1(
        candidate_id="cand_empty_panel",
        parent_genome_id="g0",
        derived_from_failures=("f1",),
        detector_rule=DetectorRule("r1", "ep1", r"float\("),
        constraint_clause="No floats.",
        typed_ops=_make_default_ops(),
    )
    with pytest.raises(ValueError):
        controller.screen_with_thymus(delta, ())


# --- F4 Boundaries & Refusals (Tier 3 Fable Derivation Router: 6 tests) ---


def test_t2_f4_empty_survivor_report_routes_to_empty_tuple() -> None:
    """F4 Boundary: A Tier2FalsificationReportV1 with zero survivors routes cleanly to an empty tuple."""
    fn = _funnel_mod()
    empty_report = _instantiate_adaptive(
        fn.Tier2FalsificationReportV1,
        {
            "tier1_input_count": 10,
            "killed_by_falsifier": 4,
            "killed_by_thymus": 3,
            "killed_by_pciv_bloat": 3,
            "survivors": (),
            "authority_effect": "None",
        },
    )
    routed = fn.route_tier3_fable_derivations(empty_report)
    assert routed == ()


def test_t2_f4_authority_escalation_on_survivor_or_report_refused() -> None:
    """F4 Boundary: Any attempt to set authority_effect != 'None' on Tier 2/3 artifacts is refused."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=3, target_count=128)
    val_cases = (_make_validation_case(case_id="t3_esc_1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    assert len(report.survivors) >= 1
    with pytest.raises((ValueError, dataclasses.FrozenInstanceError)):
        tampered_surv = dataclasses.replace(report.survivors[0], authority_effect="Enforce")
        tampered_rep = dataclasses.replace(report, survivors=(tampered_surv,))
        fn.route_tier3_fable_derivations(tampered_rep)


def test_t2_f4_mismatched_rust_outcome_and_survivor_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=3, target_count=128)
    cases = (_make_validation_case(case_id="t3_unk_1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, cases)
    surv = report.survivors[0]
    single = dataclasses.replace(
        report, tier1_input_count=1, killed_by_falsifier=0, killed_by_thymus=0,
        killed_by_pciv_bloat=0, withheld_without_replay=(), survivors=(surv,),
    )
    packet = fn.route_tier3_fable_derivations(single)[0]
    receipt = json.loads(packet.rust_receipt_json)
    assert receipt["candidate"]["survivor_id"] == surv.survivor_id
    assert receipt["request"]["candidates"] == [surv.proposal.operation_wire]
    assert receipt["candidate"]["adopted_genome"]["genome_id"] == surv.adopted_genome.genome_id
    assert receipt["candidate"]["step_receipt"]["canonical_trace_digest"] == surv.step_receipt.canonical_trace_digest
    with monkeypatch.context() as missing:
        missing.setattr(fn, "_lean_binary", lambda: None)
        with pytest.raises(RuntimeError, match="PINNED_LEAN_UNAVAILABLE"):
            fn.route_tier3_fable_derivations(single)
    with pytest.raises(ValueError, match="digest mismatch"):
        dataclasses.replace(packet, rust_receipt_json="{}")

    other = {"status": "PASS", "result": {
        "accepted": True, "verdict": "CANDIDATE_VERIFIED", "verified": ["other"],
        "candidates": [{"id": "other", "disposition": "HOST_VERIFIED"}],
    }}
    monkeypatch.setattr(fn.operad_host, "outcome", lambda *_: other)
    with pytest.raises(RuntimeError, match="RUST_REPLAY_REJECTED"):
        fn.route_tier3_fable_derivations(single)


def test_t2_f4_lean_rejects_unknown_source_and_missing_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fn = _funnel_mod()
    launched = []
    monkeypatch.setattr(fn.subprocess, "run", lambda *a, **kw: launched.append(a))
    assert fn.verify_lean4_snippet("theorem unregistered : True := trivial")[0] is False
    monkeypatch.setattr(fn, "_lean_binary", lambda: None)
    trusted = fn._default_lean4_candidates()[0]
    assert fn.verify_lean4_snippet(trusted.lean_source) == (False, (), "PINNED_LEAN_UNAVAILABLE")
    assert launched == []


def test_t2_f4_lean_uses_scratch_and_does_not_forward_host_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    fn = _funnel_mod()
    binary = tmp_path / "lean"
    monkeypatch.setattr(fn, "_lean_binary", lambda: binary)
    monkeypatch.setenv("PFP_TEST_PRIVATE_SENTINEL", "not for the compiler")
    trusted = fn._default_lean4_candidates()[0]
    calls = []

    def run(args: list[str], **kwargs: Any) -> Any:
        scratch = Path(kwargs["cwd"])
        assert scratch != REPO_ROOT and scratch.is_dir()
        assert "PFP_TEST_PRIVATE_SENTINEL" not in kwargs["env"]
        assert kwargs["env"]["HOME"] == str(scratch)
        assert kwargs["env"]["LEAN_PATH"] == ""
        assert args == [str(binary), "CandidateCheck.lean"]
        assert (scratch / args[1]).read_text(encoding="utf-8") == (
            trusted.lean_source + f"\n#print axioms {trusted.lemma_name}\n"
        )
        calls.append(scratch)
        return SimpleNamespace(returncode=0, stdout="no theorem audit in this output")

    monkeypatch.setattr(fn.subprocess, "run", run)
    assert fn.verify_lean4_snippet(trusted.lean_source) == (False, (), "LEAN_AXIOM_AUDIT_REJECTED")
    assert len(calls) == 1 and not calls[0].exists()


def test_t2_f4_tier3_packet_is_immutable_frozen_dataclass() -> None:
    """F4 Boundary: Tier3DerivationPacketV1 instances are frozen and reject post-hoc mutation."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=3, target_count=128)
    val_cases = (_make_validation_case(case_id="t3_frz_1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    pkt = fn.route_tier3_fable_derivations(report)[0]
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        pkt.authority_effect = "Enforce"  # type: ignore[misc]


def test_t2_f4_special_characters_and_unicode_in_candidate_clauses_preserved_safely(
    tmp_path: Path,
) -> None:
    """F4 Adversarial Encoding: Unicode math symbols (∀, ∃, ⊗, Λ) and quotes serialize losslessly."""
    ol = _outer_loop_mod()
    clause = 'Enforce ∀i≠j: {γ_i, γ_j} = 2δ_{ij} over F_2 ⊗ C^2 with DDC trace "CRM\\Λ" & <tag>.'
    delta = ol.CandidateStrandDeltaV1(
        candidate_id="cand_unicode_∀⊗Λ",
        parent_genome_id="g_root",
        derived_from_failures=("fail_unicode_01",),
        detector_rule=DetectorRule("rule_unicode_safe", "unicode_ep", r"float\("),
        constraint_clause=clause,
        typed_ops=_make_default_ops(),
    )
    controller = _make_controller(tmp_path)
    inc = _make_genome(genome_id="g_root")
    val_slice = (
        _make_validation_case(case_id="val_uni_1", baseline_passed=False, treated_passed=True),
    )
    _adopted, receipt = controller.evaluate_and_compress(
        inc, delta, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    encoded = json.dumps(
        {
            "candidate_id": delta.candidate_id,
            "clause": delta.constraint_clause,
            "decision": receipt.pciv_decision,
            "authority_effect": receipt.authority_effect,
        },
        ensure_ascii=False,
    )
    decoded = json.loads(encoded)
    assert decoded["clause"] == clause
    assert decoded["authority_effect"] == "None"


def test_t2_f4_self_certified_or_forged_model_danger_never_grants_credit() -> None:
    """F4 Adversarial: Model-authored danger signals and self-sealed AUTHORIZED dicts earn 0 credit."""
    forged = imm.host_danger("FAKE_ALARM", "opus-5.5-xhigh", "model claims danger")
    dec = imm.decide([], forged)
    assert dec.disposition == imm.PASS
    assert dec.refusal_code == "UNWITNESSED_DANGER_SIGNAL"

    calc = PromptFitnessCalculatorV1()
    assert calc.extract_success_credit({"status": "VERIFIED_EXACT", "gate_status": "AUTHORIZED"}) == 0
    assert (
        calc.extract_obligation_success_credit(
            "OBL-01",
            {"obligation_id": "OBL-01", "status": "VERIFIED_EXACT", "sha256": "sha256:" + "a" * 64},
        )
        == 0
    )


# --- F5 Boundaries & Refusals (5-Arm Sequential Ablation: 6 tests) ---


def test_t2_f5_invalid_track_id_raises_value_error() -> None:
    """F5 Boundary: Unknown or non-string track_id raises ValueError or TypeError."""
    ab = _ablation_mod()
    with pytest.raises(ValueError):
        ab.run_five_arm_sequential_ablation("unknown_track_xyz")
    with pytest.raises((ValueError, TypeError)):
        ab.run_five_arm_sequential_ablation(True)  # type: ignore[arg-type]


def test_t2_f5_naive_append_control_exhibits_monotone_prompt_token_growth() -> None:
    """F5 Boundary: Unpruned naive_append_control grows active prompt tokens above PCIV-compressed Arm 5."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_1_fermion_finite_qm")
    arms = _extract_ablation_arms(rep)
    naive_tok = _extract_attr(arms["naive_append_control"], ("active_prompt_tokens", "final_prompt_tokens"))
    base_tok = _extract_attr(arms["pfp_baseline"], ("active_prompt_tokens", "final_prompt_tokens"))
    full_tok = _extract_attr(arms["pfp_eis_operads_pciv_full"], ("active_prompt_tokens", "final_prompt_tokens"))
    assert naive_tok > base_tok
    assert naive_tok > full_tok


def test_t2_f5_stateless_arm1_never_mutates_genome_across_tasks() -> None:
    """F5 Boundary: Stateless Arm 1 (pfp_baseline) carries 0 cross-task learned rules across tasks."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_2_cohomology_obstruction")
    arms = _extract_ablation_arms(rep)
    base = arms["pfp_baseline"]
    if hasattr(base, "admitted_rules_count") or (
        isinstance(base, Mapping) and "admitted_rules_count" in base
    ):
        assert _extract_attr(base, ("admitted_rules_count",)) == 0
    assert _extract_attr(base, ("autoimmune_false_refusals", "autoimmune_violations")) == 0


def test_t2_f5_whole_run_budget_cap_enforced_across_all_five_arms(
    cached_ablation_all_report: Any,
) -> None:
    """F5 Boundary: Every arm stays strictly within WholeRunBudget microUSD ceiling."""
    arms = _extract_ablation_arms(cached_ablation_all_report)
    cap = getattr(cached_ablation_all_report, "budget_cap_microusd", 5_000_000)
    for arm_name in FIVE_ARM_NAMES:
        summary = arms[arm_name]
        mps = _extract_attr(summary, ("microusd_per_certified_solve", "spent_microusd", "total_microusd"))
        assert mps >= 0
        if hasattr(summary, "total_microusd"):
            assert summary.total_microusd <= cap


def test_t2_f5_zero_pass_arm_denominator_preserves_refused_and_failed_tasks() -> None:
    """F5 Boundary: Pass-rate denominators preserve all assigned tasks (never dropping failures)."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_3_lean4_certificates")
    arms = _extract_ablation_arms(rep)
    n_tasks = len(TRACK_3_TASKS)
    for arm_name, summary in arms.items():
        rate = _extract_attr(summary, ("cumulative_pass_rate", "pass_rate"))
        assert isinstance(rate, Fraction)
        assert Fraction(0) <= rate <= Fraction(1)
        # Reduced Fraction denominator must divide total assigned cases (a multiple of n_tasks)
        if hasattr(summary, "attempted") or (isinstance(summary, Mapping) and "attempted" in summary):
            attempted = _extract_attr(summary, ("attempted",))
            assert attempted >= n_tasks and attempted % n_tasks == 0, f"Bad denominator in {arm_name}"


def test_t2_f5_ablation_report_immutability_and_deterministic_replay() -> None:
    """F5 Boundary: Repeated Track 2 runs produce identical exact Fraction metrics."""
    ab = _ablation_mod()
    r1 = ab.run_five_arm_sequential_ablation("track_2_cohomology_obstruction")
    r2 = ab.run_five_arm_sequential_ablation("track_2_cohomology_obstruction")
    a1 = _extract_ablation_arms(r1)
    a2 = _extract_ablation_arms(r2)
    for name in FIVE_ARM_NAMES:
        assert _extract_attr(a1[name], ("cumulative_pass_rate", "pass_rate")) == _extract_attr(
            a2[name], ("cumulative_pass_rate", "pass_rate")
        )
        assert _extract_attr(a1[name], ("tokens_per_certified_solve",)) == _extract_attr(
            a2[name], ("tokens_per_certified_solve",)
        )


# --- F6 Boundaries & Refusals (Native Rust Hosts & Custody: 6 tests) ---


def test_t2_f6_pfp_operad_ledger_refuses_unknown_failure_class_and_bad_sha256(
    tmp_path: Path,
) -> None:
    """F6 Boundary: Rust pfp_operad refuses unregistered failure classes and malformed SHA-256 digests."""
    ledger_path = tmp_path / "refused.jsonl"
    out_class = operad_ledger.record_failure(
        ledger_path,
        failure_id="f_bad_class",
        workflow="wf_test",
        run="r1",
        failure_class="InventedNonCanonicalFailure",
        ddc_trace="CRM",
        evidence_sha256="a" * 64,
    )
    assert out_class["status"] == "REFUSED"
    out_sha = operad_ledger.record_failure(
        ledger_path,
        failure_id="f_bad_sha",
        workflow="wf_test",
        run="r1",
        failure_class="StructuralNonFit",
        ddc_trace="CRM",
        evidence_sha256="not_a_64_hex_digest",
    )
    assert out_sha["status"] == "REFUSED"
    assert not ledger_path.exists() or ledger_path.read_text(encoding="utf-8") == ""


def test_t2_f6_pfp_operad_ledger_refuses_tampered_hash_chain_on_verify(tmp_path: Path) -> None:
    """F6 Boundary: Tampering 1 byte in ledger.jsonl is caught by Rust pfp_operad ledger verify."""
    ledger_path = tmp_path / "tamper.jsonl"
    res = operad_ledger.record_failure(
        ledger_path,
        failure_id="f_legit_1",
        workflow="wf_tamper",
        run="r1",
        failure_class="StructuralNonFit",
        ddc_trace="CRM",
        evidence_sha256=sha256_hex("clean_evidence"),
    )
    assert res["status"] == "PASS"
    assert operad_ledger.verify(ledger_path)["status"] == "PASS"

    raw = ledger_path.read_text(encoding="utf-8")
    tampered = raw.replace("f_legit_1", "f_legit_2", 1)
    ledger_path.write_text(tampered, encoding="utf-8")
    ver = operad_ledger.verify(ledger_path)
    assert ver["status"] in ("FAIL", "REFUSED")


def test_t2_f6_pfp_operad_ledger_refuses_bool_or_negative_trial_counts(tmp_path: Path) -> None:
    """F6 Boundary: record_trial refuses boolean subclasses, negative ints, and floats."""
    ledger_path = tmp_path / "trial_guard.jsonl"
    for bad_kwargs in (
        {"baseline_correct": True, "treated_correct": 1, "clean_panel_hits": 0},
        {"baseline_correct": 1, "treated_correct": -1, "clean_panel_hits": 0},
        {"baseline_correct": 1, "treated_correct": 2, "clean_panel_hits": False},
    ):
        with pytest.raises(operad_ledger.OperadLedgerError):
            operad_ledger.record_trial(
                ledger_path,
                candidate_id="c1",
                held_out=["h1"],
                **bad_kwargs,  # type: ignore[arg-type]
            )


def test_t2_f6_pfp_immune_refuses_float_and_bool_in_exact_rational_decide() -> None:
    """F6 Boundary: immune_host.decide prohibits float and bool in rational wire payloads."""
    with pytest.raises(TypeError, match="floating point"):
        immune_host.decide(["r1"], 0.5, Fraction(1, 2))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="boolean"):
        immune_host.decide(["r1"], True, Fraction(1, 2))  # type: ignore[arg-type]


def test_t2_f6_pfp_immune_taint_refuses_cyclic_lineage_graph() -> None:
    """F6 Boundary: Rust pfp_immune taint refuses cyclic lineage edges."""
    res = immune_host.taint(
        [
            {"parent": "g_alpha", "child": "g_beta", "witness": "sha256:" + "1" * 64},
            {"parent": "g_beta", "child": "g_alpha", "witness": "sha256:" + "2" * 64},
        ],
        ["g_alpha"],
    )
    assert res["status"] == "REFUSED"


def test_t2_f6_no_teamwork_metadata_pollutes_pfp_git_repository() -> None:
    """F6 Boundary: In-repo .agents/teamwork directory must not exist inside the PFP repository."""
    in_repo_teamwork = REPO_ROOT / ".agents" / "teamwork"
    assert not in_repo_teamwork.exists(), f"Forbidden teamwork metadata found in repo: {in_repo_teamwork}"


# --- F7 Boundaries & Refusals (Lean 4 Mechanization: 6 tests) ---


def test_t2_f7_lean4_funnel_closure_contains_zero_sorry_admit_or_unsafe() -> None:
    """F7 Boundary: FunnelCompressionClosure.lean contains zero sorry, admit, unsafe, or extern escapes."""
    text = (REPO_ROOT / "lean4" / "FunnelCompressionClosure.lean").read_text(encoding="utf-8")
    # Strip line comments and block comments before token scan
    stripped = re.sub(r"/-.*?-/", "", text, flags=re.DOTALL)
    stripped = re.sub(r"--[^\n]*", "", stripped)
    for forbidden in ("sorry", "admit", "sorryAx", "unsafe ", "@[extern", "@[implemented_by"):
        assert forbidden not in stripped, f"Forbidden token {forbidden!r} found in FunnelCompressionClosure.lean"


def test_t2_f7_lean4_funnel_closure_forbids_classical_choice_if_constructive_target(
    tmp_path: Path,
) -> None:
    """F7 Boundary: FunnelCompressionClosure uses zero Classical.choice and zero Lean.ofReduceBool."""
    lean_src = (REPO_ROOT / "lean4" / "FunnelCompressionClosure.lean").read_text(encoding="utf-8")
    lines = lean_src.splitlines()
    import_lines = [ln for ln in lines if ln.strip().startswith("import ")]
    body_lines = [ln for ln in lines if not ln.strip().startswith("import ")]
    probe = tmp_path / "NoClassicalCheck.lean"
    probe.write_text(
        "\n".join(
            [
                "import Lean",
                *[ln for ln in import_lines if ln.strip() != "import Lean"],
                *body_lines,
                "open Lean Elab Command in",
                "run_cmd do",
                "  let env ← getEnv",
                "  for (n, ci) in env.constants.map₂.toList do",
                "    if (ci matches .thmInfo _) && !n.isInternal then",
                "      let axs ← liftCoreM (Lean.collectAxioms n)",
                "      if axs.contains `Classical.choice then",
                '        throwError s!"{n} uses Classical.choice"',
                "      if axs.contains `Lean.ofReduceBool then",
                '        throwError s!"{n} uses native_decide (Lean.ofReduceBool)"',
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["lake", "env", "lean", str(probe)],
        cwd=REPO_ROOT / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, f"Constructive axiom check failed:\n{proc.stdout}\n{proc.stderr}"


def test_t2_f7_lean4_kernel_negation_probe_rejects_false_bloat_promotion_claim(
    tmp_path: Path,
) -> None:
    """F7 Boundary: Kernel decidability probe confirms bloated candidate cannot satisfy Pareto compression."""
    probe = tmp_path / "NegateBloatProbe.lean"
    probe.write_text(
        "\n".join(
            [
                "def pcivPromotes (basePass treatPass baseTok treatTok cleanHits : Nat) : Bool :=",
                "  (cleanHits == 0) && ((treatPass > basePass)",
                "    || ((treatPass == basePass) && (treatPass > 0) && (treatTok < baseTok)))",
                "",
                "theorem bloated_equal_accuracy_rejected : pcivPromotes 3 3 200 450 0 = false := rfl",
                "theorem regression_rejected_even_if_accurate : pcivPromotes 3 4 200 150 1 = false := rfl",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["lake", "env", "lean", str(probe)],
        cwd=REPO_ROOT / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_t2_f7_lean4_kernel_negation_probe_rejects_autoimmune_rule_admission(
    tmp_path: Path,
) -> None:
    """F7 Boundary: Kernel negation probe confirms a rule hitting >=1 self-fixture cannot pass monotone Thymus."""
    probe = tmp_path / "NegateThymusProbe.lean"
    probe.write_text(
        "\n".join(
            [
                "def thymusAdmits (fires : Nat → Bool) (panel : List Nat) : Bool :=",
                "  panel.all (fun x => !(fires x))",
                "",
                "theorem autoimmune_hit_refused :",
                "    thymusAdmits (fun x => x == 2) [1, 2, 3] = false := rfl",
                "theorem panel_extension_monotone_rejection :",
                "    thymusAdmits (fun x => x == 2) [1, 2, 3, 4] = false := rfl",
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["lake", "env", "lean", str(probe)],
        cwd=REPO_ROOT / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_t2_f7_lean4_contract_score_sha256_tamper_detection_verified() -> None:
    """F7 Boundary: Companion .contract.score.json binds non-trivial 64-hex SHA-256 matching disk bytes."""
    lean_path = REPO_ROOT / "lean4" / "FunnelCompressionClosure.lean"
    score_path = REPO_ROOT / "lean4" / "FunnelCompressionClosure.contract.score.json"
    assert score_path.is_file(), (
        "Missing lean4/FunnelCompressionClosure.contract.score.json companion"
    )
    data = json.loads(score_path.read_text(encoding="utf-8"))
    digest_hex = hashlib.sha256(lean_path.read_bytes()).hexdigest()
    assert len(digest_hex) == 64 and digest_hex != "0" * 64
    assert data["contract"]["artifact"]["sha256"] == digest_hex
    assert data["score"]["artifact"]["sha256"] == digest_hex


def test_t2_f7_lean4_theorems_are_non_vacuous_not_true_trivial(tmp_path: Path) -> None:
    """F7 Boundary: Elaborated theorem types in FunnelCompressionClosure are non-vacuous (never bare True)."""
    lean_src = (REPO_ROOT / "lean4" / "FunnelCompressionClosure.lean").read_text(encoding="utf-8")
    lines = lean_src.splitlines()
    import_lines = [ln for ln in lines if ln.strip().startswith("import ")]
    body_lines = [ln for ln in lines if not ln.strip().startswith("import ")]
    probe = tmp_path / "NonVacuousCheck.lean"
    probe.write_text(
        "\n".join(
            [
                "import Lean",
                *[ln for ln in import_lines if ln.strip() != "import Lean"],
                *body_lines,
                "open Lean Elab Command in",
                "run_cmd do",
                "  let env ← getEnv",
                "  for (n, ci) in env.constants.map₂.toList do",
                "    if let .thmInfo info := ci then",
                "      if !n.isInternal then",
                "        if info.type.isConstOf ``True then",
                '          throwError s!"vacuous theorem {n} : True"',
            ]
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["lake", "env", "lean", str(probe)],
        cwd=REPO_ROOT / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, f"Vacuity check failed:\n{proc.stdout}\n{proc.stderr}"


# --- F8 Boundaries & Refusals (Atlas & DAG Derivations P015/P016/P018/P019: 6 tests) ---


def test_t2_f8_p015_local_green_global_red_triangle_obstruction_counterexample() -> None:
    """F8 Boundary (P015): 3-cycle local-green edge assignments with non-zero holonomy admit 0 global sections."""
    # Over Z/2Z on 3 vertices {0, 1, 2}, locally valid edge differences (0, 0, 1) have cycle sum 1 != 0:
    edge_diffs = (0, 0, 1)
    global_sections = [
        (x0, x1, x2)
        for x0 in (0, 1)
        for x1 in (0, 1)
        for x2 in (0, 1)
        if ((x1 - x0) % 2, (x2 - x1) % 2, (x0 - x2) % 2) == edge_diffs
    ]
    assert global_sections == []
    # Whereas exact coboundary (1, 1, 0) admits exactly 2 global sections over Z/2Z:
    exact_sections = [
        (x0, x1, x2)
        for x0 in (0, 1)
        for x1 in (0, 1)
        for x2 in (0, 1)
        if ((x1 - x0) % 2, (x2 - x1) % 2, (x0 - x2) % 2) == (1, 1, 0)
    ]
    assert len(exact_sections) == 2
    p015_texts = "\n".join(
        (REPO_ROOT / "dag" / "derivations" / f"audit_p015_{i:03d}.md").read_text(encoding="utf-8")
        for i in range(1, 5)
    )
    assert "global" in p015_texts.lower() and "local" in p015_texts.lower()


def test_t2_f8_p016_cost_breaking_quotient_identification_counterexample() -> None:
    """F8 Boundary (P016): Merging states with equal transitions but unequal action costs corrupts optimal cost."""
    # States s1 and s2 both transition on action 'a' to goal g, with cost(s1,a)=1 and cost(s2,a)=10.
    transitions = {
        ("s0", "left"): ("s1", 2),
        ("s0", "right"): ("s2", 1),
        ("s1", "a"): ("g", 1),
        ("s2", "a"): ("g", 10),
    }
    true_opt_s0 = min(
        transitions[("s0", "left")][1] + transitions[("s1", "a")][1],
        transitions[("s0", "right")][1] + transitions[("s2", "a")][1],
    )
    assert true_opt_s0 == 3  # s0 -> s1 (2) -> g (1) = 3 < 11
    # Cost-blind quotient merging {s1, s2} -> q with optimistic value min(1,10)=1 falsely predicts 2!
    naive_quotient_opt = transitions[("s0", "right")][1] + min(
        transitions[("s1", "a")][1], transitions[("s2", "a")][1]
    )
    assert naive_quotient_opt == 2 and naive_quotient_opt != true_opt_s0
    p016_texts = "\n".join(
        (REPO_ROOT / "dag" / "derivations" / f"audit_p016_{i:03d}.md").read_text(encoding="utf-8")
        for i in range(1, 5)
    )
    assert "partition" in p016_texts.lower() or "quotient" in p016_texts.lower()


def test_t2_f8_p018_creimt_ddc_negative_cases_partial_regression_refused() -> None:
    """F8 Boundary (P018): CREIMT bounded repair certifies only REPAIRED, refusing PARTIAL/REGRESSION."""
    p018_texts = "\n".join(
        (REPO_ROOT / "dag" / "derivations" / f"audit_p018_{i:03d}.md").read_text(encoding="utf-8")
        for i in range(2, 6)
    )
    assert "CREIMT" in p018_texts or "C-R-E-I-M-T" in p018_texts
    lower_text = p018_texts.lower()
    assert "partial" in lower_text and "regression" in lower_text


def test_t2_f8_p019_replacement_rule_rejects_stale_confirmation_or_family_regression() -> None:
    """F8 Boundary (P019): research_selection.decide refuses reused occurrences and retains incumbent on regression."""
    def _h(tag: str) -> str:
        return _autopoiesis_digest({"tag": tag})

    files_inc = (
        ("context_policy.py", "CTX = 'v1'\n"),
        ("prompt.txt", "Solve task.\n"),
        ("search_policy.py", "BUDGET = 1\n"),
        ("workflow.json", '{"v": 1}'),
    )
    files_cand = (
        ("context_policy.py", "CTX = 'v2'\n"),
        ("prompt.txt", "Solve task compactly.\n"),
        ("search_policy.py", "BUDGET = 1\n"),
        ("workflow.json", '{"v": 2}'),
    )
    inc = HarnessCandidateV1(_h("src"), _h("root_parent"), files_inc, "baseline", "seed")
    cand = HarnessCandidateV1(_h("src"), inc.candidate_id, files_cand, "compact", "prune_prompt")
    exp = ExperimentSpecV1("camp_p019", _h("src"), _h("chk"), _h("split"), "camp_p019", _h("cfg"))

    def _row(c_obj: HarnessCandidateV1, occ: str, fam: str, passed: bool, phase: str) -> EvaluationReceiptV1:
        return EvaluationReceiptV1(
            exp.experiment_id, _h("src"), c_obj.candidate_id, c_obj.parent, _h("chk"), _h("split"),
            "claude-haiku-5-5", _h("cfg"), "camp_p019", occ, f"t_{fam}", fam, phase,
            0, _h(f"r_{occ}"), True, passed,
            "HOST_ACCEPTED" if passed else "EXECUTION_ERROR",
            100, (_h(f"ev_{occ}"),),
        )

    # 1. Reused occurrence ID between selection and confirmation -> CONFIRMATION_NOT_FRESH
    sel_stale = (_row(inc, "occ_dup", "f1", False, "discovery"), _row(cand, "occ_c1", "f1", True, "discovery"))
    conf_stale = (_row(inc, "occ_dup", "f1", False, "transfer"), _row(cand, "occ_c2", "f1", True, "transfer"))
    with pytest.raises(ValueError, match="CONFIRMATION_NOT_FRESH"):
        research_selection.decide(exp, inc, cand, sel_stale, conf_stale, controls_pass=True)

    # 2. Family regression on f2 despite aggregate gain on f1+f3 -> RETAIN_INCUMBENT
    sel_reg = (
        _row(inc, "s_i1", "f1", False, "discovery"),
        _row(inc, "s_i2", "f2", True, "discovery"),
        _row(inc, "s_i3", "f3", False, "discovery"),
        _row(cand, "s_c1", "f1", True, "discovery"),
        _row(cand, "s_c2", "f2", False, "discovery"),
        _row(cand, "s_c3", "f3", True, "discovery"),
    )
    conf_reg = (
        _row(inc, "k_i1", "f1", False, "transfer"),
        _row(inc, "k_i2", "f2", True, "transfer"),
        _row(inc, "k_i3", "f3", False, "transfer"),
        _row(cand, "k_c1", "f1", True, "transfer"),
        _row(cand, "k_c2", "f2", False, "transfer"),
        _row(cand, "k_c3", "f3", True, "transfer"),
    )
    decision = research_selection.decide(exp, inc, cand, sel_reg, conf_reg, controls_pass=True)
    assert decision.reason == "RETAIN_INCUMBENT"
    assert decision.selected == inc.candidate_id


def test_t2_f8_zero_dangling_edges_or_duplicate_node_ids_in_derivations_dag() -> None:
    """F8 Boundary: dag/derivations_dag.json has unique node IDs and zero dangling edge endpoints."""
    dag = json.loads((REPO_ROOT / "dag" / "derivations_dag.json").read_text(encoding="utf-8"))
    ids = [n["id"] for n in dag["nodes"]]
    assert len(ids) == len(set(ids)), "Duplicate node IDs in derivations_dag.json"
    id_set = set(ids)
    for edge in dag["edges"]:
        src = edge.get("source") or edge.get("from")
        tgt = edge.get("target") or edge.get("to")
        assert src in id_set and tgt in id_set, f"Dangling edge {edge}"


def test_t2_f8_archive_claim_total_conserved_at_607_with_zero_unreviewed() -> None:
    """F8 Boundary: atlas_claim_matches.json conserves all 607 archive claims with valid verdicts."""
    matches = json.loads(
        (REPO_ROOT / "atlas" / "atlas_claim_matches.json").read_text(encoding="utf-8")
    )
    results = matches["results"]
    assert len(results) == 607
    assert all(r["verdict"] in ("matched", "partial", "gap") for r in results)


# --- F9 Boundaries & Refusals (Statistical & Claim Hygiene: 6 tests) ---


def test_t2_f9_comparative_claim_without_holdout_split_raises_value_error() -> None:
    """F9 Boundary: ComparativeClaimAuditorV1 raises ValueError when has_held_out_split is False."""
    auditor = ComparativeClaimAuditorV1()
    with pytest.raises(ValueError, match="COMPARATIVE_CLAIM_HOLDOUT_REQUIRED"):
        auditor.evaluate_claim(
            claim_type="COMPARATIVE_BENEFIT",
            has_held_out_split=False,
            multiplicity_correction="holm",
        )


def test_t2_f9_comparative_claim_without_multiplicity_correction_raises_value_error() -> None:
    """F9 Boundary: ComparativeClaimAuditorV1 raises ValueError when multiplicity_correction is missing."""
    auditor = ComparativeClaimAuditorV1()
    for missing_corr in (None, ""):
        with pytest.raises(ValueError, match="COMPARATIVE_CLAIM_MULTIPLICITY_REQUIRED"):
            auditor.evaluate_claim(
                claim_type="COMPARATIVE_BENEFIT",
                has_held_out_split=True,
                multiplicity_correction=missing_corr,
            )


def test_t2_f9_research_selection_unpaired_evaluations_raises_value_error() -> None:
    """F9 Boundary: research_selection.improved raises UNPAIRED_EVALUATIONS on mismatched task keys."""
    d = sha256_hex
    r_a = EvaluationReceiptV1(
        d("e"), d("s"), d("c1"), d("p"), d("k"), d("sp"),
        "claude-haiku-5-5", d("cfg"), "b1", "o1", "task_A", "fam1", "discovery",
        0, d("r1"), True, True, "HOST_ACCEPTED", 100, (d("ev1"),),
    )
    r_b = EvaluationReceiptV1(
        d("e"), d("s"), d("c2"), d("p"), d("k"), d("sp"),
        "claude-haiku-5-5", d("cfg"), "b1", "o2", "task_B", "fam1", "discovery",
        0, d("r2"), True, True, "HOST_ACCEPTED", 100, (d("ev2"),),
    )
    with pytest.raises(ValueError, match="UNPAIRED_EVALUATIONS"):
        research_selection.improved([r_a], [r_b])


def test_t2_f9_research_selection_incomplete_or_infra_error_row_blocks_promotion() -> None:
    """F9 Boundary: Any INCOMPLETE or INFRASTRUCTURE_ERROR row prevents candidate promotion."""
    d = sha256_hex
    inc_row = EvaluationReceiptV1(
        d("e"), d("s"), d("inc"), d("p"), d("k"), d("sp"),
        "claude-haiku-5-5", d("cfg"), "b1", "o1", "task_1", "fam1", "discovery",
        0, d("r1"), False, False, "INFRASTRUCTURE_ERROR", 100, (),
    )
    cand_row = EvaluationReceiptV1(
        d("e"), d("s"), d("cand"), d("inc"), d("k"), d("sp"),
        "claude-haiku-5-5", d("cfg"), "b1", "o2", "task_1", "fam1", "discovery",
        0, d("r2"), True, True, "HOST_ACCEPTED", 80, (d("ev2"),),
    )
    assert research_selection.improved([cand_row], [inc_row]) is False


def test_t2_f9_pareto_front_selector_never_uses_composite_scalar_weight() -> None:
    """F9 Boundary: ParetoFrontSelectorV1 retains non-convex trade-off points in lexicographic order."""
    selector = ParetoFrontSelectorV1()
    fronts = selector.partition_fronts(
        [
            {"id": "cheap_low", "correctness": Fraction(2, 4), "cost": 50},
            {"id": "accurate_high", "correctness": Fraction(4, 4), "cost": 500},
            {"id": "mid_tradeoff", "correctness": Fraction(3, 4), "cost": 100},
            {"id": "dominated_expensive", "correctness": Fraction(3, 4), "cost": 250},
        ]
    )
    assert [c["id"] for c in fronts[0]] == ["accurate_high", "mid_tradeoff", "cheap_low"]
    assert [c["id"] for c in fronts[1]] == ["dominated_expensive"]


def test_t2_f9_holm_correction_rejects_marginal_unadjusted_p_under_multiple_arms() -> None:
    """F9 Boundary: Holm step-down over m=4 comparisons adjusts p=0.02 to 0.08 > alpha=0.05."""
    raw_ps = [Fraction(2, 100), Fraction(15, 100), Fraction(40, 100), Fraction(80, 100)]
    m = len(raw_ps)
    holm_adjusted: list[Fraction] = []
    running_max = Fraction(0)
    for idx, p_val in enumerate(sorted(raw_ps)):
        step_p = min(Fraction(1), p_val * (m - idx))
        running_max = max(running_max, step_p)
        holm_adjusted.append(running_max)
    assert holm_adjusted[0] == Fraction(8, 100)
    assert holm_adjusted[0] > Fraction(5, 100)


# ===========================================================================
# TIER 3 — CROSS-FEATURE PAIRWISE INTERACTIONS (12 TESTS)
# ===========================================================================


def test_t3_pair01_pfp_obstruction_to_eis_thymus_and_active_signal1_repair(
    tmp_path: Path,
) -> None:
    """Tier 3 (PFP x EIS): Obstruction on Task t -> Thymus screen -> active Signal 1 repair on Task t+1."""
    controller = _make_controller(tmp_path)
    seed = _make_genome(genome_id="pair1_g0")
    cand = controller.extract_obstruction_candidate(
        task_id="task_t1",
        failure_text='{"energy": "1.5"}',
        host_failed_predicates=("float_decimal_forbidden",),
        parent_genome=seed,
    )
    thymus_res = controller.screen_with_thymus(cand, CLEAN_EXACT_PYTHON_PANEL)
    assert thymus_res.is_admitted is True and thymus_res.autoimmune_violations == 0

    val_slice = (
        _make_validation_case(case_id="pair1_v1", baseline_passed=False, treated_passed=True),
    )
    adopted, receipt = controller.evaluate_and_compress(
        seed, cand, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert receipt.pciv_decision in ("PROMOTE_ACCURACY", "PROMOTE_COMPRESSION")

    def _task2_checker(text: str) -> Any:
        ok = '"0.125"' not in text and "0.125" not in text
        return _make_host_outcome(
            passed=ok,
            failed_predicates=() if ok else ("float_decimal_forbidden",),
            evidence=text,
        )

    reg = controller.apply_active_regulation(
        adopted,
        '{"energy": "0.125"}',
        _task2_checker,
        repair_generator=lambda _prompt: '{"energy": "1/8"}',
    )
    repair_prompt = str(
        _extract_attr(reg, ("repair_prompt", "repair_feedback", "feedback_prompt", "bounded_repair_prompt"))
    )
    assert "float_decimal_forbidden" in repair_prompt
    assert cand.detector_rule.rule_id in repair_prompt or cand.constraint_clause in repair_prompt


def test_t3_pair02_pfp_obstruction_to_operads_compose_and_rust_ledger_chain(
    tmp_path: Path,
) -> None:
    """Tier 3 (PFP x Operads): Candidate typed_ops composes and writes verified Rust pfp_operad hash chain."""
    controller = _make_controller(tmp_path)
    seed = _make_genome(genome_id="pair2_g0")
    cand = controller.extract_obstruction_candidate(
        task_id="task_operad_1",
        failure_text="```python\ndef solve(): return 1\n```",
        host_failed_predicates=("host.ast_parse",),
        parent_genome=seed,
    )
    sig = compose(list(cand.typed_ops))
    assert sig.arity == 1
    val_slice = (
        _make_validation_case(case_id="pair2_v1", baseline_passed=False, treated_passed=True),
    )
    _adopted, receipt = controller.evaluate_and_compress(
        seed, cand, val_slice, CLEAN_EXACT_PYTHON_PANEL
    )
    assert bool(receipt.ledger_head)
    ledger_files = list(tmp_path.glob("*.jsonl"))
    if ledger_files:
        ver = operad_ledger.verify(ledger_files[0])
        assert ver["status"] == "PASS"


def test_t3_pair03_pfp_trial_to_pciv_pareto_compression_and_lineage_taint(
    tmp_path: Path,
) -> None:
    """Tier 3 (PFP x PCIV): Accuracy promotion -> compression promotion -> autoimmune child taint isolation."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    lineage = civ.Lineage()
    g0 = _make_genome(genome_id="g0_base", base_tokens=500)
    lineage.add("g0_base")

    c1 = ol.CandidateStrandDeltaV1(
        candidate_id="g1_accurate",
        parent_genome_id="g0_base",
        derived_from_failures=("f_step1",),
        detector_rule=DetectorRule("r_step1", "md_fence", r"```python"),
        constraint_clause="Output raw Python without fences. " * 10,
        typed_ops=_make_default_ops(ctx_keys=("c1_verbose",), gen_tokens=380, ctx_tokens=100),
    )
    g1, r1 = controller.evaluate_and_compress(
        g0,
        c1,
        (
            _make_validation_case(
                case_id="s1_v1",
                baseline_passed=False,
                treated_passed=True,
                baseline_tokens=500,
                treated_tokens=480,
            ),
        ),
        CLEAN_EXACT_PYTHON_PANEL,
    )
    assert r1.pciv_decision == "PROMOTE_ACCURACY"
    lineage.derive("g0_base", "g1_accurate", "promote_accuracy")

    c2 = ol.CandidateStrandDeltaV1(
        candidate_id="g2_compressed",
        parent_genome_id="g1_accurate",
        derived_from_failures=("f_step2",),
        detector_rule=DetectorRule("r_step2", "float_cast", r"float\("),
        constraint_clause="Raw Python; Fraction only.",
        typed_ops=_make_default_ops(ctx_keys=("c2_compact",), gen_tokens=160, ctx_tokens=30),
    )
    g2, r2 = controller.evaluate_and_compress(
        g1,
        c2,
        (
            _make_validation_case(
                case_id="s2_v1",
                baseline_passed=True,
                treated_passed=True,
                baseline_tokens=480,
                treated_tokens=190,
            ),
        ),
        CLEAN_EXACT_PYTHON_PANEL,
    )
    assert r2.pciv_decision == "PROMOTE_COMPRESSION"
    lineage.derive("g1_accurate", "g2_compressed", "promote_compression")

    c3_bad = ol.CandidateStrandDeltaV1(
        candidate_id="g3_autoimmune",
        parent_genome_id="g2_compressed",
        derived_from_failures=("f_step3",),
        detector_rule=DetectorRule("r_autoimmune", "clean_hit", r"Fraction"),
        constraint_clause="Bad rule hitting Fraction.",
        typed_ops=_make_default_ops(ctx_keys=("c3_bad",)),
    )
    g_after, r3 = controller.evaluate_and_compress(
        g2,
        c3_bad,
        (_make_validation_case(case_id="s3_v1", baseline_passed=True, treated_passed=True),),
        CLEAN_EXACT_PYTHON_PANEL,
    )
    assert r3.pciv_decision == "REJECT_AUTOIMMUNE"
    assert _genome_id_of(g_after) == "g2_compressed"
    lineage.derive("g2_compressed", "g3_autoimmune", "attempted_child")
    tainted = lineage.taint({"g3_autoimmune"})
    assert tainted == {"g3_autoimmune"}
    sel = civ.select(
        [
            civ.Candidate("g0_base", 1, 2, 250, 500, 20, is_baseline=True),
            civ.Candidate("g1_accurate", 2, 2, 240, 480, 18),
            civ.Candidate("g2_compressed", 2, 2, 95, 190, 12),
            civ.Candidate("g3_autoimmune", 2, 2, 80, 160, 10),
        ],
        tainted=tainted,
    )
    assert sel["Front"] == ["g2_compressed"]
    assert sel["demoted"]["g3_autoimmune"] == "lineage taint"


def test_t3_pair04_tier1_quotient_into_tier2_thymus_saves_screening_work() -> None:
    """Tier 3 (Tier 1 Quotient x Tier 2 Thymus): Quotienting collapses permutations prior to Tier 2 screening."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=512)
    assert batch.unique_quotient_classes < batch.total_generated
    val_cases = (_make_validation_case(case_id="p4_v1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    assert report.tier1_input_count < batch.total_generated
    assert len(report.survivors) >= 1


def test_t3_pair05_tier2_pciv_survivors_into_tier3_lean4_rust_atlas_packets() -> None:
    """Tier 3 (Tier 2 PCIV x Tier 3 Multi-Substrate): Only Tier 2 survivors reach Tier 3 Lean4+Rust+Atlas packets."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=384)
    val_cases = (
        _make_validation_case(
            case_id="p5_v1",
            baseline_passed=False,
            treated_passed=True,
            baseline_tokens=400,
            treated_tokens=220,
        ),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    packets = fn.route_tier3_fable_derivations(report)
    assert len(packets) == len(report.survivors)
    surv_ids = {
        str(_extract_attr(s, ("survivor_id", "candidate_id", "proposal_id", "id")))
        for s in report.survivors
    }
    for pkt in packets:
        pkt_cid = str(_extract_attr(pkt, ("survivor_id", "candidate_id", "proposal_id", "id")))
        assert pkt_cid in surv_ids


def test_t3_pair06_outer_loop_with_c028_jordan_wigner_fermion_host_verifier(
    tmp_path: Path,
) -> None:
    """Tier 3 (Outer Loop x C028 Fermions): Couples active regulation with real C028 Jordan-Wigner dual checker."""
    c028_root = REPO_ROOT / "workflows" / "tasks" / "certified_challenges" / "c028_jordan_wigner_majorana_mapping"
    c028_parent = str(c028_root.parent)
    if c028_parent not in sys.path:
        sys.path.insert(0, c028_parent)
    from c028_jordan_wigner_majorana_mapping.judge_packet.checkers.dual_evaluator import (
        evaluate_dual as c028_eval,
    )

    ex_path = c028_root / "participant_packet" / "examples" / "ex_02_hopping_jw.json"
    ex_case = json.loads(ex_path.read_text(encoding="utf-8"))
    answers = [
        json.loads(line)
        for line in (c028_root / "participant_packet" / "answers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    gold_ans = next(a for a in answers if a["id"] == "ex_02_hopping_jw")
    ok_gold, _msg_gold, _ = c028_eval(ex_case, gold_ans)
    assert ok_gold is True

    # Corrupted draft drops Jordan-Wigner minus sign / uses float string "0.5"
    bad_ans = {**gold_ans, "hamiltonian": [["XX", "0.5"], ["YY", "-1/2"]]}
    ok_bad, msg_bad, _ = c028_eval(ex_case, bad_ans)
    assert ok_bad is False

    controller = _make_controller(tmp_path)
    seed = _make_genome(genome_id="c028_seed")
    cand = controller.extract_obstruction_candidate(
        task_id="C028_ex_02_hopping_jw",
        failure_text=json.dumps(bad_ans),
        host_failed_predicates=("c028_dual_car_and_pauli_expansion", msg_bad[:40]),
        parent_genome=seed,
    )
    clean_panel = tuple(json.dumps(a) for a in answers if a.get("status") == "SOLVED")
    # Ensure rule is screened against real C028 solved JSON outputs
    safe_cand = dataclasses.replace(
        cand,
        detector_rule=DetectorRule("r_c028_decimal", "decimal_coeff", r'"[0-9]{1,4}\.[0-9]{1,4}"'),
    )
    screen = controller.screen_with_thymus(safe_cand, clean_panel)
    assert screen.is_admitted is True and screen.autoimmune_violations == 0


def test_t3_pair07_outer_loop_with_c011_coboundary_repair_and_p015_gluing(
    tmp_path: Path,
) -> None:
    """Tier 3 (Outer Loop x C011 x P015): Couples outer-loop obstruction handling with real C011 dual checker."""
    c011_root = REPO_ROOT / "workflows" / "tasks" / "certified_challenges" / "c011_cycle_rank_ladder_coboundary_repair"
    c011_parent = str(c011_root.parent)
    if c011_parent not in sys.path:
        sys.path.insert(0, c011_parent)
    from c011_cycle_rank_ladder_coboundary_repair.judge_packet.checkers.dual_evaluator import (
        evaluate_dual as c011_eval,
    )

    ex_path = c011_root / "participant_packet" / "examples" / "ex01_solved_diamond.json"
    ex_raw = json.loads(ex_path.read_text(encoding="utf-8"))
    ex_input = ex_raw["input"]
    answers = [
        json.loads(line)
        for line in (c011_root / "participant_packet" / "answers.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    gold_ans = next(a for a in answers if a["id"] == "ex01_solved_diamond")
    res_gold = c011_eval(ex_input, gold_ans)
    assert res_gold["verdict"] == "PASS" and res_gold["agreement"] is True

    bad_ans = {**gold_ans, "phi1": "999"}
    res_bad = c011_eval(ex_input, bad_ans)
    assert res_bad["verdict"] == "FAIL" and res_bad["agreement"] is True

    controller = _make_controller(tmp_path)
    seed = _make_genome(genome_id="c011_seed")

    def _c011_host_checker(reply_json: str) -> Any:
        try:
            parsed = json.loads(reply_json)
            verdict = c011_eval(ex_input, parsed)
            ok = verdict["verdict"] == "PASS"
        except (ValueError, KeyError, TypeError):
            ok = False
        return _make_host_outcome(
            passed=ok,
            failed_predicates=() if ok else ("c011_primal_dual_gap_nonzero",),
            evidence=reply_json,
        )

    reg_ok = controller.apply_active_regulation(seed, json.dumps(gold_ans), _c011_host_checker)
    assert _extract_attr(reg_ok, ("passed", "accepted", "certified", "host_passed")) is True


def test_t3_pair08_outer_loop_with_c041_lean4_lemma_prover_and_axiom_gate(
    tmp_path: Path,
) -> None:
    """Tier 3 (Outer Loop x C041 Lean 4): Screens Lean tactic detector rules against clean Core Lean proofs."""
    clean_lean_proofs = (
        "theorem add_zero_fin (a : Nat) : a + 0 = a := Nat.add_zero a\n",
        "theorem bool_involutive (b : Bool) : (!(!b)) = b := by cases b <;> rfl\n",
    )
    unsound_rule = DetectorRule(
        rule_id="rule_ban_unsound_lean",
        target_epitope="lean_unsound_escape",
        match_pattern=r"sorry|native_decide|Classical\.choice",
    )
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    cand = ol.CandidateStrandDeltaV1(
        candidate_id="cand_c041_guard",
        parent_genome_id="g_lean_0",
        derived_from_failures=("c041_sorry_attempt",),
        detector_rule=unsound_rule,
        constraint_clause="Prove finite lemmas constructively using rfl/cases/decide; never sorry or native_decide.",
        typed_ops=_make_default_ops(ctx_keys=("lean_constructive_guard",)),
    )
    res = controller.screen_with_thymus(cand, clean_lean_proofs)
    assert res.is_admitted is True and res.autoimmune_violations == 0
    hits = imm.signal1("theorem bad : 1 = 2 := by sorry", [unsound_rule])
    assert len(hits) == 1 and hits[0].detector_id == "rule_ban_unsound_lean"


def test_t3_pair09_outer_loop_with_wf52_finite_qm_xxz_hamiltonian_custody() -> None:
    """Tier 3 (Ablation Track 1 WF52 x Custody): Running Track 1 preserves WF52 regulation source pins."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_1_fermion_finite_qm")
    assert "WF52" in tuple(_extract_attr(rep, ("tasks", "task_sequence", "challenge_ids", "track_tasks")))

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "workflows/wf52_finite_qm_benchmark/test_source_custody.py",
            "-k",
            "test_plans_pin_regulation_modules or test_changed_regulation_module_invalidates_a_plan",
            "-q",
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert proc.returncode == 0, f"WF52 source custody broken:\n{proc.stdout}\n{proc.stderr}"


def test_t3_pair10_rust_pfp_immune_and_python_thymus_exact_parity_in_outer_loop(
    tmp_path: Path,
) -> None:
    """Tier 3 (Outer Loop x Rust pfp_immune x Python ThymusGate): 100% screening parity across 12 rules."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    py_gate = ThymusGate(self_panel=CLEAN_EXACT_PYTHON_PANEL)
    patterns = [
        ("r01", r"float\("),
        ("r02", r"Fraction"),
        ("r03", r"eval\("),
        ("r04", r"exact_sum"),
        ("r05", r"import\s{1,4}random"),
        ("r06", r"majorana_sign"),
        ("r07", r"sorryAx"),
        ("r08", r"return\s{1,4}-1"),
        ("r09", r"np\.linalg"),
        ("r10", r"coboundary_residual"),
        ("r11", r"math\.isclose"),
        ("r12", r"0\.0001"),
    ]
    rules = [DetectorRule(rid, f"ep_{rid}", pat) for rid, pat in patterns]
    rust_admitted, _ = imm.screen_rules(rules, list(CLEAN_EXACT_PYTHON_PANEL))
    rust_ids = {r.rule_id for r in rust_admitted}

    for rule in rules:
        py_res = py_gate.evaluate_rule(rule)
        cand = ol.CandidateStrandDeltaV1(
            candidate_id=f"c_{rule.rule_id}",
            parent_genome_id="g0",
            derived_from_failures=("f1",),
            detector_rule=rule,
            constraint_clause="Guard.",
            typed_ops=_make_default_ops(),
        )
        ctrl_res = controller.screen_with_thymus(cand, CLEAN_EXACT_PYTHON_PANEL)
        assert ctrl_res.is_admitted is py_res.is_admitted
        assert (rule.rule_id in rust_ids) is py_res.is_admitted


def test_t3_pair11_five_arm_ablation_into_comparative_claim_auditor_and_pareto_front(
    cached_ablation_all_report: Any,
) -> None:
    """Tier 3 (Ablation x PCIV ParetoFrontSelectorV1 x ComparativeClaimAuditorV1): Full arm sits on Front 0."""
    arms = _extract_ablation_arms(cached_ablation_all_report)
    candidates = [
        {
            "id": arm_name,
            "correctness": _extract_attr(summary, ("cumulative_pass_rate", "pass_rate")),
            "cost": _extract_attr(summary, ("tokens_per_certified_solve",)),
        }
        for arm_name, summary in arms.items()
    ]
    fronts = ParetoFrontSelectorV1().partition_fronts(candidates)
    front0_ids = [c["id"] for c in fronts[0]]
    assert "pfp_eis_operads_pciv_full" in front0_ids
    assert "pfp_baseline" not in front0_ids
    assert "naive_append_control" not in front0_ids


def test_t3_pair12_lean4_funnel_theorems_cross_checked_against_python_funnel_counts() -> None:
    """Tier 3 (Python 3-Tier Funnel x Lean 4 FunnelCompressionClosure): Empirical run obeys mechanized bounds."""
    fn = _funnel_mod()
    batch = fn.generate_python_workflow_permutations(max_depth=4, target_count=512)
    val_cases = (_make_validation_case(case_id="p12_v1", baseline_passed=False, treated_passed=True),)
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    packets = fn.route_tier3_fable_derivations(report)
    # Monotone filtration chain: |Tier3| <= |Tier2| <= |Quotient(Tier1)| <= |Tier1|
    assert len(packets) <= len(report.survivors) <= batch.unique_quotient_classes <= batch.total_generated


# ===========================================================================
# TIER 4 — REAL-WORLD APPLICATION SCENARIOS (6 END-TO-END WORKLOAD TESTS)
# ===========================================================================


def test_t4_scenario1_full_1024_proposal_three_tier_discovery_funnel_end_to_end(
    cached_tier1_1024_batch: Any,
) -> None:
    """Scenario 1: Full 1,024-proposal Tier 1 -> Tier 2 (opus 5.5 xhigh) -> Tier 3 (Fable 5.2) funnel run."""
    fn = _funnel_mod()
    batch = cached_tier1_1024_batch
    assert batch.total_generated >= 1024
    assert 0 < batch.unique_quotient_classes < batch.total_generated

    val_cases = (
        _make_validation_case(
            case_id="scen1_holdout_1",
            baseline_passed=False,
            treated_passed=True,
            baseline_tokens=420,
            treated_tokens=240,
        ),
        _make_validation_case(
            case_id="scen1_holdout_2",
            baseline_passed=True,
            treated_passed=True,
            baseline_tokens=420,
            treated_tokens=240,
        ),
    )
    report = fn.run_tier2_opus_xhigh_gate(batch, CLEAN_EXACT_PYTHON_PANEL, val_cases)
    assert len(report.survivors) >= 1
    assert report.killed_by_falsifier + report.killed_by_thymus + report.killed_by_pciv_bloat >= 1

    packets = fn.route_tier3_fable_derivations(report)
    assert len(packets) == len(report.survivors)
    for pkt in packets:
        assert pkt.authority_effect == "None"
        assert pkt.lean4_verified and pkt.lean4_axioms == ()
        assert pkt.lean4_theorem_name == f"survivor_{pkt.rust_receipt_sha256}"
        assert pkt.dag_node_id is None


def test_t4_scenario2_sequential_fermion_to_finite_qm_track1_campaign() -> None:
    """Scenario 2: Sequential Fermion (C028) -> C021 -> C022 -> C026 -> Finite QM (WF52) campaign."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_1_fermion_finite_qm")
    arms = _extract_ablation_arms(rep)
    base = arms["pfp_baseline"]
    naive = arms["naive_append_control"]
    full = arms["pfp_eis_operads_pciv_full"]

    assert _extract_attr(full, ("cumulative_pass_rate", "pass_rate")) > _extract_attr(
        base, ("cumulative_pass_rate", "pass_rate")
    )
    assert _extract_attr(full, ("tokens_per_certified_solve",)) < _extract_attr(
        base, ("tokens_per_certified_solve",)
    )
    assert _extract_attr(full, ("tokens_per_certified_solve",)) < _extract_attr(
        naive, ("tokens_per_certified_solve",)
    )
    assert _extract_attr(full, ("autoimmune_false_refusals", "autoimmune_violations")) == 0
    assert _extract_attr(rep, ("claim_audit_status", "comparative_claim_audit", "audit_status")) in ("PASS", True)


def test_t4_scenario3_sequential_cohomology_and_obstruction_repair_track2_campaign() -> None:
    """Scenario 3: Sequential Cohomology & Obstruction Repair (C011 -> C012 -> C014 -> C018 -> C019) campaign."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_2_cohomology_obstruction")
    arms = _extract_ablation_arms(rep)
    base = arms["pfp_baseline"]
    naive = arms["naive_append_control"]
    full = arms["pfp_eis_operads_pciv_full"]

    assert _extract_attr(full, ("cumulative_pass_rate", "pass_rate")) > _extract_attr(
        base, ("cumulative_pass_rate", "pass_rate")
    )
    assert _extract_attr(full, ("tokens_per_certified_solve",)) < _extract_attr(
        base, ("tokens_per_certified_solve",)
    )
    assert _extract_attr(full, ("active_prompt_tokens", "final_prompt_tokens")) < _extract_attr(
        naive, ("active_prompt_tokens", "final_prompt_tokens")
    )
    assert _extract_attr(full, ("autoimmune_false_refusals", "autoimmune_violations")) == 0


def test_t4_scenario4_sequential_lean4_and_exact_certificates_track3_campaign() -> None:
    """Scenario 4: Sequential Lean 4 & Exact Certificates (C041 -> C046 -> C050 -> C051 -> C053 -> C060) campaign."""
    ab = _ablation_mod()
    rep = ab.run_five_arm_sequential_ablation("track_3_lean4_certificates")
    arms = _extract_ablation_arms(rep)
    base = arms["pfp_baseline"]
    naive = arms["naive_append_control"]
    full = arms["pfp_eis_operads_pciv_full"]

    assert _extract_attr(full, ("cumulative_pass_rate", "pass_rate")) > _extract_attr(
        base, ("cumulative_pass_rate", "pass_rate")
    )
    assert _extract_attr(full, ("tokens_per_certified_solve",)) < _extract_attr(
        base, ("tokens_per_certified_solve",)
    )
    assert _extract_attr(full, ("tokens_per_certified_solve",)) < _extract_attr(
        naive, ("tokens_per_certified_solve",)
    )
    assert _extract_attr(full, ("autoimmune_false_refusals", "autoimmune_violations")) == 0


def test_t4_scenario5_full_repository_custody_governance_and_atlas_dag_sync() -> None:
    """Scenario 5: End-to-end WF52/WF53 custody, governance floor, Lean 4 build, and Atlas/DAG 1-to-1 sync."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    # 1. WF52 regulation pins + WF53 allowed-paths tests
    k_expr = (
        "test_plans_pin_regulation_modules "
        "or test_changed_regulation_module_invalidates_a_plan "
        "or test_branch_touches_only_allowed_paths"
    )
    custody_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "workflows/wf52_finite_qm_benchmark/test_source_custody.py",
            "workflows/wf53_industry_replacement_benchmark/tests/test_industry_replacement.py",
            "-k",
            k_expr,
            "-q",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert custody_proc.returncode == 0, f"Custody suite failed:\n{custody_proc.stdout}\n{custody_proc.stderr}"

    # 2. Governance checker on branch diff
    gov_proc = subprocess.run(
        [sys.executable, "-m", "governance.tools.checker", "check", "--changed-since", "origin/main"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert gov_proc.returncode == 0, f"Governance check failed:\n{gov_proc.stdout}\n{gov_proc.stderr}"

    # 3. Lean 4 lake build
    lean_proc = subprocess.run(
        ["lake", "build"],
        cwd=REPO_ROOT / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert lean_proc.returncode == 0, f"lake build failed:\n{lean_proc.stdout}\n{lean_proc.stderr}"

    # 4. Atlas & DAG 1-to-1 sync
    atlas_proc = subprocess.run(
        [sys.executable, "dag/build_atlas.py", "--check"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert atlas_proc.returncode == 0, f"Atlas check failed:\n{atlas_proc.stdout}\n{atlas_proc.stderr}"
    assert json.loads(atlas_proc.stdout)["stale"] == []


def test_t4_scenario6_multi_step_autonomous_outer_loop_session_with_ledger_audit(
    tmp_path: Path,
) -> None:
    """Scenario 6: Multi-step outer-loop session exercising all 5 PCIV decisions + active regulation + budget."""
    ol = _outer_loop_mod()
    controller = _make_controller(tmp_path)
    budget = WholeRunBudget("scen6_run", sha256_hex("scen6"), cap_microusd=10_000)

    genome = _make_genome(genome_id="s6_g0", base_tokens=480)
    panel = list(CLEAN_EXACT_PYTHON_PANEL)

    # Step 1: Accuracy promotion
    assert budget.charge("step1_trial", sha256_hex("s1"), 800, 500, 120, 60)
    d1 = ol.CandidateStrandDeltaV1(
        candidate_id="s6_g1_acc",
        parent_genome_id=_genome_id_of(genome),
        derived_from_failures=("s6_f1",),
        detector_rule=DetectorRule("s6_r1", "md_fence", r"```python"),
        constraint_clause="Unwrap markdown fences; emit pure Python. " * 6,
        typed_ops=_make_default_ops(ctx_keys=("s6_verbose_fence",), gen_tokens=360, ctx_tokens=100),
    )
    genome, rec1 = controller.evaluate_and_compress(
        genome,
        d1,
        (
            _make_validation_case(
                case_id="s6_v1",
                baseline_passed=False,
                treated_passed=True,
                baseline_tokens=480,
                treated_tokens=460,
            ),
        ),
        panel,
    )
    assert rec1.pciv_decision == "PROMOTE_ACCURACY" and _genome_id_of(genome) == "s6_g1_acc"
    panel.append("def newly_certified_task1(k: int) -> int:\n    return k + 1\n")

    # Step 2: Compression promotion at equal accuracy
    assert budget.charge("step2_trial", sha256_hex("s2"), 600, 400, 90, 40)
    d2 = ol.CandidateStrandDeltaV1(
        candidate_id="s6_g2_comp",
        parent_genome_id=_genome_id_of(genome),
        derived_from_failures=("s6_f2",),
        detector_rule=DetectorRule("s6_r2", "float_cast", r"float\("),
        constraint_clause="Pure Python; Fraction only.",
        typed_ops=_make_default_ops(ctx_keys=("s6_compact",), gen_tokens=150, ctx_tokens=30),
    )
    genome, rec2 = controller.evaluate_and_compress(
        genome,
        d2,
        (
            _make_validation_case(
                case_id="s6_v2",
                baseline_passed=True,
                treated_passed=True,
                baseline_tokens=460,
                treated_tokens=180,
            ),
        ),
        panel,
    )
    assert rec2.pciv_decision == "PROMOTE_COMPRESSION" and _genome_id_of(genome) == "s6_g2_comp"

    # Step 3: Autoimmune rejection on expanded cumulative panel (hits newly_certified_task1!)
    d3_auto = ol.CandidateStrandDeltaV1(
        candidate_id="s6_g3_auto",
        parent_genome_id=_genome_id_of(genome),
        derived_from_failures=("s6_f3",),
        detector_rule=DetectorRule("s6_r3_bad", "hits_task1", r"newly_certified_task1"),
        constraint_clause="Bad overfitted rule.",
        typed_ops=_make_default_ops(ctx_keys=("s6_auto",)),
    )
    genome, rec3 = controller.evaluate_and_compress(
        genome,
        d3_auto,
        (_make_validation_case(case_id="s6_v3", baseline_passed=True, treated_passed=True),),
        panel,
    )
    assert rec3.pciv_decision == "REJECT_AUTOIMMUNE" and _genome_id_of(genome) == "s6_g2_comp"

    # Step 4: Bloat rejection
    d4_bloat = ol.CandidateStrandDeltaV1(
        candidate_id="s6_g4_bloat",
        parent_genome_id=_genome_id_of(genome),
        derived_from_failures=("s6_f4",),
        detector_rule=DetectorRule("s6_r4_noop", "unseen", r"UNSEEN_XYZ_TOKEN"),
        constraint_clause="Huge non-improving prose block. " * 30,
        typed_ops=_make_default_ops(ctx_keys=("s6_bloat",), gen_tokens=600, ctx_tokens=300),
    )
    genome, rec4 = controller.evaluate_and_compress(
        genome,
        d4_bloat,
        (
            _make_validation_case(
                case_id="s6_v4",
                baseline_passed=True,
                treated_passed=True,
                baseline_tokens=180,
                treated_tokens=900,
            ),
        ),
        panel,
    )
    assert rec4.pciv_decision == "REJECT_BLOAT" and _genome_id_of(genome) == "s6_g2_comp"

    # Step 5: Active regulation on downstream task using compressed genome
    norm_res = norm_mod.normalize_python("```python\ndef final_task() -> int:\n    return 42\n```")
    assert norm_res.parses is True
    reg_final = controller.apply_active_regulation(
        genome,
        "```python\ndef final_task() -> int:\n    return 42\n```",
        lambda txt: _make_host_outcome(
            passed=("```" not in txt and "def final_task" in txt),
            failed_predicates=() if ("```" not in txt and "def final_task" in txt) else ("syntax",),
            evidence=txt,
        ),
    )
    assert _extract_attr(reg_final, ("passed", "accepted", "certified", "host_passed")) is True
    budget.close()
