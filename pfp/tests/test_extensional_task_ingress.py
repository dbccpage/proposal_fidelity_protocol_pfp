"""Extensional Task Family Dynamic Ingress & Verification Test Suite.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).

Demonstrates dynamic ingestion and verification of an arbitrary text-prompt task family
without ANY modifications to core runner schemas or value object definitions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from omega_engine_pfp.domain.value_objects.taxonomy import (
    TaskFamilyVO,
    get_valid_task_families,
    register_task_family_token,
)
from omega_engine_pfp.infrastructure.pilot_runner import (
    AnswerPayload,
    PfpPilotRunner,
    SuppliedReply,
    build_requests,
    get_ground_truth,
    grade,
    materialize_results,
)
from omega_engine_pfp.domain.stages.cartesian_matrix_types import CartesianCoordinate
from omega_engine_pfp.infrastructure.catalogs.pilot_dimensions import CartesianMatrixSpace
from omega_engine_pfp.domain.task_families.task_family_types import DomainCategory
from omega_engine_pfp.domain.task_families.task_family_types import EvaluationStrategy
from omega_engine_pfp.domain.task_families.task_family_types import InputModality
from omega_engine_pfp.domain.types.pilot_spec import PilotCoordinates
from omega_engine_pfp.domain.task_families.task_family_types import SolutionModality
from omega_engine_pfp.domain.task_families.task_family_types import TaskFamilyDefinition
from omega_engine_pfp.infrastructure.catalogs.task_families import TaskFamilyRegistry


# =============================================================================
# ARBITRARY EXTENSIONAL TASK FAMILY: 3-SAT BOOLEAN CIRCUIT
# =============================================================================


def _sat_ground_truth_provider(difficulty_rung: int = 1) -> dict[str, Any]:
    """Deterministic oracle provider for arbitrary extensional boolean_circuit_sat family."""
    if difficulty_rung == 1:
        return {
            "req_0": {
                "query": (
                    "Given 3-SAT formula: (x1 OR x2 OR NOT x3) AND (NOT x1 OR x2 OR x3) AND (NOT x1 OR NOT x2 OR x3). "
                    "Provide a satisfying truth assignment as an integer bitmask where x1=bit0, x2=bit1, x3=bit2. "
                    'Return JSON {"answer": bitmask}.'
                ),
                "expected": 7,  # x1=1, x2=1, x3=1 satisfies all clauses: (1|1|0)&(0|1|1)&(0|0|1) = 1&1&1 = 1
                "clauses": [
                    [(1, True), (2, True), (3, False)],
                    [(1, False), (2, True), (3, True)],
                    [(1, False), (2, False), (3, True)],
                ],
            },
            "req_1": {
                "query": (
                    "Given unsatisfiable formula with contradictory premises: x1 AND (NOT x1). "
                    "No satisfying assignment exists. "
                    "Return answer null, status REFUSED, and witness containing remaining=[]."
                ),
                "expected": None,
                "remaining": [],
            },
        }
    else:
        return {
            "req_0": {
                "query": 'Solve higher-order 3-SAT formula for rung 2. Return {"answer": bitmask}.',
                "expected": 15,
            },
        }


@pytest.fixture(autouse=True)
def setup_registry():
    """Register the extensional family before tests and clean up after."""
    registry = TaskFamilyRegistry.get_instance()
    sat_def = TaskFamilyDefinition(
        family_id="boolean_circuit_sat",
        display_name="Propositional 3-SAT Satisfiability & Refusal Certifier",
        domain_category=DomainCategory.FORMAL_LOGIC,
        input_modality=InputModality.PLAIN_PROSE,
        solution_modality=SolutionModality.TYPED_SCHEMA_RECORD,
        evaluation_strategy=EvaluationStrategy.ORACLE_EXECUTION,
        checker_contract_id="PFP-EXT-SAT",
        supports_refusal=True,
        difficulty_metric="variable_and_clause_count",
        default_rungs={
            1: {"variables": 3, "clauses": 3, "satisfiable": True},
            2: {"variables": 4, "clauses": 8, "satisfiable": True},
        },
        is_extensional=True,
        description="Arbitrary extensional text-prompt task family for propositional satisfiability.",
    )
    registry.register(sat_def)
    registry.register_ground_truth_provider("boolean_circuit_sat", _sat_ground_truth_provider)
    yield
    # No teardown needed as registry handles overrides gracefully


class TestExtensionalTaskIngress:
    """Verifies that arbitrary text-prompt task families can be ingested without core schema changes."""

    def test_registry_registration_and_lookup(self) -> None:
        """Verify the extensional family is registered, queryable, and correctly typed."""
        registry = TaskFamilyRegistry.get_instance()
        assert registry.is_valid_family("boolean_circuit_sat")
        defn = registry.get("boolean_circuit_sat")
        assert defn is not None
        assert defn.family_id == "boolean_circuit_sat"
        assert defn.is_extensional is True
        assert defn.checker_contract_id == "PFP-EXT-SAT"
        assert defn.supports_refusal is True

    def test_task_family_value_object_acceptance(self) -> None:
        """Verify TaskFamilyVO accepts the dynamically registered extensional family."""
        tf = TaskFamilyVO("boolean_circuit_sat")
        assert str(tf) == "boolean_circuit_sat"
        assert tf.value == "boolean_circuit_sat"

        # Assert unregistered garbage is still rejected fail-closed
        with pytest.raises(ValueError):
            TaskFamilyVO("unregistered_random_domain_abc")

    def test_pilot_coordinates_pydantic_validation(self) -> None:
        """Verify PilotCoordinates accepts extensional task family."""
        coords = PilotCoordinates(
            task_family="boolean_circuit_sat",
            difficulty_rung=1,
            representation_rewrite="raw_prose",
            rewrite_count=0,
            legend_present=False,
            mode="mode_02",
            stage_count=1,
            pass_count=1,
            single_shot=True,
            antibody_active=False,
            model_class="8B",
            model_id="openrouter/meta-llama/llama-3-8b-instruct:free",
            temperature=0.0,
            target_spend_usd=0.0,
        )
        assert coords.task_family == "boolean_circuit_sat"
        assert coords.difficulty_rung == 1

    def test_spk001_request_packet_assembly(self) -> None:
        """Verify build_requests compiles extensional prompts into SPK-001 packets without leakage."""
        pilot_id = "pilot_ext_001"
        requests = build_requests(pilot_id, "boolean_circuit_sat", difficulty_rung=1)
        assert len(requests) == 2
        req0 = requests[0]
        assert req0["request_id"] == "pilot_ext_001_req_0"
        assert req0["trial_status"] == "NOT_RUN"
        user_msg = req0["messages"][1]["content"]

        # Assert zero answer leakage
        assert "expected" not in user_msg.lower()
        assert "answer: 7" not in user_msg.lower()
        assert "3-SAT formula" in user_msg

    def test_fail_closed_grading_accepted(self) -> None:
        """Verify grade accepts a correct candidate answer for extensional task."""
        pilot_id = "pilot_ext_001"
        valid_replies = [
            {"request_id": f"{pilot_id}_req_0", "raw_reply": json.dumps({"answer": 7})},
            {
                "request_id": f"{pilot_id}_req_1",
                "raw_reply": json.dumps(
                    {"answer": None, "status": "REFUSED", "witness": {"remaining": []}}
                ),
            },
        ]
        report = grade(valid_replies, pilot_id, "boolean_circuit_sat", difficulty_rung=1)
        assert report["pilot_id"] == pilot_id
        assert report["task_family"] == "boolean_circuit_sat"
        results = report["results"]
        assert results[0]["status"] == "ACCEPTED"
        assert results[0]["answer"] == 7
        assert results[1]["status"] == "ACCEPTED"
        assert results[1]["answer"] is None

    def test_fail_closed_grading_wrong_answer(self) -> None:
        """Verify grade flags incorrect candidate assignment as WRONG_ANSWER."""
        pilot_id = "pilot_ext_001"
        wrong_replies = [
            {
                "request_id": f"{pilot_id}_req_0",
                "raw_reply": json.dumps({"answer": 2}),
            },  # 2 does not satisfy
            {
                "request_id": f"{pilot_id}_req_1",
                "raw_reply": json.dumps(
                    {"answer": None, "status": "REFUSED", "witness": {"remaining": []}}
                ),
            },
        ]
        report = grade(wrong_replies, pilot_id, "boolean_circuit_sat", difficulty_rung=1)
        assert report["results"][0]["status"] == "WRONG_ANSWER"
        assert report["results"][1]["status"] == "ACCEPTED"

    def test_fail_closed_grading_false_certainty(self) -> None:
        """Verify grade flags ungrounded answer to contradictory formula as FALSE_CERTAINTY."""
        pilot_id = "pilot_ext_001"
        bluffing_replies = [
            {"request_id": f"{pilot_id}_req_0", "raw_reply": json.dumps({"answer": 7})},
            {
                "request_id": f"{pilot_id}_req_1",
                "raw_reply": json.dumps({"answer": 1}),
            },  # Bluffing certainty on unsolvable formula
        ]
        report = grade(bluffing_replies, pilot_id, "boolean_circuit_sat", difficulty_rung=1)
        assert report["results"][0]["status"] == "ACCEPTED"
        assert report["results"][1]["status"] == "FALSE_CERTAINTY"

    def test_fail_closed_grading_malformed(self) -> None:
        """Verify grade flags non-JSON or invalid syntax as MALFORMED."""
        pilot_id = "pilot_ext_001"
        malformed_replies = [
            {"request_id": f"{pilot_id}_req_0", "raw_reply": "Here is the answer: 7."},
            {
                "request_id": f"{pilot_id}_req_1",
                "raw_reply": json.dumps(
                    {"answer": None, "status": "REFUSED", "witness": {"remaining": []}}
                ),
            },
        ]
        report = grade(malformed_replies, pilot_id, "boolean_circuit_sat", difficulty_rung=1)
        assert report["results"][0]["status"] == "MALFORMED"

    def test_four_artifact_materialization(self, tmp_path: Path) -> None:
        """Verify complete 4-artifact materialization for an extensional task family."""
        pilot_id = "pilot_ext_001"
        runner = PfpPilotRunner(
            pilot_id=pilot_id,
            task_family="boolean_circuit_sat",
            difficulty_rung=1,
            pilot_dir=tmp_path,
        )
        artifacts = runner.materialize_results(tmp_path / "results")
        assert artifacts["prompt_template"].is_file()
        assert artifacts["seed"].is_file()
        assert artifacts["p_star"].is_file()
        assert artifacts["response"].is_file()

        # Parse response.yaml and verify resolved checker_id
        resp_data = yaml.safe_load(artifacts["response"].read_text(encoding="utf-8"))
        assert resp_data["schema"] == "pfp.pilot-response.v1"
        assert resp_data["evaluation"]["checker_id"] == "PFP-EXT-SAT"
        assert resp_data["evaluation"]["expected"] == 7

        # Parse seed.yaml
        seed_data = yaml.safe_load(artifacts["seed"].read_text(encoding="utf-8"))
        assert seed_data["schema"] == "pfp.seed-prompt.v1"
        assert seed_data["task_family"] == "boolean_circuit_sat"
        assert seed_data["difficulty_rung"] == 1

    def test_cartesian_matrix_coordinate_validation(self) -> None:
        """Verify the extensional task family integrates into the Cartesian Matrix space."""
        space = CartesianMatrixSpace.get_instance()
        coord = CartesianCoordinate(
            task_family="boolean_circuit_sat",
            difficulty_rung=1,
            prompt_representation="structured_spans",
            operational_mode="mode_02",
            stage_pipeline="single_pass",
            rewrite_strategy="none",
            gate_profile="canonical_exact_rational",
            inoculation_status="none",
            model_tier="class_8b",
            decoding_control="deterministic_t0",
            execution_channel="offline_fixture",
        )
        is_valid, errors = space.validate_coordinate(coord)
        assert is_valid is True, f"Validation errors: {errors}"
        assert coord.coordinate_vector()[0] == "boolean_circuit_sat"
        assert coord.coordinate_vector()[1] == 1
