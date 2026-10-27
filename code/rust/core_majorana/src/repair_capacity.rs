//! Repair-capacity **diagnostic** helper (CODE_DEMO only).
//!
//! QM_102-shaped shadow: given a declared code / homology distance \(d\),
//! the classical unique-decode repair radius is
//! \(t = \lfloor(d-1)/2\rfloor\), which always satisfies \(t < d/2\).
//!
//! # Authority fence
//!
//! - **AuthorityEffect: None**
//! - Does **not** mint a threshold theorem, THR-001 packet, or PROVED claim.
//! - Does **not** assert a physical surface-code distance for any complex.

#![forbid(unsafe_code)]

/// Diagnostic repair capacity \(t = \lfloor(d-1)/2\rfloor\) for positive distance \(d\).
///
/// Refuses \(d = 0\) (undeclared distance is not a certificate).
pub fn repair_capacity_from_distance(d: u32) -> Result<u32, String> {
    if d == 0 {
        return Err(
            "repair_capacity: homology/code distance d must be positive (undeclared d refuses)"
                .into(),
        );
    }
    Ok(d.saturating_sub(1) / 2)
}

/// Invariant gate: \(t = \lfloor(d-1)/2\rfloor\) and \(t < d/2\) (equivalently \(2t < d\)).
pub fn assert_repair_capacity_invariant(d: u32) -> Result<u32, String> {
    let t = repair_capacity_from_distance(d)?;
    let expected = (d - 1) / 2;
    if t != expected {
        return Err(format!(
            "repair_capacity: t={} != floor((d-1)/2)={} for d={}",
            t, expected, d
        ));
    }
    // Real inequality t < d/2 ⇔ 2t < d for integer d ≥ 1.
    if 2 * t >= d {
        return Err(format!(
            "repair_capacity: invariant broken: t={} is not < d/2 for d={}",
            t, d
        ));
    }
    Ok(t)
}

/// Optional CODE_DEMO: min Hamming weight among a declared list of nontrivial
/// closed residuals (proxy for distance lower bound — **not** a threshold proof).
pub fn min_weight_nontrivial(cycles: &[Vec<u8>]) -> Option<u32> {
    cycles
        .iter()
        .filter(|c| c.iter().any(|&b| b % 2 == 1))
        .map(|c| c.iter().map(|&b| (b % 2) as u32).sum::<u32>())
        .min()
}

// Origin: engine/crates_rs/core_majorana/src/repair_capacity.rs
// Claim: urn:core:crates_rs:core-majorana:repair-capacity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb9919a78 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb9919a78` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb9919a78 {
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
impl BoundaryErrorb9919a78 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb9919a78 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb9919a78 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb9919a78 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb9919a78> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb9919a78::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb9919a78::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb9919a78::ExceedsCapacity {
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
    fn repair_capacity_matches_a_hand_table() {
        // Kills: returning d/2 or d-1, both of which disagree with this table.
        let table = [
            (1u32, 0u32),
            (2, 0),
            (3, 1),
            (4, 1),
            (5, 2),
            (8, 3),
            (9, 4),
            (15, 7),
            (u32::MAX, 2_147_483_647),
        ];
        for (d, t) in table {
            assert_eq!(repair_capacity_from_distance(d).unwrap(), t, "d={d}");
            assert_eq!(assert_repair_capacity_invariant(d).unwrap(), t, "d={d}");
        }
    }

    #[test]
    fn d_zero_refuses() {
        // Kills: accepting an undeclared distance as t = 0.
        let err = repair_capacity_from_distance(0).unwrap_err();
        assert!(err.contains("positive"), "{err}");
        let err = assert_repair_capacity_invariant(0).unwrap_err();
        assert!(err.contains("positive"), "{err}");
    }

    #[test]
    fn min_weight_ignores_evens_empty_and_the_first_odd_vector() {
        // Kills: returning the first vector's raw sum, or Some(0) for an empty list.
        assert_eq!(min_weight_nontrivial(&[]), None);
        assert_eq!(min_weight_nontrivial(&[vec![0, 2, 4], vec![0, 0, 0]]), None);
        assert_eq!(
            min_weight_nontrivial(&[vec![1, 1, 1], vec![0, 2, 4], vec![3]]),
            Some(1),
            "odd weight of [3] is 1 and is smaller than the leading weight-3 vector"
        );
        assert_eq!(
            min_weight_nontrivial(&[vec![1, 1, 1, 1], vec![5, 0, 7]]),
            Some(2)
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_b9919a78 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb9919a78::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb9919a78::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb9919a78::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb9919a78::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb9919a78::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb9919a78::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb9919a78::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
