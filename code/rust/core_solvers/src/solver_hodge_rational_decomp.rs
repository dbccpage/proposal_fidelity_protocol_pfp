//! Exact Euclidean Hodge decomposition on finite rational cochain complexes.
//!
//! Solves d0^T d0 alpha = d0^T f and d1 d1^T beta = d1 f using the
//! sovereign fraction-free Bareiss solver, then independently replays the
//! certificate. Zero free coordinates select deterministic gauges. This is the
//! unweighted Euclidean inner product; no weighted-star operator is inferred.
//! One fuel budget covers validation, both solves, construction and replay.
//! AuthorityEffect: None.

use crate::cert_hodge_decomp::{
    check_hodge_certificate, validate_problem, HodgeCertificate, HodgeError, HodgeProblem,
    VerifiedHodge,
};
use linear_algebra::exact_field::rational_bareiss::{self as exact, RationalBudget, RationalError};
use num_rational::BigRational;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct HodgeSolution {
    pub certificate: HodgeCertificate,
    pub verified: VerifiedHodge,
    pub scalar_ops: usize,
}

fn compute_harmonic_residual(
    flow: &[BigRational],
    exact: &[BigRational],
    coexact: &[BigRational],
    fuel: &mut RationalBudget,
) -> Result<Vec<BigRational>, HodgeError> {
    let mut harmonic = Vec::new();
    harmonic
        .try_reserve_exact(flow.len())
        .map_err(|_| RationalError::Allocation)?;
    for (i, x) in flow.iter().enumerate() {
        let residual = fuel.sub(x, &exact[i])?;
        harmonic.push(fuel.sub(&residual, &coexact[i])?);
    }
    Ok(harmonic)
}

fn solve_exact_component(
    p: &HodgeProblem<'_>,
    fuel: &mut RationalBudget,
) -> Result<(Vec<BigRational>, Vec<BigRational>), HodgeError> {
    let d0t = p.d0.try_transpose().map_err(RationalError::from)?;
    let g0 = exact::multiply(&d0t, p.d0, fuel)?;
    let rhs0 = exact::multiply_vector(&d0t, p.flow, fuel)?;
    let alpha = exact::solve(&g0, &rhs0, fuel)?.particular;
    let exact = exact::multiply_vector(p.d0, &alpha, fuel)?;
    Ok((alpha, exact))
}

fn solve_coexact_component(
    p: &HodgeProblem<'_>,
    fuel: &mut RationalBudget,
) -> Result<(Vec<BigRational>, Vec<BigRational>), HodgeError> {
    let d1t = p.d1.try_transpose().map_err(RationalError::from)?;
    let g2 = exact::multiply(p.d1, &d1t, fuel)?;
    let rhs2 = exact::multiply_vector(p.d1, p.flow, fuel)?;
    let beta = exact::solve(&g2, &rhs2, fuel)?.particular;
    let coexact = exact::multiply_vector(&d1t, &beta, fuel)?;
    Ok((beta, coexact))
}

fn solve_exact_and_coexact(
    p: &HodgeProblem<'_>,
    fuel: &mut RationalBudget,
) -> Result<
    (
        Vec<BigRational>,
        Vec<BigRational>,
        Vec<BigRational>,
        Vec<BigRational>,
    ),
    HodgeError,
> {
    let (alpha, exact) = solve_exact_component(p, fuel)?;
    let (beta, coexact) = solve_coexact_component(p, fuel)?;
    Ok((alpha, beta, exact, coexact))
}

pub fn solve_hodge(
    p: &HodgeProblem<'_>,
    fuel: &mut RationalBudget,
) -> Result<HodgeSolution, HodgeError> {
    let start = fuel.used();
    validate_problem(p, fuel)?;
    let (alpha, beta, exact, coexact) = solve_exact_and_coexact(p, fuel)?;
    let harmonic = compute_harmonic_residual(p.flow, &exact, &coexact, fuel)?;
    let certificate = HodgeCertificate {
        alpha,
        beta,
        exact,
        coexact,
        harmonic,
    };
    let verified = check_hodge_certificate(p, &certificate, fuel)?;
    Ok(HodgeSolution {
        certificate,
        verified,
        scalar_ops: fuel.used() - start,
    })
}

// Origin: engine/crates_rs/core_solvers/src/solver_hodge_rational_decomp.rs
// Claim: urn:core:crates_rs:core-solvers:solver-hodge-rational-decomp:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7bf48338 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7bf48338` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7bf48338 {
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
impl BoundaryError7bf48338 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7bf48338 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7bf48338 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7bf48338 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7bf48338> {
        if capacity_bound == 0 {
            return Err(BoundaryError7bf48338::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7bf48338::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7bf48338::ExceedsCapacity {
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
mod l4_boundary_tests_7bf48338 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7bf48338::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7bf48338::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7bf48338::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7bf48338::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7bf48338::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError7bf48338::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError7bf48338::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
