"""WP-7 acceptance: the guarantee is tiered, recorded, and never overstated."""

from __future__ import annotations

import pytest

from pfp.domain.carrier_decoding import (
    BLIND_SPOT_TOKEN_BOUNDARY,
    CONSTRAINT_BY_PROVIDER,
    OPENAI_BAN_BIAS,
    ConstraintMode,
    DecodingReceipt,
    carrier_gbnf,
    logit_bias_ban,
    resolve_constraint,
    verify_emission,
)
from pfp.domain.glyph_calculus import Carrier

APL_ALPHA = "⍺"  # U+237A, the symgam.md:77 impostor

CONTRACT_CARRIER = [
    {"symbol": "alpha", "codepoint": "U+03B1"},
    {"symbol": "beta", "codepoint": "U+03B2"},
    {"symbol": "gamma", "codepoint": "U+03B3"},
    {"symbol": "delta", "codepoint": "U+03B4"},
    {"symbol": "epsilon", "codepoint": "U+03B5"},
]


def carrier() -> Carrier:
    return Carrier.from_wire(CONTRACT_CARRIER)


def clean_term() -> str:
    return "".join(member.char for member in carrier().members)


class TestExactness:
    def test_only_a_grammar_is_exact(self) -> None:
        assert ConstraintMode.GRAMMAR.is_exact is True
        assert ConstraintMode.LOGIT_BIAS.is_exact is False
        assert ConstraintMode.UNCONSTRAINED.is_exact is False

    def test_a_bounded_bias_is_not_a_mask(self) -> None:
        """The correction this module exists to carry.

        An earlier framing claimed masking non-carrier logits yields "exact
        zeros". Through an OpenAI-compatible API the strongest available term
        is a bias of -100, which is bounded. Softmax of a large negative logit
        is small and is not zero, so the mode is a strong bias and must not be
        reported as exact.
        """
        assert OPENAI_BAN_BIAS == -100
        assert OPENAI_BAN_BIAS > float("-inf")
        assert not ConstraintMode.LOGIT_BIAS.is_exact

    def test_an_unknown_provider_never_resolves_upward(self) -> None:
        # Guessing a stronger tier than the provider supplied would let a
        # receipt claim a guarantee nobody gave.
        assert resolve_constraint("some-new-vendor") is ConstraintMode.UNCONSTRAINED

    def test_providers_without_a_bias_parameter_are_unconstrained(self) -> None:
        # Neither exposes a per-token bias, so nothing can be imposed at
        # decode time and the receipt must say so.
        assert resolve_constraint("anthropic") is ConstraintMode.UNCONSTRAINED
        assert resolve_constraint("gemini") is ConstraintMode.UNCONSTRAINED

    def test_the_local_path_is_the_one_that_can_be_exact(self) -> None:
        assert resolve_constraint("local") is ConstraintMode.GRAMMAR
        assert resolve_constraint("LOCAL").is_exact

    @pytest.mark.parametrize("provider", sorted(CONSTRAINT_BY_PROVIDER))
    def test_every_declared_provider_resolves_to_its_table_entry(
        self, provider: str
    ) -> None:
        assert resolve_constraint(provider) is CONSTRAINT_BY_PROVIDER[provider]


class TestProviderTableParity:
    def test_every_real_provider_has_a_declared_constraint_tier(self) -> None:
        """The gate, not the table.

        `CONSTRAINT_BY_PROVIDER` is keyed by wire name so the domain does not
        import the swarm's enum. That decoupling is right for the module and
        wrong for the table, which can then drift silently: a provider added
        upstream would resolve to UNCONSTRAINED without anyone deciding that.

        A test may couple where domain code may not, so the coupling lives
        here. This is the same defect class as a capability list nothing
        checks.
        """
        providers = pytest.importorskip(
            "adversary.domain.providers.types"
        )
        declared = {member.value for member in providers.Provider}
        missing = declared - set(CONSTRAINT_BY_PROVIDER)
        assert not missing, (
            f"providers with no declared constraint tier: {sorted(missing)}. "
            "Add them to CONSTRAINT_BY_PROVIDER deliberately rather than "
            "letting them default to UNCONSTRAINED."
        )

        stale = set(CONSTRAINT_BY_PROVIDER) - declared
        assert not stale, f"constraint tiers for providers that no longer exist: {sorted(stale)}"


class TestGrammar:
    def test_the_grammar_admits_every_member_and_names_nothing_else(self) -> None:
        grammar = carrier_gbnf(carrier())
        for member in carrier().members:
            assert f'"{member.char}"' in grammar
        assert APL_ALPHA not in grammar
        assert grammar.startswith("root ::= sym+")

    def test_the_grammar_has_one_alternative_per_member(self) -> None:
        grammar = carrier_gbnf(carrier())
        assert grammar.count("|") == len(CONTRACT_CARRIER) - 1


class TestLogitBias:
    NONE: frozenset[int] = frozenset()

    def test_only_non_carrier_tokens_are_banned(self) -> None:
        vocabulary = {"α": 1, "β": 2, APL_ALPHA: 3, " ": 4, "the": 5}
        bias = logit_bias_ban(vocabulary, carrier(), protected_ids=self.NONE)
        assert bias == {3: OPENAI_BAN_BIAS, 4: OPENAI_BAN_BIAS, 5: OPENAI_BAN_BIAS}

    def test_a_carrier_only_vocabulary_needs_no_bans(self) -> None:
        assert logit_bias_ban({"α": 1, "β": 2}, carrier(), protected_ids=self.NONE) == {}

    def test_a_multi_glyph_token_is_admissible(self) -> None:
        """The bug the membership test shipped.

        `piece in allowed` compares a whole token against a set of single
        characters, so it banned every multi-character piece -- including one
        made entirely of carrier glyphs. BPE merges a small repeated alphabet
        into exactly such pieces, so on a real vocabulary the ban intended to
        constrain the alphabet banned the carrier language itself and left the
        model no admissible token at all.
        """
        vocabulary = {"αβ": 1, "αβγ": 2, "βα": 3}
        assert logit_bias_ban(vocabulary, carrier(), protected_ids=self.NONE) == {}

    def test_a_mixed_token_is_still_banned(self) -> None:
        # The discriminating half: `set(piece) <= allowed` must not degrade
        # into "allow anything longer than one character".
        vocabulary = {"αβ": 1, "α" + APL_ALPHA: 2, "αx": 3}
        bias = logit_bias_ban(vocabulary, carrier(), protected_ids=self.NONE)
        assert bias == {2: OPENAI_BAN_BIAS, 3: OPENAI_BAN_BIAS}

    def test_the_empty_piece_is_admissible(self) -> None:
        # The empty set is a subset of anything, and an empty decode
        # contributes no character, so it cannot leave the carrier.
        assert logit_bias_ban({"": 9}, carrier(), protected_ids=self.NONE) == {}

    def test_a_protected_token_is_never_banned(self) -> None:
        """EOS decodes to no carrier glyph, so the subset test bans it.

        A model that cannot emit EOS cannot stop. The ban meant to constrain
        the alphabet would instead prevent termination, and it would present as
        a hang rather than as a constraint bug.
        """
        vocabulary = {"α": 1, "<|eos|>": 2, "\n": 3, "the": 4}
        bias = logit_bias_ban(
            vocabulary, carrier(), protected_ids=frozenset({2, 3})
        )
        assert 2 not in bias, "EOS must remain emittable or generation cannot end"
        assert 3 not in bias
        assert bias == {4: OPENAI_BAN_BIAS}

    def test_protection_must_be_stated_rather_than_defaulted(self) -> None:
        # Required keyword, for the same reason `carrier_authored_by` is: the
        # dangerous choice must not be the silent one.
        with pytest.raises(TypeError, match="protected_ids"):
            logit_bias_ban({"α": 1}, carrier())  # type: ignore[call-arg]

    def test_the_token_boundary_blind_spot_is_named(self) -> None:
        # The predicate is per token; the property is per string. On byte-level
        # BPE a piece can decode to a fragment of a multi-byte character, so
        # the ban cannot see across the boundary. Named, not implied.
        assert BLIND_SPOT_TOKEN_BOUNDARY
        receipt = DecodingReceipt(
            provider="openai",
            mode=ConstraintMode.LOGIT_BIAS,
            capability=ConstraintMode.LOGIT_BIAS,
            violations=(),
        )
        assert BLIND_SPOT_TOKEN_BOUNDARY in receipt.guarantee
        assert "not made impossible" in receipt.guarantee


class TestVerification:
    def test_a_clean_emission_has_no_violations(self) -> None:
        assert verify_emission(clean_term(), carrier()) == ()

    def test_an_impostor_glyph_is_caught(self) -> None:
        violations = verify_emission("α" + APL_ALPHA, carrier())
        assert len(violations) == 1
        assert "U+237A" in violations[0].detail

    def test_verification_runs_even_where_the_grammar_was_exact(self) -> None:
        """A guarantee is not a substitute for measuring.

        If a run claims GRAMMAR and the emission still left the carrier, the
        guarantee was not delivered -- and only the check can tell us that.
        """
        receipt = DecodingReceipt.measure(
            "local", "α" + APL_ALPHA, carrier(), applied=ConstraintMode.GRAMMAR
        )
        assert receipt.mode is ConstraintMode.GRAMMAR
        assert receipt.emission_within_carrier is False
        assert receipt.guarantee.startswith("violated")


class TestReceipt:
    def test_an_unconstrained_clean_run_does_not_read_as_constrained(self) -> None:
        receipt = DecodingReceipt.measure("anthropic", clean_term(), carrier())
        assert receipt.emission_within_carrier is True
        # Clean, but nothing enforced it. The wire form must not let a reader
        # mistake that for a guarantee.
        assert receipt.mode.is_exact is False
        assert receipt.guarantee.startswith("checked only")
        assert receipt.to_wire()["constraint_is_exact"] is False

    def test_a_biased_run_says_biased_not_exact(self) -> None:
        receipt = DecodingReceipt.measure(
            "openai", clean_term(), carrier(), applied=ConstraintMode.LOGIT_BIAS
        )
        assert receipt.guarantee.startswith("biased")
        assert "not made impossible" in receipt.guarantee

    def test_an_exact_run_says_so(self) -> None:
        receipt = DecodingReceipt.measure(
            "local", clean_term(), carrier(), applied=ConstraintMode.GRAMMAR
        )
        assert receipt.guarantee.startswith("exact")
        assert receipt.to_wire()["constraint_is_exact"] is True

    def test_the_wire_form_carries_provider_mode_and_outcome(self) -> None:
        wire = DecodingReceipt.measure(
            "openai", clean_term(), carrier(), applied=ConstraintMode.LOGIT_BIAS
        ).to_wire()
        assert wire == {
            "provider": "openai",
            "constraint_applied": "logit_bias",
            "constraint_available": "logit_bias",
            "constraint_is_exact": False,
            "emission_within_carrier": True,
            "violations": [],
        }

    def test_violations_are_stringified_without_the_raw_glyph(self) -> None:
        # Receipts are read on cp1252 consoles.
        wire = DecodingReceipt.measure("openai", APL_ALPHA, carrier()).to_wire()
        rendered = str(wire["violations"])
        assert APL_ALPHA not in rendered
        rendered.encode("cp1252")


class TestExactnessIsAppliedNotAvailable:
    """The defect an external review found in this module.

    `mode` was derived from `provider_capability(provider)` -- a lookup on a
    provider NAME. A run against a grammar-capable backend therefore reported
    "exact: non-carrier output was unrepresentable" whether or not a grammar was
    ever handed to a sampler, in the module whose own docstring says a receipt
    claiming a guarantee nobody supplied is worse than no receipt.

    A lever that cannot be shown to have fired may not appear as though it had.
    """

    def test_a_capable_provider_alone_does_not_earn_exactness(self) -> None:
        # `local` CAN take a grammar. This run did not send one.
        receipt = DecodingReceipt.measure("local", clean_term(), carrier())
        assert receipt.capability is ConstraintMode.GRAMMAR
        assert receipt.mode is ConstraintMode.UNCONSTRAINED
        assert receipt.to_wire()["constraint_is_exact"] is False
        assert receipt.guarantee.startswith("checked only")
        assert "not pulled" in receipt.guarantee, (
            "the reader should see that an available lever went unused"
        )

    def test_applied_defaults_down_never_up(self) -> None:
        # Silence is not a guarantee. A caller that says nothing gets nothing.
        assert (
            DecodingReceipt.measure("local", clean_term(), carrier()).mode
            is ConstraintMode.UNCONSTRAINED
        )

    def test_claiming_more_than_the_provider_can_supply_is_refused(self) -> None:
        # Anthropic exposes no per-token bias, so a run cannot have applied one.
        # Silently clamping would hide a caller bug; refusing surfaces it.
        with pytest.raises(ValueError, match="can only supply"):
            DecodingReceipt.measure(
                "anthropic", clean_term(), carrier(), applied=ConstraintMode.GRAMMAR
            )

    def test_the_wire_separates_what_was_done_from_what_was_possible(self) -> None:
        wire = DecodingReceipt.measure(
            "openai", clean_term(), carrier()
        ).to_wire()
        assert wire["constraint_applied"] == "unconstrained"
        assert wire["constraint_available"] == "logit_bias"
