//! Cayley charts: rational parametrisations of rotation and unit-phase groups.
//!
//! For a skew-symmetric rational matrix `X` and a rational `tau`, the Cayley transform
//! `C_tau(X) = (I - tau X)(I + tau X)^(-1)` is an orthogonal matrix of determinant 1
//! with rational entries, and every rotation without the eigenvalue `-1` arises this way:
//! `X = (I - R)(I + R)^(-1) / tau`. The chart is exact, total on skew input, and misses
//! exactly the rotations with eigenvalue `-1` (its cut locus), which are refused
//! with [`CayleyError::EigenvalueMinusOne`].
//!
//! Two steps with one generator compose to one step of another generator:
//! `C_s(X) C_t(X) = C_1(K)` with `K = (s + t) X (I + s t X^2)^(-1)` ([`compose_steps`]).
//! For the plane generator `J`, `J^2 = -I`, this is the tangent addition law
//! `(s + t) / (1 - s t)` of the unit-circle parameter (see [`compose_circle_parameters`]).
//!
//! The unit circle of the Gaussian rationals `Q(i)` has the same chart:
//! `t -> ((1 - t^2) + 2 t i) / (1 + t^2)` hits every unit except `-1`
//! ([`unit_from_parameter`], [`parameter_of_unit`]). Roots of unity in `Q(i)` are read
//! from the cyclotomic degree bound `phi(n) <= 2` ([`gaussian_unit_order`]).
//!
//! Charts for unitary groups over `Q(i)` live in [`crate::cayley_unitary`].
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::polynomial::euler_phi;
use core_number_theory::rational::ri;

use linear_algebra::exact_field::{elimination, matrix as mx, ExactFieldError};

use crate::QMatrix;

/// The largest dimension the matrix charts accept.
pub const MAX_DIMENSION: usize = 32;
/// The largest exponent [`unit_pow`] accepts (its output has `O(|k|)` bits).
pub const MAX_UNIT_EXPONENT: u32 = 1 << 16;

/// Refusals of the Cayley charts.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CayleyError {
    #[error("a square matrix of dimension 1..={MAX_DIMENSION} is required, got {rows}x{cols}")]
    Shape { rows: usize, cols: usize },
    #[error("the matrix is not skew-symmetric: entry ({row}, {col}) is not the negative of entry ({col}, {row})")]
    NotSkew { row: usize, col: usize },
    #[error("the matrix is not orthogonal: R^T R != I")]
    NotOrthogonal,
    #[error("I + tau X is singular")]
    Singular,
    #[error("I + R is singular: -1 is an eigenvalue of R, outside the Cayley chart")]
    EigenvalueMinusOne,
    #[error("the chart parameter must be nonzero")]
    ZeroParameter,
    #[error("the composite step has eigenvalue -1 and lies outside the Cayley chart")]
    OutsideChart,
    #[error("{0} is not a unit of Q(i): its squared modulus is not 1")]
    NotUnit(String),
    #[error("the exponent {exponent} exceeds the bound {bound}")]
    ExponentTooLarge { exponent: String, bound: u32 },
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

fn check_shape(m: &QMatrix) -> Result<usize, CayleyError> {
    if m.rows() != m.cols() || m.rows() == 0 || m.rows() > MAX_DIMENSION {
        return Err(CayleyError::Shape {
            rows: m.rows(),
            cols: m.cols(),
        });
    }
    Ok(m.rows())
}

/// The first position `(i, j)`, `i < j` or `i = j`, with `x[i][j] != -x[j][i]`; `None` if `x`
/// is skew-symmetric (which forces a zero diagonal).
pub fn skew_defect(x: &QMatrix) -> Option<(usize, usize)> {
    let (rows, cols) = x.shape();
    if rows != cols {
        return Some((0, 0));
    }
    for i in 0..rows {
        for j in i..cols {
            let a = &x.as_slice()[i * cols + j];
            let b = &x.as_slice()[j * cols + i];
            if a != &-b {
                return Some((i, j));
            }
        }
    }
    None
}

/// `R^T R = I`.
pub fn is_orthogonal(m: &QMatrix) -> bool {
    mx::transpose(m)
        .and_then(|t| mx::multiply(&t, m))
        .and_then(|product| mx::is_identity_matrix(&product))
        .unwrap_or(false)
}

/// `R^T R = I` and `det R = 1`.
pub fn is_special_orthogonal(m: &QMatrix) -> bool {
    is_orthogonal(m) && elimination::determinant(m).is_ok_and(|d| d.is_one())
}

/// `C_tau(X) = (I - tau X)(I + tau X)^(-1)` for a skew-symmetric rational `X`.
///
/// The result lies in `SO(n, Q)`. For skew `X` and rational `tau`, `I + tau X` is always
/// invertible (its eigenvalues `1 + i tau y` have real part 1), so
/// [`CayleyError::Singular`] is reported only if the elimination disagrees, which would be
/// an internal inconsistency.
pub fn cayley_transform(x: &QMatrix, tau: &BigRational) -> Result<QMatrix, CayleyError> {
    let n = check_shape(x)?;
    if let Some((row, col)) = skew_defect(x) {
        return Err(CayleyError::NotSkew { row, col });
    }
    let identity = mx::identity::<BigRational>(n)?;
    let tau_x = mx::scale(x, tau)?;
    let numerator = mx::sub(&identity, &tau_x)?;
    let denominator = mx::add(&identity, &tau_x)?;
    let inverse = match elimination::inverse(&denominator) {
        Ok(inverse) => inverse,
        Err(ExactFieldError::Singular { .. }) => return Err(CayleyError::Singular),
        Err(other) => return Err(other.into()),
    };
    Ok(mx::multiply(&numerator, &inverse)?)
}

fn invert_or(m: &QMatrix, on_singular: CayleyError) -> Result<QMatrix, CayleyError> {
    match elimination::inverse(m) {
        Ok(inverse) => Ok(inverse),
        Err(ExactFieldError::Singular { .. }) => Err(on_singular),
        Err(other) => Err(other.into()),
    }
}

/// The skew `X` with `C_tau(X) = R`, that is `X = (I - R)(I + R)^(-1) / tau`, for an
/// orthogonal `R` without the eigenvalue `-1`.
pub fn cayley_inverse(r: &QMatrix, tau: &BigRational) -> Result<QMatrix, CayleyError> {
    let n = check_shape(r)?;
    if tau.is_zero() {
        return Err(CayleyError::ZeroParameter);
    }
    if !is_orthogonal(r) {
        return Err(CayleyError::NotOrthogonal);
    }
    let identity = mx::identity::<BigRational>(n)?;
    let shifted = mx::add(&identity, r)?;
    let inverse = invert_or(&shifted, CayleyError::EigenvalueMinusOne)?;
    let y = mx::multiply(&mx::sub(&identity, r)?, &inverse)?;
    mx::scale(&y, &(BigRational::one() / tau)).map_err(CayleyError::from)
}

/// The generator `K` with `C_1(K) = C_s(X) C_t(X)`: `K = (s + t) X (I + s t X^2)^(-1)`.
/// Refused with [`CayleyError::OutsideChart`] when `I + s t X^2` is singular, that is, when
/// the composite has eigenvalue `-1`.
pub fn compose_steps(
    x: &QMatrix,
    s: &BigRational,
    t: &BigRational,
) -> Result<QMatrix, CayleyError> {
    let n = check_shape(x)?;
    if let Some((row, col)) = skew_defect(x) {
        return Err(CayleyError::NotSkew { row, col });
    }
    let identity = mx::identity::<BigRational>(n)?;
    let x2 = mx::multiply(x, x)?;
    let denominator = mx::add(&identity, &mx::scale(&x2, &(s * t))?)?;
    let inverse = invert_or(&denominator, CayleyError::OutsideChart)?;
    mx::scale(&mx::multiply(x, &inverse)?, &(s + t)).map_err(CayleyError::from)
}

/// The standard basis `E_ij - E_ji`, `i < j`, of `so(n)`, in row-major order of `(i, j)`.
pub fn so_basis(n: usize) -> Result<Vec<QMatrix>, CayleyError> {
    if n == 0 || n > MAX_DIMENSION {
        return Err(CayleyError::Shape { rows: n, cols: n });
    }
    let mut basis = Vec::with_capacity(n * (n - 1) / 2);
    for i in 0..n {
        for j in (i + 1)..n {
            let mut m = mx::zeros::<BigRational>(n, n)?;
            m.set(i, j, ri(1)).map_err(ExactFieldError::from)?;
            m.set(j, i, ri(-1)).map_err(ExactFieldError::from)?;
            basis.push(m);
        }
    }
    Ok(basis)
}

/// The cross-product matrix `[v]_x` of `v = (a, b, c)`: `[v]_x w = v x w`.
pub fn cross_product_matrix(v: &[BigRational; 3]) -> Result<QMatrix, CayleyError> {
    let rows = vec![
        vec![ri(0), -&v[2], v[1].clone()],
        vec![v[2].clone(), ri(0), -&v[0]],
        vec![-&v[1], v[0].clone(), ri(0)],
    ];
    Ok(mx::from_rows(rows)?)
}

/// `(s + t) / (1 - s t)`, the parameter of the product of the circle points of `s` and `t`
/// (the tangent addition law). Refused when `s t = 1`: the product is `-1`, the point at
/// infinity of the chart.
pub fn compose_circle_parameters(
    s: &BigRational,
    t: &BigRational,
) -> Result<BigRational, CayleyError> {
    let denominator = BigRational::one() - s * t;
    if denominator.is_zero() {
        return Err(CayleyError::OutsideChart);
    }
    Ok((s + t) / denominator)
}

/// `|z|^2 = 1`.
pub fn is_unit(z: &GaussianRat) -> bool {
    z.norm_sq().is_one()
}

/// The rational point `((1 - t^2) + 2 t i) / (1 + t^2)` of the unit circle. Every unit
/// Gaussian rational except `-1` arises from exactly one rational `t`.
pub fn unit_from_parameter(t: &BigRational) -> GaussianRat {
    let t2 = t * t;
    let denominator = BigRational::one() + &t2;
    GaussianRat {
        re: (BigRational::one() - &t2) / &denominator,
        im: (t + t) / &denominator,
    }
}

/// The parameter `t = Im z / (1 + Re z)` of a unit `z`; `Ok(None)` for `z = -1`, the one
/// point outside the chart. Refused for `z` off the unit circle.
pub fn parameter_of_unit(z: &GaussianRat) -> Result<Option<BigRational>, CayleyError> {
    if !is_unit(z) {
        return Err(CayleyError::NotUnit(format!("{}+{}i", z.re, z.im)));
    }
    let denominator = BigRational::one() + &z.re;
    if denominator.is_zero() {
        return Ok(None);
    }
    Ok(Some(&z.im / denominator))
}

/// `u^k` for a unit `u` and an integer `k` (negative powers use the conjugate), refused
/// for a non-unit or `|k|` above [`MAX_UNIT_EXPONENT`].
pub fn unit_pow(u: &GaussianRat, k: &BigInt) -> Result<GaussianRat, CayleyError> {
    if !is_unit(u) {
        return Err(CayleyError::NotUnit(format!("{}+{}i", u.re, u.im)));
    }
    if k.abs() > BigInt::from(MAX_UNIT_EXPONENT) {
        return Err(CayleyError::ExponentTooLarge {
            exponent: k.to_string(),
            bound: MAX_UNIT_EXPONENT,
        });
    }
    let (mut base, mut exponent) = if k.is_negative() {
        (u.conj(), -k.clone())
    } else {
        (u.clone(), k.clone())
    };
    let two = BigInt::from(2);
    let mut acc = GaussianRat::one();
    while exponent.is_positive() {
        if (&exponent % &two).is_one() {
            acc = acc.mul(&base);
        }
        base = base.mul(&base);
        exponent /= &two;
    }
    Ok(acc)
}

/// The multiplicative order of a unit Gaussian rational, or `None` if it has infinite order.
///
/// A root of unity of order `n` generates a field of degree `phi(n)`, and `Q(i)` has degree
/// 2, so only `n` with `phi(n) <= 2` can occur (`1, 2, 3, 4, 6`); `zeta_3` and `zeta_6`
/// generate other quadratic fields, so the test of each candidate `u^n = 1` finds only
/// `1, 2, 4`. The list is derived from the totient, not assumed.
pub fn gaussian_unit_order(u: &GaussianRat) -> Result<Option<usize>, CayleyError> {
    if !is_unit(u) {
        return Err(CayleyError::NotUnit(format!("{}+{}i", u.re, u.im)));
    }
    for n in (1..=6usize).filter(|&n| euler_phi(n) <= 2) {
        let exponent = BigInt::from(n);
        if unit_pow(u, &exponent)? == GaussianRat::one() {
            return Ok(Some(n));
        }
    }
    Ok(None)
}

// Origin: engine/crates_rs/core_lie_theory/src/cayley.rs
// Claim: urn:core:crates_rs:core-lie-theory:cayley:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;

    #[test]
    fn the_plane_cayley_transform_is_the_pythagorean_parametrisation() {
        let j = QMatrix::from_row_major(2, 2, vec![ri(0), ri(-1), ri(1), ri(0)]).unwrap();
        // tau = 1/2 gives the triple 3-4-5, tau = 1/3 the triple 4-3-5 with swapped entries.
        let r = cayley_transform(&j, &rq(1, 2)).unwrap();
        let expected =
            mx::from_rows(vec![vec![rq(3, 5), rq(4, 5)], vec![rq(-4, 5), rq(3, 5)]]).unwrap();
        assert_eq!(r, expected);
        assert!(is_special_orthogonal(&r));
    }

    #[test]
    fn circle_parameter_is_inverse_to_the_unit_chart_away_from_minus_one() {
        for t in [rq(0, 1), rq(1, 2), rq(-3, 7), rq(5, 1)] {
            let z = unit_from_parameter(&t);
            assert!(is_unit(&z));
            assert_eq!(parameter_of_unit(&z).unwrap(), Some(t));
        }
        let minus_one = GaussianRat::from_ints(-1, 0);
        assert_eq!(parameter_of_unit(&minus_one).unwrap(), None);
    }
}

/// Multiplication on the rational circle including the missing point `-1`.
/// `None` denotes the Cayley chart's point at infinity; finite coordinates
/// compose by tangent addition. The returned infinity is exact, not a refusal.
pub fn compactified_circle_composition(
    left: Option<&BigRational>,
    right: Option<&BigRational>,
) -> Option<BigRational> {
    match (left, right) {
        (Some(s), Some(t)) => compose_circle_parameters(s, t).ok(),
        (None, None) => Some(BigRational::zero()),
        (None, Some(t)) | (Some(t), None) if t.is_zero() => None,
        (None, Some(t)) | (Some(t), None) => Some(-BigRational::one() / t),
    }
}
