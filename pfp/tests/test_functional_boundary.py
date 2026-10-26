"""Legacy Python producers must refuse before minting named functionals."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from omega_engine_pfp.entrypoints.cli.symbol_game import main
from omega_engine_pfp.functional_boundary import RustFunctionalRequired


# gate11-self, gate11-ingest and gate11-project left this list when they began
# taking every Phi1/Gamma2 from omega_functional through the native port
# (tests/test_exact_functional_port.py). These three still have no Rust-backed
# producer and must keep refusing.
@pytest.mark.parametrize("command", ["run-turn", "run-bout", "run"])
def test_legacy_cli_refuses_before_writing(command: str, capsys) -> None:
    output = Path(f"boundary-should-not-exist-{uuid4().hex}")
    argv = [command, "--prompt", "finite input", "--output-dir", str(output)]

    assert main(argv) == 2
    assert "RUST_FUNCTIONAL_REQUIRED" in capsys.readouterr().err
    assert not output.exists()


def test_python_metric_producers_refuse_before_inputs_are_used() -> None:
    from omega_engine_pfp.domain.bridge.real_evaluators import (
        LPDualityCalculator,
        MeronClusterCalculator,
    )
    from omega_engine_pfp.domain.entities.cochain_projector import CochainProjector
    from omega_engine_pfp.use_cases.problem_runner import ProblemRunnerUseCase
    from omega_engine_pfp.use_cases.symbol_game_runner import SymbolGameRunnerUseCase

    producers = (
        lambda: LPDualityCalculator.evaluate_lp(
            objective_coeffs={}, is_max=False, constraints=[], primal_point={}, dual_multipliers={}
        ),
        lambda: MeronClusterCalculator.evaluate_clusters([], [], [], {}),
        lambda: CochainProjector.project(None, None),
        lambda: ProblemRunnerUseCase.run_problem(None, "test"),
        lambda: SymbolGameRunnerUseCase.run_problem(None, "test"),
    )
    for produce in producers:
        with pytest.raises(RustFunctionalRequired, match="omega_engine/crates_rs/omega_functional/src"):
            produce()


def test_empty_trace_refuses_before_touching_emitters():
    from omega_engine_pfp.domain.bridge.symbol_game_emitter import UnifiedNarrativeScriptEmitter

    with pytest.raises(RustFunctionalRequired):
        UnifiedNarrativeScriptEmitter.emit_uns_trace(
            None, "empty", None, (), "PASS_TO_MASTER", "unused"
        )


def test_other_legacy_scores_refuse_and_structural_checks_remain_available():
    from omega_engine_pfp.domain.bridge.real_evaluators import (
        AdjunctionSheafDefectCalculator, CochainTriadCalculator,
        KagomeMultiThimbleCalculator, LPConstraint,
        MajoranaThimbleLiftCalculator, MeronClusterCalculator,
    )
    producers = (
        lambda: CochainTriadCalculator.evaluate_cochain(None, None, None),
        lambda: MeronClusterCalculator.evaluate_frustrated_lattice(None, None, None, None),
        lambda: MajoranaThimbleLiftCalculator.evaluate_thimble_lift(
            sites=None, odd_cycle=None, flow_time=None
        ),
        lambda: KagomeMultiThimbleCalculator.evaluate_kagome_thimbles(
            sites=None, triangles=None, flow_time=None, include_stokes_resummation=True
        ),
        lambda: AdjunctionSheafDefectCalculator.evaluate_adjunction(
            adjunction_name="test", stage_round=1
        ),
    )
    for produce in producers:
        with pytest.raises(RustFunctionalRequired):
            produce()
    assert LPConstraint("bound", {"x": 1}, "<=", 2).evaluate({"x": 1}) == (1, 0, True)
    assert MeronClusterCalculator.check_bipartiteness([0, 1], [(0, 1)]) == (True, [])
