"""EPIC-OE-OEWAS-006 pins the live budget gate and refuses a 16/16 claim.

A SKILL.md past the gate's own line or byte ceiling, with no approved unexpired
exception, is a BREACH from check_budgets. The census reads DEFAULT_GOVERNED
when that name is assigned, and SEED_GOVERNED when it is the only governed
name. Reading case ids does not run eval_runner.py.
"""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest

from omega_engine_operads.application.anti_skill_admission.generate_truth_boundary_canary import (
    generate_truth_boundary_canary,
)
from omega_engine_operads.infrastructure import skill_budget_census
from omega_engine_operads.infrastructure.skill_budget_census import (
    EVAL_BANK_SCHEMA,
    GATE_SOURCE,
    CensusError,
    EvalBankIndex,
    read_eval_bank_index,
    read_gate_terms,
)
from omega_engine_operads.skill_operad.skill_compiler.budget_gate import (
    DEFAULT_GOVERNED,
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_LINES,
    SEED_GOVERNED,
    check_budgets,
)

REPO = Path(__file__).resolve().parents[3]
TODAY = date(2026, 10, 2)
FORBIDDEN_ENGINES = (
    "SkillCompilerEngine",
    "TruthBoundaryCanaryHarness",
    "GardenNaturalSelectionAuditor",
)
SCANNED_SOURCES = (
    GATE_SOURCE,
    Path("omega_engine_operads/infrastructure/skill_budget_census.py"),
    Path("omega_engine_operads/application/operad/compiler_service.py"),
    Path(
        "omega_engine_operads/application/anti_skill_admission/generate_truth_boundary_canary.py"
    ),
    Path("omega_engine_operads/skill_operad/skill_compiler/eval_runner.py"),
)


def _write_gate(root: Path, source: str) -> None:
    gate = root / GATE_SOURCE
    gate.parent.mkdir(parents=True)
    gate.write_text(source, encoding="utf-8")


def _write_skill(root: Path, name: str, text: str) -> None:
    skill = root / ".agents" / "skills" / name
    skill.mkdir(parents=True)
    skill.joinpath("SKILL.md").write_text(text, encoding="utf-8")


def test_gate_source_names_the_live_file_not_the_missing_operations_path() -> None:
    assert GATE_SOURCE.as_posix().endswith(
        "omega_engine_operads/skill_operad/skill_compiler/budget_gate.py"
    )
    assert (REPO / GATE_SOURCE).is_file()
    assert (
        REPO / "omega_engine_operations/skill_operad/skill_compiler/budget_gate.py"
    ).is_file() is False
    assert ".agents/operad/skill_compiler/budget_gate.py" not in (skill_budget_census.__doc__ or "")
    assert "5 of 110" not in (skill_budget_census.__doc__ or "")


def test_live_gate_terms_are_the_assigned_constants() -> None:
    terms = read_gate_terms(REPO)
    assert terms.max_lines == DEFAULT_MAX_LINES == 300
    assert terms.max_bytes == DEFAULT_MAX_BYTES == 20 * 1024
    assert terms.governed == frozenset(DEFAULT_GOVERNED)
    assert SEED_GOVERNED == DEFAULT_GOVERNED
    assert "auto-skill" in terms.governed


def test_seed_governed_is_readable_when_default_governed_is_absent(tmp_path: Path) -> None:
    _write_gate(
        tmp_path,
        "SEED_GOVERNED = ('from-seed',)\nDEFAULT_MAX_LINES = 300\nDEFAULT_MAX_BYTES = 20 * 1024\n",
    )
    terms = read_gate_terms(tmp_path)
    assert terms.governed == frozenset({"from-seed"})
    assert terms.max_lines == 300
    assert terms.max_bytes == 20480


def test_default_governed_wins_when_both_names_are_literal_sequences(
    tmp_path: Path,
) -> None:
    _write_gate(
        tmp_path,
        "DEFAULT_GOVERNED = ('from-default',)\n"
        "SEED_GOVERNED = ('from-seed',)\n"
        "DEFAULT_MAX_LINES = 300\n"
        "DEFAULT_MAX_BYTES = 20480\n",
    )
    terms = read_gate_terms(tmp_path)
    assert terms.governed == frozenset({"from-default"})


def test_absent_gate_is_gate_absent(tmp_path: Path) -> None:
    with pytest.raises(CensusError) as excinfo:
        read_gate_terms(tmp_path)
    assert excinfo.value.code == "GATE_ABSENT"


def test_neither_governed_name_is_gate_unreadable(tmp_path: Path) -> None:
    _write_gate(
        tmp_path,
        "DEFAULT_MAX_LINES = 300\nDEFAULT_MAX_BYTES = 20480\n",
    )
    with pytest.raises(CensusError) as excinfo:
        read_gate_terms(tmp_path)
    assert excinfo.value.code == "GATE_UNREADABLE"
    assert "DEFAULT_GOVERNED" in str(excinfo.value)
    assert "SEED_GOVERNED" in str(excinfo.value)


def test_seed_alias_without_a_literal_sequence_is_unreadable(tmp_path: Path) -> None:
    _write_gate(
        tmp_path,
        "SEED_GOVERNED = DEFAULT_GOVERNED\nDEFAULT_MAX_LINES = 300\nDEFAULT_MAX_BYTES = 20480\n",
    )
    with pytest.raises(CensusError) as excinfo:
        read_gate_terms(tmp_path)
    assert excinfo.value.code == "GATE_UNREADABLE"


def test_over_line_skill_without_an_exception_is_a_breach(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_skill(tmp_path, "fat", "\n".join(["line"] * (DEFAULT_MAX_LINES + 1)))
    rc = check_budgets(
        tmp_path,
        ["fat"],
        DEFAULT_MAX_LINES,
        DEFAULT_MAX_BYTES,
        {},
        today=TODAY,
    )
    assert rc == 1
    assert "[BREACH] fat:" in capsys.readouterr().out


def test_over_byte_skill_without_an_exception_is_a_breach(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    skill = tmp_path / ".agents" / "skills" / "wide"
    skill.mkdir(parents=True)
    skill.joinpath("SKILL.md").write_bytes(b"x" * (DEFAULT_MAX_BYTES + 1))
    rc = check_budgets(
        tmp_path,
        ["wide"],
        DEFAULT_MAX_LINES,
        DEFAULT_MAX_BYTES,
        {},
        today=TODAY,
    )
    assert rc == 1
    assert "[BREACH] wide:" in capsys.readouterr().out


def test_unapproved_raised_limit_is_still_a_breach(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_skill(tmp_path, "fat", "\n".join(["line"] * (DEFAULT_MAX_LINES + 1)))
    rc = check_budgets(
        tmp_path,
        ["fat"],
        DEFAULT_MAX_LINES,
        DEFAULT_MAX_BYTES,
        {
            "fat": {
                "approved": False,
                "expires": "2026-12-31",
                "reason": "not approved",
                "max_lines": DEFAULT_MAX_LINES + 50,
                "max_bytes": DEFAULT_MAX_BYTES + 50,
            }
        },
        today=TODAY,
    )
    assert rc == 1
    assert "[BREACH] fat:" in capsys.readouterr().out


def test_approved_unexpired_exception_is_not_a_breach(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_skill(tmp_path, "fat", "\n".join(["line"] * (DEFAULT_MAX_LINES + 1)))
    rc = check_budgets(
        tmp_path,
        ["fat"],
        DEFAULT_MAX_LINES,
        DEFAULT_MAX_BYTES,
        {
            "fat": {
                "approved": True,
                "expires": "2026-12-31",
                "reason": "temporary split",
                "max_lines": DEFAULT_MAX_LINES + 1,
            }
        },
        today=TODAY,
    )
    captured = capsys.readouterr().out
    assert rc == 0
    assert "[BREACH]" not in captured
    assert "[EXCEPTION] fat:" in captured


def test_eval_bank_ids_are_named_and_not_a_run() -> None:
    index = read_eval_bank_index(REPO)
    assert index.schema == EVAL_BANK_SCHEMA
    assert index.executed is False
    assert index.case_ids[0] == "sc-01-dda-oe010-shared-contract"
    assert "sc-16-historical-pr-immunity-shared-contract" in index.case_ids
    assert "sc-17-verification-boundary-float-injection" in index.case_ids
    assert type(index.executed) is bool
    again = EvalBankIndex(schema=index.schema, case_ids=index.case_ids, executed=False)
    assert index == again
    assert hash(index) == hash(again)


def test_eval_bank_index_cannot_record_a_run() -> None:
    with pytest.raises(CensusError) as excinfo:
        EvalBankIndex(schema=EVAL_BANK_SCHEMA, case_ids=("sc-01",), executed=True)
    assert excinfo.value.code == "BANK_NOT_RUN"
    with pytest.raises(CensusError) as typed:
        EvalBankIndex(schema=EVAL_BANK_SCHEMA, case_ids=("sc-01",), executed=1)  # type: ignore[arg-type]
    assert typed.value.code == "BANK_NOT_RUN"


def test_eval_bank_index_rejects_a_different_type() -> None:
    index = EvalBankIndex(schema="s", case_ids=("a",), executed=False)
    with pytest.raises(AssertionError):
        index.__eq__(object())


def test_canary_generator_raises_and_writes_nothing(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        generate_truth_boundary_canary(tmp_path / "out")
    assert list(tmp_path.iterdir()) == []


def test_named_compiler_engines_stay_absent() -> None:
    defined: set[str] = set()
    for relative in SCANNED_SOURCES:
        source = (REPO / relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        defined.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        )
    assert defined.isdisjoint(FORBIDDEN_ENGINES)
