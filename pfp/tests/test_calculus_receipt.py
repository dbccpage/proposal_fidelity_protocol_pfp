"""WP-5 acceptance: a wrong landing value produces a terminal, not a warning."""

from __future__ import annotations

import pytest

from omega_engine_pfp.domain.calculus_receipt import (
    CALCULUS_RECEIPT_SCHEMA,
    CalculusReceipt,
    CarrierAuthority,
    ReceiptRow,
    RowOutcome,
    Terminal,
    carrier_digest,
)
from omega_engine_pfp.domain.glyph_calculus import Carrier

CONTRACT_CARRIER = [
    {"symbol": "alpha", "codepoint": "U+03B1"},
    {"symbol": "beta", "codepoint": "U+03B2"},
    {"symbol": "gamma", "codepoint": "U+03B3"},
    {"symbol": "delta", "codepoint": "U+03B4"},
    {"symbol": "epsilon", "codepoint": "U+03B5"},
]


def carrier() -> Carrier:
    return Carrier.from_wire(CONTRACT_CARRIER)


def built(rows, authored_by=CarrierAuthority.HOST):
    """A receipt whose ledger had exactly these rows -- nothing dropped.

    The honest default for a complete ledger. Cases that test row accounting
    call `CalculusReceipt.over` directly with a mismatched count.

    `authored_by` defaults to HOST here so that the cases below keep testing
    the ROW logic. Everything about carrier authorship is tested explicitly in
    `TestCarrierAuthority`, where it is the subject rather than the backdrop.
    """
    return CalculusReceipt.over(
        carrier(),
        rows,
        declared_row_count=len(rows),
        carrier_authored_by=authored_by,
    )


def rederived(index: int, statement: str = "period(c5) = 5") -> ReceiptRow:
    return ReceiptRow(
        index=index,
        op="PROVE",
        statement=statement,
        evidence_ref="cycle:c5",
        producer_claimed_valid=True,
        outcome=RowOutcome.REDERIVED,
        host_value="5",
    )


class TestCarrierDigest:
    def test_the_digest_is_stable(self) -> None:
        assert carrier_digest(carrier()) == carrier_digest(carrier())

    def test_a_homoglyph_swap_changes_the_digest(self) -> None:
        """The digest covers codepoints, not the rendered page.

        Swapping Greek alpha for the APL alpha is invisible to a reader and
        must not be invisible to the receipt.
        """
        impostor = [{"symbol": "alpha", "codepoint": "U+237A"}] + CONTRACT_CARRIER[1:]
        assert carrier_digest(Carrier.from_wire(impostor)) != carrier_digest(carrier())

    def test_reordering_members_changes_the_digest(self) -> None:
        # Declaration order is the cycle order, so it is load-bearing.
        reordered = [CONTRACT_CARRIER[1], CONTRACT_CARRIER[0], *CONTRACT_CARRIER[2:]]
        assert carrier_digest(Carrier.from_wire(reordered)) != carrier_digest(carrier())


class TestRowInvariants:
    def test_an_op_outside_the_closed_set_is_refused(self) -> None:
        with pytest.raises(ValueError, match="not in the closed set"):
            ReceiptRow(
                index=1,
                op="QED",
                statement="x",
                evidence_ref="r",
                producer_claimed_valid=True,
                outcome=RowOutcome.REDERIVED,
            )

    def test_an_uncheckable_row_must_name_its_blind_spot(self) -> None:
        # An unnamed blind spot is exactly what this receipt exists to prevent.
        with pytest.raises(ValueError, match="names no missing fields"):
            ReceiptRow(
                index=1,
                op="LAND",
                statement="successor^2(alpha) = gamma",
                evidence_ref="cycle:c5",
                producer_claimed_valid=True,
                outcome=RowOutcome.UNCHECKABLE,
            )

    def test_a_checked_row_may_not_claim_missing_fields(self) -> None:
        with pytest.raises(ValueError, match="names missing fields"):
            ReceiptRow(
                index=1,
                op="PROVE",
                statement="x",
                evidence_ref="r",
                producer_claimed_valid=True,
                outcome=RowOutcome.REDERIVED,
                missing_fields=("cycle_id",),
            )


class TestTerminal:
    def test_all_rederived_passes(self) -> None:
        receipt = built([rederived(0), rederived(1)])
        assert receipt.terminal is Terminal.PASS

    def test_a_wrong_landing_value_refuses(self) -> None:
        """The WP-5 acceptance criterion.

        The producer claims the walk lands on delta; the host iterates the
        generator table and gets gamma. That is a terminal, not a warning.
        """
        receipt = built([
                rederived(0),
                ReceiptRow(
                    index=1,
                    op="LAND",
                    statement="successor^17(alpha) = delta",
                    evidence_ref="cycle:c5",
                    producer_claimed_valid=True,
                    outcome=RowOutcome.CONTRADICTED,
                    host_value="gamma",  # 17 mod 5 = 2
                ),
            ],
        )
        assert receipt.terminal is Terminal.REFUSE
        assert receipt.to_wire()["terminal_status"] == "REFUSE"

    def test_an_uncheckable_row_cannot_license_a_pass(self) -> None:
        receipt = built([
                rederived(0),
                ReceiptRow(
                    index=1,
                    op="SHOW",
                    statement="the transport is natural",
                    evidence_ref="prose",
                    producer_claimed_valid=True,
                    outcome=RowOutcome.UNCHECKABLE,
                    missing_fields=("soundness", "application_scope"),
                ),
            ],
        )
        assert receipt.terminal is Terminal.OPEN_RESIDUAL

    def test_a_contradiction_outranks_a_blind_spot(self) -> None:
        # Knowing the producer is wrong is stronger information than not
        # knowing, so REFUSE wins over OPEN_RESIDUAL.
        receipt = built([
                ReceiptRow(
                    index=0,
                    op="SHOW",
                    statement="prose",
                    evidence_ref="none",
                    producer_claimed_valid=True,
                    outcome=RowOutcome.UNCHECKABLE,
                    missing_fields=("soundness",),
                ),
                ReceiptRow(
                    index=1,
                    op="REDUCE",
                    statement="17 mod 5 = 3",
                    evidence_ref="integer-mod-replay",
                    producer_claimed_valid=True,
                    outcome=RowOutcome.CONTRADICTED,
                    host_value="2",
                ),
            ],
        )
        assert receipt.terminal is Terminal.REFUSE

    def test_an_empty_receipt_does_not_pass(self) -> None:
        # Nothing checked is not the same as everything checked.
        assert built([]).terminal is Terminal.OPEN_RESIDUAL


class TestHallucinationAccounting:
    def test_only_a_contradiction_counts_as_a_hallucination(self) -> None:
        """The correction WP-10 needs.

        WP-10 defined a hallucination as `producer_claimed_valid and not
        host_rederived`. That is too wide: `not host_rederived` also covers
        rows the host could not check, so the rate would be inflated by exactly
        the size of the host's own blind spot. A claim the host has no opinion
        about is an unverified claim, not a lie.
        """
        contradicted = ReceiptRow(
            index=0,
            op="REDUCE",
            statement="17 mod 5 = 3",
            evidence_ref="integer-mod-replay",
            producer_claimed_valid=True,
            outcome=RowOutcome.CONTRADICTED,
            host_value="2",
        )
        uncheckable = ReceiptRow(
            index=1,
            op="SHOW",
            statement="prose",
            evidence_ref="none",
            producer_claimed_valid=True,
            outcome=RowOutcome.UNCHECKABLE,
            missing_fields=("soundness",),
        )
        receipt = built([contradicted, uncheckable])

        assert receipt.hallucinations == (contradicted,)
        assert receipt.unverified_claims == (uncheckable,)
        # Both have host_rederived False -- which is why the boolean alone
        # cannot carry this distinction.
        assert contradicted.host_rederived is False
        assert uncheckable.host_rederived is False

    def test_an_unclaimed_contradiction_is_not_a_hallucination(self) -> None:
        # The producer did not assert it, so being wrong about it is not a
        # false claim.
        row = ReceiptRow(
            index=0,
            op="OPEN",
            statement="candidate",
            evidence_ref="none",
            producer_claimed_valid=False,
            outcome=RowOutcome.CONTRADICTED,
            host_value="2",
        )
        assert row.is_hallucination is False


class TestBlindSpot:
    def test_the_blind_spot_is_the_union_of_unsupplied_fields(self) -> None:
        receipt = built([
                ReceiptRow(
                    index=0,
                    op="SHOW",
                    statement="a",
                    evidence_ref="none",
                    producer_claimed_valid=True,
                    outcome=RowOutcome.UNCHECKABLE,
                    missing_fields=("soundness", "application_scope"),
                ),
                ReceiptRow(
                    index=1,
                    op="SHOW",
                    statement="b",
                    evidence_ref="none",
                    producer_claimed_valid=True,
                    outcome=RowOutcome.UNCHECKABLE,
                    missing_fields=("soundness", "carrier_digest"),
                ),
            ],
        )
        assert receipt.blind_spot == ("application_scope", "carrier_digest", "soundness")

    def test_a_fully_checked_receipt_has_an_empty_blind_spot(self) -> None:
        assert built([rederived(0)]).blind_spot == ()


class TestWire:
    def test_the_wire_form_carries_the_contract_fields(self) -> None:
        receipt = built([rederived(0)])
        wire = receipt.to_wire()
        assert wire["schema"] == CALCULUS_RECEIPT_SCHEMA
        assert wire["carrier_digest"] == carrier_digest(carrier())
        assert wire["terminal_status"] == "PASS"
        assert wire["authority_effect"] == "None"
        row = wire["operations"][0]
        assert row["producer_claimed_valid"] is True
        assert row["host_rederived"] is True
        assert row["host_outcome"] == "rederived"

    def test_the_wire_form_distinguishes_the_two_falses(self) -> None:
        receipt = built([
                ReceiptRow(
                    index=0,
                    op="SHOW",
                    statement="prose",
                    evidence_ref="none",
                    producer_claimed_valid=True,
                    outcome=RowOutcome.UNCHECKABLE,
                    missing_fields=("soundness",),
                )
            ],
        )
        row = receipt.to_wire()["operations"][0]
        # A reader with only host_rederived would think this was contradicted.
        assert row["host_rederived"] is False
        assert row["host_outcome"] == "uncheckable"
        assert row["host_missing_fields"] == ["soundness"]
        assert receipt.to_wire()["hallucination_count"] == 0
        assert receipt.to_wire()["unverified_claim_count"] == 1


class TestRefusalIsNotLaunderedIntoAPass:
    """The defect the WP-6 review found, end to end.

    `ReceiptRow` refused to *construct* a row whose op was outside the closed
    set. The caller therefore had to drop it, and a receipt over the surviving
    rows returned PASS: the linter's refusal disappeared into the datatype.
    """

    LEDGER = ["PROVE period(c5) = 5", "op QED", "REDUCE 17 mod 5 = 2"]

    def test_the_reviews_exact_scenario_no_longer_passes(self) -> None:
        from omega_engine_pfp.domain.glyph_calculus import (
            REFUSAL_OP_UNDECLARED,
            lint_rows,
        )

        findings = lint_rows(self.LEDGER)
        assert [f.code for f in findings] == [REFUSAL_OP_UNDECLARED]

        # The row the linter refused is now representable, so it stays in the
        # receipt instead of being dropped by the caller.
        rows = [
            rederived(0, "period(c5) = 5"),
            ReceiptRow.refused(
                index=1,
                op="QED",
                statement="op QED",
                evidence_ref="none",
                producer_claimed_valid=True,
                refusal_code=REFUSAL_OP_UNDECLARED,
            ),
            rederived(2, "17 mod 5 = 2"),
        ]
        receipt = CalculusReceipt.over(
            carrier(),
            rows,
            declared_row_count=3,
            carrier_authored_by=CarrierAuthority.HOST,
        )
        assert receipt.terminal is Terminal.REFUSE
        assert len(receipt.refused_rows) == 1
        assert receipt.to_wire()["refused_row_count"] == 1

    def test_dropping_the_row_is_caught_by_the_accounting(self) -> None:
        """The other half: a caller that drops it anyway cannot hide that.

        Even with a refusable row available, nothing stops a caller from
        omitting it. The ledger's own row count is therefore carried in the
        receipt, and a receipt that does not account for every declared row
        refuses -- whatever the surviving rows say.
        """
        surviving = [rederived(0, "period(c5) = 5"), rederived(2, "17 mod 5 = 2")]
        receipt = CalculusReceipt.over(
            carrier(),
            surviving,
            declared_row_count=3,
            carrier_authored_by=CarrierAuthority.HOST,
        )

        assert receipt.unaccounted_rows == 1
        assert receipt.terminal is Terminal.REFUSE, (
            "a receipt missing a ledger row must not license anything; this is "
            "the shape the refusal used to escape through"
        )
        assert receipt.to_wire()["unaccounted_rows"] == 1

    def test_the_same_rows_pass_only_when_the_ledger_had_only_them(self) -> None:
        # Control: the accounting refuses because a row is missing, not because
        # two REDERIVED rows are somehow objectionable.
        surviving = [rederived(0), rederived(2)]
        assert built(surviving).terminal is Terminal.PASS

    def test_a_refused_row_must_carry_a_code(self) -> None:
        with pytest.raises(ValueError, match="names no refusal code"):
            ReceiptRow(
                index=1,
                op="QED",
                statement="op QED",
                evidence_ref="none",
                producer_claimed_valid=True,
                outcome=RowOutcome.REFUSED,
            )

    def test_a_refused_row_records_the_op_the_producer_actually_wrote(self) -> None:
        # Rendering an undeclared op as something declared would be a second
        # forgery on top of the first.
        row = ReceiptRow.refused(1, "QED", "op QED", "none", True, "FW-OP-UNDECLARED")
        assert row.op == "QED"
        assert row.to_wire()["op"] == "QED"
        assert row.to_wire()["refusal_code"] == "FW-OP-UNDECLARED"

    def test_a_refusal_is_not_counted_as_a_hallucination(self) -> None:
        # The host never formed a contrary opinion; it declined to admit the
        # row. Counting that as a producer lie would inflate the rate with the
        # host's own admission policy.
        row = ReceiptRow.refused(1, "QED", "op QED", "none", True, "FW-OP-UNDECLARED")
        assert row.is_hallucination is False
        assert row.host_rederived is False


class TestDigestIsNotInjectable:
    """The old canonical form joined members with ``:`` and a newline.

    A symbol containing those delimiters could reproduce a different carrier's
    serialisation byte for byte, so two distinct carriers digested the same. A
    digest whose pre-image is ambiguous is not a digest of the thing it names.
    """

    TWO_MEMBERS = [
        {"symbol": "a", "codepoint": "U+03B1"},
        {"symbol": "b", "codepoint": "U+03B2"},
    ]
    # One member whose symbol replays the first carrier's serialisation. Under
    # "sym:U+XXXX" joined by newline, both render as: a:U+03B1\nb:U+03B2
    ONE_MEMBER_SMUGGLING_THE_DELIMITERS = [
        {"symbol": "a:U+03B1\nb", "codepoint": "U+03B2"},
    ]

    @staticmethod
    def legacy_canonical(carrier: Carrier) -> str:
        return "\n".join(f"{m.symbol}:U+{ord(m.char):04X}" for m in carrier.members)

    def test_the_delimiter_collision_no_longer_collides(self) -> None:
        honest = Carrier.from_wire(self.TWO_MEMBERS)
        forged = Carrier.from_wire(self.ONE_MEMBER_SMUGGLING_THE_DELIMITERS)

        # Anchor the test to the real defect: confirm the collision existed
        # under the old encoding, so this cannot quietly become a test of a
        # hypothetical problem.
        assert self.legacy_canonical(honest) == self.legacy_canonical(forged), (
            "fixture is stale: it no longer reproduces the collision it pins"
        )

        assert carrier_digest(honest) != carrier_digest(forged), (
            "two different carriers still digest the same; the canonical form "
            "is injectable"
        )

    def test_distinct_carriers_stay_distinct(self) -> None:
        one = Carrier.from_wire([{"symbol": "a", "codepoint": "U+03B1"}])
        two = Carrier.from_wire([{"symbol": "b", "codepoint": "U+03B1"}])
        assert carrier_digest(one) != carrier_digest(two)


class TestCarrierAuthority:
    """A PASS earned against the packet's own carrier is not a PASS.

    The rows are checked against an allowlist the same producer wrote, so what
    a clean receipt establishes is that the packet agrees with itself. A
    producer wanting one need only widen its carrier.
    """

    def test_a_producer_authored_carrier_cannot_reach_pass(self) -> None:
        receipt = built(
            [rederived(0), rederived(1, "17 mod 5 = 2")],
            authored_by=CarrierAuthority.PRODUCER,
        )
        assert receipt.terminal is Terminal.SELF_CONSISTENT_ONLY

    def test_a_host_authored_carrier_reaches_pass(self) -> None:
        # The discriminating half. Without it, a terminal that always said
        # SELF_CONSISTENT_ONLY would pass the test above.
        receipt = built(
            [rederived(0), rederived(1, "17 mod 5 = 2")],
            authored_by=CarrierAuthority.HOST,
        )
        assert receipt.terminal is Terminal.PASS

    def test_the_rows_are_identical_in_both_cases(self) -> None:
        """Guards the pair above: only the authorship differs.

        If the two fixtures differed in their rows as well, the test would be
        asserting something about the rows and reporting it as authorship.
        """
        rows = [rederived(0), rederived(1, "17 mod 5 = 2")]
        host = built(rows, authored_by=CarrierAuthority.HOST)
        producer = built(rows, authored_by=CarrierAuthority.PRODUCER)
        assert host.rows == producer.rows
        assert host.carrier_digest == producer.carrier_digest
        assert host.terminal is not producer.terminal

    def test_an_open_residual_is_not_downgraded(self) -> None:
        # OPEN_RESIDUAL already establishes nothing, so there is nothing in it
        # for a carrier to have established. Calling it self-consistent would
        # claim MORE than the truth over rows the host never checked -- the one
        # direction this module must never move.
        unchecked = ReceiptRow(
            index=1,
            op="SHOW",
            statement="successor(alpha) = beta",
            evidence_ref="none",
            producer_claimed_valid=True,
            outcome=RowOutcome.UNCHECKABLE,
            missing_fields=("evidence_ref",),
        )
        receipt = built(
            [rederived(0), unchecked],
            authored_by=CarrierAuthority.PRODUCER,
        )
        assert receipt.terminal is Terminal.OPEN_RESIDUAL

    def test_an_empty_receipt_is_not_self_consistent_either(self) -> None:
        assert (
            built([], authored_by=CarrierAuthority.PRODUCER).terminal
            is Terminal.OPEN_RESIDUAL
        )

    @pytest.mark.parametrize(
        "authored_by", [CarrierAuthority.HOST, CarrierAuthority.PRODUCER]
    )
    def test_a_refusal_outranks_the_downgrade(
        self, authored_by: CarrierAuthority
    ) -> None:
        # Knowing something is wrong outranks knowing only that it is
        # consistent, and it does so from either carrier.
        receipt = built(
            [
                rederived(0),
                ReceiptRow.refused(
                    index=1,
                    op="QED",
                    statement="op QED",
                    evidence_ref="none",
                    producer_claimed_valid=True,
                    refusal_code="FW-OP-UNDECLARED",
                ),
            ],
            authored_by=authored_by,
        )
        assert receipt.terminal is Terminal.REFUSE

    def test_the_wire_names_who_authored_the_carrier(self) -> None:
        # A reader of the receipt alone must be able to tell which claim it is.
        wire = built([rederived(0)], authored_by=CarrierAuthority.PRODUCER).to_wire()
        assert wire["carrier_authored_by"] == "producer"
        assert wire["terminal_status"] == "SELF_CONSISTENT_ONLY"

    def test_the_constructor_will_not_guess(self) -> None:
        """`over` refuses to default the authorship, in either direction.

        HOST would hand every caller a PASS it did not earn. PRODUCER is safe
        but silently caps a host that really did pin its carrier. Neither is a
        decision this constructor is in a position to make.
        """
        with pytest.raises(TypeError, match="carrier_authored_by"):
            CalculusReceipt.over(carrier(), [rederived(0)], declared_row_count=1)
