"""Retired duplicate Python seat gateway and historical injected fixture oracle.

Public execution refuses. The private scripted fixture profile preserves old
routing/vector observations only; no supported production entrypoint selects it.
Live seven-act execution uses native PFP with the continuing accounted ledger.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from pathlib import Path
from typing import Any, Callable, Mapping

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.value_objects.seat_turn import SeatTurnReplyV1, SeatTurnRequestV1
from omega_engine_pfp.infrastructure.seat_transport.routing import (
    RouteLeg,
    RoutingTable,
    admit_spend,
)
from omega_engine_pfp.infrastructure.seat_transport.transport import SYMBOL_GAME_PROTOCOL_V2
from omega_engine_woland.domain.providers.types import CandidateRequest, Provider
from omega_engine_woland.infrastructure.providers.openai_compat import parse_openai_compat_response

Transport = Callable[[str, CandidateRequest, int], bytes]

MACHINE_BLOCK = re.compile(r"```machine\s*\n(.*?)```", re.DOTALL)
REQUIRED_MACHINE_KEYS = ("AUTHORITY_EFFECT", "RESIDUAL_COLOUR", "DISPOSITION", "DDC_LETTER")
RESIDUAL_COLOURS = ("Open", "Closed", "Exact")

SYSTEM_TEMPLATE = """You are seat '{seat_id}' (cognitive operator: {operator}) in scene '{scene_id}' of Woland's Swarm Dialectic.
You have no authority. End your reply with exactly one machine block:

```machine
AUTHORITY_EFFECT=None
RESIDUAL_COLOUR=<Open|Closed|Exact>
DISPOSITION=<SELECT|CHALLENGE|REJECT|PASS_TO_MASTER|REFUSE>
DDC_LETTER=<E|R|C|I|Λ|D|M|T>
```
"""


class SeatTurnRefused(RuntimeError):
    """Raised by ``__call__`` for callers that expect an exception, carrying the Refusal."""

    def __init__(self, refusal: Refusal) -> None:
        self.refusal = refusal
        super().__init__(f"{refusal.code}: {refusal.message}")


class CallLedger:
    """Append-only JSONL of every attempt. The path is explicit."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, record: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(dict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")

    def spent_on(self, day: str) -> int:
        if not self.path.exists():
            return 0
        total = 0
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("day") == day and type(rec.get("cost_microusd")) is int:
                    total += rec["cost_microusd"]
        return total


@dataclass(frozen=True)
class ParsedReply:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_microusd: int
    cost_source: str
    finish_reason: str | None = None


def _parse(leg: RouteLeg, raw: bytes) -> ParsedReply:
    data = json.loads(raw.decode("utf-8"), parse_float=Decimal)
    parser_data = data
    usage = data.get("usage") if isinstance(data, Mapping) else None
    if isinstance(usage, Mapping):
        # The shared parser accepts JSON cost strings, not Decimal objects.
        # Keep the original Decimal receipt below for exact micro-USD rounding.
        parser_usage = dict(usage)
        for field in ("cost", "total_cost"):
            if isinstance(parser_usage.get(field), Decimal):
                parser_usage[field] = str(parser_usage[field])
        parser_data = {**data, "usage": parser_usage}
    resp = parse_openai_compat_response(parser_data, provider=Provider.OPENROUTER, fallback_model=leg.model)
    usage = data.get("usage") or {}
    receipt = usage.get("cost") if usage.get("cost") is not None else usage.get("total_cost")
    if isinstance(receipt, (Decimal, int)) and not isinstance(receipt, bool) and receipt >= 0:
        cost, source = ceil(Decimal(receipt) * 1_000_000), "provider_receipt"
    else:
        cost, source = leg.cost_microusd(resp.input_tokens, resp.output_tokens), "price_table"
    choices = data.get("choices") or [{}]
    finish = (choices[0] or {}).get("finish_reason")
    finish_reason = finish if isinstance(finish, str) and finish else None
    return ParsedReply(
        resp.content, resp.model, resp.input_tokens, resp.output_tokens, cost, source, finish_reason
    )


def parse_machine_block(text: str) -> Result[dict[str, str], Refusal]:
    found = MACHINE_BLOCK.findall(text)
    if len(found) != 1:
        return Err(Refusal("MALFORMED", f"expected one machine block, found {len(found)}"))
    fields: dict[str, str] = {}
    for line in found[0].strip().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip()
    missing = [k for k in REQUIRED_MACHINE_KEYS if k not in fields]
    if missing:
        return Err(Refusal("MALFORMED", f"machine block missing {missing}"))
    if fields["RESIDUAL_COLOUR"] not in RESIDUAL_COLOURS:
        return Err(Refusal("MALFORMED", f"bad RESIDUAL_COLOUR {fields['RESIDUAL_COLOUR']!r}"))
    return Ok(fields)


class RoutedSeatExecutor:
    protocol_id = SYMBOL_GAME_PROTOCOL_V2

    def __init__(
        self,
        *,
        table: RoutingTable,
        config_digest: str,
        transports: Mapping[str, Transport],
        ledger: CallLedger,
        bout_id: str,
        max_output_tokens: int = 65536,
        clock: Callable[[], float] = time.monotonic,
        today: Callable[[], str] = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    ) -> None:
        self.table = table
        self.config_digest = config_digest
        self.transports = dict(transports)
        self.ledger = ledger
        self.bout_id = bout_id
        self.max_output_tokens = max_output_tokens
        self._clock = clock
        self._today = today
        self.spent_bout = 0
        self.spent_tier: dict[str, int] = {}

    def _record(self, request: SeatTurnRequestV1, tier: str, leg: RouteLeg | None, idx: int, **fields: Any) -> None:
        self.ledger.append(
            {
                "authority_effect": "None",
                "bout_id": self.bout_id,
                "candidate_id": request.candidate_id,
                "config_digest": self.config_digest,
                "day": self._today(),
                "leg_index": idx,
                "model": leg.model if leg else None,
                "request_digest": request.request_digest(),
                "round_index": request.round_index,
                "router": leg.router if leg else None,
                "seat_id": request.seat_id,
                "tier": tier,
                **fields,
            }
        )

    def execute(self, request: SeatTurnRequestV1) -> Result[SeatTurnReplyV1, Refusal]:
        return Err(Refusal("LEGACY_SEAT_TRANSPORT_RETIRED", "Use the PFP-mediated native bout or teamwork backend."))

    def _execute_legacy_fixture(self, request: SeatTurnRequestV1) -> Result[SeatTurnReplyV1, Refusal]:
        """Historical fixture oracle only; supported live entrypoints cannot select it."""
        route_r = self.table.seat(request.seat_id)
        if isinstance(route_r, Err):
            return route_r
        route = route_r.value
        if not route.calls_model:
            return Err(Refusal("SEAT_NOT_MODEL_BACKED", f"seat {route.seat_id!r} is {route.tier}"))

        system = SYSTEM_TEMPLATE.format(
            seat_id=request.seat_id,
            operator=request.cognitive_operator or "adversarial_retinue",
            scene_id=request.scene_id,
        )
        user = request.prompt_text
        if request.context_bytes:
            user += "\n\n[Candidate Context]:\n" + request.context_bytes.decode("utf-8", errors="replace")
        candidate = CandidateRequest(system=system, user=user)
        input_upper_bound = len(system.encode("utf-8")) + len(user.encode("utf-8"))

        max_in = self.table.budget.max_input_bytes_per_call
        if max_in is not None and input_upper_bound > max_in:
            self._record(
                request, route.tier, None, 0, outcome="INPUT_TOO_LARGE", cost_microusd=0,
                input_bytes=input_upper_bound, max_input_bytes=max_in,
            )
            return Err(
                Refusal("INPUT_TOO_LARGE", f"input {input_upper_bound} bytes exceeds per-call limit {max_in}")
            )

        failures: list[str] = []
        for idx, leg in enumerate(route.legs):
            transport = self.transports.get(leg.router)
            if transport is None:
                self._record(request, route.tier, leg, idx, outcome="ROUTER_UNCONFIGURED", cost_microusd=0)
                failures.append(f"{leg.router}:{leg.model}=ROUTER_UNCONFIGURED")
                continue
            reserve = self.table.budget.admission_reserve_output_tokens
            admission_tokens = (
                self.max_output_tokens if reserve is None else min(self.max_output_tokens, reserve)
            )
            worst = leg.worst_case_microusd(input_upper_bound, admission_tokens)
            admitted = admit_spend(
                spent_bout=self.spent_bout,
                spent_day=self.ledger.spent_on(self._today()),
                worst_case=worst,
                policy=self.table.budget,
                tier=route.tier,
                spent_tier=self.spent_tier.get(route.tier, 0),
            )
            if isinstance(admitted, Err):
                self._record(request, route.tier, leg, idx, outcome=admitted.error.code, cost_microusd=0, worst_case_microusd=worst)
                return admitted
            started = self._clock()
            try:
                raw = transport(leg.model, candidate, self.max_output_tokens)
                parsed = _parse(leg, raw)
            except Exception as exc:
                self.spent_bout += worst
                self.spent_tier[route.tier] = self.spent_tier.get(route.tier, 0) + worst
                self._record(request, route.tier, leg, idx, outcome="OUTCOME_UNKNOWN",
                    cost_microusd=worst, reported_cost_microusd=None,
                    cost_source="retained_worst_case", error=type(exc).__name__)
                return Err(Refusal("OUTCOME_UNKNOWN", "Reservation retained; fallback requires a new authorized run."))
            latency_ms = int((self._clock() - started) * 1000)
            self.spent_bout += parsed.cost_microusd
            self.spent_tier[route.tier] = self.spent_tier.get(route.tier, 0) + parsed.cost_microusd
            machine = parse_machine_block(parsed.content)
            if isinstance(machine, Ok) and machine.value["AUTHORITY_EFFECT"] != "None":
                self._record(request, route.tier, leg, idx, outcome="AUTHORITY_MINT_REFUSED", cost_microusd=parsed.cost_microusd, cost_source=parsed.cost_source, latency_ms=latency_ms)
                return Err(Refusal("AUTHORITY_MINT_REFUSED", f"{leg.model} returned AUTHORITY_EFFECT={machine.value['AUTHORITY_EFFECT']!r}"))
            outcome = "OK" if isinstance(machine, Ok) else "MALFORMED"
            fields = machine.value if isinstance(machine, Ok) else {}
            try:
                reply = SeatTurnReplyV1(
                    reply_text=parsed.content,
                    machine_fields=dict(fields),
                    residual_colour=fields.get("RESIDUAL_COLOUR", "Open"),
                    raw_bytes=raw,
                    model=parsed.model or leg.model,
                    provider=leg.router,
                    parameters={
                        "bout_id": self.bout_id,
                        "config_digest": self.config_digest,
                        "cost_microusd": parsed.cost_microusd,
                        "cost_source": parsed.cost_source,
                        "leg_index": idx,
                        "machine_block": outcome,
                        "max_tokens": self.max_output_tokens,
                        "tier": route.tier,
                    },
                    usage={"input_tokens": parsed.input_tokens, "output_tokens": parsed.output_tokens},
                    request_digest=request.request_digest(),
                )
            except (TypeError, ValueError) as exc:
                # The call was paid for, but the reply carries a value the contract rejects
                # (for example a negative token count). Record it; do not fabricate a reply.
                self._record(
                    request, route.tier, leg, idx,
                    outcome="REPLY_INVALID",
                    cost_microusd=parsed.cost_microusd,
                    cost_source=parsed.cost_source,
                    latency_ms=latency_ms,
                    error=type(exc).__name__,
                    max_tokens=self.max_output_tokens,
                    overshoot_microusd=max(0, self.spent_bout - self.table.budget.per_bout_microusd),
                )
                return Err(Refusal("REPLY_INVALID", f"{leg.model}: reply rejected by the seat-turn contract ({exc})"))
            self._record(
                request, route.tier, leg, idx,
                outcome=outcome,
                disposition=fields.get("DISPOSITION"),
                cost_microusd=parsed.cost_microusd,
                cost_source=parsed.cost_source,
                input_tokens=parsed.input_tokens,
                output_tokens=parsed.output_tokens,
                latency_ms=latency_ms,
                id_verified=leg.id_verified,
                admission_output_tokens=admission_tokens,
                finish_reason=parsed.finish_reason,
                ddc_letter=fields.get("DDC_LETTER"),
                residual_colour=fields.get("RESIDUAL_COLOUR"),
                reply_digest="sha256:" + hashlib.sha256(parsed.content.encode("utf-8")).hexdigest(),
                temperature_sent=None,
                max_tokens=self.max_output_tokens,
                overshoot_microusd=max(0, self.spent_bout - self.table.budget.per_bout_microusd),
            )
            return Ok(reply)
        return Err(Refusal("ALL_LEGS_FAILED", f"seat {route.seat_id!r}: " + "; ".join(failures)))

    def __call__(self, request: SeatTurnRequestV1) -> SeatTurnReplyV1:
        result = self.execute(request)
        if isinstance(result, Err):
            raise SeatTurnRefused(result.error)
        return result.value
