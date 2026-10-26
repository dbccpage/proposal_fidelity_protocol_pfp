"""Tests for the Symbol Game interactive board rendering and educational scenario runner.

AuthorityEffect: None.
Tests:
- Publication-grade HTML board rendering across 4 discrete defect states.
- HTML decision banners for ADMITTED, ACCEPTED, and REFUSED outcomes.
- HTML sanitization / escaping for declared invariants.
- SVG triangle geometry, vertex placement, and circulation arithmetic.
- CLI fallback output when IPython is unavailable.
- Complete execution and feedback commentary for scenarios 1 through 7.
- Negative control refusal on unknown scenario numbers.
- Dynamic widget factory handling.
"""

from __future__ import annotations

import importlib.util
import sys
from io import StringIO
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gov_mod = _load_module("educational_governor", _THIS_DIR / "educational_governor.py")
_board_mod = _load_module("interactive_board", _THIS_DIR / "interactive_board.py")

EducationalHostGovernor = _gov_mod.EducationalHostGovernor
render_html_board = _board_mod.render_html_board
render_svg_triangle = _board_mod.render_svg_triangle
display_board = _board_mod.display_board
run_scenario_with_feedback = _board_mod.run_scenario_with_feedback
create_interactive_game_widget = _board_mod.create_interactive_game_widget


def make_fresh_board(initial_fuel: int = 10) -> EducationalHostGovernor:
    """Create a standard 3-cycle triangle board with circulation 2 + 1 + 3 = 6."""
    return EducationalHostGovernor(
        vertices=[0, 1, 2],
        edges=["0->1", "1->2", "2->0"],
        initial_claims={"0->1": 2, "1->2": 1, "2->0": 3},
        fuel=initial_fuel,
    )


class TestHtmlBoardRendering:
    """Tests for render_html_board states and formatting."""

    def test_active_defect_state(self) -> None:
        """Defect > 3 renders ACTIVE DEFECT in red."""
        host = make_fresh_board()
        html_out = render_html_board(host)
        assert "ACTIVE DEFECT (Φ₁ = 6)" in html_out
        assert "#dc2626" in html_out
        assert "0->1" in html_out
        assert "1->2" in html_out
        assert "2->0" in html_out
        assert "(No invariants declared)" in html_out

    def test_repair_in_progress_state(self) -> None:
        """Defect in 1..3 renders REPAIR IN PROGRESS in amber."""
        host = make_fresh_board()
        host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -1}}})
        assert host.compute_total_defect() == 2
        html_out = render_html_board(host)
        assert "REPAIR IN PROGRESS (defect = 2)" in html_out
        assert "#d97706" in html_out

    def test_zero_defect_unsealed_state(self) -> None:
        """Defect = 0 before verify renders ZERO DEFECT in blue."""
        host = make_fresh_board()
        host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -3}}})
        assert host.compute_total_defect() == 0
        assert not host.is_terminal
        html_out = render_html_board(host)
        assert "ZERO DEFECT (READY FOR VERIFY)" in html_out
        assert "#2563eb" in html_out

    def test_sealed_terminal_state(self) -> None:
        """Calling VERIFY at zero defect renders TEACHING CHECK PASSED in green."""
        host = make_fresh_board()
        host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -3}}})
        host.execute_move({"move_type": "VERIFY", "payload": {}})
        assert host.is_terminal
        html_out = render_html_board(host)
        assert "TEACHING CHECK PASSED (ZERO CIRCULATION)" in html_out
        assert "#16a34a" in html_out

    def test_decision_banner_admitted_vs_refused(self) -> None:
        """Decision banner displays green check for ADMITTED and red cross for REFUSED."""
        host = make_fresh_board()
        res_ok = host.execute_move({"move_type": "ASSERT", "payload": {"relation": "R1"}})
        html_ok = render_html_board(host, last_result=res_ok)
        assert "ADMITTED" in html_ok
        assert "#15803d" in html_ok
        assert "✓" in html_ok

        res_refused = host.execute_move(
            {"move_type": "CUT", "payload": {"proposed_claims": {"2->0": 99}}}
        )
        html_refused = render_html_board(host, last_result=res_refused)
        assert "REFUSED_MONOTONICITY_VIOLATION" in html_refused
        assert "#991b1b" in html_refused
        assert "✗" in html_refused

    def test_invariants_sanitization(self) -> None:
        """Invariants containing HTML tags or ampersands are properly escaped."""
        host = make_fresh_board()
        host.execute_move({"move_type": "ASSERT", "payload": {"relation": "<INVARIANT & PROOF>"}})
        html_out = render_html_board(host)
        assert "&lt;INVARIANT &amp; PROOF&gt;" in html_out
        assert "<INVARIANT & PROOF>" not in html_out


class TestSvgTriangleRendering:
    """Tests for render_svg_triangle SVG markup and geometry."""

    def test_svg_structure_and_coordinates(self) -> None:
        """SVG contains valid header, viewBox, vertex nodes, and circulation formula."""
        host = make_fresh_board()
        svg = render_svg_triangle(host)
        assert svg.startswith("<svg") or "<svg" in svg
        assert 'viewBox="0 0 460 300"' in svg
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg
        # Vertices 0, 1, 2
        assert 'cx="230" cy="55"' in svg
        assert 'cx="350" cy="220"' in svg
        assert 'cx="110" cy="220"' in svg
        # Defect text
        assert "Φ₁" in svg
        assert "Circulation = (2) + (1) + (3) = 6" in svg

    def test_svg_updates_upon_cut(self) -> None:
        """SVG reflects updated edge claims and reduced defect."""
        host = make_fresh_board()
        host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -3}}})
        svg = render_svg_triangle(host)
        assert "Circulation = (2) + (1) + (-3) = 0" in svg


class TestDisplayBoardFallback:
    """Tests for display_board text fallback."""

    def test_cli_display_board_output(self, monkeypatch) -> None:
        """When HAS_IPYTHON is False, display_board prints structured text to stdout."""
        monkeypatch.setattr(_board_mod, "HAS_IPYTHON", False)
        host = make_fresh_board()
        out = StringIO()
        monkeypatch.setattr(sys, "stdout", out)

        display_board(
            host, last_result={"decision": "TEST_DECISION", "message": "Test explanation"}
        )
        output_str = out.getvalue()
        assert "=== BOARD STATE: Defect Φ1 = 6" in output_str
        assert (
            "Claims: {'0->1': Fraction(2, 1), '1->2': Fraction(1, 1), '2->0': Fraction(3, 1)}"
            in output_str
        )
        assert "Last Move Decision: TEST_DECISION - Test explanation" in output_str


class TestScenarioRunnerWithFeedback:
    """Tests for run_scenario_with_feedback across all 7 scenarios."""

    @pytest.mark.parametrize(
        "scenario_num,expected_decision,expected_snippet",
        [
            (1, "ADMITTED", "ASSERT Move"),
            (2, "ADMITTED", "Valid Descending CUT"),
            (3, "REFUSED_MONOTONICITY_VIOLATION", "Non-Monotonic CUT"),
            (4, "REFUSED_CARRIER_DOMAIN", "Carrier Domain Smuggling"),
            (5, "REFUSED_NONZERO_DEFECT", "Premature VERIFY Attempt"),
            (6, "ACCEPTED_ZERO_DEFECT", "Exact Chord CUT & Terminal Certification"),
            (7, "REFUSED_TERMINAL_STATE", "Post-Terminal Mutation Rejection"),
        ],
    )
    def test_canonical_scenarios(
        self, scenario_num: int, expected_decision: str, expected_snippet: str
    ) -> None:
        """Each scenario 1..7 returns its expected decision code and pedagogical commentary."""
        host = make_fresh_board()
        res, commentary = run_scenario_with_feedback(scenario_num, host)
        assert res["decision"] == expected_decision
        assert expected_snippet in commentary

    def test_negative_control_unknown_scenario(self) -> None:
        """Unknown scenario number returns REFUSED_UNKNOWN_SCENARIO."""
        host = make_fresh_board()
        res, commentary = run_scenario_with_feedback(999, host)
        assert res["decision"] == "REFUSED_UNKNOWN_SCENARIO"
        assert "Unknown scenario number 999" in commentary


class TestInteractiveGameWidget:
    """Tests for create_interactive_game_widget."""

    def test_create_widget_headless(self, monkeypatch) -> None:
        """When ipywidgets is not installed, creates widget gracefully or returns error notice."""
        monkeypatch.setattr(_board_mod, "HAS_IPYTHON", False)
        monkeypatch.setattr(_board_mod, "widgets", None)
        host = make_fresh_board()
        widget = create_interactive_game_widget(host)
        # In headless environment without ipywidgets, returns notice string or None
        assert widget is None or isinstance(widget, str)
