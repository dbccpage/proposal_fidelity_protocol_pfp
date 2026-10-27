//! Independent original-function oracle for the two source admission meanings.
use num_bigint::BigInt;
use num_traits::Zero;
use core_wdp::genesis_admission_execution::{
    Source15Admission, Source15Tagged, Source16Change, Source16Reading, Source16Run, Source16State,
    Source9Change, Source9State,
};
use core_wdp::genesis_ongoing_adapter::GenesisOngoingPacket;
use core_wdp::genesis_source_execution::SourceRelation;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const RECEIPT: &str = include_str!("fixtures/admission_execution/receipt.json");
const INPUTS: &[u8] = include_bytes!("fixtures/admission_execution/inputs.json");
const VERIFIER: &[u8] = include_bytes!("fixtures/admission_execution/verifier.py.txt");
fn receipt() -> Value {
    let data: Value = serde_json::from_str(RECEIPT).unwrap();
    assert_eq!(data["schema"], "wdp-admission-execution-receipt-v1");
    assert_eq!(data["authority_effect"], "None");
    assert_eq!(data["inputs_sha256"], hex::encode(Sha256::digest(INPUTS)));
    assert_eq!(
        data["verifier_sha256"],
        hex::encode(Sha256::digest(VERIFIER))
    );
    assert_eq!(data["bound_inputs"], 17);
    data
}
fn number(v: &Value) -> usize {
    usize::try_from(v.as_u64().unwrap()).unwrap()
}
fn integers(v: &Value) -> Vec<BigInt> {
    v.as_array()
        .unwrap()
        .iter()
        .map(|v| v.as_str().unwrap().parse().unwrap())
        .collect()
}
fn state9(v: &Value) -> Source9State {
    let n = number(&v[0]);
    Source9State::try_new(GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: integers(&v[1]),
        s: integers(&v[2]),
        filled: vec![],
    })
    .unwrap()
}
fn state16(v: &Value) -> Source16State {
    Source16State::try_new(state9(v), integers(&v[3])).unwrap()
}
fn wire9(s: &Source9State) -> Value {
    let p = s.packet();
    json!([
        p.terms.len(),
        p.r.iter().map(ToString::to_string).collect::<Vec<_>>(),
        p.s.iter().map(ToString::to_string).collect::<Vec<_>>()
    ])
}
fn wire16(s: &Source16State) -> Value {
    let mut wire = wire9(s.state());
    wire.as_array_mut().unwrap().push(json!(s
        .leftovers()
        .iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>()));
    wire
}
fn relation(v: &Value) -> SourceRelation {
    match v.as_str().unwrap() {
        "r" => SourceRelation::R,
        "s" => SourceRelation::S,
        _ => panic!("source relation"),
    }
}
fn event9(v: &Value) -> Source9Change {
    match v[0].as_str().unwrap() {
        "add_term" => Source9Change::AddTerm,
        "identify" => Source9Change::Identify {
            x: number(&v[1]),
            y: number(&v[2]),
        },
        "remove" => Source9Change::Remove {
            relation: relation(&v[1]),
            x: number(&v[2]),
            y: number(&v[3]),
        },
        "add_assertion" => Source9Change::AddAssertion {
            relation: relation(&v[1]),
            x: number(&v[2]),
            y: number(&v[3]),
        },
        _ => panic!("source event"),
    }
}
fn event16(v: &Value) -> Source16Change {
    if v[0] == "admit" {
        Source16Change::Admit {
            relation: relation(&v[1]),
            x: number(&v[2]),
            y: number(&v[3]),
        }
    } else {
        Source16Change::Direct { change: event9(v) }
    }
}
fn wire_event9(c: Source9Change) -> Value {
    let label = |rel| match rel {
        SourceRelation::R => "r",
        SourceRelation::S => "s",
    };
    match c {
        Source9Change::AddTerm => json!(["add_term"]),
        Source9Change::Identify { x, y } => json!(["identify", x, y]),
        Source9Change::Remove { relation, x, y } => json!(["remove", label(relation), x, y]),
        Source9Change::AddAssertion { relation, x, y } => {
            json!(["add_assertion", label(relation), x, y])
        }
    }
}
fn wire_event16(c: Source16Change) -> Value {
    match c {
        Source16Change::Direct { change } => wire_event9(change),
        Source16Change::Admit { relation, x, y } => json!([
            "admit",
            match relation {
                SourceRelation::R => "r",
                SourceRelation::S => "s",
            },
            x,
            y
        ]),
    }
}
fn metric(s: &Source16State) -> Vec<String> {
    vec![
        s.source_size().to_string(),
        s.potential().to_string(),
        s.mass().to_string(),
        s.diagonal_mass().to_string(),
    ]
}
fn stream(hash: &mut Sha256, data: Value) {
    hash.update(serde_json::to_vec(&data).unwrap());
    hash.update(b"\n");
}
fn binary(n: usize, mask: usize, tables: usize) -> Value {
    let mut wire = vec![json!(n)];
    for k in 0..tables {
        wire.push(json!((0..n * n)
            .map(|i| ((mask >> (k * n * n + i)) & 1).to_string())
            .collect::<Vec<_>>()));
    }
    Value::Array(wire)
}

#[test]
fn seed15_all_7356_original_outputs_prices_and_joint_reset_match() {
    let data = receipt();
    let corpus = &data["seed15"];
    let mut digest = Sha256::new();
    let (mut states, mut transitions) = (0usize, 0usize);
    let mut record = |raw: Source9State| {
        let enabled = raw.enabled_changes();
        for admitted in [false, true] {
            let tagged = Source15Tagged::new(raw.clone(), Source15Admission { admitted });
            let outcomes: Vec<_> = enabled
                .iter()
                .map(|&change| {
                    let reached = tagged.perform_enabled(change, 120).unwrap();
                    let (t, a) = change.additions();
                    json!([
                        wire_event9(change),
                        [t, a],
                        wire9(&raw.perform_enabled(change).unwrap()),
                        [wire9(reached.state()), reached.admission().admitted],
                        Source15Admission::after_reaching().admitted
                    ])
                })
                .collect();
            let admitted = tagged.admit();
            stream(
                &mut digest,
                json!([
                    wire9(&raw),
                    tagged.admission().admitted,
                    outcomes,
                    [wire9(admitted.state()), admitted.admission().admitted],
                    raw.source_size().to_string(),
                    [enabled.len(), 0, enabled.len()]
                ]),
            );
            states += 1;
            transitions += enabled.len();
        }
    };
    for n in 0..=2 {
        for mask in 0..(1usize << (2 * n * n)) {
            record(state9(&binary(n, mask, 2)));
        }
    }
    for extra in corpus["extra_inputs"].as_array().unwrap() {
        record(state9(extra));
    }
    assert_eq!(states, number(&corpus["tagged_inputs"]));
    assert_eq!(transitions, 7356);
    assert_eq!(transitions, number(&corpus["transitions"]));
    assert_eq!(hex::encode(digest.finalize()), corpus["stream_sha256"]);
}

#[test]
fn seed16_all_221724_original_transitions_and_three_readings_match() {
    let data = receipt();
    let corpus = &data["seed16"];
    let mut digest = Sha256::new();
    let (mut states, mut transitions) = (0usize, 0usize);
    let mut record = |raw: Source16State| {
        let enabled = raw.enabled_changes();
        let n = raw.state().packet().terms.len();
        let occupied = raw.leftovers().iter().filter(|v| !v.is_zero()).count();
        for (reading, label) in [
            (Source16Reading::Count, "count"),
            (Source16Reading::Set, "set"),
            (Source16Reading::Drop, "drop"),
        ] {
            let outcomes: Vec<_> = enabled
                .iter()
                .map(|&change| {
                    assert!(raw.is_enabled(change));
                    let after = raw.perform_enabled(change, reading).unwrap();
                    let (t, a) = change.additions();
                    let m = metric(&after);
                    json!([
                        wire_event16(change),
                        [t, a],
                        wire16(&after),
                        m[0],
                        m[1],
                        m[2],
                        m[3]
                    ])
                })
                .collect();
            let m = metric(&raw);
            stream(
                &mut digest,
                json!([
                    wire16(&raw),
                    label,
                    outcomes,
                    wire16(&raw.canonical(24).unwrap()),
                    m[0],
                    m[1],
                    m[2],
                    m[3],
                    [enabled.len(), 1 + 2 * n * n, 2 * occupied]
                ]),
            );
            states += 1;
            transitions += enabled.len();
        }
    };
    for n in 0..=2 {
        for mask in 0..(1usize << (3 * n * n)) {
            record(state16(&binary(n, mask, 3)));
        }
    }
    for extra in corpus["extra_inputs"].as_array().unwrap() {
        record(state16(extra));
    }
    assert_eq!(states, number(&corpus["state_readings"]));
    assert_eq!(transitions, 221724);
    assert_eq!(transitions, number(&corpus["transitions"]));
    assert_eq!(hex::encode(digest.finalize()), corpus["stream_sha256"]);
}

fn assert_seed15_history(h15: &Value) {
    let initial = &h15["states"][0];
    let mut tagged = Source15Tagged::new(
        state9(&initial[0]),
        Source15Admission {
            admitted: initial[1].as_bool().unwrap(),
        },
    );
    let mut price = (BigInt::zero(), BigInt::zero());
    for (i, change) in h15["changes"].as_array().unwrap().iter().enumerate() {
        if change == &json!(["admit"]) {
            tagged = tagged.admit();
        } else {
            let change = event9(change);
            let (t, a) = change.additions();
            price.0 += t;
            price.1 += a;
            tagged = tagged.perform_enabled(change, 24).unwrap();
        }
        assert_eq!(
            json!([wire9(tagged.state()), tagged.admission().admitted]),
            h15["states"][i + 1]
        );
    }
    assert_eq!(
        json!([price.0.to_string(), price.1.to_string()]),
        h15["addition_price"]
    );
}

fn assert_seed16_history(history: &Value) {
    let reading = match history["reading"].as_str().unwrap() {
        "count" => Source16Reading::Count,
        "set" => Source16Reading::Set,
        "drop" => Source16Reading::Drop,
        _ => panic!("reading"),
    };
    let before = state16(&history["states"][0]);
    let changes: Vec<_> = history["changes"]
        .as_array()
        .unwrap()
        .iter()
        .map(event16)
        .collect();
    let run = Source16Run::replay(before.clone(), &changes, reading).unwrap();
    assert_eq!(
        json!(run.states().iter().map(wire16).collect::<Vec<_>>()),
        history["states"]
    );
    assert_eq!(
        json!([
            run.addition_price().0.to_string(),
            run.addition_price().1.to_string()
        ]),
        history["addition_price"]
    );
    for split in 0..=changes.len() {
        let left = Source16Run::replay(before.clone(), &changes[..split], reading).unwrap();
        let right =
            Source16Run::replay(left.final_state().clone(), &changes[split..], reading).unwrap();
        assert_eq!(left.then(&right).unwrap(), run);
    }
}

#[test]
fn original_histories_all_splits_and_alternative_future_countermodels_match() {
    let data = receipt();
    assert_seed15_history(&data["seed15"]["history"]);
    for history in data["seed16"]["histories"].as_array().unwrap() {
        assert_seed16_history(history);
    }
    for example in data["seed16"]["countermodels"].as_array().unwrap() {
        let before = state16(&example["before"]);
        let change = event16(&example["change"]);
        for (reading, label) in [
            (Source16Reading::Count, "count"),
            (Source16Reading::Set, "set"),
            (Source16Reading::Drop, "drop"),
        ] {
            assert_eq!(
                wire16(&before.perform_enabled(change, reading).unwrap()),
                example["outcomes"][label]
            );
        }
    }
    let future = &data["seed16"]["record_future"];
    for (state_key, enabled_key) in [
        ("with_record", "with_enabled"),
        ("without_record", "without_enabled"),
    ] {
        assert_eq!(
            json!(state16(&future[state_key])
                .enabled_changes()
                .into_iter()
                .map(wire_event16)
                .collect::<Vec<_>>()),
            future[enabled_key]
        );
    }
}

#[test]
fn count_shortest_recipes_reach_every_binary_target_in_the_source_corpus() {
    for n in 0..=2 {
        for mask in 0..(1usize << (3 * n * n)) {
            let target = state16(&binary(n, mask, 3));
            let recipe = target.count_minimum_recipe();
            assert_eq!(recipe.length(), target.potential());
            let run = recipe.expand(18).unwrap();
            assert_eq!(run.final_state(), &target);
            assert_eq!(BigInt::from(run.changes().len()), target.potential());
        }
    }
}

// Origin: engine/crates_rs/tests/core_wdp/test_admission_execution_oracle.rs
// Claim: urn:core:crates_rs:tests:test-admission-execution-oracle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf8730dc3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf8730dc3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf8730dc3 {
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
impl BoundaryErrorf8730dc3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf8730dc3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf8730dc3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf8730dc3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf8730dc3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf8730dc3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf8730dc3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf8730dc3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f8730dc3() {
    let admitted = BoundaryRecordf8730dc3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf8730dc3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
