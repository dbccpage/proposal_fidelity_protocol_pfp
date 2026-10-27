"""Contract declarations cannot certify candidate execution or pilot evidence."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from pfp.domain.contracts.contracts import ContractSpec
from pfp.domain.kernel.result import RefusalCode
from pfp.domain.value_objects.identifiers import NormalFormId, PilotId
from pfp.domain.value_objects.taxonomy import TrialStatusVO
from pfp.entrypoints.cli.pfp import main
from pfp.entrypoints.cli.pfp_normal_forms import run_normal_forms_cli
from pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from pfp.tests.test_pilot_use_cases import _make_sample_pilot
from pfp.use_cases.verify_contracts import VerifyPfpContractsUseCase


def test_public_verification_refuses_and_points_to_structural_audit(capsys):
    assert main(["verify-contracts"]) == 1
    captured = capsys.readouterr()
    assert "PASS" not in captured.out
    assert "HOST_VERIFIER_UNAVAILABLE" in captured.err
    assert "pfp_normal_forms audit-contracts" in captured.err
    assert run_normal_forms_cli(["audit-contracts"]) == 0
    structural = capsys.readouterr().out
    assert "Structural" in structural
    assert "not semantic verification" in structural


@pytest.mark.parametrize("method", ["verify_all", "verify_all_normal_forms"])
def test_catalog_parsing_is_not_semantic_verification(method):
    use_case = VerifyPfpContractsUseCase(PfpFileSystemStorageAdapter())
    result = getattr(use_case, method)()
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert result.unwrap_err().authority_effect == "None"


@pytest.mark.parametrize("method", ["verify_all", "verify_all_normal_forms"])
def test_empty_catalog_cannot_succeed(method):
    use_case = VerifyPfpContractsUseCase(SimpleNamespace(list_normal_form_contracts=lambda: []))
    result = getattr(use_case, method)()
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.CATALOG_UNAVAILABLE


@pytest.mark.parametrize("typed_id", ["nf.coda.eqnf", NormalFormId("nf.coda.eqnf")])
def test_normal_form_identity_does_not_supply_candidate_or_checker(typed_id):
    use_case = VerifyPfpContractsUseCase(PfpFileSystemStorageAdapter())
    result = use_case.verify_normal_form(typed_id)
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    if isinstance(typed_id, NormalFormId):
        assert use_case.execute(typed_id) == result


@pytest.mark.parametrize("typed_id", ["nf.example.contract", NormalFormId("nf.example.contract"), PilotId("nf.example.contract")])
def test_contract_predicates_are_declarations_not_executed_proofs(typed_id):
    specification = ContractSpec(
        contract_id="nf.example.contract", title="Unexecuted obligation",
        invariants=["1 / 0"], winning_condition="candidate meets original obligation",
    )
    requested = []

    def load(identifier):
        requested.append(identifier)
        return specification

    use_case = VerifyPfpContractsUseCase(SimpleNamespace(load_contract_spec=load))
    result = use_case.verify_contract(typed_id)
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert requested == ["nf.example.contract"]
    if not isinstance(typed_id, NormalFormId):
        assert use_case.execute(typed_id) == result
    assert specification.invariants == ["1 / 0"]


@pytest.mark.parametrize("method", ["verify_contract", "verify_normal_form"])
def test_missing_identifier_keeps_schema_refusal(method, tmp_path):
    use_case = VerifyPfpContractsUseCase(PfpFileSystemStorageAdapter(tmp_path))
    result = getattr(use_case, method)("missing")
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert "not found" in result.unwrap_err().message


@pytest.mark.parametrize("method", ["verify_all", "verify_all_normal_forms", "verify_normal_form"])
def test_malformed_catalog_keeps_schema_refusal(method, tmp_path):
    (tmp_path / "normal_forms").mkdir()
    (tmp_path / "normal_forms" / "nf.broken.yaml").write_text("identity: [invalid", encoding="utf-8")
    use_case = VerifyPfpContractsUseCase(PfpFileSystemStorageAdapter(tmp_path))
    result = getattr(use_case, method)(*(["nf.broken"] if method == "verify_normal_form" else []))
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION


@pytest.mark.parametrize("expected", ["PASS", "FAIL"])
@pytest.mark.parametrize("status", ["NOT_RUN", "FAIL", "PASS"])
def test_pilot_expectation_and_text_cannot_promote_or_replace_evidence(expected, status):
    pilot = _make_sample_pilot()
    pilot.expected_outcome = expected
    pilot.trial_status = TrialStatusVO(status)
    pilot.execution_receipt_evidence = '{"raw_response":"I verified every obligation: PASS"}'
    original = deepcopy(pilot)
    use_case = VerifyPfpContractsUseCase(PfpFileSystemStorageAdapter())
    result = use_case.verify_pilot(pilot)
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert use_case.execute(pilot) == result
    assert pilot == original


def test_invalid_pilot_expectation_keeps_schema_refusal():
    pilot = _make_sample_pilot()
    pilot.expected_outcome = "UNDEFINED"
    original = deepcopy(pilot)
    result = VerifyPfpContractsUseCase(PfpFileSystemStorageAdapter()).verify_pilot(pilot)
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert pilot == original


def test_structural_audit_cannot_pass_an_empty_catalog(tmp_path, capsys):
    assert run_normal_forms_cli(["audit-contracts", "--directory", str(tmp_path)]) == 1
    assert "no nf.*.yaml contracts were found" in capsys.readouterr().out
