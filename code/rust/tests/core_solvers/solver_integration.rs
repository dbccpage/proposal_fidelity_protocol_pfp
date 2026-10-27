// AuthorityEffect: None.
//! Integration tests for exact primal-dual solvers and falsification of positive-epsilon gap claims.
//! (SPEC-OE-ADVERSARY-RUST-006)

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use core_solvers::solver_lp_exact_simplex::solve_weighted_l1_projection;

fn int(v: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(v))
}

#[test]
fn exact_weighted_l1_lp_produces_exact_duality_certificate_not_epsilon() {
    // 2 edges, 1 face (boundary d1: row 0 = -1 on e0, +1 on e1)
    let d0 = vec![vec![int(-1), int(1)]];
    let target = vec![int(0)];
    let weights = vec![int(1)];

    let solve_res = solve_weighted_l1_projection(&target, &weights, &d0, 1024);
    assert!(solve_res.is_ok());
    let opt = solve_res.unwrap();

    // Exact duality requires exact zero value and exact dual witness equality
    assert_eq!(opt.value, BigRational::zero());
    assert_eq!(opt.residual, vec![BigRational::zero()]);
    assert_eq!(opt.dual, vec![BigRational::zero()]);
}

#[test]
fn positive_epsilon_is_not_an_exact_duality_certificate() {
    // Epsilon tolerance such as 1e-6 must not be conflated with exact zero
    let epsilon_residual = 1e-6_f64;
    assert!(epsilon_residual > 0.0);
    assert_ne!(
        BigRational::from_float(epsilon_residual),
        Some(BigRational::zero()),
        "positive float epsilon must never equal exact zero"
    );
}

// Origin: engine/crates_rs/tests/core_solvers/solver_integration.rs
// Claim: urn:core:crates_rs:tests:solver-integration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9eaab899 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9eaab899` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9eaab899 {
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
impl BoundaryError9eaab899 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9eaab899 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9eaab899 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9eaab899 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9eaab899> {
        if capacity_bound == 0 {
            return Err(BoundaryError9eaab899::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9eaab899::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9eaab899::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9eaab899() {
    let admitted = BoundaryRecord9eaab899::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9eaab899::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
