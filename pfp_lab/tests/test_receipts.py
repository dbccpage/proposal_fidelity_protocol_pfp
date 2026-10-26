"""Receipts: digest binding, replay verification and tamper detection.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:receipts:v1
"""

from __future__ import annotations

import json

import pytest

from pfp_lab.core.admission import BudgetExceededError
from pfp_lab.core.contracts import CORE_VERSION, PACK_IDS, admit_json, get_pack
from pfp_lab.core.session import (
    RECEIPT_SCHEMA,
    ReceiptOut,
    build_receipt,
    canonical_json,
    receipt_digest,
    run_scenario,
    verify_receipt,
)


def worked_receipt() -> ReceiptOut:
    return build_receipt(run_scenario(get_pack("paper-005-worked-session")))


def test_canonical_json_is_sorted_and_compact() -> None:
    assert canonical_json({"b": 1, "a": ["x", None, True]}) == '{"a":["x",null,true],"b":1}'
    assert canonical_json({"é": "ü"}) == '{"é":"ü"}'
    with pytest.raises(ValueError):
        canonical_json({"x": float("nan")})


def test_receipt_fields_and_digest() -> None:
    receipt = worked_receipt()
    assert receipt.schema_id == RECEIPT_SCHEMA
    assert receipt.core_version == CORE_VERSION
    assert receipt.digest == receipt_digest(receipt)
    assert len(receipt.digest) == 64
    assert worked_receipt().digest == receipt.digest


@pytest.mark.parametrize("pack_id", list(PACK_IDS))
def test_every_pack_receipt_verifies_after_json_round_trip(pack_id: str) -> None:
    receipt = build_receipt(run_scenario(get_pack(pack_id)))
    text = receipt.model_dump_json(by_alias=True)
    reloaded = admit_json(ReceiptOut, text)
    report = verify_receipt(reloaded)
    assert (report.valid, report.problems, report.digest) == (True, (), receipt.digest)


def test_key_order_does_not_change_the_digest() -> None:
    receipt = worked_receipt()
    body = json.loads(receipt.model_dump_json(by_alias=True))
    reordered = json.dumps(dict(reversed(list(body.items()))))
    assert verify_receipt(admit_json(ReceiptOut, reordered)).valid


def test_forged_digest_is_detected() -> None:
    receipt = worked_receipt().model_copy(update={"digest": "f" * 64})
    report = verify_receipt(receipt)
    assert not report.valid
    assert report.problems[0].startswith("digest mismatch")
    assert report.digest == worked_receipt().digest


def test_edited_verdict_with_recomputed_digest_fails_replay() -> None:
    receipt = worked_receipt()
    forged_verdict = receipt.verdicts[3].model_copy(update={"admitted": True})
    verdicts = (*receipt.verdicts[:3], forged_verdict, *receipt.verdicts[4:])
    forged = receipt.model_copy(update={"verdicts": verdicts})
    forged = forged.model_copy(update={"digest": receipt_digest(forged)})
    report = verify_receipt(forged)
    assert report.problems == ("verdict 3 (step_004) differs from the replay",)


def test_dropped_verdict_and_edited_final_state_fail() -> None:
    receipt = worked_receipt()
    short = receipt.model_copy(update={"verdicts": receipt.verdicts[:-1]})
    short = short.model_copy(update={"digest": receipt_digest(short)})
    assert verify_receipt(short).problems == ("receipt has 7 verdicts; replay produced 8",)
    final = receipt.final.model_copy(update={"obstruction": "0"})
    edited = receipt.model_copy(update={"final": final})
    edited = edited.model_copy(update={"digest": receipt_digest(edited)})
    assert verify_receipt(edited).problems == ("final state differs from the replayed final state",)


def test_bad_receipt_json_is_refused() -> None:
    body = json.loads(worked_receipt().model_dump_json(by_alias=True))
    for key, value in (("digest", "XYZ"), ("schema", "other"), ("core_version", "x" * 40)):
        with pytest.raises(ValueError):
            admit_json(ReceiptOut, json.dumps({**body, key: value}))


def test_budget_failure_propagates_from_session() -> None:
    with pytest.raises(BudgetExceededError):
        run_scenario(get_pack("paper-005-worked-session"), budget=2)
