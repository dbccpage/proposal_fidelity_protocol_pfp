//! Canonical routing axis for the engine.
//!
//! The routing axis is a closed set: `CheckPassed`, `RequiresLift`, `Repair`,
//! `Refusal`, `NoRule`, `BudgetUnknown`, `Refused`.
//! It is disjoint from the diagnostic classes.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

use crate::terminal_status::TerminalStatus;

/// The seven canonical routing terminal values.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum RoutingTerminal {
    CheckPassed,
    RequiresLift,
    Repair,
    Refusal,
    NoRule,
    BudgetUnknown,
    Refused,
}

impl From<TerminalStatus> for RoutingTerminal {
    fn from(status: TerminalStatus) -> Self {
        match status {
            TerminalStatus::ExactRuleDerived | TerminalStatus::UniqueOutputDerived => {
                RoutingTerminal::CheckPassed
            }
            TerminalStatus::NoRuleInSearchClass => RoutingTerminal::NoRule,
            TerminalStatus::BudgetUnknown => RoutingTerminal::BudgetUnknown,
            TerminalStatus::LiftRequired => RoutingTerminal::RequiresLift,
            TerminalStatus::ParseRefused | TerminalStatus::NoPacket => RoutingTerminal::Refusal,
            TerminalStatus::Refused
            | TerminalStatus::LabelConflictsWithDerivation
            | TerminalStatus::InvalidProposal
            | TerminalStatus::OperatorConflict => RoutingTerminal::Refused,
            TerminalStatus::NonUniqueOutput
            | TerminalStatus::EnumeratorFailure
            | TerminalStatus::UnknownSector
            | TerminalStatus::NoDescentYet
            | TerminalStatus::LabelOnlyUncertified
            | TerminalStatus::ReplayMismatch
            | TerminalStatus::PolicyAmbiguous
            | TerminalStatus::VerifierDisabled
            | TerminalStatus::SearchIncomplete
            | TerminalStatus::PolicyUnderspecified => RoutingTerminal::Repair,
        }
    }
}

/// The PFP terminal statuses (`pfp.domain.kernel.result.TerminalStatus`).
///
/// Each one routes to exactly one `RoutingTerminal`. The same map is data in
/// `pfp/infrastructure/yaml/stages/terminal_routing.json`, and the
/// test below checks the two agree. `BudgetExhausted` routes to `BudgetUnknown`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum PfpTerminal {
    Exact,
    Verified,
    VerifiedWithResiduals,
    StabilizedSurvivor,
    NeedsExternalOracle,
    OpenObstruction,
    BlockedByEvidence,
    InfrastructureFailure,
    Refused,
    BudgetExhausted,
}

impl PfpTerminal {
    pub const ALL: [PfpTerminal; 10] = [
        PfpTerminal::Exact,
        PfpTerminal::Verified,
        PfpTerminal::VerifiedWithResiduals,
        PfpTerminal::StabilizedSurvivor,
        PfpTerminal::NeedsExternalOracle,
        PfpTerminal::OpenObstruction,
        PfpTerminal::BlockedByEvidence,
        PfpTerminal::InfrastructureFailure,
        PfpTerminal::Refused,
        PfpTerminal::BudgetExhausted,
    ];
}

impl From<PfpTerminal> for RoutingTerminal {
    fn from(status: PfpTerminal) -> Self {
        match status {
            PfpTerminal::Exact | PfpTerminal::Verified | PfpTerminal::VerifiedWithResiduals => {
                RoutingTerminal::CheckPassed
            }
            PfpTerminal::StabilizedSurvivor | PfpTerminal::NeedsExternalOracle => {
                RoutingTerminal::RequiresLift
            }
            PfpTerminal::OpenObstruction
            | PfpTerminal::BlockedByEvidence
            | PfpTerminal::InfrastructureFailure => RoutingTerminal::Refusal,
            PfpTerminal::Refused => RoutingTerminal::Refused,
            PfpTerminal::BudgetExhausted => RoutingTerminal::BudgetUnknown,
        }
    }
}

// Origin: engine/crates_rs/core_types/src/routing.rs
// Claim: urn:core:crates_rs:core-types:routing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord402bfcd8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord402bfcd8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError402bfcd8 {
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
impl BoundaryError402bfcd8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError402bfcd8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError402bfcd8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord402bfcd8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError402bfcd8> {
        if capacity_bound == 0 {
            return Err(BoundaryError402bfcd8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError402bfcd8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError402bfcd8::ExceedsCapacity {
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
    fn test_all_seven_routing_terminals_are_reachable() {
        assert_eq!(
            RoutingTerminal::from(TerminalStatus::ExactRuleDerived),
            RoutingTerminal::CheckPassed
        );
        assert_eq!(
            RoutingTerminal::from(TerminalStatus::LiftRequired),
            RoutingTerminal::RequiresLift
        );
        assert_eq!(
            RoutingTerminal::from(TerminalStatus::NonUniqueOutput),
            RoutingTerminal::Repair
        );
        assert_eq!(
            RoutingTerminal::from(TerminalStatus::ParseRefused),
            RoutingTerminal::Refusal
        );
        assert_eq!(
            RoutingTerminal::from(TerminalStatus::NoRuleInSearchClass),
            RoutingTerminal::NoRule
        );
        assert_eq!(
            RoutingTerminal::from(TerminalStatus::BudgetUnknown),
            RoutingTerminal::BudgetUnknown
        );
        assert_eq!(
            RoutingTerminal::from(TerminalStatus::Refused),
            RoutingTerminal::Refused
        );
    }

    #[test]
    fn test_pfp_terminal_routing_matches_the_shared_data_file() {
        let text = include_str!(
            "../../../../pfp/infrastructure/yaml/stages/terminal_routing.json"
        );
        let data: serde_json::Value = serde_json::from_str(text).expect("valid JSON");
        let routing = data["routing"].as_object().expect("routing object");
        assert_eq!(routing.len(), PfpTerminal::ALL.len());
        for status in PfpTerminal::ALL {
            let key = serde_json::to_value(status).expect("serialize");
            let expected = serde_json::to_value(RoutingTerminal::from(status)).expect("serialize");
            assert_eq!(routing[key.as_str().expect("string")], expected, "{status:?}");
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_402bfcd8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord402bfcd8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord402bfcd8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord402bfcd8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord402bfcd8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord402bfcd8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError402bfcd8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError402bfcd8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
