"""quotient_operad.py

Candidate quotient analysis for coloured operads.

Matching type signatures and a few scalar residual observations are necessary
diagnostics, not a semantic congruence proof. This module therefore reports
candidate classes but never merges or culls distinct declared operations.

AuthorityEffect: None. Finite residual structure only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict
import json
import math

if __package__:
    from .evidence_observations import classify_residual_rows
    from .coloured_operad import ColouredOperad, Colour, Operation, CompositionKey, IllTypedCompositionRefusal
else:
    from evidence_observations import classify_residual_rows
    from coloured_operad import ColouredOperad, Colour, Operation, CompositionKey, IllTypedCompositionRefusal


# ---------------------------------------------------------------------------
# Residual evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResidualEvidence:
    """Compatibility record for one scalar observation, never a certificate."""
    run_id: str
    phi_before: float
    phi_after: float

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if not math.isfinite(self.phi_before) or not math.isfinite(self.phi_after):
            raise ValueError("residual evidence must be finite")
        if self.phi_before < 0.0 or self.phi_after < 0.0:
            raise ValueError("residual evidence must be non-negative")

    @property
    def delta(self) -> float:
        return self.phi_after - self.phi_before

    def is_contractive(self) -> bool:
        """Compatibility API: scalar observations never certify contractivity."""
        return False

    def is_exact(self) -> bool:
        """Compatibility API: scalar observations never certify exactness."""
        return False

    def observed_trend(self) -> str:
        if self.phi_after < self.phi_before:
            return "decrease"
        if self.phi_after > self.phi_before:
            return "increase"
        return "unchanged"


@dataclass
class EvidenceLedger:
    """Accumulated residual evidence for one concrete skill."""
    skill_id: str
    entries: List[ResidualEvidence] = field(default_factory=list)

    def add(self, run_id: str, phi_before: float, phi_after: float) -> None:
        evidence = ResidualEvidence(run_id, phi_before, phi_after)
        matches = [entry for entry in self.entries if entry.run_id == evidence.run_id]
        if matches:
            if len(matches) != 1 or matches[0] != evidence:
                raise ValueError(f"conflicting duplicate run_id {run_id!r}")
            return
        self.entries.append(evidence)

    def __len__(self) -> int:
        return len(self.entries)

    def residual_class(self) -> str:
        """Scalar observations cannot establish a residual behavior class."""
        return "unknown"

    def is_stable(self, min_instances: int = 3) -> bool:
        """No finite count of these observations becomes a semantic certificate."""
        return False


# ---------------------------------------------------------------------------
# Congruence key
# ---------------------------------------------------------------------------

def congruence_key(op: Operation, residual_class: str) -> Tuple:
    """
    Two operations are congruent when this key coincides and both
    possess stable evidence ledgers.
    """
    return (
        tuple(c.name for c in op.source),
        op.target.name,
        residual_class,
    )


# ---------------------------------------------------------------------------
# Quotient functor
# ---------------------------------------------------------------------------

class QuotientFunctor:
    """
    Q : O_concrete -> O_meta

    Computes possible comparison families but preserves every concrete
    operation. A true quotient needs a separately replayed compatibility proof
    for semantics and composition; this package does not yet have one.
    """

    def __init__(self, concrete: ColouredOperad, min_instances: int = 3):
        self.concrete = concrete
        self.min_instances = min_instances
        self.ledgers: Dict[str, EvidenceLedger] = {}
        self._classes: Dict[Tuple, List[str]] = defaultdict(list)
        self._candidate_classes: Dict[Tuple, List[str]] = defaultdict(list)
        self._repr: Dict[str, str] = {}          # concrete id -> meta id
        self.meta: Optional[ColouredOperad] = None

    # ----- evidence collection (Step 1) ------------------------------------

    def record(
        self,
        skill_id: str,
        run_id: str,
        phi_before: float,
        phi_after: float,
    ) -> None:
        if skill_id not in self.ledgers:
            self.ledgers[skill_id] = EvidenceLedger(skill_id)
        self.ledgers[skill_id].add(run_id, phi_before, phi_after)

    # ----- congruence (Step 2) ---------------------------------------------

    def _build_classes(self) -> None:
        self._classes.clear()
        self._candidate_classes.clear()
        self._repr.clear()
        for op_id, op in self.concrete.operations.items():
            if op_id.startswith("id_"):
                continue
            ledger = self.ledgers.get(op_id)
            residual = (
                ledger.residual_class()
                if ledger is not None and ledger.is_stable(self.min_instances)
                else op.residual_effect
            )
            self._candidate_classes[congruence_key(op, residual)].append(op_id)
            self._classes[("operation", op_id)].append(op_id)
            self._repr[op_id] = op_id

    def congruent(self, op_a: str, op_b: str) -> bool:
        """Return only definitional identity; no semantic quotient is minted."""

        return op_a == op_b and op_a in self.concrete.operations

    # ----- promote / cull (Step 3) -----------------------------------------

    def build_meta_operad(self, name: str = "MetaSkillOperad") -> ColouredOperad:
        """
        Construct an identity-preserving comparison operad.

        Distinct operations remain distinct. Candidate groups are available in
        ``report`` for future independent equivalence checking.
        """
        self._build_classes()
        meta = ColouredOperad(name)

        # colours are identical
        for c in self.concrete.colours:
            meta.add_colour(c)

        for members in self._classes.values():
            cid = members[0]
            concrete_operation = self.concrete.operations[cid]
            meta.add_operation(
                op_id=cid,
                name=concrete_operation.name,
                source_colours=[colour.name for colour in concrete_operation.source],
                target_colour=concrete_operation.target.name,
                equivariant=concrete_operation.equivariant,
                residual_effect=concrete_operation.residual_effect,
            )

        # induce composition on meta representatives with ROP error tracking
        for ck, result in self.concrete.composition.items():
            outer_m = self._repr.get(ck.outer, ck.outer)
            inner_m = self._repr.get(ck.inner, ck.inner)
            result_m = self._repr.get(result, result)
            # only register if all three survived into meta
            if (
                outer_m in meta.operations
                and inner_m in meta.operations
                and result_m in meta.operations
            ):
                comp_res = meta.add_composition(outer_m, ck.slot, inner_m, result_m)
                if comp_res.is_failure:
                    # Refusal is explicitly tracked inside meta.refusals
                    pass

        meta.ensure_units()
        self.meta = meta
        return meta

    def cull_list(self) -> List[str]:
        """
        No concrete skill is deletable from scalar residual observations.
        """
        return []

    def report(self) -> dict:
        if self.meta is None:
            self.build_meta_operad()
        return {
            "concrete_ops": len(
                [k for k in self.concrete.operations if not k.startswith("id_")]
            ),
            "meta_ops": len(
                [k for k in self.meta.operations if not k.startswith("id_")]
            ),
            "certified_classes": {},
            "candidate_classes": {
                str(k): v
                for k, v in self._candidate_classes.items()
                if len(v) > 1
            },
            "culled": self.cull_list(),
            "automatic_merges_enabled": False,
            "candidate_class_ceiling": (
                "same signature/residual observations only; no behavioral or "
                "composition congruence established"
            ),
            "observation_claim_effect": {
                "contractivity": False,
                "equivalence": False,
                "promotion": False,
            },
            "refusals_count": len(self.meta.refusals),
            "refusals": [
                {
                    "outer": r.outer,
                    "slot": r.slot,
                    "inner": r.inner,
                    "message": r.message,
                }
                for r in self.meta.refusals
            ],
            "authority_effect": "None",
        }


# ---------------------------------------------------------------------------
# Convenience: load ledgers from a simple JSON trace
# ---------------------------------------------------------------------------

def load_ledgers_from_trace(path: str, q: QuotientFunctor) -> None:
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    for observation in classify_residual_rows(rows):
        q.record(
            observation.skill_id,
            observation.run_id,
            observation.phi_before,
            observation.phi_after,
        )
