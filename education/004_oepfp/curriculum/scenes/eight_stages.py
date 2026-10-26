"""Track A video 6 — eight packet and receipt schemas, including the code-change proposal.

``STAGE_FILES`` is a packet-schema index (indexes 0–7) over
``omega_engine_pfp/packet_schemas/``. It is not a pipeline and not the
11-stage public ladder. That ladder stays ``stage_1`` through ``stage_11``
in ``omega_engine_pfp/infrastructure/yaml/stages/``. The envelope carries one
payload family (an LLM turn or a code-change proposal), so the eight files
are not a sequence. Index 5 is the code-change proposal; additionalProperties
is false; the schema ``$comment`` forbids model-authored
passed/verified/promotion_eligible. jsonschema rejects an index-5 payload
that adds ``passed: true``.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[4]


_ROOT = _find_repo_root()
_SCENES = Path(__file__).resolve().parent
_PACKET_SCHEMAS = _ROOT / "omega_engine_pfp" / "packet_schemas"

# Packet-schema index, not the 11-stage public ladder.
STAGE_FILES = [
    (0, "Packet Envelope", "packet_envelope_v2.schema.json"),
    (1, "Prompt Artifact", "prompt_artifact_v1.schema.json"),
    (2, "Candidate Artifact", "candidate_artifact_v1.schema.json"),
    (3, "LLM Turn", "llm_turn_v1.schema.json"),
    (4, "Coboundary Score", "coboundary_score_v1.schema.json"),
    (5, "Code Change Proposal", "code_change_proposal_v1.schema.json"),
    (6, "Evaluation Receipt", "evaluation_receipt_v1.schema.json"),
    (7, "Elimination Receipt", "elimination_receipt_v1.schema.json"),
]


def _schema(name: str) -> dict:
    path = _PACKET_SCHEMAS / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def stage5_minimal() -> dict:
    digest = "a" * 64
    return {
        "schema_version": "omega.symbol-game.code-change-proposal.v1",
        "family": "code_change_proposal",
        "objective": "land a typed refusal on a planted contradiction",
        "source_revision": "track-a",
        "owned_paths": ["notebooks/scenes/eight_stages.py"],
        "protected_paths": [],
        "allowed_transforms": ["edit"],
        "candidate_budget": 1,
        "operation_budget": 8,
        "required_gates": ["replay"],
        "terminal_target": "TransportValidatedOrTypedRefusal",
        "evidence_ceiling": "ReplayableLabEvidence",
        "parent_packet_id": None,
        "path_manifest_root": digest,
        "authority_effect": "None",
    }


def inventory() -> dict:
    rows = []
    for idx, title, name in STAGE_FILES:
        schema = _schema(name)
        rows.append(
            {
                "index": idx,
                "title": title,
                "file": name,
                "exists": True,
                "additional_properties": schema.get("additionalProperties"),
                "schema_id": schema.get("$id", ""),
            }
        )
    s5 = _schema("code_change_proposal_v1.schema.json")
    import jsonschema

    clean = stage5_minimal()
    try:
        jsonschema.validate(clean, s5)
        clean_ok = True
    except jsonschema.ValidationError:
        clean_ok = False
    poisoned = {**clean, "passed": True}
    extra_keys = sorted(
        set(poisoned) - set(clean)
    )  # the fields we added (e.g. ["passed"]), derived not fabricated
    extra_failed = False
    try:
        jsonschema.validate(poisoned, s5)
    except jsonschema.ValidationError:
        extra_failed = True
    comment = s5.get("$comment", "")
    return {
        "n_stages": len(rows),
        "rows": rows,
        "stage5_additional": s5.get("additionalProperties"),
        "stage5_has_passed_property": "passed" in s5.get("properties", {}),
        "stage5_comment_forbids": all(
            w in comment for w in ("passed", "verified", "promotion_eligible")
        ),
        "stage5_clean_ok": clean_ok,
        "stage5_passed_refused": extra_failed,
        "stage5_error_path": extra_keys,
    }


def render_mp4(out_path: Path | None = None, fps: int = 12) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FFMpegWriter, FuncAnimation
    from matplotlib.patches import FancyBboxPatch

    inv = inventory()
    if (
        inv["n_stages"] != 8
        or not inv["stage5_passed_refused"]
        or inv["stage5_additional"] is not False
    ):
        raise RuntimeError(
            f"packet-schema index failed: { {k: inv[k] for k in inv if k != 'rows'} }"
        )

    if out_path is None:
        out_path = _SCENES / "_render" / "06_eight_stages.mp4"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bg, ink, muted = "#10141a", "#e8e6e3", "#9aa3ad"
    ok, _bad, gold = "#6ec89b", "#e85d4c", "#f0c14a"
    _duration_s, n_frames = 26, 26 * fps

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = []
    labels = []
    for i, (_idx, title, _name) in enumerate(STAGE_FILES):
        y = 0.72 - i * 0.075
        box = FancyBboxPatch(
            (0.22, y),
            0.56,
            0.065,
            boxstyle="round,pad=0.008",
            facecolor="#1c2430",
            edgecolor="#3d4a5c",
            lw=1.2,
        )
        ax.add_patch(box)
        lab = ax.text(
            0.50, y + 0.032, f"{i}  {title}", ha="center", va="center", color=ink, fontsize=11
        )
        boxes.append(box)
        labels.append(lab)

    title = ax.text(
        0.5, 0.92, "", ha="center", va="center", color=ink, fontsize=20, fontweight="bold"
    )
    sub = ax.text(0.5, 0.85, "", ha="center", va="center", color=muted, fontsize=12)
    fence = ax.text(0.5, 0.06, "", ha="center", va="center", color=muted, fontsize=11)

    def _highlight(active: int | None, special: int | None = None) -> None:
        for i, box in enumerate(boxes):
            if special is not None and i == special:
                box.set_facecolor("#3a2418")
                box.set_edgecolor(gold)
                labels[i].set_color(gold)
            elif active is not None and i == active:
                box.set_facecolor("#1e3a2f")
                box.set_edgecolor(ok)
                labels[i].set_color(ok)
            else:
                box.set_facecolor("#1c2430")
                box.set_edgecolor("#3d4a5c")
                labels[i].set_color(ink)

    def update(frame: int):
        t = frame / fps
        if t < 8:
            step = min(7, int(t))
            title.set_text("Eight packet schemas, not the ladder")
            sub.set_text("packet-schema index 0–7  ·  not the 11-stage public ladder")
            _highlight(step)
            fence.set_text("")
        elif t < 16:
            title.set_text("The code-change proposal is in the host")
            sub.set_text("code_change_proposal_v1.schema.json  ·  additionalProperties: false")
            _highlight(None, special=5)
            fence.set_text("")
        elif t < 21:
            title.set_text("passed: true is not a field")
            sub.set_text("jsonschema rejects extra keys  ·  model cannot author verified")
            _highlight(None, special=5)
            fence.set_text("")
        else:
            title.set_text("Fail closed at the schema")
            sub.set_text("Course I walks all eight packet schemas. Skipping the proposal schema is a hole, not a simplification.")
            _highlight(None, special=5)
            fence.set_text(
                "CANNOT: this packet-schema index is not the 11-stage public ladder and not a live governed run."
            )
        return []

    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / fps, blit=False)
    writer = FFMpegWriter(
        fps=fps, metadata={"title": "Track A video 6: packet-schema index, not the 11-stage ladder", "artist": "the_symbol_game"}
    )
    anim.save(str(out_path), writer=writer)
    plt.close(fig)
    return out_path


def main() -> None:
    inv = inventory()
    print(f"[Pinned] {inv['n_stages']} packet schemas (index, not the 11-stage ladder)")
    for row in inv["rows"]:
        print(
            f"  {row['index']} {row['title']}: additionalProperties={row['additional_properties']}"
        )
    print(
        f"[Pinned] index 5 extra 'passed' refused={inv['stage5_passed_refused']} path={inv['stage5_error_path']}"
    )
    path = render_mp4()
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
