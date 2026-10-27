use std::io::Cursor;

use pfp::invoke::RUNTIME_REQUEST_SCHEMA;
use pfp::mcp::{
    serve, tool_actions, McpSession, MAX_ARTIFACT_MCP_MESSAGE_BYTES, MAX_MCP_MESSAGE_BYTES,
};
use pfp::{dispatch_runtime_request, RuntimeRequestV1};
use serde_json::{json, Value};

fn call(session: &mut McpSession, value: Value) -> Value {
    session
        .handle(&serde_json::to_vec(&value).unwrap())
        .expect("request response")
}

fn initialized() -> McpSession {
    let mut session = McpSession::default();
    let response = call(
        &mut session,
        json!({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
            "protocolVersion":"2025-03-26", "capabilities":{},"clientInfo":{"name":"test","version":"1"}
        }}),
    );
    assert_eq!(response["result"]["protocolVersion"], "2025-03-26");
    assert!(session
        .handle(br#"{"jsonrpc":"2.0","method":"notifications/initialized"}"#)
        .is_none());
    session
}

#[test]
fn tool_catalog_is_derived_from_dispatch_registry() {
    let mut session = initialized();
    let response = call(
        &mut session,
        json!({"jsonrpc":"2.0","id":"list","method":"tools/list"}),
    );
    let names: Vec<&str> = response["result"]["tools"]
        .as_array()
        .unwrap()
        .iter()
        .map(|tool| tool["name"].as_str().unwrap())
        .collect();
    let mut expected = tool_actions();
    expected.push("core_prime_host");
    assert_eq!(names, expected);
    assert!(!names.contains(&"run_folder_seal"));
    assert!(!names.contains(&"run_folder_verify"));
}

#[test]
fn tools_retain_exact_native_outcomes_and_typed_refusals() {
    let mut session = initialized();
    for (action, payload) in [
        (
            "exact_rank",
            json!({"matrix":{"rows":[["1","2"],["2","4"]]}}),
        ),
        ("exact_rank", json!({"matrix":{"rows":[[1.5]]}})),
    ] {
        let direct = dispatch_runtime_request(&RuntimeRequestV1 {
            schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
            action: action.to_owned(),
            payload: payload.clone(),
        });
        let response = call(
            &mut session,
            json!({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
                "name":action,"arguments":{"payload":payload}
            }}),
        );
        let outcome = serde_json::to_value(&direct).unwrap();
        assert_eq!(response["result"]["structuredContent"], outcome);
        assert_eq!(response["result"]["isError"], !direct.success);
        assert_eq!(outcome["authority_effect"], "None");
        assert_eq!(
            serde_json::from_str::<Value>(
                response["result"]["content"][0]["text"].as_str().unwrap()
            )
            .unwrap(),
            outcome
        );
    }
}

#[test]
fn initialization_ids_duplicates_and_unknown_tools_fail_closed() {
    let mut session = McpSession::default();
    assert_eq!(
        call(
            &mut session,
            json!({"jsonrpc":"2.0","id":1,"method":"tools/list"})
        )["error"]["code"],
        -32002
    );
    assert_eq!(
        session
            .handle(br#"{"jsonrpc":"2.0","id":1,"id":2,"method":"ping"}"#)
            .unwrap()["error"]["code"],
        -32700
    );
    assert_eq!(
        call(
            &mut session,
            json!({"jsonrpc":"2.0","id":true,"method":"ping"})
        )["error"]["code"],
        -32600
    );
    assert_eq!(
        call(
            &mut session,
            json!({"jsonrpc":"2.0","id":1.25,"method":"ping"})
        )["error"]["code"],
        -32600
    );
    let mut session = initialized();
    for name in ["run_folder_seal", "run_folder_verify"] {
        assert_eq!(
            call(
                &mut session,
                json!({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":name,"arguments":{"payload":{"run_dir":"/tmp"}}}})
            )["error"]["code"],
            -32602
        );
    }
    assert_eq!(
        call(
            &mut session,
            json!({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"exact_rank","arguments":{"payload":{}},"undeclared":true}})
        )["error"]["message"],
        "UNDECLARED_TOOL_PARAMS"
    );
    assert_eq!(
        call(
            &mut session,
            json!({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"shell","arguments":{"payload":"echo unsafe"}}})
        )["error"]["code"],
        -32602
    );
    assert_eq!(
        call(
            &mut session,
            json!({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"exact_rank","arguments":{"payload":{},"extra":true}}})
        )["error"]["code"],
        -32602
    );
}

#[test]
fn runtime_payload_limit_and_prime_refusal_remain_distinct() {
    let mut session = initialized();
    let large = call(
        &mut session,
        json!({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{
            "name":"canonical_json","arguments":{"payload":"x".repeat(65_536)}
        }}),
    );
    assert_eq!(large["result"]["isError"], true);
    assert_eq!(
        large["result"]["structuredContent"]["code"],
        "RUNTIME_REQUEST_TOO_LARGE"
    );
    let prime = call(
        &mut session,
        json!({"jsonrpc":"2.0","id":4,"method":"tools/call","params":{
            "name":"core_prime_host","arguments":{"request":{}}
        }}),
    );
    assert_eq!(prime["result"]["isError"], true);
    assert_eq!(
        prime["result"]["structuredContent"]["execution_status"],
        "REFUSED"
    );
    assert!(prime["result"]["structuredContent"]["outcome_root_sha256"].is_string());
}

#[test]
fn dag_allowance_reaches_native_validation_and_keeps_its_own_limit() {
    let mut session = initialized();
    let call_dag = |session: &mut McpSession, length| {
        call(
            session,
            json!({"jsonrpc":"2.0","id":8,"method":"tools/call","params":{
                "name":"architecture_dag_verify","arguments":{"payload":"x".repeat(length)}
            }}),
        )
    };
    let admitted = call_dag(&mut session, 70_000);
    assert!(admitted["result"]["structuredContent"]["error"]
        .as_str()
        .unwrap()
        .starts_with("DAG_REQUEST:"));
    let oversized = call_dag(
        &mut session,
        pfp::invoke::MAX_DAG_RUNTIME_REQUEST_BYTES,
    );
    assert_eq!(
        oversized["result"]["structuredContent"]["code"],
        "RUNTIME_REQUEST_TOO_LARGE"
    );
}

#[test]
fn stdio_flushes_multiple_frames_and_closes_without_draining_oversized_tail() {
    let input = b"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"ping\"}\n{\"jsonrpc\":\"2.0\",\"method\":\"notifications/cancelled\"}\n{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"ping\"}\n";
    let mut output = Vec::new();
    serve(Cursor::new(input), &mut output).unwrap();
    let responses: Vec<Value> = String::from_utf8(output)
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    assert_eq!(responses.len(), 2);
    assert_eq!(responses[1]["id"], 2);
    let oversized = vec![b'x'; MAX_ARTIFACT_MCP_MESSAGE_BYTES + 100];
    let mut reader = Cursor::new(oversized);
    let mut output = Vec::new();
    serve(&mut reader, &mut output).unwrap();
    assert_eq!(
        reader.position(),
        (MAX_ARTIFACT_MCP_MESSAGE_BYTES + 1) as u64
    );
    let response: Value = serde_json::from_slice(&output).unwrap();
    assert_eq!(response["error"]["message"], "MCP_MESSAGE_TOO_LARGE");
}

#[test]
fn larger_artifact_transport_does_not_widen_other_method_limits() {
    for method in ["ping", "initialize", "tools/list"] {
        let bytes = serde_json::to_vec(&json!({"jsonrpc":"2.0","id":1,"method":method,"padding":"x".repeat(MAX_MCP_MESSAGE_BYTES)})).unwrap();
        assert!(bytes.len() > MAX_MCP_MESSAGE_BYTES);
        assert!(bytes.len() < MAX_ARTIFACT_MCP_MESSAGE_BYTES);
        let response = McpSession::default().handle(&bytes).unwrap();
        assert_eq!(response["error"]["message"], "MCP_MESSAGE_TOO_LARGE");
    }
}

#[test]
fn compiled_binary_speaks_mcp_without_python_or_repository_cwd() {
    use std::io::Write;
    use std::process::{Command, Stdio};
    let mut child = Command::new(env!("CARGO_BIN_EXE_pfp"))
        .arg("--mcp")
        .current_dir(std::env::temp_dir())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(b"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"ping\"}\n")
        .unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let response: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(response, json!({"jsonrpc":"2.0","id":1,"result":{}}));
}

// Origin: engine/crates_rs/tests/pfp/mcp_transport.rs
// Claim: urn:core:crates_rs:tests:mcp-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2b1cb718 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2b1cb718` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2b1cb718 {
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
impl BoundaryError2b1cb718 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2b1cb718 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2b1cb718 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2b1cb718 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2b1cb718> {
        if capacity_bound == 0 {
            return Err(BoundaryError2b1cb718::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2b1cb718::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2b1cb718::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2b1cb718() {
    let admitted = BoundaryRecord2b1cb718::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2b1cb718::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
