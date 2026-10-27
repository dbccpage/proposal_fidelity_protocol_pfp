"""The calculus receipt: what the producer claimed, what the host re-derived.

WP-5 of the OEv1.0 Symbol Game build, and the shape the whole design turns on.
A producer-authored ``verified: true`` is a sentence. This module records, per
row, what the host independently derived -- and, where it derived nothing, why.

Three outcomes, not a boolean
-----------------------------

The obvious modelling is ``host_rederived: bool``. It is wrong, and the way it
is wrong matters for every statistic built on top of it. A false value would
mean two different things:

* the host recomputed the row and got a **different answer** -- the producer
  said something untrue; and
* the host **could not check** the row at all, because the producer did not
  supply the fields the check needs.

Collapsing those makes the host's own blind spot look like the producer's
dishonesty, and inflates any hallucination rate by exactly the amount the host
cannot see. So rows carry :class:`RowOutcome` with three values, and
``host_rederived`` is kept only as the derived boolean the schema needs.

The blind spot is named, not implied
------------------------------------

``[TAU]`` is a ``SELECT``. It names the columns the host will read, so what it
omits is precisely what the host structurally cannot check. An ``UNCHECKABLE``
row therefore records *which fields it did not receive*, which is the difference
between "we did not check that" and "we cannot know what we did not check".

A row that cannot be admitted is still a row
--------------------------------------------

There is a fourth outcome, ``REFUSED``, and it exists because its absence was a
defect. This module used to *raise* when handed an op outside the closed set,
which forced the caller to drop the row -- and a receipt over the surviving rows
returned ``PASS``. The linter's refusal was laundered into a pass by the
datatype. A receipt must be able to represent a row it could not admit, or the
rows it cannot admit disappear.

Dropping rows is closed separately, because representability alone does not stop
a caller from omitting one. The receipt carries ``declared_row_count`` -- how
many rows the producer emitted -- as a **required** argument, so a caller has to
confront the question, and a receipt that does not account for every declared
row refuses whatever its surviving rows say.

The terminal is a terminal
--------------------------

A row the host could not replay cannot license a positive terminal. That is
enforced here as a verdict, not surfaced as a warning:

====================  =========================================================
unaccounted rows      ``REFUSE`` -- the receipt does not cover its own ledger
any CONTRADICTED      ``REFUSE`` -- the host holds a different answer
any REFUSED           ``REFUSE`` -- the host declined to admit the row
any UNCHECKABLE       ``OPEN_RESIDUAL`` -- nothing is known to be wrong, and
                      nothing is established either
all REDERIVED, and    ``SELF_CONSISTENT_ONLY`` -- every row agrees with a
the carrier came      carrier the packet chose
with the packet
all REDERIVED         ``PASS``
====================  =========================================================

Who authored the carrier
------------------------

``PASS`` used to be reachable by a packet that declared its own carrier, and
that made it a much weaker claim than it read as: the rows were checked against
an allowlist the same producer wrote, so what was established was that the
packet agrees with itself. A producer wanting a clean receipt had only to widen
its carrier.

So the receipt records :class:`CarrierAuthority`, and a run whose carrier came
with the packet tops out at ``SELF_CONSISTENT_ONLY``. Nothing is wrong with such
a run and nothing is hidden -- the rows really do re-derive -- but the word for
that is consistency, not verification.

``OPEN_RESIDUAL`` is deliberately NOT qualified this way. It already establishes
nothing, so there is nothing in it for a carrier to have established. The same
rule holds on the Rust side, where a `NeedsEvidence` peak verdict is likewise
left alone and only decisions are downgraded.

A refusal is not a hallucination. The host never formed a contrary opinion; it
declined to admit the row. Counting that against the producer would inflate the
rate with the host's own admission policy.

AuthorityEffect: None. A ``PASS`` here says the host re-derived every row it was
given. It is not a promotion, and ``LocalGreen`` is not ``GlobalGreen``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum

from .glyph_calculus import CLOSED_OPS, Carrier

__all__ = [
    "CALCULUS_RECEIPT_SCHEMA",
    "CalculusReceipt",
    "CarrierAuthority",
    "ReceiptRow",
    "RowOutcome",
    "Terminal",
    "carrier_digest",
]

CALCULUS_RECEIPT_SCHEMA = "core.glyph_receipt.draft.v1"


class RowOutcome(str, Enum):
    """What the host managed to establish about one row."""

    #: Host recomputed the claim and agreed.
    REDERIVED = "rederived"
    #: Host recomputed the claim and got something else.
    CONTRADICTED = "contradicted"
    #: Host could not recompute: the row did not supply what the check needs.
    UNCHECKABLE = "uncheckable"
    #: Row was refused before any check could run -- an op outside the closed
    #: set, a carrier violation, a malformed field.
    #:
    #: This outcome exists because the alternative was worse. Refusing to
    #: *construct* such a row forced the caller to drop it, and a receipt over
    #: the surviving rows returned PASS: the refusal was laundered into a pass
    #: by the datatype. A receipt must be able to represent a row it could not
    #: admit, or the rows it cannot admit disappear.
    REFUSED = "refused"


class CarrierAuthority(str, Enum):
    """Who authored the carrier the host checked the rows against.

    The distinction the whole terminal turns on. `HOST` means the host brought
    its own carrier and confirmed the packet declares the same one; `PRODUCER`
    means the only carrier in play arrived with the rows it licenses.

    There is deliberately no packet field for this, and there must not be one.
    A packet that could declare its carrier host-authored would be the claim
    vouching for itself, which is the entire defect. The value is set by the
    caller from what it actually did -- and it defaults DOWN, exactly as the
    decode tier does, because a caller that says nothing has said nothing.
    """

    #: The host supplied the carrier and the packet's matches it.
    HOST = "host"
    #: The carrier arrived with the packet.
    PRODUCER = "producer"


class Terminal(str, Enum):
    PASS = "PASS"
    #: Every row re-derived -- against a carrier the packet supplied. True, and
    #: a strictly weaker claim than PASS. See :class:`CarrierAuthority`.
    SELF_CONSISTENT_ONLY = "SELF_CONSISTENT_ONLY"
    OPEN_RESIDUAL = "OPEN_RESIDUAL"
    REFUSE = "REFUSE"


def carrier_digest(carrier: Carrier) -> str:
    """SHA-256 over the carrier's declared members, in declaration order.

    Digests the *codepoints*, not the rendered glyphs, so a homoglyph
    substitution changes the digest even where it would not change the page.

    The canonical form is JSON rather than a delimiter-joined string. Joining
    with ``:`` and a newline made the encoding **injectable**: a symbol
    containing those delimiters could reproduce another carrier's serialisation
    exactly, so two different carriers digested the same. A digest whose
    pre-image is ambiguous is not a digest of the thing it names. JSON escapes
    the delimiters, so distinct member lists always produce distinct bytes.
    """
    canonical = json.dumps(
        [[member.symbol, f"U+{ord(member.char):04X}"] for member in carrier.members],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ReceiptRow:
    """One ledger row, with the producer's claim and the host's finding kept apart."""

    index: int
    op: str
    statement: str
    evidence_ref: str
    producer_claimed_valid: bool
    outcome: RowOutcome
    #: What the host derived, when it could derive anything.
    host_value: str | None = None
    #: Fields the row did not supply. Populated only for UNCHECKABLE rows: this
    #: is the blind spot, named.
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    #: Why the row was refused. Required for, and only for, REFUSED rows.
    refusal_code: str | None = None

    def __post_init__(self) -> None:
        if self.outcome is RowOutcome.REFUSED:
            if not self.refusal_code:
                raise ValueError(
                    f"row {self.index} is REFUSED but names no refusal code; an "
                    "unexplained refusal is not auditable"
                )
        elif self.refusal_code:
            raise ValueError(
                f"row {self.index} carries refusal code {self.refusal_code!r} but "
                f"was {self.outcome.value}"
            )
        if self.op not in CLOSED_OPS and self.outcome is not RowOutcome.REFUSED:
            # Still refused, but as a *programming* error rather than a data
            # one: an undeclared op is producer data and must be represented
            # as a REFUSED row, never dropped and never silently admitted.
            raise ValueError(
                f"row {self.index} declares op {self.op!r}, which is not in the "
                "closed set; construct it with ReceiptRow.refused(...) so the "
                "refusal appears in the receipt instead of vanishing from it"
            )
        if self.outcome is RowOutcome.UNCHECKABLE and not self.missing_fields:
            raise ValueError(
                f"row {self.index} is UNCHECKABLE but names no missing fields; an "
                "unnamed blind spot is the thing this receipt exists to prevent"
            )
        if self.outcome is not RowOutcome.UNCHECKABLE and self.missing_fields:
            raise ValueError(
                f"row {self.index} names missing fields but was {self.outcome.value}"
            )

    @classmethod
    def refused(
        cls,
        index: int,
        op: str,
        statement: str,
        evidence_ref: str,
        producer_claimed_valid: bool,
        refusal_code: str,
    ) -> "ReceiptRow":
        """A row the host refused to admit, kept IN the receipt.

        The op is recorded exactly as the producer wrote it, including when it
        is outside the closed set. A receipt that renders an undeclared op as
        something declared would be a second forgery on top of the first.
        """
        return cls(
            index=index,
            op=op,
            statement=statement,
            evidence_ref=evidence_ref,
            producer_claimed_valid=producer_claimed_valid,
            outcome=RowOutcome.REFUSED,
            refusal_code=refusal_code,
        )

    @property
    def host_rederived(self) -> bool:
        return self.outcome is RowOutcome.REDERIVED

    @property
    def is_hallucination(self) -> bool:
        """Claimed true, and the host holds a different answer.

        Deliberately **not** ``claimed and not host_rederived``. An
        ``UNCHECKABLE`` row is a claim the host has no opinion about, and
        counting it here would charge the producer for the host's blind spot.
        """
        return self.producer_claimed_valid and self.outcome is RowOutcome.CONTRADICTED

    @property
    def is_unverified_claim(self) -> bool:
        """Claimed true, and the host could not check it. Not a lie; not evidence."""
        return self.producer_claimed_valid and self.outcome is RowOutcome.UNCHECKABLE

    def to_wire(self) -> dict[str, object]:
        wire: dict[str, object] = {
            "index": self.index,
            "op": self.op,
            "statement": self.statement,
            "evidence_ref": self.evidence_ref,
            "producer_claimed_valid": self.producer_claimed_valid,
            "host_rederived": self.host_rederived,
            "host_outcome": self.outcome.value,
        }
        if self.host_value is not None:
            wire["host_value"] = self.host_value
        if self.missing_fields:
            wire["host_missing_fields"] = list(self.missing_fields)
        if self.refusal_code:
            wire["refusal_code"] = self.refusal_code
        return wire


@dataclass(frozen=True, slots=True)
class CalculusReceipt:
    """A whole run: the carrier it ran over, and every row's fate."""

    carrier_digest: str
    rows: tuple[ReceiptRow, ...]
    #: How many rows the producer emitted, independently of how many this
    #: receipt managed to represent.
    declared_row_count: int
    #: Who authored the carrier every row above was checked against.
    carrier_authored_by: CarrierAuthority

    @classmethod
    def over(
        cls,
        carrier: Carrier,
        rows: Sequence[ReceiptRow],
        *,
        declared_row_count: int,
        carrier_authored_by: CarrierAuthority,
    ) -> "CalculusReceipt":
        """Build a receipt over `rows`, out of a ledger of `declared_row_count`.

        `declared_row_count` is a required keyword on purpose. Defaulting it to
        `len(rows)` would make the count agree with itself by construction and
        re-open the hole it exists to close: a caller that drops the rows it
        could not build would produce a receipt that looks complete.

        `carrier_authored_by` is required for the same reason and would be more
        dangerous to default. Defaulting it to `HOST` hands every caller a
        `PASS` it did not earn; defaulting it to `PRODUCER` is safe but silently
        caps a host that really did pin its carrier. Neither is a decision this
        constructor is in a position to make, so it declines to make one.
        """
        return cls(
            carrier_digest=carrier_digest(carrier),
            rows=tuple(rows),
            declared_row_count=declared_row_count,
            carrier_authored_by=carrier_authored_by,
        )

    @property
    def unaccounted_rows(self) -> int:
        """Ledger rows the producer emitted that this receipt does not contain."""
        return max(0, self.declared_row_count - len(self.rows))

    @property
    def terminal(self) -> Terminal:
        """A verdict, not a warning.

        Order matters: knowing something is wrong outranks not knowing. A
        refused row and a contradicted row both mean the host holds a positive
        objection, so both refuse.
        """
        if self.unaccounted_rows:
            # Rows went missing between the ledger and the receipt. Whatever
            # they said, a receipt that does not account for them cannot
            # license anything -- and silence here is exactly how a refusal
            # used to become a pass.
            return Terminal.REFUSE
        if any(
            row.outcome in (RowOutcome.CONTRADICTED, RowOutcome.REFUSED)
            for row in self.rows
        ):
            return Terminal.REFUSE
        if any(row.outcome is RowOutcome.UNCHECKABLE for row in self.rows):
            # Not qualified by carrier authorship. A run that established
            # nothing has nothing for a carrier to have established, so
            # downgrading it would report "self-consistent" over rows the host
            # never checked -- which is a stronger claim than the truth, in the
            # one direction this module must never move.
            return Terminal.OPEN_RESIDUAL
        if not self.rows:
            return Terminal.OPEN_RESIDUAL
        if self.carrier_authored_by is CarrierAuthority.PRODUCER:
            # Every row re-derived against an allowlist the packet wrote. The
            # rows agree with the carrier and the carrier agrees with the rows;
            # a producer wanting this outcome need only widen its carrier.
            return Terminal.SELF_CONSISTENT_ONLY
        return Terminal.PASS

    @property
    def refused_rows(self) -> tuple[ReceiptRow, ...]:
        return tuple(row for row in self.rows if row.outcome is RowOutcome.REFUSED)

    @property
    def hallucinations(self) -> tuple[ReceiptRow, ...]:
        return tuple(row for row in self.rows if row.is_hallucination)

    @property
    def unverified_claims(self) -> tuple[ReceiptRow, ...]:
        return tuple(row for row in self.rows if row.is_unverified_claim)

    @property
    def blind_spot(self) -> tuple[str, ...]:
        """Every field any row failed to supply, deduplicated and sorted.

        The union of what `[TAU]` selected away. A reader can see the shape of
        what was never checkable, rather than inferring it from silence.
        """
        names: set[str] = set()
        for row in self.rows:
            names.update(row.missing_fields)
        return tuple(sorted(names))

    def to_wire(self) -> dict[str, object]:
        return {
            "schema": CALCULUS_RECEIPT_SCHEMA,
            "carrier_digest": self.carrier_digest,
            "carrier_authored_by": self.carrier_authored_by.value,
            "operations": [row.to_wire() for row in self.rows],
            "declared_row_count": self.declared_row_count,
            "represented_row_count": len(self.rows),
            "unaccounted_rows": self.unaccounted_rows,
            "refused_row_count": len(self.refused_rows),
            "terminal_status": self.terminal.value,
            "host_blind_spot": list(self.blind_spot),
            "hallucination_count": len(self.hallucinations),
            "unverified_claim_count": len(self.unverified_claims),
            "authority_effect": "None",
        }
