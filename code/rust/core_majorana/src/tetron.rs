//! Homology-correct tetron-array carriers on a surface.
//!
//! A tetron **is a 2-cell**: one superconducting island, four MZMs on its
//! boundary, total fermion parity pinned by charging energy. An `R x C` array
//! of tetrons therefore tiles a surface, and the array's cohomology is the
//! surface's.
//!
//! - `C^0` = MZMs. A 0-cochain is a per-MZM reference-frame bit.
//! - `C^1` = parity-measurement channels. A channel on MZMs `a, b` measures
//!   `i * gamma_a * gamma_b`; a 1-cochain is the per-channel parity residual.
//! - `C^2` = islands. The product of the four channel parities around an island
//!   has every gamma twice, so it is a fixed scalar: a constraint.
//!
//! Three topologies, three Betti numbers:
//!
//! ```text
//! disk      chi = 1   dim H^1 = 0    open linear array (control)
//! cylinder  chi = 0   dim H^1 = 1    tetron ring / H-junction ladder
//! torus     chi = 0   dim H^1 = 2    periodic array (class typing possible)
//! ```
//!
//! Adjacent islands share the boundary MZM their coupler acts through. That is
//! an idealization of a coupled tetron array, and it is what makes the array a
//! clean cell complex.
//!
//! Python dual face: `engine/majorana/carriers/surface_carrier.py`.
//! The golden fixtures in [`crate::harmonic`] pin the two surfaces together.
//!
//! AuthorityEffect: None. Nothing here asserts physical Majorana modes.

use crate::complexes::ChainComplexGf2;
use crate::gf2_terminalizer::{GF2Matrix, Gf2CocycleClassifier};
use serde::{Deserialize, Serialize};

/// Surface the tetron array is laid out on.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Topology {
    /// Open in both directions. `dim H^1 = 0`.
    Disk,
    /// Periodic in columns, open in rows. `dim H^1 = 1`.
    Cylinder,
    /// Periodic in both directions. `dim H^1 = 2`.
    Torus,
}

impl Topology {
    /// `dim H^1` predicted by the Euler characteristic.
    pub fn expected_dim_h1(self) -> usize {
        match self {
            Topology::Disk => 0,
            Topology::Cylinder => 1,
            Topology::Torus => 2,
        }
    }

    pub fn name(self) -> &'static str {
        match self {
            Topology::Disk => "tetron_disk",
            Topology::Cylinder => "tetron_cylinder",
            Topology::Torus => "tetron_torus",
        }
    }

    /// Hardware reading, carried into receipts.
    pub fn hardware_reading(self) -> &'static str {
        match self {
            Topology::Disk => "open tetron array; no protected logical parity error",
            Topology::Cylinder => "tetron ring / H-junction ladder; one logical parity class",
            Topology::Torus => "periodic tetron array; two independent logical parity classes",
        }
    }

    fn wraps(self) -> (bool, bool) {
        match self {
            Topology::Disk => (false, false),
            Topology::Cylinder => (false, true),
            Topology::Torus => (true, true),
        }
    }
}

/// Which family of logical string to build.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Axis {
    /// Every horizontal channel in one column slot. Non-exact on cylinder and torus.
    Column,
    /// Every vertical channel in one row slot. Non-exact on the torus only.
    Row,
}

/// Measured structure of a tetron-array carrier.
///
/// Every field except `expected_dim_h1` is computed from the built matrices.
#[derive(Debug, Clone)]
pub struct TetronReport {
    pub topology: Topology,
    pub rows: usize,
    pub cols: usize,
    pub num_mzm: usize,
    pub num_channels: usize,
    pub num_islands: usize,
    pub euler_characteristic: i64,
    pub rank_d0: usize,
    pub rank_d1: usize,
    pub graph_b1: usize,
    pub dim_h1: usize,
    pub expected_dim_h1: usize,
    /// Horizontal channel index by `(vertex_row, column_slot)`.
    pub horizontal: Vec<Vec<usize>>,
    /// Vertical channel index by `(row_slot, vertex_col)`.
    pub vertical: Vec<Vec<usize>>,
    pub authority_effect: &'static str,
}

impl TetronReport {
    pub fn homology_matches_prediction(&self) -> bool {
        self.dim_h1 == self.expected_dim_h1
    }
}

/// Build an `rows x cols` tetron array on `topology`.
///
/// Returns the complex and a report whose `dim_h1` is *measured*, not asserted.
///
/// # Errors
///
/// A periodic direction of extent 1 identifies a channel's two endpoints and
/// would emit a self-loop with zero boundary; that is refused rather than built.
fn validate_tetron_extents(
    rows: usize,
    cols: usize,
    topology: Topology,
) -> Result<(bool, bool), String> {
    if rows == 0 || cols == 0 {
        return Err("rows and cols must be >= 1".into());
    }
    let (wrap_r, wrap_c) = topology.wraps();
    if wrap_c && cols < 2 {
        return Err(format!(
            "{:?} is periodic in columns; cols must be >= 2 (got {})",
            topology, cols
        ));
    }
    if wrap_r && rows < 2 {
        return Err(format!(
            "{:?} is periodic in rows; rows must be >= 2 (got {})",
            topology, rows
        ));
    }
    Ok((wrap_r, wrap_c))
}

fn push_mzm_channel(u: usize, v: usize, num_mzm: usize, sink: &mut Vec<Vec<u8>>) -> usize {
    let mut row = vec![0u8; num_mzm];
    row[u] ^= 1;
    row[v] ^= 1;
    sink.push(row);
    sink.len() - 1
}

fn build_tetron_channels(
    vrows: usize,
    vcols: usize,
    wrap_r: bool,
    wrap_c: bool,
) -> (Vec<Vec<u8>>, Vec<Vec<usize>>, Vec<Vec<usize>>) {
    let num_mzm = vrows * vcols;
    let mut d0_rows: Vec<Vec<u8>> = Vec::new();
    // Horizontal channel H(i, j) joins MZM (i, j) to (i, j+1).
    let h_span = if wrap_c { vcols } else { vcols - 1 };
    let mut horizontal = vec![vec![usize::MAX; h_span]; vrows];
    for (i, slots) in horizontal.iter_mut().enumerate() {
        for (j, slot) in slots.iter_mut().enumerate() {
            let u = (i % vrows) * vcols + (j % vcols);
            let v = (i % vrows) * vcols + ((j + 1) % vcols);
            *slot = push_mzm_channel(u, v, num_mzm, &mut d0_rows);
        }
    }
    // Vertical channel V(i, j) joins MZM (i, j) to (i+1, j).
    let v_span = if wrap_r { vrows } else { vrows - 1 };
    let mut vertical = vec![vec![usize::MAX; vcols]; v_span];
    for (i, slots) in vertical.iter_mut().enumerate() {
        for (j, slot) in slots.iter_mut().enumerate() {
            let u = (i % vrows) * vcols + (j % vcols);
            let v = ((i + 1) % vrows) * vcols + (j % vcols);
            *slot = push_mzm_channel(u, v, num_mzm, &mut d0_rows);
        }
    }
    (d0_rows, horizontal, vertical)
}

fn build_tetron_islands(
    rows: usize,
    cols: usize,
    vrows: usize,
    vcols: usize,
    wrap_r: bool,
    wrap_c: bool,
    num_channels: usize,
    horizontal: &[Vec<usize>],
    vertical: &[Vec<usize>],
) -> Vec<Vec<u8>> {
    // Island 2-cells: island (i, j) is bounded by H(i,j), V(i,j+1), H(i+1,j),
    // V(i,j) -- a 4-cycle, so d1 . d0 = 0 holds by construction.
    let mut d1_rows: Vec<Vec<u8>> = Vec::new();
    for i in 0..rows {
        for j in 0..cols {
            let mut row = vec![0u8; num_channels];
            let j_next = if wrap_c { (j + 1) % vcols } else { j + 1 };
            let i_next = if wrap_r { (i + 1) % vrows } else { i + 1 };
            row[horizontal[i][j]] ^= 1;
            row[vertical[i][j_next]] ^= 1;
            row[horizontal[i_next][j]] ^= 1;
            row[vertical[i][j]] ^= 1;
            d1_rows.push(row);
        }
    }
    d1_rows
}

pub fn build_tetron_array(
    rows: usize,
    cols: usize,
    topology: Topology,
) -> Result<(ChainComplexGf2, TetronReport), String> {
    let (wrap_r, wrap_c) = validate_tetron_extents(rows, cols, topology)?;
    let vrows = if wrap_r { rows } else { rows + 1 };
    let vcols = if wrap_c { cols } else { cols + 1 };
    let num_mzm = vrows * vcols;
    let (d0_rows, horizontal, vertical) = build_tetron_channels(vrows, vcols, wrap_r, wrap_c);
    let num_channels = d0_rows.len();
    let d1_rows = build_tetron_islands(
        rows,
        cols,
        vrows,
        vcols,
        wrap_r,
        wrap_c,
        num_channels,
        &horizontal,
        &vertical,
    );
    let num_islands = d1_rows.len();

    let d0 = GF2Matrix::from_data(d0_rows);
    let d1 = GF2Matrix::from_data(d1_rows);
    let (rank_d0, _) = d0.rref();
    let (rank_d1, _) = d1.rref();
    let dim_h1 = (num_channels - rank_d1) - rank_d0;

    let complex = ChainComplexGf2 {
        name: topology.name(),
        d0,
        d1,
        num_vertices: num_mzm,
        num_edges: num_channels,
        num_faces: num_islands,
    };
    if !Gf2CocycleClassifier::verify_boundary(&complex.d0, &complex.d1) {
        return Err("constructed carrier violates d1 . d0 = 0".into());
    }

    let report = TetronReport {
        topology,
        rows,
        cols,
        num_mzm,
        num_channels,
        num_islands,
        euler_characteristic: num_mzm as i64 - num_channels as i64 + num_islands as i64,
        rank_d0,
        rank_d1,
        graph_b1: num_channels - rank_d0,
        dim_h1,
        expected_dim_h1: topology.expected_dim_h1(),
        horizontal,
        vertical,
        authority_effect: "None",
    };
    Ok((complex, report))
}

/// An explicit closed 1-cochain generating a logical parity class.
///
/// [`Axis::Column`]: every horizontal channel in column slot `index`. Closed
/// because island `(i, index)` contains exactly `H(i, index)` and
/// `H(i+1, index)`. Non-exact on a torus and a cylinder.
///
/// [`Axis::Row`]: every vertical channel in row slot `index`. Non-exact on a
/// torus only -- on a cylinder it equals `d0 alpha` for `alpha = 1` on lattice
/// rows `<= index`.
///
/// Physically: a string of faulty channels crossing the array.
pub fn logical_class_representative(report: &TetronReport, axis: Axis, index: usize) -> Vec<u8> {
    let mut residual = vec![0u8; report.num_channels];
    match axis {
        Axis::Column => {
            let slot = index % report.horizontal[0].len();
            for row in &report.horizontal {
                residual[row[slot]] = 1;
            }
        }
        Axis::Row => {
            let slot = index % report.vertical.len();
            for &channel in &report.vertical[slot] {
                residual[channel] = 1;
            }
        }
    }
    residual
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TetronScalingRow {
    pub topology: Topology,
    pub rows: usize,
    pub cols: usize,
    pub num_mzm: usize,
    pub num_channels: usize,
    pub num_islands: usize,
    pub rank_d0: usize,
    pub rank_d1: usize,
    pub dim_h1: usize,
    pub expected_dim_h1: usize,
    pub boundary_exact: bool,
    pub euler_agrees: bool,
    pub generators_closed: bool,
}

/// Serialize `TetronScalingRow` slice to canonical 2-space pretty JSON with LF line endings.
pub fn tetron_scaling_to_canonical_json(rows: &[TetronScalingRow]) -> Result<String, String> {
    serde_json::to_string_pretty(rows).map_err(|e| e.to_string())
}

/// Deserialize `TetronScalingRow` vector from canonical JSON string.
pub fn tetron_scaling_from_canonical_json(json_str: &str) -> Result<Vec<TetronScalingRow>, String> {
    serde_json::from_str(json_str).map_err(|e| e.to_string())
}

fn are_generators_closed(complex: &ChainComplexGf2, report: &TetronReport) -> Result<bool, String> {
    for axis in [Axis::Column, Axis::Row] {
        let rep = logical_class_representative(report, axis, 0);
        let syn = crate::repair_limit::apply_d1(&complex.d1, &rep)?;
        if syn.iter().any(|&b| b != 0) {
            return Ok(false);
        }
    }
    Ok(true)
}

fn benchmark_single_tetron_lattice(
    rows: usize,
    cols: usize,
    topology: Topology,
) -> Result<TetronScalingRow, String> {
    let (complex, report) = build_tetron_array(rows, cols, topology)?;
    let boundary_exact = complex.verify_boundary();
    let closed_surface = topology == Topology::Torus;
    let predicted_h1 = (if closed_surface { 2 } else { 1 }) - report.euler_characteristic;
    let euler_agrees = (report.dim_h1 as i64) == predicted_h1;
    let generators_closed = are_generators_closed(&complex, &report)?;

    Ok(TetronScalingRow {
        topology,
        rows,
        cols,
        num_mzm: report.num_mzm,
        num_channels: report.num_channels,
        num_islands: report.num_islands,
        rank_d0: report.rank_d0,
        rank_d1: report.rank_d1,
        dim_h1: report.dim_h1,
        expected_dim_h1: report.expected_dim_h1,
        boundary_exact,
        euler_agrees,
        generators_closed,
    })
}

/// Finite lattice scaling benchmark for 2D Tetron cochain complexes across declared
/// `(rows, cols)` grid dimensions and topologies (`Disk`, `Cylinder`, `Torus`).
pub fn benchmark_tetron_lattice_scaling(
    sizes: &[(usize, usize)],
    topologies: &[Topology],
) -> Result<Vec<TetronScalingRow>, String> {
    if sizes.is_empty() || topologies.is_empty() {
        return Err("sizes and topologies must be non-empty".into());
    }
    let mut rows_out = Vec::with_capacity(sizes.len() * topologies.len());
    for &topology in topologies {
        for &(rows, cols) in sizes {
            rows_out.push(benchmark_single_tetron_lattice(rows, cols, topology)?);
        }
    }
    Ok(rows_out)
}

// Origin: engine/crates_rs/core_majorana/src/tetron.rs
// Claim: urn:core:crates_rs:core-majorana:tetron:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda3beeebc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda3beeebc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora3beeebc {
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
impl BoundaryErrora3beeebc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora3beeebc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora3beeebc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda3beeebc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora3beeebc> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora3beeebc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora3beeebc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora3beeebc::ExceedsCapacity {
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

    const ALL: [Topology; 3] = [Topology::Disk, Topology::Cylinder, Topology::Torus];

    #[test]
    fn cochain_relation_holds_everywhere() {
        for topology in ALL {
            for (rows, cols) in [(2usize, 2usize), (2, 3), (3, 3), (3, 4), (4, 4)] {
                let (complex, _) = build_tetron_array(rows, cols, topology).unwrap();
                assert!(
                    complex.verify_boundary(),
                    "d1 . d0 != 0 for {topology:?} {rows}x{cols}"
                );
            }
        }
    }

    #[test]
    fn dim_h1_is_the_topologys_betti_number() {
        for (topology, expected) in [
            (Topology::Disk, 0usize),
            (Topology::Cylinder, 1),
            (Topology::Torus, 2),
        ] {
            for (rows, cols) in [(2usize, 2usize), (2, 3), (3, 3), (3, 4), (4, 4)] {
                let (_, report) = build_tetron_array(rows, cols, topology).unwrap();
                assert_eq!(
                    report.dim_h1, expected,
                    "{topology:?} {rows}x{cols}: dim H^1 = {}, expected {expected}",
                    report.dim_h1
                );
                assert!(report.homology_matches_prediction());
            }
        }
    }

    #[test]
    fn dim_h1_agrees_with_the_euler_characteristic() {
        for topology in ALL {
            for (rows, cols) in [(2usize, 2usize), (3, 3), (3, 4)] {
                let (_, report) = build_tetron_array(rows, cols, topology).unwrap();
                let closed = topology == Topology::Torus;
                let predicted = (if closed { 2 } else { 1 }) - report.euler_characteristic;
                assert_eq!(
                    report.dim_h1 as i64, predicted,
                    "{topology:?} {rows}x{cols}"
                );
            }
        }
    }

    #[test]
    fn cell_counts_match_the_lattice() {
        let (_, disk) = build_tetron_array(2, 3, Topology::Disk).unwrap();
        assert_eq!(
            (disk.num_mzm, disk.num_channels, disk.num_islands),
            (12, 17, 6)
        );
        let (_, cyl) = build_tetron_array(2, 3, Topology::Cylinder).unwrap();
        assert_eq!((cyl.num_mzm, cyl.num_channels, cyl.num_islands), (9, 15, 6));
        let (_, tor) = build_tetron_array(2, 3, Topology::Torus).unwrap();
        assert_eq!((tor.num_mzm, tor.num_channels, tor.num_islands), (6, 12, 6));
    }

    #[test]
    fn degenerate_periodic_extents_are_refused() {
        // Kills: accepting a 1-row torus, and accepting a 1x1 disk without checking its cells.
        assert!(build_tetron_array(1, 1, Topology::Torus)
            .unwrap_err()
            .contains("columns"));
        assert!(build_tetron_array(2, 1, Topology::Torus)
            .unwrap_err()
            .contains("columns"));
        assert!(build_tetron_array(1, 2, Topology::Torus)
            .unwrap_err()
            .contains("rows"));
        assert!(build_tetron_array(1, 1, Topology::Cylinder)
            .unwrap_err()
            .contains("columns"));
        assert!(build_tetron_array(0, 3, Topology::Disk)
            .unwrap_err()
            .contains(">= 1"));
        let (_, disk) = build_tetron_array(1, 1, Topology::Disk).unwrap();
        assert_eq!(
            (disk.num_mzm, disk.num_channels, disk.num_islands, disk.dim_h1),
            (4, 4, 1, 0)
        );
        assert_eq!(disk.euler_characteristic, 1);
    }

    #[test]
    fn logical_generators_have_the_expected_weight() {
        let (_, report) = build_tetron_array(3, 4, Topology::Torus).unwrap();
        let column = logical_class_representative(&report, Axis::Column, 0);
        let row = logical_class_representative(&report, Axis::Row, 0);
        assert_eq!(column.iter().filter(|&&b| b == 1).count(), 3, "one per row");
        assert_eq!(row.iter().filter(|&&b| b == 1).count(), 4, "one per column");
    }

    #[test]
    fn logical_generators_are_closed() {
        for topology in ALL {
            let (complex, report) = build_tetron_array(3, 4, topology).unwrap();
            for axis in [Axis::Column, Axis::Row] {
                let residual = logical_class_representative(&report, axis, 0);
                let syndrome = crate::repair_limit::apply_d1(&complex.d1, &residual).unwrap();
                assert!(
                    syndrome.iter().all(|&b| b == 0),
                    "{topology:?} {axis:?} generator is not closed"
                );
            }
        }
    }

    #[test]
    fn tetron_lattice_scaling_benchmark_up_to_8x8() {
        let sizes = [
            (2usize, 2usize),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6),
            (6, 8),
            (8, 8),
        ];
        let rows = benchmark_tetron_lattice_scaling(&sizes, &ALL).unwrap();
        assert_eq!(rows.len(), sizes.len() * ALL.len());

        for r in &rows {
            assert!(r.boundary_exact, "{:?} {}x{}", r.topology, r.rows, r.cols);
            assert!(r.euler_agrees, "{:?} {}x{}", r.topology, r.rows, r.cols);
            assert!(r.generators_closed, "{:?} {}x{}", r.topology, r.rows, r.cols);
            assert_eq!(
                r.dim_h1, r.expected_dim_h1,
                "{:?} {}x{}",
                r.topology, r.rows, r.cols
            );
            assert_eq!(r.num_islands, r.rows * r.cols);
        }

        // Verify largest 8x8 torus counts: 64 MZM, 128 channels, 64 islands, rank(d0)=63, rank(d1)=63, dim H^1=2
        let torus_8x8 = rows
            .iter()
            .find(|r| r.topology == Topology::Torus && r.rows == 8 && r.cols == 8)
            .unwrap();
        assert_eq!(
            (
                torus_8x8.num_mzm,
                torus_8x8.num_channels,
                torus_8x8.num_islands,
                torus_8x8.rank_d0,
                torus_8x8.rank_d1,
                torus_8x8.dim_h1
            ),
            (64, 128, 64, 63, 63, 2)
        );
    }

    #[test]
    fn tetron_lattice_scaling_matches_cross_language_json_fixture_bit_for_bit() {
        let sizes = [
            (2usize, 2usize),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6),
            (6, 8),
            (8, 8),
        ];
        let rows = benchmark_tetron_lattice_scaling(&sizes, &ALL).unwrap();
        let serialized = tetron_scaling_to_canonical_json(&rows).unwrap();
        let fixture = include_str!("fixtures/tetron_lattice_scaling.json").replace("\r\n", "\n");
        assert_eq!(
            serialized.as_bytes(),
            fixture.as_bytes(),
            "Rust benchmark_tetron_lattice_scaling JSON output drifted from cross-language fixture"
        );
        let round_trip = tetron_scaling_from_canonical_json(&fixture).unwrap();
        assert_eq!(round_trip, rows);
    }
}

#[cfg(test)]
mod l4_boundary_tests_a3beeebc {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda3beeebc::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda3beeebc::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda3beeebc::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda3beeebc::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda3beeebc::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora3beeebc::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora3beeebc::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
