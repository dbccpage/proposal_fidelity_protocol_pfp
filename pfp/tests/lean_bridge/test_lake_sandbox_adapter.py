"""Tests for Sandboxed Lake 4 Verification Adapter (U17).

Tests lexer scanning, axiom auditing, and typed refusal on missing toolchain.
AuthorityEffect: None.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import pytest

from omega_engine_pfp.domain.lean_bridge.models import (
    LeanVerificationRequest,
    LeanVerificationReceipt,
)
from omega_engine_pfp.infrastructure.adapters.lake_sandbox_adapter import (
    LakeSandboxAdapter,
)
from omega_engine_pfp.ffi import get_default_host


def test_lean_scan_sources_comments_and_strings_ignored() -> None:
    host = get_default_host()

    code = r"""
-- Line comment with sorry and axiom
/-
   Block comment:
   /- Nested block comment with sorry and unsafe -/
   still in block comment: admit
-/
def greeting : String := "this string has sorry and axiom"
theorem valid_thm : True := trivial
"""
    sources = [{"file": "Valid.lean", "content": code}]
    outcome = host.lean_scan_sources(sources)
    assert outcome.is_ok
    raw = outcome.unwrap()
    res = raw.get("result", raw)
    assert res["clean"] is True
    assert len(res["findings"]) == 0


def test_lean_scan_sources_flags_code_constructs() -> None:
    host = get_default_host()

    code = r"""
axiom my_cheat : False
theorem bad_proof : 1 = 2 := by
  sorry
"""
    sources = [{"file": "Bad.lean", "content": code}]
    outcome = host.lean_scan_sources(sources)
    assert outcome.is_ok
    raw = outcome.unwrap()
    res = raw.get("result", raw)
    assert res["clean"] is False
    findings = res["findings"]
    assert len(findings) == 2
    constructs = [f["construct"] for f in findings]
    assert "axiom" in constructs
    assert "sorry" in constructs


def test_lean_audit_report_policy_check() -> None:
    host = get_default_host()

    # Clean case
    clean_out = host.lean_audit_report(
        axioms_output="'judge_check_1' depends on axioms: [propext, Quot.sound]\n",
        policy=["propext", "Quot.sound"],
        required_declarations=["judge_check_1"],
        build_success=True,
        harness_elaborated=True,
    )
    assert clean_out.is_ok
    res_clean = clean_out.unwrap().get("result", clean_out.unwrap())
    assert res_clean["status"] == "PASS"
    assert res_clean["refusal_code"] is None

    # Axiom violation case
    bad_out = host.lean_audit_report(
        axioms_output="'judge_check_1' depends on axioms: [propext, Quot.sound, Classical.choice]\n",
        policy=["propext", "Quot.sound"],
        required_declarations=["judge_check_1"],
        build_success=True,
        harness_elaborated=True,
    )
    assert bad_out.is_ok
    res_bad = bad_out.unwrap().get("result", bad_out.unwrap())
    assert res_bad["status"] == "FAIL"
    assert res_bad["refusal_code"] == "AXIOM_POLICY_VIOLATION"


def test_lake_toolchain_unavailable_typed_refusal(tmp_path: Path) -> None:
    # Explicitly test that missing lake returns LEAN_TOOLCHAIN_UNAVAILABLE and does NOT silently skip
    fake_lake = tmp_path / "nonexistent_lake_binary_executable"
    adapter = LakeSandboxAdapter(lake_binary=fake_lake)

    req = LeanVerificationRequest(
        package_digest="pkg_digest_123",
        toolchain_pin="leanprover/lean4:v4.34.0",
        required_declarations=(("my_thm", "1 = 1"),),
    )

    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "Test.lean").write_text("theorem my_thm : 1 = 1 := rfl\n", encoding="utf-8")

    result = adapter.verify(req, pkg_dir)
    assert result.is_err
    refusal = result.unwrap_err()
    assert refusal.code == "LEAN_TOOLCHAIN_UNAVAILABLE"


def test_lake_adapter_simulated_success(tmp_path: Path) -> None:
    # Test full adapter orchestration with mocked subprocess execution
    fake_lake = tmp_path / "fake_lake"
    fake_lake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    adapter = LakeSandboxAdapter(lake_binary=fake_lake)

    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "Clean.lean").write_text("theorem my_thm : 1 = 1 := rfl\n", encoding="utf-8")
    (pkg_dir / "Second.lean").write_text("theorem second_thm : True := trivial\n", encoding="utf-8")
    (pkg_dir / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    (pkg_dir / ".lake/packages/cached").mkdir(parents=True)
    (pkg_dir / ".lake/packages/cached/Stale.lean").write_text("axiom cached : False\n", encoding="utf-8")

    req = LeanVerificationRequest(
        package_digest="pkg_clean_123",
        toolchain_pin="leanprover/lean4:v4.34.0",
        required_declarations=(("my_thm", "1 = 1"),),
    )

    real_run = subprocess.run
    lake_commands = []

    def mock_subprocess_run(cmd, **kwargs):
        if not any("lake" in str(arg).lower() for arg in cmd):
            return real_run(cmd, **kwargs)
        lake_commands.append(cmd)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        if "lean" in cmd and "Verify.lean" in cmd:
            harness = (Path(kwargs["cwd"]) / "Verify.lean").read_text(encoding="utf-8")
            assert "import Clean Second\n" in harness
            mock_proc.stdout = "'judge_check_1' depends on axioms: [propext, Quot.sound]\n"
        else:
            mock_proc.stdout = "Building Clean...\n"
        mock_proc.stderr = ""
        return mock_proc

    with patch(
        "omega_engine_pfp.infrastructure.adapters.lake_sandbox_adapter.subprocess.run",
        side_effect=mock_subprocess_run,
    ):
        result = adapter.verify(req, pkg_dir)
        assert result.is_ok
        receipt = result.unwrap()
        assert isinstance(receipt, LeanVerificationReceipt)
        assert receipt.status == "PASS"
        assert receipt.build_success is True
        assert receipt.harness_elaborated is True
        assert receipt.authority_effect == "None"
        assert receipt.refusal_code is None
        assert lake_commands[0] == [str(fake_lake), "build", "+Clean:olean", "+Second:olean"]


def test_lake_adapter_refuses_configuration_without_submitted_modules(tmp_path: Path) -> None:
    fake_lake = tmp_path / "fake_lake"
    fake_lake.write_text("unused", encoding="utf-8")
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    result = LakeSandboxAdapter(lake_binary=fake_lake).verify(
        LeanVerificationRequest("empty", "leanprover/lean4:v4.34.1", (("missing", "True"),)),
        package,
    )
    assert result.is_err
    assert result.unwrap_err().code == "LEAN_SOURCE_MODULES_UNAVAILABLE"
