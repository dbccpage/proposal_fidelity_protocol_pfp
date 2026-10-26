"""Durable provider adapter for research loops; domain judges are injected."""

import json
import math
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal

from omega_engine_woland.domain.providers.types import CandidateRequest, DecodingParamsV1
from omega_engine_woland.infrastructure.providers.budget_ledger import SqliteBudgetLedger
from omega_engine_woland.infrastructure.providers.openai_compat import build_openai_compat_body
from omega_engine_woland.infrastructure.providers.openrouter_deadline import dispatch_deadline
from omega_engine_woland.infrastructure.providers.wire import decode_reply
from omega_engine_pfp.use_cases.pfp_derivation_loops import DerivationLimits, DerivationStop

from .pfp_evidence import canonical, digest, write_once

MAX_OUTPUT = 2500


def microusd(value):
    if type(value) not in (int, float, str, Decimal):
        raise ValueError("MISSING_COST")
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise ValueError("INVALID_COST")
    return int((amount * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


def model_pricing(raw, model):
    catalog = decode_reply(raw)
    row = next((row for row in catalog["data"] if row["id"] == model), None)
    if row is None:
        raise ValueError("MODEL_NOT_LISTED")
    if not {"max_tokens", "temperature", "reasoning", "seed"}.issubset(row["supported_parameters"]):
        raise ValueError("REQUIRED_DECODING_UNSUPPORTED")
    rates = row["pricing"]
    if not {"prompt", "completion"}.issubset(rates):
        raise ValueError("MISSING_PRICE")
    # This campaign authorizes this named free route only. A priced route needs a new preflight.
    for value in rates.values():
        if microusd(value) != 0:
            raise ValueError("NONZERO_ROUTE_PRICE")
    return row


def request_for(prompt):
    return CandidateRequest(
        prompt["system_prompt"],
        prompt["user_prompt"],
        decoding=DecodingParamsV1(
            seed=1000 + prompt["generation"],
            temperature=0,
            allow_fallbacks=False,
            require_parameters=True,
            thinking="disabled",
        ),
    )


def wire_for(prompt, model):
    wire = build_openai_compat_body(request_for(prompt), model=model, max_tokens=MAX_OUTPUT)
    wire["usage"] = {"include": True}
    return wire


def provider_result(raw, model):
    reply = decode_reply(raw)
    if reply.get("model") != model or type(reply.get("id")) is not str or not reply["id"]:
        raise ValueError("PROVIDER_IDENTITY_MISMATCH")
    usage = reply.get("usage", {})
    if any(
        type(usage.get(k)) is not int or usage[k] < 0
        for k in ("prompt_tokens", "completion_tokens", "total_tokens")
    ):
        raise ValueError("MISSING_USAGE")
    if (
        usage["total_tokens"] != usage["prompt_tokens"] + usage["completion_tokens"]
        or usage["completion_tokens"] > MAX_OUTPUT
    ):
        raise ValueError("INVALID_USAGE")
    content = reply["choices"][0]["message"]["content"]
    if type(content) is not str:
        raise ValueError("MISSING_CONTENT")
    return dict(
        generation_id=reply["id"],
        tokens=usage["total_tokens"],
        usage=dict(usage),
        cost_microusd=microusd(usage.get("cost")),
        finish_reason=reply["choices"][0].get("finish_reason"),
        content=content,
    )


def current_canonical(value):
    """Version 2 captures preserve escaped invalid Unicode without altering v1."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False).encode("ascii")


def write_current(path, value):
    write_once(path, value if isinstance(value, bytes) else current_canonical(value) + b"\n")


def prepare_research_turn(prompt, model, run_id, pilot, loop, *, experiment=False):
    from dataclasses import replace
    from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn

    if experiment:
        from .pfp_experiment import request_for as original_request
        maximum = prompt["max_output_tokens"]
    else:
        original_request, maximum = request_for, MAX_OUTPUT
    candidate = original_request(prompt)
    turn = prepare_task_turn(system=candidate.system, user=candidate.user,
        task_id="research:" + run_id + ":" + pilot,
        attempt_id=run_id + ":loop:" + str(loop),
        answer_schema={"anyOf": [{"type": "object"}, {"type": "array"},
            {"type": "string", "minLength": 1}]}, checker_id="research-original-observer-pending-v1")
    candidate = replace(candidate, system=turn.prompt.system, user=turn.prompt.user)
    wire = build_openai_compat_body(candidate, model=model, max_tokens=maximum)
    wire["usage"] = {"include": True}
    return candidate, turn, wire


def inner_proposal(checked):
    if not checked["schema_valid"] or checked["failure_class"] != "NONE":
        raise ValueError("PFP_" + checked["failure_class"])
    answer = checked["answer"]
    text = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("PFP_INVALID_ANSWER_UNICODE") from None
    return text


class PfpDerivationAdapter:
    def __init__(
        self, *, pilot, folder, campaign, model, pricing_sha256, sources, prompt_builder, observer
    ):
        self.pilot, self.folder, self.campaign, self.model = pilot, folder, campaign, model
        self.pricing_sha256, self.sources = pricing_sha256, sources
        self.prompt_builder, self.observer = prompt_builder, observer
        self.rows = []
        self.experiment = False

    def begin(self, limits):
        from uuid import uuid4

        if any((self.folder / name).exists() for name in
                ("run.json", "terminal.json", "budget.sqlite3")) or any(self.folder.glob("loop_*")):
            raise ValueError("RUN_ALREADY_EXISTS_NO_AUTOMATIC_RETRY")
        self.limits, self.start, self.run_id = limits, time.monotonic(), uuid4().hex
        write_current(self.folder / "run.json", dict(schema="pfp.derivation-run.v2",
            authority_effect="None", pilot_id=self.pilot, campaign=self.campaign, model=self.model,
            limits=vars(limits), started_at=datetime.now(timezone.utc).isoformat(),
            pricing_sha256=self.pricing_sha256, sources=self.sources, run_id=self.run_id,
            adapter_kind="experiment" if self.experiment else "derivation",
            canonicalization_profile="python-json-sorted-ascii-v1"))
        self.ledger = SqliteBudgetLedger(self.folder / "budget.sqlite3", budget_id=self.pilot)

    def state(self):
        with self.ledger.transaction(self.limits.microusd) as state:
            return json.loads(json.dumps(state))

    def _maximum(self, prompt):
        return MAX_OUTPUT

    def _timeout(self, remaining, loop):
        return remaining

    def _dispatch(self, request, maximum, timeout):
        return dispatch_deadline(self.model, request, maximum, timeout)

    def propose(self, loop, context):
        remaining = self.limits.seconds - (time.monotonic() - self.start)
        if remaining <= 0:
            raise DerivationStop("TIME_CAP")
        state = self.state()
        if any(row["state"] != "settled" for row in state["attempts"].values()):
            raise DerivationStop("UNRECONCILED_ATTEMPT")
        if state["spent"] >= self.limits.microusd:
            raise DerivationStop("COST_CAP")
        prompt = self.prompt_builder(self.pilot, loop, context)
        maximum = self._maximum(prompt)
        request, turn, wire_value = prepare_research_turn(prompt, self.model,
            self.run_id, self.pilot, loop, experiment=self.experiment)
        wire, prompt_bytes = current_canonical(wire_value), current_canonical(prompt)
        hold = len(wire) + 512 + maximum
        reserve = microusd(getattr(self, "rate", Decimal(0)) * hold)
        if sum(row["tokens"] for row in state["attempts"].values()) + hold > self.limits.tokens:
            raise DerivationStop("TOKEN_CAP")
        if state["spent"] + reserve > self.limits.microusd:
            raise DerivationStop("COST_CAP")
        path, attempt = self.folder / f"loop_{loop:02d}", str(loop)
        write_current(path / "prompt.json", prompt)
        write_current(path / "request.json", wire)
        with self.ledger.transaction(self.limits.microusd) as state:
            if attempt in state["attempts"]:
                raise DerivationStop("ATTEMPT_ALREADY_RECORDED")
            state["attempts"][attempt] = dict(state="reserved", reserved=reserve,
                token_hold=hold, prompt_sha256=digest(prompt_bytes), request_sha256=digest(wire),
                sequence=loop, dispatched=False)
            state["spent"] += reserve
        remaining = self.limits.seconds - (time.monotonic() - self.start)
        timeout = self._timeout(remaining, loop)
        if timeout <= 0:
            write_current(path / "infrastructure_error.json", dict(code="TIME_CAP_BEFORE_DISPATCH",
                hold_retained=True, raw_sha256=None, deadline_seconds=0,
                observed_unsettled_usage=None))
            raise DerivationStop("TIME_CAP")
        with self.ledger.transaction(self.limits.microusd) as state:
            state["attempts"][attempt]["dispatched"] = True
        result = None
        try:
            raw = self._dispatch(request, maximum, timeout)
            write_current(path / "raw_reply.json", raw)
            result = provider_result(raw, self.model)
            if self.experiment and (result["usage"]["completion_tokens"] > maximum
                    or result["tokens"] > hold or result["cost_microusd"] > reserve):
                raise ValueError("PROVIDER_EXCEEDED_RESERVATION")
        except Exception as exc:
            observed = None
            if result is not None:
                observed = dict(tokens=result["tokens"], cost_microusd=result["cost_microusd"])
                with self.ledger.transaction(self.limits.microusd) as state:
                    liability = max(reserve, result["cost_microusd"])
                    state["spent"] += liability - reserve
                    state["attempts"][attempt].update(reserved=liability,
                        tokens=result["tokens"], observed=observed)
            raw_path = path / "raw_reply.json"
            write_current(path / "infrastructure_error.json", dict(code=type(exc).__name__,
                hold_retained=True, raw_sha256=digest(raw_path.read_bytes()) if raw_path.exists() else None,
                deadline_seconds=timeout, observed_unsettled_usage=observed))
            elapsed = time.monotonic() - self.start
            raise DerivationStop("TIME_CAP" if elapsed >= self.limits.seconds
                else "INFRASTRUCTURE_ERROR") from None
        with self.ledger.transaction(self.limits.microusd) as state:
            duplicate = any(row.get("generation_id") == result["generation_id"]
                            for row in state["attempts"].values())
            if duplicate:
                observed = dict(tokens=result["tokens"], cost_microusd=result["cost_microusd"])
                liability = max(reserve, result["cost_microusd"])
                state["spent"] += liability - reserve
                state["attempts"][attempt].update(reserved=liability,
                    tokens=result["tokens"], observed=observed)
            else:
                state["spent"] += result["cost_microusd"] - reserve
                state["attempts"][attempt].update(state="settled", actual=result["cost_microusd"],
                    tokens=result["tokens"], generation_id=result["generation_id"])
        if duplicate:
            # Retain observed liability before a stop can roll back the transaction.
            write_current(path / "infrastructure_error.json", dict(code="DUPLICATE_GENERATION",
                hold_retained=True, raw_sha256=digest(raw), deadline_seconds=timeout,
                observed_unsettled_usage=observed))
            raise DerivationStop("INFRASTRUCTURE_ERROR")
        checked = turn.check_completion(result["content"])
        write_current(path / "pfp_check.json", checked)
        receipt = {key: value for key, value in result.items() if key != "content"}
        receipt.update(raw_sha256=digest(raw), prompt_sha256=digest(prompt_bytes),
            request_sha256=digest(wire), elapsed_seconds=time.monotonic() - self.start,
            pfp_check_sha256=digest(current_canonical(checked)), deadline_seconds=timeout)
        if self.experiment:
            receipt["stage_name"] = prompt["experiment_stage"]
        # Observers may serialize mappings with insertion-order-sensitive YAML.
        # Hand them the exact v2 serialized order used during offline readback.
        receipt = json.loads(current_canonical(receipt))
        write_current(path / "provider_receipt.json", receipt)
        self.rows.append(receipt)
        try:
            result = {**result, "content": inner_proposal(checked)}
        except ValueError as exc:
            raise DerivationStop(str(exc)) from None
        return prompt, result, receipt

    def observe(self, loop, proposal, context):
        prompt, result, receipt = proposal
        return self.observer(self.pilot, loop, self.folder / f"loop_{loop:02d}",
            prompt, result, receipt, context)

    def finish(self, completed, terminal, context):
        state = self.state()
        if state["spent"] > self.limits.microusd:
            terminal = "COST_CAP"
        elif sum(row.get("tokens", 0) for row in state["attempts"].values()) > self.limits.tokens:
            terminal = "TOKEN_CAP"
        elif time.monotonic() - self.start >= self.limits.seconds:
            terminal = "TIME_CAP"
        known = sum(row.get("actual", row.get("observed", {}).get("cost_microusd", 0))
            for row in state["attempts"].values())
        unknown = any(row.get("dispatched") and row["state"] != "settled"
            and "observed" not in row for row in state["attempts"].values())
        write_current(self.folder / "budget_snapshot.json", state)
        result = dict(schema="pfp.derivation-terminal.v2", authority_effect="None",
            pilot_id=self.pilot, completed_loops=completed,
            provider_calls=sum(bool(row.get("dispatched")) for row in state["attempts"].values()),
            recorded_attempts=len(state["attempts"]), terminal=terminal, settled_calls=len(self.rows),
            tokens=sum(row.get("tokens", 0) for row in state["attempts"].values()),
            cost_microusd=None if unknown else known, known_cost_microusd=known,
            reserved_liability_microusd=state["spent"],
            elapsed_seconds=time.monotonic() - self.start, context=context,
            limits=vars(self.limits), analytical_status="UNVERIFIED")
        write_current(self.folder / "terminal.json", result)
        return result


def replay_run(folder, pilot, model, prompt_builder, observer, sources):
    """Dispatch current PFP replay; the original v1 replay below stays unchanged."""
    if decode_reply((folder / "run.json").read_bytes()).get("schema") == "pfp.derivation-run.v2":
        return replay_current_run(folder, pilot, model, prompt_builder, observer, sources)

    def load(path):
        return dict(decode_reply(path.read_bytes()))

    config, terminal = load(folder / "run.json"), load(folder / "terminal.json")
    limits = DerivationLimits(**config["limits"])
    if terminal["limits"] != config["limits"] or terminal["pilot_id"] != pilot:
        raise ValueError("LIMIT_OR_ID_MISMATCH")
    if (
        type(terminal["elapsed_seconds"]) not in (float, int)
        or not math.isfinite(terminal["elapsed_seconds"])
        or terminal["elapsed_seconds"] < 0
    ):
        raise ValueError("INVALID_ELAPSED_TIME")
    if config["sources"] != sources or config["model"] != model or config["pilot_id"] != pilot:
        raise ValueError("SOURCE_OR_CONFIG_DRIFT")
    context = {}
    rows = []
    for path in sorted(folder.glob("loop_*")):
        if not (path / "provider_receipt.json").exists():
            continue
        loop = int(path.name.split("_")[1])
        if loop != len(rows) + 1:
            raise ValueError("LOOP_SEQUENCE_MISMATCH")
        prompt = prompt_builder(pilot, loop, context)
        if load(path / "prompt.json") != prompt:
            raise ValueError("PROMPT_LINEAGE_MISMATCH")
        wire = canonical(wire_for(prompt, model))
        raw, receipt = (path / "raw_reply.json").read_bytes(), load(path / "provider_receipt.json")
        if (
            (path / "request.json").read_bytes() != wire
            or receipt["request_sha256"] != digest(wire)
            or receipt["raw_sha256"] != digest(raw)
            or receipt["prompt_sha256"] != digest(canonical(prompt))
        ):
            raise ValueError("RECEIPT_DIGEST_MISMATCH")
        result = provider_result(raw, model)
        if any(receipt[key] != value for key, value in result.items() if key != "content"):
            raise ValueError("PROVIDER_RECEIPT_MISMATCH")
        context = observer(pilot, loop, path, prompt, result, receipt, context)
        rows.append(receipt)
    snapshot = load(folder / "budget_snapshot.json")
    with closing(
        sqlite3.connect(f"{(folder / 'budget.sqlite3').resolve().as_uri()}?mode=ro", uri=True)
    ) as connection:
        row = connection.execute(
            "SELECT state FROM provider_budget WHERE id=?", (pilot,)
        ).fetchone()
    if row is None or json.loads(row[0]) != snapshot:
        raise ValueError("BUDGET_SNAPSHOT_MISMATCH")
    if (
        terminal["settled_calls"] != len(rows)
        or terminal["tokens"] != sum(row["tokens"] for row in rows)
        or terminal["cost_microusd"] != snapshot["spent"]
    ):
        raise ValueError("TERMINAL_ACCOUNTING_MISMATCH")
    attempts = snapshot["attempts"]
    if terminal["provider_calls"] != len(attempts) or snapshot["limit"] != limits.microusd:
        raise ValueError("ATTEMPT_COUNT_OR_LIMIT_MISMATCH")
    if terminal["context"] != context or terminal["completed_loops"] != len(rows):
        raise ValueError("COMPLETED_CONTEXT_MISMATCH")
    if len(rows) > limits.loops:
        raise ValueError("LOOP_CEILING_BREACHED")
    spent = sum(receipt["cost_microusd"] for receipt in rows)
    unresolved = {key: row for key, row in attempts.items() if row["state"] != "settled"}
    if snapshot["spent"] != spent + sum(row["reserved"] for row in unresolved.values()):
        raise ValueError("SPEND_RECONCILIATION_MISMATCH")
    if set(attempts) != {str(i) for i in range(1, len(attempts) + 1)} or len(unresolved) > 1:
        raise ValueError("ATTEMPT_SEQUENCE_MISMATCH")
    for loop, receipt in enumerate(rows, 1):
        attempt = attempts[str(loop)]
        prompt = load(folder / f"loop_{loop:02d}/prompt.json")
        hold = len(canonical(wire_for(prompt, model))) + 512 + MAX_OUTPUT
        elapsed = receipt["elapsed_seconds"]
        prior_elapsed = rows[loop - 2]["elapsed_seconds"] if loop > 1 else 0
        if (
            type(elapsed) not in (int, float)
            or not math.isfinite(elapsed)
            or not prior_elapsed <= elapsed <= terminal["elapsed_seconds"]
        ):
            raise ValueError("RECEIPT_TIME_MISMATCH")
        if (
            attempt["state"] != "settled"
            or attempt["actual"] != receipt["cost_microusd"]
            or attempt["tokens"] != receipt["tokens"]
            or attempt["generation_id"] != receipt["generation_id"]
            or attempt["request_sha256"] != receipt["request_sha256"]
            or attempt["prompt_sha256"] != receipt["prompt_sha256"]
            or attempt["sequence"] != loop
            or attempt["token_hold"] != hold
            or type(attempt["reserved"]) is not int
            or attempt["reserved"] != 0
        ):
            raise ValueError("ATTEMPT_ACCOUNTING_MISMATCH")
    if {key for key, attempt in attempts.items() if attempt["state"] == "settled"} != {
        str(i) for i in range(1, len(rows) + 1)
    }:
        raise ValueError("UNRECEIPTED_SETTLED_ATTEMPT")
    if len(attempts) > limits.loops:
        raise ValueError("ATTEMPT_CEILING_BREACHED")
    for key, attempt in unresolved.items():
        if type(attempt["reserved"]) is not int or attempt["reserved"] != 0:
            raise ValueError("PENDING_RESERVATION_MISMATCH")
        loop = len(rows) + 1
        path = folder / f"loop_{loop:02d}"
        expected = prompt_builder(pilot, loop, context)
        wire = canonical(wire_for(expected, model))
        if (
            key != str(loop)
            or attempt["state"] != "reserved"
            or attempt["sequence"] != loop
            or load(path / "prompt.json") != expected
            or (path / "request.json").read_bytes() != wire
            or attempt["request_sha256"] != digest(wire)
            or attempt["prompt_sha256"] != digest(canonical(expected))
            or attempt["token_hold"] != len(wire) + 512 + MAX_OUTPUT
        ):
            raise ValueError("PENDING_ATTEMPT_CUSTODY_MISMATCH")
        error = load(path / "infrastructure_error.json")
        raw_path = path / "raw_reply.json"
        if error.get("hold_retained") is not True or error.get("raw_sha256") != (
            digest(raw_path.read_bytes()) if raw_path.exists() else None
        ):
            raise ValueError("PENDING_RAW_BINDING_MISMATCH")
    reason = terminal["terminal"]
    if reason == "LOOP_LIMIT":
        if (
            len(rows) != limits.loops
            or unresolved
            or terminal["elapsed_seconds"] >= limits.seconds
            or spent > limits.microusd
            or terminal["tokens"] > limits.tokens
        ):
            raise ValueError("LOOP_LIMIT_MISMATCH")
    elif reason == "TIME_CAP":
        if terminal["elapsed_seconds"] < limits.seconds:
            raise ValueError("TIME_CAP_UNWITNESSED")
    elif reason == "COST_CAP":
        if spent < limits.microusd:
            raise ValueError("COST_CAP_UNWITNESSED")
    elif reason == "TOKEN_CAP":
        next_wire = wire_for(prompt_builder(pilot, len(rows) + 1, context), model)
        if terminal["tokens"] + len(canonical(next_wire)) + 512 + MAX_OUTPUT <= limits.tokens:
            raise ValueError("TOKEN_CAP_UNWITNESSED")
    elif reason == "INFRASTRUCTURE_ERROR":
        if (
            len(unresolved) != 1
            or not (folder / f"loop_{len(rows) + 1:02d}/infrastructure_error.json").exists()
        ):
            raise ValueError("INFRASTRUCTURE_STOP_UNWITNESSED")
    else:
        raise ValueError("UNSUPPORTED_TERMINAL")
    return dict(
        pilot_id=pilot, replayed_calls=len(rows), context=context, analytical_status="UNVERIFIED"
    )

def replay_current_run(folder, pilot, model, prompt_builder, observer, sources):
    """Recheck v2 wire, billing and actual PFP replies; never dispatch or create a ledger."""
    def load(path):
        return dict(decode_reply(path.read_bytes()))

    config = load(folder / "run.json")
    terminal = load(folder / "terminal.json")
    limits = DerivationLimits(**config["limits"])
    if (config.get("schema") != "pfp.derivation-run.v2"
            or terminal.get("schema") != "pfp.derivation-terminal.v2"
            or config["pilot_id"] != pilot or terminal["pilot_id"] != pilot
            or config["model"] != model or config["sources"] != sources
            or terminal["limits"] != config["limits"]
            or config.get("canonicalization_profile") != "python-json-sorted-ascii-v1"):
        raise ValueError("SOURCE_OR_CONFIG_DRIFT")
    elapsed = terminal["elapsed_seconds"]
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("INVALID_ELAPSED_TIME")
    if config["adapter_kind"] not in {"experiment", "derivation"}:
        raise ValueError("UNSUPPORTED_ADAPTER_KIND")
    experiment = config["adapter_kind"] == "experiment"
    rate = Decimal(0)
    if experiment:
        profile = load(folder / "pricing_profile.json")
        rate = Decimal(profile["ceiling_usd_per_token"])
        if (not rate.is_finite() or rate < 0 or rate * 120000 > Decimal("0.05")
                or profile.get("model", model) != model):
            raise ValueError("INVALID_PRICING_PROFILE")
    snapshot = load(folder / "budget_snapshot.json")
    with closing(sqlite3.connect((folder / "budget.sqlite3").resolve().as_uri() + "?mode=ro", uri=True)) as db:
        row = db.execute("SELECT state FROM provider_budget WHERE id=?", (pilot,)).fetchone()
    if row is None or json.loads(row[0]) != snapshot:
        raise ValueError("BUDGET_SNAPSHOT_MISMATCH")
    attempts = snapshot["attempts"]
    if (snapshot["limit"] != limits.microusd or len(attempts) > limits.loops
            or set(attempts) != {str(n) for n in range(1, len(attempts) + 1)}
            or {p.name for p in folder.glob("loop_*")} != {f"loop_{n:02d}" for n in range(1, len(attempts) + 1)}):
        raise ValueError("ATTEMPT_SEQUENCE_OR_LIMIT_MISMATCH")
    context, receipts, generations, completed = {}, [], set(), 0
    refusal = None
    previous_elapsed = 0
    consumed = 0
    for loop in range(1, len(attempts) + 1):
        path, attempt = folder / f"loop_{loop:02d}", attempts[str(loop)]
        prompt = prompt_builder(pilot, loop, context)
        maximum = prompt["max_output_tokens"] if experiment else MAX_OUTPUT
        if type(maximum) is not int or not 0 < maximum <= MAX_OUTPUT:
            raise ValueError("INVALID_EXPERIMENT_OUTPUT_CAP")
        _, turn, wire_value = prepare_research_turn(prompt, model, config["run_id"],
            pilot, loop, experiment=experiment)
        wire = current_canonical(wire_value)
        hold, reserve = len(wire) + 512 + maximum, microusd(rate * (len(wire) + 512 + maximum))
        if (load(path / "prompt.json") != prompt or (path / "request.json").read_bytes() != wire
                or attempt["request_sha256"] != digest(wire)
                or attempt["prompt_sha256"] != digest(current_canonical(prompt))
                or attempt["sequence"] != loop or attempt["token_hold"] != hold
                or consumed + hold > limits.tokens or type(attempt.get("dispatched")) is not bool):
            raise ValueError("PENDING_ATTEMPT_CUSTODY_MISMATCH")
        raw_path, receipt_path = path / "raw_reply.json", path / "provider_receipt.json"
        if not receipt_path.exists():
            if loop != len(attempts) or attempt["state"] != "reserved":
                raise ValueError("PENDING_ATTEMPT_CUSTODY_MISMATCH")
            error = load(path / "infrastructure_error.json")
            raw = raw_path.read_bytes() if raw_path.exists() else None
            if (error.get("hold_retained") is not True
                    or error.get("raw_sha256") != (digest(raw) if raw is not None else None)):
                raise ValueError("PENDING_RAW_BINDING_MISMATCH")
            observed = None
            if raw is not None:
                try:
                    result = provider_result(raw, model)
                except Exception as exc:
                    if error["code"] != type(exc).__name__:
                        raise ValueError("PROVIDER_FAILURE_MISMATCH") from None
                else:
                    observed = dict(tokens=result["tokens"], cost_microusd=result["cost_microusd"])
                    duplicate = result["generation_id"] in generations
                    exceeded = experiment and (result["usage"]["completion_tokens"] > maximum
                        or result["tokens"] > hold or result["cost_microusd"] > reserve)
                    if not duplicate and not exceeded:
                        raise ValueError("UNRECEIPTED_SETTLED_ATTEMPT")
                    if error["code"] != ("DUPLICATE_GENERATION" if duplicate else "ValueError"):
                        raise ValueError("PROVIDER_FAILURE_MISMATCH")
            elif not attempt["dispatched"] and error["code"] != "TIME_CAP_BEFORE_DISPATCH":
                raise ValueError("PENDING_ATTEMPT_CUSTODY_MISMATCH")
            if error.get("observed_unsettled_usage") != observed:
                raise ValueError("PROVIDER_FAILURE_MISMATCH")
            expected_reserve = max(reserve, observed["cost_microusd"]) if observed is not None else reserve
            if (attempt["reserved"] != expected_reserve
                    or (observed is not None and attempt.get("observed") != observed)):
                raise ValueError("PENDING_RESERVATION_MISMATCH")
            refusal = "TIME_CAP" if not attempt["dispatched"] else "INFRASTRUCTURE_ERROR"
            continue
        if attempt["state"] != "settled" or not attempt["dispatched"]:
            raise ValueError("ATTEMPT_ACCOUNTING_MISMATCH")
        receipt, raw = load(receipt_path), raw_path.read_bytes()
        result = provider_result(raw, model)
        if result["generation_id"] in generations:
            raise ValueError("DUPLICATE_GENERATION")
        generations.add(result["generation_id"])
        checked = turn.check_completion(result["content"])
        if current_canonical(load(path / "pfp_check.json")) != current_canonical(checked):
            raise ValueError("PFP_REPLAY_MISMATCH")
        if (any(receipt[key] != value for key, value in result.items() if key != "content")
                or receipt["raw_sha256"] != digest(raw)
                or receipt["request_sha256"] != digest(wire)
                or receipt["prompt_sha256"] != digest(current_canonical(prompt))
                or receipt["pfp_check_sha256"] != digest(current_canonical(checked))):
            raise ValueError("PROVIDER_RECEIPT_MISMATCH")
        receipt_elapsed, deadline = receipt["elapsed_seconds"], receipt["deadline_seconds"]
        if (type(receipt_elapsed) not in (int, float) or not math.isfinite(receipt_elapsed)
                or not previous_elapsed <= receipt_elapsed <= elapsed
                or type(deadline) not in (int, float) or not math.isfinite(deadline)
                or not 0 < deadline <= limits.seconds
                or (experiment and receipt["stage_name"] != prompt["experiment_stage"])):
            raise ValueError("RECEIPT_TIME_MISMATCH")
        previous_elapsed = receipt_elapsed
        if (attempt["reserved"] != reserve or attempt["actual"] != result["cost_microusd"]
                or attempt["tokens"] != result["tokens"] or attempt["generation_id"] != result["generation_id"]
                or (experiment and (result["usage"]["completion_tokens"] > maximum
                    or result["tokens"] > hold or result["cost_microusd"] > reserve))):
            raise ValueError("ATTEMPT_ACCOUNTING_MISMATCH")
        consumed += result["tokens"]
        receipts.append(receipt)
        try:
            inner = inner_proposal(checked)
        except ValueError as exc:
            if loop != len(attempts):
                raise ValueError("PFP_UNAUTHORIZED_CONTINUATION") from None
            refusal = str(exc)
        else:
            context = observer(pilot, loop, path, prompt, {**result, "content": inner}, receipt, context)
            completed += 1
    known = sum(row.get("actual", row.get("observed", {}).get("cost_microusd", 0)) for row in attempts.values())
    unknown = any(row.get("dispatched") and row["state"] != "settled" and "observed" not in row
        for row in attempts.values())
    liability = sum(row["actual"] if row["state"] == "settled" else row["reserved"] for row in attempts.values())
    expected = dict(provider_calls=sum(bool(row["dispatched"]) for row in attempts.values()),
        recorded_attempts=len(attempts), settled_calls=len(receipts), completed_loops=completed,
        tokens=sum(row.get("tokens", 0) for row in attempts.values()),
        cost_microusd=None if unknown else known, known_cost_microusd=known,
        reserved_liability_microusd=snapshot["spent"], context=context)
    if (snapshot["spent"] != liability or any(terminal[key] != value for key, value in expected.items())):
        raise ValueError("TERMINAL_ACCOUNTING_MISMATCH")
    reason = terminal["terminal"]
    if reason == "TIME_CAP":
        if elapsed < limits.seconds and refusal != "TIME_CAP":
            raise ValueError("TIME_CAP_UNWITNESSED")
    elif reason == "COST_CAP":
        if snapshot["spent"] < limits.microusd:
            next_prompt = prompt_builder(pilot, len(attempts) + 1, context)
            maximum = next_prompt["max_output_tokens"] if experiment else MAX_OUTPUT
            _, _, next_wire = prepare_research_turn(next_prompt, model, config["run_id"],
                pilot, len(attempts) + 1, experiment=experiment)
            if snapshot["spent"] + microusd(rate * (len(current_canonical(next_wire)) + 512 + maximum)) <= limits.microusd:
                raise ValueError("COST_CAP_UNWITNESSED")
    elif reason == "TOKEN_CAP":
        next_prompt = prompt_builder(pilot, len(attempts) + 1, context)
        maximum = next_prompt["max_output_tokens"] if experiment else MAX_OUTPUT
        _, _, next_wire = prepare_research_turn(next_prompt, model, config["run_id"],
            pilot, len(attempts) + 1, experiment=experiment)
        if expected["tokens"] + len(current_canonical(next_wire)) + 512 + maximum <= limits.tokens:
            raise ValueError("TOKEN_CAP_UNWITNESSED")
    elif refusal is not None:
        if reason != refusal:
            raise ValueError("STOP_REASON_MISMATCH")
    elif reason != "LOOP_LIMIT" or completed != limits.loops or len(receipts) != limits.loops:
        raise ValueError("LOOP_LIMIT_MISMATCH")
    return dict(pilot_id=pilot, replayed_calls=len(receipts), completed_loops=completed,
        terminal=reason, context=context, analytical_status="UNVERIFIED")
