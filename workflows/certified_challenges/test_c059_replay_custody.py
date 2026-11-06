"""Replay-custody test for Challenge C059: reference solver, dual checkers and SQLite replay.

Ported from an internal test suite. The original file also drove synthetic
replies through a provider boundary that is not part of this repository;
that test and a unified-store test built on it were removed. The remaining
test is unchanged apart from import paths.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from c059_sql_null_total_query_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from c059_sql_null_total_query_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from c059_sql_null_total_query_synthesis.reference_solver.solver import (
    solve as c059_solve,
)
from c059_sql_null_total_query_synthesis.matrix_cases import (
    TEST_CASES,
)
from sqlite_pilot_store import (
    PilotRunRecord,
    SqlitePilotStore,
)

C059_DIR = Path(__file__).resolve().parent / "c059_sql_null_total_query_synthesis"
MUTATIONS_DIR = C059_DIR / "judge_packet" / "hostile_mutations"


def _load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def test_c059_pfp_reference_solver_and_checkers(tmp_path: Path) -> None:
    """Verifies C059 reference solver and judge packet checkers under native PFP harness."""
    db_path = tmp_path / "pilots.db"
    store = SqlitePilotStore(db_path)

    checkers = [("exact", verify_candidate), ("independent", independent_check)]

    # 1. Test all 10 standard C059 matrix cases (constructive and poisoned)
    for case in TEST_CASES:
        solution = c059_solve(case)

        # Run dual checkers
        exact_ok, exact_msg = verify_candidate(case, solution)
        assert exact_ok is True, f"Exact checker failed on {case['case_id']}: {exact_msg}"

        indep_ok, indep_msg = independent_check(case, solution)
        assert indep_ok is True, f"Independent checker failed on {case['case_id']}: {indep_msg}"

        expected_status = "OUT_OF_SCOPE" if "poison" in case["case_id"] else "ACCEPTED"

        # Record run in SQLite
        record = PilotRunRecord(
            run_id=f"pfp_{case['case_id']}",
            challenge_id="C059",
            harness="PFP",
            model_id="reference_solver_v1",
            case_id=case["case_id"],
            outcome=expected_status,
            input_data=case,
            output_data=solution,
            checkers=[
                {"checker": "exact", "ok": exact_ok, "message": exact_msg},
                {"checker": "independent", "ok": indep_ok, "message": indep_msg},
            ],
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            cost_usd=0.0,
        )
        store.record_run(record)

    # 2. Test hostile mutation rejection
    mut_files = sorted(MUTATIONS_DIR.glob("*.json"))[:3]
    for mut_file in mut_files:
        mut_data = _load_json(mut_file)
        case = mut_data.get("case", {})
        cand = mut_data.get("candidate", {})
        if case and cand:
            exact_ok, _ = verify_candidate(case, cand)
            indep_ok, _ = independent_check(case, cand)
            assert not (exact_ok and indep_ok), f"Hostile mutation unexpectedly accepted: {mut_file}"

    # 3. Verify SQLite persistence and replay
    pfp_runs = store.list_runs(challenge_id="C059", harness="PFP")
    assert len(pfp_runs) == len(TEST_CASES)

    for run in pfp_runs:
        replay = store.replay_run(run.run_id, checkers)
        assert replay["all_passed"] is True
        assert replay["original_outcome"] in ("ACCEPTED", "OUT_OF_SCOPE")
