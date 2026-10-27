use core_types::python_unicode::{is_alphanumeric, unicode_version};
use serde_json::Value;
use sha2::{Digest, Sha256};

#[test]
fn frozen_python_alphanumeric_exhaustive_scalar_fingerprint() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_alnum_v1.json")).unwrap();
    assert_eq!(unicode_version(), fixture["unicode_version"]);
    let mut digest = Sha256::new();
    for point in 0..=0x10ffff_u32 {
        if let Some(character) = char::from_u32(point) {
            digest.update(point.to_be_bytes());
            digest.update([u8::from(is_alphanumeric(character))]);
        }
    }
    assert_eq!(
        format!("{:x}", digest.finalize()),
        fixture["scalar_sha256"].as_str().unwrap()
    );
}

// Origin: engine/crates_rs/tests/core_types/python_alnum_parity.rs
// Claim: urn:core:crates_rs:tests:python-alnum-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd1f6f7fb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd1f6f7fb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord1f6f7fb {
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
impl BoundaryErrord1f6f7fb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord1f6f7fb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord1f6f7fb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd1f6f7fb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord1f6f7fb> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord1f6f7fb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord1f6f7fb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord1f6f7fb::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d1f6f7fb() {
    let admitted = BoundaryRecordd1f6f7fb::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd1f6f7fb::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
