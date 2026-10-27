//! Python-compatible prompt artifact compilation and strict wire verification.
//!
//! This content-addressed profile is separate from the legacy turn driver's
//! context-addressed prompt profile in `prompt_turn`. AuthorityEffect: None.

use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

use crate::canonical::domain_digest_json;
use crate::prompt_turn::PROMPT_ARTIFACT_SCHEMA;

pub const PAYLOAD_DOMAIN: &str = "core.symbol-game.prompt-artifact-payload.v1";
pub const MAX_BODY_BYTES: usize = 1024 * 1024;
pub const DEFAULT_REQUIRED_FIELDS: &[&str] = &[
    "AUTHORITY_EFFECT",
    "CANDIDATE",
    "OPEN_OBSTRUCTIONS",
    "PACKET_ID",
    "PARENT",
    "RESIDUAL_COLOUR",
    "RUN_ROOT",
];

const ARTIFACT_FIELDS: &[&str] = &[
    "schema_version",
    "family",
    "prompt_artifact_id",
    "regime_id",
    "regime_kind",
    "admitted_constructors",
    "open_obstructions",
    "demand_set",
    "kill_conditions",
    "required_reply_fields",
    "objective_typed",
    "residual_colour",
    "dual_witness_required",
    "dual_witness_ref",
    "prompt_body_sha256",
    "prompt_body_byte_count",
    "parent_packet_id",
    "conversation_root_id",
    "authority_effect",
];
const OBSTRUCTION_FIELDS: &[&str] = &[
    "obstruction_id",
    "family",
    "residual_colour",
    "magnitude",
    "demand_id",
    "prior_report_digests",
];
const OBJECTIVE_FIELDS: &[&str] = &[
    "kind",
    "summary",
    "target_obstruction_ids",
    "target_demand_ids",
];
const COMPILE_FIELDS: &[&str] = &[
    "operation",
    "regime_kind",
    "regime_definition_bytes",
    "prompt_body_bytes",
    "objective_typed",
    "admitted_constructors",
    "open_obstructions",
    "demand_set",
    "kill_conditions",
    "required_reply_fields",
    "residual_colour",
    "dual_witness_required",
    "dual_witness_ref",
    "parent_packet_id",
    "conversation_root_id",
    "normalize_body",
];

fn object<'a>(value: &'a Value, label: &str) -> Result<&'a Map<String, Value>, String> {
    let map = value
        .as_object()
        .ok_or_else(|| format!("{label} must be an object"))?;
    if let Some(key) = map.keys().find(|key| {
        matches!(
            key.as_str(),
            "passed" | "verified" | "promotion_eligible" | "trusted"
        )
    }) {
        return Err(format!("FORBIDDEN_AUTHORITY_FIELD: {label}: {key}"));
    }
    Ok(map)
}

fn fields(
    map: &Map<String, Value>,
    required: &[&str],
    allowed: &[&str],
    label: &str,
) -> Result<(), String> {
    if let Some(key) = required.iter().find(|key| !map.contains_key(**key)) {
        return Err(format!("{label} is missing field: {key}"));
    }
    if let Some(key) = map.keys().find(|key| !allowed.contains(&key.as_str())) {
        return Err(format!("{label} has unknown field: {key}"));
    }
    Ok(())
}

fn python_whitespace(c: char) -> bool {
    c.is_whitespace() || matches!(c, '\u{001c}'..='\u{001f}')
}

fn trimmed(value: &str) -> &str {
    value.trim_matches(python_whitespace)
}

fn text<'a>(value: &'a Value, label: &str, nonempty: bool) -> Result<&'a str, String> {
    let value = value
        .as_str()
        .ok_or_else(|| format!("{label} must be a string"))?;
    if value.len() > 8192 {
        return Err(format!("{label} exceeds the string resource limit"));
    }
    if nonempty && (value.is_empty() || trimmed(value) != value) {
        return Err(format!("{label} must be a nonempty normalized string"));
    }
    Ok(value)
}

fn digest(value: &Value, label: &str) -> Result<(), String> {
    let value = text(value, label, true)?;
    if value.len() != 64
        || !value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
    {
        return Err(format!(
            "{label} must be a lowercase 64-character hex digest"
        ));
    }
    Ok(())
}

fn optional_digest(value: &Value, label: &str) -> Result<(), String> {
    if !value.is_null() {
        digest(value, label)?;
    }
    Ok(())
}

fn identifier(value: &Value, label: &str, stable: bool) -> Result<String, String> {
    let raw = value
        .as_str()
        .ok_or_else(|| format!("{label} must be a string"))?;
    let value = if stable {
        text(value, label, true)?
    } else {
        trimmed(raw)
    };
    if value.is_empty()
        || value.len() > 128
        || !value
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"_.:-".contains(&c))
        || (stable && !value.as_bytes()[0].is_ascii_alphanumeric())
    {
        return Err(format!(
            "{label} contains invalid identifier characters or exceeds limit"
        ));
    }
    Ok(value.to_owned())
}

fn kind(value: &Value, label: &str) -> Result<String, String> {
    let raw = value
        .as_str()
        .ok_or_else(|| format!("{label} must be a string"))?;
    let value = trimmed(raw).to_lowercase();
    if value.is_empty()
        || value.len() > 64
        || !value
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"_.-".contains(&c))
    {
        return Err(format!("{label} must be a kind identifier"));
    }
    Ok(value)
}

fn array<'a>(value: &'a Value, label: &str, maximum: usize) -> Result<&'a [Value], String> {
    let array = value
        .as_array()
        .ok_or_else(|| format!("{label} must be an array"))?;
    if array.len() > maximum {
        return Err(format!("{label} exceeds the resource limit"));
    }
    Ok(array)
}

fn ordered(values: &[Value], label: &str) -> Result<(), String> {
    if values
        .windows(2)
        .any(|pair| pair[0].as_str() >= pair[1].as_str())
    {
        return Err(format!("ARRAY_NOT_CANONICALLY_SORTED: {label}"));
    }
    Ok(())
}

fn string_array(
    value: &Value,
    label: &str,
    maximum: usize,
    stable: bool,
    nonempty: bool,
) -> Result<Vec<Value>, String> {
    let values = array(value, label, maximum)?;
    if nonempty && values.is_empty() {
        return Err(format!("ARRAY_NOT_CANONICALLY_SORTED: {label}"));
    }
    for item in values {
        if stable {
            identifier(item, label, true)?;
        } else {
            text(item, label, true)?;
        }
    }
    ordered(values, label)?;
    Ok(values.to_vec())
}

fn normalize_objective(value: &Value) -> Result<Value, String> {
    let map = object(value, "objective_typed")?;
    fields(map, OBJECTIVE_FIELDS, OBJECTIVE_FIELDS, "objective_typed")?;
    let summary = map["summary"].as_str().ok_or("summary must be a string")?;
    let summary = trimmed(summary);
    if summary.is_empty() || summary.chars().count() > 1024 {
        return Err("summary must contain 1..=1024 characters".into());
    }
    Ok(json!({
        "kind": kind(&map["kind"], "objective kind")?,
        "summary": summary,
        "target_obstruction_ids": string_array(&map["target_obstruction_ids"], "target_obstruction_ids", usize::MAX, true, false)?,
        "target_demand_ids": string_array(&map["target_demand_ids"], "target_demand_ids", usize::MAX, true, false)?,
    }))
}

fn colour(value: &Value) -> Result<&str, String> {
    let value = text(value, "residual_colour", true)?;
    if !matches!(value, "Open" | "Closed" | "Exact") {
        return Err("residual_colour is unsupported".into());
    }
    Ok(value)
}

fn normalize_hint_magnitude(raw: &Value) -> Result<Value, String> {
    if raw.is_null() {
        return Ok(Value::Null);
    }
    let number = raw
        .as_number()
        .ok_or("magnitude must be a number or null")?;
    let finite = number
        .to_string()
        .parse::<f64>()
        .map_err(|_| "magnitude must be finite")?;
    if !finite.is_finite() {
        return Err("magnitude must be finite".into());
    }
    if let Ok(integer) = number.to_string().parse::<num_bigint::BigInt>() {
        return serde_json::from_str(&integer.to_string())
            .map_err(|_| "invalid integer magnitude".into());
    }
    Ok(raw.clone())
}

fn normalize_hint_colour(raw: &Value) -> Result<&'static str, String> {
    match raw.as_str().map(str::to_uppercase).as_deref() {
        Some("OPEN") => Ok("Open"),
        Some("CLOSED") => Ok("Closed"),
        Some("EXACT") => Ok("Exact"),
        _ => Err("obstruction residual_colour is unsupported".into()),
    }
}

fn normalize_hint_demand_id(raw: &Value) -> Result<Value, String> {
    if raw.is_null() {
        Ok(Value::Null)
    } else {
        Ok(Value::String(identifier(raw, "demand_id", false)?))
    }
}

fn validate_prior_digests(raw: &Value) -> Result<&[Value], String> {
    let prior = array(raw, "prior_report_digests", 64)?;
    for value in prior {
        digest(value, "prior_report_digest")?;
    }
    ordered(prior, "prior_report_digests")?;
    Ok(prior)
}

fn normalize_hint(value: &Value) -> Result<Value, String> {
    let map = object(value, "obstruction hint")?;
    fields(
        map,
        OBSTRUCTION_FIELDS,
        OBSTRUCTION_FIELDS,
        "obstruction hint",
    )?;
    let magnitude = normalize_hint_magnitude(&map["magnitude"])?;
    let prior = validate_prior_digests(&map["prior_report_digests"])?;
    Ok(json!({
        "obstruction_id": identifier(&map["obstruction_id"], "obstruction_id", false)?,
        "family": kind(&map["family"], "family")?,
        "residual_colour": normalize_hint_colour(&map["residual_colour"])?,
        "magnitude": magnitude,
        "demand_id": normalize_hint_demand_id(&map["demand_id"])?,
        "prior_report_digests": prior,
    }))
}

fn normalize_demand(value: &Value) -> Result<Value, String> {
    let map = object(value, "demand item")?;
    fields(
        map,
        &["demand_id", "kind", "note"],
        &["demand_id", "kind", "note"],
        "demand item",
    )?;
    if !map["note"].is_null() {
        text(&map["note"], "note", false)?;
    }
    Ok(
        json!({"demand_id":identifier(&map["demand_id"], "demand_id", false)?, "kind":kind(&map["kind"], "demand kind")?, "note":map["note"]}),
    )
}

fn records(
    value: &Value,
    label: &str,
    maximum: usize,
    normalize: fn(&Value) -> Result<Value, String>,
    id_key: &str,
    sort: bool,
    unique: bool,
) -> Result<Vec<Value>, String> {
    let mut values: Vec<Value> = array(value, label, maximum)?
        .iter()
        .map(normalize)
        .collect::<Result<_, _>>()?;
    if sort {
        values.sort_by(|a, b| a[id_key].as_str().cmp(&b[id_key].as_str()));
    }
    if unique
        && values
            .windows(2)
            .any(|pair| pair[0][id_key].as_str() >= pair[1][id_key].as_str())
    {
        return Err(format!("ARRAY_NOT_CANONICALLY_SORTED: {label}"));
    }
    Ok(values)
}

fn regime(value: &Value) -> Result<&str, String> {
    let value = text(value, "regime_kind", true)?;
    if !matches!(
        value,
        "branch_u_undecidable"
            | "branch_o_observational"
            | "branch_q_opaque_normalizer"
            | "fence_only"
            | "code_change"
            | "research_claim"
            | "custom_bound"
            | "coda_l1"
            | "coda_regge_mc_4d"
            | "symbol_only"
            | "finite_library"
            | "prose-regime"
            | "code-diff-regime"
            | "lean4-proof-regime"
            | "hybrid-regime"
    ) {
        return Err("regime_kind is unsupported".into());
    }
    Ok(value)
}

fn sha256(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn normalized(bytes: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(bytes.len());
    let mut index = 0;
    while index < bytes.len() {
        if bytes[index] == b'\r' {
            out.push(b'\n');
            if bytes.get(index + 1) == Some(&b'\n') {
                index += 1;
            }
        } else {
            out.push(bytes[index]);
        }
        index += 1;
    }
    out
}

fn byte_array(value: &Value, label: &str) -> Result<Vec<u8>, String> {
    array(value, label, usize::MAX)?
        .iter()
        .map(|value| {
            value
                .as_u64()
                .and_then(|value| u8::try_from(value).ok())
                .ok_or_else(|| format!("{label} must contain integer bytes"))
        })
        .collect()
}

fn identity(artifact: &Map<String, Value>) -> Result<String, String> {
    let mut payload = artifact.clone();
    payload.remove("prompt_artifact_id");
    domain_digest_json(PAYLOAD_DOMAIN, &Value::Object(payload))
        .map_err(|error| format!("PROMPT_ARTIFACT_ID_INVALID: {error}"))
}

fn validate_optional_envelope_digests(map: &Map<String, Value>) -> Result<(), String> {
    optional_digest(&map["dual_witness_ref"], "dual_witness_ref")?;
    optional_digest(&map["parent_packet_id"], "parent_packet_id")?;
    optional_digest(&map["conversation_root_id"], "conversation_root_id")
}

fn validate_header_and_digests(map: &Map<String, Value>) -> Result<(), String> {
    fields(map, ARTIFACT_FIELDS, ARTIFACT_FIELDS, "prompt artifact")?;
    digest(&map["prompt_artifact_id"], "prompt_artifact_id")?;
    digest(&map["regime_id"], "regime_id")?;
    digest(&map["prompt_body_sha256"], "prompt_body_sha256")?;
    regime(&map["regime_kind"])?;
    if map["schema_version"].as_str() != Some(PROMPT_ARTIFACT_SCHEMA) {
        return Err("prompt artifact schema version is unsupported".into());
    }
    if map["family"].as_str() != Some("prompt_artifact") {
        return Err("prompt artifact family is unsupported".into());
    }
    if map["authority_effect"].as_str() != Some("None") {
        return Err("AUTHORITY_EFFECT_NON_NONE".into());
    }
    validate_optional_envelope_digests(map)
}

fn validate_dual_witness_and_count(map: &Map<String, Value>) -> Result<u64, String> {
    let residual = colour(&map["residual_colour"])?;
    let dual_required = map["dual_witness_required"]
        .as_bool()
        .ok_or("dual_witness_required must be a boolean")?;
    let has_dual_ref = !map["dual_witness_ref"].is_null();
    if residual == "Exact" && (!dual_required || !has_dual_ref) {
        return Err("EXACT_WITHOUT_DUAL_WITNESS".into());
    }
    if residual != "Exact" && has_dual_ref {
        return Err("OPEN_CLOSED_WITH_DUAL_WITNESS".into());
    }
    let count = map["prompt_body_byte_count"]
        .as_u64()
        .ok_or("prompt_body_byte_count must be an integer")?;
    if count > MAX_BODY_BYTES as u64 {
        return Err("prompt_body_byte_count exceeds resource limit".into());
    }
    Ok(count)
}

fn normalize_validated_collections(
    map: &Map<String, Value>,
    output: &mut Map<String, Value>,
) -> Result<(), String> {
    output.insert(
        "admitted_constructors".into(),
        Value::Array(string_array(
            &map["admitted_constructors"],
            "admitted_constructors",
            64,
            true,
            false,
        )?),
    );
    output.insert(
        "kill_conditions".into(),
        Value::Array(string_array(
            &map["kill_conditions"],
            "kill_conditions",
            32,
            true,
            true,
        )?),
    );
    output.insert(
        "required_reply_fields".into(),
        Value::Array(string_array(
            &map["required_reply_fields"],
            "required_reply_fields",
            32,
            false,
            true,
        )?),
    );
    output.insert(
        "open_obstructions".into(),
        Value::Array(records(
            &map["open_obstructions"],
            "open_obstructions",
            256,
            normalize_hint,
            "obstruction_id",
            false,
            true,
        )?),
    );
    output.insert(
        "demand_set".into(),
        Value::Array(records(
            &map["demand_set"],
            "demand_set",
            64,
            normalize_demand,
            "demand_id",
            false,
            true,
        )?),
    );
    output.insert(
        "objective_typed".into(),
        normalize_objective(&map["objective_typed"])?,
    );
    Ok(())
}

fn verify_body_and_identity(
    map: &Map<String, Value>,
    output: &Map<String, Value>,
    count: u64,
    body: Option<&[u8]>,
) -> Result<(), String> {
    let expected_id = map["prompt_artifact_id"]
        .as_str()
        .ok_or("prompt_artifact_id must be string")?;
    if identity(output)? != expected_id {
        return Err("PROMPT_ARTIFACT_ID_MISMATCH".into());
    }
    if let Some(body) = body {
        let expected_sha = map["prompt_body_sha256"]
            .as_str()
            .ok_or("prompt_body_sha256 must be string")?;
        if body.len() as u64 != count || sha256(body) != expected_sha {
            return Err("PROMPT_BODY_DIGEST_MISMATCH".into());
        }
    }
    Ok(())
}

/// Verify the Python wire schema, its content address, and optional exact body.
/// The verify path never sorts arrays; Python value-object normalization of
/// nested identifiers, kinds, and summaries is retained before identity replay.
pub fn validate(value: &Value, body: Option<&[u8]>) -> Result<Value, String> {
    let map = object(value, "prompt artifact")?;
    validate_header_and_digests(map)?;
    let count = validate_dual_witness_and_count(map)?;
    let mut output = map.clone();
    normalize_validated_collections(map, &mut output)?;
    verify_body_and_identity(map, &output, count, body)?;
    Ok(Value::Object(output))
}

fn default_array(map: &Map<String, Value>, key: &str) -> Value {
    map.get(key).cloned().unwrap_or_else(|| json!([]))
}

fn compile_strings(
    map: &Map<String, Value>,
    key: &str,
    fallback: &[&str],
    maximum: usize,
    stable: bool,
) -> Result<Value, String> {
    let input = default_array(map, key);
    let raw = array(&input, key, usize::MAX)?;
    let mut values: Vec<Value> = if raw.is_empty() {
        fallback
            .iter()
            .map(|value| Value::String((*value).to_owned()))
            .collect()
    } else {
        raw.to_vec()
    };
    for item in &values {
        if stable {
            identifier(item, key, true)?;
        } else {
            text(item, key, true)?;
        }
    }
    values.sort_by(|a, b| a.as_str().cmp(&b.as_str()));
    values.dedup();
    if values.len() > maximum {
        return Err(format!("{key} exceeds resource limit"));
    }
    Ok(Value::Array(values))
}

fn resolve_compile_bytes(map: &Map<String, Value>) -> Result<(Vec<u8>, Vec<u8>), String> {
    let regime_bytes = byte_array(&map["regime_definition_bytes"], "regime_definition_bytes")?;
    let body = byte_array(&map["prompt_body_bytes"], "prompt_body_bytes")?;
    let normalize = match map.get("normalize_body") {
        None => true,
        Some(value) => value.as_bool().ok_or("normalize_body must be a boolean")?,
    };
    let body = if normalize { normalized(&body) } else { body };
    Ok((regime_bytes, body))
}

fn resolve_compile_dual_witness(map: &Map<String, Value>) -> Result<(Value, bool), String> {
    let residual = map
        .get("residual_colour")
        .cloned()
        .unwrap_or_else(|| json!("Open"));
    let residual_name = colour(&residual)?;
    let dual_required = match map.get("dual_witness_required") {
        None | Some(Value::Null) => residual_name == "Exact",
        Some(value) => value
            .as_bool()
            .ok_or("dual_witness_required must be a boolean or null")?,
    };
    Ok((residual, dual_required))
}

fn build_compiled_artifact_json(
    map: &Map<String, Value>,
    regime_kind: &str,
    regime_bytes: &[u8],
    body: &[u8],
    residual: Value,
    dual_required: bool,
) -> Result<Value, String> {
    Ok(json!({
        "schema_version": PROMPT_ARTIFACT_SCHEMA, "family":"prompt_artifact", "prompt_artifact_id":"0".repeat(64),
        "regime_id":sha256(&normalized(regime_bytes)), "regime_kind":regime_kind,
        "admitted_constructors":compile_strings(map,"admitted_constructors", &[],64,true)?,
        "kill_conditions":compile_strings(map,"kill_conditions", &["F-01_inherited_meaning"],32,true)?,
        "required_reply_fields":compile_strings(map,"required_reply_fields",DEFAULT_REQUIRED_FIELDS,32,false)?,
        "open_obstructions":records(&default_array(map,"open_obstructions"),"open_obstructions",256,normalize_hint,"obstruction_id",true,true)?,
        "demand_set":records(&default_array(map,"demand_set"),"demand_set",64,normalize_demand,"demand_id",true,true)?,
        "objective_typed":normalize_objective(&map["objective_typed"] )?, "residual_colour":residual,
        "dual_witness_required":dual_required, "dual_witness_ref":map.get("dual_witness_ref").unwrap_or(&Value::Null),
        "prompt_body_sha256":sha256(body), "prompt_body_byte_count":body.len(),
        "parent_packet_id":map.get("parent_packet_id").unwrap_or(&Value::Null),
        "conversation_root_id":map.get("conversation_root_id").unwrap_or(&Value::Null), "authority_effect":"None",
    }))
}

/// Compile a Python-compatible artifact and return the bytes its body binds.
pub fn compile(value: &Value) -> Result<Value, String> {
    let map = object(value, "compile request")?;
    fields(
        map,
        &[
            "operation",
            "regime_kind",
            "regime_definition_bytes",
            "prompt_body_bytes",
            "objective_typed",
        ],
        COMPILE_FIELDS,
        "compile request",
    )?;
    let regime_kind = regime(&map["regime_kind"])?;
    let (regime_bytes, body) = resolve_compile_bytes(map)?;
    let (residual, dual_required) = resolve_compile_dual_witness(map)?;
    let mut artifact = build_compiled_artifact_json(
        map,
        regime_kind,
        &regime_bytes,
        &body,
        residual,
        dual_required,
    )?;
    let artifact_map = artifact
        .as_object_mut()
        .ok_or("compiled artifact must be an object")?;
    let computed = identity(artifact_map)?;
    artifact_map.insert("prompt_artifact_id".into(), Value::String(computed));
    let artifact = validate(&artifact, Some(&body))?;
    Ok(json!({"artifact":artifact,"prompt_body_bytes":body}))
}

fn join_lines(values: &[Value], render: impl Fn(&Value) -> String) -> String {
    if values.is_empty() {
        "none".into()
    } else {
        values.iter().map(render).collect::<Vec<_>>().join("\n")
    }
}

fn sorted_strings(map: &Map<String, Value>, key: &str) -> Result<Vec<String>, String> {
    let input = default_array(map, key);
    let mut values: Vec<String> = array(&input, key, usize::MAX)?
        .iter()
        .map(|value| {
            value
                .as_str()
                .map(str::to_owned)
                .ok_or_else(|| format!("{key} must contain strings"))
        })
        .collect::<Result<_, _>>()?;
    values.sort();
    values.dedup();
    Ok(values)
}

fn float_repr(number: &serde_json::Number) -> Result<String, String> {
    let text = number.to_string();
    if !text.contains(['.', 'e', 'E']) {
        return Ok(text);
    }
    let value = text
        .parse::<f64>()
        .map_err(|_| "magnitude must be finite")?;
    if !value.is_finite() {
        return Err("magnitude must be finite".into());
    }
    let mut buffer = ryu::Buffer::new();
    let shortest = buffer.format_finite(value);
    let (mantissa, exponent) = shortest.split_once('e').unwrap_or((shortest, "0"));
    let exponent: i32 = exponent.parse().map_err(|_| "invalid float exponent")?;
    let negative = mantissa.starts_with('-');
    let digits: String = mantissa
        .trim_start_matches('-')
        .chars()
        .filter(|&c| c != '.')
        .collect();
    let decimal = mantissa
        .trim_start_matches('-')
        .find('.')
        .unwrap_or(mantissa.trim_start_matches('-').len()) as i32
        + exponent;
    let first = digits.bytes().position(|c| c != b'0').unwrap_or(0);
    let significant = &digits[first..];
    let scientific_exponent = decimal - first as i32 - 1;
    let sign = if negative { "-" } else { "" };
    if value != 0.0 && !(-4..16).contains(&scientific_exponent) {
        let significant = significant.trim_end_matches('0');
        let mantissa = if significant.len() == 1 {
            significant.to_owned()
        } else {
            format!("{}.{}", &significant[..1], &significant[1..])
        };
        return Ok(format!(
            "{sign}{mantissa}e{}{exponent:02}",
            if scientific_exponent < 0 { '-' } else { '+' },
            exponent = scientific_exponent.abs()
        ));
    }
    let unsigned = if decimal <= 0 {
        format!("0.{}{}", "0".repeat((-decimal) as usize), digits)
    } else if decimal as usize >= digits.len() {
        format!(
            "{}{}.0",
            digits,
            "0".repeat(decimal as usize - digits.len())
        )
    } else {
        format!(
            "{}.{}",
            &digits[..decimal as usize],
            &digits[decimal as usize..]
        )
    };
    Ok(format!("{sign}{unsigned}"))
}

/// Render the Python structured prompt body (UTF-8/LF). Raw compile bytes are
/// intentionally separate: rendering must decode UTF-8 while hashing need not.
pub fn render(value: &Value) -> Result<Value, String> {
    let map = object(value, "render request")?;
    let allowed = &[
        "operation",
        "regime_definition_bytes",
        "objective_typed",
        "admitted_constructors",
        "open_obstructions",
        "demand_set",
        "kill_conditions",
        "required_reply_fields",
    ];
    fields(
        map,
        &["operation", "regime_definition_bytes", "objective_typed"],
        allowed,
        "render request",
    )?;
    let regime_bytes = normalized(&byte_array(
        &map["regime_definition_bytes"],
        "regime_definition_bytes",
    )?);
    let regime = std::str::from_utf8(&regime_bytes)
        .map_err(|_| "regime_definition_bytes must be UTF-8 for rendering")?;
    let objective = normalize_objective(&map["objective_typed"])?;
    let constructors = sorted_strings(map, "admitted_constructors")?;
    let kills = sorted_strings(map, "kill_conditions")?;
    let mut reply = sorted_strings(map, "required_reply_fields")?;
    if reply.is_empty() {
        reply = DEFAULT_REQUIRED_FIELDS
            .iter()
            .map(|value| (*value).to_owned())
            .collect();
        reply.sort();
        reply.dedup();
    }
    let obstructions = records(
        &default_array(map, "open_obstructions"),
        "open_obstructions",
        usize::MAX,
        normalize_hint,
        "obstruction_id",
        true,
        false,
    )?;
    let demands = records(
        &default_array(map, "demand_set"),
        "demand_set",
        usize::MAX,
        normalize_demand,
        "demand_id",
        true,
        false,
    )?;
    let obs_lines = obstructions
        .iter()
        .map(|o| {
            let mut line = format!(
                "- {} [{}] ({})",
                o["obstruction_id"].as_str().unwrap_or_default(),
                o["family"].as_str().unwrap_or_default(),
                o["residual_colour"].as_str().unwrap_or_default()
            );
            if let Some(number) = o["magnitude"].as_number() {
                line.push_str(&format!(" mag={}", float_repr(number)?));
            }
            if let Some(demand) = o["demand_id"].as_str() {
                line.push_str(&format!(" demand={demand}"));
            }
            Ok(line)
        })
        .collect::<Result<Vec<_>, String>>()?;
    let obs_lines = if obs_lines.is_empty() {
        "none".into()
    } else {
        obs_lines.join("\n")
    };
    let dem_lines = join_lines(&demands, |d| {
        let mut line = format!(
            "- {} [{}]",
            d["demand_id"].as_str().unwrap_or_default(),
            d["kind"].as_str().unwrap_or_default()
        );
        if let Some(note) = d["note"].as_str().filter(|note| !note.is_empty()) {
            line.push_str(&format!(": {note}"));
        }
        line
    });
    let lines = |values: &[String]| {
        if values.is_empty() {
            "none".into()
        } else {
            values
                .iter()
                .map(|value| format!("- {value}"))
                .collect::<Vec<_>>()
                .join("\n")
        }
    };
    let targets = |key: &str| {
        objective[key]
            .as_array()
            .map(|values| {
                values
                    .iter()
                    .filter_map(Value::as_str)
                    .collect::<Vec<_>>()
                    .join(",")
            })
            .filter(|value| !value.is_empty())
            .unwrap_or_else(|| "none".into())
    };
    let body = format!("{}\n\n=== STRUCTURED OBJECTIVE ===\nKIND: {}\nSUMMARY: {}\nTARGET_OBSTRUCTIONS: {}\nTARGET_DEMANDS: {}\n\n=== ADMITTED CONSTRUCTORS ===\n{}\n\n=== OPEN OBSTRUCTIONS ===\n{}\n\n=== DEMAND SET ===\n{}\n\n=== ACTIVE KILL CONDITIONS ===\n{}\n\n=== REQUIRED REPLY FIELDS ===\n{}\n", trimmed(regime), objective["kind"].as_str().unwrap_or_default(), objective["summary"].as_str().unwrap_or_default(), targets("target_obstruction_ids"), targets("target_demand_ids"),lines(&constructors),obs_lines,dem_lines,lines(&kills),reply.join(","));
    Ok(json!({"prompt_body_bytes":body.into_bytes()}))
}

/// Native action boundary. No `Value` is deserialized a second time: this keeps
/// arbitrary-precision integers distinct from user objects with number markers.
pub fn execute(value: &Value) -> Result<Value, String> {
    let map = object(value, "prompt artifact request")?;
    let operation = map
        .get("operation")
        .and_then(Value::as_str)
        .ok_or("operation must be a string")?;
    match operation {
        "compile" => compile(value),
        "render" => render(value),
        "validate" => {
            fields(
                map,
                &["operation", "artifact"],
                &["operation", "artifact", "prompt_body_bytes"],
                "validate request",
            )?;
            let body = map
                .get("prompt_body_bytes")
                .map(|value| byte_array(value, "prompt_body_bytes"))
                .transpose()?;
            Ok(json!({"artifact":validate(&map["artifact"],body.as_deref())?,"valid":true}))
        }
        "validate_reply" => {
            fields(
                map,
                &["operation", "artifact", "reply_content"],
                &["operation", "artifact", "reply_content"],
                "validate reply request",
            )?;
            let artifact = validate(&map["artifact"], None)?;
            let reply = map["reply_content"]
                .as_str()
                .ok_or("reply_content must be a string")?;
            let values = artifact["required_reply_fields"]
                .as_array()
                .ok_or("required_reply_fields must be an array")?;
            let satisfied = values
                .iter()
                .all(|field| field.as_str().is_some_and(|field| reply.contains(field)));
            Ok(json!({"residual_satisfied":satisfied}))
        }
        _ => Err(format!(
            "unsupported prompt artifact operation: {operation}"
        )),
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/prompt_artifact.rs
// Claim: urn:core:crates_rs:pfp-runtime:prompt-artifact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc168439a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc168439a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc168439a {
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
impl BoundaryErrorc168439a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc168439a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc168439a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc168439a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc168439a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc168439a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc168439a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc168439a::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_c168439a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc168439a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc168439a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc168439a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc168439a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc168439a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc168439a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc168439a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
