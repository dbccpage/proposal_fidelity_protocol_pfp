"""Tests for pfp package and unified SymbolGameController."""

from __future__ import annotations

import pytest

from pfp.controllers.symbol_game_controller import SymbolGameController
from pfp.functional_boundary import RustFunctionalRequired


def test_symbol_game_turn_execution():
    controller = SymbolGameController()
    outcome = controller.run_turn(
        task_id="sg_task_001",
        prompt="verify formal coboundary obstruction for 1-cochain",
    )
    assert outcome.step_id.startswith("step_")
    assert outcome.purity > 0.0
    assert outcome.evidence_sha256.startswith("sha256:")
    assert outcome.authority_effect == "None"


def test_symbol_game_specimen_mt000():
    controller = SymbolGameController()
    with pytest.raises(RustFunctionalRequired):
        controller.run_specimen_mt000()


def test_symbol_game_refactoring_packet():
    controller = SymbolGameController()
    with pytest.raises(RustFunctionalRequired):
        controller.run_refactoring_packet(max_steps=2)
