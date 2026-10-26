"""P1 AbstentionGovernor over the native WDP kernel certificate checker.

Implements the AbstentionGovernor protocol from p1_abstention_governor/contracts.py
using the existing kernel WdpCertificateChecker and DTO-owned label rule.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from fractions import Fraction

from omega_engine_applications.wdp_products.kernel.adapter import (
    WdpCertificateChecker,
)
from omega_engine_applications.wdp_products.kernel.contracts import (
    TypedRefusal,
    is_rational_text,
)
from omega_engine_applications.wdp_products.p1_abstention_governor.contracts import (
    AbstentionGovernor,
    GovernorReport,
    TerminationLabel,
    derive_label,
)


class WdpAbstentionGovernor:
    """AbstentionGovernor using native certificate replay and the existing label rule.

    Reproduces the reference label assignment across all certificate-backed outcomes
    and supports declared controller refusal actions (TerminationLabel.REFUSED) when
    no certificate is submitted. AuthorityEffect: None.
    """

    def __init__(self, checker: WdpCertificateChecker | None = None) -> None:
        self.checker = checker if checker is not None else WdpCertificateChecker()

    def report(
        self,
        model: object,
        certificate: object,
        budget: str,
        *,
        task_admits_impossibility: bool,
        evidence_refs: tuple[str, ...] = (),
        refusal_action: str | None = None,
    ) -> GovernorReport | TypedRefusal:
        """Assign a checked TerminationLabel and return a validated GovernorReport."""
        if type(task_admits_impossibility) is not bool:
            return TypedRefusal(
                code="invalid_input",
                reason="task reporting policy must be an explicit boolean",
                authority_effect="None",
            )
        if not isinstance(budget, str) or not is_rational_text(budget):
            return TypedRefusal(
                code="invalid_input",
                reason="budget must be a canonical exact rational string",
                authority_effect="None",
            )
        try:
            if Fraction(budget) < 0:
                raise ValueError("negative value or nonpositive action cost")
        except (ValueError, ZeroDivisionError) as exc:
            return TypedRefusal(
                code="invalid_input",
                reason=str(exc),
                authority_effect="None",
            )

        if refusal_action is not None or (
            certificate is None and any(ref.startswith("refusal_action:") for ref in evidence_refs)
        ):
            if certificate is not None:
                return TypedRefusal(
                    code="invalid_input",
                    reason="Refused controller action carries no certificate receipt",
                    authority_effect="None",
                )
            if refusal_action is not None and (
                not isinstance(refusal_action, str) or not refusal_action.strip()
            ):
                return TypedRefusal(
                    code="invalid_input",
                    reason="refusal_action must be a nonempty string",
                    authority_effect="None",
                )
            refs = (
                evidence_refs
                if evidence_refs
                else (f"refusal_action:{refusal_action}",)
            )
            return GovernorReport(
                label=TerminationLabel.REFUSED,
                task_admits_impossibility=task_admits_impossibility,
                budget=budget,
                check=None,
                evidence_refs=refs,
            )

        check_receipt = self.checker.check(model, certificate)
        if any(reason.startswith(("WDP_NATIVE_UNAVAILABLE", "WDP_NATIVE_BINDING_MISMATCH",
                                  "WDP_NATIVE_REFUSED")) for reason in check_receipt.failures):
            return TypedRefusal(code="native_unavailable", reason="; ".join(check_receipt.failures))
        label = derive_label(
            check_receipt, budget,
            task_admits_impossibility=task_admits_impossibility,
        )
        return GovernorReport(
            label=label,
            task_admits_impossibility=task_admits_impossibility,
            budget=budget,
            check=check_receipt,
            evidence_refs=evidence_refs,
        )


def operator_decision_for_label(label: TerminationLabel) -> str:
    """Map a P1 TerminationLabel onto a deterministic operator workflow action."""
    if not isinstance(label, TerminationLabel):
        raise TypeError(f"Expected TerminationLabel, got {type(label).__name__}")
    if label is TerminationLabel.RESOLVED_WITHIN_BUDGET:
        return "proceed_to_emit"
    if label is TerminationLabel.EXHAUSTED:
        return "request_budget_or_prune"
    if label is TerminationLabel.UNDETERMINED_BUDGET:
        return "request_tighter_certificate"
    if label in (TerminationLabel.LOSING_IN_DECLARED_ARENA, TerminationLabel.IMPOSSIBLE):
        return "halt_and_escalate_arena_revision"
    return "abort_on_refusal_or_stalled"


def evaluate_pilot_p1_kill_conditions() -> dict[str, object]:
    """Evaluate PROD-P1-KILL on the pilot arena and losing rollout variant.

    Checks that none of the P1 kill conditions hold:
    1. 'Arenas for real tasks exceed the solver's practical size' -> False
       (pilot arena has 4 states <= 64 practical solver ceiling).
    2. 'Labels do not change any operator decision in a pilot' -> False
       (ResolvedWithinBudget -> proceed_to_emit, Exhausted -> request_budget_or_prune,
        LosingInDeclaredArena -> halt_and_escalate_arena_revision).
    3. 'A LOSS certificate cannot be produced on real agent rollouts' -> False
       (when repair_provenance is disabled on rejected states, solve_progress
        has a retained LOSS certificate checked by the native owner).
    AuthorityEffect: None.
    """
    from omega_engine_applications.wdp_products.kernel.adapter import (
        PILOT_ARENA_USABLE_BUDGET,
        declare_pilot_agent_loop_arena,
        pilot_agent_loop_certificate,
    )

    arena = declare_pilot_agent_loop_arena()
    win_cert = pilot_agent_loop_certificate(arena)
    governor = WdpAbstentionGovernor()

    rep_resolved = governor.report(
        arena, win_cert, PILOT_ARENA_USABLE_BUDGET, task_admits_impossibility=False
    )
    rep_exhausted = governor.report(
        arena, win_cert, "2", task_admits_impossibility=False
    )
    assert isinstance(rep_resolved, GovernorReport)
    assert isinstance(rep_exhausted, GovernorReport)

    # Retained finite losing declaration/certificate, independently replayed natively.
    losing_arena = json.loads('{"actions":["issue_receipt","retry_without_repair","run_g5_gate"],"assumptions":["A1","A2","A4","A5","A6"],"authorization":{"effect":"None"},"costs":[{"action":"run_g5_gate","belief":["draft"],"cost":"1"},{"action":"issue_receipt","belief":["gated"],"cost":"1"},{"action":"retry_without_repair","belief":["rejected"],"cost":"1"}],"emissions":{},"enabled":{"draft":["run_g5_gate"],"gated":["issue_receipt"],"rejected":["retry_without_repair"],"verified":[]},"initial":["draft"],"reports":[{"action":"run_g5_gate","observation":"gated","state":"gated"},{"action":"retry_without_repair","observation":"rejected","state":"rejected"},{"action":"run_g5_gate","observation":"rejected","state":"rejected"},{"action":"issue_receipt","observation":"verified","state":"verified"}],"resolutions":[],"schema":"wdp-finite-belief-model-v1","states":["draft","gated","rejected","verified"],"targets":[["verified"]],"task_id":"pilot-g5-unrepaired-rollout","transitions":[{"action":"run_g5_gate","state":"draft","successors":["gated","rejected"]},{"action":"issue_receipt","state":"gated","successors":["verified"]},{"action":"retry_without_repair","state":"rejected","successors":["rejected"]}],"valid_resolutions":{"draft":[],"gated":[],"rejected":[],"verified":[]}}')
    loss_cert = json.loads('{"assumptions":["A1","A2","A4","A5","A6"],"authorization":{"effect":"None"},"closure":[{"action":"run_g5_gate","belief":["draft"],"successor":["rejected"]},{"action":"retry_without_repair","belief":["rejected"],"successor":["rejected"]}],"initial":["draft"],"kind":"LOSS","losing":[["draft"],["rejected"]],"model_digest":"89958b1edfef83c8a78d8eafe79cf6c5450e713e9a6892786a2b647754e7a431","optimality_requested":false,"ranks":[],"resolutions":[],"schema":"wdp-progress-certificate-v1","stalled":[],"strategy":[],"task_id":"pilot-g5-unrepaired-rollout","values":[],"winning":[]}')
    rep_losing = governor.report(
        losing_arena, loss_cert, PILOT_ARENA_USABLE_BUDGET, task_admits_impossibility=False
    )
    assert isinstance(rep_losing, GovernorReport)

    decisions = {
        "at_usable_budget": operator_decision_for_label(rep_resolved.label),
        "at_tight_budget": operator_decision_for_label(rep_exhausted.label),
        "on_losing_rollout": operator_decision_for_label(rep_losing.label),
    }
    arena_state_count = len(arena["states"])
    kill_exceeds_practical_size = arena_state_count > 64
    kill_labels_do_not_change_decision = len(set(decisions.values())) < 3
    kill_loss_cert_unavailable = not (
        rep_losing.check is not None
        and rep_losing.check.accepted
        and rep_losing.check.claim == "LOSS"
        and rep_losing.label is TerminationLabel.LOSING_IN_DECLARED_ARENA
    )

    return {
        "goal_id": "PROD-P1-KILL",
        "arena_state_count": arena_state_count,
        "labels": {
            "at_usable_budget": rep_resolved.label.value,
            "at_tight_budget": rep_exhausted.label.value,
            "on_losing_rollout": rep_losing.label.value,
        },
        "operator_decisions": decisions,
        "loss_certificate_verified": not kill_loss_cert_unavailable,
        "kill_exceeds_practical_size": kill_exceeds_practical_size,
        "kill_labels_do_not_change_decision": kill_labels_do_not_change_decision,
        "kill_loss_cert_unavailable": kill_loss_cert_unavailable,
        "any_kill_condition_holds": (
            kill_exceeds_practical_size
            or kill_labels_do_not_change_decision
            or kill_loss_cert_unavailable
        ),
        "authority_effect": rep_resolved.authority_effect,
    }


_check_governor_protocol: AbstentionGovernor = WdpAbstentionGovernor()
