"""Composition root for four-host skill mirroring."""

from __future__ import annotations

from typing import Sequence

from omega_engine_operations.infrastructure.packaging import MirrorRecoveryFactory
from omega_engine_operations.use_cases.packaging.sync_cross_host_skills import (
    main as run_skill_mirror,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run skill mirroring with production custody and locking adapters."""
    return run_skill_mirror(argv, recovery_factory=MirrorRecoveryFactory())


if __name__ == "__main__":
    raise SystemExit(main())
