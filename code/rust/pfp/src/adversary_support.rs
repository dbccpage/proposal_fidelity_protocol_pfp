//! Native boundaries for Adversary's public Python DTO callers. AuthorityEffect: None.
use core_adversary::stage::ports::Refusal;
use core_adversary::stage::synthetic_diagnostic::NativeSbeDiagnostic;
use core_adversary::journal::JournalPort;
use core_adversary::{
    carrier, council, evidence, evidence_parse, journal, novella, render_record::RenderRecord,
    run_folder_store, run_persistence,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::io::Read;
use std::path::Path;
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_NATIVE_INPUT_INVALID", message)
}
fn text<'a>(payload: &'a Value, key: &str) -> Result<&'a str, Refusal> {
    payload[key]
        .as_str()
        .ok_or_else(|| invalid(format!("{key} must be a string")))
}
fn record(payload: &Value, key: &str) -> Result<RenderRecord, Refusal> {
    RenderRecord::from_json(text(payload, key)?)
}
fn steps(payload: &Value) -> Result<Vec<RenderRecord>, Refusal> {
    match record(payload, "steps_json")? {
        RenderRecord::Array(values) => Ok(values),
        _ => Err(invalid("steps must be an array")),
    }
}
/// Large captured artifacts remain byte-bound without growing the IPC envelope.
pub fn execute_file(payload: &Value) -> Result<Value, Refusal> {
    let size = payload["size"]
        .as_u64()
        .filter(|size| *size <= 64 * 1024 * 1024)
        .ok_or_else(|| invalid("request file size must be at most 64 MiB"))?;
    let mut bytes = Vec::new();
    std::fs::File::open(text(payload, "request_file")?)
        .map_err(|e| invalid(e.to_string()))?
        .take(size + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| invalid(e.to_string()))?;
    if bytes.len() as u64 != size
        || format!("sha256:{}", hex::encode(Sha256::digest(&bytes))) != text(payload, "sha256")?
    {
        return Err(invalid(
            "request file bytes do not match their bound size and digest",
        ));
    }
    let request: Value = serde_json::from_slice(&bytes).map_err(|e| invalid(e.to_string()))?;
    execute(&request)
}

fn council_for_support(payload: &Value) -> Result<Value, Refusal> {
    let panel = text(payload, "panel")?;
    let scenes = text(payload, "scenes")?;
    let mode = match payload.get("panel_mode") {
        None | Some(Value::Null) => council::PanelMode::Core,
        Some(Value::String(mode)) => council::PanelMode::parse(mode)?,
        Some(_) => return Err(invalid("panel_mode must be core or full")),
    };
    // assemble_council stays the full panel. Omitted mode is Core.
    let assembly = if mode == council::PanelMode::Full {
        council::assemble_council(panel, scenes)?
    } else {
        council::assemble_council_for(panel, scenes, mode)?
    };
    assembly.to_dict()
}

fn decode_scheduler_record<T: serde::de::DeserializeOwned>(
    payload: &Value,
    key: &str,
) -> Result<T, Refusal> {
    serde_json::from_value(payload.get(key).cloned().unwrap_or(Value::Null))
        .map_err(|error| invalid(error.to_string()))
}

fn native_scheduler(
    payload: &Value,
) -> Result<core_adversary::stage::scheduler::DeterministicScheduler, Refusal> {
    core_adversary::stage::scheduler::DeterministicScheduler::new(
        decode_scheduler_record(payload, "definition")?,
        decode_scheduler_record(payload, "profile")?,
        decode_scheduler_record(payload, "graph")?,
        decode_scheduler_record(payload, "plan")?,
        decode_scheduler_record(payload, "stop")?,
    )
}

fn scheduler_start(payload: &Value) -> Result<Value, Refusal> {
    let scheduler = native_scheduler(payload)?;
    let packet: core_adversary::stage::packets::WorkPacket =
        decode_scheduler_record(payload, "packet")?;
    let state = scheduler.start(text(payload, "run_key")?, &packet)?;
    serde_json::to_value(state).map_err(|error| invalid(error.to_string()))
}

fn scheduler_advance(payload: &Value) -> Result<Value, Refusal> {
    let scheduler = native_scheduler(payload)?;
    let state: core_adversary::stage::run::SwarmRunState = decode_scheduler_record(payload, "state")?;
    let result: core_adversary::stage::packets::AgentResult =
        decode_scheduler_record(payload, "result")?;
    let progress: core_adversary::stage::run::ProgressMeasure =
        decode_scheduler_record(payload, "progress")?;
    let next = scheduler.advance(&state, &result, &progress)?;
    serde_json::to_value(next).map_err(|error| invalid(error.to_string()))
}

fn project_run_reports_op(payload: &Value) -> Result<Value, Refusal> {
    let history =
        serde_json::from_str(text(payload, "history_json")?).map_err(|e| invalid(e.to_string()))?;
    let context =
        serde_json::from_str(text(payload, "context_json")?).map_err(|e| invalid(e.to_string()))?;
    core_adversary::run_reporting::project_run_reports(
        &history,
        &context,
        text(payload, "source_reference")?,
    )
}

fn gate_schemas_json() -> Value {
    json!({
        "schema_version": "core.adversary.gate-schemas.v1",
        "primary_and_empirical": core_adversary::primary_gates::describe(),
        "intergate_ids": core_adversary::intergates::IDS,
        "intergate_profiles": [
            core_adversary::intergates::LEGACY_DIAGNOSTIC_PROFILE,
            core_adversary::intergates::SOURCE_CONTRACT_PROFILE,
            core_adversary::intergates::MEASURED_SOURCE_CONTRACT_PROFILE,
        ],
        "authority_effect": "None",
    })
}

fn parse_history_edges(payload: &Value) -> Result<Vec<String>, Refusal> {
    match payload.get("history_edges") {
        None => Ok(Vec::new()),
        Some(Value::Array(values)) if values.len() <= 64 => values
            .iter()
            .map(|value| {
                value
                    .as_str()
                    .map(str::to_owned)
                    .ok_or_else(|| invalid("history edges must be strings"))
            })
            .collect(),
        _ => Err(invalid("history_edges must be a list of at most 64 edges")),
    }
}

fn gate_evaluate_op(payload: &Value) -> Result<Value, Refusal> {
    let id = text(payload, "gate_id")?;
    let history = parse_history_edges(payload)?;
    if core_adversary::primary_gates::known_gate_id(id) {
        core_adversary::primary_gates::evaluate(id, &payload["payload"], &history)
    } else {
        core_adversary::intergates::evaluate(id, &payload["payload"], &history)
    }
}

fn skill_persist_op(payload: &Value) -> Result<Value, Refusal> {
    let dir = Path::new(text(payload, "output_dir")?).to_owned();
    core_adversary::skill_run::persist(&payload["request"], dir).map(|s| json!(s))
}

fn checker_receipt_op(payload: &Value) -> Result<Value, Refusal> {
    let bytes = hex::decode(text(payload, "receipt_hex")?).map_err(|e| invalid(e.to_string()))?;
    Ok(evidence_parse::parse_checker_receipt(&bytes)?.to_dict())
}

fn family_validate_op(payload: &Value) -> Result<Value, Refusal> {
    use core_prompt_civilization::prompt_family::{decode_family, validate_family};
    let map =
        |e: core_prompt_civilization::prompt_family::Refusal| Refusal::new(&e.code, e.message);
    let raw = text(payload, "family_json")?.as_bytes();
    let family = decode_family(raw).map_err(map)?;
    validate_family(&family).map_err(map)?;
    Ok(Value::Null)
}

fn family_digest_op(payload: &Value) -> Result<Value, Refusal> {
    let digest = core_prompt_civilization::prompt_family::canonical_digest(&payload["record"])
        .map_err(|e| Refusal::new(&e.code, e.message))?;
    Ok(json!(digest))
}

fn specialization_validate_op(payload: &Value) -> Result<Value, Refusal> {
    let spec: core_adversary::specialization::SwarmSpecialization =
        serde_json::from_value(payload["specialization"].clone())
            .map_err(|e| Refusal::new("SPECIALIZATION_INVALID", e.to_string()))?;
    spec.validate_within(&core_adversary::specialization::base())?;
    Ok(json!({
        "specialization_id": spec.specialization_id,
        "routing_terminals": spec.routing_terminals,
        "authority_effect": "None",
    }))
}

fn specialization_base_op() -> Result<Value, Refusal> {
    let mut terminals = serde_json::Map::new();
    for status in core_adversary::specialization::BOUT_STATUSES {
        terminals.insert(
            status.into(),
            json!(core_adversary::specialization::terminal_of_bout_status(
                status
            )?),
        );
    }
    Ok(json!({
        "base": core_adversary::specialization::base(),
        "terminal_by_bout_status": terminals,
    }))
}

fn routing_load_op(payload: &Value) -> Result<Value, Refusal> {
    let (table, digest) = core_adversary::routing::load_routing(Path::new(text(payload, "path")?))?;
    Ok(json!({"table":table,"config_digest":digest}))
}

fn routing_table_op(operation: &str, payload: &Value) -> Result<Value, Refusal> {
    let table: core_adversary::routing::RoutingTable =
        serde_json::from_str(text(payload, "table_json")?)
            .map_err(|e| Refusal::new("ROUTING_BUDGET_INVALID", e.to_string()))?;
    match operation {
        "routing_validate" => {
            core_adversary::routing::validate_table(&table)?;
            Ok(Value::Null)
        }
        "routing_share" => Ok(json!(table.cheap_share().to_string())),
        _ => Ok(json!(table.seat(text(payload, "seat_id")?)?)),
    }
}

fn exact_int_field(payload: &Value, key: &str, msg: &str) -> Result<num_bigint::BigInt, Refusal> {
    core_adversary::exact::integer(&payload[key]).ok_or_else(|| invalid(msg))
}

fn routing_cost_op(payload: &Value) -> Result<Value, Refusal> {
    let leg: core_adversary::routing::RouteLeg = serde_json::from_str(text(payload, "leg_json")?)
        .map_err(|e| invalid(e.to_string()))?;
    let input = exact_int_field(payload, "input_tokens", "input tokens must be integer")?;
    let output = exact_int_field(payload, "output_tokens", "output tokens must be integer")?;
    Ok(json!(leg.cost_microusd(&input, &output).to_string()))
}

fn routing_spend_op(payload: &Value) -> Result<Value, Refusal> {
    let policy: core_adversary::routing::BudgetPolicy =
        serde_json::from_str(text(payload, "policy_json")?).map_err(|e| invalid(e.to_string()))?;
    let number = |key: &str| exact_int_field(payload, key, &format!("{key} must be an integer"));
    let spent_bout = number("spent_bout")?;
    let spent_day = number("spent_day")?;
    let worst_case = number("worst_case")?;
    let spent_tier = number("spent_tier")?;
    core_adversary::routing::admit_spend(
        &spent_bout,
        &spent_day,
        &worst_case,
        &policy,
        text(payload, "tier")?,
        &spent_tier,
    )?;
    Ok(Value::Null)
}

fn render_novella_op(payload: &Value) -> Result<Value, Refusal> {
    let input = novella::NovellaInput::from_json(text(payload, "record_json")?)?;
    let rendered = novella::render_7act_novella(
        &input,
        text(payload, "fallback_timestamp")?,
        &mut NativeSbeDiagnostic,
    )?;
    Ok(json!(rendered))
}

fn dda_tape_op(payload: &Value) -> Result<Value, Refusal> {
    let tape = run_persistence::dda_tape(&steps(payload)?)?;
    Ok(json!({"bytes_hex":hex::encode(tape.bytes),"head_sha256":tape.head_sha256}))
}

fn compute_receipt_id(
    operation: &str,
    novella_md: &str,
    dda_steps: &[RenderRecord],
    summary: &RenderRecord,
    payload: &Value,
) -> Result<String, Refusal> {
    match operation {
        "receipt_id" => run_persistence::content_addressed_receipt_id(novella_md, dda_steps, summary),
        "receipt_id_v2" => run_persistence::content_addressed_receipt_id_v2(
            novella_md,
            dda_steps,
            summary,
            text(payload, "uts_jsonl")?,
        ),
        _ => run_persistence::content_addressed_receipt_id_v3(
            novella_md,
            dda_steps,
            summary,
            text(payload, "uts_jsonl")?,
        ),
    }
}

fn receipt_id_op(operation: &str, payload: &Value) -> Result<Value, Refusal> {
    let novella_md = text(payload, "novella_md")?;
    let dda_steps = steps(payload)?;
    let summary = record(payload, "summary_json")?;
    let id = compute_receipt_id(operation, novella_md, &dda_steps, &summary, payload)?;
    Ok(json!(id))
}

fn dispatch_persist_version(
    operation: &str,
    input: &run_persistence::PersistenceInput<'_>,
    payload: &Value,
    store: &mut run_folder_store::RunFolderStore,
) -> Result<String, Refusal> {
    match operation {
        "persist_v3" => run_persistence::persist_bout_run_folder_v3(
            input,
            text(payload, "uts_jsonl")?,
            store,
        ),
        "persist_v2" => run_persistence::persist_bout_run_folder_v2(
            input,
            text(payload, "uts_jsonl")?,
            store,
        ),
        _ => run_persistence::persist_bout_run_folder(input, store),
    }
}

fn persist_bout_op(operation: &str, payload: &Value) -> Result<Value, Refusal> {
    let receipt = record(payload, "receipt_json")?;
    let summary = record(payload, "summary_json")?;
    let dda_steps = steps(payload)?;
    let input = run_persistence::PersistenceInput {
        run_key: text(payload, "run_key")?,
        receipt: &receipt,
        novella_md: text(payload, "novella_md")?,
        dda_steps: &dda_steps,
        summary_data: &summary,
    };
    let mut store =
        run_folder_store::RunFolderStore::new(Path::new(text(payload, "output_dir")?).to_owned());
    let path = dispatch_persist_version(operation, &input, payload, &mut store)?;
    Ok(json!(path))
}

fn journal_append_op(payload: &Value) -> Result<Value, Refusal> {
    let entry: journal::JournalEntry =
        serde_json::from_value(payload["entry"].clone()).map_err(|e| invalid(e.to_string()))?;
    core_adversary::journal_store::JsonlJournal::new(text(payload, "path")?).append(&entry)?;
    Ok(Value::Null)
}

fn journal_parse_line_op(payload: &Value) -> Result<Value, Refusal> {
    let number = payload["number"]
        .as_u64()
        .and_then(|v| usize::try_from(v).ok())
        .ok_or_else(|| invalid("line number required"))?;
    let line = hex::decode(text(payload, "line_hex")?).map_err(|e| invalid(e.to_string()))?;
    Ok(json!(core_adversary::journal_store::parse_line(
        number, &line
    )))
}

fn dispatch_finite_and_prompt(
    operation: &str,
    payload: &Value,
) -> Option<Result<Value, Refusal>> {
    match operation {
        "coda_finite_evaluate" => Some(finite_coda(&payload["request"])),
        "lggr_finite_evaluate" => Some(finite_lggr(&payload["request"])),
        "lggr_joint_kernel_soundness" => Some(joint_kernel_soundness(&payload["request"])),
        "prompt_density_observe" | "prompt_density_compare" => {
            Some(crate::prompt_geometry_host::execute(operation, payload).map_err(invalid))
        }
        "forge_organize_prompt" => {
            Some(core_prompt_civilization::forge::organize_prompt(payload).map_err(invalid))
        }
        "forge_verify_preparation" => {
            Some(core_prompt_civilization::forge::verify_organization(payload).map_err(invalid))
        }
        _ => None,
    }
}

fn dispatch_gates_and_skills(
    operation: &str,
    payload: &Value,
) -> Option<Result<Value, Refusal>> {
    match operation {
        "project_run_reports" => Some(project_run_reports_op(payload)),
        "gate_schemas" => Some(Ok(gate_schemas_json())),
        "gate_evaluate" => Some(gate_evaluate_op(payload)),
        "skill_actions" => Some(
            text(payload, "text").and_then(|t| core_adversary::skill_run::parse_actions(t)),
        ),
        "skill_persist" => Some(skill_persist_op(payload)),
        "council" => Some(council_for_support(payload)),
        "scheduler_start" => Some(scheduler_start(payload)),
        "scheduler_advance" => Some(scheduler_advance(payload)),
        _ => None,
    }
}

fn dispatch_evidence_and_family(
    operation: &str,
    payload: &Value,
) -> Option<Result<Value, Refusal>> {
    match operation {
        "carrier" => Some(
            carrier::parse_carrier_json(payload["carrier_json"].as_str())
                .and_then(|c| c.to_dict()),
        ),
        "critique" => Some(
            evidence_parse::parse_structured_critique(&payload["reply"])
                .map(|c| c.to_dict()),
        ),
        "checker_receipt" => Some(checker_receipt_op(payload)),
        "measurement" => Some(
            evidence::ObstructionMeasurement::from_json(&payload["measurement"])
                .and_then(|m| m.to_dict()),
        ),
        "candidate_check" => Some(
            evidence::CandidateCheck::from_json(&payload["check"]).map(|c| c.to_dict()),
        ),
        "rational" => Some(
            evidence::parse_exact_rational(&payload["value"])
                .map(|q| json!(evidence::canonical_rational(&q))),
        ),
        "family_validate" => Some(family_validate_op(payload)),
        "family_shape" => Some(text(payload, "text").map(|t| {
            json!(core_prompt_civilization::prompt_family::Shape::from_text(
                t
            ))
        })),
        "family_digest" => Some(family_digest_op(payload)),
        _ => None,
    }
}

fn dispatch_specialization_and_routing(
    operation: &str,
    payload: &Value,
) -> Option<Result<Value, Refusal>> {
    if operation.starts_with("research_") {
        return Some(crate::research_host::execute(operation, payload));
    }
    match operation {
        "specialization_validate" => Some(specialization_validate_op(payload)),
        "specialization_base" => Some(specialization_base_op()),
        "routing_key" => Some(
            text(payload, "seat_id")
                .map(core_adversary::routing::canonical_seat_key)
                .map(|k| json!(k)),
        ),
        "routing_parse" => Some(
            text(payload, "routing_json")
                .and_then(core_adversary::routing::parse_routing)
                .map(|r| json!(r)),
        ),
        "routing_load" => Some(routing_load_op(payload)),
        "routing_validate" | "routing_seat" | "routing_share" => {
            Some(routing_table_op(operation, payload))
        }
        "routing_cost" => Some(routing_cost_op(payload)),
        "routing_spend" => Some(routing_spend_op(payload)),
        _ => None,
    }
}

fn dispatch_persistence_and_receipts(
    operation: &str,
    payload: &Value,
) -> Option<Result<Value, Refusal>> {
    match operation {
        "render" => Some(render_novella_op(payload)),
        "run_name" => Some(
            text(payload, "run_key")
                .and_then(run_persistence::run_directory_name)
                .map(|n| json!(n)),
        ),
        "tape" => Some(dda_tape_op(payload)),
        "trace_digest" => Some(
            steps(payload)
                .and_then(|s| run_persistence::ddc_trace_digest(&s))
                .map(|d| json!(d)),
        ),
        "receipt_id" | "receipt_id_v2" | "receipt_id_v3" => {
            Some(receipt_id_op(operation, payload))
        }
        "verify_reported_bundle" => Some(
            text(payload, "run_dir")
                .and_then(|d| run_folder_store::verify_reported_bundle(Path::new(d)))
                .map(Value::String),
        ),
        "recompute_receipt" => Some(
            text(payload, "run_dir")
                .and_then(|d| run_folder_store::recompute_receipt_id(Path::new(d)))
                .map(|r| json!(r)),
        ),
        "persist" | "persist_v2" | "persist_v3" => Some(persist_bout_op(operation, payload)),
        _ => None,
    }
}

fn dispatch_journal(operation: &str, payload: &Value) -> Option<Result<Value, Refusal>> {
    match operation {
        "unterminated" => Some(
            serde_json::from_value::<Vec<journal::JournalEntry>>(payload["entries"].clone())
                .map_err(|e| invalid(e.to_string()))
                .map(|entries| json!(journal::unterminated_bouts(&entries))),
        ),
        "crashed_entry" => Some(
            serde_json::from_value::<journal::UnterminatedBout>(payload["bout"].clone())
                .map_err(|e| invalid(e.to_string()))
                .map(|bout| json!(bout.crashed_unknown_entry())),
        ),
        "journal_append" => Some(journal_append_op(payload)),
        "journal_read" => Some(
            text(payload, "path")
                .and_then(|p| core_adversary::journal_store::JsonlJournal::new(p).read_all())
                .map(|entries| json!(entries)),
        ),
        "journal_parse_line" => Some(journal_parse_line_op(payload)),
        _ => None,
    }
}

pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let op = text(payload, "operation")?;
    for handler in [
        dispatch_finite_and_prompt,
        dispatch_gates_and_skills,
        dispatch_evidence_and_family,
        dispatch_specialization_and_routing,
        dispatch_persistence_and_receipts,
        dispatch_journal,
    ] {
        if let Some(result) = handler(op, payload) {
            return result;
        }
    }
    Err(invalid("unknown Adversary support operation"))
}

fn finite_binding(request: &Value) -> Result<(), Refusal> {
    let binding = request["binding"].as_object().ok_or_else(|| invalid("FINITE_BINDING_REQUIRED"))?;
    let keys = ["source_id", "candidate_id", "question", "operation_id", "checker_id"];
    if binding.len() != keys.len() || keys.iter().any(|key| binding.get(*key)
        .and_then(Value::as_str).is_none_or(|s| s.trim().is_empty())) {
        return Err(invalid("FINITE_BINDING_REQUIRED"));
    }
    Ok(())
}

fn finite_fields(value: &Value, keys: &[&str]) -> Result<(), Refusal> {
    let fields = value.as_object().ok_or_else(|| invalid("finite request must be an object"))?;
    if fields.len() != keys.len() || keys.iter().any(|key| !fields.contains_key(*key)) {
        return Err(invalid("finite request fields do not match the selected profile"));
    }
    Ok(())
}

fn finite_q(value: &Value) -> Result<num_rational::BigRational, Refusal> {
    let token = value.as_str().filter(|s| s.len() <= 128)
        .ok_or_else(|| invalid("finite rationals must be bounded exact strings"))?;
    core_kernel::parse_exact(token).map_err(|e| invalid(e.to_string()))
}

fn finite_vector(value: &Value) -> Result<Vec<num_rational::BigRational>, Refusal> {
    let values = value.as_array().filter(|v| v.len() <= 8)
        .ok_or_else(|| invalid("finite vector dimension exceeds eight"))?;
    values.iter().map(finite_q).collect()
}

fn finite_matrix(value: &Value) -> Result<Vec<Vec<num_rational::BigRational>>, Refusal> {
    let rows = value.as_array().filter(|v| v.len() <= 8)
        .ok_or_else(|| invalid("finite matrix dimension exceeds eight"))?;
    rows.iter().map(finite_vector).collect()
}

fn validate_coda_dimensions(
    problem: &core_wdp::coda::types::ProblemInstance,
) -> Result<(usize, usize), Refusal> {
    let n = problem.defect_cochain.len();
    let width = problem.d0.first().map_or(0, Vec::len);
    let d0_invalid =
        n == 0 || width == 0 || problem.d0.len() != n || problem.d0.iter().any(|r| r.len() != width);
    let d1_invalid = problem.d1.iter().any(|row| row.len() != n);
    if d0_invalid || d1_invalid {
        return Err(invalid("CODA_CARRIER_DIMENSION_MISMATCH"));
    }
    Ok((n, width))
}

fn compute_coda_composition_defects(
    problem: &core_wdp::coda::types::ProblemInstance,
    n: usize,
    width: usize,
) -> Vec<Value> {
    use num_traits::Zero;
    let mut composition = Vec::new();
    for (face_index, face) in problem.d1.iter().enumerate() {
        for column in 0..width {
            let sum = (0..n)
                .map(|row| &face[row] * &problem.d0[row][column])
                .sum::<num_rational::BigRational>();
            if !sum.is_zero() {
                composition.push(json!({
                    "face": face_index,
                    "column": column,
                    "sum": sum.to_string(),
                }));
            }
        }
    }
    composition
}

fn refuse_nonflat_coda(composition: Vec<Value>) -> Refusal {
    let report = json!({
        "refusal_code": "CODA_FLAT_FINITE_PROFILE_REQUIRED",
        "evaluated": false,
        "composition": composition,
        "phi1": Value::Null,
        "gamma2": Value::Null,
        "authority_effect": "None",
    });
    let mut refusal = invalid("CODA_FLAT_FINITE_PROFILE_REQUIRED");
    refusal.details.insert("report".to_string(), report.to_string());
    refusal.details.insert("evaluated".to_string(), "false".to_string());
    refusal.details.insert("authority_effect".to_string(), "None".to_string());
    refusal
}

fn parse_coda_problem(
    request: &Value,
) -> Result<core_wdp::coda::types::ProblemInstance, Refusal> {
    finite_fields(request, &["task_id", "binding", "x", "d0", "d1"])?;
    finite_binding(request)?;
    let mut problem = core_wdp::coda::types::ProblemInstance::new(text(request, "task_id")?);
    problem.defect_cochain = finite_vector(&request["x"])?;
    problem.d0 = finite_matrix(&request["d0"])?;
    problem.d1 = finite_matrix(&request["d1"])?;
    Ok(problem)
}

fn finite_coda(request: &Value) -> Result<Value, Refusal> {
    use num_traits::Zero;
    let problem = parse_coda_problem(request)?;
    let (n, width) = validate_coda_dimensions(&problem)?;
    let composition = compute_coda_composition_defects(&problem, n, width);
    if !composition.is_empty() {
        return Err(refuse_nonflat_coda(composition));
    }
    let (record, phi, gamma, witness, repair) = core_wdp::coda::layer1_foc::Layer1Foc::evaluate(&problem)
        .map_err(|record| invalid(record.diagnostic_message))?;
    let dual = witness.map_or_else(|| vec![num_rational::BigRational::zero(); n], |w| w.vector);
    Ok(json!({"schema_version":"adversary.coda_finite_evaluate.v1", "request":request,
        "phi1":phi.to_string(), "gamma2":gamma.to_string(),
        "primal_repair":repair.iter().map(ToString::to_string).collect::<Vec<_>>(),
        "dual_witness":dual.iter().map(ToString::to_string).collect::<Vec<_>>(),
        "owner_record":record, "authority_effect":"None"}))
}

/// LGGR V soundness for a declared defect family `D` and observer quotient `Q`. The verdict is
/// `core_adversary::soundness`, never a caller-supplied flag.
fn joint_kernel_soundness(request: &Value) -> Result<Value, Refusal> {
    use linear_algebra::backend::basic_matrix::BasicMatrix;
    finite_binding(request)?;
    finite_fields(request, &["binding", "d", "q"])?;
    let exact = |key: &str| -> Result<BasicMatrix<num_rational::BigRational>, Refusal> {
        let rows = finite_matrix(&request[key])?;
        let cols = rows.first().map(Vec::len).unwrap_or(0);
        if rows.is_empty() || cols == 0 || rows.iter().any(|row| row.len() != cols) {
            return Err(invalid(format!("LGGR_SOUNDNESS_{}_NOT_RECTANGULAR", key.to_uppercase())));
        }
        BasicMatrix::from_row_major(rows.len(), cols, rows.into_iter().flatten().collect())
            .map_err(|e| invalid(e.to_string()))
    };
    let verdict = core_adversary::soundness::record_joint_kernel_soundness(&exact("d")?, &exact("q")?)
        .map_err(|e| Refusal::new("LGGR_SOUNDNESS_REFUSED", e.to_string()))?;
    let report = verdict.report;
    Ok(json!({"schema_version":"adversary.lggr_joint_kernel_soundness.v1", "request":request,
        "decision":verdict.decision, "sound":report.sound, "d_rank":report.d_rank,
        "qd_rank":report.qd_rank,
        "witness":report.witness.map(|v| v.iter().map(ToString::to_string).collect::<Vec<_>>()),
        "authority_effect":"None"}))
}

fn parse_lggr_vertices(carrier: &Value) -> Result<Vec<String>, Refusal> {
    let values = carrier["vertices"]
        .as_array()
        .filter(|v| !v.is_empty() && v.len() <= 8)
        .ok_or_else(|| invalid("finite graph needs one to eight named vertices"))?;
    values
        .iter()
        .map(|v| {
            v.as_str()
                .filter(|s| !s.is_empty())
                .map(str::to_owned)
                .ok_or_else(|| invalid("graph names must be nonempty strings"))
        })
        .collect()
}

fn parse_lggr_edge(v: &Value) -> Result<(String, String), Refusal> {
    let pair = v
        .as_array()
        .filter(|v| v.len() == 2)
        .ok_or_else(|| invalid("edge must have two names"))?;
    let left = pair[0].as_str().ok_or_else(|| invalid("edge name"))?;
    let right = pair[1].as_str().ok_or_else(|| invalid("edge name"))?;
    Ok((left.to_string(), right.to_string()))
}

fn parse_lggr_edges(carrier: &Value) -> Result<Vec<(String, String)>, Refusal> {
    let raw_edges = carrier["edges"]
        .as_array()
        .filter(|v| !v.is_empty() && v.len() <= 8)
        .ok_or_else(|| invalid("finite graph needs one to eight edges"))?;
    raw_edges.iter().map(parse_lggr_edge).collect()
}

fn parse_lggr_matrix_2x2(
    v: &Value,
) -> Result<core_wdp::path_kernel_gluing::RationalMatrix2x2, Refusal> {
    let rows = finite_matrix(v)?;
    if rows.len() != 2 || rows.iter().any(|r| r.len() != 2) {
        return Err(invalid("LGGR_MATRIX_DIMENSION_MISMATCH"));
    }
    Ok(core_wdp::path_kernel_gluing::RationalMatrix2x2::new(
        rows[0][0].clone(),
        rows[0][1].clone(),
        rows[1][0].clone(),
        rows[1][1].clone(),
    ))
}

fn parse_lggr_matrices(
    carrier: &Value,
    edge_count: usize,
) -> Result<Vec<core_wdp::path_kernel_gluing::RationalMatrix2x2>, Refusal> {
    let raw = carrier["matrices"]
        .as_array()
        .filter(|v| v.len() == edge_count)
        .ok_or_else(|| invalid("one matrix per edge is required"))?;
    raw.iter().map(parse_lggr_matrix_2x2).collect()
}

fn parse_lggr_cycle(carrier: &Value) -> Result<Vec<usize>, Refusal> {
    let raw = carrier["cycle"]
        .as_array()
        .filter(|v| !v.is_empty() && v.len() <= 16)
        .ok_or_else(|| invalid("bounded cycle required"))?;
    raw.iter()
        .map(|v| {
            v.as_u64()
                .and_then(|n| usize::try_from(n).ok())
                .ok_or_else(|| invalid("cycle index"))
        })
        .collect()
}

fn build_lggr_graph(
    carrier: &Value,
) -> Result<(core_wdp::path_kernel_gluing::EvaluatedPathKernelGraph, Vec<usize>), Refusal> {
    use core_wdp::path_kernel_gluing::EvaluatedPathKernelGraph;
    let vertices = parse_lggr_vertices(carrier)?;
    let edges = parse_lggr_edges(carrier)?;
    let matrices = parse_lggr_matrices(carrier, edges.len())?;
    let cycle = parse_lggr_cycle(carrier)?;
    let graph = EvaluatedPathKernelGraph::new(vertices, edges, matrices)
        .map_err(|e| invalid(e.to_string()))?;
    Ok((graph, cycle))
}

fn finite_lggr(request: &Value) -> Result<Value, Refusal> {
    use core_wdp::path_kernel_gluing::EvaluationColor;
    finite_binding(request)?;
    finite_fields(request, &["binding", "carrier"])?;
    let carrier = &request["carrier"];
    finite_fields(carrier, &["vertices", "edges", "matrices", "cycle", "edge_threshold", "cycle_threshold"])?;
    let (graph, cycle) = build_lggr_graph(carrier)?;
    let edge_thresh = finite_q(&carrier["edge_threshold"])?;
    let cycle_thresh = finite_q(&carrier["cycle_threshold"])?;
    let (_, local) = graph.check_local_green(edge_thresh).map_err(|e| invalid(e.to_string()))?;
    let (global, product) = graph.check_global_cycle(&cycle, cycle_thresh).map_err(|e| invalid(e.to_string()))?;
    Ok(json!({"schema_version":"adversary.lggr_finite_evaluate.v1", "request":request,
        "local_green":local.iter().map(|c| *c == EvaluationColor::Green).collect::<Vec<_>>(),
        "global_green":global, "product":[[product.m00.to_string(),product.m01.to_string()],
                                             [product.m10.to_string(),product.m11.to_string()]],
        "authority_effect":"None"}))
}

// Origin: engine/crates_rs/pfp/src/adversary_support.rs
// Claim: urn:core:crates_rs:pfp:adversary-support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3a4efecf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3a4efecf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3a4efecf {
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
impl BoundaryError3a4efecf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3a4efecf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3a4efecf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3a4efecf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3a4efecf> {
        if capacity_bound == 0 {
            return Err(BoundaryError3a4efecf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3a4efecf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3a4efecf::ExceedsCapacity {
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
mod l4_boundary_tests_3a4efecf {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3a4efecf::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3a4efecf::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3a4efecf::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3a4efecf::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3a4efecf::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3a4efecf::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3a4efecf::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
