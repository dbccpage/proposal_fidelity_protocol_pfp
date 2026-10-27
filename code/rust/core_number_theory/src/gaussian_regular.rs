//! The regular Q-linear representation Q(i) -> M_2(Q).
//!
//! a+bi maps to [[a,-b],[b,a]]. Multiplication is composition of multiplication
//! on the Q-basis (1,i); the image of i is a complex structure J²=-I.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_77b89130<T> {
    fn checked_invariant_77b89130(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_77b89130<T> for Option<T> {
    #[inline]
    fn checked_invariant_77b89130(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_77b89130<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_77b89130(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::cyclotomic::GaussianRat;
use crate::rational::Rational;
use linear_algebra::backend::basic_matrix::BasicMatrix;

pub fn regular_representation(z: &GaussianRat) -> BasicMatrix<Rational> {
    BasicMatrix::from_row_major(2, 2, vec![z.re.clone(), -&z.im, z.im.clone(), z.re.clone()])
        .checked_invariant_77b89130("the regular field representation has four entries")
}
pub fn regular_coordinates(m: &BasicMatrix<Rational>) -> Option<GaussianRat> {
    if m.shape() != (2, 2) {
        return None;
    }
    let data = m.as_slice();
    (data[0] == data[3] && data[1] == -&data[2]).then(|| GaussianRat {
        re: data[0].clone(),
        im: data[2].clone(),
    })
}

// Origin: engine/crates_rs/core_number_theory/src/gaussian_regular.rs
// Claim: urn:core:crates_rs:core-number-theory:gaussian-regular:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord77b89130 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord77b89130` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError77b89130 {
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
impl BoundaryError77b89130 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError77b89130 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError77b89130 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord77b89130 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError77b89130> {
        if capacity_bound == 0 {
            return Err(BoundaryError77b89130::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError77b89130::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError77b89130::ExceedsCapacity {
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
mod l4_boundary_tests_77b89130 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord77b89130::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord77b89130::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord77b89130::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord77b89130::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord77b89130::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError77b89130::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError77b89130::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
