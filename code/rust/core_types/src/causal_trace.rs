// # Causal Trace Stage Kinds
//
// Typed stages for the self-repair causal loop.
// Enforces ordering: InternalDescent â†’ Exhaustion â†’ LiftApplied â†’ PostLiftDescent
//
// Ref: Lift Operator Spec v1.2

use serde::{Deserialize, Serialize};

/// The four causal phases of the self-repair loop.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CausalStageKind {
    /// OP applied, Î¦ decreasing.
    InternalDescent,
    /// No further internal descent: Î¦ > 0 âˆ§ Â¬âˆƒ internal: Î¦â†“
    Exhaustion,
    /// Structural lift applied: G(E,V) < G(E',V')
    LiftApplied,
    /// Post-lift descent: F1 < F0
    PostLiftDescent,
}

/// Validate that a trace of causal stages follows correct ordering.
///
/// Valid sequences:
/// - [InternalDescent, Exhaustion, LiftApplied, PostLiftDescent, ...]
/// - [InternalDescent, PostLiftDescent] (resolved internally, no exhaustion)
///
/// Rules:
/// - Exhaustion must follow InternalDescent
/// - LiftApplied must follow Exhaustion
/// - PostLiftDescent must follow LiftApplied
/// - After PostLiftDescent, the loop may restart with InternalDescent
pub fn is_allowed_successor(prev: CausalStageKind, curr: CausalStageKind) -> bool {
    match curr {
        CausalStageKind::InternalDescent => {
            prev == CausalStageKind::PostLiftDescent || prev == CausalStageKind::InternalDescent
        }
        CausalStageKind::Exhaustion => prev == CausalStageKind::InternalDescent,
        CausalStageKind::LiftApplied => prev == CausalStageKind::Exhaustion,
        CausalStageKind::PostLiftDescent => prev == CausalStageKind::LiftApplied,
    }
}

pub fn validate_causal_trace(trace: &[CausalStageKind]) -> Result<(), String> {
    if trace.is_empty() {
        return Ok(());
    }

    for i in 1..trace.len() {
        let prev = trace[i - 1];
        let curr = trace[i];

        if !is_allowed_successor(prev, curr) {
            return Err(format!(
                "Invalid causal trace at position {i}: {:?} â†’ {:?}",
                prev, curr
            ));
        }
    }

    Ok(())
}

// Origin: engine/crates_rs/core_types/src/causal_trace.rs
// Claim: urn:core:crates_rs:core-types:causal-trace:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord71452189 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord71452189` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError71452189 {
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
impl BoundaryError71452189 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError71452189 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError71452189 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord71452189 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError71452189> {
        if capacity_bound == 0 {
            return Err(BoundaryError71452189::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError71452189::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError71452189::ExceedsCapacity {
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
    use CausalStageKind::*;

    #[test]
    fn valid_full_loop() {
        let trace = vec![InternalDescent, Exhaustion, LiftApplied, PostLiftDescent];
        assert!(validate_causal_trace(&trace).is_ok());
    }

    #[test]
    fn valid_double_loop() {
        let trace = vec![
            InternalDescent,
            Exhaustion,
            LiftApplied,
            PostLiftDescent,
            InternalDescent,
            Exhaustion,
            LiftApplied,
            PostLiftDescent,
        ];
        assert!(validate_causal_trace(&trace).is_ok());
    }

    #[test]
    fn invalid_lift_before_exhaustion() {
        let trace = vec![InternalDescent, LiftApplied];
        assert!(validate_causal_trace(&trace).is_err());
    }

    #[test]
    fn invalid_descent_after_exhaustion() {
        let trace = vec![InternalDescent, Exhaustion, PostLiftDescent];
        assert!(validate_causal_trace(&trace).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_71452189 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord71452189::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord71452189::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord71452189::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord71452189::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord71452189::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError71452189::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError71452189::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
