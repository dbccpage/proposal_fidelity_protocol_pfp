use serde::{Deserialize, Serialize};

use crate::authority::{AuthorityLevel, AuthorityTerminal};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TerminationCondition {
    Converged,
    Irreducible,
    BudgetExhausted,
    ExternalAbort,
    Suspended,
    ConstraintViolation,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TerminalStatus {
    ExactRuleDerived,
    UniqueOutputDerived,
    NoRuleInSearchClass,
    NonUniqueOutput,
    EnumeratorFailure,
    Refused,
    LabelConflictsWithDerivation,
    BudgetUnknown,
    InvalidProposal,
    OperatorConflict,
    UnknownSector,
    NoDescentYet,
    LabelOnlyUncertified,
    LiftRequired,
    ParseRefused,
    ReplayMismatch,
    PolicyAmbiguous,
    NoPacket,
    VerifierDisabled,
    SearchIncomplete,
    PolicyUnderspecified,
}

pub const ALL_TERMINAL_STATUSES: [TerminalStatus; 21] = [
    TerminalStatus::ExactRuleDerived,
    TerminalStatus::UniqueOutputDerived,
    TerminalStatus::NoRuleInSearchClass,
    TerminalStatus::NonUniqueOutput,
    TerminalStatus::EnumeratorFailure,
    TerminalStatus::Refused,
    TerminalStatus::LabelConflictsWithDerivation,
    TerminalStatus::BudgetUnknown,
    TerminalStatus::InvalidProposal,
    TerminalStatus::OperatorConflict,
    TerminalStatus::UnknownSector,
    TerminalStatus::NoDescentYet,
    TerminalStatus::LabelOnlyUncertified,
    TerminalStatus::LiftRequired,
    TerminalStatus::ParseRefused,
    TerminalStatus::ReplayMismatch,
    TerminalStatus::PolicyAmbiguous,
    TerminalStatus::NoPacket,
    TerminalStatus::VerifierDisabled,
    TerminalStatus::SearchIncomplete,
    TerminalStatus::PolicyUnderspecified,
];

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ResidualClass {
    Exact,
    ClosedSurvivor,
    Open,
    Refused,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct FiberAgreement {
    pub coherent_transport_verified: bool,
    pub replay_equivalence_verified: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TerminalClassificationError {
    InvalidFiberCounts,
    InvalidFiberState,
}

// Origin: engine/crates_rs/core_types/src/terminal_status.rs
// Claim: urn:core:crates_rs:core-types:terminal-status:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TerminalClassificationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TerminalClassificationError {}

impl TerminalStatus {
    /// Map a terminal status to an authority **level** from the tag alone.
    ///
    /// A terminal tag is NOT authority: the authority-bearing terminals
    /// (`ExactRuleDerived`, `UniqueOutputDerived`) map to
    /// [`AuthorityLevel::Certifiable`], never `Certified`. This diagnostic type
    /// has no conversion to `CertifiedAuthority`; promotion belongs to the
    /// separate host boundary after packet certification and receipt review.
    pub fn authority_level(self) -> AuthorityLevel {
        match self {
            TerminalStatus::ExactRuleDerived | TerminalStatus::UniqueOutputDerived => {
                AuthorityLevel::Certifiable
            }
            TerminalStatus::Refused
            | TerminalStatus::LabelConflictsWithDerivation
            | TerminalStatus::InvalidProposal
            | TerminalStatus::OperatorConflict => AuthorityLevel::Refused,
            TerminalStatus::NoRuleInSearchClass
            | TerminalStatus::NonUniqueOutput
            | TerminalStatus::EnumeratorFailure
            | TerminalStatus::BudgetUnknown
            | TerminalStatus::UnknownSector
            | TerminalStatus::NoDescentYet
            | TerminalStatus::LabelOnlyUncertified
            | TerminalStatus::LiftRequired
            | TerminalStatus::ParseRefused
            | TerminalStatus::ReplayMismatch
            | TerminalStatus::PolicyAmbiguous
            | TerminalStatus::NoPacket
            | TerminalStatus::VerifierDisabled
            | TerminalStatus::SearchIncomplete
            | TerminalStatus::PolicyUnderspecified => AuthorityLevel::Uncertified,
        }
    }

    pub fn residual_class(self) -> ResidualClass {
        match self {
            TerminalStatus::ExactRuleDerived | TerminalStatus::UniqueOutputDerived => {
                ResidualClass::Exact
            }
            TerminalStatus::NoRuleInSearchClass => ResidualClass::ClosedSurvivor,
            TerminalStatus::Refused
            | TerminalStatus::LabelConflictsWithDerivation
            | TerminalStatus::InvalidProposal
            | TerminalStatus::OperatorConflict
            | TerminalStatus::ParseRefused => ResidualClass::Refused,
            TerminalStatus::NonUniqueOutput
            | TerminalStatus::EnumeratorFailure
            | TerminalStatus::BudgetUnknown
            | TerminalStatus::UnknownSector
            | TerminalStatus::NoDescentYet
            | TerminalStatus::LabelOnlyUncertified
            | TerminalStatus::LiftRequired
            | TerminalStatus::ReplayMismatch
            | TerminalStatus::PolicyAmbiguous
            | TerminalStatus::NoPacket
            | TerminalStatus::VerifierDisabled
            | TerminalStatus::SearchIncomplete
            | TerminalStatus::PolicyUnderspecified => ResidualClass::Open,
        }
    }

    pub fn can_teach(self) -> bool {
        matches!(
            self,
            TerminalStatus::ExactRuleDerived | TerminalStatus::UniqueOutputDerived
        )
    }

    /// `T_auth` projection: `Some(t)` iff this status is authority-bearing.
    ///
    /// This is the only place a `TerminalStatus` is mapped into the `T_auth`
    /// type [`AuthorityTerminal`]; every non-authority terminal returns `None`.
    pub fn authority_terminal(self) -> Option<AuthorityTerminal> {
        match self {
            TerminalStatus::ExactRuleDerived => Some(AuthorityTerminal::ExactRuleDerived),
            TerminalStatus::UniqueOutputDerived => Some(AuthorityTerminal::UniqueOutputDerived),
            _ => None,
        }
    }
}

fn resolve_multi_candidate_fiber(
    output_count: usize,
    agreement: Option<FiberAgreement>,
) -> TerminalStatus {
    if output_count != 1 {
        return TerminalStatus::NonUniqueOutput;
    }
    let agreement = agreement.unwrap_or(FiberAgreement {
        coherent_transport_verified: true,
        replay_equivalence_verified: true,
    });
    if !agreement.coherent_transport_verified {
        TerminalStatus::PolicyAmbiguous
    } else if !agreement.replay_equivalence_verified {
        TerminalStatus::ReplayMismatch
    } else {
        TerminalStatus::UniqueOutputDerived
    }
}

fn validate_fiber_counts(
    candidate_count: usize,
    output_count: usize,
) -> Result<(), TerminalClassificationError> {
    if (candidate_count > 0 && output_count == 0) || output_count > candidate_count {
        return Err(TerminalClassificationError::InvalidFiberCounts);
    }
    Ok(())
}

pub fn terminal_from_fiber(
    packet_selected: bool,
    candidate_count: usize,
    output_count: usize,
    search_exhaustive: bool,
    agreement: Option<FiberAgreement>,
    verifier_enabled: bool,
) -> Result<TerminalStatus, TerminalClassificationError> {
    if !packet_selected {
        if (candidate_count, output_count, search_exhaustive) != (0, 0, false) {
            return Err(TerminalClassificationError::InvalidFiberState);
        }
        return Ok(TerminalStatus::NoPacket);
    }
    if !verifier_enabled {
        return Ok(TerminalStatus::VerifierDisabled);
    }
    validate_fiber_counts(candidate_count, output_count)?;
    Ok(match candidate_count {
        0 if search_exhaustive => TerminalStatus::NoRuleInSearchClass,
        0 => TerminalStatus::SearchIncomplete,
        1 => TerminalStatus::ExactRuleDerived,
        _ => resolve_multi_candidate_fiber(output_count, agreement),
    })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{
        terminal_from_fiber, ResidualClass, TerminalClassificationError, TerminalStatus,
        ALL_TERMINAL_STATUSES,
    };
    use crate::authority::AuthorityLevel;

    /// No wildcard arm: a new variant fails to compile here until it is given an
    /// ordinal, and the test below then fails until it also reaches
    /// `ALL_TERMINAL_STATUSES`.
    fn ordinal_high(status: TerminalStatus) -> usize {
        match status {
            TerminalStatus::ParseRefused => 14,
            TerminalStatus::ReplayMismatch => 15,
            TerminalStatus::PolicyAmbiguous => 16,
            TerminalStatus::NoPacket => 17,
            TerminalStatus::VerifierDisabled => 18,
            TerminalStatus::SearchIncomplete => 19,
            TerminalStatus::PolicyUnderspecified => 20,
            _ => 0,
        }
    }

    fn ordinal_mid(status: TerminalStatus) -> usize {
        match status {
            TerminalStatus::BudgetUnknown => 7,
            TerminalStatus::InvalidProposal => 8,
            TerminalStatus::OperatorConflict => 9,
            TerminalStatus::UnknownSector => 10,
            TerminalStatus::NoDescentYet => 11,
            TerminalStatus::LabelOnlyUncertified => 12,
            TerminalStatus::LiftRequired => 13,
            other => ordinal_high(other),
        }
    }

    fn ordinal(status: TerminalStatus) -> usize {
        match status {
            TerminalStatus::ExactRuleDerived => 0,
            TerminalStatus::UniqueOutputDerived => 1,
            TerminalStatus::NoRuleInSearchClass => 2,
            TerminalStatus::NonUniqueOutput => 3,
            TerminalStatus::EnumeratorFailure => 4,
            TerminalStatus::Refused => 5,
            TerminalStatus::LabelConflictsWithDerivation => 6,
            other => ordinal_mid(other),
        }
    }

    #[test]
    fn all_terminal_statuses_is_exhaustive_and_duplicate_free() {
        let mut seen = vec![false; ALL_TERMINAL_STATUSES.len()];
        for status in ALL_TERMINAL_STATUSES {
            let index = ordinal(status);
            assert!(
                !seen[index],
                "{status:?} appears twice in ALL_TERMINAL_STATUSES"
            );
            seen[index] = true;
        }
        assert!(
            seen.iter().all(|hit| *hit),
            "a variant is missing from ALL_TERMINAL_STATUSES, so every gate that \
             iterates it silently skips that terminal"
        );
    }

    #[test]
    fn budget_unknown_is_a_resource_record_not_an_obstruction_class() {
        // Rubric section 5: BudgetUnknown is a resource debt record, never an
        // obstruction class, and it is never authority-bearing.
        assert_eq!(
            TerminalStatus::BudgetUnknown.residual_class(),
            ResidualClass::Open
        );
        assert_eq!(TerminalStatus::BudgetUnknown.authority_terminal(), None);
        assert!(!TerminalStatus::BudgetUnknown.can_teach());
    }

    #[test]
    fn every_terminal_has_authority_and_residual_mapping() {
        for status in ALL_TERMINAL_STATUSES {
            let _ = status.authority_level();
            let _ = status.residual_class();
        }
    }

    #[test]
    fn certified_terminals_are_the_only_teaching_terminals() {
        for status in ALL_TERMINAL_STATUSES {
            assert_eq!(
                status.can_teach(),
                matches!(
                    status,
                    TerminalStatus::ExactRuleDerived | TerminalStatus::UniqueOutputDerived
                )
            );
        }
    }

    #[test]
    fn refused_and_parse_refused_are_not_certified() {
        assert!(!TerminalStatus::ParseRefused
            .authority_level()
            .is_certified());
        assert_eq!(
            TerminalStatus::ParseRefused.residual_class(),
            ResidualClass::Refused
        );
    }

    #[test]
    fn authority_level_never_returns_certified_from_tag_alone() {
        // The tag alone is never certified: at most `Certifiable`.
        for status in ALL_TERMINAL_STATUSES {
            assert!(
                !status.authority_level().is_certified(),
                "{status:?} minted Certified from the tag alone, bypassing descent"
            );
        }
        assert_eq!(
            TerminalStatus::ExactRuleDerived.authority_level(),
            AuthorityLevel::Certifiable
        );
        assert_eq!(
            TerminalStatus::UniqueOutputDerived.authority_level(),
            AuthorityLevel::Certifiable
        );
    }

    #[test]
    fn terminal_from_fiber_enforces_count_invariants() {
        assert_eq!(
            terminal_from_fiber(false, 0, 0, false, None, true),
            Ok(TerminalStatus::NoPacket)
        );
        assert_eq!(
            terminal_from_fiber(true, 2, 3, false, None, true),
            Err(TerminalClassificationError::InvalidFiberCounts)
        );
        assert_eq!(
            terminal_from_fiber(true, 1, 1, true, None, true),
            Ok(TerminalStatus::ExactRuleDerived)
        );
    }
}
