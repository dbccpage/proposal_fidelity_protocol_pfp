//! Cyclotomic number fields `Q(zeta_n)` of any conductor `1 <= n <= MAX_CONDUCTOR`, exact.
//!
//! An element is stored in the power basis `1, zeta, ..., zeta^{phi(n) - 1}` modulo the
//! cyclotomic polynomial `Phi_n`, with `zeta = e^{2 pi i / n}` under the canonical
//! embedding. Two types share one arithmetic:
//!
//! - [`CyclotomicNumber`]: the conductor is a run-time value; operations are checked and
//!   return [`CyclotomicError::ConductorMismatch`] for operands from different fields.
//! - [`Cyclotomic<N>`]: the conductor is a compile-time constant (a bad `N` does not
//!   compile); it implements the `linear_algebra::scalars` tower and the `std::ops`
//!   operators, so matrices, polynomials and the exact solvers work over it.
//!
//! Beyond field arithmetic the module provides the structure the physics needs:
//! conjugation and every Galois automorphism `sigma_k`, the exact trace and norm to `Q`,
//! the real subfield through `t = zeta + zeta^{-1}` and the minimal polynomial of
//! `2 cos(2 pi / n)` computed from `Phi_n`, quantum integers `[k]_q` at `q = zeta_n`,
//! Gauss sums and the exact position of `sqrt(d)` inside `Q(zeta_n)` when it lies there,
//! and conversions to and from the fixed-conductor types of [`crate::cyclotomic`].
//!
//! Per-conductor data (the modulus, the reduced powers of `zeta`) is computed once and
//! shared; sharing affects speed only, never a result.
//!
//! There is no floating point in this module. AuthorityEffect: None.

use std::collections::BTreeMap;
use std::hash::{Hash, Hasher};
use std::sync::{Arc, Mutex, OnceLock};

use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Deserializer, Serialize, Serializer};

use crate::cyclotomic::{Cyc12, Cyc24, Cyc5, Cyc8, EisensteinRat, GaussianRat};
use crate::cyclotomic120::Cyc120;
use crate::cyclotomic28::Cyc28;
use crate::cyclotomic44::Cyc44;
use crate::cyclotomic52::Cyc52;
use crate::polynomial::{
    cyclotomic_polynomial, distinct_prime_factors, euler_phi, mobius, Polynomial, PolynomialError,
    MAX_CONDUCTOR,
};
use crate::rational::{r_one, r_zero, squarefree_part, ArithmeticError, Rational};

/// The largest index `k` accepted by [`quantum_integer`].
pub const MAX_QUANTUM_INDEX: u64 = 1 << 20;

/// Refusals of the cyclotomic-field types.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CyclotomicError {
    #[error("conductor 0 does not define a cyclotomic field")]
    ConductorZero,
    #[error("conductor {conductor} exceeds the supported maximum {max}")]
    ConductorTooLarge { conductor: usize, max: usize },
    #[error("the operands lie in different cyclotomic fields, Q(zeta_{left}) and Q(zeta_{right})")]
    ConductorMismatch { left: usize, right: usize },
    #[error("Q(zeta_{conductor}) has degree {expected}, but {actual} coefficients were given")]
    CoefficientCount {
        conductor: usize,
        expected: usize,
        actual: usize,
    },
    #[error("division by zero")]
    DivisionByZero,
    #[error(
        "the exponent {k} is not coprime to the conductor {conductor}, so it is not a Galois \
         automorphism"
    )]
    NotCoprime { k: i64, conductor: usize },
    #[error(
        "sqrt({d}) does not lie in Q(zeta_{conductor}): Q(sqrt {squarefree}) has conductor \
         {required}, which does not divide {conductor}"
    )]
    NoSquareRoot {
        d: BigInt,
        squarefree: BigInt,
        conductor: usize,
        required: BigInt,
    },
    #[error("quantum integer index {index} exceeds the supported maximum {max}")]
    QuantumIndexTooLarge { index: u64, max: u64 },
    #[error("{prime} is not an odd prime dividing the conductor {conductor}")]
    NotAGaussSumModulus { prime: usize, conductor: usize },
    #[error("internal inconsistency: {0}")]
    Inconsistent(&'static str),
    #[error(transparent)]
    Polynomial(#[from] PolynomialError),
    #[error(transparent)]
    Arithmetic(#[from] ArithmeticError),
}

fn check_conductor(conductor: usize) -> Result<(), CyclotomicError> {
    if conductor == 0 {
        return Err(CyclotomicError::ConductorZero);
    }
    if conductor > MAX_CONDUCTOR {
        return Err(CyclotomicError::ConductorTooLarge {
            conductor,
            max: MAX_CONDUCTOR,
        });
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Per-conductor context
// ---------------------------------------------------------------------------

/// Everything derived from the conductor alone: `Phi_n`, the reduced powers of `zeta`,
/// the minimal polynomial of `zeta + zeta^{-1}`.
struct CyclotomicContext {
    conductor: usize,
    degree: usize,
    modulus: Polynomial<Rational>,
    /// `Phi_n = x^degree + sum m_i x^i`: the nonzero `(i, m_i)` with `i < degree`.
    modulus_low: Vec<(usize, Rational)>,
    powers: OnceLock<Vec<Vec<Rational>>>,
    min_poly: OnceLock<Polynomial<Rational>>,
}

impl CyclotomicContext {
    fn build(conductor: usize) -> Result<Self, CyclotomicError> {
        check_conductor(conductor)?;
        let modulus = cyclotomic_polynomial(conductor)?;
        let degree = modulus
            .degree()
            .ok_or(CyclotomicError::Inconsistent("Phi_n is nonzero"))?;
        let modulus_low = modulus
            .coefficients()
            .iter()
            .take(degree)
            .enumerate()
            .filter(|(_, c)| !c.is_zero())
            .map(|(i, c)| (i, c.clone()))
            .collect();
        Ok(Self {
            conductor,
            degree,
            modulus,
            modulus_low,
            powers: OnceLock::new(),
            min_poly: OnceLock::new(),
        })
    }

    /// Reduce a polynomial of any length modulo `Phi_n` to exactly `degree` coefficients.
    fn reduce(&self, mut poly: Vec<Rational>) -> Vec<Rational> {
        let d = self.degree;
        while poly.len() > d {
            let Some(top) = poly.pop() else {
                break;
            };
            if top.is_zero() {
                continue;
            }
            // x^k = x^{k-d} x^d and x^d = -sum m_i x^i.
            let shift = poly.len() - d;
            for (i, m) in &self.modulus_low {
                poly[shift + i] -= &top * m;
            }
        }
        poly.resize(d, r_zero());
        poly
    }

    fn mul_coefficients(&self, a: &[Rational], b: &[Rational]) -> Vec<Rational> {
        if a.is_empty() || b.is_empty() {
            return vec![r_zero(); self.degree];
        }
        let mut product = vec![r_zero(); a.len() + b.len() - 1];
        for (i, x) in a.iter().enumerate() {
            if x.is_zero() {
                continue;
            }
            for (j, y) in b.iter().enumerate() {
                if !y.is_zero() {
                    product[i + j] += x * y;
                }
            }
        }
        self.reduce(product)
    }

    /// `zeta^0, zeta^1, ..., zeta^{n-1}` as reduced coefficient vectors.
                // Multiply by zeta: shift up, and fold the overflowing top coefficient
                // back with zeta^d = -sum m_i zeta^i.
    fn build_powers(&self) -> Vec<Vec<Rational>> {
        let mut table = Vec::with_capacity(self.conductor);
        let mut current = vec![r_zero(); self.degree];
        if let Some(first) = current.first_mut() {
            *first = r_one();
        }
        for _ in 0..self.conductor {
            table.push(current.clone());
            let carry = current.pop().unwrap_or_else(r_zero);
            current.insert(0, r_zero());
            if !carry.is_zero() {
                for (i, m) in &self.modulus_low {
                    current[*i] -= &carry * m;
                }
            }
        }
        table
    }

    fn powers(&self) -> &[Vec<Rational>] {
        self.powers.get_or_init(|| self.build_powers())
    }

    /// The reduced coefficients of `zeta^k` for any integer `k`.
    fn zeta(&self, k: i64) -> Vec<Rational> {
        // The conductor is at most MAX_CONDUCTOR, so the conversions below are lossless.
        let index = k.rem_euclid(self.conductor as i64) as usize;
        self.powers()
            .get(index)
            .cloned()
            .unwrap_or_else(|| vec![r_zero(); self.degree])
    }

    /// `sigma_k(x) = sum c_i zeta^{ik}` for `k` coprime to the conductor.
    fn galois(&self, coefficients: &[Rational], k: usize) -> Vec<Rational> {
        let table = self.powers();
        let mut out = vec![r_zero(); self.degree];
        for (i, c) in coefficients.iter().enumerate() {
            if c.is_zero() {
                continue;
            }
            // i < degree and k < conductor, both at most MAX_CONDUCTOR: no overflow.
            let index = (i * k) % self.conductor;
            let Some(power) = table.get(index) else {
                continue;
            };
            for (slot, p) in out.iter_mut().zip(power) {
                if !p.is_zero() {
                    *slot += c * p;
                }
            }
        }
        out
    }

    /// The minimal polynomial of `zeta + zeta^{-1}`, computed from `Phi_n`.
    fn min_poly(&self) -> &Polynomial<Rational> {
        self.min_poly
            .get_or_init(|| min_poly_from_cyclotomic(self.conductor, &self.modulus))
    }

    fn inverse(&self, coefficients: &[Rational]) -> Option<Vec<Rational>> {
        let element = Polynomial::from_coefficients(coefficients.to_vec());
        if element.is_zero() {
            return None;
        }
        let (gcd, bezout, _) = element.xgcd(&self.modulus);
        if gcd != Polynomial::one() {
            return None;
        }
        Some(self.reduce(bezout.coefficients().to_vec()))
    }
}

fn registry() -> &'static Mutex<BTreeMap<usize, Arc<CyclotomicContext>>> {
    static REGISTRY: OnceLock<Mutex<BTreeMap<usize, Arc<CyclotomicContext>>>> = OnceLock::new();
    REGISTRY.get_or_init(|| Mutex::new(BTreeMap::new()))
}

fn context(conductor: usize) -> Result<Arc<CyclotomicContext>, CyclotomicError> {
    check_conductor(conductor)?;
    {
        let cache = registry().lock().unwrap_or_else(|e| e.into_inner());
        if let Some(found) = cache.get(&conductor) {
            return Ok(Arc::clone(found));
        }
    }
    let built = Arc::new(CyclotomicContext::build(conductor)?);
    let mut cache = registry().lock().unwrap_or_else(|e| e.into_inner());
    Ok(Arc::clone(cache.entry(conductor).or_insert(built)))
}

/// The Dickson polynomials `D_0, ..., D_k` with `D_j(x + 1/x) = x^j + x^{-j}`:
/// `D_0 = 2`, `D_1 = t`, `D_{j+1} = t D_j - D_{j-1}`.
fn dickson_polynomials(k: usize) -> Vec<Polynomial<Rational>> {
    let t = Polynomial::from_i64s(&[0, 1]);
    let mut all = vec![Polynomial::from_i64s(&[2])];
    if k >= 1 {
        all.push(t.clone());
    }
    for j in 2..=k {
        let next = t.mul(&all[j - 1]).sub(&all[j - 2]);
        all.push(next);
    }
    all
}

/// `Psi_n(t)` with `Phi_n(x) = x^m Psi_n(x + 1/x)`, `m = phi(n) / 2`, from the palindromic
/// `Phi_n = sum c_i x^i`: `Psi_n = c_m + sum_{j >= 1} c_{m+j} D_j(t)`.
fn min_poly_from_cyclotomic(conductor: usize, phi: &Polynomial<Rational>) -> Polynomial<Rational> {
    match conductor {
        1 => return Polynomial::from_i64s(&[-2, 1]),
        2 => return Polynomial::from_i64s(&[2, 1]),
        _ => {}
    }
    let m = phi.coefficients().len().saturating_sub(1) / 2;
    let dickson = dickson_polynomials(m);
    let mut psi = Polynomial::constant(phi.coefficient(m));
    for (j, d) in dickson.iter().enumerate().skip(1) {
        psi = psi.add(&d.scale(&phi.coefficient(m + j)));
    }
    psi
}

/// The minimal polynomial `Psi_n` of `2 cos(2 pi / n) = zeta_n + zeta_n^{-1}` over `Q`,
/// computed from `Phi_n` (not tabulated). It is monic of degree `phi(n)/2` for `n >= 3`,
/// `t - 2` for `n = 1` and `t + 2` for `n = 2`.
pub fn min_poly_of_2cos(conductor: usize) -> Result<Polynomial<Rational>, CyclotomicError> {
    Ok(context(conductor)?.min_poly().clone())
}

/// Least conductor of Q(zeta_n), accounting for Q(zeta_(2r))=Q(zeta_r)
/// when r is odd. This normalization also identifies Q(zeta_1)=Q(zeta_2).
pub fn normalized_conductor(n: usize) -> Result<usize, CyclotomicError> {
    check_conductor(n)?;
    Ok(if n % 4 == 2 { n / 2 } else { n })
}

/// Exact inclusion of full cyclotomic fields (not just divisibility of labels).
pub fn contains_cyclotomic_field(source: usize, target: usize) -> Result<bool, CyclotomicError> {
    Ok(normalized_conductor(target)? % normalized_conductor(source)? == 0)
}

pub fn compositum_conductor(a: usize, b: usize) -> Result<usize, CyclotomicError> {
    let (a, b) = (normalized_conductor(a)?, normalized_conductor(b)?);
    let n = a
        .checked_mul(b / a.gcd(&b))
        .ok_or(CyclotomicError::ConductorTooLarge {
            conductor: usize::MAX,
            max: MAX_CONDUCTOR,
        })?;
    normalized_conductor(n)
}

pub fn intersection_conductor(a: usize, b: usize) -> Result<usize, CyclotomicError> {
    normalized_conductor(normalized_conductor(a)?.gcd(&normalized_conductor(b)?))
}

pub fn real_subfield_degree(n: usize) -> Result<usize, CyclotomicError> {
    check_conductor(n)?;
    Ok(euler_phi(n).max(2) / 2)
}

/// The canonical inclusion, evaluated in the common complex embedding. The
/// source generator is replaced by its exact power of the target generator,
/// including the sign needed for conductors congruent to two modulo four.
pub fn embed_cyclotomic(
    x: &CyclotomicNumber,
    target: usize,
) -> Result<CyclotomicNumber, CyclotomicError> {
    if !contains_cyclotomic_field(x.conductor(), target)? {
        return Err(CyclotomicError::ConductorMismatch {
            left: x.conductor(),
            right: target,
        });
    }
    let source = x.conductor();
    let (power, negative) = if source % 4 == 2 {
        let odd = source / 2;
        ((target / odd) * odd.div_ceil(2), true)
    } else {
        (target / source, false)
    };
    let mut out = CyclotomicNumber::zero(target)?;
    for (i, c) in x.coefficients().iter().enumerate() {
        let coefficient = if negative && i % 2 != 0 {
            -c
        } else {
            c.clone()
        };
        out = out.add(&CyclotomicNumber::zeta(target, (i * power) as i64)?.scale(&coefficient))?;
    }
    Ok(out)
}

// ---------------------------------------------------------------------------
// CyclotomicNumber
// ---------------------------------------------------------------------------

/// An element of `Q(zeta_n)` with a run-time conductor `n`, in the power basis modulo
/// `Phi_n`: exactly `phi(n)` rational coefficients.
///
/// Equality and hashing are those of the pair (conductor, coefficients); the shared
/// per-conductor data it carries is not part of the value.
#[derive(Clone)]
pub struct CyclotomicNumber {
    context: Arc<CyclotomicContext>,
    coefficients: Vec<Rational>,
}

impl std::fmt::Debug for CyclotomicNumber {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self}")
    }
}

impl std::fmt::Display for CyclotomicNumber {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "[Q(zeta_{}): ", self.conductor())?;
        for (i, c) in self.coefficients.iter().enumerate() {
            if i > 0 {
                write!(f, ", ")?;
            }
            write!(f, "{c}")?;
        }
        write!(f, "]")
    }
}

impl PartialEq for CyclotomicNumber {
    fn eq(&self, other: &Self) -> bool {
        self.conductor() == other.conductor() && self.coefficients == other.coefficients
    }
}

impl Eq for CyclotomicNumber {}

impl Hash for CyclotomicNumber {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.conductor().hash(state);
        self.coefficients.hash(state);
    }
}

#[derive(Serialize, Deserialize)]
struct CyclotomicNumberWire {
    conductor: usize,
    coefficients: Vec<Rational>,
}

impl Serialize for CyclotomicNumber {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        CyclotomicNumberWire {
            conductor: self.conductor(),
            coefficients: self.coefficients.clone(),
        }
        .serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for CyclotomicNumber {
    /// Validates the conductor and the coefficient count, so a wire form cannot smuggle
    /// in an element that is not in its claimed field.
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let wire = CyclotomicNumberWire::deserialize(deserializer)?;
        Self::from_coefficients(wire.conductor, wire.coefficients).map_err(serde::de::Error::custom)
    }
}

impl CyclotomicNumber {
    fn in_context(context: &Arc<CyclotomicContext>, coefficients: Vec<Rational>) -> Self {
        Self {
            context: Arc::clone(context),
            coefficients,
        }
    }

    /// The element with these power-basis coefficients. There must be exactly
    /// `phi(conductor)` of them.
    pub fn from_coefficients(
        conductor: usize,
        coefficients: Vec<Rational>,
    ) -> Result<Self, CyclotomicError> {
        let context = context(conductor)?;
        if coefficients.len() != context.degree {
            return Err(CyclotomicError::CoefficientCount {
                conductor,
                expected: context.degree,
                actual: coefficients.len(),
            });
        }
        Ok(Self {
            context,
            coefficients,
        })
    }

    /// The element `p(zeta)` for a polynomial `p` of any degree (reduced modulo `Phi_n`).
    pub fn from_polynomial(
        conductor: usize,
        p: &Polynomial<Rational>,
    ) -> Result<Self, CyclotomicError> {
        let context = context(conductor)?;
        let coefficients = context.reduce(p.coefficients().to_vec());
        Ok(Self {
            context,
            coefficients,
        })
    }

    /// The polynomial in `zeta` of degree below `phi(n)` that represents the element.
    pub fn to_polynomial(&self) -> Polynomial<Rational> {
        Polynomial::from_coefficients(self.coefficients.clone())
    }

    pub fn zero(conductor: usize) -> Result<Self, CyclotomicError> {
        Self::from_rational(conductor, r_zero())
    }

    pub fn one(conductor: usize) -> Result<Self, CyclotomicError> {
        Self::from_rational(conductor, r_one())
    }

    /// The rational number `q` as an element of `Q(zeta_n)`.
    pub fn from_rational(conductor: usize, q: Rational) -> Result<Self, CyclotomicError> {
        let context = context(conductor)?;
        let mut coefficients = vec![r_zero(); context.degree];
        if let Some(first) = coefficients.first_mut() {
            *first = q;
        }
        Ok(Self {
            context,
            coefficients,
        })
    }

    /// `zeta_n^k` for any integer `k` (taken modulo `n`).
    pub fn zeta(conductor: usize, k: i64) -> Result<Self, CyclotomicError> {
        let context = context(conductor)?;
        let coefficients = context.zeta(k);
        Ok(Self {
            context,
            coefficients,
        })
    }

    pub fn conductor(&self) -> usize {
        self.context.conductor
    }

    /// `phi(n)`, the number of coefficients.
    pub fn degree(&self) -> usize {
        self.coefficients.len()
    }

    pub fn coefficients(&self) -> &[Rational] {
        &self.coefficients
    }

    pub fn is_zero(&self) -> bool {
        self.coefficients.iter().all(|c| c.is_zero())
    }

    /// Whether the element lies in `Q` (every coefficient of `zeta^i`, `i > 0`, vanishes).
    pub fn is_rational(&self) -> bool {
        self.coefficients.iter().skip(1).all(|c| c.is_zero())
    }

    pub fn as_rational(&self) -> Option<Rational> {
        if self.is_rational() {
            self.coefficients.first().cloned()
        } else {
            None
        }
    }

    fn same_field(&self, other: &Self) -> Result<(), CyclotomicError> {
        if self.conductor() != other.conductor() {
            return Err(CyclotomicError::ConductorMismatch {
                left: self.conductor(),
                right: other.conductor(),
            });
        }
        Ok(())
    }

    fn with(&self, coefficients: Vec<Rational>) -> Self {
        Self::in_context(&self.context, coefficients)
    }

    /// Coefficientwise combination of two elements of the same field. Internal: callers
    /// have established (or know by type) that the conductors agree.
    fn zip_same_field(&self, other: &Self, f: impl Fn(&Rational, &Rational) -> Rational) -> Self {
        self.with(
            self.coefficients
                .iter()
                .zip(&other.coefficients)
                .map(|(a, b)| f(a, b))
                .collect(),
        )
    }

    pub fn add(&self, other: &Self) -> Result<Self, CyclotomicError> {
        self.same_field(other)?;
        Ok(self.zip_same_field(other, |a, b| a + b))
    }

    pub fn sub(&self, other: &Self) -> Result<Self, CyclotomicError> {
        self.same_field(other)?;
        Ok(self.zip_same_field(other, |a, b| a - b))
    }

    pub fn neg(&self) -> Self {
        self.with(self.coefficients.iter().map(|c| -c).collect())
    }

    /// `c * self` for a rational `c`.
    pub fn scale(&self, c: &Rational) -> Self {
        self.with(self.coefficients.iter().map(|a| a * c).collect())
    }

    pub fn mul(&self, other: &Self) -> Result<Self, CyclotomicError> {
        self.same_field(other)?;
        Ok(self.mul_same_field(other))
    }

    fn mul_same_field(&self, other: &Self) -> Self {
        self.with(
            self.context
                .mul_coefficients(&self.coefficients, &other.coefficients),
        )
    }

    /// `self^n`.
    pub fn pow(&self, n: u32) -> Self {
        let mut result = Self::in_context(&self.context, {
            let mut one = vec![r_zero(); self.context.degree];
            if let Some(first) = one.first_mut() {
                *first = r_one();
            }
            one
        });
        let mut base = self.clone();
        let mut n = n;
        while n > 0 {
            if n & 1 == 1 {
                result = result.mul_same_field(&base);
            }
            n >>= 1;
            if n > 0 {
                base = base.mul_same_field(&base);
            }
        }
        result
    }

    /// `1 / self`, or `None` for zero.
    pub fn inverse(&self) -> Option<Self> {
        Some(self.with(self.context.inverse(&self.coefficients)?))
    }

    /// `self / other`; refuses a zero divisor and different conductors.
    pub fn checked_div(&self, other: &Self) -> Result<Self, CyclotomicError> {
        self.same_field(other)?;
        let inverse = other.inverse().ok_or(CyclotomicError::DivisionByZero)?;
        Ok(self.mul_same_field(&inverse))
    }

    /// Complex conjugation, `zeta -> zeta^{-1}`.
    pub fn conjugate(&self) -> Self {
        // sigma_{n-1} is sigma_{-1}; for n <= 2 conjugation is the identity, sigma_1.
        let k = self.conductor().saturating_sub(1).max(1);
        self.with(self.context.galois(&self.coefficients, k))
    }

    /// The Galois automorphism `sigma_k: zeta -> zeta^k`, for `k` coprime to `n`
    /// (negative `k` allowed, taken modulo `n`).
    pub fn galois(&self, k: i64) -> Result<Self, CyclotomicError> {
        let n = self.conductor();
        let not_coprime = || CyclotomicError::NotCoprime { k, conductor: n };
        // n <= MAX_CONDUCTOR, so it fits i64; the residue is nonnegative and below n.
        let residue = usize::try_from(k.rem_euclid(n as i64)).map_err(|_| not_coprime())?;
        if residue.gcd(&n) != 1 {
            return Err(not_coprime());
        }
        Ok(self.with(self.context.galois(&self.coefficients, residue)))
    }

    /// Whether complex conjugation fixes the element, i.e. it lies in `Q(zeta_n)^+`.
    pub fn is_real(&self) -> bool {
        self.conjugate() == *self
    }

    /// The real part `(x + conj x) / 2`, itself an element of `Q(zeta_n)^+`.
    pub fn real_part(&self) -> Self {
        let sum = self.zip_same_field(&self.conjugate(), |a, b| a + b);
        sum.scale(&Rational::new(BigInt::one(), BigInt::from(2)))
    }

    /// The trace `Tr_{K/Q}(x) = sum_sigma sigma(x)`, exactly, by the Ramanujan sums
    /// `Tr(zeta^j) = mu(n/g) phi(n) / phi(n/g)` with `g = gcd(j, n)`.
    pub fn trace(&self) -> Rational {
        let n = self.conductor();
        let phi = euler_phi(n);
        let mut total = r_zero();
        for (j, c) in self.coefficients.iter().enumerate() {
            if c.is_zero() {
                continue;
            }
            let quotient = n / j.gcd(&n);
            // phi(n/g) divides phi(n), so the integer division is exact.
            let ramanujan =
                BigInt::from(mobius(quotient)) * BigInt::from(phi / euler_phi(quotient));
            total += c * Rational::from_integer(ramanujan);
        }
        total
    }

    /// The norm `N_{K/Q}(x) = prod_sigma sigma(x)`, exactly, as the resultant
    /// `Res(Phi_n, x(t))`.
    pub fn norm(&self) -> Rational {
        self.context.modulus.resultant(&self.to_polynomial())
    }

    /// The real part as a polynomial in `t = zeta + zeta^{-1}` of degree below `phi(n)/2`
    /// (reduced modulo the minimal polynomial `Psi_n` of `t`):
    /// `Re(x) = c_0 + sum_{i >= 1} (c_i / 2) D_i(t)`. For a real element this is the
    /// element itself, written in the power basis of the real subfield.
    pub fn real_part_polynomial(&self) -> Polynomial<Rational> {
        let dickson = dickson_polynomials(self.coefficients.len().saturating_sub(1));
        let half = Rational::new(BigInt::one(), BigInt::from(2));
        let mut g = Polynomial::constant(self.coefficients.first().cloned().unwrap_or_else(r_zero));
        for (c, d) in self.coefficients.iter().zip(&dickson).skip(1) {
            g = g.add(&d.scale(&(c * &half)));
        }
        // Psi_n is monic, so the division cannot refuse; a refusal would leave `g` as is.
        g.rem(self.context.min_poly()).unwrap_or(g)
    }

    /// `g(t)` with `t = zeta + zeta^{-1}`: the element of `Q(zeta_n)^+` with these
    /// coordinates in the power basis of the real subfield.
    pub fn from_real_polynomial(
        conductor: usize,
        g: &Polynomial<Rational>,
    ) -> Result<Self, CyclotomicError> {
        let zeta = Self::zeta(conductor, 1)?;
        let t = zeta.zip_same_field(&zeta.conjugate(), |a, b| a + b);
        Ok(t.eval_polynomial(g))
    }

    /// `p(self)` for a polynomial `p` over `Q`, by Horner's rule in the field.
    pub fn eval_polynomial(&self, p: &Polynomial<Rational>) -> Self {
        let mut acc = Self::in_context(&self.context, vec![r_zero(); self.context.degree]);
        for c in p.coefficients().iter().rev() {
            let mut next = acc.mul_same_field(self);
            if let Some(first) = next.coefficients.first_mut() {
                *first += c;
            }
            acc = next;
        }
        acc
    }

    /// The image of `self` in `Q(zeta_m)` under `zeta_n -> zeta_m^{m/n}`, for `n | m`.
    pub fn lift(&self, m: usize) -> Result<Self, CyclotomicError> {
        let target = context(m)?;
        let n = self.conductor();
        if m % n != 0 {
            return Err(CyclotomicError::ConductorMismatch { left: n, right: m });
        }
        // m <= MAX_CONDUCTOR: the conversions are lossless.
        let step = (m / n) as i64;
        let mut coefficients = vec![r_zero(); target.degree];
        for (i, c) in self.coefficients.iter().enumerate() {
            if c.is_zero() {
                continue;
            }
            for (slot, p) in coefficients.iter_mut().zip(target.zeta(i as i64 * step)) {
                if !p.is_zero() {
                    *slot += c * p;
                }
            }
        }
        Ok(Self {
            context: target,
            coefficients,
        })
    }
}

// ---------------------------------------------------------------------------
// Quantum integers, Gauss sums, square roots
// ---------------------------------------------------------------------------

/// The quantum integer `[k]_q = q^{k-1} + q^{k-3} + ... + q^{-(k-1)}` at `q = zeta_n`,
/// with `[0] = 0` and `[-k] = -[k]`. It equals `(q^k - q^{-k}) / (q - q^{-1})` whenever
/// `q != +-1`, and is defined (as `k` and `(-1)^{k-1} k`) when `q = +-1`.
pub fn quantum_integer(conductor: usize, k: i64) -> Result<CyclotomicNumber, CyclotomicError> {
    let magnitude = k.unsigned_abs();
    if magnitude > MAX_QUANTUM_INDEX {
        return Err(CyclotomicError::QuantumIndexTooLarge {
            index: magnitude,
            max: MAX_QUANTUM_INDEX,
        });
    }
    let context = context(conductor)?;
    let mut total = vec![r_zero(); context.degree];
    // magnitude <= MAX_QUANTUM_INDEX: lossless.
    let top = magnitude as i64;
    for j in 0..top {
        for (slot, p) in total.iter_mut().zip(context.zeta(top - 1 - 2 * j)) {
            *slot += p;
        }
    }
    let number = CyclotomicNumber::in_context(&context, total);
    Ok(if k < 0 { number.neg() } else { number })
}

/// The quadratic Gauss sum `g_p = sum_{x = 0}^{p-1} zeta_p^{x^2}` for an odd prime `p`
/// dividing `n`, inside `Q(zeta_n)`, where `zeta_p = zeta_n^{n/p}`.
///
/// Gauss's theorem fixes its value under the canonical embedding: `g_p = sqrt(p)` for
/// `p = 1 (mod 4)` and `g_p = i sqrt(p)` for `p = 3 (mod 4)`.
pub fn gauss_sum(conductor: usize, p: usize) -> Result<CyclotomicNumber, CyclotomicError> {
    let context = context(conductor)?;
    let odd_prime = p >= 3 && distinct_prime_factors(p) == vec![p];
    if !odd_prime || conductor % p != 0 {
        return Err(CyclotomicError::NotAGaussSumModulus {
            prime: p,
            conductor,
        });
    }
    let step = conductor / p;
    let mut total = vec![r_zero(); context.degree];
    for x in 0..p {
        // x < p <= conductor and step <= conductor: the product is below 2^20.
        let exponent = (((x * x) % p) * step) as i64;
        for (slot, power) in total.iter_mut().zip(context.zeta(exponent)) {
            *slot += power;
        }
    }
    Ok(CyclotomicNumber::in_context(&context, total))
}

/// The conductor of the quadratic field `Q(sqrt f)` for a squarefree integer `f`:
/// `|f|` when `f = 1 (mod 4)`, else `4 |f|` (and `1` for `f = 1`).
pub fn quadratic_field_conductor(squarefree: &BigInt) -> BigInt {
    if squarefree.is_one() {
        return BigInt::one();
    }
    if squarefree.mod_floor(&BigInt::from(4)) == BigInt::one() {
        squarefree.abs()
    } else {
        BigInt::from(4) * squarefree.abs()
    }
}

fn prime_sqrt_factor(
    context: &Arc<CyclotomicContext>,
    conductor: usize,
    p: usize,
) -> Result<CyclotomicNumber, CyclotomicError> {
    if p == 2 {
        let zeta8 = CyclotomicNumber::in_context(context, context.zeta((conductor / 8) as i64));
        Ok(zeta8.zip_same_field(&zeta8.conjugate(), |a, b| a + b))
    } else {
        gauss_sum(conductor, p)
    }
}

fn apply_i_power(
    context: &Arc<CyclotomicContext>,
    root: CyclotomicNumber,
    i_exponent: i64,
) -> Option<CyclotomicNumber> {
    match i_exponent {
        0 => Some(root),
        2 => Some(root.neg()),
        odd => {
            if context.conductor % 4 != 0 {
                return None;
            }
            let i = CyclotomicNumber::in_context(
                context,
                context.zeta((context.conductor / 4) as i64 * odd),
            );
            Some(root.mul_same_field(&i))
        }
    }
}

fn squarefree_cyclotomic_sqrt(
    context: &Arc<CyclotomicContext>,
    conductor: usize,
    f: &BigInt,
) -> Result<Option<CyclotomicNumber>, CyclotomicError> {
    let mut root = CyclotomicNumber::one(conductor)?;
    let mut odd_primes_3_mod_4 = 0i64;
    let f_magnitude = usize::try_from(f.abs())
        .map_err(|_| CyclotomicError::Inconsistent("a squarefree part dividing n is small"))?;
    for p in distinct_prime_factors(f_magnitude) {
        if p != 2 && p % 4 == 3 {
            odd_primes_3_mod_4 += 1;
        }
        let factor = prime_sqrt_factor(context, conductor, p)?;
        root = root.mul_same_field(&factor);
    }
    let i_exponent = (i64::from(f.is_negative()) - odd_primes_3_mod_4).rem_euclid(4);
    Ok(apply_i_power(context, root, i_exponent))
}

/// The canonical square root of the nonzero integer `d` inside `Q(zeta_n)`: for `d > 0`
/// the element that is the positive real `sqrt(d)` under `zeta_n = e^{2 pi i/n}`, and for
/// `d < 0` the element `i sqrt(|d|)` with positive imaginary part. It exists exactly when
/// the conductor of `Q(sqrt d)` divides `n` (Kronecker-Weber); otherwise
/// [`CyclotomicError::NoSquareRoot`].
///
/// For `d = f s^2` with `f` squarefree, `sqrt(d) = s sqrt(f)`, and `sqrt(f)` is the product
/// of `zeta_8 + zeta_8^{-1}` (for the prime 2) and the Gauss sums `g_p` of the odd primes
/// of `f`, times the power of `i` that removes the `i` carried by each `p = 3 (mod 4)`
/// and adds the one of a negative `f`. The result is checked to square to `d`.
pub fn sqrt_of_integer(conductor: usize, d: &BigInt) -> Result<CyclotomicNumber, CyclotomicError> {
    check_conductor(conductor)?;
    if d.is_zero() {
        return CyclotomicNumber::zero(conductor);
    }
    let (f, s) = squarefree_part(d)?;
    let required = quadratic_field_conductor(&f);
    if !(BigInt::from(conductor) % &required).is_zero() {
        return Err(CyclotomicError::NoSquareRoot {
            d: d.clone(),
            squarefree: f,
            conductor,
            required,
        });
    }
    let context = context(conductor)?;
    // |f| divides the conductor (it divides `required`, which divides n), so it is small.
            // sqrt 2 = zeta_8 + zeta_8^{-1}; 8 | n because f is even, so 4|f| divides n.
    // Each p = 3 (mod 4) contributes an i; a negative f contributes one more.
    let Some(root) = squarefree_cyclotomic_sqrt(&context, conductor, &f)? else {
        return Err(CyclotomicError::NoSquareRoot {
            d: d.clone(),
            squarefree: f,
            conductor,
            required,
        });
    };
    let root = root.scale(&Rational::from_integer(s));
    let expected = CyclotomicNumber::from_rational(conductor, Rational::from_integer(d.clone()))?;
    if root.mul_same_field(&root) != expected {
        return Err(CyclotomicError::Inconsistent(
            "the constructed square root does not square to d",
        ));
    }
    Ok(root)
}

// ---------------------------------------------------------------------------
// Cyclotomic<N>: compile-time conductor, scalar tower
// ---------------------------------------------------------------------------

/// An element of `Q(zeta_N)` with the conductor fixed at compile time. `N` must satisfy
/// `1 <= N <= MAX_CONDUCTOR`; any other `N` does not compile. Implements the
/// `linear_algebra::scalars` tower, the `std::ops` operators, `Zero` and `One`.
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Cyclotomic<const N: usize>(CyclotomicNumber);

impl<const N: usize> std::fmt::Debug for Cyclotomic<N> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl<const N: usize> std::fmt::Display for Cyclotomic<N> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl<const N: usize> Serialize for Cyclotomic<N> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        self.0.serialize(serializer)
    }
}

impl<'de, const N: usize> Deserialize<'de> for Cyclotomic<N> {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let number = CyclotomicNumber::deserialize(deserializer)?;
        Self::try_from(number).map_err(serde::de::Error::custom)
    }
}

impl<const N: usize> From<Cyclotomic<N>> for CyclotomicNumber {
    fn from(value: Cyclotomic<N>) -> Self {
        value.0
    }
}

impl<const N: usize> TryFrom<CyclotomicNumber> for Cyclotomic<N> {
    type Error = CyclotomicError;
    fn try_from(number: CyclotomicNumber) -> Result<Self, CyclotomicError> {
        let () = Self::VALID;
        if number.conductor() != N {
            return Err(CyclotomicError::ConductorMismatch {
                left: number.conductor(),
                right: N,
            });
        }
        Ok(Self(number))
    }
}

impl<const N: usize> Cyclotomic<N> {
    const VALID: () = assert!(
        N >= 1 && N <= MAX_CONDUCTOR,
        "Cyclotomic<N> needs a conductor 1 <= N <= MAX_CONDUCTOR"
    );

    /// The conductor.
    pub const CONDUCTOR: usize = N;

    fn ctx() -> Arc<CyclotomicContext> {
        let () = Self::VALID;
        context(N).expect("N is validated by Self::VALID in this function")
    }

    /// The underlying run-time element.
    pub fn as_number(&self) -> &CyclotomicNumber {
        &self.0
    }

    pub fn zero() -> Self {
        let context = Self::ctx();
        let coefficients = vec![r_zero(); context.degree];
        Self(CyclotomicNumber::in_context(&context, coefficients))
    }

    pub fn one() -> Self {
        Self::rational(r_one())
    }

    /// The rational `q`.
    pub fn rational(q: Rational) -> Self {
        let context = Self::ctx();
        let mut coefficients = vec![r_zero(); context.degree];
        if let Some(first) = coefficients.first_mut() {
            *first = q;
        }
        Self(CyclotomicNumber::in_context(&context, coefficients))
    }

    /// `zeta_N^k` for any integer `k`.
    pub fn zeta(k: i64) -> Self {
        let context = Self::ctx();
        let coefficients = context.zeta(k);
        Self(CyclotomicNumber::in_context(&context, coefficients))
    }

    pub fn coefficients(&self) -> &[Rational] {
        &self.0.coefficients
    }

    pub fn is_zero(&self) -> bool {
        self.0.is_zero()
    }

    pub fn is_rational(&self) -> bool {
        self.0.is_rational()
    }

    pub fn as_rational(&self) -> Option<Rational> {
        self.0.as_rational()
    }

    pub fn add(&self, other: &Self) -> Self {
        Self(self.0.zip_same_field(&other.0, |a, b| a + b))
    }

    pub fn sub(&self, other: &Self) -> Self {
        Self(self.0.zip_same_field(&other.0, |a, b| a - b))
    }

    pub fn neg(&self) -> Self {
        Self(self.0.neg())
    }

    pub fn scale(&self, c: &Rational) -> Self {
        Self(self.0.scale(c))
    }

    pub fn mul(&self, other: &Self) -> Self {
        Self(self.0.mul_same_field(&other.0))
    }

    pub fn pow(&self, n: u32) -> Self {
        Self(self.0.pow(n))
    }

    /// `1 / self`, or `None` for zero.
    pub fn inverse(&self) -> Option<Self> {
        Some(Self(self.0.inverse()?))
    }

    /// Complex conjugation, `zeta -> zeta^{-1}`.
    pub fn conjugate(&self) -> Self {
        Self(self.0.conjugate())
    }

    /// The Galois automorphism `sigma_k`, for `k` coprime to `N`.
    pub fn galois(&self, k: i64) -> Result<Self, CyclotomicError> {
        Ok(Self(self.0.galois(k)?))
    }

    pub fn is_real(&self) -> bool {
        self.0.is_real()
    }

    pub fn trace(&self) -> Rational {
        self.0.trace()
    }

    pub fn norm(&self) -> Rational {
        self.0.norm()
    }
}

impl<const N: usize> std::ops::Add for Cyclotomic<N> {
    type Output = Cyclotomic<N>;
    fn add(self, rhs: Cyclotomic<N>) -> Cyclotomic<N> {
        Cyclotomic::add(&self, &rhs)
    }
}
impl<'a, 'b, const N: usize> std::ops::Add<&'b Cyclotomic<N>> for &'a Cyclotomic<N> {
    type Output = Cyclotomic<N>;
    fn add(self, rhs: &'b Cyclotomic<N>) -> Cyclotomic<N> {
        Cyclotomic::add(self, rhs)
    }
}
impl<const N: usize> std::ops::Sub for Cyclotomic<N> {
    type Output = Cyclotomic<N>;
    fn sub(self, rhs: Cyclotomic<N>) -> Cyclotomic<N> {
        Cyclotomic::sub(&self, &rhs)
    }
}
impl<'a, 'b, const N: usize> std::ops::Sub<&'b Cyclotomic<N>> for &'a Cyclotomic<N> {
    type Output = Cyclotomic<N>;
    fn sub(self, rhs: &'b Cyclotomic<N>) -> Cyclotomic<N> {
        Cyclotomic::sub(self, rhs)
    }
}
impl<const N: usize> std::ops::Mul for Cyclotomic<N> {
    type Output = Cyclotomic<N>;
    fn mul(self, rhs: Cyclotomic<N>) -> Cyclotomic<N> {
        Cyclotomic::mul(&self, &rhs)
    }
}
impl<'a, 'b, const N: usize> std::ops::Mul<&'b Cyclotomic<N>> for &'a Cyclotomic<N> {
    type Output = Cyclotomic<N>;
    fn mul(self, rhs: &'b Cyclotomic<N>) -> Cyclotomic<N> {
        Cyclotomic::mul(self, rhs)
    }
}
impl<const N: usize> std::ops::Neg for Cyclotomic<N> {
    type Output = Cyclotomic<N>;
    fn neg(self) -> Cyclotomic<N> {
        Cyclotomic::neg(&self)
    }
}
impl<'a, const N: usize> std::ops::Neg for &'a Cyclotomic<N> {
    type Output = Cyclotomic<N>;
    fn neg(self) -> Cyclotomic<N> {
        Cyclotomic::neg(self)
    }
}

impl<const N: usize> Zero for Cyclotomic<N> {
    fn zero() -> Self {
        Cyclotomic::zero()
    }
    fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

impl<const N: usize> One for Cyclotomic<N> {
    fn one() -> Self {
        Cyclotomic::one()
    }
}

impl<const N: usize> linear_algebra::scalars::Semiring for Cyclotomic<N> {
    fn zero() -> Self {
        Cyclotomic::zero()
    }
    fn one() -> Self {
        Cyclotomic::one()
    }
    fn add(&self, rhs: &Self) -> Self {
        Cyclotomic::add(self, rhs)
    }
    fn mul(&self, rhs: &Self) -> Self {
        Cyclotomic::mul(self, rhs)
    }
    fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

impl<const N: usize> linear_algebra::scalars::Ring for Cyclotomic<N> {
    fn neg(&self) -> Self {
        Cyclotomic::neg(self)
    }
}

impl<const N: usize> linear_algebra::scalars::Field for Cyclotomic<N> {
    fn try_inv(&self) -> Option<Self> {
        self.inverse()
    }
}

impl<const N: usize> linear_algebra::scalars::ExactRing for Cyclotomic<N> {}

// ---------------------------------------------------------------------------
// Conversions with the fixed-conductor types
// ---------------------------------------------------------------------------

/// The shared context of a fixed conductor that is known to be within `MAX_CONDUCTOR`.
fn fixed_context(conductor: usize) -> Arc<CyclotomicContext> {
    context(conductor).expect("fixed conductors are literals within MAX_CONDUCTOR")
}

macro_rules! fixed_conductor_conversions {
    ($ty:ty, $conductor:expr, $len:expr) => {
        impl From<&$ty> for CyclotomicNumber {
            fn from(value: &$ty) -> Self {
                CyclotomicNumber::in_context(&fixed_context($conductor), value.a.to_vec())
            }
        }

        impl TryFrom<&CyclotomicNumber> for $ty {
            type Error = CyclotomicError;
            fn try_from(number: &CyclotomicNumber) -> Result<Self, CyclotomicError> {
                if number.conductor() != $conductor {
                    return Err(CyclotomicError::ConductorMismatch {
                        left: number.conductor(),
                        right: $conductor,
                    });
                }
                if number.coefficients.len() != $len {
                    return Err(CyclotomicError::CoefficientCount {
                        conductor: $conductor,
                        expected: $len,
                        actual: number.coefficients.len(),
                    });
                }
                Ok(Self {
                    a: std::array::from_fn(|i| {
                        number.coefficients.get(i).cloned().unwrap_or_else(r_zero)
                    }),
                })
            }
        }
    };
}

fixed_conductor_conversions!(Cyc5, 5, 4);
fixed_conductor_conversions!(Cyc8, 8, 4);
fixed_conductor_conversions!(Cyc12, 12, 4);
fixed_conductor_conversions!(Cyc24, 24, 8);
fixed_conductor_conversions!(Cyc28, 28, 12);
fixed_conductor_conversions!(Cyc44, 44, 20);
fixed_conductor_conversions!(Cyc52, 52, 24);
fixed_conductor_conversions!(Cyc120, 120, 32);

impl From<&GaussianRat> for CyclotomicNumber {
    /// `a + b i` is `a + b zeta_4`.
    fn from(value: &GaussianRat) -> Self {
        CyclotomicNumber::in_context(&fixed_context(4), vec![value.re.clone(), value.im.clone()])
    }
}

impl TryFrom<&CyclotomicNumber> for GaussianRat {
    type Error = CyclotomicError;
    fn try_from(number: &CyclotomicNumber) -> Result<Self, CyclotomicError> {
        if number.conductor() != 4 {
            return Err(CyclotomicError::ConductorMismatch {
                left: number.conductor(),
                right: 4,
            });
        }
        let coefficient = |i: usize| number.coefficients.get(i).cloned().unwrap_or_else(r_zero);
        Ok(GaussianRat {
            re: coefficient(0),
            im: coefficient(1),
        })
    }
}

impl From<&EisensteinRat> for CyclotomicNumber {
    /// `a + b zeta_3`.
    fn from(value: &EisensteinRat) -> Self {
        CyclotomicNumber::in_context(&fixed_context(3), vec![value.a.clone(), value.b.clone()])
    }
}

impl TryFrom<&CyclotomicNumber> for EisensteinRat {
    type Error = CyclotomicError;
    fn try_from(number: &CyclotomicNumber) -> Result<Self, CyclotomicError> {
        if number.conductor() != 3 {
            return Err(CyclotomicError::ConductorMismatch {
                left: number.conductor(),
                right: 3,
            });
        }
        let coefficient = |i: usize| number.coefficients.get(i).cloned().unwrap_or_else(r_zero);
        Ok(EisensteinRat {
            a: coefficient(0),
            b: coefficient(1),
        })
    }
}

// Origin: engine/crates_rs/core_number_theory/src/cyclotomic_field.rs
// Claim: urn:core:crates_rs:core-number-theory:cyclotomic-field:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::polynomial::divisors;
    use crate::rational::{ri, rq};
    use crate::scalar::RationalEmbedding;
    use crate::test_support::{check_field_axioms, Lcg};
    use linear_algebra::exact_field::involution::Involution;

    fn num(n: usize, coefficients: &[i64]) -> CyclotomicNumber {
        let degree = euler_phi(n);
        let mut c: Vec<Rational> = coefficients.iter().map(|&x| ri(x)).collect();
        c.resize(degree, r_zero());
        CyclotomicNumber::from_coefficients(n, c).unwrap()
    }

    /// A deterministic grid element of Q(zeta_n) with small rational coefficients.
    fn grid_element(n: usize, rng: &mut Lcg) -> CyclotomicNumber {
        let degree = euler_phi(n);
        let coefficients = (0..degree)
            .map(|_| rq(rng.next_signed(4), 1 + rng.next_below(3) as i64))
            .collect();
        CyclotomicNumber::from_coefficients(n, coefficients).unwrap()
    }

    fn gcd_i64(a: i64, b: i64) -> i64 {
        a.gcd(&b)
    }

    fn one(n: usize) -> CyclotomicNumber {
        CyclotomicNumber::one(n).unwrap()
    }

    fn zeta(n: usize, k: i64) -> CyclotomicNumber {
        CyclotomicNumber::zeta(n, k).unwrap()
    }

    // ----- Psi_n: the minimal polynomial of 2cos(2 pi / n) ---------------------

    #[test]
    fn min_poly_of_2cos_matches_the_known_table() {
        let table: [(usize, &[i64]); 13] = [
            (1, &[-2, 1]),
            (2, &[2, 1]),
            (3, &[1, 1]),
            (4, &[0, 1]),
            (5, &[-1, 1, 1]),
            (6, &[-1, 1]),
            (7, &[-1, -2, 1, 1]),
            (8, &[-2, 0, 1]),
            (9, &[1, -3, 0, 1]),
            (12, &[-3, 0, 1]),
            (16, &[2, 0, -4, 0, 1]),
            (20, &[5, 0, -5, 0, 1]),
            (24, &[1, 0, -4, 0, 1]),
        ];
        for (n, coefficients) in table {
            assert_eq!(
                min_poly_of_2cos(n).unwrap(),
                Polynomial::from_i64s(coefficients),
                "Psi_{n}"
            );
        }
        assert_eq!(
            min_poly_of_2cos(15).unwrap(),
            Polynomial::from_i64s(&[1, 4, -4, -1, 1])
        );
        // The degree-16 polynomial of conductor 120 that an old table hard-coded.
        assert_eq!(
            min_poly_of_2cos(120).unwrap(),
            Polynomial::from_i64s(&[
                1, 0, -96, 0, 440, 0, -784, 0, 714, 0, -364, 0, 105, 0, -16, 0, 1
            ])
        );
    }

    #[test]
    fn t_is_a_root_of_psi_and_psi_has_degree_phi_over_two() {
        for n in 1..=60usize {
            let psi = min_poly_of_2cos(n).unwrap();
            let expected_degree = if n <= 2 { 1 } else { euler_phi(n) / 2 };
            assert_eq!(psi.degree(), Some(expected_degree), "deg Psi_{n}");
            assert_eq!(psi.leading_coefficient(), Some(&r_one()), "monic Psi_{n}");
            let z = zeta(n, 1);
            let t = z.add(&z.conjugate()).unwrap();
            assert!(
                t.eval_polynomial(&psi).is_zero(),
                "Psi_{n}(zeta + zeta^-1) = 0"
            );
        }
    }

    #[test]
    fn psi_is_the_palindromic_reduction_of_phi() {
        // Phi_n(x) = x^m Psi_n(x + 1/x): check by evaluating both sides at rational x.
        for n in [5usize, 7, 8, 9, 12, 15, 24, 30] {
            let phi = cyclotomic_polynomial(n).unwrap();
            let psi = min_poly_of_2cos(n).unwrap();
            let m = euler_phi(n) / 2;
            for x in [ri(2), rq(3, 2), ri(-5), rq(-1, 3)] {
                let t = &x + x.recip();
                let x_m = (0..m).fold(r_one(), |acc, _| acc * &x);
                assert_eq!(phi.eval(&x), x_m * psi.eval(&t), "n = {n}, x = {x}");
            }
        }
    }

    // ----- field structure -------------------------------------------------------

    #[test]
    fn zeta_has_exact_order_n_and_the_roots_sum_to_zero() {
        for n in 1..=36usize {
            let z = zeta(n, 1);
            let n_u32 = u32::try_from(n).unwrap();
            assert_eq!(z.pow(n_u32), one(n), "zeta^n = 1 for n = {n}");
            for k in 1..n_u32 {
                assert_ne!(z.pow(k), one(n), "zeta^{k} != 1 for n = {n}");
            }
            let sum = (0..i64::try_from(n).unwrap())
                .fold(CyclotomicNumber::zero(n).unwrap(), |acc, k| {
                    acc.add(&zeta(n, k)).unwrap()
                });
            assert_eq!(sum.is_zero(), n > 1, "sum of n-th roots of unity, n = {n}");
            if n % 2 == 0 {
                assert_eq!(
                    zeta(n, i64::try_from(n / 2).unwrap()),
                    CyclotomicNumber::from_rational(n, ri(-1)).unwrap(),
                    "zeta^(n/2) = -1 for n = {n}"
                );
            }
        }
    }

    #[test]
    fn zeta_power_follows_the_group_law_including_negative_exponents() {
        let n = 12;
        for j in -15i64..15 {
            for k in -15i64..15 {
                let product = zeta(n, j).mul(&zeta(n, k)).unwrap();
                assert_eq!(product, zeta(n, j + k), "zeta^{j} zeta^{k}");
            }
        }
    }

    #[test]
    fn phi_n_vanishes_at_zeta_and_no_smaller_cyclotomic_polynomial_does() {
        for n in 1..=30usize {
            let z = zeta(n, 1);
            let phi = cyclotomic_polynomial(n).unwrap();
            assert!(z.eval_polynomial(&phi).is_zero(), "Phi_{n}(zeta) = 0");
            for d in divisors(n).into_iter().filter(|d| *d < n) {
                let other = cyclotomic_polynomial(d).unwrap();
                assert!(
                    !z.eval_polynomial(&other).is_zero(),
                    "Phi_{d}(zeta_{n}) != 0"
                );
            }
        }
    }

    #[test]
    fn typed_fields_satisfy_the_field_axioms() {
        fn samples<const N: usize>() -> Vec<Cyclotomic<N>> {
            vec![
                Cyclotomic::zero(),
                Cyclotomic::one(),
                Cyclotomic::zeta(1),
                Cyclotomic::zeta(1).add(&Cyclotomic::rational(rq(1, 2))),
                Cyclotomic::zeta(2).sub(&Cyclotomic::zeta(-1)),
            ]
        }
        check_field_axioms(&samples::<1>());
        check_field_axioms(&samples::<2>());
        check_field_axioms(&samples::<3>());
        check_field_axioms(&samples::<4>());
        check_field_axioms(&samples::<5>());
        check_field_axioms(&samples::<7>());
        check_field_axioms(&samples::<8>());
        check_field_axioms(&samples::<9>());
        check_field_axioms(&samples::<12>());
        check_field_axioms(&samples::<15>());
        check_field_axioms(&samples::<24>());
    }

    #[test]
    fn inverse_agrees_with_the_shared_multiplication_matrix_solver() {
        // Independent route: power_basis::invert_by_multiplication_matrix solves M_x y = e_0.
        let mut rng = Lcg::new(31);
        for n in [5usize, 7, 8, 12, 15, 24] {
            for _ in 0..4 {
                let x = grid_element(n, &mut rng);
                if x.is_zero() {
                    continue;
                }
                let via_solver =
                    crate::power_basis::invert_by_multiplication_matrix(x.degree(), |j| {
                        x.mul(&zeta(n, i64::try_from(j).unwrap()))
                            .unwrap()
                            .coefficients()
                            .to_vec()
                    })
                    .expect("a nonzero element is invertible");
                let via_xgcd = x.inverse().unwrap();
                assert_eq!(via_xgcd.coefficients(), via_solver.as_slice(), "n = {n}");
                assert_eq!(x.mul(&via_xgcd).unwrap(), one(n));
            }
        }
        assert_eq!(CyclotomicNumber::zero(8).unwrap().inverse(), None);
    }

    #[test]
    fn checked_division_refuses_zero_and_mismatched_conductors() {
        let x = num(8, &[1, 1]);
        let zero = CyclotomicNumber::zero(8).unwrap();
        assert_eq!(x.checked_div(&zero), Err(CyclotomicError::DivisionByZero));
        let y = num(12, &[1, 1]);
        assert_eq!(
            x.checked_div(&y),
            Err(CyclotomicError::ConductorMismatch { left: 8, right: 12 })
        );
        assert_eq!(x.checked_div(&x).unwrap(), one(8));
    }

    #[test]
    fn operations_refuse_elements_of_different_fields() {
        let (a, b) = (num(5, &[1, 2]), num(8, &[1, 2]));
        let mismatch = CyclotomicError::ConductorMismatch { left: 5, right: 8 };
        assert_eq!(a.add(&b), Err(mismatch.clone()));
        assert_eq!(a.sub(&b), Err(mismatch.clone()));
        assert_eq!(a.mul(&b), Err(mismatch));
        // equal values in equal fields compare equal; the same coefficients in different
        assert_ne!(num(5, &[1, 2]), num(8, &[1, 2]));
        let a_same = num(5, &[1, 2]);
        assert_eq!(a, a_same);
    }

    #[test]
    fn construction_refuses_bad_conductors_and_coefficient_counts() {
        assert_eq!(
            CyclotomicNumber::zero(0),
            Err(CyclotomicError::ConductorZero)
        );
        assert_eq!(
            CyclotomicNumber::zero(MAX_CONDUCTOR + 1),
            Err(CyclotomicError::ConductorTooLarge {
                conductor: MAX_CONDUCTOR + 1,
                max: MAX_CONDUCTOR
            })
        );
        assert_eq!(
            CyclotomicNumber::from_coefficients(5, vec![ri(1), ri(2)]),
            Err(CyclotomicError::CoefficientCount {
                conductor: 5,
                expected: 4,
                actual: 2
            })
        );
        assert!(CyclotomicNumber::from_rational(MAX_CONDUCTOR, ri(1)).is_ok());
    }

    #[test]
    fn polynomials_reduce_modulo_phi_and_round_trip() {
        // zeta_5^4 = -1 - zeta - zeta^2 - zeta^3
        let p = Polynomial::from_i64s(&[0, 0, 0, 0, 1]);
        assert_eq!(
            CyclotomicNumber::from_polynomial(5, &p).unwrap(),
            num(5, &[-1, -1, -1, -1])
        );
        let x = num(12, &[1, -2, 3, 5]);
        assert_eq!(
            CyclotomicNumber::from_polynomial(12, &x.to_polynomial()).unwrap(),
            x
        );
        assert_eq!(
            CyclotomicNumber::from_polynomial(5, &cyclotomic_polynomial(5).unwrap()).unwrap(),
            CyclotomicNumber::zero(5).unwrap()
        );
    }

    // ----- conjugation and Galois ------------------------------------------------

    #[test]
    fn conjugation_is_an_involutive_ring_automorphism_fixing_the_real_subfield() {
        let mut rng = Lcg::new(7);
        for n in [3usize, 5, 7, 8, 9, 12, 15, 24] {
            assert_eq!(zeta(n, 1).conjugate(), zeta(n, -1), "conj zeta = zeta^-1");
            for _ in 0..4 {
                let (x, y) = (grid_element(n, &mut rng), grid_element(n, &mut rng));
                assert_eq!(x.conjugate().conjugate(), x);
                assert_eq!(
                    x.mul(&y).unwrap().conjugate(),
                    x.conjugate().mul(&y.conjugate()).unwrap()
                );
                assert_eq!(
                    x.add(&y).unwrap().conjugate(),
                    x.conjugate().add(&y.conjugate()).unwrap()
                );
                assert!(x.mul(&x.conjugate()).unwrap().is_real());
                assert!(x.add(&x.conjugate()).unwrap().is_real());
                assert!(x.real_part().is_real());
                assert_eq!(x.real_part().real_part(), x.real_part());
            }
        }
        assert!(!zeta(5, 1).is_real());
        assert!(CyclotomicNumber::from_rational(5, rq(2, 3))
            .unwrap()
            .is_real());
        assert!(zeta(2, 1).is_real(), "n = 2: every element is real");
        assert!(zeta(1, 1).is_real(), "n = 1: every element is real");
    }

    #[test]
    fn galois_automorphisms_compose_like_the_unit_group() {
        let n = 15;
        let mut rng = Lcg::new(13);
        let x = grid_element(n, &mut rng);
        let units: Vec<i64> = (1..15).filter(|k| gcd_i64(*k, 15) == 1).collect();
        assert_eq!(units.len(), euler_phi(15));
        for &j in &units {
            assert_eq!(
                zeta(n, 1).galois(j).unwrap(),
                zeta(n, j),
                "sigma_j(zeta) = zeta^j"
            );
            for &k in &units {
                let composed = x.galois(k).unwrap().galois(j).unwrap();
                assert_eq!(
                    composed,
                    x.galois(j * k).unwrap(),
                    "sigma_j sigma_k = sigma_jk"
                );
            }
            let y = grid_element(n, &mut rng);
            assert_eq!(
                x.mul(&y).unwrap().galois(j).unwrap(),
                x.galois(j).unwrap().mul(&y.galois(j).unwrap()).unwrap()
            );
        }
        assert_eq!(x.galois(-1).unwrap(), x.conjugate());
        assert_eq!(x.galois(14).unwrap(), x.conjugate());
        assert_eq!(x.galois(1).unwrap(), x);
    }

    #[test]
    fn galois_refuses_exponents_that_share_a_factor_with_the_conductor() {
        let x = num(15, &[1, 1]);
        for k in [0i64, 3, 5, 6, 9, 10, 12, 15, 30] {
            assert_eq!(
                x.galois(k),
                Err(CyclotomicError::NotCoprime { k, conductor: 15 }),
                "k = {k}"
            );
        }
    }

    #[test]
    fn the_orbit_of_zeta_has_exactly_phi_n_distinct_members() {
        for n in [5usize, 8, 12, 15, 24] {
            let z = zeta(n, 1);
            let mut orbit: Vec<CyclotomicNumber> = (1..i64::try_from(n).unwrap())
                .filter_map(|k| z.galois(k).ok())
                .collect();
            assert_eq!(orbit.len(), euler_phi(n));
            orbit.sort_by_key(|a| format!("{a}"));
            orbit.dedup();
            assert_eq!(orbit.len(), euler_phi(n), "distinct conjugates for n = {n}");
        }
    }

    // ----- trace and norm --------------------------------------------------------

    /// The multiplication-by-x matrix in the power basis, as integers scaled by a common
    /// denominator (test-only independent route for trace and norm).
    fn scaled_multiplication_matrix(x: &CyclotomicNumber) -> (BigInt, Vec<Vec<BigInt>>) {
        let n = x.conductor();
        let d = x.degree();
        let columns: Vec<Vec<Rational>> = (0..d)
            .map(|j| {
                x.mul(&zeta(n, i64::try_from(j).unwrap()))
                    .unwrap()
                    .coefficients()
                    .to_vec()
            })
            .collect();
        let denominator = columns
            .iter()
            .flatten()
            .fold(BigInt::one(), |acc, c| acc.lcm(c.denom()));
        let matrix = (0..d)
            .map(|i| {
                (0..d)
                    .map(|j| columns[j][i].numer() * (&denominator / columns[j][i].denom()))
                    .collect()
            })
            .collect();
        (denominator, matrix)
    }

    #[test]
    fn trace_agrees_with_the_galois_orbit_sum_and_the_matrix_trace() {
        let mut rng = Lcg::new(21);
        for n in [3usize, 4, 5, 7, 8, 9, 12, 15, 24] {
            let n_i64 = i64::try_from(n).unwrap();
            for _ in 0..3 {
                let x = grid_element(n, &mut rng);
                let orbit_sum = (1..n_i64)
                    .filter(|k| gcd_i64(*k, n_i64) == 1)
                    .fold(CyclotomicNumber::zero(n).unwrap(), |acc, k| {
                        acc.add(&x.galois(k).unwrap()).unwrap()
                    });
                assert_eq!(orbit_sum.as_rational(), Some(x.trace()), "n = {n}");
                let (denominator, matrix) = scaled_multiplication_matrix(&x);
                let diagonal: BigInt = (0..matrix.len()).map(|i| matrix[i][i].clone()).sum();
                assert_eq!(x.trace(), Rational::new(diagonal, denominator), "n = {n}");
            }
            assert_eq!(
                one(n).trace(),
                ri(i64::try_from(euler_phi(n)).unwrap()),
                "Tr(1) = phi"
            );
            assert_eq!(
                zeta(n, 1).trace(),
                ri(i64::from(mobius(n))),
                "Tr(zeta) = mu(n)"
            );
        }
    }

    #[test]
    fn trace_is_additive_and_rational_linear() {
        let mut rng = Lcg::new(25);
        for n in [5usize, 8, 12] {
            let (x, y) = (grid_element(n, &mut rng), grid_element(n, &mut rng));
            assert_eq!(x.add(&y).unwrap().trace(), x.trace() + y.trace());
            assert_eq!(x.scale(&rq(3, 5)).trace(), x.trace() * rq(3, 5));
        }
    }

    #[test]
    fn norm_agrees_with_the_galois_orbit_product_and_the_determinant() {
        let mut rng = Lcg::new(22);
        for n in [3usize, 4, 5, 7, 8, 12, 15] {
            let n_i64 = i64::try_from(n).unwrap();
            for _ in 0..3 {
                let x = grid_element(n, &mut rng);
                let orbit_product = (1..n_i64)
                    .filter(|k| gcd_i64(*k, n_i64) == 1)
                    .fold(one(n), |acc, k| acc.mul(&x.galois(k).unwrap()).unwrap());
                assert_eq!(orbit_product.as_rational(), Some(x.norm()), "n = {n}");
                let (denominator, matrix) = scaled_multiplication_matrix(&x);
                let det = linear_algebra::determinant::bareiss_determinant(&matrix).unwrap();
                let scale = denominator.pow(u32::try_from(x.degree()).unwrap());
                assert_eq!(x.norm(), Rational::new(det, scale), "n = {n}");
            }
        }
    }

    #[test]
    fn norm_is_multiplicative_and_takes_the_known_values() {
        let mut rng = Lcg::new(23);
        for n in [5usize, 8, 12] {
            let (x, y) = (grid_element(n, &mut rng), grid_element(n, &mut rng));
            assert_eq!(x.mul(&y).unwrap().norm(), x.norm() * y.norm());
        }
        // N(c) = c^phi(n)
        assert_eq!(
            CyclotomicNumber::from_rational(8, ri(3)).unwrap().norm(),
            ri(81)
        );
        // N(1 - zeta_n) = p for n = p^k, and 1 when n has two distinct prime factors
        let one_minus_zeta = |n: usize| one(n).sub(&zeta(n, 1)).unwrap();
        assert_eq!(one_minus_zeta(5).norm(), ri(5));
        assert_eq!(one_minus_zeta(8).norm(), ri(2));
        assert_eq!(one_minus_zeta(9).norm(), ri(3));
        assert_eq!(one_minus_zeta(12).norm(), ri(1));
        assert_eq!(one_minus_zeta(15).norm(), ri(1));
        // N(zeta) = 1 and N(a + b i) = a^2 + b^2 in Q(i)
        assert_eq!(zeta(7, 1).norm(), ri(1));
        assert_eq!(num(4, &[3, 4]).norm(), ri(25));
        assert!(CyclotomicNumber::zero(5).unwrap().norm().is_zero());
    }

    // ----- the real subfield -----------------------------------------------------

    #[test]
    fn real_part_polynomial_and_from_real_polynomial_are_inverse_on_real_elements() {
        let mut rng = Lcg::new(41);
        for n in [5usize, 7, 8, 9, 12, 15, 24] {
            for _ in 0..4 {
                let x = grid_element(n, &mut rng);
                let real = x.real_part();
                let g = real.real_part_polynomial();
                let m = euler_phi(n) / 2;
                assert!(
                    g.degree().unwrap_or(0) < m.max(1),
                    "deg g < phi/2 for n = {n}"
                );
                assert_eq!(
                    CyclotomicNumber::from_real_polynomial(n, &g).unwrap(),
                    real,
                    "g(t) reproduces the real part, n = {n}"
                );
                assert_eq!(
                    x.real_part_polynomial(),
                    g,
                    "the polynomial of x is the polynomial of Re(x)"
                );
            }
        }
        // n = 8: t = sqrt 2, and the real part of zeta_8 is sqrt2/2 = t/2
        assert_eq!(
            zeta(8, 1).real_part_polynomial(),
            Polynomial::from_coefficients(vec![r_zero(), rq(1, 2)])
        );
    }

    #[test]
    fn a_non_real_element_has_a_real_part_distinct_from_itself() {
        let z = zeta(5, 1);
        assert!(!z.is_real());
        assert_ne!(z.real_part(), z);
        assert!(z.real_part().is_real());
        // Re(zeta) + Re(zeta^2) = -1/2 for n = 5 (2 sum of the four real parts is -1)
        let sum = z.real_part().add(&zeta(5, 2).real_part()).unwrap();
        assert_eq!(sum.as_rational(), Some(rq(-1, 2)));
    }

    // ----- quantum integers ------------------------------------------------------

    #[test]
    fn quantum_integers_satisfy_the_q_difference_identity() {
        // [k](q - q^-1) = q^k - q^-k whenever q != +-1.
        for n in [3usize, 4, 5, 8, 12, 24] {
            let q_minus_inverse = zeta(n, 1).sub(&zeta(n, -1)).unwrap();
            for k in -8i64..=8 {
                let lhs = quantum_integer(n, k)
                    .unwrap()
                    .mul(&q_minus_inverse)
                    .unwrap();
                let rhs = zeta(n, k).sub(&zeta(n, -k)).unwrap();
                assert_eq!(lhs, rhs, "n = {n}, k = {k}");
            }
        }
    }

    #[test]
    fn quantum_integers_at_zeta_12_are_two_sin_k_pi_over_six() {
        // [k] = sin(k pi/6)/sin(pi/6) = 2 sin(k pi/6): 1, sqrt3, 2, sqrt3, 1, 0, -1, ...
        let sqrt3 = sqrt_of_integer(12, &BigInt::from(3)).unwrap();
        let expected = [
            one(12),
            sqrt3.clone(),
            CyclotomicNumber::from_rational(12, ri(2)).unwrap(),
            sqrt3,
            one(12),
            CyclotomicNumber::zero(12).unwrap(),
        ];
        for (index, value) in expected.iter().enumerate() {
            let k = i64::try_from(index).unwrap() + 1;
            assert_eq!(&quantum_integer(12, k).unwrap(), value, "[{k}]");
            assert_eq!(
                &quantum_integer(12, k + 6).unwrap(),
                &value.neg(),
                "[{}]",
                k + 6
            );
            assert_eq!(&quantum_integer(12, -k).unwrap(), &value.neg(), "[-{k}]");
        }
        assert!(quantum_integer(12, 0).unwrap().is_zero());
        // The form q^9 (q^k - q^-k) used by the finite spin-foam model agrees.
        let q9 = zeta(12, 9);
        for k in 0..=12i64 {
            let formula = q9.mul(&zeta(12, k).sub(&zeta(12, -k)).unwrap()).unwrap();
            assert_eq!(quantum_integer(12, k).unwrap(), formula, "k = {k}");
        }
    }

    #[test]
    fn quantum_integers_are_defined_at_q_equal_plus_or_minus_one() {
        // [k]_1 = k, [k]_{-1} = (-1)^{k-1} k
        for k in 0..=8i64 {
            assert_eq!(quantum_integer(1, k).unwrap().as_rational(), Some(ri(k)));
            let sign = if k % 2 == 1 { 1 } else { -1 };
            assert_eq!(
                quantum_integer(2, k).unwrap().as_rational(),
                Some(ri(sign * k))
            );
        }
    }

    #[test]
    fn quantum_integer_vanishes_at_index_m_when_q_is_a_primitive_2m_th_root() {
        for m in 2..=12usize {
            let m_i64 = i64::try_from(m).unwrap();
            assert!(
                quantum_integer(2 * m, m_i64).unwrap().is_zero(),
                "[m] at zeta_2m, m = {m}"
            );
            assert!(!quantum_integer(2 * m, m_i64 - 1).unwrap().is_zero());
        }
    }

    #[test]
    fn quantum_integer_refuses_absurd_indices() {
        assert_eq!(
            quantum_integer(5, i64::try_from(MAX_QUANTUM_INDEX).unwrap() + 1),
            Err(CyclotomicError::QuantumIndexTooLarge {
                index: MAX_QUANTUM_INDEX + 1,
                max: MAX_QUANTUM_INDEX
            })
        );
    }

    // ----- Gauss sums and square roots -------------------------------------------

    #[test]
    fn gauss_sums_square_to_plus_or_minus_p() {
        // g_p^2 = p for p = 1 (mod 4) and -p for p = 3 (mod 4); |g_p|^2 = p always.
        for p in [3usize, 5, 7, 11, 13] {
            let g = gauss_sum(p, p).unwrap();
            let p_i64 = i64::try_from(p).unwrap();
            let sign = if p % 4 == 1 { 1 } else { -1 };
            assert_eq!(
                g.mul(&g).unwrap().as_rational(),
                Some(ri(sign * p_i64)),
                "g_{p}^2"
            );
            assert_eq!(
                g.mul(&g.conjugate()).unwrap().as_rational(),
                Some(ri(p_i64)),
                "|g_{p}|^2"
            );
            assert_eq!(
                g.is_real(),
                p % 4 == 1,
                "g_p is real iff p = 1 (mod 4), p = {p}"
            );
        }
    }

    #[test]
    fn gauss_sum_refuses_non_primes_and_non_divisors() {
        for (n, p) in [(15usize, 9usize), (15, 2), (10, 10), (7, 3), (9, 1), (8, 4)] {
            assert_eq!(
                gauss_sum(n, p),
                Err(CyclotomicError::NotAGaussSumModulus {
                    prime: p,
                    conductor: n
                }),
                "n = {n}, p = {p}"
            );
        }
        assert!(gauss_sum(9, 3).is_ok());
        assert!(gauss_sum(15, 5).is_ok());
    }

    #[test]
    fn square_roots_of_integers_appear_exactly_when_the_quadratic_conductor_divides_n() {
        // (d, conductor of Q(sqrt d))
        let cases: [(i64, usize); 14] = [
            (2, 8),
            (3, 12),
            (5, 5),
            (7, 28),
            (6, 24),
            (10, 40),
            (-1, 4),
            (-2, 8),
            (-3, 3),
            (-5, 20),
            (-7, 7),
            (13, 13),
            (21, 21),
            (15, 60),
        ];
        for (d, conductor) in cases {
            let d = BigInt::from(d);
            assert_eq!(
                quadratic_field_conductor(&d),
                BigInt::from(conductor),
                "conductor of Q(sqrt {d})"
            );
            for n in 1..=120usize {
                let result = sqrt_of_integer(n, &d);
                if n % conductor == 0 {
                    let root = result.unwrap_or_else(|e| panic!("sqrt({d}) in Q(zeta_{n}): {e}"));
                    assert_eq!(
                        root.mul(&root).unwrap(),
                        CyclotomicNumber::from_rational(n, Rational::from_integer(d.clone()))
                            .unwrap(),
                        "sqrt({d})^2 = {d} in Q(zeta_{n})"
                    );
                } else {
                    assert!(
                        matches!(result, Err(CyclotomicError::NoSquareRoot { .. })),
                        "sqrt({d}) must not exist in Q(zeta_{n}) (conductor {conductor} does not divide {n})"
                    );
                }
            }
        }
    }

    #[test]
    fn square_roots_extract_square_factors_and_handle_perfect_squares() {
        let two = CyclotomicNumber::from_rational(24, ri(2)).unwrap();
        assert_eq!(
            sqrt_of_integer(24, &BigInt::from(8)).unwrap(),
            sqrt_of_integer(24, &BigInt::from(2))
                .unwrap()
                .mul(&two)
                .unwrap(),
            "sqrt 8 = 2 sqrt 2"
        );
        assert_eq!(
            sqrt_of_integer(24, &BigInt::from(12)).unwrap(),
            sqrt_of_integer(24, &BigInt::from(3))
                .unwrap()
                .mul(&two)
                .unwrap(),
            "sqrt 12 = 2 sqrt 3"
        );
        assert_eq!(
            sqrt_of_integer(3, &BigInt::from(9)).unwrap(),
            CyclotomicNumber::from_rational(3, ri(3)).unwrap(),
            "sqrt 9 = 3"
        );
        assert_eq!(
            sqrt_of_integer(4, &BigInt::from(-4)).unwrap(),
            zeta(4, 1).scale(&ri(2)),
            "sqrt(-4) = 2i"
        );
        assert_eq!(
            sqrt_of_integer(3, &BigInt::from(-12)).unwrap(),
            sqrt_of_integer(3, &BigInt::from(-3)).unwrap().scale(&ri(2)),
            "sqrt(-12) = 2 sqrt(-3)"
        );
        assert_eq!(sqrt_of_integer(1, &BigInt::from(1)).unwrap(), one(1));
        assert!(sqrt_of_integer(5, &BigInt::from(0)).unwrap().is_zero());
    }

    #[test]
    fn square_root_errors_name_the_required_conductor() {
        assert_eq!(
            sqrt_of_integer(7, &BigInt::from(2)).unwrap_err(),
            CyclotomicError::NoSquareRoot {
                d: BigInt::from(2),
                squarefree: BigInt::from(2),
                conductor: 7,
                required: BigInt::from(8)
            }
        );
        // sqrt 3 needs 12, not 6, although sqrt(-3) lives in Q(zeta_3)
        assert!(sqrt_of_integer(6, &BigInt::from(3)).is_err());
        assert!(sqrt_of_integer(3, &BigInt::from(-3)).is_ok());
        assert_eq!(
            sqrt_of_integer(0, &BigInt::from(2)),
            Err(CyclotomicError::ConductorZero)
        );
    }

    #[test]
    fn the_constructed_roots_match_the_hand_built_legacy_constants() {
        // Cyc8::sqrt2, Cyc24::sqrt2, Cyc24::sqrt3 and Cyc28's sqrt7 are built by other
        // formulas; the Gauss-sum construction must give the same elements.
        assert_eq!(
            sqrt_of_integer(8, &BigInt::from(2)).unwrap(),
            CyclotomicNumber::from(&Cyc8::sqrt2())
        );
        assert_eq!(
            sqrt_of_integer(24, &BigInt::from(2)).unwrap(),
            CyclotomicNumber::from(&Cyc24::sqrt2())
        );
        assert_eq!(
            sqrt_of_integer(24, &BigInt::from(3)).unwrap(),
            CyclotomicNumber::from(&Cyc24::sqrt3())
        );
        assert_eq!(
            sqrt_of_integer(28, &BigInt::from(7)).unwrap(),
            CyclotomicNumber::from(&crate::cyclotomic28::sqrt7_28())
        );
    }

    // ----- conversions and cross-validation against the fixed-conductor types -----

    /// Every fixed-conductor type must agree with the generic field on a deterministic grid:
    /// the conversion commutes with add, sub, mul, conj and scaling, and round-trips.
    fn cross_validate<T>(n: usize, make: impl Fn(&[Rational]) -> T)
    where
        T: RationalEmbedding + Involution + std::fmt::Debug,
        for<'a> CyclotomicNumber: From<&'a T>,
        for<'a> T: TryFrom<&'a CyclotomicNumber, Error = CyclotomicError>,
    {
        let mut rng = Lcg::new(1000 + n as u64);
        let degree = euler_phi(n);
        for _ in 0..4 {
            let cx: Vec<Rational> = (0..degree)
                .map(|_| rq(rng.next_signed(3), 1 + rng.next_below(2) as i64))
                .collect();
            let cy: Vec<Rational> = (0..degree)
                .map(|_| rq(rng.next_signed(3), 1 + rng.next_below(2) as i64))
                .collect();
            let (fx, fy) = (make(&cx), make(&cy));
            let (gx, gy) = (CyclotomicNumber::from(&fx), CyclotomicNumber::from(&fy));
            assert_eq!(
                gx.coefficients(),
                cx.as_slice(),
                "conversion copies the coefficients"
            );
            assert_eq!(
                CyclotomicNumber::from(&fx.add(&fy)),
                gx.add(&gy).unwrap(),
                "add, n = {n}"
            );
            assert_eq!(
                CyclotomicNumber::from(&fx.sub(&fy)),
                gx.sub(&gy).unwrap(),
                "sub, n = {n}"
            );
            assert_eq!(
                CyclotomicNumber::from(&fx.mul(&fy)),
                gx.mul(&gy).unwrap(),
                "mul, n = {n}"
            );
            assert_eq!(
                CyclotomicNumber::from(&fx.conjugate()),
                gx.conjugate(),
                "conj, n = {n}"
            );
            assert_eq!(
                CyclotomicNumber::from(&fx.mul(&T::from_rational(&rq(3, 7)))),
                gx.scale(&rq(3, 7)),
                "scale, n = {n}"
            );
            assert_eq!(T::try_from(&gx).unwrap(), fx, "round trip, n = {n}");
        }
        assert_eq!(zeta(n, 1).pow(u32::try_from(n).unwrap()), one(n));
    }

    #[test]
    fn the_fixed_conductor_types_agree_with_the_generic_field() {
        cross_validate(5, |c| Cyc5 {
            a: std::array::from_fn(|i| c[i].clone()),
        });
        cross_validate(8, |c| Cyc8 {
            a: std::array::from_fn(|i| c[i].clone()),
        });
        cross_validate(12, |c| Cyc12 {
            a: std::array::from_fn(|i| c[i].clone()),
        });
        cross_validate(24, |c| Cyc24 {
            a: std::array::from_fn(|i| c[i].clone()),
        });
        cross_validate(28, |c| Cyc28 {
            a: std::array::from_fn(|i| c[i].clone()),
        });
        cross_validate(44, |c| Cyc44 {
            a: std::array::from_fn(|i| c[i].clone()),
        });
        cross_validate(52, |c| Cyc52 {
            a: std::array::from_fn(|i| c[i].clone()),
        });
        cross_validate(120, |c| Cyc120 {
            a: std::array::from_fn(|i| c[i].clone()),
        });
    }

    #[test]
    fn inverses_agree_with_the_fixed_conductor_types() {
        let mut rng = Lcg::new(5150);
        for _ in 0..3 {
            let c: Vec<Rational> = (0..8)
                .map(|_| rq(rng.next_signed(3), 1 + rng.next_below(2) as i64))
                .collect();
            let x = Cyc24 {
                a: std::array::from_fn(|i| c[i].clone()),
            };
            if x.is_zero() {
                continue;
            }
            assert_eq!(
                CyclotomicNumber::from(&x).inverse().unwrap(),
                CyclotomicNumber::from(&x.inv())
            );
        }
        let c: Vec<Rational> = (0..4).map(|i| rq(i + 1, 2)).collect();
        let x = Cyc5 {
            a: std::array::from_fn(|i| c[i].clone()),
        };
        assert_eq!(
            CyclotomicNumber::from(&x).inverse().unwrap(),
            CyclotomicNumber::from(&x.inv())
        );
    }

    #[test]
    fn gaussian_and_eisenstein_rationals_convert_exactly() {
        let g = GaussianRat::from_ints(3, -4);
        let n = CyclotomicNumber::from(&g);
        assert_eq!(n.conductor(), 4);
        assert_eq!(GaussianRat::try_from(&n).unwrap(), g);
        assert_eq!(n.mul(&n).unwrap(), CyclotomicNumber::from(&g.mul(&g)));
        assert_eq!(n.norm(), g.norm_sq());
        let e = EisensteinRat::from_ints(2, -5);
        let m = CyclotomicNumber::from(&e);
        assert_eq!(m.conductor(), 3);
        assert_eq!(EisensteinRat::try_from(&m).unwrap(), e);
        assert_eq!(m.mul(&m).unwrap(), CyclotomicNumber::from(&e.mul(&e)));
        assert_eq!(m.norm(), e.norm_sq());
    }

    #[test]
    fn conversion_to_the_wrong_fixed_type_is_refused() {
        let five = zeta(5, 1);
        assert_eq!(
            Cyc8::try_from(&five),
            Err(CyclotomicError::ConductorMismatch { left: 5, right: 8 })
        );
        assert_eq!(
            GaussianRat::try_from(&five),
            Err(CyclotomicError::ConductorMismatch { left: 5, right: 4 })
        );
        assert!(Cyc5::try_from(&five).is_ok());
    }

    #[test]
    fn lifting_into_a_larger_field_is_a_ring_embedding_that_matches_the_fixed_types() {
        // Q(zeta_8) inside Q(zeta_24): zeta_8 -> zeta_24^3.
        let s8 = CyclotomicNumber::from(&Cyc8::sqrt2());
        assert_eq!(
            s8.lift(24).unwrap(),
            CyclotomicNumber::from(&Cyc24::sqrt2())
        );
        let z8 = CyclotomicNumber::from(&Cyc8::zeta8(3));
        assert_eq!(
            z8.lift(24).unwrap(),
            CyclotomicNumber::from(&Cyc24::zeta24(9))
        );
        // Q(zeta_3) inside Q(zeta_12): zeta_3 = zeta_12^4
        let w = CyclotomicNumber::from(&EisensteinRat::zeta3());
        assert_eq!(w.lift(12).unwrap(), zeta(12, 4));
        // ring embedding, and the norm to Q squares: N_24(x) = N_8(x)^[24:8 degree ratio]
        let mut rng = Lcg::new(88);
        let (x, y) = (grid_element(8, &mut rng), grid_element(8, &mut rng));
        assert_eq!(
            x.mul(&y).unwrap().lift(24).unwrap(),
            x.lift(24).unwrap().mul(&y.lift(24).unwrap()).unwrap()
        );
        assert_eq!(x.lift(24).unwrap().norm(), x.norm().pow(2));
        assert_eq!(
            x.lift(12),
            Err(CyclotomicError::ConductorMismatch { left: 8, right: 12 })
        );
    }

    #[test]
    fn typed_wrapper_operators_agree_with_the_checked_type() {
        type K = Cyclotomic<12>;
        let mut rng = Lcg::new(99);
        for _ in 0..5 {
            let (a, b) = (grid_element(12, &mut rng), grid_element(12, &mut rng));
            let (ta, tb) = (
                K::try_from(a.clone()).unwrap(),
                K::try_from(b.clone()).unwrap(),
            );
            assert_eq!(
                CyclotomicNumber::from(ta.clone() * tb.clone()),
                a.mul(&b).unwrap()
            );
            assert_eq!(CyclotomicNumber::from(&ta + &tb), a.add(&b).unwrap());
            assert_eq!(CyclotomicNumber::from(&ta - &tb), a.sub(&b).unwrap());
            assert_eq!(CyclotomicNumber::from(-ta.clone()), a.neg());
            assert_eq!(CyclotomicNumber::from(ta.conjugate()), a.conjugate());
            assert_eq!(ta.trace(), a.trace());
            assert_eq!(ta.norm(), a.norm());
            assert_eq!(ta.inverse().map(CyclotomicNumber::from), a.inverse());
        }
        assert_eq!(
            K::try_from(zeta(8, 1)),
            Err(CyclotomicError::ConductorMismatch { left: 8, right: 12 })
        );
    }

    #[test]
    fn typed_wrapper_reports_its_conductor_and_zeta() {
        assert_eq!(Cyclotomic::<24>::CONDUCTOR, 24);
        let z = Cyclotomic::<24>::zeta(1);
        assert_eq!(z.pow(24), Cyclotomic::<24>::one());
        assert_eq!(z.pow(12), Cyclotomic::<24>::one().neg());
        assert!(Cyclotomic::<24>::zero().is_zero());
        assert_eq!(
            Cyclotomic::<24>::rational(rq(3, 2)).as_rational(),
            Some(rq(3, 2))
        );
        assert_eq!(z.galois(5).unwrap(), Cyclotomic::<24>::zeta(5));
        assert!(z.galois(2).is_err());
    }

    // ----- serde ---------------------------------------------------------------

    #[test]
    fn wire_form_round_trips_and_rejects_a_forged_field() {
        let x = num(12, &[1, -2, 3, 5]);
        let text = serde_json::to_string(&x).unwrap();
        let back: CyclotomicNumber = serde_json::from_str(&text).unwrap();
        assert_eq!(back, x);
        // a wire form claiming conductor 7 (degree 6) with 4 coefficients is refused
        let forged = text.replace("\"conductor\":12", "\"conductor\":7");
        assert_ne!(forged, text, "the replacement must have applied");
        assert!(serde_json::from_str::<CyclotomicNumber>(&forged).is_err());
        // and the typed wrapper refuses a wire form of the wrong conductor
        assert!(serde_json::from_str::<Cyclotomic<8>>(&text).is_err());
        let typed: Cyclotomic<12> = serde_json::from_str(&text).unwrap();
        assert_eq!(typed.as_number(), &x);
    }

    // ----- scale ---------------------------------------------------------------

    #[test]
    fn a_conductor_120_element_multiplies_and_inverts_exactly() {
        let x = zeta(120, 7)
            .add(&CyclotomicNumber::from_rational(120, ri(3)).unwrap())
            .unwrap();
        let inverse = x.inverse().unwrap();
        assert_eq!(x.mul(&inverse).unwrap(), one(120));
        assert_eq!(x.degree(), 32);
        // N(3 + zeta) = prod (3 + zeta_sigma) = Phi_120(-3), since phi(120) is even.
        assert_eq!(x.norm(), cyclotomic_polynomial(120).unwrap().eval(&ri(-3)));
    }
}

/// Refusals for the bounded quadratic-conductor obstruction search.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum QuadraticPrimeSearchError {
    #[error("a positive conductor is required")]
    InvalidConductor,
    #[error("the prime candidate search exhausted its declared budget")]
    CandidateBudget,
    #[error(transparent)]
    Factorization(#[from] crate::integer_factorization::FactorizationError),
}
/// The least prime p for which Q(sqrt(p)) is not a subfield of Q(zeta_n).
/// Every preceding candidate is checked with canonical deterministic primality;
/// the quadratic field conductor owns the embedding criterion. This function
/// does not construct the ambient field and so supports any usize conductor.
pub fn first_missing_quadratic_prime(
    conductor: usize,
    candidate_budget: usize,
) -> Result<usize, QuadraticPrimeSearchError> {
    if conductor == 0 {
        return Err(QuadraticPrimeSearchError::InvalidConductor);
    }
    let n = BigInt::from(conductor);
    let mut p = 2usize;
    for _ in 0..candidate_budget {
        let primality = crate::integer_factorization::is_prime_u64(
            u64::try_from(p).map_err(|_| QuadraticPrimeSearchError::CandidateBudget)?,
            crate::integer_factorization::FactorizationBudget::default(),
        )?;
        if primality && (&n % quadratic_field_conductor(&BigInt::from(p))).is_zero() {
        } else if primality {
            return Ok(p);
        }
        p = p
            .checked_add(1)
            .ok_or(QuadraticPrimeSearchError::CandidateBudget)?;
    }
    Err(QuadraticPrimeSearchError::CandidateBudget)
}
#[cfg(test)]
mod quadratic_prime_search_laws {
    use super::*;
    #[test]
    fn least_missing_prime_uses_complete_predecessors_and_typed_bounds() {
        for (n, p) in [(120, 7), (240, 7), (480, 7), (840, 11)] {
            assert_eq!(first_missing_quadratic_prime(n, 100).unwrap(), p);
        }
        let n = 8usize * 3 * 5 * 7 * 11 * 13 * 17 * 19 * 23;
        assert_eq!(first_missing_quadratic_prime(n, 100).unwrap(), 29);
        assert!(first_missing_quadratic_prime(n, 20).is_err());
        assert!(first_missing_quadratic_prime(0, 100).is_err());
    }
}

#[cfg(test)]
mod dynamics_inclusion_laws {
    use super::*;
    use num_integer::Integer;
    #[test]
    fn normalized_conductor_inclusion_agrees_with_compositum_degree_and_embeddings() {
        for m in 1usize..=16 {
            for n in 1usize..=16 {
                let compositum = m.lcm(&n);
                let same_degree = cyclotomic_polynomial(compositum).unwrap().degree()
                    == cyclotomic_polynomial(n).unwrap().degree();
                assert_eq!(contains_cyclotomic_field(m, n).unwrap(), same_degree);
            }
        }
        let z = CyclotomicNumber::zeta(3, 1).unwrap();
        let w = embed_cyclotomic(&z, 12).unwrap();
        assert_eq!(w, CyclotomicNumber::zeta(12, 4).unwrap());
        assert_eq!(
            embed_cyclotomic(&z.mul(&z).unwrap(), 12).unwrap(),
            w.mul(&w).unwrap()
        );
        assert_eq!(embed_cyclotomic(&z.conjugate(), 12).unwrap(), w.conjugate());
        assert!(embed_cyclotomic(&z, 4).is_err());
        assert!(normalized_conductor(0).is_err());
    }
}
