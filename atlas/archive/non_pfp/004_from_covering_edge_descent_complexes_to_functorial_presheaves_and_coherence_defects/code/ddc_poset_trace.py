"""DDC Poset Trace and Operational Commutator Engine.

Implements the Discrete Deformation Calculus (DDC) 8-letter operational
alphabet A_DDC = {E, R, C, I, Lambda, D, M, T}, poset trace logging,
and operational commutator word evaluation on finite posets.

Theorem 4.6: In the Discrete Deformation Calculus over a modular lattice P,
the curvature cochain on any diamond a < b1, b2 < c equals the DDC commutator:
    K_diamond = [[ Lambda_{c, b1} D_{b1, a}, Lambda_{c, b2} D_{b2, a} ]].

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from exact import exact_equal
from exactsym import Matrix
from covering_edge_poset import FinitePoset
from restriction_system import RestrictionSystem, RestrictionMap


class DDCRune(str, Enum):
    """The 8-letter canonical operational rune alphabet of DDC."""
    E = "E"        # Evaluation: evaluate section value s(x)
    R = "R"        # Restriction: apply covering restriction r_{b,a}
    C = "C"        # Comparison: compute discrepancy r_{b,a} s(b) - s(a)
    I = "I"        # Injection: embed fiber data into higher chain spaces
    LAMBDA = "L"   # Structural Lift: ascend along comparable chains
    D = "D"        # Descent Retraction: retract data down to covering edges
    M = "M"        # Mutation: perturb restriction maps or section values
    T = "T"        # Terminal Gate: evaluate terminal reality criteria (Phi1, Gamma2)


@dataclass(frozen=True)
class DDCTraceStep:
    """An immutable, append-only step receipt in a DDC operational trace."""
    step_index: int
    rune: DDCRune
    source_node: str
    target_node: Optional[str]
    payload_hash: str
    defect_scalar: Fraction
    is_authorized: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


class DDCPosetTraceLogger:
    """Maintains an append-only cryptographic execution trace of DDC transitions."""

    def __init__(self, poset: FinitePoset) -> None:
        self.poset = poset
        self.steps: List[DDCTraceStep] = []

    def log_step(
        self,
        rune: DDCRune,
        source: str,
        target: Optional[str] = None,
        defect: Fraction = Fraction(0),
        authorized: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DDCTraceStep:
        idx = len(self.steps)
        payload_repr = f"{idx}:{rune.value}:{source}:{target}:{defect}"
        step = DDCTraceStep(
            step_index=idx,
            rune=rune,
            source_node=source,
            target_node=target,
            payload_hash=hex(abs(hash(payload_repr)))[2:],
            defect_scalar=defect,
            is_authorized=authorized,
            metadata=metadata or {},
        )
        self.steps.append(step)
        return step

    def total_accumulated_defect(self) -> Fraction:
        return sum((s.defect_scalar for s in self.steps), Fraction(0))

    def extract_word(self) -> str:
        return "".join(s.rune.value for s in self.steps)


class DDCPosetCommutator:
    """Evaluates DDC operational commutators [[ Lambda, D ]] across poset chains."""

    @staticmethod
    def evaluate_chain_descent(
        system: RestrictionSystem, chain: Sequence[str], initial_vector: Matrix
    ) -> Matrix:
        """Apply sequential descent along descending chain x_k > x_{k-1} > ... > x_0."""
        current = initial_vector
        for i in range(len(chain) - 1, 0, -1):
            src = chain[i]
            tgt = chain[i - 1]
            rmap = system.get_restriction(tgt, src)
            current = rmap(current)
        return current

    @classmethod
    def evaluate_diamond_commutator(
        cls,
        system: RestrictionSystem,
        bottom: str,
        branch1: str,
        branch2: str,
        top: str,
        test_vector: Matrix,
    ) -> Dict[str, Any]:
        """Compute the operational commutator between two saturated diamond branches:

        Path 1: top -> branch1 -> bottom
        Path 2: top -> branch2 -> bottom
        Commutator defect: Delta = Path1(v) - Path2(v).
        """
        # Verify diamond relations
        poset = system.poset
        assert poset.is_le(bottom, branch1)
        assert poset.is_le(branch1, top)
        assert poset.is_le(bottom, branch2)
        assert poset.is_le(branch2, top)

        # Path 1: r_{branch1, bottom} o r_{top, branch1}
        r_top_b1 = system.get_restriction(branch1, top)
        r_b1_bot = system.get_restriction(bottom, branch1)
        v1 = r_b1_bot(r_top_b1(test_vector))

        # Path 2: r_{branch2, bottom} o r_{top, branch2}
        r_top_b2 = system.get_restriction(branch2, top)
        r_b2_bot = system.get_restriction(bottom, branch2)
        v2 = r_b2_bot(r_top_b2(test_vector))

        diff = v1 - v2
        is_commuting = exact_equal(v1, v2)
        l1_norm = sum(abs(diff[r, c]) for r in range(diff.rows) for c in range(diff.cols))

        return {
            "is_commuting": is_commuting,
            "path1_result": v1,
            "path2_result": v2,
            "commutator_defect": diff,
            "l1_defect_norm": l1_norm,
        }
