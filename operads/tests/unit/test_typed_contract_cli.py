"""Actual compiler CLI and pinned-resource controls; no provider or dispatch calls."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from pathlib import Path

import pytest

from omega_engine_operations.use_cases.packaging.sync_cross_host_skills import HOST_SKILL_ROOTS
from omega_engine_operads.contracts.typed_capabilities_v1 import (
    ROOT as CONTRACT_ROOT,
)
from omega_engine_operads.contracts.typed_capabilities_v1 import (
    canonical_bytes,
    contract_json_schema,
)
from omega_engine_operads.domain.anti_skills.anti_skill_v2 import (
    AntiSkillFixtureBankV1,
    AntiSkillSubjectV1,
    canonical_json_bytes,
)
from omega_engine_operads.infrastructure.typed_contract_compiler import (
    compile_typed_contracts,
    main,
)

REPO = next(
    path for path in Path(__file__).resolve().parents if (path / "pyproject.toml").is_file()
)


@pytest.fixture
def estate(tmp_path: Path) -> Path:
    shutil.copytree(REPO / CONTRACT_ROOT, tmp_path / CONTRACT_ROOT,
                    ignore=shutil.ignore_patterns("lessons"))
    for host in HOST_SKILL_ROOTS:
        (tmp_path / host).mkdir(parents=True)
    return tmp_path


def _main(root: Path, *mode: str) -> tuple[int, bytes, str]:
    buffer = io.BytesIO()
    stdout = io.TextIOWrapper(buffer, encoding="utf-8", write_through=True)
    stderr = io.StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(["--repo-root", str(root), *mode])
        stdout.flush()
        return code, buffer.getvalue(), stderr.getvalue()
    finally:
        stdout.detach()


def _snapshot(root: Path) -> dict[str, bytes | None]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def _resource(root: Path, filename: str, key: str, raw: bytes) -> Path:
    source = root / CONTRACT_ROOT / filename
    value = json.loads(source.read_bytes())
    destination = root / value[key]["path"]
    destination.write_bytes(raw)
    value[key].update(sha256=hashlib.sha256(raw).hexdigest(), byte_length=len(raw))
    source.write_bytes(canonical_bytes(value))
    return destination


def _subject(*, overclaim: bool = False) -> AntiSkillSubjectV1:
    return AntiSkillSubjectV1(
        claim_scope=("finite", "general") if overclaim else ("finite",),
        evidence_scope=("finite",),
        producer_identity="cli.producer",
        verifier_identity="cli.verifier",
        claim_mode="BOUNDED",
        requested_effect="FINDING",
    )


def _assert_refused(result: tuple[int, bytes, str], code: str) -> None:
    exit_code, stdout, stderr = result
    assert exit_code == 1
    assert stdout == b""
    assert code in stderr
    assert "TYPED_PACKAGES_OK" not in stderr


def test_schema_mode_emits_actual_closed_schema_without_reading_or_writing(tmp_path: Path) -> None:
    missing = tmp_path / "absent-repository"
    code, stdout, stderr = _main(missing, "--show-schema")
    assert code == 0
    assert stderr == ""
    schema = json.loads(stdout)
    assert schema == contract_json_schema()
    assert schema["$defs"]["SkillWireV1"]["additionalProperties"] is False
    assert schema["$defs"]["AntiSkillWireV1"]["additionalProperties"] is False
    assert not missing.exists()


def test_write_and_check_modes_use_actual_four_host_writer(estate: Path) -> None:
    package = compile_typed_contracts(estate)
    code, stdout, stderr = _main(estate, "--write")
    assert code == 0
    assert stderr == ""
    assert stdout.decode().strip() == (
        "TYPED_PACKAGES_OK packages=2 files=8 contracts=" + package.contracts_digest
    )
    for skill_id, raw in package.packages:
        for host in HOST_SKILL_ROOTS:
            assert (estate / host / skill_id / "SKILL.md").read_bytes() == raw
    before = _snapshot(estate)
    assert _main(estate, "--check") == (code, stdout, stderr)
    assert _main(estate, "--write") == (code, stdout, stderr)
    assert _snapshot(estate) == before


def test_check_missing_projection_refuses_without_creating(estate: Path) -> None:
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--check"), "HOST_PROJECTION_MISSING")
    assert _snapshot(estate) == before


def test_write_late_host_conflict_keeps_entire_estate_unchanged(estate: Path) -> None:
    path = estate / HOST_SKILL_ROOTS[-1] / "woland-scope-falsifier/SKILL.md"
    path.parent.mkdir()
    path.write_bytes(b"Local host owner instruction.\n")
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "HOST_PROJECTION_CONFLICT")
    assert _snapshot(estate) == before


@pytest.mark.parametrize("overclaim", [False, True])
def test_audit_mode_replays_real_detector_and_keeps_unadmitted_ceiling(
    estate: Path, overclaim: bool
) -> None:
    subject = _subject(overclaim=overclaim)
    path = estate / "subject.json"
    path.write_bytes(canonical_json_bytes(subject.to_dict()))
    before = _snapshot(estate)
    code, stdout, stderr = _main(estate, "--audit-subject", str(path))
    assert code == 0
    assert stderr == ""
    receipt = json.loads(stdout)
    assert receipt["subject_id"] == subject.subject_id
    assert receipt["disposition"] == ("FINDING" if overclaim else "CLEAN")
    assert len(receipt["hits"]) == int(overclaim)
    assert receipt["evaluation_receipt"]["outcome"] == "COMPUTED_PASS"
    assert (receipt["admission"], receipt["runtime_activation"], receipt["authority_effect"]) == (
        "Unadmitted",
        "HOLD",
        "None",
    )
    assert _snapshot(estate) == before


@pytest.mark.parametrize(
    "raw",
    [
        b"{}",
        b"[]",
        b"null",
        b'{"claim_scope": [], "claim_scope": []}',
        b'{"value": NaN}',
        b"\xff",
        b"\xef\xbb\xbf{}",
    ],
)
def test_audit_malformed_input_refuses_without_success(estate: Path, raw: bytes) -> None:
    path = estate / "subject.json"
    path.write_bytes(raw)
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--audit-subject", str(path)), "TYPED_CONTRACT_REFUSED")
    assert _snapshot(estate) == before


@pytest.mark.parametrize("change", ["stale_id", "oversize_text", "boolean_scope", "extra_field"])
def test_audit_subject_content_cannot_bypass_typed_decoder(estate: Path, change: str) -> None:
    value = _subject().to_dict()
    if change == "stale_id":
        value["evidence_scope"] = ["foreign"]
    elif change == "oversize_text":
        value["producer_identity"] = "p" * 4097
    elif change == "boolean_scope":
        value["claim_scope"] = [True]
    else:
        value["approved"] = True
    path = estate / "subject.json"
    path.write_bytes(canonical_bytes(value))
    _assert_refused(_main(estate, "--audit-subject", str(path)), "TYPED_CONTRACT_REFUSED")
    assert not (estate / HOST_SKILL_ROOTS[0] / "woland-claim-audit").exists()


def test_audit_missing_subject_file_refuses(estate: Path) -> None:
    before = _snapshot(estate)
    _assert_refused(
        _main(estate, "--audit-subject", str(estate / "missing.json")), "TYPED_CONTRACT_REFUSED"
    )
    assert _snapshot(estate) == before


def test_audit_current_source_failure_cannot_emit_receipt(estate: Path) -> None:
    path = estate / "subject.json"
    path.write_bytes(canonical_json_bytes(_subject().to_dict()))
    (estate / CONTRACT_ROOT / "woland_scope_falsifier.json").unlink()
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--audit-subject", str(path)), "TYPED_CONTRACT_SOURCE_REFUSED")
    assert _snapshot(estate) == before


@pytest.mark.parametrize(
    "relative",
    [
        "woland_claim_audit.json",
        "woland_scope_falsifier.json",
        "instructions/woland_claim_audit.md",
        "scope_falsifier_fixtures.json",
    ],
)
def test_missing_source_or_resource_refuses_before_projection(estate: Path, relative: str) -> None:
    (estate / CONTRACT_ROOT / relative).unlink()
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "SOURCE_UNAVAILABLE")
    assert _snapshot(estate) == before


@pytest.mark.parametrize(
    "relative", ["woland_claim_audit.json", "instructions/woland_claim_audit.md"]
)
def test_oversize_source_or_resource_refuses_before_read_and_projection(
    estate: Path, relative: str
) -> None:
    path = estate / CONTRACT_ROOT / relative
    path.write_bytes(b"x" * 131073)
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "SOURCE_SIZE_REFUSED")
    assert _snapshot(estate) == before


def test_resource_hash_or_length_edit_cannot_be_hidden_by_cli(estate: Path) -> None:
    path = estate / CONTRACT_ROOT / "instructions/woland_claim_audit.md"
    path.write_bytes(path.read_bytes() + b"Local edit.\n")
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "RESOURCE_BINDING_REFUSED")
    assert _snapshot(estate) == before


@pytest.mark.parametrize("raw", [b"\xff\n", b"CRLF\r\n", b" \n", b"x" * 2049])
def test_rebound_instruction_decoding_or_shape_refuses(estate: Path, raw: bytes) -> None:
    _resource(estate, "woland_claim_audit.json", "instruction", raw)
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "INSTRUCTION_REFUSED")
    assert _snapshot(estate) == before


@pytest.mark.parametrize("raw", [b"{}", b"[]", b"\xff", b'{"cases": [], "cases": []}'])
def test_rebound_malformed_fixture_bank_refuses_before_projection(estate: Path, raw: bytes) -> None:
    _resource(estate, "woland_scope_falsifier.json", "fixtures", raw)
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "FIXTURE_BANK_REFUSED")
    assert _snapshot(estate) == before


def test_well_formed_rebound_bank_with_false_oracle_cannot_pass(estate: Path) -> None:
    bank_path = estate / CONTRACT_ROOT / "scope_falsifier_fixtures.json"
    bank = AntiSkillFixtureBankV1.from_dict(json.loads(bank_path.read_bytes()))
    first = replace(bank.cases[0], expected_hit=False, case_digest="")
    changed = replace(bank, cases=(first, *bank.cases[1:]), bank_id="")
    raw = canonical_json_bytes(changed.to_dict())
    _resource(estate, "woland_scope_falsifier.json", "fixtures", raw)
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "FALSIFIER_CONTROLS_REFUSED")
    assert _snapshot(estate) == before


def test_real_instruction_directory_link_refuses_outside_canonical_bytes(estate: Path) -> None:
    instructions = estate / CONTRACT_ROOT / "instructions"
    outside = estate.parent / (estate.name + "-outside")
    shutil.copytree(instructions, outside)
    for path in instructions.iterdir():
        path.unlink()
    instructions.rmdir()
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(instructions), str(outside)],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, (result.stdout, result.stderr)
    else:
        instructions.symlink_to(outside, target_is_directory=True)
    before = {path.name: path.read_bytes() for path in outside.iterdir()}
    _assert_refused(_main(estate, "--write"), "SOURCE_LINK_REFUSED")
    assert {path.name: path.read_bytes() for path in outside.iterdir()} == before
    assert not (estate / HOST_SKILL_ROOTS[0] / "woland-claim-audit").exists()


@pytest.mark.parametrize("mode", [[], ["--write", "--check"], ["--show-schema", "--write"]])
def test_cli_requires_exactly_one_mode(tmp_path: Path, mode: list[str], capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--repo-root", str(tmp_path), *mode])
    assert caught.value.code == 2
    output = capsys.readouterr()
    assert "error:" in output.err
    assert not tmp_path.joinpath(".agents").exists()


def test_resource_declared_length_mismatch_refuses_with_matching_hash(estate: Path) -> None:
    source = estate / CONTRACT_ROOT / "woland_claim_audit.json"
    value = json.loads(source.read_bytes())
    value["instruction"]["byte_length"] += 1
    source.write_bytes(canonical_bytes(value))
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "RESOURCE_BINDING_REFUSED")
    assert _snapshot(estate) == before


def test_directory_instead_of_instruction_is_not_a_resource(estate: Path) -> None:
    instruction = estate / CONTRACT_ROOT / "instructions/woland_claim_audit.md"
    instruction.unlink()
    instruction.mkdir()
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "SOURCE_PATH_REFUSED")
    assert _snapshot(estate) == before


def test_swapped_typed_contract_kinds_refuse_before_projection(estate: Path) -> None:
    first = estate / CONTRACT_ROOT / "woland_claim_audit.json"
    second = estate / CONTRACT_ROOT / "woland_scope_falsifier.json"
    first_bytes, second_bytes = first.read_bytes(), second.read_bytes()
    first.write_bytes(second_bytes)
    second.write_bytes(first_bytes)
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "CONTRACT_KINDS_REFUSED")
    assert _snapshot(estate) == before


def test_missing_declared_guard_dependency_refuses_before_projection(estate: Path) -> None:
    source = estate / CONTRACT_ROOT / "woland_claim_audit.json"
    value = json.loads(source.read_bytes())
    value["dependencies"] = []
    source.write_bytes(canonical_bytes(value))
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "DEPENDENCY_REFUSED")
    assert _snapshot(estate) == before


def test_valid_bank_with_unknown_spec_id_cannot_enter_replay(estate: Path) -> None:
    bank_path = estate / CONTRACT_ROOT / "scope_falsifier_fixtures.json"
    bank = AntiSkillFixtureBankV1.from_dict(json.loads(bank_path.read_bytes()))
    first = replace(bank.cases[0], spec_id="foreign-spec", case_digest="")
    changed = replace(bank, cases=(first, *bank.cases[1:]), bank_id="")
    _resource(
        estate,
        "woland_scope_falsifier.json",
        "fixtures",
        canonical_json_bytes(changed.to_dict()),
    )
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "FALSIFIER_CONTROLS_REFUSED")
    assert _snapshot(estate) == before


def test_bom_instruction_refuses_after_exact_resource_rebinding(estate: Path) -> None:
    _resource(estate, "woland_claim_audit.json", "instruction", b"\xef\xbb\xbftext\n")
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "INSTRUCTION_REFUSED")
    assert _snapshot(estate) == before


def test_instruction_limit_is_in_utf8_bytes(estate: Path) -> None:
    _resource(estate, "woland_claim_audit.json", "instruction", ("\u03c9" * 1025).encode())
    before = _snapshot(estate)
    _assert_refused(_main(estate, "--write"), "INSTRUCTION_REFUSED")
    assert _snapshot(estate) == before


def test_instruction_at_exact_byte_limit_projects_successfully(estate: Path) -> None:
    raw = b"x" * 2048
    _resource(estate, "woland_claim_audit.json", "instruction", raw)
    code, stdout, stderr = _main(estate, "--write")
    assert code == 0
    assert b"TYPED_PACKAGES_OK packages=2 files=8" in stdout
    assert stderr == ""
    for host in HOST_SKILL_ROOTS:
        markdown = (estate / host / "woland-claim-audit/SKILL.md").read_bytes()
        assert raw in markdown


@pytest.mark.parametrize("where", ["subject", "contract", "fixtures"])
def test_deep_malformed_json_is_a_cli_refusal_without_uncaught_recursion(
    estate: Path, where: str
) -> None:
    raw = b"[" * 1100 + b"0" + b"]" * 1100
    if where == "subject":
        path = estate / "subject.json"
        path.write_bytes(raw)
        mode = ("--audit-subject", str(path))
    elif where == "contract":
        (estate / CONTRACT_ROOT / "woland_claim_audit.json").write_bytes(raw)
        mode = ("--write",)
    else:
        _resource(estate, "woland_scope_falsifier.json", "fixtures", raw)
        mode = ("--write",)
    before = _snapshot(estate)
    _assert_refused(_main(estate, *mode), "TYPED_CONTRACT_REFUSED")
    assert _snapshot(estate) == before


def test_relative_repository_root_cli_write_and_check(estate: Path, monkeypatch) -> None:
    monkeypatch.chdir(estate)
    package = compile_typed_contracts(estate)
    code, stdout, stderr = _main(Path("."), "--write")
    assert code == 0, stderr
    assert stderr == ""
    assert stdout.decode().strip() == (
        "TYPED_PACKAGES_OK packages=2 files=8 contracts=" + package.contracts_digest
    )
    before = _snapshot(estate)
    assert _main(Path("."), "--check") == (code, stdout, stderr)
    assert _snapshot(estate) == before
    for skill_id, raw in package.packages:
        for host in HOST_SKILL_ROOTS:
            assert (estate / host / skill_id / "SKILL.md").read_bytes() == raw


def test_relative_root_directory_alias_is_not_resolved_away(estate: Path, monkeypatch) -> None:
    alias = estate.parent / (estate.name + "-alias")
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(estate)],
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, (result.stdout, result.stderr)
    else:
        alias.symlink_to(estate, target_is_directory=True)
    monkeypatch.chdir(estate.parent)
    before = _snapshot(estate)
    _assert_refused(_main(Path(alias.name), "--write"), "SOURCE_LINK_REFUSED")
    assert _snapshot(estate) == before
