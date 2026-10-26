"""
conditions.py — the judging conditions for the head-to-head.

- `symbol_game`: the exact host (Phi_1 == 0 ?). Reference; exact by construction.
- `llm(..., "direct")`: a snap yes/no judgment from a language model.
- `llm(..., "cot")`:   the same model asked to reason step by step first.

Grammar-constrained decoding is not implemented in this pilot. A prompt requesting
one word is not a constrained decoder.
"""

from __future__ import annotations

import re

from .host import host_verdict


def _format_problem(instance) -> str:
    lines = [f"  r({v}) - r({u}) = {d}" for (u, v), d in instance.claims.items()]
    return ("You are given integer ranks r(X) for the items: "
            + ", ".join(instance.items) + ".\n"
            "All of the following constraints are claimed to hold simultaneously:\n"
            + "\n".join(lines))


_DIRECT = ("\n\nCan a single integer assignment of ranks satisfy ALL of these "
           "constraints at once? Answer with exactly one word: "
           "CONSISTENT or CONTRADICTION.")
_COT = ("\n\nDetermine whether a single integer assignment of ranks can satisfy ALL "
        "of these constraints at once. Reason through it, then end with a final line "
        "exactly of the form 'VERDICT: CONSISTENT' or 'VERDICT: CONTRADICTION'.")


def parse_verdict(raw: str) -> str:
    """Read only a whole verdict or the required final VERDICT line.

    Prose, refusals and ambiguous answers remain UNKNOWN. In particular, the
    substring CONSISTENT inside INCONSISTENT must never count as acceptance.
    """
    up = (raw or "").strip().upper()
    if up in ("CONSISTENT", "CONTRADICTION"):
        return up
    final = up.splitlines()[-1] if up else ""
    match = re.fullmatch(r"VERDICT:\s*(CONSISTENT|CONTRADICTION)", final)
    if match:
        return match.group(1)
    return "UNKNOWN"


def symbol_game(instance) -> str:
    return host_verdict(instance)


def judge(backend, instance, style: str = "direct") -> dict:
    if style not in ("direct", "cot"):
        raise ValueError(f"unknown judge style {style!r}")
    ask = _COT if style == "cot" else _DIRECT
    prompt = _format_problem(instance) + ask
    raw = backend.complete(prompt)
    return {"prompt": prompt, "raw": raw, "verdict": parse_verdict(raw)}


def llm(backend, instance, style: str = "direct") -> str:
    return judge(backend, instance, style)["verdict"]
