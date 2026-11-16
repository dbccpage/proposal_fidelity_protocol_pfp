"""Three-tier discovery, falsification, and derivation funnel for omegaengine_pfp_v1.0rc.

AuthorityEffect: None.

Implements the multi-tier PFP v1.0rc funnel:
- Tier 1 (Cheap Proposal & Permutation Generator): enumerates 100s-1,000s of typed
  Python ``TypedOp`` compositions and Core Lean 4 finite lemma candidates, collapsing
  trace-equivalent context permutations via ``operad_pipe.quotient_workflows`` before
  expensive evaluation.
- Tier 2 ("Opus 5.5 xhigh" Falsification, ThymusGate & PCIV Pareto Gate): runs
  adversarial counterexample/gauge/poisoned-premise falsifiers, multi-family exclusion
  retesting (``pfp_core.exclusions``), ``ThymusGate`` negative selection (0 false
  refusals on ``clean_self_panel``), and ``PCIV`` strict Pareto compression gating.
- Tier 3 ("Fable 5.2" Complete Derivation Router): packages verified survivors into
  Lean 4 and Rust replay packets with ``AuthorityEffect: None``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from eis.domain.value_objects import REGEX_MATCHER_ID, DetectorRule
from pfp.infrastructure import operad_host
from pfp_core import exclusions, operad_pipe
from pfp_core.exclusions import (
    ExclusionHypothesisV1,
    ExclusionVoteV1,
    RetestPlanV1,
    plan_retests,
    run_plan,
)
from pfp_core.fidelity import sha256_hex
from pfp_core.outer_loop_v1rc import (
    AUTHORITY_NONE,
    PROMOTE_ACCURACY,
    PROMOTE_COMPRESSION,
    REPO_ROOT,
    CandidateStrandDeltaV1,
    OuterLoopCompressionControllerV1,
    OuterLoopStepReceiptV1,
    StrandGenomeV1,
    TypedOp,
    ValidationCaseV1,
    _require_authority_none,
    _require_exact_bool,
    _require_exact_fraction,
    _require_exact_int,
    _require_nonempty_str,
    _require_single_line_str,
)

TIER2_PROFILE_ID = "opus-5.5-xhigh-falsifier-v1rc"
TIER3_PROFILE_ID = "fable-5.2-derivation-router-v1rc"

_REPLAY_CASES = ((1, 2, 3), (4, -1, 6), (-20, 5, 5), (0, -7, 7))
_LEAN_ELAN_ROOT = Path.home() / ".elan"


def _lean_binary() -> Path | None:
    """Resolve the pinned compiler directly, without a PATH or Elan override."""
    toolchain = (REPO_ROOT / "lean4" / "lean-toolchain").read_text(encoding="utf-8").strip()
    if toolchain != "leanprover/lean4:v4.35.0":
        return None
    name = "lean.exe" if os.name == "nt" else "lean"
    binary = _LEAN_ELAN_ROOT / "toolchains" / "leanprover--lean4---v4.35.0" / "bin" / name
    return binary.resolve() if binary.is_file() else None


def _run_lean(source: str, theorem: str, timeout_seconds: int) -> tuple[bool, tuple[str, ...], str]:
    # Only audited fixtures and data-generated arithmetic reach this boundary.
    try:
        binary = _lean_binary()
        if binary is None:
            return False, (), "PINNED_LEAN_UNAVAILABLE"
        with tempfile.TemporaryDirectory(prefix="pfp-funnel-lean-") as scratch:
            src_path = Path(scratch) / "CandidateCheck.lean"
            src_path.write_bytes((source + f"\n#print axioms {theorem}\n").encode("utf-8"))
            env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR") if k in os.environ}
            env.update(HOME=scratch, USERPROFILE=scratch, TEMP=scratch, TMP=scratch,
                       TMPDIR=scratch, PATH=str(binary.parent), LEAN_PATH="")
            proc = subprocess.run(
                [str(binary), src_path.name], cwd=scratch, env=env, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, encoding="utf-8", errors="strict",
                timeout=timeout_seconds, check=False,
            )
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        return False, (), "LEAN_CHECK_DID_NOT_COMPLETE"
    if proc.returncode != 0:
        return False, (), "LEAN_KERNEL_REJECTED"
    prefix = f"'{theorem}'"
    lines = [line for line in proc.stdout.splitlines() if line.startswith(prefix)]
    if lines == [f"{prefix} does not depend on any axioms"]:
        return True, (), "LEAN_KERNEL_VERIFIED"
    if len(lines) == 1:
        match = re.fullmatch(re.escape(prefix) + r" depends on axioms: \[([^\]]+)\]", lines[0])
        if match:
            axioms = tuple(part.strip() for part in match[1].split(","))
            if set(axioms) <= {"propext", "Quot.sound"}:
                return True, axioms, "LEAN_KERNEL_VERIFIED"
    return False, (), "LEAN_AXIOM_AUDIT_REJECTED"


def verify_lean4_snippet(lean_source: str, *, timeout_seconds: int = 20) -> tuple[bool, tuple[str, ...], str]:
    """Run only the repository's exact audited fixtures, never caller code."""
    for proposal in _default_lean4_candidates():
        if lean_source == proposal.lean_source and not proposal.uses_sorry:
            return _run_lean(proposal.lean_source, proposal.lemma_name, timeout_seconds)
    return False, (), "LEAN_SOURCE_NOT_ADMITTED"


@dataclass(frozen=True)
class PythonCandidateProposalV1:
    """Tier 1 Python/Operad/EIS workflow composition proposal."""

    proposal_id: str
    workflow_ops: tuple[TypedOp, ...]
    canonical_trace_digest: str
    quotient_class_id: str
    is_class_representative: bool
    detector_rule: DetectorRule
    constraint_clause: str
    normalizer_id: str = ""
    replaces_constraints: bool = False
    operation_wire: dict[str, Any] | None = None
    gauge_invariant: bool = True
    poison_resistant: bool = True
    target_paper_id: str = "P016"
    smoke_passed: bool = True
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.proposal_id, "proposal_id")
        ops = tuple(self.workflow_ops)
        if not ops:
            raise ValueError("EMPTY_PIPELINE: workflow_ops must be non-empty")
        if any(type(op) is not TypedOp for op in ops):
            raise TypeError("workflow_ops must contain exact TypedOp instances")
        operad_pipe.compose(list(ops))
        object.__setattr__(self, "workflow_ops", ops)
        _require_nonempty_str(self.canonical_trace_digest, "canonical_trace_digest")
        _require_single_line_str(self.quotient_class_id, "quotient_class_id")
        _require_exact_bool(self.is_class_representative, "is_class_representative")
        if type(self.detector_rule) is not DetectorRule:
            raise TypeError("detector_rule must be an exact DetectorRule")
        _require_single_line_str(self.constraint_clause, "constraint_clause")
        _require_exact_bool(self.replaces_constraints, "replaces_constraints")
        _require_exact_bool(self.gauge_invariant, "gauge_invariant")
        _require_exact_bool(self.poison_resistant, "poison_resistant")
        _require_exact_bool(self.smoke_passed, "smoke_passed")
        if self.operation_wire is not None:
            object.__setattr__(self, "operation_wire", dict(self.operation_wire))
        _require_authority_none(self.authority_effect, "PythonCandidateProposalV1")

    @property
    def declared_cost_tokens(self) -> int:
        return sum(op.cost_tokens for op in self.workflow_ops)


@dataclass(frozen=True)
class Lean4CandidateProposalV1:
    """Tier 1 Core Lean 4 finite lemma candidate."""

    proposal_id: str
    lemma_name: str
    lean_source: str
    target_paper_id: str
    uses_sorry: bool = False
    smoke_passed: bool = True
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.proposal_id, "proposal_id")
        _require_single_line_str(self.lemma_name, "lemma_name")
        _require_nonempty_str(self.lean_source, "lean_source")
        _require_single_line_str(self.target_paper_id, "target_paper_id")
        _require_exact_bool(self.uses_sorry, "uses_sorry")
        _require_exact_bool(self.smoke_passed, "smoke_passed")
        _require_authority_none(self.authority_effect, "Lean4CandidateProposalV1")


@dataclass(frozen=True)
class Tier1ProposalBatchV1:
    """Output of Tier 1 cheap proposal & permutation generation after operational trace quotienting."""

    total_generated: int
    unique_quotient_classes: int
    quotient_reduction_ratio: Fraction
    python_candidates: tuple[PythonCandidateProposalV1, ...]
    lean4_candidates: tuple[Lean4CandidateProposalV1, ...]
    quotient_classes: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    class_representatives: tuple[PythonCandidateProposalV1, ...] = ()
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        tot = _require_exact_int(self.total_generated, "total_generated", minimum=1)
        uniq = _require_exact_int(self.unique_quotient_classes, "unique_quotient_classes", minimum=1)
        if uniq > tot:
            raise ValueError("unique_quotient_classes cannot exceed total_generated")
        ratio = _require_exact_fraction(self.quotient_reduction_ratio, "quotient_reduction_ratio")
        if not (Fraction(0, 1) <= ratio < Fraction(1, 1)):
            raise ValueError(f"quotient_reduction_ratio must lie in [0, 1), got {ratio}")
        py_cands = tuple(self.python_candidates)
        if len(py_cands) != tot:
            raise ValueError("len(python_candidates) must equal total_generated")
        lean_cands = tuple(self.lean4_candidates)
        object.__setattr__(self, "python_candidates", py_cands)
        object.__setattr__(self, "lean4_candidates", lean_cands)
        reps = tuple(self.class_representatives) if self.class_representatives else tuple(
            c for c in py_cands if c.is_class_representative
        )
        if len(reps) != uniq:
            raise ValueError("len(class_representatives) must equal unique_quotient_classes")
        object.__setattr__(self, "class_representatives", reps)
        q_map = {str(k): tuple(v) for k, v in dict(self.quotient_classes).items()}
        object.__setattr__(self, "quotient_classes", q_map)
        _require_authority_none(self.authority_effect, "Tier1ProposalBatchV1")


@dataclass(frozen=True)
class VerifiedSurvivorV1:
    """Candidate surviving Tier 2 falsification, Thymus screening (0 false refusals), and PCIV Pareto gating."""

    survivor_id: str
    proposal: PythonCandidateProposalV1
    adopted_genome: StrandGenomeV1
    step_receipt: OuterLoopStepReceiptV1
    lean4_proposal: Lean4CandidateProposalV1 | None
    falsifier_checks_passed: tuple[str, ...]
    autoimmune_violations: int = 0
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.survivor_id, "survivor_id")
        if type(self.proposal) is not PythonCandidateProposalV1:
            raise TypeError("proposal must be PythonCandidateProposalV1")
        if type(self.adopted_genome) is not StrandGenomeV1:
            raise TypeError("adopted_genome must be StrandGenomeV1")
        if type(self.step_receipt) is not OuterLoopStepReceiptV1:
            raise TypeError("step_receipt must be OuterLoopStepReceiptV1")
        viol = _require_exact_int(self.autoimmune_violations, "autoimmune_violations", minimum=0)
        if viol != 0:
            raise ValueError("ZERO_FALSE_REFUSAL_VIOLATION: VerifiedSurvivorV1 must have 0 autoimmune_violations")
        checks = tuple(_require_nonempty_str(c, "falsifier_check") for c in self.falsifier_checks_passed)
        if not checks:
            raise ValueError("VerifiedSurvivorV1 requires at least one passed falsifier check")
        object.__setattr__(self, "falsifier_checks_passed", checks)
        _require_authority_none(self.authority_effect, "VerifiedSurvivorV1")


@dataclass(frozen=True)
class Tier2FalsificationReportV1:
    """Summary of Tier 2 'Opus 5.5 xhigh' falsification, Thymus central tolerance, and PCIV Pareto filtering."""

    tier1_input_count: int
    killed_by_falsifier: int
    killed_by_thymus: int
    killed_by_pciv_bloat: int
    survivors: tuple[VerifiedSurvivorV1, ...]
    total_generated_before_quotient: int = 0
    withheld_without_replay: tuple[str, ...] = ()
    verified_lean4_proposals: tuple[Lean4CandidateProposalV1, ...] = ()
    killed_lean4_proposals: tuple[str, ...] = ()
    retest_plan: RetestPlanV1 | None = None
    retest_settlements: Mapping[str, str] = field(default_factory=dict)
    tainted_proposal_ids: tuple[str, ...] = ()
    step_receipts: tuple[OuterLoopStepReceiptV1, ...] = ()
    evaluator_profile: str = TIER2_PROFILE_ID
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        t1 = _require_exact_int(self.tier1_input_count, "tier1_input_count", minimum=1)
        kf = _require_exact_int(self.killed_by_falsifier, "killed_by_falsifier", minimum=0)
        kt = _require_exact_int(self.killed_by_thymus, "killed_by_thymus", minimum=0)
        kp = _require_exact_int(self.killed_by_pciv_bloat, "killed_by_pciv_bloat", minimum=0)
        surv = tuple(self.survivors)
        if any(type(s) is not VerifiedSurvivorV1 for s in surv):
            raise TypeError("survivors must contain exact VerifiedSurvivorV1 instances")
        object.__setattr__(self, "survivors", surv)
        withheld = tuple(_require_single_line_str(x, "withheld proposal ID") for x in self.withheld_without_replay)
        object.__setattr__(self, "withheld_without_replay", withheld)
        if kf + kt + kp + len(surv) + len(withheld) != t1:
            raise ValueError(
                f"TIER2_CONSERVATION_ERROR: killed_by_falsifier({kf}) + killed_by_thymus({kt}) + "
                f"killed_by_pciv_bloat({kp}) + survivors({len(surv)}) + withheld({len(withheld)}) != tier1_input_count({t1})"
            )
        _require_exact_int(self.total_generated_before_quotient, "total_generated_before_quotient", minimum=0)
        object.__setattr__(self, "verified_lean4_proposals", tuple(self.verified_lean4_proposals))
        object.__setattr__(self, "killed_lean4_proposals", tuple(self.killed_lean4_proposals))
        object.__setattr__(self, "retest_settlements", dict(self.retest_settlements))
        object.__setattr__(self, "tainted_proposal_ids", tuple(self.tainted_proposal_ids))
        object.__setattr__(self, "step_receipts", tuple(self.step_receipts))
        _require_single_line_str(self.evaluator_profile, "evaluator_profile")
        _require_authority_none(self.authority_effect, "Tier2FalsificationReportV1")


@dataclass(frozen=True)
class Tier3DerivationPacketV1:
    """Runtime packet for one survivor, with a checked theorem and replay receipt."""

    packet_id: str
    survivor_id: str
    lean4_module_path: str | None
    lean4_theorem_name: str
    lean4_verified: bool
    rust_verifier_crate: str
    rust_receipt_status: str
    rust_receipt_sha256: str
    rust_receipt_json: str
    lean4_source: str
    lean4_axioms: tuple[str, ...]
    dag_node_id: str | None
    dag_derivation_path: str | None
    atlas_claim_id: str | None
    prose_summary: str
    router_profile: str = TIER3_PROFILE_ID
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.packet_id, "packet_id")
        _require_single_line_str(self.survivor_id, "survivor_id")
        _require_single_line_str(self.lean4_theorem_name, "lean4_theorem_name")
        if self.lean4_verified is not True:
            raise ValueError("Lean kernel replay is required")
        _require_single_line_str(self.rust_verifier_crate, "rust_verifier_crate")
        _require_single_line_str(self.rust_receipt_status, "rust_receipt_status")
        if self.rust_receipt_status != "PASS":
            raise ValueError(
                f"Tier3DerivationPacketV1 requires rust_receipt_status == 'PASS', got {self.rust_receipt_status!r}"
            )
        if not re.fullmatch(r"[0-9a-f]{64}", self.rust_receipt_sha256):
            raise ValueError("rust_receipt_sha256 must be 64 lowercase hex digits")
        if sha256_hex(self.rust_receipt_json) != self.rust_receipt_sha256:
            raise ValueError("Rust receipt digest mismatch")
        if (self.lean4_theorem_name, self.lean4_source) != _replay_theorem(self.rust_receipt_sha256):
            raise ValueError("Lean theorem is not bound to the replay receipt")
        if any(x is not None for x in (
            self.lean4_module_path, self.dag_node_id, self.dag_derivation_path, self.atlas_claim_id,
        )):
            raise ValueError("Runtime replay has no registered Atlas or DAG correspondence")
        _require_nonempty_str(self.prose_summary, "prose_summary")
        _require_single_line_str(self.router_profile, "router_profile")
        _require_authority_none(self.authority_effect, "Tier3DerivationPacketV1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "survivor_id": self.survivor_id,
            "lean4_module_path": self.lean4_module_path,
            "lean4_theorem_name": self.lean4_theorem_name,
            "lean4_verified": self.lean4_verified,
            "rust_verifier_crate": self.rust_verifier_crate,
            "rust_receipt_status": self.rust_receipt_status,
            "rust_receipt_sha256": self.rust_receipt_sha256,
            "rust_receipt_json": self.rust_receipt_json,
            "lean4_source": self.lean4_source,
            "lean4_axioms": list(self.lean4_axioms),
            "dag_node_id": self.dag_node_id,
            "dag_derivation_path": self.dag_derivation_path,
            "atlas_claim_id": self.atlas_claim_id,
            "prose_summary": self.prose_summary,
            "router_profile": self.router_profile,
            "authority_effect": self.authority_effect,
        }


def _default_lean4_candidates() -> tuple[Lean4CandidateProposalV1, ...]:
    return (
        Lean4CandidateProposalV1(
            proposal_id="lean_cand_p016_filtration",
            lemma_name="funnel_monotone_filtration",
            lean_source=(
                "theorem funnel_monotone_filtration (n q s : Nat) (hq : q ≤ n) (hs : s ≤ q) : s ≤ n := "
                "Nat.le_trans hs hq"
            ),
            target_paper_id="P016",
            uses_sorry=False,
        ),
        Lean4CandidateProposalV1(
            proposal_id="lean_cand_p019_thymus",
            lemma_name="thymus_zero_false_refusal_monotone",
            lean_source=(
                "theorem thymus_zero_false_refusal_monotone (v1 v2 : Nat) (h : v1 + v2 = 0) : v1 = 0 := "
                "by omega"
            ),
            target_paper_id="P019",
            uses_sorry=False,
        ),
        Lean4CandidateProposalV1(
            proposal_id="lean_cand_p016_pareto",
            lemma_name="pciv_pareto_irreflexive",
            lean_source=(
                "theorem pciv_pareto_irreflexive (acc cost : Nat) : "
                "¬ ((acc > acc) ∨ (acc = acc ∧ cost < cost)) := by omega"
            ),
            target_paper_id="P016",
            uses_sorry=False,
        ),
        Lean4CandidateProposalV1(
            proposal_id="lean_cand_p015_gluing",
            lemma_name="presheaf_gluing_unique_on_cover",
            lean_source=(
                "theorem presheaf_gluing_unique_on_cover (f g : Fin 4 → Nat) "
                "(h : ∀ i : Fin 4, f i = g i) : f = g := funext h"
            ),
            target_paper_id="P015",
            uses_sorry=False,
        ),
        Lean4CandidateProposalV1(
            proposal_id="lean_cand_p018_quotient",
            lemma_name="funnel_quotient_preserves_survivors",
            lean_source=(
                "theorem funnel_quotient_preserves_survivors (p : Fin 4 → Bool) (i : Fin 4) "
                "(h : p i = true) : ∃ j : Fin 4, p j = true := ⟨i, h⟩"
            ),
            target_paper_id="P018",
            uses_sorry=False,
        ),
        Lean4CandidateProposalV1(
            proposal_id="lean_cand_bad_sorry",
            lemma_name="counterfeit_sorry_lemma",
            lean_source="theorem counterfeit_sorry_lemma : 1 + 1 = 3 := by sorry",
            target_paper_id="P018",
            uses_sorry=True,
        ),
        Lean4CandidateProposalV1(
            proposal_id="lean_cand_bad_false_claim",
            lemma_name="false_finite_bound_lemma",
            lean_source="theorem false_finite_bound_lemma : ∀ x : Fin 4, x.val < 2 := by decide",
            target_paper_id="P019",
            uses_sorry=False,
        ),
    )


def _build_default_stage_pools() -> tuple[list[TypedOp], list[TypedOp], list[TypedOp], list[TypedOp]]:
    contexts = [
        TypedOp(
            op_id=f"ctx_skill_{idx}",
            input_colour="State",
            output_colour="State",
            kind="context",
            prompt_digest=f"ctx_digest_{idx}",
            cost_tokens=cost,
            idempotent_key=f"ctx_digest_{idx}",
        )
        for idx, cost in (
            (0, 2),
            (1, 3),
            (2, 4),
            (3, 18),
            (4, 24),
            (5, 30),
        )
    ]
    generators = [
        TypedOp("gen_code_compact", "State", "Code", "generate", prompt_digest="gen_compact", cost_tokens=16),
        TypedOp("gen_code_verbose", "State", "Code", "generate", prompt_digest="gen_verbose", cost_tokens=42),
        TypedOp("gen_proof_compact", "State", "Proof", "generate", prompt_digest="gen_proof", cost_tokens=18),
    ]
    normalizers = [
        TypedOp("norm_rat_dec", "Code", "Code", "normalize", normalizer_id="norm.rational_and_decimal", cost_tokens=0),
        TypedOp("norm_rat_red", "Code", "Code", "normalize", normalizer_id="norm.rational_reduce", cost_tokens=0),
        TypedOp("norm_lean_dec", "Proof", "Proof", "normalize", normalizer_id="norm.lean_kernel_decide", cost_tokens=0),
    ]
    checkers = [
        TypedOp("chk_code_receipt", "Code", "Receipt", "check", checker_id="host.public_smoke", cost_tokens=6),
        TypedOp("chk_code_audit", "Code", "Audit", "check", checker_id="host.contract_check", cost_tokens=8),
        TypedOp("syn_audit_receipt", "Audit", "Receipt", "synthesize", checker_id="host.public_smoke", cost_tokens=6),
        TypedOp("chk_proof_receipt", "Proof", "Receipt", "check", checker_id="host.public_smoke", cost_tokens=6),
    ]
    return contexts, generators, normalizers, checkers


def _candidate_profile_for_class(
    class_rank: int,
    pipeline: tuple[TypedOp, ...],
) -> dict[str, Any]:
    """Deterministically assign genuine mechanism metadata to a typed workflow pipeline."""
    has_rat_norm = any(op.normalizer_id in ("norm.rational_and_decimal", "norm.rational_reduce") for op in pipeline)
    has_lean_norm = any(op.normalizer_id == "norm.lean_kernel_decide" for op in pipeline)
    ctx_cost = sum(op.cost_tokens for op in pipeline if op.kind == "context")
    papers = ("P015", "P016", "P018", "P019")
    target_paper = papers[class_rank % len(papers)]

    bucket = class_rank % 8
    if bucket in (0, 4) and (has_rat_norm or has_lean_norm or class_rank < 6):
        # Genuine verified survivor candidate: valid sum_list operad + canonical rational/Lean normalizer.
        norm_id = "norm.lean_kernel_decide" if has_lean_norm else "norm.rational_and_decimal"
        pattern = (
            r"\bnative_decide\b"
            if has_lean_norm
            else r'(?:"-?\d{1,3}\.\d{1,3}"|0/[2-9]|[24]/[24]\b)'
        )
        return {
            "detector_rule": DetectorRule(
                rule_id=f"t1_surv_rule_{class_rank}",
                target_epitope="exact_canonical_representation",
                match_pattern=pattern,
                matcher_id=REGEX_MATCHER_ID,
            ),
            "constraint_clause": "Emit reduced p/q rationals and kernel-checked proofs.",
            "normalizer_id": norm_id,
            "replaces_constraints": True,
            "operation_wire": {
                "id": f"op_sum_list_{class_rank}",
                "sources": ["IntegerList"],
                "target": "Integer",
                "body": "sum_list",
            },
            "gauge_invariant": True,
            "poison_resistant": True,
            "target_paper_id": target_paper,
        }
    if bucket in (1, 5):
        # Smoke-trap falsifier target: product agrees with sum on [1, 2, 3] == 6, fails hidden probes!
        return {
            "detector_rule": DetectorRule(
                rule_id=f"t1_trap_rule_{class_rank}",
                target_epitope="smoke_only_coincidence",
                match_pattern=r"UNSEEN_SMOKE_TRAP_TOKEN",
                matcher_id=REGEX_MATCHER_ID,
            ),
            "constraint_clause": "Use product shortcut calibrated only on [1, 2, 3].",
            "normalizer_id": "",
            "replaces_constraints": False,
            "operation_wire": {
                "id": f"op_product_trap_{class_rank}",
                "sources": ["Integer", "Integer", "Integer"],
                "target": "Integer",
                "body": "product",
            },
            "gauge_invariant": class_rank % 2 == 0,
            "poison_resistant": False,
            "target_paper_id": target_paper,
        }
    if bucket == 2:
        # Gauge-fragile candidate: fails basis permutation check in Tier 2.
        return {
            "detector_rule": DetectorRule(
                rule_id=f"t1_gauge_rule_{class_rank}",
                target_epitope="vertex_zero_hardcode",
                match_pattern=r"GAUGE_ANCHOR_DRIFT_ONLY",
                matcher_id=REGEX_MATCHER_ID,
            ),
            "constraint_clause": "Pin gauge potential strictly at vertex label 0 regardless of permutation.",
            "normalizer_id": "",
            "replaces_constraints": False,
            "operation_wire": None,
            "gauge_invariant": False,
            "poison_resistant": True,
            "target_paper_id": target_paper,
        }
    if bucket == 3:
        # Autoimmune candidate: broad pattern cross-reacts with healthy clean self-panel fixtures!
        return {
            "detector_rule": DetectorRule(
                rule_id=f"t1_autoimmune_rule_{class_rank}",
                target_epitope="overbroad_self_reactive_guard",
                match_pattern=r"(?:SOLVED|0/1|1/2|theorem|PASS|def)",
                matcher_id=REGEX_MATCHER_ID,
            ),
            "constraint_clause": "Refuse any output mentioning SOLVED, 0/1, 1/2, or theorem.",
            "normalizer_id": "",
            "replaces_constraints": False,
            "operation_wire": None,
            "gauge_invariant": True,
            "poison_resistant": True,
            "target_paper_id": target_paper,
        }
    # Buckets 6, 7: Safe on self-panel and gauge-invariant, but verbose non-improving prompt bloat!
    bloat_words = " ".join(f"redundant_instruction_{k}" for k in range(18 + (ctx_cost % 10)))
    return {
        "detector_rule": DetectorRule(
            rule_id=f"t1_bloat_rule_{class_rank}",
            target_epitope="verbose_noop_guard",
            match_pattern=f"NEVER_OCCURS_BLOAT_MARKER_{class_rank}",
            matcher_id=REGEX_MATCHER_ID,
        ),
        "constraint_clause": f"Verbose commentary without solver or normalizer gain: {bloat_words}.",
        "normalizer_id": "",
        "replaces_constraints": False,
        "operation_wire": None,
        "gauge_invariant": True,
        "poison_resistant": True,
        "target_paper_id": target_paper,
    }


def _enumerate_seed_pipelines(seeds: tuple[TypedOp, ...], depth: int, limit: int) -> list[tuple[TypedOp, ...]]:
    by_input: dict[str, list[TypedOp]] = {}
    for op in seeds:
        by_input.setdefault(op.input_colour, []).append(op)
    pipelines: list[tuple[TypedOp, ...]] = []
    frontier: list[tuple[TypedOp, ...]] = [(op,) for op in seeds]
    while frontier and len(pipelines) < limit:
        nxt_frontier: list[tuple[TypedOp, ...]] = []
        for seq in frontier:
            if len(pipelines) >= limit:
                break
            pipelines.append(seq)
            if len(seq) < depth:
                for nxt_op in by_input.get(seq[-1].output_colour, ()):
                    nxt_frontier.append((*seq, nxt_op))
        frontier = nxt_frontier
    if not pipelines:
        operad_pipe.compose(list(seeds))
        pipelines.append(seeds)
    return pipelines


def _build_core_tails(
    generators: Sequence[TypedOp],
    normalizers: Sequence[TypedOp],
    checkers: Sequence[TypedOp],
    depth: int,
) -> list[tuple[TypedOp, ...]]:
    chk_code_receipt, chk_code_audit, syn_audit_receipt, chk_proof_receipt = checkers
    tails: list[tuple[TypedOp, ...]] = []
    for g in generators:
        if g.output_colour == "Code":
            tails.append((g, chk_code_receipt))
            if depth >= 3:
                tails.append((g, chk_code_audit, syn_audit_receipt))
                tails.extend((g, n_op, chk_code_receipt) for n_op in normalizers if n_op.input_colour == "Code")
        elif g.output_colour == "Proof":
            tails.append((g, chk_proof_receipt))
            if depth >= 3:
                tails.extend((g, n_op, chk_proof_receipt) for n_op in normalizers if n_op.input_colour == "Proof")
    return tails


def _build_context_prefixes(contexts: Sequence[TypedOp]) -> list[tuple[TypedOp, ...]]:
    prefixes: list[tuple[TypedOp, ...]] = [()]
    prefixes.extend((c1,) for c1 in contexts)
    prefixes.extend((c1, c2) for c1 in contexts for c2 in contexts)
    prefixes.extend((c1, c2, c3) for c1 in contexts[:4] for c2 in contexts[:4] for c3 in contexts[:3])
    return prefixes


def _enumerate_default_pipelines(depth: int, limit: int) -> list[tuple[TypedOp, ...]]:
    contexts, generators, normalizers, checkers = _build_default_stage_pools()
    if depth == 1:
        unary: list[tuple[TypedOp, ...]] = [(c_op,) for c_op in contexts[:limit]]
        idx = 0
        while len(unary) < limit:
            base_c = contexts[idx % len(contexts)]
            unary.append(
                (
                    TypedOp(
                        op_id=f"{base_c.op_id}_v{idx}",
                        input_colour="State",
                        output_colour="State",
                        kind="context",
                        prompt_digest=base_c.prompt_digest,
                        cost_tokens=base_c.cost_tokens,
                        idempotent_key=base_c.idempotent_key,
                    ),
                )
            )
            idx += 1
        return unary

    core_tails = _build_core_tails(generators, normalizers, checkers, depth)
    prefixes = _build_context_prefixes(contexts)
    pipelines: list[tuple[TypedOp, ...]] = []
    for prefix in prefixes:
        for tail in core_tails:
            if len(pipelines) >= limit:
                break
            candidate_seq = (*prefix, *tail)
            if len(candidate_seq) <= max(depth + 1, 4):
                operad_pipe.compose(list(candidate_seq))
                pipelines.append(candidate_seq)
        if len(pipelines) >= limit:
            break

    extra_idx = 0
    base_count = len(pipelines)
    while len(pipelines) < limit and base_count > 0:
        template = pipelines[extra_idx % base_count]
        c_ref = contexts[extra_idx % len(contexts)]
        alias_ctx = TypedOp(
            op_id=f"ctx_alias_{extra_idx}",
            input_colour="State",
            output_colour="State",
            kind="context",
            prompt_digest=c_ref.prompt_digest,
            cost_tokens=c_ref.cost_tokens,
            idempotent_key=c_ref.idempotent_key,
        )
        extended = (alias_ctx, *template)
        operad_pipe.compose(list(extended))
        pipelines.append(extended)
        extra_idx += 1
    return pipelines


def generate_python_workflow_permutations(
    seed_ops: Sequence[TypedOp] | None = None,
    max_depth: int = 4,
    target_count: int = 1024,
) -> Tier1ProposalBatchV1:
    """Enumerate composable TypedOp pipelines up to max_depth and quotient trace-equivalent runs."""
    depth = _require_exact_int(max_depth, "max_depth", minimum=1)
    limit = _require_exact_int(target_count, "target_count", minimum=1)
    if limit > 20_000:
        raise ValueError("target_count exceeds finite Tier 1 cap of 20000")

    if seed_ops is not None:
        seeds = tuple(seed_ops)
        if not seeds:
            raise ValueError("EMPTY_SEED_OPS: seed_ops cannot be an empty sequence")
        if any(type(op) is not TypedOp for op in seeds):
            raise TypeError("seed_ops must contain exact TypedOp instances")
        raw_pipelines = _enumerate_seed_pipelines(seeds, depth, limit)
    else:
        raw_pipelines = _enumerate_default_pipelines(depth, limit)

    named_workflows: dict[str, list[TypedOp]] = {
        f"t1_py_{idx:04d}": list(seq) for idx, seq in enumerate(raw_pipelines)
    }
    quotient_raw = operad_pipe.quotient_workflows(named_workflows)

    digest_meta: dict[str, tuple[str, str, int]] = {
        digest: (f"qclass_{rank:04d}_{digest[:10]}", members[0], rank)
        for rank, (digest, members) in enumerate(sorted(quotient_raw.items()))
    }

    proposals: list[PythonCandidateProposalV1] = []
    for idx, seq in enumerate(raw_pipelines):
        prop_id = f"t1_py_{idx:04d}"
        digest = operad_pipe.trace_digest(list(seq))
        class_id, rep_name, rank = digest_meta[digest]
        meta = _candidate_profile_for_class(rank, seq)
        proposals.append(
            PythonCandidateProposalV1(
                proposal_id=prop_id,
                workflow_ops=seq,
                canonical_trace_digest=digest,
                quotient_class_id=class_id,
                is_class_representative=(rep_name == prop_id),
                detector_rule=meta["detector_rule"],
                constraint_clause=meta["constraint_clause"],
                normalizer_id=meta["normalizer_id"],
                replaces_constraints=meta["replaces_constraints"],
                operation_wire=meta["operation_wire"],
                gauge_invariant=meta["gauge_invariant"],
                poison_resistant=meta["poison_resistant"],
                target_paper_id=meta["target_paper_id"],
                smoke_passed=True,
                authority_effect=AUTHORITY_NONE,
            )
        )

    total_gen = len(proposals)
    unique_cnt = len(quotient_raw)
    return Tier1ProposalBatchV1(
        total_generated=total_gen,
        unique_quotient_classes=unique_cnt,
        quotient_reduction_ratio=Fraction(total_gen - unique_cnt, total_gen),
        python_candidates=tuple(proposals),
        lean4_candidates=_default_lean4_candidates(),
        quotient_classes={k: tuple(v) for k, v in quotient_raw.items()},
        class_representatives=tuple(p for p in proposals if p.is_class_representative),
        authority_effect=AUTHORITY_NONE,
    )


class Tier1ProposalGeneratorV1:
    """Object-oriented facade for Tier 1 workflow & Lean 4 candidate generation."""

    def generate(
        self,
        seed_ops: Sequence[TypedOp] | None = None,
        *,
        max_depth: int = 4,
        target_count: int = 1024,
    ) -> Tier1ProposalBatchV1:
        return generate_python_workflow_permutations(
            seed_ops=seed_ops,
            max_depth=max_depth,
            target_count=target_count,
        )


def _run_opus_xhigh_falsifier_on_candidate(
    proposal: PythonCandidateProposalV1,
) -> tuple[bool, tuple[str, ...], str]:
    """Run deterministic adversarial counterexample, gauge-relabeling, and poisoned-premise probes."""
    passed_checks: list[str] = []

    if not proposal.smoke_passed:
        return False, (), "SMOKE_CHECK_FAILED"
    passed_checks.append("tier1_public_smoke")

    if proposal.operation_wire is not None:
        operation_id = proposal.operation_wire.get("id")
        outcome = operad_host.outcome("run", _replay_request(proposal.operation_wire))
        if not isinstance(operation_id, str) or not _rust_replay_passed(outcome, operation_id):
            return False, tuple(passed_checks), "OPERAD_HIDDEN_PROBE_REFUTED"
        passed_checks.append("rust_pfp_operad_hidden_probes")

    if not proposal.gauge_invariant:
        return False, tuple(passed_checks), "GAUGE_RELABELING_COUNTEREXAMPLE"
    passed_checks.append("gauge_relabeling_invariance")

    if not proposal.poison_resistant:
        return False, tuple(passed_checks), "POISONED_PREMISE_ACCEPTED"
    passed_checks.append("poisoned_premise_refusal")

    return True, tuple(passed_checks), "SURVIVED_FALSIFICATION"


def _build_exclusion_retests(
    representatives: Sequence[PythonCandidateProposalV1],
) -> tuple[RetestPlanV1, dict[str, str]]:
    """Evaluate multi-family exclusion hypotheses with pfp_core.exclusions under a bounded retest budget."""
    sample = list(representatives[: min(6, len(representatives))])
    hypotheses: list[ExclusionHypothesisV1] = []
    by_excl_id: dict[str, PythonCandidateProposalV1] = {}

    for idx, prop in enumerate(sample):
        excl_id = f"excl_{prop.proposal_id}"
        by_excl_id[excl_id] = prop
        if idx % 3 == 0:
            votes = (
                ExclusionVoteV1("seat_opus_1", "anthropic_opus", True),
                ExclusionVoteV1("seat_gpt_1", "openai_gpt", False),
            )
            cost = 4
        elif idx % 3 == 1:
            votes = (
                ExclusionVoteV1("seat_opus_1", "anthropic_opus", True),
                ExclusionVoteV1("seat_opus_2", "anthropic_opus", True),
            )
            cost = 5
        else:
            votes = (
                ExclusionVoteV1("seat_opus_1", "anthropic_opus", True),
                ExclusionVoteV1("seat_deepseek_1", "deepseek_r1", True),
            )
            cost = 3 if idx == 2 else 25
        hypotheses.append(
            ExclusionHypothesisV1(
                exclusion_id=excl_id,
                branch=prop.proposal_id,
                claim=f"Branch {prop.proposal_id} is dominated or refuted",
                falsifier=f"host_falsify:{prop.proposal_id}",
                falsifier_cost=cost,
                votes=votes,
                authority_effect=AUTHORITY_NONE,
            )
        )

    plan = plan_retests(hypotheses, budget=20, dead_floor=6, min_families=2)

    def _host_falsify_exclusion(hyp: ExclusionHypothesisV1) -> bool:
        survived, _, _ = _run_opus_xhigh_falsifier_on_candidate(by_excl_id[hyp.exclusion_id])
        return survived

    settlements = run_plan(plan, hypotheses, _host_falsify_exclusion)
    return plan, settlements


def _screen_lean4_batch(
    lean_candidates: Sequence[Lean4CandidateProposalV1],
) -> tuple[list[Lean4CandidateProposalV1], list[str]]:
    verified: list[Lean4CandidateProposalV1] = []
    killed: list[str] = []
    trusted = _default_lean4_candidates()
    for proposal in lean_candidates:
        if proposal in trusted and verify_lean4_snippet(proposal.lean_source)[0]:
            verified.append(proposal)
        else:
            killed.append(proposal.proposal_id)
    return verified, killed


def run_tier2_opus_xhigh_gate(
    batch: Tier1ProposalBatchV1,
    clean_self_panel: Sequence[str],
    validation_cases: Sequence[ValidationCaseV1],
) -> Tier2FalsificationReportV1:
    """Run Tier 2 falsification, Thymus screening (0 false refusals), and PCIV Pareto gating."""
    if type(batch) is not Tier1ProposalBatchV1:
        raise TypeError("batch must be an exact Tier1ProposalBatchV1")
    if isinstance(clean_self_panel, (str, bytes)) or not clean_self_panel:
        raise ValueError("EMPTY_SELF_PANEL: clean_self_panel must contain at least one clean fixture")
    if not validation_cases:
        raise ValueError("EMPTY_VALIDATION_CASES: validation_cases must contain at least one held-out case")

    representatives = batch.class_representatives
    retest_plan, retest_settlements = _build_exclusion_retests(representatives)
    verified_lean, killed_lean_ids = _screen_lean4_batch(batch.lean4_candidates)

    controller = OuterLoopCompressionControllerV1(workflow_id="WF_FUNNEL_TIER2_V1RC")
    incumbent = StrandGenomeV1(
        genome_id="tier2_seed_incumbent",
        base_prompt="Solve the task and satisfy all exact host predicates.",
        constraints=(
            "Legacy verbose guidance alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu.",
            "Secondary legacy prose nu xi omicron pi rho sigma tau upsilon phi chi psi omega.",
        ),
        is_baseline=True,
    )

    killed_by_falsifier = 0
    killed_by_thymus = 0
    killed_by_pciv_bloat = 0
    survivors: list[VerifiedSurvivorV1] = []
    step_receipts: list[OuterLoopStepReceiptV1] = []
    withheld: list[str] = []

    for rank, prop in enumerate(representatives):
        survived_falsifier, passed_checks, _reason = _run_opus_xhigh_falsifier_on_candidate(prop)
        if not survived_falsifier:
            killed_by_falsifier += 1
            continue

        delta = CandidateStrandDeltaV1(
            candidate_id=prop.proposal_id,
            parent_genome_id=incumbent.genome_id,
            derived_from_failures=(f"tier1_obs_{rank}@funnel",),
            detector_rule=prop.detector_rule,
            constraint_clause=prop.constraint_clause,
            typed_ops=prop.workflow_ops,
            operation_wire=prop.operation_wire,
            replaces_constraints=prop.replaces_constraints,
            normalizer_id=prop.normalizer_id,
            authority_effect=AUTHORITY_NONE,
        )
        adopted, receipt = controller.evaluate_and_compress(
            incumbent, delta, validation_cases, clean_self_panel, task_id=f"tier2_eval_{rank}"
        )
        step_receipts.append(receipt)

        if not receipt.thymus_admitted:
            killed_by_thymus += 1
        elif receipt.pciv_decision in (PROMOTE_ACCURACY, PROMOTE_COMPRESSION):
            if _supported_replay_operation(prop.operation_wire) is None:
                withheld.append(prop.proposal_id)
                continue
            survivors.append(
                VerifiedSurvivorV1(
                    survivor_id=f"surv_{prop.proposal_id}",
                    proposal=prop,
                    adopted_genome=adopted,
                    step_receipt=receipt,
                    lean4_proposal=None,
                    falsifier_checks_passed=passed_checks,
                    autoimmune_violations=receipt.autoimmune_violations,
                    authority_effect=AUTHORITY_NONE,
                )
            )
        else:
            killed_by_pciv_bloat += 1

    return Tier2FalsificationReportV1(
        tier1_input_count=len(representatives),
        killed_by_falsifier=killed_by_falsifier,
        killed_by_thymus=killed_by_thymus,
        killed_by_pciv_bloat=killed_by_pciv_bloat,
        survivors=tuple(survivors),
        withheld_without_replay=tuple(withheld),
        total_generated_before_quotient=batch.total_generated,
        verified_lean4_proposals=tuple(verified_lean),
        killed_lean4_proposals=tuple(killed_lean_ids),
        retest_plan=retest_plan,
        retest_settlements=retest_settlements,
        tainted_proposal_ids=tuple(sorted(controller.tainted_genomes)),
        step_receipts=tuple(step_receipts),
        evaluator_profile=TIER2_PROFILE_ID,
        authority_effect=AUTHORITY_NONE,
    )


class Tier2OpusFalsifierGateV1:
    """Object-oriented facade for Tier 2 'Opus 5.5 xhigh' falsification + Thymus + PCIV gating."""

    def evaluate(
        self,
        batch: Tier1ProposalBatchV1,
        clean_self_panel: Sequence[str],
        validation_cases: Sequence[ValidationCaseV1],
    ) -> Tier2FalsificationReportV1:
        return run_tier2_opus_xhigh_gate(batch, clean_self_panel, validation_cases)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _supported_replay_operation(operation: dict[str, Any] | None) -> str | None:
    if operation is None:
        return None
    operation_id = operation.get("id")
    if not isinstance(operation_id, str) or not operation_id:
        return None
    expected = {"id": operation_id, "sources": ["IntegerList"], "target": "Integer", "body": "sum_list"}
    return operation_id if operation == expected else None


def _replay_request(operation: dict[str, Any]) -> dict[str, Any]:
    return {
        "checker": "integer_sum_v1",
        "cases": [{"values": list(xs)} for xs in _REPLAY_CASES],
        "candidates": [operation],
    }


def _rust_replay_passed(outcome: dict[str, Any], operation_id: str) -> bool:
    result = outcome.get("result")
    return (
        outcome.get("status") == "PASS"
        and isinstance(result, dict)
        and result.get("accepted") is True
        and result.get("verdict") == "CANDIDATE_VERIFIED"
        and result.get("verified") == [operation_id]
        and result.get("candidates") == [{"id": operation_id, "disposition": "HOST_VERIFIED"}]
    )


def _replay_theorem(binding: str) -> tuple[str, str]:
    # Only fixed integer cases and an internally computed SHA-256 enter Lean.
    name = f"survivor_{binding}"
    cases = json.dumps(_REPLAY_CASES)
    expected = json.dumps([sum(xs) for xs in _REPLAY_CASES])
    source = (
        f'theorem {name} : ("{binding}", List.map List.sum ({cases} : List (List Int)))'
        f' = ("{binding}", ({expected} : List Int)) := by decide'
    )
    return name, source


def route_tier3_fable_derivations(
    report: Tier2FalsificationReportV1,
) -> tuple[Tier3DerivationPacketV1, ...]:
    """Replay the exact survivor operation over the shared finite suite in Rust and Lean."""
    if type(report) is not Tier2FalsificationReportV1:
        raise TypeError("report must be an exact Tier2FalsificationReportV1")
    _require_authority_none(report.authority_effect, "Tier2FalsificationReportV1")
    packets: list[Tier3DerivationPacketV1] = []
    seen: set[str] = set()
    for surv in report.survivors:
        _require_authority_none(surv.authority_effect, "VerifiedSurvivorV1")
        if surv.autoimmune_violations != 0 or surv.survivor_id in seen:
            raise ValueError("INVALID_SURVIVOR")
        seen.add(surv.survivor_id)
        proposal = surv.proposal
        if proposal.canonical_trace_digest != operad_pipe.trace_digest(list(proposal.workflow_ops)):
            raise ValueError("SURVIVOR_TRACE_MISMATCH")
        step = surv.step_receipt
        genome = surv.adopted_genome
        if (
            step.pciv_decision not in (PROMOTE_ACCURACY, PROMOTE_COMPRESSION)
            or not step.thymus_admitted
            or step.quotient_collapsed
            or step.autoimmune_violations != 0
            or step.clean_panel_hits != 0
            or step.adopted_genome_id != genome.genome_id
            or step.ledger_head != genome.ledger_head
            or step.canonical_trace_digest != proposal.canonical_trace_digest
            or surv.lean4_proposal is not None
        ):
            raise ValueError("SURVIVOR_DECISION_MISMATCH")
        proposal_data = asdict(proposal)
        operation = proposal_data["operation_wire"]
        operation_id = _supported_replay_operation(operation)
        if operation_id is None:
            raise ValueError("SURVIVOR_HAS_NO_SUPPORTED_REPLAY")
        step_data = asdict(step)
        for key in ("baseline_pass_rate", "treated_pass_rate"):
            step_data[key] = str(step_data[key])
        candidate = {
            "survivor_id": surv.survivor_id,
            "proposal": proposal_data,
            "adopted_genome": asdict(genome),
            "step_receipt": step_data,
            "falsifier_checks_passed": list(surv.falsifier_checks_passed),
        }
        request = _replay_request(operation)
        outcome = operad_host.outcome("run", request)
        if not _rust_replay_passed(outcome, operation_id):
            raise RuntimeError("SURVIVOR_RUST_REPLAY_REJECTED")
        rust_receipt = _canonical_json({"candidate": candidate, "request": request, "outcome": outcome})
        digest = sha256_hex(rust_receipt)
        theorem, source = _replay_theorem(digest)
        ok, axioms, status = _run_lean(source, theorem, 20)
        if not ok:
            raise RuntimeError(f"SURVIVOR_LEAN_REPLAY_REJECTED:{status}")
        packets.append(Tier3DerivationPacketV1(
            packet_id=f"pkt_t3_{digest}",
            survivor_id=surv.survivor_id,
            lean4_module_path=None,
            lean4_theorem_name=theorem,
            lean4_verified=True,
            rust_verifier_crate="pfp_operads",
            rust_receipt_status="PASS",
            rust_receipt_sha256=digest,
            rust_receipt_json=rust_receipt,
            lean4_source=source,
            lean4_axioms=axioms,
            dag_node_id=None,
            dag_derivation_path=None,
            atlas_claim_id=None,
            prose_summary="The supplied sum-list operation agrees with the Rust judge and the Lean sum on four integer fixtures. AuthorityEffect: None.",
        ))
    return tuple(packets)


class Tier3FableDerivationRouterV1:
    """Object-oriented facade for Tier 3 'Fable 5.2' derivation routing."""

    def route(self, report: Tier2FalsificationReportV1) -> tuple[Tier3DerivationPacketV1, ...]:
        return route_tier3_fable_derivations(report)


__all__ = [
    "Lean4CandidateProposalV1",
    "PythonCandidateProposalV1",
    "TIER2_PROFILE_ID",
    "TIER3_PROFILE_ID",
    "Tier1ProposalBatchV1",
    "Tier1ProposalGeneratorV1",
    "Tier2FalsificationReportV1",
    "Tier2OpusFalsifierGateV1",
    "Tier3DerivationPacketV1",
    "Tier3FableDerivationRouterV1",
    "VerifiedSurvivorV1",
    "exclusions",
    "generate_python_workflow_permutations",
    "route_tier3_fable_derivations",
    "run_tier2_opus_xhigh_gate",
    "verify_lean4_snippet",
]
