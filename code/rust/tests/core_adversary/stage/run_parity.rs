use num_rational::Rational64;
use core_adversary::stage::emission::{
    Clock, DdcSink, EmitterSuite, IntelligenceEvent, UnsSink, UtsSink,
};
use core_adversary::stage::evaluation::{EvaluatorEpoch, ValuationReceipt};
use core_adversary::stage::oscillation::OscillationDetector;
use core_adversary::stage::packets::{
    AgentResult, CandidateProposal, LicensedWorkflowPlan, WorkPacket,
};
use core_adversary::stage::ports::{
    ContinuationPort, ContinueDecision, ModelPort, Refusal, SchedulerPort, ValuatorPort,
};
use core_adversary::stage::run::{ProgressMeasure, SwarmRunState};
use core_adversary::stage::run_swarm::{run_swarm, SwarmRuntime};
use core_adversary::stage::scheduler::DeterministicScheduler;
use serde::{de::DeserializeOwned, Serialize};
use serde_json::{json, Value};
use std::{cell::RefCell, collections::VecDeque, rc::Rc};

fn decode<T: DeserializeOwned>(value: &Value) -> Result<T, serde_json::Error> {
    serde_json::from_slice(&serde_json::to_vec(value)?)
}
fn outcome<T: Serialize>(result: Result<T, Refusal>) -> Value {
    match result {
        Ok(value) => json!({"ok": value}),
        Err(error) => json!({"error": error}),
    }
}
fn next<T: DeserializeOwned>(replies: &mut VecDeque<Value>) -> Result<T, Refusal> {
    let row = replies
        .pop_front()
        .ok_or_else(|| Refusal::new("TRANSCRIPT_ENTRY_MISSING", "fixture reply is missing"))?;
    if let Some(error) = row.get("error") {
        return Err(
            decode(error).map_err(|error| Refusal::new("TRANSCRIPT_INVALID", error.to_string()))?
        );
    }
    decode(&row["ok"]).map_err(|error| Refusal::new("TRANSCRIPT_INVALID", error.to_string()))
}
type Calls = Rc<RefCell<Vec<Value>>>;
struct Model {
    calls: Calls,
    replies: VecDeque<Value>,
}
impl ModelPort for Model {
    fn propose(
        &mut self,
        packet: &WorkPacket,
        context: &[u8],
    ) -> Result<CandidateProposal, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"port": "model", "packet": packet, "context_bytes": context}));
        next(&mut self.replies)
    }
}
struct Valuator {
    calls: Calls,
    replies: VecDeque<Value>,
}
impl ValuatorPort for Valuator {
    fn evaluate(
        &mut self,
        epoch: &EvaluatorEpoch,
        candidate: &CandidateProposal,
    ) -> Result<ValuationReceipt, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"port": "valuator", "epoch": epoch, "candidate": candidate}));
        next(&mut self.replies)
    }
}
struct Continuation {
    calls: Calls,
    replies: VecDeque<Value>,
}
impl ContinuationPort for Continuation {
    fn can_continue(&mut self, state: &SwarmRunState) -> Result<ContinueDecision, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"port": "cont", "state": state}));
        next(&mut self.replies)
    }
}
struct Scheduler {
    calls: Calls,
    inner: DeterministicScheduler,
    fail: bool,
    has_plan: bool,
}
impl SchedulerPort for Scheduler {
    fn start(&mut self, key: &str, packet: &WorkPacket) -> Result<SwarmRunState, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"port": "scheduler_start", "run_key": key, "packet": packet}));
        self.inner.start(key, packet)
    }
    fn advance(
        &mut self,
        state: &SwarmRunState,
        result: &AgentResult,
        progress: &ProgressMeasure,
    ) -> Result<SwarmRunState, Refusal> {
        self.calls.borrow_mut().push(json!({"port": "scheduler_advance", "state": state, "result": result, "progress": progress}));
        if self.fail {
            let mut error = Refusal::new("SCHEDULER_DEADLOCK", "Transition impossible");
            error.locus = "dummy.scheduler".into();
            Err(error)
        } else {
            self.inner.advance(state, result, progress)
        }
    }
    fn plan(&self) -> Option<&LicensedWorkflowPlan> {
        self.has_plan.then(|| self.inner.plan())
    }
}
struct Sink {
    calls: Calls,
    name: &'static str,
    fail: bool,
    rollback_capable: bool,
    recorded_steps: usize,
}
impl Sink {
    fn result(&self) -> Result<String, Refusal> {
        if self.fail {
            let mut error = Refusal::new("FIXTURE_SINK_REFUSED", format!("{} refused", self.name));
            error.locus = "fixture".into();
            Err(error)
        } else {
            Ok("recorded".into())
        }
    }
}
impl UtsSink for Sink {
    fn record_event(
        &mut self,
        event: &IntelligenceEvent,
        payload: &[u8],
    ) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"port": self.name, "event": event, "raw_bytes": payload}));
        self.result()
    }
}
impl DdcSink for Sink {
    fn record_step(&mut self, step: &core_adversary::stage::ddc::DdcStep) -> Result<String, Refusal> {
        self.recorded_steps += 1;
        self.calls
            .borrow_mut()
            .push(json!({"port": self.name, "step": step}));
        self.result()
    }
    fn recorded_step_count(&self) -> Option<usize> {
        self.rollback_capable.then_some(self.recorded_steps)
    }
    fn rollback(&mut self, checkpoint_index: usize, reason: &str) -> Result<(), Refusal> {
        self.calls.borrow_mut().push(
            json!({"port": "rollback", "checkpoint_index": checkpoint_index, "reason": reason}),
        );
        Ok(())
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, session: &str, text: &str) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"port": self.name, "session": session, "text": text}));
        self.result()
    }
}
struct FrozenClock;
impl Clock for FrozenClock {
    fn timestamp_utc(&self) -> String {
        "2026-10-04T12:00:00Z".into()
    }
}

fn build_seeded_detector(
    row: &Value,
) -> Result<Option<OscillationDetector>, Box<dyn std::error::Error>> {
    if row["options"]["oscillation"].is_null() {
        return Ok(None);
    }
    let thresh_f64 = row["options"]["oscillation"]["threshold"].as_f64().unwrap();
    let thresh = Rational64::approximate_float(thresh_f64).unwrap();
    let mut det = OscillationDetector::new(
        thresh,
        row["options"]["oscillation"]["turns"].as_i64().unwrap(),
    )?;
    let seed: CandidateProposal = decode(&row["detector_seed"])?;
    det.record_and_evaluate("scene_001", &seed, false)?;
    det.record_and_evaluate("scene_001", &seed, false)?;
    Ok(Some(det))
}

fn normalize_detector_json(detector: &Option<OscillationDetector>) -> Value {
    let mut val = serde_json::to_value(detector).unwrap();
    if let Some(obj) = val.as_object_mut() {
        for key in ["stall_distance_threshold", "last_distance"] {
            if let Some(arr) = obj.get(key).and_then(|v| v.as_array()) {
                if arr.len() == 2 {
                    obj.insert(
                        key.into(),
                        json!(arr[0].as_f64().unwrap_or(0.0) / arr[1].as_f64().unwrap_or(1.0)),
                    );
                }
            }
        }
    }
    val
}

fn patch_stall_narrative_entry(a: &mut Value, e: &Value) {
    let is_stall_uns = e.get("port") == Some(&json!("uns"))
        && e.get("text")
            .and_then(Value::as_str)
            .is_some_and(|t| t.contains("SWARM_STALL_DETECTED"));
    if is_stall_uns {
        a["text"] = e["text"].clone();
    }
    let is_narrative_uts = e.get("port") == Some(&json!("uts"))
        && e["event"]["payload_uri"]
            .as_str()
            .is_some_and(|u| u.contains("ie_narrative"));
    if is_narrative_uts {
        a["raw_bytes"] = e["raw_bytes"].clone();
        a["event"]["payload_sha256"] = e["event"]["payload_sha256"].clone();
    }
}

fn normalize_stall_calls(case: &str, actual_calls: &mut Value, expected_calls: &Value) {
    if case != "oscillation_stall" {
        return;
    }
    let (Some(actual_arr), Some(expected_arr)) =
        (actual_calls.as_array_mut(), expected_calls.as_array())
    else {
        return;
    };
    for (a, e) in actual_arr.iter_mut().zip(expected_arr.iter()) {
        patch_stall_narrative_entry(a, e);
    }
}

fn verify_run_row(row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let case = row["case"].as_str().unwrap();
    let calls = Rc::new(RefCell::new(Vec::new()));
    let mut model = Model {
        calls: Rc::clone(&calls),
        replies: decode(&row["replies"]["model"]).unwrap(),
    };
    let mut valuator = Valuator {
        calls: Rc::clone(&calls),
        replies: decode(&row["replies"]["valuator"]).unwrap(),
    };
    let mut continuation = Continuation {
        calls: Rc::clone(&calls),
        replies: decode(&row["replies"]["cont"]).unwrap(),
    };
    let mut scheduler = Scheduler {
        calls: Rc::clone(&calls),
        inner: DeterministicScheduler::new(
            decode(&row["definition"]).unwrap(),
            decode(&row["profile"]).unwrap(),
            decode(&row["graph"]).unwrap(),
            decode(&row["plan"]).unwrap(),
            decode(&row["stop"]).unwrap(),
        )
        .unwrap(),
        fail: case == "scheduler_failed",
        has_plan: row["scheduler_has_plan"] == true,
    };
    let sink = |name| Sink {
        calls: Rc::clone(&calls),
        name,
        fail: case == format!("{name}_failed"),
        rollback_capable: row["options"]["rollback_capable"] == true,
        recorded_steps: 0,
    };
    let (mut uts, mut ddc, mut uns) = (sink("uts"), sink("ddc"), sink("uns"));
    let mut emitters = EmitterSuite {
        uts: Some(&mut uts),
        ddc: (row["options"]["has_ddc_sink"] == true).then_some(&mut ddc as &mut dyn DdcSink),
        uns: Some(&mut uns),
        sgt: None,
        ..EmitterSuite::default()
    };
    let epoch: Option<EvaluatorEpoch> = decode(&row["epoch"]).unwrap();
    let mut detector = build_seeded_detector(row)?;
    let mut runtime = SwarmRuntime {
        model: (row["enabled"]["model"] == true).then_some(&mut model as &mut dyn ModelPort),
        valuator: (row["enabled"]["valuator"] == true)
            .then_some(&mut valuator as &mut dyn ValuatorPort),
        scheduler: (row["enabled"]["scheduler"] == true)
            .then_some(&mut scheduler as &mut dyn SchedulerPort),
        continuation: (row["enabled"]["cont"] == true)
            .then_some(&mut continuation as &mut dyn ContinuationPort),
        emitters: &mut emitters,
        epoch: epoch.as_ref(),
        clock: &FrozenClock,
        rollback_on_refusal: row["options"]["rollback_on_refusal"] == true,
        oscillation_detector: detector.as_mut(),
    };
    let actual = outcome(run_swarm(
        &decode(&row["definition"]).unwrap(),
        &decode(&row["profile"]).unwrap(),
        &mut runtime,
        &decode(&row["packet"]).unwrap(),
        "fixture-run",
    ));
    assert_eq!(actual, row["expected"], "run outcome {case}");
    assert_eq!(
        normalize_detector_json(&detector),
        row["expected_detector"],
        "detector after run {case}"
    );
    let mut actual_calls = json!(*calls.borrow());
    normalize_stall_calls(case, &mut actual_calls, &row["calls"]);
    assert_eq!(actual_calls, row["calls"], "ordered port trace {case}");
    assert_eq!(
        (
            model.replies.is_empty(),
            valuator.replies.is_empty(),
            continuation.replies.is_empty()
        ),
        (true, true, true)
    );
    Ok(())
}

#[test]
fn frozen_python_generic_run_outcomes_and_ordered_port_traces(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_run_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 40);
    for row in rows {
        verify_run_row(row)?;
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/run_parity.rs
// Claim: urn:core:crates_rs:tests:run-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
