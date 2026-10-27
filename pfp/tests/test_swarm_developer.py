"""Unit tests for the SPOE Swarm Developer CLI and contract engine.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from operations.domain.rop.result import Err, Ok
from pfp.entrypoints.cli import swarm_developer


def test_verify_governance_skill(tmp_path: Path) -> None:
    # 1. Missing governance skill
    res_missing = swarm_developer.verify_governance_skill(tmp_path)
    assert isinstance(res_missing, Err)
    assert res_missing.error.code == "SWARM_GOVERNANCE_MISSING"

    # 2. Existing governance skill
    gov_dir = tmp_path / "operads" / "skills" / "governance-pfp"
    gov_dir.mkdir(parents=True)
    gov_file = gov_dir / "SKILL.md"
    gov_file.write_text("# Governance Symbol Game\nAuthorityEffect: None.\n", encoding="utf-8")

    res_ok = swarm_developer.verify_governance_skill(tmp_path)
    assert isinstance(res_ok, Ok)
    assert len(res_ok.value) == 64


def test_load_task_contract_validation(tmp_path: Path) -> None:
    # 1. Non-existent file
    res_not_found = swarm_developer.load_task_contract(tmp_path / "nonexistent.json")
    assert isinstance(res_not_found, Err)
    assert res_not_found.error.code == "CONTRACT_NOT_FOUND"

    # 2. Unsupported contract version
    bad_contract = tmp_path / "bad_contract.json"
    bad_contract.write_text(json.dumps({"contract_version": "UnknownV99"}), encoding="utf-8")
    res_bad = swarm_developer.load_task_contract(bad_contract)
    assert isinstance(res_bad, Err)
    assert res_bad.error.code == "UNSUPPORTED_CONTRACT_VERSION"

    # 3. Valid SwarmTaskContractV1
    valid_contract = tmp_path / "valid_contract.json"
    valid_contract.write_text(
        json.dumps(
            {
                "contract_version": "SwarmTaskContractV1",
                "contract_id": "TEST-CONTRACT-001",
                "task_objective": "Test contract objective",
                "allowed_paths": ["tests/"],
                "protected_paths": [".agents/rules/"],
                "verifier_routes": [],
            }
        ),
        encoding="utf-8",
    )
    res_valid = swarm_developer.load_task_contract(valid_contract)
    assert isinstance(res_valid, Ok)
    assert res_valid.value["contract_id"] == "TEST-CONTRACT-001"


def test_claim_hygiene_auditor() -> None:
    text_clean = "This model supports the discrete finite boundary in this setting."
    assert swarm_developer.audit_candidate_claim_hygiene(text_clean) == []

    text_hype = "This algorithm proves universal convergence and guarantees flawless execution, simply and merely impossible."
    violations = swarm_developer.audit_candidate_claim_hygiene(text_hype)
    assert "proves" in violations
    assert "universal" in violations
    assert "guarantees" in violations
    assert "flawless" in violations
    assert "simply" in violations
    assert "merely" in violations
    assert "impossible" in violations


def test_cli_validate_contract(tmp_path: Path) -> None:
    valid_contract = tmp_path / "valid_contract.json"
    valid_contract.write_text(
        json.dumps(
            {
                "contract_version": "SwarmTaskContractV1",
                "contract_id": "TEST-CONTRACT-002",
                "task_objective": "Audit test",
                "allowed_paths": [],
                "protected_paths": [],
                "verifier_routes": [],
            }
        ),
        encoding="utf-8",
    )
    exit_code = swarm_developer.main(["validate-contract", "--contract", str(valid_contract)])
    assert exit_code == 0


def test_cli_run_swarm_minimal(tmp_path: Path) -> None:
    # Contract with empty routes and skip-harvest to run purely in memory
    contract_file = tmp_path / "minimal_contract.json"
    contract_file.write_text(
        json.dumps(
            {
                "contract_version": "SwarmTaskContractV1",
                "contract_id": "TEST-CONTRACT-MINIMAL",
                "task_objective": "Execute minimal swarm turn",
                "allowed_paths": [],
                "protected_paths": [],
                "verifier_routes": [],
                "audit_profile": "software",
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "swarm_run_output"

    exit_code = swarm_developer.main(
        [
            "run-swarm",
            "--contract",
            str(contract_file),
            "--output-dir",
            str(out_dir),
            "--skip-harvest",
        ]
    )
    assert exit_code == 0
    assert (out_dir / "evidence_envelope.json").is_file()
    assert (out_dir / "receipt.json").is_file()
    assert (out_dir / "novella.md").is_file()
    assert (out_dir / "dda_actions.jsonl").is_file()
    assert (out_dir / "summary.json").is_file()

    envelope = json.loads((out_dir / "evidence_envelope.json").read_text(encoding="utf-8"))
    assert envelope["contract_id"] == "TEST-CONTRACT-MINIMAL"
    assert envelope["governance_terminal"] == "Verified"
    assert "supports" in envelope["claim_hygiene"]
    assert "does_not_support" in envelope["claim_hygiene"]
    assert "narrowest_defensible_claim" in envelope["claim_hygiene"]
    assert "next_test_needed" in envelope["claim_hygiene"]


def test_run_verifier_routes_timeout(monkeypatch, tmp_path: Path) -> None:
    import subprocess

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=120)

    monkeypatch.setattr(subprocess, "run", fake_run)
    receipts, passed = swarm_developer.run_verifier_routes(["pytest fake_test.py"], tmp_path)
    assert not passed
    assert len(receipts) == 1
    assert receipts[0]["passed"] is False
    assert "Timeout expired after 120s" in receipts[0]["error"]


def test_audit_clean_architecture_boundaries(tmp_path: Path) -> None:
    # 1. Non-domain path is ignored
    non_domain = tmp_path / "use_cases" / "service.py"
    non_domain.parent.mkdir(parents=True)
    non_domain.write_text("import engine.use_cases\n", encoding="utf-8")
    assert swarm_developer.audit_clean_architecture_boundaries(non_domain) == []

    # 2. Domain path with outer layer import is flagged
    domain_bad = tmp_path / "domain" / "entity.py"
    domain_bad.parent.mkdir(parents=True)
    domain_bad.write_text("from operations.use_cases import run\n", encoding="utf-8")
    violations = swarm_developer.audit_clean_architecture_boundaries(domain_bad)
    assert len(violations) == 1
    assert "use_cases" in violations[0]

    # 3. Domain path with port mentioning frontend in identifier is NOT falsely flagged
    domain_ok = tmp_path / "domain" / "ports.py"
    domain_ok.write_text("from .ports import ui_frontend_port\n", encoding="utf-8")
    assert swarm_developer.audit_clean_architecture_boundaries(domain_ok) == []


def test_cli_validate_contract_digest_mismatch(tmp_path: Path, monkeypatch) -> None:
    contract_file = tmp_path / "mismatch_contract.json"
    contract_file.write_text(
        json.dumps(
            {
                "contract_version": "SwarmTaskContractV1",
                "contract_id": "TEST-MISMATCH",
                "task_objective": "Test mismatch",
                "governance_precondition": {"sha256": "0" * 64},
                "allowed_paths": [],
                "protected_paths": [],
                "verifier_routes": [],
            }
        ),
        encoding="utf-8",
    )
    # Ensure governance skill exists in tmp_path
    gov_dir = tmp_path / "operads" / "skills" / "governance-pfp"
    gov_dir.mkdir(parents=True)
    (gov_dir / "SKILL.md").write_text("# Test\n", encoding="utf-8")
    monkeypatch.setattr(swarm_developer, "resolve_repo_root", lambda: tmp_path)

    exit_code = swarm_developer.main(["validate-contract", "--contract", str(contract_file)])
    assert exit_code == 2


def test_cli_fireproof_audit(tmp_path: Path, monkeypatch) -> None:
    test_target = tmp_path / "clean_module.py"
    test_target.write_text("def solve(): return 42\n", encoding="utf-8")
    monkeypatch.setattr(swarm_developer, "resolve_repo_root", lambda: tmp_path)

    report_file = tmp_path / "audit_report.jsonl"
    exit_code = swarm_developer.main(
        [
            "fireproof-audit",
            "--target",
            str(test_target),
            "--profile",
            "software",
            "--report-out",
            str(report_file),
        ]
    )
    assert exit_code == 0
    assert report_file.is_file()


def test_run_verifier_routes_check_discipline(monkeypatch, tmp_path: Path) -> None:
    import subprocess

    called_kwargs: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        called_kwargs.update(kwargs)

        class _Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        return _Completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    receipts, passed = swarm_developer.run_verifier_routes(["pytest fake_test.py"], tmp_path)
    assert passed is True
    assert receipts[0]["passed"] is True
    assert called_kwargs.get("check") is False


def test_resolve_repo_root_prefers_linked_worktree(monkeypatch, tmp_path: Path) -> None:
    work = tmp_path / "linked"
    work.mkdir()
    (work / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")
    other = tmp_path / "main-checkout"
    other.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setattr(
        swarm_developer,
        "try_resolve_intelligence_repo_root",
        lambda _cwd: Ok(other),
    )
    assert swarm_developer.resolve_repo_root() == work.resolve()


def test_resolve_repo_root_refuses_without_git_checkout(monkeypatch) -> None:
    outside = Path(tempfile.mkdtemp(prefix="swarm-no-git-"))
    loose = outside / "loose" / "swarm_developer.py"
    monkeypatch.chdir(outside)
    monkeypatch.setattr(swarm_developer, "__file__", str(loose))
    try:
        with pytest.raises(swarm_developer.CodeCheckoutUnresolved):
            swarm_developer.resolve_repo_root()
    finally:
        shutil.rmtree(outside, ignore_errors=True)


def test_auto_repair_triggers_autop_and_writes_receipt(tmp_path: Path, monkeypatch) -> None:
    # 1. Setup mock repo root in tmp_path with governance skill
    gov_dir = tmp_path / "operads" / "skills" / "governance-pfp"
    gov_dir.mkdir(parents=True)
    (gov_dir / "SKILL.md").write_text("# Governance\nAuthorityEffect: None.\n", encoding="utf-8")

    # 2. Setup a candidate path with a blocking claim hygiene word under paper_release profile
    candidate_file = tmp_path / "candidate.md"
    candidate_file.write_text("This proves universal completeness without bounds.\n", encoding="utf-8")

    # 3. Valid SwarmTaskContractV1 with a failing verifier route and candidate path
    contract_file = tmp_path / "failing_contract.json"
    contract_data = {
        "contract_version": "SwarmTaskContractV1",
        "contract_id": "REPAIR-TEST-001",
        "task_objective": "Test auto-repair AutoP trigger",
        "allowed_paths": [candidate_file.name],
        "target_paths": [candidate_file.name],
        "protected_paths": [".agents/rules/"],
        "verifier_routes": ["pytest non_existent_failing_route.py"],
        "audit_profile": "paper_release",
    }
    contract_file.write_text(json.dumps(contract_data, indent=2), encoding="utf-8")

    monkeypatch.setattr(swarm_developer, "resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        swarm_developer,
        "try_resolve_intelligence_repo_root",
        lambda _cwd: Ok(tmp_path),
    )

    out_receipt = tmp_path / "runs" / "autop_receipt.json"

    # Run with --auto-repair
    exit_code = swarm_developer.main(
        [
            "run-swarm",
            "--contract",
            str(contract_file),
            "--auto-repair",
            "--max-rounds",
            "1",
            "--skip-harvest",
            "--autop-output",
            str(out_receipt),
        ]
    )

    # Round failed, so exit_code should be 2 (Refused)
    assert exit_code == 2

    # Verify that AutoP was triggered and out_receipt exists
    assert out_receipt.is_file(), "runs/autop_receipt.json must be written by AutoP"
    autop_data = json.loads(out_receipt.read_text(encoding="utf-8"))
    assert autop_data["authority_effect"] == "None"
    assert "stages" in autop_data
    stage_0 = autop_data["stages"][0]
    assert stage_0["stage_name"] == "process_intake_receipt"
    assert stage_0["status"] == "PASS"
    assert stage_0["details"]["item_count"] == 1
    assert stage_0["details"]["extracted_error_count"] >= 1
    assert "ADVERSARY-REPAIR-REPAIR-TEST-001-R1" in stage_0["details"]["paper_ids"]

    # Verify that evidence_envelope recorded autop_receipts
    envelope_file = (
        tmp_path
        / "_ic"
        / "nara"
        / "legacy"
        / "swarm"
        / "run_REPAIR-TEST-001"
        / "evidence_envelope.json"
    )
    assert envelope_file.is_file()
    env_data = json.loads(envelope_file.read_text(encoding="utf-8"))
    assert "autop_receipts" in env_data["evidence"]
    assert len(env_data["evidence"]["autop_receipts"]) == 1
    assert env_data["evidence"]["autop_receipts"][0]["autop_id"] == autop_data["autop_id"]


def test_failing_round_without_auto_repair_does_not_trigger_autop(tmp_path: Path, monkeypatch) -> None:
    gov_dir = tmp_path / "operads" / "skills" / "governance-pfp"
    gov_dir.mkdir(parents=True)
    (gov_dir / "SKILL.md").write_text("# Governance\nAuthorityEffect: None.\n", encoding="utf-8")

    contract_file = tmp_path / "failing_contract.json"
    contract_data = {
        "contract_version": "SwarmTaskContractV1",
        "contract_id": "NO-REPAIR-TEST-001",
        "task_objective": "Test without auto-repair",
        "allowed_paths": [],
        "target_paths": [],
        "protected_paths": [],
        "verifier_routes": ["pytest non_existent_failing_route.py"],
    }
    contract_file.write_text(json.dumps(contract_data, indent=2), encoding="utf-8")

    monkeypatch.setattr(swarm_developer, "resolve_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        swarm_developer,
        "try_resolve_intelligence_repo_root",
        lambda _cwd: Ok(tmp_path),
    )

    out_receipt = tmp_path / "runs" / "autop_receipt.json"

    exit_code = swarm_developer.main(
        [
            "run-swarm",
            "--contract",
            str(contract_file),
            "--max-rounds",
            "1",
            "--skip-harvest",
            "--autop-output",
            str(out_receipt),
        ]
    )
    assert exit_code == 2
    assert not out_receipt.exists(), "AutoP receipt should not be written when --auto-repair is not set"


