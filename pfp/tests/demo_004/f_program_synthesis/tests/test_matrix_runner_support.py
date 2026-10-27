"""Shared matrix-runner support: explicit configuration, custody and outcome taxonomy.

Counterexamples from the 2026-09-28 audit that these tests pin down:

- provider errors were scored as wrong answers (C051 m07, C056 m06);
- replies were kept only as parsed JSON or a 200-character excerpt;
- a JSON-array reply crashed the C054 checker and aborted the sweep;
- runners read ``.env`` files and overwrote retained results.

No test here opens a network connection: every exchange uses a fake transport.
"""

from __future__ import annotations

import json
import urllib.error

import pytest
from pfp.infrastructure import synthesis_matrix as mrs


def _ok_body(content: str, **extra) -> str:
    return json.dumps(
        {
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 7, "completion_tokens_details": {"reasoning_tokens": 0}},
            **extra,
        }
    )


def _transport(status: int, body: str):
    def send(url, headers, payload, timeout):
        return status, body

    return send


def _accept_all(case, answer):
    return True, "OK"


def _dict_only(case, answer):
    if not isinstance(answer, dict):
        return False, "ANSWER_NOT_OBJECT"
    return answer.get("case_id") == case["case_id"], "CASE_ID"


CASE = {
    "case_id": "c999_m01_hidden_verdict_infeasible",
    "x": 1,
    "type": "INFEASIBLE",
    "expected_status": "UNKNOWN",
}


def test_missing_api_key_is_a_typed_refusal_and_no_dotenv_is_read():
    with pytest.raises(mrs.RunnerRefusal) as info:
        mrs.require_api_key({})
    assert info.value.code == "CONFIGURATION_MISSING"
    with pytest.raises(mrs.RunnerRefusal):
        mrs.require_api_key({mrs.API_KEY_ENV: "   "})
    source = mrs.__file__ and open(mrs.__file__, encoding="utf-8").read()
    assert "load_dotenv" not in source and "find_dotenv" not in source


def test_prompt_view_uses_opaque_token_and_drops_answer_bearing_fields():
    view = mrs.prompt_view(CASE, "case_01")
    assert view == {"case_id": "case_01", "x": 1}
    prompt = mrs.build_user_prompt("Case input:", CASE, "case_01")
    assert CASE["case_id"] not in prompt and "INFEASIBLE" not in prompt and "UNKNOWN" not in prompt
    with pytest.raises(mrs.RunnerRefusal) as info:
        mrs.build_user_prompt(f"Solve {CASE['case_id']}", CASE, "case_01")
    assert info.value.code == "PROMPT_LEAK"
    with pytest.raises(mrs.RunnerRefusal):
        mrs.build_user_prompt("Output only RFC 8785 JSON.", CASE, "case_01")


@pytest.mark.parametrize(
    "transport",
    [
        _transport(200, json.dumps({"error": {"code": 429, "message": "rate limited"}})),
        _transport(502, "bad gateway"),
        _transport(200, "<html>not json</html>"),
        _transport(200, json.dumps({"choices": []})),
    ],
)
def test_provider_errors_are_infra_errors_never_wrong_answers(transport):
    exchange = mrs.call_model(
        "k", "m", "sys", "user", max_tokens=16, title="t", transport=transport
    )
    record = mrs.score_exchange(CASE, "case_01", exchange, (("any", _accept_all),))
    assert record["outcome"] == mrs.OUTCOME_INFRA_ERROR
    assert mrs.summarize([record])["scored"] == 0


def test_transport_exceptions_are_infra_errors():
    def raising(url, headers, payload, timeout):
        raise urllib.error.URLError("connection reset")

    exchange = mrs.call_model("k", "m", "sys", "user", max_tokens=16, title="t", transport=raising)
    assert exchange.ok is False and "URLError" in exchange.error
    assert mrs.score_exchange(CASE, "case_01", exchange, ())["outcome"] == mrs.OUTCOME_INFRA_ERROR


def test_full_raw_text_is_kept_not_an_excerpt():
    long_text = "not json " * 100
    exchange = mrs.call_model(
        "k",
        "m",
        "sys",
        "user",
        max_tokens=16,
        title="t",
        transport=_transport(200, _ok_body(long_text)),
    )
    record = mrs.score_exchange(CASE, "case_01", exchange, (("any", _accept_all),))
    assert record["outcome"] == mrs.OUTCOME_REJECTED
    assert record["content"] == long_text and len(record["content"]) > 200
    assert long_text.strip() in json.loads(record["raw_body"])["choices"][0]["message"]["content"]
    assert "Authorization" not in json.dumps(record["request"])


def test_crashing_checker_is_a_checker_defect_and_the_token_is_rebound():
    def crashing(case, answer):
        return answer["rank_rows"][0]  # a JSON array reply makes this raise TypeError

    exchange = mrs.call_model(
        "k",
        "m",
        "sys",
        "user",
        max_tokens=16,
        title="t",
        transport=_transport(200, _ok_body("[1, 2]")),
    )
    record = mrs.score_exchange(
        CASE, "case_01", exchange, (("crashing", crashing), ("dict_only", _dict_only))
    )
    assert record["outcome"] == mrs.OUTCOME_CHECKER_DEFECT
    assert record["checkers"][1] == {
        "checker": "dict_only",
        "ok": False,
        "message": "ANSWER_NOT_OBJECT",
    }

    reply = json.dumps({"case_id": "case_01", "status": "SOLVED"})
    exchange = mrs.call_model(
        "k",
        "m",
        "sys",
        "user",
        max_tokens=16,
        title="t",
        transport=_transport(200, _ok_body(reply)),
    )
    assert (
        mrs.score_exchange(CASE, "case_01", exchange, (("dict_only", _dict_only),))["outcome"]
        == mrs.OUTCOME_ACCEPTED
    )


def test_run_matrix_survives_checker_defects_and_refuses_to_overwrite(tmp_path):
    calls = []

    def fake(url, headers, payload, timeout):
        calls.append(payload)
        return 200, _ok_body("[]" if len(calls) == 1 else json.dumps({"case_id": "case_02"}))

    def crash_on_list(case, answer):
        return answer.get("case_id") == case["case_id"], "CASE_ID"

    spec = mrs.MatrixSpec(
        challenge="CTEST",
        system_prompt="Reply with JSON.",
        instruction="Case input:",
        cases=[{"case_id": "secret_a", "x": 1}, {"case_id": "secret_b", "x": 2}],
        checkers=(("crash_on_list", crash_on_list),),
        models=[{"id": "vendor/model-a"}],
    )
    out = tmp_path / "run"
    summary = mrs.run_matrix(spec, out, "k", transport=fake, pause_s=0)
    counts = summary["models"]["vendor/model-a"]["counts"]
    assert counts[mrs.OUTCOME_CHECKER_DEFECT] == 1 and counts[mrs.OUTCOME_ACCEPTED] == 1
    lines = (out / "records_vendor_model_a.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all("secret_" not in m["content"] for p in calls for m in p["messages"])
    with pytest.raises(mrs.RunnerRefusal) as info:
        mrs.run_matrix(spec, out, "k", transport=fake, pause_s=0)
    assert info.value.code == "OUTPUT_DIR_EXISTS"


def test_truncation_is_recorded():
    body = json.dumps(
        {"choices": [{"message": {"content": "{"}, "finish_reason": "length"}], "usage": {}}
    )
    exchange = mrs.call_model(
        "k", "m", "sys", "user", max_tokens=16, title="t", transport=_transport(200, body)
    )
    record = mrs.score_exchange(CASE, "case_01", exchange, ())
    assert record["truncated"] is True and record["outcome"] == mrs.OUTCOME_REJECTED


def test_warranted_refusals_are_counted_apart_from_constructive_solutions():
    """Review of 2026-09-29: accepted refusals must not be reported as solutions."""

    def accept_code_proof(case, answer):
        if answer.get("status") == "UNKNOWN":
            return answer.get("code") == "PROOF", "refusal checked"
        return answer.get("status") == "SOLVED", "solution checked"

    replies = [
        {"case_id": "case_01", "status": "SOLVED"},
        {"case_id": "case_01", "status": "UNKNOWN", "code": "PROOF"},
        {"case_id": "case_01", "status": "UNKNOWN", "code": "NO_NETWORK_FOUND"},
        {"case_id": "case_01", "status": "BROKEN"},
    ]
    records = []
    for reply in replies:
        exchange = mrs.call_model(
            "k",
            "m",
            "sys",
            "user",
            max_tokens=16,
            title="t",
            transport=_transport(200, _ok_body(json.dumps(reply))),
        )
        records.append(
            mrs.score_exchange(CASE, "case_01", exchange, (("proof", accept_code_proof),))
        )
    assert [r["outcome"] for r in records] == [
        mrs.OUTCOME_ACCEPTED,
        mrs.OUTCOME_WARRANTED_REFUSAL,
        mrs.OUTCOME_UNWARRANTED_REFUSAL,
        mrs.OUTCOME_REJECTED,
    ]
    summary = mrs.summarize(records)
    assert (summary["accepted"], summary["warranted_refusals"], summary["scored"]) == (1, 1, 4)
