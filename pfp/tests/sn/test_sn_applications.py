"""Unit tests for S(n) Downstream Domain Applications (Track 020).

AuthorityEffect: None.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

from pfp.domain.sn_tower.sn_applications import (
    DownstreamApplication,
    ReggeCurvature,
    ReggeMetric,
    SessionChannel,
    topological_relational_join,
)


def test_topological_relational_join():
    table_a = {("Alice", "Engineering"), ("Bob", "Design")}
    table_b = {("Engineering", "Building1"), ("Design", "Building2")}
    joined = topological_relational_join(table_a, table_b)
    assert len(joined) == 2
    assert ("Alice", "Engineering", "Building1") in joined
    assert ("Bob", "Design", "Building2") in joined

    # Disjoint join
    table_c = {("Marketing", "Building3")}
    disjoint = topological_relational_join(table_a, table_c)
    assert len(disjoint) == 0


def test_session_channel_linear_lifecycle():
    chan = SessionChannel()
    assert chan.state == "INIT"
    assert chan.is_closed is False

    chan.send("DATA_PAYLOAD")
    assert chan.state == "SENT"

    reply = chan.recv()
    assert reply == "ACK"
    assert chan.state == "CLOSED"
    assert chan.is_closed is True

    # Linear exhaustion: cannot send after closing
    with pytest.raises(AssertionError, match="Linear violation"):
        chan.send("SECOND_SEND")


def test_downstream_application_fences():
    app = DownstreamApplication(name="discrete_regge", domain="physics")
    assert app.verify_fences() is True

    # Rogue authority escalation is caught
    rogue = DownstreamApplication(name="rogue", domain="finance", authority_effect="Full")
    assert rogue.verify_fences() is False

    # Rogue layer promotion is caught
    rogue_layer = DownstreamApplication(name="rogue2", domain="finance", layer=1)
    assert rogue_layer.verify_fences() is False


def test_regge_metric_positivity():
    assert ReggeMetric.verify_positivity(1.0) is True
    assert ReggeMetric.verify_positivity(2.5) is True
    assert ReggeMetric.equilateral_gram_determinant(1.0) == 0.75
    assert ReggeMetric.equilateral_gram_trace(1.0) == 2.0


def test_regge_curvature_deficit():
    # Flat hinge (4 right angles)
    dihedrals_flat = [math.pi / 2.0] * 4
    assert ReggeCurvature.is_flat_hinge(dihedrals_flat) is True
    assert math.isclose(ReggeCurvature.deficit_angle(dihedrals_flat), 0.0, abs_tol=1e-9)

    # Positive curvature (acute sum)
    dihedrals_pos = [math.pi / 3.0] * 5
    assert ReggeCurvature.is_positive_curvature(dihedrals_pos) is True
    assert ReggeCurvature.is_flat_hinge(dihedrals_pos) is False
