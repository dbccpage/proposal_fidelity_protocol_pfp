//! Quadratic number fields `Q(sqrt d)`, exact.
//!
//! Three types, for three jobs:
//!
//! - [`Quadratic<D>`]: `a + b sqrt(D)` with the radicand `D` fixed at compile time. `D`
//!   must be squarefree and not `0` or `1`; any other `D` is a compile error, not a
//!   runtime surprise. It implements the full `linear_algebra::scalars` tower and the
//!   `std::ops` operators, so matrices, polynomials and the exact solvers work over it.
//!   For `D > 0` it carries an exact total order ([`Quadratic::sign`], [`Ord`]) decided by
//!   comparing `a^2` with `D b^2`, never by approximating `sqrt(D)`. `D = -1` is the
//!   Gaussian rationals and `D = -3` the Eisenstein rationals.
//! - [`Surd`]: a one-term real surd `c sqrt(d)` with `d` squarefree and positive, closed
//!   under multiplication and inversion; a sum is a surd only when the radicands agree.
//! - [`QuadraticNumber`]: `a + b sqrt(d)` with the radicand chosen at run time. Operations
//!   return `Result` and refuse to mix two different irrational fields; a rational lifts
//!   into any field. Square roots inside the field are decided exactly.
//!
//! There is no floating point in this module. Every refusal is typed
//! ([`QuadraticError`]); nothing panics on caller data.
//!
//! AuthorityEffect: None.

use std::cmp::Ordering;
use std::fmt;

use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Deserializer, Serialize, Serializer};

use crate::rational::{r_one, r_zero, ri, sqrt_exact, squarefree_part, ArithmeticError, Rational};

/// Refusals of the quadratic-field types.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum QuadraticError {
    #[error("an enclosure needs a strictly positive width")]
    NonPositiveWidth,
    #[error("quadratic enclosure exceeds the 16384-bit input or precision budget")]
    EnclosureBudget,
    #[error("the radicand 0 does not define a quadratic field")]
    ZeroRadicand,
    #[error(
        "the radicand {radicand} is not squarefree: it is {squarefree} * {root}^2 with root > 1"
    )]
    RadicandNotSquarefree {
        radicand: BigInt,
        squarefree: BigInt,
        root: BigInt,
    },
    #[error("a real surd needs a nonnegative radicand, got {0}")]
    NegativeRadicand(Rational),
    #[error(
        "the operands lie in different quadratic fields, Q(sqrt({left})) and Q(sqrt({right}))"
    )]
    RadicandMismatch { left: BigInt, right: BigInt },
    #[error("c1 sqrt({left}) + c2 sqrt({right}) with different radicands is not a single surd")]
    SurdSumNotSingle { left: BigInt, right: BigInt },
    #[error("Q(sqrt({0})) is not a real field, so its elements have no order")]
    NotReal(BigInt),
    #[error("division by zero")]
    DivisionByZero,
    #[error(transparent)]
    Arithmetic(#[from] ArithmeticError),
}

/// Whether `d` is a valid compile-time radicand: squarefree and not `0` or `1`.
///
/// `const` so that [`Quadratic`] can reject a bad radicand at compile time. The test is
/// trial division up to `sqrt(|d|)`, so very large `|d|` (beyond about `10^11`) exceed the
/// compiler's const-evaluation budget and are refused at compile time as well.
pub const fn is_valid_radicand(d: i64) -> bool {
    if d == 0 || d == 1 {
        return false;
    }
    let magnitude = d.unsigned_abs();
    let mut p: u64 = 2;
    while p <= magnitude / p {
        if magnitude % (p * p) == 0 {
            return false;
        }
        p += 1;
    }
    true
}

fn half() -> Rational {
    Rational::new(BigInt::one(), BigInt::from(2))
}

/// Check that `d` is a nonzero squarefree integer (`1` and `-1` included).
fn check_radicand(d: &BigInt) -> Result<(), QuadraticError> {
    if d.is_zero() {
        return Err(QuadraticError::ZeroRadicand);
    }
    let (squarefree, root) = squarefree_part(d)?;
    if !root.is_one() {
        return Err(QuadraticError::RadicandNotSquarefree {
            radicand: d.clone(),
            squarefree,
            root,
        });
    }
    Ok(())
}

/// The sign of `a + b sqrt(d)` for a positive non-square `d`, by comparing `a^2` with
/// `d b^2` when `a` and `b` have opposite signs.
fn real_sign(a: &Rational, b: &Rational, d: &Rational) -> Ordering {
    let zero = r_zero();
    match (a.cmp(&zero), b.cmp(&zero)) {
        (Ordering::Equal, Ordering::Equal) => Ordering::Equal,
        (Ordering::Greater, Ordering::Greater)
        | (Ordering::Greater, Ordering::Equal)
        | (Ordering::Equal, Ordering::Greater) => Ordering::Greater,
        (Ordering::Less, Ordering::Less)
        | (Ordering::Less, Ordering::Equal)
        | (Ordering::Equal, Ordering::Less) => Ordering::Less,
        // a > 0 > b: the sign of a - |b| sqrt(d) is the sign of a^2 - d b^2.
        (Ordering::Greater, Ordering::Less) => (a * a).cmp(&(d * b * b)),
        // a < 0 < b: the sign of b sqrt(d) - |a| is the sign of d b^2 - a^2.
        (Ordering::Less, Ordering::Greater) => (d * b * b).cmp(&(a * a)),
    }
}

// ---------------------------------------------------------------------------
// Quadratic<D>: compile-time radicand
// ---------------------------------------------------------------------------

/// Zero-sized proof that `D` is a valid radicand. It can only be made by
/// [`Radicand::checked`], which fails to compile for an invalid `D`.
#[derive(Clone, Copy, PartialEq, Eq, Hash)]
struct Radicand<const D: i64>;

impl<const D: i64> Radicand<D> {
    const VALID: () = assert!(
        is_valid_radicand(D),
        "Quadratic<D> needs a squarefree radicand D other than 0 and 1"
    );

    const fn checked() -> Self {
        let () = Self::VALID;
        Radicand
    }
}

/// `a + b sqrt(D)` in the quadratic field `Q(sqrt D)`; `D` is squarefree, not `0` or `1`,
/// and is checked at compile time.
///
/// The fields are public for reading and writing values; the struct cannot be built by
/// a literal outside this module, so `Quadratic::new` is the only door and the
/// radicand check cannot be bypassed.
#[derive(Clone, PartialEq, Eq, Hash)]
pub struct Quadratic<const D: i64> {
    /// The rational part.
    pub a: Rational,
    /// The coefficient of `sqrt(D)`.
    pub b: Rational,
    radicand: Radicand<D>,
}

impl<const D: i64> fmt::Debug for Quadratic<D> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}) + ({})*sqrt({})", self.a, self.b, D)
    }
}

impl<const D: i64> fmt::Display for Quadratic<D> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} + {}*sqrt({})", self.a, self.b, D)
    }
}

#[derive(Serialize, Deserialize)]
struct QuadraticWire {
    a: Rational,
    b: Rational,
}

impl<const D: i64> Serialize for Quadratic<D> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        QuadraticWire {
            a: self.a.clone(),
            b: self.b.clone(),
        }
        .serialize(serializer)
    }
}

impl<'de, const D: i64> Deserialize<'de> for Quadratic<D> {
    fn deserialize<De: Deserializer<'de>>(deserializer: De) -> Result<Self, De::Error> {
        let wire = QuadraticWire::deserialize(deserializer)?;
        Ok(Self::new(wire.a, wire.b))
    }
}

impl<const D: i64> Quadratic<D> {
    /// The radicand.
    pub const RADICAND: i64 = D;

    /// `a + b sqrt(D)`.
    pub fn new(a: Rational, b: Rational) -> Self {
        Self {
            a,
            b,
            radicand: Radicand::<D>::checked(),
        }
    }

    /// The rational `a`.
    pub fn from_rational(a: Rational) -> Self {
        Self::new(a, r_zero())
    }

    /// `a + b sqrt(D)` for integers `a`, `b`.
    pub fn from_ints(a: i64, b: i64) -> Self {
        Self::new(ri(a), ri(b))
    }

    pub fn zero() -> Self {
        Self::new(r_zero(), r_zero())
    }

    pub fn one() -> Self {
        Self::new(r_one(), r_zero())
    }

    /// `sqrt(D)` itself.
    pub fn sqrt_d() -> Self {
        Self::new(r_zero(), r_one())
    }

    pub fn is_zero(&self) -> bool {
        self.a.is_zero() && self.b.is_zero()
    }

    /// Whether the element lies in `Q`.
    pub fn is_rational(&self) -> bool {
        self.b.is_zero()
    }

    pub fn add(&self, other: &Self) -> Self {
        Self::new(&self.a + &other.a, &self.b + &other.b)
    }

    pub fn sub(&self, other: &Self) -> Self {
        Self::new(&self.a - &other.a, &self.b - &other.b)
    }

    pub fn neg(&self) -> Self {
        Self::new(-&self.a, -&self.b)
    }

    /// `(a + b sqrt D)(c + d sqrt D) = (ac + D bd) + (ad + bc) sqrt D`.
    pub fn mul(&self, other: &Self) -> Self {
        let d = ri(D);
        Self::new(
            &self.a * &other.a + &d * &self.b * &other.b,
            &self.a * &other.b + &self.b * &other.a,
        )
    }

    /// `c * self` for a rational `c`.
    pub fn scale(&self, c: &Rational) -> Self {
        Self::new(&self.a * c, &self.b * c)
    }

    /// The Galois conjugate `a - b sqrt D`.
    pub fn conjugate(&self) -> Self {
        Self::new(self.a.clone(), -&self.b)
    }

    /// The field norm `a^2 - D b^2 = x * conjugate(x)`.
    pub fn norm(&self) -> Rational {
        &self.a * &self.a - ri(D) * &self.b * &self.b
    }

    /// The field trace `2a = x + conjugate(x)`.
    pub fn trace(&self) -> Rational {
        &self.a + &self.a
    }

    /// `1 / self`, or `None` for zero. Nonzero elements have a nonzero norm because
    /// `D` is not a square.
    pub fn inverse(&self) -> Option<Self> {
        let norm = self.norm();
        if norm.is_zero() {
            return None;
        }
        Some(Self::new(&self.a / &norm, -&self.b / &norm))
    }

    /// `self / other`, or `None` when `other` is zero.
    pub fn checked_div(&self, other: &Self) -> Option<Self> {
        Some(self.mul(&other.inverse()?))
    }

    /// `self^n`.
    pub fn pow(&self, n: u32) -> Self {
        let mut result = Self::one();
        let mut base = self.clone();
        let mut n = n;
        while n > 0 {
            if n & 1 == 1 {
                result = result.mul(&base);
            }
            n >>= 1;
            if n > 0 {
                base = base.mul(&base);
            }
        }
        result
    }

    /// One square root of `self` in this field, if there is one. The root returned has a
    /// positive rational part, or, when that is zero, a positive coefficient of
    /// `sqrt(D)`; its negative is the other root.
    pub fn sqrt(&self) -> Option<Self> {
        let number = self.to_number();
        let root = number.sqrt_in(&BigInt::from(D)).ok()??;
        Self::from_number(&root)
    }

    /// The same number as a [`QuadraticNumber`] in normal form.
    pub fn to_number(&self) -> QuadraticNumber {
        QuadraticNumber::normalised(BigInt::from(D), self.a.clone(), self.b.clone())
    }

    /// The element of this field equal to `n`, or `None` when `n` is irrational with a
    /// different radicand.
    pub fn from_number(n: &QuadraticNumber) -> Option<Self> {
        if n.b.is_zero() {
            Some(Self::from_rational(n.a.clone()))
        } else if n.radicand == BigInt::from(D) {
            Some(Self::new(n.a.clone(), n.b.clone()))
        } else {
            None
        }
    }

    const REAL: () = assert!(
        D > 0,
        "the sign and order of Quadratic<D> need a real quadratic field, D > 0"
    );

    /// The sign of the real number `a + b sqrt(D)` (`D > 0` only), decided exactly by
    /// comparing `a^2` with `D b^2` when `a` and `b` differ in sign.
    pub fn sign(&self) -> Ordering {
        let () = Self::REAL;
        real_sign(&self.a, &self.b, &ri(D))
    }

    pub fn is_positive(&self) -> bool {
        self.sign() == Ordering::Greater
    }

    pub fn is_negative(&self) -> bool {
        self.sign() == Ordering::Less
    }

    pub fn is_nonnegative(&self) -> bool {
        self.sign() != Ordering::Less
    }
}

impl Quadratic<5> {
    /// The golden ratio `(1 + sqrt 5) / 2`, the root of `x^2 = x + 1`.
    pub fn golden_ratio() -> Self {
        Self::new(half(), half())
    }

    /// The conjugate golden ratio `(1 - sqrt 5) / 2`, the other root of `x^2 = x + 1`.
    pub fn golden_ratio_conjugate() -> Self {
        Self::new(half(), -half())
    }
}

impl Quadratic<2> {
    /// The silver ratio `1 + sqrt 2`, the root of `x^2 = 2x + 1`.
    pub fn silver_ratio() -> Self {
        Self::new(r_one(), r_one())
    }
}

impl<const D: i64> Ord for Quadratic<D> {
    /// The order of the real numbers (`D > 0` only; using it for `D < 0` does not compile).
    fn cmp(&self, other: &Self) -> Ordering {
        self.sub(other).sign()
    }
}

impl<const D: i64> PartialOrd for Quadratic<D> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl<const D: i64> std::ops::Add for Quadratic<D> {
    type Output = Quadratic<D>;
    fn add(self, rhs: Quadratic<D>) -> Quadratic<D> {
        Quadratic::add(&self, &rhs)
    }
}
impl<'a, 'b, const D: i64> std::ops::Add<&'b Quadratic<D>> for &'a Quadratic<D> {
    type Output = Quadratic<D>;
    fn add(self, rhs: &'b Quadratic<D>) -> Quadratic<D> {
        Quadratic::add(self, rhs)
    }
}
impl<const D: i64> std::ops::Sub for Quadratic<D> {
    type Output = Quadratic<D>;
    fn sub(self, rhs: Quadratic<D>) -> Quadratic<D> {
        Quadratic::sub(&self, &rhs)
    }
}
impl<'a, 'b, const D: i64> std::ops::Sub<&'b Quadratic<D>> for &'a Quadratic<D> {
    type Output = Quadratic<D>;
    fn sub(self, rhs: &'b Quadratic<D>) -> Quadratic<D> {
        Quadratic::sub(self, rhs)
    }
}
impl<const D: i64> std::ops::Mul for Quadratic<D> {
    type Output = Quadratic<D>;
    fn mul(self, rhs: Quadratic<D>) -> Quadratic<D> {
        Quadratic::mul(&self, &rhs)
    }
}
impl<'a, 'b, const D: i64> std::ops::Mul<&'b Quadratic<D>> for &'a Quadratic<D> {
    type Output = Quadratic<D>;
    fn mul(self, rhs: &'b Quadratic<D>) -> Quadratic<D> {
        Quadratic::mul(self, rhs)
    }
}
impl<const D: i64> std::ops::Neg for Quadratic<D> {
    type Output = Quadratic<D>;
    fn neg(self) -> Quadratic<D> {
        Quadratic::neg(&self)
    }
}
impl<'a, const D: i64> std::ops::Neg for &'a Quadratic<D> {
    type Output = Quadratic<D>;
    fn neg(self) -> Quadratic<D> {
        Quadratic::neg(self)
    }
}

impl<const D: i64> Zero for Quadratic<D> {
    fn zero() -> Self {
        Quadratic::new(r_zero(), r_zero())
    }
    fn is_zero(&self) -> bool {
        self.a.is_zero() && self.b.is_zero()
    }
}

impl<const D: i64> One for Quadratic<D> {
    fn one() -> Self {
        Quadratic::new(r_one(), r_zero())
    }
}

impl<const D: i64> linear_algebra::scalars::Semiring for Quadratic<D> {
    fn zero() -> Self {
        Quadratic::new(r_zero(), r_zero())
    }
    fn one() -> Self {
        Quadratic::new(r_one(), r_zero())
    }
    fn add(&self, rhs: &Self) -> Self {
        Quadratic::add(self, rhs)
    }
    fn mul(&self, rhs: &Self) -> Self {
        Quadratic::mul(self, rhs)
    }
    fn is_zero(&self) -> bool {
        Quadratic::is_zero(self)
    }
}

impl<const D: i64> linear_algebra::scalars::Ring for Quadratic<D> {
    fn neg(&self) -> Self {
        Quadratic::neg(self)
    }
}

impl<const D: i64> linear_algebra::scalars::Field for Quadratic<D> {
    fn try_inv(&self) -> Option<Self> {
        self.inverse()
    }
}

impl<const D: i64> linear_algebra::scalars::ExactRing for Quadratic<D> {}

/// Complex conjugation in the standard embedding. For a real quadratic
/// field this is the identity; it differs from the named Galois conjugate.
impl<const D: i64> linear_algebra::exact_field::involution::Involution for Quadratic<D> {
    fn conjugate(&self) -> Self {
        if D > 0 {
            self.clone()
        } else {
            Quadratic::conjugate(self)
        }
    }
}

impl<const D: i64> linear_algebra::exact_field::ordered::HermitianOrdered for Quadratic<D> {
    fn fixed_field_sign(&self) -> Option<i8> {
        if D > 0 {
            Some(match real_sign(&self.a, &self.b, &ri(D)) {
                Ordering::Less => -1,
                Ordering::Equal => 0,
                Ordering::Greater => 1,
            })
        } else if self.b.is_zero() {
            Some(linear_algebra::exact_field::ordered::OrderedExactField::signum(&self.a))
        } else {
            None
        }
    }
}

// ---------------------------------------------------------------------------
// Surd: one-term c sqrt(d)
// ---------------------------------------------------------------------------

/// The real number `c sqrt(d)` with `c` rational and `d` a positive squarefree integer.
///
/// Normal form: zero is `0 * sqrt(1)`; every other value has a unique pair
/// `(c, d)` with `c != 0` and `d` squarefree, so equality and hashing are mathematical
/// equality, and the order below is the order of the real numbers.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Surd {
    coefficient: Rational,
    radicand: BigInt,
}

impl Surd {
    /// Zero.
    pub fn zero() -> Self {
        Self {
            coefficient: r_zero(),
            radicand: BigInt::one(),
        }
    }

    /// One.
    pub fn one() -> Self {
        Self::rational(r_one())
    }

    /// The rational number `value`, as a surd with radicand `1`.
    pub fn rational(value: Rational) -> Self {
        if value.is_zero() {
            Self::zero()
        } else {
            Self {
                coefficient: value,
                radicand: BigInt::one(),
            }
        }
    }

    /// `coefficient * sqrt(square)`, normalised. A negative `square` is refused whatever
    /// the coefficient; a radicand whose squarefree part cannot be decided within the
    /// trial-division limit is refused with [`QuadraticError::Arithmetic`].
    pub fn new(coefficient: Rational, square: &Rational) -> Result<Self, QuadraticError> {
        let square = square.reduced();
        if square.is_negative() {
            return Err(QuadraticError::NegativeRadicand(square));
        }
        Self::from_fraction(coefficient, square.numer(), square.denom())
    }

    /// `coefficient * sqrt(m)` for a natural number `m`.
    pub fn from_natural(coefficient: Rational, m: &BigInt) -> Result<Self, QuadraticError> {
        if m.is_negative() {
            return Err(QuadraticError::NegativeRadicand(Rational::from_integer(
                m.clone(),
            )));
        }
        Self::from_fraction(coefficient, m, &BigInt::one())
    }

    /// `coefficient * sqrt(p / q)` for `p >= 0`, `q > 0`: `sqrt(p/q) = sqrt(pq) / q`.
    fn from_fraction(
        coefficient: Rational,
        p: &BigInt,
        q: &BigInt,
    ) -> Result<Self, QuadraticError> {
        if coefficient.is_zero() || p.is_zero() {
            return Ok(Self::zero());
        }
        let (radicand, root) = squarefree_part(&(p * q))?;
        Ok(Self {
            coefficient: coefficient * Rational::new(root, q.clone()),
            radicand,
        })
    }

    /// The rational coefficient `c`.
    pub fn coefficient(&self) -> &Rational {
        &self.coefficient
    }

    /// The squarefree positive radicand `d` (`1` for a rational and for zero).
    pub fn radicand(&self) -> &BigInt {
        &self.radicand
    }

    pub fn is_zero(&self) -> bool {
        self.coefficient.is_zero()
    }

    /// Whether the value is a rational number.
    pub fn is_rational(&self) -> bool {
        self.radicand.is_one()
    }

    /// `-self`.
    pub fn neg(&self) -> Self {
        Self {
            coefficient: -&self.coefficient,
            radicand: self.radicand.clone(),
        }
    }

    /// `(c1 sqrt d1)(c2 sqrt d2) = c1 c2 g sqrt((d1/g)(d2/g))` with `g = gcd(d1, d2)`;
    /// `(d1/g)(d2/g)` is squarefree, so the product is again a surd in normal form.
    pub fn mul(&self, other: &Self) -> Self {
        if self.is_zero() || other.is_zero() {
            return Self::zero();
        }
        let g = num_integer::Integer::gcd(&self.radicand, &other.radicand);
        Self {
            coefficient: &self.coefficient * &other.coefficient * Rational::from_integer(g.clone()),
            radicand: (&self.radicand / &g) * (&other.radicand / &g),
        }
    }

    /// `1 / (c sqrt d) = sqrt(d) / (c d)`, or `None` for zero.
    pub fn inverse(&self) -> Option<Self> {
        if self.is_zero() {
            return None;
        }
        Some(Self {
            coefficient: (&self.coefficient * Rational::from_integer(self.radicand.clone()))
                .recip(),
            radicand: self.radicand.clone(),
        })
    }

    /// `self / other`, refusing a zero divisor.
    pub fn checked_div(&self, other: &Self) -> Result<Self, QuadraticError> {
        let inverse = other.inverse().ok_or(QuadraticError::DivisionByZero)?;
        Ok(self.mul(&inverse))
    }

    /// The rational square `c^2 d` of the value.
    pub fn square(&self) -> Rational {
        &self.coefficient * &self.coefficient * Rational::from_integer(self.radicand.clone())
    }

    /// `self + other` when the result is a single surd: either operand zero, or equal
    /// radicands. Otherwise [`QuadraticError::SurdSumNotSingle`].
    pub fn checked_add(&self, other: &Self) -> Result<Self, QuadraticError> {
        if self.is_zero() {
            return Ok(other.clone());
        }
        if other.is_zero() {
            return Ok(self.clone());
        }
        if self.radicand != other.radicand {
            return Err(QuadraticError::SurdSumNotSingle {
                left: self.radicand.clone(),
                right: other.radicand.clone(),
            });
        }
        let sum = &self.coefficient + &other.coefficient;
        if sum.is_zero() {
            return Ok(Self::zero());
        }
        Ok(Self {
            coefficient: sum,
            radicand: self.radicand.clone(),
        })
    }

    /// `self - other` when the result is a single surd.
    pub fn checked_sub(&self, other: &Self) -> Result<Self, QuadraticError> {
        self.checked_add(&other.neg())
    }

    /// The sign of the real number.
    pub fn sign(&self) -> Ordering {
        self.coefficient.cmp(&r_zero())
    }

    /// The same number as a [`QuadraticNumber`].
    pub fn to_number(&self) -> QuadraticNumber {
        QuadraticNumber::normalised(self.radicand.clone(), r_zero(), self.coefficient.clone())
    }
}

impl Ord for Surd {
    /// The order of the real numbers: by sign, then by comparing squares
    /// (reversed for negative values).
    fn cmp(&self, other: &Self) -> Ordering {
        let (left, right) = (self.sign(), other.sign());
        if left != right {
            return left.cmp(&right);
        }
        match left {
            Ordering::Equal => Ordering::Equal,
            Ordering::Greater => self.square().cmp(&other.square()),
            Ordering::Less => other.square().cmp(&self.square()),
        }
    }
}

impl PartialOrd for Surd {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl fmt::Display for Surd {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}*sqrt({})", self.coefficient, self.radicand)
    }
}

// ---------------------------------------------------------------------------
// QuadraticNumber: run-time radicand
// ---------------------------------------------------------------------------

/// `a + b sqrt(d)` with a run-time squarefree radicand `d`.
///
/// Normal form: an element with `b = 0` is a rational and carries radicand `1`; an
/// irrational element carries its squarefree radicand `d != 0, 1` (negative allowed,
/// giving an imaginary field). So equal numbers have equal representations. Operations
/// take the radicand of whichever operand is irrational, treating rationals as members
/// of every field, and return [`QuadraticError::RadicandMismatch`] only when two
/// irrational operands come from different fields.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct QuadraticNumber {
    radicand: BigInt,
    a: Rational,
    b: Rational,
}

impl QuadraticNumber {
    /// The element in normal form, with no validation of the radicand. Internal: every
    /// caller has already checked it.
    fn normalised(radicand: BigInt, a: Rational, b: Rational) -> Self {
        if b.is_zero() || radicand.is_one() {
            // For radicand 1, sqrt(1) = 1 folds the irrational part into the rational.
            let a = if radicand.is_one() { a + b } else { a };
            return Self {
                radicand: BigInt::one(),
                a,
                b: r_zero(),
            };
        }
        Self { radicand, a, b }
    }

    /// `a + b sqrt(radicand)`. The radicand must be a nonzero squarefree integer; `1`
    /// is allowed and means the rational field.
    pub fn new(radicand: BigInt, a: Rational, b: Rational) -> Result<Self, QuadraticError> {
        check_radicand(&radicand)?;
        Ok(Self::normalised(radicand, a, b))
    }

    /// The rational `a`.
    pub fn from_rational(a: Rational) -> Self {
        Self::normalised(BigInt::one(), a, r_zero())
    }

    /// The rational part `a`.
    pub fn rational_part(&self) -> &Rational {
        &self.a
    }

    /// The coefficient `b` of `sqrt(d)` (zero for a rational).
    pub fn sqrt_part(&self) -> &Rational {
        &self.b
    }

    /// Primitive integer minimal polynomial, in ascending degree order.
    /// Rational values have degree one; irrational values have degree two.
    pub fn minimal_polynomial(&self) -> Vec<BigInt> {
        let coefficients = if self.is_rational() {
            vec![-self.a.clone(), r_one()]
        } else {
            vec![self.norm(), -(&self.a + &self.a), r_one()]
        };
        crate::polynomial::Polynomial::from_coefficients(coefficients)
            .content_and_primitive_part()
            .1
            .integer_coefficients()
            .1
    }

    /// A certified real interval of width at most `width`. The integer square
    /// root bounds `sqrt(d)` directly; this does not use floating point.
    pub fn enclosure(
        &self,
        width: &Rational,
    ) -> Result<core_kernel::interval::Interval, QuadraticError> {
        if !width.is_positive() {
            return Err(QuadraticError::NonPositiveWidth);
        }
        if self.is_rational() {
            return Ok(core_kernel::interval::Interval::point(self.a.clone()));
        }
        if self.radicand.is_negative() {
            return Err(QuadraticError::NotReal(self.radicand.clone()));
        }
        if [
            self.a.numer(),
            self.a.denom(),
            self.b.numer(),
            self.b.denom(),
            width.numer(),
            width.denom(),
            &self.radicand,
        ]
        .iter()
        .any(|n| n.bits() > 16384)
        {
            return Err(QuadraticError::EnclosureBudget);
        }
        let scale = (self.b.abs() / width)
            .ceil()
            .to_integer()
            .max(BigInt::one());
        if scale.bits() > 16384 {
            return Err(QuadraticError::EnclosureBudget);
        }
        let k = (&self.radicand * &scale * &scale).sqrt();
        let low = Rational::new(k.clone(), scale.clone());
        let high = Rational::new(k + BigInt::one(), scale);
        let (low, high) = if self.b.is_positive() {
            (low, high)
        } else {
            (high, low)
        };
        Ok(core_kernel::interval::Interval::new(
            &self.a + &self.b * low,
            &self.a + &self.b * high,
        ))
    }

    /// The squarefree radicand of an irrational element; `1` for a rational.
    pub fn radicand(&self) -> &BigInt {
        &self.radicand
    }

    pub fn is_zero(&self) -> bool {
        self.a.is_zero() && self.b.is_zero()
    }

    pub fn is_rational(&self) -> bool {
        self.b.is_zero()
    }

    /// The radicand shared by `self` and `other`: the irrational one's, a rational lifts
    /// into any field, and two different irrational radicands are refused.
    fn common_radicand(&self, other: &Self) -> Result<BigInt, QuadraticError> {
        if self.b.is_zero() {
            Ok(other.radicand.clone())
        } else if other.b.is_zero() || self.radicand == other.radicand {
            Ok(self.radicand.clone())
        } else {
            Err(QuadraticError::RadicandMismatch {
                left: self.radicand.clone(),
                right: other.radicand.clone(),
            })
        }
    }

    pub fn add(&self, other: &Self) -> Result<Self, QuadraticError> {
        let d = self.common_radicand(other)?;
        Ok(Self::normalised(d, &self.a + &other.a, &self.b + &other.b))
    }

    pub fn sub(&self, other: &Self) -> Result<Self, QuadraticError> {
        let d = self.common_radicand(other)?;
        Ok(Self::normalised(d, &self.a - &other.a, &self.b - &other.b))
    }

    pub fn neg(&self) -> Self {
        Self::normalised(self.radicand.clone(), -&self.a, -&self.b)
    }

    /// `(a + b sqrt d)(c + e sqrt d) = (ac + d b e) + (ae + bc) sqrt d`.
    pub fn mul(&self, other: &Self) -> Result<Self, QuadraticError> {
        let d = self.common_radicand(other)?;
        let d_rational = Rational::from_integer(d.clone());
        Ok(Self::normalised(
            d,
            &self.a * &other.a + &d_rational * &self.b * &other.b,
            &self.a * &other.b + &self.b * &other.a,
        ))
    }

    /// The Galois conjugate `a - b sqrt d`.
    pub fn conjugate(&self) -> Self {
        Self::normalised(self.radicand.clone(), self.a.clone(), -&self.b)
    }

    /// The norm `a^2 - d b^2` from the quadratic field down to `Q` (a rational has norm
    /// `a^2`).
    pub fn norm(&self) -> Rational {
        &self.a * &self.a - Rational::from_integer(self.radicand.clone()) * &self.b * &self.b
    }

    /// The trace `2a`.
    pub fn trace(&self) -> Rational {
        &self.a + &self.a
    }

    /// `1 / self`, or `None` for zero.
    pub fn inverse(&self) -> Option<Self> {
        let norm = self.norm();
        if norm.is_zero() {
            return None;
        }
        Some(Self::normalised(
            self.radicand.clone(),
            &self.a / &norm,
            -&self.b / &norm,
        ))
    }

    /// `self / other`; refuses a zero divisor and mixed irrational fields.
    pub fn checked_div(&self, other: &Self) -> Result<Self, QuadraticError> {
        let inverse = other.inverse().ok_or(QuadraticError::DivisionByZero)?;
        self.mul(&inverse)
    }

    /// `self^n`.
    pub fn pow(&self, n: u32) -> Self {
        let mut result = Self::from_rational(r_one());
        let mut base = self.clone();
        let mut n = n;
        while n > 0 {
            if n & 1 == 1 {
                // `result` and `base` share `self`'s field, so the product cannot mismatch.
                result = Self::normalised(
                    self.radicand.clone(),
                    &result.a * &base.a
                        + Rational::from_integer(self.radicand.clone()) * &result.b * &base.b,
                    &result.a * &base.b + &result.b * &base.a,
                );
            }
            n >>= 1;
            if n > 0 {
                base = Self::normalised(
                    self.radicand.clone(),
                    &base.a * &base.a
                        + Rational::from_integer(self.radicand.clone()) * &base.b * &base.b,
                    &base.a * &base.b + &base.b * &base.a,
                );
            }
        }
        result
    }

    /// The sign of the real number. Refuses an irrational element of an imaginary field,
    /// which has no sign ([`QuadraticError::NotReal`]).
    pub fn sign(&self) -> Result<Ordering, QuadraticError> {
        if self.b.is_zero() {
            return Ok(self.a.cmp(&r_zero()));
        }
        if self.radicand.is_negative() {
            return Err(QuadraticError::NotReal(self.radicand.clone()));
        }
        Ok(real_sign(
            &self.a,
            &self.b,
            &Rational::from_integer(self.radicand.clone()),
        ))
    }

    /// Compare two real numbers exactly.
    pub fn cmp_real(&self, other: &Self) -> Result<Ordering, QuadraticError> {
        self.sub(other)?.sign()
    }

    fn rational_sqrt_in_field(&self, field: &BigInt, d: &Rational) -> Option<Self> {
        if let Some(root) = sqrt_exact(&self.a) {
            return Some(Self::from_rational(root));
        }
        if !field.is_one() {
            if let Some(z) = sqrt_exact(&(&self.a / d)) {
                return Some(Self::normalised(field.clone(), r_zero(), z));
            }
        }
        None
    }

    /// A square root of `self` inside the field `Q(sqrt(field))`, decided exactly:
    /// `Ok(None)` means there is none there. `field` must be a nonzero squarefree
    /// integer (`1` for `Q`); an irrational `self` from a different field is refused.
    ///
    /// For `x = a + b sqrt d` with `b != 0` a root `s + v sqrt d` exists iff the norm
    /// `N = a^2 - d b^2` is a rational square `r^2` and one of `(a +- r)/2` is a
    /// nonzero rational square `s^2`; then `v = b / (2 s)`. The returned root has `s > 0`;
    /// its negative is the other root. A rational `a` has the root `sqrt a` when `a` is a
    /// rational square, else `sqrt(a / d) sqrt d` when `a / d` is one.
    pub fn sqrt_in(&self, field: &BigInt) -> Result<Option<Self>, QuadraticError> {
        check_radicand(field)?;
        if !self.b.is_zero() && self.radicand != *field {
            return Err(QuadraticError::RadicandMismatch {
                left: self.radicand.clone(),
                right: field.clone(),
            });
        }
        let d = Rational::from_integer(field.clone());
        if self.b.is_zero() {
            return Ok(self.rational_sqrt_in_field(field, &d));
        }
        let norm = &self.a * &self.a - &d * &self.b * &self.b;
        let Some(r) = sqrt_exact(&norm) else {
            return Ok(None);
        };
        for signed_r in [r.clone(), -r] {
            let half_sum = (&self.a + signed_r) * half();
            if let Some(s) = sqrt_exact(&half_sum) {
                if !s.is_zero() {
                    let v = &self.b / (&s + &s);
                    return Ok(Some(Self::normalised(field.clone(), s, v)));
                }
            }
        }
        Ok(None)
    }

    /// Whether `self` is a square in `Q(sqrt(field))`.
    pub fn is_square_in(&self, field: &BigInt) -> Result<bool, QuadraticError> {
        Ok(self.sqrt_in(field)?.is_some())
    }
}

impl fmt::Display for QuadraticNumber {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.b.is_zero() {
            write!(f, "{}", self.a)
        } else {
            write!(f, "{} + {}*sqrt({})", self.a, self.b, self.radicand)
        }
    }
}

// Origin: engine/crates_rs/core_number_theory/src/quadratic.rs
// Claim: urn:core:crates_rs:core-number-theory:quadratic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cyclotomic::{EisensteinRat, GaussianRat};
    use crate::rational::{integer_sqrt, rq};
    use crate::test_support::{check_field_axioms, Lcg};

    type Q2 = Quadratic<2>;

    #[test]
    fn runtime_quadratics_have_minimal_polynomials_and_certified_bounded_enclosures() {
        let phi = QuadraticNumber::new(BigInt::from(5), rq(1, 2), rq(1, 2)).unwrap();
        assert_eq!(
            phi.minimal_polynomial(),
            vec![(-1).into(), (-1).into(), 1.into()]
        );
        let interval = phi.enclosure(&rq(1, 1_000_000)).unwrap();
        assert!(interval.diam() <= rq(1, 1_000_000));
        let polynomial = |q: &Rational| q * q - q - r_one();
        assert!(polynomial(interval.lo()).is_negative());
        assert!(polynomial(interval.hi()).is_positive());
        let negative = phi.neg().enclosure(&rq(1, 1_000_000)).unwrap();
        assert_eq!(negative.lo(), &-interval.hi());
        assert_eq!(negative.hi(), &-interval.lo());
        assert_eq!(
            QuadraticNumber::from_rational(rq(7, 3)).minimal_polynomial(),
            vec![(-7).into(), 3.into()]
        );
        assert!(matches!(
            phi.enclosure(&r_zero()),
            Err(QuadraticError::NonPositiveWidth)
        ));
        assert!(matches!(
            phi.enclosure(&Rational::new(BigInt::one(), BigInt::one() << 16385usize)),
            Err(QuadraticError::EnclosureBudget)
        ));
        let imaginary = QuadraticNumber::new(BigInt::from(-1), r_zero(), r_one()).unwrap();
        assert!(matches!(
            imaginary.enclosure(&rq(1, 10)),
            Err(QuadraticError::NotReal(_))
        ));
    }
    type Q3 = Quadratic<3>;
    type Q5 = Quadratic<5>;
    type Q7 = Quadratic<7>;

    fn samples<const D: i64>() -> Vec<Quadratic<D>> {
        vec![
            Quadratic::zero(),
            Quadratic::one(),
            Quadratic::sqrt_d(),
            Quadratic::from_ints(3, -4),
            Quadratic::new(rq(1, 2), rq(-2, 3)),
            Quadratic::new(rq(-5, 7), rq(3, 2)),
        ]
    }

    // ----- compile-time radicand --------------------------------------------------

    #[test]
    fn the_radicand_predicate_accepts_exactly_the_squarefree_integers_other_than_0_and_1() {
        let accepted = [
            2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, -1, -2, -3, -5, -6, -7,
        ];
        for d in accepted {
            assert!(is_valid_radicand(d), "{d} is squarefree");
        }
        let refused = [
            0, 1, 4, 8, 9, 12, 16, 18, 20, 24, 25, 27, 28, 32, 36, -4, -8, -9, -12, -16, -18,
        ];
        for d in refused {
            assert!(!is_valid_radicand(d), "{d} is 0, 1 or has a square factor");
        }
        // The const predicate agrees with the runtime squarefree decomposition.
        for d in -300i64..=300 {
            let runtime = d != 0
                && d != 1
                && squarefree_part(&BigInt::from(d))
                    .map(|(_, root)| root == BigInt::one())
                    .unwrap_or(false);
            assert_eq!(is_valid_radicand(d), runtime, "d = {d}");
        }
    }

    // ----- field axioms and ring identities ---------------------------------------

    #[test]
    fn every_quadratic_field_satisfies_the_field_axioms() {
        check_field_axioms(&samples::<2>());
        check_field_axioms(&samples::<3>());
        check_field_axioms(&samples::<5>());
        check_field_axioms(&samples::<7>());
        check_field_axioms(&samples::<-1>());
        check_field_axioms(&samples::<-3>());
        check_field_axioms(&samples::<-7>());
    }

    #[test]
    fn multiplication_reduces_sqrt_d_squared_to_d() {
        assert_eq!(Q2::sqrt_d().mul(&Q2::sqrt_d()), Q2::from_ints(2, 0));
        assert_eq!(Q5::sqrt_d().mul(&Q5::sqrt_d()), Q5::from_ints(5, 0));
        assert_eq!(
            Quadratic::<-1>::sqrt_d().mul(&Quadratic::<-1>::sqrt_d()),
            Quadratic::<-1>::from_ints(-1, 0)
        );
        // (1 + sqrt 3)(2 - sqrt 3) = 2 - sqrt 3 + 2 sqrt 3 - 3 = -1 + sqrt 3
        assert_eq!(
            Q3::from_ints(1, 1).mul(&Q3::from_ints(2, -1)),
            Q3::from_ints(-1, 1)
        );
    }

    #[test]
    fn the_norm_is_multiplicative_and_the_conjugate_is_a_ring_automorphism() {
        let mut rng = Lcg::new(17);
        for _ in 0..60 {
            let x = Q5::new(
                rq(rng.next_signed(9), 1 + rng.next_below(5) as i64),
                rq(rng.next_signed(9), 1 + rng.next_below(5) as i64),
            );
            let y = Q5::new(
                rq(rng.next_signed(9), 1 + rng.next_below(5) as i64),
                rq(rng.next_signed(9), 1 + rng.next_below(5) as i64),
            );
            assert_eq!(x.mul(&y).norm(), x.norm() * y.norm(), "N(xy) = N(x) N(y)");
            assert_eq!(x.mul(&y).conjugate(), x.conjugate().mul(&y.conjugate()));
            assert_eq!(x.add(&y).conjugate(), x.conjugate().add(&y.conjugate()));
            assert_eq!(x.conjugate().conjugate(), x);
            // x * conj(x) = N(x), x + conj(x) = Tr(x)
            assert_eq!(x.mul(&x.conjugate()), Q5::new(x.norm(), r_zero()));
            assert_eq!(x.add(&x.conjugate()), Q5::new(x.trace(), r_zero()));
        }
    }

    #[test]
    fn inverse_divides_exactly_and_zero_has_none() {
        let x = Q7::new(rq(3, 2), rq(-5, 3));
        assert_eq!(x.mul(&x.inverse().unwrap()), Q7::one());
        assert_eq!(Q7::zero().inverse(), None);
        assert_eq!(Q7::one().checked_div(&Q7::zero()), None);
        let y = Q7::from_ints(2, 1);
        assert_eq!(x.checked_div(&y).unwrap().mul(&y), x);
    }

    #[test]
    fn pow_matches_repeated_multiplication() {
        let x = Q3::from_ints(2, 1);
        let mut acc = Q3::one();
        for n in 0..12u32 {
            assert_eq!(x.pow(n), acc, "x^{n}");
            acc = acc.mul(&x);
        }
    }

    #[test]
    fn std_operators_agree_with_the_inherent_methods() {
        let a = Q5::new(rq(1, 3), rq(2, 5));
        let b = Q5::new(rq(-7, 2), rq(1, 9));
        assert_eq!(a.clone() + b.clone(), a.add(&b));
        assert_eq!(&a - &b, a.sub(&b));
        assert_eq!(a.clone() * b.clone(), a.mul(&b));
        assert_eq!(-a.clone(), a.neg());
        assert_eq!(&a * &b, a.mul(&b));
    }

    // ----- golden and silver ratio ------------------------------------------------

    #[test]
    fn the_golden_ratio_satisfies_its_defining_identities() {
        let phi = Q5::golden_ratio();
        let psi = Q5::golden_ratio_conjugate();
        assert_eq!(phi.mul(&phi), phi.add(&Q5::one()), "phi^2 = phi + 1");
        assert_eq!(psi.mul(&psi), psi.add(&Q5::one()), "psi^2 = psi + 1");
        assert_eq!(phi.add(&psi), Q5::one(), "phi + psi = 1");
        assert_eq!(phi.mul(&psi), Q5::from_ints(-1, 0), "phi psi = -1");
        assert_eq!(phi.conjugate(), psi);
        assert_eq!(
            phi.inverse().unwrap(),
            phi.sub(&Q5::one()),
            "1/phi = phi - 1"
        );
        assert_eq!(phi.sub(&psi), Q5::sqrt_d(), "phi - psi = sqrt 5");
        assert_eq!(phi.norm(), ri(-1));
        assert_eq!(phi.trace(), ri(1));
    }

    #[test]
    fn powers_of_phi_carry_the_fibonacci_numbers() {
        // phi^n = F_n phi + F_{n-1}, with F computed by the integer recurrence.
        let phi = Q5::golden_ratio();
        let (mut f_prev, mut f) = (BigInt::from(0), BigInt::from(1));
        for n in 1..=60u32 {
            let expected = Q5::new(Rational::from_integer(f_prev.clone()), r_zero())
                .add(&phi.scale(&Rational::from_integer(f.clone())));
            assert_eq!(phi.pow(n), expected, "phi^{n}");
            let next = &f_prev + &f;
            f_prev = f;
            f = next;
        }
    }

    #[test]
    fn the_silver_ratio_satisfies_its_defining_identities() {
        let delta = Q2::silver_ratio();
        assert_eq!(
            delta.mul(&delta),
            delta.scale(&ri(2)).add(&Q2::one()),
            "delta^2 = 2 delta + 1"
        );
        assert_eq!(
            delta.inverse().unwrap(),
            delta.sub(&Q2::from_ints(2, 0)),
            "1/delta = delta - 2"
        );
        assert_eq!(delta.norm(), ri(-1));
        assert_eq!(delta.conjugate(), Q2::from_ints(1, -1));
    }

    // ----- exact order ------------------------------------------------------------

    /// An independent enclosure of sqrt(d) for the sign cross-check: floor(sqrt(d 10^2k)) / 10^k
    /// and its successor, both exact rationals.
    fn sqrt_enclosure(d: i64, digits: u32) -> (Rational, Rational) {
        let scale = BigInt::from(10u8).pow(digits);
        let root = integer_sqrt(&(BigInt::from(d) * &scale * &scale));
        (
            Rational::new(root.clone(), scale.clone()),
            Rational::new(root + BigInt::one(), scale),
        )
    }

    #[test]
    fn exact_sign_agrees_with_an_independent_rational_enclosure_of_the_root() {
        // Test-only oracle: bracket sqrt(D) with 12 decimal digits and read the sign from
        // a + b [lo, hi]; skip the (here nonexistent) cases whose bracket straddles zero.
        fn check<const D: i64>() {
            let (lo, hi) = sqrt_enclosure(D, 12);
            for a in -12..=12i64 {
                for b in -12..=12i64 {
                    let x = Quadratic::<D>::new(rq(a, 3), rq(b, 2));
                    let (p, q) = (&x.a + &x.b * &lo, &x.a + &x.b * &hi);
                    let expected = if p.is_positive() && q.is_positive() {
                        Ordering::Greater
                    } else if p.is_negative() && q.is_negative() {
                        Ordering::Less
                    } else if a == 0 && b == 0 {
                        Ordering::Equal
                    } else {
                        panic!("bracket straddles zero for {a}/3 + {b}/2 sqrt({D})");
                    };
                    assert_eq!(x.sign(), expected, "sign of {a}/3 + {b}/2 sqrt({D})");
                }
            }
        }
        check::<2>();
        check::<3>();
        check::<5>();
        check::<7>();
        check::<10>();
        check::<11>();
    }

    #[test]
    fn exact_sign_is_correct_where_floating_point_cannot_tell() {
        // Pell solutions x^2 - 2 y^2 = 1 give t = x - y sqrt 2 = 1 / (x + y sqrt 2) > 0, and
        // 1/(2x) < t < 1/(2x - 1). The gap between those bounds is about 1/(4 x^2), which for
        // the later solutions (x near 10^38) is far below any floating-point resolution.
        let (mut x, mut y) = (BigInt::from(3), BigInt::from(2));
        for step in 0..60 {
            let t = Q2::new(
                Rational::from_integer(x.clone()),
                Rational::from_integer(-y.clone()),
            );
            assert!(
                t.is_positive(),
                "step {step}: x - y sqrt 2 > 0 because x^2 - 2y^2 = 1"
            );
            let below = Rational::new(BigInt::one(), BigInt::from(2) * &x);
            let above = Rational::new(BigInt::one(), BigInt::from(2) * &x - BigInt::one());
            assert!(
                t.sub(&Q2::from_rational(below)).is_positive(),
                "step {step}: t > 1/(2x)"
            );
            assert!(
                t.sub(&Q2::from_rational(above)).is_negative(),
                "step {step}: t < 1/(2x - 1)"
            );
            let next_x = BigInt::from(3) * &x + BigInt::from(4) * &y;
            let next_y = BigInt::from(2) * &x + BigInt::from(3) * &y;
            x = next_x;
            y = next_y;
        }
        assert!(
            x > BigInt::from(10u8).pow(40),
            "the loop reached 40-digit solutions"
        );
        // Pell with -1: x^2 - 2 y^2 = -1 gives x - y sqrt 2 < 0 (here 1 - sqrt 2).
        assert!(Q2::from_ints(1, -1).is_negative());
        assert!(Q2::from_ints(7, -5).is_negative(), "49 - 50 = -1");
        assert!(Q2::from_ints(7, -5).neg().is_positive());
    }

    #[test]
    fn the_order_is_total_translation_invariant_and_scale_compatible() {
        let mut rng = Lcg::new(99);
        let make = |rng: &mut Lcg| {
            Q3::new(
                rq(rng.next_signed(8), 1 + rng.next_below(4) as i64),
                rq(rng.next_signed(8), 1 + rng.next_below(4) as i64),
            )
        };
        for _ in 0..80 {
            let (x, y, z) = (make(&mut rng), make(&mut rng), make(&mut rng));
            assert_eq!(x.cmp(&y), y.cmp(&x).reverse(), "antisymmetry");
            assert_eq!(
                x.cmp(&y) == Ordering::Equal,
                x == y,
                "cmp agrees with equality"
            );
            assert_eq!(
                x.add(&z).cmp(&y.add(&z)),
                x.cmp(&y),
                "translation invariance"
            );
            if z.is_positive() {
                assert_eq!(x.mul(&z).cmp(&y.mul(&z)), x.cmp(&y), "positive scaling");
            }
            if x < y && y < z {
                assert!(x < z, "transitivity");
            }
        }
    }

    #[test]
    fn the_order_of_known_real_numbers_is_correct() {
        // sqrt 2 < 3/2 < sqrt 3 < 7/4 < 2 (1.414 < 1.5 < 1.732 < 1.75 < 2)
        assert!(Q2::sqrt_d() < Q2::new(rq(3, 2), r_zero()));
        assert!(Q3::new(rq(3, 2), r_zero()) < Q3::sqrt_d());
        assert!(Q3::sqrt_d() < Q3::new(rq(7, 4), r_zero()));
        // 2cos(2 pi / 5) = (sqrt 5 - 1)/2 is positive, the conjugate is negative.
        let t = Q5::new(rq(-1, 2), rq(1, 2));
        assert!(t.is_positive());
        assert!(t.conjugate().is_negative());
        assert!(Q5::golden_ratio() > Q5::one());
        assert!(Q5::golden_ratio_conjugate() < Q5::zero());
        assert!(Q5::zero().sign() == Ordering::Equal);
        assert!(
            Q5::zero().is_nonnegative() && !Q5::zero().is_positive() && !Q5::zero().is_negative()
        );
    }

    // ----- cross-validation against the other implementations ----------------------

    #[test]
    fn quadratic_minus_one_agrees_with_the_gaussian_rationals() {
        let to_gaussian = |x: &Quadratic<-1>| GaussianRat {
            re: x.a.clone(),
            im: x.b.clone(),
        };
        let mut rng = Lcg::new(5);
        let make = |rng: &mut Lcg| {
            Quadratic::<-1>::new(
                rq(rng.next_signed(6), 1 + rng.next_below(3) as i64),
                rq(rng.next_signed(6), 1 + rng.next_below(3) as i64),
            )
        };
        for _ in 0..50 {
            let (x, y) = (make(&mut rng), make(&mut rng));
            assert_eq!(
                to_gaussian(&x.mul(&y)),
                to_gaussian(&x).mul(&to_gaussian(&y))
            );
            assert_eq!(
                to_gaussian(&x.add(&y)),
                to_gaussian(&x).add(&to_gaussian(&y))
            );
            assert_eq!(to_gaussian(&x.conjugate()), to_gaussian(&x).conj());
            if let Some(inverse) = x.inverse() {
                assert_eq!(to_gaussian(&inverse), to_gaussian(&x).inv());
            }
            assert_eq!(x.norm(), to_gaussian(&x).norm_sq());
        }
    }

    #[test]
    fn quadratic_minus_three_agrees_with_the_eisenstein_rationals() {
        // sqrt(-3) = 2 zeta_3 + 1, so a + b sqrt(-3) = (a + b) + 2b zeta_3.
        let to_eisenstein = |x: &Quadratic<-3>| EisensteinRat {
            a: &x.a + &x.b,
            b: &x.b + &x.b,
        };
        let mut rng = Lcg::new(6);
        let make = |rng: &mut Lcg| {
            Quadratic::<-3>::new(
                rq(rng.next_signed(6), 1 + rng.next_below(3) as i64),
                rq(rng.next_signed(6), 1 + rng.next_below(3) as i64),
            )
        };
        for _ in 0..50 {
            let (x, y) = (make(&mut rng), make(&mut rng));
            assert_eq!(
                to_eisenstein(&x.mul(&y)),
                to_eisenstein(&x).mul(&to_eisenstein(&y))
            );
            assert_eq!(
                to_eisenstein(&x.add(&y)),
                to_eisenstein(&x).add(&to_eisenstein(&y))
            );
            assert_eq!(to_eisenstein(&x.conjugate()), to_eisenstein(&x).conj());
            assert_eq!(x.norm(), to_eisenstein(&x).norm_sq());
        }
    }

    // ----- square roots -----------------------------------------------------------

    #[test]
    fn squares_of_elements_have_a_square_root_that_squares_back() {
        let mut rng = Lcg::new(1234);
        for _ in 0..80 {
            let y = Q5::new(
                rq(rng.next_signed(7), 1 + rng.next_below(4) as i64),
                rq(rng.next_signed(7), 1 + rng.next_below(4) as i64),
            );
            let x = y.mul(&y);
            let root = x.sqrt().expect("the square of an element has a root");
            assert_eq!(root.mul(&root), x);
            assert!(
                root == y || root == y.neg(),
                "the root is one of the two roots"
            );
        }
        let mut rng = Lcg::new(4321);
        for _ in 0..40 {
            let y = Quadratic::<-1>::new(
                rq(rng.next_signed(7), 1 + rng.next_below(4) as i64),
                rq(rng.next_signed(7), 1 + rng.next_below(4) as i64),
            );
            let x = y.mul(&y);
            let root = x
                .sqrt()
                .expect("the square of a Gaussian rational has a root");
            assert_eq!(root.mul(&root), x);
        }
    }

    #[test]
    fn square_root_decisions_on_known_cases() {
        // (1 + sqrt 2)^2 = 3 + 2 sqrt 2
        assert_eq!(Q2::from_ints(3, 2).sqrt(), Some(Q2::from_ints(1, 1)));
        // phi^2 = (3 + sqrt 5)/2
        assert_eq!(Q5::new(rq(3, 2), rq(1, 2)).sqrt(), Some(Q5::golden_ratio()));
        // 2 = (sqrt 2)^2 in Q(sqrt 2); 2 is not a square in Q(sqrt 3) or Q(sqrt 5)
        assert_eq!(Q2::from_ints(2, 0).sqrt(), Some(Q2::sqrt_d()));
        assert_eq!(Q3::from_ints(2, 0).sqrt(), None);
        assert_eq!(Q5::from_ints(2, 0).sqrt(), None);
        // -1 is a square in Q(i) but not in Q(sqrt 5)
        assert_eq!(
            Quadratic::<-1>::from_ints(-1, 0).sqrt(),
            Some(Quadratic::<-1>::sqrt_d())
        );
        assert_eq!(Q5::from_ints(-1, 0).sqrt(), None);
        // 3 + 4i = (2 + i)^2
        assert_eq!(
            Quadratic::<-1>::from_ints(3, 4).sqrt(),
            Some(Quadratic::<-1>::from_ints(2, 1))
        );
        // 0 and 1 and 9/4
        assert_eq!(Q5::zero().sqrt(), Some(Q5::zero()));
        assert_eq!(Q5::one().sqrt(), Some(Q5::one()));
        assert_eq!(
            Q5::new(rq(9, 4), r_zero()).sqrt(),
            Some(Q5::new(rq(3, 2), r_zero()))
        );
        // a non-square with a square norm: 1 + sqrt 2 has norm -1, not a rational square
        assert_eq!(Q2::from_ints(1, 1).sqrt(), None);
        // norm a rational square but neither half-sum a square: 2 + sqrt 3 has norm 1,
        // half-sums (2 +- 1)/2 = 3/2, 1/2, neither a square
        assert_eq!(Q3::from_ints(2, 1).sqrt(), None);
    }

    #[test]
    fn sqrt_returns_the_root_with_positive_rational_part() {
        // (1 - sqrt 2)^2 = (sqrt 2 - 1)^2 = 3 - 2 sqrt 2: the roots are +-(1 - sqrt 2) and
        // the returned one has positive rational part, 1 - sqrt 2.
        let root = Q2::from_ints(3, -2).sqrt().unwrap();
        assert_eq!(root, Q2::from_ints(1, -1));
        assert!(root.a.is_positive());
    }

    // ----- mismatches and serde ---------------------------------------------------

    #[test]
    fn conversion_between_the_typed_and_runtime_forms_round_trips() {
        let x = Q5::new(rq(2, 3), rq(-1, 7));
        let n = x.to_number();
        assert_eq!(n.radicand(), &BigInt::from(5));
        assert_eq!(Q5::from_number(&n), Some(x.clone()));
        // a number from another field is not an element of Q(sqrt 5), a rational is
        let other = QuadraticNumber::new(BigInt::from(3), ri(1), ri(1)).unwrap();
        assert_eq!(Q5::from_number(&other), None);
        let rational = QuadraticNumber::from_rational(rq(3, 4));
        assert_eq!(
            Q5::from_number(&rational),
            Some(Q5::new(rq(3, 4), r_zero()))
        );
        // rationals normalise to radicand 1 whatever field they were built in
        assert_eq!(
            Q5::from_ints(4, 0).to_number(),
            QuadraticNumber::from_rational(ri(4))
        );
    }

    #[test]
    fn wire_round_trip_and_the_typed_form_keeps_its_radicand() {
        let x = Q7::new(rq(1, 3), rq(-5, 2));
        let text = serde_json::to_string(&x).unwrap();
        let back: Q7 = serde_json::from_str(&text).unwrap();
        assert_eq!(back, x);
    }

    // ----- Surd ------------------------------------------------------------------

    fn surd(c: Rational, square: Rational) -> Surd {
        Surd::new(c, &square).unwrap()
    }

    #[test]
    fn surd_normalisation_extracts_square_factors_and_denominators() {
        // sqrt 8 = 2 sqrt 2; sqrt(1/2) = sqrt 2 / 2; sqrt(2/9) = sqrt 2 / 3
        let s = surd(ri(1), ri(8));
        assert_eq!((s.coefficient(), s.radicand()), (&ri(2), &BigInt::from(2)));
        let s = surd(ri(1), rq(1, 2));
        assert_eq!(
            (s.coefficient(), s.radicand()),
            (&rq(1, 2), &BigInt::from(2))
        );
        let s = surd(ri(1), rq(2, 9));
        assert_eq!(
            (s.coefficient(), s.radicand()),
            (&rq(1, 3), &BigInt::from(2))
        );
        // the Gell-Mann diagonal scales sqrt(2 / (l (l + 1)))
        // l = 1: 1; l = 2: sqrt(1/3) = sqrt 3 / 3; l = 3: sqrt 6 / 6; l = 4: sqrt 10 / 10;
        // l = 7: sqrt(1/28) = sqrt 7 / 14 (a square factor 4 in the denominator).
        let scales: Vec<(i64, i64, i64)> = vec![
            (1, 1, 1),
            (2, 3, 3),
            (3, 6, 6),
            (4, 10, 10),
            (5, 15, 15),
            (7, 7, 14),
        ];
        for (l, radicand, denominator) in scales {
            let s = surd(ri(1), rq(2, l * (l + 1)));
            assert_eq!(
                s.radicand(),
                &BigInt::from(radicand),
                "radicand for l = {l}"
            );
            assert_eq!(
                s.coefficient(),
                &rq(1, denominator),
                "coefficient for l = {l}"
            );
        }
    }

    #[test]
    fn surd_zero_has_a_single_normal_form_and_equality_is_mathematical() {
        assert_eq!(surd(ri(0), ri(7)), Surd::zero());
        assert_eq!(surd(ri(5), ri(0)), Surd::zero());
        assert_eq!(surd(ri(1), ri(9)), Surd::rational(ri(3)));
        assert_eq!(surd(ri(2), ri(2)), surd(ri(1), ri(8)), "2 sqrt 2 = sqrt 8");
        assert_eq!(surd(rq(1, 2), ri(8)), surd(ri(1), ri(2)));
        assert!(Surd::zero().is_zero());
        assert!(Surd::rational(ri(3)).is_rational());
        assert!(!surd(ri(1), ri(2)).is_rational());
    }

    #[test]
    fn a_negative_radicand_is_refused_whatever_the_coefficient() {
        assert_eq!(
            Surd::new(ri(0), &ri(-1)),
            Err(QuadraticError::NegativeRadicand(ri(-1)))
        );
        assert_eq!(
            Surd::new(ri(3), &rq(-1, 4)),
            Err(QuadraticError::NegativeRadicand(rq(-1, 4)))
        );
        assert!(matches!(
            Surd::from_natural(ri(1), &BigInt::from(-3)),
            Err(QuadraticError::NegativeRadicand(_))
        ));
        // an unreduced negative radicand is still negative
        assert!(matches!(
            Surd::new(
                ri(1),
                &num_rational::Ratio::new_raw(BigInt::from(2), BigInt::from(-4))
            ),
            Err(QuadraticError::NegativeRadicand(_))
        ));
    }

    #[test]
    fn surds_multiply_and_invert_in_normal_form() {
                                    // 3 sqrt 2 * sqrt 6 = 3 sqrt 12 = 6 sqrt 3
        let a = surd(ri(3), ri(2));
        let b = surd(ri(1), ri(6));
        assert_eq!(a.mul(&b), surd(ri(6), ri(3)));
        // sqrt 2 * sqrt 2 = 2 (rational)
        let r2 = surd(ri(1), ri(2));
        assert_eq!(r2.mul(&r2), Surd::rational(ri(2)));
        assert_eq!(a.square(), ri(18));
        // inverse: 1 / (3 sqrt 2) = sqrt 2 / 6
        assert_eq!(a.inverse().unwrap(), surd(rq(1, 6), ri(2)));
        assert_eq!(a.mul(&a.inverse().unwrap()), Surd::one());
        assert_eq!(Surd::zero().inverse(), None);
        assert_eq!(
            a.checked_div(&Surd::zero()),
            Err(QuadraticError::DivisionByZero)
        );
        assert_eq!(a.mul(&Surd::zero()), Surd::zero());
    }

    #[test]
    fn surd_sums_exist_only_for_equal_radicands_or_zero() {
        let (a, b) = (surd(ri(1), ri(2)), surd(ri(3), ri(2)));
        assert_eq!(a.checked_add(&b).unwrap(), surd(ri(4), ri(2)));
        assert_eq!(a.checked_sub(&a).unwrap(), Surd::zero());
        assert_eq!(a.checked_add(&Surd::zero()).unwrap(), a);
        assert_eq!(Surd::zero().checked_add(&b).unwrap(), b);
        assert_eq!(
            a.checked_add(&surd(ri(1), ri(3))),
            Err(QuadraticError::SurdSumNotSingle {
                left: BigInt::from(2),
                right: BigInt::from(3)
            })
        );
        // a rational plus an irrational is also not a single surd
        assert!(a.checked_add(&Surd::one()).is_err());
    }

    #[test]
    fn surd_order_is_the_order_of_the_real_numbers() {
        let values = [
            surd(ri(-3), ri(2)),
            surd(ri(-1), ri(5)),
            Surd::rational(ri(-2)),
            surd(ri(-1), ri(2)),
            Surd::zero(),
            surd(rq(1, 2), ri(2)),
            surd(ri(1), ri(2)),
            Surd::rational(ri(2)),
            surd(ri(1), ri(5)),
            surd(ri(3), ri(2)),
        ];
        for window in values.windows(2) {
            assert!(window[0] < window[1], "{} < {}", window[0], window[1]);
        }
        for (i, x) in values.iter().enumerate() {
            for (j, y) in values.iter().enumerate() {
                assert_eq!(x.cmp(y), i.cmp(&j));
            }
        }
        assert_eq!(surd(ri(1), ri(2)).sign(), Ordering::Greater);
        assert_eq!(surd(ri(-1), ri(2)).sign(), Ordering::Less);
    }

    #[test]
    fn surd_embeds_into_the_quadratic_number_with_the_same_value() {
        let s = surd(rq(2, 3), ri(5));
        let n = s.to_number();
        assert_eq!(n.radicand(), &BigInt::from(5));
        assert_eq!(n.rational_part(), &r_zero());
        assert_eq!(n.sqrt_part(), &rq(2, 3));
        assert_eq!(
            Surd::rational(ri(4)).to_number(),
            QuadraticNumber::from_rational(ri(4))
        );
    }

    // ----- QuadraticNumber --------------------------------------------------------

    fn number(d: i64, a: Rational, b: Rational) -> QuadraticNumber {
        QuadraticNumber::new(BigInt::from(d), a, b).unwrap()
    }

    #[test]
    fn a_non_squarefree_or_zero_radicand_is_refused() {
        assert_eq!(
            QuadraticNumber::new(BigInt::from(0), ri(1), ri(1)),
            Err(QuadraticError::ZeroRadicand)
        );
        assert_eq!(
            QuadraticNumber::new(BigInt::from(12), ri(1), ri(1)),
            Err(QuadraticError::RadicandNotSquarefree {
                radicand: BigInt::from(12),
                squarefree: BigInt::from(3),
                root: BigInt::from(2)
            })
        );
        assert!(QuadraticNumber::new(BigInt::from(-8), ri(1), ri(1)).is_err());
        assert!(QuadraticNumber::new(BigInt::from(-3), ri(1), ri(1)).is_ok());
        assert!(QuadraticNumber::new(BigInt::from(1), ri(1), ri(1)).is_ok());
    }

    #[test]
    fn rational_elements_have_one_normal_form_whatever_field_they_came_from() {
        assert_eq!(number(5, ri(3), ri(0)), number(2, ri(3), ri(0)));
        assert_eq!(
            number(5, ri(3), ri(0)),
            QuadraticNumber::from_rational(ri(3))
        );
        assert_eq!(number(5, ri(3), ri(0)).radicand(), &BigInt::one());
        // radicand 1: sqrt 1 = 1 folds b into a
        assert_eq!(
            number(1, ri(1), ri(2)),
            QuadraticNumber::from_rational(ri(3))
        );
        // an irrational element keeps its radicand
        assert_eq!(number(5, ri(3), ri(1)).radicand(), &BigInt::from(5));
    }

    #[test]
    fn operations_lift_rationals_and_refuse_to_mix_irrational_fields() {
        let x = number(2, ri(1), ri(1));
        let y = number(3, ri(1), ri(1));
        let r = QuadraticNumber::from_rational(rq(1, 2));
        assert_eq!(x.add(&r).unwrap(), number(2, rq(3, 2), ri(1)));
        assert_eq!(r.mul(&x).unwrap(), number(2, rq(1, 2), rq(1, 2)));
        assert_eq!(r.add(&r).unwrap(), QuadraticNumber::from_rational(ri(1)));
        fn mismatch<T>() -> Result<T, QuadraticError> {
            Err(QuadraticError::RadicandMismatch {
                left: BigInt::from(2),
                right: BigInt::from(3),
            })
        }
        assert_eq!(x.add(&y), mismatch());
        assert_eq!(x.mul(&y), mismatch());
        assert_eq!(x.sub(&y), mismatch());
        assert_eq!(x.checked_div(&y), mismatch());
        assert_eq!(x.cmp_real(&y), mismatch());
        // the difference of a number and itself is the rational zero
        assert_eq!(x.sub(&x).unwrap(), QuadraticNumber::from_rational(ri(0)));
    }

    #[test]
    fn quadratic_number_arithmetic_agrees_with_the_compile_time_type() {
        let mut rng = Lcg::new(77);
        for _ in 0..60 {
            let (a, b, c, d) = (
                rq(rng.next_signed(6), 1 + rng.next_below(3) as i64),
                rq(rng.next_signed(6), 1 + rng.next_below(3) as i64),
                rq(rng.next_signed(6), 1 + rng.next_below(3) as i64),
                rq(rng.next_signed(6), 1 + rng.next_below(3) as i64),
            );
            let (tx, ty) = (Q3::new(a.clone(), b.clone()), Q3::new(c.clone(), d.clone()));
            let (nx, ny) = (number(3, a, b), number(3, c, d));
            assert_eq!(nx.mul(&ny).unwrap(), tx.mul(&ty).to_number());
            assert_eq!(nx.add(&ny).unwrap(), tx.add(&ty).to_number());
            assert_eq!(nx.sub(&ny).unwrap(), tx.sub(&ty).to_number());
            assert_eq!(nx.conjugate(), tx.conjugate().to_number());
            assert_eq!(nx.norm(), tx.norm());
            assert_eq!(nx.trace(), tx.trace());
            assert_eq!(nx.inverse(), tx.inverse().map(|t| t.to_number()));
            assert_eq!(nx.sign().unwrap(), tx.sign());
            assert_eq!(nx.pow(5), tx.pow(5).to_number());
        }
    }

    #[test]
    fn signs_of_quadratic_numbers_are_exact_and_imaginary_fields_refuse() {
        assert_eq!(number(2, ri(-1), ri(1)).sign().unwrap(), Ordering::Greater);
        assert_eq!(number(2, ri(-3), ri(2)).sign().unwrap(), Ordering::Less);
        assert_eq!(
            QuadraticNumber::from_rational(ri(-3)).sign().unwrap(),
            Ordering::Less
        );
        assert_eq!(
            number(-1, ri(0), ri(1)).sign(),
            Err(QuadraticError::NotReal(BigInt::from(-1)))
        );
        // a rational is comparable even when built in an imaginary field
        assert_eq!(number(-3, ri(2), ri(0)).sign().unwrap(), Ordering::Greater);
        assert_eq!(
            number(2, ri(3), ri(0))
                .cmp_real(&number(2, ri(0), ri(2)))
                .unwrap(),
            Ordering::Greater,
            "3 > 2 sqrt 2 = 2.83"
        );
    }

    #[test]
    fn sqrt_in_decides_squares_inside_a_named_field() {
        let field = BigInt::from(5);
        // phi^2 = (3 + sqrt 5)/2 has the root (1 + sqrt 5)/2
        let phi_squared = number(5, rq(3, 2), rq(1, 2));
        let root = phi_squared.sqrt_in(&field).unwrap().unwrap();
        assert_eq!(root, number(5, rq(1, 2), rq(1, 2)));
        assert_eq!(root.mul(&root).unwrap(), phi_squared);
        // 5 is the square of sqrt 5 inside Q(sqrt 5), and is not a rational square
        let five = QuadraticNumber::from_rational(ri(5));
        assert_eq!(five.sqrt_in(&field).unwrap(), Some(number(5, ri(0), ri(1))));
        assert_eq!(five.sqrt_in(&BigInt::one()).unwrap(), None);
        // a rational square root needs no irrational part
        let four = QuadraticNumber::from_rational(ri(4));
        assert_eq!(
            four.sqrt_in(&field).unwrap(),
            Some(QuadraticNumber::from_rational(ri(2)))
        );
        // 2 is not a square in Q(sqrt 5)
        assert_eq!(
            QuadraticNumber::from_rational(ri(2))
                .sqrt_in(&field)
                .unwrap(),
            None
        );
        assert!(phi_squared.is_square_in(&field).unwrap());
        assert!(!QuadraticNumber::from_rational(ri(2))
            .is_square_in(&field)
            .unwrap());
    }

    #[test]
    fn sqrt_in_refuses_a_foreign_field_and_an_invalid_field() {
        let x = number(2, ri(1), ri(1));
        assert_eq!(
            x.sqrt_in(&BigInt::from(3)),
            Err(QuadraticError::RadicandMismatch {
                left: BigInt::from(2),
                right: BigInt::from(3)
            })
        );
        assert_eq!(
            x.sqrt_in(&BigInt::from(0)),
            Err(QuadraticError::ZeroRadicand)
        );
        assert!(matches!(
            x.sqrt_in(&BigInt::from(8)),
            Err(QuadraticError::RadicandNotSquarefree { .. })
        ));
        // an irrational element asked about Q itself is a field mismatch
        assert!(x.sqrt_in(&BigInt::one()).is_err());
    }

    #[test]
    fn the_square_root_decision_is_sound_and_complete_on_a_grid() {
        // Complete: every square has a root. Sound: whatever root is returned squares back.
        let field = BigInt::from(6);
        let mut roots_found = 0;
        for a in -8..=8i64 {
            for b in -8..=8i64 {
                let x = number(6, rq(a, 2), rq(b, 3));
                let square = x.mul(&x).unwrap();
                let root = square
                    .sqrt_in(&field)
                    .unwrap()
                    .expect("a square has a root");
                assert_eq!(root.mul(&root).unwrap(), square);
                roots_found += 1;
                // a generic element is usually not a square; when a root is returned it is right
                if let Some(root) = x.sqrt_in(&field).unwrap() {
                    assert_eq!(root.mul(&root).unwrap(), x);
                }
            }
        }
        assert_eq!(roots_found, 17 * 17);
    }

    #[test]
    fn display_forms_are_readable() {
        assert_eq!(format!("{}", number(2, rq(1, 2), ri(3))), "1/2 + 3*sqrt(2)");
        assert_eq!(format!("{}", QuadraticNumber::from_rational(ri(7))), "7");
        assert_eq!(format!("{}", surd(ri(2), ri(3))), "2*sqrt(3)");
        assert_eq!(format!("{}", Q5::from_ints(1, 2)), "1 + 2*sqrt(5)");
    }
}
