use core_adversary::authorization::AuthorizationTime;
use core_adversary::carrier::parse_carrier_json;
use core_adversary::evidence::ObstructionMeasurement;
use core_adversary::obstruction_identification::{
    execute_act2_obstruction_identification, ObstructionIdentificationInput,
};
use core_adversary::scoring_ports::{CochainScoringPort, CochainScoringRequest};
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{
    Clock, DdcSink, EmitterSuite, IntelligenceEvent, PacketSink, SgtSink, UnsSink, UtsSink,
};
use core_adversary::stage::ports::Refusal;
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
struct Scorer {
    calls: Rc<RefCell<Vec<Value>>>,
    measurement: ObstructionMeasurement,
    failed: bool,
}
impl CochainScoringPort for Scorer {
    fn identify_obstructions(
        &mut self,
        request: &CochainScoringRequest<'_>,
    ) -> Result<ObstructionMeasurement, Refusal> {
        self.calls.borrow_mut().push(json!({"sink":"scorer","network":request.network.to_dict()?,"cochain":request.initial_cochain.to_dict(),"ablation_flags":request.ablation_flags}));
        if self.failed {
            Err(refused("FIXTURE_SCORER_REFUSED", "scorer unavailable"))
        } else {
            Ok(self.measurement.clone())
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
        panic!("Act II must not emit SGT")
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, _session: &str, _text: &str) -> Result<String, Refusal> {
        panic!("Act II must not emit UNS")
    }
}

fn verify_obstruction_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let carrier = parse_carrier_json(Some(row["carrier_json"].as_str().unwrap()))?;
    let input = ObstructionIdentificationInput {
        network: carrier.network(),
        initial_cochain: carrier.cochain(),
        ablation_flags: row["flags"].as_object(),
        run_key: "obstruction_fixture",
        now_utc: row["timestamp"].as_str().unwrap(),
    };
    let calls = Rc::new(RefCell::new(Vec::new()));
    let mut scorer = Scorer {
        calls: calls.clone(),
        measurement: ObstructionMeasurement::from_json(&row["measurement"])?,
        failed: row["scorer_failed"].as_bool().unwrap(),
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
        ..EmitterSuite::default()
    };
    let result = execute_act2_obstruction_identification(
        &input,
        (row["port"] == true).then_some(&mut scorer as &mut dyn CochainScoringPort),
        mask.map(|_| &mut suite),
        &AuthorizationTime {
            event_clock: &FrozenClock,
            dda_timestamp: "2026-10-04 12:00:00 UTC",
        },
    );
    let actual = match result {
        Ok(value) => {
            assert_eq!(
                value.measurement().to_dict()?,
                row["expected"]["ok"]["measurement"]
            );
            assert_eq!(value.narrative(), &row["expected"]["ok"]["narrative"]);
            json!({"ok":value.to_dict()?})
        }
        Err(error) => json!({"error":error}),
    };
    assert_eq!(actual, row["expected"], "obstruction vector {index}");
    assert_eq!(
        json!(*calls.borrow()),
        row["calls"],
        "obstruction trace {index}"
    );
    Ok(())
}

#[test]
fn frozen_python_obstruction_identification_typed_port_and_exact_unicode_r_step(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/python_obstruction_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors")?;
    assert_eq!(rows.len(), 54);
    for (index, row) in rows.iter().enumerate() {
        verify_obstruction_row(index, row)?;
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/obstruction_parity.rs
// Claim: urn:core:crates_rs:tests:obstruction-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
