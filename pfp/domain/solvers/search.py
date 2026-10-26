"""Declared finite candidate classes, same-stage exhaustion, and minimal witness search.

Classification: Domain Solvers Search Engine.
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import combinations, product
from math import comb
from typing import Literal

from .errors import Refusal
from .guards import ResourceBound
from .iso import IsoBudgetError, _class_perms, _perm_count, _refine, serialize
from .kinds import (
    Closure,
    Holds,
    RegimeOracle,
    Separate,
    Total,
    refutation,
    rename_req,
    req_json,
)
from .regime import (
    Delta,
    Item,
    NewDatum,
    NewForm,
    NewInst,
    canonical_delta,
    item_key,
    mu2,
)
from .regimek import RegimeK, Stage, admit_response, check_witness_only, valid_response

Measure = Literal["mu1", "mu2"]
EVAL_BUDGET = 400_000
PERM_BUDGET = 100_000


# ---------------------------------------------------------------------------
# Pools
# ---------------------------------------------------------------------------


def _domain(s: RegimeK, sort_form: int, n_total: int) -> list[int]:
    o = RegimeOracle(s.base)
    return [d for d in range(min(n_total, s.base.n_data())) if o.derivable((sort_form, (d,)))]


def _witness_pool(s: RegimeK, stage: Stage, n_total: int, pruned: bool) -> list[Item]:
    out: list[Item] = []
    for f, sorts in s.witness_forms:
        arity = s.base.forms[f]
        if arity > stage.witness_arity:
            continue
        if pruned and sorts:
            doms = [_domain(s, sf, n_total) for sf in sorts]
            for args in product(*doms):
                out.append(NewInst(f, tuple(args)))
        else:
            for args in product(range(n_total), repeat=arity):
                out.append(NewInst(f, tuple(args)))
    return out


def _mentions(it: Item, d: int) -> bool:
    return isinstance(it, NewInst) and d in it.args


def pruning_sound(s: RegimeK) -> bool:
    """Side condition of sort relevance: witness forms occur only where
    dropping an off-sort instance cannot break a requirement."""
    sorted_wf = {f for f, so in s.witness_forms if so}
    if not sorted_wf:
        return True
    for q in s.reqs:
        if isinstance(q, Separate):
            return False
        if isinstance(q, Holds) and q.atom[0] in sorted_wf:
            return False
        if isinstance(q, (Closure, Total)):
            for f, args in q.head:
                if f in sorted_wf:
                    sorts = s.sorts_of(f)
                    for k, t in enumerate(args):
                        if isinstance(t, int):
                            continue
                        guard = (sorts[k], (t,))
                        if guard not in q.head and guard not in q.body:
                            return False
    return True


def iter_class(s: RegimeK, stage: Stage, bound: ResourceBound, pruned: bool) -> Iterator[Delta]:
    """The declared class, by item count, each delta canonical and once."""
    n = s.base.n_data()
    use_prune = pruned and pruning_sound(s)
    datum_opts = [False, True] if "datum" in stage.item_kinds else [False]
    form_opts: list[int | None] = [None]
    if "witness_form" in stage.item_kinds and s.new_forms_allowed:
        form_opts += list(range(1, stage.witness_arity + 1))
    nf = len(s.base.forms)
    for size in range(0, bound.max_items + 1):
        for a in form_opts:
            for dat in datum_opts:
                fixed: list[Item] = []
                if a is not None:
                    fixed.append(NewForm(a))
                if dat:
                    fixed.append(NewDatum())
                room = size - len(fixed)
                if room < 0:
                    continue
                n_total = n + (1 if dat else 0)
                pool = _witness_pool(s, stage, n_total, use_prune)
                if a is not None:
                    pool += [NewInst(nf, tuple(args)) for args in product(range(n_total), repeat=a)]
                for chosen in combinations(pool, room):
                    delta = canonical_delta(tuple(fixed) + chosen)
                    if pruned:
                        if a is not None and not any(isinstance(it, NewInst) and it.form == nf for it in chosen):
                            continue
                        if dat and not any(_mentions(it, n) for it in chosen):
                            continue
                    yield delta


def _csum(pool: int, k: int) -> int:
    return sum(comb(pool, j) for j in range(0, k + 1)) if k >= 0 else 0


def class_size_formula(s: RegimeK, stage: Stage, bound: ResourceBound, pruned: bool) -> int:
    """Independent count of ``iter_class`` by binomial sums."""
    n = s.base.n_data()
    b = bound.max_items
    use_prune = pruned and pruning_sound(s)

    def wpool(n_total: int) -> int:
        tot = 0
        for f, sorts in s.witness_forms:
            arity = s.base.forms[f]
            if arity > stage.witness_arity:
                continue
            if use_prune and sorts:
                p = 1
                for sf in sorts:
                    p *= len(_domain(s, sf, n_total))
                tot += p
            else:
                tot += n_total**arity
        return tot

    total = _csum(wpool(n), b)
    datum = "datum" in stage.item_kinds
    forms = "witness_form" in stage.item_kinds and s.new_forms_allowed
    p_old, p_new = wpool(n), wpool(n + 1)
    if datum:
        total += (_csum(p_new, b - 1) - _csum(p_old, b - 1)) if pruned else _csum(p_new, b - 1)
    if forms:
        for a in range(1, stage.witness_arity + 1):
            na, nb = n**a, (n + 1) ** a
            if pruned:
                total += _csum(na + p_old, b - 1) - _csum(p_old, b - 1)
            else:
                total += _csum(na + p_old, b - 1)
            if datum:
                full = nb + p_new
                if pruned:
                    no_form_inst = p_new
                    no_mention = na + p_old
                    neither = p_old
                    total += (
                        _csum(full, b - 2) - _csum(no_form_inst, b - 2)
                        - _csum(no_mention, b - 2) + _csum(neither, b - 2)
                    )
                else:
                    total += _csum(full, b - 2)
    return total


# ---------------------------------------------------------------------------
# Isomorphism, extended to typed requirements and claim/witness split
# ---------------------------------------------------------------------------


def canonical_k(s: RegimeK, perm_budget: int = PERM_BUDGET) -> tuple[object, ...]:
    """Minimum, over bijection pairs preserving the refinement's colors,
    of the serialization extended by mapped requirements and forms."""
    r = s.base
    dcol, fcol = _refine(r)
    total = _perm_count(dcol) * _perm_count(fcol)
    if total > perm_budget:
        raise IsoBudgetError(f"{total} bijections exceed {perm_budget}")
    best: tuple[object, ...] | None = None
    for pi in _class_perms(dcol):
        for phi in _class_perms(fcol):
            key = (
                serialize(r, pi, phi),
                tuple(sorted(repr(req_json(rename_req(q, pi, phi))) for q in s.reqs)),
                tuple(sorted(phi[f] for f in s.claim_forms)),
                tuple(sorted((phi[f], tuple(phi[x] for x in so)) for f, so in s.witness_forms)),
            )
            if best is None or repr(key) < repr(best):
                best = key
    assert best is not None
    return best


# ---------------------------------------------------------------------------
# Exhaustion and witness search
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Exhaustion:
    status: Literal["CLOSED", "CLOSED_BY_THEOREM", "FOUND", "BUDGET_UNKNOWN"]
    stage: str
    bound: int
    pruned: bool
    class_sha256: str
    class_size: int
    class_size_expected: int
    theorem: str | None
    cost_found: int | None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.status == other.status
            and self.stage == other.stage
            and self.bound == other.bound
            and self.pruned == other.pruned
            and self.class_sha256 == other.class_sha256
            and self.class_size == other.class_size
            and self.class_size_expected == other.class_size_expected
            and self.theorem == other.theorem
            and self.cost_found == other.cost_found
        )

    def to_json(self) -> dict[str, object]:
        return {
            "bound_max_items": self.bound,
            "class_sha256": self.class_sha256,
            "class_size": self.class_size,
            "class_size_expected": self.class_size_expected,
            "cost_found": self.cost_found,
            "pruned": self.pruned,
            "stage": self.stage,
            "status": self.status,
            "theorem": self.theorem,
        }


@dataclass(frozen=True)
class WitnessResult:
    grade: Literal["none", "unique_delta", "unique_class", "tie", "budget_unknown"]
    measure: Measure
    cost: tuple[int, int] | None
    minima: tuple[Delta, ...]
    classes: tuple[tuple[Delta, int], ...]
    exhaustion: Exhaustion

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.grade == other.grade
            and self.measure == other.measure
            and self.cost == other.cost
            and self.minima == other.minima
            and self.classes == other.classes
            and self.exhaustion == other.exhaustion
        )

    def to_json(self) -> dict[str, object]:
        return {
            "classes": [{"representative": delta_json(rep), "size": k} for rep, k in self.classes],
            "cost": list(self.cost) if self.cost is not None else None,
            "exhaustion": self.exhaustion.to_json(),
            "grade": self.grade,
            "literal_minima": len(self.minima),
            "measure": self.measure,
        }


def delta_json(delta: Delta) -> list[list[object]]:
    out: list[list[object]] = []
    for it in delta:
        if isinstance(it, NewDatum):
            out.append(["datum"])
        elif isinstance(it, NewForm):
            out.append(["form", it.arity])
        elif isinstance(it, NewInst):
            out.append(["inst", it.form, list(it.args)])
        else:
            out.append(["rule", it.form])
    return out


def _digest_update(h: "hashlib._Hash", delta: Delta) -> None:
    h.update(repr(tuple(item_key(it) for it in delta)).encode("ascii") + b"\n")


def check_count(seen: int, expected: int) -> None:
    """A class whose enumeration count differs from its independent count is never closed."""
    if seen != expected:
        raise Refusal("RR-EXHAUSTION", f"enumerated {seen} deltas, the formula counts {expected}")


def denied_terminal(s: RegimeK) -> tuple[str, ...]:
    """Requirement ids that read only claim forms and fail on the claim."""
    o = RegimeOracle(s.base)
    return tuple(q.rid for q in s.reqs if s.claim_only(q) and refutation(o, q))


def decide_k(
    s: RegimeK, stage: Stage, bound: ResourceBound, measure: Measure = "mu1", pruned: bool = True
) -> WitnessResult:
    failed = denied_terminal(s)
    if failed:
        ex = Exhaustion(
            "CLOSED_BY_THEOREM", stage.name, bound.max_items, pruned, "", 0, 0,
            "denied_terminal", None,
        )
        return WitnessResult("none", measure, None, (), (), ex)
    declared = class_size_formula(s, stage, bound, pruned)
    if declared > EVAL_BUDGET:
        ex = Exhaustion(
            "BUDGET_UNKNOWN", stage.name, bound.max_items, pruned, "", 0, declared,
            "class_over_budget", None,
        )
        return WitnessResult("budget_unknown", measure, None, (), (), ex)
    h = hashlib.sha256()
    seen = 0
    by_size: dict[int, list[Delta]] = {}
    for delta in iter_class(s, stage, bound, pruned):
        seen += 1
        check_witness_only(s, stage, delta)
        if seen > declared:
            raise Refusal("RR-EXHAUSTION", f"the enumeration outran its declared count of {declared}")
        _digest_update(h, delta)
        if by_size and len(delta) > min(by_size):
            continue
        if valid_response(s, stage, delta):
            by_size.setdefault(len(delta), []).append(delta)
    expected = declared
    digest = "sha256:" + h.hexdigest()
    check_count(seen, expected)
    if not by_size:
        ex = Exhaustion("CLOSED", stage.name, bound.max_items, pruned, digest, seen, expected, None, None)
        return WitnessResult("none", measure, None, (), (), ex)
    k = min(by_size)
    valid = by_size[k]
    if measure == "mu2":
        best = min(mu2(d) for d in valid)
        chosen = tuple(sorted((d for d in valid if mu2(d) == best), key=lambda d: [item_key(i) for i in d]))
        cost = best
    else:
        chosen = tuple(sorted(valid, key=lambda d: [item_key(i) for i in d]))
        cost = (k, -1)
    ex = Exhaustion("FOUND", stage.name, bound.max_items, pruned, digest, seen, expected, None, k)
    if len(chosen) == 1:
        return WitnessResult("unique_delta", measure, cost, chosen, ((chosen[0], 1),), ex)
    groups: dict[str, list[Delta]] = {}
    for d in chosen:
        key = repr(canonical_k(admit_response(s, stage, d)))
        groups.setdefault(key, []).append(d)
    classes = tuple((members[0], len(members)) for _, members in sorted(groups.items()))
    grade: Literal["unique_class", "tie"] = "unique_class" if len(classes) == 1 else "tie"
    return WitnessResult(grade, measure, cost, chosen, classes, ex)


__all__ = [
    "EVAL_BUDGET",
    "Exhaustion",
    "Measure",
    "PERM_BUDGET",
    "WitnessResult",
    "canonical_k",
    "check_count",
    "class_size_formula",
    "decide_k",
    "delta_json",
    "denied_terminal",
    "iter_class",
    "pruning_sound",
]
