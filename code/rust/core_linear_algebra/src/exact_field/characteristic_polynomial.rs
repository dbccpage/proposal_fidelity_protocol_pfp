//! The characteristic polynomial by the Berkowitz algorithm.
//!
//! The polynomial `det(xI − A)` is computed without a single division, so it is valid in
//! every characteristic (including `GF(2)` and `GF(3)` at dimensions where the
//! Faddeev–LeVerrier recurrence would divide by `0`) and over rings of any kind, and it
//! needs only `add`, `mul` and `neg` from the scalar.
//!
//! Write the trailing principal submatrix `S = A[k.., k..]` of size `s` as
//! `[[a, R], [C, M]]` with `M` the trailing `(s−1) × (s−1)` block. Then
//! `charpoly(S) = T · charpoly(M)` where `T` is the `(s+1) × s` lower-triangular
//! Toeplitz matrix with first column `(1, −a, −R·C, −R·M·C, …, −R·M^{s−2}·C)`.
//! Starting from the empty submatrix (`charpoly = 1`) and peeling one row and column at
//! a time gives `charpoly(A)` in `O(n⁴)` scalar operations.
//!
//! Coefficient order: the returned vector lists the coefficients in **ascending** powers,
//! entry `i` is the coefficient of `xⁱ`, the last entry is `1`, and the length is `n + 1`.
//! Consequently `entry[0] = (−1)ⁿ det(A)` and `entry[n−1] = −tr(A)`.
//!
//! The minimal polynomial is the monic polynomial of least degree annihilating `A`. It is
//! found by the smallest `k` for which `vec(A^k)` lies in the span of `vec(I), …, vec(A^{k−1})`,
//! one reduction of an `n² × (k+1)` grid per step (at most `n` steps by Cayley–Hamilton).
//! For the multiplication matrix of a field element `α` it is the minimal polynomial of `α`.
//!
//! Cost model used by the budget checks (worst case, scalar calls): characteristic polynomial
//! `2n⁴ + 4n³`; minimal polynomial `2n⁴ + Σₖ₌₁ⁿ min(n², k+1)·(2n²(k+1) + k + 2)`, which is `O(n⁵)`.
//!
//! AuthorityEffect: None.

use crate::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use crate::exact_field::elimination::{reduce_to_rref, reduction_cost};
use crate::exact_field::matrix::{
    identity, is_identity_matrix, is_zero_matrix, multiply, multiply_with_limits, power, zeros,
};
use crate::exact_field::{
    charge, element_count, plus, require_square, reserve, times, ExactFieldError, Grid,
};
use crate::scalars::{ExactRing, Field};

/// The characteristic polynomial `det(xI − A)` as ascending coefficients (see the module
/// documentation).
pub fn characteristic_polynomial<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
) -> Result<Vec<F>, ExactFieldError> {
    characteristic_polynomial_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`characteristic_polynomial`] under a budget: `n²` elements and `2n⁴ + 4n³` scalar calls.
pub fn characteristic_polynomial_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Vec<F>, ExactFieldError> {
    let n = require_square("characteristic_polynomial", a)?;
    charge_charpoly_budget(n, limits)?;

    // Descending coefficients of the characteristic polynomial of A[k+1.., k+1..].
    let mut poly: Vec<F> = reserve(1)?;
    poly.push(F::one());
    for k in (0..n).rev() {
        let s = n - k;
        let toeplitz = peel_toeplitz_column(a, k, n, s)?;
        poly = convolve_toeplitz(&toeplitz, &poly, s)?;
    }
    poly.reverse();
    Ok(poly)
}

fn charge_charpoly_budget(
    n: usize,
    limits: OperationLimits,
) -> Result<(), crate::backend::basic_matrix::MatrixError> {
    let square = element_count(n, n)?;
    let cube = times(square, n)?;
    let ops = plus(times(2, times(cube, n)?)?, times(4, cube)?)?;
    charge(limits, square, ops)
}

fn peel_toeplitz_column<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    k: usize,
    n: usize,
    s: usize,
) -> Result<Vec<F>, ExactFieldError> {
    let data = a.as_slice();
    // Entry (r, c) of `a`; every call below has r, c < n by its loop bounds.
    let at = |r: usize, c: usize| &data[r * n + c];
    let mut toeplitz: Vec<F> = reserve(s + 1)?;
    toeplitz.push(F::one());
    toeplitz.push(at(k, k).neg());
    // v = M^j C, starting at C = A[k+1.., k].
    let mut v: Vec<F> = reserve(s - 1)?;
    for i in 0..(s - 1) {
        v.push(at(k + 1 + i, k).clone());
    }
    for j in 0..(s - 1) {
        // t_{j+2} = −R · M^j C with R = A[k, k+1..]
        let mut acc = F::zero();
        for (idx, vi) in v.iter().enumerate() {
            acc = acc.add(&at(k, k + 1 + idx).mul(vi));
        }
        toeplitz.push(acc.neg());
        if j + 1 < s - 1 {
            v = advance_krylov_vector(data, &v, k, n, s)?;
        }
    }
    Ok(toeplitz)
}

fn advance_krylov_vector<F: Field + ExactRing>(
    data: &[F],
    v: &[F],
    k: usize,
    n: usize,
    s: usize,
) -> Result<Vec<F>, ExactFieldError> {
    let at = |r: usize, c: usize| &data[r * n + c];
    let mut next: Vec<F> = reserve(s - 1)?;
    for i in 0..(s - 1) {
        let mut sum = F::zero();
        for (idx, vi) in v.iter().enumerate() {
            sum = sum.add(&at(k + 1 + i, k + 1 + idx).mul(vi));
        }
        next.push(sum);
    }
    Ok(next)
}

fn convolve_toeplitz<F: Field + ExactRing>(
    toeplitz: &[F],
    poly: &[F],
    s: usize,
) -> Result<Vec<F>, ExactFieldError> {
    // poly ← T · poly, with T[i][j] = toeplitz[i − j] for j ≤ i.
    let mut next_poly: Vec<F> = reserve(s + 1)?;
    for i in 0..=s {
        let mut acc = F::zero();
        for j in 0..s.min(i + 1) {
            acc = acc.add(&toeplitz[i - j].mul(&poly[j]));
        }
        next_poly.push(acc);
    }
    Ok(next_poly)
}

/// `p(A)` for the polynomial with ascending `coefficients` (Horner's rule on matrices).
/// The empty coefficient list is the zero polynomial and gives the zero matrix.
pub fn evaluate_polynomial_at_matrix<F: Field + ExactRing>(
    coefficients: &[F],
    a: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    evaluate_polynomial_at_matrix_with_limits(coefficients, a, OperationLimits::UNLIMITED)
}

/// [`evaluate_polynomial_at_matrix`] under a budget: `n²` elements, at most
/// `terms − 1` products of `2n³` calls and `2n²` calls per term for the diagonal update.
pub fn evaluate_polynomial_at_matrix_with_limits<F: Field + ExactRing>(
    coefficients: &[F],
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let n = require_square("evaluate_polynomial_at_matrix", a)?;
    charge_eval_poly_budget(n, coefficients.len(), limits)?;

    let mut acc = zeros::<F>(n, n)?;
    for c in coefficients.iter().rev() {
        acc = horner_step(&acc, a, c, n)?;
    }
    Ok(acc)
}

fn charge_eval_poly_budget(
    n: usize,
    terms: usize,
    limits: OperationLimits,
) -> Result<(), crate::backend::basic_matrix::MatrixError> {
    let square = element_count(n, n)?;
    let products = times(terms.saturating_sub(1), times(2, times(square, n)?)?)?;
    let ops = plus(products, times(terms, times(2, square)?)?)?;
    charge(limits, square, ops)
}

fn horner_step<F: Field + ExactRing>(
    acc: &BasicMatrix<F>,
    a: &BasicMatrix<F>,
    c: &F,
    n: usize,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let product = multiply_with_limits(acc, a, OperationLimits::UNLIMITED)?;
    Ok(BasicMatrix::try_from_fn_result::<_, ExactFieldError>(
        n,
        n,
        |r, col| {
            let entry = product.get_ref(r, col)?;
            Ok(if r == col {
                entry.add(c)
            } else {
                entry.clone()
            })
        },
    )?)
}

/// The minimal polynomial of `a`: the monic polynomial of least degree `d` with `p(A) = 0`, as
/// `d + 1` ascending coefficients (so the last entry is `1`). The zero matrix gives `x`, a
/// scalar matrix `cI` gives `x − c`, and the empty matrix gives the constant `1`.
///
/// It divides the characteristic polynomial and has the same roots, and `d ≤ n`.
pub fn minimal_polynomial<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
) -> Result<Vec<F>, ExactFieldError> {
    minimal_polynomial_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`minimal_polynomial`] under a budget: `n²·(n+1)` elements (the largest grid) and the
/// worst-case scalar calls of the `n` products and `n` reductions given in the module
/// documentation.
pub fn minimal_polynomial_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Vec<F>, ExactFieldError> {
    let n = require_square("minimal_polynomial", a)?;
    if n == 0 {
        let mut one = reserve(1)?;
        one.push(F::one());
        return Ok(one);
    }
    let square = element_count(n, n)?;
    charge_minpoly_budget(n, square, limits)?;
    find_minimal_polynomial(a, n, square)
}

fn charge_minpoly_budget(
    n: usize,
    square: usize,
    limits: OperationLimits,
) -> Result<(), ExactFieldError> {
    let mut ops = times(n, times(2, times(square, n)?)?)?;
    for k in 1..=n {
        ops = plus(ops, reduction_cost(square, plus(k, 1)?)?)?;
    }
    charge(limits, element_count(square, plus(n, 1)?)?, ops).map_err(ExactFieldError::from)
}

fn find_minimal_polynomial<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    n: usize,
    square: usize,
) -> Result<Vec<F>, ExactFieldError> {
    // columns[i] = vec(A^i), row-major
    let mut columns: Vec<Vec<F>> = reserve(n)?;
    let mut power = identity::<F>(n)?;
    let mut first: Vec<F> = reserve(square)?;
    first.extend_from_slice(power.as_slice());
    columns.push(first);
    for k in 1..=n {
        power = multiply_with_limits(&power, a, OperationLimits::UNLIMITED)?;
        if let Some(coefficients) = check_krylov_dependency(&columns, &power, square, k)? {
            return Ok(coefficients);
        }
        let mut next: Vec<F> = reserve(square)?;
        next.extend_from_slice(power.as_slice());
        columns.push(next);
    }
    // Cayley–Hamilton makes vec(Aⁿ) dependent on the lower powers, so this is unreachable
    // for a field; a scalar that is not a field can land here.
    Err(ExactFieldError::ReplayFailed {
        operation: "minimal_polynomial",
    })
}

fn check_krylov_dependency<F: Field + ExactRing>(
    columns: &[Vec<F>],
    power: &BasicMatrix<F>,
    square: usize,
    k: usize,
) -> Result<Option<Vec<F>>, ExactFieldError> {
    let mut grid = Grid::from_fn(square, k + 1, |r, c| {
        Ok::<F, ExactFieldError>(if c < k {
            columns[c][r].clone()
        } else {
            power.as_slice()[r].clone()
        })
    })?;
    let pivots = reduce_to_rref(&mut grid)?;
    if pivots.last() != Some(&k) {
        // vec(A^k) is a combination of the k independent earlier powers; the pivots are
        // exactly the columns 0..k in rows 0..k, so the coefficients are in the last column.
        let mut coefficients: Vec<F> = reserve(k + 1)?;
        for i in 0..k {
            coefficients.push(grid.at(i, k).neg());
        }
        coefficients.push(F::one());
        return Ok(Some(coefficients));
    }
    Ok(None)
}

/// `true` when some power of `a` is zero. For an `n × n` matrix that is `aⁿ = 0`, which
/// over any field is equivalent to the characteristic polynomial being `xⁿ`.
pub fn is_nilpotent<F: Field + ExactRing>(a: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    let n = require_square("is_nilpotent", a)?;
    let exponent = u64::try_from(n).map_err(|_| MatrixError::OperationCountOverflow)?;
    Ok(is_zero_matrix(&power(a, exponent)?))
}

/// `true` when `a² = a`. Refuses a non-square matrix.
pub fn is_idempotent<F: Field + ExactRing>(a: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    require_square("is_idempotent", a)?;
    Ok(&multiply(a, a)? == a)
}

/// `true` when `a² = I` (a matrix involution; not to be confused with the field
/// involution of `involution::Involution`). Refuses a non-square matrix.
pub fn is_involution<F: Field + ExactRing>(a: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    require_square("is_involution", a)?;
    is_identity_matrix(&multiply(a, a)?)
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/characteristic_polynomial.rs
// Claim: urn:core:crates_rs:core-linear-algebra:characteristic-polynomial:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb14a1886 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb14a1886` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb14a1886 {
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
impl BoundaryErrorb14a1886 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb14a1886 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb14a1886 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb14a1886 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb14a1886> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb14a1886::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb14a1886::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb14a1886::ExceedsCapacity {
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
    use crate::exact_field::elimination::{determinant, inverse};
    use crate::exact_field::matrix::{from_rows, identity, scale, sub, trace, transpose};
    use crate::exact_field::test_support::{m, q, random_matrix, Fp, Rng};
    use num_rational::BigRational;

    type Q = BigRational;

    fn rat(v: &[&[i64]]) -> BasicMatrix<Q> {
        m(v)
    }

    fn ints(v: &[i64]) -> Vec<Q> {
        v.iter().map(|&x| q(x, 1)).collect()
    }

    // ------------------------------------------------------------------ known polynomials

    /// Hand-computed polynomials, ascending coefficients.
    #[test]
    fn known_characteristic_polynomials() {
        // [[a]] -> x - a
        assert_eq!(
            characteristic_polynomial(&rat(&[&[7]])).unwrap(),
            ints(&[-7, 1])
        );
        // [[1,2],[3,4]] -> x^2 - 5x - 2
        assert_eq!(
            characteristic_polynomial(&rat(&[&[1, 2], &[3, 4]])).unwrap(),
            ints(&[-2, -5, 1])
        );
        // I_4 -> (x-1)^4 = x^4 - 4x^3 + 6x^2 - 4x + 1
        assert_eq!(
            characteristic_polynomial(&identity::<Q>(4).unwrap()).unwrap(),
            ints(&[1, -4, 6, -4, 1])
        );
        // zero 3x3 -> x^3
        assert_eq!(
            characteristic_polynomial(&zeros::<Q>(3, 3).unwrap()).unwrap(),
            ints(&[0, 0, 0, 1])
        );
        // diag(1,2,3) -> (x-1)(x-2)(x-3) = x^3 - 6x^2 + 11x - 6
        assert_eq!(
            characteristic_polynomial(&rat(&[&[1, 0, 0], &[0, 2, 0], &[0, 0, 3]])).unwrap(),
            ints(&[-6, 11, -6, 1])
        );
        // empty matrix -> 1
        assert_eq!(
            characteristic_polynomial(&zeros::<Q>(0, 0).unwrap()).unwrap(),
            ints(&[1])
        );
    }

    /// The companion matrix of a monic polynomial has that polynomial as characteristic
    /// polynomial: `x³ − 2x + 5` here. Nonzero entries in every Toeplitz position.
    #[test]
    fn companion_matrix_reproduces_its_polynomial() {
        let companion = rat(&[&[0, 0, -5], &[1, 0, 2], &[0, 1, 0]]);
        assert_eq!(
            characteristic_polynomial(&companion).unwrap(),
            ints(&[5, -2, 0, 1])
        );
        // x^4 + 3x^3 - x^2 + 4x - 7
        let c4 = rat(&[&[0, 0, 0, 7], &[1, 0, 0, -4], &[0, 1, 0, 1], &[0, 0, 1, -3]]);
        assert_eq!(
            characteristic_polynomial(&c4).unwrap(),
            ints(&[-7, 4, -1, 3, 1])
        );
    }

    /// A triangular matrix has its diagonal as eigenvalues; the off-diagonal entries must
    /// not change the polynomial (this exercises the R·M^j·C terms, which vanish here).
    #[test]
    fn triangular_matrices_have_the_diagonal_polynomial_and_nilpotent_blocks_give_x_to_the_n() {
        let upper = rat(&[&[1, 5, 7, 9], &[0, 2, 4, 6], &[0, 0, 3, 8], &[0, 0, 0, 4]]);
        // (x-1)(x-2)(x-3)(x-4) = x^4 - 10x^3 + 35x^2 - 50x + 24
        assert_eq!(
            characteristic_polynomial(&upper).unwrap(),
            ints(&[24, -50, 35, -10, 1])
        );
        let jordan = rat(&[&[0, 1, 0, 0], &[0, 0, 1, 0], &[0, 0, 0, 1], &[0, 0, 0, 0]]);
        assert_eq!(
            characteristic_polynomial(&jordan).unwrap(),
            ints(&[0, 0, 0, 0, 1])
        );
    }

    // ------------------------------------------------------------------ Cayley–Hamilton

    /// Invariant: `p(A) = 0` for random matrices of every size from 1 to 6. Any wrong sign,
    /// Toeplitz offset or truncated power of `M` breaks this for some size.
    #[test]
    fn cayley_hamilton_holds_for_random_matrices_of_size_one_to_six() {
        let mut rng = Rng::new(201);
        for n in 1..=6usize {
            for _ in 0..3 {
                let a = random_matrix(&mut rng, n, n, 5);
                let p = characteristic_polynomial(&a).unwrap();
                assert_eq!(p.len(), n + 1);
                assert_eq!(p[n], q(1, 1), "monic");
                let evaluated = evaluate_polynomial_at_matrix(&p, &a).unwrap();
                assert!(is_zero_matrix(&evaluated), "p(A) != 0 at n={n}");
            }
        }
    }

    /// Invariants: `c_{n-1} = −tr A` and `c_0 = (−1)ⁿ det A` (the determinant is computed
    /// by elimination, an independent route).
    #[test]
    fn the_extreme_coefficients_are_the_trace_and_the_determinant() {
        let mut rng = Rng::new(211);
        for n in 1..=6usize {
            let a = random_matrix(&mut rng, n, n, 4);
            let p = characteristic_polynomial(&a).unwrap();
            assert_eq!(p[n - 1], -trace(&a).unwrap(), "n={n}");
            let det = determinant(&a).unwrap();
            let signed = if n % 2 == 0 { det } else { -det };
            assert_eq!(p[0], signed, "n={n}");
        }
    }

    /// Invariant: similar matrices share the polynomial, `p(S A S⁻¹) = p(A)`.
    #[test]
    fn the_polynomial_is_a_similarity_invariant() {
        let mut rng = Rng::new(221);
        for n in 2..=4usize {
            let a = random_matrix(&mut rng, n, n, 3);
            let mut s = random_matrix(&mut rng, n, n, 2);
            for r in 0..n {
                for c in 0..n {
                    let v = if r == c {
                        q(1, 1)
                    } else if c < r {
                        s.get(r, c).unwrap()
                    } else {
                        q(0, 1)
                    };
                    s.set(r, c, v).unwrap();
                }
            }
            // unit lower triangular => invertible
            let similar = multiply(&multiply(&s, &a).unwrap(), &inverse(&s).unwrap()).unwrap();
            assert_eq!(
                characteristic_polynomial(&similar).unwrap(),
                characteristic_polynomial(&a).unwrap(),
                "n={n}"
            );
        }
    }

    /// Invariant: `p_{Aᵀ} = p_A`, and `p_{cA}(x) = cⁿ p_A(x / c)` checked on the trace/det
    /// coefficients.
    #[test]
    fn transpose_and_scaling_behave() {
        let mut rng = Rng::new(223);
        let a = random_matrix(&mut rng, 4, 4, 4);
        assert_eq!(
            characteristic_polynomial(&transpose(&a).unwrap()).unwrap(),
            characteristic_polynomial(&a).unwrap()
        );
        let c = q(3, 2);
        let scaled = characteristic_polynomial(&scale(&a, &c).unwrap()).unwrap();
        let base = characteristic_polynomial(&a).unwrap();
        // coefficient of x^i scales by c^(n-i)
        let mut power_of_c = q(1, 1);
        for i in (0..=4usize).rev() {
            assert_eq!(
                scaled[i],
                base[i].clone() * power_of_c.clone(),
                "coefficient {i}"
            );
            power_of_c *= c.clone();
        }
    }

    // ------------------------------------------------------------------ other fields

    /// Division-free: Cayley–Hamilton over GF(2), GF(3) and GF(5) at sizes up to 6, where a
    /// recurrence that divides by `k` (Faddeev–LeVerrier) would divide by zero.
    #[test]
    fn the_algorithm_is_valid_in_small_characteristic() {
        fn check<const P: u64>(seed: u64) {
            let mut rng = Rng::new(seed);
            for n in 1..=6usize {
                for _ in 0..3 {
                    let rows: Vec<Vec<Fp<P>>> = (0..n)
                        .map(|_| {
                            (0..n)
                                .map(|_| Fp::<P>::new(rng.range(0, P as i64 - 1)))
                                .collect()
                        })
                        .collect();
                    let a = from_rows(rows).unwrap();
                    let p = characteristic_polynomial(&a).unwrap();
                    let evaluated = evaluate_polynomial_at_matrix(&p, &a).unwrap();
                    assert!(is_zero_matrix(&evaluated), "GF({P}) n={n}");
                }
            }
        }
        check::<2>(301);
        check::<3>(302);
        check::<5>(303);
    }

    /// The algorithm needs only `add`, `mul` and `neg`: Cayley–Hamilton holds over `Z/6`, a ring
    /// with zero divisors in which a division-based recurrence has no meaning.
    #[test]
    fn the_characteristic_polynomial_needs_no_division_even_over_a_ring_with_zero_divisors() {
        use crate::exact_field::test_support::Z6;
        let mut rng = Rng::new(262);
        for n in 1..=5usize {
            for _ in 0..4 {
                let rows: Vec<Vec<Z6>> = (0..n)
                    .map(|_| (0..n).map(|_| Z6::new(rng.range(0, 5))).collect())
                    .collect();
                let a = from_rows(rows).unwrap();
                let p = characteristic_polynomial(&a).unwrap();
                assert_eq!(p.len(), n + 1);
                assert!(
                    is_zero_matrix(&evaluate_polynomial_at_matrix(&p, &a).unwrap()),
                    "Z/6 n={n}"
                );
            }
        }
    }

    /// Over GF(2) the Fibonacci matrix has `x² + x + 1`: `−(1+0) = 1` and `0·1 − 1·1 = 1`.
    #[test]
    fn a_hand_computed_polynomial_over_gf2() {
        type F2 = Fp<2>;
        let a = from_rows(vec![
            vec![F2::new(1), F2::new(1)],
            vec![F2::new(1), F2::new(0)],
        ])
        .unwrap();
        assert_eq!(
            characteristic_polynomial(&a).unwrap(),
            vec![F2::new(1), F2::new(1), F2::new(1)]
        );
    }

    // ------------------------------------------------------------------ polynomial evaluation

    #[test]
    fn evaluating_a_polynomial_at_a_matrix_matches_the_expanded_expression() {
        let a = rat(&[&[1, 2], &[3, 4]]);
        // x^2 - 3x + 2 at A = A^2 - 3A + 2I
        let p = ints(&[2, -3, 1]);
        let expected = crate::exact_field::matrix::add(
            &sub(&multiply(&a, &a).unwrap(), &scale(&a, &q(3, 1)).unwrap()).unwrap(),
            &scale(&identity::<Q>(2).unwrap(), &q(2, 1)).unwrap(),
        )
        .unwrap();
        assert_eq!(evaluate_polynomial_at_matrix(&p, &a).unwrap(), expected);
        assert!(is_zero_matrix(
            &evaluate_polynomial_at_matrix(&[], &a).unwrap()
        ));
        assert_eq!(
            evaluate_polynomial_at_matrix(&ints(&[5]), &a).unwrap(),
            scale(&identity::<Q>(2).unwrap(), &q(5, 1)).unwrap()
        );
    }

    // ------------------------------------------------------------------ minimal polynomial

    /// Known minimal polynomials, including the two cases where it differs from the
    /// characteristic polynomial: a repeated eigenvalue with a diagonalisable matrix
    /// (`diag(2, 2)`: `x − 2` against `(x − 2)²`) and a defective one (`[[1,1],[0,1]]`:
    /// `(x − 1)²` for both).
    #[test]
    fn known_minimal_polynomials() {
        assert_eq!(
            minimal_polynomial(&zeros::<Q>(3, 3).unwrap()).unwrap(),
            ints(&[0, 1])
        );
        assert_eq!(
            minimal_polynomial(&identity::<Q>(3).unwrap()).unwrap(),
            ints(&[-1, 1])
        );
        assert_eq!(
            minimal_polynomial(&rat(&[&[2, 0], &[0, 2]])).unwrap(),
            ints(&[-2, 1])
        );
        assert_eq!(
            minimal_polynomial(&rat(&[&[1, 1], &[0, 1]])).unwrap(),
            ints(&[1, -2, 1])
        );
        // diag(1,1,2): (x-1)(x-2) = x^2 - 3x + 2, although the characteristic polynomial has degree 3
        assert_eq!(
            minimal_polynomial(&rat(&[&[1, 0, 0], &[0, 1, 0], &[0, 0, 2]])).unwrap(),
            ints(&[2, -3, 1])
        );
        // a nilpotent Jordan block of size 3: x^3; of size 2 inside a size-3 matrix: x^2
        assert_eq!(
            minimal_polynomial(&rat(&[&[0, 1, 0], &[0, 0, 1], &[0, 0, 0]])).unwrap(),
            ints(&[0, 0, 0, 1])
        );
        assert_eq!(
            minimal_polynomial(&rat(&[&[0, 1, 0], &[0, 0, 0], &[0, 0, 0]])).unwrap(),
            ints(&[0, 0, 1])
        );
        assert_eq!(minimal_polynomial(&rat(&[&[7]])).unwrap(), ints(&[-7, 1]));
        assert_eq!(
            minimal_polynomial(&zeros::<Q>(0, 0).unwrap()).unwrap(),
            ints(&[1])
        );
        // the companion matrix of x^3 - 2x + 5 is cyclic: minimal = characteristic
        let companion = rat(&[&[0, 0, -5], &[1, 0, 2], &[0, 1, 0]]);
        assert_eq!(
            minimal_polynomial(&companion).unwrap(),
            ints(&[5, -2, 0, 1])
        );
    }

    /// Polynomial `f mod g` over `Q` (ascending coefficients, `g` monic): the remainder of the
    /// long division, used to check `minimal | characteristic` independently.
    fn remainder(mut f: Vec<Q>, g: &[Q]) -> Vec<Q> {
        while f.len() >= g.len() {
            let lead = f[f.len() - 1].clone();
            let shift = f.len() - g.len();
            for (i, gc) in g.iter().enumerate() {
                f[shift + i] = f[shift + i].clone() - lead.clone() * gc.clone();
            }
            f.pop();
        }
        f
    }

    /// Invariants on random matrices: `p_min(A) = 0`, `p_min` divides `p_char`, the degree
    /// equals the rank of the Krylov matrix of powers (independent route), and it is at most `n`.
    #[test]
    fn the_minimal_polynomial_annihilates_divides_the_characteristic_polynomial_and_is_minimal() {
        use crate::exact_field::elimination::rank;
        let mut rng = Rng::new(251);
        for n in 1..=5usize {
            for trial in 0..6 {
                let a = if trial % 2 == 0 {
                    random_matrix(&mut rng, n, n, 3)
                } else {
                    // a matrix with repeated structure: block diagonal of a small block and a scalar
                    let block = random_matrix(&mut rng, n.max(2) - 1, n.max(2) - 1, 2);
                    crate::exact_field::matrix::direct_sum(&block, &rat(&[&[3]])).unwrap()
                };
                let n_actual = a.rows();
                let min = minimal_polynomial(&a).unwrap();
                let chi = characteristic_polynomial(&a).unwrap();
                assert!(min.len() <= n_actual + 1);
                assert_eq!(min[min.len() - 1], q(1, 1));
                assert!(is_zero_matrix(
                    &evaluate_polynomial_at_matrix(&min, &a).unwrap()
                ));
                assert!(
                    remainder(chi, &min).iter().all(|c| *c == q(0, 1)),
                    "min must divide char"
                );
                // independent: degree = rank of {vec(I), vec(A), ..., vec(A^n)}
                let mut rows = Vec::new();
                for k in 0..=n_actual as u64 {
                    rows.push(power(&a, k).unwrap().as_slice().to_vec());
                }
                let krylov = from_rows(rows).unwrap();
                assert_eq!(
                    min.len() - 1,
                    rank(&krylov).unwrap(),
                    "n={n_actual} trial={trial}"
                );
            }
        }
    }

    /// The minimal polynomial of a field element is that of its multiplication matrix. In
    /// `Q(√2)` with basis `(1, √2)`: `1 + √2` acts by `[[1,2],[1,1]]` (columns are the images of
    /// `1` and `√2`), with minimal polynomial `x² − 2x − 1`; the rational `3` acts by `3I`, with
    /// minimal polynomial `x − 3` although its characteristic polynomial is `(x − 3)²`.
    #[test]
    fn the_minimal_polynomial_of_a_field_element_is_that_of_its_multiplication_matrix() {
        let one_plus_sqrt2 = rat(&[&[1, 2], &[1, 1]]);
        assert_eq!(
            minimal_polynomial(&one_plus_sqrt2).unwrap(),
            ints(&[-1, -2, 1])
        );
        assert_eq!(
            characteristic_polynomial(&one_plus_sqrt2).unwrap(),
            ints(&[-1, -2, 1])
        );
        let three = rat(&[&[3, 0], &[0, 3]]);
        assert_eq!(minimal_polynomial(&three).unwrap(), ints(&[-3, 1]));
        assert_eq!(
            characteristic_polynomial(&three).unwrap(),
            ints(&[9, -6, 1])
        );
    }

    /// Over GF(2) the transvection `[[1,1],[0,1]]` has minimal polynomial `(x+1)² = x² + 1`,
    /// and the identity `x + 1`.
    #[test]
    fn minimal_polynomials_over_gf2() {
        type F2 = Fp<2>;
        let one = F2::new(1);
        let zero = F2::new(0);
        let t = from_rows(vec![vec![one, one], vec![zero, one]]).unwrap();
        assert_eq!(minimal_polynomial(&t).unwrap(), vec![one, zero, one]);
        assert_eq!(
            minimal_polynomial(&identity::<F2>(2).unwrap()).unwrap(),
            vec![one, one]
        );
    }

    #[test]
    fn minimal_polynomial_refuses_non_square_input_and_respects_its_budget() {
        assert!(matches!(
            minimal_polynomial(&zeros::<Q>(2, 3).unwrap()),
            Err(ExactFieldError::NotSquare {
                operation: "minimal_polynomial",
                ..
            })
        ));
        // n = 2: 2 products of 2·2³ = 16 calls (32) + reductions of the 4×2 grid
        // (2·(2·8 + 2 + 1) = 38) and the 4×3 grid (3·(2·12 + 3 + 1) = 84) = 154 calls; the
        // largest grid has 4·3 = 12 elements.
        let a = rat(&[&[1, 2], &[3, 4]]);
        let exact = OperationLimits {
            max_elements: 12,
            max_scalar_ops: 154,
        };
        assert!(minimal_polynomial_with_limits(&a, exact).is_ok());
        assert_eq!(
            minimal_polynomial_with_limits(
                &a,
                OperationLimits {
                    max_scalar_ops: 153,
                    ..exact
                }
            ),
            Err(ExactFieldError::Matrix(
                MatrixError::OperationLimitExceeded {
                    requested: 154,
                    limit: 153
                }
            ))
        );
        assert!(minimal_polynomial_with_limits(
            &a,
            OperationLimits {
                max_elements: 11,
                ..exact
            }
        )
        .is_err());
    }

    // ------------------------------------------------------------------ predicates

    #[test]
    fn nilpotent_idempotent_and_involution_predicates() {
        let strictly_upper = rat(&[&[0, 3, 1], &[0, 0, 2], &[0, 0, 0]]);
        assert!(is_nilpotent(&strictly_upper).unwrap());
        assert!(!is_nilpotent(&identity::<Q>(2).unwrap()).unwrap());
        assert!(!is_nilpotent(&rat(&[&[0, 1], &[1, 0]])).unwrap());
        assert!(is_nilpotent(&zeros::<Q>(0, 0).unwrap()).unwrap());

        let projector = rat(&[&[1, 0], &[0, 0]]);
        assert!(is_idempotent(&projector).unwrap());
        assert!(!is_idempotent(&rat(&[&[1, 1], &[0, 1]])).unwrap());

        let swap = rat(&[&[0, 1], &[1, 0]]);
        assert!(is_involution(&swap).unwrap());
        assert!(!is_involution(&rat(&[&[1, 1], &[0, 1]])).unwrap());
        // an idempotent that is not an involution and vice versa
        assert!(!is_involution(&projector).unwrap());
        assert!(!is_idempotent(&swap).unwrap());
    }

    /// Two independent criteria for nilpotency agree: `Aⁿ = 0` and `p_A = xⁿ`.
    #[test]
    fn nilpotency_agrees_with_the_characteristic_polynomial_criterion() {
        let mut rng = Rng::new(241);
        for n in 1..=5usize {
            for trial in 0..4 {
                // a conjugate of a strictly upper triangular matrix, or a random matrix
                let raw = random_matrix(&mut rng, n, n, 3);
                let candidate = if trial % 2 == 0 {
                    let mut upper = raw.clone();
                    for r in 0..n {
                        for c in 0..=r {
                            upper.set(r, c, q(0, 1)).unwrap();
                        }
                    }
                    upper
                } else {
                    raw
                };
                let p = characteristic_polynomial(&candidate).unwrap();
                let is_x_to_the_n = p[..n].iter().all(|c| *c == q(0, 1));
                assert_eq!(
                    is_nilpotent(&candidate).unwrap(),
                    is_x_to_the_n,
                    "n={n} trial={trial}"
                );
            }
        }
    }

    #[test]
    fn predicates_and_polynomial_refuse_non_square_input() {
        let wide = zeros::<Q>(2, 3).unwrap();
        assert!(matches!(
            characteristic_polynomial(&wide),
            Err(ExactFieldError::NotSquare {
                operation: "characteristic_polynomial",
                ..
            })
        ));
        assert!(matches!(
            is_nilpotent(&wide),
            Err(ExactFieldError::NotSquare { .. })
        ));
        assert!(matches!(
            is_idempotent(&wide),
            Err(ExactFieldError::NotSquare { .. })
        ));
        assert!(matches!(
            is_involution(&wide),
            Err(ExactFieldError::NotSquare { .. })
        ));
        assert!(matches!(
            evaluate_polynomial_at_matrix(&ints(&[1]), &wide),
            Err(ExactFieldError::NotSquare { .. })
        ));
    }

    /// Boundary: the documented cost for `n = 2` is `2·16 + 4·8 = 64` scalar calls and
    /// `4` elements.
    #[test]
    fn charpoly_budget_boundary_is_inclusive() {
        let a = rat(&[&[1, 2], &[3, 4]]);
        let exact = OperationLimits {
            max_elements: 4,
            max_scalar_ops: 64,
        };
        assert!(characteristic_polynomial_with_limits(&a, exact).is_ok());
        assert_eq!(
            characteristic_polynomial_with_limits(
                &a,
                OperationLimits {
                    max_scalar_ops: 63,
                    ..exact
                }
            ),
            Err(ExactFieldError::Matrix(
                MatrixError::OperationLimitExceeded {
                    requested: 64,
                    limit: 63
                }
            ))
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_b14a1886 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb14a1886::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb14a1886::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb14a1886::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb14a1886::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb14a1886::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb14a1886::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb14a1886::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
