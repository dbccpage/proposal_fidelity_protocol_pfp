"""The stage Symbol Game trace packet sink as the Woland SGT port.

A turn is written as one canonical JSON line ``{"session_id", "turn"}`` to the stage
packet file; the returned id is the sink's packet id.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Refusal, Result
from omega_engine_woland.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from omega_engine_woland.domain.specialization import PortName
from omega_engine_woland.stage.infrastructure.default_adapters import InMemorySymbolGamePacketSink

from .probe_support import canonical_bytes, observed, refusal, run_probe

_LOCUS = "omega_engine_woland.infrastructure.estates.stage_sgt"


class StageSgtAdapter:
    estate = EstateName.STAGE
    port = PortName.SGT_EMISSION
    adapter_id = "stage.symbol_game_packet_sink"

    def __init__(self, packet_file: Path) -> None:
        self.packet_file = Path(packet_file)

    def record_turn(self, session_id: str, payload: Mapping[str, Any]) -> Result[str, Refusal]:
        try:
            packet = canonical_bytes({"session_id": session_id, "turn": dict(payload)})
        except (TypeError, ValueError) as exc:
            return Err(refusal("SGT_TURN_INVALID", exc, _LOCUS))
        return InMemorySymbolGamePacketSink(self.packet_file).record_packet(packet)

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            path = Path(scratch_root) / "sgt_packets.jsonl"
            packet = canonical_bytes(
                {"session_id": "connection-probe", "turn": {"authority_effect": "None"}}
            )
            recorded = InMemorySymbolGamePacketSink(path).record_packet(packet)
            if isinstance(recorded, Err):
                return disconnected(self.estate, self.port, self.adapter_id, recorded.error.code)
            raw = path.read_bytes()
            if raw.splitlines() != [packet]:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "packet not read back"
                )
            return observed(
                self.estate, self.port, self.adapter_id, raw, "appended one packet and read it back"
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)


__all__ = ["StageSgtAdapter"]
