"""C041 experiment harness: no invented answers, arm-scoped antibodies, INFRA_ERROR custody.

Counterexamples named by these tests:
- extract_json_answer turned any unparsable reply containing "by decide" into
  {"status": "SOLVED", "kind": "PROOF", "proof": "by decide"};
- M3 loaded every antibody ever written for a case, across runs, models and arms, into later
  prompts;
- a provider error raised and aborted the run (or was scored as a wrong answer), and
  load_dotenv() read a .env file at import.
No provider is called: ``call_openrouter`` is replaced by a local stub.
"""

from __future__ import annotations

import inspect
import json

import pytest
from pfp.infrastructure.formal_matrix import (
    ArmAntibodyStore,
)
from pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver import symbol_game_experiment as exp

CASE = {"case_id": "c041_pub_03", "prelude": "", "statement": "∀ b : Bool, (b && true) = b"}


def test_unparsable_reply_is_not_turned_into_a_proof() -> None:
    assert exp.extract_json_answer("I would close it by decide, or maybe by rfl.", "x") is None


def test_harness_reads_no_env_file_and_writes_nothing_at_import() -> None:
    source = inspect.getsource(exp)
    assert "load_dotenv" not in source
    assert '".env"' not in source
    assert "parents[4]" not in source
    assert "CEMETERY_DIR" not in source


def _reply(obj: dict) -> dict:
    body = json.dumps(obj)
    return {
        "ok": True,
        "content": body,
        "reasoning": "",
        "usage": {"prompt_tokens": 1},
        "elapsed": 0.0,
        "raw_body": body,
    }


def test_m3_injects_only_this_arms_antibodies(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake_call(_key, _model, messages, **_kw):
        seen.append(messages[-1]["content"])
        return _reply(
            {"case_id": CASE["case_id"], "status": "SOLVED", "kind": "LIFT", "proof": "by simp"}
        )

    monkeypatch.setattr(exp, "call_openrouter", fake_call)
    ArmAntibodyStore("other_arm").mint(CASE["case_id"], "foreign proof", "foreign diagnostic")
    store = ArmAntibodyStore("M3_RETRACTION_m")
    res = exp.run_experiment_on_lemma("k", CASE, "m", "M3_RETRACTION", store)
    assert res["verified"] is False
    assert [r["injected_antibody_ids"] for r in res["rounds"]] == [
        [],
        ["ab_M3_RETRACTION_m_c041_pub_03_1"],
        ["ab_M3_RETRACTION_m_c041_pub_03_1", "ab_M3_RETRACTION_m_c041_pub_03_2"],
    ]
    assert all("foreign" not in text for text in seen)


def test_refusal_reply_is_abstention_not_verified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        exp,
        "call_openrouter",
        lambda *_a, **_k: _reply(
            {"case_id": CASE["case_id"], "status": "UNKNOWN", "code": "SEARCH_LIMIT_REACHED"}
        ),
    )
    res = exp.run_experiment_on_lemma("k", CASE, "m", "M1_LOGITS")
    assert res["verified"] is False
    assert res["outcome"] == "ABSTAINED"


def test_provider_error_is_infra_error_with_full_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        exp,
        "call_openrouter",
        lambda *_a, **_k: {
            "ok": False,
            "outcome": "INFRA_ERROR",
            "error": "HTTP 503",
            "raw_body": "x" * 1000,
            "elapsed": 0.0,
        },
    )
    res = exp.run_experiment_on_lemma("k", CASE, "m", "M3_RETRACTION", ArmAntibodyStore("a"))
    assert res["outcome"] == "INFRA_ERROR"
    assert len(res["rounds"]) == 1
    assert res["rounds"][0]["raw_body"] == "x" * 1000


def test_parse_failure_keeps_full_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    text = "no json here, " * 50
    monkeypatch.setattr(
        exp,
        "call_openrouter",
        lambda *_a, **_k: {
            "ok": True,
            "content": text,
            "reasoning": "",
            "usage": {},
            "elapsed": 0.0,
            "raw_body": text,
        },
    )
    res = exp.run_experiment_on_lemma("k", CASE, "m", "M1_LOGITS")
    assert res["outcome"] == "PARSE_FAILURE"
    assert res["rounds"][0]["content"] == text
