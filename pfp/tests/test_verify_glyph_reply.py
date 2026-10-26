"""The surface is wired: these call the CLI, not the library.

Defect 6 of the WP-6 review was that `lint_rows`, `CalculusReceipt`,
`DecodingReceipt` and the strict-parse checks had no caller anywhere in the
repository. Tested library code with no caller defends nothing, so at least one
test here has to reach the checks the way an operator would.
"""

from __future__ import annotations

import json
from pathlib import Path

from omega_engine_pfp.domain.calculus_receipt import CarrierAuthority
from omega_engine_pfp.domain.glyph_calculus import Carrier
from omega_engine_pfp.entrypoints.cli.symbol_game import main
from omega_engine_pfp.use_cases.verify_glyph_reply import (
    PACKET_FIELDS,
    verify_glyph_reply,
)

#: The carrier this estate pins, as shipped. Resolved from this file rather
#: than hard-coded so that moving the pin breaks the test that reads it.
GOVERNANCE_CARRIER_PIN = (
    Path(__file__).resolve().parents[2]
    / "omega_engine_governance"
    / "contracts"
    / "pinned"
    / "symbol_game_carrier.json"
)
GOVERNANCE_PRESENTATION_PINS = GOVERNANCE_CARRIER_PIN.with_name(
    "symbol_game_presentations.json"
)

CARRIER = [
    {"symbol": "alpha", "codepoint": "U+03B1"},
    {"symbol": "beta", "codepoint": "U+03B2"},
    {"symbol": "gamma", "codepoint": "U+03B3"},
    {"symbol": "delta", "codepoint": "U+03B4"},
    {"symbol": "epsilon", "codepoint": "U+03B5"},
]
APL_ALPHA = "⍺"  # U+237A


def packet(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema": "omega.glyph_calculus.draft.v1",
        "carrier": CARRIER,
        "rows": ["PROVE period(c5) = 5", "REDUCE 17 mod 5 = 2"],
    }
    base.update(overrides)
    return base


def run_cli(tmp_path: Path, body: str, *extra: str) -> tuple[int, dict]:
    """Invoke the real CLI entry point over a real file."""
    target = tmp_path / "packet.json"
    target.write_text(body, encoding="utf-8")
    import io
    import contextlib

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(
            ["verify-glyph-reply", "--packet", str(target), *extra]
        )
    return code, json.loads(buffer.getvalue())


class TestTheSurfaceIsReachable:
    def test_the_cli_command_exists_and_runs(self, tmp_path: Path) -> None:
        code, wire = run_cli(tmp_path, json.dumps(packet()))
        assert wire["authority_effect"] == "None"
        assert "calculus_receipt" in wire
        # No row can be re-derived yet, so nothing is established and nothing
        # is wrong. OPEN_RESIDUAL is the honest terminal, and exit 0.
        assert wire["terminal_status"] == "OPEN_RESIDUAL"
        assert code == 0

    def test_an_undeclared_op_refuses_through_the_cli(self, tmp_path: Path) -> None:
        code, wire = run_cli(tmp_path, json.dumps(packet(rows=["op QED"])))
        assert wire["terminal_status"] == "REFUSE"
        assert code == 2
        row = wire["calculus_receipt"]["operations"][0]
        assert row["host_outcome"] == "refused"
        assert row["refusal_code"] == "FW-OP-UNDECLARED"
        # Recorded as the producer wrote it.
        assert row["op"] == "QED"

    def test_a_homoglyph_refuses_through_the_cli(self, tmp_path: Path) -> None:
        code, wire = run_cli(
            tmp_path, json.dumps(packet(rows=[f"LAND {APL_ALPHA}"]))
        )
        assert wire["terminal_status"] == "REFUSE"
        assert code == 2
        assert (
            wire["calculus_receipt"]["operations"][0]["refusal_code"]
            == "FW-CARRIER-CODEPOINT"
        )

    def test_a_duplicate_key_refuses_before_any_meaning_is_taken(
        self, tmp_path: Path
    ) -> None:
        # Only visible pre-collapse: by the time a dict exists the repetition
        # has already been resolved, silently and in the parser's favour.
        body = (
            '{"schema": "a", "carrier": [], "rows": [], '
            '"schema": "b"}'
        )
        code, wire = run_cli(tmp_path, body)
        assert code == 2
        assert wire["terminal_status"] == "REFUSE"
        assert any("FW-DUPLICATE-KEY" in f for f in wire["parse_findings"])

    def test_an_undeclared_field_refuses(self, tmp_path: Path) -> None:
        code, wire = run_cli(tmp_path, json.dumps(packet(vibe="good")))
        assert code == 2
        assert any("FW-UNKNOWN-FIELD" in f for f in wire["parse_findings"])

    def test_a_missing_file_refuses_rather_than_crashing(self, tmp_path: Path) -> None:
        code = main(["verify-glyph-reply", "--packet", str(tmp_path / "nope.json")])
        assert code == 2, "a run that could not read its input established nothing"


class TestRowAccounting:
    def test_every_ledger_row_reaches_the_receipt(self) -> None:
        # The laundering guard, at the level that would actually leak: the use
        # case must not drop the rows it refuses.
        verdict = verify_glyph_reply(
            packet(rows=["PROVE ok", "op QED", "REDUCE 17 mod 5 = 2"])
        )
        assert verdict.receipt is not None
        assert verdict.receipt.declared_row_count == 3
        assert len(verdict.receipt.rows) == 3
        assert verdict.receipt.unaccounted_rows == 0
        assert verdict.terminal.value == "REFUSE"

    def test_a_refused_row_is_not_charged_as_a_hallucination(self) -> None:
        verdict = verify_glyph_reply(packet(rows=["op QED"]))
        assert verdict.receipt is not None
        assert verdict.receipt.hallucinations == ()


class TestDecoding:
    def test_the_decode_tier_is_recorded_when_a_provider_is_named(self) -> None:
        verdict = verify_glyph_reply(
            packet(provider="anthropic", reply_text="αβγ")
        )
        assert verdict.decoding is not None
        wire = verdict.decoding.to_wire()
        assert wire["constraint_applied"] == "unconstrained"
        assert wire["constraint_available"] == "unconstrained"
        assert wire["constraint_is_exact"] is False
        assert wire["emission_within_carrier"] is True

    def test_an_emission_outside_the_carrier_refuses(self) -> None:
        verdict = verify_glyph_reply(
            packet(provider="local", reply_text=f"α{APL_ALPHA}")
        )
        assert verdict.decoding is not None
        assert verdict.decoding.emission_within_carrier is False
        assert verdict.terminal.value == "REFUSE", (
            "a clean receipt must not license a run whose emission left the carrier"
        )


class TestHostCarrier:
    """Who authored the carrier the rows were checked against.

    The packet declares its own carrier, so without a host-side one the check
    is a consistency check: the rows are measured against an allowlist the same
    producer wrote.
    """

    def test_without_a_host_carrier_the_receipt_says_producer(self) -> None:
        verdict = verify_glyph_reply(packet())
        assert verdict.receipt is not None
        assert verdict.receipt.carrier_authored_by is CarrierAuthority.PRODUCER
        assert verdict.to_wire()["calculus_receipt"]["carrier_authored_by"] == "producer"

    def test_with_a_matching_host_carrier_the_receipt_says_host(self) -> None:
        verdict = verify_glyph_reply(
            packet(), host_carrier=Carrier.from_wire(CARRIER)
        )
        assert verdict.receipt is not None
        assert verdict.receipt.carrier_authored_by is CarrierAuthority.HOST

    def test_a_carrier_the_host_does_not_pin_is_refused(self) -> None:
        # Not FW-CARRIER-CODEPOINT: every glyph in the packet is legal under
        # the carrier the packet supplied. The objection is that the packet
        # supplied it, and it is not ours.
        theirs = CARRIER + [{"symbol": "zeta", "codepoint": "U+03B6"}]
        verdict = verify_glyph_reply(
            packet(carrier=theirs), host_carrier=Carrier.from_wire(CARRIER)
        )
        assert verdict.terminal.value == "REFUSE"
        assert [f.code for f in verdict.parse_findings] == ["FW-CARRIER-MISMATCH"]
        assert verdict.receipt is None, (
            "a run against the wrong allowlist establishes nothing about the "
            "right one, so there is no receipt to read"
        )

    def test_the_same_packet_is_admitted_against_its_own_carrier(self) -> None:
        # Control for the case above: the wider carrier is refused because the
        # HOST does not pin it, not because it is malformed.
        theirs = CARRIER + [{"symbol": "zeta", "codepoint": "U+03B6"}]
        verdict = verify_glyph_reply(packet(carrier=theirs))
        assert verdict.terminal.value == "OPEN_RESIDUAL"
        assert verdict.receipt is not None
        assert verdict.receipt.carrier_authored_by is CarrierAuthority.PRODUCER

    def test_the_packet_cannot_declare_its_own_authority(self) -> None:
        """The laundering attempt, refused by the field allowlist.

        If a packet could say `carrier_authored_by: host`, it would be the
        claim vouching for itself -- the whole defect. The host's carrier
        reaches the use case as an argument or not at all.
        """
        verdict = verify_glyph_reply(packet(carrier_authored_by="host"))
        assert verdict.terminal.value == "REFUSE"
        assert any("FW-UNKNOWN-FIELD" in str(f) for f in verdict.parse_findings)
        assert "carrier_authored_by" not in PACKET_FIELDS


class TestTheCarrierPinReachesTheCli:
    def test_the_governance_pin_is_the_carrier_this_estate_declares(self) -> None:
        """The shipped pin file is read, not just shipped.

        A pin file nothing parses is a file, not a pin -- and if it silently
        stopped matching, every run through `--carrier` would refuse and the
        cause would be three layers away from the message.
        """
        body = json.loads(GOVERNANCE_CARRIER_PIN.read_text(encoding="utf-8"))
        assert body["schema"] == "omega.glyph_carrier_pin.v1"
        assert body["carrier"] == CARRIER

    def test_the_carrier_flag_makes_the_run_a_verification(
        self, tmp_path: Path
    ) -> None:
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet()),
            "--carrier",
            str(GOVERNANCE_CARRIER_PIN),
        )
        assert code == 0
        assert wire["calculus_receipt"]["carrier_authored_by"] == "host"

    def test_without_the_flag_the_same_packet_is_only_consistent(
        self, tmp_path: Path
    ) -> None:
        code, wire = run_cli(tmp_path, json.dumps(packet()))
        assert code == 0
        assert wire["calculus_receipt"]["carrier_authored_by"] == "producer"

    def test_a_packet_declaring_another_carrier_refuses_under_the_pin(
        self, tmp_path: Path
    ) -> None:
        theirs = CARRIER + [{"symbol": "zeta", "codepoint": "U+03B6"}]
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet(carrier=theirs)),
            "--carrier",
            str(GOVERNANCE_CARRIER_PIN),
        )
        assert code == 2
        assert wire["terminal_status"] == "REFUSE"
        assert any("FW-CARRIER-MISMATCH" in f for f in wire["parse_findings"])

    def test_an_unreadable_pin_refuses_rather_than_falling_back(
        self, tmp_path: Path
    ) -> None:
        """Fatal, not a fallback.

        An operator who asked for verification and silently received a
        consistency check has been told something false about their run. That
        is worse than being told the file is unreadable.
        """
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet()),
            "--carrier",
            str(tmp_path / "no-such-pin.json"),
        )
        assert code == 2
        assert wire["terminal_status"] == "REFUSE"

    def test_a_pin_with_an_undeclared_field_refuses(self, tmp_path: Path) -> None:
        bad = tmp_path / "pin.json"
        bad.write_text(
            json.dumps(
                {
                    "schema": "omega.glyph_carrier_pin.v1",
                    "carrier": CARRIER,
                    "vibe": "good",
                }
            ),
            encoding="utf-8",
        )
        code, wire = run_cli(tmp_path, json.dumps(packet()), "--carrier", str(bad))
        assert code == 2
        assert "undeclared fields" in wire["error"]

    def test_a_pin_declaring_the_wrong_schema_refuses(self, tmp_path: Path) -> None:
        bad = tmp_path / "pin.json"
        bad.write_text(
            json.dumps({"schema": "something.else.v1", "carrier": CARRIER}),
            encoding="utf-8",
        )
        code, wire = run_cli(tmp_path, json.dumps(packet()), "--carrier", str(bad))
        assert code == 2
        assert "expected" in wire["error"]


class TestTheTerminalLadderIsReachable:
    """Every rung, end to end, through the real use case.

    Before the modular decider landed, every admitted row was UNCHECKABLE, so
    every clean run stopped at OPEN_RESIDUAL and PASS, SELF_CONSISTENT_ONLY and
    a non-zero hallucination count were structurally unreachable. A receipt that
    can only ever say "I could not check this" is not a receipt, and an
    always-zero hallucination count reads as a clean bill of health rather than
    as an unasked question.
    """

    DECIDABLE = ["REDUCE 17 mod 5 = 2", "op: REDUCE 33 mod 7 = 5"]

    def test_a_producer_carrier_tops_out_at_self_consistent_only(self) -> None:
        verdict = verify_glyph_reply(packet(rows=self.DECIDABLE))
        assert verdict.terminal.value == "SELF_CONSISTENT_ONLY"
        assert verdict.receipt is not None
        assert [row.outcome.value for row in verdict.receipt.rows] == [
            "rederived",
            "rederived",
        ]
        assert verdict.receipt.blind_spot == (), "nothing went unchecked here"

    def test_the_same_rows_reach_pass_against_the_hosts_carrier(self) -> None:
        # The discriminating pair: identical rows, and only the authorship of
        # the carrier differs.
        verdict = verify_glyph_reply(
            packet(rows=self.DECIDABLE), host_carrier=Carrier.from_wire(CARRIER)
        )
        assert verdict.terminal.value == "PASS"

    def test_one_undecidable_row_holds_the_run_at_open_residual(self) -> None:
        # One unchecked row is enough to establish that not everything was
        # established, whoever wrote the carrier.
        #
        # The fixture is a form no decider owns. `period(c5)` was used here
        # until `period` became decidable -- a reminder that a test asserting
        # "this is unchecked" is only as stable as the host's ignorance.
        verdict = verify_glyph_reply(
            packet(rows=[*self.DECIDABLE, "SHOW the carrier has five members"]),
            host_carrier=Carrier.from_wire(CARRIER),
        )
        assert verdict.terminal.value == "OPEN_RESIDUAL"
        assert verdict.receipt is not None
        assert verdict.receipt.blind_spot == ("host_decidable_form",)

    def test_a_false_arithmetic_claim_is_a_hallucination_and_refuses(self) -> None:
        """The count that was structurally always zero.

        `is_hallucination` is claimed AND contradicted. With no decider nothing
        could ever be contradicted, so the property was unreachable and the
        receipt reported a zero it had not earned.
        """
        verdict = verify_glyph_reply(
            packet(rows=["REDUCE 17 mod 5 = 3"]),
            host_carrier=Carrier.from_wire(CARRIER),
        )
        assert verdict.terminal.value == "REFUSE"
        assert verdict.receipt is not None
        assert len(verdict.receipt.hallucinations) == 1
        row = verdict.receipt.rows[0]
        assert row.outcome.value == "contradicted"
        assert row.host_value == "2", "the receipt must carry what the host held"
        assert verdict.to_wire()["calculus_receipt"]["hallucination_count"] == 1

    def test_a_statement_with_no_truth_value_refuses_without_charging_the_producer(
        self,
    ) -> None:
        # `17 mod 0` names no value, so the host holds no contrary answer. It
        # declines to admit the row, and a refusal is not a hallucination.
        verdict = verify_glyph_reply(packet(rows=["REDUCE 17 mod 0 = 2"]))
        assert verdict.terminal.value == "REFUSE"
        assert verdict.receipt is not None
        assert verdict.receipt.rows[0].refusal_code == "FW-STATEMENT-ILL-FORMED"
        assert verdict.receipt.hallucinations == ()

    def test_a_zero_modulus_does_not_escape_as_an_exception(self) -> None:
        # `17 % 0` raises in Python. A crash is not a terminal.
        assert verify_glyph_reply(packet(rows=["REDUCE 1 mod 0 = 0"])) is not None


class TestTheLadderThroughTheCli:
    DECIDABLE = ["REDUCE 17 mod 5 = 2"]

    def test_pass_exits_zero_and_says_pass(self, tmp_path: Path) -> None:
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet(rows=self.DECIDABLE)),
            "--carrier",
            str(GOVERNANCE_CARRIER_PIN),
        )
        assert code == 0
        assert wire["terminal_status"] == "PASS"
        assert wire["calculus_receipt"]["carrier_authored_by"] == "host"

    def test_without_the_pin_the_same_run_is_only_self_consistent(
        self, tmp_path: Path
    ) -> None:
        code, wire = run_cli(tmp_path, json.dumps(packet(rows=self.DECIDABLE)))
        assert code == 0, "self-consistency is not an objection"
        assert wire["terminal_status"] == "SELF_CONSISTENT_ONLY"

    def test_a_contradicted_row_exits_two(self, tmp_path: Path) -> None:
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet(rows=["REDUCE 17 mod 5 = 3"])),
            "--carrier",
            str(GOVERNANCE_CARRIER_PIN),
        )
        assert code == 2
        assert wire["terminal_status"] == "REFUSE"
        assert wire["calculus_receipt"]["hallucination_count"] == 1
        assert wire["calculus_receipt"]["operations"][0]["host_value"] == "2"


class TestPresentationRefThroughTheCli:
    """A row about a presentation, resolved end to end against the host's pins.

    The packet contributes a NAME. The rules come from the governance pin file
    and from nowhere else, so naming a presentation buys a producer nothing
    except the chance that this host pins the same name.
    """

    SUCCESSOR = ["LAND successor^2(alpha) = gamma"]

    def pins(self) -> list[str]:
        return ["--presentations", str(GOVERNANCE_PRESENTATION_PINS)]

    def test_a_named_pin_resolves_and_the_row_rederives(self, tmp_path: Path) -> None:
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet(rows=self.SUCCESSOR, presentation_ref="c5")),
            *self.pins(),
            "--carrier",
            str(GOVERNANCE_CARRIER_PIN),
        )
        assert code == 0
        assert wire["terminal_status"] == "PASS"
        assert wire["calculus_receipt"]["operations"][0]["host_value"] == "gamma"

    def test_without_a_ref_the_host_declines_to_guess(self, tmp_path: Path) -> None:
        # The pin file is loaded and c5 is the only entry. The host still will
        # not use it, because the row never said that is what it meant.
        code, wire = run_cli(
            tmp_path, json.dumps(packet(rows=self.SUCCESSOR)), *self.pins()
        )
        assert code == 0
        assert wire["terminal_status"] == "OPEN_RESIDUAL"
        assert wire["calculus_receipt"]["host_blind_spot"] == [
            "packet_presentation_ref"
        ]

    def test_a_name_the_host_does_not_pin_is_a_different_blind_spot(
        self, tmp_path: Path
    ) -> None:
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet(rows=self.SUCCESSOR, presentation_ref="c7")),
            *self.pins(),
        )
        assert code == 0
        assert wire["calculus_receipt"]["host_blind_spot"] == [
            "presentation_pinned_by_this_host"
        ]

    def test_a_false_landing_refuses(self, tmp_path: Path) -> None:
        code, wire = run_cli(
            tmp_path,
            json.dumps(
                packet(
                    rows=["LAND successor^2(alpha) = delta"], presentation_ref="c5"
                )
            ),
            *self.pins(),
            "--carrier",
            str(GOVERNANCE_CARRIER_PIN),
        )
        assert code == 2
        assert wire["terminal_status"] == "REFUSE"
        assert wire["calculus_receipt"]["hallucination_count"] == 1
        assert wire["calculus_receipt"]["operations"][0]["host_value"] == "gamma"

    def test_period_needs_no_ref_because_it_names_its_own_subject(
        self, tmp_path: Path
    ) -> None:
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet(rows=["PROVE period(c5) = 5"])),
            *self.pins(),
            "--carrier",
            str(GOVERNANCE_CARRIER_PIN),
        )
        assert code == 0
        assert wire["terminal_status"] == "PASS"

    def test_without_the_pin_file_nothing_about_a_presentation_is_decidable(
        self, tmp_path: Path
    ) -> None:
        code, wire = run_cli(
            tmp_path, json.dumps(packet(rows=["PROVE period(c5) = 5"]))
        )
        assert code == 0
        assert wire["terminal_status"] == "OPEN_RESIDUAL"

    def test_an_unreadable_pin_file_refuses_rather_than_falling_back(
        self, tmp_path: Path
    ) -> None:
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet(rows=self.SUCCESSOR)),
            "--presentations",
            str(tmp_path / "nope.json"),
        )
        assert code == 2
        assert wire["terminal_status"] == "REFUSE"

    def test_a_pin_file_with_the_wrong_schema_refuses(self, tmp_path: Path) -> None:
        bad = tmp_path / "pins.json"
        bad.write_text(json.dumps({"schema": "other.v1", "pins": []}), encoding="utf-8")
        code, wire = run_cli(
            tmp_path,
            json.dumps(packet(rows=self.SUCCESSOR)),
            "--presentations",
            str(bad),
        )
        assert code == 2
        assert "expected" in wire["error"]

    def test_the_packet_cannot_supply_rules_only_a_name(self) -> None:
        """There is no field by which a producer can hand the host a rule.

        `presentation_ref` is a string key. A packet trying to carry a
        presentation is refused by the field allowlist, so the worst a producer
        can do is name something -- and a name it invents resolves to nothing.
        """
        assert "presentation_ref" in PACKET_FIELDS
        assert "presentation" not in PACKET_FIELDS
        assert "rules" not in PACKET_FIELDS
        verdict = verify_glyph_reply(
            packet(presentation={"signature": [], "rules": []})
        )
        assert verdict.terminal.value == "REFUSE"
        assert any("FW-UNKNOWN-FIELD" in str(f) for f in verdict.parse_findings)
