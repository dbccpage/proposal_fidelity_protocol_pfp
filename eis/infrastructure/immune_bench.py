"""Thymus screening bench for farm detector rules, with a phrase-to-rule helper.

What it does:

1. `AntimorphismImmuneBench.screen_candidate_rules` runs the thymus
   (`domain.thymus.ThymusGate`) on regex detector rules against a fixed panel
   of six clean physics statements (`CLEAN_PHYSICS_SELF_PANEL`, each with the
   source it is attributed to) and counts admitted and refused rules.
2. `mutate_and_mature` and `age_repertoire` apply the idle-run counters of
   `domain.clonal_selection`: a caller-supplied replacement pattern, and one
   unmatched run per rule. There is no guided mutation, affinity maturation or
   half-life here.
3. `PhagocyticFormularyRegenerator.phagocytose_and_admit` turns caller-supplied
   (phrase, epitope) pairs into literal (escaped) regex rules and keeps those the
   thymus admits. It does not read the CemeterySink or any run record; the
   caller supplies the phrases.

Nothing here admits a rule to any live formulary.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Sequence, Tuple

from eis.domain import (
    DetectorRule,
    ThymusGate,
)
from eis.domain.thymus import ThymusSelectionResult

from .native_domain import NativeClonalSelectionEngine

# =============================================================================
# Clean Physics Self-Panel (Ground-Truth Valid Science)
# =============================================================================

CLEAN_PHYSICS_SELF_PANEL: Tuple[str, ...] = (
    # Lieb (1989) on Attractive Hubbard Model
    "For the attractive Hubbard model on any bipartite lattice at half-filling, the ground state has total spin S = 0.",
    # Hirsch (1985) on Auxiliary-field determinant
    "The determinant of the fermion matrix for the attractive Hubbard model is a product of identical real determinants, guaranteeing positivity.",
    # Chandrasekharan & Wiese (1999) on Meron cluster solution
    "In the meron-cluster algorithm, configurations with non-zero topological charge can be clustered into orbits that cancel exactly in specific spin models.",
    # Troyer & Wiese (2005) on Computational complexity of the sign problem
    "The general fermionic sign problem is NP-hard; no polynomial-time quantum Monte Carlo algorithm can universally eliminate the sign problem across all Hamiltonians.",
    # Li & Yao (2019) on Majorana quantum Monte Carlo
    "Majorana reflection positivity provides a mathematical framework for constructing sign-problem-free continuous-time quantum Monte Carlo simulations for specific invariant interactions.",
    # Loh et al. (1990) on Average sign behavior
    "In generic repulsive fermion models away from half-filling, the average sign decays exponentially with spatial volume and inverse temperature beta.",
)


@dataclass(frozen=True, slots=True)
class ImmuneBenchReport:
    """Exact-type report emitted by the Antimorphism Immune Bench."""

    total_rules_evaluated: int
    admitted_rules: int
    purged_rules: int
    results: Tuple[ThymusSelectionResult, ...]

    def __post_init__(self) -> None:
        if type(self.total_rules_evaluated) is not int or self.total_rules_evaluated < 0:
            raise ValueError("total_rules_evaluated must be non-negative int")
        if type(self.admitted_rules) is not int or self.admitted_rules < 0:
            raise ValueError("admitted_rules must be non-negative int")
        if type(self.purged_rules) is not int or self.purged_rules < 0:
            raise ValueError("purged_rules must be non-negative int")
        if self.admitted_rules + self.purged_rules != self.total_rules_evaluated:
            raise ValueError("admitted_rules + purged_rules must equal total_rules_evaluated")
        if len(self.results) != self.total_rules_evaluated:
            raise ValueError("results must hold one selection per evaluated rule")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ImmuneBenchReport)
        return (
            self.total_rules_evaluated == other.total_rules_evaluated
            and self.admitted_rules == other.admitted_rules
            and self.purged_rules == other.purged_rules
            and self.results == other.results
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.total_rules_evaluated,
                self.admitted_rules,
                self.purged_rules,
                self.results,
            )
        )


class AntimorphismImmuneBench:
    """Manages Thymic Negative Selection and Clonal Selection for Farm detectors."""

    def __init__(self, self_panel: Sequence[str] | None = None) -> None:
        panel = self_panel if self_panel is not None else CLEAN_PHYSICS_SELF_PANEL
        self.thymus = ThymusGate(panel)

    def screen_candidate_rules(self, rules: Sequence[DetectorRule]) -> ImmuneBenchReport:
        """Screen candidate rules against the Clean Physics Self-Panel."""
        results: list[ThymusSelectionResult] = []
        admitted = 0
        purged = 0

        for rule in rules:
            res = self.thymus.evaluate_rule(rule)
            results.append(res)
            if res.is_admitted:
                admitted += 1
            else:
                purged += 1

        return ImmuneBenchReport(
            total_rules_evaluated=len(rules),
            admitted_rules=admitted,
            purged_rules=purged,
            results=tuple(results),
        )

    @staticmethod
    def mutate_and_mature(
        rule: DetectorRule, mutation_variant: str, new_rule_id: str
    ) -> DetectorRule:
        """A child rule with a caller-supplied pattern (no search or maturation)."""
        return NativeClonalSelectionEngine.mutate_rule(rule, mutation_variant, new_rule_id)

    @staticmethod
    def age_repertoire(repertoire: Sequence[DetectorRule]) -> Sequence[DetectorRule]:
        """Count one unmatched run for every rule (linear idle counter)."""
        return tuple(NativeClonalSelectionEngine.apply_decay(r) for r in repertoire)


class PhagocyticFormularyRegenerator:
    """Turns caller-supplied phrases into literal rules and keeps those the thymus admits."""

    def __init__(self, bench: AntimorphismImmuneBench | None = None) -> None:
        self.bench = bench if bench is not None else AntimorphismImmuneBench()

    def synthesize_candidate_rule(
        self,
        refused_motif: str,
        target_epitope: str,
        rule_id: str = "",
    ) -> DetectorRule:
        """A literal (escaped) regex rule for one caller-supplied phrase."""
        if not rule_id:
            h = hashlib.sha256(f"{target_epitope}:{refused_motif}".encode("utf-8")).hexdigest()[:12]
            rule_id = f"ANTIBODY-{h}"
        escaped = re.escape(refused_motif)
        return DetectorRule(
            rule_id=rule_id,
            target_epitope=target_epitope,
            match_pattern=escaped,
        )

    def phagocytose_and_admit(
        self,
        refused_motifs: Sequence[tuple[str, str]],
    ) -> tuple[DetectorRule, ...]:
        """Rules for the given phrases that the thymus admits."""
        candidate_rules = [
            self.synthesize_candidate_rule(motif, epitope) for motif, epitope in refused_motifs
        ]
        report = self.bench.screen_candidate_rules(candidate_rules)
        admitted = [rule for rule, res in zip(candidate_rules, report.results) if res.is_admitted]
        return tuple(admitted)


__all__ = [
    "AntimorphismImmuneBench",
    "CLEAN_PHYSICS_SELF_PANEL",
    "ImmuneBenchReport",
    "PhagocyticFormularyRegenerator",
]
