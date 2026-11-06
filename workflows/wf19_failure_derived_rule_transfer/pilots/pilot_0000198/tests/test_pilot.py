"""Actual PFP gate mutants, not inventory passes."""

import pytest

from omega_engine_adversary.tests.pilots.challenge_suite.__main__ import HARNESS_MUTANTS
from omega_engine_pfp.tests.test_challenge_learning import (
    test_gate_mutant as _assert_mutant,
)


@pytest.mark.parametrize("name", HARNESS_MUTANTS)
def test_pfp_gate_mutant(name):
    _assert_mutant(name)
