"""Inbound data port for StructureBench bundle evaluation."""

from typing import Protocol


class BundleReader(Protocol):
    """Read-only bundle boundary supplied to the evaluator.

    Implementations decide where bytes live.  The evaluator depends only on
    this port, so in-memory readers can exercise every constraint without host
    filesystem access.
    """

    def is_bundle(self) -> bool:
        """Return whether the bundle container is available."""

    def read(self, name: str) -> bytes | None:
        """Return one named artifact, or ``None`` when it is unavailable."""


__all__ = ["BundleReader"]
