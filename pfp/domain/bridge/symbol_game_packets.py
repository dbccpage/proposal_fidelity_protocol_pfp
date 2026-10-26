from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional, Tuple

from ..entities.packet_envelope import PacketEnvelopeV2


class SymbolGamePacketCompiler:
    """Compile root and child PacketEnvelopeV2 values. No dialogue or persistence."""

    @staticmethod
    def compile_text_problem(
        *,
        task_id: str,
        text_content: str,
        packet_family: str = "symbol_game_v1",
        carrier_id: str = "text_claim_carrier_v1",
        step_budget: int = 8,
        constraints: Tuple[str, ...] = ("finite exact carrier", "strict verified descent", "d1*d0=0"),
        protected_boundaries: Tuple[str, ...] = ("claim:phi1", "claim:gamma2"),
    ) -> PacketEnvelopeV2:
        payload = {
            "objective": "Verify claims, extract 1-cochains, and achieve exact coboundary descent",
            "content": text_content,
        }
        return PacketEnvelopeV2(
            task_id=task_id,
            packet_family=packet_family,
            carrier_id=carrier_id,
            initial_state_hash=hashlib.sha256(text_content.encode("utf-8")).hexdigest(),
            payload=payload,
            constraints=constraints,
            protected_boundaries=protected_boundaries,
            step_budget=step_budget,
            authority_effect="None",
        )

    @staticmethod
    def compile_problem_packet(
        task_id: str,
        problem_data: Dict[str, Any],
        packet_family: str = "symbol_game_v1",
        carrier_id: str = "ast_cochain_carrier_v1",
        step_budget: int = 8,
        constraints: Tuple[str, ...] = ("finite exact carrier", "strict verified descent", "d1*d0=0"),
        protected_boundaries: Tuple[str, ...] = ("claim:phi1", "claim:gamma2"),
    ) -> PacketEnvelopeV2:
        content_str = json.dumps(problem_data, sort_keys=True)
        return PacketEnvelopeV2(
            task_id=task_id,
            packet_family=packet_family,
            carrier_id=carrier_id,
            initial_state_hash=hashlib.sha256(content_str.encode("utf-8")).hexdigest(),
            payload=problem_data,
            constraints=constraints,
            protected_boundaries=protected_boundaries,
            step_budget=step_budget,
            authority_effect="None",
        )

    @staticmethod
    def compile_step_packet(
        task_id: str,
        step_index: int,
        candidate: Dict[str, Any],
        score: Any,
        prior_score: Optional[Any] = None,
        parent_event_id: Optional[str] = None,
        packet_family: str = "symbol_game_v1",
        carrier_id: str = "ast_cochain_carrier_v1",
        step_budget: int = 8,
        constraints: Tuple[str, ...] = ("finite exact carrier", "strict verified descent", "d1*d0=0"),
        protected_boundaries: Tuple[str, ...] = ("claim:phi1", "claim:gamma2"),
    ) -> PacketEnvelopeV2:
        payload = {
            "step_index": step_index,
            "candidate": candidate,
            "score": {
                "phi_1": score.phi_1,
                "gamma_2": score.gamma_2,
                "active_count": score.active_count,
                "is_exact": score.is_exact,
            },
            "prior_score": {
                "phi_1": prior_score.phi_1,
                "gamma_2": prior_score.gamma_2,
                "active_count": prior_score.active_count,
            } if prior_score else None,
        }
        content_str = json.dumps(payload, sort_keys=True)
        return PacketEnvelopeV2(
            task_id=f"{task_id}_step_{step_index}",
            packet_family=packet_family,
            carrier_id=carrier_id,
            initial_state_hash=hashlib.sha256(content_str.encode("utf-8")).hexdigest(),
            payload=payload,
            constraints=constraints,
            protected_boundaries=protected_boundaries,
            step_budget=step_budget,
            parent_event_id=parent_event_id,
            authority_effect="None",
        )

    @staticmethod
    def compile_child_packet(
        parent_packet: PacketEnvelopeV2,
        *,
        child_task_id: str,
        refined_payload: Dict[str, Any],
        step_budget: int,
    ) -> PacketEnvelopeV2:
        return PacketEnvelopeV2(
            task_id=child_task_id,
            packet_family=parent_packet.packet_family,
            carrier_id=parent_packet.carrier_id,
            initial_state_hash=parent_packet.initial_state_hash,
            payload=refined_payload,
            constraints=parent_packet.constraints,
            protected_boundaries=parent_packet.protected_boundaries,
            step_budget=step_budget,
            parent_event_id=parent_packet.packet_id,
            authority_effect="None",
        )
