# AuthorityEffect: None.
"""
Term representation, first-order unification, and term rewriting engine for C046.
Pure Python standard library with zero external dependencies.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple


class Term:
    """Abstract base class for first-order terms."""

    def is_var(self) -> bool:
        raise NotImplementedError

    def vars(self) -> Set[str]:
        raise NotImplementedError

    def apply_subst(self, subst: Dict[str, Term]) -> Term:
        raise NotImplementedError

    def subterms_with_paths(self) -> List[Tuple[Tuple[int, ...], Term]]:
        raise NotImplementedError

    def replace_at_path(self, path: Tuple[int, ...], replacement: Term) -> Term:
        raise NotImplementedError

    def to_json(self) -> Any:
        raise NotImplementedError


class Var(Term):
    """Variable term."""

    def __init__(self, name: str):
        self.name = name

    def is_var(self) -> bool:
        return True

    def vars(self) -> Set[str]:
        return {self.name}

    def apply_subst(self, subst: Dict[str, Term]) -> Term:
        if self.name in subst:
            return subst[self.name]
        return self

    def subterms_with_paths(self) -> List[Tuple[Tuple[int, ...], Term]]:
        return [((), self)]

    def replace_at_path(self, path: Tuple[int, ...], replacement: Term) -> Term:
        if not path:
            return replacement
        raise IndexError("Cannot descend into a variable")

    def to_json(self) -> str:
        return self.name

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Var) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("Var", self.name))

    def __repr__(self) -> str:
        return self.name


class Fun(Term):
    """Function symbol or constant term."""

    def __init__(self, symbol: str, args: Optional[List[Term]] = None):
        self.symbol = symbol
        self.args: List[Term] = args if args is not None else []

    def is_var(self) -> bool:
        return False

    def vars(self) -> Set[str]:
        v: Set[str] = set()
        for a in self.args:
            v |= a.vars()
        return v

    def apply_subst(self, subst: Dict[str, Term]) -> Term:
        return Fun(self.symbol, [a.apply_subst(subst) for a in self.args])

    def subterms_with_paths(self) -> List[Tuple[Tuple[int, ...], Term]]:
        res: List[Tuple[Tuple[int, ...], Term]] = [((), self)]
        for i, a in enumerate(self.args):
            for sub_path, sub_t in a.subterms_with_paths():
                res.append(((i,) + sub_path, sub_t))
        return res

    def replace_at_path(self, path: Tuple[int, ...], replacement: Term) -> Term:
        if not path:
            return replacement
        idx = path[0]
        if idx >= len(self.args):
            raise IndexError("Path index out of bounds")
        new_args = list(self.args)
        new_args[idx] = self.args[idx].replace_at_path(path[1:], replacement)
        return Fun(self.symbol, new_args)

    def to_json(self) -> str:
        if not self.args:
            return self.symbol
        return f"{self.symbol}({', '.join(a.to_json() for a in self.args)})"

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Fun)
            and self.symbol == other.symbol
            and len(self.args) == len(other.args)
            and all(a1 == a2 for a1, a2 in zip(self.args, other.args))
        )

    def __hash__(self) -> int:
        return hash(("Fun", self.symbol, tuple(self.args)))

    def __repr__(self) -> str:
        return self.to_json()


# Parser for string terms
def parse_term(s: str) -> Term:
    s = s.strip()
    if not s:
        raise ValueError("Empty term string")

    # Match function call symbol(arg1, arg2, ...)
    m = re.match(r"^([a-zA-Z0-9_]+)\s*\((.*)\)$", s)
    if m:
        sym = m.group(1)
        inner = m.group(2).strip()
        if not inner:
            return Fun(sym, [])
        # Split args respecting nested parentheses
        args = []
        depth = 0
        cur = []
        for char in inner:
            if char == "(":
                depth += 1
                cur.append(char)
            elif char == ")":
                depth -= 1
                cur.append(char)
            elif char == "," and depth == 0:
                args.append(parse_term("".join(cur)))
                cur = []
            else:
                cur.append(char)
        if cur:
            args.append(parse_term("".join(cur)))
        return Fun(sym, args)

    # Identifiers: variables start with lowercase x, y, z, u, v, w or match r\d+_
    if (
        re.match(r"^[x-z][0-9]*$", s)
        or re.match(r"^[u-w][0-9]*$", s)
        or re.match(r"^r[0-9]+_.*$", s)
    ):
        return Var(s)

    # Constants (e.g. e, 0, 1, a, b, c)
    return Fun(s, [])


# First-Order Unification (Robinson's Algorithm)
def mgu(t1: Term, t2: Term) -> Optional[Dict[str, Term]]:
    """Computes the Most General Unifier (MGU) of two terms, or None if not unifiable."""
    subst: Dict[str, Term] = {}

    def occur_check(v: str, term: Term) -> bool:
        return v in term.vars()

    def unify_step(s: Term, t: Term) -> bool:
        s = s.apply_subst(subst)
        t = t.apply_subst(subst)
        if s == t:
            return True
        if s.is_var():
            assert isinstance(s, Var)
            if occur_check(s.name, t):
                return False
            # Update all existing substitutions
            for k in list(subst.keys()):
                subst[k] = subst[k].apply_subst({s.name: t})
            subst[s.name] = t
            return True
        if t.is_var():
            assert isinstance(t, Var)
            if occur_check(t.name, s):
                return False
            for k in list(subst.keys()):
                subst[k] = subst[k].apply_subst({t.name: s})
            subst[t.name] = s
            return True
        if isinstance(s, Fun) and isinstance(t, Fun):
            if s.symbol != t.symbol or len(s.args) != len(t.args):
                return False
            for a1, a2 in zip(s.args, t.args):
                if not unify_step(a1, a2):
                    return False
            return True
        return False

    if unify_step(t1, t2):
        return subst
    return None


# Pattern Matching: does pattern p match target term t?
def match_term(pattern: Term, target: Term) -> Optional[Dict[str, Term]]:
    subst: Dict[str, Term] = {}

    def match_step(p: Term, t: Term) -> bool:
        if p.is_var():
            assert isinstance(p, Var)
            if p.name in subst:
                return subst[p.name] == t
            subst[p.name] = t
            return True
        if isinstance(p, Fun) and isinstance(t, Fun):
            if p.symbol != t.symbol or len(p.args) != len(t.args):
                return False
            for a1, a2 in zip(p.args, t.args):
                if not match_step(a1, a2):
                    return False
            return True
        return False

    if match_step(pattern, target):
        return subst
    return None


# Term Rewriting: Reduce term using a set of rules (lhs -> rhs)
def reduce_one_step(term: Term, rules: List[Tuple[Term, Term]]) -> Optional[Term]:
    """Applies the first matching rewrite rule at the leftmost-innermost position."""
    for path, sub in term.subterms_with_paths():
        for lhs, rhs in rules:
            sigma = match_term(lhs, sub)
            if sigma is not None:
                new_sub = rhs.apply_subst(sigma)
                return term.replace_at_path(path, new_sub)
    return None


def normalize(term: Term, rules: List[Tuple[Term, Term]], max_steps: int = 1000) -> Term:
    """Reduces term to normal form under the rewrite rules."""
    cur = term
    for _ in range(max_steps):
        nxt = reduce_one_step(cur, rules)
        if nxt is None or nxt == cur:
            return cur
        cur = nxt
    raise RuntimeError(f"Rewrite normalization exceeded max steps ({max_steps}) for term {term}")
