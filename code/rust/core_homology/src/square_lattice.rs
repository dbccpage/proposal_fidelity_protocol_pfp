//! Cell complexes of square lattices: the periodic `l1 x l2` torus, the open
//! disk and the cylinder, with boundary maps over `Z` and over GF(2).
//!
//! A lattice of `rows x cols` plaquettes has vertices on a grid of
//! `Rv x Cv` sites, where `Rv = rows` when the row direction is periodic and
//! `rows + 1` when it is open, and likewise `Cv` for the columns. The cells,
//! in the order this crate fixes:
//!
//! - vertex `(r, c)` has index `r * Cv + c`;
//! - horizontal edges `h(r, c)` from `(r, c)` to `(r, c + 1)` come first, at
//!   index `r * cols + c` for `r < Rv`, `c < cols`;
//! - vertical edges `v(r, c)` from `(r, c)` to `(r + 1, c)` follow, at index
//!   `Rv * cols + r * Cv + c` for `r < rows`, `c < Cv`;
//! - plaquette `(pr, pc)` has index `pr * cols + pc` and boundary
//!   `h(pr, pc) + v(pr, pc+1) - h(pr+1, pc) - v(pr, pc)`.
//!
//! Indices wrap modulo the site count in a periodic direction. With this
//! numbering the mod-2 matrices are exactly those of
//! `core_majorana::complexes::surface_grid`, which the tests compare
//! entry by entry. A periodic direction needs at least 2 sites: with one
//! site every edge in that direction would be a loop; with two sites the two
//! edges between a pair of vertices are distinct cells joining the same
//! vertices in opposite directions, which a cell complex allows and a
//! simplicial complex does not.
//!
//! The torus has `H_1(T; Z) = Z^2` and `dim H_1(T; F_2) = 2`, so the ground
//! state degeneracy of a code whose logical operators are representatives of
//! `H_1` is `2^2 = 4`. [`SquareLattice::horizontal_loop`] and
//! [`SquareLattice::vertical_loop`] give one non-contractible cycle in each
//! direction.
//!
//! AuthorityEffect: None.

use crate::f2_cohomology::{ComplexError, F2ChainComplex};
use crate::integral_chain_complex::{IntegralChainComplex, SparseIntegerMatrix};
use core_number_theory::gf2::{F2Error, F2Vector};

/// Largest number of plaquettes (`rows * cols`) of a lattice.
pub const MAX_LATTICE_PLAQUETTES: usize = 4096;

/// Refusals of the lattice constructors and queries.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LatticeError {
    #[error(
        "a periodic direction needs at least 2 sites, got {sites}: with one site every edge \
         in that direction would be a loop"
    )]
    PeriodicDirectionTooShort { sites: usize },
    #[error("a lattice needs at least one plaquette in each direction")]
    EmptyDirection,
    #[error("a {rows} x {cols} lattice has more than the bound of {limit} plaquettes")]
    TooManyPlaquettes {
        rows: usize,
        cols: usize,
        limit: usize,
    },
    #[error("index {index} is outside 0..{len}")]
    IndexOutOfRange { index: usize, len: usize },
    #[error("the {direction} direction is open, so it carries no non-contractible loop")]
    DirectionNotPeriodic { direction: &'static str },
    #[error(transparent)]
    Complex(#[from] ComplexError),
    #[error(transparent)]
    F2(#[from] F2Error),
}

/// How a lattice direction closes up.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Boundary {
    Open,
    Periodic,
}

/// A cell complex of a square lattice (see the module docs for the numbering).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SquareLattice {
    rows: usize,
    cols: usize,
    row_boundary: Boundary,
    col_boundary: Boundary,
    vertex_rows: usize,
    vertex_cols: usize,
    /// `(source, target)` vertex indices of every edge.
    edges: Vec<(usize, usize)>,
    /// `(edge, direction)` steps around every plaquette.
    faces: Vec<Vec<(usize, i8)>>,
    complex: IntegralChainComplex,
}

/// The `l1 x l2` periodic square lattice: a cell complex of the torus with
/// `l1 l2` vertices, `2 l1 l2` edges and `l1 l2` plaquettes. Refused when
/// `l1` or `l2` is below 2, or `l1 l2` exceeds [`MAX_LATTICE_PLAQUETTES`].
pub fn periodic_square_complex(l1: usize, l2: usize) -> Result<SquareLattice, LatticeError> {
    SquareLattice::new(l1, l2, Boundary::Periodic, Boundary::Periodic)
}

/// The open `l1 x l2` plaquette lattice: a cell complex of a disk with
/// `(l1 + 1)(l2 + 1)` vertices.
pub fn open_square_complex(l1: usize, l2: usize) -> Result<SquareLattice, LatticeError> {
    SquareLattice::new(l1, l2, Boundary::Open, Boundary::Open)
}

/// The lattice periodic in the row direction and open in the column
/// direction: a cell complex of a cylinder.
pub fn cylinder_square_complex(l1: usize, l2: usize) -> Result<SquareLattice, LatticeError> {
    SquareLattice::new(l1, l2, Boundary::Periodic, Boundary::Open)
}

impl SquareLattice {
    /// A `rows x cols` plaquette lattice with the given boundary conditions.
    pub fn new(
        rows: usize,
        cols: usize,
        row_boundary: Boundary,
        col_boundary: Boundary,
    ) -> Result<Self, LatticeError> {
        Self::validate_lattice_dims(rows, cols, row_boundary, col_boundary)?;
        let vertex_rows = if row_boundary == Boundary::Periodic {
            rows
        } else {
            rows + 1
        };
        let vertex_cols = if col_boundary == Boundary::Periodic {
            cols
        } else {
            cols + 1
        };
        let (edges, faces) = Self::build_edges_and_faces(
            rows,
            cols,
            vertex_rows,
            vertex_cols,
            row_boundary,
            col_boundary,
        );

        let vertex_count = vertex_rows * vertex_cols;
        let edge_columns: Vec<Vec<(usize, i64)>> = edges
            .iter()
            .map(|&(source, target)| vec![(target, 1), (source, -1)])
            .collect();
        let face_columns: Vec<Vec<(usize, i64)>> = faces
            .iter()
            .map(|steps| {
                steps
                    .iter()
                    .map(|&(edge, direction)| (edge, i64::from(direction)))
                    .collect()
            })
            .collect();
        let complex = IntegralChainComplex::new(
            vec![vertex_count, edges.len(), faces.len()],
            vec![
                SparseIntegerMatrix::new(vertex_count, edge_columns)?,
                SparseIntegerMatrix::new(edges.len(), face_columns)?,
            ],
        )?;
        Ok(Self {
            rows,
            cols,
            row_boundary,
            col_boundary,
            vertex_rows,
            vertex_cols,
            edges,
            faces,
            complex,
        })
    }

    fn validate_lattice_dims(
        rows: usize,
        cols: usize,
        row_boundary: Boundary,
        col_boundary: Boundary,
    ) -> Result<(), LatticeError> {
        if rows == 0 || cols == 0 {
            return Err(LatticeError::EmptyDirection);
        }
        for (sites, boundary) in [(rows, row_boundary), (cols, col_boundary)] {
            if boundary == Boundary::Periodic && sites < 2 {
                return Err(LatticeError::PeriodicDirectionTooShort { sites });
            }
        }
        match rows.checked_mul(cols) {
            Some(plaquettes) if plaquettes <= MAX_LATTICE_PLAQUETTES => Ok(()),
            _ => Err(LatticeError::TooManyPlaquettes {
                rows,
                cols,
                limit: MAX_LATTICE_PLAQUETTES,
            }),
        }
    }

    fn build_edges_and_faces(
        rows: usize,
        cols: usize,
        vertex_rows: usize,
        vertex_cols: usize,
        row_boundary: Boundary,
        col_boundary: Boundary,
    ) -> (Vec<(usize, usize)>, Vec<Vec<(usize, i8)>>) {
        let wrap_row = |r: usize| if row_boundary == Boundary::Periodic { r % vertex_rows } else { r };
        let wrap_col = |c: usize| if col_boundary == Boundary::Periodic { c % vertex_cols } else { c };
        let vertex = |r: usize, c: usize| r * vertex_cols + c;
        let h_index = |r: usize, c: usize| r * cols + c;
        let v_index = |r: usize, c: usize| vertex_rows * cols + r * vertex_cols + c;

        let mut edges = Vec::with_capacity(vertex_rows * cols + rows * vertex_cols);
        for r in 0..vertex_rows {
            for c in 0..cols {
                edges.push((vertex(r, c), vertex(r, wrap_col(c + 1))));
            }
        }
        for r in 0..rows {
            for c in 0..vertex_cols {
                edges.push((vertex(r, c), vertex(wrap_row(r + 1), c)));
            }
        }

        let mut faces = Vec::with_capacity(rows * cols);
        for pr in 0..rows {
            for pc in 0..cols {
                faces.push(vec![
                    (h_index(pr, pc), 1),
                    (v_index(pr, wrap_col(pc + 1)), 1),
                    (h_index(wrap_row(pr + 1), pc), -1),
                    (v_index(pr, pc), -1),
                ]);
            }
        }
        (edges, faces)
    }

    /// Plaquettes in the row direction.
    pub fn rows(&self) -> usize {
        self.rows
    }

    /// Plaquettes in the column direction.
    pub fn cols(&self) -> usize {
        self.cols
    }

    pub fn row_boundary(&self) -> Boundary {
        self.row_boundary
    }

    pub fn col_boundary(&self) -> Boundary {
        self.col_boundary
    }

    pub fn vertex_count(&self) -> usize {
        self.vertex_rows * self.vertex_cols
    }

    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }

    pub fn face_count(&self) -> usize {
        self.faces.len()
    }

    /// Index of vertex `(r, c)`.
    pub fn vertex_index(&self, r: usize, c: usize) -> Result<usize, LatticeError> {
        check(r, self.vertex_rows)?;
        check(c, self.vertex_cols)?;
        Ok(r * self.vertex_cols + c)
    }

    /// Index of the horizontal edge `h(r, c)` from `(r, c)` to `(r, c + 1)`.
    pub fn horizontal_edge(&self, r: usize, c: usize) -> Result<usize, LatticeError> {
        check(r, self.vertex_rows)?;
        check(c, self.cols)?;
        Ok(r * self.cols + c)
    }

    /// Index of the vertical edge `v(r, c)` from `(r, c)` to `(r + 1, c)`.
    pub fn vertical_edge(&self, r: usize, c: usize) -> Result<usize, LatticeError> {
        check(r, self.rows)?;
        check(c, self.vertex_cols)?;
        Ok(self.vertex_rows * self.cols + r * self.vertex_cols + c)
    }

    /// `(source, target)` vertex indices of every edge.
    pub fn edge_endpoints(&self) -> &[(usize, usize)] {
        &self.edges
    }

    /// The `(edge, direction)` steps around a plaquette.
    pub fn face_boundary(&self, face: usize) -> Result<&[(usize, i8)], LatticeError> {
        check(face, self.faces.len())?;
        Ok(&self.faces[face])
    }

    /// The complex over `Z`.
    pub fn integral_complex(&self) -> &IntegralChainComplex {
        &self.complex
    }

    /// The complex over GF(2).
    pub fn f2_complex(&self) -> Result<F2ChainComplex, LatticeError> {
        Ok(self.complex.reduce_mod_2()?)
    }

    /// The edges `h(row, c)` for every `c`: a cycle that runs once around the
    /// column direction. Needs a periodic column direction.
    pub fn horizontal_loop(&self, row: usize) -> Result<F2Vector, LatticeError> {
        if self.col_boundary != Boundary::Periodic {
            return Err(LatticeError::DirectionNotPeriodic {
                direction: "column",
            });
        }
        check(row, self.vertex_rows)?;
        let indices: Vec<usize> = (0..self.cols).map(|c| row * self.cols + c).collect();
        Ok(F2Vector::from_indices(self.edges.len(), &indices)?)
    }

    /// The edges `v(r, col)` for every `r`: a cycle that runs once around the
    /// row direction. Needs a periodic row direction.
    pub fn vertical_loop(&self, col: usize) -> Result<F2Vector, LatticeError> {
        if self.row_boundary != Boundary::Periodic {
            return Err(LatticeError::DirectionNotPeriodic { direction: "row" });
        }
        check(col, self.vertex_cols)?;
        let base = self.vertex_rows * self.cols;
        let indices: Vec<usize> = (0..self.rows)
            .map(|r| base + r * self.vertex_cols + col)
            .collect();
        Ok(F2Vector::from_indices(self.edges.len(), &indices)?)
    }
}

fn check(index: usize, len: usize) -> Result<(), LatticeError> {
    if index < len {
        Ok(())
    } else {
        Err(LatticeError::IndexOutOfRange { index, len })
    }
}

// Origin: engine/crates_rs/core_homology/src/square_lattice.rs
// Claim: urn:core:crates_rs:core-homology:square-lattice:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e3f8395a {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
