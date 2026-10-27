//! Exact finite 𝔽₂ linear algebra and the gauge trichotomy.
//!
//! Implements the decision procedure in merge spec section 4.5. Given
//! `D0 ∈ 𝔽₂^{E×V}`, `D1 ∈ 𝔽₂^{F×E}` with `D1·D0 = 0`, and a parity cochain
//! `a ∈ 𝔽₂^E`, exactly one of three things is true, and each carries an explicit
//! witness:
//!
//! 1. `κ = D1·a ≠ 0` — `LocalCurvature`, witnessed by the syndrome itself. No
//!    vertex gauge can remove the sign, because `D1·D0 = 0` means every gauge
//!    move leaves `D1·a` unchanged.
//! 2. `κ = 0` and `D0·λ = a` solvable — `GaugeExact`, witnessed by `λ`.
//! 3. `κ = 0` and `a ∉ im(D0)` — `GlobalH1Obstruction`, witnessed by a separator
//!    `z` with `D0ᵀ·z = 0` and `⟨a,z⟩ = 1`.
//!
//! The separator in case 3 always exists: over 𝔽₂, `im(D0)^⊥ = ker(D0ᵀ)`, so
//! `a ∉ im(D0)` is exactly the statement that some `z ∈ ker(D0ᵀ)` pairs to 1
//! with `a`. Returning the witness rather than the bare verdict is the point --
//! a caller can replay the check without trusting this code.
//!
//! Everything is exact. There is no floating point anywhere in this module.
//!
//! AuthorityEffect: None. A verdict here is a local mathematical fact about the
//! declared board, never an admission or a terminal decision.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// A dense 𝔽₂ matrix in row-major order.
///
/// Boards in this system are small and declared explicitly, so a dense
/// representation keeps the code auditable. Bit-packing would buy speed at the
/// cost of the property that matters most here: being obviously correct.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "F2MatrixWire", into = "F2MatrixWire")]
#[serde(deny_unknown_fields)]
pub struct F2Matrix {
    rows: usize,
    cols: usize,
    data: Vec<bool>,
}

/// The wire form of an [`F2Matrix`], and the only way one enters from data.
///
/// The fields were briefly public so the struct could derive `Serialize` and
/// `Deserialize`. That gave away the shape invariant twice over: directly, since
/// `F2Matrix { rows: 3, cols: 3, data: vec![] }` became constructible, and
/// through `Deserialize`, which rebuilds a struct field by field without ever
/// calling [`F2Matrix::new`].
///
/// Routing both directions through this type keeps the derives and the
/// invariant. The JSON shape is unchanged — `{rows, cols, data}` — so anything
/// already serialized still reads.
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct F2MatrixWire {
    rows: usize,
    cols: usize,
    data: Vec<bool>,
}

impl TryFrom<F2MatrixWire> for F2Matrix {
    type Error = F2Error;

    fn try_from(wire: F2MatrixWire) -> Result<Self, Self::Error> {
        // The same constructor a caller in this process must use, so a matrix
        // arriving over the seam is held to the shape check a local one is.
        Self::new(wire.rows, wire.cols, wire.data)
    }
}

impl From<F2Matrix> for F2MatrixWire {
    fn from(matrix: F2Matrix) -> Self {
        Self {
            rows: matrix.rows,
            cols: matrix.cols,
            data: matrix.data,
        }
    }
}

#[derive(Debug, Error, PartialEq, Eq, Serialize, Deserialize)]
pub enum F2Error {
    #[error("matrix data length {len} does not match {rows}x{cols}")]
    ShapeMismatch {
        rows: usize,
        cols: usize,
        len: usize,
    },

    #[error("dimension mismatch: {left} columns cannot multiply {right} rows")]
    DimensionMismatch { left: usize, right: usize },

    #[error("vector length {actual} does not match the expected {expected}")]
    VectorLength { expected: usize, actual: usize },

    #[error("entry at row {row} column {column} is {value}; only 0 and 1 are bits")]
    EntryNotBinary {
        row: usize,
        column: usize,
        value: u8,
    },

    /// `a ∉ im(D0)` and `κ = 0`, yet no element of `ker(D0ᵀ)` pairs to 1 with
    /// `a`. Linear algebra over F2 forbids this: `im(D0)^⊥ = ker(D0ᵀ)`, so a
    /// vector outside the image must pair non-trivially with some kernel
    /// element.
    ///
    /// Reaching it means the kernel basis is not a basis, which is a defect in
    /// this crate rather than in the caller's board. It has its own variant so
    /// the operator is told that, instead of the previous
    /// `VectorLength { expected: n, actual: n }` -- a message that rendered as
    /// "vector length 3 does not match the expected 3" and was surfaced by the
    /// host as `BOARD_SHAPE_MISMATCH`, blaming well-formed input.
    #[error(
        "internal invariant broken: a is outside im(D0) with zero syndrome, but \
         ker(D0^T) has no separator for it (dim ker = {kernel_dim})"
    )]
    SeparatorMissing { kernel_dim: usize },
}

impl F2Matrix {
    pub fn new(rows: usize, cols: usize, data: Vec<bool>) -> Result<Self, F2Error> {
        if data.len() != rows * cols {
            return Err(F2Error::ShapeMismatch {
                rows,
                cols,
                len: data.len(),
            });
        }
        Ok(Self { rows, cols, data })
    }

    /// Build from rows of 0/1 integers, the shape boards are usually declared in.
    pub fn from_rows(rows: &[Vec<u8>]) -> Result<Self, F2Error> {
        let row_count = rows.len();
        let col_count = rows.first().map(Vec::len).unwrap_or(0);
        let mut data = Vec::with_capacity(row_count * col_count);
        for (row_index, row) in rows.iter().enumerate() {
            if row.len() != col_count {
                return Err(F2Error::ShapeMismatch {
                    rows: row_count,
                    cols: col_count,
                    len: rows.iter().map(Vec::len).sum(),
                });
            }
            for (column, value) in row.iter().copied().enumerate() {
                data.push(match value {
                    0 => false,
                    1 => true,
                    _ => {
                        return Err(F2Error::EntryNotBinary {
                            row: row_index,
                            column,
                            value,
                        })
                    }
                });
            }
        }
        Self::new(row_count, col_count, data)
    }

    pub fn zeros(rows: usize, cols: usize) -> Self {
        Self {
            rows,
            cols,
            data: vec![false; rows * cols],
        }
    }

    pub fn rows(&self) -> usize {
        self.rows
    }

    pub fn cols(&self) -> usize {
        self.cols
    }

    pub fn get(&self, row: usize, col: usize) -> bool {
        self.data[row * self.cols + col]
    }

    pub fn set(&mut self, row: usize, col: usize, value: bool) {
        self.data[row * self.cols + col] = value;
    }

    pub fn is_zero(&self) -> bool {
        !self.data.iter().any(|bit| *bit)
    }

    pub fn transpose(&self) -> F2Matrix {
        let mut out = F2Matrix::zeros(self.cols, self.rows);
        for r in 0..self.rows {
            for c in 0..self.cols {
                out.set(c, r, self.get(r, c));
            }
        }
        out
    }

    /// `self · other` over 𝔽₂.
    pub fn matmul(&self, other: &F2Matrix) -> Result<F2Matrix, F2Error> {
        if self.cols != other.rows {
            return Err(F2Error::DimensionMismatch {
                left: self.cols,
                right: other.rows,
            });
        }
        let mut out = F2Matrix::zeros(self.rows, other.cols);
        for r in 0..self.rows {
            for k in 0..self.cols {
                if !self.get(r, k) {
                    continue;
                }
                for c in 0..other.cols {
                    if other.get(k, c) {
                        let current = out.get(r, c);
                        out.set(r, c, !current);
                    }
                }
            }
        }
        Ok(out)
    }

    /// `self · vector` over 𝔽₂.
    pub fn apply(&self, vector: &[bool]) -> Result<Vec<bool>, F2Error> {
        if vector.len() != self.cols {
            return Err(F2Error::VectorLength {
                expected: self.cols,
                actual: vector.len(),
            });
        }
        let mut out = vec![false; self.rows];
        for (r, out_val) in out.iter_mut().enumerate() {
            let mut acc = false;
            for (c, &v) in vector.iter().enumerate() {
                if self.get(r, c) && v {
                    acc = !acc;
                }
            }
            *out_val = acc;
        }
        Ok(out)
    }

    /// Row-reduce `[self | rhs]`, returning the reduced matrix, the augmented
    /// column, and the pivot column of each row.
    fn row_reduce(&self, rhs: Option<&[bool]>) -> (F2Matrix, Vec<bool>, Vec<Option<usize>>) {
        let mut work = self.clone();
        let mut aug = rhs
            .map(<[bool]>::to_vec)
            .unwrap_or_else(|| vec![false; self.rows]);
        let mut pivots: Vec<Option<usize>> = vec![None; self.rows];

        let mut row = 0usize;
        for col in 0..self.cols {
            let Some(pivot) = (row..work.rows).find(|candidate| work.get(*candidate, col)) else {
                continue;
            };
            if pivot != row {
                for c in 0..work.cols {
                    let a = work.get(row, c);
                    let b = work.get(pivot, c);
                    work.set(row, c, b);
                    work.set(pivot, c, a);
                }
                aug.swap(row, pivot);
            }
            for other in 0..work.rows {
                if other != row && work.get(other, col) {
                    for c in 0..work.cols {
                        let value = work.get(other, c) ^ work.get(row, c);
                        work.set(other, c, value);
                    }
                    aug[other] ^= aug[row];
                }
            }
            pivots[row] = Some(col);
            row += 1;
            if row == work.rows {
                break;
            }
        }
        (work, aug, pivots)
    }

    pub fn rank(&self) -> usize {
        let (_, _, pivots) = self.row_reduce(None);
        pivots.iter().filter(|pivot| pivot.is_some()).count()
    }

    /// Solve `self · x = rhs`, or return None when no solution exists.
    pub fn solve(&self, rhs: &[bool]) -> Result<Option<Vec<bool>>, F2Error> {
        if rhs.len() != self.rows {
            return Err(F2Error::VectorLength {
                expected: self.rows,
                actual: rhs.len(),
            });
        }
        let (reduced, aug, pivots) = self.row_reduce(Some(rhs));

        // An all-zero row with a 1 in the augmented column is 0 = 1.
        for (r, &aug_val) in aug.iter().enumerate().take(reduced.rows) {
            let empty = (0..reduced.cols).all(|c| !reduced.get(r, c));
            if empty && aug_val {
                return Ok(None);
            }
        }

        let mut x = vec![false; self.cols];
        for (r, pivot) in pivots.iter().enumerate() {
            if let Some(col) = pivot {
                x[*col] = aug[r];
            }
        }
        Ok(Some(x))
    }

    /// A basis of `{x : self·x = 0}`.
    pub fn kernel_basis(&self) -> Vec<Vec<bool>> {
        let (reduced, _, pivots) = self.row_reduce(None);
        let pivot_cols: Vec<usize> = pivots.iter().filter_map(|pivot| *pivot).collect();
        let free_cols: Vec<usize> = (0..self.cols)
            .filter(|col| !pivot_cols.contains(col))
            .collect();

        let mut basis = Vec::with_capacity(free_cols.len());
        for free in &free_cols {
            let mut vector = vec![false; self.cols];
            vector[*free] = true;
            for (r, pivot) in pivots.iter().enumerate() {
                if let Some(col) = pivot {
                    if reduced.get(r, *free) {
                        vector[*col] = true;
                    }
                }
            }
            basis.push(vector);
        }
        basis
    }
}

/// `⟨left, right⟩ mod 2`.
pub fn pairing(left: &[bool], right: &[bool]) -> Result<bool, F2Error> {
    if left.len() != right.len() {
        return Err(F2Error::VectorLength {
            expected: left.len(),
            actual: right.len(),
        });
    }
    Ok(left.iter().zip(right).filter(|(a, b)| **a && **b).count() % 2 == 1)
}

/// The exact verdict for one declared gauge board.
///
/// Each variant carries the witness that makes it independently replayable.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum GaugeVerdict {
    /// `D1·D0 ≠ 0`: the input is a graded diagram or precomplex, not a cochain
    /// complex. Refused before any semantic interpretation.
    BoardInvalid { product: F2Matrix },

    /// `κ = D1·a ≠ 0`. No vertex gauge can remove the sign.
    LocalCurvature { syndrome: Vec<bool> },

    /// `a = D0·λ`. The sign is removable; `λ` is the rephasing.
    GaugeExact { lambda: Vec<bool> },

    /// `κ = 0` but `a ∉ im(D0)`, witnessed by a separator.
    GlobalH1Obstruction { separator: Vec<bool> },
}

impl GaugeVerdict {
    /// A short, stable token for traces. Not an authority status.
    pub fn token(&self) -> &'static str {
        match self {
            Self::BoardInvalid { .. } => "BOARD_INVALID",
            Self::LocalCurvature { .. } => "LOCAL_CURVATURE",
            Self::GaugeExact { .. } => "GAUGE_EXACT",
            Self::GlobalH1Obstruction { .. } => "GLOBAL_H1_OBSTRUCTION",
        }
    }
}

/// A declared finite gauge board.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GaugeBoard {
    pub d0: F2Matrix,
    pub d1: F2Matrix,
}

impl GaugeBoard {
    pub fn new(d0: F2Matrix, d1: F2Matrix) -> Self {
        Self { d0, d1 }
    }

    /// Check the chain law `D1·D0 = 0`.
    ///
    /// This runs before anything else. A nonzero product means the declared
    /// object is not a cochain complex, and calling its `D1·a` a "defect inside
    /// the complex" would be a category error.
    pub fn chain_law(&self) -> Result<Option<F2Matrix>, F2Error> {
        let product = self.d1.matmul(&self.d0)?;
        Ok(if product.is_zero() {
            None
        } else {
            Some(product)
        })
    }

    /// The full trichotomy, board validity first.
    pub fn classify(&self, a: &[bool]) -> Result<GaugeVerdict, F2Error> {
        if let Some(product) = self.chain_law()? {
            return Ok(GaugeVerdict::BoardInvalid { product });
        }

        let syndrome = self.d1.apply(a)?;
        if syndrome.iter().any(|bit| *bit) {
            return Ok(GaugeVerdict::LocalCurvature { syndrome });
        }

        if let Some(lambda) = self.d0.solve(a)? {
            return Ok(GaugeVerdict::GaugeExact { lambda });
        }

        // a ∉ im(D0) with κ = 0, so some element of ker(D0ᵀ) pairs to 1 with a.
        let transpose = self.d0.transpose();
        let basis = transpose.kernel_basis();
        let kernel_dim = basis.len();
        for candidate in basis {
            if pairing(a, &candidate)? {
                return Ok(GaugeVerdict::GlobalH1Obstruction {
                    separator: candidate,
                });
            }
        }

        // Unreachable for a consistent board: no separator would mean
        // a ∈ im(D0), which `solve` just refuted. Reported as an internal
        // invariant breach rather than a shape error, because the board is
        // well-formed and the fault would be ours -- still an error rather than
        // a panic, so a defect here costs the request and not the process.
        Err(F2Error::SeparatorMissing { kernel_dim })
    }

    /// Apply a gauge move `a ↦ a + D0·λ`.
    pub fn gauge_shift(&self, a: &[bool], lambda: &[bool]) -> Result<Vec<bool>, F2Error> {
        let shift = self.d0.apply(lambda)?;
        if shift.len() != a.len() {
            return Err(F2Error::VectorLength {
                expected: a.len(),
                actual: shift.len(),
            });
        }
        Ok(a.iter()
            .zip(shift)
            .map(|(left, right)| left ^ right)
            .collect())
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/f2.rs
// Claim: urn:core:crates_rs:pfp-runtime:f2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn m(rows: &[&[u8]]) -> F2Matrix {
        F2Matrix::from_rows(&rows.iter().map(|r| r.to_vec()).collect::<Vec<_>>()).unwrap()
    }

    fn bits(values: &[u8]) -> Vec<bool> {
        values.iter().map(|v| v % 2 == 1).collect()
    }

    /// A triangle: 3 vertices, 3 edges, 1 face. D1·D0 = 0 holds.
    fn triangle() -> GaugeBoard {
        // edges: e0 = v0+v1, e1 = v1+v2, e2 = v2+v0
        let d0 = m(&[&[1, 1, 0], &[0, 1, 1], &[1, 0, 1]]);
        // one face bounded by all three edges
        let d1 = m(&[&[1, 1, 1]]);
        GaugeBoard::new(d0, d1)
    }

    #[test]
    fn arithmetic_is_mod_two() {
        let a = m(&[&[1, 1], &[0, 1]]);
        let product = a.matmul(&a).unwrap();
        // [[1,1],[0,1]]^2 = [[1, 1+1],[0,1]] = [[1,0],[0,1]]
        assert_eq!(product, m(&[&[1, 0], &[0, 1]]));
    }

    #[test]
    fn the_triangle_satisfies_the_chain_law() {
        assert!(triangle().chain_law().unwrap().is_none());
    }

    #[test]
    fn a_board_violating_the_chain_law_is_refused_before_interpretation() {
        // D1 picks a single edge, so D1·D0 is that edge's vertex row, nonzero.
        let board = GaugeBoard::new(m(&[&[1, 1, 0], &[0, 1, 1], &[1, 0, 1]]), m(&[&[1, 0, 0]]));
        let verdict = board.classify(&bits(&[0, 0, 0])).unwrap();
        assert_eq!(verdict.token(), "BOARD_INVALID");
        assert!(matches!(verdict, GaugeVerdict::BoardInvalid { .. }));
    }

    #[test]
    fn board_invalid_outranks_a_zero_cochain() {
        // Even the all-zero cochain, which would otherwise be GAUGE_EXACT, must
        // not be interpreted on an invalid board.
        let board = GaugeBoard::new(m(&[&[1, 1, 0], &[0, 1, 1], &[1, 0, 1]]), m(&[&[1, 0, 0]]));
        assert_eq!(
            board.classify(&bits(&[0, 0, 0])).unwrap().token(),
            "BOARD_INVALID"
        );
    }

    #[test]
    fn nonzero_curvature_is_local() {
        // a = e0 alone: D1·a = 1 ≠ 0.
        let verdict = triangle().classify(&bits(&[1, 0, 0])).unwrap();
        assert_eq!(verdict.token(), "LOCAL_CURVATURE");
        match verdict {
            GaugeVerdict::LocalCurvature { syndrome } => assert_eq!(syndrome, bits(&[1])),
            other => panic!("expected local curvature, got {other:?}"),
        }
    }

    #[test]
    fn an_exact_cochain_yields_a_replayable_lambda() {
        let board = triangle();
        // a = D0·(1,0,0) = e0 + e2
        let a = board.d0.apply(&bits(&[1, 0, 0])).unwrap();
        let verdict = board.classify(&a).unwrap();
        assert_eq!(verdict.token(), "GAUGE_EXACT");

        match verdict {
            GaugeVerdict::GaugeExact { lambda } => {
                // The witness must actually reproduce a; any lambda in the coset works.
                assert_eq!(board.d0.apply(&lambda).unwrap(), a);
            }
            other => panic!("expected gauge exact, got {other:?}"),
        }
    }

    #[test]
    fn a_global_obstruction_yields_a_replayable_separator() {
        // A single loop with no faces: D1 is the zero map, so curvature always
        // vanishes and the only question is exactness. The loop cochain
        // a = (1,1,1) is closed but not a coboundary.
        let d0 = m(&[&[1, 1, 0], &[0, 1, 1], &[1, 0, 1]]);
        let d1 = F2Matrix::zeros(1, 3);
        let board = GaugeBoard::new(d0, d1);
        let a = bits(&[1, 1, 1]);

        let verdict = board.classify(&a).unwrap();
        assert_eq!(verdict.token(), "GLOBAL_H1_OBSTRUCTION");

        match verdict {
            GaugeVerdict::GlobalH1Obstruction { separator } => {
                // The two defining properties of a separator, checked here so the
                // test fails if the witness is merely well-shaped.
                assert!(board
                    .d0
                    .transpose()
                    .apply(&separator)
                    .unwrap()
                    .iter()
                    .all(|b| !b));
                assert!(pairing(&a, &separator).unwrap());
            }
            other => panic!("expected global obstruction, got {other:?}"),
        }
    }

    #[test]
    fn the_three_outcomes_are_distinguished_on_one_board() {
        // Acceptance criterion 10: the same 𝔽₂ fixture separates all three.
        let d0 = m(&[&[1, 1, 0], &[0, 1, 1], &[1, 0, 1]]);
        let loop_board = GaugeBoard::new(d0.clone(), F2Matrix::zeros(1, 3));
        let faced_board = GaugeBoard::new(d0.clone(), m(&[&[1, 1, 1]]));

        assert_eq!(
            faced_board.classify(&bits(&[1, 0, 0])).unwrap().token(),
            "LOCAL_CURVATURE"
        );
        let exact = d0.apply(&bits(&[1, 0, 0])).unwrap();
        assert_eq!(faced_board.classify(&exact).unwrap().token(), "GAUGE_EXACT");
        assert_eq!(
            loop_board.classify(&bits(&[1, 1, 1])).unwrap().token(),
            "GLOBAL_H1_OBSTRUCTION"
        );
    }

    #[test]
    fn a_gauge_move_preserves_the_syndrome() {
        // The structural reason LOCAL_CURVATURE is not repairable by gauge:
        // D1·(a + D0·λ) = D1·a because D1·D0 = 0.
        let board = triangle();
        let a = bits(&[1, 0, 0]);
        let before = board.d1.apply(&a).unwrap();
        for lambda in [bits(&[1, 0, 0]), bits(&[0, 1, 1]), bits(&[1, 1, 1])] {
            let shifted = board.gauge_shift(&a, &lambda).unwrap();
            assert_eq!(board.d1.apply(&shifted).unwrap(), before);
        }
    }

    #[test]
    fn solve_reports_unsolvable_systems() {
        // x + y = 1 and x + y = 0 cannot both hold.
        let a = m(&[&[1, 1], &[1, 1]]);
        assert_eq!(a.solve(&bits(&[1, 0])).unwrap(), None);
    }

    #[test]
    fn kernel_basis_vectors_are_annihilated() {
        let a = m(&[&[1, 1, 0], &[0, 1, 1]]);
        let basis = a.kernel_basis();
        assert!(!basis.is_empty());
        for vector in basis {
            assert!(a.apply(&vector).unwrap().iter().all(|bit| !bit));
        }
    }

    #[test]
    fn rank_plus_nullity_is_the_column_count() {
        let a = m(&[&[1, 1, 0], &[0, 1, 1], &[1, 0, 1]]);
        assert_eq!(a.rank() + a.kernel_basis().len(), a.cols());
    }

    #[test]
    fn dimension_mismatches_are_errors_not_panics() {
        let a = m(&[&[1, 1]]);
        let b = m(&[&[1, 1]]);
        assert!(a.matmul(&b).is_err());
        assert!(a.apply(&bits(&[1])).is_err());
    }
}
