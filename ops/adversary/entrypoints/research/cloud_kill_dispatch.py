"""Cloud-under-kill dispatch for lake/cargo/panel jobs (SCALE-005 S2).

- kill_domain required on every admit
- Cancel path explicit; no auto-resume after kill
- Path escape refused (allowed roots only)
- Fixture/default: records dispatch + cancel without spawning remote workers

AuthorityEffect: None. Not production unattended deploy.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence

AUTHORITY_EFFECT = "None"
SCHEMA_VERSION = "core.oears.cloud_kill_dispatch.v1"
SPRINT = "sprint_ort_oears_scale_005_s2"

JobKind = Literal["lake", "cargo", "panel"]
JobStatus = Literal[
    "ADMITTED",
    "DISPATCHED",
    "RUNNING",
    "COMPLETED",
    "KILLED",
    "COST_KILLED",
    "REFUSED",
]

KILL_DOMAIN_REQUIRED = "required"
DEFAULT_ALLOWED_ROOT_SEGMENTS = (
    "engine/lean4",
    "engine",
    "engine_py",
)

RESIDUAL_NO_AUTO_RESUME = "OEARS-SCALE-005-NO-AUTO-RESUME"
RESIDUAL_NOT_DEPLOYED = "OEARS-SCALE-005-CLOUD-WORKER-NOT-DEPLOYED"


from adversary.domain.research.protocols import (
    CloudJobReceipt,
    CloudJobSpec,
    CloudKillDispatchError,
    CloudKillDispatcherPort,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_posix(path: Path | str) -> str:
    return Path(path).as_posix().replace("\\", "/")


def path_within_allowed_roots(
    work_path: Path | str,
    *,
    repo_root: Optional[Path | str] = None,
    allowed_segments: Sequence[str] = DEFAULT_ALLOWED_ROOT_SEGMENTS,
) -> bool:
    """True if work_path sits under an allowed estate segment (path-escape gate)."""
    posix = _norm_posix(Path(work_path).resolve())
    for seg in allowed_segments:
        norm = seg.replace("\\", "/").strip("/")
        if f"/{norm}/" in f"/{posix}/" or posix.endswith(f"/{norm}"):
            return True
        if norm and norm in posix:
            return True
    if repo_root is not None:
        root = Path(repo_root).resolve()
        try:
            Path(work_path).resolve().relative_to(root)
            # still require segment match inside repo
            rel = Path(work_path).resolve().relative_to(root).as_posix()
            for seg in allowed_segments:
                if rel == seg or rel.startswith(seg.rstrip("/") + "/"):
                    return True
        except ValueError:
            return False
    return False


class CloudKillDispatcher:
    """In-memory cloud-under-kill dispatcher (fixture-safe)."""

    def __init__(
        self,
        *,
        repo_root: Optional[Path | str] = None,
        allowed_segments: Sequence[str] = DEFAULT_ALLOWED_ROOT_SEGMENTS,
    ) -> None:
        self._repo_root = Path(repo_root).resolve() if repo_root else None
        self._allowed = tuple(allowed_segments)
        self._jobs: Dict[str, CloudJobReceipt] = {}

    def admit_and_dispatch(self, spec: CloudJobSpec) -> CloudJobReceipt:
        """Admit under kill domain and record dispatch (does not spawn workers)."""
        if not path_within_allowed_roots(
            spec.work_path,
            repo_root=self._repo_root,
            allowed_segments=self._allowed,
        ):
            raise CloudKillDispatchError(
                f"path escape refused for work_path={spec.work_path!r}; "
                f"allowed={list(self._allowed)}"
            )

        job_id = str(uuid.uuid4())
        rec = CloudJobReceipt(
            job_id=job_id,
            kind=spec.kind,
            work_path=spec.work_path,
            command=spec.command,
            status="DISPATCHED",
            kill_domain=spec.kill_domain,
            kill_handle=f"kill:{job_id}",
            auto_resume=False,
            resumed_after_kill=False,
            budget_microusd=spec.budget_microusd,
            cost_spent_microusd=0,
            deploys_worker=False,
            residual_open_ids=[
                RESIDUAL_NO_AUTO_RESUME,
                RESIDUAL_NOT_DEPLOYED,
            ],
            notes=[
                "Fixture dispatch: receipt only; no remote worker spawn",
                f"max_wall_seconds={spec.max_wall_seconds}",
            ],
        )
        self._jobs[job_id] = rec
        return rec

    def kill(self, job_id: str, *, reason: str = "operator_kill") -> CloudJobReceipt:
        """Cancel job via kill handle. Does not auto-resume."""
        rec = self._jobs.get(job_id)
        if rec is None:
            raise CloudKillDispatchError(f"unknown job_id {job_id!r}")
        if rec.status in ("KILLED", "COST_KILLED"):
            return rec
        rec.status = "KILLED"
        rec.updated_at_utc = _utc_now()
        rec.notes.append(f"killed:{reason}")
        rec.resumed_after_kill = False
        return rec

    def cost_kill(self, job_id: str) -> CloudJobReceipt:
        """Budget/cost kill terminal (valid; not a hidden failure)."""
        rec = self._jobs.get(job_id)
        if rec is None:
            raise CloudKillDispatchError(f"unknown job_id {job_id!r}")
        rec.status = "COST_KILLED"
        rec.updated_at_utc = _utc_now()
        rec.notes.append("cost_kill: budget ceiling")
        rec.resumed_after_kill = False
        return rec

    def refuse_auto_resume(self, job_id: str) -> None:
        """Hard refuse any attempt to resume a killed job automatically."""
        rec = self._jobs.get(job_id)
        if rec is None:
            raise CloudKillDispatchError(f"unknown job_id {job_id!r}")
        if rec.status in ("KILLED", "COST_KILLED"):
            raise CloudKillDispatchError(
                "auto-resume after kill refused — issue a new explicit authorize/dispatch"
            )
        raise CloudKillDispatchError(
            f"refuse_auto_resume only applies to killed jobs; status={rec.status!r}"
        )

    def get(self, job_id: str) -> CloudJobReceipt:
        rec = self._jobs.get(job_id)
        if rec is None:
            raise CloudKillDispatchError(f"unknown job_id {job_id!r}")
        return rec

    def list_jobs(self) -> List[CloudJobReceipt]:
        return list(self._jobs.values())
