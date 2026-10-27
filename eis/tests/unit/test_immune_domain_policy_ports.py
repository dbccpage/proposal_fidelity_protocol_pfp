"""Unit and mutation-style coverage for inward immune policy ports."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from eis.domain.external_admission import (
    AntibodyObservationV1,
    ReplayResult,
    ReplayVerifierV1,
    distinct_observations,
)
from eis.domain.guard_activation import (
    DangerSignalReceiptV1,
    DetectorHitRefV1,
    GuardActivationReceiptV1,
    evaluate_activation,
)
from eis.domain.provisional_promotion import (
    PromotionResult,
    ProvisionalPromotionEngineV1,
)


def digest(character: str) -> str:
    return "sha256:" + character * 64


def test_external_admission_policy_is_injected_and_observable() -> None:
    observation = AntibodyObservationV1(digest("1"), "host", "run")
    policy = Mock()
    policy.distinct_observations.return_value = (digest("f"),)
    policy.verify_replay.return_value = ReplayResult("ACTIVE", True, 1)

    assert distinct_observations((observation,), policy=policy) == (digest("f"),)
    replay = ReplayVerifierV1(["candidate"], policy=policy).verify_replay("candidate")

    assert replay.is_valid_replay is True
    policy.distinct_observations.assert_called_once_with((observation,))
    policy.verify_replay.assert_called_once_with("candidate", False, frozenset({"candidate"}))


def test_guard_input_validation_fails_before_an_injected_policy_runs() -> None:
    policy = Mock()

    with pytest.raises(ValueError, match="exact boolean"):
        evaluate_activation(
            digest("a"),
            None,
            None,
            externally_admitted=1,
            suspended=False,
            policy=policy,
        )

    policy.evaluate_activation.assert_not_called()


def test_guard_policy_can_be_replaced_without_patching_infrastructure() -> None:
    hit = DetectorHitRefV1(digest("1"), "spec", "FAILURE", digest("2"))
    danger = DangerSignalReceiptV1("REPLAY_FAILURE", "host", digest("2"), digest("3"))
    expected = GuardActivationReceiptV1(
        profile_digest=digest("4"),
        hit_id=hit.hit_id,
        danger_receipt_id=danger.receipt_id,
        subject_id=hit.subject_id,
        disposition="HOLD",
        independence_basis="test policy supplied two independent signals",
    )
    policy = Mock()
    policy.evaluate_activation.return_value = expected

    actual = evaluate_activation(
        digest("4"),
        hit,
        danger,
        externally_admitted=True,
        suspended=False,
        disposition="HOLD",
        policy=policy,
    )

    assert actual is expected
    policy.evaluate_activation.assert_called_once()


def test_promotion_policy_is_constructor_injected() -> None:
    expected = PromotionResult("candidate", "Candidate", False)
    policy = Mock()
    policy.promote.return_value = expected
    engine = ProvisionalPromotionEngineV1(policy=policy)

    actual = engine.promote_candidate_if_eligible("candidate", 99, ["math"])

    assert actual is expected
    policy.promote.assert_called_once_with("candidate", 99, ["math"])
