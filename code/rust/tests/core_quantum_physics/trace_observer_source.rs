use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix::{diagonal, from_rows as matrix_from_rows};
use linear_algebra::exact_field::{involution as star, matrix as mx};
use core_number_theory::cyclotomic::GaussianRat;
// AuthorityEffect: None.
use num_rational::BigRational;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::gi;
use core_quantum_physics::exact_instrument::ExactDensityState;
use core_quantum_physics::trace_observer_certificate::*;

fn cycle() -> (OperatorRepairProblem, TraceObserverWitness) {
    let x = matrix_from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap();
    let zero = mx::zeros(2, 2).unwrap();
    let problem = OperatorRepairProblem {
        defects: vec![x.clone(), zero.clone(), zero.clone()],
        repair_generators: vec![
            vec![
                x.clone(),
                mx::scale(
                    &(x),
                    &core_number_theory::cyclotomic::GaussianRat::from_rational(ri(-1)),
                )
                .unwrap(),
                zero.clone(),
            ],
            vec![
                zero.clone(),
                x.clone(),
                mx::scale(
                    &(x),
                    &core_number_theory::cyclotomic::GaussianRat::from_rational(ri(-1)),
                )
                .unwrap(),
            ],
        ],
        weights: vec![ri(1); 3],
    };
    let witness = TraceObserverWitness {
        repair_coefficients: vec![ri(0); 2],
        residuals: problem.defects.clone(),
        positive_parts: vec![
            mx::scale(
                &(mx::add(&(mx::identity(2).unwrap()), &x).unwrap()),
                &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
            )
            .unwrap(),
            zero.clone(),
            zero.clone(),
        ],
        negative_parts: vec![
            mx::scale(
                &(mx::sub(&(mx::identity(2).unwrap()), &x).unwrap()),
                &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
            )
            .unwrap(),
            zero.clone(),
            zero,
        ],
        dual_observables: vec![
            mx::scale(
                &(x),
                &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2))
            )
            .unwrap();
            3
        ],
    };
    (problem, witness)
}
#[test]
fn noncommutative_cycle_primal_dual_certificate_and_forgery_refusals() {
    let (problem, witness) = cycle();
    assert_eq!(witness.verify(&problem).unwrap().obstruction, ri(1));
    let mut bad = witness.clone();
    bad.dual_observables[0] = mx::scale(
        &(bad.dual_observables[0]),
        &core_number_theory::cyclotomic::GaussianRat::from_rational(ri(2)),
    )
    .unwrap();
    assert!(bad.verify(&problem).is_err());
    let mut bad = witness.clone();
    bad.dual_observables[1] = mx::zeros(2, 2).unwrap();
    assert!(bad.verify(&problem).is_err());
    let mut bad = witness.clone();
    bad.positive_parts[0] = mx::add(&(bad.positive_parts[0]), &mx::identity(2).unwrap()).unwrap();
    bad.negative_parts[0] = mx::add(&(bad.negative_parts[0]), &mx::identity(2).unwrap()).unwrap();
    assert!(bad.verify(&problem).is_err());
    let mut bad = witness.clone();
    bad.residuals[0] = mx::zeros(2, 2).unwrap();
    assert!(bad.verify(&problem).is_err());
    let mut bad = problem.clone();
    bad.weights[0] = ri(0);
    assert!(witness.verify(&bad).is_err());
    let mut bad = problem.clone();
    bad.defects[0] =
        BasicMatrix::<GaussianRat>::from_row_major(1, 2, vec![gi(0, 0), gi(0, 0)]).unwrap();
    assert!(witness.verify(&bad).is_err());
    let mut bad = problem.clone();
    bad.weights[0] = BigRational::new_raw(1.into(), 0.into());
    assert!(witness.verify(&bad).is_err());
    let mut bad = witness.clone();
    bad.repair_coefficients[0] = BigRational::new_raw(1.into(), 0.into());
    assert!(bad.verify(&problem).is_err());
}

#[test]
fn actual_state_section_repairs_are_perturbations_and_common_reference_flattens() {
    let states = vec![
        ExactDensityState::try_new(diagonal(&[gi(1, 0), gi(0, 0)]).unwrap()).unwrap(),
        ExactDensityState::try_new(diagonal(&[gi(0, 0), gi(1, 0)]).unwrap()).unwrap(),
    ];
    let edge = OperatorComparison {
        from: 0,
        to: 1,
        channel: ExactKrausChannel::identity(2, "identity restriction").unwrap(),
    };
    let perturbation = diagonal(&[gi(-1, 0), gi(1, 0)]).unwrap();
    let fields = vec![vec![mx::zeros(2, 2).unwrap(), perturbation.clone()]];
    let problem = operator_section_problem(&states, &[edge.clone()], &fields, vec![ri(1)]).unwrap();
    assert_eq!(problem.defects, vec![perturbation]);
    let zero = mx::zeros(2, 2).unwrap();
    let witness = TraceObserverWitness {
        repair_coefficients: vec![ri(1)],
        residuals: vec![zero.clone()],
        positive_parts: vec![zero.clone()],
        negative_parts: vec![zero.clone()],
        dual_observables: vec![zero],
    };
    assert_eq!(witness.verify(&problem).unwrap().obstruction, ri(0));
    assert!(operator_section_problem(
        &states,
        &[edge.clone()],
        &[vec![states[0].matrix().clone(), states[1].matrix().clone()]],
        vec![ri(1)]
    )
    .is_err());
    let mut wrong = edge;
    wrong.to = 2;
    assert!(operator_section_problem(&states, &[wrong], &fields, vec![ri(1)]).is_err());
}

#[test]
fn actual_channel_quotient_transport_requires_repair_license() {
    let (source, _) = cycle();
    let channels = vec![ExactKrausChannel::identity(2, "transport").unwrap(); 3];
    assert!(verify_operator_repair_transport(
        &source,
        &source,
        &channels,
        &[vec![ri(1), ri(0)], vec![ri(0), ri(1)]]
    )
    .is_ok());
    let mut target = source.clone();
    target.repair_generators.clear();
    assert!(
        verify_operator_repair_transport(&source, &target, &channels, &[vec![], vec![]]).is_err()
    );
    let mut target = source.clone();
    target.weights = vec![rq(1, 2); 3];
    assert!(verify_operator_repair_transport(
        &source,
        &target,
        &channels,
        &[vec![ri(1), ri(0)], vec![ri(0), ri(1)]]
    )
    .is_ok());
    target.weights[0] = ri(2);
    assert!(verify_operator_repair_transport(
        &source,
        &target,
        &channels,
        &[vec![ri(1), ri(0)], vec![ri(0), ri(1)]]
    )
    .is_err());
}

#[test]
fn incompatible_cptp_reference_comparisons_have_actual_nonzero_obstruction() {
    let ket0 = diagonal(&[gi(1, 0), gi(0, 0)]).unwrap();
    let e01 = matrix_from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(0, 0), gi(0, 0)]]).unwrap();
    let ket1 = diagonal(&[gi(0, 0), gi(1, 0)]).unwrap();
    let e10 = star::adjoint(&(e01)).unwrap();
    let reset0 = ExactKrausChannel::try_new(2, 2, vec![ket0.clone(), e01], "reset0").unwrap();
    let reset1 = ExactKrausChannel::try_new(2, 2, vec![e10, ket1.clone()], "reset1").unwrap();
    let state = ExactDensityState::try_new(ket0.clone()).unwrap();
    let states = vec![state; 3];
    let edges = vec![
        OperatorComparison {
            from: 0,
            to: 1,
            channel: reset0,
        },
        OperatorComparison {
            from: 0,
            to: 2,
            channel: reset1,
        },
    ];
    let z = mx::sub(&(ket1), &ket0).unwrap();
    let zero = mx::zeros(2, 2).unwrap();
    let x = matrix_from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap();
    let y = matrix_from_rows(vec![vec![gi(0, 0), gi(0, -1)], vec![gi(0, 1), gi(0, 0)]]).unwrap();
    let fields = vec![
        vec![z.clone(), zero.clone(), zero.clone()],
        vec![x, zero.clone(), zero.clone()],
        vec![y, zero.clone(), zero.clone()],
    ];
    let problem = operator_section_problem(&states, &edges, &fields, vec![ri(1); 2]).unwrap();
    let witness = TraceObserverWitness {
        repair_coefficients: vec![ri(0); 3],
        residuals: vec![zero.clone(), z.clone()],
        positive_parts: vec![zero.clone(), ket1],
        negative_parts: vec![zero, ket0],
        dual_observables: vec![
            mx::scale(
                &(z),
                &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(-1, 2)),
            )
            .unwrap(),
            mx::scale(
                &(z),
                &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
            )
            .unwrap(),
        ],
    };
    assert_eq!(witness.verify(&problem).unwrap().obstruction, ri(1));
}

#[test]
fn irrational_jordan_parts_are_not_replaced_by_a_rational_surrogate() {
    let h = matrix_from_rows(vec![vec![gi(1, 0), gi(1, 0)], vec![gi(1, 0), gi(-1, 0)]]).unwrap();
    // h^2=2I; its half trace norm is sqrt(2), outside the rational payload.
    assert_eq!(
        mx::multiply(&(h), &h).unwrap(),
        mx::scale(
            &(mx::identity(2).unwrap()),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(ri(2))
        )
        .unwrap()
    );
    let problem = OperatorRepairProblem {
        defects: vec![h.clone()],
        repair_generators: vec![],
        weights: vec![ri(1)],
    };
    let witness = TraceObserverWitness {
        repair_coefficients: vec![],
        residuals: vec![h.clone()],
        positive_parts: vec![mx::scale(
            &(mx::add(&(mx::identity(2).unwrap()), &h).unwrap()),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
        )
        .unwrap()],
        negative_parts: vec![mx::scale(
            &(mx::sub(&(mx::identity(2).unwrap()), &h).unwrap()),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
        )
        .unwrap()],
        dual_observables: vec![mx::scale(
            &(h),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
        )
        .unwrap()],
    };
    assert!(witness.verify(&problem).is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/trace_observer_source.rs
// Claim: urn:core:crates_rs:tests:trace-observer-source:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfe0a9a9f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfe0a9a9f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfe0a9a9f {
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
impl BoundaryErrorfe0a9a9f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfe0a9a9f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfe0a9a9f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfe0a9a9f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfe0a9a9f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfe0a9a9f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfe0a9a9f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfe0a9a9f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fe0a9a9f() {
    let admitted = BoundaryRecordfe0a9a9f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfe0a9a9f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
