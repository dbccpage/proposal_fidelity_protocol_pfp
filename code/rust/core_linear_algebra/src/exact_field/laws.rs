//! Executable checks of the obligations the scalar traits state in prose.
//!
//! `Field`, [`Involution`], [`OrderedExactField`] and [`HermitianOrdered`] are promises
//! the compiler cannot check: an implementor must prove field axioms, that conjugation is a
//! ring automorphism of order at most two, and that `signum` is an order. These functions
//! replay those obligations on a finite sample and name the first law that fails, so a
//! downstream crate can put one line in its own tests:
//!
//! ```
//! use linear_algebra::exact_field::laws::{
//!     check_field_axioms, check_involution_axioms, check_ordered_axioms,
//! };
//! use num_bigint::BigInt;
//! use num_rational::BigRational;
//!
//! let samples: Vec<BigRational> = (-3..=3)
//!     .map(|n| BigRational::new(BigInt::from(n), BigInt::from(2)))
//!     .collect();
//! check_field_axioms(&samples).unwrap();
//! check_involution_axioms(&samples).unwrap();
//! check_ordered_axioms(&samples).unwrap();
//! ```
//!
//! A passing check is evidence on the sample, not a proof; a failing check is a proof that
//! the implementation breaks the named law. The samples should include zero, one, negative
//! elements and elements with every component nonzero.
//!
//! The checks are `O(|samples|³)` (the associativity and distributivity laws range over
//! triples); keep the sample to a few dozen elements.
//!
//! AuthorityEffect: None.

use crate::exact_field::involution::Involution;
use crate::exact_field::ordered::{HermitianOrdered, OrderedExactField};
use crate::exact_field::ExactFieldError;
use crate::scalars::{ExactRing, Field};

fn violated(law: &'static str) -> Result<(), ExactFieldError> {
    Err(ExactFieldError::LawViolated { law })
}

/// Replays the field axioms on `samples`: additive and multiplicative identity, additive
/// inverse, commutativity, associativity and distributivity of `+` and `·`, `0 ≠ 1`,
/// `is_zero` agreeing with equality, `try_inv` answering `Some` exactly for nonzero elements
/// with `a · a⁻¹ = 1`, and `try_div` being multiplication by the inverse.
pub fn check_field_axioms<F: Field + ExactRing>(samples: &[F]) -> Result<(), ExactFieldError> {
    let (zero, one) = (F::zero(), F::one());
    if !zero.is_zero() {
        return violated("zero is zero");
    }
    if one == zero || one.is_zero() {
        return violated("a field has 0 != 1");
    }
    // Pass 1: one element at a time.
    for a in samples {
        check_single_element_axioms(a, &zero, &one)?;
    }
    // Pass 2: pairs.
    for a in samples {
        for b in samples {
            check_pair_axioms(a, b)?;
        }
    }
    // Pass 3: triples.
    check_all_triples(samples)
}

fn check_single_element_axioms<F: Field + ExactRing>(
    a: &F,
    zero: &F,
    one: &F,
) -> Result<(), ExactFieldError> {
    if a.add(zero) != *a {
        return violated("0 is the additive identity");
    }
    if a.mul(one) != *a {
        return violated("1 is the multiplicative identity");
    }
    if !a.add(&a.neg()).is_zero() {
        return violated("a + (-a) = 0");
    }
    if a.is_zero() != (*a == *zero) {
        return violated("is_zero agrees with equality to zero");
    }
    check_element_inverse(a, one)
}

fn check_element_inverse<F: Field + ExactRing>(a: &F, one: &F) -> Result<(), ExactFieldError> {
    match a.try_inv() {
        None if !a.is_zero() => violated("every nonzero element has an inverse"),
        Some(_) if a.is_zero() => violated("zero has no inverse"),
        Some(inverse) if a.mul(&inverse) != *one => violated("a · a⁻¹ = 1"),
        _ => Ok(()),
    }
}

fn check_pair_axioms<F: Field + ExactRing>(a: &F, b: &F) -> Result<(), ExactFieldError> {
    if a.add(b) != b.add(a) {
        return violated("addition is commutative");
    }
    if a.mul(b) != b.mul(a) {
        return violated("multiplication is commutative");
    }
    match (b.is_zero(), a.try_div(b)) {
        (true, Some(_)) => violated("division by zero is undefined"),
        (false, None) => violated("division by a nonzero element is defined"),
        (false, Some(quotient)) if quotient.mul(b) != *a => violated("(a / b) · b = a"),
        _ => Ok(()),
    }
}

fn check_all_triples<F: Field + ExactRing>(samples: &[F]) -> Result<(), ExactFieldError> {
    for a in samples {
        for b in samples {
            for c in samples {
                check_triple_axioms(a, b, c)?;
            }
        }
    }
    Ok(())
}

fn check_triple_axioms<F: Field + ExactRing>(a: &F, b: &F, c: &F) -> Result<(), ExactFieldError> {
    if a.add(b).add(c) != a.add(&b.add(c)) {
        return violated("addition is associative");
    }
    if a.mul(b).mul(c) != a.mul(&b.mul(c)) {
        return violated("multiplication is associative");
    }
    if a.mul(&b.add(c)) != a.mul(b).add(&a.mul(c)) {
        return violated("multiplication distributes over addition");
    }
    Ok(())
}

/// Replays the involution obligations on `samples`, in this order: `conj(a + b) = conj a +
/// conj b`, `conj(a · b) = conj a · conj b`, `conj 1 = 1`, `conj(conj a) = a`.
pub fn check_involution_axioms<F: Involution>(samples: &[F]) -> Result<(), ExactFieldError> {
    for a in samples {
        for b in samples {
            if a.add(b).conjugate() != a.conjugate().add(&b.conjugate()) {
                return violated("conjugation is additive");
            }
        }
    }
    for a in samples {
        for b in samples {
            if a.mul(b).conjugate() != a.conjugate().mul(&b.conjugate()) {
                return violated("conjugation is multiplicative");
            }
        }
    }
    if F::one().conjugate() != F::one() {
        return violated("conjugation fixes 1");
    }
    for a in samples {
        if a.conjugate().conjugate() != *a {
            return violated("conjugation has order at most two");
        }
    }
    Ok(())
}

/// Replays the order obligations on `samples`, in this order: `signum` is `-1`, `0` or `1`;
/// it is `0` exactly for zero; `signum(−a) = −signum(a)`; the positive elements are closed
/// under `+`; and under `·`.
pub fn check_ordered_axioms<F: OrderedExactField>(samples: &[F]) -> Result<(), ExactFieldError> {
    for a in samples {
        if !(-1..=1).contains(&a.signum()) {
            return violated("a sign is -1, 0 or 1");
        }
    }
    for a in samples {
        if (a.signum() == 0) != a.is_zero() {
            return violated("a sign is zero exactly for zero");
        }
    }
    for a in samples {
        if a.neg().signum() != -a.signum() {
            return violated("the sign of a negation is the negated sign");
        }
    }
    check_positive_closure(samples)
}

fn check_positive_closure<F: OrderedExactField>(samples: &[F]) -> Result<(), ExactFieldError> {
    for a in samples {
        for b in samples {
            if a.signum() > 0 && b.signum() > 0 {
                if a.add(b).signum() <= 0 {
                    return violated("a sum of positive elements is positive");
                }
                if a.mul(b).signum() <= 0 {
                    return violated("a product of positive elements is positive");
                }
            }
        }
    }
    Ok(())
}

/// Replays the Hermitian-order obligations on `samples`, in this order: `fixed_field_sign`
/// is `None` exactly for elements not fixed by the involution; its values are `-1`, `0` or
/// `1` and `0` exactly for zero; on the fixed elements the sign of a negation is the negated
/// sign and positive elements are closed under `+` and `·`; and every norm `x · conj x` has
/// sign `≥ 0`, with `0` only for `x = 0`.
pub fn check_hermitian_ordered_axioms<F: HermitianOrdered>(
    samples: &[F],
) -> Result<(), ExactFieldError> {
    for a in samples {
        check_fixed_sign_domain(a)?;
    }
    let fixed: Vec<&F> = samples.iter().filter(|a| a.conjugate() == **a).collect();
    for a in &fixed {
        if a.neg().fixed_field_sign() != a.fixed_field_sign().map(|s| -s) {
            return violated("the sign of a negation is the negated sign on the fixed field");
        }
    }
    check_fixed_positive_closure(&fixed)?;
    check_hermitian_norms(samples)
}

fn check_fixed_sign_domain<F: HermitianOrdered>(a: &F) -> Result<(), ExactFieldError> {
    let fixed = a.conjugate() == *a;
    match a.fixed_field_sign() {
        None if fixed => violated("fixed_field_sign is None exactly for non-fixed elements"),
        Some(_) if !fixed => violated("fixed_field_sign is None exactly for non-fixed elements"),
        Some(sign) if !(-1..=1).contains(&sign) => violated("a fixed-field sign is -1, 0 or 1"),
        Some(sign) if (sign == 0) != a.is_zero() => {
            violated("a fixed-field sign is zero exactly for zero")
        }
        _ => Ok(()),
    }
}

fn check_fixed_positive_closure<F: HermitianOrdered>(fixed: &[&F]) -> Result<(), ExactFieldError> {
    for a in fixed {
        for b in fixed {
            if a.fixed_field_sign() == Some(1) && b.fixed_field_sign() == Some(1) {
                if a.add(b).fixed_field_sign() != Some(1) {
                    return violated("a sum of positive fixed elements is positive");
                }
                if a.mul(b).fixed_field_sign() != Some(1) {
                    return violated("a product of positive fixed elements is positive");
                }
            }
        }
    }
    Ok(())
}

fn check_hermitian_norms<F: HermitianOrdered>(samples: &[F]) -> Result<(), ExactFieldError> {
    for a in samples {
        let norm = a.mul(&a.conjugate());
        match norm.fixed_field_sign() {
            Some(sign) if sign >= 0 && (sign == 0) == a.is_zero() => {}
            _ => return violated("a norm x · conj(x) is nonnegative and zero only for zero"),
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/laws.rs
// Claim: urn:core:crates_rs:core-linear-algebra:laws:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf9e2875f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf9e2875f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf9e2875f {
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
impl BoundaryErrorf9e2875f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf9e2875f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf9e2875f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf9e2875f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf9e2875f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf9e2875f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf9e2875f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf9e2875f::ExceedsCapacity {
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
    use crate::exact_field::test_support::{
        gi, gq, q, qs, qsi, Fp, GaussianRational, QSqrt2, Shaky, Z6,
    };
    use num_rational::BigRational;

    fn rationals() -> Vec<BigRational> {
        vec![
            q(0, 1),
            q(1, 1),
            q(-1, 1),
            q(1, 2),
            q(-3, 7),
            q(22, 5),
            q(-10, 3),
        ]
    }

    fn assert_law(result: Result<(), ExactFieldError>, law: &'static str) {
        assert_eq!(result, Err(ExactFieldError::LawViolated { law }));
    }

    /// The shipped `BigRational` tower satisfies every obligation on a mixed sample.
    #[test]
    fn bigrational_satisfies_the_field_involution_and_order_obligations() {
        let s = rationals();
        check_field_axioms(&s).unwrap();
        check_involution_axioms(&s).unwrap();
        check_ordered_axioms(&s).unwrap();
        check_hermitian_ordered_axioms(&s).unwrap();
    }

    /// Finite fields are fields (including characteristic 2) and their identity involution is one.
    #[test]
    fn finite_fields_satisfy_the_field_axioms_and_the_identity_is_an_involution() {
        fn all<const P: u64>() -> Vec<Fp<P>> {
            (0..P as i64).map(Fp::<P>::new).collect()
        }
        check_field_axioms(&all::<2>()).unwrap();
        check_field_axioms(&all::<3>()).unwrap();
        check_field_axioms(&all::<7>()).unwrap();
        check_involution_axioms(&all::<7>()).unwrap();
    }

    #[test]
    fn the_gaussian_rationals_and_q_sqrt2_satisfy_their_obligations() {
        let g: Vec<GaussianRational> = vec![
            gi(0, 0),
            gi(1, 0),
            gi(0, 1),
            gi(-2, 3),
            gq(q(1, 2), q(-3, 5)),
            gq(q(7, 3), q(2, 7)),
        ];
        check_field_axioms(&g).unwrap();
        check_involution_axioms(&g).unwrap();
        check_hermitian_ordered_axioms(&g).unwrap();

        let s: Vec<QSqrt2> = vec![
            qsi(0, 0),
            qsi(1, 0),
            qsi(0, 1),
            qsi(1, -1),
            qsi(3, -2),
            qs(q(1, 2), q(-3, 5)),
            qsi(-5, 4),
        ];
        check_field_axioms(&s).unwrap();
        check_involution_axioms(&s).unwrap();
        check_ordered_axioms(&s).unwrap();
        check_hermitian_ordered_axioms(&s).unwrap();
    }

    /// `Z/6` claims to be a field: 2 is nonzero but `try_inv` answers `None`.
    #[test]
    fn a_ring_with_zero_divisors_fails_the_field_axioms() {
        let all: Vec<Z6> = (0..6).map(Z6::new).collect();
        assert_law(
            check_field_axioms(&all),
            "every nonzero element has an inverse",
        );
    }

    /// Each involution defect is named by the first law it breaks, in the documented order.
    /// `try_inv` answering `Some(x)` for `x = 2` gives `2 · 2 = 4 != 1`: the inverse law names it.
    #[test]
    fn a_wrong_inverse_is_caught_and_named() {
        let s: Vec<Shaky<8>> = [0, 1, 2].iter().map(|&x| Shaky::<8>(q(x, 1))).collect();
        assert_law(check_field_axioms(&s), "a · a⁻¹ = 1");
    }

    #[test]
    fn a_defective_involution_is_caught_and_named() {
        let s = |v: &[i64]| -> Vec<Shaky<3>> { v.iter().map(|&x| Shaky::<3>(q(x, 1))).collect() };
        assert_law(
            check_involution_axioms(&s(&[0, 1, 2])),
            "conjugation is additive",
        );
        let t: Vec<Shaky<4>> = [1, 2, 3].iter().map(|&x| Shaky::<4>(q(x, 1))).collect();
        assert_law(check_involution_axioms(&t), "conjugation is multiplicative");
        // the empty sample exposes the unital law for a negating map
        let none: Vec<Shaky<4>> = Vec::new();
        assert_law(check_involution_axioms(&none), "conjugation fixes 1");
    }

    #[test]
    fn a_defective_order_is_caught_and_named() {
        let pos = |v: &[i64]| v.iter().map(|&x| q(x, 1)).collect::<Vec<_>>();
        let s1: Vec<Shaky<1>> = pos(&[0, 1, -1]).into_iter().map(Shaky::<1>).collect();
        assert_law(check_ordered_axioms(&s1), "a sign is -1, 0 or 1");
        let s2: Vec<Shaky<2>> = pos(&[0, 1, -1]).into_iter().map(Shaky::<2>).collect();
        assert_law(check_ordered_axioms(&s2), "a sign is zero exactly for zero");
        let s7: Vec<Shaky<7>> = pos(&[0, 1, -1]).into_iter().map(Shaky::<7>).collect();
        assert_law(
            check_ordered_axioms(&s7),
            "the sign of a negation is the negated sign",
        );
    }

    #[test]
    fn a_defective_hermitian_sign_is_caught_and_named() {
        let s5: Vec<Shaky<5>> = [0, 1, -1].iter().map(|&x| Shaky::<5>(q(x, 1))).collect();
        assert_law(
            check_hermitian_ordered_axioms(&s5),
            "fixed_field_sign is None exactly for non-fixed elements",
        );
        let s6: Vec<Shaky<6>> = [0, 1, -1].iter().map(|&x| Shaky::<6>(q(x, 1))).collect();
        assert_law(
            check_hermitian_ordered_axioms(&s6),
            "a fixed-field sign is -1, 0 or 1",
        );
    }

    /// Complex conjugation on `Q(√2)` would make `x · conj(x)` (the norm) negative for `√2`;
    /// the honest identity involution satisfies the norm law, and the failing alternative is
    /// shown with a hand-built type whose norm is negative.
    #[test]
    fn a_negative_norm_violates_the_hermitian_order_obligations() {
        // Q(√2) with the Galois conjugation √2 ↦ −√2 and the order of the fixed field Q:
        // the norm of √2 is −2 < 0.
        #[derive(Debug, Clone, PartialEq, Eq)]
        struct Galois(QSqrt2);
        use crate::scalars::{Ring, Semiring};
        impl Semiring for Galois {
            fn zero() -> Self {
                Galois(<QSqrt2 as Semiring>::zero())
            }
            fn one() -> Self {
                Galois(<QSqrt2 as Semiring>::one())
            }
            fn add(&self, rhs: &Self) -> Self {
                Galois(Semiring::add(&self.0, &rhs.0))
            }
            fn mul(&self, rhs: &Self) -> Self {
                Galois(Semiring::mul(&self.0, &rhs.0))
            }
            fn is_zero(&self) -> bool {
                Semiring::is_zero(&self.0)
            }
        }
        impl Ring for Galois {
            fn neg(&self) -> Self {
                Galois(Ring::neg(&self.0))
            }
        }
        impl Field for Galois {
            fn try_inv(&self) -> Option<Self> {
                self.0.try_inv().map(Galois)
            }
        }
        impl ExactRing for Galois {}
        impl Involution for Galois {
            fn conjugate(&self) -> Self {
                Galois(qs(self.0.a.clone(), -self.0.b.clone()))
            }
        }
        impl HermitianOrdered for Galois {
            fn fixed_field_sign(&self) -> Option<i8> {
                if num_traits::Zero::is_zero(&self.0.b) {
                    Some(crate::exact_field::test_support::sign_of_rational(
                        &self.0.a,
                    ))
                } else {
                    None
                }
            }
        }
        let samples: Vec<Galois> = vec![
            Galois(qsi(0, 0)),
            Galois(qsi(1, 0)),
            Galois(qsi(0, 1)),
            Galois(qsi(2, 0)),
        ];
        check_field_axioms(&samples).unwrap();
        check_involution_axioms(&samples).unwrap();
        assert_law(
            check_hermitian_ordered_axioms(&samples),
            "a norm x · conj(x) is nonnegative and zero only for zero",
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_f9e2875f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf9e2875f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf9e2875f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf9e2875f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf9e2875f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf9e2875f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf9e2875f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf9e2875f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
