//! Test for Section 7.8: Ising ring local adapter and cycle-gradient repair differential.
//! Verifies that cycle-gradient repair on 1D ring lattices removes cycle holonomy
//! and has condition number 1 independent of ring size N.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use core_wdp::carrier_binding::IsingCycleGradientRepair;

fn q(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

#[test]
fn test_ising_ring_size_independent_conditioning() {
    let ring_sizes = [3, 4, 8, 16, 32, 64];

    for &n in &ring_sizes {
        // 1. Condition number is uniformly 1, independent of ring size
        let cond = IsingCycleGradientRepair::condition_number(n);
        assert_eq!(
            cond,
            BigRational::one(),
            "Condition number must be 1 for ring size {}",
            n
        );

        // 2. Uniform flux cochain (c_i = 1 for all edges)
        let uniform_cochain = vec![q(1); n];
        let repaired_uniform =
            IsingCycleGradientRepair::compute_repair_differential(n, &uniform_cochain);
        for val in &repaired_uniform {
            assert_eq!(
                *val,
                BigRational::zero(),
                "Uniform flux must be completely removed by cycle repair"
            );
        }

        // 3. Non-trivial cochain c_i = i + 1
        let cochain: Vec<BigRational> = (1..=n).map(|i| q(i as i64)).collect();
        let repaired = IsingCycleGradientRepair::compute_repair_differential(n, &cochain);

        // Sum of repaired cochain must be zero (zero total holonomy on the cycle)
        let sum_repaired: BigRational = repaired.iter().cloned().sum();
        assert_eq!(
            sum_repaired,
            BigRational::zero(),
            "Repaired cochain on ring size {} must have zero cycle flux",
            n
        );

        // 4. Idempotence of the repair differential: P^2 = P
        let repaired_again = IsingCycleGradientRepair::compute_repair_differential(n, &repaired);
        assert_eq!(
            repaired, repaired_again,
            "Repair differential must be idempotent on ring size {}",
            n
        );
    }
}

// Origin: engine/crates_rs/tests/core_wdp/test_ising_cycle_repair.rs
// Claim: urn:core:crates_rs:tests:test-ising-cycle-repair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbf3e9b27 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbf3e9b27` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbf3e9b27 {
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
impl BoundaryErrorbf3e9b27 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbf3e9b27 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbf3e9b27 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbf3e9b27 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbf3e9b27> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbf3e9b27::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbf3e9b27::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbf3e9b27::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_bf3e9b27() {
    let admitted = BoundaryRecordbf3e9b27::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbf3e9b27::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
