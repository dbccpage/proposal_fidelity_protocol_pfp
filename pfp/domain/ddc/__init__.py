"""Discrete Deformation Calculus (DDC) Domain Package.

Provides graded cochains (C^0, C^1, C^2), coboundary operators (d^0, d^1) with exact nilpotency,
historical defect-triad data types, the DDA 9-letter operational alphabet,
Lyapunov trace types, and visualization helpers. Python Phi1, Gamma2, and Xi
calculation entry points refuse until a Rust-backed adapter is available.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .coboundary import NilpotencyReceipt, audit_nilpotency_all_basis, d0, d1, verify_nilpotency
    from .cochains import Cochain0, Cochain1, Cochain2
    from .complex import Edge, Face, SimplicialComplex
    from .dda import CascadeResult, DDACascadeSolver, DDALetter, DDATraceNode, LyapunovTracker
    from .triad import DefectTriad, FunctionalBoundaryUnavailable, ObstructionTrichotomy, Phi1Certificate, compute_gamma2, compute_phi1, compute_xi, evaluate_defect_triad
    from .visualize import LyapunovPlotRendererPort, export_cochain_graph_data, export_cochain_graph_dot, export_lyapunov_descent_data, export_lyapunov_descent_plot, get_lyapunov_plot_renderer, register_lyapunov_plot_renderer, render_lyapunov_descent_ascii

__all__ = ['Edge', 'Face', 'SimplicialComplex', 'Cochain0', 'Cochain1', 'Cochain2', 'd0', 'd1', 'verify_nilpotency', 'audit_nilpotency_all_basis', 'NilpotencyReceipt', 'compute_phi1', 'compute_gamma2', 'compute_xi', 'evaluate_defect_triad', 'Phi1Certificate', 'DefectTriad', 'FunctionalBoundaryUnavailable', 'ObstructionTrichotomy', 'DDALetter', 'DDATraceNode', 'LyapunovTracker', 'DDACascadeSolver', 'CascadeResult', 'LyapunovPlotRendererPort', 'export_cochain_graph_data', 'export_cochain_graph_dot', 'export_lyapunov_descent_data', 'export_lyapunov_descent_plot', 'get_lyapunov_plot_renderer', 'register_lyapunov_plot_renderer', 'render_lyapunov_descent_ascii']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'NilpotencyReceipt': ('.coboundary', 'NilpotencyReceipt'),
    'audit_nilpotency_all_basis': ('.coboundary', 'audit_nilpotency_all_basis'),
    'd0': ('.coboundary', 'd0'),
    'd1': ('.coboundary', 'd1'),
    'verify_nilpotency': ('.coboundary', 'verify_nilpotency'),
    'Cochain0': ('.cochains', 'Cochain0'),
    'Cochain1': ('.cochains', 'Cochain1'),
    'Cochain2': ('.cochains', 'Cochain2'),
    'Edge': ('.complex', 'Edge'),
    'Face': ('.complex', 'Face'),
    'SimplicialComplex': ('.complex', 'SimplicialComplex'),
    'CascadeResult': ('.dda', 'CascadeResult'),
    'DDACascadeSolver': ('.dda', 'DDACascadeSolver'),
    'DDALetter': ('.dda', 'DDALetter'),
    'DDATraceNode': ('.dda', 'DDATraceNode'),
    'LyapunovTracker': ('.dda', 'LyapunovTracker'),
    'DefectTriad': ('.triad', 'DefectTriad'),
    'FunctionalBoundaryUnavailable': ('.triad', 'FunctionalBoundaryUnavailable'),
    'ObstructionTrichotomy': ('.triad', 'ObstructionTrichotomy'),
    'Phi1Certificate': ('.triad', 'Phi1Certificate'),
    'compute_gamma2': ('.triad', 'compute_gamma2'),
    'compute_phi1': ('.triad', 'compute_phi1'),
    'compute_xi': ('.triad', 'compute_xi'),
    'evaluate_defect_triad': ('.triad', 'evaluate_defect_triad'),
    'LyapunovPlotRendererPort': ('.visualize', 'LyapunovPlotRendererPort'),
    'export_cochain_graph_data': ('.visualize', 'export_cochain_graph_data'),
    'export_cochain_graph_dot': ('.visualize', 'export_cochain_graph_dot'),
    'export_lyapunov_descent_data': ('.visualize', 'export_lyapunov_descent_data'),
    'export_lyapunov_descent_plot': ('.visualize', 'export_lyapunov_descent_plot'),
    'get_lyapunov_plot_renderer': ('.visualize', 'get_lyapunov_plot_renderer'),
    'register_lyapunov_plot_renderer': ('.visualize', 'register_lyapunov_plot_renderer'),
    'render_lyapunov_descent_ascii': ('.visualize', 'render_lyapunov_descent_ascii'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
