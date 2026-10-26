"""The extended state: an admitted regime, typed requirements, and claim/witness form split.

Classification: Domain Solvers Extended Regime Model.
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .errors import ClaimFrozen, StageRefusal
from .guards import check_delta_size, refuse
from .kinds import RegimeOracle, Req, forms_of, satisfies
from .regime import (
    AdmitForm,
    Delta,
    Event,
    NewDatum,
    NewForm,
    NewInst,
    NewRuleAll,
    Regime,
    apply_delta,
    delta_events,
    replay,
)

ITEM_KINDS = frozenset({"witness_inst", "witness_form", "datum"})
EMBARGOED_ITEM_KINDS = {
    "growth": "growth",
    "removal": "removal",
    "responder": "declared_responder",
}


@dataclass(frozen=True)
class Stage:
    """A capability stage: which item kinds a response may use, and largest witness arity."""

    name: str
    index: int
    item_kinds: frozenset[str]
    witness_arity: int

    def __post_init__(self) -> None:
        for k in self.item_kinds:
            if k in EMBARGOED_ITEM_KINDS:
                raise refuse(EMBARGOED_ITEM_KINDS[k], f"stage {self.name} asks for {k}")
            if k == "rule":
                raise StageRefusal("RULE_ITEM", "a uniform rule is never a response item")
            if k not in ITEM_KINDS:
                raise StageRefusal("ITEM_KIND", f"unknown item kind {k}")
        if self.witness_arity < 1:
            raise StageRefusal("WITNESS_ARITY", "witness arity must be at least 1")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.name == other.name
            and self.index == other.index
            and self.item_kinds == other.item_kinds
            and self.witness_arity == other.witness_arity
        )

    def capabilities(self) -> frozenset[str]:
        return self.item_kinds | {f"arity{k}" for k in range(1, self.witness_arity + 1)}


BASE = Stage("base", 0, frozenset({"witness_inst", "witness_form"}), 2)


@dataclass(frozen=True)
class RegimeK:
    base: Regime
    history: tuple[Event, ...]
    reqs: tuple[Req, ...]
    claim_forms: frozenset[int]
    witness_forms: tuple[tuple[int, tuple[int, ...]], ...] = field(default=())
    new_forms_allowed: bool = False

    def __post_init__(self) -> None:
        if replay(self.history) != self.base:
            raise StageRefusal("REPLAY_MISMATCH", "history does not replay to the regime")
        wf = {f for f, _ in self.witness_forms}
        if wf & self.claim_forms:
            raise StageRefusal("SPLIT", "a form cannot be both claim and witness")
        if (wf | self.claim_forms) != set(range(len(self.base.forms))):
            raise StageRefusal("SPLIT", "every form must be a claim form or a witness form")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.base == other.base
            and self.history == other.history
            and self.reqs == other.reqs
            and self.claim_forms == other.claim_forms
            and self.witness_forms == other.witness_forms
            and self.new_forms_allowed == other.new_forms_allowed
        )

    def witness_form_set(self) -> frozenset[int]:
        return frozenset(f for f, _ in self.witness_forms)

    def sorts_of(self, f: int) -> tuple[int, ...]:
        for g, s in self.witness_forms:
            if g == f:
                return s
        raise KeyError(f)

    def claim_only(self, q: Req) -> bool:
        fs = forms_of(q)
        return fs is not None and fs <= self.claim_forms


def host(
    base_history: tuple[Event, ...],
    claim_forms: frozenset[int],
    reqs: tuple[Req, ...],
    witness_forms: tuple[tuple[int, tuple[int, ...]], ...] = (),
    new_forms_allowed: bool = False,
) -> RegimeK:
    """Declare witness forms on top of a hosted claim."""
    base = replay(base_history)
    events = list(base_history)
    declared: list[tuple[int, tuple[int, ...]]] = []
    nf = len(base.forms)
    for k, (arity, sorts) in enumerate(witness_forms):
        events.append(AdmitForm(arity))
        declared.append((nf + k, sorts))
    hist = tuple(events)
    return RegimeK(replay(hist), hist, reqs, claim_forms, tuple(declared), new_forms_allowed)


def check_witness_only(s: RegimeK, stage: Stage, delta: Delta) -> None:
    """Refuse, before state changes, any delta outside stage capabilities."""
    check_delta_size(len(delta))
    nf = len(s.base.forms)
    new_forms = [it for it in delta if isinstance(it, NewForm)]
    for it in delta:
        if isinstance(it, NewInst) and it.form < nf and it.form in s.claim_forms:
            raise ClaimFrozen("CLAIM_FROZEN", f"an instance on claim form {it.form}")
        if isinstance(it, NewRuleAll):
            if it.form < nf and it.form in s.claim_forms:
                raise ClaimFrozen("CLAIM_FROZEN", f"a uniform rule on claim form {it.form}")
            raise StageRefusal("RULE_ITEM", "a uniform rule is never a response item")
        if isinstance(it, NewDatum) and "datum" not in stage.item_kinds:
            raise StageRefusal("ITEM_KIND", f"fresh data are not a capability of stage {stage.name}")
        if isinstance(it, NewForm):
            if "witness_form" not in stage.item_kinds or not s.new_forms_allowed:
                raise StageRefusal("ITEM_KIND", "a fresh witness form is not available here")
            if it.arity > stage.witness_arity:
                raise StageRefusal("WITNESS_ARITY", f"arity {it.arity} above {stage.witness_arity}")
        if isinstance(it, NewInst) and it.form >= nf and it.form - nf >= len(new_forms):
            raise StageRefusal("MALFORMED_DELTA", "an instance on a form the delta does not create")
        if isinstance(it, NewInst) and it.form < nf:
            arity = s.base.forms[it.form]
            if arity > stage.witness_arity:
                raise StageRefusal("WITNESS_ARITY", f"witness form {it.form} has arity {arity}")


def admit_response(s: RegimeK, stage: Stage, delta: Delta) -> RegimeK:
    """The only path from a response to a regime."""
    check_witness_only(s, stage, delta)
    nf = len(s.base.forms)
    child = apply_delta(s.base, delta)
    events = s.history + delta_events(s.base, delta)
    new = tuple((nf + k, ()) for k in range(len(child.forms) - nf))
    return RegimeK(
        child,
        events,
        s.reqs,
        s.claim_forms,
        s.witness_forms + new,
        s.new_forms_allowed,
    )


def valid_response(s: RegimeK, stage: Stage, delta: Delta) -> bool:
    child = admit_response(s, stage, delta)
    o = RegimeOracle(child.base)
    return all(satisfies(o, q) for q in s.reqs)


def claims_unchanged(s: RegimeK, child: RegimeK) -> bool:
    """The instances of every claim form are identical in child."""
    before = {i for i in s.base.insts if i[0] in s.claim_forms}
    after = {i for i in child.base.insts if i[0] in s.claim_forms}
    return before == after


__all__ = [
    "BASE",
    "RegimeK",
    "Stage",
    "admit_response",
    "check_witness_only",
    "claims_unchanged",
    "host",
    "valid_response",
]
