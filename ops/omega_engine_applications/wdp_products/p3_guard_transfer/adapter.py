"""P3 transferable guard library.

``omega_wdp`` has no ``guard_transfer`` owner, and no host action calls one.
This adapter does not import the paper package. AuthorityEffect: None.
"""

from __future__ import annotations

from omega_engine_applications.wdp_products.kernel.contracts import TypedRefusal
from omega_engine_applications.wdp_products.p3_guard_transfer.contracts import (
    BreakEven,
    GuardRule,
    GuardTransferChecker,
)

GUARD_TRANSFER_OWNER = "omega_wdp::guard_transfer"


def _missing(owner: str) -> TypedRefusal:
    return TypedRefusal(
        code="missing_native_owner",
        reason=f"missing owner {owner}; authority_effect=None",
        authority_effect="None",
    )


def _invalid(reason: str) -> TypedRefusal:
    return TypedRefusal(code="invalid_input", reason=reason, authority_effect="None")


def make_source_guard_rule(
    rule_id: str,
    source_task: object,
    *,
    soundness_claim: str = "WDP-CHS-P19:source-sound",
) -> GuardRule | TypedRefusal:
    """Refuse: no native owner can digest ``source_task`` into a source guard."""
    if not isinstance(rule_id, str) or not rule_id:
        return _invalid("rule_id must be a non-empty string")
    if not isinstance(source_task, dict):
        return _invalid("source_task must be a dict")
    if not isinstance(soundness_claim, str) or not soundness_claim:
        return _invalid("soundness_claim must be a non-empty string")
    return _missing(GUARD_TRANSFER_OWNER)


def q4_worked_example_ledger(hits: int = 13) -> BreakEven:
    """Appendix Q.4 ledger arithmetic on the product contract. Not a transfer result."""
    return BreakEven(
        candidates=10000,
        hits=hits,
        verify_cost="1",
        guard_cost="1/1000",
        setup_cost="2",
    )


class WdpGuardTransferChecker:
    """GuardTransferChecker that names the missing guard-transfer owner."""

    def transfer(self, rule: GuardRule, target: object) -> GuardRule | TypedRefusal:
        if not isinstance(rule, GuardRule) or not isinstance(target, dict):
            return _invalid("rule must be a GuardRule and target must be a dict")
        return _missing(GUARD_TRANSFER_OWNER)

    def price(self, rule: GuardRule, ledger: BreakEven) -> TypedRefusal:
        if not isinstance(rule, GuardRule) or not isinstance(ledger, BreakEven):
            return _invalid("rule must be a GuardRule and ledger must be a BreakEven")
        return _missing(GUARD_TRANSFER_OWNER)


def evaluate_pilot_p3_kill_conditions() -> TypedRefusal:
    """PROD-P3-KILL cannot admit a transferred rule without ``omega_wdp::guard_transfer``."""
    rule = GuardRule(
        rule_id="circulation",
        source_instance_digest="pilot-source",
        soundness_claim="WDP-CHS-P19:source-sound",
    )
    refusal = WdpGuardTransferChecker().transfer(rule, {"pilot": "p3"})
    if isinstance(refusal, TypedRefusal):
        return refusal
    return _missing(GUARD_TRANSFER_OWNER)


_check_protocol: GuardTransferChecker = WdpGuardTransferChecker()
