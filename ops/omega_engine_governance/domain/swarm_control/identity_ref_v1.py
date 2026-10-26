"""Identity Ref V1 Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from .identity_contract_error import IdentityContractError
from .identity_domain_v1 import IdentityDomainV1

_SCHEMA_RE = re.compile(r"^[a-z0-9_.-]{1,64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ZERO_DIGEST = "0" * 64
MAX_IDENTITY_SCHEMA_CHARS = 64


def _require_exact_enum(value: object, enum_type: type[Enum], code: str) -> None:
    if type(value) is not enum_type:
        raise IdentityContractError(code)


@dataclass(frozen=True, slots=True)
class IdentityRefV1:
    domain: IdentityDomainV1
    schema: str
    digest: str

    def __post_init__(self) -> None:
        if type(self) is not IdentityRefV1:
            raise IdentityContractError("IDENTITY_REF_SUBCLASS_REFUSED")
        _require_exact_enum(
            self.domain, IdentityDomainV1, "IDENTITY_DOMAIN_TYPE_REFUSED"
        )
        if (
            type(self.schema) is not str
            or len(self.schema) > MAX_IDENTITY_SCHEMA_CHARS
            or _SCHEMA_RE.fullmatch(self.schema) is None
        ):
            raise IdentityContractError("IDENTITY_SCHEMA_REFUSED")
        if (
            type(self.digest) is not str
            or _DIGEST_RE.fullmatch(self.digest) is None
            or self.digest == _ZERO_DIGEST
        ):
            raise IdentityContractError("IDENTITY_DIGEST_REFUSED")
