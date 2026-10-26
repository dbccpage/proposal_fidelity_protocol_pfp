"""Tier 2 E2E Test Suite: Boundary & Corner Cases (Domain Limits).

AuthorityEffect: None.
Reference: TEST_INFRA.md Tier 2 Specification.
Soviet Lev Landau Falsification Methodology:
Every test explicitly documents Invariant, Break, Witness, and Mutation.
Claim Hygiene: Uses bounded, defensible phrasing; zero forbidden hype words.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import pytest

# Domain Exact Rational Kernel
from omega_engine_pfp.domain.exact.q import Q, ONE, ZERO, parse_q, fmt_q
from omega_engine_pfp.domain.exact.errors import ExactError

# Domain Packet Codec & Sealing
from omega_engine_pfp.domain.packet_codec import (
    PacketCodec,
    canonical_json_bytes,
    compute_sha256,
)
from omega_engine_pfp.domain.exceptions import SymbolGameValidationError

# Presentation Pins
from omega_engine_pfp.domain.presentation_pins import (
    PresentationPins,
    PinnedPresentation,
    PinnedRule,
)

# Carrier Constrained Decoding
from omega_engine_pfp.domain.carrier_decoding import (
    DecodingReceipt,
    ConstraintMode,
    provider_capability,
    verify_emission,
    carrier_gbnf,
    logit_bias_ban,
    OPENAI_BAN_BIAS,
    BLIND_SPOT_TOKEN_BOUNDARY,
)
from omega_engine_pfp.domain.glyph_calculus import Carrier, CarrierMember, Finding

# Tower Grammar, Parser, and Wire
from omega_engine_pfp.domain.tower.parser import (
    parse_packet,
    serialize_packet,
    validate_level3_simplex,
    validate_rational,
    validate_dual_cert,
    validate_level7_orbit,
    SimplexValidationError,
    RationalValidationError,
    OrbitValidationError,
    DualWitnessError,
    LexicalError,
    SyntaxError,
    ArityError,
    Atom,
    App,
    Diff,
)
from omega_engine_pfp.domain.tower.wire import (
    parse_wire,
    emit_wire,
    parse_compact,
    emit_compact,
    parse_postfix,
    emit_postfix,
    parse_tagged_json,
    emit_tagged_json,
    parse_dag,
    emit_dag,
    WireError,
    MAX_DEPTH,
)

# Epistemic Immune System & Allostery
from omega_engine_epistemic_immune_system.domain.allostery import (
    AllostericConsensusGate,
    AllostericDecision,
    HillParameters,
)
from omega_engine_epistemic_immune_system.domain.value_objects import AllosteryRefusal
from omega_engine_epistemic_immune_system.domain.danger_gate import (
    TwoSignalDangerGate,
    DangerEvaluationResult,
)
from omega_engine_epistemic_immune_system.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
    DetectorRule,
)

# Quarantine Persistence
from omega_engine_pfp.domain.mssn_research.grammar.entities import (
    EpistemicQuarantineLedger,
)
from omega_engine_pfp.infrastructure.adapters.mssn_research.contracts.grammar.ledger_codec import (
    serialize_ledger_to_jsonl,
    deserialize_ledger_from_jsonl,
)
from omega_engine_pfp.domain.mssn_research.grammar.exact_structures import (
    QuarantinedShadowPacket,
    PontryaginKillFlags,
    HostFenceAudit,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import (
    StageLevel,
)
from omega_engine_pfp.domain.mssn_research.grammar.errors import (
    LedgerTruncationError,
    LedgerIntegrityError,
    ScopeBoundaryViolationError,
    LedgerSerializationError,
)


class TestExactRationalBoundariesTier2:
    """Tier 2 Boundary Tests: Exact Rational Kernel Limits (Prompt 47)."""

    def test_b01_zero_denominator_refusal(self) -> None:
        """Verify Q constructor and Q.of refuse zero denominator.

        - Invariant: A fraction with zero denominator is ill-defined and refused under RR-DENOMINATOR.
        - Break: System returns Infinity, NaN, or creates an invalid zero-denominator object.
        - Witness: ExactError with code 'RR-DENOMINATOR'.
        - Mutation: Removing d <= 0 check leads to ZeroDivisionError during arithmetic.
        """
        with pytest.raises(ExactError) as exc_info:
            Q(1, 0)
        assert exc_info.value.code == "RR-DENOMINATOR"

        with pytest.raises(ExactError) as exc_info2:
            Q.of(5, 0)
        assert exc_info2.value.code == "RR-DENOMINATOR"

    def test_b02_negative_denominator_constructor_refusal(self) -> None:
        """Verify Q constructor requires strictly positive denominator (d > 0).

        - Invariant: Q(num, den) demands den > 0; Q.of(num, den) normalizes signs.
        - Break: Unnormalized negative denominator admitted in raw constructor.
        - Witness: Q(3, -4) raises ExactError('RR-DENOMINATOR'); Q.of(3, -4) produces Q(-3, 4).
        - Mutation: Allowing den < 0 in constructor breaks ordering cross-multiplication.
        """
        with pytest.raises(ExactError) as exc_info:
            Q(3, -4)
        assert exc_info.value.code == "RR-DENOMINATOR"

        normalized = Q.of(3, -4)
        assert normalized.num == -3
        assert normalized.den == 4
        assert str(normalized) == "-3/4"

    def test_b03_unreduced_fraction_constructor_refusal(self) -> None:
        """Verify Q constructor refuses unreduced pairs (gcd(num, den) != 1).

        - Invariant: Q constructor requires already-reduced coprime pairs; Q.of normalizes via gcd.
        - Break: Non-reduced representation enters discrete state representations.
        - Witness: Q(6, 8) raises ExactError('RR-NOT-REDUCED'); Q.of(6, 8) yields Q(3, 4).
        - Mutation: Omitting coprime check allows non-unique representation of identical rationals.
        """
        with pytest.raises(ExactError) as exc_info:
            Q(6, 8)
        assert exc_info.value.code == "RR-NOT-REDUCED"

        reduced = Q.of(6, 8)
        assert reduced.num == 3
        assert reduced.den == 4

    def test_b04_type_confusion_rejection(self) -> None:
        """Verify Q constructor refuses non-integer types (bool, float, None, str).

        - Invariant: _int helper rejects bool (subclass of int), float, None, and strings.
        - Break: True/False treated as 1/0 or float admitted via implicit conversion.
        - Witness: ExactError with code 'RR-FLOAT' or 'RR-NOT-INTEGER'.
        - Mutation: Removing isinstance(x, bool) allows bool arithmetic in exact rationals.
        """
        with pytest.raises(ExactError) as exc_bool:
            Q(True, 1)  # type: ignore[arg-type]
        assert exc_bool.value.code == "RR-NOT-INTEGER"

        with pytest.raises(ExactError) as exc_float:
            Q(0.0, 1)  # type: ignore[arg-type]
        assert exc_float.value.code == "RR-FLOAT"

        with pytest.raises(ExactError) as exc_str:
            Q("3", 4)  # type: ignore[arg-type]
        assert exc_str.value.code == "RR-NOT-INTEGER"

    def test_b05_division_by_zero_rational_refusal(self) -> None:
        """Verify Q division by ZERO raises ExactError('RR-DIVISION-BY-ZERO').

        - Invariant: Zero rational has no multiplicative inverse.
        - Break: Zero division produces float inf or unhandled ZeroDivisionError.
        - Witness: ExactError with code 'RR-DIVISION-BY-ZERO'.
        - Mutation: Delegating to Python float division bypasses exact error taxonomy.
        """
        q = Q(3, 4)
        with pytest.raises(ExactError) as exc_info:
            q / ZERO
        assert exc_info.value.code == "RR-DIVISION-BY-ZERO"

    def test_b06_parse_q_canonical_string_boundaries(self) -> None:
        """Verify parse_q rejects non-canonical representations (leading plus, decimals, bare ints).

        - Invariant: parse_q matches exact regex '^(0|-?[1-9][0-9]*)/([1-9][0-9]*)$'.
        - Break: Permissive parsing admits non-canonical string forms without reduction check.
        - Witness: parse_q('5'), parse_q('+1/2'), parse_q('1/0'), parse_q('2/4') raise ExactError.
        - Mutation: Permitting bare integer parsing breaks canonical 'p/q' wire contract.
        """
        invalid_strings = ["5", "+1/2", "1/0", "2/4", "0/0", "01/2", "1.5", "", "1/-2"]
        for s in invalid_strings:
            with pytest.raises(ExactError):
                parse_q(s)

        # Valid boundary canonical values
        assert parse_q("0/1") == ZERO
        assert parse_q("1/1") == ONE
        assert parse_q("-1/1") == -ONE

    def test_b07_exact_type_equality_negative_controls(self) -> None:
        """Verify Q.__eq__ returns False across heterogeneous types without raising.

        - Invariant: type(self) is type(other) guard returns False on any cross-class comparison.
        - Break: Q(1, 1) == 1.0 or Q(1, 1) == 1 returns True.
        - Witness: Q(1, 1) != 1.0; Q(1, 1) != 1; Q(1, 1) != "1/1".
        - Mutation: Using duck typing (float conversion) causes semantic type confusion.
        """
        q = Q(1, 1)
        assert (q == 1.0) is False
        assert (q == 1) is False
        assert (q == Fraction(1, 1)) is False
        assert (q == "1/1") is False
        assert (q == (1, 1)) is False


class TestPacketCodecBoundariesTier2:
    """Tier 2 Boundary Tests: PacketCodec & Canonical Sealing (Prompt 44)."""

    def test_b08_empty_payload_sealing_determinism(self) -> None:
        """Verify empty dictionary payload seals deterministically and verifies cleanly.

        - Invariant: canonical_json_bytes({}) produces b'{}' with zero whitespace.
        - Break: Empty dictionary causes serialization KeyError or null digest.
        - Witness: PacketCodec.verify(sealed) == (True, sha, 'OK').
        - Mutation: Failing to normalize empty dictionary causes payload hash mismatch.
        """
        empty_payload: dict[str, Any] = {}
        sealed = PacketCodec.seal(empty_payload, packet_family="empty_turn")
        assert sealed["payload"] == {}
        assert sealed["payload_sha256"] == compute_sha256(canonical_json_bytes(empty_payload))

        is_valid, actual_sha, msg = PacketCodec.verify(sealed)
        assert is_valid
        assert msg == "OK"

    def test_b09_unicode_nfc_key_normalization(self) -> None:
        """Verify Unicode normalization: NFD and NFC string keys map to identical canonical bytes.

        - Invariant: All dictionary keys and string scalars are normalized to NFC before hashing.
        - Break: Composed vs decomposed Unicode strings hash to different values.
        - Witness: Digest of decomposed e-acute key matches composed e-acute key.
        - Mutation: Skipping NFC normalization allows equivalent Unicode strings to alter hash.
        """
        import unicodedata
        # Composed 'é' (U+00E9) vs decomposed 'e' + combining acute (U+0065 U+0301)
        composed = "caf\u00e9"
        decomposed = "cafe\u0301"
        assert composed != decomposed  # different python byte sequences

        bytes_comp = canonical_json_bytes({composed: "val"})
        bytes_decomp = canonical_json_bytes({decomposed: "val"})
        assert bytes_comp == bytes_decomp
        with pytest.raises(SymbolGameValidationError, match="collapses two keys"):
            canonical_json_bytes({composed: "a", decomposed: "b"})

    def test_b10_single_bit_flip_payload_tamper_detection(self) -> None:
        """Verify single bit flip in sealed payload causes immediate verification failure.

        - Invariant: Cryptographic SHA-256 bijection detects 100% of bit alterations.
        - Break: Bit corruption in payload passes verification without error.
        - Witness: PacketCodec.verify returns is_valid=False with 'Payload SHA-256 mismatch'.
        - Mutation: Bypassing payload_sha256 recalculation masks transmission errors.
        """
        payload = {"step": 42, "data": "incompressible_token"}
        sealed = PacketCodec.seal(payload, packet_family="step_packet")

        # Invert bit in data string
        tampered = dict(sealed)
        tampered["payload"] = {"step": 42, "data": "incompressible_tokeo"}  # 'n' -> 'o'

        is_valid, computed_sha, msg = PacketCodec.verify(tampered)
        assert not is_valid
        assert "Payload SHA-256 mismatch" in msg

    def test_b11_missing_required_envelope_fields_refusal(self) -> None:
        """Verify PacketCodec.verify raises SymbolGameValidationError when required fields are missing.

        - Invariant: Envelopes lacking 'payload' or 'payload_sha256' are structurally invalid.
        - Break: Malformed dictionary access raises unhandled KeyError escaping API boundary.
        - Witness: SymbolGameValidationError raised.
        - Mutation: Using dict.get without assertion returns incorrect verification tuple.
        """
        with pytest.raises(SymbolGameValidationError):
            PacketCodec.verify({"only_header": 1})

        with pytest.raises(SymbolGameValidationError):
            PacketCodec.verify({"payload": {"a": 1}})  # missing payload_sha256


class TestWireAndParserBoundariesTier2:
    """Tier 2 Boundary Tests: Gamma38 Wire, Recursion Depth & Syntax (Prompt 48)."""

    def test_b12_empty_wire_string_refusal(self) -> None:
        """Verify parse_packet and parse_wire refuse empty string.

        - Invariant: Wire protocol requires at least one structural delimiter ('<' or 'op<').
        - Break: Empty string returns None or enters infinite loop.
        - Witness: SyntaxError raised by parse_packet; WireError raised by parse_wire.
        - Mutation: Returning empty AST node for empty input admits empty packets.
        """
        with pytest.raises(SyntaxError, match="empty input"):
            parse_packet("")

        with pytest.raises(WireError, match="empty or oversized"):
            parse_wire("")

    def test_b13_unclosed_application_syntax_error(self) -> None:
        """Verify parser refuses unclosed application brackets with exact position reporting.

        - Invariant: Every 'op<' must have a balancing '>'.
        - Break: Parser hangs or consumes trailing text into unbounded child list.
        - Witness: SyntaxError raised with reason 'unclosed application'.
        - Mutation: Failing to check EOF inside while loop causes hang on unclosed op.
        """
        with pytest.raises(SyntaxError, match="unclosed application"):
            parse_packet("op<<0><1>")

        with pytest.raises(WireError, match="unclosed application"):
            parse_wire("op<<0><1>")

    def test_b14_multiple_outer_packets_trailing_content_refusal(self) -> None:
        """Verify Parsing Law 1: Exactly one complete outer packet permitted.

        - Invariant: Trailing characters after the first outer packet close are forbidden.
        - Break: Second packet or garbage accepted as valid trailing payload.
        - Witness: SyntaxError raised with reason 'multiple outer packets or trailing garbage'.
        - Mutation: Omitting EOF check on cursor accepts stream concatenations without isolation.
        """
        with pytest.raises(SyntaxError, match="multiple outer packets or trailing garbage"):
            parse_packet("<><>")

        with pytest.raises(WireError, match="multiple packets or trailing data"):
            parse_wire("<><>")

    def test_b15_recursion_depth_limit_boundary(self) -> None:
        """Verify parse_wire enforces MAX_DEPTH = 64 to prevent stack overflow attacks.

        - Invariant: Nesting depth exceeding 64 raises WireError('recursion depth limit').
        - Break: Unbounded recursive descent causes Python RecursionError / crash.
        - Witness: WireError with message 'recursion depth limit'.
        - Mutation: Omitting depth check exposes process to stack exhaustion.
        """
        # Create nested application with depth 66
        deep_expr = "op<" * 66 + "<0>" + ">" * 66
        with pytest.raises(WireError, match="recursion depth limit"):
            parse_wire(deep_expr)

    def test_b16_illegal_characters_outside_gamma38(self) -> None:
        """Verify strict lexical scanner rejects characters outside Gamma38 (36 alnum + '<' + '>').

        - Invariant: Character set is strictly frozenset('0123456789abcdefghijklmnopqrstuvwxyz<>').
        - Break: Whitespace, uppercase letters, underscores, or control characters admitted.
        - Witness: LexicalError raised naming offending character and position.
        - Mutation: Using re.match without exact character allowlist accepts whitespace.
        """
        bad_inputs = [
            "<hello world>",  # whitespace
            "<ABC>",          # uppercase
            "<a_b>",          # underscore
            "<\n>",           # newline
            "<\t>",           # tab
            "<@>",            # punctuation
        ]
        for bad in bad_inputs:
            with pytest.raises((LexicalError, WireError)):
                parse_packet(bad)


class TestTopologicalGrammarBoundariesTier2:
    """Tier 2 Boundary Tests: Simplex, Orbit, and Duality Boundaries (P23, P28, P34)."""

    def test_b17_simplex_empty_and_zero_dimension_boundaries(self) -> None:
        """Verify Level 3 Simplex validator at dimension boundary limits.

        - Invariant: Simplex requires at least dimension atom; dim 0 requires exactly 1 vertex.
        - Break: Dim 0 accepts multiple vertices or 0 vertices.
        - Witness: SimplexValidationError on dimension mismatch.
        - Mutation: Setting expected_count = dim instead of dim + 1 breaks simplicial homology.
        """
        # Valid 0-simplex: dim 0, exactly 1 vertex
        s0 = parse_packet("op<<101><0><0>>")
        assert isinstance(s0, App)
        validate_level3_simplex(s0)

        # Broken 0-simplex: dim 0 with 2 vertices
        bad_s0 = parse_packet("op<<101><0><0><1>>")
        assert isinstance(bad_s0, App)
        with pytest.raises(SimplexValidationError, match="Dimension mismatch"):
            validate_level3_simplex(bad_s0)

    def test_b18_orbit_length_mismatch_boundary(self) -> None:
        """Verify Level 7 orbit validator detects declared period != vertex sequence length.

        - Invariant: Declared integer period must match count of child vertex atoms.
        - Break: Orbit claims period 3 but provides 4 vertex states.
        - Witness: OrbitValidationError with 'Length consistency violation'.
        - Mutation: Skipping length comparison allows false periodic orbit certificates.
        """
        # Declared period 3 (<11>), but 4 vertices (<0>, <1>, <0>, <1>)
        bad_orbit = parse_packet("op<<1110><11><0><0><1><0><1>>")
        assert isinstance(bad_orbit, App)
        with pytest.raises(OrbitValidationError, match="Length consistency violation"):
            validate_level7_orbit(bad_orbit)

    def test_b19_orbit_false_primitive_claim_refusal(self) -> None:
        """Verify Level 7 orbit validator catches non-primitive orbits claiming primitive flag <1>.

        - Invariant: Orbit claiming primitive flag <1> must have minimal period equal to declared period.
        - Break: Periodic sequence (e.g. 0,1,0,1 with period 4) claiming primitivity is accepted.
        - Witness: OrbitValidationError with 'MalformedPrimitiveClaim'.
        - Mutation: Trusting primitive_flag atom without orbit shift comparison admits composite orbits.
        """
        # Sequence 0, 1, 0, 1 has minimal period 2, but declares period 4 and asserts primitive flag <1>
        false_prim = parse_packet("op<<1110><100><1><0><1><0><1>>")
        assert isinstance(false_prim, App)
        with pytest.raises(OrbitValidationError, match="MalformedPrimitiveClaim"):
            validate_level7_orbit(false_prim)

    def test_b20_dual_witness_unbalanced_vertex_circulation_refusal(self) -> None:
        """Verify Level 8 Dual Certificate catches circulation flow leakage at a vertex.

        - Invariant: Kirchhoff's law: sum of incoming flows equals sum of outgoing flows at every vertex.
        - Break: Flow vector creates or destroys circulation mass at a vertex.
        - Witness: DualWitnessError with 'Flow conservation violated'.
        - Mutation: Skipping net flow accumulation admits unbounded potential gradients.
        """
        # Flow 1->2 has mass 1, but no return flow 2->1 (net at vertex 1 is -1, at vertex 2 is +1)
        unbalanced_flow = parse_packet(
            "op<<10001>"
            "op<<10010><0><1><1>>"  # primal mass 1/1
            "op<<10010><0><1><1>>"  # dual mass 1/1
            "op<<11>"
            "op<<10011><1><10>op<<10010><0><1><1>>>"  # only 1 -> 2
            ">>"
        )
        assert isinstance(unbalanced_flow, App)
        with pytest.raises(DualWitnessError, match="Flow conservation violated"):
            validate_dual_cert(unbalanced_flow)


class TestPresentationPinsBoundariesTier2:
    """Tier 2 Boundary Tests: Presentation Pins & Rewrite Cycles (Prompt 45)."""

    def test_b21_non_permutation_presentation_returns_none(self) -> None:
        """Verify PinnedPresentation.successor_map returns None if rules do not form a total permutation.

        - Invariant: Only presentations whose rules form a total bijection on the signature have order.
        - Break: Non-bijective system returns partial cycle or enters infinite loop.
        - Witness: successor_map is None, period is None, apply_successor returns None.
        - Mutation: Weakening bijection check allows dead-end or branch rewriting.
        """
        # Presentation where rule maps 'a' -> 'b', but 'b' has no rule (not total)
        rule = PinnedRule(name="r1", lhs="a", rhs="b")
        pres = PinnedPresentation(name="broken", signature=("a", "b"), rules=(rule,))

        assert pres.successor_map is None
        assert pres.period is None
        assert pres.apply_successor("a", 1) is None

    def test_b22_presentation_pins_duplicate_name_refusal(self) -> None:
        """Verify PresentationPins.from_wire refuses duplicate pin names.

        - Invariant: Pinned presentation names must be strictly unique within the host pin set.
        - Break: Duplicate pin silently overwrites or aliases previous presentation.
        - Witness: ValueError raised with 'declared twice'.
        - Mutation: Using last-one-wins dictionary assignment allows shadow presentations.
        """
        dup_pins = [
            {"name": "c2", "presentation": {"signature": ["a", "b"], "rules": [
                {"name": "r1", "lhs": "a", "rhs": "b"},
                {"name": "r2", "lhs": "b", "rhs": "a"},
            ]}},
            {"name": "c2", "presentation": {"signature": ["a", "b"], "rules": []}},
        ]
        with pytest.raises(ValueError, match="declared twice"):
            PresentationPins.from_wire(dup_pins)

    def test_b23_presentation_period_with_disjoint_orbits(self) -> None:
        """Verify PinnedPresentation.period computes LCM of disjoint cycle lengths, not signature size.

        - Invariant: Order of permutation is LCM(cycle_lengths).
        - Break: Host reports len(signature) instead of LCM, failing on disjoint orbits.
        - Witness: Signature of size 5 with 2-cycle and 3-cycle has period 6 != 5.
        - Mutation: Returning len(self.signature) gives wrong answer on disconnected systems.
        """
        # (a <-> b) (length 2) and (c -> d -> e -> c) (length 3). Total size = 5. Period = 6.
        rules = (
            PinnedRule("r1", "a", "b"),
            PinnedRule("r2", "b", "a"),
            PinnedRule("r3", "c", "d"),
            PinnedRule("r4", "d", "e"),
            PinnedRule("r5", "e", "c"),
        )
        pres = PinnedPresentation(name="disjoint", signature=("a", "b", "c", "d", "e"), rules=rules)
        assert pres.period == 6
        assert pres.apply_successor("a", 6) == "a"
        assert pres.apply_successor("c", 6) == "c"


class TestCarrierDecodingBoundariesTier2:
    """Tier 2 Boundary Tests: Carrier Constrained Decoding Boundaries (Prompt 46)."""

    def test_b24_protected_eos_token_boundary_in_logit_bias(self) -> None:
        """Verify logit_bias_ban never bans protected tokens (e.g. EOS) even if not in carrier.

        - Invariant: Protected IDs passed to logit_bias_ban must be exempt from negative bias.
        - Break: EOS token is banned, causing generative models to enter infinite loop.
        - Witness: protected_id not in logit_bias_ban returned dictionary.
        - Mutation: Defaulting protected_ids to empty set bans termination tokens.
        """
        carrier = Carrier((CarrierMember("a", "U+0061"),))
        token_vocab = {
            "a": 101,
            "b": 102,
            "<|endoftext|>": 50256,
        }
        protected_ids = frozenset({50256})

        bans = logit_bias_ban(token_vocab, carrier, protected_ids=protected_ids)

        # 'b' should be banned
        assert 102 in bans
        assert bans[102] == OPENAI_BAN_BIAS

        # 'a' is in carrier -> not banned
        assert 101 not in bans

        # EOS is protected -> not banned despite not being in carrier
        assert 50256 not in bans

    def test_b25_unknown_provider_resolves_down_to_unconstrained(self) -> None:
        """Verify unknown or unconfigured provider names resolve down to UNCONSTRAINED.

        - Invariant: Epistemic security: unknown backends never inherit unearned capabilities.
        - Break: Unregistered provider defaults upward or crashes.
        - Witness: provider_capability('new_unregistered_model') == ConstraintMode.UNCONSTRAINED.
        - Mutation: Defaulting to GRAMMAR or LOGIT_BIAS grants unverified claims.
        """
        assert provider_capability("exotic_provider_xyz") == ConstraintMode.UNCONSTRAINED
        assert provider_capability(" ") == ConstraintMode.UNCONSTRAINED


class TestQuarantinePersistenceBoundariesTier2:
    """Tier 2 Boundary Tests: Cemetery & Ledger Truncation Boundaries (Prompt 10, 35)."""

    def test_b26_empty_ledger_file_refusal(self) -> None:
        """Verify deserialize_ledger_from_jsonl refuses empty or whitespace-only content.

        - Invariant: A valid quarantine ledger must contain at least a HEADER record.
        - Break: Empty file returns empty ledger object without error.
        - Witness: Result is refusal with code HOST_VERIFICATION_REQUIRED.
        - Mutation: Returning Ok(EpistemicQuarantineLedger.empty()) allows silent file wipes.
        """
        res = deserialize_ledger_from_jsonl("   \n  \n")
        assert res.is_refusal
        assert isinstance(res.refusal, LedgerTruncationError)

    def test_b27_log_extension_beyond_head_refusal(self) -> None:
        """Verify deserialize_ledger_from_jsonl refuses spurious appending beyond declared head count.

        - Invariant: If actual entry count > declared entry_count, ledger has been tampered with.
        - Break: Attacker appends forged entries after declared head.
        - Witness: Refusal with message 'Log extension detected beyond declared head'.
        - Mutation: Checking actual_count == declared_count with '<=' allows forged appending.
        """
        flags = PontryaginKillFlags(flag_pi=False, flag_u1=False, flag_zn=False, flag_alpha=False)
        p1 = QuarantinedShadowPacket(
            target_theorem="T1",
            assertion_flags=flags,
            fence_audit=HostFenceAudit.evaluate(flags),
            shadow_type="S",
            evidence_bound="B",
            raw_transcript=(),
        )
        ledger = EpistemicQuarantineLedger(
            ledger_id="LEDGER-EXT-01",
            stage_level=StageLevel(10),
            entries=(p1,),
        )
        serialized = serialize_ledger_to_jsonl(ledger)
        lines = serialized.strip().split("\n")

        # Duplicate entry line (actual = 2, declared = 1)
        extended = lines[0] + "\n" + lines[1] + "\n" + lines[1] + "\n"

        res = deserialize_ledger_from_jsonl(extended)
        assert res.is_refusal
        assert "Log extension detected" in res.refusal.message

    def test_b28_stage_floor_scope_boundary_enforcement(self) -> None:
        """Verify Permanent Quarantine Law enforces stage floor >= 10 (FW-SCOPE).

        - Invariant: Epistemic quarantine ledger is prohibited below Stage 10.
        - Break: Stage 0-9 ledgers admitted.
        - Witness: ScopeBoundaryViolationError with 'Permanent Quarantine Law violation'.
        - Mutation: Allowing stage_int < 10 violates scope boundary contract.
        """
        header_bad_stage = json.dumps({
            "record_type": "HEADER",
            "ledger_id": "L-BAD",
            "schema_version": "v1",
            "stage_level": 9,  # Below Stage 10 floor
            "entry_count": 0,
            "head_digest": "genesis",
        }) + "\n"

        res = deserialize_ledger_from_jsonl(header_bad_stage)
        assert res.is_refusal
        assert isinstance(res.refusal, ScopeBoundaryViolationError)
        assert "stage floor must be >= 10" in res.refusal.message


class TestAllostericCooperativityBoundariesTier2:
    """Tier 2 Boundary Tests: Allosteric Quorum & Hill Equation Limits (Prompt 19)."""

    def test_b29_zero_and_negative_signal_stability(self) -> None:
        """Verify the Hill response is exactly zero at zero and refuses negative signals.

        - Invariant: A zero signal yields exactly Fraction(0); a negative signal is refused
          with SIGNAL_OUT_OF_RANGE rather than silently read as zero.
        - Break: Zero division, or a negative signal quietly contributing (or being ignored).
        - Witness: calculate_cooperativity(0) == 0; a sensor reporting -1 is refused;
          two sensors reporting 0 are inactive with hill_value 0.
        - Mutation: Clamping negatives to zero would let a malformed sensor pass unnoticed.
        """
        params = HillParameters(hill_coefficient=2, half_maximal_constant=Fraction(2))
        assert params.calculate_cooperativity(0) == Fraction(0)
        with pytest.raises(AllosteryRefusal) as negative:
            params.calculate_cooperativity(-5)
        assert negative.value.code == "SIGNAL_OUT_OF_RANGE"

        gate = AllostericConsensusGate(parameters=params, activation_threshold=Fraction(1, 2))
        with pytest.raises(AllosteryRefusal) as refused:
            gate.evaluate_quorum({"sensor_a": -1, "sensor_b": 0})
        assert refused.value.code == "SIGNAL_OUT_OF_RANGE"

        silent = gate.evaluate_quorum({"sensor_a": 0, "sensor_b": 0})
        assert silent.is_activated is False
        assert silent.hill_value == Fraction(0)
        assert silent.positive_sensors == 0

    def test_b30_asymptotic_upper_bound_cooperativity(self) -> None:
        """Verify the exact Hill response approaches 1 but stays strictly below it.

        - Invariant: For every exact S >= 0, H(S) = S**n / (K**n + S**n) < 1.
        - Break: A large signal overflows or yields H(S) >= 1.
        - Witness: calculate_cooperativity(10**6) is the exact Fraction 10**18 / (1 + 10**18).
        - Mutation: An inverted denominator term yields an unbounded response.
        """
        params = HillParameters(hill_coefficient=3, half_maximal_constant=Fraction(1))
        huge_response = params.calculate_cooperativity(1_000_000)
        assert type(huge_response) is Fraction
        assert huge_response == Fraction(10**18, 10**18 + 1)
        assert Fraction(9999, 10000) <= huge_response < 1
        with pytest.raises(AllosteryRefusal) as inexact:
            params.calculate_cooperativity(1_000_000.0)
        assert inexact.value.code == "NOT_EXACT"
