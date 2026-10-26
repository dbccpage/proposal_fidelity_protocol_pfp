# AuthorityEffect: None.
"""
Independent Checker for C046.

Uses its own strict term parser, lexicographic path order (LPO), matcher and innermost
normalizer; it does not import the reference solver.

1. Answer shape: an object whose case_id matches, with status SOLVED or REFUSED and the
   fields its task requires. An empty object or an unknown status never passes.
2. Refusals pass only when the case supports them: UNKNOWN_TASK (task not recognized),
   MALFORMED_INPUT (a required field is missing), MALFORMED_TERM (an entry is not a pair of
   well-formed terms), ORDER_FAILURE (the witness names an input equation that is malformed
   or that LPO cannot orient either way), MAX_STEPS_EXCEEDED (only when the case declares a
   max_steps budget; the completion itself is not replayed here).
3. COMPLETE: every rule is LPO-decreasing and introduces no new variables; every critical
   pair of the submitted rules is joinable; every input equation joins under the submitted
   rules; and every submitted rule is an equational consequence of the input: this checker
   runs its own Knuth-Bendix completion of the input equations (same LPO precedence),
   verifies that the result is locally confluent, and requires both sides of each submitted
   rule to reach the same normal form under it. If its own completion does not finish within
   its budget, the answer is not certified. REDUCE: the normal form is irreducible and
   reachable from the term (bounded search). CHECK_CONFLUENCE: is_confluent must equal the
   independent Knuth-Bendix criterion (every critical pair has a common normal form; the rule
   set is assumed terminating, as in the task).
4. DDC operational trace letters must be in A_DDC = {E, R, C, I, Lambda, D, M, T}.
"""

from __future__ import annotations

import re
from typing import Any

KNOWN_TASKS = frozenset({"COMPLETE", "CHECK_CONFLUENCE", "REDUCE"})
_IDENT = re.compile(r"[A-Za-z0-9_]+")
_VAR = re.compile(r"^(?:[x-z][0-9]*|[u-w][0-9]*|r[0-9]+_.*)$")
# TASK convention: default precedence when a case declares none.
_DEFAULT_PRECEDENCE = {
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
_MAX_REWRITE_STEPS = 5000

# A term is ("v", name) or ("f", symbol, (args...)).
Term = tuple


class TermSyntaxError(ValueError):
    pass


def parse(text: Any) -> Term:
    if not isinstance(text, str):
        raise TermSyntaxError(f"term must be a string, got {text!r}")
    s = text.replace(" ", "")
    term, pos = _parse_at(s, 0)
    if pos != len(s):
        raise TermSyntaxError(f"trailing input in {text!r}")
    return term


def _parse_at(s: str, pos: int) -> tuple[Term, int]:
    m = _IDENT.match(s, pos)
    if not m:
        raise TermSyntaxError(f"expected identifier at {pos} in {s!r}")
    name = m.group(0)
    pos = m.end()
    if pos < len(s) and s[pos] == "(":
        pos += 1
        args = []
        if pos < len(s) and s[pos] == ")":
            return ("f", name, ()), pos + 1
        while True:
            arg, pos = _parse_at(s, pos)
            args.append(arg)
            if pos < len(s) and s[pos] == ",":
                pos += 1
                continue
            if pos < len(s) and s[pos] == ")":
                return ("f", name, tuple(args)), pos + 1
            raise TermSyntaxError(f"unclosed argument list in {s!r}")
    if _VAR.match(name):
        return ("v", name), pos
    return ("f", name, ()), pos


def variables(t: Term) -> set[str]:
    if t[0] == "v":
        return {t[1]}
    out: set[str] = set()
    for a in t[2]:
        out |= variables(a)
    return out


def lpo_greater(s: Term, t: Term, prec: dict[str, int]) -> bool:
    if t[0] == "v":
        return s != t and t[1] in variables(s)
    if s[0] == "v":
        return False
    if any(si == t or lpo_greater(si, t, prec) for si in s[2]):
        return True
    if not all(lpo_greater(s, tj, prec) for tj in t[2]):
        return False
    ps, pt = prec.get(s[1], 0), prec.get(t[1], 0)
    if ps > pt:
        return True
    if s[1] == t[1]:
        for si, tj in zip(s[2], t[2]):
            if si != tj:
                return lpo_greater(si, tj, prec)
        return len(s[2]) > len(t[2])
    return False


def _match(pattern: Term, target: Term, subst: dict[str, Term]) -> bool:
    if pattern[0] == "v":
        bound = subst.get(pattern[1])
        if bound is None:
            subst[pattern[1]] = target
            return True
        return bound == target
    if target[0] == "v" or pattern[1] != target[1] or len(pattern[2]) != len(target[2]):
        return False
    return all(_match(p, t, subst) for p, t in zip(pattern[2], target[2]))


def _substitute(t: Term, subst: dict[str, Term]) -> Term:
    if t[0] == "v":
        return subst.get(t[1], t)
    return ("f", t[1], tuple(_substitute(a, subst) for a in t[2]))


def normalize(t: Term, rules: list[tuple[Term, Term]], budget: list[int]) -> Term:
    """Innermost normalization; budget[0] counts down rewrite steps."""
    if t[0] == "f" and t[2]:
        t = ("f", t[1], tuple(normalize(a, rules, budget) for a in t[2]))
    for lhs, rhs in rules:
        subst: dict[str, Term] = {}
        if _match(lhs, t, subst):
            budget[0] -= 1
            if budget[0] < 0:
                raise RecursionError("rewrite step budget exhausted")
            return normalize(_substitute(rhs, subst), rules, budget)
    return t


def _pairs(entries: Any) -> list[tuple[Term, Term]]:
    """Parses a list of [lhs, rhs] pairs (lists or {"lhs","rhs"} objects)."""
    if not isinstance(entries, list):
        raise TermSyntaxError("expected a list of pairs")
    out = []
    for e in entries:
        if isinstance(e, dict) and set(e) >= {"lhs", "rhs"}:
            out.append((parse(e["lhs"]), parse(e["rhs"])))
        elif isinstance(e, list) and len(e) == 2:
            out.append((parse(e[0]), parse(e[1])))
        else:
            raise TermSyntaxError(f"malformed pair {e!r}")
    return out


def _missing_field(case: dict[str, Any], task: str) -> str | None:
    required = {
        "COMPLETE": ("equations",),
        "CHECK_CONFLUENCE": ("rules",),
        "REDUCE": ("rules", "term"),
    }[task]
    for field in required:
        if field not in case:
            return field
    return None


def _malformed_terms(case: dict[str, Any], task: str) -> bool:
    try:
        if task == "COMPLETE":
            _pairs(case.get("equations"))
        else:
            _pairs(case.get("rules"))
            if task == "REDUCE":
                parse(case.get("term"))
    except TermSyntaxError:
        return True
    return False


def _precedence(case: dict[str, Any]) -> dict[str, int]:
    prec = case.get("precedence")
    return prec if isinstance(prec, dict) and prec else _DEFAULT_PRECEDENCE


def _check_refusal(case: dict[str, Any], ans: dict[str, Any]) -> tuple[bool, str]:
    reason = ans.get("reason")
    witness = ans.get("witness")
    if not isinstance(reason, str) or not reason or witness is None:
        return False, "Refusal lacks reason or witness"
    task = case.get("task", "COMPLETE")
    if reason == "UNKNOWN_TASK":
        return (task not in KNOWN_TASKS), f"UNKNOWN_TASK refusal on task {task!r}"
    if task not in KNOWN_TASKS:
        return False, f"Refusal {reason} on unknown task {task!r} (expected UNKNOWN_TASK)"
    missing = _missing_field(case, task)
    if reason == "MALFORMED_INPUT":
        return (missing is not None), f"MALFORMED_INPUT refusal (missing field: {missing})"
    if missing is not None:
        return (
            False,
            f"Refusal {reason} but the case is missing {missing} (expected MALFORMED_INPUT)",
        )
    if reason == "MALFORMED_TERM":
        return _malformed_terms(case, task), "MALFORMED_TERM refusal"
    if reason == "ORDER_FAILURE":
        if task != "COMPLETE" or not isinstance(witness, dict):
            return False, "ORDER_FAILURE needs a COMPLETE case and a witness object"
        eq = witness.get("unorientable_equation")
        equations = case.get("equations")
        if not isinstance(equations, list) or eq not in equations:
            return False, "ORDER_FAILURE witness does not name an input equation"
        try:
            lhs, rhs = parse(eq[0]), parse(eq[1])
        except (TermSyntaxError, TypeError, IndexError):
            return True, "ORDER_FAILURE on a malformed input equation"
        prec = _precedence(case)
        if lhs != rhs and not lpo_greater(lhs, rhs, prec) and not lpo_greater(rhs, lhs, prec):
            return True, "ORDER_FAILURE: LPO orients the witness equation neither way"
        return False, "ORDER_FAILURE witness equation is orientable or trivial"
    if reason == "MAX_STEPS_EXCEEDED":
        budget = case.get("max_steps")
        if type(budget) is int and budget >= 0:
            return True, f"MAX_STEPS_EXCEEDED under the declared budget {budget} (not replayed)"
        return False, "MAX_STEPS_EXCEEDED on a case that declares no step budget"
    return False, f"Unrecognized refusal reason {reason!r}"


def check_independent(case: dict[str, Any], ans: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(ans, dict):
        return False, "Answer must be a dictionary"
    if not isinstance(case, dict):
        return False, "Case must be a dictionary"
    if ans.get("case_id") != case.get("case_id"):
        return (
            False,
            f"case_id mismatch: expected {case.get('case_id')!r}, got {ans.get('case_id')!r}",
        )

    trace = ans.get("ddc_trace")
    if trace:
        steps = trace.get("steps", []) if isinstance(trace, dict) else None
        if not isinstance(steps, list):
            return False, "Malformed DDC trace"
        valid_ops = {"E", "R", "C", "I", "Lambda", "D", "M", "T"}
        for s in steps:
            if not isinstance(s, dict) or s.get("op") not in valid_ops:
                return False, f"Invalid DDC operation in trace: {s!r}"

    status = ans.get("status")
    if status == "REFUSED":
        return _check_refusal(case, ans)
    if status != "SOLVED":
        return False, f"Invalid status: {status!r}"

    task = case.get("task", "COMPLETE")
    if (
        task not in KNOWN_TASKS
        or _missing_field(case, task) is not None
        or _malformed_terms(case, task)
    ):
        return False, "SOLVED on a case that requires a refusal"
    try:
        if task == "COMPLETE":
            return _check_complete(case, ans)
        if task == "CHECK_CONFLUENCE":
            return _check_confluence(case, ans)
        return _check_reduce(case, ans)
    except (TermSyntaxError, RecursionError) as exc:
        return False, f"Independent term audit failed: {exc}"


def _check_complete(case: dict[str, Any], ans: dict[str, Any]) -> tuple[bool, str]:
    if ans.get("converged") is not True:
        return False, "converged must be true for a SOLVED completion"
    rules_raw = ans.get("rules")
    if (
        not isinstance(rules_raw, list)
        or type(ans.get("rules_count")) is not int
        or ans["rules_count"] != len(rules_raw)
    ):
        return False, "rules must be a list whose length equals rules_count"
    if (
        type(ans.get("joinability_certificates_count")) is not int
        or ans["joinability_certificates_count"] < 0
    ):
        return False, "joinability_certificates_count must be a non-negative int"
    rules = _pairs(rules_raw)
    prec = _precedence(case)
    for lhs, rhs in rules:
        if variables(rhs) - variables(lhs):
            return False, "A rule introduces variables absent from its left-hand side"
        if not lpo_greater(lhs, rhs, prec):
            return False, "A rule is not decreasing in the lexicographic path order"
    equations = _pairs(case["equations"])
    if not rules and any(lhs != rhs for lhs, rhs in equations):
        return False, "An empty rule set cannot join a non-trivial equation"
    for lhs, rhs in equations:
        budget = [_MAX_REWRITE_STEPS]
        if normalize(lhs, rules, budget) != normalize(rhs, rules, budget):
            return False, "An input equation does not join under the submitted rules"
    for left, right in critical_pairs(rules):
        if not (_normal_forms(left, rules) & _normal_forms(right, rules)):
            return False, "A critical pair of the submitted rules is not joinable"
    reference = complete_equations(equations, prec)
    if reference is None:
        return (
            False,
            "Independent completion of the input did not finish; soundness of the rules is not certified",
        )
    for lhs, rhs in rules:
        budget = [_MAX_REWRITE_STEPS]
        if normalize(lhs, reference, budget) != normalize(rhs, reference, budget):
            return False, "A submitted rule is not an equational consequence of the input equations"
    return True, (
        f"Independent audit: {len(rules)} LPO-decreasing rules, locally confluent, join every input "
        "equation, and each rule follows from the input"
    )


def _one_step_reducts(t: Term, rules: list[tuple[Term, Term]]) -> list[Term]:
    """Every term reachable in one rewrite step, at any position with any rule."""
    out = []
    for lhs, rhs in rules:
        subst: dict[str, Term] = {}
        if _match(lhs, t, subst):
            out.append(_substitute(rhs, subst))
    if t[0] == "f":
        for i, arg in enumerate(t[2]):
            for red in _one_step_reducts(arg, rules):
                out.append(("f", t[1], t[2][:i] + (red,) + t[2][i + 1 :]))
    return out


def _check_reduce(case: dict[str, Any], ans: dict[str, Any]) -> tuple[bool, str]:
    """The normal form must be irreducible and reachable from the term.

    When the rules are not confluent a term can have several normal forms; any reachable
    irreducible one passes here, and the exact checker decides which one the task wants.
    """
    nf_raw = ans.get("normal_form")
    if not isinstance(nf_raw, str):
        return False, "normal_form must be a string"
    rules = _pairs(case["rules"])
    nf = parse(nf_raw)
    if _one_step_reducts(nf, rules):
        return False, "normal_form is reducible"
    start = parse(case["term"])
    frontier, seen = [start], {start}
    while frontier:
        nxt = []
        for t in frontier:
            if t == nf:
                return True, "Independent audit: normal form is irreducible and reachable"
            for red in _one_step_reducts(t, rules):
                if red not in seen:
                    seen.add(red)
                    if len(seen) > _MAX_REWRITE_STEPS:
                        return (
                            False,
                            "Reachability of the normal form not established within the search budget",
                        )
                    nxt.append(red)
        frontier = nxt
    return False, "normal_form is not reachable from the term"


def _rename(t: Term, suffix: str) -> Term:
    if t[0] == "v":
        return ("v", t[1] + suffix)
    return ("f", t[1], tuple(_rename(a, suffix) for a in t[2]))


def _walk(t: Term, subst: dict[str, Term]) -> Term:
    while t[0] == "v" and t[1] in subst:
        t = subst[t[1]]
    return t


def _occurs(name: str, t: Term, subst: dict[str, Term]) -> bool:
    t = _walk(t, subst)
    if t[0] == "v":
        return t[1] == name
    return any(_occurs(name, a, subst) for a in t[2])


def _unify(a: Term, b: Term, subst: dict[str, Term]) -> bool:
    a, b = _walk(a, subst), _walk(b, subst)
    if a == b:
        return True
    if a[0] == "v":
        if _occurs(a[1], b, subst):
            return False
        subst[a[1]] = b
        return True
    if b[0] == "v":
        return _unify(b, a, subst)
    if a[1] != b[1] or len(a[2]) != len(b[2]):
        return False
    return all(_unify(x, y, subst) for x, y in zip(a[2], b[2]))


def _resolve(t: Term, subst: dict[str, Term]) -> Term:
    t = _walk(t, subst)
    if t[0] == "v":
        return t
    return ("f", t[1], tuple(_resolve(a, subst) for a in t[2]))


def _positions(t: Term, path: tuple[int, ...] = ()) -> list[tuple[tuple[int, ...], Term]]:
    if t[0] == "v":
        return []
    out = [(path, t)]
    for i, a in enumerate(t[2]):
        out += _positions(a, path + (i,))
    return out


def _replace(t: Term, path: tuple[int, ...], new: Term) -> Term:
    if not path:
        return new
    i = path[0]
    return ("f", t[1], t[2][:i] + (_replace(t[2][i], path[1:], new),) + t[2][i + 1 :])


def critical_pairs(rules: list[tuple[Term, Term]]) -> list[tuple[Term, Term]]:
    out = []
    for i, (l1, r1) in enumerate(rules):
        l1, r1 = _rename(l1, "_1"), _rename(r1, "_1")
        for j, (l2, r2) in enumerate(rules):
            l2, r2 = _rename(l2, "_2"), _rename(r2, "_2")
            for path, sub in _positions(l1):
                if i == j and not path:
                    continue
                subst: dict[str, Term] = {}
                if _unify(sub, l2, subst):
                    out.append((_resolve(_replace(l1, path, r2), subst), _resolve(r1, subst)))
    return out


def _normal_forms(t: Term, rules: list[tuple[Term, Term]]) -> set[Term]:
    frontier, seen, forms = [t], {t}, set()
    while frontier:
        nxt = []
        for u in frontier:
            reducts = _one_step_reducts(u, rules)
            if not reducts:
                forms.add(u)
            for red in reducts:
                if red not in seen:
                    seen.add(red)
                    if len(seen) > _MAX_REWRITE_STEPS:
                        raise RecursionError("normal-form search budget exhausted")
                    nxt.append(red)
        frontier = nxt
    return forms


def _check_confluence(case: dict[str, Any], ans: dict[str, Any]) -> tuple[bool, str]:
    claimed = ans.get("is_confluent")
    if type(claimed) is not bool:
        return False, "is_confluent must be a Boolean"
    rules = _pairs(case["rules"])
    joinable = all(
        _normal_forms(a, rules) & _normal_forms(b, rules) for a, b in critical_pairs(rules)
    )
    if claimed != joinable:
        return (
            False,
            f"is_confluent={claimed} but the independent critical-pair check gives {joinable}",
        )
    return True, f"Independent critical-pair check agrees: is_confluent={joinable}"


_COMPLETION_MAX_STEPS = 1000
_COMPLETION_MAX_RULES = 200


def _term_size(t: Term) -> int:
    return 1 if t[0] == "v" else 1 + sum(_term_size(a) for a in t[2])


def _canonical_rule(lhs: Term, rhs: Term) -> tuple[Term, Term]:
    """Renames variables to x0, x1, ... in order of first occurrence in lhs."""
    names: dict[str, str] = {}

    def walk(t: Term) -> Term:
        if t[0] == "v":
            if t[1] not in names:
                names[t[1]] = f"x{len(names)}"
            return ("v", names[t[1]])
        return ("f", t[1], tuple(walk(a) for a in t[2]))

    return walk(lhs), walk(rhs)


def _overlaps(
    outer: tuple[Term, Term], inner: tuple[Term, Term], same: bool
) -> list[tuple[Term, Term]]:
    """Critical pairs from unifying inner's lhs with non-variable subterms of outer's lhs."""
    l1, r1 = _rename(outer[0], "_a"), _rename(outer[1], "_a")
    l2, r2 = _rename(inner[0], "_b"), _rename(inner[1], "_b")
    out = []
    for path, sub in _positions(l1):
        if same and not path:
            continue
        subst: dict[str, Term] = {}
        if _unify(sub, l2, subst):
            out.append((_resolve(_replace(l1, path, r2), subst), _resolve(r1, subst)))
    return out


def complete_equations(
    equations: list[tuple[Term, Term]], prec: dict[str, int]
) -> list[tuple[Term, Term]] | None:
    """Knuth-Bendix completion under LPO; a locally confluent rule set, or None.

    Every rule produced is an equational consequence of the input. The result is returned
    only after its own critical pairs are checked to join, so it decides equality modulo
    the input equations (it is terminating because every rule decreases in LPO).
    """
    agenda = list(equations)
    rules: list[tuple[Term, Term]] = []
    steps = 0
    try:
        while agenda:
            steps += 1
            if steps > _COMPLETION_MAX_STEPS or len(rules) > _COMPLETION_MAX_RULES:
                return None
            agenda.sort(key=lambda eq: _term_size(eq[0]) + _term_size(eq[1]))
            s, t = agenda.pop(0)
            s = normalize(s, rules, [_MAX_REWRITE_STEPS])
            t = normalize(t, rules, [_MAX_REWRITE_STEPS])
            if s == t:
                continue
            if lpo_greater(s, t, prec):
                rule = _canonical_rule(s, t)
            elif lpo_greater(t, s, prec):
                rule = _canonical_rule(t, s)
            else:
                return None
            kept: list[tuple[Term, Term]] = []
            for old in rules:
                if _one_step_reducts(old[0], [rule]):
                    agenda.append(old)  # its lhs is now reducible: re-derive it as an equation
                else:
                    kept.append(
                        _canonical_rule(
                            old[0], normalize(old[1], rules + [rule], [_MAX_REWRITE_STEPS])
                        )
                    )
            kept.append(rule)
            for other in kept:
                agenda.extend(_overlaps(rule, other, other is rule))
                if other is not rule:
                    agenda.extend(_overlaps(other, rule, False))
            rules = kept
        for left, right in critical_pairs(rules):
            if normalize(left, rules, [_MAX_REWRITE_STEPS]) != normalize(
                right, rules, [_MAX_REWRITE_STEPS]
            ):
                return None
    except RecursionError:
        return None
    return rules
