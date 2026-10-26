"""Real producer output validates against its packet schema and YAML twin.

Each case builds a packet or receipt with the producer code, then validates it
against the JSON Schema in `packet_schemas/` and, where one exists, against its
twin in `infrastructure/yaml/schemas/`. The negative controls check that a
schema rejects an extra field and a float where an exact string is required.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import json
from fractions import Fraction
from pathlib import Path

import jsonschema
import pytest
import yaml

from omega_engine_pfp import packet_schemas
from omega_engine_pfp.domain.aggregates import prompt_artifact
from omega_engine_pfp.domain.aggregates.code_change_bind import build_code_change_proposal_envelope
from omega_engine_pfp.domain.aggregates.code_change_proposal import CodeChangeProposalPayloadV1
from omega_engine_pfp.domain.aggregates.llm_turn_run_root import build_llm_turn_envelope
from omega_engine_pfp.domain.entities.candidate_artifact import CandidateArtifactV1
from omega_engine_pfp.domain.entities.coboundary_score import CoboundaryScoreResult

YAML_SCHEMAS = Path(packet_schemas.__file__).resolve().parents[1] / "infrastructure" / "yaml" / "schemas"


def _validator(path: Path) -> jsonschema.Draft202012Validator:
    text = path.read_text(encoding="utf-8")
    schema = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _errors(path: Path, document: dict) -> list[str]:
    return [error.message for error in _validator(path).iter_errors(document)]


def _artifact():
    return prompt_artifact.compile_prompt_artifact(
        regime_kind="fence_only",
        regime_definition_bytes=b"regime",
        prompt_body_bytes=b"body",
        objective_typed=prompt_artifact.ObjectiveTypedV1.create(kind="retraction_turn", summary="s"),
    )


def _code_change() -> CodeChangeProposalPayloadV1:
    return CodeChangeProposalPayloadV1(
        objective="tighten a gate",
        source_revision="abc123",
        owned_paths=("omega_engine_pfp/example.py",),
        protected_paths=(),
        allowed_transforms=("edit",),
        candidate_budget=1,
        operation_budget=4,
        required_gates=("gate_syntax",),
    )


def _documents() -> dict[str, dict]:
    turn = prompt_artifact.build_payload_from_prompt_artifact(_artifact())
    change = _code_change()
    change_envelope = build_code_change_proposal_envelope(change, task_id="task-1")
    return {
        "prompt_artifact_v1": _artifact().to_dict(),
        "llm_turn_v1": turn.to_dict(),
        "code_change_proposal_v1": change.to_dict(),
        "packet_envelope_v2/llm_turn": build_llm_turn_envelope(turn, task_id="task-1").to_dict(),
        "packet_envelope_v2/code_change": change_envelope.to_dict(),
        "candidate_artifact_v1": CandidateArtifactV1(
            packet_id=change_envelope.packet_id, producer_id="model", payload={"x": 1}, witness="w"
        ).to_dict(),
        "coboundary_score_v1": CoboundaryScoreResult(
            proposal_id="p1",
            prior_residual_norm=Fraction(2),
            post_residual_norm=Fraction(1),
            residual_drop=Fraction(1),
            structural_cost=Fraction(1, 2),
            normalized_efficiency=Fraction(2, 3),
        ).to_dict(),
        "elimination_receipt_v1": prompt_artifact.create_elimination_receipt(
            packet_id="a" * 64,
            prior_residual_colour="Open",
            new_residual_colour="Closed",
            evidence_root="b" * 64,
            eliminated_obstruction_ids=["o1"],
        ).to_dict(),
    }


CASES = sorted(_documents())


def _schema_paths(case: str) -> list[Path]:
    stem = case.split("/")[0]
    paths = [packet_schemas.PACKET_SCHEMAS_ROOT / f"{stem}.schema.json"]
    twin = YAML_SCHEMAS / f"{stem}.schema.yaml"
    if twin.is_file():
        paths.append(twin)
    return paths


@pytest.mark.parametrize("case", CASES)
def test_producer_output_validates(case):
    document = _documents()[case]
    for path in _schema_paths(case):
        assert _errors(path, document) == [], path.name


@pytest.mark.parametrize("case", CASES)
def test_an_extra_field_is_rejected(case):
    document = copy.deepcopy(_documents()[case])
    document["passed"] = True
    for path in _schema_paths(case):
        assert _errors(path, document), f"{path.name} accepted an extra field"


@pytest.mark.parametrize("field", ["structural_cost", "residual_drop", "normalized_efficiency"])
def test_a_float_score_is_rejected(field):
    document = _documents()["coboundary_score_v1"]
    document[field] = 0.5
    assert _errors(packet_schemas.COBOUNDARY_SCORE_V1, document)


def test_every_schema_in_the_folder_is_a_valid_schema():
    exported = {
        getattr(packet_schemas, name)
        for name in packet_schemas.__all__
        if name != "PACKET_SCHEMAS_ROOT"
    }
    on_disk = {path for path in packet_schemas.PACKET_SCHEMAS_ROOT.iterdir() if path.suffix == ".json"}
    assert exported == on_disk
    for path in sorted(on_disk - {packet_schemas.KILL_CONDITION_REFUSAL_MAP_V1}):
        _validator(path)
