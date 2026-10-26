#!/usr/bin/env python3
"""Pre-execution hook: mechanically block forbidden git commands and whole-suite sweeps.

Command-pattern diagnostic for explicitly configured host hook integrations across
Google Antigravity, Claude Code, and Codex.

Exit code 2 signals mechanical rejection to agent runtimes.
Exit code 0 signals permitted execution.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure hook_core is discoverable regardless of execution cwd
_HOOKS_ROOT = Path(__file__).resolve().parent.parent
if str(_HOOKS_ROOT) not in sys.path:
    sys.path.insert(0, str(_HOOKS_ROOT))

from hook_core.command_guard import evaluate_command  # noqa: E402
from hook_core.envelope import extract_payload  # noqa: E402


def extract_command(raw_input: str) -> str:
    """Extract command line string from raw CLI arg or stdin payload."""
    payload = extract_payload([raw_input] if raw_input else [], "", expected_kind="command")
    if payload.command is not None:
        return payload.command
    return raw_input.strip()


def main() -> int:
    cli_args = sys.argv[1:]
    raw_stdin = ""
    if not cli_args:
        try:
            if not sys.stdin.isatty():
                raw_stdin = sys.stdin.read()
        except (OSError, ValueError):
            raw_stdin = ""

    payload = extract_payload(cli_args, raw_stdin, expected_kind="command")

    if payload.status == "INPUT_ERROR":
        sys.stderr.write(
            f"\n[MECHANICAL_HOOK_INPUT_ERROR] Invalid hook payload:\n  {payload.error_message}\n\n"
        )
        return 2

    if payload.status == "NOT_APPLICABLE" or not payload.command:
        return 0

    allowed, reason = evaluate_command(payload.command)
    if not allowed:
        sys.stderr.write(
            f"\n[MECHANICAL_HOOK_GATEKEEPER_BLOCKED] Execution rejected by AGENTS.md safety fence:\n"
            f"  Reason:  {reason}\n"
            f"  Command: {payload.command}\n\n"
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
