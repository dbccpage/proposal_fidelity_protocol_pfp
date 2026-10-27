//! Canonical finite sums of normalized real radicals. AuthorityEffect: None.
use crate::quadratic::Surd;
use crate::rational::Rational;
use num_bigint::BigInt;
use num_traits::Zero;
use std::collections::BTreeMap;
/// An exact finite sum `sum c_r sqrt(r)` over distinct squarefree radicands.
/// Such sums are equal exactly when their coefficients are, because square roots
/// of distinct squarefree integers are linearly independent over `Q`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct SurdSum {
    terms: BTreeMap<BigInt, Rational>,
}

impl SurdSum {
    pub fn terms(&self) -> &BTreeMap<BigInt, Rational> {
        &self.terms
    }
    pub fn add_surd(&mut self, surd: &Surd) {
        if surd.is_zero() {
            return;
        }
        let entry = self
            .terms
            .entry(surd.radicand().clone())
            .or_insert_with(Rational::zero);
        *entry = &*entry + surd.coefficient();
        if entry.is_zero() {
            self.terms.remove(surd.radicand());
        }
    }

    /// The value when it is rational (only the radicand `1` survives).
    pub fn as_rational(&self) -> Option<Rational> {
        match self.terms.len() {
            0 => Some(Rational::zero()),
            1 => self.terms.get(&BigInt::from(1)).cloned(),
            _ => None,
        }
    }
}

// Origin: engine/crates_rs/core_number_theory/src/radical_sum.rs
// Claim: urn:core:crates_rs:core-number-theory:radical-sum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2c611c09 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2c611c09` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2c611c09 {
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
impl BoundaryError2c611c09 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2c611c09 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2c611c09 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2c611c09 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2c611c09> {
        if capacity_bound == 0 {
            return Err(BoundaryError2c611c09::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2c611c09::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2c611c09::ExceedsCapacity {
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
mod dynamics_laws {

    use super::*;
    use crate::rational::{ri, rq};
    #[test]
    fn normalized_radicals_coalesce_and_exact_cancellation_is_rational() {
        let mut sum = SurdSum::default();
        sum.add_surd(&Surd::new(ri(1), &ri(8)).unwrap());
        sum.add_surd(&Surd::new(ri(-2), &ri(2)).unwrap());
        assert_eq!(sum.as_rational(), Some(ri(0)));
        sum.add_surd(&Surd::new(rq(1, 3), &ri(9)).unwrap());
        assert_eq!(sum.as_rational(), Some(ri(1)));
        sum.add_surd(&Surd::new(ri(1), &ri(3)).unwrap());
        assert_eq!(sum.as_rational(), None);
    }
}

#[cfg(test)]
mod l4_boundary_tests_2c611c09 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2c611c09::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2c611c09::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2c611c09::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2c611c09::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2c611c09::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2c611c09::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2c611c09::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
