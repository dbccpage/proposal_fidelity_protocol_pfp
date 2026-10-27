use core_epistemic_immune_system::{
    activation::DetectorHitRefV1,
    activation_ports::{DangerSensorPort, GuardStatePort, ObservedDanger},
    activation_use_case::{activate_learned_guard, ActivationRequest},
    Refusal,
};
use serde_json::{json, Value};
use std::{cell::RefCell, rc::Rc};

type Trace = Rc<RefCell<Vec<Value>>>;
struct State {
    trace: Trace,
    admitted: bool,
    suspended: bool,
    fail_at: Option<&'static str>,
}
impl GuardStatePort for State {
    fn is_externally_admitted(&mut self, spec_id: &str, scope: &str) -> Result<bool, Refusal> {
        self.trace
            .borrow_mut()
            .push(json!(["admitted", spec_id, scope]));
        if self.fail_at == Some("admitted") {
            return Err(Refusal::new("STATE_UNAVAILABLE", "custody unavailable"));
        }
        Ok(self.admitted)
    }
    fn is_suspended(&mut self, spec_id: &str, scope: &str) -> Result<bool, Refusal> {
        self.trace
            .borrow_mut()
            .push(json!(["suspended", spec_id, scope]));
        if self.fail_at == Some("suspended") {
            return Err(Refusal::new("STATE_UNAVAILABLE", "custody unavailable"));
        }
        Ok(self.suspended)
    }
}
struct Sensor {
    trace: Trace,
    observation: Option<ObservedDanger>,
    failed: bool,
}
impl DangerSensorPort for Sensor {
    fn detect_danger(&mut self, content: &str) -> Result<Option<ObservedDanger>, Refusal> {
        self.trace.borrow_mut().push(json!(["sensor", content]));
        if self.failed {
            return Err(Refusal::new("SENSOR_UNAVAILABLE", "host check unavailable"));
        }
        Ok(self.observation.clone())
    }
}
fn text<'a>(input: &'a Value, key: &str) -> Result<&'a str, Box<dyn std::error::Error>> {
    input[key]
        .as_str()
        .ok_or_else(|| format!("{key} required").into())
}

fn build_activation_request<'a>(
    input: &Value,
    hit: Option<&'a DetectorHitRefV1>,
) -> Result<ActivationRequest<'a>, Box<dyn std::error::Error>> {
    Ok(ActivationRequest {
        profile_digest: text(input, "profile_digest")?,
        spec_id: text(input, "spec_id")?,
        hit,
        content: text(input, "content")?,
        subject_scope: text(input, "subject_scope")?,
        disposition: text(input, "disposition")?,
    })
}

fn run_guard_use_case_row(input: &Value) -> Result<(Value, Value), Box<dyn std::error::Error>> {
    let trace = Trace::default();
    let mut state = State {
        trace: trace.clone(),
        admitted: input["admitted"].as_bool().ok_or("admitted required")?,
        suspended: input["suspended"].as_bool().ok_or("suspended required")?,
        fail_at: None,
    };
    let mut sensor = Sensor {
        trace: trace.clone(),
        observation: serde_json::from_value(input["signal"].clone())?,
        failed: false,
    };
    let hit: Option<DetectorHitRefV1> = serde_json::from_value(input["hit"].clone())?;
    let request = build_activation_request(input, hit.as_ref())?;
    let actual = match activate_learned_guard(request, &mut sensor, &mut state) {
        Ok(receipt) => json!({"ok":receipt}),
        Err(error) => json!({"error":error}),
    };
    Ok((actual, json!(*trace.borrow())))
}

#[test]
fn frozen_python_guard_ports_and_full_ordered_trace() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_guard_use_case_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 24);
    for (index, row) in rows.iter().enumerate() {
        let (actual, calls) = run_guard_use_case_row(&row["input"])?;
        assert_eq!(actual, row["expected"], "use case vector {index}");
        assert_eq!(calls, row["calls"], "ordered trace vector {index}");
    }
    Ok(())
}

#[test]
fn injected_port_failures_remain_typed_and_stop_dependent_calls() {
    for (fail_at, sensor_failed, expected_calls, expected_code) in [
        (Some("admitted"), false, 1, "STATE_UNAVAILABLE"),
        (Some("suspended"), false, 2, "STATE_UNAVAILABLE"),
        (None, true, 3, "SENSOR_UNAVAILABLE"),
    ] {
        let trace = Trace::default();
        let mut state = State {
            trace: trace.clone(),
            admitted: true,
            suspended: false,
            fail_at,
        };
        let mut sensor = Sensor {
            trace: trace.clone(),
            observation: None,
            failed: sensor_failed,
        };
        let result = activate_learned_guard(
            ActivationRequest {
                profile_digest: "bad",
                spec_id: "detector.one",
                hit: None,
                content: "payload",
                subject_scope: "fixture",
                disposition: "FINDING",
            },
            &mut sensor,
            &mut state,
        );
        assert_eq!(
            result.expect_err("failed port cannot activate").code,
            expected_code
        );
        assert_eq!(trace.borrow().len(), expected_calls);
    }
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/activation_use_case_parity.rs
// Claim: urn:core:crates_rs:tests:activation-use-case-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
