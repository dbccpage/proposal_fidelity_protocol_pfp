"""
Arity Rewrite Engine for S(n) Tower Transitions

Exact float-free Abstract Reduction System (ARS) and Term/String Rewriting System
operating over discrete distinction stages (0 to 5) and relational presentations.

Enforces:
- Redex-keyed derivation steps (position, rule) eliminating name-keyed laundering.
- Critical pair generation and local confluence (WCR) checking.
- Rewriting modulo group action (R / ~_G) to avoid infinite reduction loops on symmetric links (S_2).
- Zero floating-point arithmetic: all positions, weights, and metrics use exact integers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)


class StageKind(Enum):
    """Canonical distinction stages in the S(n) tower progression."""
    STAGE_0_VOID = "Void"                    # <> Empty carrier, 0 degrees of freedom
    STAGE_1_POINT = "Point"                  # <a> Lone mark, C_1 = 0, H_0 = Z
    STAGE_2_PAIR = "Pair"                    # <ab> Undistinguished pair, Aut = S_2
    STAGE_3_CUT_D2 = "PointedCutD2"          # <arb> Directed cut a -> b, Aut = {id}
    STAGE_4_LOOP_ARA = "RefusedLoopARA"      # <ara> Self-loop a -> a, partial l = 0 (refused)
    STAGE_5_LINK_S2 = "SymmetricLinkS2"      # <arb> + <bra> Bidirectional link, Aut = Z_2


@dataclass(frozen=True)
class DistinctionObject:
    """Represents a finite relational presentation in the S(n) hierarchy."""
    stage: StageKind
    vertices: Tuple[str, ...]
    edges: Tuple[Tuple[str, str], ...] = ()
    automorphism_group: str = "1"
    is_admissible_primitive: bool = True
    refusal_reason: Optional[str] = None


def create_stage_object(stage: StageKind, vertices: Sequence[str]) -> DistinctionObject:
    """Constructs a canonical distinction object for a declared stage."""
    verts = tuple(vertices)
    if stage == StageKind.STAGE_0_VOID:
        return DistinctionObject(
            stage=stage,
            vertices=(),
            edges=(),
            automorphism_group="1",
            is_admissible_primitive=True,
        )
    if stage == StageKind.STAGE_1_POINT:
        if len(verts) != 1:
            raise ValueError("Stage 1 Point requires exactly 1 vertex.")
        return DistinctionObject(
            stage=stage,
            vertices=verts,
            edges=(),
            automorphism_group="1",
            is_admissible_primitive=True,
        )
    if stage == StageKind.STAGE_2_PAIR:
        if len(verts) != 2:
            raise ValueError("Stage 2 Pair requires exactly 2 vertices.")
        return DistinctionObject(
            stage=stage,
            vertices=verts,
            edges=(),
            automorphism_group="S_2",
            is_admissible_primitive=True,
        )
    if stage == StageKind.STAGE_3_CUT_D2:
        if len(verts) != 2 or verts[0] == verts[1]:
            raise ValueError("Stage 3 Cut D2 requires 2 distinct vertices.")
        return DistinctionObject(
            stage=stage,
            vertices=verts,
            edges=((verts[0], verts[1]),),
            automorphism_group="{id}",
            is_admissible_primitive=True,
        )
    if stage == StageKind.STAGE_4_LOOP_ARA:
        if len(verts) != 1:
            raise ValueError("Stage 4 Loop ARA requires 1 vertex.")
        return DistinctionObject(
            stage=stage,
            vertices=verts,
            edges=((verts[0], verts[0]),),
            automorphism_group="Z_2",
            is_admissible_primitive=False,
            refusal_reason="Diagonal self-loop a -> a violates irreflexivity (sigma_{x=y} = empty).",
        )
    if stage == StageKind.STAGE_5_LINK_S2:
        if len(verts) != 2 or verts[0] == verts[1]:
            raise ValueError("Stage 5 Link S2 requires 2 distinct vertices.")
        return DistinctionObject(
            stage=stage,
            vertices=verts,
            edges=((verts[0], verts[1]), (verts[1], verts[0])),
            automorphism_group="Z_2",
            is_admissible_primitive=True,
        )
    raise ValueError(f"Unknown StageKind: {stage}")


def check_irreflexivity(carrier: Sequence[str], relation: Sequence[Tuple[str, str]]) -> bool:
    """
    Checks whether a relation satisfies strict diagonal excision:
    sigma_{x=y}(R) = empty, meaning for all (x, y) in R, x != y.
    """
    return all(u != v for u, v in relation)


@dataclass(frozen=True)
class Rule:
    """
    A discrete rewrite rule lhs -> rhs.
    Length and weight costs must be exact integers.
    """
    name: str
    lhs: str
    rhs: str
    description: str = ""
    weight: int = 1

    def is_length_reducing(self) -> bool:
        """True if application strictly decreases word length."""
        return len(self.rhs) < len(self.lhs)


@dataclass(frozen=True)
class Redex:
    """Identifies an exact match site: rule applied at position pos."""
    pos: int
    rule_name: str
    length: int


@dataclass(frozen=True)
class Step:
    """
    A redex-keyed derivation step (position, rule).
    Ensures that host application is a total, deterministic function.
    """
    rule_name: str
    pos: int
    producer_claim: Optional[str] = None


@dataclass(frozen=True)
class CriticalPair:
    """
    A non-trivial divergence overlap between two rules.
    word: the minimal common ancestor word where both rules match.
    left_reduct / right_reduct: the divergent immediate descendants.
    """
    word: str
    left_rule: str
    left_pos: int
    left_reduct: str
    right_rule: str
    right_pos: int
    right_reduct: str


@dataclass(frozen=True)
class PeakVerdict:
    """Verdict on joinability of a local peak u <- w -> v."""
    kind: str  # "Joined", "NotJoinable", "NotJoinedWithinBound"
    at_term: Optional[str]
    basis: str
    left_reach_size: int
    right_reach_size: int


class RewriteSystem:
    """
    Exact float-free Abstract Reduction System and String/Term Rewriting Engine.
    Supports:
    - Step determinacy keyed by (pos, rule)
    - Critical pair detection
    - Reachability search with bounded fuel
    - Local confluence checking (WCR)
    - Rewriting modulo group action (R / ~_G)
    """

    def __init__(
        self,
        rules: Sequence[Rule] = (),
        group_symmetries: Optional[Sequence[Dict[str, str]]] = None,
        max_reach: int = 10000,
        max_reduction_steps: int = 1000,
    ) -> None:
        self.rules: List[Rule] = []
        self.by_name: Dict[str, Rule] = {}
        for r in rules:
            self.add_rule(r)
        self.group_symmetries: List[Dict[str, str]] = list(group_symmetries) if group_symmetries else []
        self.max_reach = max_reach
        self.max_reduction_steps = max_reduction_steps

    def add_rule(self, rule: Rule) -> None:
        """Registers a rewrite rule, asserting uniqueness of rule name and non-empty LHS."""
        if not rule.lhs:
            raise ValueError(f"Rule '{rule.name}' has empty LHS.")
        if rule.name in self.by_name:
            raise ValueError(f"Duplicate rule name: '{rule.name}'.")
        self.rules.append(rule)
        self.by_name[rule.name] = rule

    def find_redexes(self, s: str) -> List[Redex]:
        """
        Finds all active redexes in string s.
        Returns a sorted list ordered by position, then rule name.
        """
        redexes: List[Redex] = []
        for r in self.rules:
            start = 0
            k = len(r.lhs)
            while True:
                idx = s.find(r.lhs, start)
                if idx < 0:
                    break
                redexes.append(Redex(pos=idx, rule_name=r.name, length=k))
                start = idx + 1
        redexes.sort(key=lambda x: (x.pos, x.rule_name))
        return redexes

    def apply_step(self, s: str, step: Step) -> Tuple[Optional[str], Optional[str]]:
        """
        Applies a redex-keyed step (pos, rule_name) to string s.
        Returns (result_string, error_message).
        Rejection occurs if:
        - Rule does not exist
        - Position is out of bounds
        - Substring at pos does not match rule.lhs
        - Producer claim is provided but contradicts host recomputed state
        """
        rule = self.by_name.get(step.rule_name)
        if rule is None:
            return None, f"Unknown rule '{step.rule_name}'."
        k = len(rule.lhs)
        if step.pos < 0 or step.pos + k > len(s):
            return None, f"Position {step.pos} out of range for string of length {len(s)}."
        target_sub = s[step.pos : step.pos + k]
        if target_sub != rule.lhs:
            return (
                None,
                f"Redex mismatch: rule '{rule.name}' requires '{rule.lhs}' at {step.pos}, found '{target_sub}'.",
            )
        computed = s[: step.pos] + rule.rhs + s[step.pos + k :]
        if step.producer_claim is not None and step.producer_claim != computed:
            return (
                None,
                f"Producer claim divergence: host computed '{computed}', producer claimed '{step.producer_claim}'.",
            )
        return computed, None

    def orbit(self, s: str) -> Set[str]:
        """
        Computes the complete orbit [s]_G under registered group symmetries.
        """
        if not self.group_symmetries:
            return {s}
        candidates = {s}
        for perm in self.group_symmetries:
            permuted = "".join(perm.get(ch, ch) for ch in s)
            candidates.add(permuted)
        return candidates

    def canonical_orbit_representative(self, s: str) -> str:
        """
        Computes the canonical representative of the orbit [s]_G under group symmetries.
        Selects the lexicographically minimal element across all group permutations.
        """
        return min(self.orbit(s))

    def are_equivalent_modulo_group(self, s1: str, s2: str) -> bool:
        """Checks whether s1 and s2 belong to the same orbit [s]_G."""
        return self.canonical_orbit_representative(s1) == self.canonical_orbit_representative(s2)

    def is_terminating_by_length(self) -> bool:
        """True if every registered rule is strictly length-reducing (guaranteeing SN)."""
        return all(r.is_length_reducing() for r in self.rules)

    def reach(self, s: str, modulo_group: bool = False) -> Tuple[Set[str], bool]:
        """
        Computes the forward reachable set of s under ->*.
        If modulo_group is True, reachable terms are canonicalized modulo ~_G.
        Returns (reachable_set, is_complete).
        If fuel is exhausted before frontier empties, is_complete is False.
        """
        start_term = self.canonical_orbit_representative(s) if modulo_group else s
        seen: Set[str] = {start_term}
        frontier: List[str] = [start_term]

        while frontier:
            cur = frontier.pop()
            orbit_terms = self.orbit(cur) if modulo_group else {cur}
            for term in orbit_terms:
                for redex in self.find_redexes(term):
                    nxt, err = self.apply_step(term, Step(rule_name=redex.rule_name, pos=redex.pos))
                    if err is None and nxt is not None:
                        target = self.canonical_orbit_representative(nxt) if modulo_group else nxt
                        if target not in seen:
                            if len(seen) >= self.max_reach:
                                return seen, False
                            seen.add(target)
                            frontier.append(target)
        return seen, True

    def find_critical_pairs(self) -> List[CriticalPair]:
        """
        Exhaustively computes all non-trivial critical pairs (overlaps) between rules.
        Examines:
        1. Suffix-prefix overlaps: l1 = u . w, l2 = w . v with non-empty w.
        2. Substring inclusions: l2 is a proper factor of l1.
        """
        pairs: List[CriticalPair] = []
        seen_keys: Set[Tuple[str, str, int, str, int]] = set()

        for r1 in self.rules:
            for r2 in self.rules:
                l1, l2 = r1.lhs, r2.lhs

                # 1. Suffix-prefix overlaps:
                # l1 ends with w of length k >= 1, l2 begins with w of length k
                for k in range(1, min(len(l1), len(l2)) + 1):
                    # Discard identical full overlap on same rule (trivial identity)
                    if k == len(l1) and k == len(l2) and r1.name == r2.name:
                        continue
                    if l1[-k:] == l2[:k]:
                        word = l1 + l2[k:]
                        p1, p2 = 0, len(l1) - k
                        if p1 == p2 and r1.name == r2.name:
                            continue
                        a, err_a = self.apply_step(word, Step(r1.name, p1))
                        b, err_b = self.apply_step(word, Step(r2.name, p2))
                        if err_a is None and err_b is None and a is not None and b is not None:
                            key = (word, r1.name, p1, r2.name, p2)
                            if key not in seen_keys:
                                seen_keys.add(key)
                                pairs.append(
                                    CriticalPair(
                                        word=word,
                                        left_rule=r1.name,
                                        left_pos=p1,
                                        left_reduct=a,
                                        right_rule=r2.name,
                                        right_pos=p2,
                                        right_reduct=b,
                                    )
                                )

                # 2. Factor inclusions: l2 occurs inside l1
                start = 0
                while True:
                    idx = l1.find(l2, start)
                    if idx < 0:
                        break
                    start = idx + 1
                    # Skip trivial identity match of same rule at position 0
                    if r1.name == r2.name and idx == 0 and len(l1) == len(l2):
                        continue
                    word = l1
                    a, err_a = self.apply_step(word, Step(r1.name, 0))
                    b, err_b = self.apply_step(word, Step(r2.name, idx))
                    if err_a is None and err_b is None and a is not None and b is not None:
                        key = (word, r1.name, 0, r2.name, idx)
                        if key not in seen_keys:
                            seen_keys.add(key)
                            pairs.append(
                                CriticalPair(
                                    word=word,
                                    left_rule=r1.name,
                                    left_pos=0,
                                    left_reduct=a,
                                    right_rule=r2.name,
                                    right_pos=idx,
                                    right_reduct=b,
                                )
                            )

        return pairs

    def check_joinability(self, u: str, v: str, modulo_group: bool = False) -> PeakVerdict:
        """
        Determines whether two divergent reducts u and v join (u downarrow v).
        Explores forward reachability up to max_reach.
        """
        if u == v or (modulo_group and self.are_equivalent_modulo_group(u, v)):
            return PeakVerdict(
                kind="Joined",
                at_term=self.canonical_orbit_representative(u) if modulo_group else u,
                basis="IdenticalInitialReducts",
                left_reach_size=1,
                right_reach_size=1,
            )

        reach_u, complete_u = self.reach(u, modulo_group=modulo_group)
        reach_v, complete_v = self.reach(v, modulo_group=modulo_group)

        intersection = reach_u & reach_v
        if intersection:
            canonical_join = sorted(intersection)[0]
            return PeakVerdict(
                kind="Joined",
                at_term=canonical_join,
                basis="ReachIntersection",
                left_reach_size=len(reach_u),
                right_reach_size=len(reach_v),
            )

        if complete_u and complete_v:
            basis = "TerminatingSN" if self.is_terminating_by_length() else "FiniteReachExhausted"
            return PeakVerdict(
                kind="NotJoinable",
                at_term=None,
                basis=basis,
                left_reach_size=len(reach_u),
                right_reach_size=len(reach_v),
            )

        return PeakVerdict(
            kind="NotJoinedWithinBound",
            at_term=None,
            basis=f"BudgetExhausted({self.max_reach})",
            left_reach_size=len(reach_u),
            right_reach_size=len(reach_v),
        )

    def check_local_confluence(
        self, modulo_group: bool = False
    ) -> Tuple[bool, List[Tuple[CriticalPair, PeakVerdict]]]:
        """
        Evaluates the Critical Pair Lemma:
        An ARS is locally confluent (WCR) iff all critical pairs join.
        Returns (is_locally_confluent, critical_pair_verdicts).
        """
        cps = self.find_critical_pairs()
        verdicts: List[Tuple[CriticalPair, PeakVerdict]] = []
        all_joined = True

        for cp in cps:
            verdict = self.check_joinability(cp.left_reduct, cp.right_reduct, modulo_group=modulo_group)
            verdicts.append((cp, verdict))
            if verdict.kind != "Joined":
                all_joined = False

        return all_joined, verdicts

    def reduce_to_normal_form(
        self,
        s: str,
        strategy: str = "leftmost_first",
        modulo_group: bool = False,
    ) -> Tuple[str, List[Step], bool]:
        """
        Normalizes string s by applying reduction steps until a normal form is reached.
        Strategy:
        - "leftmost_first": chooses redex with smallest position.
        Returns (terminal_string, step_history, terminated).
        """
        cur = s
        history: List[Step] = []

        for _ in range(self.max_reduction_steps):
            redexes = self.find_redexes(cur)
            if not redexes:
                res = self.canonical_orbit_representative(cur) if modulo_group else cur
                return res, history, True

            if strategy == "leftmost_first":
                chosen = min(redexes, key=lambda x: (x.pos, x.rule_name))
            else:
                chosen = redexes[0]

            step = Step(rule_name=chosen.rule_name, pos=chosen.pos)
            nxt, err = self.apply_step(cur, step)
            if err is not None or nxt is None:
                break
            history.append(step)
            cur = nxt

        res = self.canonical_orbit_representative(cur) if modulo_group else cur
        return res, history, False


__all__ = ['Any', 'Callable', 'CriticalPair', 'Dict', 'DistinctionObject', 'Enum', 'FrozenSet', 'List', 'Optional', 'PeakVerdict', 'Redex', 'RewriteSystem', 'Rule', 'Sequence', 'Set', 'StageKind', 'Step', 'Tuple', 'check_irreflexivity', 'create_stage_object', 'dataclass', 'field']
