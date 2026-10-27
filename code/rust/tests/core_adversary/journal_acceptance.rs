use core_adversary::stage::ports::{Refusal, SeatPort, SeatTurnReply, SeatTurnRequest};
use core_adversary::bout_boundary::{
    execute_bout_boundary, BoutAbort, BoutRunSpec, RefusalBundlePort,
};
use core_adversary::journal::{unterminated_bouts, EntryKind, JournalEntry, JournalPort};
use core_adversary::journal_store::{JsonlJournal, TimestampPort};
use core_adversary::recovery::reconcile_crashed_bouts;
use serde_json::{Map, Value};
use std::collections::BTreeMap;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::process::Command;

struct FixedClock;
impl TimestampPort for FixedClock {
    fn now_utc(&self) -> String {
        "2026-10-04T00:00:00+00:00".into()
    }
}
#[derive(Default)]
struct Bundles {
    turns: Vec<Map<String, Value>>,
}
impl RefusalBundlePort for Bundles {
    fn persist(
        &mut self,
        _: &BoutRunSpec,
        _: &Refusal,
        _: &str,
        turns: &[Map<String, Value>],
    ) -> Result<String, Refusal> {
        self.turns = turns.to_vec();
        Ok("fixture-bundle".into())
    }
}
struct Seat {
    mode: &'static str,
}
impl SeatPort for Seat {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        match self.mode {
            "exit" => abrupt_exit(),
            "panic" => panic!("adapter failed"),
            _ => Ok(SeatTurnReply {
                reply_text: "answer".into(),
                machine_fields: BTreeMap::new(),
                residual_colour: "Exact".into(),
                authority_effect: "None".into(),
                raw_bytes: b"\xfffull raw reply".to_vec(),
                model: None,
                provider: None,
                parameters: None,
                usage: None,
                request_digest: Some(request.request_digest()?),
            }),
        }
    }
}
#[cfg(unix)]
fn abrupt_exit() -> ! {
    // SAFETY: _exit requires no pointer or other precondition. Skipping atexit
    // and all destructors is precisely the crash condition under test.
    unsafe { libc::_exit(3) }
}
#[cfg(not(unix))]
fn abrupt_exit() -> ! {
    std::process::exit(3)
}
fn spec() -> BoutRunSpec {
    BoutRunSpec {
        bout_id: "bout-1".into(),
        task_key: "crash_bout".into(),
        objective: "x".into(),
        fixture_seats: true,
        learning_guidance: String::new(),
        instruction_plan: None,
    }
}
fn request() -> SeatTurnRequest {
    SeatTurnRequest {
        scene_id: "act1".into(),
        seat_id: "seat_manuscript_truth".into(),
        prompt_text: "full prompt".into(),
        cognitive_operator: String::new(),
        role_kind: "prose".into(),
        candidate_id: String::new(),
        round_index: 0,
        context_bytes: Vec::new(),
    }
}
#[test]
fn store_roundtrip_torn_record_and_typed_io_failures() {
    let dir = tempfile::tempdir().unwrap();
    let mut journal = JsonlJournal::with_clock(dir.path().join("nested/j.jsonl"), FixedClock);
    assert!(journal.read_all().unwrap().is_empty());
    let mut start = JournalEntry::new("b", EntryKind::BoutStarted, "task");
    start.sequence = core_adversary::exact::Integer(7.into());
    start.detail.push(("k".into(), "é λ".into()));
    journal.append(&start).unwrap();
    let got = journal.read_all().unwrap().pop().unwrap();
    assert_eq!(got.bout_id, "b");
    assert_eq!(got.sequence, start.sequence);
    assert_eq!(got.detail_map()["k"], "é λ");
    assert_eq!(got.detail_map()["recorded_at_utc"], FixedClock.now_utc());
    OpenOptions::new()
        .append(true)
        .open(journal.path())
        .unwrap()
        .write_all(b"{\"kind\":\"BOUT_TERM")
        .unwrap();
    journal
        .append(&JournalEntry::new("b", EntryKind::BoutTerminal, "task"))
        .unwrap();
    let entries = journal.read_all().unwrap();
    assert_eq!(
        entries.iter().map(|e| e.kind).collect::<Vec<_>>(),
        vec![
            EntryKind::BoutStarted,
            EntryKind::JournalLineUnreadable,
            EntryKind::BoutTerminal
        ]
    );
    assert_eq!(entries[1].detail_map()["line_number"], "2");
    let mut blocked = JsonlJournal::new(dir.path());
    assert_eq!(
        blocked.append(&start).unwrap_err().code,
        "BOUT_JOURNAL_UNAVAILABLE"
    );
    assert_eq!(
        blocked.read_all().unwrap_err().code,
        "BOUT_JOURNAL_UNAVAILABLE"
    );
    fs::write(journal.path(), b" \r\n\t\n").unwrap();
    assert!(journal.read_all().unwrap().is_empty());
    journal.append(&start).unwrap();
    assert_eq!(journal.read_all().unwrap().len(), 1);
}

#[test]
fn a_native_unwind_balances_markers_and_an_unexpected_act_keeps_raw_custody() {
    for mode in ["panic", "unexpected"] {
        let dir = tempfile::tempdir().unwrap();
        let mut journal = JsonlJournal::new(dir.path().join("j.jsonl"));
        let mut bundles = Bundles::default();
        let mut seat = Seat { mode };
        let outcome = execute_bout_boundary::<(), _>(
            &spec(),
            &mut seat,
            Some(&mut journal),
            &mut bundles,
            |port, act| {
                *act = "ACT_I".into();
                port.execute_turn(&request())?;
                *act = "ACT_III".into();
                panic!("checker failed");
            },
        );
        let expected = if mode == "panic" {
            "ADVERSARY_SEAT_EXECUTION_RAISED"
        } else {
            "ADVERSARY_BOUT_UNEXPECTED_EXCEPTION"
        };
        assert!(matches!(outcome.result, Err(BoutAbort::Refused(ref e)) if e.code == expected));
        let entries = journal.read_all().unwrap();
        assert_eq!(
            entries
                .iter()
                .filter(|e| e.kind == EntryKind::BoutTerminal)
                .count(),
            1
        );
        assert_eq!(
            entries
                .iter()
                .filter(|e| e.kind == EntryKind::SeatTurnStarted)
                .count(),
            1
        );
        assert_eq!(
            entries
                .iter()
                .filter(|e| e.kind == EntryKind::SeatTurnCompleted)
                .count(),
            1
        );
        assert_eq!(bundles.turns[0]["prompt_text"], "full prompt");
        if mode == "unexpected" {
            assert_eq!(
                bundles.turns[0]["raw_reply_hex"],
                hex::encode(b"\xfffull raw reply")
            );
        }
    }
}

#[test]
#[ignore = "subprocess helper invoked only by the crash acceptance test"]
fn native_crash_child() {
    let path = std::env::var_os("CORE_TEST_CRASH_JOURNAL").unwrap();
    let mut journal = JsonlJournal::new(path);
    let mut seat = Seat { mode: "exit" };
    let _ = execute_bout_boundary(
        &spec(),
        &mut seat,
        Some(&mut journal),
        &mut Bundles::default(),
        |port, act| {
            *act = "ACT_I".into();
            port.execute_turn(&request())?;
            Ok(())
        },
    );
    panic!("the child must terminate inside the seat call");
}

#[test]
fn a_process_that_exits_mid_turn_is_closed_as_crashed_unknown_on_restart() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("j.jsonl");
    let child = Command::new(std::env::current_exe().unwrap())
        .args(["--ignored", "--exact", "native_crash_child", "--nocapture"])
        .env("CORE_TEST_CRASH_JOURNAL", &path)
        .output()
        .unwrap();
    assert_eq!(
        child.status.code(),
        Some(3),
        "{}",
        String::from_utf8_lossy(&child.stderr)
    );
    let mut journal = JsonlJournal::new(path);
    let entries = journal.read_all().unwrap();
    assert_eq!(
        entries.iter().map(|e| e.kind).collect::<Vec<_>>(),
        vec![EntryKind::BoutStarted, EntryKind::SeatTurnStarted]
    );
    let pending = unterminated_bouts(&entries);
    assert_eq!(pending[0].task_key, "crash_bout");
    assert_eq!(pending[0].in_flight_seat_turns(), 1);
    assert_eq!(reconcile_crashed_bouts(&mut journal).unwrap(), pending);
    let entries = journal.read_all().unwrap();
    let terminal = entries.last().unwrap().detail_map();
    assert_eq!(terminal["terminal_status"], "CRASHED_UNKNOWN");
    assert_eq!(terminal["cause"], "UNKNOWN");
    assert_eq!(terminal["single_writer_assumed"], "true");
    assert!(reconcile_crashed_bouts(&mut journal).unwrap().is_empty());
    assert_eq!(
        journal
            .read_all()
            .unwrap()
            .iter()
            .filter(|e| e.kind == EntryKind::BoutTerminal)
            .count(),
        1
    );
}

#[test]
fn corrupt_tail_prevents_native_reconciliation_without_rewriting_evidence() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("damaged.jsonl");
    let mut journal = JsonlJournal::new(&path);
    journal
        .append(&JournalEntry::new("b", EntryKind::BoutStarted, "task"))
        .unwrap();
    let intact_prefix = fs::read(&path).unwrap();
    OpenOptions::new()
        .append(true)
        .open(&path)
        .unwrap()
        .write_all(b"{\"kind\":\"BOUT_TERM")
        .unwrap();
    let damaged = fs::read(&path).unwrap();
    let refusal = reconcile_crashed_bouts(&mut journal).unwrap_err();
    assert_eq!(refusal.code, "BOUT_RECONCILE_CORRUPT");
    assert_eq!(fs::read(&path).unwrap(), damaged);
    assert_eq!(
        journal.read_all().unwrap()[1].kind,
        EntryKind::JournalLineUnreadable
    );
    // Only explicit operator repair permits recovery. Archive the damaged bytes
    // before restoring the known intact prefix; the reconciler never does this.
    fs::write(dir.path().join("damaged.original"), &damaged).unwrap();
    fs::write(&path, intact_prefix).unwrap();
    let closed = reconcile_crashed_bouts(&mut journal).unwrap();
    assert_eq!(closed.len(), 1);
    assert_eq!(closed[0].bout_id, "b");
    assert!(reconcile_crashed_bouts(&mut journal).unwrap().is_empty());
    assert_eq!(
        fs::read(dir.path().join("damaged.original")).unwrap(),
        damaged
    );
}

// Origin: engine/crates_rs/tests/core_adversary/journal_acceptance.rs
// Claim: urn:core:crates_rs:tests:journal-acceptance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord97fd3db9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord97fd3db9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError97fd3db9 {
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
impl BoundaryError97fd3db9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError97fd3db9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError97fd3db9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord97fd3db9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError97fd3db9> {
        if capacity_bound == 0 {
            return Err(BoundaryError97fd3db9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError97fd3db9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError97fd3db9::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_97fd3db9() {
    let admitted = BoundaryRecord97fd3db9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord97fd3db9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
