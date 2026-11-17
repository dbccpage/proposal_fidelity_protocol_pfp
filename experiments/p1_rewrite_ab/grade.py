"""P1 exact grader. AuthorityEffect: None. Standard library only, no float.

Each (task, arm) gets one grade:
  CORRECT    every field equals the reference exactly
  PULLED     (sums only) the total equals the wrong total the trigger sentence predicts
  WRONG      parsed, but not equal
  MALFORMED  not one JSON object with exactly the contract's fields and value shapes
  TRUNCATED  finish_reason was "length"
  NO_REPLY   HTTP error, transport error, or an intent with no result (held)
  NOT_RUN    no ledger line

Paired comparisons use the tasks both arms ran: b = A correct and B not, c = B correct and A not.
The exact two-sided sign test p is a Fraction: min(1, 2 * sum_{k<=min(b,c)} C(b+c,k) / 2^(b+c)).

    python grade.py --ledger ledger_live.jsonl > report.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hodge  # noqa: E402
import run  # noqa: E402

INT = re.compile(r"-?(0|[1-9][0-9]*)")
RAT = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?")
PAIRS = {
    "S": [("plain", "prose"), ("wf5", "prose"), ("fenced", "prose"), ("wf5", "plain")],
    "H": [("wire", "prose"), ("wire_qed", "wire"), ("wire_qed", "prose"),
          ("tier_s_qed", "wire_qed"), ("tier_s_qed", "prose")],
}
GRADES = ("CORRECT", "PULLED", "WRONG", "MALFORMED", "TRUNCATED", "NO_REPLY", "NOT_RUN")
INT_FIELDS = ("b0", "b1", "euler_characteristic")


class Malformed(ValueError):
    pass


def rational(value: object) -> Fraction:
    """A string 'a' or 'a/b' in lowest terms, b > 1. Anything else is malformed."""
    if not isinstance(value, str) or not RAT.fullmatch(value):
        raise Malformed(f"not an exact rational string: {value!r}")
    x = Fraction(value)
    if hodge.text(x) != value:
        raise Malformed(f"not in lowest terms: {value!r}")
    return x


def integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise Malformed(f"not a JSON integer: {value!r}")
    return value


def parse_object(content: str) -> dict:
    try:
        obj = json.loads(content, parse_float=lambda s: (_ for _ in ()).throw(Malformed(s)))
    except Malformed:
        raise
    except ValueError as err:
        raise Malformed(f"not JSON: {err}") from None
    if not isinstance(obj, dict):
        raise Malformed("not a JSON object")
    return obj


def grade_sum(task: dict, obj: dict) -> str:
    if set(obj) != {"total"}:
        raise Malformed(f"fields {sorted(obj)}")
    total = obj["total"]
    if not isinstance(total, str) or not INT.fullmatch(total) or total == "-0":
        raise Malformed(f"total {total!r}")
    if int(total) == int(task["expected"]["total"]):
        return "CORRECT"
    pulled = Fraction(task["pulled_total"])
    # A mean pull may be a fraction; an integer within 1 of it is the same pull, rounded.
    if Fraction(total) == pulled or (pulled.denominator > 1 and abs(Fraction(total) - pulled) < 1):
        return "PULLED"
    return "WRONG"


def grade_hodge(task: dict, obj: dict) -> str:
    if set(obj) != set(hodge.FIELDS):
        raise Malformed(f"fields {sorted(obj)}")
    ref = task["expected"]
    ok = True
    for field in hodge.FIELDS:
        got, want = obj[field], ref[field]
        if field in INT_FIELDS:
            ok &= integer(got) == want
        elif isinstance(want, list):
            if not isinstance(got, list) or len(got) != len(want):
                raise Malformed(f"{field} shape")
            ok &= [rational(g) for g in got] == [Fraction(w) for w in want]
        else:
            ok &= rational(got) == Fraction(want)
    return "CORRECT" if ok else "WRONG"


def grade_result(task: dict, result: dict | None) -> str:
    if result is None or result["status"] != 200 or result.get("error"):
        return "NO_REPLY"
    try:
        reply = json.loads(result["reply"])
        choice = reply["choices"][0]
        content = choice["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        return "MALFORMED"
    if choice.get("finish_reason") == "length":
        return "TRUNCATED"
    if not isinstance(content, str):
        return "MALFORMED"
    try:
        obj = parse_object(content)
        return grade_sum(task, obj) if task["family"] == "S" else grade_hodge(task, obj)
    except Malformed:
        return "MALFORMED"


def sign_test(b: int, c: int) -> Fraction:
    n = b + c
    if n == 0:
        return Fraction(1)
    tail = sum(math.comb(n, k) for k in range(min(b, c) + 1))
    return min(Fraction(1), Fraction(2 * tail, 2**n))


def bind(tasks: list[dict], ledger: list[dict]) -> tuple[dict[tuple[str, str], dict], set[tuple[str, str]]]:
    """Keep only the records bound to the request each current (task, arm) would send.

    The request is rebuilt from the task file with the model and effort its intent recorded, and its
    hash must equal the intent's request_sha256. A (task, arm) the ledger holds only under another
    request, such as an older kit that reused the task ids, refuses the whole grading.
    """
    seen, intents, results = run.ledger_index(ledger)
    params = {(r["task_id"], r["arm"], r["request_sha256"]): (r["model"], r["effort"])
              for r in ledger if r["kind"] == "intent"}
    wanted: dict[tuple[str, str], str] = {}
    for task in tasks:
        for arm in task["arms"]:
            key = (task["task_id"], arm)
            for got in seen.get(key, ()):
                if run.request_sha(task, arm, *params[(*key, got)]) == got:
                    wanted[key] = got
            wanted.setdefault(key, "")
    bad = run.mismatches({k: v for k, v in seen.items() if k in wanted},
                         {k: v for k, v in wanted.items() if k in seen})
    if bad:
        raise run.LedgerMismatch(f"LEDGER_REQUEST_MISMATCH: {len(bad)} (task, arm) pairs were sent as a "
                                 f"request this task file does not make, first {bad[0]}")
    bound = {k: results[(*k, v)] for k, v in wanted.items() if (*k, v) in results}
    held = {k for k, v in wanted.items() if (*k, v) in intents}
    return bound, held


def grade_all(tasks: list[dict], ledger: list[dict]) -> dict:
    results, intents = bind(tasks, ledger)
    grades: dict[tuple[str, str], str] = {}
    for task in tasks:
        for arm in task["arms"]:
            key = (task["task_id"], arm)
            if key in results:
                grades[key] = grade_result(task, results[key])
            else:
                grades[key] = "NO_REPLY" if key in intents else "NOT_RUN"
    arms: dict[str, dict] = {}
    for task in tasks:
        for arm in task["arms"]:
            row = arms.setdefault(f"{task['family']}|{arm}", {g: 0 for g in GRADES})
            row[grades[(task["task_id"], arm)]] += 1
    by_trigger: dict[str, Counter] = {}
    for task in tasks:
        if task["family"] == "S":
            for arm in task["arms"]:
                by_trigger.setdefault(f"{task['trigger']}|{arm}", Counter())[
                    grades[(task["task_id"], arm)]] += 1
    pairs = []
    for family, comparisons in PAIRS.items():
        fam = [t for t in tasks if t["family"] == family]
        for a, b_arm in comparisons:
            both = [t for t in fam if grades.get((t["task_id"], a), "NOT_RUN") != "NOT_RUN"
                    and grades.get((t["task_id"], b_arm), "NOT_RUN") != "NOT_RUN"]
            if not both:
                continue
            b = sum(grades[(t["task_id"], a)] == "CORRECT" and grades[(t["task_id"], b_arm)] != "CORRECT"
                    for t in both)
            c = sum(grades[(t["task_id"], b_arm)] == "CORRECT" and grades[(t["task_id"], a)] != "CORRECT"
                    for t in both)
            p = sign_test(b, c)
            pairs.append({"family": family, "a": a, "b": b_arm, "paired_tasks": len(both),
                          "a_only_correct": b, "b_only_correct": c,
                          "sign_test_p": hodge.text(p)})
    cost = sum(r.get("cost_nano_usd", 0) for r in results.values())
    return {"authority_effect": "None", "arms": arms,
            "sum_by_trigger": {k: dict(v) for k, v in sorted(by_trigger.items())},
            "pairs": pairs, "calls": len(results),
            "cost_micro_usd_measured": math.ceil(Fraction(cost, 1000)),
            "cost_sources": dict(Counter(r.get("cost_source", "?") for r in results.values())),
            "grades": {f"{t}|{a}": g for (t, a), g in sorted(grades.items())}}


def merge_tasks(task_lists: list[list[dict]]) -> list[dict]:
    """Union the arms of tasks that share a task_id (for example tasks.jsonl and tasks_tier_s.jsonl)."""
    merged: dict[str, dict] = {}
    for rows in task_lists:
        for t in rows:
            if t["task_id"] in merged:
                base = merged[t["task_id"]]
                if base["expected"] != t["expected"] or base["system"] != t["system"]:
                    raise SystemExit(f"TASK_CONFLICT: {t['task_id']} differs between task files")
                clash = set(base["arms"]) & set(t["arms"])
                if clash:
                    raise SystemExit(f"ARM_CONFLICT: {t['task_id']} {sorted(clash)}")
                base["arms"] = {**base["arms"], **t["arms"]}
            else:
                merged[t["task_id"]] = dict(t, arms=dict(t["arms"]))
    return list(merged.values())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tasks", type=Path, action="append")
    ap.add_argument("--ledger", type=Path, action="append", required=True)
    args = ap.parse_args(argv)
    from run import load_ledger, load_tasks

    tasks = merge_tasks([load_tasks(p) for p in (args.tasks or [HERE / "tasks.jsonl"])])
    ledger = [r for p in args.ledger for r in load_ledger(p)]
    report = grade_all(tasks, ledger)
    print(json.dumps(report, sort_keys=True, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
