"""Routing file and DTO boundary to the native policy. AuthorityEffect: None."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.infrastructure.seat_transport.routing import (
    BudgetPolicy,
    RouteLeg,
    RoutingTable,
    SeatRoute,
)

from ..infrastructure.native import invoke

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "seat_routing_v1.yaml"


def _table(record: dict) -> RoutingTable:
    policy = dict(record["budget"])
    policy["tier_per_bout_microusd"] = tuple(
        tuple(pair) for pair in policy["tier_per_bout_microusd"]
    )
    seats = []
    for seat in record["seats"]:
        legs = []
        for leg in seat["legs"]:
            fields = dict(leg)
            for key in ("input_microusd_per_token", "output_microusd_per_token"):
                fields[key] = Fraction(fields[key])
            legs.append(RouteLeg(**fields))
        seats.append(SeatRoute(seat["seat_id"], seat["tier"], tuple(legs)))
    return RoutingTable(
        record["version"],
        record["primary_router"],
        Fraction(record["cheap_share_min"]),
        BudgetPolicy(**policy),
        tuple(seats),
    )


def parse_routing(data: Any) -> Result[RoutingTable, Refusal]:
    result = invoke("routing_parse", routing_json=json.dumps(data, ensure_ascii=False))
    return result if isinstance(result, Err) else Ok(_table(result.value))


def load_routing(path: Path) -> Result[tuple[RoutingTable, str], Refusal]:
    result = invoke("routing_load", path=str(path))
    return (
        result
        if isinstance(result, Err)
        else Ok((_table(result.value["table"]), result.value["config_digest"]))
    )
