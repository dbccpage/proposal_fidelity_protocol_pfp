use core_adversary::authorization::AuthorizationTime;
use core_adversary::evidence::ObstructionMeasurement;
use core_adversary::residual_ledger::{execute_act6_residual_ledger, ResidualLedgerInput};
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{
    AntibodySink, Clock, DdcSink, EmitterSuite, IntelligenceEvent, PacketSink, SgtSink, UnsSink,
    UtsSink,
};
use core_adversary::stage::genealogy::{AntibodyEntry, CemeteryHeadstone};
use core_adversary::stage::packets::Challenge;
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
struct History {
    calls: Rc<RefCell<Vec<Value>>>,
    failed: usize,
    count: usize,
}
impl AntibodySink for History {
    fn record_failure(&mut self, pattern: &str, rule: &str) -> Result<String, Refusal> {
        self.calls
            .borrow_mut()
            .push(json!({"sink":"history","failure_pattern":pattern,"constraint_rule":rule}));
        self.count += 1;
        if self.count == self.failed {
            let mut error = Refusal::new("FIXTURE_HISTORY_REFUSED", "history unavailable");
            error.locus = "fixture".into();
            Err(error)
        } else {
            Ok("recorded".into())
        }
    }
    fn load_antibodies(&mut self, _context: &str) -> Result<Vec<AntibodyEntry>, Refusal> {
        panic!("Act VI must not load antibodies")
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
            let mut error = Refusal::new("FIXTURE_SINK_REFUSED", format!("{} refused", self.name));
            error.locus = "fixture".into();
            Err(error)
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
        panic!("Act VI must not emit SGT")
    }
}
impl UnsSink for Sink {
    fn record_narrative(&mut self, _session: &str, _text: &str) -> Result<String, Refusal> {
        panic!("Act VI must not emit UNS")
    }
}

fn verify_residual_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let wire = &row["input"];
    let dead = wire["dead_candidates"]
        .as_array()
        .unwrap()
        .iter()
        .map(CemeteryHeadstone::from_json)
        .collect::<Result<Vec<_>, _>>()?;
    let critiques: Vec<Challenge> = serde_json::from_value(wire["critiques"].clone())?;
    let verdicts: BTreeMap<String, String> =
        serde_json::from_value(wire["critique_verdicts"].clone())?;
    let measurement = ObstructionMeasurement::from_json(&wire["measurement"])?;
    let input = ResidualLedgerInput {
        dead_candidates: &dead,
        critiques: &critiques,
        critique_verdicts: &verdicts,
        measurement: &measurement,
        ablation_flags: wire["ablation_flags"].as_object(),
        run_key: wire["run_key"].as_str().unwrap(),
        now_utc: wire["now_utc"].as_str().unwrap(),
    };
    let calls = Rc::new(RefCell::new(Vec::new()));
    let mut history = History {
        calls: calls.clone(),
        failed: row["history_failure"].as_u64().unwrap() as usize,
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
    let mut suite = EmitterSuite {
        uts: Some(&mut uts),
        ddc: Some(&mut ddc),
        sgt: Some(SgtSink::Packet(&mut sgt)),
        uns: Some(&mut uns),
        antibodies: (row["history"] == true).then_some(&mut history as &mut dyn AntibodySink),
        ..EmitterSuite::default()
    };
    let result = execute_act6_residual_ledger(
        &input,
        (row["emit"] == true).then_some(&mut suite),
        &AuthorizationTime {
            event_clock: &FrozenClock,
            dda_timestamp: "2026-10-04 12:00:00 UTC",
        },
    );
    let actual = match result {
        Ok(value) => {
            assert_eq!(
                value.residual_ledger(),
                &row["expected"]["ok"]["residual_ledger"]
            );
            assert_eq!(
                json!(value.antibodies_recorded()),
                row["expected"]["ok"]["antibodies_recorded"]
            );
            assert_eq!(value.narrative(), &row["expected"]["ok"]["narrative"]);
            json!({"ok":value.to_dict()})
        }
        Err(error) => json!({"error":error}),
    };
    assert_eq!(actual, row["expected"], "residual vector {index}");
    assert_eq!(
        json!(*calls.borrow()),
        row["calls"],
        "residual trace {index}"
    );
    Ok(())
}

#[test]
fn frozen_python_residual_declaration_ordered_history_and_i_step_witness(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_residual_ledger_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors")?;
    assert_eq!(rows.len(), 34);
    for (index, row) in rows.iter().enumerate() {
        verify_residual_row(index, row)?;
    }
    Ok(())
}

// Origin: engine/crates_rs/tests/core_adversary/residual_parity.rs
// Claim: urn:core:crates_rs:tests:residual-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
