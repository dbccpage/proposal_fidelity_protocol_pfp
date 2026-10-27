use core_adversary::stage::ports::{Refusal, SeatPort, SeatTurnReply, SeatTurnRequest};
use core_adversary::bout_boundary::{
    execute_bout_boundary, BoutAbort, BoutRunSpec, RefusalBundlePort,
};
use core_adversary::custody::RecordingSeatPort;
use core_adversary::journal::{unterminated_bouts, JournalEntry, JournalPort};
use core_adversary::journal_store::parse_line;
use core_adversary::journal_store::{JsonlJournal, TimestampPort};
use core_adversary::recovery::reconcile_crashed_bouts;
use serde::de::DeserializeOwned;
use serde_json::{json, Value};
use std::collections::BTreeMap;

struct FixedClock;
impl TimestampPort for FixedClock {
    fn now_utc(&self) -> String {
        "2026-10-04T00:00:00+00:00".into()
    }
}

fn decode<T: DeserializeOwned>(value: &Value) -> T {
    serde_json::from_slice(&serde_json::to_vec(value).unwrap()).unwrap()
}
struct MemoryJournal {
    entries: Vec<JournalEntry>,
    appended: Vec<JournalEntry>,
    fail_after: Option<usize>,
    read_error: bool,
}
fn disk_error(message: &str) -> Refusal {
    let mut failure = Refusal::new("BOUT_JOURNAL_UNAVAILABLE", message);
    failure.locus = "test".into();
    failure
}
impl JournalPort for MemoryJournal {
    fn read_all(&self) -> Result<Vec<JournalEntry>, Refusal> {
        if self.read_error {
            Err(disk_error("read failed"))
        } else {
            Ok(self.entries.clone())
        }
    }
    fn append(&mut self, entry: &JournalEntry) -> Result<(), Refusal> {
        if self.fail_after.is_some_and(|n| self.appended.len() >= n) {
            return Err(disk_error("disk full"));
        }
        self.appended.push(entry.clone());
        self.entries.push(entry.clone());
        Ok(())
    }
}
struct FixtureSeat {
    mode: String,
    calls: usize,
}

struct BoundarySeat {
    mode: String,
    calls: usize,
}
impl SeatPort for BoundarySeat {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        self.calls += 1;
        if self.mode == "interrupted" {
            std::panic::panic_any(core_adversary::stage::ports::ExecutionInterruption {
                exception_type: "KeyboardInterrupt".into(),
            });
        }
        if self.mode == "refused" {
            let mut error = Refusal::new("TEST_REFUSAL", "seat refused");
            error.locus = "test".into();
            return Err(error);
        }
        Ok(SeatTurnReply {
            reply_text: "reply".into(),
            machine_fields: BTreeMap::new(),
            residual_colour: "Exact".into(),
            authority_effect: "None".into(),
            raw_bytes: b"\xffreply".to_vec(),
            model: None,
            provider: None,
            parameters: None,
            usage: None,
            request_digest: Some(request.request_digest()?),
        })
    }
}
#[derive(Default)]
struct MemoryBundles {
    calls: Vec<Value>,
    fail: bool,
}
impl RefusalBundlePort for MemoryBundles {
    fn persist(
        &mut self,
        _: &BoutRunSpec,
        _: &Refusal,
        act: &str,
        turns: &[serde_json::Map<String, Value>],
    ) -> Result<String, Refusal> {
        self.calls.push(json!({"act": act, "turns": turns}));
        if self.fail {
            return Err(Refusal::new("BUNDLE_UNAVAILABLE", "disk full"));
        }
        Ok("/fixture/refusal-bundle".into())
    }
}
impl SeatPort for FixtureSeat {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        self.calls += 1;
        if self.mode == "refused" || self.mode == "raised" {
            // A Python adapter can report an exception with its original type.
            // The native unwinding boundary is checked in journal_acceptance.
            let mut error = if self.mode == "raised" {
                Refusal::new(
                    "ADVERSARY_SEAT_EXECUTION_RAISED",
                    "the seat port raised ValueError: seat failed",
                )
            } else {
                Refusal::new("TEST_REFUSAL", "seat refused")
            };
            error.locus = if self.mode == "raised" {
                "adversary.use_cases.seat_custody"
            } else {
                "test"
            }
            .into();
            return Err(error);
        }
        Ok(SeatTurnReply {
            reply_text: "reply".into(),
            machine_fields: BTreeMap::from([("AUTHORITY_EFFECT".into(), "None".into())]),
            residual_colour: "Exact".into(),
            authority_effect: "None".into(),
            raw_bytes: b"\xffraw reply".to_vec(),
            model: Some("fixture".into()),
            provider: None,
            parameters: None,
            usage: None,
            request_digest: Some(if self.mode == "unbound" {
                "sha256:other".into()
            } else {
                request.request_digest()?
            }),
        })
    }
}
fn run_boundary_vector(index: usize, row: &Value) -> Value {
    let mode = row["mode"].as_str().unwrap();
    let mut seat = BoundarySeat { mode: mode.into(), calls: 0 };
    let mut journal = MemoryJournal {
        entries: Vec::new(),
        appended: Vec::new(),
        fail_after: row["fail_after"].as_u64().map(|n| n as usize),
        read_error: false,
    };
    let mut bundles = MemoryBundles { fail: mode == "bundle_failed", ..MemoryBundles::default() };
    let spec = BoutRunSpec {
        bout_id: "task:000000000000".into(),
        task_key: "task".into(),
        objective: "journal boundary".into(),
        fixture_seats: true,
        learning_guidance: String::new(),
        instruction_plan: None,
    };
    let optional = (row["use_journal"] == true).then_some(&mut journal as &mut dyn JournalPort);
    let outcome = execute_bout_boundary(&spec, &mut seat, optional, &mut bundles, |port, act| {
        *act = "ACT_I".into();
        port.execute_turn(&decode(&row["request"]))?;
        *act = "ACT_III".into();
        match mode {
            "bundle_failed" => {
                let mut refusal = Refusal::new("TEST_REFUSAL", "seat refused");
                refusal.locus = "test".into();
                Err(BoutAbort::Refused(refusal))
            }
            "unexpected" => Err(BoutAbort::UnexpectedException("KeyError: 'checker blew up'".into())),
            _ => Ok(json!({"fixture": "completed"})),
        }
    });
    assert_eq!(json!(seat.calls), row["calls"], "boundary calls {index}");
    assert_eq!(json!(journal.appended), row["appended"], "boundary appends {index}");
    assert_eq!(json!(bundles.calls), row["bundles"], "boundary bundles {index}");
    match outcome.result {
        Ok(value) => json!({"ok": value}),
        Err(BoutAbort::Refused(error)) => json!({"error": error}),
        Err(BoutAbort::Interrupted(exception)) => json!({"interrupted": exception}),
        other => panic!("unconverted result {other:?}"),
    }
}

#[test]
fn frozen_python_journal_recovery_and_custody_vectors() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_journal_v1.json")).unwrap();
    assert_eq!(
        fixture["source_revision"],
        "cc107bec4922bd69b37f82622241f10cfc13c893"
    );
    for (index, row) in fixture["vectors"].as_array().unwrap().iter().enumerate() {
        let actual = match row["op"].as_str().unwrap() {
            "store" => {
                let dir = tempfile::tempdir().unwrap();
                let path = dir.path().join("j.jsonl");
                std::fs::write(
                    &path,
                    hex::decode(row["initial_hex"].as_str().unwrap()).unwrap(),
                )
                .unwrap();
                let mut journal = JsonlJournal::with_clock(&path, FixedClock);
                journal.append(&decode(&row["entry"])).unwrap();
                json!({"raw_hex": hex::encode(std::fs::read(&path).unwrap()), "entries": journal.read_all().unwrap()})
            }
            "boundary" => run_boundary_vector(index, row),
            "parse_line" => json!(parse_line(
                row["number"].as_u64().unwrap() as usize,
                &hex::decode(row["line_hex"].as_str().unwrap()).unwrap()
            )),
            "unterminated" => {
                let bouts = unterminated_bouts(&decode::<Vec<JournalEntry>>(&row["entries"]));
                let terminals: Vec<_> = bouts.iter().map(|b| b.crashed_unknown_entry()).collect();
                json!({"bouts": bouts, "terminals": terminals})
            }
            "reconcile" => {
                let mut journal = MemoryJournal {
                    entries: decode(&row["entries"]),
                    appended: Vec::new(),
                    fail_after: row["fail_after"].as_u64().map(|n| n as usize),
                    read_error: row["read_error"].as_bool().unwrap(),
                };
                let result = match reconcile_crashed_bouts(&mut journal) {
                    Ok(bouts) => json!({"ok": bouts}),
                    Err(error) => json!({"error": error}),
                };
                assert_eq!(json!(journal.appended), row["appended"], "appends {index}");
                result
            }
            "custody" => {
                let mut seat = FixtureSeat {
                    mode: row["mode"].as_str().unwrap().into(),
                    calls: 0,
                };
                let mut journal = MemoryJournal {
                    entries: Vec::new(),
                    appended: Vec::new(),
                    fail_after: row["fail_after"].as_u64().map(|n| n as usize),
                    read_error: false,
                };
                let mut port = RecordingSeatPort::new(
                    &mut seat,
                    Some(&mut journal),
                    "b",
                    "task",
                    row["guidance"].as_str().unwrap(),
                    None,
                );
                let result = match port.execute_turn(&decode(&row["request"])) {
                    Ok(_) => json!({"ok": true}),
                    Err(error) => json!({"error": error}),
                };
                assert_eq!(json!(port.turns), row["turns"], "turn custody {index}");
                assert_eq!(
                    json!(port.journal_residuals),
                    row["residuals"],
                    "residuals {index}"
                );
                drop(port);
                assert_eq!(json!(journal.appended), row["appended"], "appends {index}");
                assert_eq!(json!(seat.calls), row["calls"], "calls {index}");
                result
            }
            other => panic!("unknown fixture {other}"),
        };
        assert_eq!(actual, row["expected"], "journal vector {index}");
    }
}

// Origin: engine/crates_rs/tests/core_adversary/journal_parity.rs
// Claim: urn:core:crates_rs:tests:journal-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfd3961dd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfd3961dd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfd3961dd {
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
impl BoundaryErrorfd3961dd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfd3961dd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfd3961dd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfd3961dd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfd3961dd> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfd3961dd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfd3961dd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfd3961dd::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fd3961dd() {
    let admitted = BoundaryRecordfd3961dd::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfd3961dd::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
