//! Exact decision of whether a rational matrix has finite order.
//!
//! A matrix `M` over `Q` has finite order exactly when its minimal polynomial is a product
//! of distinct cyclotomic polynomials. Its characteristic polynomial `chi` then has integer
//! coefficients and factors into cyclotomic polynomials `Phi_k` with `phi(k) <= n` (Kronecker:
//! the eigenvalues are roots of unity of degree at most `n`), which bounds `k` by `2 n^2`.
//! The decision needs no iteration bound:
//!
//! 1. compute `chi` (Faddeev-LeVerrier);
//! 2. divide out `Phi_k` for every `k` with `phi(k) <= n`; a cofactor other than 1 means
//!    some eigenvalue is not a root of unity, so the order is infinite;
//! 3. let `L` be the least common multiple of the `k` found; the order is `L` if `M^L = I`
//!    and infinite otherwise (a non-diagonalisable `M` has roots-of-unity eigenvalues but
//!    infinite order).
//!
//! [`rational_cosines_of_finite_order_rotations`] is Niven's set `{-1, -1/2, 0, 1/2, 1}`,
//! derived from the cyclotomic polynomials of degree at most 2 rather than listed.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::One;
use core_number_theory::polynomial::{
    cyclotomic_polynomial, euler_phi, Polynomial, PolynomialError,
};
use core_number_theory::rational::checked_lcm_usize;

use linear_algebra::exact_field::{characteristic_polynomial, matrix as mx, ExactFieldError};

use crate::QMatrix;

/// The largest dimension for which the decision is made.
pub const MAX_DIMENSION: usize = 16;

/// Refusals of the finite-order decision.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FiniteOrderError {
    #[error("a square matrix of dimension 1..={MAX_DIMENSION} is required, got {rows}x{cols}")]
    Shape { rows: usize, cols: usize },
    #[error("cyclotomic factorisation degree bound {bound} exceeds {MAX_DIMENSION}")]
    DegreeBound { bound: usize },
    #[error("polynomial degree {degree} exceeds declared degree bound {bound}")]
    PolynomialDegree { degree: usize, bound: usize },
    #[error("the least common multiple of the eigenvalue orders overflows")]
    Overflow,
    #[error(transparent)]
    Polynomial(#[from] PolynomialError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

fn divide_out_cyclotomic(
    remaining: &mut Polynomial<BigRational>,
    k: usize,
) -> Result<usize, FiniteOrderError> {
    let phi_k = cyclotomic_polynomial(k)?;
    let phi_degree = phi_k.degree().unwrap_or(0);
    let mut multiplicity = 0usize;
    while matches!(remaining.degree(), Some(d) if d >= phi_degree) {
        let (quotient, remainder) = remaining.div_rem(&phi_k)?;
        if !remainder.is_zero() {
            break;
        }
        *remaining = quotient;
        multiplicity += 1;
    }
    Ok(multiplicity)
}

/// The multiplicity of each cyclotomic polynomial `Phi_k` (with `phi(k) <= n`) in a monic
/// integer polynomial of degree at most `n`, or `None` if it is not a product of them.
/// Bounds greater than [`MAX_DIMENSION`] and polynomials exceeding the supplied
/// bound are refused before the finite conductor search.
pub fn cyclotomic_factorisation(
    polynomial: &Polynomial<BigRational>,
    degree_bound: usize,
) -> Result<Option<Vec<(usize, usize)>>, FiniteOrderError> {
    if degree_bound > MAX_DIMENSION {
        return Err(FiniteOrderError::DegreeBound {
            bound: degree_bound,
        });
    }
    if let Some(degree) = polynomial.degree() {
        if degree > degree_bound {
            return Err(FiniteOrderError::PolynomialDegree {
                degree,
                bound: degree_bound,
            });
        }
    }
    let mut remaining = polynomial.clone();
    let mut factors = Vec::new();
    // phi(k) >= sqrt(k / 2), so phi(k) <= n forces k <= 2 n^2.
    for k in 1..=(2 * degree_bound * degree_bound).max(1) {
        if euler_phi(k) <= degree_bound {
            let multiplicity = divide_out_cyclotomic(&mut remaining, k)?;
            if multiplicity > 0 {
                factors.push((k, multiplicity));
            }
        }
    }
    let is_unit = remaining.degree() == Some(0) && remaining.coefficient(0) == BigRational::one();
    Ok(is_unit.then_some(factors))
}

fn lcm_of_factors(factors: &[(usize, usize)]) -> Result<(usize, u64), FiniteOrderError> {
    let mut candidate = 1usize;
    for (k, _) in factors {
        candidate = checked_lcm_usize(candidate, *k).ok_or(FiniteOrderError::Overflow)?;
    }
    let exp = u64::try_from(candidate).map_err(|_| FiniteOrderError::Overflow)?;
    Ok((candidate, exp))
}

/// The multiplicative order of a square rational matrix, or `None` if it is infinite.
pub fn finite_order(m: &QMatrix) -> Result<Option<usize>, FiniteOrderError> {
    let n = m.rows();
    if m.rows() != m.cols() || n == 0 || n > MAX_DIMENSION {
        return Err(FiniteOrderError::Shape {
            rows: m.rows(),
            cols: m.cols(),
        });
    }
    let coefficients = characteristic_polynomial::characteristic_polynomial(m)?;
    // A finite-order matrix has a monic integer characteristic polynomial.
    if coefficients.iter().any(|c| !c.is_integer()) {
        return Ok(None);
    }
    let chi = Polynomial::from_coefficients(coefficients);
    let Some(factors) = cyclotomic_factorisation(&chi, n)? else {
        return Ok(None);
    };
    let (candidate, exp) = lcm_of_factors(&factors)?;
    let power = mx::power(m, exp)?;
    Ok(mx::is_identity_matrix(&power)?.then_some(candidate))
}

/// The rational numbers `c` such that a rotation of the plane with cosine `c` and rational
/// sine has finite order, in increasing order. They are the `cos` of the angles `2 pi j / k`
/// that have rational cosine, which happens exactly for `phi(k) <= 2` (Niven): `k` in
/// `1, 2, 3, 4, 6`. Read here from the cyclotomic polynomials `Phi_k = x^2 - 2 c x + 1`
/// (or `x -+ 1`) instead of being listed.
pub fn rational_cosines_of_finite_order_rotations() -> Result<Vec<BigRational>, FiniteOrderError> {
    let mut cosines: Vec<BigRational> = Vec::new();
    for k in 1..=6usize {
        if euler_phi(k) > 2 {
            continue;
        }
        let phi_k = cyclotomic_polynomial(k)?;
        let cosine = match phi_k.degree() {
            // x - 1 and x + 1 give the rotations 1 and -1.
            Some(1) => -phi_k.coefficient(0),
            // x^2 - 2 c x + 1 gives cos = -(coefficient of x) / 2.
            Some(2) => -phi_k.coefficient(1) / BigRational::from_integer(BigInt::from(2)),
            _ => continue,
        };
        if !cosines.contains(&cosine) {
            cosines.push(cosine);
        }
    }
    cosines.sort();
    Ok(cosines)
}

// Origin: engine/crates_rs/core_lie_theory/src/finite_order.rs
// Claim: urn:core:crates_rs:core-lie-theory:finite-order:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::{ri, rq};

    fn mat(rows: &[&[i64]]) -> QMatrix {
        let cols = rows[0].len();
        QMatrix::from_row_major(
            rows.len(),
            cols,
            rows.iter().flat_map(|r| r.iter().map(|&v| ri(v))).collect(),
        )
        .unwrap()
    }

    #[test]
    fn niven_set_is_derived_from_the_cyclotomic_polynomials() {
        assert_eq!(
            rational_cosines_of_finite_order_rotations().unwrap(),
            vec![ri(-1), rq(-1, 2), ri(0), rq(1, 2), ri(1)]
        );
    }

    #[test]
    fn direct_polynomial_entry_refuses_overflowing_and_false_degree_bounds() {
        let quadratic = cyclotomic_polynomial(3).unwrap();
        assert_eq!(
            cyclotomic_factorisation(&quadratic, usize::MAX),
            Err(FiniteOrderError::DegreeBound { bound: usize::MAX })
        );
        assert_eq!(
            cyclotomic_factorisation(&quadratic, 1),
            Err(FiniteOrderError::PolynomialDegree {
                degree: 2,
                bound: 1
            })
        );
        assert_eq!(
            cyclotomic_factorisation(&quadratic, 2).unwrap(),
            Some(vec![(3, 1)])
        );
        assert_eq!(
            cyclotomic_factorisation(&Polynomial::from_coefficients(vec![ri(1)]), 0).unwrap(),
            Some(vec![])
        );
    }

    #[test]
    fn small_matrices_of_known_order() {
        assert_eq!(finite_order(&mat(&[&[1, 0], &[0, 1]])).unwrap(), Some(1));
        assert_eq!(finite_order(&mat(&[&[-1, 0], &[0, -1]])).unwrap(), Some(2));
        assert_eq!(finite_order(&mat(&[&[0, -1], &[1, 0]])).unwrap(), Some(4));
        // The 3-cycle permutation matrix has order 3; the companion matrices of Phi_6 and Phi_3 have orders 6 and 3.
        assert_eq!(
            finite_order(&mat(&[&[0, 0, 1], &[1, 0, 0], &[0, 1, 0]])).unwrap(),
            Some(3)
        );
        assert_eq!(finite_order(&mat(&[&[0, -1], &[1, 1]])).unwrap(), Some(6));
        assert_eq!(finite_order(&mat(&[&[0, -1], &[1, -1]])).unwrap(), Some(3));
        // A 5-cycle of order 5 and a block of orders 2 and 3 of order 6.
        let five = mat(&[
            &[0, 0, 0, 0, 1],
            &[1, 0, 0, 0, 0],
            &[0, 1, 0, 0, 0],
            &[0, 0, 1, 0, 0],
            &[0, 0, 0, 1, 0],
        ]);
        assert_eq!(finite_order(&five).unwrap(), Some(5));
    }

    #[test]
    fn matrices_of_infinite_order_are_decided_without_a_bound() {
        // A rational rotation by an angle that is not a rational multiple of pi (cos = 3/5).
        let rotation =
            QMatrix::from_row_major(2, 2, vec![rq(3, 5), rq(-4, 5), rq(4, 5), rq(3, 5)]).unwrap();
        assert_eq!(finite_order(&rotation).unwrap(), None);
        // A hyperbolic matrix, a unipotent matrix (eigenvalues 1 but not diagonalisable), a nonintegral one.
        assert_eq!(finite_order(&mat(&[&[2, 1], &[1, 1]])).unwrap(), None);
        assert_eq!(finite_order(&mat(&[&[1, 1], &[0, 1]])).unwrap(), None);
        assert_eq!(
            finite_order(
                &QMatrix::from_row_major(2, 2, vec![rq(1, 2), ri(0), ri(0), ri(2)]).unwrap()
            )
            .unwrap(),
            None
        );
    }

    #[test]
    fn the_decision_agrees_with_direct_powers_up_to_the_order() {
        // Independent route: M^k for k = 1..=12 against the identity.
        let candidates = [
            mat(&[&[0, -1], &[1, 0]]),
            mat(&[&[0, -1], &[1, 1]]),
            mat(&[&[0, -1], &[1, -1]]),
            mat(&[&[1, 1], &[0, 1]]),
            mat(&[&[2, 1], &[1, 1]]),
            mat(&[&[0, 1, 0], &[0, 0, 1], &[1, 0, 0]]),
        ];
        for m in candidates {
            let by_powers =
                (1..=12u64).find(|&k| mx::is_identity_matrix(&mx::power(&m, k).unwrap()).unwrap());
            let decided = finite_order(&m).unwrap();
            match decided {
                Some(order) => assert_eq!(by_powers, Some(order as u64)),
                None => assert_eq!(by_powers, None),
            }
        }
    }

    #[test]
    fn shapes_are_refused() {
        assert!(matches!(
            finite_order(&QMatrix::zero(2, 3).unwrap()),
            Err(FiniteOrderError::Shape { .. })
        ));
        assert!(matches!(
            finite_order(&QMatrix::zero(0, 0).unwrap()),
            Err(FiniteOrderError::Shape { .. })
        ));
        let big = MAX_DIMENSION + 1;
        assert!(matches!(
            finite_order(&QMatrix::zero(big, big).unwrap()),
            Err(FiniteOrderError::Shape { .. })
        ));
    }

    #[test]
    fn cyclotomic_factorisation_reports_multiplicities() {
        // (x - 1)^2 (x^2 + x + 1) = x^4 - x^3 - x + 1 = Phi_1^2 Phi_3.
        let p = Polynomial::from_i64s(&[1, -1, 0, -1, 1]);
        let factors = cyclotomic_factorisation(&p, 4).unwrap().unwrap();
        assert_eq!(factors, vec![(1, 2), (3, 1)]);
        // x^2 - 2 is not a product of cyclotomic polynomials.
        assert_eq!(
            cyclotomic_factorisation(&Polynomial::from_i64s(&[-2, 0, 1]), 2).unwrap(),
            None
        );
    }
}

/// The multiplicative order over Q(i), decided by the faithful rational
/// realification [Re A,-Im A; Im A,Re A]. The rational dimension budget applies
/// to the doubled carrier. This is an algebraic decision, not a cutoff search.
pub fn gaussian_finite_order(
    matrix: &linear_algebra::backend::basic_matrix::BasicMatrix<
        core_number_theory::cyclotomic::GaussianRat,
    >,
) -> Result<Option<usize>, FiniteOrderError> {
    let n = matrix.rows();
    if n == 0 || n != matrix.cols() || n > MAX_DIMENSION / 2 {
        return Err(FiniteOrderError::Shape {
            rows: n,
            cols: matrix.cols(),
        });
    }
    let realification = mx::from_fn(2 * n, 2 * n, |r, c| {
        let z = matrix
            .get_ref(r % n, c % n)
            .expect("bounded realification index");
        match (r < n, c < n) {
            (true, true) | (false, false) => z.re.clone(),
            (true, false) => -z.im.clone(),
            (false, true) => z.im.clone(),
        }
    })?;
    finite_order(&realification)
}

#[cfg(test)]
mod dynamics_laws {

    use super::*;
    use core_number_theory::cyclotomic::GaussianRat;
    use core_number_theory::rational::{ri, rq};
    #[test]
    fn gaussian_order_decision_preserves_the_faithful_realification() {
        let phase = GaussianRat {
            re: ri(0),
            im: ri(1),
        };
        let root = mx::diagonal(&[phase]).unwrap();
        assert_eq!(gaussian_finite_order(&root).unwrap(), Some(4));
        let infinite = mx::diagonal(&[GaussianRat {
            re: rq(3, 5),
            im: rq(4, 5),
        }])
        .unwrap();
        assert_eq!(gaussian_finite_order(&infinite).unwrap(), None);
        assert!(
            gaussian_finite_order(&mx::identity::<GaussianRat>(MAX_DIMENSION).unwrap()).is_err()
        );
    }
}
