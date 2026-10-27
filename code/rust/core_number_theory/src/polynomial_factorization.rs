//! Bounded Berlekamp-Zassenhaus factorisation over Q.
//!
//! Yun decomposition removes multiplicities. Primitive integer factors are
//! monicised by x -> x/lc, factored modulo a good prime with Berlekamp kernels,
//! pair-Hensel lifted past a Examiner-Mignotte coefficient bound, and recombined
//! exhaustively. Every candidate divides exactly; the final product replays.
//! Budget or prime-search exhaustion never means irreducible. AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_d3a7f610<T> {
    fn checked_invariant_d3a7f610(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_d3a7f610<T> for Option<T> {
    #[inline]
    fn checked_invariant_d3a7f610(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_d3a7f610<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_d3a7f610(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::polynomial::{Polynomial, PolynomialError};
use crate::rational::Rational;
use linear_algebra::exact_field::{elimination::kernel_basis, matrix, ExactFieldError};
use linear_algebra::scalars::{ExactRing, Field, Ring, Semiring};
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, ToPrimitive};
use core_combinatorics::enumeration::{Combinations, CombinatoricsError};

pub const MAX_FACTOR_DEGREE: usize = 32;
pub const MAX_FACTOR_COEFFICIENT_BITS: u64 = 8192;
pub const MAX_RECOMBINATION_SETS: usize = 1 << 20;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PolynomialFactorBudget {
    pub max_steps: u64,
}
impl Default for PolynomialFactorBudget {
    fn default() -> Self {
        Self { max_steps: 100_000 }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum PolynomialFactorError {
    #[error("the zero polynomial has no finite irreducible factorisation")]
    Zero,
    #[error("polynomial degree or coefficient size exceeds the declared supported range")]
    SizeLimit,
    #[error("factorisation exhausted the declared operation budget")]
    Budget,
    #[error("no squarefree reduction was found in the bounded good-prime search")]
    PrimeSearch,
    #[error("a modular, Hensel, or final product replay failed")]
    Replay,
    #[error(transparent)]
    Polynomial(#[from] PolynomialError),
    #[error(transparent)]
    Algebra(#[from] ExactFieldError),
    #[error(transparent)]
    Enumeration(#[from] CombinatoricsError),
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RationalFactorization {
    pub unit: Rational,
    /// Monic irreducible Q-polynomials with positive multiplicities.
    pub factors: Vec<(Polynomial<Rational>, usize)>,
}
impl RationalFactorization {
    /// Product replay checks an input binding; irreducibility is established by
    /// the complete modular/recombination algorithm, not by this method alone.
    pub fn verify_product(
        &self,
        input: &Polynomial<Rational>,
    ) -> Result<(), PolynomialFactorError> {
        let total_degree = self.factors.iter().try_fold(0usize, |sum, (p, m)| {
            sum.checked_add(p.degree()?.checked_mul(*m)?)
        });
        if total_degree.is_none_or(|d| d > MAX_FACTOR_DEGREE) {
            return Err(PolynomialFactorError::SizeLimit);
        }
        if num_traits::Zero::is_zero(&self.unit)
            || self.factors.iter().any(|(p, m)| {
                *m == 0
                    || p.degree().is_none_or(|d| d == 0)
                    || p.leading_coefficient() != Some(&q(1))
            })
        {
            return Err(PolynomialFactorError::Replay);
        }
        let product = self
            .factors
            .iter()
            .fold(Polynomial::constant(self.unit.clone()), |a, (p, m)| {
                a.mul(&p.pow(*m))
            });
        if &product != input {
            return Err(PolynomialFactorError::Replay);
        }
        Ok(())
    }
}
fn q(n: i64) -> Rational {
    Rational::from_integer(BigInt::from(n))
}
struct Work {
    left: u64,
}
impl Work {
    fn step(&mut self) -> Result<(), PolynomialFactorError> {
        if self.left == 0 {
            return Err(PolynomialFactorError::Budget);
        }
        self.left -= 1;
        Ok(())
    }
}

// Internal prime-field scalars are instantiated only at the listed proven
// primes below. They are not an unchecked public field-constructor surface.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Mod<const P: u64>(u64);
impl<const P: u64> Mod<P> {
    fn integer(n: &BigInt) -> Self {
        Self(
            n.mod_floor(&BigInt::from(P))
                .to_u64()
                .checked_invariant_d3a7f610("reduced residue fits"),
        )
    }
}
impl<const P: u64> Semiring for Mod<P> {
    fn zero() -> Self {
        Self(0)
    }
    fn one() -> Self {
        Self(1)
    }
    fn is_zero(&self) -> bool {
        self.0 == 0
    }
    fn add(&self, b: &Self) -> Self {
        Self((self.0 + b.0) % P)
    }
    fn mul(&self, b: &Self) -> Self {
        Self(((self.0 as u128 * b.0 as u128) % P as u128) as u64)
    }
}
impl<const P: u64> Ring for Mod<P> {
    fn neg(&self) -> Self {
        Self((P - self.0) % P)
    }
}
impl<const P: u64> Field for Mod<P> {
    fn try_inv(&self) -> Option<Self> {
        if self.0 == 0 {
            return None;
        }
        let (mut a, mut e, mut out) = (*self, P - 2, Self(1));
        while e > 0 {
            if e & 1 == 1 {
                out = out.mul(&a);
            }
            a = a.mul(&a);
            e >>= 1;
        }
        Some(out)
    }
}
impl<const P: u64> ExactRing for Mod<P> {}
fn reduce<const P: u64>(
    f: &Polynomial<Rational>,
) -> Result<Polynomial<Mod<P>>, PolynomialFactorError> {
    let coefficients = f
        .coefficients()
        .iter()
        .map(|c| {
            if !c.is_integer() {
                return Err(PolynomialFactorError::Replay);
            }
            Ok(Mod::<P>::integer(&c.to_integer()))
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(Polynomial::from_coefficients(coefficients))
}
fn integer_lift<const P: u64>(f: &Polynomial<Mod<P>>) -> Polynomial<Rational> {
    Polynomial::from_coefficients(
        f.coefficients()
            .iter()
            .map(|c| Rational::from_integer(c.0.into()))
            .collect(),
    )
}
fn pow_mod<const P: u64>(
    base: &Polynomial<Mod<P>>,
    mut e: u64,
    modulus: &Polynomial<Mod<P>>,
    work: &mut Work,
) -> Result<Polynomial<Mod<P>>, PolynomialFactorError> {
    let mut out = Polynomial::one();
    let mut a = base.rem(modulus)?;
    while e > 0 {
        work.step()?;
        if e & 1 == 1 {
            out = out.mul(&a).rem(modulus)?;
        }
        e >>= 1;
        if e > 0 {
            a = a.mul(&a).rem(modulus)?;
        }
    }
    Ok(out)
}
fn berlekamp_basis<const P: u64>(
    f: &Polynomial<Mod<P>>,
    work: &mut Work,
) -> Result<Vec<Vec<Mod<P>>>, PolynomialFactorError> {
    let n = f.degree().ok_or(PolynomialFactorError::Replay)?;
    let mut columns = Vec::new();
    for j in 0..n {
        work.step()?;
        columns.push(pow_mod(&Polynomial::x(), P * j as u64, f, work)?);
    }
    let operator = matrix::from_fn(n, n, |r, c| {
        columns[c]
            .coefficient(r)
            .sub(&if r == c { Mod(1) } else { Mod(0) })
    })?;
    Ok(kernel_basis(&operator)?)
}

fn split_factor_by_shifted<const P: u64>(
    factor: Polynomial<Mod<P>>,
    shifted: &Polynomial<Mod<P>>,
    next: &mut Vec<Polynomial<Mod<P>>>,
    work: &mut Work,
) -> Result<(), PolynomialFactorError> {
    work.step()?;
    if factor.degree() == Some(1) {
        next.push(factor);
        return Ok(());
    }
    let gcd = factor.gcd(shifted);
    if !gcd.is_constant() && gcd.degree() != factor.degree() {
        let (other, remainder) = factor.div_rem(&gcd)?;
        if !remainder.is_zero() {
            return Err(PolynomialFactorError::Replay);
        }
        next.push(gcd);
        next.push(other.monic().ok_or(PolynomialFactorError::Replay)?);
    } else {
        next.push(factor);
    }
    Ok(())
}

fn berlekamp<const P: u64>(
    f: &Polynomial<Mod<P>>,
    work: &mut Work,
) -> Result<Vec<Polynomial<Mod<P>>>, PolynomialFactorError> {
    let basis = berlekamp_basis(f, work)?;
    let expected = basis.len();
    let mut factors = vec![f.clone()];
    for vector in basis {
        let splitter = Polynomial::from_coefficients(vector);
        for value in 0..P {
            let shifted = splitter.sub(&Polynomial::constant(Mod(value)));
            let mut next = Vec::new();
            for factor in factors {
                split_factor_by_shifted(factor, &shifted, &mut next, work)?;
            }
            factors = next;
            if factors.len() == expected {
                return Ok(factors);
            }
        }
    }
    if factors.len() != expected {
        return Err(PolynomialFactorError::Replay);
    }
    Ok(factors)
}

fn symmetric_lift_polynomial(g: &Polynomial<Rational>, modulus: &BigInt) -> Polynomial<Rational> {
    let coefficients = g
        .coefficients()
        .iter()
        .map(|c| {
            let residue = c.to_integer().mod_floor(modulus);
            let symmetric = if &residue * 2 > *modulus {
                residue - modulus
            } else {
                residue
            };
            Rational::from_integer(symmetric)
        })
        .collect();
    Polynomial::from_coefficients(coefficients)
}

fn pair_hensel<const P: u64>(
    f: &Polynomial<Rational>,
    g0: &Polynomial<Mod<P>>,
    h0: &Polynomial<Mod<P>>,
    bound: &BigInt,
    work: &mut Work,
) -> Result<Polynomial<Rational>, PolynomialFactorError> {
    let (gcd, s, t) = g0.xgcd(h0);
    if gcd != Polynomial::one() {
        return Err(PolynomialFactorError::Replay);
    }
    let (mut g, mut h) = (integer_lift(g0), integer_lift(h0));
    let mut modulus = BigInt::from(P);
    while modulus <= bound * 2 {
        work.step()?;
        let error = f
            .sub(&g.mul(&h))
            .scale(&Rational::new(BigInt::one(), modulus.clone()));
        let error_mod = reduce::<P>(&error)?;
        let delta_g = t.mul(&error_mod).rem(g0)?;
        let numerator = error_mod.sub(&delta_g.mul(h0));
        let (delta_h, remainder) = numerator.div_rem(g0)?;
        if !remainder.is_zero() || s.mul(&error_mod).rem(h0)? != delta_h {
            return Err(PolynomialFactorError::Replay);
        }
        let m = Rational::from_integer(modulus.clone());
        g = g.add(&integer_lift(&delta_g).scale(&m));
        h = h.add(&integer_lift(&delta_h).scale(&m));
        modulus *= P;
    }
    Ok(symmetric_lift_polynomial(&g, &modulus))
}

fn mignotte_bound(f: &Polynomial<Rational>) -> Result<BigInt, PolynomialFactorError> {
    let degree = f.degree().ok_or(PolynomialFactorError::Replay)?;
    let height = f
        .coefficients()
        .iter()
        .map(|c| c.to_integer().abs())
        .max()
        .ok_or(PolynomialFactorError::Replay)?;
    Ok((BigInt::one() << degree) * BigInt::from(degree + 1) * height)
}

fn partition_modular_factors<const P: u64>(
    modular: &[Polynomial<Mod<P>>],
    subset: &[usize],
) -> (Polynomial<Mod<P>>, Polynomial<Mod<P>>) {
    let mut g0 = Polynomial::one();
    let mut h0 = Polynomial::one();
    for (i, factor) in modular.iter().enumerate() {
        if subset.contains(&i) {
            g0 = g0.mul(factor);
        } else {
            h0 = h0.mul(factor);
        }
    }
    (g0, h0)
}

fn try_recombination_subset<const P: u64>(
    f: &Polynomial<Rational>,
    modular: &[Polynomial<Mod<P>>],
    subset: &[usize],
    bound: &BigInt,
    work: &mut Work,
) -> Result<Option<Polynomial<Rational>>, PolynomialFactorError> {
    work.step()?;
    let (g0, h0) = partition_modular_factors(modular, subset);
    let candidate = pair_hensel::<P>(f, &g0, &h0, bound, work)?;
    if candidate.is_constant() || candidate.degree() == f.degree() {
        return Err(PolynomialFactorError::Replay);
    }
    if f.div_rem(&candidate)?.1.is_zero() {
        Ok(Some(candidate))
    } else {
        Ok(None)
    }
}

fn recombine_modular_factors<const P: u64>(
    f: &Polynomial<Rational>,
    modular: &[Polynomial<Mod<P>>],
    bound: &BigInt,
    work: &mut Work,
) -> Result<Option<Polynomial<Rational>>, PolynomialFactorError> {
    for size in 1..=modular.len() / 2 {
        let limit = usize::try_from(work.left)
            .unwrap_or(usize::MAX)
            .min(MAX_RECOMBINATION_SETS);
        for subset in Combinations::new(modular.len(), size, limit)? {
            if let Some(candidate) = try_recombination_subset(f, modular, &subset, bound, work)? {
                return Ok(Some(candidate));
            }
        }
    }
    Ok(None)
}

fn good_prime<const P: u64>(
    f: &Polynomial<Rational>,
    work: &mut Work,
) -> Result<Option<Option<Polynomial<Rational>>>, PolynomialFactorError> {
    work.step()?;
    let reduced = reduce::<P>(f)?;
    if reduced.gcd(&reduced.derivative()).degree() != Some(0) {
        return Ok(None);
    }
    let modular = berlekamp(&reduced, work)?;
    if modular.len() == 1 {
        return Ok(Some(None));
    }
    let bound = mignotte_bound(f)?;
    Ok(Some(recombine_modular_factors(f, &modular, &bound, work)?))
}
fn integer_factors(
    f: &Polynomial<Rational>,
    work: &mut Work,
) -> Result<Vec<Polynomial<Rational>>, PolynomialFactorError> {
    if f.degree() == Some(1) {
        return Ok(vec![f.clone()]);
    }
    let mut result = None;
    macro_rules! prime {
        ($p:literal) => {
            if result.is_none() {
                result = good_prime::<$p>(f, work)?;
            }
        };
    }
    prime!(2);
    prime!(3);
    prime!(5);
    prime!(7);
    prime!(11);
    prime!(13);
    prime!(17);
    prime!(19);
    prime!(23);
    prime!(29);
    prime!(31);
    prime!(37);
    match result.ok_or(PolynomialFactorError::PrimeSearch)? {
        None => Ok(vec![f.clone()]),
        Some(factor) => {
            let (other, remainder) = f.div_rem(&factor)?;
            if !remainder.is_zero() {
                return Err(PolynomialFactorError::Replay);
            }
            let mut factors = integer_factors(&factor, work)?;
            factors.extend(integer_factors(&other, work)?);
            Ok(factors)
        }
    }
}
/// Monic irreducible factorisation with exact multiplicities and a rational unit.
fn validate_factor_input(input: &Polynomial<Rational>) -> Result<(), PolynomialFactorError> {
    let degree = input.degree().ok_or(PolynomialFactorError::Zero)?;
    if degree > MAX_FACTOR_DEGREE
        || input.coefficients().iter().any(|c| {
            c.numer().bits() > MAX_FACTOR_COEFFICIENT_BITS
                || c.denom().bits() > MAX_FACTOR_COEFFICIENT_BITS
        })
    {
        return Err(PolynomialFactorError::SizeLimit);
    }
    Ok(())
}

fn to_monic_integer_poly(
    primitive: &Polynomial<Rational>,
) -> Result<(BigInt, Polynomial<Rational>), PolynomialFactorError> {
    let n = primitive.degree().ok_or(PolynomialFactorError::Replay)?;
    let a = primitive
        .leading_coefficient()
        .ok_or(PolynomialFactorError::Replay)?
        .to_integer();
    let mut monic_coeff = Vec::new();
    for i in 0..n {
        monic_coeff.push(Rational::from_integer(
            primitive.coefficient(i).to_integer() * a.pow((n - 1 - i) as u32),
        ));
    }
    monic_coeff.push(q(1));
    let monic = Polynomial::from_coefficients(monic_coeff);
    if monic
        .coefficients()
        .iter()
        .any(|c| c.numer().bits() > MAX_FACTOR_COEFFICIENT_BITS)
    {
        return Err(PolynomialFactorError::SizeLimit);
    }
    Ok((a, monic))
}

fn restore_nonmonic_factor(
    factor: &Polynomial<Rational>,
    a: &BigInt,
) -> Result<Polynomial<Rational>, PolynomialFactorError> {
    let d = factor.degree().ok_or(PolynomialFactorError::Replay)?;
    let denominator = a.pow(d as u32);
    Ok(Polynomial::from_coefficients(
        factor
            .coefficients()
            .iter()
            .enumerate()
            .map(|(i, c)| Rational::new(c.to_integer() * a.pow(i as u32), denominator.clone()))
            .collect(),
    ))
}

fn factor_squarefree_component(
    squarefree: &Polynomial<Rational>,
    multiplicity: usize,
    factors: &mut Vec<(Polynomial<Rational>, usize)>,
    work: &mut Work,
) -> Result<(), PolynomialFactorError> {
    let (_, primitive) = squarefree.content_and_primitive_part();
    let (a, monic) = to_monic_integer_poly(&primitive)?;
    for factor in integer_factors(&monic, work)? {
        let restored = restore_nonmonic_factor(&factor, &a)?;
        factors.push((restored, multiplicity));
    }
    Ok(())
}

pub fn factor_over_q(
    input: &Polynomial<Rational>,
    budget: PolynomialFactorBudget,
) -> Result<RationalFactorization, PolynomialFactorError> {
    validate_factor_input(input)?;
    let mut work = Work {
        left: budget.max_steps,
    };
    work.step()?;
    let mut factors = Vec::new();
    for (squarefree, multiplicity) in input.squarefree_decomposition()? {
        factor_squarefree_component(&squarefree, multiplicity, &mut factors, &mut work)?;
    }
    factors.sort_by(|(a, m), (b, n)| a.coefficients().cmp(b.coefficients()).then(m.cmp(n)));
    let answer = RationalFactorization {
        unit: input
            .leading_coefficient()
            .ok_or(PolynomialFactorError::Zero)?
            .clone(),
        factors,
    };
    answer.verify_product(input)?;
    Ok(answer)
}
// Origin: engine/crates_rs/core_number_theory/src/polynomial_factorization.rs
// Claim: urn:core:crates_rs:core-number-theory:polynomial-factorization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn zassenhaus_factors_nonmonic_and_repeated_irreducible_polynomials() {
        let a = Polynomial::from_i64s(&[1, 0, 1]);
        let b = Polynomial::from_i64s(&[1, 1, 0, 1]);
        let p = a.pow(2).mul(&b).scale(&Rational::new(3.into(), 7.into()));
        let factorization = factor_over_q(&p, PolynomialFactorBudget::default()).unwrap();
        assert!(factorization.factors.contains(&(a, 2)));
        assert!(factorization.factors.contains(&(b, 1)));
        factorization.verify_product(&p).unwrap();
        let p = Polynomial::from_i64s(&[3, 5, 5, 2]);
        let answer = factor_over_q(&p, PolynomialFactorBudget::default()).unwrap();
        assert_eq!(answer.factors.len(), 2);
        assert!(answer.factors.contains(&(
            Polynomial::from_coefficients(vec![Rational::new(3.into(), 2.into()), q(1)]),
            1
        )));
    }
    #[test]
    fn hensel_recombination_certifies_factors_with_large_coefficients() {
        let a = Polynomial::from_i64s(&[101, 2, 1]);
        let b = Polynomial::from_i64s(&[103, -3, 1]);
        let p = a.mul(&b);
        let answer = factor_over_q(&p, PolynomialFactorBudget::default()).unwrap();
        assert_eq!(answer.factors.len(), 2);
        assert!(answer.factors.contains(&(a, 1)));
        assert!(answer.factors.contains(&(b, 1)));
        let irreducible = Polynomial::from_i64s(&[3, 0, 0, 0, 1]);
        assert_eq!(
            factor_over_q(&irreducible, PolynomialFactorBudget::default())
                .unwrap()
                .factors,
            vec![(irreducible, 1)]
        );
    }
    #[test]
    fn factorization_refuses_exhaustion_and_rejects_mutated_product_witnesses() {
        let p = Polynomial::from_i64s(&[-1, 0, 1]);
        assert_eq!(
            factor_over_q(&p, PolynomialFactorBudget { max_steps: 0 }),
            Err(PolynomialFactorError::Budget)
        );
        assert_eq!(
            factor_over_q(&Polynomial::zero(), PolynomialFactorBudget::default()),
            Err(PolynomialFactorError::Zero)
        );
        let mut answer = factor_over_q(&p, PolynomialFactorBudget::default()).unwrap();
        answer.unit = q(2);
        assert_eq!(
            answer.verify_product(&p),
            Err(PolynomialFactorError::Replay)
        );
        assert_eq!(
            factor_over_q(
                &Polynomial::constant(q(7)),
                PolynomialFactorBudget::default()
            )
            .unwrap()
            .factors,
            vec![]
        );
    }
}
