"""Connection receipts: what an estate adapter actually did when probed.

A probe performs one real round trip against the estate inside a scratch root and reads
the estate's own store back. ``connected`` is true only when that effect was observed;
``effect_digest`` is then the SHA-256 of the observed bytes. Null adapters always report
``connected=False``. A receipt carries no authority.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .specialization import PortName

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class EstateName(str, Enum):
    STAGE = "adversary.stage"
    SYMBOL_GAME = "pfp"
    OEEIS = "eis"
    OEWAS = "operads"
    PROMPT_CIVILIZATION = "pciv"
    #: Local run custody under the resolved intelligence root (not an OEOS call).
    INTELLIGENCE_CUSTODY = "_intelligence"
    CRATES_RS = "engine/crates_rs"


@dataclass(frozen=True, slots=True)
class ConnectionReceiptV1:
    estate: EstateName
    port: PortName
    adapter_id: str
    connected: bool
    effect_digest: str | None
    detail: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("connection receipts carry no authority")
        if type(self.estate) is not EstateName or type(self.port) is not PortName:
            raise TypeError("estate and port must be EstateName and PortName")
        if type(self.connected) is not bool:
            raise TypeError("connected must be an exact bool")
        if not isinstance(self.adapter_id, str) or not self.adapter_id:
            raise ValueError("adapter_id must be a non-empty string")
        if self.connected:
            if not isinstance(self.effect_digest, str) or _SHA256.fullmatch(self.effect_digest) is None:
                raise ValueError("a connected receipt needs the sha256 of the observed effect")
        elif self.effect_digest is not None:
            raise ValueError("a disconnected receipt cannot carry an effect digest")


def disconnected(estate: EstateName, port: PortName, adapter_id: str, detail: str) -> ConnectionReceiptV1:
    return ConnectionReceiptV1(estate, port, adapter_id, False, None, detail)


__all__ = ["ConnectionReceiptV1", "EstateName", "disconnected"]
