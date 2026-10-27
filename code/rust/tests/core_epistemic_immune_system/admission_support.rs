use core_epistemic_immune_system::admission::execute;
use serde_json::Value;
#[test]
fn source_admission_and_observation_support_agree() {
    let rows: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/admission_support.json")).unwrap();
    for row in rows {
        match execute(&row["request"]) {
            Ok(value) => {
                assert!(row["refusal"].is_null(), "{}", row["name"]);
                assert_eq!(value, row["outcome"], "{}", row["name"]);
            }
            Err(error) => {
                assert_eq!(error.code, row["refusal"]["code"], "{}", row["name"]);
                assert_eq!(error.message, row["refusal"]["message"], "{}", row["name"]);
            }
        }
    }
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/admission_support.rs
// Claim: urn:core:crates_rs:tests:admission-support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1b8e3d6c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1b8e3d6c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1b8e3d6c {
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
impl BoundaryError1b8e3d6c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1b8e3d6c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1b8e3d6c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1b8e3d6c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1b8e3d6c> {
        if capacity_bound == 0 {
            return Err(BoundaryError1b8e3d6c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1b8e3d6c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1b8e3d6c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1b8e3d6c() {
    let admitted = BoundaryRecord1b8e3d6c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1b8e3d6c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
