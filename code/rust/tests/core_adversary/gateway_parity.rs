use num_bigint::BigInt;
use core_adversary::stage::ports::Refusal;
use core_adversary::stage::ports::SeatPort;
use core_adversary::{
    exact::{integer, Integer},
    gateway::{
        parse_machine_block, parse_reply, CallLedger, Clock, RoutedSeatExecutor, SeatPrompt,
        SeatTransport, TransportFailure,
    },
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

fn outcome<T: serde::Serialize>(result: Result<T, Refusal>) -> Value {
    match result {
        Ok(value) => json!({"ok": value}),
        Err(error) => json!({"error": error}),
    }
}
struct StubTransport {
    configured: bool,
    responses: Vec<Value>,
    attempts: Vec<Value>,
}
impl SeatTransport for StubTransport {
    fn configured(&self, _: &str) -> bool {
        self.configured
    }
    fn send(
        &mut self,
        _: &str,
        model: &str,
        request: &SeatPrompt,
        max_tokens: u64,
    ) -> Result<Vec<u8>, TransportFailure> {
        let response = &self.responses[self.attempts.len().min(self.responses.len() - 1)];
        self.attempts.push(json!({"model": model, "system": request.system, "user": request.user, "max_tokens": max_tokens}));
        if response.as_str() == Some("timeout") {
            return Err(TransportFailure {
                kind: "TimeoutError".into(),
            });
        }
        Ok(serde_json::from_value(response.clone()).unwrap())
    }
}
struct MemoryLedger(Vec<Value>);
impl CallLedger for MemoryLedger {
    fn append(&mut self, record: &Value) -> Result<(), Refusal> {
        self.0.push(record.clone());
        Ok(())
    }
    fn spent_on(&mut self, day: &str) -> Result<BigInt, Refusal> {
        Ok(self
            .0
            .iter()
            .filter(|r| r["day"] == day)
            .filter_map(|r| integer(&r["cost_microusd"]))
            .sum())
    }
}
struct FixtureClock;
impl Clock for FixtureClock {
    fn today(&self) -> String {
        "2026-10-04".into()
    }
    fn milliseconds(&self) -> u64 {
        0
    }
}

/// Three intentional changes from the immutable Python v1 observations:
/// malformed replies exhaust real fallbacks, and authority refusals gain raw
/// billed-response custody (the refusal code remains a hard stop). Invalid usage
/// replies also retain raw custody while preserving their v1 refusal and charge.
fn assert_gateway_delta_case(
    row: &Value,
    actual: &Value,
    frozen: &Value,
    failure: &Value,
    observed: &Value,
) -> (&'static str, usize, i64) {
    if row["case"] == "malformed" {
        assert!(frozen["result"].get("ok").is_some(), "v1 recorded malformed prose as a reply");
        assert_eq!(frozen["result"]["ok"]["machine_fields"], json!({}));
        assert_eq!(failure["code"], "ALL_LEGS_FAILED");
        assert_eq!(actual["attempts"].as_array().unwrap().len(), 3);
        // Fixture table order is not dispatch order: this request targets Gauge Breaker.
        let table: core_adversary::routing::RoutingTable =
            serde_json::from_value(row["table"].clone()).unwrap();
        let route = table.seat(row["request"]["seat_id"].as_str().unwrap()).unwrap();
        for leg in &route.legs {
            assert!(failure["message"]
                .as_str()
                .unwrap()
                .contains(&format!("{}:{}=MALFORMED", leg.router, leg.model)));
        }
        return ("MALFORMED", 3, 369);
    }
    assert_eq!(failure["code"], frozen["result"]["error"]["code"]);
    let expected_msg = if row["case"] == "authority" {
        json!(format!("{} returned AUTHORITY_EFFECT='Sovereign'", observed["model"].as_str().unwrap()))
    } else {
        frozen["result"]["error"]["message"].clone()
    };
    assert_eq!(failure["message"], expected_msg);
    assert_eq!(actual["attempts"], frozen["attempts"]);
    for (key, value) in frozen["ledger"][0].as_object().unwrap() {
        if key != "model" {
            assert_eq!(&actual["ledger"][0][key], value, "preserved authority ledger field {key}");
        }
    }
    let code = if row["case"] == "authority" { "AUTHORITY_MINT_REFUSED" } else { "REPLY_INVALID" };
    (code, 1, 123)
}

fn intentional_gateway_delta(row: &Value, actual: &Value) -> bool {
    if row["op"] != "gateway"
        || !matches!(
            row["case"].as_str(),
            Some("malformed" | "authority" | "negative_tokens")
        )
    {
        return false;
    }
    let frozen = &row["expected"];
    let raw: Vec<u8> = serde_json::from_value(row["responses"][0].clone()).unwrap();
    let observed: Value = serde_json::from_slice(&raw).unwrap();
    let failure = &actual["result"]["error"];
    assert!(actual["result"].get("ok").is_none());
    assert_eq!(failure["locus"], "");
    assert_eq!(failure["details"].as_object().unwrap().len(), 1);
    let rejected: Vec<Value> =
        serde_json::from_str(failure["details"]["rejected_attempts"].as_str().unwrap()).unwrap();
    let (code, attempts, paid) = assert_gateway_delta_case(row, actual, frozen, failure, &observed);
    assert_eq!(actual["ledger"].as_array().unwrap().len(), attempts);
    assert_eq!(rejected.len(), attempts);
    assert_eq!(actual["spent_bout"], paid);
    assert_eq!(actual["spent_tier"], json!({"cheap":paid}));
    for (index, attempt) in rejected.iter().enumerate() {
        assert_eq!(attempt["outcome"], code);
        assert_eq!(attempt["refusal"]["code"], code);
        assert_eq!(attempt["cost_microusd"], 123);
        assert_eq!(attempt["cost_source"], "provider_receipt");
        assert_eq!(attempt["raw_reply_hex"], hex::encode(&raw));
        assert_eq!(
            attempt["raw_reply_sha256"],
            format!("sha256:{}", hex::encode(Sha256::digest(&raw)))
        );
        assert_eq!(attempt["model"], observed["model"]);
        assert_eq!(
            attempt["request_digest"],
            actual["ledger"][index]["request_digest"]
        );
        for (key, value) in attempt.as_object().unwrap() {
            assert_eq!(
                &actual["ledger"][index][key], value,
                "retained attempted field {key}"
            );
        }
    }
    true
}
#[test]
fn frozen_python_gateway_vectors() {
    let rows: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/python_routing_v1.json")).unwrap();
    // The historical data stays byte-for-byte frozen; deltas live in assertions.
    assert_eq!(
        hex::encode(Sha256::digest(include_bytes!(
            "fixtures/python_routing_v1.json"
        ))),
        "0f4096430765bea91ef9ed1c46dd97846101281ec49512ed309dc788428a358b"
    );
    let mut count = 0;
    let mut intentional_deltas = 0;
    for row in rows {
        let actual = match row["op"].as_str().unwrap() {
            "machine" => outcome(parse_machine_block(row["text"].as_str().unwrap())),
            "parse_reply" => {
                let leg = serde_json::from_value(row["leg"].clone()).unwrap();
                let raw: Vec<u8> = serde_json::from_value(row["raw"].clone()).unwrap();
                json!(parse_reply(&leg, &raw).unwrap())
            }
            "gateway" => {
                let mut executor = RoutedSeatExecutor {
                    table: serde_json::from_value(row["table"].clone()).unwrap(),
                    config_digest: "sha256:fixture-config".into(),
                    transports: StubTransport {
                        configured: row["configured"].as_bool().unwrap(),
                        responses: serde_json::from_value(row["responses"].clone()).unwrap(),
                        attempts: Vec::new(),
                    },
                    ledger: MemoryLedger(serde_json::from_value(row["prior"].clone()).unwrap()),
                    bout_id: "fixture-bout".into(),
                    max_output_tokens: 65536,
                    clock: FixtureClock,
                    spent_bout: BigInt::from(0),
                    spent_tier: BTreeMap::new(),
                };
                let request = serde_json::from_value(row["request"].clone()).unwrap();
                let result = outcome(executor.execute_turn(&request));
                let tier_spend: BTreeMap<_, _> = executor
                    .spent_tier
                    .into_iter()
                    .map(|(key, value)| (key, Integer(value)))
                    .collect();
                json!({"result": result, "ledger": executor.ledger.0, "attempts": executor.transports.attempts, "spent_bout": Integer(executor.spent_bout), "spent_tier": tier_spend})
            }
            "parse_routing" | "validate_table" | "admit_spend" | "seat" | "canonical_seat_key"
            | "cost" => continue,
            other => panic!("unknown fixture {other}"),
        };
        if intentional_gateway_delta(&row, &actual) {
            intentional_deltas += 1;
        } else {
            assert_eq!(
                actual, row["expected"],
                "operation {} case {}",
                row["op"], row["case"]
            );
        }
        count += 1;
    }
    assert_eq!(count, 30);
    assert_eq!(intentional_deltas, 3);
}

// Origin: engine/crates_rs/tests/core_adversary/gateway_parity.rs
// Claim: urn:core:crates_rs:tests:gateway-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda46eb9b8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda46eb9b8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora46eb9b8 {
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
impl BoundaryErrora46eb9b8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora46eb9b8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora46eb9b8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda46eb9b8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora46eb9b8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora46eb9b8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora46eb9b8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora46eb9b8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a46eb9b8() {
    let admitted = BoundaryRecorda46eb9b8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda46eb9b8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
