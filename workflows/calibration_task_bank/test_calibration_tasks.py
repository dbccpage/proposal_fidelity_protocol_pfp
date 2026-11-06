"""Calibration task bank: checkers accept the reference and refuse planted mistakes.

Each review task's truth is computed by its checker; these controls pin that the computed
reference passes and that a miss, a false alarm, a fenced reply and a drifted prompt fail.
AuthorityEffect: None.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parent / "tasks"
REVIEW_TASKS = ("review_graph_claims", "review_hodge_claims", "review_code_claims")


def run_checker(task_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(task_dir / "check.py"), *args],
        capture_output=True, text=True, check=False, timeout=60)


def reference(task_dir: Path) -> list[str]:
    done = run_checker(task_dir, "--reference")
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)["flagged_claims"]


@pytest.mark.parametrize("task", REVIEW_TASKS)
def test_reference_passes_and_each_planted_mistake_fails(tmp_path, task):
    task_dir = TASKS / task
    flagged = reference(task_dir)
    assert flagged, "a review task must plant at least one fault"
    cases = {
        "ok": ({"flagged_claims": flagged}, 0),
        "miss": ({"flagged_claims": flagged[1:]}, 1),
        "false_alarm": ({"flagged_claims": [*flagged, "c1"] if "c1" not in flagged else [*flagged, "c3"]}, 1),
        "extra_key": ({"flagged_claims": flagged, "notes": "x"}, 1),
    }
    for name, (answer, expected) in cases.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(answer), encoding="utf-8")
        assert run_checker(task_dir, str(path)).returncode == expected, name
    fenced = tmp_path / "fenced.json"
    fenced.write_text("```json\n" + json.dumps({"flagged_claims": flagged}) + "\n```", encoding="utf-8")
    assert run_checker(task_dir, str(fenced)).returncode == 1


@pytest.mark.parametrize("task", REVIEW_TASKS)
def test_prompt_lists_every_claim_and_leaks_no_answer(task):
    task_dir = TASKS / task
    prompt = (task_dir / "prompt.md").read_text(encoding="utf-8")
    spec_text = (task_dir / "check.py").read_text(encoding="utf-8")
    claims = dict(re.findall(r'^    "(c\d+)": [\'"](.+?)[\'"],$', spec_text, flags=re.MULTILINE))
    assert claims and all(f"`{cid}`: {text}" in prompt for cid, text in claims.items())
    example = re.search(r'\{"flagged_claims": \[(.*?)\]\}', prompt).group(1)
    assert not re.search(r'"c\d+"', example), "the format example must not name a claim id"


def test_code_checker_refuses_a_prompt_that_drifted_from_its_source(tmp_path):
    copy = tmp_path / "calibration"
    shutil.copytree(TASKS, copy)
    prompt = copy / "review_code_claims" / "prompt.md"
    prompt.write_text(prompt.read_text(encoding="utf-8").replace("lower()", "upper()"), encoding="utf-8")
    answer = tmp_path / "answer.json"
    answer.write_text(json.dumps({"flagged_claims": reference(TASKS / "review_code_claims")}), encoding="utf-8")
    done = run_checker(copy / "review_code_claims", str(answer))
    assert done.returncode == 1 and "does not show the checked data or claims" in done.stdout


@pytest.mark.parametrize("task,answer_key", [("graph_cycle_rank", None), ("hodge_split", "--reference")])
def test_exact_tasks_accept_their_reference(tmp_path, task, answer_key):
    task_dir = TASKS / task
    if answer_key:
        answer = run_checker(task_dir, "--reference").stdout
    else:
        answer = json.dumps({"vertices": 12, "edges": 16, "components": 3, "component_sizes": [7, 4, 1],
            "cycle_rank": 7, "spanning_forest_edge_ids": [0, 1, 3, 4, 5, 7, 11, 12, 13]})
    path = tmp_path / "answer.json"
    path.write_text(answer, encoding="utf-8")
    assert run_checker(task_dir, str(path)).returncode == 0
