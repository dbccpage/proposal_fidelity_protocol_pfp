"""OEWAS operad resolver: compose and run typed op trees from the operad v2 inventory.

AuthorityEffect: None.
"""

from __future__ import annotations

from .executors import HOST_DETECTORS, HOST_EXECUTORS
from .resolver import (
    DEFAULT_MAX_OPS,
    Composition,
    Detector,
    Executor,
    Refusal,
    RunReceipt,
    Step,
    compose,
    run,
    wire_json,
)

__all__ = [
    "DEFAULT_MAX_OPS",
    "Composition",
    "Detector",
    "Executor",
    "HOST_DETECTORS",
    "HOST_EXECUTORS",
    "Refusal",
    "RunReceipt",
    "Step",
    "compose",
    "run",
    "wire_json",
]
