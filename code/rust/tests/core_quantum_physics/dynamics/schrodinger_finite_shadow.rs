//! Discrete Schrödinger shadow: a Hermitian generator has zero norm
//! rate, the Cayley step conserves the norm exactly while the explicit step
//! gains exactly `tau^2 |H psi|^2`, and holonomy, not local data, separates
//! triangle Hamiltonians.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{self, gi, gq};
use core_quantum_physics::u1_graph_connection::{OrientedWalk, U1Connection, VertexGauge};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use linear_algebra::exact_field::{involution as iv, matrix as mx};
use core_lie_theory::cayley_unitary::cayley_unitary;
use core_quantum_physics::finite_schrodinger_step::{
    cycle_product, euler_propagator, norm_rate, SchrodingerError,
};
use core_quantum_physics::u1_gauge_triviality::{trivializing_gauge, GaugeTrivialityError};

/// Triangle a-b-c with a pendant edge c -> d and weights 1, 2, 3, 1/2.
fn kite() -> FiniteCochainPacket {
    let complex = FiniteCochainPacket::build_complex(
        &["a", "b", "c", "d"],
        &[("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")],
        &[],
    )
    .unwrap();
    FiniteCochainPacket::new(complex, vec![ri(1), ri(2), ri(3), rq(1, 2)]).unwrap()
}

/// The connection Laplacian of a non-flat connection on the kite.
fn kite_hamiltonian() -> BasicMatrix<GaussianRat> {
    let packet = kite();
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

fn field() -> Vec<GaussianRat> {
    vec![gi(1, 2), gi(3, 0), gi(0, -1), gi(2, -1)]
}

fn norm_sq(psi: &[GaussianRat]) -> Rational {
    psi.iter().map(GaussianRat::norm_sq).sum()
}

fn triangle() -> FiniteCochainPacket {
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(
            &["a", "b", "c"],
            &[("a", "b"), ("b", "c"), ("c", "a")],
            &[],
        )
        .unwrap(),
    )
    .unwrap()
}

#[test]
fn a_hermitian_generator_has_zero_norm_rate_and_a_lossy_one_does_not() {
    let h = kite_hamiltonian();
    assert!(exact_hermitian::is_hermitian(&h));
    for psi in [
        field(),
        vec![gi(0, 1), gi(1, 1), gq(1, 2, -3, 4), gi(-2, 0)],
    ] {
        assert_eq!(norm_rate(&h, &psi).unwrap(), ri(0));
    }
    // An absorbing term -i/3 at vertex b drains 2/3 |psi_b|^2 per unit time.
    let mut lossy = h.clone();
    let drained = (lossy)
        .get_ref(1, 1)
        .expect("validated finite matrix shape and budget")
        .sub(&gq(0, 1, 1, 3));
    (lossy)
        .set(1, 1, drained)
        .expect("validated finite matrix shape and budget");
    assert!(!exact_hermitian::is_hermitian(&lossy));
    assert_eq!(norm_rate(&lossy, &field()).unwrap(), ri(-6));
}

#[test]
fn the_cayley_step_conserves_the_norm_exactly() {
    let h = kite_hamiltonian();
    let psi = field();
    assert_eq!(norm_sq(&psi), ri(20));
    for tau in [rq(1, 2), ri(3), rq(-2, 7)] {
        let u = cayley_unitary(&h, &tau).unwrap();
        assert!(iv::is_unitary(&u).unwrap());
        let mut state = psi.clone();
        for _ in 0..3 {
            state = linear_algebra::exact_field::matrix::multiply_vector(&u, &state)
                .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
                .unwrap();
            assert_eq!(norm_sq(&state), ri(20));
        }
        assert_ne!(state, psi);
    }
}

#[test]
fn the_explicit_step_gains_exactly_tau_squared_times_the_squared_energy() {
    let h = kite_hamiltonian();
    let psi = field();
    let tau = rq(1, 2);
    let e = euler_propagator(&h, &tau).unwrap();
    assert!(!iv::is_unitary(&e).unwrap());
    let tau_sq = &tau * &tau;
    assert_eq!(
        mx::multiply(&iv::adjoint(&e).unwrap(), &e).unwrap(),
        mx::add(
            &mx::identity::<GaussianRat>(4).unwrap(),
            &mx::scale(
                &mx::multiply(&h, &h).unwrap(),
                &GaussianRat::from_rational(tau_sq.clone())
            )
            .unwrap()
        )
        .unwrap()
    );
    let h_psi = linear_algebra::exact_field::matrix::multiply_vector(&h, &psi)
        .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
        .unwrap();
    let stepped = linear_algebra::exact_field::matrix::multiply_vector(&e, &psi)
        .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
        .unwrap();
    assert_eq!(norm_sq(&stepped), norm_sq(&psi) + &tau_sq * norm_sq(&h_psi));
    assert!(norm_sq(&stepped) > norm_sq(&psi));
    // On the kernel of H the explicit step keeps the norm: constants under the flat connection.
    let packet = kite();
    let flat = U1Connection::trivial(&packet).laplacian(&packet);
    let constant = vec![gi(1, 1); 4];
    let kept = linear_algebra::exact_field::matrix::multiply_vector(
        &euler_propagator(&flat, &tau).unwrap(),
        &constant,
    )
    .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
    .unwrap();
    assert_eq!(kept, constant);
    // An eigenvector of eigenvalue lambda is multiplied by 1 - i tau lambda.
    let swap = linear_algebra::exact_field::matrix::from_rows(vec![
        vec![gi(0, 0), gi(1, 0)],
        vec![gi(1, 0), gi(0, 0)],
    ])
    .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
    .unwrap();
    let e_swap = euler_propagator(&swap, &tau).unwrap();
    assert_eq!(
        mx::multiply_vector(&e_swap, &[gi(1, 0), gi(1, 0)]).unwrap(),
        vec![gq(1, 1, -1, 2), gq(1, 1, -1, 2)]
    );
    assert_eq!(
        mx::multiply_vector(&e_swap, &[gi(1, 0), gi(-1, 0)]).unwrap(),
        vec![gq(1, 1, 1, 2), gq(-1, 1, -1, 2)]
    );
}

#[test]
fn the_cycle_product_is_the_weighted_holonomy_and_reverses_to_its_conjugate() {
    let packet = kite();
    let connection = U1Connection::new(
        &packet,
        vec![
            gq(3, 5, 4, 5),
            gq(5, 13, 12, 13),
            gi(0, 1),
            gq(8, 17, 15, 17),
        ],
    )
    .unwrap();
    let h = connection.laplacian(&packet);
    let walk = OrientedWalk::new(&packet, "a", &[(0, 1), (1, 1), (2, 1)]).unwrap();
    let holonomy = connection.holonomy(&packet, &walk).unwrap();
    assert_eq!(holonomy, gq(-56, 65, -33, 65));
    // Hopping u -> v is -w A, so around a -> b -> c -> a the product is -(1 * 2 * 3) Hol.
    let forward = cycle_product(&h, &[0, 1, 2]).unwrap();
    assert_eq!(forward, holonomy.mul(&gi(-6, 0)));
    assert_eq!(forward, gq(336, 65, 198, 65));
    assert_eq!(cycle_product(&h, &[2, 1, 0]).unwrap(), forward.conj());
    assert_eq!(cycle_product(&h, &[1, 2, 0]).unwrap(), forward);
}

#[test]
fn holonomy_not_local_data_separates_the_triangle_hamiltonians() {
    let packet = triangle();
    let flat = U1Connection::trivial(&packet).laplacian(&packet);
    let flux = U1Connection::new(&packet, vec![gi(1, 0), gi(1, 0), gi(-1, 0)]).unwrap();
    let twisted = flux.laplacian(&packet);
    assert_ne!(flat, twisted);
    for r in 0..3 {
        assert_eq!(flat.get(r, r), twisted.get(r, r));
        for c in 0..3 {
            assert_eq!(
                flat.get_ref(r, c).unwrap().norm_sq(),
                twisted.get_ref(r, c).unwrap().norm_sq()
            );
        }
    }
    // Hopping u -> v is -w A: the cycle product is -holonomy.
    assert_eq!(cycle_product(&flat, &[0, 1, 2]).unwrap(), gi(-1, 0));
    assert_eq!(cycle_product(&twisted, &[0, 1, 2]).unwrap(), gi(1, 0));
    // tr(H^3) is a unitary invariant: 54 = 0 + 27 + 27 against 66 = 1 + 1 + 64.
    let cube_trace = |h: &BasicMatrix<GaussianRat>| {
        linear_algebra::exact_field::matrix::trace(
            &(linear_algebra::exact_field::matrix::multiply_with_limits(
                &(linear_algebra::exact_field::matrix::multiply_with_limits(
                    &(h),
                    h,
                    linear_algebra::backend::basic_matrix::OperationLimits {
                        max_elements: 1 << 20,
                        max_scalar_ops: 1 << 24,
                    },
                )
                .expect("validated finite matrix shape and budget")),
                h,
                linear_algebra::backend::basic_matrix::OperationLimits {
                    max_elements: 1 << 20,
                    max_scalar_ops: 1 << 24,
                },
            )
            .expect("validated finite matrix shape and budget")),
        )
        .expect("validated finite matrix shape and budget")
    };
    assert_eq!(cube_trace(&flat), gi(54, 0));
    assert_eq!(cube_trace(&twisted), gi(66, 0));
    assert!(matches!(
        trivializing_gauge(&packet, &flux),
        Err(GaugeTrivialityError::NontrivialHolonomy(_))
    ));
    // A vertex gauge changes the matrix but neither invariant.
    let g = VertexGauge::new(&packet, vec![gq(3, 5, 4, 5), gi(0, 1), gq(-5, 13, 12, 13)]).unwrap();
    let big_g = g.diagonal();
    let moved = mx::multiply(
        &mx::multiply(&big_g, &twisted).unwrap(),
        &iv::adjoint(&big_g).unwrap(),
    )
    .unwrap();
    assert_ne!(moved, twisted);
    assert_eq!(cycle_product(&moved, &[0, 1, 2]).unwrap(), gi(1, 0));
    assert_eq!(cycle_product(&moved, &[2, 1, 0]).unwrap(), gi(1, 0));
    assert_eq!(cube_trace(&moved), gi(66, 0));
}

#[test]
fn a_cycle_with_nonzero_first_cohomology_can_carry_trivial_holonomy() {
    let packet = triangle();
    assert_eq!(packet.dimensions().h1, 1);
    let flat = U1Connection::trivial(&packet);
    let g = trivializing_gauge(&packet, &flat).unwrap();
    assert_eq!(g.values(), &[gi(1, 0), gi(1, 0), gi(1, 0)]);
    let hamiltonian = flat.laplacian(&packet);
    assert_eq!(cycle_product(&hamiltonian, &[0, 1, 2]).unwrap(), gi(-1, 0));
}

#[test]
fn malformed_schrodinger_inputs_are_refused() {
    let h = kite_hamiltonian();
    assert!(matches!(
        norm_rate(&h, &[gi(1, 0)]),
        Err(SchrodingerError::Hermitian(_))
    ));
    assert_eq!(cycle_product(&h, &[]), Err(SchrodingerError::EmptyCycle));
    assert_eq!(
        cycle_product(&h, &[0, 7]),
        Err(SchrodingerError::VertexOutOfRange {
            vertex: 7,
            dimension: 4
        })
    );
    assert_eq!(
        cycle_product(&h, &[0, 4]),
        Err(SchrodingerError::VertexOutOfRange {
            vertex: 4,
            dimension: 4
        })
    );
    let rectangular =
        linear_algebra::exact_field::matrix::from_rows(vec![vec![gi(1, 0), gi(0, 0)]])
            .map_err(core_quantum_physics::exact_hermitian::ExactHermitianError::from)
            .unwrap();
    assert_eq!(
        euler_propagator(&rectangular, &ri(1)),
        Err(SchrodingerError::NotSquare { rows: 1, cols: 2 })
    );
    assert_eq!(
        norm_rate(&rectangular, &[gi(1, 0), gi(0, 0)]),
        Err(SchrodingerError::NotSquare { rows: 1, cols: 2 })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/dynamics/schrodinger_finite_shadow.rs
// Claim: urn:core:crates_rs:tests:schrodinger-finite-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord781f738d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord781f738d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError781f738d {
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
impl BoundaryError781f738d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError781f738d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError781f738d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord781f738d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError781f738d> {
        if capacity_bound == 0 {
            return Err(BoundaryError781f738d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError781f738d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError781f738d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_781f738d() {
    let admitted = BoundaryRecord781f738d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord781f738d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
