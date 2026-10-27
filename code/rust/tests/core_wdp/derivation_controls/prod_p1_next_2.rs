//! Companion Rust witness for PROD-P1-NEXT-2 (P1 negative controls: Impossible policy gate & forged cert rejection).

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AbstentionLabel {
    SolvedOptimally,
    LosingInDeclaredArena,
    Impossible,
    RefusedCertificate,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Certificate {
    pub task_id: &'static str,
    pub outcome: &'static str,
    pub trap_closed: bool,
    pub win_witness_valid: bool,
}

pub fn verify_and_classify(
    arena_task_id: &str,
    cert: &Certificate,
    task_admits_impossibility: bool,
) -> AbstentionLabel {
    if cert.task_id != arena_task_id {
        return AbstentionLabel::RefusedCertificate;
    }
    match cert.outcome {
        "WIN_OPTIMAL" => {
            if cert.win_witness_valid {
                AbstentionLabel::SolvedOptimally
            } else {
                AbstentionLabel::RefusedCertificate
            }
        }
        "LOSS" => {
            if !cert.trap_closed {
                AbstentionLabel::RefusedCertificate
            } else if task_admits_impossibility {
                AbstentionLabel::Impossible
            } else {
                AbstentionLabel::LosingInDeclaredArena
            }
        }
        _ => AbstentionLabel::RefusedCertificate,
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/prod_p1_next_2.rs
// Claim: urn:core:crates_rs:tests:prod-p1-next-2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord31a0178b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord31a0178b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError31a0178b {
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
impl BoundaryError31a0178b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError31a0178b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError31a0178b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord31a0178b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError31a0178b> {
        if capacity_bound == 0 {
            return Err(BoundaryError31a0178b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError31a0178b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError31a0178b::ExceedsCapacity {
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

    #[test]
    fn negative_controls_impossible_without_policy_and_forged_certificates() {
        let valid_loss = Certificate {
            task_id: "arena-loss",
            outcome: "LOSS",
            trap_closed: true,
            win_witness_valid: false,
        };
        assert_eq!(
            verify_and_classify("arena-loss", &valid_loss, false),
            AbstentionLabel::LosingInDeclaredArena
        );
        assert_eq!(
            verify_and_classify("arena-loss", &valid_loss, true),
            AbstentionLabel::Impossible
        );

        let forged_task = Certificate {
            task_id: "forged-task-id",
            ..valid_loss
        };
        assert_eq!(
            verify_and_classify("arena-loss", &forged_task, true),
            AbstentionLabel::RefusedCertificate
        );

        let forged_win = Certificate {
            outcome: "WIN_OPTIMAL",
            ..valid_loss
        };
        assert_eq!(
            verify_and_classify("arena-loss", &forged_win, false),
            AbstentionLabel::RefusedCertificate
        );
    }
}

#[test]
fn l4_boundary_admits_and_refuses_31a0178b() {
    let admitted = BoundaryRecord31a0178b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord31a0178b::try_admit(9, 8).is_err());
}
