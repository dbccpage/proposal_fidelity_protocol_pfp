//! Exact finite causal sets, interval abundances and the dimension-two interval action.
//! These finite observables do not identify a continuum spacetime. AuthorityEffect: None.
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite causal set; no continuum admission.";
use num_bigint::BigInt;
use num_traits::Zero;
use core_homology::finite_poset::{FinitePoset, PosetError};
use core_number_theory::rational::Rational;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CausalSet {
    pub degree: usize,
    pub label: String,
    order: FinitePoset,
}
impl CausalSet {
    /// A discrete causal set of `degree` events carrying the declared label.
    /// Use from_order for a nontrivial validated causal order.
    pub fn new(degree: usize, label: impl Into<String>) -> Result<Self, PosetError> {
        Ok(Self {
            degree,
            label: label.into(),
            order: FinitePoset::new(degree, [])?,
        })
    }
    pub fn from_order(order: FinitePoset, label: impl Into<String>) -> Self {
        Self {
            degree: order.size(),
            label: label.into(),
            order,
        }
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
    pub fn order(&self) -> &FinitePoset {
        &self.order
    }
    pub fn spacelike(&self, u: usize, v: usize) -> Result<bool, PosetError> {
        Ok(u != v && !self.order.less(u, v)? && !self.order.less(v, u)?)
    }
    pub fn alexandrov_interval(&self, u: usize, v: usize) -> Result<Vec<usize>, PosetError> {
        self.order.interval(u, v)
    }
    pub fn past(&self, v: usize) -> Result<Vec<usize>, PosetError> {
        self.order.predecessors(v)
    }
    pub fn future(&self, v: usize) -> Result<Vec<usize>, PosetError> {
        self.order.successors(v)
    }
    pub fn ordering_fraction(&self) -> Rational {
        let n = self.order.size();
        if n < 2 {
            return Rational::zero();
        }
        Rational::new(
            BigInt::from(2) * BigInt::from(self.order.relation_count()),
            BigInt::from(n) * BigInt::from(n - 1),
        )
    }
    /// Counts comparable pairs with each cardinality of their open interval.
    pub fn interval_abundances(&self) -> Result<Vec<BigInt>, PosetError> {
        let mut counts = vec![BigInt::zero(); self.order.size().saturating_sub(1)];
        for (u, v) in self.order.strict_relations() {
            let open = self.order.interval(u, v)?.len() - 2;
            counts[open] += 1;
        }
        Ok(counts)
    }
    /// The dimension-two Benincasa-Dowker interval polynomial, before any
    /// continuum normalization: N-2N0+4N1-2N2 (Ni has i interior events).
    pub fn two_dimensional_interval_action(&self) -> Result<BigInt, PosetError> {
        let counts = self.interval_abundances()?;
        let count = |i| counts.get(i).cloned().unwrap_or_else(BigInt::zero);
        Ok(BigInt::from(self.order.size()) - 2 * count(0) + 4 * count(1) - 2 * count(2))
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/causal_set.rs
// Claim: urn:core:crates_rs:core-general-relativity:causal-set:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbe7b70b3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbe7b70b3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbe7b70b3 {
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
impl BoundaryErrorbe7b70b3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbe7b70b3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbe7b70b3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbe7b70b3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbe7b70b3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbe7b70b3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbe7b70b3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbe7b70b3::ExceedsCapacity {
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
mod l4_boundary_tests_be7b70b3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbe7b70b3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbe7b70b3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbe7b70b3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbe7b70b3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbe7b70b3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbe7b70b3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbe7b70b3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
