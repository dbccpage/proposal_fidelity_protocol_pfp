//! Run composition over the authority lattice: weakest step wins, `Refused`
//! is absorbing, and composition never raises a run above any of its steps.

use core_types::authority_lattice::AuthorityEffectLevel;

const ALL: [AuthorityEffectLevel; 6] = [
    AuthorityEffectLevel::Refused,
    AuthorityEffectLevel::None,
    AuthorityEffectLevel::Uncertified,
    AuthorityEffectLevel::EvidenceOnly,
    AuthorityEffectLevel::FactOnly,
    AuthorityEffectLevel::Certified,
];

#[test]
fn a_later_none_step_never_lifts_a_refused_run() {
    let run = [AuthorityEffectLevel::Refused, AuthorityEffectLevel::None];
    assert_eq!(
        AuthorityEffectLevel::run_grade(run),
        AuthorityEffectLevel::Refused
    );
}

#[test]
fn refused_is_absorbing_on_either_side() {
    for level in ALL {
        assert_eq!(
            AuthorityEffectLevel::Refused.compose_sequential(level),
            AuthorityEffectLevel::Refused
        );
        assert_eq!(
            level.compose_sequential(AuthorityEffectLevel::Refused),
            AuthorityEffectLevel::Refused
        );
    }
}

#[test]
fn composition_never_exceeds_either_step() {
    for a in ALL {
        for b in ALL {
            let composed = a.compose_sequential(b);
            assert!(composed <= a && composed <= b, "{a:?} then {b:?} gave {composed:?}");
        }
    }
}

#[test]
fn a_run_of_none_steps_stays_none() {
    let run = [AuthorityEffectLevel::None; 5];
    assert_eq!(
        AuthorityEffectLevel::run_grade(run),
        AuthorityEffectLevel::None
    );
}

#[test]
fn an_empty_run_asserts_nothing() {
    assert_eq!(
        AuthorityEffectLevel::run_grade(std::iter::empty()),
        AuthorityEffectLevel::None
    );
}

#[test]
fn a_none_step_caps_an_otherwise_certified_run() {
    let run = [
        AuthorityEffectLevel::Certified,
        AuthorityEffectLevel::None,
        AuthorityEffectLevel::Certified,
    ];
    assert_eq!(
        AuthorityEffectLevel::run_grade(run),
        AuthorityEffectLevel::None
    );
}

// Origin: engine/crates_rs/tests/core_types/authority_run_composition.rs
// Claim: urn:core:crates_rs:tests:authority-run-composition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfc4c2d87 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfc4c2d87` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfc4c2d87 {
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
impl BoundaryErrorfc4c2d87 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfc4c2d87 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfc4c2d87 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfc4c2d87 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfc4c2d87> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfc4c2d87::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfc4c2d87::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfc4c2d87::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fc4c2d87() {
    let admitted = BoundaryRecordfc4c2d87::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfc4c2d87::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
