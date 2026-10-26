#!/usr/bin/env python3
"""Domain enumerations for the paper_iteration Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class AuthorityEffect(str, Enum):
    """Execution authority effect indicator."""

    NONE = "None"
    READ = "Read"


class ResearchMode(str, Enum):
    """Research evaluation execution mode."""

    FAST = "fast"
    STRICT = "strict"
    SYMBOL = "symbol"
    FULL = "full"


class ResearchGate(str, Enum):
    """Individual verification gate in the paper iteration pipeline."""

    PACKET_SHAPE = "packet_shape"
    CORPUS_REPLAY = "corpus_replay"
    FIDELITY = "fidelity"
    CLAIM_HYGIENE = "claim_hygiene"
    MECHANICAL = "mechanical"
    ADVERSARIAL = "adversarial"
    CITATION_PROVENANCE = "citation_provenance"
    AUTHORITY_FIREWALL = "authority_firewall"


class GateVerdict(str, Enum):
    """Terminal verification decision for an individual gate."""

    PASS = "pass"
    FAIL = "fail"
    OPEN = "open"
    REFUSE = "refuse"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"


class ResearchTerminal(str, Enum):
    """Aggregate lifecycle disposition for a evaluated research packet."""

    READY_FOR_HUMAN_REVIEW = "ready_for_human_review"
    EXPLORATORY_CANDIDATE = "exploratory_candidate"
    THEORY_REFUTATION_CANDIDATE = "theory_refutation_candidate"
    REPAIR_REQUIRED = "repair_required"
    ORACLE_NEEDED = "oracle_needed"
    REFUSED = "refused"
    PROCESS_OBSTRUCTION = "process_obstruction"


class LedgerLane(str, Enum):
    """Routing lane in the paper iteration ledger."""

    HUMAN_REVIEW = "human_review"
    EXPLORATORY = "exploratory"
    OBLIGATIONS = "obligations"
    FAILURE_ATLAS = "failure_atlas"
