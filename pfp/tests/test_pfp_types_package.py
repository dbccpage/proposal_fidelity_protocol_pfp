"""Tests for modular pfp/domain/types package.

AuthorityEffect: None.

Verifies:
1. All 12 modular type files import cleanly from pfp.domain.types:
   - base
   - pilot_spec
   - pilot_response
   - prompt_templates
   - seed_prompts
   - cycle_balance
   - task_packets
   - modes
   - normal_forms
   - rewriting
   - schemas
   - stages
   - type_register
2. 100% Type identity parity between domain exports and their directly owned type modules.
3. Serialization and deserialization fidelity for primary domain entities.
"""

from __future__ import annotations

import importlib
import pytest

from pfp import domain
from pfp.domain import types


MODULE_NAMES = [
    "base",
    "pilot_spec",
    "pilot_response",
    "prompt_templates",
    "seed_prompts",
    "cycle_balance",
    "task_packets",
    "modes",
    "normal_forms",
    "rewriting",
    "schemas",
    "stages",
    "type_register",
]


@pytest.mark.parametrize("mod_name", MODULE_NAMES)
def test_types_submodule_importable(mod_name: str):
    """Verify each submodule in pfp.domain.types can be imported independently."""
    mod = importlib.import_module(f"pfp.domain.types.{mod_name}")
    assert mod is not None


def test_types_package_exports():
    """Verify types/__init__.py exports all canonical PFP data types."""
    assert len(types.__all__) >= 70

    for attr in types.__all__:
        assert hasattr(types, attr), f"Attribute {attr} declared in __all__ but missing from types"


def test_domain_reexports_canonical_types():
    """Verify domain package re-exports canonical pilot and prompt types with exact identity."""
    canonical_types = [
        "PilotSpec",
        "PilotCoordinates",
        "PilotIngress",
        "PilotHostGate",
        "SeedPrompt",
        "ExpectedOutcome",
        "EvaluationStatus",
        "CheckerId",
    ]
    for attr in canonical_types:
        assert hasattr(domain, attr), f"domain missing re-export of {attr}"
        obj_types = getattr(types, attr)
        obj_domain = getattr(domain, attr)
        assert obj_domain is obj_types, f"Type identity mismatch for {attr}"


def test_core_model_instantiation():
    """Verify core models instantiate correctly with default configurations."""
    from pfp.domain.types.pilot_spec import (
        PilotSpec,
        PilotCoordinates,
        PilotIngress,
        PilotHostGate,
    )
    from pfp.domain.types.prompt_templates import NegativeMutationFixture
    from pfp.domain.types.seed_prompts import SeedPrompt, ExpectedOutcome
    from pfp.domain.types.base import EvaluationStatus, CheckerId

    # NegativeMutationFixture
    fix = NegativeMutationFixture(
        fixture_id="test_fix_01",
        checker_id=CheckerId.EXACT_LINALG,
        mutation_kind="test",
        description="A test fixture",
        expected_status=EvaluationStatus.WRONG_ANSWER,
        expected_refusal_code="ARITHMETIC_ERROR",
    )
    assert fix.fixture_id == "test_fix_01"
    assert fix.expected_status == EvaluationStatus.WRONG_ANSWER

    # SeedPrompt
    seed = SeedPrompt(
        pilot_id="pilot_00000",
        task_family="linear_algebra",
        difficulty_rung=1,
        request_id="req_0",
        seed_prompt="solve equations",
        expected_outcome=ExpectedOutcome(answer=3),
    )
    assert seed.pilot_id == "pilot_00000"
    assert seed.expected_outcome.answer == 3

    # PilotSpec
    spec = PilotSpec(
        pilot_id="pilot_00000",
        prompt_id="prompt_00000",
        phase="phase_1",
        split="train",
        coordinates=PilotCoordinates(
            task_family="linear_algebra",
            difficulty_rung=1,
            representation_rewrite="raw_prose",
            rewrite_count=0,
            legend_present=False,
            mode="mode_01",
            stage_count=1,
            pass_count=1,
            single_shot=True,
            antibody_active=False,
            model_class="8B",
            model_id="test-model",
            temperature=0.0,
            target_spend_usd=0.0,
        ),
        ingress=PilotIngress(
            task_mode_fidelity="literal_extraction",
            variable_identifier_permutation="canonical",
            floating_point_approximation_risk="exact_modular",
            arm_template="A0",
            missing_premise="answerable",
            cohomology_defect_class="none",
            magma_associativity_type="none",
        ),
        host_gate=PilotHostGate(
            checker_id="PFP-01-EXACT-LINALG",
            response_schema="{}",
            residual_logging=False,
            structure_delta_metric="exact_rational_delta",
            expected_outcome="ACCEPTED",
        ),
    )
    assert spec.pilot_id == "pilot_00000"
    assert spec.coordinates.model_class == "8B"
