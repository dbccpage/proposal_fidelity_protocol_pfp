"""Core computational engine for Workflows, Agents, Skills (WAS), Multicategories & Operads.

AuthorityEffect: None.

Formalizes operations across Levels 00–09:
- Level 00: Coloured Operad Architecture (ColouredOperad)
- Level 01: Skill Document & Packaging Discipline (SkillPackage)
- Level 02: Planar Trees & Operadic Associativity (PlanarTree)
- Level 03: Capability Slices & Swarm Wing Boundaries (SwarmWing)
- Level 04: Epistemic Anti-Skills & Somatic Mutation (AntiSkillRegistry)
- Level 05: Regulatory Treg Supervision & Antibody Synthesis (OperadTregSupervisor)
- Level 06: Residual Geometry & DDC Contractivity (DDCContractivityEngine)
- Level 07: Workflow Graphs & Dialectic Pipelines (DialecticWorkflow)
- Level 08: Four-Host Mirror Parity & Synchronization (FourHostParityManager)
- Level 09: Sovereign Non-Authority & Deliberation Receipts (DeliberationReceiptEmitter)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class Colour(str, Enum):
    CODE = "CODE"
    TEST_RECEIPT = "TEST_RECEIPT"
    NORMAL_FORM = "NORMAL_FORM"
    LEAN_PROOF = "LEAN_PROOF"
    DELIBERATION = "DELIBERATION"
    ANY = "ANY"


@dataclass(frozen=True)
class OperadOp:
    """Multicategory/Operad operation with typed profile inputs -> output."""

    id: int
    name: str
    inputs: Tuple[Colour, ...]
    output: Colour

    @property
    def arity(self) -> int:
        return len(self.inputs)


class ColouredOperad:
    """Level 00: Coloured Operad Architecture supporting partial composition o_i."""

    def __init__(self) -> None:
        self.operations: Dict[int, OperadOp] = {}

    def register_op(self, op: OperadOp) -> None:
        self.operations[op.id] = op

    def identity(self, c: Colour) -> OperadOp:
        return OperadOp(id=0, name=f"id_{c.value}", inputs=(c,), output=c)

    def partial_compose(self, f: OperadOp, g: OperadOp, slot_i: int) -> OperadOp:
        """Operadic partial composition f o_i g at 0-indexed slot i.
        Requires f.inputs[slot_i] == g.output.
        """
        if slot_i < 0 or slot_i >= len(f.inputs):
            raise IndexError(f"Slot {slot_i} out of bounds for arity {len(f.inputs)}")
        if (
            f.inputs[slot_i] != g.output
            and f.inputs[slot_i] != Colour.ANY
            and g.output != Colour.ANY
        ):
            raise TypeError(
                f"Colour mismatch at slot {slot_i}: expected {f.inputs[slot_i]}, got {g.output}"
            )
        new_inputs = f.inputs[:slot_i] + g.inputs + f.inputs[slot_i + 1 :]
        new_name = f"({f.name} o_{slot_i} {g.name})"
        new_id = int(hashlib.md5(f"{f.id}_{g.id}_{slot_i}".encode("utf-8")).hexdigest()[:8], 16)
        return OperadOp(id=new_id, name=new_name, inputs=new_inputs, output=f.output)


@dataclass(frozen=True)
class SkillPackage:
    """Level 01: Skill Document & Packaging Discipline enforcing line/size limits."""

    name: str
    description: str
    instruction_lines: int
    size_bytes: int
    has_frontmatter: bool
    reference_dispatch_matrix: bool

    def check_packaging_compliance(self) -> Tuple[bool, List[str]]:
        violations = []
        if not self.has_frontmatter:
            violations.append("Missing YAML frontmatter with name and description")
        if self.instruction_lines > 300:
            violations.append(f"Instruction lines {self.instruction_lines} exceeds ceiling 300")
        if self.size_bytes > 20000:
            violations.append(f"Size {self.size_bytes} bytes exceeds ceiling 20 KB")
        if not self.reference_dispatch_matrix:
            violations.append("Missing Reference Dispatch Matrix")
        return len(violations) == 0, violations


@dataclass(frozen=True)
class PlanarTree:
    """Level 02: Planar Trees & Operadic Associativity."""

    op: Optional[OperadOp] = None
    subtrees: Tuple[PlanarTree, ...] = ()
    colour: Optional[Colour] = None  # for leaf nodes

    @property
    def is_leaf(self) -> bool:
        return self.op is None

    def height(self) -> int:
        if self.is_leaf:
            return 0
        return 1 + (max((st.height() for st in self.subtrees), default=0))

    def leaf_colours(self) -> List[Colour]:
        if self.is_leaf:
            return [self.colour] if self.colour else []
        res = []
        for st in self.subtrees:
            res.extend(st.leaf_colours())
        return res

    def root_output(self) -> Colour:
        if self.is_leaf:
            return self.colour or Colour.ANY
        assert self.op is not None
        return self.op.output


class SwarmWing:
    """Level 03: Capability Slices & Swarm Wing Boundaries."""

    def __init__(self, name: str, allowed_capabilities: Set[str]) -> None:
        self.name = name
        self.allowed_capabilities = allowed_capabilities

    def can_execute(self, capability: str) -> bool:
        return capability in self.allowed_capabilities

    def execute_bounded(self, capability: str, task: str) -> Tuple[bool, str]:
        if not self.can_execute(capability):
            return (
                False,
                f"Wing {self.name} refuses capability '{capability}': outside authorized slice",
            )
        return True, f"Wing {self.name} executed '{capability}' on task"


class AntiSkillRegistry:
    """Level 04: Epistemic Anti-Skills & Somatic Mutation from incident receipts."""

    def __init__(self) -> None:
        self.patterns: Dict[str, Dict[str, Any]] = {}

    def mint_anti_skill(self, defect_type: str, incident_receipt: Dict[str, Any]) -> str:
        anti_skill_id = f"anti_{defect_type.lower()}"
        self.patterns[anti_skill_id] = {
            "defect_type": defect_type,
            "incident_receipt": incident_receipt,
            "authority_effect": "None",
        }
        return anti_skill_id

    def check_candidate(self, anti_skill_id: str, candidate_text: str) -> bool:
        if anti_skill_id not in self.patterns:
            return True
        pattern_str = self.patterns[anti_skill_id]["incident_receipt"].get("trigger", "")
        if pattern_str and pattern_str.lower() in candidate_text.lower():
            return False  # Blocked by anti-skill
        return True


class OperadTregSupervisor:
    """Level 05: Regulatory Treg Supervision & Antibody Synthesis for operad flows."""

    def __init__(self, rate_limit_per_second: float = 10.0) -> None:
        self.rate_limit = rate_limit_per_second
        self.recent_calls: List[float] = []

    def check_rate_compliance(self, current_time: float) -> bool:
        self.recent_calls = [t for t in self.recent_calls if current_time - t <= 1.0]
        if len(self.recent_calls) >= self.rate_limit:
            return False
        self.recent_calls.append(current_time)
        return True


class DDCContractivityEngine:
    """Level 06: Residual Geometry & DDC Contractivity enforcing Lipschitz contraction < 1."""

    def __init__(self, contraction_factor: float = 0.5) -> None:
        if not (0.0 <= contraction_factor < 1.0):
            raise ValueError("Contraction factor lambda must satisfy 0 <= lambda < 1")
        self.contraction_factor = contraction_factor

    def scale_descent_step(self, residual_norm: float) -> float:
        """Scale descent contracts residual error norm by factor lambda."""
        return residual_norm * self.contraction_factor

    def verify_contractivity(self, sequence: List[float]) -> bool:
        """Verifies sequence monotonically strictly contracts toward zero."""
        for i in range(len(sequence) - 1):
            if sequence[i + 1] >= sequence[i] and sequence[i] > 1e-9:
                return False
        return True


class DialecticWorkflow:
    """Level 07: Workflow Graphs & Dialectic Pipelines (Thesis -> Antithesis -> Synthesis)."""

    def __init__(self) -> None:
        self.stages = ["THESIS", "ANTITHESIS", "SYNTHESIS"]

    def run_pipeline(
        self,
        thesis_fn: Callable[[str], str],
        antithesis_fn: Callable[[str], str],
        synthesis_fn: Callable[[str, str], str],
        initial_input: str,
    ) -> Dict[str, str]:
        thesis = thesis_fn(initial_input)
        antithesis = antithesis_fn(thesis)
        synthesis = synthesis_fn(thesis, antithesis)
        return {
            "thesis": thesis,
            "antithesis": antithesis,
            "synthesis": synthesis,
            "authority_effect": "None",
        }


class FourHostParityManager:
    """Level 08: Four-Host Mirror Parity & Synchronization across active estate host seats."""

    HOST_SEATS = (".agents", ".claude", ".codex", ".grok")

    def __init__(self) -> None:
        self.store: Dict[str, Dict[str, str]] = {seat: {} for seat in self.HOST_SEATS}

    def sync_file(self, rel_path: str, content: str) -> None:
        """Atomically synchronizes identical content across all active host roots."""
        for seat in self.HOST_SEATS:
            self.store[seat][rel_path] = content

    def verify_mirror_parity(self, rel_path: str) -> bool:
        first_content = self.store[self.HOST_SEATS[0]].get(rel_path)
        if first_content is None:
            return False
        for seat in self.HOST_SEATS[1:]:
            if self.store[seat].get(rel_path) != first_content:
                return False
        return True


class DeliberationReceiptEmitter:
    """Level 09: Sovereign Non-Authority & Deliberation Receipts."""

    def __init__(self) -> None:
        self.receipts: List[Dict[str, Any]] = []

    def emit_receipt(
        self,
        proposal_id: int,
        proposer: str,
        reviewer: str,
        verifier: str,
        accepted: bool,
    ) -> Dict[str, Any]:
        receipt = {
            "receipt_id": len(self.receipts) + 1,
            "proposal_id": proposal_id,
            "proposer": proposer,
            "reviewer": reviewer,
            "verifier": verifier,
            "accepted": accepted,
            "authority_effect": "None",
        }
        serialized = json.dumps(receipt, sort_keys=True)
        receipt["digest"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.receipts.append(receipt)
        return receipt
