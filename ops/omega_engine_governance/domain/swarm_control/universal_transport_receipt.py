from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any


class MutationShape(str, Enum):
    PATH_ONLY = "PATH_ONLY"
    CONTENT_CHANGED = "CONTENT_CHANGED"
    ADDED_REDIRECT = "ADDED_REDIRECT"
    DELETED = "DELETED"
    SPLIT = "SPLIT"
    MERGED = "MERGED"
    RESIDUAL = "RESIDUAL"


class TransportReceiptStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REFUSED = "REFUSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TransportReceiptError(Exception):
    """Raised when transport validation violates fail-closed rules."""
    pass


@dataclass(frozen=True, slots=True)
class UniversalTransportReceipt:
    receipt_id: str
    source_path: str
    destination_path: str | None
    mutation_shape: MutationShape
    source_digest: str | None
    destination_digest: str | None
    status: TransportReceiptStatus
    notes: str = ""

    def __post_init__(self) -> None:
        # Hard invariant: If locus changed (source != destination), NOT_APPLICABLE is forbidden
        if (
            self.destination_path is not None
            and self.source_path != self.destination_path
            and self.status == TransportReceiptStatus.NOT_APPLICABLE
        ):
            raise TransportReceiptError(
                f"Transport receipt '{self.receipt_id}' cannot be marked NOT_APPLICABLE when path changed "
                f"from '{self.source_path}' to '{self.destination_path}'"
            )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, UniversalTransportReceipt)
        return (
            self.receipt_id == other.receipt_id
            and self.source_path == other.source_path
            and self.destination_path == other.destination_path
            and self.mutation_shape == other.mutation_shape
            and self.source_digest == other.source_digest
            and self.destination_digest == other.destination_digest
            and self.status == other.status
            and self.notes == other.notes
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "mutation_shape": self.mutation_shape.value,
            "source_digest": self.source_digest,
            "destination_digest": self.destination_digest,
            "status": self.status.value,
            "notes": self.notes,
        }

    def compute_hash(self) -> str:
        canonical_json = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def create_transport_receipt(
    receipt_id: str,
    source_path: str,
    destination_path: str | None,
    source_digest: str | None,
    destination_digest: str | None,
    *,
    has_redirect: bool = False,
    is_deleted: bool = False,
    notes: str = "",
) -> UniversalTransportReceipt:
    """Classify the mutation shape and say whether the evidence supports it.

    Every branch used to end in ``VERIFIED``. ``REFUSED`` was unreachable, and
    ``create_transport_receipt(r, 'old/a.md', 'new/a.md', None, None)`` — a
    relocation with no digest measured on either side — was certified verified.
    That is the NOT_MEASURED-to-verified smuggle that
    ``evaluate_chaos_measurement_strict`` in this same package exists to refuse.

    The rule now: **a claim about content requires the content to have been
    measured.** Where a shape is a statement about bytes, absent digests are
    ``REFUSED``, not silently accepted.
    """
    if is_deleted or destination_path is None:
        shape = MutationShape.DELETED
        # A deletion is a claim about the source: it must have existed and been
        # measured. Nothing is claimed about a destination.
        status = (
            TransportReceiptStatus.VERIFIED
            if source_digest is not None
            else TransportReceiptStatus.REFUSED
        )
    elif has_redirect:
        shape = MutationShape.ADDED_REDIRECT
        # The redirect itself is the new artifact, so it is the one that must
        # be measured.
        status = (
            TransportReceiptStatus.VERIFIED
            if destination_digest is not None
            else TransportReceiptStatus.REFUSED
        )
    elif source_path != destination_path:
        if source_digest is None or destination_digest is None:
            # A move is a claim that something arrived. Unmeasured on either
            # side, the shape itself is unknown -- so do not guess at one.
            shape = MutationShape.RESIDUAL
            status = TransportReceiptStatus.REFUSED
        elif source_digest == destination_digest:
            shape = MutationShape.PATH_ONLY
            status = TransportReceiptStatus.VERIFIED
        else:
            shape = MutationShape.CONTENT_CHANGED
            status = TransportReceiptStatus.VERIFIED
    elif source_digest is None or destination_digest is None:
        shape = MutationShape.RESIDUAL
        status = TransportReceiptStatus.REFUSED
    elif source_digest != destination_digest:
        shape = MutationShape.CONTENT_CHANGED
        status = TransportReceiptStatus.VERIFIED
    else:
        # Same path, same bytes: nothing was transported. Previously labelled
        # PATH_ONLY, which reads as "this moved" about a file that did not.
        shape = MutationShape.RESIDUAL
        status = TransportReceiptStatus.NOT_APPLICABLE

    return UniversalTransportReceipt(
        receipt_id=receipt_id,
        source_path=source_path,
        destination_path=destination_path,
        mutation_shape=shape,
        source_digest=source_digest,
        destination_digest=destination_digest,
        status=status,
        notes=notes,
    )
