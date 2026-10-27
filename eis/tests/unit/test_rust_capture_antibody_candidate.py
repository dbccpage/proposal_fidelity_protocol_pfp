"""Qualify the inert Rust capture candidate, not its runtime admission.

AuthorityEffect: None. Native regression execution belongs to core_sandbox.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from eis.domain import (
    ConstraintType,
    PharmacyStatus,
    RuntimeAction,
    Severity,
)

_ROOT = Path(__file__).resolve().parents[3]
_SPEC = _ROOT / ".agents/antibodies/specs/anti_rust_capture_completion_loss.yaml"


def _spec() -> dict:
    spec = yaml.safe_load(_SPEC.read_text(encoding="utf-8"))
    assert isinstance(spec, dict)
    return spec


def test_rust_capture_candidate_retains_inert_status_and_projection() -> None:
    spec = _spec()
    assert spec["schema_version"] == "core.immune.antibody-spec.v1"
    assert spec["antibody_id"] == "ab_rust_capture_completion_loss"
    assert spec["constraint_type"] == ConstraintType.RESTRAIN.value
    assert spec["action"] == RuntimeAction.REPAIR.value
    assert spec["severity"] == Severity.P1.value
    assert spec["pharmacy_status"] == PharmacyStatus.CANDIDATE.value
    assert spec["authority_effect"] == "None"
    assert _SPEC.read_bytes() == (_ROOT / ".agents/antibodies" / _SPEC.name).read_bytes()
    for path in spec["governing_invariants"]:
        assert (_ROOT / path).is_file()


def test_rust_capture_signature_distinguishes_hostile_repair_and_benign() -> None:
    spec = _spec()
    pattern = re.compile(spec["target_pattern"])
    assert pattern.search(spec["adversarial_mutation_fixture"])
    assert not pattern.search(spec["repaired_invariant_fixture"])
    assert not pattern.search(spec["benign_control_fixture"])
    assert spec["detection_mechanisms"]["regex_triggers"] == [spec["target_pattern"]]


def test_rust_capture_candidate_binds_real_native_controls() -> None:
    spec = _spec()
    assert (_ROOT / spec["implementation_binding"]).is_file()
    source = (_ROOT / spec["native_test_binding"]).read_text(encoding="utf-8")
    for name in spec["harmful_control_tests"] + spec["benign_control_tests"]:
        assert re.search(r"(?m)^\s*fn\s+" + re.escape(name) + r"\s*\(", source), name
    control = spec["additional_failure_control"]
    source = (_ROOT / control["source"]).read_text(encoding="utf-8")
    assert re.search(r"(?m)^\s*fn\s+" + re.escape(control["test"]) + r"\s*\(", source)
