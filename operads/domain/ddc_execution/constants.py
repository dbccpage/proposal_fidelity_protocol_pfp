#!/usr/bin/env python3
"""Domain Constants for the operad Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

from operads.canon import OPERAD_COLOUR

ADMITTED_FINITE_COLOURS: tuple[str, ...] = OPERAD_COLOUR

REQUIRED_CONTRACTIVE_RUNS: int = 3
EVIDENCE_TRACE_SCHEMA: str = "core.operad.evidence_trace.v1"
