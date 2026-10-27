//! Canonical evidence ceiling type.
//!
//! This is the single authoritative definition of the evidence-routing ceiling.
//! It is a routing/authorization convention, not an absolute truth-strength claim.
//! See `evidence_ceiling_reconciliation_proof.md` for the formal justification.

use serde::{Deserialize, Serialize};

/// The canonical evidence ceiling chain.
///
/// `ShapeOnly < LocalReplay < BoundaryChecked < ExternalOracleRequired < EmpiricalOracleRequired`
///
/// This is a **capability chain** describing what the host can verify.
/// It is NOT a rigor/provenance axis (see `RigorGrade`) and NOT a
/// witness-certainty axis (see `WitnessCertainty`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum EvidenceCeiling {
    ShapeOnly = 0,
    LocalReplay = 1,
    BoundaryChecked = 2,
    ExternalOracleRequired = 3,
    EmpiricalOracleRequired = 4,
}

impl EvidenceCeiling {
    pub fn meet(self, other: Self) -> Self {
        std::cmp::min(self, other)
    }

    pub fn join(self, other: Self) -> Self {
        std::cmp::max(self, other)
    }

    pub fn raise_with(self, cert_level: Self) -> Self {
        std::cmp::max(self, cert_level)
    }
}

// Origin: engine/crates_rs/core_types/src/ceiling.rs
// Claim: urn:core:crates_rs:core-types:ceiling:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord87d38a8b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord87d38a8b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError87d38a8b {
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
impl BoundaryError87d38a8b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError87d38a8b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError87d38a8b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord87d38a8b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError87d38a8b> {
        if capacity_bound == 0 {
            return Err(BoundaryError87d38a8b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError87d38a8b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError87d38a8b::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn order_chain_correct() {
        assert!(EvidenceCeiling::ShapeOnly < EvidenceCeiling::LocalReplay);
        assert!(EvidenceCeiling::LocalReplay < EvidenceCeiling::BoundaryChecked);
        assert!(EvidenceCeiling::BoundaryChecked < EvidenceCeiling::ExternalOracleRequired);
        assert!(EvidenceCeiling::ExternalOracleRequired < EvidenceCeiling::EmpiricalOracleRequired);
    }

    #[test]
    fn meet_returns_minimum() {
        assert_eq!(
            EvidenceCeiling::BoundaryChecked.meet(EvidenceCeiling::ShapeOnly),
            EvidenceCeiling::ShapeOnly,
        );
        assert_eq!(
            EvidenceCeiling::ShapeOnly.meet(EvidenceCeiling::EmpiricalOracleRequired),
            EvidenceCeiling::ShapeOnly,
        );
    }

    #[test]
    fn join_returns_maximum() {
        assert_eq!(
            EvidenceCeiling::ShapeOnly.join(EvidenceCeiling::BoundaryChecked),
            EvidenceCeiling::BoundaryChecked,
        );
        assert_eq!(
            EvidenceCeiling::EmpiricalOracleRequired.join(EvidenceCeiling::LocalReplay),
            EvidenceCeiling::EmpiricalOracleRequired,
        );
    }

    #[test]
    fn meet_idempotent() {
        for v in [
            EvidenceCeiling::ShapeOnly,
            EvidenceCeiling::LocalReplay,
            EvidenceCeiling::BoundaryChecked,
        ] {
            assert_eq!(v.meet(v), v);
        }
    }

    #[test]
    fn join_idempotent() {
        for v in [
            EvidenceCeiling::ShapeOnly,
            EvidenceCeiling::ExternalOracleRequired,
            EvidenceCeiling::EmpiricalOracleRequired,
        ] {
            assert_eq!(v.join(v), v);
        }
    }

    #[test]
    fn meet_commutative() {
        let a = EvidenceCeiling::LocalReplay;
        let b = EvidenceCeiling::ExternalOracleRequired;
        assert_eq!(a.meet(b), b.meet(a));
    }

    #[test]
    fn join_commutative() {
        let a = EvidenceCeiling::ShapeOnly;
        let b = EvidenceCeiling::BoundaryChecked;
        assert_eq!(a.join(b), b.join(a));
    }

    #[test]
    fn absorption() {
        let a = EvidenceCeiling::LocalReplay;
        let b = EvidenceCeiling::BoundaryChecked;
        assert_eq!(a.meet(a.join(b)), a);
        assert_eq!(a.join(a.meet(b)), a);
    }

    #[test]
    fn raise_with_is_max() {
        assert_eq!(
            EvidenceCeiling::ShapeOnly.raise_with(EvidenceCeiling::BoundaryChecked),
            EvidenceCeiling::BoundaryChecked,
        );
        assert_eq!(
            EvidenceCeiling::EmpiricalOracleRequired.raise_with(EvidenceCeiling::LocalReplay),
            EvidenceCeiling::EmpiricalOracleRequired,
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_87d38a8b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord87d38a8b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord87d38a8b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord87d38a8b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord87d38a8b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord87d38a8b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError87d38a8b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError87d38a8b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
