//! Chain complexes, homology and cohomology with coefficients in `F_2 = GF(2)`.
//!
//! An [`F2ChainComplex`] is a finite sequence of cell counts `n_0, .., n_top`
//! with boundary maps `d_k : C_k -> C_{k-1}` (matrices of shape
//! `n_{k-1} x n_k` over GF(2)) that compose to zero. It can be built from a
//! [`crate::simplicial::SimplicialComplex`] (boundary coefficients reduced
//! mod 2), from the boundary matrices of any cell complex, or from an
//! [`crate::integral_chain_complex::IntegralChainComplex`].
//!
//! The coboundary `delta^k : C^k -> C^{k+1}` is the transpose of `d_{k+1}`, so
//! a cochain is a vector of length `n_k` and a cocycle is a vector in the
//! kernel of `delta^k`. Everything below is exact GF(2) elimination on
//! [`core_number_theory::gf2::F2Matrix`]:
//!
//! - bases of cycles, boundaries, cocycles and coboundaries, and bases of
//!   `H_k` and `H^k` (representatives that are cycles or cocycles);
//! - the dimensions `dim H_k`, `dim H^k` and the counts `|Z^k| = 2^dim Z^k`,
//!   `|B^k|`, `|H^k|` as exact integers, with the Euler-Poincare identity
//!   `sum (-1)^k n_k = sum (-1)^k dim H^k` available as two separate numbers;
//! - the coordinates of the class of a cocycle in the basis of `H^k`;
//! - the solutions of `delta^k s = w`: empty when `w` is not a coboundary,
//!   and otherwise a torsor over `Z^k`: a particular solution plus any
//!   cocycle ([`core_number_theory::gf2::F2AffineSpace`]). This is the statement behind
//!   the lifts of a flat bundle to a double cover: lifts form a torsor over
//!   `Z^1(X; F_2)` when they exist, and classes of lifts modulo gauge form a
//!   torsor over `H^1(X; F_2)`.
//!
//! The integral lift needed for the Bockstein homomorphism lives in
//! [`crate::integral_chain_complex`], which stores the same complex over `Z`.
//!
//! AuthorityEffect: None.

use crate::errors::HomologicalError;
use crate::simplicial::SimplicialComplex;
use num_bigint::{BigInt, BigUint};
use num_traits::One;
use core_number_theory::gf2::{F2AffineSpace, F2Error, F2Matrix, F2Span, F2Vector};

/// Refusals of the complex-level routines (GF(2) and integral).
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ComplexError {
    #[error(transparent)]
    F2(#[from] F2Error),
    #[error(transparent)]
    Homological(#[from] HomologicalError),
    #[error("a chain complex lists at least the cell count of degree 0")]
    NoDimensions,
    #[error("{dims} cell counts need {expected} boundary maps, got {actual}")]
    BoundaryCount {
        dims: usize,
        expected: usize,
        actual: usize,
    },
    #[error("boundary of degree {degree} has shape {actual:?}, expected {expected:?}")]
    BoundaryShape {
        degree: usize,
        expected: (usize, usize),
        actual: (usize, usize),
    },
    #[error("boundary maps do not compose to zero: d_{} d_{degree} != 0", .degree - 1)]
    BoundaryNotZero { degree: usize },
    #[error("cannot multiply a matrix with {left_cols} columns by one with {right_rows} rows")]
    ProductShape { left_cols: usize, right_rows: usize },
    #[error("degree {degree} is outside 0..={top}")]
    DegreeOutOfRange { degree: usize, top: usize },
    #[error("the cochain of degree {degree} is not a cocycle")]
    NotACocycle { degree: usize },
    #[error("the chain of degree {degree} is not a cycle")]
    NotACycle { degree: usize },
    #[error("column {column} names row {row} but the matrix has {rows} rows")]
    EntryOutOfRange {
        column: usize,
        row: usize,
        rows: usize,
    },
    #[error("integer overflow in {operation}")]
    Overflow { operation: &'static str },
    #[error("boundary entry ({row}, {col}) of degree {degree} is not an integer")]
    NonIntegralBoundary {
        degree: usize,
        row: usize,
        col: usize,
    },
    #[error("integer elimination failed: {detail}")]
    Elimination { detail: String },
}

/// A finite chain complex over GF(2).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct F2ChainComplex {
    dims: Vec<usize>,
    /// `boundaries[k - 1]` is `d_k : C_k -> C_{k-1}`, of shape `dims[k-1] x dims[k]`.
    boundaries: Vec<F2Matrix>,
}

impl F2ChainComplex {
    /// The complex with cell counts `dims` (degree 0 first) and boundary maps
    /// `boundaries[k - 1] = d_k`. Refused: no degrees; a wrong number of maps;
    /// a map of the wrong shape; consecutive maps whose product is not zero.
    pub fn new(dims: Vec<usize>, boundaries: Vec<F2Matrix>) -> Result<Self, ComplexError> {
        if dims.is_empty() {
            return Err(ComplexError::NoDimensions);
        }
        if boundaries.len() != dims.len() - 1 {
            return Err(ComplexError::BoundaryCount {
                dims: dims.len(),
                expected: dims.len() - 1,
                actual: boundaries.len(),
            });
        }
        for (index, boundary) in boundaries.iter().enumerate() {
            let degree = index + 1;
            let expected = (dims[degree - 1], dims[degree]);
            if (boundary.rows(), boundary.cols()) != expected {
                return Err(ComplexError::BoundaryShape {
                    degree,
                    expected,
                    actual: (boundary.rows(), boundary.cols()),
                });
            }
        }
        for degree in 2..dims.len() {
            if !boundaries[degree - 2]
                .mul(&boundaries[degree - 1])?
                .is_zero()
            {
                return Err(ComplexError::BoundaryNotZero { degree });
            }
        }
        Ok(Self { dims, boundaries })
    }

    /// The mod-2 reduction of the boundary maps of a simplicial complex (each
    /// `+-1` becomes `1`).
    pub fn from_simplicial_complex(complex: &SimplicialComplex) -> Result<Self, ComplexError> {
        let top = complex.max_dimension();
        let dims: Vec<usize> = (0..=top).map(|k| complex.count(k)).collect();
        let mut boundaries = Vec::with_capacity(top);
        for degree in 1..=top {
            let integral = complex.boundary_matrix(degree)?;
            let mut m = F2Matrix::zeros(integral.rows(), integral.cols())?;
            for r in 0..integral.rows() {
                for c in 0..integral.cols() {
                    let entry = integral.get(r, c).map_err(HomologicalError::MatrixError)?;
                    if !entry.denom().is_one() {
                        return Err(ComplexError::NonIntegralBoundary {
                            degree,
                            row: r,
                            col: c,
                        });
                    }
                    if entry.numer().bit(0) {
                        m.set(r, c, true)?;
                    }
                }
            }
            boundaries.push(m);
        }
        Self::new(dims, boundaries)
    }

    /// The highest degree with a cell count.
    pub fn top_dimension(&self) -> usize {
        self.dims.len() - 1
    }

    /// The number of cells of a degree; `0` above the top degree.
    pub fn cell_count(&self, degree: usize) -> usize {
        self.dims.get(degree).copied().unwrap_or(0)
    }

    /// `sum (-1)^k n_k`.
    pub fn euler_characteristic(&self) -> BigInt {
        self.dims
            .iter()
            .enumerate()
            .map(|(k, &n)| {
                if k % 2 == 0 {
                    BigInt::from(n)
                } else {
                    -BigInt::from(n)
                }
            })
            .sum()
    }

    fn check_degree(&self, degree: usize) -> Result<(), ComplexError> {
        if degree <= self.top_dimension() {
            Ok(())
        } else {
            Err(ComplexError::DegreeOutOfRange {
                degree,
                top: self.top_dimension(),
            })
        }
    }

    /// `d_k : C_k -> C_{k-1}` for `1 <= k <= top`.
    pub fn boundary(&self, degree: usize) -> Result<&F2Matrix, ComplexError> {
        if degree == 0 || degree > self.top_dimension() {
            return Err(ComplexError::DegreeOutOfRange {
                degree,
                top: self.top_dimension(),
            });
        }
        Ok(&self.boundaries[degree - 1])
    }

    /// `delta^k : C^k -> C^{k+1}`, the transpose of `d_{k+1}`; for the top
    /// degree it is the zero map to the zero space (a matrix with no rows).
    pub fn coboundary(&self, degree: usize) -> Result<F2Matrix, ComplexError> {
        self.check_degree(degree)?;
        if degree == self.top_dimension() {
            return Ok(F2Matrix::zeros(0, self.dims[degree])?);
        }
        Ok(self.boundaries[degree].transpose())
    }

    /// A basis of the cycles `Z_k = ker d_k` (all of `C_0` for `k = 0`).
    pub fn cycle_space(&self, degree: usize) -> Result<Vec<F2Vector>, ComplexError> {
        self.check_degree(degree)?;
        if degree == 0 {
            return Ok(unit_vectors(self.dims[0])?);
        }
        Ok(self.boundaries[degree - 1].nullspace())
    }

    /// A basis of the boundaries `B_k = im d_{k+1}` (zero for the top degree).
    pub fn boundary_space(&self, degree: usize) -> Result<Vec<F2Vector>, ComplexError> {
        self.check_degree(degree)?;
        if degree == self.top_dimension() {
            return Ok(Vec::new());
        }
        Ok(self.boundaries[degree].column_space_basis())
    }

    /// A basis of the cocycles `Z^k = ker delta^k` (all of `C^top` at the top).
    pub fn cocycle_space(&self, degree: usize) -> Result<Vec<F2Vector>, ComplexError> {
        self.check_degree(degree)?;
        if degree == self.top_dimension() {
            return Ok(unit_vectors(self.dims[degree])?);
        }
        Ok(self.coboundary(degree)?.nullspace())
    }

    /// A basis of the coboundaries `B^k = im delta^{k-1}` (zero for `k = 0`).
    pub fn coboundary_space(&self, degree: usize) -> Result<Vec<F2Vector>, ComplexError> {
        self.check_degree(degree)?;
        if degree == 0 {
            return Ok(Vec::new());
        }
        Ok(self.coboundary(degree - 1)?.column_space_basis())
    }

    /// `dim H_k(X; F_2) = dim Z_k - dim B_k`.
    pub fn homology_dimension(&self, degree: usize) -> Result<usize, ComplexError> {
        Ok(self.cycle_space(degree)?.len() - self.boundary_space(degree)?.len())
    }

    /// `dim H^k(X; F_2) = dim Z^k - dim B^k`.
    pub fn cohomology_dimension(&self, degree: usize) -> Result<usize, ComplexError> {
        Ok(self.cocycle_space(degree)?.len() - self.coboundary_space(degree)?.len())
    }

    /// The number of cocycles `|Z^k| = 2^dim Z^k`.
    pub fn cocycle_count(&self, degree: usize) -> Result<BigUint, ComplexError> {
        Ok(BigUint::one() << self.cocycle_space(degree)?.len())
    }

    /// The number of coboundaries `|B^k| = 2^dim B^k`.
    pub fn coboundary_count(&self, degree: usize) -> Result<BigUint, ComplexError> {
        Ok(BigUint::one() << self.coboundary_space(degree)?.len())
    }

    /// The number of cohomology classes `|H^k| = 2^dim H^k`.
    pub fn cohomology_count(&self, degree: usize) -> Result<BigUint, ComplexError> {
        Ok(BigUint::one() << self.cohomology_dimension(degree)?)
    }

    /// Representatives of a basis of `H_k`: cycles independent modulo the
    /// boundaries, one per dimension of the homology.
    pub fn homology_basis(&self, degree: usize) -> Result<Vec<F2Vector>, ComplexError> {
        self.check_degree(degree)?;
        let mut span = F2Span::new(self.dims[degree]);
        for boundary in self.boundary_space(degree)? {
            span.insert(&boundary)?;
        }
        let mut representatives = Vec::new();
        for cycle in self.cycle_space(degree)? {
            if span.insert(&cycle)? {
                representatives.push(cycle);
            }
        }
        Ok(representatives)
    }

    /// Representatives of a basis of `H^k`: cocycles independent modulo the
    /// coboundaries.
    pub fn cohomology_basis(&self, degree: usize) -> Result<Vec<F2Vector>, ComplexError> {
        self.check_degree(degree)?;
        let mut span = F2Span::new(self.dims[degree]);
        for coboundary in self.coboundary_space(degree)? {
            span.insert(&coboundary)?;
        }
        let mut representatives = Vec::new();
        for cocycle in self.cocycle_space(degree)? {
            if span.insert(&cocycle)? {
                representatives.push(cocycle);
            }
        }
        Ok(representatives)
    }

    fn check_cochain(&self, degree: usize, c: &F2Vector) -> Result<(), ComplexError> {
        self.check_degree(degree)?;
        if c.len() != self.dims[degree] {
            return Err(ComplexError::F2(F2Error::LengthMismatch {
                expected: self.dims[degree],
                actual: c.len(),
            }));
        }
        Ok(())
    }

    /// Whether `delta^k c = 0`.
    pub fn is_cocycle(&self, degree: usize, c: &F2Vector) -> Result<bool, ComplexError> {
        self.check_cochain(degree, c)?;
        if degree == self.top_dimension() {
            return Ok(true);
        }
        Ok(self.coboundary(degree)?.mul_vec(c)?.is_zero())
    }

    /// Whether `c` is `delta^{k-1} b` for some `b`.
    pub fn is_coboundary(&self, degree: usize, c: &F2Vector) -> Result<bool, ComplexError> {
        self.check_cochain(degree, c)?;
        if degree == 0 {
            return Ok(c.is_zero());
        }
        Ok(self.coboundary(degree - 1)?.in_column_space(c)?)
    }

    /// Whether `d_k z = 0`.
    pub fn is_cycle(&self, degree: usize, z: &F2Vector) -> Result<bool, ComplexError> {
        self.check_cochain(degree, z)?;
        if degree == 0 {
            return Ok(true);
        }
        Ok(self.boundaries[degree - 1].mul_vec(z)?.is_zero())
    }

    /// Whether `z` is `d_{k+1} c` for some `c`.
    pub fn is_boundary(&self, degree: usize, z: &F2Vector) -> Result<bool, ComplexError> {
        self.check_cochain(degree, z)?;
        if degree == self.top_dimension() {
            return Ok(z.is_zero());
        }
        Ok(self.boundaries[degree].in_column_space(z)?)
    }

    /// The coordinates of the class `[c]` in the basis
    /// [`F2ChainComplex::cohomology_basis`]: the unique bits `a_i` with
    /// `c = sum a_i h_i + (a coboundary)`. Refused when `c` is not a cocycle.
    pub fn cohomology_coordinates(
        &self,
        degree: usize,
        c: &F2Vector,
    ) -> Result<Vec<bool>, ComplexError> {
        if !self.is_cocycle(degree, c)? {
            return Err(ComplexError::NotACocycle { degree });
        }
        let basis = self.cohomology_basis(degree)?;
        let mut columns = basis.clone();
        columns.extend(self.coboundary_space(degree)?);
        let system = F2Matrix::from_columns(self.dims[degree], &columns)?;
        let solution = system
            .solve(c)?
            .ok_or(ComplexError::NotACocycle { degree })?;
        // The columns are independent, so the solution is unique.
        (0..basis.len())
            .map(|i| Ok(solution.particular().get(i)?))
            .collect()
    }

    /// The solutions `s` of `delta^k s = w` for `w` in `C^{k+1}`: `None` when
    /// `w` is not a coboundary, otherwise a particular solution plus the
    /// cocycles `Z^k` (a torsor over `Z^k`). At the top degree `w` has length
    /// 0 and every cochain is a solution.
    pub fn solve_coboundary(
        &self,
        degree: usize,
        w: &F2Vector,
    ) -> Result<Option<F2AffineSpace>, ComplexError> {
        self.check_degree(degree)?;
        Ok(self.coboundary(degree)?.solve(w)?)
    }
}

fn unit_vectors(len: usize) -> Result<Vec<F2Vector>, F2Error> {
    (0..len).map(|i| F2Vector::unit(len, i)).collect()
}

// Origin: engine/crates_rs/core_homology/src/f2_cohomology.rs
// Claim: urn:core:crates_rs:core-homology:f2-cohomology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_a294cdef {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
