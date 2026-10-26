"""WDP Infrastructure Adapter for P1 Abstention and Impossibility Governor (PROD-P1).

Implements `AbstentionGovernorPort` over `certified_progress` (`model`, `producer`,
`checker`, `observation`, `structural`) and `WdpAbstentionGovernor` /
`WdpReceiptIssuer` (`PROD-KERNEL`, `REV-SMRM-P1-QUOTIENT`).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

from omega_engine_applications.wdp_products.reference.certified_progress import checker as cp_checker
from omega_engine_applications.wdp_products.reference.certified_progress import model as cp_model
from omega_engine_applications.wdp_products.reference.certified_progress import observation as cp_obs
from omega_engine_applications.wdp_products.reference.certified_progress import producer as cp_producer
from omega_engine_applications.wdp_products.reference.certified_progress import structural as cp_structural
from omega_engine_applications.wdp_products.kernel.adapter import (
    WdpReceiptIssuer,
)
from omega_engine_applications.wdp_products.p1_abstention_governor.adapter import (
    WdpAbstentionGovernor,
)
from omega_engine_applications.wdp_products.p1_abstention_governor.contracts import (
    GovernorReport,
)


class WdpAbstentionGovernorAdapter:
    """Binds `certified_progress` and `WdpAbstentionGovernor` to `omega_engine_pfp`."""

    def __init__(self) -> None:
        self._governor = WdpAbstentionGovernor()
        self._issuer = WdpReceiptIssuer()

    def evaluate_arena(
        self,
        raw_graph: Mapping[str, Any],
        initial: str,
        targets: tuple[str, ...],
        budget: str,
        *,
        task_id: str = "pfp-abstention-governor",
        compress_quotient: bool = True,
    ) -> dict[str, Any]:
        model = cp_model.graph_model(
            dict(raw_graph), initial=initial, targets=targets, task_id=task_id
        )
        arena = cp_model.compile_model(model)
        raw_state_count = len(arena.reachable)

        active_model = model
        quotient_verified = False
        quotient_state_count = raw_state_count

        if compress_quotient and raw_state_count > 1:
            target_block = [list(b) for b in arena.reachable if b in arena.targets]
            non_target_block = [list(b) for b in arena.reachable if b not in arena.targets]
            seed = [b for b in (target_block, non_target_block) if b]
            if len(seed) >= 1:
                refinement_out = cp_obs.refine_operation_presentation(model, seed)
                blocks = refinement_out["blocks"]
                table = refinement_out["table"]
                ref_ok = cp_structural.check_refinement(
                    model, seed, refinement_out["refinement"]
                )
                quo_ok = cp_structural.check_quotient(model, blocks, table)
                cong_ok = cp_obs.is_congruence(model, blocks)
                if ref_ok and quo_ok and cong_ok:
                    quotient_verified = True
                    active_model = cp_obs.quotient_model(model, blocks)
                    quotient_state_count = len(cp_model.compile_model(active_model).reachable)

        cert = cp_producer.solve_progress(active_model)["certificate"]
        check_res = cp_checker.check_certificate(active_model, cert)
        report = self._governor.report(
            active_model, cert, budget, task_admits_impossibility=True
        )

        if not isinstance(report, GovernorReport):
            return {
                "certificate_accepted": False,
                "termination_label": "REFUSED",
                "refusal_reason": report.reason,
                "authority_effect": "None",
            }

        initial_value = str(check_res.get("initial_value", "INF"))
        receipt = self._issuer.issue(
            subject=f"prod-p1:{task_id}",
            inputs={
                "task_id": task_id,
                "budget": str(budget),
                "compress_quotient": compress_quotient,
            },
            output={
                "termination_label": report.label.value,
                "initial_value": initial_value,
                "quotient_state_count": quotient_state_count,
            },
            claim_ids=("WDP-CH12-D01", "WDP-CHS-P08"),
        )

        return {
            "certificate_accepted": bool(check_res["accepted"]),
            "termination_label": report.label.value,
            "initial_value": initial_value,
            "budget": str(budget),
            "raw_state_count": raw_state_count,
            "quotient_state_count": quotient_state_count,
            "quotient_verified": quotient_verified,
            "receipt_digest": receipt.receipt_digest,
            "authority_effect": "None",
        }
