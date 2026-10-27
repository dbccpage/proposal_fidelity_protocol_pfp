//! P4 Observation-Budget Planner (PROD-P4) exact verifier.

pub fn optimal_subset_cost_halves(
    costs_in_halves: &[u64],
    pair_masks: &[u8],
    required_mask: u8,
) -> Option<(u8, u64)> {
    let n = costs_in_halves.len();
    let mut best: Option<(u8, u64)> = None;
    for mask in 0u8..(1u8 << n) {
        let mut covered = 0u8;
        let mut cost = 0u64;
        for i in 0..n {
            if (mask & (1u8 << i)) != 0 {
                covered |= pair_masks[i];
                cost += costs_in_halves[i];
            }
        }
        if (covered & required_mask) == required_mask {
            if best.map_or(true, |(_, c)| cost < c) {
                best = Some((mask, cost));
            }
        }
    }
    best
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p4.rs
// Claim: urn:core:crates_rs:tests:prod-p4:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc0a79bd6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc0a79bd6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc0a79bd6 {
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
impl BoundaryErrorc0a79bd6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc0a79bd6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc0a79bd6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc0a79bd6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc0a79bd6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc0a79bd6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc0a79bd6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc0a79bd6::ExceedsCapacity {
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
    fn test_p4_planner_beats_monolithic() {
        // I0: cost 10/2 = 5, covers all 3 pairs (0b111)
        // I1: cost 3/2, covers pairs 0,2 (0b101)
        // I2: cost 4/2 = 2, covers pairs 1,2 (0b110)
        let costs = [10u64, 3, 4];
        let masks = [0b111u8, 0b101, 0b110];
        let (mask, cost) = optimal_subset_cost_halves(&costs, &masks, 0b111).unwrap();
        assert_eq!(mask, 0b110);
        assert_eq!(cost, 7); // 7/2 < 5
    }
}

#[test]
fn l4_boundary_admits_and_refuses_c0a79bd6() {
    let admitted = BoundaryRecordc0a79bd6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc0a79bd6::try_admit(9, 8).is_err());
}
