"""Retraction context for synthesis repair attempts (U10).

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetractionContext:
    module_name: str
    attempt_number: int
    spec_text: str
    schema_card: str
    previous_code: str | None = None
    failing_diff: str | None = None
    error_feedback: str = ""
    authority_effect: str = "None"

    def render_prompt(self) -> str:
        """Renders prompt enforcing retraction invariants.

        Invariant:
        For attempt >= 2, previous_code AND failing_diff MUST be provided.
        MUTATION KILL GATE: Omitting previous_code or failing_diff raises ValueError!
        """
        prompt = (
            f"### Module Synthesis: {self.module_name}\n"
            f"Attempt: {self.attempt_number}\n\n"
            f"Specification:\n{self.spec_text}\n\n"
            f"Schema:\n{self.schema_card}\n\n"
        )

        if self.attempt_number >= 2:
            if not self.previous_code:
                raise ValueError("REPAIR_MISSING_PREVIOUS_CODE: attempt >= 2 requires previous code")
            if not self.failing_diff:
                raise ValueError("REPAIR_MISSING_FAILING_DIFF: attempt >= 2 requires failing diff")

            prompt += (
                "### Previous Code (Failed Host Verification)\n```python\n"
                f"{self.previous_code}\n"
                "```\n\n"
                "### Failure Diagnostics & Diff\n"
                f"{self.failing_diff}\n\n"
                f"Error Feedback:\n{self.error_feedback}\n\n"
                "Please repair the code to eliminate all failure modes.\n"
            )
        else:
            prompt += "Please synthesize code matching the specification.\n"

        return prompt
