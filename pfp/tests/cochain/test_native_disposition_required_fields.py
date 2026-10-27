"""Literal native-reply boundary controls; these do not execute native mathematics."""

import copy
import json
from fractions import Fraction

import pytest

from operations.domain.rop.result import Ok
from pfp.domain import cochain
from pfp.infrastructure.finite_qm_cochain_judge import NativeCochainJudge

REPLIES = {
    "ExactCoboundary": {
        "disposition": "ExactCoboundary", "potential": ["0", "1", "3"],
        "residual": ["0", "0", "0"], "phi1": "0", "gamma2": "0",
    },
    "ClosedNonExactClass": {
        "disposition": "ClosedNonExactClass", "cohomology_class": ["1", "1", "1"],
        "dual_witness": ["1", "1", "1"], "phi1": "3", "gamma2": "0",
    },
    "NonClosedEdgeData": {
        "disposition": "NonClosedEdgeData", "face_defect": ["3"], "phi1": "3", "gamma2": "3",
    },
}
REQUIRED_FIELDS = tuple(
    (variant, field)
    for variant, reply in REPLIES.items()
    for field in reply if field != "disposition"
)
VECTOR_FIELDS = (
    ("ExactCoboundary", "potential", "potential"),
    ("ExactCoboundary", "residual", "dual_witness"),
    ("ClosedNonExactClass", "cohomology_class", "cohomology_class_vec"),
    ("ClosedNonExactClass", "dual_witness", "dual_witness"),
    ("NonClosedEdgeData", "face_defect", "defect_vector"),
)
SCALAR_FIELDS = tuple((variant, field) for variant in REPLIES for field in ("phi1", "gamma2"))


class LiteralPort:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def evaluate_prompt_cochain(self, **kwargs):
        self.calls.append(kwargs)
        return Ok(self.reply)


def wire_complex():
    return {
        "c0_dim": 3, "c1_dim": 3, "c2_dim": 1,
        "d0": [["-1", "1", "0"], ["0", "-1", "1"], ["1", "0", "-1"]],
        "d1": [["1", "1", "1"]],
    }


def evaluate(reply):
    before = copy.deepcopy(reply)
    port = LiteralPort(reply)
    result = cochain.evaluate_prompt_cochain(
        complex=wire_complex(), cochain=["1", "2", "-3"],
        primal_potential=[99, 100, 102], dual_witness=[7, 8, 9], host=port,
    )
    assert len(port.calls) == 1
    assert reply == before
    return result


def assert_malformed(result, reply):
    assert isinstance(result, cochain.CochainRefusal)
    assert result.reason == "MALFORMED_NATIVE_REPLY"
    assert result.receipt is reply


@pytest.mark.parametrize("variant,field", REQUIRED_FIELDS, ids=["-".join(case) for case in REQUIRED_FIELDS])
def test_missing_native_field_does_not_use_details_or_candidates(variant, field):
    reply = copy.deepcopy(REPLIES[variant])
    original = copy.deepcopy(reply)
    del reply[field]
    reply["details"] = dict(original, provisional_phi1=3, defect_vector=["3"])
    result = evaluate({"result": reply})
    assert_malformed(result, reply)
    assert field in result.detail


@pytest.mark.parametrize("variant,field", REQUIRED_FIELDS, ids=["-".join(case) for case in REQUIRED_FIELDS])
def test_null_native_field_is_a_typed_refusal(variant, field):
    reply = copy.deepcopy(REPLIES[variant])
    reply[field] = None
    result = evaluate({"result": reply})
    assert_malformed(result, reply)
    assert field in result.detail


@pytest.mark.parametrize(
    "variant,field,attribute", VECTOR_FIELDS, ids=["-".join(case[:2]) for case in VECTOR_FIELDS],
)
@pytest.mark.parametrize("value", ["0", {"0": "0"}, [False], [0.5]], ids=["text", "mapping", "bool", "float"])
def test_malformed_native_vector_is_a_typed_refusal(variant, field, attribute, value):
    reply = copy.deepcopy(REPLIES[variant])
    reply[field] = value
    result = evaluate({"result": reply})
    assert_malformed(result, reply)
    assert field in result.detail
    assert not hasattr(result, attribute)


@pytest.mark.parametrize("variant,field", SCALAR_FIELDS, ids=["-".join(case) for case in SCALAR_FIELDS])
@pytest.mark.parametrize("value", [False, 0.5, "not-rational", "1/0"], ids=["bool", "float", "text", "zero-denominator"])
def test_malformed_native_scalar_is_a_typed_refusal(variant, field, value):
    reply = copy.deepcopy(REPLIES[variant])
    reply[field] = value
    result = evaluate({"result": reply})
    assert_malformed(result, reply)
    assert field in result.detail


@pytest.mark.parametrize("value", [0, "0"], ids=["integer", "wire-string"])
def test_explicit_nonclosed_phi1_zero_is_not_missing(value):
    reply = copy.deepcopy(REPLIES["NonClosedEdgeData"])
    reply["phi1"] = value
    result = evaluate({"result": reply})
    assert isinstance(result, cochain.NonClosedEdgeData)
    assert result.phi1 == Fraction(0)


@pytest.mark.parametrize(
    "variant,field,attribute", VECTOR_FIELDS, ids=["-".join(case[:2]) for case in VECTOR_FIELDS],
)
def test_explicit_empty_native_vector_does_not_use_candidates(variant, field, attribute):
    reply = copy.deepcopy(REPLIES[variant])
    reply[field] = []
    result = evaluate({"result": reply})
    assert not isinstance(result, cochain.CochainRefusal)
    assert getattr(result, attribute) == ()


@pytest.mark.parametrize("variant", tuple(REPLIES))
def test_native_variants_do_not_add_absent_output_fields(variant):
    reply = copy.deepcopy(REPLIES[variant])
    result = evaluate({"result": reply})
    assert result.receipt is reply
    assert result.phi1 == Fraction(reply["phi1"])
    assert result.gamma2 == Fraction(reply["gamma2"])
    if variant == "ExactCoboundary":
        assert isinstance(result, cochain.ExactCoboundary)
        assert result.potential == (Fraction(0), Fraction(1), Fraction(3))
        assert result.dual_witness == (Fraction(0),) * 3
        assert result.defect_vector == ()
    elif variant == "ClosedNonExactClass":
        assert isinstance(result, cochain.ClosedNonExactClass)
        assert result.potential == ()
        assert result.cohomology_class == (Fraction(1),) * 3
        assert result.dual_witness == (Fraction(1),) * 3
        assert result.defect_vector == ()
    else:
        assert isinstance(result, cochain.NonClosedEdgeData)
        assert result.defect_vector == (Fraction(3),)


def test_exact_legacy_reply_only_dual_alias_remains_supported():
    reply = copy.deepcopy(REPLIES["ExactCoboundary"])
    reply["dual_witness"] = reply.pop("residual")
    result = evaluate({"result": reply})
    assert isinstance(result, cochain.ExactCoboundary)
    assert result.dual_witness == (Fraction(0),) * 3


def test_present_invalid_residual_does_not_fall_through_reply_alias():
    reply = copy.deepcopy(REPLIES["ExactCoboundary"])
    reply.update(residual=None, dual_witness=["0", "0", "0"])
    result = evaluate({"result": reply})
    assert_malformed(result, reply)


def test_present_empty_residual_does_not_fall_through_reply_alias():
    reply = copy.deepcopy(REPLIES["ExactCoboundary"])
    reply.update(residual=[], dual_witness=["7", "8", "9"])
    result = evaluate({"result": reply})
    assert isinstance(result, cochain.ExactCoboundary)
    assert result.dual_witness == ()


@pytest.mark.parametrize("result", [None, [], "invalid"], ids=["null", "list", "text"])
def test_malformed_result_envelope_is_a_typed_refusal(result):
    reply = {"result": result}
    assert_malformed(evaluate(reply), reply)


def test_bare_exact_reply_is_native_check_unavailability_in_the_judge():
    port = LiteralPort({"result": {"disposition": "ExactCoboundary"}})
    case = {"prompt": json.dumps({"operad_slots": {"slot_m1_layer0_ambient_carrier": {
        "coefficient_ring": "Q", "public_input": {"complex": wire_complex(), "cochain": ["1", "2", "-3"]},
    }}})}
    answer = {
        "potential": [{"num": 0, "den": 1}, {"num": 1, "den": 1}, {"num": 3, "den": 1}],
        "dual_witness": [{"num": 0, "den": 1}] * 3,
        "phi1": {"num": 0, "den": 1}, "gamma2": {"num": 0, "den": 1},
    }
    judge = NativeCochainJudge(port)
    with pytest.raises(RuntimeError, match="NATIVE_CHECK_UNAVAILABLE:MALFORMED_NATIVE_REPLY"):
        judge(case, answer)
    assert judge.receipts == [port.reply["result"]]
    assert len(port.calls) == 1
