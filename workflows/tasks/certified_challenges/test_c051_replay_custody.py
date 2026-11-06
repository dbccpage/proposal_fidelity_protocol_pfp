"""Replay-custody test for Challenge C051: reference solver, dual checkers and SQLite replay.

Ported from an internal test suite. The original file also drove synthetic
replies through a provider boundary that is not part of this repository;
that test was removed. The two remaining tests are unchanged apart from
import paths and the second harness label.

AuthorityEffect: None.
"""

from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
from typing import Any

from c051_exact_lp_solver_with_duals.judge_packet.exact_checker import (
    check_solution as exact_check,
)
from c051_exact_lp_solver_with_duals.judge_packet.independent_checker import (
    check_solution as indep_check,
)
from c051_exact_lp_solver_with_duals.reference_solver.solver import (
    solve as c051_solve,
)
from sqlite_pilot_store import (
    PilotRunRecord,
    SqlitePilotStore,
)

C051_DIR = Path(__file__).resolve().parent / "c051_exact_lp_solver_with_duals"
CASES_DIR = C051_DIR / "judge_packet" / "cases"
MUTATIONS_DIR = C051_DIR / "judge_packet" / "hostile_mutations"


def _load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def test_c051_pfp_reference_solver_and_checkers(tmp_path: Path) -> None:
    """Verifies C051 reference solver and judge packet checkers under native PFP harness."""
    db_path = tmp_path / "pilots.db"
    store = SqlitePilotStore(db_path)

    checkers = [("exact", exact_check), ("independent", indep_check)]

    # 1. Test standard C051 judge cases
    case_files = sorted(CASES_DIR.glob("*.json"))[:12]
    assert len(case_files) == 12

    for case_file in case_files:
        case = _load_json(case_file)
        solution = c051_solve(case)

        # Run dual checkers
        exact_ok, exact_msg = exact_check(case, solution)
        assert exact_ok is True, f"Exact checker failed on {case['case_id']}: {exact_msg}"

        indep_ok, indep_msg = indep_check(case, solution)
        assert indep_ok is True, f"Independent checker failed on {case['case_id']}: {indep_msg}"

        status = solution.get("status", "SOLVED")

        # Record run in SQLite
        record = PilotRunRecord(
            run_id=f"pfp_{case['case_id']}",
            challenge_id="C051",
            harness="PFP",
            model_id="reference_solver_v1",
            case_id=case["case_id"],
            outcome=status,
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
    mut_files = sorted(MUTATIONS_DIR.glob("*.json"))[:5]
    for mut_file in mut_files:
        mut_data = _load_json(mut_file)
        case = mut_data.get("case", {})
        cand = mut_data.get("corrupted_result", {})
        if case and cand:
            exact_ok, _ = exact_check(case, cand)
            indep_ok, _ = indep_check(case, cand)
            assert not (exact_ok and indep_ok), f"Hostile mutation unexpectedly accepted: {mut_file}"

    # 3. Verify SQLite persistence and replay
    pfp_runs = store.list_runs(challenge_id="C051", harness="PFP")
    assert len(pfp_runs) == len(case_files)

    for run in pfp_runs:
        replay = store.replay_run(run.run_id, checkers)
        assert replay["all_passed"] is True
        assert replay["original_outcome"] in ("SOLVED", "OUT_OF_SCOPE")


def test_concurrent_dual_harness_unified_sqlite_replay(tmp_path: Path) -> None:
    """Verifies that runs from both PFP and second harnesses stored in SQLite can be replayed concurrently."""
    db_path = tmp_path / "unified_pilots.db"
    store = SqlitePilotStore(db_path)
    checkers = [("exact", exact_check), ("independent", indep_check)]

    target_cases = [_load_json(p) for p in sorted(CASES_DIR.glob("*.json"))[:3]]

    # 1. Store synthetic runs from both harnesses
    for idx, case in enumerate(target_cases):
        ans = c051_solve(case)
        # PFP record
        pfp_rec = PilotRunRecord(
            run_id=f"pfp_run_{idx}",
            challenge_id="C051",
            harness="PFP",
            model_id="ref_solver",
            case_id=case["case_id"],
            outcome="SOLVED",
            input_data=case,
            output_data=ans,
            checkers=[],
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            cost_usd=0.0,
        )
        store.record_run(pfp_rec)

        # Second-harness record
        adversary_rec = PilotRunRecord(
            run_id=f"adversary_run_{idx}",
            challenge_id="C051",
            harness="ADVERSARY",
            model_id="synthetic-model",
            case_id=case["case_id"],
            outcome="SOLVED",
            input_data=case,
            output_data=ans,
            checkers=[],
            usage={"prompt_tokens": 150, "completion_tokens": 60},
            cost_usd=0.00042,
        )
        store.record_run(adversary_rec)

    all_runs = store.list_runs(challenge_id="C051")
    assert len(all_runs) == 6

    # 2. Replay all runs concurrently across multiple threads
    def replay_worker(run_id: str) -> dict[str, Any]:
        return store.replay_run(run_id, checkers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(replay_worker, r.run_id): r.run_id for r in all_runs}
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 6
    for res in results:
        assert res["all_passed"] is True
        assert len(res["replayed_checkers"]) == 2
        for chk in res["replayed_checkers"]:
            assert chk["ok"] is True
