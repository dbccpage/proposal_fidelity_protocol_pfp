use num_bigint::BigUint;
use num_rational::BigRational;
use core_operads::{
    immune_guards::{
        allosteric_consensus_substitute, immune_guarded_substitute, validate_workflow_immune_guard,
        DangerScreenRequest,
    },
    immune_ports::{
        DetectorIdentity, DetectorMatch, ExactCount, HostDangerObservation, ImmuneScreenPort,
        ImmuneVerdict, SensorReading,
    },
    planar::OperadOperation,
    policy::DangerSignalPolicy,
    workflow::{WorkflowFinding, WorkflowReport},
    Refusal,
};
use serde_json::{json, Value};

struct Stub {
    response: Value,
    calls: Vec<Value>,
}
impl Stub {
    fn answer(&self) -> Result<ImmuneVerdict, Refusal> {
        if let Some(error) = self.response.get("error") {
            return Err(Refusal::new(
                error["code"].as_str().unwrap_or("TEST_INVALID"),
                error["detail"].as_str().unwrap_or("fixture detail missing"),
            ));
        }
        let verdict = ImmuneVerdict::from_json(&self.response["ok"])?;
        assert_eq!(
            verdict.decision(),
            self.response["ok"]["decision"].as_str().expect("decision")
        );
        Ok(verdict)
    }
}
impl ImmuneScreenPort for Stub {
    fn danger_verdict(
        &mut self,
        matches: &[DetectorMatch],
        danger: Option<&HostDangerObservation>,
        detector: &DetectorIdentity,
    ) -> Result<ImmuneVerdict, Refusal> {
        self.calls
            .push(json!({"port":"danger","matches":matches,"danger":danger,"detector":detector}));
        self.answer()
    }
    fn quorum_verdict(&mut self, readings: &[SensorReading]) -> Result<ImmuneVerdict, Refusal> {
        self.calls
            .push(json!({"port":"quorum","readings":readings}));
        self.answer()
    }
    fn trigger_tolerance_verdict(
        &mut self,
        _: &str,
        _: &[String],
    ) -> Result<ImmuneVerdict, Refusal> {
        Err(Refusal::new(
            "TEST_UNEXPECTED_PORT",
            "thymus must not be called",
        ))
    }
}

fn finding_from_json(row: &Value) -> Result<WorkflowFinding, Box<dyn std::error::Error>> {
    Ok(WorkflowFinding::new(
        row["workflow_id"].as_str().ok_or("workflow id")?.into(),
        row["code"].as_str().ok_or("code")?.into(),
        row["detail"].as_str().ok_or("detail")?.into(),
        row["step_index"].as_u64().map(usize::try_from).transpose()?,
        (!row["operation"].is_null()).then(|| row["operation"].clone()),
    ))
}

fn report(value: &Value) -> Result<WorkflowReport, Box<dyn std::error::Error>> {
    let findings = value["findings"]
        .as_array()
        .ok_or("findings required")?
        .iter()
        .map(finding_from_json)
        .collect::<Result<Vec<_>, _>>()?;
    let composed = if value["composed"].is_null() {
        None
    } else {
        Some(OperadOperation::from_json(&value["composed"])?)
    };
    Ok(WorkflowReport::new(
        value["workflow_id"].as_str().ok_or("workflow id")?.into(),
        OperadOperation::from_json(&value["declared"])?,
        composed,
        findings,
    ))
}

fn assert_guard_inputs_roundtrip(
    row: &Value,
    detector: &DetectorIdentity,
    matches: &[DetectorMatch],
    danger: &HostDangerObservation,
    readings: &[SensorReading],
) -> Result<(), Box<dyn std::error::Error>> {
    assert_eq!(json!(detector.detector_id()), row["detector"]["detector_id"]);
    assert_eq!(json!(detector.predicates()), row["detector"]["predicates"]);
    assert_eq!(json!(detector.offsets_are_content()), row["detector"]["offsets_are_content"]);
    for (value, wire) in matches.iter().zip(row["matches"].as_array().ok_or("matches")?) {
        assert_eq!(json!(value.epitope()), wire["epitope"]);
        assert_eq!(json!(value.matched_text()), wire["matched_text"]);
        assert_eq!(json!(ExactCount::new(value.offset().get().clone())), wire["offset"]);
    }
    assert_eq!(json!(danger.kind()), row["danger"]["kind"]);
    assert_eq!(json!(danger.severity()), row["danger"]["severity"]);
    assert_eq!(json!(danger.defect_count()), row["danger"]["defect_count"]);
    assert_eq!(json!(danger.evidence_digest()), row["danger"]["evidence_digest"]);
    assert_eq!(json!(danger.observer_id()), row["danger"]["observer_id"]);
    assert_eq!(json!(danger.evidence_spans()), row["danger"]["evidence_spans"]);
    for (reading, wire) in readings.iter().zip(row["readings"].as_array().ok_or("readings")?) {
        assert_eq!(json!(reading.sensor_id()), wire["sensor_id"]);
        assert_eq!(
            reading.value().numer().to_string(),
            wire["value"]["numerator"].as_str().ok_or("numerator")?
        );
    }
    Ok(())
}

fn dispatch_substitute_op(
    row: &Value,
    readings: &[SensorReading],
    evidence: DangerScreenRequest<'_>,
    immune: &mut Stub,
) -> Result<Value, Box<dyn std::error::Error>> {
    let theta = OperadOperation::from_json(&row["theta"])?;
    let phi = OperadOperation::from_json(&row["phi"])?;
    let result = if row["op"] == "danger_substitute" {
        immune_guarded_substitute(&theta, &row["index"], &phi, immune, evidence)
    } else {
        allosteric_consensus_substitute(&theta, &row["index"], &phi, readings, immune)
    };
    Ok(match result {
        Ok(value) => json!({"ok":value}),
        Err(error) => json!({"error":error}),
    })
}

fn dispatch_guard_op(
    index: usize,
    row: &Value,
    readings: &[SensorReading],
    evidence: DangerScreenRequest<'_>,
    immune: &mut Stub,
) -> Result<Value, Box<dyn std::error::Error>> {
    match row["op"].as_str().ok_or("op")? {
        "danger_substitute" | "quorum_substitute" => {
            dispatch_substitute_op(row, readings, evidence, immune)
        }
        "workflow_guard" => {
            let original = report(&row["report"])?;
            let value = validate_workflow_immune_guard(
                &original,
                &DangerSignalPolicy::from_json(&row["policy"])?,
                immune,
                evidence,
            )?;
            assert_eq!(json!(original), row["report"], "original report preserved {index}");
            Ok(json!({"ok":value}))
        }
        op => Err(format!("unknown op {op}").into()),
    }
}

fn check_guard_vector_row(index: usize, row: &Value) -> Result<(), Box<dyn std::error::Error>> {
    let detector = DetectorIdentity::from_json(&row["detector"])?;
    let matches = row["matches"]
        .as_array()
        .ok_or("matches")?
        .iter()
        .map(DetectorMatch::from_json)
        .collect::<Result<Vec<_>, _>>()?;
    let danger = HostDangerObservation::from_json(&row["danger"])?;
    let readings = row["readings"]
        .as_array()
        .ok_or("readings")?
        .iter()
        .map(SensorReading::from_json)
        .collect::<Result<Vec<_>, _>>()?;
    assert_guard_inputs_roundtrip(row, &detector, &matches, &danger, &readings)?;
    let evidence = DangerScreenRequest {
        detector: &detector,
        matches: &matches,
        danger: Some(&danger),
    };
    let mut immune = Stub {
        response: row["response"].clone(),
        calls: Vec::new(),
    };
    let actual = dispatch_guard_op(index, row, &readings, evidence, &mut immune)?;
    assert_eq!(actual, row["expected"], "guard vector {index}");
    assert_eq!(json!(immune.calls), row["calls"], "ordered trace {index}");
    Ok(())
}

#[test]
fn frozen_python_guard_outcomes_and_ordered_owned_port_calls(
) -> Result<(), Box<dyn std::error::Error>> {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_immune_guards_v1.json"))?;
    let rows = fixture["vectors"].as_array().ok_or("vectors required")?;
    assert_eq!(rows.len(), 216);
    for (index, row) in rows.iter().enumerate() {
        check_guard_vector_row(index, row)?;
    }
    Ok(())
}

#[test]
fn owned_port_admission_refuses_blank_fields_and_nonexact_numbers() {
    let count = ExactCount::new(BigUint::from(0_u8));
    assert!(DetectorMatch::new(" \u{1f}".into(), "match".into(), count.clone()).is_err());
    assert!(DetectorMatch::new("E".into(), "\t".into(), count.clone()).is_err());
    assert!(DetectorIdentity::new("".into(), Default::default(), false).is_err());
    assert!(SensorReading::new("".into(), BigRational::from_integer(1.into())).is_err());
    assert!(ImmuneVerdict::new(false, "".into(), "reason".into()).is_err());
    assert!(ImmuneVerdict::new(false, "ADMITTED".into(), "".into()).is_err());
    for (kind, severity, digest, observer) in [
        ("", "HIGH", "e", "o"),
        ("K", "SEVERE", "e", "o"),
        ("K", "HIGH", "", "o"),
        ("K", "HIGH", "e", ""),
    ] {
        assert!(HostDangerObservation::new(
            kind.into(),
            severity.into(),
            count.clone(),
            digest.into(),
            observer.into(),
            Vec::new()
        )
        .is_err());
    }
    for offset in [
        "-1",
        "1.0",
        "true",
        r#"{"$serde_json::private::Number":"1"}"#,
    ] {
        let raw = format!(r#"{{"epitope":"E","matched_text":"m","offset":{offset}}}"#);
        assert_eq!(
            DetectorMatch::from_bytes(raw.as_bytes())
                .expect_err("exact offset")
                .code,
            "IMMUNE_PORT_WIRE_INVALID"
        );
    }
    let duplicate = br#"{"epitope":"E","epitope":"X","matched_text":"m","offset":0}"#;
    assert!(DetectorMatch::from_bytes(duplicate).is_err());
    for value in [
        json!({"numerator":"1","denominator":"0"}),
        json!({"numerator":"bad","denominator":"2"}),
        json!({"numerator":"1","denominator":"bad"}),
        json!(true),
    ] {
        assert!(SensorReading::from_json(&json!({"sensor_id":"s","value":value})).is_err());
    }
}

// Origin: engine/crates_rs/tests/core_operads/immune_guards_parity.rs
// Claim: urn:core:crates_rs:tests:immune-guards-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
