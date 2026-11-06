"""Twenty-five host-only adversarial controls; no provider calls."""

import pytest
from omega_engine_adversary.tests.pilots.relational_spacetime.finite_fixtures import VARIANTS
from omega_engine_adversary.tests.pilots.relational_spacetime.finite_fixtures import check_variant


@pytest.mark.parametrize("variant", VARIANTS)
def test_certificate_control(variant):
    check_variant("pilot_0000201", variant)
