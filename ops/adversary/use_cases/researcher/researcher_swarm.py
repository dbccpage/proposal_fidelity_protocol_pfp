"""The research loop as a Adversary specialisation (WF_RESEARCH_PFP).

The Rust controller owns every decision: admission, budget, order, freezing, review
binding and the disposition. This use case carries its checkpoint between calls, keeps
the run folder, and turns a stage response into a controller command:

1. the raw bytes are written to the run folder before anything reads them;
2. the response is parsed and checked against the packet's response schema on the host;
3. a parse failure or schema violation is recorded as a failed, charged attempt;
4. an accepted response is recorded; stage 4 freezes the candidate, and stages 6 and 7
   are bound to the candidate digest their rows name. A critic with no rows names no
   other bytes, so it is bound to the candidate frozen when it was dispatched;
5. a record the controller refuses is recorded again as a failed attempt, so a charged
   occurrence is never left unrecorded.

Responses arrive two ways and meet the same path: an IDE agent writes a file
(``submit``), or a Symbol Game transport calls the provider (``dispatch``).

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, ClassVar

from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.researcher.models import (
    Dispatch,
    LoopSnapshotV1,
    SubmissionV1,
)
from adversary.domain.researcher.ports import (
    ModelDispatchPort,
    ResearchLoopHostPort,
    RunCustodyPort,
)
from adversary.domain.specialization import PortName, SwarmSpecializationV1
from adversary.use_cases.base_swarm.specializations import RESEARCHER_PROFILE_V01
from adversary.use_cases.base_swarm.adversary_swarm import (
    AdversarySwarm,
    bind_adversary,
)

_LOCUS = "adversary.use_cases.researcher.researcher_swarm"
PACKET_IDS: Mapping[int, str] = {stage: f"P_RESEARCH_{stage:02d}" for stage in range(1, 9)}
_CRITIC_SECTIONS: Mapping[int, str] = {6: "objections", 7: "countermodels"}


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _refused(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code, message, _LOCUS))


def _critic_binding(response: Mapping[str, Any], stage: int, frozen: str | None) -> str | None:
    """The one candidate digest every row of a critic response names.

    With no rows the critic objected to nothing and named no bytes; it is bound to
    ``frozen``, the candidate its packet carried. Rows naming different digests bind to
    nothing, which the controller refuses as a stale critic.
    """
    rows = [
        row
        for section in response.get("sections", [])
        if isinstance(section, Mapping) and section.get("name") == _CRITIC_SECTIONS[stage]
        for row in section.get("rows", [])
        if isinstance(row, Mapping)
    ]
    if not rows:
        return frozen
    named = {row.get("candidate_sha256") for row in rows}
    return named.pop() if len(named) == 1 and None not in named else None


def _no_constants(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


class ResearchLoopUseCase:
    """Drives one research run through the Rust controller and keeps its run folder."""

    SPECIALIZATION: ClassVar[SwarmSpecializationV1] = RESEARCHER_PROFILE_V01

    def __init__(
        self,
        *,
        adversary: AdversarySwarm,
        host: ResearchLoopHostPort,
        custody: RunCustodyPort,
        dispatcher: ModelDispatchPort | None = None,
    ) -> None:
        self.adversary = bind_adversary(adversary, self.SPECIALIZATION)
        self._host = host
        self._custody = custody
        self._dispatcher = dispatcher

    # -- run lifecycle -------------------------------------------------------------------

    def start(self, mission: Mapping[str, Any]) -> Result[LoopSnapshotV1, Refusal]:
        admitted = self._host.admit(mission)
        if isinstance(admitted, Err):
            return admitted
        created = self._custody.create(admitted.value.run_id, mission, admitted.value)
        if isinstance(created, Err):
            return created
        return admitted

    def status(self, run_id: str) -> Result[LoopSnapshotV1, Refusal]:
        return self._apply(run_id, None)

    def begin_round(
        self, run_id: str, source_snapshot_sha256: str
    ) -> Result[LoopSnapshotV1, Refusal]:
        return self._apply(
            run_id, {"command": "begin_round", "source_snapshot_sha256": source_snapshot_sha256}
        )

    def evaluate(
        self, run_id: str, checks: list[Mapping[str, Any]], checker_policy_sha256: str
    ) -> Result[LoopSnapshotV1, Refusal]:
        return self._apply(
            run_id,
            {
                "command": "host_evaluate",
                "checks": checks,
                "checker_policy_sha256": checker_policy_sha256,
            },
        )

    def route(self, run_id: str, observation: Mapping[str, Any]) -> Result[LoopSnapshotV1, Refusal]:
        routed = self._apply(run_id, {"command": "route", "observation": dict(observation)})
        if isinstance(routed, Err) or routed.value.terminal is None:
            return routed
        return self._finish(run_id, routed.value, list(observation.get("residual_ids", [])))

    def halt(self, run_id: str, disposition: str, reason: str) -> Result[LoopSnapshotV1, Refusal]:
        halted = self._apply(
            run_id, {"command": "halt", "disposition": disposition, "reason": reason}
        )
        if isinstance(halted, Err):
            return halted
        return self._finish(run_id, halted.value, [])

    # -- responses -----------------------------------------------------------------------

    def submit(
        self, run_id: str, *, stage: int, attempt: int, raw: bytes
    ) -> Result[SubmissionV1, Refusal]:
        """Record a response an IDE agent wrote. The host did not meter it: cost 0, one call."""
        located = self._occurrence(run_id, stage, attempt)
        if isinstance(located, Err):
            return located
        round_id, occurrence_id = located.value
        raw_path = self._custody.write_raw(run_id, round_id, occurrence_id, raw)
        if isinstance(raw_path, Err):
            return raw_path
        reserved = self._reserve(run_id, stage, occurrence_id, "ide_agent", 0, 0)
        if isinstance(reserved, Err):
            return reserved
        settled = self._apply(
            run_id,
            {
                "command": "settle",
                "idempotency_key": reserved.value[0],
                "tokens": 0,
                "cost_microusd": 0,
            },
        )
        if isinstance(settled, Err):
            return settled
        return self._record(run_id, stage, occurrence_id, raw, raw_path.value)

    def dispatch(
        self,
        run_id: str,
        *,
        stage: int,
        attempt: int,
        request: Mapping[str, Any],
        ceiling_microusd: int,
        token_bound: int,
    ) -> Result[SubmissionV1, Refusal]:
        """Send a rendered request through the Symbol Game transport and record the reply."""
        if self._dispatcher is None:
            return _refused("MODEL_DISPATCH_UNBOUND", "this run has no bound model transport")
        located = self._occurrence(run_id, stage, attempt)
        if isinstance(located, Err):
            return located
        round_id, occurrence_id = located.value
        reserved = self._reserve(
            run_id, stage, occurrence_id, "model", token_bound, ceiling_microusd
        )
        if isinstance(reserved, Err):
            return reserved
        key, snapshot = reserved.value
        # A repeated reserve returns the existing key whatever its state; only a pending
        # reservation may be sent, or a retry would pay for a second call.
        held = snapshot.checkpoint["state"]["ledger"]["reservations"].get(key, {}).get("state")
        if held != "PENDING":
            return _refused(
                "OCCURRENCE_ALREADY_DISPATCHED",
                f"{occurrence_id} was already dispatched (reservation {held}); use a new attempt",
            )
        sent = self._dispatcher.send(
            request,
            raw_dir=self._custody.raw_dir(run_id, round_id),
            raw_name=f"{occurrence_id}.response.json",
            ceiling_microusd=ceiling_microusd,
        )
        if isinstance(sent, Err):
            # The transport may have reached the provider: keep the reservation charged.
            return self._close(run_id, "reconcile", key, sent.error)
        outcome = sent.value
        if outcome.dispatch is not Dispatch.REPLIED:
            refusal = outcome.refusal or {}
            error = Refusal(
                str(refusal.get("code", outcome.dispatch.value)),
                # A refusal must carry a message; an empty one would raise, not close.
                str(refusal.get("message") or f"the request ended {outcome.dispatch.value}"),
                _LOCUS,
            )
            closing = "release" if outcome.dispatch is Dispatch.NOT_SENT else "reconcile"
            return self._close(run_id, closing, key, error)
        usage = outcome.usage or {}
        tokens = int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
        cost = (
            outcome.metered_cost_microusd
            if outcome.metered_cost_microusd is not None
            else ceiling_microusd
        )
        settled = self._apply(
            run_id,
            {"command": "settle", "idempotency_key": key, "tokens": tokens, "cost_microusd": cost},
        )
        if isinstance(settled, Err):
            return settled
        # The persisted reply is the custody record; the extracted text is what is parsed.
        text = None if outcome.text is None else outcome.text.encode("utf-8")
        return self._record(
            run_id,
            stage,
            occurrence_id,
            text,
            str(outcome.raw_path),
            raw_sha256=outcome.raw_sha256,
            reply_refusal=outcome.refusal,
        )

    # -- internals -----------------------------------------------------------------------

    def _apply(
        self, run_id: str, command: Mapping[str, Any] | None
    ) -> Result[LoopSnapshotV1, Refusal]:
        stored = self._custody.load(run_id)
        if isinstance(stored, Err):
            return stored
        checkpoint = stored.value["checkpoint"]
        if command is None:
            return self._host.status(checkpoint)
        applied = self._host.apply(checkpoint, command)
        if isinstance(applied, Err):
            return applied
        saved = self._custody.save(run_id, checkpoint["state_sha256"], applied.value)
        if isinstance(saved, Err):
            return saved
        return applied

    def _close(self, run_id: str, command: str, key: str, error: Refusal) -> Err[Refusal]:
        """Close a reservation whose call produced no reply, then report why."""
        closed = self._apply(run_id, {"command": command, "idempotency_key": key})
        if isinstance(closed, Err):
            return Err(
                Refusal(
                    "RESERVATION_LEFT_OPEN",
                    f"{error.code}: {error.message}; {command} failed with {closed.error.code}",
                    _LOCUS,
                )
            )
        return Err(error)

    def _occurrence(
        self, run_id: str, stage: int, attempt: int
    ) -> Result[tuple[int, str], Refusal]:
        if not isinstance(stage, int) or isinstance(stage, bool):
            return _refused("STAGE_INVALID", "stage is an integer")
        if stage not in PACKET_IDS or stage == 5:
            return _refused("STAGE5_HOST_ONLY", f"stage {stage} has no model response")
        if not (isinstance(attempt, int) and not isinstance(attempt, bool) and attempt >= 1):
            return _refused("ATTEMPT_INVALID", "attempt is a positive integer")
        current = self.status(run_id)
        if isinstance(current, Err):
            return current
        action = current.value.next_action
        if action.get("action") != "DISPATCH" or action.get("stage") != stage:
            return _refused("STAGE_ORDER", f"the controller's next action is {dict(action)}")
        round_id = int(action["round"])
        return Ok((round_id, f"{run_id}.r{round_id}.s{stage}.a{attempt}"))

    def _reserve(
        self, run_id: str, stage: int, occurrence_id: str, executor: str, tokens: int, cost: int
    ) -> Result[tuple[str, LoopSnapshotV1], Refusal]:
        packet = self._host.packet_digest(PACKET_IDS[stage])
        if isinstance(packet, Err):
            return packet
        reserved = self._apply(
            run_id,
            {
                "command": "reserve",
                "stage": stage,
                "occurrence_id": occurrence_id,
                "packet_sha256": packet.value,
                "executor": executor,
                "tokens": tokens,
                "cost_microusd": cost,
            },
        )
        if isinstance(reserved, Err):
            return reserved
        return Ok((str(reserved.value.output["idempotency_key"]), reserved.value))

    def _record(
        self,
        run_id: str,
        stage: int,
        occurrence_id: str,
        raw: bytes | None,
        raw_path: str,
        *,
        raw_sha256: str | None = None,
        reply_refusal: Mapping[str, Any] | None = None,
    ) -> Result[SubmissionV1, Refusal]:
        """Record one response.

        ``raw`` is what is parsed. ``raw_sha256`` names the file the transport persisted
        (API mode); without it the digest is of ``raw`` itself (IDE mode).
        """
        raw_sha256 = raw_sha256 or _sha256(raw or b"")
        payload: dict[str, Any]
        violations: tuple[str, ...] = ()
        response: Any = None
        if raw is None:
            refusal = reply_refusal or {}
            code = refusal.get("code", "NO_TEXT")
            violations = (f"/ reply: {code}: {refusal.get('message', '')}",)
        else:
            try:
                response = json.loads(raw.decode("utf-8"), parse_constant=_no_constants)
            except (UnicodeDecodeError, ValueError) as exc:
                response, violations = None, (f"/ parse: {exc}",)
        if response is not None:
            checked = self._host.validate_response(PACKET_IDS[stage], response)
            if isinstance(checked, Err):
                error = checked.error
                violations = (f"/ host validation {error.code}: {error.message}",)
            else:
                violations = checked.value
        accepted = not violations
        if not accepted:
            payload = {"raw_sha256": raw_sha256, "violations": list(violations)}
        elif stage == 4:
            payload = {"raw_sha256": raw_sha256, "candidate": response}
        else:
            payload = {"raw_sha256": raw_sha256, "response": response}
            if stage in _CRITIC_SECTIONS:
                current = self.status(run_id)
                if isinstance(current, Err):
                    return current
                frozen = current.value.checkpoint["state"].get("frozen_sha256")
                payload["candidate_sha"] = _critic_binding(response, stage, frozen)
        recorded = self._apply(
            run_id,
            {
                "command": "record",
                "occurrence_id": occurrence_id,
                "payload": payload,
                "failed": not accepted,
            },
        )
        if isinstance(recorded, Err) and accepted:
            # The occurrence is charged: keep it as a failed attempt rather than leave it
            # unrecorded (a critic of other bytes, or any other refusal of the record).
            refused = recorded.error
            violations = (f"/ {refused.code}: {refused.message}",)
            accepted = False
            recorded = self._apply(
                run_id,
                {
                    "command": "record",
                    "occurrence_id": occurrence_id,
                    "payload": {"raw_sha256": raw_sha256, "violations": list(violations)},
                    "failed": True,
                },
            )
        if isinstance(recorded, Err):
            return recorded
        logged = self._custody.append(
            run_id,
            "execution_occurrences.jsonl",
            {
                "occurrence_id": occurrence_id,
                "stage": stage,
                "raw_path": raw_path,
                "raw_sha256": raw_sha256,
                "accepted": accepted,
                "violations": list(violations),
            },
        )
        if isinstance(logged, Err):
            return logged
        return Ok(SubmissionV1(occurrence_id, raw_path, accepted, violations, recorded.value))

    def _finish(
        self, run_id: str, snapshot: LoopSnapshotV1, residual_ids: list[str]
    ) -> Result[LoopSnapshotV1, Refusal]:
        """Write the receipt bundle and offer residuals to OEEIS as candidates only."""
        events = self._host.events(snapshot.checkpoint)
        if isinstance(events, Err):
            return events
        routes = [e for e in events.value if e.get("event") in {"HOST_ROUTE", "HALTED"}]
        candidates: tuple[str, ...] = ()
        immune_refusal: dict[str, str] | None = None
        if residual_ids and PortName.IMMUNE_ANTIBODIES in self.SPECIALIZATION.licensed_ports:
            try:
                recorded = self.adversary.spine.immune.record_candidates(
                    [f"research_residual:{item}" for item in residual_ids],
                    run_id=run_id,
                    task_id=run_id,
                )
            except Exception as exc:  # another context's failure must not cost the bundle
                message = f"{type(exc).__name__}: {exc}"
                recorded = Err(Refusal("OEEIS_SEEDER_RAISED", message, _LOCUS))
            if isinstance(recorded, Err):
                immune_refusal = {"code": recorded.error.code, "message": recorded.error.message}
            else:
                candidates = recorded.value
        summary = {
            "run_id": run_id,
            "disposition": snapshot.terminal,
            "spent": dict(snapshot.spent),
            "residual_ids": residual_ids,
            "oeeis_candidates": list(candidates),
            "oeeis_refusal": immune_refusal,
            "authority_effect": "None",
        }
        bundle = self._custody.write_bundle(
            run_id,
            {
                "summary.json": summary,
                "receipt.json": {
                    "run_id": run_id,
                    "state_sha256": snapshot.state_sha256,
                    "disposition": snapshot.terminal,
                    "evidence_kind": "RESEARCH_LOOP_CONTROLLER_RECEIPT",
                    "claim_semantic_verification": "NOT_PERFORMED_BY_THE_CONTROLLER",
                    "authority_effect": "None",
                },
                "adapter_loss_ledger.jsonl": [
                    {
                        "sequence": event["sequence"],
                        "disposition": event["data"]["decision"],
                        "routing_terminal": event["data"]["routing_terminal"],
                        "projection_lossy": event["data"].get("projection_lossy", True),
                    }
                    for event in routes
                ],
            },
        )
        if isinstance(bundle, Err):
            return bundle
        return Ok(snapshot)


__all__ = ["PACKET_IDS", "ResearchLoopUseCase"]
