"""Finite checks for the proved rows of The Authority Gap.

These functions call the package checkers. They do not reimplement the
gluing ratio, the backlog product, or the packet refutation rule.
"""

from __future__ import annotations

from fractions import Fraction

from mod_authority_gap_core import (
    Attestation,
    AuthorityPacket,
    Institution,
    ObserverPacket,
    Proposal,
    Residual,
    Terminal,
    TerminalStatus,
    TraceRecord,
    calculate_backlog_accumulation,
    calculate_ngd,
    evaluate_exactness_fraud_criterion,
)


def _packet(descent: bool, defect: Fraction) -> AuthorityPacket:
    proposal = Proposal(
        proposal_id="prop_proved",
        generator_id="agent_generator_alpha",
        payload="candidate",
        context="declared context",
    )
    trace = TraceRecord.create(
        trace_id="tr_proved",
        actions=["read"],
        tool_calls=["lookup"],
        sources=["record"],
        proposal=proposal,
    )
    observer = ObserverPacket(
        carrier="carrier",
        local_states=("ready",),
        comparisons=("compare",),
        defects=(),
        admissible_repairs=(),
        gauge="gauge",
        closure_diagnostics=(),
    )
    institution = Institution(
        entity_id="office",
        governing_jurisdiction="declared",
        accountable_officer="officer",
        appeal_path="appeal",
    )
    return AuthorityPacket(
        proposal=proposal,
        trace=trace,
        observer=observer,
        residual=Residual(defect_mass=defect, unverified_scope=(), refusal_reasons=()),
        terminal=Terminal(
            status=TerminalStatus.AUTHORIZED_UNDER_OBSERVER,
            decider_id="officer_jane_doe",
            is_human_or_delegated_body=True,
            justification="claimed",
        ),
        attestation=Attestation(
            descent_executed=descent,
            verification_hash="",
            replay_receipt=None,
        ),
        institution=institution,
    )


def replay_proved_rows() -> dict:
    hidden = [
        {"local_green": True, "global_red": left != right}
        for left in (0, 1)
        for right in (0, 1)
    ]
    extreme = [
        {"local_green": True, "global_red": True},
        {"local_green": True, "global_red": True},
    ]
    hidden_ngd = calculate_ngd(hidden)
    extreme_ngd = calculate_ngd(extreme)
    worked = calculate_backlog_accumulation(Fraction(50, 1), Fraction(10, 1), 12)
    step = calculate_backlog_accumulation(10, 3, 1)
    verified = Fraction(3, 1)
    share = verified / (step + verified)
    missing_descent, missing_reason = evaluate_exactness_fraud_criterion(_packet(False, Fraction(0, 1)))
    nonzero, nonzero_reason = evaluate_exactness_fraud_criterion(_packet(True, Fraction(3, 10)))
    return {
        "ok": hidden_ngd == Fraction(1, 2)
        and extreme_ngd == Fraction(1, 1)
        and worked == Fraction(480, 1)
        and step == Fraction(7, 1)
        and share == Fraction(3, 10)
        and missing_descent is False
        and nonzero is False,
        "CLM-005-007": {
            "hidden_bit_ngd": str(hidden_ngd),
            "unconditional_red_ngd": str(extreme_ngd),
            "hidden_bit_cases": len(hidden),
        },
        "CLM-005-010": {
            "backlog_50_10_12": str(worked),
            "backlog_10_3_1": str(step),
            "verified_share_10_3": str(share),
        },
        "CLM-005-011": {
            "missing_descent_admitted": missing_descent,
            "missing_descent_reason": missing_reason,
            "nonzero_residual_admitted": nonzero,
            "nonzero_residual_reason": nonzero_reason,
        },
    }
