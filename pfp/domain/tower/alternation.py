"""A brute-force bounded-alternation evaluator, and a real, hand-checkable
instance of the 4-vs-5-alternation collapse disagreement Doc 08's own
Theorem 3.1 (Alternation Irreducibility) describes.

AuthorityEffect: None.

Source: `1_historical_documents/08_the_higher_ladder_mss8_to_mss15.md`
sections 1-4 and `0_research_briefs/30_higher_ordinals_and_oracle_towers.md`.

This module does not implement, simulate, or claim to instantiate any real
oracle-Turing-machine stack -- none exists in this repository (confirmed
absent during research). What it does is smaller and fully honest: it
brute-force evaluates bounded prenex formulas over tiny finite domains, and
uses that evaluator to EXHIBIT (not merely assert) a concrete instance where
a naive "collapse two alternating quantifier layers into one paired move"
strategy gives the WRONG truth value. The instance is small enough to be
checked by hand (see the module-level docstring math in
`FOUR_VS_FIVE_DISAGREEMENT_EXPLANATION` and tests/test_mssn_alternation.py).
"""

from __future__ import annotations

from itertools import product
from typing import Callable

__all__ = [
    "evaluate_alternating_formula",
    "domain_size_cost",
    "four_vs_five_predicate",
    "evaluate_full_five_alternation",
    "evaluate_naive_four_collapse",
    "FOUR_VS_FIVE_DISAGREEMENT_EXPLANATION",
    "GeographyGame",
]

Predicate = Callable[..., bool]


def evaluate_alternating_formula(
    predicate: Predicate, domain: tuple, num_quantifiers: int, first_is_exists: bool = True
) -> bool:
    """Brute-force evaluation of a bounded prenex formula
    `Q1 x1 Q2 x2 ... Qk xk. predicate(x1, ..., xk)` where the quantifiers
    strictly alternate starting with `exists` (if `first_is_exists`) or
    `forall`, over the given finite `domain`. This is the honest, exhaustive
    definition -- no shortcuts, no memoization tricks that would themselves
    smuggle in an assumption about independence between quantifier layers.
    """

    def go(depth: int, assigned: tuple) -> bool:
        if depth == num_quantifiers:
            return predicate(*assigned)
        is_exists = (depth % 2 == 0) == first_is_exists
        if is_exists:
            return any(go(depth + 1, assigned + (x,)) for x in domain)
        return all(go(depth + 1, assigned + (x,)) for x in domain)

    return go(0, ())


def domain_size_cost(domain_size: int, num_quantifiers: int) -> int:
    """The brute-force cost of `evaluate_alternating_formula`: |domain|^k
    predicate-argument-tuples in the worst case (doc's own point, section
    2.2: real alternation depth is computationally expensive even though it
    remains decidable over a bounded domain -- this is exactly why the
    domains used in this module and in N8-N10 stay tiny).
    """
    return domain_size**num_quantifiers


# --- The 4-vs-5 disagreement instance (Doc 08 section 3.4) -----------------

FOUR_VS_FIVE_DISAGREEMENT_EXPLANATION = """
Predicate: P(x1, x2, x3, x4, x5) := (x3 == x2) and (x5 == x4) and (x1 == 0)
Domain: {0, 1} (or larger -- the disagreement holds for any domain size >= 2)

The TRUE 5-alternation statement:
    exists x1. forall x2. exists x3. forall x4. exists x5. P(x1,x2,x3,x4,x5)
is TRUE: pick x1=0; for every x2, pick x3=x2 (always legal, since x3 ranges
over the whole domain); for every x4, pick x5=x4. Every clause of P is then
satisfied by construction, for every choice of x2 and x4.

The NAIVE "4-alternation collapse" that pairs (x1, x3) into ONE existential
move made before x2 is revealed:
    exists (x1,x3). forall x2. forall x4. exists x5. P(x1,x2,x3,x4,x5)
is FALSE whenever |domain| >= 2: once x3 is fixed to some single value c
before x2 is known, the clause "x3 == x2" fails for every x2 != c, so the
inner "forall x2" clause is never satisfied by any single fixed (x1, x3)
pair -- there is no legal move for the collapsed existential to make.

This is a real, computed disagreement (5-alternation TRUE, naive 4-collapse
FALSE) on ONE concrete predicate and domain, not an assertion about
alternation hierarchies in general. See Doc 08 section 3.4's own Skolem
dependency chain argument for the general shape this instance witnesses:
x3 must be a genuine FUNCTION of x2 (a Skolem function f3(x2) = x2 here),
and a pre-committed single value cannot stand in for that function.
"""


def four_vs_five_predicate(x1: int, x2: int, x3: int, x4: int, x5: int) -> bool:
    return (x3 == x2) and (x5 == x4) and (x1 == 0)


def evaluate_full_five_alternation(domain: tuple) -> bool:
    """The honest, correctly-alternating 5-quantifier evaluation."""
    return evaluate_alternating_formula(four_vs_five_predicate, domain, num_quantifiers=5)


def evaluate_naive_four_collapse(domain: tuple) -> bool:
    """The naive attempt to fold (x1, x3) into one paired existential move
    made before x2 is known -- computed directly (not via
    evaluate_alternating_formula, since the whole point is that this collapse
    is a DIFFERENT, non-equivalent formula, not a valid rewriting of the
    5-alternation one).
    """
    return any(
        all(
            all(
                any(four_vs_five_predicate(x1, x2, x3, x4, x5) for x5 in domain)
                for x4 in domain
            )
            for x2 in domain
        )
        for x1, x3 in product(domain, domain)
    )


# --- A small, always-terminating finite alternating game (Doc 08 section 4) -


class GeographyGame:
    """A tiny finite directed-graph token-passing game (the shape Doc 08
    section 4.1 cites as its own canonical example of "high alternation,
    zero unbounded recursion"): two players alternate moving a token along
    directed edges; a player who cannot move loses; no edge may be reused
    within a single play. Because the edge set is finite and strictly
    shrinks by one every move (no revisits), termination is guaranteed
    within `len(edges)` moves -- this is proved directly by
    `play_and_confirm_termination`'s own move-count bound check, not merely
    claimed.
    """

    def __init__(self, edges: frozenset[tuple[str, str]], start: str) -> None:
        self.edges = edges
        self.start = start

    def _available_moves(self, position: str, used_edges: frozenset) -> list[tuple[str, str]]:
        return [
            (u, v)
            for (u, v) in self.edges
            if u == position and (u, v) not in used_edges
        ]

    def player_to_move_wins(
        self, position: str | None = None, used_edges: frozenset = frozenset()
    ) -> bool:
        """True iff the player ABOUT TO MOVE from `position` wins under
        optimal play (standard normal-play convention: no legal move means
        the player to move loses).
        """
        if position is None:
            position = self.start
        moves = self._available_moves(position, used_edges)
        if not moves:
            return False  # the player to move has no move: they lose
        return any(
            not self.player_to_move_wins(v, used_edges | {(u, v)}) for (u, v) in moves
        )

    def play_and_confirm_termination(self) -> dict:
        """Plays out one full optimal-play game (both players playing to
        win where possible), returning the move count, the final position,
        and a direct check that the move count never exceeded len(edges) --
        the concrete termination bound this game-shape guarantees.
        """
        position = self.start
        used: frozenset = frozenset()
        move_count = 0
        while True:
            moves = self._available_moves(position, used)
            if not moves:
                break
            # Optimal play: pick a move that leaves the opponent losing, if
            # one exists; otherwise any legal move (this player is losing
            # regardless).
            winning_moves = [
                (u, v) for (u, v) in moves if not self.player_to_move_wins(v, used | {(u, v)})
            ]
            chosen = winning_moves[0] if winning_moves else moves[0]
            used = used | {chosen}
            position = chosen[1]
            move_count += 1
        return {
            "final_position": position,
            "move_count": move_count,
            "bound_respected": move_count <= len(self.edges),
            "terminated": True,
        }
