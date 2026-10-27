"""Save the existing teamwork checkpoint and its native report projections."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from dataclasses import replace

from ..use_cases.teamwork import TeamworkRun, next_action
from .teamwork_reporting import checkpoint_reports


def prepared_saved_turn(action, pending: dict | None):
    """Reuse measured pending bytes only after checking the normal PFP binding."""
    from ..use_cases.teamwork_pfp import prepare_teamwork_turn

    if pending is None:
        return prepare_teamwork_turn(action)
    turn = prepare_teamwork_turn(action, observe=False)
    if (pending.get("action_id") != action.action_id or pending.get("status") != "PREPARED"
            or pending.get("binding") != turn.binding
            or any(pending.get(key) != value for key, value in turn.prompt.to_dict().items())):
        raise ValueError("PENDING_PROMPT_CHANGED: reprepare from the retained state before dispatch")
    return replace(turn, observation_metadata=pending.get("observation_metadata", {}))


def default_state_path(run: TeamworkRun) -> Path:
    from operating_system.adapters.intelligence_custody.ic_routing import intelligence_path
    from operating_system.adapters.intelligence_custody.intelligence_root import resolve_intelligence_repo_root

    root = intelligence_path(resolve_intelligence_repo_root(), "_intelligence/_adversary")
    key = hashlib.sha256(run.run_id.encode("utf-8")).hexdigest()[:24]
    return root / "working" / key / "state.json"


def save_teamwork_state(path: Path, run: TeamworkRun, *, new: bool = False) -> dict:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    reporting_enabled = bool(run.brief and run.brief.density_dimension is not None)
    action = next_action(run) if reporting_enabled else None
    if reporting_enabled and action and action.communication == "pfp":
        from ..use_cases.teamwork_pfp import prepare_teamwork_turn

        try:
            turn = prepare_teamwork_turn(action)
            pending = {"action_id": action.action_id, "status": "PREPARED",
                       **turn.prompt.to_dict(), "binding": turn.binding,
                       "observation_metadata": turn.observation_metadata}
        except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
            pending = {"action_id": action.action_id, "status": "PREPARATION_FAILED", "error": str(exc)}
        run = run.model_copy(update={"pending_prompt": pending})
    elif reporting_enabled:
        run = run.model_copy(update={"pending_prompt": None})
    raw = (run.model_dump_json(indent=2) + "\n").encode("utf-8")
    if new:
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    if not reporting_enabled:
        return {"status": "LEGACY_REPORTING_UNCHANGED", "state_path": str(path)}
    return checkpoint_reports(path, run, finalize=action is None)
