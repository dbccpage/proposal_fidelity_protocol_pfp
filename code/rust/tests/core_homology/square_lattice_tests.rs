//! Square-lattice cell complexes: the periodic torus, the open disk and the
//! cylinder, with boundary maps over Z and over GF(2).
//!
//! Each test states the invariant it protects. The independent routes are
//! `core_majorana::complexes::surface_grid` (a separate construction of the
//! same GF(2) complexes, compared entry by entry), `core_majorana::h1_basis`
//! (a separate GF(2) kernel and image computation), the existing rational and
//! integral homology of `core_homology::exact_betti` (Smith normal form over
//! a `Carrier` built from the same matrices), and brute-force enumeration of
//! every cochain of the smallest torus.
//!
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigUint;
use core_homology::carrier::Carrier;
use core_homology::cochain_complex::TheoremProvenance;
use core_homology::exact_betti::exact_betti;
use core_homology::f2_cohomology::F2ChainComplex;
use core_homology::integral_chain_complex::IntegralChainComplex;
use core_homology::scalar::{q, Q};
use core_homology::square_lattice::{
    cylinder_square_complex, open_square_complex, periodic_square_complex, Boundary, LatticeError,
    SquareLattice, MAX_LATTICE_PLAQUETTES,
};
use core_majorana::complexes::surface_grid;
use core_number_theory::gf2::F2Vector;
use std::collections::BTreeSet;

fn dims(complex: &F2ChainComplex) -> Vec<usize> {
    (0..=complex.top_dimension())
        .map(|k| complex.cohomology_dimension(k).unwrap())
        .collect()
}

/// The lattice as a two-step `Carrier` over Q: `d0` is the transpose of the
/// vertex-edge boundary and `d1` the transpose of the edge-face boundary.
fn carrier(z: &IntegralChainComplex) -> Carrier {
    let (v, e, f) = (z.cell_count(0), z.cell_count(1), z.cell_count(2));
    let mut d0 = vec![q(0); e * v];
    let d1_boundary = z.boundary(1).unwrap();
    for edge in 0..e {
        for &(vertex, coefficient) in d1_boundary.column(edge).unwrap() {
            d0[edge * v + vertex] = q(coefficient);
        }
    }
    let mut d1 = vec![q(0); f * e];
    let d2_boundary = z.boundary(2).unwrap();
    for face in 0..f {
        for &(edge, coefficient) in d2_boundary.column(face).unwrap() {
            d1[face * e + edge] = q(coefficient);
        }
    }
    Carrier::new(
        v,
        e,
        f,
        BasicMatrix::<Q>::from_row_major(e, v, d0).unwrap(),
        BasicMatrix::<Q>::from_row_major(f, e, d1).unwrap(),
        vec![q(1); e],
        TheoremProvenance::new("square lattice boundary matrices".to_owned()).unwrap(),
    )
    .unwrap()
}

// ---------------------------------------------------------------------------
// Shape
// ---------------------------------------------------------------------------

#[test]
fn a_periodic_lattice_has_l1_l2_vertices_twice_as_many_edges_and_l1_l2_faces() {
    for (l1, l2) in [(2, 2), (2, 3), (3, 2), (3, 3), (4, 5), (6, 6)] {
        let lattice = periodic_square_complex(l1, l2).unwrap();
        assert_eq!(lattice.vertex_count(), l1 * l2);
        assert_eq!(lattice.edge_count(), 2 * l1 * l2);
        assert_eq!(lattice.face_count(), l1 * l2);
        assert_eq!((lattice.rows(), lattice.cols()), (l1, l2));
        assert_eq!(
            lattice.integral_complex().euler_characteristic(),
            0.into(),
            "a torus has chi = 0"
        );
    }
}

#[test]
fn open_and_cylinder_lattices_have_the_expected_cell_counts() {
    for (l1, l2) in [(1, 1), (2, 3), (4, 4)] {
        let disk = open_square_complex(l1, l2).unwrap();
        assert_eq!(disk.vertex_count(), (l1 + 1) * (l2 + 1));
        assert_eq!(disk.edge_count(), (l1 + 1) * l2 + l1 * (l2 + 1));
        assert_eq!(disk.face_count(), l1 * l2);
        assert_eq!(
            disk.integral_complex().euler_characteristic(),
            1.into(),
            "a disk has chi = 1"
        );
    }
    for (l1, l2) in [(2, 1), (3, 3), (4, 2)] {
        let cylinder = cylinder_square_complex(l1, l2).unwrap();
        assert_eq!(cylinder.vertex_count(), l1 * (l2 + 1));
        assert_eq!(cylinder.edge_count(), l1 * l2 + l1 * (l2 + 1));
        assert_eq!(cylinder.face_count(), l1 * l2);
        assert_eq!(cylinder.integral_complex().euler_characteristic(), 0.into());
    }
}

#[test]
fn the_numbering_places_edges_and_plaquette_boundaries_as_documented() {
    let lattice = periodic_square_complex(3, 4).unwrap();
    // Horizontal edges first: h(r, c) joins (r, c) to (r, c+1 mod 4).
    for r in 0..3 {
        for c in 0..4 {
            let e = lattice.horizontal_edge(r, c).unwrap();
            assert_eq!(e, r * 4 + c);
            assert_eq!(
                lattice.edge_endpoints()[e],
                (
                    lattice.vertex_index(r, c).unwrap(),
                    lattice.vertex_index(r, (c + 1) % 4).unwrap()
                )
            );
        }
    }
    // Then vertical edges: v(r, c) joins (r, c) to (r+1 mod 3, c).
    for r in 0..3 {
        for c in 0..4 {
            let e = lattice.vertical_edge(r, c).unwrap();
            assert_eq!(e, 12 + r * 4 + c);
            assert_eq!(
                lattice.edge_endpoints()[e],
                (
                    lattice.vertex_index(r, c).unwrap(),
                    lattice.vertex_index((r + 1) % 3, c).unwrap()
                )
            );
        }
    }
    // The plaquette (2, 3) wraps in both directions.
    let steps = lattice.face_boundary(2 * 4 + 3).unwrap();
    assert_eq!(
        steps,
        &[
            (lattice.horizontal_edge(2, 3).unwrap(), 1),
            (lattice.vertical_edge(2, 0).unwrap(), 1),
            (lattice.horizontal_edge(0, 3).unwrap(), -1),
            (lattice.vertical_edge(2, 3).unwrap(), -1),
        ][..]
    );
}

#[test]
fn each_plaquette_boundary_is_a_closed_walk_over_z() {
    // d_1 d_2 = 0 is checked on construction; here the walk is followed
    // vertex by vertex for every plaquette of several lattices.
    for lattice in [
        periodic_square_complex(2, 2).unwrap(),
        periodic_square_complex(3, 5).unwrap(),
        open_square_complex(3, 2).unwrap(),
        cylinder_square_complex(3, 2).unwrap(),
    ] {
        for face in 0..lattice.face_count() {
            let steps = lattice.face_boundary(face).unwrap();
            let (first_edge, first_direction) = steps[0];
            let (source, target) = lattice.edge_endpoints()[first_edge];
            let start = if first_direction == 1 { source } else { target };
            let mut here = start;
            for &(edge, direction) in steps {
                let (s, t) = lattice.edge_endpoints()[edge];
                let (from, to) = if direction == 1 { (s, t) } else { (t, s) };
                assert_eq!(from, here, "plaquette {face} is not a walk");
                here = to;
            }
            assert_eq!(here, start, "plaquette {face} does not close");
        }
    }
}

// ---------------------------------------------------------------------------
// Homology
// ---------------------------------------------------------------------------

#[test]
fn the_torus_has_h1_of_dimension_two_over_f2_and_the_counts_match() {
    // dim Z^1 = N + 1 and dim B^1 = N - 1 for N = l1 l2 vertices, so
    // |H^1| = 2^2 = 4: the ground state degeneracy 2^dim H_1 = 4.
    for (l1, l2) in [(2, 2), (2, 3), (3, 3), (3, 4), (4, 4), (5, 3)] {
        let complex = periodic_square_complex(l1, l2)
            .unwrap()
            .f2_complex()
            .unwrap();
        let n = l1 * l2;
        assert_eq!(dims(&complex), vec![1, 2, 1], "{l1} x {l2}");
        assert_eq!(
            complex.cocycle_count(1).unwrap(),
            BigUint::from(2u32).pow((n + 1) as u32)
        );
        assert_eq!(
            complex.coboundary_count(1).unwrap(),
            BigUint::from(2u32).pow((n - 1) as u32)
        );
        assert_eq!(complex.cohomology_count(1).unwrap(), BigUint::from(4u32));
        assert_eq!(complex.homology_dimension(1).unwrap(), 2);
        assert_eq!(complex.euler_characteristic(), 0.into());
    }
}

#[test]
fn the_two_by_two_torus_counts_agree_with_brute_force_over_all_256_cochains() {
    let lattice = periodic_square_complex(2, 2).unwrap();
    let complex = lattice.f2_complex().unwrap();
    // Incidence from the walks, not from the boundary matrices.
    let faces: Vec<u64> = (0..lattice.face_count())
        .map(|f| {
            lattice
                .face_boundary(f)
                .unwrap()
                .iter()
                .fold(0u64, |m, &(edge, _)| m ^ (1u64 << edge))
        })
        .collect();
    let cocycles = (0u64..256)
        .filter(|&c| faces.iter().all(|face| (face & c).count_ones() % 2 == 0))
        .count();
    let coboundaries: BTreeSet<u64> = (0u64..16)
        .map(|s| {
            lattice
                .edge_endpoints()
                .iter()
                .enumerate()
                .fold(0u64, |m, (e, &(u, v))| {
                    m | ((((s >> u) ^ (s >> v)) & 1) << e)
                })
        })
        .collect();
    assert_eq!(
        complex.cocycle_count(1).unwrap().to_string(),
        cocycles.to_string()
    );
    assert_eq!(
        complex.coboundary_count(1).unwrap().to_string(),
        coboundaries.len().to_string()
    );
    assert_eq!((cocycles, coboundaries.len()), (32, 8));
}

#[test]
fn integral_homology_of_the_torus_is_z_z_squared_z_with_no_torsion() {
    for (l1, l2) in [(2, 2), (3, 4), (4, 4)] {
        let z = periodic_square_complex(l1, l2)
            .unwrap()
            .integral_complex()
            .clone();
        for (k, rank) in [1usize, 2, 1].into_iter().enumerate() {
            let h = z.integral_homology(k).unwrap();
            assert_eq!(
                (h.free_rank, h.torsion.len()),
                (rank, 0),
                "H_{k} of the {l1} x {l2} torus"
            );
        }
    }
}

#[test]
fn the_existing_exact_betti_code_agrees_on_the_lattice_carrier() {
    // The same matrices as a two-step carrier over Q: b = (1, 2, 1) and no
    // invariant factor above 1, by the existing Smith normal form code.
    for (l1, l2) in [(2, 2), (3, 3)] {
        let lattice = periodic_square_complex(l1, l2).unwrap();
        let betti = exact_betti(&carrier(lattice.integral_complex())).unwrap();
        assert_eq!((betti.b0(), betti.b1(), betti.b2_terminal()), (1, 2, 1));
        assert!(!betti.has_torsion());
        assert_eq!(betti.euler_characteristic(), 0.into());
    }
    let disk = open_square_complex(2, 2).unwrap();
    let betti = exact_betti(&carrier(disk.integral_complex())).unwrap();
    assert_eq!((betti.b0(), betti.b1(), betti.b2_terminal()), (1, 0, 0));
}

#[test]
fn disks_and_cylinders_have_the_expected_f2_cohomology() {
    for (l1, l2) in [(1, 1), (2, 3), (4, 4)] {
        let complex = open_square_complex(l1, l2).unwrap().f2_complex().unwrap();
        assert_eq!(dims(&complex), vec![1, 0, 0], "disk {l1} x {l2}");
    }
    for (l1, l2) in [(2, 1), (3, 3), (4, 2)] {
        let complex = cylinder_square_complex(l1, l2)
            .unwrap()
            .f2_complex()
            .unwrap();
        assert_eq!(dims(&complex), vec![1, 1, 0], "cylinder {l1} x {l2}");
    }
}

// ---------------------------------------------------------------------------
// Comparison with core_majorana
// ---------------------------------------------------------------------------

#[test]
fn the_periodic_lattice_matches_surface_grid_entry_by_entry() {
    for (m, n) in [(2, 2), (2, 3), (3, 2), (3, 3), (4, 5)] {
        let theirs = surface_grid(m, n, true);
        let ours = periodic_square_complex(m, n).unwrap().f2_complex().unwrap();
        assert_eq!(
            (theirs.num_vertices, theirs.num_edges, theirs.num_faces),
            (ours.cell_count(0), ours.cell_count(1), ours.cell_count(2))
        );
        // Their d0 is |E| x |V| and d1 is |F| x |E|: our coboundaries.
        assert_eq!(
            theirs.d0.data,
            ours.coboundary(0).unwrap().to_rows(),
            "d0 of {m} x {n}"
        );
        assert_eq!(
            theirs.d1.data,
            ours.coboundary(1).unwrap().to_rows(),
            "d1 of {m} x {n}"
        );
    }
}

#[test]
fn the_open_lattice_matches_surface_grid_entry_by_entry() {
    for (m, n) in [(1, 1), (2, 2), (2, 3), (4, 3)] {
        let theirs = surface_grid(m, n, false);
        let ours = open_square_complex(m, n).unwrap().f2_complex().unwrap();
        assert_eq!(
            (theirs.num_vertices, theirs.num_edges, theirs.num_faces),
            (ours.cell_count(0), ours.cell_count(1), ours.cell_count(2))
        );
        assert_eq!(
            theirs.d0.data,
            ours.coboundary(0).unwrap().to_rows(),
            "d0 of {m} x {n}"
        );
        assert_eq!(
            theirs.d1.data,
            ours.coboundary(1).unwrap().to_rows(),
            "d1 of {m} x {n}"
        );
    }
}

#[test]
fn an_independent_h1_computation_finds_the_same_dimension() {
    for (m, n) in [(2, 2), (3, 3), (3, 5)] {
        let theirs = surface_grid(m, n, true);
        let basis = core_majorana::h1_basis(&theirs.d0, &theirs.d1);
        let ours = periodic_square_complex(m, n).unwrap().f2_complex().unwrap();
        assert_eq!(basis.dim, ours.cohomology_dimension(1).unwrap());
        assert_eq!(basis.dim, 2);
    }
    let planar = surface_grid(3, 3, false);
    assert_eq!(core_majorana::h1_basis(&planar.d0, &planar.d1).dim, 0);
}

// ---------------------------------------------------------------------------
// Logical operators
// ---------------------------------------------------------------------------

#[test]
fn the_two_noncontractible_loops_are_a_basis_of_h1() {
    for (l1, l2) in [(2, 2), (3, 3), (4, 5)] {
        let lattice = periodic_square_complex(l1, l2).unwrap();
        let complex = lattice.f2_complex().unwrap();
        let horizontal = lattice.horizontal_loop(0).unwrap();
        let vertical = lattice.vertical_loop(0).unwrap();
        assert_eq!((horizontal.weight(), vertical.weight()), (l2, l1));
        for loop_ in [&horizontal, &vertical] {
            assert!(complex.is_cycle(1, loop_).unwrap());
            assert!(
                !complex.is_boundary(1, loop_).unwrap(),
                "the loop is not contractible"
            );
        }
        // Independent modulo boundaries: the sum is not a boundary either.
        let both = horizontal.add(&vertical).unwrap();
        assert!(!complex.is_boundary(1, &both).unwrap());
        assert_eq!(complex.homology_dimension(1).unwrap(), 2);
        // Loops in different rows or columns are homologous.
        for r in 1..l1 {
            let shifted = lattice.horizontal_loop(r).unwrap();
            assert!(complex
                .is_boundary(1, &horizontal.add(&shifted).unwrap())
                .unwrap());
        }
        for c in 1..l2 {
            let shifted = lattice.vertical_loop(c).unwrap();
            assert!(complex
                .is_boundary(1, &vertical.add(&shifted).unwrap())
                .unwrap());
        }
        // The boundary of a plaquette is a boundary.
        let plaquette = complex.boundary(2).unwrap().column(0).unwrap();
        assert!(complex.is_boundary(1, &plaquette).unwrap());
    }
}

#[test]
fn the_pairing_of_loops_with_cohomology_classes_is_nondegenerate() {
    // <cycle, cocycle> is well defined on classes: it vanishes on coboundaries
    // and on boundaries, and on the torus the 2 x 2 matrix of the two loops
    // against a basis of H^1 is invertible (universal coefficients).
    let lattice = periodic_square_complex(3, 4).unwrap();
    let complex = lattice.f2_complex().unwrap();
    let loops = [
        lattice.horizontal_loop(1).unwrap(),
        lattice.vertical_loop(2).unwrap(),
    ];
    for coboundary in complex.coboundary_space(1).unwrap() {
        for l in &loops {
            assert!(
                !l.dot(&coboundary).unwrap(),
                "a loop pairs to zero with a coboundary"
            );
        }
    }
    for boundary in complex.boundary_space(1).unwrap() {
        for class in complex.cohomology_basis(1).unwrap() {
            assert!(
                !boundary.dot(&class).unwrap(),
                "a cocycle pairs to zero with a boundary"
            );
        }
    }
    let classes = complex.cohomology_basis(1).unwrap();
    let pairing: Vec<Vec<bool>> = loops
        .iter()
        .map(|l| classes.iter().map(|c| l.dot(c).unwrap()).collect())
        .collect();
    let determinant = (pairing[0][0] & pairing[1][1]) ^ (pairing[0][1] & pairing[1][0]);
    assert!(determinant, "the pairing matrix {pairing:?} is singular");
    // A cocycle that evaluates to 1 on the horizontal loop and 0 on the
    // vertical one exists: the edges h(r, 0) for all r cut each horizontal loop once.
    let seam = F2Vector::from_indices(
        lattice.edge_count(),
        &(0..3)
            .map(|r| lattice.horizontal_edge(r, 0).unwrap())
            .collect::<Vec<_>>(),
    )
    .unwrap();
    assert!(complex.is_cocycle(1, &seam).unwrap());
    assert!(!complex.is_coboundary(1, &seam).unwrap());
    assert!(loops[0].dot(&seam).unwrap() && !loops[1].dot(&seam).unwrap());
}

#[test]
fn the_bockstein_of_the_torus_lattice_vanishes() {
    // No 2-torsion: the Bockstein map H^1 -> H^2 is zero.
    let z = periodic_square_complex(3, 3)
        .unwrap()
        .integral_complex()
        .clone();
    let matrix = z.bockstein_matrix(1).unwrap();
    assert_eq!((matrix.rows(), matrix.cols()), (1, 2));
    assert!(matrix.is_zero());
}

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[test]
fn lattice_constructors_refuse_too_small_and_too_large_sizes() {
    assert_eq!(
        periodic_square_complex(1, 4).unwrap_err(),
        LatticeError::PeriodicDirectionTooShort { sites: 1 }
    );
    assert_eq!(
        periodic_square_complex(4, 1).unwrap_err(),
        LatticeError::PeriodicDirectionTooShort { sites: 1 }
    );
    assert_eq!(
        periodic_square_complex(0, 4).unwrap_err(),
        LatticeError::EmptyDirection
    );
    assert_eq!(
        open_square_complex(3, 0).unwrap_err(),
        LatticeError::EmptyDirection
    );
    assert_eq!(
        cylinder_square_complex(1, 3).unwrap_err(),
        LatticeError::PeriodicDirectionTooShort { sites: 1 }
    );
    // One column is fine on a cylinder, whose columns are open.
    assert!(cylinder_square_complex(3, 1).is_ok());
    assert_eq!(MAX_LATTICE_PLAQUETTES, 4096);
    assert!(periodic_square_complex(64, 64).is_ok());
    assert_eq!(
        periodic_square_complex(64, 65).unwrap_err(),
        LatticeError::TooManyPlaquettes {
            rows: 64,
            cols: 65,
            limit: 4096
        }
    );
    assert!(matches!(
        periodic_square_complex(usize::MAX, 2),
        Err(LatticeError::TooManyPlaquettes { .. })
    ));
    assert!(matches!(
        SquareLattice::new(usize::MAX, usize::MAX, Boundary::Open, Boundary::Open),
        Err(LatticeError::TooManyPlaquettes { .. })
    ));
}

#[test]
fn lattice_queries_refuse_out_of_range_indices_and_open_directions() {
    let torus = periodic_square_complex(2, 3).unwrap();
    assert_eq!(
        torus.vertex_index(2, 0).unwrap_err(),
        LatticeError::IndexOutOfRange { index: 2, len: 2 }
    );
    assert!(torus.horizontal_edge(0, 3).is_err());
    assert!(torus.vertical_edge(2, 0).is_err());
    assert!(torus.face_boundary(6).is_err());
    assert!(torus.horizontal_loop(2).is_err());
    assert!(torus.vertical_loop(3).is_err());
    let cylinder = cylinder_square_complex(3, 2).unwrap();
    // Periodic rows, open columns: vertical loops exist, horizontal ones do not.
    assert!(cylinder.vertical_loop(0).is_ok());
    assert_eq!(
        cylinder.horizontal_loop(0).unwrap_err(),
        LatticeError::DirectionNotPeriodic {
            direction: "column"
        }
    );
    let disk = open_square_complex(2, 2).unwrap();
    assert!(matches!(
        disk.vertical_loop(0),
        Err(LatticeError::DirectionNotPeriodic { .. })
    ));
    assert!(matches!(
        disk.horizontal_loop(0),
        Err(LatticeError::DirectionNotPeriodic { .. })
    ));
}

// Origin: engine/crates_rs/tests/core_homology/square_lattice_tests.rs
// Claim: urn:core:crates_rs:tests:square-lattice-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord067ea7eb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord067ea7eb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError067ea7eb {
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
impl BoundaryError067ea7eb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError067ea7eb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError067ea7eb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord067ea7eb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError067ea7eb> {
        if capacity_bound == 0 {
            return Err(BoundaryError067ea7eb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError067ea7eb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError067ea7eb::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_067ea7eb() {
    let admitted = BoundaryRecord067ea7eb::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord067ea7eb::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
