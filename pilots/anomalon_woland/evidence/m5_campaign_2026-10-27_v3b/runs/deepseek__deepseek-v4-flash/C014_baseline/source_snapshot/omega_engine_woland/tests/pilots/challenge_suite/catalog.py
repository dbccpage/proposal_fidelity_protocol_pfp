"""Source-bound family pilots. No answers are materialized in participant requests.

AuthorityEffect: None. Original problem definitions and judges remain sovereign.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import yaml

from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from omega_engine_pfp.infrastructure.adapters.pfp_evidence import resource_root
from omega_engine_pfp.use_cases.pfp_prompt import AssemblePfpPromptUseCase

ROOT = resource_root(Path(__file__))
PILOTS = ROOT / "omega_engine_woland/tests/pilots"
SOURCE = ROOT / "omega_engine_pfp/tests/demo_004"
# C051-C055 and C059 kept the education catalog identity but live beside
# demo_004. Those prefixes must be tried before the demo_004 prefix.
_SYNTHESIS_UNDER_PILOTS = (
    "c051_exact_lp_solver_with_duals",
    "c052_maxflow_mincut_certificates",
    "c053_bareiss_fraction_free_matrix_inversion",
    "c054_exact_linear_systems",
    "c055_assignment_with_potentials",
    "c059_sql_null_total_query_synthesis",
)
_MOVED_PREFIXES = (
    *(
        (
            f"omega_engine_education/pilots/demo_004/f_program_synthesis/{name}",
            f"omega_engine_woland/tests/pilots/{name}",
        )
        for name in _SYNTHESIS_UNDER_PILOTS
    ),
    *(
        (
            f"omega_engine_pfp/tests/pilots/{name}",
            f"omega_engine_woland/tests/pilots/{name}",
        )
        for name in _SYNTHESIS_UNDER_PILOTS
    ),
    ("omega_engine_education/pilots/demo_004", "omega_engine_pfp/tests/demo_004"),
    *(
        (
            f"omega_engine_education/pilots/pilot_{index:07d}",
            f"omega_engine_woland/tests/pilots/pilot_{index:07d}",
        )
        for index in range(6)
    ),
    *(
        (
            f"omega_engine_pfp/tests/pilot_{index:07d}",
            f"omega_engine_woland/tests/pilots/pilot_{index:07d}",
        )
        for index in range(6)
    ),
    ("omega_engine_education/pilots", "omega_engine_woland/tests/pilots"),
)


def relocated(relative: str) -> str:
    """Open a frozen education locator at the directory it was moved to."""
    text = str(relative).replace("\\", "/")
    for old, new in _MOVED_PREFIXES:
        if text == old or text.startswith(old + "/"):
            return new + text[len(old) :]
    return text
TEMPLATE = ROOT / "omega_engine_pfp/infrastructure/yaml/prompts/prompt_template.yaml"
CAMPAIGN = PILOTS / "matrix/max_pilot_matrix.yaml"
FAMILIES = (
    "a_mechanism",
    "b_cohomology",
    "c_quantum",
    "d_physics_mtheory",
    "e_formal_math",
    "f_program_synthesis",
    "harness_tests",
)


def canonical(value):
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        + "\n"
    ).encode("utf-8")


def digest(data):
    return sha256(data).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def load_case(row):
    if row["challenge"] == "C001":
        from .c001 import load_case as load_c001

        return load_c001(row)
    path = ROOT / relocated(row["source"])
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
            kind = next(
                (k for k in ("poisoned", "controls", "base") if k in path.parts), "declared"
            )
            rows.append(
                dict(
                    challenge=challenge.name[:4].upper(),
                    source=relative(path),
                    sha256=digest(raw),
                    index=i if type(value) is list else None,
                    partition=kind,
                    case_id=case.get("case_id", case.get("id", f"item_{i}")),
                )
            )
    # Freeze disjoint development/held-out cases across the entire difficulty
    # range. Keep all original cases available for later widening.
    for i, row in enumerate(rows):
        row["split"] = "development" if i % 3 == 0 else "held_out"
    return rows


def mechanism_rows():
    from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.cases import (
        get_hidden_base_cases,
        get_public_examples,
        get_relabel_controls,
    )

    path = PILOTS / "pilot_0000192/cases/c005.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    cases = get_public_examples() + get_hidden_base_cases() + get_relabel_controls()
    path.write_bytes(canonical(cases))
    challenge = SOURCE / "a_mechanism/c005_hosted_decode_controls"
    return [
        dict(
            challenge="C005",
            challenge_path=relative(challenge),
            source=relative(path),
            sha256=digest(path.read_bytes()),
            index=i,
            partition="public" if i < 30 else "hidden_base" if i < 130 else "controls",
            split="development" if i < 30 else "held_out",
            case_id=case["case_id"],
        )
        for i, case in enumerate(cases)
    ]


def prompt_input_paths(row):
    """Files consumed by prompt assembly, including non-Python task inputs."""
    source = ROOT / relocated(row["source"])
    challenge = (
        ROOT / relocated(row["challenge_path"])
        if "challenge_path" in row
        else next(p for p in source.parents if p.name[:4] == row["challenge"].lower())
    )
    task = challenge / ("TASK.md" if row["challenge"] == "C005" else "participant_packet/TASK.md")
    return TEMPLATE, source, task


def prompt_for(row, arm="baseline", feedback=None):
    """Load education-owned inputs; the runtime assembles the participant prompt."""
    template_path, _source, task = prompt_input_paths(row)
    template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    case = load_case(row)
    answer_schema = None
    if row["challenge"] == "C005":
        from omega_engine_pfp.tests.demo_004.a_mechanism.c005_hosted_decode_controls.schemas import (
            CONSISTENCY_JSON_SCHEMA,
            CYCLE_REPAIR_JSON_SCHEMA,
        )

        answer_schema = (
            CONSISTENCY_JSON_SCHEMA if case["kind"] == "consistency" else CYCLE_REPAIR_JSON_SCHEMA
        )["schema"]
    return (
        AssemblePfpPromptUseCase()
        .execute(
            PfpPromptTemplate(
                template["system_prompt"],
                template["user_prompt"],
                yaml.safe_load(template["response_schema"]),
            ),
            PfpTaskPrompt(
                row["challenge"], task.read_text(encoding="utf-8-sig"), case, answer_schema
            ),
            arm,
            feedback,
        )
        .to_dict()
    )


def build():
    families = []
    for family_index, family in enumerate(FAMILIES):
        entries = []
        for challenge in sorted((SOURCE / family).glob("c[0-9][0-9][0-9]*")):
            if not challenge.is_dir():
                continue
            rows = case_rows(challenge)
            if challenge.name.startswith("c005"):
                rows = mechanism_rows()
            entries.append(
                dict(challenge=challenge.name[:4].upper(), path=relative(challenge), cases=rows)
            )
        spec_files = sorted((SOURCE / family).glob("c[0-9][0-9][0-9]_*.md"))
        for spec in spec_files:
            if spec.name[:4].upper() not in {e["challenge"] for e in entries}:
                entries.append(
                    dict(
                        challenge=spec.name[:4].upper(),
                        path=relative(spec),
                        cases=[],
                        status="PLANNED",
                        blocker="NO_EXECUTABLE_MECHANISM_PROTOCOL",
                    )
                )
        entries.sort(key=lambda e: e["challenge"])
        for entry in entries:
            entry["task_family"] = Path(entry["path"]).stem[5:]
        family_spec = dict(
            pilot_id=f"pilot_{192 + family_index:07d}",
            family=family,
            challenges=entries,
            mechanism_contracts=[
                dict(source=relative(p), sha256=digest(p.read_bytes())) for p in spec_files
            ],
        )
        families.append(family_spec)
    plan = dict(
        schema="pfp.challenge-learning.v1",
        authority_effect="None",
        source_base="182544f602ef063eb5c2d3e06d5a80478bff26ad",
        template=dict(source=relative(TEMPLATE), sha256=digest(TEMPLATE.read_bytes())),
        max_stages=2,
        per_run_cap_microusd=50000,
        families=families,
        claims=dict(
            model_advantage="UNMEASURED",
            rust_scope="Q40 certificate adapter only",
            automatic_admission=False,
        ),
    )
    existing = CAMPAIGN.read_text(encoding="utf-8").split("\npfp_challenge_learning:\n")[0]
    CAMPAIGN.write_text(
        existing.rstrip()
        + "\n"
        + yaml.safe_dump({"pfp_challenge_learning": plan}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
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
            indices = sorted(
                {
                    round(i * (len(rows) - 1) / (limit_per_challenge - 1))
                    for i in range(limit_per_challenge)
                }
            )
            yield from (rows[i] for i in indices)
