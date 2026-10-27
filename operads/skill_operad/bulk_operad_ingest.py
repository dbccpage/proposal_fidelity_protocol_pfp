#!/usr/bin/env python3
"""bulk_operad_ingest.py — Operadic Ingest Engine with Explicit Manifest Declarations.

Rejects heuristic substring matching. Requires explicit operad_source_colours and
operad_target_colour declarations in skill manifests/headers (DEF-OP-01).

Default mode is **dry-run / report-only**. Writes require explicit consent:

    CORE_BULK_OPERAD_INGEST=1 python .agents/operad/bulk_operad_ingest.py

AuthorityEffect: None. Does not mint residual_effect=contractive.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

from operads.canon import OPERAD_COLOUR

WRITE_ENV = "CORE_BULK_OPERAD_INGEST"

VALID_COLOURS = set(OPERAD_COLOUR)
SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def extract_explicit_colours(item: dict[str, Any]) -> Tuple[Optional[List[str]], Optional[str], Optional[str]]:
    """Extracts explicit operad colours from item declaration.

    Returns: (source_colours, target_colour, refusal_reason)
    """
    src = item.get("operad_source_colours") or item.get("source_colours")
    tgt = item.get("operad_target_colour") or item.get("target_colour")

    if not src or not tgt:
        return None, None, "REFUSED_MISSING_OPERAD_DECLARATION: operad_source_colours and operad_target_colour must be explicitly declared."

    if isinstance(src, str):
        try:
            src = json.loads(src)
        except Exception:
            src = [c.strip() for c in src.split(",")]

    if not isinstance(src, list) or len(src) == 0:
        return None, None, f"REFUSED_INVALID_SOURCE_COLOURS: expected non-empty list of colours, got {src}"

    invalid_src = [c for c in src if c not in VALID_COLOURS]
    if invalid_src:
        return None, None, f"REFUSED_UNKNOWN_COLOUR: source colours contain unrecognised colours {invalid_src}"

    if tgt not in VALID_COLOURS:
        return None, None, f"REFUSED_UNKNOWN_COLOUR: target colour '{tgt}' is not in valid colour set."

    return src, str(tgt), None


def operad_dir_from(start: Path | None = None) -> Path:
    here = (start or Path(__file__).resolve()).parent
    return here


def propose_ingest(
    skills_raw: list[dict[str, Any]],
    *,
    origin: str = "external",
    operad_dir: Path | None = None,
) -> dict[str, Any]:
    """Compute proposed operations using strict explicit manifest declarations."""
    odir = operad_dir or operad_dir_from()
    sig_path = (
        odir / "json" / "operad_signature.json"
        if (odir / "json" / "operad_signature.json").is_file()
        else odir / "operad_signature.json"
    )
    sig = json.loads(sig_path.read_text(encoding="utf-8"))
    existing = {op["skill_id"] for op in sig.get("operations") or []}

    proposed: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    seen_batch: set[str] = set()
    collisions: list[str] = []

    for item in skills_raw:
        name = item.get("name", "unnamed_skill")
        sid = item.get("skill_id") or f"ext_{origin}_{str(name).lower().replace(' ', '_').replace('-', '_')}"

        if not isinstance(sid, str) or SKILL_ID.fullmatch(sid) is None:
            refused.append({
                "skill_id": str(sid),
                "name": name,
                "reason": "REFUSED_INVALID_SKILL_ID: expected lowercase [a-z0-9_-] identifier",
            })
            continue

        if sid in existing:
            continue
        if sid in seen_batch:
            collisions.append(
                f"normalization collision: skill_id '{sid}' already proposed in this batch (name={name!r})"
            )
            continue
        seen_batch.add(sid)

        src, tgt, error_msg = extract_explicit_colours(item)
        if error_msg:
            refused.append({
                "skill_id": sid,
                "name": name,
                "reason": error_msg,
            })
            continue

        declared_residual = item.get("residual_effect", "unknown")
        if declared_residual != "unknown":
            refused.append({
                "skill_id": sid,
                "name": name,
                "reason": (
                    "REFUSED_UNVERIFIED_RESIDUAL_EFFECT: ingest may register only "
                    "residual_effect=unknown"
                ),
            })
            continue

        proposed.append(
            {
                "skill_id": sid,
                "name": f"[{origin}] {name}",
                "arity": len(src),
                "source_colours": src,
                "target_colour": tgt,
                "equivariant": False,
                "residual_effect": "unknown",
                "origin": origin,
                "ingest_status": "PROPOSED_EXPLICIT",
                "def_op": "DEF-OP-01",
            }
        )

    out: dict[str, Any] = {
        "ok": not collisions and len(refused) == 0,
        "write_allowed": os.environ.get(WRITE_ENV) == "1",
        "proposed_count": len(proposed),
        "proposed": proposed,
        "refused_count": len(refused),
        "refused": refused,
        "existing_ops": len(existing),
        "collisions": collisions,
        "note": (
            "DEF-OP-01 explicit gate: dry-run unless CORE_BULK_OPERAD_INGEST=1. "
            "Requires explicit manifest colour declarations."
        ),
    }

    if collisions:
        out["error"] = f"refused: skill_id normalization collisions ({len(collisions)})"
    elif len(refused) > 0:
        out["error"] = f"refused: {len(refused)} skills lack explicit operad colour declarations"

    return out


def apply_ingest(
    skills_raw: list[dict[str, Any]],
    *,
    origin: str = "external",
    operad_dir: Path | None = None,
) -> dict[str, Any]:
    """Write proposed ops. Requires CORE_BULK_OPERAD_INGEST=1."""
    if os.environ.get(WRITE_ENV) != "1":
        plan = propose_ingest(skills_raw, origin=origin, operad_dir=operad_dir)
        plan["applied"] = False
        plan["error"] = plan.get("error") or f"refused: set {WRITE_ENV}=1 to write signature/slices"
        return plan

    odir = operad_dir or operad_dir_from()
    sig_path = (
        odir / "json" / "operad_signature.json"
        if (odir / "json" / "operad_signature.json").is_file()
        else odir / "operad_signature.json"
    )
    plan = propose_ingest(skills_raw, origin=origin, operad_dir=odir)
    if plan.get("error") or not plan.get("ok", True):
        plan["applied"] = False
        return plan

    sig = json.loads(sig_path.read_text(encoding="utf-8"))
    for op_record in plan["proposed"]:
        sig["operations"].append(op_record)

    sig_path.write_text(json.dumps(sig, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan["applied"] = True
    plan["total_ops"] = len(sig["operations"])
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help=f"Write disk (also requires {WRITE_ENV}=1)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    sample_skills = [
        {
            "name": "spec-planner",
            "description": "Generates structured software design specification from user requirements",
            "operad_source_colours": ["State"],
            "operad_target_colour": "Contract",
        },
        {
            "name": "lean4-tactic-prover",
            "description": "Executes Lean 4 tactic step and verifies proof assertion",
            "operad_source_colours": ["Proof", "Code"],
            "operad_target_colour": "Proof",
        },
    ]

    out = apply_ingest(sample_skills, origin="superpowers") if args.apply else propose_ingest(sample_skills, origin="superpowers")

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print("=== BULK OPERAD INGEST (DEF-OP-01) ===")
        print(out.get("note"))
        print(f"proposed: {out.get('proposed_count')} | refused: {out.get('refused_count')} | applied: {out.get('applied')}")
        for op in out.get("proposed") or []:
            print(f"  - {op['skill_id']}: {op['source_colours']} -> {op['target_colour']} (residual={op['residual_effect']})")
        if out.get("error"):
            print(f"ERROR: {out['error']}")
            return 2
    return 0 if not out.get("error") else 2


if __name__ == "__main__":
    sys.exit(main())
