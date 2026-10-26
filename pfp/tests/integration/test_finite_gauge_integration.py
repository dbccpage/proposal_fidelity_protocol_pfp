"""Integration contract for the real Paper 002 finite-gauge adapter."""

from omega_engine_pfp.domain.finite_gauge import RunConfig
from omega_engine_pfp.infrastructure.composition.finite_gauge import build_run


def test_real_checker_replays_verified_even_triangle() -> None:
    outcome = build_run(RunConfig("gauge_even_triangle", 8, 0)).execute()

    assert outcome.is_ok
    assert outcome.unwrap()["receipt"]["verified_by_replay"] is True
