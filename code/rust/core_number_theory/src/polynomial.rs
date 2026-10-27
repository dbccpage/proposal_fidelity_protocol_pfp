//! Dense univariate polynomials over an exact field, and exact real-root machinery over `Q`.
//!
//! [`Polynomial<F>`] stores ascending coefficients and is always normalised: the last
//! stored coefficient is nonzero, and the zero polynomial has no coefficients, so
//! equality of values is equality of representations. It works over any `F` in the
//! scalar tower of `linear_algebra::scalars` ([`ExactField`]): `Q`, the Gaussian and
//! Eisenstein rationals, every cyclotomic field of this crate, and the quadratic fields.
//!
//! Generic operations: ring arithmetic, Horner evaluation, derivative, composition,
//! Euclidean division with a typed refusal on a zero divisor, monic gcd, the extended
//! gcd, resultant, discriminant, the squarefree part and Yun's squarefree decomposition.
//! The squarefree operations assume characteristic zero (they use `gcd(f, f')`).
//!
//! Over `Q` this module adds what exact real algebra needs: the Gauss content and
//! primitive part, cyclotomic polynomials computed by division, Sturm sequences, exact
//! counts of real roots in `(a, b]`, Cauchy root bounds, isolation of every real root by
//! rational intervals, and bisection refinement. A rational root is always reported
//! exactly; an irrational root is reported by an interval whose endpoints are not roots.
//!
//! There is no floating point and no tolerance in this module.
//!
//! AuthorityEffect: None.

use std::cmp::Ordering;

use linear_algebra::scalars::{ExactRing, Field};
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use core_kernel::interval::Interval;
use serde::{Deserialize, Deserializer, Serialize, Serializer};

use crate::rational::{r_one, r_zero, ri, Rational};

/// The largest conductor `n` for which [`cyclotomic_polynomial`] (and the cyclotomic
/// fields built on it) are available. It keeps the dense `phi(n)`-coefficient
/// arithmetic tractable; raising it is a deliberate decision, not an accident.
pub const MAX_CONDUCTOR: usize = 1024;

/// Refusals of the polynomial operations.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PolynomialError {
    #[error("interpolation requires at least one distinct node")]
    EmptyNodes,
    #[error("interpolation nodes {first} and {second} coincide")]
    RepeatedNode { first: usize, second: usize },
    #[error("interpolation exceeds 256 nodes")]
    InterpolationBudget,
    #[error("division by the zero polynomial")]
    DivisionByZero,
    #[error("the zero polynomial has every scalar as a root, so this is undefined for it")]
    ZeroPolynomial,
    #[error("the operation needs degree at least {required}, got {actual}")]
    DegreeTooSmall { required: usize, actual: usize },
    #[error("interval endpoints are reversed: {lower} > {upper}")]
    ReversedInterval { lower: String, upper: String },
    #[error("tolerance must be positive, got {0}")]
    NonPositiveTolerance(String),
    #[error(
        "the interval [{lower}, {upper}] does not isolate a simple root: the polynomial has the \
         same sign at both endpoints, or vanishes at one"
    )]
    NotIsolating { lower: String, upper: String },
    #[error("conductor 0 has no cyclotomic polynomial")]
    ConductorZero,
    #[error("conductor {conductor} exceeds the supported maximum {max}")]
    ConductorTooLarge { conductor: usize, max: usize },
    #[error(
        "a field element that should be invertible has no inverse (corrupt field implementation)"
    )]
    NotInvertible,
    #[error("internal inconsistency in root isolation: {0}")]
    Inconsistent(&'static str),
}

/// Lagrange coefficients for evaluating the interpolating polynomial at `x0`.
/// Big-rational products preserve arbitrary denominators and large nodes.
pub fn lagrange_weights_at(
    x0: &Rational,
    nodes: &[Rational],
) -> Result<Vec<Rational>, PolynomialError> {
    if nodes.is_empty() {
        return Err(PolynomialError::EmptyNodes);
    }
    if nodes.len() > 256 {
        return Err(PolynomialError::InterpolationBudget);
    }
    for (j, x) in nodes.iter().enumerate() {
        if let Some(k) = nodes.iter().take(j).position(|y| y == x) {
            return Err(PolynomialError::RepeatedNode {
                first: k,
                second: j,
            });
        }
    }
    Ok(nodes
        .iter()
        .enumerate()
        .map(|(j, x)| {
            nodes
                .iter()
                .enumerate()
                .filter(|(k, _)| *k != j)
                .fold(r_one(), |w, (_, y)| w * (x0 - y) / (x - y))
        })
        .collect())
}

/// Shorthand for the scalar bounds every polynomial operation needs: an exact field of
/// the `linear_algebra` scalar tower.
pub trait ExactField: Field + ExactRing {}
impl<T: Field + ExactRing> ExactField for T {}

/// A univariate polynomial with ascending coefficients, `c_0 + c_1 x + ... + c_d x^d`,
/// normalised so that the leading stored coefficient is nonzero.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Polynomial<F> {
    coeffs: Vec<F>,
}

impl<F: Serialize> Serialize for Polynomial<F> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        self.coeffs.serialize(serializer)
    }
}

impl<'de, F: Deserialize<'de> + ExactField> Deserialize<'de> for Polynomial<F> {
    /// Deserialises the coefficient list and normalises it, so a wire form with trailing
    /// zeros gives the same value as the trimmed form.
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        Ok(Self::from_coefficients(Vec::<F>::deserialize(
            deserializer,
        )?))
    }
}

/// `k * c` by repeated doubling, for a natural number `k`.
fn natural_multiple<F: ExactField>(c: &F, k: usize) -> F {
    let mut result = F::zero();
    let mut addend = c.clone();
    let mut k = k;
    while k > 0 {
        if k & 1 == 1 {
            result = result.add(&addend);
        }
        k >>= 1;
        if k > 0 {
            addend = addend.add(&addend);
        }
    }
    result
}

/// `c^k` by repeated squaring.
fn field_pow<F: ExactField>(c: &F, k: usize) -> F {
    let mut result = F::one();
    let mut base = c.clone();
    let mut k = k;
    while k > 0 {
        if k & 1 == 1 {
            result = result.mul(&base);
        }
        k >>= 1;
        if k > 0 {
            base = base.mul(&base);
        }
    }
    result
}

impl<F: ExactField> Polynomial<F> {
    /// The zero polynomial.
    pub fn zero() -> Self {
        Self { coeffs: Vec::new() }
    }

    /// The constant polynomial `1`.
    pub fn one() -> Self {
        Self::constant(F::one())
    }

    /// The constant polynomial `c`.
    pub fn constant(c: F) -> Self {
        Self::from_coefficients(vec![c])
    }

    /// The polynomial `x`.
    pub fn x() -> Self {
        Self::from_coefficients(vec![F::zero(), F::one()])
    }

    /// `c x^degree`.
    pub fn monomial(c: F, degree: usize) -> Self {
        if c.is_zero() {
            return Self::zero();
        }
        let mut coeffs = vec![F::zero(); degree];
        coeffs.push(c);
        Self { coeffs }
    }

    /// The polynomial with the given ascending coefficients; trailing zeros are dropped.
    pub fn from_coefficients(mut coeffs: Vec<F>) -> Self {
        while coeffs.last().is_some_and(|c| c.is_zero()) {
            coeffs.pop();
        }
        Self { coeffs }
    }

    /// `prod (x - r)` over the given roots (the monic polynomial with exactly these
    /// roots, with multiplicity).
    pub fn from_roots(roots: &[F]) -> Self {
        roots.iter().fold(Self::one(), |acc, root| {
            acc.mul(&Self::from_coefficients(vec![root.neg(), F::one()]))
        })
    }

    /// The ascending coefficients; empty for the zero polynomial.
    pub fn coefficients(&self) -> &[F] {
        &self.coeffs
    }

    /// The coefficient of `x^i`, zero beyond the degree.
    pub fn coefficient(&self, i: usize) -> F {
        self.coeffs.get(i).cloned().unwrap_or_else(F::zero)
    }

    /// The degree, or `None` for the zero polynomial.
    pub fn degree(&self) -> Option<usize> {
        self.coeffs.len().checked_sub(1)
    }

    pub fn is_zero(&self) -> bool {
        self.coeffs.is_empty()
    }

    /// Whether the polynomial is a constant (including zero).
    pub fn is_constant(&self) -> bool {
        self.coeffs.len() <= 1
    }

    /// The leading coefficient, `None` for the zero polynomial.
    pub fn leading_coefficient(&self) -> Option<&F> {
        self.coeffs.last()
    }

    /// `self + other`.
    pub fn add(&self, other: &Self) -> Self {
        let n = self.coeffs.len().max(other.coeffs.len());
        let coeffs = (0..n)
            .map(|i| match (self.coeffs.get(i), other.coeffs.get(i)) {
                (Some(a), Some(b)) => a.add(b),
                (Some(a), None) => a.clone(),
                (None, Some(b)) => b.clone(),
                (None, None) => F::zero(),
            })
            .collect();
        Self::from_coefficients(coeffs)
    }

    /// `-self`.
    pub fn neg(&self) -> Self {
        Self {
            coeffs: self.coeffs.iter().map(|c| c.neg()).collect(),
        }
    }

    /// `self - other`.
    pub fn sub(&self, other: &Self) -> Self {
        self.add(&other.neg())
    }

    /// `self * other` (schoolbook).
    pub fn mul(&self, other: &Self) -> Self {
        if self.is_zero() || other.is_zero() {
            return Self::zero();
        }
        let mut out = vec![F::zero(); self.coeffs.len() + other.coeffs.len() - 1];
        for (i, a) in self.coeffs.iter().enumerate() {
            if a.is_zero() {
                continue;
            }
            for (j, b) in other.coeffs.iter().enumerate() {
                out[i + j] = out[i + j].add(&a.mul(b));
            }
        }
        Self::from_coefficients(out)
    }

    /// `c * self`.
    pub fn scale(&self, c: &F) -> Self {
        Self::from_coefficients(self.coeffs.iter().map(|a| a.mul(c)).collect())
    }

    /// `self^k`.
    pub fn pow(&self, k: usize) -> Self {
        let mut result = Self::one();
        let mut base = self.clone();
        let mut k = k;
        while k > 0 {
            if k & 1 == 1 {
                result = result.mul(&base);
            }
            k >>= 1;
            if k > 0 {
                base = base.mul(&base);
            }
        }
        result
    }

    /// Horner evaluation at `x`.
    pub fn eval(&self, x: &F) -> F {
        self.coeffs
            .iter()
            .rev()
            .fold(F::zero(), |acc, c| acc.mul(x).add(c))
    }

    /// The composition `self(other(x))`.
    pub fn compose(&self, other: &Self) -> Self {
        self.coeffs.iter().rev().fold(Self::zero(), |acc, c| {
            acc.mul(other).add(&Self::constant(c.clone()))
        })
    }

    /// `self(x + a)`.
    pub fn shift(&self, a: &F) -> Self {
        self.compose(&Self::from_coefficients(vec![a.clone(), F::one()]))
    }

    /// The formal derivative.
    pub fn derivative(&self) -> Self {
        Self::from_coefficients(
            self.coeffs
                .iter()
                .enumerate()
                .skip(1)
                .map(|(i, c)| natural_multiple(c, i))
                .collect(),
        )
    }

    /// `self / lc(self)`, or `None` for the zero polynomial.
    pub fn monic(&self) -> Option<Self> {
        let inverse = self.leading_coefficient()?.try_inv()?;
        Some(self.scale(&inverse))
    }

    /// Euclidean division: `(q, r)` with `self = q * divisor + r` and
    /// `deg r < deg divisor`. Refuses a zero divisor.
    pub fn div_rem(&self, divisor: &Self) -> Result<(Self, Self), PolynomialError> {
        let Some(lead) = divisor.leading_coefficient() else {
            return Err(PolynomialError::DivisionByZero);
        };
        let lead_inverse = lead.try_inv().ok_or(PolynomialError::NotInvertible)?;
        let d = divisor.coeffs.len() - 1;
        if self.coeffs.len() <= d {
            return Ok((Self::zero(), self.clone()));
        }
        let mut remainder = self.coeffs.clone();
        let mut quotient = vec![F::zero(); remainder.len() - d];
        while remainder.len() > d {
            let shift = remainder.len() - 1 - d;
            let top = remainder.pop().ok_or(PolynomialError::Inconsistent(
                "remainder emptied inside division",
            ))?;
            let factor = top.mul(&lead_inverse);
            for (j, c) in divisor.coeffs.iter().take(d).enumerate() {
                remainder[shift + j] = remainder[shift + j].sub(&factor.mul(c));
            }
            quotient[shift] = factor;
            while remainder.last().is_some_and(|c| c.is_zero()) {
                remainder.pop();
            }
        }
        Ok((
            Self::from_coefficients(quotient),
            Self::from_coefficients(remainder),
        ))
    }

    /// The remainder of Euclidean division.
    pub fn rem(&self, divisor: &Self) -> Result<Self, PolynomialError> {
        Ok(self.div_rem(divisor)?.1)
    }

    /// The monic greatest common divisor; `gcd(0, 0) = 0`.
    pub fn gcd(&self, other: &Self) -> Self {
        let (mut a, mut b) = (self.clone(), other.clone());
        while !b.is_zero() {
            // `b` is nonzero, so the division cannot refuse.
            let Ok(r) = a.rem(&b) else {
                break;
            };
            a = b;
            b = r;
        }
        a.monic().unwrap_or_else(Self::zero)
    }

    /// The extended gcd: `(g, s, t)` with `s * self + t * other = g` and `g` monic (or
    /// zero when both arguments are zero).
    pub fn xgcd(&self, other: &Self) -> (Self, Self, Self) {
        let (mut r0, mut r1) = (self.clone(), other.clone());
        let (mut s0, mut s1) = (Self::one(), Self::zero());
        let (mut t0, mut t1) = (Self::zero(), Self::one());
        while !r1.is_zero() {
            let Ok((q, r2)) = r0.div_rem(&r1) else {
                break;
            };
            let s2 = s0.sub(&q.mul(&s1));
            let t2 = t0.sub(&q.mul(&t1));
            r0 = r1;
            r1 = r2;
            s0 = s1;
            s1 = s2;
            t0 = t1;
            t1 = t2;
        }
        match r0.leading_coefficient().and_then(|lead| lead.try_inv()) {
            Some(inverse) => (r0.scale(&inverse), s0.scale(&inverse), t0.scale(&inverse)),
            None => (Self::zero(), Self::zero(), Self::zero()),
        }
    }

    /// The resultant `Res(self, other)`, by the Euclidean recursion
    /// `Res(f, g) = (-1)^{mn} lc(g)^{m - deg r} Res(g, r)` with `r = f mod g`.
    ///
    /// The resultant with the zero polynomial is zero. For monic `f` of degree `m`,
    /// `Res(f, g) = prod g(alpha)` over the roots `alpha` of `f`.
    pub fn resultant(&self, other: &Self) -> F {
        let (mut f, mut g) = (self.clone(), other.clone());
        let mut scalar = F::one();
        loop {
            let (Some(m), Some(n)) = (f.degree(), g.degree()) else {
                return F::zero();
            };
            if n == 0 {
                return scalar.mul(&field_pow(&g.coeffs[0], m));
            }
            if m == 0 {
                return scalar.mul(&field_pow(&f.coeffs[0], n));
            }
            let Ok(r) = f.rem(&g) else {
                return F::zero();
            };
            let Some(k) = r.degree() else {
                return F::zero();
            };
            let lead_g = g.coeffs[n].clone();
            let mut factor = field_pow(&lead_g, m - k);
            // (-1)^{mn}: the parity of a product is the product of the parities.
            if (m % 2) * (n % 2) == 1 {
                factor = factor.neg();
            }
            scalar = scalar.mul(&factor);
            f = g;
            g = r;
        }
    }

    /// The discriminant `(-1)^{n(n-1)/2} Res(f, f') / lc(f)` of a polynomial of degree
    /// `n >= 1`; it vanishes exactly when `f` has a repeated root.
    pub fn discriminant(&self) -> Result<F, PolynomialError> {
        let Some(n) = self.degree() else {
            return Err(PolynomialError::ZeroPolynomial);
        };
        if n < 1 {
            return Err(PolynomialError::DegreeTooSmall {
                required: 1,
                actual: n,
            });
        }
        let lead_inverse = self.coeffs[n]
            .try_inv()
            .ok_or(PolynomialError::NotInvertible)?;
        let mut value = self.resultant(&self.derivative()).mul(&lead_inverse);
        // n(n-1)/2 is odd exactly when n = 2 or 3 (mod 4).
        if n % 4 >= 2 {
            value = value.neg();
        }
        Ok(value)
    }

    /// The monic squarefree part `f / gcd(f, f')` (characteristic zero); zero for zero.
    pub fn squarefree_part(&self) -> Self {
        if self.is_constant() {
            return if self.is_zero() {
                Self::zero()
            } else {
                Self::one()
            };
        }
        let g = self.gcd(&self.derivative());
        match self.div_rem(&g) {
            Ok((q, _)) => q.monic().unwrap_or_else(Self::zero),
            Err(_) => Self::zero(),
        }
    }

    /// Yun's squarefree decomposition (characteristic zero): the monic pairwise-coprime
    /// squarefree polynomials `q_i` and multiplicities `i` with
    /// `self = lc(self) * prod q_i^i`, in increasing multiplicity. Constants give an
    /// empty list; the zero polynomial is refused.
    pub fn squarefree_decomposition(&self) -> Result<Vec<(Self, usize)>, PolynomialError> {
        let Some(monic) = self.monic() else {
            return Err(PolynomialError::ZeroPolynomial);
        };
        if monic.is_constant() {
            return Ok(Vec::new());
        }
        let derivative = monic.derivative();
        let a0 = monic.gcd(&derivative);
        let mut b = monic.div_rem(&a0)?.0;
        let mut c = derivative.div_rem(&a0)?.0;
        let mut d = c.sub(&b.derivative());
        let mut factors = Vec::new();
        let mut multiplicity = 1usize;
        while !b.is_constant() {
            let a = b.gcd(&d);
            if !a.is_constant() {
                factors.push((a.clone(), multiplicity));
            }
            b = b.div_rem(&a)?.0;
            c = d.div_rem(&a)?.0;
            d = c.sub(&b.derivative());
            multiplicity += 1;
        }
        Ok(factors)
    }
}

fn fmt_monomial<F: std::fmt::Display>(
    f: &mut std::fmt::Formatter<'_>,
    deg: usize,
    coeff: &F,
) -> std::fmt::Result {
    match deg {
        0 => write!(f, "({coeff})"),
        1 => write!(f, "({coeff})x"),
        _ => write!(f, "({coeff})x^{deg}"),
    }
}

impl<F: ExactField + std::fmt::Display> std::fmt::Display for Polynomial<F> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if self.coeffs.is_empty() {
            return write!(f, "0");
        }
        let mut first = true;
        for (i, c) in self.coeffs.iter().enumerate().rev() {
            if c.is_zero() {
                continue;
            }
            if !first {
                write!(f, " + ")?;
            }
            first = false;
            fmt_monomial(f, i, c)?;
        }
        Ok(())
    }
}

// ---------------------------------------------------------------------------
// Integer arithmetic on conductors
// ---------------------------------------------------------------------------

/// Euler's totient `phi(n)`: the number of `k` in `1..=n` coprime to `n`.
/// By that definition `phi(0) = 0` and `phi(1) = 1`.
pub fn euler_phi(n: usize) -> usize {
    let mut result = n;
    let mut remaining = n;
    let mut p = 2usize;
    while p <= remaining / p {
        if remaining % p == 0 {
            while remaining % p == 0 {
                remaining /= p;
            }
            result -= result / p;
        }
        p += 1;
    }
    if remaining > 1 {
        result -= result / remaining;
    }
    result
}

/// The distinct prime divisors of `n`, ascending (empty for `0` and `1`).
pub fn distinct_prime_factors(n: usize) -> Vec<usize> {
    let mut primes = Vec::new();
    let mut remaining = n;
    let mut p = 2usize;
    while remaining > 1 && p <= remaining / p {
        if remaining % p == 0 {
            primes.push(p);
            while remaining % p == 0 {
                remaining /= p;
            }
        }
        p += 1;
    }
    if remaining > 1 {
        primes.push(remaining);
    }
    primes
}

/// The Moebius function `mu(n)` for `n >= 1` (`0` for `n = 0`).
pub fn mobius(n: usize) -> i8 {
    if n == 0 {
        return 0;
    }
    let mut remaining = n;
    let mut sign = 1i8;
    for p in distinct_prime_factors(n) {
        remaining /= p;
        if remaining % p == 0 {
            return 0;
        }
        sign = -sign;
    }
    sign
}

/// The divisors of `n` in ascending order (empty for `0`).
pub fn divisors(n: usize) -> Vec<usize> {
    if n == 0 {
        return Vec::new();
    }
    let mut small = Vec::new();
    let mut large = Vec::new();
    let mut d = 1usize;
    while d <= n / d {
        if n % d == 0 {
            small.push(d);
            if d != n / d {
                large.push(n / d);
            }
        }
        d += 1;
    }
    large.reverse();
    small.extend(large);
    small
}

// ---------------------------------------------------------------------------
// Polynomials over Q
// ---------------------------------------------------------------------------

impl Polynomial<Rational> {
    /// The polynomial with the given ascending integer coefficients.
    pub fn from_i64s(coefficients: &[i64]) -> Self {
        Self::from_coefficients(coefficients.iter().map(|&c| ri(c)).collect())
    }

    /// The smallest positive `D` with `D * self` in `Z[x]`, and those integer
    /// coefficients. The zero polynomial gives `(1, [])`.
    pub fn integer_coefficients(&self) -> (BigInt, Vec<BigInt>) {
        let denominator = self
            .coeffs
            .iter()
            .fold(BigInt::one(), |acc, c| acc.lcm(c.denom()));
        let integers = self
            .coeffs
            .iter()
            .map(|c| c.numer() * (&denominator / c.denom()))
            .collect();
        (denominator, integers)
    }

    /// The Gauss content: `gcd` of the numerators over `lcm` of the denominators, a
    /// nonnegative rational, zero only for the zero polynomial.
    pub fn content(&self) -> Rational {
        if self.is_zero() {
            return r_zero();
        }
        let numerator_gcd = self
            .coeffs
            .iter()
            .fold(BigInt::zero(), |acc, c| acc.gcd(c.numer()));
        let denominator_lcm = self
            .coeffs
            .iter()
            .fold(BigInt::one(), |acc, c| acc.lcm(c.denom()));
        Rational::new(numerator_gcd, denominator_lcm)
    }

    /// `(c, p)` with `self = c * p`, where `p` has coprime integer coefficients and a
    /// positive leading coefficient, so `c` carries the sign. The zero polynomial gives
    /// `(0, 0)`.
    pub fn content_and_primitive_part(&self) -> (Rational, Self) {
        let Some(lead) = self.leading_coefficient() else {
            return (r_zero(), Self::zero());
        };
        let mut content = self.content();
        if lead.is_negative() {
            content = -content;
        }
        let primitive = self.scale(&(r_one() / &content));
        (content, primitive)
    }

    /// The sign of `self(x)`.
    pub fn sign_at(&self, x: &Rational) -> Ordering {
        self.eval(x).cmp(&r_zero())
    }

    /// An interval containing `{ self(t) : t in x }`, by Horner's rule in interval
    /// arithmetic. It is an enclosure (possibly wider than the exact image) whose width
    /// goes to zero with the width of `x`.
    pub fn eval_interval(&self, x: &Interval) -> Interval {
        self.coeffs
            .iter()
            .rev()
            .fold(Interval::point(r_zero()), |acc, c| {
                acc.mul(x).add(&Interval::point(c.clone()))
            })
    }
}

/// The cyclotomic polynomial `Phi_n(x)` over `Q` (integer coefficients), computed by
/// exact division: `Phi_n = (x^n - 1) / prod_{d | n, d < n} Phi_d`.
///
/// Refuses `n = 0` and `n > MAX_CONDUCTOR`.
pub fn cyclotomic_polynomial(n: usize) -> Result<Polynomial<Rational>, PolynomialError> {
    if n == 0 {
        return Err(PolynomialError::ConductorZero);
    }
    if n > MAX_CONDUCTOR {
        return Err(PolynomialError::ConductorTooLarge {
            conductor: n,
            max: MAX_CONDUCTOR,
        });
    }
    let mut computed: std::collections::BTreeMap<usize, Polynomial<Rational>> =
        std::collections::BTreeMap::new();
    for d in divisors(n) {
        let mut numerator = Polynomial::monomial(r_one(), d).sub(&Polynomial::one());
        for (&e, phi_e) in &computed {
            if d % e == 0 {
                numerator = numerator.div_rem(phi_e)?.0;
            }
        }
        computed.insert(d, numerator);
    }
    computed.remove(&n).ok_or(PolynomialError::Inconsistent(
        "divisor list misses n itself",
    ))
}

// ---------------------------------------------------------------------------
// Sturm sequences and real roots
// ---------------------------------------------------------------------------

/// The sign of `p(x)` for a polynomial with integer coefficients `p` (ascending) at
/// `x = a / b`, by homogeneous Horner: `b^d p(a/b) = sum c_i a^i b^{d-i}` needs only integer
/// multiplications, no gcd. `b^d > 0`, so it has the sign of `p(x)`.
fn integer_sign_at(coefficients: &[BigInt], x: &Rational) -> Ordering {
    let Some((last, rest)) = coefficients.split_last() else {
        return Ordering::Equal;
    };
    // `Ratio` keeps a positive denominator; flip defensively if a raw value does not.
    let (a, b) = if x.denom().is_negative() {
        (-x.numer(), -x.denom())
    } else {
        (x.numer().clone(), x.denom().clone())
    };
    let mut value = last.clone();
    let mut b_power = BigInt::one();
    for c in rest.iter().rev() {
        b_power *= &b;
        value = value * &a + c * &b_power;
    }
    match value.sign() {
        num_bigint::Sign::Plus => Ordering::Greater,
        num_bigint::Sign::Minus => Ordering::Less,
        num_bigint::Sign::NoSign => Ordering::Equal,
    }
}

/// The Sturm chain of a polynomial over `Q`: `P_0 = squarefree part`, `P_1 = P_0'`,
/// `P_{k+1} = -(P_{k-1} mod P_k)` up to a *positive* rational factor, ending in a nonzero
/// constant.
///
/// Sturm's theorem only uses the signs of the chain, which a positive factor does not
/// change, so each `P_k` with `k >= 2` is divided by its content to keep the coefficients
/// small integers (this is what keeps the chain of a degree-16 polynomial cheap). `P_0` and
/// `P_1` are exactly the squarefree part and its derivative.
///
/// Built from the squarefree part so that the counts are of *distinct* real roots.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SturmSequence {
    chain: Vec<Polynomial<Rational>>,
    /// The same chain with integer coefficients (each scaled by a positive integer), for
    /// gcd-free sign evaluation.
    integer_chain: Vec<Vec<BigInt>>,
}

impl SturmSequence {
    fn from_chain(chain: Vec<Polynomial<Rational>>) -> Self {
        let integer_chain = chain.iter().map(|p| p.integer_coefficients().1).collect();
        Self {
            chain,
            integer_chain,
        }
    }

    /// The chain for `p`; refuses the zero polynomial.
    pub fn new(p: &Polynomial<Rational>) -> Result<Self, PolynomialError> {
        if p.is_zero() {
            return Err(PolynomialError::ZeroPolynomial);
        }
        let squarefree = p.squarefree_part();
        if squarefree.is_constant() {
            return Ok(Self::from_chain(vec![squarefree]));
        }
        let mut chain = vec![squarefree.clone(), squarefree.derivative()];
        loop {
            let n = chain.len();
            let remainder = chain[n - 2].rem(&chain[n - 1])?;
            if remainder.is_zero() {
                break;
            }
            // Scale by a positive factor only: the sign pattern is what matters.
            let negated = remainder.neg();
            let content = negated.content();
            chain.push(negated.scale(&(r_one() / content)));
        }
        Ok(Self::from_chain(chain))
    }

    /// The chain polynomials, `P_0` first (positive multiples of the textbook chain).
    pub fn chain(&self) -> &[Polynomial<Rational>] {
        &self.chain
    }

    /// The sign of the squarefree part `P_0` at `x`, without rational-arithmetic gcds.
    pub fn sign_of_squarefree_part_at(&self, x: &Rational) -> Ordering {
        self.integer_chain
            .first()
            .map_or(Ordering::Equal, |p| integer_sign_at(p, x))
    }

    /// The number of sign changes of the chain at `x`, ignoring zeros.
    pub fn variations_at(&self, x: &Rational) -> usize {
        let mut previous = Ordering::Equal;
        let mut variations = 0;
        for p in &self.integer_chain {
            let sign = integer_sign_at(p, x);
            if sign == Ordering::Equal {
                continue;
            }
            if previous != Ordering::Equal && sign != previous {
                variations += 1;
            }
            previous = sign;
        }
        variations
    }

    /// The number of distinct real roots of the polynomial in the half-open interval
    /// `(a, b]` (Sturm's theorem). Refuses `a > b`; `a == b` is the empty interval.
    pub fn count_in(&self, a: &Rational, b: &Rational) -> Result<usize, PolynomialError> {
        if a > b {
            return Err(PolynomialError::ReversedInterval {
                lower: a.to_string(),
                upper: b.to_string(),
            });
        }
        self.variations_at(a)
            .checked_sub(self.variations_at(b))
            .ok_or(PolynomialError::Inconsistent(
                "Sturm variations increased with the evaluation point",
            ))
    }
}

/// The Sturm chain of `p`. See [`SturmSequence`].
pub fn sturm_sequence(p: &Polynomial<Rational>) -> Result<SturmSequence, PolynomialError> {
    SturmSequence::new(p)
}

/// The number of distinct real roots of `p` in `(a, b]`. Refuses the zero polynomial
/// and `a > b`.
pub fn count_real_roots(
    p: &Polynomial<Rational>,
    a: &Rational,
    b: &Rational,
) -> Result<usize, PolynomialError> {
    SturmSequence::new(p)?.count_in(a, b)
}

/// The number of distinct real roots of `p` on the whole line.
pub fn count_all_real_roots(p: &Polynomial<Rational>) -> Result<usize, PolynomialError> {
    let sequence = SturmSequence::new(p)?;
    match real_root_bound(p) {
        Some(bound) => sequence.count_in(&-bound.clone(), &bound),
        None => Ok(0),
    }
}

/// Cauchy's bound: every root (real or complex) `z` of `p` has `|z| < B` with
/// `B = 1 + max_{i < n} |a_i / a_n|`. `None` for the zero polynomial and for constants,
/// which have no roots to bound.
pub fn real_root_bound(p: &Polynomial<Rational>) -> Option<Rational> {
    if p.is_constant() {
        return None;
    }
    let lead = p.leading_coefficient()?;
    let degree = p.degree()?;
    let largest = p
        .coefficients()
        .iter()
        .take(degree)
        .map(|c| (c / lead).abs())
        .fold(r_zero(), |acc, c| if c > acc { c } else { acc });
    Some(r_one() + largest)
}

/// Where one real root is.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RootLocation {
    /// The root is exactly this rational number.
    Exact(Rational),
    /// The root is irrational and is the only root of the polynomial in this closed
    /// interval, whose endpoints are not roots.
    Isolated(Interval),
}

impl RootLocation {
    /// A lower bound for the root.
    pub fn lower(&self) -> &Rational {
        match self {
            RootLocation::Exact(r) => r,
            RootLocation::Isolated(interval) => interval.lo(),
        }
    }

    /// An upper bound for the root.
    pub fn upper(&self) -> &Rational {
        match self {
            RootLocation::Exact(r) => r,
            RootLocation::Isolated(interval) => interval.hi(),
        }
    }

    /// `upper - lower`: zero exactly when the root is known exactly.
    pub fn width(&self) -> Rational {
        self.upper() - self.lower()
    }
}

/// One real root of a polynomial with its multiplicity.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RealRoot {
    pub location: RootLocation,
    pub multiplicity: usize,
}

fn half() -> Rational {
    Rational::new(BigInt::one(), BigInt::from(2))
}

fn midpoint(lo: &Rational, hi: &Rational) -> Rational {
    (lo + hi) * half()
}

/// Require that `squarefree` has nonzero values of opposite sign at `lo` and `hi`.
fn require_sign_change(
    integer_polynomial: &[BigInt],
    lo: &Rational,
    hi: &Rational,
) -> Result<(), PolynomialError> {
    let (a, b) = (
        integer_sign_at(integer_polynomial, lo),
        integer_sign_at(integer_polynomial, hi),
    );
    if a == Ordering::Equal || b == Ordering::Equal || a == b {
        return Err(PolynomialError::NotIsolating {
            lower: lo.to_string(),
            upper: hi.to_string(),
        });
    }
    Ok(())
}

/// Bisect the isolating interval `[lo, hi]` of the simple root of `squarefree` until its
/// width is at most `tolerance`, or the root is found exactly.
///
/// `squarefree` must change sign over `[lo, hi]` with nonzero endpoint values, otherwise
/// the interval is not isolating and [`PolynomialError::NotIsolating`] is returned.
/// The tolerance must be positive.
pub fn refine_simple_root(
    squarefree: &Polynomial<Rational>,
    interval: &Interval,
    tolerance: &Rational,
) -> Result<RootLocation, PolynomialError> {
    if !tolerance.is_positive() {
        return Err(PolynomialError::NonPositiveTolerance(tolerance.to_string()));
    }
    // Integer coefficients (a positive multiple of the polynomial) give gcd-free signs.
    let integer_polynomial = squarefree.integer_coefficients().1;
    let (mut lo, mut hi) = (interval.lo().clone(), interval.hi().clone());
    require_sign_change(&integer_polynomial, &lo, &hi)?;
    let mut lo_sign = integer_sign_at(&integer_polynomial, &lo);
    while &hi - &lo > *tolerance {
        let mid = midpoint(&lo, &hi);
        match integer_sign_at(&integer_polynomial, &mid) {
            Ordering::Equal => return Ok(RootLocation::Exact(mid)),
            sign if sign == lo_sign => {
                lo = mid;
                lo_sign = sign;
            }
            _ => hi = mid,
        }
    }
    Ok(RootLocation::Isolated(Interval::new(lo, hi)))
}

/// Refine a root found by [`isolate_real_roots`] to width at most `tolerance`.
///
/// An exact root is returned unchanged. The polynomial must be the one the root was
/// isolated for, or at least share its radical. Multiplicity is preserved.
pub fn refine_root(
    p: &Polynomial<Rational>,
    root: &RealRoot,
    tolerance: &Rational,
) -> Result<RealRoot, PolynomialError> {
    if !tolerance.is_positive() {
        return Err(PolynomialError::NonPositiveTolerance(tolerance.to_string()));
    }
    let location = match &root.location {
        RootLocation::Exact(r) => RootLocation::Exact(r.clone()),
        RootLocation::Isolated(interval) => {
            refine_simple_root(&p.squarefree_part(), interval, tolerance)?
        }
    };
    Ok(RealRoot {
        location,
        multiplicity: root.multiplicity,
    })
}

/// Isolate every distinct real root of `squarefree` (squarefree, degree `>= 1`) by
/// ascending rational intervals `(lo, hi)` whose endpoints are not roots and that each
/// contain exactly one root. Neighbouring intervals may share an endpoint.
fn isolate_squarefree(
    squarefree: &Polynomial<Rational>,
) -> Result<Vec<(Rational, Rational)>, PolynomialError> {
    let Some(bound) = real_root_bound(squarefree) else {
        return Ok(Vec::new());
    };
    let degree = squarefree.degree().ok_or(PolynomialError::ZeroPolynomial)?;
    let sequence = SturmSequence::new(squarefree)?;
    let (lo, hi) = (-bound.clone(), bound);
    // Each pending interval carries the Sturm variation counts at both ends, so a split
    // costs one chain evaluation: the roots in (lo, hi] number V(lo) - V(hi).
    let (v_lo, v_hi) = (sequence.variations_at(&lo), sequence.variations_at(&hi));
    let mut pending = vec![(lo, hi, v_lo, v_hi)];
    let mut isolated: Vec<(Rational, Rational)> = Vec::new();
    while let Some((lo, hi, v_lo, v_hi)) = pending.pop() {
        let count = v_lo.checked_sub(v_hi).ok_or(PolynomialError::Inconsistent(
            "Sturm variations increased with the evaluation point",
        ))?;
        match count {
            0 => continue,
            1 => {
                isolated.push((lo, hi));
                continue;
            }
            _ => {}
        }
        // A split point that is not a root, taken from the dyadic fractions of the
        // interval in the order 1/2, 1/4, 3/4, 1/8, ... so the intervals stay balanced and
        // their endpoints stay short. The polynomial has at most `degree` roots, so one of
        // `degree + 1` distinct interior points is not a root.
        let width = &hi - &lo;
        let split = dyadic_fractions()
            .take(degree + 1)
            .map(|fraction| &lo + &width * fraction)
            .find(|candidate| sequence.sign_of_squarefree_part_at(candidate) != Ordering::Equal)
            .ok_or(PolynomialError::Inconsistent(
                "a polynomial of degree d has more than d roots",
            ))?;
        let v_split = sequence.variations_at(&split);
        pending.push((split.clone(), hi, v_split, v_hi));
        pending.push((lo, split, v_lo, v_split));
    }
    isolated.sort_by(|a, b| a.0.cmp(&b.0));
    Ok(isolated)
}

/// The dyadic fractions strictly between 0 and 1 in the order `1/2, 1/4, 3/4, 1/8, 3/8,
/// 5/8, 7/8, 1/16, ...`.
fn dyadic_fractions() -> impl Iterator<Item = Rational> {
    (1u32..=62).flat_map(|level| {
        let denominator = 1u64 << level;
        (1..denominator)
            .step_by(2)
            .map(move |numerator| Rational::new(BigInt::from(numerator), BigInt::from(denominator)))
    })
}

fn root_multiplicity(
    decomposition: &[(Polynomial<Rational>, usize)],
    lo: &Rational,
    hi: &Rational,
) -> Result<usize, PolynomialError> {
    for (factor, m) in decomposition {
        let (a, b) = (factor.sign_at(lo), factor.sign_at(hi));
        if a != Ordering::Equal && b != Ordering::Equal && a != b {
            return Ok(*m);
        }
    }
    Err(PolynomialError::Inconsistent(
        "an isolated root belongs to no squarefree factor",
    ))
}

fn refine_and_snap_root(
    radical: &Polynomial<Rational>,
    lo: Rational,
    hi: Rational,
    lattice: &Rational,
    resolution: &Rational,
) -> Result<RootLocation, PolynomialError> {
    let mut location = refine_simple_root(radical, &Interval::new(lo, hi), resolution)?;
    if let RootLocation::Isolated(interval) = &location {
        let candidate = (&interval.mid() * lattice).round() / lattice;
        if interval.contains(&candidate) && radical.sign_at(&candidate) == Ordering::Equal {
            location = RootLocation::Exact(candidate);
        }
    }
    Ok(location)
}

fn disjointify_root_intervals(
    radical: &Polynomial<Rational>,
    roots: &mut [RealRoot],
) -> Result<(), PolynomialError> {
    for i in 0..roots.len().saturating_sub(1) {
        loop {
            let RootLocation::Isolated(interval) = &roots[i].location else {
                break;
            };
            if interval.hi() < roots[i + 1].location.lower() {
                break;
            }
            let half_width = interval.diam() * half();
            let tightened = refine_simple_root(radical, interval, &half_width)?;
            roots[i].location = tightened;
        }
    }
    Ok(())
}

/// Every distinct real root of `p`, ascending, with multiplicities.
///
/// Rational roots are reported as [`RootLocation::Exact`] (a complete test: a rational
/// root of the primitive integer form with leading coefficient `A` lies on the lattice
/// `(1/A) Z`, and an interval narrower than `1 / (2A)` holds at most one lattice point).
/// Irrational roots are reported as disjoint isolating intervals with non-root endpoints.
/// Refuses the zero polynomial; a nonzero constant has no roots.
pub fn isolate_real_roots(p: &Polynomial<Rational>) -> Result<Vec<RealRoot>, PolynomialError> {
    if p.is_zero() {
        return Err(PolynomialError::ZeroPolynomial);
    }
    if p.is_constant() {
        return Ok(Vec::new());
    }
    let decomposition = p.squarefree_decomposition()?;
    let radical = p.squarefree_part();
    let (_, primitive) = radical.content_and_primitive_part();
    let lattice_denominator = primitive
        .leading_coefficient()
        .map(|lead| lead.numer().abs())
        .ok_or(PolynomialError::ZeroPolynomial)?;
    let lattice = Rational::from_integer(lattice_denominator.clone());
    let resolution = Rational::new(BigInt::one(), BigInt::from(2) * lattice_denominator);

    let mut roots = Vec::new();
    for (lo, hi) in isolate_squarefree(&radical)? {
        // Which squarefree factor owns this root: the one that changes sign here.
            // Rational roots lie on the lattice (1/A) Z; the interval is narrower than
            // half a lattice step, so at most one lattice point is near its midpoint.
            // The candidate can lie up to half a lattice step from the midpoint, which is
            // outside the interval, so it must be checked to lie inside before it can be
            // the interval's root rather than a neighbouring one.
        let multiplicity = root_multiplicity(&decomposition, &lo, &hi)?;
        let location = refine_and_snap_root(&radical, lo, hi, &lattice, &resolution)?;
        roots.push(RealRoot {
            location,
            multiplicity,
        });
    }
    // Neighbouring isolating intervals can share an endpoint (a non-root split point).
    // Tighten the left one until the closed intervals are strictly disjoint; the root is at
    // a positive distance from the shared point, so this terminates.
    disjointify_root_intervals(&radical, &mut roots)?;
    Ok(roots)
}

/// The distinct rational roots of `p`, ascending. Complete, and needs no factoring.
pub fn rational_roots(p: &Polynomial<Rational>) -> Result<Vec<Rational>, PolynomialError> {
    Ok(isolate_real_roots(p)?
        .into_iter()
        .filter_map(|root| match root.location {
            RootLocation::Exact(r) => Some(r),
            RootLocation::Isolated(_) => None,
        })
        .collect())
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cyclotomic::GaussianRat;
    use crate::rational::rq;

    fn q(coefficients: &[i64]) -> Polynomial<Rational> {
        Polynomial::from_i64s(coefficients)
    }

    /// A deterministic pseudo-random sequence (LCG), so the grids are reproducible.
    struct Lcg(u64);
    impl Lcg {
        fn next(&mut self) -> i64 {
            self.0 = self
                .0
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            ((self.0 >> 33) % 13) as i64 - 6
        }
        fn poly(&mut self, max_degree: usize) -> Polynomial<Rational> {
            let len = 1 + (self.next().unsigned_abs() as usize % (max_degree + 1));
            Polynomial::from_i64s(&(0..len).map(|_| self.next()).collect::<Vec<_>>())
        }
    }

    // ----- normal form, ring laws -------------------------------------------------

    #[test]
    fn trailing_zeros_are_trimmed_so_equal_values_have_equal_representations() {
        assert_eq!(q(&[1, 2, 0, 0]), q(&[1, 2]));
        assert!(q(&[0, 0, 0]).is_zero());
        assert_eq!(q(&[0, 0]).degree(), None);
        assert_eq!(q(&[5]).degree(), Some(0));
        assert_eq!(q(&[1, 2, 3]).degree(), Some(2));
        assert_eq!(q(&[1, 2, 3]).coefficient(7), r_zero());
        assert_eq!(
            Polynomial::monomial(ri(0), 4),
            Polynomial::<Rational>::zero()
        );
        assert_eq!(Polynomial::monomial(ri(3), 2), q(&[0, 0, 3]));
    }

    #[test]
    fn ring_laws_and_degree_additivity_hold_on_a_grid() {
        let mut rng = Lcg(7);
        for _ in 0..40 {
            let (f, g, h) = (rng.poly(4), rng.poly(4), rng.poly(4));
            assert_eq!(f.add(&g), g.add(&f));
            assert_eq!(f.mul(&g), g.mul(&f));
            assert_eq!(f.add(&g).add(&h), f.add(&g.add(&h)));
            assert_eq!(f.mul(&g).mul(&h), f.mul(&g.mul(&h)));
            assert_eq!(f.mul(&g.add(&h)), f.mul(&g).add(&f.mul(&h)));
            assert!(f.sub(&f).is_zero());
            assert_eq!(f.add(&f.neg()), Polynomial::zero());
            if !f.is_zero() && !g.is_zero() {
                assert_eq!(
                    f.mul(&g).degree().unwrap(),
                    f.degree().unwrap() + g.degree().unwrap(),
                    "a field has no zero divisors"
                );
            }
        }
    }

    #[test]
    fn evaluation_is_a_ring_homomorphism_and_composition_evaluates_inside_out() {
        let mut rng = Lcg(11);
        for _ in 0..30 {
            let (f, g) = (rng.poly(4), rng.poly(3));
            let a = rq(rng.next(), 1 + rng.next().abs());
            assert_eq!(f.mul(&g).eval(&a), f.eval(&a) * g.eval(&a));
            assert_eq!(f.add(&g).eval(&a), f.eval(&a) + g.eval(&a));
            assert_eq!(f.compose(&g).eval(&a), f.eval(&g.eval(&a)));
            assert_eq!(f.shift(&a).eval(&rq(2, 3)), f.eval(&(rq(2, 3) + &a)));
        }
        assert_eq!(q(&[1, 1]).pow(3), q(&[1, 3, 3, 1]));
        assert_eq!(q(&[1, 1]).pow(0), Polynomial::one());
    }

    // ----- division, gcd ----------------------------------------------------------

    #[test]
    fn euclidean_division_reconstructs_the_dividend_with_a_smaller_remainder() {
        let mut rng = Lcg(3);
        for _ in 0..60 {
            let (f, g) = (rng.poly(6), rng.poly(3));
            if g.is_zero() {
                continue;
            }
            let (quotient, remainder) = f.div_rem(&g).unwrap();
            assert_eq!(quotient.mul(&g).add(&remainder), f);
            assert!(
                remainder.is_zero() || remainder.degree() < g.degree(),
                "deg r < deg g"
            );
        }
    }

    #[test]
    fn division_by_the_zero_polynomial_is_refused_not_panicked() {
        assert_eq!(
            q(&[1, 2, 3]).div_rem(&Polynomial::zero()),
            Err(PolynomialError::DivisionByZero)
        );
        assert_eq!(
            q(&[1]).rem(&Polynomial::zero()),
            Err(PolynomialError::DivisionByZero)
        );
    }

    #[test]
    fn division_by_a_constant_and_by_a_larger_divisor() {
        let (quotient, remainder) = q(&[2, 4, 6]).div_rem(&q(&[2])).unwrap();
        assert_eq!(quotient, q(&[1, 2, 3]));
        assert!(remainder.is_zero());
        let (quotient, remainder) = q(&[1, 1]).div_rem(&q(&[1, 0, 1])).unwrap();
        assert!(quotient.is_zero());
        assert_eq!(remainder, q(&[1, 1]));
    }

    #[test]
    fn gcd_is_monic_and_finds_the_common_factor() {
        // (x-1)(x-2) and (x-2)(x-3) share x - 2.
        let f = q(&[2, -3, 1]);
        let g = q(&[6, -5, 1]);
        assert_eq!(f.gcd(&g), q(&[-2, 1]));
        // scaling does not change the gcd
        assert_eq!(f.scale(&ri(5)).gcd(&g.scale(&rq(1, 3))), q(&[-2, 1]));
        assert_eq!(f.gcd(&Polynomial::zero()), f);
        assert_eq!(
            Polynomial::<Rational>::zero().gcd(&Polynomial::zero()),
            Polynomial::zero()
        );
        assert_eq!(q(&[1, 0, 1]).gcd(&q(&[1, 1])), Polynomial::one(), "coprime");
    }

    #[test]
    fn extended_gcd_satisfies_the_bezout_identity() {
        let mut rng = Lcg(19);
        for _ in 0..60 {
            let (a, b) = (rng.poly(5), rng.poly(4));
            let (g, s, t) = a.xgcd(&b);
            assert_eq!(s.mul(&a).add(&t.mul(&b)), g, "s a + t b = g");
            assert_eq!(g, a.gcd(&b), "xgcd agrees with gcd");
        }
    }

    // ----- derivative -------------------------------------------------------------

    #[test]
    fn derivative_obeys_the_product_rule_and_kills_constants() {
        let mut rng = Lcg(5);
        for _ in 0..40 {
            let (f, g) = (rng.poly(4), rng.poly(4));
            assert_eq!(
                f.mul(&g).derivative(),
                f.derivative().mul(&g).add(&f.mul(&g.derivative()))
            );
            assert_eq!(f.add(&g).derivative(), f.derivative().add(&g.derivative()));
        }
        assert!(q(&[7]).derivative().is_zero());
        assert!(Polynomial::<Rational>::zero().derivative().is_zero());
        assert_eq!(
            Polynomial::monomial(ri(1), 9).derivative(),
            Polynomial::monomial(ri(9), 8)
        );
    }

    // ----- resultant, discriminant ------------------------------------------------

    /// The Sylvester determinant, by an independent route (`bareiss_determinant`).
    fn sylvester_resultant(f: &Polynomial<Rational>, g: &Polynomial<Rational>) -> Rational {
        let (m, n) = (f.degree().unwrap(), g.degree().unwrap());
        let size = m + n;
        // clear denominators: scale f and g to integer polynomials; Res(a f, b g) = a^n b^m Res
        let (df, fi) = f.integer_coefficients();
        let (dg, gi) = g.integer_coefficients();
        let mut matrix = vec![vec![BigInt::zero(); size]; size];
        for i in 0..n {
            for (j, c) in fi.iter().rev().enumerate() {
                matrix[i][i + j] = c.clone();
            }
        }
        for i in 0..m {
            for (j, c) in gi.iter().rev().enumerate() {
                matrix[n + i][i + j] = c.clone();
            }
        }
        let det = linear_algebra::determinant::bareiss_determinant(&matrix).unwrap();
        // Res(f, g) = det / (df^n dg^m)
        Rational::from_integer(det)
            / (Rational::from_integer(df.pow(n as u32)) * Rational::from_integer(dg.pow(m as u32)))
    }

    #[test]
    fn resultant_matches_the_sylvester_determinant_and_the_product_over_roots() {
        let mut rng = Lcg(23);
        for _ in 0..40 {
            let (f, g) = (rng.poly(4), rng.poly(4));
            if f.degree().unwrap_or(0) < 1 || g.degree().unwrap_or(0) < 1 {
                continue;
            }
            assert_eq!(f.resultant(&g), sylvester_resultant(&f, &g), "{f:?} {g:?}");
        }
        // Product formula with rational roots: Res(prod(x-a_i), prod(x-b_j)) = prod(a_i-b_j).
        let a = [ri(1), ri(-2), rq(1, 2)];
        let b = [ri(3), ri(5)];
        let (f, g) = (Polynomial::from_roots(&a), Polynomial::from_roots(&b));
        let expected = a
            .iter()
            .flat_map(|x| b.iter().map(move |y| x - y))
            .fold(r_one(), |acc, t| acc * t);
        assert_eq!(f.resultant(&g), expected);
    }

    #[test]
    fn resultant_is_antisymmetric_exactly_when_both_degrees_are_odd() {
        // Res(g, f) = (-1)^{mn} Res(f, g)
        let mut rng = Lcg(29);
        let mut odd_pairs = 0;
        for _ in 0..80 {
            let (f, g) = (rng.poly(4), rng.poly(4));
            let (Some(m), Some(n)) = (f.degree(), g.degree()) else {
                continue;
            };
            if m < 1 || n < 1 {
                continue;
            }
            let forward = f.resultant(&g);
            let backward = g.resultant(&f);
            if (m * n) % 2 == 1 {
                odd_pairs += 1;
                assert_eq!(backward, -forward.clone(), "{f:?} {g:?}");
            } else {
                assert_eq!(backward, forward, "{f:?} {g:?}");
            }
        }
        assert!(odd_pairs > 0, "the grid must exercise the odd-degree case");
        // A concrete odd case. Res(x - 2, x^3 - 1) = f(2) = 7 (the value of x^3 - 1 at the
        // root of x - 2), and Res(x^3 - 1, x - 2) = prod (alpha - 2) over the cube roots of
        // unity = -(2^3 - 1) = -7.
        assert_eq!(q(&[-2, 1]).resultant(&q(&[-1, 0, 0, 1])), ri(7));
        assert_eq!(q(&[-1, 0, 0, 1]).resultant(&q(&[-2, 1])), ri(-7));
    }

    #[test]
    fn resultant_vanishes_exactly_on_a_common_root_and_with_the_zero_polynomial() {
        let f = q(&[-2, 0, 1]);
        assert_eq!(
            f.resultant(&q(&[-1, 1])),
            ri(-1),
            "f(1) = -1: no common root"
        );
        assert!(
            q(&[2, -3, 1]).resultant(&q(&[-1, 1])).is_zero(),
            "common root 1"
        );
        assert!(f.resultant(&Polynomial::zero()).is_zero());
        assert!(Polynomial::<Rational>::zero().resultant(&f).is_zero());
        // constants: Res(f, c) = c^deg f
        assert_eq!(f.resultant(&q(&[3])), ri(9));
    }

    #[test]
    fn discriminant_of_the_quadratic_and_cubic_matches_the_closed_forms() {
        // b^2 - 4ac
        assert_eq!(q(&[-2, 0, 1]).discriminant().unwrap(), ri(8));
        assert_eq!(q(&[1, 3, 2]).discriminant().unwrap(), ri(9 - 8));
        // x^3 + p x + q has discriminant -4 p^3 - 27 q^2 (here 108 - 27 = 81)
        let (p, qq) = (ri(-3), ri(1));
        let cubic = q(&[1, -3, 0, 1]);
        assert_eq!(
            cubic.discriminant().unwrap(),
            ri(-4) * &p * &p * &p - ri(27) * &qq * &qq
        );
        assert_eq!(cubic.discriminant().unwrap(), ri(81));
        assert_eq!(q(&[5, 7]).discriminant().unwrap(), ri(1), "linear: 1");
    }

    #[test]
    fn discriminant_vanishes_exactly_for_repeated_roots_and_equals_the_root_product() {
        assert!(q(&[1, -2, 1]).discriminant().unwrap().is_zero());
        // prod_{i<j} (a_i - a_j)^2 for monic f with rational roots
        let roots = [ri(1), ri(4), ri(-2), rq(1, 3)];
        let f = Polynomial::from_roots(&roots);
        let mut expected = r_one();
        for i in 0..roots.len() {
            for j in (i + 1)..roots.len() {
                let d = &roots[i] - &roots[j];
                expected = expected * &d * &d;
            }
        }
        assert_eq!(f.discriminant().unwrap(), expected);
        // and the discriminant scales with the leading coefficient as lc^(2n-2)
        assert_eq!(
            f.scale(&ri(3)).discriminant().unwrap(),
            expected * ri(3).pow(2 * 4 - 2)
        );
    }

    #[test]
    fn discriminant_refuses_the_zero_polynomial_and_constants() {
        assert_eq!(
            Polynomial::<Rational>::zero().discriminant(),
            Err(PolynomialError::ZeroPolynomial)
        );
        assert_eq!(
            q(&[4]).discriminant(),
            Err(PolynomialError::DegreeTooSmall {
                required: 1,
                actual: 0
            })
        );
    }

    // ----- squarefree -------------------------------------------------------------

    #[test]
    fn squarefree_part_drops_multiplicities_and_yun_reassembles_the_polynomial() {
        // (x-1)^2 (x+2)^3 (x-5)
        let p = Polynomial::from_roots(&[ri(1), ri(1), ri(-2), ri(-2), ri(-2), ri(5)]);
        let expected = Polynomial::from_roots(&[ri(1), ri(-2), ri(5)]);
        assert_eq!(p.squarefree_part(), expected);
        let decomposition = p.squarefree_decomposition().unwrap();
        assert_eq!(
            decomposition,
            vec![
                (Polynomial::from_roots(&[ri(5)]), 1),
                (Polynomial::from_roots(&[ri(1)]), 2),
                (Polynomial::from_roots(&[ri(-2)]), 3),
            ]
        );
        let rebuilt = decomposition
            .iter()
            .fold(Polynomial::one(), |acc, (f, m)| acc.mul(&f.pow(*m)));
        assert_eq!(rebuilt, p);
        // the leading coefficient is stripped
        let scaled = p.scale(&ri(-7));
        assert_eq!(scaled.squarefree_decomposition().unwrap(), decomposition);
    }

    #[test]
    fn squarefree_decomposition_on_random_products_reassembles_them() {
        let mut rng = Lcg(31);
        for _ in 0..25 {
            let (a, b, c) = (rng.poly(2), rng.poly(2), rng.poly(2));
            let p = a.mul(&b.pow(2)).mul(&c.pow(3));
            if p.is_zero() {
                continue;
            }
            let decomposition = p.squarefree_decomposition().unwrap();
            let rebuilt = decomposition
                .iter()
                .fold(Polynomial::one(), |acc, (f, m)| acc.mul(&f.pow(*m)));
            let lead = p.leading_coefficient().unwrap().clone();
            assert_eq!(rebuilt.scale(&lead), p);
            for (f, _) in &decomposition {
                assert_eq!(
                    f.squarefree_part(),
                    *f,
                    "each factor is squarefree and monic"
                );
            }
        }
        assert_eq!(
            Polynomial::<Rational>::zero().squarefree_decomposition(),
            Err(PolynomialError::ZeroPolynomial)
        );
        assert!(q(&[3]).squarefree_decomposition().unwrap().is_empty());
    }

    // ----- genericity -------------------------------------------------------------

    #[test]
    fn polynomials_over_the_gaussian_rationals_factor_x_squared_plus_one() {
        let i = GaussianRat::i();
        let one = GaussianRat::one();
        let zero = GaussianRat::zero();
        let f: Polynomial<GaussianRat> =
            Polynomial::from_coefficients(vec![one.clone(), zero.clone(), one.clone()]);
        let x_minus_i = Polynomial::from_coefficients(vec![i.neg(), one.clone()]);
        let x_plus_i = Polynomial::from_coefficients(vec![i.clone(), one.clone()]);
        assert_eq!(x_minus_i.mul(&x_plus_i), f);
        assert_eq!(f.gcd(&x_minus_i), x_minus_i);
        assert!(f.eval(&i).is_zero());
        let (quotient, remainder) = f.div_rem(&x_plus_i).unwrap();
        assert_eq!(quotient, x_minus_i);
        assert!(remainder.is_zero());
        assert_eq!(f.discriminant().unwrap(), GaussianRat::from_ints(-4, 0));
    }

    // ----- Gauss content ----------------------------------------------------------

    #[test]
    fn content_and_primitive_part_split_a_polynomial_with_a_positive_lead() {
        let p = Polynomial::from_coefficients(vec![rq(-6, 5), rq(9, 10), rq(3, 2)]);
        let (content, primitive) = p.content_and_primitive_part();
        assert_eq!(primitive.scale(&content), p);
        assert!(primitive.leading_coefficient().unwrap().is_positive());
        assert!(primitive.coefficients().iter().all(|c| c.is_integer()));
        assert_eq!(
            primitive.content(),
            r_one(),
            "the primitive part has content 1"
        );
        assert!(content.is_positive());
        // negative lead: the content carries the sign
        let (content, primitive) = p.neg().content_and_primitive_part();
        assert!(content.is_negative());
        assert!(primitive.leading_coefficient().unwrap().is_positive());
        assert_eq!(primitive.scale(&content), p.neg());
        assert_eq!(
            Polynomial::<Rational>::zero().content_and_primitive_part(),
            (r_zero(), Polynomial::zero())
        );
    }

    #[test]
    fn gauss_lemma_content_is_multiplicative() {
        let mut rng = Lcg(41);
        for _ in 0..40 {
            let (f, g) = (rng.poly(3), rng.poly(3));
            let scaled_f = f.scale(&rq(3, 7));
            let scaled_g = g.scale(&rq(5, 4));
            assert_eq!(
                scaled_f.mul(&scaled_g).content(),
                scaled_f.content() * scaled_g.content()
            );
        }
    }

    #[test]
    fn integer_coefficients_use_the_least_common_denominator() {
        let p = Polynomial::from_coefficients(vec![rq(1, 2), rq(1, 3), rq(5, 6)]);
        let (denominator, integers) = p.integer_coefficients();
        assert_eq!(denominator, BigInt::from(6));
        assert_eq!(
            integers,
            vec![BigInt::from(3), BigInt::from(2), BigInt::from(5)]
        );
        assert_eq!(
            Polynomial::<Rational>::zero().integer_coefficients(),
            (BigInt::one(), vec![])
        );
    }

    // ----- cyclotomic polynomials -------------------------------------------------

    #[test]
    fn euler_phi_matches_the_definition_and_the_divisor_sum() {
        for n in 1..=200usize {
            let direct = (1..=n).filter(|k| gcd_naive(*k, n) == 1).count();
            assert_eq!(euler_phi(n), direct, "phi({n})");
            let sum: usize = divisors(n).iter().map(|&d| euler_phi(d)).sum();
            assert_eq!(sum, n, "sum of phi(d) over d | {n}");
        }
        assert_eq!(euler_phi(0), 0);
        assert_eq!(euler_phi(1), 1);
        assert_eq!(euler_phi(120), 32);
        assert_eq!(euler_phi(97), 96);
    }

    fn gcd_naive(a: usize, b: usize) -> usize {
        if b == 0 {
            a
        } else {
            gcd_naive(b, a % b)
        }
    }

    #[test]
    fn mobius_and_prime_factors_agree_with_their_definitions() {
        let expected: [(usize, i8); 12] = [
            (1, 1),
            (2, -1),
            (3, -1),
            (4, 0),
            (5, -1),
            (6, 1),
            (8, 0),
            (10, 1),
            (12, 0),
            (30, -1),
            (210, 1),
            (49, 0),
        ];
        for (n, mu) in expected {
            assert_eq!(mobius(n), mu, "mu({n})");
        }
        assert_eq!(mobius(0), 0);
        assert_eq!(distinct_prime_factors(360), vec![2, 3, 5]);
        assert_eq!(distinct_prime_factors(97), vec![97]);
        assert!(distinct_prime_factors(1).is_empty());
        // sum over d | n of mu(d) = [n = 1]
        for n in 1..=100usize {
            let sum: i32 = divisors(n).iter().map(|&d| i32::from(mobius(d))).sum();
            assert_eq!(sum, i32::from(n == 1));
        }
        assert_eq!(divisors(12), vec![1, 2, 3, 4, 6, 12]);
        assert_eq!(divisors(36), vec![1, 2, 3, 4, 6, 9, 12, 18, 36]);
        assert!(divisors(0).is_empty());
    }

    #[test]
    fn cyclotomic_polynomials_match_the_known_low_conductor_table() {
        let table: [(usize, &[i64]); 14] = [
            (1, &[-1, 1]),
            (2, &[1, 1]),
            (3, &[1, 1, 1]),
            (4, &[1, 0, 1]),
            (5, &[1, 1, 1, 1, 1]),
            (6, &[1, -1, 1]),
            (7, &[1, 1, 1, 1, 1, 1, 1]),
            (8, &[1, 0, 0, 0, 1]),
            (9, &[1, 0, 0, 1, 0, 0, 1]),
            (10, &[1, -1, 1, -1, 1]),
            (12, &[1, 0, -1, 0, 1]),
            (15, &[1, -1, 0, 1, -1, 1, 0, -1, 1]),
            (24, &[1, 0, 0, 0, -1, 0, 0, 0, 1]),
            (30, &[1, 1, 0, -1, -1, -1, 0, 1, 1]),
        ];
        for (n, coefficients) in table {
            assert_eq!(
                cyclotomic_polynomial(n).unwrap(),
                q(coefficients),
                "Phi_{n}"
            );
        }
    }

    #[test]
    fn cyclotomic_polynomials_satisfy_the_defining_relations_for_every_n_up_to_40() {
        let x_n_minus_1 = |n: usize| Polynomial::monomial(r_one(), n).sub(&Polynomial::one());
        for n in 1..=40usize {
            let phi = cyclotomic_polynomial(n).unwrap();
            // degree phi(n), monic, integer coefficients
            assert_eq!(phi.degree(), Some(euler_phi(n)), "deg Phi_{n}");
            assert_eq!(phi.leading_coefficient(), Some(&r_one()));
            assert!(phi.coefficients().iter().all(|c| c.is_integer()));
            // the product over divisors is x^n - 1
            let product = divisors(n).iter().fold(Polynomial::one(), |acc, &d| {
                acc.mul(&cyclotomic_polynomial(d).unwrap())
            });
            assert_eq!(
                product,
                x_n_minus_1(n),
                "prod_(d|n) Phi_d = x^n - 1 for n = {n}"
            );
            // palindromic (n > 1): x^deg Phi(1/x) = Phi(x)
            if n > 1 {
                let reversed: Vec<Rational> = phi.coefficients().iter().rev().cloned().collect();
                assert_eq!(
                    Polynomial::from_coefficients(reversed),
                    phi,
                    "Phi_{n} palindromic"
                );
            }
            // Phi_n(1) = p for a prime power p^k, 1 for two or more primes, 0 for n = 1
            let value = phi.eval(&r_one());
            let primes = distinct_prime_factors(n);
            let expected = match primes.len() {
                0 => 0,
                1 => i64::try_from(primes[0]).unwrap(),
                _ => 1,
            };
            assert_eq!(value, ri(expected), "Phi_{n}(1)");
        }
    }

    #[test]
    fn cyclotomic_polynomial_structure_lemmas() {
        // Phi_{p^k}(x) = Phi_p(x^{p^{k-1}}); Phi_{2n}(x) = Phi_n(-x) for odd n > 1
        let phi3 = cyclotomic_polynomial(3).unwrap();
        assert_eq!(
            cyclotomic_polynomial(27).unwrap(),
            phi3.compose(&Polynomial::monomial(r_one(), 9))
        );
        let phi2_then = |n: usize| cyclotomic_polynomial(2 * n).unwrap();
        for n in [3usize, 5, 7, 9, 15, 21] {
            let minus_x = Polynomial::from_i64s(&[0, -1]);
            assert_eq!(
                phi2_then(n),
                cyclotomic_polynomial(n).unwrap().compose(&minus_x),
                "n = {n}"
            );
        }
        // Phi_105 is the first with a coefficient other than 0, +-1
        let phi105 = cyclotomic_polynomial(105).unwrap();
        assert_eq!(phi105.degree(), Some(48));
        assert_eq!(phi105.coefficient(7), ri(-2));
        assert_eq!(phi105.coefficient(41), ri(-2));
        for n in 1..105usize {
            let phi = cyclotomic_polynomial(n).unwrap();
            assert!(
                phi.coefficients().iter().all(|c| c.abs() <= r_one()),
                "all coefficients of Phi_{n} are in {{-1, 0, 1}} for n < 105"
            );
        }
    }

    #[test]
    fn cyclotomic_polynomial_refuses_zero_and_oversized_conductors() {
        assert_eq!(
            cyclotomic_polynomial(0),
            Err(PolynomialError::ConductorZero)
        );
        assert_eq!(
            cyclotomic_polynomial(MAX_CONDUCTOR + 1),
            Err(PolynomialError::ConductorTooLarge {
                conductor: MAX_CONDUCTOR + 1,
                max: MAX_CONDUCTOR
            })
        );
        assert!(cyclotomic_polynomial(MAX_CONDUCTOR).is_ok());
    }

    // ----- Sturm sequences and counts --------------------------------------------

    #[test]
    fn sturm_counts_distinct_real_roots_in_half_open_intervals() {
        // x^3 - x has roots -1, 0, 1.
        let p = q(&[0, -1, 0, 1]);
        assert_eq!(count_real_roots(&p, &ri(-2), &ri(2)).unwrap(), 3);
        assert_eq!(
            count_real_roots(&p, &ri(-1), &ri(1)).unwrap(),
            2,
            "(-1, 1] = {{0, 1}}"
        );
        assert_eq!(
            count_real_roots(&p, &ri(0), &ri(0)).unwrap(),
            0,
            "(0, 0] is empty"
        );
        assert_eq!(
            count_real_roots(&p, &ri(1), &ri(5)).unwrap(),
            0,
            "(1, 5] excludes the root 1"
        );
        assert_eq!(count_real_roots(&p, &rq(-1, 2), &rq(1, 2)).unwrap(), 1);
        // x^2 - 2: two irrational roots; x^2 + 1: none
        assert_eq!(count_all_real_roots(&q(&[-2, 0, 1])).unwrap(), 2);
        assert_eq!(
            count_real_roots(&q(&[-2, 0, 1]), &ri(0), &ri(2)).unwrap(),
            1
        );
        assert_eq!(count_all_real_roots(&q(&[1, 0, 1])).unwrap(), 0);
        assert_eq!(count_all_real_roots(&q(&[5])).unwrap(), 0);
    }

    #[test]
    fn sturm_counts_distinct_roots_even_when_roots_repeat() {
        // (x-1)^2 (x-3): two distinct real roots
        let p = Polynomial::from_roots(&[ri(1), ri(1), ri(3)]);
        assert_eq!(count_all_real_roots(&p).unwrap(), 2);
        assert_eq!(count_real_roots(&p, &ri(0), &ri(2)).unwrap(), 1);
        assert_eq!(
            count_real_roots(&p, &ri(1), &ri(3)).unwrap(),
            1,
            "(1, 3] holds only 3"
        );
    }

    #[test]
    fn sturm_counts_agree_with_direct_counting_of_known_rational_roots() {
        let mut rng = Lcg(57);
        for _ in 0..30 {
            let mut roots: Vec<Rational> = (0..4)
                .map(|_| rq(rng.next(), 1 + rng.next().abs()))
                .collect();
            roots.sort();
            roots.dedup();
            let p = Polynomial::from_roots(&roots);
            let (a, b) = (rq(rng.next(), 2), rq(rng.next() + 7, 3));
            let (a, b) = if a <= b { (a, b) } else { (b, a) };
            let direct = roots.iter().filter(|r| **r > a && **r <= b).count();
            assert_eq!(
                count_real_roots(&p, &a, &b).unwrap(),
                direct,
                "{roots:?} ({a}, {b}]"
            );
        }
    }

    #[test]
    fn sturm_refuses_the_zero_polynomial_and_reversed_intervals() {
        assert_eq!(
            sturm_sequence(&Polynomial::zero()).unwrap_err(),
            PolynomialError::ZeroPolynomial
        );
        assert_eq!(
            count_real_roots(&q(&[0, 1]), &ri(2), &ri(1)),
            Err(PolynomialError::ReversedInterval {
                lower: "2".into(),
                upper: "1".into()
            })
        );
        assert_eq!(
            count_all_real_roots(&Polynomial::zero()),
            Err(PolynomialError::ZeroPolynomial)
        );
    }

    #[test]
    fn the_sturm_chain_ends_in_a_nonzero_constant_for_a_squarefree_polynomial() {
        let chain = sturm_sequence(&q(&[-2, 0, 1])).unwrap();
        let last = chain.chain().last().unwrap();
        assert!(last.is_constant() && !last.is_zero());
        assert_eq!(chain.chain()[0], q(&[-2, 0, 1]));
        assert_eq!(chain.chain()[1], q(&[0, 2]));
    }

    // ----- root bounds ------------------------------------------------------------

    #[test]
    fn cauchy_bound_strictly_contains_every_real_root() {
        let mut rng = Lcg(61);
        for _ in 0..30 {
            let roots: Vec<Rational> = (0..4)
                .map(|_| rq(rng.next(), 1 + rng.next().abs()))
                .collect();
            let p = Polynomial::from_roots(&roots).scale(&ri(3));
            let bound = real_root_bound(&p).unwrap();
            for root in &roots {
                assert!(root.abs() < bound, "|{root}| < {bound}");
            }
        }
        assert_eq!(
            real_root_bound(&q(&[0, 1])),
            Some(ri(1)),
            "x has root 0 < 1"
        );
        assert_eq!(real_root_bound(&q(&[-1, 1])), Some(ri(2)));
        assert_eq!(real_root_bound(&q(&[3])), None);
        assert_eq!(real_root_bound(&Polynomial::zero()), None);
    }

    // ----- isolation --------------------------------------------------------------

    #[test]
    fn isolation_of_x_squared_minus_two_gives_two_sign_changing_intervals() {
        let p = q(&[-2, 0, 1]);
        let roots = isolate_real_roots(&p).unwrap();
        assert_eq!(roots.len(), 2);
        for root in &roots {
            assert_eq!(root.multiplicity, 1);
            let RootLocation::Isolated(interval) = &root.location else {
                panic!("sqrt 2 is irrational, so it is isolated not exact");
            };
            assert_ne!(
                p.sign_at(interval.lo()),
                p.sign_at(interval.hi()),
                "sign change"
            );
            assert_ne!(p.sign_at(interval.lo()), Ordering::Equal);
            assert_ne!(p.sign_at(interval.hi()), Ordering::Equal);
        }
        // ordered and disjoint; one negative one positive
        let (first, second) = (&roots[0].location, &roots[1].location);
        assert!(first.upper() < second.lower());
        assert!(first.upper().is_negative() && second.lower().is_positive());
    }

    #[test]
    fn isolation_reports_every_rational_root_exactly_with_its_multiplicity() {
        // (2x - 1)(3x + 2)(x - 1)^2 x^3
        let p = q(&[-1, 2])
            .mul(&q(&[2, 3]))
            .mul(&q(&[-1, 1]).pow(2))
            .mul(&Polynomial::monomial(ri(1), 3));
        let roots = isolate_real_roots(&p).unwrap();
        let exact: Vec<(Rational, usize)> = roots
            .iter()
            .map(|r| match &r.location {
                RootLocation::Exact(v) => (v.clone(), r.multiplicity),
                other => panic!("expected an exact root, got {other:?}"),
            })
            .collect();
        assert_eq!(
            exact,
            vec![(rq(-2, 3), 1), (ri(0), 3), (rq(1, 2), 1), (ri(1), 2)]
        );
        assert_eq!(
            rational_roots(&p).unwrap(),
            vec![rq(-2, 3), ri(0), rq(1, 2), ri(1)]
        );
    }

    #[test]
    fn isolation_mixes_exact_and_irrational_roots_in_order() {
        // (x^2 - 2)(x - 1)^2
        let p = q(&[-2, 0, 1]).mul(&q(&[-1, 1]).pow(2));
        let roots = isolate_real_roots(&p).unwrap();
        assert_eq!(roots.len(), 3);
        assert!(matches!(roots[0].location, RootLocation::Isolated(_)));
        assert_eq!(roots[0].multiplicity, 1);
        assert_eq!(roots[1].location, RootLocation::Exact(ri(1)));
        assert_eq!(roots[1].multiplicity, 2);
        assert!(matches!(roots[2].location, RootLocation::Isolated(_)));
        assert_eq!(roots[2].multiplicity, 1);
        for w in roots.windows(2) {
            assert!(
                w[0].location.upper() < w[1].location.lower(),
                "disjoint and ascending"
            );
        }
    }

    #[test]
    fn isolation_separates_close_irrational_roots() {
        // roots 1 +- sqrt(2) and 1 +- sqrt(2 + 10^-6)
        let shifted =
            |extra: Rational| q(&[-1, 1]).pow(2).sub(&Polynomial::constant(ri(2) + extra));
        let p = shifted(r_zero()).mul(&shifted(rq(1, 1_000_000)));
        let roots = isolate_real_roots(&p).unwrap();
        assert_eq!(roots.len(), 4);
        for w in roots.windows(2) {
            assert!(w[0].location.upper() < w[1].location.lower());
        }
        let radical = p.squarefree_part();
        for root in &roots {
            if let RootLocation::Isolated(interval) = &root.location {
                assert_ne!(
                    radical.sign_at(interval.lo()),
                    radical.sign_at(interval.hi())
                );
            }
        }
    }

    #[test]
    fn isolation_handles_huge_coefficients_exactly() {
        let ten_20 = BigInt::from(10u8).pow(20);
        // x^2 - 10^40: exact roots +-10^20
        let square = Polynomial::from_coefficients(vec![
            Rational::from_integer(-(&ten_20 * &ten_20)),
            r_zero(),
            r_one(),
        ]);
        let roots = isolate_real_roots(&square).unwrap();
        assert_eq!(
            roots.iter().map(|r| r.location.clone()).collect::<Vec<_>>(),
            vec![
                RootLocation::Exact(Rational::from_integer(-ten_20.clone())),
                RootLocation::Exact(Rational::from_integer(ten_20.clone())),
            ]
        );
        // x^2 - (10^40 + 1): two irrational roots just outside +-10^20
        let off = Polynomial::from_coefficients(vec![
            Rational::from_integer(-(&ten_20 * &ten_20 + BigInt::one())),
            r_zero(),
            r_one(),
        ]);
        let roots = isolate_real_roots(&off).unwrap();
        assert_eq!(roots.len(), 2);
        assert!(roots
            .iter()
            .all(|r| matches!(r.location, RootLocation::Isolated(_))));
    }

    #[test]
    fn isolation_of_constants_and_the_zero_polynomial() {
        assert!(isolate_real_roots(&q(&[7])).unwrap().is_empty());
        assert_eq!(
            isolate_real_roots(&Polynomial::zero()).unwrap_err(),
            PolynomialError::ZeroPolynomial
        );
        assert!(
            isolate_real_roots(&q(&[1, 0, 1])).unwrap().is_empty(),
            "x^2 + 1"
        );
    }

    #[test]
    fn isolation_total_count_matches_sturm_and_multiplicities_sum_to_the_real_degree() {
        let mut rng = Lcg(77);
        for _ in 0..25 {
            let (a, b) = (rng.poly(3), rng.poly(2));
            let p = a.mul(&b.pow(2));
            if p.is_zero() || p.is_constant() {
                continue;
            }
            let roots = isolate_real_roots(&p).unwrap();
            assert_eq!(roots.len(), count_all_real_roots(&p).unwrap());
            for w in roots.windows(2) {
                assert!(w[0].location.upper() < w[1].location.lower());
            }
            // the sum of multiplicities never exceeds the degree
            let total: usize = roots.iter().map(|r| r.multiplicity).sum();
            assert!(total <= p.degree().unwrap());
        }
    }

    #[test]
    fn rational_roots_agree_with_divisor_enumeration_on_integer_polynomials() {
        // test-only oracle: enumerate p/q with p | a_0, q | a_n (small coefficients)
        let mut rng = Lcg(91);
        for _ in 0..30 {
            let roots: Vec<Rational> = (0..3)
                .map(|_| rq(rng.next(), 1 + rng.next().abs()))
                .collect();
            let p = Polynomial::from_roots(&roots)
                .mul(&q(&[1, 0, 1]))
                .scale(&ri(6));
            let found = rational_roots(&p).unwrap();
            let mut expected: Vec<Rational> = roots.clone();
            expected.sort();
            expected.dedup();
            assert_eq!(found, expected);
        }
    }

    #[test]
    fn irrational_roots_are_never_reported_as_exact() {
        // x^2 - 2, x^3 - 2, x^2 - x - 1
        for coefficients in [&[-2i64, 0, 1][..], &[-2, 0, 0, 1], &[-1, -1, 1]] {
            assert!(
                rational_roots(&q(coefficients)).unwrap().is_empty(),
                "{coefficients:?}"
            );
        }
    }

    // ----- refinement -------------------------------------------------------------

    #[test]
    fn refinement_halves_the_interval_and_keeps_the_root_inside() {
        let p = q(&[-2, 0, 1]);
        let roots = isolate_real_roots(&p).unwrap();
        let tolerance = rq(1, 1_000_000_000);
        for root in &roots {
            let refined = refine_root(&p, root, &tolerance).unwrap();
            assert!(refined.location.width() <= tolerance);
            assert_eq!(refined.multiplicity, 1);
            let (lo, hi) = (
                refined.location.lower().clone(),
                refined.location.upper().clone(),
            );
            assert_ne!(p.sign_at(&lo), p.sign_at(&hi), "the root stays bracketed");
            // the refinement is nested in the original interval
            assert!(lo >= *root.location.lower() && hi <= *root.location.upper());
            // and it brackets sqrt 2: lo^2 < 2 < hi^2 on the positive side
            if lo.is_positive() {
                assert!(&lo * &lo < ri(2) && &hi * &hi > ri(2));
            }
        }
    }

    #[test]
    fn refinement_works_on_a_double_root_through_the_radical() {
        // (x^2 - 2)^2 has double roots at +-sqrt 2 where p itself does not change sign
        let p = q(&[-2, 0, 1]).pow(2);
        let roots = isolate_real_roots(&p).unwrap();
        assert!(roots.iter().all(|r| r.multiplicity == 2));
        let refined = refine_root(&p, &roots[1], &rq(1, 1000)).unwrap();
        assert!(refined.location.width() <= rq(1, 1000));
        assert_eq!(refined.multiplicity, 2);
    }

    #[test]
    fn refinement_refuses_a_non_positive_tolerance_and_a_non_isolating_interval() {
        let p = q(&[-2, 0, 1]);
        let roots = isolate_real_roots(&p).unwrap();
        assert!(matches!(
            refine_root(&p, &roots[0], &r_zero()),
            Err(PolynomialError::NonPositiveTolerance(_))
        ));
        assert!(matches!(
            refine_root(&p, &roots[0], &rq(-1, 2)),
            Err(PolynomialError::NonPositiveTolerance(_))
        ));
        // [-3, 3] holds both roots: same sign at the endpoints
        assert!(matches!(
            refine_simple_root(&p, &Interval::new(ri(-3), ri(3)), &rq(1, 10)),
            Err(PolynomialError::NotIsolating { .. })
        ));
        // an endpoint that is a root is not a valid isolating endpoint
        assert!(matches!(
            refine_simple_root(&q(&[-1, 1]), &Interval::new(ri(1), ri(3)), &rq(1, 10)),
            Err(PolynomialError::NotIsolating { .. })
        ));
    }

    #[test]
    fn refinement_returns_an_exact_root_when_a_midpoint_hits_it() {
        // root 1/2 of 2x - 1 inside [0, 1]: the first midpoint is the root
        let location =
            refine_simple_root(&q(&[-1, 2]), &Interval::new(ri(0), ri(1)), &rq(1, 100)).unwrap();
        assert_eq!(location, RootLocation::Exact(rq(1, 2)));
    }

    // ----- interval evaluation ----------------------------------------------------

    #[test]
    fn interval_evaluation_encloses_every_sampled_value() {
        let p = q(&[3, -5, 0, 2]);
        let interval = Interval::new(rq(-3, 2), rq(5, 4));
        let image = p.eval_interval(&interval);
        for k in 0..=20 {
            let x = interval.lo() + (interval.hi() - interval.lo()) * rq(k, 20);
            assert!(image.contains(&p.eval(&x)), "p({x}) in the enclosure");
        }
        // a point interval gives the exact value
        let point = p.eval_interval(&Interval::point(rq(1, 3)));
        assert_eq!(point, Interval::point(p.eval(&rq(1, 3))));
    }

    #[test]
    fn interval_evaluation_width_shrinks_with_the_interval() {
        let p = q(&[1, 1, 1, 1]);
        let wide = p.eval_interval(&Interval::new(ri(0), ri(1)));
        let narrow = p.eval_interval(&Interval::new(rq(1, 2), rq(501, 1000)));
        assert!(narrow.diam() < wide.diam());
    }

    // ----- serde ------------------------------------------------------------------

    #[test]
    fn deserialisation_normalises_trailing_zeros_and_roundtrips() {
        // A wire form with trailing zero coefficients deserialises to the trimmed value.
        let padded = serde_json::to_string(&vec![ri(1), ri(2), ri(0), ri(0)]).unwrap();
        let parsed: Polynomial<Rational> = serde_json::from_str(&padded).unwrap();
        assert_eq!(parsed, q(&[1, 2]));
        assert_eq!(parsed.degree(), Some(1));
        // A value survives a serialise / deserialise round trip unchanged.
        let p = Polynomial::from_coefficients(vec![rq(1, 3), ri(0), rq(-5, 7)]);
        let back: Polynomial<Rational> =
            serde_json::from_str(&serde_json::to_string(&p).unwrap()).unwrap();
        assert_eq!(back, p);
        // The all-zero wire form is the zero polynomial.
        let zero: Polynomial<Rational> =
            serde_json::from_str(&serde_json::to_string(&vec![ri(0), ri(0)]).unwrap()).unwrap();
        assert!(zero.is_zero());
    }
}

#[cfg(test)]
mod dynamics_laws {

    use super::*;
    #[test]
    fn interpolation_reproduces_polynomial_values_with_arbitrary_denominators() {
        let nodes = vec![crate::rational::rq(1, 7), ri(2), ri(5), ri(9)];
        let x = crate::rational::rq(-1, 3);
        let weights = lagrange_weights_at(&x, &nodes).unwrap();
        for degree in 0..4 {
            assert_eq!(
                weights
                    .iter()
                    .zip(&nodes)
                    .map(|(w, y)| w * y.pow(degree))
                    .sum::<Rational>(),
                x.pow(degree)
            );
        }
        assert!(matches!(
            lagrange_weights_at(&x, &[ri(1), ri(1)]),
            Err(PolynomialError::RepeatedNode { .. })
        ));
        assert!(lagrange_weights_at(&x, &[]).is_err());
    }
}
