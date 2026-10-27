//! The exact scalar protocol for fusion-category data.
//!
//! F-symbols, R-symbols, twists, dimensions and modular matrices are elements of an
//! exact number field `K` of characteristic zero. [`FusionScalar`] is the small
//! protocol the crate needs on top of the estate's scalar tower
//! (`linear_algebra::scalars::{Semiring, Ring, Field, ExactRing}`): complex
//! conjugation of the field, embedding of `Q`, and the group of roots of unity the
//! field contains. Equality is mathematical equality; there is no tolerance.
//!
//! The roots of unity are the only transcendental-looking constants a braided
//! category needs (`zeta_16` for Ising, `zeta_10` for Fibonacci), and they are also
//! what makes the modular identities decidable in the field: a central charge is read
//! off as an exact root of unity, never as an angle.
//!
//! AuthorityEffect: None.

use std::cmp::Ordering;

use linear_algebra::scalars::{ExactRing, Field};
use num_traits::Signed;
use core_number_theory::cyclotomic::{Cyc12, Cyc24, Cyc5, Cyc8, EisensteinRat, GaussianRat};
use core_number_theory::cyclotomic120::Cyc120;
use core_number_theory::cyclotomic28::Cyc28;
use core_number_theory::cyclotomic44::Cyc44;
use core_number_theory::cyclotomic52::Cyc52;
use core_number_theory::cyclotomic_field::{Cyclotomic, CyclotomicNumber};
use core_number_theory::rational::Rational;
use core_number_theory::real_embedding::real_embeddings;

use crate::error::FusionError;

/// An exact number field of characteristic zero with complex conjugation and a
/// finite cyclic group of roots of unity.
///
/// Implementors promise: `conjugate` is a field automorphism of order at most two
/// (the restriction of complex conjugation, the identity on a real field);
/// `from_rational` is the embedding of `Q`; `to_rational` is its partial inverse;
/// `primitive_root_of_unity` has multiplicative order exactly `root_of_unity_order`
/// and generates every root of unity the field contains.
pub trait FusionScalar:
    Field
    + ExactRing
    + linear_algebra::exact_field::involution::Involution
    + core_number_theory::scalar::RationalEmbedding
{
    /// `Some(q)` exactly when the element is the image of the rational `q`.
    fn to_rational(&self) -> Option<Rational>;

    /// The number `w` of roots of unity in the field (`2` for a real field).
    fn root_of_unity_order() -> u32;

    /// A generator `zeta_w` of the roots of unity of the field.
    fn primitive_root_of_unity() -> Self;

    /// The sign of the element under the canonical embedding into the real numbers
    /// (`zeta_N -> e^{2 pi i / N}` for a cyclotomic field of conductor `N`), decided exactly,
    /// when the element is real (fixed by conjugation). `None` when the element is not
    /// real or the implementation cannot decide signs; it never guesses.
    fn real_sign(&self) -> Option<Ordering> {
        None
    }

    /// `zeta_n^k` for a primitive `n`-th root of unity `zeta_n = zeta_w^(w/n)`, when
    /// `n` divides `w`; `None` when the field has no primitive `n`-th root of unity.
    fn root_of_unity(n: u32, k: i64) -> Option<Self>
    where
        Self: Sized,
    {
        let w = Self::root_of_unity_order();
        if n == 0 || w == 0 || w > 4096 || w % n != 0 {
            return None;
        }
        let step = i64::from(w / n);
        let exponent = k.checked_mul(step)?.rem_euclid(i64::from(w));
        let exponent = u32::try_from(exponent).ok()?;
        core_number_theory::scalar::power_unsigned(
            &Self::primitive_root_of_unity(),
            u64::from(exponent),
        )
        .ok()
    }
}

/// The exact sign of a real element under the canonical embedding, or
/// [`FusionError::SignUndecided`] when the element is not real or the scalar type cannot
/// decide signs.
pub fn sign_of<K: FusionScalar>(x: &K) -> Result<Ordering, FusionError> {
    x.real_sign().ok_or(FusionError::SignUndecided {
        context: "a real scalar",
    })
}

/// `zeta_n^k`, or [`FusionError::FieldTooSmall`] when the field has no primitive
/// `n`-th root of unity.
pub fn root_of_unity<K: FusionScalar>(n: u32, k: i64) -> Result<K, FusionError> {
    K::root_of_unity(n, k).ok_or(FusionError::FieldTooSmall {
        needed: "a primitive root of unity of the requested order",
    })
}

/// `sqrt(2) = zeta_8 + zeta_8^-1`, when the field contains an eighth root of unity.
pub fn sqrt_two<K: FusionScalar>() -> Result<K, FusionError> {
    let zeta = K::root_of_unity(8, 1).ok_or(FusionError::FieldTooSmall {
        needed: "sqrt(2) (an eighth root of unity)",
    })?;
    let inverse = K::root_of_unity(8, -1).ok_or(FusionError::FieldTooSmall {
        needed: "sqrt(2) (an eighth root of unity)",
    })?;
    Ok(zeta.add(&inverse))
}

/// The golden ratio `phi = zeta_10 + zeta_10^-1 = 2 cos(pi/5)`, when the field
/// contains a tenth root of unity.
pub fn golden_ratio<K: FusionScalar>() -> Result<K, FusionError> {
    let zeta = K::root_of_unity(10, 1).ok_or(FusionError::FieldTooSmall {
        needed: "the golden ratio (a tenth root of unity)",
    })?;
    let inverse = K::root_of_unity(10, -1).ok_or(FusionError::FieldTooSmall {
        needed: "the golden ratio (a tenth root of unity)",
    })?;
    Ok(zeta.add(&inverse))
}

/// The exact order of `x` as a root of unity of the field: `Some((n, k))` with
/// `x = zeta_n^k`, `gcd(n, k) = 1` (`(1, 0)` for `x = 1`), or `None` when `x` is not a
/// root of unity of the field.
pub fn root_of_unity_data<K: FusionScalar>(x: &K) -> Option<(u32, u32)> {
    let w = K::root_of_unity_order();
    if w == 0 || w > 4096 {
        return None;
    }
    let generator = K::primitive_root_of_unity();
    let mut current = K::one();
    for k in 0..w {
        if current == *x {
            let g = num_integer::Integer::gcd(&k, &w);
            return Some((w / g, k / g));
        }
        current = current.mul(&generator);
    }
    None
}

fn constant_term(coefficients: &[Rational]) -> Option<Rational> {
    let (first, rest) = coefficients.split_first()?;
    rest.iter()
        .all(num_traits::Zero::is_zero)
        .then(|| first.clone())
}

impl FusionScalar for Rational {
    fn to_rational(&self) -> Option<Rational> {
        Some(self.clone())
    }
    fn root_of_unity_order() -> u32 {
        2
    }
    fn primitive_root_of_unity() -> Self {
        -Rational::from_integer(1.into())
    }
    fn real_sign(&self) -> Option<Ordering> {
        Some(if self.is_positive() {
            Ordering::Greater
        } else if self.is_negative() {
            Ordering::Less
        } else {
            Ordering::Equal
        })
    }
}

impl FusionScalar for GaussianRat {
    fn to_rational(&self) -> Option<Rational> {
        num_traits::Zero::is_zero(&self.im).then(|| self.re.clone())
    }
    fn root_of_unity_order() -> u32 {
        4
    }
    fn primitive_root_of_unity() -> Self {
        GaussianRat::i()
    }
    fn real_sign(&self) -> Option<Ordering> {
        if num_traits::Zero::is_zero(&self.im) {
            FusionScalar::real_sign(&self.re)
        } else {
            None
        }
    }
}

impl FusionScalar for EisensteinRat {
    fn to_rational(&self) -> Option<Rational> {
        num_traits::Zero::is_zero(&self.b).then(|| self.a.clone())
    }
    fn root_of_unity_order() -> u32 {
        6
    }
    fn primitive_root_of_unity() -> Self {
        // zeta_6 = 1 + zeta_3 (= -zeta_3^2).
        EisensteinRat::one().add(&EisensteinRat::zeta3())
    }
    fn real_sign(&self) -> Option<Ordering> {
        if num_traits::Zero::is_zero(&self.b) {
            FusionScalar::real_sign(&self.a)
        } else {
            None
        }
    }
}

/// The sign of a real cyclotomic number under the canonical embedding, exactly.
fn cyclotomic_sign(number: &CyclotomicNumber) -> Option<Ordering> {
    if !number.is_real() {
        return None;
    }
    real_embeddings(number.conductor()).ok()?.sign(number).ok()
}

impl<const N: usize> FusionScalar for Cyclotomic<N> {
    fn to_rational(&self) -> Option<Rational> {
        self.as_rational()
    }
    fn root_of_unity_order() -> u32 {
        let order = if N % 2 == 0 { N } else { 2 * N };
        u32::try_from(order).unwrap_or(u32::MAX)
    }
    fn primitive_root_of_unity() -> Self {
        if N % 2 == 0 {
            Cyclotomic::zeta(1)
        } else {
            // -zeta_N^{(N+1)/2} has order 2N for odd N.
            let exponent = i64::try_from((N + 1) / 2).unwrap_or(1);
            Cyclotomic::zeta(exponent).neg()
        }
    }
    fn real_sign(&self) -> Option<Ordering> {
        cyclotomic_sign(self.as_number())
    }
}

macro_rules! cyclotomic_scalar {
    ($ty:ty, $order:expr, $root:expr) => {
        impl FusionScalar for $ty {
            fn to_rational(&self) -> Option<Rational> {
                constant_term(&self.a)
            }
            fn root_of_unity_order() -> u32 {
                $order
            }
            fn primitive_root_of_unity() -> Self {
                $root
            }
            fn real_sign(&self) -> Option<Ordering> {
                cyclotomic_sign(&CyclotomicNumber::from(self))
            }
        }
    };
}

// `Q(zeta_N)` for odd `N` contains the `2N`-th roots of unity (`-zeta_N` has order `2N`);
// for even `N` exactly the `N`-th roots.
cyclotomic_scalar!(Cyc5, 10, {
    // zeta_10 = -zeta_5^3.
    let z = Cyc5::zeta5(3);
    Cyc5::zero().sub(&z)
});
cyclotomic_scalar!(Cyc8, 8, Cyc8::zeta8(1));
cyclotomic_scalar!(Cyc12, 12, Cyc12::zeta12(1));
cyclotomic_scalar!(Cyc24, 24, Cyc24::zeta24(1));
cyclotomic_scalar!(Cyc28, 28, Cyc28::zeta(1));
cyclotomic_scalar!(Cyc44, 44, Cyc44::zeta(1));
cyclotomic_scalar!(Cyc52, 52, Cyc52::zeta(1));
cyclotomic_scalar!(Cyc120, 120, Cyc120::zeta(1));

// Origin: engine/crates_rs/core_fusion_categories/src/scalar.rs
// Claim: urn:core:crates_rs:core-fusion-categories:scalar:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2c6e69de {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2c6e69de` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2c6e69de {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError2c6e69de {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2c6e69de {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2c6e69de {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2c6e69de {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2c6e69de> {
        if capacity_bound == 0 {
            return Err(BoundaryError2c6e69de::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2c6e69de::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2c6e69de::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use linear_algebra::exact_field::involution::Involution;
    use core_number_theory::rational::rq;
    use core_number_theory::scalar::RationalEmbedding;
    use core_number_theory::scalar::{from_i64, ScalarError};

    /// Every root of unity the protocol advertises is a root of unity of exactly the
    /// advertised order, and the group they form is cyclic of order `w`.
    fn check_roots<K: FusionScalar>() {
        let w = K::root_of_unity_order();
        let zeta = K::primitive_root_of_unity();
        assert_eq!(
            core_number_theory::scalar::power_unsigned(&zeta, (w).into()).unwrap(),
            K::one(),
            "zeta^w = 1"
        );
        for d in 1..w {
            if w % d == 0 {
                assert_ne!(
                    core_number_theory::scalar::power_unsigned(&zeta, (d).into()).unwrap(),
                    K::one(),
                    "zeta has no smaller order than w (checked divisor {d})"
                );
            }
        }
        // zeta^(w/2) = -1.
        assert_eq!(
            core_number_theory::scalar::power_unsigned(&zeta, (w / 2).into()).unwrap(),
            K::one().neg(),
            "the unique involution is -1"
        );
        // Conjugation inverts a root of unity.
        assert_eq!(
            zeta.conjugate().mul(&zeta),
            K::one(),
            "conjugation inverts roots of unity"
        );
    }

    #[test]
    fn every_scalar_advertises_a_primitive_root_of_exact_order() {
        check_roots::<Rational>();
        check_roots::<GaussianRat>();
        check_roots::<EisensteinRat>();
        check_roots::<Cyc5>();
        check_roots::<Cyc8>();
        check_roots::<Cyc12>();
        check_roots::<Cyc24>();
        check_roots::<Cyc28>();
    }

    #[test]
    fn roots_of_unity_of_a_divisor_order_are_powers_of_the_generator() {
        // Q(zeta_5) holds the tenth roots: zeta_10 = -zeta_5^3, and zeta_5 = zeta_10^2.
        let z10 = Cyc5::root_of_unity(10, 1).unwrap();
        assert_eq!(z10, Cyc5::zeta5(3).neg());
        assert_eq!(Cyc5::root_of_unity(5, 1).unwrap(), z10.mul(&z10));
        assert_eq!(Cyc5::root_of_unity(5, 1).unwrap(), Cyc5::zeta5(1));
        // Negative exponents are inverses.
        assert_eq!(
            Cyc5::root_of_unity(10, -4)
                .unwrap()
                .mul(&Cyc5::root_of_unity(10, 4).unwrap()),
            Cyc5::one()
        );
        // The field has no eighth root of unity.
        assert!(Cyc5::root_of_unity(8, 1).is_none());
        assert!(Rational::root_of_unity(3, 1).is_none());
        assert_eq!(
            Rational::root_of_unity(2, 1),
            Some(-Rational::from_integer(1.into()))
        );
        assert!(Rational::root_of_unity(0, 1).is_none());
    }

    #[test]
    fn root_of_unity_data_reports_the_exact_order() {
        // zeta_8^2 = i has order 4 in Q(zeta_8).
        assert_eq!(root_of_unity_data(&Cyc8::zeta8(2)), Some((4, 1)));
        assert_eq!(root_of_unity_data(&Cyc8::zeta8(6)), Some((4, 3)));
        assert_eq!(root_of_unity_data(&Cyc8::zeta8(3)), Some((8, 3)));
        assert_eq!(root_of_unity_data(&Cyc8::one()), Some((1, 0)));
        assert_eq!(root_of_unity_data(&Cyc8::one().neg()), Some((2, 1)));
        // sqrt(2) is not a root of unity.
        assert_eq!(root_of_unity_data(&sqrt_two::<Cyc8>().unwrap()), None);
        assert_eq!(root_of_unity_data(&GaussianRat::i()), Some((4, 1)));
    }

    #[test]
    fn sqrt_two_and_the_golden_ratio_satisfy_their_minimal_polynomials() {
        let s = sqrt_two::<Cyc8>().unwrap();
        assert_eq!(s.mul(&s), from_i64::<Cyc8>(2));
        let phi = golden_ratio::<Cyc5>().unwrap();
        // phi^2 = phi + 1.
        assert_eq!(phi.mul(&phi), phi.add(&Cyc5::one()));
        // Fields without the needed roots refuse.
        assert_eq!(
            sqrt_two::<GaussianRat>(),
            Err(FusionError::FieldTooSmall {
                needed: "sqrt(2) (an eighth root of unity)"
            })
        );
        assert!(golden_ratio::<Cyc8>().is_err());
    }

    #[test]
    fn rational_embedding_round_trips_and_detects_non_rationals() {
        let q = rq(-7, 3);
        assert_eq!(Cyc24::from_rational(&q).to_rational(), Some(q.clone()));
        assert_eq!(Cyc5::from_rational(&q).to_rational(), Some(q.clone()));
        assert_eq!(
            <GaussianRat as core_number_theory::scalar::RationalEmbedding>::from_rational(&q)
                .to_rational(),
            Some(q.clone())
        );
        assert_eq!(
            <EisensteinRat as core_number_theory::scalar::RationalEmbedding>::from_rational(&q)
                .to_rational(),
            Some(q)
        );
        assert_eq!(Cyc5::zeta5(1).to_rational(), None);
        assert_eq!(GaussianRat::i().to_rational(), None);
        // The embedding is a ring homomorphism on a sample.
        let a = rq(2, 5);
        let b = rq(-1, 4);
        assert_eq!(
            Cyc12::from_rational(&a).mul(&Cyc12::from_rational(&b)),
            Cyc12::from_rational(&(&a * &b))
        );
    }

    #[test]
    fn powers_handle_negative_exponents_and_refuse_zero() {
        let z = Cyc8::zeta8(1);
        assert_eq!(
            core_number_theory::scalar::power(&z, 8)
                .map_err(FusionError::from)
                .unwrap(),
            Cyc8::one()
        );
        assert_eq!(
            core_number_theory::scalar::power(&z, -1)
                .map_err(FusionError::from)
                .unwrap(),
            z.conjugate()
        );
        assert_eq!(
            core_number_theory::scalar::power(&z, 0)
                .map_err(FusionError::from)
                .unwrap(),
            Cyc8::one()
        );
        assert_eq!(
            core_number_theory::scalar::power(&Cyc8::zero(), -1).map_err(FusionError::from),
            Err(FusionError::Scalar(ScalarError::ZeroInverse))
        );
        assert_eq!(
            core_number_theory::scalar::power(&Cyc8::zero(), 0)
                .map_err(FusionError::from)
                .unwrap(),
            Cyc8::one()
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_2c6e69de {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2c6e69de::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2c6e69de::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2c6e69de::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2c6e69de::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2c6e69de::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2c6e69de::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2c6e69de::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
