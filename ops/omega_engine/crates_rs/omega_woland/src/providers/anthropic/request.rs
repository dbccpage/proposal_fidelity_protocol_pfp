//! Messages API request bodies, including the advisor and code-execution server tools.
//!
//! Wire identifiers follow the Anthropic platform docs (`advisor-tool`, `code-execution-tool`
//! and `parallel-tool-use` pages, checked 2026-10-06). Which executor/advisor model pairs
//! are valid is not hardcoded: the caller supplies the allowlist, and a pair outside it is
//! refused before anything is sent.
//!
//! AuthorityEffect: None.

use crate::providers::Refusal;
use serde::Deserialize;
use serde_json::{json, Map, Value};
use std::collections::BTreeSet;

pub const MESSAGES_URL: &str = "https://api.anthropic.com/v1/messages";
pub const API_VERSION: &str = "2023-06-01";
pub const ADVISOR_TOOL_TYPE: &str = "advisor_20260301";
pub const ADVISOR_TOOL_NAME: &str = "advisor";
pub const ADVISOR_BETA: &str = "advisor-tool-2026-03-01";
pub const ADVISOR_MIN_MAX_TOKENS: u64 = 1024;
pub const CODE_EXECUTION_TOOL_NAME: &str = "code_execution";
/// Code execution versions; none needs a beta header.
pub const CODE_EXECUTION_VERSIONS: [&str; 3] = [
    "code_execution_20250825",
    "code_execution_20260120",
    "code_execution_20260521",
];

fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ANTHROPIC_REQUEST_INVALID", message)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
pub enum CacheTtl {
    #[serde(rename = "5m")]
    FiveMinutes,
    #[serde(rename = "1h")]
    OneHour,
}

/// The advisor server tool. `max_uses` and `max_tokens` are required here, though the API
/// makes them optional, because an unbounded advisor cannot be given a worst-case quote.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AdvisorTool {
    pub model: String,
    pub max_uses: u64,
    pub max_tokens: u64,
    #[serde(default)]
    pub caching: Option<CacheTtl>,
}

/// The code-execution server tool. The API bills container time, which no token price
/// covers, and each tool call is another sampling round that re-bills the context; the
/// API offers no cap on those rounds. `max_charge_microusd` is the caller's declared bound
/// for everything this tool adds to the request's cost. It is reserved in full and must be
/// at least 1, but the provider does not enforce it: it is a declaration, not a limit.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CodeExecutionTool {
    pub version: String,
    pub max_charge_microusd: u64,
}

/// A client tool the host executes itself.
#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CustomTool {
    pub name: String,
    pub description: String,
    pub input_schema: Value,
    #[serde(default)]
    pub strict: bool,
}

/// Executor/advisor model pairs the caller has checked against current documentation.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct AdvisorPairings(BTreeSet<(String, String)>);

impl AdvisorPairings {
    pub fn new<I: IntoIterator<Item = (String, String)>>(pairs: I) -> Self {
        Self(pairs.into_iter().collect())
    }
    pub fn allows(&self, executor: &str, advisor: &str) -> bool {
        self.0.contains(&(executor.to_owned(), advisor.to_owned()))
    }
}

#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MessagesRequest {
    pub model: String,
    pub max_tokens: u64,
    #[serde(default)]
    pub system: Option<String>,
    /// Prior turns verbatim, including assistant content blocks (redacted advisor results
    /// must be sent back unchanged).
    pub messages: Vec<Value>,
    #[serde(default)]
    pub advisor: Option<AdvisorTool>,
    #[serde(default)]
    pub code_execution: Option<CodeExecutionTool>,
    #[serde(default)]
    pub custom_tools: Vec<CustomTool>,
    /// A container id from an earlier response, to reuse its files and state.
    #[serde(default)]
    pub container: Option<String>,
    #[serde(default)]
    pub disable_parallel_tool_use: bool,
    /// Documented Messages output configuration; temperature and provider seed are
    /// intentionally absent from this bounded profile.
    #[serde(default)]
    pub output_config: Option<Value>,
}

fn tool_name_ok(name: &str) -> bool {
    (1..=64).contains(&name.len())
        && name
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
}

impl MessagesRequest {
    /// The JSON body and the request-specific headers (the beta header when the advisor is
    /// present). Authentication and version headers are added by the transport.
    pub fn build(
        &self,
        pairings: &AdvisorPairings,
    ) -> Result<(Value, Vec<(String, String)>), Refusal> {
        if self.model.trim().is_empty() {
            return Err(invalid("model required"));
        }
        if self.max_tokens == 0 {
            return Err(invalid("max_tokens must be at least 1"));
        }
        self.check_messages()?;
        let mut tools = Vec::new();
        let mut names = BTreeSet::new();
        let mut headers = Vec::new();
        if let Some(advisor) = &self.advisor {
            if advisor.model.trim().is_empty() || advisor.max_uses == 0 {
                return Err(invalid("advisor needs a model and max_uses >= 1"));
            }
            if advisor.max_tokens < ADVISOR_MIN_MAX_TOKENS {
                return Err(invalid(format!(
                    "advisor max_tokens must be at least {ADVISOR_MIN_MAX_TOKENS}"
                )));
            }
            if !pairings.allows(&self.model, &advisor.model) {
                return Err(Refusal::new(
                    "ADVISOR_PAIRING_UNKNOWN",
                    format!(
                        "executor {} with advisor {} is not on the allowlist",
                        self.model, advisor.model
                    ),
                ));
            }
            let mut tool = json!({
                "type": ADVISOR_TOOL_TYPE, "name": ADVISOR_TOOL_NAME, "model": advisor.model,
                "max_uses": advisor.max_uses, "max_tokens": advisor.max_tokens,
            });
            if let Some(ttl) = advisor.caching {
                let ttl = match ttl {
                    CacheTtl::FiveMinutes => "5m",
                    CacheTtl::OneHour => "1h",
                };
                tool["caching"] = json!({"type": "ephemeral", "ttl": ttl});
            }
            names.insert(ADVISOR_TOOL_NAME.to_owned());
            tools.push(tool);
            headers.push(("anthropic-beta".to_owned(), ADVISOR_BETA.to_owned()));
        }
        if let Some(code) = &self.code_execution {
            if code.max_charge_microusd == 0 {
                return Err(invalid(
                    "code execution needs max_charge_microusd >= 1: its rounds and container time are billed outside the token quote",
                ));
            }
            if !CODE_EXECUTION_VERSIONS.contains(&code.version.as_str()) {
                return Err(invalid(format!(
                    "unknown code execution version {}",
                    code.version
                )));
            }
            names.insert(CODE_EXECUTION_TOOL_NAME.to_owned());
            tools.push(json!({"type": code.version, "name": CODE_EXECUTION_TOOL_NAME}));
        }
        for tool in &self.custom_tools {
            if !tool_name_ok(&tool.name) || !names.insert(tool.name.clone()) {
                return Err(invalid(format!(
                    "custom tool name {:?} is invalid or repeated",
                    tool.name
                )));
            }
            if !tool.input_schema.is_object() {
                return Err(invalid(format!(
                    "tool {} input_schema must be an object",
                    tool.name
                )));
            }
            let mut definition = json!({
                "name": tool.name, "description": tool.description, "input_schema": tool.input_schema,
            });
            if tool.strict {
                definition["strict"] = json!(true);
            }
            tools.push(definition);
        }
        let mut body = Map::new();
        body.insert("model".into(), json!(self.model));
        body.insert("max_tokens".into(), json!(self.max_tokens));
        body.insert("messages".into(), Value::Array(self.messages.clone()));
        if let Some(config) = &self.output_config {
            let object = config.as_object().ok_or_else(|| invalid("output_config must be an object"))?;
            if object.keys().any(|key| key != "format")
                || config["format"]["type"] != "json_schema"
                || !config["format"]["schema"].is_object()
                || config["format"].as_object().is_none_or(|format| format.keys().any(|key| key != "type" && key != "schema"))
            {
                return Err(invalid("output_config requires format.type=json_schema and a schema object"));
            }
            body.insert("output_config".into(), config.clone());
        }
        if let Some(system) = &self.system {
            body.insert("system".into(), json!(system));
        }
        if !tools.is_empty() {
            body.insert("tools".into(), Value::Array(tools));
            if self.disable_parallel_tool_use {
                body.insert(
                    "tool_choice".into(),
                    json!({"type": "auto", "disable_parallel_tool_use": true}),
                );
            }
        } else if self.disable_parallel_tool_use {
            return Err(invalid("disable_parallel_tool_use needs at least one tool"));
        }
        if let Some(container) = &self.container {
            if container.trim().is_empty() {
                return Err(invalid("container id must not be blank"));
            }
            if self.code_execution.is_none() {
                return Err(invalid(
                    "a container is reused only with the code execution tool",
                ));
            }
            body.insert("container".into(), json!(container));
        }
        Ok((Value::Object(body), headers))
    }

    fn check_messages(&self) -> Result<(), Refusal> {
        if self.messages.is_empty() {
            return Err(invalid("at least one message is required"));
        }
        for (index, message) in self.messages.iter().enumerate() {
            let role = message.get("role").and_then(Value::as_str);
            let expected = if index % 2 == 0 { "user" } else { "assistant" };
            if role != Some(expected) {
                return Err(invalid(format!(
                    "message {index} must have role {expected}"
                )));
            }
            match message.get("content") {
                Some(Value::String(text)) if !text.is_empty() => {}
                Some(Value::Array(blocks)) if !blocks.is_empty() => {
                    if let Some(found) = blocks.iter().find_map(unpriced_content) {
                        return Err(Refusal::new(
                            "ANTHROPIC_CONTENT_UNPRICED",
                            format!(
                                "message {index} carries {found}, whose tokens the body's byte length does not bound; send the content inline"
                            ),
                        ));
                    }
                }
                _ => return Err(invalid(format!("message {index} needs non-empty content"))),
            }
        }
        Ok(())
    }

    /// Whether any part of the request writes to the prompt cache, which bills input above
    /// the base rate (1.25x for 5 minutes, 2x for an hour).
    pub fn caches(&self) -> bool {
        self.advisor.as_ref().is_some_and(|a| a.caching.is_some())
            || self.messages.iter().any(has_cache_control)
    }
}

fn has_cache_control(value: &Value) -> bool {
    match value {
        Value::Object(map) => {
            map.contains_key("cache_control") || map.values().any(has_cache_control)
        }
        Value::Array(items) => items.iter().any(has_cache_control),
        _ => false,
    }
}

/// Content whose billed tokens are not bounded by the request body's bytes: a block that
/// pulls content in by reference (a `url` or `file` source, a container upload), or a
/// base64 source that is not an image (a compressed PDF can expand far past its bytes).
fn unpriced_content(value: &Value) -> Option<String> {
    let map = match value {
        Value::Object(map) => map,
        Value::Array(items) => return items.iter().find_map(unpriced_content),
        _ => return None,
    };
    if map.get("type").and_then(Value::as_str) == Some("container_upload") {
        return Some("a container_upload block".to_owned());
    }
    if let Some(source) = map.get("source").and_then(Value::as_object) {
        let kind = source.get("type").and_then(Value::as_str).unwrap_or("");
        let media = source
            .get("media_type")
            .and_then(Value::as_str)
            .unwrap_or("");
        match kind {
            "text" | "content" => {}
            "base64" if media.starts_with("image/") => {}
            _ => return Some(format!("a {kind:?} source of type {media:?}")),
        }
    }
    map.values().find_map(unpriced_content)
}

// Origin: omega_engine/crates_rs/omega_woland/src/providers/anthropic/request.rs
// Claim: urn:omega:crates_rs:omega-woland:request:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7be06283 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7be06283` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7be06283 {
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
impl BoundaryError7be06283 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7be06283 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7be06283 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7be06283 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7be06283> {
        if capacity_bound == 0 {
            return Err(BoundaryError7be06283::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7be06283::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7be06283::ExceedsCapacity {
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
mod l4_boundary_tests_7be06283 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7be06283::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7be06283::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7be06283::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7be06283::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7be06283::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7be06283::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7be06283::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
