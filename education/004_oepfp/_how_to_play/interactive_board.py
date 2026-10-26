"""Interactive Board & Visualizer for The Symbol Game How to Play Series.

Provides publication-grade HTML/SVG board rendering, dynamic ipywidgets control
panels, and scenario runners directly consuming EducationalHostGovernor.
"""

from __future__ import annotations

import html
import unittest
from fractions import Fraction
from typing import Any, Dict, Optional, Tuple

try:
    import ipywidgets as widgets
    from IPython.display import HTML, SVG, clear_output, display

    HAS_IPYTHON = True
except Exception:
    widgets = None
    display = None
    clear_output = None
    HTML = None
    SVG = None
    HAS_IPYTHON = False

try:
    from .educational_governor import EducationalHostGovernor
except (ImportError, ValueError):
    try:
        from educational_governor import EducationalHostGovernor
    except ImportError:
        import sys
        from pathlib import Path
        _this = Path(__file__).resolve().parent
        if str(_this) not in sys.path:
            sys.path.insert(0, str(_this))
        from educational_governor import EducationalHostGovernor


def render_html_board(
    host: EducationalHostGovernor, last_result: Optional[Dict[str, Any]] = None
) -> str:
    """Render a responsive, publication-grade HTML board representation."""
    defect = host.compute_total_defect()
    fuel = host.fuel
    initial_fuel = host.initial_fuel
    is_terminal = host.is_terminal

    # Color tokens
    if is_terminal:
        status_bg = "#dcfce7"
        status_color = "#15803d"
        status_text = "TEACHING CHECK PASSED (ZERO CIRCULATION)"
        defect_color = "#16a34a"
    elif defect == 0:
        status_bg = "#eff6ff"
        status_color = "#1d4ed8"
        status_text = "ZERO DEFECT (READY FOR VERIFY)"
        defect_color = "#2563eb"
    elif defect <= 3:
        status_bg = "#fef3c7"
        status_color = "#b45309"
        status_text = f"REPAIR IN PROGRESS (defect = {defect})"
        defect_color = "#d97706"
    else:
        status_bg = "#fee2e2"
        status_color = "#b91c1c"
        status_text = f"ACTIVE DEFECT (Φ₁ = {defect})"
        defect_color = "#dc2626"

    # Fuel percentage
    fuel_pct = int((fuel / max(1, initial_fuel)) * 100)
    fuel_color = "#16a34a" if fuel > 2 else ("#f59e0b" if fuel > 0 else "#dc2626")

    # Invariants list
    invariants_html = (
        "".join(
            f'<span style="background: #e2e8f0; color: #1e293b; padding: 2px 8px; border-radius: 4px; font-family: monospace; font-size: 11px; margin-right: 6px;">{html.escape(inv)}</span>'
            for inv in sorted(host.invariants)
        )
        if host.invariants
        else '<span style="color: #94a3b8; font-style: italic; font-size: 12px;">(No invariants declared)</span>'
    )

    # Claims table
    claims_rows = ""
    for edge in sorted(host.edges):
        val = host.claims.get(edge, Fraction(0))
        claims_rows += f"""
        <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 6px 12px; font-family: monospace; font-weight: 600; color: #334155;">{edge}</td>
            <td style="padding: 6px 12px; font-family: monospace; color: #0f172a; text-align: right;">{val}</td>
            <td style="padding: 6px 12px; text-align: center;">
                <span style="background: #dbeafe; color: #1e40af; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;">PINNED CARRIER</span>
            </td>
        </tr>
        """

    # Last decision banner
    decision_html = ""
    if last_result:
        dec = last_result.get("decision", "UNKNOWN")
        msg = last_result.get("message", "")
        if "ACCEPTED" in dec or dec == "ADMITTED":
            badge_bg = "#dcfce7"
            badge_border = "#86efac"
            badge_color = "#15803d"
            icon = "✓"
        else:
            badge_bg = "#fee2e2"
            badge_border = "#fca5a5"
            badge_color = "#991b1b"
            icon = "✗"
        decision_html = f"""
        <div style="margin-top: 12px; padding: 10px 14px; background: {badge_bg}; border: 1px solid {badge_border}; border-radius: 6px; color: {badge_color};">
            <strong style="font-size: 12px;">{icon} {html.escape(dec)}</strong>
            {f'<span style="font-size: 11px; margin-left: 8px;">— {html.escape(msg)}</span>' if msg else ""}
        </div>
        """

    # History summary
    history_html = (
        "".join(
            f'<div style="font-family: monospace; font-size: 11px; color: #475569; padding: 2px 0;">'
            f"• Turn {i + 1}: <b>{h.get('move', 'MOVE')}</b> {'(' + html.escape(str(h.get('relation') or h.get('new_defect'))) + ')' if h.get('relation') or h.get('new_defect') else ''}</div>"
            for i, h in enumerate(host.history[-4:])
        )
        if host.history
        else '<div style="color: #94a3b8; font-style: italic; font-size: 11px;">(Zero moves executed)</div>'
    )

    html_code = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 10px 0; max-width: 780px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px;">
            <div>
                <span style="font-size: 15px; font-weight: 700; color: #0f172a;">Symbol Game Board State</span>
                <span style="background: {status_bg}; color: {status_color}; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 12px; margin-left: 8px;">
                    {status_text}
                </span>
            </div>
            <div style="font-size: 11px; color: #64748b;">
                Vertices: <b>{len(host.vertices)}</b> | Edges: <b>{len(host.edges)}</b>
            </div>
        </div>

        <!-- Metric Meters -->
        <div style="display: flex; gap: 16px; margin-top: 14px;">
            <!-- Defect Gauge -->
            <div style="flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">Triangle circulation defect</div>
                <div style="font-size: 26px; font-weight: 800; color: {defect_color}; margin: 4px 0;">{defect}</div>
                <div style="font-size: 10px; color: #94a3b8;">Circulation |∑ c(e)|</div>
            </div>

            <!-- Turn Fuel Meter -->
            <div style="flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: 600; color: #64748b;">
                    <span>TURN FUEL</span>
                    <span style="color: {fuel_color}; font-weight: 700;">{fuel} / {initial_fuel}</span>
                </div>
                <div style="background: #e2e8f0; border-radius: 6px; height: 10px; margin-top: 8px; overflow: hidden;">
                    <div style="background: {fuel_color}; width: {fuel_pct}%; height: 100%; border-radius: 6px; transition: width 0.3s ease;"></div>
                </div>
                <div style="font-size: 10px; color: #94a3b8; margin-top: 6px; text-align: right;">{initial_fuel - fuel} turns consumed</div>
            </div>
        </div>

        <!-- Claims and Invariants -->
        <div style="display: flex; gap: 16px; margin-top: 14px;">
            <!-- Edge Claims -->
            <div style="flex: 1.2;">
                <div style="font-size: 12px; font-weight: 700; color: #334155; margin-bottom: 6px;">Pinned Carrier Edge Claims</div>
                <table style="width: 100%; border-collapse: collapse; font-size: 12px; background: #fafafa; border: 1px solid #f1f5f9; border-radius: 6px;">
                    <thead>
                        <tr style="background: #f1f5f9; color: #475569; text-align: left; font-size: 11px;">
                            <th style="padding: 6px 12px;">Edge</th>
                            <th style="padding: 6px 12px; text-align: right;">Claim Value</th>
                            <th style="padding: 6px 12px; text-align: center;">Domain</th>
                        </tr>
                    </thead>
                    <tbody>
                        {claims_rows}
                    </tbody>
                </table>
            </div>

            <!-- Invariants & History -->
            <div style="flex: 1;">
                <div style="font-size: 12px; font-weight: 700; color: #334155; margin-bottom: 6px;">Asserted Invariants</div>
                <div style="background: #fafafa; border: 1px solid #f1f5f9; border-radius: 6px; padding: 8px 10px; min-height: 40px; margin-bottom: 10px;">
                    {invariants_html}
                </div>

                <div style="font-size: 12px; font-weight: 700; color: #334155; margin-bottom: 6px;">Recent Move History</div>
                <div style="background: #fafafa; border: 1px solid #f1f5f9; border-radius: 6px; padding: 8px 10px; min-height: 40px;">
                    {history_html}
                </div>
            </div>
        </div>

        {decision_html}
    </div>
    """
    return html_code


def render_svg_triangle(host: EducationalHostGovernor) -> str:
    """Generate dynamic SVG of the 3-cycle triangle graph with live claims and defect."""
    defect = host.compute_total_defect()
    c01 = host.claims.get("0->1", Fraction(0))
    c12 = host.claims.get("1->2", Fraction(0))
    c20 = host.claims.get("2->0", Fraction(0))

    edge_color = "#16a34a" if defect == 0 else "#dc2626"
    badge_bg = "#22c55e" if defect == 0 else "#ef4444"
    status_text = "BALANCED (Φ₁ = 0)" if defect == 0 else f"DEFECT (Φ₁ = {defect})"

    svg_code = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 300" width="460" height="300" style="background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0;">
      <defs>
        <marker id="arrow-dyn" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="{edge_color}"/>
        </marker>
        <filter id="node-shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.15"/>
        </filter>
      </defs>

      <!-- Title Banner -->
      <rect x="10" y="10" width="440" height="28" rx="5" fill="#f8fafc"/>
      <text x="230" y="28" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155" text-anchor="middle">
        3-Cycle Circulation Graph: {status_text}
      </text>

      <!-- Directed Edges -->
      <!-- Edge 0->1 -->
      <path d="M 235 70 L 335 205" fill="none" stroke="{edge_color}" stroke-width="3" marker-end="url(#arrow-dyn)"/>
      <rect x="295" y="125" width="60" height="22" rx="4" fill="#ffffff" stroke="{edge_color}" stroke-width="1.2"/>
      <text x="325" y="140" font-family="monospace" font-size="11" font-weight="700" fill="#0f172a" text-anchor="middle">c={c01}</text>

      <!-- Edge 1->2 -->
      <path d="M 330 220 L 130 220" fill="none" stroke="{edge_color}" stroke-width="3" marker-end="url(#arrow-dyn)"/>
      <rect x="200" y="230" width="60" height="22" rx="4" fill="#ffffff" stroke="{edge_color}" stroke-width="1.2"/>
      <text x="230" y="245" font-family="monospace" font-size="11" font-weight="700" fill="#0f172a" text-anchor="middle">c={c12}</text>

      <!-- Edge 2->0 -->
      <path d="M 125 205 L 225 70" fill="none" stroke="{edge_color}" stroke-width="3" marker-end="url(#arrow-dyn)"/>
      <rect x="105" y="125" width="60" height="22" rx="4" fill="#ffffff" stroke="{edge_color}" stroke-width="1.2"/>
      <text x="135" y="140" font-family="monospace" font-size="11" font-weight="700" fill="#0f172a" text-anchor="middle">c={c20}</text>

      <!-- Nodes: V0 (230, 55), V1 (350, 220), V2 (110, 220) -->
      <g filter="url(#node-shadow)">
        <circle cx="230" cy="55" r="18" fill="#1e293b"/>
        <text x="230" y="61" font-family="system-ui, sans-serif" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">0</text>
      </g>
      <g filter="url(#node-shadow)">
        <circle cx="350" cy="220" r="18" fill="#1e293b"/>
        <text x="350" y="226" font-family="system-ui, sans-serif" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">1</text>
      </g>
      <g filter="url(#node-shadow)">
        <circle cx="110" cy="220" r="18" fill="#1e293b"/>
        <text x="110" y="226" font-family="system-ui, sans-serif" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">2</text>
      </g>

      <!-- Central Defect Badge -->
      <circle cx="230" cy="165" r="28" fill="{badge_bg}" opacity="0.15"/>
      <circle cx="230" cy="165" r="22" fill="{badge_bg}"/>
      <text x="230" y="161" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#ffffff" text-anchor="middle">Φ₁</text>
      <text x="230" y="174" font-family="system-ui, sans-serif" font-size="13" font-weight="800" fill="#ffffff" text-anchor="middle">{defect}</text>

      <text x="230" y="285" font-family="monospace" font-size="10" fill="#64748b" text-anchor="middle">
        Circulation = ({c01}) + ({c12}) + ({c20}) = {c01 + c12 + c20}
      </text>
    </svg>
    """
    return svg_code


def display_board(
    host: EducationalHostGovernor, last_result: Optional[Dict[str, Any]] = None
) -> None:
    """Display the board state with HTML and SVG in notebook or text fallback in CLI."""
    if HAS_IPYTHON and HTML and SVG and display:
        display(HTML(render_html_board(host, last_result)))
        display(SVG(render_svg_triangle(host)))
    else:
        defect = host.compute_total_defect()
        print(
            f"=== BOARD STATE: Defect Φ1 = {defect}, Fuel = {host.fuel}/{host.initial_fuel}, Terminal = {host.is_terminal} ==="
        )
        print(f"Claims: {dict(host.claims)}")
        print(f"Invariants: {sorted(host.invariants)}")
        if last_result:
            print(
                f"Last Move Decision: {last_result.get('decision')} - {last_result.get('message', '')}"
            )


def run_scenario_with_feedback(
    scenario_num: int, host: EducationalHostGovernor
) -> Tuple[Dict[str, Any], str]:
    """Execute a canonical test scenario and return decision receipt and educational commentary."""
    if scenario_num == 1:
        res = host.execute_move({"move_type": "ASSERT", "payload": {"relation": "TREE_SPAN_0_1_2"}})
        commentary = (
            "Scenario 1: ASSERT Move\n"
            "The player declares relation 'TREE_SPAN_0_1_2'. The host admits this relation without changing "
            "edge claims or defect Φ₁. Turn fuel decrements by 1."
        )
    elif scenario_num == 2:
        res = host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -1}}})
        commentary = (
            "Scenario 2: Valid Descending CUT\n"
            "The player updates edge '2->0' from claim 3 to -1. Circulation changes from (2 + 1 + 3 = 6) to "
            "(2 + 1 + (-1) = 2). Since 2 < 6, strict Lyapunov descent holds and the move is ADMITTED."
        )
    elif scenario_num == 3:
        res = host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": 7}}})
        commentary = (
            "Scenario 3: Non-Monotonic CUT (Adversarial Trap)\n"
            "The player attempts to set edge '2->0' to 7, which would increase circulation to 10. "
            "The host detects new_defect (10) >= old_defect (6), triggers atomic ROLLBACK of claims, "
            "and decrements turn fuel as an anti-spam penalty."
        )
    elif scenario_num == 4:
        res = host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"3->4": 0}}})
        commentary = (
            "Scenario 4: Carrier Domain Smuggling\n"
            "The player attempts to introduce claim on edge '3->4', which is outside the pinned carrier {0->1, 1->2, 2->0}. "
            "FW-CARRIER immediately refuses the proposal with REFUSED_CARRIER_DOMAIN."
        )
    elif scenario_num == 5:
        res = host.execute_move({"move_type": "VERIFY", "payload": {}})
        commentary = (
            "Scenario 5: Premature VERIFY Attempt\n"
            "The player calls VERIFY while defect Φ₁ > 0. The host refuses the verification request with "
            "REFUSED_NONZERO_DEFECT and leaves the board unsealed."
        )
    elif scenario_num == 6:
        host.execute_move(
            {"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -3}}}
        )
        res = host.execute_move({"move_type": "VERIFY", "payload": {}})
        commentary = (
            "Scenario 6: Exact Chord CUT & Terminal Certification\n"
            "The player sets '2->0' to -3, yielding exact circulation 2 + 1 + (-3) = 0. "
            "Calling VERIFY then succeeds with ACCEPTED_ZERO_DEFECT, permanently sealing the board and emitting "
            "a certified terminal receipt."
        )
    elif scenario_num == 7:
        if not host.is_terminal:
            host.execute_move(
                {"move_type": "CUT", "payload": {"proposed_claims": {"2->0": -3}}}
            )
            host.execute_move({"move_type": "VERIFY", "payload": {}})
        res = host.execute_move({"move_type": "CUT", "payload": {"proposed_claims": {"2->0": 0}}})
        commentary = (
            "Scenario 7: Post-Terminal Mutation Rejection\n"
            "The player attempts to alter claims on a sealed, certified board. "
            "The host rejects the mutation with REFUSED_TERMINAL_STATE, enforcing immutability."
        )
    else:
        res = {"decision": "REFUSED_UNKNOWN_SCENARIO", "fuel_remaining": host.fuel}
        commentary = f"Unknown scenario number {scenario_num}."

    return res, commentary


def create_interactive_game_widget(host: Optional[EducationalHostGovernor] = None) -> Any:
    """Build an interactive ipywidgets control panel for live browser sessions."""
    if not HAS_IPYTHON or widgets is None:
        print("Note: ipywidgets is not installed; running in text output mode.")
        return None

    if host is None:
        host = EducationalHostGovernor(
            vertices=[0, 1, 2],
            edges=["0->1", "1->2", "2->0"],
            initial_claims={"0->1": 2, "1->2": 1, "2->0": 3},
            fuel=8,
        )

    # UI Controls
    move_dropdown = widgets.Dropdown(
        options=[
            ("1. ASSERT (Declare Invariant)", "ASSERT"),
            ("2. CUT (Propose Edge Claims)", "CUT"),
            ("3. VERIFY (Request Certification)", "VERIFY"),
            ("4. RETRACT (Step Back)", "RETRACT"),
        ],
        value="CUT",
        description="Move Type:",
        style={"description_width": "110px"},
        layout=widgets.Layout(width="340px"),
    )

    edge_dropdown = widgets.Dropdown(
        options=["2->0", "0->1", "1->2", "3->4 (Smuggle Test)"],
        value="2->0",
        description="Target Edge:",
        style={"description_width": "110px"},
        layout=widgets.Layout(width="340px"),
    )

    claim_slider = widgets.IntSlider(
        value=-1,
        min=-10,
        max=10,
        step=1,
        description="Claim Value:",
        style={"description_width": "110px"},
        layout=widgets.Layout(width="340px"),
    )

    relation_text = widgets.Text(
        value="TREE_SPAN_0_1_2",
        placeholder="Enter invariant name",
        description="Invariant:",
        style={"description_width": "110px"},
        layout=widgets.Layout(width="340px"),
    )

    execute_btn = widgets.Button(
        description="Execute Move",
        button_style="primary",
        icon="play",
        layout=widgets.Layout(width="180px"),
    )

    reset_btn = widgets.Button(
        description="Reset Board",
        button_style="warning",
        icon="rotate-left",
        layout=widgets.Layout(width="140px"),
    )

    # Scenario Shortcuts
    sc1_btn = widgets.Button(
        description="Scenario 1: ASSERT", button_style="info", layout=widgets.Layout(width="170px")
    )
    sc2_btn = widgets.Button(
        description="Scenario 2: Valid CUT",
        button_style="success",
        layout=widgets.Layout(width="170px"),
    )
    sc3_btn = widgets.Button(
        description="Scenario 3: Bad CUT",
        button_style="danger",
        layout=widgets.Layout(width="170px"),
    )
    sc4_btn = widgets.Button(
        description="Scenario 4: Carrier Smuggle",
        button_style="danger",
        layout=widgets.Layout(width="170px"),
    )
    sc5_btn = widgets.Button(
        description="Scenario 5: Early VERIFY",
        button_style="warning",
        layout=widgets.Layout(width="170px"),
    )
    sc6_btn = widgets.Button(
        description="Scenario 6: Win & Certify",
        button_style="success",
        layout=widgets.Layout(width="170px"),
    )
    sc7_btn = widgets.Button(
        description="Scenario 7: Post-Seal Mutate",
        button_style="danger",
        layout=widgets.Layout(width="170px"),
    )
    run_all_btn = widgets.Button(
        description="Run Full Battery",
        button_style="primary",
        icon="check-double",
        layout=widgets.Layout(width="170px"),
    )

    output_area = widgets.Output()

    def update_control_visibility(change: Any) -> None:
        m = move_dropdown.value
        if m == "ASSERT":
            relation_text.layout.display = "flex"
            edge_dropdown.layout.display = "none"
            claim_slider.layout.display = "none"
        elif m == "CUT":
            relation_text.layout.display = "none"
            edge_dropdown.layout.display = "flex"
            claim_slider.layout.display = "flex"
        else:
            relation_text.layout.display = "none"
            edge_dropdown.layout.display = "none"
            claim_slider.layout.display = "none"

    move_dropdown.observe(update_control_visibility, names="value")
    update_control_visibility(None)

    def refresh_display(last_res: Optional[Dict[str, Any]] = None, message: str = "") -> None:
        with output_area:
            clear_output(wait=True)
            if message:
                print(message)
            display(HTML(render_html_board(host, last_res)))
            display(SVG(render_svg_triangle(host)))

    def on_execute_click(b: Any) -> None:
        m = move_dropdown.value
        if m == "ASSERT":
            prop = {"move_type": "ASSERT", "payload": {"relation": relation_text.value.strip()}}
        elif m == "CUT":
            edge = edge_dropdown.value.split()[0]
            prop = {"move_type": "CUT", "payload": {"proposed_claims": {edge: claim_slider.value}}}
        elif m == "VERIFY":
            prop = {"move_type": "VERIFY", "payload": {}}
        elif m == "RETRACT":
            prop = {"move_type": "RETRACT", "payload": {}}
        else:
            prop = {"move_type": "UNKNOWN"}

        res = host.execute_move(prop)
        refresh_display(res)

    def on_reset_click(b: Any) -> None:
        nonlocal host
        host = EducationalHostGovernor(
            vertices=[0, 1, 2],
            edges=["0->1", "1->2", "2->0"],
            initial_claims={"0->1": 2, "1->2": 1, "2->0": 3},
            fuel=8,
        )
        refresh_display(message="Board reset to initial state (Φ₁ = 6, Fuel = 8).")

    def make_scenario_handler(sc_num: int):
        def handler(b: Any) -> None:
            res, comm = run_scenario_with_feedback(sc_num, host)
            refresh_display(res, message=comm)

        return handler

    def on_run_all(b: Any) -> None:
        on_reset_click(None)
        from test_how_to_play_scenarios import TestSymbolGameHowToPlay

        suite = unittest.TestLoader().loadTestsFromTestCase(TestSymbolGameHowToPlay)
        runner = unittest.TextTestRunner(verbosity=1)
        res = runner.run(suite)
        status_msg = f"Automated Test Battery: {res.testsRun} tests run, {len(res.errors)} errors, {len(res.failures)} failures."
        refresh_display(message=status_msg)

    execute_btn.on_click(on_execute_click)
    reset_btn.on_click(on_reset_click)
    sc1_btn.on_click(make_scenario_handler(1))
    sc2_btn.on_click(make_scenario_handler(2))
    sc3_btn.on_click(make_scenario_handler(3))
    sc4_btn.on_click(make_scenario_handler(4))
    sc5_btn.on_click(make_scenario_handler(5))
    sc6_btn.on_click(make_scenario_handler(6))
    sc7_btn.on_click(make_scenario_handler(7))
    run_all_btn.on_click(on_run_all)

    # Initial render
    refresh_display()

    # Layout container
    panel = widgets.VBox(
        [
            widgets.HTML(
                "<h3 style='margin: 0 0 8px 0; color: #0f172a;'>Symbol Game Interactive Player Workbench</h3>"
            ),
            widgets.HBox(
                [
                    widgets.VBox(
                        [
                            widgets.HTML("<b>Move Builder:</b>"),
                            move_dropdown,
                            relation_text,
                            edge_dropdown,
                            claim_slider,
                            widgets.HBox([execute_btn, reset_btn]),
                        ],
                        layout=widgets.Layout(
                            padding="10px",
                            background="#f8fafc",
                            border="1px solid #e2e8f0",
                            border_radius="8px",
                        ),
                    ),
                    widgets.VBox(
                        [
                            widgets.HTML("<b>Scenario Fast-Triggers:</b>"),
                            widgets.HBox([sc1_btn, sc2_btn]),
                            widgets.HBox([sc3_btn, sc4_btn]),
                            widgets.HBox([sc5_btn, sc6_btn]),
                            widgets.HBox([sc7_btn, run_all_btn]),
                        ],
                        layout=widgets.Layout(
                            padding="10px",
                            background="#f8fafc",
                            border="1px solid #e2e8f0",
                            border_radius="8px",
                        ),
                    ),
                ]
            ),
            output_area,
        ]
    )

    return panel
