use core_adversary::authorization::AuthorizationTime;
use core_adversary::carrier::parse_carrier_json;
use core_adversary::carrier_framing::{execute_act1_carrier_framing, CarrierFramingInput};
use core_adversary::evidence::ObstructionMeasurement;
use core_adversary::gauge_break::{execute_act4_gauge_break, GaugeBreakInput};
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::diagnostics::{SbeDiagnosticPort, SbeReport};
use core_adversary::stage::emission::{
    AntibodySink, Clock, DdcSink, EmitterSuite, IntelligenceEvent, PacketSink, SgtSink, UnsSink,
    UtsSink,
};
use core_adversary::stage::genealogy::AntibodyEntry;
use core_adversary::stage::ports::{Refusal, SeatPort, SeatTurnReply, SeatTurnRequest};
use serde_json::{json, Value};
use std::cell::RefCell;
use std::rc::Rc;

struct FrozenClock;
impl Clock for FrozenClock {
    fn timestamp_utc(&self) -> String {
        "2026-10-04T12:00:00Z".into()
    }
}
fn refused(code: &str, message: impl Into<String>) -> Refusal {
    let mut error = Refusal::new(code, message);
    error.locus = "fixture".into();
    error
}
struct Diagnostic {
    reports: Value,
    calls: Rc<RefCell<Vec<Value>>>,
    act1: bool,
}
impl SbeDiagnosticPort for Diagnostic {
    fn compute(&mut self, text: &str, dim: usize) -> Result<SbeReport, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":"sbe","text":text,"dim":dim}));
        SbeReport::from_json(if self.act1 {
            &self.reports[0]
        } else {
            &self.reports[text]
        })
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
            Err(refused(
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
        panic!("no SGT in Acts I/IV")
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, _session: &str, _text: &str) -> Result<String, Refusal> {
        panic!("no UNS in Acts I/IV")
    }
}
struct History {
    entries: Vec<AntibodyEntry>,
    calls: Rc<RefCell<Vec<Value>>>,
    failed: bool,
}
impl AntibodySink for History {
    fn record_failure(&mut self, _failure: &str, _constraint: &str) -> Result<String, Refusal> {
        panic!("Act I only loads history")
    }
    fn load_antibodies(&mut self, context_key: &str) -> Result<Vec<AntibodyEntry>, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":"antibodies","context_key":context_key}));
        if self.failed {
            Err(refused("FIXTURE_ANTIBODIES_REFUSED", "history unavailable"))
        } else {
            Ok(self.entries.clone())
        }
    }
}
struct Seats {
    reply: SeatTurnReply,
    calls: Rc<RefCell<Vec<Value>>>,
    failed: bool,
}
impl SeatPort for Seats {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        self.calls.borrow_mut().push(
            json!({"sink":"seat","request":request,"request_digest":request.request_digest()?}),
        );
        if self.failed {
            Err(refused("FIXTURE_SEAT_REFUSED", "seat unavailable"))
        } else {
            Ok(self.reply.clone())
        }
    }
}
fn replay_act1(
    row: &Value,
    input: &Value,
    carrier_json: &str,
    timestamp: &str,
    diagnostic: &mut Diagnostic,
    emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<Value, Box<dyn std::error::Error>> {
    match execute_act1_carrier_framing(
        &CarrierFramingInput {
            carrier_json: Some(carrier_json),
            objective: input["objective"].as_str().unwrap(),
            run_key: "perception_fixture",
            now_utc: timestamp,
        },
        diagnostic,
        emitters,
        time,
    ) {
        Ok(outcome) => {
            assert_eq!(
                outcome.network().to_dict()?,
                row["expected"]["ok"]["network"]
            );
            assert_eq!(
                json!(outcome.initial_cochain().to_dict()),
                row["expected"]["ok"]["cochain"]
            );
            assert_eq!(
                outcome
                    .active_antibodies()
                    .iter()
                    .map(AntibodyEntry::to_dict)
                    .collect::<Vec<_>>(),
                row["expected"]["ok"]["active_antibodies"]
                    .as_array()
                    .unwrap()
                    .clone()
            );
            assert_eq!(
                outcome.prompt_sbe().to_dict(),
                row["expected"]["ok"]["prompt_sbe"]
            );
            assert_eq!(outcome.narrative(), &row["expected"]["ok"]["narrative"]);
            assert_eq!(
                outcome.carrier_status(),
                row["expected"]["ok"]["narrative"]["carrier_status"]
                    .as_str()
                    .unwrap()
            );
            Ok(json!({"ok":outcome.to_dict()?}))
        }
        Err(error) => Ok(json!({"error":error})),
    }
}

#[allow(clippy::too_many_arguments)]
fn replay_act4(
    row: &Value,
    input: &Value,
    carrier_json: &str,
    timestamp: &str,
    diagnostic: &mut Diagnostic,
    seats: &mut Option<Seats>,
    emitters: Option<&mut EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<Value, Box<dyn std::error::Error>> {
    let parsed = parse_carrier_json(Some(carrier_json))?;
    let contents: Vec<String> = input["candidates_data"]
        .as_array()
        .unwrap()
        .iter()
        .map(|data| data["content"].as_str().unwrap_or("").to_string())
        .collect();
    let measurement = ObstructionMeasurement::from_json(&input["measurement"])?;
    match execute_act4_gauge_break(
        &GaugeBreakInput {
            network: parsed.network(),
            initial_cochain: parsed.cochain(),
            candidate_contents: &contents,
            measurement: &measurement,
            ablation_flags: input["flags"].as_object(),
            run_key: "lift_fixture",
            now_utc: timestamp,
        },
        diagnostic,
        (input["seat_port"] == true).then(|| seats.as_mut().unwrap() as &mut dyn SeatPort),
        emitters,
        time,
    ) {
        Ok(outcome) => {
            assert_eq!(
                outcome.triggered(),
                row["expected"]["ok"]["gauge_break_triggered"]
                    .as_bool()
                    .unwrap()
            );
            assert_eq!(
                outcome.network().to_dict()?,
                row["expected"]["ok"]["network"]
            );
            assert_eq!(
                json!(outcome.cochain().to_dict()),
                row["expected"]["ok"]["cochain"]
            );
            assert_eq!(outcome.telemetry(), &row["expected"]["ok"]["telemetry"]);
            assert_eq!(outcome.narrative(), &row["expected"]["ok"]["narrative"]);
            Ok(json!({"ok":outcome.to_dict()?}))
        }
        Err(error) => Ok(json!({"error":error})),
    }
}

fn replay_row(act1: bool, index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let input = &row["input"];
    let calls = Rc::new(RefCell::new(Vec::new()));
    let mut diagnostic = Diagnostic {
        reports: input["reports"].clone(),
        calls: calls.clone(),
        act1,
    };
    let make_sink = |name| Sink {
        name,
        calls: calls.clone(),
        failed: input["failed"].as_str().unwrap_or("").into(),
    };
    let mut uts = make_sink("uts");
    let mut ddc = make_sink("ddc");
    let mut uns = make_sink("uns");
    let mut sgt = make_sink("sgt");
    let entries = input["antibodies"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .map(|v| AntibodyEntry::from_json(v).unwrap())
                .collect()
        })
        .unwrap_or_default();
    let mut history = History {
        entries,
        calls: calls.clone(),
        failed: input["history_failed"] == true,
    };
    let mut seats = (!act1).then(|| Seats {
        reply: serde_json::from_value(input["reply"].clone()).unwrap(),
        calls: calls.clone(),
        failed: input["seat_failed"] == 1,
    });
    let mask = input["emission"].as_str();
    let mut suite = EmitterSuite {
        uts: mask
            .filter(|m| ["all", "uts"].contains(m))
            .map(|_| &mut uts as &mut dyn UtsSink),
        ddc: mask
            .filter(|m| ["all", "ddc"].contains(m))
            .map(|_| &mut ddc as &mut dyn DdcSink),
        uns: mask
            .filter(|m| *m == "all")
            .map(|_| &mut uns as &mut dyn UnsSink),
        sgt: mask
            .filter(|m| *m == "all")
            .map(|_| SgtSink::Packet(&mut sgt)),
        antibodies: (input["history_port"] == true)
            .then_some(&mut history as &mut dyn AntibodySink),
        ..EmitterSuite::default()
    };
    let mut emitters = mask.map(|_| &mut suite);
    let time = AuthorizationTime {
        event_clock: &FrozenClock,
        dda_timestamp: "2026-10-04 12:00:00 UTC",
    };
    let carrier_json = serde_json::to_string(&input["carrier_context"]).unwrap();
    let timestamp = input["timestamp"].as_str().unwrap();
    let actual = if act1 {
        replay_act1(
            row,
            input,
            &carrier_json,
            timestamp,
            &mut diagnostic,
            emitters.take(),
            &time,
        )?
    } else {
        replay_act4(
            row,
            input,
            &carrier_json,
            timestamp,
            &mut diagnostic,
            &mut seats,
            emitters.take(),
            &time,
        )?
    };
    assert_eq!(
        actual,
        row["expected"],
        "act {} vector {index}",
        if act1 { "I" } else { "IV" }
    );
    assert_eq!(
        json!(*calls.borrow()),
        row["calls"],
        "act {} trace {index}",
        if act1 { "I" } else { "IV" }
    );
    Ok(())
}

fn replay(act1: bool) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_perception_lift_v1.json"))?;
    let rows = fixture[if act1 { "act1" } else { "act4" }]
        .as_array()
        .ok_or("rows")?;
    assert_eq!(rows.len(), if act1 { 40 } else { 95 });
    for (index, row) in rows.iter().enumerate() {
        replay_row(act1, index, row)?;
    }
    Ok(())
}
#[test]
fn frozen_python_carrier_framing_history_and_injected_perception(
) -> Result<(), Box<dyn std::error::Error>> {
    replay(true)
}
#[test]
fn frozen_python_gauge_break_stagnation_and_exact_cochain_transport(
) -> Result<(), Box<dyn std::error::Error>> {
    replay(false)
}

// Origin: engine/crates_rs/tests/core_adversary/perception_lift_parity.rs
// Claim: urn:core:crates_rs:tests:perception-lift-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
