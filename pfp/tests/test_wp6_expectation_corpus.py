"""WP-6 expectation corpus — the packet surface.

Every assertion here is transcribed from `_ooutwire/wp6_expectation_corpus.md`,
which was derived from contracts and doctrine and committed at `c5ebce8230`
**before** any of these ran. The git history is the proof of that ordering; a
corpus whose expectations were written after the run is a transcript, and a
transcript cannot refute anything.

That derivation was deleted from the tree on 2026-09-04 and lives only in git
now — read it at `git show c5ebce8230:_ooutwire/wp6_expectation_corpus.md`. The
citation is kept rather than dropped because the ordering claim above is the
whole warrant for this file, and a claim whose evidence has no address is not
checkable. This test file is the executable copy of that derivation.

A disagreement between this file and the code is a FINDING, and which side is
wrong is decided case by case. The previous corpus was refuted 8 of 8.

Cases 1-3 live on the peak surface and are Rust; see the derivation.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_engine_pfp.domain.glyph_calculus import Carrier
from omega_engine_pfp.domain.presentation_pins import PresentationPins
from omega_engine_pfp.use_cases.verify_glyph_reply import verify_glyph_reply

_PINNED = (
    Path(__file__).resolve().parents[2]
    / "omega_engine_governance"
    / "contracts"
    / "pinned"
)
APL_ALPHA = "⍺"  # U+237A, the symgam.md:77 impostor

CARRIER = [
    {"symbol": "alpha", "codepoint": "U+03B1"},
    {"symbol": "beta", "codepoint": "U+03B2"},
    {"symbol": "gamma", "codepoint": "U+03B3"},
    {"symbol": "delta", "codepoint": "U+03B4"},
    {"symbol": "epsilon", "codepoint": "U+03B5"},
]
WIDE_CARRIER = [*CARRIER, {"symbol": "zeta", "codepoint": "U+03B6"}]


def host_pins() -> PresentationPins:
    body = json.loads(
        (_PINNED / "symbol_game_presentations.json").read_text(encoding="utf-8")
    )
    return PresentationPins.from_wire(body["pins"])


def run(rows, *, carrier=None, ref=None, with_host_carrier=True):
    carrier = carrier or CARRIER
    packet = {"schema": "omega.glyph_calculus.draft.v1", "carrier": carrier, "rows": rows}
    if ref:
        packet["presentation_ref"] = ref
    return verify_glyph_reply(
        packet,
        host_carrier=Carrier.from_wire(carrier) if with_host_carrier else None,
        host_presentations=host_pins(),
    )


class TestCase4AnOpOutsideTheClosedSet:
    """Derived: REFUSE, FW-OP-UNDECLARED, op verbatim, ZERO hallucinations."""

    def verdict(self):
        return run(["PROVE period(c5) = 5", "op QED"])

    def test_the_terminal_is_refuse(self) -> None:
        assert self.verdict().terminal.value == "REFUSE"

    def test_the_refused_row_stays_in_the_receipt(self) -> None:
        receipt = self.verdict().receipt
        assert receipt is not None
        assert receipt.declared_row_count == 2
        assert len(receipt.rows) == 2
        assert receipt.unaccounted_rows == 0

    def test_the_refusal_code_and_verbatim_op(self) -> None:
        row = self.verdict().receipt.rows[1]
        assert row.refusal_code == "FW-OP-UNDECLARED"
        assert row.op == "QED", "an undeclared op is recorded as the producer wrote it"

    def test_a_refusal_is_not_a_hallucination(self) -> None:
        # The host never formed a contrary opinion; it declined to admit the row.
        assert self.verdict().receipt.hallucinations == ()


class TestCase5TheCarrierSubstitution:
    """Derived: REFUSE, FW-CARRIER-CODEPOINT, names U+237A, no raw glyph."""

    def verdict(self):
        return run([f"LAND {APL_ALPHA}"])

    def test_the_terminal_is_refuse(self) -> None:
        assert self.verdict().terminal.value == "REFUSE"

    def test_it_names_the_codepoint(self) -> None:
        row = self.verdict().receipt.rows[0]
        assert row.refusal_code == "FW-CARRIER-CODEPOINT"

    def test_no_finding_carries_the_raw_glyph(self) -> None:
        # Findings print on cp1252 consoles, where the glyph is a crash.
        wire = json.dumps(self.verdict().to_wire(), ensure_ascii=True)
        assert APL_ALPHA not in wire


class TestCase6AWrongLandingValue:
    """Derived: REFUSE, contradicted, host_value gamma, ONE hallucination."""

    def verdict(self):
        return run(["LAND successor^2(alpha) = delta"], ref="c5")

    def test_the_terminal_is_refuse(self) -> None:
        assert self.verdict().terminal.value == "REFUSE"

    def test_the_host_holds_a_different_answer(self) -> None:
        row = self.verdict().receipt.rows[0]
        assert row.outcome.value == "contradicted", (
            "the host can resolve both sides, so declining would be dishonest"
        )
        assert row.host_value == "gamma"

    def test_this_is_the_case_that_makes_the_count_non_zero(self) -> None:
        assert len(self.verdict().receipt.hallucinations) == 1


class TestCase7LandauNegativeControl:
    """UNBLOCKED 2026-09-04: `c6` is now pinned in governance.

    Derived while it was still blocked, and the derivation recorded both
    expectations rather than only the reachable one:

        Once `c6` is pinned: REDERIVED, host_value 6; and
        `PROVE period(c6) = 5` must be CONTRADICTED, which is the assertion
        that actually kills a size-capped checker.

    Both are asserted below, unchanged from that text. Landau's g(5) = 6 -- on
    five symbols the maximum order of a permutation is six, realised by a
    2-cycle beside a 3-cycle -- so a checker reporting the SIZE of the signature
    returns 5 and is wrong. `c5` cannot detect that, because for a single cycle
    the order and the size coincide.
    """

    def test_the_period_is_six_not_the_signature_size(self) -> None:
        verdict = run(["PROVE period(c6) = 6"])
        assert verdict.terminal.value == "PASS"
        row = verdict.receipt.rows[0]
        assert row.outcome.value == "rederived"
        assert row.host_value == "6"

    def test_the_size_capped_answer_is_contradicted(self) -> None:
        """The assertion the whole case exists for.

        Five is what a checker returns when it reports the size of the
        signature. A corpus that only asserted the correct value would pass on
        such a checker for `c5` and never ask it this question.
        """
        verdict = run(["PROVE period(c6) = 5"])
        assert verdict.terminal.value == "REFUSE"
        row = verdict.receipt.rows[0]
        assert row.outcome.value == "contradicted"
        assert row.host_value == "6"
        assert len(verdict.receipt.hallucinations) == 1

    def test_c5_could_not_have_caught_this(self) -> None:
        # Guards the control itself: if `c5` distinguished the two numbers,
        # `c6` would be redundant and this case would prove nothing new.
        assert run(["PROVE period(c5) = 5"]).terminal.value == "PASS"


class TestCase8ScopeEscapeRestated:
    """Derived: `FW-MOVE` does not exist; the host emits exactly eight codes.

    Restated as what a scope escape actually is: a carrier symbol outside the
    pinned presentation's signature. Carrier and presentation are INDEPENDENT
    pins, so that is a named blind spot, never a refusal.
    """

    def verdict(self):
        return run(
            ["LAND successor(zeta) = alpha"], carrier=WIDE_CARRIER, ref="c5"
        )

    def test_it_is_uncheckable_not_a_refusal(self) -> None:
        assert self.verdict().terminal.value == "OPEN_RESIDUAL"

    def test_the_blind_spot_names_the_signature(self) -> None:
        assert self.verdict().receipt.blind_spot == (
            "symbol_within_presentation_signature",
        )

    def test_it_does_not_slander_the_pinned_presentation(self) -> None:
        # c5 IS a permutation. Saying otherwise puts a false claim about a pin
        # into a receipt, which is the one place a false claim may not appear.
        detail = self.verdict().receipt.rows[0].to_wire()
        assert "not a permutation" not in json.dumps(detail)

    def test_fw_move_is_not_a_code_this_host_emits(self) -> None:
        """The original expectation, recorded as refuted.

        Case 8 was specified against `FW-MOVE`. No such code exists, so a test
        expecting it would have failed for a reason unrelated to scope.
        """
        source_roots = [
            Path(__file__).resolve().parents[1],
            Path(__file__).resolve().parents[2] / "omega_engine" / "crates_rs",
        ]
        me = Path(__file__).resolve()
        for root in source_roots:
            for path in root.rglob("*.py"):
                if path.resolve() == me:
                    # This file names the code in order to record that it does
                    # not exist. Without the exclusion the corpus witnesses its
                    # own experiment -- the same shape as the mutation
                    # catalogue's anchor test failing on every mutation it
                    # described. Third occurrence in one sprint.
                    continue
                assert "FW-MOVE" not in path.read_text(encoding="utf-8", errors="ignore")
