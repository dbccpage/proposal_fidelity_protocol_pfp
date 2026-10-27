import json
from pathlib import Path

from pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.reference_solver import (
    solve,
)

ex_dir = Path(__file__).resolve().parent / "participant_packet" / "examples"
ex_dir.mkdir(parents=True, exist_ok=True)

raw_cases = [
    {"case_id": "dfa_ex_01", "task": "MINIMIZE", "alphabet": ["a", "b"], "regex": "(a|b)*abb"},
    {"case_id": "dfa_ex_02", "task": "MINIMIZE", "alphabet": ["a", "b"], "regex": "#"},
    {"case_id": "dfa_ex_03", "task": "MINIMIZE", "alphabet": ["a", "b"], "regex": "%"},
    {"case_id": "dfa_ex_04", "task": "EQUIV", "alphabet": ["a", "b"], "r1": "a*b*", "r2": "(a|b)*"},
    {"case_id": "dfa_ex_05", "task": "MINIMIZE", "alphabet": ["a", "b"], "regex": "(a|b)*"},
    {
        "case_id": "dfa_ex_06",
        "task": "EQUIV",
        "alphabet": ["a", "b"],
        "r1": "(a|b)*",
        "r2": "(a*b*)*",
    },
    {
        "case_id": "dfa_ex_07",
        "task": "MINIMIZE",
        "alphabet": ["a", "b"],
        "regex": "(a|b)*a(a|b)(a|b)",
    },
    {
        "case_id": "dfa_ex_08",
        "task": "MINIMIZE",
        "alphabet": ["a", "b", "c"],
        "regex": "(a|b|c)*a(b|c)*",
    },
    {"case_id": "dfa_ex_09", "task": "MINIMIZE", "alphabet": ["a"], "regex": "((a*)*)*"},
    {"case_id": "dfa_ex_10", "task": "EQUIV", "alphabet": ["a", "b"], "r1": "a|b", "r2": "b|a"},
    {"case_id": "dfa_ex_11", "task": "MINIMIZE", "alphabet": ["a", "b"], "regex": "(a|b)*|a*"},
    {"case_id": "dfa_ex_12", "task": "MINIMIZE", "alphabet": ["a", "b"], "regex": "a("},
    {
        "case_id": "dfa_ex_13",
        "task": "MINIMIZE",
        "alphabet": ["a", "b", "c", "d"],
        "regex": "a*b*c*d*",
    },
    {
        "case_id": "dfa_ex_14",
        "task": "EQUIV",
        "alphabet": ["a", "b"],
        "r1": "(a|b)*ab",
        "r2": "(a|b)*ba",
    },
]

for c in raw_cases:
    sol = solve(c)
    payload = {"case": c, "expected_output": sol}
    with open(ex_dir / f"{c['case_id']}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
print(f"Generated {len(raw_cases)} examples in {ex_dir}")
