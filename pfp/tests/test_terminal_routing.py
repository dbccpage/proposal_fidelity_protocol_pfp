"""Every PFP terminal status routes to exactly one of the seven routing terminals.

AuthorityEffect: None.
"""

import pytest

from omega_engine_pfp.domain.kernel.result import TerminalStatus
from omega_engine_pfp.infrastructure.terminal_routing import (
    ROUTING_TERMINALS,
    load_terminal_routing,
    routing_terminal,
)


def test_every_status_is_keyed_once():
    assert set(load_terminal_routing()) == {status.value for status in TerminalStatus}


def test_every_value_is_a_routing_terminal():
    assert set(load_terminal_routing().values()) <= set(ROUTING_TERMINALS)


@pytest.mark.parametrize("status,expected", [
    (TerminalStatus.VERIFIED, "CheckPassed"),
    ("VERIFIED", "CheckPassed"),
    ("BlockedByEvidence", "Refusal"),
    (TerminalStatus.BUDGET_EXHAUSTED, "BudgetUnknown"),
    (TerminalStatus.REFUSED, "Refused"),
    (TerminalStatus.STABILIZED_SURVIVOR, "RequiresLift"),
])
def test_lookup_by_member_value_or_name(status, expected):
    assert routing_terminal(status) == expected


def test_an_unknown_status_is_refused():
    with pytest.raises(ValueError):
        routing_terminal("Passed")
