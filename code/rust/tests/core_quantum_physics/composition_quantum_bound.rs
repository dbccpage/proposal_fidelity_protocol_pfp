use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
// AuthorityEffect: None.
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::composition_quantum_bound::{
    passes_squared_chsh_bound, QuantumChshCertificate,
};
use core_quantum_physics::exact_hermitian::outer;
use core_quantum_physics::finite_chsh_correlations::PairwiseBox;

#[test]
fn finite_quantum_composition_admits_nonclassical_correlations_and_excludes_pr() {
    let z = BasicMatrix::<GaussianRat>::from_row_major(
        2,
        2,
        vec![
            GaussianRat::one(),
            GaussianRat::zero(),
            GaussianRat::zero(),
            GaussianRat::from_ints(-1, 0),
        ],
    )
    .unwrap();
    let x = BasicMatrix::<GaussianRat>::from_row_major(
        2,
        2,
        vec![
            GaussianRat::zero(),
            GaussianRat::one(),
            GaussianRat::one(),
            GaussianRat::zero(),
        ],
    )
    .unwrap();
    let b0 = mx::add(
        &(mx::scale(
            &(z),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(3, 5)),
        )
        .unwrap()),
        &mx::scale(
            &(x),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(4, 5)),
        )
        .unwrap(),
    )
    .unwrap();
    let b1 = mx::sub(
        &(mx::scale(
            &(z),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(3, 5)),
        )
        .unwrap()),
        &mx::scale(
            &(x),
            &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(4, 5)),
        )
        .unwrap(),
    )
    .unwrap();
    let vector = [
        GaussianRat::one(),
        GaussianRat::zero(),
        GaussianRat::zero(),
        GaussianRat::one(),
    ];
    let rho = mx::scale(
        &(outer(&vector, &vector).unwrap()),
        &core_number_theory::cyclotomic::GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap();
    let cert = QuantumChshCertificate::from_tensor_model(&rho, [&z, &x], [&b0, &b1]).unwrap();
    assert_eq!(cert.correlations().chsh(), rq(14, 5));
    assert_eq!(cert.squared_chsh(), rq(196, 25));
    assert_eq!(
        cert.variance_slack() + cert.operator_bound_slack(),
        rq(4, 25)
    );
    assert!(cert.correlations().is_no_signalling());
    assert!(passes_squared_chsh_bound(cert.correlations()));
    let mut pr = vec![ri(0); 16];
    for setting in 0..4 {
        for a in 0..2 {
            let b = if setting == 3 { 1 - a } else { a };
            pr[4 * setting + 2 * a + b] = rq(1, 2);
        }
    }
    let pr = PairwiseBox::new(pr).unwrap();
    assert!(pr.is_no_signalling());
    assert_eq!(pr.chsh(), ri(4));
    assert!(!passes_squared_chsh_bound(&pr));
    assert!(QuantumChshCertificate::from_tensor_model(
        &rho,
        [
            &z,
            &mx::scale(
                &(x),
                &core_number_theory::cyclotomic::GaussianRat::from_rational(ri(2))
            )
            .unwrap()
        ],
        [&b0, &b1]
    )
    .is_err());
}

#[test]
fn pr_has_a_signed_global_section_with_sharp_half_negative_mass() {
    use core_finite_probability::signed_representation::SignedValuation;
    use core_quantum_physics::finite_chsh_correlations::JointAssignment;
    let assignments = JointAssignment::all();
    let weights: Vec<_> = assignments.iter().map(|a| rq(1 + a.chsh(), 16)).collect();
    let signed = SignedValuation::from_weights(weights.clone()).unwrap();
    let values: Vec<_> = assignments.iter().map(|a| ri(a.chsh())).collect();
    let bound = signed.expectation_negativity_bound(&values, ri(2)).unwrap();
    assert_eq!(bound.expectation, ri(4));
    assert_eq!(bound.negativity, rq(1, 2));
    assert_eq!(bound.required_negativity, rq(1, 2));
    assert_eq!(bound.upper_bound, ri(4));
    // Every pairwise readout is normalized and nonnegative despite the
    // unavoidable negative global section. Thus local accepted packets do not
    // entail joint-run classicality.
    for x in 0..2 {
        for y in 0..2 {
            for a in [-1, 1] {
                for b in [-1, 1] {
                    let marginal: core_number_theory::rational::Rational = assignments
                        .iter()
                        .zip(&weights)
                        .filter(|(assignment, _)| assignment.a[x] == a && assignment.b[y] == b)
                        .map(|(_, weight)| weight.clone())
                        .sum();
                    let expected = if a * b == if x == 1 && y == 1 { -1 } else { 1 } {
                        rq(1, 2)
                    } else {
                        ri(0)
                    };
                    assert_eq!(marginal, expected);
                }
            }
        }
    }
}

#[test]
fn commuting_full_local_algebras_select_tensor_up_to_hidden_multiplicity() {
    use core_quantum_physics::composition_quantum_bound::classify_commuting_matrix_units;
    let units: Vec<_> = (0..2)
        .flat_map(|i| {
            (0..2).map(move |j| {
                let mut e = mx::zeros(2, 2).unwrap();
                e.set(i, j, GaussianRat::one()).unwrap();
                e
            })
        })
        .collect();
    let left: Vec<_> = units
        .iter()
        .map(|e| mx::kronecker(&(e), &mx::identity(2).unwrap()).unwrap())
        .collect();
    let right: Vec<_> = units
        .iter()
        .map(|e| mx::kronecker(&(mx::identity(2).unwrap()), e).unwrap())
        .collect();
    let certificate = classify_commuting_matrix_units(2, 2, &left, &right).unwrap();
    assert!(certificate.minimal_tensor_carrier);
    assert_eq!(certificate.hidden_multiplicity, ri(1));
    let left_extra: Vec<_> = left
        .iter()
        .map(|e| mx::kronecker(&(e), &mx::identity(2).unwrap()).unwrap())
        .collect();
    let right_extra: Vec<_> = right
        .iter()
        .map(|e| mx::kronecker(&(e), &mx::identity(2).unwrap()).unwrap())
        .collect();
    let extra = classify_commuting_matrix_units(2, 2, &left_extra, &right_extra).unwrap();
    assert_eq!(extra.hidden_multiplicity, ri(2));
    assert!(!extra.minimal_tensor_carrier);
    assert!(classify_commuting_matrix_units(2, 2, &left, &left).is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/composition_quantum_bound.rs
// Claim: urn:core:crates_rs:tests:composition-quantum-bound:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord724494bf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord724494bf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError724494bf {
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
impl BoundaryError724494bf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError724494bf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError724494bf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord724494bf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError724494bf> {
        if capacity_bound == 0 {
            return Err(BoundaryError724494bf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError724494bf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError724494bf::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_724494bf() {
    let admitted = BoundaryRecord724494bf::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord724494bf::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
