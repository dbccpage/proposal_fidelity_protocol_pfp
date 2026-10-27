"""Tests for scoured PFP pilot and frontier prompt types.

Validates 100% typed deserialization and roundtrip fidelity without key drop across:
- spec.yaml
- response.yaml
- prompt_template.yaml
- p_star.yaml & p_star_rewrite_10.yaml
- seed.yaml
- seed_rewrite_01.yaml .. seed_rewrite_10.yaml
- MUB6 subgap_r7_enc1147_karlsson_stengle_prompt.yaml

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pfp.infrastructure.model_loading import load_yaml_model

from pfp.domain.types import AntibodySlot
from pfp.domain.types import ArmTemplate
from pfp.domain.types import EvaluationStatus
from pfp.domain.types import PromptTemplate
from pfp.domain.types import PfpUniversalPromptTemplate
from pfp.domain.types import PilotComparisonResults
from pfp.domain.types import PilotResponse
from pfp.domain.types import PilotSpec
from pfp.domain.types import PStarPrompt
from pfp.domain.types import RepresentationRewrite
from pfp.domain.types import RewriteTestPlan
from pfp.domain.types import SeedPrompt
from pfp.domain.types import TestSpec

REPO_ROOT = Path(__file__).resolve().parents[2]
PILOT_0000000 = REPO_ROOT / "pfp" / "tests" / "pilot_0000000"
MUB6_PROMPT = (
    REPO_ROOT
    / "projects"
    / "mub6"
    / "prompts"
    / "subgap_r7_enc1147_karlsson_stengle_prompt.yaml"
)


def test_pilot_spec_deserialization():
    spec_path = PILOT_0000000 / "spec.yaml"
    assert spec_path.exists()
    spec = load_yaml_model(PilotSpec, spec_path)

    assert spec.pilot_id == "pilot_0000000"
    assert spec.prompt_id == "prompt_0000000"
    assert spec.coordinates.task_family == "linear_algebra"
    assert spec.coordinates.representation_rewrite == RepresentationRewrite.RAW_PROSE
    assert spec.ingress.arm_template == ArmTemplate.A0
    assert spec.host_gate.expected_outcome == "ACCEPTED"

    raw = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    plan_path = PILOT_0000000 / raw["test_plan"]["path"]
    assert plan_path.name == "testplan.yaml"
    assert plan_path.is_file()
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    assert plan["spec"] == "spec.yaml"
    assert plan["pilot_id"] == spec.pilot_id
    assert plan["counts"]["tests"] == raw["test_plan"]["tests"]
    assert plan["counts"]["unique_cases"] == raw["test_plan"]["cases"]
    assert raw["responses"]["directory"] in ("results", "misc")
    assert (PILOT_0000000 / raw["responses"]["directory"]).is_dir()


def test_pilot_response_deserialization():
    resp_path = PILOT_0000000 / "tests" / "test_11" / "response.yaml"
    if not resp_path.exists():
        resp_path = PILOT_0000000 / "results" / "response.yaml"
    assert resp_path.exists()
    resp = load_yaml_model(PilotResponse, resp_path)

    assert resp.pilot_id == "pilot_0000000"
    assert resp.evaluation.status == EvaluationStatus.ACCEPTED
    assert resp.extracted_answer == 3
    assert resp.parsed_response is not None
    assert resp.parsed_response.summary.next_concrete_test != ""


def test_test_spec_deserialization():
    test_spec_path = PILOT_0000000 / "tests" / "test_00" / "test_spec.yaml"
    assert test_spec_path.exists()
    ts = load_yaml_model(TestSpec, test_spec_path)

    assert ts.schema_ == "pfp.test-spec.v1"
    assert ts.test_id == "seed_plain"
    assert ts.case_id == "seed"
    assert ts.expected_outcome.answer == 3
    assert ts.expected_outcome.status == "ACCEPTED"
    assert ts.actual_outcome.extracted_answer == 3
    assert ts.actual_outcome.gate_status == "ACCEPTED"
    assert ts.metrics.prompt_tokens == 58


def test_rewrite_test_plan_deserialization():
    plan_path = PILOT_0000000 / "testplan.yaml"
    assert plan_path.exists()
    plan = load_yaml_model(RewriteTestPlan, plan_path)

    assert plan.schema_ == "pfp.rewrite-test-plan.v1"
    assert plan.pilot_id == "pilot_0000000"
    assert plan.counts.unique_cases == 11
    assert plan.counts.tests == 20
    assert len(plan.cases) == 11
    assert len(plan.tests) == 20
    assert plan.expected_outcome.answer == 3


def test_pilot_comparison_results_deserialization():
    comp_path = PILOT_0000000 / "misc" / "comparison_results.yaml"
    if not comp_path.exists():
        comp_path = PILOT_0000000 / "results" / "comparison_results.yaml"
    assert comp_path.exists()
    comp = load_yaml_model(PilotComparisonResults, comp_path)

    assert comp.schema_ == "pfp.pilot-comparison-results.v1"
    assert comp.pilot_id == "pilot_0000000"
    assert comp.aggregates is not None
    assert comp.aggregates.plain_inputs.count == 11
    assert comp.aggregates.p_star_templated.count == 11
    assert comp.aggregates.overall.count == 22
    assert len(comp.tests) == 22
    assert comp.tests[0].test_id == "seed_plain"
    assert comp.tests[0].gate_status == "ACCEPTED"


def test_prompt_template_and_p_star():
    pt_path = PILOT_0000000 / "prompt_template.yaml"
    pstar_path = PILOT_0000000 / "tests" / "test_11" / "p_star.yaml"
    if not pstar_path.exists():
        pstar_path = PILOT_0000000 / "p_star.yaml"
    pstar10_path = PILOT_0000000 / "tests" / "test_21" / "p_star_rewrite_10.yaml"
    if not pstar10_path.exists():
        pstar10_path = PILOT_0000000 / "p_star_rewrite_10.yaml"

    assert pt_path.exists()
    assert pstar_path.exists()
    assert pstar10_path.exists()

    pt = load_yaml_model(PfpUniversalPromptTemplate, pt_path)
    assert pt.lineage.family_id == "[PROMPT FAMILY ID]"

    pstar = load_yaml_model(PStarPrompt, pstar_path)
    assert pstar.lineage.prompt_id == "pilot_0000000_p_star"
    assert len(pstar.guidance.rules) >= 2
    assert len(pstar.guidance.antibodies) >= 1

    pstar10 = load_yaml_model(PStarPrompt, pstar10_path)
    assert pstar10.lineage.prompt_id == "pilot_0000000_p_star_rewrite_10"
    assert pstar10.lineage.parent_id == "pilot_0000000_p_star"


def test_seed_prompt_and_all_rewrites():
    seed_path = PILOT_0000000 / "seed.yaml"
    assert seed_path.exists()
    seed = load_yaml_model(SeedPrompt, seed_path)
    assert seed.pilot_id == "pilot_0000000"
    assert seed.expected_outcome.answer == 3

    for i in range(1, 11):
        rw_path = PILOT_0000000 / "tests" / f"test_{i:02d}" / f"seed_rewrite_{i:02d}.yaml"
        if not rw_path.exists():
            rw_path = PILOT_0000000 / f"seed_rewrite_{i:02d}.yaml"
        assert rw_path.exists(), f"Missing seed_rewrite_{i:02d}.yaml"
        raw_data = yaml.safe_load(rw_path.read_text(encoding="utf-8"))

        rw = load_yaml_model(SeedPrompt, rw_path)
        assert rw.pilot_id == "pilot_0000000"
        assert rw.rewrite_metadata is not None
        assert rw.rewrite_metadata.rewrite_id == f"rewrite_{i:02d}"
        assert rw.input_typing is not None
        assert rw.input_typing.lexical_alphabet != ""
        assert rw.expected_outcome.answer == 3

        # Key coverage audit
        for key in raw_data:
            if key == "schema":
                continue
            assert hasattr(rw, key), f"Field {key} not mapped in SeedPrompt for {rw_path.name}"

        if "codebook_slots" in raw_data.get("rewrite_metadata", {}):
            assert len(rw.rewrite_metadata.codebook_slots) == len(
                raw_data["rewrite_metadata"]["codebook_slots"]
            )


def test_mub6_frontier_prompt_packet_lineage_and_antibodies():
    if not MUB6_PROMPT.exists():
        pytest.skip(f"MUB6 prompt not found at {MUB6_PROMPT}")

    pstar = load_yaml_model(PStarPrompt, MUB6_PROMPT)
    assert pstar.lineage.prompt_id == "mub6_subgap_r7_enc1147_karlsson_stengle_sos_p_star"
    assert pstar.lineage.template_id == "prompt_template_typed"
    assert pstar.lineage.template_version == "2.0.0"
    assert pstar.lineage.mutation_kind == "root_seed"
    assert pstar.lineage.mutation_notes is not None
    assert pstar.lineage.mutation_note == pstar.lineage.mutation_notes
    assert pstar.lineage.author == "gemini-frontier-architect"
    assert pstar.lineage.status == "assembled"

    assert len(pstar.guidance.antibodies) >= 3
    for ab in pstar.guidance.antibodies:
        assert isinstance(ab, AntibodySlot)
        assert ab.antibody_id.startswith("ab_")
        assert ab.severity in ["P0", "P1", "P2", "P3"]


def test_max_pilot_matrix_yaml_and_results_estate():
    matrix_dir = REPO_ROOT / "adversary" / "tests" / "pilots" / "matrix"
    matrix_yaml = matrix_dir / "max_pilot_matrix.yaml"
    matrix_md = matrix_dir / "max_pilot_matrix.md"

    assert matrix_yaml.exists(), "max_pilot_matrix.yaml must exist"
    assert not matrix_md.exists(), "max_pilot_matrix.md must be deleted"

    raw_matrix = yaml.safe_load(matrix_yaml.read_text(encoding="utf-8"))
    assert raw_matrix["schema"] == "pfp.pilot-matrix.v1"
    assert raw_matrix["task_family"] == "linear_algebra"
    assert raw_matrix["host_checker"] == "PFP-01-EXACT-LINALG"
    assert len(raw_matrix["pilots"]) == 75

    results_dir = REPO_ROOT / "adversary" / "tests" / "pilots" / "results"
    assert results_dir.exists(), "pilots/results directory must exist"

    for idx, p_info in enumerate(raw_matrix["pilots"]):
        pilot_id = p_info["pilot_id"]
        expected_id = f"pilot_{idx:07d}" if idx <= 25 else f"pilot_{idx:05d}"
        assert pilot_id == expected_id
        p_dir = results_dir / pilot_id
        assert p_dir.is_dir(), f"Missing results folder for {pilot_id}"

        # 1. spec.yaml
        spec_path = p_dir / "spec.yaml"
        assert spec_path.is_file(), f"Missing spec.yaml in {p_dir}"
        spec = load_yaml_model(PilotSpec, spec_path)
        assert spec.pilot_id == pilot_id

        # 2. seed.yaml
        seed_path = p_dir / "seed.yaml"
        assert seed_path.is_file(), f"Missing seed.yaml in {p_dir}"
        seed = load_yaml_model(SeedPrompt, seed_path)
        assert seed.pilot_id == pilot_id
        assert seed.expected_outcome.answer is not None

        # 3. p_star.yaml
        p_star_path = p_dir / "p_star.yaml"
        assert p_star_path.is_file(), f"Missing p_star.yaml in {p_dir}"
        p_star = load_yaml_model(PStarPrompt, p_star_path)
        assert p_star.lineage.prompt_id.startswith(f"pilot_")

        # 4. prompt_template.yaml
        tpl_path = p_dir / "prompt_template.yaml"
        assert tpl_path.is_file(), f"Missing prompt_template.yaml in {p_dir}"
        load_yaml_model(PfpUniversalPromptTemplate, tpl_path)

        # 5. response.yaml
        resp_path = p_dir / "response.yaml"
        assert resp_path.is_file(), f"Missing response.yaml in {p_dir}"
        resp = load_yaml_model(PilotResponse, resp_path)
        assert resp.pilot_id == pilot_id
        assert resp.evaluation.status == "ACCEPTED"
        assert resp.evaluation.expected is not None
        assert resp.evaluation.received is not None


def test_offline_evaluator_dry_run_execution(tmp_path):
    import shutil

    from adversary.tests.pilots.offline_evaluator import run_all_pilots
    source = REPO_ROOT / "adversary" / "tests" / "pilots" / "results"
    shutil.copytree(source, tmp_path / "results")
    reports = run_all_pilots(tmp_path / "results")
    assert len(reports) == 75
    assert all(r["efficacy_eligible"] is False for r in reports)
    assert all(r["provider_calls"] == 0 for r in reports)
    assert all(r["evaluation_receipt"] for r in reports)
    for original in source.glob("*/response.yaml"):
        assert original.read_bytes() == (tmp_path / "results" / original.parent.name / original.name).read_bytes()


def test_offline_evaluator_negative_mutation_suite():
    from adversary.tests.pilots.offline_evaluator import run_negative_mutation_suite

    reports = run_negative_mutation_suite()
    assert len(reports) >= 20
    assert all(r["passed"] is True for r in reports)
    assert all(r["received_status"] != "ACCEPTED" for r in reports)
    assert all(r["received_status"] == r["expected_status"] for r in reports)



