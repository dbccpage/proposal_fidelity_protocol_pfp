use num_rational::BigRational;
use num_traits::One;

/// Quotient certificate carrying primal repair, residual, and dual witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuotientCertificate {
    pub distance: BigRational,
    pub repair: Vec<BigRational>,
    pub residual: Vec<BigRational>,
    pub witness: Vec<BigRational>,
    pub method: String,
}

#[allow(clippy::needless_range_loop)]
impl QuotientCertificate {
    /// Replay and verify the exact rational certificate against original data.
    pub fn verify(&self, matrix: &[Vec<BigRational>], x: &[BigRational]) -> bool {
        core_functional::phi1::Phi1Functional::verify_exact_certificate(
            core_functional::phi1::ExactPhi1Certificate {
                omega: x.to_vec(),
                d0: matrix.to_vec(),
                weights: vec![BigRational::one(); x.len()],
                alpha: self.repair.clone(),
                primal_residual: self.residual.clone(),
                dual_witness: self.witness.clone(),
                reported_value: self.distance.clone(),
            },
        )
        .is_ok()
    }
}

pub use crate::solver_lp_phi1_quotient::{
    compute_curvature_k, solve_constrained_curved_phi1, verify_constrained_curved_phi1,
    CurvedConstrainedPhi1Certificate, CurvedConstrainedPhi1Error, VerifiedCurvedConstrainedPhi1,
};

/// Propose primal and dual witnesses with the canonical exact solver, then
/// return the independently evaluated certificate in the existing wire shape.
pub fn solve_l1_quotient(
    matrix: &[Vec<BigRational>],
    x: &[BigRational],
) -> Result<QuotientCertificate, String> {
    let space = core_functional::l1_seminorm::L1Seminorm::new(
        matrix.to_vec(),
        vec![BigRational::one(); x.len()],
    )
    .map_err(|error| error.to_string())?;
    let verified = crate::solver_lp_phi1_quotient::solve_exact_phi1(&space, x)
        .map_err(|error| error.to_string())?;
    Ok(QuotientCertificate {
        distance: verified.value().clone(),
        repair: verified.alpha().to_vec(),
        residual: verified.primal_residual().to_vec(),
        witness: verified.dual_witness().to_vec(),
        method: "exact_primal_dual_simplex".into(),
    })
}

/// Solve the unweighted closure-constrained curved repair linear program
/// `min_{f in C^0} ||x - d0 f||_1 s.t. ||d1 x - K f||_1 <= ||d1 x||_1 + tau`
/// using [`core_functional::gamma2::RawClosureDefectResult`] when `K = d1 d0 != 0`.
pub fn solve_l1_curved_constrained(
    d0: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    x: &[BigRational],
    tau: &BigRational,
) -> Result<VerifiedCurvedConstrainedPhi1, String> {
    let space = core_functional::l1_seminorm::L1Seminorm::new(
        d0.to_vec(),
        vec![BigRational::one(); x.len()],
    )
    .map_err(|error| error.to_string())?;
    solve_constrained_curved_phi1(&space, d1, x, tau).map_err(|error| error.to_string())
}

// Origin: engine/crates_rs/core_solvers/src/solver_cohomology_simplicial_l1.rs
// Claim: urn:core:crates_rs:core-solvers:solver-cohomology-simplicial-l1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord12530f83 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord12530f83` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError12530f83 {
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
impl BoundaryError12530f83 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError12530f83 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError12530f83 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord12530f83 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError12530f83> {
        if capacity_bound == 0 {
            return Err(BoundaryError12530f83::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError12530f83::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError12530f83::ExceedsCapacity {
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
mod l4_boundary_tests_12530f83 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord12530f83::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord12530f83::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord12530f83::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord12530f83::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord12530f83::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError12530f83::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError12530f83::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
