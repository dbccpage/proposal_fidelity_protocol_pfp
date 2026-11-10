"""Participant runner for C051: Exact LP Solver with Duals.

Usage: ``py -3.12 runner.py <path to candidate solver .py>``. Loads the
candidate's ``solve(case)`` and checks it on the public examples.

Correction, 2026-09-29: OUT_OF_SCOPE is accepted only when the example is
malformed. Before, any OUT_OF_SCOPE reply counted as a pass, so a solver that
refused everything scored 14/14. Replies must also carry the example's
``case_id`` and canonical rational strings, and a reply that makes the check
fail with an exception is counted as a failure, not a crash.
"""

import glob
import importlib.util
import json
import os
import re
import sys
from fractions import Fraction

_CANONICAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?")


def parse_input(value):
    """Case entries: an int (not a Boolean) or a fraction string."""
    if type(value) is int:
        return Fraction(value)
    if type(value) is str and re.fullmatch(r"-?[0-9]+(?:/[0-9]+)?", value.strip()):
        num, _, den = value.strip().partition("/")
        return Fraction(int(num), int(den) if den else 1)
    raise ValueError(f"invalid case entry: {value!r}")


def parse_answer(value):
    """Answer entries: canonical rational strings such as "3", "-1/2"."""
    if type(value) is not str or not _CANONICAL.fullmatch(value) or value == "-0":
        raise ValueError(f"non-canonical answer entry: {value!r}")
    num, _, den = value.partition("/")
    frac = Fraction(int(num), int(den) if den else 1)
    if den and (den == "1" or frac.denominator != int(den)):
        raise ValueError(f"answer entry not in lowest terms: {value!r}")
    return frac


def case_is_malformed(case):
    if not isinstance(case, dict):
        return True
    if any(not isinstance(case.get(key), list) for key in ("A", "b", "c")):
        return True
    m, n = len(case["b"]), len(case["c"])
    if m < 1 or n < 1 or len(case["A"]) != m:
        return True
    if any(not isinstance(row, list) or len(row) != n for row in case["A"]):
        return True
    try:
        for value in [v for row in case["A"] for v in row] + case["b"] + case["c"]:
            parse_input(value)
    except (ValueError, ZeroDivisionError):
        return True
    return False


def check_solution(case, result):
    try:
        return _check(case, result)
    except (ValueError, TypeError, ZeroDivisionError, AttributeError, KeyError):
        return False


def _check(case, result):
    if not isinstance(result, dict) or result.get("case_id") != case.get("case_id"):
        return False
    status = result.get("status")
    malformed = case_is_malformed(case)
    if status == "OUT_OF_SCOPE":
        return malformed
    if malformed or status != "SOLVED":
        return False
    kind = result.get("kind")
    A = [[parse_input(x) for x in row] for row in case["A"]]
    b = [parse_input(x) for x in case["b"]]
    c = [parse_input(x) for x in case["c"]]
    m, n = len(b), len(c)
    if kind == "OPTIMAL":
        x = [parse_answer(v) for v in result.get("x", [])]
        y = [parse_answer(v) for v in result.get("y", [])]
        val = parse_answer(result.get("value"))
        if len(x) != n or len(y) != m:
            return False
        if any(xi < 0 for xi in x) or any(yi < 0 for yi in y):
            return False
        for i in range(m):
            if sum(A[i][j] * x[j] for j in range(n)) > b[i]:
                return False
        for j in range(n):
            if sum(A[i][j] * y[i] for i in range(m)) < c[j]:
                return False
        cx = sum(c[j] * x[j] for j in range(n))
        by = sum(b[i] * y[i] for i in range(m))
        return cx == by == val
    if kind == "INFEASIBLE":
        y = [parse_answer(v) for v in result.get("farkas_y", [])]
        if len(y) != m or any(yi < 0 for yi in y):
            return False
        for j in range(n):
            if sum(A[i][j] * y[i] for i in range(m)) < 0:
                return False
        return sum(b[i] * y[i] for i in range(m)) < 0
    if kind == "UNBOUNDED":
        x = [parse_answer(v) for v in result.get("x", [])]
        d = [parse_answer(v) for v in result.get("ray", [])]
        if len(x) != n or len(d) != n or any(xi < 0 for xi in x) or any(di < 0 for di in d):
            return False
        for i in range(m):
            if sum(A[i][j] * x[j] for j in range(n)) > b[i]:
                return False
            if sum(A[i][j] * d[j] for j in range(n)) > 0:
                return False
        return sum(c[j] * d[j] for j in range(n)) > 0
    return False


def score(solve, example_paths):
    passed = 0
    for path in example_paths:
        with open(path, encoding="utf-8") as handle:
            case = json.load(handle)["input"]
        if check_solution(case, solve(case)):
            passed += 1
    return passed


def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("candidate_solver", sys.argv[1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["candidate_solver"] = mod
    spec.loader.exec_module(mod)
    files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "examples", "*.json")))
    passed = score(mod.solve, files)
    print(f"Runner result: {passed}/{len(files)} passed.")
    sys.exit(0 if passed == len(files) else 1)


if __name__ == "__main__":
    main()
