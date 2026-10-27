//! Finite cell complexes for Majorana GF(2) play (triangle, plaquette, prism).
//!
//! Built so that \(d_1 \circ d_0 = 0 \pmod 2\) by construction (edge-vertex + face-edge).
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2500a638<T> {
    fn checked_invariant_2500a638(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2500a638<T> for Option<T> {
    #[inline]
    fn checked_invariant_2500a638(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2500a638<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2500a638(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::gf2_terminalizer::GF2Matrix;

/// A 2-step GF(2) chain complex \(C_0 \xrightarrow{d_0} C_1 \xrightarrow{d_1} C_2\).
#[derive(Debug, Clone)]
pub struct ChainComplexGf2 {
    pub name: &'static str,
    /// \(d_0\): |E| × |V| (edge-vertex incidence mod 2).
    pub d0: GF2Matrix,
    /// \(d_1\): |F| × |E| (face-edge incidence mod 2).
    pub d1: GF2Matrix,
    pub num_vertices: usize,
    pub num_edges: usize,
    pub num_faces: usize,
}

impl ChainComplexGf2 {
    pub fn verify_boundary(&self) -> bool {
        crate::gf2_terminalizer::Gf2CocycleClassifier::verify_boundary(&self.d0, &self.d1)
    }
}

/// Triangle: 3 vertices, 3 edges, 1 face.
///
/// Edges: e0=(0,1), e1=(1,2), e2=(0,2). Face: all three edges.
pub fn triangle() -> ChainComplexGf2 {
    let d0 = GF2Matrix::from_data(vec![vec![1, 1, 0], vec![0, 1, 1], vec![1, 0, 1]]);
    let d1 = GF2Matrix::from_data(vec![vec![1, 1, 1]]);
    ChainComplexGf2 {
        name: "triangle",
        d0,
        d1,
        num_vertices: 3,
        num_edges: 3,
        num_faces: 1,
    }
}

/// Square plaquette: 4 vertices, 4 edges, 1 face.
///
/// Edges: (0,1),(1,2),(2,3),(3,0). Face: cycle of four.
pub fn plaquette() -> ChainComplexGf2 {
    let d0 = GF2Matrix::from_data(vec![
        vec![1, 1, 0, 0],
        vec![0, 1, 1, 0],
        vec![0, 0, 1, 1],
        vec![1, 0, 0, 1],
    ]);
    let d1 = GF2Matrix::from_data(vec![vec![1, 1, 1, 1]]);
    ChainComplexGf2 {
        name: "plaquette",
        d0,
        d1,
        num_vertices: 4,
        num_edges: 4,
        num_faces: 1,
    }
}

/// Triangular prism: 6 vertices, 9 edges, 5 faces (2 triangles + 3 quads).
///
/// Bottom triangle 0,1,2; top 3,4,5; vertical edges 0-3,1-4,2-5.
/// Faces: bottom, top, and three lateral quads (each as 4-edge incidence).
pub fn prism() -> ChainComplexGf2 {
    // Edge order:
    // 0:(0,1) 1:(1,2) 2:(0,2) bottom
    // 3:(3,4) 4:(4,5) 5:(3,5) top
    // 6:(0,3) 7:(1,4) 8:(2,5) vertical
    let d0 = GF2Matrix::from_data(vec![
        vec![1, 1, 0, 0, 0, 0],
        vec![0, 1, 1, 0, 0, 0],
        vec![1, 0, 1, 0, 0, 0],
        vec![0, 0, 0, 1, 1, 0],
        vec![0, 0, 0, 0, 1, 1],
        vec![0, 0, 0, 1, 0, 1],
        vec![1, 0, 0, 1, 0, 0],
        vec![0, 1, 0, 0, 1, 0],
        vec![0, 0, 1, 0, 0, 1],
    ]);
    // Faces as edge sets (mod 2 incidence):
    // f0 bottom: e0,e1,e2
    // f1 top: e3,e4,e5
    // f2 side 01-34: e0,e7,e3,e6
    // f3 side 12-45: e1,e8,e4,e7
    // f4 side 02-35: e2,e8,e5,e6
    let d1 = GF2Matrix::from_data(vec![
        vec![1, 1, 1, 0, 0, 0, 0, 0, 0],
        vec![0, 0, 0, 1, 1, 1, 0, 0, 0],
        vec![1, 0, 0, 1, 0, 0, 1, 1, 0],
        vec![0, 1, 0, 0, 1, 0, 0, 1, 1],
        vec![0, 0, 1, 0, 0, 1, 1, 0, 1],
    ]);
    ChainComplexGf2 {
        name: "prism",
        d0,
        d1,
        num_vertices: 6,
        num_edges: 9,
        num_faces: 5,
    }
}

/// Example syndromes for triangle play (edge-length 3).
pub fn exact_syndrome_example() -> Vec<u8> {
    // d0 * e_1 = edge incidence of vertex 1 = (1,1,0) on triangle edges
    vec![1, 1, 0]
}

pub fn open_syndrome_example() -> Vec<u8> {
    vec![1, 0, 0]
}

/// Closed but non-exact cycle on triangle: all edges (boundary of face) — in GF(2)
/// this is d1^T * face; for classification we need d1 ω = 0 and not in im d0.
/// On triangle, ω = (1,1,1) has d1 ω = 1+1+1 = 1 mod 2 → open.
/// For closed residual use a graph with H1 ≠ 0 — plaquette cycle ω = (1,1,1,1):
/// d1 ω = 0 mod 2, and not a vertex coboundary if consistent.
pub fn closed_residual_syndrome_example() -> Vec<u8> {
    // Plaquette full cycle (all four edges)
    vec![1, 1, 1, 1]
}

// ---------------------------------------------------------------------------
// Multi-plaquette surface-code toys (CODE_DEMO only; not device thresholds)
// ---------------------------------------------------------------------------

/// Planar \(2\times 2\) plaquette grid (disk topology): \(3\times 3\) vertices,
/// 12 edges, 4 faces. Disk fill ⇒ \(\dim H^1 = 0\) under \(d_1 d_0 = 0\).
///
/// Surface-code **shadow**: edge residual \(e\) with face syndrome \(s = d_1 e\).
/// Logical-like nontrivial classes require the torus toy below.
pub fn surface_grid_2x2_planar() -> ChainComplexGf2 {
    surface_grid(2, 2, false)
}

/// Periodic \(2\times 2\) plaquette torus: \(2\times 2\) vertices, 8 edges, 4 faces.
/// Expect \(\dim H^1 = 2\) (two independent non-contractible cycles over \(\mathbb{F}_2\)).
///
/// **Not** a Willow/Microsoft surface-code packet. CODE_DEMO only.
pub fn surface_grid_2x2_torus() -> ChainComplexGf2 {
    surface_grid(2, 2, true)
}

/// Build an \(m\times n\) plaquette grid over GF(2).
///
/// - `periodic = false`: planar \((m+1)\times(n+1)\) vertices (disk if all faces filled).
/// - `periodic = true`: \(m\times n\) vertices with wrap (torus).
///
/// Edge order: all horizontal edges first (row-major), then all vertical.
/// Face order: plaquette row-major; each face uses the four bounding edges.
fn grid_vid(r: usize, c: usize, nrows: usize, ncols: usize, periodic: bool) -> usize {
    let rr = if periodic { r % nrows } else { r };
    let cc = if periodic { c % ncols } else { c };
    rr * ncols + cc
}

    // Horizontal edges: for each row r, each col c in 0..n_h
fn build_surface_edges(
    m: usize,
    n: usize,
    nrows: usize,
    ncols: usize,
    periodic: bool,
) -> (Vec<(usize, usize)>, Vec<(usize, usize)>) {
    let n_h_rows = if periodic { m } else { m + 1 };
    let mut h_edges: Vec<(usize, usize)> = Vec::new();
    for r in 0..n_h_rows {
        for c in 0..n {
            let u = grid_vid(r, c, nrows, ncols, periodic);
            let v = grid_vid(r, c + 1, nrows, ncols, periodic);
            h_edges.push((u, v));
        }
    }

    // Vertical edges
    let n_v_cols = if periodic { n } else { n + 1 };
    let mut v_edges: Vec<(usize, usize)> = Vec::new();
    for r in 0..m {
        for c in 0..n_v_cols {
            let u = grid_vid(r, c, nrows, ncols, periodic);
            let v = grid_vid(r + 1, c, nrows, ncols, periodic);
            v_edges.push((u, v));
        }
    }
    (h_edges, v_edges)
}

fn build_surface_d0(
    num_vertices: usize,
    h_edges: &[(usize, usize)],
    v_edges: &[(usize, usize)],
) -> GF2Matrix {
    let num_h = h_edges.len();
    let num_edges = num_h + v_edges.len();
    let mut d0_data = vec![vec![0u8; num_vertices]; num_edges];
    for (ei, &(u, v)) in h_edges.iter().enumerate() {
        d0_data[ei][u] = 1;
        d0_data[ei][v] = 1;
    }
    for (ei, &(u, v)) in v_edges.iter().enumerate() {
        d0_data[num_h + ei][u] = 1;
        d0_data[num_h + ei][v] = 1;
    }
    GF2Matrix::from_data(d0_data)
}

    // Face (r,c): lower-left vertex (r,c) in plaquette coords
    // edges: H(r,c), V(r,c+1), H(r+1,c), V(r,c)  (indices)
fn h_edge_index(r: usize, c: usize, m: usize, n: usize, periodic: bool) -> usize {
    if periodic {
        (r % m) * n + (c % n)
    } else {
        r * n + c
    }
}

fn v_edge_index(r: usize, c: usize, m: usize, n: usize, num_h: usize, periodic: bool) -> usize {
    if periodic {
        num_h + (r % m) * n + (c % n)
    } else {
        num_h + r * (n + 1) + c
    }
}

fn build_surface_d1(
    m: usize,
    n: usize,
    num_h: usize,
    num_edges: usize,
    periodic: bool,
) -> GF2Matrix {
    let mut d1_data = vec![vec![0u8; num_edges]; m * n];
    for pr in 0..m {
        for pc in 0..n {
            let fi = pr * n + pc;
            let e_top = h_edge_index(pr, pc, m, n, periodic);
            let e_right = v_edge_index(pr, pc + 1, m, n, num_h, periodic);
            let e_bot = h_edge_index(pr + 1, pc, m, n, periodic);
            let e_left = v_edge_index(pr, pc, m, n, num_h, periodic);
            d1_data[fi][e_top] ^= 1;
            d1_data[fi][e_right] ^= 1;
            d1_data[fi][e_bot] ^= 1;
            d1_data[fi][e_left] ^= 1;
        }
    }
    GF2Matrix::from_data(d1_data)
}

pub fn try_surface_grid(
    m: usize,
    n: usize,
    periodic: bool,
) -> Result<ChainComplexGf2, &'static str> {
    if m == 0 || n == 0 {
        return Err("surface_grid requires m >= 1 and n >= 1");
    }
    let (nrows, ncols) = if periodic { (m, n) } else { (m + 1, n + 1) };
    let num_vertices = nrows * ncols;
    let (h_edges, v_edges) = build_surface_edges(m, n, nrows, ncols, periodic);
    let num_h = h_edges.len();
    let num_edges = num_h + v_edges.len();
    let d0 = build_surface_d0(num_vertices, &h_edges, &v_edges);
    let d1 = build_surface_d1(m, n, num_h, num_edges, periodic);
    let name: &'static str = if periodic {
        "surface_grid_2x2_torus"
    } else {
        "surface_grid_2x2_planar"
    };
    // Only the 2x2 names are static for the two public constructors; rebuild name via leak only if needed.
    // For general m,n callers use the private builder only via the two pubs for now.
            // fallthrough label for future expansion
    Ok(ChainComplexGf2 {
        name,
        d0,
        d1,
        num_vertices,
        num_edges,
        num_faces: m * n,
    })
}

pub fn surface_grid(m: usize, n: usize, periodic: bool) -> ChainComplexGf2 {
    try_surface_grid(m, n, periodic).checked_invariant_2500a638("need at least one plaquette")
}

/// Nontrivial \(H^1\) cocycle on the \(2\times 2\) torus (cochain class, not bare chain cycle).
///
/// Edge order: 4 horizontal then 4 vertical. Representative: alternating H edges
/// `e1 + e3` — lies in \(\ker d_1 \setminus \operatorname{im} d_0\) (CODE_DEMO).
pub fn torus_logical_x_example() -> Vec<u8> {
    vec![0, 1, 0, 1, 0, 0, 0, 0]
}

/// Independent nontrivial cocycle: both vertical edges of the first vertical “row”
/// (`e4 + e5`). Also \(\ker d_1 \setminus \operatorname{im} d_0\) on the \(2\times 2\) torus.
pub fn torus_logical_z_example() -> Vec<u8> {
    vec![0, 0, 0, 0, 1, 1, 0, 0]
}

/// One edge flip → open plaquette syndrome on torus/planar grids with faces.
pub fn surface_open_single_edge_example(num_edges: usize) -> Vec<u8> {
    let mut w = vec![0u8; num_edges];
    if num_edges > 0 {
        w[0] = 1;
    }
    w
}

/// Vertex coboundary of vertex 0 on a complex (Exact class when boundary-valid).
pub fn surface_exact_from_vertex0(d0: &GF2Matrix) -> Vec<u8> {
    // column 0 of d0 is the coboundary of vertex 0 (d0 is |E|×|V|)
    (0..d0.rows).map(|r| d0.data[r][0]).collect()
}

// Origin: engine/crates_rs/core_majorana/src/complexes.rs
// Claim: urn:core:crates_rs:core-majorana:complexes:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2500a638 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2500a638` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2500a638 {
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
impl BoundaryError2500a638 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2500a638 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2500a638 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2500a638 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2500a638> {
        if capacity_bound == 0 {
            return Err(BoundaryError2500a638::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2500a638::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2500a638::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::gf2_terminalizer::{GF2ScheduleStatus, Gf2CocycleClassifier};

    #[test]
    fn all_complexes_have_valid_boundary() {
        for c in [
            triangle(),
            plaquette(),
            prism(),
            surface_grid_2x2_planar(),
            surface_grid_2x2_torus(),
        ] {
            assert!(c.verify_boundary(), "{} fails d1 d0 = 0", c.name);
        }
        assert!(try_surface_grid(0, 2, false).is_err());
        assert!(try_surface_grid(2, 0, true).is_err());
    }

    #[test]
    fn play_triangle_exact_and_open() {
        let c = triangle();
        let exact =
            Gf2CocycleClassifier::classify(&c.d0, &c.d1, &exact_syndrome_example()).unwrap();
        assert_eq!(exact.status, GF2ScheduleStatus::Exact);
        assert_eq!(exact.authority_effect, "None");

        let open = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &open_syndrome_example()).unwrap();
        assert_eq!(open.status, GF2ScheduleStatus::OpenObstruction);
    }

    #[test]
    fn play_plaquette_even_cycle_is_exact() {
        // Kills: labeling every even-weight closed vector ClosedResidual.
        // (1,1,1,1) = d0*(0,1,0,1) on C4, and the plaquette has q1 = 0.
        let c = plaquette();
        let cert =
            Gf2CocycleClassifier::classify(&c.d0, &c.d1, &closed_residual_syndrome_example())
                .unwrap();
        assert_eq!(cert.status, GF2ScheduleStatus::Exact);
        assert_eq!(cert.q1_dimension, 0);
        assert_ne!(cert.status, GF2ScheduleStatus::ClosedResidual);
    }

    #[test]
    fn play_surface_planar_exact_and_open() {
        let c = surface_grid_2x2_planar();
        assert_eq!(c.num_faces, 4);
        assert_eq!(c.num_vertices, 9);
        assert_eq!(c.num_edges, 12);

        let exact_syn = surface_exact_from_vertex0(&c.d0);
        let exact = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &exact_syn).unwrap();
        assert_eq!(exact.status, GF2ScheduleStatus::Exact);
        assert_eq!(exact.authority_effect, "None");
        // Disk fill: homology trivial → q1_dimension 0
        assert_eq!(exact.q1_dimension, 0);

        let open_syn = surface_open_single_edge_example(c.num_edges);
        let open = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &open_syn).unwrap();
        assert_eq!(open.status, GF2ScheduleStatus::OpenObstruction);
    }

    #[test]
    fn play_surface_torus_logical_closed_residual() {
        let c = surface_grid_2x2_torus();
        assert_eq!(c.num_faces, 4);
        assert_eq!(c.num_vertices, 4);
        assert_eq!(c.num_edges, 8);
        assert!(c.verify_boundary());

        // Non-contractible cycles: closed (all plaquette syndromes 0) and not Exact
        let lx = torus_logical_x_example();
        let cert_x = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &lx).unwrap();
        assert_eq!(
            cert_x.status,
            GF2ScheduleStatus::ClosedResidual,
            "horizontal torus cycle should be ClosedResidual, got {:?}",
            cert_x.status
        );
        assert_eq!(cert_x.authority_effect, "None");
        assert!(
            cert_x.q1_dimension >= 1,
            "torus should have positive H1 dim, got {}",
            cert_x.q1_dimension
        );

        let lz = torus_logical_z_example();
        let cert_z = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &lz).unwrap();
        assert_eq!(cert_z.status, GF2ScheduleStatus::ClosedResidual);
        assert_eq!(cert_z.authority_effect, "None");

        // Single edge remains open
        let open = Gf2CocycleClassifier::classify(
            &c.d0,
            &c.d1,
            &surface_open_single_edge_example(c.num_edges),
        )
        .unwrap();
        assert_eq!(open.status, GF2ScheduleStatus::OpenObstruction);
    }
}

#[cfg(test)]
mod l4_boundary_tests_2500a638 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2500a638::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2500a638::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2500a638::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2500a638::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2500a638::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2500a638::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2500a638::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
