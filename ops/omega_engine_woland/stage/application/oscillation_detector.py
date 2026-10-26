"""Swarm proposal token distance tracking and oscillation circuit-breaker.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Set, Tuple

from ..domain.packets import CandidateProposalV1


def extract_proposal_tokens(proposal: CandidateProposalV1) -> Set[str]:
    """Extract normalized alphanumeric tokens from proposal nonclaims and artifact references."""
    parts = list(proposal.nonclaims) + list(proposal.artifact_refs)
    text = " ".join(parts).lower()
    return set(re.findall(r"\w+", text))


def proposal_semantic_distance(p1: CandidateProposalV1, p2: CandidateProposalV1) -> Fraction:
    """Compute normalized token-level Jaccard distance between proposals in [0, 1] over Q.

    0 represents complete token identity (potential stall).
    1 represents completely disjoint token sets.
    """
    t1 = extract_proposal_tokens(p1)
    t2 = extract_proposal_tokens(p2)
    if not t1 and not t2:
        return Fraction(0, 1)
    union = len(t1 | t2)
    if union == 0:
        return Fraction(0, 1)
    intersection = len(t1 & t2)
    return Fraction(union - intersection, union)


@dataclass
class OscillationDetectorV1:
    """Tracks proposal token distance within scenes and triggers circuit breaks on repetitive cycles."""

    stall_distance_threshold: Fraction | float = field(default_factory=lambda: Fraction(1, 10))
    max_stagnant_turns: int = 2
    recent_proposals_by_scene: Dict[str, List[CandidateProposalV1]] = field(default_factory=dict)
    stagnant_count_by_scene: Dict[str, int] = field(default_factory=dict)
    tripped: bool = False
    tripped_scene_id: str = ""
    last_distance: Fraction = field(default_factory=lambda: Fraction(1, 1))

    def __post_init__(self) -> None:
        if isinstance(self.stall_distance_threshold, (int, float)) and not isinstance(
            self.stall_distance_threshold, Fraction
        ):
            self.stall_distance_threshold = Fraction(str(self.stall_distance_threshold))
        if (
            not isinstance(self.stall_distance_threshold, Fraction)
            or not (Fraction(0, 1) <= self.stall_distance_threshold <= Fraction(1, 1))
        ):
            raise ValueError("stall_distance_threshold must be finite and in [0, 1]")
        if type(self.max_stagnant_turns) is not int or self.max_stagnant_turns < 1:
            raise ValueError("max_stagnant_turns must be a positive integer")
        if isinstance(self.last_distance, (int, float)) and not isinstance(
            self.last_distance, Fraction
        ):
            self.last_distance = Fraction(str(self.last_distance))

    def record_and_evaluate(
        self,
        scene_id: str,
        proposal: CandidateProposalV1,
        progressed: bool,
    ) -> Tuple[bool, Fraction]:
        """Record a candidate proposal for a scene and return (is_stalled, distance).

        A stall is flagged if consecutive proposals have distance below the threshold
        AND the step failed to make progress on the DDC tape (progressed is False).
        """
        history = self.recent_proposals_by_scene.setdefault(scene_id, [])
        if not history:
            history.append(proposal)
            self.stagnant_count_by_scene[scene_id] = 0
            return False, Fraction(1, 1)

        last_proposal = history[-1]
        dist = proposal_semantic_distance(last_proposal, proposal)
        self.last_distance = dist
        history[:] = [proposal]

        if dist < self.stall_distance_threshold and not progressed:
            count = self.stagnant_count_by_scene.get(scene_id, 0) + 1
            self.stagnant_count_by_scene[scene_id] = count
            if count >= self.max_stagnant_turns:
                self.tripped = True
                self.tripped_scene_id = scene_id
                return True, dist
        else:
            self.stagnant_count_by_scene[scene_id] = 0

        return False, dist

    def reset(self) -> None:
        """Reset internal history and circuit breaker state."""
        self.recent_proposals_by_scene.clear()
        self.stagnant_count_by_scene.clear()
        self.tripped = False
        self.tripped_scene_id = ""
        self.last_distance = Fraction(1, 1)


__all__ = [
    "OscillationDetectorV1",
    "extract_proposal_tokens",
    "proposal_semantic_distance",
]
