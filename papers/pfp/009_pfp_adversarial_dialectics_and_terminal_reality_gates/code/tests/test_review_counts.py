"""Positive and negative controls for the educational recount, not a model trial."""
import copy
import json
from fractions import Fraction
from pathlib import Path

import pytest

from review_counts import Counts, recount

ROOT = Path(__file__).resolve().parents[2]


def rows():
    path = ROOT / "docs/historical_evidence/demo2_r7_adversarial_debate_1790210039.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_exact_fractions_and_census():
    counts = recount(rows())
    assert counts == Counts(6, 0, 2, 2)
    assert counts.total == 10
    assert counts.rates() == {
        "challenge_among_refused": Fraction(1),
        "challenge_among_not_refused": Fraction(1, 2),
        "refused_among_challenges": Fraction(3, 4),
        "agreement_with_historical_labels": Fraction(4, 5),
    }


def test_constant_flag_does_not_control_counts():
    original = rows()
    changed = copy.deepcopy(original)
    for row in changed:
        row["adversary_caught_am"] = False
    assert recount(changed) == recount(original)


def test_one_changed_verdict_changes_the_recount():
    changed = copy.deepcopy(rows())
    refused = next(row for row in changed if row["proposer_hallucination"])
    refused["adversary_critique"]["adversary_verdict"] = "CONCUR"
    assert recount(changed) == Counts(5, 1, 2, 2)
    assert recount(changed).rates()["challenge_among_refused"] == Fraction(5, 6)


@pytest.mark.parametrize("label", [1, "false", None])
def test_non_boolean_labels_are_rejected(label):
    changed = rows()[:1]
    changed[0]["proposer_hallucination"] = label
    with pytest.raises(TypeError):
        recount(changed)


def test_disagreed_label_and_unknown_verdict_are_rejected():
    changed = rows()[:1]
    changed[0]["proposer_hallucination"] = not changed[0]["proposer_hallucination"]
    with pytest.raises(ValueError):
        recount(changed)
    changed = rows()[:1]
    changed[0]["adversary_critique"]["adversary_verdict"] = "QED"
    with pytest.raises(ValueError):
        recount(changed)


def test_empty_rows_do_not_become_perfect_detection():
    assert recount([]) == Counts()
    assert set(recount([]).rates().values()) == {None}


def test_gate_record_is_five_probes_in_four_families():
    path = ROOT / "docs/historical_evidence/adversary_gate_falsifiers.json"
    record = json.loads(path.read_text())
    assert record["audited_commit"] == "30609de2c3928238715375a9bac608256fa381d8"
    probes = record["falsifiers"]
    assert [row["id"] for row in probes] == ["F1", "F2a", "F2b", "F3", "F4"]
    assert len({row["defect"] for row in probes}) == 4
    assert probes[0]["is_authorized"] is True
    assert probes[0]["trace"]["cochain_after_act4"] == [0]
    assert probes[1]["candidate_survives"] is True
    assert probes[2]["candidate_survives"] is False
    assert probes[3]["observed"]["first_reference_is_sha256_of_run_key"] is True
    assert probes[4]["observed"]["step_E_payload"] == [{"status": "repaired"}]


def test_all_retained_record_digests_and_git_identities():
    import hashlib

    directory = ROOT / "docs/historical_evidence"
    provenance = json.loads((directory / "provenance.json").read_text())
    assert len(provenance["records"]) == 3
    for entry in provenance["records"]:
        data = (directory / entry["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        git_blob = b"blob " + str(len(data)).encode() + b"\0" + data
        assert hashlib.sha1(git_blob).hexdigest() == entry["git_blob_sha1"]
