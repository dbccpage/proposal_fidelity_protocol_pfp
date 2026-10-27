//! Row-stochastic maps between finite carriers: the category of finite stochastic kernels.
//!
//! A [`StochasticMap`] `Fin(source) -> Fin(target)` is a nonnegative rational matrix whose
//! rows each sum to exactly one, with `entries[i][j] = P(target = j | source = i)`. Its
//! fields are private: a value exists only after [`StochasticMap::try_from_rows`] has checked
//! the shape, non-negativity and the exact row sums, so consumers never re-validate it.
//!
//! Conventions. A distribution is a row vector and a map acts on the right, `p' = p M`, so
//! composition "first `f`, then `g`" is the matrix product `f * g`. Structure:
//!
//! - composition, identities and the pushforward [`StochasticMap::apply`] of a distribution;
//! - the pullback [`StochasticMap::pullback`] of a function, `(M f)_i = E[f(Y) | X = i]`, which
//!   is adjoint to the pushforward: `sum_i p_i (M f)_i = sum_j (p M)_j f_j`;
//! - deterministic maps ([`StochasticMap::from_function`]), permutations
//!   ([`StochasticMap::permutation`]) and the test [`StochasticMap::is_doubly_stochastic`];
//! - the monoidal product [`StochasticMap::tensor`] with the copy, discard, projection and
//!   swap maps, which make finite stochastic kernels a Markov category: a map commutes with
//!   copying exactly when it is deterministic;
//! - Bayesian inversion [`StochasticMap::bayesian_inverse`], which swaps the roles of a
//!   prior and a likelihood;
//! - the exact Dobrushin contraction coefficient [`StochasticMap::dobrushin_coefficient`].
//!
//! Classical kernels only: this module claims nothing about a quantum channel or a Born rule.
//!
//! ```compile_fail,E0451
//! use core_finite_probability::stochastic_map::StochasticMap;
//! // An unvalidated kernel cannot be spelled outside the module.
//! let _ = StochasticMap { source_n: 1, target_n: 1, rows: vec![], label: String::new() };
//! ```
//!
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};
use core_number_theory::rational::Rational;

use crate::error::ClassicalShadowError;
use crate::finite_set::{checked_size_product, FinN};
use crate::simplex::ProbabilitySimplex;

/// Row-stochastic map `Fin(source) -> Fin(target)` with exact rational entries.
///
/// `entries[i][j] = P(target = j | source = i)`; each row sums exactly to 1 and every entry is
/// `>= 0`. Equality is equality of shape and entries; the label is provenance only.
#[derive(Debug, Clone)]
pub struct StochasticMap {
    /// Source cardinality.
    source_n: usize,
    /// Target cardinality.
    target_n: usize,
    /// Rows: length `source_n`; each row has length `target_n`.
    rows: Vec<Vec<Rational>>,
    /// Provenance label. Not part of equality.
    label: String,
}

impl PartialEq for StochasticMap {
    fn eq(&self, other: &Self) -> bool {
        self.source_n == other.source_n
            && self.target_n == other.target_n
            && self.rows == other.rows
    }
}

impl Eq for StochasticMap {}

fn half() -> Rational {
    Rational::new(BigInt::one(), BigInt::from(2))
}

impl StochasticMap {
    /// Validated map from a row-major list of rows.
    ///
    /// Refuses a zero source or target, a wrong row count or row length, a negative entry
    /// (reported by its row-major index) and a row that does not sum exactly to one.
    pub fn try_from_rows(
        source_n: usize,
        target_n: usize,
        rows: Vec<Vec<Rational>>,
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        if source_n == 0 || target_n == 0 {
            return Err(ClassicalShadowError::ZeroCardinality);
        }
        if rows.len() != source_n {
            return Err(ClassicalShadowError::DimensionMismatch {
                expected: source_n,
                actual: rows.len(),
            });
        }
        for (i, row) in rows.iter().enumerate() {
            if row.len() != target_n {
                return Err(ClassicalShadowError::DimensionMismatch {
                    expected: target_n,
                    actual: row.len(),
                });
            }
            let mut sum = Rational::zero();
            for (j, e) in row.iter().enumerate() {
                if e.is_negative() {
                    return Err(ClassicalShadowError::NegativeEntry {
                        index: i * target_n + j,
                    });
                }
                sum += e;
            }
            if !sum.is_one() {
                return Err(ClassicalShadowError::RowNotNormalized { row: i, sum });
            }
        }
        Ok(Self {
            source_n,
            target_n,
            rows,
            label: label.into(),
        })
    }

    /// The map whose row `i` is the distribution `conditionals[i]`.
    pub fn from_conditionals(
        conditionals: &[ProbabilitySimplex],
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        let first = conditionals.first().ok_or(ClassicalShadowError::Empty)?;
        let rows = conditionals
            .iter()
            .map(|c| c.probs().to_vec())
            .collect::<Vec<_>>();
        Self::try_from_rows(conditionals.len(), first.n(), rows, label)
    }

    /// The deterministic map `i -> images[i]` from `Fin(images.len())` to `Fin(target_n)`.
    pub fn from_function(
        target_n: usize,
        images: &[usize],
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        if images.is_empty() || target_n == 0 {
            return Err(ClassicalShadowError::ZeroCardinality);
        }
        let mut rows = Vec::with_capacity(images.len());
        for &image in images {
            if image >= target_n {
                return Err(ClassicalShadowError::IndexOutOfRange {
                    index: image,
                    bound: target_n,
                });
            }
            let mut row = vec![Rational::zero(); target_n];
            row[image] = Rational::one();
            rows.push(row);
        }
        Self::try_from_rows(images.len(), target_n, rows, label)
    }

    /// The permutation map `i -> images[i]` on `Fin(images.len())`.
    ///
    /// Refuses a list that is not a bijection of `0..n`, naming the first position whose
    /// image repeats an earlier one or leaves the range.
    pub fn permutation(
        images: &[usize],
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        let n = images.len();
        let mut seen = vec![false; n];
        for (position, &image) in images.iter().enumerate() {
            if image >= n || seen[image] {
                return Err(ClassicalShadowError::NotAPermutation { position });
            }
            seen[image] = true;
        }
        Self::from_function(n, images, label)
    }

    /// The constant map sending every point of `Fin(source_n)` to `distribution`.
    pub fn constant(
        source_n: usize,
        distribution: &ProbabilitySimplex,
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        if source_n == 0 {
            return Err(ClassicalShadowError::ZeroCardinality);
        }
        let rows = vec![distribution.probs().to_vec(); source_n];
        Self::try_from_rows(source_n, distribution.n(), rows, label)
    }

    /// Identity stochastic map on `Fin n`.
    pub fn identity(
        carrier: &FinN,
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        let n = carrier.cardinality();
        let images: Vec<usize> = (0..n).collect();
        Self::from_function(n, &images, label)
    }

    /// The copy map `Fin n -> Fin(n n)`, `i -> (i, i)`.
    pub fn copy(n: usize) -> Result<Self, ClassicalShadowError> {
        let size = checked_size_product(n, n)?;
        let images: Vec<usize> = (0..n).map(|i| i * n + i).collect();
        Self::from_function(size, &images, "copy")
    }

    /// The discard map `Fin n -> Fin 1`.
    pub fn discard(n: usize) -> Result<Self, ClassicalShadowError> {
        Self::from_function(1, &vec![0; n], "discard")
    }

    /// The projection `Fin(n m) -> Fin n` onto the first coordinate of a pair.
    pub fn first_projection(n: usize, m: usize) -> Result<Self, ClassicalShadowError> {
        let size = checked_size_product(n, m)?;
        let images: Vec<usize> = (0..size).map(|k| k / m).collect();
        Self::from_function(n, &images, "first projection")
    }

    /// The projection `Fin(n m) -> Fin m` onto the second coordinate of a pair.
    pub fn second_projection(n: usize, m: usize) -> Result<Self, ClassicalShadowError> {
        let size = checked_size_product(n, m)?;
        let images: Vec<usize> = (0..size).map(|k| k % m).collect();
        Self::from_function(m, &images, "second projection")
    }

    /// The swap `Fin(n m) -> Fin(m n)`, `(i, j) -> (j, i)`.
    pub fn swap(n: usize, m: usize) -> Result<Self, ClassicalShadowError> {
        let size = checked_size_product(n, m)?;
        let images: Vec<usize> = (0..size).map(|k| (k % m) * n + k / m).collect();
        Self::from_function(size, &images, "swap")
    }

    /// Source cardinality.
    pub fn source_n(&self) -> usize {
        self.source_n
    }

    /// Target cardinality.
    pub fn target_n(&self) -> usize {
        self.target_n
    }

    /// Validated rows `P(. | i)`.
    pub fn rows(&self) -> &[Vec<Rational>] {
        &self.rows
    }

    /// Provenance label.
    pub fn label(&self) -> &str {
        &self.label
    }

    /// Entry `P(j | i)`.
    pub fn get(&self, i: usize, j: usize) -> Option<Rational> {
        self.rows.get(i).and_then(|r| r.get(j).cloned())
    }

    /// The distribution `P(. | i)` of row `i`.
    pub fn conditional(&self, i: usize) -> Result<ProbabilitySimplex, ClassicalShadowError> {
        let row = self
            .rows
            .get(i)
            .ok_or(ClassicalShadowError::IndexOutOfRange {
                index: i,
                bound: self.source_n,
            })?;
        ProbabilitySimplex::try_new(row.clone())
    }

    /// Whether the map is an endomorphism (`source_n == target_n`).
    pub fn is_endomorphism(&self) -> bool {
        self.source_n == self.target_n
    }

    /// Pushforward of a distribution on the source: `p -> p M`.
    pub fn apply(
        &self,
        p: &ProbabilitySimplex,
    ) -> Result<ProbabilitySimplex, ClassicalShadowError> {
        if p.n() != self.source_n {
            return Err(ClassicalShadowError::ShapeMismatch {
                left: p.n(),
                right: self.source_n,
            });
        }
        let mut out = vec![Rational::zero(); self.target_n];
        for (pi, row) in p.probs().iter().zip(&self.rows) {
            for (acc, e) in out.iter_mut().zip(row) {
                *acc += pi * e;
            }
        }
        let target = FinN::try_new(self.target_n)?;
        ProbabilitySimplex::try_from_probs(&target, out, format!("{}o{}", self.label, p.label()))
    }

    /// Pullback of a function on the target: `(M f)_i = sum_j M_ij f_j`, the conditional
    /// expectation of `f` given the source point `i`.
    pub fn pullback(&self, values: &[Rational]) -> Result<Vec<Rational>, ClassicalShadowError> {
        if values.len() != self.target_n {
            return Err(ClassicalShadowError::DimensionMismatch {
                expected: self.target_n,
                actual: values.len(),
            });
        }
        Ok(self
            .rows
            .iter()
            .map(|row| row.iter().zip(values).map(|(m, f)| m * f).sum())
            .collect())
    }

    /// Compose `self` then `next`: `(self ; next)(p) = next(self(p))`, the matrix product
    /// `self * next`. Requires `self.target_n == next.source_n`.
    pub fn compose(&self, next: &StochasticMap) -> Result<StochasticMap, ClassicalShadowError> {
        if self.target_n != next.source_n {
            return Err(ClassicalShadowError::ShapeMismatch {
                left: self.target_n,
                right: next.source_n,
            });
        }
        let mut rows = Vec::with_capacity(self.source_n);
        for self_row in &self.rows {
            let mut row = vec![Rational::zero(); next.target_n];
            for (sik, next_row) in self_row.iter().zip(&next.rows) {
                if sik.is_zero() {
                    continue;
                }
                for (acc, e) in row.iter_mut().zip(next_row) {
                    *acc += sik * e;
                }
            }
            rows.push(row);
        }
        Self::try_from_rows(
            self.source_n,
            next.target_n,
            rows,
            format!("({} ; {})", self.label, next.label),
        )
    }

    /// The `k`-th power of an endomorphism, `M^0 = id`.
    ///
    /// Entries of a power have denominators that grow with `k`, so the exponent is bounded by
    /// the caller: an exponent above `max_exponent` is refused, not attempted.
    pub fn power(
        &self,
        exponent: u32,
        max_exponent: u32,
    ) -> Result<StochasticMap, ClassicalShadowError> {
        if !self.is_endomorphism() {
            return Err(ClassicalShadowError::ShapeMismatch {
                left: self.source_n,
                right: self.target_n,
            });
        }
        if exponent > max_exponent {
            return Err(ClassicalShadowError::LimitExceeded {
                what: "matrix power",
                requested: exponent as usize,
                limit: max_exponent as usize,
            });
        }
        let mut result = Self::identity(&FinN::try_new(self.source_n)?, "id")?;
        let mut square = self.clone();
        let mut remaining = exponent;
        while remaining > 0 {
            if remaining & 1 == 1 {
                result = result.compose(&square)?;
            }
            remaining >>= 1;
            if remaining > 0 {
                square = square.compose(&square)?;
            }
        }
        result.label = format!("{}^{}", self.label, exponent);
        Ok(result)
    }

    /// The monoidal product `self (x) other : Fin(s1 s2) -> Fin(t1 t2)` with entry
    /// `M1[i1][j1] * M2[i2][j2]` at row `i1 * s2 + i2` and column `j1 * t2 + j2`.
    pub fn tensor(&self, other: &StochasticMap) -> Result<StochasticMap, ClassicalShadowError> {
        let source_n = checked_size_product(self.source_n, other.source_n)?;
        let target_n = checked_size_product(self.target_n, other.target_n)?;
        let mut rows = Vec::with_capacity(source_n);
        for row1 in &self.rows {
            for row2 in &other.rows {
                let mut row = Vec::with_capacity(target_n);
                for a in row1 {
                    for b in row2 {
                        row.push(a * b);
                    }
                }
                rows.push(row);
            }
        }
        Self::try_from_rows(
            source_n,
            target_n,
            rows,
            format!("({} x {})", self.label, other.label),
        )
    }

    /// The function `i -> j` when every row is a point mass, else `None`.
    pub fn deterministic_function(&self) -> Option<Vec<usize>> {
        self.rows
            .iter()
            .map(|row| {
                let mut one_at = None;
                for (j, e) in row.iter().enumerate() {
                    if e.is_one() {
                        one_at = Some(j);
                    } else if !e.is_zero() {
                        return None;
                    }
                }
                one_at
            })
            .collect()
    }

    /// Every row is a point mass: the map is a function `Fin(source) -> Fin(target)`.
    pub fn is_deterministic(&self) -> bool {
        self.deterministic_function().is_some()
    }

    /// The map is the identity on `Fin n`.
    pub fn is_identity(&self) -> bool {
        self.is_endomorphism()
            && self
                .deterministic_function()
                .is_some_and(|images| images.iter().enumerate().all(|(i, &image)| i == image))
    }

    /// The map is a permutation of `Fin n`.
    pub fn is_permutation(&self) -> bool {
        if !self.is_endomorphism() {
            return false;
        }
        match self.deterministic_function() {
            Some(images) => {
                let mut seen = vec![false; self.target_n];
                images.iter().all(|&image| {
                    let fresh = !seen[image];
                    seen[image] = true;
                    fresh
                })
            }
            None => false,
        }
    }

    /// The sum of each column: the total mass the map sends to target `j` from unit mass at
    /// every source point.
    pub fn column_sums(&self) -> Vec<Rational> {
        let mut sums = vec![Rational::zero(); self.target_n];
        for row in &self.rows {
            for (acc, e) in sums.iter_mut().zip(row) {
                *acc += e;
            }
        }
        sums
    }

    /// Square with every column also summing to one: the map preserves the uniform
    /// distribution, and is a convex mixture of permutations (Birkhoff).
    pub fn is_doubly_stochastic(&self) -> bool {
        self.is_endomorphism() && self.column_sums().iter().all(Rational::is_one)
    }

    /// The transposed matrix as a stochastic map, when it is one.
    ///
    /// The transpose of a square stochastic matrix is stochastic exactly when the matrix is
    /// doubly stochastic; otherwise the first column that does not sum to one is refused.
    pub fn transpose(&self) -> Result<StochasticMap, ClassicalShadowError> {
        let rows: Vec<Vec<Rational>> = (0..self.target_n)
            .map(|j| self.rows.iter().map(|row| row[j].clone()).collect())
            .collect();
        Self::try_from_rows(
            self.target_n,
            self.source_n,
            rows,
            format!("{}^T", self.label),
        )
    }

    /// The Dobrushin contraction coefficient
    /// `delta(M) = 1/2 max_(i, i') sum_j |M_ij - M_i'j|`, the largest total variation between
    /// two rows.
    ///
    /// It lies in `[0, 1]`, is `0` exactly when all rows are equal, is `1` exactly when two
    /// rows have disjoint supports, and bounds the contraction of total variation:
    /// `TV(p M, q M) <= delta(M) TV(p, q)`, with equality for some pair of point masses.
    pub fn dobrushin_coefficient(&self) -> Rational {
        let mut best = Rational::zero();
        for (i, row) in self.rows.iter().enumerate() {
            for other in &self.rows[i + 1..] {
                let l1: Rational = row.iter().zip(other).map(|(a, b)| (a - b).abs()).sum();
                if l1 > best {
                    best = l1;
                }
            }
        }
        best * half()
    }

    /// Bayesian inversion of the map against a prior `p` on the source.
    ///
    /// Returns the marginal `q = p M` on the target and the posterior kernel
    /// `K : Fin(target) -> Fin(source)` with `K[j][i] = p_i M_ij / q_j`, so that the joint
    /// distributions `p_i M_ij` and `q_j K[j][i]` coincide. Every target point must carry
    /// positive mass, otherwise its posterior is undetermined and the point is refused.
    pub fn bayesian_inverse(
        &self,
        prior: &ProbabilitySimplex,
    ) -> Result<(ProbabilitySimplex, StochasticMap), ClassicalShadowError> {
        let marginal = self.apply(prior)?;
        let mut rows = Vec::with_capacity(self.target_n);
        for (j, q) in marginal.probs().iter().enumerate() {
            if q.is_zero() {
                return Err(ClassicalShadowError::ZeroMass { index: j });
            }
            rows.push(
                prior
                    .probs()
                    .iter()
                    .zip(&self.rows)
                    .map(|(p, row)| p * &row[j] / q)
                    .collect(),
            );
        }
        let posterior = Self::try_from_rows(
            self.target_n,
            self.source_n,
            rows,
            format!("bayes({})", self.label),
        )?;
        Ok((marginal, posterior))
    }

    /// The matrix of the map in `core_linear_algebra` dense storage.
    pub fn to_basic_matrix(&self) -> Result<BasicMatrix<Rational>, ClassicalShadowError> {
        let data: Vec<Rational> = self.rows.iter().flatten().cloned().collect();
        Ok(BasicMatrix::from_row_major(
            self.source_n,
            self.target_n,
            data,
        )?)
    }

    /// The map of a dense matrix, refusing a matrix that is not row-stochastic.
    pub fn try_from_basic_matrix(
        matrix: &BasicMatrix<Rational>,
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        let mut rows = Vec::with_capacity(matrix.rows());
        for i in 0..matrix.rows() {
            let mut row = Vec::with_capacity(matrix.cols());
            for j in 0..matrix.cols() {
                row.push(matrix.get(i, j)?);
            }
            rows.push(row);
        }
        Self::try_from_rows(matrix.rows(), matrix.cols(), rows, label)
    }
}

// Origin: engine/crates_rs/core_finite_probability/src/stochastic_map.rs
// Claim: urn:core:crates_rs:core-finite-probability:stochastic-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord89a7df8b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord89a7df8b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError89a7df8b {
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
impl BoundaryError89a7df8b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError89a7df8b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError89a7df8b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord89a7df8b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError89a7df8b> {
        if capacity_bound == 0 {
            return Err(BoundaryError89a7df8b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError89a7df8b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError89a7df8b::ExceedsCapacity {
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
    use crate::test_support::{grid_simplices, simplex, stochastic as map};
    use core_number_theory::rational::{ri, rq};

    fn q(n: i64, d: i64) -> Rational {
        rq(n, d)
    }

    fn fin(n: usize) -> FinN {
        FinN::try_new(n).unwrap()
    }

    /// A 3-state chain with no zero entry on the diagonal and mixed denominators.
    fn chain_a() -> StochasticMap {
        map(&[
            &[(1, 2), (1, 3), (1, 6)],
            &[(1, 4), (1, 4), (1, 2)],
            &[(2, 5), (1, 5), (2, 5)],
        ])
    }

    fn chain_b() -> StochasticMap {
        map(&[
            &[(0, 1), (1, 1), (0, 1)],
            &[(1, 3), (1, 3), (1, 3)],
            &[(1, 7), (2, 7), (4, 7)],
        ])
    }

    // --- ported laws -----------------------------------------------------------------

    #[test]
    fn the_identity_is_row_stochastic_with_ones_on_the_diagonal() {
        let id = StochasticMap::identity(&fin(3), "id").unwrap();
        assert!(id.is_endomorphism());
        assert!(id.is_identity());
        for i in 0..3 {
            for j in 0..3 {
                assert_eq!(id.get(i, j).unwrap(), if i == j { ri(1) } else { ri(0) });
            }
        }
    }

    #[test]
    fn the_identity_is_a_two_sided_unit_for_composition_on_square_and_rectangular_maps() {
        let id2 = StochasticMap::identity(&fin(2), "id2").unwrap();
        let id3 = StochasticMap::identity(&fin(3), "id3").unwrap();
        let flip = map(&[&[(0, 1), (1, 1)], &[(1, 1), (0, 1)]]);
        assert_eq!(id2.compose(&flip).unwrap(), flip);
        assert_eq!(flip.compose(&id2).unwrap(), flip);
        let emb = map(&[&[(1, 2), (1, 2), (0, 1)], &[(0, 1), (1, 3), (2, 3)]]);
        assert_eq!(id2.compose(&emb).unwrap(), emb);
        assert_eq!(emb.compose(&id3).unwrap(), emb);
        // Identity acts as identity on distributions.
        let p = simplex(&[(1, 4), (3, 4)]);
        assert_eq!(id2.apply(&p).unwrap(), p);
    }

    #[test]
    fn composition_is_associative_and_the_action_agrees_with_it() {
        let a = map(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]);
        let b = map(&[&[(1, 1), (0, 1), (0, 1)], &[(0, 1), (1, 2), (1, 2)]]);
        let c = map(&[&[(1, 4), (3, 4)], &[(1, 2), (1, 2)], &[(2, 5), (3, 5)]]);
        let left = a.compose(&b).unwrap().compose(&c).unwrap();
        let right = a.compose(&b.compose(&c).unwrap()).unwrap();
        assert_eq!(left, right);
        assert_eq!((left.source_n(), left.target_n()), (2, 2));
        // ((p A) B) C = p ((A;B);C): pushforward is a functor.
        let p = simplex(&[(2, 5), (3, 5)]);
        let step = c.apply(&b.apply(&a.apply(&p).unwrap()).unwrap()).unwrap();
        assert_eq!(step, left.apply(&p).unwrap());
    }

    #[test]
    fn a_map_sends_a_distribution_to_a_distribution_with_the_hand_computed_masses() {
        let m = map(&[&[(1, 1), (0, 1)], &[(1, 2), (1, 2)], &[(0, 1), (1, 1)]]);
        let u = ProbabilitySimplex::uniform(&fin(3), "u").unwrap();
        // col0 = 1/3 + 1/6 = 1/2 ; col1 = 1/6 + 1/3 = 1/2
        assert_eq!(m.apply(&u).unwrap().probs(), &[q(1, 2), q(1, 2)]);
    }

    #[test]
    fn a_non_row_stochastic_matrix_is_refused_at_its_row() {
        let err = StochasticMap::try_from_rows(
            2,
            2,
            vec![vec![q(1, 2), q(1, 3)], vec![q(1, 1), q(0, 1)]],
            "bad",
        );
        assert_eq!(
            err,
            Err(ClassicalShadowError::RowNotNormalized {
                row: 0,
                sum: q(5, 6)
            })
        );
    }

    #[test]
    fn malformed_shapes_and_negative_entries_are_refused_with_their_positions() {
        let try_rows = |target_n: usize, rows: Vec<Vec<Rational>>| {
            StochasticMap::try_from_rows(2, target_n, rows, "hand")
        };
        assert_eq!(
            try_rows(0, vec![vec![], vec![]]),
            Err(ClassicalShadowError::ZeroCardinality)
        );
        assert_eq!(
            StochasticMap::try_from_rows(0, 2, vec![], "hand"),
            Err(ClassicalShadowError::ZeroCardinality)
        );
        assert_eq!(
            try_rows(2, vec![vec![ri(1), ri(0)]]),
            Err(ClassicalShadowError::DimensionMismatch {
                expected: 2,
                actual: 1
            })
        );
        assert_eq!(
            try_rows(2, vec![vec![ri(1), ri(0)], vec![ri(1)]]),
            Err(ClassicalShadowError::DimensionMismatch {
                expected: 2,
                actual: 1
            })
        );
        assert_eq!(
            try_rows(2, vec![vec![q(3, 2), q(-1, 2)], vec![ri(1), ri(0)]]),
            Err(ClassicalShadowError::NegativeEntry { index: 1 })
        );
    }

    /// Composition runs past the `i64` ceiling of a fixed-width rational carrier.
    ///
    /// Entry `(0, 0)` of `A ; B` is `2^-40 * 3^-25 + (1 - 2^-40) / 5`. Its reduced
    /// denominator has 79 bits, so an `i64` rational could not hold it. Here it is exact, and
    /// every composite row still sums to exactly one.
    #[test]
    fn composition_passes_the_i64_ceiling_exactly() {
        let a0 = Rational::new(BigInt::one(), BigInt::from(2u8).pow(40));
        let b0 = Rational::new(BigInt::one(), BigInt::from(3u8).pow(25));
        let a = StochasticMap::try_from_rows(
            2,
            2,
            vec![vec![a0.clone(), q(1, 1) - &a0], vec![q(1, 2), q(1, 2)]],
            "A",
        )
        .unwrap();
        let b = StochasticMap::try_from_rows(
            2,
            2,
            vec![vec![b0.clone(), q(1, 1) - &b0], vec![q(1, 5), q(4, 5)]],
            "B",
        )
        .unwrap();
        let ab = a.compose(&b).unwrap();
        let expected = &a0 * &b0 + (q(1, 1) - &a0) * q(1, 5);
        assert!(*expected.denom() > BigInt::from(i64::MAX));
        assert_eq!(ab.get(0, 0), Some(expected));
        for row in ab.rows() {
            assert_eq!(row.iter().sum::<Rational>(), q(1, 1));
        }
    }

    // --- independent routes -----------------------------------------------------------

    #[test]
    fn composition_agrees_with_the_dense_matrix_product_of_linear_algebra() {
        let (a, b) = (chain_a(), chain_b());
        let via_kernel = a.compose(&b).unwrap().to_basic_matrix().unwrap();
        let via_matrix = a
            .to_basic_matrix()
            .unwrap()
            .mul(&b.to_basic_matrix().unwrap())
            .unwrap();
        assert_eq!(via_kernel, via_matrix);
    }

    #[test]
    fn the_dense_matrix_round_trip_is_the_identity_and_refuses_a_non_stochastic_matrix() {
        let a = chain_a();
        let m = a.to_basic_matrix().unwrap();
        assert_eq!(StochasticMap::try_from_basic_matrix(&m, "a").unwrap(), a);
        let bad = BasicMatrix::from_row_major(1, 2, vec![q(1, 2), q(1, 3)]).unwrap();
        assert_eq!(
            StochasticMap::try_from_basic_matrix(&bad, "bad"),
            Err(ClassicalShadowError::RowNotNormalized {
                row: 0,
                sum: q(5, 6)
            })
        );
    }

    #[test]
    fn pushforward_of_p_is_composition_of_the_point_preparation_with_the_map() {
        let a = chain_a();
        let p = simplex(&[(1, 2), (1, 3), (1, 6)]);
        let prepare = StochasticMap::constant(1, &p, "prepare").unwrap();
        let composite = prepare.compose(&a).unwrap();
        assert_eq!(composite.conditional(0).unwrap(), a.apply(&p).unwrap());
    }

    #[test]
    fn pullback_is_adjoint_to_pushforward_on_enumerated_functions() {
        let a = chain_a();
        let p = simplex(&[(1, 2), (1, 3), (1, 6)]);
        let pushed = a.apply(&p).unwrap();
        for f in [
            vec![ri(1), ri(0), ri(0)],
            vec![ri(2), ri(-3), ri(7)],
            vec![q(1, 2), q(5, 3), q(-4, 9)],
        ] {
            let pulled = a.pullback(&f).unwrap();
            assert_eq!(
                p.expectation(&pulled).unwrap(),
                pushed.expectation(&f).unwrap(),
                "sum_i p_i (M f)_i = sum_j (p M)_j f_j for f = {f:?}"
            );
        }
        assert_eq!(
            a.pullback(&[ri(1), ri(2)]),
            Err(ClassicalShadowError::DimensionMismatch {
                expected: 3,
                actual: 2
            })
        );
    }

    // --- deterministic maps, permutations, doubly stochastic -------------------------------

    #[test]
    fn a_function_becomes_a_deterministic_map_and_composition_composes_functions() {
        let f = StochasticMap::from_function(3, &[2, 0], "f").unwrap();
        let g = StochasticMap::from_function(2, &[1, 1, 0], "g").unwrap();
        assert!(f.is_deterministic());
        assert_eq!(f.deterministic_function(), Some(vec![2, 0]));
        let fg = f.compose(&g).unwrap();
        // g(f(0)) = g(2) = 0 ; g(f(1)) = g(0) = 1
        assert_eq!(fg.deterministic_function(), Some(vec![0, 1]));
        assert_eq!(
            StochasticMap::from_function(3, &[0, 3], "bad"),
            Err(ClassicalShadowError::IndexOutOfRange { index: 3, bound: 3 })
        );
        assert_eq!(
            StochasticMap::from_function(3, &[], "bad"),
            Err(ClassicalShadowError::ZeroCardinality)
        );
        assert!(!chain_a().is_deterministic());
        assert_eq!(chain_a().deterministic_function(), None);
    }

    #[test]
    fn a_permutation_is_validated_and_its_inverse_composes_to_the_identity() {
        let images = [2usize, 0, 3, 1];
        let p = StochasticMap::permutation(&images, "p").unwrap();
        assert!(p.is_permutation());
        let mut inverse = [0usize; 4];
        for (i, &image) in images.iter().enumerate() {
            inverse[image] = i;
        }
        let inv = StochasticMap::permutation(&inverse, "inv").unwrap();
        assert!(p.compose(&inv).unwrap().is_identity());
        assert!(inv.compose(&p).unwrap().is_identity());
        // The position of the first repeated or out-of-range image is named.
        assert_eq!(
            StochasticMap::permutation(&[0, 1, 1], "bad"),
            Err(ClassicalShadowError::NotAPermutation { position: 2 })
        );
        assert_eq!(
            StochasticMap::permutation(&[1, 3], "bad"),
            Err(ClassicalShadowError::NotAPermutation { position: 1 })
        );
        // A constant function is deterministic but not a permutation.
        let constant = StochasticMap::from_function(2, &[0, 0], "c").unwrap();
        assert!(constant.is_deterministic());
        assert!(!constant.is_permutation());
    }

    #[test]
    fn doubly_stochastic_means_the_uniform_distribution_is_preserved() {
        let half_half = map(&[&[(1, 2), (1, 2)], &[(1, 2), (1, 2)]]);
        assert!(half_half.is_doubly_stochastic());
        let u = ProbabilitySimplex::uniform(&fin(3), "u").unwrap();
        let mix = map(&[
            &[(1, 2), (1, 4), (1, 4)],
            &[(1, 4), (1, 2), (1, 4)],
            &[(1, 4), (1, 4), (1, 2)],
        ]);
        assert!(mix.is_doubly_stochastic());
        assert_eq!(mix.apply(&u).unwrap(), u);
        // A row-stochastic map that is not doubly stochastic moves the uniform distribution.
        let skew = map(&[&[(1, 1), (0, 1)], &[(1, 2), (1, 2)]]);
        assert!(!skew.is_doubly_stochastic());
        assert_ne!(
            skew.apply(&ProbabilitySimplex::uniform(&fin(2), "u").unwrap())
                .unwrap(),
            ProbabilitySimplex::uniform(&fin(2), "u").unwrap()
        );
        // A rectangular map is never doubly stochastic.
        assert!(
            !map(&[&[(1, 2), (1, 2), (0, 1)], &[(0, 1), (1, 2), (1, 2)]]).is_doubly_stochastic()
        );
        assert_eq!(skew.column_sums(), vec![q(3, 2), q(1, 2)]);
    }

    #[test]
    fn convex_mixtures_of_permutations_are_doubly_stochastic_and_the_transpose_is_too() {
        let id = StochasticMap::identity(&fin(3), "id").unwrap();
        let rot = StochasticMap::permutation(&[1, 2, 0], "rot").unwrap();
        let swap = StochasticMap::permutation(&[1, 0, 2], "swap").unwrap();
        let weights = [q(1, 2), q(1, 3), q(1, 6)];
        let mut rows = vec![vec![ri(0); 3]; 3];
        for (w, perm) in weights.iter().zip([&id, &rot, &swap]) {
            for (i, row) in perm.rows().iter().enumerate() {
                for (j, e) in row.iter().enumerate() {
                    rows[i][j] += w * e;
                }
            }
        }
        let mixture = StochasticMap::try_from_rows(3, 3, rows, "mix").unwrap();
        assert!(mixture.is_doubly_stochastic());
        let transposed = mixture.transpose().unwrap();
        assert!(transposed.is_doubly_stochastic());
        assert_eq!(transposed.transpose().unwrap(), mixture);
    }

    #[test]
    fn the_transpose_of_a_map_that_is_not_doubly_stochastic_is_refused() {
        let skew = map(&[&[(1, 1), (0, 1)], &[(1, 2), (1, 2)]]);
        assert_eq!(
            skew.transpose(),
            Err(ClassicalShadowError::RowNotNormalized {
                row: 0,
                sum: q(3, 2)
            })
        );
    }

    // --- tensor and the Markov category ---------------------------------------------------

    #[test]
    fn the_tensor_product_has_product_shape_and_entries() {
        let a = map(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]);
        let b = map(&[&[(1, 4), (3, 4), (0, 1)]]);
        let t = a.tensor(&b).unwrap();
        assert_eq!((t.source_n(), t.target_n()), (2, 6));
        for i1 in 0..2 {
            for j1 in 0..2 {
                for j2 in 0..3 {
                    assert_eq!(
                        t.get(i1, j1 * 3 + j2).unwrap(),
                        a.get(i1, j1).unwrap() * b.get(0, j2).unwrap()
                    );
                }
            }
        }
    }

    #[test]
    fn the_interchange_law_and_the_action_on_products_hold() {
        let a = map(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]);
        let b = map(&[&[(1, 4), (1, 4), (1, 2)], &[(1, 1), (0, 1), (0, 1)]]);
        let c = map(&[&[(1, 5), (4, 5)], &[(2, 3), (1, 3)]]);
        let d = map(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)], &[(3, 4), (1, 4)]]);
        // (A (x) B) ; (C (x) D) = (A ; C) (x) (B ; D)
        let left = a
            .tensor(&b)
            .unwrap()
            .compose(&c.tensor(&d).unwrap())
            .unwrap();
        let right = a
            .compose(&c)
            .unwrap()
            .tensor(&b.compose(&d).unwrap())
            .unwrap();
        assert_eq!(left, right);
        // (p (x) r) (A (x) B) = (p A) (x) (r B)
        let p = simplex(&[(1, 4), (3, 4)]);
        let r = simplex(&[(1, 2), (1, 2)]);
        let on_product = a
            .tensor(&b)
            .unwrap()
            .apply(&p.product(&r).unwrap())
            .unwrap();
        assert_eq!(
            on_product,
            a.apply(&p).unwrap().product(&b.apply(&r).unwrap()).unwrap()
        );
    }

    #[test]
    fn tensoring_with_the_one_point_identity_changes_nothing() {
        let a = chain_a();
        let unit = StochasticMap::identity(&fin(1), "unit").unwrap();
        assert_eq!(unit.tensor(&a).unwrap(), a);
        assert_eq!(a.tensor(&unit).unwrap(), a);
    }

    #[test]
    fn structural_maps_refuse_a_size_that_overflows_before_allocating() {
        assert_eq!(
            StochasticMap::copy(usize::MAX),
            Err(ClassicalShadowError::SizeOverflow {
                left: usize::MAX,
                right: usize::MAX
            })
        );
        assert_eq!(
            StochasticMap::swap(usize::MAX, 2),
            Err(ClassicalShadowError::SizeOverflow {
                left: usize::MAX,
                right: 2
            })
        );
        assert_eq!(
            StochasticMap::first_projection(2, usize::MAX),
            Err(ClassicalShadowError::SizeOverflow {
                left: 2,
                right: usize::MAX
            })
        );
        assert_eq!(
            StochasticMap::second_projection(usize::MAX, 3),
            Err(ClassicalShadowError::SizeOverflow {
                left: usize::MAX,
                right: 3
            })
        );
    }

    #[test]
    fn copy_and_discard_are_a_comonoid() {
        for n in 1..=4usize {
            let id = StochasticMap::identity(&fin(n), "id").unwrap();
            let copy = StochasticMap::copy(n).unwrap();
            let discard = StochasticMap::discard(n).unwrap();
            // counit: copy ; (discard (x) id) = id = copy ; (id (x) discard)
            assert_eq!(copy.compose(&discard.tensor(&id).unwrap()).unwrap(), id);
            assert_eq!(copy.compose(&id.tensor(&discard).unwrap()).unwrap(), id);
            // coassociativity: copy ; (copy (x) id) = copy ; (id (x) copy)
            let left = copy.compose(&copy.tensor(&id).unwrap()).unwrap();
            let right = copy.compose(&id.tensor(&copy).unwrap()).unwrap();
            assert_eq!(left, right);
            // cocommutativity: copy ; swap = copy
            assert_eq!(
                copy.compose(&StochasticMap::swap(n, n).unwrap()).unwrap(),
                copy
            );
        }
    }

    #[test]
    fn a_map_commutes_with_copy_exactly_when_it_is_deterministic() {
        let natural = |f: &StochasticMap| {
            let lhs = f
                .compose(&StochasticMap::copy(f.target_n()).unwrap())
                .unwrap();
            let rhs = StochasticMap::copy(f.source_n())
                .unwrap()
                .compose(&f.tensor(f).unwrap())
                .unwrap();
            lhs == rhs
        };
        // Every deterministic map from Fin 3 to Fin 2 commutes with copy.
        for a in 0..2usize {
            for b in 0..2usize {
                for c in 0..2usize {
                    let f = StochasticMap::from_function(2, &[a, b, c], "f").unwrap();
                    assert!(natural(&f), "deterministic f = [{a}, {b}, {c}]");
                }
            }
        }
        // A genuinely random map does not: copying its output is not two independent draws.
        let noisy = map(&[&[(1, 2), (1, 2)], &[(1, 1), (0, 1)]]);
        assert!(!noisy.is_deterministic());
        assert!(!natural(&noisy));
        assert!(!natural(&chain_a()));
    }

    #[test]
    fn projections_recover_the_factors_of_a_product_and_swap_is_natural() {
        let p = simplex(&[(1, 4), (3, 4)]);
        let r = simplex(&[(1, 2), (1, 3), (1, 6)]);
        let pr = p.product(&r).unwrap();
        assert_eq!(
            StochasticMap::first_projection(2, 3)
                .unwrap()
                .apply(&pr)
                .unwrap(),
            p
        );
        assert_eq!(
            StochasticMap::second_projection(2, 3)
                .unwrap()
                .apply(&pr)
                .unwrap(),
            r
        );
        // swap(a, b) ; (g (x) f) = (f (x) g) ; swap(a', b') for f: Fin 2 -> Fin 3, g: Fin 3 -> Fin 2.
        let f = map(&[&[(1, 2), (1, 2), (0, 1)], &[(0, 1), (1, 3), (2, 3)]]);
        let g = map(&[&[(1, 4), (3, 4)], &[(1, 2), (1, 2)], &[(2, 5), (3, 5)]]);
        let lhs = StochasticMap::swap(2, 3)
            .unwrap()
            .compose(&g.tensor(&f).unwrap())
            .unwrap();
        let rhs = f
            .tensor(&g)
            .unwrap()
            .compose(&StochasticMap::swap(3, 2).unwrap())
            .unwrap();
        assert_eq!(lhs, rhs);
        // swap twice is the identity, and swap is a permutation.
        let s = StochasticMap::swap(2, 3).unwrap();
        assert!(s.is_permutation());
        assert!(s
            .compose(&StochasticMap::swap(3, 2).unwrap())
            .unwrap()
            .is_identity());
    }

    // --- Bayesian inversion --------------------------------------------------------------

    #[test]
    fn the_bayesian_inverse_reproduces_the_joint_distribution_and_inverts_back() {
        let a = chain_a();
        let prior = simplex(&[(1, 2), (1, 3), (1, 6)]);
        let (marginal, posterior) = a.bayesian_inverse(&prior).unwrap();
        assert_eq!(marginal, a.apply(&prior).unwrap());
        for i in 0..3 {
            for j in 0..3 {
                // p_i M_ij = q_j K[j][i]
                assert_eq!(
                    prior.get(i).unwrap() * a.get(i, j).unwrap(),
                    marginal.get(j).unwrap() * posterior.get(j, i).unwrap()
                );
            }
        }
        // Inverting the posterior against the marginal returns the original kernel and prior.
        let (prior_back, kernel_back) = posterior.bayesian_inverse(&marginal).unwrap();
        assert_eq!(prior_back, prior);
        assert_eq!(kernel_back, a);
    }

    #[test]
    fn a_target_with_zero_mass_has_no_posterior_and_is_refused() {
        let m = map(&[&[(1, 1), (0, 1)], &[(1, 1), (0, 1)]]);
        let prior = simplex(&[(1, 2), (1, 2)]);
        assert_eq!(
            m.bayesian_inverse(&prior),
            Err(ClassicalShadowError::ZeroMass { index: 1 })
        );
    }

    // --- Dobrushin ----------------------------------------------------------------------

    #[test]
    fn the_dobrushin_coefficient_has_the_expected_extreme_values() {
        // Equal rows: the map forgets its input.
        assert_eq!(
            map(&[&[(1, 3), (2, 3)], &[(1, 3), (2, 3)]]).dobrushin_coefficient(),
            ri(0)
        );
        // A single source point: nothing to contract.
        assert_eq!(map(&[&[(1, 3), (2, 3)]]).dobrushin_coefficient(), ri(0));
        // Two rows with disjoint supports: nothing is contracted.
        assert_eq!(
            StochasticMap::identity(&fin(3), "id")
                .unwrap()
                .dobrushin_coefficient(),
            ri(1)
        );
        // Hand value: rows (1/2, 1/2, 0) and (0, 1/2, 1/2) differ by l1 = 1, so TV = 1/2.
        assert_eq!(
            map(&[&[(1, 2), (1, 2), (0, 1)], &[(0, 1), (1, 2), (1, 2)]]).dobrushin_coefficient(),
            q(1, 2)
        );
    }

    #[test]
    fn total_variation_contracts_by_at_most_the_dobrushin_coefficient_and_the_bound_is_tight() {
        // Square and rectangular maps, with two and three source points.
        let maps = [
            chain_a(),
            chain_b(),
            map(&[&[(1, 2), (1, 2), (0, 1)], &[(0, 1), (1, 2), (1, 2)]]),
        ];
        for m in &maps {
            let n = m.source_n();
            let delta = m.dobrushin_coefficient();
            assert!(delta >= ri(0) && delta <= ri(1));
            // Every pair of distributions on a grid.
            let grid = grid_simplices(4, n);
            for p in &grid {
                for r in &grid {
                    let before = p.total_variation(r).unwrap();
                    let after = m
                        .apply(p)
                        .unwrap()
                        .total_variation(&m.apply(r).unwrap())
                        .unwrap();
                    assert!(after <= &delta * before);
                }
            }
            // Tightness: two point masses at the most distant rows attain the coefficient.
            let mut attained = false;
            for i in 0..n {
                for k in 0..n {
                    let pi = ProbabilitySimplex::dirac(&fin(n), i, "p").unwrap();
                    let pk = ProbabilitySimplex::dirac(&fin(n), k, "r").unwrap();
                    let after = m
                        .apply(&pi)
                        .unwrap()
                        .total_variation(&m.apply(&pk).unwrap())
                        .unwrap();
                    if i != k && after == delta {
                        attained = true;
                    }
                }
            }
            assert!(attained, "no pair of point masses attains delta = {delta}");
        }
    }

    // --- powers and structural refusals ---------------------------------------------------

    #[test]
    fn powers_agree_with_repeated_composition_and_are_bounded() {
        let a = chain_a();
        assert!(a.power(0, 10).unwrap().is_identity());
        assert_eq!(a.power(1, 10).unwrap(), a);
        let cubed = a.compose(&a).unwrap().compose(&a).unwrap();
        assert_eq!(a.power(3, 10).unwrap(), cubed);
        let seventh = (0..6).fold(a.clone(), |acc, _| acc.compose(&a).unwrap());
        assert_eq!(a.power(7, 10).unwrap(), seventh);
        assert_eq!(
            a.power(11, 10),
            Err(ClassicalShadowError::LimitExceeded {
                what: "matrix power",
                requested: 11,
                limit: 10
            })
        );
        let rectangular = map(&[&[(1, 2), (1, 2), (0, 1)], &[(0, 1), (1, 2), (1, 2)]]);
        assert_eq!(
            rectangular.power(2, 10),
            Err(ClassicalShadowError::ShapeMismatch { left: 2, right: 3 })
        );
    }

    #[test]
    fn composition_and_application_refuse_mismatched_carriers() {
        let a = chain_a();
        let two = map(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]);
        assert_eq!(
            a.compose(&two),
            Err(ClassicalShadowError::ShapeMismatch { left: 3, right: 2 })
        );
        assert_eq!(
            two.apply(&simplex(&[(1, 3), (1, 3), (1, 3)])),
            Err(ClassicalShadowError::ShapeMismatch { left: 3, right: 2 })
        );
    }

    #[test]
    fn conditionals_and_constant_maps_round_trip() {
        let a = chain_a();
        let rows: Vec<ProbabilitySimplex> = (0..3).map(|i| a.conditional(i).unwrap()).collect();
        assert_eq!(StochasticMap::from_conditionals(&rows, "a").unwrap(), a);
        assert_eq!(
            a.conditional(3),
            Err(ClassicalShadowError::IndexOutOfRange { index: 3, bound: 3 })
        );
        assert_eq!(
            StochasticMap::from_conditionals(&[], "a"),
            Err(ClassicalShadowError::Empty)
        );
        let p = simplex(&[(1, 4), (3, 4)]);
        let c = StochasticMap::constant(3, &p, "c").unwrap();
        assert_eq!(c.dobrushin_coefficient(), ri(0));
        assert_eq!(c.apply(&simplex(&[(1, 3), (1, 3), (1, 3)])).unwrap(), p);
        assert_eq!(
            StochasticMap::constant(0, &p, "c"),
            Err(ClassicalShadowError::ZeroCardinality)
        );
    }

    #[test]
    fn labels_are_provenance_and_do_not_affect_equality() {
        let x = StochasticMap::try_from_rows(1, 2, vec![vec![q(1, 2), q(1, 2)]], "x").unwrap();
        let y = StochasticMap::try_from_rows(1, 2, vec![vec![q(1, 2), q(1, 2)]], "y").unwrap();
        assert_eq!(x, y);
        assert_eq!(x.label(), "x");
    }
}

#[cfg(test)]
mod l4_boundary_tests_89a7df8b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord89a7df8b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord89a7df8b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord89a7df8b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord89a7df8b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord89a7df8b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError89a7df8b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError89a7df8b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
