"""PFP -> native Symbol Game certificate seam, initially scoped to Q40/C021.

No native process implementation is duplicated here. The canonical OEOS seam
owns invocation, hashing, and the complete runtime outcome. AuthorityEffect: None.
"""

from __future__ import annotations

from ...use_cases.pfp_proposal import parse_proposal


class SymbolGameProposalAdapter:
    def __init__(self, host):
        self.host = host

    def verify_q40(self, case, raw_reply):
        """Keep the full native railway outcome; a refusal is never a Python pass."""
        answer = parse_proposal(raw_reply)["answer"]
        return self.host.stabilizer_check(case, answer)
