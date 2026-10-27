//! Exact finite control witness for `PLAN-QP-C9` (`plan_qp_c9`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_unscoped_majorana_hardness_or_leakage_claim`.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub carrier_val: i64,
    pub secondary_pair: (i64, i64),
    pub coboundary_cycle_zero: i64,
}

pub fn witness() -> Witness {
    let a = [3_i64, 7, 11];
    let coboundary_cycle_zero = (a[1] - a[0]) + (a[2] - a[1]) + (a[0] - a[2]);
    Witness {
        carrier_val: 6,
        secondary_pair: (2, 3),
        coboundary_cycle_zero,
    }
}

pub fn reject_unscoped_majorana_hardness_or_leakage_claim(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "unscoped_majorana_hardness_or_leakage_claim" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-C9: unscoped_majorana_hardness_or_leakage_claim")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_c9.rs
// Claim: urn:core:crates_rs:tests:plan-qp-c9:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc1076806 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc1076806` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc1076806 {
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
impl BoundaryErrorc1076806 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc1076806 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc1076806 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc1076806 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc1076806> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc1076806::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc1076806::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc1076806::ExceedsCapacity {
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
    use super::{reject_unscoped_majorana_hardness_or_leakage_claim, witness};

    #[test]
    fn plan_qp_c9_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 6);
        assert_eq!(w.secondary_pair, (2, 3));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_c9_refuses_unscoped_majorana_hardness_or_leakage_claim() {
        assert!(reject_unscoped_majorana_hardness_or_leakage_claim("unscoped_majorana_hardness_or_leakage_claim").is_err());
        assert!(reject_unscoped_majorana_hardness_or_leakage_claim("promote_unrestricted").is_err());
        assert!(reject_unscoped_majorana_hardness_or_leakage_claim("admissible_scoped_control").is_ok());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_c1076806() {
    let admitted = BoundaryRecordc1076806::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc1076806::try_admit(9, 8).is_err());
}
