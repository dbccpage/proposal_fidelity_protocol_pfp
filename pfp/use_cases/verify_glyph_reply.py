"""Verify a glyph-calculus reply end to end, and emit the receipt.

This is the caller the analyzer, the receipt and the decode tiers were missing.
Each of `lint_rows`, `Carrier`, `CalculusReceipt` and `DecodingReceipt` was
tested library code that nothing in the repository invoked -- and tested is not
wired. A check nobody calls defends nothing, however green its own suite is.

The pipeline, in the order a host must run it:

1. **Strict parse.** Duplicate keys and undeclared fields are refused before any
   meaning is taken from the packet. A packet whose reading depends on which
   parser read it is not a packet.
2. **Carrier pin.** The declared carrier is an allowlist of exact codepoints --
   and, where the caller supplied one, the host's own carrier is what the rows
   are checked against, with a disagreement refused rather than resolved.
3. **Op lint.** Every ledger row opens with one op from the closed set.
4. **Receipt.** One row per ledger row, carrying what the producer claimed and
   what the host established -- including the rows it refused, which is what
   stops a refusal disappearing into a `PASS`.
5. **Emission check.** What the decode tier was, and whether the reply stayed
   inside the carrier regardless.

On the carrier the host checks against
-------------------------------------

Pass `host_carrier` and the run is a verification: the host brought the
allowlist, confirmed the packet declares the same one, and a `PASS` means the
rows agree with a carrier the host pins.

Omit it and the run is a consistency check. The rows are checked against an
allowlist the same producer wrote, so the strongest available terminal is
`SELF_CONSISTENT_ONLY` -- true, and a much weaker claim than `PASS` reads as. A
producer wanting a clean receipt need only widen its own carrier.

There is deliberately no packet field for this. `PACKET_FIELDS` does not list
one and `check_no_unknown_fields` refuses anything it does not list, so a packet
cannot declare its carrier host-authored: the host's carrier reaches this
function as an argument or not at all. That is the same enforcement the Rust
side gets from `PresentationPins` deriving no `Deserialize`.

What this function can and cannot decide
---------------------------------------

Rows are re-derived by :mod:`..domain.row_rederivation`, which today decides
exactly one form -- modular reduction, `REDUCE 17 mod 5 = 2`. Everything else is
`UNCHECKABLE` with the blind spot named, which is the honest answer and not a
failure.

That one decider is what makes the terminal ladder reachable. Before it, every
admitted row was `UNCHECKABLE`, so every clean run landed on `OPEN_RESIDUAL` and
`PASS`, `SELF_CONSISTENT_ONLY` and the whole hallucination count were
structurally unreachable -- a receipt that could only ever say "I could not check
this", and a hallucination count that was always zero for reasons having nothing
to do with the producer.

A ledger mixing decidable and undecidable rows still terminates at
`OPEN_RESIDUAL`: one unchecked row is enough to establish that not everything
was established. Reaching `PASS` requires every row decidable, every row agreed,
AND a host-supplied carrier.

AuthorityEffect: None. A `PASS` says the host re-derived every row it was given,
against a carrier the host itself supplied.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..domain.calculus_receipt import (
    CalculusReceipt,
    CarrierAuthority,
    ReceiptRow,
    RowOutcome,
    Terminal,
    carrier_digest,
)
from ..domain.carrier_decoding import ConstraintMode, DecodingReceipt
from ..domain.glyph_calculus import (
    REFUSAL_CARRIER_CODEPOINT,
    REFUSAL_CARRIER_MISMATCH,
    REFUSAL_OP_UNDECLARED,
    REFUSAL_STATEMENT_ILL_FORMED,
    Carrier,
    Finding,
    check_no_duplicate_keys,
    check_no_unknown_fields,
    lint_ledger_row,
)
from ..domain.presentation_pins import PresentationPins
from ..domain.row_rederivation import DeciderContext, rederive_statement, split_row

__all__ = ["GlyphReplyVerdict", "PACKET_FIELDS", "verify_glyph_reply"]

#: The fields a glyph-calculus packet may declare. Anything else is refused
#: rather than ignored, because an ignored field is one a reader believes is
#: load-bearing while it is inert.
PACKET_FIELDS = (
    "schema",
    "carrier",
    "rows",
    "provider",
    "reply_text",
    "constraint_applied",
    #: The NAME of a rewrite presentation, resolved against the HOST's pins.
    #: A name is not content: there is deliberately no field by which a packet
    #: can supply rules, so naming one it likes buys a producer nothing except
    #: the chance that this host pins the same name. An unpinned name is a
    #: blind spot, not a refusal -- the row may be about something legitimate
    #: this estate simply does not pin.
    "presentation_ref",
)


@dataclass(frozen=True, slots=True)
class GlyphReplyVerdict:
    """Everything the host established, and nothing it did not."""

    receipt: CalculusReceipt | None
    decoding: DecodingReceipt | None
    parse_findings: tuple[Finding, ...]

    @property
    def terminal(self) -> Terminal:
        # A packet that would not parse never reached the receipt stage, so
        # there is nothing to license and the refusal stands on its own.
        if self.parse_findings:
            return Terminal.REFUSE
        if self.receipt is None:
            return Terminal.REFUSE
        if self.decoding is not None and not self.decoding.emission_within_carrier:
            return Terminal.REFUSE
        return self.receipt.terminal

    def to_wire(self) -> dict[str, object]:
        wire: dict[str, object] = {
            "terminal_status": self.terminal.value,
            "parse_findings": [str(finding) for finding in self.parse_findings],
            "authority_effect": "None",
        }
        if self.receipt is not None:
            wire["calculus_receipt"] = self.receipt.to_wire()
        if self.decoding is not None:
            wire["decoding"] = self.decoding.to_wire()
        return wire


def verify_glyph_reply(
    packet: Mapping[str, object],
    *,
    host_carrier: Carrier | None = None,
    host_presentations: PresentationPins | None = None,
    packet_pairs: Sequence[tuple[str, object]] | None = None,
) -> GlyphReplyVerdict:
    """Run the whole host-side check over one packet.

    `host_carrier` is the carrier the HOST pins. Supply it and the packet's
    declared carrier must be the same one, byte for byte at the codepoint
    level, or the run refuses. Omit it and the run can establish consistency
    but not verification -- see the module docstring.

    `host_presentations` is the pin registry this host recognises. The packet's
    `presentation_ref` is resolved against it and never against anything the
    packet supplied; omit it and every row about a presentation reports
    `UNCHECKABLE` with the blind spot named.

    `packet_pairs` is the packet's key/value pairs *as parsed*, before a mapping
    collapsed them. Duplicate keys are only visible there -- by the time a
    `dict` exists the repetition has already been resolved, silently. Callers
    reading JSON should pass `object_pairs_hook`'s output.
    """
    parse_findings: list[Finding] = []
    if packet_pairs is not None:
        parse_findings.extend(check_no_duplicate_keys(packet_pairs))
    parse_findings.extend(check_no_unknown_fields(dict(packet), PACKET_FIELDS))
    if parse_findings:
        return GlyphReplyVerdict(None, None, tuple(parse_findings))

    carrier_wire = packet.get("carrier")
    if not isinstance(carrier_wire, list):
        return GlyphReplyVerdict(
            None,
            None,
            (Finding("FW-UNKNOWN-FIELD", "packet declares no carrier list"),),
        )
    try:
        carrier = Carrier.from_wire(carrier_wire)
    except ValueError as error:
        return GlyphReplyVerdict(
            None, None, (Finding(REFUSAL_CARRIER_CODEPOINT, str(error)),)
        )

    # Defaults DOWN. A caller that brought no carrier of its own gets no
    # verification, whatever the rows turn out to say.
    authored_by = CarrierAuthority.PRODUCER
    if host_carrier is not None:
        declared = carrier_digest(carrier)
        pinned = carrier_digest(host_carrier)
        if declared != pinned:
            # A positive objection, and a different one from
            # FW-CARRIER-CODEPOINT: every glyph in the packet may be legal
            # under the carrier the packet supplied. The objection is that the
            # packet supplied it, and it is not ours.
            return GlyphReplyVerdict(
                None,
                None,
                (
                    Finding(
                        REFUSAL_CARRIER_MISMATCH,
                        f"the packet declares carrier {declared[:16]}... and this "
                        f"host pins {pinned[:16]}...; a run against the wrong "
                        "allowlist establishes nothing about the right one",
                    ),
                ),
            )
        authored_by = CarrierAuthority.HOST

    # The packet contributes a NAME; the host contributes the rules. Resolution
    # happens once, here, so no decider is ever handed a presentation a
    # producer wrote.
    pins = host_presentations or PresentationPins.empty()
    declared_ref = packet.get("presentation_ref")
    declared_ref = declared_ref if isinstance(declared_ref, str) else None
    context = DeciderContext(
        # The HOST's carrier where one was supplied. The digests were compared
        # above so the two are member-for-member identical when both exist,
        # making this behaviourally a no-op today -- and the docstring on
        # DeciderContext promises host-side material, so the code should say so
        # rather than rely on a check made twenty lines earlier.
        carrier=host_carrier or carrier,
        presentation=pins.resolve(declared_ref) if declared_ref else None,
        presentation_ref=declared_ref,
        pins=pins,
    )

    rows_wire = packet.get("rows")
    rows_wire = rows_wire if isinstance(rows_wire, list) else []

    receipt_rows: list[ReceiptRow] = []
    for index, raw in enumerate(rows_wire):
        sentence = raw if isinstance(raw, str) else str(raw)
        op = _leading_op(sentence)

        # Refusals become rows rather than dropped rows. This is the whole
        # reason RowOutcome.REFUSED exists: a caller that drops what it cannot
        # admit produces a receipt that looks complete.
        op_findings = lint_ledger_row(sentence, row=index)
        carrier_findings = carrier.check_ledger_text(sentence, row=index)
        if op_findings or carrier_findings:
            code = (
                REFUSAL_OP_UNDECLARED if op_findings else REFUSAL_CARRIER_CODEPOINT
            )
            receipt_rows.append(
                ReceiptRow.refused(
                    index=index,
                    op=op,
                    statement=sentence,
                    evidence_ref="none",
                    producer_claimed_valid=True,
                    refusal_code=code,
                )
            )
            continue

        # What the host can establish on its own. A form it does not decide
        # comes back UNCHECKABLE with the blind spot named -- not a PASS, and
        # not a hallucination charge against the producer.
        derivation = rederive_statement(sentence, context)

        # ReceiptRow enforces its own invariants and will reject an op outside
        # the closed set. The linter above should have caught that already, so
        # a rejection here means the two disagree -- and a disagreement between
        # two host-side checks must surface as a refusal, not as an exception
        # escaping the use case. A crash is not a terminal.
        try:
            if derivation.outcome is RowOutcome.REFUSED:
                receipt_rows.append(
                    ReceiptRow.refused(
                        index=index,
                        op=op,
                        statement=sentence,
                        evidence_ref="none",
                        producer_claimed_valid=True,
                        refusal_code=derivation.refusal_code
                        or REFUSAL_STATEMENT_ILL_FORMED,
                    )
                )
            else:
                receipt_rows.append(
                    ReceiptRow(
                        index=index,
                        op=op,
                        statement=sentence,
                        evidence_ref="none",
                        producer_claimed_valid=True,
                        outcome=derivation.outcome,
                        host_value=derivation.host_value,
                        missing_fields=derivation.missing_fields,
                    )
                )
        except ValueError as error:
            receipt_rows.append(
                ReceiptRow.refused(
                    index=index,
                    op=op,
                    statement=sentence,
                    evidence_ref="none",
                    producer_claimed_valid=True,
                    refusal_code=REFUSAL_OP_UNDECLARED,
                )
            )
            del error

    receipt = CalculusReceipt.over(
        carrier,
        receipt_rows,
        declared_row_count=len(rows_wire),
        carrier_authored_by=authored_by,
    )

    decoding = None
    provider = packet.get("provider")
    reply_text = packet.get("reply_text")
    if isinstance(provider, str) and isinstance(reply_text, str):
        # What the run says it ACTUALLY applied, defaulting DOWN. Deriving this
        # from the provider name made the receipt claim exactness for any run
        # against a grammar-capable backend, whether or not a grammar was ever
        # sent. A caller that says nothing gets no guarantee.
        declared = packet.get("constraint_applied")
        try:
            applied = (
                ConstraintMode(declared)
                if isinstance(declared, str)
                else ConstraintMode.UNCONSTRAINED
            )
        except ValueError:
            applied = ConstraintMode.UNCONSTRAINED
        try:
            decoding = DecodingReceipt.measure(
                provider, reply_text, carrier, applied=applied
            )
        except ValueError as error:
            return GlyphReplyVerdict(
                receipt, None, (Finding("FW-UNKNOWN-FIELD", str(error)),)
            )

    return GlyphReplyVerdict(receipt, decoding, ())


def _leading_op(sentence: str) -> str:
    """The op token exactly as the producer wrote it, or the empty string.

    Recorded verbatim even when undeclared: rendering an unrecognised op as
    something recognised would be a second forgery on top of the first.

    Derived from `statement_body` rather than re-parsing the prefix, so the op
    and the statement are always the two halves of the SAME split. Two copies of
    the `op:` rule is how the prefix came to be counted twice once already, and
    a drift between these two would put an op in the receipt that is not the one
    the decider was handed.
    """
    return split_row(sentence)[0]
