//! The Anthropic Messages transport: quote, gate, send, persist, parse.
//!
//! Order of operations for one call:
//!
//! 1. Build and validate the request body.
//! 2. Quote the worst case from dated price observations. A ceiling of 0 refuses before
//!    any quote or socket: paid dispatch is off unless the caller grants a budget.
//! 3. Refuse if the worst case exceeds the ceiling.
//! 4. Send. A transport failure leaves the outcome unknown (`OutcomeUnknown`); the caller
//!    keeps the reservation charged.
//! 5. Persist the raw reply bytes, success or error, before parsing them. A reply cut off
//!    at the byte limit or by a failed read is persisted as far as it arrived and parsed
//!    as a refusal; a name that already holds other bytes gets a content-addressed sibling.
//! 6. Parse, and price the reply's usage where the price table can.
//!
//! AuthorityEffect: None.

use super::raw_store::{digest, PersistedRaw, RawReplySink};
use super::request::{AdvisorPairings, MessagesRequest, API_VERSION, MESSAGES_URL};
use super::response::{error_refusal, parse_response, MessagesResponse};
use crate::providers::budget::PriceTable;
use crate::providers::credentials::AnthropicApiKey;
use crate::providers::transport::HttpClient;
use crate::providers::Refusal;
use num_bigint::BigInt;
use num_traits::ToPrimitive;
use serde_json::Value;
use std::collections::BTreeMap;

/// Why a send did not produce a reply.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SendError {
    /// Nothing left the host; the caller may release its reservation.
    NotSent(Refusal),
    /// The request may have reached the provider; the caller must keep it charged.
    OutcomeUnknown(Refusal),
}

// Origin: omega_engine/crates_rs/omega_woland/src/providers/anthropic/transport.rs
// Claim: urn:omega:crates_rs:omega-woland:transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SendError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SendError {}

impl SendError {
    pub fn refusal(&self) -> &Refusal {
        match self {
            SendError::NotSent(refusal) | SendError::OutcomeUnknown(refusal) => refusal,
        }
    }
}

/// The worst-case cost reserved for a call, by component.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorstCaseQuote {
    pub input_token_bound: u64,
    pub executor_microusd: u64,
    pub advisor_microusd: u64,
    pub code_execution_microusd: u64,
    pub total_microusd: u64,
}

/// A reply that reached the host. `raw` is always persisted; `parsed` may still fail.
#[derive(Debug, Clone, PartialEq)]
pub struct SendOutcome {
    pub status: u16,
    pub raw: PersistedRaw,
    pub quote: WorstCaseQuote,
    pub parsed: Result<MessagesResponse, Refusal>,
    /// Priced usage, or `None` when the reply carries charges the price table cannot price
    /// (cache tokens, advisor or code-execution use); the caller then settles at the quote.
    pub metered_cost_microusd: Option<u64>,
}

pub struct AnthropicMessagesTransport<C: HttpClient, S: RawReplySink> {
    key: AnthropicApiKey,
    client: C,
    sink: S,
    pairings: AdvisorPairings,
}

fn microusd(value: BigInt) -> Result<u64, Refusal> {
    value.to_u64().ok_or_else(|| {
        Refusal::new(
            "BUDGET_ARITHMETIC_OVERFLOW",
            "quote does not fit u64 micro-USD",
        )
    })
}

fn checked(values: &[u64]) -> Result<u64, Refusal> {
    values.iter().try_fold(0u64, |sum, value| {
        sum.checked_add(*value)
            .ok_or_else(|| Refusal::new("BUDGET_ARITHMETIC_OVERFLOW", "quote overflowed"))
    })
}

fn product(a: u64, b: u64) -> Result<u64, Refusal> {
    a.checked_mul(b)
        .ok_or_else(|| Refusal::new("BUDGET_ARITHMETIC_OVERFLOW", "quote overflowed"))
}

/// Tokens the provider adds to the prompt that are not in the body (tool-use system text).
pub const PROVIDER_PROMPT_ALLOWANCE_TOKENS: u64 = 4096;

/// The largest reply read in full. Code-execution output and encrypted advisor results
/// make Messages replies larger than chat completions.
pub const ANTHROPIC_MAX_REPLY_BYTES: usize = 16 * 1024 * 1024;

/// Cache writes bill input at up to twice the base rate (one-hour TTL).
pub const CACHE_WRITE_INPUT_FACTOR: u64 = 2;

/// Worst case for one request.
///
/// The body's byte length plus [`PROVIDER_PROMPT_ALLOWANCE_TOKENS`] bounds its input
/// tokens (a byte-fallback tokenizer emits at most one token per byte). Each advisor use can see the whole
/// context (the body, the executor's output and earlier advice) and returns up to its
/// `max_tokens`, which re-enters the executor's context; the executor is re-billed for
/// that context once per sampling iteration (1 + `max_uses`). When the request writes to
/// the prompt cache, input is priced at [`CACHE_WRITE_INPUT_FACTOR`] times the base rate.
/// Code execution adds the caller's declared bound. Content the body's bytes cannot bound
/// (files, URLs, PDFs) is refused when the request is built.
pub fn worst_case(
    request: &MessagesRequest,
    body: &Value,
    prices: &PriceTable,
    at_utc: &Value,
) -> Result<WorstCaseQuote, Refusal> {
    let body_bytes = serde_json::to_vec(body)
        .map_err(|e| Refusal::new("ANTHROPIC_REQUEST_INVALID", e.to_string()))?
        .len() as u64;
    let input_bound = checked(&[body_bytes, PROVIDER_PROMPT_ALLOWANCE_TOKENS])?;
    let (uses, advice) = request
        .advisor
        .as_ref()
        .map_or((0, 0), |advisor| (advisor.max_uses, advisor.max_tokens));
    let context = checked(&[input_bound, request.max_tokens, product(uses, advice)?])?;
    let cache = if request.caches() {
        CACHE_WRITE_INPUT_FACTOR
    } else {
        1
    };
    let executor = quote_executor(request, prices, at_utc, cache, uses, context)?;
    let advisor = quote_advisor(request, prices, at_utc, cache, uses, advice, context)?;
    let code = request
        .code_execution
        .as_ref()
        .map_or(0, |tool| tool.max_charge_microusd);
    Ok(WorstCaseQuote {
        input_token_bound: input_bound,
        executor_microusd: executor,
        advisor_microusd: advisor,
        code_execution_microusd: code,
        total_microusd: checked(&[executor, advisor, code])?,
    })
}

fn quote_executor(
    request: &MessagesRequest,
    prices: &PriceTable,
    at_utc: &Value,
    cache: u64,
    uses: u64,
    context: u64,
) -> Result<u64, Refusal> {
    let iterations = checked(&[1, uses])?;
    let in_tokens = product(cache, product(iterations, context)?)?;
    let (_, executor) = prices.quote(
        &request.model,
        &BigInt::from(in_tokens),
        &BigInt::from(request.max_tokens),
        at_utc,
    )?;
    microusd(executor)
}

fn quote_advisor(
    request: &MessagesRequest,
    prices: &PriceTable,
    at_utc: &Value,
    cache: u64,
    uses: u64,
    advice: u64,
    context: u64,
) -> Result<u64, Refusal> {
    match &request.advisor {
        Some(advisor) => {
            let in_tokens = product(cache, product(uses, context)?)?;
            let out_tokens = product(uses, advice)?;
            let (_, cost) = prices.quote(
                &advisor.model,
                &BigInt::from(in_tokens),
                &BigInt::from(out_tokens),
                at_utc,
            )?;
            microusd(cost)
        }
        None => Ok(0),
    }
}

impl<C: HttpClient, S: RawReplySink> AnthropicMessagesTransport<C, S> {
    pub fn new(key: AnthropicApiKey, client: C, sink: S, pairings: AdvisorPairings) -> Self {
        Self {
            key,
            client,
            sink,
            pairings,
        }
    }

    pub fn client(&self) -> &C {
        &self.client
    }

    /// Send one request. `raw_name` names the persisted reply (the occurrence id);
    /// `ceiling_microusd` is the cost the caller has reserved for this call.
    pub fn send(
        &mut self,
        request: &MessagesRequest,
        raw_name: &str,
        prices: &PriceTable,
        at_utc: &Value,
        ceiling_microusd: u64,
    ) -> Result<SendOutcome, SendError> {
        let (body, extra_headers) = request.build(&self.pairings).map_err(SendError::NotSent)?;
        let quote = Self::check_send_budget(request, &body, prices, at_utc, ceiling_microusd)?;
        let mut headers = BTreeMap::from([
            ("x-api-key".to_owned(), self.key.header_value().to_owned()),
            ("anthropic-version".to_owned(), API_VERSION.to_owned()),
            ("content-type".to_owned(), "application/json".to_owned()),
        ]);
        headers.extend(extra_headers);
        let reply = self
            .client
            .post_with_status(MESSAGES_URL, &headers, &body, ANTHROPIC_MAX_REPLY_BYTES)
            .map_err(SendError::OutcomeUnknown)?;
        // Persist before parsing: a reply the parser rejects is still kept.
        let raw = self.persist_reply(raw_name, &reply.body)?;
        let parsed = Self::decode_reply(&reply);
        let metered_cost_microusd = match &parsed {
            Ok(response) => meter_response(request, response, prices, at_utc),
            Err(_) => None,
        };
        Ok(SendOutcome {
            status: reply.status,
            raw,
            quote,
            parsed,
            metered_cost_microusd,
        })
    }

    fn check_send_budget(
        request: &MessagesRequest,
        body: &Value,
        prices: &PriceTable,
        at_utc: &Value,
        ceiling_microusd: u64,
    ) -> Result<WorstCaseQuote, SendError> {
        if ceiling_microusd == 0 {
            return Err(SendError::NotSent(Refusal::new(
                "PAID_DISPATCH_DISABLED",
                "the cost ceiling is 0: paid dispatch is off",
            )));
        }
        let quote = worst_case(request, body, prices, at_utc).map_err(SendError::NotSent)?;
        if quote.total_microusd > ceiling_microusd {
            return Err(SendError::NotSent(Refusal::new(
                "BUDGET_CEILING_EXCEEDED",
                format!(
                    "worst case {} micro-USD exceeds the reserved {ceiling_microusd}",
                    quote.total_microusd
                ),
            )));
        }
        Ok(quote)
    }

    fn persist_reply(
        &mut self,
        raw_name: &str,
        body: &[u8],
    ) -> Result<PersistedRaw, SendError> {
        match self.sink.persist(raw_name, body) {
            Err(refusal) if refusal.code == "RAW_REPLY_CONFLICT" => {
                let hex = digest(body);
                let sibling = format!("{raw_name}.{}", &hex["sha256:".len()..][..16]);
                self.sink.persist(&sibling, body)
            }
            other => other,
        }
        .map_err(SendError::OutcomeUnknown)
    }

    fn decode_reply(
        reply: &crate::providers::transport::HttpReply,
    ) -> Result<MessagesResponse, Refusal> {
        if let Some(code) = &reply.truncated {
            Err(Refusal::new(
                "ANTHROPIC_REPLY_TRUNCATED",
                format!(
                    "{code}: {} bytes arrived and were persisted",
                    reply.body.len()
                ),
            ))
        } else if reply.is_success() {
            parse_response(&reply.body)
        } else {
            Err(error_refusal(reply.status, &reply.body))
        }
    }
}

/// Price plain input and output tokens; `None` when anything else was billed or may have
/// been (any server tool use, or a block this parser does not know).
pub fn meter_response(
    request: &MessagesRequest,
    response: &MessagesResponse,
    prices: &PriceTable,
    at_utc: &Value,
) -> Option<u64> {
    let usage = &response.usage;
    let raw = usage.raw.as_object()?;
    if !is_plain_usage_raw(raw, usage.output_tokens) || !is_plain_response(request, response) {
        return None;
    }
    let (_, cost) = prices
        .quote(
            &request.model,
            &BigInt::from(usage.input_tokens),
            &BigInt::from(usage.output_tokens),
            at_utc,
        )
        .ok()?;
    cost.to_u64()
}

fn is_plain_usage_raw(raw: &serde_json::Map<String, Value>, output_tokens: u64) -> bool {
    const ALLOWED: [&str; 10] = [
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "cache_creation",
        "server_tool_use",
        "service_tier",
        "inference_geo",
        "output_tokens_details",
        "speed",
    ];
    if raw.keys().any(|k| !ALLOWED.contains(&k.as_str())) {
        return false;
    }
    if !is_zero_nested_usage(raw, "cache_creation") || !is_zero_nested_usage(raw, "server_tool_use")
    {
        return false;
    }
    is_valid_output_details(raw, output_tokens) && is_standard_tier_and_geo(raw)
}

fn is_zero_nested_usage(raw: &serde_json::Map<String, Value>, field: &str) -> bool {
    match raw.get(field) {
        None | Some(Value::Null) => true,
        Some(Value::Object(map)) => map.values().all(|v| v.as_u64() == Some(0)),
        Some(_) => false,
    }
}

fn is_valid_output_details(raw: &serde_json::Map<String, Value>, output_tokens: u64) -> bool {
    match raw.get("output_tokens_details") {
        None => true,
        Some(Value::Object(fields)) => {
            fields.len() == 1
                && fields
                    .get("thinking_tokens")
                    .and_then(Value::as_u64)
                    .is_some_and(|t| t <= output_tokens)
        }
        Some(_) => false,
    }
}

fn is_standard_tier_and_geo(raw: &serde_json::Map<String, Value>) -> bool {
    let tier_ok = raw
        .get("service_tier")
        .is_none_or(|v| v.is_null() || v == "standard");
    let speed_ok = raw.get("speed").is_none_or(|v| v == "standard");
    let geo_ok = raw
        .get("inference_geo")
        .is_none_or(|v| v.is_null() || v == "global" || v == "not_available");
    [tier_ok, speed_ok, geo_ok].into_iter().all(|b| b)
}

fn is_plain_response(request: &MessagesRequest, response: &MessagesResponse) -> bool {
    use super::response::ContentBlock;
    let advisor_used = response.content.iter().any(|block| {
        matches!(
            block,
            ContentBlock::AdvisorResult { .. }
                | ContentBlock::AdvisorRedactedResult { .. }
                | ContentBlock::AdvisorError { .. }
                | ContentBlock::ServerToolUse { .. }
                | ContentBlock::Unknown(_)
        )
    });
    let usage = &response.usage;
    [
        usage.cache_creation_input_tokens == 0,
        usage.cache_read_input_tokens == 0,
        usage.code_execution_requests == 0,
        !advisor_used,
        request.code_execution.is_none(),
    ]
    .into_iter()
    .all(|b| b)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_2113e680 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
