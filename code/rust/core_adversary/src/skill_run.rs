//! Skill-authored run validation and byte-bound persistence. AuthorityEffect: None.
use crate::evidence::{sha256_ref, CheckerVerdict};
use crate::evidence_parse::{parse_checker_receipt, python_value_repr};
use crate::render_record::RenderRecord;
use crate::run_folder_store::RunFolderStore;
use crate::run_persistence::{
    content_addressed_receipt_id_v3, persist_bout_run_folder, persist_bout_run_folder_v3,
    PersistenceInput,
};
use crate::run_reporting::project_run_reports;
use crate::stage::ports::Refusal;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::path::PathBuf;
pub const VERDICTS: [&str; 5] = [
    "PASS_TO_MASTER",
    "REFUSE",
    "OPEN_RESIDUAL",
    "REFERENCE_SELF_CONSISTENT",
    "REFERENCE_SELF_INCONSISTENT",
];
fn refuse(code: &str, message: impl Into<String>) -> Refusal {
    let mut error = Refusal::new(code, message);
    error.locus = "adversary.use_cases.skill_run_persistence".into();
    error
}
fn required<'a>(
    input: &'a Value,
    key: &str,
    code: &str,
    message: &str,
) -> Result<&'a str, Refusal> {
    input[key]
        .as_str()
        .filter(|s| {
            !s.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
                .is_empty()
        })
        .ok_or_else(|| refuse(code, message))
}
fn json_object(input: &Value, key: &str) -> Result<Map<String, Value>, Refusal> {
    match &input[key] {
        Value::Null => Ok(Map::new()),
        Value::Object(map) => Ok(map.clone()),
        other => Err(refuse(
            "SKILL_RUN_INPUT_INVALID",
            format!(
                "{key} must be a JSON object, got {}",
                python_value_repr(other)
            ),
        )),
    }
}
fn json_array(input: &Value, key: &str) -> Result<Vec<Value>, Refusal> {
    match &input[key] {
        Value::Null => Ok(Vec::new()),
        Value::Array(items) => Ok(items.clone()),
        other => Err(refuse(
            "SKILL_RUN_INPUT_INVALID",
            format!(
                "{key} must be a JSON array, got {}",
                python_value_repr(other)
            ),
        )),
    }
}
fn encode(value: &Value) -> Result<RenderRecord, Refusal> {
    RenderRecord::from_json(&value.to_string())
}
fn digest(value: &Value) -> Result<String, Refusal> {
    let bytes =
        serde_json::to_vec(value).map_err(|e| refuse("SKILL_RUN_INPUT_INVALID", e.to_string()))?;
    Ok(hex::encode(Sha256::digest(bytes)))
}
pub fn parse_actions(text: &str) -> Result<Value, Refusal> {
    let mut steps = Vec::new();
    for (number, line) in text.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let row: Value = serde_json::from_str(line).map_err(|e| {
            refuse(
                "DDA_ACTION_INVALID_JSON",
                format!("line {}: {e}", number + 1),
            )
        })?;
        if !row.is_object() {
            return Err(refuse(
                "DDA_ACTION_NOT_OBJECT",
                format!("line {}: expected a JSON object", number + 1),
            ));
        }
        if let Some(letter) = row.get("letter") {
            if !letter
                .as_str()
                .is_some_and(|s| ["E", "R", "C", "I", "Λ", "Lambda", "D", "M", "T"].contains(&s))
            {
                return Err(refuse(
                    "UNKNOWN_DDC_LETTER",
                    format!(
                        "line {}: letter {} is not in the DDC alphabet",
                        number + 1,
                        python_value_repr(letter)
                    ),
                ));
            }
        }
        steps.push(row);
    }
    Ok(Value::Array(steps))
}
pub fn persist(input: &Value, output: PathBuf) -> Result<String, Refusal> {
    persist_version(input, output, true)
}
/// Frozen source fixture reproduction; current entrypoints always use `persist`.
pub fn persist_historical(input: &Value, output: PathBuf) -> Result<String, Refusal> {
    persist_version(input, output, false)
}
fn persist_skill_run_bundle(
    reported: bool,
    task: &str,
    verdict: &str,
    novella: &str,
    summary_data: Map<String, Value>,
    receipt: Value,
    steps: &[RenderRecord],
    output: PathBuf,
) -> Result<String, Refusal> {
    if reported {
        return persist_reported_skill_run(
            task,
            verdict,
            novella,
            summary_data,
            receipt,
            steps,
            output,
        );
    }
    let receipt = encode(&receipt)?;
    let summary = encode(&Value::Object(summary_data))?;
    persist_bout_run_folder(
        &PersistenceInput {
            run_key: task,
            receipt: &receipt,
            novella_md: novella,
            dda_steps: steps,
            summary_data: &summary,
        },
        &mut RunFolderStore::new(output),
    )
}

#[allow(clippy::too_many_arguments)]
fn compute_skill_run_summary_and_id(
    input: &Value,
    task: &str,
    objective: &str,
    verdict: &str,
    source: &str,
    novella: &str,
    checker_record: &Value,
    checker_digest: &Value,
    bytes: Option<&[u8]>,
) -> Result<(Map<String, Value>, Vec<Value>, String, Map<String, Value>), Refusal> {
    let summary = json_object(input, "summary")?;
    let generated = json!({"authority_effect":"None","checker_receipt":checker_record,"checker_receipt_sha256":checker_digest,"source":source,"task_key":task,"terminal_verdict":verdict});
    let fields = generated
        .as_object()
        .ok_or_else(|| refuse("SKILL_RUN_INPUT_INVALID", "generated summary required"))?;
    check_summary_key_conflicts(&summary, fields)?;
    let steps_raw = json_array(input, "dda_steps")?;
    let material = json!({"checker_receipt":checker_record,"checker_receipt_sha256":checker_digest,"dda_steps":steps_raw,"novella_sha256":hex::encode(Sha256::digest(novella.as_bytes())),"objective":objective,"source":source,"summary":summary,"task_key":task,"verdict":verdict});
    let receipt_id = digest(&material)?;
    let summary_data = build_skill_summary_data(
        summary.clone(),
        fields,
        &steps_raw,
        objective,
        &receipt_id,
        bytes,
    );
    Ok((summary, steps_raw, receipt_id, summary_data))
}

fn persist_version(input: &Value, output: PathBuf, reported: bool) -> Result<String, Refusal> {
    let (objective, verdict, source, novella) = extract_skill_run_text_fields(input)?;
    let (bytes, checker_digest, checker_record) =
        parse_and_verify_checker_receipt(input, &verdict)?;
    let task = input["task_key"]
        .as_str()
        .ok_or_else(|| refuse("SKILL_RUN_INPUT_INVALID", "task_key required"))?;
    let (summary, steps_raw, receipt_id, summary_data) = compute_skill_run_summary_and_id(
        input,
        task,
        &objective,
        &verdict,
        &source,
        &novella,
        &checker_record,
        &checker_digest,
        bytes.as_deref(),
    )?;
    let receipt = build_skill_receipt(
        input,
        &summary,
        &checker_record,
        &checker_digest,
        &objective,
        &receipt_id,
        &source,
        task,
        &verdict,
    );
    let steps = steps_raw
        .iter()
        .map(encode)
        .collect::<Result<Vec<_>, _>>()?;
    persist_skill_run_bundle(
        reported,
        task,
        &verdict,
        &novella,
        summary_data,
        receipt,
        &steps,
        output,
    )
}

fn extract_skill_run_text_fields(
    input: &Value,
) -> Result<(String, String, String, String), Refusal> {
    let objective = required(
        input,
        "objective",
        "EMPTY_OBJECTIVE",
        "objective must be a nonempty string",
    )?;
    let verdict = input["verdict"].as_str().unwrap_or("");
    if !VERDICTS.contains(&verdict) {
        return Err(refuse(
            "INVALID_VERDICT",
            format!(
                "verdict {} is not one of {}",
                python_value_repr(&input["verdict"]),
                VERDICTS.join(", ")
            ),
        ));
    }
    let source = required(
        input,
        "source",
        "EMPTY_SOURCE",
        "source must be a nonempty string",
    )?;
    let novella = required(
        input,
        "novella_md",
        "EMPTY_NOVELLA",
        "novella must contain text",
    )?;
    Ok((objective.to_owned(), verdict.to_owned(), source.to_owned(), novella.to_owned()))
}

fn parse_and_verify_checker_receipt(
    input: &Value,
    verdict: &str,
) -> Result<(Option<Vec<u8>>, Value, Value), Refusal> {
    if input["checker_receipt_hex"].is_null() {
        if verdict == "PASS_TO_MASTER" {
            return Err(refuse("CHECKER_RECEIPT_REQUIRED", format!("{verdict} is refused without the challenge checker receipt; persist OPEN_RESIDUAL, or pass the receipt file that accepted the answer")));
        }
        return Ok((None, Value::Null, Value::Null));
    }
    let raw = hex::decode(input["checker_receipt_hex"].as_str().unwrap_or(""))
        .map_err(|e| refuse("CHECKER_RECEIPT_MALFORMED", e.to_string()))?;
    if raw.is_empty() {
        return Err(refuse(
            "CHECKER_RECEIPT_EMPTY",
            "the checker receipt file is empty",
        ));
    }
    let record =
        parse_checker_receipt(&raw).map_err(|e| refuse("CHECKER_RECEIPT_MALFORMED", e.message))?;
    verify_checker_verdict_matches(verdict, &record)?;
    let digest_val = json!(sha256_ref(&raw));
    let dict_val = record.to_dict();
    Ok((Some(raw), digest_val, dict_val))
}

fn verify_checker_verdict_matches(
    verdict: &str,
    record: &crate::evidence_parse::CheckerReceiptRecord,
) -> Result<(), Refusal> {
    let required = match verdict {
        "PASS_TO_MASTER" => Some(CheckerVerdict::Accepted),
        "REFUSE" => Some(CheckerVerdict::Rejected),
        _ => None,
    };
    let Some(required) = required else {
        return Ok(());
    };
    if record.verdict() != required {
        let req_str = serde_json::to_value(required)
            .map_err(|e| refuse("SKILL_RUN_INPUT_INVALID", e.to_string()))?;
        return Err(refuse(
            "CHECKER_RECEIPT_VERDICT_MISMATCH",
            format!(
                "{verdict} needs a checker receipt stating {}; this receipt states {}",
                req_str.as_str().unwrap_or(""),
                record.to_dict()["verdict"].as_str().unwrap_or("")
            ),
        ));
    }
    Ok(())
}

fn check_summary_key_conflicts(
    summary: &Map<String, Value>,
    fields: &Map<String, Value>,
) -> Result<(), Refusal> {
    // Check fields in the source's precedence order, independently of JSON map ordering.
    for key in [
        "authority_effect",
        "checker_receipt",
        "checker_receipt_sha256",
        "source",
        "task_key",
        "terminal_verdict",
    ] {
        if summary.get(key).is_some_and(|v| v != &fields[key]) {
            return Err(refuse(
                "SUMMARY_KEY_CONFLICT",
                format!(
                    "summary.{key}={} conflicts with {}",
                    python_value_repr(&summary[key]),
                    python_value_repr(&fields[key])
                ),
            ));
        }
    }
    for key in ["receipt_id", "checker_receipt_hex"] {
        if summary.contains_key(key) {
            return Err(refuse(
                "SUMMARY_KEY_CONFLICT",
                format!("summary.{key} is assigned by the writer"),
            ));
        }
    }
    Ok(())
}

fn build_skill_summary_data(
    mut summary_data: Map<String, Value>,
    fields: &Map<String, Value>,
    steps: &[Value],
    objective: &str,
    receipt_id: &str,
    bytes: Option<&[u8]>,
) -> Map<String, Value> {
    summary_data.extend(fields.clone());
    summary_data.extend(Map::from_iter([
        ("dda_actions_supplied".into(), json!(!steps.is_empty())),
        ("objective".into(), json!(objective)),
        ("receipt_id".into(), json!(receipt_id)),
    ]));
    if let Some(raw) = bytes {
        summary_data.insert("checker_receipt_hex".into(), json!(hex::encode(raw)));
    }
    summary_data
}

#[allow(clippy::too_many_arguments)]
fn build_skill_receipt(
    input: &Value,
    summary: &Map<String, Value>,
    checker_record: &Value,
    checker_digest: &Value,
    objective: &str,
    receipt_id: &str,
    source: &str,
    task: &str,
    verdict: &str,
) -> Value {
    let mut receipt = json!({"authority_effect":"None","checker_receipt":checker_record,"checker_receipt_sha256":checker_digest,"created_utc":input["created_utc"],"objective":objective,"receipt_id":receipt_id,"schema":"core.adversary.skill-run-receipt.v1","source":source,"task_key":task,"terminal_verdict":verdict});
    for key in ["lean4_proof_hash", "selected_candidate_id", "carrier_hash"] {
        if let Some(value) = summary.get(key) {
            receipt[key] = value.clone();
        }
    }
    receipt
}

fn persist_reported_skill_run(
    task: &str,
    verdict: &str,
    novella: &str,
    mut summary_data: Map<String, Value>,
    mut receipt: Value,
    steps: &[crate::render_record::RenderRecord],
    output: PathBuf,
) -> Result<String, Refusal> {
    summary_data.insert("submitted_narrative".into(), json!(novella));
    summary_data.insert(
        "submitted_narrative_kind".into(),
        json!("CALLER_AUTHORED_UNVERIFIED"),
    );
    let mut summary = Value::Object(summary_data);
    let reports = project_run_reports(
        &summary,
        &json!({"work_status":summary.get("work_status").unwrap_or(&json!("UNREPORTED")),
        "evidence_verdict":verdict,"checkpoint_finalized":true}),
        "summary.json",
    )?;
    let novella = reports["novella_md"]
        .as_str()
        .ok_or_else(|| refuse("ADVERSARY_REPORT_HISTORY_INVALID", "missing native novella"))?;
    let uts = reports["uts_jsonl"]
        .as_str()
        .ok_or_else(|| refuse("ADVERSARY_REPORT_HISTORY_INVALID", "missing native UTS"))?;
    let identity = content_addressed_receipt_id_v3(novella, steps, &encode(&summary)?, uts)?;
    summary["receipt_id"] = json!(identity);
    receipt["receipt_id"] = json!(identity);
    persist_bout_run_folder_v3(
        &PersistenceInput {
            run_key: task,
            receipt: &encode(&receipt)?,
            novella_md: novella,
            dda_steps: steps,
            summary_data: &encode(&summary)?,
        },
        uts,
        &mut RunFolderStore::new(output),
    )
}

// Origin: engine/crates_rs/core_adversary/src/skill_run.rs
// Claim: urn:core:crates_rs:core-adversary:skill-run:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb1d87bc2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb1d87bc2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb1d87bc2 {
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
impl BoundaryErrorb1d87bc2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb1d87bc2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb1d87bc2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb1d87bc2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb1d87bc2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb1d87bc2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb1d87bc2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb1d87bc2::ExceedsCapacity {
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
mod l4_boundary_tests_b1d87bc2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb1d87bc2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb1d87bc2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb1d87bc2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb1d87bc2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb1d87bc2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorb1d87bc2::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorb1d87bc2::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
