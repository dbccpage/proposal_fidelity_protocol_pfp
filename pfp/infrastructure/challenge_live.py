"""Canonical PFP execution and lineage for trusted Education challenge sources.

The Symbol Game runtime owns prompt assembly, stage dispatch, budgets, and replay.
AuthorityEffect: None.
"""

from __future__ import annotations

import base64
import json
from dataclasses import replace
from uuid import uuid4
from pathlib import Path

from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPrompt
from omega_engine_pfp.infrastructure.adapters.pfp_campaign import (
    replay_stages, grade_reply, micro, request,
    write_new as _write_new,
)
from omega_engine_pfp.use_cases.pfp_stages import PfpStagePolicy
from omega_engine_pfp.use_cases.pfp_proposal import ProposalCheck, REPAIR_RULES
from omega_engine_pfp.infrastructure.pilot_matrix import _scope, complete_pilot_turn
from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn
from omega_engine_woland.domain.providers.types import Provider
from omega_engine_woland.infrastructure.providers.openai_compat import build_openai_compat_body, parse_openai_compat_response
from omega_engine_woland.infrastructure.providers.wire import decode_reply
from omega_engine_woland.use_cases.providers.completion import request_digest

from omega_engine_woland.tests.pilots.challenge_suite.catalog import ROOT
from omega_engine_woland.tests.pilots.challenge_suite.catalog import digest
from omega_engine_woland.tests.pilots.challenge_suite.catalog import load_plan
from omega_engine_woland.tests.pilots.challenge_suite.catalog import prompt_for, prompt_input_paths
from omega_engine_woland.tests.pilots.challenge_suite.catalog import relocated
from omega_engine_pfp.infrastructure.challenge_execution import isolated
from omega_engine_pfp.infrastructure.challenge_execution import source_bindings


def choose_case(challenge_id, split, ordinal):
    if split not in ("development", "held_out") or type(ordinal) is not int or ordinal < 0:
        raise ValueError("INVALID_CASE_SELECTION")
    if challenge_id == "C001":
        from omega_engine_woland.tests.pilots.challenge_suite.c001 import case_rows

        matches = [row for row in case_rows() if row["split"] == split]
        if ordinal >= len(matches):
            raise ValueError("CASE_NOT_FOUND")
        return matches[ordinal]
    matches = [
        row
        for f in load_plan()["families"]
        for c in f["challenges"]
        if c["challenge"] == challenge_id
        for row in c["cases"]
        if row["split"] == split
    ]
    if ordinal >= len(matches):
        raise ValueError("CASE_NOT_FOUND")
    return matches[ordinal]


RUNTIME_SOURCES = (
    "omega_engine_pfp/domain/pfp_ingress.py",
    "omega_engine_pfp/domain/contracts/__init__.py",
    "omega_engine_pfp/domain/contracts/pfp_runtime.py",
    "omega_engine_pfp/use_cases/pfp_prompt.py",
    "omega_engine_pfp/infrastructure/adapters/pfp_campaign.py",
    "omega_engine_pfp/use_cases/pfp_proposal.py",
    "omega_engine_pfp/use_cases/pfp_stages.py",
    "omega_engine_pfp/infrastructure/adapters/pfp_proposals.py",
    "omega_engine_pfp/ffi.py",
    "omega_engine_woland/tests/pilots/challenge_suite/catalog.py",
    "omega_engine_pfp/infrastructure/challenge_execution.py",
    "omega_engine_pfp/infrastructure/challenge_live.py",
)


SCHEMA = "pfp.challenge-accounted.v1"
RUNTIME_SOURCES += (
    "omega_engine_pfp/infrastructure/pilot_matrix.py",
    "omega_engine_pfp/infrastructure/task_turn.py",
    "omega_engine_pfp/infrastructure/estimated_gateway.py",
    "omega_engine_woland/infrastructure/providers/wire.py",
    "omega_engine_woland/infrastructure/providers/openai_compat.py",
    "omega_engine_woland/use_cases/providers/completion.py",
)


def _capture_bytes(value):
    """Current capture JSON escapes Unicode losslessly; raw and historical bytes stay exact."""
    if isinstance(value, bytes):
        return value
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _write_capture(path, value):
    _write_new(path, _capture_bytes(value))


def _prepared(row, arm, feedback, config, stage):
    prompt = PfpPrompt(**prompt_for(row, arm, feedback))
    candidate = request(prompt)
    task_id = f"challenge:{config['run_id']}:{row['challenge']}"
    attempt_id = f"{config['run_id']}:stage:{stage}"
    turn = prepare_task_turn(system=prompt.system, user=prompt.user, task_id=task_id,
        attempt_id=attempt_id, answer_schema={"anyOf": [{"type": "object"}, {"type": "array"},
            {"type": "string", "minLength": 1}]},
        checker_id="pilot-original-judge-pending-v1")
    mediated = replace(candidate, system=turn.prompt.system, user=turn.prompt.user)
    wire = build_openai_compat_body(mediated, model=config["model"],
        max_tokens=config["max_output_tokens"], provider=Provider.OPENROUTER)
    return candidate, mediated, turn, wire


def _receipt(raw, exchange, row, model):
    data = dict(model=model, generation_id=exchange["usage"].get("generation_id", ""),
        usage=exchange["usage"], cost_microusd=None, finish_reason=None)
    cost = exchange["usage"].get("cost")
    if cost is not None:
        data["cost_microusd"] = micro(cost)
    elif not exchange["attempted"]:
        data["cost_microusd"] = 0
    if not exchange["ok"] or exchange["stop"]:
        data["result"] = dict(status="INFRASTRUCTURE_ERROR", failure_class="PFP_OR_ACCOUNTING",
            feedback=None, reason=exchange["error"])
    else:
        try:
            # Original identity/usage/SPK/checker semantics remain in their owner.
            data.update(grade_reply(raw, model, lambda _: isolated(dict(
                kind="LLM", row=row, raw_reply=exchange["content"]), timeout=30)).data)
        except UnicodeEncodeError:
            data["result"] = dict(status="INFRASTRUCTURE_ERROR",
                failure_class="INVALID_COMPLETION_UNICODE", feedback=None,
                reason="The decoded inner answer is not valid UTF-8; original bytes retained.")
        except Exception as exc:
            data["result"] = dict(status="INFRASTRUCTURE_ERROR", failure_class="REPLY_OR_CHECKER",
                feedback=None, reason=str(exc))
    return data


def _summary(records):
    return dict(schema=SCHEMA, status=records[-1]["result"]["status"], stages=len(records),
        cost_microusd=None if any(r["cost_microusd"] is None for r in records)
            else sum(r["cost_microusd"] for r in records),
        known_cost_subtotal_microusd=sum(r["cost_microusd"] or 0 for r in records),
        provider_calls=sum(bool(r["attempted"]) for r in records), transfer_benefit="UNMEASURED",
        scope="Current synthetic/live capture; source-bound replay is not ledger authentication.")


def _source_manifest(row):
    source = ROOT / relocated(row["source"])
    challenge = ROOT / relocated(row["challenge_path"]) if "challenge_path" in row else next(
        p for p in source.parents if p.name[:4] == row["challenge"].lower())
    sources = source_bindings(challenge)
    sources.update({p: digest((ROOT / p).read_bytes()) for p in RUNTIME_SOURCES})
    sources.update({p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in prompt_input_paths(row)})
    return sources


def live_run(row, output: Path, model, arm, price=None, transfer_from=None, *,
        gateway=None, max_output_tokens=None, max_provider_calls=None):
    output = Path(output)
    if output.exists():
        raise ValueError("RUN_ALREADY_EXISTS")
    scope = _scope(gateway, model, max_output_tokens)
    if type(max_output_tokens) is not int or type(max_provider_calls) is not int or max_provider_calls < 1:
        raise ValueError("EXPLICIT_OUTPUT_AND_CALL_BOUNDS_REQUIRED")
    if scope[3] > max_provider_calls:
        raise ValueError("PFP_INJECTED_ALLOWANCE_EXCEEDS_REQUESTED_CAP")
    if arm not in {"baseline", "typed_witness", "transfer"}:
        raise ValueError("UNKNOWN_ARM")
    if price is not None and price["row"]["id"] != model:
        raise ValueError("PRICING_MODEL_MISMATCH")
    owned_price = getattr(gateway, "price", None)
    if price is not None and owned_price is not None and price != owned_price:
        raise ValueError("PRICING_SNAPSHOT_MISMATCH")
    initial_feedback, lineage = None, None
    if arm == "transfer":
        if transfer_from is None or row["split"] != "held_out":
            raise ValueError("TRANSFER_REQUIRES_HELD_OUT_AND_DEVELOPMENT_EVIDENCE")
        transfer_from = Path(transfer_from)
        replay_live(transfer_from)
        previous = json.loads((transfer_from / "config.json").read_bytes())["row"]
        if previous["split"] != "development" or previous["challenge"] != row["challenge"] or previous["source"] == row["source"]:
            raise ValueError("TRANSFER_SPLIT_OR_FAMILY_VIOLATION")
        initial_feedback = json.loads((transfer_from / "stage_1/receipt.json").read_bytes())["result"].get("feedback")
        if initial_feedback not in REPAIR_RULES.values():
            raise ValueError("NO_REUSABLE_FAILURE_RULE")
        lineage = dict(source_run=str(transfer_from), source_receipt_sha256=digest(
            (transfer_from / "stage_1/receipt.json").read_bytes()), admission_status="CANDIDATE_ONLY")
    sources = _source_manifest(row)
    config = dict(schema=SCHEMA, serialization="python-json-sorted-ascii-v1",
        row=row, model=model, arm=arm, max_stages=2, sources=sources,
        initial_feedback=initial_feedback, lineage=lineage, run_id=uuid4().hex,
        max_output_tokens=max_output_tokens, max_provider_calls=max_provider_calls,
        accounting_scope=dict(gateway.scope), accounting_path=str(scope[0]),
        authority_effect="None", execution_scope="Caller-owned accounted gateway; no authorization attestation")
    _prepared(row, arm, initial_feedback, config, 1)  # Validate original prompt/schema before output.
    output.mkdir(parents=True, exist_ok=False)
    _write_capture(output / "config.json", config)
    if owned_price is not None:
        _write_capture(output / "pricing.json", owned_price)
    for relative in sources:
        snapshot = output / "source_snapshot" / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        _write_capture(snapshot, (ROOT / relative).read_bytes())
    policy, feedback, records = PfpStagePolicy(), initial_feedback, []
    for stage in range(1, policy.max_stages + 1):
        candidate, mediated, turn, wire = _prepared(row, arm, feedback, config, stage)
        directory = output / f"stage_{stage}"
        directory.mkdir()
        _write_capture(directory / "request.json", wire)
        cancellation = None
        try:
            exchange = complete_pilot_turn(gateway, candidate, model=model,
                task_id=turn.binding["task_id"], attempt_id=turn.binding["attempt_id"],
                max_tokens=max_output_tokens)
        except BaseException as exc:
            cancellation = exc
            exchange = dict(ok=False, stop=True, content=None, usage={}, pfp=None,
                provider_wire=None, attempt_state=None, error=type(exc).__name__, request=wire)
        try:
            claim = gateway.action(turn.binding["attempt_id"])
        except KeyError:
            claim = None
        raw = None
        if exchange["provider_wire"] is not None:
            raw = base64.b64decode(exchange["provider_wire"]["raw_reply_base64"], validate=True)
        elif claim is not None and "wire_file" in claim:
            raw = gateway.raw_reply(turn.binding["attempt_id"])
        exchange["attempted"] = bool(raw is not None or claim is not None and claim["state"] != "refused_before_dispatch")
        if raw is not None:
            _write_capture(directory / "provider_response.json", raw)
        _write_capture(directory / "exchange.json", exchange)
        _write_capture(directory / "accounting.json", claim)
        receipt = _receipt(raw, exchange, row, model)
        receipt.update(schema=SCHEMA, stage=stage, attempted=exchange["attempted"],
            attempt_id=turn.binding["attempt_id"], request_sha256=digest(_capture_bytes(wire)),
            raw_sha256=digest(raw) if raw is not None else None,
            exchange_sha256=digest(_capture_bytes(exchange)), accounting_sha256=digest(_capture_bytes(claim)))
        _write_capture(directory / "receipt.json", receipt)
        records.append(receipt)
        if cancellation is not None:
            _write_capture(output / "summary.json", _summary(records))
            raise cancellation
        result = receipt["result"]
        feedback = policy.feedback_after(stage, ProposalCheck(result["status"], result["failure_class"]))
        if feedback is None:
            break
    _write_capture(output / "summary.json", _summary(records))
    return records


def _replay_current(output, config):
    if config["sources"] != _source_manifest(config["row"]):
        raise ValueError("REPLAY_SOURCE_MANIFEST_MISMATCH")
    if config["initial_feedback"] is not None and config["initial_feedback"] not in REPAIR_RULES.values():
        raise ValueError("UNTRUSTED_REPAIR_FEEDBACK")
    policy = PfpStagePolicy(config["max_stages"])
    directories = sorted(output.glob("stage_*"))
    if not directories or len(directories) > policy.max_stages:
        raise ValueError("REPLAY_STAGE_BOUND")
    feedback, records = config["initial_feedback"], []
    terminals = dict(settled="CompletedSettled", completed_pending="CompletedPendingSettlement",
        cost_unknown="CompletedCostUnknown", identity_unavailable="CompletedAccountingUnavailable",
        over_estimate="CompletedOverEstimatedBudget", over_admitted="CompletedOverAdmittedBudget")
    for number, directory in enumerate(directories, 1):
        if directory.name != f"stage_{number}":
            raise ValueError("REPLAY_STAGE_SEQUENCE")
        _, mediated, turn, wire = _prepared(config["row"], config["arm"], feedback, config, number)
        exchange = json.loads((directory / "exchange.json").read_bytes())
        claim = json.loads((directory / "accounting.json").read_bytes())
        receipt = json.loads((directory / "receipt.json").read_bytes())
        raw_path = directory / "provider_response.json"
        raw = raw_path.read_bytes() if raw_path.exists() else None
        if (directory / "request.json").read_bytes() != _capture_bytes(wire) or exchange["request"] != wire:
            raise ValueError("REPLAY_BINDING_MISMATCH")
        attempted = bool(raw is not None or claim is not None and claim["state"] != "refused_before_dispatch")
        if exchange["attempted"] != attempted:
            raise ValueError("REPLAY_ATTEMPT_MISMATCH")
        if claim is not None and claim["binding"] != dict(action_id=turn.binding["attempt_id"],
                request_digest=request_digest(mediated), provider="openrouter", model=config["model"],
                max_output_tokens=config["max_output_tokens"]):
            raise ValueError("REPLAY_ACCOUNTING_BINDING_MISMATCH")
        if raw is not None and exchange["provider_wire"] is not None:
            retained = exchange["provider_wire"]
            if retained != dict(raw_reply_base64=base64.b64encode(raw).decode("ascii"),
                    raw_reply_sha256=digest(raw), raw_reply_bytes=len(raw)):
                raise ValueError("REPLAY_RAW_MISMATCH")
        if exchange["attempt_state"] is not None:
            if claim is None or terminals.get(claim["state"]) != exchange["attempt_state"]:
                raise ValueError("REPLAY_ACCOUNTING_STATE_MISMATCH")
            candidate = parse_openai_compat_response(decode_reply(raw), provider=Provider.OPENROUTER,
                fallback_model=config["model"])
            checked = turn.check_completion(candidate.content)
            usage = dict(prompt_tokens=candidate.input_tokens, completion_tokens=candidate.output_tokens,
                cost=candidate.cost_usd, generation_id=candidate.generation_id)
            accepted = exchange["attempt_state"] in {"CompletedSettled", "CompletedPendingSettlement"}
            ok = accepted and checked["schema_valid"] and checked["failure_class"] == "NONE"
            error = None if ok else (exchange["attempt_state"] if not accepted else "PFP_" + checked["failure_class"])
            content = checked["answer"] if ok else None
            if ok and not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)
            if (_capture_bytes(checked) != _capture_bytes(exchange["pfp"]) or usage != exchange["usage"]
                    or ok != exchange["ok"] or (not accepted) != exchange["stop"]
                    or error != exchange["error"] or content != exchange["content"]):
                raise ValueError("REPLAY_PFP_MISMATCH")
        elif exchange["ok"] or not exchange["stop"] or exchange["pfp"] is not None or exchange["usage"]:
            raise ValueError("REPLAY_UNAVAILABLE_STATE_MISMATCH")
        actual = _receipt(raw, exchange, config["row"], config["model"])
        actual.update(schema=SCHEMA, stage=number, attempted=exchange["attempted"],
            attempt_id=turn.binding["attempt_id"], request_sha256=digest(_capture_bytes(wire)),
            raw_sha256=digest(raw) if raw is not None else None,
            exchange_sha256=digest(_capture_bytes(exchange)), accounting_sha256=digest(_capture_bytes(claim)))
        if _capture_bytes(actual) != _capture_bytes(receipt):
            raise ValueError("REPLAY_RESULT_MISMATCH")
        records.append(actual)
        result = actual["result"]
        feedback = policy.feedback_after(number, ProposalCheck(result["status"], result["failure_class"]))
        if feedback is None and number < len(directories):
            raise ValueError("REPLAY_UNAUTHORIZED_STAGE")
    if json.loads((output / "summary.json").read_bytes()) != _summary(records):
        raise ValueError("REPLAY_SUMMARY_MISMATCH")
    return len(records)


def replay_live(output):
    output = Path(output)
    config = json.loads((output / "config.json").read_bytes())
    for path, expected in config["sources"].items():
        try:
            source = (ROOT / path).read_bytes()
        except OSError as error:
            raise ValueError("RUNTIME_SOURCE_DRIFT") from error
        if digest(source) != expected:
            raise ValueError("RUNTIME_SOURCE_DRIFT")
        if config.get("schema") == SCHEMA and (output / "source_snapshot" / path).read_bytes() != source:
            raise ValueError("REPLAY_SOURCE_SNAPSHOT_MISMATCH")
    if config.get("schema") == SCHEMA:
        return _replay_current(output, config)
    if "schema" in config:
        raise ValueError("REPLAY_RUN_SCHEMA_UNSUPPORTED")
    return replay_stages(output, config["model"], config["initial_feedback"], config["max_stages"],
        assemble=lambda feedback: PfpPrompt(**prompt_for(config["row"], config["arm"], feedback)),
        judge=lambda text: isolated(dict(kind="LLM", row=config["row"], raw_reply=text), timeout=30))
