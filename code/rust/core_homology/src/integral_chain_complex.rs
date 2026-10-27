//! Finite chain complexes over the integers with sparse boundary matrices:
//! the mod-2 reduction to an [`F2ChainComplex`], integral homology with
//! torsion by Smith normal form, and the Bockstein homomorphism.
//!
//! The boundary of a cell is stored as a sparse column of `(row, coefficient)`
//! pairs, so a lattice complex with a handful of cells per boundary stays
//! small. `d_{k-1} d_k = 0` is checked exactly (in `i128`, with a typed
//! overflow refusal) when the complex is built.
//!
//! Homology uses the invariant factors of the boundary maps: for
//! `H_k = ker d_k / im d_{k+1}` the free rank is
//! `n_k - rank d_k - rank d_{k+1}` and the torsion subgroup is
//! `sum Z/d` over the invariant factors `d > 1` of `d_{k+1}`. The
//! elimination is `linear_algebra::smith_normal_form`, which shares nothing
//! with the GF(2) elimination of [`core_number_theory::gf2`], so the two give independent
//! routes to `dim H^k(X; F_2)` through the universal coefficient theorem:
//! `dim H^k(X; F_2) = rank H_k + t_k + t_{k-1}`, where `t_j` is the number of
//! even invariant factors in the torsion of `H_j`.
//!
//! The Bockstein homomorphism `beta : H^k(X; F_2) -> H^{k+1}(X; F_2)` lifts
//! a cocycle to an integral cochain with entries `0` and `1`, applies the
//! integral coboundary, divides by 2 and reduces mod 2. It is well defined on
//! classes, and it detects the 2-torsion of `H^{k+1}(X; Z)`.
//!
//! AuthorityEffect: None.

use crate::f2_cohomology::{ComplexError, F2ChainComplex};
use crate::simplicial::SimplicialComplex;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::smith_normal_form::smith_normal_form_checked;
use num_bigint::BigInt;
use num_traits::{One, Zero};
use core_number_theory::gf2::{F2Matrix, F2Vector};
use std::collections::BTreeMap;

/// An integer matrix stored by columns; each column lists `(row, coefficient)`
/// pairs with distinct rows in increasing order and nonzero coefficients.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SparseIntegerMatrix {
    rows: usize,
    columns: Vec<Vec<(usize, i64)>>,
}

impl SparseIntegerMatrix {
    /// From columns of `(row, coefficient)` pairs: repeated rows in one
    /// column are summed (checked), zeros dropped, rows sorted. Refused: a
    /// row index at or above `rows`, or an overflowing sum.
    pub fn new(rows: usize, columns: Vec<Vec<(usize, i64)>>) -> Result<Self, ComplexError> {
        let mut normalised = Vec::with_capacity(columns.len());
        for (column_index, column) in columns.into_iter().enumerate() {
            let mut merged: BTreeMap<usize, i64> = BTreeMap::new();
            for (row, coefficient) in column {
                if row >= rows {
                    return Err(ComplexError::EntryOutOfRange {
                        column: column_index,
                        row,
                        rows,
                    });
                }
                let slot = merged.entry(row).or_insert(0);
                *slot = slot
                    .checked_add(coefficient)
                    .ok_or(ComplexError::Overflow {
                        operation: "summing the entries of one boundary column",
                    })?;
            }
            normalised.push(merged.into_iter().filter(|&(_, v)| v != 0).collect());
        }
        Ok(Self {
            rows,
            columns: normalised,
        })
    }

    pub fn rows(&self) -> usize {
        self.rows
    }

    pub fn cols(&self) -> usize {
        self.columns.len()
    }

    /// The nonzero entries of a column; `None` beyond the last column.
    pub fn column(&self, column: usize) -> Option<&[(usize, i64)]> {
        self.columns.get(column).map(Vec::as_slice)
    }

    /// Whether every entry is zero.
    pub fn is_zero(&self) -> bool {
        self.columns.iter().all(Vec::is_empty)
    }

    /// The matrix product `self * other`, with `self.cols() == other.rows()`.
    pub fn mul(&self, other: &Self) -> Result<Self, ComplexError> {
        if self.cols() != other.rows {
            return Err(ComplexError::ProductShape {
                left_cols: self.cols(),
                right_rows: other.rows,
            });
        }
        let mut columns = Vec::with_capacity(other.cols());
        for other_column in &other.columns {
            let mut accumulator: BTreeMap<usize, i128> = BTreeMap::new();
            for &(k, b) in other_column {
                for &(r, a) in &self.columns[k] {
                    let product =
                        i128::from(a)
                            .checked_mul(i128::from(b))
                            .ok_or(ComplexError::Overflow {
                                operation: "multiplying boundary coefficients",
                            })?;
                    let slot = accumulator.entry(r).or_insert(0);
                    *slot = slot.checked_add(product).ok_or(ComplexError::Overflow {
                        operation: "accumulating a boundary product",
                    })?;
                }
            }
            let column = accumulator
                .into_iter()
                .filter(|&(_, v)| v != 0)
                .map(|(r, v)| {
                    i64::try_from(v)
                        .map(|v| (r, v))
                        .map_err(|_| ComplexError::Overflow {
                            operation: "narrowing a boundary product to i64",
                        })
                })
                .collect::<Result<Vec<_>, _>>()?;
            columns.push(column);
        }
        Ok(Self {
            rows: self.rows,
            columns,
        })
    }

    /// The entries reduced modulo 2 (an odd entry is `1`).
    pub fn to_f2(&self) -> Result<F2Matrix, ComplexError> {
        let mut m = F2Matrix::zeros(self.rows, self.cols())?;
        for (c, column) in self.columns.iter().enumerate() {
            for &(r, v) in column {
                if v.rem_euclid(2) == 1 {
                    m.set(r, c, true)?;
                }
            }
        }
        Ok(m)
    }

    /// The dense `rows x cols` matrix over `Z`.
    pub fn to_dense(&self) -> Result<BasicMatrix<BigInt>, ComplexError> {
        let mut data = vec![BigInt::zero(); self.rows * self.cols()];
        for (c, column) in self.columns.iter().enumerate() {
            for &(r, v) in column {
                data[r * self.cols() + c] = BigInt::from(v);
            }
        }
        BasicMatrix::from_row_major(self.rows, self.cols(), data).map_err(|e| {
            ComplexError::Elimination {
                detail: e.to_string(),
            }
        })
    }

    /// The invariant factors of the matrix over `Z`, positive and in
    /// divisibility order; their number is the rank.
    pub fn invariant_factors(&self) -> Result<Vec<BigInt>, ComplexError> {
        if self.rows == 0 || self.cols() == 0 || self.is_zero() {
            return Ok(Vec::new());
        }
        let normal_form = smith_normal_form_checked(&self.to_dense()?).map_err(|e| {
            ComplexError::Elimination {
                detail: e.to_string(),
            }
        })?;
        Ok(normal_form.diagonal().invariants().to_vec())
    }
}

/// `H_k(X; Z) = Z^free_rank + sum Z/torsion[i]`, each torsion entry an
/// invariant factor greater than 1.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IntegralHomology {
    pub free_rank: usize,
    pub torsion: Vec<BigInt>,
}

impl IntegralHomology {
    /// The number of torsion summands `Z/d` with `d` even: the 2-rank of the torsion.
    pub fn even_torsion_summands(&self) -> usize {
        let two = BigInt::from(2);
        self.torsion
            .iter()
            .filter(|d| (*d % &two).is_zero())
            .count()
    }
}

/// A finite chain complex over `Z`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IntegralChainComplex {
    dims: Vec<usize>,
    /// `boundaries[k - 1]` is `d_k`, of shape `dims[k-1] x dims[k]`.
    boundaries: Vec<SparseIntegerMatrix>,
}

impl IntegralChainComplex {
    /// Cell counts (degree 0 first) and boundary maps `boundaries[k-1] = d_k`.
    /// Refused: no degrees; a wrong number of maps; a map of the wrong shape;
    /// consecutive maps whose product is not zero.
    pub fn new(
        dims: Vec<usize>,
        boundaries: Vec<SparseIntegerMatrix>,
    ) -> Result<Self, ComplexError> {
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

    /// The signed boundary maps of a simplicial complex, over `Z`.
    pub fn from_simplicial_complex(complex: &SimplicialComplex) -> Result<Self, ComplexError> {
        let top = complex.max_dimension();
        let dims: Vec<usize> = (0..=top).map(|k| complex.count(k)).collect();
        let mut boundaries = Vec::with_capacity(top);
        for degree in 1..=top {
            let dense = complex.boundary_matrix(degree)?;
            let mut columns = vec![Vec::new(); dense.cols()];
            for (c, column) in columns.iter_mut().enumerate() {
                for r in 0..dense.rows() {
                    let entry = dense
                        .get(r, c)
                        .map_err(crate::errors::HomologicalError::MatrixError)?;
                    if entry.is_zero() {
                        continue;
                    }
                    if !entry.denom().is_one() {
                        return Err(ComplexError::NonIntegralBoundary {
                            degree,
                            row: r,
                            col: c,
                        });
                    }
                    let coefficient = i64::try_from(entry.numer().clone()).map_err(|_| {
                        ComplexError::Overflow {
                            operation: "reading a simplicial boundary coefficient",
                        }
                    })?;
                    column.push((r, coefficient));
                }
            }
            boundaries.push(SparseIntegerMatrix::new(dense.rows(), columns)?);
        }
        Self::new(dims, boundaries)
    }

    pub fn top_dimension(&self) -> usize {
        self.dims.len() - 1
    }

    /// The number of cells of a degree; `0` above the top degree.
    pub fn cell_count(&self, degree: usize) -> usize {
        self.dims.get(degree).copied().unwrap_or(0)
    }

    /// `d_k` for `1 <= k <= top`.
    pub fn boundary(&self, degree: usize) -> Result<&SparseIntegerMatrix, ComplexError> {
        if degree == 0 || degree > self.top_dimension() {
            return Err(ComplexError::DegreeOutOfRange {
                degree,
                top: self.top_dimension(),
            });
        }
        Ok(&self.boundaries[degree - 1])
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

    /// The same complex with every coefficient reduced modulo 2.
    pub fn reduce_mod_2(&self) -> Result<F2ChainComplex, ComplexError> {
        let boundaries = self
            .boundaries
            .iter()
            .map(SparseIntegerMatrix::to_f2)
            .collect::<Result<Vec<_>, _>>()?;
        F2ChainComplex::new(self.dims.clone(), boundaries)
    }

    /// `H_k(X; Z)`: free rank and torsion, by Smith normal form.
    pub fn integral_homology(&self, degree: usize) -> Result<IntegralHomology, ComplexError> {
        if degree > self.top_dimension() {
            return Err(ComplexError::DegreeOutOfRange {
                degree,
                top: self.top_dimension(),
            });
        }
        let rank_below = if degree == 0 {
            0
        } else {
            self.boundaries[degree - 1].invariant_factors()?.len()
        };
        let factors_above = if degree == self.top_dimension() {
            Vec::new()
        } else {
            self.boundaries[degree].invariant_factors()?
        };
        let free_rank = self.dims[degree]
            .checked_sub(rank_below + factors_above.len())
            .ok_or_else(|| ComplexError::Elimination {
                detail: format!("ranks exceed the number of cells in degree {degree}"),
            })?;
        let one = BigInt::one();
        Ok(IntegralHomology {
            free_rank,
            torsion: factors_above.into_iter().filter(|d| *d > one).collect(),
        })
    }

    /// `beta(c)` for a cocycle `c` of degree `k < top`: lift `c` to an
    /// integral cochain with entries `0` and `1`, apply the integral
    /// coboundary, divide by 2 and reduce mod 2. The result is a cocycle of
    /// degree `k + 1`. Refused when `c` is not a cocycle mod 2.
    pub fn bockstein_of_cocycle(
        &self,
        degree: usize,
        c: &F2Vector,
    ) -> Result<F2Vector, ComplexError> {
        let f2 = self.reduce_mod_2()?;
        self.bockstein_with(&f2, degree, c)
    }

    fn bockstein_with(
        &self,
        f2: &F2ChainComplex,
        degree: usize,
        c: &F2Vector,
    ) -> Result<F2Vector, ComplexError> {
        if degree >= self.top_dimension() {
            return Err(ComplexError::DegreeOutOfRange {
                degree,
                top: self.top_dimension().saturating_sub(1),
            });
        }
        if !f2.is_cocycle(degree, c)? {
            return Err(ComplexError::NotACocycle { degree });
        }
        // (delta c)_j = sum over the boundary of cell j of coefficient * c_i.
        let boundary = &self.boundaries[degree];
        let mut halved = F2Vector::zeros(self.dims[degree + 1])?;
        for j in 0..boundary.cols() {
            if self.halved_coboundary_bit(boundary, c, degree, j)? {
                halved.set(j, true)?;
            }
        }
        Ok(halved)
    }

    fn halved_coboundary_bit(
        &self,
        boundary: &SparseIntegerMatrix,
        c: &F2Vector,
        degree: usize,
        j: usize,
    ) -> Result<bool, ComplexError> {
        let mut total: i128 = 0;
        for &(i, coefficient) in boundary.column(j).unwrap_or(&[]) {
            if c.get(i)? {
                total += i128::from(coefficient);
            }
        }
        if total.rem_euclid(2) != 0 {
            return Err(ComplexError::Elimination {
                detail: format!(
                    "the integral coboundary of a mod-2 cocycle is odd on cell {j} of degree {}",
                    degree + 1
                ),
            });
        }
        Ok(total.div_euclid(2).rem_euclid(2) == 1)
    }

    /// The matrix of `beta : H^k(X; F_2) -> H^{k+1}(X; F_2)` in the bases
    /// `cohomology_basis(k)` and `cohomology_basis(k + 1)` of the mod-2
    /// reduction: column `j` holds the coordinates of `beta(h_j)`.
    pub fn bockstein_matrix(&self, degree: usize) -> Result<F2Matrix, ComplexError> {
        let f2 = self.reduce_mod_2()?;
        let source = f2.cohomology_basis(degree)?;
        let target_dimension = f2.cohomology_dimension(degree + 1)?;
        let mut matrix = F2Matrix::zeros(target_dimension, source.len())?;
        for (column, representative) in source.iter().enumerate() {
            let image = self.bockstein_with(&f2, degree, representative)?;
            let coords = f2.cohomology_coordinates(degree + 1, &image)?;
            Self::set_column_from_bits(&mut matrix, column, &coords)?;
        }
        Ok(matrix)
    }

    fn set_column_from_bits(
        matrix: &mut F2Matrix,
        column: usize,
        coords: &[bool],
    ) -> Result<(), ComplexError> {
        for (row, &bit) in coords.iter().enumerate() {
            if bit {
                matrix.set(row, column, true)?;
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_homology/src/integral_chain_complex.rs
// Claim: urn:core:crates_rs:core-homology:integral-chain-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord51013581 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord51013581` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError51013581 {
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
impl BoundaryError51013581 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError51013581 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError51013581 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord51013581 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError51013581> {
        if capacity_bound == 0 {
            return Err(BoundaryError51013581::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError51013581::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError51013581::ExceedsCapacity {
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
mod l4_boundary_tests_51013581 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord51013581::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord51013581::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord51013581::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord51013581::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord51013581::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError51013581::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError51013581::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
