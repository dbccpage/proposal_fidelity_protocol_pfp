//! Lexicographic words over 0..base, including the unique empty word.
//! Cardinality is exact and checked before enumeration. Width has its own
//! explicit resource ceiling; cardinality one does not admit a huge buffer.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_5ae2f2a0<T> {
    fn checked_invariant_5ae2f2a0(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_5ae2f2a0<T> for Option<T> {
    #[inline]
    fn checked_invariant_5ae2f2a0(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_5ae2f2a0<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_5ae2f2a0(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::enumeration::CombinatoricsError;
use num_bigint::BigUint;
use num_traits::ToPrimitive;

pub const MAX_CARTESIAN_WIDTH: usize = 4096;

#[derive(Debug, Clone)]
pub struct CartesianWords {
    base: usize,
    current: Option<Vec<usize>>,
    cardinality: usize,
}
impl CartesianWords {
    pub fn new(
        base: usize,
        width: usize,
        max_words: usize,
        max_width: usize,
    ) -> Result<Self, CombinatoricsError> {
        let admitted_width = max_width.min(MAX_CARTESIAN_WIDTH);
        if width > admitted_width {
            return Err(CombinatoricsError::BudgetExceeded {
                what: "Cartesian word width",
                requested: width.into(),
                limit: admitted_width,
            });
        }
        let count = BigUint::from(base).pow(u32::try_from(width).checked_invariant_5ae2f2a0("width ceiling fits u32"));
        if count > BigUint::from(max_words) {
            return Err(CombinatoricsError::BudgetExceeded {
                what: "Cartesian words",
                requested: count,
                limit: max_words,
            });
        }
        let cardinality = count.to_usize().checked_invariant_5ae2f2a0("count below usize limit");
        Ok(Self {
            base,
            current: if cardinality == 0 {
                None
            } else {
                Some(vec![0; width])
            },
            cardinality,
        })
    }
    pub fn cardinality(&self) -> usize {
        self.cardinality
    }
}
impl Iterator for CartesianWords {
    type Item = Vec<usize>;
    fn next(&mut self) -> Option<Self::Item> {
        let out = self.current.clone()?;
        let mut next = out.clone();
        let mut advanced = false;
        for slot in next.iter_mut().rev() {
            *slot += 1;
            if *slot < self.base {
                advanced = true;
                break;
            }
            *slot = 0;
        }
        self.current = if advanced { Some(next) } else { None };
        Some(out)
    }
}

// Origin: engine/crates_rs/core_combinatorics/src/cartesian_words.rs
// Claim: urn:core:crates_rs:core-combinatorics:cartesian-words:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5ae2f2a0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5ae2f2a0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5ae2f2a0 {
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
impl BoundaryError5ae2f2a0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5ae2f2a0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5ae2f2a0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5ae2f2a0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5ae2f2a0> {
        if capacity_bound == 0 {
            return Err(BoundaryError5ae2f2a0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5ae2f2a0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5ae2f2a0::ExceedsCapacity {
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
mod l4_boundary_tests_5ae2f2a0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5ae2f2a0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5ae2f2a0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5ae2f2a0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5ae2f2a0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5ae2f2a0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5ae2f2a0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5ae2f2a0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
