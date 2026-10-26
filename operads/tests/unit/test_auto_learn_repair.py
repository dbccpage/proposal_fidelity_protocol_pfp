"""Tests for auto-learn automated repair step and file diff re-check."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
AUTO_LEARN_SCRIPT = REPO / "omega_engine_operads" / "skills" / "auto-learn" / "scripts" / "auto_learn.py"


def _load_auto_learn():
    spec = importlib.util.spec_from_file_location("auto_learn", AUTO_LEARN_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["auto_learn"] = module
    spec.loader.exec_module(module)
    return module


def test_repair_ap_md_058_bullet_transformation():
    auto_learn = _load_auto_learn()

    # Standard bullet
    success, res, conf = auto_learn.repair_ap_md_058("* Item one\n")
    assert success is True
    assert res == "- Item one\n"
    assert conf == "HIGH"

    # Indented bullet
    success, res, conf = auto_learn.repair_ap_md_058("    * Sub-item\n")
    assert success is True
    assert res == "    - Sub-item\n"
    assert conf == "HIGH"

    # Bold text (not a list bullet)
    success, res, conf = auto_learn.repair_ap_md_058("**Bold Heading**\n")
    assert success is False
    assert res == "**Bold Heading**\n"
    assert conf == "LOW"


def test_apply_high_confidence_fix_markdown_bullet():
    auto_learn = _load_auto_learn()

    sugg = {
        "anti_pattern_id": "AP_MD_058",
        "dual_healthy_pattern": "HP_MD_058_hyphen_list_bullet_syntax",
        "line": 1,
    }
    success, new_line, conf, explanation = auto_learn.apply_high_confidence_fix(sugg, "* test line\n")
    assert success is True
    assert new_line == "- test line\n"
    assert conf == "HIGH"


def test_apply_high_confidence_fix_skips_low_confidence_patterns():
    auto_learn = _load_auto_learn()

    sugg = {
        "anti_pattern_id": "AP_PY_002",
        "dual_healthy_pattern": "HP_PY_002_explicit_runtime_guards",
        "line": 1,
        "remediation_advice": "Replace assert with explicit guard exception.",
    }
    success, new_line, conf, explanation = auto_learn.apply_high_confidence_fix(sugg, "assert x > 0\n")
    assert success is False
    assert new_line == "assert x > 0\n"
    assert conf == "LOW"
    assert "manual review" in explanation


def test_repair_file_applies_smallest_diff_and_captures_diff(tmp_path: Path):
    auto_learn = _load_auto_learn()

    sample_md = tmp_path / "sample.md"
    sample_md.write_text(
        "# Title\n\n* First item\n* Second item\n\nSome text.\n",
        encoding="utf-8",
    )

    suggestions = [
        {
            "file": str(sample_md),
            "line": 3,
            "anti_pattern_id": "AP_MD_058",
            "dual_healthy_pattern": "HP_MD_058_hyphen_list_bullet_syntax",
            "remediation_advice": "Replace asterisk with hyphen.",
        },
        {
            "file": str(sample_md),
            "line": 4,
            "anti_pattern_id": "AP_MD_058",
            "dual_healthy_pattern": "HP_MD_058_hyphen_list_bullet_syntax",
            "remediation_advice": "Replace asterisk with hyphen.",
        },
    ]

    receipt = auto_learn.repair_file(
        file_path=sample_md,
        suggestions=suggestions,
        repo_root=tmp_path,
        dry_run=False,
        check_diff=False,
    )

    assert receipt.corrections_applied == 2
    assert receipt.corrections_skipped == 0
    assert "- First item" in sample_md.read_text(encoding="utf-8")
    assert "- Second item" in sample_md.read_text(encoding="utf-8")
    assert "* First item" not in sample_md.read_text(encoding="utf-8")
    assert "-* First item" in receipt.unified_diff
    assert "+- First item" in receipt.unified_diff


def test_repair_file_dry_run_does_not_modify_disk(tmp_path: Path):
    auto_learn = _load_auto_learn()

    sample_md = tmp_path / "sample_dry.md"
    original_text = "# Title\n\n* Untouched bullet\n"
    sample_md.write_text(original_text, encoding="utf-8")

    suggestions = [
        {
            "file": str(sample_md),
            "line": 3,
            "anti_pattern_id": "AP_MD_058",
            "dual_healthy_pattern": "HP_MD_058_hyphen_list_bullet_syntax",
        }
    ]

    receipt = auto_learn.repair_file(
        file_path=sample_md,
        suggestions=suggestions,
        repo_root=tmp_path,
        dry_run=True,
        check_diff=False,
    )

    assert receipt.status == "REPAIRED_DRY_RUN"
    assert receipt.corrections_applied == 1
    # Verify disk content was not changed
    assert sample_md.read_text(encoding="utf-8") == original_text
    # Verify unified diff was generated
    assert "+- Untouched bullet" in receipt.unified_diff


def test_extract_remediation_suggestions_from_varied_payloads():
    auto_learn = _load_auto_learn()

    # Raw list
    raw_list = [{"file": "a.md", "line": 1, "anti_pattern_id": "AP_MD_058"}]
    assert auto_learn.extract_remediation_suggestions(raw_list) == raw_list

    # Handoff with remediation_suggestions
    handoff = {"remediation_suggestions": raw_list}
    assert auto_learn.extract_remediation_suggestions(handoff) == raw_list

    # Handoff with nested changed_files_anti_pattern_lint
    nested = {"changed_files_anti_pattern_lint": {"remediation_suggestions": raw_list}}
    assert auto_learn.extract_remediation_suggestions(nested) == raw_list


def test_repair_integration_with_anti_pattern_lint_recheck(tmp_path: Path):
    auto_learn = _load_auto_learn()

    test_md = tmp_path / "test_notes.md"
    test_md.write_text("# Notes\n\n* Unapproved asterisk bullet\n", encoding="utf-8")

    # Initial audit should detect AP_MD_058
    lint_script = (
        REPO / "omega_engine_operads" / "skills" / "auto-anti-pattern-lint" / "scripts" / "anti_pattern_lint.py"
    )
    assert lint_script.is_file()

    import subprocess
    proc1 = subprocess.run(
        [sys.executable, str(lint_script), "--files", str(test_md), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc1.returncode == 1
    assert "Anti-pattern file findings: 1" in proc1.stdout

    suggestions = [
        {
            "file": str(test_md),
            "line": 3,
            "anti_pattern_id": "AP_MD_058",
            "dual_healthy_pattern": "HP_MD_058_hyphen_list_bullet_syntax",
            "remediation_advice": "Replace asterisk with hyphen.",
        }
    ]

    receipt = auto_learn.repair_file(
        file_path=test_md,
        suggestions=suggestions,
        repo_root=REPO,
        dry_run=False,
        check_diff=True,
    )

    assert receipt.status == "VERIFIED_CLEAN"
    assert receipt.corrections_applied == 1
    assert receipt.recheck_exit_code == 0
    assert receipt.recheck_findings_count == 0

    # Post-repair audit must pass with 0 findings
    proc2 = subprocess.run(
        [sys.executable, str(lint_script), "--files", str(test_md), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc2.returncode == 0
    assert "Anti-pattern file findings: 0" in proc2.stdout
    assert test_md.read_text(encoding="utf-8") == "# Notes\n\n- Unapproved asterisk bullet\n"


def test_extract_mypy_error_codes_assignment(tmp_path: Path):
    auto_learn = _load_auto_learn()

    test_py = tmp_path / "sample_type_error.py"
    test_py.write_text("x: str = 123  # type: ignore\n", encoding="utf-8")

    codes = auto_learn.extract_mypy_error_codes(test_py, 1, REPO)
    assert codes == ["assignment"]


def test_repair_ap_py_001_promotes_to_high_confidence(tmp_path: Path):
    auto_learn = _load_auto_learn()

    test_py = tmp_path / "sample_type_error.py"
    test_py.write_text("x: str = 123  # type: ignore\n", encoding="utf-8")

    success, new_line, conf, explanation = auto_learn.repair_ap_py_001(
        line="x: str = 123  # type: ignore\n",
        file_path=test_py,
        line_number=1,
        repo_root=REPO,
    )
    assert success is True
    assert conf == "HIGH"
    assert new_line == "x: str = 123  # type: ignore[assignment]\n"
    assert "assignment" in explanation


def test_repair_file_python_scoped_ignore_verified_clean(tmp_path: Path):
    auto_learn = _load_auto_learn()

    test_py = tmp_path / "mod_beta.py"
    test_py.write_text(
        "def compute(n: int) -> int:\n    res: str = n * 2  # type: ignore\n    return 0\n",
        encoding="utf-8",
    )

    suggestions = [
        {
            "file": str(test_py),
            "line": 2,
            "anti_pattern_id": "AP_PY_001",
            "dual_healthy_pattern": "HP_PY_001_scoped_mypy_overrides",
            "remediation_advice": "Replace blanket ignore with scoped override.",
        }
    ]

    receipt = auto_learn.repair_file(
        file_path=test_py,
        suggestions=suggestions,
        repo_root=REPO,
        dry_run=False,
        check_diff=True,
    )

    assert receipt.status == "VERIFIED_CLEAN"
    assert receipt.corrections_applied == 1
    assert "type: ignore[assignment]" in test_py.read_text(encoding="utf-8")
    assert "-    res: str = n * 2  # type: ignore" in receipt.unified_diff
    assert "+    res: str = n * 2  # type: ignore[assignment]" in receipt.unified_diff


def test_repair_ap_py_001_multi_code_comma_separated(tmp_path: Path):
    auto_learn = _load_auto_learn()

    test_py = tmp_path / "multi_code_error.py"
    code = (
        "def func(a: int) -> int:\n"
        "    return a\n\n"
        "val: str = func('hello')  # type: ignore\n"
    )
    test_py.write_text(code, encoding="utf-8")

    codes = auto_learn.extract_mypy_error_codes(test_py, 4, REPO)
    assert "assignment" in codes
    assert "arg-type" in codes

    success, new_line, conf, explanation = auto_learn.repair_ap_py_001(
        line="val: str = func('hello')  # type: ignore\n",
        file_path=test_py,
        line_number=4,
        repo_root=REPO,
    )
    assert success is True
    assert conf == "HIGH"
    assert "type: ignore[assignment, arg-type]" in new_line or "type: ignore[arg-type, assignment]" in new_line

    suggestions = [
        {
            "file": str(test_py),
            "line": 4,
            "anti_pattern_id": "AP_PY_001",
            "dual_healthy_pattern": "HP_PY_001_scoped_mypy_overrides",
            "remediation_advice": "Replace blanket ignore with scoped override.",
        }
    ]
    receipt = auto_learn.repair_file(
        file_path=test_py,
        suggestions=suggestions,
        repo_root=REPO,
        dry_run=False,
        check_diff=True,
    )
    assert receipt.status == "VERIFIED_CLEAN"
    assert receipt.corrections_applied == 1
    assert "type: ignore[" in test_py.read_text(encoding="utf-8")



