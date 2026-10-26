"""Domain rules common helpers for supplement review rules.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import re
from pathlib import PurePosixPath
from typing import Any, Dict, Iterator, List, Optional, Sequence, Set, Tuple

from ..base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
)

MAX_FINDINGS = 50


def _cap(findings: List[RuleFinding]) -> List[RuleFinding]:
    return findings[:MAX_FINDINGS]


def _python_code_files(ctx: PaperContext) -> Iterator[str]:
    """Iterate over Python files in the code/ tree, skipping archives."""
    for path in ctx.list_paths():
        if path.startswith("code/") and path.endswith(".py"):
            parts = PurePosixPath(path).parts
            if not any(p.lower() in ("archive", "archives", "_archive") for p in parts):
                yield path
