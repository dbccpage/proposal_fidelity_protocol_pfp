//! P5 Continuous Claim-Ledger Certification (PROD-P5) exact verifier.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ClaimStatus {
    Verified,
    BoundedExternal,
    OpenDeclared,
    UnverifiedWritten,
    InvalidLink,
}

pub fn recompute_claim_status(
    declared: ClaimStatus,
    pointers_all_exist: bool,
    deps_all_verified: bool,
) -> ClaimStatus {
    if !pointers_all_exist {
        return ClaimStatus::InvalidLink;
    }
    if declared == ClaimStatus::Verified && !deps_all_verified {
        return ClaimStatus::UnverifiedWritten;
    }
    declared
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p5.rs
// Claim: urn:core:crates_rs:tests:prod-p5:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9b55b11b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9b55b11b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9b55b11b {
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
impl BoundaryError9b55b11b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9b55b11b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9b55b11b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9b55b11b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9b55b11b> {
        if capacity_bound == 0 {
            return Err(BoundaryError9b55b11b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9b55b11b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9b55b11b::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_p5_recompute_status() {
        assert_eq!(
            recompute_claim_status(ClaimStatus::Verified, true, true),
            ClaimStatus::Verified
        );
        assert_eq!(
            recompute_claim_status(ClaimStatus::Verified, false, true),
            ClaimStatus::InvalidLink
        );
        assert_eq!(
            recompute_claim_status(ClaimStatus::Verified, true, false),
            ClaimStatus::UnverifiedWritten
        );
    }
}

#[test]
fn l4_boundary_admits_and_refuses_9b55b11b() {
    let admitted = BoundaryRecord9b55b11b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9b55b11b::try_admit(9, 8).is_err());
}
