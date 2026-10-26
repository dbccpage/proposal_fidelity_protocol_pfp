#!/usr/bin/env python3
"""Mechanical Hook Gatekeeper: PreToolUse interceptor (legacy wrapper).

Delegates directly to pre_tool_git_guard to prevent policy drift.
AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pre_tool_git_guard import evaluate_command as check_command  # noqa: E402
from pre_tool_git_guard import main  # noqa: E402

__all__ = ["check_command", "main"]

if __name__ == "__main__":
    sys.exit(main())
