//! The exact scalar tower for this crate's number fields.
//!
//! Every exact type here is a commutative ring whose equality is mathematical
//! equality (elements are stored in a canonical reduced form), and every nonzero
//! element is invertible. This module states that in the vocabulary the rest of the
//! estate already uses:
//!
//! - `std::ops::{Add, Sub, Mul, Neg}` (owned and by reference), so
//!   `linear_algebra::backend::basic_matrix::BasicMatrix<T>` and its checked
//!   products apply;
//! - `num_traits::{Zero, One}`;
//! - `linear_algebra::scalars::{Semiring, Ring, Field, ExactRing}`, the tower that
//!   the exact rank, kernel, determinant and path-sum algorithms are generic over.
//!
//! The tower delegates to each number field's arithmetic and complex conjugation.
//! Rational embedding is declared separately from the ring and involution laws.
//!
//! AuthorityEffect: None.

use linear_algebra::scalars::{ExactRing, Field, Ring, Semiring};

use crate::cyclotomic::{Cyc12, Cyc24, Cyc5, Cyc8, EisensteinRat, GaussianRat};
use crate::cyclotomic120::Cyc120;
use crate::cyclotomic28::Cyc28;
use crate::cyclotomic44::Cyc44;
use crate::cyclotomic52::Cyc52;

/// The specified embedding of Q into an exact field of characteristic zero.
/// Implementers preserve zero, one, addition, and multiplication exactly.
pub trait RationalEmbedding: Field + ExactRing {
    fn from_rational(value: &crate::rational::Rational) -> Self;
}

/// Generic exact scalar refusals, independent of any domain carrier.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ScalarError {
    #[error("the inverse of zero is undefined")]
    ZeroInverse,
    #[error("a nonzero element violates the declared field inverse law")]
    FieldContract,
    #[error("{what} exceeds the scalar work budget {limit}")]
    Budget { what: &'static str, limit: u64 },
}

/// The exponent bound limits scalar-internal output growth as well as work.
pub const MAX_SCALAR_EXPONENT: u64 = 1 << 20;
pub const MAX_EMBEDDED_POLYNOMIAL_COEFFICIENTS: usize = 1024;

/// Exact semiring power, including `0^0=1`, with an explicit exponent bound.
pub fn power_unsigned<K: Semiring>(x: &K, mut exponent: u64) -> Result<K, ScalarError> {
    if exponent > MAX_SCALAR_EXPONENT {
        return Err(ScalarError::Budget {
            what: "unsigned exponent",
            limit: MAX_SCALAR_EXPONENT,
        });
    }
    let mut result = K::one();
    let mut base = x.clone();
    while exponent > 0 {
        if exponent & 1 == 1 {
            result = result.mul(&base);
        }
        exponent >>= 1;
        if exponent > 0 {
            base = base.mul(&base);
        }
    }
    Ok(result)
}

/// Signed exact field power. Magnitude is checked before inversion, including
/// `i64::MIN`; an inverse-of-zero refusal differs from a resource refusal.
pub fn power<K: Field + ExactRing>(x: &K, exponent: i64) -> Result<K, ScalarError> {
    let magnitude = exponent.unsigned_abs();
    if magnitude > MAX_SCALAR_EXPONENT {
        return Err(ScalarError::Budget {
            what: "signed exponent",
            limit: MAX_SCALAR_EXPONENT,
        });
    }
    if exponent < 0 {
        power_unsigned(&inverse(x)?, magnitude)
    } else {
        power_unsigned(x, magnitude)
    }
}

pub fn inverse<K: Field + ExactRing>(x: &K) -> Result<K, ScalarError> {
    if x.is_zero() {
        return Err(ScalarError::ZeroInverse);
    }
    x.try_inv().ok_or(ScalarError::FieldContract)
}

pub fn divide<K: Field + ExactRing>(x: &K, y: &K) -> Result<K, ScalarError> {
    Ok(x.mul(&inverse(y)?))
}

pub fn from_i64<K: RationalEmbedding>(value: i64) -> K {
    K::from_rational(&crate::rational::Rational::from_integer(value.into()))
}

pub fn from_fraction<K: RationalEmbedding>(numerator: i64, denominator: i64) -> Option<K> {
    (denominator != 0).then(|| {
        K::from_rational(&crate::rational::Rational::new(
            numerator.into(),
            denominator.into(),
        ))
    })
}

/// Embed an integer polynomial into the specified characteristic-zero field,
/// then evaluate it with the canonical polynomial implementation.
pub fn evaluate_integer_polynomial<K: RationalEmbedding>(
    coefficients: &[num_bigint::BigInt],
    x: &K,
) -> Result<K, ScalarError> {
    if coefficients.len() > MAX_EMBEDDED_POLYNOMIAL_COEFFICIENTS {
        return Err(ScalarError::Budget {
            what: "embedded polynomial coefficients",
            limit: MAX_EMBEDDED_POLYNOMIAL_COEFFICIENTS as u64,
        });
    }
    Ok(crate::polynomial::Polynomial::from_coefficients(
        coefficients
            .iter()
            .map(|c| K::from_rational(&crate::rational::Rational::from_integer(c.clone())))
            .collect(),
    )
    .eval(x))
}

/// Exact semiring sum. A finite term budget also bounds infinite iterators.
pub fn sum_with_budget<'a, K: Semiring + 'a>(
    items: impl IntoIterator<Item = &'a K>,
    budget: usize,
) -> Result<K, ScalarError> {
    if budget > MAX_SCALAR_EXPONENT as usize {
        return Err(ScalarError::Budget {
            what: "sum term budget",
            limit: MAX_SCALAR_EXPONENT,
        });
    }
    let mut total = K::zero();
    for (count, value) in items.into_iter().enumerate() {
        if count >= budget {
            return Err(ScalarError::Budget {
                what: "sum terms",
                limit: budget as u64,
            });
        }
        total = total.add(value);
    }
    Ok(total)
}

// Origin: engine/crates_rs/core_number_theory/src/scalar.rs
// Claim: urn:core:crates_rs:core-number-theory:scalar:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod bounded_arithmetic_tests {
    use super::*;
    use crate::rational::{ri, rq};
    #[test]
    fn scalar_power_inverse_and_budget_refusals_are_distinct() {
        assert_eq!(power(&ri(2), -3).unwrap(), rq(1, 8));
        assert_eq!(power_unsigned(&ri(2), 16).unwrap(), ri(65536));
        assert_eq!(power(&ri(0), 0).unwrap(), ri(1));
        assert_eq!(power(&ri(0), -1), Err(ScalarError::ZeroInverse));
        assert!(matches!(
            power(&ri(1), i64::MIN),
            Err(ScalarError::Budget { .. })
        ));
        assert!(matches!(
            power(&ri(1), 1i64 << 32),
            Err(ScalarError::Budget { .. })
        ));
        assert!(matches!(
            power_unsigned(&ri(2), u64::MAX),
            Err(ScalarError::Budget { .. })
        ));
        assert_eq!(divide(&ri(3), &ri(2)).unwrap(), rq(3, 2));
        assert_eq!(divide(&ri(3), &ri(0)), Err(ScalarError::ZeroInverse));
    }
    #[test]
    fn embedded_polynomials_and_infinite_sums_use_canonical_bounded_math() {
        let i = GaussianRat::i();
        assert_eq!(
            evaluate_integer_polynomial(&[1.into(), 0.into(), 1.into()], &i).unwrap(),
            GaussianRat::zero()
        );
        assert!(matches!(
            evaluate_integer_polynomial(&vec![0.into(); 1025], &i),
            Err(ScalarError::Budget { .. })
        ));
        assert_eq!(
            from_fraction::<GaussianRat>(3, 2),
            Some(GaussianRat::from_rational(rq(3, 2)))
        );
        assert_eq!(from_fraction::<GaussianRat>(1, 0), None);
        let one = ri(1);
        assert!(matches!(
            sum_with_budget(std::iter::repeat(&one), 3),
            Err(ScalarError::Budget {
                what: "sum terms",
                ..
            })
        ));
        assert_eq!(sum_with_budget([&one, &one], 2).unwrap(), ri(2));
        assert_eq!(
            sum_with_budget(std::iter::empty::<&crate::rational::Rational>(), 0).unwrap(),
            ri(0)
        );
    }
}

impl RationalEmbedding for crate::rational::Rational {
    fn from_rational(value: &crate::rational::Rational) -> Self {
        value.clone()
    }
}

impl<const N: usize> RationalEmbedding for crate::cyclotomic_field::Cyclotomic<N> {
    fn from_rational(value: &crate::rational::Rational) -> Self {
        Self::rational(value.clone())
    }
}

impl<const D: i64> RationalEmbedding for crate::quadratic::Quadratic<D> {
    fn from_rational(value: &crate::rational::Rational) -> Self {
        Self::new(value.clone(), crate::rational::ri(0))
    }
}

macro_rules! exact_scalar {
    ($t:ty, |$x:ident| $inv:expr, |$q:ident| $embedding:expr) => {
        impl std::ops::Add for $t {
            type Output = $t;
            fn add(self, rhs: $t) -> $t {
                <$t>::add(&self, &rhs)
            }
        }
        impl<'a, 'b> std::ops::Add<&'b $t> for &'a $t {
            type Output = $t;
            fn add(self, rhs: &'b $t) -> $t {
                <$t>::add(self, rhs)
            }
        }
        impl std::ops::Sub for $t {
            type Output = $t;
            fn sub(self, rhs: $t) -> $t {
                <$t>::sub(&self, &rhs)
            }
        }
        impl<'a, 'b> std::ops::Sub<&'b $t> for &'a $t {
            type Output = $t;
            fn sub(self, rhs: &'b $t) -> $t {
                <$t>::sub(self, rhs)
            }
        }
        impl std::ops::Mul for $t {
            type Output = $t;
            fn mul(self, rhs: $t) -> $t {
                <$t>::mul(&self, &rhs)
            }
        }
        impl<'a, 'b> std::ops::Mul<&'b $t> for &'a $t {
            type Output = $t;
            fn mul(self, rhs: &'b $t) -> $t {
                <$t>::mul(self, rhs)
            }
        }
        impl std::ops::Neg for $t {
            type Output = $t;
            fn neg(self) -> $t {
                <$t>::zero().sub(&self)
            }
        }
        impl<'a> std::ops::Neg for &'a $t {
            type Output = $t;
            fn neg(self) -> $t {
                <$t>::zero().sub(self)
            }
        }
        impl num_traits::Zero for $t {
            fn zero() -> Self {
                <$t>::zero()
            }
            fn is_zero(&self) -> bool {
                self == &<$t>::zero()
            }
        }
        impl num_traits::One for $t {
            fn one() -> Self {
                <$t as RationalEmbedding>::from_rational(&crate::rational::ri(1))
            }
        }
        impl Semiring for $t {
            fn zero() -> Self {
                <$t>::zero()
            }
            fn one() -> Self {
                <$t as RationalEmbedding>::from_rational(&crate::rational::ri(1))
            }
            fn add(&self, rhs: &Self) -> Self {
                <$t>::add(self, rhs)
            }
            fn mul(&self, rhs: &Self) -> Self {
                <$t>::mul(self, rhs)
            }
            fn is_zero(&self) -> bool {
                self == &<$t>::zero()
            }
        }
        impl Ring for $t {
            fn neg(&self) -> Self {
                <$t>::zero().sub(self)
            }
        }
        impl Field for $t {
            fn try_inv(&self) -> Option<Self> {
                if self == &<$t>::zero() {
                    None
                } else {
                    let $x = self;
                    Some($inv)
                }
            }
        }
        impl ExactRing for $t {}
        impl RationalEmbedding for $t {
            fn from_rational($q: &crate::rational::Rational) -> Self {
                $embedding
            }
        }
        impl linear_algebra::exact_field::involution::Involution for $t {
            fn conjugate(&self) -> Self {
                <$t>::conj(self)
            }
        }
    };
}

exact_scalar!(GaussianRat, |x| x.inv(), |q| GaussianRat::from_rational(
    q.clone()
));
exact_scalar!(
    EisensteinRat,
    |x| x.inv(),
    |q| EisensteinRat::from_rational(q.clone())
);
exact_scalar!(Cyc5, |x| x.inv(), |q| Cyc5::rat(q.clone()));
exact_scalar!(Cyc8, |x| x.inv(), |q| Cyc8 {
    a: std::array::from_fn(|i| if i == 0 {
        q.clone()
    } else {
        crate::rational::ri(0)
    })
});
exact_scalar!(Cyc12, |x| x.inv(), |q| Cyc12 {
    a: std::array::from_fn(|i| if i == 0 {
        q.clone()
    } else {
        crate::rational::ri(0)
    })
});
exact_scalar!(Cyc24, |x| x.inv(), |q| Cyc24::rat(q.clone()));
exact_scalar!(Cyc28, |x| x.inv(), |q| Cyc28::rat(q.clone()));
exact_scalar!(Cyc44, |x| x.inv(), |q| Cyc44::rat(q.clone()));
exact_scalar!(Cyc52, |x| x.inv(), |q| Cyc52::rat(q.clone()));
exact_scalar!(Cyc120, |x| x.inv(), |q| Cyc120::rat(q.clone()));

impl linear_algebra::exact_field::ordered::HermitianOrdered for GaussianRat {
    fn fixed_field_sign(&self) -> Option<i8> {
        if self.im != crate::rational::r_zero() {
            return None;
        }
        Some(linear_algebra::exact_field::ordered::OrderedExactField::signum(&self.re))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rational::{ri, rq};
    use linear_algebra::backend::basic_matrix::BasicMatrix;

    /// Field axioms on a finite sample, through the `linear_algebra` trait tower only.
    fn check_field_axioms<F: Field + ExactRing>(samples: &[F]) {
        let zero = F::zero();
        let one = F::one();
        for a in samples {
            assert_eq!(a.add(&zero), *a, "additive identity");
            assert_eq!(a.mul(&one), *a, "multiplicative identity");
            assert!(a.add(&a.neg()).is_zero(), "additive inverse");
            assert_eq!(a.sub(a), zero, "a - a = 0");
            if !a.is_zero() {
                let inv = a.try_inv().expect("nonzero element is invertible");
                assert_eq!(a.mul(&inv), one, "a * a^-1 = 1");
                assert_eq!(a.try_div(a), Some(one.clone()), "a / a = 1");
            } else {
                assert!(a.try_inv().is_none(), "zero has no inverse");
            }
            for b in samples {
                assert_eq!(a.add(b), b.add(a), "commutative addition");
                assert_eq!(a.mul(b), b.mul(a), "commutative multiplication");
                for c in samples {
                    assert_eq!(a.add(b).add(c), a.add(&b.add(c)), "associative addition");
                    assert_eq!(
                        a.mul(b).mul(c),
                        a.mul(&b.mul(c)),
                        "associative multiplication"
                    );
                    assert_eq!(a.mul(&b.add(c)), a.mul(b).add(&a.mul(c)), "distributivity");
                }
            }
        }
    }

    #[test]
    fn gaussian_rationals_form_a_field() {
        let s = [
            GaussianRat::zero(),
            GaussianRat::one(),
            GaussianRat::i(),
            GaussianRat::from_ints(3, -4),
            GaussianRat {
                re: rq(1, 2),
                im: rq(-2, 3),
            },
        ];
        check_field_axioms(&s);
    }

    #[test]
    fn eisenstein_rationals_form_a_field() {
        let s = [
            EisensteinRat::zero(),
            EisensteinRat::one(),
            EisensteinRat::zeta3(),
            EisensteinRat::from_ints(2, -5),
        ];
        check_field_axioms(&s);
    }

    #[test]
    fn cyclotomic_fields_form_fields() {
        check_field_axioms(&[
            Cyc5::zero(),
            Cyc5::zeta5(1),
            Cyc5::zeta5(2).add(&Cyc5::one()),
        ]);
        check_field_axioms(&[
            Cyc8::zero(),
            Cyc8::zeta8(1),
            Cyc8::sqrt2(),
            Cyc8::zeta8(3).add(&Cyc8::one()),
        ]);
        check_field_axioms(&[
            Cyc12::zero(),
            Cyc12::zeta12(1),
            Cyc12::zeta12(5).add(&Cyc12::one()),
        ]);
        check_field_axioms(&[
            Cyc24::zero(),
            Cyc24::zeta24(1),
            Cyc24::sqrt2().add(&Cyc24::sqrt3()),
        ]);
    }

    #[test]
    fn large_conductor_fields_invert_through_the_shared_solver() {
        let z28 = Cyc28::zeta(1).add(&Cyc28::rat(ri(2)));
        assert_eq!(z28.mul(&z28.try_inv().unwrap()), <Cyc28 as Semiring>::one());
        let z120 = Cyc120::zeta(7).sub(&Cyc120::rat(ri(3)));
        assert_eq!(
            z120.mul(&z120.try_inv().unwrap()),
            <Cyc120 as Semiring>::one()
        );
    }

    #[test]
    fn operators_agree_with_the_inherent_methods() {
        let a = Cyc24::zeta24(5);
        let b = Cyc24::sqrt2();
        assert_eq!(a.clone() + b.clone(), a.add(&b));
        assert_eq!(&a * &b, a.mul(&b));
        assert_eq!(-a.clone(), a.neg());
        assert_eq!(a.clone() - b.clone(), a.sub(&b));
    }

    #[test]
    fn cyclotomic_matrices_use_the_linear_algebra_matrix_type() {
        // The Hadamard-like matrix [[1, 1], [1, -1]] / sqrt2 over Q(zeta_8) squares to 1.
        let s = Cyc8::sqrt2().inv();
        let one = Cyc8::one();
        let m =
            BasicMatrix::from_row_major(2, 2, vec![&s * &one, &s * &one, &s * &one, -(&s * &one)])
                .unwrap();
        let sq = m.mul(&m).unwrap();
        assert_eq!(sq.get(0, 0).unwrap(), Cyc8::one());
        assert_eq!(sq.get(1, 1).unwrap(), Cyc8::one());
        assert_eq!(sq.get(0, 1).unwrap(), Cyc8::zero());
        assert_eq!(sq.get(1, 0).unwrap(), Cyc8::zero());
    }
}
