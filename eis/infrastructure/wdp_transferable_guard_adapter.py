"""Immune-system binding for the P3 transferable guard.

``omega_wdp::rejection_reuse`` and ``omega_wdp::guard_transfer`` are missing.
This adapter raises that refusal and does not report a successful transfer.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping, NoReturn

from omega_engine_applications.wdp_products.p3_guard_transfer.adapter import (
    GUARD_TRANSFER_OWNER,
)
from omega_engine_epistemic_immune_system.use_cases.transferable_guard_library import (
    GuardTransferEvaluationRequest,
    GuardTransferRefusal,
)

REJECTION_REUSE_OWNER = "omega_wdp::rejection_reuse"


class WdpTransferableGuardAdapter:
    """Binds the missing guard owners to epistemic_immune_system without a paper import."""

    def evaluate_transfer(self, request: GuardTransferEvaluationRequest) -> Mapping[str, Any]:
        self._refuse(request)

    def _refuse(self, request: GuardTransferEvaluationRequest) -> NoReturn:
        if type(request.task_id) is not int or type(request.level) is not int:
            raise GuardTransferRefusal(
                "invalid_input",
                "task_id and level must be ints; authority_effect=None",
            )
        raise GuardTransferRefusal(
            "missing_native_owner",
            (
                f"missing owner {REJECTION_REUSE_OWNER} and {GUARD_TRANSFER_OWNER}; "
                "authority_effect=None"
            ),
        )
