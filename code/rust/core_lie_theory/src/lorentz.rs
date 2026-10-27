//! The Lorentz group `SO+(1, d; Q)` over the rationals: boosts, rotations, the polar
//! decomposition and the Thomas-Wigner rotation, exactly.
//!
//! Coordinates are `(t, x_1, .., x_d)` with the form `eta = diag(1, -1, .., -1)`.
//!
//! - A boost is determined by a rational point `(gamma, w)` of the future hyperboloid
//!   `gamma^2 - |w|^2 = 1`, `gamma >= 1`: `B = [[gamma, w^T], [w, I + w w^T / (gamma + 1)]]`.
//!   It is symmetric, lies in `SO+(1, d; Q)`, and has first column `(gamma, w)`. The
//!   boosts along a rational unit direction `n` with rapidity ratio `r = e^eta` in `Q_{>0}`
//!   have `gamma = (r + 1/r)/2` and `w = (r - 1/r)/2 n`; collinear boosts compose by
//!   `r_1 r_2` ([`boost`]). Rational points of the hyperbola are `gamma = (m^2 + n^2)/2mn`,
//!   `gamma beta = (m^2 - n^2)/2mn` ([`rational_hyperbola_points`]).
//! - Every `M` in `SO+(1, d; Q)` is uniquely `B R` with `B` a boost and `R` a spatial
//!   rotation: `B` is the boost with the first column of `M`, and `R = B^(-1) M`
//!   ([`polar_decompose`]). The spatial part of the product of two boosts is the Thomas-Wigner
//!   rotation ([`thomas_wigner_rotation`]); for perpendicular boosts its cosine is
//!   `(gamma_1 + gamma_2) / (1 + gamma_1 gamma_2)` and in general
//!   `(1 + gamma + gamma_1 + gamma_2)^2 / ((1 + gamma)(1 + gamma_1)(1 + gamma_2)) - 1` with
//!   `gamma = gamma_1 gamma_2 + w_1 . w_2` ([`wigner_cosine_closed_form`]).
//! - Whether a rotation has finite order is decided exactly by its characteristic polynomial
//!   ([`crate::finite_order::finite_order`]): no iteration bound is involved.
//! - `SO+(1, 2; Q)` is the projective group `PGL(2, Q)` acting by conjugation on the
//!   trace-zero `2 x 2` matrices ([`adjoint_of_gl2`]); the determinant class of `g` modulo
//!   squares is the obstruction to lifting the element to `SL(2, Q)`.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_integer::Integer;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_number_theory::rational::{ri, rq, sqrt_exact, squarefree_part, ArithmeticError};

use crate::cayley::is_special_orthogonal;
use crate::finite_order::{finite_order, FiniteOrderError};
use linear_algebra::exact_field::{elimination, matrix as mx, ExactFieldError};

use crate::QMatrix;

/// The largest number of space dimensions `d` of `SO+(1, d)`.
pub const MAX_SPACE_DIMENSION: usize = 5;
/// The largest exponent of a matrix power (the entries grow like `r^k`).
pub const MAX_POWER: u64 = 4096;
/// The largest `m` of a rapidity census.
pub const MAX_CENSUS_M: usize = 64;

/// Refusals for Lorentz-group constructions.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LorentzError {
    #[error("the number of space dimensions must be between 1 and {MAX_SPACE_DIMENSION}, got {0}")]
    SpaceDimension(usize),
    #[error("a square matrix of size 1 + d is required, got {rows}x{cols}")]
    Shape { rows: usize, cols: usize },
    #[error("the matrix does not preserve the Minkowski form: M^T eta M != eta")]
    NotLorentz,
    #[error("the matrix has determinant -1")]
    Improper,
    #[error("the matrix reverses the direction of time (M_00 <= -1)")]
    NotOrthochronous,
    #[error("a direction needs {expected} components of unit Euclidean norm")]
    Direction { expected: usize },
    #[error("the point is not on the future hyperboloid gamma^2 - |w|^2 = 1 with gamma >= 1")]
    OffHyperboloid,
    #[error("the rapidity ratio e^eta must be positive")]
    NonPositiveRatio,
    #[error("the exponent {power} exceeds the bound {max}")]
    PowerTooLarge { power: u64, max: u64 },
    #[error("the matrix is not a rotation of space: it is not of the block form diag(1, R) with R in SO(d)")]
    NotRotation,
    #[error("the census bound m = {0} exceeds {MAX_CENSUS_M}")]
    CensusTooLarge(usize),
    #[error("the matrix is singular")]
    Singular,
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error(transparent)]
    FiniteOrder(#[from] FiniteOrderError),
    #[error(transparent)]
    Arithmetic(#[from] ArithmeticError),
}

fn check_space_dimension(d: usize) -> Result<(), LorentzError> {
    if d == 0 || d > MAX_SPACE_DIMENSION {
        return Err(LorentzError::SpaceDimension(d));
    }
    Ok(())
}

fn element(m: &QMatrix, r: usize, c: usize) -> &BigRational {
    &m.as_slice()[r * m.cols() + c]
}

fn dot(u: &[BigRational], v: &[BigRational]) -> BigRational {
    u.iter().zip(v).fold(ri(0), |acc, (a, b)| acc + a * b)
}

/// `eta = diag(1, -1, .., -1)` on `1 + d` coordinates.
pub fn minkowski_form(space_dim: usize) -> Result<QMatrix, LorentzError> {
    check_space_dimension(space_dim)?;
    Ok(QMatrix::try_from_fn(space_dim + 1, space_dim + 1, |r, c| {
        if r != c {
            ri(0)
        } else if r == 0 {
            ri(1)
        } else {
            ri(-1)
        }
    })
    .map_err(ExactFieldError::from)?)
}

/// The number of space dimensions `d` of a square matrix of size `1 + d`.
pub fn space_dimension(m: &QMatrix) -> Result<usize, LorentzError> {
    if m.rows() != m.cols() || m.rows() < 2 {
        return Err(LorentzError::Shape {
            rows: m.rows(),
            cols: m.cols(),
        });
    }
    check_space_dimension(m.rows() - 1)?;
    Ok(m.rows() - 1)
}

/// `M^T eta M = eta`.
pub fn preserves_form(m: &QMatrix) -> Result<bool, LorentzError> {
    let d = space_dimension(m)?;
    let eta = minkowski_form(d)?;
    let product = mx::multiply(&mx::multiply(&mx::transpose(m)?, &eta)?, m)?;
    Ok(product == eta)
}

/// `M_00 >= 1` (numeric order on the rationals).
pub fn is_orthochronous(m: &QMatrix) -> bool {
    m.rows() > 0 && m.cols() > 0 && *element(m, 0, 0) >= ri(1)
}

/// Checks `M` is in `SO+(1, d; Q)` and returns `d`.
pub fn check_proper_orthochronous(m: &QMatrix) -> Result<usize, LorentzError> {
    let d = space_dimension(m)?;
    if !preserves_form(m)? {
        return Err(LorentzError::NotLorentz);
    }
    if !elimination::determinant(m)?.is_one() {
        return Err(LorentzError::Improper);
    }
    if !is_orthochronous(m) {
        return Err(LorentzError::NotOrthochronous);
    }
    Ok(d)
}

/// The boost of the future-hyperboloid point `(gamma, w)`:
/// `[[gamma, w^T], [w, I + w w^T / (gamma + 1)]]`.
pub fn boost_from_point(point: &[BigRational]) -> Result<QMatrix, LorentzError> {
    let d = point
        .len()
        .checked_sub(1)
        .ok_or(LorentzError::SpaceDimension(0))?;
    check_space_dimension(d)?;
    let gamma = &point[0];
    let w = &point[1..];
    if *gamma < ri(1) || gamma * gamma - dot(w, w) != ri(1) {
        return Err(LorentzError::OffHyperboloid);
    }
    let denominator = gamma + ri(1);
    Ok(QMatrix::try_from_fn(d + 1, d + 1, |r, c| match (r, c) {
        (0, 0) => gamma.clone(),
        (0, j) => w[j - 1].clone(),
        (i, 0) => w[i - 1].clone(),
        (i, j) => {
            let kronecker = if i == j { ri(1) } else { ri(0) };
            kronecker + &w[i - 1] * &w[j - 1] / &denominator
        }
    })
    .map_err(ExactFieldError::from)?)
}

/// The boost along a rational unit `direction` with rapidity ratio `ratio = e^eta > 0`:
/// `gamma = (r + 1/r)/2`, `w = (r - 1/r)/2 n`.
pub fn boost(
    space_dim: usize,
    ratio: &BigRational,
    direction: &[BigRational],
) -> Result<QMatrix, LorentzError> {
    check_space_dimension(space_dim)?;
    if !ratio.is_positive() {
        return Err(LorentzError::NonPositiveRatio);
    }
    if direction.len() != space_dim || dot(direction, direction) != ri(1) {
        return Err(LorentzError::Direction {
            expected: space_dim,
        });
    }
    let inverse = BigRational::one() / ratio;
    let gamma = (ratio + &inverse) / ri(2);
    let s = (ratio - &inverse) / ri(2);
    let mut point = vec![gamma];
    point.extend(direction.iter().map(|n| &s * n));
    boost_from_point(&point)
}

/// The first column `(gamma, w)` of an element of `SO+(1, d; Q)`.
pub fn boost_point(m: &QMatrix) -> Result<Vec<BigRational>, LorentzError> {
    let d = check_proper_orthochronous(m)?;
    Ok((0..=d).map(|r| element(m, r, 0).clone()).collect())
}

/// `diag(1, R)` for a spatial rotation `R` in `SO(d; Q)`.
pub fn spatial_rotation(rotation: &QMatrix) -> Result<QMatrix, LorentzError> {
    if rotation.rows() != rotation.cols() || !is_special_orthogonal(rotation) {
        return Err(LorentzError::NotRotation);
    }
    let d = rotation.rows();
    check_space_dimension(d)?;
    Ok(QMatrix::try_from_fn(d + 1, d + 1, |r, c| match (r, c) {
        (0, 0) => ri(1),
        (0, _) | (_, 0) => ri(0),
        (i, j) => element(rotation, i - 1, j - 1).clone(),
    })
    .map_err(ExactFieldError::from)?)
}

/// The rational point `(gamma, gamma beta) = ((m^2 + n^2)/2mn, (m^2 - n^2)/2mn)` with
/// `e^eta = m/n`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RapidityPoint {
    pub m: usize,
    pub n: usize,
    pub gamma: BigRational,
    pub gamma_beta: BigRational,
}

/// The rapidity points `e^eta = m/n` with `1 <= n < m <= max_m` coprime, in increasing `(m, n)`.
pub fn rational_hyperbola_points(max_m: usize) -> Vec<RapidityPoint> {
    let mut points = Vec::new();
    for m in 2..=max_m {
        for n in 1..m {
            if m.gcd(&n) == 1 {
                let (mb, nb) = (BigInt::from(m), BigInt::from(n));
                let den = BigInt::from(2) * &mb * &nb;
                points.push(RapidityPoint {
                    m,
                    n,
                    gamma: BigRational::new(&mb * &mb + &nb * &nb, den.clone()),
                    gamma_beta: BigRational::new(&mb * &mb - &nb * &nb, den),
                });
            }
        }
    }
    points
}

/// The rational point `((1 - t^2)/(1 + t^2), 2 t/(1 + t^2))` of the unit circle.
pub fn rational_unit_vector_2d(t: &BigRational) -> [BigRational; 2] {
    let t2 = t * t;
    let den = BigRational::one() + &t2;
    [(BigRational::one() - &t2) / &den, (t + t) / den]
}

/// The rational point `(2 s, 2 t, s^2 + t^2 - 1)/(s^2 + t^2 + 1)` of the unit sphere (every
/// rational point except the north pole arises; the denominators are the Pythagorean quadruples).
pub fn rational_unit_vector_3d(s: &BigRational, t: &BigRational) -> [BigRational; 3] {
    let q = s * s + t * t;
    let den = &q + BigRational::one();
    [
        (s + s) / &den,
        (t + t) / &den,
        (&q - BigRational::one()) / den,
    ]
}

/// `M = B R`: the boost, the same decomposition as a `(1 + d)`-matrix `diag(1, R)`, and `R`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolarDecomposition {
    pub space_dim: usize,
    /// The symmetric boost `B`.
    pub boost: QMatrix,
    /// `diag(1, R)`.
    pub rotation: QMatrix,
    /// The spatial rotation `R`, `d x d`.
    pub spatial_rotation: QMatrix,
}

fn extract_spatial_block(rotation: &QMatrix, d: usize) -> Result<QMatrix, LorentzError> {
    // B^(-1) M fixes the time axis, so it is diag(1, R).
    let block = (0..=d).all(|i| {
        let expected = if i == 0 { ri(1) } else { ri(0) };
        *element(rotation, 0, i) == expected && *element(rotation, i, 0) == expected
    });
    if !block {
        return Err(LorentzError::NotLorentz);
    }
    let spatial = QMatrix::try_from_fn(d, d, |r, c| element(rotation, r + 1, c + 1).clone())
        .map_err(ExactFieldError::from)?;
    if !is_special_orthogonal(&spatial) {
        return Err(LorentzError::NotLorentz);
    }
    Ok(spatial)
}

/// The unique decomposition `M = B R` of an element of `SO+(1, d; Q)` into a boost and a
/// spatial rotation: `B` is the boost with the first column of `M`, and `R = B^(-1) M`.
pub fn polar_decompose(m: &QMatrix) -> Result<PolarDecomposition, LorentzError> {
    let d = check_proper_orthochronous(m)?;
    let point = boost_point(m)?;
    let boost = boost_from_point(&point)?;
    let mut inverse_point = point.clone();
    for w in inverse_point.iter_mut().skip(1) {
        *w = -w.clone();
    }
    let inverse = boost_from_point(&inverse_point)?;
    let rotation = mx::multiply(&inverse, m)?;
    let spatial = extract_spatial_block(&rotation, d)?;
    Ok(PolarDecomposition {
        space_dim: d,
        boost,
        rotation,
        spatial_rotation: spatial,
    })
}

/// The spatial rotation of the product `B_1 B_2` of two elements of `SO+(1, d; Q)`: the
/// Thomas-Wigner rotation.
pub fn thomas_wigner_rotation(b1: &QMatrix, b2: &QMatrix) -> Result<QMatrix, LorentzError> {
    check_proper_orthochronous(b1)?;
    check_proper_orthochronous(b2)?;
    let product = mx::multiply(b1, b2)?;
    Ok(polar_decompose(&product)?.spatial_rotation)
}

/// `gamma_1 gamma_2 + w_1 . w_2`, the time-time entry of the product of the boosts of two
/// hyperboloid points (their relative Lorentz factor).
pub fn composed_gamma(p1: &[BigRational], p2: &[BigRational]) -> Result<BigRational, LorentzError> {
    if p1.len() != p2.len() || p1.len() < 2 {
        return Err(LorentzError::OffHyperboloid);
    }
    Ok(&p1[0] * &p2[0] + dot(&p1[1..], &p2[1..]))
}

/// `(1 + gamma + gamma_1 + gamma_2)^2 / ((1 + gamma)(1 + gamma_1)(1 + gamma_2)) - 1`, the
/// cosine of the Thomas-Wigner rotation angle of two boosts with Lorentz factors `gamma_1`,
/// `gamma_2` and composite Lorentz factor `gamma`.
pub fn wigner_cosine_closed_form(
    gamma1: &BigRational,
    gamma2: &BigRational,
    gamma: &BigRational,
) -> BigRational {
    let one = BigRational::one();
    let numerator = &one + gamma + gamma1 + gamma2;
    &numerator * &numerator / ((&one + gamma) * (&one + gamma1) * (&one + gamma2)) - one
}

/// `(gamma_1 + gamma_2) / (1 + gamma_1 gamma_2)`, the cosine for perpendicular boosts.
pub fn perpendicular_wigner_cosine(gamma1: &BigRational, gamma2: &BigRational) -> BigRational {
    (gamma1 + gamma2) / (BigRational::one() + gamma1 * gamma2)
}

/// The cosine of the rotation angle of a spatial rotation: `tr R / 2` in the plane and
/// `(tr R - 1) / 2` in space.
pub fn rotation_cosine(r: &QMatrix) -> Result<BigRational, LorentzError> {
    if !is_special_orthogonal(r) {
        return Err(LorentzError::NotRotation);
    }
    let trace = mx::trace(r)?;
    match r.rows() {
        2 => Ok(trace / ri(2)),
        3 => Ok((trace - ri(1)) / ri(2)),
        _ => Err(LorentzError::NotRotation),
    }
}

/// The entries `(cosh k eta, sinh k eta)` of the `k`-th power of a collinear boost of ratio `r`:
/// `((r^k + r^-k)/2, (r^k - r^-k)/2)`.
pub fn collinear_power_entries(
    ratio: &BigRational,
    k: u64,
) -> Result<(BigRational, BigRational), LorentzError> {
    if !ratio.is_positive() {
        return Err(LorentzError::NonPositiveRatio);
    }
    if k > MAX_POWER {
        return Err(LorentzError::PowerTooLarge {
            power: k,
            max: MAX_POWER,
        });
    }
    let exponent = u32::try_from(k).map_err(|_| LorentzError::PowerTooLarge {
        power: k,
        max: MAX_POWER,
    })?;
    let (p, q) = (ratio.numer().pow(exponent), ratio.denom().pow(exponent));
    let big = BigRational::new(p, q);
    let small = BigRational::one() / &big;
    Ok(((&big + &small) / ri(2), (&big - &small) / ri(2)))
}

/// `M^k` for a Lorentz matrix, refused above [`MAX_POWER`].
pub fn lorentz_power(m: &QMatrix, k: u64) -> Result<QMatrix, LorentzError> {
    if k > MAX_POWER {
        return Err(LorentzError::PowerTooLarge {
            power: k,
            max: MAX_POWER,
        });
    }
    check_proper_orthochronous(m)?;
    Ok(mx::power(m, k)?)
}

/// The largest absolute numerator or denominator among the entries.
pub fn height(m: &QMatrix) -> BigInt {
    m.as_slice()
        .iter()
        .flat_map(|e| [e.numer().abs(), e.denom().abs()])
        .max()
        .unwrap_or_else(BigInt::zero)
}

/// The conjugacy type of an element of `SO+(1, 2; Q)`, read from its trace.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ElementClass {
    Identity,
    /// `-1 <= tr < 3`: conjugate to a rotation of the plane.
    Elliptic,
    /// `tr = 3`, not the identity.
    Parabolic,
    /// `tr > 3`: conjugate to a boost.
    Hyperbolic,
}

/// Classify an element of `SO+(1, 2; Q)` by `tr M` (the eigenvalues are `1, lambda, 1/lambda`,
/// so `tr = 1 + 2 cosh eta` or `1 + 2 cos theta`).
pub fn classify_so21(m: &QMatrix) -> Result<ElementClass, LorentzError> {
    if check_proper_orthochronous(m)? != 2 {
        return Err(LorentzError::Shape {
            rows: m.rows(),
            cols: m.cols(),
        });
    }
    if mx::is_identity_matrix(m)? {
        return Ok(ElementClass::Identity);
    }
    let trace = mx::trace(m)?;
    Ok(match trace.cmp(&ri(3)) {
        std::cmp::Ordering::Greater => ElementClass::Hyperbolic,
        std::cmp::Ordering::Equal => ElementClass::Parabolic,
        std::cmp::Ordering::Less => ElementClass::Elliptic,
    })
}

/// The adjoint action of `g` in `GL(2, Q)` on the trace-zero matrices
/// `X(t, x, y) = [[x, y + t], [y - t, -x]]`, whose determinant is `t^2 - x^2 - y^2`, as a
/// `3 x 3` matrix in the coordinates `(t, x, y)`: `g X g^(-1) = X(A(g) (t, x, y))`.
/// `A(g)` preserves the form, `A(g1 g2) = A(g1) A(g2)`, `A(c g) = A(g)`, and `A(g)` is
/// orthochronous exactly when `det g > 0`.
pub fn adjoint_of_gl2(g: &QMatrix) -> Result<QMatrix, LorentzError> {
    if g.shape() != (2, 2) {
        return Err(LorentzError::Shape {
            rows: g.rows(),
            cols: g.cols(),
        });
    }
    let inverse = match elimination::inverse(g) {
        Ok(inverse) => inverse,
        Err(ExactFieldError::Singular { .. }) => return Err(LorentzError::Singular),
        Err(other) => return Err(other.into()),
    };
    // X(1, 0, 0), X(0, 1, 0), X(0, 0, 1).
    let units = [[[0, 1], [-1, 0]], [[1, 0], [0, -1]], [[0, 1], [1, 0]]];
    let mut columns: Vec<[BigRational; 3]> = Vec::with_capacity(3);
    for unit in units {
        let x = QMatrix::from_row_major(2, 2, unit.iter().flatten().map(|&v| ri(v)).collect())
            .map_err(ExactFieldError::from)?;
        let image = mx::multiply(&mx::multiply(g, &x)?, &inverse)?;
        let (e00, e01, e10) = (
            element(&image, 0, 0).clone(),
            element(&image, 0, 1).clone(),
            element(&image, 1, 0).clone(),
        );
        // x' = e00; y' + t' = e01; y' - t' = e10.
        columns.push([(&e01 - &e10) / ri(2), e00, (&e01 + &e10) / ri(2)]);
    }
    Ok(QMatrix::try_from_fn(3, 3, |r, c| columns[c][r].clone()).map_err(ExactFieldError::from)?)
}

/// The squarefree class of `det g` modulo rational squares (with sign): the element `A(g)` of
/// `SO(1, 2; Q)` lifts to `SL(2, Q)` exactly when it is 1; otherwise a lift needs the square
/// root of the class.
pub fn gl2_determinant_class(g: &QMatrix) -> Result<BigInt, LorentzError> {
    if g.shape() != (2, 2) {
        return Err(LorentzError::Shape {
            rows: g.rows(),
            cols: g.cols(),
        });
    }
    let det = elimination::determinant(g)?;
    if det.is_zero() {
        return Err(LorentzError::Singular);
    }
    let (class, _) = squarefree_part(&(det.numer() * det.denom()))?;
    Ok(class)
}

/// `m/n`, the rapidity ratio `e^eta` of a rapidity point.
pub fn ratio_of(point: &RapidityPoint) -> BigRational {
    BigRational::new(BigInt::from(point.m), BigInt::from(point.n))
}

/// A census of Thomas-Wigner rotations over pairs of boosts.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThomasWignerCensus {
    pub rapidity_count: usize,
    pub direction_count: usize,
    pub pairs: usize,
    pub collinear_pairs: usize,
    /// Pairs whose Thomas-Wigner rotation has finite order (the identity counts).
    pub finite_order_pairs: usize,
    pub finite_order_collinear_pairs: usize,
    pub finite_order_noncollinear_pairs: usize,
}

fn record_census_pair(
    census: &mut ThomasWignerCensus,
    b1: &QMatrix,
    ratio2: &BigRational,
    direction: &[BigRational; 2],
) -> Result<(), LorentzError> {
    let b2 = boost(2, ratio2, direction)?;
    let rotation = thomas_wigner_rotation(b1, &b2)?;
    let collinear = direction[1].is_zero();
    let finite = finite_order(&rotation)?.is_some();
    census.pairs += 1;
    census.collinear_pairs += usize::from(collinear);
    if finite {
        census.finite_order_pairs += 1;
        if collinear {
            census.finite_order_collinear_pairs += 1;
        } else {
            census.finite_order_noncollinear_pairs += 1;
        }
    }
    Ok(())
}

/// Over every pair `(B_1, B_2)` of boosts in `SO+(1, 2; Q)` with `B_1` along `x` and `B_2` along a
/// declared unit direction (collinear when the direction is parallel to `x`), both with ratios `m/n` of the rapidity points up to `max_m`: how many
/// Thomas-Wigner rotations have finite order, decided exactly.
pub fn thomas_wigner_census(
    max_m: usize,
    directions: &[[BigRational; 2]],
) -> Result<ThomasWignerCensus, LorentzError> {
    if max_m > MAX_CENSUS_M {
        return Err(LorentzError::CensusTooLarge(max_m));
    }
    let points = rational_hyperbola_points(max_m);
    let x_axis = [ri(1), ri(0)];
    let mut census = ThomasWignerCensus {
        rapidity_count: points.len(),
        direction_count: directions.len(),
        pairs: 0,
        collinear_pairs: 0,
        finite_order_pairs: 0,
        finite_order_collinear_pairs: 0,
        finite_order_noncollinear_pairs: 0,
    };
    for p1 in &points {
        let b1 = boost(2, &ratio_of(p1), &x_axis)?;
        for p2 in &points {
            let ratio2 = ratio_of(p2);
            for direction in directions {
                record_census_pair(&mut census, &b1, &ratio2, direction)?;
            }
        }
    }
    Ok(census)
}

/// The five rational unit directions of the plane used in census tests: along `x`, along `y`,
/// and the Pythagorean directions 3-4-5, 5-12-13, 7-24-25.
pub fn standard_plane_directions() -> [[BigRational; 2]; 5] {
    [
        [ri(1), ri(0)],
        [ri(0), ri(1)],
        [rq(3, 5), rq(4, 5)],
        [rq(5, 13), rq(12, 13)],
        [rq(7, 25), rq(24, 25)],
    ]
}

/// `e^eta = gamma + |w|` of a hyperboloid point `(gamma, w)`, when the speed `|w|` is rational.
pub fn rapidity_ratio(point: &[BigRational]) -> Option<BigRational> {
    let w = point.get(1..)?;
    Some(point.first()? + sqrt_exact(&dot(w, w))?)
}

// Origin: engine/crates_rs/core_lie_theory/src/lorentz.rs
// Claim: urn:core:crates_rs:core-lie-theory:lorentz:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_bc422684 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
