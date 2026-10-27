"""A bounded Adversary PFP operation using the existing native WDP checker.

This is one reusable worker operation, not a replacement swarm coordinator or
a claim that the 22-role workflow was exercised. Model prose stays unverified;
only the original native task check can install a report.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass

from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.report_operation_ports import ReportEpisodePort, ReportOperationPort
from adversary.use_cases.teamwork import TeamworkAction
from adversary.use_cases.teamwork_pfp import (
    check_teamwork_reply,
    prepare_teamwork_turn,
    validate_teamwork_observation,
)


def _refuse(message: str) -> Err:
    prefix = message.split(":", 1)[0]
    code = prefix if re.fullmatch(r"[A-Z][A-Z0-9_]*", prefix) else "REPORT_OPERATION_REFUSAL"
    return Err(Refusal(code=code, message=message or code, locus=__name__))


def _body(outcome: Result) -> dict:
    if isinstance(outcome, Err):
        raise ValueError(outcome.error.code)
    if outcome.value.get("success") is not True:
        raise ValueError("REPORT_NATIVE_REFUSAL: " + str(outcome.value.get("error")))
    body = outcome.value.get("result")
    if type(body) is not dict:
        raise ValueError("REPORT_NATIVE_SHAPE")
    return body


def _source(request: dict, source: bytes) -> None:
    if type(source) is not bytes or hashlib.sha256(source).hexdigest() != request.get("source_sha256"):
        raise ValueError("REPORT_SOURCE_BINDING")


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("REPORT_DUPLICATE_FIELD")
        value[key] = item
    return value


def _turn(episode: str, attempt: int, bundle: dict):
    action = TeamworkAction(
        action_id=f"{episode}:report:{attempt}", initial_task_id=episode, kind="repair",
        objective="Install a sufficient report for the retained finite Genesis task.",
        instructions='Return the JSON string {"repair_prefix": N}, where N selects a complete native repair prefix. '
                     'Do not replace the histories, questions, continuation language or original global task.',
        candidate=json.dumps(bundle, sort_keys=True, separators=(",", ":")),
        operator="finite-genesis-report-install.v1", communication="pfp",
    )
    return action, prepare_teamwork_turn(action)


@dataclass(frozen=True)
class ReportOperation:
    host: ReportOperationPort
    episodes: ReportEpisodePort

    def prepare(self, episode: str, request: dict, *, source: bytes, allowance: int = 4) -> Result:
        try:
            raw = json.dumps(request, allow_nan=False)
            if len(raw.encode()) > 50_000:
                raise ValueError("REPORT_REQUEST_SIZE")
            retained = json.loads(raw)
            if type(retained) is not dict:
                raise ValueError("REPORT_REQUEST_SHAPE")
            _source(retained, source)
            descriptor = _body(self.host.invoke("genesis_report_describe_operation", {"request": retained, "target": episode}))
            bundle = {"request": retained, "descriptor": descriptor, "operation_sha256": self.host.identity()}
            attempt = self.episodes.reserve(episode, bundle, allowance)
            _, turn = _turn(episode, attempt, bundle)
            return Ok({"episode": episode, "attempt": attempt, "binding": turn.binding,
                       "system": turn.prompt.system, "user": turn.prompt.user,
                       "response_schema": turn.prompt.response_schema})
        except (ValueError, TypeError, KeyError, OSError, sqlite3.Error) as error:
            return _refuse(str(error))

    def submit(self, episode: str, attempt: int, raw_reply: bytes, *, source: bytes) -> Result:
        if type(raw_reply) is not bytes or len(raw_reply) > 65_536:
            return _refuse("REPORT_REPLY_BYTES")
        try:
            bundle = self.episodes.claim(episode, attempt)
        except (ValueError, TypeError, OSError, sqlite3.Error) as error:
            return _refuse(str(error))
        evidence = {"raw_reply_base64": base64.b64encode(raw_reply).decode(),
                    "raw_reply_sha256": hashlib.sha256(raw_reply).hexdigest()}
        try:
            if self.host.identity() != bundle["operation_sha256"]:
                raise ValueError("REPORT_OPERATION_CHANGED")
            _source(bundle["request"], source)
            action, turn = _turn(episode, attempt, bundle)
            observation = check_teamwork_reply(action, turn, raw_reply, worker="supplied PFP bytes")
            validate_teamwork_observation(action, observation)
            evidence["pfp_observation"] = observation.model_dump(mode="json")
            if observation.blocked:
                raise ValueError("REPORT_PFP_REFUSAL")
            selection = json.loads(observation.content, object_pairs_hook=_unique_pairs)
            if (type(selection) is not dict or set(selection) != {"repair_prefix"}
                    or type(selection["repair_prefix"]) is not int or not 0 <= selection["repair_prefix"] <= 64):
                raise ValueError("REPORT_PROPOSAL_SHAPE")
            payload = {"request": bundle["request"], "current": bundle["descriptor"]["initial"],
                       "route": bundle["descriptor"]["route"], "repair_prefix": selection["repair_prefix"]}
            candidate = _body(self.host.invoke("genesis_report_commit", payload))
            replay = _body(self.host.invoke("genesis_report_verify_commit", {"input": payload, "candidate": candidate}))
            if replay != {"schema_version": "core.genesis.report-commit-replay.v1", "verified": True, "authority_effect": "None"}:
                raise ValueError("REPORT_COMMIT_REPLAY")
            if self.host.identity() != bundle["operation_sha256"]:
                raise ValueError("REPORT_OPERATION_CHANGED")
            if not self.episodes.finish(episode, attempt, evidence, candidate):
                return _refuse("REPORT_STATE_CONFLICT")
            return Ok({"episode": episode, "attempt": attempt, "native_commit": candidate})
        except (ValueError, TypeError, KeyError, OSError, sqlite3.Error) as error:
            evidence["refusal"] = str(error)
            try:
                self.episodes.finish(episode, attempt, evidence, None)
            except (ValueError, OSError, sqlite3.Error) as storage_error:
                return _refuse("REPORT_EVIDENCE_STORAGE: " + str(storage_error))
            return _refuse(str(error))
