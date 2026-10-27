"""Unit tests for Layer 4 Verification Machinery (Track 030).

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pfp.domain.sn_tower.sn_verification import (
    AlternationMonitor,
    DDAEventRecord,
    Kleene3Logic,
    VerificationRGBFirewall,
)


def test_alternation_monitor_lifecycle():
    monitor = AlternationMonitor(max_depth=12)
    assert len(monitor.routes) == 11
    assert "ROUTE_REPAIR" in monitor.routes
    assert "ROUTE_REFUSE" in monitor.routes

    # Progressive steps continue
    assert monitor.evaluate_step(1, "s0", 1) == "ROUTE_CONTINUE"
    assert monitor.evaluate_step(2, "s1", 2) == "ROUTE_CONTINUE"

    # Cycle detected without progress -> ROUTE_REPAIR
    assert monitor.evaluate_step(3, "s0", 1) == "ROUTE_REPAIR"

    # Depth bound exceeded -> ROUTE_REFUSE
    assert monitor.evaluate_step(13, "s_deep", 100) == "ROUTE_REFUSE"


def test_dda_event_record_fuel_conservation():
    rec_valid = DDAEventRecord(
        budget=50,
        c_in=10,
        s_in=2,
        op="step",
        cost=5,
        c_out=15,
        s_out=1,
        d_in=0,
        d_out=0,
        obs_in=1,
        obs_out=1,
        delta=5,
    )
    assert rec_valid.fuel_conserved() is True

    # Fuel depletion: budget less than cost
    rec_depleted = DDAEventRecord(
        budget=3,
        c_in=10,
        s_in=2,
        op="step",
        cost=5,
        c_out=15,
        s_out=1,
        d_in=0,
        d_out=0,
        obs_in=1,
        obs_out=1,
        delta=5,
    )
    assert rec_depleted.fuel_conserved() is False

    # Broken carrier conservation: c_out != c_in + delta
    rec_broken = DDAEventRecord(
        budget=50,
        c_in=10,
        s_in=2,
        op="step",
        cost=5,
        c_out=12,
        s_out=1,
        d_in=0,
        d_out=0,
        obs_in=1,
        obs_out=1,
        delta=5,
    )
    assert rec_broken.fuel_conserved() is False


def test_kleene3_logic():
    K_F, K_T, K_U = Kleene3Logic.K_FALSE, Kleene3Logic.K_TRUE, Kleene3Logic.K_UNKNOWN

    # Conjunction
    assert Kleene3Logic.kleene_and(K_T, K_T) == K_T
    assert Kleene3Logic.kleene_and(K_F, K_U) == K_F
    assert Kleene3Logic.kleene_and(K_T, K_U) == K_U

    # Disjunction
    assert Kleene3Logic.kleene_or(K_T, K_U) == K_T
    assert Kleene3Logic.kleene_or(K_F, K_U) == K_U
    assert Kleene3Logic.kleene_or(K_F, K_F) == K_F

    # Negation
    assert Kleene3Logic.kleene_not(K_T) == K_F
    assert Kleene3Logic.kleene_not(K_F) == K_T
    assert Kleene3Logic.kleene_not(K_U) == K_U

    # Horizon routing for depleted record
    rec_depleted = DDAEventRecord(
        budget=2,
        c_in=10,
        s_in=2,
        op="step",
        cost=5,
        c_out=15,
        s_out=1,
        d_in=0,
        d_out=0,
        obs_in=1,
        obs_out=1,
        delta=5,
    )
    assert Kleene3Logic.evaluate_fuel_status(rec_depleted) == K_U


def test_verification_rgb_firewall():
    firewall = VerificationRGBFirewall()
    firewall.submit_red("prop_42")
    assert "prop_42" in firewall.red_proposals
    assert "prop_42" not in firewall.green_receipts

    # Verification passes
    res = firewall.execute_blue("prop_42", lambda: 10 > 5)
    assert res is True
    assert "prop_42" in firewall.green_receipts

    # Untracked prop raises KeyError
    with pytest.raises(KeyError, match="Untracked proposition"):
        firewall.execute_blue("untracked", lambda: True)

    # Escalation to Genesis raises PermissionError
    with pytest.raises(PermissionError, match="ERR_AUTHORITY_ESCALATION"):
        firewall.promote_to_genesis("prop_42")
