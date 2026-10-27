"""Real finite replay and detached instruction signatures; no live activation."""

import hashlib
import json
import shutil
import subprocess
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from operations.domain.rop.result import Err, Ok
from workflows_agents_skills.application.typed_contract_audit import (
    TypedContractAuditReceiptV1,
    audit_typed_contracts,
)
from workflows_agents_skills.application.adversary_candidate_plan import (
    PlanNodeV01,
    compile_candidate_plan,
)
from workflows_agents_skills.application.adversary_instruction_admission import (
    source_snapshot_digest,
)
from workflows_agents_skills.application.adversary_task_selection import (
    AdversaryCandidateRouteV01,
    AdversaryTaskShapeV01,
    select_candidate_plan,
)
from workflows_agents_skills.domain.anti_skills import AntiSkillSubjectV1
from workflows_agents_skills.infrastructure.typed_contract_compiler import (
    compile_typed_contracts,
)

ROOT = next(
    path
    for path in Path(__file__).resolve().parents
    if (path / ".git").exists() and (path / "workflows_agents_skills").is_dir()
)
CONTRACTS = Path("workflows_agents_skills/catalog/contracts/v1")
EFFECTS = frozenset({"read_subject", "emit_finding"})


def _subject() -> AntiSkillSubjectV1:
    return AntiSkillSubjectV1(
        claim_scope=("code", "paper"),
        evidence_scope=("code", "paper"),
        producer_identity="fixture.producer",
        verifier_identity="fixture.verifier",
        claim_mode="PROPOSAL",
        requested_effect="NONE",
    )


def _canonical(value) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def _clone(tmp_path: Path) -> Path:
    clone = tmp_path / "repo"
    shutil.copytree(ROOT / CONTRACTS, clone / CONTRACTS)
    return clone


def _change_instruction(clone: Path, *, repin: bool) -> None:
    record_path = clone / CONTRACTS / "adversary_claim_audit.json"
    record = json.loads(record_path.read_bytes())
    body_path = clone / record["instruction"]["path"]
    changed = body_path.read_bytes() + b"\nRetain the changed finite source binding.\n"
    body_path.write_bytes(changed)
    if repin:
        record["instruction"]["byte_length"] = len(changed)
        record["instruction"]["sha256"] = hashlib.sha256(changed).hexdigest()
        record_path.write_bytes(_canonical(record))


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


def test_audit_recompiles_current_source_on_every_call(tmp_path: Path) -> None:
    clone = _clone(tmp_path)
    calls = []

    def fresh():
        calls.append(True)
        return compile_typed_contracts(clone)

    first = audit_typed_contracts(_subject(), compile_current=fresh)
    assert isinstance(first, Ok), first
    _change_instruction(clone, repin=False)
    refused = audit_typed_contracts(_subject(), compile_current=fresh)
    assert isinstance(refused, Err), refused
    assert refused.error.code == "TYPED_CONTRACT_SOURCE_REFUSED"
    assert len(calls) == 2


def test_rebound_source_refuses_a_replayed_expected_digest(tmp_path: Path) -> None:
    clone = _clone(tmp_path)
    before = compile_typed_contracts(clone)
    _change_instruction(clone, repin=True)
    after = compile_typed_contracts(clone)
    assert after.contracts_digest != before.contracts_digest
    refused = audit_typed_contracts(
        _subject(),
        compile_current=lambda: compile_typed_contracts(clone),
        expected_contracts_digest=before.contracts_digest,
    )
    assert isinstance(refused, Err), refused
    assert refused.error.code == "TYPED_CONTRACT_BINDING_MISMATCH"
    recovered = audit_typed_contracts(
        _subject(),
        compile_current=lambda: compile_typed_contracts(clone),
        expected_contracts_digest=after.contracts_digest,
    )
    assert isinstance(recovered, Ok), recovered
    assert recovered.value.contracts_digest == after.contracts_digest


def test_audit_replays_controls_instead_of_trusting_prior_compile() -> None:
    package = compile_typed_contracts(ROOT)
    for expected_hit in (False, True):
        case = next(
            case for case in package.fixture_bank.cases if case.expected_hit == expected_hit
        )
        changed_subject = replace(
            case.subject,
            evidence_scope=case.subject.claim_scope if expected_hit else (),
            subject_id="",
        )
        changed_case = replace(case, subject=changed_subject, case_digest="")
        bank = replace(
            package.fixture_bank,
            cases=tuple(
                changed_case if item.case_id == case.case_id else item
                for item in package.fixture_bank.cases
            ),
            bank_id="",
        )
        changed_package = replace(package, fixture_bank=bank)
        refused = audit_typed_contracts(_subject(), compile_current=lambda: changed_package)
        assert isinstance(refused, Err), refused
        assert refused.error.code == "TYPED_CONTRACT_CONTROLS_FAILED"


def test_stale_predicate_implementation_is_refused() -> None:
    package = compile_typed_contracts(ROOT)
    stale_spec = replace(
        package.anti_spec, implementation_digest="sha256:" + "0" * 64, spec_digest=""
    )
    refused = audit_typed_contracts(
        _subject(), compile_current=lambda: replace(package, anti_spec=stale_spec)
    )
    assert isinstance(refused, Err), refused
    assert refused.error.code == "ANTISKILL_EVALUATION_REFUSED"
    assert "implementation bytes" in refused.error.message


def test_malformed_subjects_are_typed_refusals_before_compilation() -> None:
    def forbidden_compile():
        pytest.fail("malformed subject reached the compiler")

    for malformed in (None, {}, b"{}", "subject", True):
        result = audit_typed_contracts(malformed, compile_current=forbidden_compile)
        assert isinstance(result, Err), result
        assert result.error.code == "TYPED_CONTRACT_SUBJECT_REFUSED"
    altered = _subject()
    object.__setattr__(altered, "subject_id", "sha256:" + "f" * 64)
    result = audit_typed_contracts(altered, compile_current=forbidden_compile)
    assert isinstance(result, Err), result
    assert result.error.code == "TYPED_CONTRACT_SUBJECT_REFUSED"


def test_malformed_packages_and_compile_failure_are_typed_refusals() -> None:
    package = compile_typed_contracts(ROOT)
    for malformed in (None, {}, replace(package, contracts_digest="not-a-digest")):
        result = audit_typed_contracts(_subject(), compile_current=lambda: malformed)
        assert isinstance(result, Err), result
        assert result.error.code == "TYPED_CONTRACT_PACKAGE_REFUSED"

    def unavailable():
        raise OSError("fixture source unavailable")

    refused = audit_typed_contracts(_subject(), compile_current=unavailable)
    assert isinstance(refused, Err), refused
    assert refused.error.code == "TYPED_CONTRACT_SOURCE_REFUSED"


def test_receipt_wire_schema_digest_and_nonpromotion_are_bound() -> None:
    result = audit_typed_contracts(
        _subject(), compile_current=lambda: compile_typed_contracts(ROOT)
    )
    assert isinstance(result, Ok), result
    receipt = result.value
    wire = receipt.to_dict()
    assert set(wire) == set(asdict(receipt))
    assert TypeAdapter(TypedContractAuditReceiptV1).validate_json(_canonical(wire)) == receipt
    payload = dict(wire)
    payload.pop("receipt_id")
    envelope = {"domain": "oewas.typed_contract.audit_receipt.v1", "payload": payload}
    oracle = json.dumps(
        envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    assert receipt.receipt_id == "sha256:" + hashlib.sha256(oracle).hexdigest()
    for changed in (
        {"admission": "Admitted"},
        {"runtime_activation": "ACTIVE"},
        {"authority_effect": "StateTransition"},
        {"receipt_id": "sha256:" + "0" * 64},
    ):
        with pytest.raises(ValueError):
            replace(receipt, **changed)
    second = audit_typed_contracts(
        replace(_subject(), producer_identity="another.producer", subject_id=""),
        compile_current=lambda: compile_typed_contracts(ROOT),
    )
    assert isinstance(second, Ok), second
    assert second.value.contracts_digest == receipt.contracts_digest
    assert second.value.subject_id != receipt.subject_id
    assert second.value.receipt_id != receipt.receipt_id


def test_single_detector_receipt_rejects_multiple_hits() -> None:
    hostile = replace(_subject(), evidence_scope=("code",), subject_id="")
    result = audit_typed_contracts(hostile, compile_current=lambda: compile_typed_contracts(ROOT))
    assert isinstance(result, Ok), result
    receipt = result.value
    assert len(receipt.hits) == 1
    assert (
        TypeAdapter(TypedContractAuditReceiptV1).validate_json(_canonical(receipt.to_dict()))
        == receipt
    )
    with pytest.raises(ValueError):
        replace(receipt, hits=receipt.hits * 2, receipt_id="")
    wire = receipt.to_dict()
    wire["hits"] *= 2
    wire["receipt_id"] = ""
    with pytest.raises(ValueError):
        TypeAdapter(TypedContractAuditReceiptV1).validate_json(_canonical(wire))


def _signed_fixture(tmp_path: Path):
    ssh = shutil.which("ssh-keygen")
    assert ssh is not None, "The required real OpenSSH signature control is unavailable"
    clone = _clone(tmp_path)
    subject = _subject()
    package = compile_typed_contracts(clone)
    root = PlanNodeV01("adversary-claim-audit", ((0, PlanNodeV01("adversary-scope-falsifier")),))
    plan = compile_candidate_plan(package.documents, root, allowed_effects=EFFECTS)
    task = AdversaryTaskShapeV01(
        subject.subject_id,
        "fixture-profile",
        "sha256:" + "a" * 64,
        "fixture-domain",
        plan.inputs,
        plan.output,
        required_operation_ids=frozenset({"adversary-claim-audit", "adversary-scope-falsifier"}),
        allowed_effects=EFFECTS,
    )
    route = AdversaryCandidateRouteV01(
        "route.typed-contract-audit",
        task.workload_profile_id,
        task.workload_profile_digest,
        task.domain_id,
        package.documents,
        root,
    )
    selected = select_candidate_plan(task, (route,))
    manifest = {
        "schema_version": "oewas.adversary.instruction_admission.v0.1",
        "decision": "APPROVE",
        "reviewer_identity": "human.fixture",
        "authority_effect": "None",
        "request_digest": subject.subject_id,
        "task_shape_digest": selected.task_shape_digest,
        "workload_profile_id": task.workload_profile_id,
        "workload_profile_digest": task.workload_profile_digest,
        "domain_id": task.domain_id,
        "selection_digest": selected.selection_digest,
        "route_id": selected.route_id,
        "plan_digest": selected.plan.plan_digest,
        "source_snapshot_digest": source_snapshot_digest(selected),
    }
    manifest_bytes = _canonical(manifest)
    manifest_path = tmp_path / "instruction.json"
    manifest_path.write_bytes(manifest_bytes)
    key_path = tmp_path / "fixture_signer"
    subprocess.run(
        [ssh, "-q", "-t", "ed25519", "-N", "", "-f", str(key_path)],
        check=True,
        capture_output=True,
        timeout=10,
    )
    subprocess.run(
        [
            ssh,
            "-Y",
            "sign",
            "-f",
            str(key_path),
            "-n",
            "oewas-adversary-instruction-v0.1",
            str(manifest_path),
        ],
        check=True,
        capture_output=True,
        timeout=10,
    )
    trust_root = tmp_path / "allowed_signers"
    trust_root.write_text(
        "human.fixture " + key_path.with_suffix(".pub").read_text(encoding="ascii"),
        encoding="ascii",
    )
    assert not trust_root.is_relative_to(clone)
    arguments = dict(
        compile_current=lambda: compile_typed_contracts(clone),
        task=task,
        manifest_bytes=manifest_bytes,
        signature_path=tmp_path / "instruction.json.sig",
        allowed_signers_path=trust_root,
        ssh_keygen=ssh,
    )
    return subject, package, selected, clone, arguments


def test_external_signature_admits_only_exact_fresh_instruction_evidence(tmp_path: Path) -> None:
    from workflows_agents_skills.application.typed_contract_audit import (
        verify_typed_contract_admission,
    )

    subject, package, selected, _clone_root, arguments = _signed_fixture(tmp_path)
    verified = verify_typed_contract_admission(subject, **arguments)
    assert isinstance(verified, Ok), verified
    result = verified.value
    assert result.admission_scope == "SIGNED_INSTRUCTION_ONLY"
    assert result.audit.subject_id == subject.subject_id
    assert result.audit.contracts_digest == package.contracts_digest
    assert result.audit.admission == "Unadmitted"
    assert result.audit.runtime_activation == "HOLD"
    assert result.instruction_admission.request_digest == subject.subject_id
    assert result.instruction_admission.plan_digest == selected.plan.plan_digest
    assert (
        result.instruction_admission.ordered_operand_bodies == selected.plan.ordered_operand_bodies
    )
    assert result.instruction_admission.operation_ids == (
        "adversary-scope-falsifier",
        "adversary-claim-audit",
    )
    assert selected.admission == selected.plan.admission == "Unadmitted"
    assert package.anti_spec.status == "PROPOSED"
    assert package.anti_spec.runtime_enforcement is False
    for binding in (
        package.contracts_digest,
        package.anti_spec.spec_digest,
        package.fixture_bank.bank_id,
        result.audit.evaluation_receipt.receipt_id,
        result.audit.implementation_digest,
    ):
        assert all(binding in body for body in result.instruction_admission.ordered_operand_bodies)
    assert result.to_dict()["admission_scope"] == "SIGNED_INSTRUCTION_ONLY"


def test_signed_instruction_refuses_subject_transplant_and_actual_finding(tmp_path: Path) -> None:
    from workflows_agents_skills.application.typed_contract_audit import (
        verify_typed_contract_admission,
    )

    subject, _package, _selected, _clone_root, arguments = _signed_fixture(tmp_path)
    other = replace(subject, producer_identity="another.producer", subject_id="")
    transplanted = verify_typed_contract_admission(other, **arguments)
    assert isinstance(transplanted, Err), transplanted
    assert transplanted.error.code == "TYPED_CONTRACT_TASK_BINDING_MISMATCH"
    adjusted = {**arguments, "task": replace(arguments["task"], request_digest=other.subject_id)}
    refused_manifest = verify_typed_contract_admission(other, **adjusted)
    assert isinstance(refused_manifest, Err), refused_manifest
    assert refused_manifest.error.code == "REQUEST_MISMATCH"
    hostile = replace(subject, evidence_scope=("code",), subject_id="")
    refused_hit = verify_typed_contract_admission(hostile, **arguments)
    assert isinstance(refused_hit, Err), refused_hit
    assert refused_hit.error.code == "TYPED_CONTRACT_SUBJECT_FALSIFIED"


def test_old_signature_refuses_rebound_source_and_fixture_changes(tmp_path: Path) -> None:
    from workflows_agents_skills.application.typed_contract_audit import (
        verify_typed_contract_admission,
    )

    subject, package, _selected, clone, arguments = _signed_fixture(tmp_path)
    original_record = (clone / CONTRACTS / "adversary_claim_audit.json").read_bytes()
    original_body_path = clone / json.loads(original_record)["instruction"]["path"]
    original_body = original_body_path.read_bytes()
    _change_instruction(clone, repin=True)
    changed = compile_typed_contracts(clone)
    assert changed.contracts_digest != package.contracts_digest
    refused = verify_typed_contract_admission(subject, **arguments)
    assert isinstance(refused, Err), refused
    assert refused.error.code == "PLAN_OR_SCOPE_MISMATCH"

    # Restore the first change: the fixture-only control must be independent.
    (clone / CONTRACTS / "adversary_claim_audit.json").write_bytes(original_record)
    original_body_path.write_bytes(original_body)
    restored = verify_typed_contract_admission(subject, **arguments)
    assert isinstance(restored, Ok), restored

    anti_path = clone / CONTRACTS / "adversary_scope_falsifier.json"
    anti = json.loads(anti_path.read_bytes())
    bank_path = clone / anti["fixtures"]["path"]
    bank = package.fixture_bank
    cases = tuple(
        replace(case, context_key=case.context_key + ".rebound", case_digest="")
        for case in bank.cases
    )
    rebound = replace(bank, cases=cases, bank_id="")
    raw = _canonical(rebound.to_dict()).rstrip(b"\n")
    bank_path.write_bytes(raw)
    anti["fixtures"]["sha256"] = hashlib.sha256(raw).hexdigest()
    anti["fixtures"]["byte_length"] = len(raw)
    anti_path.write_bytes(_canonical(anti))
    # Changed but passing controls still require a new external signature.
    fresh = compile_typed_contracts(clone)
    assert fresh.fixture_bank.bank_id != bank.bank_id
    refused_controls = verify_typed_contract_admission(subject, **arguments)
    assert isinstance(refused_controls, Err), refused_controls
    assert refused_controls.error.code == "PLAN_OR_SCOPE_MISMATCH"


def test_missing_and_tampered_signature_evidence_refuses(tmp_path: Path) -> None:
    from workflows_agents_skills.application.typed_contract_audit import (
        verify_typed_contract_admission,
    )

    subject, _package, _selected, _clone_root, arguments = _signed_fixture(tmp_path)
    absent = verify_typed_contract_admission(
        subject,
        **{**arguments, "signature_path": tmp_path / "absent.sig"},
    )
    assert isinstance(absent, Err), absent
    assert absent.error.code == "SIGNATURE_OR_TRUST_ROOT_MISSING"
    manifest = json.loads(arguments["manifest_bytes"])
    manifest["reviewer_identity"] = "forged.reviewer"
    forged = verify_typed_contract_admission(
        subject, **{**arguments, "manifest_bytes": _canonical(manifest)}
    )
    assert isinstance(forged, Err), forged
    assert forged.error.code == "SIGNATURE_INVALID"
    malformed = verify_typed_contract_admission(subject, **{**arguments, "manifest_bytes": b"{}"})
    assert isinstance(malformed, Err), malformed
    assert malformed.error.code == "MANIFEST_NONCANONICAL"
