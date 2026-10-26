"""Not Yet Created Sentinel Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from .identity_contract_error import IdentityContractError
from .identity_slot_v1 import IdentitySlotV1


@dataclass(frozen=True, slots=True)
class NotYetCreated:
    slot: IdentitySlotV1

    def __post_init__(self) -> None:
        if type(self.slot) is not IdentitySlotV1:
            raise IdentityContractError("IDENTITY_SLOT_TYPE_REFUSED")
