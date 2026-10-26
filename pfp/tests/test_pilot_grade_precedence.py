"""Finite public grading boundaries; caller evidence has AuthorityEffect: None."""

import json

import pytest

from omega_engine_pfp.infrastructure.pilot_runner import grade


@pytest.mark.parametrize(
    ("family", "payload", "expected_status"),
    [
        pytest.param(
            "linear_algebra", {"answer": 3, "status": "REFUSED"}, "REFUSED",
            id="correct-answer-refused",
        ),
        pytest.param(
            "linear_algebra", {"answer": 3, "status": "UNKNOWN"}, "MALFORMED",
            id="correct-answer-unknown-status",
        ),
        pytest.param(
            "linear_algebra", {"answer": 3, "status": "SOLVED"}, "ACCEPTED",
            id="correct-answer-solved",
        ),
        pytest.param(
            "linear_algebra", {"answer": 4, "status": "ACCEPTED"}, "WRONG_ANSWER",
            id="wrong-answer-accepted-status",
        ),
        pytest.param(
            "refusal", {"answer": None, "status": "REFUSED", "witness": {"remaining": [4, 2]}},
            "ACCEPTED", id="refusal-reordered-exact-witness",
        ),
        pytest.param(
            "refusal", {"answer": 3, "status": "UNKNOWN"}, "FALSE_CERTAINTY",
            id="false-certainty-before-unknown-status",
        ),
        pytest.param(
            "refusal", {"answer": 3, "status": "REFUSED"}, "FALSE_CERTAINTY",
            id="false-certainty-before-refused-status",
        ),
        pytest.param(
            "refusal", {"answer": None, "status": "REFUSED"}, "MALFORMED",
            id="refusal-missing-witness",
        ),
        pytest.param(
            "refusal",
            {"answer": None, "status": "REFUSED", "witness": {"remaining": [2, 4], "extra": 0}},
            "MALFORMED", id="refusal-extra-witness-key",
        ),
        pytest.param(
            "refusal", {"answer": None, "status": "REFUSED", "witness": {"remaining": [2, True]}},
            "MALFORMED", id="refusal-bool-witness",
        ),
        pytest.param(
            "refusal", {"answer": None, "status": "REFUSED", "witness": {"remaining": [2, 4.0]}},
            "MALFORMED", id="refusal-float-witness",
        ),
        pytest.param(
            "refusal", {"answer": None, "status": "ACCEPTED", "witness": {"remaining": [2, 4]}},
            "MALFORMED", id="refusal-accepted-status",
        ),
    ],
)
def test_public_status_precedence(family, payload, expected_status):
    raw = json.dumps(payload)
    result = grade([{"request_id": "p_req_0", "raw_reply": raw}], "p", family)
    assert result["results"][0] == {
        "request_id": "p_req_0",
        "status": expected_status,
        "raw_reply": raw,
        "answer": payload["answer"],
    }
    assert result["results"][1] == {
        "request_id": "p_req_1", "status": "NOT_RUN", "raw_reply": None,
    }


@pytest.mark.parametrize(
    ("edge_id", "expected_status"),
    [(1, "ACCEPTED"), (2, "ACCEPTED"), (0, "WRONG_ANSWER"), (4, "WRONG_ANSWER")],
    ids=["alternative-first-edge", "alternative-second-edge", "zero-edge", "past-last-edge"],
)
def test_public_triangle_repair_alternatives(edge_id, expected_status):
    # Every single edge removal breaks 1->2->3->1; edge IDs 0 and 4 do not exist.
    raw = json.dumps({"answer": edge_id})
    result = grade([{"request_id": "p_req_0", "raw_reply": raw}], "p", "graph_repair")
    assert result["results"][0] == {
        "request_id": "p_req_0", "status": expected_status, "raw_reply": raw, "answer": edge_id,
    }


@pytest.mark.parametrize("answer", [True, 3.0], ids=["bool-is-not-integer", "float-is-not-integer"])
def test_public_grade_rejects_noninteger_answer(answer):
    raw = json.dumps({"answer": answer})
    result = grade([{"request_id": "p_req_0", "raw_reply": raw}], "p", "linear_algebra")
    row = result["results"][0]
    assert set(row) == {"request_id", "status", "raw_reply", "detail"}
    assert row["request_id"] == "p_req_0"
    assert row["status"] == "MALFORMED"
    assert row["raw_reply"] == raw
    assert isinstance(row["detail"], str) and row["detail"]


def test_public_duplicate_id_precedes_malformed_parse():
    replies = [
        {"request_id": "p_req_0", "raw_reply": "not json"},
        {"request_id": "p_req_0", "raw_reply": "still not json"},
    ]
    with pytest.raises(ValueError, match="^Duplicate request_id: p_req_0$"):
        grade(replies, "p", "linear_algebra")


def test_public_unknown_ids_precede_malformed_parse_and_are_sorted():
    replies = [
        {"request_id": "p_z", "raw_reply": "not json"},
        {"request_id": "p_a", "raw_reply": "still not json"},
    ]
    with pytest.raises(ValueError, match="^UNKNOWN_REQUEST_ID: p_a, p_z$"):
        grade(replies, "p", "linear_algebra")


@pytest.mark.parametrize("raw", ['{"answer":1,"answer":2}', "not json"], ids=["duplicate-json-keys", "non-json"])
def test_public_malformed_raw_envelope_is_preserved(raw):
    result = grade([{"request_id": "p_req_0", "raw_reply": raw}], "p", "linear_algebra")
    row = result["results"][0]
    assert set(row) == {"request_id", "status", "raw_reply", "detail"}
    assert row["request_id"] == "p_req_0"
    assert row["status"] == "MALFORMED"
    assert row["raw_reply"] == raw
    assert isinstance(row["detail"], str) and row["detail"]
    assert result["results"][1] == {
        "request_id": "p_req_1", "status": "NOT_RUN", "raw_reply": None,
    }


def test_public_empty_input_retains_pending_unauthenticated_envelope():
    assert grade([], "p", "linear_algebra") == {
        "pilot_id": "p",
        "task_family": "linear_algebra",
        "results": [
            {"request_id": "p_req_0", "status": "NOT_RUN", "raw_reply": None},
            {"request_id": "p_req_1", "status": "NOT_RUN", "raw_reply": None},
        ],
        "live_trial": "PENDING",
        "evidence": "CALLER_SUPPLIED_UNAUTHENTICATED",
        "provider_calls": 0,
        "cost_microusd": 0,
    }
