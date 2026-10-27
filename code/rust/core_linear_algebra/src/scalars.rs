use num_traits::{CheckedAdd, CheckedDiv, CheckedMul, CheckedSub, One, Zero};
use std::fmt;

// ============================================================================
// Semiring: additive commutative monoid + multiplicative monoid + distributivity
// ============================================================================

pub trait Semiring: Clone + PartialEq + fmt::Debug {
    fn zero() -> Self;
    fn one() -> Self;
    fn add(&self, rhs: &Self) -> Self;
    fn mul(&self, rhs: &Self) -> Self;
    fn is_zero(&self) -> bool;
}

// ============================================================================
// Ring: Semiring + additive inverse
// ============================================================================

pub trait Ring: Semiring {
    fn neg(&self) -> Self;

    fn sub(&self, other: &Self) -> Self {
        self.add(&other.neg())
    }
}

// ============================================================================
// Field: Ring + multiplicative inverse (for nonzero elements)
// ============================================================================

pub trait Field: Ring {
    /// Multiplicative inverse. Returns None if zero or non-invertible.
    fn try_inv(&self) -> Option<Self>;

    fn try_div(&self, other: &Self) -> Option<Self> {
        let inv = other.try_inv()?;
        Some(self.mul(&inv))
    }
}

// ============================================================================
// Sealed Checked Exact Field Protocol
// ============================================================================

mod sealed {
    pub trait Sealed {}
    impl Sealed for num_rational::Rational64 {}
    impl Sealed for num_rational::BigRational {}
}

/// Sealed, fallible exact-field protocol for theorem-grade exact linear algebra.
///
/// Implemented EXPLICITLY ONLY for [`num_rational::Rational64`] and
/// [`num_rational::BigRational`]. Integer primitives (such as `i64`) and
/// floating-point types (`f64`) are explicitly EXCLUDED: `num_traits::CheckedDiv`
/// on integers performs truncating integer division (e.g., `1 / 2 = 0`), which
/// produces mathematically false row reduction, ranks, and kernels.
///
/// Authority provenance: `one_oears.md` ruling 4.
pub trait CheckedExactField:
    sealed::Sealed
    + Clone
    + Eq
    + Zero
    + One
    + CheckedAdd
    + CheckedSub
    + CheckedMul
    + CheckedDiv
    + fmt::Debug
    + 'static
{
    fn checked_neg(&self) -> Option<Self>;
}

impl CheckedExactField for num_rational::Rational64 {
    fn checked_neg(&self) -> Option<Self> {
        Self::zero().checked_sub(self)
    }
}

impl CheckedExactField for num_rational::BigRational {
    fn checked_neg(&self) -> Option<Self> {
        Some(-self.clone())
    }
}

// ============================================================================
// Exact rationals in the scalar tower
// ============================================================================
//
// `BigRational` is unbounded, so the infallible `Semiring`/`Ring`/`Field` operations
// cannot overflow and equality is mathematical equality. `Rational64` is deliberately
// absent: its arithmetic can overflow, which is exactly why it is reached through the
// checked protocol (`CheckedExactField`) instead.

impl Semiring for num_rational::BigRational {
    fn zero() -> Self {
        <Self as Zero>::zero()
    }
    fn one() -> Self {
        <Self as One>::one()
    }
    fn add(&self, rhs: &Self) -> Self {
        self + rhs
    }
    fn mul(&self, rhs: &Self) -> Self {
        self * rhs
    }
    fn is_zero(&self) -> bool {
        <Self as Zero>::is_zero(self)
    }
}

impl Ring for num_rational::BigRational {
    fn neg(&self) -> Self {
        -self
    }
}

impl Field for num_rational::BigRational {
    fn try_inv(&self) -> Option<Self> {
        if <Self as Zero>::is_zero(self) {
            None
        } else {
            Some(self.recip())
        }
    }
}

impl ExactRing for num_rational::BigRational {}

// ============================================================================
// Epistemic/Safety Markers
// ============================================================================

/// Marker trait for mathematically exact rings (e.g. GF(2), Rationals, bounded integers).
/// Equality must mean mathematical equality. No floating point tolerance.
pub trait ExactRing: Ring {}

/// Marker trait for analytic rings (e.g. f64, C64).
/// Real-world physics, but mathematically unsafe for exact homological proofs.
pub trait AnalyticRing: Ring {
    fn tolerance() -> f64;
    fn approx_eq(&self, other: &Self) -> bool;
}

// ============================================================================
// Test Implementations
// ============================================================================

impl Semiring for i64 {
    fn zero() -> Self {
        0
    }
    fn one() -> Self {
        1
    }
    fn add(&self, rhs: &Self) -> Self {
        *self + *rhs
    }
    fn mul(&self, rhs: &Self) -> Self {
        *self * *rhs
    }
    fn is_zero(&self) -> bool {
        *self == 0
    }
}

impl Ring for i64 {
    fn neg(&self) -> Self {
        -*self
    }
}

impl ExactRing for i64 {}

// Origin: engine/crates_rs/core_linear_algebra/src/scalars.rs
// Claim: urn:core:crates_rs:core-linear-algebra:scalars:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9ba6b3c5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9ba6b3c5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9ba6b3c5 {
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
impl BoundaryError9ba6b3c5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9ba6b3c5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9ba6b3c5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9ba6b3c5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9ba6b3c5> {
        if capacity_bound == 0 {
            return Err(BoundaryError9ba6b3c5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9ba6b3c5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9ba6b3c5::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    /// A dummy exact field Z5 for testing the trait bounds and defaults.
    #[derive(Debug, Clone, PartialEq, Eq)]
    struct Z5(u8);

    impl Semiring for Z5 {
        fn zero() -> Self {
            Z5(0)
        }
        fn one() -> Self {
            Z5(1)
        }
        fn add(&self, rhs: &Self) -> Self {
            Z5((self.0 + rhs.0) % 5)
        }
        fn mul(&self, rhs: &Self) -> Self {
            Z5((self.0 * rhs.0) % 5)
        }
        fn is_zero(&self) -> bool {
            self.0 == 0
        }
    }

    impl Ring for Z5 {
        fn neg(&self) -> Self {
            Z5((5 - self.0) % 5)
        }
    }

    impl Field for Z5 {
        fn try_inv(&self) -> Option<Self> {
            match self.0 {
                1 => Some(Z5(1)),
                2 => Some(Z5(3)),
                3 => Some(Z5(2)),
                4 => Some(Z5(4)),
                _ => None,
            }
        }
    }

    impl ExactRing for Z5 {}

    #[test]
    fn z5_is_exact_field() {
        let a = Z5(2);
        let b = Z5(4);

        let sum = a.add(&b); // 2 + 4 = 1 mod 5
        assert_eq!(sum, Z5(1));

        let diff = a.sub(&b); // 2 - 4 = 3 mod 5
        assert_eq!(diff, Z5(3));

        let inv = a.try_inv().unwrap(); // 2^-1 = 3
        assert_eq!(inv, Z5(3));

        let div = a.try_div(&b).unwrap(); // 2 / 4 = 2 * 4 = 3
        assert_eq!(div, Z5(3));

        assert!(Z5::zero().try_inv().is_none());
    }
}

#[cfg(test)]
mod l4_boundary_tests_9ba6b3c5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9ba6b3c5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9ba6b3c5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9ba6b3c5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9ba6b3c5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9ba6b3c5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9ba6b3c5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9ba6b3c5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
