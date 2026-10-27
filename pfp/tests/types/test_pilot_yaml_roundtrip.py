"""YAML roundtrip and schema parity for pilot document models.

AuthorityEffect: None.
Fixtures in this file are constructed here. They are not live pilot documents.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from pfp.tests.pilot_custody_support import is_historical_dossier

from pfp.domain.types.base import (
    ArmTemplate,
    CheckerId,
    CohomologyDefectClass,
    EvaluationStatus,
    ExecutionMode,
    FloatingPointRisk,
    MagmaAssociativityType,
    MissingPremise,
    ModelClass,
    RepresentationRewrite,
    StructureDeltaMetric,
    TaskFamily,
    TaskModeFidelity,
    TrialStatus,
    VariableIdentifierPermutation,
)
from pfp.domain.types.pilot_comparison import (
    ComparisonAggregates,
    ComparisonRatios,
    PilotComparisonResults,
)
from pfp.domain.types.pilot_comparison import (
    TestComparisonEntry as ComparisonEntryModel,
    TestKindAggregate as KindAggregateModel,
)
from pfp.domain.types.pilot_response import (
    CostDetails,
    EvaluationReport,
    ExecutionReceipt,
    InputMetadata,
    PilotResponse,
    ProcessIntegrityPayload,
    PromptResponsePayload,
    ResponseSummaryPayload,
    SanitizationReport,
    TokenUsageDetails,
)
from pfp.domain.types.pilot_spec import (
    PilotCoordinates,
    PilotHostGate,
    PilotIngress,
    PilotResponsesReference,
    PilotSpec,
    PilotTestPlanReference,
)
from pfp.domain.types.prompt_templates import (
    AntibodySlot,
    AntipatternSlot,
    GuidanceSlot,
    HelpfulPatternSlot,
    PStarPrompt,
    PromptLineageSlot,
    PromptTemplate,
    RuleSlot,
)
from pfp.domain.types.rewrite_test_plan import (
    RewriteTestCase,
    RewriteTestItem,
    RewriteTestPlan,
)
from pfp.domain.types.rewrite_test_plan import (
    TestPlanCounts as PlanCountsModel,
    TestPlanExpectedOutcome as PlanExpectedOutcomeModel,
    TestPlanSeedRef as PlanSeedRefModel,
    TestPlanTemplateRef as PlanTemplateRefModel,
)
from pfp.domain.types.seed_prompts import (
    CodebookSlotModel,
    ExpectedOutcome,
    InputTypingModel,
    RewriteMetadataModel,
    SeedPrompt,
)
from pfp.domain.types.test_spec import (
    ActualTestOutcome,
    ExpectedTestOutcome,
    TestMetrics,
    TestSpec,
)

DRAFT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_DIR = Path(__file__).resolve().parents[2] / "infrastructure" / "yaml" / "pilots"
PILOT_0000000 = Path(__file__).resolve().parents[3] / "pfp" / "tests" / "pilot_0000000"

ROOT_MODELS = {
    "pilot_spec_v1.schema.yaml": PilotSpec,
    "seed_prompt_v1.schema.yaml": SeedPrompt,
    "p_star_prompt_v1.schema.yaml": PStarPrompt,
    "rewrite_test_plan_v1.schema.yaml": RewriteTestPlan,
    "pilot_response_v1.schema.yaml": PilotResponse,
    "pilot_comparison_results_v1.schema.yaml": PilotComparisonResults,
    "test_spec_v1.schema.yaml": TestSpec,
}

DEF_MODELS = {
    "pilot_spec_v1.schema.yaml": {
        "PilotCoordinates": PilotCoordinates,
        "PilotIngress": PilotIngress,
        "PilotHostGate": PilotHostGate,
        "PilotTestPlanReference": PilotTestPlanReference,
        "PilotResponsesReference": PilotResponsesReference,
    },
    "seed_prompt_v1.schema.yaml": {
        "ExpectedOutcome": ExpectedOutcome,
        "CodebookSlotModel": CodebookSlotModel,
        "RewriteMetadataModel": RewriteMetadataModel,
        "InputTypingModel": InputTypingModel,
    },
    "p_star_prompt_v1.schema.yaml": {
        "PromptLineageSlot": PromptLineageSlot,
        "RuleSlot": RuleSlot,
        "AntibodySlot": AntibodySlot,
        "AntipatternSlot": AntipatternSlot,
        "HelpfulPatternSlot": HelpfulPatternSlot,
        "GuidanceSlot": GuidanceSlot,
    },
    "rewrite_test_plan_v1.schema.yaml": {
        "TestPlanTemplateReference": PlanTemplateRefModel,
        "TestPlanSeedReference": PlanSeedRefModel,
        "TestPlanExpectedOutcome": PlanExpectedOutcomeModel,
        "TestPlanCounts": PlanCountsModel,
        "TestCaseModel": RewriteTestCase,
        "TestPlanEntryModel": RewriteTestItem,
    },
    "pilot_response_v1.schema.yaml": {
        "ResponseSummaryPayload": ResponseSummaryPayload,
        "ProcessIntegrityPayload": ProcessIntegrityPayload,
        "PromptResponsePayload": PromptResponsePayload,
        "SanitizationReport": SanitizationReport,
        "EvaluationReport": EvaluationReport,
        "TokenUsageDetails": TokenUsageDetails,
        "CostDetails": CostDetails,
        "InputMetadata": InputMetadata,
        "ExecutionReceipt": ExecutionReceipt,
    },
    "pilot_comparison_results_v1.schema.yaml": {
        "TestKindAggregate": KindAggregateModel,
        "ComparisonRatios": ComparisonRatios,
        "ComparisonAggregates": ComparisonAggregates,
        "TestComparisonEntry": ComparisonEntryModel,
    },
    "test_spec_v1.schema.yaml": {
        "ExpectedOutcome": ExpectedTestOutcome,
        "ActualOutcome": ActualTestOutcome,
        "TestMetrics": TestMetrics,
    },
}

ENUM_DEFS = {
    "pilot_spec_v1.schema.yaml": {
        "AuthorityEffect": ["None"],
        "TaskFamily": [item.value for item in TaskFamily],
        "RepresentationRewrite": [item.value for item in RepresentationRewrite],
        "ModelClass": [item.value for item in ModelClass],
        "ArmTemplate": [item.value for item in ArmTemplate],
        "TaskModeFidelity": [item.value for item in TaskModeFidelity],
        "VariableIdentifierPermutation": [item.value for item in VariableIdentifierPermutation],
        "FloatingPointRisk": [item.value for item in FloatingPointRisk],
        "MissingPremise": [item.value for item in MissingPremise],
        "CohomologyDefectClass": [item.value for item in CohomologyDefectClass],
        "MagmaAssociativityType": [item.value for item in MagmaAssociativityType],
        "StructureDeltaMetric": [item.value for item in StructureDeltaMetric],
        "CheckerId": [item.value for item in CheckerId],
    },
    "seed_prompt_v1.schema.yaml": {"AuthorityEffect": ["None"]},
    "p_star_prompt_v1.schema.yaml": {"AuthorityEffect": ["None"]},
    "rewrite_test_plan_v1.schema.yaml": {"AuthorityEffect": ["None"]},
    "pilot_response_v1.schema.yaml": {
        "AuthorityEffect": ["None"],
        "TrialStatus": [item.value for item in TrialStatus],
        "EvaluationStatus": [item.value for item in EvaluationStatus],
        "ExecutionMode": [item.value for item in ExecutionMode],
    },
    "pilot_comparison_results_v1.schema.yaml": {"AuthorityEffect": ["None"]},
    "test_spec_v1.schema.yaml": {
        "AuthorityEffect": ["None"],
        "EvaluationStatus": [item.value for item in EvaluationStatus],
    },
}

SPEC_YAML = """\
schema: pfp.pilot-spec.v1
pilot_id: pilot_roundtrip
prompt_id: prompt_roundtrip
phase: phase_0
split: development
coordinates:
  task_family: linear_algebra
  difficulty_rung: 1
  representation_rewrite: raw_prose
  rewrite_count: 0
  legend_present: false
  mode: mode_0
  stage_count: 1
  pass_count: 1
  single_shot: true
  antibody_active: false
  model_class: 8B
  model_id: fixture-model
  temperature: 0.0
  target_spend_usd: 0.0
ingress:
  task_mode_fidelity: literal_extraction
  variable_identifier_permutation: canonical
  floating_point_approximation_risk: exact_modular
  arm_template: A0
  missing_premise: answerable
  cohomology_defect_class: none
  magma_associativity_type: none
host_gate:
  checker_id: PFP-01-EXACT-LINALG
  response_schema: "{}"
  residual_logging: false
  structure_delta_metric: exact_rational_delta
  expected_outcome: held
"""

SEED_YAML = """\
pilot_id: pilot_roundtrip
task_family: linear_algebra
difficulty_rung: 1
request_id: req_roundtrip
seed_prompt: State the carrier. Do not compute a numeric result.
expected_outcome:
  answer: fixture-token
"""

PROMPT_YAML = """\
lineage:
  prompt_id: prompt_roundtrip
  family_id: family_roundtrip
guidance:
  rules:
    - rule_id: rule_roundtrip
      statement: Keep the carrier symbolic.
system_prompt: system
user_prompt: State the carrier.
response_schema: "{}"
"""

PLAN_YAML = """\
pilot_id: pilot_roundtrip
prompt_template:
  path: prompt_template.yaml
seed:
  path: seed.yaml
  seed_prompt: State the carrier. Do not compute a numeric result.
expected_outcome:
  answer: fixture-token
counts:
  unique_cases: 1
  tests: 1
"""

RESPONSE_YAML = """\
pilot_id: pilot_roundtrip
request_id: req_roundtrip
trial_status: NOT_RUN
sanitization:
  fence_stripped: false
  is_valid_json: false
  structure_leakage_debt_chars: 0
evaluation:
  checker_id: PFP-01-EXACT-LINALG
  expected: fixture-token
  received: fixture-token
  status: NOT_RUN
receipt: {}
"""

COMPARISON_YAML = """\
schema: pfp.pilot-comparison-results.v1
pilot_id: pilot_roundtrip
tests:
  - test_id: fixture_test
    test_kind: plain_input
    case_id: fixture_case
    source_file: seed.yaml
    response_file: response.yaml
    payload_kb: 0.1
    duration_seconds: 0.0
    prompt_tokens: 1
    completion_tokens: 1
    total_tokens: 2
    cost_usd: 0.0
    gate_status: NOT_RUN
"""

TEST_SPEC_YAML = """\
test_id: fixture_test
case_id: fixture_case
model_id: fixture-model
expected_outcome:
  answer: fixture-token
actual_outcome: {}
"""

ROUNDTRIPS = [
    (PilotSpec, SPEC_YAML),
    (SeedPrompt, SEED_YAML),
    (PromptTemplate, PROMPT_YAML),
    (PStarPrompt, PROMPT_YAML),
    (RewriteTestPlan, PLAN_YAML),
    (PilotResponse, RESPONSE_YAML),
    (PilotComparisonResults, COMPARISON_YAML),
    (TestSpec, TEST_SPEC_YAML),
]


def _load_schema(name: str) -> dict:
    return yaml.safe_load((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _required(node: dict) -> set[str]:
    return set(node.get("required") or [])


@pytest.mark.parametrize(("model", "document"), ROUNDTRIPS, ids=[item[0].__name__ for item in ROUNDTRIPS])
def test_yaml_roundtrip(model, document: str) -> None:
    first = model.from_yaml(document)
    dumped = first.to_yaml()
    assert not dumped.startswith("\ufeff")
    assert "schema_:" not in dumped
    second = model.from_yaml(dumped)
    assert second == first


@pytest.mark.parametrize(("model", "document"), ROUNDTRIPS, ids=[item[0].__name__ for item in ROUNDTRIPS])
def test_extra_field_rejected(model, document: str) -> None:
    rejected = document.rstrip() + "\nnot_a_field: 1\n"
    with pytest.raises(ValidationError):
        model.from_yaml(rejected)


def test_models_emit_draft_2020_12() -> None:
    for model in ROOT_MODELS.values():
        schema = model.model_json_schema()
        assert schema["$schema"] == DRAFT


def test_schema_required_and_enums_match_models() -> None:
    for filename, model in ROOT_MODELS.items():
        document = _load_schema(filename)
        assert document["$schema"] == DRAFT
        assert _required(document) == _required(model.model_json_schema())
        defs = document["$defs"]
        for def_name, def_model in DEF_MODELS[filename].items():
            assert _required(defs[def_name]) == _required(def_model.model_json_schema()), def_name
        for def_name, expected in ENUM_DEFS[filename].items():
            assert list(defs[def_name]["enum"]) == expected, def_name


def test_constructed_fixtures_validate_against_yaml_schemas() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    pairs = [
        ("pilot_spec_v1.schema.yaml", SPEC_YAML),
        ("seed_prompt_v1.schema.yaml", SEED_YAML),
        ("p_star_prompt_v1.schema.yaml", PROMPT_YAML),
        ("rewrite_test_plan_v1.schema.yaml", PLAN_YAML),
        ("pilot_response_v1.schema.yaml", RESPONSE_YAML),
        ("pilot_comparison_results_v1.schema.yaml", COMPARISON_YAML),
        ("test_spec_v1.schema.yaml", TEST_SPEC_YAML),
    ]
    for filename, document in pairs:
        jsonschema.validate(instance=yaml.safe_load(document), schema=_load_schema(filename))


def test_pilot_0000000_documents_still_match_schemas() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    spec = _load_schema("pilot_spec_v1.schema.yaml")
    jsonschema.validate(
        instance=yaml.safe_load((PILOT_0000000 / "spec.yaml").read_text(encoding="utf-8")),
        schema=spec,
    )
    seed_schema = _load_schema("seed_prompt_v1.schema.yaml")
    jsonschema.validate(
        instance=yaml.safe_load((PILOT_0000000 / "seed.yaml").read_text(encoding="utf-8")),
        schema=seed_schema,
    )
    for path in sorted((PILOT_0000000 / "tests").glob("test_*/seed_rewrite_*.yaml")):
        jsonschema.validate(instance=yaml.safe_load(path.read_text(encoding="utf-8")), schema=seed_schema)
    prompt_schema = _load_schema("p_star_prompt_v1.schema.yaml")
    jsonschema.validate(
        instance=yaml.safe_load((PILOT_0000000 / "prompt_template.yaml").read_text(encoding="utf-8")),
        schema=prompt_schema,
    )
    for path in sorted((PILOT_0000000 / "tests").glob("test_*/p_star*.yaml")):
        jsonschema.validate(instance=yaml.safe_load(path.read_text(encoding="utf-8")), schema=prompt_schema)
    jsonschema.validate(
        instance=yaml.safe_load((PILOT_0000000 / "testplan.yaml").read_text(encoding="utf-8")),
        schema=_load_schema("rewrite_test_plan_v1.schema.yaml"),
    )
    response_schema = _load_schema("pilot_response_v1.schema.yaml")
    spec_schema = _load_schema("test_spec_v1.schema.yaml")
    for path in sorted((PILOT_0000000 / "tests").glob("test_*/response.yaml")):
        if is_historical_dossier(path.parent):
            continue
        jsonschema.validate(instance=yaml.safe_load(path.read_text(encoding="utf-8")), schema=response_schema)
    for path in sorted((PILOT_0000000 / "tests").glob("test_*/test_spec.yaml")):
        if is_historical_dossier(path.parent):
            continue
        jsonschema.validate(instance=yaml.safe_load(path.read_text(encoding="utf-8")), schema=spec_schema)
    jsonschema.validate(
        instance=yaml.safe_load((PILOT_0000000 / "misc" / "comparison_results.yaml").read_text(encoding="utf-8")),
        schema=_load_schema("pilot_comparison_results_v1.schema.yaml"),
    )
