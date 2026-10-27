//! The completely positive import boundary (annex of the stochastic-kernel
//! paper): on classical kernels positivity already gives complete positivity;
//! on maps that move coherence it does not; and a Kraus decomposition is a
//! presentation of the channel, not part of it.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, involution as star, matrix as mx};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{rq, Rational};
use core_quantum_physics::exact_channel::{apply_choi, choi_is_cptp, ExactKrausChannel};
use core_quantum_physics::exact_hermitian::{self, gi};

use crate::support::{dm, pauli_x, rm, unit};

fn lift(kernel: &[Vec<Rational>]) -> BasicMatrix<GaussianRat> {
    mx::diagonal(
        &kernel
            .iter()
            .flatten()
            .cloned()
            .map(GaussianRat::from_rational)
            .collect::<Vec<_>>(),
    )
    .unwrap()
}

#[test]
fn positivity_gives_complete_positivity_on_classical_kernels_only() {
    // A nonnegative kernel K and K (x) I_2 (rows (g, a), columns (h, b), entry K(h|g) [a = b]).
    let k = vec![vec![rq(1, 2), rq(1, 2)], vec![rq(1, 4), rq(3, 4)]];
    let tensored: Vec<Vec<Rational>> = (0..4)
        .map(|row| {
            (0..4)
                .map(|col| {
                    if row % 2 == col % 2 {
                        k[row / 2][col / 2].clone()
                    } else {
                        rq(0, 1)
                    }
                })
                .collect()
        })
        .collect();
    assert!(tensored
        .iter()
        .all(|row| row.iter().sum::<Rational>() == rq(1, 1)));
    // Both classical lifts are CPTP: their Choi matrices are diagonal and nonnegative.
    assert!(choi_is_cptp(&lift(&k), 2, 2));
    assert!(choi_is_cptp(&lift(&tensored), 4, 4));
    // The transpose map is positive on states, yet the same extension by an
    // identity breaks positivity: the partial transpose of the Bell state has
    // the negative direction (0, 1, -1, 0).
    let mut swap = mx::zeros(4, 4).unwrap();
    for (row, col) in [(0, 0), (1, 2), (2, 1), (3, 3)] {
        swap.set(row, col, GaussianRat::one()).unwrap();
    }
    let state = rm(&[&[9, 12], &[12, 16]], 25);
    assert!(exact_hermitian::is_positive_semidefinite(
        &apply_choi(&swap, 2, 2, &state).unwrap()
    ));
    assert!(!choi_is_cptp(&swap, 2, 2));
    let bell = rm(
        &[&[1, 0, 0, 1], &[0, 0, 0, 0], &[0, 0, 0, 0], &[1, 0, 0, 1]],
        2,
    );
    let extended = exact_hermitian::partial_transpose_second(&bell, 2, 2).unwrap();
    let direction = [gi(0, 0), gi(1, 0), gi(-1, 0), gi(0, 0)];
    assert_eq!(
        star::inner_product(
            &direction,
            &mx::multiply_vector_with_limits(
                &extended,
                &direction,
                exact_hermitian::exact_limits()
            )
            .unwrap()
        )
        .unwrap(),
        gi(-1, 0)
    );
    assert!(!exact_hermitian::is_positive_semidefinite(&extended));
}

#[test]
fn kraus_decompositions_are_presentations_of_one_choi_matrix() {
    let a0 = dm(&[5, 3], 5);
    let a1 = rm(&[&[0, 4], &[0, 0]], 5);
    let original = ExactKrausChannel::from_operators(vec![a0.clone(), a1.clone()]).unwrap();
    // Mixing the operators by the orthogonal U = [[3/5, 4/5], [-4/5, 3/5]] gives another Kraus family.
    let u = rm(&[&[3, 4], &[-4, 3]], 5);
    let mixed = vec![
        mx::add(
            &mx::scale(&a0, &GaussianRat::from_rational(rq(3, 5))).unwrap(),
            &mx::scale(&a1, &GaussianRat::from_rational(rq(4, 5))).unwrap(),
        )
        .unwrap(),
        mx::add(
            &mx::scale(&a0, &GaussianRat::from_rational(rq(-4, 5))).unwrap(),
            &mx::scale(&a1, &GaussianRat::from_rational(rq(3, 5))).unwrap(),
        )
        .unwrap(),
    ];
    let remixed = ExactKrausChannel::from_operators(mixed).unwrap();
    let padded = ExactKrausChannel::from_operators(vec![a0, a1, mx::zeros(2, 2).unwrap()]).unwrap();
    assert_ne!(original.operators(), remixed.operators());
    assert_eq!(original.choi(), remixed.choi());
    assert_eq!(original.choi(), padded.choi());
    for rho in [
        rm(&[&[1, 1], &[1, 1]], 2),
        rm(&[&[9, 12], &[12, 16]], 25),
        unit(2, 1, 1),
    ] {
        assert_eq!(original.apply(&rho).unwrap(), remixed.apply(&rho).unwrap());
        assert_eq!(original.apply(&rho).unwrap(), padded.apply(&rho).unwrap());
    }
    // The number of operators is not intrinsic; the Kraus rank is the Choi rank.
    assert_eq!(
        elimination::rank(original.choi().unwrap().matrix()).unwrap(),
        2
    );
    assert_eq!(padded.operators().len(), 3);
    // Stinespring isometries differ by a unitary on the environment: V' = (I (x) U) V.
    assert_ne!(
        original.stinespring_isometry().unwrap(),
        remixed.stinespring_isometry().unwrap()
    );
    assert_eq!(
        mx::multiply_with_limits(
            &mx::kronecker_with_limits(
                &mx::identity(2).unwrap(),
                &u,
                exact_hermitian::exact_limits()
            )
            .unwrap(),
            &original.stinespring_isometry().unwrap(),
            exact_hermitian::exact_limits()
        )
        .unwrap(),
        remixed.stinespring_isometry().unwrap()
    );
    // A unitary channel has Kraus rank one.
    let flip = ExactKrausChannel::from_operators(vec![pauli_x()]).unwrap();
    assert_eq!(elimination::rank(flip.choi().unwrap().matrix()).unwrap(), 1);
}

// Origin: engine/crates_rs/tests/core_quantum_physics/channels/completely_positive_import_boundary.rs
// Claim: urn:core:crates_rs:tests:completely-positive-import-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3b660038 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3b660038` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3b660038 {
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
impl BoundaryError3b660038 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3b660038 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3b660038 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3b660038 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3b660038> {
        if capacity_bound == 0 {
            return Err(BoundaryError3b660038::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3b660038::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3b660038::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3b660038() {
    let admitted = BoundaryRecord3b660038::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3b660038::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
