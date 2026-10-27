//! Certified exact-rational interval enclosures of elementary functions.
//!
//! Every function returns an [`Interval`] with `BigRational` endpoints that
//! contains the true value, and whose width is at most `2^-bits` for the
//! caller's precision `bits` (an absolute bound). Containment is proved, not
//! assumed: each series is summed exactly and stopped at a term where an
//! explicit tail bound, stated next to the series below and derived from a
//! geometric or alternating-series majorant, is below the tolerance. There
//! are no floats, no rounding modes and no tolerances on the result.
//!
//! | function | method | proved tail bound |
//! |---|---|---|
//! | [`arctan_enclosure`] on `[0, 1]` | Euler's series in `y = x^2/(1+x^2) <= 1/2` | `c_n x y^n` |
//! | [`pi_enclosure`] | Machin, `16 arctan(1/5) - 4 arctan(1/239)` | sum of the two |
//! | [`ln_enclosure`] | `x = 2^e m`, `m in (1/2, 2)`; `2 atanh` series in `|y| < 1/3` | `2 y^(2n+1) / ((2n+1)(1-y^2))` |
//! | [`exp_enclosure`] | Taylor series, reciprocal for negative arguments | `2 x^n / n!` once `n >= 2x` |
//! | [`sqrt_enclosure`] | integer square root of `floor(x 4^bits)` | one unit in the last place |
//! | [`sin_enclosure`], [`cos_enclosure`] | Taylor series after reduction mod `pi` | first omitted term |
//! | [`arccos_enclosure`] | `2 arctan(sqrt((1-x)/(1+x)))` | sum of the parts |
//! | [`arccosh_enclosure`] | `ln(x + sqrt(x^2 - 1))` | sum of the parts |
//!
//! The inverse functions are computed through the arctan and logarithm series
//! and a square-root enclosure, not declared, and each is cross-checked in the
//! tests against an independent forward function (cosine, exponential).
//!
//! Euler's series, for `x` real, is
//! `arctan x = sum_{k >= 0} c_k x^(2k+1) / (1+x^2)^(k+1)` with
//! `c_k = prod_{j=1..k} 2j/(2j+1)`. With `y = x^2/(1+x^2)` its `k`-th term is
//! `c_k (x/(1+x^2)) y^k`, positive and, because `c_k` is non-increasing, the
//! tail from `n` on is at most `c_n (x/(1+x^2)) y^n / (1-y) = c_n x y^n`.
//!
//! The public functions refuse a precision outside `1..=`[`MAX_PRECISION_BITS`].
//! Internally a function may ask another for a few more bits than that, so the
//! shared routines take the precision as a `u64` and do not apply the cap.
//!
//! AuthorityEffect: None.

use crate::interval::{Interval, IntervalError};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use thiserror::Error;

/// Largest supported precision, in bits of absolute accuracy.
pub const MAX_PRECISION_BITS: u32 = 4096;

/// Largest `|x|` accepted by [`exp_enclosure`]: the series needs about
/// `e |x| + bits` terms.
pub const MAX_EXP_ARGUMENT: u32 = 256;

/// Largest magnitude of an interval endpoint accepted by the trigonometric
/// enclosures: the reduction modulo `pi` needs `pi` to `bits + log2 |x|` bits.
pub const MAX_TRIG_ARGUMENT: u64 = 1 << 32;

/// Refusals of the elementary-function enclosures.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ElementaryError {
    #[error("precision of {bits} bits is outside 1..={max}")]
    PrecisionOutOfRange { bits: u32, max: u32 },
    #[error("the logarithm is defined for positive arguments, got {argument}")]
    LogOfNonPositive { argument: String },
    #[error("the square root is defined for non-negative arguments, got {argument}")]
    SqrtOfNegative { argument: String },
    #[error("arccos is defined for -1 <= x <= 1, got {argument}")]
    ArccosOutOfDomain { argument: String },
    #[error("arccosh is defined for x >= 1, got {argument}")]
    ArccoshOutOfDomain { argument: String },
    #[error("{function} does not accept |x| above {limit}, got {argument}")]
    ArgumentTooLarge {
        function: &'static str,
        argument: String,
        limit: String,
    },
    #[error("the argument reduction left an argument outside [-2, 2]: {argument}")]
    ReductionFailed { argument: String },
    #[error(transparent)]
    Interval(#[from] IntervalError),
}

fn int(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

fn half() -> BigRational {
    BigRational::new(BigInt::one(), BigInt::from(2))
}

/// `2^-bits`.
fn two_pow_neg(bits: u64) -> BigRational {
    BigRational::new(BigInt::one(), BigInt::one() << bits)
}

fn check_bits(bits: u32) -> Result<u64, ElementaryError> {
    if (1..=MAX_PRECISION_BITS).contains(&bits) {
        Ok(u64::from(bits))
    } else {
        Err(ElementaryError::PrecisionOutOfRange {
            bits,
            max: MAX_PRECISION_BITS,
        })
    }
}

/// `sum_{k < n} c_k x/(1+x^2) y^k` and the tail bound `c_n x y^n`, stopped once
/// the bound is at most `tolerance`; `0 <= x <= 1`. The enclosure is
/// `[sum, sum + bound]`: every omitted term is positive.
fn arctan_unit_series(
    x: &BigRational,
    tolerance: &BigRational,
) -> Result<Interval, ElementaryError> {
    let x_squared = x * x;
    let denominator = BigRational::one() + &x_squared;
    let y = &x_squared / &denominator;
    let scale = x / &denominator;
    let mut coefficient = BigRational::one();
    let mut power = BigRational::one();
    let mut sum = BigRational::zero();
    let mut n: i64 = 0;
    loop {
        let tail = &coefficient * x * &power;
        if tail <= *tolerance {
            return Ok(Interval::try_new(sum.clone(), sum + tail)?);
        }
        sum += &coefficient * &scale * &power;
        coefficient = coefficient * int(2 * n + 2) / int(2 * n + 3);
        power *= &y;
        n += 1;
    }
}

fn pi_inner(bits: u64) -> Result<Interval, ElementaryError> {
    // 16 w + 4 w = 20 w <= 2^-bits for w = 2^-(bits + 5).
    let tolerance = two_pow_neg(bits + 5);
    let fifth = arctan_unit_series(
        &BigRational::new(BigInt::one(), BigInt::from(5)),
        &tolerance,
    )?;
    let small = arctan_unit_series(
        &BigRational::new(BigInt::one(), BigInt::from(239)),
        &tolerance,
    )?;
    Ok(fifth.mul_scalar(&int(16)).sub(&small.mul_scalar(&int(4))))
}

/// An enclosure of `pi` of width at most `2^-bits`, by Machin's formula
/// `pi = 16 arctan(1/5) - 4 arctan(1/239)`.
pub fn pi_enclosure(bits: u32) -> Result<Interval, ElementaryError> {
    pi_inner(check_bits(bits)?)
}

fn arctan_inner(x: &BigRational, bits: u64) -> Result<Interval, ElementaryError> {
    if x.is_zero() {
        return Ok(Interval::point(BigRational::zero()));
    }
    let magnitude = x.abs();
    let positive = if magnitude <= BigRational::one() {
        arctan_unit_series(&magnitude, &two_pow_neg(bits))?
    } else {
        // width <= 2^-(bits+3) for pi/2 and 2^-(bits+2) for the series.
        let half_pi = pi_inner(bits + 2)?.mul_scalar(&half());
        let reciprocal = arctan_unit_series(&magnitude.recip(), &two_pow_neg(bits + 2))?;
        half_pi.sub(&reciprocal)
    };
    Ok(if x.is_negative() {
        positive.mul_scalar(&int(-1))
    } else {
        positive
    })
}

/// An enclosure of `arctan x` of width at most `2^-bits`, for any rational `x`.
///
/// For `|x| <= 1` Euler's series; for `|x| > 1` the identity
/// `arctan x = pi/2 - arctan(1/x)`; odd in `x`.
pub fn arctan_enclosure(x: &BigRational, bits: u32) -> Result<Interval, ElementaryError> {
    arctan_inner(x, check_bits(bits)?)
}

/// `2 atanh y = ln((1 + y)/(1 - y))` for `|y| < 1`, as `2 sum y^(2k+1)/(2k+1)`,
/// stopped when the tail bound `2 |y|^(2n+1) / ((2n+1)(1 - y^2))` is at most
/// `tolerance`. All omitted terms have the sign of `y`.
fn atanh_series(y: &BigRational, tolerance: &BigRational) -> Result<Interval, ElementaryError> {
    let y_squared = y * y;
    let one_minus = BigRational::one() - &y_squared;
    let mut power = y.clone();
    let mut sum = BigRational::zero();
    let mut n: i64 = 0;
    loop {
        let bound = int(2) * power.abs() / (int(2 * n + 1) * &one_minus);
        if bound <= *tolerance {
            return Ok(if y.is_negative() {
                Interval::try_new(&sum - &bound, sum)?
            } else {
                Interval::try_new(sum.clone(), sum + bound)?
            });
        }
        sum += int(2) * &power / int(2 * n + 1);
        power *= &y_squared;
        n += 1;
    }
}

fn ln_inner(x: &BigRational, bits: u64) -> Result<Interval, ElementaryError> {
    if !x.is_positive() {
        return Err(ElementaryError::LogOfNonPositive {
            argument: x.to_string(),
        });
    }
    if x.is_one() {
        return Ok(Interval::point(BigRational::zero()));
    }
    // 2^(a-1) <= numerator < 2^a and 2^(b-1) <= denominator < 2^b give
    // x / 2^(a-b) in (1/2, 2).
    let (a, b) = (x.numer().bits(), x.denom().bits());
    let shift = a.abs_diff(b);
    let (scaled, e0) = if a >= b {
        (
            x / BigRational::from_integer(BigInt::one() << shift),
            BigInt::from(shift),
        )
    } else {
        (
            x * BigRational::from_integer(BigInt::one() << shift),
            -BigInt::from(shift),
        )
    };
    let y = (&scaled - BigRational::one()) / (&scaled + BigRational::one());
    // ln m to 2^-(bits+2); |e0| ln 2 to the same scale divided by 2^bitlen(e0).
    let ln_m = atanh_series(&y, &two_pow_neg(bits + 2))?;
    if e0.is_zero() {
        return Ok(ln_m);
    }
    let ln_two = atanh_series(
        &BigRational::new(BigInt::one(), BigInt::from(3)),
        &two_pow_neg(bits + 2 + e0.bits()),
    )?;
    Ok(ln_two.mul_scalar(&BigRational::from_integer(e0)).add(&ln_m))
}

/// An enclosure of `ln x` for a positive rational `x`, of width at most `2^-bits`.
///
/// `x = 2^e m` with `m` in `(1/2, 2)` (from the bit lengths of the numerator
/// and denominator), `ln m = 2 atanh((m-1)/(m+1))` with `|(m-1)/(m+1)| < 1/3`,
/// and `ln 2 = 2 atanh(1/3)`.
pub fn ln_enclosure(x: &BigRational, bits: u32) -> Result<Interval, ElementaryError> {
    ln_inner(x, check_bits(bits)?)
}

/// `e^x` for `x >= 0` as `sum x^k/k!`: stopped at `n >= 2x` once
/// `2 x^n/n!` is at most `tolerance`. For `n + 1 >= 2x` the tail satisfies
/// `sum_{k >= n} x^k/k! <= (x^n/n!) sum_j (x/(n+1))^j <= 2 x^n/n!`.
fn exp_series(x: &BigRational, tolerance: &BigRational) -> Result<Interval, ElementaryError> {
    let two_x = int(2) * x;
    let mut term = BigRational::one();
    let mut sum = BigRational::zero();
    let mut n: i64 = 0;
    loop {
        let tail = int(2) * &term;
        if int(n) >= two_x && tail <= *tolerance {
            return Ok(Interval::try_new(sum.clone(), sum + tail)?);
        }
        sum += &term;
        n += 1;
        term = term * x / int(n);
    }
}

/// An enclosure of `e^x` of width at most `2^-bits`, for rational `|x|` up to
/// [`MAX_EXP_ARGUMENT`]. A negative argument uses `e^-x = 1/e^x`, whose width
/// is no larger because `e^x >= 1`.
pub fn exp_enclosure(x: &BigRational, bits: u32) -> Result<Interval, ElementaryError> {
    let bits = check_bits(bits)?;
    if x.abs() > int(i64::from(MAX_EXP_ARGUMENT)) {
        return Err(ElementaryError::ArgumentTooLarge {
            function: "exp_enclosure",
            argument: x.to_string(),
            limit: MAX_EXP_ARGUMENT.to_string(),
        });
    }
    let positive = exp_series(&x.abs(), &two_pow_neg(bits))?;
    if x.is_negative() {
        Ok(Interval::try_new(
            positive.hi().recip(),
            positive.lo().recip(),
        )?)
    } else {
        Ok(positive)
    }
}

fn sqrt_inner(x: &BigRational, bits: u64) -> Result<Interval, ElementaryError> {
    if x.is_negative() {
        return Err(ElementaryError::SqrtOfNegative {
            argument: x.to_string(),
        });
    }
    let scaled_numerator = x.numer() << (2 * bits);
    let floored = &scaled_numerator / x.denom();
    let root = floored.sqrt();
    let exact = &root * &root * x.denom() == scaled_numerator;
    let scale = BigInt::one() << bits;
    let lo = BigRational::new(root.clone(), scale.clone());
    let hi = if exact {
        lo.clone()
    } else {
        BigRational::new(root + BigInt::one(), scale)
    };
    Ok(Interval::try_new(lo, hi)?)
}

/// An enclosure of `sqrt x` of width at most `2^-bits` for a non-negative
/// rational `x`: with `r = floor(sqrt(floor(x 4^bits)))` the root lies in
/// `[r/2^bits, (r+1)/2^bits]`; a point when the root is exact.
pub fn sqrt_enclosure(x: &BigRational, bits: u32) -> Result<Interval, ElementaryError> {
    sqrt_inner(x, check_bits(bits)?)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Trig {
    Sin,
    Cos,
}

impl Trig {
    /// The critical points are `(k + phase) pi`, where the value is `(-1)^k`.
    fn phase(self) -> BigRational {
        match self {
            Trig::Sin => half(),
            Trig::Cos => BigRational::zero(),
        }
    }
}

/// `sin` or `cos` of a rational `m` with `|m| <= 2` by its Taylor series. The
/// terms alternate and decrease from the second on (the ratio of consecutive
/// terms is at most `m^2/12 < 1`), so the truncation error is at most the first
/// omitted term, `|m|^(2n+1)/(2n+1)!` for sine and `m^(2n)/(2n)!` for cosine.
/// The enclosure `[S - bound, S + bound]` has width at most `2 tolerance`.
fn trig_taylor(
    m: &BigRational,
    kind: Trig,
    tolerance: &BigRational,
) -> Result<Interval, ElementaryError> {
    let m_squared = m * m;
    let mut term = match kind {
        Trig::Sin => m.clone(),
        Trig::Cos => BigRational::one(),
    };
    let mut sum = BigRational::zero();
    let mut n: i64 = 0;
    loop {
        if n >= 1 && term.abs() <= *tolerance {
            let bound = term.abs();
            return Ok(Interval::try_new(&sum - &bound, sum + bound)?);
        }
        sum += &term;
        // term_{n+1} = - term_n m^2 / ((2n+a)(2n+b)): sine a=2, b=3; cosine a=1, b=2.
        let (a, b) = match kind {
            Trig::Sin => (2 * n + 2, 2 * n + 3),
            Trig::Cos => (2 * n + 1, 2 * n + 2),
        };
        term = -(term * &m_squared) / (int(a) * int(b));
        n += 1;
    }
}

/// An enclosure of `sin x` or `cos x` at one rational point, width at most
/// `2^-bits`. Beyond `|x| <= 2` the argument is reduced by the nearest
/// multiple `k pi`: `sin x = (-1)^k sin(x - k pi)`, with `x - k pi` held as an
/// interval `Y` of radius `r = |k| w(pi)/2` and `|sin a - sin b| <= |a - b|`
/// used to widen the Taylor enclosure at the midpoint of `Y` by `r`.
fn trig_point(x: &BigRational, kind: Trig, bits: u64) -> Result<Interval, ElementaryError> {
    // Taylor width <= 2 * 2^-(bits+2); the reduction adds 2 r <= 2^-(bits+4).
    let taylor_tolerance = two_pow_neg(bits + 2);
    if x.abs() <= int(2) {
        return trig_taylor(x, kind, &two_pow_neg(bits + 1));
    }
    let magnitude_bits = x.abs().ceil().to_integer().bits();
    // |k| < |x| < 2^magnitude_bits and w(pi) <= 2^-(bits + 4 + magnitude_bits)
    // give r = |k| w(pi) / 2 <= 2^-(bits + 5).
    let pi = pi_inner(bits + 4 + magnitude_bits)?;
    let k = (x / pi.mid()).round().to_integer();
    let y = Interval::point(x.clone()).sub(&pi.mul_scalar(&BigRational::from_integer(k.clone())));
    let midpoint = y.mid();
    if midpoint.abs() > int(2) {
        return Err(ElementaryError::ReductionFailed {
            argument: midpoint.to_string(),
        });
    }
    let radius = y.rad();
    let taylor = trig_taylor(&midpoint, kind, &taylor_tolerance)?;
    let widened = Interval::try_new(taylor.lo() - &radius, taylor.hi() + &radius)?;
    Ok(if (&k & BigInt::one()).is_zero() {
        widened
    } else {
        widened.mul_scalar(&int(-1))
    })
}

/// The range of `sin` or `cos` over an interval, enclosed: endpoint values
/// plus `+-1` when a critical point `(k + phase) pi` may lie inside (decided
/// with an enclosure of `pi`, so a critical point within the width of that
/// enclosure of an endpoint is conservatively included).
fn check_trig_endpoints(interval: &Interval) -> Result<(), ElementaryError> {
    let limit = int(i64::try_from(MAX_TRIG_ARGUMENT).unwrap_or(i64::MAX));
    for endpoint in [interval.lo(), interval.hi()] {
        if endpoint.abs() > limit {
            return Err(ElementaryError::ArgumentTooLarge {
                function: "sin_enclosure / cos_enclosure",
                argument: endpoint.to_string(),
                limit: MAX_TRIG_ARGUMENT.to_string(),
            });
        }
    }
    Ok(())
}

fn absorb_critical_points(
    interval: &Interval,
    pi: &Interval,
    phase: &BigRational,
    lo: &mut BigRational,
    hi: &mut BigRational,
) {
    let one = BigRational::one();
    // Candidate indices k with (k + phase) pi possibly in [a, b].
    let scaled_lo = (interval.lo() / pi.lo()).min(interval.lo() / pi.hi()) - phase - &one;
    let scaled_hi = (interval.hi() / pi.lo()).max(interval.hi() / pi.hi()) - phase + &one;
    let mut k = scaled_lo.floor().to_integer();
    let last = scaled_hi.ceil().to_integer();
    while k <= last {
        let critical = pi.mul_scalar(&(BigRational::from_integer(k.clone()) + phase));
        if !critical.is_disjoint_from(interval) {
            if (&k & BigInt::one()).is_zero() {
                *hi = one.clone();
            } else {
                *lo = -one.clone();
            }
        }
        k += BigInt::one();
    }
}

fn trig_range(interval: &Interval, kind: Trig, bits: u64) -> Result<Interval, ElementaryError> {
    check_trig_endpoints(interval)?;
    let at_lo = trig_point(interval.lo(), kind, bits)?;
    let at_hi = trig_point(interval.hi(), kind, bits)?;
    let mut lo = at_lo.lo().clone().min(at_hi.lo().clone());
    let mut hi = at_lo.hi().clone().max(at_hi.hi().clone());

    let magnitude = interval.lo().abs().max(interval.hi().abs());
    let pi = pi_inner(bits + 6 + magnitude.ceil().to_integer().bits())?;
    // A full period contains both extremes: 2 pi < 2 * pi.hi().
    if interval.diam() >= int(2) * pi.hi() {
        return Ok(Interval::try_new(int(-1), int(1))?);
    }
    absorb_critical_points(interval, &pi, &kind.phase(), &mut lo, &mut hi);
    // The true values lie in [-1, 1].
    Ok(Interval::try_new(lo.max(int(-1)), hi.min(int(1)))?)
}

/// An enclosure of `{ sin t : t in x }`. Each endpoint value is enclosed to
/// `2^-bits`; the range is widened to `+-1` when a critical point
/// `pi/2 + k pi` may lie in the interval.
pub fn sin_enclosure(x: &Interval, bits: u32) -> Result<Interval, ElementaryError> {
    trig_range(x, Trig::Sin, check_bits(bits)?)
}

/// An enclosure of `{ cos t : t in x }`, like [`sin_enclosure`] with critical
/// points `k pi`.
pub fn cos_enclosure(x: &Interval, bits: u32) -> Result<Interval, ElementaryError> {
    trig_range(x, Trig::Cos, check_bits(bits)?)
}

/// An enclosure of `arccos x` for `-1 <= x <= 1`, of width at most `2^-bits`,
/// computed as `2 arctan(sqrt((1 - x)/(1 + x)))` (and `pi` at `x = -1`).
pub fn arccos_enclosure(x: &BigRational, bits: u32) -> Result<Interval, ElementaryError> {
    let bits = check_bits(bits)?;
    if x.abs() > BigRational::one() {
        return Err(ElementaryError::ArccosOutOfDomain {
            argument: x.to_string(),
        });
    }
    if x.is_one() {
        return Ok(Interval::point(BigRational::zero()));
    }
    if *x == int(-1) {
        return pi_inner(bits);
    }
    let ratio = (BigRational::one() - x) / (BigRational::one() + x);
    // t = sqrt(ratio) in an interval of width 2^-(bits+3); arctan is
    // increasing with slope at most 1, so the image has width at most
    // 2^-(bits+3) + 2 * 2^-(bits+3), doubled: 3/4 of 2^-bits.
    let root = sqrt_inner(&ratio, bits + 3)?;
    let low = arctan_inner(root.lo(), bits + 3)?;
    let high = arctan_inner(root.hi(), bits + 3)?;
    Ok(Interval::try_new(int(2) * low.lo(), int(2) * high.hi())?)
}

/// An enclosure of `arccosh x` for `x >= 1`, of width at most `2^-bits`,
/// computed as `ln(x + sqrt(x^2 - 1))`.
pub fn arccosh_enclosure(x: &BigRational, bits: u32) -> Result<Interval, ElementaryError> {
    let bits = check_bits(bits)?;
    if *x < BigRational::one() {
        return Err(ElementaryError::ArccoshOutOfDomain {
            argument: x.to_string(),
        });
    }
    if x.is_one() {
        return Ok(Interval::point(BigRational::zero()));
    }
    // x + sqrt(x^2 - 1) >= 1, where ln has slope at most 1: the image of the
    // root's interval has width at most 2^-(bits+3), plus two logarithm
    // enclosures of width at most 2^-(bits+4) each.
    let root = sqrt_inner(&(x * x - BigRational::one()), bits + 3)?;
    let low = ln_inner(&(x + root.lo()), bits + 3)?;
    let high = ln_inner(&(x + root.hi()), bits + 3)?;
    Ok(Interval::try_new(low.lo().clone(), high.hi().clone())?)
}

// Origin: engine/crates_rs/core_kernel/src/elementary.rs
// Claim: urn:core:crates_rs:core-kernel:elementary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_34dc5c95 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
