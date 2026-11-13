"""Generate the package figure public_export/fig1_descent_and_obstruction.png.

Panel (a) replays admitted CUTs on the manuscript triangle (reports (1, 1, 1),
penalties (1, 2, 3)): the proposal cost D_c(s) falls 6, 5, 4, 3 and stops at the
fixed quotient minimum Phi(c) = 3. Panel (b) replays the single-edge sequence
whose costs 2^-t decrease strictly but never reach the minimum 0 within fuel.

Every plotted value is computed by symbol_game_governor with exact Fractions and
converted to float only for drawing. The PNG carries no software or time
metadata, so reruns with the same matplotlib version give identical bytes. The
script fails if matplotlib is missing rather than writing a placeholder image.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from symbol_game_governor import ConstraintGraph, Edge, MoveType, SymbolGameGovernor  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[1] / "public_export" / "fig1_descent_and_obstruction.png"
TRIANGLE_PATH = [(-1, 0), (-1, -1), (-2, -1)]  # successive (s_b, s_c) with s_a = 0
FUEL = 10


def triangle_series() -> tuple[list[Fraction], Fraction]:
    graph = ConstraintGraph(("a", "b", "c"), (Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 3)))
    governor = SymbolGameGovernor(graph, {("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1})
    costs = [governor.compute_section_defect(governor.section)]
    phi = governor.compute_phi_1()[0]
    for s_b, s_c in TRIANGLE_PATH:
        step = governor.execute_move(MoveType.CUT, {"potentials": {"b": s_b, "c": s_c}})
        if not step.admitted or step.phi_1 != phi:
            raise RuntimeError(f"triangle replay diverged at {(s_b, s_c)}: {step.feedback}")
        costs.append(step.defect)
    if costs != [6, 5, 4, 3] or phi != 3:
        raise RuntimeError(f"unexpected triangle costs {costs} or minimum {phi}")
    return costs, phi


def rational_series() -> list[Fraction]:
    governor = SymbolGameGovernor(ConstraintGraph(("a", "b"), (Edge("a", "b", 1),)), {("a", "b"): 1})
    costs = [governor.compute_section_defect(governor.section)]
    for t in range(1, FUEL + 1):
        step = governor.execute_move(MoveType.CUT, {"potentials": {"b": 1 - Fraction(1, 2**t)}})
        if not step.admitted:
            raise RuntimeError(f"rational replay refused at t={t}: {step.feedback}")
        costs.append(step.defect)
    if costs != [Fraction(1, 2**t) for t in range(FUEL + 1)]:
        raise RuntimeError("unexpected rational descent costs")
    return costs


def generate_fig1() -> Path:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise SystemExit(f"matplotlib is required to generate {OUTPUT.name}: {error}")

    triangle, phi = triangle_series()
    rational = rational_series()

    fig, (left, right) = plt.subplots(1, 2, figsize=(8.0, 3.2), dpi=200)
    steps = list(range(len(triangle)))
    left.step(steps, [float(x) for x in triangle], where="post", color="#1f4e79", linewidth=1.6)
    left.plot(steps, [float(x) for x in triangle], "o", color="#1f4e79", markersize=5, label=r"admitted cost $D_c(s_t)$")
    left.axhline(float(phi), color="#b03a2e", linestyle="--", linewidth=1.2, label=r"quotient minimum $\Phi(c)=3$")
    for t, value in zip(steps, triangle):
        left.annotate(str(value), (t, float(value)), textcoords="offset points", xytext=(6, 5), ha="left", fontsize=8)
    left.set_xticks(steps)
    left.set_xlabel("admitted CUT")
    left.set_ylabel("weighted residual cost")
    left.set_ylim(0, 7)
    left.set_title("(a) triangle: descent stops at the fixed minimum", fontsize=9)
    left.legend(fontsize=7, loc="lower left")

    ticks = list(range(len(rational)))
    right.plot(ticks, [float(x) for x in rational], "o-", color="#1f4e79", markersize=4, linewidth=1.2,
               label=r"admitted cost $2^{-t}$")
    right.axhline(0.0, color="#b03a2e", linestyle="--", linewidth=1.2, label=r"minimum $\Phi(c)=0$")
    right.annotate(f"fuel exhausted: cost {rational[-1]} > 0", (ticks[-1], float(rational[-1])),
                   textcoords="offset points", xytext=(-4, 22), ha="right", fontsize=7,
                   arrowprops={"arrowstyle": "->", "linewidth": 0.8})
    right.set_xticks(ticks[::2])
    right.set_xlabel("attempt t (fuel 10)")
    right.set_ylim(-0.05, 1.1)
    right.set_title("(b) one edge: strict descent without termination", fontsize=9)
    right.legend(fontsize=7, loc="upper right")

    fig.tight_layout()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=200, metadata={"Software": None})
    plt.close(fig)
    print(f"Generated figure: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    generate_fig1()
