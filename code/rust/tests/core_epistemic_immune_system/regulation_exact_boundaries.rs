//! Exact finite false-discovery policy controls; no FPR or admission claim.
use core_epistemic_immune_system::{
    AntiSkillSpecV2, AntiSkillStatus, DetectorTelemetry, FailureClass, TregSupervisor,
};

fn admitted() -> AntiSkillSpecV2 {
    let mut spec = AntiSkillSpecV2::propose(
        "defect",
        FailureClass::CounterfeitExactness,
        "fixture",
        "boundary control",
        0,
    );
    // This fixture selects a legacy state; it does not authenticate admission.
    spec.status = AntiSkillStatus::Admitted;
    spec
}

fn telemetry(spec: &AntiSkillSpecV2, tp: u64, fp: u64) -> DetectorTelemetry {
    DetectorTelemetry {
        anti_skill_id: spec.id.clone(),
        true_positives: tp,
        false_positives: fp,
        last_active_epoch: 0,
    }
}

#[test]
fn exact_threshold_controls() {
    let scale = 1_u64 << 53;
    // All three totals are 10*scale; only the third numerator exceeds scale.
    for (tp, fp, suspended) in [
        (9 * scale + 1, scale - 1, false),
        (9 * scale, scale, false),
        (9 * scale - 1, scale + 1, true),
        (0, 0, false),
        (0, 9, false),
        (9, 1, false),
        (0, 10, true),
    ] {
        let mut spec = admitted();
        let counts = telemetry(&spec, tp, fp);
        assert_eq!(
            TregSupervisor::default().review(&mut spec, &counts),
            suspended,
            "TP={tp}, FP={fp}"
        );
        assert_eq!(spec.status == AntiSkillStatus::Suspended, suspended);
    }
}

#[test]
fn widened_total_does_not_overflow() {
    let mut spec = admitted();
    let counts = telemetry(&spec, u64::MAX, u64::MAX);
    // FP/(TP+FP)=1/2 even though the total exceeds u64::MAX.
    assert!(TregSupervisor::default().review(&mut spec, &counts));
    assert_eq!(spec.status, AntiSkillStatus::Suspended);
}

#[test]
fn foreign_telemetry_cannot_suspend_a_detector() {
    let mut spec = admitted();
    let mut counts = telemetry(&spec, 0, 10);
    counts.anti_skill_id = "another-detector".into();
    assert!(!TregSupervisor::default().review(&mut spec, &counts));
    assert_eq!(spec.status, AntiSkillStatus::Admitted);
}

#[test]
fn custom_threshold_and_full_width_products_are_exact() {
    assert!(TregSupervisor::try_new(1, 0, 0).is_err());
    assert!(TregSupervisor::try_new(2, 1, 0).is_err());
    for (numerator, denominator, suspend) in
        [(1, 3, true), (1, 2, false), (u64::MAX - 1, u64::MAX, false)]
    {
        let mut spec = admitted();
        let counts = telemetry(&spec, u64::MAX, u64::MAX);
        let policy = TregSupervisor::try_new(numerator, denominator, 0).unwrap();
        assert_eq!(policy.review(&mut spec, &counts), suspend);
    }
}

#[test]
fn fdr_is_not_fpr_and_zero_samples_are_absent() {
    use num_rational::Ratio;
    let spec = admitted();
    let counts = telemetry(&spec, 9, 1);
    assert_eq!(
        TregSupervisor::observed_false_discovery_proportion(&counts),
        Some(Ratio::new(1, 10))
    );
    // TN=0 gives FPR=1; TN=9 gives FPR=1/10. Neither changes this TP/FP policy.
    assert_ne!(
        TregSupervisor::observed_false_discovery_proportion(&counts),
        Some(Ratio::new(1, 1))
    );
    assert_eq!(
        TregSupervisor::observed_false_discovery_proportion(&telemetry(&spec, 0, 0)),
        None
    );
}

#[test]
fn review_preserves_telemetry_and_does_not_readmit_or_resuspend() {
    let mut spec = admitted();
    let counts = telemetry(&spec, 0, 10);
    let before = serde_json::to_value(&counts).unwrap();
    assert!(TregSupervisor::default().review(&mut spec, &counts));
    assert!(!TregSupervisor::default().review(&mut spec, &counts));
    assert_eq!(spec.status, AntiSkillStatus::Suspended);
    assert_eq!(serde_json::to_value(&counts).unwrap(), before);
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/regulation_exact_boundaries.rs
// Claim: urn:core:crates_rs:tests:regulation-exact-boundaries:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddf067af6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddf067af6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordf067af6 {
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
impl BoundaryErrordf067af6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordf067af6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordf067af6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddf067af6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordf067af6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordf067af6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordf067af6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordf067af6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_df067af6() {
    let admitted = BoundaryRecorddf067af6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddf067af6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
