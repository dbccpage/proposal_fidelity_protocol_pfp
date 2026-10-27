"""Prompt lifecycle DTO adapter over the native civilization kernel."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, replace
from fractions import Fraction
from typing import Any

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err

from ..domain.elenchus import ElenchusResult, SocraticElenchusBureau
from ..domain.models import (
    CivilizationPrompt,
    CivilizationState,
    CustodyTier,
    PopulationTier,
    PromotionDecision,
    UnauthorizedAdmissionError,
)
from ..use_cases.custody import PromptCustodyLedgerV1, PromptReviewReceiptV1


class PromptCivilizationController:
    """Keep Python DTOs while Rust executes interrogation and state transitions."""

    def __init__(
        self, state: CivilizationState | None = None, *,
        custody_ledger: PromptCustodyLedgerV1 | None = None,
    ) -> None:
        self.state = state or CivilizationState()
        self.elenchus = SocraticElenchusBureau()
        self.custody_ledger = custody_ledger

    def _restore(self, records: dict[str, Any]) -> None:
        self.state.prompts.clear()
        for key, wire in records.items():
            self.state.prompts[key] = CivilizationPrompt(
                **{
                    **wire,
                    "tier": PopulationTier(wire["tier"]),
                    "pagerank_score": Fraction(wire["pagerank_score"]),
                }
            )

    def _invoke(self, operation: str, prompt_id: str, **kwargs: Any) -> Any:
        records = {
            key: {
                **asdict(prompt),
                "tier": prompt.tier.value,
                "pagerank_score": str(prompt.pagerank_score),
            }
            for key, prompt in self.state.prompts.items()
        }
        result = RustSymbolGameHost().invoke_runtime(
            "prompt_civilization",
            {"operation": operation, "prompt_id": prompt_id, "state": records, **kwargs},
        )
        if isinstance(result, Err):
            raise RuntimeError(f"{result.error.code}: {result.error.message}")
        if not result.value["success"]:
            raise RuntimeError(str(result.value["error"]))
        wire = result.value["result"]
        refusal = wire["refusal"]
        if refusal is not None:
            if refusal.get("state") is not None:
                self._restore(refusal["state"])
            error = {
                "UNAUTHORIZED_ADMISSION": UnauthorizedAdmissionError,
                "PROMPT_NOT_FOUND": KeyError,
            }.get(refusal["code"], ValueError)
            raise error(refusal["message"])
        self._restore(wire["outcome"]["state"])
        return wire["outcome"]["value"]

    @staticmethod
    def _decision(wire: dict[str, Any]) -> PromotionDecision:
        return PromotionDecision(
            **{
                **wire,
                "from_tier": PopulationTier(wire["from_tier"]),
                "to_tier": PopulationTier(wire["to_tier"]),
            }
        )

    def process_wild_inbound(self, prompt_id: str, content: str) -> ElenchusResult:
        wire = self._invoke("process_wild_inbound", prompt_id, content=content)
        return ElenchusResult(
            **{
                **wire,
                "fitness_score": Fraction(wire["fitness_score"]),
                "prime_rules_checked": tuple(wire["prime_rules_checked"]),
            }
        )

    def ingest_prompt(self, prompt_id: str, content: str) -> dict[str, Any]:
        wire = self._invoke("ingest_prompt", prompt_id, content=content)
        wire["decision"] = self._decision(wire["decision"])
        return wire

    def promote_candidate(self, prompt_id: str) -> PromotionDecision:
        return self._decision(self._invoke("promote_candidate", prompt_id))

    def promote_reviewed(self, prompt_id: str) -> PromotionDecision:
        return self._decision(self._invoke("promote_reviewed", prompt_id))

    def promote_admitted(
        self, prompt_id: str, operator_sig: str | None = None, *,
        review_receipt: PromptReviewReceiptV1 | None = None, scope: str | None = None,
    ) -> PromotionDecision:
        """Project admission only after the host-bound ledger authenticates it."""
        del operator_sig  # A token-shaped string cannot authorize this route.
        ledger = self.custody_ledger
        if ledger is None or review_receipt is None:
            raise UnauthorizedAdmissionError("EXTERNAL_REVIEW_NOT_AUTHENTICATED")
        if review_receipt.outcome is not CustodyTier.ADMITTED:
            raise ValueError("ADMISSION_DECISION_REQUIRED")
        if not scope or scope not in review_receipt.scope:
            raise PermissionError("REFUSE_SCOPE_ESCALATION")
        prompt = self.state.prompts[prompt_id]
        genome = ledger.genome(prompt_id)
        content_digest = hashlib.sha256(prompt.content.encode("utf-8")).hexdigest()
        # This DTO contains one complete prompt, not a composite source tree.
        if (
            len(genome.source_packet_refs) != 1
            or genome.source_packet_refs[0].get("sha256", "").removeprefix("sha256:") != content_digest
        ):
            raise ValueError("PROMPT_BYTES_MISMATCH")
        ledger.apply(genome, review_receipt)
        approved = ledger.approved(genome, scope)
        self.state.prompts[prompt_id] = replace(
            prompt, tier=PopulationTier.ADMITTED,
            operator_signature=review_receipt.external_receipt, authority_effect="None",
        )
        return PromotionDecision(
            prompt_id, prompt.tier, PopulationTier.ADMITTED, True, "ADMITTED",
            f"Authenticated custody decision {approved.decision_id}; scope {scope}",
        )

    def authorize_admission(
        self, prompt_id: str, operator_signature: str | None = None, *,
        review_receipt: PromptReviewReceiptV1 | None = None, scope: str | None = None,
    ) -> dict[str, Any]:
        decision = self.promote_admitted(
            prompt_id, operator_signature, review_receipt=review_receipt, scope=scope,
        )
        return {
            "is_admitted": decision.is_admitted, "status": decision.status,
            "prompt": {"prompt_id": prompt_id, "tier": decision.to_tier.value},
            "authority_effect": "None",
        }


__all__ = ["PromptCivilizationController"]
