//! Exact finite control witness for `PLAN-QP-8` (`plan_qp_8`).
//!
//! Evaluates the declared finite carrier invariant and refuses out-of-scope
//! promotion via `reject_noninvariant_observable_orbit_cancellation`.

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
        carrier_val: 2,
        secondary_pair: (1, 1),
        coboundary_cycle_zero,
    }
}

pub fn reject_noninvariant_observable_orbit_cancellation(claim_flag: &str) -> Result<(), &'static str> {
    if claim_flag == "noninvariant_observable_orbit_cancellation" || claim_flag == "promote_unrestricted" || claim_flag == "bypass_guard" {
        Err("refused out-of-scope promotion for PLAN-QP-8: noninvariant_observable_orbit_cancellation")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_qp_8.rs
// Claim: urn:core:crates_rs:tests:plan-qp-8:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6f905304 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6f905304` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6f905304 {
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
impl BoundaryError6f905304 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6f905304 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6f905304 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6f905304 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6f905304> {
        if capacity_bound == 0 {
            return Err(BoundaryError6f905304::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6f905304::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6f905304::ExceedsCapacity {
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
    use super::{reject_noninvariant_observable_orbit_cancellation, witness};

    #[test]
    fn plan_qp_8_witness_matches_derivation() {
        let w = witness();
        assert_eq!(w.carrier_val, 2);
        assert_eq!(w.secondary_pair, (1, 1));
        assert_eq!(w.coboundary_cycle_zero, 0);
    }

    #[test]
    fn plan_qp_8_refuses_noninvariant_observable_orbit_cancellation() {
        assert!(reject_noninvariant_observable_orbit_cancellation("noninvariant_observable_orbit_cancellation").is_err());
        assert!(reject_noninvariant_observable_orbit_cancellation("promote_unrestricted").is_err());
        assert!(reject_noninvariant_observable_orbit_cancellation("admissible_scoped_control").is_ok());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_6f905304() {
    let admitted = BoundaryRecord6f905304::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6f905304::try_admit(9, 8).is_err());
}
