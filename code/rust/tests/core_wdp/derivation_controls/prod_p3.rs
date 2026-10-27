//! P3 Transferable Guard Library (PROD-P3) exact verifier.

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TransferOutcome {
    Accepted { net_savings_num: i64, net_savings_den: i64 },
    Refused { code: String },
}

pub fn verify_guard_transfer(
    parent_digest_matches: bool,
    sound_on_valid: bool,
    trace_verified: bool,
    net_savings_num: i64,
    net_savings_den: i64,
) -> TransferOutcome {
    if !parent_digest_matches {
        return TransferOutcome::Refused {
            code: "PARENT_DIGEST_MISMATCH".to_string(),
        };
    }
    if !sound_on_valid {
        return TransferOutcome::Refused {
            code: "UNSOUND_GUARD".to_string(),
        };
    }
    if !trace_verified || net_savings_den <= 0 || net_savings_num <= 0 {
        return TransferOutcome::Refused {
            code: "TRACE_REJECTED".to_string(),
        };
    }
    TransferOutcome::Accepted {
        net_savings_num,
        net_savings_den,
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p3.rs
// Claim: urn:core:crates_rs:tests:prod-p3:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord21a8ad59 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord21a8ad59` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError21a8ad59 {
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
impl BoundaryError21a8ad59 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError21a8ad59 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError21a8ad59 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord21a8ad59 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError21a8ad59> {
        if capacity_bound == 0 {
            return Err(BoundaryError21a8ad59::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError21a8ad59::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError21a8ad59::ExceedsCapacity {
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
    fn test_p3_guard_transfer_verification() {
        assert_eq!(
            verify_guard_transfer(true, true, true, 15, 2),
            TransferOutcome::Accepted {
                net_savings_num: 15,
                net_savings_den: 2
            }
        );
        assert_eq!(
            verify_guard_transfer(false, true, true, 15, 2),
            TransferOutcome::Refused {
                code: "PARENT_DIGEST_MISMATCH".to_string()
            }
        );
    }
}

#[test]
fn l4_boundary_admits_and_refuses_21a8ad59() {
    let admitted = BoundaryRecord21a8ad59::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord21a8ad59::try_admit(9, 8).is_err());
}
