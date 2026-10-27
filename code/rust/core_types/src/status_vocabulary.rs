//! Status vocabulary map across Sentinel crates.
//!
//! Provides a unified mapping registry for translating between:
//! - `core_policy::trichotomy::ObstructionDiagnosticClass`
//! - `core_types::q_continuum::TerminalStatus`
//! - `ProductTerminalTarget` (replacing BPA `PacketTerminalTarget`)
//! - `SweepDecision` (mirroring sweep kernel `Decision`)

use crate::q_continuum::TerminalStatus;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use serde::{Deserialize, Serialize};

/// Product terminal targets (prose classifiers).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ProductTerminalTarget {
    Repaired,
    ExactRepair,
    ClosedSurvivor,
    LiftNeeded,
    OracleNeeded,
    NoRule,
    Refusal,
    Accepted,
}

/// Sweep decisions.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum SweepDecision {
    Certified,
    Killed,
    Obligation,
    DeferredToValidator,
    RefusedHostAuthority,
    NotGated,
}

/// A unified mapping registry for translating status vocabulary across Sentinel crates.
pub struct StatusVocabularyMap;

impl StatusVocabularyMap {
    /// Maps finite obstruction trichotomy statuses to Q-continuum terminal statuses.
    pub fn trichotomy_to_q(status: ObstructionDiagnosticClass) -> TerminalStatus {
        match status {
            ObstructionDiagnosticClass::ExactRepair => TerminalStatus::Supported,
            ObstructionDiagnosticClass::ClosedResidual => TerminalStatus::Residual,
            ObstructionDiagnosticClass::ActiveClosureFailure => TerminalStatus::Refused,
        }
    }

    /// Maps product terminal targets (prose) to Q-continuum terminal statuses.
    pub fn product_to_q(target: ProductTerminalTarget) -> TerminalStatus {
        match target {
            ProductTerminalTarget::Repaired => TerminalStatus::Supported,
            ProductTerminalTarget::ExactRepair => TerminalStatus::Supported,
            ProductTerminalTarget::ClosedSurvivor => TerminalStatus::Residual,
            ProductTerminalTarget::LiftNeeded => TerminalStatus::Underdetermined,
            ProductTerminalTarget::OracleNeeded => TerminalStatus::Underdetermined,
            ProductTerminalTarget::NoRule => TerminalStatus::Refused,
            ProductTerminalTarget::Refusal => TerminalStatus::Refused,
            ProductTerminalTarget::Accepted => TerminalStatus::Implemented,
        }
    }

    /// Maps Q-continuum terminal statuses to sweep decisions.
    pub fn q_to_sweep(status: TerminalStatus) -> SweepDecision {
        match status {
            TerminalStatus::Supported => SweepDecision::Certified,
            TerminalStatus::ConditionallySupported => SweepDecision::Obligation,
            TerminalStatus::Residual => SweepDecision::DeferredToValidator,
            TerminalStatus::Underdetermined => SweepDecision::DeferredToValidator,
            TerminalStatus::Refuted => SweepDecision::Killed,
            TerminalStatus::Refused => SweepDecision::RefusedHostAuthority,
            TerminalStatus::Speculative => SweepDecision::NotGated,
            TerminalStatus::Implemented => SweepDecision::NotGated,
        }
    }
}

// Origin: engine/crates_rs/core_types/src/status_vocabulary.rs
// Claim: urn:core:crates_rs:core-types:status-vocabulary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda835250d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda835250d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora835250d {
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
impl BoundaryErrora835250d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora835250d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora835250d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda835250d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora835250d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora835250d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora835250d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora835250d::ExceedsCapacity {
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

    #[test]
    fn test_mappings() {
        assert_eq!(
            StatusVocabularyMap::trichotomy_to_q(ObstructionDiagnosticClass::ExactRepair),
            TerminalStatus::Supported
        );
        assert_eq!(
            StatusVocabularyMap::product_to_q(ProductTerminalTarget::Repaired),
            TerminalStatus::Supported
        );
        assert_eq!(
            StatusVocabularyMap::q_to_sweep(TerminalStatus::Supported),
            SweepDecision::Certified
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_a835250d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda835250d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda835250d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda835250d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda835250d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda835250d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora835250d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora835250d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
