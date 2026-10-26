"""Domain Ports & Protocols for Operad operations.

AuthorityEffect: None.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Protocol

from .evidence import DiagnosticObservation
from omega_engine_operads.domain.operad.operad import ColouredOperad


class OperadRepositoryPort(Protocol):
    """Port for operad repository persistence and loading."""

    root_dir: Path

    def load_operad(self) -> ColouredOperad:
        ...

    def load_composition_matrix(self) -> Dict[str, Any]:
        ...

    def load_agent_capability_slices(self) -> Dict[str, Any]:
        ...

    def load_evidence_traces(self) -> List[DiagnosticObservation]:
        ...

    def save_operad_signatures(self, operad: ColouredOperad) -> None:
        ...


class FileLockPort(Protocol):
    """Port for exclusive file locking."""

    def __call__(
        self, lock_path: Path, timeout_seconds: float = 30.0
    ) -> contextlib.AbstractContextManager[None]:
        ...


@contextlib.contextmanager
def null_file_lock(
    lock_path: Path, timeout_seconds: float = 30.0
) -> Iterator[None]:
    """Null object implementation of FileLockPort (no-op context manager)."""
    yield
