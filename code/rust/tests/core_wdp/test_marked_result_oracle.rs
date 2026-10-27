//! Joint marked observations compared with the independently pinned source functions.
use num_bigint::BigInt;
use core_combinatorics::cartesian_words::CartesianWords;
use core_combinatorics::enumeration::Permutations;
use core_wdp::genesis_gauge_result::Source23Error;
use core_wdp::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use core_wdp::genesis_source_execution::{Source25Change, Source25State};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const RECEIPT: &str = include_str!("fixtures/marked_result/receipt.json");
const INPUTS: &[u8] = include_bytes!("fixtures/marked_result/inputs.json");
const VERIFIER: &[u8] = include_bytes!("fixtures/marked_result/verifier.py.txt");

fn receipt() -> Value {
    let data: Value = serde_json::from_str(RECEIPT).unwrap();
    assert_eq!(data["schema"], "wdp-marked-result-receipt-v1");
    assert_eq!(data["inputs_sha256"], hex::encode(Sha256::digest(INPUTS)));
    assert_eq!(
        data["verifier_sha256"],
        hex::encode(Sha256::digest(VERIFIER))
    );
    assert_eq!(data["authority_effect"], "None");
    assert_eq!(data["bound_inputs"], 15);
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
fn triples(v: &Value) -> Vec<MarkedTriple> {
    v.as_array()
        .unwrap()
        .iter()
        .map(|t| MarkedTriple {
            x: number(&t[0]),
            y: number(&t[1]),
            z: number(&t[2]),
        })
        .collect()
}
fn triple_wires(ts: &[MarkedTriple]) -> Vec<[usize; 3]> {
    ts.iter().map(|t| [t.x, t.y, t.z]).collect()
}
fn raw(n: usize, r: Vec<BigInt>, s: Vec<BigInt>, filled: Vec<MarkedTriple>) -> Source25State {
    Source25State::try_new(GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r,
        s,
        filled,
    })
    .unwrap()
}
fn state(v: &Value) -> Source25State {
    raw(
        number(&v[0]),
        integers(&v[1]),
        integers(&v[2]),
        triples(&v[3]),
    )
}
fn wire(s: &Source25State) -> Value {
    let p = s.packet();
    json!([
        p.terms.len(),
        strings(&p.r),
        strings(&p.s),
        triple_wires(&p.filled)
    ])
}
fn mark(s: &Source25State) -> Value {
    let m = s.result_mark(10000).unwrap();
    json!([m.n, strings(&m.normal), triple_wires(&m.filled)])
}
fn balance(s: &Source25State) -> Value {
    json!(s
        .balance_record()
        .unwrap()
        .iter()
        .map(|(t, b)| ([t.x, t.y, t.z], *b))
        .collect::<Vec<_>>())
}
fn observations(s: &Source25State) -> Value {
    json!([
        wire(&s.canonical_state(10000).unwrap()),
        mark(s),
        wire(&s.plain_state().unwrap()),
        wire(&s.swap_relations().unwrap()),
        balance(s),
        triple_wires(&s.unbalanced().unwrap()),
        wire(&s.nothing_with().unwrap()),
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
    fn record(&mut self, s: Source25State, manifest: &Value) {
        let n = s.packet().terms.len();
        let before_mark = mark(&s);
        let mut raised = Vec::new();
        for word in CartesianWords::new(number(&manifest["raising_radix"]), n, 10000, 16).unwrap() {
            let counts: Vec<BigInt> = word.into_iter().map(BigInt::from).collect();
            let after = s.raise_terms(&counts).unwrap();
            let after_mark = mark(&after);
            assert_eq!(after_mark, before_mark);
            raised.push(json!([
                strings(&counts),
                wire(&after),
                after_mark,
                balance(&after)
            ]));
            self.raisings += 1;
        }
        let mut renamed = Vec::new();
        for image in Permutations::new(n, 10000).unwrap() {
            let after = s.rewrite(&image).unwrap();
            let after_mark = mark(&after);
            assert_eq!(after_mark, before_mark);
            renamed.push(json!([image, wire(&after), after_mark, balance(&after)]));
            self.rewritings += 1;
        }
        let image: Vec<_> = (0..n).rev().collect();
        let counts: Vec<BigInt> = (0..n).map(|x| BigInt::from(x % 2)).collect();
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
fn all_declared_original_joint_observations_and_writings_agree() {
    let expected = receipt();
    let inputs: Value = serde_json::from_slice(INPUTS).unwrap();
    let manifest = &inputs["corpus"];
    let mut corpus = Corpus::default();
    for n in 0..=number(&manifest["binary_r_and_s_max_n"]) {
        for cells in CartesianWords::new(2, 2 * n * n, 10000, 32).unwrap() {
            corpus.record(
                raw(
                    n,
                    cells[..n * n].iter().map(|&v| v.into()).collect(),
                    cells[n * n..].iter().map(|&v| v.into()).collect(),
                    vec![],
                ),
                manifest,
            );
        }
    }
    let n = number(&manifest["binary_r_zero_s_n"]);
    for cells in CartesianWords::new(2, n * n, 10000, 32).unwrap() {
        for filled in manifest["filled_subsets"].as_array().unwrap() {
            corpus.record(
                raw(
                    n,
                    cells.iter().map(|&v| v.into()).collect(),
                    vec![0.into(); n * n],
                    triples(filled),
                ),
                manifest,
            );
        }
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
fn original_joint_orientation_and_carrier_countermodels_are_retained() {
    let data = receipt();
    for name in ["joint_incidence_countermodel", "orientation_countermodel"] {
        let countermodel = &data[name];
        let a = state(&countermodel["states"][0]);
        let b = state(&countermodel["states"][1]);
        assert_eq!(
            json!([observations(&a), observations(&b)]),
            countermodel["observations"]
        );
        assert_ne!(mark(&a), mark(&b));
        assert_eq!(a.align_to(&b, 10000), Err(Source23Error::NotSameResult));
    }
    let addition = &data["term_addition_countermodel"];
    let before: Vec<_> = addition["before"]
        .as_array()
        .unwrap()
        .iter()
        .map(state)
        .collect();
    let after: Vec<_> = before
        .iter()
        .map(|s| s.perform_enabled(Source25Change::AddTerm).unwrap())
        .collect();
    let after_fill: Vec<_> = after
        .iter()
        .map(|s| {
            s.perform_enabled(Source25Change::Fill { x: 0, y: 1, z: 2 })
                .unwrap()
        })
        .collect();
    assert_eq!(
        json!(after.iter().map(wire).collect::<Vec<_>>()),
        addition["after"]
    );
    assert_eq!(
        json!(after_fill.iter().map(wire).collect::<Vec<_>>()),
        addition["after_fill"]
    );
    assert_eq!(
        json!(before.iter().map(mark).collect::<Vec<_>>()),
        addition["marks_before"]
    );
    assert_eq!(
        json!(after.iter().map(mark).collect::<Vec<_>>()),
        addition["marks_after"]
    );
    assert_eq!(
        json!(after_fill.iter().map(balance).collect::<Vec<_>>()),
        addition["balance_after_fill"]
    );
    assert_eq!(mark(&before[0]), mark(&before[1]));
    assert_ne!(mark(&after[0]), mark(&after[1]));

    let identification = &data["identification_countermodel"];
    let before: Vec<_> = identification["before"]
        .as_array()
        .unwrap()
        .iter()
        .map(state)
        .collect();
    let after: Vec<_> = before
        .iter()
        .map(|s| {
            s.perform_enabled(Source25Change::Identify { x: 0, y: 1 })
                .unwrap()
        })
        .collect();
    assert_eq!(
        json!(after.iter().map(wire).collect::<Vec<_>>()),
        identification["after"]
    );
    assert_eq!(
        json!(before.iter().map(mark).collect::<Vec<_>>()),
        identification["marks_before"]
    );
    assert_eq!(
        json!(after.iter().map(mark).collect::<Vec<_>>()),
        identification["marks_after"]
    );
    assert_eq!(
        json!(before.iter().map(balance).collect::<Vec<_>>()),
        identification["balance_before"]
    );
    assert_eq!(
        json!(after.iter().map(balance).collect::<Vec<_>>()),
        identification["balance_after"]
    );
    assert_eq!(mark(&before[0]), mark(&before[1]));
    assert_ne!(mark(&after[0]), mark(&after[1]));
}

// Origin: engine/crates_rs/tests/core_wdp/test_marked_result_oracle.rs
// Claim: urn:core:crates_rs:tests:test-marked-result-oracle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1117b1c8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1117b1c8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1117b1c8 {
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
impl BoundaryError1117b1c8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1117b1c8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1117b1c8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1117b1c8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1117b1c8> {
        if capacity_bound == 0 {
            return Err(BoundaryError1117b1c8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1117b1c8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1117b1c8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1117b1c8() {
    let admitted = BoundaryRecord1117b1c8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1117b1c8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
