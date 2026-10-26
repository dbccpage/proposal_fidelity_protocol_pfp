"""Cherry Receipt Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CherryReceipt:
    """Typed evidence from `git cherry` (or equivalent measured subprocess)."""

    exit_status: int
    argv: tuple[str, ...]
    stdout_lines: tuple[str, ...]
    candidate_sha: str
    main_sha: str

    def __post_init__(self) -> None:
        if not isinstance(self.argv, tuple):
            object.__setattr__(self, "argv", tuple(self.argv))
        if not isinstance(self.stdout_lines, tuple):
            object.__setattr__(self, "stdout_lines", tuple(self.stdout_lines))
