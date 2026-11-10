"""Source-bound family pilots. No answers are materialized in participant requests.

AuthorityEffect: None. Original problem definitions and judges remain sovereign.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

import yaml

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
PILOTS = ROOT / "omega_engine_education/pilots"
SOURCE = PILOTS / "demo_004"
TEMPLATE = ROOT / "omega_engine_education/pfp/infrastructure/yaml/prompts/prompt_template.yaml"
CAMPAIGN = PILOTS / "matrix/max_pilot_matrix.yaml"
FAMILIES = ("a_mechanism", "b_cohomology", "c_quantum", "d_physics_mtheory", "e_formal_math", "f_program_synthesis", "harness_tests")
HIDDEN_KEYS = {"held_out_terms", "test_databases", "ground_truth", "optimal_cost", "solution", "category", "note"}


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(data):
    return sha256(data).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def stimulus(value):
    """Remove judge-only labels recursively, without coercing or repairing input."""
    if type(value) is dict:
        return {k: stimulus(v) for k, v in value.items() if k not in HIDDEN_KEYS
                and not k.startswith("expected_") and not k.endswith("_expected")}
    if type(value) is list:
        return [stimulus(v) for v in value]
    return value


def load_case(row):
    path = ROOT / row["source"]
    data = path.read_bytes()
    if digest(data) != row["sha256"]:
        raise ValueError("CASE_SOURCE_DRIFT")
    value = json.loads(data)
    return value[row["index"]] if row["index"] is not None else value


def case_rows(challenge):
    files = sorted((challenge / "judge_packet/cases").rglob("*.json"))
    if not files:
        files = sorted((challenge / "judge_packet/hidden_cases").glob("*.json"))
    if challenge.name.startswith("c025"):
        files += sorted((challenge / "participant_packet/examples").glob("*.json"))
    rows = []
    for path in files:
        raw = path.read_bytes()
        value = json.loads(raw)
        for i, case in enumerate(value if type(value) is list else [value]):
            if type(case) is not dict:
                raise ValueError(f"NON_OBJECT_CASE: {path}")
            kind = next((k for k in ("poisoned", "controls", "base") if k in path.parts), "declared")
            rows.append(dict(challenge=challenge.name[:4].upper(), source=relative(path),
                             sha256=digest(raw), index=i if type(value) is list else None,
                             partition=kind, case_id=case.get("case_id", case.get("id", f"item_{i}"))))
    # Freeze disjoint development/held-out cases across the entire difficulty
    # range. Keep all original cases available for later widening.
    for i, row in enumerate(rows):
        row["split"] = "development" if i % 3 == 0 else "held_out"
    return rows


def task_contract(path):
    text = path.read_text(encoding="utf-8-sig")
    # JSON examples include solved outputs. Replace their values with a schema
    # shape, preserving field names and container structure only.
    def schema(value):
        if type(value) is dict:
            return {"type": "object", "properties": {k: schema(v) for k, v in value.items()}}
        if type(value) is list:
            return {"type": "array", "items": schema(value[0]) if value else {}}
        return {"type": {str: "string", int: "integer", float: "number", bool: "boolean", type(None): "null"}[type(value)]}
    def redact(match):
        try:
            return "\nWire field shape (values withheld):\n" + json.dumps(schema(json.loads(match[1]))) + "\n"
        except (ValueError, KeyError):
            return "\n[Example block withheld; follow the surrounding task contract.]\n"
    return re.sub(r"```(?:json)?\s*\n(.*?)```", redact, text, flags=re.S)


def prompt_for(row, arm="baseline", feedback=None):
    if arm not in ("baseline", "typed_witness", "transfer"):
        raise ValueError("UNKNOWN_ARM")
    template = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    source = ROOT / row["source"]
    challenge = next(p for p in source.parents if p.name[:4] == row["challenge"].lower())
    task = challenge / "participant_packet/TASK.md"
    contract = task_contract(task)
    response_schema = yaml.safe_load(template["response_schema"])
    response_schema["properties"]["answer"] = {"type": "object", "description": "The original task's complete certificate; task-specific judges enforce its wire types."}
    response_schema["required"].append("answer")
    seed = {"challenge": row["challenge"], "task_contract": contract, "input": stimulus(load_case(row))}
    rule = ""
    if arm in ("typed_witness", "transfer"):
        rule = ("Before submitting, privately check the task's exact wire types and all witness equations. "
                "Preserve identifiers. Use canonical exact rationals where required. A scalar claim without its witness is insufficient. "
                "Do not copy judge labels or invent a host acceptance. Keep the complete candidate in answer; leave sections empty.")
    if feedback is not None:
        from omega_engine_symbol_game.use_cases.pfp_proposal import REPAIR_RULES
        if feedback not in REPAIR_RULES.values():
            raise ValueError("UNTRUSTED_REPAIR_FEEDBACK")
        rule += "\nPrevious stage host feedback: " + feedback
    user = json.dumps(seed, ensure_ascii=False, sort_keys=True) + "\n" + rule
    return dict(system=template["system_prompt"] + "\nTask license: the mathematical operations explicitly defined in task_contract are licensed for this finite task only.\n" +
                "Return only this JSON response schema:\n" + json.dumps(response_schema),
                user=template["user_prompt"].replace("[USER PROMPT]", user),
                response_schema=response_schema)


def build():
    families = []
    for family_index, family in enumerate(FAMILIES):
        entries = []
        for challenge in sorted((SOURCE / family).glob("c[0-9][0-9][0-9]*")):
            if not challenge.is_dir():
                continue
            rows = case_rows(challenge)
            entries.append(dict(challenge=challenge.name[:4].upper(), path=relative(challenge), cases=rows))
        spec_files = sorted((SOURCE / family).glob("c[0-9][0-9][0-9]_*.md"))
        for spec in spec_files:
            if spec.name[:4].upper() not in {e["challenge"] for e in entries}:
                entries.append(dict(challenge=spec.name[:4].upper(), path=relative(spec), cases=[],
                                    status="PLANNED", blocker="NO_EXECUTABLE_MECHANISM_PROTOCOL"))
        entries.sort(key=lambda e: e["challenge"])
        for entry in entries:
            entry["task_family"] = Path(entry["path"]).stem[5:]
        family_spec = dict(pilot_id=f"pilot_{192 + family_index:07d}", family=family,
                           challenges=entries, mechanism_contracts=[dict(source=relative(p), sha256=digest(p.read_bytes())) for p in spec_files])
        families.append(family_spec)
    plan = dict(schema="pfp.challenge-learning.v1", authority_effect="None", source_base="182544f602ef063eb5c2d3e06d5a80478bff26ad",
                template=dict(source=relative(TEMPLATE), sha256=digest(TEMPLATE.read_bytes())),
                max_stages=2, per_run_cap_microusd=50000, families=families,
                claims=dict(model_advantage="UNMEASURED", rust_scope="Q40 certificate adapter only", automatic_admission=False))
    existing = CAMPAIGN.read_text(encoding="utf-8").split("\npfp_challenge_learning:\n")[0]
    CAMPAIGN.write_text(existing.rstrip() + "\n" + yaml.safe_dump({"pfp_challenge_learning": plan}, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return plan


def load_plan():
    plan = yaml.safe_load(CAMPAIGN.read_text(encoding="utf-8"))["pfp_challenge_learning"]
    if digest(TEMPLATE.read_bytes()) != plan["template"]["sha256"]:
        raise ValueError("TEMPLATE_DRIFT")
    return plan


def selected_rows(family, limit_per_challenge=4):
    for challenge in family["challenges"]:
        rows = challenge["cases"]
        if rows:
            # Quantiles include hard and poisoned cases; no easier replacements
            # are substituted when a checker or solver fails.
            indices = sorted({round(i * (len(rows) - 1) / (limit_per_challenge - 1)) for i in range(limit_per_challenge)})
            yield from (rows[i] for i in indices)
