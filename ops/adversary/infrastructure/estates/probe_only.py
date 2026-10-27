"""Probe-only connections: the stage runtime and the Symbol Game seat transport.

Neither is called by the base swarm directly; the bout service uses both. Their probes
show that each still answers: the stage scheduler starts a run at the Adversary entry scene,
and Symbol Game's native routing check accepts the configured seat routing table.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from operations.domain.rop.result import Err
from pfp.infrastructure.seat_transport.routing import validate_table
from adversary.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from adversary.domain.specialization import PortName
from adversary.infrastructure.seat_routing_loader import (
    DEFAULT_CONFIG_PATH,
    load_routing,
)
from adversary.stage.domain.packets import WorkPacketV1

from .probe_support import canonical_bytes, observed, run_probe

ENTRY_SCENE = "act1_perception"


class StageRuntimeProbe:
    estate = EstateName.STAGE
    port = PortName.ADVERSARY_RUNTIME
    adapter_id = "stage.deterministic_scheduler"

    def __init__(self, runtime_factory: Callable[..., Any]) -> None:
        self.runtime_factory = runtime_factory

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            runtime = self.runtime_factory(output_dir=Path(scratch_root), fixture_mode=True)
            state = runtime.scheduler.start(
                "connection-probe",
                WorkPacketV1(
                    task_key="connection-probe",
                    scene_id=ENTRY_SCENE,
                    objective="Connection probe.",
                    input_artifact_refs=(),
                    acceptance_criteria=("Start at the entry scene.",),
                    budget_units=1,
                    evaluator_epoch_id="sha256:"
                    + hashlib.sha256(b"connection-probe").hexdigest(),
                ),
            )
            if state.current_scene_id != ENTRY_SCENE:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "run did not start at the entry"
                )
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                canonical_bytes(state.to_dict()),
                f"scheduler started run state {state.state_id}",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)


class SeatTransportProbe:
    estate = EstateName.SYMBOL_GAME
    port = PortName.SEAT_TRANSPORT
    adapter_id = "symbol_game.seat_routing"

    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.config_path = Path(config_path)

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            loaded = load_routing(self.config_path)
            if isinstance(loaded, Err):
                return disconnected(self.estate, self.port, self.adapter_id, loaded.error.code)
            table, config_digest = loaded.value
            checked = validate_table(table)
            if isinstance(checked, Err):
                return disconnected(self.estate, self.port, self.adapter_id, checked.error.code)
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                canonical_bytes({"config_digest": config_digest, "validated": True}),
                f"native routing_validate accepted {self.config_path.name}",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)


__all__ = ["ENTRY_SCENE", "StageRuntimeProbe", "SeatTransportProbe"]
