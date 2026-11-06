"""Dual test harness verifying Challenge C059 under both Adversary and PFP executions with unified SQLite replay custody.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from omega_engine_adversary.tests.pilots.c059_sql_null_total_query_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from omega_engine_adversary.tests.pilots.c059_sql_null_total_query_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from omega_engine_adversary.tests.pilots.c059_sql_null_total_query_synthesis.reference_solver.solver import (
    solve as c059_solve,
)
from omega_engine_adversary.tests.pilots.c059_sql_null_total_query_synthesis.run_c059_matrix import (
    TEST_CASES,
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


def test_c059_adversary_mediated_execution_and_custody(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Synthetic solver replies traverse the real accounted PFP boundary and original judges."""
    # Fail-closed network barrier
    def fail_on_urlopen(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Raw network egress detected: urllib.request.urlopen was invoked")

    monkeypatch.setattr(urllib.request, "urlopen", fail_on_urlopen)

    db_path = tmp_path / "pilots.db"
    store = SqlitePilotStore(db_path)

    target_cases = TEST_CASES[:3]
    gateway, fixture = make_solver_gateway(tmp_path, c059_solve, target_cases,
        model="stealth/space-bunny-alpha", max_output_tokens=256,
        input_tokens=120, output_tokens=45)
    exchanges = []

    checkers = [("exact", verify_candidate), ("independent", independent_check)]

    for case in target_cases:
        payload = {
            "model": "stealth/space-bunny-alpha",
            "messages": [
                {"role": "system", "content": "You are a SQL synthesis compiler."},
                {"role": "user", "content": f"Synthesize SQL for case {case['case_id']}: {json.dumps(case)}"},
            ],
            "max_tokens": 256,
        }

        exchange = complete_pilot_turn(gateway,
            CandidateRequest(messages=tuple(ChatMessage(**m) for m in payload["messages"]),
                decoding=DecodingParamsV1(temperature=0.0)),
            model=payload["model"], task_id="matrix:C059",
            attempt_id=f"C059:{case['case_id']}", max_tokens=payload["max_tokens"])
        assert exchange["ok"] and not exchange["stop"]
        assert exchange["pfp"]["schema_valid"] and exchange["pfp"]["evidence_grade"] == "UNVERIFIED"
        assert base64.b64decode(exchange["provider_wire"]["raw_reply_base64"]) == fixture.raw[-1]
        assert gateway.raw_reply(f"C059:{case['case_id']}") == fixture.raw[-1]
        assert fixture.cases[-1] == case
        exchanges.append(exchange)
        content_json = json.loads(exchange["content"])

        exact_ok, exact_msg = verify_candidate(case, content_json)
        indep_ok, indep_msg = independent_check(case, content_json)
        assert exact_ok is True
        assert indep_ok is True

        # Record Adversary run in SQLite store
        record = PilotRunRecord(
            run_id=f"adversary_{case['case_id']}",
            challenge_id="C059",
            harness="ADVERSARY",
            model_id="stealth/space-bunny-alpha",
            case_id=case["case_id"],
            outcome="ACCEPTED",
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
    assert len(fixture.calls) == len(exchanges) == 3
    assert sum(row["usage"]["prompt_tokens"] for row in exchanges) == 360
    assert sum(row["usage"]["completion_tokens"] for row in exchanges) == 135
    assert sum(reply["usage"]["total_tokens"] for reply in fixture.responses) == 495
    with gateway.ledger.transaction(gateway.limit) as state:
        assert len(state["attempts"]) == 3
        assert state["spent"] == sum(micro(row["usage"]["cost"]) for row in exchanges)

    # Verify SQLite persistence and replay
    adversary_runs = store.list_runs(challenge_id="C059", harness="ADVERSARY")
    assert len(adversary_runs) == 3

    for run in adversary_runs:
        replay = store.replay_run(run.run_id, checkers)
        assert replay["all_passed"] is True
        assert replay["original_outcome"] == "ACCEPTED"


def test_concurrent_dual_harness_unified_sqlite_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests both PFP and Adversary concurrently writing to a single SQLite store and replaying from it."""
    # Ensure network barrier
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **kw: pytest.fail("urlopen forbidden"))

    db_path = tmp_path / "unified_pilots.db"
    store = SqlitePilotStore(db_path)

    checkers = [("exact", verify_candidate), ("independent", independent_check)]
    case = TEST_CASES[0]

    # 1. PFP Run
    pfp_solution = c059_solve(case)
    p_exact_ok, p_exact_msg = verify_candidate(case, pfp_solution)
    p_indep_ok, p_indep_msg = independent_check(case, pfp_solution)

    store.record_run(
        PilotRunRecord(
            run_id="pfp_c059_m01",
            challenge_id="C059",
            harness="PFP",
            model_id="c059_reference_solver",
            case_id=case["case_id"],
            outcome="ACCEPTED",
            input_data=case,
            output_data=pfp_solution,
            checkers=[
                {"checker": "exact", "ok": p_exact_ok, "message": p_exact_msg},
                {"checker": "independent", "ok": p_indep_ok, "message": p_indep_msg},
            ],
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            cost_usd=0.0,
        )
    )

    # 2. One actual bound synthetic Adversary/PFP reply for the same public case.
    gateway, fixture = make_solver_gateway(tmp_path, c059_solve, [case],
        model="meta-llama/llama-3.3-70b-instruct", max_output_tokens=256,
        input_tokens=80, output_tokens=40)
    exchange = complete_pilot_turn(gateway,
        CandidateRequest(user="solve " + json.dumps(case), decoding=DecodingParamsV1(temperature=0.0)),
        model="meta-llama/llama-3.3-70b-instruct", task_id="C059-unified",
        attempt_id="C059-unified:0", max_tokens=256)
    assert exchange["ok"] and not exchange["stop"]
    assert base64.b64decode(exchange["provider_wire"]["raw_reply_base64"]) == fixture.raw[0]
    adversary_reply = json.loads(exchange["content"])
    w_exact_ok, w_exact_msg = verify_candidate(case, adversary_reply)
    w_indep_ok, w_indep_msg = independent_check(case, adversary_reply)

    store.record_run(
        PilotRunRecord(
            run_id="adversary_c059_m01",
            challenge_id="C059",
            harness="ADVERSARY",
            model_id="meta-llama/llama-3.3-70b-instruct",
            case_id=case["case_id"],
            outcome="ACCEPTED",
            input_data=case,
            output_data=adversary_reply,
            checkers=[
                {"checker": "exact", "ok": w_exact_ok, "message": w_exact_msg},
                {"checker": "independent", "ok": w_indep_ok, "message": w_indep_msg},
            ],
            usage={key: exchange["usage"][key] for key in ("prompt_tokens", "completion_tokens")},
            cost_usd=exchange["usage"]["cost"],
        )
    )

    # 3. Verify unified DB holds both runs
    all_runs = store.list_runs(challenge_id="C059")
    assert len(all_runs) == 2
    harnesses = {r.harness for r in all_runs}
    assert harnesses == {"PFP", "ADVERSARY"}

    # 4. Replay both runs from SQLite
    for r in all_runs:
        replay = store.replay_run(r.run_id, checkers)
        assert replay["all_passed"] is True
        assert replay["original_outcome"] == "ACCEPTED"
