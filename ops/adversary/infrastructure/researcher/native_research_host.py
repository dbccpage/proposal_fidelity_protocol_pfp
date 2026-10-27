"""The research-loop controller on the native host (``adversary_support`` research operations).

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.researcher.models import LoopSnapshotV1

_LOCUS = "adversary.infrastructure.researcher.native_research_host"
WORKFLOW_RELATIVE = Path(
    "education/documentation/004_oepfp/workflows/research"
)


def default_workflow_dir() -> Path:
    """The research workflow folder of the checkout this module is installed in."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / WORKFLOW_RELATIVE
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"{WORKFLOW_RELATIVE} not found above {here}")


def _snapshot(outcome: Mapping[str, Any]) -> LoopSnapshotV1:
    return LoopSnapshotV1(
        checkpoint=outcome["checkpoint"],
        next_action=outcome["next_action"],
        spent=outcome["spent"],
        terminal=outcome["terminal"],
        output=outcome.get("output") or {},
    )


class NativeResearchLoopHost:
    """Calls the Rust controller; the checkpoint travels whole on every call."""

    def __init__(
        self, workflow_dir: Path | None = None, host: RustSymbolGameHost | None = None
    ) -> None:
        self.workflow_dir = (
            Path(workflow_dir) if workflow_dir is not None else default_workflow_dir()
        )
        self._host = host if host is not None else RustSymbolGameHost()

    def _invoke(self, operation: str, **payload: Any) -> Result[Any, Refusal]:
        response = self._host.invoke_runtime_with_file(
            "adversary_support", {"operation": operation, **payload}, file_action="adversary_support_file"
        )
        if isinstance(response, Err):
            return response
        envelope = response.value
        if not envelope["success"]:
            return Err(Refusal("RESEARCH_NATIVE_DISPATCH_FAILED", str(envelope["error"]), _LOCUS))
        reply = envelope["result"]
        if reply["refusal"] is not None:
            error = reply["refusal"]
            return Err(Refusal(error["code"], error["message"], error.get("locus") or _LOCUS))
        return Ok(reply["outcome"])

    def _snapshot_of(self, operation: str, **payload: Any) -> Result[LoopSnapshotV1, Refusal]:
        reply = self._invoke(operation, **payload)
        if isinstance(reply, Err):
            return reply
        return Ok(_snapshot(reply.value))

    def admit(self, mission: Mapping[str, Any]) -> Result[LoopSnapshotV1, Refusal]:
        return self._snapshot_of("research_admit", mission=dict(mission))

    def status(self, checkpoint: Mapping[str, Any]) -> Result[LoopSnapshotV1, Refusal]:
        return self._snapshot_of("research_next", checkpoint=checkpoint)

    def apply(
        self, checkpoint: Mapping[str, Any], command: Mapping[str, Any]
    ) -> Result[LoopSnapshotV1, Refusal]:
        return self._snapshot_of("research_apply", checkpoint=checkpoint, command=dict(command))

    def events(self, checkpoint: Mapping[str, Any]) -> Result[Sequence[Mapping[str, Any]], Refusal]:
        return self._invoke("research_events", checkpoint=checkpoint)

    def validate_response(self, prompt_id: str, response: Any) -> Result[tuple[str, ...], Refusal]:
        reply = self._invoke(
            "research_response_validate",
            workflow_dir=str(self.workflow_dir),
            prompt_id=prompt_id,
            response=response,
        )
        if isinstance(reply, Err):
            return reply
        return Ok(tuple(f"{v['path']} {v['rule']}" for v in reply.value["violations"]))

    def check_pack(self) -> Result[Mapping[str, Any], Refusal]:
        return self._invoke("research_pack_check", workflow_dir=str(self.workflow_dir))

    def packet_digest(self, prompt_id: str) -> Result[str, Refusal]:
        """sha256 of the packet file as stored; the prompt tree is fixed for the run."""
        path = self.workflow_dir / "prompts" / f"{prompt_id.lower()}.yaml"
        try:
            data = path.read_bytes()
        except OSError as exc:
            return Err(Refusal("RESEARCH_PACKET_UNREADABLE", str(exc), _LOCUS))
        return Ok("sha256:" + hashlib.sha256(data).hexdigest())


__all__ = ["NativeResearchLoopHost", "WORKFLOW_RELATIVE", "default_workflow_dir"]
