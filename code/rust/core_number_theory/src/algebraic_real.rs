//! Exact real algebraic values, with canonical polynomial and quadratic carriers.
//!
//! Largest real roots of monic integer polynomials are recognized as rationals
//! or quadratic values when certified, otherwise retained as isolated roots.
//! Polynomial arithmetic and Sturm counts belong to `crate::polynomial`;
//! squarefree radical normalization belongs to `crate::quadratic`.
//! AuthorityEffect: None.
use crate::polynomial::{Polynomial, PolynomialError, SturmSequence};
use crate::quadratic::{QuadraticError, QuadraticNumber, Surd};
use crate::rational::Rational;
use num_bigint::BigInt;
use num_traits::{One, Signed, ToPrimitive, Zero};
use core_kernel::interval::Interval;
use std::fmt;
type Q = Rational;
pub const MAX_POLYNOMIAL_DEGREE: usize = 64;
pub const MAX_COEFFICIENT_BITS: u64 = 4096;
pub const MAX_REFINEMENT_STEPS: usize = 16384;
const MAX_QUADRATIC_CANDIDATES: usize = 8192;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AlgebraicRealError {
    #[error("algebraic root request: {0}")]
    Invalid(&'static str),
    #[error("{what} exceeds the exact algebraic root budget {limit}")]
    Budget { what: &'static str, limit: usize },
    #[error(transparent)]
    Polynomial(#[from] PolynomialError),
    #[error(transparent)]
    Quadratic(#[from] QuadraticError),
}
fn check_width(width: &Q) -> Result<(), AlgebraicRealError> {
    if !width.is_positive() {
        return Err(AlgebraicRealError::Invalid(
            "enclosure width must be positive",
        ));
    }
    if width.numer().bits() > MAX_REFINEMENT_STEPS as u64
        || width.denom().bits() > MAX_REFINEMENT_STEPS as u64
    {
        return Err(AlgebraicRealError::Budget {
            what: "enclosure width bits",
            limit: MAX_REFINEMENT_STEPS,
        });
    }
    Ok(())
}
/// A canonical squarefree integer polynomial with exactly one root in `(lower, upper]`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IsolatedRoot {
    polynomial: Vec<BigInt>,
    lower: Q,
    upper: Q,
}
impl IsolatedRoot {
    pub fn polynomial(&self) -> &[BigInt] {
        &self.polynomial
    }
    pub fn isolating_interval(&self) -> Result<Interval, AlgebraicRealError> {
        Interval::try_new(self.lower.clone(), self.upper.clone())
            .map_err(|_| AlgebraicRealError::Invalid("ordered isolating interval"))
    }
    pub fn enclosure(&self, width: &Q) -> Result<Interval, AlgebraicRealError> {
        check_width(width)?;
        let poly = Polynomial::from_coefficients(
            self.polynomial
                .iter()
                .cloned()
                .map(Q::from_integer)
                .collect(),
        );
        let chain = SturmSequence::new(&poly)?;
        let (lo, hi) = refine_interval(&chain, self.lower.clone(), self.upper.clone(), width)?;
        Interval::try_new(lo, hi).map_err(|_| AlgebraicRealError::Invalid("ordered enclosure"))
    }
}
/// A real algebraic number in the strongest form certified by the constructor.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RealAlgebraic {
    Rational(Q),
    Quadratic(QuadraticNumber),
    Root(IsolatedRoot),
}
impl RealAlgebraic {
    pub fn enclosure(&self, width: &Q) -> Result<Interval, AlgebraicRealError> {
        check_width(width)?;
        match self {
            Self::Rational(q) => Ok(Interval::point(q.clone())),
            Self::Quadratic(q) => Ok(q.enclosure(width)?),
            Self::Root(root) => root.enclosure(width),
        }
    }
    pub fn is_closed_form(&self) -> bool {
        !matches!(self, Self::Root(_))
    }
    pub fn as_rational(&self) -> Option<&Q> {
        match self {
            Self::Rational(q) => Some(q),
            _ => None,
        }
    }
    pub fn as_quadratic(&self) -> Option<&QuadraticNumber> {
        match self {
            Self::Quadratic(q) => Some(q),
            _ => None,
        }
    }
}
impl fmt::Display for RealAlgebraic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Rational(q) => write!(f, "{q}"),
            Self::Quadratic(q) => write!(f, "{q}"),
            Self::Root(root) => write!(
                f,
                "the root of {:?} in ({}, {}]",
                root.polynomial, root.lower, root.upper
            ),
        }
    }
}
fn refine_interval(
    chain: &SturmSequence,
    mut lo: Q,
    mut hi: Q,
    width: &Q,
) -> Result<(Q, Q), AlgebraicRealError> {
    let two = Q::from_integer(2.into());
    for _ in 0..MAX_REFINEMENT_STEPS {
        if &hi - &lo <= *width {
            return Ok((lo, hi));
        }
        let mid = (&lo + &hi) / &two;
        if chain.count_in(&mid, &hi)? >= 1 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    Err(AlgebraicRealError::Budget {
        what: "root refinement steps",
        limit: MAX_REFINEMENT_STEPS,
    })
}
/// Largest real root of a monic integer polynomial, in ascending coefficient order.
/// Invalid degree, coefficient growth and refinement work fail with typed errors.
fn validate_monic_input(monic: &[BigInt]) -> Result<(), AlgebraicRealError> {
    if monic.last() != Some(&BigInt::one()) || monic.len() < 2 {
        return Err(AlgebraicRealError::Invalid(
            "expected a monic integer polynomial of positive degree",
        ));
    }
    if monic.len() - 1 > MAX_POLYNOMIAL_DEGREE {
        return Err(AlgebraicRealError::Budget {
            what: "polynomial degree",
            limit: MAX_POLYNOMIAL_DEGREE,
        });
    }
    if monic.iter().any(|n| n.bits() > MAX_COEFFICIENT_BITS) {
        return Err(AlgebraicRealError::Budget {
            what: "polynomial coefficient bits",
            limit: MAX_COEFFICIENT_BITS as usize,
        });
    }
    Ok(())
}

fn isolate_largest_root(
    chain: &SturmSequence,
    mut lo: Q,
    mut hi: Q,
) -> Result<(Q, Q), AlgebraicRealError> {
    if chain.count_in(&lo, &hi)? == 0 {
        return Err(AlgebraicRealError::Invalid(
            "the polynomial has no real root",
        ));
    }
    let two = Q::from_integer(2.into());
    for _ in 0..MAX_REFINEMENT_STEPS {
        if chain.count_in(&lo, &hi)? == 1 {
            return Ok((lo, hi));
        }
        let mid = (&lo + &hi) / &two;
        if chain.count_in(&mid, &hi)? >= 1 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    Err(AlgebraicRealError::Budget {
        what: "largest root isolation",
        limit: MAX_REFINEMENT_STEPS,
    })
}

pub fn largest_real_root(monic: &[BigInt]) -> Result<RealAlgebraic, AlgebraicRealError> {
    validate_monic_input(monic)?;
    let poly = Polynomial::from_coefficients(monic.iter().cloned().map(Q::from_integer).collect());
    let squarefree = poly.squarefree_part();
    let chain = SturmSequence::new(&squarefree)?;
    let bound = crate::polynomial::real_root_bound(&squarefree).ok_or(
        AlgebraicRealError::Invalid("root bound of constant polynomial"),
    )?;
    let (lo, hi) = isolate_largest_root(&chain, -bound.clone(), bound.clone())?;
    let bound_ceiling = bound.ceil().to_integer();
    let target = Q::new(
        BigInt::one(),
        BigInt::from(8) * (&bound_ceiling + BigInt::one()),
    );
    let (refined_lo, refined_hi) = refine_interval(&chain, lo.clone(), hi.clone(), &target)?;
    let candidate = Q::from_integer(refined_hi.floor().to_integer());
    if candidate > refined_lo && squarefree.eval(&candidate).is_zero() {
        return Ok(RealAlgebraic::Rational(candidate));
    }
    if let Some(q) = find_quadratic_factor(&squarefree, &refined_lo, &refined_hi, &bound_ceiling)? {
        return Ok(RealAlgebraic::Quadratic(q));
    }
    Ok(RealAlgebraic::Root(IsolatedRoot {
        polynomial: squarefree.integer_coefficients().1,
        lower: lo,
        upper: hi,
    }))
}

fn quadratic_n_bounds(lo: &Q, hi: &Q, t: i64) -> Result<(BigInt, BigInt), AlgebraicRealError> {
    let two = Q::from_integer(2.into());
    let t_q = Q::from_integer(t.into());
    let mut values = vec![lo * (&t_q - lo), hi * (&t_q - hi)];
    let vertex = &t_q / &two;
    if *lo <= vertex && vertex <= *hi {
        values.push(&vertex * (&t_q - &vertex));
    }
    let low = values
        .iter()
        .min()
        .ok_or(AlgebraicRealError::Invalid("quadratic bounds"))?;
    let high = values
        .iter()
        .max()
        .ok_or(AlgebraicRealError::Invalid("quadratic bounds"))?;
    Ok((low.ceil().to_integer(), high.floor().to_integer()))
}

/// Bounded optional closed-form recognition. Exhaustion retains the already
/// certified isolated root; it does not guess a radical or refuse a valid root.
fn find_quadratic_factor(
    squarefree: &Polynomial<Q>,
    lo: &Q,
    hi: &Q,
    bound: &BigInt,
) -> Result<Option<QuadraticNumber>, AlgebraicRealError> {
    let Some(t_max) = (bound * BigInt::from(2)).to_i64() else {
        return Ok(None);
    };
    if t_max > MAX_QUADRATIC_CANDIDATES as i64 / 2 {
        return Ok(None);
    }
    let mut checked = 0usize;
    for t in -t_max..=t_max {
        let (mut n, end) = quadratic_n_bounds(lo, hi, t)?;
        while n <= end {
            if checked == MAX_QUADRATIC_CANDIDATES {
                return Ok(None);
            }
            checked += 1;
            if let Some(q) = try_quadratic(squarefree, lo, hi, t, &n)? {
                return Ok(Some(q));
            }
            n += BigInt::one();
        }
    }
    Ok(None)
}

fn quadratic_root_in_interval(lo: &Q, hi: &Q, t_int: &BigInt, discriminant: &BigInt) -> bool {
    let two = Q::from_integer(2.into());
    let t_q = Q::from_integer(t_int.clone());
    let low = &two * lo - &t_q;
    let high = &two * hi - &t_q;
    let d_q = Q::from_integer(discriminant.clone());
    (low.is_negative() || &low * &low < d_q) && !high.is_negative() && d_q <= &high * &high
}

fn try_quadratic(
    squarefree: &Polynomial<Q>,
    lo: &Q,
    hi: &Q,
    t: i64,
    n: &BigInt,
) -> Result<Option<QuadraticNumber>, AlgebraicRealError> {
    let t_int = BigInt::from(t);
    let discriminant = &t_int * &t_int - BigInt::from(4) * n;
    if !discriminant.is_positive() {
        return Ok(None);
    }
    let root = discriminant.sqrt();
    if &root * &root == discriminant {
        return Ok(None);
    }
    let quadratic = Polynomial::from_coefficients(vec![
        Q::from_integer(n.clone()),
        -Q::from_integer(t_int.clone()),
        Q::one(),
    ]);
    if !squarefree.rem(&quadratic)?.is_zero() || !quadratic_root_in_interval(lo, hi, &t_int, &discriminant) {
        return Ok(None);
    }
    let Ok(surd) = Surd::from_natural(Q::new(BigInt::one(), 2.into()), &discriminant) else {
        return Ok(None);
    };
    Ok(Some(QuadraticNumber::new(
        surd.radicand().clone(),
        Q::new(t_int, 2.into()),
        surd.coefficient().clone(),
    )?))
}

// Origin: engine/crates_rs/core_number_theory/src/algebraic_real.rs
// Claim: urn:core:crates_rs:core-number-theory:algebraic-real:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rational::rq;

    fn ints(values: &[i64]) -> Vec<BigInt> {
        values.iter().map(|&v| BigInt::from(v)).collect()
    }

    fn matrix(rows: &[&[i64]]) -> Vec<Vec<BigInt>> {
        rows.iter().map(|row| ints(row)).collect()
    }
    fn characteristic_polynomial(
        rows: &[Vec<BigInt>],
    ) -> Result<Vec<BigInt>, linear_algebra::exact_field::ExactFieldError> {
        let matrix = linear_algebra::exact_field::matrix::from_rows(
            rows.iter()
                .map(|r| r.iter().cloned().map(Q::from_integer).collect())
                .collect(),
        )?;
        Ok(
            linear_algebra::exact_field::characteristic_polynomial::characteristic_polynomial(
                &matrix,
            )?
            .into_iter()
            .map(|q| {
                assert!(
                    q.is_integer(),
                    "integer matrices have integer characteristic coefficients"
                );
                q.to_integer()
            })
            .collect(),
        )
    }

    #[test]
    fn characteristic_polynomial_matches_hand_computed_cases() {
        // [[0,1],[1,1]] has x^2 - x - 1.
        assert_eq!(
            characteristic_polynomial(&matrix(&[&[0, 1], &[1, 1]])).unwrap(),
            ints(&[-1, -1, 1])
        );
        // The Ising sigma fusion matrix has x^3 - 2x.
        assert_eq!(
            characteristic_polynomial(&matrix(&[&[0, 1, 0], &[1, 0, 1], &[0, 1, 0]])).unwrap(),
            ints(&[0, -2, 0, 1])
        );
        // Identity 3x3: (x - 1)^3 = x^3 - 3x^2 + 3x - 1.
        assert_eq!(
            characteristic_polynomial(&matrix(&[&[1, 0, 0], &[0, 1, 0], &[0, 0, 1]])).unwrap(),
            ints(&[-1, 3, -3, 1])
        );
        // A 1x1 matrix [7]: x - 7.
        assert_eq!(
            characteristic_polynomial(&matrix(&[&[7]])).unwrap(),
            ints(&[-7, 1])
        );
    }

    #[test]
    fn characteristic_polynomial_refuses_ragged_and_accepts_mathematical_empty_input() {
        assert_eq!(characteristic_polynomial(&[]).unwrap(), ints(&[1]));
        assert!(characteristic_polynomial(&matrix(&[&[1, 2], &[3]])).is_err());
    }

    #[test]
    fn integer_largest_roots_are_recognised() {
        // (x - 2)(x + 1)(x - 5) = x^3 - 6x^2 + 3x + 10.
        let root = largest_real_root(&ints(&[10, 3, -6, 1])).unwrap();
        assert_eq!(root, RealAlgebraic::Rational(rq(5, 1)));
        // x^2 - 4: the largest root is 2.
        assert_eq!(
            largest_real_root(&ints(&[-4, 0, 1])).unwrap(),
            RealAlgebraic::Rational(rq(2, 1))
        );
        // A repeated root: (x - 3)^2 (x + 1) = x^3 - 5x^2 + 3x + 9.
        assert_eq!(
            largest_real_root(&ints(&[9, 3, -5, 1])).unwrap(),
            RealAlgebraic::Rational(rq(3, 1))
        );
    }

    #[test]
    fn quadratic_largest_roots_are_exact_surds() {
        // Golden ratio: x^2 - x - 1 -> 1/2 + (1/2) sqrt(5).
        let phi = largest_real_root(&ints(&[-1, -1, 1])).unwrap();
        let surd = phi
            .as_quadratic()
            .expect("the golden ratio is a quadratic surd");
        assert_eq!(surd.rational_part(), &rq(1, 2));
        assert_eq!(surd.sqrt_part(), &rq(1, 2));
        assert_eq!(surd.radicand(), &BigInt::from(5));
        assert_eq!(surd.minimal_polynomial(), ints(&[-1, -1, 1]));
        // Ising sigma: x^3 - 2x -> sqrt(2) (non-radical factor x is irrelevant).
        let sigma = largest_real_root(&ints(&[0, -2, 0, 1])).unwrap();
        let surd = sigma.as_quadratic().unwrap();
        assert_eq!(surd.rational_part(), &rq(0, 1));
        assert_eq!(surd.sqrt_part(), &rq(1, 1));
        assert_eq!(surd.radicand(), &BigInt::from(2));
        // x^2 - 12 -> 2 sqrt(3): the square factor moves into the coefficient.
        let root = largest_real_root(&ints(&[-12, 0, 1])).unwrap();
        let surd = root.as_quadratic().unwrap();
        assert_eq!(surd.sqrt_part(), &rq(2, 1));
        assert_eq!(surd.radicand(), &BigInt::from(3));
        // Golden-ratio square: (x^2 - x - 1) shifted -> phi^2 = phi + 1 = 3/2 + sqrt(5)/2
        // has minimal polynomial x^2 - 3x + 1.
        let phi_squared = largest_real_root(&ints(&[1, -3, 1])).unwrap();
        let surd = phi_squared.as_quadratic().unwrap();
        assert_eq!(surd.rational_part(), &rq(3, 2));
        assert_eq!(surd.radicand(), &BigInt::from(5));
    }

    #[test]
    fn higher_degree_roots_are_isolated_not_guessed() {
        // x^3 - x - 1 (plastic number, irreducible cubic): not quadratic.
        let root = largest_real_root(&ints(&[-1, -1, 0, 1])).unwrap();
        let RealAlgebraic::Root(isolated) = &root else {
            panic!("the plastic number is not a rational or quadratic surd: {root:?}");
        };
        assert_eq!(isolated.polynomial(), ints(&[-1, -1, 0, 1]).as_slice());
        // It is about 1.3247: the enclosure brackets it tightly and exactly.
        let width = rq(1, 1_000_000);
        let enclosure = root.enclosure(&width).unwrap();
        assert!(enclosure.diam() <= width);
        let cube = |x: &Q| x * x * x - x - Q::one();
        assert!(cube(enclosure.lo()).is_negative());
        assert!(cube(enclosure.hi()).is_positive());
        assert!(enclosure.lo() > &rq(13247, 10_000));
        assert!(enclosure.hi() < &rq(13248, 10_000));
    }

    #[test]
    fn enclosures_of_closed_forms_are_certified() {
        let phi = largest_real_root(&ints(&[-1, -1, 1])).unwrap();
        let width = rq(1, 1_000_000_000);
        let enclosure = phi.enclosure(&width).unwrap();
        assert!(enclosure.diam() <= width);
        // phi^2 - phi - 1 changes sign across the enclosure.
        let f = |x: &Q| x * x - x - Q::one();
        assert!(f(enclosure.lo()).is_negative());
        assert!(f(enclosure.hi()).is_positive());
        assert!(enclosure.lo() > &rq(1_618_033_987, 1_000_000_000));
        assert!(enclosure.hi() < &rq(1_618_033_990, 1_000_000_000));
        // Rational values enclose to a point.
        let five = RealAlgebraic::Rational(rq(5, 1));
        assert_eq!(
            five.enclosure(&rq(1, 10)).unwrap(),
            Interval::point(rq(5, 1))
        );
    }

    #[test]
    fn malformed_polynomials_are_refused() {
        // Not monic.
        assert!(largest_real_root(&ints(&[1, 2])).is_err());
        // Constant.
        assert!(largest_real_root(&ints(&[1])).is_err());
        // No real root: x^2 + 1.
        assert!(largest_real_root(&ints(&[1, 0, 1])).is_err());
        assert!(RealAlgebraic::Rational(rq(1, 1))
            .enclosure(&rq(0, 1))
            .is_err());
    }

    #[test]
    fn oversized_root_and_enclosure_requests_refuse_before_refinement() {
        assert!(matches!(
            largest_real_root(&[BigInt::one() << 4097usize, BigInt::one()]),
            Err(AlgebraicRealError::Budget {
                what: "polynomial coefficient bits",
                ..
            })
        ));
        assert!(matches!(
            largest_real_root(&vec![BigInt::one(); 66]),
            Err(AlgebraicRealError::Budget {
                what: "polynomial degree",
                ..
            })
        ));
        let root = largest_real_root(&ints(&[-1, -1, 0, 1])).unwrap();
        let too_precise = Q::new(BigInt::one(), BigInt::one() << 16385usize);
        assert!(matches!(
            root.enclosure(&too_precise),
            Err(AlgebraicRealError::Budget { .. })
        ));
        if let RealAlgebraic::Root(isolated) = root {
            assert!(isolated.enclosure(&rq(0, 1)).is_err());
            assert!(isolated.enclosure(&rq(-1, 1)).is_err());
        }
    }
}
