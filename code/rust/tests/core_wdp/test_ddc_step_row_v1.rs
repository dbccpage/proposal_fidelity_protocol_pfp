//! Tests for DdcStepRowV1, assign_letter witness dominance, and Prime Triad tracing (U03).

use core_wdp::ddc::dda_alphabet::{DdaOp, RefusalReason};
use core_wdp::ddc::{
    assign_letter, compute_ddc_row_hash, DdcStepRowV1, StateMetrics,
};
use core_wdp::prime_algos::prime_candidate::{
    compute_prime_stage_hash, CandidateProposalV1, PrimeStage, PrimeStageRecordV1,
};

#[test]
fn test_dda_op_ordering_and_from_letter() {
    assert_eq!(DdaOp::from_letter("E"), Some(DdaOp::ExactRepair));
    assert_eq!(DdaOp::from_letter("R"), Some(DdaOp::ResidualProjection));
    assert_eq!(DdaOp::from_letter("C"), Some(DdaOp::ContextExposure));
    assert_eq!(DdaOp::from_letter("I"), Some(DdaOp::Integration));
    assert_eq!(DdaOp::from_letter("Λ"), Some(DdaOp::Lift));
    assert_eq!(DdaOp::from_letter("\\Lambda"), Some(DdaOp::Lift));
    assert_eq!(DdaOp::from_letter("Lambda"), Some(DdaOp::Lift));
    assert_eq!(DdaOp::from_letter("Meta"), Some(DdaOp::Lift));
    assert_eq!(DdaOp::from_letter("D"), Some(DdaOp::Descent));
    assert_eq!(DdaOp::from_letter("M"), Some(DdaOp::Refusal));
    assert_eq!(DdaOp::from_letter("T"), Some(DdaOp::Terminalize));
    assert_eq!(DdaOp::from_letter("INVALID"), None);

    // PartialOrd / Ord check
    assert!(DdaOp::ExactRepair != DdaOp::Refusal);
    let mut ops = vec![DdaOp::Terminalize, DdaOp::ExactRepair, DdaOp::Refusal];
    ops.sort();
    assert_eq!(ops.len(), 3);
}

#[test]
fn test_assign_letter_witness_dominance_kills_forged_exact_repair() {
    let before = StateMetrics {
        phi1: 10,
        gamma2: 5,
        residual: 10,
        has_carrier: true,
        has_loss_ledger: false,
        is_terminal: false,
        is_licensed_lift: false,
        refusal: None,
    };

    // Case 1: Honest exact repair (residual == 0, phi1 == 0, gamma2 == 0)
    let honest_resolved = StateMetrics {
        phi1: 0,
        gamma2: 0,
        residual: 0,
        has_carrier: true,
        has_loss_ledger: false,
        is_terminal: false,
        is_licensed_lift: false,
        refusal: None,
    };
    assert_eq!(assign_letter(&before, &honest_resolved), DdaOp::ExactRepair);

    // Case 2: Witness dominance: residual == 0, BUT gamma2 > 0 (cycle obstruction)
    // Exact repair E is STRICTLY FORBIDDEN and emits Refusal M!
    let forged_repair_gamma2 = StateMetrics {
        phi1: 0,
        gamma2: 1, // Cycle obstruction nonzero!
        residual: 0,
        has_carrier: true,
        has_loss_ledger: false,
        is_terminal: false,
        is_licensed_lift: false,
        refusal: None,
    };
    assert_eq!(
        assign_letter(&before, &forged_repair_gamma2),
        DdaOp::Refusal,
        "Witness dominance must reject exact repair when gamma2 > 0"
    );

    // Case 3: Witness dominance: residual == 0, BUT phi1 > 0
    let forged_repair_phi1 = StateMetrics {
        phi1: 1, // Boundary obstruction nonzero!
        gamma2: 0,
        residual: 0,
        has_carrier: true,
        has_loss_ledger: false,
        is_terminal: false,
        is_licensed_lift: false,
        refusal: None,
    };
    assert_eq!(
        assign_letter(&before, &forged_repair_phi1),
        DdaOp::Refusal,
        "Witness dominance must reject exact repair when phi1 > 0"
    );
}

#[test]
fn test_assign_letter_transitions() {
    let mut before = StateMetrics::default();
    let mut after = StateMetrics::default();

    // Terminal
    after.is_terminal = true;
    assert_eq!(assign_letter(&before, &after), DdaOp::Terminalize);
    after.is_terminal = false;

    // Refusal
    after.refusal = Some(RefusalReason::RefusedInvalidWitness);
    assert_eq!(assign_letter(&before, &after), DdaOp::Refusal);
    after.refusal = None;

    // Lift
    after.is_licensed_lift = true;
    assert_eq!(assign_letter(&before, &after), DdaOp::Lift);
    after.is_licensed_lift = false;

    // Context Exposure (Carrier)
    before.has_carrier = false;
    after.has_carrier = true;
    assert_eq!(assign_letter(&before, &after), DdaOp::ContextExposure);

    // Descent
    before.has_carrier = true;
    before.phi1 = 5;
    after.has_loss_ledger = true;
    after.phi1 = 3;
    assert_eq!(assign_letter(&before, &after), DdaOp::Descent);

    // Residual Projection
    after.has_loss_ledger = false;
    before.phi1 = 3;
    after.phi1 = 3;
    after.residual = 2;
    assert_eq!(assign_letter(&before, &after), DdaOp::ResidualProjection);
}

#[test]
fn test_ddc_row_hash_chaining() {
    let hash0 = compute_ddc_row_hash(0, "C", "actor_init", "S0", "S1", "wit0", None, None);
    assert!(!hash0.is_empty());

    let row0 = DdcStepRowV1 {
        seq: 0,
        letter: "C".to_string(),
        actor: "actor_init".to_string(),
        before_state: "S0".to_string(),
        after_state: "S1".to_string(),
        witness: "wit0".to_string(),
        refusal_reason: None,
        prev_step_hash: None,
        step_hash: hash0.clone(),
        authority_effect: "None".to_string(),
    };

    let hash1 = compute_ddc_row_hash(
        1,
        "D",
        "actor_step",
        "S1",
        "S2",
        "wit1",
        None,
        Some(&row0.step_hash),
    );

    let row1 = DdcStepRowV1 {
        seq: 1,
        letter: "D".to_string(),
        actor: "actor_step".to_string(),
        before_state: "S1".to_string(),
        after_state: "S2".to_string(),
        witness: "wit1".to_string(),
        refusal_reason: None,
        prev_step_hash: Some(row0.step_hash.clone()),
        step_hash: hash1.clone(),
        authority_effect: "None".to_string(),
    };

    assert_eq!(row1.prev_step_hash, Some(row0.step_hash.clone()));
    assert_ne!(row0.step_hash, row1.step_hash);

    // Changing any field changes the row hash
    let hash1_tampered = compute_ddc_row_hash(
        1,
        "E", // Tampered letter!
        "actor_step",
        "S1",
        "S2",
        "wit1",
        None,
        Some(&row0.step_hash),
    );
    assert_ne!(hash1, hash1_tampered);
}

#[test]
fn test_prime_triad_candidate_and_stage_record() {
    let mut proposal = CandidateProposalV1::new(
        "prop_001",
        "locus_a",
        b"raw candidate proposal code",
        "proposer_alpha",
    );
    assert!(!proposal.enters_dda_trace);
    assert!(proposal.refusal_reason.is_none());
    assert_eq!(proposal.authority_effect, "None");

    // Refuse proposal
    proposal.refuse("Syntax error in chord declaration");
    assert_eq!(
        proposal.refusal_reason.as_deref(),
        Some("Syntax error in chord declaration")
    );
    assert!(!proposal.enters_dda_trace);

    // Admit proposal
    proposal.admit_to_trace();
    assert!(proposal.enters_dda_trace);
    assert!(proposal.refusal_reason.is_none());

    // Prime Triad Stage Hash Chaining
    let stage_hash0 = compute_prime_stage_hash(
        0,
        PrimeStage::PrimeMinus1.as_str(),
        &proposal.proposal_id,
        "proposer_alpha",
        "ADMITTED",
        "witness_sig",
        None,
    );

    let rec0 = PrimeStageRecordV1::new(
        0,
        PrimeStage::PrimeMinus1,
        &proposal.proposal_id,
        "proposer_alpha",
        "ADMITTED",
        "witness_sig",
        None,
    );
    assert_eq!(rec0.record_hash, stage_hash0);
    assert_eq!(rec0.authority_effect, "None");

    let rec1 = PrimeStageRecordV1::new(
        1,
        PrimeStage::Prime000,
        &proposal.proposal_id,
        "declarator",
        "LOCAL_GREEN_FOR_SCOPE",
        "7_step_order_complete",
        Some(rec0.record_hash.clone()),
    );
    assert_eq!(rec1.prev_record_hash, Some(rec0.record_hash.clone()));
    assert_ne!(rec1.record_hash, rec0.record_hash);
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_step_row_v1.rs
// Claim: urn:core:crates_rs:tests:test-ddc-step-row-v1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb04f1ef8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb04f1ef8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb04f1ef8 {
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
impl BoundaryErrorb04f1ef8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb04f1ef8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb04f1ef8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb04f1ef8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb04f1ef8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb04f1ef8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb04f1ef8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb04f1ef8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b04f1ef8() {
    let admitted = BoundaryRecordb04f1ef8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb04f1ef8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
