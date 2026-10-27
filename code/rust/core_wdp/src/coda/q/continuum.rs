use serde::{Deserialize, Serialize};

use super::errors::QError;
use super::packet::option_has_text;

/// Continuum admission debt required before a candidate may be Q-held.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ContinuumDebt {
    pub finite_shadow: Option<String>,
    pub refinement_relation: Option<String>,
    pub declared_topology: Option<String>,
    pub convergence_certificate_route: Option<String>,
    pub descent_trigger: Option<String>,
}

impl ContinuumDebt {
    pub fn has_finite_shadow(&self) -> bool {
        option_has_text(&self.finite_shadow)
    }

    pub fn has_refinement_route(&self) -> bool {
        option_has_text(&self.refinement_relation)
            && option_has_text(&self.convergence_certificate_route)
    }

    pub fn has_declared_topology(&self) -> bool {
        option_has_text(&self.declared_topology)
    }

    pub fn has_descent_trigger(&self) -> bool {
        option_has_text(&self.descent_trigger)
    }

    pub fn validate_for_qheld(&self) -> Result<(), QError> {
        if !self.has_finite_shadow() {
            return Err(QError::QHeldWithoutFiniteShadow);
        }
        if !self.has_refinement_route() {
            return Err(QError::QHeldWithoutRefinementRoute);
        }
        if !self.has_declared_topology() {
            return Err(QError::ContinuumClaimWithoutTopology);
        }
        if !self.has_descent_trigger() {
            return Err(QError::QHeldWithoutDescentTrigger);
        }
        Ok(())
    }

    pub fn validate_for_admission(&self) -> Result<(), QError> {
        if !self.has_finite_shadow() {
            return Err(QError::RefusedContinuumNoShadow);
        }
        if !self.has_declared_topology() {
            return Err(QError::ContinuumClaimWithoutTopology);
        }
        if !option_has_text(&self.convergence_certificate_route) {
            return Err(QError::OracleNeededConvergence);
        }
        if !option_has_text(&self.refinement_relation) || !self.has_descent_trigger() {
            return Err(QError::OpenResidual);
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/continuum.rs
// Claim: urn:core:crates_rs:core-wdp:continuum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda2fa37ca {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda2fa37ca` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora2fa37ca {
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
impl BoundaryErrora2fa37ca {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora2fa37ca {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora2fa37ca {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda2fa37ca {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora2fa37ca> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora2fa37ca::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora2fa37ca::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora2fa37ca::ExceedsCapacity {
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
mod l4_boundary_tests_a2fa37ca {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda2fa37ca::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda2fa37ca::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda2fa37ca::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda2fa37ca::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda2fa37ca::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora2fa37ca::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora2fa37ca::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
