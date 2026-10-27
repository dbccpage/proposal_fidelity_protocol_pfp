"""Original C001 finite-witness adapter, separate from its neural experiment.

This selects public development inputs and uses the existing Python certificate
checker. It neither installs attention hooks nor substitutes for the prescribed
native/independent checks, frozen local pipelines or paired hidden-case arms.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from pfp.tests.demo_004.a_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_public_set,
)
from pfp.tests.demo_004.a_mechanism.c001_attention_distractor_mask.solver import (
    verify_certificate,
)
from pfp.domain.contracts.pfp_runtime import PfpTaskPrompt
from pfp.use_cases.pfp_proposal import task_turn_validator

from .catalog import ROOT, canonical, digest, relative


CHALLENGE_PATH = ROOT / "pfp/tests/demo_004/a_mechanism/c001_attention_distractor_mask"
TASK_PATH = CHALLENGE_PATH.with_name("c001_attention_distractor_mask_task_level.md")
GENERATOR_PATH = CHALLENGE_PATH / "case_generator.py"
SOURCE_PATHS = (Path(__file__), TASK_PATH, GENERATOR_PATH, CHALLENGE_PATH / "solver.py",
    CHALLENGE_PATH / "solve.py")
CHECKER_ID = "c001:python-original-finite-witness-v1"
OPEN_REQUIREMENTS = (
    "Pinned primary/replication local models, tokenizer and prompt-template digests, eager attention and compute accounting.",
    "Actual labelled-span attention masking/readout and matched null/carrier/random/delete/gated controls.",
    "Original 200 hidden paired cases, seed replications, McNemar analysis and false-witness safety gate.",
    "C001 native propagation/graph_phi1 parity and the specified independent Fraction checker remain unbound here.",
)
_HOST_FIELDS = ("case_id", "kind", "items", "edges", "claims", "prompt_text",
    "distractor_spans", "carrier_spans", "seed")


def public_case(case: dict) -> dict:
    """Retain the original prose stimulus; parsed graphs and spans stay host-side.

    The claimed audit potential is already present in this original prose.
    Supplying another clean graph would bypass the distractor-reading task.
    """
    return {key: case[key] for key in ("case_id", "kind", "prompt_text")}


def _host_case(case: dict) -> dict:
    projected = {key: case[key] for key in _HOST_FIELDS if key in case}
    if case.get("kind") == "audit" and "claimed_potential" in case:
        projected["claimed_potential"] = case["claimed_potential"]
    # The original generator uses tuple spans; the PFP input is native JSON.
    return json.loads(json.dumps(projected, ensure_ascii=False, allow_nan=False))


def case_rows() -> list[dict]:
    """Describe original generated public cases without creating another corpus."""
    source_hash = digest(GENERATOR_PATH.read_bytes())
    return [dict(challenge="C001", challenge_path=relative(CHALLENGE_PATH),
        source=relative(GENERATOR_PATH), sha256=source_hash, index=index,
        partition="public", split="development", case_id=case["case_id"],
        case_sha256=digest(canonical(_host_case(case))))
        for index, case in enumerate(generate_public_set())]


def load_case(row: dict) -> dict:
    if (row.get("challenge") != "C001" or row.get("source") != relative(GENERATOR_PATH)
            or row.get("sha256") != digest(GENERATOR_PATH.read_bytes())
            or row.get("challenge_path") != relative(CHALLENGE_PATH)):
        raise ValueError("C001_CASE_SOURCE_DRIFT")
    cases = generate_public_set()
    index = row.get("index")
    if type(index) is not int or not 0 <= index < len(cases):
        raise ValueError("C001_CASE_INDEX_INVALID")
    case = _host_case(cases[index])
    if (row.get("case_id") != case["case_id"]
            or row.get("case_sha256") != digest(canonical(case))):
        raise ValueError("C001_CASE_BINDING_MISMATCH")
    return case


def task_text() -> str:
    return TASK_PATH.read_text(encoding="utf-8-sig")


def _object(properties: dict) -> dict:
    return dict(type="object", properties=properties, required=list(properties), additionalProperties=False)


def answer_schema(case: dict) -> dict:
    """The original response variants, with canonical decimal-string values."""
    integer = {"type": "string", "pattern": r"^(0|-?[1-9][0-9]*)$"}
    text = {"type": "string", "minLength": 1, "pattern": r"\S"}
    vertex = {"type": "string", "enum": list(case["items"])}
    pair = dict(type="array", items=vertex, minItems=2, maxItems=2)
    kind = case["kind"]
    base = dict(status={"const": "SOLVED"}, kind={"const": kind})
    if kind == "verdict":
        solved = [
            _object(dict(base, answer={"const": "CONSISTENT"},
                potential=_object({name: integer for name in case["items"]}))),
            _object(dict(base, answer={"const": "CONTRADICTION"},
                cycle=dict(type="array", items=vertex, minItems=4))),
        ]
    elif kind == "repair":
        solved = [_object(dict(base, edge=pair, value=integer))]
    elif kind == "audit":
        solved = [_object(dict(base, answer={"const": "ACCEPT"})),
            _object(dict(base, answer={"const": "REJECT"}, violated=pair))]
    else:
        raise ValueError("C001_UNSUPPORTED_CASE_KIND")
    return {"oneOf": [*solved,
        _object(dict(status={"const": "UNKNOWN"}, refusal=text)),
        _object(dict(status={"const": "OUT_OF_SCOPE"},
            witness=_object(dict(field=text, reason=text)))),
    ]}


def task_prompt(case: dict) -> PfpTaskPrompt:
    public = public_case(case)
    return PfpTaskPrompt("C001", task_text(), public, answer_schema(case))


def check_answer(case: dict, answer: dict) -> tuple[bool, str]:
    if not task_turn_validator(answer_schema(case)).is_valid(answer):
        return False, "C001_ANSWER_SCHEMA: follow the original typed witness contract"
    return verify_certificate(case, answer)
