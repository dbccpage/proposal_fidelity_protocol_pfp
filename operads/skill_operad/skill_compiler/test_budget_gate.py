from __future__ import annotations

from datetime import date
from pathlib import Path

from budget_gate import (
    DEFAULT_MAX_BYTES,
    DEFAULT_MAX_LINES,
    check_budgets,
    load_exceptions,
)


def write_skill(root: Path, name: str, lines: int) -> None:
    skill_dir = root / ".agents" / "skills" / name
    skill_dir.mkdir(parents=True)
    skill_dir.joinpath("SKILL.md").write_text("\n".join(["line"] * lines), encoding="utf-8")


def run_gate(tmp_path: Path, exception: dict) -> int:
    write_skill(tmp_path, "oversize", 4)
    return check_budgets(
        tmp_path,
        ["oversize"],
        max_lines=1,
        max_bytes=20 * 1024,
        exceptions={"oversize": exception},
        today=date(2026, 8, 8),
    )


def test_future_expiry_allows_approved_exception(tmp_path: Path) -> None:
    result = run_gate(
        tmp_path,
        {
            "approved": True,
            "expires": "2026-09-01",
            "reason": "temporary split",
            "max_lines": 4,
        },
    )

    assert result == 0


def test_expired_exception_fails_closed(tmp_path: Path) -> None:
    result = run_gate(
        tmp_path,
        {"approved": True, "expires": "2026-01-01", "reason": "expired"},
    )

    assert result == 1


def test_missing_expiry_fails_closed(tmp_path: Path) -> None:
    result = run_gate(tmp_path, {"approved": True, "reason": "no expiry"})

    assert result == 1


def test_malformed_expiry_fails_closed(tmp_path: Path) -> None:
    result = run_gate(
        tmp_path,
        {"approved": True, "expires": "soon", "reason": "malformed"},
    )

    assert result == 1


def test_repo_budget_exceptions_are_unexpired_and_sufficient() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    exception_path = repo_root / ".agents" / "operad" / "yaml" / "budget_exceptions.yaml"
    if not exception_path.is_file():
        exception_path = repo_root / ".agents" / "operad" / "skill_compiler" / "budget_exceptions.yaml"

    result = check_budgets(
        repo_root,
        ["auto-improve-autoskill", "auto-symmetry-hunter"],
        max_lines=DEFAULT_MAX_LINES,
        max_bytes=DEFAULT_MAX_BYTES,
        exceptions=load_exceptions(exception_path),
        today=date(2026, 8, 8),
    )

    assert result == 0
