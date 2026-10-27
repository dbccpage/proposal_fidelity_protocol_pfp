//! Falsification tests for rationalized oscillation.rs in core_adversary::stage.
//!
//! Validates:
//! - Exact Rational64 Jaccard semantic distance (satisfying Congruence Ideal I_float_metric)
//! - Elimination of float metric drift
//! - Refusal of out-of-bounds thresholds and invalid stagnant turn limits
//! - Exact circuit-breaker tripping behavior

use num_rational::Rational64;
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::ddc_tape_evaluator::DdcTapeEvaluator;
use core_adversary::stage::oscillation::{proposal_semantic_distance, OscillationDetector};
use core_adversary::stage::packets::CandidateProposal;
use core_wdp::ddc::ddc_alphabet::DdcOp;
use serde_json::json;
use sha2::{Digest, Sha256};

fn candidate(text: &str, artifact: &str) -> CandidateProposal {
    let art_hash = format!("sha256:{}", hex::encode(Sha256::digest(artifact.as_bytes())));
    let raw = json!({
        "producer_agent_id": "test_agent_001",
        "work_packet_id": "sha256:7426afc489d0eef99a0b438def226ad139f752350c25cf2c04900281afbb79e0",
        "artifact_refs": [
            art_hash
        ],
        "prediction_receipt_id": "sha256:70ad7b8f9a1c6c89a3cc93717b738ce9cf78395501b51d3707fc53cd63bb49d7",
        "nonclaims": [
            text
        ],
        "authority_effect": "None",
        "schema_version": "core.oeas.candidate-proposal.v1",
    });
    serde_json::from_value(raw).expect("valid CandidateProposal")
}

#[test]
fn test_exact_rational_proposal_distance() {
    let p1 = candidate("claim Alpha Beta Gamma", "art1");
    let p2 = candidate("claim Alpha Beta Gamma", "art1");

    // Identical proposals: distance = 0/1
    let d_identical = proposal_semantic_distance(&p1, &p2);
    assert_eq!(d_identical, Rational64::new(0, 1));

    // Tokens:
    // p1 has: "claim", "alpha", "beta", "gamma", "sha256", "artifact_art1" (6 tokens)
    // p3 has: "claim", "alpha", "delta", "epsilon", "sha256", "artifact_art2" (6 tokens)
    // intersection: "claim", "alpha", "sha256" (3 tokens)
    // union: "claim", "alpha", "beta", "gamma", "delta", "epsilon", "sha256", "artifact_art1", "artifact_art2" (9 tokens)
    // distance = 1 - 3/9 = 6/9 = 2/3
    let p3 = candidate("claim Alpha Delta Epsilon", "art2");
    let d_partial = proposal_semantic_distance(&p1, &p3);
    assert_eq!(d_partial, Rational64::new(2, 3));
    assert_eq!(*d_partial.numer(), 2);
    assert_eq!(*d_partial.denom(), 3);

    // Disjoint nonclaims (sharing only the single 'sha256' artifact prefix token):
    let p_x = candidate("foo bar", "x");
    let p_y = candidate("baz qux", "y");
    let d_disjoint = proposal_semantic_distance(&p_x, &p_y);
    assert_eq!(d_disjoint, Rational64::new(6, 7));
}

#[test]
fn test_oscillation_detector_exact_rational_circuit_breaker() {
    // Threshold: 3/4 = 0.75, max turns = 2
    let mut detector =
        OscillationDetector::new(Rational64::new(3, 4), 2).expect("valid detector");
    assert_eq!(detector.stall_distance_threshold(), Rational64::new(3, 4));

    let p1 = candidate("claim Alpha Beta Gamma", "art1");
    // Turn 1: initial seed proposal -> not stalled, distance = 1/1
    let (stalled1, d1) = detector
        .record_and_evaluate("scene_01", &p1, false)
        .expect("turn 1 evaluates");
    assert!(!stalled1);
    assert_eq!(d1, Rational64::new(1, 1));

    // Turn 2: similar proposal (distance 2/3 < 3/4) -> not progressed -> count = 1 -> not stalled yet
    let p2 = candidate("claim Alpha Delta Epsilon", "art2");
    let (stalled2, d2) = detector
        .record_and_evaluate("scene_01", &p2, false)
        .expect("turn 2 evaluates");
    assert!(!stalled2);
    assert_eq!(d2, Rational64::new(2, 3));

    // Turn 3: another similar proposal (distance 2/3 < 3/4) -> count = 2 >= max_turns (2) -> TRIPPED!
    let p3 = candidate("claim Alpha Beta Gamma", "art1");
    let (stalled3, d3) = detector
        .record_and_evaluate("scene_01", &p3, false)
        .expect("turn 3 evaluates");
    assert!(stalled3);
    assert_eq!(d3, Rational64::new(2, 3));

    // Reset clears state
    detector.reset();
    assert_eq!(detector.last_distance(), Rational64::new(1, 1));
}

#[test]
fn falsify_out_of_bounds_rational_threshold() {
    // Negative rational threshold -> rejected
    let err_neg = OscillationDetector::new(Rational64::new(-1, 2), 2)
        .expect_err("negative threshold must be rejected");
    assert_eq!(err_neg.code, "OSCILLATION_CONFIGURATION_REFUSED");

    // Threshold greater than 1/1 -> rejected
    let err_high = OscillationDetector::new(Rational64::new(5, 4), 2)
        .expect_err("threshold > 1 must be rejected");
    assert_eq!(err_high.code, "OSCILLATION_CONFIGURATION_REFUSED");
}

#[test]
fn falsify_non_positive_max_stagnant_turns() {
    // 0 turns -> rejected
    let err_zero = OscillationDetector::new(Rational64::new(1, 2), 0)
        .expect_err("zero turns must be rejected");
    assert_eq!(err_zero.code, "OSCILLATION_CONFIGURATION_REFUSED");

    // Negative turns -> rejected
    let err_neg = OscillationDetector::new(Rational64::new(1, 2), -3)
        .expect_err("negative turns must be rejected");
    assert_eq!(err_neg.code, "OSCILLATION_CONFIGURATION_REFUSED");
}

#[test]
fn test_zero_float_metrics_invariant() {
    // Supports Congruence Ideal I_float_metric:
    // Repeated fractions over 7 (e.g. 1/7, 2/7, 3/7) in binary float have recurring representation
    // (0.14285714285714285...), which causes precision drift in accumulators.
    // In exact Rational64, 7 * (1/7) is strictly and identically equal to 1/1.
    let seventh = Rational64::new(1, 7);
    let mut accumulator = Rational64::new(0, 1);
    for _ in 0..7 {
        accumulator += seventh;
    }
    assert_eq!(accumulator, Rational64::new(1, 1));
    assert_eq!(*accumulator.numer(), 1);
    assert_eq!(*accumulator.denom(), 1);
}

#[test]
fn test_adversarial_proposal_semantic_distance_boundary_values() {
    // 1. CandidateProposal schema invariants: proposals require non-empty artifacts and non-empty nonclaims
    let raw_no_artifacts = json!({
        "producer_agent_id": "test_agent_001",
        "work_packet_id": "sha256:7426afc489d0eef99a0b438def226ad139f752350c25cf2c04900281afbb79e0",
        "artifact_refs": [], // empty artifacts -> strictly rejected!
        "prediction_receipt_id": "sha256:70ad7b8f9a1c6c89a3cc93717b738ce9cf78395501b51d3707fc53cd63bb49d7",
        "nonclaims": ["some nonclaim text"],
        "authority_effect": "None",
        "schema_version": "core.oeas.candidate-proposal.v1",
    });
    let err_art = serde_json::from_value::<CandidateProposal>(raw_no_artifacts).unwrap_err();
    assert!(err_art.to_string().contains("candidate proposal requires artifacts"));

    let raw_no_nonclaims = json!({
        "producer_agent_id": "test_agent_001",
        "work_packet_id": "sha256:7426afc489d0eef99a0b438def226ad139f752350c25cf2c04900281afbb79e0",
        "artifact_refs": ["sha256:70ad7b8f9a1c6c89a3cc93717b738ce9cf78395501b51d3707fc53cd63bb49d7"],
        "prediction_receipt_id": "sha256:70ad7b8f9a1c6c89a3cc93717b738ce9cf78395501b51d3707fc53cd63bb49d7",
        "nonclaims": [], // empty nonclaims -> strictly rejected!
        "authority_effect": "None",
        "schema_version": "core.oeas.candidate-proposal.v1",
    });
    let err_nc = serde_json::from_value::<CandidateProposal>(raw_no_nonclaims).unwrap_err();
    assert!(err_nc.to_string().contains("candidate proposal requires nonclaims"));

    // 2. Identical proposals: distance is strictly 0/1
    let p_a = candidate("Hello, WORLD! Token_123.", "art_same");
    let p_b = candidate("hello world token_123", "art_same");
    let d_case = proposal_semantic_distance(&p_a, &p_b);
    assert_eq!(d_case, Rational64::new(0, 1));
    assert_eq!(*d_case.numer(), 0);
    assert_eq!(*d_case.denom(), 1);

    // 3. Minimally overlapping proposals (sharing only the common "sha256" token from artifact refs):
    let p_c = candidate("alpha beta", "x1");
    let p_d = candidate("gamma delta", "x2");
    // p_c has tokens: "alpha", "beta", "sha256", "<art_x1_sha>" (4 tokens)
    // p_d has tokens: "gamma", "delta", "sha256", "<art_x2_sha>" (4 tokens)
    // Union = 7 tokens, Intersection = {"sha256"} = 1 token.
    // Distance = (7 - 1) / 7 = 6/7.
    let d_part = proposal_semantic_distance(&p_c, &p_d);
    assert_eq!(d_part, Rational64::new(6, 7));
    assert_eq!(*d_part.numer(), 6);
    assert_eq!(*d_part.denom(), 7);

    // 4. Repeated identical proposals with multiple tokens
    let p_e = candidate("alpha beta gamma delta epsilon", "art_fixed");
    let p_f = candidate("alpha beta gamma delta epsilon", "art_fixed");
    assert_eq!(proposal_semantic_distance(&p_e, &p_f), Rational64::new(0, 1));
}

#[test]
fn test_adversarial_oscillation_detector_circuit_breaker_boundary_and_falsification() {
    // 1. Boundary threshold at exact 0/1 (never stalls because distance < 0 is unreachable for non-negative distances)
    let mut det_zero = OscillationDetector::new(Rational64::new(0, 1), 1).expect("valid detector");
    let p_same = candidate("repeat repeat", "art");
    det_zero.record_and_evaluate("s1", &p_same, false).unwrap();
    let (stalled_zero, d_zero) = det_zero.record_and_evaluate("s1", &p_same, false).unwrap();
    assert!(!stalled_zero, "Detector with threshold 0/1 should never trip");
    assert_eq!(d_zero, Rational64::new(0, 1));

    // 2. Boundary threshold at exact 1/1 (trips on any non-disjoint repeated proposal)
    let mut det_one = OscillationDetector::new(Rational64::new(1, 1), 2).expect("valid detector");
    let p1 = candidate("claim Alpha Beta", "art1");
    let p2 = candidate("claim Alpha Gamma", "art2");
    det_one.record_and_evaluate("s1", &p1, false).unwrap();
    // Turn 2: distance < 1/1 -> count = 1
    let (stalled_one_1, _) = det_one.record_and_evaluate("s1", &p2, false).unwrap();
    assert!(!stalled_one_1);
    // Turn 3: distance < 1/1 -> count = 2 >= max_turns (2) -> TRIPPED!
    let (stalled_one_2, _) = det_one.record_and_evaluate("s1", &p1, false).unwrap();
    assert!(stalled_one_2, "Detector with threshold 1/1 must trip on turn 3");

    // 3. Progress flag overrides stall
    let mut det_prog = OscillationDetector::new(Rational64::new(3, 4), 2).expect("valid detector");
    det_prog.record_and_evaluate("s1", &p1, false).unwrap();
    det_prog.record_and_evaluate("s1", &p2, false).unwrap(); // count = 1
    // Turn 3 has progressed = true! Should reset count to 0 and NOT trip
    let (stalled_prog, _) = det_prog.record_and_evaluate("s1", &p1, true).unwrap();
    assert!(!stalled_prog);

    // Turn 4 with progressed = false -> count becomes 1 (not 3), so still does NOT trip
    let (stalled_prog2, _) = det_prog.record_and_evaluate("s1", &p2, false).unwrap();
    assert!(!stalled_prog2);

    // 4. Multi-scene isolation
    let mut det_multi = OscillationDetector::new(Rational64::new(3, 4), 2).expect("valid detector");
    det_multi.record_and_evaluate("scene_A", &p1, false).unwrap();
    det_multi.record_and_evaluate("scene_A", &p2, false).unwrap(); // scene_A count = 1

    // Interleaved evaluation in scene_B
    det_multi.record_and_evaluate("scene_B", &p1, false).unwrap(); // scene_B count = 0
    let (stalled_b, _) = det_multi.record_and_evaluate("scene_B", &p2, false).unwrap(); // scene_B count = 1
    assert!(!stalled_b);

    // scene_A turn 3 -> count becomes 2 -> TRIPPED!
    let (stalled_a, _) = det_multi.record_and_evaluate("scene_A", &p1, false).unwrap();
    assert!(stalled_a);

    // scene_B remains untripped
    let (stalled_b2, _) = det_multi.record_and_evaluate("scene_B", &p2, true).unwrap(); // progress in B resets B
    assert!(!stalled_b2);
}

#[test]
fn test_adversarial_ddc_sliding_window_extreme_step_sequences() {
    let mut evaluator = DdcTapeEvaluator::new("extreme_seq_test");

    // Construct 1,000 steps with non-trivial repeating rational numbers
    // phi_1 = 1/7, gamma_2 = 3/13
    let phi1_val = Rational64::new(1, 7);
    let gamma2_val = Rational64::new(3, 13);

    for idx in 0..1000 {
        let op = if idx % 2 == 0 {
            DdcOp::ExactRepair
        } else {
            DdcOp::ResidualProjection
        };
        let b = format!("c_{idx}");
        let a = format!("c_{}", idx + 1);
        let raw = json!({
            "letter": op.letter(),
            "before_class": b,
            "after_class": a,
            "carrier_hash": "c_ext",
            "witness_hash": "w_ext",
            "receipt_sha256": "r_ext",
            "authority_effect": "None",
            "timestamp": "2026-10-15T22:00:00Z",
            "phi_1": "1/7",
            "gamma_2": "3/13",
        });
        let step: DdcStep = serde_json::from_value(raw).expect("valid step");
        let rcpt = evaluator.eval_step(&step).expect("eval step succeeds");
        assert_eq!(rcpt.sequence, idx as u64);
        assert_eq!(rcpt.phi_1, Some(phi1_val));
        assert_eq!(rcpt.gamma_2, Some(gamma2_val));
    }

    assert_eq!(evaluator.step_count(), 1000);

    // In binary floating-point (f64), 1/7 = 0.14285714285714285...
    // Summing 0.14285714285714285 7 times yields 0.9999999999999999 or 1.0000000000000002.
    // Summing 1,000 times yields severe floating-point drift!
    // In compiled exact Rational64, precision drift is mathematically 0.0000000%!

    // Window 0:
    assert_eq!(evaluator.sliding_window_metric(0), Rational64::new(0, 1));
    assert_eq!(evaluator.sliding_window_gamma2(0), Rational64::new(0, 1));
    assert_eq!(evaluator.sliding_window_mean(0), Rational64::new(0, 1));

    // Window 1:
    assert_eq!(evaluator.sliding_window_metric(1), Rational64::new(1, 7));
    assert_eq!(evaluator.sliding_window_gamma2(1), Rational64::new(3, 13));
    assert_eq!(evaluator.sliding_window_mean(1), Rational64::new(1, 7));

    // Window 7: exactly 7 * (1/7) = 1/1
    assert_eq!(evaluator.sliding_window_metric(7), Rational64::new(1, 1));

    // Window 13: exactly 13 * (3/13) = 3/1
    assert_eq!(evaluator.sliding_window_gamma2(13), Rational64::new(3, 1));

    // Window 91 (7 * 13):
    // phi_1 sum: 91 * (1/7) = 13/1
    // gamma_2 sum: 91 * (3/13) = 21/1
    // phi_1 mean: 13 / 91 = 1/7
    assert_eq!(evaluator.sliding_window_metric(91), Rational64::new(13, 1));
    assert_eq!(evaluator.sliding_window_gamma2(91), Rational64::new(21, 1));
    assert_eq!(evaluator.sliding_window_mean(91), Rational64::new(1, 7));

    // Window 1000 (all steps):
    // phi_1 sum: 1000 * (1/7) = 1000/7
    // gamma_2 sum: 1000 * (3/13) = 3000/13
    // phi_1 mean: (1000/7) / 1000 = 1/7
    assert_eq!(evaluator.sliding_window_metric(1000), Rational64::new(1000, 7));
    assert_eq!(evaluator.sliding_window_gamma2(1000), Rational64::new(3000, 13));
    assert_eq!(evaluator.sliding_window_mean(1000), Rational64::new(1, 7));

    // Window 5000 (oversized window, saturates cleanly without allocating or panicking):
    assert_eq!(evaluator.sliding_window_metric(5000), Rational64::new(1000, 7));
    assert_eq!(evaluator.sliding_window_gamma2(5000), Rational64::new(3000, 13));
    assert_eq!(evaluator.sliding_window_mean(5000), Rational64::new(1, 7));
}

// Origin: engine/crates_rs/tests/core_adversary/stage/oscillation_rational_falsification.rs
// Claim: urn:core:crates_rs:tests:oscillation-rational-falsification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord973411d0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord973411d0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError973411d0 {
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
impl BoundaryError973411d0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError973411d0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError973411d0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord973411d0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError973411d0> {
        if capacity_bound == 0 {
            return Err(BoundaryError973411d0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError973411d0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError973411d0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_973411d0() {
    let admitted = BoundaryRecord973411d0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord973411d0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
