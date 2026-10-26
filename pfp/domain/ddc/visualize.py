"""Interactive visualization and telemetry export helpers for Discrete Deformation Calculus.

Provides export functions for:
1. Cochain graph topology, node potentials, edge claims, residuals, and dual circulations.
2. Step-by-step Lyapunov descent trajectories (Phi_1, Gamma_2, Xi, V = Phi_1 + Gamma_2).
3. Graphviz DOT format for topological diagrams.
4. ASCII descent curves for headless CLI audits.
5. Optional Matplotlib figure exports for interactive notebooks.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Optional

from .coboundary import d0, d1
from .cochains import Cochain0, Cochain1
from .complex import SimplicialComplex
from .dda import LyapunovTracker


def export_cochain_graph_data(
    complex_: SimplicialComplex,
    cochain: Cochain1,
    potentials: Optional[Cochain0] = None,
    dual_circulation: Optional[Cochain1] = None,
) -> Dict[str, Any]:
    """Export cochain graph data as a JSON-serializable dictionary.

    Suitable for D3.js, Cytoscape, or interactive Jupyter widgets.
    """
    pot = potentials if potentials is not None else Cochain0.zero(complex_.vertices)
    dual = dual_circulation if dual_circulation is not None else Cochain1.zero([])

    nodes_data: List[Dict[str, Any]] = []
    for v in complex_.vertices:
        p_val = pot.get(v)
        nodes_data.append({
            "id": v,
            "potential_fraction": str(p_val),
            "potential_float": float(p_val),
        })

    edges_data: List[Dict[str, Any]] = []
    d0_pot = d0(complex_, pot)
    for e in complex_.edges:
        claim_val = cochain.get(e.u, e.v)
        gauge_diff = d0_pot.get(e.u, e.v)
        res_val = claim_val - gauge_diff
        dual_val = dual.get(e.u, e.v)
        edges_data.append({
            "source": e.u,
            "target": e.v,
            "weight": float(e.weight),
            "weight_fraction": str(e.weight),
            "claim_fraction": str(claim_val),
            "claim_float": float(claim_val),
            "gauge_diff_fraction": str(gauge_diff),
            "gauge_diff_float": float(gauge_diff),
            "residual_fraction": str(res_val),
            "residual_float": float(res_val),
            "dual_fraction": str(dual_val),
            "dual_float": float(dual_val),
        })

    faces_data: List[Dict[str, Any]] = []
    c2 = d1(complex_, cochain)
    for f in complex_.faces:
        curl_val = c2.get(f.u, f.v, f.w)
        faces_data.append({
            "vertices": [f.u, f.v, f.w],
            "curl_defect_fraction": str(curl_val),
            "curl_defect_float": float(curl_val),
        })

    return {
        "nodes": nodes_data,
        "edges": edges_data,
        "faces": faces_data,
        "summary": {
            "num_vertices": complex_.num_vertices,
            "num_edges": complex_.num_edges,
            # L1 norm and Gamma2 calculations belong to omega_functional, not this Python view.
            "cochain_l1_norm": None,
            "closure_defect_gamma2": None,
            "functional_status": "FUNCTIONAL_BOUNDARY_UNAVAILABLE",
        },
    }



def export_cochain_graph_dot(
    complex_: SimplicialComplex,
    cochain: Cochain1,
    potentials: Optional[Cochain0] = None,
) -> str:
    """Generate Graphviz DOT markup for visual inspection of the cochain complex."""
    pot = potentials if potentials is not None else Cochain0.zero(complex_.vertices)
    lines: List[str] = [
        "digraph DDC_Cochain {",
        "  rankdir=LR;",
        '  node [shape=circle, fontname="Helvetica", style=filled, fillcolor="#E8F0FE"];',
        '  edge [fontname="Helvetica", fontsize=10];',
    ]

    for v in complex_.vertices:
        p_val = pot.get(v)
        label = f"{v}\\nφ={p_val}"
        lines.append(f'  "{v}" [label="{label}"];')

    for e in complex_.edges:
        claim_val = cochain.get(e.u, e.v)
        w_val = e.weight
        label = f"c={claim_val}\\nw={w_val}"
        color = "#D93025" if claim_val != Fraction(0) else "#1E8E3E"
        lines.append(f'  "{e.u}" -> "{e.v}" [label="{label}", color="{color}"];')

    lines.append("}")
    return "\n".join(lines)


def export_lyapunov_descent_data(tracker: LyapunovTracker) -> Dict[str, Any]:
    """Export the Lyapunov descent trajectory as serializable time series."""
    steps: List[int] = []
    letters: List[str] = []
    phi_1_vals: List[float] = []
    gamma_2_vals: List[float] = []
    xi_vals: List[float] = []
    lyapunov_v: List[float] = []
    delta_phi: List[float] = []
    hashes: List[str] = []
    summaries: List[str] = []

    for n in tracker.nodes:
        steps.append(n.step_index)
        letters.append(n.letter.value)
        phi_1_vals.append(float(n.phi_1))
        gamma_2_vals.append(float(n.gamma_2))
        xi_vals.append(float(n.xi))
        lyapunov_v.append(float(n.phi_1 + n.gamma_2))
        delta_phi.append(float(n.delta_phi_1))
        hashes.append(n.state_hash)
        summaries.append(n.action_summary)

    return {
        "tape": tracker.tape,
        "is_strictly_monotonic": tracker.is_strictly_monotonic(),
        "total_steps": tracker.total_steps,
        "steps": steps,
        "letters": letters,
        "phi_1": phi_1_vals,
        "gamma_2": gamma_2_vals,
        "xi": xi_vals,
        "lyapunov_energy_v": lyapunov_v,
        "delta_phi_1": delta_phi,
        "state_hashes": hashes,
        "action_summaries": summaries,
    }


def render_lyapunov_descent_ascii(tracker: LyapunovTracker) -> str:
    """Render an ASCII table and bar chart showing Lyapunov descent across DDA steps."""
    if not tracker.nodes:
        return "Empty Lyapunov descent trace."

    lines: List[str] = [
        "================================================================================",
        "DDA EXECUTION TAPE: " + tracker.tape,
        "================================================================================",
        f"{'Step':<5} | {'Tok':<4} | {'Phi_1':<8} | {'Gamma_2':<8} | {'V=Phi+Gamma':<11} | {'Delta_Phi':<10} | {'Descent Bar'}",
        "--------------------------------------------------------------------------------",
    ]

    max_v = max(float(n.phi_1 + n.gamma_2) for n in tracker.nodes)
    scale = 20.0 / (max_v if max_v > 0 else 1.0)

    for n in tracker.nodes:
        v_float = float(n.phi_1 + n.gamma_2)
        bar_len = int(round(v_float * scale))
        bar = "#" * bar_len
        lines.append(
            f"{n.step_index:<5} | {n.letter.value:<4} | {float(n.phi_1):<8.4f} | "
            f"{float(n.gamma_2):<8.4f} | {v_float:<11.4f} | {float(n.delta_phi_1):<+10.4f} | {bar}"
        )

    lines.append("================================================================================")
    return "\n".join(lines)


from typing import Protocol, runtime_checkable


@runtime_checkable
class LyapunovPlotRendererPort(Protocol):
    """Domain protocol for rendering Lyapunov descent plots."""

    def __call__(
        self,
        tracker: LyapunovTracker,
        filepath: Optional[str] = None,
    ) -> Any: ...


_PLOT_RENDERER: Optional[LyapunovPlotRendererPort] = None


def register_lyapunov_plot_renderer(renderer: LyapunovPlotRendererPort) -> None:
    """Register an adapter for rendering Lyapunov plots."""
    global _PLOT_RENDERER
    _PLOT_RENDERER = renderer


def get_lyapunov_plot_renderer() -> Optional[LyapunovPlotRendererPort]:
    """Retrieve the registered renderer, falling back to infrastructure adapter."""
    global _PLOT_RENDERER
    if _PLOT_RENDERER is None:
        try:
            import importlib
            adapter_mod = importlib.import_module(
                "omega_engine_pfp.infrastructure.adapters.ddc_plot_adapter"
            )
            _PLOT_RENDERER = getattr(adapter_mod, "render_lyapunov_descent_plot")
        except Exception:
            return None
    return _PLOT_RENDERER


def export_lyapunov_descent_plot(
    tracker: LyapunovTracker,
    filepath: Optional[str] = None,
    *,
    renderer: Optional[LyapunovPlotRendererPort] = None,
) -> Any:
    """Plot Lyapunov descent curves via the presentation adapter.

    Domain logic delegates to the presentation renderer port without directly importing matplotlib.
    Saves to filepath or returns the Figure object.
    """
    active_renderer = renderer if renderer is not None else get_lyapunov_plot_renderer()
    if active_renderer is None:
        return None
    return active_renderer(tracker, filepath)

