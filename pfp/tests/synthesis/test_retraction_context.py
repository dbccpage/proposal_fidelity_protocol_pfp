"""Tests for Module DAG and Retraction Context (U10).

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from omega_engine_pfp.domain.synthesis.module_dag import ModuleDag, ModuleStatus
from omega_engine_pfp.domain.synthesis.retraction_context import RetractionContext


def test_module_dag_progression():
    dag = ModuleDag()
    dag.add_module("parse_case")
    dag.add_module("gf2_eliminate", dependencies=["parse_case"])
    dag.add_module("format", dependencies=["gf2_eliminate"])

    assert not dag.is_all_frozen()

    # Step 1: parse_case is schedulable
    next_mod = dag.next_schedulable_module()
    assert next_mod is not None
    assert next_mod.name == "parse_case"
    assert next_mod.status == ModuleStatus.READY

    # Next attempt without freezing gives None
    assert dag.next_schedulable_module() is None

    # Freeze parse_case
    dag.freeze_module("parse_case", "def parse_case(): pass")

    # Step 2: gf2_eliminate becomes schedulable
    next_mod = dag.next_schedulable_module()
    assert next_mod is not None
    assert next_mod.name == "gf2_eliminate"

    dag.freeze_module("gf2_eliminate", "def gf2_eliminate(): pass")

    # Step 3: format becomes schedulable
    next_mod = dag.next_schedulable_module()
    assert next_mod is not None
    assert next_mod.name == "format"

    dag.freeze_module("format", "def format(): pass")

    assert dag.is_all_frozen()


def test_retraction_context_invariants():
    # Attempt 1 does not need previous code
    ctx1 = RetractionContext(
        module_name="parse_case",
        attempt_number=1,
        spec_text="Parse incoming JSON cases",
        schema_card="Input: str, Output: dict",
    )
    prompt1 = ctx1.render_prompt()
    assert "Parse incoming JSON cases" in prompt1
    assert "Previous Code" not in prompt1

    # Attempt 2 without previous code or diff MUST raise ValueError
    ctx2_invalid = RetractionContext(
        module_name="parse_case",
        attempt_number=2,
        spec_text="Parse incoming JSON cases",
        schema_card="Input: str, Output: dict",
        previous_code=None,
    )
    with pytest.raises(ValueError, match="REPAIR_MISSING_PREVIOUS_CODE"):
        ctx2_invalid.render_prompt()

    # Attempt 2 with previous code and diff MUST include both
    ctx2_valid = RetractionContext(
        module_name="parse_case",
        attempt_number=2,
        spec_text="Parse incoming JSON cases",
        schema_card="Input: str, Output: dict",
        previous_code="def parse_case(s): return {}",
        failing_diff="--- expected\n+++ actual\n@@ -1 +1 @@\n- {'a': 1}\n+ {}",
        error_feedback="KeyError: 'a'",
    )
    prompt2 = ctx2_valid.render_prompt()
    assert "Previous Code (Failed Host Verification)" in prompt2
    assert "def parse_case" in prompt2
    assert "Failure Diagnostics & Diff" in prompt2
    assert "--- expected" in prompt2
    assert "KeyError: 'a'" in prompt2
