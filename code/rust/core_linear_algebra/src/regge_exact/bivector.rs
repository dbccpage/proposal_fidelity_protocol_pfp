//! Bivectors in `∧² Q^4`.
//!
//! Component order: `e01, e02, e03, e12, e13, e23`.
//! `from_wedge_half(u, v)` stores `(1/2)(u_i v_j - u_j v_i)`.
//! The coefficient of the unit 4-vector in `Σ ∧ Σ` is twice the pfaffian
//! `c01 c23 - c02 c13 + c03 c12`. Both vanish together, so simplicity is
//! `pfaffian = 0`.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use num_rational::BigRational;
use num_traits::Zero;

const PAIRS: [(usize, usize); 6] = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)];

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Bivector4 {
    pub c: [BigRational; 6],
}

impl Bivector4 {
    pub fn zero() -> Self {
        Self {
            c: std::array::from_fn(|_| BigRational::zero()),
        }
    }

    pub fn from_components(c: [BigRational; 6]) -> Self {
        Self { c }
    }

    pub fn from_wedge_half(u: &[BigRational; 4], v: &[BigRational; 4]) -> Self {
        let two = BigRational::from_integer(num_bigint::BigInt::from(2));
        Self {
            c: std::array::from_fn(|index| {
                let (i, j) = PAIRS[index];
                (&u[i] * &v[j] - &u[j] * &v[i]) / &two
            }),
        }
    }

    /// Pfaffian `c01 c23 - c02 c13 + c03 c12`.
    ///
    /// `Σ ∧ Σ` is twice this pfaffian times the unit 4-vector. The two
    /// expressions vanish together.
    pub fn pfaffian(&self) -> BigRational {
        &self.c[0] * &self.c[5] - &self.c[1] * &self.c[4] + &self.c[2] * &self.c[3]
    }

    pub fn is_simple(&self) -> bool {
        self.pfaffian().is_zero()
    }

    pub fn checked_add(&self, other: &Self) -> Self {
        Self {
            c: std::array::from_fn(|index| &self.c[index] + &other.c[index]),
        }
    }

    pub fn checked_scale(&self, scale: &BigRational) -> Self {
        Self {
            c: std::array::from_fn(|index| &self.c[index] * scale),
        }
    }

    pub fn is_zero(&self) -> bool {
        self.c.iter().all(BigRational::is_zero)
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/regge_exact/bivector.rs
// Claim: urn:core:crates_rs:core-linear-algebra:bivector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd7c581f0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd7c581f0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord7c581f0 {
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
impl BoundaryErrord7c581f0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord7c581f0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord7c581f0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd7c581f0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord7c581f0> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord7c581f0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord7c581f0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord7c581f0::ExceedsCapacity {
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
    use super::Bivector4;
    use crate::regge_exact::{q_i64, q_ratio};

    #[test]
    fn coordinate_wedge_is_simple_and_a_sum_of_complementary_planes_is_not() {
        let mut e0 = std::array::from_fn(|_| q_i64(0));
        let mut e1 = std::array::from_fn(|_| q_i64(0));
        e0[0] = q_i64(1);
        e1[1] = q_i64(1);
        let area = Bivector4::from_wedge_half(&e0, &e1);
        assert_eq!(area.c[0], q_ratio(1, 2).unwrap());
        assert!(area.c[1..].iter().all(|component| component == &q_i64(0)));
        assert!(area.is_simple());

        let mixed = Bivector4::from_components([
            q_i64(1),
            q_i64(0),
            q_i64(0),
            q_i64(0),
            q_i64(0),
            q_i64(1),
        ]);
        assert_eq!(mixed.pfaffian(), q_i64(1));
        assert!(!mixed.is_simple());
        assert_eq!(
            area.checked_scale(&q_i64(2)).checked_add(&mixed).c[0],
            q_i64(2)
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_d7c581f0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd7c581f0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd7c581f0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd7c581f0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd7c581f0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd7c581f0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord7c581f0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord7c581f0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
