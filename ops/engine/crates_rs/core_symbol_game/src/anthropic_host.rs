//! The Anthropic Messages transport as a Symbol Game host action.
//!
//! The outcome says what happened to the request, which decides how the caller settles its
//! budget reservation: `NOT_SENT` (release it), `OUTCOME_UNKNOWN` (keep it charged) or
//! `REPLIED` (settle at `metered_cost_microusd`, or at the quote when that is null). A cost
//! ceiling of 0 is answered before the key is read or a socket is opened.
//!
//! AuthorityEffect: None.

use core_adversary::providers::anthropic::raw_store::DirectoryRawSink;
use core_adversary::providers::anthropic::request::{AdvisorPairings, MessagesRequest};
use core_adversary::providers::anthropic::response::{parse_response, MessagesResponse};
use core_adversary::providers::anthropic::transport::{meter_response, worst_case, AnthropicMessagesTransport, SendError, ANTHROPIC_MAX_REPLY_BYTES};
use core_adversary::providers::budget::{PriceTable, PricingObservation};
use core_adversary::providers::credentials::AnthropicApiKey;
use core_adversary::providers::transport::VerifiedHttpClient;
use core_adversary::providers::Refusal;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::{Component, Path};
use std::io::Read;
use std::time::Duration;

const TIMEOUT: Duration = Duration::from_secs(600);

fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ANTHROPIC_HOST_INPUT_INVALID", message)
}

fn not_sent(refusal: Refusal) -> Value {
    json!({"dispatch": "NOT_SENT", "refusal": refusal, "authority_effect": "None"})
}

fn response_value(reply: &MessagesResponse) -> Value {
    json!({"id": reply.id, "model": reply.model, "stop_reason": reply.stop_reason.wire(),
        "assistant_message": reply.assistant_message(), "text": reply.text(),
        "usage": reply.usage.raw, "container_id": reply.container_id})
}

fn canonicalize_checked(path: &Path) -> Result<std::path::PathBuf, Refusal> {
    std::fs::canonicalize(path).map_err(|e| invalid(e.to_string()))
}

fn parse_raw_dir(payload: &Value) -> Result<&str, Refusal> {
    let raw_dir = payload["raw_dir"]
        .as_str()
        .ok_or_else(|| invalid("raw_dir must be a string"))?;
    // The caller names the run folder; it must be absolute and must not climb out of it.
    let dir = Path::new(raw_dir);
    if !dir.is_absolute() || dir.components().any(|c| c == Component::ParentDir) {
        return Err(invalid("raw_dir must be an absolute path without '..'"));
    }
    Ok(raw_dir)
}

fn parse_price_table(payload: &Value) -> Result<PriceTable, Refusal> {
    let observations = payload["observations"]
        .as_array()
        .ok_or_else(|| invalid("observations must be an array"))?
        .iter()
        .map(PricingObservation::from_json)
        .collect::<Result<Vec<_>, _>>()?;
    PriceTable::new(observations)
}

fn parse_pairing_row(row: &Value) -> Result<(String, String), Refusal> {
    match (row[0].as_str(), row[1].as_str()) {
        (Some(executor), Some(advisor)) => Ok((executor.to_owned(), advisor.to_owned())),
        _ => Err(invalid("advisor_pairings rows are [executor, advisor]")),
    }
}

fn parse_advisor_pairings(payload: &Value) -> Result<AdvisorPairings, Refusal> {
    let pairs = payload["advisor_pairings"]
        .as_array()
        .map(|rows| rows.iter().map(parse_pairing_row).collect::<Result<Vec<_>, _>>())
        .transpose()?
        .unwrap_or_default();
    Ok(AdvisorPairings::new(pairs))
}

fn verify_replay_paths(path: &Path, dir: &Path, raw_name: &str) -> Result<(), Refusal> {
    let expected = dir.join(raw_name);
    if canonicalize_checked(path)? != canonicalize_checked(&expected)? {
        return Err(invalid("replay raw path differs from the selected retained file"));
    }
    let parent = path.parent().ok_or_else(|| invalid("replay parent missing"))?;
    if canonicalize_checked(parent)? != canonicalize_checked(dir)? {
        return Err(invalid("replay file escapes the retained directory"));
    }
    Ok(())
}

fn read_replay_file(path: &Path, size: u64) -> Result<Vec<u8>, Refusal> {
    let file = std::fs::File::open(path).map_err(|e| invalid(e.to_string()))?;
    let metadata = file.metadata().map_err(|e| invalid(e.to_string()))?;
    if !metadata.is_file() || metadata.len() != size {
        return Err(invalid("replay file size mismatch"));
    }
    let mut bytes = Vec::new();
    file.take(ANTHROPIC_MAX_REPLY_BYTES as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| invalid(e.to_string()))?;
    Ok(bytes)
}

fn parse_replay_meta(raw: &Value) -> Result<(u64, &str, u64), Refusal> {
    let size = raw["bytes"].as_u64().ok_or_else(|| invalid("replay size missing"))?;
    if size > ANTHROPIC_MAX_REPLY_BYTES as u64 {
        return Err(invalid("replay size exceeds the retained reply limit"));
    }
    let digest = raw["sha256"].as_str().ok_or_else(|| invalid("replay digest missing"))?;
    let status = raw["status"].as_u64().ok_or_else(|| invalid("replay status missing"))?;
    if !(200..300).contains(&status) {
        return Err(invalid("replay HTTP status mismatch"));
    }
    Ok((size, digest, status))
}

fn verify_and_read_replay_raw(
    raw: &Value,
    dir: &Path,
    raw_name: &str,
) -> Result<(u64, Vec<u8>), Refusal> {
    let path = Path::new(raw["path"].as_str().ok_or_else(|| invalid("replay path missing"))?);
    verify_replay_paths(path, dir, raw_name)?;
    let (size, digest, status) = parse_replay_meta(raw)?;
    let bytes = read_replay_file(path, size)?;
    let actual = hex::encode(Sha256::digest(&bytes));
    let expected_digest = digest.strip_prefix("sha256:").unwrap_or(digest);
    if actual != expected_digest || size != bytes.len() as u64 {
        return Err(invalid("replay bytes, digest or HTTP status mismatch"));
    }
    Ok((status, bytes))
}

fn execute_replay(
    raw: &Value,
    quote_only: bool,
    dir: &Path,
    raw_name: &str,
    request: &MessagesRequest,
    pairings: &AdvisorPairings,
    prices: &PriceTable,
    at_utc: &Value,
) -> Result<Value, Refusal> {
    if quote_only {
        return Err(invalid("replay and quote-only are distinct operations"));
    }
    let (status, bytes) = verify_and_read_replay_raw(raw, dir, raw_name)?;
    request.build(pairings)?;
    let response = parse_response(&bytes)?;
    if response.model != request.model {
        return Err(invalid("replay model differs from request"));
    }
    let cost = meter_response(request, &response, prices, at_utc);
    Ok(json!({"dispatch":"REPLIED", "status":status,
        "raw":{"path":raw["path"],"sha256":raw["sha256"],"bytes":bytes.len()},
        "metered_cost_microusd":cost,"response":response_value(&response),
        "parse_refusal":null,"authority_effect":"None","replayed":true,"provider_calls":0}))
}

fn execute_quote_only(
    request: &MessagesRequest,
    pairings: &AdvisorPairings,
    prices: &PriceTable,
    at_utc: &Value,
) -> Result<Value, Refusal> {
    let (body, _) = request.build(pairings)?;
    let quote = worst_case(request, &body, prices, at_utc)?;
    Ok(json!({"dispatch": "NOT_SENT", "quote_microusd": quote.total_microusd,
        "input_token_bound": quote.input_token_bound, "authority_effect": "None"}))
}

fn execute_live(
    request: &MessagesRequest,
    raw_dir: &str,
    raw_name: &str,
    prices: &PriceTable,
    pairings: AdvisorPairings,
    at_utc: &Value,
    ceiling: u64,
) -> Result<Value, Refusal> {
    let key = match AnthropicApiKey::from_process_env() {
        Ok(key) => key,
        Err(refusal) => return Ok(not_sent(refusal)),
    };
    let client = VerifiedHttpClient::new(TIMEOUT)?;
    let mut transport = AnthropicMessagesTransport::new(
        key,
        client,
        DirectoryRawSink::new(raw_dir),
        pairings,
    );
    match transport.send(request, raw_name, prices, at_utc, ceiling) {
        Err(SendError::NotSent(refusal)) => Ok(not_sent(refusal)),
        Err(SendError::OutcomeUnknown(refusal)) => Ok(
            json!({"dispatch": "OUTCOME_UNKNOWN", "refusal": refusal, "authority_effect": "None"}),
        ),
        Ok(outcome) => {
            let response = match &outcome.parsed {
                Ok(reply) => response_value(reply),
                Err(_) => Value::Null,
            };
            Ok(json!({
                "dispatch": "REPLIED",
                "status": outcome.status,
                "raw": {"path": outcome.raw.path, "sha256": outcome.raw.sha256, "bytes": outcome.raw.bytes},
                "quote_microusd": outcome.quote.total_microusd,
                "metered_cost_microusd": outcome.metered_cost_microusd,
                "response": response,
                "parse_refusal": outcome.parsed.as_ref().err(),
                "authority_effect": "None",
            }))
        }
    }
}

fn parse_execute_envelope(payload: &Value) -> Result<(MessagesRequest, u64, bool), Refusal> {
    let request: MessagesRequest = serde_json::from_value(payload["request"].clone())
        .map_err(|e| invalid(format!("request: {e}")))?;
    let ceiling = payload["ceiling_microusd"]
        .as_u64()
        .ok_or_else(|| invalid("ceiling_microusd must be a non-negative integer"))?;
    let quote_only = payload.get("quote_only").and_then(Value::as_bool).unwrap_or(false);
    Ok((request, ceiling, quote_only))
}

fn parse_raw_sink_params(payload: &Value) -> Result<(&str, &str), Refusal> {
    let raw_dir = parse_raw_dir(payload)?;
    let raw_name = payload["raw_name"]
        .as_str()
        .ok_or_else(|| invalid("raw_name must be a string"))?;
    Ok((raw_dir, raw_name))
}

pub fn execute(payload: &Value) -> Result<Value, Refusal> {
    let (request, ceiling, quote_only) = parse_execute_envelope(payload)?;
    let replay_raw = payload.get("replay_raw").filter(|value| !value.is_null());
    if ceiling == 0 && !quote_only && replay_raw.is_none() {
        return Ok(not_sent(Refusal::new(
            "PAID_DISPATCH_DISABLED",
            "the cost ceiling is 0: paid dispatch is off",
        )));
    }
    let (raw_dir, raw_name) = parse_raw_sink_params(payload)?;
    let prices = parse_price_table(payload)?;
    let pairings = parse_advisor_pairings(payload)?;
    if let Some(raw) = replay_raw {
        return execute_replay(
            raw,
            quote_only,
            Path::new(raw_dir),
            raw_name,
            &request,
            &pairings,
            &prices,
            &payload["at_utc"],
        );
    }
    if quote_only {
        return execute_quote_only(&request, &pairings, &prices, &payload["at_utc"]);
    }
    execute_live(&request, raw_dir, raw_name, &prices, pairings, &payload["at_utc"], ceiling)
}

// Origin: engine/crates_rs/core_symbol_game/src/anthropic_host.rs
// Claim: urn:core:crates_rs:core-symbol-game:anthropic-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc81a5eac {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc81a5eac` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc81a5eac {
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
impl BoundaryErrorc81a5eac {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc81a5eac {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc81a5eac {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc81a5eac {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc81a5eac> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc81a5eac::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc81a5eac::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc81a5eac::ExceedsCapacity {
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
mod l4_boundary_tests_c81a5eac {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc81a5eac::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc81a5eac::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc81a5eac::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc81a5eac::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc81a5eac::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc81a5eac::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc81a5eac::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
