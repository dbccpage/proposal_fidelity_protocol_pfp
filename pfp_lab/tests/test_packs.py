"""Built-in packs, with expected numbers taken from the Paper 005 guide.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:packs:v1
"""

from __future__ import annotations

import pytest

from pfp_lab.core.admission import ErrorCode, UnknownPackError
from pfp_lab.core.contracts import PACK_IDS, get_pack, list_packs
from pfp_lab.core.session import run_scenario


def test_catalog_lists_every_pack_in_order() -> None:
    summaries = list_packs()
    assert [item.pack_id for item in summaries] == list(PACK_IDS)
    assert summaries[0].pack_id == "paper-005-worked-session"
    assert summaries[0].moves == 8
    assert all(item.title for item in summaries)


def test_unknown_pack() -> None:
    with pytest.raises(UnknownPackError) as caught:
        get_pack("nope")
    assert caught.value.code is ErrorCode.UNKNOWN_PACK


def test_paper_005_worked_session_numbers() -> None:
    # Expected values are those printed by papers/005_pfp_practitioners_field_manual/code/play_demo.py
    # and stated in the guide: Phi_1 = 3 after ASSERT x3, the bad CUT is refused 3 -> 5, the repair
    # is ExactRepair 3 -> 0, VERIFY passes, RETRACT restores Phi_1 = 3.
    verdicts = run_scenario(get_pack("paper-005-worked-session")).verdicts
    bad, repair, verify, retract, after = verdicts[3:]
    assert (bad.admitted, bad.status.value, bad.defect_before, bad.defect_after) == (False, "DefectIncrease", "3", "5")
    assert (repair.status.value, repair.defect_before, repair.defect_after) == ("ExactRepair", "3", "0")
    assert verify.admitted
    assert retract.status.value == "Retracted"
    assert (after.admitted, after.details) == (False, "Primary obstruction Phi_1 is 3.")


def test_refusal_gallery_admits_only_its_one_assert() -> None:
    verdicts = run_scenario(get_pack("refusal-gallery")).verdicts
    assert [verdict.admitted for verdict in verdicts].count(True) == 1
    statuses = {verdict.status.value for verdict in verdicts if not verdict.admitted}
    assert statuses == {
        "InvariantViolation",
        "MoveViolation",
        "DefectIncrease",
        "CarrierViolation",
        "IncompleteProposal",
        "Refused",
        "VerificationFailed",
    }


def test_two_islands_repair() -> None:
    session = run_scenario(get_pack("two-islands"))
    assert session.verdicts[5].defect_before == "2"
    assert session.final.obstruction == "0"
    assert session.final.section["y"] == "-4/3"
