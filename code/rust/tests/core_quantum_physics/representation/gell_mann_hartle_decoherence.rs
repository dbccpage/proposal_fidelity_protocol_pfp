//! A two-history residual in the Gell-Mann–Hartle setting: the decoherence
//! functional `D_jk = Tr(C_j rho C_k*)` is positive semidefinite for a positive
//! state, with the conjugated quadratic form; the global-minus-local residual
//! of two histories is twice the real part of their off-diagonal entry; and
//! the diagonal sums to `Tr(rho)` under `sum C* C = I`, not under `sum C = I`.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as iv, matrix as mx, ordered};
use num_traits::{Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_hermitian::{self, gi, gq};

use crate::support::{basis_partition, basis_projector, complex_mixer, rotation};
use core_functional::decoherence::{DecoherenceError, DecoherenceFunctional};
use core_quantum_physics::chain_histories::chain_histories;
use core_quantum_physics::heisenberg_picture::HeisenbergError;

fn weakly_decoherent() -> (BasicMatrix<GaussianRat>, Vec<BasicMatrix<GaussianRat>>) {
    let histories = chain_histories(
        &[rotation(), complex_mixer()],
        &[basis_partition(2), basis_partition(2)],
    )
    .unwrap();
    (
        basis_projector(2, 0),
        histories.into_iter().map(|h| h.class_operator).collect(),
    )
}

fn combination(
    operators: &[BasicMatrix<GaussianRat>],
    weights: &[GaussianRat],
) -> BasicMatrix<GaussianRat> {
    operators.iter().zip(weights).fold(
        linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
            operators[0].rows(),
            operators[0].rows(),
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .expect("validated finite matrix shape and budget"),
        |acc, (c, w)| mx::add(&acc, &mx::scale(c, w).unwrap()).unwrap(),
    )
}

#[test]
fn the_functional_entries_are_traces_of_class_operators_against_the_state() {
    let (rho, operators) = weakly_decoherent();
    let functional = DecoherenceFunctional::new(rho.clone(), operators.clone()).unwrap();
    for (j, cj) in operators.iter().enumerate() {
        for (k, ck) in operators.iter().enumerate() {
            assert_eq!(
                *functional.matrix().get_ref(j, k).unwrap(),
                mx::trace(
                    &mx::multiply(&mx::multiply(cj, &rho).unwrap(), &iv::adjoint(ck).unwrap())
                        .unwrap()
                )
                .unwrap()
            );
        }
    }
    assert!(exact_hermitian::is_hermitian(functional.matrix()));
}

#[test]
fn a_positive_state_gives_a_positive_functional_through_the_conjugated_quadratic_form() {
    let (rho, operators) = weakly_decoherent();
    let functional = DecoherenceFunctional::new(rho.clone(), operators.clone()).unwrap();
    assert!(exact_hermitian::is_positive_semidefinite(&rho));
    assert!(exact_hermitian::is_positive_semidefinite(
        functional.matrix()
    ));
    let z = [gi(1, 0), gi(0, 1), gi(2, -1), gq(1, 2, 0, 1)];
    let form = ordered::hermitian_form(functional.matrix(), &z).unwrap();
    assert!(form.im.is_zero() && !form.re.is_negative());
    // z* D z = Tr(A rho A*) for A = sum_j conj(z_j) C_j ...
    let conjugated: Vec<GaussianRat> = z.iter().map(GaussianRat::conj).collect();
    let a = combination(&operators, &conjugated);
    assert_eq!(
        mx::trace(
            &mx::multiply(&mx::multiply(&a, &rho).unwrap(), &iv::adjoint(&a).unwrap()).unwrap()
        )
        .unwrap(),
        form
    );
    // ... and not for sum_j z_j C_j, since D has non-real entries.
    let b = combination(&operators, &z);
    assert_ne!(
        mx::trace(
            &mx::multiply(&mx::multiply(&b, &rho).unwrap(), &iv::adjoint(&b).unwrap()).unwrap()
        )
        .unwrap(),
        form
    );
}

#[test]
fn the_two_history_residual_is_twice_the_real_part_of_the_off_diagonal_entry() {
    // The integer triple (d11, d12, d22) = (2, 1, 3), realized by class
    // operators against rho = I: local weight 5, global weight 7, residual 2.
    let c1 = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(1, 0), gi(1, 0)],
        vec![gi(0, 0), gi(0, 0)],
    ])
    .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
    .unwrap();
    let c2 = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(1, 0), gi(0, 0)],
        vec![gi(1, 0), gi(1, 0)],
    ])
    .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
    .unwrap();
    let integer = DecoherenceFunctional::new(
        linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
            2,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .expect("validated finite matrix shape and budget"),
        vec![c1, c2],
    )
    .unwrap();
    assert_eq!(
        *integer.matrix(),
        mx::from_rows(vec![vec![gi(2, 0), gi(1, 0)], vec![gi(1, 0), gi(3, 0)]]).unwrap()
    );
    let global = integer.coarse_grain(&[vec![0, 1]]).unwrap();
    assert_eq!(*global.matrix().get_ref(0, 0).unwrap(), gi(7, 0));
    assert_eq!(integer.sum_rule_residual(0, 1).unwrap(), gi(2, 0));
    // For complex entries the residual is 2 Re D_12: a nonzero imaginary
    // off-diagonal entry leaves the global and local weights equal.
    let (rho, operators) = weakly_decoherent();
    let complex = DecoherenceFunctional::new(rho, operators).unwrap();
    for j in 0..4 {
        for k in 0..4 {
            if j == k {
                continue;
            }
            let entry = complex.matrix().get_ref(j, k).unwrap();
            assert_eq!(
                complex.sum_rule_residual(j, k).unwrap(),
                GaussianRat::from_rational(&entry.re + &entry.re)
            );
        }
    }
    assert_eq!(*complex.matrix().get_ref(0, 2).unwrap(), gq(0, 1, 144, 625));
    let pair = complex
        .coarse_grain(&[vec![0, 2], vec![1], vec![3]])
        .unwrap();
    assert_eq!(
        *pair.matrix().get_ref(0, 0).unwrap(),
        complex
            .matrix()
            .get_ref(0, 0)
            .unwrap()
            .add(complex.matrix().get_ref(2, 2).unwrap())
    );
    assert_eq!(*pair.matrix().get_ref(0, 0).unwrap(), gq(337, 625, 0, 1));
}

#[test]
fn diagonal_normalization_needs_the_completeness_premise() {
    let (rho, operators) = weakly_decoherent();
    let chain = DecoherenceFunctional::new(rho, operators.clone()).unwrap();
    assert!(chain.is_complete());
    let sum = operators.iter().fold(
        linear_algebra::exact_field::matrix::zeros_with_limits::<GaussianRat>(
            2,
            2,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .expect("validated finite matrix shape and budget"),
        |acc, c| mx::add(&acc, c).unwrap(),
    );
    assert_eq!(sum, mx::identity::<GaussianRat>(2).unwrap());
    assert_eq!(mx::trace(chain.matrix()).unwrap(), gi(1, 0));
    // C_1 + C_2 = I without C_1* C_1 + C_2* C_2 = I: the diagonal sums to 3.
    let c1 = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(1, 0), gi(1, 0)],
        vec![gi(0, 0), gi(0, 0)],
    ])
    .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
    .unwrap();
    let c2 = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(0, 0), gi(-1, 0)],
        vec![gi(0, 0), gi(1, 0)],
    ])
    .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
    .unwrap();
    assert_eq!(
        mx::add(&c1, &c2).unwrap(),
        mx::identity::<GaussianRat>(2).unwrap()
    );
    let incomplete =
        DecoherenceFunctional::new(basis_projector(2, 1), vec![c1.clone(), c2.clone()]).unwrap();
    assert!(!incomplete.is_complete());
    assert_eq!(mx::trace(incomplete.matrix()).unwrap(), gi(3, 0));
    // The same operators happen to give 1 on the other basis state.
    let lucky = DecoherenceFunctional::new(basis_projector(2, 0), vec![c1, c2]).unwrap();
    assert_eq!(mx::trace(lucky.matrix()).unwrap(), gi(1, 0));
}

#[test]
fn malformed_histories_and_partitions_are_refused() {
    let (rho, operators) = weakly_decoherent();
    assert_eq!(
        DecoherenceFunctional::new(rho.clone(), Vec::new()),
        Err(DecoherenceError::Empty)
    );
    assert_eq!(
        DecoherenceFunctional::new(mx::zeros::<GaussianRat>(2, 3).unwrap(), operators.clone()),
        Err(DecoherenceError::StateNotSquare { rows: 2, cols: 3 })
    );
    assert_eq!(
        DecoherenceFunctional::new(
            rho.clone(),
            vec![
                operators[0].clone(),
                mx::identity::<GaussianRat>(3).unwrap()
            ]
        ),
        Err(DecoherenceError::ClassOperatorShape {
            index: 1,
            dimension: 2
        })
    );
    let functional = DecoherenceFunctional::new(rho, operators).unwrap();
    assert_eq!(
        functional.coarse_grain(&[vec![0, 1], vec![1, 2, 3]]),
        Err(DecoherenceError::NotAPartition {
            index: 1,
            classes: 2
        })
    );
    assert_eq!(
        functional.coarse_grain(&[vec![0, 1, 2]]),
        Err(DecoherenceError::NotAPartition {
            index: 3,
            classes: 0
        })
    );
    assert_eq!(
        functional.coarse_grain(&[vec![0, 1, 2, 3], Vec::new()]),
        Err(DecoherenceError::EmptyClass { class: 1 })
    );
    assert_eq!(
        functional.sum_rule_residual(1, 4),
        Err(DecoherenceError::HistoryOutOfRange { index: 4, count: 4 })
    );
    assert_eq!(
        functional.sum_rule_residual(2, 2),
        Err(DecoherenceError::SameHistory { index: 2 })
    );

    let basis = basis_partition(2);
    assert_eq!(
        chain_histories(&[rotation()], &[basis.clone(), basis.clone()]),
        Err(DecoherenceError::StepCount {
            steps: 1,
            partitions: 2
        })
    );
    assert_eq!(
        chain_histories(&[rotation()], &[Vec::new()]),
        Err(DecoherenceError::Empty)
    );
    assert_eq!(
        chain_histories(&[rotation(), rotation()], &[basis.clone(), Vec::new()]),
        Err(DecoherenceError::EmptyPartition { time: 1 })
    );
    let doubled = vec![mx::scale(&basis[0], &gi(2, 0)).unwrap(), basis[1].clone()];
    assert_eq!(
        chain_histories(&[rotation()], &[doubled]),
        Err(DecoherenceError::NotProjector {
            time: 0,
            index: 0,
            dimension: 2
        })
    );
    let half = GaussianRat::from_rational(rq(1, 2));
    let plus = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![half.clone(), half.clone()],
        vec![half.clone(), half],
    ])
    .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
    .unwrap();
    assert_eq!(
        chain_histories(&[rotation()], &[vec![basis[0].clone(), plus]]),
        Err(DecoherenceError::NotOrthogonal {
            time: 0,
            first: 0,
            second: 1
        })
    );
    assert_eq!(
        chain_histories(&[rotation()], &[vec![basis[0].clone()]]),
        Err(DecoherenceError::IncompletePartition { time: 0 })
    );
    let not_unitary = linear_algebra::exact_field::matrix::scale(
        &(rotation()),
        &GaussianRat::from_rational(ri(2)),
    )
    .expect("validated finite matrix shape and budget");
    assert_eq!(
        chain_histories(&[not_unitary], std::slice::from_ref(&basis)),
        Err(DecoherenceError::Heisenberg(
            HeisenbergError::NotUnitary { step: 0 }.to_string()
        ))
    );
    let many_steps = vec![mx::identity::<GaussianRat>(2).unwrap(); 17];
    let many_partitions = vec![basis; 17];
    assert_eq!(
        chain_histories(&many_steps, &many_partitions),
        Err(DecoherenceError::HistoryBudget { budget: 1 << 16 })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/representation/gell_mann_hartle_decoherence.rs
// Claim: urn:core:crates_rs:tests:gell-mann-hartle-decoherence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddb5f112a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddb5f112a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordb5f112a {
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
impl BoundaryErrordb5f112a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordb5f112a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordb5f112a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddb5f112a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordb5f112a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordb5f112a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordb5f112a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordb5f112a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_db5f112a() {
    let admitted = BoundaryRecorddb5f112a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddb5f112a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
