"""Record submitted stage metadata in the existing ``stages.ndjson`` tape.

This receipt-only surface does not execute stages, or measure residuals. Recorded completion is not independently verified execution evidence;
the tape is not authenticated or tamper-evident. AuthorityEffect: None.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paperrun.stage_spec import (
    CODE_STAGE_PIPELINE,
    RIP_PAPERS_STAGE_PIPELINE,
    StageSpec,
)


class StageDriverError(ValueError):
    """Illegal stage driver operation."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


_BY_ID: dict[str, StageSpec] = {s.stage_id: s for s in RIP_PAPERS_STAGE_PIPELINE}

_CODE_BY_ID: dict[str, StageSpec] = {s.stage_id: s for s in CODE_STAGE_PIPELINE}


def catalog() -> list[dict[str, Any]]:
    return [s.to_dict() for s in RIP_PAPERS_STAGE_PIPELINE]


def get_stage(stage_id: str) -> StageSpec:
    sid = stage_id.strip()
    if sid in _BY_ID:
        return _BY_ID[sid]
    if sid in _CODE_BY_ID:
        return _CODE_BY_ID[sid]
    known_p = ", ".join(s.stage_id for s in RIP_PAPERS_STAGE_PIPELINE)
    known_c = ", ".join(s.stage_id for s in CODE_STAGE_PIPELINE)
    raise StageDriverError(
        f"unknown stage_id {sid!r}; papers: {known_p}; code: {known_c}"
    )


def get_code_stage(stage_id: str) -> StageSpec:
    sid = stage_id.strip()
    if sid not in _CODE_BY_ID:
        known = ", ".join(s.stage_id for s in CODE_STAGE_PIPELINE)
        raise StageDriverError(f"unknown code stage_id {sid!r}; known: {known}")
    return _CODE_BY_ID[sid]


def next_stage_after(stage_id: str) -> StageSpec | None:
    cur = get_stage(stage_id)
    nxt = cur.order + 1
    pipeline = (
        CODE_STAGE_PIPELINE
        if stage_id.strip() in _CODE_BY_ID
        else RIP_PAPERS_STAGE_PIPELINE
    )
    for s in pipeline:
        if s.order == nxt:
            return s
    return None


def _default_role_for_skill(skill_id: str) -> str:
    """Map stage skill_id to transition role when caller omits actor_role."""
    sid = (skill_id or "").lower()
    if any(x in sid for x in ("improver", "propose", "formalize", "lean4-improver")):
        return "proposer"
    if any(x in sid for x in ("adversary", "evaluate", "referee", "red-team")):
        return "evaluator"
    if "build" in sid or "release" in sid:
        return "evaluator"  # host measurement of package face, not human promote
    return "evaluator"


def _default_event_for_status(status: str, role: str) -> str:
    if status == "STARTED":
        return "measurement" if role == "evaluator" else "candidate_patch"
    if status in ("COMPLETED", "SKIPPED"):
        return "evaluation_receipt" if role == "evaluator" else "candidate_patch"
    if status == "FAILED":
        return "finding" if role == "evaluator" else "candidate_patch"
    return "measurement"


@dataclass
class StageReceipt:
    receipt_id: str
    job_id: str
    stage_id: str
    skill_id: str
    result_token: str
    status: str  # STARTED | COMPLETED | SKIPPED | FAILED
    residual_open_ids: list[str] = field(default_factory=list)
    note: str = ""
    tree_sha256: str = ""
    created_at_utc: str = ""
    authority_effect: str = "None"
    claims_global_green: bool = False
    schema_version: str = "core.research.stage_receipt.v1"
    sprint: str = "sprint-paper-007-0"
    # Transition binding (007-0)
    actor_role: str = ""
    event_type: str = ""
    claims_pass: bool = False
    source_mutated_after_build: bool = False
    post_build: bool = False

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise StageDriverError("authority_effect must be None")
        if self.claims_global_green:
            raise StageDriverError("stage receipts must not claim GlobalGreen")
        if self.status not in ("STARTED", "COMPLETED", "SKIPPED", "FAILED"):
            raise StageDriverError(f"invalid status: {self.status}")
        if not self.created_at_utc:
            self.created_at_utc = _utc_now()
        if not self.actor_role:
            self.actor_role = _default_role_for_skill(self.skill_id)
        if not self.event_type:
            self.event_type = _default_event_for_status(self.status, self.actor_role)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "job_id": self.job_id,
            "stage_id": self.stage_id,
            "skill_id": self.skill_id,
            "result_token": self.result_token,
            "status": self.status,
            "residual_open_ids": list(self.residual_open_ids),
            "note": self.note,
            "tree_sha256": self.tree_sha256,
            "created_at_utc": self.created_at_utc,
            "authority_effect": self.authority_effect,
            "claims_global_green": self.claims_global_green,
            "sprint": self.sprint,
            "actor_role": self.actor_role,
            "event_type": self.event_type,
            "claims_pass": self.claims_pass,
            "source_mutated_after_build": self.source_mutated_after_build,
            "post_build": self.post_build,
        }
        return d

    @classmethod
    def issue(
        cls,
        *,
        job_id: str,
        stage_id: str,
        status: str,
        result_token: str,
        residual_open_ids: list[str] | None = None,
        note: str = "",
        tree_sha256: str = "",
        actor_role: str = "",
        event_type: str = "",
        claims_pass: bool = False,
        source_mutated_after_build: bool = False,
        post_build: bool = False,
    ) -> StageReceipt:
        spec = get_stage(stage_id)
        return cls(
            receipt_id=str(uuid.uuid4()),
            job_id=job_id,
            stage_id=spec.stage_id,
            skill_id=spec.skill_id,
            result_token=result_token.strip() or status,
            status=status,
            residual_open_ids=list(residual_open_ids or []),
            note=note,
            tree_sha256=tree_sha256,
            actor_role=actor_role,
            event_type=event_type,
            claims_pass=claims_pass,
            source_mutated_after_build=source_mutated_after_build,
            post_build=post_build,
        )


class StageDriver:
    """Filesystem receipt tape only; no stage executor side effect."""

    BUILD_STAGE_ID = "stage_5_build_public_object"

    def __init__(self, job_dir: Path | str) -> None:
        self.job_dir = Path(job_dir)
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self.tape_path = self.job_dir / "stages.ndjson"

    def _build_completed(self) -> bool:
        for r in self.list_receipts():
            if r.get("stage_id") == self.BUILD_STAGE_ID and r.get("status") in (
                "COMPLETED",
                "SKIPPED",
            ):
                return True
        return False

    def enforce_rebuild_contract(self, receipt: StageReceipt) -> None:
        """
        Hard law: after a completed public-object build, source mutation without
        a new build stage receipt is refused .
        """
        if not receipt.source_mutated_after_build:
            return
        if not self._build_completed():
            return
        # Mutation after build is only legal as a *new* build stage that rebuilds.
        if receipt.stage_id != self.BUILD_STAGE_ID:
            raise StageDriverError(
                "rebuild required: source mutated after stage_5_build_public_object; "
                "complete a new build stage before further stage receipts"
            )
        if receipt.status not in ("STARTED", "COMPLETED", "FAILED"):
            raise StageDriverError("rebuild stage must be STARTED|COMPLETED|FAILED")

    def enforce_transition(self, receipt: StageReceipt) -> None:
        """Fail-closed role/event gate via PaperRunGraph validator."""
        from paperrun.paper_run_graph import (
            PaperRunGraphError,
            TransitionEvent,
            validate_transition_or_raise,
        )

        carrier = (receipt.tree_sha256 or receipt.job_id or "unknown").strip()
        # A new build stage is the authorized recovery path after mutation.
        if (
            receipt.stage_id == self.BUILD_STAGE_ID
            and receipt.source_mutated_after_build
        ):
            post_build_flag = False
            mutated_flag = False
        else:
            post_build_flag = bool(receipt.post_build or self._build_completed())
            mutated_flag = receipt.source_mutated_after_build
        try:
            validate_transition_or_raise(
                TransitionEvent(
                    role=receipt.actor_role,
                    event_type=receipt.event_type,
                    carrier_hash=carrier,
                    candidate_hash=receipt.tree_sha256 or "",
                    post_build=post_build_flag,
                    source_mutated_after_build=mutated_flag,
                    claims_pass=receipt.claims_pass,
                    authority_effect=receipt.authority_effect,
                )
            )
        except PaperRunGraphError as exc:
            raise StageDriverError(f"transition refused: {exc}") from exc

    def append_receipt(self, receipt: StageReceipt) -> StageReceipt:
        """Apply existing gates and append one receipt, propagating I/O failures.

        The returned object is the submitted receipt, not proof of execution. Existing tape bytes and the v1 record shape are retained.
        """
        if receipt.claims_global_green or receipt.authority_effect != "None":
            raise StageDriverError("refusing non-None authority stage receipt")
        self.enforce_rebuild_contract(receipt)
        self.enforce_transition(receipt)
        with self.tape_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(receipt.to_dict(), sort_keys=True) + "\n")
        return receipt

    def list_receipts(self) -> list[dict[str, Any]]:
        if not self.tape_path.is_file():
            return []
        out: list[dict[str, Any]] = []
        for line in self.tape_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
        return out

    def completed_stage_ids(self) -> set[str]:
        done: set[str] = set()
        for r in self.list_receipts():
            if r.get("status") in ("COMPLETED", "SKIPPED"):
                done.add(str(r.get("stage_id", "")))
        return done

    def pipeline_status(self, *, current_stage_id: str = "") -> dict[str, Any]:
        done = self.completed_stage_ids()
        stages = []
        for s in RIP_PAPERS_STAGE_PIPELINE:
            if s.stage_id in done:
                state = "DONE"
            elif current_stage_id and s.stage_id == current_stage_id:
                state = "ACTIVE"
            else:
                state = "PENDING"
            stages.append({**s.to_dict(), "state": state})
        all_done = all(s["state"] == "DONE" for s in stages)
        return {
            "catalog_version": "rip_papers_v1_binding",
            "stages": stages,
            "completed_count": len(done),
            "total_count": len(RIP_PAPERS_STAGE_PIPELINE),
            "all_stages_done": all_done,
            "current_stage_id": current_stage_id,
            "receipt_count": len(self.list_receipts()),
            "authority_effect": "None",
            "claims_global_green": False,
            "note": (
                "Stage driver records bindings only; it does not execute skill panels "
                "or mint AuthorityEffect. It does not verify "
                "execution or residual measurements."
            ),
        }

    def first_pending(self, *, current_stage_id: str = "") -> StageSpec | None:
        done = self.completed_stage_ids()
        for s in RIP_PAPERS_STAGE_PIPELINE:
            if s.stage_id not in done:
                return s
        return None
