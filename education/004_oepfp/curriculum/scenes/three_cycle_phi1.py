"""Track A video 3 — one directed 3-cycle; coboundary; Phi_1 = 3.

The graph is Paper 033 `play_demo.py`: vertices a,b,c; edges
a->b (weight 1), b->c (weight 2), c->a (weight 2); claims (1,1,1).
The host reports Phi_1 = 3. This file does not reimplement that norm:
it calls the SHA-256-pinned canonical Rust graph evaluator.

This is a different graph from notebook 05's opening cell (the chorded
triangle A,B,C with a chord A->C). Do not film them as the same example.

Render without Manim (matplotlib + ffmpeg):

    python notebooks/scenes/three_cycle_phi1.py

Optional Manim Community (needs a separate install; this repo does not
pin it, and the notebook tests do not import it):

    manim -pql notebooks/scenes/three_cycle_phi1.py ThreeCyclePhi1

AuthorityEffect: None.
"""

from __future__ import annotations

import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Dict, Tuple


def _find_repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[3]


_ROOT = _find_repo_root()
_SCENES = Path(__file__).resolve().parent


if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from omega_engine_woland.infrastructure.providers.adapters.native_functional import compute_graph_phi1

# Exact play_demo.py carrier. Claims are all 1; holonomy 1+1+1 = 3.
PLAY_VERTICES: Tuple[str, ...] = ("a", "b", "c")
PLAY_EDGES: Tuple[Tuple[str, str, int], ...] = (
    ("a", "b", 1),
    ("b", "c", 2),
    ("c", "a", 2),
)
PLAY_CLAIMS: Dict[Tuple[str, str], Fraction] = {
    ("a", "b"): Fraction(1),
    ("b", "c"): Fraction(1),
    ("c", "a"): Fraction(1),
}
TRANSFER_CLAIMS: Dict[Tuple[str, str], Fraction] = {
    ("a", "b"): Fraction(1),
    ("b", "c"): Fraction(1),
    ("c", "a"): Fraction(-2),
}


def phi1_of(claims: Dict[Tuple[str, str], Fraction]) -> Tuple[Fraction, Dict[str, Fraction]]:
    """Phi_1 of `claims` on the play_demo carrier, computed by the native Rust functional."""
    return compute_graph_phi1(PLAY_VERTICES, PLAY_EDGES, dict(claims))


def cycle_sum(claims: Dict[Tuple[str, str], Fraction]) -> Fraction:
    return claims[("a", "b")] + claims[("b", "c")] + claims[("c", "a")]


def host_verdict(phi: Fraction) -> str:
    return "CONSISTENT" if phi == 0 else "CONTRADICTION"


# ---------------------------------------------------------------------------
# matplotlib renderer (ships the video without pinning Manim)
# ---------------------------------------------------------------------------

_BG = "#10141a"
_INK = "#e8e6e3"
_MUTED = "#9aa3ad"
_EDGE = "#6cb3ff"
_BAD = "#e85d4c"
_GOLD = "#f0c14a"


def _vertex_xy() -> Dict[str, Tuple[float, float]]:
    # Equilateral triangle, a at the top.
    r = 1.0
    return {
        "a": (0.0, r),
        "b": (r * math.sqrt(3) / 2, -r / 2),
        "c": (-r * math.sqrt(3) / 2, -r / 2),
    }


def render_mp4(out_path: Path | None = None, fps: int = 12) -> Path:
    """Write a ~24s single-example clip. Discrete decisions stay on Fraction."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation
    from matplotlib.patches import Circle, FancyArrowPatch

    phi, gauge = phi1_of(PLAY_CLAIMS)
    if phi != Fraction(3):
        raise RuntimeError(f"pinned compute_phi1 returned {phi}, expected 3")
    verdict = host_verdict(phi)

    if out_path is None:
        out_path = _SCENES / "_render" / "03_three_cycle_phi1.mp4"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    duration_s = 24
    n_frames = duration_s * fps
    pos = _vertex_xy()

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.set_xlim(-2.35, 2.35)
    ax.set_ylim(-1.85, 1.95)
    ax.set_aspect("equal")
    ax.axis("off")

    title = ax.text(
        0.0,
        1.72,
        "One 3-cycle",
        ha="center",
        va="center",
        color=_INK,
        fontsize=22,
        fontweight="bold",
    )
    subtitle = ax.text(
        0.0,
        1.48,
        "",
        ha="center",
        va="center",
        color=_MUTED,
        fontsize=13,
    )
    cannot = ax.text(
        0.0,
        -1.68,
        "",
        ha="center",
        va="center",
        color=_MUTED,
        fontsize=11,
        wrap=True,
    )
    phi_text = ax.text(
        1.85,
        0.15,
        "",
        ha="center",
        va="center",
        color=_GOLD,
        fontsize=16,
        fontweight="bold",
    )
    verdict_text = ax.text(
        1.85,
        -0.15,
        "",
        ha="center",
        va="center",
        color=_BAD,
        fontsize=14,
        fontweight="bold",
    )

    vertex_patches = {}
    vertex_labels = {}
    for name, (x, y) in pos.items():
        circ = Circle((x, y), 0.16, facecolor="#1c2430", edgecolor=_INK, lw=1.6, zorder=5)
        ax.add_patch(circ)
        vertex_patches[name] = circ
        vertex_labels[name] = ax.text(
            x,
            y,
            name,
            ha="center",
            va="center",
            color=_INK,
            fontsize=14,
            fontweight="bold",
            zorder=6,
        )
        circ.set_visible(False)
        vertex_labels[name].set_visible(False)

    edge_artists = {}
    claim_labels = {}
    for u, v, _w in PLAY_EDGES:
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        shrink = 0.20 / length
        start = (x0 + dx * shrink, y0 + dy * shrink)
        end = (x1 - dx * shrink, y1 - dy * shrink)
        arrow = FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=16,
            lw=2.2,
            color=_EDGE,
            zorder=3,
        )
        ax.add_patch(arrow)
        arrow.set_visible(False)
        edge_artists[(u, v)] = arrow
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        nx, ny = -dy / length * 0.18, dx / length * 0.18
        claim_labels[(u, v)] = ax.text(
            mx + nx,
            my + ny,
            "",
            ha="center",
            va="center",
            color=_INK,
            fontsize=12,
            zorder=4,
        )

    walk_marker = ax.text(0.0, -1.38, "", ha="center", va="center", color=_GOLD, fontsize=14)

    def _show_vertices(on: bool) -> None:
        for name in PLAY_VERTICES:
            vertex_patches[name].set_visible(on)
            vertex_labels[name].set_visible(on)

    def _show_edges(on: bool) -> None:
        for key, art in edge_artists.items():
            art.set_visible(on)

    def t_of(frame: int) -> float:
        return frame / fps

    def update(frame: int):
        t = t_of(frame)
        _show_vertices(t >= 1.0)
        _show_edges(t >= 4.0)

        if t < 4.0:
            title.set_text("One 3-cycle")
            subtitle.set_text("C⁰  —  potentials on vertices {a, b, c}")
        elif t < 8.0:
            title.set_text("Coboundary  δ : C⁰ → C¹")
            subtitle.set_text("(δf)(u → v)  =  f(v) − f(u)     cycle sum of every coboundary is 0")
        elif t < 13.0:
            title.set_text("Claims  c  =  (1, 1, 1)")
            subtitle.set_text("a 1-cochain, not a potential  —  each edge asserts 1")
            for key, lab in claim_labels.items():
                lab.set_text(f"c = {PLAY_CLAIMS[key]}")
        elif t < 18.0:
            title.set_text("Walk the cycle")
            subtitle.set_text("a → b → c → a")
            walk_marker.set_text("1  +  1  +  1  =  3  ≠  0")
            for art in edge_artists.values():
                art.set_color(_BAD)
        else:
            title.set_text("Not a coboundary")
            subtitle.set_text(
                "host reports a positive obstruction  —  Φ₁ = 3 here only because the lightest edge is weight 1"
            )
            walk_marker.set_text("1  +  1  +  1  =  3  ≠  0")
            phi_text.set_text(f"Φ₁ = {phi}")
            verdict_text.set_text(verdict)
            cannot.set_text(
                "CANNOT: one finite weighted graph. Not a claim that language models are cochain complexes."
            )
            for art in edge_artists.values():
                art.set_color(_BAD)

        return []

    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(
        fps=fps, metadata={"title": "Track A video 3: one 3-cycle", "artist": "the_symbol_game"}
    )
    anim.save(str(out_path), writer=writer)
    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# Optional Manim scene (same example, same numbers)
# ---------------------------------------------------------------------------

try:
    from manim import DOWN, UP, WHITE, Arrow, Circle, Create, FadeIn, Scene, Text, VGroup
except ImportError:  # pragma: no cover - Manim is not a notebook dependency
    Scene = object  # type: ignore[misc,assignment]
else:

    class ThreeCyclePhi1(Scene):
        """Same play_demo 3-cycle. Run only if Manim Community is installed."""

        def construct(self):
            phi, _gauge = phi1_of(PLAY_CLAIMS)
            title = Text("One 3-cycle", color=WHITE).scale(0.7).to_edge(UP)
            self.play(FadeIn(title))

            coords = {
                "a": [0, 1.4, 0],
                "b": [1.4, -0.8, 0],
                "c": [-1.4, -0.8, 0],
            }
            dots = VGroup()
            labels = VGroup()
            for name, xyz in coords.items():
                dot = Circle(radius=0.18, color=WHITE).move_to(xyz)
                lab = Text(name, color=WHITE).scale(0.4).move_to(xyz)
                dots.add(dot)
                labels.add(lab)
            self.play(FadeIn(dots), FadeIn(labels))
            cob = Text("(df)(u->v) = f(v) - f(u)", color=WHITE).scale(0.35).next_to(title, DOWN)
            self.play(FadeIn(cob))

            arrows = VGroup()
            for u, v, _w in PLAY_EDGES:
                arrows.add(Arrow(coords[u], coords[v], buff=0.22, color=WHITE))
            self.play(Create(arrows))
            claims = Text("c = (1, 1, 1)", color=WHITE).scale(0.4).to_edge(DOWN)
            self.play(FadeIn(claims))
            walk = Text("1 + 1 + 1 = 3 != 0", color=WHITE).scale(0.45).next_to(claims, UP)
            self.play(FadeIn(walk))
            result = Text(f"Phi_1 = {phi}    CONTRADICTION", color=WHITE).scale(0.45)
            result.next_to(walk, UP)
            self.play(FadeIn(result))
            fence = (
                Text(
                    "CANNOT: one finite weighted graph, not a claim that LLMs are cochain complexes.",
                    color=WHITE,
                )
                .scale(0.28)
                .to_edge(DOWN)
            )
            self.play(FadeIn(fence))
            self.wait(2)


def main() -> None:
    phi, gauge = phi1_of(PLAY_CLAIMS)
    print(f"[Pinned] compute_phi1 play_demo cycle -> Phi_1 = {phi}, gauge = {gauge}")
    print(f"[Pinned] cycle sum = {cycle_sum(PLAY_CLAIMS)}, verdict = {host_verdict(phi)}")
    t_phi, t_gauge = phi1_of(TRANSFER_CLAIMS)
    print(f"[Pinned] one-parameter transfer c(c->a)=-2 -> Phi_1 = {t_phi}, gauge = {t_gauge}")
    path = render_mp4()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
