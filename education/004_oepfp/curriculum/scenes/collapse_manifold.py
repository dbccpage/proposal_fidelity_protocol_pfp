"""Track A video 7 — one lattice: 125 → 19 RESIDUAL → 1 LANDED, or REFUSED_EMPTY.

Uses bench/packets/antimorphism.py on product(range(-2,3), repeat=3). Does not
re-code Φ₁: LAND_ON_ZERO(phi1_cycle) is the pinned filter. SHAPE.op is REDUCE;
DEMAND.op is DECIDE; LAND is LAND_ON_ZERO.

    python notebooks/scenes/collapse_manifold.py

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from itertools import product
from pathlib import Path


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[4]


_ROOT = _find_repo_root()
_PACKETS = _ROOT / "bench" / "packets"
_HERE = Path(__file__).resolve().parent
_SCENES = _HERE
_PACKETIZATION = _HERE.parent.parent / "packetization"


def _load_anti():
    for _dir in (_HERE, _PACKETIZATION, _PACKETS):
        if _dir.is_dir() and str(_dir) not in sys.path:
            sys.path.insert(0, str(_dir))
    from antimorphism import (  # noqa: WPS433
        DEMAND,
        LAND_ON_ZERO,
        PIN,
        SHAPE,
        collapse,
        collapse_adaptive,
        phi1_cycle,
    )

    return DEMAND, LAND_ON_ZERO, PIN, SHAPE, collapse, collapse_adaptive, phi1_cycle


DEMAND, LAND_ON_ZERO, PIN, SHAPE, collapse, collapse_adaptive, phi1_cycle = _load_anti()

K = 3
UNIVERSE = [tuple(t) for t in product(range(-2, 3), repeat=K)]


def base_ops():
    return [
        SHAPE(K),
        PIN(set("0123456789-"), render=lambda x: "".join(map(str, x))),
        LAND_ON_ZERO(phi1_cycle),
    ]


def traces() -> dict:
    residual = collapse(UNIVERSE, base_ops())

    def propose(a):
        if len(a) <= 1:
            return None
        return DEMAND("prefix", lambda x: tuple(x[:2]) == (1, -1))

    landed, issued = collapse_adaptive(UNIVERSE, base_ops(), propose)
    refused = collapse(UNIVERSE, base_ops() + [DEMAND("impossible", lambda x: sum(x) == 99)])
    witness = next(iter(landed.fixpoint)) if landed.verdict == "LANDED" else None
    return {
        "universe": len(UNIVERSE),
        "residual_sizes": residual.sizes,
        "residual_verdict": residual.verdict,
        "landed_sizes": landed.sizes,
        "landed_verdict": landed.verdict,
        "landed_witness": witness,
        "demands": len(issued),
        "refused_verdict": refused.verdict,
        "shape_op": SHAPE(K).op,
        "demand_op": DEMAND("prefix", lambda x: True).op,
        "land_op": LAND_ON_ZERO(phi1_cycle).op,
    }


def render_mp4(out_path: Path | None = None, fps: int = 12) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation
    from matplotlib.patches import FancyBboxPatch

    t = traces()
    if t["universe"] != 125 or t["residual_verdict"] != "RESIDUAL":
        raise RuntimeError(f"unexpected residual collapse: {t}")
    if t["landed_verdict"] != "LANDED" or t["landed_witness"] != (1, -1, 0):
        raise RuntimeError(f"unexpected landed collapse: {t}")
    if t["refused_verdict"] != "REFUSED_EMPTY":
        raise RuntimeError(f"unexpected refused collapse: {t}")

    if out_path is None:
        out_path = _SCENES / "_render" / "07_collapse_manifold.mp4"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bg, ink, muted = "#10141a", "#e8e6e3", "#9aa3ad"
    ok, bad, gold = "#6ec89b", "#e85d4c", "#f0c14a"
    _duration_s, n_frames = 26, 26 * fps

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    bar = FancyBboxPatch(
        (0.15, 0.42),
        0.70,
        0.12,
        boxstyle="round,pad=0.01",
        facecolor="#2a3340",
        edgecolor="#3d4a5c",
        lw=1.5,
    )
    ax.add_patch(bar)
    fill = FancyBboxPatch(
        (0.15, 0.42), 0.70, 0.12, boxstyle="round,pad=0.01", facecolor=gold, edgecolor="none"
    )
    ax.add_patch(fill)

    title = ax.text(
        0.5, 0.90, "", ha="center", va="center", color=ink, fontsize=22, fontweight="bold"
    )
    sub = ax.text(0.5, 0.82, "", ha="center", va="center", color=muted, fontsize=13)
    count = ax.text(
        0.5, 0.48, "", ha="center", va="center", color=bg, fontsize=22, fontweight="bold"
    )
    verdict = ax.text(
        0.5, 0.28, "", ha="center", va="center", color=gold, fontsize=18, fontweight="bold"
    )
    note = ax.text(0.5, 0.18, "", ha="center", va="center", color=ink, fontsize=13)
    fence = ax.text(0.5, 0.07, "", ha="center", va="center", color=muted, fontsize=11)

    def _bar_width(n: int) -> float:
        return 0.70 * (n / 125)

    def update(frame: int):
        tsec = frame / fps
        if tsec < 6:
            title.set_text("One lattice, 125 labelings")
            sub.set_text("k=3 cycle  ·  each edge in {−2,−1,0,1,2}  ·  5³ = 125")
            fill.set_width(0.70)
            fill.set_facecolor("#6cb3ff")
            count.set_text("125")
            verdict.set_text("")
            note.set_text("SHAPE (REDUCE) · PIN · LAND_ON_ZERO")
            fence.set_text("")
        elif tsec < 13:
            title.set_text("Filters collapse the set")
            sub.set_text("keep Φ₁ = 0  ·  order-independent core")
            fill.set_width(_bar_width(19))
            fill.set_facecolor(gold)
            count.set_text("19")
            verdict.set_color(gold)
            verdict.set_text("RESIDUAL")
            note.set_text("19 zero-holonomy labelings remain  —  under-determined")
            fence.set_text("")
        elif tsec < 20:
            title.set_text("One residual-derived DEMAND")
            sub.set_text("prefix (1, −1)  ·  op = DECIDE")
            fill.set_width(_bar_width(1))
            fill.set_facecolor(ok)
            count.set_text("1")
            verdict.set_color(ok)
            verdict.set_text("LANDED")
            note.set_text("witness (1, −1, 0)  ·  Φ₁ = 0")
            fence.set_text("")
        else:
            title.set_text("Impossible DEMAND is an honest no")
            sub.set_text("sum == 99 is unsatisfiable on this carrier")
            fill.set_width(0.02)
            fill.set_facecolor(bad)
            count.set_text("0")
            verdict.set_color(bad)
            verdict.set_text("REFUSED_EMPTY")
            note.set_text("the host proves no admissible answer is in the carrier")
            fence.set_text(
                "CANNOT: collapse cannot conjure a point outside the intersection. Not a Lean theorem."
            )
        return []

    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(
        fps=fps, metadata={"title": "Track A video 7: collapse", "artist": "the_symbol_game"}
    )
    anim.save(str(out_path), writer=writer)
    plt.close(fig)
    return out_path


def main() -> None:
    t = traces()
    print(f"[Pinned] |U|={t['universe']} residual {t['residual_sizes']} {t['residual_verdict']}")
    print(
        f"[Pinned] landed {t['landed_sizes']} {t['landed_verdict']} witness={t['landed_witness']}"
    )
    print(
        f"[Pinned] refused {t['refused_verdict']}; SHAPE.op={t['shape_op']} DEMAND.op={t['demand_op']} LAND.op={t['land_op']}"
    )
    path = render_mp4()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
