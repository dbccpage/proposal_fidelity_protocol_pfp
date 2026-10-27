//! Ordered real places and CM coordinates of finite cyclotomic fields.
//! Arithmetic delegates to the canonical rational polynomial and cyclotomic kernels.
//! The represented conductors are 4, 5, 8, 12 and 24; a real place is explicit.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c9ef399b<T> {
    fn checked_invariant_c9ef399b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c9ef399b<T> for Option<T> {
    #[inline]
    fn checked_invariant_c9ef399b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c9ef399b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c9ef399b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::cyclotomic_field::{min_poly_of_2cos, Cyclotomic, CyclotomicError, CyclotomicNumber};
use crate::polynomial::{
    isolate_real_roots, refine_root, Polynomial, PolynomialError, RootLocation, SturmSequence,
};
use crate::rational::{r_one, r_zero, ri, rq, Rational, Zero};
use num_traits::Signed;
use serde::{Deserialize, Serialize};
use std::ops::{Add, Div, Mul, Neg, Sub};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CyclotomicOrderError {
    #[error(transparent)]
    Polynomial(#[from] PolynomialError),
    #[error(transparent)]
    Cyclotomic(#[from] CyclotomicError),
    #[error("a non-real cyclotomic element has no ordered sign")]
    NotReal,
    #[error("division by zero")]
    DivisionByZero,
    #[error("a nonpositive requested width has no finite refinement")]
    NonpositiveWidth,
    #[error("exact linear algebra refused: {0}")]
    LinearAlgebra(String),
    #[error("the element minimal-polynomial computation exceeds the field-degree budget of 128")]
    ComputationBudget,
    #[error("no independent field relation was found")]
    NoRelation,
}

fn rational_sign(q: &Rational) -> i8 {
    if q.is_positive() {
        1
    } else if q.is_negative() {
        -1
    } else {
        0
    }
}

fn sign_at_root_location(reduced: &Polynomial<Rational>, location: &RootLocation) -> Option<i8> {
    match location {
        RootLocation::Exact(value) => Some(rational_sign(&reduced.eval(value))),
        RootLocation::Isolated(interval) => {
            let bounds = reduced.eval_interval(interval);
            if bounds.lo() > &r_zero() {
                Some(1)
            } else if bounds.hi() < &r_zero() {
                Some(-1)
            } else {
                None
            }
        }
    }
}

/// Sign at zeta_n=exp(2*pi*i/n). The real coordinate t=2*cos(2*pi/n)
/// is the largest root of its minimal polynomial. Interval refinement separates
/// every nonzero reduced polynomial from zero, while reduction detects equality.
pub fn standard_real_sign(number: &CyclotomicNumber) -> Result<i8, CyclotomicOrderError> {
    if !number.is_real() {
        return Err(CyclotomicOrderError::NotReal);
    }
    if let Some(q) = number.as_rational() {
        return Ok(rational_sign(&q));
    }
    let minimal = min_poly_of_2cos(number.conductor())?;
    let reduced = number.real_part_polynomial().rem(&minimal)?;
    if reduced.is_zero() {
        return Ok(0);
    }
    let mut root = isolate_real_roots(&minimal)?
        .pop()
        .checked_invariant_c9ef399b("real cyclotomic minimal polynomial has a real root");
    loop {
        if let Some(sign) = sign_at_root_location(&reduced, &root.location) {
            return Ok(sign);
        }
        let width = root.location.width() / ri(2);
        root = refine_root(&minimal, &root, &width)?;
    }
}
impl<const N: usize> linear_algebra::exact_field::involution::Involution for Cyclotomic<N> {
    fn conjugate(&self) -> Self {
        Cyclotomic::conjugate(self)
    }
}
impl<const N: usize> linear_algebra::exact_field::ordered::HermitianOrdered for Cyclotomic<N> {
    fn fixed_field_sign(&self) -> Option<i8> {
        standard_real_sign(self.as_number()).ok()
    }
}

pub fn conductor_min_poly(conductor: usize) -> Polynomial<Rational> {
    match conductor {
        // n=4: theta_4 = 0, F^+ = Q, min poly is x
        4 => Polynomial::<Rational>::from_i64s(&[0, 1]),
        // n=5: theta_5^2 + theta_5 - 1 = 0
        5 => Polynomial::<Rational>::from_i64s(&[-1, 1, 1]),
        // n=8: theta_8^2 - 2 = 0
        8 => Polynomial::<Rational>::from_i64s(&[-2, 0, 1]),
        // n=12: theta_12^2 - 3 = 0
        12 => Polynomial::<Rational>::from_i64s(&[-3, 0, 1]),
        // n=24: theta_24^4 - 4 theta_24^2 + 1 = 0
        24 => Polynomial::<Rational>::from_i64s(&[1, 0, -4, 0, 1]),
        _ => unreachable!(
            "Conductor {} not in supported set {{4, 5, 8, 12, 24}}",
            conductor
        ),
    }
}

pub fn conductor_initial_interval(conductor: usize) -> (Rational, Rational) {
    match conductor {
        4 => (rq(-1, 2), rq(1, 2)),
        5 => (rq(1, 2), rq(1, 1)),
        8 => (rq(1, 1), rq(2, 1)),
        12 => (rq(1, 1), rq(2, 1)),
        24 => (rq(7, 4), rq(2, 1)),
        _ => unreachable!("Conductor {} not supported", conductor),
    }
}

/// Isolates the positive real root alpha_* of minimal polynomial P_n(x) with rational intervals.
#[derive(Clone, Debug)]
pub struct CyclotomicRealRoot {
    pub conductor: usize,
    pub poly: Polynomial<Rational>,
    pub sturm: SturmSequence,
    pub a: Rational,
    pub b: Rational,
}

impl CyclotomicRealRoot {
    pub fn new(conductor: usize) -> Self {
        let poly = conductor_min_poly(conductor);
        let sturm = SturmSequence::new(&poly).checked_invariant_c9ef399b("nonzero conductor polynomial");
        let (a, b) = conductor_initial_interval(conductor);
        if conductor != 4 {
            let n_roots = sturm.count_in(&a, &b).checked_invariant_c9ef399b("ordered initial interval");
            assert_eq!(
                n_roots, 1,
                "Initial interval ({:?}, {:?}) for conductor {} contains {} roots, expected 1",
                a, b, conductor, n_roots
            );
        }
        Self {
            conductor,
            poly,
            sturm,
            a,
            b,
        }
    }

    /// Bisect the isolating interval (a, b) once to half its width.
    pub fn refine(&mut self) {
        if self.conductor == 4 {
            self.a = r_zero();
            self.b = r_zero();
            return;
        }
        if self.a == self.b {
            return;
        }
        let mid = (&self.a + &self.b) / ri(2);
        if self.poly.eval(&mid).is_zero() {
            self.a = mid.clone();
            self.b = mid;
            return;
        }
        if self
            .sturm
            .count_in(&self.a, &mid)
            .checked_invariant_c9ef399b("midpoint in isolating interval")
            == 1
        {
            self.b = mid;
        } else {
            self.a = mid;
        }
    }

    /// Repeatedly bisect interval until (b - a) <= max_width.
    pub fn refine_to_width(&mut self, max_width: &Rational) -> Result<(), CyclotomicOrderError> {
        if max_width <= &r_zero() {
            return Err(CyclotomicOrderError::NonpositiveWidth);
        }
        while (&self.b - &self.a) > *max_width {
            self.refine();
        }
        Ok(())
    }

    fn interval_sign_if_certified(
        &self,
        rem: &Polynomial<Rational>,
        sturm_rem: &SturmSequence,
    ) -> Option<i8> {
        if self.a == self.b {
            return Some(rational_sign(&rem.eval(&self.a)));
        }
        let s_a = rational_sign(&rem.eval(&self.a));
        let s_b = rational_sign(&rem.eval(&self.b));
        if s_a == 0 || s_a != s_b {
            return None;
        }
        if sturm_rem
            .count_in(&self.a, &self.b)
            .checked_invariant_c9ef399b("ordered isolating interval")
            == 0
        {
            Some(s_a)
        } else {
            None
        }
    }

    /// Determine the exact algebraic sign (-1, 0, 1) of poly(alpha_*) under the embedding.
    pub fn sign_of_poly(&mut self, poly: &Polynomial<Rational>) -> i8 {
        if poly.is_zero() {
            return 0;
        }
        if self.conductor == 4 {
            return rational_sign(&poly.eval(&r_zero()));
        }

        let (_, rem) = poly
            .div_rem(&self.poly)
            .checked_invariant_c9ef399b("nonzero conductor polynomial");
        if rem.is_zero() {
            return 0;
        }

        let sturm_rem = SturmSequence::new(&rem).checked_invariant_c9ef399b("nonzero reduced polynomial");
        loop {
            if let Some(sign) = self.interval_sign_if_certified(&rem, &sturm_rem) {
                return sign;
            }
            self.refine();
        }
    }

    /// Compute exact rational bounds r <= poly(alpha_*) <= s with (s - r) <= epsilon.
    pub fn bound_poly(
        &mut self,
        poly: &Polynomial<Rational>,
        epsilon: &Rational,
    ) -> (Rational, Rational) {
        if poly.is_zero() {
            return (r_zero(), r_zero());
        }
        if self.conductor == 4 {
            let v = poly.eval(&r_zero());
            return (v.clone(), v);
        }

        let (_, rem) = poly
            .div_rem(&self.poly)
            .checked_invariant_c9ef399b("nonzero conductor polynomial");
        if rem.is_zero() {
            return (r_zero(), r_zero());
        }

        let rem_deriv = rem.derivative();
        let max_abs_x = self.a.abs().max(self.b.abs()).max(ri(2));
        let mut lip_bound = r_zero();
        let mut x_pow = r_one();
        for c in rem_deriv.coefficients() {
            lip_bound += c.abs() * &x_pow;
            x_pow *= &max_abs_x;
        }
        if lip_bound.is_zero() {
            let val = rem.eval(&self.a);
            return (val.clone(), val);
        }

        let target_width = epsilon / &lip_bound;
        while (&self.b - &self.a) > target_width {
            self.refine();
        }

        let mid = (&self.a + &self.b) / ri(2);
        let val_mid = rem.eval(&mid);
        let radius = &lip_bound * (&self.b - &self.a) / ri(2);
        (&val_mid - &radius, &val_mid + &radius)
    }
}

// ---------------------------------------------------------------------------
// Section 3: Maximal Real Subfield F^+ = Q(theta_n)
// ---------------------------------------------------------------------------

pub fn f_plus_degree(conductor: usize) -> usize {
    match conductor {
        4 => 1,
        5 | 8 | 12 => 2,
        24 => 4,
        _ => unreachable!("Unsupported conductor {}", conductor),
    }
}

/// Exact element of maximal real subfield F^+ = Q(theta_n) in basis {1, theta, ..., theta^{m-1}}.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FieldElementFPlus {
    pub conductor: usize,
    pub coeffs: Vec<Rational>,
}

impl FieldElementFPlus {
    pub fn new(conductor: usize, coeffs: &[Rational]) -> Self {
        let degree = f_plus_degree(conductor);
        let reduced = Polynomial::from_coefficients(coeffs.to_vec())
            .rem(&conductor_min_poly(conductor))
            .checked_invariant_c9ef399b("nonzero field polynomial");
        let mut values = vec![r_zero(); degree];
        for (i, c) in reduced.coefficients().iter().enumerate() {
            values[i] = c.clone();
        }
        Self {
            conductor,
            coeffs: values,
        }
    }

    pub fn from_i64_slice(conductor: usize, coeffs: &[i64]) -> Self {
        let c_rats: Vec<Rational> = coeffs.iter().map(|&c| ri(c)).collect();
        Self::new(conductor, &c_rats)
    }

    pub fn rational(q: Rational, conductor: usize) -> Self {
        let deg = f_plus_degree(conductor);
        let mut c = vec![r_zero(); deg];
        c[0] = q;
        Self {
            conductor,
            coeffs: c,
        }
    }

    pub fn zero(conductor: usize) -> Self {
        Self::rational(r_zero(), conductor)
    }

    pub fn one(conductor: usize) -> Self {
        Self::rational(r_one(), conductor)
    }

    pub fn theta(conductor: usize) -> Self {
        let deg = f_plus_degree(conductor);
        if deg == 1 {
            return Self::zero(conductor);
        }
        let mut c = vec![r_zero(); deg];
        c[1] = r_one();
        Self {
            conductor,
            coeffs: c,
        }
    }

    pub fn is_zero(&self) -> bool {
        self.coeffs.iter().all(|c| c.is_zero())
    }

    pub fn as_cyclotomic(&self) -> Result<CyclotomicNumber, CyclotomicError> {
        CyclotomicNumber::from_real_polynomial(self.conductor, &self.to_poly())
    }

    pub fn to_poly(&self) -> Polynomial<Rational> {
        Polynomial::<Rational>::from_coefficients(self.coeffs.clone())
    }

    pub fn sign(&self, embedding: &mut CyclotomicRealRoot) -> i8 {
        assert_eq!(embedding.conductor, self.conductor);
        embedding.sign_of_poly(&self.to_poly())
    }

    pub fn interval_bounds(
        &self,
        embedding: &mut CyclotomicRealRoot,
        epsilon: &Rational,
    ) -> (Rational, Rational) {
        assert_eq!(embedding.conductor, self.conductor);
        embedding.bound_poly(&self.to_poly(), epsilon)
    }

    pub fn inverse(&self) -> Self {
        self.try_inverse()
            .checked_invariant_c9ef399b("a field operator requires a nonzero element")
    }

    pub fn try_inverse(&self) -> Result<Self, CyclotomicOrderError> {
        if self.is_zero() {
            return Err(CyclotomicOrderError::DivisionByZero);
        }
        let (gcd, inverse, _) = self.to_poly().xgcd(&conductor_min_poly(self.conductor));
        if !gcd.is_constant() {
            return Err(CyclotomicOrderError::DivisionByZero);
        }
        let reduced = inverse
            .scale(&(r_one() / gcd.coefficient(0)))
            .rem(&conductor_min_poly(self.conductor))?;
        Ok(Self::new(self.conductor, reduced.coefficients()))
    }
}

impl Add for &FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn add(self, other: Self) -> FieldElementFPlus {
        assert_eq!(self.conductor, other.conductor);
        let deg = f_plus_degree(self.conductor);
        let new_c: Vec<Rational> = (0..deg)
            .map(|i| &self.coeffs[i] + &other.coeffs[i])
            .collect();
        FieldElementFPlus {
            conductor: self.conductor,
            coeffs: new_c,
        }
    }
}

impl Add for FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn add(self, other: FieldElementFPlus) -> FieldElementFPlus {
        &self + &other
    }
}

impl Sub for &FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn sub(self, other: Self) -> FieldElementFPlus {
        assert_eq!(self.conductor, other.conductor);
        let deg = f_plus_degree(self.conductor);
        let new_c: Vec<Rational> = (0..deg)
            .map(|i| &self.coeffs[i] - &other.coeffs[i])
            .collect();
        FieldElementFPlus {
            conductor: self.conductor,
            coeffs: new_c,
        }
    }
}

impl Sub for FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn sub(self, other: FieldElementFPlus) -> FieldElementFPlus {
        &self - &other
    }
}

impl Neg for &FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn neg(self) -> FieldElementFPlus {
        let new_c: Vec<Rational> = self.coeffs.iter().map(|c| -c).collect();
        FieldElementFPlus {
            conductor: self.conductor,
            coeffs: new_c,
        }
    }
}

impl Neg for FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn neg(self) -> FieldElementFPlus {
        -(&self)
    }
}

impl Mul for &FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn mul(self, other: Self) -> FieldElementFPlus {
        let product = self
            .as_cyclotomic()
            .and_then(|left| left.mul(&other.as_cyclotomic()?))
            .checked_invariant_c9ef399b("matching supported real cyclotomic fields");
        FieldElementFPlus::new(
            self.conductor,
            product.real_part_polynomial().coefficients(),
        )
    }
}

impl Mul for FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn mul(self, other: FieldElementFPlus) -> FieldElementFPlus {
        &self * &other
    }
}

impl Mul<&Rational> for &FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn mul(self, scalar: &Rational) -> FieldElementFPlus {
        let new_c: Vec<Rational> = self.coeffs.iter().map(|c| c * scalar).collect();
        FieldElementFPlus {
            conductor: self.conductor,
            coeffs: new_c,
        }
    }
}

#[allow(clippy::suspicious_arithmetic_impl)]
impl Div for &FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn div(self, other: Self) -> FieldElementFPlus {
        self * &other.inverse()
    }
}

impl Div for FieldElementFPlus {
    type Output = FieldElementFPlus;
    fn div(self, other: FieldElementFPlus) -> FieldElementFPlus {
        &self / &other
    }
}

// ---------------------------------------------------------------------------
// Section 4: Cyclotomic Field F = Q(zeta_n) = F^+(xi)
// ---------------------------------------------------------------------------

pub fn xi_squared(conductor: usize) -> FieldElementFPlus {
    match conductor {
        4 | 8 | 12 | 24 => FieldElementFPlus::rational(ri(-1), conductor),
        5 => FieldElementFPlus::from_i64_slice(5, &[-3, -1]),
        _ => unreachable!("Conductor {} not supported", conductor),
    }
}

/// Exact element of cyclotomic field F = F^+(xi) represented as x + y * xi, with x, y in F^+.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FieldElementF {
    pub conductor: usize,
    pub real: FieldElementFPlus,
    pub imag: FieldElementFPlus,
}

impl FieldElementF {
    pub fn new(conductor: usize, real: FieldElementFPlus, imag: FieldElementFPlus) -> Self {
        assert_eq!(real.conductor, conductor);
        assert_eq!(imag.conductor, conductor);
        Self {
            conductor,
            real,
            imag,
        }
    }

    pub fn rational(q: Rational, conductor: usize) -> Self {
        Self {
            conductor,
            real: FieldElementFPlus::rational(q, conductor),
            imag: FieldElementFPlus::zero(conductor),
        }
    }

    pub fn zero(conductor: usize) -> Self {
        Self {
            conductor,
            real: FieldElementFPlus::zero(conductor),
            imag: FieldElementFPlus::zero(conductor),
        }
    }

    pub fn one(conductor: usize) -> Self {
        Self {
            conductor,
            real: FieldElementFPlus::one(conductor),
            imag: FieldElementFPlus::zero(conductor),
        }
    }

    pub fn xi(conductor: usize) -> Self {
        Self {
            conductor,
            real: FieldElementFPlus::zero(conductor),
            imag: FieldElementFPlus::one(conductor),
        }
    }

    pub fn from_cyclotomic(number: &CyclotomicNumber) -> Result<Self, CyclotomicError> {
        let conductor = number.conductor();
        let real = number.real_part();
        let xi = if conductor == 5 {
            CyclotomicNumber::zeta(5, 1)?.sub(&CyclotomicNumber::zeta(5, -1)?)?
        } else {
            CyclotomicNumber::zeta(conductor, (conductor / 4) as i64)?
        };
        let imaginary = number.sub(&real)?.checked_div(&xi)?;
        Ok(Self::new(
            conductor,
            FieldElementFPlus::new(conductor, real.real_part_polynomial().coefficients()),
            FieldElementFPlus::new(conductor, imaginary.real_part_polynomial().coefficients()),
        ))
    }

    /// The CM coordinate is i for conductors divisible by four, and
    /// zeta-zeta^{-1} for conductor five. Both presentations map to Q(zeta_n).
    pub fn as_cyclotomic(&self) -> Result<CyclotomicNumber, CyclotomicError> {
        let xi = if self.conductor == 5 {
            CyclotomicNumber::zeta(5, 1)?.sub(&CyclotomicNumber::zeta(5, -1)?)?
        } else {
            CyclotomicNumber::zeta(self.conductor, (self.conductor / 4) as i64)?
        };
        self.real
            .as_cyclotomic()?
            .add(&self.imag.as_cyclotomic()?.mul(&xi)?)
    }

    pub fn is_zero(&self) -> bool {
        self.real.is_zero() && self.imag.is_zero()
    }

    pub fn is_real(&self) -> bool {
        self.imag.is_zero()
    }

    pub fn conjugate(&self) -> Self {
        Self {
            conductor: self.conductor,
            real: self.real.clone(),
            imag: -&self.imag,
        }
    }

    pub fn norm(&self) -> FieldElementFPlus {
        let xi2 = xi_squared(self.conductor);
        let x2 = &self.real * &self.real;
        let y2 = &self.imag * &self.imag;
        let y2_xi2 = &y2 * &xi2;
        &x2 - &y2_xi2
    }

    pub fn inverse(&self) -> Self {
        assert!(!self.is_zero(), "Cannot invert zero FieldElementF");
        let n = self.norm();
        let inv_n = n.inverse();
        let re = &self.real * &inv_n;
        let im = &(-&self.imag) * &inv_n;
        Self {
            conductor: self.conductor,
            real: re,
            imag: im,
        }
    }
}

impl Add for &FieldElementF {
    type Output = FieldElementF;
    fn add(self, other: Self) -> FieldElementF {
        assert_eq!(self.conductor, other.conductor);
        FieldElementF {
            conductor: self.conductor,
            real: &self.real + &other.real,
            imag: &self.imag + &other.imag,
        }
    }
}

impl Add for FieldElementF {
    type Output = FieldElementF;
    fn add(self, other: FieldElementF) -> FieldElementF {
        &self + &other
    }
}

impl Sub for &FieldElementF {
    type Output = FieldElementF;
    fn sub(self, other: Self) -> FieldElementF {
        assert_eq!(self.conductor, other.conductor);
        FieldElementF {
            conductor: self.conductor,
            real: &self.real - &other.real,
            imag: &self.imag - &other.imag,
        }
    }
}

impl Sub for FieldElementF {
    type Output = FieldElementF;
    fn sub(self, other: FieldElementF) -> FieldElementF {
        &self - &other
    }
}

impl Neg for &FieldElementF {
    type Output = FieldElementF;
    fn neg(self) -> FieldElementF {
        FieldElementF {
            conductor: self.conductor,
            real: -&self.real,
            imag: -&self.imag,
        }
    }
}

impl Neg for FieldElementF {
    type Output = FieldElementF;
    fn neg(self) -> FieldElementF {
        -(&self)
    }
}

impl Mul for &FieldElementF {
    type Output = FieldElementF;
    fn mul(self, other: Self) -> FieldElementF {
        let product = self
            .as_cyclotomic()
            .and_then(|left| left.mul(&other.as_cyclotomic()?))
            .checked_invariant_c9ef399b("matching supported CM fields");
        FieldElementF::from_cyclotomic(&product)
            .checked_invariant_c9ef399b("CM coordinates reconstruct a cyclotomic element")
    }
}

impl Mul for FieldElementF {
    type Output = FieldElementF;
    fn mul(self, other: FieldElementF) -> FieldElementF {
        &self * &other
    }
}

impl Mul<&FieldElementFPlus> for &FieldElementF {
    type Output = FieldElementF;
    fn mul(self, other: &FieldElementFPlus) -> FieldElementF {
        assert_eq!(self.conductor, other.conductor);
        FieldElementF {
            conductor: self.conductor,
            real: &self.real * other,
            imag: &self.imag * other,
        }
    }
}

impl Mul<&Rational> for &FieldElementF {
    type Output = FieldElementF;
    fn mul(self, other: &Rational) -> FieldElementF {
        FieldElementF {
            conductor: self.conductor,
            real: &self.real * other,
            imag: &self.imag * other,
        }
    }
}

#[allow(clippy::suspicious_arithmetic_impl)]
impl Div for &FieldElementF {
    type Output = FieldElementF;
    fn div(self, other: Self) -> FieldElementF {
        self * &other.inverse()
    }
}

impl Div for FieldElementF {
    type Output = FieldElementF;
    fn div(self, other: FieldElementF) -> FieldElementF {
        &self / &other
    }
}

// Origin: engine/crates_rs/core_number_theory/src/cyclotomic_ordered.rs
// Claim: urn:core:crates_rs:core-number-theory:cyclotomic-ordered:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_polynomial_euclidean_and_derivative() {
        let p1 = Polynomial::<Rational>::from_i64s(&[-2, 0, 1]);
        let p2 = Polynomial::<Rational>::from_i64s(&[-1, 1]);

        let prod = p1.mul(&p2);
        assert_eq!(prod.coefficients(), vec![ri(2), ri(-2), ri(-1), ri(1)]);

        let d_prod = prod.derivative();
        assert_eq!(d_prod.coefficients(), vec![ri(-2), ri(-2), ri(3)]);

        let (quot, rem) = p1.div_rem(&p2).unwrap();
        assert_eq!(quot.coefficients(), vec![ri(1), ri(1)]);
        assert_eq!(rem.coefficients(), vec![ri(-1)]);
    }

    #[test]
    fn test_sturm_root_isolation_all_conductors() {
        let conductors = [4, 5, 8, 12, 24];
        for &cond in &conductors {
            let mut root_iso = CyclotomicRealRoot::new(cond);
            if cond == 4 {
                assert_eq!(
                    root_iso.sign_of_poly(&Polynomial::<Rational>::from_i64s(&[1])),
                    1
                );
                assert_eq!(
                    root_iso.sign_of_poly(&Polynomial::<Rational>::from_i64s(&[-1])),
                    -1
                );
                continue;
            }

            let n_roots = root_iso.sturm.count_in(&root_iso.a, &root_iso.b).unwrap();
            assert_eq!(n_roots, 1);

            let theta_poly = Polynomial::<Rational>::from_i64s(&[0, 1]);
            assert_eq!(root_iso.sign_of_poly(&theta_poly), 1);

            let neg_poly = Polynomial::<Rational>::from_i64s(&[-10, 1]);
            assert_eq!(root_iso.sign_of_poly(&neg_poly), -1);
        }
    }

    #[test]
    fn test_fplus_arithmetic_and_inversion() {
        for &cond in &[4, 5, 8, 12, 24] {
            let mut emb = CyclotomicRealRoot::new(cond);
            let one = FieldElementFPlus::one(cond);
            let two = FieldElementFPlus::rational(ri(2), cond);

            assert_eq!(&one + &one, two);
            assert_eq!(&two - &one, one);
            assert_eq!(&two * &one, two);

            let inv_two = two.inverse();
            assert_eq!(inv_two, FieldElementFPlus::rational(rq(1, 2), cond));
            assert_eq!(&two * &inv_two, one);

            if cond != 4 {
                let theta = FieldElementFPlus::theta(cond);
                assert_eq!(theta.sign(&mut emb), 1);
                let inv_theta = theta.inverse();
                assert_eq!(&theta * &inv_theta, one);
            }
        }
    }

    #[test]
    fn test_field_f_arithmetic() {
        for &cond in &[4, 5, 8, 12, 24] {
            let z = FieldElementF::new(
                cond,
                FieldElementFPlus::rational(ri(3), cond),
                FieldElementFPlus::rational(ri(4), cond),
            );
            let z_conj = z.conjugate();
            assert_eq!(z_conj.real, z.real);
            assert_eq!(z_conj.imag, -&z.imag);

            let norm_val = z.norm();
            assert!(!norm_val.is_zero());

            let inv_z = z.inverse();
            let prod = &z * &inv_z;
            assert_eq!(prod, FieldElementF::one(cond));
        }
    }
}

/// Minimal polynomial of an exact field element, found as the first dependence
/// among 1,x,...,x^degree. The relation is reduced over Q and made monic;
/// no numerical eigenvalue or root approximation enters the certificate.
pub fn element_minimal_polynomial(
    number: &CyclotomicNumber,
) -> Result<Polynomial<Rational>, CyclotomicOrderError> {
    use linear_algebra::exact_field::{elimination, matrix};
    if number.degree() > 128 {
        return Err(CyclotomicOrderError::ComputationBudget);
    }
    let mut powers = vec![CyclotomicNumber::one(number.conductor())?];
    for degree in 1..=number.degree() {
        powers.push(powers.last().expect("the powers contain one").mul(number)?);
        let rows = (0..number.degree())
            .map(|i| powers.iter().map(|p| p.coefficients()[i].clone()).collect())
            .collect();
        let m = matrix::from_rows(rows)
            .map_err(|e| CyclotomicOrderError::LinearAlgebra(e.to_string()))?;
        let relations = elimination::kernel_basis(&m)
            .map_err(|e| CyclotomicOrderError::LinearAlgebra(e.to_string()))?;
        if let Some(relation) = relations.first() {
            let leading = &relation[degree];
            if leading.is_zero() {
                return Err(CyclotomicOrderError::NoRelation);
            }
            return Ok(Polynomial::from_coefficients(
                relation.iter().map(|c| c / leading).collect(),
            ));
        }
    }
    Err(CyclotomicOrderError::NoRelation)
}

#[cfg(test)]
mod ordered_sign_tests {
    use super::*;

    #[test]
    fn exact_real_signs_and_first_relations_replay_mixed_quadratic_controls() {
        let s2 = CyclotomicNumber::zeta(24, 3)
            .unwrap()
            .add(&CyclotomicNumber::zeta(24, -3).unwrap())
            .unwrap();
        let s3 = CyclotomicNumber::zeta(24, 2)
            .unwrap()
            .add(&CyclotomicNumber::zeta(24, -2).unwrap())
            .unwrap();
        let value = s2.add(&s3).unwrap();
        assert_eq!(standard_real_sign(&value), Ok(1));
        assert_eq!(standard_real_sign(&value.neg()), Ok(-1));
        assert_eq!(standard_real_sign(&value.sub(&value).unwrap()), Ok(0));
        let polynomial = element_minimal_polynomial(&value).unwrap();
        assert_eq!(polynomial, Polynomial::from_i64s(&[1, 0, -10, 0, 1]));
        let mut evaluation = CyclotomicNumber::zero(24).unwrap();
        for coefficient in polynomial.coefficients().iter().rev() {
            evaluation = evaluation
                .mul(&value)
                .unwrap()
                .add(&CyclotomicNumber::from_rational(24, coefficient.clone()).unwrap())
                .unwrap();
        }
        assert!(evaluation.is_zero());
        assert!(matches!(
            standard_real_sign(&CyclotomicNumber::zeta(24, 6).unwrap()),
            Err(CyclotomicOrderError::NotReal)
        ));
        let tiny = Rational::new(1.into(), num_bigint::BigInt::from(10).pow(100));
        let positive = CyclotomicNumber::from_rational(24, tiny).unwrap();
        assert_eq!(standard_real_sign(&positive), Ok(1));
        assert_eq!(standard_real_sign(&positive.neg()), Ok(-1));
    }
}
