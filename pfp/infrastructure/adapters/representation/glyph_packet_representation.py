"""Glyph Packet Representation Adapter (U25).

Encodes TurnView as a structured JSON/glyph packet.
AuthorityEffect: None.
"""
from __future__ import annotations

import json
from typing import Any

from omega_engine_pfp.domain.representation.models import TurnView
from omega_engine_pfp.domain.representation.ports import RepresentationPort


class GlyphPacketRepresentation(RepresentationPort):
    """Encodes TurnView into canonical compact JSON glyph packet."""

    @property
    def representation_id(self) -> str:
        return "GLYPH_PACKET"

    def render(self, view: TurnView) -> str:
        packet = {
            "header": "GLYPH_PACKET_V1",
            "round_seq": view.round_seq,
            "metrics": {
                "phi1": view.phi1,
                "gamma2": view.gamma2,
            },
            "open_constraints": [
                {"name": k, "expr": v} for k, v in view.open_constraints
            ],
            "decided_values": [
                {"name": k, "value": v} for k, v in view.decided_values
            ],
            "refused_moves": [
                {"move": k, "reason": v} for k, v in view.refused_moves
            ],
            "prompt_regime": view.prompt_regime,
            "authority_effect": view.authority_effect,
        }
        return json.dumps(packet, sort_keys=True, indent=2)

    def parse(self, rendered: str) -> TurnView:
        data = json.loads(rendered)
        if data.get("header") != "GLYPH_PACKET_V1":
            raise ValueError(f"Invalid glyph packet header: {data.get('header')}")

        metrics = data.get("metrics", {})
        open_constraints = tuple(
            (item["name"], item["expr"]) for item in data.get("open_constraints", [])
        )
        decided_values = tuple(
            (item["name"], int(item["value"])) for item in data.get("decided_values", [])
        )
        refused_moves = tuple(
            (item["move"], item["reason"]) for item in data.get("refused_moves", [])
        )

        return TurnView(
            round_seq=int(data["round_seq"]),
            phi1=int(metrics["phi1"]),
            gamma2=int(metrics["gamma2"]),
            open_constraints=open_constraints,
            decided_values=decided_values,
            refused_moves=refused_moves,
            prompt_regime=str(data["prompt_regime"]),
            authority_effect=str(data.get("authority_effect", "None")),
        )
