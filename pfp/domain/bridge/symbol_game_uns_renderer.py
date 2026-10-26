from __future__ import annotations

import json
from typing import Any, Dict, Sequence

from omega_engine_pfp.domain import PacketEnvelopeV2

from .sbe import SBEAnalyzer
from .symbol_game_models import SymbolGameStepResult


class UNSRenderer:
    """Pure-ish Markdown renderer: input receipts -> UNS text."""

    def __init__(self, sbe_analyzer: SBEAnalyzer):
        self.sbe_analyzer = sbe_analyzer

    def render(
        self,
        *,
        task_id: str,
        packet_0: PacketEnvelopeV2,
        step_results: Sequence[SymbolGameStepResult],
        terminal_status: str,
        evidence_sha256: str,
        timestamp_str: str,
        antibody_ids: Sequence[str],
        session_sbe: Any,
        packets_filename: str,
        packets_path: str,
    ) -> tuple[str, Dict[str, Any]]:
        title_str = self._packet_title(packet_0)
        lines: list[str] = [
            f"# Unified Narrative Script (UNS): {task_id}",
            "",
            f"- **Run ID:** `{task_id}`",
            f"- **Timestamp:** `{timestamp_str}`",
            f"- **Initial Packet ID:** `{packet_0.packet_id}`",
            f"- **Carrier ID:** `{packet_0.carrier_id}`",
            f"- **Final Terminal Status:** `{terminal_status}`",
            f"- **Evidence SHA-256:** `{evidence_sha256}`",
            f"- **Antibodies Farmed:** `{len(antibody_ids)}` ({', '.join(antibody_ids) if antibody_ids else 'None'})",
            f"- **SBE Session Purity $\\text{{Tr}}(\\rho^2)$:** `{session_sbe.purity:.6f}`",
            f"- **SBE Von Neumann Entropy $S(\\rho)$:** `{session_sbe.entropy_bits:.4f}` bits",
            f"- **Packets Ledger:** Stored in `{packets_filename}` and `_ic/nara/legacy/unified_oe_packets.jsonl`",
            "- **AuthorityEffect:** `None`",
            "",
            "---",
            "",
            "## 1. Problem Packet 0 Specification",
            "",
            f"- **Task ID:** `{packet_0.task_id}`",
        ]
        if title_str:
            lines.append(f"- **Title / Objective:** {title_str}")
        lines.extend(
            [
                f"- **Packet ID:** `{packet_0.packet_id}`",
                f"- **Carrier ID:** `{packet_0.carrier_id}`",
                f"- **Initial State Hash:** `{packet_0.initial_state_hash}`",
                f"- **Constraints:** `{', '.join(packet_0.constraints)}`",
                f"- **Protected Boundaries:** `{', '.join(packet_0.protected_boundaries)}`",
                f"- **Step Budget:** `{packet_0.step_budget}`",
                f"- **Full Packet Envelope:** Extracted to companion JSONL ledger (`{packets_filename}`).",
                "",
                "---",
                "",
                "## 2. Multi-Round Symbol Game & Enacted Character Debate",
                "",
            ]
        )

        for result in step_results:
            round_sbe = self.sbe_analyzer.analyze_dialogue_ensemble(
                [beat.dialogue for beat in result.character_debates]
            )
            score = result.obstruction_score
            lines.extend(
                [
                    f"### Round {result.step_index}: Packet `{result.packet.task_id}`",
                    "",
                    f"- **Host Obstruction Score:** $\\Phi_1 = {score.phi_1:.3f}$, $\\gamma_2 = {score.gamma_2:.3f}$, Active Count: `{score.active_count}`",
                    f"- **Strict Descent Verified:** `{result.strict_descent_passed}`",
                    f"- **Action Taken:** `{result.action_taken}`",
                    f"- **SBE Quantum Density:** Purity=`{round_sbe.purity:.5f}`, Entropy=`{round_sbe.entropy_bits:.4f}` bits, $L_1$ Coherence=`{round_sbe.l1_coherence:.4f}`, Non-zero Eigenvalues=`{round_sbe.nonzero_eigenvalues}`",
                    "",
                    f"#### Enacted Dialogue & Cognitive Auditing (Round {result.step_index})",
                    "",
                ]
            )
            for index, beat in enumerate(result.character_debates, start=1):
                lines.extend(
                    [
                        f"##### Round {result.step_index} Beat {index}: {beat.speaker} ({beat.operator_tag})",
                        "",
                        beat.dialogue,
                        "",
                    ]
                )
            if result.child_packet:
                lines.extend(
                    [
                        f"#### Child Packet Emitted (Round {result.step_index})",
                        "",
                        f"- **Child Task ID:** `{result.child_packet.task_id}`",
                        f"- **Child Packet ID:** `{result.child_packet.packet_id}`",
                        f"- **Parent Event ID:** `{result.child_packet.parent_event_id}`",
                        f"- **Step Budget:** `{result.child_packet.step_budget}`",
                        f"- **Full Packet Envelope:** Extracted to companion JSONL ledger (`{packets_filename}`).",
                        "",
                    ]
                )
            lines.extend(["---", ""])

        receipt = {
            "task_id": task_id,
            "terminal_status": terminal_status,
            "evidence_sha256": evidence_sha256,
            "rounds_completed": len(step_results),
            "antibodies_mined": list(antibody_ids),
            "sbe": session_sbe.to_dict(),
            "packets_jsonl_path": str(packets_path),
            "authority_effect": "None",
            "licensing_token": (
                "proposal:residual_admissible_transition_token:authority_effect_none"
                if terminal_status == "PASS_TO_MASTER"
                else None
            ),
        }
        lines.extend(
            [
                "## 3. Terminal Execution Receipt & SBE Quantum Density Report",
                "",
                "```json",
                json.dumps(receipt, indent=2),
                "```",
                "",
            ]
        )
        return "\n".join(lines), receipt

    @staticmethod
    def _packet_title(packet: PacketEnvelopeV2) -> str:
        payload = packet.payload
        if isinstance(payload, dict):
            return payload.get("title") or payload.get("objective") or ""
        if hasattr(payload, "raw") and isinstance(payload.raw, dict):
            return payload.raw.get("title") or payload.raw.get("objective") or ""
        return ""
