"""Doc 08 section 6's Four Non-Forced Premises: P1-vs-P2 policy disagreement,
and the Survivor Birth-Death Identity (Theorem 6.2).

AuthorityEffect: None.

Source: `1_historical_documents/08_the_higher_ladder_mss8_to_mss15.md`
sections 6.2-6.3. That document cites its own detail as living in
`raw/mss_15_rbg_proof_program.md` -- the `raw/` directory does not exist
anywhere in this repository (confirmed absent, matching the same wrong-path
pattern already flagged in N0/N2's own reader-check exercises), so this
module works only from Doc 08's own text, not from that uncited file.

Doc 08 does not give worked numeric examples for the six Forcing Policies
(P1 Fewest Primitive Constructors, P2 Minimum Description Length) -- it
states them in prose only. The `LiftCandidate` fixture below is this
series' own small, declared, illustrative instance built to satisfy the
doc's own description of each policy's measure; the specific numbers
(`n_rewrite_rules`, `description_bits`) are DECLARED by this module, not
extracted from any source document, and are chosen specifically to make P1
and P2 disagree -- exhibiting Premise 1's point (a unique next lift is not
forced; different declared cost measures rank the same candidates
differently) as a real, computed disagreement rather than an assertion.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "LiftCandidate",
    "PARITY_TAG",
    "LENGTH_SCHEMA",
    "CANDIDATES",
    "rank_by_fewest_constructors_then_rules",
    "rank_by_description_length",
    "all_tied_under",
    "SurvivorState",
    "apply_birth_death_step",
]


@dataclass(frozen=True)
class LiftCandidate:
    """One candidate minimal refinement resolving the doc's own forced
    collision `<a> !~ <ab>` (Theorem 6.1), carrying the two declared cost
    measures Policies P1 and P2 each minimize.
    """

    name: str
    n_constructors: int  # Policy P1's primary measure: |delta Sigma_n|
    n_rewrite_rules: int  # Policy P1's stated tie-break
    description_bits: int  # Policy P2's measure: declared MDL cost


# Doc section 6.2's own two examples (Premise 1): refinement by parity
# (distinguishes 1 from 2, but equates 1 and 3 -- a flat, non-recursive
# tag) vs. refinement by length (a recursive zero/successor schema that
# also separates 1 from 3). Declared costs: parity needs only one flat
# rewrite rule, but a flat tag's description does not compress with scale;
# length needs one extra rewrite rule (the successor case) but its
# recursive schema has a shorter total description than re-stating a flat
# tag's case-by-case behavior -- a real, well-known shape of MDL
# comparisons, illustrated here on two small fixed fixtures, not derived
# from an actual Kolmogorov-complexity computation (which is uncomputable
# in general).
PARITY_TAG = LiftCandidate(
    name="parity_tag", n_constructors=1, n_rewrite_rules=1, description_bits=20
)
LENGTH_SCHEMA = LiftCandidate(
    name="length_schema", n_constructors=1, n_rewrite_rules=2, description_bits=11
)
CANDIDATES: tuple[LiftCandidate, ...] = (PARITY_TAG, LENGTH_SCHEMA)


def rank_by_fewest_constructors_then_rules(
    candidates: tuple[LiftCandidate, ...],
) -> LiftCandidate:
    """Policy P1: minimize constructor count, tie-break by rewrite-rule
    count, then by lowest total arity (arity is not modeled in this small
    fixture -- both candidates are arity-1 taggers, so the doc's own
    tie-break never needs to go past rewrite-rule count here).
    """
    return min(candidates, key=lambda c: (c.n_constructors, c.n_rewrite_rules))


def rank_by_description_length(candidates: tuple[LiftCandidate, ...]) -> LiftCandidate:
    """Policy P2: minimize the declared MDL encoding cost."""
    return min(candidates, key=lambda c: c.description_bits)


def all_tied_under(candidates: tuple[LiftCandidate, ...], key) -> tuple[LiftCandidate, ...]:
    """Policy P6: retain every candidate tied for minimal under `key`,
    rather than breaking the tie -- "the default honest mathematical
    posture when uniqueness cannot be established" (doc section 6.3).
    """
    best = key(min(candidates, key=key))
    return tuple(c for c in candidates if key(c) == best)


# --- Premise 4: Survivor Accounting and the Birth-Death Identity -----------


@dataclass(frozen=True)
class SurvivorState:
    """A toy `Surv_n` (doc section 6.2's Premise 4): each element of
    `raw_survivors` stands for one `(x, y)` pair that collides under the
    level-`level` quotient while remaining distinguished by some active
    demand -- an abstract stand-in for the doc's own
    `(x, y, d) in D_{<=n}` triples, small enough to check by hand.
    """

    level: int
    raw_survivors: frozenset[tuple]


def apply_birth_death_step(
    state: SurvivorState, died: frozenset[tuple], born: frozenset[tuple]
) -> SurvivorState:
    """One lift step from level `n` to `n+1`. `died` must be exactly the
    survivors resolved by this lift (a subset of the current set); `born`
    must be genuinely new (disjoint from what remains after removing
    `died`) -- both are checked, not assumed. Returns the new state, and
    Theorem 6.2's identity `s_{n+1} = s_n - d_{n+1} + b_{n+1}` is asserted
    against the actual resulting set sizes before returning, so this is a
    real structural check on set operations, not a restatement of the
    arithmetic it is meant to verify.
    """
    if not died <= state.raw_survivors:
        raise ValueError(f"died set {died!r} is not a subset of the current survivors")
    remaining = state.raw_survivors - died
    overlap = remaining & born
    if overlap:
        raise ValueError(f"born set {born!r} is not new -- overlaps remaining survivors {overlap!r}")
    new_state = SurvivorState(level=state.level + 1, raw_survivors=remaining | born)
    assert len(new_state.raw_survivors) == len(state.raw_survivors) - len(died) + len(born)
    return new_state
