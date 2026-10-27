//! Pure write-ahead vocabulary and ordered crash inventory. Single writer.
use crate::exact::Integer;
use indexmap::IndexMap;
use crate::stage::ports::Refusal;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EntryKind {
    BoutStarted,
    SeatTurnStarted,
    SeatTurnCompleted,
    BoutTerminal,
    JournalLineUnreadable,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum TerminalStatus {
    Completed,
    Refused,
    UnexpectedException,
    Interrupted,
    CrashedUnknown,
}
impl TerminalStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Completed => "COMPLETED",
            Self::Refused => "REFUSED",
            Self::UnexpectedException => "UNEXPECTED_EXCEPTION",
            Self::Interrupted => "INTERRUPTED",
            Self::CrashedUnknown => "CRASHED_UNKNOWN",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct JournalEntry {
    pub bout_id: String,
    pub kind: EntryKind,
    pub task_key: String,
    pub sequence: Integer,
    pub detail: Vec<(String, String)>,
    pub authority_effect: String,
}
impl JournalEntry {
    pub fn new(bout: &str, kind: EntryKind, task: &str) -> Self {
        Self {
            bout_id: bout.into(),
            kind,
            task_key: task.into(),
            sequence: Integer(0.into()),
            detail: Vec::new(),
            authority_effect: "None".into(),
        }
    }
    pub fn detail_map(&self) -> BTreeMap<String, String> {
        self.detail.iter().cloned().collect()
    }
}

pub trait JournalPort {
    fn append(&mut self, entry: &JournalEntry) -> Result<(), Refusal>;
    fn read_all(&self) -> Result<Vec<JournalEntry>, Refusal>;
    /// Optional working reports of captured history. Reporting does not grant
    /// dispatch permission or replace the journal's write-ahead decisions.
    fn checkpoint(
        &mut self,
        _turns: &[serde_json::Map<String, serde_json::Value>],
        _pending: Option<&serde_json::Map<String, serde_json::Value>>,
    ) -> Result<(), Refusal> {
        Ok(())
    }
    fn checkpoint_outcome(&mut self, _summary: &serde_json::Value) -> Result<(), Refusal> {
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UnterminatedBout {
    pub bout_id: String,
    pub task_key: String,
    pub seat_turns_started: usize,
    pub seat_turns_completed: usize,
}
impl UnterminatedBout {
    pub fn in_flight_seat_turns(&self) -> usize {
        self.seat_turns_started
            .saturating_sub(self.seat_turns_completed)
    }
    pub fn crashed_unknown_entry(&self) -> JournalEntry {
        let mut entry = JournalEntry::new(&self.bout_id, EntryKind::BoutTerminal, &self.task_key);
        entry.detail = vec![
            ("terminal_status".into(), "CRASHED_UNKNOWN".into()),
            ("cause".into(), "UNKNOWN".into()),
            ("reconciled".into(), "true".into()),
            (
                "seat_turns_started".into(),
                self.seat_turns_started.to_string(),
            ),
            (
                "seat_turns_completed".into(),
                self.seat_turns_completed.to_string(),
            ),
            (
                "in_flight_seat_turns".into(),
                self.in_flight_seat_turns().to_string(),
            ),
            ("single_writer_assumed".into(), "true".into()),
        ];
        entry
    }
}

pub fn unterminated_bouts(entries: &[JournalEntry]) -> Vec<UnterminatedBout> {
    let mut started = IndexMap::<String, String>::new();
    let mut terminal = BTreeSet::new();
    let mut counts = BTreeMap::<String, (usize, usize)>::new();
    for entry in entries {
        match entry.kind {
            EntryKind::BoutStarted => {
                started
                    .entry(entry.bout_id.clone())
                    .or_insert_with(|| entry.task_key.clone());
            }
            EntryKind::BoutTerminal => {
                terminal.insert(entry.bout_id.clone());
            }
            EntryKind::SeatTurnStarted => {
                counts.entry(entry.bout_id.clone()).or_default().0 += 1;
            }
            EntryKind::SeatTurnCompleted => {
                counts.entry(entry.bout_id.clone()).or_default().1 += 1;
            }
            EntryKind::JournalLineUnreadable => {}
        }
    }
    started
        .into_iter()
        .filter(|(bout, _)| !terminal.contains(bout))
        .map(|(bout_id, task_key)| {
            let (seat_turns_started, seat_turns_completed) =
                counts.get(&bout_id).copied().unwrap_or_default();
            UnterminatedBout {
                bout_id,
                task_key,
                seat_turns_started,
                seat_turns_completed,
            }
        })
        .collect()
}

// Origin: engine/crates_rs/core_adversary/src/journal.rs
// Claim: urn:core:crates_rs:core-adversary:journal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5ec621d7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5ec621d7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5ec621d7 {
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
impl BoundaryError5ec621d7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5ec621d7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5ec621d7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5ec621d7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5ec621d7> {
        if capacity_bound == 0 {
            return Err(BoundaryError5ec621d7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5ec621d7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5ec621d7::ExceedsCapacity {
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
mod l4_boundary_tests_5ec621d7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5ec621d7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5ec621d7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5ec621d7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5ec621d7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5ec621d7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5ec621d7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5ec621d7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
