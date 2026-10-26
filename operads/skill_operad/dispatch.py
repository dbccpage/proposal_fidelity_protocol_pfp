"""dispatch.py

CLI operadic registry resolver. It does not execute skills or workflows.

Usage:
    python .agents/operad/dispatch.py <skill_or_workflow_id> [--agent AGENT_ID]

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

# Single ROP kernel from domain (SoT). Relative import works when loaded as a
# package member; path fallback covers direct CLI execution.
try:
    from .domain.errors import DomainError, Failure, Result, Success
except ImportError:
    _here = os.path.dirname(os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    from domain.errors import DomainError, Failure, Result, Success


def dispatch_target(target_id: str, agent_id: Optional[str] = None) -> Result[Dict[str, Any], DomainError]:
    """Resolve a target and inspect its license; never claim execution."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(base_dir))

    sig_path = (
        os.path.join(base_dir, "json", "operad_signature.json")
        if os.path.exists(os.path.join(base_dir, "json", "operad_signature.json"))
        else os.path.join(base_dir, "operad_signature.json")
    )
    slice_path = (
        os.path.join(base_dir, "json", "agent_capability_slices.json")
        if os.path.exists(os.path.join(base_dir, "json", "agent_capability_slices.json"))
        else os.path.join(base_dir, "agent_capability_slices.json")
    )
    comp_path = (
        os.path.join(base_dir, "json", "composition_matrix.json")
        if os.path.exists(os.path.join(base_dir, "json", "composition_matrix.json"))
        else os.path.join(base_dir, "composition_matrix.json")
    )
    workflows_dir = os.path.join(repo_root, "omega_engine_operads", "workflows")

    if not os.path.exists(sig_path) or not os.path.exists(slice_path) or not os.path.exists(comp_path):
        return Failure(DomainError("FILE_NOT_FOUND", "Operad JSON registry files missing"))

    with open(sig_path, "r", encoding="utf-8") as f:
        sig = json.load(f)
    with open(slice_path, "r", encoding="utf-8") as f:
        slices = json.load(f)
    with open(comp_path, "r", encoding="utf-8") as f:
        comp_matrix = json.load(f)

    target = target_id.lower().strip()
    agent = agent_id.lower().strip() if agent_id else None

    ops = {op["skill_id"]: op for op in sig.get("operations", [])}

    # 1. Enforce Agent Capability Slice Permission Gate
    if agent:
        if agent not in slices.get("agents", {}):
            return Failure(DomainError("PERMISSION_DENIED", f"Unknown agent slice '{agent}'."))
        licensed = slices["agents"][agent].get("licensed_skills", [])
        if target not in licensed:
            return Failure(DomainError("PERMISSION_DENIED", f"Agent '{agent}' is not licensed for skill '{target}'."))
        if target in ops:
            allowed = set(slices["agents"][agent].get("sub_operad", []))
            used = set(ops[target].get("source_colours", []))
            used.add(ops[target].get("target_colour"))
            escaped = sorted(colour for colour in used if colour and colour not in allowed)
            if escaped:
                return Failure(
                    DomainError(
                        "CAPABILITY_ESCAPE",
                        f"Agent '{agent}' license for '{target}' escapes colors {escaped}.",
                    )
                )

    # 2. Check Workflow Composition JSON
    wf_path = os.path.join(workflows_dir, f"{target}.json")
    if os.path.exists(wf_path):
        with open(wf_path, "r", encoding="utf-8") as f:
            wf_data = json.load(f)
        pipeline = wf_data.get("pipeline", [])
        if type(pipeline) is not list or any(type(step) is not dict for step in pipeline):
            return Failure(DomainError("MALFORMED_WORKFLOW", "workflow pipeline must be an array of objects"))
        unknown = sorted({
            str(step.get("operation"))
            for step in pipeline
            if step.get("operation") not in ops
        })
        if unknown:
            return Failure(
                DomainError(
                    "WORKFLOW_UNKNOWN_OPERATION",
                    f"workflow '{target}' names unknown operations {unknown}",
                )
            )
        if wf_data.get("authority_effect") != "None":
            return Failure(
                DomainError(
                    "WORKFLOW_AUTHORITY_ESCAPE",
                    f"workflow '{target}' must declare authority_effect=None",
                )
            )
        if agent:
            licensed = set(slices["agents"][agent].get("licensed_skills", []))
            unlicensed = sorted({
                str(step["operation"])
                for step in pipeline
                if step["operation"] not in licensed
            })
            if unlicensed:
                return Failure(
                    DomainError(
                        "WORKFLOW_LICENSE_ESCAPE",
                        f"agent '{agent}' is not licensed for workflow operations {unlicensed}",
                    )
                )
        return Success({
            "dispatch_type": "WORKFLOW",
            "target": target,
            "agent": agent,
            "pipeline": pipeline,
            "status": "RESOLVED_NOT_EXECUTED",
            "executed": False,
            "validation": "registry_presence_only",
        })

    # 3. Check Composite Operation
    for c in comp_matrix.get("compositions", []):
        if c.get("composite_id") == target or c.get("result") == target:
            return Success({
                "dispatch_type": "COMPOSITE",
                "target": target,
                "agent": agent,
                "composition": f"{c['outer']} o_{c['slot']} {c['inner']}",
                "source_colours": c.get("source_colours"),
                "target_colour": c.get("target_colour"),
                "status": "RESOLVED_NOT_EXECUTED",
                "executed": False,
                "validation": "declared_composition_only",
            })

    # 4. Check Skill Signature
    if target in ops:
        op = ops[target]
        return Success({
            "dispatch_type": "SKILL",
            "target": target,
            "agent": agent,
            "name": op["name"],
            "source_colours": op["source_colours"],
            "target_colour": op["target_colour"],
            "arity": op["arity"],
            "residual_effect": op.get("residual_effect", "unknown"),
            "status": "RESOLVED_NOT_EXECUTED",
            "executed": False,
            "validation": "signature_only",
        })

    return Failure(DomainError("TARGET_NOT_FOUND", f"Target '{target}' not found in signatures, workflows, or compositions."))


def main() -> int:
    parser = argparse.ArgumentParser(description="Anomalon operad registry resolver (no execution)")
    parser.add_argument("target", help="Skill ID, Workflow ID, or composite operation to execute")
    parser.add_argument("--agent", help="Optional agent slice ID to enforce capability licensing", default=None)
    args = parser.parse_args()

    res = dispatch_target(args.target, args.agent)
    if res.is_success:
        val = res.unwrap()
        print(f"=== OPERAD DISPATCHER: Target='{args.target}' | Agent='{args.agent or 'UNCONSTRAINED'}' ===")
        print(f"[{val['dispatch_type']}] Resolved; NOT EXECUTED: {val}")
        return 0
    else:
        err = getattr(res, "error", DomainError("UNKNOWN_FAILURE", "resolver returned an unreadable failure"))
        print(f"[FAIL] {err.code}: {err.message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
