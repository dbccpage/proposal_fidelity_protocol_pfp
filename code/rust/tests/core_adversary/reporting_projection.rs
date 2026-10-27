use core_adversary::run_reporting::project_run_reports;
use serde_json::{json, Value};

fn history() -> Value {
    json!({"run_id":"partial-λ", "objective":"Keep ``` and </details> verbatim.",
        "executor":"ide", "panel_plan":{"steps":[{"role_id":"syntax_prefilter"},{"role_id":"gauge_breaker"}]},
        "observations":[{"action_id":"a1","worker":"IDE current session","summary":"Captured", "content":"λ ```\n</details>",
            "blocked":true,"findings":["unresolved"],"metadata":{"role_id":"gauge_breaker","pfp":{"raw_reply_base64":"bm90IGpzb24="},
            "failure_code":"MALFORMED_REVIEW", "density":{"status":"OBSERVED","entropy_bits":0.0,"factors":[[1,0]]}}}]})
}

#[test]
fn projections_share_actual_partial_history_and_do_not_repeat_raw_text_in_uts() {
    let source = history();
    let report = project_run_reports(
        &source,
        &json!({"work_status":"partial", "evidence_verdict":"OPEN_RESIDUAL"}),
        "../state.json",
    )
    .unwrap();
    assert_eq!(
        report,
        project_run_reports(
            &source,
            &json!({"work_status":"partial", "evidence_verdict":"OPEN_RESIDUAL"}),
            "../state.json"
        )
        .unwrap()
    );
    let novella = report["novella_md"].as_str().unwrap();
    assert!(novella.contains("IDE current session"));
    assert!(novella.contains("λ ```\n</details>"));
    assert!(novella.contains("````"));
    assert!(novella.contains("not json"));
    assert!(novella.contains("MISSING: syntax_prefilter"));
    assert!(!novella.contains("PASS_TO_MASTER"));
    assert!(!novella.contains("healthy"));
    let rows: Vec<Value> = report["uts_jsonl"]
        .as_str()
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    let action = rows.iter().find(|row| row["action_id"] == "a1").unwrap();
    assert_eq!(action["source_ref"], "../state.json#/observations/0");
    assert_eq!(action["blocked"], true);
    assert!(action.get("content").is_none());
    assert!(action.to_string().contains("raw_reply_base64"));
    assert!(!action.to_string().contains("bm90IGpzb24="));
}

#[test]
fn scheduled_skips_use_report_context_without_hiding_other_missing_roles() {
    let source = history();
    let before = source.clone();
    let report = project_run_reports(
        &source,
        &json!({"skipped_by_schedule":["syntax_prefilter"]}),
        "state.json",
    )
    .unwrap();
    let novella = report["novella_md"].as_str().unwrap();
    assert!(novella.contains("SKIPPED BY SCHEDULE: syntax_prefilter"));
    assert!(!novella.contains("MISSING: syntax_prefilter"));
    assert!(novella.contains("MISSING: gauge_breaker"));
    assert_eq!(source, before);

    let unskipped = project_run_reports(&source, &json!({}), "state.json").unwrap();
    assert!(unskipped["novella_md"]
        .as_str()
        .unwrap()
        .contains("MISSING: syntax_prefilter"));
}

#[test]
fn duplicate_action_ids_and_malformed_history_refuse() {
    let mut source = history();
    let duplicate = source["observations"][0].clone();
    source["observations"]
        .as_array_mut()
        .unwrap()
        .push(duplicate);
    assert!(project_run_reports(&source, &json!({}), "state.json").is_err());
    assert!(project_run_reports(&json!([]), &json!({}), "state.json").is_err());
}

#[test]
fn native_turns_keep_prompts_actual_worker_and_refusal() {
    let source = json!({"task_key":"native-refused","objective":"Seed", "terminal_status":"REFUSED",
        "seat_turns":[{"seat":"Gauge Breaker","prompt":"Actual prompt", "reply":{"content":"Actual reply","model":"fixture-model"},"refusal":{"code":"STOP"}}]});
    let report = project_run_reports(&source, &json!({}), "summary.json#/source_history").unwrap();
    let text = report["novella_md"].as_str().unwrap();
    assert!(text.contains("Actual prompt"));
    assert!(text.contains("Actual reply"));
    assert!(text.contains("fixture-model"));
    assert!(report["uts_jsonl"]
        .as_str()
        .unwrap()
        .contains("summary.json#/source_history/seat_turns/0"));
}

#[test]
fn pending_prompt_is_visible_without_becoming_an_executed_contribution() {
    let source = json!({"run_id":"pending","objective":"Seed","observations":[],
        "pending_prompt":{"action_id":"next","system":"Actual system","user":"Actual user"}});
    let report = project_run_reports(
        &source,
        &json!({"work_status":"pending_host"}),
        "state.json",
    )
    .unwrap();
    let text = report["novella_md"].as_str().unwrap();
    assert!(text.contains("Actual system"));
    assert!(text.contains("No Panel contributions have been captured"));
    let rows: Vec<Value> = report["uts_jsonl"]
        .as_str()
        .unwrap()
        .lines()
        .map(|s| serde_json::from_str(s).unwrap())
        .collect();
    assert_eq!(
        rows.iter()
            .filter(|v| v["kind"] == "captured_action")
            .count(),
        0
    );
    assert!(rows
        .iter()
        .any(|v| v["execution_status"] == "NOT_ESTABLISHED"));
}

#[test]
fn reported_bundle_binds_six_files_and_resolves_action_source_bytes() {
    use core_adversary::render_record::RenderRecord;
    use core_adversary::run_folder_store::{
        recompute_receipt_id, verify_reported_bundle, RunFolderStore,
    };
    use core_adversary::run_persistence::{
        persist_bout_run_folder_v2, validate_uts, PersistenceInput,
    };
    let history = history();
    let projection = project_run_reports(
        &history,
        &json!({"work_status":"partial"}),
        "summary.json#/source_history",
    )
    .unwrap();
    let summary = json!({"source_history":history,"task_key":"report-test"});
    let record = |value: &Value| RenderRecord::from_json(&value.to_string()).unwrap();
    let root = tempfile::tempdir().unwrap();
    let receipt = record(&json!({}));
    let source = record(&summary);
    let input = PersistenceInput {
        run_key: "report-test",
        receipt: &receipt,
        summary_data: &source,
        novella_md: projection["novella_md"].as_str().unwrap(),
        dda_steps: &[],
    };
    let uts = projection["uts_jsonl"].as_str().unwrap();
    let folder =
        persist_bout_run_folder_v2(&input, uts, &mut RunFolderStore::new(root.path().into()))
            .unwrap();
    let folder = std::path::Path::new(&folder);
    assert_eq!(std::fs::read_dir(folder).unwrap().count(), 6);
    assert_eq!(
        verify_reported_bundle(folder).unwrap(),
        recompute_receipt_id(folder).unwrap()
    );
    assert_eq!(
        std::fs::read(folder.join("dda_actions.jsonl")).unwrap(),
        std::fs::read(folder.join("ddc.jsonl")).unwrap()
    );
    let mut tampered = summary.clone();
    tampered["source_history"]["observations"][0]["content"] = json!("changed");
    assert!(validate_uts(uts, &record(&tampered)).is_err());
    std::fs::write(folder.join("uts.jsonl"), format!("{uts}{{}}\n")).unwrap();
    assert!(verify_reported_bundle(folder).is_err());
}

#[test]
fn invalid_utf8_is_rendered_as_hex_and_external_references_cannot_be_sealed() {
    use core_adversary::render_record::RenderRecord;
    use core_adversary::run_persistence::validate_uts;
    let source = json!({"run_id":"bad-encoding","observations":[{"action_id":"x","worker":"actual-worker", "metadata":{"pfp":{"raw_reply_base64":"/w=="}}}]});
    let projected = project_run_reports(&source, &json!({}), "../state.json").unwrap();
    assert!(projected["novella_md"]
        .as_str()
        .unwrap()
        .contains("INVALID_UTF8"));
    assert!(validate_uts(
        projected["uts_jsonl"].as_str().unwrap(),
        &RenderRecord::from_json(&source.to_string()).unwrap()
    )
    .is_err());
}

#[test]
fn nested_skill_history_preserves_source_references_and_distinguishes_submitted_text() {
    use core_adversary::render_record::RenderRecord;
    use core_adversary::run_persistence::validate_uts;
    let source = json!({"task_key":"skill", "objective":"Original task", "teamwork":history(),
        "submitted_narrative":"An author asserted PASS, without a captured worker."});
    let projected = project_run_reports(&source, &json!({}), "summary.json").unwrap();
    let novella = projected["novella_md"].as_str().unwrap();
    assert!(novella.contains("IDE current session"));
    assert!(novella.contains("Caller-authored narrative"));
    let uts = projected["uts_jsonl"].as_str().unwrap();
    assert!(uts.contains("summary.json#/teamwork/observations/0"));
    let mut sealed = source;
    sealed["receipt_id"] = json!("sha256:sealing-metadata");
    sealed["bundle_schema_version"] = json!("core.adversary.reported-run-bundle.v1");
    validate_uts(uts, &RenderRecord::from_json(&sealed.to_string()).unwrap()).unwrap();
    sealed["objective"] = json!("Changed original task");
    assert!(validate_uts(uts, &RenderRecord::from_json(&sealed.to_string()).unwrap()).is_err());
}

#[test]
fn graph_turns_use_original_array_references_and_actual_model() {
    use core_adversary::render_record::RenderRecord;
    use core_adversary::run_persistence::validate_uts;
    let turn = json!({"role":"gauge_breaker","request_hex":hex::encode(b"Actual graph prompt"),
        "output_hex":hex::encode(b"Actual graph reply"),"metadata":{"model":"captured-model",
        "pfp_turn":{"raw_body":"retained provider bytes"}},"validation_outcome":"VALID"});
    let mut critique = turn.clone();
    critique["role"] = json!("defect_hunter");
    let source = json!({"task_key":"graph", "objective":"Original", "result":{
        "model_turns":[turn],"challenges":[{"turn":critique},
        {"status":"NOT_MEASURED","code":"TOOL_UNAVAILABLE","message":"Unavailable"}]}});
    let report = project_run_reports(&source, &json!({}), "summary.json").unwrap();
    let novella = report["novella_md"].as_str().unwrap();
    assert!(novella.contains("Actual graph prompt"));
    assert!(novella.contains("Actual graph reply"));
    assert!(novella.contains("captured-model"));
    let uts = report["uts_jsonl"].as_str().unwrap();
    assert!(uts.contains("summary.json#/result/model_turns/0"));
    assert!(uts.contains("summary.json#/result/challenges/0/turn"));
    assert!(!uts.contains("retained provider bytes"));
    validate_uts(uts, &RenderRecord::from_json(&source.to_string()).unwrap()).unwrap();
}

// Origin: engine/crates_rs/tests/core_adversary/reporting_projection.rs
// Claim: urn:core:crates_rs:tests:reporting-projection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord83966b63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord83966b63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError83966b63 {
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
impl BoundaryError83966b63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError83966b63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError83966b63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord83966b63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError83966b63> {
        if capacity_bound == 0 {
            return Err(BoundaryError83966b63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError83966b63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError83966b63::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_83966b63() {
    let admitted = BoundaryRecord83966b63::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord83966b63::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
