"""Integration contract for the real Paper 002 finite-gauge adapter."""

from pfp.domain.finite_gauge import RunConfig
from pfp.infrastructure.composition.finite_gauge import build_run


def test_real_checker_replays_verified_even_triangle() -> None:
    outcome = build_run(RunConfig("gauge_even_triangle", 8, 0)).execute()

    assert outcome.is_ok
    assert outcome.unwrap()["receipt"]["verified_by_replay"] is True
