"""Demographic models and state transitions for Prompt Civilization.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import enum
from fractions import Fraction
from typing import Any, Mapping


@enum.unique
class PopulationTier(str, enum.Enum):
    """The 4-population demographic lifecycle tiers (+ Cemetery refusal store).

    - WILD: Untrusted inbound user queries and uncurated model continuations.
    - CANDIDATE: Synthesized failure motifs and candidate anti-skills (no authority).
    - REVIEWED: Passed negative selection and holdout banks (provisional, no normative authority).
    - ADMITTED: Human-authorized, versioned, cryptographically sealed formulary.
    - CEMETERY: Permanently refused or discarded failure archive.
    """

    WILD = "WILD"
    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    ADMITTED = "ADMITTED"
    CEMETERY = "CEMETERY"


class UnauthorizedAdmissionError(Exception):
    """Raised when attempting to promote a prompt to ADMITTED without an operator cryptographic signature.

    Enforces the Demographic Law: Recurrence and PageRank propose candidates;
    they never grant normative authority.
    """


@dataclass(frozen=True)
class CivilizationPrompt:
    """A prompt or behavioral instruction residing in a demographic tier."""

    prompt_id: str
    content: str
    tier: PopulationTier
    pagerank_score: Fraction = Fraction(0, 1)
    operator_signature: str | None = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if isinstance(self.pagerank_score, float):
            raise TypeError("Float pagerank_score violates Zero-Float law; use Fraction")
        if not isinstance(self.pagerank_score, Fraction):
            object.__setattr__(self, "pagerank_score", Fraction(self.pagerank_score))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.prompt_id == other.prompt_id
            and self.content == other.content
            and self.tier == other.tier
            and self.pagerank_score == other.pagerank_score
            and self.operator_signature == other.operator_signature
            and self.authority_effect == other.authority_effect
        )


@dataclass(frozen=True)
class PromotionDecision:
    """Decision recording demographic promotion or refusal."""

    prompt_id: str
    from_tier: PopulationTier
    to_tier: PopulationTier
    is_admitted: bool
    status: str
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.prompt_id == other.prompt_id
            and self.from_tier == other.from_tier
            and self.to_tier == other.to_tier
            and self.is_admitted == other.is_admitted
            and self.status == other.status
            and self.reason == other.reason
        )


@dataclass
class CivilizationState:
    """State machine governing the 4-population lifecycle."""

    prompts: dict[str, CivilizationPrompt] = field(default_factory=dict)

    def register_wild_prompt(self, prompt_id: str, content: str) -> CivilizationPrompt:
        """Register an untrusted inbound prompt in the WILD tier."""
        p = CivilizationPrompt(
            prompt_id=prompt_id,
            content=content,
            tier=PopulationTier.WILD,
            pagerank_score=Fraction(0, 1),
        )
        self.prompts[prompt_id] = p
        return p

    def promote_to_candidate(
        self, prompt_id: str, pagerank_score: Fraction = Fraction(1, 10)
    ) -> PromotionDecision:
        """Promote a prompt from WILD to CANDIDATE based on recurring motif."""
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            raise KeyError(f"Prompt {prompt_id} not found in civilization")
        if prompt.tier is not PopulationTier.WILD:
            raise ValueError(
                f"Prompt {prompt_id} must be in WILD tier, currently in {prompt.tier}"
            )

        new_prompt = CivilizationPrompt(
            prompt_id=prompt.prompt_id,
            content=prompt.content,
            tier=PopulationTier.CANDIDATE,
            pagerank_score=Fraction(pagerank_score),
            operator_signature=None,
        )
        self.prompts[prompt_id] = new_prompt
        return PromotionDecision(
            prompt_id=prompt_id,
            from_tier=prompt.tier,
            to_tier=PopulationTier.CANDIDATE,
            is_admitted=False,
            status="PROMOTED_TO_CANDIDATE",
            reason="Prompt synthesized into candidate anti-skill; no normative authority",
        )

    def promote_to_reviewed(self, prompt_id: str) -> PromotionDecision:
        """Promote a prompt from CANDIDATE to REVIEWED after negative selection."""
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            raise KeyError(f"Prompt {prompt_id} not found in civilization")
        if prompt.tier is not PopulationTier.CANDIDATE:
            raise ValueError(f"Prompt {prompt_id} must be in CANDIDATE tier, currently in {prompt.tier}")

        new_prompt = CivilizationPrompt(
            prompt_id=prompt.prompt_id,
            content=prompt.content,
            tier=PopulationTier.REVIEWED,
            pagerank_score=prompt.pagerank_score,
            operator_signature=None,
        )
        self.prompts[prompt_id] = new_prompt
        return PromotionDecision(
            prompt_id=prompt_id,
            from_tier=prompt.tier,
            to_tier=PopulationTier.REVIEWED,
            is_admitted=False,
            status="PROMOTED_TO_REVIEWED",
            reason="Passed negative selection holdout banks; provisional status, no normative authority",
        )

    def promote_to_admitted(
        self, prompt_id: str, operator_signature: str | None = None
    ) -> PromotionDecision:
        """Refuse admission. A ``sig:ed25519:`` prefix is not a grant.

        No sealed-token check lives here. The stored authority stays ``None``.
        """
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            raise KeyError(f"Prompt {prompt_id} not found in civilization")
        if prompt.tier is not PopulationTier.REVIEWED:
            raise ValueError(f"Prompt {prompt_id} must be in REVIEWED tier, currently in {prompt.tier}")

        raise UnauthorizedAdmissionError(
            f"Promotion of prompt '{prompt_id}' to ADMITTED strictly requires a valid cryptographic operator signature; "
            f"got {operator_signature!r}. A sig:ed25519: prefix is not a grant. "
            "Demographic Law: PageRank proposes; human authority admits."
        )

    def promote_to_cemetery(
        self, prompt_id: str, reason: str = "Refused"
    ) -> PromotionDecision:
        """Move a prompt to the permanent CEMETERY refusal tier."""
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            raise KeyError(f"Prompt {prompt_id} not found in civilization")

        new_prompt = CivilizationPrompt(
            prompt_id=prompt.prompt_id,
            content=prompt.content,
            tier=PopulationTier.CEMETERY,
            pagerank_score=prompt.pagerank_score,
            operator_signature=None,
        )
        self.prompts[prompt_id] = new_prompt
        return PromotionDecision(
            prompt_id=prompt_id,
            from_tier=prompt.tier,
            to_tier=PopulationTier.CEMETERY,
            is_admitted=False,
            status="CEMETERY_ARCHIVED",
            reason=reason,
        )


__all__ = [
    "CivilizationPrompt",
    "CivilizationState",
    "PopulationTier",
    "PromotionDecision",
    "UnauthorizedAdmissionError",
]
