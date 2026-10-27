//! Exact elements of `Z[zeta_n]` for a run-time conductor `n`, the value ring of
//! character tables.
//!
//! An element is stored in the power basis `1, zeta, ..., zeta^(phi(n) - 1)` with
//! integer coefficients, reduced modulo the cyclotomic polynomial `Phi_n`, so two
//! elements are equal exactly when their coefficient vectors are equal. Complex
//! conjugation is `zeta -> zeta^(-1)`. There is no floating point.
//!
//! Character values and integral host amplitudes share this single BigInt carrier.
//! Rational coefficient admission proves integrality and checks a caller-declared
//! coefficient limit before entering the ring. The cyclotomic modulus comes from
//! the canonical polynomial implementation in this crate.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_aea8ec37<T> {
    fn checked_invariant_aea8ec37(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_aea8ec37<T> for Option<T> {
    #[inline]
    fn checked_invariant_aea8ec37(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_aea8ec37<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_aea8ec37(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;
use std::sync::{Arc, Mutex, OnceLock};

use crate::polynomial::{cyclotomic_polynomial, Polynomial, MAX_CONDUCTOR};
use crate::rational::Rational;
use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};

/// Refusals of the `Z[zeta_n]` constructions.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CyclotomicIntegerError {
    #[error("the conductor {0} is outside 1..={MAX_CONDUCTOR}")]
    Conductor(usize),
    #[error("the operands have different conductors {left} and {right}")]
    ConductorMismatch { left: usize, right: usize },
    #[error("coefficient {index} is not an integer")]
    NonIntegralCoefficient { index: usize },
    #[error("{actual} coefficients exceed the declared limit {limit}")]
    CoefficientBudget { actual: usize, limit: usize },
}

impl From<CyclotomicIntegerError> for String {
    fn from(error: CyclotomicIntegerError) -> Self {
        error.to_string()
    }
}

/// `Phi_n` as integer coefficients from the constant term up (monic, degree `phi(n)`), for a
/// conductor already checked against `1..=MAX_CONDUCTOR`, computed once per conductor.
fn modulus(n: usize) -> Arc<Vec<BigInt>> {
    static CACHE: OnceLock<Mutex<BTreeMap<usize, Arc<Vec<BigInt>>>>> = OnceLock::new();
    let cache = CACHE.get_or_init(|| Mutex::new(BTreeMap::new()));
    let mut guard = cache
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    guard
        .entry(n)
        .or_insert_with(|| {
            let polynomial = cyclotomic_polynomial(n).checked_invariant_aea8ec37(
                "the conductor was checked to lie in 1..=MAX_CONDUCTOR, where Phi_n exists",
            );
            Arc::new(
                polynomial
                    .coefficients()
                    .iter()
                    .map(|c| {
                        debug_assert!(
                            c.is_integer(),
                            "cyclotomic polynomials have integer coefficients"
                        );
                        c.numer().clone()
                    })
                    .collect(),
            )
        })
        .clone()
}

fn check_conductor(conductor: usize) -> Result<usize, CyclotomicIntegerError> {
    if conductor == 0 || conductor > MAX_CONDUCTOR {
        return Err(CyclotomicIntegerError::Conductor(conductor));
    }
    Ok(conductor)
}

/// An element of `Z[zeta_n]`.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CyclotomicInteger {
    conductor: usize,
    /// Coefficients of `1, zeta, .., zeta^(phi(n) - 1)`.
    coefficients: Vec<BigInt>,
}

impl CyclotomicInteger {
    /// Admit integral rational coefficients, at the default limit of 512 entries.
    pub fn new(
        conductor: usize,
        coefficients: Vec<Rational>,
    ) -> Result<Self, CyclotomicIntegerError> {
        Self::with_budget(conductor, coefficients, 512)
    }

    /// Check the coefficient count and integrality before exact integer reduction.
    pub fn with_budget(
        conductor: usize,
        coefficients: Vec<Rational>,
        coefficient_limit: usize,
    ) -> Result<Self, CyclotomicIntegerError> {
        if coefficients.len() > coefficient_limit {
            return Err(CyclotomicIntegerError::CoefficientBudget {
                actual: coefficients.len(),
                limit: coefficient_limit,
            });
        }
        if let Some(index) = coefficients.iter().position(|c| !c.is_integer()) {
            return Err(CyclotomicIntegerError::NonIntegralCoefficient { index });
        }
        Ok(Self::reduce(
            check_conductor(conductor)?,
            coefficients.into_iter().map(|c| c.to_integer()).collect(),
        ))
    }

    /// Canonically trimmed rational values for JSON and rational-polynomial ingestion.
    /// This allocates an adapter view; the only stored arithmetic coefficients are BigInt.
    pub fn coefficient_values(&self) -> Vec<Rational> {
        let length = self
            .coefficients
            .iter()
            .rposition(|c| !c.is_zero())
            .map_or(0, |i| i + 1);
        self.coefficients[..length]
            .iter()
            .cloned()
            .map(Rational::from_integer)
            .collect()
    }

    pub fn scalar(conductor: usize, value: i64) -> Result<Self, CyclotomicIntegerError> {
        Self::from_integer(conductor, value.into())
    }

    pub fn zeta(conductor: usize) -> Result<Self, CyclotomicIntegerError> {
        Self::root_of_unity(conductor, 1)
    }

    pub fn sub(&self, other: &Self) -> Result<Self, CyclotomicIntegerError> {
        self.add(&other.negate())
    }

    /// Exact exponentiation in the already admitted ring, including exponent zero.
    pub fn pow(&self, mut exponent: usize) -> Self {
        let mut base = self.clone();
        let mut out = Self::reduce(self.conductor, vec![BigInt::one()]);
        while exponent != 0 {
            if exponent & 1 == 1 {
                out = out.mul(&base).checked_invariant_aea8ec37("one admitted conductor");
            }
            exponent >>= 1;
            if exponent != 0 {
                base = base.mul(&base).checked_invariant_aea8ec37("one admitted conductor");
            }
        }
        out
    }

    pub fn conj(&self) -> Self {
        self.conjugate()
    }

    /// Algebraic norm, the canonical resultant Res(Phi_n, value).
    pub fn norm(&self) -> BigInt {
        let phi = Polynomial::from_coefficients(
            modulus(self.conductor)
                .iter()
                .cloned()
                .map(Rational::from_integer)
                .collect(),
        );
        let value = Polynomial::from_coefficients(self.coefficient_values());
        let norm = phi.resultant(&value);
        debug_assert!(
            norm.is_integer(),
            "the norm of an algebraic integer is integral"
        );
        norm.to_integer()
    }

    /// An algebraic integer is a unit precisely when its integral norm is +/-1.
    pub fn is_unit(&self) -> bool {
        self.norm().abs() == BigInt::one()
    }

    /// Reduce an arbitrary-length coefficient vector modulo `Phi_n`; `conductor` is valid.
    fn reduce(conductor: usize, mut raw: Vec<BigInt>) -> Self {
        let modulus = modulus(conductor);
        let degree = modulus.len() - 1;
        if raw.len() > degree {
            for top in (degree..raw.len()).rev() {
                let c = raw[top].clone();
                if c.is_zero() {
                    continue;
                }
                for (k, mk) in modulus.iter().enumerate() {
                    raw[top - degree + k] -= &c * mk;
                }
            }
        }
        raw.resize(degree, BigInt::zero());
        Self {
            conductor,
            coefficients: raw,
        }
    }

    pub fn zero(conductor: usize) -> Result<Self, CyclotomicIntegerError> {
        Ok(Self::reduce(check_conductor(conductor)?, Vec::new()))
    }

    pub fn from_integer(conductor: usize, value: BigInt) -> Result<Self, CyclotomicIntegerError> {
        Ok(Self::reduce(check_conductor(conductor)?, vec![value]))
    }

    /// `zeta_n^exponent`, for any integer exponent (reduced modulo `n`).
    pub fn root_of_unity(conductor: usize, exponent: i64) -> Result<Self, CyclotomicIntegerError> {
        let n = check_conductor(conductor)?;
        let n_signed = i64::try_from(n).checked_invariant_aea8ec37("a conductor up to MAX_CONDUCTOR fits i64");
        let e = usize::try_from(exponent.rem_euclid(n_signed))
            .checked_invariant_aea8ec37("rem_euclid of a positive modulus is nonnegative");
        let mut raw = vec![BigInt::zero(); e + 1];
        raw[e] = BigInt::one();
        Ok(Self::reduce(n, raw))
    }

    /// `sum multiplicity * zeta_n^exponent` for a formal sum over exponents (reduced modulo `n`).
    pub fn from_formal_sum(
        conductor: usize,
        terms: &[(usize, BigInt)],
    ) -> Result<Self, CyclotomicIntegerError> {
        let n = check_conductor(conductor)?;
        let mut raw = vec![BigInt::zero(); n];
        for (exponent, multiplicity) in terms {
            raw[exponent % n] += multiplicity;
        }
        Ok(Self::reduce(n, raw))
    }

    pub fn conductor(&self) -> usize {
        self.conductor
    }

    /// The reduced coefficients of `1, zeta, .., zeta^(phi(n) - 1)`.
    pub fn coefficients(&self) -> &[BigInt] {
        &self.coefficients
    }

    pub fn is_zero(&self) -> bool {
        self.coefficients.iter().all(Zero::is_zero)
    }

    /// The integer this element equals, when it lies in `Z`.
    pub fn as_integer(&self) -> Option<BigInt> {
        if self.coefficients.iter().skip(1).all(Zero::is_zero) {
            Some(
                self.coefficients
                    .first()
                    .cloned()
                    .unwrap_or_else(BigInt::zero),
            )
        } else {
            None
        }
    }

    fn require_same_conductor(&self, other: &Self) -> Result<(), CyclotomicIntegerError> {
        if self.conductor != other.conductor {
            return Err(CyclotomicIntegerError::ConductorMismatch {
                left: self.conductor,
                right: other.conductor,
            });
        }
        Ok(())
    }

    pub fn add(&self, other: &Self) -> Result<Self, CyclotomicIntegerError> {
        self.require_same_conductor(other)?;
        Ok(Self {
            conductor: self.conductor,
            coefficients: self
                .coefficients
                .iter()
                .zip(&other.coefficients)
                .map(|(a, b)| a + b)
                .collect(),
        })
    }

    pub fn mul(&self, other: &Self) -> Result<Self, CyclotomicIntegerError> {
        self.require_same_conductor(other)?;
        let mut raw = vec![BigInt::zero(); self.coefficients.len() + other.coefficients.len()];
        for (i, a) in self.coefficients.iter().enumerate() {
            if a.is_zero() {
                continue;
            }
            for (j, b) in other.coefficients.iter().enumerate() {
                raw[i + j] += a * b;
            }
        }
        Ok(Self::reduce(self.conductor, raw))
    }

    pub fn scale(&self, factor: &BigInt) -> Self {
        Self {
            conductor: self.conductor,
            coefficients: self.coefficients.iter().map(|c| c * factor).collect(),
        }
    }

    pub fn negate(&self) -> Self {
        self.scale(&-BigInt::one())
    }

    /// Complex conjugation `zeta -> zeta^(-1)`.
    pub fn conjugate(&self) -> Self {
        let n = self.conductor;
        let mut raw = vec![BigInt::zero(); n];
        for (k, c) in self.coefficients.iter().enumerate() {
            // zeta^k -> zeta^(n - k) for k >= 1, and 1 -> 1.
            raw[(n - k % n) % n] += c;
        }
        Self::reduce(n, raw)
    }
}

// Origin: engine/crates_rs/core_number_theory/src/cyclotomic_integer.rs
// Claim: urn:core:crates_rs:core-number-theory:cyclotomic-integer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::polynomial::euler_phi;

    fn big(n: i64) -> BigInt {
        BigInt::from(n)
    }

    fn z(n: usize, k: i64) -> CyclotomicInteger {
        CyclotomicInteger::root_of_unity(n, k).unwrap()
    }

    #[test]
    fn the_modulus_is_the_monic_integer_cyclotomic_polynomial() {
        let coefficients = |n: usize| -> Vec<i64> {
            modulus(n)
                .iter()
                .map(|c| i64::try_from(c).expect("small"))
                .collect()
        };
        assert_eq!(coefficients(1), vec![-1, 1]);
        assert_eq!(coefficients(2), vec![1, 1]);
        assert_eq!(coefficients(3), vec![1, 1, 1]);
        assert_eq!(coefficients(4), vec![1, 0, 1]);
        assert_eq!(coefficients(6), vec![1, -1, 1]);
        assert_eq!(coefficients(12), vec![1, 0, -1, 0, 1]);
        assert_eq!(coefficients(24), vec![1, 0, 0, 0, -1, 0, 0, 0, 1]);
    }

    #[test]
    fn the_stored_coefficient_count_is_the_totient() {
        for n in 1..=60usize {
            assert_eq!(z(n, 1).coefficients().len(), euler_phi(n), "n = {n}");
        }
    }

    #[test]
    fn the_sum_of_all_nth_roots_of_unity_vanishes() {
        for n in 2..=12usize {
            let terms: Vec<(usize, BigInt)> = (0..n).map(|e| (e, BigInt::one())).collect();
            assert!(
                CyclotomicInteger::from_formal_sum(n, &terms)
                    .unwrap()
                    .is_zero(),
                "n = {n}"
            );
        }
    }

    #[test]
    fn a_root_of_unity_times_its_conjugate_is_one() {
        for n in [3usize, 5, 8, 12] {
            let zeta = z(n, 1);
            assert_eq!(
                zeta.mul(&zeta.conjugate()).unwrap(),
                CyclotomicInteger::from_integer(n, big(1)).unwrap(),
                "n = {n}"
            );
        }
    }

    #[test]
    fn conjugation_is_an_involutive_ring_automorphism() {
        let a = z(12, 1).add(&z(12, 5).scale(&big(3))).unwrap();
        let b = z(12, 7).add(&z(12, 2)).unwrap();
        assert_eq!(a.conjugate().conjugate(), a);
        assert_eq!(
            a.mul(&b).unwrap().conjugate(),
            a.conjugate().mul(&b.conjugate()).unwrap()
        );
        assert_eq!(
            a.add(&b).unwrap().conjugate(),
            a.conjugate().add(&b.conjugate()).unwrap()
        );
    }

    #[test]
    fn a_conductor_three_element_reduces_and_compares_canonically() {
        // zeta_3^2 = -1 - zeta_3.
        let w = z(3, 1);
        let w2 = w.mul(&w).unwrap();
        assert_eq!(w2.coefficients(), &[big(-1), big(-1)]);
        assert_eq!(z(3, 2), w2);
        assert_eq!(z(3, -1), w2);
        assert_eq!(w.conjugate(), w2);
    }

    #[test]
    fn invalid_conductors_and_mismatched_operands_are_refused() {
        assert_eq!(
            CyclotomicInteger::zero(0),
            Err(CyclotomicIntegerError::Conductor(0))
        );
        assert_eq!(
            CyclotomicInteger::root_of_unity(MAX_CONDUCTOR + 1, 1),
            Err(CyclotomicIntegerError::Conductor(MAX_CONDUCTOR + 1))
        );
        assert!(CyclotomicInteger::from_integer(0, big(1)).is_err());
        assert!(CyclotomicInteger::from_formal_sum(0, &[]).is_err());
        let a = z(3, 1);
        let b = z(4, 1);
        assert_eq!(
            a.add(&b),
            Err(CyclotomicIntegerError::ConductorMismatch { left: 3, right: 4 })
        );
        assert_eq!(
            a.mul(&b),
            Err(CyclotomicIntegerError::ConductorMismatch { left: 3, right: 4 })
        );
    }

    #[test]
    fn as_integer_reads_only_true_integers() {
        assert_eq!(
            CyclotomicInteger::from_integer(5, big(7))
                .unwrap()
                .as_integer(),
            Some(big(7))
        );
        assert_eq!(z(5, 1).as_integer(), None);
        // zeta_6 + zeta_6^5 = 1 (twice the real part of e^{i pi/3}).
        assert_eq!(z(6, 1).add(&z(6, 5)).unwrap().as_integer(), Some(big(1)));
    }
}
