"""Recount the retained proposer-adversary run discussed in Section 4.1 of Paper 009.

The trace and receipt are byte-identical copies of the retained Paper 001
records, bundled here for a standalone recount. No model or checker is rerun.
"""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "docs" / "historical_evidence"
TRACE = RESULTS / "demo2_r7_adversarial_debate_1790210039.jsonl"
RECEIPT = RESULTS / "demo2_r7_adversarial_debate_receipt.json"
TRACE_SHA256 = "329e29228b3278dc9172bc318d82c38876107175a64c834c386e60d98bd509d7"
RECEIPT_SHA256 = "41256258279dd25c8af2323c6c5cc115293104bc09cfe3958c793d80e5cb4856"


def _rows():
    data = TRACE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == TRACE_SHA256
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def _receipt():
    data = RECEIPT.read_bytes()
    assert hashlib.sha256(data).hexdigest() == RECEIPT_SHA256
    return json.loads(data)


def test_trace_covers_two_lattices_at_five_values():
    rows = _rows()
    conditions = {(row["lattice_key"], row["u_val"]) for row in rows}
    expected = {
        (lattice, value)
        for lattice in ("c5_pentagon", "kagome_cluster")
        for value in (-4.0, -2.0, 0.0, 2.0, 4.0)
    }
    assert len(rows) == 10
    assert conditions == expected


def test_confusion_counts():
    counts = Counter(
        (row["proposer_hallucination"], row["adversary_critique"]["adversary_verdict"])
        for row in _rows()
    )
    assert counts == Counter(
        {(True, "CHALLENGE"): 6, (False, "CHALLENGE"): 2, (False, "CONCUR"): 2}
    )
    assert counts[(True, "CONCUR")] == 0


def test_labels_follow_the_checker_status():
    for row in _rows():
        move = row["proposer_move"]["move_type"]
        refused = row["proposer_status"].startswith("Refused")
        assert type(row["proposer_hallucination"]) is bool
        assert row["proposer_hallucination"] is refused
        assert move == ("VERIFY_SIGN_FREE" if refused else "OPEN_SIGN_OBSTRUCTION")


def test_challenges_of_sound_labels_keep_the_same_conclusion():
    challenged = [
        row
        for row in _rows()
        if row["proposer_hallucination"] is False
        and row["adversary_critique"]["adversary_verdict"] == "CHALLENGE"
    ]
    assert len(challenged) == 2
    for row in challenged:
        assert row["proposer_move"]["move_type"] == "OPEN_SIGN_OBSTRUCTION"
        assert row["adversary_critique"]["counter_move"] == "OPEN_SIGN_OBSTRUCTION"


def test_caught_field_is_true_in_every_record():
    rows = _rows()
    assert all(row["adversary_caught_am"] is True for row in rows)
    concurrences = [
        row for row in rows if row["adversary_critique"]["adversary_verdict"] == "CONCUR"
    ]
    assert len(concurrences) == 2
    assert all(row["adversary_caught_am"] is True for row in concurrences)


def test_every_trial_ends_in_the_same_terminal_state():
    assert {row["terminal_state"] for row in _rows()} == {"OpenSignObstruction"}


def test_trace_records_no_model_identifiers():
    assert not any("model" in key for row in _rows() for key in row)
    receipt = _receipt()
    assert receipt["reported_proposer_model"] == "meta-llama/llama-3.1-8b-instruct"
    assert receipt["reported_adversary_model"] == "deepseek/deepseek-chat"


def test_retained_replay_refuses_all_ten():
    receipt = _receipt()
    assert receipt["source_trace_sha256"] == TRACE_SHA256
    assert receipt["total_trials"] == 10
    assert (
        receipt["adversary_true_positives"],
        receipt["adversary_false_negatives"],
        receipt["adversary_false_positives"],
        receipt["adversary_true_negatives"],
    ) == (6, 0, 2, 2)
    assert len(receipt["trials"]) == 10
    assert not any(trial["current_replay_admitted"] for trial in receipt["trials"])
    obstruction_claims = [
        trial for trial in receipt["trials"] if trial["proposer_move"] == "OPEN_SIGN_OBSTRUCTION"
    ]
    assert len(obstruction_claims) == 4
    assert {trial["current_replay_status"] for trial in obstruction_claims} == {
        "Refused_UnverifiedObstruction"
    }
