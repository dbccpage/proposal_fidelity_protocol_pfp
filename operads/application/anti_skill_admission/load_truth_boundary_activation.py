"""Retired compatibility boundary for Python truth-boundary activation.

The loader returns a typed retirement refusal without reading evidence or
activating a profile. Active detector work lives in the Rust implementation.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Refusal, Result

from .retirement import runtime_retired


def load_truth_boundary_activation(
    *,
    canary_directory: Path,
    admitted_directory: Path,
    profile_id: str = "woland-engineering-v1",
) -> Result[Any, Refusal]:
    """Refuse the retired path without reading evidence or activating a profile."""
    return runtime_retired("governance-anti-skill-loader")


__all__ = ["load_truth_boundary_activation"]
