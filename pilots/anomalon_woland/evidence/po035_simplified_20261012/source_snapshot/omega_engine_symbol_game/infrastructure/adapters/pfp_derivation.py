"""Durable provider adapter for research loops; domain judges are injected."""

import json
import math
import sqlite3
import time
from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal

from omega_engine_providers.domain.types import CandidateRequest, DecodingParamsV1
from omega_engine_providers.infrastructure.budget_ledger import SqliteBudgetLedger
from omega_engine_providers.infrastructure.openai_compat import build_openai_compat_body
from omega_engine_providers.infrastructure.openrouter_deadline import dispatch_deadline
from omega_engine_providers.infrastructure.wire import decode_reply
from omega_engine_symbol_game.use_cases.pfp_derivation_loops import DerivationLimits, DerivationStop

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


class PfpDerivationAdapter:
    def __init__(
        self, *, pilot, folder, campaign, model, pricing_sha256, sources, prompt_builder, observer
    ):
        self.pilot, self.folder, self.campaign, self.model = pilot, folder, campaign, model
        self.pricing_sha256, self.sources = pricing_sha256, sources
        self.prompt_builder, self.observer = prompt_builder, observer
        self.rows = []

    def begin(self, limits):
        self.limits = limits
        self.start = time.monotonic()
        write_once(
            self.folder / "run.json",
            dict(
                schema="pfp.derivation-run.v1",
                authority_effect="None",
                pilot_id=self.pilot,
                campaign=self.campaign,
                model=self.model,
                limits=vars(limits),
                started_at=datetime.now(timezone.utc).isoformat(),
                pricing_sha256=self.pricing_sha256,
                sources=self.sources,
            ),
        )
        self.ledger = SqliteBudgetLedger(self.folder / "budget.sqlite3", budget_id=self.pilot)

    def state(self):
        with self.ledger.transaction(self.limits.microusd) as state:
            return json.loads(json.dumps(state))

    def propose(self, loop, context):
        elapsed = time.monotonic() - self.start
        if elapsed >= self.limits.seconds:
            raise DerivationStop("TIME_CAP")
        state = self.state()
        if any(row["state"] != "settled" for row in state["attempts"].values()):
            raise DerivationStop("UNRECONCILED_ATTEMPT")
        if state["spent"] >= self.limits.microusd:
            raise DerivationStop("COST_CAP")
        prompt = self.prompt_builder(self.pilot, loop, context)
        wire = wire_for(prompt, self.model)
        # Byte count upper-bounds byte-tokenized prompt, with framing allowance.
        reserved_tokens = len(canonical(wire)) + 512 + MAX_OUTPUT
        consumed = sum(row["tokens"] for row in state["attempts"].values())
        if consumed + reserved_tokens > self.limits.tokens:
            raise DerivationStop("TOKEN_CAP")
        path = self.folder / f"loop_{loop:02d}"
        write_once(path / "prompt.json", prompt)
        write_once(path / "request.json", canonical(wire))
        # Verified zero pricing, yet a durable attempt/maximum-output hold is mandatory.
        with self.ledger.transaction(self.limits.microusd) as state:
            attempt = str(loop)
            if attempt in state["attempts"]:
                raise DerivationStop("ATTEMPT_ALREADY_RECORDED")
            state["attempts"][attempt] = dict(
                state="reserved",
                reserved=0,
                token_hold=reserved_tokens,
                prompt_sha256=digest(canonical(prompt)),
                request_sha256=digest(canonical(wire)),
                sequence=loop,
            )
        remaining = self.limits.seconds - (time.monotonic() - self.start)
        if remaining <= 0:
            write_once(
                path / "infrastructure_error.json",
                {"code": "TIME_CAP_BEFORE_DISPATCH", "hold_retained": True, "raw_sha256": None},
            )
            raise DerivationStop("TIME_CAP")
        try:
            raw = dispatch_deadline(self.model, request_for(prompt), MAX_OUTPUT, remaining)
            write_once(path / "raw_reply.json", raw)
            result = provider_result(raw, self.model)
        except Exception as exc:
            # Never print transport text (it could include private request/credential metadata).
            write_once(
                path / "infrastructure_error.json",
                {
                    "code": type(exc).__name__,
                    "hold_retained": True,
                    "raw_sha256": digest((path / "raw_reply.json").read_bytes())
                    if (path / "raw_reply.json").exists()
                    else None,
                },
            )
            elapsed = time.monotonic() - self.start
            raise DerivationStop(
                "TIME_CAP" if elapsed >= self.limits.seconds else "INFRASTRUCTURE_ERROR"
            ) from None
        with self.ledger.transaction(self.limits.microusd) as state:
            if any(
                row.get("generation_id") == result["generation_id"]
                for row in state["attempts"].values()
            ):
                write_once(
                    path / "infrastructure_error.json",
                    {
                        "code": "DUPLICATE_GENERATION",
                        "hold_retained": True,
                        "raw_sha256": digest(raw),
                    },
                )
                raise DerivationStop("INFRASTRUCTURE_ERROR")
            state["spent"] += result["cost_microusd"]
            state["attempts"][attempt].update(
                state="settled",
                actual=result["cost_microusd"],
                tokens=result["tokens"],
                generation_id=result["generation_id"],
            )
        receipt = {key: value for key, value in result.items() if key != "content"}
        receipt.update(
            raw_sha256=digest(raw),
            prompt_sha256=digest(canonical(prompt)),
            request_sha256=digest(canonical(wire)),
            elapsed_seconds=time.monotonic() - self.start,
        )
        write_once(path / "provider_receipt.json", receipt)
        self.rows.append(receipt)
        return prompt, result, receipt

    def observe(self, loop, proposal, context):
        prompt, result, receipt = proposal
        # Host stages always retain the obtained proposal even when it arrives at the deadline.
        return self.observer(
            self.pilot, loop, self.folder / f"loop_{loop:02d}", prompt, result, receipt, context
        )

    def finish(self, completed, terminal, context):
        state = self.state()
        if state["spent"] > self.limits.microusd:
            terminal = "COST_CAP"
        elif sum(row.get("tokens", 0) for row in state["attempts"].values()) > self.limits.tokens:
            terminal = "TOKEN_CAP"
        elif time.monotonic() - self.start >= self.limits.seconds:
            terminal = "TIME_CAP"
        write_once(self.folder / "budget_snapshot.json", state)
        result = dict(
            schema="pfp.derivation-terminal.v1",
            authority_effect="None",
            pilot_id=self.pilot,
            completed_loops=completed,
            provider_calls=len(state["attempts"]),
            terminal=terminal,
            settled_calls=len(self.rows),
            tokens=sum(row.get("tokens", 0) for row in state["attempts"].values()),
            cost_microusd=state["spent"],
            elapsed_seconds=time.monotonic() - self.start,
            context=context,
            limits=vars(self.limits),
            analytical_status="UNVERIFIED",
        )
        write_once(self.folder / "terminal.json", result)
        return result


def replay_run(folder, pilot, model, prompt_builder, observer, sources):
    """Recompute requests, all finite verdicts and learning stages without transport."""

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
    with sqlite3.connect(
        f"{(folder / 'budget.sqlite3').resolve().as_uri()}?mode=ro", uri=True
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
