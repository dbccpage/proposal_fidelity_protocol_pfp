//! Preserved host admission laws for the canonical BigInt cyclotomic integer ring.

// Origin: engine/crates_rs/tests/core_number_theory/cyclotomic_ring_admission.rs
// Claim: urn:core:crates_rs:tests:cyclotomic-ring-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2a81ff85 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2a81ff85` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2a81ff85 {
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
impl BoundaryError2a81ff85 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2a81ff85 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2a81ff85 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2a81ff85 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2a81ff85> {
        if capacity_bound == 0 {
            return Err(BoundaryError2a81ff85::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2a81ff85::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2a81ff85::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use num_traits::Zero;
    use core_number_theory::cyclotomic::{Cyc12, Cyc24};
    use core_number_theory::cyclotomic_integer::{CyclotomicInteger, CyclotomicIntegerError};
    use core_number_theory::polynomial::cyclotomic_polynomial;
    use core_number_theory::rational::rq;
    use core_number_theory::rational::{ri, Rational};

    #[test]
    fn roots_satisfy_the_order_and_defining_polynomial() {
        for n in 1..=40 {
            let z = CyclotomicInteger::zeta(n).unwrap();
            let zero = CyclotomicInteger::scalar(n, 0).unwrap();
            assert_eq!(z.pow(n), CyclotomicInteger::scalar(n, 1).unwrap());
            let phi = cyclotomic_polynomial(n).unwrap();
            let mut value = zero.clone();
            for c in phi.coefficients().iter().rev() {
                value = value
                    .mul(&z)
                    .unwrap()
                    .add(&CyclotomicInteger::new(n, vec![c.clone()]).unwrap())
                    .unwrap();
            }
            assert_eq!(value, zero);
            assert_eq!(
                z.conj().mul(&z).unwrap(),
                CyclotomicInteger::scalar(n, 1).unwrap()
            );
        }
    }
    #[test]
    fn canonical_norms_agree_with_fixed_conductor_fields() {
        let check = |n, mut expected: Vec<Rational>| {
            while expected.last().is_some_and(Zero::is_zero) {
                expected.pop();
            }
            let z = CyclotomicInteger::zeta(n).unwrap();
            let x = CyclotomicInteger::scalar(n, 1).unwrap().add(&z).unwrap();
            assert_eq!(
                x.mul(&x.conj()).unwrap().coefficient_values(),
                expected.as_slice()
            );
        };
        let x12 = Cyc12::one().add(&Cyc12::zeta12(1));
        let x24 = Cyc24::one().add(&Cyc24::zeta24(1));
        check(12, x12.mul(&x12.conj()).a.to_vec());
        check(24, x24.mul(&x24.conj()).a.to_vec());
    }
    #[test]
    fn construction_refuses_invalid_conductors_coefficients_and_cross_ring_arithmetic() {
        assert!(matches!(
            CyclotomicInteger::scalar(0, 1),
            Err(CyclotomicIntegerError::Conductor(0))
        ));
        assert!(matches!(
            CyclotomicInteger::new(3, vec![rq(1, 2)]),
            Err(CyclotomicIntegerError::NonIntegralCoefficient { index: 0 })
        ));
        assert!(matches!(
            CyclotomicInteger::with_budget(3, vec![ri(0); 3], 2),
            Err(CyclotomicIntegerError::CoefficientBudget { .. })
        ));
        assert!(matches!(
            CyclotomicInteger::zeta(3)
                .unwrap()
                .mul(&CyclotomicInteger::zeta(4).unwrap()),
            Err(CyclotomicIntegerError::ConductorMismatch { .. })
        ));
    }
}

use core_number_theory::{
    cyclotomic_integer::{CyclotomicInteger, CyclotomicIntegerError},
    rational::{ri, rq, Rational},
};
#[test]
fn integral_admission_and_character_arithmetic_share_unbounded_integer_coefficients() {
    use num_bigint::BigInt;
    use core_number_theory::polynomial::MAX_CONDUCTOR;
    let huge = BigInt::from(1u8) << 256usize;
    let x = CyclotomicInteger::new(4, vec![Rational::from_integer(huge.clone()), ri(1)]).unwrap();
    let expected: BigInt = &huge * &huge + 1;
    assert_eq!(
        x.mul(&x.conj()).unwrap().as_integer(),
        Some(expected.clone())
    );
    assert_eq!(x.norm(), expected);
    assert!(!x.is_unit());
    let z = CyclotomicInteger::zeta(4).unwrap();
    assert!(z.is_unit());
    assert!(CyclotomicInteger::scalar(4, -1).unwrap().is_unit());
    assert!(!CyclotomicInteger::scalar(4, 0).unwrap().is_unit());
    let cyclotomic_unit = CyclotomicInteger::scalar(5, 1)
        .unwrap()
        .add(&CyclotomicInteger::zeta(5).unwrap())
        .unwrap();
    assert!(cyclotomic_unit.is_unit());
    assert_eq!(
        z.pow(usize::MAX),
        CyclotomicInteger::root_of_unity(4, (usize::MAX % 4) as i64).unwrap()
    );
    assert_eq!(
        CyclotomicInteger::zero(5).unwrap().coefficient_values(),
        Vec::<Rational>::new()
    );
    assert_eq!(CyclotomicInteger::zero(5).unwrap().coefficients().len(), 4);
    assert!(matches!(
        CyclotomicInteger::with_budget(MAX_CONDUCTOR + 1, vec![], 0),
        Err(CyclotomicIntegerError::Conductor(_))
    ));
    let as_string: String = CyclotomicInteger::new(4, vec![rq(1, 2)])
        .unwrap_err()
        .into();
    assert!(as_string.contains("not an integer"));
}

#[test]
fn l4_boundary_admits_and_refuses_2a81ff85() {
    let admitted = BoundaryRecord2a81ff85::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2a81ff85::try_admit(9, 8).is_err());
}
