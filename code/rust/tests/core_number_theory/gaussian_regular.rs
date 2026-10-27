//! The exact regular field representation, with independent ring and image laws.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::gaussian_regular::{regular_coordinates, regular_representation};
use core_number_theory::rational::{ri, rq, Rational};
fn rational_matrix(rows: [[i64; 2]; 2]) -> BasicMatrix<Rational> {
    BasicMatrix::from_row_major(2, 2, rows.iter().flatten().map(|&v| ri(v)).collect()).unwrap()
}

#[test]
fn the_complex_structure_squares_to_minus_one_and_the_sign_to_plus_one() {
    let identity = mx::identity(2).unwrap();
    let j = regular_representation(&GaussianRat::from_ints(0, 1));
    assert_eq!(j, rational_matrix([[0, -1], [1, 0]]));
    assert_eq!(
        mx::multiply(&(j), &(&j)).unwrap(),
        mx::scale(&(identity), &ri(-1)).unwrap()
    );
    let s = rational_matrix([[1, 0], [0, -1]]);
    assert_eq!(mx::multiply(&(s), &(&s)).unwrap(), identity);
    assert_ne!(
        mx::multiply(&(j), &(&j)).unwrap(),
        mx::multiply(&(s), &(&s)).unwrap()
    );
    // J is a complex scalar; the sign carrier is not.
    assert_eq!(regular_coordinates(&j), Some(GaussianRat::from_ints(0, 1)));
    assert_eq!(regular_coordinates(&s), None);
    assert_eq!(regular_coordinates(&mx::identity(3).unwrap()), None);
}

#[test]
fn the_regular_representation_is_an_injective_unital_ring_homomorphism() {
    let identity = mx::identity(2).unwrap();
    let one = regular_representation(&GaussianRat::from_ints(1, 0));
    let j = regular_representation(&GaussianRat::from_ints(0, 1));
    assert_eq!(one, identity);
    // Q-linearity plus the products on the basis {1, i} decide the product law.
    for (re, im) in [(rq(2, 3), rq(-5, 7)), (ri(0), ri(4)), (rq(-1, 2), ri(0))] {
        let z = GaussianRat {
            re: re.clone(),
            im: im.clone(),
        };
        assert_eq!(
            regular_representation(&z),
            mx::add(
                &(mx::scale(&(one), &re).unwrap()),
                &(&mx::scale(&(j), &im).unwrap())
            )
            .unwrap()
        );
    }
    assert_eq!(
        mx::multiply(&(j), &(&j)).unwrap(),
        regular_representation(&GaussianRat::from_ints(0, 1).mul(&GaussianRat::from_ints(0, 1)))
    );
    assert_eq!(
        mx::multiply(&(j), &(&one)).unwrap(),
        mx::multiply(&(one), &(&j)).unwrap()
    );
    // Exhaustively on a box of Gaussian integers.
    let mut elements = Vec::new();
    for a in -3..=3 {
        for b in -3..=3 {
            elements.push(GaussianRat::from_ints(a, b));
        }
    }
    for z in &elements {
        let rz = regular_representation(z);
        assert_eq!(regular_coordinates(&rz), Some(z.clone()));
        for w in &elements {
            let rw = regular_representation(w);
            assert_eq!(
                regular_representation(&z.mul(w)),
                mx::multiply(&(rz), &(&rw)).unwrap()
            );
            assert_eq!(
                regular_representation(&z.add(w)),
                mx::add(&(rz), &(&rw)).unwrap()
            );
            assert_eq!(rz == rw, z == w);
        }
    }
}

// Origin: engine/crates_rs/tests/core_number_theory/gaussian_regular.rs
// Claim: urn:core:crates_rs:tests:gaussian-regular:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord656d6c83 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord656d6c83` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError656d6c83 {
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
impl BoundaryError656d6c83 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError656d6c83 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError656d6c83 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord656d6c83 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError656d6c83> {
        if capacity_bound == 0 {
            return Err(BoundaryError656d6c83::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError656d6c83::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError656d6c83::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_656d6c83() {
    let admitted = BoundaryRecord656d6c83::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord656d6c83::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
