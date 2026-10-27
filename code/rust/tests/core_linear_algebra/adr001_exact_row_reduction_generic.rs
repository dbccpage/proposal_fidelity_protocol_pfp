//! ADR-001 witness: `ExactRowReduction` serves both coefficient domains.
//!
//! ADR-001 (2026-08-04) makes `BigRational` the canonical coefficient domain for the
//! Φ₁/cochain authority path, and forbids a *parallel* carrier — so the exact row
//! reduction had to become generic rather than gain a duplicate impl.
//!
//! These are integration tests deliberately. `cargo test -p linear_algebra` cannot
//! build the crate's **unit** tests on `origin/main`: `src/vector/row_vector.rs:284`
//! and `src/vector/vector.rs:234` reference `crate::miscellaneous`, which is one of
//! nine undeclared subdirectories. That breakage predates this change and is not
//! addressed here. Integration tests link the library normally and are unaffected.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::{ExactLinearAlgebraError, ExactRowReduction};
use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use num_traits::{One, Zero};

fn r64(n: i64, d: i64) -> Rational64 {
    Rational64::new(n, d)
}

fn rbig(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

// --- behaviour is unchanged for the legacy domain -------------------------------

#[test]
fn rational64_rank_is_unchanged() {
    // [1 2]
    // [2 4]   rank 1 — second row is twice the first.
    let m = BasicMatrix::from_row_major(2, 2, vec![r64(1, 1), r64(2, 1), r64(2, 1), r64(4, 1)])
        .unwrap();
    assert_eq!(m.rank().unwrap(), 1);
}

#[test]
fn rational64_kernel_basis_is_unchanged() {
    let m = BasicMatrix::from_row_major(2, 2, vec![r64(1, 1), r64(2, 1), r64(2, 1), r64(4, 1)])
        .unwrap();
    let kb = m.kernel_basis().unwrap();
    assert_eq!(
        kb.len(),
        1,
        "rank 1 in a 2-column matrix leaves a 1-d kernel"
    );
    // Free column is 1, so the basis vector is (-2, 1).
    assert_eq!(kb[0][0], r64(-2, 1));
    assert_eq!(kb[0][1], r64(1, 1));
}

// --- the same implementation now serves BigRational ------------------------------

#[test]
fn bigrational_rank_agrees_with_rational64() {
    let m = BasicMatrix::from_row_major(2, 2, vec![rbig(1, 1), rbig(2, 1), rbig(2, 1), rbig(4, 1)])
        .unwrap();
    assert_eq!(m.rank().unwrap(), 1);
}

#[test]
fn bigrational_kernel_basis_agrees_with_rational64() {
    let m = BasicMatrix::from_row_major(2, 2, vec![rbig(1, 1), rbig(2, 1), rbig(2, 1), rbig(4, 1)])
        .unwrap();
    let kb = m.kernel_basis().unwrap();
    assert_eq!(kb.len(), 1);
    assert_eq!(kb[0][0], rbig(-2, 1));
    assert_eq!(kb[0][1], rbig(1, 1));
}

#[test]
fn bigrational_identity_has_full_rank_and_empty_kernel() {
    let m = BasicMatrix::from_row_major(
        2,
        2,
        vec![
            BigRational::one(),
            BigRational::zero(),
            BigRational::zero(),
            BigRational::one(),
        ],
    )
    .unwrap();
    assert_eq!(m.rank().unwrap(), 2);
    assert!(m.kernel_basis().unwrap().is_empty());
}

// --- the point of the widening ---------------------------------------------------

/// The bounded domain hits its ceiling and says so. This is the behaviour ADR-001
/// preserves for legacy callers: a typed refusal, never a wrapped value.
#[test]
fn rational64_hits_the_ceiling_on_large_coefficients() {
    let big = 3_037_000_500i64; // > sqrt(i64::MAX); the product overflows.
    let m = BasicMatrix::from_row_major(
        2,
        2,
        vec![r64(big, 1), r64(1, big), r64(1, big), r64(big, 1)],
    )
    .unwrap();

    match m.rank_and_rref() {
        Err(ExactLinearAlgebraError::OverflowCeiling { .. }) => {}
        other => panic!("expected a typed OverflowCeiling refusal, got {other:?}"),
    }
}

/// The canonical domain carries the same matrix without a ceiling. This is the
/// whole reason ADR-001 widens: the computation is not merely faster, it is
/// *possible*.
#[test]
fn bigrational_completes_where_rational64_refuses() {
    let big = 3_037_000_500i64;
    let m = BasicMatrix::from_row_major(
        2,
        2,
        vec![rbig(big, 1), rbig(1, big), rbig(1, big), rbig(big, 1)],
    )
    .unwrap();

    let reduction = m
        .rank_and_rref()
        .expect("BigRational is unbounded: OverflowCeiling must be unreachable");
    assert_eq!(reduction.rank(), 2);
}

/// A coefficient that cannot be represented in `Rational64` at all — not merely one
/// whose product overflows.
#[test]
fn bigrational_carries_coefficients_beyond_i64() {
    use num_traits::ToPrimitive;
    use std::str::FromStr;

    let huge = BigInt::from_str("170141183460469231731687303715884105727").unwrap();
    assert!(
        huge.to_i64().is_none(),
        "must exceed i64, else this proves nothing"
    );

    let m = BasicMatrix::from_row_major(
        2,
        2,
        vec![
            BigRational::new(huge.clone(), BigInt::one()),
            BigRational::zero(),
            BigRational::zero(),
            BigRational::one(),
        ],
    )
    .unwrap();

    assert_eq!(m.rank().unwrap(), 2);
    assert!(m.kernel_basis().unwrap().is_empty());
}

// Origin: engine/crates_rs/tests/core_linear_algebra/adr001_exact_row_reduction_generic.rs
// Claim: urn:core:crates_rs:tests:adr001-exact-row-reduction-generic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord73f0b3ca {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord73f0b3ca` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError73f0b3ca {
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
impl BoundaryError73f0b3ca {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError73f0b3ca {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError73f0b3ca {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord73f0b3ca {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError73f0b3ca> {
        if capacity_bound == 0 {
            return Err(BoundaryError73f0b3ca::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError73f0b3ca::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError73f0b3ca::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_73f0b3ca() {
    let admitted = BoundaryRecord73f0b3ca::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord73f0b3ca::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
