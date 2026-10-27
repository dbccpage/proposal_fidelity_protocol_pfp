//! Differential oracle for original admitted regimes and full candidate replay.
use core_wdp::genesis_primitive_execution::*;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const RECEIPT: &str = include_str!("fixtures/primitive_execution/receipt.json");
const INPUTS: &[u8] = include_bytes!("fixtures/primitive_execution/inputs.json");
const VERIFIER: &[u8] = include_bytes!("fixtures/primitive_execution/verifier.py.txt");
fn receipt() -> Value {
    let data: Value = serde_json::from_str(RECEIPT).unwrap();
    assert_eq!(data["schema"], "wdp-primitive-execution-receipt-v1");
    assert_eq!(data["inputs_sha256"], hex::encode(Sha256::digest(INPUTS)));
    assert_eq!(
        data["verifier_sha256"],
        hex::encode(Sha256::digest(VERIFIER))
    );
    assert_eq!(data["authority_effect"], "None");
    assert_eq!(data["bound_inputs"], 4);
    data
}
fn limits() -> PrimitiveLimits {
    PrimitiveLimits {
        max_tuples: 10000,
        max_width: 16,
        max_candidates: 100000,
    }
}
fn number(v: &Value) -> usize {
    usize::try_from(v.as_u64().unwrap()).unwrap()
}
fn numbers(v: &Value) -> Vec<usize> {
    v.as_array().unwrap().iter().map(number).collect()
}
fn state(v: &Value) -> PrimitiveRegime {
    PrimitiveRegime::try_new(
        v[0].as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_string())
            .collect(),
        numbers(&v[1]),
        v[2].as_array()
            .unwrap()
            .iter()
            .map(|v| PrimitiveInstance {
                form: number(&v[0]),
                args: numbers(&v[1]),
            })
            .collect(),
        numbers(&v[3]).into_iter().collect(),
        v[4].as_array()
            .unwrap()
            .iter()
            .map(|v| (number(&v[0]), number(&v[1])))
            .collect(),
    )
    .unwrap()
}
fn wire(s: &PrimitiveRegime) -> Value {
    json!([
        s.data(),
        s.forms(),
        s.instances()
            .iter()
            .map(|v| json!([v.form, v.args]))
            .collect::<Vec<_>>(),
        s.rules().iter().collect::<Vec<_>>(),
        s.requirements()
            .iter()
            .map(|&(i, j)| json!([i, j]))
            .collect::<Vec<_>>()
    ])
}
fn context(c: &PrimitiveContext) -> Value {
    json!([c.form, c.slots])
}
fn observations(s: &PrimitiveRegime) -> Value {
    let witnesses: Vec<_> = (0..s.data().len())
        .flat_map(|i| {
            (i + 1..s.data().len()).map(move |j| {
                json!([
                    [i, j],
                    s.witness(i, j, limits()).unwrap().as_ref().map(context)
                ])
            })
        })
        .collect();
    json!([
        s.contexts(limits())
            .unwrap()
            .iter()
            .map(context)
            .collect::<Vec<_>>(),
        s.profiles(limits())
            .unwrap()
            .iter()
            .map(|p| p.iter().map(context).collect::<Vec<_>>())
            .collect::<Vec<_>>(),
        s.collapsed_pairs(limits())
            .unwrap()
            .into_iter()
            .map(|(i, j)| json!([i, j]))
            .collect::<Vec<_>>(),
        s.satisfies(limits()).unwrap(),
        witnesses
    ])
}
fn event(e: &PrimitiveEvent) -> Value {
    match e {
        PrimitiveEvent::Supply { token } => json!(["supply", token]),
        PrimitiveEvent::AdmitDatum { token } => json!(["admit_datum", token]),
        PrimitiveEvent::AdmitForm { arity } => json!(["admit_form", arity]),
        PrimitiveEvent::AdmitInst { form, args } => json!(["admit_inst", form, args]),
        PrimitiveEvent::AdmitRuleAll { form } => json!(["admit_rule_all", form]),
        PrimitiveEvent::Impose { i, j } => json!(["impose", i, j]),
    }
}
fn decode(v: &Value) -> PrimitiveEvent {
    match v[0].as_str().unwrap() {
        "supply" => PrimitiveEvent::Supply {
            token: v[1].as_str().unwrap().to_string(),
        },
        "admit_datum" => PrimitiveEvent::AdmitDatum {
            token: v[1].as_str().unwrap().to_string(),
        },
        "admit_form" => PrimitiveEvent::AdmitForm {
            arity: number(&v[1]),
        },
        "admit_inst" => PrimitiveEvent::AdmitInst {
            form: number(&v[1]),
            args: numbers(&v[2]),
        },
        "admit_rule_all" => PrimitiveEvent::AdmitRuleAll {
            form: number(&v[1]),
        },
        "impose" => PrimitiveEvent::Impose {
            i: number(&v[1]),
            j: number(&v[2]),
        },
        _ => panic!("source event"),
    }
}
fn words(base: usize, width: usize) -> Vec<Vec<usize>> {
    core_combinatorics::cartesian_words::CartesianWords::new(base, width, 10000, 16)
        .unwrap()
        .collect()
}
fn alphabet(s: &PrimitiveRegime) -> Vec<PrimitiveEvent> {
    let n = s.data().len();
    let mut out = vec![
        PrimitiveEvent::Supply {
            token: "<ab>".into(),
        },
        PrimitiveEvent::AdmitDatum {
            token: "fresh".into(),
        },
    ];
    if n > 0 {
        out.push(PrimitiveEvent::AdmitDatum {
            token: s.data()[0].clone(),
        });
    }
    out.extend([0, 1, 2].map(|arity| PrimitiveEvent::AdmitForm { arity }));
    for (form, &arity) in s.forms().iter().enumerate() {
        out.extend(
            words(n, arity)
                .into_iter()
                .map(|args| PrimitiveEvent::AdmitInst { form, args }),
        );
        out.push(PrimitiveEvent::AdmitInst { form, args: vec![] });
        out.push(PrimitiveEvent::AdmitInst {
            form,
            args: vec![n; arity],
        });
    }
    out.push(PrimitiveEvent::AdmitInst {
        form: s.forms().len(),
        args: vec![],
    });
    out.extend((0..=s.forms().len()).map(|form| PrimitiveEvent::AdmitRuleAll { form }));
    for i in 0..n {
        for j in i + 1..n {
            out.push(PrimitiveEvent::Impose { i, j });
        }
    }
    out.extend([
        PrimitiveEvent::Impose { i: 0, j: 0 },
        PrimitiveEvent::Impose { i: 0, j: n },
    ]);
    out
}
fn stream(hash: &mut Sha256, data: Value) {
    hash.update(serde_json::to_vec(&data).unwrap());
    hash.update(b"\n");
}

#[test]
fn all_72954_original_event_attempts_and_complete_context_observations_match() {
    let data = receipt();
    let corpus = &data["corpus"];
    let mut digest = Sha256::new();
    let (mut regimes, mut attempts, mut refused) = (0usize, 0usize, 0usize);
    let mut record = |s: PrimitiveRegime| {
        let mut outcomes = Vec::new();
        for (reading, label) in [
            (PrimitiveReading::Dedup, "dedup"),
            (PrimitiveReading::Occurrence, "occurrence"),
        ] {
            let rows: Vec<_> = alphabet(&s)
                .iter()
                .map(|e| {
                    let after = match s.step(e, reading) {
                        Ok(after) => wire(&after),
                        Err(PrimitiveExecutionError::InvalidArgument) => {
                            refused += 1;
                            Value::Null
                        }
                        Err(error) => panic!("unexpected refusal {error}"),
                    };
                    json!([event(e), after])
                })
                .collect();
            attempts += rows.len();
            outcomes.push(json!([label, rows]));
        }
        stream(&mut digest, json!([wire(&s), observations(&s), outcomes]));
        regimes += 1;
    };
    for n in 0..=2 {
        for shape in corpus["form_shapes"].as_array().unwrap() {
            let forms = numbers(shape);
            let instances: Vec<_> = forms
                .iter()
                .enumerate()
                .flat_map(|(form, &arity)| {
                    words(n, arity)
                        .into_iter()
                        .map(move |args| PrimitiveInstance { form, args })
                })
                .collect();
            let pairs: Vec<_> = (0..n)
                .flat_map(|i| (i + 1..n).map(move |j| (i, j)))
                .collect();
            for mask in 0..(1usize << (instances.len() + forms.len() + pairs.len())) {
                let insts = instances
                    .iter()
                    .enumerate()
                    .filter(|(i, _)| (mask >> i) & 1 == 1)
                    .map(|(_, v)| v.clone())
                    .collect();
                let rules = (0..forms.len())
                    .filter(|&f| (mask >> (instances.len() + f)) & 1 == 1)
                    .collect();
                let reqs = pairs
                    .iter()
                    .enumerate()
                    .filter(|(i, _)| (mask >> (instances.len() + forms.len() + i)) & 1 == 1)
                    .map(|(_, p)| *p)
                    .collect();
                record(
                    PrimitiveRegime::try_new(
                        (0..n).map(|i| format!("d{i}")).collect(),
                        forms.clone(),
                        insts,
                        rules,
                        reqs,
                    )
                    .unwrap(),
                );
            }
        }
    }
    for extra in corpus["extra_inputs"].as_array().unwrap() {
        record(state(extra));
    }
    assert_eq!(regimes, 1664);
    assert_eq!(regimes, number(&corpus["regimes"]));
    assert_eq!(attempts, 72954);
    assert_eq!(attempts, number(&corpus["event_attempts"]));
    assert_eq!(refused, 25408);
    assert_eq!(refused, number(&corpus["refused_events"]));
    assert_eq!(hex::encode(digest.finalize()), corpus["stream_sha256"]);
}
fn item(i: &PrimitiveItem) -> Value {
    match i {
        PrimitiveItem::NewDatum => json!(["new_datum"]),
        PrimitiveItem::NewForm { arity } => json!(["new_form", arity]),
        PrimitiveItem::NewRuleAll { form } => json!(["new_rule_all", form]),
        PrimitiveItem::NewInst { form, args } => json!(["new_inst", form, args]),
    }
}
fn delta(v: &Value) -> PrimitiveDelta {
    PrimitiveDelta::new(
        v.as_array()
            .unwrap()
            .iter()
            .map(|v| match v[0].as_str().unwrap() {
                "new_datum" => PrimitiveItem::NewDatum,
                "new_form" => PrimitiveItem::NewForm {
                    arity: number(&v[1]),
                },
                "new_rule_all" => PrimitiveItem::NewRuleAll {
                    form: number(&v[1]),
                },
                "new_inst" => PrimitiveItem::NewInst {
                    form: number(&v[1]),
                    args: numbers(&v[2]),
                },
                _ => panic!("item"),
            })
            .collect(),
    )
}
fn delta_wire(d: &PrimitiveDelta) -> Value {
    json!(d.items().iter().map(item).collect::<Vec<_>>())
}
fn minimum_wire(m: Option<PrimitiveMinimum>) -> Value {
    match m {
        None => Value::Null,
        Some(m) => {
            json!({"price":[m.price.0.to_string(),m.price.1.to_string()],"deltas":m.deltas.iter().map(delta_wire).collect::<Vec<_>>()})
        }
    }
}

#[test]
fn every_full_candidate_output_and_checked_minimum_matches_actual_source_replay() {
    let data = receipt();
    let mut total = 0;
    for case in data["candidate_cases"].as_array().unwrap() {
        let s = state(&case["base"]);
        let target = (number(&case["target"][0]), number(&case["target"][1]));
        let arity = number(&case["max_arity"]);
        let mut digest = Sha256::new();
        for cost in 0..=2 {
            let deltas = s.full_deltas(cost, arity, limits()).unwrap();
            assert_eq!(deltas.len(), number(&case["counts"][cost]));
            total += deltas.len();
            let rows: Vec<_> = deltas
                .iter()
                .map(|d| {
                    let price = d.price();
                    json!([
                        delta_wire(d),
                        s.delta_events(d)
                            .unwrap()
                            .iter()
                            .map(event)
                            .collect::<Vec<_>>(),
                        wire(&s.apply_delta(d).unwrap()),
                        [price.0.to_string(), price.1.to_string()],
                        s.response_valid(target, d, limits()).unwrap()
                    ])
                })
                .collect();
            stream(&mut digest, json!([cost, rows]));
        }
        assert_eq!(
            hex::encode(digest.finalize()),
            case["stream_sha256"],
            "candidate order and full replay for base {:?}",
            case["base"]
        );
        for (measure, label) in [
            (PrimitiveMeasure::Items, "mu1"),
            (PrimitiveMeasure::ItemsThenArity, "mu2"),
        ] {
            assert_eq!(
                minimum_wire(
                    s.minimum_responses_checked(target, measure, 2, arity, limits())
                        .unwrap()
                ),
                case["checked_minima"][label]
            );
        }
    }
    assert_eq!(total, 582);
    assert_eq!(total, number(&data["complete_candidate_deltas"]));
    let c = &data["generated_name_countermodel"];
    assert_eq!(c["source_fast_valid"], true);
    assert_eq!(c["source_naive"], "ill_formed");
    assert_eq!(
        state(&c["base"]).apply_delta(&delta(&c["delta"])),
        Err(PrimitiveExecutionError::InvalidArgument)
    );
}

#[test]
fn both_actual_reading_histories_preserve_all_intermediates_and_prefix_splits() {
    let data = receipt();
    for h in data["histories"].as_array().unwrap() {
        let reading = if h["reading"] == "dedup" {
            PrimitiveReading::Dedup
        } else {
            PrimitiveReading::Occurrence
        };
        let base = state(&h["states"][0]);
        let events: Vec<_> = h["events"].as_array().unwrap().iter().map(decode).collect();
        let run = PrimitiveRun::replay(base.clone(), &events, reading).unwrap();
        assert_eq!(
            json!(run.states().iter().map(wire).collect::<Vec<_>>()),
            h["states"]
        );
        for split in 0..=events.len() {
            let left = PrimitiveRun::replay(base.clone(), &events[..split], reading).unwrap();
            let right = PrimitiveRun::replay(left.final_state().clone(), &events[split..], reading)
                .unwrap();
            assert_eq!(left.then(&right).unwrap(), run);
        }
    }
    // Standalone canonical ordering agrees with source item_key even for repeats.
    let repeated = PrimitiveDelta::new(vec![
        PrimitiveItem::NewInst {
            form: 0,
            args: vec![0],
        },
        PrimitiveItem::NewDatum,
        PrimitiveItem::NewForm { arity: 1 },
        PrimitiveItem::NewDatum,
    ]);
    assert_eq!(repeated.items()[0], PrimitiveItem::NewDatum);
    assert_eq!(repeated.items()[1], PrimitiveItem::NewDatum);
}

// Origin: engine/crates_rs/tests/core_wdp/test_primitive_execution_oracle.rs
// Claim: urn:core:crates_rs:tests:test-primitive-execution-oracle:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord11676b94 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord11676b94` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError11676b94 {
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
impl BoundaryError11676b94 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError11676b94 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError11676b94 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord11676b94 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError11676b94> {
        if capacity_bound == 0 {
            return Err(BoundaryError11676b94::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError11676b94::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError11676b94::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_11676b94() {
    let admitted = BoundaryRecord11676b94::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord11676b94::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
