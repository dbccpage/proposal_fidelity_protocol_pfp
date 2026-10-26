"""Domain port for the Sandboxed Execution Seam (U09).

AuthorityEffect: None.
Untrusted model-generated code executes only in an isolated subprocess
under Windows Job Object boundaries with strict resource caps. Unsupported
isolation is refused before spawn; POSIX enforcement is not implemented.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class SandboxOutcomeKind(str, Enum):
    """Disjoint outcomes of sandboxed execution."""

    COMPLETED = "Completed"
    TIMED_OUT = "TimedOut"
    CPU_LIMIT_EXCEEDED = "CpuLimitExceeded"
    MEMORY_LIMIT_EXCEEDED = "MemoryLimitExceeded"
    OUTPUT_LIMIT_EXCEEDED = "OutputLimitExceeded"
    PROCESS_LIMIT_EXCEEDED = "ProcessLimitExceeded"
    LAUNCH_REFUSED = "LaunchRefused"
    ISOLATION_UNAVAILABLE = "IsolationUnavailable"


@dataclass(frozen=True)
class SandboxExecutionResult:
    """Execution receipt from the sandbox boundary."""

    outcome: SandboxOutcomeKind
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    peak_memory_bytes: int = 0
    detail: str | None = None
    authority_effect: str = "None"
    resource_observation: dict | None = None

    @property
    def is_success(self) -> bool:
        return self.outcome == SandboxOutcomeKind.COMPLETED and self.exit_code == 0


class ProcessSandboxPort(Protocol):
    """Protocol for executing untrusted child processes in an isolated sandbox."""

    def execute(
        self,
        command: Sequence[str],
        *,
        cwd: str | None = None,
        timeout_ms: int = 5000,
        memory_limit_bytes: int = 268_435_456,
        max_output_bytes: int = 1_048_576,
        env: Mapping[str, str] | None = None,
    ) -> SandboxExecutionResult:
        """Execute a command under process isolation with strict resource caps."""
        ...


__all__ = [
    "ProcessSandboxPort",
    "SandboxExecutionResult",
    "SandboxOutcomeKind",
]
