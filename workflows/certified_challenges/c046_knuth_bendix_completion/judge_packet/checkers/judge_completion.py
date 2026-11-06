# AuthorityEffect: None.
"""
Checker 1's own equational decision procedure for C046 soundness.

Written for the judge from the textbook algorithm (Huet's completion with marked rules,
lexicographic path order, Robinson/Martelli-Montanari unification, leftmost-outermost
rewriting). It imports neither the reference solver nor the other checker.

``follows_from(equations, precedence, rules)`` completes the input equations and decides, for
each submitted rule, whether its two sides are equal modulo the equations. It returns
(True, msg) when every rule follows, (False, msg) naming the first rule that does not, and
(None, msg) when its own completion does not finish within budget (then nothing is
certified).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Union

# TASK convention for cases that declare no precedence (same data the task publishes).
DEFAULT_PRECEDENCE = {
    "inv": 100,
    "mul": 50,
    "add": 40,
    "neg": 80,
    "f": 30,
    "g": 20,
    "h": 10,
    "e": 5,
    "0": 5,
    "1": 5,
}

MAX_ITERATIONS = 3000
MAX_RULES = 300
MAX_REWRITES = 20000

_TOKEN = re.compile(r"\s*([A-Za-z0-9_]+|[(),])")
_VARIABLE = re.compile(r"^(?:[u-z][0-9]*|r[0-9]+_.*)$")


@dataclass(frozen=True)
class V:
    name: str


@dataclass(frozen=True)
class F:
    head: str
    args: tuple = ()


T = Union[V, F]


class BudgetExceeded(Exception):
    pass


# ----------------------------------------------------------------------------- parsing


def read(text: str) -> T:
    tokens: list[str] = []
    pos = 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ValueError(f"unexpected character in term {text!r} at {pos}")
        tokens.append(m.group(1))
        pos = m.end()
    term, used = _read(tokens, 0)
    if used != len(tokens):
        raise ValueError(f"trailing tokens in term {text!r}")
    return term


def _read(tokens: list[str], i: int) -> tuple[T, int]:
    if i >= len(tokens) or tokens[i] in "(),":
        raise ValueError("expected a symbol")
    head = tokens[i]
    i += 1
    if i < len(tokens) and tokens[i] == "(":
        i += 1
        args: list[T] = []
        if i < len(tokens) and tokens[i] == ")":
            return F(head, ()), i + 1
        while True:
            arg, i = _read(tokens, i)
            args.append(arg)
            if i < len(tokens) and tokens[i] == ",":
                i += 1
            elif i < len(tokens) and tokens[i] == ")":
                return F(head, tuple(args)), i + 1
            else:
                raise ValueError("unbalanced parentheses")
    return (V(head) if _VARIABLE.match(head) else F(head, ())), i


# ----------------------------------------------------------------------------- basic operations


def var_names(t: T) -> frozenset:
    if isinstance(t, V):
        return frozenset({t.name})
    names: set[str] = set()
    for a in t.args:
        names |= var_names(a)
    return frozenset(names)


def subst(t: T, sigma: dict) -> T:
    if isinstance(t, V):
        return sigma.get(t.name, t)
    return F(t.head, tuple(subst(a, sigma) for a in t.args))


def occurs(name: str, t: T) -> bool:
    return name in var_names(t)


def lpo_gt(s: T, t: T, prec: dict) -> bool:
    """s >_lpo t for the precedence (higher number = bigger symbol; absent symbols rank 0)."""
    if isinstance(s, V):
        return False
    if isinstance(t, V):
        return occurs(t.name, s)
    # (LPO1) some argument of s is >= t
    for a in s.args:
        if a == t or lpo_gt(a, t, prec):
            return True
    # (LPO2) f > g and s > every argument of t
    if s.head != t.head:
        return prec.get(s.head, 0) > prec.get(t.head, 0) and all(lpo_gt(s, b, prec) for b in t.args)
    # (LPO3) same head: s > every argument of t and args lexicographically greater
    if not all(lpo_gt(s, b, prec) for b in t.args):
        return False
    for a, b in zip(s.args, t.args):
        if a != b:
            return lpo_gt(a, b, prec)
    return len(s.args) > len(t.args)


def match(pattern: T, term: T) -> Optional[dict]:
    sigma: dict = {}
    stack = [(pattern, term)]
    while stack:
        p, u = stack.pop()
        if isinstance(p, V):
            if p.name in sigma:
                if sigma[p.name] != u:
                    return None
            else:
                sigma[p.name] = u
        elif isinstance(u, F) and u.head == p.head and len(u.args) == len(p.args):
            stack.extend(zip(p.args, u.args))
        else:
            return None
    return sigma


def unify(a: T, b: T) -> Optional[dict]:
    """Most general unifier by Martelli-Montanari, with the substitution kept solved."""
    sigma: dict = {}
    work = [(a, b)]
    while work:
        s, t = work.pop()
        s, t = subst(s, sigma), subst(t, sigma)
        if s == t:
            continue
        if isinstance(t, V) and not isinstance(s, V):
            s, t = t, s
        if isinstance(s, V):
            if occurs(s.name, t):
                return None
            binding = {s.name: t}
            sigma = {k: subst(v, binding) for k, v in sigma.items()}
            sigma[s.name] = t
            continue
        if s.head != t.head or len(s.args) != len(t.args):
            return None
        work.extend(zip(s.args, t.args))
    return sigma


def rewrite_once(t: T, rules: list) -> Optional[T]:
    """One leftmost-outermost rewrite step, or None if t is irreducible."""
    for lhs, rhs in rules:
        sigma = match(lhs, t)
        if sigma is not None:
            return subst(rhs, sigma)
    if isinstance(t, F):
        for i, a in enumerate(t.args):
            r = rewrite_once(a, rules)
            if r is not None:
                return F(t.head, t.args[:i] + (r,) + t.args[i + 1 :])
    return None


def normal_form(t: T, rules: list, budget: list) -> T:
    while True:
        nxt = rewrite_once(t, rules)
        if nxt is None:
            return t
        budget[0] -= 1
        if budget[0] < 0:
            raise BudgetExceeded("rewrite budget exhausted")
        t = nxt


def _size(t: T) -> int:
    return 1 if isinstance(t, V) else 1 + sum(_size(a) for a in t.args)


def _rename(t: T, tag: str) -> T:
    return subst(t, {n: V(n + tag) for n in var_names(t)})


def _subterm_positions(t: T, path: tuple = ()) -> list:
    if isinstance(t, V):
        return []
    out = [(path, t)]
    for i, a in enumerate(t.args):
        out.extend(_subterm_positions(a, path + (i,)))
    return out


def _put(t: T, path: tuple, new: T) -> T:
    if not path:
        return new
    i = path[0]
    return F(t.head, t.args[:i] + (_put(t.args[i], path[1:], new),) + t.args[i + 1 :])


def critical_pairs_between(r1: tuple, r2: tuple, same_rule: bool) -> list:
    """Overlaps of r2's lhs into non-variable positions of r1's lhs (renamed apart)."""
    l1, rr1 = _rename(r1[0], "#1"), _rename(r1[1], "#1")
    l2, rr2 = _rename(r2[0], "#2"), _rename(r2[1], "#2")
    pairs = []
    for path, sub in _subterm_positions(l1):
        if same_rule and path == ():
            continue
        sigma = unify(sub, l2)
        if sigma is not None:
            pairs.append((subst(rr1, sigma), subst(_put(l1, path, rr2), sigma)))
    return pairs


# ----------------------------------------------------------------------------- completion


def complete(equations: list, prec: dict) -> Optional[list]:
    """Huet-style completion; a convergent rule list equivalent to the equations, or None."""
    pending = list(equations)
    rules: list = []  # entries [lhs, rhs, marked]
    budget = [MAX_REWRITES]
    try:
        for _ in range(MAX_ITERATIONS):
            active = [(r[0], r[1]) for r in rules]
            if pending:
                pending.sort(key=lambda e: _size(e[0]) + _size(e[1]))
                s, t = pending.pop(0)
                s, t = normal_form(s, active, budget), normal_form(t, active, budget)
                if s == t:
                    continue
                if lpo_gt(s, t, prec):
                    new = (s, t)
                elif lpo_gt(t, s, prec):
                    new = (t, s)
                else:
                    return None
                survivors = []
                for lhs, rhs, marked in rules:
                    if rewrite_once(lhs, [new]) is not None:
                        pending.append((lhs, rhs))  # collapse: re-derive as an equation
                    else:
                        survivors.append([lhs, normal_form(rhs, active + [new], budget), marked])
                survivors.append([new[0], new[1], False])
                rules = survivors
                if len(rules) > MAX_RULES:
                    return None
                continue
            unmarked = [r for r in rules if not r[2]]
            if not unmarked:
                final = [(r[0], r[1]) for r in rules]
                for a in final:
                    for b in final:
                        for p, q in critical_pairs_between(a, b, a is b):
                            if normal_form(p, final, budget) != normal_form(q, final, budget):
                                return None
                return final
            chosen = min(unmarked, key=lambda r: _size(r[0]) + _size(r[1]))
            chosen[2] = True
            this = (chosen[0], chosen[1])
            for other in rules:
                if not other[2]:
                    continue
                that = (other[0], other[1])
                pending.extend(critical_pairs_between(this, that, other is chosen))
                if other is not chosen:
                    pending.extend(critical_pairs_between(that, this, False))
        return None
    except (BudgetExceeded, RecursionError):
        return None


def follows_from(
    equations: list[tuple[str, str]],
    precedence: Optional[dict],
    rules: list[tuple[str, str]],
) -> tuple[Optional[bool], str]:
    # As in the task: a missing or empty precedence means the default one.
    prec = precedence if isinstance(precedence, dict) and precedence else DEFAULT_PRECEDENCE
    try:
        eqs = [(read(a), read(b)) for a, b in equations]
        submitted = [(read(a), read(b)) for a, b in rules]
    except ValueError as exc:
        return False, f"unparseable term: {exc}"
    system = complete(eqs, prec)
    if system is None:
        return None, "judge completion of the input did not finish within its budget"
    budget = [MAX_REWRITES]
    try:
        for (lhs, rhs), (a, b) in zip(submitted, rules):
            if normal_form(lhs, system, budget) != normal_form(rhs, system, budget):
                return False, f"rule {a} -> {b} is not an equational consequence of the input"
    except (BudgetExceeded, RecursionError):
        return None, "rewrite budget exhausted while deciding soundness"
    return True, f"all {len(rules)} rules follow from the input ({len(system)} judge rules)"
