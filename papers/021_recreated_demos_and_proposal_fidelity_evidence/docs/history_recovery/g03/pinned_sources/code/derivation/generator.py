"""F5 run: reflective growth composed with pair-separation closure.

Classification: metatheory apparatus for
``paper/endogenous_generator.md``.  The question (F5 of
``paper/refusal_as_difference.md``): is the composite of the declared
reflective refusal semantics and the pair-separation closure policy a
self-sustaining challenge generator with no per-round external act —
and is the full obstruction-*repair* cycle self-sustaining, or does
every repair strategy in a declared class either import per repair,
act vacuously, or end generation?

Declared bounds: fifteen accepted rounds per branch (the standing
per-branch bound); observation depths 1 and 2; the five-strategy repair
class below.  Everything here is deterministic; no model judgment
decides separability, repair, or classification.  Horizon-free halves
are in ``lean4/Derivation/Generator.lean``; this module computes the
bounded trajectories and the in-bounds exclusion.

The chain at round ``n`` is the reflective chain proved in Lean:
carrier ``0..n``, tags ``1..n``, relation the successor edges.  Element
indices are metatheoretic bookkeeping; observation sees only tags,
incident edges, and (per strategy) marks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional

ROUNDS = 15

Profile1 = tuple[bool, bool, bool]
Profile2 = tuple[Profile1, tuple[Profile1, ...], tuple[Profile1, ...]]
View = tuple[object, ...]

STRATEGIES = (
    "none",
    "per_pair_fresh_mark",
    "automark_presence",
    "automark_valued",
    "depth2",
)

ONE_TIME_IMPORTS: dict[str, tuple[str, ...]] = {
    "none": (),
    "per_pair_fresh_mark": (),
    "automark_presence": ("automark presence rule (vacuous: receipts "
                          "are already tagged)",),
    "automark_valued": ("automark valued rule (unbounded observable "
                        "alphabet - identity-grade observation)",),
    "depth2": ("observation regime raised to depth 2",),
}


def chain_tags(n: int) -> frozenset[int]:
    return frozenset(range(1, n + 1))


def chain_rel(n: int) -> tuple[tuple[int, int], ...]:
    return tuple((k, k + 1) for k in range(n))


def profile1(n: int, i: int) -> Profile1:
    tags = chain_tags(n)
    rel = chain_rel(n)
    return (
        i in tags,
        any(b == i for (_, b) in rel),
        any(a == i for (a, _) in rel),
    )


def profile2(n: int, i: int) -> Profile2:
    rel = chain_rel(n)
    return (
        profile1(n, i),
        tuple(profile1(n, a) for (a, b) in rel if b == i),
        tuple(profile1(n, b) for (a, b) in rel if a == i),
    )


def view(
    strategy: str, n: int, i: int, marks: Mapping[int, frozenset[int]]
) -> View:
    """What the declared observation regime sees of element ``i``.

    ``automark_presence`` adds a presence bit that every receipt
    carries — indistinguishable from the tag bit already in the
    profile; ``automark_valued`` exposes the mark *value* (the index:
    presentation identity made observable); ``per_pair_fresh_mark``
    exposes the set of repair observables applied to ``i``."""
    if strategy == "depth2":
        return (profile2(n, i),)
    base: View = (profile1(n, i),)
    if strategy == "automark_presence":
        return base + (i >= 1,)
    if strategy == "automark_valued":
        return base + (i,)
    if strategy == "per_pair_fresh_mark":
        return base + (marks.get(i, frozenset()),)
    return base


def obstructions(
    strategy: str, n: int, marks: Mapping[int, frozenset[int]]
) -> list[tuple[int, int]]:
    """The closure policy's demand: all unordered pairs of distinct
    carrier elements the regime cannot separate."""
    views = [view(strategy, n, i, marks) for i in range(n + 1)]
    return [
        (i, j)
        for i in range(n + 1)
        for j in range(i + 1, n + 1)
        if views[i] == views[j]
    ]


@dataclass
class RoundRecord:
    round_no: int
    obstructions_before: int
    first_pair: Optional[tuple[int, int]]
    repairs: int
    imports_this_round: int
    obstructions_after: int

    def json(self) -> dict[str, object]:
        return {
            "round": self.round_no,
            "obstructions_before": self.obstructions_before,
            "first_pair": (
                list(self.first_pair) if self.first_pair else None
            ),
            "repairs": self.repairs,
            "imports_this_round": self.imports_this_round,
            "obstructions_after": self.obstructions_after,
        }


@dataclass
class BranchReport:
    strategy: str
    rounds: list[RoundRecord] = field(default_factory=list)

    def fired_ever(self) -> bool:
        return any(r.obstructions_before > 0 for r in self.rounds)

    def repaired_every_round(self) -> bool:
        return all(r.obstructions_after == 0 for r in self.rounds)

    def per_round_import_rounds(self) -> int:
        return sum(1 for r in self.rounds if r.imports_this_round > 0)

    def first_fire_round(self) -> Optional[int]:
        fires = [
            r.round_no for r in self.rounds if r.obstructions_before > 0
        ]
        return min(fires) if fires else None

    def classification(self) -> str:
        """Decided by the implemented predicates alone.  The F5-positive
        class is ``endogenous_cycle``: the generator fires, every
        obstruction is repaired, and no round imports."""
        if (
            self.fired_ever()
            and self.repaired_every_round()
            and self.per_round_import_rounds() == 0
        ):
            return "endogenous_cycle"
        if not self.fired_ever():
            return "generation_dead"
        if self.repaired_every_round():
            return "repairs_by_recurring_imports"
        return "fires_unrepaired"

    def json(self) -> dict[str, object]:
        return {
            "strategy": self.strategy,
            "one_time_imports": list(ONE_TIME_IMPORTS[self.strategy]),
            "rounds": [r.json() for r in self.rounds],
            "fired_ever": self.fired_ever(),
            "first_fire_round": self.first_fire_round(),
            "repaired_every_round": self.repaired_every_round(),
            "per_round_import_rounds": self.per_round_import_rounds(),
            "classification": self.classification(),
        }


def repair_per_pair(
    n: int, marks: dict[int, frozenset[int]], next_mark: int
) -> tuple[int, int]:
    """Deterministic per-pair repair: while an obstruction exists, mint
    a fresh observable and apply it to the larger element of the
    lexicographically first unseparated pair.  Returns (repairs done,
    next fresh mark id).  Every repair is an external act."""
    repairs = 0
    while True:
        obs = obstructions("per_pair_fresh_mark", n, marks)
        if not obs:
            return repairs, next_mark
        _, j = obs[0]
        marks[j] = marks.get(j, frozenset()) | {next_mark}
        next_mark += 1
        repairs += 1


def run_branch(strategy: str, rounds: int = ROUNDS) -> BranchReport:
    """One branch: per round, one reflective growth step (internally
    enabled — never counted as an import), then the closure demand,
    then the strategy's repair."""
    report = BranchReport(strategy)
    marks: dict[int, frozenset[int]] = {}
    next_mark = 0
    for n in range(1, rounds + 1):
        obs = obstructions(strategy, n, marks)
        repairs = 0
        imports_now = 0
        if strategy == "per_pair_fresh_mark" and obs:
            repairs, new_next = repair_per_pair(n, marks, next_mark)
            imports_now = new_next - next_mark
            next_mark = new_next
        after = obstructions(strategy, n, marks)
        report.rounds.append(
            RoundRecord(
                round_no=n,
                obstructions_before=len(obs),
                first_pair=obs[0] if obs else None,
                repairs=repairs,
                imports_this_round=imports_now,
                obstructions_after=len(after),
            )
        )
    return report


def exclusion_check(rounds: int = ROUNDS) -> dict[str, object]:
    """The F5 decision within bounds: does any declared strategy
    realize the endogenous cycle (fires, repairs, never imports)?"""
    branches = [run_branch(s, rounds) for s in STRATEGIES]
    found = [
        b.strategy
        for b in branches
        if b.classification() == "endogenous_cycle"
    ]
    return {
        "rounds": rounds,
        "strategies": [b.json() for b in branches],
        "endogenous_cycle_found": bool(found),
        "endogenous_cycle_strategies": found,
        "classification_table": {
            b.strategy: b.classification() for b in branches
        },
    }


def middle_pairs(n: int) -> list[tuple[int, int]]:
    """The interior pairs — by the Lean exactness theorem, exactly the
    depth-1 obstructions of the bare chain."""
    return [
        (i, j)
        for i in range(1, n)
        for j in range(i + 1, n)
    ]


def lean_agreement(max_n: int = ROUNDS) -> dict[str, object]:
    """Cross-checks against the Lean theorems, decided by computation:
    obstruction exactness at depth 1; depth-2 near-end separation at
    n=4 and deep-interior collapse at n=5; valued marks separating
    every pair."""
    exactness = all(
        obstructions("none", n, {}) == middle_pairs(n)
        for n in range(1, max_n + 1)
    )
    depth2_separates = profile2(4, 1) != profile2(4, 3)
    depth2_outrun = profile2(5, 2) == profile2(5, 3)
    valued_total = all(
        len(obstructions("automark_valued", n, {})) == 0
        for n in range(1, max_n + 1)
    )
    return {
        "depth1_obstructions_are_exactly_middle_pairs": exactness,
        "depth2_separates_near_ends_n4": depth2_separates,
        "depth2_obstruction_n5": depth2_outrun,
        "valued_marks_collapse_generation": valued_total,
    }
