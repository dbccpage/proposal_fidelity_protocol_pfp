"""Original consistency teaching scene over the canonical accounted PFP recorder.

Import and rendering are offline. Recording requires an explicit caller-owned
gateway or the bounded record CLI. Historical captures are never overwritten.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    _source_root = next((p for p in Path(__file__).resolve().parents
        if (p / "omega_engine_pfp").is_dir()), None)
    if _source_root is not None:
        sys.path.insert(0, str(_source_root))

from omega_engine_pfp.infrastructure.consistency_teaching import (
    DEFAULT_MODEL, TEACHING_ITEMS, TEACHING_RELATIONS, TEACHING_SEED,
    record_one as _record_one, record_main,
)

_SCENES = Path(__file__).resolve().parent


def record_one(
    model: str = DEFAULT_MODEL,
    seed: int = TEACHING_SEED,
    style: str = "direct",
    n_items: int = TEACHING_ITEMS,
    n_relations: int = TEACHING_RELATIONS,
    *, gateway=None, output_path: Path | str | None = None,
    max_output_tokens: int = 2048,
) -> dict:
    return _record_one(model, seed, style, n_items, n_relations,
        gateway=gateway, output_path=output_path, max_output_tokens=max_output_tokens)


def render_mp4(receipt: dict, out_path: Path | None = None, fps: int = 12) -> Path:
    """24s clip from a recorded receipt. Does not call the API."""
    if out_path is None:
        out_path = _SCENES / "_render" / "01_naked_prompt_launder.mp4"
    out_path = Path(out_path)
    if out_path.exists():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation

    out_path.parent.mkdir(parents=True, exist_ok=True)

    claims = receipt["instance"]["claims"]
    claim_lines = [f"r({v}) − r({u}) = {d}" for u, v, d in claims]
    model = receipt["config"]["model"]
    host_v = receipt["host_verdict"]
    model_v = receipt["model_verdict"]
    raw = (receipt.get("model_raw") or "").strip().replace("\n", " ")
    if len(raw) > 80:
        raw = raw[:77] + "…"
    laundered = receipt.get("laundered") is True

    bg, ink, muted = "#10141a", "#e8e6e3", "#9aa3ad"
    bad, ok, gold = "#e85d4c", "#6ec89b", "#f0c14a"
    duration_s = 24
    n_frames = duration_s * fps

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    title = ax.text(
        0.5,
        0.90,
        "The naked prompt",
        ha="center",
        va="center",
        color=ink,
        fontsize=22,
        fontweight="bold",
    )
    sub = ax.text(0.5, 0.82, "", ha="center", va="center", color=muted, fontsize=13)
    body = ax.text(0.5, 0.52, "", ha="center", va="center", color=ink, fontsize=15, linespacing=1.6)
    left = ax.text(
        0.28, 0.22, "", ha="center", va="center", color=ok, fontsize=16, fontweight="bold"
    )
    right = ax.text(
        0.72, 0.22, "", ha="center", va="center", color=bad, fontsize=16, fontweight="bold"
    )
    fence = ax.text(0.5, 0.07, "", ha="center", va="center", color=muted, fontsize=11)

    def update(frame: int):
        t = frame / fps
        if t < 6:
            title.set_text("The naked prompt")
            sub.set_text("one planted contradiction  ·  three rank-difference claims")
            body.set_text("\n".join(claim_lines))
            left.set_text("")
            right.set_text("")
            fence.set_text("")
        elif t < 14:
            title.set_text("Ask a cheap hosted model")
            sub.set_text(model)
            body.set_text(
                "Can a single integer assignment satisfy ALL of these at once?\nAnswer CONSISTENT or CONTRADICTION."
            )
            left.set_text("")
            right.set_text("")
            fence.set_text("")
        elif t < 19:
            title.set_text("Two verdicts")
            sub.set_text("same instance  ·  host is exact  ·  model is a prompt")
            body.set_text(f"model said: {raw}" if raw else "")
            left.set_color(ok)
            left.set_text(f"host\n{host_v}")
            right.set_color(bad if model_v == "CONSISTENT" else gold)
            right.set_text(f"{model}\n{model_v}")
            fence.set_text("")
        else:
            title.set_text("No model verdict" if model_v == "UNKNOWN" else
                "Laundering" if laundered else "This run did not launder")
            sub.set_text("One recorded reply compared with an exact finite host check")
            body.set_text("")
            left.set_color(ok)
            left.set_text(f"host\n{host_v}")
            right.set_color(bad if model_v == "CONSISTENT" else gold)
            right.set_text(f"{model}\n{model_v}")
            fence.set_text(
                "One recorded instance. No scaling law or model-efficacy claim."
            )
        return []

    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(
        fps=fps, metadata={"title": "Track A video 1: naked prompt", "artist": "the_symbol_game"}
    )
    anim.save(str(out_path), writer=writer)
    plt.close(fig)
    return out_path


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "record":
        return record_main(args[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("render",))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fps", type=int, default=12)
    options = parser.parse_args(args)
    if options.output.exists():
        parser.error("OUTPUT_ALREADY_EXISTS")
    if options.fps < 1:
        parser.error("fps must be positive")
    receipt = json.loads(options.input.read_text(encoding="utf-8"))
    print(render_mp4(receipt, options.output, options.fps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
