"""Shared runtime kernel for P1 and P2: typed refusal, receipt, certificate checker.

Skeleton only. The reference behaviour lives in the WDP package
(``code/witnessed_difference/receipts.py``, ``code/witnessed_difference/outcomes.py``,
``code/certified_progress/checker.py``); a kernel adapter must reproduce it, not
replace it. AuthorityEffect: None.
"""

from __future__ import annotations

import re
from typing import Literal, Protocol

from pydantic import Field, field_validator, model_validator

from omega_engine_applications.wdp_products.base import FrozenModel

SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
RATIONAL = re.compile(r"^-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?$")

CertificateClaim = Literal["LOSS", "WIN_OPTIMAL", "WIN_FEASIBLE"]


def is_rational_text(value: str) -> bool:
    """True for a canonical ``p`` or ``p/q`` string. Coprimality is the adapter's job."""
    return bool(RATIONAL.fullmatch(value))


class TypedRefusal(FrozenModel):
    """A refusal is an output, not an error path (WDP Ch. 2, App. G.3)."""

    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    reason: str = Field(min_length=1)
    authority_effect: Literal["None"] = "None"


class ReceiptRecord(FrozenModel):
    """Wire form of the six-field WDP receipt plus its fixed authority field.

    Mirrors ``witnessed_difference.receipts.Receipt``. ``claim_ids`` is sorted and
    distinct, as ``make_receipt`` normalises it.
    """

    subject: str = Field(min_length=1)
    input_digest: str
    output_digest: str
    claim_ids: tuple[str, ...] = Field(min_length=1)
    implementation_version: str = Field(min_length=1)
    receipt_digest: str
    authority_effect: Literal["None"] = "None"

    @field_validator("input_digest", "output_digest", "receipt_digest")
    @classmethod
    def _digest(cls, value: str) -> str:
        if not SHA256_HEX.fullmatch(value):
            raise ValueError("digest must be 64 lowercase hex characters")
        return value

    @field_validator("claim_ids")
    @classmethod
    def _claims(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if tuple(sorted(set(value))) != value or any(not item for item in value):
            raise ValueError("claim ids must be nonempty, distinct and sorted")
        return value


class CheckReceipt(FrozenModel):
    """What an independent checker returns after replaying a submitted certificate.

    Mirrors ``certified_progress.check_certificate``. An accepted receipt names the
    claim it replayed: an accepted win carries the checked exact ``initial_value``,
    an accepted loss records whether the initial belief is stalled (no admissible
    action). A rejected receipt names at least one failure and carries no claim.
    """

    accepted: bool
    model_digest: str
    certificate_digest: str
    claim: CertificateClaim | None = None
    initial_value: str | None = None
    initial_stalled: bool | None = None
    failures: tuple[str, ...] = ()
    authority_effect: Literal["None"] = "None"

    @field_validator("model_digest", "certificate_digest")
    @classmethod
    def _digest(cls, value: str) -> str:
        if not SHA256_HEX.fullmatch(value):
            raise ValueError("digest must be 64 lowercase hex characters")
        return value

    @model_validator(mode="after")
    def _shape(self) -> CheckReceipt:
        if not self.accepted:
            if not self.failures:
                raise ValueError("a rejected certificate names at least one failure")
            if (self.claim, self.initial_value, self.initial_stalled) != (None, None, None):
                raise ValueError("a rejected certificate carries no claim, value or stall flag")
            return self
        if self.failures:
            raise ValueError("an accepted certificate has no failures")
        if self.claim is None:
            raise ValueError("an accepted certificate names the claim it replayed")
        if self.claim == "LOSS":
            if self.initial_value is not None or self.initial_stalled is None:
                raise ValueError("an accepted loss records initial_stalled and no initial_value")
            return self
        if self.initial_stalled is not None:
            raise ValueError("an accepted win carries no stall flag")
        if self.initial_value is None or not is_rational_text(self.initial_value):
            raise ValueError("an accepted win records an exact rational initial_value")
        return self


class ReceiptIssuer(Protocol):
    """Binds inputs and output to a receipt; refuses what it cannot canonicalise."""

    def issue(
        self, subject: str, inputs: object, output: object, claim_ids: tuple[str, ...]
    ) -> ReceiptRecord | TypedRefusal: ...

    def verify(
        self, receipt: ReceiptRecord, inputs: object, output: object
    ) -> bool | TypedRefusal: ...


class CertificateChecker(Protocol):
    """Replays a submitted certificate against the declared model.

    Law: a checker never calls the producer and never substitutes its own answer
    for a bad certificate (WDP App. S.4; ``certified_progress.check_certificate``).
    """

    def check(self, model: object, certificate: object) -> CheckReceipt: ...


for _model in (TypedRefusal, ReceiptRecord, CheckReceipt):
    _model.model_rebuild()
