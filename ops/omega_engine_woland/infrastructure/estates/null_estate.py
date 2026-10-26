"""Null estate adapter: an explicit, visible disconnection.

It stands in for any port. Every call returns a typed ``ESTATE_DISCONNECTED`` refusal
and the probe reports ``connected=False``. The composition root uses it only when the
caller asks for a port to be disconnected; it is never a silent default.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from omega_engine_operations.domain.rop.result import Err, Refusal
from omega_engine_woland.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from omega_engine_woland.domain.specialization import PortName

_LOCUS = "omega_engine_woland.infrastructure.estates.null_estate"


class NullEstateAdapter:
    adapter_id = "null"

    def __init__(self, estate: EstateName, port: PortName) -> None:
        self.estate = estate
        self.port = port

    def _refused(self, *_args: Any, **_kwargs: Any) -> Err[Refusal]:
        return Err(
            Refusal(
                "ESTATE_DISCONNECTED",
                f"{self.port.value} is disconnected from {self.estate.value}",
                _LOCUS,
            )
        )

    execute_bout = _refused
    evaluate = _refused
    record_candidates = _refused
    admitted_guidance = _refused
    record_lineage = _refused
    record_turn = _refused
    persist = _refused

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        return disconnected(self.estate, self.port, self.adapter_id, "null adapter")


__all__ = ["NullEstateAdapter"]
