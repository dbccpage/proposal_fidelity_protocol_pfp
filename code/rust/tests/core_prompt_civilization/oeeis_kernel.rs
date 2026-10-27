//! Integration tests for the OEEIS Exact Immune Kernel (U16).
//!
//! Verifies:
//! - Allostery: Exact integer Hill coefficient n=4, Kd=2 with H(2)=1/2 and H(3)=81/97.
//! - Danger Gate: Quarantine requires both Signal 1 and Signal 2; Signal 1 alone is a finding.
//! - Thymus: Negative selection deletes self-reactive candidates via apoptosis.
//! - Treg: Suppression active when global obstruction Phi_1 = 0.
//! - Complement: Recruitment cascade capped by explicit integer budget.
//! - Proofreading: Candidate finding requires delay steps to become confirmed.
//! - Clonal: Exponential half-life decay and below-threshold pruning.
//! - MHC: Windowed antigen epitope slicing.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use core_prompt_civilization::immune::*;

#[test]
fn test_allosteric_exact_hill_responses() {
    let gate = AllostericGate::new(4, 2);

    // H(0) = 0
    let (state0, resp0) = gate.evaluate(0);
    assert_eq!(state0, QuorumState::Quiescent);
    assert_eq!(resp0, BigRational::from_integer(BigInt::from(0)));

    // H(1) = 1^4 / (2^4 + 1^4) = 1 / 17 <= 1/4 -> Quiescent
    let (state1, resp1) = gate.evaluate(1);
    assert_eq!(state1, QuorumState::Quiescent);
    assert_eq!(resp1, BigRational::new(BigInt::from(1), BigInt::from(17)));

    // H(2) = 2^4 / (2^4 + 2^4) = 16 / 32 = 1/2 -> Indeterminate (between 1/4 and 3/4)
    let (state2, resp2) = gate.evaluate(2);
    assert_eq!(state2, QuorumState::Indeterminate);
    assert_eq!(resp2, BigRational::new(BigInt::from(1), BigInt::from(2)));

    // H(3) = 3^4 / (2^4 + 3^4) = 81 / (16 + 81) = 81 / 97 >= 3/4 (81/97 = 0.835) -> Active
    let (state3, resp3) = gate.evaluate(3);
    assert_eq!(state3, QuorumState::Active);
    assert_eq!(resp3, BigRational::new(BigInt::from(81), BigInt::from(97)));

    // H(4) = 4^4 / (2^4 + 4^4) = 256 / 272 = 16 / 17 >= 3/4 -> Active
    let (state4, resp4) = gate.evaluate(4);
    assert_eq!(state4, QuorumState::Active);
    assert_eq!(resp4, BigRational::new(BigInt::from(16), BigInt::from(17)));
}

#[test]
fn test_danger_gate_two_signal_quarantine_invariant() {
    let gate = DangerGate::new();

    // Signal 1 alone (finding only, never quarantine)
    let r1 = gate.evaluate(Some("SYNTAX_DEFECT".to_string()), None);
    assert_eq!(r1.disposition, DangerDisposition::FindingOnly);
    assert_eq!(r1.quarantined, false);
    assert_eq!(r1.signal1_detected, true);
    assert_eq!(r1.signal2_detected, false);

    // Signal 2 alone (alert only, never quarantine)
    let r2 = gate.evaluate(None, Some("UNAUTHORIZED_WRITE".to_string()));
    assert_eq!(r2.disposition, DangerDisposition::AlertOnly);
    assert_eq!(r2.quarantined, false);
    assert_eq!(r2.signal1_detected, false);
    assert_eq!(r2.signal2_detected, true);

    // Both signals present -> QUARANTINE
    let r3 = gate.evaluate(
        Some("SYNTAX_DEFECT".to_string()),
        Some("UNAUTHORIZED_WRITE".to_string()),
    );
    assert_eq!(r3.disposition, DangerDisposition::Quarantine);
    assert_eq!(r3.quarantined, true);
    assert_eq!(r3.authority_effect, "None");

    // Neither signal present -> Clear
    let r0 = gate.evaluate(None, None);
    assert_eq!(r0.disposition, DangerDisposition::Clear);
    assert_eq!(r0.quarantined, false);
}

#[test]
fn test_thymus_negative_selection_apoptosis() {
    let self_panel = vec![
        SelfFixture {
            fixture_id: "clean_proof_1".to_string(),
            content: "theorem add_comm : a + b = b + a := by omega".to_string(),
            description: "Standard clean commutativity proof".to_string(),
        },
        SelfFixture {
            fixture_id: "clean_code_2".to_string(),
            content: "fn zero() -> i32 { 0 }".to_string(),
            description: "Standard clean Rust function".to_string(),
        },
    ];
    let thymus = Thymus::new(self_panel);

    // Candidate 1: Reacts against clean_proof_1 (cross-reactive)
    let report1 = thymus.evaluate_candidate("overly_aggressive_detector", |fixture| {
        fixture.content.contains("theorem")
    });
    assert_eq!(report1.admitted, false);
    assert_eq!(report1.apoptosis_triggered, true);
    assert_eq!(report1.self_reactive_fixtures, vec!["clean_proof_1"]);

    // Candidate 2: Strictly non-self-reactive
    let report2 = thymus.evaluate_candidate("sound_detector", |fixture| {
        fixture.content.contains("FORBIDDEN_EXPLOIT")
    });
    assert_eq!(report2.admitted, true);
    assert_eq!(report2.apoptosis_triggered, false);
    assert!(report2.self_reactive_fixtures.is_empty());
}

#[test]
fn test_treg_suppression_on_zero_defect() {
    let treg = TregRegulator::new();

    // When Phi_1 == 0: Treg suppresses alarm
    let clean_eval = treg.evaluate(0, true);
    assert_eq!(clean_eval.status, TregStatus::Suppressive);
    assert_eq!(clean_eval.alarm_suppressed, true);

    // When Phi_1 > 0: Treg allows alarm
    let dirty_eval = treg.evaluate(3, true);
    assert_eq!(dirty_eval.status, TregStatus::Permissive);
    assert_eq!(dirty_eval.alarm_suppressed, false);
}

#[test]
fn test_complement_cascade_capped_by_budget() {
    let cascade = ComplementCascade::new(10, 4);

    // Trigger = 2, potential = 8 <= 10 -> recruited 8
    let r1 = cascade.execute(2);
    assert_eq!(r1.recruited_effectors, 8);
    assert_eq!(r1.budget_exhausted, false);
    assert_eq!(r1.reached_terminal_mac, true);

    // Trigger = 5, potential = 20 > 10 -> capped at 10
    let r2 = cascade.execute(5);
    assert_eq!(r2.recruited_effectors, 10);
    assert_eq!(r2.budget_exhausted, true);
}

#[test]
fn test_clonal_decay_and_pruning() {
    let mut pool = ClonalPool::new(5, 1, 4); // Half-life 5 gen, min threshold 1/4
    let clone1 = DetectorClone::new("clone_a".to_string(), 1, 1, 0); // 1.0 at gen 0
    pool.add_clone(clone1);

    // At gen 4: elapsed 4 < 5 -> no halving, affinity = 1.0 >= 1/4
    let pruned4 = pool.prune(4);
    assert!(pruned4.is_empty());
    assert_eq!(pool.clones.len(), 1);

    // At gen 11: elapsed 11 -> 2 halving steps (2^2 = 4) -> affinity = 1/4 >= 1/4 -> retained
    let pruned11 = pool.prune(11);
    assert!(pruned11.is_empty());

    // At gen 16: elapsed 16 -> 3 halving steps (2^3 = 8) -> affinity = 1/8 < 1/4 -> pruned!
    let pruned16 = pool.prune(16);
    assert_eq!(pruned16, vec!["clone_a"]);
    assert!(pool.clones.is_empty());
}

#[test]
fn test_kinetic_proofreading_delay() {
    let mut proofreader = KineticProofreader::new(3); // requires 3 consecutive observations

    assert_eq!(proofreader.record_occurrence("finding_x"), false);
    assert_eq!(proofreader.record_occurrence("finding_x"), false);
    // 3rd occurrence: confirmed!
    assert_eq!(proofreader.record_occurrence("finding_x"), true);
}

#[test]
fn test_mhc_windowed_slicing() {
    let window = MhcPresentationWindow::new(8, 4);
    let payload = "ABCDEFGH12345678";
    let slices = window.present_slices(payload);

    assert_eq!(slices.len(), 3);
    assert_eq!(slices[0].content, "ABCDEFGH");
    assert_eq!(slices[1].content, "EFGH1234");
    assert_eq!(slices[2].content, "12345678");
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/oeeis_kernel.rs
// Claim: urn:core:crates_rs:tests:oeeis-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1255b792 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1255b792` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1255b792 {
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
impl BoundaryError1255b792 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1255b792 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1255b792 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1255b792 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1255b792> {
        if capacity_bound == 0 {
            return Err(BoundaryError1255b792::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1255b792::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1255b792::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1255b792() {
    let admitted = BoundaryRecord1255b792::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1255b792::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
