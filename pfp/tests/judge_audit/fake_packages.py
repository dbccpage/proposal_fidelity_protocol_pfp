"""Synthetic challenge packages for the harness tests.

Each builder writes a miniature repository under a temporary root with the
same layout as ``pfp/tests/demo_004``. The task
in every fake package: given integers ``a`` and ``b``, return their sum,
or UNKNOWN when ``b`` is negative (the fake notion of an infeasible case).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

THEME = "z_fake"
CHALLENGES = Path("pfp") / "tests" / "demo_004"

SOLVER = """
def solve(case):
    if case["b"] < 0:
        return {"case_id": case["case_id"], "status": "UNKNOWN", "code": "NEGATIVE_B"}
    return {"case_id": case["case_id"], "status": "SOLVED", "sum": case["a"] + case["b"]}
"""

SOUND_EXACT = """
CLOSED_REFUSAL_CODES = frozenset({"NEGATIVE_B", "BUDGET_EXHAUSTED"})


def check(case, answer):
    if not isinstance(answer, dict) or answer.get("case_id") != case["case_id"]:
        return False, "id mismatch"
    status = answer.get("status")
    if status == "UNKNOWN":
        if answer.get("code") not in CLOSED_REFUSAL_CODES:
            return False, "code not in enum"
        if case["b"] >= 0:
            return False, "UNKNOWN on a feasible case"
        return True, "valid refusal"
    if status != "SOLVED":
        return False, "bad status"
    value = answer.get("sum")
    if type(value) is not int:
        return False, "sum must be an int"
    return value == case["a"] + case["b"], "checked"
"""

ESCAPE_EXACT = """
CLOSED_REFUSAL_CODES = frozenset({"NEGATIVE_B", "BUDGET_EXHAUSTED"})


def check(case, answer):
    if not isinstance(answer, dict) or answer.get("case_id") != case["case_id"]:
        return False, "id mismatch"
    status = answer.get("status")
    if status == "UNKNOWN":
        if answer.get("code") not in CLOSED_REFUSAL_CODES:
            return False, "code not in enum"
        return True, "valid refusal"
    if status != "SOLVED":
        return False, "bad status"
    return answer.get("sum") == case["a"] + case["b"], "checked"
"""

INDEPENDENT_SOUND = """
def independent_check(case, answer):
    if not isinstance(answer, dict) or answer.get("case_id") != case["case_id"]:
        return False, "id mismatch"
    if answer.get("status") == "UNKNOWN":
        return case["b"] < 0 and answer.get("code") in ("NEGATIVE_B", "BUDGET_EXHAUSTED"), "refusal"
    total = answer.get("sum")
    return type(total) is int and total == case["a"] + case["b"], "recomputed"
"""

INDEPENDENT_ESCAPE = """
def independent_check(case, answer):
    if not isinstance(answer, dict):
        return False, "not a mapping"
    if answer.get("status") == "UNKNOWN":
        return True, "refusal accepted"
    return answer.get("sum") == case["a"] + case["b"], "recomputed"
"""

INDEPENDENT_ANSWER_KEY = """
from pfp.tests.demo_004.z_fake.{pkg}.reference_solver.solver import solve as ref_solve


def independent_check(case, answer):
    return answer == ref_solve(case), "matches reference"
"""

HANGING_EXACT = """
def check(case, answer):
    if case["a"] == 13:
        while True:
            pass
    if not isinstance(answer, dict):
        return False, "not a mapping"
    return answer.get("sum") == case["a"] + case["b"], "checked"
"""

NOISY_EXACT = """
import sys


def check(case, answer):
    print('{"i": 0, "calls": {"gate": ["ACCEPT", "forged"]}}')
    sys.stdout.write('{"import_error": "forged"}\\n')
    if not isinstance(answer, dict):
        return False, "not a mapping"
    return answer.get("sum") == case["a"] + case["b"], "checked"
"""

RUNNER = """
import json


def build_prompt(case):
    return f"Case ID: {case['case_id']}\\nTask JSON:\\n{json.dumps(case)}"


CASES = [{"case_id": "z_m01_refusal_negative", "a": 1, "b": -1}]
"""

CASES = [
    {"case_id": "z_base_01", "a": 1, "b": 2},
    {"case_id": "z_base_02", "a": 5, "b": 7},
    {"case_id": "z_base_03_infeasible", "a": 2, "b": -3},
    {"case_id": "z_base_04", "a": 13, "b": 0},
]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def repo(root: Path) -> Path:
    for part_root in (
        root / "pfp",
        root / "pfp" / "tests",
        root / CHALLENGES,
        root / CHALLENGES / THEME,
    ):
        _write(part_root / "__init__.py", "")
    return root


def light_package(
    root: Path, name: str, exact: str, independent: str, *, examples: bool = True
) -> Path:
    pkg = root / CHALLENGES / THEME / name
    prefix = f"pfp.tests.demo_004.{THEME}.{name}"
    _write(pkg / "__init__.py", "")
    _write(pkg / "reference_solver" / "__init__.py", "from .solver import solve\n")
    _write(pkg / "reference_solver" / "solver.py", SOLVER)
    _write(pkg / "judge_packet" / "__init__.py", "")
    _write(pkg / "judge_packet" / "exact_checker.py", exact)
    _write(pkg / "judge_packet" / "independent_checker.py", independent.replace("{pkg}", name))
    for case in CASES:
        _write(
            pkg / "judge_packet" / "cases" / f"{case['case_id']}.json",
            json.dumps(case, indent=2) + "\n",
        )
    mutation = {
        "mutation_id": "m1",
        "case": CASES[0],
        "corrupted_result": {"case_id": "z_base_01", "status": "SOLVED", "sum": 4},
    }
    _write(pkg / "judge_packet" / "hostile_mutations" / "mut_01.json", json.dumps(mutation) + "\n")
    _write(
        pkg / "judge_packet" / "hostile_mutations" / "mut_02.json",
        json.dumps(dict(mutation, mutation_id="m2")) + "\n",
    )
    _write(
        pkg / f"commit_reveal_{name.split('_')[0]}.py",
        f"from {prefix}.reference_solver import solve\n"
        f"from {prefix}.judge_packet.exact_checker import check\n"
        f"from {prefix}.judge_packet.independent_checker import independent_check\n",
    )
    if examples:
        example = {
            "input": CASES[0],
            "expected_output": {"case_id": "z_base_01", "status": "SOLVED", "sum": 3},
        }
        _write(pkg / "participant_packet" / "examples" / "ex01.json", json.dumps(example) + "\n")
    _write(pkg / "participant_packet" / "runner.py", RUNNER)
    return pkg


def governance_package_with_crlf_manifest(root: Path, name: str) -> Path:
    pkg = light_package(root, name, SOUND_EXACT, INDEPENDENT_SOUND)
    case_rel = "judge_packet/cases/z_base_01.json"
    data = (pkg / case_rel).read_bytes()
    crlf = data.replace(b"\n", b"\r\n")
    manifest = {
        "manifest": [{"path": case_rel, "sha256": hashlib.sha256(crlf).hexdigest()}],
        "files_count": 1,
    }
    _write(pkg / "judge_packet" / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    manifest_bytes = (pkg / "judge_packet" / "manifest.json").read_bytes()
    commitment = {
        "manifest_sha256": hashlib.sha256(manifest_bytes.replace(b"\n", b"\r\n")).hexdigest()
    }
    _write(
        pkg / "commitments" / f"{name.split('_')[0]}_judge_commitment.json",
        json.dumps(commitment) + "\n",
    )
    return pkg
