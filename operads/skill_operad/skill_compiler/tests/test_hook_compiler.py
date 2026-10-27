"""Hook compiler: hooks.json is generated from the register, and every hook names live rules."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from operads.skill_operad.skill_compiler import hook_compiler, rule_gate

REPO = Path(__file__).resolve().parents[4]
GUARD = "operads/hooks/hook_core/command_guard.py"


def _registry(status: str = "ENFORCED", enforced_by: str = f"{GUARD}::_inspect_git_push") -> dict:
    return {
        "rules": [
            {
                "path": "git/rl_x.md",
                "invariants": [{"id": "RULE_X_001", "status": status, "enforced_by": enforced_by}],
            }
        ],
        "external_sources": [],
        "hooks": [
            {
                "event": "PreToolUse",
                "matcher": "Bash",
                "script": "operads/hooks/scripts/pre_tool_git_guard.py",
                "description": "guard",
                "enforces": ["RULE_X_001"],
            }
        ],
    }


def _codes(root: Path, registry: dict) -> list[str]:
    return [finding.code for finding in hook_compiler.check_hooks(root, registry)]


@pytest.fixture
def root(tmp_path: Path) -> Path:
    script = tmp_path / "operads" / "hooks" / "scripts" / "pre_tool_git_guard.py"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    return tmp_path


def test_written_hooks_pass(root: Path) -> None:
    registry = _registry()
    hook_compiler.write_hooks(root, registry)
    assert _codes(root, registry) == []


def test_hand_edited_hooks_drift(root: Path) -> None:
    registry = _registry()
    hook_compiler.write_hooks(root, registry)
    target = root / hook_compiler.HOOKS_JSON
    target.write_text(target.read_text(encoding="utf-8").replace("guard", "edited"), encoding="utf-8")
    assert _codes(root, registry) == ["R10_HOOKS_DRIFT"]


def test_crlf_checkout_is_not_drift(root: Path) -> None:
    registry = _registry()
    hook_compiler.write_hooks(root, registry)
    target = root / hook_compiler.HOOKS_JSON
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
    assert _codes(root, registry) == []


def test_a_hook_cannot_enforce_a_candidate(root: Path) -> None:
    registry = _registry(status="CANDIDATE")
    hook_compiler.write_hooks(root, registry)
    assert _codes(root, registry) == ["R10_HOOK_RULE"]


def test_a_hook_rule_must_be_enforced_by_hook_code(root: Path) -> None:
    registry = _registry(enforced_by="ops/elsewhere.py::check")
    hook_compiler.write_hooks(root, registry)
    assert _codes(root, registry) == ["R10_HOOK_RULE"]


def test_a_hook_check_without_a_listing_hook_is_refused(root: Path) -> None:
    registry = _registry()
    registry["rules"][0]["invariants"].append(
        {"id": "RULE_Y_001", "status": "ENFORCED", "enforced_by": f"{GUARD}::_inspect_pytest"}
    )
    hook_compiler.write_hooks(root, registry)
    assert _codes(root, registry) == ["R10_HOOK_UNLISTED"]


def test_a_missing_script_is_refused(root: Path) -> None:
    registry = _registry()
    registry["hooks"][0]["script"] = "operads/hooks/scripts/gone.py"
    hook_compiler.write_hooks(root, registry)
    assert _codes(root, registry) == ["R10_HOOK_SCRIPT"]


def test_live_hooks_match_the_register() -> None:
    registry = rule_gate.load_registry(rule_gate.DEFAULT_REGISTRY)
    assert hook_compiler.check_hooks(REPO, registry) == []


@pytest.mark.parametrize(
    ("command", "rule"),
    [
        ("git push --force origin feature", "RULE_GIT_NO_FORCE_OR_MAIN_PUSH_001"),
        ("git push origin main", "RULE_GIT_NO_FORCE_OR_MAIN_PUSH_001"),
        ("git add -A", "RULE_GIT_EXPLICIT_STAGING_001"),
        ("git commit -am message", "RULE_GIT_NO_COMMIT_ALL_001"),
        ("python -m pytest", "RULE_PYTEST_TARGETED_RUNS_001"),
        ("git stash drop stash@{0}", "RULE_SHELL_QUOTED_STASH_REF_001"),
    ],
)
def test_each_refusal_names_its_rule(command: str, rule: str) -> None:
    sys.path.insert(0, str(REPO / "operads" / "hooks"))
    try:
        from hook_core.command_guard import evaluate_command
    finally:
        sys.path.pop(0)
    allowed, reason = evaluate_command(command)
    assert not allowed
    assert reason.startswith(f"[{rule}] ")


def test_a_named_push_is_allowed() -> None:
    sys.path.insert(0, str(REPO / "operads" / "hooks"))
    try:
        from hook_core.command_guard import evaluate_command
    finally:
        sys.path.pop(0)
    assert evaluate_command("git push -u origin feature") == (True, "")
