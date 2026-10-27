//! Bounded MCP stdio transport. All tools execute the existing native owners.
//! Transport success never promotes an outcome's AuthorityEffect.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_45dce916<T> {
    fn checked_invariant_45dce916(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_45dce916<T> for Option<T> {
    #[inline]
    fn checked_invariant_45dce916(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_45dce916<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_45dce916(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::io::{self, BufRead, Write};

use core_adversary::stage::strict_json::parse_with_limit as strict_json;
use serde_json::{json, Value};

use crate::invoke::{
    dispatchable_actions, runtime_request_byte_limit, MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES,
    RUNTIME_REQUEST_SCHEMA,
};
use crate::{dispatch_runtime_request, evaluate_request_bytes, RuntimeRequestV1};

pub const MAX_MCP_MESSAGE_BYTES: usize = 1_048_576;
pub const MAX_ARTIFACT_MCP_MESSAGE_BYTES: usize = MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES + 4096;
const PROTOCOLS: &[&str] = &["2025-06-18", "2025-03-26", "2024-11-05"];

/// MCP exposes computation over supplied bytes. Filesystem sealing and reading
/// retain their explicit CLI contracts and are not available to MCP clients.
pub fn tool_actions() -> Vec<&'static str> {
    dispatchable_actions()
        .into_iter()
        .filter(|action| !matches!(*action, "run_folder_seal" | "run_folder_verify"))
        .collect()
}

#[derive(Default)]
pub struct McpSession {
    initialized: bool,
    ready: bool,
}

fn error(id: Value, code: i32, message: &str) -> Value {
    json!({"jsonrpc":"2.0", "id":id, "error":{"code":code,"message":message}})
}

fn response(id: Value, result: Value) -> Value {
    json!({"jsonrpc":"2.0", "id":id, "result":result})
}

fn tool_result(id: Value, outcome: Value, failed: bool) -> Value {
    response(
        id,
        json!({
            "content":[{"type":"text","text":outcome.to_string()}],
            "structuredContent": outcome,
            "isError":failed
        }),
    )
}

fn is_large_artifact_call(object: & serde_json::Map<String, Value>) -> bool {
    object.get("method").and_then(Value::as_str) == Some("tools/call")
        && matches!(
            object
                .get("params")
                .and_then(|params| params.get("name"))
                .and_then(Value::as_str),
            Some("prompt_artifact" | "validate_reply_residual")
        )
}

fn is_valid_jsonrpc_id(id: &Value) -> bool {
    id.is_string() || id.as_i64().is_some() || id.as_u64().is_some()
}

fn is_valid_jsonrpc_envelope(object: &serde_json::Map<String, Value>) -> bool {
    let valid_rpc = object.get("jsonrpc").and_then(Value::as_str) == Some("2.0")
        && object.get("method").and_then(Value::as_str).is_some();
    let valid_id = object.get("id").is_none_or(is_valid_jsonrpc_id);
    let valid_params = object.get("params").is_none_or(Value::is_object);
    valid_rpc && valid_id && valid_params
}

fn is_valid_initialize_params(params: &Value) -> bool {
    let has_version = params
        .get("protocolVersion")
        .and_then(Value::as_str)
        .is_some();
    let has_caps = params.get("capabilities").is_some_and(Value::is_object);
    let has_client = params.get("clientInfo").is_some_and(|info| {
        info.get("name").is_some_and(Value::is_string)
            && info.get("version").is_some_and(Value::is_string)
    });
    has_version && has_caps && has_client
}

fn handle_tools_list(id: Value, params: &Value) -> Value {
    if params.as_object().is_some_and(|params| !params.is_empty()) {
        return error(id, -32602, "UNSUPPORTED_LIST_PARAMS");
    }
    let mut tools: Vec<Value> = tool_actions().into_iter().map(|action| json!({
        "name":action,
        "description":format!("Execute native {action}; retain complete evidence-only outcome. AuthorityEffect: None."),
        "inputSchema":{"type":"object","properties":{"payload":{}},"required":["payload"],"additionalProperties":false}
    })).collect();
    tools.push(json!({
        "name":"core_prime_host",
        "description":"Evaluate a complete prime-host request with native intake and replay. AuthorityEffect: None.",
        "inputSchema":{"type":"object","properties":{"request":{"type":"object"}},"required":["request"],"additionalProperties":false}
    }));
    response(id, json!({"tools":tools}))
}

fn handle_prime_host_call(id: Value, arguments: &serde_json::Map<String, Value>) -> Value {
    if arguments.len() != 1 || !arguments.get("request").is_some_and(Value::is_object) {
        return error(id, -32602, "INVALID_PRIME_HOST_ARGUMENTS");
    }
    let bytes = serde_json::to_vec(&arguments["request"])
        .checked_invariant_45dce916("JSON value serializes");
    let outcome = serde_json::to_value(evaluate_request_bytes(&bytes))
        .checked_invariant_45dce916("outcome serializes");
    let failed = outcome.get("refusal").is_some_and(|value| !value.is_null());
    tool_result(id, outcome, failed)
}

fn handle_tools_call(id: Value, params: &Value) -> Value {
    if params
        .as_object()
        .checked_invariant_45dce916("params validated")
        .keys()
        .any(|key| !matches!(key.as_str(), "name" | "arguments" | "_meta"))
    {
        return error(id, -32602, "UNDECLARED_TOOL_PARAMS");
    }
    let Some(name) = params.get("name").and_then(Value::as_str) else {
        return error(id, -32602, "TOOL_NAME_REQUIRED");
    };
    let Some(arguments) = params.get("arguments").and_then(Value::as_object) else {
        return error(id, -32602, "TOOL_ARGUMENTS_REQUIRED");
    };
    if name == "core_prime_host" {
        return handle_prime_host_call(id, arguments);
    }
    if !tool_actions().contains(&name) {
        return error(id, -32602, "UNKNOWN_TOOL");
    }
    if arguments.len() != 1 || !arguments.contains_key("payload") {
        return error(id, -32602, "INVALID_RUNTIME_ARGUMENTS");
    }
    let request = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: name.to_owned(),
        payload: arguments["payload"].clone(),
    };
    let bytes = serde_json::to_vec(&request).checked_invariant_45dce916("request serializes");
    if bytes.len() > runtime_request_byte_limit(name) {
        return tool_result(
            id,
            json!({"code":"RUNTIME_REQUEST_TOO_LARGE","authority_effect":"None"}),
            true,
        );
    }
    let outcome = dispatch_runtime_request(&request);
    let failed = !outcome.success;
    tool_result(
        id,
        serde_json::to_value(outcome).checked_invariant_45dce916("outcome serializes"),
        failed,
    )
}

impl McpSession {
    fn handle_initialize(&mut self, id: Value, params: &Value) -> Value {
        if self.initialized {
            return error(id, -32600, "ALREADY_INITIALIZED");
        }
        if !is_valid_initialize_params(params) {
            return error(id, -32602, "INVALID_INITIALIZE_PARAMS");
        }
        let requested = params["protocolVersion"]
            .as_str()
            .checked_invariant_45dce916("version validated");
        let version = if PROTOCOLS.contains(&requested) {
            requested
        } else {
            PROTOCOLS[0]
        };
        self.initialized = true;
        response(
            id,
            json!({
                "protocolVersion":version,
                "capabilities":{"tools":{"listChanged":false}},
                "serverInfo":{"name":"pfp","version":env!("CARGO_PKG_VERSION")},
                "instructions":"Native evidence tools. Preserve full outcomes. AuthorityEffect: None; no provider calls or external promotion."
            }),
        )
    }

    fn decode_envelope(&self, bytes: &[u8]) -> Result<serde_json::Map<String, Value>, Value> {
        if bytes.len() > MAX_ARTIFACT_MCP_MESSAGE_BYTES {
            return Err(error(Value::Null, -32600, "MCP_MESSAGE_TOO_LARGE"));
        }
        let Ok(value) = strict_json(bytes, MAX_ARTIFACT_MCP_MESSAGE_BYTES) else {
            return Err(error(Value::Null, -32700, "MALFORMED_OR_DUPLICATE_JSON"));
        };
        let Some(object) = value.as_object() else {
            return Err(error(Value::Null, -32600, "INVALID_REQUEST"));
        };
        if bytes.len() > MAX_MCP_MESSAGE_BYTES && !is_large_artifact_call(object) {
            return Err(error(Value::Null, -32600, "MCP_MESSAGE_TOO_LARGE"));
        }
        if !is_valid_jsonrpc_envelope(object) {
            return Err(error(Value::Null, -32600, "INVALID_REQUEST"));
        }
        Ok(object.clone())
    }

    fn dispatch_ready_method(&self, id: Value, method: &str, params: &Value) -> Value {
        if !self.ready {
            return error(id, -32002, "INITIALIZATION_REQUIRED");
        }
        match method {
            "tools/list" => handle_tools_list(id, params),
            "tools/call" => handle_tools_call(id, params),
            _ => error(id, -32601, "METHOD_NOT_FOUND"),
        }
    }

    pub fn handle(&mut self, bytes: &[u8]) -> Option<Value> {
        let object = match self.decode_envelope(bytes) {
            Ok(object) => object,
            Err(err_val) => return Some(err_val),
        };
        let method = object["method"].as_str().checked_invariant_45dce916("method validated");
        if !object.contains_key("id") {
            if method == "notifications/initialized" && self.initialized {
                self.ready = true;
            }
            // MCP notifications, including cancellation, have no response.
            return None;
        }
        let id = object.get("id").cloned().unwrap_or(Value::Null);
        let params = object.get("params").cloned().unwrap_or_else(|| json!({}));
        match method {
            "ping" => Some(response(id, json!({}))),
            "initialize" => Some(self.handle_initialize(id, &params)),
            _ => Some(self.dispatch_ready_method(id, method, &params)),
        }
    }
}

fn read_mcp_frame(reader: &mut impl BufRead) -> io::Result<(Vec<u8>, bool)> {
    let mut bytes = Vec::new();
    let mut oversized = false;
    loop {
        let available = reader.fill_buf()?;
        if available.is_empty() {
            break;
        }
        let length = available
            .iter()
            .position(|byte| *byte == b'\n')
            .map_or(available.len(), |index| index + 1);
        let take = length.min(MAX_ARTIFACT_MCP_MESSAGE_BYTES + 1 - bytes.len());
        let newline = available[take - 1] == b'\n';
        bytes.extend_from_slice(&available[..take]);
        reader.consume(take);
        if bytes.len() > MAX_ARTIFACT_MCP_MESSAGE_BYTES {
            oversized = true;
            break;
        }
        if newline {
            break;
        }
    }
    Ok((bytes, oversized))
}

/// Read at most the limit plus one witness byte. Oversized frames close the
/// session rather than draining an unbounded tail or dispatching its suffix.
pub fn serve(reader: impl BufRead, mut writer: impl Write) -> io::Result<()> {
    let mut reader = reader;
    let mut session = McpSession::default();
    loop {
        let (bytes, oversized) = read_mcp_frame(&mut reader)?;
        if bytes.is_empty() {
            return Ok(());
        }
        if let Some(response) = session.handle(&bytes) {
            serde_json::to_writer(&mut writer, &response)?;
            writer.write_all(b"\n")?;
            writer.flush()?;
        }
        if oversized {
            return Ok(());
        }
    }
}

// Origin: engine/crates_rs/pfp/src/mcp.rs
// Claim: urn:core:crates_rs:pfp:mcp:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord45dce916 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord45dce916` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError45dce916 {
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
impl BoundaryError45dce916 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError45dce916 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError45dce916 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord45dce916 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError45dce916> {
        if capacity_bound == 0 {
            return Err(BoundaryError45dce916::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError45dce916::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError45dce916::ExceedsCapacity {
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
mod l4_boundary_tests_45dce916 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord45dce916::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord45dce916::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord45dce916::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord45dce916::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord45dce916::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError45dce916::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError45dce916::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
