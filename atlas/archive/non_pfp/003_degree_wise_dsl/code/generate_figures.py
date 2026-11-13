"""Figure generation for Paper 009: Degree-Wise Obstruction Calculus and Symbolic DSL.

Plots the graded cell complex C^0 -> C^1 -> C^2 on C_3 and illustrates the
degree separation boundary between C^1 edge data and C^2 closure defects.

AuthorityEffect: None.
"""

from __future__ import annotations

import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC_EXPORT = PACKAGE_ROOT / "public_export"


def generate_fig1() -> pathlib.Path:
    PUBLIC_EXPORT.mkdir(parents=True, exist_ok=True)
    out_path = PUBLIC_EXPORT / "fig1_overview.png"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=300)

    # Panel 1: Graph-Only Model (No 2-cell)
    # C3 vertices on unit circle
    angles = np.array([np.pi / 2, np.pi / 2 + 2 * np.pi / 3, np.pi / 2 + 4 * np.pi / 3])
    vx = np.cos(angles)
    vy = np.sin(angles)

    ax1.set_title("(a) Graph-Only Model (C^1 Data Only)\nPhi_1 = 1.0, Gamma_2 = UNDEFINED", fontsize=11, fontweight="bold")
    for i in range(3):
        nxt = (i + 1) % 3
        ax1.annotate(
            "",
            xy=(vx[nxt], vy[nxt]),
            xytext=(vx[i], vy[i]),
            arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=2, shrinkA=10, shrinkB=10),
        )
        mid_x = (vx[i] + vx[nxt]) / 2 + (0.1 if i == 0 else -0.1 if i == 1 else 0.0)
        mid_y = (vy[i] + vy[nxt]) / 2 + (0.05 if i != 2 else -0.12)
        val = "omega_0 = 1" if i == 0 else f"omega_{i} = 0"
        ax1.text(mid_x, mid_y, val, color="#1f77b4", fontweight="bold", ha="center")

    ax1.scatter(vx, vy, s=300, color="#2ca02c", zorder=5)
    for i, (x, y) in enumerate(zip(vx, vy)):
        ax1.text(x, y, f"v_{i}", color="white", fontweight="bold", ha="center", va="center", zorder=6)

    ax1.text(0, 0, "No 2-Cell Attached\n(C^2 = {0}, d_1 absent)", ha="center", va="center", color="#7f7f7f", style="italic")
    ax1.set_xlim(-1.5, 1.5)
    ax1.set_ylim(-1.3, 1.3)
    ax1.set_aspect("equal")
    ax1.axis("off")

    # Panel 2: Cellular Complex with Attached 2-Cell
    ax2.set_title("(b) Cellular Complex with 2-Cell sigma\nPhi_1 = 1.0, Gamma_2 = 1.0 (Visible)", fontsize=11, fontweight="bold")
    tri = plt.Polygon(np.column_stack([vx, vy]), closed=True, color="#ff7f0e", alpha=0.25, zorder=2)
    ax2.add_patch(tri)

    for i in range(3):
        nxt = (i + 1) % 3
        ax2.annotate(
            "",
            xy=(vx[nxt], vy[nxt]),
            xytext=(vx[i], vy[i]),
            arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=2, shrinkA=10, shrinkB=10),
        )
        mid_x = (vx[i] + vx[nxt]) / 2 + (0.1 if i == 0 else -0.1 if i == 1 else 0.0)
        mid_y = (vy[i] + vy[nxt]) / 2 + (0.05 if i != 2 else -0.12)
        val = "h_0 = 1" if i == 0 else f"h_{i} = 0"
        ax2.text(mid_x, mid_y, val, color="#1f77b4", fontweight="bold", ha="center")

    ax2.scatter(vx, vy, s=300, color="#2ca02c", zorder=5)
    for i, (x, y) in enumerate(zip(vx, vy)):
        ax2.text(x, y, f"v_{i}", color="white", fontweight="bold", ha="center", va="center", zorder=6)

    ax2.text(0, 0, "2-Cell sigma Attached\nd_1 = [1, 1, 1]\nGamma_2 = |1+0+0| = 1", ha="center", va="center", color="#d62728", fontweight="bold")
    ax2.set_xlim(-1.5, 1.5)
    ax2.set_ylim(-1.3, 1.3)
    ax2.set_aspect("equal")
    ax2.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


if __name__ == "__main__":
    p = generate_fig1()
    print(f"Generated {p}")
