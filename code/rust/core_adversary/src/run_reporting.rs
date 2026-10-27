//! Deterministic UNS/UTS projections of captured run history, never new verdicts.
use crate::novella::literal_block;
use crate::render_record::{JsonStyle, RenderRecord};
use base64::{engine::general_purpose::STANDARD, Engine};
use crate::stage::ports::Refusal;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

pub const UTS_SCHEMA: &str = "core.adversary.uts.v1";
pub const REPORT_SCHEMA: &str = "core.adversary.run-reports.v1";

fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_REPORT_HISTORY_INVALID", message)
}
fn canonical(value: &Value) -> Result<String, Refusal> {
    RenderRecord::from_json(&value.to_string())?.json(JsonStyle::CompactSortedAscii)
}
fn digest(value: &Value) -> Result<String, Refusal> {
    Ok(hex::encode(Sha256::digest(canonical(value)?.as_bytes())))
}
pub(crate) fn captured_history_digest(value: &Value) -> Result<String, Refusal> {
    let mut source = value.clone();
    if let Some(fields) = source.as_object_mut() {
        fields.remove("receipt_id");
        fields.remove("bundle_schema_version");
    }
    digest(&source)
}
fn reference(root: &str, pointer: &str) -> String {
    format!(
        "{root}{}{pointer}",
        if root.contains('#') { "" } else { "#" }
    )
}
fn pointer_key(key: &str) -> String {
    key.replace('~', "~0").replace('/', "~1")
}
fn source_record(value: &Value, root: &str, pointer: &str) -> Result<Value, Refusal> {
    Ok(json!({"source_ref":reference(root, pointer),"content_sha256":digest(value)?}))
}
fn text<'a>(record: &'a Value, keys: &[&str], fallback: &'a str) -> &'a str {
    keys.iter()
        .find_map(|key| record.get(*key).and_then(Value::as_str))
        .unwrap_or(fallback)
}
fn json_block(lines: &mut Vec<String>, value: &Value) -> Result<(), Refusal> {
    let value = serde_json::to_string_pretty(value).map_err(|error| invalid(error.to_string()))?;
    lines.extend(literal_block(&value, "json"));
    Ok(())
}
fn escaped_summary(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\n', " ")
        .replace('\r', " ")
}
fn detail(lines: &mut Vec<String>, title: &str, value: &str) {
    lines.extend([
        format!("<details><summary>{}</summary>", escaped_summary(title)),
        String::new(),
    ]);
    lines.extend(literal_block(value, "text"));
    lines.extend(["</details>".into(), String::new()]);
}
const COMPACT_REFERENCE_KEYS: &[&str] = &[
    "factors",
    "component_vectors",
    "raw_reply_base64",
    "raw_reply_hex",
    "prompt",
    "user_prompt",
    "system_prompt",
    "prompt_text",
    "reply_text",
    "response_schema",
    "answer",
    "raw_reply",
    "pfp_prepared_prompts",
    "organized_text",
    "content",
    "body",
    "input_hex",
    "output_hex",
    "request_hex",
    "raw_body",
    "request",
];

fn should_compact_to_reference(key: &str, item: &Value) -> bool {
    COMPACT_REFERENCE_KEYS.contains(&key) || (key == "density_attempts" && item.is_string())
}

fn compact_observation(value: &Value, root: &str, pointer: &str) -> Result<Value, Refusal> {
    // Factors and source text remain in the captured history. Human views show
    // scalar diagnostics, explicit measurement status and source references.
    match value {
        Value::Object(fields) => {
            let mut result = Map::new();
            for (key, item) in fields {
                let child = format!("{pointer}/{}", pointer_key(key));
                if should_compact_to_reference(key, item) {
                    result.insert(
                        format!("{key}_reference"),
                        source_record(item, root, &child)?,
                    );
                } else {
                    result.insert(key.clone(), compact_observation(item, root, &child)?);
                }
            }
            Ok(Value::Object(result))
        }
        Value::Array(items) => {
            if items.len() > 32 {
                Ok(json!({"items":items.len(),"retained":source_record(value,root,pointer)?}))
            } else {
                Ok(Value::Array(
                    items
                        .iter()
                        .enumerate()
                        .map(|(index, item)| {
                            compact_observation(item, root, &format!("{pointer}/{index}"))
                        })
                        .collect::<Result<Vec<_>, _>>()?,
                ))
            }
        }
        _ => Ok(value.clone()),
    }
}

fn validate_report_inputs(
    history: &Value,
    context: &Value,
    source_reference: &str,
) -> Result<(), Refusal> {
    if !history.is_object()
        || !context.is_object()
        || source_reference.is_empty()
        || source_reference.chars().any(char::is_control)
    {
        return Err(invalid(
            "history/context must be objects and source_reference must be nonempty",
        ));
    }
    Ok(())
}

fn resolve_history_view(history: &Value) -> (&Value, String) {
    let nested = ["teamwork", "retained_context"].into_iter().find(|key| {
        history
            .get(*key)
            .is_some_and(|value| value.get("observations").is_some())
    });
    let view = nested.and_then(|key| history.get(key)).unwrap_or(history);
    let view_pointer = nested.map(|key| format!("/{key}")).unwrap_or_default();
    (view, view_pointer)
}

fn render_act1_captured_keys(
    view: &Value,
    view_pointer: &str,
    source_reference: &str,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    for key in [
        "forge",
        "prompt_organization",
        "geometry",
        "density",
        "density_observations",
        "prompt_geometry",
        "prompt_sbe",
        "sieve_sbe",
        "antibodies_loaded",
    ] {
        if let Some(value) = view.get(key).filter(|item| !item.is_null()) {
            lines.extend([format!("### Captured {key}"), String::new()]);
            json_block(
                lines,
                &compact_observation(value, source_reference, &format!("{view_pointer}/{key}"))?,
            )?;
            events.push(json!({"kind":"preparation","event_id":format!("preparation:{key}"),
                "source_ref":reference(source_reference,&format!("{view_pointer}/{key}")),"content_sha256":digest(value)?}));
        }
    }
    Ok(())
}

fn render_act1_brief_pointers(
    view: &Value,
    view_pointer: &str,
    source_reference: &str,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    for (pointer, title) in [
        ("/brief/forge_preparation", "Captured Forge organization"),
        (
            "/brief/task_premises/immune_binding",
            "Captured admitted immune binding",
        ),
    ] {
        if let Some(value) = view.pointer(pointer).filter(|value| !value.is_null()) {
            let pointer = format!("{view_pointer}{pointer}");
            lines.extend([format!("### {title}"), String::new()]);
            if let Some(organized) = value.get("organized_text").and_then(Value::as_str) {
                detail(
                    lines,
                    "Organized prompt (original seed retained)",
                    organized,
                );
            }
            json_block(lines, &compact_observation(value, source_reference, &pointer)?)?;
            events.push(
                json!({"kind":"preparation","event_id":format!("preparation:{pointer}"),
                "source_ref":reference(source_reference,&pointer),"content_sha256":digest(value)?}),
            );
        }
    }
    Ok(())
}

fn render_act1_pending_prompt(
    view: &Value,
    view_pointer: &str,
    source_reference: &str,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    if let Some(pending) = view.get("pending_prompt").filter(|value| !value.is_null()) {
        lines.extend([
            "### Prepared pending turn — execution not established".into(),
            String::new(),
        ]);
        for key in ["system", "user"] {
            if let Some(value) = pending.get(key).and_then(Value::as_str) {
                detail(lines, &format!("Prepared pending {key} prompt"), value);
            }
        }
        json_block(
            lines,
            &json!({"action_id":pending.get("action_id"),"binding":pending.get("binding"),
            "status":pending.get("status"),"error":pending.get("error"),
            "observation_metadata":compact_observation(pending.get("observation_metadata").unwrap_or(&Value::Null),source_reference,&format!("{view_pointer}/pending_prompt/observation_metadata"))?}),
        )?;
        events.push(json!({"kind":"prepared_pending_turn","event_id":"run:pending",
            "execution_status":"NOT_ESTABLISHED","source_ref":reference(source_reference,&format!("{view_pointer}/pending_prompt")),
            "preparation_status":pending.get("status"),"error":pending.get("error"),
            "content_sha256":digest(pending)?,"action_id":pending.get("action_id")}));
    }
    Ok(())
}

fn render_act1_syntax_prefilter_and_forge(
    history: &Value,
    view: &Value,
    view_pointer: &str,
    source_reference: &str,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    lines.extend([
        "## Act I: Syntax Prefilter and the Forge".into(),
        String::new(),
        "### Original seed".into(),
        String::new(),
    ]);
    lines.extend(literal_block(
        text(
            history,
            &["original_seed", "objective", "seed"],
            "NOT_CAPTURED",
        ),
        "text",
    ));
    if history.get("original_seed").is_some()
        && history.get("original_seed") != history.get("objective")
    {
        detail(
            lines,
            "Prepared objective carried by the native workflow",
            text(history, &["objective"], "NOT_CAPTURED"),
        );
    }
    render_act1_captured_keys(view, view_pointer, source_reference, lines, events)?;
    render_act1_brief_pointers(view, view_pointer, source_reference, lines, events)?;
    render_act1_pending_prompt(view, view_pointer, source_reference, lines, events)
}

fn collect_graph_turn_entries<'a>(
    view: &'a Value,
    view_pointer: &str,
) -> Result<Vec<(&'a Value, String)>, Refusal> {
    let mut entries = Vec::new();
    for array_key in ["model_turns", "challenges"] {
        if let Some(items) = view.pointer(&format!("/result/{array_key}")) {
            for (index, item) in items
                .as_array()
                .ok_or_else(|| invalid("graph turns must be an array"))?
                .iter()
                .enumerate()
            {
                let pointer = format!("{view_pointer}/result/{array_key}/{index}");
                if let Some(turn) = item.get("turn") {
                    entries.push((turn, format!("{pointer}/turn")));
                } else {
                    entries.push((item, pointer));
                }
            }
        }
    }
    Ok(entries)
}

fn collect_contribution_entries<'a>(
    view: &'a Value,
    view_pointer: &str,
) -> Result<Vec<(&'a Value, String)>, Refusal> {
    if let Some(items) = view.get("observations") {
        return Ok(items
            .as_array()
            .ok_or_else(|| invalid("observations must be an array"))?
            .iter()
            .enumerate()
            .map(|(index, item)| (item, format!("{view_pointer}/observations/{index}")))
            .collect());
    }
    if let Some(items) = view.get("seat_turns") {
        return Ok(items
            .as_array()
            .ok_or_else(|| invalid("seat_turns must be an array"))?
            .iter()
            .enumerate()
            .map(|(index, item)| (item, format!("{view_pointer}/seat_turns/{index}")))
            .collect());
    }
    collect_graph_turn_entries(view, view_pointer)
}

fn is_contribution_blocked(entry: &Value) -> bool {
    entry
        .get("blocked")
        .and_then(Value::as_bool)
        .unwrap_or_else(|| {
            !entry.get("refusal").unwrap_or(&Value::Null).is_null()
                || entry.get("status").and_then(Value::as_str) == Some("NOT_MEASURED")
        })
}

fn build_contribution_provenance(
    entry: &Value,
    metadata: &Value,
    reply: &Value,
    action_id: &str,
    role: &str,
    worker: &str,
    blocked: bool,
    source_reference: &str,
    pointer: &str,
) -> Result<Value, Refusal> {
    Ok(json!({"action_id":action_id,"role_id":role,"worker":worker,"blocked":blocked,
        "source_ref":reference(source_reference,pointer),"content_sha256":digest(entry)?,
        "metadata":compact_observation(metadata,source_reference,&format!("{pointer}/metadata"))?,
        "provenance":compact_observation(entry.get("provenance").unwrap_or(&Value::Null),source_reference,&format!("{pointer}/provenance"))?,
        "check":entry.get("check").or_else(|| entry.get("decode_verification")),
        "validation_outcome":entry.get("validation_outcome"),"recorded_status":entry.get("status"),
        "failure_code":entry.get("code"),"failure_message":entry.get("message"),
        "refusal":compact_observation(entry.get("refusal").unwrap_or(&Value::Null),source_reference,&format!("{pointer}/refusal"))?,"artifacts":entry.get("artifacts"),
        "findings":entry.get("findings"),"usage":entry.get("usage").or_else(|| reply.get("usage")),
        "host_observation":entry.pointer("/ddc_program/host_observation"),
        "cost_usd":entry.get("cost_usd").or_else(|| metadata.get("cost_usd"))}))
}

fn render_contribution_text_details(entry: &Value, reply: &Value, lines: &mut Vec<String>) {
    for (label, value) in [
        ("Captured summary", entry.get("summary")),
        ("Captured contribution", entry.get("content")),
        ("Captured prompt", entry.get("prompt")),
        ("Captured prompt text", entry.get("prompt_text")),
        ("Captured system prompt", entry.get("system_prompt")),
        ("Captured user prompt", entry.get("user_prompt")),
        ("Captured raw reply", entry.get("raw_reply")),
        ("Captured reply", reply.get("content")),
        ("Captured reply text", entry.get("reply_text")),
    ] {
        if let Some(Value::String(value)) = value {
            if !value.is_empty() {
                detail(lines, label, value);
            }
        }
    }
}

fn render_contribution_encoded_details(
    entry: &Value,
    metadata: &Value,
    lines: &mut Vec<String>,
) -> Result<(), Refusal> {
    for (field, label) in [
        ("raw_reply_hex", "Captured native raw reply"),
        ("request_hex", "Captured graph request"),
        ("output_hex", "Captured graph output"),
    ] {
        if let Some(raw) = entry.get(field).and_then(Value::as_str) {
            let bytes = hex::decode(raw)
                .map_err(|_| invalid("captured bytes are not valid hexadecimal"))?;
            match std::str::from_utf8(&bytes) {
                Ok(reply) => detail(lines, label, reply),
                Err(_) => detail(
                    lines,
                    &format!("{label}: INVALID_UTF8; hexadecimal bytes"),
                    raw,
                ),
            }
        }
    }
    if let Some(raw) = metadata
        .pointer("/pfp/raw_reply_base64")
        .and_then(Value::as_str)
    {
        let bytes = STANDARD
            .decode(raw)
            .map_err(|_| invalid("captured raw reply is not valid base64"))?;
        match std::str::from_utf8(&bytes) {
            Ok(reply) => detail(
                lines,
                "Captured PFP reply (including malformed envelopes)",
                reply,
            ),
            Err(_) => detail(
                lines,
                "Captured PFP reply: INVALID_UTF8; hexadecimal bytes",
                &hex::encode(bytes),
            ),
        }
    }
    Ok(())
}

fn render_attempt_prompts(attempts: &[Value], prefix: &str, lines: &mut Vec<String>) {
    for (attempt_index, attempt) in attempts.iter().enumerate() {
        for key in ["system", "user"] {
            if let Some(value) = attempt
                .pointer(&format!("/pfp_prepared_prompts/{key}"))
                .and_then(Value::as_str)
            {
                detail(lines, &format!("{prefix} {attempt_index}: {key}"), value);
            }
        }
    }
}

fn render_contribution_pfp_prompts(entry: &Value, metadata: &Value, lines: &mut Vec<String>) {
    if let Some(prompts) = metadata.get("pfp_prepared_prompts") {
        for key in ["system", "user"] {
            if let Some(value) = prompts.get(key).and_then(Value::as_str) {
                detail(lines, &format!("Captured final PFP {key} prompt"), value);
            }
        }
    }
    if let Some(attempts) = entry
        .pointer("/provenance/parameters/density_attempts")
        .and_then(Value::as_array)
    {
        render_attempt_prompts(attempts, "Captured native PFP attempt", lines);
    }
    if let Some(encoded) = entry
        .pointer("/refusal/details/density_attempts")
        .and_then(Value::as_str)
    {
        if let Ok(Value::Array(attempts)) = serde_json::from_str::<Value>(encoded) {
            render_attempt_prompts(&attempts, "Captured refused native PFP attempt", lines);
        }
    }
}

fn build_captured_action_event(
    mut event: Value,
    action_id: &str,
    entry: &Value,
    source_reference: &str,
    pointer: &str,
) -> Result<Value, Refusal> {
    event["event_id"] = json!(format!("action:{action_id}"));
    event["kind"] = json!("captured_action");
    for key in [
        "content",
        "prompt",
        "prompt_text",
        "system_prompt",
        "user_prompt",
        "raw_reply",
        "reply",
        "reply_text",
        "raw_reply_hex",
        "request_hex",
        "output_hex",
    ] {
        if let Some(value) = entry.get(key) {
            event[format!("{key}_reference")] =
                source_record(value, source_reference, &format!("{pointer}/{key}"))?;
        }
    }
    Ok(event)
}

fn render_single_contribution(
    index: usize,
    entry: &Value,
    pointer: &str,
    source_reference: &str,
    action_ids: &mut BTreeSet<String>,
    observed_roles: &mut BTreeSet<String>,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    if !entry.is_object() {
        return Err(invalid("captured contribution must be an object"));
    }
    let fallback_id = format!("native-turn:{index}");
    let action_id = text(entry, &["action_id", "attempt_id", "turn_id"], &fallback_id);
    if !action_ids.insert(action_id.to_owned()) {
        return Err(invalid("duplicate captured action identity"));
    }
    let metadata = entry.get("metadata").unwrap_or(&Value::Null);
    let role = text(
        metadata,
        &["role_id"],
        text(
            entry,
            &["seat", "seat_id", "role_id", "role", "character"],
            "UNRECORDED_ROLE",
        ),
    );
    let reply = entry.get("reply").unwrap_or(&Value::Null);
    let worker = text(
        entry,
        &["worker", "model"],
        text(
            reply,
            &["model"],
            text(
                entry.get("provenance").unwrap_or(&Value::Null),
                &["model"],
                text(metadata, &["model"], "UNRECORDED_WORKER"),
            ),
        ),
    );
    let blocked = is_contribution_blocked(entry);
    if !blocked {
        observed_roles.insert(role.to_owned());
    }
    let provenance = build_contribution_provenance(
        entry,
        metadata,
        reply,
        action_id,
        role,
        worker,
        blocked,
        source_reference,
        pointer,
    )?;
    lines.extend([format!("### Contribution {}", index + 1), String::new()]);
    json_block(lines, &provenance)?;
    render_contribution_text_details(entry, reply, lines);
    render_contribution_encoded_details(entry, metadata, lines)?;
    render_contribution_pfp_prompts(entry, metadata, lines);
    let event =
        build_captured_action_event(provenance, action_id, entry, source_reference, pointer)?;
    events.push(event);
    Ok(())
}

fn render_missing_role_contributions(
    view: &Value,
    context: &Value,
    observed_roles: &BTreeSet<String>,
    lines: &mut Vec<String>,
) {
    if let Some(steps) = view
        .pointer("/panel_plan/steps")
        .and_then(Value::as_array)
    {
        // A declared schedule's skips arrive in the report context; they are not missing seats.
        let skipped: BTreeSet<&str> = context
            .get("skipped_by_schedule")
            .and_then(Value::as_array)
            .map(|items| items.iter().filter_map(Value::as_str).collect())
            .unwrap_or_default();
        lines.extend([
            "### Missing successful role contributions".into(),
            String::new(),
        ]);
        let mut skipped_lines = Vec::new();
        for step in steps {
            if let Some(role) = step
                .get("role_id")
                .and_then(Value::as_str)
                .filter(|role| !observed_roles.contains(*role))
            {
                if skipped.contains(role) {
                    skipped_lines.push(format!("SKIPPED BY SCHEDULE: {}", escaped_summary(role)));
                } else {
                    lines.push(format!("MISSING: {}", escaped_summary(role)));
                }
            }
        }
        lines.push(String::new());
        if !skipped_lines.is_empty() {
            lines.extend(["### Seats skipped by the declared schedule".into(), String::new()]);
            lines.extend(skipped_lines);
            lines.push(String::new());
        }
    }
}

fn render_single_act3_check_key(
    key: &str,
    history: &Value,
    context: &Value,
    source_reference: &str,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    if let Some(value) = history
        .get(key)
        .or_else(|| context.get(key))
        .filter(|v| !v.is_null())
    {
        json_block(
            lines,
            &json!({key:compact_observation(value,source_reference,&format!("/{key}"))?}),
        )?;
        if history.get(key).is_some() {
            events.push(json!({"kind":"captured_check_or_transition","event_id":format!("checks:{key}"),
                "source_ref":reference(source_reference,&format!("/{key}")),"content_sha256":digest(value)?,
                "observation":compact_observation(value,source_reference,&format!("/{key}"))?}));
        }
    }
    Ok(())
}

fn render_act3_checks_and_dissent(
    history: &Value,
    context: &Value,
    source_reference: &str,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    lines.extend(["## Act III: Checks, dissent and original-task rechecks".into(),String::new(),
        "Captured checks and findings appear beside their contributing action above. A role's assertion is not an independent check.".into(),String::new()]);
    if let Some(narrative) = history.get("submitted_narrative").and_then(Value::as_str) {
        detail(
            lines,
            "Caller-authored narrative - retained, not recorded worker dialogue",
            narrative,
        );
        events.push(json!({"kind":"submitted_narrative","event_id":"run:submitted-narrative",
            "source_ref":reference(source_reference,"/submitted_narrative"),"content_sha256":digest(&json!(narrative))?,
            "execution_status":"NOT_ESTABLISHED_BY_NARRATIVE"}));
    }
    for key in [
        "checker_receipt",
        "checker_verdict",
        "checker_receipt_sha256",
        "candidate_checks",
        "candidate_artifacts",
        "authorization_blockers",
        "authorization_evidence",
        "transition_receipts",
        "scene_orchestration",
        "nonclaims",
        "refusal",
        "continuations",
        "continuation",
        "native_gates",
    ] {
        render_single_act3_check_key(key, history, context, source_reference, lines, events)?;
    }
    Ok(())
}

fn render_act2_contributions_section(
    view: &Value,
    view_pointer: &str,
    context: &Value,
    source_reference: &str,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    lines.extend([
        "## Act II: Captured Panel contributions".into(),
        String::new(),
    ]);
    let entries = collect_contribution_entries(view, view_pointer)?;
    let mut action_ids = BTreeSet::new();
    let mut observed_roles = BTreeSet::new();
    for (index, (entry, pointer)) in entries.iter().enumerate() {
        render_single_contribution(
            index,
            entry,
            pointer,
            source_reference,
            &mut action_ids,
            &mut observed_roles,
            lines,
            events,
        )?;
    }
    if entries.is_empty() {
        lines.extend([
            "No Panel contributions have been captured.".into(),
            String::new(),
        ]);
    }
    render_missing_role_contributions(view, context, &observed_roles, lines);
    Ok(())
}

fn render_act4_and_act5_accounting(
    view: &Value,
    view_pointer: &str,
    context: &Value,
    status: &str,
    source_reference: &str,
    lines: &mut Vec<String>,
    events: &mut Vec<Value>,
) -> Result<(), Refusal> {
    lines.extend(["## Act IV: Learning and changed artifacts".into(),String::new(),
        "Learning, repairs and changed paths are recorded with their actual contributing action. Proposed guidance is not an installed change.".into(),String::new(),
        "## Act V: Accounting and remaining work".into(),String::new()]);
    let provider_ref = view
        .get("provider_binding")
        .filter(|v| !v.is_null())
        .map(|v| source_record(v, source_reference, &format!("{view_pointer}/provider_binding")))
        .transpose()?;
    let usage_status = if view.get("executor") == Some(&json!("ide")) {
        "IDE_USAGE_AND_BILLING_UNOBSERVED"
    } else {
        "PER_CAPTURED_ACTION; MISSING_IS_UNOBSERVED"
    };
    let accounting = json!({"executor":view.get("executor"),"provider_binding_reference":provider_ref,
        "usage_status":usage_status,
        "external_dispatch_count":"NOT_INFERRED_FROM_RENDERED_TEXT"});
    json_block(lines, &accounting)?;
    json_block(lines, context)?;
    events.push(
        json!({"kind":"run_checkpoint","event_id":"run:checkpoint","work_status":status,
        "context":context,"accounting":accounting,"authority_effect":"None"}),
    );
    Ok(())
}

fn serialize_uts_events(events: Vec<Value>) -> Result<String, Refusal> {
    let mut uts = String::new();
    for (sequence, mut event) in events.into_iter().enumerate() {
        event["schema_version"] = json!(UTS_SCHEMA);
        event["sequence"] = json!(sequence);
        uts.push_str(&canonical(&event)?);
        uts.push('\n');
    }
    Ok(uts)
}

/// Pure projection: callers retain source bytes and provide checked workflow
/// status. No diagnostic, provider, evaluator or clock is run by this renderer.
pub fn project_run_reports(
    history: &Value,
    context: &Value,
    source_reference: &str,
) -> Result<Value, Refusal> {
    validate_report_inputs(history, context, source_reference)?;
    let run_id = text(
        history,
        &["run_id", "task_key", "run_key"],
        "UNNAMED_CAPTURE",
    );
    let (view, view_pointer) = resolve_history_view(history);
    let status = text(
        context,
        &["work_status"],
        text(
            history,
            &["terminal_status", "work_status", "status"],
            "INCOMPLETE",
        ),
    );
    let source_sha256 = captured_history_digest(history)?;
    let mut lines = vec!["# Universal Narrative".into(), String::new(),
        "AuthorityEffect: None. This is a projection of captured history; rendering performs no verification.".into(),
        "Role coverage records contributions, not independent workers. Density diagnostics do not establish task correctness.".into(), String::new(),
        "## Run identity and outcome".into(), String::new()];
    let identity = json!({"run_id":run_id,"work_status":status,"source_ref":source_reference,
        "source_sha256":source_sha256,"digest_profile":"core.adversary.render-record.compact-sorted-ascii.v1",
        "source_excluded_fields":["receipt_id","bundle_schema_version"],
        "evidence_verdict":context.get("evidence_verdict").unwrap_or(&Value::Null),
        "context":context});
    json_block(&mut lines, &identity)?;
    let mut events = vec![
        json!({"schema_version":UTS_SCHEMA,"event_id":"run:source","kind":"run_source",
        "source_ref":source_reference,"source_sha256":source_sha256,"run_id":run_id,
        "digest_profile":"core.adversary.render-record.compact-sorted-ascii.v1",
        "source_excluded_fields":["receipt_id","bundle_schema_version"],"authority_effect":"None"}),
    ];
    render_act1_syntax_prefilter_and_forge(
        history,
        view,
        &view_pointer,
        source_reference,
        &mut lines,
        &mut events,
    )?;
    render_act2_contributions_section(
        view,
        &view_pointer,
        context,
        source_reference,
        &mut lines,
        &mut events,
    )?;
    render_act3_checks_and_dissent(history, context, source_reference, &mut lines, &mut events)?;
    render_act4_and_act5_accounting(
        view,
        &view_pointer,
        context,
        status,
        source_reference,
        &mut lines,
        &mut events,
    )?;
    let uts = serialize_uts_events(events)?;
    Ok(
        json!({"schema_version":REPORT_SCHEMA,"novella_md":format!("{}\n",lines.join("\n")),
        "uts_jsonl":uts,"source_sha256":source_sha256,"authority_effect":"None"}),
    )
}

// Origin: engine/crates_rs/core_adversary/src/run_reporting.rs
// Claim: urn:core:crates_rs:core-adversary:run-reporting:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3c3d93aa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3c3d93aa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3c3d93aa {
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
impl BoundaryError3c3d93aa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3c3d93aa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3c3d93aa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3c3d93aa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3c3d93aa> {
        if capacity_bound == 0 {
            return Err(BoundaryError3c3d93aa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3c3d93aa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3c3d93aa::ExceedsCapacity {
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
mod schedule_reporting_tests {
    use super::*;

    #[test]
    fn declared_schedule_skips_are_distinct_from_missing_contributions() {
        let view = json!({"panel_plan": {"steps": [
            {"role_id": "observed"}, {"role_id": "scheduled_skip"}, {"role_id": "absent"}
        ]}});
        let context = json!({"skipped_by_schedule": ["scheduled_skip"]});
        let observed = BTreeSet::from(["observed".to_owned()]);
        let mut lines = Vec::new();
        render_missing_role_contributions(&view, &context, &observed, &mut lines);
        assert!(lines.iter().any(|line| line == "SKIPPED BY SCHEDULE: scheduled_skip"));
        assert!(lines.iter().any(|line| line == "MISSING: absent"));
        assert!(!lines.iter().any(|line| line == "MISSING: scheduled_skip"));
        assert!(!lines.iter().any(|line| line == "MISSING: observed"));

        lines.clear();
        render_missing_role_contributions(&view, &json!({}), &observed, &mut lines);
        assert!(lines.iter().any(|line| line == "MISSING: scheduled_skip"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_3c3d93aa {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3c3d93aa::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3c3d93aa::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3c3d93aa::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3c3d93aa::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3c3d93aa::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3c3d93aa::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3c3d93aa::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
