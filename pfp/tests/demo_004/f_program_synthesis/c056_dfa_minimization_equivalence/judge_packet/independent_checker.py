"""Independent Checker for Challenge C056: DFA Minimization and Equivalence.

Written without the reference solver or the exact checker. Its pipeline is:
its own regex parser -> Thompson NFA -> subset-construction DFA, and exact
language equivalence by the Hopcroft-Karp union-find algorithm (1971).

- MINIMIZE: the submitted DFA is complete, every state has an access word,
  every pair of states has a separating suffix (Myhill-Nerode: minimality),
  the separations agree with the regex's language, and L(DFA) == L(regex).
- EQUIV: equality or difference of L(r1) and L(r2) is decided exactly (no
  sampling); a DIFFERENT word is checked by NFA simulation; an EQUAL answer
  must carry minimal dfa1, dfa2 recognising L(r1), L(r2) and an isomorphism.

Correction, 2026-09-29: the previous version imported the reference parser,
never compared L(DFA) with L(regex) (a 1-state accept-everything DFA for '%'
passed), and checked EQUAL only on words of length at most 4.
"""

from __future__ import annotations

from typing import Any

OPERATORS = "%#()*|"


class NotARegex(Exception):
    pass


# --- parser: precedence climbing over a token list -----------------------------


def _tokens(text: str, sigma: frozenset) -> list[str]:
    body = text.strip()
    out = []
    for ch in body:
        if ch in " \t\n":
            continue
        if ch in sigma or ch in OPERATORS:
            out.append(ch)
        else:
            raise NotARegex(f"illegal character {ch!r}")
    return out


def parse_expression(text: Any, alphabet: Any):
    """Return an AST of nested lists: ['E'], ['0'], ['L', c], ['.', a, b], ['+', a, b], ['*', a]."""
    if not isinstance(alphabet, list) or len(alphabet) == 0:
        raise NotARegex("alphabet must be a non-empty list")
    if any(type(a) is not str or len(a) != 1 or a in OPERATORS for a in alphabet):
        raise NotARegex("alphabet symbols must be single non-operator characters")
    if len(frozenset(alphabet)) != len(alphabet):
        raise NotARegex("duplicate alphabet symbols")
    if type(text) is not str:
        raise NotARegex("expression must be a string")
    sigma = frozenset(alphabet)
    toks = _tokens(text, sigma)
    if not toks:
        return ["E"]
    pos = [0]

    def at():
        return toks[pos[0]] if pos[0] < len(toks) else ""

    def starts_operand(t):
        return t in sigma or t in ("%", "#", "(")

    def alternatives():
        left = sequence()
        while at() == "|":
            pos[0] += 1
            left = ["+", left, sequence()]
        return left

    def sequence():
        if not starts_operand(at()):
            raise NotARegex(f"operand expected at position {pos[0]}")
        left = starred()
        while starts_operand(at()):
            left = [".", left, starred()]
        return left

    def starred():
        t = at()
        pos[0] += 1
        if t in sigma:
            node = ["L", t]
        elif t == "%":
            node = ["E"]
        elif t == "#":
            node = ["0"]
        elif t == "(":
            node = alternatives()
            if at() != ")":
                raise NotARegex("missing ')'")
            pos[0] += 1
        else:
            raise NotARegex(f"unexpected {t!r}")
        while at() == "*":
            pos[0] += 1
            node = ["*", node]
        return node

    tree = alternatives()
    if pos[0] != len(toks):
        raise NotARegex(f"trailing input at position {pos[0]}")
    return tree


# --- Thompson NFA and subset construction --------------------------------------


class _NFA:
    def __init__(self, tree) -> None:
        self.eps: dict[int, list[int]] = {}
        self.sym: dict[tuple[int, str], list[int]] = {}
        self.count = 0
        self.start, self.final = self._build(tree)

    def _new(self) -> int:
        self.count += 1
        return self.count - 1

    def _e(self, u: int, v: int) -> None:
        self.eps.setdefault(u, []).append(v)

    def _build(self, t):
        s, f = self._new(), self._new()
        tag = t[0]
        if tag == "E":
            self._e(s, f)
        elif tag == "L":
            self.sym.setdefault((s, t[1]), []).append(f)
        elif tag == ".":
            s1, f1 = self._build(t[1])
            s2, f2 = self._build(t[2])
            self._e(s, s1)
            self._e(f1, s2)
            self._e(f2, f)
        elif tag == "+":
            for child in (t[1], t[2]):
                cs, cf = self._build(child)
                self._e(s, cs)
                self._e(cf, f)
        elif tag == "*":
            cs, cf = self._build(t[1])
            self._e(s, cs)
            self._e(cf, cs)
            self._e(cf, f)
            self._e(s, f)
        return s, f

    def closure(self, states) -> frozenset:
        seen = set(states)
        stack = list(states)
        while stack:
            u = stack.pop()
            for v in self.eps.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        return frozenset(seen)

    def step(self, states: frozenset, ch: str) -> frozenset:
        nxt = set()
        for u in states:
            nxt.update(self.sym.get((u, ch), ()))
        return self.closure(nxt)

    def accepts(self, word: str) -> bool:
        cur = self.closure([self.start])
        for ch in word:
            cur = self.step(cur, ch)
        return self.final in cur


def subset_dfa(nfa: _NFA, alphabet: list[str]):
    """Return (accepting flags, transition table) of the subset DFA; state 0 is the start."""
    start = nfa.closure([nfa.start])
    index = {start: 0}
    order = [start]
    table: list[list[int]] = []
    i = 0
    while i < len(order):
        row = []
        for ch in alphabet:
            target = nfa.step(order[i], ch)
            if target not in index:
                index[target] = len(order)
                order.append(target)
            row.append(index[target])
        table.append(row)
        i += 1
    return [nfa.final in s for s in order], table


def hopcroft_karp_equal(acc_a, delta_a, acc_b, delta_b, n_symbols: int) -> bool:
    """Hopcroft-Karp: are the start states of two complete DFAs language-equivalent?"""
    offset = len(acc_a)
    parent = list(range(offset + len(acc_b)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def accepting(x: int) -> bool:
        return acc_a[x] if x < offset else acc_b[x - offset]

    def succ(x: int, k: int) -> int:
        return delta_a[x][k] if x < offset else delta_b[x - offset][k] + offset

    parent[find(0)] = find(offset)
    stack = [(0, offset)]
    while stack:
        p, q = stack.pop()
        if accepting(p) != accepting(q):
            return False
        for k in range(n_symbols):
            rp, rq = find(succ(p, k)), find(succ(q, k))
            if rp != rq:
                parent[rp] = rq
                stack.append((succ(p, k), succ(q, k)))
    return True


# --- certificate checks --------------------------------------------------------


def _shape_problem(n: Any, acc: Any, delta: Any, width: int) -> str:
    if type(n) is not int or n < 1:
        return "states must be a positive int"
    if not isinstance(acc, list) or any(type(s) is not int or not 0 <= s < n for s in acc):
        return "accept must list int states in range"
    if len(set(acc)) != len(acc):
        return "accept has duplicates"
    if not isinstance(delta, list) or len(delta) != n:
        return "delta row count mismatch"
    for row in delta:
        if not isinstance(row, list) or len(row) != width:
            return "delta row width mismatch"
        if any(type(t) is not int or not 0 <= t < n for t in row):
            return "delta target not an int state in range"
    return ""


def _is_minimal(n: int, acc: set, delta, width: int) -> bool:
    """Reachability plus table-filling distinguishability."""
    reach = {0}
    todo = [0]
    while todo:
        s = todo.pop()
        for t in delta[s]:
            if t not in reach:
                reach.add(t)
                todo.append(t)
    if len(reach) != n:
        return False
    marked = {(p, q) for p in range(n) for q in range(p + 1, n) if (p in acc) != (q in acc)}
    changed = True
    while changed:
        changed = False
        for p in range(n):
            for q in range(p + 1, n):
                if (p, q) in marked:
                    continue
                for k in range(width):
                    a, b = sorted((delta[p][k], delta[q][k]))
                    if a != b and (a, b) in marked:
                        marked.add((p, q))
                        changed = True
                        break
    return len(marked) == n * (n - 1) // 2


def _same_language_as(tree, alphabet, n, acc: set, delta) -> bool:
    flags, table = subset_dfa(_NFA(tree), alphabet)
    return hopcroft_karp_equal([s in acc for s in range(n)], delta, flags, table, len(alphabet))


def independent_check(case: dict[str, Any], result: Any) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a JSON object"
    if result.get("case_id") != case.get("case_id"):
        return False, "Case ID mismatch"
    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    alphabet = case.get("alphabet")
    task = case.get("task")
    trees = None
    try:
        if task == "MINIMIZE":
            trees = [parse_expression(case.get("regex"), alphabet)]
        elif task == "EQUIV":
            trees = [
                parse_expression(case.get("r1"), alphabet),
                parse_expression(case.get("r2"), alphabet),
            ]
    except NotARegex:
        trees = None

    if status == "OUT_OF_SCOPE":
        if trees is not None:
            return False, "False OUT_OF_SCOPE on valid case"
        return True, "Valid OUT_OF_SCOPE"
    if trees is None:
        return False, f"Expected OUT_OF_SCOPE, got {status}"
    if status == "UNKNOWN":
        return False, "UNKNOWN on a decidable in-scope case"

    width = len(alphabet)
    if task == "MINIMIZE":
        n, acc, delta = result.get("states"), result.get("accept"), result.get("delta")
        problem = _shape_problem(n, acc, delta, width)
        if problem:
            return False, problem
        access, separators = result.get("access"), result.get("separators")
        if not isinstance(access, list) or len(access) != n:
            return False, "Invalid access list length"
        if not isinstance(separators, dict):
            return False, "Invalid separators dictionary"
        pos = {a: i for i, a in enumerate(alphabet)}

        def run(state: int, word: str):
            for ch in word:
                if ch not in pos:
                    return None
                state = delta[state][pos[ch]]
            return state

        for s, w in enumerate(access):
            if not isinstance(w, str) or run(0, w) != s:
                return False, f"access[{s}] does not lead to state {s}"
        nfa = _NFA(trees[0])
        for p in range(n):
            for q in range(p + 1, n):
                sep = separators.get(f"{p},{q}")
                if not isinstance(sep, str):
                    return False, f"Missing or non-string separator {p},{q}"
                end_p, end_q = run(p, sep), run(q, sep)
                if end_p is None or end_q is None:
                    return False, f"Separator {p},{q} uses a symbol outside the alphabet"
                if (end_p in acc) == (end_q in acc):
                    return False, f"Separator {p},{q} does not separate the states"
                if nfa.accepts(access[p] + sep) == nfa.accepts(access[q] + sep):
                    return (
                        False,
                        f"Myhill-Nerode separation fails in the regex language for {p},{q}",
                    )
        if not _same_language_as(trees[0], alphabet, n, set(acc), delta):
            return False, "L(DFA) != L(regex) (Hopcroft-Karp)"
        return True, "Independent check passed: minimal DFA with L(DFA) == L(regex)"

    kind = result.get("kind")
    flags1, table1 = subset_dfa(_NFA(trees[0]), alphabet)
    flags2, table2 = subset_dfa(_NFA(trees[1]), alphabet)
    equal = hopcroft_karp_equal(flags1, table1, flags2, table2, width)
    if kind == "DIFFERENT":
        if equal:
            return False, "DIFFERENT claimed but L(r1) == L(r2)"
        word = result.get("word")
        if not isinstance(word, str) or any(ch not in alphabet for ch in word):
            return False, "word must be a string over the alphabet"
        if _NFA(trees[0]).accepts(word) == _NFA(trees[1]).accepts(word):
            return False, f"Word '{word}' does not distinguish r1 and r2"
        return True, f"Independent check passed: word '{word}' distinguishes r1 and r2"
    if kind != "EQUAL":
        return False, f"Invalid EQUIV kind: {kind}"
    if not equal:
        return False, "EQUAL claimed but L(r1) != L(r2)"
    shapes = []
    for name, tree in (("dfa1", trees[0]), ("dfa2", trees[1])):
        dfa = result.get(name)
        if not isinstance(dfa, dict):
            return False, f"Missing {name}"
        n, acc, delta = dfa.get("states"), dfa.get("accept"), dfa.get("delta")
        problem = _shape_problem(n, acc, delta, width)
        if problem:
            return False, f"{name}: {problem}"
        if not _is_minimal(n, set(acc), delta, width):
            return False, f"{name} is not minimal"
        if not _same_language_as(tree, alphabet, n, set(acc), delta):
            return False, f"{name} does not recognise its regex"
        shapes.append((n, set(acc), delta))
    (n1, acc1, d1), (n2, acc2, d2) = shapes
    bij = result.get("bijection")
    if n1 != n2 or not isinstance(bij, dict) or len(bij) != n1:
        return False, "Bijection size mismatch"
    phi = {}
    for key, value in bij.items():
        canonical = (
            isinstance(key, str) and key.isascii() and key.isdigit() and str(int(key)) == key
        )
        if not canonical or type(value) is not int or not 0 <= value < n2:
            return False, "Bijection entries must map decimal state keys to int states"
        phi[int(key)] = value
    if sorted(phi) != list(range(n1)) or sorted(phi.values()) != list(range(n2)) or phi.get(0) != 0:
        return False, "Bijection must be a bijection fixing state 0"
    for s1, s2 in phi.items():
        if (s1 in acc1) != (s2 in acc2):
            return False, f"Bijection violates acceptance: state {s1} -> {s2}"
        for k in range(width):
            if phi[d1[s1][k]] != d2[s2][k]:
                return False, f"Bijection violates transition homomorphism on letter {alphabet[k]}"
    return True, "Independent check passed for EQUAL (Hopcroft-Karp)"
