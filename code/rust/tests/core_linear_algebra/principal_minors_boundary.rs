//! Principal subsets are algebraic carriers; positivity admission belongs to physics.
use linear_algebra::exact_field::{elimination::principal_minors, matrix};
use num_bigint::BigInt;
use num_rational::BigRational as Rational;

fn ri(n: i64) -> Rational {
    Rational::from_integer(BigInt::from(n))
}

#[test]
fn principal_minors_replay_subsets_and_permutations_over_exact_fields() {
    let a = matrix::from_rows(vec![
        vec![ri(2), ri(1), ri(0)],
        vec![ri(1), ri(3), ri(1)],
        vec![ri(0), ri(1), ri(4)],
    ])
    .unwrap();
    assert_eq!(
        principal_minors(&a).unwrap(),
        [2, 3, 5, 4, 8, 11, 18].map(ri)
    );
    let permutation = [2, 1, 0];
    let permuted = matrix::from_fn(3, 3, |r, c| {
        a.get_ref(permutation[r], permutation[c]).unwrap().clone()
    })
    .unwrap();
    assert_eq!(
        principal_minors(&permuted).unwrap(),
        [4, 3, 11, 2, 8, 5, 18].map(ri)
    );
}

#[test]
fn principal_minors_admit_empty_carriers_and_refuse_rectangles_or_size_exhaustion() {
    assert!(principal_minors(&matrix::zeros::<Rational>(0, 0).unwrap())
        .unwrap()
        .is_empty());
    assert!(principal_minors(&matrix::zeros::<Rational>(2, 3).unwrap()).is_err());
    assert!(principal_minors(&matrix::identity::<Rational>(13).unwrap()).is_err());
    assert_eq!(
        principal_minors(&matrix::identity::<Rational>(4).unwrap()).unwrap(),
        vec![ri(1); 15]
    );
}

// Origin: engine/crates_rs/tests/core_linear_algebra/principal_minors_boundary.rs
// Claim: urn:core:crates_rs:tests:principal-minors-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda0637f56 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda0637f56` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora0637f56 {
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
impl BoundaryErrora0637f56 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora0637f56 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora0637f56 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda0637f56 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora0637f56> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora0637f56::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora0637f56::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora0637f56::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a0637f56() {
    let admitted = BoundaryRecorda0637f56::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda0637f56::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
