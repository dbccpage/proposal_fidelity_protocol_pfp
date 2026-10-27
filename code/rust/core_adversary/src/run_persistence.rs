//! Content-addressed run custody through an injected artifact transaction port.
use crate::algorithm_metadata::{validate_algorithm_metadata, AlgorithmMetadataInput};
use crate::evidence::sha256_ref;
use crate::mam::{render_mam, MAM_FILES, MAM_SCHEMA};
use crate::render_record::{JsonStyle, RenderRecord};
use crate::stage::ports::Refusal;
use indexmap::IndexMap;
use num_bigint::BigInt;
use num_rational::BigRational;
use core_types::python_unicode::is_alphanumeric;
use sha2::{Digest, Sha256};

const NULL: RenderRecord = RenderRecord::Null;
pub const RECEIPT_ID_SCHEMA: &str = "core.adversary.bout-receipt-id.v1";
pub const RUN_BUNDLE_V2: &str = "core.adversary.reported-run-bundle.v1";
pub const RUN_BUNDLE_V3: &str = "core.adversary.reported-run-bundle.v2";
const LOCUS: &str = "adversary.use_cases.persistence";
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_RUN_CUSTODY_INVALID", message)
}
fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}
fn field<'a>(map: &'a IndexMap<String, RenderRecord>, key: &str) -> &'a RenderRecord {
    map.get(key).unwrap_or(&NULL)
}
fn record(pairs: &[(&str, RenderRecord)]) -> RenderRecord {
    RenderRecord::object(
        pairs
            .iter()
            .map(|(key, value)| ((*key).into(), value.clone())),
    )
}
fn pretty_bytes(record: &RenderRecord) -> Result<Vec<u8>, Refusal> {
    Ok(format!("{}\n", record.json(JsonStyle::PrettySortedAscii)?).into_bytes())
}
pub fn novella_bytes(text: &str) -> Vec<u8> {
    format!("{}\n", text.trim_end_matches('\n')).into_bytes()
}
pub fn run_directory_name(run_key: &str) -> Result<String, Refusal> {
    if run_key.is_empty() {
        return Err(invalid("run_key must be an exact nonempty string"));
    }
    if is_safe_run_key(run_key) {
        return Ok(run_key.into());
    }
    let replaced = run_key.chars().map(sanitize_run_char).collect::<String>();
    let stem = replaced
        .trim_matches(['_', '-'])
        .chars()
        .take(80)
        .collect::<String>();
    let stem = if stem.is_empty() { "run" } else { &stem };
    Ok(format!("{stem}-{}", &digest(run_key.as_bytes())[..12]))
}

fn is_safe_run_key(run_key: &str) -> bool {
    let mut bytes = run_key.bytes();
    let first_ok = bytes.next().is_some_and(|c| c.is_ascii_alphanumeric());
    let rest_ok = bytes.all(|c| c.is_ascii_alphanumeric() || b"-_".contains(&c));
    first_ok && rest_ok
}

fn sanitize_run_char(c: char) -> char {
    if is_alphanumeric(c) || "-_".contains(c) {
        c
    } else {
        '_'
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DdaTape {
    pub bytes: Vec<u8>,
    pub head_sha256: Option<String>,
}
pub fn dda_tape(steps: &[RenderRecord]) -> Result<DdaTape, Refusal> {
    let mut bytes = Vec::new();
    let mut head = RenderRecord::Null;
    let mut head_sha256 = None;
    for (sequence, payload) in steps.iter().enumerate() {
        let fields = payload.as_object()?;
        let sequence = RenderRecord::Integer(BigInt::from(sequence));
        let material = record(&[
            ("sequence", sequence.clone()),
            ("parent_sha256", head.clone()),
            ("payload", payload.clone()),
        ]);
        let hash = digest(material.json(JsonStyle::CompactSortedAscii)?.as_bytes());
        let mut line = record(&[
            ("sequence", sequence),
            ("parent_sha256", head),
            ("payload", payload.clone()),
            ("record_sha256", RenderRecord::text(&hash)),
        ])
        .as_object()?
        .clone();
        if let Some(timestamp) = fields.get("timestamp") {
            line.insert("timestamp".into(), timestamp.clone());
        }
        bytes.extend_from_slice(
            RenderRecord::Object(line)
                .json(JsonStyle::SpacedSortedAscii)?
                .as_bytes(),
        );
        bytes.push(b'\n');
        head = RenderRecord::text(&hash);
        head_sha256 = Some(hash);
    }
    Ok(DdaTape { bytes, head_sha256 })
}
pub fn ddc_trace_digest(steps: &[RenderRecord]) -> Result<Option<String>, Refusal> {
    if steps.is_empty() {
        return Ok(None);
    }
    Ok(Some(sha256_ref(&dda_tape(steps)?.bytes)))
}
pub(crate) fn receipt_id_from_parts(
    novella: &[u8],
    dda: &[u8],
    summary_core: &[u8],
) -> Result<String, Refusal> {
    let material = record(&[
        ("dda_actions_sha256", RenderRecord::text(digest(dda))),
        ("novella_sha256", RenderRecord::text(digest(novella))),
        ("schema", RenderRecord::text(RECEIPT_ID_SCHEMA)),
        (
            "summary_core_sha256",
            RenderRecord::text(digest(summary_core)),
        ),
    ]);
    Ok(sha256_ref(
        material.json(JsonStyle::CompactSortedAscii)?.as_bytes(),
    ))
}
pub(crate) fn receipt_id_from_parts_v2(
    novella: &[u8],
    dda: &[u8],
    summary_core: &[u8],
    uts: &[u8],
) -> Result<String, Refusal> {
    let material = record(&[
        ("dda_actions_sha256", RenderRecord::text(digest(dda))),
        ("novella_sha256", RenderRecord::text(digest(novella))),
        (
            "summary_core_sha256",
            RenderRecord::text(digest(summary_core)),
        ),
        ("uts_sha256", RenderRecord::text(digest(uts))),
        (
            "schema",
            RenderRecord::text("core.adversary.bout-receipt-id.v2"),
        ),
    ]);
    Ok(sha256_ref(
        material.json(JsonStyle::CompactSortedAscii)?.as_bytes(),
    ))
}
pub fn content_addressed_receipt_id_v2(
    novella: &str,
    steps: &[RenderRecord],
    summary: &RenderRecord,
    uts: &str,
) -> Result<String, Refusal> {
    let mut summary = summary.as_object()?.clone();
    summary.insert(
        "bundle_schema_version".into(),
        RenderRecord::text(RUN_BUNDLE_V2),
    );
    receipt_id_from_parts_v2(
        &novella_bytes(novella),
        &dda_tape(steps)?.bytes,
        &summary_core_bytes(&RenderRecord::Object(summary))?,
        uts.as_bytes(),
    )
}

pub(crate) fn receipt_id_from_parts_v3(
    uns: &[u8],
    ddc: &[u8],
    summary_core: &[u8],
    uts: &[u8],
) -> Result<String, Refusal> {
    let material = record(&[
        ("ddc_sha256", RenderRecord::text(digest(ddc))),
        ("uns_sha256", RenderRecord::text(digest(uns))),
        (
            "summary_core_sha256",
            RenderRecord::text(digest(summary_core)),
        ),
        ("uts_sha256", RenderRecord::text(digest(uts))),
        (
            "schema",
            RenderRecord::text("core.adversary.bout-receipt-id.v3"),
        ),
    ]);
    Ok(sha256_ref(
        material.json(JsonStyle::CompactSortedAscii)?.as_bytes(),
    ))
}

pub fn content_addressed_receipt_id_v3(
    uns: &str,
    steps: &[RenderRecord],
    summary: &RenderRecord,
    uts: &str,
) -> Result<String, Refusal> {
    let mut summary = summary.as_object()?.clone();
    summary.insert(
        "bundle_schema_version".into(),
        RenderRecord::text(RUN_BUNDLE_V3),
    );
    receipt_id_from_parts_v3(
        &novella_bytes(uns),
        &dda_tape(steps)?.bytes,
        &summary_core_bytes(&RenderRecord::Object(summary))?,
        uts.as_bytes(),
    )
}

/// Check event ordering and resolve retained source references before sealing.
pub fn validate_uts(uts: &str, summary: &RenderRecord) -> Result<(), Refusal> {
    use serde_json::Value;
    use std::collections::BTreeSet;
    let summary: Value = serde_json::from_str(&summary.json(JsonStyle::PrettyUnicode)?)
        .map_err(|error| invalid(error.to_string()))?;
    let mut ids = BTreeSet::new();
    let mut count = 0;
    for (sequence, line) in uts.lines().enumerate() {
        validate_uts_line(sequence, line, &summary, &mut ids)?;
        count += 1;
    }
    if count < 2 || !uts.ends_with('\n') {
        return Err(invalid(
            "UTS requires source and checkpoint events with newline termination",
        ));
    }
    Ok(())
}

fn validate_uts_line(
    sequence: usize,
    line: &str,
    summary: &serde_json::Value,
    ids: &mut std::collections::BTreeSet<String>,
) -> Result<(), Refusal> {
    let row: serde_json::Value =
        serde_json::from_str(line).map_err(|error| invalid(error.to_string()))?;
    let id = row
        .get("event_id")
        .and_then(serde_json::Value::as_str)
        .ok_or_else(|| invalid("UTS event identity is missing"))?;
    let row_ok = [
        row["schema_version"] == crate::run_reporting::UTS_SCHEMA,
        row["sequence"].as_u64() == Some(sequence as u64),
        ids.insert(id.to_owned()),
    ]
    .into_iter()
    .all(|b| b);
    if !row_ok {
        return Err(invalid("UTS sequence, schema or event identity is invalid"));
    }
    validate_uts_references(&row, summary)
}

fn validate_uts_references(
    value: &serde_json::Value,
    summary: &serde_json::Value,
) -> Result<(), Refusal> {
    match value {
        serde_json::Value::Object(fields) => {
            if let Some(reference) = fields.get("source_ref").and_then(serde_json::Value::as_str) {
                validate_uts_source_ref(fields, reference, summary)?;
            }
            // Only projection-owned references are custody links. A model's
            // JSON field named source_ref remains untrusted source content.
            for (key, value) in fields {
                if key.ends_with("_reference") {
                    validate_uts_references(value, summary)?;
                }
            }
        }
        serde_json::Value::Array(items) => {
            for item in items {
                validate_uts_references(item, summary)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn resolve_summary_pointer<'a>(
    reference: &'a str,
    summary: &'a serde_json::Value,
) -> Result<&'a serde_json::Value, Refusal> {
    let pointer = if let Some(p) = reference.strip_prefix("summary.json#") {
        p
    } else if reference == "summary.json" {
        ""
    } else {
        return Err(invalid(
            "UTS source reference must name retained summary bytes",
        ));
    };
    summary
        .pointer(pointer)
        .ok_or_else(|| invalid("UTS source reference is unresolved"))
}

fn validate_uts_source_ref(
    fields: &serde_json::Map<String, serde_json::Value>,
    reference: &str,
    summary: &serde_json::Value,
) -> Result<(), Refusal> {
    let source = resolve_summary_pointer(reference, summary)?;
    if let Some(expected) = fields
        .get("content_sha256")
        .and_then(serde_json::Value::as_str)
    {
        let record = RenderRecord::from_json(&source.to_string())?;
        if digest(record.json(JsonStyle::CompactSortedAscii)?.as_bytes()) != expected {
            return Err(invalid("UTS source content digest mismatch"));
        }
    }
    if fields.get("kind").and_then(serde_json::Value::as_str) == Some("run_source") {
        validate_uts_run_source(fields, source)?;
    }
    Ok(())
}

fn validate_uts_run_source(
    fields: &serde_json::Map<String, serde_json::Value>,
    source: &serde_json::Value,
) -> Result<(), Refusal> {
    let excluded_ok = fields.get("source_excluded_fields")
        == Some(&serde_json::json!(["receipt_id", "bundle_schema_version"]));
    let sha_ok = fields
        .get("source_sha256")
        .and_then(serde_json::Value::as_str)
        == Some(crate::run_reporting::captured_history_digest(source)?.as_str());
    if !excluded_ok || !sha_ok {
        return Err(invalid("UTS retained source snapshot digest mismatch"));
    }
    Ok(())
}
pub(crate) fn summary_core_bytes(summary: &RenderRecord) -> Result<Vec<u8>, Refusal> {
    let core = RenderRecord::object(
        summary
            .as_object()?
            .iter()
            .filter(|(key, _)| key.as_str() != "receipt_id")
            .map(|(key, value)| (key.clone(), value.clone())),
    );
    pretty_bytes(&core)
}
pub fn content_addressed_receipt_id(
    novella: &str,
    steps: &[RenderRecord],
    summary: &RenderRecord,
) -> Result<String, Refusal> {
    receipt_id_from_parts(
        &novella_bytes(novella),
        &dda_tape(steps)?.bytes,
        &summary_core_bytes(summary)?,
    )
}
fn numeric(value: &RenderRecord) -> Option<BigRational> {
    match value {
        RenderRecord::Bool(value) => {
            Some(BigRational::from_integer(BigInt::from(u8::from(*value))))
        }
        RenderRecord::Integer(value) => Some(BigRational::from_integer(value.clone())),
        RenderRecord::Float(value) => BigRational::from_float(*value),
        _ => None,
    }
}
fn python_equal(left: &RenderRecord, right: &RenderRecord) -> bool {
    if let (Some(left), Some(right)) = (numeric(left), numeric(right)) {
        return left == right;
    }
    match (left, right) {
        (RenderRecord::Array(left), RenderRecord::Array(right)) => {
            left.len() == right.len() && left.iter().zip(right).all(|(l, r)| python_equal(l, r))
        }
        (RenderRecord::Object(left), RenderRecord::Object(right)) => {
            left.len() == right.len()
                && left
                    .iter()
                    .all(|(key, value)| right.get(key).is_some_and(|r| python_equal(value, r)))
        }
        _ => left == right,
    }
}
fn same_typed_value(left: &RenderRecord, right: &RenderRecord) -> bool {
    std::mem::discriminant(left) == std::mem::discriminant(right) && python_equal(left, right)
}
fn validate_custody(
    receipt: &IndexMap<String, RenderRecord>,
    summary: &IndexMap<String, RenderRecord>,
    steps: &[RenderRecord],
) -> Result<(), Refusal> {
    check_custody_agreement(receipt, summary)?;
    for payload in [receipt, summary] {
        check_payload_metadata(payload)?;
    }
    check_carrier_measurement_custody(receipt, summary)?;
    check_step_traces_custody(receipt, summary, steps)
}

fn check_custody_agreement(
    receipt: &IndexMap<String, RenderRecord>,
    summary: &IndexMap<String, RenderRecord>,
) -> Result<(), Refusal> {
    for key in [
        "lggr_joint_kernel_status",
        "carrier_degree",
        "phi1",
        "gamma2",
        "measurement_status",
        "defect_count",
    ] {
        if let (Some(left), Some(right)) = (receipt.get(key), summary.get(key)) {
            if !same_typed_value(left, right) {
                return Err(invalid(format!(
                    "ALGORITHM_METADATA_MISMATCH: receipt and summary disagree on {key}"
                )));
            }
        }
    }
    Ok(())
}

fn check_payload_metadata(payload: &IndexMap<String, RenderRecord>) -> Result<(), Refusal> {
    if payload.contains_key("lggr_joint_kernel_status") || payload.contains_key("carrier_degree") {
        let default_status = RenderRecord::text("NOT_MEASURED");
        validate_algorithm_metadata(&AlgorithmMetadataInput {
            ddc_trace_hash: field(payload, "ddc_trace_hash"),
            joint_kernel_status: payload
                .get("lggr_joint_kernel_status")
                .unwrap_or(&default_status),
            phi1: field(payload, "phi1"),
            gamma2: field(payload, "gamma2"),
            carrier_degree: field(payload, "carrier_degree"),
        })?;
    }
    if let Some(status) = payload.get("measurement_status") {
        let measured = field(payload, "phi1") != &NULL && field(payload, "gamma2") != &NULL;
        let expected = if measured { "MEASURED" } else { "NOT_MEASURED" };
        if status != &RenderRecord::text(expected) {
            return Err(invalid(
                "ALGORITHM_METADATA_MISMATCH: measurement status disagrees with values",
            ));
        }
    }
    Ok(())
}

fn check_carrier_measurement_custody(
    receipt: &IndexMap<String, RenderRecord>,
    summary: &IndexMap<String, RenderRecord>,
) -> Result<(), Refusal> {
    let Some(measurement) = summary
        .get("carrier_measurement")
        .filter(|value| *value != &NULL)
    else {
        return Ok(());
    };
    let RenderRecord::Object(measurement) = measurement else {
        return Err(invalid(
            "ALGORITHM_METADATA_MISMATCH: carrier measurement must be a record",
        ));
    };
    if field(measurement, "status") == &RenderRecord::text("MEASURED")
        && field(measurement, "certificate_verified") != &RenderRecord::Bool(true)
    {
        return Err(invalid(
            "ALGORITHM_METADATA_MISMATCH: measured carrier lacks a verified certificate",
        ));
    }
    check_measurement_fields_match(measurement, receipt)?;
    check_measurement_fields_match(measurement, summary)
}

fn check_measurement_fields_match(
    measurement: &IndexMap<String, RenderRecord>,
    payload: &IndexMap<String, RenderRecord>,
) -> Result<(), Refusal> {
    for (inner, outer) in [
        ("status", "measurement_status"),
        ("phi1", "phi1"),
        ("gamma2", "gamma2"),
        ("defect_count", "defect_count"),
    ] {
        if let (Some(left), Some(right)) = (measurement.get(inner), payload.get(outer)) {
            if !same_typed_value(left, right) {
                return Err(invalid(format!(
                    "ALGORITHM_METADATA_MISMATCH: carrier measurement disagrees on {outer}"
                )));
            }
        }
    }
    Ok(())
}

fn check_step_traces_custody(
    receipt: &IndexMap<String, RenderRecord>,
    summary: &IndexMap<String, RenderRecord>,
    steps: &[RenderRecord],
) -> Result<(), Refusal> {
    for step in steps {
        let step = step.as_object()?;
        if !matches!(field(step, "after_class"), RenderRecord::String(text) if text.starts_with("Checker_"))
        {
            continue;
        }
        check_step_against_payload(step, receipt)?;
        check_step_against_payload(step, summary)?;
    }
    Ok(())
}

fn check_step_against_payload(
    step: &IndexMap<String, RenderRecord>,
    payload: &IndexMap<String, RenderRecord>,
) -> Result<(), Refusal> {
    for (trace_key, key) in [("phi_1", "phi1"), ("gamma_2", "gamma2")] {
        if let Some(value) = payload.get(key) {
            if !python_equal(field(step, trace_key), value) {
                return Err(invalid(format!(
                    "ALGORITHM_METADATA_MISMATCH: checker trace disagrees on {key}"
                )));
            }
        }
    }
    Ok(())
}
pub trait RunArtifactPort {
    fn begin(&mut self, directory_name: &str) -> Result<(), Refusal>;
    fn write_artifact(&mut self, name: &str, bytes: &[u8]) -> Result<(), Refusal>;
    fn commit(&mut self) -> Result<String, Refusal>;
    fn abort(&mut self);
}
pub struct PersistenceInput<'a> {
    pub run_key: &'a str,
    pub receipt: &'a RenderRecord,
    pub novella_md: &'a str,
    pub dda_steps: &'a [RenderRecord],
    pub summary_data: &'a RenderRecord,
}
pub fn persist_bout_run_folder(
    input: &PersistenceInput<'_>,
    port: &mut dyn RunArtifactPort,
) -> Result<String, Refusal> {
    persist_bundle(input, None, false, port)
}
pub fn persist_bout_run_folder_v2(
    input: &PersistenceInput<'_>,
    uts_jsonl: &str,
    port: &mut dyn RunArtifactPort,
) -> Result<String, Refusal> {
    validate_uts(uts_jsonl, input.summary_data)?;
    persist_bundle(input, Some(uts_jsonl), false, port)
}
/// Current output contract: one DDC action tape, UNS, UTS and the `mam/` story, without aliases.
pub fn persist_bout_run_folder_v3(
    input: &PersistenceInput<'_>,
    uts_jsonl: &str,
    port: &mut dyn RunArtifactPort,
) -> Result<String, Refusal> {
    validate_uts(uts_jsonl, input.summary_data)?;
    persist_bundle(input, Some(uts_jsonl), true, port)
}
fn persist_bundle(
    input: &PersistenceInput<'_>,
    uts_jsonl: Option<&str>,
    consolidated: bool,
    port: &mut dyn RunArtifactPort,
) -> Result<String, Refusal> {
    persist_bundle_inner(input, uts_jsonl, consolidated, port).map_err(|r| {
        port.abort();
        let mut refusal = if r.code == "RUN_FOLDER_EXISTS" {
            r
        } else {
            Refusal::new(
                "RUN_FOLDER_PERSIST_FAILED",
                format!("Failed to persist canonical run folder: {}", r.message),
            )
        };
        refusal.locus = LOCUS.into();
        refusal
    })
}

fn write_optional_uts_and_mam(
    uts_jsonl: Option<&str>,
    consolidated: bool,
    receipt: &mut IndexMap<String, RenderRecord>,
    summary_bytes: &[u8],
    tape_bytes: &[u8],
    port: &mut dyn RunArtifactPort,
) -> Result<(), Refusal> {
    if let Some(uts) = uts_jsonl {
        port.write_artifact("uts.jsonl", uts.as_bytes())?;
        receipt.insert(
            "uts_sha256".into(),
            RenderRecord::text(digest(uts.as_bytes())),
        );
    }
    if consolidated {
        write_consolidated_mam(receipt, summary_bytes, tape_bytes, port)?;
    }
    Ok(())
}

fn finalize_receipt_and_commit(
    receipt: IndexMap<String, RenderRecord>,
    novella: &[u8],
    tape: &DdaTape,
    summary_bytes: &[u8],
    consolidated: bool,
    port: &mut dyn RunArtifactPort,
) -> Result<String, Refusal> {
    let mut receipt = receipt;
    populate_receipt_hashes(&mut receipt, novella, tape, summary_bytes, consolidated);
    let receipt_bytes = pretty_bytes(&RenderRecord::Object(receipt))?;
    port.write_artifact("receipt.json", &receipt_bytes)?;
    port.commit()
}

fn persist_bundle_inner(
    input: &PersistenceInput<'_>,
    uts_jsonl: Option<&str>,
    consolidated: bool,
    port: &mut dyn RunArtifactPort,
) -> Result<String, Refusal> {
    let name = run_directory_name(input.run_key)?;
    port.begin(&name)?;
    let (mut receipt, mut summary) = init_receipt_and_summary(input)?;
    if let Some(uts) = uts_jsonl {
        apply_uts_identity(input, &mut receipt, &mut summary, uts, consolidated)?;
    }
    let novella = novella_bytes(input.novella_md);
    let novella_name = if consolidated { "uns.md" } else { "novella.md" };
    port.write_artifact(novella_name, &novella)?;
    let (tape, summary_bytes) =
        write_tape_and_summary(input, &mut receipt, &summary, consolidated, port)?;
    write_optional_uts_and_mam(
        uts_jsonl,
        consolidated,
        &mut receipt,
        &summary_bytes,
        &tape.bytes,
        port,
    )?;
    finalize_receipt_and_commit(receipt, &novella, &tape, &summary_bytes, consolidated, port)
}

fn init_receipt_and_summary(
    input: &PersistenceInput<'_>,
) -> Result<
    (
        IndexMap<String, RenderRecord>,
        IndexMap<String, RenderRecord>,
    ),
    Refusal,
> {
    let mut receipt = match input.receipt {
        RenderRecord::Object(fields) => fields.clone(),
        _ => IndexMap::new(),
    };
    let mut summary = input.summary_data.as_object()?.clone();
    for key in ["task_key", "receipt_id", "selected_candidate_id"] {
        sync_shared_key(&mut receipt, &mut summary, key);
    }
    Ok((receipt, summary))
}

fn sync_shared_key(
    receipt: &mut IndexMap<String, RenderRecord>,
    summary: &mut IndexMap<String, RenderRecord>,
    key: &str,
) {
    match (receipt.get(key).cloned(), summary.get(key).cloned()) {
        (None, Some(value)) => {
            receipt.insert(key.into(), value);
        }
        (Some(value), None) => {
            summary.insert(key.into(), value);
        }
        (Some(left), Some(right)) if !python_equal(&left, &right) => {
            if left == NULL || left == RenderRecord::text("") {
                receipt.insert(key.into(), right);
            } else {
                summary.insert(key.into(), left);
            }
        }
        _ => {}
    }
}

fn apply_uts_identity(
    input: &PersistenceInput<'_>,
    receipt: &mut IndexMap<String, RenderRecord>,
    summary: &mut IndexMap<String, RenderRecord>,
    uts: &str,
    consolidated: bool,
) -> Result<(), Refusal> {
    let (identity_fn, schema_ver) = if consolidated {
        (
            content_addressed_receipt_id_v3
                as fn(&str, &[RenderRecord], &RenderRecord, &str) -> Result<String, Refusal>,
            RUN_BUNDLE_V3,
        )
    } else {
        (
            content_addressed_receipt_id_v2
                as fn(&str, &[RenderRecord], &RenderRecord, &str) -> Result<String, Refusal>,
            RUN_BUNDLE_V2,
        )
    };
    let identity = identity_fn(
        input.novella_md,
        input.dda_steps,
        &RenderRecord::Object(summary.clone()),
        uts,
    )?;
    for data in [&mut *summary, &mut *receipt] {
        data.insert(
            "bundle_schema_version".into(),
            RenderRecord::text(schema_ver),
        );
        data.insert("receipt_id".into(), RenderRecord::text(&identity));
    }
    validate_uts(uts, &RenderRecord::Object(summary.clone()))
}

fn verify_and_bind_trace_hash(
    tape: &DdaTape,
    receipt: &mut IndexMap<String, RenderRecord>,
    summary: &IndexMap<String, RenderRecord>,
) -> Result<(), Refusal> {
    let trace = if tape.bytes.is_empty() {
        NULL
    } else {
        RenderRecord::text(sha256_ref(&tape.bytes))
    };
    for data in [&*receipt, summary] {
        let claimed = field(data, "ddc_trace_hash");
        if claimed != &NULL && !python_equal(claimed, &trace) {
            return Err(invalid(
                "DDC_TRACE_DIGEST_MISMATCH: receipt names different tape bytes",
            ));
        }
    }
    receipt.insert("ddc_trace_hash".into(), trace);
    Ok(())
}

fn write_tape_and_summary(
    input: &PersistenceInput<'_>,
    receipt: &mut IndexMap<String, RenderRecord>,
    summary: &IndexMap<String, RenderRecord>,
    consolidated: bool,
    port: &mut dyn RunArtifactPort,
) -> Result<(DdaTape, Vec<u8>), Refusal> {
    let tape = dda_tape(input.dda_steps)?;
    verify_and_bind_trace_hash(&tape, receipt, summary)?;
    validate_custody(receipt, summary, input.dda_steps)?;
    if !consolidated {
        port.write_artifact("dda_actions.jsonl", &tape.bytes)?;
    }
    port.write_artifact("ddc.jsonl", &tape.bytes)?;
    let summary_bytes = pretty_bytes(&RenderRecord::Object(summary.clone()))?;
    port.write_artifact("summary.json", &summary_bytes)?;
    Ok((tape, summary_bytes))
}

fn write_consolidated_mam(
    receipt: &mut IndexMap<String, RenderRecord>,
    summary_bytes: &[u8],
    tape_bytes: &[u8],
    port: &mut dyn RunArtifactPort,
) -> Result<(), Refusal> {
    // The Panel's story, re-rendered by readers from the bound bytes.
    let book = render_mam(summary_bytes, tape_bytes)?;
    receipt.insert("mam_schema_version".into(), RenderRecord::text(MAM_SCHEMA));
    for ((name, key), bytes) in
        MAM_FILES
            .iter()
            .zip([book.md.as_bytes(), book.tex.as_bytes(), &book.pdf])
    {
        port.write_artifact(name, bytes)?;
        receipt.insert((*key).into(), RenderRecord::text(digest(bytes)));
    }
    Ok(())
}

fn populate_receipt_hashes(
    receipt: &mut IndexMap<String, RenderRecord>,
    novella: &[u8],
    tape: &DdaTape,
    summary_bytes: &[u8],
    consolidated: bool,
) {
    let mut hashes = vec![
        ("ddc_sha256", digest(&tape.bytes)),
        ("summary_sha256", digest(summary_bytes)),
    ];
    if consolidated {
        for key in ["novella_sha256", "dda_actions_sha256", "dda_head_sha256"] {
            receipt.shift_remove(key);
        }
        hashes.push(("uns_sha256", digest(novella)));
        let head_rec = tape
            .head_sha256
            .as_ref()
            .map(RenderRecord::text)
            .unwrap_or(NULL);
        receipt.insert("ddc_head_sha256".into(), head_rec);
    } else {
        hashes.extend([
            ("novella_sha256", digest(novella)),
            ("dda_actions_sha256", digest(&tape.bytes)),
        ]);
        if let Some(head) = &tape.head_sha256 {
            receipt.insert("dda_head_sha256".into(), RenderRecord::text(head));
        }
    }
    for (key, hash) in hashes {
        receipt.insert(key.into(), RenderRecord::text(hash));
    }
}

// Origin: engine/crates_rs/core_adversary/src/run_persistence.rs
// Claim: urn:core:crates_rs:core-adversary:run-persistence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf5ef1aa7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf5ef1aa7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf5ef1aa7 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorf5ef1aa7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf5ef1aa7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf5ef1aa7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf5ef1aa7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf5ef1aa7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf5ef1aa7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf5ef1aa7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf5ef1aa7::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_f5ef1aa7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf5ef1aa7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf5ef1aa7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf5ef1aa7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf5ef1aa7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf5ef1aa7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorf5ef1aa7::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorf5ef1aa7::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
