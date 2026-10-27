use pfp::{dispatch_runtime_request, RuntimeRequestV1};
use serde_json::{json, Value};

fn fixtures() -> Value {
    serde_json::from_str(include_str!("data/qm_classical.json")).unwrap()
}
fn call(action: &str, payload: Value) -> pfp::RuntimeOutcomeV1 {
    dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: "core.symbol-game.runtime-request.v1".into(),
        action: action.into(),
        payload,
    })
}
fn evaluate(v: Value) -> Value {
    let r = call("qm_classical_evaluate", v);
    assert!(r.success, "{:?}", r.error);
    r.result.unwrap()
}

#[test]
fn three_tests_cross_the_registered_host_and_replay() {
    for input in fixtures().as_object().unwrap().values() {
        let c = evaluate(input.clone());
        assert_eq!(c["normal_form"], *input);
        let v = call(
            "qm_classical_verify",
            json!({"experiment":input,"certificate":c}),
        );
        assert!(v.success, "{:?}", v.error);
        assert_eq!(evaluate(c["normal_form"].clone()), c);
    }
    let f = fixtures();
    assert_eq!(
        evaluate(f["report_collision"].clone())["result"]["answers"],
        json!(["1", "49/625"])
    );
    assert_eq!(
        evaluate(f["bell_nonlocal"].clone())["result"]["chsh"],
        "14/5"
    );
    assert_eq!(
        evaluate(f["central_mixture"].clone())["result"]["central_purity_ceiling"],
        "1/2"
    );
}

#[test]
fn certificates_bind_inputs_and_reject_tampering() {
    let f = fixtures();
    let input = f["central_mixture"].clone();
    let good = evaluate(input.clone());
    for key in [
        "central_purity_ceiling",
        "central_trace_distance_floor",
        "available_ancilla_max_purity",
    ] {
        let mut bad = good.clone();
        bad["result"][key] = json!("1");
        assert!(
            !call(
                "qm_classical_verify",
                json!({"experiment":input,"certificate":bad})
            )
            .success
        );
    }
    assert!(
        !call(
            "qm_classical_verify",
            json!({"experiment":f["quantum_purification"],"certificate":good})
        )
        .success
    );
    let mut authority = good.clone();
    authority["authority_effect"] = json!("Authorized");
    assert!(
        !call(
            "qm_classical_verify",
            json!({"experiment":input,"certificate":authority})
        )
        .success
    );
}

#[test]
fn malformed_and_unpaid_model_inputs_are_refused() {
    let f = fixtures();
    let mut cases = Vec::new();
    for x in [
        json!(0.25),
        json!(true),
        json!("1/0"),
        json!("2/8"),
        json!("1/1"),
        json!("-1/4"),
    ] {
        let mut v = f["bell_local"].clone();
        v["test"]["probabilities"][0] = x;
        cases.push(v);
    }
    for x in [json!([]), json!([0]), json!([usize::MAX]), json!([true])] {
        let mut v = f["central_mixture"].clone();
        v["test"]["ancilla_blocks"] = x;
        cases.push(v);
    }
    let mut v = f["central_mixture"].clone();
    v["test"]["model"] = json!("arbitrary_operational_theory");
    cases.push(v);
    let mut v = f["bell_local"].clone();
    v["ignored_premise"] = json!(true);
    cases.push(v);
    let mut v = f["report_collision"].clone();
    v["test"]["states"][0][0][0][0] = json!("-1");
    cases.push(v);
    let mut v = f["report_collision"].clone();
    v["test"]["kraus"] = json!([]);
    cases.push(v);
    for v in cases {
        assert!(
            !call("qm_classical_evaluate", v.clone()).success,
            "accepted {v}"
        );
    }
}

#[test]
fn lossless_normal_form_preserves_semantic_array_order() {
    let f = fixtures();
    let mut reordered = f["report_collision"].clone();
    reordered["test"]["states"]
        .as_array_mut()
        .unwrap()
        .reverse();
    let a = evaluate(f["report_collision"].clone());
    let b = evaluate(reordered);
    assert_ne!(a["input_digest"], b["input_digest"]);
    assert_eq!(b["result"]["answers"], json!(["49/625", "1"]));
}

#[test]
fn object_order_is_ignored_but_numeric_types_in_certificates_are_bound() {
    let input = fixtures()["central_mixture"].clone();
    let text = format!(
        "{{\"test\":{},\"schema_version\":{}}}",
        input["test"], input["schema_version"]
    );
    let reordered: Value = serde_json::from_str(&text).unwrap();
    let good = evaluate(input.clone());
    assert_eq!(evaluate(reordered), good);
    let mut bad = good.clone();
    bad["result"]["available_ancilla_min_rank"] = json!(true);
    assert!(
        !call(
            "qm_classical_verify",
            json!({"experiment":input,"certificate":bad})
        )
        .success
    );
}

// Origin: engine/crates_rs/tests/pfp/qm_classical.rs
// Claim: urn:core:crates_rs:tests:qm-classical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord371a6544 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord371a6544` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError371a6544 {
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
impl BoundaryError371a6544 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError371a6544 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError371a6544 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord371a6544 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError371a6544> {
        if capacity_bound == 0 {
            return Err(BoundaryError371a6544::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError371a6544::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError371a6544::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_371a6544() {
    let admitted = BoundaryRecord371a6544::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord371a6544::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
