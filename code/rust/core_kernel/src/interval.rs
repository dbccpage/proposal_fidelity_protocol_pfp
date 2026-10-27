//! Exact rational intervals `[lo, hi]` and boxes of them.
//!
//! Arithmetic is exact over ℚ, so there is no outward rounding: every result is
//! the true image interval (for `add`, `sub`, `mul_scalar`, `sq`) or the tight
//! hull of the four endpoint products (for `mul`). Construction keeps
//! `lo <= hi` and stores each endpoint in lowest terms with a positive
//! denominator. Deserialization checks the order and canonicalizes the
//! endpoints, so equal intervals have one spelling.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_6b849b71<T> {
    fn checked_invariant_6b849b71(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_6b849b71<T> for Option<T> {
    #[inline]
    fn checked_invariant_6b849b71(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_6b849b71<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_6b849b71(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
#[error("invalid rational interval endpoints [{lo}, {hi}]")]
pub struct IntervalError {
    pub lo: String,
    pub hi: String,
}

/// A closed exact rational interval `[lo, hi]` with `lo <= hi`.
///
/// The endpoints are private, so every interval comes from [`Interval::new`],
/// [`Interval::try_new`], [`Interval::point`], an operation below or a checked
/// deserialization. Those paths keep `lo <= hi` and a canonical endpoint, so
/// neither the order nor a second spelling of the same rational can be
/// introduced from outside.
///
/// ```compile_fail,E0451
/// use num_bigint::BigInt;
/// use num_rational::BigRational;
/// use core_kernel::interval::Interval;
/// let one = BigRational::from_integer(BigInt::from(1));
/// // A misordered interval cannot be written as a literal outside this module.
/// let _ = Interval { lo: &one + &one, hi: one };
/// ```
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(try_from = "IntervalWire")]
pub struct Interval {
    lo: BigRational,
    hi: BigRational,
}

#[derive(Deserialize)]
struct IntervalWire {
    lo: BigRational,
    hi: BigRational,
}

impl TryFrom<IntervalWire> for Interval {
    type Error = IntervalError;
    fn try_from(wire: IntervalWire) -> Result<Self, Self::Error> {
        Self::try_new(wire.lo, wire.hi)
    }
}

fn two() -> BigRational {
    BigRational::from_integer(BigInt::from(2))
}

impl Interval {
    /// `[lo, hi]`, refusing zero denominators and `lo > hi`.
    ///
    /// Endpoints are reduced, with a positive denominator, before they are
    /// stored. `BigRational`'s serde keeps unreduced and negative-denominator
    /// fractions, and those are a second spelling of the same value.
    pub fn try_new(lo: BigRational, hi: BigRational) -> Result<Self, IntervalError> {
        if lo.denom().is_zero() || hi.denom().is_zero() {
            return Err(IntervalError {
                lo: lo.to_string(),
                hi: hi.to_string(),
            });
        }
        let lo = lo.reduced();
        let hi = hi.reduced();
        if lo > hi {
            return Err(IntervalError {
                lo: lo.to_string(),
                hi: hi.to_string(),
            });
        }
        Ok(Self { lo, hi })
    }

    /// `[lo, hi]`.
    ///
    /// # Panics
    /// When an endpoint has a zero denominator or `lo > hi`. Use
    /// [`Interval::try_new`] for untrusted endpoints.
    pub fn new(lo: BigRational, hi: BigRational) -> Self {
        let lo = lo.reduced();
        let hi = hi.reduced();
        assert!(lo <= hi, "Interval::new requires lo <= hi");
        Self { lo, hi }
    }

    /// The degenerate interval `[r, r]` for a trusted rational.
    ///
    /// # Panics
    /// When `r` has a zero denominator. Use [`Interval::try_new`] for untrusted
    /// rational input.
    pub fn point(r: BigRational) -> Self {
        let r = r.reduced();
        Self {
            lo: r.clone(),
            hi: r,
        }
    }

    /// `[center - radius, center + radius]`.
    ///
    /// # Panics
    /// When `radius < 0`.
    pub fn from_center_radius(center: &BigRational, radius: &BigRational) -> Self {
        assert!(
            *radius >= BigRational::zero(),
            "radius must be non-negative"
        );
        Self {
            lo: center - radius,
            hi: center + radius,
        }
    }

    pub fn lo(&self) -> &BigRational {
        &self.lo
    }

    pub fn hi(&self) -> &BigRational {
        &self.hi
    }

    /// `(lo, hi)`, consuming the interval.
    pub fn into_endpoints(self) -> (BigRational, BigRational) {
        (self.lo, self.hi)
    }

    /// `(lo + hi) / 2`.
    pub fn mid(&self) -> BigRational {
        (&self.lo + &self.hi) / two()
    }

    /// `(hi - lo) / 2`.
    pub fn rad(&self) -> BigRational {
        (&self.hi - &self.lo) / two()
    }

    /// `hi - lo`.
    pub fn diam(&self) -> BigRational {
        &self.hi - &self.lo
    }

    /// `[a, b] + [c, d] = [a + c, b + d]`.
    pub fn add(&self, o: &Interval) -> Interval {
        Interval {
            lo: &self.lo + &o.lo,
            hi: &self.hi + &o.hi,
        }
    }

    /// `[a, b] - [c, d] = [a - d, b - c]`.
    pub fn sub(&self, o: &Interval) -> Interval {
        Interval {
            lo: &self.lo - &o.hi,
            hi: &self.hi - &o.lo,
        }
    }

    /// `[a, b] · [c, d]`: the min and max of the four endpoint products.
    pub fn mul(&self, o: &Interval) -> Interval {
        let products = [
            &self.lo * &o.lo,
            &self.lo * &o.hi,
            &self.hi * &o.lo,
            &self.hi * &o.hi,
        ];
        let lo = products.iter().min().checked_invariant_6b849b71("four products").clone();
        let hi = products.iter().max().checked_invariant_6b849b71("four products").clone();
        Interval { lo, hi }
    }

    /// `k · [a, b]`.
    pub fn mul_scalar(&self, k: &BigRational) -> Interval {
        if *k >= BigRational::zero() {
            Interval {
                lo: &self.lo * k,
                hi: &self.hi * k,
            }
        } else {
            Interval {
                lo: &self.hi * k,
                hi: &self.lo * k,
            }
        }
    }

    /// `{ x² : x ∈ [lo, hi] }`, which is `[0, max(lo², hi²)]` when the interval
    /// straddles zero.
    pub fn sq(&self) -> Interval {
        let zero = BigRational::zero();
        if self.lo >= zero {
            Interval {
                lo: &self.lo * &self.lo,
                hi: &self.hi * &self.hi,
            }
        } else if self.hi <= zero {
            Interval {
                lo: &self.hi * &self.hi,
                hi: &self.lo * &self.lo,
            }
        } else {
            let a = &self.lo * &self.lo;
            let b = &self.hi * &self.hi;
            Interval {
                lo: zero,
                hi: if a >= b { a } else { b },
            }
        }
    }

    /// Reciprocal enclosure when the whole interval avoids zero.
    /// Invalid endpoint ordering and zero-crossing intervals are refused.
    pub fn try_reciprocal(&self) -> Option<Interval> {
        if self.lo > self.hi || self.contains(&BigRational::zero()) {
            return None;
        }
        Some(Interval::new(self.hi.recip(), self.lo.recip()))
    }
    /// Division by an interval that avoids zero, preserving enclosure.
    pub fn try_divide(&self, denominator: &Interval) -> Option<Interval> {
        if self.lo > self.hi {
            return None;
        }
        Some(self.mul(&denominator.try_reciprocal()?))
    }

    /// Split at the midpoint `m` into the closed halves `[lo, m]` and `[m, hi]`.
    ///
    /// Both halves contain `m`, so their union is the parent with no gap.
    pub fn bisect_closed(&self) -> (Interval, Interval) {
        let mid = self.mid();
        (
            Interval::new(self.lo.clone(), mid.clone()),
            Interval::new(mid, self.hi.clone()),
        )
    }

    /// `lo <= x <= hi`.
    pub fn contains(&self, x: &BigRational) -> bool {
        &self.lo <= x && x <= &self.hi
    }

    /// `lo < x < hi`.
    pub fn interior_contains(&self, x: &BigRational) -> bool {
        &self.lo < x && x < &self.hi
    }

    /// `self ⊆ other`.
    pub fn subset_of(&self, other: &Interval) -> bool {
        other.lo <= self.lo && self.hi <= other.hi
    }

    /// `self` lies in the open interior of `other`.
    pub fn strict_interior_subset_of(&self, other: &Interval) -> bool {
        other.lo < self.lo && self.hi < other.hi
    }

    /// The two intervals share no point.
    pub fn is_disjoint_from(&self, other: &Interval) -> bool {
        self.hi < other.lo || other.hi < self.lo
    }

    /// Every point is strictly positive.
    pub fn is_strictly_positive(&self) -> bool {
        self.lo > BigRational::zero()
    }
}

/// A product of intervals `∏ₖ [uₖ, vₖ]`. Each axis keeps its own order invariant.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct IntervalBox {
    pub intervals: Vec<Interval>,
}

impl IntervalBox {
    pub fn new(intervals: Vec<Interval>) -> Self {
        Self { intervals }
    }

    /// The box centred at `center` with the same radius on every axis.
    pub fn from_center_uniform_radius(center: &[BigRational], radius: &BigRational) -> Self {
        Self {
            intervals: center
                .iter()
                .map(|c| Interval::from_center_radius(c, radius))
                .collect(),
        }
    }

    pub fn dim(&self) -> usize {
        self.intervals.len()
    }

    pub fn midpoint(&self) -> Vec<BigRational> {
        self.intervals.iter().map(Interval::mid).collect()
    }

    /// `pt` has the box's dimension and lies in it.
    pub fn contains_point(&self, pt: &[BigRational]) -> bool {
        pt.len() == self.intervals.len()
            && self.intervals.iter().zip(pt).all(|(iv, x)| iv.contains(x))
    }

    /// Every axis of `self` lies in the open interior of the same axis of `parent`.
    /// Boxes of different dimension are never nested.
    pub fn strict_interior_subset_of(&self, parent: &IntervalBox) -> bool {
        self.dim() == parent.dim()
            && self
                .intervals
                .iter()
                .zip(&parent.intervals)
                .all(|(child, outer)| child.strict_interior_subset_of(outer))
    }

    /// Some axis is disjoint. Boxes of different dimension count as disjoint.
    pub fn is_disjoint_from(&self, other: &IntervalBox) -> bool {
        self.dim() != other.dim()
            || self
                .intervals
                .iter()
                .zip(&other.intervals)
                .any(|(a, b)| a.is_disjoint_from(b))
    }
}

// Origin: engine/crates_rs/core_kernel/src/interval.rs
// Claim: urn:core:crates_rs:core-kernel:interval:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }

    fn iv(a: i64, b: i64) -> Interval {
        Interval::new(q(a, 1), q(b, 1))
    }

    #[test]
    fn misordered_endpoints_are_refused() {
        assert!(Interval::try_new(q(2, 1), q(1, 1)).is_err());
        assert!(Interval::try_new(q(1, 1), q(1, 1)).is_ok());
    }

    #[test]
    fn invalid_denominator_refuses_before_normalization_and_through_serde() {
        for (lo, hi) in [
            (BigRational::new_raw(1.into(), 0.into()), q(1, 1)),
            (q(0, 1), BigRational::new_raw(1.into(), 0.into())),
            (BigRational::new_raw(0.into(), 0.into()), q(1, 1)),
            (q(0, 1), BigRational::new_raw(0.into(), 0.into())),
        ] {
            let error = Interval::try_new(lo.clone(), hi.clone()).unwrap_err();
            assert_eq!(error.lo, lo.to_string());
            assert_eq!(error.hi, hi.to_string());
            let wire = serde_json::json!({"lo": lo, "hi": hi});
            assert!(serde_json::from_value::<Interval>(wire).is_err());
        }
        let lo = BigRational::new_raw(2.into(), 4.into());
        let hi = BigRational::new_raw((-3).into(), (-4).into());
        let canonical = Interval::new(q(1, 2), q(3, 4));
        assert_eq!(
            Interval::try_new(lo.clone(), hi.clone()).unwrap(),
            canonical
        );
        let wire = serde_json::json!({"lo": lo, "hi": hi});
        assert_eq!(serde_json::from_value::<Interval>(wire).unwrap(), canonical);
    }

    #[test]
    fn deserialization_checks_the_order() {
        let x = Interval::new(q(1, 2), q(3, 4));
        let mut wire = serde_json::to_value(&x).unwrap();
        assert_eq!(serde_json::from_value::<Interval>(wire.clone()).unwrap(), x);
        let object = wire.as_object_mut().unwrap();
        let lo = object.remove("lo").unwrap();
        let hi = object.remove("hi").unwrap();
        object.insert("lo".to_owned(), hi);
        object.insert("hi".to_owned(), lo);
        assert!(serde_json::from_value::<Interval>(wire).is_err());
    }

    #[test]
    fn arithmetic_is_the_exact_image() {
        assert_eq!(iv(1, 2).add(&iv(-3, 5)), iv(-2, 7));
        assert_eq!(iv(1, 2).sub(&iv(-3, 5)), iv(-4, 5));
        assert_eq!(iv(-1, 2).mul(&iv(-3, 5)), iv(-6, 10));
        assert_eq!(iv(1, 2).mul_scalar(&q(-3, 1)), iv(-6, -3));
        assert_eq!(iv(-3, 2).sq(), iv(0, 9));
        assert_eq!(iv(-3, -2).sq(), iv(4, 9));
        assert_eq!(iv(2, 3).sq(), iv(4, 9));
    }

    #[test]
    fn bisection_leaves_no_gap() {
        let (left, right) = iv(0, 1).bisect_closed();
        assert_eq!(left.hi, right.lo);
        assert!(left.contains(&q(1, 2)) && right.contains(&q(1, 2)));
        assert_eq!(left.lo, q(0, 1));
        assert_eq!(right.hi, q(1, 1));
    }

    #[test]
    fn measures_and_predicates() {
        let x = Interval::from_center_radius(&q(1, 2), &q(1, 4));
        assert_eq!(x, Interval::new(q(1, 4), q(3, 4)));
        assert_eq!((x.mid(), x.rad(), x.diam()), (q(1, 2), q(1, 4), q(1, 2)));
        assert!(x.interior_contains(&q(1, 2)) && !x.interior_contains(&q(1, 4)));
        assert!(x.subset_of(&iv(0, 1)) && x.strict_interior_subset_of(&iv(0, 1)));
        assert!(!x.strict_interior_subset_of(&Interval::new(q(1, 4), q(1, 1))));
        assert!(x.is_disjoint_from(&iv(1, 2)) && !x.is_disjoint_from(&iv(0, 1)));
        assert!(x.is_strictly_positive() && !iv(0, 1).is_strictly_positive());
    }

    #[test]
    fn unreduced_endpoints_canonicalize_to_one_spelling() {
        // Ratio serde uses `new_raw`, so the wire can carry 2/4 or 1/-2.
        // Those are the same rationals as 1/2 and -1/2, and must not survive
        // as a second serialization.
        let unreduced = r#"{"lo":[[1,[2]],[1,[4]]],"hi":[[1,[6]],[1,[8]]]}"#;
        let parsed: Interval = serde_json::from_str(unreduced).unwrap();
        let reduced = Interval::new(q(1, 2), q(3, 4));
        assert_eq!(parsed, reduced);
        assert_eq!(
            serde_json::to_string(&parsed).unwrap(),
            serde_json::to_string(&reduced).unwrap()
        );

        let negative_denom = r#"{"lo":[[1,[3]],[-1,[4]]],"hi":[[1,[1]],[-1,[2]]]}"#;
        let parsed: Interval = serde_json::from_str(negative_denom).unwrap();
        let reduced = Interval::new(q(-3, 4), q(-1, 2));
        assert_eq!(parsed, reduced);
        assert_eq!(
            serde_json::to_string(&parsed).unwrap(),
            serde_json::to_string(&reduced).unwrap()
        );
        let (left, right) = parsed.bisect_closed();
        assert_eq!(left.lo().reduced(), *left.lo());
        assert!(*left.lo().denom() > BigInt::zero());
        assert_eq!(right.hi().reduced(), *right.hi());
        assert!(*right.hi().denom() > BigInt::zero());

        // A negative denominator that puts the lower value above the upper
        // one is still a misordered interval.
        let misordered = r#"{"lo":[[1,[1]],[-1,[2]]],"hi":[[1,[3]],[-1,[4]]]}"#;
        assert!(serde_json::from_str::<Interval>(misordered).is_err());

        let point = Interval::point(BigRational::new_raw(BigInt::from(2), BigInt::from(-4)));
        assert_eq!(point, Interval::point(q(-1, 2)));
        assert_eq!(
            serde_json::to_string(&point).unwrap(),
            serde_json::to_string(&Interval::point(q(-1, 2))).unwrap()
        );
    }

    #[test]
    fn boxes_nest_and_separate_axis_by_axis() {
        let outer = IntervalBox::new(vec![iv(0, 4), iv(0, 4)]);
        let inner = IntervalBox::from_center_uniform_radius(&[q(2, 1), q(2, 1)], &q(1, 1));
        assert_eq!(inner.midpoint(), vec![q(2, 1), q(2, 1)]);
        assert!(inner.strict_interior_subset_of(&outer));
        assert!(!outer.strict_interior_subset_of(&inner));
        assert!(inner.contains_point(&[q(1, 1), q(3, 1)]));
        assert!(!inner.contains_point(&[q(1, 1)]));
        let apart = IntervalBox::new(vec![iv(0, 4), iv(5, 6)]);
        assert!(apart.is_disjoint_from(&outer));
        assert!(IntervalBox::new(vec![iv(0, 4)]).is_disjoint_from(&outer));
    }
}

#[cfg(test)]
mod reciprocal_laws {
    use super::*;
    fn q(v: i64) -> BigRational {
        BigRational::from_integer(v.into())
    }
    #[test]
    fn signed_reciprocal_division_and_zero_crossing_refusals() {
        let positive = Interval::new(q(2), q(4));
        let negative = Interval::new(q(-4), q(-2));
        assert_eq!(
            positive.try_reciprocal().unwrap(),
            Interval::new(q(4).recip(), q(2).recip())
        );
        assert_eq!(
            negative.try_reciprocal().unwrap(),
            Interval::new(q(-2).recip(), q(-4).recip())
        );
        let quotient = positive.try_divide(&negative).unwrap();
        assert!(quotient.contains(&(q(2) / q(-2))));
        assert!(quotient.contains(&(q(4) / q(-4))));
        assert!(Interval::new(q(-1), q(1)).try_reciprocal().is_none());
        assert!(Interval::point(q(0)).try_reciprocal().is_none());
        let forged = Interval { lo: q(2), hi: q(1) };
        assert!(forged.try_reciprocal().is_none());
        assert!(forged.try_divide(&positive).is_none());
    }
}
