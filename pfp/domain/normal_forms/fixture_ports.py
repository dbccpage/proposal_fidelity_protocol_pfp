"""Ports and pure parsing for BQNF fixture cases.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

BqnfFixture = dict[str, Any]
BqnfFixtures = tuple[BqnfFixture, ...]


class BqnfFixtureLoaderPort(Protocol):
    """Injected boundary for reading fixture documents."""

    def load(self, location: str) -> Result[BqnfFixtures, Refusal]: ...


def parse_bqnf_fixture_payload(payload: object) -> Result[BqnfFixtures, Refusal]:
    """Normalize decoded JSON/YAML data without performing I/O."""
    cases: object = (
        payload.get("fixtures")
        if isinstance(payload, Mapping) and "fixtures" in payload
        else payload
    )
    if isinstance(cases, Mapping):
        cases = [cases]
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes, bytearray)):
        return Err(
            Refusal(
                "BQNF_FIXTURE_SHAPE_REFUSED",
                "Fixture payload must be a case, a list of cases, or a fixtures mapping",
                "bqnf.fixture.parse",
            )
        )
    if not all(isinstance(case, Mapping) for case in cases):
        return Err(
            Refusal(
                "BQNF_FIXTURE_CASE_REFUSED",
                "Every BQNF fixture case must be a mapping",
                "bqnf.fixture.parse",
            )
        )
    return Ok(tuple(dict(case) for case in cases))


__all__ = [
    "BqnfFixture",
    "BqnfFixtureLoaderPort",
    "BqnfFixtures",
    "parse_bqnf_fixture_payload",
]
