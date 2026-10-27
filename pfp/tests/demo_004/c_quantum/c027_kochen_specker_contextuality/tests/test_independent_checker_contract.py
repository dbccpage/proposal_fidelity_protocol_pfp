"""Individual C027 judge controls; a combined rejection cannot hide a false accept."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from pfp.tests.demo_004.c_quantum.c027_kochen_specker_contextuality.judge_packet.checkers import (
    independent_checker,
)
from pfp.tests.demo_004.c_quantum.c027_kochen_specker_contextuality.judge_packet.checkers.exact_checker import (
    verify_exact,
)


ROOT = Path(__file__).resolve().parents[1]


def standard_basis():
    return json.loads(
        (ROOT / "judge_packet/cases/base_04_standard_basis_dim3.json").read_text(
            encoding="utf-8"
        )
    )


def retained_parity():
    case = json.loads(
        (ROOT / "participant_packet/examples/example_01_cabello_18.json").read_text(
            encoding="utf-8"
        )
    )
    answer = next(
        item
        for line in (ROOT / "participant_packet/answers.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if (item := json.loads(line))["id"] == case["case_id"]
    )
    return case, answer


def test_false_refutation_is_rejected_by_each_checker():
    case = standard_basis()
    answer = dict(
        id=case["case_id"], status="SOLVED", colourable=False,
        subset=[0, 1, 2], certificate=dict(kind="refutation", contexts=[]),
    )
    assert verify_exact(case, answer)[0] is False
    assert independent_checker.verify_independent(case, answer)[0] is False


def test_fabricated_parity_context_is_rejected_by_each_checker():
    case = standard_basis()
    answer = dict(
        id=case["case_id"], status="SOLVED", colourable=False,
        subset=[0, 1], certificate=dict(kind="parity", contexts=[[0, 0, 1, 1]]),
    )
    assert verify_exact(case, answer)[0] is False
    assert independent_checker.verify_independent(case, answer)[0] is False


def test_valid_colouring_remains_accepted_by_each_checker():
    case = standard_basis()
    answer = dict(
        id=case["case_id"], status="SOLVED", colourable=True, colouring=[1, 0, 0]
    )
    assert verify_exact(case, answer)[0] is True
    assert independent_checker.verify_independent(case, answer)[0] is True


def test_retained_valid_parity_remains_accepted_by_each_checker():
    case, answer = retained_parity()
    before = deepcopy((case, answer))
    assert verify_exact(case, answer)[0] is True
    assert independent_checker.verify_independent(case, answer)[0] is True
    assert (case, answer) == before


def test_even_incidence_of_nonorthogonal_contexts_is_not_a_parity_proof():
    # Every coordinate is positive, so no pair is orthogonal. Each fabricated
    # four-ray context nevertheless has distinct valid indices and even counts.
    case = dict(
        case_id="nonorthogonal_contexts", dimension=4,
        vectors=[[[1, 0], [i, 0], [i * i, 0], [i * i * i, 0]] for i in range(1, 7)],
    )
    answer = dict(
        id=case["case_id"], status="SOLVED", colourable=False,
        subset=list(range(6)), certificate=dict(
            kind="parity", contexts=[[0, 1, 2, 3], [0, 1, 4, 5], [2, 3, 4, 5]],
        ),
    )
    assert verify_exact(case, answer)[0] is False
    assert independent_checker.verify_independent(case, answer)[0] is False


def test_bounded_refutation_uses_its_own_constraints(monkeypatch):
    case, answer = retained_parity()
    answer["certificate"] = dict(kind="refutation", contexts=[])

    def forbidden(*args, **kwargs):
        raise AssertionError("The independent solved branch must not call checker one")

    monkeypatch.setattr(independent_checker, "verify_exact", forbidden)
    passed, _, details = independent_checker.verify_independent(case, answer)
    assert passed is True
    assert details["verification_method"] == "independent_exhaustive"
    assert details["assignments"] == 1 << 18


def test_refutation_must_establish_the_claimed_subset():
    case, answer = retained_parity()
    answer["subset"] = [0]
    answer["certificate"] = dict(kind="refutation", contexts=[])
    assert independent_checker.verify_independent(case, answer)[0] is False


def test_parity_contexts_must_belong_to_the_claimed_subset():
    case, answer = retained_parity()
    answer["subset"].remove(0)
    assert independent_checker.verify_independent(case, answer)[0] is False


def test_above_bound_refutation_is_unavailable_not_a_mathematical_refusal():
    case = dict(
        case_id="above_independent_bound", dimension=3,
        vectors=[[[1, 0], [i, 0], [i * i, 0]] for i in range(1, 22)],
    )
    answer = dict(
        id=case["case_id"], status="SOLVED", colourable=False,
        subset=list(range(21)), certificate=dict(kind="refutation", contexts=[]),
    )
    with pytest.raises(independent_checker.IndependentVerificationUnavailable) as failure:
        independent_checker.verify_independent(case, answer)
    assert failure.value.code == "C027_INDEPENDENT_ENUMERATION_UNAVAILABLE"
    assert failure.value.merged_rays == 21
    assert failure.value.limit == 20


def test_unregistered_certificate_kind_cannot_gain_acceptance():
    case = standard_basis()
    answer = dict(
        id=case["case_id"], status="SOLVED", colourable=False,
        subset=[0, 1, 2], certificate=dict(kind="not_registered"),
    )
    assert independent_checker.verify_independent(case, answer)[0] is False
