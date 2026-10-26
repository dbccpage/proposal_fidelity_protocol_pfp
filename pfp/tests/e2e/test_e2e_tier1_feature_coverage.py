"""Tier 1 E2E Test Suite: Feature Coverage (Equivalence Classes).

AuthorityEffect: None.
Reference: TEST_INFRA.md Tier 1 Specification.
Soviet Lev Landau Falsification Methodology:
Every test explicitly documents Invariant, Break, Witness, and Mutation.
Claim Hygiene: Uses bounded, defensible phrasing; zero forbidden hype words.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
from typing import Any

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
)
from omega_engine_pfp.domain.glyph_calculus import Carrier, CarrierMember, Finding

# Tower Grammar, Parser, and Wire
from omega_engine_pfp.domain.tower.parser import (
    parse_packet,
    serialize_packet,
    validate_packet_semantics,
    validate_level3_simplex,
    validate_rational,
    validate_dual_cert,
    validate_level7_orbit,
    SimplexValidationError,
    RationalValidationError,
    DualWitnessError,
    LexicalError,
    SyntaxError,
    ArityError,
    Atom,
    App,
    Diff,
    GAMMA_38,
    SIGMA_36,
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
    application,
)

# Demos & Descent
from omega_engine_pfp.domain.demos import (
    exact_functional,
    strict_descent,
    refuse_model_functionals,
    DemoRefusal,
    Scenario,
)

# Epistemic Immune System & Pharmacy
from omega_engine_epistemic_immune_system.infrastructure.mssn_pharmacy import (
    FailureClass,
    Disposition,
    DetectionContext,
    DetectorReport,
    HostReplayReceipt,
    detect,
)
from omega_engine_epistemic_immune_system.domain.allostery import (
    AllostericConsensusGate,
    AllostericDecision,
    HillParameters,
)
from omega_engine_epistemic_immune_system.domain.value_objects import AllosteryRefusal
from omega_engine_epistemic_immune_system.domain.danger_gate import TwoSignalDangerGate
from omega_engine_epistemic_immune_system.domain.thymus import (
    ThymusGate,
    ThymusSelectionResult,
)
from omega_engine_epistemic_immune_system.domain.clonal_selection import (
    ClonalSelectionEngine,
)
from omega_engine_epistemic_immune_system.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
    DetectorRule,
    HillParameters,
)

# Cemetery & Quarantine Persistence
from omega_engine_pfp.domain.mssn_research.grammar.entities import (
    EpistemicQuarantineLedger,
)
from omega_engine_pfp.infrastructure.adapters.mssn_research.contracts.grammar.ledger_codec import (
    serialize_ledger_to_jsonl,
    deserialize_ledger_from_jsonl,
    packet_to_dict,
)
from omega_engine_pfp.infrastructure.adapters.mssn_research.contracts.grammar.ledger_repository import (
    EpistemicQuarantineRepository,
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
    RefusalCode,
)

# Boundary Functional & Problem Runner
from omega_engine_pfp.use_cases.problem_runner import ProblemRunnerUseCase
from omega_engine_pfp.functional_boundary import (
    RustFunctionalRequired,
    require_rust_functional,
)


class TestEpistemicImmuneSystemTier1:
    """Tier 1 Feature Coverage: Epistemic Immune System (P01-P04, P19, P21)."""

    def test_p01_failure_classes_twelve_taxonomy_and_dispositions(self) -> None:
        """Verify all 12 mechanical failure classes exist and have strictly typed dispositions.

        - Invariant: Pharmacy specifies exactly 12 failure classes with defined severity ranking.
        - Break: An unregistered failure class code is added or disposition mapping returns None.
        - Witness: FailureClass enum contains 12 members; all default_disposition() return Disposition.
        - Mutation: Removing an enum member or returning arbitrary string causes immediate failure.
        """
        assert len(FailureClass) == 12

        expected_refuse = {
            FailureClass.SELF_CERTIFICATION,
            FailureClass.FAKE_RECEIPT,
            FailureClass.PERSONA_AUTHORITY_LEAK,
        }
        expected_hold = {
            FailureClass.SCHEMA_SEMANTIC_LAUNDERING,
            FailureClass.PRIVATE_COT_DEPENDENCY,
        }

        for fc in FailureClass:
            disp = fc.default_disposition()
            assert isinstance(disp, Disposition)
            if fc in expected_refuse:
                assert disp == Disposition.REFUSE
            elif fc in expected_hold:
                assert disp == Disposition.HOLD
            else:
                assert disp == Disposition.FINDING

        assert Disposition.FINDING.severity_rank() < Disposition.HOLD.severity_rank()
        assert Disposition.HOLD.severity_rank() < Disposition.REFUSE.severity_rank()

    def test_p01_failure_classes_detectors_positive_and_negative(self) -> None:
        """Verify positive detection triggers and negative control passes for failure classes.

        - Invariant: Detector emits Finding on matching defective pattern; returns None on clean input.
        - Break: False positives on clean inputs or false negatives on exact trigger substrings.
        - Witness: Detector returns finding with matching FailureClass code.
        - Mutation: Inverting detector predicate causes negative control failure.
        """
        # Clean base context with verified replay receipt
        clean_ctx = DetectionContext(
            host_replay_receipt=HostReplayReceipt(
                receipt_id="REC-01",
                host_signer="TEST_HOST",
                target_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
                replay_passed=True,
            ),
            semantic_replay_passed=True,
        )

        # Positive trigger: self-certification and fake receipt
        pos_fake = {"receipt": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
        rep_fake = detect(pos_fake, clean_ctx)
        classes_found = {f.failure_class for f in rep_fake.findings}
        assert FailureClass.SELF_CERTIFICATION in classes_found
        assert FailureClass.FAKE_RECEIPT in classes_found

        # Positive trigger: persona authority leak
        pos_leak = {"persona_statement": "I act with unrestricted authority as sovereign arbiter"}
        rep_leak = detect(pos_leak, clean_ctx)
        assert any(f.failure_class == FailureClass.PERSONA_AUTHORITY_LEAK for f in rep_leak.findings)

        # Positive trigger: private chain-of-thought leak
        pos_cot = {"reasoning": "<think> internal unlogged tokens </think>"}
        rep_cot = detect(pos_cot, clean_ctx)
        assert any(f.failure_class == FailureClass.PRIVATE_COT_DEPENDENCY for f in rep_cot.findings)

        # Negative control: neutral descriptive document
        neg_clean = {"method": "compute_reduced_echelon_form", "field": "F2"}
        rep_clean = detect(neg_clean, clean_ctx)
        assert rep_clean.is_clean()

    def test_p02_thymus_negative_selection_self_tolerance(self) -> None:
        """Verify Epistemic Thymus negative selection filter rejects cross-reactive candidate rules.

        - Invariant: Candidate rules matching clean self-panel fixtures are eliminated (apoptosis).
        - Break: A detector rule reacting to valid benign code is erroneously admitted.
        - Witness: ThymusSelectionResult has is_admitted=False with first_violating_sample.
        - Mutation: Skipping self-panel iteration causes cross-reactive rules to be admitted.
        """
        clean_self_panel = (
            "def compute_coboundary(chain):\n    return [chain[i] for i in range(len(chain))]\n",
            "class SimplicialComplex:\n    def __init__(self, vertices):\n        self.vertices = vertices\n",
        )
        thymus = ThymusGate(clean_self_panel)

        # Cross-reactive rule that triggers on standard python def
        cross_reactive_rule = DetectorRule(
            rule_id="RULE-BAD-01",
            target_epitope="compute_coboundary",
            match_pattern=r"def compute_coboundary",
            generation=1,
            affinity_score=1.0,
            half_life_runs=10,
        )
        res_cross = thymus.evaluate_rule(cross_reactive_rule)
        assert not res_cross.is_admitted
        assert res_cross.first_violating_sample is not None

        # Clean non-cross-reactive rule targeting genuine defect token
        clean_rule = DetectorRule(
            rule_id="RULE-GOOD-01",
            target_epitope="HALT_UNAUTHORIZED",
            match_pattern=r"HALT_UNAUTHORIZED_EXPLICIT_DEFECT",
            generation=1,
            affinity_score=1.0,
            half_life_runs=10,
        )
        res_clean = thymus.evaluate_rule(clean_rule)
        assert res_clean.is_admitted
        assert res_clean.first_violating_sample is None

    def test_p03_two_signal_danger_gate_activation(self) -> None:
        """Verify Two-Signal Activation: Signal 1 (AST match) + Signal 2 (Danger) required for quarantine.

        - Invariant: Quarantine decision requires both Signal 1 antigen match and Signal 2 tissue danger.
        - Break: Signal 1 alone triggers quarantine (autoimmune attack) or Signal 2 alone triggers action.
        - Witness: DangerEvaluationResult.decision is QUARANTINED only when both signals are present with CRITICAL severity.
        - Mutation: Ignoring Signal 2 sensor triggers false positive quarantine on benign matches.
        """
        match = Signal1Match(
            epitope_name="PROSE_AUTHORITY_ASSERTION",
            pattern_matched="verified",
            confidence=1.0,
            offset=10,
        )
        danger = Signal2Danger(
            danger_type="AUTHORITY_DAMAGE",
            severity=DangerSeverity.CRITICAL,
            defect_count=1,
            evidence_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
        )

        # Signal 1 present + Signal 2 present -> QUARANTINED
        dec_both = TwoSignalDangerGate.evaluate((match,), danger)
        assert dec_both.decision == DangerDecision.QUARANTINED
        assert dec_both.signal1_count == 1
        assert dec_both.signal2_severity == DangerSeverity.CRITICAL

        # Signal 1 present + Signal 2 absent (None) -> DIAGNOSTIC_ONLY
        dec_sig1_only = TwoSignalDangerGate.evaluate((match,), None)
        assert dec_sig1_only.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert not dec_sig1_only.is_suppressed

        # Signal 1 absent + Signal 2 absent -> TOLERATED
        dec_none = TwoSignalDangerGate.evaluate((), None)
        assert dec_none.decision == DangerDecision.TOLERATED

    def test_p04_tregs_clonal_selection_and_half_life_decay(self) -> None:
        """Verify Clonal Selection: stimulation increases affinity; idle turns cause exponential decay.

        - Invariant: Stimulated antibodies undergo affinity maturation; unobserved rules decay towards zero.
        - Break: Inactive rules remain immortal or stimulated rules decay.
        - Witness: stimulated.affinity_score > original.affinity_score, decayed.runs_idle > original.runs_idle.
        - Mutation: Negating decay delta causes uncontrolled antibody proliferation.
        """
        rule = DetectorRule(
            rule_id="RULE-CLONE-01",
            target_epitope="STOLEN_RECEIPT",
            match_pattern=r"fake_digest",
            generation=1,
            affinity_score=0.5,
            half_life_runs=5,
        )

        stimulated = ClonalSelectionEngine.stimulate(rule, affinity_boost=0.2)
        assert stimulated.affinity_score > rule.affinity_score

        decayed = ClonalSelectionEngine.apply_decay(rule)
        assert decayed.runs_idle == rule.runs_idle + 1

        # Expired rule deactivates after half_life_runs idle turns
        expired_rule = DetectorRule(
            rule_id="RULE-DEAD-01",
            target_epitope="INERT",
            match_pattern=r"inert",
            generation=1,
            affinity_score=0.1,
            half_life_runs=2,
            runs_idle=1,
        )
        expired_decayed = ClonalSelectionEngine.apply_decay(expired_rule)
        assert not expired_decayed.is_active

        active = ClonalSelectionEngine.filter_active_repertoire((stimulated, expired_decayed))
        assert stimulated in active
        assert expired_decayed not in active

    def test_p19_allosteric_quorum_cooperativity_hill_gate(self) -> None:
        """Verify the Allosteric Quorum Gate needs several sensors under the per-sensor cap.

        - Invariant: with every signal at most the cap 1, H(S) >= 1/2 needs S >= K = 2,
          so no single sensor can activate the gate (quorum_size == 2).
        - Break: A single anomaly, however loud, triggers activation.
        - Witness: one sensor at the cap stays inactive; three sensors summing to 29/10 activate.
        - Mutation: removing the per-sensor cap lets one sensor reporting 3 activate the gate.
        """
        params = HillParameters(hill_coefficient=3, half_maximal_constant=Fraction(2))
        gate = AllostericConsensusGate(parameters=params, activation_threshold=Fraction(1, 2))
        assert gate.quorum_size == 2

        # Single weak sensor signal, and a single sensor at its cap.
        decision_weak = gate.evaluate_quorum({"sensor_a": Fraction(1, 2)})
        assert decision_weak.is_activated is False
        assert decision_weak.hill_value < Fraction(1, 2)
        assert gate.evaluate_quorum({"sensor_a": 1}).is_activated is False

        # Cooperative multi-sensor binding: 1 + 1 + 9/10 = 29/10 >= K = 2.
        decision_strong = gate.evaluate_quorum(
            {"sensor_a": 1, "sensor_b": 1, "sensor_c": Fraction(9, 10)}
        )
        assert decision_strong.is_activated is True
        assert decision_strong.aggregate_signal == Fraction(29, 10)
        assert decision_strong.hill_value > Fraction(1, 2)
        assert decision_strong.positive_sensors == 3

        # A loud lone sensor is refused, and a float is refused, not converted.
        with pytest.raises(AllosteryRefusal) as loud:
            gate.evaluate_quorum({"sensor_a": 3})
        assert loud.value.code == "SIGNAL_ABOVE_SENSOR_CAP"
        with pytest.raises(AllosteryRefusal) as inexact:
            gate.evaluate_quorum({"sensor_a": 0.5})
        assert inexact.value.code == "NOT_EXACT"
        # One sensor cannot count twice, whatever the letter case of its id.
        with pytest.raises(AllosteryRefusal) as twice:
            gate.evaluate_quorum({"sensor_a": 1, "SENSOR_A": 1})
        assert twice.value.code == "DUPLICATE_SENSOR"


class TestDiscreteManifoldAndExactArithmeticTier1:
    """Tier 1 Feature Coverage: Exact Rational, Codecs, Pins, Decoding (P44-P48, P24)."""

    def test_p47_exact_rational_q_zero_float_law(self) -> None:
        """Verify Q refuses floating-point inputs and non-canonical representations under Zero-Float Law.

        - Invariant: Discrete state arithmetic admits only exact integers and reduced fractions; floats raise ExactError.
        - Break: A floating point value is silently converted to float approximation.
        - Witness: Q(1.5) or parse_q(1.5) raises ExactError("RR-FLOAT").
        - Mutation: Adding float branch in _int converts float and drops ExactError.
        """
        # Exact valid initialization
        q1 = Q(3, 4)
        assert q1.num == 3 and q1.den == 4
        assert str(q1) == "3/4"

        # Refusal of float
        with pytest.raises(ExactError) as exc_info:
            Q(1.5)  # type: ignore[arg-type]
        assert exc_info.value.code == "RR-FLOAT"

        with pytest.raises(ExactError) as exc_info:
            Q(1, 2.5)  # type: ignore[arg-type]
        assert exc_info.value.code == "RR-FLOAT"

        # Refusal of zero denominator
        with pytest.raises(ExactError) as exc_info:
            Q.of(1, 0)
        assert exc_info.value.code == "RR-DENOMINATOR"

        # Exact-Type Equality
        assert q1 != (3, 4)
        assert (q1 == 0.75) is False

    def test_p47_exact_rational_q_operations_and_canonical_reduction(self) -> None:
        """Verify field operations on Q preserve canonical reduction and exactness.

        - Invariant: (a/b) + (c/d) returns coprime reduced fraction via cross-multiplication.
        - Break: Operations produce unreduced fraction or numeric overflow.
        - Witness: Q(1, 2) + Q(1, 2) == Q(1, 1); Q(1, 3) * Q(3, 1) == Q(1, 1).
        - Mutation: Omitting gcd reduction creates non-canonical Q instances.
        """
        half = Q(1, 2)
        third = Q(1, 3)

        added = half + third
        assert added == Q(5, 6)

        subtracted = half - third
        assert subtracted == Q(1, 6)

        multiplied = half * third
        assert multiplied == Q(1, 6)

        divided = half / third
        assert divided == Q(3, 2)

        # Parse string canonical representation
        assert parse_q("5/6") == added
        with pytest.raises(ExactError):
            parse_q("0.83333")  # non-canonical float string refused

    def test_p44_packet_codec_sealing_and_verification(self) -> None:
        """Verify PacketCodec seals payloads with RFC 8785 canonical JSON and SHA-256 digests.

        - Invariant: Byte-for-byte deterministic seal; payload tampering causes verification failure.
        - Break: Unsorted keys or non-canonical whitespaces alter hash; tampered payload passes.
        - Witness: PacketCodec.verify(sealed) == (True, sha, "OK").
        - Mutation: Inverting hash equality check returns True on tampered payload.
        """
        payload = {
            "turn_index": 1,
            "carrier": "witten-five-slot",
            "delta": {"v1": "1/2", "v2": "0/1"},
        }
        sealed = PacketCodec.seal(payload, packet_family="retraction_turn")

        assert sealed["packet_family"] == "retraction_turn"
        assert sealed["authority_effect"] == "None"
        assert "envelope_sha256" in sealed
        assert "payload_sha256" in sealed

        # Verification of unmodified envelope
        is_valid, computed_sha, msg = PacketCodec.verify(sealed)
        assert is_valid
        assert computed_sha == sealed["payload_sha256"]
        assert msg == "OK"

        # Tampering detection: modify payload content
        tampered = dict(sealed)
        tampered["payload"] = dict(tampered["payload"])
        tampered["payload"]["turn_index"] = 999

        is_valid_tampered, _, msg_tampered = PacketCodec.verify(tampered)
        assert not is_valid_tampered
        assert "mismatch" in msg_tampered.lower()

    def test_p44_packet_codec_authority_effect_none_enforcement(self) -> None:
        """Verify PacketCodec rejects envelopes with non-'None' AuthorityEffect.

        - Invariant: A symbol game envelope must carry authority_effect == "None".
        - Break: Envelope asserting executive promotion authority is admitted.
        - Witness: PacketCodec.verify returns is_valid=False with 'Prohibited authority effect'.
        - Mutation: Allowing authority_effect='Promote' violates epistemic firewall.
        """
        payload = {"data": "test_payload"}
        sealed = PacketCodec.seal(payload, packet_family="test_packet")

        tampered_auth = dict(sealed)
        tampered_auth["authority_effect"] = "FullExecutiveAuthority"

        is_valid, _, msg = PacketCodec.verify(tampered_auth)
        assert not is_valid
        assert "prohibited authority effect" in msg.lower()

    def test_p45_presentation_pins_lookup_and_cycle_resolution(self) -> None:
        """Verify PresentationPins resolves presentation names from host pin set without conflating rules.

        - Invariant: Host resolves declared pin name; unregistered name yields None (UNCHECKABLE).
        - Break: Host guesses presentation rules for unpinned name or crashes.
        - Witness: pins.resolve("c5") returns PinnedPresentation; pins.resolve("c99") is None.
        - Mutation: Returning a default fallback presentation for unknown names guesses producer intent.
        """
        raw_pins = [
            {
                "name": "c3",
                "presentation": {
                    "signature": ["a", "b", "c"],
                    "rules": [
                        {"name": "r1", "lhs": "a", "rhs": "b"},
                        {"name": "r2", "lhs": "b", "rhs": "c"},
                        {"name": "r3", "lhs": "c", "rhs": "a"},
                    ],
                },
            }
        ]
        pins = PresentationPins.from_wire(raw_pins)
        assert pins.names == ("c3",)

        # Resolution of pinned presentation
        c3 = pins.resolve("c3")
        assert c3 is not None
        assert c3.period == 3
        assert c3.apply_successor("a", 1) == "b"
        assert c3.apply_successor("a", 2) == "c"
        assert c3.apply_successor("a", 3) == "a"
        assert c3.apply_successor("a", 300) == "a"

        # Resolution of unpinned presentation yields None (uncheckable)
        assert pins.resolve("unknown_pin") is None

    def test_p46_carrier_decoding_receipt_measure_and_capabilities(self) -> None:
        """Verify DecodingReceipt measures emission against carrier and enforces provider capabilities.

        - Invariant: Applied constraint cannot exceed declared provider capability; defaults down.
        - Break: Caller asserts GRAMMAR constraint against an UNCONSTRAINED provider (e.g. anthropic).
        - Witness: Attempt to claim GRAMMAR on anthropic raises ValueError.
        - Mutation: Clamping upward or ignoring provider capability misrepresents receipt evidence.
        """
        assert provider_capability("local") == ConstraintMode.GRAMMAR
        assert provider_capability("openai") == ConstraintMode.LOGIT_BIAS
        assert provider_capability("anthropic") == ConstraintMode.UNCONSTRAINED

        carrier = Carrier((CarrierMember("a", "U+0061"), CarrierMember("b", "U+0062")))

        # Valid measurement against local with grammar
        rec_local = DecodingReceipt.measure(
            provider="local",
            text="aba",
            carrier=carrier,
            applied=ConstraintMode.GRAMMAR,
        )
        assert rec_local.emission_within_carrier
        assert rec_local.mode.is_exact

        # Refusal: claiming GRAMMAR on provider that only supports LOGIT_BIAS
        with pytest.raises(ValueError, match="a receipt may not assert a constraint"):
            DecodingReceipt.measure(
                provider="openai",
                text="aba",
                carrier=carrier,
                applied=ConstraintMode.GRAMMAR,
            )

    def test_p48_wire_gamma38_recursive_descent_and_roundtrip(self) -> None:
        """Verify Gamma38 wire recursive-descent parser and canonical serializer round-trip.

        - Invariant: serialize_packet(parse_packet(s)) == s for all valid wire strings.
        - Break: Grammar parser mangles delimiters or drops application nodes.
        - Witness: Wire string parses to AST and serializes back identically.
        - Mutation: Altering delimiter emit logic breaks round-trip bijection.
        """
        samples = [
            "<>",
            "<abc>",
            "op<<><a><b>>",
            "op<<101><10><0><1><10>>",
        ]
        for sample in samples:
            parsed = parse_packet(sample)
            serialized = serialize_packet(parsed)
            assert serialized == sample

        # Non-Gamma38 character raises LexicalError
        with pytest.raises(LexicalError):
            parse_packet("<bad_char_!>")

    def test_p48_wire_compact_postfix_tagged_json_dag_codecs(self) -> None:
        """Verify wire external representation codecs (compact, postfix, tagged JSON, DAG).

        - Invariant: All four external codecs lossless round-trip parse and emit.
        - Break: External dialect parser drops terms or fails to reconstruct AST.
        - Witness: parse_*(emit_*(ast)) == ast for all dialects.
        - Mutation: Changing token delimiter in postfix breaks parsing.
        """
        ast = parse_wire("op<<1><a>>")

        # Compact profile
        comp = emit_compact(ast)
        assert parse_compact(comp) == ast

        # Postfix profile
        post = emit_postfix(ast)
        assert parse_postfix(post) == ast

        # Tagged JSON profile
        tj = emit_tagged_json(ast)
        assert parse_tagged_json(tj) == ast

        # Hash-consed DAG profile
        dag = emit_dag(ast)
        assert parse_dag(dag) == ast


class TestTopologicalAndGrammarValidationTier1:
    """Tier 1 Feature Coverage: Simplicial Complexes, Regge Deficits, Dual Witness (P23, P32, P34)."""

    def test_p23_simplex_dimension_distinctness_and_ordering(self) -> None:
        """Verify Level 3 abstract simplex validator enforces dimension, distinctness, and ascending order.

        - Invariant: Simplex <101> has dim+1 distinct vertices in strictly ascending binary integer order.
        - Break: Duplicate vertex, incorrect vertex count, or descending order passes validation.
        - Witness: SimplexValidationError raised with specific cause.
        - Mutation: Omitting distinctness check admits degenerate self-collapsing simplices.
        """
        # Valid 2-simplex: dimension 2, 3 vertices: 0, 1, 10 (binary for 0, 1, 2)
        valid_s2 = parse_packet("op<<101><10><0><1><10>>")
        assert isinstance(valid_s2, App)
        validate_level3_simplex(valid_s2)

        # Dimension mismatch: declared dim 2 (needs 3 vertices) but provided 2
        bad_dim = parse_packet("op<<101><10><0><1>>")
        assert isinstance(bad_dim, App)
        with pytest.raises(SimplexValidationError, match="Dimension mismatch"):
            validate_level3_simplex(bad_dim)

        # Duplicate vertex
        bad_dup = parse_packet("op<<101><10><0><1><1>>")
        assert isinstance(bad_dup, App)
        with pytest.raises(SimplexValidationError, match="distinctness violation"):
            validate_level3_simplex(bad_dup)

        # Non-ascending ordering: <10> before <1>
        bad_order = parse_packet("op<<101><10><0><10><1>>")
        assert isinstance(bad_order, App)
        with pytest.raises(SimplexValidationError, match="Canonical ordering violation"):
            validate_level3_simplex(bad_order)

    def test_p32_level5_regge_curvature_deficit_accounting(self) -> None:
        """Verify Level 5 Regge deficit receipt enforces exact integer angle sum: full == sum + deficit.

        - Invariant: 2*pi angle deficit formula holds identically in exact binary integer units.
        - Break: Deficit angle fails to balance the total dihedral angle sum.
        - Witness: ValidationError raised with 'Deficit arithmetic violation'.
        - Mutation: Altering arithmetic equality allows fictitious zero-curvature claims.
        """
        from omega_engine_pfp.domain.tower.parser import validate_level5_regge

        # full = 8, sum = 6, deficit = 2 (in binary: <1000>, <110>, <10>)
        valid_deficit = parse_packet("op<<1010><10><1><1000><110><10>>")
        assert isinstance(valid_deficit, App)
        validate_level5_regge(valid_deficit)

        # Broken deficit: full = 8, sum = 5, deficit = 2 (sum + deficit = 7 != 8)
        broken_deficit = parse_packet("op<<1010><10><1><1000><101><10>>")
        assert isinstance(broken_deficit, App)
        with pytest.raises(ValueError, match="Deficit arithmetic violation"):
            validate_level5_regge(broken_deficit)

    def test_p34_level8_dual_witness_zero_gap_and_circulation(self) -> None:
        """Verify Level 8 Dual Certificate asserts exact zero duality gap and circulation conservation.

        - Invariant: primal_mass == dual_mass and net vertex flow sum equals zero at every vertex.
        - Break: Non-zero duality gap or boundary circulation leakage is accepted.
        - Witness: DualWitnessError raised with specific violation.
        - Mutation: Accepting primal_mass != dual_mass breaks LP duality certification.
        """
        # Valid zero duality gap: primal = 1/1, dual = 1/1, balanced cycle: 1->2 (1), 2->1 (1)
        valid_cert = parse_packet(
            "op<<10001>"
            "op<<10010><0><1><1>>"  # primal mass 1/1
            "op<<10010><0><1><1>>"  # dual mass 1/1
            "op<<11>"               # flow vector container
            "op<<10011><1><10>op<<10010><0><1><1>>>"   # 1 -> 2 flow 1
            "op<<10011><10><1>op<<10010><0><1><1>>>"   # 2 -> 1 flow 1
            ">>"
        )
        assert isinstance(valid_cert, App)
        validate_dual_cert(valid_cert)

        # Non-zero duality gap: primal 1/1 != dual 0/1
        broken_gap = parse_packet(
            "op<<10001>"
            "op<<10010><0><1><1>>"  # primal mass 1/1
            "op<<10010><0><0><1>>"  # dual mass 0/1
            "op<<11>>"
            ">"
        )
        assert isinstance(broken_gap, App)
        with pytest.raises(DualWitnessError, match="non-zero duality gap"):
            validate_dual_cert(broken_gap)


class TestZeroDataLossAndPersistenceTier1:
    """Tier 1 Feature Coverage: CemeterySink, Quarantine Ledger, Tail Truncation (P10, P35)."""

    def test_p10_epistemic_quarantine_ledger_hash_chain(self) -> None:
        """Verify EpistemicQuarantineLedger maintains cryptographically verifiable SHA-256 hash chain.

        - Invariant: Every entry binds the digest of its predecessor; line 0 binds total count.
        - Break: Bit corruption or out-of-order records go undetected.
        - Witness: deserialize_ledger_from_jsonl verifies 100% of chain digests.
        - Mutation: Tampering with a single byte in payload causes LedgerIntegrityError.
        """
        flags = PontryaginKillFlags(flag_pi=True, flag_u1=False, flag_zn=False, flag_alpha=False)
        audit = HostFenceAudit.evaluate(flags)
        packet = QuarantinedShadowPacket(
            target_theorem="THM-001",
            assertion_flags=flags,
            fence_audit=audit,
            shadow_type="SHADOW_PROSE",
            evidence_bound="EXACT_0",
            raw_transcript=("prompt_1", "reply_1"),
        )
        ledger = EpistemicQuarantineLedger(
            ledger_id="LEDGER-E2E-01",
            stage_level=StageLevel(10),
            entries=(packet,),
        )
        serialized = serialize_ledger_to_jsonl(ledger)
        assert "HEADER" in serialized
        assert "ENTRY" in serialized

        # Roundtrip parse
        res = deserialize_ledger_from_jsonl(serialized)
        assert res.is_ok
        unpacked = res.unwrap()
        assert unpacked.ledger_id == "LEDGER-E2E-01"
        assert len(unpacked.entries) == 1

    def test_p10_epistemic_quarantine_explicit_head_and_truncation_detection(self) -> None:
        """Verify explicit head record prevents stealth tail-truncation attacks across sessions.

        - Invariant: Ledger header entry_count must match actual parsed entry record count exactly.
        - Break: Attacker deletes the last entry; header still declared old count.
        - Witness: deserialize_ledger_from_jsonl returns Refusal(LedgerTruncationError).
        - Mutation: Skipping entry_count comparison against actual count permits silent truncation.
        """
        f1 = PontryaginKillFlags(flag_pi=True, flag_u1=False, flag_zn=False, flag_alpha=False)
        p1 = QuarantinedShadowPacket(
            target_theorem="THM-001",
            assertion_flags=f1,
            fence_audit=HostFenceAudit.evaluate(f1),
            shadow_type="SHADOW_1",
            evidence_bound="B-1",
            raw_transcript=(),
        )
        f2 = PontryaginKillFlags(flag_pi=False, flag_u1=True, flag_zn=False, flag_alpha=False)
        p2 = QuarantinedShadowPacket(
            target_theorem="THM-002",
            assertion_flags=f2,
            fence_audit=HostFenceAudit.evaluate(f2),
            shadow_type="SHADOW_2",
            evidence_bound="B-2",
            raw_transcript=(),
        )
        ledger = EpistemicQuarantineLedger(
            ledger_id="LEDGER-TRUNC-01",
            stage_level=StageLevel(10),
            entries=(p1, p2),
        )
        serialized = serialize_ledger_to_jsonl(ledger)
        lines = serialized.strip().split("\n")
        assert len(lines) == 3  # Header + 2 entries

        # Simulate adversarial tail truncation: delete line 2 (entry 1) while header says count=2
        truncated_jsonl = lines[0] + "\n" + lines[1] + "\n"

        res = deserialize_ledger_from_jsonl(truncated_jsonl)
        assert res.is_refusal
        err = res.refusal
        assert isinstance(err, LedgerTruncationError)
        assert "Tail truncation detected" in err.message


class TestGovernanceAndArchitecturalBoundariesTier1:
    """Tier 1 Feature Coverage: Schema vs Kill Map, Regime Manifest, FFI Isolation (P49-P53)."""

    def test_p49_stage_schema_validation_orthogonality_to_kill_map(self) -> None:
        """Verify stage schema validation is orthogonal to the kill-condition refusal map (Prompt 49).

        - Invariant: A schema-valid stage 0 packet envelope can still trigger a named kill refusal.
        - Break: Schema validity is erroneously treated as exemption from the kill map.
        - Witness: Packet envelope valid under stage 0 schema produces kill refusal on kill condition.
        - Mutation: Returning 'no kill' whenever schema validator passes causes security bypass.
        """
        stage0_path = Path("omega_engine_pfp/packet_schemas/packet_envelope_v2.schema.json")
        refusal_map_path = Path("omega_engine_pfp/packet_schemas/kill_condition_refusal_map_v1.json")

        assert stage0_path.exists()
        assert refusal_map_path.exists()

        refusal_map = json.loads(refusal_map_path.read_text(encoding="utf-8"))
        mapping = refusal_map["mapping"]

        # Verify kill condition 'SYNTAX_VALID_IMPLIES_SEMANTIC_TRUE' is explicitly mapped
        assert "SYNTAX_VALID_IMPLIES_SEMANTIC_TRUE" in mapping
        entry = mapping["SYNTAX_VALID_IMPLIES_SEMANTIC_TRUE"]
        assert entry["refusal_code"] == "CLAIM_EVALUATOR_RECEIPT_REQUIRED"

        # Construct a schema-valid envelope that nonetheless commits this kill trigger
        payload = {
            "evidence": "syntax_ok",
            "kill_triggers": ["SYNTAX_VALID_IMPLIES_SEMANTIC_TRUE"],
        }
        envelope = PacketCodec.seal(payload, packet_family="retraction_turn")

        # Envelope is cryptographically valid and conforms to envelope structure
        is_valid, _, msg = PacketCodec.verify(envelope)
        assert is_valid, msg

        # But in domain scoring, the kill trigger must be caught and named
        from omega_engine_pfp.use_cases.scoring import CandidateProposal, score_discrete_proposal
        proposal = CandidateProposal(
            proposal_id="PROP-01",
            repaired_obstruction_ids=(),
            cochain_delta=(),
            structural_cost=1,
            authority_effect="None",
            kill_triggers=("SYNTAX_VALID_IMPLIES_SEMANTIC_TRUE",),
        )
        score_res = score_discrete_proposal(["OBS-01"], proposal)
        assert not score_res.is_legal
        assert "CLAIM_EVALUATOR_RECEIPT_REQUIRED" in score_res.refusal_reason

    def test_p50_regime_manifest_byte_level_replay_matches_manifest(self) -> None:
        """Verify regime manifest SHA-256 digests match actual regime file bytes (Prompt 50).

        - Invariant: Every filename declared in regime_manifest.json matches actual disk file SHA-256.
        - Break: Stale or mismatched checksums between manifest and disk files.
        - Witness: compute_sha256(file.read_bytes()) == entry["sha256"].
        - Mutation: Comparing filename instead of byte hash misses content tampering.
        """
        regimes_dir = Path("omega_engine_pfp/regimes")
        manifest_path = regimes_dir / "regime_manifest.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for regime_key, record in manifest.items():
            filename = record["filename"]
            expected_sha = record["sha256"]
            expected_bytes = record["byte_count"]

            regime_file = regimes_dir / filename
            assert regime_file.exists(), f"Regime file {filename} missing"

            content = regime_file.read_bytes()
            assert len(content) == expected_bytes, f"Byte count mismatch for {filename}"
            actual_sha = hashlib.sha256(content).hexdigest()
            assert actual_sha == expected_sha, f"SHA-256 mismatch for {filename}"

    def test_p51_ffi_seam_isolation_no_subprocess_or_direct_unpack(self) -> None:
        """Verify FFI adapter source does not call subprocess or directly unpack outcome (Prompt 51).

        - Invariant: FFI adapter isolates host invocation through OEOS seam; zero direct process spawning.
        - Break: Module imports subprocess or parses raw outcome['result'] without envelope check.
        - Witness: Code scan of omega_engine_pfp/ffi.py passes structural constraints.
        - Mutation: Adding 'import subprocess' or direct dictionary indexing causes test failure.
        """
        ffi_path = Path("omega_engine_pfp/ffi.py")
        assert ffi_path.exists()
        source = ffi_path.read_text(encoding="utf-8")

        # Assert no direct subprocess usage
        assert "subprocess" not in source
        assert "os.system" not in source
        assert "popen" not in source.lower()

        # Assert no unchecked bracket access to outcome["result"]
        assert 'outcome["result"]' not in source
        assert "outcome.get('result')" not in source

    def test_p52_problem_runner_refuses_before_consuming_input(self) -> None:
        """Verify ProblemRunnerUseCase raises RustFunctionalRequired before inspecting input (Prompt 52).

        - Invariant: Python cannot calculate Phi1/Gamma2; ProblemRunnerUseCase refuses immediately.
        - Break: Python attempts ad-hoc mathematical metric evaluation or accesses problem_input.
        - Witness: ProblemRunnerUseCase.run_problem raises RustFunctionalRequired.
        - Mutation: Returning a Python dictionary reduction without raising fails test.
        """
        runner = ProblemRunnerUseCase()
        with pytest.raises(RustFunctionalRequired) as exc_info:
            runner.run_problem(problem_input=None, task_id="specimen_test")
        assert "RUST_FUNCTIONAL_REQUIRED" in str(exc_info.value)

    def test_p11_clean_architecture_domain_inward_dependency_purity(self) -> None:
        """Verify Clean Architecture: domain package has zero outward imports to use_cases/infra/etc.

        - Invariant: All domain imports point strictly inward or to Python standard library.
        - Break: domain/ imports from use_cases/, infrastructure/, or controllers/.
        - Witness: AST scan of all domain/ files finds zero outward package references.
        - Mutation: Adding outward import violates Clean Architecture layer boundary.
        """
        import ast
        domain_root = Path("omega_engine_pfp/domain")
        forbidden_prefixes = (
            "omega_engine_pfp.use_cases",
            "omega_engine_pfp.infrastructure",
            "omega_engine_pfp.controllers",
            "omega_engine_pfp.entrypoints",
        )

        for py_file in domain_root.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_prefixes:
                            assert not alias.name.startswith(forbidden), (
                                f"Inward purity violation in {py_file}: imports {alias.name}"
                            )
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for forbidden in forbidden_prefixes:
                        assert not mod.startswith(forbidden), (
                            f"Inward purity violation in {py_file}: from {mod} import ..."
                        )


class TestPolarizedOperadTier1:
    """Tier 1 Feature Coverage: Polarized Operads Triad & Graft Sites (Prompt 05)."""

    def test_p05_polarized_operad_triad_role_purity_and_planar_grafts(self) -> None:
        r"""Verify operadic triad role purity, prohibited actions, and planar graft invariants.

        - Invariant: O = O^+ \sqcup O^- \sqcup O_repair.
          O^- raises ProhibitedRepairError on patch emission.
          O_repair raises ProhibitedEvaluationError on verdict.
          Planar grafts evaluate V, E, and T site invariants.
        - Break: O^- emits patch; O_repair evaluates truth; seam type mismatches.
        - Witness: ProhibitedRepairError, ProhibitedEvaluationError, IllTypedCompositionError.
        - Mutation: Allowing O^- to emit patches without raising turns test red.
        """
        from omega_engine_pfp.domain.operad import (
            ConstructiveMorphism,
            GraftSite,
            IllTypedCompositionError,
            InterrogativeMorphism,
            PlanarGraft,
            Polarity,
            PolarizedOperadTriad,
            ProhibitedEvaluationError,
            ProhibitedRepairError,
            RepairMorphism,
        )

        triad = PolarizedOperadTriad()

        gen = ConstructiveMorphism(
            name="gen_claim",
            input_types=("Premise", "Context"),
            output_type="Theorem",
            polarity=Polarity.CONSTRUCTIVE,
        )
        anti = InterrogativeMorphism(
            name="audit_claim",
            input_types=("Theorem",),
            output_type="FindingSet",
            polarity=Polarity.INTERROGATIVE,
        )
        repair = RepairMorphism(
            name="repair_claim",
            input_types=("Theorem", "FindingSet"),
            output_type="PatchedTheorem",
            polarity=Polarity.CORRECTIVE,
        )

        triad.register_constructive(gen)
        triad.register_interrogative(anti)
        triad.register_corrective(repair)

        # Break & Witness: O^- cannot emit patch
        with pytest.raises(ProhibitedRepairError):
            anti.emit_patch()

        # Break & Witness: O_repair cannot evaluate
        with pytest.raises(ProhibitedEvaluationError):
            repair.evaluate()

        # Planar Grafts
        gv = triad.create_graft(GraftSite.VERTEX, "t1", gen.name)
        assert gv.evaluate_invariants({"generator_valid": True})[0] is True

        ge = triad.create_graft(
            GraftSite.EDGE, "t1_e0", anti.name, seam_index=0, expected_type="Theorem", actual_type="Theorem"
        )
        assert ge.evaluate_invariants({})[0] is True

        ge_bad = triad.create_graft(
            GraftSite.EDGE, "t1_e0_bad", anti.name, seam_index=0, expected_type="Theorem", actual_type="Lemma"
        )
        assert ge_bad.evaluate_invariants({})[0] is False

        # Composition
        sub_gen = ConstructiveMorphism(
            name="load_premise",
            input_types=("Axiom",),
            output_type="Premise",
            polarity=Polarity.CONSTRUCTIVE,
        )
        composed = triad.partial_compose(gen, sub_gen, i=0)
        assert composed.input_types == ("Axiom", "Context")

        with pytest.raises(IllTypedCompositionError):
            triad.partial_compose(gen, sub_gen, i=1)

        # Mutation verification: mutant allowing repair on anti-skill fails
        mutant_allows_repair = False
        try:
            anti.emit_patch()
            mutant_allows_repair = True
        except ProhibitedRepairError:
            mutant_allows_repair = False
        assert mutant_allows_repair is False

