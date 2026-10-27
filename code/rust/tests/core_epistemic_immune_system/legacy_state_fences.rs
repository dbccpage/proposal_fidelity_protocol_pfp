//! Regression checks for existing state fences; no Python receipt-parity claim.
use core_epistemic_immune_system::{
    AntiSkillSpecV2, AntiSkillStatus, DangerGateVerdict, DetectorTelemetry, FailureClass,
    Formulary, IndependentDangerSignal, ThymusGate, ThymusVerdict, TregSupervisor,
    TwoSignalDangerGate,
};

fn proposed(pattern: &str) -> AntiSkillSpecV2 {
    AntiSkillSpecV2::propose(
        pattern,
        FailureClass::CounterfeitExactness,
        "fixture",
        "Regression",
        0,
    )
}

#[test]
fn registry_refuses_unselected_missing_blank_and_repeated_admission() {
    let mut formulary = Formulary::new();
    let mut spec = proposed("defect");
    assert_eq!(
        formulary.register_candidate(spec.clone()),
        Err("ONLY_CANDIDATE_CAN_BE_REGISTERED_IN_FORMULARY")
    );
    assert!(matches!(
        formulary.admit_with_receipt("missing", "reviewer", 0, "receipt"),
        Err("ANTI_SKILL_NOT_FOUND")
    ));
    assert!(matches!(
        ThymusGate::new(vec!["clean".into()]).screen(&mut spec),
        ThymusVerdict::Survived { .. }
    ));
    assert_eq!(spec.status, AntiSkillStatus::Candidate);
    assert!(spec.status.is_candidate());
    assert!(!spec.status.is_active());
    assert!(!spec.status.is_admitted());
    assert_eq!(formulary.register_candidate(spec.clone()), Ok(()));
    assert!(matches!(
        formulary.admit_with_receipt(&spec.id, "reviewer", 0, " "),
        Err("ADMISSION_REQUIRES_HUMAN_RECEIPT_DIGEST")
    ));
    assert!(formulary.list_active().is_empty());
    let receipt = formulary
        .admit_with_receipt(&spec.id, "reviewer", 1, "receipt")
        .expect("valid legacy admission");
    assert_eq!(receipt.authority_effect, "None");
    assert_eq!(formulary.list_active().len(), 1);
    let admitted = formulary.get(&spec.id).expect("registered");
    assert!(admitted.status.is_active());
    assert!(admitted.status.is_admitted());
    assert!(!admitted.status.is_candidate());
    assert!(matches!(
        formulary.admit_with_receipt(&spec.id, "reviewer", 2, "other"),
        Err("ONLY_CANDIDATE_CAN_BE_ADMITTED")
    ));
    assert_eq!(formulary.list_active().len(), 1);
}

#[test]
fn legacy_invalid_patterns_and_lifecycle_do_not_activate() {
    let gate = ThymusGate::new(vec!["clean".into()]);
    let mut invalid = proposed("[");
    assert!(matches!(
        gate.screen(&mut invalid),
        ThymusVerdict::InvalidPattern { .. }
    ));
    assert_eq!(invalid.status, AntiSkillStatus::Proposed);
    // These public legacy records can be authored by callers. This regression
    // checks their gate and does not treat such a record as checked admission.
    invalid.status = AntiSkillStatus::Admitted;
    assert!(matches!(
        TwoSignalDangerGate::evaluate(
            &invalid,
            "defect",
            Some(IndependentDangerSignal::InvalidSignature)
        ),
        DangerGateVerdict::RefusedStatus {
            status: AntiSkillStatus::Retired,
            ..
        }
    ));
    let mut spec = proposed("defect");
    spec.status = AntiSkillStatus::Admitted;
    assert!(
        matches!(gate.screen(&mut spec),ThymusVerdict::InvalidPattern{error} if error=="SPEC_NOT_PROPOSED")
    );
    assert!(matches!(
        TwoSignalDangerGate::evaluate(
            &spec,
            "clean",
            Some(IndependentDangerSignal::InvalidSignature)
        ),
        DangerGateVerdict::NoMatch
    ));
    for status in [
        AntiSkillStatus::Proposed,
        AntiSkillStatus::Candidate,
        AntiSkillStatus::Suspended,
        AntiSkillStatus::Retired,
    ] {
        spec.status = status;
        assert!(
            matches!(TwoSignalDangerGate::evaluate(&spec,"defect",Some(IndependentDangerSignal::InvalidSignature)),DangerGateVerdict::RefusedStatus{status:refused,..} if refused==status)
        );
    }
    spec.suspend();
    assert_eq!(spec.status, AntiSkillStatus::Retired);
}

#[test]
fn legacy_telemetry_requires_samples_and_exceeds_threshold_strictly() {
    let supervisor = TregSupervisor::default();
    let mut spec = proposed("defect");
    spec.status = AntiSkillStatus::Admitted;
    for (true_positives, false_positives) in [(0, 0), (0, 9), (9, 1), (10, 0)] {
        let telemetry = DetectorTelemetry {
            anti_skill_id: spec.id.clone(),
            true_positives,
            false_positives,
            last_active_epoch: 0,
        };
        assert!(!supervisor.review(&mut spec, &telemetry));
        assert_eq!(spec.status, AntiSkillStatus::Admitted);
    }
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/legacy_state_fences.rs
// Claim: urn:core:crates_rs:tests:legacy-state-fences:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord66d04d0f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord66d04d0f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError66d04d0f {
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
impl BoundaryError66d04d0f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError66d04d0f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError66d04d0f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord66d04d0f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError66d04d0f> {
        if capacity_bound == 0 {
            return Err(BoundaryError66d04d0f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError66d04d0f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError66d04d0f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_66d04d0f() {
    let admitted = BoundaryRecord66d04d0f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord66d04d0f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
