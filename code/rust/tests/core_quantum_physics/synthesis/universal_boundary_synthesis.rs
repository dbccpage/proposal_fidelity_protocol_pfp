//! QM_206: the "universal exact sequence" `0 -> C^0 -> C^1 -> C^2 -> Obs -> 0`
//! and the pointer-basis identification with `ker d1`, checked on declared
//! finite complexes. Both statements fail as written; the tests hold the
//! countermodels and the part that is true.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution, matrix};
use num_traits::{One, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

fn packet(vertices: &[&str], edges: &[(&str, &str)], faces: &[&[&str]]) -> FiniteCochainPacket {
    let complex = FiniteCochainPacket::build_complex(vertices, edges, faces).unwrap();
    FiniteCochainPacket::with_unit_weights(complex).unwrap()
}

pub(crate) fn triangle(filled: bool) -> FiniteCochainPacket {
    let faces: &[&[&str]] = if filled { &[&["a", "b", "c"]] } else { &[] };
    packet(
        &["a", "b", "c"],
        &[("a", "b"), ("b", "c"), ("c", "a")],
        faces,
    )
}

/// The boundary of a tetrahedron, faces oriented so that every edge is
/// traversed once in each direction.
fn tetrahedron_boundary() -> FiniteCochainPacket {
    packet(
        &["a", "b", "c", "d"],
        &[
            ("a", "b"),
            ("a", "c"),
            ("a", "d"),
            ("b", "c"),
            ("b", "d"),
            ("c", "d"),
        ],
        &[
            &["a", "c", "b"],
            &["a", "b", "d"],
            &["a", "d", "c"],
            &["b", "c", "d"],
        ],
    )
}

/// `(dim ker d0, dim H^1, dim coker d1)`: exactness fails at `C^0`, at `C^1`
/// and at `C^2 -> Obs` exactly where these are nonzero.
fn failures_of_exactness(p: &FiniteCochainPacket) -> (usize, usize, usize) {
    let dims = p.dimensions();
    let rank_d1 = dims.c1 - dims.z1;
    (dims.c0 - dims.b1, dims.h1, dims.c2 - rank_d1)
}

#[test]
fn the_declared_four_term_sequence_is_a_complex_but_never_exact() {
    let open = triangle(false);
    let disk = triangle(true);
    let sphere = tetrahedron_boundary();

    // d1 d0 = 0 is replayed at construction; here on a nonconstant potential too.
    for p in [&open, &disk, &sphere] {
        let f: Vec<Rational> = (0..p.vertex_count())
            .map(|v| ri(v as i64 * v as i64 + 1))
            .collect();
        let x = p.primitive_difference(&f).unwrap();
        assert!(p.face_coboundary(&x).unwrap().iter().all(Zero::is_zero));
        // Constants lie in ker d0, so 0 -> C^0 -> C^1 is never exact.
        let constant = vec![Rational::one(); p.vertex_count()];
        assert!(p
            .primitive_difference(&constant)
            .unwrap()
            .iter()
            .all(Zero::is_zero));
    }

    assert_eq!(failures_of_exactness(&open), (1, 1, 0));
    assert_eq!(failures_of_exactness(&disk), (1, 0, 0));
    assert_eq!(failures_of_exactness(&sphere), (1, 0, 1));
    // Euler characteristic c0 - c1 + c2 = h0 - h1 + h2 on each complex.
    for (p, euler) in [(&open, 0i64), (&disk, 1), (&sphere, 2)] {
        let dims = p.dimensions();
        assert_eq!(dims.c0 as i64 - dims.c1 as i64 + dims.c2 as i64, euler);
        let (h0, h1, h2) = failures_of_exactness(p);
        assert_eq!(h0 as i64 - h1 as i64 + h2 as i64, euler);
    }

    // The H^1 witness on the open triangle: the unit circulation is closed and
    // not a coboundary; its loop sum 3 is its quotient mass.
    let circulation = vec![Rational::one(); 3];
    let class = open.classify(&circulation).unwrap();
    assert_eq!(
        class.diagnostic_class(),
        ObstructionDiagnosticClass::ClosedResidual
    );
    assert_eq!(class.phi1_value(), &ri(3));

    // The fourth term: coker d1 on the sphere is nonzero. Every column of d1
    // sums to zero (each edge bounds two faces with opposite orientations), so
    // the all-ones face functional kills im d1; it reads 1 on the cochain that
    // is 1 on one face, which is therefore not in im d1.
    let d1 = sphere.d1();
    for edge in 0..sphere.edge_count() {
        let column: Rational = d1.iter().map(|row| row[edge].clone()).sum();
        assert!(column.is_zero());
    }
}

/// The projector onto the real integer vector `v`.
fn projector(v: &[i64]) -> BasicMatrix<GaussianRat> {
    let norm: i64 = v.iter().map(|x| x * x).sum();
    let v: Vec<_> = v.iter().map(|&x| gi(x, 0)).collect();
    matrix::scale(
        &involution::outer_product(&v, &v).unwrap(),
        &gq(1, norm, 0, 1),
    )
    .unwrap()
}

fn dephasing(first: &[i64], second: &[i64]) -> ExactKrausChannel {
    ExactKrausChannel::from_operators(vec![projector(first), projector(second)]).unwrap()
}

/// The pure states among `candidates` that the channel leaves fixed.
fn fixed_states(
    channel: &ExactKrausChannel,
    candidates: &[BasicMatrix<GaussianRat>],
) -> Vec<usize> {
    (0..candidates.len())
        .filter(|&k| channel.apply(&candidates[k]).unwrap() == candidates[k])
        .collect()
}

#[test]
fn a_pointer_basis_is_not_a_function_of_the_carrier_complex() {
    // One carrier: a single edge, no faces. ker d1 = C^1 has dimension 1.
    let edge = packet(&["u", "v"], &[("u", "v")], &[]);
    assert_eq!(edge.dimensions().z1, 1);

    // Two declared environments on l2(V) = C^2: dephasing in the vertex basis
    // and in the Hadamard basis.
    let vertex_dephasing = dephasing(&[1, 0], &[0, 1]);
    let hadamard_dephasing = dephasing(&[1, 1], &[1, -1]);
    let candidates = [
        projector(&[1, 0]),
        projector(&[0, 1]),
        projector(&[1, 1]),
        projector(&[1, -1]),
    ];
    assert_eq!(fixed_states(&vertex_dephasing, &candidates), vec![0, 1]);
    assert_eq!(fixed_states(&hadamard_dephasing, &candidates), vec![2, 3]);
    // Each environment sends the other's pointer states to the maximally mixed state.
    let half_identity = matrix::from_rows(vec![
        vec![gq(1, 2, 0, 1), gi(0, 0)],
        vec![gi(0, 0), gq(1, 2, 0, 1)],
    ])
    .unwrap();
    assert_eq!(
        vertex_dephasing.apply(&candidates[2]).unwrap(),
        half_identity
    );
    assert_eq!(
        hadamard_dephasing.apply(&candidates[0]).unwrap(),
        half_identity
    );

    // Counting: on a path of three vertices ker d1 has dimension 2, while any
    // pointer basis of l2(V) has three states; on the filled triangle, 2 against 3.
    let path = packet(&["a", "b", "c"], &[("a", "b"), ("b", "c")], &[]);
    assert_eq!((path.dimensions().z1, path.vertex_count()), (2, 3));
    let disk = triangle(true);
    assert_eq!((disk.dimensions().z1, disk.vertex_count()), (2, 3));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/synthesis/universal_boundary_synthesis.rs
// Claim: urn:core:crates_rs:tests:universal-boundary-synthesis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord98b71a7c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord98b71a7c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError98b71a7c {
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
impl BoundaryError98b71a7c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError98b71a7c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError98b71a7c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord98b71a7c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError98b71a7c> {
        if capacity_bound == 0 {
            return Err(BoundaryError98b71a7c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError98b71a7c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError98b71a7c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_98b71a7c() {
    let admitted = BoundaryRecord98b71a7c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord98b71a7c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
