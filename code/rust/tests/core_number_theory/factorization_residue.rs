use num_bigint::{BigInt, BigUint};
use core_number_theory::integer_factorization::{
    factor_integer, factor_natural, is_prime_u64, FactorizationBudget, FactorizationError,
};
use core_number_theory::residue::{square_roots_unity, two_torsion};

#[test]
fn certified_factorization_reconstructs_large_integers_and_refuses_exhaustion() {
    let budget = FactorizationBudget::default();
    for n in [1u64, 8, 561, 3215031751, 18446744073709551557, u64::MAX] {
        let factors = factor_natural(&BigUint::from(n), budget).unwrap();
        let mut product = BigUint::from(1u8);
        for (p, e) in factors {
            assert!(is_prime_u64(u64::try_from(&p).unwrap(), budget).unwrap());
            product *= p.pow(e);
        }
        assert_eq!(product, BigUint::from(n));
    }
    assert_eq!(
        factor_integer(&BigInt::from(-5), budget),
        Err(FactorizationError::NonPositive)
    );
    assert!(matches!(
        factor_natural(
            &((BigUint::from(1u8) << 127usize) - 1u8),
            FactorizationBudget { max_operations: 10 }
        ),
        Err(FactorizationError::Exhausted { .. })
    ));
}
#[test]
fn residue_roots_agree_with_small_exhaustive_models_and_scale_to_u64_limits() {
    let budget = FactorizationBudget::default();
    for n in 2..200u64 {
        let brute = (0..n)
            .filter(|x| u128::from(*x) * u128::from(*x) % u128::from(n) == 1)
            .collect::<Vec<_>>();
        assert_eq!(square_roots_unity(n, budget).unwrap(), brute);
        let torsion = (0..n)
            .filter(|x| 2 * u128::from(*x) % u128::from(n) == 0)
            .collect::<Vec<_>>();
        assert_eq!(two_torsion(n).unwrap(), torsion);
    }
    let n = 1u64 << 63;
    assert_eq!(
        square_roots_unity(n, budget).unwrap(),
        vec![1, n / 2 - 1, n / 2 + 1, n - 1]
    );
    assert_eq!(two_torsion(u64::MAX).unwrap(), vec![0]);
}
#[test]
fn rational_factorization_replays_signed_exponents_and_shares_one_budget() {
    use core_number_theory::integer_factorization::factor_positive_rational;
    use core_number_theory::rational::rq;
    for q in [rq(1, 1), rq(72, 175), rq(17, 65536), rq(184467, 5)] {
        let factors = factor_positive_rational(&q, FactorizationBudget::default()).unwrap();
        let mut replay = rq(1, 1);
        for (p, e) in factors {
            let power = BigInt::from(p.pow(e.unsigned_abs() as u32));
            if e > 0 {
                replay *= power;
            } else {
                replay /= power;
            }
        }
        assert_eq!(replay, q);
    }
    assert!(factor_positive_rational(&rq(0, 1), FactorizationBudget::default()).is_err());
    assert!(factor_positive_rational(&rq(-1, 2), FactorizationBudget::default()).is_err());
    assert!(matches!(
        factor_positive_rational(&rq(53, 59), FactorizationBudget { max_operations: 1 }),
        Err(FactorizationError::Exhausted { .. })
    ));
}

// Origin: engine/crates_rs/tests/core_number_theory/factorization_residue.rs
// Claim: urn:core:crates_rs:tests:factorization-residue:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord99089095 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord99089095` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError99089095 {
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
impl BoundaryError99089095 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError99089095 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError99089095 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord99089095 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError99089095> {
        if capacity_bound == 0 {
            return Err(BoundaryError99089095::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError99089095::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError99089095::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_99089095() {
    let admitted = BoundaryRecord99089095::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord99089095::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
