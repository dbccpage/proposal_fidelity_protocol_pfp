//! Regulatory T-Cell (Treg) Suppression and Self-Tolerance Maintenance (U16).
//!
//! Suppresses hyper-activation when global defect is zero (Phi_1 = 0).
//! When the system is in an un-obstructed ground state, Treg actively suppresses
//! candidate alarms to prevent destructive autoimmune over-reaction on benign variance.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TregStatus {
    Suppressive,
    Permissive,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TregEvaluation {
    pub global_obstruction_phi1: i64,
    pub status: TregStatus,
    pub alarm_suppressed: bool,
    pub reasoning: String,
    pub authority_effect: String,
}

#[derive(Debug, Default, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TregRegulator;

impl TregRegulator {
    pub fn new() -> Self {
        Self
    }

    /// Evaluates whether an unconfirmed alarm should be suppressed by Treg.
    /// If global_obstruction_phi1 == 0, suppression is active.
    pub fn evaluate(&self, global_obstruction_phi1: i64, alarm_present: bool) -> TregEvaluation {
        if global_obstruction_phi1 == 0 {
            TregEvaluation {
                global_obstruction_phi1,
                status: TregStatus::Suppressive,
                alarm_suppressed: alarm_present,
                reasoning: if alarm_present {
                    "Treg suppression active: zero global defect Phi_1 = 0; candidate alarm suppressed".to_string()
                } else {
                    "Treg quiescent: state is clean".to_string()
                },
                authority_effect: "None".to_string(),
            }
        } else {
            TregEvaluation {
                global_obstruction_phi1,
                status: TregStatus::Permissive,
                alarm_suppressed: false,
                reasoning: format!(
                    "Treg permissive: non-zero global defect Phi_1 = {global_obstruction_phi1}; effector response permitted"
                ),
                authority_effect: "None".to_string(),
            }
        }
    }
}
/// Batch ledger: suppressive rows plus permissive rows restore the number examined.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TregBatch {
    examined: u64,
    suppressive: u64,
    permissive: u64,
}

fn record_treg_row(
    evaluation: &TregEvaluation,
    phi: i64,
    alarm: bool,
    suppressive: &mut u64,
    permissive: &mut u64,
) -> Result<(), &'static str> {
    match evaluation.status {
        TregStatus::Suppressive => {
            if phi != 0 || evaluation.alarm_suppressed != alarm {
                return Err("suppression does not match a zero defect");
            }
            *suppressive = suppressive
                .checked_add(1)
                .ok_or("suppressive count overflow")?;
        }
        TregStatus::Permissive => {
            if phi == 0 || evaluation.alarm_suppressed {
                return Err("a permissive row still suppressed an alarm");
            }
            *permissive = permissive
                .checked_add(1)
                .ok_or("permissive count overflow")?;
        }
    }
    Ok(())
}

pub fn try_treg_batch(rows: &[(i64, bool)]) -> Result<TregBatch, &'static str> {
    if rows.is_empty() {
        return Err("a batch examines at least one row");
    }
    let regulator = TregRegulator::new();
    let mut examined = 0u64;
    let mut suppressive = 0u64;
    let mut permissive = 0u64;
    for &(phi, alarm) in rows {
        let evaluation = regulator.evaluate(phi, alarm);
        record_treg_row(&evaluation, phi, alarm, &mut suppressive, &mut permissive)?;
        examined = examined.checked_add(1).ok_or("examined count overflow")?;
    }
    let restored = suppressive
        .checked_add(permissive)
        .ok_or("batch total overflow")?;
    if restored != examined {
        return Err("suppressive and permissive rows do not cover the batch");
    }
    Ok(TregBatch {
        examined,
        suppressive,
        permissive,
    })
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/treg.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:treg:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3c199cd0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3c199cd0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3c199cd0 {
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
impl BoundaryError3c199cd0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3c199cd0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3c199cd0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3c199cd0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3c199cd0> {
        if capacity_bound == 0 {
            return Err(BoundaryError3c199cd0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3c199cd0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3c199cd0::ExceedsCapacity {
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
mod treg_batch_checks {
    use super::try_treg_batch;
    #[test]
    fn one_zero_defect_and_one_positive_defect_split_the_batch() {
        let batch = try_treg_batch(&[(0, true), (3, true)]);
        assert_eq!(batch.as_ref().map(|item| item.examined), Ok(2));
        assert_eq!(batch.as_ref().map(|item| item.suppressive), Ok(1));
        assert_eq!(batch.as_ref().map(|item| item.permissive), Ok(1));
    }
}

#[cfg(test)]
mod l4_boundary_tests_3c199cd0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3c199cd0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3c199cd0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3c199cd0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3c199cd0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3c199cd0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError3c199cd0::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError3c199cd0::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
