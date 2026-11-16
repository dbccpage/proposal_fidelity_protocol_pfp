"""Cross-package causal outer-loop compression controller for omegaengine_pfp_v1.0rc.

AuthorityEffect: None.

Closes the error-driven non-parametric outer loop across ``pfp``, ``eis``, ``operads``,
and ``pciv`` while preserving ``AuthorityEffect: None`` on host grading and leaving all
pinned workflow custody files untouched:

    Mistake -> Host Obstruction -> ThymusGate (0 false refusals)
    -> Operad Trace Quotient & Verified Normalizers
    -> Held-Out Paired Trial & Strict PCIV Pareto Compression Gate
    -> Active Two-Signal Regulation on Next Task
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
for _extra_path in (
    REPO_ROOT,
    REPO_ROOT / "ops",
    REPO_ROOT / "workflows" / "wf52_finite_qm_benchmark",
    REPO_ROOT / "workflows" / "tasks" / "certified_challenges",
    REPO_ROOT / "workflows" / "tasks" / "yardstick",
):
    _extra_str = str(_extra_path)
    if _extra_str not in sys.path:
        sys.path.append(_extra_str)

from eis.domain.safe_pattern import UnsafePatternRefusal, compile_safe_pattern  # noqa: E402
from eis.domain.thymus import ThymusGate, ThymusSelectionResult  # noqa: E402
from eis.domain.value_objects import (  # noqa: E402
    REGEX_MATCHER_ID,
    DetectorRule,
    Signal1Match,
    Signal2Danger,
)
from operads.application.typed_workflow_compiler import (  # noqa: E402
    CompiledWorkflowV1,
    compile_typed_workflow,
)
from pciv.use_cases import research_selection as _pciv_rs  # noqa: E402
from pciv.use_cases.fitness import (  # noqa: E402
    ComparativeClaimAuditorV1,
    ParetoFrontSelectorV1,
)

pciv_research_decide = _pciv_rs.decide
pciv_research_improved = _pciv_rs.improved
pciv_research_metrics = _pciv_rs.metrics
from pfp.infrastructure import operad_host  # noqa: E402
from pfp_core import civilization, immunity, operad_ledger, operad_pipe  # noqa: E402
from pfp_core.fidelity import (  # noqa: E402
    HostOracleContext,
    ProtectedContract,
    WholeRunBudget,
    sha256_hex,
)
from pfp_core.operad_pipe import TypedOp  # noqa: E402

AUTHORITY_NONE = "None"

PROMOTE_ACCURACY = "PROMOTE_ACCURACY"
PROMOTE_COMPRESSION = "PROMOTE_COMPRESSION"
REJECT_AUTOIMMUNE = "REJECT_AUTOIMMUNE"
REJECT_REGRESSION = "REJECT_REGRESSION"
REJECT_BLOAT = "REJECT_BLOAT"
COLLAPSE_QUOTIENT = "COLLAPSE_QUOTIENT"

PCIV_DECISIONS: frozenset[str] = frozenset(
    {
        PROMOTE_ACCURACY,
        PROMOTE_COMPRESSION,
        REJECT_AUTOIMMUNE,
        REJECT_REGRESSION,
        REJECT_BLOAT,
        COLLAPSE_QUOTIENT,
    }
)

GENESIS_LEDGER_HEAD = "0" * 64


def _require_exact_int(value: Any, name: str, *, minimum: int | None = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an exact int (not bool), got {type(value).__name__}")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _require_exact_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be an exact bool, got {type(value).__name__}")
    return value


def _require_nonempty_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or isinstance(value, bool) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_single_line_str(value: Any, name: str) -> str:
    checked = _require_nonempty_str(value, name)
    if "\n" in checked or "\r" in checked:
        raise ValueError(f"RULE_NOT_ONE_LINE: {name} must not contain line breaks")
    return checked


def _require_authority_none(value: Any, context: str) -> str:
    if value != AUTHORITY_NONE:
        raise ValueError(
            f"AUTHORITY_ESCALATION: {context} requires authority_effect == 'None', got {value!r}"
        )
    return AUTHORITY_NONE


def _require_exact_fraction(value: Any, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, Fraction):
        raise TypeError(f"{name} must be an exact Fraction, got {type(value).__name__}")
    return value


def _case_stem(identifier: str) -> str:
    return identifier.split("@", 1)[0]


def _default_seed_ops() -> tuple[TypedOp, ...]:
    return (
        TypedOp(
            op_id="seed_context",
            input_colour="State",
            output_colour="State",
            kind="context",
            prompt_digest="seed_prompt_v1",
            cost_tokens=16,
            idempotent_key="seed_prompt_v1",
        ),
        TypedOp(
            op_id="seed_generate",
            input_colour="State",
            output_colour="Code",
            kind="generate",
            prompt_digest="draft_solver_v1",
            cost_tokens=24,
        ),
        TypedOp(
            op_id="seed_check",
            input_colour="Code",
            output_colour="Receipt",
            kind="check",
            checker_id="host.public_smoke",
            cost_tokens=8,
        ),
    )


def estimate_token_count(text: str) -> int:
    """Deterministic non-negative token count estimate for prompts and candidate replies."""
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    stripped = text.strip()
    if not stripped:
        return 0
    word_count = len(stripped.split())
    byte_floor = (len(stripped.encode("utf-8")) + 3) // 4
    return max(word_count, byte_floor)


def _reduce_rational_literals_in_text(text: str) -> str:
    """Value-preserving canonicalizer turning unreduced integer ratios a/b into reduced p/q."""

    def _replace_ratio(match: re.Match[str]) -> str:
        raw_num = int(match.group(1))
        raw_den = int(match.group(2))
        if raw_den <= 0:
            return match.group(0)
        reduced = Fraction(raw_num, raw_den)
        return f"{reduced.numerator}/{reduced.denominator}"

    return re.sub(r"(?<![A-Za-z0-9_.])(-?\d+)/([1-9]\d*)(?![A-Za-z0-9_./])", _replace_ratio, text)


def _replace_decimal_halves_and_quarters(text: str) -> str:
    """Value-preserving exact rational normalizer for non-version decimal fraction literals in JSON strings."""
    replacements = {
        '"0.0"': '"0/1"',
        '"-0.0"': '"0/1"',
        '"0.5"': '"1/2"',
        '"-0.5"': '"-1/2"',
        '"0.25"': '"1/4"',
        '"-0.25"': '"-1/4"',
        '"0.75"': '"3/4"',
        '"-0.75"': '"-3/4"',
    }
    out = text
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out


def _replace_lean_native_decide(text: str) -> str:
    """Value-preserving tactic canonicalizer replacing banned native_decide with kernel decide."""
    return re.sub(r"\bnative_decide\b", "decide", text)


BUILTIN_NORMALIZERS: Mapping[str, Callable[[str], str]] = {
    "norm.rational_reduce": _reduce_rational_literals_in_text,
    "norm.decimal_to_rational": _replace_decimal_halves_and_quarters,
    "norm.lean_kernel_decide": _replace_lean_native_decide,
    "norm.rational_and_decimal": lambda s: _reduce_rational_literals_in_text(
        _replace_decimal_halves_and_quarters(s)
    ),
}


@dataclass(frozen=True)
class HostCheckOutcomeV1:
    """Deterministic host verification verdict with explicit predicate bindings."""

    passed: bool
    failed_predicates: tuple[str, ...] = ()
    evidence: str = ""
    observer_id: str = "host.public_smoke"
    danger_type: str = "HOST_PREDICATE_FAILURE"
    defect_count: int = 0
    uncertified_obligations: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_exact_bool(self.passed, "passed")
        _require_nonempty_str(self.observer_id, "observer_id")
        _require_nonempty_str(self.danger_type, "danger_type")
        if not isinstance(self.evidence, str):
            raise TypeError("evidence must be a str")
        normalized_failed = tuple(_require_nonempty_str(p, "failed_predicate") for p in self.failed_predicates)
        normalized_obligations = tuple(
            _require_nonempty_str(o, "uncertified_obligation") for o in self.uncertified_obligations
        )
        object.__setattr__(self, "failed_predicates", normalized_failed)
        object.__setattr__(self, "uncertified_obligations", normalized_obligations)
        effective_defects = _require_exact_int(self.defect_count, "defect_count", minimum=0)
        if not self.passed and effective_defects == 0:
            effective_defects = max(1, len(normalized_failed) + len(normalized_obligations))
        if self.passed and (normalized_failed or normalized_obligations):
            raise ValueError(
                "HOST_OUTCOME_INCONSISTENT: passed=True cannot carry failed_predicates or uncertified_obligations"
            )
        object.__setattr__(self, "defect_count", 0 if self.passed else effective_defects)
        _require_authority_none(self.authority_effect, "HostCheckOutcomeV1")

    @classmethod
    def from_oracle(
        cls,
        oracle: HostOracleContext,
        *,
        observer_id: str = "host.public_smoke",
        danger_type: str = "HOST_PREDICATE_FAILURE",
        evidence: str = "",
    ) -> HostCheckOutcomeV1:
        failed = tuple(oracle.failed)
        uncertified = tuple(oracle.uncertified_obligations)
        certified = oracle.final_output_certified
        if not certified and not failed and not uncertified:
            failed = ("no_certified_predicates_recorded",)
        return cls(
            passed=certified,
            failed_predicates=failed,
            evidence=evidence or json.dumps(oracle.to_dict(), sort_keys=True),
            observer_id=observer_id,
            danger_type=danger_type,
            defect_count=0 if certified else max(1, len(failed) + len(uncertified)),
            uncertified_obligations=uncertified,
        )

    def to_signal2_danger(self) -> Signal2Danger | None:
        if self.passed:
            return None
        return immunity.host_danger(
            self.danger_type,
            self.observer_id,
            self.evidence or ",".join(self.failed_predicates) or "host_failure",
            defects=max(1, self.defect_count),
        )


@dataclass(frozen=True)
class CandidateStrandDeltaV1:
    """Typed candidate guard + prompt constraint + operad pipeline delta derived from host obstructions."""

    candidate_id: str
    parent_genome_id: str
    derived_from_failures: tuple[str, ...]
    detector_rule: DetectorRule
    constraint_clause: str
    typed_ops: tuple[TypedOp, ...]
    operation_wire: dict[str, Any] | None = None
    lean_lemma_source: str | None = None
    replaces_constraints: bool = False
    normalizer_id: str = ""
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.candidate_id, "candidate_id")
        _require_single_line_str(self.parent_genome_id, "parent_genome_id")
        if isinstance(self.derived_from_failures, (str, bytes)):
            raise TypeError("derived_from_failures must be a sequence of failure IDs, not a bare string")
        failures = tuple(_require_single_line_str(f, "failure_id") for f in self.derived_from_failures)
        if not failures:
            raise ValueError("CANDIDATE_WITHOUT_FAILURES: derived_from_failures must be non-empty")
        if len(set(failures)) != len(failures):
            raise ValueError("DUPLICATE_FAILURE_REF: derived_from_failures must not contain duplicates")
        object.__setattr__(self, "derived_from_failures", failures)

        if type(self.detector_rule) is not DetectorRule:
            raise TypeError("detector_rule must be an exact DetectorRule")
        _require_single_line_str(self.constraint_clause, "constraint_clause")

        ops = tuple(self.typed_ops)
        if not ops:
            raise ValueError("EMPTY_PIPELINE: typed_ops must be non-empty")
        if any(type(op) is not TypedOp for op in ops):
            raise TypeError("typed_ops elements must be exact TypedOp instances")
        operad_pipe.compose(list(ops))
        object.__setattr__(self, "typed_ops", ops)

        if self.operation_wire is not None:
            if not isinstance(self.operation_wire, Mapping):
                raise TypeError("operation_wire must be a dict/mapping or None")
            object.__setattr__(self, "operation_wire", dict(self.operation_wire))
        if self.lean_lemma_source is not None and not isinstance(self.lean_lemma_source, str):
            raise TypeError("lean_lemma_source must be a str or None")
        _require_exact_bool(self.replaces_constraints, "replaces_constraints")
        if not isinstance(self.normalizer_id, str):
            raise TypeError("normalizer_id must be a str")
        _require_authority_none(self.authority_effect, "CandidateStrandDeltaV1")

    @property
    def canonical_trace_digest(self) -> str:
        return operad_pipe.trace_digest(list(self.typed_ops))

    @property
    def declared_cost_tokens(self) -> int:
        return sum(op.cost_tokens for op in self.typed_ops)


@dataclass(frozen=True)
class StrandGenomeV1:
    """Immutable regulated solver strand carrying admitted EIS rules, compact constraints, and TypedOps."""

    genome_id: str
    base_prompt: str = "Solve the task and satisfy all exact host predicates."
    admitted_rules: tuple[DetectorRule, ...] = ()
    constraints: tuple[str, ...] = ()
    rule_constraints: Mapping[str, str] = field(default_factory=dict)
    typed_ops: tuple[TypedOp, ...] = field(default_factory=_default_seed_ops)
    normalizer_ids: tuple[str, ...] = ()
    parent_genome_id: str | None = None
    ledger_head: str = GENESIS_LEDGER_HEAD
    is_baseline: bool = False
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.genome_id, "genome_id")
        _require_nonempty_str(self.base_prompt, "base_prompt")
        rules = tuple(self.admitted_rules)
        if any(type(r) is not DetectorRule for r in rules):
            raise TypeError("admitted_rules must contain exact DetectorRule instances")
        object.__setattr__(self, "admitted_rules", rules)

        cleaned_constraints = tuple(_require_single_line_str(c, "constraint") for c in self.constraints)
        object.__setattr__(self, "constraints", cleaned_constraints)

        rc_map = {
            str(k): _require_single_line_str(v, "rule_constraint")
            for k, v in dict(self.rule_constraints).items()
        }
        object.__setattr__(self, "rule_constraints", rc_map)

        ops = tuple(self.typed_ops)
        if not ops:
            raise ValueError("EMPTY_PIPELINE: StrandGenomeV1.typed_ops must be non-empty")
        if any(type(op) is not TypedOp for op in ops):
            raise TypeError("typed_ops must contain exact TypedOp instances")
        operad_pipe.compose(list(ops))
        object.__setattr__(self, "typed_ops", ops)

        norm_ids = tuple(str(n) for n in self.normalizer_ids if str(n))
        for op in ops:
            if op.kind == "normalize" and op.normalizer_id and op.normalizer_id not in norm_ids:
                norm_ids = (*norm_ids, op.normalizer_id)
        object.__setattr__(self, "normalizer_ids", norm_ids)

        if self.parent_genome_id is not None:
            _require_single_line_str(self.parent_genome_id, "parent_genome_id")
        _require_nonempty_str(self.ledger_head, "ledger_head")
        _require_exact_bool(self.is_baseline, "is_baseline")
        _require_authority_none(self.authority_effect, "StrandGenomeV1")

    @property
    def canonical_trace_digest(self) -> str:
        return operad_pipe.trace_digest(list(self.typed_ops))

    def render_prompt(self) -> str:
        if not self.constraints:
            return self.base_prompt
        short_head = self.ledger_head[:16]
        lines = [self.base_prompt, "", f"Rules loaded from failure ledger {short_head}:"]
        for idx, clause in enumerate(self.constraints, start=1):
            lines.append(f"- [g{idx}] {clause}")
        return "\n".join(lines)

    @property
    def active_prompt_tokens(self) -> int:
        op_overhead = sum(op.cost_tokens for op in self.typed_ops if op.kind == "context")
        return estimate_token_count(self.render_prompt()) + op_overhead

    def apply_delta(self, delta: CandidateStrandDeltaV1, *, ledger_head: str | None = None) -> StrandGenomeV1:
        updated_rules = (
            self.admitted_rules
            if any(r.rule_id == delta.detector_rule.rule_id for r in self.admitted_rules)
            else (*self.admitted_rules, delta.detector_rule)
        )
        if delta.replaces_constraints:
            updated_constraints = (delta.constraint_clause,)
        elif delta.constraint_clause in self.constraints:
            updated_constraints = self.constraints
        else:
            updated_constraints = (*self.constraints, delta.constraint_clause)

        updated_rc = dict(self.rule_constraints)
        updated_rc[delta.detector_rule.rule_id] = delta.constraint_clause

        updated_norms = list(self.normalizer_ids)
        if delta.normalizer_id and delta.normalizer_id not in updated_norms:
            updated_norms.append(delta.normalizer_id)
        for op in delta.typed_ops:
            if op.kind == "normalize" and op.normalizer_id and op.normalizer_id not in updated_norms:
                updated_norms.append(op.normalizer_id)

        return StrandGenomeV1(
            genome_id=delta.candidate_id,
            base_prompt=self.base_prompt,
            admitted_rules=updated_rules,
            constraints=updated_constraints,
            rule_constraints=updated_rc,
            typed_ops=delta.typed_ops,
            normalizer_ids=tuple(updated_norms),
            parent_genome_id=self.genome_id,
            ledger_head=ledger_head if ledger_head is not None else self.ledger_head,
            is_baseline=False,
            authority_effect=AUTHORITY_NONE,
        )


@dataclass(frozen=True)
class ValidationCaseV1:
    """Held-out evaluation case for paired incumbent vs candidate outer-loop trials."""

    case_id: str
    family: str = "default"
    prompt_text: str = ""
    draft_reply: str = ""
    repaired_reply: str | None = None
    host_checker: Callable[[str], HostCheckOutcomeV1] | None = None
    attempt_generator: Callable[[StrandGenomeV1, str | None], str] | None = None
    baseline_passed: bool | None = None
    treated_passed: bool | None = None
    baseline_tokens: int | None = None
    treated_tokens: int | None = None
    baseline_microusd: int | None = None
    treated_microusd: int | None = None
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.case_id, "case_id")
        _require_single_line_str(self.family, "family")
        if not isinstance(self.prompt_text, str):
            raise TypeError("prompt_text must be a str")
        if not isinstance(self.draft_reply, str):
            raise TypeError("draft_reply must be a str")
        if self.repaired_reply is not None and not isinstance(self.repaired_reply, str):
            raise TypeError("repaired_reply must be a str or None")
        if self.host_checker is None and (self.baseline_passed is None or self.treated_passed is None):
            raise ValueError(
                "ValidationCaseV1 requires either a callable host_checker or explicit paired "
                "baseline_passed and treated_passed booleans"
            )
        if self.baseline_passed is not None:
            _require_exact_bool(self.baseline_passed, "baseline_passed")
        if self.treated_passed is not None:
            _require_exact_bool(self.treated_passed, "treated_passed")
        for field_name in ("baseline_tokens", "treated_tokens", "baseline_microusd", "treated_microusd"):
            val = getattr(self, field_name)
            if val is not None:
                _require_exact_int(val, field_name, minimum=0)
        _require_authority_none(self.authority_effect, "ValidationCaseV1")


@dataclass(frozen=True)
class RegulatedAttemptReceiptV1:
    """Receipt from Stage 5 active two-signal regulation + bounded repair on a task attempt."""

    genome_id: str
    initial_reply: str
    normalized_reply: str
    final_reply: str
    normalization_applied: bool
    signal1_matches: tuple[Signal1Match, ...]
    matched_rule_ids: tuple[str, ...]
    matched_constraints: tuple[str, ...]
    initial_host_outcome: HostCheckOutcomeV1
    final_host_outcome: HostCheckOutcomeV1
    immune_disposition: str
    repair_triggered: bool
    repair_prompt: str | None
    certified: bool
    calls_used: int
    tokens_used: int
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_single_line_str(self.genome_id, "genome_id")
        _require_exact_bool(self.normalization_applied, "normalization_applied")
        _require_exact_bool(self.repair_triggered, "repair_triggered")
        _require_exact_bool(self.certified, "certified")
        _require_exact_int(self.calls_used, "calls_used", minimum=1)
        _require_exact_int(self.tokens_used, "tokens_used", minimum=0)
        if type(self.initial_host_outcome) is not HostCheckOutcomeV1:
            raise TypeError("initial_host_outcome must be HostCheckOutcomeV1")
        if type(self.final_host_outcome) is not HostCheckOutcomeV1:
            raise TypeError("final_host_outcome must be HostCheckOutcomeV1")
        if self.certified != self.final_host_outcome.passed:
            raise ValueError("CERTIFICATION_MISMATCH: certified must equal final_host_outcome.passed")
        _require_authority_none(self.authority_effect, "RegulatedAttemptReceiptV1")


@dataclass(frozen=True)
class OuterLoopStepReceiptV1:
    """Typed receipt emitted after one Mistake -> Obstruction -> Thymus -> Operad/PCIV step."""

    step_index: int
    task_id: str
    incumbent_genome_id: str
    adopted_genome_id: str
    thymus_admitted: bool
    autoimmune_violations: int
    quotient_collapsed: bool
    canonical_trace_digest: str
    baseline_pass_rate: Fraction
    treated_pass_rate: Fraction
    baseline_tokens: int
    treated_tokens: int
    clean_panel_hits: int
    pciv_decision: str
    ledger_head: str
    authority_effect: str = AUTHORITY_NONE

    def __post_init__(self) -> None:
        _require_exact_int(self.step_index, "step_index", minimum=0)
        _require_single_line_str(self.task_id, "task_id")
        _require_single_line_str(self.incumbent_genome_id, "incumbent_genome_id")
        _require_single_line_str(self.adopted_genome_id, "adopted_genome_id")
        _require_exact_bool(self.thymus_admitted, "thymus_admitted")
        _require_exact_int(self.autoimmune_violations, "autoimmune_violations", minimum=0)
        _require_exact_bool(self.quotient_collapsed, "quotient_collapsed")
        _require_nonempty_str(self.canonical_trace_digest, "canonical_trace_digest")
        b_rate = _require_exact_fraction(self.baseline_pass_rate, "baseline_pass_rate")
        t_rate = _require_exact_fraction(self.treated_pass_rate, "treated_pass_rate")
        if not (Fraction(0, 1) <= b_rate <= Fraction(1, 1)):
            raise ValueError(f"baseline_pass_rate must lie in [0, 1], got {b_rate}")
        if not (Fraction(0, 1) <= t_rate <= Fraction(1, 1)):
            raise ValueError(f"treated_pass_rate must lie in [0, 1], got {t_rate}")
        _require_exact_int(self.baseline_tokens, "baseline_tokens", minimum=0)
        _require_exact_int(self.treated_tokens, "treated_tokens", minimum=0)
        _require_exact_int(self.clean_panel_hits, "clean_panel_hits", minimum=0)
        if self.pciv_decision not in PCIV_DECISIONS:
            raise ValueError(f"pciv_decision must be one of {sorted(PCIV_DECISIONS)}, got {self.pciv_decision!r}")
        _require_nonempty_str(self.ledger_head, "ledger_head")
        _require_authority_none(self.authority_effect, "OuterLoopStepReceiptV1")


@dataclass(frozen=True)
class _PairedSelectionRow:
    """Adapter row matching pciv.use_cases.research_selection.improved structural protocol."""

    task: str
    family: str
    repetition: int
    private_pass: int
    cost: int
    status: str = "COMPLETE"


def _match_obstruction_template(
    task_id: str,
    failure_text: str,
    host_failed_predicates: tuple[str, ...],
    rule_id: str,
) -> tuple[str, str, str, str, dict[str, Any] | None]:
    joined_preds = " ".join(host_failed_predicates).lower()
    result: tuple[str, str, str, str, dict[str, Any] | None]
    if re.search(r"\bnative_decide\b", failure_text):
        result = (
            r"\bnative_decide\b",
            "lean4_banned_native_decide",
            "Never invoke native_decide in Core Lean 4 proofs; use kernel decide or explicit term witnesses.",
            "norm.lean_kernel_decide",
            None,
        )
    elif re.search(r"\bsorry\b", failure_text):
        result = (
            r"\bsorry\b",
            "lean4_sorry_placeholder",
            "Complete every finite proof obligation without sorry or unverified axioms.",
            "",
            None,
        )
    elif re.search(r'"-?\d+\.\d+"', failure_text) or "float" in joined_preds or "decimal" in joined_preds:
        result = (
            r'"-?\d{1,4}\.\d{1,4}"',
            "float_literal_in_exact_rational_path",
            "Encode all exact quantities as canonical reduced p/q strings; never emit decimal floats.",
            "norm.rational_and_decimal",
            None,
        )
    elif re.search(r"(?<![A-Za-z0-9_.])(?:-?\d+/[2-9]\d*|0/[2-9]\d*)", failure_text):
        result = (
            r"(?:0/[2-9]\d{0,3}|-?[2468]/[2468]\b)",
            "unreduced_rational_string",
            "Reduce every rational p/q by gcd(|p|, q) with q >= 1 and represent zero strictly as 0/1.",
            "norm.rational_reduce",
            None,
        )
    elif any(tok in joined_preds for tok in ("car", "anticommut", "majorana", "pauli")):
        escaped = re.escape(failure_text.strip()[:32]) or "CAR_PHASE_DEFECT"
        pat = r"(?:SIGN_DROP|anti_hermitian)" if "SIGN_DROP" in failure_text else escaped
        clause = (
            "Track Jordan-Wigner / F2 parity Z-strings and i-powers mod 4 "
            "so all 2N Majoranas square to +I and anticommute."
        )
        wire = {"id": f"op_{rule_id}", "sources": ["IntegerList"], "target": "Integer", "body": "sum_list"}
        result = (pat, "fermion_car_phase_bookkeeping", clause, "norm.rational_and_decimal", wire)
    elif any(tok in joined_preds for tok in ("coboundary", "circulation", "hodge", "sheaf")):
        escaped = re.escape(failure_text.strip()[:32]) or "COBOUNDARY_RESIDUAL_DEFECT"
        pat = r"(?:UNBALANCED_CYCLE|GAUGE_DRIFT)" if "UNBALANCED_CYCLE" in failure_text else escaped
        clause = (
            "Verify exact coboundary d0(phi) residual and dual cycle "
            "circulation feasibility with zero duality gap."
        )
        wire = {"id": f"op_{rule_id}", "sources": ["IntegerList"], "target": "Integer", "body": "sum_list"}
        result = (pat, "cochain_coboundary_duality_defect", clause, "norm.rational_reduce", wire)
    else:
        escaped = re.escape(failure_text.strip()[:40]) or "EMPTY_DRAFT_DEFECT"
        epitope = re.sub(r"[^a-zA-Z0-9_]", "_", host_failed_predicates[0])[:48] or "host_predicate_defect"
        pred_summary = ", ".join(host_failed_predicates[:3])
        clause = f"Satisfy host predicates ({pred_summary}) and avoid defective pattern from {task_id}."
        result = (escaped, epitope, clause, "", None)
    return result


def _ensure_safe_detector_pattern(pattern: str, failure_text: str) -> str:
    try:
        compiled = compile_safe_pattern(pattern)
        if compiled.search(failure_text) is None and failure_text.strip():
            fallback = re.escape(failure_text.strip()[:32])
            compile_safe_pattern(fallback)
            return fallback
        return pattern
    except UnsafePatternRefusal:
        fallback = re.escape(failure_text.strip()[:24] or "DEFECT")
        compile_safe_pattern(fallback)
        return fallback


def _synthesize_detector_from_obstruction(
    task_id: str,
    failure_text: str,
    host_failed_predicates: tuple[str, ...],
    step_num: int,
) -> tuple[DetectorRule, str, str, dict[str, Any] | None]:
    """Derive a concrete safe-regex DetectorRule, single-line constraint, normalizer_id, and optional operad wire."""
    rule_id = f"rule_{re.sub(r'[^a-zA-Z0-9_-]', '_', task_id)}_{step_num}"
    raw_pat, epitope, constraint, normalizer_id, wire = _match_obstruction_template(
        task_id, failure_text, host_failed_predicates, rule_id
    )
    safe_pat = _ensure_safe_detector_pattern(raw_pat, failure_text)
    rule = DetectorRule(
        rule_id=rule_id,
        target_epitope=epitope,
        match_pattern=safe_pat,
        matcher_id=REGEX_MATCHER_ID,
    )
    return rule, constraint, normalizer_id, wire


class OuterLoopCompressionControllerV1:
    """Causal cross-package controller wiring PFP obstructions, EIS Thymus, Operads, and PCIV."""

    def __init__(
        self,
        *,
        ledger_path: Path | str | None = None,
        workflow_id: str = "WF_OUTER_LOOP_V1RC",
        repair_generator: Callable[[str], str] | None = None,
        custom_normalizers: Mapping[str, Callable[[str], str]] | None = None,
    ) -> None:
        _require_single_line_str(workflow_id, "workflow_id")
        if ledger_path is None:
            self._temp_dir: tempfile.TemporaryDirectory[str] | None = tempfile.TemporaryDirectory(
                prefix="pfp-outer-loop-v1rc-"
            )
            self._ledger_path = Path(self._temp_dir.name) / "ledger.jsonl"
            self._ledger_path.write_text("", encoding="utf-8")
        else:
            self._temp_dir = None
            self._ledger_path = Path(ledger_path)
            self._ledger_path.parent.mkdir(parents=True, exist_ok=True)
            if not self._ledger_path.exists():
                self._ledger_path.write_text("", encoding="utf-8")

        self.workflow_id = workflow_id
        self._default_repair_generator = repair_generator
        self._normalizers: dict[str, Callable[[str], str]] = dict(BUILTIN_NORMALIZERS)
        if custom_normalizers:
            self._normalizers.update(custom_normalizers)

        self.lineage = civilization.Lineage()
        self.tainted_genomes: set[str] = set()
        self._recorded_failures: dict[str, str] = {}
        self._proposed_candidates: set[str] = set()
        self._evaluated_trace_pool: dict[str, str] = {}
        self._step_counter = 0

    @property
    def ledger_path(self) -> Path:
        return self._ledger_path

    def current_ledger_head(self) -> str:
        verified = operad_ledger.verify(self._ledger_path)
        if verified.get("status") != "PASS":
            raise operad_ledger.OperadLedgerError(
                f"LEDGER_CHAIN_CORRUPT: {verified.get('refusal', verified)}"
            )
        result = verified.get("result", {})
        return str(result.get("head", GENESIS_LEDGER_HEAD))

    def register_normalizer(self, normalizer_id: str, fn: Callable[[str], str]) -> None:
        _require_single_line_str(normalizer_id, "normalizer_id")
        if not callable(fn):
            raise TypeError("normalizer fn must be callable")
        self._normalizers[normalizer_id] = fn

    def record_failure_witness(
        self,
        *,
        failure_id: str,
        run_id: str,
        failure_text: str,
        failed_predicates: Sequence[str],
        observer_id: str = "host.public_smoke",
        ddc_trace: str = "CRM",
    ) -> tuple[Signal2Danger, dict[str, Any]]:
        """Stage 1 (Mistake -> Obstruction): verify host observer and append Record::Failure to Rust ledger."""
        _require_single_line_str(failure_id, "failure_id")
        _require_single_line_str(run_id, "run_id")
        if not failed_predicates:
            raise ValueError("PASSING_OUTPUT_NOT_A_FAILURE: failed_predicates must be non-empty")
        danger = immunity.host_danger(
            kind=str(failed_predicates[0]),
            observer=observer_id,
            evidence=failure_text,
            defects=len(failed_predicates),
        )
        decision = immunity.decide([], danger)
        if decision.disposition != immunity.HOLD:
            raise ValueError(
                f"UNWITNESSED_DANGER_SIGNAL: observer {observer_id!r} cannot originate host failure records"
            )
        evidence_sha = sha256_hex(failure_text)
        raw_class = operad_ledger.resolve_failure_class(str(failed_predicates[0]))
        failure_class = (
            raw_class if raw_class in operad_ledger.CANONICAL_FAILURE_CLASSES else "StructuralNonFit"
        )
        if failure_id not in self._recorded_failures:
            outcome = operad_ledger.record_failure(
                self._ledger_path,
                failure_id=failure_id,
                workflow=self.workflow_id,
                run=run_id,
                failure_class=failure_class,
                ddc_trace=ddc_trace if operad_ledger.is_valid_ddc_trace(ddc_trace) else "CRM",
                evidence_sha256=evidence_sha,
            )
            if outcome.get("status") != "PASS":
                refusal = outcome.get("refusal", {})
                if refusal.get("code") != "DUPLICATE_ID":
                    raise operad_ledger.OperadLedgerError(
                        f"LEDGER_FAILURE_REFUSED: {refusal.get('code')}: {refusal.get('message')}"
                    )
            self._recorded_failures[failure_id] = evidence_sha
        else:
            outcome = operad_ledger.verify(self._ledger_path)
        return danger, outcome

    def extract_obstruction_candidate(
        self,
        task_id: str,
        failure_text: str,
        host_failed_predicates: tuple[str, ...],
        parent_genome: StrandGenomeV1,
    ) -> CandidateStrandDeltaV1:
        """Stage 1-2 (Mistake -> Obstruction -> CandidateStrandDeltaV1)."""
        _require_single_line_str(task_id, "task_id")
        if not isinstance(failure_text, str) or not failure_text.strip():
            raise ValueError("failure_text must be a non-empty string")
        if type(parent_genome) is not StrandGenomeV1:
            raise TypeError("parent_genome must be an exact StrandGenomeV1")
        preds = tuple(_require_nonempty_str(p, "host_failed_predicate") for p in host_failed_predicates)
        if not preds:
            raise ValueError("NO_HOST_OBSTRUCTION: host_failed_predicates must be non-empty")

        self._step_counter += 1
        step_num = self._step_counter
        obs_hash = sha256_hex(f"{task_id}:{failure_text}:{','.join(preds)}")[:10]
        failure_id = f"{task_id}@obs_{obs_hash}"

        self.record_failure_witness(
            failure_id=failure_id,
            run_id=f"run_{step_num}",
            failure_text=failure_text,
            failed_predicates=preds,
            observer_id="host.public_smoke",
        )

        detector_rule, constraint_clause, normalizer_id, operation_wire = _synthesize_detector_from_obstruction(
            task_id=task_id,
            failure_text=failure_text,
            host_failed_predicates=preds,
            step_num=step_num,
        )

        # Verify optional WF56 operad candidate body on public + probe cases when present.
        if operation_wire is not None:
            run_outcome = operad_host.outcome(
                "run",
                {
                    "checker": "integer_sum_v1",
                    "cases": [{"values": [1, 2, 3]}, {"values": [4, -1, 6]}],
                    "candidates": [operation_wire],
                },
            )
            if run_outcome.get("status") != "PASS":
                operation_wire = None

        # Compose compact typed_ops pipeline incorporating the new context guard and optional normalizer.
        cand_id = f"cand_{re.sub(r'[^a-zA-Z0-9_-]', '_', task_id)}_{step_num}_{obs_hash[:6]}"
        constraint_digest = sha256_hex(constraint_clause)[:16]
        new_ops: list[TypedOp] = [
            op for op in parent_genome.typed_ops if op.kind == "context"
        ]
        new_ops.append(
            TypedOp(
                op_id=f"ctx_{cand_id}",
                input_colour="State",
                output_colour="State",
                kind="context",
                prompt_digest=constraint_digest,
                cost_tokens=max(4, min(16, estimate_token_count(constraint_clause) // 2)),
                idempotent_key=constraint_digest,
            )
        )
        gen_ops = [op for op in parent_genome.typed_ops if op.kind == "generate"]
        new_ops.extend(
            gen_ops
            if gen_ops
            else [
                TypedOp(
                    op_id="seed_generate",
                    input_colour="State",
                    output_colour="Code",
                    kind="generate",
                    prompt_digest="draft_solver_v1",
                    cost_tokens=24,
                )
            ]
        )
        existing_norm_ops = [op for op in parent_genome.typed_ops if op.kind == "normalize"]
        new_ops.extend(existing_norm_ops)
        if normalizer_id and all(op.normalizer_id != normalizer_id for op in existing_norm_ops):
            new_ops.append(
                TypedOp(
                    op_id=f"norm_{cand_id}",
                    input_colour="Code",
                    output_colour="Code",
                    kind="normalize",
                    normalizer_id=normalizer_id,
                    cost_tokens=0,
                )
            )
        tail_ops = [
            op for op in parent_genome.typed_ops if op.kind in ("check", "repair", "synthesize")
        ]
        new_ops.extend(
            tail_ops
            if tail_ops
            else [
                TypedOp(
                    op_id="seed_check",
                    input_colour="Code",
                    output_colour="Receipt",
                    kind="check",
                    checker_id="host.public_smoke",
                    cost_tokens=8,
                )
            ]
        )

        return CandidateStrandDeltaV1(
            candidate_id=cand_id,
            parent_genome_id=parent_genome.genome_id,
            derived_from_failures=(failure_id,),
            detector_rule=detector_rule,
            constraint_clause=constraint_clause,
            typed_ops=tuple(new_ops),
            operation_wire=operation_wire,
            normalizer_id=normalizer_id,
            authority_effect=AUTHORITY_NONE,
        )

    def screen_with_thymus(
        self,
        candidate: CandidateStrandDeltaV1,
        clean_self_panel: Sequence[str],
    ) -> ThymusSelectionResult:
        """Stage 3 (ThymusGate Zero-False-Refusal Screen via Rust pfp_immune + EIS ThymusGate)."""
        if type(candidate) is not CandidateStrandDeltaV1:
            raise TypeError("candidate must be an exact CandidateStrandDeltaV1")
        if isinstance(clean_self_panel, (str, bytes)) or not clean_self_panel:
            raise ValueError("EMPTY_SELF_PANEL: clean_self_panel must contain at least one clean fixture")
        panel_list = [str(item) for item in clean_self_panel]

        gate = ThymusGate(self_panel=panel_list)
        py_result = gate.evaluate_rule(candidate.detector_rule)

        # Cross-verify with Rust pfp_immune screen via immunity.screen_rules when regex-bound.
        if candidate.detector_rule.matcher_id == REGEX_MATCHER_ID and py_result.self_fixtures_tested > 0:
            admitted_rules, killed_records = immunity.screen_rules([candidate.detector_rule], panel_list)
            rust_admitted = len(admitted_rules) == 1 and len(killed_records) == 0
            if not rust_admitted and py_result.is_admitted:
                return ThymusSelectionResult(
                    rule_id=candidate.detector_rule.rule_id,
                    is_admitted=False,
                    self_fixtures_tested=len(panel_list),
                    autoimmune_violations=max(1, len(killed_records)),
                    first_violating_sample=panel_list[0][:120],
                    rationale=f"Purged by native pfp_immune screen: {killed_records}",
                )
        return py_result

    def _run_genome_normalizers(self, genome: StrandGenomeV1, text: str) -> str:
        out = text
        for norm_id in genome.normalizer_ids:
            norm_fn = self._normalizers.get(norm_id)
            if norm_fn is not None:
                out = norm_fn(out)
        return out

    def _build_repair_prompt(
        self,
        genome: StrandGenomeV1,
        normalized: str,
        initial_outcome: HostCheckOutcomeV1,
        danger: Signal2Danger | None,
        matches: tuple[Signal1Match, ...],
    ) -> str:
        s1_diagnostics = [
            f"{m.detector_id} ({m.epitope_name}): {genome.rule_constraints.get(m.detector_id, m.pattern_matched)}"
            for m in matches
        ]
        return (
            "REPAIR_REQUEST: Fix all host predicate obstructions while preserving fenced contracts.\n"
            f"Failed host predicates: {list(initial_outcome.failed_predicates)}\n"
            f"Danger kind: {danger.danger_type if danger is not None else 'NONE'}\n"
            f"Signal 1 rule diagnostics: {s1_diagnostics}\n"
            f"Previous answer:\n{normalized}"
        )

    def apply_active_regulation(
        self,
        genome: StrandGenomeV1,
        draft_reply: str,
        host_checker: Callable[[str], HostCheckOutcomeV1],
        repair_generator: Callable[[str], str] | None = None,
    ) -> RegulatedAttemptReceiptV1:
        """Stage 5 (Next Task Active Regulation): Signal 1 pre-normalization, host check, and enriched repair."""
        if type(genome) is not StrandGenomeV1 or not isinstance(draft_reply, str) or not callable(host_checker):
            raise TypeError("apply_active_regulation requires (StrandGenomeV1, str, callable)")

        active_rules = [r for r in genome.admitted_rules if r.is_active]
        initial_matches = tuple(immunity.signal1(draft_reply, active_rules))
        should_norm = bool(genome.normalizer_ids) and (
            bool(initial_matches) or any(op.kind == "normalize" for op in genome.typed_ops)
        )
        normalized = self._run_genome_normalizers(genome, draft_reply) if should_norm else draft_reply
        normalization_applied = normalized != draft_reply

        post_norm_matches = tuple(immunity.signal1(normalized, active_rules))
        initial_outcome = host_checker(normalized)
        if type(initial_outcome) is not HostCheckOutcomeV1:
            raise TypeError("host_checker must return an exact HostCheckOutcomeV1")

        danger = initial_outcome.to_signal2_danger()
        decision = immunity.decide(list(post_norm_matches), danger)
        total_tokens = genome.active_prompt_tokens + estimate_token_count(draft_reply)

        if initial_outcome.passed:
            return RegulatedAttemptReceiptV1(
                genome_id=genome.genome_id,
                initial_reply=draft_reply,
                normalized_reply=normalized,
                final_reply=normalized,
                normalization_applied=normalization_applied,
                signal1_matches=initial_matches,
                matched_rule_ids=tuple(m.detector_id for m in initial_matches),
                matched_constraints=tuple(
                    genome.rule_constraints.get(m.detector_id, m.epitope_name) for m in initial_matches
                ),
                initial_host_outcome=initial_outcome,
                final_host_outcome=initial_outcome,
                immune_disposition=decision.disposition,
                repair_triggered=False,
                repair_prompt=None,
                certified=True,
                calls_used=1,
                tokens_used=total_tokens,
            )

        all_matches = initial_matches if initial_matches else post_norm_matches
        repair_prompt = self._build_repair_prompt(genome, normalized, initial_outcome, danger, all_matches)
        effective_repair = repair_generator if repair_generator is not None else self._default_repair_generator
        matched_ids = tuple(m.detector_id for m in all_matches)
        matched_cons = tuple(genome.rule_constraints.get(m.detector_id, m.epitope_name) for m in all_matches)

        if effective_repair is None:
            return RegulatedAttemptReceiptV1(
                genome_id=genome.genome_id,
                initial_reply=draft_reply,
                normalized_reply=normalized,
                final_reply=normalized,
                normalization_applied=normalization_applied,
                signal1_matches=all_matches,
                matched_rule_ids=matched_ids,
                matched_constraints=matched_cons,
                initial_host_outcome=initial_outcome,
                final_host_outcome=initial_outcome,
                immune_disposition=decision.disposition,
                repair_triggered=False,
                repair_prompt=repair_prompt,
                certified=False,
                calls_used=1,
                tokens_used=total_tokens,
            )

        repaired_raw = effective_repair(repair_prompt)
        if not isinstance(repaired_raw, str):
            raise TypeError("repair_generator must return a str")
        repaired_norm = self._run_genome_normalizers(genome, repaired_raw)
        final_outcome = host_checker(repaired_norm)
        if type(final_outcome) is not HostCheckOutcomeV1:
            raise TypeError("host_checker must return an exact HostCheckOutcomeV1")
        final_decision = immunity.decide(
            immunity.signal1(repaired_norm, active_rules), final_outcome.to_signal2_danger()
        )
        repair_tokens = estimate_token_count(repair_prompt) + estimate_token_count(repaired_raw)
        return RegulatedAttemptReceiptV1(
            genome_id=genome.genome_id,
            initial_reply=draft_reply,
            normalized_reply=normalized,
            final_reply=repaired_norm,
            normalization_applied=normalization_applied or (repaired_norm != repaired_raw),
            signal1_matches=all_matches,
            matched_rule_ids=matched_ids,
            matched_constraints=matched_cons,
            initial_host_outcome=initial_outcome,
            final_host_outcome=final_outcome,
            immune_disposition=final_decision.disposition,
            repair_triggered=True,
            repair_prompt=repair_prompt,
            certified=final_outcome.passed,
            calls_used=2,
            tokens_used=total_tokens + repair_tokens,
        )

    def _evaluate_genome_on_case(
        self,
        genome: StrandGenomeV1,
        vc: ValidationCaseV1,
        *,
        is_treated: bool,
    ) -> tuple[bool, int, int]:
        """Evaluate a genome on one held-out ValidationCaseV1, returning (passed, tokens, microusd)."""
        exp_tokens = vc.treated_tokens if is_treated else vc.baseline_tokens
        exp_usd = vc.treated_microusd if is_treated else vc.baseline_microusd
        if vc.host_checker is None:
            passed = bool(vc.treated_passed if is_treated else vc.baseline_passed)
            tokens = exp_tokens if exp_tokens is not None else genome.active_prompt_tokens
            microusd = exp_usd if exp_usd is not None else max(1, tokens * 3)
            return passed, tokens, microusd

        if vc.attempt_generator is not None:
            gen_fn = vc.attempt_generator
            draft = gen_fn(genome, None)

            def _gen_rep(rp: str) -> str:
                return gen_fn(genome, rp)

            repair_fn: Callable[[str], str] | None = _gen_rep
        elif vc.repaired_reply is not None:
            draft = vc.draft_reply

            def _rep(rep_prompt: str) -> str:
                if vc.repaired_reply is not None and (
                    "Signal 1 rule diagnostics: []" not in rep_prompt or bool(genome.admitted_rules)
                ):
                    return vc.repaired_reply
                return draft

            repair_fn = _rep
        else:
            draft = vc.draft_reply
            repair_fn = None

        receipt = self.apply_active_regulation(genome, draft, vc.host_checker, repair_generator=repair_fn)
        tokens = exp_tokens if exp_tokens is not None else receipt.tokens_used
        microusd = exp_usd if exp_usd is not None else max(1, tokens * 3)
        return receipt.certified, tokens, microusd

    def _ensure_failures_and_candidate_in_ledger(self, candidate: CandidateStrandDeltaV1) -> None:
        for fid in candidate.derived_from_failures:
            if fid not in self._recorded_failures:
                evidence_sha = sha256_hex(f"failure:{fid}")
                res = operad_ledger.record_failure(
                    self._ledger_path,
                    failure_id=fid,
                    workflow=self.workflow_id,
                    run="outer_loop_run",
                    failure_class="StructuralNonFit",
                    ddc_trace="CRM",
                    evidence_sha256=evidence_sha,
                )
                if res.get("status") != "PASS" and res.get("refusal", {}).get("code") != "DUPLICATE_ID":
                    raise operad_ledger.OperadLedgerError(f"LEDGER_FAILURE_APPEND_FAILED: {res}")
                self._recorded_failures[fid] = evidence_sha

        if candidate.candidate_id not in self._proposed_candidates:
            prop_res = operad_ledger.propose_candidate(
                self._ledger_path,
                candidate_id=candidate.candidate_id,
                capability_kind="antibody",
                constraint=candidate.constraint_clause,
                derived_from=candidate.derived_from_failures,
            )
            if prop_res.get("status") != "PASS" and prop_res.get("refusal", {}).get("code") != "DUPLICATE_ID":
                raise operad_ledger.OperadLedgerError(f"LEDGER_CANDIDATE_APPEND_FAILED: {prop_res}")
            self._proposed_candidates.add(candidate.candidate_id)

    def _validate_eval_inputs(
        self,
        incumbent: StrandGenomeV1,
        candidate: CandidateStrandDeltaV1,
        validation_slice: Sequence[ValidationCaseV1],
    ) -> tuple[tuple[ValidationCaseV1, ...], list[str]]:
        if type(incumbent) is not StrandGenomeV1 or type(candidate) is not CandidateStrandDeltaV1:
            raise TypeError("evaluate_and_compress requires exact StrandGenomeV1 and CandidateStrandDeltaV1")
        if not validation_slice:
            raise ValueError("EMPTY_VALIDATION_SLICE: validation_slice must contain at least one held-out case")
        val_cases = tuple(validation_slice)
        if any(type(vc) is not ValidationCaseV1 for vc in val_cases):
            raise TypeError("validation_slice elements must be exact ValidationCaseV1 instances")
        case_ids = [vc.case_id for vc in val_cases]
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("DUPLICATE_VALIDATION_CASE: validation_slice case_ids must be distinct")
        failure_stems = {_case_stem(fid) for fid in candidate.derived_from_failures}
        overlapping = [vc.case_id for vc in val_cases if _case_stem(vc.case_id) in failure_stems]
        if overlapping:
            raise ValueError(
                f"SPLIT_OVERLAP: held-out validation cases {overlapping} overlap "
                f"derived_from_failures {list(candidate.derived_from_failures)}"
            )
        return val_cases, case_ids

    def _run_paired_slice(
        self,
        incumbent: StrandGenomeV1,
        trial_genome: StrandGenomeV1,
        val_cases: tuple[ValidationCaseV1, ...],
    ) -> tuple[int, int, int, int, int, int, int, list[_PairedSelectionRow], list[_PairedSelectionRow]]:
        b_ok = t_ok = b_tok = t_tok = b_usd = t_usd = hits = 0
        inc_rows: list[_PairedSelectionRow] = []
        cand_rows: list[_PairedSelectionRow] = []
        for vc in val_cases:
            bp, bt, bu = self._evaluate_genome_on_case(incumbent, vc, is_treated=False)
            tp, tt, tu = self._evaluate_genome_on_case(trial_genome, vc, is_treated=True)
            b_ok += int(bp)
            t_ok += int(tp)
            hits += int(bp and not tp)
            b_tok += bt
            t_tok += tt
            b_usd += bu
            t_usd += tu
            inc_rows.append(_PairedSelectionRow(vc.case_id, vc.family, 0, int(bp), bt))
            cand_rows.append(_PairedSelectionRow(vc.case_id, vc.family, 0, int(tp), tt))
        return b_ok, t_ok, b_tok, t_tok, b_usd, t_usd, hits, inc_rows, cand_rows

    def _admit_accuracy_promotion(
        self,
        incumbent: StrandGenomeV1,
        candidate: CandidateStrandDeltaV1,
        trial_seq: int,
    ) -> tuple[StrandGenomeV1, str]:
        adm = operad_ledger.record_admission(
            self._ledger_path, candidate_id=candidate.candidate_id, trial_seq=trial_seq
        )
        if adm.get("status") != "PASS":
            raise operad_ledger.OperadLedgerError(f"LEDGER_ADMISSION_REFUSED: {adm.get('refusal')}")
        loaded = operad_host.call(
            ("ledger", "load", str(self._ledger_path)), {"seed_prompt": incumbent.base_prompt}
        )
        if loaded.get("status") != "PASS":
            raise operad_ledger.OperadLedgerError(f"LEDGER_LOAD_FAILED: {loaded}")
        head = str(loaded["result"]["ledger_head"])
        adopted = incumbent.apply_delta(candidate, ledger_head=head)
        self.lineage.add(adopted.genome_id)
        self.lineage.derive(incumbent.genome_id, adopted.genome_id, PROMOTE_ACCURACY)
        return adopted, head

    def evaluate_and_compress(
        self,
        incumbent: StrandGenomeV1,
        candidate: CandidateStrandDeltaV1,
        validation_slice: Sequence[ValidationCaseV1],
        clean_self_panel: Sequence[str],
        *,
        task_id: str | None = None,
    ) -> tuple[StrandGenomeV1, OuterLoopStepReceiptV1]:
        """Stages 3-4: Thymus negative selection, Operad trace quotient, held-out trial, and PCIV Pareto gate."""
        val_cases, case_ids = self._validate_eval_inputs(incumbent, candidate, validation_slice)
        self._step_counter += 1
        step_idx = self._step_counter
        eff_task = task_id or _case_stem(candidate.derived_from_failures[0])
        self.lineage.add(incumbent.genome_id)
        self._evaluated_trace_pool.setdefault(incumbent.canonical_trace_digest, incumbent.genome_id)
        cand_digest = candidate.canonical_trace_digest

        thymus_result = self.screen_with_thymus(candidate, clean_self_panel)
        if not thymus_result.is_admitted or thymus_result.autoimmune_violations > 0:
            self.lineage.add(candidate.candidate_id)
            self.lineage.derive(incumbent.genome_id, candidate.candidate_id, "autoimmune_purged")
            self.tainted_genomes = self.lineage.taint(self.tainted_genomes | {candidate.candidate_id})
            return incumbent, OuterLoopStepReceiptV1(
                step_idx, eff_task, incumbent.genome_id, incumbent.genome_id, False,
                max(1, thymus_result.autoimmune_violations), False, cand_digest,
                Fraction(0, 1), Fraction(0, 1), 0, 0, 0, REJECT_AUTOIMMUNE, self.current_ledger_head(),
            )

        q_classes = operad_pipe.quotient_workflows(
            {"incumbent": list(incumbent.typed_ops), "candidate": list(candidate.typed_ops)}
        )
        if (cand_digest in self._evaluated_trace_pool or len(q_classes.get(cand_digest, [])) > 1) and (
            not candidate.replaces_constraints
        ):
            return incumbent, OuterLoopStepReceiptV1(
                step_idx, eff_task, incumbent.genome_id, incumbent.genome_id, True, 0, True, cand_digest,
                Fraction(0, 1), Fraction(0, 1), 0, 0, 0, COLLAPSE_QUOTIENT, self.current_ledger_head(),
            )

        self._evaluated_trace_pool[cand_digest] = candidate.candidate_id
        trial_genome = incumbent.apply_delta(candidate)
        b_ok, t_ok, b_tok, t_tok, b_usd, t_usd, hits, inc_rows, cand_rows = self._run_paired_slice(
            incumbent, trial_genome, val_cases
        )
        n_cases = len(val_cases)
        b_rate, t_rate = Fraction(b_ok, n_cases), Fraction(t_ok, n_cases)

        self._ensure_failures_and_candidate_in_ledger(candidate)
        trial_out = operad_ledger.record_trial(
            self._ledger_path,
            candidate_id=candidate.candidate_id,
            held_out=case_ids,
            baseline_correct=b_ok,
            treated_correct=t_ok,
            clean_panel_hits=hits,
        )
        if trial_out.get("status") != "PASS":
            raise operad_ledger.OperadLedgerError(f"LEDGER_TRIAL_REFUSED: {trial_out.get('refusal')}")
        trial_seq = int(trial_out["result"]["seq"])

        fam_regressed = any(
            pciv_research_metrics([r for r in cand_rows if r.family == fam])["correctness"]
            < pciv_research_metrics([r for r in inc_rows if r.family == fam])["correctness"]
            for fam in {r.family for r in cand_rows}
        )
        if hits > 0 or t_rate < b_rate or fam_regressed:
            return incumbent, OuterLoopStepReceiptV1(
                step_idx, eff_task, incumbent.genome_id, incumbent.genome_id, True, 0, False, cand_digest,
                b_rate, t_rate, b_tok, t_tok, hits, REJECT_REGRESSION, self.current_ledger_head(),
            )

        fronts = ParetoFrontSelectorV1().partition_fronts(
            [
                {"id": candidate.candidate_id, "metrics": {"correctness": t_rate, "cost": Fraction(t_tok, 1)}},
                {"id": incumbent.genome_id, "metrics": {"correctness": b_rate, "cost": Fraction(b_tok, 1)}},
            ]
        )
        on_front = any(item["id"] == candidate.candidate_id for item in fronts[0])
        if t_rate > b_rate and on_front:
            adopted, head = self._admit_accuracy_promotion(incumbent, candidate, trial_seq)
            return adopted, OuterLoopStepReceiptV1(
                step_idx, eff_task, incumbent.genome_id, adopted.genome_id, True, 0, False, cand_digest,
                b_rate, t_rate, b_tok, t_tok, 0, PROMOTE_ACCURACY, head,
            )

        inc_civ = civilization.Candidate(incumbent.genome_id, b_ok, n_cases, b_usd, b_tok, 1, True, True)
        trt_civ = civilization.Candidate(candidate.candidate_id, t_ok, n_cases, t_usd, t_tok, 1, True, False)
        if (
            t_rate == b_rate > Fraction(0, 1)
            and ((t_tok < b_tok) or (t_usd < b_usd))
            and civilization.dominates(trt_civ, inc_civ)
            and (pciv_research_improved(cand_rows, inc_rows) or t_usd < b_usd)
        ):
            head = self.current_ledger_head()
            adopted = incumbent.apply_delta(candidate, ledger_head=head)
            self.lineage.add(adopted.genome_id)
            self.lineage.derive(incumbent.genome_id, adopted.genome_id, PROMOTE_COMPRESSION)
            return adopted, OuterLoopStepReceiptV1(
                step_idx, eff_task, incumbent.genome_id, adopted.genome_id, True, 0, False, cand_digest,
                b_rate, t_rate, b_tok, t_tok, 0, PROMOTE_COMPRESSION, head,
            )

        return incumbent, OuterLoopStepReceiptV1(
            step_idx, eff_task, incumbent.genome_id, incumbent.genome_id, True, 0, False, cand_digest,
            b_rate, t_rate, b_tok, t_tok, 0, REJECT_BLOAT, self.current_ledger_head(),
        )


__all__ = [
    "AUTHORITY_NONE",
    "BUILTIN_NORMALIZERS",
    "COLLAPSE_QUOTIENT",
    "CandidateStrandDeltaV1",
    "ComparativeClaimAuditorV1",
    "CompiledWorkflowV1",
    "GENESIS_LEDGER_HEAD",
    "HostCheckOutcomeV1",
    "HostOracleContext",
    "OuterLoopCompressionControllerV1",
    "OuterLoopStepReceiptV1",
    "PCIV_DECISIONS",
    "PROMOTE_ACCURACY",
    "PROMOTE_COMPRESSION",
    "ProtectedContract",
    "REJECT_AUTOIMMUNE",
    "REJECT_BLOAT",
    "REJECT_REGRESSION",
    "RegulatedAttemptReceiptV1",
    "StrandGenomeV1",
    "TypedOp",
    "ValidationCaseV1",
    "WholeRunBudget",
    "compile_typed_workflow",
    "estimate_token_count",
    "hashlib",
    "pciv_research_decide",
]
