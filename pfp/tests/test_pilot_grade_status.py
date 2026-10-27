import json

import pytest

from pfp.infrastructure.pilot_runner import get_ground_truth, grade


def test_answerable_refusal_cannot_be_accepted():
    rows = grade([dict(request_id="p_req_0", raw_reply=json.dumps(
        dict(answer=3, status="REFUSED")))], "p", "linear_algebra")["results"]
    assert rows[0]["status"] == "REFUSED"


def test_unknown_reply_id_is_an_explicit_refusal():
    with pytest.raises(ValueError, match="UNKNOWN_REQUEST_ID"):
        grade([dict(request_id="p_unknown", raw_reply='{"answer":3}')], "p", "linear_algebra")


def test_witnessed_legitimate_refusal_still_accepts():
    truth = get_ground_truth("refusal", 1)
    replies = [dict(request_id="p_" + key, raw_reply=json.dumps(dict(
        answer=None, status="REFUSED", witness=dict(remaining=row["remaining"]))))
        for key, row in truth.items() if row["expected"] is None]
    assert grade(replies, "p", "refusal")["results"][0]["status"] == "ACCEPTED"
