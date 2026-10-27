# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""The embargo guard.

Until the second derivation freezes, the engine refuses, by name
(``GUARD_EMBARGO``) and **before any computation**, every request on this
list.  The list is written in native terms and pinned by digest in the
tests.  A refused request is never evaluated, not even to check it.

AuthorityEffect: None
"""

from __future__ import annotations

from dataclasses import dataclass

from .canon import dumps, sha256_hex
from .errors import EmbargoRefusal

MAX_ITEMS_UNDER_EMBARGO = 3

EMBARGO_LIST: tuple[tuple[str, str], ...] = (
    ("four_item_delta", "any delta of four or more items, of any kind, on any regime"),
    ("growth", "the sealed supply-and-continuation policy or its closure policy; "
               "hosting a fixture is a one-shot supplied presentation, not growth"),
    ("removal", "any removal event; the item grammar is additive"),
    ("declared_responder", "any declared responder for the second derivation's stake"),
    ("first_demand_index", "anything about the first-demand index under the implemented "
                           "isomorphism (the next rung's question)"),
    ("second_state", "loading any research/second* state"),
    ("history_symmetry", "anything about symmetry along a history on the sealed carrier: whether the size of "
                         "the automorphism group under the implemented isomorphism is preserved or monotone "
                         "along the events of a history, and at which event kinds it moves (the running "
                         "rung's question)"),
    ("element_count_succession", "anything about whether the element count settles the census row for "
                                 "succession: rung six's question, asked of the second derivation's census "
                                 "of challenge five"),
    ("duration_under_changing", "anything about duration under changing: round counts, or how long a history "
                                "lasts while its state changes, on the sealed carrier (rung seven's question, "
                                "rung six's named next leftover W-1)"),
    ("element_count_across_isomorphism", "anything about whether two isomorphic regimes always have the same "
                                         "element count, or about element counts across isomorphism classes, on "
                                         "the sealed carrier (rung seven's named next rung Z-1, reserved while the "
                                         "rung sequence is paused)"),
    ("shortest_class_matched_witnesses", "anything about the shortest class-matched witnesses over stakes: rung "
                                         "eight's leftover candidate Y-1, from the second derivation's index "
                                         "tree, while rung eight runs"),
    ("census_undecided_rows_x6", "anything about the undecided rows of the second derivation's census (two-ness, "
                                 "observational classes, adjacency, reach, branching and exhaustion, as its index and "
                                 "class trees name them) computed for the second derivation's regimes, histories or "
                                 "stakes: rung nine's X-6, while rung nine runs"),
    ("second_derivation_engine_class", "anything that declares the second derivation's engine class, enumerates "
                                       "minimal engines from its surviving stakes, applies its two continuation "
                                       "rules and validity rules, counts their capabilities, or runs those engines "
                                       "forward (its Challenges 3 and 4), and every FORCED column of its census: "
                                       "the continuation the author ruled (19L57G1 #266), while it runs; the level "
                                       "engine's own stage-change machinery is not that class"),
)

EMBARGO_KINDS = frozenset(k for k, _ in EMBARGO_LIST)


def embargo_digest() -> str:
    return sha256_hex(dumps([list(e) for e in EMBARGO_LIST]))


def refuse(kind: str, detail: str = "") -> EmbargoRefusal:
    if kind not in EMBARGO_KINDS:
        raise ValueError(f"unknown embargo kind {kind!r}")
    return EmbargoRefusal("GUARD_EMBARGO", f"{kind}: {detail}" if detail else kind)


@dataclass(frozen=True)
class ResourceBound:
    """How far a search runs.  Raising it is never a lift.  Under the
    embargo it is at most three items; a larger bound cannot be built."""

    max_items: int

    def __post_init__(self) -> None:
        if isinstance(self.max_items, bool) or not isinstance(self.max_items, int):
            raise EmbargoRefusal("GUARD_EMBARGO", "a bound is a plain integer")
        if self.max_items > MAX_ITEMS_UNDER_EMBARGO:
            raise refuse("four_item_delta", f"requested max_items={self.max_items}")
        if self.max_items < 0:
            raise ValueError("negative bound")


def check_delta_size(n_items: int) -> None:
    if n_items > MAX_ITEMS_UNDER_EMBARGO:
        raise refuse("four_item_delta", f"a delta of {n_items} items")


def request(kind: str, detail: str = "") -> None:
    """Any embargoed capability is requested through here and refused."""
    raise refuse(kind, detail)
