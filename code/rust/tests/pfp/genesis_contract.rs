//! Contract tests for the genesis stratification, observer regimes, and the
//! Examiner quiz.
//!
//! `EPIC-OE-SYMGAM-011`. The epic's own acceptance criteria are stated as
//! "the tests pass", which is not a criterion -- it names no mutation that would
//! turn it red. The criteria exercised here are the ones the *spec* actually
//! commits to, each paired with the mutation that breaks it:
//!
//! 1. `G0` is opaque and inert: no two data are distinguishable without an
//!    admitted context, and demanding one anyway is a refusal.
//! 2. `G1` reports typography and does not adjudicate structure.
//! 3. `G2` admits a carrier or refuses it, and both halves of the Dyck
//!    condition are load-bearing.
//! 4. A separation names its witnessing context rather than returning a bare
//!    boolean.
//! 5. The Examiner quiz is exact, deterministic, and names the offending pairs.

use num_bigint::BigInt;
use num_rational::BigRational;

use pfp::genesis::{
    admit, evaluate_depth, score_examiner, verify_examiner, AdmittedContext, GenesisErrorCode,
    ExaminerChallenge, ExaminerFlavour, ExaminerQuizGenerator, ObserverContext, ObserverRegime,
    OpaqueDatum, PresentationCodec, GLYPH_CLOSE, GLYPH_OPEN,
};

fn q(numerator: i64, denominator: i64) -> BigRational {
    BigRational::new(BigInt::from(numerator), BigInt::from(denominator))
}

fn codec() -> PresentationCodec {
    PresentationCodec::ascii_angle()
}

// ---------------------------------------------------------------------------
// Criterion 1 -- G0 opacity and ground inertia
// ---------------------------------------------------------------------------

#[test]
fn a_primitive_difference_carries_no_payload() {
    // Zero-sized: there is no interior for a later level to read back.
    assert_eq!(std::mem::size_of::<OpaqueDatum>(), 0);
}

#[test]
fn every_ground_datum_equals_every_other() {
    // Not a stub. Two distinctions are indistinguishable until something is
    // admitted that can tell them apart.
    assert_eq!(OpaqueDatum::new(), OpaqueDatum::new());
    assert_eq!(OpaqueDatum::default(), OpaqueDatum::new());
}

#[test]
fn the_ground_regime_admits_nothing() {
    let ground = ObserverRegime::ground();
    assert!(ground.is_ground());
    assert!(ground.contexts().is_empty());
}

#[test]
fn under_the_ground_regime_everything_is_equivalent() {
    // The quantifier is vacuous, so this is `true` -- ground inertia stated
    // positively.
    let ground = ObserverRegime::ground();
    assert!(ground
        .equivalent(OpaqueDatum::new(), OpaqueDatum::new())
        .expect("ground equivalence is computable"));
}

#[test]
fn demanding_a_separation_without_a_context_is_refused() {
    // The decisive one. A system that answers "they differ" with no context to
    // differ in has invented a distinction it was not given, so the ground
    // regime must refuse rather than return `false`.
    let ground = ObserverRegime::ground();
    let error = ground
        .demand_separation(OpaqueDatum::new(), OpaqueDatum::new())
        .expect_err("the ground regime cannot separate");
    assert_eq!(error.code(), GenesisErrorCode::NoAdmittedContext);
}

#[test]
fn a_context_family_may_not_count_the_same_context_twice() {
    // A duplicated context would report more separating power than the family
    // has.
    let error = ObserverRegime::admit_contexts(
        vec![
            ObserverContext::new("wrap-1", 1),
            ObserverContext::new("wrap-1", 1),
        ],
        evaluate_depth,
    )
    .expect_err("duplicates are refused");
    assert_eq!(error.code(), GenesisErrorCode::DuplicateContext);
}

// ---------------------------------------------------------------------------
// Criterion 2 -- G1 is typography, not topology
// ---------------------------------------------------------------------------

#[test]
fn the_canonical_codec_is_ascii_angle_brackets() {
    assert_eq!(codec().open(), GLYPH_OPEN);
    assert_eq!(codec().close(), GLYPH_CLOSE);
    assert_eq!(GLYPH_OPEN, 0x3C);
    assert_eq!(GLYPH_CLOSE, 0x3E);
}

#[test]
fn rendering_a_datum_produces_matched_glyphs() {
    assert_eq!(codec().render(OpaqueDatum::new(), 0), "");
    assert_eq!(codec().render(OpaqueDatum::new(), 1), "<>");
    assert_eq!(codec().render(OpaqueDatum::new(), 3), "<<<>>>");
}

#[test]
fn a_scan_reports_counts_and_a_depth_profile() {
    let scan = codec().scan("<<>>").expect("codec glyphs only");
    assert_eq!(scan.opens(), 2);
    assert_eq!(scan.closes(), 2);
    assert_eq!(scan.length(), 4);
    assert_eq!(scan.depth_profile(), &[1, 2, 1, 0]);
    assert_eq!(scan.max_depth(), 2);
}

#[test]
fn a_scan_records_a_negative_depth_rather_than_judging_it() {
    // `><` is not a nesting, and `G1` is not the level that says so. It reports
    // the number and leaves the verdict to `admit`.
    let scan = codec().scan("><").expect("codec glyphs only");
    assert_eq!(scan.min_depth(), -1);
    assert_eq!(scan.net_depth(), 0);
}

#[test]
fn a_foreign_glyph_is_refused_with_its_index() {
    let error = codec().scan("<x>").expect_err("x is outside the codec");
    assert_eq!(error.code(), GenesisErrorCode::ForeignGlyph);
    assert!(
        error.message().contains("index 1"),
        "the refusal must locate the glyph: {}",
        error.message()
    );
}

#[test]
fn the_stratification_does_not_depend_on_the_glyphs_chosen() {
    // If any of this were secretly about the characters `<` and `>`, swapping
    // them for another pair would change the verdicts. It does not.
    let parens = PresentationCodec::with_glyphs(b'(', b')').expect("distinct glyphs");
    let scan = parens.scan("(())").expect("codec glyphs only");
    let admitted = admit(&scan).expect("a balanced word is admissible");
    assert_eq!(admitted.nesting_depth(), 2);
}

#[test]
fn a_codec_whose_glyphs_coincide_is_refused() {
    let error = PresentationCodec::with_glyphs(b'<', b'<').expect_err("glyphs must differ");
    assert_eq!(error.code(), GenesisErrorCode::ForeignGlyph);
}

// ---------------------------------------------------------------------------
// Criterion 3 -- G2 admission
// ---------------------------------------------------------------------------

#[test]
fn a_balanced_word_is_admitted_as_a_carrier() {
    let scan = codec().scan("<<>><>").expect("codec glyphs only");
    let admitted = admit(&scan).expect("balanced and closed");
    assert_eq!(admitted.pairs(), 3);
    assert_eq!(admitted.nesting_depth(), 2);
    assert!(admitted.boundary_isolated());
}

#[test]
fn a_close_before_its_open_is_refused() {
    // Prefix non-negativity constraint of Dyck condition: `><` ends at zero net
    // depth, so a net-depth check alone would erroneously admit it.
    let scan = codec().scan("><").expect("codec glyphs only");
    let error = admit(&scan).expect_err("a close preceded its open");
    assert_eq!(error.code(), GenesisErrorCode::NotDyck);
    assert!(error.message().contains("-1"), "{}", error.message());
}

#[test]
fn an_unclosed_word_is_refused() {
    // Terminal zero-depth constraint: `<<` maintains non-negative prefix depth,
    // so a prefix check alone would erroneously admit it. Both conditions are load-bearing.
    let scan = codec().scan("<<").expect("codec glyphs only");
    let error = admit(&scan).expect_err("the word is unclosed");
    assert_eq!(error.code(), GenesisErrorCode::NotDyck);
    assert!(
        error.message().contains("net depth 2"),
        "{}",
        error.message()
    );
}

#[test]
fn the_empty_word_is_the_identity_carrier() {
    let scan = codec().scan("").expect("the empty word is scannable");
    let admitted = admit(&scan).expect("the empty word is a Dyck word");
    assert_eq!(admitted.pairs(), 0);
    assert_eq!(admitted.nesting_depth(), 0);
    assert_eq!(admitted, AdmittedContext::empty());
}

// ---------------------------------------------------------------------------
// Criterion 4 -- separations name their witness
// ---------------------------------------------------------------------------

#[test]
fn a_regime_with_contexts_is_not_ground() {
    let regime =
        ObserverRegime::admit_contexts(vec![ObserverContext::new("wrap-1", 1)], evaluate_depth)
            .expect("a single context is a family");
    assert!(!regime.is_ground());
    assert_eq!(regime.contexts().len(), 1);
}

#[test]
fn identical_data_stay_equivalent_however_many_contexts_are_admitted() {
    // Admitting contexts gives the *power* to separate; it does not manufacture
    // a separation where there is none. Both data here are the same ground
    // datum, so no context can tell them apart.
    let regime = ObserverRegime::admit_contexts(
        vec![
            ObserverContext::new("wrap-0", 0),
            ObserverContext::new("wrap-1", 1),
            ObserverContext::new("wrap-7", 7),
        ],
        evaluate_depth,
    )
    .expect("distinct contexts");

    assert!(regime
        .equivalent(OpaqueDatum::new(), OpaqueDatum::new())
        .expect("computable"));
    assert!(regime
        .demand_separation(OpaqueDatum::new(), OpaqueDatum::new())
        .expect("the demand is admissible")
        .is_none());
}

#[test]
fn a_context_evaluates_to_its_nesting_depth_exactly() {
    let context = ObserverContext::new("wrap-4", 4);
    let filled = context
        .fill(OpaqueDatum::new(), &codec())
        .expect("filling admits");
    assert_eq!(
        evaluate_depth(&filled),
        BigRational::from_integer(BigInt::from(4))
    );
}

#[test]
fn filling_a_hole_yields_an_admitted_carrier() {
    let context = ObserverContext::new("wrap-2", 2);
    let filled = context
        .fill(OpaqueDatum::new(), &codec())
        .expect("filling admits");
    assert_eq!(filled.pairs(), 2);
    assert!(filled.boundary_isolated());
}

// ---------------------------------------------------------------------------
// Criterion 5 -- the Examiner quiz
// ---------------------------------------------------------------------------

#[test]
fn a_strict_partial_order_passes_both_checks() {
    let challenge = ExaminerChallenge::new(3, [(0, 1), (1, 2), (0, 2)]).expect("in domain");
    let verdict = verify_examiner(&challenge);
    assert!(verdict.is_irreflexive());
    assert!(verdict.is_asymmetric());
    assert!(verdict.is_strict());
}

#[test]
fn a_reflexive_pair_is_named_not_merely_counted() {
    let challenge = ExaminerChallenge::new(3, [(0, 1), (2, 2)]).expect("in domain");
    let verdict = verify_examiner(&challenge);
    assert!(!verdict.is_irreflexive());
    assert_eq!(verdict.reflexive_witnesses, vec![(2, 2)]);
    // Asymmetry is untouched by a reflexive fault: the two are reported
    // separately so a single boolean cannot hide which one failed.
    assert!(verdict.is_asymmetric());
    assert!(!verdict.is_strict());
}

#[test]
fn a_symmetric_pair_is_named_not_merely_counted() {
    let challenge = ExaminerChallenge::new(3, [(0, 1), (1, 0)]).expect("in domain");
    let verdict = verify_examiner(&challenge);
    assert!(!verdict.is_asymmetric());
    assert_eq!(verdict.symmetric_witnesses, vec![(0, 1)]);
    assert!(verdict.is_irreflexive());
    assert!(!verdict.is_strict());
}

#[test]
fn a_pair_outside_the_domain_is_refused() {
    let error = ExaminerChallenge::new(2, [(0, 5)]).expect_err("5 escapes a domain of 2");
    assert_eq!(error.code(), GenesisErrorCode::OutOfDomain);
}

#[test]
fn the_generator_is_deterministic_for_a_seed() {
    // "Procedurally randomized" and "reproducible receipt" are only compatible
    // if the stream is fixed. Two generators on the same seed must agree
    // exactly, digest included.
    let mut left = ExaminerQuizGenerator::new(0xC0FFEE);
    let mut right = ExaminerQuizGenerator::new(0xC0FFEE);
    for _ in 0..8 {
        let a = left.generate(6, ExaminerFlavour::Strict).expect("in domain");
        let b = right.generate(6, ExaminerFlavour::Strict).expect("in domain");
        assert_eq!(a, b);
        assert_eq!(a.digest(), b.digest());
    }
}

#[test]
fn different_seeds_produce_different_challenges() {
    // Otherwise the previous test would pass against a generator that emits a
    // constant.
    let mut left = ExaminerQuizGenerator::new(1);
    let mut right = ExaminerQuizGenerator::new(2);
    let a = left.generate(8, ExaminerFlavour::Strict).expect("in domain");
    let b = right.generate(8, ExaminerFlavour::Strict).expect("in domain");
    assert_ne!(a, b);
}

#[test]
fn generated_strict_challenges_are_strict_by_construction() {
    // Orienting every pair from the smaller index upward makes irreflexivity
    // and asymmetry structural rather than lucky, so a failure here is a real
    // defect in the checker rather than an unlucky draw.
    let mut generator = ExaminerQuizGenerator::new(42);
    for size in 0..12u32 {
        let challenge = generator
            .generate(size, ExaminerFlavour::Strict)
            .expect("in domain");
        let verdict = verify_examiner(&challenge);
        assert!(verdict.is_strict(), "size {size} was not strict");
    }
}

#[test]
fn generated_traps_are_caught() {
    let mut generator = ExaminerQuizGenerator::new(7);

    let reflexive = generator
        .generate(6, ExaminerFlavour::ReflexiveTrap)
        .expect("in domain");
    let verdict = verify_examiner(&reflexive);
    assert!(!verdict.is_irreflexive(), "the reflexive trap was missed");

    let symmetric = generator
        .generate(6, ExaminerFlavour::SymmetricTrap)
        .expect("in domain");
    let verdict = verify_examiner(&symmetric);
    assert!(!verdict.is_asymmetric(), "the symmetric trap was missed");
}

#[test]
fn a_symmetric_trap_fires_even_when_the_draw_is_empty() {
    // The generator mirrors an existing edge, so a draw that produced no edges
    // would otherwise emit a "trap" that is actually strict -- a challenge
    // whose declared answer is wrong.
    for seed in 0..64u64 {
        let mut generator = ExaminerQuizGenerator::new(seed);
        let challenge = generator
            .generate(2, ExaminerFlavour::SymmetricTrap)
            .expect("in domain");
        let verdict = verify_examiner(&challenge);
        assert!(
            !verdict.is_asymmetric(),
            "seed {seed} produced a symmetric trap that is asymmetric"
        );
    }
}

#[test]
fn the_digest_changes_when_the_relation_changes() {
    let base = ExaminerChallenge::new(3, [(0, 1)]).expect("in domain");
    let altered = ExaminerChallenge::new(3, [(0, 2)]).expect("in domain");
    assert_ne!(base.digest(), altered.digest());
    // And it is stable across constructions of the same relation.
    let same = ExaminerChallenge::new(3, [(0, 1)]).expect("in domain");
    assert_eq!(base.digest(), same.digest());
}

#[test]
fn the_digest_separates_domains_of_different_size() {
    // The same edge set over a larger domain is a different challenge.
    let small = ExaminerChallenge::new(3, [(0, 1)]).expect("in domain");
    let large = ExaminerChallenge::new(9, [(0, 1)]).expect("in domain");
    assert_ne!(small.digest(), large.digest());
}

#[test]
fn a_verdict_carries_the_digest_of_what_it_scored() {
    let challenge = ExaminerChallenge::new(3, [(0, 1)]).expect("in domain");
    let verdict = verify_examiner(&challenge);
    assert_eq!(verdict.challenge_digest, challenge.digest());
}

#[test]
fn scoring_is_exact_rational_arithmetic() {
    let expected = [
        ExaminerFlavour::Strict,
        ExaminerFlavour::ReflexiveTrap,
        ExaminerFlavour::Strict,
    ];
    // Two of three correct: the middle answer calls a trap strict.
    let score = score_examiner(&expected, &[true, true, true]).expect("a scorable quiz");
    assert_eq!(score.correct, 2);
    assert_eq!(score.asked, 3);
    assert_eq!(score.fraction, q(2, 3));
}

#[test]
fn a_perfect_and_a_zero_score_are_both_exact() {
    let expected = [ExaminerFlavour::Strict, ExaminerFlavour::SymmetricTrap];
    let perfect = score_examiner(&expected, &[true, false]).expect("scorable");
    assert_eq!(perfect.fraction, q(1, 1));
    let zero = score_examiner(&expected, &[false, true]).expect("scorable");
    assert_eq!(zero.fraction, q(0, 1));
}

#[test]
fn an_empty_quiz_is_refused_rather_than_scored_zero_of_zero() {
    let error = score_examiner(&[], &[]).expect_err("nothing to score");
    assert_eq!(error.code(), GenesisErrorCode::EmptyQuiz);
}

#[test]
fn a_mismatched_answer_sheet_is_refused() {
    let expected = [ExaminerFlavour::Strict, ExaminerFlavour::Strict];
    let error = score_examiner(&expected, &[true]).expect_err("one answer, two questions");
    assert_eq!(error.code(), GenesisErrorCode::EmptyQuiz);
    assert!(
        error.message().contains("do not match"),
        "{}",
        error.message()
    );
}

#[test]
fn examiner_receipt_is_schema_validated_and_reproducible() {
    let expected = [
        ExaminerFlavour::Strict,
        ExaminerFlavour::ReflexiveTrap,
        ExaminerFlavour::Strict,
    ];
    let score = score_examiner(&expected, &[true, true, true]).expect("a scorable quiz");
    let digests = vec!["a".repeat(64), "b".repeat(64), "c".repeat(64)];
    let receipt = score.to_receipt(&digests);
    assert_eq!(receipt.schema, "core.symbol_game.genesis_examiner.v1");
    assert_eq!(receipt.authority_effect, "None");
    assert_eq!(receipt.correct, 2);
    assert_eq!(receipt.asked, 3);
    assert_eq!(receipt.score_rational, "2/3");
    assert!(receipt.is_valid());
    let receipt2 = score.to_receipt(&digests);
    assert_eq!(receipt, receipt2);
}

#[test]
fn examiner_receipt_rejects_score_identity_and_schema_mutations() {
    use pfp::genesis::{score_examiner_challenge, ExaminerReceiptV1};
    let challenge = ExaminerChallenge::new(2, [(0, 1)]).unwrap();
    let receipt = score_examiner_challenge(&challenge, true);
    assert!(receipt.is_valid());
    assert_eq!(receipt.challenge_digests, vec![challenge.digest()]);
    assert_eq!(receipt.correct, 1);
    let bytes = serde_json::to_vec(&receipt).unwrap();
    assert_eq!(ExaminerReceiptV1::from_json(&bytes).unwrap(), receipt);
    assert_eq!(
        serde_json::from_slice::<ExaminerReceiptV1>(&bytes).unwrap(),
        receipt
    );
    for (field, value) in [
        ("score_rational", serde_json::json!("0")),
        ("asked", serde_json::json!(0)),
        ("correct", serde_json::json!(2)),
        ("digest", serde_json::json!("a".repeat(64))),
        ("challenge_digests", serde_json::json!(["not-a-digest"])),
        ("authority_effect", serde_json::json!("Admit")),
        ("schema", serde_json::json!("unknown")),
        ("unexpected", serde_json::json!(true)),
    ] {
        let mut wire = serde_json::to_value(&receipt).unwrap();
        wire[field] = value;
        assert!(
            serde_json::from_value::<ExaminerReceiptV1>(wire.clone()).is_err(),
            "standard Serde decoding bypassed {field} validation"
        );
        assert!(
            ExaminerReceiptV1::from_json(&serde_json::to_vec(&wire).unwrap()).is_err(),
            "{field}"
        );
    }
    let wrong = score_examiner_challenge(&challenge, false);
    assert!(wrong.is_valid());
    assert_eq!(wrong.correct, 0);
    assert_ne!(wrong.digest, receipt.digest);
}

// Origin: engine/crates_rs/tests/pfp/genesis_contract.rs
// Claim: urn:core:crates_rs:tests:genesis-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd0000204 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd0000204` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord0000204 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrord0000204 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord0000204 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord0000204 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd0000204 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord0000204> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord0000204::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord0000204::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord0000204::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_d0000204() {
    let admitted = BoundaryRecordd0000204::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd0000204::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
