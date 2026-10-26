"""Presentation adapter for DDC Lyapunov descent visualization using Matplotlib.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Optional

from omega_engine_pfp.domain.ddc.visualize import (
    LyapunovTracker,
    export_lyapunov_descent_data,
)


def render_lyapunov_descent_plot(
    tracker: LyapunovTracker,
    filepath: Optional[str] = None,
) -> Any:
    """Plot Lyapunov descent curves using Matplotlib (if installed).

    Saves to filepath or returns the Figure object.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    data = export_lyapunov_descent_data(tracker)
    steps = data["steps"]
    phi_1 = data["phi_1"]
    gamma_2 = data["gamma_2"]
    v_energy = data["lyapunov_energy_v"]
    letters = data["letters"]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(steps, phi_1, "o-", color="#1A73E8", label=r"$\Phi_1$ (Quotient Defect)")
    ax.plot(steps, gamma_2, "s--", color="#EA4335", label=r"$\Gamma_2$ (Closure Defect)")
    ax.plot(steps, v_energy, "^-.", color="#34A853", label=r"$V = \Phi_1 + \Gamma_2$")

    for i, txt in enumerate(letters):
        ax.annotate(txt, (steps[i], v_energy[i]), textcoords="offset points", xytext=(0, 8), ha="center")

    ax.set_xlabel("DDA Step")
    ax.set_ylabel("Defect Mass")
    ax.set_title(f"Lyapunov Defect Descent (Tape: {data['tape']})")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend()
    plt.tight_layout()

    if filepath:
        fig.savefig(filepath, dpi=150)
    return fig


__all__ = ["render_lyapunov_descent_plot"]
