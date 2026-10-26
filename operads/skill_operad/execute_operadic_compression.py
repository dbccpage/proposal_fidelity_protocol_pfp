"""execute_operadic_compression.py

Proposal generator for declared symmetric normalization and quotient candidates.

The default path is read-only. It does not establish behavioral equivalence or
authorize skill deletion, admission, or capability mutation.

AuthorityEffect: None. Finite residual structure only.
"""

from __future__ import annotations

import argparse
import os
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Set

from coloured_operad import ColouredOperad
from symmetric_quotient import SymmetricQuotientFunctor


def run_compression(
    *,
    apply_changes: bool = False,
    archive_culled: bool = False,
    operad_dir: Path | str | None = None,
) -> Dict[str, Any]:
    """Compute a quotient candidate report; mutate only with explicit apply.

    ``archive_culled`` is accepted only with ``apply_changes``. The current
    quotient implementation never certifies a concrete operation for culling.
    """
    if archive_culled and not apply_changes:
        raise ValueError("archive_culled requires apply_changes=True")
    here = os.path.dirname(os.path.abspath(__file__))
    if operad_dir is not None:
        operad_dir = str(operad_dir)
        repo_root = os.path.dirname(os.path.dirname(operad_dir))
    elif os.path.exists(os.path.join(here, "json", "operad_signature.json")) or os.path.exists(os.path.join(here, "operad_signature.json")):
        operad_dir = here
        repo_root = os.path.dirname(os.path.dirname(here))
    else:
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        operad_dir = os.path.join(repo_root, ".agents", "operad")
    skills_dir = os.path.join(repo_root, "omega_engine_operads", "skills")
    archived_dir = os.path.join(skills_dir, "_archived")

    sig_path = (
        os.path.join(operad_dir, "json", "operad_signature.json")
        if os.path.exists(os.path.join(operad_dir, "json", "operad_signature.json"))
        else os.path.join(operad_dir, "operad_signature.json")
    )
    comp_path = (
        os.path.join(operad_dir, "json", "composition_matrix.json")
        if os.path.exists(os.path.join(operad_dir, "json", "composition_matrix.json"))
        else os.path.join(operad_dir, "composition_matrix.json")
    )
    slice_path = (
        os.path.join(operad_dir, "json", "agent_capability_slices.json")
        if os.path.exists(os.path.join(operad_dir, "json", "agent_capability_slices.json"))
        else os.path.join(operad_dir, "agent_capability_slices.json")
    )
    trace_path = (
        os.path.join(operad_dir, "json", "evidence_trace.json")
        if os.path.exists(os.path.join(operad_dir, "json", "evidence_trace.json"))
        else os.path.join(operad_dir, "evidence_trace.json")
    )

    with open(sig_path, "r", encoding="utf-8") as f:
        sig = json.load(f)
    with open(comp_path, "r", encoding="utf-8") as f:
        comp_matrix = json.load(f)
    with open(slice_path, "r", encoding="utf-8") as f:
        slices = json.load(f)

    # 1. Build initial concrete operad
    concrete = ColouredOperad("AnomalonConcreteOperad")
    for c in sig.get("colours", {}).keys():
        concrete.add_colour(c)

    for op in sig.get("operations", []):
        concrete.add_operation(
            op_id=op["skill_id"],
            name=op["name"],
            source_colours=op["source_colours"],
            target_colour=op["target_colour"],
            equivariant=op.get("equivariant", False),
            residual_effect=op.get("residual_effect", "unknown"),
        )

    for c in comp_matrix.get("compositions", []):
        res = concrete.add_composition(
            outer=c["outer"],
            slot=c["slot"],
            inner=c["inner"],
            result=c.get("composite_id", c.get("result", "composite_op")),
        )
        if res.is_failure:
            pass

    concrete.ensure_units()

    # 2. Run Symmetric Quotient Functor Q
    # ``min_instances`` is retained for API compatibility and diagnostic
    # grouping only. No scalar-observation count authorizes a quotient.
    SQ = SymmetricQuotientFunctor(concrete, min_instances=3)

    # Record trace evidence from evidence_trace.json
    if os.path.exists(trace_path):
        with open(trace_path, "r", encoding="utf-8") as f:
            traces = json.load(f)
        for row in traces:
            SQ.record(row["skill_id"], row["run_id"], float(row["phi_before"]), float(row["phi_after"]))

    meta_operad = SQ.build_meta_operad("AnomalonMetaOperad")
    report = SQ.report()
    report["applied"] = False
    report["status"] = "PROPOSED_NOT_EXECUTED"

    if not apply_changes:
        print(
            "[PROPOSED_NOT_EXECUTED] Operad comparison report computed; "
            "registries, skills, and capability slices were not changed."
        )
        return report

    # 3. Synchronize operad_signature.json meta-operations
    meta_sig_dict = meta_operad.to_signature_dict()
    sig["meta_operations"] = meta_sig_dict["operations"]

    # Register synthesized meta-skills dynamically from composition_matrix.json
    synthesized_meta_skills = comp_matrix.get("synthesized_meta_skills", [])
    existing_ids = {op["skill_id"] for op in sig["operations"]}

    for ms in synthesized_meta_skills:
        if ms["id"] not in existing_ids:
            sig["operations"].append({
                "skill_id": ms["id"],
                "name": ms["name"],
                "arity": len(ms["source_colours"]),
                "source_colours": ms["source_colours"],
                "target_colour": ms["target_colour"],
                "equivariant": False,
                "residual_effect": "unknown",
            })
            existing_ids.add(ms["id"])

    with open(sig_path, "w", encoding="utf-8") as f:
        json.dump(sig, f, indent=2)

    # 4. Save composition matrix cleanly (source/target colors read directly from composition_matrix.json)
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(comp_matrix, f, indent=2)

    # 5. Synchronize agent capability slices dynamically without hardcoding agent roles
    all_op_ids = {op["skill_id"] for op in sig["operations"]}
    identities_raw = sig.get("identities", [])
    if isinstance(identities_raw, dict):
        for id_op in identities_raw.values():
            all_op_ids.add(id_op)
    elif isinstance(identities_raw, list):
        for id_op in identities_raw:
            if isinstance(id_op, dict):
                all_op_ids.add(id_op.get("skill_id", ""))
            elif isinstance(id_op, str):
                all_op_ids.add(id_op)

    for agent_id, adata in slices.get("agents", {}).items():
        licensed: Set[str] = set()
        for sk in adata.get("licensed_skills", []):
            if sk in all_op_ids:
                licensed.add(sk)
            elif sk in SQ._repr:
                licensed.add(SQ._repr[sk])
        adata["licensed_skills"] = sorted(list(licensed))

    with open(slice_path, "w", encoding="utf-8") as f:
        json.dump(slices, f, indent=2)

    # 6. Archive culled concrete skills — OPT-IN ONLY
    culled = SQ.cull_list()
    if archive_culled:
        os.makedirs(archived_dir, exist_ok=True)
        for sid in culled:
            s_path = os.path.join(skills_dir, sid)
            if os.path.exists(s_path):
                dest_path = os.path.join(archived_dir, sid)
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                shutil.move(s_path, dest_path)
        print(f"[WARN] Archived {len(culled)} culled skill directories (archive_culled=True).")
    elif culled:
        print(
            f"[INFO] {len(culled)} operations are quotient-redundant but were NOT archived: "
            f"{sorted(culled)[:8]}" + (" ..." if len(culled) > 8 else "")
        )

    # 7. Create SKILL.md manifests for synthesized meta-skills — CREATE ONLY, NEVER OVERWRITE
    for ms in synthesized_meta_skills:
        ms_dir = os.path.join(skills_dir, ms["id"])
        os.makedirs(ms_dir, exist_ok=True)
        ms_md = os.path.join(ms_dir, "SKILL.md")
        if os.path.exists(ms_md):
            continue
        content = f"""---
name: {ms["id"]}
description: "{ms["description"]}"
status: provisional
invocation: discipline
operad_source_colours: {json.dumps(ms["source_colours"])}
operad_target_colour: "{ms["target_colour"]}"
operad_arity: {len(ms["source_colours"])}
operad_residual: "unknown"
---

# {ms["name"]}

> **PROVISIONAL — not a minted residual invariant.** Rows in
> `evidence_trace.json` are diagnostic observations only. No count of them
> supports contractivity, equivalence, quotienting, or promotion.

{ms["description"]}

AuthorityEffect: None.
"""
        with open(ms_md, "w", encoding="utf-8") as f:
            f.write(content)

    report["applied"] = True
    report["status"] = "APPLIED_EXPLICITLY"
    print(
        f"[APPLIED_EXPLICITLY] Symmetric normalization complete: "
        f"{report['concrete_ops']} concrete ops -> {report['meta_ops']} comparison ops."
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--archive-culled", action="store_true")
    arguments = parser.parse_args()
    run_compression(
        apply_changes=arguments.apply,
        archive_culled=arguments.archive_culled,
    )
