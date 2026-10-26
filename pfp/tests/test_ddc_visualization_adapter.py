"""Unit tests for DDC visualization and presentation adapter decoupling.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Optional

import pytest

from omega_engine_pfp.domain.ddc.dda import (
    DDALetter,
    DDATraceNode,
    LyapunovTracker,
)
from omega_engine_pfp.domain.ddc.visualize import (
    LyapunovPlotRendererPort,
    export_lyapunov_descent_data,
    export_lyapunov_descent_plot,
    register_lyapunov_plot_renderer,
    render_lyapunov_descent_ascii,
)
from omega_engine_pfp.infrastructure.adapters.ddc_plot_adapter import (
    render_lyapunov_descent_plot,
)


def _make_tracker() -> LyapunovTracker:
    tracker = LyapunovTracker()
    tracker.nodes.append(
        DDATraceNode(
            step_index=0,
            letter=DDALetter.E,
            phi_1=Fraction(2, 1),
            gamma_2=Fraction(1, 1),
            xi=Fraction(0, 1),
            delta_phi_1=Fraction(0, 1),
            state_hash="0" * 64,
            action_summary="Initial state",
        )
    )
    tracker.nodes.append(
        DDATraceNode(
            step_index=1,
            letter=DDALetter.R,
            phi_1=Fraction(1, 1),
            gamma_2=Fraction(1, 1),
            xi=Fraction(0, 1),
            delta_phi_1=Fraction(-1, 1),
            state_hash="1" * 64,
            action_summary="Descent step",
        )
    )
    return tracker




class TestDdcVisualizationAdapter:
    def test_export_lyapunov_descent_data_pure_structure(self) -> None:
        """Verify data export is a pure domain dictionary without presentation coupling."""
        tracker = _make_tracker()
        data = export_lyapunov_descent_data(tracker)
        assert data["tape"] == "E.R"
        assert data["steps"] == [0, 1]
        assert data["phi_1"] == [2.0, 1.0]
        assert data["gamma_2"] == [1.0, 1.0]
        assert data["lyapunov_energy_v"] == [3.0, 2.0]
        assert data["letters"] == ["E", "R"]


    def test_ascii_visualization_pure_domain(self) -> None:
        """Verify ASCII renderer runs cleanly inside domain."""
        tracker = _make_tracker()
        ascii_out = render_lyapunov_descent_ascii(tracker)
        assert "Step  | Tok  | Phi_1    | Gamma_2  | V=Phi+Gamma | Delta_Phi  | Descent Bar" in ascii_out
        assert "0     | E" in ascii_out
        assert "1     | R" in ascii_out


    def test_plot_renderer_port_injection(self) -> None:
        """Verify plot renderer port allows injecting presentation adapters cleanly."""
        tracker = _make_tracker()
        rendered_calls: list[dict[str, Any]] = []

        class MockPlotRenderer:
            def __call__(
                self,
                t: LyapunovTracker,
                filepath: Optional[str] = None,
            ) -> Any:
                rendered_calls.append({"tape": t.tape, "filepath": filepath})
                return "mock_figure"

        mock_renderer = MockPlotRenderer()
        assert isinstance(mock_renderer, LyapunovPlotRendererPort)

        # Explicit injection via parameter
        fig = export_lyapunov_descent_plot(tracker, filepath="test.png", renderer=mock_renderer)
        assert fig == "mock_figure"
        assert len(rendered_calls) == 1
        assert rendered_calls[0]["filepath"] == "test.png"

        # Registration via port registry
        register_lyapunov_plot_renderer(mock_renderer)
        fig2 = export_lyapunov_descent_plot(tracker)
        assert fig2 == "mock_figure"
        assert len(rendered_calls) == 2

        # Reset to default adapter
        register_lyapunov_plot_renderer(render_lyapunov_descent_plot)
