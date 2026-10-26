"""Track A video 5 — seal one packet; mutate one field; digest breaks.

Uses hexagonal PacketCodec.seal/verify. Canonical bytes are json.dumps with
sort_keys and NFC, then SHA-256 — not RFC 8785 JCS. Duplicate keys refuse via
glyph_calculus.check_no_duplicate_keys.

    python notebooks/scenes/seal_packet.py

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[4]


_ROOT = _find_repo_root()
_SCENES = Path(__file__).resolve().parent
_DOMAIN = _ROOT / "omega_engine_pfp" / "domain"

FOUR_FIELD = {
    "contract": "SYM-TRACK-A",
    "task": "PROVE_CYCLE_0",
    "payload": {"op": "ASSERT", "claim": "holonomy-3"},
    "parent_hash": "0" * 64,
}


def _load_codec():
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from omega_engine_pfp.domain.packet_codec import (  # noqa: WPS433
        PacketCodec,
        canonical_json_bytes,
        compute_sha256,
    )

    return PacketCodec, canonical_json_bytes, compute_sha256


def _load_glyph():
    if str(_DOMAIN) not in sys.path:
        sys.path.insert(0, str(_DOMAIN))
    from glyph_calculus import REFUSAL_DUPLICATE_KEY, check_no_duplicate_keys  # noqa: WPS433

    return check_no_duplicate_keys, REFUSAL_DUPLICATE_KEY


PacketCodec, canonical_json_bytes, compute_sha256 = _load_codec()
check_no_duplicate_keys, REFUSAL_DUPLICATE_KEY = _load_glyph()


def demo_numbers() -> dict:
    envelope = PacketCodec.seal(FOUR_FIELD, packet_family="track_a")
    ok, sha, detail = PacketCodec.verify(envelope)
    tampered_payload = {
        **FOUR_FIELD,
        "payload": {**FOUR_FIELD["payload"], "claim": "holonomy-0"},
    }
    tampered = PacketCodec.seal(tampered_payload, packet_family="track_a")
    mutated = dict(envelope)
    mutated["payload"] = tampered_payload
    mutated_ok, mutated_sha, mutated_detail = PacketCodec.verify(mutated)
    dups = check_no_duplicate_keys([("op", "ASSERT"), ("op", "CUT")])
    # Tagged canonical bytes from domain codec
    dumped = canonical_json_bytes(envelope["payload"])
    return {
        "ok": ok,
        "detail": detail,
        "payload_sha": envelope["payload_sha256"],
        "envelope_sha": envelope["envelope_sha256"],
        "verify_sha": sha,
        "tampered_sha": tampered["payload_sha256"],
        "digest_changed": tampered["payload_sha256"] != envelope["payload_sha256"],
        "mutated_ok": mutated_ok,
        "mutated_detail": mutated_detail,
        "dup_code": dups[0].code if dups else None,
        "dup_refusal": REFUSAL_DUPLICATE_KEY,
        "canonical_is_sorted_json": dumped == canonical_json_bytes(envelope["payload"]),
        "payload_sha_matches_bytes": compute_sha256(dumped) == envelope["payload_sha256"],
    }


def render_mp4(out_path: Path | None = None, fps: int = 12) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation

    nums = demo_numbers()
    if not nums["ok"] or not nums["digest_changed"] or nums["mutated_ok"]:
        raise RuntimeError(f"seal/verify did not behave as pinned: {nums}")
    if not nums["canonical_is_sorted_json"] or not nums["payload_sha_matches_bytes"]:
        raise RuntimeError("digest is not SHA-256 of sorted JSON")

    if out_path is None:
        out_path = _SCENES / "_render" / "05_seal_packet.mp4"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bg, ink, muted = "#10141a", "#e8e6e3", "#9aa3ad"
    ok, bad, _gold = "#6ec89b", "#e85d4c", "#f0c14a"
    _duration_s, n_frames = 24, 24 * fps
    short = nums["payload_sha"][:16] + "..."
    short_t = nums["tampered_sha"][:16] + "..."

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
    body = ax.text(0.5, 0.50, "", ha="center", va="center", color=ink, fontsize=14, linespacing=1.7)
    left = ax.text(
        0.28, 0.20, "", ha="center", va="center", color=ok, fontsize=13, fontweight="bold"
    )
    right = ax.text(
        0.72, 0.20, "", ha="center", va="center", color=bad, fontsize=13, fontweight="bold"
    )
    fence = ax.text(0.5, 0.07, "", ha="center", va="center", color=muted, fontsize=11)

    def update(frame: int):
        t = frame / fps
        if t < 6:
            title.set_text("Four fields, then a digest")
            sub.set_text("contract  ·  task  ·  payload  ·  parent_hash")
            body.set_text(
                "contract = SYM-TRACK-A\ntask = PROVE_CYCLE_0\npayload.op = ASSERT\nparent_hash = 00…0"
            )
            left.set_text("")
            right.set_text("")
            fence.set_text("")
        elif t < 12:
            title.set_text("PacketCodec.seal")
            sub.set_text("json.dumps(..., sort_keys=True)  then  SHA-256")
            body.set_text(f"payload_sha256 = {short}\nverify() → OK")
            left.set_color(ok)
            left.set_text("sealed")
            right.set_text("")
            fence.set_text("")
        elif t < 18:
            title.set_text("Mutate one field")
            sub.set_text('payload.claim  "holonomy-3"  →  "holonomy-0"')
            body.set_text(f"was  {short}\nnow  {short_t}")
            left.set_color(ok)
            left.set_text("original\nstill verifies")
            right.set_color(bad)
            right.set_text("mutated envelope\nSHA-256 mismatch")
            fence.set_text("")
        else:
            title.set_text("The digest is the identity")
            sub.set_text("duplicate keys refuse  ·  last-one-wins is not a reading")
            body.set_text("FW-DUPLICATE-KEY  if  op appears twice")
            left.set_color(ok)
            left.set_text(f"ok\n{short}")
            right.set_color(bad)
            right.set_text(f"tamper\n{short_t}")
            fence.set_text(
                "CANNOT: SHA-256 of sorted JSON with NFC. Not RFC 8785 JCS. Not a signature."
            )
        return []

    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(
        fps=fps, metadata={"title": "Track A video 5: seal packet", "artist": "the_symbol_game"}
    )
    anim.save(str(out_path), writer=writer)
    plt.close(fig)
    return out_path


def main() -> None:
    nums = demo_numbers()
    print(f"[Pinned] verify={nums['ok']} {nums['detail']} sha={nums['payload_sha'][:16]}...")
    print(
        f"[Pinned] tamper changed digest={nums['digest_changed']} mutated_ok={nums['mutated_ok']}"
    )
    print(
        f"[Pinned] duplicate op → {nums['dup_code']}; canonical=sorted JSON {nums['canonical_is_sorted_json']}"
    )
    path = render_mp4()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
