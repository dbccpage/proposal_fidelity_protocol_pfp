"""Tests for PFP Pilot YAML Schemas, Pilot Types, and Pilot Suite Execution.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
import base64
import json
import pytest
import yaml

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from pfp.use_cases.evaluate_pilot_suite import (
    EvaluatePilotSuiteUseCase,
)
from pfp.tests.pilot_custody_support import is_historical_dossier
from pfp.tests.test_pilot_matrix_pfp import make_gateway
from pfp.infrastructure.providers import OpenRouterLiveProvider


def accounted_suite(gateway):
    return EvaluatePilotSuiteUseCase(
        OpenRouterLiveProvider(default_model="vendor/model", gateway=gateway, max_output_tokens=256)
    )


@pytest.fixture
def accounted_pilot(tmp_path):
    pilot = tmp_path / "pilot"
    pilot.mkdir()
    (pilot / "seed.yaml").write_text(
        yaml.safe_dump({"seed_prompt": "Compute one plus two.", "expected_outcome": {"answer": 3}}),
        encoding="utf-8",
    )
    return pilot


def suite_specs(pilot):
    return [
        dict(
            test_id=f"case_{index}",
            test_kind="plain_input",
            case_id=str(index),
            source_file="seed.yaml",
            source_path=str(pilot / "seed.yaml"),
            response_filename=f"response_{index}.yaml",
            messages=[dict(role="user", content="Compute one plus two.")],
        )
        for index in range(3)
    ]


def test_accounted_suite_exact_binding_wire_and_original_judge(accounted_pilot, tmp_path):
    gateway, provider = make_gateway(tmp_path, answer={"answer": 3})
    result = (
        accounted_suite(gateway)
        .execute(
            accounted_pilot,
            "vendor/model",
            suite_specs(accounted_pilot),
            output_dir=tmp_path / "new",
            max_cases=2,
            max_provider_calls=4,
            max_output_tokens=256,
        )
        .unwrap()
    )
    assert len(provider.calls) == 2 and result["total_tests"] == 2
    assert all(row["is_correct"] for row in result["tests"])
    response = yaml.safe_load((tmp_path / "new" / "response_1.yaml").read_text())
    assert (
        base64.b64decode(response["exchange"]["provider_wire"]["raw_reply_base64"]) == provider.raw
    )
    prepared = json.loads(provider.calls[0].user)
    assert json.loads(prepared["input"]["prompt"]) == suite_specs(accounted_pilot)[0]["messages"]
    assert "expected_outcome" not in prepared["input"]["prompt"]
    assert not (accounted_pilot / "results").exists()


def test_accounted_suite_unknown_cost_stops_and_persists_partial(accounted_pilot, tmp_path):
    gateway, provider = make_gateway(tmp_path, answer={"answer": 3}, cost=None)
    result = (
        accounted_suite(gateway)
        .execute(
            accounted_pilot,
            "vendor/model",
            suite_specs(accounted_pilot),
            output_dir=tmp_path / "new",
            max_provider_calls=4,
            max_output_tokens=256,
        )
        .unwrap()
    )
    assert len(provider.calls) == 1 and result["stop_reason"] == "CompletedCostUnknown"
    assert result["aggregates"]["overall"]["total_cost_usd"] is None
    assert not result["tests"][0]["is_correct"] and result["unattempted_test_ids"] == [
        "case_1",
        "case_2",
    ]
    assert (tmp_path / "new" / "comparison_results.yaml").is_file()


@pytest.mark.parametrize("raw", ["not json", '{"task_id":"wrong","answer":{"answer":3}}'])
def test_accounted_suite_malformed_binding_never_reaches_judge(
    accounted_pilot, tmp_path, monkeypatch, raw
):
    gateway, provider = make_gateway(tmp_path, raw_content=raw)
    monkeypatch.setattr(
        "pfp.use_cases.evaluate_pilot_suite.evaluate_candidate",
        lambda *args: pytest.fail("unbound reply reached original judge"),
    )
    result = (
        accounted_suite(gateway)
        .execute(
            accounted_pilot,
            "vendor/model",
            suite_specs(accounted_pilot),
            output_dir=tmp_path / "new",
            max_cases=1,
            max_provider_calls=4,
            max_output_tokens=256,
        )
        .unwrap()
    )
    assert len(provider.calls) == 1 and not result["tests"][0]["is_correct"]
    assert result["tests"][0]["gate_status"] == "MALFORMED"
    assert result["aggregates"]["overall"]["accuracy_percent"] is None
    assert result["aggregates"]["overall"]["malformed_or_infrastructure_count"] == 1


def test_accounted_suite_raw_provider_refuses_before_output(accounted_pilot, tmp_path):
    from pfp.infrastructure.providers import OpenRouterLiveProvider

    result = EvaluatePilotSuiteUseCase(
        OpenRouterLiveProvider(api_key="fixture-key", default_model="vendor/model")
    ).execute(accounted_pilot, "vendor/model", output_dir=tmp_path / "new")
    assert result.is_err and "PFP_ACCOUNTED_GATEWAY_REQUIRED" in result.unwrap_err().message
    assert not (tmp_path / "new").exists()


def test_accounted_suite_dry_fixture_and_no_overwrite(accounted_pilot, tmp_path):
    case = EvaluatePilotSuiteUseCase()
    result = case.execute(
        accounted_pilot, output_dir=tmp_path / "new", dry_run=True, max_cases=1
    ).unwrap()
    assert result["evidence_grade"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    assert result["provider_calls"] == 0 and result["tests"][0]["is_correct"]
    retained = (tmp_path / "new" / "comparison_results.yaml").read_bytes()
    refused = case.execute(accounted_pilot, output_dir=tmp_path / "new", dry_run=True)
    assert (
        refused.is_err and (tmp_path / "new" / "comparison_results.yaml").read_bytes() == retained
    )


def test_accounted_suite_duplicate_json_keys_are_not_sanitized_into_acceptance():
    from pfp.use_cases.evaluate_pilot_suite import sanitize_raw_reply

    assert sanitize_raw_reply('{"answer":0,"answer":3}')[1] is False


def test_accounted_suite_smaller_injected_allowance_refuses(accounted_pilot, tmp_path):
    gateway, provider = make_gateway(tmp_path, answer={"answer": 3}, max_calls=4)
    result = accounted_suite(gateway).execute(
        accounted_pilot,
        "vendor/model",
        output_dir=tmp_path / "new",
        max_provider_calls=1,
        max_output_tokens=256,
    )
    assert result.is_err and not provider.calls and not (tmp_path / "new").exists()


@pytest.mark.parametrize("change", ["missing_case", "escape", "collision", "suffix"])
def test_accounted_suite_bad_spec_refuses_before_send(accounted_pilot, tmp_path, change):
    gateway, provider = make_gateway(tmp_path, answer={"answer": 3})
    specs = suite_specs(accounted_pilot)
    suffix = ""
    if change == "missing_case":
        del specs[0]["case_id"]
    elif change == "escape":
        specs[0]["response_filename"] = "../seed.yaml"
    elif change == "collision":
        specs[0]["response_filename"] = "comparison_results.yaml"
    else:
        suffix = "/../../seed"
    result = accounted_suite(gateway).execute(
        accounted_pilot,
        "vendor/model",
        specs,
        suffix,
        output_dir=tmp_path / "new",
        max_provider_calls=4,
        max_output_tokens=256,
    )
    assert result.is_err and not provider.calls and not (tmp_path / "new").exists()


def test_accounted_suite_unmatched_case_ratios_unavailable_and_micro_cost(
    accounted_pilot, tmp_path
):
    gateway, provider = make_gateway(tmp_path, answer={"answer": 3}, cost=0.0000001)
    specs = suite_specs(accounted_pilot)[:2]
    specs[1]["test_kind"] = "p_star_templated"
    result = (
        accounted_suite(gateway)
        .execute(
            accounted_pilot,
            "vendor/model",
            specs,
            output_dir=tmp_path / "new",
            max_provider_calls=4,
            max_output_tokens=256,
        )
        .unwrap()
    )
    ratios = result["aggregates"]["ratios_templated_vs_plain"]
    assert ratios["status"] == "UNAVAILABLE" and ratios["cost_ratio"] is None
    assert all(
        row["cost_microusd"] == 1 and row["cost_usd"] == 0.0000001 for row in result["tests"]
    )


@pytest.mark.parametrize("extra", [None, "malformed", "duplicate"])
def test_accounted_suite_ratios_require_only_complete_unique_pairs(accounted_pilot, tmp_path, extra):
    from dataclasses import replace
    from operations.domain.rop.result import Ok

    gateway, provider = make_gateway(tmp_path, answer={"answer": 3})
    specs = suite_specs(accounted_pilot)[:2 if extra is None else 3]
    for spec in specs:
        spec["case_id"] = "A"
    specs[-1]["test_kind"] = "p_star_templated"
    if extra == "malformed":
        specs[1]["case_id"] = "B"
        send = provider.complete_result

        def varied(request, **options):
            result = send(request, **options)
            if len(provider.calls) == 2:
                wire = json.loads(result.value.reply_bytes)
                wire["choices"][0]["message"]["content"] = "not JSON"
                return Ok(replace(result.value,
                    candidate=replace(result.value.candidate, content="not JSON"),
                    reply_bytes=json.dumps(wire).encode()))
            return result

        provider.complete_result = varied
    report = accounted_suite(gateway).execute(accounted_pilot, "vendor/model", specs,
        output_dir=tmp_path / "new", max_provider_calls=4, max_output_tokens=256).unwrap()
    ratios = report["aggregates"]["ratios_templated_vs_plain"]
    assert report["aggregates"]["overall"]["known_cost_subtotal_usd"] == len(specs) * 0.000001
    assert ratios["status"] == ("AVAILABLE" if extra is None else "UNAVAILABLE")
    assert ratios["cost_ratio"] == (1.0 if extra is None else None)


def test_accounted_suite_cli_dry_result_and_explicit_live_model(accounted_pilot, tmp_path, capsys):
    from pfp.entrypoints.cli.pfp import main

    assert (
        main(
            [
                "run-pilot-suite",
                "--pilot-dir",
                str(accounted_pilot),
                "--output-dir",
                str(tmp_path / "dry"),
                "--max-cases",
                "1",
                "--dry-run",
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert (
        report["provider_calls"] == 0
        and report["evidence_grade"] == "HOST_REFERENCE_SELF_CONSISTENCY"
    )
    assert (
        main(
            [
                "run-pilot-suite",
                "--pilot-dir",
                str(accounted_pilot),
                "--output-dir",
                str(tmp_path / "live"),
            ]
        )
        != 0
    )
    assert not (tmp_path / "live").exists()


@pytest.mark.parametrize("alias", ["RESPONSE_0.yaml", "trailing.yaml.", "trailing.yaml ", "ACCOUNTING.SQLITE3"])
def test_accounted_suite_windows_alias_refuses_before_send(accounted_pilot, tmp_path, alias):
    gateway, provider = make_gateway(tmp_path, answer={"answer": 3})
    specs = suite_specs(accounted_pilot)
    specs[1]["response_filename"] = alias
    result = accounted_suite(gateway).execute(accounted_pilot, "vendor/model", specs,
        output_dir=tmp_path / "new", max_provider_calls=4, max_output_tokens=256)
    assert result.is_err and not provider.calls and not (tmp_path / "new").exists()


def test_accounted_suite_pending_settlement_keeps_answer_and_stops(
    accounted_pilot, tmp_path, monkeypatch
):
    from pfp.infrastructure import pilot_matrix

    complete = pilot_matrix.complete_pilot_turn

    def pending(*args, **kwargs):
        return dict(complete(*args, **kwargs), attempt_state="CompletedPendingSettlement")

    monkeypatch.setattr(pilot_matrix, "complete_pilot_turn", pending)
    gateway, provider = make_gateway(tmp_path, answer={"answer": 3})
    result = (
        accounted_suite(gateway)
        .execute(
            accounted_pilot,
            "vendor/model",
            suite_specs(accounted_pilot),
            output_dir=tmp_path / "new",
            max_provider_calls=4,
            max_output_tokens=256,
        )
        .unwrap()
    )
    assert len(provider.calls) == 1 and result["stop_reason"] == "CompletedPendingSettlement"
    response = yaml.safe_load((tmp_path / "new" / "response_0.yaml").read_text())
    assert response["parsed_response"] == {"answer": 3}
    assert not response["evaluation"]["judge_eligible"] and not result["tests"][0]["is_correct"]


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def pilots_yaml_dir(repo_root: Path) -> Path:
    return Path(__file__).resolve().parents[1] / "infrastructure" / "yaml" / "pilots"


@pytest.fixture(scope="module")
def pilot_0000000_dir(repo_root: Path) -> Path:
    return repo_root / "adversary" / "tests" / "pilots" / "pilot_0000000"


def test_pilot_types_catalog_loads(pilots_yaml_dir: Path) -> None:
    catalog_path = pilots_yaml_dir / "pilot_types.yaml"
    assert catalog_path.is_file(), f"Catalog not found: {catalog_path}"
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    assert data["meta"]["schema"] == "pfp.pilot-types.v1"
    assert data["meta"]["authority_effect"] == "None"
    
    types = data["types"]
    assert "PilotSpec" in types
    assert "SeedPrompt" in types
    assert "PStarPrompt" in types
    assert "RewriteTestPlan" in types
    assert "TestSpec" in types
    assert "PilotResponse" in types
    assert "PilotComparisonResults" in types

    seed_subtypes = types["SeedPrompt"]["subtypes"]
    assert len(seed_subtypes) == 11
    assert "pfp.seed-prompt.plain-text" in seed_subtypes
    assert "pfp.seed-prompt.math-formal" in seed_subtypes
    assert "pfp.seed-prompt.codebook-cipher" in seed_subtypes


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema required for schema verification")
def test_pilot_spec_schema_validates(pilots_yaml_dir: Path, pilot_0000000_dir: Path) -> None:
    schema = yaml.safe_load((pilots_yaml_dir / "pilot_spec_v1.schema.yaml").read_text(encoding="utf-8"))
    instance = yaml.safe_load((pilot_0000000_dir / "spec.yaml").read_text(encoding="utf-8"))
    jsonschema.validate(instance=instance, schema=schema)


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema required for schema verification")
def test_seed_prompts_validate(pilots_yaml_dir: Path, pilot_0000000_dir: Path) -> None:
    schema = yaml.safe_load((pilots_yaml_dir / "seed_prompt_v1.schema.yaml").read_text(encoding="utf-8"))
    seed_files = [pilot_0000000_dir / "seed.yaml"]
    tests_dir = pilot_0000000_dir / "tests"
    for i in range(1, 11):
        t_dir = tests_dir / f"test_{i:02d}"
        named_f = t_dir / f"seed_rewrite_{i:02d}.yaml"
        inp_f = t_dir / "input.yaml"
        root_f = pilot_0000000_dir / f"seed_rewrite_{i:02d}.yaml"
        if named_f.is_file():
            seed_files.append(named_f)
        elif inp_f.is_file():
            seed_files.append(inp_f)
        elif root_f.is_file():
            seed_files.append(root_f)
    assert len(seed_files) == 11
    for sf in seed_files:
        instance = yaml.safe_load(sf.read_text(encoding="utf-8"))
        jsonschema.validate(instance=instance, schema=schema)


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema required for schema verification")
def test_p_star_prompts_validate(pilots_yaml_dir: Path, pilot_0000000_dir: Path) -> None:
    schema = yaml.safe_load((pilots_yaml_dir / "p_star_prompt_v1.schema.yaml").read_text(encoding="utf-8"))
    tests_dir = pilot_0000000_dir / "tests"
    p_star_seed = tests_dir / "test_11" / "p_star.yaml"
    p_star_v1_files = [p_star_seed if p_star_seed.is_file() else pilot_0000000_dir / "p_star.yaml"]
    for i in range(1, 11):
        t_dir = tests_dir / f"test_{i+11:02d}"
        named_f = t_dir / f"p_star_rewrite_{i:02d}.yaml"
        inp_f = t_dir / "input.yaml"
        root_f = pilot_0000000_dir / f"p_star_rewrite_{i:02d}.yaml"
        if named_f.is_file():
            p_star_v1_files.append(named_f)
        elif inp_f.is_file():
            p_star_v1_files.append(inp_f)
        elif root_f.is_file():
            p_star_v1_files.append(root_f)
    assert len(p_star_v1_files) == 11
    p_star_all = list(pilot_0000000_dir.glob("p_star*.yaml"))
    for t_dir in tests_dir.iterdir():
        if t_dir.is_dir() and int(t_dir.name.split("_")[1]) >= 11:
            for pf in t_dir.glob("p_star*.yaml"):
                if pf not in p_star_all:
                    p_star_all.append(pf)
            inp_p = t_dir / "input.yaml"
            if inp_p.is_file() and inp_p not in p_star_all:
                p_star_all.append(inp_p)
    for pf in p_star_all:
        instance = yaml.safe_load(pf.read_text(encoding="utf-8"))
        if "task" in instance and "prompt" in instance:
            # A dossier carries its typed prompt inside the task envelope.
            instance = instance["prompt"]
        jsonschema.validate(instance=instance, schema=schema)


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema required for schema verification")
def test_testplan_validates(pilots_yaml_dir: Path, pilot_0000000_dir: Path) -> None:
    schema = yaml.safe_load((pilots_yaml_dir / "rewrite_test_plan_v1.schema.yaml").read_text(encoding="utf-8"))
    instance = yaml.safe_load((pilot_0000000_dir / "testplan.yaml").read_text(encoding="utf-8"))
    jsonschema.validate(instance=instance, schema=schema)


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema required for schema verification")
def test_results_validate(pilots_yaml_dir: Path, pilot_0000000_dir: Path) -> None:
    resp_schema = yaml.safe_load((pilots_yaml_dir / "pilot_response_v1.schema.yaml").read_text(encoding="utf-8"))
    comp_schema = yaml.safe_load((pilots_yaml_dir / "pilot_comparison_results_v1.schema.yaml").read_text(encoding="utf-8"))
    test_spec_schema = yaml.safe_load((pilots_yaml_dir / "test_spec_v1.schema.yaml").read_text(encoding="utf-8"))

    results_dir = pilot_0000000_dir / "misc"
    if not results_dir.is_dir():
        results_dir = pilot_0000000_dir / "results"
    tests_dir = pilot_0000000_dir / "tests"

    # Validate encapsulated responses and test specifications
    capsule_responses = list(tests_dir.glob("test_*/response.yaml"))
    assert len(capsule_responses) >= 22, f"Expected at least 22 capsule responses, found {len(capsule_responses)}"
    for rf in capsule_responses:
        if is_historical_dossier(rf.parent):
            continue  # Historical custody only; this is not a PilotResponse verdict reissuance.
        instance = yaml.safe_load(rf.read_text(encoding="utf-8"))
        jsonschema.validate(instance=instance, schema=resp_schema)

    capsule_specs = list(tests_dir.glob("test_*/test_spec.yaml"))
    assert len(capsule_specs) >= 22, f"Expected at least 22 test specs, found {len(capsule_specs)}"
    for sf in capsule_specs:
        if is_historical_dossier(sf.parent):
            continue
        instance = yaml.safe_load(sf.read_text(encoding="utf-8"))
        jsonschema.validate(instance=instance, schema=test_spec_schema)

    # Validate aggregate comparison matrix
    comp_file = results_dir / "comparison_results.yaml"
    assert comp_file.is_file()
    comp_instance = yaml.safe_load(comp_file.read_text(encoding="utf-8"))
    jsonschema.validate(instance=comp_instance, schema=comp_schema)


def test_evaluate_pilot_suite_use_case_collects_prompts(pilot_0000000_dir: Path) -> None:
    use_case = EvaluatePilotSuiteUseCase()
    specs = use_case.build_test_specs(pilot_0000000_dir)
    assert len(specs) == 22
    plain_specs = [s for s in specs if s["test_kind"] == "plain_input"]
    p_star_specs = [s for s in specs if s["test_kind"] == "p_star_templated"]
    assert len(plain_specs) == 11
    assert len(p_star_specs) == 11
    assert plain_specs[0]["case_id"] == "seed"
    assert p_star_specs[0]["case_id"] == "seed"


def test_ab_intermediate_witness_verification(pilot_0000000_dir: Path) -> None:
    from pfp.domain.pilots.fail_closed_gate import FailClosedRefusalGate
    from pfp.domain.types.base import EvaluationStatus

    results_dir = pilot_0000000_dir / "results"
    tests_dir = pilot_0000000_dir / "tests"

    # 1. Verify the 5 accepted templated P* runs and seed_plain witness x=1 and y=2
    accepted_mapping = {
        "seed_plain": "test_00",
        "p_star_seed": "test_11",
        "p_star_rewrite_01": "test_12",
        "p_star_rewrite_02": "test_13",
        "p_star_rewrite_04": "test_15",
        "p_star_rewrite_05": "test_16",
    }
    for tid, tfolder in accepted_mapping.items():
        resp_file = tests_dir / tfolder / "response.yaml"
        if not resp_file.is_file():
            resp_file = results_dir / f"response_{tid}.yaml"
        assert resp_file.is_file(), f"Missing response file: {resp_file}"
        doc = yaml.safe_load(resp_file.read_text(encoding="utf-8"))
        reasoning = doc.get("reasoning_content", "")
        gate_res = FailClosedRefusalGate.verify_intermediate_witness(
            checker_id="PFP-01-EXACT-LINALG",
            reasoning_content=reasoning,
            witness_bindings={"x": 1, "y": 2},
        )
        assert gate_res.is_accepted, f"{tid} failed intermediate witness audit: {gate_res.reason}"
        assert gate_res.extracted_answer == {"x": 1, "y": 2}

    # 2. Verify negative fixture: heuristic shortcut claiming answer without x=1, y=2 bindings
    shortcut_reasoning = "The system is simple, so by quick inspection x+y = 3 directly."
    shortcut_res = FailClosedRefusalGate.verify_intermediate_witness(
        checker_id="PFP-01-EXACT-LINALG",
        reasoning_content=shortcut_reasoning,
        witness_bindings={"x": 1, "y": 2},
    )
    assert not shortcut_res.is_accepted
    assert shortcut_res.status == EvaluationStatus.FALSE_CERTAINTY
    assert "AB_INTERMEDIATE_WITNESS violation" in shortcut_res.reason

    # 3. Verify empty reasoning trace fails closed
    empty_res = FailClosedRefusalGate.verify_intermediate_witness(
        checker_id="PFP-01-EXACT-LINALG",
        reasoning_content="",
    )
    assert not empty_res.is_accepted
    assert empty_res.status == EvaluationStatus.FALSE_CERTAINTY


def test_pilot_0000001_structure_and_gate(pilot_0000000_dir: Path) -> None:
    """Verify pilot_0000001 directory structure, template organization, and PFP-02-GRAPH-FACTS gate."""
    from pfp.domain.pilots.fail_closed_gate import FailClosedRefusalGate
    from pfp.domain.types.base import EvaluationStatus
    from pfp.domain.types.prompt_templates import PromptTemplate, PStarPrompt

    p1_dir = pilot_0000000_dir.parent / "pilot_0000001"
    assert (p1_dir / "seed.yaml").is_file()
    assert (p1_dir / "prompt_template.yaml").is_file()
    p_star_path = p1_dir / "tests" / "test_11" / "p_star.yaml"
    assert p_star_path.is_file()
    assert (p1_dir / "README.md").is_file()
    assert (p1_dir / "misc").is_dir()
    assert not (p1_dir / "results").exists()
    assert (p1_dir / "tests").is_dir()

    # Validate PromptTemplate and PStarPrompt models
    template_data = yaml.safe_load((p1_dir / "prompt_template.yaml").read_text(encoding="utf-8"))
    pt = PromptTemplate.model_validate(template_data)
    assert pt.lineage.prompt_id == "prompt_0000001"
    assert len(pt.guidance.rules) >= 2
    assert pt.guidance.rules[0].rule_id == "rule_name_the_checker_field"
    manifest = pt.parse_system_manifest()
    assert manifest.semantic_policy_manifest.policy_id == "SPK-001"

    pstar_data = yaml.safe_load(p_star_path.read_text(encoding="utf-8"))
    pstar = PStarPrompt.model_validate(pstar_data)
    assert pstar.lineage.prompt_id == "p_star_seed"

    # Validate test_00, test_01, test_02 organization
    for tid in ["test_00", "test_01", "test_02"]:
        tdir = p1_dir / "tests" / tid
        assert tdir.is_dir()
        assert (tdir / "test_spec.yaml").is_file()
        assert (tdir / "input.yaml").is_file()
        assert (tdir / "response.yaml").is_file()

    # Test sovereign FailClosedRefusalGate for PFP-02-GRAPH-FACTS
    expected = {
        "connected": True,
        "triangle_012": True,
        "bridge_03": True,
        "edge_count": 4,
    }

    # 1. Honest answer -> ACCEPTED
    res_honest = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id="PFP-02-GRAPH-FACTS",
        expected_answer=expected,
        payload={"derived_under_policy": "SPK-001", "answer": expected},
    )
    assert res_honest.is_accepted

    # 2. Schema displaced answer (test_02 reproduction) -> MALFORMED
    displaced_ans = {"connected": True, "triangle": True, "bridge": True, "edge_count": 4}
    res_displaced = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id="PFP-02-GRAPH-FACTS",
        expected_answer=expected,
        payload={"derived_under_policy": "SPK-001", "answer": displaced_ans},
    )
    assert not res_displaced.is_accepted
    assert res_displaced.status == EvaluationStatus.MALFORMED

    # 3. Wrong graph fact value -> WRONG_ANSWER
    wrong_ans = {
        "connected": True,
        "triangle_012": True,
        "bridge_03": False,
        "edge_count": 4,
    }
    res_wrong = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id="PFP-02-GRAPH-FACTS",
        expected_answer=expected,
        payload={"derived_under_policy": "SPK-001", "answer": wrong_ans},
    )
    assert not res_wrong.is_accepted
    assert res_wrong.status == EvaluationStatus.WRONG_ANSWER


def test_observer_visibility_gate_requires_the_declared_certificate(repo_root: Path) -> None:
    """A partial tally or a bare 6 must not pass the three-patch certificate."""
    from pfp.domain.pilots.fail_closed_gate import FailClosedRefusalGate

    seed_path = repo_root / "adversary" / "tests" / "pilots" / "pilot_0000051" / "seed.yaml"
    expected = yaml.safe_load(seed_path.read_text(encoding="utf-8"))["expected_outcome"]["answer"]
    honest = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id="PFP-03-OBSERVER-VISIBILITY",
        expected_answer=expected,
        payload={"answer": expected},
    )
    assert honest.is_accepted

    partial = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id="PFP-03-OBSERVER-VISIBILITY",
        expected_answer=expected,
        payload={"answer": {"raw_global_defect_I": 6}},
    )
    assert not partial.is_accepted

    scalar = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id="PFP-03-OBSERVER-VISIBILITY",
        expected_answer=expected,
        payload={"answer": 6},
    )
    assert not scalar.is_accepted

    missing_oracle = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id="PFP-03-OBSERVER-VISIBILITY",
        expected_answer=6,
        payload={"answer": expected},
    )
    assert not missing_oracle.is_accepted

