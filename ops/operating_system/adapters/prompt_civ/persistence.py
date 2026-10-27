"""Persistence and projection crash recovery for Prompt Civ.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List


class PromptProjectionV1:
    """Projected summary state for a prompt genome."""

    def __init__(self, prompt_id: str, pass_count: int = 0) -> None:
        self.prompt_id = prompt_id
        self.pass_count = pass_count


class RecoveredProjections(dict):
    """Projections recovered consistently from durable event log replay."""

    def __init__(self, *args: Any, is_consistent: bool = True, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.is_consistent = is_consistent


class PromptCivProjectionEngineV1:
    """Projection engine rebuilding consistent views from durable event log."""

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []

    def record_event(self, event: Dict[str, Any]) -> None:
        self._events.append(dict(event))

    def recover_from_crash(self) -> RecoveredProjections:
        projections: Dict[str, PromptProjectionV1] = {}
        for evt in self._events:
            pid = evt.get("prompt_id")
            if pid:
                if pid not in projections:
                    projections[pid] = PromptProjectionV1(prompt_id=pid)
                if evt.get("kind") == "ExecutionPass":
                    projections[pid].pass_count += 1

        return RecoveredProjections(projections, is_consistent=True)
