"""Regressions for five epistemic immune system defects reproduced on 2026-09-26.

Each test names its invariant; the matching production mutation is noted beside it.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import pytest

from omega_engine_pfp.domain.biochem.proofreading import HopfieldNinioProofreader
from omega_engine_pfp.domain.immune.clonal_selection import (
    ClonalCandidate,
    ClonalSelectionEngine,
    KillConditionRefusal,
)
from omega_engine_pfp.domain.immune.thymus import SelfPanel
from omega_engine_pfp.domain.immune.treg import TregSupervisor


def _rule(half_life_runs: int = 10, pattern: str = r"eval_unrestricted_code") -> ClonalCandidate:
    return ClonalCandidate(
        rule_id="RULE-PARENT",
        target_epitope="malicious_eval",
        match_pattern=pattern,
        affinity_score=Fraction(1),
        half_life_runs=half_life_runs,
    )


# 1. Half-life decay halves once per completed tau interval.
# Mutation: dividing by 2**(new_runs_idle // tau) again on every call.


def test_decay_halves_once_per_completed_interval() -> None:
    step = _rule()
    seen = []
    for _ in range(12):
        step = ClonalSelectionEngine.apply_half_life_decay(step, elapsed_runs=1, tau=5)
        seen.append(step.affinity_score)
    half, quarter = Fraction(1, 2), Fraction(1, 4)
    assert seen == [1, 1, 1, 1, half, half, half, half, half, quarter, quarter, quarter]


def test_decay_does_not_depend_on_how_idle_runs_are_batched() -> None:
    single = ClonalSelectionEngine.apply_half_life_decay(_rule(), elapsed_runs=12, tau=5)
    batched = _rule()
    for elapsed in (3, 4, 5):
        batched = ClonalSelectionEngine.apply_half_life_decay(batched, elapsed_runs=elapsed, tau=5)
    assert single.affinity_score == batched.affinity_score == Fraction(1, 4)
    assert single.runs_idle == batched.runs_idle == 12


def test_decay_refuses_a_nonpositive_tau() -> None:
    with pytest.raises(ValueError):
        ClonalSelectionEngine.apply_half_life_decay(_rule(), elapsed_runs=1, tau=0)
    with pytest.raises(ValueError):
        ClonalSelectionEngine.apply_half_life_decay(_rule(), elapsed_runs=True, tau=5)
    with pytest.raises(ValueError):
        ClonalSelectionEngine.apply_half_life_decay(_rule(), elapsed_runs=1, tau=True)


# 2. An uncompilable clone pattern yields a typed refusal, not re.error.
# Mutation: compiling the pattern outside the guard.


def test_kill_condition_refuses_an_invalid_pattern_without_raising() -> None:
    parent = _rule()
    clone = ClonalSelectionEngine.mutate_rule(parent, new_pattern="([unclosed", clone_id="RULE-CLONE-BAD")
    killed, outcome = ClonalSelectionEngine.check_kill_condition(
        clone, parent, SelfPanel.from_strings(["theorem clean : True := trivial"])
    )
    assert killed is False
    assert type(outcome) is KillConditionRefusal
    assert outcome.code == "INVALID_MATCH_PATTERN"
    assert outcome.clone_id == "RULE-CLONE-BAD"
    assert outcome.parent_id == "RULE-PARENT"
    assert outcome.authority_effect == "None"


def test_kill_condition_refusal_rejects_duck_typed_equality() -> None:
    refusal = KillConditionRefusal(
        clone_id="C", parent_id="P", match_pattern="(", reason="bad", code="INVALID_MATCH_PATTERN"
    )

    @dataclass(frozen=True)
    class Duck:
        clone_id: str = "C"
        parent_id: str = "P"
        match_pattern: str = "("
        reason: str = "bad"
        code: str = "INVALID_MATCH_PATTERN"
        authority_effect: str = "None"

    assert refusal != Duck()
    assert refusal == KillConditionRefusal(
        clone_id="C", parent_id="P", match_pattern="(", reason="bad", code="INVALID_MATCH_PATTERN"
    )


# 3. The Treg threshold is inclusive: toxicity at or above tau downgrades.
# Mutation: comparing with > instead of >=.


def test_treg_downgrades_at_exactly_tau() -> None:
    supervisor = TregSupervisor(tau=Fraction(1, 5))
    report = supervisor.evaluate_toxicity("RULE-EDGE", triggers=[(True, False)] + [(True, True)] * 4)
    assert report.toxicity_index == Fraction(1, 5)
    antibody = supervisor.synthesize_treg(report)
    assert antibody is not None
    assert antibody.downgraded_authority == "DIAGNOSTIC_ONLY"
    assert "meets or exceeds" in antibody.reason


def test_treg_keeps_a_detector_just_below_tau() -> None:
    supervisor = TregSupervisor(tau=Fraction(1, 5))
    report = supervisor.evaluate_toxicity("RULE-BELOW", triggers=[(True, False)] + [(True, True)] * 5)
    assert report.toxicity_index == Fraction(1, 6)
    assert supervisor.synthesize_treg(report) is None


def test_treg_prompt_corpus_toxicity_is_zero_or_one() -> None:
    supervisor = TregSupervisor(tau=Fraction(1, 5))
    corpus = ["benign prompt number %d" % i for i in range(9)] + ["mentions eval once"]
    firing = supervisor.evaluate_toxicity("RULE-FIRES", prompt_corpus=corpus, rule=_rule(pattern="eval"))
    silent = supervisor.evaluate_toxicity("RULE-SILENT", prompt_corpus=corpus, rule=_rule(pattern="zzz_never"))
    assert firing.toxicity_index == Fraction(1)
    assert silent.toxicity_index == Fraction(0)
    assert supervisor.synthesize_treg(firing) is not None
    assert supervisor.synthesize_treg(silent) is None


# 4. The canonical self panel is thinner than its count. Pinned until the
# panel is regenerated and resealed (see documentation/immune/SELF_PANEL_DIVERSITY.md).
# Mutation: counting raw entries instead of base contents.


def test_canonical_self_panel_has_forty_distinct_base_contents() -> None:
    panel = SelfPanel.load_canonical()
    assert len(panel) == 1000
    bases = panel.distinct_base_contents()
    assert len(bases) == 40
    per_category: dict[str, set[str]] = {}
    for entry in panel:
        per_category.setdefault(entry.category, set()).add(SelfPanel.base_content(entry.content))
    assert {category: len(found) for category, found in per_category.items()} == {
        "clean_lean4_proof": 10,
        "clean_architecture_port": 10,
        "clean_prompt_template": 10,
        "clean_physics_expression": 10,
    }


def test_base_content_strips_only_the_synthetic_trailer() -> None:
    assert SelfPanel.base_content("x = 1  -- index 007 hash_mod_42") == "x = 1"
    assert SelfPanel.base_content("-- a real Lean comment") == "-- a real Lean comment"
    panel = SelfPanel.from_strings(["a -- index 001 hash_mod_3", "a -- index 002 hash_mod_9", "b"])
    assert panel.distinct_base_contents() == frozenset({"a", "b"})


# 5. Proofreading normalizes hyphenation, whitespace and case before matching.
# Mutation: letting a word-internal hyphen count as an equation character.

_PSEUDO = "The sign problem vanishes by symmetry, and gauge invariance guarantees positivity."


def _status(text: str) -> str:
    return HopfieldNinioProofreader().proofread("CAND", text).status


def test_buzzword_pseudo_proof_dissociates() -> None:
    assert _status(_PSEUDO) == "DISSOCIATED_DURING_DELAY"


def test_word_internal_hyphen_does_not_rescue_a_pseudo_proof() -> None:
    assert _status(_PSEUDO + " The weights are sign-free.") == "DISSOCIATED_DURING_DELAY"
    assert _status(_PSEUDO + " It holds and/or generalizes.") == "DISSOCIATED_DURING_DELAY"


def test_buzzwords_match_across_hyphenation_whitespace_and_case() -> None:
    text = "By\n  SYMMETRY the Gauge-Invariance argument settles it."
    assert _status(text) == "DISSOCIATED_DURING_DELAY"


def test_a_real_equation_is_still_admitted() -> None:
    text = "By symmetry and gauge invariance, Z = sum_i w_i x_i = 0 for every sign-free weight."
    assert _status(text) == "CATALYTIC_ADMISSION"
