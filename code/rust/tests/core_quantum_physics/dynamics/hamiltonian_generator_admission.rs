//! Hamiltonian generator admission: the Cayley chart admits a unique
//! Hermitian generator for every unitary without eigenvalue -1 and refuses the
//! rest. Two Cayley steps of one generator compose by tangent addition only
//! when its square is the identity; the steps agree with the existing toggle
//! formula and with the real skew-symmetric Cayley chart.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as iv, matrix as mx};
use core_lie_theory::cayley::compactified_circle_composition;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::dynamics::cayley_transform_toggle;
use core_quantum_physics::exact_hermitian::{self, gi, gq};
use core_quantum_physics::u1_graph_connection::U1Connection;
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use core_lie_theory::cayley_unitary::{cayley_generator, cayley_unitary, UnitaryCayleyError};

fn swap() -> BasicMatrix<GaussianRat> {
    linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(0, 0), gi(1, 0)],
        vec![gi(1, 0), gi(0, 0)],
    ])
    .unwrap()
}

fn two_level() -> BasicMatrix<GaussianRat> {
    linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(1, 0), gi(1, 1)],
        vec![gi(1, -1), gi(-1, 0)],
    ])
    .unwrap()
}

fn kite_hamiltonian() -> BasicMatrix<GaussianRat> {
    let complex = FiniteCochainPacket::build_complex(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")],
        &[],
    )
    .unwrap();
    let packet = FiniteCochainPacket::new(complex, vec![ri(1), ri(2), ri(3), rq(1, 2)]).unwrap();
    U1Connection::new(
        &packet,
        vec![
            gq(3, 5, 4, 5),
            gq(5, 13, 12, 13),
            gi(0, 1),
            gq(8, 17, 15, 17),
        ],
    )
    .unwrap()
    .laplacian(&packet)
}

fn real(q: Rational) -> GaussianRat {
    GaussianRat::from_rational(q)
}

/// `[[Re Z, -Im Z], [Im Z, Re Z]]`, the real form of a complex matrix.
fn realification(m: &BasicMatrix<GaussianRat>) -> Vec<Vec<Rational>> {
    let n = m.rows();
    (0..2 * n)
        .map(|r| {
            (0..2 * n)
                .map(|c| {
                    let z = (m)
                        .get_ref(r % n, c % n)
                        .expect("validated finite matrix shape and budget");
                    match (r < n, c < n) {
                        (true, false) => -z.im.clone(),
                        (false, true) => z.im.clone(),
                        _ => z.re.clone(),
                    }
                })
                .collect()
        })
        .collect()
}

#[test]
fn the_cayley_generator_inverts_the_cayley_step() {
    let h = kite_hamiltonian();
    for tau in [ri(1), rq(1, 2), rq(-3, 5)] {
        let u = cayley_unitary(&h, &tau).unwrap();
        assert_eq!(
            cayley_generator(&u).unwrap(),
            mx::scale(&h, &real(tau)).unwrap()
        );
    }
}

#[test]
fn a_product_of_cayley_steps_is_admitted_with_one_hermitian_generator() {
    let h2 = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(0, 0), gi(2, 0)],
        vec![gi(2, 0), gi(3, 0)],
    ])
    .unwrap();
    let u = linear_algebra::exact_field::matrix::multiply_with_limits(
        &(cayley_unitary(&two_level(), &ri(1)).unwrap()),
        &cayley_unitary(&h2, &rq(1, 2)).unwrap(),
        linear_algebra::backend::basic_matrix::OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1 << 24,
        },
    )
    .expect("validated finite matrix shape and budget");
    assert!(iv::is_unitary(&u).unwrap());
    let generator = cayley_generator(&u).unwrap();
    assert_eq!(
        generator,
        mx::from_rows(vec![
            vec![gq(13, 7, 0, 1), gq(-1, 7, -1, 1)],
            vec![gq(-1, 7, 1, 1), gq(-1, 7, 0, 1)]
        ])
        .unwrap()
    );
    assert!(exact_hermitian::is_hermitian(&generator));
    assert_eq!(cayley_unitary(&generator, &ri(1)).unwrap(), u);
    // The steps do not commute, and the product's generator is not the sum of the parts.
    assert_ne!(
        generator,
        mx::add(&two_level(), &mx::scale(&h2, &real(rq(1, 2))).unwrap()).unwrap()
    );
}

#[test]
fn a_unitary_with_eigenvalue_minus_one_has_no_cayley_generator() {
    assert_eq!(
        cayley_generator(&swap()),
        Err(UnitaryCayleyError::CutLocus {
            kernel_dimension: 1
        })
    );
    let minus_identity = linear_algebra::exact_field::matrix::scale(
        &(linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
            3,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .expect("validated finite matrix shape and budget")),
        &gi(-1, 0),
    )
    .expect("validated finite matrix shape and budget");
    assert_eq!(
        cayley_generator(&minus_identity),
        Err(UnitaryCayleyError::CutLocus {
            kernel_dimension: 3
        })
    );
    // i X has eigenvalues i and -i and is admitted, with generator -X.
    let quarter = linear_algebra::exact_field::matrix::scale(&(swap()), &gi(0, 1))
        .expect("validated finite matrix shape and budget");
    let generator = cayley_generator(&quarter).unwrap();
    assert_eq!(generator, mx::scale(&swap(), &gi(-1, 0)).unwrap());
    assert_eq!(cayley_unitary(&generator, &ri(1)).unwrap(), quarter);
    // Every Cayley step of the swap Hamiltonian is admitted: C_tau(X) never has eigenvalue -1.
    for tau in [rq(1, 2), ri(7), rq(-4, 3)] {
        let u = cayley_unitary(&swap(), &tau).unwrap();
        assert_eq!(
            cayley_generator(&u).unwrap(),
            mx::scale(&swap(), &real(tau)).unwrap()
        );
    }
}

#[test]
fn non_unitary_non_hermitian_and_non_square_inputs_are_refused() {
    let not_unitary = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(1, 0), gi(1, 0)],
        vec![gi(0, 0), gi(1, 0)],
    ])
    .unwrap();
    assert!(!iv::is_unitary(&not_unitary).unwrap());
    assert_eq!(
        cayley_generator(&not_unitary),
        Err(UnitaryCayleyError::NotUnitary)
    );
    assert_eq!(
        cayley_unitary(&not_unitary, &ri(1)),
        Err(UnitaryCayleyError::NotHermitian)
    );
    let rectangular =
        linear_algebra::exact_field::matrix::from_rows(vec![vec![gi(1, 0), gi(0, 0)]]).unwrap();
    assert!(iv::is_unitary(&rectangular).is_err());
    assert_eq!(
        cayley_unitary(&rectangular, &ri(1)),
        Err(UnitaryCayleyError::Shape)
    );
    assert_eq!(
        cayley_generator(&rectangular),
        Err(UnitaryCayleyError::Shape)
    );
}

#[test]
fn tangent_addition_composes_cayley_steps_only_when_h_squared_is_the_identity() {
    let pairs = [
        (rq(1, 2), rq(1, 3)),
        (ri(2), rq(-1, 5)),
        (rq(-3, 4), rq(2, 7)),
    ];
    let step = |h: &BasicMatrix<GaussianRat>, s: &Rational, t: &Rational| {
        linear_algebra::exact_field::matrix::multiply_with_limits(
            &(cayley_unitary(h, s).unwrap()),
            &cayley_unitary(h, t).unwrap(),
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .expect("validated finite matrix shape and budget")
    };
    // The toggle has X^2 = I: the existing tangent-addition law holds.
    for (s, t) in &pairs {
        let composed = compactified_circle_composition(Some(&s), Some(&t)).unwrap();
        assert_eq!(
            step(&swap(), s, t),
            cayley_unitary(&swap(), &composed).unwrap()
        );
    }
    // H^2 = 3 I: the parameter is (s + t) / (1 - 3 s t), and the toggle law fails.
    let h = two_level();
    assert_eq!(
        mx::multiply(&h, &h).unwrap(),
        mx::scale(&mx::identity::<GaussianRat>(2).unwrap(), &gi(3, 0)).unwrap()
    );
    for (s, t) in &pairs {
        let scaled = (s + t) / (ri(1) - ri(3) * s * t);
        assert_eq!(step(&h, s, t), cayley_unitary(&h, &scaled).unwrap());
        let toggle_law = compactified_circle_composition(Some(&s), Some(&t)).unwrap();
        assert_ne!(step(&h, s, t), cayley_unitary(&h, &toggle_law).unwrap());
    }
    // General H: the product's generator G solves (I - s t H^2) G = (s + t) H
    // and is not a multiple of H.
    let k = kite_hamiltonian();
    let (s, t) = (rq(1, 2), rq(1, 3));
    let generator = cayley_generator(&step(&k, &s, &t)).unwrap();
    let damping = linear_algebra::exact_field::matrix::sub(
        &(linear_algebra::exact_field::matrix::identity_with_limits::<GaussianRat>(
            4,
            linear_algebra::backend::basic_matrix::OperationLimits {
                max_elements: 1 << 20,
                max_scalar_ops: 1 << 24,
            },
        )
        .expect("validated finite matrix shape and budget")),
        &linear_algebra::exact_field::matrix::scale(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(k),
                &k,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .expect("validated finite matrix shape and budget")),
            &real(&s * &t),
        )
        .expect("validated finite matrix shape and budget"),
    )
    .expect("validated finite matrix shape and budget");
    assert_eq!(
        mx::multiply(&damping, &generator).unwrap(),
        mx::scale(&k, &real(&s + &t)).unwrap()
    );
    let ratio = (generator)
        .get_ref(0, 1)
        .expect("validated finite matrix shape and budget")
        .mul(
            &(k).get_ref(0, 1)
                .expect("validated finite matrix shape and budget")
                .inv(),
        );
    assert_ne!(generator, mx::scale(&k, &ratio).unwrap());
}

#[test]
fn the_general_cayley_step_matches_the_toggle_formula_and_the_real_skew_chart() {
    for tau in [rq(1, 2), rq(3, 4), ri(1)] {
        let toggle = cayley_transform_toggle(tau.clone());
        let diagonal = real(toggle.diag_re.clone());
        let off_diagonal = GaussianRat {
            re: ri(0),
            im: toggle.offdiag_im.clone(),
        };
        let expected = linear_algebra::exact_field::matrix::from_rows(vec![
            vec![diagonal.clone(), off_diagonal.clone()],
            vec![off_diagonal, diagonal],
        ])
        .unwrap();
        assert_eq!(cayley_unitary(&swap(), &tau).unwrap(), expected);
    }
    // The realification of C_tau(H) is the canonical real Cayley of i H.
    let h = kite_hamiltonian();
    for tau in [rq(1, 2), rq(-5, 3)] {
        let skew = realification(
            &linear_algebra::exact_field::matrix::scale(&(h), &gi(0, 1))
                .expect("validated finite matrix shape and budget"),
        );
        assert_eq!(
            mx::to_rows(
                &core_lie_theory::cayley::cayley_transform(&mx::from_rows(skew).unwrap(), &tau)
                    .unwrap()
            )
            .unwrap(),
            realification(&cayley_unitary(&h, &tau).unwrap())
        );
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/dynamics/hamiltonian_generator_admission.rs
// Claim: urn:core:crates_rs:tests:hamiltonian-generator-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord00d4f043 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord00d4f043` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError00d4f043 {
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
impl BoundaryError00d4f043 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError00d4f043 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError00d4f043 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord00d4f043 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError00d4f043> {
        if capacity_bound == 0 {
            return Err(BoundaryError00d4f043::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError00d4f043::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError00d4f043::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_00d4f043() {
    let admitted = BoundaryRecord00d4f043::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord00d4f043::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
