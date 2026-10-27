use core_adversary::authorization::{
    execute_act7_authorization_gate, AuthorizationGateInput, AuthorizationTime, CARRIER_DECLARED,
};
use core_adversary::evidence::{CandidateCheck, ObstructionMeasurement};
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{
    Clock, DdcSink, EmitterSuite, IntelligenceEvent, PacketSink, SgtSink, UnsSink, UtsSink,
};
use core_adversary::stage::packets::{CandidateProposal, Challenge};
use core_adversary::stage::ports::Refusal;
use serde_json::{json, Value};
use std::cell::RefCell;
use std::collections::BTreeMap;
use std::rc::Rc;

struct FrozenClock;
impl Clock for FrozenClock {
    fn timestamp_utc(&self) -> String {
        "2026-10-04T12:00:00Z".into()
    }
}
struct Sink {
    name: &'static str,
    calls: Rc<RefCell<Vec<Value>>>,
    failed: String,
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
    fn record_event(
        &mut self,
        event: &IntelligenceEvent,
        payload: &[u8],
    ) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":self.name,"event":event,"raw_bytes":payload}));
        self.result()
    }
}
impl DdcSink for Sink {
    fn record_step(&mut self, step: &DdcStep) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":self.name,"step":step}));
        self.result()
    }
}
impl PacketSink for Sink {
    fn record_packet(&mut self, _payload: &[u8]) -> Result<String, Refusal> {
        panic!("Act VII must not emit an SGT packet");
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, _session: &str, _text: &str) -> Result<String, Refusal> {
        panic!("Act VII must not emit an UNS narrative");
    }
}

fn verify_authorization_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let wire = &row["input"];
    let candidates: Vec<CandidateProposal> =
        serde_json::from_value(wire["surviving_candidates"].clone())?;
    let critiques: Vec<Challenge> = serde_json::from_value(wire["critiques"].clone())?;
    let measurement = ObstructionMeasurement::from_json(&wire["measurement"]).ok();
    let checks = wire["candidate_checks"]
        .as_object()
        .ok_or("checks object")?
        .iter()
        .map(|(key, value)| Ok((key.clone(), CandidateCheck::from_json(value)?)))
        .collect::<Result<BTreeMap<_, _>, Refusal>>()?;
    let verdicts: BTreeMap<String, String> =
        serde_json::from_value(wire["critique_verdicts"].clone())?;
    let input = AuthorizationGateInput {
        run_key: wire["run_key"].as_str().ok_or("run key")?,
        surviving_candidates: &candidates,
        critiques: &critiques,
        measurement: measurement.as_ref(),
        candidate_checks: &checks,
        carrier_context: wire.get("carrier_context").and_then(Value::as_object),
        ablation_flags: wire.get("ablation_flags").and_then(Value::as_object),
        delta2_defect: wire.get("delta2_defect"),
        delta3_defect: wire.get("delta3_defect"),
        regge_converged: wire.get("regge_converged"),
        carrier_status: wire
            .get("carrier_status")
            .map(|value| value.as_str().unwrap_or(""))
            .unwrap_or(CARRIER_DECLARED),
        critique_verdicts: &verdicts,
        fixture_seats: &wire["fixture_seats"],
        now_utc: wire["now_utc"].as_str().ok_or("now_utc")?,
    };
    run_and_assert_authorization(&input, index, row)
}

fn run_and_assert_authorization(
    input: &AuthorizationGateInput<'_>,
    index: usize,
    row: &Value,
) -> Result<(), Box<dyn std::error::Error>> {
    let calls = Rc::new(RefCell::new(Vec::new()));
    let failed = row["failed"].as_str().unwrap_or("");
    let mut uts = Sink {
        name: "uts",
        calls: calls.clone(),
        failed: failed.into(),
    };
    let mut ddc = Sink {
        name: "ddc",
        calls: calls.clone(),
        failed: failed.into(),
    };
    let mut sgt = Sink {
        name: "sgt",
        calls: calls.clone(),
        failed: failed.into(),
    };
    let mut uns = Sink {
        name: "uns",
        calls: calls.clone(),
        failed: failed.into(),
    };
    let mask = row["emission"].as_str();
    let mut suite = EmitterSuite {
        uts: mask
            .filter(|m| ["all", "uts"].contains(m))
            .map(|_| &mut uts as &mut dyn UtsSink),
        ddc: mask
            .filter(|m| ["all", "ddc"].contains(m))
            .map(|_| &mut ddc as &mut dyn DdcSink),
        sgt: mask
            .filter(|m| *m == "all")
            .map(|_| SgtSink::Packet(&mut sgt)),
        uns: mask
            .filter(|m| *m == "all")
            .map(|_| &mut uns as &mut dyn UnsSink),
        ..EmitterSuite::default()
    };
    let result = execute_act7_authorization_gate(
        input,
        mask.map(|_| &mut suite),
        &AuthorizationTime {
            event_clock: &FrozenClock,
            dda_timestamp: "2026-10-04 12:00:00 UTC",
        },
    );
    let actual = match result {
        Ok(value) => {
            assert_eq!(
                json!(value.status()),
                row["expected"]["ok"]["status"],
                "authorization vector {index}"
            );
            assert_eq!(
                json!(value.selected_candidate_id()),
                row["expected"]["ok"]["selected_candidate_id"]
            );
            assert_eq!(json!(value.proposal()), row["expected"]["ok"]["proposal"]);
            assert_eq!(
                json!(value.is_authorized()),
                row["expected"]["ok"]["is_authorized"]
            );
            assert_eq!(value.narrative(), &row["expected"]["ok"]["narrative"]);
            json!({"ok":value.to_dict()?})
        }
        Err(error) => json!({"error":error}),
    };
    assert_eq!(actual, row["expected"], "authorization vector {index}");
    assert_eq!(
        json!(*calls.borrow()),
        row["calls"],
        "ordered sink trace {index}"
    );
    Ok(())
}

#[test]
fn frozen_python_authorization_outcomes_receipt_digests_and_ordered_emission(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_authorization_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 284);
    for (index, row) in rows.iter().enumerate() {
        verify_authorization_row(index, row)?;
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/authorization_parity.rs
// Claim: urn:core:crates_rs:tests:authorization-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
