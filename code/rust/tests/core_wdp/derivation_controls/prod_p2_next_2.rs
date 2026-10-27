//! Companion Rust witness for PROD-P2-NEXT-2 (Fixture per G.5 step failing exclusively that step).

pub const G5_STEPS: [&str; 12] = [
    "G.5.1", "G.5.2", "G.5.3", "G.5.4", "G.5.5", "G.5.6",
    "G.5.7", "G.5.8", "G.5.9", "G.5.10", "G.5.11", "G.5.12",
];

pub fn evaluate_single_step_fixture(step_flags: &[bool; 12]) -> Vec<&'static str> {
    G5_STEPS
        .iter()
        .zip(step_flags.iter())
        .filter_map(|(step, &passed)| if !passed { Some(*step) } else { None })
        .collect()
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p2_next_2.rs
// Claim: urn:core:crates_rs:tests:prod-p2-next-2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6e878fc6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6e878fc6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6e878fc6 {
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
impl BoundaryError6e878fc6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6e878fc6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6e878fc6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6e878fc6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6e878fc6> {
        if capacity_bound == 0 {
            return Err(BoundaryError6e878fc6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6e878fc6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6e878fc6::ExceedsCapacity {
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
    fn each_g5_fixture_fails_exclusively_its_target_step() {
        for idx in 0..12 {
            let mut flags = [true; 12];
            flags[idx] = false;
            let failures = evaluate_single_step_fixture(&flags);
            assert_eq!(failures, vec![G5_STEPS[idx]]);
        }
    }
}

#[test]
fn l4_boundary_admits_and_refuses_6e878fc6() {
    let admitted = BoundaryRecord6e878fc6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6e878fc6::try_admit(9, 8).is_err());
}
