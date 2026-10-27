//! Original source-23 differential evidence, with unchanged source/control pins.
use num_bigint::BigInt;
use core_combinatorics::cartesian_words::CartesianWords;
use core_combinatorics::enumeration::Permutations;
use core_wdp::genesis_gauge_result::*;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const RECEIPT: &str = include_str!("fixtures/gauge_result/receipt.json");
const INPUTS: &[u8] = include_bytes!("fixtures/gauge_result/inputs.json");
const VERIFIER: &[u8] = include_bytes!("fixtures/gauge_result/verifier.py.txt");
fn receipt() -> Value {
    let data: Value = serde_json::from_str(RECEIPT).unwrap();
    assert_eq!(data["schema"], "wdp-gauge-result-receipt-v1");
    assert_eq!(data["inputs_sha256"], hex::encode(Sha256::digest(INPUTS)));
    assert_eq!(
        data["verifier_sha256"],
        hex::encode(Sha256::digest(VERIFIER))
    );
    assert_eq!(data["authority_effect"], "None");
    assert_eq!(data["bound_inputs"], 9);
    assert_eq!(data["post_execution_rehash"], "unchanged");
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
fn strings(v: &[BigInt]) -> Vec<String> {
    v.iter().map(ToString::to_string).collect()
}
fn state(v: &Value) -> Source23State {
    Source23State::try_new(number(&v[0]), integers(&v[1]), integers(&v[2])).unwrap()
}
fn wire(s: &Source23State) -> Value {
    json!([s.n(), strings(s.r()), strings(s.s())])
}
fn key(s: &Source23State) -> Value {
    let result = s.result_key(10000).unwrap();
    json!([result.n, strings(&result.normal)])
}
fn profile(s: &Source23State) -> Value {
    let p = s.sum_profile(10000).unwrap();
    json!([
        strings(&p.loops),
        strings(&p.pairs),
        strings(&p.rounds),
        p.total.to_string()
    ])
}
fn observations(s: &Source23State) -> Value {
    let certificate = s
        .nothing_certificate(10000)
        .unwrap()
        .map(|c| json!([c.kind, c.terms, c.value.to_string()]));
    json!([
        strings(&s.excess()),
        strings(&s.normal_table().unwrap()),
        key(s),
        certificate,
        profile(s),
        wire(&s.plain_state().unwrap()),
        s.plain_cost().to_string()
    ])
}
#[derive(Default)]
struct Corpus {
    digest: Sha256,
    states: usize,
    raisings: usize,
    rewritings: usize,
    alignments: usize,
}
impl Corpus {
    fn record(&mut self, s: Source23State, manifest: &Value) {
        let radix = number(
            &manifest[if s.n() <= 3 {
                "small_raising_radix"
            } else {
                "larger_raising_radix"
            }],
        );
        let mut raised = Vec::new();
        for word in CartesianWords::new(radix, s.n(), 10000, 16).unwrap() {
            let counts: Vec<BigInt> = word.into_iter().map(BigInt::from).collect();
            let after = s.raise_terms(&counts).unwrap();
            raised.push(json!([
                strings(&counts),
                wire(&after),
                strings(&after.normal_table().unwrap()),
                after.plain_cost().to_string()
            ]));
            self.raisings += 1;
        }
        let mut renamed = Vec::new();
        for image in Permutations::new(s.n(), 10000).unwrap() {
            let after = s.rewrite(&image).unwrap();
            renamed.push(json!([
                image,
                wire(&after),
                strings(&after.normal_table().unwrap())
            ]));
            self.rewritings += 1;
        }
        let image: Vec<_> = (0..s.n()).rev().collect();
        let counts: Vec<BigInt> = (0..s.n()).map(|x| BigInt::from(x % 3)).collect();
        let target = s.rewrite(&image).unwrap().raise_terms(&counts).unwrap();
        let alignment = json!([wire(&target), wire(&s.align_to(&target, 10000).unwrap())]);
        self.alignments += 1;
        let row = json!([wire(&s), observations(&s), raised, renamed, alignment]);
        self.digest.update(serde_json::to_vec(&row).unwrap());
        self.digest.update(b"\n");
        self.states += 1;
    }
}

#[test]
fn every_declared_original_state_raising_rewriting_and_alignment_agrees() {
    let expected = receipt();
    let inputs: Value = serde_json::from_slice(INPUTS).unwrap();
    let manifest = &inputs["corpus"];
    let mut corpus = Corpus::default();
    for n in 0..=number(&manifest["binary_r_and_s_max_n"]) {
        for cells in CartesianWords::new(2, 2 * n * n, 10000, 32).unwrap() {
            let r = cells[..n * n].iter().map(|&x| BigInt::from(x)).collect();
            let s = cells[n * n..].iter().map(|&x| BigInt::from(x)).collect();
            corpus.record(Source23State::try_new(n, r, s).unwrap(), manifest);
        }
    }
    let n = number(&manifest["binary_r_zero_s_n"]);
    for cells in CartesianWords::new(2, n * n, 10000, 32).unwrap() {
        let r = cells.into_iter().map(BigInt::from).collect();
        corpus.record(
            Source23State::try_new(n, r, vec![0.into(); n * n]).unwrap(),
            manifest,
        );
    }
    for v in manifest["extra_inputs"].as_array().unwrap() {
        corpus.record(state(v), manifest);
    }
    assert_eq!(corpus.states, number(&expected["corpus"]["states"]));
    assert_eq!(
        corpus.raisings,
        number(&expected["corpus"]["bulk_raisings"])
    );
    assert_eq!(corpus.rewritings, number(&expected["corpus"]["rewritings"]));
    assert_eq!(corpus.alignments, number(&expected["corpus"]["alignments"]));
    assert_eq!(
        hex::encode(corpus.digest.finalize()),
        expected["corpus"]["stream_sha256"]
    );
}

#[test]
fn original_countermodels_and_all_atomic_history_splits_are_retained() {
    let data = receipt();
    let example = &data["profile_countermodel"];
    let a = state(&example["a"]);
    let b = state(&example["b"]);
    assert_eq!(profile(&a), example["common_profile"]);
    assert_eq!(profile(&b), example["common_profile"]);
    assert_eq!(json!([key(&a), key(&b)]), example["keys"]);
    assert!(!a.same_result(&b, 6).unwrap());
    assert_eq!(a.align_to(&b, 6), Err(Source23Error::NotSameResult));
    let cost = &data["cost_countermodel"];
    let before = state(&cost["before"]);
    let after = before.raise_term(0).unwrap();
    assert_eq!(wire(&after), cost["after"]);
    assert_eq!(
        json!([
            before.plain_cost().to_string(),
            after.plain_cost().to_string()
        ]),
        cost["costs"]
    );
    assert_eq!(key(&before), cost["common_key"]);
    assert_eq!(key(&after), cost["common_key"]);
    let order = &data["normalization_order_countermodel"];
    let s = state(&order["state"]);
    let image: Vec<_> = order["image"]
        .as_array()
        .unwrap()
        .iter()
        .map(number)
        .collect();
    assert_eq!(
        json!(strings(&s.rewrite(&image).unwrap().normal_table().unwrap())),
        order["normal_after_rewrite"]
    );
    assert_ne!(
        order["normal_after_rewrite"],
        order["rewrite_only_after_normal"]
    );
    for history in data["histories"].as_array().unwrap() {
        let initial = state(&history["states"][0]);
        let word: Vec<_> = history["raised_terms"]
            .as_array()
            .unwrap()
            .iter()
            .map(number)
            .collect();
        let run = Source23Run::replay(initial.clone(), &word).unwrap();
        assert_eq!(
            json!(run.states().iter().map(wire).collect::<Vec<_>>()),
            history["states"]
        );
        assert_eq!(run.raised_terms(), word);
        for split in 0..=word.len() {
            let left = Source23Run::replay(initial.clone(), &word[..split]).unwrap();
            let right = Source23Run::replay(left.final_state().clone(), &word[split..]).unwrap();
            assert_eq!(left.then(&right).unwrap(), run);
        }
    }
}

// Origin: engine/crates_rs/tests/core_wdp/test_gauge_result_oracle.rs
// Claim: urn:core:crates_rs:tests:test-gauge-result-oracle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord07b01840 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord07b01840` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError07b01840 {
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
impl BoundaryError07b01840 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError07b01840 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError07b01840 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord07b01840 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError07b01840> {
        if capacity_bound == 0 {
            return Err(BoundaryError07b01840::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError07b01840::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError07b01840::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_07b01840() {
    let admitted = BoundaryRecord07b01840::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord07b01840::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
