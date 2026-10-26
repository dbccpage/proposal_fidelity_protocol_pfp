"""C047: every judge case runs through both checkers within a per-case time limit.

Counterexample named by this test: the independent checker enumerated divisor candidates
``for d in range(1, c0 + 1)`` of the leading polynomial's constant term. On the package's own
case ``c047_poison_62_overflow_terms`` that constant is 1180591620717411303424, so the loop
never finished and any participant could stall the judge with a large constant.

The cases run in one worker process; the parent kills it if any single case exceeds the
limit and names that case.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from omega_engine_pfp.tests.demo_004.e_formal_math.c047_sequence_law_discovery.judge_packet.independent_checker import (
    _has_integer_root_at_or_after,
)

PKG = Path(__file__).resolve().parents[1]
REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
CASES = sorted((PKG / "judge_packet" / "cases").glob("*.json"))
PER_CASE_SECONDS = 20.0

WORKER = r"""
import json, sys, time
from omega_engine_pfp.tests.demo_004.e_formal_math.c047_sequence_law_discovery.reference_solver.solver import solve
from omega_engine_pfp.tests.demo_004.e_formal_math.c047_sequence_law_discovery.judge_packet.exact_checker import check_solution
from omega_engine_pfp.tests.demo_004.e_formal_math.c047_sequence_law_discovery.judge_packet.independent_checker import independent_check
print(json.dumps({"ready": True}), flush=True)
for line in sys.stdin:
    path = line.strip()
    if not path:
        continue
    case = json.loads(open(path, encoding="utf-8").read())
    t0 = time.time()
    answer = solve(case)
    exact = check_solution(case, answer)
    indep = independent_check(case, answer)
    print(json.dumps({"case": case["case_id"], "exact": list(exact), "indep": list(indep),
                      "seconds": time.time() - t0}), flush=True)
"""


def test_every_judge_case_finishes_in_bounded_time_and_both_checkers_accept() -> None:
    assert (REPO_ROOT / "omega_engine_projects").is_dir()
    assert len(CASES) == 64
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT), PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen(
        [sys.executable, "-c", WORKER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=str(REPO_ROOT),
    )
    lines: queue.Queue[str] = queue.Queue()
    threading.Thread(target=lambda: [lines.put(ln) for ln in proc.stdout], daemon=True).start()
    try:
        assert json.loads(lines.get(timeout=60.0)) == {"ready": True}
        results = []
        for path in CASES:
            proc.stdin.write(str(path) + "\n")
            proc.stdin.flush()
            try:
                results.append(json.loads(lines.get(timeout=PER_CASE_SECONDS)))
            except queue.Empty:
                pytest.fail(f"{path.stem} did not finish within {PER_CASE_SECONDS} s")
    finally:
        proc.kill()
        proc.wait()
    failures = [r for r in results if not (r["exact"][0] and r["indep"][0])]
    assert failures == []
    finished = {r["case"] for r in results}
    for tail in (
        "c047_poison_62_overflow_terms",
        "c047_poison_63_leading_root_jump",
        "c047_poison_64_zeros_with_noise",
    ):
        assert tail in finished


LARGE_ROOT_CHECKS = r"""
from omega_engine_pfp.tests.demo_004.e_formal_math.c047_sequence_law_discovery.judge_packet.independent_checker import (
    _has_integer_root_at_or_after as has_root,
)
big = 1180591620717411303424
huge = 10**30
quadratic = [huge * (huge + 7), -(2 * huge + 7), 1]  # (n - 10^30)(n - 10^30 - 7)
results = [
    has_root([big, 1], 0) is False,
    has_root([-big, 1], 0) is True,
    has_root(quadratic, huge + 1) is True,
    has_root(quadratic, huge + 8) is False,
    has_root([5, 0, 0, big], -(10**40)) is False,
    has_root([0, 0, 1], 0) is True,
    has_root([0, 0, 1], 1) is False,
    has_root([0, 0, 0], 5) is True,
]
print(results)
"""


def test_integer_roots_found_without_enumerating_the_constant() -> None:
    """Run in a subprocess so that an enumerating implementation times out instead of hanging."""
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT), PYTHONDONTWRITEBYTECODE="1")
    try:
        done = subprocess.run(
            [sys.executable, "-c", LARGE_ROOT_CHECKS],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(REPO_ROOT),
            timeout=PER_CASE_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"integer-root search on a 70-bit constant did not finish within {PER_CASE_SECONDS} s"
        )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == str([True] * 8)


def test_integer_roots_agree_with_brute_force_on_small_polynomials() -> None:
    import itertools

    for coeffs in itertools.product(range(-3, 4), repeat=4):
        trimmed = list(coeffs)
        while trimmed and trimmed[-1] == 0:
            trimmed.pop()
        if len(trimmed) < 2:
            continue
        for start in (-5, 0, 3):
            brute = any(sum(c * n**j for j, c in enumerate(trimmed)) == 0 for n in range(start, 50))
            assert _has_integer_root_at_or_after(trimmed, start) is brute, (trimmed, start)
