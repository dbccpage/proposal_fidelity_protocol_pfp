//! Exact rational arithmetic and univariate polynomials, dependency-free.
//!
//! The crate has no rational type because the sealed derivation never
//! needed one; PO-000's exact rail is built on `fractions.Fraction`, so the
//! replication needs one.  It is written here rather than pulled from a
//! registry so that every number in the receipt is computed by code in this
//! folder.
//!
//! `Rational` is a reduced fraction of `i128`s.  Every operation is checked:
//! an overflow is a panic (in release builds too), never a wrapped and wrong
//! answer.  That is the declared bound of this arithmetic: exact within
//! `i128`, refused beyond it.
//!
//! `Poly` is a polynomial in one symbol with rational coefficients.  It
//! carries the exponential `q = e^{-t}` of Prop 3.B as a symbol whose
//! identities are polynomial in `q` (`projection_factor.rs`); the chart
//! computation of §3 uses the bivariate `Poly2` in `retraction_geometry.rs`.

use std::cmp::Ordering;
use std::fmt;
use std::ops::{Add, Div, Mul, Neg, Sub};

/// A reduced fraction.  Denominator always positive.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Rational {
    num: i128,
    den: i128,
}

fn gcd(mut a: i128, mut b: i128) -> i128 {
    a = a.checked_abs().expect("i128 overflow");
    b = b.checked_abs().expect("i128 overflow");
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

impl Rational {
    /// Zero.
    pub const ZERO: Rational = Rational { num: 0, den: 1 };
    /// One.
    pub const ONE: Rational = Rational { num: 1, den: 1 };

    /// `num / den`, reduced.  Panics on a zero denominator.
    pub fn new(num: i128, den: i128) -> Rational {
        assert!(den != 0, "rational with zero denominator");
        let g = gcd(num, den);
        let (mut n, mut d) = if g == 0 { (0, 1) } else { (num / g, den / g) };
        if d < 0 {
            n = n.checked_neg().expect("i128 overflow");
            d = d.checked_neg().expect("i128 overflow");
        }
        Rational { num: n, den: d }
    }

    /// An integer.
    pub const fn int(n: i128) -> Rational {
        Rational { num: n, den: 1 }
    }

    /// Numerator.
    pub fn numerator(self) -> i128 {
        self.num
    }

    /// Denominator (positive).
    pub fn denominator(self) -> i128 {
        self.den
    }

    /// Absolute value.
    pub fn abs(self) -> Rational {
        Rational { num: self.num.checked_abs().expect("i128 overflow"), den: self.den }
    }

    /// Sign as −1, 0, 1.
    pub fn signum(self) -> i128 {
        self.num.signum()
    }

    /// Is zero.
    pub fn is_zero(self) -> bool {
        self.num == 0
    }

    /// Is strictly positive.
    pub fn is_positive(self) -> bool {
        self.num > 0
    }

    /// Multiplicative inverse.  Panics at zero.
    pub fn recip(self) -> Rational {
        Rational::new(self.den, self.num)
    }

    /// Non-negative integer power.
    pub fn pow(self, k: u32) -> Rational {
        let mut out = Rational::ONE;
        for _ in 0..k {
            out = out * self;
        }
        out
    }

    /// The larger of two.
    pub fn max(self, other: Rational) -> Rational {
        if self >= other {
            self
        } else {
            other
        }
    }

    /// The smaller of two.
    pub fn min(self, other: Rational) -> Rational {
        if self <= other {
            self
        } else {
            other
        }
    }

    /// Exact square root, if the rational is a perfect square; `None`
    /// otherwise.
    pub fn exact_sqrt(self) -> Option<Rational> {
        if self.num < 0 {
            return None;
        }
        let n = isqrt(self.num);
        let d = isqrt(self.den);
        if n * n == self.num && d * d == self.den {
            Some(Rational::new(n, d))
        } else {
            None
        }
    }

    /// Sum of an iterator.
    pub fn sum<'a>(items: impl IntoIterator<Item = &'a Rational>) -> Rational {
        items.into_iter().fold(Rational::ZERO, |a, b| a + *b)
    }

    /// As an `f64`, for the numerical rail's receipts only.
    pub fn to_f64(self) -> f64 {
        self.num as f64 / self.den as f64
    }
}

fn isqrt(n: i128) -> i128 {
    if n <= 0 {
        return 0;
    }
    if n < 4 {
        return 1;
    }
    let shift = (128 - n.leading_zeros()).div_ceil(2);
    let mut x0 = 1i128 << shift;
    loop {
        let x1 = (x0 + n / x0) / 2;
        if x1 >= x0 {
            break;
        }
        x0 = x1;
    }
    while x0 * x0 > n {
        x0 -= 1;
    }
    while (x0 + 1).checked_mul(x0 + 1).is_some_and(|sq| sq <= n) {
        x0 += 1;
    }
    x0
}

impl From<i128> for Rational {
    fn from(n: i128) -> Rational {
        Rational::int(n)
    }
}

impl From<i32> for Rational {
    fn from(n: i32) -> Rational {
        Rational::int(n as i128)
    }
}

impl Add for Rational {
    type Output = Rational;
    fn add(self, o: Rational) -> Rational {
        let n = self
            .num
            .checked_mul(o.den)
            .and_then(|a| o.num.checked_mul(self.den).and_then(|b| a.checked_add(b)))
            .expect("i128 overflow");
        let d = self.den.checked_mul(o.den).expect("i128 overflow");
        Rational::new(n, d)
    }
}

impl Sub for Rational {
    type Output = Rational;
    fn sub(self, o: Rational) -> Rational {
        self + (-o)
    }
}

impl Neg for Rational {
    type Output = Rational;
    fn neg(self) -> Rational {
        Rational { num: self.num.checked_neg().expect("i128 overflow"), den: self.den }
    }
}

impl Mul for Rational {
    type Output = Rational;
    fn mul(self, o: Rational) -> Rational {
        let n = self.num.checked_mul(o.num).expect("i128 overflow");
        let d = self.den.checked_mul(o.den).expect("i128 overflow");
        Rational::new(n, d)
    }
}

impl Div for Rational {
    type Output = Rational;
    fn div(self, o: Rational) -> Rational {
        let n = self.num.checked_mul(o.den).expect("i128 overflow");
        let d = self.den.checked_mul(o.num).expect("i128 overflow");
        Rational::new(n, d)
    }
}

impl PartialOrd for Rational {
    fn partial_cmp(&self, o: &Rational) -> Option<Ordering> {
        Some(self.cmp(o))
    }
}

impl Ord for Rational {
    fn cmp(&self, o: &Rational) -> Ordering {
        let l = self.num.checked_mul(o.den).expect("i128 overflow");
        let r = o.num.checked_mul(self.den).expect("i128 overflow");
        l.cmp(&r)
    }
}

impl fmt::Display for Rational {
    /// `Fraction`'s text: `3`, `-1`, `1/64`, `3/256`.  This is what the
    /// evidence JSON records, so the receipt compares byte for byte.
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.den == 1 {
            write!(f, "{}", self.num)
        } else {
            write!(f, "{}/{}", self.num, self.den)
        }
    }
}

/// Shorthand: `r(3, 4)` is `3/4`.
pub fn r(num: i128, den: i128) -> Rational {
    Rational::new(num, den)
}

/// Shorthand: `q(5)` is the integer `5`.
pub fn q(n: i128) -> Rational {
    Rational::int(n)
}

/// A polynomial in one symbol with rational coefficients, lowest degree
/// first, trailing zeros trimmed.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Poly {
    /// Coefficients `c[0] + c[1] x + c[2] x² + …`.
    pub coeffs: Vec<Rational>,
    /// The symbol's name, for display.
    pub symbol: &'static str,
}

impl Poly {
    /// A constant.
    pub fn constant(c: Rational, symbol: &'static str) -> Poly {
        Poly { coeffs: vec![c], symbol }.trimmed()
    }

    /// The symbol itself.
    pub fn symbol(symbol: &'static str) -> Poly {
        Poly { coeffs: vec![Rational::ZERO, Rational::ONE], symbol }
    }

    fn trimmed(mut self) -> Poly {
        while self.coeffs.len() > 1 && self.coeffs.last() == Some(&Rational::ZERO) {
            self.coeffs.pop();
        }
        if self.coeffs.is_empty() {
            self.coeffs.push(Rational::ZERO);
        }
        self
    }

    /// Degree (0 for constants, including zero).
    pub fn degree(&self) -> usize {
        self.coeffs.len() - 1
    }

    /// Is the zero polynomial.
    pub fn is_zero(&self) -> bool {
        self.coeffs.iter().all(|c| c.is_zero())
    }

    /// Formal derivative.
    pub fn derivative(&self) -> Poly {
        if self.coeffs.len() <= 1 {
            return Poly::constant(Rational::ZERO, self.symbol);
        }
        let coeffs = self.coeffs.iter().enumerate().skip(1).map(|(k, c)| *c * q(k as i128)).collect();
        Poly { coeffs, symbol: self.symbol }.trimmed()
    }

    /// Evaluate at a rational.
    pub fn eval(&self, x: Rational) -> Rational {
        self.coeffs.iter().rev().fold(Rational::ZERO, |acc, c| acc * x + *c)
    }

    /// Sum.
    pub fn add(&self, o: &Poly) -> Poly {
        let n = self.coeffs.len().max(o.coeffs.len());
        let coeffs = (0..n)
            .map(|k| {
                self.coeffs.get(k).copied().unwrap_or(Rational::ZERO) + o.coeffs.get(k).copied().unwrap_or(Rational::ZERO)
            })
            .collect();
        Poly { coeffs, symbol: self.symbol }.trimmed()
    }

    /// Difference.
    pub fn sub(&self, o: &Poly) -> Poly {
        self.add(&o.scale(-Rational::ONE))
    }

    /// Product.
    pub fn mul(&self, o: &Poly) -> Poly {
        let mut coeffs = vec![Rational::ZERO; self.coeffs.len() + o.coeffs.len() - 1];
        for (i, a) in self.coeffs.iter().enumerate() {
            for (j, b) in o.coeffs.iter().enumerate() {
                coeffs[i + j] = coeffs[i + j] + *a * *b;
            }
        }
        Poly { coeffs, symbol: self.symbol }.trimmed()
    }

    /// Scalar multiple.
    pub fn scale(&self, c: Rational) -> Poly {
        Poly { coeffs: self.coeffs.iter().map(|a| *a * c).collect(), symbol: self.symbol }.trimmed()
    }
}

impl fmt::Display for Poly {
    /// The Python engine's text: `x**2`, `2*x`, `0`, `1 - q`.
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_zero() {
            return write!(f, "0");
        }
        let mut parts: Vec<String> = Vec::new();
        for (k, c) in self.coeffs.iter().enumerate() {
            if c.is_zero() {
                continue;
            }
            let mono = match k {
                0 => String::new(),
                1 => self.symbol.to_string(),
                _ => format!("{}**{}", self.symbol, k),
            };
            let term = if mono.is_empty() {
                c.to_string()
            } else if *c == Rational::ONE {
                mono
            } else if *c == -Rational::ONE {
                format!("-{mono}")
            } else {
                format!("{c}*{mono}")
            };
            parts.push(term);
        }
        let mut out = String::new();
        for (i, p) in parts.iter().enumerate() {
            if i == 0 {
                out.push_str(p);
            } else if let Some(rest) = p.strip_prefix('-') {
                out.push_str(" - ");
                out.push_str(rest);
            } else {
                out.push_str(" + ");
                out.push_str(p);
            }
        }
        write!(f, "{out}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fractions_reduce_and_print_like_python() {
        assert_eq!(r(2, 4), r(1, 2));
        assert_eq!(r(3, -9), r(-1, 3));
        assert_eq!(r(1, 64).to_string(), "1/64");
        assert_eq!(q(-3).to_string(), "-3");
        assert_eq!((r(1, 2) + r(1, 3)).to_string(), "5/6");
        assert_eq!((r(3, 4) * r(4, 3)), Rational::ONE);
        assert!(r(1, 3) < r(1, 2));
        assert_eq!(r(-7, 2).abs(), r(7, 2));
        assert_eq!(q(48).recip(), r(1, 48));
    }

    #[test]
    fn square_roots_are_exact_or_refused() {
        assert_eq!(q(4).exact_sqrt(), Some(q(2)));
        assert_eq!(r(9, 16).exact_sqrt(), Some(r(3, 4)));
        assert_eq!(q(2).exact_sqrt(), None);
        assert_eq!(q(-1).exact_sqrt(), None);
    }

    #[test]
    #[should_panic(expected = "i128 overflow")]
    fn overflow_panics_rather_than_wrapping() {
        let big = Rational::int(i128::MAX);
        let _ = big * q(2);
    }

    #[test]
    fn polynomials_differentiate_and_print() {
        let x = Poly::symbol("x");
        let x2 = x.mul(&x);
        assert_eq!(x2.to_string(), "x**2");
        assert_eq!(x2.derivative().to_string(), "2*x");
        assert_eq!(x2.derivative().derivative().to_string(), "2");
        assert_eq!(Poly::constant(Rational::ZERO, "x").derivative().to_string(), "0");
        assert_eq!(x2.eval(r(1, 2)), r(1, 4));
        let one_minus_q = Poly::constant(Rational::ONE, "q").sub(&Poly::symbol("q"));
        assert_eq!(one_minus_q.to_string(), "1 - q");
    }
}
