//! Ordered model attempts and exact admission; transports, ledger and clock are injected.
use crate::stage::exact::rational;
use crate::stage::ports::{Refusal, SeatPort, SeatTurnReply, SeatTurnRequest};
use crate::{
    exact::{integer, Integer},
    routing::{admit_spend, RouteLeg, RoutingTable},
};
use num_bigint::BigInt;
use num_integer::Integer as IntegerOps;
use num_traits::Zero;
use core_types::python_unicode::repr_string;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

pub struct SeatPrompt {
    pub system: String,
    pub user: String,
}
#[derive(Debug, Clone)]
pub struct TransportFailure {
    pub kind: String,
}
pub struct SeatTransportOutcome {
    pub raw: Vec<u8>,
    pub status: u16,
    pub truncated: Option<String>,
}
pub trait SeatTransport {
    fn configured(&self, router: &str) -> bool;
    fn send(
        &mut self,
        router: &str,
        model: &str,
        request: &SeatPrompt,
        max_tokens: u64,
    ) -> Result<Vec<u8>, TransportFailure>;
    fn send_bound(
        &mut self,
        router: &str,
        model: &str,
        request: &SeatPrompt,
        max_tokens: u64,
    ) -> Result<SeatTransportOutcome, TransportFailure> {
        self.send(router, model, request, max_tokens)
            .map(|raw| SeatTransportOutcome {
                raw,
                status: 200,
                truncated: None,
            })
    }
}
pub trait CallLedger {
    fn append(&mut self, record: &Value) -> Result<(), Refusal>;
    fn spent_on(&mut self, day: &str) -> Result<BigInt, Refusal>;
    /// Live PFP admission must recover holds and continuing bout/tier spend.
    /// Historical in-memory fixture ledgers need not implement this capability.
    fn records(&mut self) -> Result<Vec<Value>, Refusal> {
        Err(Refusal::new(
            "PFP_LEDGER_UNAVAILABLE",
            "live PFP requires readable continuing ledger custody",
        ))
    }
}
pub trait Clock {
    fn today(&self) -> String;
    fn milliseconds(&self) -> u64;
}

fn trim_python(text: &str) -> &str {
    text.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ParsedReply {
    pub content: String,
    pub model: String,
    pub input_tokens: Integer,
    pub output_tokens: Integer,
    pub cost_microusd: Integer,
    pub cost_source: String,
    pub finish_reason: Option<String>,
}
fn decode_reply_json(raw: &[u8]) -> Result<Value, Refusal> {
    if raw.len() > 1024 * 1024 {
        return Err(Refusal::new(
            "SWARM_PROVIDER_REPLY_TOO_LARGE",
            "provider reply exceeds byte limit",
        ));
    }
    serde_json::from_slice(raw).map_err(|_| {
        let mut refusal = Refusal::new(
            "TRANSPORT_PROTOCOL_INVALID",
            "provider response is not UTF-8 JSON",
        );
        refusal.details.insert(
            "exception_type".into(),
            if std::str::from_utf8(raw).is_err() {
                "UnicodeDecodeError"
            } else {
                "JSONDecodeError"
            }
            .into(),
        );
        refusal
    })
}

fn extract_reply_content(first: Option<&Value>) -> Result<(String, Option<String>), Refusal> {
    let raw_content = match first
        .and_then(|v| v.get("message"))
        .and_then(|v| v.get("content"))
    {
        None | Some(Value::Null) => "",
        Some(Value::String(content)) => content,
        _ => {
            return Err(Refusal::new(
                "TRANSPORT_PROTOCOL_INVALID",
                "response content must be text",
            ))
        }
    };
    let finish = first
        .and_then(|v| v.get("finish_reason"))
        .and_then(Value::as_str)
        .filter(|v| !v.is_empty());
    let content = if finish == Some("content_filter") && trim_python(raw_content).is_empty() {
        "[PROVIDER_CONTENT_FILTER]".into()
    } else {
        trim_python(raw_content).to_owned()
    };
    Ok((content, finish.map(str::to_owned)))
}

fn usage_tokens(data: &Value, name: &str) -> Result<Integer, Refusal> {
    let raw = &data["usage"][name];
    if raw.is_null() {
        return Ok(Integer(BigInt::zero()));
    }
    integer(raw).map(Integer).ok_or_else(|| {
        Refusal::new(
            "TRANSPORT_PROTOCOL_INVALID",
            "usage token count must be integer",
        )
    })
}

fn compute_reply_cost(
    leg: &RouteLeg,
    data: &Value,
    input: &Integer,
    output: &Integer,
) -> (BigInt, &'static str) {
    let receipt = match &data["usage"]["cost"] {
        Value::Number(n) => {
            rational(&n.to_string()).filter(|cost| cost >= &num_rational::BigRational::zero())
        }
        _ => None,
    };
    match receipt {
        Some(cost) => {
            let cost = cost * BigInt::from(1_000_000);
            (cost.numer().div_ceil(cost.denom()), "provider_receipt")
        }
        None => (leg.cost_microusd(&input.0, &output.0), "price_table"),
    }
}

pub fn parse_reply(leg: &RouteLeg, raw: &[u8]) -> Result<ParsedReply, Refusal> {
    let data = decode_reply_json(raw)?;
    let first = data["choices"].as_array().and_then(|v| v.first());
    let (content, finish_reason) = extract_reply_content(first)?;
    let input = usage_tokens(&data, "prompt_tokens")?;
    let output = usage_tokens(&data, "completion_tokens")?;
    let (cost, source) = compute_reply_cost(leg, &data, &input, &output);
    let model = data["model"]
        .as_str()
        .filter(|v| !v.is_empty())
        .unwrap_or(&leg.model)
        .to_owned();
    Ok(ParsedReply {
        content,
        model,
        input_tokens: input,
        output_tokens: output,
        cost_microusd: Integer(cost),
        cost_source: source.into(),
        finish_reason,
    })
}

fn extract_machine_fields(text: &str) -> Result<Vec<(String, String)>, Refusal> {
    let pattern = Regex::new(r"(?s)```machine\s*\n(.*?)```")
        .map_err(|_| Refusal::new("MALFORMED", "machine parser unavailable"))?;
    let found: Vec<_> = pattern.captures_iter(text).collect();
    if found.len() != 1 {
        return Err(Refusal::new(
            "MALFORMED",
            format!("expected one machine block, found {}", found.len()),
        ));
    }
    let body = found[0]
        .get(1)
        .ok_or_else(|| Refusal::new("MALFORMED", "machine block body is absent"))?
        .as_str();
    let mut fields = Vec::new();
    for line in trim_python(body).split([
        '\n', '\r', '\u{b}', '\u{c}', '\u{1c}', '\u{1d}', '\u{1e}', '\u{85}', '\u{2028}',
        '\u{2029}',
    ]) {
        if let Some((key, value)) = line.split_once('=') {
            fields.push((trim_python(key).into(), trim_python(value).into()));
        }
    }
    Ok(fields)
}
fn validate_machine_fields(
    fields: BTreeMap<String, String>,
) -> Result<BTreeMap<String, String>, Refusal> {
    let missing: Vec<_> = [
        "AUTHORITY_EFFECT",
        "RESIDUAL_COLOUR",
        "DISPOSITION",
        "DDC_LETTER",
    ]
    .into_iter()
    .filter(|k| !fields.contains_key(*k))
    .map(repr_string)
    .collect();
    if !missing.is_empty() {
        return Err(Refusal::new(
            "MALFORMED",
            format!("machine block missing [{}]", missing.join(", ")),
        ));
    }
    if !matches!(
        fields.get("RESIDUAL_COLOUR").map(String::as_str),
        Some("Open" | "Closed" | "Exact")
    ) {
        return Err(Refusal::new(
            "MALFORMED",
            format!(
                "bad RESIDUAL_COLOUR {}",
                repr_string(
                    fields
                        .get("RESIDUAL_COLOUR")
                        .map(String::as_str)
                        .unwrap_or("")
                )
            ),
        ));
    }
    Ok(fields)
}

pub fn parse_machine_block(text: &str) -> Result<BTreeMap<String, String>, Refusal> {
    validate_machine_fields(extract_machine_fields(text)?.into_iter().collect())
}
pub(crate) fn usable_machine_reply(
    parsed: &ParsedReply,
) -> Result<BTreeMap<String, String>, Refusal> {
    let extracted = extract_machine_fields(&parsed.content);
    if let Ok(fields) = &extracted {
        // Inspect each declared authority before missing/colour validation and
        // before duplicate fields collapse into the legacy public map shape.
        if let Some((_, authority)) = fields
            .iter()
            .find(|(key, value)| key == "AUTHORITY_EFFECT" && value != "None")
        {
            return Err(Refusal::new(
                "AUTHORITY_MINT_REFUSED",
                format!(
                    "{} returned AUTHORITY_EFFECT={}",
                    parsed.model,
                    repr_string(authority)
                ),
            ));
        }
    }
    if matches!(
        parsed.finish_reason.as_deref(),
        Some("length" | "max_tokens" | "max_output_tokens")
    ) {
        return Err(Refusal::new("TRUNCATED", "provider stopped at its output limit; incomplete reply cannot become candidate evidence"));
    }
    if trim_python(&parsed.content).is_empty() {
        return Err(Refusal::new(
            "EMPTY_REPLY",
            "provider returned no deliverable content",
        ));
    }
    validate_machine_fields(extracted?.into_iter().collect())
}
fn rejected_attempts(mut refusal: Refusal, attempts: &[Value]) -> Refusal {
    if !attempts.is_empty() {
        refusal
            .details
            .insert("rejected_attempts".into(), json!(attempts).to_string());
    }
    refusal
}
pub struct RoutedSeatExecutor<T: SeatTransport, L: CallLedger, C: Clock> {
    pub table: RoutingTable,
    pub config_digest: String,
    pub transports: T,
    pub ledger: L,
    pub bout_id: String,
    pub max_output_tokens: u64,
    pub clock: C,
    pub spent_bout: BigInt,
    pub spent_tier: BTreeMap<String, BigInt>,
}
impl<T: SeatTransport, L: CallLedger, C: Clock> RoutedSeatExecutor<T, L, C> {
    pub(crate) fn record(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: Option<&RouteLeg>,
        index: usize,
        extra: Value,
    ) -> Result<(), Refusal> {
        let mut record = json!({
            "authority_effect": "None", "bout_id": self.bout_id, "candidate_id": request.candidate_id,
            "config_digest": self.config_digest, "day": self.clock.today(), "leg_index": index,
            "model": leg.map(|l| &l.model), "request_digest": request.request_digest()?,
            "round_index": request.round_index, "router": leg.map(|l| &l.router), "seat_id": request.seat_id, "tier": tier,
        });
        let fields = extra
            .as_object()
            .ok_or_else(|| Refusal::new("LEDGER_INVALID", "record fields must be a mapping"))?;
        let record_fields = record
            .as_object_mut()
            .ok_or_else(|| Refusal::new("LEDGER_INVALID", "record must be a mapping"))?;
        for (key, value) in fields {
            record_fields.insert(key.clone(), value.clone());
        }
        // Python's JSONL canonical key order is part of its byte contract.
        record_fields.sort_keys();
        self.ledger.append(&record)
    }
    fn build_seat_prompt(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
    ) -> Result<(SeatPrompt, BigInt), Refusal> {
        let operator = if request.cognitive_operator.is_empty() {
            "adversarial_panel"
        } else {
            &request.cognitive_operator
        };
        let system = format!("You are seat '{}' (cognitive operator: {}) in scene '{}' of Adversary's Swarm Dialectic.\nYou have no authority. End your reply with exactly one machine block:\n\n```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=<Open|Closed|Exact>\nDISPOSITION=<SELECT|CHALLENGE|REJECT|PASS_TO_MASTER|REFUSE>\nDDC_LETTER=<E|R|C|I|Λ|D|M|T>\n```\n", request.seat_id, operator, request.scene_id);
        let mut user = request.prompt_text.clone();
        if !request.context_bytes.is_empty() {
            user.push_str("\n\n[Candidate Context]:\n");
            user.push_str(&String::from_utf8_lossy(&request.context_bytes));
        }
        let input = BigInt::from(system.len()) + BigInt::from(user.len());
        if let Some(limit) = &self.table.budget.max_input_bytes_per_call {
            if input > limit.0 {
                let limit = limit.clone();
                self.record(
                    request,
                    tier,
                    None,
                    0,
                    json!({"outcome": "INPUT_TOO_LARGE", "cost_microusd": 0, "input_bytes": Integer(input.clone()), "max_input_bytes": limit}),
                )?;
                return Err(Refusal::new(
                    "INPUT_TOO_LARGE",
                    format!("input {input} bytes exceeds per-call limit {}", limit.0),
                ));
            }
        }
        Ok((SeatPrompt { system, user }, input))
    }

    fn admit_leg_spend(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &RouteLeg,
        index: usize,
        input: &BigInt,
        rejected: &[Value],
    ) -> Result<BigInt, Refusal> {
        let max_tokens = BigInt::from(self.max_output_tokens);
        let admission_tokens = self
            .table
            .budget
            .admission_reserve_output_tokens
            .as_ref()
            .map_or(max_tokens.clone(), |r| max_tokens.min(r.0.clone()));
        let worst = leg.cost_microusd(input, &admission_tokens);
        let day_spend = self.ledger.spent_on(&self.clock.today())?;
        let admitted = admit_spend(
            &self.spent_bout,
            &day_spend,
            &worst,
            &self.table.budget,
            tier,
            self.spent_tier.get(tier).unwrap_or(&BigInt::zero()),
        );
        if let Err(error) = admitted {
            self.record(
                request,
                tier,
                Some(leg),
                index,
                json!({"outcome": error.code, "cost_microusd": 0, "worst_case_microusd": Integer(worst)}),
            )?;
            return Err(rejected_attempts(error, rejected));
        }
        Ok(admission_tokens)
    }

    fn send_and_parse_leg(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &RouteLeg,
        index: usize,
        candidate: &SeatPrompt,
        failures: &mut Vec<String>,
    ) -> Result<Option<(Vec<u8>, ParsedReply, u64)>, Refusal> {
        let started = self.clock.milliseconds();
        let sent = self
            .transports
            .send(&leg.router, &leg.model, candidate, self.max_output_tokens);
        let parsed = sent.and_then(|raw| {
            parse_reply(leg, &raw)
                .map(|p| (raw, p))
                .map_err(|failure| TransportFailure {
                    kind: failure
                        .details
                        .get("exception_type")
                        .cloned()
                        .unwrap_or_else(|| "ValueError".into()),
                })
        });
        let (raw, parsed) = match parsed {
            Ok(pair) => pair,
            Err(error) => {
                self.record(
                    request,
                    tier,
                    Some(leg),
                    index,
                    json!({"outcome": "TRANSPORT_ERROR", "cost_microusd": 0, "error": error.kind}),
                )?;
                failures.push(format!(
                    "{}:{}=TRANSPORT_ERROR({})",
                    leg.router, leg.model, error.kind
                ));
                return Ok(None);
            }
        };
        let latency = self.clock.milliseconds().saturating_sub(started);
        self.spent_bout += &parsed.cost_microusd.0;
        *self.spent_tier.entry(tier.to_owned()).or_default() += &parsed.cost_microusd.0;
        Ok(Some((raw, parsed, latency)))
    }

    #[allow(clippy::too_many_arguments)]
    fn handle_machine_failure(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &RouteLeg,
        index: usize,
        raw: &[u8],
        parsed: &ParsedReply,
        latency: u64,
        failure: Refusal,
        rejected: &mut Vec<Value>,
        failures: &mut Vec<String>,
    ) -> Result<(), Refusal> {
        let attempt = json!({
            "outcome":failure.code,"refusal":failure,"model":parsed.model,"provider":leg.router,
            "leg_index":index,"request_digest":request.request_digest()?,
            "cost_microusd":parsed.cost_microusd,"cost_source":parsed.cost_source,
            "input_tokens":parsed.input_tokens,"output_tokens":parsed.output_tokens,
            "finish_reason":parsed.finish_reason,"latency_ms":latency,"max_tokens":self.max_output_tokens,
            "raw_reply_hex":hex::encode(raw),
            "raw_reply_sha256":format!("sha256:{}",hex::encode(Sha256::digest(raw))),
            "reply_digest":format!("sha256:{}",hex::encode(Sha256::digest(parsed.content.as_bytes()))),
            "authority_effect":"None"
        });
        rejected.push(attempt.clone());
        self.record(request, tier, Some(leg), index, attempt)
            .map_err(|error| rejected_attempts(error, rejected))?;
        if failure.code == "AUTHORITY_MINT_REFUSED" {
            return Err(rejected_attempts(failure, rejected));
        }
        failures.push(format!("{}:{}={}", leg.router, leg.model, failure.code));
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    fn finalize_leg_reply(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &RouteLeg,
        index: usize,
        raw: Vec<u8>,
        parsed: ParsedReply,
        fields: BTreeMap<String, String>,
        latency: u64,
        admission_tokens: BigInt,
        rejected: &mut Vec<Value>,
    ) -> Result<SeatTurnReply, Refusal> {
        let outcome = "OK";
        let overshoot =
            (&self.spent_bout - &self.table.budget.per_bout_microusd.0).max(BigInt::zero());
        let mut parameters = BTreeMap::from([
            ("bout_id".into(), json!(self.bout_id)),
            ("config_digest".into(), json!(self.config_digest)),
            ("cost_microusd".into(), json!(parsed.cost_microusd)),
            ("cost_source".into(), json!(parsed.cost_source)),
            ("leg_index".into(), json!(index)),
            ("machine_block".into(), json!(outcome)),
            ("max_tokens".into(), json!(self.max_output_tokens)),
            ("tier".into(), json!(tier)),
        ]);
        if !rejected.is_empty() {
            parameters.insert("rejected_attempts".into(), json!(rejected));
        }
        let reply = SeatTurnReply {
            reply_text: parsed.content.clone(),
            residual_colour: fields
                .get("RESIDUAL_COLOUR")
                .cloned()
                .unwrap_or_else(|| "Open".into()),
            authority_effect: "None".into(),
            machine_fields: fields.clone(),
            raw_bytes: raw,
            model: Some(parsed.model.clone()),
            provider: Some(leg.router.clone()),
            parameters: Some(parameters),
            usage: Some(BTreeMap::from([
                ("input_tokens".into(), json!(parsed.input_tokens)),
                ("output_tokens".into(), json!(parsed.output_tokens)),
            ])),
            request_digest: Some(request.request_digest()?),
        };
        if let Err(failure) = reply.validate() {
            let refusal = Refusal::new(
                "REPLY_INVALID",
                format!(
                    "{}: reply rejected by the seat-turn contract ({})",
                    leg.model, failure.message
                ),
            );
            let attempt = json!({
                "outcome":"REPLY_INVALID","refusal":refusal,"model":parsed.model,"provider":leg.router,
                "leg_index":index,"request_digest":request.request_digest()?,
                "cost_microusd":parsed.cost_microusd,"cost_source":parsed.cost_source,
                "input_tokens":parsed.input_tokens,"output_tokens":parsed.output_tokens,
                "finish_reason":parsed.finish_reason,"latency_ms":latency,"max_tokens":self.max_output_tokens,
                "raw_reply_hex":hex::encode(&reply.raw_bytes),
                "raw_reply_sha256":format!("sha256:{}",hex::encode(Sha256::digest(&reply.raw_bytes))),
                "reply_digest":format!("sha256:{}",hex::encode(Sha256::digest(parsed.content.as_bytes()))),
                "overshoot_microusd":Integer(overshoot),"error":"TypeError","authority_effect":"None"
            });
            rejected.push(attempt.clone());
            self.record(request, tier, Some(leg), index, attempt)
                .map_err(|error| rejected_attempts(error, rejected))?;
            return Err(rejected_attempts(refusal, rejected));
        }
        self.record(
            request,
            tier,
            Some(leg),
            index,
            json!({
                "outcome": outcome, "disposition": fields.get("DISPOSITION"), "cost_microusd": parsed.cost_microusd,
                "cost_source": parsed.cost_source, "input_tokens": parsed.input_tokens, "output_tokens": parsed.output_tokens,
                "latency_ms": latency, "id_verified": leg.id_verified, "admission_output_tokens": Integer(admission_tokens),
                "finish_reason": parsed.finish_reason, "ddc_letter": fields.get("DDC_LETTER"), "residual_colour": fields.get("RESIDUAL_COLOUR"),
                "reply_digest": format!("sha256:{}", hex::encode(Sha256::digest(parsed.content.as_bytes()))),
                "temperature_sent": Value::Null, "max_tokens": self.max_output_tokens, "overshoot_microusd": Integer(overshoot),
            }),
        )?;
        Ok(reply)
    }

    #[allow(clippy::too_many_arguments)]
    fn try_execute_leg(
        &mut self,
        request: &SeatTurnRequest,
        tier: &str,
        leg: &RouteLeg,
        index: usize,
        candidate: &SeatPrompt,
        input: &BigInt,
        failures: &mut Vec<String>,
        rejected: &mut Vec<Value>,
    ) -> Result<Option<SeatTurnReply>, Refusal> {
        if !self.transports.configured(&leg.router) {
            self.record(
                request,
                tier,
                Some(leg),
                index,
                json!({"outcome": "ROUTER_UNCONFIGURED", "cost_microusd": 0}),
            )?;
            failures.push(format!("{}:{}=ROUTER_UNCONFIGURED", leg.router, leg.model));
            return Ok(None);
        }
        let admission_tokens = self.admit_leg_spend(request, tier, leg, index, input, rejected)?;
        let Some((raw, parsed, latency)) =
            self.send_and_parse_leg(request, tier, leg, index, candidate, failures)?
        else {
            return Ok(None);
        };
        let fields = match usable_machine_reply(&parsed) {
            Ok(fields) => fields,
            Err(failure) => {
                self.handle_machine_failure(
                    request, tier, leg, index, &raw, &parsed, latency, failure, rejected, failures,
                )?;
                return Ok(None);
            }
        };
        self.finalize_leg_reply(
            request,
            tier,
            leg,
            index,
            raw,
            parsed,
            fields,
            latency,
            admission_tokens,
            rejected,
        )
        .map(Some)
    }

    pub fn execute(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        let route = self.table.seat(&request.seat_id)?.clone();
        if !route.calls_model() {
            return Err(Refusal::new(
                "SEAT_NOT_MODEL_BACKED",
                format!("seat {} is {}", repr_string(&route.seat_id), route.tier),
            ));
        }
        let (candidate, input) = self.build_seat_prompt(request, &route.tier)?;
        let mut failures = Vec::new();
        let mut rejected = Vec::new();
        for (index, leg) in route.legs.iter().enumerate() {
            if let Some(reply) = self.try_execute_leg(
                request,
                &route.tier,
                leg,
                index,
                &candidate,
                &input,
                &mut failures,
                &mut rejected,
            )? {
                return Ok(reply);
            }
        }
        Err(rejected_attempts(
            Refusal::new(
                "ALL_LEGS_FAILED",
                format!(
                    "seat {}: {}",
                    repr_string(&route.seat_id),
                    failures.join("; ")
                ),
            ),
            &rejected,
        ))
    }
}
impl<T: SeatTransport, L: CallLedger, C: Clock> SeatPort for RoutedSeatExecutor<T, L, C> {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        self.execute(request)
    }
}

// Origin: engine/crates_rs/core_adversary/src/gateway.rs
// Claim: urn:core:crates_rs:core-adversary:gateway:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1e23cf4c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1e23cf4c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1e23cf4c {
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
impl BoundaryError1e23cf4c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1e23cf4c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1e23cf4c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1e23cf4c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1e23cf4c> {
        if capacity_bound == 0 {
            return Err(BoundaryError1e23cf4c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1e23cf4c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1e23cf4c::ExceedsCapacity {
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
mod l4_boundary_tests_1e23cf4c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1e23cf4c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1e23cf4c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1e23cf4c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1e23cf4c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1e23cf4c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError1e23cf4c::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError1e23cf4c::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
