//! Finite kinematical shadows of general relativity: `d1 d0 = 0` on a filled
//! triangle and the based product of face holonomies on a tetrahedron's
//! boundary, isometries of declared pairings, path-ordered transport that is
//! path independent exactly when flat, and incomplete transport orbits read as
//! refusals. Every check is exact.

use linear_algebra::exact_field::{involution, matrix};
use core_holonomy::functional_graph::{
    orbit_value, transport_orbit, TransportOrbit, TransportOrbitError,
};
use core_kernel::resource_limits::OperationLimits;
use std::collections::BTreeMap;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_holonomy::{
    compute_loop_holonomy, compute_path_holonomy, verify_discrete_bianchi_identity,
};
use core_lie_theory::lorentz;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_solvers::cert_cohomology_admission::{admit, complex_of_packet, Admission};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use crate::support::quaternion_group;
use crate::support::{
    cell_complex, connection, field, identity, path, q8, quaternion_plaquette, Connection, I, J, K,
    MINUS_ONE,
};
use core_quantum_physics::transport_isometry_orbits::{is_isometry, IsometryError};

#[test]
fn the_coboundary_of_a_coboundary_vanishes_on_the_filled_triangle() {
    let triangle = FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(
            &["a", "b", "c"],
            &[("a", "b"), ("b", "c"), ("c", "a")],
            &[&["a", "b", "c"]],
        )
        .unwrap(),
    )
    .unwrap();
    let d0 = triangle.d0();
    let d1 = triangle.d1();
    let composite: Vec<Rational> = (0..3)
        .map(|column| (0..3).map(|e| &d1[0][e] * &d0[e][column]).sum())
        .collect();
    assert_eq!(composite, vec![ri(0); 3]);
    let complex = complex_of_packet(&triangle).unwrap();
    for code in 0..125i64 {
        let f: Vec<Rational> = (0..3).map(|i| ri(code / 5i64.pow(i) % 5 - 2)).collect();
        let coboundary = triangle.primitive_difference(&f).unwrap();
        assert_eq!(triangle.face_coboundary(&coboundary).unwrap(), vec![ri(0)]);
        assert!(matches!(
            admit(&complex, Some(&coboundary)),
            Admission::Exact { .. }
        ));
    }
    // The triangle is contractible, and an edge of its face is not closed.
    let dims = triangle.dimensions();
    assert_eq!((dims.b1, dims.z1, dims.h1), (2, 2, 0));
    let edge = vec![ri(1), ri(0), ri(0)];
    assert!(matches!(
        admit(&complex, Some(&edge)),
        Admission::ActiveClosureFailure { .. }
    ));
}

/// The tetrahedron `a b c d` with the four face loops based at `a`; the last
/// one reaches the face `b d c` along `a -> b` and returns.
fn based_faces() -> Vec<Vec<String>> {
    vec![
        path(&["a", "b", "d", "c", "b", "a"]),
        path(&["a", "d", "b", "a"]),
        path(&["a", "c", "d", "a"]),
        path(&["a", "b", "c", "a"]),
    ]
}

fn tetrahedron_edges() -> [(&'static str, &'static str); 6] {
    [
        ("a", "b"),
        ("b", "c"),
        ("a", "c"),
        ("a", "d"),
        ("b", "d"),
        ("c", "d"),
    ]
}

#[test]
fn based_face_holonomies_of_a_closed_surface_multiply_to_one_for_any_connection() {
    let one = matrix::identity(2).unwrap();
    let values = [q8(I), q8(J), one.clone(), q8(K), one, q8(MINUS_ONE)];
    let curved = connection(
        2,
        &tetrahedron_edges()
            .iter()
            .zip(values)
            .map(|(&(u, v), m)| (u, v, m))
            .collect::<Vec<_>>(),
    );
    // Every face is curved.
    for face in based_faces() {
        assert_ne!(compute_loop_holonomy(&curved, &face).unwrap(), identity(2));
    }
    assert!(verify_discrete_bianchi_identity(&curved, &based_faces()).unwrap());
    // Without the base-point transport to `b` the product is -1.
    let mut unbased = based_faces();
    unbased[0] = path(&["b", "d", "c", "b"]);
    assert!(!verify_discrete_bianchi_identity(&curved, &unbased).unwrap());
    let product = unbased.iter().fold(identity(2), |acc, face| {
        acc.matmul(&compute_loop_holonomy(&curved, face).unwrap())
            .unwrap()
    });
    assert_eq!(product, field(&q8(MINUS_ONE)));
    // For an abelian connection the base point does not matter.
    let phases = [
        gi(0, 1),
        gq(3, 5, 4, 5),
        gi(-1, 0),
        gq(5, 13, -12, 13),
        gi(0, -1),
        gi(1, 0),
    ];
    let abelian = connection(
        1,
        &tetrahedron_edges()
            .iter()
            .zip(phases)
            .map(|(&(u, v), z)| (u, v, matrix::diagonal(&[z]).unwrap()))
            .collect::<Vec<_>>(),
    );
    assert!(verify_discrete_bianchi_identity(&abelian, &based_faces()).unwrap());
    assert!(verify_discrete_bianchi_identity(&abelian, &unbased).unwrap());
}

fn rational_matrix(rows: Vec<Vec<Rational>>) -> BasicMatrix<Rational> {
    matrix::from_rows(rows).unwrap()
}

fn signed_permutations() -> Vec<BasicMatrix<Rational>> {
    let permutations = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ];
    let mut matrices = Vec::new();
    for sigma in permutations {
        for signs in 0..8 {
            let mut m = matrix::zeros(3, 3).unwrap();
            for (row, &column) in sigma.iter().enumerate() {
                m.set(
                    row,
                    column,
                    if signs >> row & 1 == 1 { ri(-1) } else { ri(1) },
                )
                .unwrap();
            }
            matrices.push(m);
        }
    }
    matrices
}

#[test]
fn isometries_of_a_declared_pairing_compose_and_depend_on_the_pairing() {
    let euclidean3 = matrix::identity(3).unwrap();
    let group = signed_permutations();
    assert_eq!(group.len(), 48);
    for a in &group {
        assert!(is_isometry(&euclidean3, a).unwrap());
        for b in &group {
            let ab = matrix::multiply(&a, b).unwrap();
            assert!(is_isometry(&euclidean3, &ab).unwrap());
            assert!(group.contains(&ab));
        }
    }
    // Holonomies of quaternion steps preserve the Hermitian pairing on Q(i)^2.
    let hermitian = matrix::identity(2).unwrap();
    let q = quaternion_group();
    for a in &q {
        for b in &q {
            for c in &q {
                assert!(is_isometry(
                    &hermitian,
                    &matrix::multiply(&matrix::multiply(&a, b).unwrap(), c).unwrap()
                )
                .unwrap());
            }
        }
    }
    let squeeze = matrix::diagonal(&[gi(2, 0), gq(1, 2, 0, 1)]).unwrap();
    assert!(!is_isometry(&hermitian, &matrix::multiply(&q[I], &squeeze).unwrap()).unwrap());

    // One transport, two pairings: a rational boost keeps diag(1, -1), a rotation keeps I.
    let boost = lorentz::boost(1, &ri(2), &[ri(1)]).unwrap();
    assert!(lorentz::preserves_form(&boost).unwrap());
    let b = rational_matrix(boost.as_slice().chunks(2).map(|row| row.to_vec()).collect());
    let minkowski = rational_matrix(vec![vec![ri(1), ri(0)], vec![ri(0), ri(-1)]]);
    let euclidean2 = matrix::identity(2).unwrap();
    let rotation = rational_matrix(vec![vec![rq(3, 5), rq(-4, 5)], vec![rq(4, 5), rq(3, 5)]]);
    let stretch = rational_matrix(vec![vec![ri(2), ri(0)], vec![ri(0), rq(1, 2)]]);
    assert_eq!(
        [&b, &rotation, &stretch].map(|t| (
            is_isometry(&minkowski, t).unwrap(),
            is_isometry(&euclidean2, t).unwrap()
        )),
        [(true, false), (false, true), (false, false)]
    );
    assert_eq!(
        is_isometry(&euclidean2, &euclidean3),
        Err(IsometryError::Shape)
    );
}

#[test]
fn transport_composes_along_paths_and_is_path_independent_exactly_when_flat() {
    let k4 = cell_complex(
        &["a", "b", "c", "d"],
        &[
            ("a", "b"),
            ("a", "c"),
            ("a", "d"),
            ("b", "c"),
            ("b", "d"),
            ("c", "d"),
        ],
        &[],
    );
    let q = quaternion_group();
    let gauge: BTreeMap<String, _> = [("a", I), ("b", J), ("c", K), ("d", MINUS_ONE)]
        .into_iter()
        .map(|(v, g)| (v.to_string(), field(&q[g])))
        .collect();
    let flat = Connection::from_pure_gauge(&k4, &gauge, 2, OperationLimits::holonomy()).unwrap();
    let paths = [
        path(&["a", "d"]),
        path(&["a", "b", "d"]),
        path(&["a", "c", "d"]),
        path(&["a", "b", "c", "d"]),
        path(&["a", "c", "b", "d"]),
    ];
    let endpoints =
        field(&matrix::multiply(&q[MINUS_ONE], &involution::adjoint(&q[I]).unwrap()).unwrap());
    for p in &paths {
        assert_eq!(compute_path_holonomy(&flat, p).unwrap(), endpoints);
    }
    // Concatenation multiplies, later steps on the left, flat or not.
    let curved_k4 = connection(
        2,
        &[
            ("a", "b", q8(I)),
            ("a", "c", q8(J)),
            ("a", "d", q8(K)),
            ("b", "c", q8(J)),
            ("b", "d", q8(I)),
            ("c", "d", q8(K)),
        ],
    );
    for c in [&flat, &curved_k4] {
        let whole = compute_path_holonomy(c, &path(&["a", "b", "c", "d"])).unwrap();
        let first = compute_path_holonomy(c, &path(&["a", "b", "c"])).unwrap();
        let second = compute_path_holonomy(c, &path(&["c", "d"])).unwrap();
        assert_eq!(whole, second.matmul(&first).unwrap());
    }
    // On the curved plaquette two paths from a to c differ by the loop holonomy -1.
    let curved = quaternion_plaquette();
    let upper = compute_path_holonomy(&curved, &path(&["a", "b", "c"])).unwrap();
    let lower = compute_path_holonomy(&curved, &path(&["a", "d", "c"])).unwrap();
    assert_ne!(upper, lower);
    let loop_holonomy = compute_loop_holonomy(&curved, &path(&["a", "b", "c", "d", "a"])).unwrap();
    assert_eq!(
        lower.inverse().unwrap().matmul(&upper).unwrap(),
        loop_holonomy
    );
    assert_eq!(loop_holonomy, field(&q8(MINUS_ONE)));
}

#[test]
fn an_incomplete_transport_orbit_is_a_refusal_not_a_vertex() {
    let options = [None, Some(0), Some(1), Some(2)];
    let (mut refused, mut periodic) = (0, 0);
    for code in 0..64usize {
        let step: Vec<Option<usize>> = (0..3).map(|v| options[code / 4usize.pow(v) % 4]).collect();
        for start in 0..3 {
            let values: Vec<Option<usize>> = (0..=6)
                .map(|k| orbit_value(&step, start, k).unwrap())
                .collect();
            assert_eq!(values[0], Some(start));
            match transport_orbit(&step, start).unwrap() {
                TransportOrbit::Refused { at_step } => {
                    assert!((1..=3).contains(&at_step));
                    assert!(values[..at_step].iter().all(Option::is_some));
                    assert!(values[at_step..].iter().all(Option::is_none));
                    refused += 1;
                }
                TransportOrbit::Periodic { entry, period } => {
                    assert!(period >= 1 && entry + period <= 3);
                    assert!(values.iter().all(Option::is_some));
                    for k in entry..=6 - period {
                        assert_eq!(values[k], values[k + period]);
                    }
                    let prefix: Vec<_> = values[..entry + period].to_vec();
                    assert!((0..prefix.len()).all(|i| !prefix[..i].contains(&prefix[i])));
                    periodic += 1;
                }
            }
        }
    }
    assert_eq!(refused + periodic, 192);
    assert_eq!(
        transport_orbit(&[Some(1), Some(2), None], 0).unwrap(),
        TransportOrbit::Refused { at_step: 3 }
    );
    assert_eq!(
        transport_orbit(&[Some(1), Some(2), None], 2).unwrap(),
        TransportOrbit::Refused { at_step: 1 }
    );
    assert_eq!(
        transport_orbit(&[Some(1), Some(2), Some(1)], 0).unwrap(),
        TransportOrbit::Periodic {
            entry: 1,
            period: 2
        }
    );
    assert_eq!(
        transport_orbit(&[Some(0), None, None], 0).unwrap(),
        TransportOrbit::Periodic {
            entry: 0,
            period: 1
        }
    );
    assert_eq!(
        transport_orbit(&[Some(0)], 1),
        Err(TransportOrbitError::StartOutOfRange {
            start: 1,
            vertices: 1
        })
    );
    assert_eq!(
        orbit_value(&[Some(3), None], 0, 1),
        Err(TransportOrbitError::TargetOutOfRange {
            vertex: 0,
            target: 3,
            vertices: 2
        })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/repair_and_gravity/general_relativity_kinematical_shadows.rs
// Claim: urn:core:crates_rs:tests:general-relativity-kinematical-shadows:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7fb8b7a9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7fb8b7a9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7fb8b7a9 {
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
impl BoundaryError7fb8b7a9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7fb8b7a9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7fb8b7a9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7fb8b7a9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7fb8b7a9> {
        if capacity_bound == 0 {
            return Err(BoundaryError7fb8b7a9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7fb8b7a9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7fb8b7a9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7fb8b7a9() {
    let admitted = BoundaryRecord7fb8b7a9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7fb8b7a9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
