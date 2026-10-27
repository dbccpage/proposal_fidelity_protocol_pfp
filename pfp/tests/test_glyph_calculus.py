"""WP-4 acceptance: the analyzer refuses the document that motivated it.

The fixtures below are the defects as they appear in `_ooutwire/symgam.md` in
the CODA repository, at the revision reviewed on 2026-09-01. That file is not
in this repository, so the constructs are reproduced here with their original
line numbers rather than read from disk -- a test that reaches into another
checkout is a test that fails for reasons unrelated to the code.

Provenance of each fixture is given at its use.
"""

from __future__ import annotations

import unicodedata

import pytest

from pfp.domain.glyph_calculus import (
    CLOSED_OPS,
    REFUSAL_CARRIER_CODEPOINT,
    REFUSAL_DUPLICATE_KEY,
    REFUSAL_OP_UNDECLARED,
    REFUSAL_UNKNOWN_FIELD,
    Carrier,
    check_no_duplicate_keys,
    check_no_unknown_fields,
    lint_ledger_row,
    lint_rows,
)

# The carrier the design note declares: five Greek letters, alpha to epsilon.
CONTRACT_CARRIER = [
    {"symbol": "alpha", "codepoint": "U+03B1"},
    {"symbol": "beta", "codepoint": "U+03B2"},
    {"symbol": "gamma", "codepoint": "U+03B3"},
    {"symbol": "delta", "codepoint": "U+03B4"},
    {"symbol": "epsilon", "codepoint": "U+03B5"},
]

# Written as escapes on purpose: these four are mutually indistinguishable in a
# source listing, which is the entire point of the check below.
GREEK_ALPHA = "α"  # GREEK SMALL LETTER ALPHA
APL_ALPHA = "⍺"  # APL FUNCTIONAL SYMBOL ALPHA -- symgam.md:77 node 1
MATH_ALPHA = "\U0001d6c2"  # MATHEMATICAL BOLD SMALL ALPHA
CYRILLIC_A = "а"  # CYRILLIC SMALL LETTER A


def contract_carrier() -> Carrier:
    return Carrier.from_wire(CONTRACT_CARRIER)


class TestCarrierPin:
    def test_the_declared_carrier_admits_its_own_members(self) -> None:
        carrier = contract_carrier()
        term = "".join(member.char for member in carrier.members)
        assert carrier.check_term(term) == ()

    def test_the_apl_alpha_from_symgam_line_77_is_refused(self) -> None:
        # symgam.md:77 declares node 1 as U+237A while nodes 2-5 are Greek,
        # under a section promising "No other symbols are allowed" and naming
        # no validator. On the page the substitution is invisible.
        findings = contract_carrier().check_term(APL_ALPHA + "β")
        assert len(findings) == 1
        assert findings[0].code == REFUSAL_CARRIER_CODEPOINT
        assert "U+237A" in findings[0].detail
        # Advisory, not the decision: the name similarity is what makes it
        # invisible to a reader, so the finding says so.
        assert "looks like alpha" in findings[0].detail

    def test_nfkc_would_not_have_caught_it(self) -> None:
        """Negative control for the implementation that was almost written.

        Folding a suspect character with NFKC and testing membership is the
        obvious design. It fails on the exact attack in the source document:
        the APL alpha has no compatibility decomposition. Only the
        mathematical alphanumeric folds.

        If this assertion ever flips, the allowlist is still correct and this
        test should be updated rather than the analyzer relaxed.
        """
        assert unicodedata.normalize("NFKC", APL_ALPHA) == APL_ALPHA
        assert unicodedata.normalize("NFKC", CYRILLIC_A) == CYRILLIC_A
        assert unicodedata.normalize("NFKC", MATH_ALPHA) == GREEK_ALPHA

        # The allowlist refuses all three without anticipating any of them.
        carrier = contract_carrier()
        for impostor in (APL_ALPHA, MATH_ALPHA, CYRILLIC_A):
            assert carrier.check_term(impostor), (
                f"U+{ord(impostor):04X} is not a declared member and must be refused"
            )

    def test_each_offending_codepoint_is_reported_once(self) -> None:
        findings = contract_carrier().check_term(APL_ALPHA * 5 + CYRILLIC_A)
        assert len(findings) == 2

    def test_a_finding_never_carries_the_raw_glyph(self) -> None:
        # Findings are printed on cp1252 consoles, where emitting the glyph
        # turns a refusal into a UnicodeEncodeError.
        detail = contract_carrier().check_term(APL_ALPHA)[0].detail
        assert APL_ALPHA not in detail
        detail.encode("cp1252")

    def test_two_symbols_for_one_codepoint_is_refused_at_declaration(self) -> None:
        with pytest.raises(ValueError, match="more than one symbol"):
            Carrier.from_wire(
                [
                    {"symbol": "alpha", "codepoint": "U+03B1"},
                    {"symbol": "a", "codepoint": "U+03B1"},
                ]
            )

    def test_an_unknown_field_on_a_member_is_refused(self) -> None:
        with pytest.raises(ValueError, match="unknown fields"):
            Carrier.from_wire(
                [{"symbol": "alpha", "codepoint": "U+03B1", "weight": 1}]
            )


class TestOpLinter:
    @pytest.mark.parametrize("op", CLOSED_OPS)
    def test_every_declared_op_is_admitted(self, op: str) -> None:
        assert lint_ledger_row(f"{op} period(c5) = 5") == ()

    @pytest.mark.parametrize(
        "sentence",
        ["op: PROVE period = 5", "op PROVE period = 5", "PROVE period = 5"],
    )
    def test_the_op_prefix_forms_in_the_corpus_all_parse(self, sentence: str) -> None:
        assert lint_ledger_row(sentence) == ()

    def test_qed_is_refused(self) -> None:
        # symgam.md:243 and :437 open rows with `op QED`. QED was never in the
        # closed set and is not in the contract's nine either.
        findings = lint_ledger_row("op QED")
        assert len(findings) == 1
        assert findings[0].code == REFUSAL_OP_UNDECLARED
        assert "'QED'" in findings[0].detail

    def test_land_is_now_declared_and_therefore_admitted(self) -> None:
        """The correction to the build schedule, encoded.

        symgam.md used `op: LAND` at :87, :128 and :194 against eight declared
        ops that omitted it, and the review counted that as a defect. The
        glyph-calculus contract closed the gap by *declaring* LAND -- the set
        is nine, not eight -- so under the contract this module implements,
        LAND is legal. The schedule's acceptance criterion still holds, but it
        holds on QED and the carrier, not on LAND.
        """
        assert "LAND" in CLOSED_OPS
        assert lint_ledger_row("op: LAND gamma") == ()

    def test_a_row_with_no_op_is_refused(self) -> None:
        assert lint_ledger_row("   ")[0].code == REFUSAL_OP_UNDECLARED
        assert lint_ledger_row("op:")[0].code == REFUSAL_OP_UNDECLARED

    def test_rows_are_numbered_from_one(self) -> None:
        findings = lint_rows(["PROVE ok", "op QED"])
        assert len(findings) == 1
        assert findings[0].row == 2


class TestStrictParse:
    def test_a_repeated_key_is_refused_rather_than_resolved(self) -> None:
        findings = check_no_duplicate_keys(
            [("period", 5), ("semantics", "x"), ("period", 7)]
        )
        assert len(findings) == 1
        assert findings[0].code == REFUSAL_DUPLICATE_KEY
        assert "'period'" in findings[0].detail

    def test_distinct_keys_pass(self) -> None:
        assert check_no_duplicate_keys([("a", 1), ("b", 2)]) == ()

    def test_an_undeclared_field_is_refused(self) -> None:
        findings = check_no_unknown_fields(
            {"cycle_id": "c5", "period": 5, "vibe": "good"},
            allowed=("cycle_id", "period"),
        )
        assert len(findings) == 1
        assert findings[0].code == REFUSAL_UNKNOWN_FIELD
        assert "'vibe'" in findings[0].detail


class TestAcceptance:
    def test_the_contract_ledger_lints_clean(self) -> None:
        # The worked example from the design note's receipt contract.
        rows = [
            "PROVE period(c5) = 5",
            "REDUCE 17 mod 5 = 2",
            "LAND successor^2(alpha) = gamma",
        ]
        assert lint_rows(rows) == ()

    def test_the_source_document_fails_its_own_linter(self) -> None:
        """The acceptance criterion for WP-4.

        Both surviving defects, in one pass: an op outside the closed set, and
        a carrier glyph outside the declared codepoints.
        """
        rows = [
            "PROVE period(c5) = 5",
            "op QED",  # symgam.md:243, :437
            f"LAND {APL_ALPHA}",  # carrier from symgam.md:77
        ]
        findings = lint_rows(rows, carrier=contract_carrier())
        codes = {finding.code for finding in findings}
        assert codes == {REFUSAL_OP_UNDECLARED, REFUSAL_CARRIER_CODEPOINT}
        assert {finding.row for finding in findings} == {2, 3}


class TestTheOpPredicateIsPinned:
    """The one mutant an external adversary left alive in our suite.

    Our linter was already case-sensitive and already correct. Nothing tested
    it, so mutating `token not in CLOSED_OPS` to `token.upper() not in
    CLOSED_OPS` left the whole suite green. An untested predicate is a
    coincidence, not a decision -- and this one is load-bearing beyond
    correctness: with the mutant applied, `verify_glyph_reply` lints "prove x"
    clean and then `ReceiptRow` rejects the op, raising out of the use case.
    """

    @pytest.mark.parametrize("variant", ["prove", "Prove", "pRoVe", "PROVe"])
    def test_a_case_variant_is_not_the_declared_op(self, variant: str) -> None:
        findings = lint_ledger_row(f"{variant} period(c5) = 5")
        assert len(findings) == 1
        assert findings[0].code == REFUSAL_OP_UNDECLARED
        assert "case variant of PROVE" in findings[0].detail, (
            "the refusal should tell a reader why a word that looks like an op "
            "is not one"
        )

    def test_the_exact_token_still_passes(self) -> None:
        # Guards the fixture: if PROVE stopped being admitted, the tests above
        # would pass for the wrong reason.
        assert lint_ledger_row("PROVE period(c5) = 5") == ()

    def test_a_row_declares_exactly_one_op(self) -> None:
        # The contract says every row begins with exactly ONE op. Two make the
        # evidence class ambiguous, since the op IS the evidence class.
        findings = lint_ledger_row("PROVE SHOW period(c5) = 5")
        assert len(findings) == 1
        assert findings[0].code == REFUSAL_OP_UNDECLARED
        assert "exactly one op" in findings[0].detail

    @pytest.mark.parametrize(
        "sentence", ["op: PROVE period = 5", "op PROVE period = 5"]
    )
    def test_the_op_prefix_is_not_mistaken_for_a_second_op(
        self, sentence: str
    ) -> None:
        # The prefix forms carry two tokens before the statement. Counting
        # naively makes a row's own op look like a second one and refuses every
        # well-formed row in the corpus.
        assert lint_ledger_row(sentence) == ()
