use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{
    build_intelligence_event, emit_event, Clock, DdcSink, EmitterSuite, EventDescriptor,
    IntelligenceEvent, PacketSink, Payload, SgtSink, TurnSink, UnsSink, UtsSink,
};
use core_adversary::stage::ports::Refusal;
use serde::de::DeserializeOwned;
use serde_json::{json, Map, Value};
use std::cell::RefCell;
use std::rc::Rc;

fn decode<T: DeserializeOwned>(value: &Value) -> Result<T, serde_json::Error> {
    serde_json::from_slice(&serde_json::to_vec(value)?)
}
struct FrozenClock;
impl Clock for FrozenClock {
    fn timestamp_utc(&self) -> String {
        "2026-10-04T12:00:00Z".into()
    }
}
struct Sink {
    name: &'static str,
    failed: String,
    calls: Rc<RefCell<Vec<Value>>>,
}
impl Sink {
    fn result(&self) -> Result<String, Refusal> {
        if self.failed == self.name {
            let mut refusal =
                Refusal::new("FIXTURE_SINK_REFUSED", format!("{} refused", self.name));
            refusal.locus = "fixture".into();
            Err(refusal)
        } else {
            Ok("recorded".into())
        }
    }
}
impl UtsSink for Sink {
    fn record_event(&mut self, event: &IntelligenceEvent, raw: &[u8]) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink": self.name, "event": event, "raw_bytes": raw}));
        self.result()
    }
}
impl DdcSink for Sink {
    fn record_step(&mut self, step: &DdcStep) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink": self.name, "step": step}));
        self.result()
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, session: &str, text: &str) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink": self.name, "session": session, "text": text}));
        self.result()
    }
}
impl PacketSink for Sink {
    fn record_packet(&mut self, raw: &[u8]) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink": self.name, "raw_bytes": raw}));
        self.result()
    }
}
impl TurnSink for Sink {
    fn record_turn(
        &mut self,
        session: &str,
        payload: &Map<String, Value>,
    ) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink": self.name, "session": session, "payload": payload}));
        self.result()
    }
}

fn eval_build_emission_row(row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    let descriptor = EventDescriptor {
        ie_id: "fixture-event",
        actor_id: "fixture-actor",
        actor_kind: "SWARM_AGENT",
        event_kind: row["kind"].as_str().unwrap(),
        source_system: "oeas",
        session_id: "fixture-session",
        parent_ie_id: Vec::new(),
        object_ids: Vec::new(),
        terminal: false,
    };
    let bytes;
    let payload = if let Some(value) = row["payload"].get("bytes") {
        bytes = decode::<Vec<u8>>(value)?;
        Payload::Bytes(&bytes)
    } else if let Some(value) = row["payload"].get("text") {
        Payload::Text(value.as_str().unwrap())
    } else {
        Payload::Object(row["payload"]["object"].as_object().unwrap())
    };
    let (event, raw) = build_intelligence_event(descriptor, payload, &FrozenClock)?;
    Ok(json!({"event": event, "raw_bytes": raw}))
}

fn eval_emit_emission_row(index: usize, row: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    let calls = Rc::new(RefCell::new(Vec::new()));
    let sink = |name| Sink {
        name,
        calls: Rc::clone(&calls),
        failed: row["failed"].as_str().unwrap_or("").into(),
    };
    let (mut uts, mut ddc, mut uns, mut sgt) = (sink("uts"), sink("ddc"), sink("uns"), sink("sgt"));
    let sgt = if row["sgt_mode"] == "packet" { SgtSink::Packet(&mut sgt) } else { SgtSink::Turn(&mut sgt) };
    let mut suite = EmitterSuite {
        uts: Some(&mut uts),
        ddc: Some(&mut ddc),
        uns: Some(&mut uns),
        sgt: Some(sgt),
        ..EmitterSuite::default()
    };
    let event: IntelligenceEvent = decode(&row["event"])?;
    let raw: Vec<u8> = decode(&row["raw_bytes"])?;
    let step: Option<DdcStep> = decode(&row["step"])?;
    let outcome = emit_event(&event, &raw, &mut suite, step.as_ref(), row["sgt_payload"].as_object());
    assert_eq!(json!(*calls.borrow()), row["calls"], "sink order/custody vector {index}");
    Ok(match outcome {
        Ok(id) => json!({"ok": id}),
        Err(error) => json!({"error": error}),
    })
}

fn check_invalid_emission_row(row: &Value) {
    if row["op"] == "event_decode" {
        let error = decode::<IntelligenceEvent>(&row["input"]).err().unwrap().to_string();
        let message = error.rsplit_once(" at line ").map_or(error.as_str(), |(m, _)| m);
        assert_eq!(message, row["python_error"].as_str().unwrap());
    } else {
        let descriptor = EventDescriptor {
            ie_id: "",
            actor_id: "actor",
            actor_kind: "ACTOR",
            event_kind: "PROPOSAL",
            source_system: "oeas",
            session_id: "session",
            parent_ie_id: Vec::new(),
            object_ids: Vec::new(),
            terminal: false,
        };
        let error = build_intelligence_event(descriptor, Payload::Bytes(b"payload"), &FrozenClock).err().unwrap();
        assert_eq!(error.message, row["python_error"].as_str().unwrap());
        assert_eq!(error.to_string(), error.message);
    }
}

#[test]
fn frozen_python_ddc_and_ordered_emission_vectors() -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_emission_v1.json")).unwrap();
    let vectors = fixture["vectors"].as_array().unwrap();
    assert_eq!(vectors.len(), 50);
    for (index, row) in vectors.iter().enumerate() {
        let op = row["op"].as_str().unwrap();
        if matches!(op, "event_decode" | "build_invalid") {
            check_invalid_emission_row(row);
            continue;
        }
        let actual = match op {
            "ddc" => serde_json::to_value(decode::<DdcStep>(&row["input"]).unwrap()).unwrap(),
            "build" => eval_build_emission_row(row)?,
            "emit" => eval_emit_emission_row(index, row)?,
            other => panic!("unknown op {other}"),
        };
        assert_eq!(actual, row["expected"], "emission vector {index}");
    }
    Ok(())
}

#[test]
fn ddc_actions_reject_authority_narrative_and_inexact_wire_values(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_emission_v1.json"))?;
    let original = &fixture["vectors"][0]["input"];
    for (key, value) in [
        ("authority_effect", json!("Accept")),
        ("phi_1", json!(1.5)),
        ("letter", json!("IMPORT")),
        ("before_class", json!(" invalid ")),
        ("narrative", json!("must stay out of the DDC stream")),
    ] {
        let mut step = original.clone();
        step[key] = value;
        assert!(decode::<DdcStep>(&step).is_err(), "must refuse {key}");
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/stage/emission_parity.rs
// Claim: urn:core:crates_rs:tests:emission-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
