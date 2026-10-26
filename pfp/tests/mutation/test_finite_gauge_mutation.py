"""Mutation-killing contract for independent replay."""

from omega_engine_pfp.domain.finite_gauge import GaugeRefusalCode, RunConfig
from omega_engine_pfp.infrastructure.adapters.finite_gauge.paper002_checker import (
    Paper002FiniteGaugeChecker,
)


def test_false_replay_verdict_cannot_reach_success_track() -> None:
    checker = Paper002FiniteGaugeChecker(receipt_verifier=lambda *_args: False)

    outcome = checker.search_and_replay(
        RunConfig("gauge_even_triangle", 8, 0).graph_spec(), 8
    )

    assert outcome.is_err
    assert outcome.unwrap_err().code is GaugeRefusalCode.REPLAY_FAILED
