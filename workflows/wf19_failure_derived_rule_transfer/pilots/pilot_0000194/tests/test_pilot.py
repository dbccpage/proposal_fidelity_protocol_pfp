"""Frozen test-plan custody. Domain attempts are retained in campaign receipts."""

from pathlib import Path

import pytest
import yaml

from omega_engine_adversary.tests.pilots.challenge_suite.catalog import load_case
from omega_engine_pfp.use_cases.pfp_prompt import stimulus

_PLAN = yaml.safe_load(
    (Path(__file__).resolve().parent.parent / "testplan.yaml").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", _PLAN["cases"])
def test_declared_case(case):
    if "source" in case:
        value = load_case(case)
        assert type(value) is dict
        assert type(stimulus(value)) is dict
    else:
        pytest.skip(case.get("blocker", "Planned instrumentation condition"))


@pytest.mark.parametrize("case", [c for c in _PLAN["cases"] if "source" in c][:4])
def test_refuse_source_digest_mutation(case):
    mutated = dict(case, sha256="0" * 64)
    with pytest.raises(ValueError, match="CASE_SOURCE_DRIFT"):
        load_case(mutated)
