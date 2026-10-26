"""Per-run and master packet JSONL ledgers, written through the run artifact port.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Sequence

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_pfp.domain import PacketEnvelopeV2
from omega_engine_pfp.domain.ports.run_artifact_port import RunArtifactSinkPort

from .symbol_game_models import SymbolGameStepResult

MASTER_PACKET_LEDGER = canonical_intelligence_route("_intelligence/unified_oe_packets.jsonl")


class PacketLedgerWriter:
    """Persist per-run and master packet JSONL ledgers."""

    def write(
        self,
        *,
        artifact_sink: RunArtifactSinkPort,
        run_dir: str,
        timestamp_str: str,
        clean_slug: str,
        task_id: str,
        packet_0: PacketEnvelopeV2,
        step_results: Sequence[SymbolGameStepResult],
    ) -> tuple[str, str]:
        filename = f"{timestamp_str}_packets_{clean_slug}.jsonl"
        records = [
            {
                "run_id": f"{timestamp_str}_{clean_slug}",
                "task_id": task_id,
                "round": 0,
                "kind": "problem_packet_0",
                "packet_id": packet_0.packet_id,
                "carrier_id": packet_0.carrier_id,
                "packet": packet_0.to_dict(),
            }
        ]
        for result in step_results:
            if result.child_packet is not None:
                records.append(
                    {
                        "run_id": f"{timestamp_str}_{clean_slug}",
                        "task_id": task_id,
                        "round": result.step_index,
                        "kind": "child_packet",
                        "packet_id": result.child_packet.packet_id,
                        "carrier_id": result.child_packet.carrier_id,
                        "packet": result.child_packet.to_dict(),
                    }
                )

        lines = self._jsonl_lines(records)
        run_locator = artifact_sink.put_text(
            f"{run_dir.strip('/')}/{filename}", "".join(line + "\n" for line in lines)
        )
        artifact_sink.append_lines(MASTER_PACKET_LEDGER, lines)
        return run_locator, filename

    @staticmethod
    def _jsonl_lines(records: Sequence[Dict[str, Any]]) -> list[str]:
        return [json.dumps(record) for record in records]


__all__ = ["MASTER_PACKET_LEDGER", "PacketLedgerWriter"]
