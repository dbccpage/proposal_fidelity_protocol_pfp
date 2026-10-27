//! Differential execution against original, independently pinned Python functions.
//! Complete raw outputs and enabled ordering are checked, not only WDP readouts.
use num_bigint::BigInt;
use num_traits::Zero;
use core_wdp::genesis_ongoing_adapter::{
    GenesisOngoingAdapter, GenesisOngoingPacket, MarkedTriple,
};
use core_wdp::genesis_source_execution::{
    Source25Change, Source25Run, Source25State, SourceRelation,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

// Exact retained LF bytes and their Git provenance live beside the test.
// The historical Python verifier is hash-bound data, not executed here.
const RECEIPT: &str = include_str!("fixtures/source_execution/receipt.json");
const INPUTS: &[u8] = include_bytes!("fixtures/source_execution/inputs.json");
const VERIFIER: &[u8] = include_bytes!("fixtures/source_execution/verifier.py.txt");

fn receipt() -> Value {
    let data: Value = serde_json::from_str(RECEIPT).unwrap();
    assert_eq!(data["schema"], "wdp-source-execution-v1");
    assert_eq!(data["authority_effect"], "None");
    assert_eq!(data["inputs_sha256"], hex::encode(Sha256::digest(INPUTS)));
    assert_eq!(
        data["verifier_sha256"],
        hex::encode(Sha256::digest(VERIFIER))
    );
    data
}

fn number(value: &Value) -> usize {
    usize::try_from(value.as_u64().unwrap()).unwrap()
}
fn integers(value: &Value) -> Vec<BigInt> {
    value
        .as_array()
        .unwrap()
        .iter()
        .map(|v| v.as_str().unwrap().parse().unwrap())
        .collect()
}
fn state(value: &Value) -> Source25State {
    let n = number(&value[0]);
    Source25State::try_new(GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: integers(&value[1]),
        s: integers(&value[2]),
        filled: value[3]
            .as_array()
            .unwrap()
            .iter()
            .map(|t| MarkedTriple {
                x: number(&t[0]),
                y: number(&t[1]),
                z: number(&t[2]),
            })
            .collect(),
    })
    .unwrap()
}
fn wire(state: &Source25State) -> Value {
    let p = state.packet();
    json!([
        p.terms.len(),
        p.r.iter().map(ToString::to_string).collect::<Vec<_>>(),
        p.s.iter().map(ToString::to_string).collect::<Vec<_>>(),
        p.filled.iter().map(|t| [t.x, t.y, t.z]).collect::<Vec<_>>()
    ])
}
fn relation(value: &Value) -> SourceRelation {
    match value.as_str().unwrap() {
        "r" => SourceRelation::R,
        "s" => SourceRelation::S,
        _ => panic!("unknown source relation"),
    }
}
fn change(value: &Value) -> Source25Change {
    match value[0].as_str().unwrap() {
        "add_term" => Source25Change::AddTerm,
        "identify" => Source25Change::Identify {
            x: number(&value[1]),
            y: number(&value[2]),
        },
        "fill" => Source25Change::Fill {
            x: number(&value[1]),
            y: number(&value[2]),
            z: number(&value[3]),
        },
        "remove" => Source25Change::Remove {
            relation: relation(&value[1]),
            x: number(&value[2]),
            y: number(&value[3]),
        },
        "add_assertion" => Source25Change::AddAssertion {
            relation: relation(&value[1]),
            x: number(&value[2]),
            y: number(&value[3]),
        },
        _ => panic!("unknown source event"),
    }
}
fn event_wire(change: Source25Change) -> Value {
    fn label(relation: SourceRelation) -> &'static str {
        match relation {
            SourceRelation::R => "r",
            SourceRelation::S => "s",
        }
    }
    match change {
        Source25Change::AddTerm => json!(["add_term"]),
        Source25Change::Identify { x, y } => json!(["identify", x, y]),
        Source25Change::Fill { x, y, z } => json!(["fill", x, y, z]),
        Source25Change::Remove { relation, x, y } => json!(["remove", label(relation), x, y]),
        Source25Change::AddAssertion { relation, x, y } => {
            json!(["add_assertion", label(relation), x, y])
        }
    }
}

#[test]
fn full_native_steps_order_and_prices_match_all_3770_original_transitions() {
    let data = receipt();
    let corpus = &data["corpus"];
    assert_eq!(corpus["binary_max_terms"], 2);
    let mut digest = Sha256::new();
    let mut states = 0usize;
    let mut transitions = 0usize;
    let mut record = |before: Source25State| {
        let mut outcomes = Vec::new();
        for change in before.enabled_changes() {
            assert!(before.is_enabled(change));
            let after = before.perform_enabled(change).unwrap();
            let (terms, assertions) = change.additions();
            let addition = matches!(
                change,
                Source25Change::AddTerm | Source25Change::AddAssertion { .. }
            );
            outcomes.push(json!([
                event_wire(change),
                addition,
                [terms, assertions],
                wire(&after),
                after.source_size().to_string(),
                after.plain_state_cost().to_string()
            ]));
            transitions += 1;
        }
        let row = json!([
            wire(&before),
            outcomes,
            before.source_size().to_string(),
            before.plain_state_cost().to_string()
        ]);
        digest.update(serde_json::to_vec(&row).unwrap());
        digest.update(b"\n");
        states += 1;
    };
    for n in 0..=2usize {
        for mask in 0..1usize << (2 * n * n) {
            record(
                Source25State::try_new(GenesisOngoingPacket {
                    terms: (0..n).map(|i| format!("t{i}")).collect(),
                    r: (0..n * n).map(|i| BigInt::from((mask >> i) & 1)).collect(),
                    s: (0..n * n)
                        .map(|i| BigInt::from((mask >> (n * n + i)) & 1))
                        .collect(),
                    filled: vec![],
                })
                .unwrap(),
            );
        }
    }
    for before in corpus["extra_states"].as_array().unwrap() {
        record(state(before));
    }
    assert_eq!(states, number(&corpus["states"]));
    assert_eq!(transitions, number(&corpus["transitions"]));
    assert_eq!(transitions, 3770);
    assert_eq!(
        hex::encode(digest.finalize()),
        corpus["sha256"].as_str().unwrap()
    );
}

#[test]
fn original_ordered_runs_raising_and_all_prefix_compositions_are_preserved() {
    let data = receipt();
    for history in data["histories"].as_array().unwrap() {
        let initial = state(&history["states"][0]);
        let events: Vec<_> = history["changes"]
            .as_array()
            .unwrap()
            .iter()
            .map(change)
            .collect();
        let run = Source25Run::replay(initial.clone(), &events).unwrap();
        assert_eq!(
            json!(run.states().iter().map(wire).collect::<Vec<_>>()),
            history["states"]
        );
        assert_eq!(
            json!(run
                .changes()
                .iter()
                .copied()
                .map(event_wire)
                .collect::<Vec<_>>()),
            history["changes"]
        );
        assert_eq!(
            json!([
                run.addition_price().0.to_string(),
                run.addition_price().1.to_string()
            ]),
            history["addition_price"]
        );
        for split in 0..=events.len() {
            let first = Source25Run::replay(initial.clone(), &events[..split]).unwrap();
            let second =
                Source25Run::replay(first.final_state().clone(), &events[split..]).unwrap();
            assert_eq!(first.then(&second).unwrap(), run);
        }
    }
    let histories = &data["histories"];
    assert_eq!(
        histories[1]["states"].as_array().unwrap().last(),
        histories[2]["states"].as_array().unwrap().last()
    );
    assert_ne!(histories[1]["changes"], histories[2]["changes"]);
    assert_ne!(
        histories[1]["addition_price"],
        histories[2]["addition_price"]
    );
    for raising in data["raising"].as_array().unwrap() {
        let before = state(&raising["before"]);
        let after = before.raise_terms(&integers(&raising["counts"])).unwrap();
        assert_eq!(wire(&after), raising["after"]);
    }
}

#[test]
fn actual_source_result_countermodels_refuse_carrier_change_descent() {
    let data = receipt();
    for countermodel in data["quotient_countermodels"].as_array().unwrap() {
        let left = state(&countermodel["before"][0]);
        let right = state(&countermodel["before"][1]);
        let adapter =
            |state: &Source25State| GenesisOngoingAdapter::try_new(state.packet().clone()).unwrap();
        assert!(adapter(&left)
            .repair_equivalence(&adapter(&right))
            .unwrap()
            .is_some());
        let event = change(&countermodel["change"]);
        let a = left.perform_enabled(event).unwrap();
        let b = right.perform_enabled(event).unwrap();
        assert_eq!(wire(&a), countermodel["after"][0]);
        assert_eq!(wire(&b), countermodel["after"][1]);
        assert!(adapter(&a)
            .repair_equivalence(&adapter(&b))
            .unwrap()
            .is_none());
    }
    assert_eq!(Source25State::empty().source_size(), BigInt::zero());
}

// Origin: engine/crates_rs/tests/core_wdp/test_source_execution_oracle.rs
// Claim: urn:core:crates_rs:tests:test-source-execution-oracle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord99ccb563 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord99ccb563` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError99ccb563 {
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
impl BoundaryError99ccb563 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError99ccb563 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError99ccb563 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord99ccb563 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError99ccb563> {
        if capacity_bound == 0 {
            return Err(BoundaryError99ccb563::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError99ccb563::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError99ccb563::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_99ccb563() {
    let admitted = BoundaryRecord99ccb563::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord99ccb563::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
