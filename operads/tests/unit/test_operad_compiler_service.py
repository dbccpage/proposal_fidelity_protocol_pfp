"""
Unit Tests for OEWAS Operad Compiler and Budget Services.
=========================================================

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from operads.application.operad import (
    OperadBudgetService,
    OperadCompilerService,
)


def test_compiler_service_parses_skills_garden(tmp_path: Path):
    # Create mock skill packages
    skill1_dir = tmp_path / "skill_alpha"
    skill1_dir.mkdir()
    (skill1_dir / "SKILL.md").write_text(
        "---\nname: skill-alpha\noperad_source_colours: [State, Code]\noperad_target_colour: Audit\n---\n# Skill Alpha",
        encoding="utf-8",
    )

    skill2_dir = tmp_path / "skill_beta"
    skill2_dir.mkdir()
    (skill2_dir / "SKILL.md").write_text(
        "---\nname: skill-beta\noperad_source_colours: [Audit]\noperad_target_colour: Receipt\n---\n# Skill Beta",
        encoding="utf-8",
    )

    compiler = OperadCompilerService()
    receipt = compiler.compile_skills_garden(tmp_path)

    assert receipt.passed
    assert "skill-alpha" in compiler.operad.operations
    assert "skill-beta" in compiler.operad.operations

    op_alpha = compiler.operad.operations["skill-alpha"]
    assert op_alpha.source_colours == ("State", "Code")
    assert op_alpha.target_colour == "Audit"


def test_budget_service_detects_excess_lines(tmp_path: Path):
    skill_dir = tmp_path / "skill_bloated"
    skill_dir.mkdir()

    # Create a 350-line file (exceeds 300 line limit)
    lines = ["Line " + str(i) for i in range(350)]
    (skill_dir / "SKILL.md").write_text("\n".join(lines), encoding="utf-8")

    budget_service = OperadBudgetService()
    res = budget_service.audit_skill_file(skill_dir / "SKILL.md")
    assert not res["passed"]
    assert res["lines"] == 350

    receipt = budget_service.audit_skills_directory(tmp_path)
    assert not receipt.passed
