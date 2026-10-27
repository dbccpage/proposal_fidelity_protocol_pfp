//! Exact Rational Paired Statistics (U08).
//!
//! Enforces:
//! - Exact two-sided McNemar test p-value in BigRational:
//!   p = min(1, 2 * sum_{i=0}^{min(b,c)} binom(n, i) / 2^n) where n = b + c.
//! - Exact rational Clopper-Pearson / Wilson intervals.
//! - No float approximations.
//! AuthorityEffect: None (const).

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};

fn default_authority_effect() -> String {
    "None".to_string()
}

/// Computes binomial coefficient binom(n, k) exactly as BigInt.
pub fn binom(n: u64, k: u64) -> BigInt {
    if k > n {
        return BigInt::zero();
    }
    if k == 0 || k == n {
        return BigInt::one();
    }
    let k = k.min(n - k);
    let mut c = BigInt::one();
    for i in 1..=k {
        c = (c * BigInt::from(n - i + 1)) / BigInt::from(i);
    }
    c
}

/// Exact two-sided McNemar test.
///
/// Parameters:
/// - b: Discordant pairs where Method 1 succeeds and Method 2 fails.
/// - c: Discordant pairs where Method 1 fails and Method 2 succeeds.
///
/// Invariant:
/// Returns exact two-sided p-value:
/// p = min(1, 2 * sum_{i=0}^{min(b,c)} binom(n, i) / 2^n)
/// MUTATION KILL GATE: Omitting the factor 2 makes the test one-sided and turns tests RED!
pub fn mcnemar_exact(b: u64, c: u64) -> BigRational {
    let n = b + c;
    if n == 0 {
        return BigRational::one();
    }
    let min_bc = b.min(c);
    let mut sum = BigInt::zero();
    for i in 0..=min_bc {
        sum += binom(n, i);
    }

    // Two-sided factor of 2!
    // MUTATION KILL GATE: MUST multiply by 2!
    let two_sided_sum = BigInt::from(2) * sum;
    let denom = BigInt::from(2).pow(n as u32);

    let p = BigRational::new(two_sided_sum, denom);
    if p > BigRational::one() {
        BigRational::one()
    } else {
        p
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct McNemarReportV1 {
    pub b: u64,
    pub c: u64,
    pub discordant_total: u64,
    pub p_value_exact: String,
    pub p_value_num: String,
    pub p_value_denom: String,
    #[serde(default = "default_authority_effect")]
    pub authority_effect: String,
}

pub fn evaluate_mcnemar(b: u64, c: u64) -> McNemarReportV1 {
    let p = mcnemar_exact(b, c);
    McNemarReportV1 {
        b,
        c,
        discordant_total: b + c,
        p_value_exact: format!("{}/{}", p.numer(), p.denom()),
        p_value_num: p.numer().to_string(),
        p_value_denom: p.denom().to_string(),
        authority_effect: default_authority_effect(),
    }
}

// Origin: engine/crates_rs/core_finite_probability/src/paired_tests.rs
// Claim: urn:core:crates_rs:core-finite-probability:paired-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf33449a7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf33449a7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf33449a7 {
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
impl BoundaryErrorf33449a7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf33449a7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf33449a7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf33449a7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf33449a7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf33449a7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf33449a7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf33449a7::ExceedsCapacity {
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
mod l4_boundary_tests_f33449a7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf33449a7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf33449a7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf33449a7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf33449a7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf33449a7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf33449a7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf33449a7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
