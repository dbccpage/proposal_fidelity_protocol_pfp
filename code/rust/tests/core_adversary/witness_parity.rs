use core_adversary::authorization::AuthorizationTime;
use core_adversary::independent_witness::{
    execute_act5_independent_witness, IndependentWitnessInput,
};
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{
    CemeterySink, Clock, DdcSink, EmitterSuite, IntelligenceEvent, PacketSink, SgtSink, UnsSink,
    UtsSink,
};
use core_adversary::stage::genealogy::CemeteryHeadstone;
use core_adversary::stage::packets::CandidateProposal;
use core_adversary::stage::ports::{Refusal, SeatPort, SeatTurnReply, SeatTurnRequest};
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
fn fixture_refusal(code: &str, message: impl Into<String>) -> Refusal {
    let mut error = Refusal::new(code, message);
    error.locus = "fixture".into();
    error
}
struct Seats {
    calls: Rc<RefCell<Vec<Value>>>,
    replies: Vec<SeatTurnReply>,
    failed: usize,
    count: usize,
}
impl SeatPort for Seats {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        self.calls.borrow_mut().push(
            json!({"sink":"seat","request":request,"request_digest":request.request_digest()?}),
        );
        self.count += 1;
        if self.count == self.failed {
            return Err(fixture_refusal("FIXTURE_SEAT_REFUSED", "seat unavailable"));
        }
        Ok(self.replies[(self.count - 1).min(self.replies.len() - 1)].clone())
    }
}
struct Cemetery {
    calls: Rc<RefCell<Vec<Value>>>,
    failed: usize,
    count: usize,
}
impl CemeterySink for Cemetery {
    fn record_headstone(&mut self, headstone: &CemeteryHeadstone) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":"cemetery","headstone":headstone.to_dict()}));
        self.count += 1;
        if self.count == self.failed {
            Err(fixture_refusal(
                "FIXTURE_CEMETERY_REFUSED",
                "cemetery unavailable",
            ))
        } else {
            Ok("recorded".into())
        }
    }
}
struct Sink {
    name: &'static str,
    calls: Rc<RefCell<Vec<Value>>>,
    failed: String,
}
impl Sink {
    fn result(&self) -> Result<String, Refusal> {
        if self.name == self.failed {
            Err(fixture_refusal(
                "FIXTURE_SINK_REFUSED",
                format!("{} refused", self.name),
            ))
        } else {
            Ok("recorded".into())
        }
    }
}
impl UtsSink for Sink {
    fn record_event(&mut self, event: &IntelligenceEvent, raw: &[u8]) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":self.name,"event":event,"raw_bytes":raw}));
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
    fn record_packet(&mut self, _raw: &[u8]) -> Result<String, Refusal> {
        panic!("Act V must not emit SGT")
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, _session: &str, _text: &str) -> Result<String, Refusal> {
        panic!("Act V must not emit UNS")
    }
}

fn verify_witness_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let wire = &row["input"];
    let candidates: Vec<CandidateProposal> = serde_json::from_value(wire["candidates"].clone())?;
    let dead = wire["dead_candidates"]
        .as_array()
        .unwrap()
        .iter()
        .map(CemeteryHeadstone::from_json)
        .collect::<Result<Vec<_>, _>>()?;
    let payloads: BTreeMap<String, Vec<u8>> =
        serde_json::from_value(wire["candidate_payloads"].clone())?;
    let input = IndependentWitnessInput {
        run_key: wire["run_key"].as_str().unwrap(),
        objective: wire["objective"].as_str().unwrap(),
        candidates: &candidates,
        dead_candidates: &dead,
        candidate_payloads: &payloads,
        ablation_flags: wire["ablation_flags"].as_object(),
        max_critique_rounds: row["max_rounds"].as_i64().unwrap(),
        now_utc: wire["now_utc"].as_str().unwrap(),
    };
    let calls = Rc::new(RefCell::new(Vec::new()));
    let mut seats = Seats {
        calls: calls.clone(),
        replies: serde_json::from_value(row["replies"].clone())?,
        failed: row["seat_failure"].as_u64().unwrap() as usize,
        count: 0,
    };
    let mut cemetery = Cemetery {
        calls: calls.clone(),
        failed: row["cemetery_failure"].as_u64().unwrap() as usize,
        count: 0,
    };
    let failed = row["failed"].as_str().unwrap();
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
        cemetery: (row["cemetery"] == true).then_some(&mut cemetery as &mut dyn CemeterySink),
        ..EmitterSuite::default()
    };
    let result = execute_act5_independent_witness(
        &input,
        (row["port"] == true).then_some(&mut seats as &mut dyn SeatPort),
        mask.map(|_| &mut suite),
        &AuthorizationTime {
            event_clock: &FrozenClock,
            dda_timestamp: "2026-10-04 12:00:00 UTC",
        },
    );
    let actual = match result {
        Ok(value) => {
            assert_eq!(
                json!(value.round_count()),
                row["expected"]["ok"]["round_count"]
            );
            assert_eq!(
                json!(value.surviving_candidates()),
                row["expected"]["ok"]["surviving_candidates"]
            );
            assert_eq!(
                json!(value
                    .dead_candidates()
                    .iter()
                    .map(CemeteryHeadstone::to_dict)
                    .collect::<Vec<_>>()),
                row["expected"]["ok"]["dead_candidates"]
            );
            assert_eq!(json!(value.critiques()), row["expected"]["ok"]["critiques"]);
            assert_eq!(
                json!(value.critiques_data()),
                row["expected"]["ok"]["critiques_data"]
            );
            assert_eq!(
                json!(value.critique_verdicts()),
                row["expected"]["ok"]["critique_verdicts"]
            );
            assert_eq!(value.narrative(), &row["expected"]["ok"]["narrative"]);
            json!({"ok":value.to_dict()?})
        }
        Err(error) => json!({"error":error}),
    };
    assert_eq!(actual, row["expected"], "witness vector {index}");
    assert_eq!(
        json!(*calls.borrow()),
        row["calls"],
        "witness trace {index}"
    );
    Ok(())
}

#[test]
fn frozen_python_independent_witness_requests_custody_kills_and_d_step(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_witness_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors")?;
    assert_eq!(rows.len(), 119);
    for (index, row) in rows.iter().enumerate() {
        verify_witness_row(index, row)?;
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/witness_parity.rs
// Claim: urn:core:crates_rs:tests:witness-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
