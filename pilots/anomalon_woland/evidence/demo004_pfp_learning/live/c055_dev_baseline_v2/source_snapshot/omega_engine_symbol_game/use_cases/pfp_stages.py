"""Small-stage policy; checker defects never authorize more generation.

AuthorityEffect: None. This is a resource bound, not a convergence theorem.
"""
from dataclasses import dataclass

from .pfp_proposal import ProposalCheck, repair_feedback


@dataclass(frozen=True)
class PfpStagePolicy:
    max_stages: int = 2

    def __post_init__(self):
        if type(self.max_stages) is not int or not 1 <= self.max_stages <= 2:
            raise ValueError("PFP_STAGE_BOUND")

    def feedback_after(self, stage: int, result: ProposalCheck) -> str | None:
        if type(stage) is not int or not 1 <= stage <= self.max_stages:
            raise ValueError("INVALID_STAGE")
        if stage == self.max_stages:
            return None
        return repair_feedback(result)
