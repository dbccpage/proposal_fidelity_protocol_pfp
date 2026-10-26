import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from fractions import Fraction

import pytest
from educational_governor import EducationalHostGovernor


def board():
    return EducationalHostGovernor(
        [0, 1, 2], ["0->1", "1->2", "2->0"], {"0->1": 2, "1->2": 1, "2->0": 3}
    )


@pytest.mark.parametrize("value", [True, 0.5, "1/0", "not rational", None])
def test_invalid_cut_is_atomic(value):
    host = board()
    before = dict(host.claims)
    receipt = host.execute_move(
        {"move_type": "CUT", "payload": {"proposed_claims": {"0->1": 0, "1->2": value}}}
    )
    assert receipt["decision"] == "REFUSED_MALFORMED_SYNTAX"
    assert host.claims == before
    assert host.fuel == 9
    assert host.history == []


@pytest.mark.parametrize(
    "proposal",
    [
        None,
        [],
        {"move_type": "CUT", "payload": []},
        {"move_type": "ASSERT", "payload": {"relation": []}},
    ],
)
def test_malformed_move_refuses_without_mutation(proposal):
    host = board()
    assert host.execute_move(proposal)["decision"] == "REFUSED_MALFORMED_SYNTAX"
    assert host.compute_total_defect() == 6


def test_retract_restores_checkpoint_and_keeps_evidence_and_fuel():
    host = board()
    host.execute_move({"move_type": "ASSERT", "payload": {"relation": "annotation"}})
    host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": "-3"}}})
    assert host.compute_total_defect() == 0
    result = host.execute_move({"move_type": "RETRACT", "payload": {"target_step": 0}})
    assert result["decision"] == "ADMITTED"
    assert host.claims["2->0"] == Fraction(3)
    assert not host.invariants
    assert [event["move"] for event in host.history] == ["ASSERT", "CUT", "RETRACT"]
    assert host.fuel == 7


def test_missing_checkpoint_refused_and_receipt_scoped():
    host = board()
    assert (
        host.execute_move({"move_type": "RETRACT", "payload": {"target_step": True}})["decision"]
        == "REFUSED_UNKNOWN_CHECKPOINT"
    )
    host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -3}}})
    receipt = host.execute_move({"move_type": "VERIFY"})["receipt"]
    assert receipt["scope"] == "educational-directed-triangle-circulation-only"
    assert receipt["native_host"] is False


def test_unsupported_board_and_noninteger_fuel_refused():
    with pytest.raises(ValueError):
        EducationalHostGovernor([0, 1], ["0->1"], {"0->1": 1})
    with pytest.raises(ValueError):
        EducationalHostGovernor(
            [0, 1, 2], ["0->1", "1->2", "2->0"], {"0->1": 2, "1->2": 1, "2->0": 3}, fuel=True
        )
