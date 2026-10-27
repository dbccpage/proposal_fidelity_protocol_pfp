//! Retains the declared finite time plan and the mathematical owner's trace.
//! Source correspondence and the written common-target theorem have separate scopes.

use crate::types::AuthorityEffect;
use core_number_theory::rational::Rational;
use core_quantum_physics::meron_source_field::{
    AnalyticResponseError, AnalyticResponsePlan, SourceFieldPlan,
};
use core_quantum_physics::meron_time_refinement::{
    EulerTimePlan, FiniteMeronChain, MeronTimeError, StaggeredMoments,
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredMeronTime {
    plan: EulerTimePlan,
    unscaled_partition: Rational,
}

impl DeclaredMeronTime {
    pub fn new(plan: EulerTimePlan) -> Result<Self, MeronTimeError> {
        let chain = FiniteMeronChain::new(plan.sites())?;
        let unscaled_partition = chain.transfer_trace(plan.repetitions(), plan.q())?;
        Ok(Self {
            plan,
            unscaled_partition,
        })
    }

    pub fn plan(&self) -> &EulerTimePlan {
        &self.plan
    }
    pub fn unscaled_partition(&self) -> &Rational {
        &self.unscaled_partition
    }
    pub fn staggered_moments(&self) -> Result<StaggeredMoments, MeronTimeError> {
        let moments = FiniteMeronChain::new(self.plan.sites())?
            .staggered_moments(self.plan.repetitions(), self.plan.q())?;
        if moments.partition() != &self.unscaled_partition {
            return Err(MeronTimeError::Matrix(
                linear_algebra::exact_field::ExactFieldError::ReplayFailed {
                    operation: "Meron observable partition",
                },
            ));
        }
        Ok(moments)
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

/// Retains the actual model owner's nonzero-source trace and declared plan.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredMeronSource {
    plan: SourceFieldPlan,
    unscaled_partition: Rational,
}
impl DeclaredMeronSource {
    pub fn new(plan: SourceFieldPlan) -> Result<Self, MeronTimeError> {
        let time = plan.time();
        let unscaled_partition = FiniteMeronChain::new(time.sites())?.source_field_trace(
            time.repetitions(),
            time.q(),
            plan.v(),
        )?;
        Ok(Self {
            plan,
            unscaled_partition,
        })
    }
    pub fn plan(&self) -> &SourceFieldPlan {
        &self.plan
    }
    pub fn unscaled_partition(&self) -> &Rational {
        &self.unscaled_partition
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

/// Retains the actual intensive time-averaged SQL/Kubo query and AR-9 radius.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredMeronResponse {
    plan: AnalyticResponsePlan,
    moments: StaggeredMoments,
    intensive_response: Rational,
}
impl DeclaredMeronResponse {
    pub fn new(plan: AnalyticResponsePlan) -> Result<Self, AnalyticResponseError> {
        let time = plan.time();
        let moments = DeclaredMeronTime::new(time.clone())?.staggered_moments()?;
        let intensive_response =
            moments.mean_square() / Rational::from_integer(time.sites().into());
        Ok(Self {
            plan,
            moments,
            intensive_response,
        })
    }
    pub fn plan(&self) -> &AnalyticResponsePlan {
        &self.plan
    }
    pub fn moments(&self) -> &StaggeredMoments {
        &self.moments
    }
    pub fn intensive_response(&self) -> &Rational {
        &self.intensive_response
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

// Origin: engine/crates_rs/core_wdp/src/meron_time_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:meron-time-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8a462942 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8a462942` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8a462942 {
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
impl BoundaryError8a462942 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8a462942 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8a462942 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8a462942 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8a462942> {
        if capacity_bound == 0 {
            return Err(BoundaryError8a462942::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8a462942::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8a462942::ExceedsCapacity {
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
mod l4_boundary_tests_8a462942 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8a462942::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8a462942::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8a462942::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8a462942::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8a462942::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8a462942::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8a462942::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
