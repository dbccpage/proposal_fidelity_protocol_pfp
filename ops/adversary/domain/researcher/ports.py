"""Ports of the research loop: the native controller, run custody and model dispatch.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from operations.domain.rop.result import Refusal, Result

from .models import DispatchOutcomeV1, LoopSnapshotV1


class ResearchLoopHostPort(Protocol):
    """The Rust controller. Every call re-verifies the checkpoint it is given."""

    def admit(self, mission: Mapping[str, Any]) -> Result[LoopSnapshotV1, Refusal]: ...

    def status(self, checkpoint: Mapping[str, Any]) -> Result[LoopSnapshotV1, Refusal]: ...

    def apply(
        self, checkpoint: Mapping[str, Any], command: Mapping[str, Any]
    ) -> Result[LoopSnapshotV1, Refusal]: ...

    def events(
        self, checkpoint: Mapping[str, Any]
    ) -> Result[Sequence[Mapping[str, Any]], Refusal]: ...

    def validate_response(
        self, prompt_id: str, response: Any
    ) -> Result[tuple[str, ...], Refusal]: ...

    def check_pack(self) -> Result[Mapping[str, Any], Refusal]: ...

    def packet_digest(self, prompt_id: str) -> Result[str, Refusal]: ...


class RunCustodyPort(Protocol):
    """One run folder. Raw responses are written once, before they are parsed."""

    def create(
        self, run_id: str, mission: Mapping[str, Any], snapshot: LoopSnapshotV1
    ) -> Result[str, Refusal]: ...

    def load(self, run_id: str) -> Result[Mapping[str, Any], Refusal]: ...

    def save(
        self, run_id: str, expected_state_sha256: str, snapshot: LoopSnapshotV1
    ) -> Result[str, Refusal]: ...

    def write_raw(
        self, run_id: str, round_id: int, occurrence_id: str, raw: bytes
    ) -> Result[str, Refusal]: ...

    def raw_dir(self, run_id: str, round_id: int) -> str: ...

    def append(
        self, run_id: str, ledger: str, record: Mapping[str, Any]
    ) -> Result[None, Refusal]: ...

    def write_bundle(
        self, run_id: str, files: Mapping[str, Any]
    ) -> Result[tuple[str, ...], Refusal]: ...


class ModelDispatchPort(Protocol):
    """A Symbol Game transport that sends one rendered request under a cost ceiling."""

    def send(
        self,
        request: Mapping[str, Any],
        *,
        raw_dir: str,
        raw_name: str,
        ceiling_microusd: int,
    ) -> Result[DispatchOutcomeV1, Refusal]: ...


__all__ = ["ModelDispatchPort", "ResearchLoopHostPort", "RunCustodyPort"]
