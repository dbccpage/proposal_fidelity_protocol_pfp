#[path = "support/candidate_audit_identity_v2.rs"]
mod candidate_audit_identity_v2;

use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{
    Clock, DdcSink, EmitterSuite, IntelligenceEvent, PacketSink, SgtSink, UnsSink, UtsSink,
};
use core_adversary::stage::packets::CandidateProposal;
use core_adversary::stage::ports::Refusal;
use core_adversary::authorization::AuthorizationTime;
use core_adversary::candidate_checks::{execute_candidate_checks, CandidateChecksInput};
use core_adversary::checker_ports::{CandidateCheckRequest, CandidateCheckerPort};
use core_adversary::evidence::{
    sha256_ref, CandidateCheck, CandidateCheckInput, CheckerVerdict, ObstructionMeasurement,
};
use serde_json::{json, Map, Value};
use std::cell::RefCell;
use std::collections::BTreeMap;
use std::rc::Rc;

struct FrozenClock;
impl Clock for FrozenClock {
    fn timestamp_utc(&self) -> String {
        "2026-10-04T12:00:00Z".into()
    }
}
struct Checker {
    mode: String,
    calls: Rc<RefCell<Vec<Value>>>,
}
impl Checker {
    fn build_check(&self, request: &CandidateCheckRequest<'_>, verdict: CheckerVerdict) -> Result<CandidateCheck, Refusal> {
        let digest = sha256_ref(if self.mode == "unbound" { b"wrong" } else { request.candidate_bytes });
        let receipt = format!(r#"{{"checker": "exact.e\u0301", "content": "{digest}"}}"#).into_bytes();
        let measured = verdict != CheckerVerdict::NotMeasured;
        CandidateCheck::new(CandidateCheckInput {
            verdict,
            candidate_id: if self.mode == "wrong_candidate" {
                sha256_ref(b"other-candidate")
            } else {
                request.candidate_id.into()
            },
            candidate_content_sha256: digest,
            checker_id: "exact.e\u{301}".into(),
            checker_receipt_sha256: measured.then(|| sha256_ref(&receipt)),
            checker_receipt_bytes: if measured { receipt } else { Vec::new() },
            reason: (if measured { "checked e\u{301}" } else { "not checked" }).into(),
        })
    }
}
impl CandidateCheckerPort for Checker {
    fn check_candidate(
        &mut self,
        request: &CandidateCheckRequest<'_>,
    ) -> Result<CandidateCheck, Refusal> {
        self.calls.borrow_mut().push(json!({"port":"checker","run_key":request.run_key,
            "objective":request.objective,"candidate_id":request.candidate_id,
            "candidate_hex":hex::encode(request.candidate_bytes),"carrier_context":request.carrier_context}));
        if self.mode == "error" || (self.mode == "second_error" && request.candidate_bytes == b"\xff\x00") {
            let mut error = Refusal::new("FIXTURE_CHECK_REFUSED", "checker unavailable");
            error.locus = "fixture".into();
            return Err(error);
        }
        let verdict = match self.mode.as_str() {
            "rejected" => CheckerVerdict::Rejected,
            "not_measured" => CheckerVerdict::NotMeasured,
            _ => CheckerVerdict::Accepted,
        };
        self.build_check(request, verdict)
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
        panic!("checker COMM must not emit SGT")
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, _session: &str, _text: &str) -> Result<String, Refusal> {
        panic!("checker COMM must not emit UNS")
    }
}

fn verify_candidate_check_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let wire = &row["input"];
    let candidates: Vec<CandidateProposal> = serde_json::from_value(wire["candidates"].clone())?;
    let payloads: BTreeMap<String, Vec<u8>> = wire["candidate_payloads"]
        .as_object()
        .unwrap()
        .iter()
        .map(|(k, v)| (k.clone(), hex::decode(v.as_str().unwrap()).unwrap()))
        .collect();
    let measurement = (!wire["measurement"].is_null())
        .then(|| ObstructionMeasurement::from_json(&wire["measurement"]).unwrap());
    let input = CandidateChecksInput {
        run_key: wire["run_key"].as_str().unwrap(),
        objective: wire["objective"].as_str().unwrap(),
        candidates: &candidates,
        candidate_payloads: &payloads,
        carrier_context: wire["carrier_context"].as_object(),
        measurement: measurement.as_ref(),
        carrier_state_hash: wire["carrier_state_hash"].as_str(),
        now_utc: wire["now_utc"].as_str().unwrap(),
    };
    run_and_assert_candidate_checks(&input, index, row)
}

fn run_and_assert_candidate_checks(
    input: &CandidateChecksInput<'_>,
    index: usize,
    row: &Value,
) -> Result<(), Box<dyn std::error::Error>> {
    let calls = Rc::new(RefCell::new(Vec::new()));
    let mode = row["mode"].as_str().unwrap();
    let mut checker = Checker { mode: mode.into(), calls: calls.clone() };
    let failed = row["failed"].as_str().unwrap();
    let mut uts = Sink { name: "uts", failed: failed.into(), calls: calls.clone() };
    let mut ddc = Sink { name: "ddc", failed: failed.into(), calls: calls.clone() };
    let mut sgt = Sink { name: "sgt", failed: failed.into(), calls: calls.clone() };
    let mut uns = Sink { name: "uns", failed: failed.into(), calls: calls.clone() };
    let mask = row["emission"].as_str();
    let mut suite = EmitterSuite {
        uts: mask.filter(|m| ["all", "uts"].contains(m)).map(|_| &mut uts as &mut dyn UtsSink),
        ddc: mask.filter(|m| ["all", "ddc"].contains(m)).map(|_| &mut ddc as &mut dyn DdcSink),
        sgt: mask.filter(|m| *m == "all").map(|_| SgtSink::Packet(&mut sgt)),
        uns: mask.filter(|m| *m == "all").map(|_| &mut uns as &mut dyn UnsSink),
        ..EmitterSuite::default()
    };
    let outcome = execute_candidate_checks(
        (mode != "null").then_some(&mut checker as &mut dyn CandidateCheckerPort),
        input,
        mask.map(|_| &mut suite),
        &AuthorizationTime {
            event_clock: &FrozenClock,
            dda_timestamp: "2026-10-04 12:00:00 UTC",
        },
    );
    let actual = match outcome {
        Ok(checks) => {
            json!({"ok":Value::Object(checks.iter().map(|(id,check)|(id.clone(),check.to_dict())).collect::<Map<_,_>>())})
        }
        Err(error) => json!({"error":error}),
    };
    assert_eq!(actual, row["expected"], "candidate-check vector {index}");
    assert_eq!(
        json!(*calls.borrow()),
        candidate_audit_identity_v2::calls_with_audit_identity_v2(&row["calls"]),
        "candidate-check trace {index}"
    );
    Ok(())
}

#[test]
fn frozen_python_checker_v1_custody_with_declared_audit_identity_v2(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_candidate_checks_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 78);
    for (index, row) in rows.iter().enumerate() {
        verify_candidate_check_row(index, row)?;
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/candidate_check_parity.rs
// Claim: urn:core:crates_rs:tests:candidate-check-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
