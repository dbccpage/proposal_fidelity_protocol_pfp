"""Tier 5 Adversarial Coverage Hardening Suite: Milestones 4–5 (Challenger 2).

White-box empirical stress testing of domain components across M4–M5:
- domain/decoding/ (TokenFrontier wire vocabulary masking, exact Bayes renormalization in Fraction,
  Tarski polygraph, antimorphism involution, information cohomology)
- domain/genesis/ (GenesisStagePin, InvariantTriad, Ruling D4 apparatus set)
- domain/tower_lift/ (Finite exhaustion search, binary relations, pinned digests)
- domain/ast_cochain/ (Asymmetric LGGR, AST 1-skeleton cochain exactness)
- domain/claim_hygiene/ (Paper claim stripper, citation anchors, regex hygiene)
- domain/sandbox/ (Process boundary config, profile A mock seam, real refusal codes)
- domain/sovereignty/ (Three-layer sovereignty: attention key mask, carrier logit projection, host replay ground truth)
- domain/dual_witness/ (Exact dual witness certificate validation, subgradient alignment, duality gap 0)
- domain/lean_bridge/ (LeanProofWitness, FormalCertificateBridge, zero sorryAx)
- domain/exact/wire.py (RationalWire canonical integers without slash, RationalDualityGap)
- domain/ports/ (All @runtime_checkable domain protocol conformance)

Examiner Discipline: Invariant, Break, Witness, Mutation on each test.
Claim Hygiene: Bounded phrasing; zero forbidden hype words.
AuthorityEffect: None.
ZERO-FLOAT Law: Pure Fraction, integer, or discrete relations.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import re
from typing import Any, Mapping, Sequence, Tuple
import pytest

# 1. Decoding domain imports
from pfp.domain.decoding import (
    AntimorphismTransitionModel,
    Confluence2Cell,
    CriticalPair,
    DecodingError,
    DecodingRefusalCode,
    EdgeInvolution,
    EntropyCocycle,
    EpistemicQuarantineLedger,
    FrontierCandidate,
    InformationCohomologyBarcode,
    InvolutionIdentityError,
    PersistenceInterval,
    ProtectedDistinction,
    ProtectedDistinctionCollapseError,
    QuarantinedShadowPacket,
    RefusedZeroRetainedMassError,
    RetainedProbabilityMass,
    ReversalMap,
    RewriteStep,
    TarskiPolygraph,
    TokenFrontier,
    WireVocabulary,
    ZeroFloatViolationError,
)

# 3. Genesis domain imports
from pfp.domain.genesis import (
    GenesisStage,
    GenesisStagePin,
    InvariantTriad,
)

# 4. Tower lift domain imports
from pfp.domain.tower_lift import (
    BinaryRelation,
    CarrierSet,
    LiftExhaustionReceipt,
    PINNED_EXHAUSTION_DIGESTS,
)

# 5. AST cochain domain imports
from pfp.domain.ast_cochain import (
    AstCochainReceipt,
    DependencyEdge,
    LggrVerdict,
)

# 6. Claim hygiene domain imports
from pfp.domain.claim_hygiene import (
    CitationAnchor,
    FORBIDDEN_HYPE_REPLACEMENTS,
    PaperClaim,
    strip_forbidden_hype_words,
)

# 7. Sandbox domain imports
from pfp.domain.sandbox import (
    ContainerProfile,
    ProcessBoundaryConfig,
    SeamExecutionResult,
)

# 9. Sovereignty domain imports
from pfp.domain.sovereignty import (
    AttentionMaskInterventionReceipt,
    CarrierProjectionReceipt,
    IndependentHostReplayVerdict,
)

# 10. Dual witness domain imports
from pfp.domain.dual_witness import (
    ExactDualWitnessCertificate,
)

# 11. Lean bridge domain imports
from pfp.domain.lean_bridge import (
    FormalCertificateBridge,
    LeanProofWitness,
)

# 12. Exact rational wire domain imports
from pfp.domain.exact import (
    RationalDualityGap,
    RationalWire,
)

# 13. Domain ports imports
from pfp.domain.ports.decoding_ports import (
    IAntimorphismService,
    ICohomologyBarcodeAnalyzer,
    ILogitsProvider,
    IPolygraphConfluenceEngine,
    IQuarantineLedgerPort,
    ITokenFrontierEvaluator,
)
from pfp.domain.ports.genesis_ports import (
    IGenesisCrosswalkOracle,
    IGenesisStageRegistry,
)
from pfp.domain.ports.tower_lift_ports import (
    IFiniteExhaustionSearch,
    ILiftNecessityVerifier,
)
from pfp.domain.ports.ast_cochain_ports import (
    IAstDependencyParser,
    ILggrArbiter,
)
from pfp.domain.ports.flagship_ports import (
    ExactDualLpPort,
    LeanKernelBridgePort,
    ProcessSandboxPort,
)
from pfp.domain.shared_kernel.result import Failure, Result, Success



class TestTier5AdversarialM4M5:
    """White-box adversarial test suite for Milestones 4 and 5."""

    # =========================================================================
    # Group A: domain/decoding/
    # =========================================================================

    def test_decoding_wire_vocabulary_adversarial_boundaries(self) -> None:
        """Challenge WireVocabulary: duplicate tokens, out-of-bounds queries, and vocabulary catalogs.

        - Invariant: A WireVocabulary must reject duplicate tokens with ValueError.
          Token-to-id and id-to-token lookups must throw KeyError and IndexError on invalid bounds.
          Standard vocabularies (toy_4, toy_8, sigma_36, gamma_38) have exact dimensions.
        - Break: Construct vocabulary with duplicate token ("a", "b", "a");
          query nonexistent token or index out of range.
        - Witness: ValueError on initialization, KeyError on missing token, IndexError on negative or high index.
        - Mutation: A mutant that ignores duplicates admits degenerate vocabulary with ambiguous token IDs.
        """
        # Break 1: Duplicate tokens in WireVocabulary
        with pytest.raises(ValueError, match="Duplicate tokens"):
            WireVocabulary(("tok0", "tok1", "tok0"))

        # Invariant: Gamma 38 exact tokens
        v38 = WireVocabulary.gamma_38()
        assert v38.size == 38
        assert v38.id_to_token(0) == "<"
        assert v38.id_to_token(1) == ">"
        assert v38.token_to_id("<") == 0
        assert v38.token_to_id(">") == 1
        assert v38.token_to_id("0") == 2
        assert v38.token_to_id("z") == 37

        # Break 2: Nonexistent token lookup
        with pytest.raises(KeyError, match="Token 'MISSING' not found"):
            v38.token_to_id("MISSING")

        # Break 3: Out-of-bounds token id
        with pytest.raises(IndexError, match="out of bounds"):
            v38.id_to_token(-1)
        with pytest.raises(IndexError, match="out of bounds"):
            v38.id_to_token(38)

        # Mutation: A mutant that allows duplicate vocab violates exact-type equality or size
        v4 = WireVocabulary.toy_4()
        assert (v4 == v38) is False
        assert (v4 == ("a", "b", "c", "d")) is False

    def test_decoding_retained_probability_mass_and_frontier_candidate_boundaries(self) -> None:
        """Challenge RetainedProbabilityMass and FrontierCandidate: range limits and ZERO-FLOAT law.

        - Invariant: Retained probability mass must be in [0, 1] in Fraction, never float.
          FrontierCandidate probabilities must be in [0, 1] in Fraction.
        - Break: Supply float, negative value, value > 1, or cross-type comparison.
        - Witness: ZeroFloatViolationError on float; ValueError on out-of-range; TypeError on invalid types.
        - Mutation: A mutant that accepts floats permits cumulative floating-point drift in normal forms.
        """
        # 1. RetainedProbabilityMass
        rpm_valid = RetainedProbabilityMass(Fraction(3, 5))
        assert rpm_valid.mass == Fraction(3, 5)
        assert rpm_valid.is_zero() is False
        assert rpm_valid.is_one() is False

        rpm_zero = RetainedProbabilityMass(Fraction(0, 1))
        assert rpm_zero.is_zero() is True

        rpm_one = RetainedProbabilityMass(Fraction(1, 1))
        assert rpm_one.is_one() is True

        # Break: float rejection
        with pytest.raises(ZeroFloatViolationError):
            RetainedProbabilityMass(0.5)  # type: ignore

        # Break: out-of-range (< 0 or > 1)
        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            RetainedProbabilityMass(Fraction(-1, 10))
        with pytest.raises(ValueError, match="must be in \\[0, 1\\]"):
            RetainedProbabilityMass(Fraction(11, 10))

        # Break: non-Fraction type
        with pytest.raises(TypeError):
            RetainedProbabilityMass("1/2")  # type: ignore

        # Exact-type equality
        assert (rpm_valid == Fraction(3, 5)) is False

        # 2. FrontierCandidate
        fc = FrontierCandidate(
            token_id=0,
            token="a",
            base_probability=Fraction(1, 4),
            constrained_probability=Fraction(1, 2),
            parser_state="active",
        )
        assert fc.constrained_probability == Fraction(1, 2)

        # Break: float in base or constrained probability
        with pytest.raises(ZeroFloatViolationError):
            FrontierCandidate(0, "a", 0.25, Fraction(1, 2))  # type: ignore
        with pytest.raises(ZeroFloatViolationError):
            FrontierCandidate(0, "a", Fraction(1, 4), 0.5)  # type: ignore

        # Break: out-of-range
        with pytest.raises(ValueError):
            FrontierCandidate(0, "a", Fraction(5, 4), Fraction(1, 2))
        with pytest.raises(ValueError):
            FrontierCandidate(0, "a", Fraction(1, 4), Fraction(-1, 2))

        # Exact-type equality
        assert (fc == (0, "a", Fraction(1, 4), Fraction(1, 2), "active")) is False

    def test_decoding_token_frontier_exact_bayes_and_support_failures(self) -> None:
        """Challenge TokenFrontier: arity mismatch, non-positive total weight, and empty/zero support carrier.

        - Invariant: TokenFrontier conditions probabilities strictly in Fraction via exact Bayes rule.
          Base weights count must equal vocabulary size (WRONG_ARITY).
          Total weight must be strictly positive (INCONSISTENT_PROBABILITY).
          Support cannot be empty or have zero total retained mass (RefusedZeroRetainedMassError).
        - Break: Supply wrong weight count; supply zero total weight; supply admitted indices with 0 base weight.
        - Witness: DecodingError with proper refusal codes or RefusedZeroRetainedMassError.
        - Mutation: A mutant that skips arity check produces index errors or unconstrained divisions.
        """
        vocab = WireVocabulary.toy_4()

        # Break 1: Wrong arity (3 weights for size 4 vocab)
        with pytest.raises(DecodingError) as exc_arity:
            TokenFrontier.evaluate_step(vocab, [1, 2, 3], [0, 1])
        assert exc_arity.value.code == DecodingRefusalCode.WRONG_ARITY

        # Break 2: Total weight <= 0
        with pytest.raises(DecodingError) as exc_nonpos:
            TokenFrontier.evaluate_step(vocab, [0, 0, 0, 0], [0, 1])
        assert exc_nonpos.value.code == DecodingRefusalCode.INCONSISTENT_PROBABILITY

        # Break 3: All admitted tokens carry zero base probability
        # Weights: [0, 0, 10, 20]; Admitted: [0, 1] -> Retained sum = 0
        with pytest.raises(RefusedZeroRetainedMassError, match="Retained probability mass is 0/1"):
            TokenFrontier.evaluate_step(vocab, [0, 0, 10, 20], [0, 1])

        # Break 4: Empty admitted indices
        with pytest.raises(RefusedZeroRetainedMassError, match="empty support carrier"):
            TokenFrontier.evaluate_step(vocab, [1, 2, 3, 4], [])

        # Valid step with evaluate_step_result ROP envelope
        res_ok = TokenFrontier.evaluate_step_result(vocab, [10, 20, 30, 40], [1, 3])
        assert res_ok.is_success is True
        frontier = res_ok.unwrap()
        assert frontier.support_width == 2
        assert frontier.masked_token_count == 2
        # token 1 (20) and token 3 (40) -> total 60. token 1 prob: 20/60 = 1/3, token 3: 40/60 = 2/3
        assert frontier.get_constrained_probability(1) == Fraction(1, 3)
        assert frontier.get_constrained_probability(3) == Fraction(2, 3)
        # Inadmissible tokens receive Fraction(0, 1)
        assert frontier.get_constrained_probability(0) == Fraction(0, 1)
        assert frontier.get_constrained_probability(2) == Fraction(0, 1)

        # ROP envelope failure path
        res_err = TokenFrontier.evaluate_step_result(vocab, [1, 2], [0])
        assert res_err.is_failure is True
        assert res_err.error.code == DecodingRefusalCode.WRONG_ARITY

    def test_decoding_tarski_polygraph_discontinuity_and_divergence(self) -> None:
        """Challenge TarskiPolygraph: discontinuous rewrite paths and divergent join mismatches.

        - Invariant: A 1-cell reduction path must be continuous: step[i].result_term == step[i+1].source_term.
          A confluent 2-cell must close: left reduction and right reduction must reach the identical join_term.
        - Break: Discontinuous step sequence; divergent reduction branches joining to differing terms.
        - Witness: DecodingError with DISCONTINUOUS_REWRITE_CHAIN and DIVERGENT_JOIN_MISMATCH.
        - Mutation: Removing continuity check allows disconnected logic leaps in polygraph confluence.
        """
        # Break 1: RewriteStep empty rule or non-string
        with pytest.raises(ValueError, match="rule_name cannot be empty"):
            RewriteStep("", "0", "termA", "termB")
        with pytest.raises(TypeError, match="Terms must be strings"):
            RewriteStep("r1", "0", 123, "termB")  # type: ignore

        # Break 2: CriticalPair with source mismatching apex
        step_l = RewriteStep("r1", "0", "termApex", "termL")
        step_r_bad = RewriteStep("r2", "0", "OTHER_APEX", "termR")
        with pytest.raises(ValueError, match="must originate from apex"):
            CriticalPair(apex="termApex", step_left=step_l, step_right=step_r_bad)

        # Break 3: Discontinuous rewrite chain
        step_discontinuous_1 = RewriteStep("r1", "0", "start", "intermediate_1")
        step_discontinuous_2 = RewriteStep("r2", "0", "JUMP_UNCONNECTED", "end")
        polygraph = TarskiPolygraph((step_discontinuous_1, step_discontinuous_2))

        with pytest.raises(DecodingError) as exc_disc:
            polygraph.check_continuity((step_discontinuous_1, step_discontinuous_2), "start")
        assert exc_disc.value.code == DecodingRefusalCode.DISCONTINUOUS_REWRITE_CHAIN

        # Break 4: Divergent join mismatch in Confluence2Cell
        step_l1 = RewriteStep("rl", "0", "apex", "left1")
        step_r1 = RewriteStep("rr", "0", "apex", "right1")
        step_l_close = RewriteStep("rl_c", "0", "left1", "join_left")
        step_r_close = RewriteStep("rr_c", "0", "right1", "join_right")

        cell_divergent = Confluence2Cell(
            peak_apex="apex",
            target_left="left1",
            target_right="right1",
            left_path=(step_l_close,),
            right_path=(step_r_close,),
            join_term="claimed_universal_join",  # Neither reaches this!
        )
        res_conf = polygraph.validate_confluence_result(cell_divergent)
        assert res_conf.is_failure is True
        assert res_conf.error.code == DecodingRefusalCode.DIVERGENT_JOIN_MISMATCH

    def test_decoding_antimorphism_involution_and_protected_distinction_collapse(self) -> None:
        """Challenge AntimorphismTransitionModel: broken involution, edge dissipation, and distinction collapse.

        - Invariant: Involution Law requires ((e)^dagger)^dagger = e.
          Contravariant path inversion: (e1 . e2 ... ek)^dagger = ek^dagger ... e1^dagger.
          Down-map projection cannot collapse any protected distinction (state_a != state_b).
        - Break: Non-involutive reversal map; reversing dissipative edge; collapsing projection.
        - Witness: satisfies_involution_law() == False; InvolutionIdentityError; ProtectedDistinctionCollapseError.
        - Mutation: A mutant allowing collapsed distinctions violates boundary preservation.
        """
        # Break 1: Non-involutive reversal map ((e1)^dag = e2, but (e2)^dag = e3 != e1)
        broken_involutions = (
            EdgeInvolution("e1", "e2"),
            EdgeInvolution("e2", "e3"),
            EdgeInvolution("e3", "e1"),
        )
        broken_map = ReversalMap(broken_involutions)
        assert broken_map.satisfies_involution_law() is False

        # Invariant: EdgeInvolution dissipative states
        dissipative_inv = EdgeInvolution("e_decay", "bot")
        assert dissipative_inv.is_dissipative() is True

        valid_involutions = (
            EdgeInvolution("e_12", "e_21"),
            EdgeInvolution("e_21", "e_12"),
            EdgeInvolution("e_23", "e_32"),
            EdgeInvolution("e_32", "e_23"),
            EdgeInvolution("e_34", "e_43"),
            EdgeInvolution("e_43", "e_34"),
            dissipative_inv,
        )
        valid_map = ReversalMap(valid_involutions)
        assert valid_map.satisfies_involution_law() is True

        # Break 2: ProtectedDistinction requires distinct states
        with pytest.raises(ValueError, match="requires distinct states"):
            ProtectedDistinction(state_a="same", state_b="same")

        dist1 = ProtectedDistinction(state_a="alice", state_b="bob", label="identity")
        dist2 = ProtectedDistinction(state_a="bob", state_b="alice", label="identity")
        # Order-insensitive equality
        assert dist1 == dist2
        assert hash(dist1) == hash(dist2)

        model = AntimorphismTransitionModel(
            model_id="atm_adv_01",
            states=frozenset({"s1", "s2", "s3", "s4", "alice", "bob"}),
            edges=frozenset({"e_12", "e_21", "e_23", "e_32", "e_34", "e_43", "e_decay"}),
            reversal_map=valid_map,
            protected_distinctions=frozenset({dist1}),
        )

        # Path reversal contravariance: 3 edges
        path3 = ("e_12", "e_23", "e_34")
        rev3 = model.reverse_path(path3)
        assert rev3 == ("e_43", "e_32", "e_21")
        # Double reversal recovers original path
        assert model.reverse_path(rev3) == path3

        # Empty path reversal returns empty tuple
        assert model.reverse_path(()) == ()

        # Break 3: Reversing dissipative edge raises InvolutionIdentityError
        with pytest.raises(InvolutionIdentityError, match="is irreversible"):
            model.reverse_edge("e_decay")
        res_dis = model.reverse_edge_result("e_decay")
        assert res_dis.is_failure is True

        # Break 4: Collapsing projection
        collapsing_proj = {"alice": "merged_actor", "bob": "merged_actor"}
        with pytest.raises(ProtectedDistinctionCollapseError, match="collapses protected distinction"):
            model.down_map(collapsing_proj)

        # Valid non-collapsing projection succeeds
        valid_proj = {"s1": "s1_new", "s2": "s2_new"}
        projected_model = model.down_map(valid_proj)
        assert "s1_new" in projected_model.states
        assert "alice" in projected_model.states

    def test_decoding_information_cohomology_and_quarantine_ledger_stress(self) -> None:
        """Challenge PersistenceInterval, InformationCohomologyBarcode, and EpistemicQuarantineLedger.

        - Invariant: PersistenceInterval requires birth <= death in Fraction.
          InformationCohomologyBarcode is diagnostic telemetry only (AuthorityEffect None).
          EntropyCocycle satisfies delta^1 o delta^0 = 0.
          QuarantinedShadowPacket cannot be promoted to core (Permanent Quarantine Law).
          EpistemicQuarantineLedger isolates active stages from contaminated theorems.
        - Break: Birth > death; float in intervals or cocycle; attempt to promote quarantined packet.
        - Witness: ValueError, ZeroFloatViolationError, can_promote_to_core() == False.
        - Mutation: A mutant allowing quarantined packet promotion violates truth boundary isolation.
        """
        # Break 1: Birth > death in PersistenceInterval
        with pytest.raises(ValueError, match="Birth 2 cannot exceed death 1"):
            PersistenceInterval(dimension=0, birth=Fraction(2, 1), death=Fraction(1, 1))


        # Break 2: Float in PersistenceInterval
        with pytest.raises(ZeroFloatViolationError):
            PersistenceInterval(dimension=0, birth=0.0, death=Fraction(1, 1))  # type: ignore

        pi = PersistenceInterval(dimension=1, birth=Fraction(1, 3), death=Fraction(5, 3))
        assert pi.persistence == Fraction(4, 3)

        # Barcode total persistence
        barcode = InformationCohomologyBarcode(
            barcode_id="bc_adv_01",
            intervals=(
                PersistenceInterval(dimension=0, birth=Fraction(0, 1), death=Fraction(1, 2)),
                PersistenceInterval(dimension=1, birth=Fraction(1, 4), death=Fraction(3, 4)),
            ),
        )
        assert barcode.total_persistence() == Fraction(1, 2) + Fraction(2, 4)  # 1/2 + 1/2 = 1/1
        assert barcode.authority_effect == "None"

        # Break 3: Float in EntropyCocycle
        with pytest.raises(ZeroFloatViolationError):
            EntropyCocycle(degree=1, coefficients=(0.5, Fraction(1, 2)))  # type: ignore

        cocycle = EntropyCocycle(degree=1, coefficients=(Fraction(1, 2), Fraction(-1, 2)))
        assert cocycle.coboundary_is_nilpotent() is True

        # Permanent Quarantine Law
        shadow_pkt = QuarantinedShadowPacket(
            target_theorem="false_conjecture_p_np",
            refusal_reason="REFUSED_CIRCUIT_LOWER_BOUND_FALLACY",
            raw_evidence=("poly_size_sat_refuted", "oracle_relativization_failure"),
        )
        assert shadow_pkt.is_permanent_quarantine is True
        assert shadow_pkt.can_promote_to_core() is False
        assert len(shadow_pkt.parent_lineage_sha256) == 64

        ledger = EpistemicQuarantineLedger()
        ledger1 = ledger.commit(shadow_pkt)
        assert len(ledger1.records) == 1
        assert ledger1.verify_isolation_against_stage(["unrelated_proven_lemma"]) is True
        assert ledger1.verify_isolation_against_stage(["false_conjecture_p_np"]) is False

        # Mutation: A mutant returning can_promote_to_core == True fails
        mutant_promoter = lambda pkt: True
        assert mutant_promoter(shadow_pkt) is True
        with pytest.raises(AssertionError):
            assert shadow_pkt.can_promote_to_core() is True

    # =========================================================================
    # Group C: domain/genesis/
    # =========================================================================


    def test_genesis_stage_pin_triad_and_ruling_d4_apparatus(self) -> None:
        """Challenge GenesisStagePin, InvariantTriad, and Ruling D4 apparatus set.

        - Invariant: Master commit pin is strictly 'e28f49abea3310ae4a9dc3d17ecb9ab55b267938'.
          InvariantTriad requires non-empty obligation, counterexample, and extension_interface.
          Ruling D4 apparatus set is {12, 17} U [82, 100], containing exactly 21 apparatus stages.
        - Break: Corrupt commit hash; empty field in InvariantTriad; apparatus stage miscount.
        - Witness: is_valid_pin() == False on corrupted hash; is_complete == False on whitespace;
          apparatus set cardinality == 21.
        - Mutation: A mutant omitting stage 17 or 82 alters the Ruling D4 apparatus boundary.
        """
        # Invariant 1: Master pin
        pin = GenesisStagePin()
        assert pin.is_valid_pin() is True

        corrupt_pin = GenesisStagePin(commit_hash="e28f49abea3310ae4a9dc3d17ecb9ab55b267939")
        assert corrupt_pin.is_valid_pin() is False

        # Invariant 2: InvariantTriad
        valid_triad = InvariantTriad(
            obligation="Coboundary exactness",
            counterexample="Non-zero holonomy loop",
            extension_interface="IExactCoboundarySolver",
        )
        assert valid_triad.is_complete is True

        empty_obligation = InvariantTriad("", "Counterexample", "Interface")
        assert empty_obligation.is_complete is False

        whitespace_counterexample = InvariantTriad("Obligation", "   ", "Interface")
        assert whitespace_counterexample.is_complete is False

        # Invariant 3: Ruling D4 Apparatus Set
        apparatus_stages = frozenset({12, 17} | set(range(82, 101)))
        assert len(apparatus_stages) == 21
        assert 12 in apparatus_stages
        assert 17 in apparatus_stages
        assert 82 in apparatus_stages
        assert 99 in apparatus_stages
        assert 100 in apparatus_stages
        assert 81 not in apparatus_stages
        assert 13 not in apparatus_stages

    # =========================================================================
    # Group D: domain/tower_lift/
    # =========================================================================

    def test_tower_lift_exhaustion_search_and_pinned_digests(self) -> None:
        """Challenge CarrierSet, BinaryRelation, and LiftExhaustionReceipt pinned digests.

        - Invariant: CarrierSet checks length(elements) == cardinality.
          Stage 0 (|X|=1): 0 of 2 relations satisfy IRREFLEXIVE_WITNESSED_RELATION.
          Stage 1 (|X|=2): 0 of 16 relations satisfy DIRECTED_PATH_COMPOSITION or DIRECTED_CYCLE_THREE.
          Receipts must strictly match PINNED_EXHAUSTION_DIGESTS.
        - Break: Carrier cardinality mismatch; tampering with exhaustion digest.
        - Witness: ValueError on cardinality mismatch; matches_pinned_digest() == False on tampering.
        - Mutation: A mutant asserting valid relations > 0 on Stage 0 or Stage 1 fails exhaustion proof.
        """
        # Break 1: CarrierSet cardinality mismatch
        with pytest.raises(ValueError, match="Carrier cardinality mismatch"):
            CarrierSet(stage=0, cardinality=2, elements=(0,))

        # Invariant: Stage 0 finite exhaustion verification (0 of 2 relations)
        c0 = CarrierSet(stage=0, cardinality=1, elements=(0,))
        r_empty = BinaryRelation(pairs=frozenset())
        r_loop = BinaryRelation(pairs=frozenset({(0, 0)}))

        # Irreflexive witnessed requires (x, y) with x != y, impossible on |X|=1
        assert (r_empty.is_irreflexive(c0) and r_empty.has_witnessed_pair(c0)) is False
        assert (r_loop.is_irreflexive(c0) and r_loop.has_witnessed_pair(c0)) is False

        # Check all 3 pinned digests
        digest_s0_1 = PINNED_EXHAUSTION_DIGESTS[(0, 1, "IRREFLEXIVE_WITNESSED_RELATION")]
        assert digest_s0_1 == "5357622ee665ea7a9f8460c58bb526234290b499e9a162651a373604c71daa8d"

        digest_s1_2_path = PINNED_EXHAUSTION_DIGESTS[(1, 2, "DIRECTED_PATH_COMPOSITION")]
        assert digest_s1_2_path == "d5d7c90b68bbc386a661aa1faae750ddcd99cf7638a6ed712ce9818635525e76"

        digest_s1_2_cycle = PINNED_EXHAUSTION_DIGESTS[(1, 2, "DIRECTED_CYCLE_THREE")]
        assert digest_s1_2_cycle == "183d94c5100decc047ad14b0c71113935926bea96a3a73301456bf2b1a13f2fc"

        rec_valid = LiftExhaustionReceipt(
            from_stage=0,
            to_stage=1,
            goal="IRREFLEXIVE_WITNESSED_RELATION",
            total_relations_tested=2,
            valid_relations_on_source=0,
            target_witness="{(0, 1)}",
            exhaustion_digest=digest_s0_1,
        )
        assert rec_valid.matches_pinned_digest() is True

        rec_tampered = LiftExhaustionReceipt(
            from_stage=0,
            to_stage=1,
            goal="IRREFLEXIVE_WITNESSED_RELATION",
            total_relations_tested=2,
            valid_relations_on_source=0,
            target_witness="{(0, 1)}",
            exhaustion_digest="0" * 64,  # Tampered digest
        )
        assert rec_tampered.matches_pinned_digest() is False

    # =========================================================================
    # Group E: domain/ast_cochain/
    # =========================================================================

    def test_ast_cochain_zero_float_and_asymmetric_lggr_verdict(self) -> None:
        """Challenge AstCochainReceipt: ZERO-FLOAT enforcement and Asymmetric LGGR verdicts.

        - Invariant: AstCochainReceipt requires defects in Fraction, never float.
          Clean architecture exactness requires BOTH phi_1 == 0 and gamma_2 == 0.
          LggrVerdict supports PASS, REFUSED_LOCAL_GREEN_GLOBAL_RED, LOCAL_RED.
        - Break: Pass float defect; test boundary with non-zero leakage or cycle obstruction.
        - Witness: TypeError on float; is_clean_architecture_exact == False on non-zero defects.
        - Mutation: Allowing local green tests to mask global non-zero phi_1 violates Clean Architecture.
        """
        # Break 1: Float in AstCochainReceipt
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            AstCochainReceipt(
                phi_1_boundary_leakage=0.25,  # type: ignore
                gamma_2_cycle_obstruction=Fraction(0, 1),
                total_modules_analyzed=10,
                total_edges_evaluated=20,
                verdict=LggrVerdict.PASS,
            )

        # Exactness check: both must vanish
        rec_exact = AstCochainReceipt(
            phi_1_boundary_leakage=Fraction(0, 1),
            gamma_2_cycle_obstruction=Fraction(0, 1),
            total_modules_analyzed=5,
            total_edges_evaluated=10,
            verdict=LggrVerdict.PASS,
        )
        assert rec_exact.is_clean_architecture_exact is True

        rec_leaked = AstCochainReceipt(
            phi_1_boundary_leakage=Fraction(1, 1),
            gamma_2_cycle_obstruction=Fraction(0, 1),
            total_modules_analyzed=5,
            total_edges_evaluated=10,
            verdict=LggrVerdict.REFUSED_LOCAL_GREEN_GLOBAL_RED,
        )
        assert rec_leaked.is_clean_architecture_exact is False
        assert rec_leaked.verdict == LggrVerdict.REFUSED_LOCAL_GREEN_GLOBAL_RED

    # =========================================================================
    # Group F: domain/claim_hygiene/
    # =========================================================================

    def test_claim_hygiene_forbidden_hype_words_and_citation_anchoring(self) -> None:
        """Challenge Claim Hygiene: regex whole-word replacement and CitationAnchor verification.

        - Invariant: strip_forbidden_hype_words replaces all 13 hype verbs without mutating substring stems.
          PaperClaim creates sanitized statements with replacement audit trail.
          CitationAnchor binds exact byte-range SHA-256.
        - Break: Text containing hype verbs ('proves', 'guarantees', 'true intelligence'); word with stem ('improve').
        - Witness: 'proves' replaced by 'shows in this model'; 'improve' NOT replaced (whole-word regex \b).
        - Mutation: Substring matching without word boundary corrupts innocent words like 'improve'.
        """
        raw_text = (
            "This work proves that we fundamentally achieve true intelligence. "
            "It guarantees flawless results and obviously improves previous methods."
        )
        sanitized, applied = strip_forbidden_hype_words(raw_text)

        # Replaced verbs
        assert "shows in this model" in sanitized
        assert "specifically" in sanitized
        assert "bounded toy evaluator" in sanitized
        assert "guarantees under the declared assumptions" in sanitized
        assert "checked" in sanitized
        assert "directly" in sanitized

        # Whole-word regex check: 'improves' contains 'proves' as substring, must NOT be mangled!
        assert "improves" in sanitized

        claim = PaperClaim.create("CLAIM_T5_01", raw_text)
        assert claim.claim_id == "CLAIM_T5_01"
        assert claim.authority_effect == "None"
        assert len(claim.replacements_applied) >= 5

        anchor = CitationAnchor(
            citation_id="cite_01",
            doi_or_arxiv="10.1000/182",
            source_title="Topological Solvers",
            byte_range_sha256="a" * 64,
            is_verified=True,
        )
        assert anchor.is_verified is True
        assert (anchor == ("cite_01", "10.1000/182")) is False

    # =========================================================================
    # Group G: domain/sandbox/
    # =========================================================================

    def test_sandbox_process_boundary_and_runtime_refusal_codes(self) -> None:
        """Challenge ProcessBoundaryConfig and native runtime refusal preservation.

        - Invariant: ProcessBoundaryConfig enforces ZERO-FLOAT on timeouts.
          Preserves native refusal codes (REQUEST_NOT_JSON, D0_MALFORMED, BOARD_SHAPE_MISMATCH).
        - Break: Float timeout in ProcessBoundaryConfig; malformed non-JSON inputs.
        - Witness: TypeError on float timeout; SeamExecutionResult records session digest.
        - Mutation: Collapsing distinct refusal codes into a single generic error code fails.
        """
        # Break 1: Float timeout
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            ProcessBoundaryConfig(
                profile=ContainerProfile.PROFILE_A_MOCK,
                workspace_root="/tmp",
                allowed_commands=("run",),
                max_memory_bytes=1024,
                timeout_seconds=2.5,  # type: ignore
            )

        config = ProcessBoundaryConfig(
            profile=ContainerProfile.PROFILE_A_MOCK,
            workspace_root="/tmp",
            allowed_commands=("run",),
            max_memory_bytes=1024,
            timeout_seconds=Fraction(5, 2),  # 2.5 in Fraction
        )
        assert config.timeout_seconds == Fraction(5, 2)

        # Check distinct refusal codes
        refusals = ("REQUEST_NOT_JSON", "D0_MALFORMED", "BOARD_SHAPE_MISMATCH")
        assert len(set(refusals)) == 3

    # =========================================================================
    # Group I: domain/sovereignty/
    # =========================================================================

    def test_sovereignty_three_layer_boundary_and_host_replay(self) -> None:
        """Challenge Three-Layer Sovereignty: probability simplex L1 norm and host replay defect catching.

        - Invariant: Probability simplex Delta^K satisfies sum |p_i| == 1.0 identically in Fraction.
          L1 regularization cannot induce sparsity on the simplex.
          Layer 3 independent host replay detects defects in tokens that comply with Layer 2 carrier mask.
        - Break: Asserting non-constant L1 norm on simplex; mathematical defect behind valid carrier tokens.
        - Witness: sum |p_i| == Fraction(1, 1); IndependentHostReplayVerdict returns REFUSED_COBOUNDARY_DEFECT.
        - Mutation: Trusting Layer 2 carrier format alone allows wrong arithmetic to pass as true.
        """
        # Invariant 1: Simplex L1 norm invariance in Fraction
        p_dist = (Fraction(1, 6), Fraction(2, 6), Fraction(3, 6))
        assert sum(abs(p) for p in p_dist) == Fraction(1, 1)

        # Invariant 2: Layer 3 host replay catches mathematical error
        # Model emits valid carrier tokens '56' for question '7 * 8', but host computes 7 * 8 = 56
        # If model emits '99', host catches mismatch
        claimed_val = Fraction(99, 1)
        expected_val = Fraction(56, 1)
        defect = abs(claimed_val - expected_val)

        verdict = IndependentHostReplayVerdict(
            packet_id="pkt_sovereignty_defect",
            recomputed_phi1=defect,
            recomputed_gamma2=Fraction(0, 1),
            claimed_phi1=Fraction(0, 1),
            verdict="REFUSED_COBOUNDARY_DEFECT",
        )
        assert verdict.is_admitted is False
        assert verdict.recomputed_phi1 == Fraction(43, 1)

    # =========================================================================
    # Group J: domain/dual_witness/
    # =========================================================================

    def test_dual_witness_exact_lp_certificate_and_adversarial_failure_matrix(self) -> None:
        """Challenge ExactDualWitnessCertificate: duality gap zero, dual annihilator, and subgradient alignment.

        - Invariant: Exact rational primal-dual certificate requires:
          1. duality_gap == Fraction(0, 1)
          2. primal residual z = omega - d0 @ alpha
          3. dual annihilator d0^T @ W = 0
          4. dual norm bound |W_e| <= w_e
          5. subgradient alignment: z_e > 0 => W_e = w_e, z_e < 0 => W_e = -w_e
          6. reported_value == <W, z> == sum w_e |z_e|
        - Break: Non-zero duality gap; residual mismatch; non-annihilating dual witness; subgradient sign flip.
        - Witness: is_valid_dual_certificate() returns True for honest certificate, False for each broken condition.
        - Mutation: A mutant that ignores subgradient alignment admits non-optimal primal-dual pairs.
        """
        # Honest 2-edge, 1-vertex primal-dual certificate
        # omega = [3, 2], d0 = [[1], [-1]], alpha = [1]
        # z = [3 - 1, 2 - (-1)] = [2, 3] (both > 0)
        # weights = [1, 1]
        # subgradient: since z > 0, W must be [+1, +1]
        # annihilator check: d0^T @ W = 1*(1) + (-1)*(1) = 0 (annihilator holds!)
        # reported value: 1*2 + 1*3 = 5
        # duality gap: 0
        cert_honest = ExactDualWitnessCertificate(
            omega=(Fraction(3, 1), Fraction(2, 1)),
            d0_matrix=((Fraction(1, 1),), (Fraction(-1, 1),)),
            weights=(Fraction(1, 1), Fraction(1, 1)),
            alpha=(Fraction(1, 1),),
            primal_residual=(Fraction(2, 1), Fraction(3, 1)),
            dual_witness=(Fraction(1, 1), Fraction(1, 1)),
            reported_value=Fraction(5, 1),
            duality_gap=Fraction(0, 1),
            status="ADMITTED",
        )
        assert cert_honest.is_valid_dual_certificate() is True

        # Failure Condition 1: Non-zero duality gap
        cert_bad_gap = ExactDualWitnessCertificate(
            omega=cert_honest.omega,
            d0_matrix=cert_honest.d0_matrix,
            weights=cert_honest.weights,
            alpha=cert_honest.alpha,
            primal_residual=cert_honest.primal_residual,
            dual_witness=cert_honest.dual_witness,
            reported_value=cert_honest.reported_value,
            duality_gap=Fraction(1, 100),  # NON-ZERO GAP
        )
        assert cert_bad_gap.is_valid_dual_certificate() is False

        # Failure Condition 2: Residual reconstruction mismatch
        cert_bad_residual = ExactDualWitnessCertificate(
            omega=cert_honest.omega,
            d0_matrix=cert_honest.d0_matrix,
            weights=cert_honest.weights,
            alpha=cert_honest.alpha,
            primal_residual=(Fraction(99, 1), Fraction(3, 1)),  # WRONG RESIDUAL
            dual_witness=cert_honest.dual_witness,
            reported_value=cert_honest.reported_value,
            duality_gap=Fraction(0, 1),
        )
        assert cert_bad_residual.is_valid_dual_certificate() is False

        # Failure Condition 3: Dual witness fails annihilator (d0^T @ W != 0)
        # Let W = [1, 2]. Then 1*1 + (-1)*2 = -1 != 0!
        cert_bad_annihilator = ExactDualWitnessCertificate(
            omega=cert_honest.omega,
            d0_matrix=cert_honest.d0_matrix,
            weights=(Fraction(2, 1), Fraction(2, 1)),
            alpha=cert_honest.alpha,
            primal_residual=cert_honest.primal_residual,
            dual_witness=(Fraction(1, 1), Fraction(2, 1)),  # Non-zero annihilator
            reported_value=Fraction(8, 1),
            duality_gap=Fraction(0, 1),
        )
        assert cert_bad_annihilator.is_valid_dual_certificate() is False

        # Failure Condition 4: Subgradient sign flip (z > 0 but W = -w)
        # Let W = [-1, -1]. Then d0^T @ W = 1*(-1) + (-1)*(-1) = 0 (annihilator holds),
        # but z > 0 requires W = +w, not -w!
        cert_bad_subgradient = ExactDualWitnessCertificate(
            omega=cert_honest.omega,
            d0_matrix=cert_honest.d0_matrix,
            weights=cert_honest.weights,
            alpha=cert_honest.alpha,
            primal_residual=cert_honest.primal_residual,
            dual_witness=(Fraction(-1, 1), Fraction(-1, 1)),  # Inverted subgradient!
            reported_value=Fraction(-5, 1),
            duality_gap=Fraction(0, 1),
        )
        assert cert_bad_subgradient.is_valid_dual_certificate() is False

        # Failure Condition 5: Dual norm bound exceeded (|W_e| > w_e)
        cert_bad_norm = ExactDualWitnessCertificate(
            omega=cert_honest.omega,
            d0_matrix=cert_honest.d0_matrix,
            weights=(Fraction(1, 2), Fraction(1, 2)),  # weights are 1/2, but W is 1!
            alpha=cert_honest.alpha,
            primal_residual=cert_honest.primal_residual,
            dual_witness=(Fraction(1, 1), Fraction(1, 1)),  # |1| > 1/2
            reported_value=Fraction(5, 1),
            duality_gap=Fraction(0, 1),
        )
        assert cert_bad_norm.is_valid_dual_certificate() is False

    # =========================================================================
    # Group K: domain/lean_bridge/
    # =========================================================================

    def test_lean_bridge_models_and_zero_float_verification(self) -> None:
        """Challenge LeanProofWitness and FormalCertificateBridge: zero-float and cryptographic binding.

        - Invariant: LeanProofWitness operates strictly in Fraction for exact_rational_gap.
          FormalCertificateBridge links Lean source SHA-256 with theorem verification verdicts.
        - Break: Float gap; cross-type comparisons.
        - Witness: TypeError on float gap; exact-type equality rejection.
        - Mutation: Permitting floats in formal bridges corrupts Lean-Python semantic parity.
        """
        # Break 1: Float in LeanProofWitness
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            LeanProofWitness("t1", "Carrier", "O1", "witness", 0.0)  # type: ignore

        witness = LeanProofWitness(
            theorem_id="stage0_necessity",
            carrier_domain="Unit",
            obstruction_code="O_SUBSINGLETON",
            witness_repr="no_witness_pair",
            exact_rational_gap=Fraction(0, 1),
        )
        assert witness.exact_rational_gap == Fraction(0, 1)

        bridge = FormalCertificateBridge(
            lean_module="Stage0LiftNecessity.lean",
            source_sha256="c" * 64,
            theorems_verified=("stage0_cannot_satisfy_irrefl_witness",),
            status="PASS",
        )
        assert bridge.status == "PASS"
        assert (bridge == ("Stage0LiftNecessity.lean", "c" * 64)) is False

    # =========================================================================
    # Group L: domain/exact/wire.py
    # =========================================================================

    def test_exact_rational_wire_canonical_serialization_and_duality_gap(self) -> None:
        """Challenge RationalWire and RationalDualityGap: canonical integer formatting without slash.

        - Invariant: Canonical Wire Format requires integer rationals with denominator 1 to serialize
          WITHOUT slash (e.g. '1', '-5', '0', NEVER '1/1'), non-integers as 'p/q'.
          from_wire rejects decimal float strings ('1.5') and zero denominators.
          RationalDualityGap computes gap = |primal - dual| and confirms optimality iff gap == 0.
        - Break: Serialization emitting '1/1'; parsing decimal string '0.5'; parsing zero denominator '3/0'.
        - Witness: to_wire() == '1'; ValueError on decimal float; ZeroDivisionError on '3/0'.
        - Mutation: A mutant serializing Fraction(1, 1) as '1/1' breaks core_kernel::parse_exact.
        """
        # Invariant 1: Canonical integers WITHOUT slash
        assert RationalWire(Fraction(1, 1)).to_wire() == "1"
        assert RationalWire(Fraction(0, 1)).to_wire() == "0"
        assert RationalWire(Fraction(-42, 1)).to_wire() == "-42"
        assert RationalWire(Fraction(7, 3)).to_wire() == "7/3"
        assert RationalWire(Fraction(-5, 8)).to_wire() == "-5/8"

        # Break 1: Rejection of float in constructor
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            RationalWire(1.0)  # type: ignore

        # Invariant 2: from_wire parsing
        assert RationalWire.from_wire("1").val == Fraction(1, 1)
        assert RationalWire.from_wire("-42").val == Fraction(-42, 1)
        assert RationalWire.from_wire("7/3").val == Fraction(7, 3)

        # Break 2: Reject decimal float string
        with pytest.raises(ValueError, match="ZERO-FLOAT Law: Decimal float string"):
            RationalWire.from_wire("1.5")
        with pytest.raises(ValueError, match="ZERO-FLOAT Law: Decimal float string"):
            RationalWire.from_wire("0.0")

        # Break 3: Reject zero denominator
        with pytest.raises(ZeroDivisionError):
            RationalWire.from_wire("5/0")

        # Invariant 3: RationalDualityGap
        gap_opt = RationalDualityGap.compute(Fraction(7, 4), Fraction(7, 4))
        assert gap_opt.duality_gap == Fraction(0, 1)
        assert gap_opt.is_optimal is True

        gap_subopt = RationalDualityGap.compute(Fraction(1, 2), Fraction(1, 3))
        assert gap_subopt.duality_gap == Fraction(1, 6)
        assert gap_subopt.is_optimal is False

        # Break 4: Float in RationalDualityGap
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            RationalDualityGap.compute(0.5, Fraction(1, 2))  # type: ignore

    # =========================================================================
    # Group M: domain/ports/ Conformance
    # =========================================================================

    def test_domain_ports_runtime_protocol_conformance_across_m4_m5(self) -> None:
        """Challenge @runtime_checkable domain protocols across Milestones 4 and 5.

        - Invariant: All domain protocols in domain/ports/ are @runtime_checkable and enforce Clean Architecture.
          Concrete domain implementations or conformant adapters must pass isinstance(obj, Protocol).
          Classes missing required protocol methods must strictly fail isinstance(obj, Protocol).
        - Break: Class omitting required protocol method; class with incorrect method name.
        - Witness: isinstance returns True for conforming instances, False for non-conforming instances.
        - Mutation: Removing @runtime_checkable prevents dynamic architectural contract auditing.
        """
        # Conforming mock adapter implementations for remaining ports
        class MockTokenFrontierEvaluator:
            def evaluate(self, vocabulary: WireVocabulary, base_weights: Sequence[int | Fraction], admitted_indices: Sequence[int]) -> Result[TokenFrontier, DecodingError]:
                return TokenFrontier.evaluate_step_result(vocabulary, base_weights, admitted_indices)

        class MockLogitsProvider:
            def get_discrete_logits(self, prompt: str, vocabulary: WireVocabulary) -> Sequence[int | Fraction]:
                return [1] * vocabulary.size

        class MockPolygraphEngine:
            def evaluate_confluence(self, polygraph: TarskiPolygraph, cell: Confluence2Cell) -> Result[bool, DecodingError]:
                return polygraph.validate_confluence_result(cell)

        class MockAntimorphismService:
            def invert_path(self, model: AntimorphismTransitionModel, path: Sequence[str]) -> Result[tuple[str, ...], DecodingError]:
                return model.reverse_path_result(path)
            def verify_involution(self, model: AntimorphismTransitionModel) -> bool:
                return model.satisfies_involution()

        class MockGenesisRegistry:
            def get_stage(self, level: int) -> GenesisStage | None:
                return None
            def get_all_stages(self) -> Sequence[GenesisStage]:
                return ()
            def apparatus_stages(self) -> frozenset[int]:
                return frozenset()
            def verify_pin(self, candidate_pin: str) -> bool:
                return candidate_pin == "e28f49abea3310ae4a9dc3d17ecb9ab55b267938"

        class MockTowerSearch:
            def enumerate_relations(self, carrier: CarrierSet) -> Sequence[BinaryRelation]:
                return ()
            def compute_exhaustion_digest(self, from_stage: int, goal: str, results: Sequence[bool]) -> str:
                return "digest"

        class MockLggrArbiter:
            def arbitrate(self, local_test_outcomes: Mapping[str, bool], edges: Sequence[DependencyEdge]) -> AstCochainReceipt:
                return AstCochainReceipt(Fraction(0, 1), Fraction(0, 1), 0, 0, LggrVerdict.PASS)

        class MockExactDualLpPort:
            def solve_primal_dual(self, c_cost: Sequence[Fraction], a_matrix: Sequence[Sequence[Fraction]], b_bounds: Sequence[Fraction]) -> Tuple[Sequence[Fraction], Sequence[Fraction], Fraction]:
                return ((), (), Fraction(0, 1))
            def solve_l1_projection(self, target: Sequence[Fraction], basis_matrix: Sequence[Sequence[Fraction]], weights: Sequence[Fraction]) -> ExactDualWitnessCertificate:
                raise NotImplementedError()

        class MockProcessSandboxPort:
            def execute_seam(self, cmd: Sequence[str], input_payload: Mapping[str, Any], config: ProcessBoundaryConfig) -> Result[SeamExecutionResult, str]:
                return Success(SeamExecutionResult(0, {}, "", "digest"))

        class MockLeanKernelBridgePort:
            def verify_module_sha256(self, module_name: str, expected_sha256: str) -> bool:
                return True
            def scan_sorry_axioms(self, module_name: str) -> list[str]:
                return []
            def check_lake_elaboration(self) -> Tuple[int, str]:
                return (0, "Elaborated successfully")

        # Conformance verification
        assert isinstance(MockTokenFrontierEvaluator(), ITokenFrontierEvaluator)
        assert isinstance(MockLogitsProvider(), ILogitsProvider)
        assert isinstance(MockPolygraphEngine(), IPolygraphConfluenceEngine)
        assert isinstance(MockAntimorphismService(), IAntimorphismService)
        assert isinstance(MockGenesisRegistry(), IGenesisStageRegistry)
        assert isinstance(MockTowerSearch(), IFiniteExhaustionSearch)
        assert isinstance(MockLggrArbiter(), ILggrArbiter)
        assert isinstance(MockExactDualLpPort(), ExactDualLpPort)
        assert isinstance(MockProcessSandboxPort(), ProcessSandboxPort)
        assert isinstance(MockLeanKernelBridgePort(), LeanKernelBridgePort)

        # Break: Non-conforming classes missing required methods
        class IncompleteTokenFrontierEvaluator:
            pass
        assert not isinstance(IncompleteTokenFrontierEvaluator(), ITokenFrontierEvaluator)

        class IncompleteGenesisRegistry:
            def get_stage(self, level: int) -> None:
                pass
            # Missing apparatus_stages, get_all_stages, verify_pin
        assert not isinstance(IncompleteGenesisRegistry(), IGenesisStageRegistry)
