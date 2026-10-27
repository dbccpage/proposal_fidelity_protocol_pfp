"""Canonical provider, durable budget, and file adapters for PFP stages.

Challenge data and independent judges are injected. AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal
from hashlib import sha256
from pathlib import Path
from typing import Callable

from pfp.domain.contracts.pfp_runtime import (
    PfpPreparedStage,
    PfpPrompt,
    PfpStageReceipt,
)
from pfp.use_cases.pfp_proposal import ProposalCheck
from pfp.use_cases.pfp_stages import PfpStagePolicy
from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1
from adversary.infrastructure.providers.budget_ledger import SqliteBudgetLedger
from adversary.infrastructure.providers.openai_compat import build_openai_compat_body
from adversary.infrastructure.providers.openrouter_catalog import fetch_openrouter_catalog
from adversary.infrastructure.providers.wire import decode_reply

MAX_OUTPUT = 3000
CAP = 50000


def canonical(value):
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        + "\n"
    ).encode("utf-8")


def digest(data):
    return sha256(data).hexdigest()


def write_new(path, data):
    if not isinstance(data, bytes):
        data = canonical(data)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def micro(value):
    if type(value) not in (str, int, float, Decimal):
        raise ValueError("MISSING_COST")
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise ValueError("INVALID_COST")
    return int((amount * 1_000_000).to_integral_value(rounding=ROUND_CEILING))


def snapshot_pricing(model, *, required_parameters=("max_tokens", "temperature", "reasoning"), text_only=False):
    raw = fetch_openrouter_catalog(timeout=30)
    catalog = json.loads(raw)
    row = next((r for r in catalog["data"] if r["id"] == model), None)
    if row is None:
        raise ValueError("MODEL_NOT_LISTED")
    pricing = row["pricing"]
    for key, value in pricing.items():
        if text_only and key == "overrides" and isinstance(value, list):
            continue
        if type(value) not in (str, int, float, Decimal):
            raise ValueError("UNSUPPORTED_PRICING_PROFILE")
        if not Decimal(value).is_finite() or Decimal(value) < 0:
            raise ValueError("INVALID_PRICING")
        if (
            key not in ("prompt", "completion", "input_cache_read", "input_cache_write")
            and not (text_only and key in (
                "web_search", "input_cache_write_1h", "internal_reasoning",
                "image", "audio", "input_audio_cache",
            ))
            and Decimal(value) != 0
        ):
            raise ValueError("UNSUPPORTED_SURCHARGE")
    if not set(required_parameters).issubset(row["supported_parameters"]):
        raise ValueError("DECODING_UNSUPPORTED")
    return dict(
        observed_at=datetime.now(timezone.utc).isoformat(), catalog_sha256=digest(raw), row=row
    )


def request(prompt: PfpPrompt):
    return CandidateRequest(
        prompt.system,
        prompt.user,
        decoding=DecodingParamsV1(
            temperature=0.0, allow_fallbacks=False, require_parameters=True, thinking="disabled"
        ),
    )


def request_body(prompt: PfpPrompt, model: str):
    body = build_openai_compat_body(request(prompt), model=model, max_tokens=MAX_OUTPUT)
    body["usage"] = {"include": True}
    return body


def prepare_stage(prompt: PfpPrompt, model: str, price: dict) -> PfpPreparedStage:
    if price["row"]["id"] != model:
        raise ValueError("PRICING_MODEL_MISMATCH")
    rates = price["row"]["pricing"]
    for key, value in rates.items():
        if type(value) not in (str, int, float, Decimal):
            raise ValueError("INVALID_PRICING")
        rate = Decimal(str(value))
        if not rate.is_finite() or rate < 0:
            raise ValueError("INVALID_PRICING")
        if (
            key not in ("prompt", "completion", "input_cache_read", "input_cache_write")
            and rate != 0
        ):
            raise ValueError("UNSUPPORTED_SURCHARGE")
    candidate = request(prompt)
    candidate.check_payload_ceiling()
    reserve = micro(
        Decimal(str(rates["prompt"])) * (candidate.estimated_payload_bytes() + 256)
        + Decimal(str(rates["completion"])) * MAX_OUTPUT
    )
    return PfpPreparedStage(candidate, request_body(prompt, model), reserve)


def grade_reply(raw: bytes, model: str, judge: Callable[[str], dict]) -> PfpStageReceipt:
    reply = decode_reply(raw)
    if reply.get("model") != model or type(reply.get("id")) is not str or not reply["id"]:
        raise ValueError("PROVIDER_IDENTITY_MISMATCH")
    usage = reply.get("usage", {})
    if any(
        type(usage.get(k)) is not int or usage[k] < 0
        for k in ("prompt_tokens", "completion_tokens", "total_tokens")
    ):
        raise ValueError("MISSING_USAGE")
    cost = micro(usage.get("cost"))
    text = reply["choices"][0]["message"]["content"]
    if type(text) is not str:
        raise ValueError("MISSING_COMPLETION")
    return PfpStageReceipt(
        dict(
            result=judge(text),
            generation_id=reply["id"],
            model=model,
            usage=usage,
            cost_microusd=cost,
            finish_reason=reply["choices"][0].get("finish_reason"),
        )
    )


class PfpCampaignAdapter:
    def __init__(
        self,
        output: Path,
        model: str,
        price: dict,
        assemble: Callable[[str | None], PfpPrompt],
        judge: Callable[[str], dict],
        send: Callable[[str, CandidateRequest, int], bytes],
        context: dict,
    ):
        if price["row"]["id"] != model:
            raise ValueError("PRICING_MODEL_MISMATCH")
        self.output, self.model, self.price = output, model, price
        self.assemble, self.judge, self.send, self.context = assemble, judge, send, context
        self.ledger = SqliteBudgetLedger(output / "budget.sqlite3", budget_id="pfp-learning")

    def prepare(self, prompt: PfpPrompt) -> PfpPreparedStage:
        return prepare_stage(prompt, self.model, self.price)

    def reserve(self, stage: int, amount: int) -> None:
        with self.ledger.transaction(CAP) as state:
            if any(a["state"] != "settled" for a in state["attempts"].values()):
                raise ValueError("UNRECONCILED_ATTEMPT")
            if str(stage) in state["attempts"]:
                raise ValueError("STAGE_ALREADY_ATTEMPTED")
            if state["spent"] + amount > CAP:
                raise ValueError("RUN_CAP_EXCEEDED")
            state["spent"] += amount
            state["attempts"][str(stage)] = dict(state="reserved", reserved=amount)

    def record_request(self, stage: int, prepared: PfpPreparedStage) -> None:
        stage_dir = self.output / f"stage_{stage}"
        stage_dir.mkdir()
        write_new(stage_dir / "request.json", prepared.wire_body)
        write_new(
            stage_dir / "reservation.json",
            dict(
                reserved_microusd=prepared.reserved_microusd,
                request_sha256=digest(canonical(prepared.wire_body)),
            ),
        )

    def dispatch(self, prepared: PfpPreparedStage) -> bytes:
        return self.send(self.model, prepared.payload, MAX_OUTPUT)

    def record_raw(self, stage: int, raw: bytes) -> None:
        write_new(self.output / f"stage_{stage}/provider_response.json", raw)

    def grade(self, raw: bytes) -> PfpStageReceipt:
        return grade_reply(raw, self.model, self.judge)

    def record_receipt(self, stage: int, receipt: PfpStageReceipt, elapsed: float) -> None:
        stage_dir = self.output / f"stage_{stage}"
        receipt.data.update(
            latency_seconds=elapsed,
            raw_sha256=digest((stage_dir / "provider_response.json").read_bytes()),
            request_sha256=digest((stage_dir / "request.json").read_bytes()),
        )
        write_new(stage_dir / "receipt.json", receipt.data)

    def settle(self, stage: int, receipt: PfpStageReceipt, reserve: int) -> None:
        data = receipt.data
        with self.ledger.transaction(CAP) as state:
            if data["generation_id"] in [
                a.get("generation_id") for a in state["attempts"].values()
            ]:
                raise ValueError("DUPLICATE_GENERATION")
            state["spent"] += data["cost_microusd"] - reserve
            state["attempts"][str(stage)].update(
                state="settled", actual=data["cost_microusd"], generation_id=data["generation_id"]
            )

    def record_failure(self, stage: int, failure: dict) -> None:
        name = "reply_failure.json" if failure.get("phase") == "reply" else "transport_failure.json"
        write_new(self.output / f"stage_{stage}/{name}", failure)

    def summarize(self, summary: dict) -> None:
        write_new(self.output / "summary.json", summary)

    def observe(self, stage: int, receipt: PfpStageReceipt) -> None:
        print(
            json.dumps(
                dict(
                    self.context,
                    stage=stage,
                    status=receipt.data["result"]["status"],
                    cost_microusd=receipt.data["cost_microusd"],
                )
            ),
            flush=True,
        )


class PfpPipelineProviderAdapter:
    """Accounted numbered-stage proposals; the original stage validators decide.

    Current captures retain the actual PFP envelope and wire. Legacy pricing.json
    captures remain replay-only and retain their original reservation contract.
    Neither transport completion nor PFP shape is mathematical acceptance.
    """

    CAPTURE_SCHEMA = "pfp.numbered-stage-capture.v2"

    def __init__(self, output: Path, model: str, *, gateway=None, send=None, replay=False):
        self.output, self.model, self.replay = Path(output), model, replay
        self.gateway = gateway
        self.provider_calls = 0
        self.cost_microusd = None if replay else 0
        self._settled_microusd = 0
        self._completed_stages, self._generations = set(), set()
        self._blocked = False
        self.last_turn = None
        self.judge = lambda _: dict(status="PROVIDER_COMPLETED", failure_class="NONE")
        marker = self.output / "pipeline.json"
        self._legacy = replay and not marker.exists()
        if self._legacy:
            self.price = json.loads((self.output / "pricing.json").read_bytes())
            self.pricing_sha256 = digest((self.output / "pricing.json").read_bytes())
        elif replay:
            self.capture = json.loads(marker.read_bytes())
            if self.capture.get("schema") != self.CAPTURE_SCHEMA or self.capture.get("model") != model:
                raise ValueError("REPLAY_BINDING_MISMATCH")
            self.max_output_tokens = self.capture["max_output_tokens"]
        else:
            from uuid import uuid4
            from pfp.infrastructure.pilot_matrix import _scope, _output_bound

            if self.output.exists():
                raise ValueError("RUN_ALREADY_EXISTS")
            scope = _scope(gateway, model)
            self.max_output_tokens = _output_bound(gateway)
            self.capture = dict(schema=self.CAPTURE_SCHEMA, model=model, run_id=uuid4().hex,
                max_output_tokens=self.max_output_tokens, accounting_path=str(scope[0]),
                accounting_scope=gateway.scope, authority_effect="None",
                canonicalization_profile="python-json-sorted-ascii-v1",
                evidence_scope="Bound provider proposal; original stage/host checks remain separate")
            self.output.mkdir(parents=True, exist_ok=False)
            self._save(marker, self.capture)

    @staticmethod
    def _bytes(value):
        # Current capture encoding also retains escaped lone surrogates. The
        # historical canonical() function and all old identities stay unchanged.
        return (json.dumps(value, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")

    @classmethod
    def _save(cls, path, value):
        write_new(path, cls._bytes(value))

    def _prepare(self, packet):
        from dataclasses import replace
        from pfp.infrastructure.task_turn import prepare_task_turn
        from adversary.domain.providers.types import Provider

        prompt = PfpPrompt(packet.system,
            packet.user + "\nReturn only JSON satisfying this response schema:\n"
            + json.dumps(packet.response_schema, sort_keys=True), packet.response_schema)
        candidate = request(prompt)
        turn = prepare_task_turn(system=candidate.system, user=candidate.user,
            task_id="numbered:" + self.capture["run_id"] + ":" + packet.demo_id,
            attempt_id=self.capture["run_id"] + ":stage:" + str(packet.stage),
            answer_schema={"anyOf": [{"type": "object"}, {"type": "array"},
                {"type": "string", "minLength": 1}]},
            checker_id="pilot-original-judge-pending-v1")
        mediated = replace(candidate, system=turn.prompt.system, user=turn.prompt.user)
        wire = build_openai_compat_body(mediated, model=self.model,
            max_tokens=self.max_output_tokens, provider=Provider.OPENROUTER)
        return candidate, turn, wire

    def _receipt(self, exchange, packet_sha256, wire, raw):
        cost = exchange.get("usage", {}).get("cost")
        return dict(schema=self.CAPTURE_SCHEMA, packet_sha256=packet_sha256,
            capture_sha256=digest(self._bytes(self.capture)),
            exchange_sha256=digest(self._bytes(exchange)),
            request_sha256=digest(self._bytes(wire)), raw_sha256=digest(raw) if raw is not None else None,
            result=dict(status="PROVIDER_COMPLETED" if exchange["ok"] and not exchange["stop"]
                else "INFRASTRUCTURE_ERROR", failure_class=exchange["error"] or "NONE"),
            generation_id=exchange.get("usage", {}).get("generation_id"), model=self.model,
            usage=exchange.get("usage", {}), cost_microusd=(micro(cost) if cost is not None
                else None if exchange["attempted"] else 0),
            attempt_state=exchange["attempt_state"], latency_seconds=exchange["elapsed"],
            authority_effect="None")

    def _record(self, directory, exchange, turn, packet_sha256, wire):
        import base64

        raw = (base64.b64decode(exchange["provider_wire"]["raw_reply_base64"], validate=True)
            if exchange.get("provider_wire") else None)
        receipt = self._receipt(exchange, packet_sha256, wire, raw)
        self.last_turn = exchange
        self._blocked = True
        cost = receipt["cost_microusd"]
        if cost is None:
            self.cost_microusd = None
        else:
            self._settled_microusd += cost
            self.cost_microusd = self._settled_microusd
        if raw is not None:
            write_new(directory / "provider_response.json", raw)
        self._save(directory / "exchange.json", exchange)
        self._save(directory / "receipt.json", receipt)
        if not exchange["ok"] or exchange["stop"]:
            self._blocked = True
            raise ValueError(exchange["error"] or "PFP_PIPELINE_REPLY_REFUSED")
        generation = receipt["generation_id"]
        if generation in self._generations:
            self._blocked = True
            raise ValueError("DUPLICATE_GENERATION")
        self._generations.add(generation)
        self._blocked = False
        return exchange["content"]

    def generate_candidate(self, packet, temperature=0.0):
        if self._legacy:
            return self._legacy_candidate(packet, temperature)
        if temperature != 0.0:
            raise ValueError("PFP_PIPELINE_DECODING_UNSUPPORTED")
        if type(packet.stage) is not int or not 1 <= packet.stage <= 8:
            raise ValueError("PFP_PIPELINE_STAGE_UNSUPPORTED")
        if self._blocked:
            raise ValueError("PFP_PIPELINE_STOPPED")
        if packet.stage in self._completed_stages:
            raise ValueError("STAGE_ALREADY_ATTEMPTED")
        candidate, turn, wire = self._prepare(packet)
        packet_sha256 = digest(self._bytes(packet.model_dump(mode="json")))
        directory = self.output / f"stage_{packet.stage}"
        if self.replay:
            answer = self._replay_current(directory, turn, packet_sha256, wire)
            self._completed_stages.add(packet.stage)
            return answer
        from pfp.infrastructure.pilot_matrix import complete_pilot_turn

        directory.mkdir()
        self._save(directory / "request.json", wire)
        self._completed_stages.add(packet.stage)
        self.cost_microusd = None
        self._blocked = True
        try:
            exchange = complete_pilot_turn(self.gateway, candidate, model=self.model,
                task_id=turn.binding["task_id"], attempt_id=turn.binding["attempt_id"],
                max_tokens=self.max_output_tokens)
        except BaseException as exc:
            # Preserve cancellation semantics and existing unknown action/wire;
            # never turn an interrupted attempt into an observed free call.
            try:
                action = self.gateway.action(turn.binding["attempt_id"])
            except (OSError, ValueError, KeyError):
                action = None
            self.provider_calls += 1
            self.cost_microusd = None
            self._blocked = True
            raw = None
            try:
                raw = self.gateway.raw_reply(turn.binding["attempt_id"])
            except (OSError, ValueError, KeyError):
                pass
            if raw is not None:
                write_new(directory / "provider_response.json", raw)
            self.last_turn = dict(error="PFP_ADAPTER_INTERRUPTED_" + type(exc).__name__,
                stop=True, ok=False, accounting=action, cost_microusd=None)
            self._save(directory / "exchange.json", self.last_turn)
            raise
        try:
            action = self.gateway.action(turn.binding["attempt_id"])
        except KeyError:
            action = None
        self._save(directory / "accounting.json", action)
        if action is not None and action["state"] != "refused_before_dispatch":
            self.provider_calls += 1
        exchange["attempted"] = bool(exchange.get("provider_wire") or
            (action is not None and action["state"] != "refused_before_dispatch"))
        if exchange["ok"]:
            try:
                exchange["content"].encode("utf-8")
            except UnicodeEncodeError:
                exchange.update(ok=False, content=None, error="PFP_INVALID_ANSWER_UNICODE")
        return self._record(directory, exchange, turn, packet_sha256, wire)

    def _replay_current(self, directory, turn, packet_sha256, wire):
        import base64
        from adversary.domain.providers.types import Provider
        from adversary.infrastructure.providers.openai_compat import parse_openai_compat_response

        exchange = json.loads((directory / "exchange.json").read_bytes())
        stored = json.loads((directory / "receipt.json").read_bytes())
        if ((directory / "request.json").read_bytes() != self._bytes(wire)
                or exchange["request"] != wire):
            raise ValueError("REPLAY_BINDING_MISMATCH")
        path = directory / "provider_response.json"
        raw = path.read_bytes() if path.exists() else None
        evidence = exchange["provider_wire"]
        if evidence is None:
            if raw is not None:
                raise ValueError("REPLAY_BINDING_MISMATCH")
        elif (raw is None or base64.b64decode(evidence["raw_reply_base64"], validate=True) != raw
                or evidence["raw_reply_sha256"] != digest(raw)
                or evidence["raw_reply_bytes"] != len(raw)):
            raise ValueError("REPLAY_BINDING_MISMATCH")
        if self._receipt(exchange, packet_sha256, wire, raw) != stored:
            raise ValueError("REPLAY_RESULT_MISMATCH")
        action = json.loads((directory / "accounting.json").read_bytes())
        attempted = bool(raw is not None or
            (action is not None and action["state"] != "refused_before_dispatch"))
        if exchange["attempted"] != attempted:
            raise ValueError("REPLAY_RESULT_MISMATCH")
        if exchange["pfp"] is None:
            # A gateway refusal/ambiguous send may have no decoded completion.
            # Recheck its request/action and retained wire without inventing one.
            from dataclasses import replace
            from adversary.use_cases.providers.completion import request_digest

            allowed_no_send = {"CALL_ALLOWANCE_EXHAUSTED", "ESTIMATED_BUDGET_EXCEEDED",
                "FUZZY_BUDGET_MILESTONE_REACHED", "UNRECONCILED_ATTEMPT",
                "RUN_RECONCILIATION_REQUIRED"}
            if action is not None:
                original = CandidateRequest(turn.prompt.system, turn.prompt.user,
                    decoding=DecodingParamsV1(temperature=0.0, allow_fallbacks=False,
                        require_parameters=True, thinking="disabled"))
                expected_binding = dict(action_id=turn.binding["attempt_id"],
                    request_digest=request_digest(replace(original, messages=())),
                    provider="openrouter", model=self.model, max_output_tokens=self.max_output_tokens)
                valid_failure = (action["binding"] == expected_binding
                    and action["state"] in {"outcome_unknown", "refused_before_dispatch"}
                    and (action.get("failure_code") == exchange["error"]
                        or (not action.get("failure_code") and exchange["error"] in {
                            "PFP_ADAPTER_ERROR_TimeoutError", "PFP_ADAPTER_ERROR_OSError",
                            "PFP_ADAPTER_ERROR_ConnectionError"})))
            else:
                valid_failure = raw is None and exchange["error"] in allowed_no_send
            if (not valid_failure or exchange["ok"] or not exchange["stop"]
                    or exchange["usage"] or exchange["content"] is not None):
                raise ValueError("REPLAY_RESULT_MISMATCH")
            self.last_turn, self._blocked = exchange, True
            self.cost_microusd = None if attempted else self._settled_microusd
            raise ValueError(exchange["error"])
        decoded = decode_reply(raw)
        candidate = parse_openai_compat_response(decoded, provider=Provider.OPENROUTER,
            fallback_model=self.model, transport="replay")
        if candidate.model != self.model:
            raise ValueError("PROVIDER_IDENTITY_MISMATCH")
        content = (decoded["choices"][0]["message"]["content"]
            if self.capture["accounting_scope"]["schema"] == "pfp.fuzzy-run.v1" else candidate.content)
        checked = turn.check_completion(content)
        usage = dict(prompt_tokens=candidate.input_tokens, completion_tokens=candidate.output_tokens,
            cost=candidate.cost_usd, generation_id=candidate.generation_id)
        success = checked["schema_valid"] and checked["failure_class"] == "NONE"
        expected_answer = checked["answer"] if success else None
        expected_content = (expected_answer if isinstance(expected_answer, str)
            else json.dumps(expected_answer, ensure_ascii=False)) if success else None
        invalid_answer_unicode = False
        if expected_content is not None:
            try:
                expected_content.encode("utf-8")
            except UnicodeEncodeError:
                invalid_answer_unicode = True
        if (self._bytes(exchange["pfp"]) != self._bytes(checked) or exchange["usage"] != usage
                or (exchange["ok"] and (not success or exchange["content"] != expected_content))
                or (exchange["ok"] and (exchange["stop"] or candidate.cost_usd is None
                    or invalid_answer_unicode
                    or exchange["attempt_state"] not in {"CompletedSettled", "CompletedPendingSettlement"}))
                or (invalid_answer_unicode and exchange["error"] != "PFP_INVALID_ANSWER_UNICODE")):
            raise ValueError("REPLAY_RESULT_MISMATCH")
        expected = self._receipt(exchange, packet_sha256, wire, raw)
        if expected != stored:
            raise ValueError("REPLAY_RESULT_MISMATCH")
        if not exchange["ok"] or exchange["stop"]:
            self._blocked = True
            self.last_turn = exchange
            self.cost_microusd = None if candidate.cost_usd is None else self._settled_microusd + micro(candidate.cost_usd)
            raise ValueError(exchange["error"] or "PFP_PIPELINE_REPLY_REFUSED")
        if candidate.generation_id in self._generations:
            raise ValueError("DUPLICATE_GENERATION")
        self._generations.add(candidate.generation_id)
        self._settled_microusd += micro(candidate.cost_usd)
        self.cost_microusd = self._settled_microusd
        self.last_turn = exchange
        return exchange["content"]

    def _legacy_candidate(self, packet, temperature=0.0):
        if temperature != 0.0:
            raise ValueError("PFP_PIPELINE_DECODING_UNSUPPORTED")
        if type(packet.stage) is not int or not 1 <= packet.stage <= 8:
            raise ValueError("PFP_PIPELINE_STAGE_UNSUPPORTED")
        if packet.stage in self._completed_stages:
            raise ValueError("STAGE_ALREADY_ATTEMPTED")
        packet_sha256 = digest(canonical(packet.model_dump(mode="json")))
        prompt = PfpPrompt(
            packet.system,
            packet.user + "\nReturn only JSON satisfying this response schema:\n"
            + json.dumps(packet.response_schema, sort_keys=True),
            packet.response_schema,
        )
        prepared = prepare_stage(prompt, self.model, self.price)
        directory = self.output / f"stage_{packet.stage}"
        wire = (directory / "request.json").read_bytes()
        raw = (directory / "provider_response.json").read_bytes()
        stored = json.loads((directory / "receipt.json").read_bytes())
        reservation = json.loads((directory / "reservation.json").read_bytes())
        if reservation != dict(
            reserved_microusd=prepared.reserved_microusd,
            request_sha256=digest(canonical(prepared.wire_body)),
        ):
            raise ValueError("REPLAY_RESERVATION_MISMATCH")
        if wire != canonical(prepared.wire_body) or digest(raw) != stored["raw_sha256"]:
            raise ValueError("REPLAY_BINDING_MISMATCH")
        if digest(wire) != stored["request_sha256"]:
            raise ValueError("REPLAY_BINDING_MISMATCH")
        if (
            stored.get("packet_sha256") != packet_sha256
            or stored.get("pricing_sha256") != self.pricing_sha256
        ):
            raise ValueError("REPLAY_BINDING_MISMATCH")
        if self._settled_microusd + prepared.reserved_microusd > CAP:
            raise ValueError("RUN_CAP_EXCEEDED")
        checked = grade_reply(raw, self.model, self.judge)
        if checked.data["cost_microusd"] > prepared.reserved_microusd:
            raise ValueError("BILL_EXCEEDS_RESERVATION")
        if checked.data["generation_id"] in self._generations:
            raise ValueError("DUPLICATE_GENERATION")
        for key, value in checked.data.items():
            if key not in stored or canonical(value) != canonical(stored[key]):
                raise ValueError("REPLAY_RESULT_MISMATCH")
        self._completed_stages.add(packet.stage)
        self._generations.add(checked.data["generation_id"])
        self._settled_microusd += checked.data["cost_microusd"]
        self.cost_microusd = self._settled_microusd
        return decode_reply(raw)["choices"][0]["message"]["content"]


def replay_stages(output, model, initial_feedback, max_stages, assemble, judge):
    """Rebuild requests and judge saved raw replies without provider dispatch."""
    policy = PfpStagePolicy(max_stages)
    stages = sorted(output.glob("stage_*"))
    if not stages or len(stages) > policy.max_stages:
        raise ValueError("REPLAY_STAGE_BOUND")
    feedback = initial_feedback
    price = json.loads((output / "pricing.json").read_bytes())
    spent = 0
    generations = set()
    for number, stage in enumerate(stages, 1):
        if stage.name != f"stage_{number}":
            raise ValueError("REPLAY_STAGE_SEQUENCE")
        receipt = json.loads((stage / "receipt.json").read_bytes())
        raw = (stage / "provider_response.json").read_bytes()
        wire = (stage / "request.json").read_bytes()
        prepared = prepare_stage(assemble(feedback), model, price)
        expected = prepared.wire_body
        reservation = json.loads((stage / "reservation.json").read_bytes())
        if reservation != dict(
            reserved_microusd=prepared.reserved_microusd, request_sha256=digest(canonical(expected))
        ):
            raise ValueError("REPLAY_RESERVATION_MISMATCH")
        if spent + prepared.reserved_microusd > CAP:
            raise ValueError("RUN_CAP_EXCEEDED")
        if (
            digest(raw) != receipt["raw_sha256"]
            or digest(wire) != receipt["request_sha256"]
            or wire != canonical(expected)
        ):
            raise ValueError("REPLAY_BINDING_MISMATCH")
        checked = grade_reply(raw, model, judge).data
        if checked["cost_microusd"] > prepared.reserved_microusd:
            raise ValueError("BILL_EXCEEDS_RESERVATION")
        if checked["generation_id"] in generations:
            raise ValueError("DUPLICATE_GENERATION")
        generations.add(checked["generation_id"])
        spent += checked["cost_microusd"]
        for key, value in checked.items():
            if canonical(value) != canonical(receipt[key]):
                raise ValueError("REPLAY_RESULT_MISMATCH")
        result = checked["result"]
        feedback = policy.feedback_after(
            number, ProposalCheck(result["status"], result["failure_class"])
        )
        if feedback is None and number < len(stages):
            raise ValueError("REPLAY_UNAUTHORIZED_STAGE")
    summary = json.loads((output / "summary.json").read_bytes())
    expected_summary = dict(
        status=result["status"],
        stages=len(stages),
        cost_microusd=sum(
            json.loads((s / "receipt.json").read_bytes())["cost_microusd"] for s in stages
        ),
        transfer_benefit="UNMEASURED",
    )
    if canonical(summary) != canonical(expected_summary):
        raise ValueError("REPLAY_SUMMARY_MISMATCH")
    return len(stages)
