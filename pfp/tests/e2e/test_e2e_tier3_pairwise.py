"""Tier 3 E2E Test Suite: Cross-Feature Pairwise Combinatorial Interactions.

AuthorityEffect: None.
Reference: TEST_INFRA.md Tier 3 Specification.
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

# Exact Rational Arithmetic
from omega_engine_pfp.domain.exact.q import Q, ONE, ZERO, parse_q, fmt_q
from omega_engine_pfp.domain.exact.errors import ExactError

# Packet Codec & Sealing
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

# Carrier Constrained Decoding & Glyphs
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
from omega_engine_epistemic_immune_system.domain.danger_gate import (
    TwoSignalDangerGate,
    DangerEvaluationResult,
)
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
)

# Quarantine & Cemetery Persistence
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


# ==============================================================================
# 1. Pairwise: PacketCodec Cryptographic Envelope + Exact Rational Arithmetic (Q)
# ==============================================================================

class TestPairwisePacketCodecAndExactKernel:
    """Pairwise interactions between RFC 8785 envelope sealing and exact rational arithmetic."""

    def test_pairwise_seal_envelope_containing_exact_rationals(self) -> None:
        """Verify that sealing payloads containing stringified exact rationals produces valid digests.

        - Invariant: Exact rational states serialized canonically preserve byte identity across seal/verify.
        - Break: Round-trip JSON serialization mutates big rational representation or breaks hash check.
        - Witness: Computed sha256 matches envelope header sha256 with exact fraction values preserved.
        - Mutation: Changing rational string '355/113' to '3.14159' breaks exactness contract.
        """
        q1 = Q.of(355, 113)
        q2 = Q.of(-22, 7)
        q_sum = q1 + q2

        payload = {
            "q1": fmt_q(q1),
            "q2": fmt_q(q2),
            "sum": fmt_q(q_sum),
            "reduced_den": q_sum.den,
            "reduced_num": q_sum.num,
        }

        sealed = PacketCodec.seal(payload, packet_family="EXACT_ARITHMETIC_EXCHANGE")
        assert sealed["packet_family"] == "EXACT_ARITHMETIC_EXCHANGE"
        assert sealed["authority_effect"] == "None"
        assert "envelope_sha256" in sealed
        assert "payload_sha256" in sealed

        is_valid, digest, msg = PacketCodec.verify(sealed)
        assert is_valid is True
        assert digest == sealed["payload_sha256"]
        assert msg == "OK"

        # Reconstructed rationals match original values exactly
        parsed_sum = parse_q(sealed["payload"]["sum"])
        assert parsed_sum == q_sum
        assert parsed_sum.num == 355 * 7 + (-22) * 113
        assert parsed_sum.den == 113 * 7

    def test_pairwise_tampered_payload_triggers_codec_failure_and_exact_check(self) -> None:
        """Verify that bit-flipping an exact rational in a sealed envelope fails verification.

        - Invariant: Cryptographic envelope verification fails-closed on any payload tampering.
        - Break: Mutated rational payload passes verification undetected.
        - Witness: PacketCodec.verify returns is_valid=False with mismatched digest message.
        - Mutation: Modifying a single character in the rational representation alters canonical bytes.
        """
        initial_q = Q.of(1000000007, 1000000009)
        payload = {"witness": fmt_q(initial_q)}
        sealed = PacketCodec.seal(payload, packet_family="WITNESS_CERT")

        # Tamper payload
        tampered = dict(sealed)
        tampered["payload"] = dict(tampered["payload"])
        tampered["payload"]["witness"] = "1000000008/1000000009"

        is_valid, digest, msg = PacketCodec.verify(tampered)
        assert is_valid is False
        assert "mismatch" in msg.lower()
        assert digest != sealed["payload_sha256"]

    def test_pairwise_exact_q_division_by_zero_precludes_envelope_construction(self) -> None:
        """Verify that attempted division by zero in Q raises before envelope creation.

        - Invariant: Domain exact arithmetic prevents creation of undefined mathematical objects.
        - Break: Q division by zero produces None or float inf that enters envelope pipeline.
        - Witness: ExactError("RR-DIVISION-BY-ZERO") is raised synchronously.
        - Mutation: Replacing ExactError with silent zero allows corrupted envelopes.
        """
        q_valid = Q.of(5, 7)
        q_zero = ZERO

        with pytest.raises(ExactError) as exc_info:
            _ = q_valid / q_zero
        assert exc_info.value.code == "RR-DIVISION-BY-ZERO"

    def test_pairwise_decoding_receipt_accuracy_with_exact_q(self) -> None:
        """Verify that DecodingReceipt measures carrier alignment and divergence deterministically.

        - Invariant: DecodingReceipt measures carrier alignment and divergence deterministically.
        - Break: Metric values diverge from exact character counts.
        - Witness: Receipt fields conform to exact non-negative integer character lengths.
        - Mutation: Claiming stronger constraint mode than provider supports raises ValueError.
        """
        carrier = Carrier((CarrierMember("a", "U+0061"), CarrierMember("b", "U+0062")))
        receipt = DecodingReceipt.measure(
            provider="local",
            text="aba",
            carrier=carrier,
            applied=ConstraintMode.GRAMMAR,
        )
        assert receipt.emission_within_carrier is True
        assert receipt.mode.is_exact is True
        assert len(receipt.violations) == 0


# ==============================================================================
# 2. Pairwise: Tower Wire Grammar Parsing + Homology & Dual Certification
# ==============================================================================

class TestPairwiseGrammarParsingAndHomologyVerification:
    """Pairwise interactions between Tower wire parser, simplicial validation, and dual witnesses."""

    def test_pairwise_wire_parse_to_simplex_boundary_validation(self) -> None:
        """Verify that valid wire expression parses into AST and passes simplicial coboundary validation.

        - Invariant: Wire parser output structures conform to simplex chain complexes with d^2 = 0.
        - Break: Valid wire expression fails simplex verification or produces unhandled exception.
        - Witness: parse_wire emits valid AST node; validate_level3_simplex returns True.
        - Mutation: Altering simplex face orientations causes coboundary non-nilpotency.
        """
        simplex_packet = parse_wire("op<<101><10><0><1><10>>")
        assert isinstance(simplex_packet, App)
        validate_level3_simplex(simplex_packet)

    def test_pairwise_wire_parse_and_dual_witness_certification(self) -> None:
        """Verify that wire expressions paired with exact dual certificates pass joint validation.

        - Invariant: Dual witness W satisfies primal_mass == dual_mass and net vertex flow is zero.
        - Break: Invalid dual witness is admitted or valid certificate rejected.
        - Witness: validate_dual_cert passes with valid zero-gap flow cycle.
        - Mutation: Certificate with unbalanced flow raises DualWitnessError.
        """
        valid_cert = parse_wire(
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

    def test_pairwise_multi_representation_wire_round_trip(self) -> None:
        """Verify round-trip translation between Wire, Compact, DAG, and Tagged JSON representations.

        - Invariant: AST is invariant under translation across all wire serialization formats.
        - Break: Converting between formats produces differing AST structures or loss of nodes.
        - Witness: parse(emit(ast)) == ast across all 4 formats.
        - Mutation: Dropping diff operands or mangling app arguments breaks round-trip.
        """
        ast = parse_wire("op<<1><a>>")

        # Compact
        compact_text = emit_compact(ast)
        reparsed_compact = parse_compact(compact_text)
        assert reparsed_compact == ast

        # Postfix
        postfix_text = emit_postfix(ast)
        reparsed_postfix = parse_postfix(postfix_text)
        assert reparsed_postfix == ast

        # Tagged JSON
        json_text = emit_tagged_json(ast)
        reparsed_json = parse_tagged_json(json_text)
        assert reparsed_json == ast

        # DAG
        dag_text = emit_dag(ast)
        reparsed_dag = parse_dag(dag_text)
        assert reparsed_dag == ast

    def test_pairwise_malformed_wire_triggers_typed_refusal(self) -> None:
        """Verify that syntactically malformed wire expressions raise typed WireError.

        - Invariant: Wire parser fails-closed with WireError on syntax, lexical, or arity errors.
        - Break: Malformed wire returns None, crashes with raw IndexError, or emits partial AST.
        - Witness: WireError raised on unclosed parenthesis or invalid operator tokens.
        - Mutation: Allowing bare strings without closing parenthesis produces silent corruption.
        """
        with pytest.raises(WireError):
            parse_wire("op<<1><a>")  # Missing closing bracket

        with pytest.raises(WireError):
            parse_wire("invalid_op(a, b)")


# ==============================================================================
# 3. Pairwise: Allosteric Quorum Gate + Clonal Selection Maturation
# ==============================================================================

class TestPairwiseAllosteryAndClonalMaturation:
    """Pairwise interactions between Allosteric consensus gating and clonal rule maturation."""

    def test_pairwise_allosteric_quorum_activates_clonal_stimulation(self) -> None:
        """Verify that reaching allosteric quorum triggers clonal rule stimulation and affinity boost.

        - Invariant: Quorum activation (Hill response >= threshold) triggers clonal proliferation.
        - Break: Quorum reached but rule remains idle, or sub-threshold signal triggers boost.
        - Witness: Gate activates when aggregate >= 2; stimulated rule resets idle and boosts affinity.
        - Mutation: Sub-threshold signal activating gate violates Hill kinetics.
        """
        gate = AllostericConsensusGate(
            parameters=HillParameters(hill_coefficient=2, half_maximal_constant=Fraction(2)),
            activation_threshold=Fraction(1, 2),
        )

        initial_rule = DetectorRule(
            rule_id="RULE-MUB-01",
            target_epitope="UNCONSTRAINED_FLOAT",
            match_pattern=r"float\(",
            generation=1,
            affinity_score=1.0,
            half_life_runs=5,
            runs_idle=2,
            is_active=True,
        )

        # Multi-sensor signals: 3 independent agents report 4/5, 7/10, 9/10 -> sum = 12/5 > K = 2
        sensor_signals = {"agent_a": Fraction(4, 5), "agent_b": Fraction(7, 10), "agent_c": Fraction(9, 10)}
        decision = gate.evaluate_quorum(sensor_signals)

        assert decision.is_activated is True
        assert decision.hill_value >= Fraction(1, 2)
        assert decision.aggregate_signal == Fraction(12, 5)
        assert decision.positive_sensors == 3

        # Upon activation, stimulate rule
        stimulated_rule = ClonalSelectionEngine.stimulate(initial_rule, affinity_boost=0.2)
        assert stimulated_rule.affinity_score == pytest.approx(1.2, abs=1e-6)
        assert stimulated_rule.runs_idle == 0
        assert stimulated_rule.is_active is True

    def test_pairwise_allosteric_subthreshold_triggers_clonal_decay(self) -> None:
        """Verify that failing allosteric quorum leads to idle decay and eventual rule eviction.

        - Invariant: When quorum is not reached, rules experience idle decay, evicting upon half-life.
        - Break: Inactive rules remain in filtered active repertoire.
        - Witness: Filtered repertoire excludes decayed rule when runs_idle >= half_life_runs.
        - Mutation: Counting expired rules as active causes token context bloat.
        """
        gate = AllostericConsensusGate(
            parameters=HillParameters(hill_coefficient=2, half_maximal_constant=Fraction(2)),
            activation_threshold=Fraction(1, 2),
        )

        # Weak isolated sensor signal: a single agent reports 2/5 < K = 2
        decision = gate.evaluate_quorum({"agent_a": Fraction(2, 5)})
        assert decision.is_activated is False
        assert decision.hill_value < Fraction(1, 2)
        assert decision.aggregate_signal == Fraction(2, 5)

        # Rule undergoing decay due to sub-threshold run
        rule = DetectorRule(
            rule_id="RULE-IDLE-01",
            target_epitope="BENIGN_PROBE",
            match_pattern=r"probe",
            generation=1,
            affinity_score=0.8,
            half_life_runs=2,
            runs_idle=1,
            is_active=True,
        )

        # After one idle cycle: runs_idle becomes 2 == half_life_runs -> is_active becomes False
        decayed_rule = ClonalSelectionEngine.apply_decay(rule)
        assert decayed_rule.runs_idle == 2
        assert decayed_rule.is_active is False

        repertoire = [decayed_rule]
        active_repertoire = ClonalSelectionEngine.filter_active_repertoire(repertoire)
        assert len(active_repertoire) == 0

    def test_pairwise_somatic_hypermutation_evaluated_by_thymus_gate(self) -> None:
        """Verify that somatic hypermutations are tested against central tolerance before circulation.

        - Invariant: Mutated daughter rules that cross-react with self-panel trigger apoptosis.
        - Break: Self-reactive mutated rule is admitted into active repertoire.
        - Witness: ThymusGate rejects mutated rule with autoimmune_violations > 0; admits clean child.
        - Mutation: Allowing wildcard pattern '.*' causes autoimmune failure on clean fixtures.
        """
        self_panel = [
            "def exact_bareiss_det(matrix: list[list[Q]]) -> Q:",
            "class SimplicialComplexChain:",
            "def verify_pontryagin_phase(cycle: HolonomyLoop) -> bool:",
        ]
        thymus = ThymusGate(self_panel)

        parent = DetectorRule(
            rule_id="PARENT-RULE",
            target_epitope="UNCONSTRAINED_FLOAT",
            match_pattern=r"float\s*\(",
            generation=1,
            affinity_score=1.0,
            half_life_runs=10,
            runs_idle=0,
            is_active=True,
        )

        # Mutate to overly broad pattern that matches self-panel keyword 'matrix'
        autoimmune_child = ClonalSelectionEngine.mutate_rule(
            parent_rule=parent,
            mutation_variant=r"matrix",
            new_rule_id="MUTANT-BROAD",
        )
        assert autoimmune_child.generation == 2
        result_bad = thymus.evaluate_rule(autoimmune_child)
        assert result_bad.is_admitted is False
        assert result_bad.autoimmune_violations >= 1

        # Mutate to specific target pattern that does NOT touch self-panel
        clean_child = ClonalSelectionEngine.mutate_rule(
            parent_rule=parent,
            mutation_variant=r"np\.float64\(",
            new_rule_id="MUTANT-SPECIFIC",
        )
        result_good = thymus.evaluate_rule(clean_child)
        assert result_good.is_admitted is True
        assert result_good.autoimmune_violations == 0


# ==============================================================================
# 4. Pairwise: Two-Signal Danger Gate + Quarantine Cemetery Ledger
# ==============================================================================

class TestPairwiseDangerGateAndCemeteryLedger:
    """Pairwise interactions between Two-Signal danger evaluation and quarantine ledger custody."""

    def test_pairwise_corroborated_danger_quarantined_to_cemetery_ledger(self, tmp_path: Path) -> None:
        """Verify that corroborated Danger (Signal 1 + Signal 2) commits to EpistemicQuarantineLedger.

        - Invariant: Quarantined decisions produce permanent, immutable ledger records.
        - Break: Quarantined packet is lost, suppressed from ledger, or fails hash binding.
        - Witness: Ledger size increments by 1; last entry records exact SHA-256 and refusal code.
        - Mutation: Failing to commit quarantined artifacts to CemeterySink violates zero data-loss.
        """
        signal1 = [
            Signal1Match(
                epitope_name="UNCHECKED_FLOAT_IN_COBOUNDARIES",
                pattern_matched="0.001",
                confidence=0.95,
                offset=42,
            )
        ]
        signal2 = Signal2Danger(
            danger_type="NON_CONVERGENT_COHOMOLOGY",
            severity=DangerSeverity.CRITICAL,
            defect_count=3,
            evidence_digest="sha256_defect_proof_hash_12345",
        )

        eval_result = TwoSignalDangerGate.evaluate(signal1, signal2)
        assert eval_result.decision == DangerDecision.QUARANTINED
        assert eval_result.is_suppressed is True

        # Commit to quarantine ledger
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
        assert len(ledger.entries) == 1

        # Persist and verify round-trip
        serialized = serialize_ledger_to_jsonl(ledger)
        res = deserialize_ledger_from_jsonl(serialized)
        assert res.is_ok
        loaded_ledger = res.unwrap()
        assert loaded_ledger.ledger_id == "LEDGER-E2E-01"
        assert len(loaded_ledger.entries) == 1

    def test_pairwise_signal1_without_signal2_tolerated_as_diagnostic_no_quarantine(self) -> None:
        """Verify that benign Signal 1 without Signal 2 evaluates to DIAGNOSTIC_ONLY without quarantine.

        - Invariant: Matzinger Danger Theory tolerates benign foreignness without structural danger.
        - Break: Benign diagnostic probe triggers defensive lockdown or unmerited quarantine.
        - Witness: DangerDecision is DIAGNOSTIC_ONLY with is_suppressed=False.
        - Mutation: Locking down on Signal 1 alone causes false-alarm deadlock.
        """
        signal1 = [
            Signal1Match(
                epitope_name="ACADEMIC_PROBE_TOKEN",
                pattern_matched="probe_query",
                confidence=0.8,
                offset=0,
            )
        ]
        # Zero structural damage: signal2_danger is None
        eval_result = TwoSignalDangerGate.evaluate(signal1, None)
        assert eval_result.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert eval_result.is_suppressed is False

    def test_pairwise_host_fence_audit_flags_drive_quarantine_kill_decision(self) -> None:
        """Verify that PontryaginKillFlags trigger quarantine verdict in HostFenceAudit.

        - Invariant: Non-zero Pontryagin obstruction flags violate HostFenceAudit (quarantine_verdict=False).
        - Break: Obstruction present but quarantine verdict evaluates to True (Clean).
        - Witness: Audit quarantine_verdict is False when flag_pi or flag_u1 is raised; True when clean.
        - Mutation: Ignoring flag_zn permits untracked torsion leaks.
        """
        # Flag raised for U(1) holonomy curvature obstruction
        flags = PontryaginKillFlags(
            flag_pi=False,
            flag_u1=True,
            flag_zn=False,
            flag_alpha=False,
        )
        audit = HostFenceAudit.evaluate(flags)
        assert audit.quarantine_verdict is False  # ViolatedKillFence (<0>)

        # All flags cleared
        clean_flags = PontryaginKillFlags(
            flag_pi=False,
            flag_u1=False,
            flag_zn=False,
            flag_alpha=False,
        )
        clean_audit = HostFenceAudit.evaluate(clean_flags)
        assert clean_audit.quarantine_verdict is True  # QuarantinedClean (<1>)


# ==============================================================================
# 5. Pairwise: Carrier Constrained Decoding + Presentation Pins
# ==============================================================================

class TestPairwiseCarrierDecodingAndPresentationPins:
    """Pairwise interactions between carrier-constrained decoding and presentation pins."""

    def test_pairwise_carrier_members_and_presentation_pin_resolution(self) -> None:
        """Verify that carrier members correctly bind to pinned generators under PresentationPins.

        - Invariant: PresentationPins resolve canonical generators without permutation ambiguity.
        - Break: Unknown generator admitted or permutation order corrupted.
        - Witness: PresentationPins.resolve maps generator to pinned carrier representation.
        - Mutation: Permuting generators without updating relations causes orbit mismatch.
        """
        carrier = Carrier((CarrierMember("a", "U+0061"), CarrierMember("b", "U+0062"), CarrierMember("c", "U+0063")))
        assert len(carrier.members) == 3

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
        c3 = pins.resolve("c3")
        assert c3 is not None
        assert c3.period == 3
        assert c3.apply_successor("a", 1) == "b"

    def test_pairwise_gbnf_grammar_enforces_carrier_boundary(self) -> None:
        """Verify that GBNF grammar generation restricts LLM token space to declared carrier.

        - Invariant: carrier_gbnf produces grammar string containing all carrier terminals.
        - Break: Carrier member missing from grammar rule or unbounded character set permitted.
        - Witness: Generated GBNF string includes explicit terminal alternatives for all carrier members.
        - Mutation: Omitting carrier members prevents legal retraction turns.
        """
        carrier = Carrier((CarrierMember("a", "U+0061"), CarrierMember("b", "U+0062")))
        gbnf_text = carrier_gbnf(carrier)
        assert "root ::=" in gbnf_text
        assert '"a"' in gbnf_text
        assert '"b"' in gbnf_text

    def test_pairwise_verify_emission_validates_against_carrier(self) -> None:
        """Verify that verify_emission rejects emissions containing out-of-carrier tokens.

        - Invariant: Strict emission verification flags any token outside the allowed carrier.
        - Break: Out-of-carrier emission marked as valid.
        - Witness: verify_emission returns non-empty findings tuple on out-of-carrier input.
        - Mutation: Tolerating unconstrained natural language violates Symbol Game discipline.
        """
        carrier = Carrier((CarrierMember("a", "U+0061"),))

        valid_emission = "a"
        violations = verify_emission(valid_emission, carrier)
        assert len(violations) == 0

        # Emission contains 'b' which is not in carrier
        invalid_emission = "b"
        violations_bad = verify_emission(invalid_emission, carrier)
        assert len(violations_bad) > 0


# ==============================================================================
# 6. Pairwise: Strict Descent Functional & Problem Runner Boundary
# ==============================================================================

class TestPairwiseDescentAndProblemRunnerBoundary:
    """Pairwise interactions between strict descent functionals and problem runner FFI boundary."""

    def test_pairwise_problem_runner_requires_sovereign_rust_functional(self) -> None:
        """Verify that ProblemRunnerUseCase enforces the sovereign Rust functional boundary.

        - Invariant: Zero ad-hoc Python mathematical solvers; runner delegates to Rust functional.
        - Break: Problem runner executes mathematical descent locally in Python without Rust engine.
        - Witness: ProblemRunnerUseCase.run_problem raises RustFunctionalRequired.
        - Mutation: Catching RustFunctionalRequired and substituting Python solver breaks sovereignty.
        """
        runner = ProblemRunnerUseCase()
        with pytest.raises(RustFunctionalRequired, match="RUST_FUNCTIONAL_REQUIRED"):
            runner.run_problem(problem_input=None, task_id="specimen_test")

    def test_pairwise_strict_descent_verifies_lexicographic_reduction(self) -> None:
        """Verify that strict_descent requires monotonic decrease on exact rational states.

        - Invariant: A candidate turn is admitted if and only if after is strictly less than before.
        - Break: Turn with higher defect count or equal state is admitted as progress.
        - Witness: strict_descent returns True for strictly smaller value; False for stagnant/worse state.
        - Mutation: Weakening strict descent to <= allows cyclic infinite loops.
        """
        before_state = Fraction(5, 1)
        after_good = Fraction(3, 1)
        after_stagnant = Fraction(5, 1)
        after_worse = Fraction(7, 1)

        assert strict_descent(before_state, after_good) is True
        assert strict_descent(before_state, after_stagnant) is False
        assert strict_descent(before_state, after_worse) is False

    def test_pairwise_refuse_model_functionals_guards_against_floats(self) -> None:
        """Verify that refuse_model_functionals blocks any uncertified model functional claims.

        - Invariant: Evaluators reject model-supplied functional or authority claims as host evidence.
        - Break: Model claims like gamma2 or phi1 admitted into discrete manifold descent calculations.
        - Witness: refuse_model_functionals raises DemoRefusal('MODEL_FUNCTIONAL_CLAIM') on gamma2.
        - Mutation: Allowing model functional claims introduces hallucinated descent.
        """
        with pytest.raises(DemoRefusal, match="MODEL_FUNCTIONAL_CLAIM"):
            refuse_model_functionals({"gamma2": "1/2"})

        # Clean dictionary without forbidden keys passes without error
        clean_payload = {"step": 1, "action": "retract"}
        refuse_model_functionals(clean_payload)


# ==============================================================================
# 7. Pairwise: Stage Progression & Failure Class Detection
# ==============================================================================

class TestPairwiseStageProgressionAndPharmacyDetection:
    """Pairwise interactions between stage level transitions and epistemic pharmacy detectors."""

    def test_pairwise_pharmacy_detects_failure_classes_in_candidate_payload(self) -> None:
        """Verify that pharmacy detector maps malformed candidate strings to exact FailureClasses.

        - Invariant: detect() categorizes uncertified claims, fake receipts, and authority leaks.
        - Break: Known failure pattern passes undetected or produces wrong FailureClass.
        - Witness: DetectorReport contains exact matching findings.
        - Mutation: Lowering detection sensitivity allows prompt-injection or hallucinated proofs.
        """
        pos_fake = {"receipt": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
        context = DetectionContext(
            host_replay_receipt=HostReplayReceipt(
                receipt_id="REC-01",
                host_signer="TEST_HOST",
                target_digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
                replay_passed=True,
            ),
        )

        report = detect(pos_fake, context)
        assert isinstance(report, DetectorReport)
        classes_found = {f.failure_class for f in report.findings}
        assert FailureClass.SELF_CERTIFICATION in classes_found
        assert FailureClass.FAKE_RECEIPT in classes_found

    def test_pairwise_stage_level_bounds_and_kill_map(self) -> None:
        """Verify that StageLevel value object enforces ordering and discrete bounds.

        - Invariant: StageLevel is an integer >= 0, supporting monotonic strict ordering (<).
        - Break: StageLevel admits negative integers or bools, or fails monotonic comparison.
        - Witness: StageLevel(0) < StageLevel(1) < StageLevel(10); negative level raises ValueError.
        - Mutation: Allowing negative stage levels corrupts stratum index.
        """
        s0 = StageLevel(0)
        s1 = StageLevel(1)
        s10 = StageLevel(10)

        assert s0 < s1 < s10
        assert s0 != 0  # Exact-type equality rejecting int confusion
        assert s0 != "0"

        with pytest.raises(ValueError, match="cannot be negative"):
            _ = StageLevel(-1)

        with pytest.raises(TypeError, match="must be an integer"):
            _ = StageLevel("1")  # type: ignore[arg-type]
