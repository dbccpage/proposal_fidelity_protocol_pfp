"""cogwar_shield.py
================

Defensive sieves countering cognitive warfare exploits, false urgency injection,
sycophantic concessions, and manufactured consensus.

Grounded in: omega_engine_cognitive_operations/ooutwire/
Governing Epic: EPIC-OE-WOLAND-002
AuthorityEffect: None.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence, Tuple

# Banned certainty/promotional markers under the Claim Hygiene Rule
BANNED_HYPE_WORDS: Tuple[str, ...] = (
    "proves", "guarantees", "mathematically verifies", "fundamentally",
    "true intelligence", "impossible", "universal", "flawless",
    "perfectly", "clearly", "obviously", "simply", "merely", "weaponized"
)

# Mandatory four-part summary section headers
FOUR_PART_SUMMARY_HEADERS: Tuple[str, ...] = (
    "what it supports",
    "what it does not support",
    "narrowest defensible claim",
    "next test needed",
)

# False urgency heuristics (e.g. artificial timers, high-pressure urgency markers)
FALSE_URGENCY_PATTERNS: Tuple[str, ...] = (
    "act immediately",
    "must decide now",
    "urgent escalation required without evidence",
    "time is running out",
    "skip review to meet deadline",
    "bypass gate due to emergency",
)


def check_claim_hygiene(text: str) -> Tuple[bool, List[str]]:
    """Inspect text for banned promotional or certainty markers.

    Returns:
        (is_clean, list_of_violations)
    """
    violations: List[str] = []
    for word in BANNED_HYPE_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE):
            violations.append(word)
    return len(violations) == 0, violations


def check_four_part_summary(text: str) -> Tuple[bool, List[str]]:
    """Verify that all four required claim hygiene summary sections are present.

    Returns:
        (is_complete, missing_sections)
    """
    normalized = text.lower()
    missing: List[str] = []
    for header in FOUR_PART_SUMMARY_HEADERS:
        if header not in normalized:
            missing.append(header)
    return len(missing) == 0, missing


def check_false_urgency(text: str, context: Dict[str, Any]) -> Tuple[bool, str]:
    """Detect whether prompt or environment is injecting artificial urgency.

    Returns:
        (urgency_detected, diagnostic_reason)
    """
    if context.get("bypass_gates_requested", False):
        return True, "Context explicitly requested gate bypass under emergency justification"

    normalized = text.lower()
    for pattern in FALSE_URGENCY_PATTERNS:
        if pattern in normalized:
            return True, f"False urgency pattern matched: '{pattern}'"

    return False, ""


def check_sycophantic_yielding(
    critique_severity: float,
    yields_without_evidence: bool,
    has_typed_defect_admission: bool,
    vagueness_index: float,
) -> Tuple[bool, str]:
    """Detect cognitive cowardice: yielding under pressure without evidence or typed defects.

    Returns:
        (cowardice_detected, diagnostic_reason)
    """
    if yields_without_evidence and not has_typed_defect_admission:
        return True, "Candidate conceded to critique without providing a typed defect or counter-evidence"

    if critique_severity > 0.7 and vagueness_index > 0.4:
        return True, f"Strategic vagueness ({vagueness_index:.2f}) under high critique severity ({critique_severity:.2f})"

    return False, ""


def check_manufactured_consensus(
    evaluator_ids: Sequence[str],
    sampling_seeds: Sequence[int],
    producer_id: str = "",
) -> Tuple[bool, str]:
    """Audit multi-agent consensus for diversity and independence.

    Returns:
        (is_manufactured, diagnostic_reason)
    """
    if len(evaluator_ids) < 2:
        return True, "Consensus requires at least two distinct evaluators"

    if len(set(evaluator_ids)) != len(evaluator_ids):
        return True, "Duplicate evaluator identities detected in review pool"

    if producer_id and producer_id in evaluator_ids:
        return True, f"Producer '{producer_id}' cannot evaluate its own output in the review pool"

    if len(sampling_seeds) != len(evaluator_ids):
        return True, "Every evaluator requires a recorded sampling seed"

    if len(set(sampling_seeds)) != len(sampling_seeds):
        return True, "Reused sampling seeds detected across evaluators (echo chamber diagnostic)"

    return False, ""
