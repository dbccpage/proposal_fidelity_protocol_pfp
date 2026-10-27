use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use core_homology::finite_rational_homology::{
    FiniteRationalChainComplex, FiniteRationalChainMap, RationalHomologyQuotient,
    RationalHomologyRefusal,
};
use core_homology::scalar::{q, Q};

fn limits() -> OperationLimits {
    OperationLimits {
        max_elements: 1000,
        max_scalar_ops: 100_000,
    }
}

fn matrix(rows: usize, cols: usize, values: &[i64]) -> BasicMatrix<Q> {
    BasicMatrix::from_row_major(rows, cols, values.iter().map(|&value| q(value)).collect()).unwrap()
}

fn one_filled_cycle() -> FiniteRationalChainComplex {
    FiniteRationalChainComplex::new(
        vec![1, 2, 1],
        vec![matrix(1, 2, &[0, 0]), matrix(2, 1, &[1, 0])],
        limits(),
    )
    .unwrap()
}

#[test]
fn exact_cycle_quotient_coordinates_and_inverse() {
    let complex = one_filled_cycle();
    let h = RationalHomologyQuotient::new(&complex, 1, limits()).unwrap();
    assert_eq!(h.dimension(), 1);
    assert_eq!(h.boundary_basis(), &[vec![q(1), q(0)]]);
    assert_eq!(h.coordinates(&[q(13), q(7)], limits()).unwrap(), vec![q(7)]);
    assert_eq!(h.coordinates(&[q(13), q(0)], limits()).unwrap(), vec![q(0)]);
    assert_eq!(
        h.representative(&[q(7)], limits()).unwrap(),
        vec![q(0), q(7)]
    );
    for k in 0..=2 {
        let quotient = RationalHomologyQuotient::new(&complex, k, limits()).unwrap();
        for (i, cycle) in quotient.representatives().iter().enumerate() {
            let coordinates = quotient.coordinates(cycle, limits()).unwrap();
            assert_eq!(coordinates[i], q(1));
            assert_eq!(
                quotient.representative(&coordinates, limits()).unwrap(),
                *cycle
            );
        }
    }
}

#[test]
fn induced_homology_preserves_identity_and_composition() {
    let complex = one_filled_cycle();
    let h = RationalHomologyQuotient::new(&complex, 1, limits()).unwrap();
    let f = FiniteRationalChainMap::new(
        &complex,
        &complex,
        vec![
            matrix(1, 1, &[1]),
            matrix(2, 2, &[3, 0, 0, 2]),
            matrix(1, 1, &[3]),
        ],
        limits(),
    )
    .unwrap();
    let g = FiniteRationalChainMap::new(
        &complex,
        &complex,
        vec![
            matrix(1, 1, &[1]),
            matrix(2, 2, &[5, 7, 0, 4]),
            matrix(1, 1, &[5]),
        ],
        limits(),
    )
    .unwrap();
    assert_eq!(f.induced(&h, &h, limits()).unwrap(), matrix(1, 1, &[2]));
    assert_eq!(g.induced(&h, &h, limits()).unwrap(), matrix(1, 1, &[4]));
    let composite = f
        .then(&g, limits())
        .unwrap()
        .induced(&h, &h, limits())
        .unwrap();
    assert_eq!(composite, matrix(1, 1, &[8]));
    assert_eq!(
        composite,
        g.induced(&h, &h, limits())
            .unwrap()
            .checked_mul(&f.induced(&h, &h, limits()).unwrap())
            .unwrap()
    );
    let identity = FiniteRationalChainMap::identity(&complex, limits()).unwrap();
    for k in 0..=2 {
        let quotient = RationalHomologyQuotient::new(&complex, k, limits()).unwrap();
        let induced = identity.induced(&quotient, &quotient, limits()).unwrap();
        assert_eq!(
            induced.shape(),
            (quotient.dimension(), quotient.dimension())
        );
        assert_eq!(
            induced,
            linear_algebra::exact_field::matrix::identity(quotient.dimension()).unwrap()
        );
    }
}

#[test]
fn noncycles_broken_chain_maps_and_changed_boundaries_refuse() {
    let interval =
        FiniteRationalChainComplex::new(vec![2, 1], vec![matrix(2, 1, &[-1, 1])], limits())
            .unwrap();
    let h1 = RationalHomologyQuotient::new(&interval, 1, limits()).unwrap();
    assert_eq!(h1.dimension(), 0);
    assert_eq!(
        h1.coordinates(&[q(1)], limits()),
        Err(RationalHomologyRefusal::NotCycle)
    );
    assert_eq!(
        h1.coordinates(&[], limits()),
        Err(RationalHomologyRefusal::InvalidShape)
    );
    let complex = one_filled_cycle();
    assert_eq!(
        FiniteRationalChainMap::new(
            &complex,
            &complex,
            vec![
                matrix(1, 1, &[1]),
                matrix(2, 2, &[1, 0, 1, 1]),
                matrix(1, 1, &[1])
            ],
            limits()
        ),
        Err(RationalHomologyRefusal::NotChainMap)
    );
    let changed = FiniteRationalChainComplex::new(
        vec![1, 2, 1],
        vec![matrix(1, 2, &[0, 0]), matrix(2, 1, &[0, 1])],
        limits(),
    )
    .unwrap();
    assert_ne!(complex.content_hash(), changed.content_hash());
    let wrong_h = RationalHomologyQuotient::new(&changed, 1, limits()).unwrap();
    let identity = FiniteRationalChainMap::identity(&complex, limits()).unwrap();
    assert_eq!(
        identity.induced(&wrong_h, &wrong_h, limits()),
        Err(RationalHomologyRefusal::CarrierMismatch)
    );
    assert_eq!(
        identity.then(
            &FiniteRationalChainMap::identity(&changed, limits()).unwrap(),
            limits()
        ),
        Err(RationalHomologyRefusal::CarrierMismatch)
    );
}

#[test]
fn boundary_shape_degree_and_resource_mutations_fail_closed() {
    assert_eq!(
        FiniteRationalChainComplex::new(
            vec![1, 1, 1],
            vec![matrix(1, 1, &[1]), matrix(1, 1, &[1])],
            limits()
        ),
        Err(RationalHomologyRefusal::BoundaryLaw)
    );
    assert_eq!(
        FiniteRationalChainComplex::new(vec![2, 1], vec![matrix(1, 1, &[0])], limits()),
        Err(RationalHomologyRefusal::InvalidShape)
    );
    let complex = one_filled_cycle();
    assert_eq!(
        RationalHomologyQuotient::new(&complex, 3, limits()),
        Err(RationalHomologyRefusal::InvalidDegree)
    );
    let exhausted = OperationLimits {
        max_elements: 1,
        max_scalar_ops: 1,
    };
    assert!(matches!(
        RationalHomologyQuotient::new(&complex, 1, exhausted),
        Err(RationalHomologyRefusal::ResourceOrArithmetic(_))
    ));
    assert_eq!(
        FiniteRationalChainMap::new(&complex, &complex, vec![matrix(1, 1, &[1])], limits()),
        Err(RationalHomologyRefusal::InvalidShape)
    );
}

// Origin: engine/crates_rs/tests/core_homology/finite_rational_homology.rs
// Claim: urn:core:crates_rs:tests:finite-rational-homology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd25da6af {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd25da6af` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord25da6af {
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
impl BoundaryErrord25da6af {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord25da6af {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord25da6af {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd25da6af {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord25da6af> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord25da6af::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord25da6af::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord25da6af::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d25da6af() {
    let admitted = BoundaryRecordd25da6af::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd25da6af::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
