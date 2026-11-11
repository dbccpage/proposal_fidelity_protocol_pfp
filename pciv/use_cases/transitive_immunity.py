"""Fixed-point lineage taint, transitive backward immunity, operational workflow quotient,
and protected-span seed fencing for Prompt Civilization.

Remediates:
- SYS-PCIV-009: Order-dependent single-pass taint propagation replaced by exact
  least-fixed-point propagation over witnessed acyclic inheritance graphs.
- 1-hop backward immunity stub replaced by bounded shortest-hop reverse BFS with
  attenuation weights (1/2)^d and global custody revocation disarming.
- Syntactic duplicate workflow bloat collapsed via colour-typed adjacent idempotent
  reduction while preserving noncommuting stage orderings.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

_OPS_DIR = Path(__file__).resolve().parents[2] / "ops"
if _OPS_DIR.is_dir() and str(_OPS_DIR) not in sys.path:
    sys.path.insert(0, str(_OPS_DIR))

from pciv.domain.causal_witness import SealedCausalWitness, is_sealed_digest  # noqa: E402
from pciv.domain.models import ProtectedSpanV1  # noqa: E402
from pciv.use_cases.fitness import ParetoFrontSelectorV1  # noqa: E402
from pciv.use_cases.forge import PopulationPolicyV1, PromptMutationEngineV1  # noqa: E402
from pciv.use_cases.genealogy import (  # noqa: E402
    INHERITANCE_RELATIONSHIPS,
    LineageEdgeV1,
    LineageGraphV1,
    RelationshipType,
)
from pciv.use_cases.immunity import GlobalCustodyRegistryV1  # noqa: E402


def _relationship_value(rel: RelationshipType | str) -> str:
    return rel.value if isinstance(rel, RelationshipType) else str(rel)


def _verify_edge_witness(witness: Any, parent_id: str, child_id: str) -> None:
    if type(witness) is not SealedCausalWitness:
        raise ValueError("CAUSAL_WITNESS_REQUIRED: inheritance edge requires an exact SealedCausalWitness")
    if not isinstance(witness.canonical_body, str) or not is_sealed_digest(witness.receipt_sha256):
        raise ValueError("CAUSAL_WITNESS_REQUIRED: witness digest is not a sealed sha256")
    expected_digest = "sha256:" + hashlib.sha256(witness.canonical_body.encode("utf-8")).hexdigest()
    if witness.receipt_sha256 != expected_digest:
        raise ValueError("CAUSAL_WITNESS_REQUIRED: witness digest does not match its body")
    try:
        body = json.loads(witness.canonical_body)
    except json.JSONDecodeError as exc:
        raise ValueError("CAUSAL_WITNESS_REQUIRED: malformed witness body") from exc
    if not isinstance(body, dict) or body.get("parent_id") != parent_id or body.get("child_id") != child_id:
        raise ValueError("CAUSAL_WITNESS_REQUIRED: witness seal does not name this parent and child")


def _assert_acyclic(edges: Sequence[tuple[str, str]]) -> None:
    nodes: set[str] = set()
    adj: dict[str, set[str]] = {}
    indegree: dict[str, int] = {}

    for parent_id, child_id in edges:
        if parent_id == child_id:
            raise ValueError(f"LINEAGE_CYCLE_REFUSED: self-loop detected on node {parent_id!r}")
        nodes.add(parent_id)
        nodes.add(child_id)
        children = adj.setdefault(parent_id, set())
        if child_id not in children:
            children.add(child_id)
            indegree[child_id] = indegree.get(child_id, 0) + 1
        indegree.setdefault(parent_id, 0)

    ready = deque(sorted(node for node in nodes if indegree.get(node, 0) == 0))
    visited_count = 0
    while ready:
        curr = ready.popleft()
        visited_count += 1
        for nxt in sorted(adj.get(curr, ())):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)

    if visited_count != len(nodes):
        raise ValueError("LINEAGE_CYCLE_REFUSED: directed cycle detected in inheritance graph")


def _extract_inheritance_edges(
    graph_or_edges: LineageGraphV1 | Sequence[LineageEdgeV1] | Sequence[tuple[str, str]],
) -> list[tuple[str, str]]:
    if isinstance(graph_or_edges, LineageGraphV1):
        extracted: list[tuple[str, str]] = []
        for edge in graph_or_edges.edges:
            if _relationship_value(edge.relationship) in INHERITANCE_RELATIONSHIPS:
                _verify_edge_witness(edge.witness_receipt, edge.parent_id, edge.child_id)
                extracted.append((edge.parent_id, edge.child_id))
        _assert_acyclic(extracted)
        return extracted

    extracted_raw: list[tuple[str, str]] = []
    allowed_rels = {r.value for r in RelationshipType}
    for item in graph_or_edges:
        if isinstance(item, LineageEdgeV1):
            rel_val = _relationship_value(item.relationship)
            if rel_val not in allowed_rels:
                raise ValueError(f"CAUSAL_WITNESS_REQUIRED: unauthorized relationship {rel_val!r}")
            if rel_val in INHERITANCE_RELATIONSHIPS:
                _verify_edge_witness(item.witness_receipt, item.parent_id, item.child_id)
                extracted_raw.append((item.parent_id, item.child_id))
        elif (
            isinstance(item, tuple)
            and len(item) == 2
            and isinstance(item[0], str)
            and isinstance(item[1], str)
            and item[0].strip()
            and item[1].strip()
        ):
            extracted_raw.append((item[0], item[1]))
        else:
            raise TypeError("Expected LineageGraphV1, LineageEdgeV1 items, or (parent_id, child_id) string pairs")

    _assert_acyclic(extracted_raw)
    return extracted_raw


def _exact_fraction(value: Fraction | int, label: str, *, allow_negative: bool = False) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (Fraction, int)):
        raise TypeError(f"{label} must be an exact int or Fraction, got {type(value).__name__}")
    frac = Fraction(value)
    if not allow_negative and frac < 0:
        raise ValueError(f"{label} must be non-negative, got {frac}")
    return frac


# =============================================================================
# 1. FixedPointLineageTaintEngineV1
# =============================================================================


class FixedPointLineageTaintEngineV1:
    """Order-independent least-fixed-point lineage taint propagation engine.

    Supports:
    - policy_rule="OR": any tainted ancestor taints all reachable descendants.
    - policy_rule="QUORUM" with quorum_k >= 1: a node becomes tainted once at least
      quorum_k distinct direct inheritance parents are tainted, iterated to convergence.
    """

    def __init__(
        self,
        *,
        policy_rule: str = "OR",
        quorum_k: int = 1,
        initial_tainted: Iterable[str] = (),
    ) -> None:
        if policy_rule not in {"OR", "QUORUM"}:
            raise ValueError(f"INVALID_TAINT_POLICY: unsupported policy_rule {policy_rule!r}")
        if isinstance(quorum_k, bool) or not isinstance(quorum_k, int) or quorum_k < 1:
            raise ValueError("INVALID_QUORUM_K: quorum_k must be an exact integer >= 1")
        self.policy_rule = policy_rule
        self.quorum_k = quorum_k
        self._tainted_nodes: set[str] = set()
        for node_id in initial_tainted:
            self.mark_tainted(node_id)

    def mark_tainted(self, node_id: str) -> None:
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("node_id must be a non-empty string")
        self._tainted_nodes.add(node_id)

    def is_tainted(self, node_id: str) -> bool:
        return node_id in self._tainted_nodes

    def tainted_nodes(self) -> frozenset[str]:
        return frozenset(self._tainted_nodes)

    def propagate_taint(
        self,
        graph_or_edges: LineageGraphV1 | Sequence[LineageEdgeV1] | Sequence[tuple[str, str]],
    ) -> frozenset[str]:
        edges = _extract_inheritance_edges(graph_or_edges)
        parents_of: dict[str, set[str]] = {}
        for parent_id, child_id in edges:
            parents_of.setdefault(child_id, set()).add(parent_id)

        threshold = 1 if self.policy_rule == "OR" else self.quorum_k
        tainted = set(self._tainted_nodes)

        changed = True
        ordered_children = sorted(parents_of.keys())
        while changed:
            changed = False
            for child_id in ordered_children:
                if child_id in tainted:
                    continue
                tainted_parent_count = sum(1 for parent_id in parents_of[child_id] if parent_id in tainted)
                if tainted_parent_count >= threshold:
                    tainted.add(child_id)
                    changed = True

        self._tainted_nodes = tainted
        return frozenset(self._tainted_nodes)


# =============================================================================
# 2. TransitiveImmunityEngineV1
# =============================================================================


@dataclass(frozen=True, slots=True)
class BackwardAttributionReceipt:
    """Bounded reverse-lineage attribution record with exact (1/2)^d attenuation."""

    ancestor_id: str
    hop_distance: int
    attenuation_weight: Fraction
    rule_id: str
    armed: bool
    authority_effect: str = "None"


class TransitiveImmunityEngineV1:
    """Propagates acquired antibody attribution backward across witnessed inheritance edges."""

    def __init__(self, max_backward_hops: int = 10) -> None:
        if isinstance(max_backward_hops, bool) or not isinstance(max_backward_hops, int) or max_backward_hops < 0:
            raise ValueError("max_backward_hops must be an exact non-negative integer")
        self.max_backward_hops = max_backward_hops

    def propagate_backward(
        self,
        *,
        graph_or_edges: LineageGraphV1 | Sequence[LineageEdgeV1] | Sequence[tuple[str, str]],
        current_prompt_id: str,
        rule_id: str,
        max_backward_hops: int | None = None,
        pretend_as_new_origin: bool = False,
        custody_registry: GlobalCustodyRegistryV1 | None = None,
    ) -> tuple[BackwardAttributionReceipt, ...]:
        if pretend_as_new_origin:
            raise ValueError(
                "HORIZON_RESET_PROHIBITED: relaying child prompt cannot reset origin for backward propagation"
            )
        if not isinstance(current_prompt_id, str) or not current_prompt_id.strip():
            raise ValueError("current_prompt_id must be a non-empty string")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError("rule_id must be a non-empty string")

        hop_limit = self.max_backward_hops if max_backward_hops is None else max_backward_hops
        if isinstance(hop_limit, bool) or not isinstance(hop_limit, int) or hop_limit < 0:
            raise ValueError("max_backward_hops must be an exact non-negative integer")

        edges = _extract_inheritance_edges(graph_or_edges)
        reverse_adj: dict[str, set[str]] = {}
        for parent_id, child_id in edges:
            reverse_adj.setdefault(child_id, set()).add(parent_id)

        visited: set[str] = {current_prompt_id}
        queue: deque[tuple[str, int]] = deque([(current_prompt_id, 0)])
        discovered: list[tuple[int, str]] = []

        while queue:
            node_id, dist = queue.popleft()
            if dist >= hop_limit:
                continue
            for parent_id in sorted(reverse_adj.get(node_id, ())):
                if parent_id not in visited:
                    visited.add(parent_id)
                    next_dist = dist + 1
                    discovered.append((next_dist, parent_id))
                    queue.append((parent_id, next_dist))

        discovered.sort(key=lambda item: (item[0], item[1]))
        receipts: list[BackwardAttributionReceipt] = []
        for hop_distance, ancestor_id in discovered:
            if custody_registry is not None:
                custody_registry.bind_antibody(ancestor_id, rule_id)
                is_armed = custody_registry.is_armed(ancestor_id, rule_id)
            else:
                is_armed = True
            receipts.append(
                BackwardAttributionReceipt(
                    ancestor_id=ancestor_id,
                    hop_distance=hop_distance,
                    attenuation_weight=Fraction(1, 2**hop_distance),
                    rule_id=rule_id,
                    armed=is_armed,
                )
            )

        return tuple(receipts)

    @staticmethod
    def refresh_custody(
        receipts: Sequence[BackwardAttributionReceipt],
        custody_registry: GlobalCustodyRegistryV1,
    ) -> tuple[BackwardAttributionReceipt, ...]:
        """Re-evaluate armed status against current GlobalCustodyRegistryV1 revocations."""
        return tuple(
            BackwardAttributionReceipt(
                ancestor_id=r.ancestor_id,
                hop_distance=r.hop_distance,
                attenuation_weight=r.attenuation_weight,
                rule_id=r.rule_id,
                armed=custody_registry.is_armed(r.ancestor_id, r.rule_id),
                authority_effect=r.authority_effect,
            )
            for r in receipts
        )


# =============================================================================
# 3. OperationalWorkflowQuotientV1
# =============================================================================


@dataclass(frozen=True, slots=True)
class WorkflowStageSpec:
    """Colour-typed stage operation inside a candidate workflow pipeline."""

    op_kind: str
    input_colour: str
    output_colour: str
    instruction_or_checker_id: str
    idempotent: bool = False

    def __post_init__(self) -> None:
        for field_name in ("op_kind", "input_colour", "output_colour", "instruction_or_checker_id"):
            val = getattr(self, field_name)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.idempotent, bool):
            raise TypeError("idempotent must be a bool")

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "idempotent": self.idempotent,
            "input_colour": self.input_colour,
            "instruction_or_checker_id": self.instruction_or_checker_id,
            "op_kind": self.op_kind,
            "output_colour": self.output_colour,
        }


@dataclass(frozen=True, slots=True)
class CandidateWorkflowSpec:
    """Candidate workflow specification submitted for operational quotienting."""

    workflow_id: str
    stages: tuple[WorkflowStageSpec, ...]
    obligation_pass_fraction: Fraction | None = None
    byte_or_token_cost: Fraction = Fraction(0, 1)
    is_baseline: bool = False

    def __init__(
        self,
        workflow_id: str,
        stages: Sequence[WorkflowStageSpec],
        *,
        obligation_pass_fraction: Fraction | int | None = None,
        byte_or_token_cost: Fraction | int = 0,
        is_baseline: bool = False,
    ) -> None:
        if not isinstance(workflow_id, str) or not workflow_id.strip():
            raise ValueError("workflow_id must be a non-empty string")
        stage_tuple = tuple(stages)
        if not stage_tuple:
            raise ValueError(f"EMPTY_WORKFLOW_STAGES: workflow {workflow_id!r} must contain at least one stage")
        for s in stage_tuple:
            if not isinstance(s, WorkflowStageSpec):
                raise TypeError("Every stage must be a WorkflowStageSpec")
        pass_frac = (
            None
            if obligation_pass_fraction is None
            else _exact_fraction(obligation_pass_fraction, "obligation_pass_fraction")
        )
        cost_frac = _exact_fraction(byte_or_token_cost, "byte_or_token_cost")
        if not isinstance(is_baseline, bool):
            raise TypeError("is_baseline must be a bool")

        object.__setattr__(self, "workflow_id", workflow_id)
        object.__setattr__(self, "stages", stage_tuple)
        object.__setattr__(self, "obligation_pass_fraction", pass_frac)
        object.__setattr__(self, "byte_or_token_cost", cost_frac)
        object.__setattr__(self, "is_baseline", is_baseline)


@dataclass(frozen=True, slots=True)
class QuotientClassRepresentativeV1:
    """Canonical normal-form representative of an operational equivalence class."""

    workflow: CandidateWorkflowSpec
    canonical_stages: tuple[WorkflowStageSpec, ...]
    canonical_trace_sha256: str
    collapsed_member_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReserveAllocationResultV1:
    """Ecological 60/30/10 reserve quotas and Pareto-ranked bucket assignments."""

    reserve_quotas: dict[str, int]
    pareto_fronts: tuple[tuple[str, ...], ...]
    buckets: dict[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class OperationalQuotientReportV1:
    """Complete operational workflow quotient and ecological reserve report."""

    representatives: tuple[QuotientClassRepresentativeV1, ...]
    collapsed_duplicates: tuple[CandidateWorkflowSpec, ...]
    reserve_allocation: ReserveAllocationResultV1


class OperationalWorkflowQuotientV1:
    """Quotients colour-typed workflows up to adjacent idempotent reduction without commuting stages."""

    def __init__(
        self,
        *,
        population_policy: PopulationPolicyV1 | None = None,
        pareto_selector: ParetoFrontSelectorV1 | None = None,
    ) -> None:
        self._population_policy = population_policy or PopulationPolicyV1()
        self._pareto_selector = pareto_selector or ParetoFrontSelectorV1()

    @staticmethod
    def validate_and_reduce_stages(stages: Sequence[WorkflowStageSpec]) -> tuple[WorkflowStageSpec, ...]:
        if not stages:
            raise ValueError("EMPTY_WORKFLOW_STAGES: stages sequence must be non-empty")

        for idx in range(len(stages) - 1):
            out_col = stages[idx].output_colour
            in_col = stages[idx + 1].input_colour
            if out_col != in_col:
                raise ValueError(
                    f"PORT_MISMATCH: stage {idx} ({stages[idx].op_kind}) output_colour {out_col!r} "
                    f"does not match stage {idx + 1} ({stages[idx + 1].op_kind}) input_colour {in_col!r}"
                )

        reduced: list[WorkflowStageSpec] = []
        for stage in stages:
            if reduced and stage.idempotent and reduced[-1] == stage:
                continue
            reduced.append(stage)
        return tuple(reduced)

    @classmethod
    def compute_canonical_trace(cls, workflow: CandidateWorkflowSpec) -> tuple[tuple[WorkflowStageSpec, ...], str]:
        canonical_stages = cls.validate_and_reduce_stages(workflow.stages)
        trace_payload = {
            "domain_colour": canonical_stages[0].input_colour,
            "codomain_colour": canonical_stages[-1].output_colour,
            "canonical_stages": [stage.to_canonical_dict() for stage in canonical_stages],
        }
        encoded = json.dumps(
            trace_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
        return canonical_stages, digest

    def quotient(
        self,
        workflows: Sequence[CandidateWorkflowSpec],
    ) -> tuple[tuple[QuotientClassRepresentativeV1, ...], tuple[CandidateWorkflowSpec, ...]]:
        if not workflows:
            raise ValueError("EMPTY_WORKFLOW_POPULATION: workflows sequence cannot be empty")

        seen_ids: set[str] = set()
        classes: dict[str, list[tuple[CandidateWorkflowSpec, tuple[WorkflowStageSpec, ...]]]] = {}
        class_order: list[str] = []

        for wf in workflows:
            if wf.workflow_id in seen_ids:
                raise ValueError(f"DUPLICATE_WORKFLOW_ID: {wf.workflow_id!r}")
            seen_ids.add(wf.workflow_id)
            canonical_stages, trace_sha256 = self.compute_canonical_trace(wf)
            if trace_sha256 not in classes:
                classes[trace_sha256] = []
                class_order.append(trace_sha256)
            classes[trace_sha256].append((wf, canonical_stages))

        representatives: list[QuotientClassRepresentativeV1] = []
        collapsed_duplicates: list[CandidateWorkflowSpec] = []

        for trace_sha256 in class_order:
            members = classes[trace_sha256]
            members_sorted = sorted(
                members,
                key=lambda item: (len(item[0].stages), item[0].byte_or_token_cost, item[0].workflow_id),
            )
            winner_wf, canonical_stages = members_sorted[0]
            dups = [item[0] for item in members_sorted[1:]]
            collapsed_duplicates.extend(dups)
            representatives.append(
                QuotientClassRepresentativeV1(
                    workflow=winner_wf,
                    canonical_stages=canonical_stages,
                    canonical_trace_sha256=trace_sha256,
                    collapsed_member_ids=tuple(d.workflow_id for d in dups),
                )
            )

        return tuple(representatives), tuple(collapsed_duplicates)

    @staticmethod
    def _fill_bucket(candidate_ids: Sequence[str], limit: int, assigned: set[str]) -> tuple[str, ...]:
        selected: list[str] = []
        for wf_id in candidate_ids:
            if len(selected) >= limit:
                break
            if wf_id not in assigned:
                selected.append(wf_id)
                assigned.add(wf_id)
        return tuple(selected)

    def allocate_ecological_reserves(
        self,
        representatives: Sequence[QuotientClassRepresentativeV1],
        *,
        reserve_cap: int | None = None,
    ) -> ReserveAllocationResultV1:
        cap = len(representatives) if reserve_cap is None else reserve_cap
        if isinstance(cap, bool) or not isinstance(cap, int) or cap <= 0:
            raise ValueError("reserve_cap must be a positive integer")

        quotas = self._population_policy.allocate_reserves(cap)

        measured_inputs: list[dict[str, Any]] = []
        unmeasured_reps: list[QuotientClassRepresentativeV1] = []
        baseline_reps: list[QuotientClassRepresentativeV1] = []

        for rep in representatives:
            wf = rep.workflow
            if wf.is_baseline:
                baseline_reps.append(rep)
            if wf.obligation_pass_fraction is None:
                unmeasured_reps.append(rep)
            else:
                measured_inputs.append(
                    {
                        "id": wf.workflow_id,
                        "metrics": {
                            "correctness": wf.obligation_pass_fraction,
                            "cost": wf.byte_or_token_cost,
                        },
                    }
                )

        if not measured_inputs:
            fronts_raw = []
        elif len(measured_inputs) == 1:
            # Guard single-element population against pinned ParetoFrontSelectorV1 closure quirk
            fronts_raw = [list(measured_inputs)]
        else:
            fronts_raw = self._pareto_selector.partition_fronts(measured_inputs)
        pareto_fronts = tuple(tuple(str(entry["id"]) for entry in front) for front in fronts_raw)
        pareto_ranked_ids = [wf_id for front in pareto_fronts for wf_id in front]

        baseline_ids = [
            r.workflow.workflow_id
            for r in sorted(
                baseline_reps,
                key=lambda r: (
                    -(r.workflow.obligation_pass_fraction or Fraction(-1, 1)),
                    r.workflow.byte_or_token_cost,
                    r.workflow.workflow_id,
                ),
            )
        ]
        unmeasured_ids = [
            r.workflow.workflow_id
            for r in sorted(
                unmeasured_reps,
                key=lambda r: (r.workflow.byte_or_token_cost, r.workflow.workflow_id),
            )
        ]

        assigned: set[str] = set()
        baseline_bucket = self._fill_bucket(baseline_ids, quotas["Baseline"], assigned)
        unmeasured_bucket = self._fill_bucket(unmeasured_ids, quotas["Unmeasured"], assigned)
        front_bucket = self._fill_bucket(pareto_ranked_ids, quotas["Front"], assigned)

        return ReserveAllocationResultV1(
            reserve_quotas=dict(quotas),
            pareto_fronts=pareto_fronts,
            buckets={
                "Front": front_bucket,
                "Unmeasured": unmeasured_bucket,
                "Baseline": baseline_bucket,
            },
        )

    def evaluate(
        self,
        workflows: Sequence[CandidateWorkflowSpec],
        *,
        reserve_cap: int = 10,
    ) -> OperationalQuotientReportV1:
        representatives, collapsed_duplicates = self.quotient(workflows)
        reserve_allocation = self.allocate_ecological_reserves(representatives, reserve_cap=reserve_cap)
        return OperationalQuotientReportV1(
            representatives=representatives,
            collapsed_duplicates=collapsed_duplicates,
            reserve_allocation=reserve_allocation,
        )


# =============================================================================
# 4. ProtectedSpanEvolutionV1
# =============================================================================


@dataclass(frozen=True, slots=True)
class FencedPromptArtifactV1:
    """Composite prompt bytes carrying a byte-fenced immutable seed span."""

    composite_bytes: bytes
    seed_span: ProtectedSpanV1
    seed_bytes: bytes
    seed_sha256: str
    extra_protected_spans: tuple[ProtectedSpanV1, ...] = ()


class ProtectedSpanEvolutionV1:
    """Wraps PromptMutationEngineV1 + ProtectedSpanV1 to preserve exact seed bytes across mutations."""

    def __init__(self, mutation_engine: PromptMutationEngineV1 | None = None) -> None:
        self._mutation_engine = mutation_engine or PromptMutationEngineV1()

    @staticmethod
    def verify_seed_integrity(
        artifact: FencedPromptArtifactV1,
        *,
        expected_seed_bytes: bytes | None = None,
        expected_seed_sha256: str | None = None,
    ) -> bool:
        span = artifact.seed_span
        if span.end_byte > len(artifact.composite_bytes):
            raise ValueError("SEED_FENCE_INTEGRITY_VIOLATION: seed_span exceeds composite_bytes length")
        extracted = artifact.composite_bytes[span.start_byte : span.end_byte]
        target_bytes = artifact.seed_bytes if expected_seed_bytes is None else expected_seed_bytes
        target_sha256 = artifact.seed_sha256 if expected_seed_sha256 is None else expected_seed_sha256
        extracted_sha256 = hashlib.sha256(extracted).hexdigest()
        if extracted != target_bytes or extracted_sha256 != target_sha256:
            raise ValueError(
                "SEED_FENCE_INTEGRITY_VIOLATION: extracted seed span bytes or SHA-256 diverged from frozen seed"
            )
        return True

    def create_fenced_template(
        self,
        *,
        prefix_bytes: bytes,
        seed_bytes: bytes,
        suffix_bytes: bytes = b"",
        span_name: str = "immutable_seed",
        extra_protected_spans: Sequence[ProtectedSpanV1] = (),
    ) -> FencedPromptArtifactV1:
        if not all(isinstance(part, bytes) for part in (prefix_bytes, seed_bytes, suffix_bytes)):
            raise TypeError("prefix_bytes, seed_bytes, and suffix_bytes must be bytes")
        if not seed_bytes:
            raise ValueError("EMPTY_SEED_BYTES: seed_bytes must be non-empty")

        composite = prefix_bytes + seed_bytes + suffix_bytes
        start_byte = len(prefix_bytes)
        end_byte = start_byte + len(seed_bytes)
        seed_span = ProtectedSpanV1(name=span_name, start_byte=start_byte, end_byte=end_byte)
        seed_sha256 = hashlib.sha256(seed_bytes).hexdigest()

        artifact = FencedPromptArtifactV1(
            composite_bytes=composite,
            seed_span=seed_span,
            seed_bytes=seed_bytes,
            seed_sha256=seed_sha256,
            extra_protected_spans=tuple(extra_protected_spans),
        )
        self.verify_seed_integrity(artifact)
        return artifact

    def mutate_governed_span(
        self,
        artifact: FencedPromptArtifactV1,
        *,
        edit_start_byte: int,
        edit_end_byte: int,
        replacement_bytes: bytes,
    ) -> FencedPromptArtifactV1:
        self.verify_seed_integrity(artifact)
        all_spans = (artifact.seed_span, *artifact.extra_protected_spans)
        mutated_bytes = self._mutation_engine.apply_mutation(
            original_bytes=artifact.composite_bytes,
            protected_spans=all_spans,
            edit_start_byte=edit_start_byte,
            edit_end_byte=edit_end_byte,
            replacement_bytes=replacement_bytes,
        )

        delta = len(replacement_bytes) - (edit_end_byte - edit_start_byte)
        if edit_end_byte <= artifact.seed_span.start_byte:
            updated_seed_span = ProtectedSpanV1(
                name=artifact.seed_span.name,
                start_byte=artifact.seed_span.start_byte + delta,
                end_byte=artifact.seed_span.end_byte + delta,
            )
        else:
            updated_seed_span = artifact.seed_span

        updated_extra: list[ProtectedSpanV1] = []
        for span in artifact.extra_protected_spans:
            if edit_end_byte <= span.start_byte:
                updated_extra.append(
                    ProtectedSpanV1(
                        name=span.name,
                        start_byte=span.start_byte + delta,
                        end_byte=span.end_byte + delta,
                    )
                )
            else:
                updated_extra.append(span)

        updated_artifact = FencedPromptArtifactV1(
            composite_bytes=mutated_bytes,
            seed_span=updated_seed_span,
            seed_bytes=artifact.seed_bytes,
            seed_sha256=artifact.seed_sha256,
            extra_protected_spans=tuple(updated_extra),
        )
        self.verify_seed_integrity(
            updated_artifact,
            expected_seed_bytes=artifact.seed_bytes,
            expected_seed_sha256=artifact.seed_sha256,
        )
        return updated_artifact


__all__ = [
    "BackwardAttributionReceipt",
    "CandidateWorkflowSpec",
    "FencedPromptArtifactV1",
    "FixedPointLineageTaintEngineV1",
    "OperationalQuotientReportV1",
    "OperationalWorkflowQuotientV1",
    "ProtectedSpanEvolutionV1",
    "QuotientClassRepresentativeV1",
    "ReserveAllocationResultV1",
    "TransitiveImmunityEngineV1",
    "WorkflowStageSpec",
]
