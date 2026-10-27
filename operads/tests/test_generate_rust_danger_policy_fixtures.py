"""Freeze exact danger policy admission before native policy implementation.

Fraction values cross the JSON boundary as numerator/denominator decimal strings.
Untyped Python TypeError/ValueError become named native Refusal records.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from operads.domain.workflow_graph import DangerSignalPolicy


def wire(value):
    if type(value) is Fraction:
        return {"numerator": str(value.numerator), "denominator": str(value.denominator)}
    return value


def main():
    cases = [
        {},
        {"enforce_danger_gate": False},
        {"quarantine_on_critical": False},
        {"enforce_danger_gate": False, "quarantine_on_critical": False},
    ]
    for name in ("enforce_danger_gate", "quarantine_on_critical"):
        for value in (0, 1, "True", None, [], {}):
            cases.append({name: value})
    for value in (
        Fraction(1, 2), Fraction(1, 3), Fraction(2, 3),
        Fraction(-2, -3), Fraction(2, 4), Fraction(10**80, 10**80 + 1),
        Fraction(1, 10**80), Fraction(-1, 2), Fraction(3, 2),
        Fraction(0), Fraction(1), -1, 0, 1, 2, 10**80,
        True, False, 0.5, "1/2", None, [], {},
    ):
        cases.append({"allosteric_quorum_threshold": value})
    # Boolean guards precede threshold admission.
    cases.append({"enforce_danger_gate": 1, "allosteric_quorum_threshold": "bad"})
    rows = []
    for kwargs in cases:
        try:
            value = DangerSignalPolicy(**kwargs)
            expected = {"ok": {
                "enforce_danger_gate": value.enforce_danger_gate,
                "quarantine_on_critical": value.quarantine_on_critical,
                "allosteric_quorum_threshold": wire(value.allosteric_quorum_threshold),
            }}
        except (TypeError, ValueError) as exc:
            code = "DANGER_POLICY_TYPE_ERROR" if type(exc) is TypeError else "DANGER_POLICY_VALUE_ERROR"
            expected = {"error": {"code": code, "message": f"{code}: {exc}"}}
        rows.append({"input": {key: wire(value) for key, value in kwargs.items()}, "expected": expected})
    path = Path(__file__).resolve().parents[2] / "engine/crates_rs/tests/core_operads/fixtures/python_danger_policy_v1.json"
    path.write_text(json.dumps({"vectors": rows}, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen {len(rows)} exact danger policy vectors before native implementation.")


if __name__ == "__main__":
    main()
