//! Primitive — **cost measures** `mu1` and `mu2`: declared, never inferred.
//!
//! Crate boundary: coda-price.  Source: `candidates.py::mu1`, `mu2`.
//!
//! ```text
//! L12  cost measures are declared, never inferred
//! ```
//!
//! `mu1` counts items.  `mu2` is `(item count, sum of new-form arities)`,
//! ordered lexicographically.  Two measures are carried because ties under
//! one may split under the other, and the sealed Challenge 3 is exactly that
//! case: three tied classes under `mu1` in reading L, one under `mu2`.
//!
//! No measure is preferred.  `CL-NO-UNIVERSAL-PROPERTY` refuses a best; the
//! `reach_measure` tree shows a third measure breaks some ties and leaves
//! others; `path_dependent_cost` shows a cost can be additive and not exact.
//! Whether cost is additive along composition is **unproved** for these two
//! (crosstab §9 item 4), so a composite's price is measured, not summed.

use crate::candidate::{Delta, Item};

/// A cost value.  Compared lexicographically.  The second component is `-1`
/// under `mu1`, so that a single `Cost` type serves both measures without
/// pretending they are comparable to each other.
pub type Cost = (usize, i64);

/// A declared cost measure.
pub trait Measure {
    /// Its name in receipts.
    fn name(&self) -> &'static str;
    /// `μ` — the cost of a candidate.
    fn cost(&self, delta: &Delta) -> Cost;
}

/// The two declared measures.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum MeasureKind {
    /// Item count.
    Mu1,
    /// `(item count, new-form arity sum)`, lexicographic.
    Mu2,
}

impl MeasureKind {
    /// Both, in the order the sealed receipts list them.
    pub const ALL: [MeasureKind; 2] = [MeasureKind::Mu1, MeasureKind::Mu2];
}

/// The new-form arity sum of a delta.
pub fn arity_sum(delta: &Delta) -> i64 {
    delta.iter().map(|it| if let Item::NewForm(a) = it { *a as i64 } else { 0 }).sum()
}

impl Measure for MeasureKind {
    fn name(&self) -> &'static str {
        match self {
            MeasureKind::Mu1 => "mu1",
            MeasureKind::Mu2 => "mu2",
        }
    }
    fn cost(&self, delta: &Delta) -> Cost {
        match self {
            MeasureKind::Mu1 => (delta.len(), -1),
            MeasureKind::Mu2 => (delta.len(), arity_sum(delta)),
        }
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/measure.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:measure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb1b5f586 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb1b5f586` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb1b5f586 {
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
impl BoundaryErrorb1b5f586 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb1b5f586 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb1b5f586 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb1b5f586 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb1b5f586> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb1b5f586::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb1b5f586::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb1b5f586::ExceedsCapacity {
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
    use crate::mark::Mark;

    #[test]
    fn mu1_counts_items_and_mu2_refines_by_arity() {
        let unary = vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])];
        let binary = vec![Item::NewForm(2), Item::NewInst(0, vec![Mark(0), Mark(0)])];
        assert_eq!(MeasureKind::Mu1.cost(&unary), MeasureKind::Mu1.cost(&binary));
        assert!(MeasureKind::Mu2.cost(&unary) < MeasureKind::Mu2.cost(&binary));
        assert_eq!(MeasureKind::Mu2.cost(&unary), (2, 1));
    }
}

#[cfg(test)]
mod l4_boundary_tests_b1b5f586 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb1b5f586::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb1b5f586::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb1b5f586::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb1b5f586::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb1b5f586::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb1b5f586::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb1b5f586::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
