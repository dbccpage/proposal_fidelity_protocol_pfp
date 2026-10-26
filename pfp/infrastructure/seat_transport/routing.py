"""Fixed per-seat model routing for Symbol Game seat transports (used by the Woland retinue).

Each seat that calls a model has one primary router and an ordered list of at
least three models from three different vendors on that router, followed by
optional fallback-router legs. Seats that run local code make no model call.

Money is exact: prices are micro-USD per token as ``Fraction`` (a price of
2 USD per million tokens is 2 micro-USD per token), and spend is integer
micro-USD. AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from fractions import Fraction
from typing import Any

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

_LOCUS = "omega_engine_pfp.infrastructure.seat_transport.routing"


def invoke(operation: str, **payload: Any) -> Result[Any, Refusal]:
    """Run one ``woland_support`` routing operation on the native host."""
    response = RustSymbolGameHost().invoke_runtime_with_file(
        "woland_support", {"operation": operation, **payload}, file_action="woland_support_file"
    )
    if isinstance(response, Err):
        return response
    envelope = response.value
    if not envelope["success"]:
        return Err(Refusal("SEAT_ROUTING_NATIVE_DISPATCH_FAILED", str(envelope["error"]), _LOCUS))
    reply = envelope["result"]
    if reply["refusal"] is not None:
        error = reply["refusal"]
        return Err(Refusal(error["code"], error["message"], error.get("locus", _LOCUS)))
    return Ok(reply["outcome"])


def value(operation: str, **payload: Any) -> Any:
    result = invoke(operation, **payload)
    if isinstance(result, Err):
        error = result.error
        if error.code == "WOLAND_EVIDENCE_TYPE_ERROR":
            raise TypeError(error.message)
        raise ValueError(error.message)
    return result.value


def wire_json(item: Any) -> str:
    def wire(node: Any) -> Any:
        if isinstance(node, Fraction):
            return str(node)
        if is_dataclass(node) and not isinstance(node, type):
            return wire(asdict(node))
        if isinstance(node, dict):
            return {key: wire(v) for key, v in node.items()}
        if isinstance(node, (tuple, list)):
            return [wire(v) for v in node]
        return node

    return json.dumps(wire(item), ensure_ascii=False)

LLM_TIERS = ("cheap", "strong")
NON_LLM_TIERS = ("deterministic", "inactive")
TIERS = LLM_TIERS + NON_LLM_TIERS
MIN_PRIMARY_MODELS = 3


def canonical_seat_key(seat_id: str) -> str:
    """Map a display name ("The Master") or runtime id ("seat_the_master") to one key."""
    return value("routing_key", seat_id=seat_id)


@dataclass(frozen=True)
class RouteLeg:
    """One (router, model) attempt with its declared prices."""

    router: str
    model: str
    input_microusd_per_token: Fraction
    output_microusd_per_token: Fraction
    id_verified: bool = True

    @property
    def vendor(self) -> str:
        return self.model.split("/", 1)[0] if "/" in self.model else self.router

    def worst_case_microusd(self, input_tokens: int, max_output_tokens: int) -> int:
        return int(
            value(
                "routing_cost",
                leg_json=wire_json(self),
                input_tokens=input_tokens,
                output_tokens=max_output_tokens,
            )
        )

    def cost_microusd(self, input_tokens: int, output_tokens: int) -> int:
        return self.worst_case_microusd(input_tokens, output_tokens)


@dataclass(frozen=True)
class SeatRoute:
    seat_id: str
    tier: str
    legs: tuple[RouteLeg, ...] = ()

    @property
    def calls_model(self) -> bool:
        return self.tier in LLM_TIERS


@dataclass(frozen=True)
class BudgetPolicy:
    """Caps in integer micro-USD.

    ``admission_reserve_output_tokens`` (optional) is the output length assumed when
    admitting a call; the request may still allow more. The receipt cost is debited
    afterwards, so a cap can be passed by at most one call's overshoot, which the
    ledger records. ``None`` means strict worst-case admission at the request's
    ``max_tokens``.
    """

    per_bout_microusd: int
    per_day_microusd: int
    admission_reserve_output_tokens: int | None = None
    tier_per_bout_microusd: tuple[tuple[str, int], ...] = ()
    max_input_bytes_per_call: int | None = None

    def tier_cap(self, tier: str) -> int | None:
        return dict(self.tier_per_bout_microusd).get(tier)


@dataclass(frozen=True)
class RoutingTable:
    version: str
    primary_router: str
    cheap_share_min: Fraction
    budget: BudgetPolicy
    seats: tuple[SeatRoute, ...]

    def seat(self, seat_id: str) -> Result[SeatRoute, Refusal]:
        result = invoke("routing_seat", table_json=wire_json(self), seat_id=seat_id)
        if isinstance(result, Err):
            return result
        return Ok(next(route for route in self.seats if route.seat_id == result.value["seat_id"]))

    def cheap_share(self) -> Fraction:
        return Fraction(value("routing_share", table_json=wire_json(self)))


def _refuse(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code, message))


def validate_table(table: RoutingTable) -> Result[RoutingTable, Refusal]:
    """Rust checks routing invariants; return the caller's original DTO."""
    result = invoke("routing_validate", table_json=wire_json(table))
    return result if isinstance(result, Err) else Ok(table)


def admit_spend(
    *,
    spent_bout: int,
    spent_day: int,
    worst_case: int,
    policy: BudgetPolicy,
    tier: str = "",
    spent_tier: int = 0,
) -> Result[None, Refusal]:
    """Rust checks the bout, tier and day budgets using exact integer spend."""
    return invoke(
        "routing_spend",
        policy_json=wire_json(policy),
        spent_bout=spent_bout,
        spent_day=spent_day,
        worst_case=worst_case,
        tier=tier,
        spent_tier=spent_tier,
    )
