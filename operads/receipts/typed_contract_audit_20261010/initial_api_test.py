"""Actual finite predicates and source bindings; no anti-skill activation."""

from dataclasses import replace
from pathlib import Path

from operations.domain.rop.result import Ok
from workflows_agents_skills.application.typed_contract_audit import (
    audit_typed_contracts,
)
from workflows_agents_skills.domain.anti_skills import AntiSkillSubjectV1
from workflows_agents_skills.infrastructure.typed_contract_compiler import (
    compile_typed_contracts,
)

ROOT = Path(__file__).resolve().parents[3]


def _subject() -> AntiSkillSubjectV1:
    return AntiSkillSubjectV1(
        claim_scope=("code", "paper"),
        evidence_scope=("code", "paper"),
        producer_identity="fixture.producer",
        verifier_identity="fixture.verifier",
        claim_mode="PROPOSAL",
        requested_effect="NONE",
    )


def test_finite_audit_runs_real_predicate_and_never_self_admits() -> None:
    package = compile_typed_contracts(ROOT)
    subject = _subject()
    clean = audit_typed_contracts(subject, compile_current=lambda: compile_typed_contracts(ROOT))
    assert isinstance(clean, Ok), clean
    receipt = clean.value
    assert receipt.contracts_digest == package.contracts_digest
    assert receipt.subject_id == subject.subject_id
    assert receipt.evaluation_receipt.outcome == "COMPUTED_PASS"
    assert receipt.hits == ()
    assert receipt.disposition == "CLEAN"
    assert receipt.admission == "Unadmitted"
    assert receipt.runtime_activation == "HOLD"
    assert receipt.authority_effect == "None"

    hostile = replace(subject, evidence_scope=("code",), subject_id="")
    found = audit_typed_contracts(hostile, compile_current=lambda: compile_typed_contracts(ROOT))
    assert isinstance(found, Ok), found
    assert found.value.subject_id == hostile.subject_id
    assert found.value.disposition == "FINDING"
    assert len(found.value.hits) == 1
    assert found.value.hits[0].subject_id == hostile.subject_id
    assert found.value.hits[0].spec_id == package.anti_spec.spec_id
    assert found.value.receipt_id != receipt.receipt_id
    assert found.value.admission == "Unadmitted"
    assert found.value.runtime_activation == "HOLD"
