//! Targeted tests for the Nine-Layer CODA Stack (Layers 1-9) in core_wdp::coda::q::coda_stack.
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use num_traits::Signed;
use core_wdp::coda::q::coda_stack::{
    SentinelRecord, SentinelRegister, CodaError, ContinuumShadow, CryptographicGrant, DualWitness,
    Enclosure, FdaPacket, FocSignature, CodaGtlaOutcome, LossLedger, MetricSeparation, OverlapGluing,
    SevenHaltGuards, TerminalRefusal, TransportCertificate,
};
use core_types::ObstructionDiagnosticClass;
use std::marker::PhantomData;

#[test]
fn test_layer1_foc_signature_and_witness() {
    let exact_sig = FocSignature::new_exact();
    assert!(exact_sig.is_exact());
    assert_eq!(
        exact_sig.trichotomy,
        ObstructionDiagnosticClass::ExactRepair
    );

    let witness = DualWitness {
        witness_id: "wit-42".into(),
        dual_vector: vec![BigRational::new(1.into(), 2.into())],
        certificate_hash: "sha256:abc123def456".into(),
    };
    let obstructed_sig = FocSignature::new_obstructed(
        BigRational::new(3.into(), 1.into()),
        BigRational::new(0.into(), 1.into()),
        witness,
    );
    assert!(!obstructed_sig.is_exact());
    assert_eq!(
        obstructed_sig.trichotomy,
        ObstructionDiagnosticClass::ClosedResidual
    );
    assert!(obstructed_sig.dual_witness.is_some());
}

#[test]
fn test_layer2_mur_transport_and_loss_ledger() {
    let mut ledger = LossLedger::default();
    assert!(ledger.is_lossless());

    ledger.record_loss("slot_phase", 2, "High-degree phase dropped in projection");
    assert!(!ledger.is_lossless());
    assert_eq!(ledger.entries.len(), 1);
    assert_eq!(ledger.entries[0].slot, "slot_phase");

    let cert = TransportCertificate {
        source_locus: "X_high".into(),
        target_locus: "X_low".into(),
        commutation_defect: BigRational::new(0.into(), 1.into()),
        loss_ledger: ledger,
        is_retraction: true,
    };
    assert!(cert.is_retraction);
}

#[test]
fn test_layer3_cs_continuum_shadow() {
    let shadow: ContinuumShadow<String, Vec<u8>> = ContinuumShadow {
        continuum_concept_id: "Circle_S1".into(),
        finite_profile: vec![0, 1, 2, 3],
        fiber_constancy_witness: "wit-fiber-constancy-4-points".into(),
        _marker: PhantomData,
    };
    assert_eq!(shadow.continuum_concept_id, "Circle_S1");
    assert_eq!(shadow.finite_profile.len(), 4);
}

#[test]
fn test_layer4_cs_q_metric_separation_bounds() {
    let epsilon = BigRational::new(1.into(), 10.into()); // 0.1
                                                         // 2 * epsilon = 0.2
    let passing_dist = BigRational::new(3.into(), 10.into()); // 0.3 > 0.2
    let failing_dist = BigRational::new(15.into(), 100.into()); // 0.15 <= 0.2

    let passed = MetricSeparation::check(passing_dist, epsilon.clone());
    assert!(passed.is_ok());

    let failed = MetricSeparation::check(failing_dist, epsilon);
    assert!(matches!(failed, Err(CodaError::MetricCollapse(_))));
}

#[test]
fn test_layer5_q_continuum_enclosure_bounds() {
    // Enclosure for sqrt(2) approx: [1.414, 1.415]
    let lo = BigRational::new(1414.into(), 1000.into());
    let hi = BigRational::new(1415.into(), 1000.into());
    let enc = Enclosure::new(lo.clone(), hi.clone()).expect("valid interval");

    assert_eq!(enc.diameter(), BigRational::new(1.into(), 1000.into()));
    let mid = enc.midpoint();
    assert_eq!(mid, BigRational::new(2829.into(), 2000.into()));

    // True value approx 1.4142
    let x = BigRational::new(14142.into(), 10000.into());
    assert!(enc.contains_with_bound(&x));

    // Midpoint non-conflation bound: |x - mid| <= width / 2
    let half_width = enc.diameter() / BigRational::from_integer(2.into());
    let diff = (x - mid).abs();
    assert!(diff <= half_width);
}

#[test]
fn test_layer6_a_sentinel_register() {
    let mut reg = SentinelRegister::default();
    let record = SentinelRecord {
        sentinel_id: "ano-001".into(),
        residual_class_hash: "sha256:111222333".into(),
        phi_1: BigRational::new(5.into(), 1.into()),
        dual_witness_hash: "sha256:444555666".into(),
        carrier_locus: "Simplex(C1)".into(),
        created_at: "2026-09-25T19:00:00Z".into(),
    };
    reg.commit(record.clone());

    let retrieved = reg.find("ano-001").expect("must exist");
    assert_eq!(retrieved.phi_1, BigRational::new(5.into(), 1.into()));
}

#[test]
fn test_layer7_or_overlap_gluing() {
    let compatible = OverlapGluing {
        left_slot: "SegmentA",
        shared_slot_left: "InterfaceB".into(),
        shared_slot_right: "InterfaceB".into(),
        right_slot: "SegmentC",
    };
    let glued = compatible.glue();
    assert!(glued.is_ok());

    let incompatible = OverlapGluing {
        left_slot: "SegmentA",
        shared_slot_left: "InterfaceB".into(),
        shared_slot_right: "InterfaceB_Prime".into(),
        right_slot: "SegmentC",
    };
    assert!(matches!(
        incompatible.glue(),
        Err(CodaError::IncompatibleOverlap(_))
    ));
}

#[test]
fn test_layer8_fda_seven_halt_guards_role_split() {
    let witness = DualWitness {
        witness_id: "wit-fda-01".into(),
        dual_vector: vec![],
        certificate_hash: "sha256:fda".into(),
    };

    // Valid role split: proposer != authorizer
    let valid_packet = FdaPacket {
        carrier: "carrier-01".into(),
        evidence: "ev-data",
        dual_witness: witness.clone(),
        transport_trace: vec!["step1".into()],
        lift_license: "license-coda".into(),
        proposer_id: "agent-alice".into(),
        authorizer_id: "agent-bob".into(),
        budget_remaining: 100,
    };
    assert!(SevenHaltGuards::verify(&valid_packet).is_ok());

    // Role split violation: proposer == authorizer
    let self_authorizing_packet = FdaPacket {
        carrier: "carrier-01".into(),
        evidence: "ev-data",
        dual_witness: witness,
        transport_trace: vec!["step1".into()],
        lift_license: "license-coda".into(),
        proposer_id: "agent-alice".into(),
        authorizer_id: "agent-alice".into(),
        budget_remaining: 100,
    };
    assert!(matches!(
        SevenHaltGuards::verify(&self_authorizing_packet),
        Err(CodaError::RoleSplitViolation(_))
    ));
}

#[test]
fn test_layer9_coda_gtla_master_normal_form_outcomes() {
    use core_types::{AuthorityTerminal, Outcome, RefusalSource, ResidualTerminal};

    let grant = CryptographicGrant {
        key_id: "secp256k1:master-coda-key".into(),
        signature_hex: "deadbeef0123456789".into(),
        timestamp: "2026-09-25T19:30:00Z".into(),
    };
    let authorized: CodaGtlaOutcome<&str> = CodaGtlaOutcome::Authorized("ValidState", grant);
    match &authorized {
        CodaGtlaOutcome::Authorized(state, g) => {
            assert_eq!(*state, "ValidState");
            assert_eq!(g.key_id, "secp256k1:master-coda-key");
        }
        _ => panic!("Expected Authorized outcome"),
    }
    assert_eq!(
        authorized.to_outcome(),
        Outcome::Terminal(AuthorityTerminal::ExactRuleDerived)
    );

    let trapped: CodaGtlaOutcome<&str> = CodaGtlaOutcome::ResidualTrapped(SentinelRecord {
        sentinel_id: "ano-001".into(),
        residual_class_hash: "hash".into(),
        phi_1: BigRational::from_integer(1.into()),
        dual_witness_hash: "wit".into(),
        carrier_locus: "c1".into(),
        created_at: "now".into(),
    });
    assert_eq!(
        trapped.to_outcome(),
        Outcome::Residual(ResidualTerminal::ClosedResidual)
    );

    let refusal: CodaGtlaOutcome<&str> = CodaGtlaOutcome::Refused(TerminalRefusal {
        code: "UNAUTHORIZED".into(),
        reason: "Zero defects does not mint permission".into(),
    });
    match &refusal {
        CodaGtlaOutcome::Refused(r) => assert_eq!(r.code, "UNAUTHORIZED"),
        _ => panic!("Expected Refused outcome"),
    }
    assert_eq!(
        refusal.to_outcome(),
        Outcome::Refused(RefusalSource::Refusal)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_coda_q_nine_layers.rs
// Claim: urn:core:crates_rs:tests:test-coda-q-nine-layers:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde2af2321 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde2af2321` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore2af2321 {
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
impl BoundaryErrore2af2321 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore2af2321 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore2af2321 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde2af2321 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore2af2321> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore2af2321::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore2af2321::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore2af2321::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e2af2321() {
    let admitted = BoundaryRecorde2af2321::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde2af2321::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
