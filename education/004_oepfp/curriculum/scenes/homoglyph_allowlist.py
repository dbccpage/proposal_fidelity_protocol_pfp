"""Track A video 4 — one homoglyph: APL alpha vs a Greek-alpha allowlist.

Pins Carrier to U+03B1 GREEK SMALL LETTER ALPHA. Injects U+237A APL FUNCTIONAL
SYMBOL ALPHA. NFKC leaves the APL glyph unchanged; Carrier.check_term refuses
FW-CARRIER-CODEPOINT. Does not reimplement the pin: imports glyph_calculus.

    python notebooks/scenes/homoglyph_allowlist.py

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[4]


_ROOT = _find_repo_root()
_SCENES = Path(__file__).resolve().parent
_DOMAIN = _ROOT / "omega_engine_pfp" / "domain"

GREEK = "\u03b1"  # U+03B1 GREEK SMALL LETTER ALPHA
APL = "\u237a"  # U+237A APL FUNCTIONAL SYMBOL ALPHA


def _load_glyph():
    if str(_DOMAIN) not in sys.path:
        sys.path.insert(0, str(_DOMAIN))
    from glyph_calculus import REFUSAL_CARRIER_CODEPOINT, Carrier  # noqa: WPS433

    return Carrier, REFUSAL_CARRIER_CODEPOINT


Carrier, REFUSAL_CARRIER_CODEPOINT = _load_glyph()


def greek_carrier():
    return Carrier.from_wire([{"symbol": "alpha", "codepoint": "U+03B1"}])


def nfkc(char: str) -> str:
    return unicodedata.normalize("NFKC", char)


def refuse_apl(carrier=None):
    carrier = carrier or greek_carrier()
    return carrier.check_term(APL)


def demo_numbers() -> dict:
    carrier = greek_carrier()
    greek_ok = carrier.check_term(GREEK)
    apl_findings = carrier.check_term(APL)
    return {
        "nfkc_apl_unchanged": nfkc(APL) == APL,
        "nfkc_apl_name": unicodedata.name(nfkc(APL)),
        "greek_ok": greek_ok == (),
        "apl_code": apl_findings[0].code if apl_findings else None,
        "apl_refusal": REFUSAL_CARRIER_CODEPOINT,
        "apl_detail": str(apl_findings[0]) if apl_findings else "",
    }


def render_mp4(out_path: Path | None = None, fps: int = 12) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation

    nums = demo_numbers()
    if not nums["nfkc_apl_unchanged"] or nums["apl_code"] != REFUSAL_CARRIER_CODEPOINT:
        raise RuntimeError(f"pinned glyph_calculus did not refuse APL alpha: {nums}")

    if out_path is None:
        out_path = _SCENES / "_render" / "04_homoglyph_allowlist.mp4"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bg, ink, muted = "#10141a", "#e8e6e3", "#9aa3ad"
    ok, bad, gold = "#6ec89b", "#e85d4c", "#f0c14a"
    _duration_s, n_frames = 22, 22 * fps

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    title = ax.text(
        0.5, 0.90, "", ha="center", va="center", color=ink, fontsize=22, fontweight="bold"
    )
    sub = ax.text(0.5, 0.82, "", ha="center", va="center", color=muted, fontsize=13)
    left = ax.text(
        0.28, 0.48, "", ha="center", va="center", color=ink, fontsize=28, fontweight="bold"
    )
    right = ax.text(
        0.72, 0.48, "", ha="center", va="center", color=ink, fontsize=28, fontweight="bold"
    )
    left_cap = ax.text(0.28, 0.28, "", ha="center", va="center", color=muted, fontsize=12)
    right_cap = ax.text(0.72, 0.28, "", ha="center", va="center", color=muted, fontsize=12)
    verdict = ax.text(
        0.5, 0.16, "", ha="center", va="center", color=bad, fontsize=16, fontweight="bold"
    )
    fence = ax.text(0.5, 0.07, "", ha="center", va="center", color=muted, fontsize=11)

    def update(frame: int):
        t = frame / fps
        if t < 6:
            title.set_text("Pin one codepoint")
            sub.set_text("Carrier = { U+03B1 GREEK SMALL LETTER ALPHA }")
            left.set_color(ok)
            left.set_text(GREEK)
            left_cap.set_text("Greek α\nU+03B1\ncheck_term → admit")
            right.set_text("")
            right_cap.set_text("")
            verdict.set_text("")
            fence.set_text("")
        elif t < 12:
            title.set_text("A look-alike is not a member")
            sub.set_text("inject APL functional symbol alpha")
            left.set_color(ok)
            left.set_text(GREEK)
            left_cap.set_text("Greek α  U+03B1")
            right.set_color(bad)
            right.set_text(APL)
            right_cap.set_text("APL ⍺  U+237A")
            verdict.set_text("")
            fence.set_text("")
        elif t < 17:
            title.set_text("NFKC does not catch it")
            sub.set_text("NFKC(U+237A) = U+237A  —  no compatibility decomposition")
            left.set_color(ok)
            left.set_text(GREEK)
            left_cap.set_text("declared")
            right.set_color(bad)
            right.set_text(APL)
            right_cap.set_text("unchanged by NFKC")
            verdict.set_text("")
            fence.set_text("")
        else:
            title.set_text("Allowlist refuses")
            sub.set_text("Carrier.check_term  —  not a normaliser")
            left.set_color(ok)
            left.set_text(GREEK)
            left_cap.set_text("admitted")
            right.set_color(bad)
            right.set_text(APL)
            right_cap.set_text("impostor")
            verdict.set_color(gold)
            verdict.set_text("FW-CARRIER-CODEPOINT")
            fence.set_text(
                "CANNOT: one allowlist. Not a claim that NFKC never helps, or that every homoglyph is named ALPHA."
            )
        return []

    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(
        fps=fps,
        metadata={"title": "Track A video 4: homoglyph allowlist", "artist": "the_symbol_game"},
    )
    anim.save(str(out_path), writer=writer)
    plt.close(fig)
    return out_path


def main() -> None:
    nums = demo_numbers()
    print(
        f"[Pinned] NFKC(APL alpha) unchanged: {nums['nfkc_apl_unchanged']} ({nums['nfkc_apl_name']})"
    )
    print(f"[Pinned] Greek alpha admitted: {nums['greek_ok']}")
    print(f"[Pinned] APL alpha: {nums['apl_detail']}")
    path = render_mp4()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
