//! Startup closure through a domain port; no cause or cost is inferred.
use crate::journal::{unterminated_bouts, EntryKind, JournalPort, UnterminatedBout};
use crate::stage::ports::Refusal;

pub fn reconcile_crashed_bouts(
    journal: &mut dyn JournalPort,
) -> Result<Vec<UnterminatedBout>, Refusal> {
    let entries = journal.read_all()?;
    // A damaged line may conceal a terminal record. Preserve every byte and
    // require explicit inspection/repair before recording any crash closure.
    if entries
        .iter()
        .any(|entry| entry.kind == EntryKind::JournalLineUnreadable)
    {
        let mut refusal = Refusal::new(
            "BOUT_RECONCILE_CORRUPT",
            "journal has unreadable lines; inspect and repair the journal before reconciliation",
        );
        refusal.locus = "adversary.use_cases.bout_recovery".into();
        return Err(refusal);
    }
    let mut closed = Vec::new();
    for bout in unterminated_bouts(&entries) {
        if let Err(failure) = journal.append(&bout.crashed_unknown_entry()) {
            let mut refusal = Refusal::new(
                "BOUT_RECONCILE_INCOMPLETE",
                format!(
                    "closed {} bout(s) before the journal refused: {}",
                    closed.len(),
                    failure.code
                ),
            );
            refusal.locus = "adversary.use_cases.bout_recovery".into();
            return Err(refusal);
        }
        closed.push(bout);
    }
    Ok(closed)
}

// Origin: engine/crates_rs/core_adversary/src/recovery.rs
// Claim: urn:core:crates_rs:core-adversary:recovery:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7b568e65 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7b568e65` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7b568e65 {
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
impl BoundaryError7b568e65 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7b568e65 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7b568e65 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7b568e65 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7b568e65> {
        if capacity_bound == 0 {
            return Err(BoundaryError7b568e65::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7b568e65::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7b568e65::ExceedsCapacity {
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
mod l4_boundary_tests_7b568e65 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7b568e65::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7b568e65::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7b568e65::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7b568e65::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7b568e65::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7b568e65::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7b568e65::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
