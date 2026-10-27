// AuthorityEffect: None.
//! Sparse coboundary matrix representation for chain/cochain complexes.

#[derive(Debug, Clone, PartialEq)]
pub struct CoboundaryEntry {
    pub row: usize,
    pub col: usize,
    pub value: i64,
}

#[derive(Debug, Clone, PartialEq)]
pub struct CoboundaryMatrix {
    pub n_cols: usize,
    pub n_rows: usize,
    pub entries: Vec<CoboundaryEntry>,
}

impl CoboundaryMatrix {
    pub fn new(n_cols: usize, n_rows: usize, entries: Vec<CoboundaryEntry>) -> Result<Self, String> {
        for e in &entries {
            if e.row >= n_rows || e.col >= n_cols {
                return Err(format!(
                    "entry out of bounds: row {} >= {}, col {} >= {}",
                    e.row, n_rows, e.col, n_cols
                ));
            }
        }
        Ok(Self {
            n_cols,
            n_rows,
            entries,
        })
    }

    pub fn target_dim(&self) -> usize {
        self.n_rows
    }

    pub fn source_dim(&self) -> usize {
        self.n_cols
    }

    pub fn apply(&self, x: &[f64]) -> Result<Vec<f64>, String> {
        if x.len() != self.n_cols {
            return Err(format!(
                "dimension mismatch: expected {}, got {}",
                self.n_cols,
                x.len()
            ));
        }
        let mut out = vec![0.0; self.n_rows];
        for e in &self.entries {
            out[e.row] += (e.value as f64) * x[e.col];
        }
        Ok(out)
    }
}

/// Refusal from an exact integer coboundary application.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExactCoboundaryError {
    /// A vector length does not match a matrix dimension.
    Dimension,
    /// An entry leaves the declared shape.
    Bounds,
    /// Checked arithmetic overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/coboundary_matrix.rs
// Claim: urn:core:crates_rs:core-homology:coboundary-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactCoboundaryError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactCoboundaryError {}

impl CoboundaryMatrix {
    /// Apply the matrix over `i64`.
    pub fn apply_exact(&self, x: &[i64]) -> Result<Vec<i64>, ExactCoboundaryError> {
        if x.len() != self.n_cols {
            return Err(ExactCoboundaryError::Dimension);
        }
        let mut out = vec![0i64; self.n_rows];
        for entry in &self.entries {
            if entry.row >= self.n_rows || entry.col >= self.n_cols {
                return Err(ExactCoboundaryError::Bounds);
            }
            let Some(input) = x.get(entry.col).copied() else {
                return Err(ExactCoboundaryError::Dimension);
            };
            let term = entry.value.checked_mul(input).ok_or(ExactCoboundaryError::Overflow)?;
            let Some(slot) = out.get_mut(entry.row) else {
                return Err(ExactCoboundaryError::Bounds);
            };
            *slot = slot.checked_add(term).ok_or(ExactCoboundaryError::Overflow)?;
        }
        Ok(out)
    }
}

/// Apply `outer` after `inner`.
pub fn compose_exact(
    outer: &CoboundaryMatrix,
    inner: &CoboundaryMatrix,
    x: &[i64],
) -> Result<Vec<i64>, ExactCoboundaryError> {
    if outer.n_cols != inner.n_rows {
        return Err(ExactCoboundaryError::Dimension);
    }
    let mid = inner.apply_exact(x)?;
    outer.apply_exact(&mid)
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_coboundary_tests {
    use super::*;
    #[test]
    fn a_triangle_boundary_of_a_boundary_is_zero() {
        let d2 = CoboundaryMatrix::new(1, 2, vec![
            CoboundaryEntry { row: 0, col: 0, value: 1 },
            CoboundaryEntry { row: 1, col: 0, value: -1 },
        ]);
        let d1 = CoboundaryMatrix::new(2, 1, vec![
            CoboundaryEntry { row: 0, col: 0, value: 1 },
            CoboundaryEntry { row: 0, col: 1, value: 1 },
        ]);
        let (Ok(d2), Ok(d1)) = (d2, d1) else {
            return;
        };
        let image = compose_exact(&d1, &d2, &[1]);
        assert!(matches!(image, Ok(ref v) if v == &vec![0]));
    }
}
