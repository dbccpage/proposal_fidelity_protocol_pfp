"""Dual test harness verifying Challenge C051 under both Adversary and PFP executions with unified SQLite replay custody.

AuthorityEffect: None.
"""

from __future__ import annotations

import concurrent.futures
import json
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from omega_engine_adversary.tests.pilots.c051_exact_lp_solver_with_duals.judge_packet.exact_checker import (
    check_solution as exact_check,
)
from omega_engine_adversary.tests.pilots.c051_exact_lp_solver_with_duals.judge_packet.independent_checker import (
    check_solution as indep_check,
)
from omega_engine_adversary.tests.pilots.c051_exact_lp_solver_with_duals.reference_solver.solver import (
    solve as c051_solve,
)
from omega_engine_adversary.tests.pilots.sqlite_pilot_store import (
    PilotRunRecord,
    SqlitePilotStore,
)
import base64
from omega_engine_pfp.infrastructure.pilot_matrix import complete_pilot_turn
from omega_engine_pfp.infrastructure.adapters.pfp_campaign import micro
from omega_engine_pfp.tests.matrix_fixture import make_solver_gateway
from omega_engine_adversary.domain.providers.types import CandidateRequest, ChatMessage, DecodingParamsV1

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


def test_c051_adversary_mediated_execution_and_custody(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Synthetic solver replies traverse the real accounted PFP boundary and original judges."""
    # Fail-closed network barrier
    def fail_on_urlopen(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Raw network egress detected: urllib.request.urlopen was invoked")

    monkeypatch.setattr(urllib.request, "urlopen", fail_on_urlopen)

    db_path = tmp_path / "pilots.db"
    store = SqlitePilotStore(db_path)

    target_cases = [_load_json(p) for p in sorted(CASES_DIR.glob("*.json"))[:4]]
    gateway, fixture = make_solver_gateway(tmp_path, c051_solve, target_cases,
        model="stealth/space-bunny-alpha", max_output_tokens=256,
        input_tokens=150, output_tokens=60)
    exchanges = []

    checkers = [("exact", exact_check), ("independent", indep_check)]

    for case in target_cases:
        payload = {
            "model": "stealth/space-bunny-alpha",
            "messages": [
                {"role": "system", "content": "You are an exact rational LP solver."},
                {"role": "user", "content": f"Solve LP case {case['case_id']}: {json.dumps(case)}"},
            ],
            "max_tokens": 256,
        }

        exchange = complete_pilot_turn(gateway,
            CandidateRequest(messages=tuple(ChatMessage(**m) for m in payload["messages"]),
                decoding=DecodingParamsV1(temperature=0.0)),
            model=payload["model"], task_id="matrix:C051",
            attempt_id=f"C051:{case['case_id']}", max_tokens=payload["max_tokens"])
        assert exchange["ok"] and not exchange["stop"]
        assert exchange["pfp"]["schema_valid"] and exchange["pfp"]["evidence_grade"] == "UNVERIFIED"
        assert base64.b64decode(exchange["provider_wire"]["raw_reply_base64"]) == fixture.raw[-1]
        assert gateway.raw_reply(f"C051:{case['case_id']}") == fixture.raw[-1]
        assert fixture.cases[-1] == case
        exchanges.append(exchange)
        content_json = json.loads(exchange["content"])

        exact_ok, exact_msg = exact_check(case, content_json)
        indep_ok, indep_msg = indep_check(case, content_json)
        assert exact_ok is True
        assert indep_ok is True

        # Record Adversary run in SQLite store
        record = PilotRunRecord(
            run_id=f"adversary_{case['case_id']}",
            challenge_id="C051",
            harness="ADVERSARY",
            model_id="stealth/space-bunny-alpha",
            case_id=case["case_id"],
            outcome="SOLVED",
            input_data=case,
            output_data=content_json,
            checkers=[
                {"checker": "exact", "ok": exact_ok, "message": exact_msg},
                {"checker": "independent", "ok": indep_ok, "message": indep_msg},
            ],
            usage={key: exchange["usage"][key] for key in ("prompt_tokens", "completion_tokens")},
            cost_usd=exchange["usage"]["cost"],
        )
        store.record_run(record)

    # Actual synthetic response usage/cost and the one existing ledger agree.
    assert len(fixture.calls) == len(exchanges) == 4
    assert sum(row["usage"]["prompt_tokens"] for row in exchanges) == 600
    assert sum(row["usage"]["completion_tokens"] for row in exchanges) == 240
    assert sum(reply["usage"]["total_tokens"] for reply in fixture.responses) == 840
    with gateway.ledger.transaction(gateway.limit) as state:
        assert len(state["attempts"]) == 4
        assert state["spent"] == sum(micro(row["usage"]["cost"]) for row in exchanges)

    # Verify SQLite persistence and replay
    adversary_runs = store.list_runs(challenge_id="C051", harness="ADVERSARY")
    assert len(adversary_runs) == 4

    for run in adversary_runs:
        replay = store.replay_run(run.run_id, checkers)
        assert replay["all_passed"] is True
        assert replay["original_outcome"] == "SOLVED"


def test_concurrent_dual_harness_unified_sqlite_replay(tmp_path: Path) -> None:
    """Verifies that runs from both PFP and Adversary harnesses stored in SQLite can be replayed concurrently."""
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

        # Adversary record
        adversary_rec = PilotRunRecord(
            run_id=f"adversary_run_{idx}",
            challenge_id="C051",
            harness="ADVERSARY",
            model_id="stealth/space-bunny-alpha",
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
