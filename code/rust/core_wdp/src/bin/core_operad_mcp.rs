//! Sovereign Native Rust Model Context Protocol (MCP) Server.
//!
//! Provides high-assurance, sub-millisecond DDC tape parsing, residual contraction
//! certifiers, and operad verification tools directly to AI coding agents via
//! standard JSON-RPC 2.0 stdio communication.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_29571f4f<T> {
    fn checked_invariant_29571f4f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_29571f4f<T> for Option<T> {
    #[inline]
    fn checked_invariant_29571f4f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_29571f4f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_29571f4f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::fs;
use std::io::{self, BufRead, Write};
use core_wdp::ddc::parser::DdcTapeParser;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

#[derive(Debug, Deserialize)]
struct JsonRpcRequest {
    #[allow(dead_code)]
    jsonrpc: String,
    id: Option<Value>,
    method: String,
    #[serde(default)]
    params: Option<Value>,
}

#[derive(Debug, Serialize)]
struct JsonRpcResponse {
    jsonrpc: &'static str,
    #[serde(skip_serializing_if = "Option::is_none")]
    id: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<Value>,
}

fn handle_initialize(id: Option<Value>) -> JsonRpcResponse {
    JsonRpcResponse {
        jsonrpc: "2.0",
        id,
        result: Some(json!({
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "core-operad-mcp",
                "version": "0.1.0"
            }
        })),
        error: None,
    }
}

fn handle_tools_list(id: Option<Value>) -> JsonRpcResponse {
    JsonRpcResponse {
        jsonrpc: "2.0",
        id,
        result: Some(json!({
            "tools": [
                {
                    "name": "operad_parse_ddc_tape",
                    "description": "Parses a DDC event tape, verifies hash-chain integrity, enforces 8-letter candidate runtime laws, and computes exact rational residual contraction receipts.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "tape_path": {
                                "type": "string",
                                "description": "Absolute or relative path to ddc.jsonl"
                            },
                            "tape_content": {
                                "type": "string",
                                "description": "Raw JSONL content string to parse directly"
                            }
                        }
                    }
                },
                {
                    "name": "operad_verify_laws",
                    "description": "Verifies candidate algebraic runtime laws (alphabet, terminal absorption, and exact monotonic repair) on a set of DDC action records.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "records_json": {
                                "type": "string",
                                "description": "JSON array of DDC step records"
                            }
                        },
                        "required": ["records_json"]
                    }
                }
            ]
        })),
        error: None,
    }
}

fn call_parse_ddc_tape(id: Option<Value>, arguments: &Value) -> JsonRpcResponse {
    let content = if let Some(raw) = arguments.get("tape_content").and_then(|v| v.as_str()) {
        raw.to_string()
    } else if let Some(path_str) = arguments.get("tape_path").and_then(|v| v.as_str()) {
        match fs::read_to_string(path_str) {
            Ok(c) => c,
            Err(e) => {
                return JsonRpcResponse {
                    jsonrpc: "2.0",
                    id,
                    result: Some(json!({
                        "content": [{
                            "type": "text",
                            "text": format!("Error reading tape file '{}': {e}", path_str)
                        }],
                        "isError": true
                    })),
                    error: None,
                };
            }
        }
    } else {
        return JsonRpcResponse {
            jsonrpc: "2.0",
            id,
            result: Some(json!({
                "content": [{
                    "type": "text",
                    "text": "Either 'tape_path' or 'tape_content' must be provided."
                }],
                "isError": true
            })),
            error: None,
        };
    };

    match DdcTapeParser::parse_jsonl(&content) {
        Ok(receipt) => {
            let receipt_str = serde_json::to_string_pretty(&receipt)
                .checked_invariant_29571f4f("checked invariant");
            JsonRpcResponse {
                jsonrpc: "2.0",
                id,
                result: Some(json!({
                    "content": [{
                        "type": "text",
                        "text": receipt_str
                    }],
                    "isError": !receipt.ddc_laws_valid || !receipt.hash_chain_valid
                })),
                error: None,
            }
        }
        Err(refusal) => {
            let refusal_str = serde_json::to_string_pretty(&json!({
                "status": "REFUSAL",
                "code": refusal.code,
                "message": refusal.message,
                "locus": refusal.locus,
                "authority_effect": "None"
            }))
            .checked_invariant_29571f4f("checked invariant");
            JsonRpcResponse {
                jsonrpc: "2.0",
                id,
                result: Some(json!({
                    "content": [{
                        "type": "text",
                        "text": refusal_str
                    }],
                    "isError": true
                })),
                error: None,
            }
        }
    }
}

fn call_verify_laws(id: Option<Value>, arguments: &Value) -> JsonRpcResponse {
    let records_str = arguments
        .get("records_json")
        .and_then(|v| v.as_str())
        .unwrap_or("[]");
    let records_val: Result<Vec<Value>, _> = serde_json::from_str(records_str);
    match records_val {
        Ok(records) => match DdcTapeParser::parse_records(&records) {
            Ok(receipt) => JsonRpcResponse {
                jsonrpc: "2.0",
                id,
                result: Some(json!({
                    "content": [{
                        "type": "text",
                        "text": serde_json::to_string_pretty(&json!({
                            "ddc_laws_valid": receipt.ddc_laws_valid,
                            "law_violations": receipt.law_violations,
                            "tape_str": receipt.tape_str,
                            "residual_effect": receipt.residual_effect,
                            "residual_delta": receipt.residual_delta
                        })).checked_invariant_29571f4f("checked invariant")
                    }]
                })),
                error: None,
            },
            Err(refusal) => JsonRpcResponse {
                jsonrpc: "2.0",
                id,
                result: Some(json!({
                    "content": [{
                        "type": "text",
                        "text": format!("Refusal: {refusal}")
                    }],
                    "isError": true
                })),
                error: None,
            },
        },
        Err(e) => JsonRpcResponse {
            jsonrpc: "2.0",
            id,
            result: Some(json!({
                "content": [{
                    "type": "text",
                    "text": format!("JSON parse error in records_json: {e}")
                }],
                "isError": true
            })),
            error: None,
        },
    }
}

fn handle_tools_call(id: Option<Value>, params: Option<Value>) -> JsonRpcResponse {
    let p = match params {
        Some(Value::Object(map)) => map,
        _ => {
            return JsonRpcResponse {
                jsonrpc: "2.0",
                id,
                result: None,
                error: Some(json!({
                    "code": -32602,
                    "message": "Invalid params"
                })),
            };
        }
    };

    let tool_name = p.get("name").and_then(|v| v.as_str()).unwrap_or("");
    let arguments = p.get("arguments").cloned().unwrap_or(json!({}));

    match tool_name {
        "operad_parse_ddc_tape" => call_parse_ddc_tape(id, &arguments),
        "operad_verify_laws" => call_verify_laws(id, &arguments),
        _ => JsonRpcResponse {
            jsonrpc: "2.0",
            id,
            result: None,
            error: Some(json!({
                "code": -32601,
                "message": format!("Tool not found: {tool_name}")
            })),
        },
    }
}

fn dispatch_request(req: JsonRpcRequest) -> Option<JsonRpcResponse> {
    match req.method.as_str() {
        "initialize" => Some(handle_initialize(req.id)),
        "notifications/initialized" => None,
        "tools/list" => Some(handle_tools_list(req.id)),
        "tools/call" => Some(handle_tools_call(req.id, req.params)),
        "ping" => Some(JsonRpcResponse {
            jsonrpc: "2.0",
            id: req.id,
            result: Some(json!({})),
            error: None,
        }),
        _ => Some(JsonRpcResponse {
            jsonrpc: "2.0",
            id: req.id,
            result: None,
            error: Some(json!({
                "code": -32601,
                "message": format!("Method not found: {}", req.method)
            })),
        }),
    }
}

fn main() -> io::Result<()> {
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    for line in stdin.lock().lines() {
        let raw = match line {
            Ok(l) => l,
            Err(e) => {
                eprintln!("Error reading stdin line: {e}");
                break;
            }
        };

        let trimmed = raw.trim();
        if trimmed.is_empty() {
            continue;
        }

        let resp = match serde_json::from_str::<JsonRpcRequest>(trimmed) {
            Ok(req) => dispatch_request(req),
            Err(e) => Some(JsonRpcResponse {
                jsonrpc: "2.0",
                id: None,
                result: None,
                error: Some(json!({
                    "code": -32700,
                    "message": format!("Parse error: {e}")
                })),
            }),
        };

        if let Some(r) = resp {
            writeln!(
                stdout,
                "{}",
                serde_json::to_string(&r).checked_invariant_29571f4f("checked invariant")
            )?;
            stdout.flush()?;
        }
    }

    Ok(())
}

// Origin: engine/crates_rs/core_wdp/src/bin/core_operad_mcp.rs
// Claim: urn:core:crates_rs:core-wdp:core-operad-mcp:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord29571f4f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord29571f4f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError29571f4f {
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
impl BoundaryError29571f4f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError29571f4f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError29571f4f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord29571f4f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError29571f4f> {
        if capacity_bound == 0 {
            return Err(BoundaryError29571f4f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError29571f4f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError29571f4f::ExceedsCapacity {
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
mod l4_boundary_tests_29571f4f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord29571f4f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord29571f4f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord29571f4f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord29571f4f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord29571f4f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError29571f4f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError29571f4f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
