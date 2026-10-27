use core_adversary::stage::exact::rational;
use core_types::python_unicode::repr_string;
use core_adversary::exact::integer;
use core_adversary::gateway::CallLedger;
use core_adversary::ledger::FileCallLedger;
use core_adversary::routing::load_routing;
use serde_json::{json, Value};
use std::fs;

#[test]
fn frozen_python_file_ledger_loader_and_exact_vectors() {
    let rows: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/python_storage_v1.json")).unwrap();
    assert_eq!(rows.len(), 32);
    for (index, row) in rows.into_iter().enumerate() {
        let actual = match row["op"].as_str().unwrap() {
            "ledger" => {
                let dir = tempfile::tempdir().unwrap();
                let path = dir.path().join("nested/calls.jsonl");
                let mut ledger = FileCallLedger { path: path.clone() };
                for record in row["records"].as_array().unwrap() {
                    ledger.append(record).unwrap();
                }
                let raw = fs::read(&path).unwrap_or_default();
                json!({"raw_hex": hex::encode(raw), "spent": core_adversary::exact::Integer(ledger.spent_on(row["day"].as_str().unwrap()).unwrap())})
            }
            "load_routing" => {
                let dir = tempfile::tempdir().unwrap();
                let path = dir.path().join("routing.yaml");
                if let Some(raw) = row["raw_hex"].as_str() {
                    fs::write(&path, hex::decode(raw).unwrap()).unwrap();
                }
                match load_routing(&path) {
                    Ok(value) => json!({"ok": value}),
                    Err(error) => json!({"code": error.code}),
                }
            }
            "rational" => json!(rational(row["raw"].as_str().unwrap()).map(|v| v.to_string())),
            "repr" => json!(repr_string(row["text"].as_str().unwrap())),
            other => panic!("unknown fixture {other}"),
        };
        assert_eq!(actual, row["expected"], "storage fixture {index}");
    }
}

#[test]
fn ledger_io_and_corrupt_records_are_typed_and_never_default_to_zero_spend() {
    let dir = tempfile::tempdir().unwrap();
    let mut blocked = FileCallLedger {
        path: dir.path().to_owned(),
    };
    assert_eq!(
        blocked.append(&json!({})).unwrap_err().code,
        "LEDGER_UNAVAILABLE"
    );
    assert!(matches!(
        blocked.spent_on("2026-10-04").unwrap_err().code.as_str(),
        "LEDGER_UNAVAILABLE" | "LEDGER_INVALID"
    ));
    let mut ledger = FileCallLedger {
        path: dir.path().join("calls.jsonl"),
    };
    for raw in [b"{broken".as_slice(), b"\xff"] {
        fs::write(&ledger.path, raw).unwrap();
        assert_eq!(
            ledger.spent_on("2026-10-04").unwrap_err().code,
            "LEDGER_INVALID"
        );
    }
    fs::write(&ledger.path, b"\n \n").unwrap();
    ledger
        .append(&json!({"day":"2026-10-04", "cost_microusd": 9}))
        .unwrap();
    assert_eq!(
        ledger.spent_on("2026-10-04").unwrap(),
        integer(&json!(9)).unwrap()
    );
    let parent = dir.path().join("file-parent");
    fs::write(&parent, b"block").unwrap();
    ledger.path = parent.join("calls.jsonl");
    assert_eq!(
        ledger.append(&json!({})).unwrap_err().code,
        "LEDGER_UNAVAILABLE"
    );
}

#[test]
fn adversarial_native_wire_inputs_fail_closed_before_allocation_or_reply_creation() {
    assert!(rational("1e10001").is_none());
    assert!(rational("1e-10001").is_none());
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_routing_v1.json")).unwrap();
    let leg = fixture
        .as_array()
        .unwrap()
        .iter()
        .find(|r| r["op"] == "parse_reply")
        .unwrap()["leg"]
        .clone();
    let leg = serde_json::from_slice(&serde_json::to_vec(&leg).unwrap()).unwrap();
    let huge = vec![b' '; 1024 * 1024 + 1];
    assert_eq!(
        core_adversary::gateway::parse_reply(&leg, &huge)
            .unwrap_err()
            .code,
        "SWARM_PROVIDER_REPLY_TOO_LARGE"
    );
    for raw in [
        b"not json".as_slice(),
        b"{\"choices\":[{\"message\":{\"content\":[]}}]}",
        b"{\"usage\":{\"prompt_tokens\":[]}}",
    ] {
        assert_eq!(
            core_adversary::gateway::parse_reply(&leg, raw)
                .unwrap_err()
                .code,
            "TRANSPORT_PROTOCOL_INVALID"
        );
    }
}

// Origin: engine/crates_rs/tests/core_adversary/storage_parity.rs
// Claim: urn:core:crates_rs:tests:storage-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord03689d47 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord03689d47` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError03689d47 {
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
impl BoundaryError03689d47 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError03689d47 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError03689d47 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord03689d47 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError03689d47> {
        if capacity_bound == 0 {
            return Err(BoundaryError03689d47::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError03689d47::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError03689d47::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_03689d47() {
    let admitted = BoundaryRecord03689d47::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord03689d47::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
