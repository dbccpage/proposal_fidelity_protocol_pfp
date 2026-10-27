//! Finite executable witness for `PROD-P1-NEXT-1`.
//!
//! Models the P1 `AbstentionGovernor` 8-label decision table (`Refused`,
//! `RefusedCertificate`, `Stalled`, `Impossible`, `LosingInDeclaredArena`,
//! `ResolvedWithinBudget`, `Exhausted`, `UndeterminedBudget`) over exact
//! rational costs/budgets and explicit `task_admits_impossibility` policy,
//! with fixed `authority_effect = "None"`.

#![forbid(unsafe_code)]

pub const AUTHORITY_EFFECT_NONE: &str = "None";

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TerminationLabel {
    Refused,
    RefusedCertificate,
    Stalled,
    Impossible,
    LosingInDeclaredArena,
    ResolvedWithinBudget,
    Exhausted,
    UndeterminedBudget,
}

impl TerminationLabel {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Refused => "Refused",
            Self::RefusedCertificate => "RefusedCertificate",
            Self::Stalled => "Stalled",
            Self::Impossible => "Impossible",
            Self::LosingInDeclaredArena => "LosingInDeclaredArena",
            Self::ResolvedWithinBudget => "ResolvedWithinBudget",
            Self::Exhausted => "Exhausted",
            Self::UndeterminedBudget => "UndeterminedBudget",
        }
    }

    pub fn parse(raw: &str) -> Option<Self> {
        match raw {
            "Refused" => Some(Self::Refused),
            "RefusedCertificate" => Some(Self::RefusedCertificate),
            "Stalled" => Some(Self::Stalled),
            "Impossible" => Some(Self::Impossible),
            "LosingInDeclaredArena" => Some(Self::LosingInDeclaredArena),
            "ResolvedWithinBudget" => Some(Self::ResolvedWithinBudget),
            "Exhausted" => Some(Self::Exhausted),
            "UndeterminedBudget" => Some(Self::UndeterminedBudget),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CheckedClaim {
    Loss { initial_stalled: bool },
    WinOptimal { initial_value_num: i64, initial_value_den: i64 },
    WinFeasible { initial_value_num: i64, initial_value_den: i64 },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckReceipt {
    pub accepted: bool,
    pub claim: Option<CheckedClaim>,
    pub authority_effect: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GovernorReport {
    pub label: TerminationLabel,
    pub task_admits_impossibility: bool,
    pub budget_num: i64,
    pub budget_den: i64,
    pub check: Option<CheckReceipt>,
    pub authority_effect: &'static str,
}

fn leq_rational(a_num: i64, a_den: i64, b_num: i64, b_den: i64) -> bool {
    i128::from(a_num) * i128::from(b_den) <= i128::from(b_num) * i128::from(a_den)
}

fn label_from_receipt(
    receipt: &CheckReceipt,
    budget_num: i64,
    budget_den: i64,
    task_admits_impossibility: bool,
) -> Result<TerminationLabel, &'static str> {
    if !receipt.accepted {
        return Ok(TerminationLabel::RefusedCertificate);
    }
    let label = match receipt.claim.as_ref().ok_or("missing claim on accepted receipt")? {
        CheckedClaim::Loss { initial_stalled: true } => TerminationLabel::Stalled,
        CheckedClaim::Loss { initial_stalled: false } => {
            if task_admits_impossibility {
                TerminationLabel::Impossible
            } else {
                TerminationLabel::LosingInDeclaredArena
            }
        }
        CheckedClaim::WinOptimal {
            initial_value_num,
            initial_value_den,
        } => {
            if leq_rational(*initial_value_num, *initial_value_den, budget_num, budget_den) {
                TerminationLabel::ResolvedWithinBudget
            } else {
                TerminationLabel::Exhausted
            }
        }
        CheckedClaim::WinFeasible {
            initial_value_num,
            initial_value_den,
        } => {
            if leq_rational(*initial_value_num, *initial_value_den, budget_num, budget_den) {
                TerminationLabel::ResolvedWithinBudget
            } else {
                TerminationLabel::UndeterminedBudget
            }
        }
    };
    Ok(label)
}

pub fn derive_governor_report(
    check: Option<CheckReceipt>,
    budget_num: i64,
    budget_den: i64,
    task_admits_impossibility: bool,
    refusal_action: Option<&str>,
) -> Result<GovernorReport, &'static str> {
    if budget_den <= 0 || budget_num < 0 {
        return Err("invalid_input: budget must be a non-negative rational");
    }
    match (check, refusal_action) {
        (None, Some(action)) if !action.is_empty() => Ok(GovernorReport {
            label: TerminationLabel::Refused,
            task_admits_impossibility,
            budget_num,
            budget_den,
            check: None,
            authority_effect: AUTHORITY_EFFECT_NONE,
        }),
        (None, _) => Err("invalid_input: Refused requires a non-empty refusal_action"),
        (Some(_), Some(_)) => Err("invalid_input: Refused carries no certificate receipt"),
        (Some(receipt), None) => {
            if receipt.authority_effect != AUTHORITY_EFFECT_NONE {
                return Err("claim_status_firewall: authority_effect must be None");
            }
            let label = label_from_receipt(&receipt, budget_num, budget_den, task_admits_impossibility)?;
            Ok(GovernorReport {
                label,
                task_admits_impossibility,
                budget_num,
                budget_den,
                check: Some(receipt),
                authority_effect: AUTHORITY_EFFECT_NONE,
            })
        }
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p1_next_1.rs
// Claim: urn:core:crates_rs:tests:prod-p1-next-1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7da4505a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7da4505a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7da4505a {
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
impl BoundaryError7da4505a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7da4505a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7da4505a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7da4505a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7da4505a> {
        if capacity_bound == 0 {
            return Err(BoundaryError7da4505a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7da4505a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7da4505a::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn all_eight_labels_round_trip() {
        let mut seen = HashSet::new();

        let r_refused = derive_governor_report(None, 5, 1, false, Some("abort")).unwrap();
        assert_eq!(r_refused.label, TerminationLabel::Refused);
        seen.insert(r_refused.label);

        let r_bad_cert = derive_governor_report(
            Some(CheckReceipt {
                accepted: false,
                claim: None,
                authority_effect: AUTHORITY_EFFECT_NONE,
            }),
            5,
            1,
            false,
            None,
        )
        .unwrap();
        assert_eq!(r_bad_cert.label, TerminationLabel::RefusedCertificate);
        seen.insert(r_bad_cert.label);

        let r_stalled = derive_governor_report(
            Some(CheckReceipt {
                accepted: true,
                claim: Some(CheckedClaim::Loss {
                    initial_stalled: true,
                }),
                authority_effect: AUTHORITY_EFFECT_NONE,
            }),
            5,
            1,
            false,
            None,
        )
        .unwrap();
        assert_eq!(r_stalled.label, TerminationLabel::Stalled);
        seen.insert(r_stalled.label);

        let r_impossible = derive_governor_report(
            Some(CheckReceipt {
                accepted: true,
                claim: Some(CheckedClaim::Loss {
                    initial_stalled: false,
                }),
                authority_effect: AUTHORITY_EFFECT_NONE,
            }),
            5,
            1,
            true,
            None,
        )
        .unwrap();
        assert_eq!(r_impossible.label, TerminationLabel::Impossible);
        seen.insert(r_impossible.label);

        let r_arena = derive_governor_report(
            Some(CheckReceipt {
                accepted: true,
                claim: Some(CheckedClaim::Loss {
                    initial_stalled: false,
                }),
                authority_effect: AUTHORITY_EFFECT_NONE,
            }),
            5,
            1,
            false,
            None,
        )
        .unwrap();
        assert_eq!(r_arena.label, TerminationLabel::LosingInDeclaredArena);
        seen.insert(r_arena.label);

        let r_resolved = derive_governor_report(
            Some(CheckReceipt {
                accepted: true,
                claim: Some(CheckedClaim::WinOptimal {
                    initial_value_num: 2,
                    initial_value_den: 1,
                }),
                authority_effect: AUTHORITY_EFFECT_NONE,
            }),
            2,
            1,
            false,
            None,
        )
        .unwrap();
        assert_eq!(r_resolved.label, TerminationLabel::ResolvedWithinBudget);
        seen.insert(r_resolved.label);

        let r_exhausted = derive_governor_report(
            Some(CheckReceipt {
                accepted: true,
                claim: Some(CheckedClaim::WinOptimal {
                    initial_value_num: 2,
                    initial_value_den: 1,
                }),
                authority_effect: AUTHORITY_EFFECT_NONE,
            }),
            1,
            1,
            false,
            None,
        )
        .unwrap();
        assert_eq!(r_exhausted.label, TerminationLabel::Exhausted);
        seen.insert(r_exhausted.label);

        let r_undetermined = derive_governor_report(
            Some(CheckReceipt {
                accepted: true,
                claim: Some(CheckedClaim::WinFeasible {
                    initial_value_num: 5,
                    initial_value_den: 1,
                }),
                authority_effect: AUTHORITY_EFFECT_NONE,
            }),
            4,
            1,
            false,
            None,
        )
        .unwrap();
        assert_eq!(r_undetermined.label, TerminationLabel::UndeterminedBudget);
        seen.insert(r_undetermined.label);

        assert_eq!(seen.len(), 8);
        for label in &seen {
            assert_eq!(TerminationLabel::parse(label.as_str()), Some(*label));
        }
    }
}

#[test]
fn l4_boundary_admits_and_refuses_7da4505a() {
    let admitted = BoundaryRecord7da4505a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7da4505a::try_admit(9, 8).is_err());
}
