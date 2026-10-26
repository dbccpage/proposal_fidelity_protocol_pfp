#!/usr/bin/env python3
"""Domain Constants for the operad Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

ADMITTED_FINITE_COLOURS: tuple[str, ...] = (
    "Audit",
    "Code",
    "Contract",
    "Diagram",
    "Ledger",
    "Paper",
    "Post",
    "Proof",
    "Receipt",
    "State",
)

REQUIRED_CONTRACTIVE_RUNS: int = 3
EVIDENCE_TRACE_SCHEMA: str = "omega.operad.evidence_trace.v1"
