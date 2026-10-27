"""Validator for the Eight Candidate Runtime Laws of DDC."""

from __future__ import annotations

from .alphabet import DDCRune
from .trace import DDCTrace


class DDCValidationError(Exception):
    """Raised when a DDC trace violates one of the eight candidate runtime laws."""
    pass


class DDCRuntimeLawValidator:
    """Enforces the 8 candidate runtime laws over a DDC execution trace."""

    @staticmethod
    def validate_trace(trace: DDCTrace) -> None:
        """Validates all transitions against Laws 1 through 8."""
        steps = trace.steps
        terminal_reached = False
        last_was_refusal = False

        for i, step in enumerate(steps):
            # Law 2: Terminal Absorption
            if terminal_reached:
                raise DDCValidationError(
                    f"Law 2 Violation (Terminal Absorption): Step {i} ({step.rune.value}) executed after terminal T."
                )

            if step.rune == DDCRune.T:
                terminal_reached = True

            # Law 1: Receipt Determinism (except if purely unadmitted proposal before intake)
            if step.receipt is None:
                raise DDCValidationError(
                    f"Law 1 Violation (Receipt Determinism): Step {i} ({step.rune.value}) lacks a deterministic step receipt."
                )

            # Law 3: Refusal Absorption
            if last_was_refusal and step.rune not in (DDCRune.C, DDCRune.T, DDCRune.LIFT):
                raise DDCValidationError(
                    f"Law 3 Violation (Refusal Absorption): Step {i} ({step.rune.value}) illegally retried after refusal M without LCE or reset."
                )
            last_was_refusal = (step.rune == DDCRune.M)

            # Law 4: Lift Trigger Law
            if step.rune == DDCRune.LIFT:
                # Structural lift requires Phi_1 > 0 and Gamma_2 == 0 (Stabilized Survivor)
                if not (step.pre_phi1 > 0 and step.pre_gamma2 == 0):
                    raise DDCValidationError(
                        f"Law 4 Violation (Lift Trigger Law): Step {i} proposed Λ without stabilized survivor status (pre_phi1={step.pre_phi1}, pre_gamma2={step.pre_gamma2})."
                    )

            # Law 5: Integration Requires Receipt
            if step.rune == DDCRune.I:
                if not step.receipt or not step.receipt.witness_digest:
                    raise DDCValidationError(
                        f"Law 5 Violation (Integration Requires Receipt): Step {i} (I) lacks cryptographic witness digest."
                    )

            # Law 6: Descent Requires Loss Ledger
            if step.rune == DDCRune.D:
                if not step.loss_ledger:
                    raise DDCValidationError(
                        f"Law 6 Violation (Descent Requires Loss Ledger): Step {i} (D) performed scale descent without declaring dropped coordinates."
                    )

            # Law 7: Exact Repair Monotonicity
            if step.rune == DDCRune.E:
                if not step.preserves_or_decreases_defect():
                    raise DDCValidationError(
                        f"Law 7 Violation (Exact Repair Monotonicity): Step {i} (E) increased defect mass (post: phi1={step.post_phi1}, gamma2={step.post_gamma2} vs pre: phi1={step.pre_phi1}, gamma2={step.pre_gamma2})."
                    )

            # Law 8: Context Exposure Is Not Repair
            if step.rune == DDCRune.C:
                if step.post_phi1 < step.pre_phi1 or step.post_gamma2 < step.pre_gamma2:
                    raise DDCValidationError(
                        f"Law 8 Violation (Context Exposure Is Not Repair): Step {i} (C) cannot reduce defect mass."
                    )
