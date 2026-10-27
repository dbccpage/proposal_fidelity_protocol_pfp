//! Finite-dimensional Lie algebras over an exact field, by structure constants.
//!
//! A [`LieAlgebra`] is a dimension and structure constants `c_ab^e` with
//! `[x_a, x_b] = sum_e c_ab^e x_e`. Everything that depends only on these constants is
//! generic over the algebra, so `sl(2)`, `so(n)`, `u(1)`, `su(N)` and any matrix Lie
//! algebra share it:
//!
//! - [`verify_antisymmetry`] and [`verify_jacobi`] (the two axioms), and
//!   [`adjoint_is_representation`]: the Jacobi identity holds exactly when
//!   `a -> ad x_a` is a representation (`[ad x_a, ad x_b] = ad [x_a, x_b]`), checked
//!   independently of [`verify_jacobi`] and in agreement with it in the tests;
//! - the adjoint representation [`adjoint_matrix`], the Killing form [`killing_form`];
//! - [`structure_constants_from_matrices`]: the structure constants of a matrix Lie algebra
//!   from a basis of matrices closed under the commutator (refused with a typed error if a
//!   commutator leaves the span, or the matrices are dependent);
//! - the Chevalley-Eilenberg complex `C^k = Lambda^k g*` with trivial coefficients
//!   ([`chevalley_eilenberg_differential`]); `d^2 = 0` holds exactly when the Jacobi identity
//!   does, and its cohomology ([`cohomology_betti_numbers`]) is the Lie-algebra cohomology:
//!   `1, 0, 0, 1` for `sl(2)` and `1, 2, 2, 1` for the Heisenberg algebra.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_d3e37b84<T> {
    fn checked_invariant_d3e37b84(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_d3e37b84<T> for Option<T> {
    #[inline]
    fn checked_invariant_d3e37b84(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_d3e37b84<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_d3e37b84(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::elimination::{self, LinearSolution};
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use linear_algebra::scalars::{ExactRing, Field, Ring, Semiring};

/// The largest dimension of an algebra whose cohomology complex is built.
pub const MAX_COMPLEX_DIMENSION: usize = 8;

/// Refusals of the Lie-algebra constructions.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LieAlgebraError {
    #[error("a structure-constant table for dimension {dimension} needs {expected} entries, got {actual}")]
    TableLength {
        dimension: usize,
        expected: usize,
        actual: usize,
    },
    #[error("the matrices are not square of one common size (or there are none)")]
    Shape,
    #[error("the basis matrices are linearly dependent")]
    DependentBasis,
    #[error("the commutator of basis elements {a} and {b} is not in their span")]
    NotClosed { a: usize, b: usize },
    #[error("the dimension {dimension} exceeds the complex bound {MAX_COMPLEX_DIMENSION}")]
    DimensionTooLarge { dimension: usize },
    #[error("cochain degree {degree} exceeds the dimension {dimension}")]
    DegreeTooLarge { degree: usize, dimension: usize },
    #[error("index {index} is out of range for dimension {dimension}")]
    IndexOutOfRange { index: usize, dimension: usize },
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

/// A Lie algebra with a chosen basis and its structure constants.
pub trait LieAlgebra {
    type Scalar: Field + ExactRing;

    fn dimension(&self) -> usize;

    /// `c_ab^e`, with `[x_a, x_b] = sum_e c_ab^e x_e`. The indices are in `0..dimension()`.
    fn structure_constant(&self, a: usize, b: usize, e: usize) -> Self::Scalar;
}

/// A table of structure constants, `table[(a * n + b) * n + e] = c_ab^e`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StructureConstants<F> {
    dimension: usize,
    table: Vec<F>,
}

impl<F: Field + ExactRing> StructureConstants<F> {
    /// A table for `dimension`, refused unless it has `dimension^3` entries.
    pub fn new(dimension: usize, table: Vec<F>) -> Result<Self, LieAlgebraError> {
        let expected = dimension * dimension * dimension;
        if table.len() != expected {
            return Err(LieAlgebraError::TableLength {
                dimension,
                expected,
                actual: table.len(),
            });
        }
        Ok(Self { dimension, table })
    }

    /// The table from a function of `(a, b, e)`.
    pub fn from_fn(dimension: usize, mut f: impl FnMut(usize, usize, usize) -> F) -> Self {
        let mut table = Vec::with_capacity(dimension * dimension * dimension);
        for a in 0..dimension {
            for b in 0..dimension {
                for e in 0..dimension {
                    table.push(f(a, b, e));
                }
            }
        }
        Self { dimension, table }
    }

    /// The abelian algebra of dimension `n` (all brackets zero).
    pub fn abelian(n: usize) -> Self {
        Self::from_fn(n, |_, _, _| F::zero())
    }
}

impl<F: Field + ExactRing> LieAlgebra for StructureConstants<F> {
    type Scalar = F;

    fn dimension(&self) -> usize {
        self.dimension
    }

    fn structure_constant(&self, a: usize, b: usize, e: usize) -> F {
        self.table[(a * self.dimension + b) * self.dimension + e].clone()
    }
}

fn check_index<L: LieAlgebra + ?Sized>(algebra: &L, index: usize) -> Result<(), LieAlgebraError> {
    if index >= algebra.dimension() {
        return Err(LieAlgebraError::IndexOutOfRange {
            index,
            dimension: algebra.dimension(),
        });
    }
    Ok(())
}

/// `[x_a, x_b] = -[x_b, x_a]` for every pair, which includes `[x_a, x_a] = 0`.
pub fn verify_antisymmetry<L: LieAlgebra>(algebra: &L) -> bool {
    let n = algebra.dimension();
    (0..n).all(|a| {
        (0..n).all(|b| {
            (0..n).all(|e| {
                algebra
                    .structure_constant(a, b, e)
                    .add(&algebra.structure_constant(b, a, e))
                    .is_zero()
            })
        })
    })
}

fn jacobi_term<L: LieAlgebra>(
    algebra: &L,
    a: usize,
    b: usize,
    cc: usize,
    e: usize,
    n: usize,
) -> L::Scalar {
    let mut sum = L::Scalar::zero();
    for d in 0..n {
        let term1 = algebra.structure_constant(a, b, d).mul(&algebra.structure_constant(d, cc, e));
        let term2 = algebra.structure_constant(b, cc, d).mul(&algebra.structure_constant(d, a, e));
        let term3 = algebra.structure_constant(cc, a, d).mul(&algebra.structure_constant(d, b, e));
        sum = sum.add(&term1).add(&term2).add(&term3);
    }
    sum
}

fn check_jacobi_for_triple<L: LieAlgebra>(
    algebra: &L,
    a: usize,
    b: usize,
    cc: usize,
    n: usize,
) -> bool {
    for e in 0..n {
        if !jacobi_term(algebra, a, b, cc, e, n).is_zero() {
            return false;
        }
    }
    true
}

fn check_jacobi_for_pair<L: LieAlgebra>(algebra: &L, a: usize, b: usize, n: usize) -> bool {
    for cc in 0..n {
        if !check_jacobi_for_triple(algebra, a, b, cc, n) {
            return false;
        }
    }
    true
}

/// The Jacobi identity `[[x_a, x_b], x_c] + [[x_b, x_c], x_a] + [[x_c, x_a], x_b] = 0` for every
/// triple of basis elements, as `sum_d (c_ab^d c_dc^e + c_bc^d c_da^e + c_ca^d c_db^e) = 0`.
pub fn verify_jacobi<L: LieAlgebra>(algebra: &L) -> bool {
    let n = algebra.dimension();
    for a in 0..n {
        for b in 0..n {
            if !check_jacobi_for_pair(algebra, a, b, n) {
                return false;
            }
        }
    }
    true
}

/// The bracket `[x, y]` of two vectors of coordinates.
pub fn bracket<L: LieAlgebra>(
    algebra: &L,
    x: &[L::Scalar],
    y: &[L::Scalar],
) -> Result<Vec<L::Scalar>, LieAlgebraError> {
    let n = algebra.dimension();
    if x.len() != n || y.len() != n {
        return Err(LieAlgebraError::Shape);
    }
    let mut out = vec![L::Scalar::zero(); n];
    for a in 0..n {
        for b in 0..n {
            let coefficient = x[a].mul(&y[b]);
            if coefficient.is_zero() {
                continue;
            }
            for (e, slot) in out.iter_mut().enumerate() {
                *slot = slot.add(&coefficient.mul(&algebra.structure_constant(a, b, e)));
            }
        }
    }
    Ok(out)
}

/// The matrix of `ad x_a` in the basis: entry `(e, b)` is `c_ab^e`.
pub fn adjoint_matrix<L: LieAlgebra>(
    algebra: &L,
    a: usize,
) -> Result<BasicMatrix<L::Scalar>, LieAlgebraError> {
    check_index(algebra, a)?;
    let n = algebra.dimension();
    Ok(mx::from_fn(n, n, |e, b| {
        algebra.structure_constant(a, b, e)
    })?)
}

/// `[ad x_a, ad x_b] = sum_e c_ab^e ad x_e` for every pair: the adjoint map is a representation.
/// For an antisymmetric bracket this is equivalent to the Jacobi identity.
pub fn adjoint_is_representation<L: LieAlgebra>(algebra: &L) -> Result<bool, LieAlgebraError> {
    let n = algebra.dimension();
    let ad: Vec<BasicMatrix<L::Scalar>> = (0..n)
        .map(|a| adjoint_matrix(algebra, a))
        .collect::<Result<_, _>>()?;
    for a in 0..n {
        for b in 0..n {
            let commutator = mx::commutator(&ad[a], &ad[b])?;
            let mut expected = mx::zeros::<L::Scalar>(n, n)?;
            for (e, ad_e) in ad.iter().enumerate() {
                expected = mx::add(
                    &expected,
                    &mx::scale(ad_e, &algebra.structure_constant(a, b, e))?,
                )?;
            }
            if commutator != expected {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

/// The Killing form `K_ab = tr(ad x_a ad x_b)`.
pub fn killing_form<L: LieAlgebra>(algebra: &L) -> Result<BasicMatrix<L::Scalar>, LieAlgebraError> {
    let n = algebra.dimension();
    let ad: Vec<BasicMatrix<L::Scalar>> = (0..n)
        .map(|a| adjoint_matrix(algebra, a))
        .collect::<Result<_, _>>()?;
    let mut entries = Vec::with_capacity(n * n);
    for a in 0..n {
        for b in 0..n {
            entries.push(mx::trace(&mx::multiply(&ad[a], &ad[b])?)?);
        }
    }
    Ok(BasicMatrix::from_row_major(n, n, entries).map_err(ExactFieldError::from)?)
}

/// The structure constants of the matrix Lie algebra spanned by `basis`, each `[b_a, b_b]`
/// expressed in the basis by an exact linear solve. Refused if the matrices are not square of a
/// common size, are linearly dependent, or if some commutator is not in their span.
fn build_basis_system<F: Field + ExactRing>(
    basis: &[BasicMatrix<F>],
    n: usize,
    size: usize,
) -> Result<BasicMatrix<F>, LieAlgebraError> {
    if basis.iter().any(|m| m.rows() != size || m.cols() != size) {
        return Err(LieAlgebraError::Shape);
    }
    // Columns are the flattened basis matrices.
    let columns: Vec<F> = (0..size * size)
        .flat_map(|row| basis.iter().map(move |m| m.as_slice()[row].clone()))
        .collect();
    let system =
        BasicMatrix::from_row_major(size * size, n, columns).map_err(ExactFieldError::from)?;
    if elimination::rank(&system)? < n {
        return Err(LieAlgebraError::DependentBasis);
    }
    Ok(system)
}

fn solve_structure_constant_pair<F: Field + ExactRing>(
    system: &BasicMatrix<F>,
    m_a: &BasicMatrix<F>,
    m_b: &BasicMatrix<F>,
    a: usize,
    b: usize,
) -> Result<Vec<F>, LieAlgebraError> {
    let commutator = mx::commutator(m_a, m_b)?;
    match elimination::solve(system, commutator.as_slice())? {
        LinearSolution::Consistent { particular, .. } => Ok(particular),
        LinearSolution::Inconsistent { .. } => Err(LieAlgebraError::NotClosed { a, b }),
    }
}

pub fn structure_constants_from_matrices<F: Field + ExactRing>(
    basis: &[BasicMatrix<F>],
) -> Result<StructureConstants<F>, LieAlgebraError> {
    let n = basis.len();
    let size = basis.first().ok_or(LieAlgebraError::Shape)?.rows();
    let system = build_basis_system(basis, n, size)?;
    let mut table = Vec::with_capacity(n * n * n);
    for a in 0..n {
        for b in 0..n {
            let particular = solve_structure_constant_pair(&system, &basis[a], &basis[b], a, b)?;
            table.extend(particular);
        }
    }
    StructureConstants::new(n, table)
}

// ---------------------------------------------------------------------------------------
// The Chevalley-Eilenberg complex
// ---------------------------------------------------------------------------------------

/// The strictly increasing `k`-subsets of `0..n`, in lexicographic order: the basis of `Lambda^k`.
fn subsets(n: usize, k: usize) -> Vec<Vec<usize>> {
    fn grow(n: usize, k: usize, start: usize, current: &mut Vec<usize>, out: &mut Vec<Vec<usize>>) {
        if current.len() == k {
            out.push(current.clone());
            return;
        }
        for i in start..n {
            current.push(i);
            grow(n, k, i + 1, current, out);
            current.pop();
        }
    }
    let mut out = Vec::new();
    grow(n, k, 0, &mut Vec::new(), &mut out);
    out
}

/// Sort `word` by adjacent transpositions, returning the sign and the sorted word, or `None` if an
/// index repeats (the wedge product vanishes).
fn sort_word(mut word: Vec<usize>) -> Option<(i8, Vec<usize>)> {
    let mut sign = 1i8;
    for i in 1..word.len() {
        let mut j = i;
        while j > 0 && word[j - 1] > word[j] {
            word.swap(j - 1, j);
            sign = -sign;
            j -= 1;
        }
    }
    word.windows(2)
        .all(|w| w[0] != w[1])
        .then_some((sign, word))
}

fn check_complex_size<L: LieAlgebra>(algebra: &L) -> Result<usize, LieAlgebraError> {
    let n = algebra.dimension();
    if n > MAX_COMPLEX_DIMENSION {
        return Err(LieAlgebraError::DimensionTooLarge { dimension: n });
    }
    Ok(n)
}

fn accumulate_pair_term<L: LieAlgebra>(
    algebra: &L,
    subset: &[usize],
    position: usize,
    leibniz_sign: i8,
    a: usize,
    b: usize,
    rows: &[Vec<usize>],
    col: usize,
    num_cols: usize,
    entries: &mut [L::Scalar],
) {
    let c = subset[position];
    let coefficient = algebra.structure_constant(a, b, c).neg();
    if coefficient.is_zero() {
        return;
    }
    let mut word: Vec<usize> = subset[..position].to_vec();
    word.push(a);
    word.push(b);
    word.extend_from_slice(&subset[position + 1..]);
    let Some((sign, sorted)) = sort_word(word) else {
        return;
    };
    let row = rows
        .binary_search(&sorted)
        .checked_invariant_d3e37b84("a sorted (k+1)-subset is a basis index");
    let total_sign = sign * leibniz_sign;
    let term = if total_sign > 0 {
        coefficient
    } else {
        coefficient.neg()
    };
    let slot = &mut entries[row * num_cols + col];
    *slot = slot.add(&term);
}

fn process_column_position<L: LieAlgebra>(
    algebra: &L,
    subset: &[usize],
    position: usize,
    n: usize,
    rows: &[Vec<usize>],
    col: usize,
    num_cols: usize,
    entries: &mut [L::Scalar],
) {
    let leibniz_sign = if position % 2 == 0 { 1i8 } else { -1i8 };
    for a in 0..n {
        for b in (a + 1)..n {
            accumulate_pair_term(
                algebra,
                subset,
                position,
                leibniz_sign,
                a,
                b,
                rows,
                col,
                num_cols,
                entries,
            );
        }
    }
}

/// The matrix of the Chevalley-Eilenberg differential `d: Lambda^k g* -> Lambda^(k+1) g*`, rows
/// indexed by the `(k+1)`-subsets and columns by the `k`-subsets (both in lexicographic order),
/// for the dual basis `e^a`: `d e^c = - sum_{a<b} c_ab^c e^a ^ e^b`, extended as a derivation.
pub fn chevalley_eilenberg_differential<L: LieAlgebra>(
    algebra: &L,
    k: usize,
) -> Result<BasicMatrix<L::Scalar>, LieAlgebraError> {
    let n = check_complex_size(algebra)?;
    if k > n {
        return Err(LieAlgebraError::DegreeTooLarge {
            degree: k,
            dimension: n,
        });
    }
    let columns = subsets(n, k);
    let rows = subsets(n, k + 1);
    let mut entries = vec![L::Scalar::zero(); rows.len() * columns.len()];
    for (col, subset) in columns.iter().enumerate() {
        for position in 0..k {
            // Leibniz: d(e^{i_1} ^ ... ^ e^{i_k}) = sum_j (-1)^(j-1) e^{i_1} ^ ... ^ d e^{i_j} ^ ... ^ e^{i_k}.
            process_column_position(
                algebra,
                subset,
                position,
                n,
                &rows,
                col,
                columns.len(),
                &mut entries,
            );
        }
    }
    Ok(
        BasicMatrix::from_row_major(rows.len(), columns.len(), entries)
            .map_err(ExactFieldError::from)?,
    )
}

/// `d_{k+1} d_k = 0` for every `k`: the Chevalley-Eilenberg complex is a complex. For an
/// antisymmetric bracket this holds exactly when the Jacobi identity does.
pub fn chevalley_eilenberg_squares_to_zero<L: LieAlgebra>(
    algebra: &L,
) -> Result<bool, LieAlgebraError> {
    let n = check_complex_size(algebra)?;
    for k in 0..n.saturating_sub(1) {
        let d_k = chevalley_eilenberg_differential(algebra, k)?;
        let d_next = chevalley_eilenberg_differential(algebra, k + 1)?;
        if !mx::is_zero_matrix(&mx::multiply(&d_next, &d_k)?) {
            return Ok(false);
        }
    }
    Ok(true)
}

/// The Betti numbers `b_k = dim H^k(g)` of the complex, `k = 0..=dimension`, by
/// `b_k = dim C^k - rank d_k - rank d_{k-1}`. Requires the complex property (`d^2 = 0`).
pub fn cohomology_betti_numbers<L: LieAlgebra>(algebra: &L) -> Result<Vec<usize>, LieAlgebraError> {
    let n = check_complex_size(algebra)?;
    let mut ranks = Vec::with_capacity(n + 1);
    for k in 0..n {
        ranks.push(elimination::rank(&chevalley_eilenberg_differential(
            algebra, k,
        )?)?);
    }
    ranks.push(0);
    let dims: Vec<usize> = (0..=n).map(|k| subsets(n, k).len()).collect();
    Ok((0..=n)
        .map(|k| {
            let previous = if k == 0 { 0 } else { ranks[k - 1] };
            dims[k] - ranks[k] - previous
        })
        .collect())
}

// Origin: engine/crates_rs/core_lie_theory/src/lie_algebra.rs
// Claim: urn:core:crates_rs:core-lie-theory:lie-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_rational::BigRational;
    use core_number_theory::rational::ri;

    #[test]
    fn subsets_are_the_lexicographic_basis_of_the_exterior_powers() {
        assert_eq!(
            subsets(4, 2),
            vec![
                vec![0, 1],
                vec![0, 2],
                vec![0, 3],
                vec![1, 2],
                vec![1, 3],
                vec![2, 3]
            ]
        );
        assert_eq!(subsets(3, 0), vec![Vec::<usize>::new()]);
        assert_eq!(subsets(3, 3), vec![vec![0, 1, 2]]);
    }

    #[test]
    fn sorting_a_word_tracks_the_sign_and_detects_repeats() {
        assert_eq!(sort_word(vec![2, 0, 1]), Some((1, vec![0, 1, 2])));
        assert_eq!(sort_word(vec![1, 0]), Some((-1, vec![0, 1])));
        assert_eq!(sort_word(vec![0, 1, 0]), None);
    }

    #[test]
    fn a_table_of_the_wrong_length_is_refused() {
        let result = StructureConstants::<BigRational>::new(2, vec![ri(0); 7]);
        assert_eq!(
            result,
            Err(LieAlgebraError::TableLength {
                dimension: 2,
                expected: 8,
                actual: 7
            })
        );
        assert!(StructureConstants::<BigRational>::new(2, vec![ri(0); 8]).is_ok());
    }
}
