"""Exact Checker for Challenge C056: DFA Minimization and Equivalence.

This checker does not import the reference solver or the independent checker.
It parses regular expressions itself and decides languages with Brzozowski
derivatives, normalised up to associativity, commutativity and idempotence of
union, so the set of derivatives of a regex is finite (Brzozowski 1964).

Validates:
- MINIMIZE: complete DFA shape; access words (every state reachable);
  separators (every pair of states distinguished), which together certify
  minimality by the Myhill-Nerode theorem; and L(DFA) == L(regex), decided
  exactly by exploring pairs (DFA state, derivative) of the product.
- EQUIV DIFFERENT: the word lies in the symmetric difference of L(r1), L(r2).
- EQUIV EQUAL: L(r1) == L(r2) exactly; dfa1 and dfa2 are complete minimal DFAs
  with L(dfa1) == L(r1) and L(dfa2) == L(r2); the bijection is an isomorphism.

Correction, 2026-09-29: the previous version imported the reference solver's
parser and minimal-DFA compiler, and let a missing dfa1/dfa2 default to the
reference's own automata.
"""

from __future__ import annotations

from collections import deque
from typing import Any

SYNTAX = ("%", "#", "(", ")", "*", "|")
SKIPPED_WHITESPACE = (" ", "\t", "\n")
PRODUCT_LIMIT = 200_000

EMPTY = ("empty",)
EPS = ("eps",)


class RegexSyntaxError(ValueError):
    pass


# --- regular expressions as normalised tuples -------------------------------


def _alt(*parts):
    items = set()
    for part in parts:
        if part[0] == "alt":
            items |= part[1]
        elif part != EMPTY:
            items.add(part)
    if not items:
        return EMPTY
    if len(items) == 1:
        return next(iter(items))
    return ("alt", frozenset(items))


def _cat(left, right):
    if left == EMPTY or right == EMPTY:
        return EMPTY
    if left == EPS:
        return right
    if right == EPS:
        return left
    if left[0] == "cat":
        return ("cat", left[1], _cat(left[2], right))
    return ("cat", left, right)


def _star(inner):
    if inner in (EMPTY, EPS):
        return EPS
    if inner[0] == "star":
        return inner
    return ("star", inner)


def nullable(r) -> bool:
    kind = r[0]
    if kind in ("eps", "star"):
        return True
    if kind in ("empty", "lit"):
        return False
    if kind == "cat":
        return nullable(r[1]) and nullable(r[2])
    return any(nullable(x) for x in r[1])


def derivative(r, ch: str):
    kind = r[0]
    if kind in ("eps", "empty"):
        return EMPTY
    if kind == "lit":
        return EPS if r[1] == ch else EMPTY
    if kind == "cat":
        head = _cat(derivative(r[1], ch), r[2])
        return _alt(head, derivative(r[2], ch)) if nullable(r[1]) else head
    if kind == "star":
        return _cat(derivative(r[1], ch), r)
    return _alt(*(derivative(x, ch) for x in r[1]))


def matches(r, word: str) -> bool:
    for ch in word:
        r = derivative(r, ch)
    return nullable(r)


class _Parser:
    """union := concat ('|' concat)* ; concat := postfix+ ; postfix := atom '*'* ;
    atom := letter | '%' | '#' | '(' union ')'."""

    def __init__(self, tokens: list[str], letters: set[str]) -> None:
        self.tokens = tokens
        self.letters = letters
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self):
        node = self.union()
        if self.peek() is not None:
            raise RegexSyntaxError(f"unexpected '{self.peek()}' at token {self.pos}")
        return node

    def union(self):
        node = self.concat()
        while self.peek() == "|":
            self.pos += 1
            node = _alt(node, self.concat())
        return node

    def concat(self):
        parts = []
        while self.peek() is not None and (
            self.peek() in self.letters or self.peek() in ("%", "#", "(")
        ):
            parts.append(self.postfix())
        if not parts:
            raise RegexSyntaxError(f"expected an operand at token {self.pos}")
        node = parts[-1]
        for part in reversed(parts[:-1]):
            node = _cat(part, node)
        return node

    def postfix(self):
        node = self.atom()
        while self.peek() == "*":
            self.pos += 1
            node = _star(node)
        return node

    def atom(self):
        tok = self.peek()
        self.pos += 1
        if tok in self.letters:
            return ("lit", tok)
        if tok == "%":
            return EPS
        if tok == "#":
            return EMPTY
        if tok == "(":
            node = self.union()
            if self.peek() != ")":
                raise RegexSyntaxError("unclosed '('")
            self.pos += 1
            return node
        raise RegexSyntaxError(f"unexpected token {tok!r}")


def parse(text: Any, alphabet: Any):
    if not isinstance(text, str):
        raise RegexSyntaxError("regex must be a string")
    letters = _alphabet_letters(alphabet)
    stripped = text.strip()
    if not stripped:
        return EPS
    tokens = []
    for ch in stripped:
        if ch in SKIPPED_WHITESPACE:
            continue
        if ch not in letters and ch not in SYNTAX:
            raise RegexSyntaxError(f"character {ch!r} is neither a letter nor syntax")
        tokens.append(ch)
    return _Parser(tokens, letters).parse()


def _alphabet_letters(alphabet: Any) -> set[str]:
    if not isinstance(alphabet, list) or not alphabet:
        raise RegexSyntaxError("alphabet must be a non-empty list")
    for a in alphabet:
        if not isinstance(a, str) or len(a) != 1 or a in SYNTAX:
            raise RegexSyntaxError(f"invalid alphabet symbol {a!r}")
    if len(set(alphabet)) != len(alphabet):
        raise RegexSyntaxError("alphabet contains duplicate letters")
    return set(alphabet)


# --- DFA shape and language checks ------------------------------------------


def simulate_dfa(delta: list[list[int]], alphabet: list[str], start_state: int, word: str) -> int:
    sym_to_idx = {a: i for i, a in enumerate(alphabet)}
    curr = start_state
    for ch in word:
        if ch not in sym_to_idx:
            raise ValueError(f"Character '{ch}' not in alphabet")
        curr = delta[curr][sym_to_idx[ch]]
    return curr


def _dfa_shape_error(states: Any, accept: Any, delta: Any, alphabet: list[str]) -> str | None:
    if type(states) is not int or states <= 0:
        return f"Invalid number of states: {states!r}"
    if not isinstance(accept, list):
        return "accept must be a list of state integers"
    for s in accept:
        if type(s) is not int or s < 0 or s >= states:
            return f"Invalid accept state index: {s!r}"
    if len(set(accept)) != len(accept):
        return "accept contains duplicate state indices"
    if not isinstance(delta, list) or len(delta) != states:
        return f"delta must have {states} rows"
    for r_idx, row in enumerate(delta):
        if not isinstance(row, list) or len(row) != len(alphabet):
            return f"delta row {r_idx} must have length {len(alphabet)}"
        for c_idx, dst in enumerate(row):
            if type(dst) is not int or dst < 0 or dst >= states:
                return f"delta[{r_idx}][{c_idx}] must be an int in 0..{states - 1}, got {dst!r}"
    return None


def language_mismatch(delta, accept_set, alphabet, regex) -> str | None:
    """Return a word on which the DFA and the regex disagree, or None if L(DFA) == L(regex)."""
    seen = {(0, regex)}
    queue = deque([(0, regex, "")])
    while queue:
        state, r, word = queue.popleft()
        if (state in accept_set) != nullable(r):
            return word
        for idx, ch in enumerate(alphabet):
            pair = (delta[state][idx], derivative(r, ch))
            if pair not in seen:
                if len(seen) >= PRODUCT_LIMIT:
                    raise RuntimeError("C056 exact checker product limit exceeded")
                seen.add(pair)
                queue.append((pair[0], pair[1], word + ch))
    return None


def regex_difference(r1, r2, alphabet) -> str | None:
    """Shortest word in the symmetric difference of L(r1) and L(r2), or None if equal."""
    seen = {(r1, r2)}
    queue = deque([(r1, r2, "")])
    while queue:
        a, b, word = queue.popleft()
        if nullable(a) != nullable(b):
            return word
        for ch in alphabet:
            pair = (derivative(a, ch), derivative(b, ch))
            if pair not in seen:
                if len(seen) >= PRODUCT_LIMIT:
                    raise RuntimeError("C056 exact checker product limit exceeded")
                seen.add(pair)
                queue.append((pair[0], pair[1], word + ch))
    return None


def moore_classes(states: int, accept_set: set[int], delta, alphabet) -> int:
    """Number of Myhill-Nerode classes among the states (Moore partition refinement)."""
    block = [1 if s in accept_set else 0 for s in range(states)]
    while True:
        signatures = {}
        refined = []
        for s in range(states):
            key = (block[s],) + tuple(block[delta[s][i]] for i in range(len(alphabet)))
            refined.append(signatures.setdefault(key, len(signatures)))
        if len(signatures) == len(set(block)):
            return len(signatures)
        block = refined


def reachable_count(states: int, delta, alphabet) -> int:
    seen = {0}
    queue = deque([0])
    while queue:
        s = queue.popleft()
        for i in range(len(alphabet)):
            t = delta[s][i]
            if t not in seen:
                seen.add(t)
                queue.append(t)
    return len(seen)


# --- entry point --------------------------------------------------------------


def _validate_case(case: Any):
    """Return (asts, error). asts is a tuple of parsed regexes for the task."""
    if not isinstance(case, dict):
        return None, "case is not an object"
    alphabet = case.get("alphabet")
    task = case.get("task")
    try:
        _alphabet_letters(alphabet)
        if task == "MINIMIZE":
            return (parse(case.get("regex"), alphabet),), None
        if task == "EQUIV":
            return (parse(case.get("r1"), alphabet), parse(case.get("r2"), alphabet)), None
    except RegexSyntaxError as exc:
        return None, str(exc)
    return None, f"Unknown task: {task!r}"


def check_exact(case: dict[str, Any], result: Any) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, f"Result must be a JSON object, got {type(result).__name__}"
    if result.get("case_id") != case.get("case_id"):
        return (
            False,
            f"Case ID mismatch: expected {case.get('case_id')}, got {result.get('case_id')}",
        )

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    asts, input_err = _validate_case(case)

    if status == "OUT_OF_SCOPE":
        if asts is not None:
            return False, "Solver returned OUT_OF_SCOPE on a valid input case"
        witness = result.get("witness")
        if not isinstance(witness, dict) or "reason" not in witness:
            return False, "Missing witness.reason in OUT_OF_SCOPE"
        return True, "Valid OUT_OF_SCOPE"

    if asts is None:
        return False, f"Expected OUT_OF_SCOPE due to ({input_err}), but solver returned {status}"
    if status == "UNKNOWN":
        return False, "UNKNOWN rejected: every in-scope C056 case is decidable"

    alphabet = case["alphabet"]
    if case["task"] == "MINIMIZE":
        return _check_minimize(result, alphabet, asts[0])
    return _check_equiv(result, alphabet, asts[0], asts[1])


def _check_minimize(result, alphabet, regex) -> tuple[bool, str]:
    states = result.get("states")
    accept = result.get("accept")
    delta = result.get("delta")
    err = _dfa_shape_error(states, accept, delta, alphabet)
    if err:
        return False, err
    accept_set = set(accept)

    access = result.get("access")
    if not isinstance(access, list) or len(access) != states:
        return False, f"access must have length {states}"
    for s, w in enumerate(access):
        if not isinstance(w, str):
            return False, f"access[{s}] must be a string"
        try:
            reached = simulate_dfa(delta, alphabet, 0, w)
        except ValueError as e:
            return False, f"Invalid access word '{w}': {e}"
        if reached != s:
            return False, f"access[{s}] = '{w}' reaches state {reached} instead of {s}"

    separators = result.get("separators")
    if not isinstance(separators, dict):
        return False, "separators must be a dictionary"
    for p in range(states):
        for q in range(p + 1, states):
            key = f"{p},{q}"
            if key not in separators:
                return False, f"Missing separator for pair ({p}, {q})"
            z = separators[key]
            if not isinstance(z, str):
                return False, f"Separator for ({p}, {q}) must be a string"
            try:
                p_end = simulate_dfa(delta, alphabet, p, z)
                q_end = simulate_dfa(delta, alphabet, q, z)
            except ValueError as e:
                return False, f"Invalid separator string '{z}' for ({p}, {q}): {e}"
            if (p_end in accept_set) == (q_end in accept_set):
                return False, f"Separator '{z}' fails to distinguish ({p}, {q})"

    witness = language_mismatch(delta, accept_set, alphabet, regex)
    if witness is not None:
        return False, f"Language mismatch: DFA and regex disagree on the word '{witness}'"
    return True, "Valid minimal DFA: L(DFA) == L(regex), states reachable and pairwise separated"


def _check_equiv(result, alphabet, r1, r2) -> tuple[bool, str]:
    kind = result.get("kind")
    if kind not in ("EQUAL", "DIFFERENT"):
        return False, f"Invalid EQUIV kind: {kind}"
    actual_diff_word = regex_difference(r1, r2, alphabet)

    if kind == "DIFFERENT":
        if actual_diff_word is None:
            return False, "Solver claimed DIFFERENT on equivalent regexes"
        word = result.get("word")
        if not isinstance(word, str):
            return False, "word must be a string for DIFFERENT kind"
        if any(ch not in alphabet for ch in word):
            return False, "word contains a character outside the alphabet"
        if matches(r1, word) == matches(r2, word):
            return False, f"Distinguishing word '{word}' is not in the symmetric difference"
        return True, f"Valid DIFFERENT distinguishing word '{word}'"

    if actual_diff_word is not None:
        return (
            False,
            f"Solver claimed EQUAL on non-equivalent regexes (distinguishing word: '{actual_diff_word}')",
        )
    dfas = []
    for name, regex in (("dfa1", r1), ("dfa2", r2)):
        dfa = result.get(name)
        if not isinstance(dfa, dict):
            return False, f"{name} must be an object"
        err = _dfa_shape_error(dfa.get("states"), dfa.get("accept"), dfa.get("delta"), alphabet)
        if err:
            return False, f"{name}: {err}"
        n, acc, delta = dfa["states"], set(dfa["accept"]), dfa["delta"]
        if reachable_count(n, delta, alphabet) != n or moore_classes(n, acc, delta, alphabet) != n:
            return False, f"{name} is not minimal"
        witness = language_mismatch(delta, acc, alphabet, regex)
        if witness is not None:
            return False, f"{name} does not accept the language of its regex (word '{witness}')"
        dfas.append((n, acc, delta))
    (n1, acc1, d1), (n2, acc2, d2) = dfas
    if n1 != n2:
        return False, f"State count mismatch in EQUAL DFAs: {n1} vs {n2}"
    bij = result.get("bijection")
    if not isinstance(bij, dict) or len(bij) != n1:
        return False, f"bijection must be an object with {n1} entries"
    phi = {}
    for key, value in bij.items():
        if (
            not isinstance(key, str)
            or not key.isascii()
            or not key.isdigit()
            or str(int(key)) != key
        ):
            return False, f"Bijection key '{key}' is not a canonical integer"
        if type(value) is not int or value < 0 or value >= n2:
            return False, f"Bijection value {value!r} out of range"
        phi[int(key)] = value
    if set(phi) != set(range(n1)) or len(set(phi.values())) != n1:
        return False, "Bijection is not a bijection on the states"
    if phi[0] != 0:
        return False, "Bijection must map start state 0 to 0"
    for s1, s2 in phi.items():
        if (s1 in acc1) != (s2 in acc2):
            return False, f"Bijection fails to preserve acceptance at state {s1}"
        for idx in range(len(alphabet)):
            if phi[d1[s1][idx]] != d2[s2][idx]:
                return (
                    False,
                    f"Bijection fails transition homomorphism on letter {alphabet[idx]} at state {s1}",
                )
    return True, "Valid EQUAL with certified isomorphism bijection"
