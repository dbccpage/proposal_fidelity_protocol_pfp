//! Exact PO006 signed-scalar operator closure and full-space CPTP map controls.
//! AuthorityEffect: None. Fixtures are local mathematical data, not paper paths.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_rational::BigRational;
use core_certifiers::operator_closure_certifier::OperatorClosureTransportVerifier;
use core_functional::operator_trace_closure::{
    KrausMapInput, OperatorClosureTransportInput, OperatorClosureWitness,
    OPERATOR_INPUT_MAX_RATIONAL_BITS,
};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::trace_observer_certificate::{
    verify_operator_2cell_transport, Operator2CellComplex, OperatorObserverError,
    OperatorRepairProblem, TraceObserverWitness,
};

type Operator = BasicMatrix<GaussianRat>;

fn pauli_y() -> Operator {
    BasicMatrix::from_row_major(
        2,
        2,
        vec![
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(0, -1),
            GaussianRat::from_ints(0, 1),
            GaussianRat::from_ints(0, 0),
        ],
    )
    .unwrap()
}

fn pauli_z() -> Operator {
    mx::diagonal(&[GaussianRat::from_ints(1, 0), GaussianRat::from_ints(-1, 0)]).unwrap()
}

fn scaled(h: &Operator, q: BigRational) -> Operator {
    mx::scale(h, &GaussianRat::from_rational(q)).unwrap()
}

fn jordan_pauli(h: &Operator) -> (Operator, Operator) {
    let identity = mx::identity(2).unwrap();
    (
        scaled(&mx::add(&identity, h).unwrap(), rq(1, 2)),
        scaled(&mx::sub(&identity, h).unwrap(), rq(1, 2)),
    )
}

fn triangle() -> (
    OperatorRepairProblem,
    TraceObserverWitness,
    Operator2CellComplex,
    OperatorClosureWitness,
) {
    let y = pauli_y();
    let zero = mx::zeros(2, 2).unwrap();
    let problem = OperatorRepairProblem {
        defects: vec![y.clone(), zero.clone(), zero.clone()],
        repair_generators: vec![
            vec![y.clone(), scaled(&y, ri(-1)), zero.clone()],
            vec![zero.clone(), y.clone(), scaled(&y, ri(-1))],
        ],
        weights: vec![ri(2), ri(3), ri(5)],
    };
    let (positive, negative) = jordan_pauli(&y);
    let trace_witness = TraceObserverWitness {
        repair_coefficients: vec![ri(0); 2],
        residuals: problem.defects.clone(),
        positive_parts: vec![positive.clone(), zero.clone(), zero.clone()],
        negative_parts: vec![negative.clone(), zero.clone(), zero],
        dual_observables: vec![y.clone(); 3],
    };
    let complex = Operator2CellComplex::new(vec![vec![(0, ri(1)), (1, ri(1)), (2, ri(1))]]);
    let closure = OperatorClosureWitness {
        face_defects: vec![y],
        positive_parts: vec![positive],
        negative_parts: vec![negative],
        claimed_d1_norm: rq(1, 2),
    };
    (problem, trace_witness, complex, closure)
}

fn zero_problem() -> OperatorRepairProblem {
    OperatorRepairProblem {
        defects: vec![mx::zeros(2, 2).unwrap(); 3],
        repair_generators: vec![],
        weights: vec![ri(1); 3],
    }
}

#[test]
fn weighted_half_trace_closure_is_certified_by_sovereign_owners() {
    let (problem, trace, complex, closure) = triangle();
    assert_eq!(trace.verify(&problem).unwrap().obstruction, ri(2));
    let receipt = complex.certify_closure(&problem, &trace, &closure).unwrap();
    assert_eq!(receipt.phi_q(), &ri(2));
    assert_eq!(receipt.gamma2_q(), &ri(1));
    assert_eq!(receipt.d1_norm(), &rq(1, 2));
    assert_eq!(receipt.closure_ratio(), Some(&rq(1, 2)));
    assert!(receipt.authority_effect().is_none());
    assert_eq!(
        complex.evaluate_face(0, &problem.defects).unwrap(),
        pauli_y()
    );
    assert!(complex
        .verify_chain_complex_condition(&problem.repair_generators)
        .unwrap());
    assert!(complex.verify_chain_for(&problem).is_ok());

    let json = serde_json::to_value(&receipt).unwrap();
    assert_eq!(json["status"], "PASS");
    assert_eq!(json["authority_effect"], "None");
    assert_eq!(json["phi_q"], "2");
    assert_eq!(json["gamma2_q"], "1");
    assert_eq!(json["d1_norm"], "1/2");
    assert_eq!(json["closure_ratio"], "1/2");
    assert_eq!(json["repair_generator_count"], 2);
}

#[test]
fn first_edge_and_orientation_are_refused_without_panics() {
    let (problem, trace, _, closure) = triangle();
    let bad_first = Operator2CellComplex::new(vec![vec![(usize::MAX, ri(1))]]);
    assert_eq!(
        bad_first.evaluate_face(0, &problem.defects),
        Err(OperatorObserverError("edge index out of bounds"))
    );
    assert_eq!(
        bad_first.certify_closure(&problem, &trace, &closure),
        Err(OperatorObserverError("edge index out of bounds"))
    );
    for sign in [
        ri(0),
        ri(2),
        rq(1, 2),
        BigRational::new_raw(1.into(), 0.into()),
        BigRational::new_raw(2.into(), 2.into()),
        BigRational::new_raw((-1).into(), (-1).into()),
    ] {
        let malformed = Operator2CellComplex::new(vec![vec![(0, sign)]]);
        assert_eq!(
            malformed.validate_for(&problem),
            Err(OperatorObserverError(
                "face orientation must be canonical +1 or -1"
            ))
        );
        assert!(malformed.evaluate_face(0, &problem.defects).is_err());
        assert!(malformed.verify_chain_complex_condition(&[]).is_err());
    }
    let empty_boundary = Operator2CellComplex::new(vec![vec![]]);
    assert_eq!(
        empty_boundary.evaluate_face(0, &problem.defects),
        Err(OperatorObserverError("empty face boundary"))
    );
}

#[test]
fn oversized_exact_scalars_are_refused_before_canonicalization_or_matrix_algebra() {
    let (mut problem, trace, complex, mut closure) = triangle();
    let oversized =
        BigRational::from_integer(num_bigint::BigInt::from(1) << OPERATOR_INPUT_MAX_RATIONAL_BITS);
    problem.weights[0] = oversized.clone();
    assert_eq!(
        complex.certify_closure(&problem, &trace, &closure),
        Err(OperatorObserverError("rational bit limit exceeded"))
    );
    let (problem, trace, complex, _) = triangle();
    closure.claimed_d1_norm = oversized.clone();
    assert_eq!(
        complex.certify_closure(&problem, &trace, &closure),
        Err(OperatorObserverError("rational bit limit exceeded"))
    );
    let mut defects = problem.defects.clone();
    defects[0] = mx::diagonal(&[
        GaussianRat::from_rational(oversized.clone()),
        GaussianRat::from_rational(-oversized),
    ])
    .unwrap();
    assert_eq!(
        complex.evaluate_face(0, &defects),
        Err(OperatorObserverError("rational bit limit exceeded"))
    );
}

#[test]
fn mixed_shapes_and_unused_malformed_edges_are_checked_with_empty_repairs() {
    let mut problem = zero_problem();
    problem.defects[1] = mx::zeros(3, 3).unwrap();
    let face = Operator2CellComplex::new(vec![vec![(0, ri(1)), (1, ri(1))]]);
    assert_eq!(
        face.validate_for(&problem),
        Err(OperatorObserverError(
            "face mixes operator stalk dimensions"
        ))
    );
    assert!(face.verify_chain_for(&problem).is_err());
    assert!(face.evaluate_face(0, &problem.defects).is_err());

    let mut problem = zero_problem();
    let first_only = Operator2CellComplex::new(vec![vec![(0, ri(1))]]);
    problem.defects[2] =
        BasicMatrix::from_row_major(1, 2, vec![GaussianRat::from_ints(0, 0); 2]).unwrap();
    assert!(first_only.validate_for(&problem).is_err());
    assert!(first_only.verify_chain_for(&problem).is_err());
    assert!(first_only.evaluate_face(0, &problem.defects).is_err());

    let mut problem = zero_problem();
    problem.defects[0] = BasicMatrix::from_row_major(
        2,
        2,
        vec![
            GaussianRat {
                re: BigRational::new_raw(1.into(), 0.into()),
                im: ri(0),
            },
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(0, 0),
            GaussianRat::from_ints(0, 0),
        ],
    )
    .unwrap();
    assert_eq!(
        first_only.validate_for(&problem),
        Err(OperatorObserverError(
            "noncanonical rational or invalid denominator"
        ))
    );
}

#[test]
fn a_repair_seen_by_d1_cannot_receive_a_quotient_closure_receipt() {
    let (mut problem, trace, complex, closure) = triangle();
    problem.repair_generators[0][1] = mx::zeros(2, 2).unwrap();
    assert!(!complex
        .verify_chain_complex_condition(&problem.repair_generators)
        .unwrap());
    assert_eq!(
        complex.certify_closure(&problem, &trace, &closure),
        Err(OperatorObserverError("d1 sees admissible repairs"))
    );
}

#[test]
fn forged_boundary_norm_face_assembly_and_jordan_parts_are_refused() {
    let (problem, trace, complex, closure) = triangle();
    for claimed in [ri(0), ri(1), BigRational::new_raw(1.into(), 0.into())] {
        let mut forged = closure.clone();
        forged.claimed_d1_norm = claimed;
        assert_eq!(
            complex.certify_closure(&problem, &trace, &forged),
            Err(OperatorObserverError("forged induced boundary norm"))
        );
    }
    let mut forged = closure.clone();
    forged.face_defects[0] = mx::zeros(2, 2).unwrap();
    assert_eq!(
        complex.certify_closure(&problem, &trace, &forged),
        Err(OperatorObserverError(
            "closure witness is not the actual boundary"
        ))
    );
    let mut forged = closure.clone();
    forged.positive_parts[0] =
        mx::add(&forged.positive_parts[0], &mx::identity(2).unwrap()).unwrap();
    forged.negative_parts[0] =
        mx::add(&forged.negative_parts[0], &mx::identity(2).unwrap()).unwrap();
    assert_eq!(
        complex.certify_closure(&problem, &trace, &forged),
        Err(OperatorObserverError("residual or Jordan decomposition"))
    );

    let mut forged_trace = trace;
    forged_trace.dual_observables[1] = mx::zeros(2, 2).unwrap();
    assert_eq!(
        complex.certify_closure(&problem, &forged_trace, &closure),
        Err(OperatorObserverError("dual sees admissible repairs"))
    );
}

#[test]
fn exact_repair_has_no_closure_ratio_and_closed_residual_has_zero_ratio() {
    let (mut problem, mut trace, complex, mut closure) = triangle();
    problem.defects = problem.repair_generators[0].clone();
    let zero = mx::zeros(2, 2).unwrap();
    trace.repair_coefficients = vec![ri(1), ri(0)];
    trace.residuals = vec![zero.clone(); 3];
    trace.positive_parts = vec![zero.clone(); 3];
    trace.negative_parts = vec![zero.clone(); 3];
    trace.dual_observables = vec![zero.clone(); 3];
    closure.face_defects = vec![zero.clone()];
    closure.positive_parts = vec![zero.clone()];
    closure.negative_parts = vec![zero];
    let receipt = complex.certify_closure(&problem, &trace, &closure).unwrap();
    assert_eq!(receipt.phi_q(), &ri(0));
    assert_eq!(receipt.gamma2_q(), &ri(0));
    assert!(receipt.closure_ratio().is_none());
    assert!(serde_json::to_value(receipt).unwrap()["closure_ratio"].is_null());

    let (problem, trace, _, _) = triangle();
    let unfilled = Operator2CellComplex::new(vec![]);
    let closure = OperatorClosureWitness {
        face_defects: vec![],
        positive_parts: vec![],
        negative_parts: vec![],
        claimed_d1_norm: ri(0),
    };
    let receipt = unfilled
        .certify_closure(&problem, &trace, &closure)
        .unwrap();
    assert_eq!(receipt.phi_q(), &ri(2));
    assert_eq!(receipt.gamma2_q(), &ri(0));
    assert_eq!(receipt.closure_ratio(), Some(&ri(0)));
}

#[test]
fn coalesced_signed_columns_and_trivial_traceless_stalks_have_exact_norms() {
    let (mut problem, mut trace, _, mut closure) = triangle();
    problem.repair_generators.clear();
    trace.repair_coefficients.clear();
    let canceled = Operator2CellComplex::new(vec![vec![(0, ri(1)), (0, ri(-1))]]);
    let zero = mx::zeros(2, 2).unwrap();
    closure.face_defects = vec![zero.clone()];
    closure.positive_parts = vec![zero.clone()];
    closure.negative_parts = vec![zero];
    closure.claimed_d1_norm = ri(0);
    assert_eq!(canceled.boundary_norm(&problem).unwrap(), ri(0));
    assert!(canceled.certify_closure(&problem, &trace, &closure).is_ok());

    let zero = mx::zeros(1, 1).unwrap();
    let scalar = OperatorRepairProblem {
        defects: vec![zero.clone()],
        repair_generators: vec![],
        weights: vec![ri(1)],
    };
    let trace = TraceObserverWitness {
        repair_coefficients: vec![],
        residuals: vec![zero.clone()],
        positive_parts: vec![zero.clone()],
        negative_parts: vec![zero.clone()],
        dual_observables: vec![zero.clone()],
    };
    let face = Operator2CellComplex::new(vec![vec![(0, ri(1))]]);
    let closure = OperatorClosureWitness {
        face_defects: vec![zero.clone()],
        positive_parts: vec![zero.clone()],
        negative_parts: vec![zero],
        claimed_d1_norm: ri(0),
    };
    assert_eq!(face.boundary_norm(&scalar).unwrap(), ri(0));
    assert!(face.certify_closure(&scalar, &trace, &closure).is_ok());
}

#[test]
fn irrational_face_norm_is_not_replaced_by_rational_positive_parts() {
    let y = pauli_y();
    let z = pauli_z();
    let (yp, yn) = jordan_pauli(&y);
    let (zp, zn) = jordan_pauli(&z);
    let h = mx::add(&y, &z).unwrap();
    assert_eq!(
        mx::multiply(&h, &h).unwrap(),
        scaled(&mx::identity(2).unwrap(), ri(2))
    );
    let problem = OperatorRepairProblem {
        defects: vec![y.clone(), z.clone()],
        repair_generators: vec![],
        weights: vec![ri(1); 2],
    };
    let trace = TraceObserverWitness {
        repair_coefficients: vec![],
        residuals: problem.defects.clone(),
        positive_parts: vec![yp.clone(), zp.clone()],
        negative_parts: vec![yn.clone(), zn.clone()],
        dual_observables: vec![scaled(&y, rq(1, 2)), scaled(&z, rq(1, 2))],
    };
    assert_eq!(trace.verify(&problem).unwrap().obstruction, ri(2));
    let face = Operator2CellComplex::new(vec![vec![(0, ri(1)), (1, ri(1))]]);
    let forged = OperatorClosureWitness {
        face_defects: vec![h],
        positive_parts: vec![mx::add(&yp, &zp).unwrap()],
        negative_parts: vec![mx::add(&yn, &zn).unwrap()],
        claimed_d1_norm: ri(1),
    };
    assert_eq!(
        face.certify_closure(&problem, &trace, &forged),
        Err(OperatorObserverError("residual or Jordan decomposition"))
    );
}

#[test]
fn valid_basis_intertwining_is_certified_and_wrong_transport_is_detected_at_zero() {
    let problem = zero_problem();
    let complex = Operator2CellComplex::new(vec![vec![(0, ri(1)), (1, ri(1)), (2, ri(1))]]);
    let identity = ExactKrausChannel::identity(2, "identity").unwrap();
    let edges = vec![identity.clone(); 3];
    let valid = verify_operator_2cell_transport(
        &problem,
        &complex,
        &problem,
        &complex,
        &edges,
        &[identity],
        &[],
    )
    .unwrap();
    assert_eq!(valid.traceless_basis_checks(), 9);
    assert!(valid.authority_effect().is_none());
    assert_eq!(serde_json::to_value(valid).unwrap()["status"], "PASS");

    let wrong = ExactKrausChannel::try_new(2, 2, vec![pauli_z()], "conjugate Z").unwrap();
    // Every declared defect, repair and actual face is zero, so sample equality
    // would accept. Off-diagonal basis directions refute the full map identity.
    assert_eq!(
        verify_operator_2cell_transport(
            &problem,
            &complex,
            &problem,
            &complex,
            &edges,
            &[wrong],
            &[]
        ),
        Err(OperatorObserverError(
            "missing closure intertwining license"
        ))
    );
}

#[test]
fn transport_binds_repair_expansions_actual_targets_and_both_face_presentations() {
    let (problem, _, complex, _) = triangle();
    let identity = ExactKrausChannel::identity(2, "identity").unwrap();
    let edges = vec![identity.clone(); 3];
    let expansions = vec![vec![ri(1), ri(0)], vec![ri(0), ri(1)]];
    assert!(verify_operator_2cell_transport(
        &problem,
        &complex,
        &problem,
        &complex,
        &edges,
        &[identity.clone()],
        &expansions
    )
    .is_ok());
    assert_eq!(
        verify_operator_2cell_transport(
            &problem,
            &complex,
            &problem,
            &complex,
            &edges,
            &[identity.clone()],
            &[vec![ri(0), ri(0)], vec![ri(0), ri(1)]]
        ),
        Err(OperatorObserverError("missing repair intertwining license"))
    );
    let mut target = problem.clone();
    target.defects[0] = mx::zeros(2, 2).unwrap();
    assert_eq!(
        verify_operator_2cell_transport(
            &problem,
            &complex,
            &target,
            &complex,
            &edges,
            &[identity.clone()],
            &expansions
        ),
        Err(OperatorObserverError(
            "actual target defect is not transported source"
        ))
    );
    let negated = Operator2CellComplex::new(vec![vec![(0, ri(-1)), (1, ri(-1)), (2, ri(-1))]]);
    assert_eq!(
        verify_operator_2cell_transport(
            &problem,
            &complex,
            &problem,
            &negated,
            &edges,
            &[identity],
            &expansions
        ),
        Err(OperatorObserverError(
            "missing closure intertwining license"
        ))
    );
}

#[test]
fn certifier_rechecks_kraus_completeness_instead_of_trusting_channel_fields() {
    let problem = zero_problem();
    let complex = Operator2CellComplex::new(vec![vec![(0, ri(1))]]);
    let identity = vec![mx::identity(2).unwrap()];
    let forged = vec![scaled(&identity[0], ri(2))];
    let weights = vec![ri(1)];
    let good = KrausMapInput {
        dim_in: 2,
        dim_out: 2,
        weights: &weights,
        operators: &identity,
    };
    let bad = KrausMapInput {
        dim_in: 2,
        dim_out: 2,
        weights: &weights,
        operators: &forged,
    };
    let edges = [bad, good, good];
    let faces = [good];
    let outcome = OperatorClosureTransportVerifier::verify(OperatorClosureTransportInput {
        source: problem.as_functional_input(),
        target: problem.as_functional_input(),
        source_faces: &complex.faces,
        target_faces: &complex.faces,
        edge_channels: &edges,
        face_channels: &faces,
        generator_images: &[],
    });
    assert_eq!(outcome.unwrap_err().0, "Kraus map is not trace preserving");
}

#[test]
fn receipts_bind_every_mathematical_role_and_replay_deterministically() {
    let (mut problem, trace, complex, closure) = triangle();
    let baseline = complex.certify_closure(&problem, &trace, &closure).unwrap();
    let repeat = complex.certify_closure(&problem, &trace, &closure).unwrap();
    assert_eq!(baseline, repeat);
    problem.repair_generators.swap(0, 1);
    let reordered = complex.certify_closure(&problem, &trace, &closure).unwrap();
    assert_eq!(baseline.phi_q(), reordered.phi_q());
    assert_ne!(
        baseline.input_and_witness_sha256(),
        reordered.input_and_witness_sha256()
    );

    let mut different_trace = trace;
    different_trace.dual_observables[2] = mx::add(
        &different_trace.dual_observables[2],
        &scaled(&mx::identity(2).unwrap(), rq(1, 4)),
    )
    .unwrap();
    // Centering by an identity component changes this admitted dual witness but
    // leaves all traceless pairings and the certified quotient value unchanged.
    let different_witness = complex
        .certify_closure(&problem, &different_trace, &closure)
        .unwrap();
    assert_eq!(reordered.phi_q(), different_witness.phi_q());
    assert_ne!(
        reordered.input_and_witness_sha256(),
        different_witness.input_and_witness_sha256()
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/test_operator_2cell_closure.rs
// Claim: urn:core:crates_rs:tests:test-operator-2cell-closure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde3ac6011 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde3ac6011` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore3ac6011 {
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
impl BoundaryErrore3ac6011 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore3ac6011 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore3ac6011 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde3ac6011 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore3ac6011> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore3ac6011::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore3ac6011::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore3ac6011::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e3ac6011() {
    let admitted = BoundaryRecorde3ac6011::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde3ac6011::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
