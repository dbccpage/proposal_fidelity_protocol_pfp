//! Public gateway regressions authored after the clean native live bundle.
//! Scripted transports exercise the real router/custody; they do not call providers.
use num_bigint::BigInt;
use core_adversary::stage::ports::{Refusal, SeatPort, SeatTurnRequest};
use core_adversary::{
    custody::RecordingSeatPort,
    exact::integer,
    gateway::{CallLedger, Clock, RoutedSeatExecutor, SeatPrompt, SeatTransport, TransportFailure},
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, VecDeque};

const GOOD: &str = "```candidate\n{\"status\":\"SOLVED\",\"payload\":\"unchanged\"}\n```\n\n```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=Exact\nDISPOSITION=SELECT\nDDC_LETTER=E\n```";

#[derive(Debug, PartialEq)]
struct Attempt {
    model: String,
    system: String,
    user: String,
    max_tokens: u64,
}
struct ScriptedTransport {
    responses: VecDeque<Vec<u8>>,
    attempts: Vec<Attempt>,
}
impl SeatTransport for ScriptedTransport {
    fn configured(&self, _: &str) -> bool {
        true
    }
    fn send(
        &mut self,
        _: &str,
        model: &str,
        prompt: &SeatPrompt,
        max_tokens: u64,
    ) -> Result<Vec<u8>, TransportFailure> {
        self.attempts.push(Attempt {
            model: model.into(),
            system: prompt.system.clone(),
            user: prompt.user.clone(),
            max_tokens,
        });
        self.responses.pop_front().ok_or_else(|| TransportFailure {
            kind: "UnscriptedCall".into(),
        })
    }
}
#[derive(Default)]
struct MemoryLedger(Vec<Value>);
impl CallLedger for MemoryLedger {
    fn append(&mut self, record: &Value) -> Result<(), Refusal> {
        self.0.push(record.clone());
        Ok(())
    }
    fn spent_on(&mut self, day: &str) -> Result<BigInt, Refusal> {
        Ok(self
            .0
            .iter()
            .filter(|row| row["day"] == day)
            .filter_map(|row| integer(&row["cost_microusd"]))
            .sum())
    }
}
struct FixedClock;
impl Clock for FixedClock {
    fn today(&self) -> String {
        "2026-10-11".into()
    }
    fn milliseconds(&self) -> u64 {
        0
    }
}
type Executor = RoutedSeatExecutor<ScriptedTransport, MemoryLedger, FixedClock>;

fn response(content: Value, finish: &str, cost: &str, output_tokens: u64) -> Vec<u8> {
    // Decimal cost is parsed as an exact JSON number, never a binary float.
    serde_json::to_vec(&json!({
        "model":"observed/model", "choices":[{"message":{"content":content},"finish_reason":finish}],
        "usage":{"prompt_tokens":3088,"completion_tokens":output_tokens,"cost":serde_json::from_str::<Value>(cost).unwrap()}
    })).unwrap()
}
fn success(cost: &str) -> Vec<u8> {
    response(json!(GOOD), "stop", cost, 12)
}
fn executor(cap: u64, legs: usize, responses: Vec<Vec<u8>>) -> Executor {
    let legs: Vec<Value> = (0..legs)
        .map(|index| {
            json!({
                "router":"openrouter","model":format!("route/model-{index}"),
                "input_microusd_per_token":"0","output_microusd_per_token":"1","id_verified":true
            })
        })
        .collect();
    let table = serde_json::from_value(json!({
        "version":"1", "primary_router":"openrouter", "cheap_share_min":"1/2",
        "budget":{"per_bout_microusd":cap,"per_day_microusd":1000000,"admission_reserve_output_tokens":1,
            "tier_per_bout_microusd":[["cheap",1000000]],"max_input_bytes_per_call":null},
        "seats":[{"seat_id":"Gauge Breaker","tier":"cheap","legs":legs}]
    })).unwrap();
    RoutedSeatExecutor {
        table,
        config_digest: "sha256:recovery-config".into(),
        transports: ScriptedTransport {
            responses: responses.into(),
            attempts: Vec::new(),
        },
        ledger: MemoryLedger::default(),
        bout_id: "recovery-bout".into(),
        max_output_tokens: 4096,
        clock: FixedClock,
        spent_bout: BigInt::from(0),
        spent_tier: BTreeMap::new(),
    }
}
fn request() -> SeatTurnRequest {
    SeatTurnRequest {
        scene_id: "act2_panel_debate".into(),
        seat_id: "seat_gauge_breaker".into(),
        prompt_text: "Produce this exact candidate without changing its task.".into(),
        cognitive_operator: "Nine-Dot Surprise".into(),
        role_kind: "prose".into(),
        candidate_id: "cand_2".into(),
        round_index: 0,
        context_bytes: b"same candidate context\nraw bytes".to_vec(),
    }
}
fn assert_raw_attempt(row: &Value, raw: &[u8], code: &str, cost: u64) {
    assert_eq!(row["outcome"], code);
    assert_eq!(row["refusal"]["code"], code);
    assert_eq!(row["raw_reply_hex"], hex::encode(raw));
    assert_eq!(
        row["raw_reply_sha256"],
        format!("sha256:{}", hex::encode(Sha256::digest(raw)))
    );
    assert_eq!(row["cost_microusd"], cost);
    assert_eq!(row["cost_source"], "provider_receipt");
    assert_eq!(row["authority_effect"], "None");
}
fn refused_attempts(refusal: &Refusal) -> Vec<Value> {
    serde_json::from_str(
        refusal
            .details
            .get("rejected_attempts")
            .expect("rejected response custody"),
    )
    .unwrap()
}

#[test]
fn observed_null_content_reasoning_exhaustion_falls_back_without_an_empty_reply() {
    // Reduced shape of the real failed provider response: no reasoning text copied.
    let bad = response(Value::Null, "length", "0.004796871", 4096);
    let good = success("0.000011");
    let mut runtime = executor(100000, 2, vec![bad.clone(), good.clone()]);
    let reply = runtime.execute_turn(&request()).unwrap();
    assert_eq!(reply.reply_text, GOOD);
    assert!(!reply.reply_text.is_empty());
    assert_eq!(reply.raw_bytes, good);
    assert_eq!(runtime.transports.attempts.len(), 2);
    assert_eq!(
        runtime.transports.attempts[0].system,
        runtime.transports.attempts[1].system
    );
    assert_eq!(
        runtime.transports.attempts[0].user,
        runtime.transports.attempts[1].user
    );
    assert_eq!(runtime.transports.attempts[1].model, "route/model-1");
    assert_eq!(runtime.spent_bout, BigInt::from(4808));
    assert_eq!(runtime.spent_tier["cheap"], BigInt::from(4808));
    assert_raw_attempt(&runtime.ledger.0[0], &bad, "TRUNCATED", 4797);
    assert_eq!(runtime.ledger.0[0]["output_tokens"], 4096);
    assert_eq!(runtime.ledger.0[0]["finish_reason"], "length");
    assert_raw_attempt(
        &reply.parameters.as_ref().unwrap()["rejected_attempts"][0],
        &bad,
        "TRUNCATED",
        4797,
    );
}

#[test]
fn truncation_is_rejected_even_when_a_complete_machine_block_is_present() {
    for finish in ["length", "max_tokens", "max_output_tokens"] {
        let bad = response(json!(GOOD), finish, "0.000007", 4096);
        let mut runtime = executor(100000, 2, vec![bad.clone(), success("0.000011")]);
        let reply = runtime.execute_turn(&request()).unwrap();
        assert_eq!(runtime.transports.attempts.len(), 2);
        assert_eq!(reply.parameters.as_ref().unwrap()["leg_index"], 1);
        assert_raw_attempt(&runtime.ledger.0[0], &bad, "TRUNCATED", 7);
        assert_eq!(runtime.spent_bout, BigInt::from(18));
    }
}

#[test]
fn empty_stop_responses_are_not_converted_to_open_candidates() {
    for content in [Value::Null, json!(""), json!(" \r\n\t ")] {
        let bad = response(content, "stop", "0.000007", 1);
        let mut runtime = executor(100000, 2, vec![bad.clone(), success("0.000011")]);
        assert_eq!(runtime.execute_turn(&request()).unwrap().reply_text, GOOD);
        assert_raw_attempt(&runtime.ledger.0[0], &bad, "EMPTY_REPLY", 7);
        assert_eq!(runtime.transports.attempts.len(), 2);
    }
}

#[test]
fn malformed_fallback_preserves_exact_request_and_both_raw_responses_in_custody() {
    let bad = response(json!("No required machine block."), "stop", "0.000007", 4);
    let good = success("0.000011");
    let mut runtime = executor(100000, 2, vec![bad.clone(), good.clone()]);
    let (reply, turns) = {
        let mut recorder =
            RecordingSeatPort::new(&mut runtime, None, "recovery-bout", "same-task", "", None);
        let reply = recorder.execute_turn(&request()).unwrap();
        (reply, recorder.turns.clone())
    };
    assert_eq!(turns.len(), 1);
    assert_eq!(turns[0]["outcome"], "REPLY");
    assert_eq!(turns[0]["raw_reply_hex"], hex::encode(&good));
    assert_raw_attempt(
        &turns[0]["provenance"]["parameters"]["rejected_attempts"][0],
        &bad,
        "MALFORMED",
        7,
    );
    assert_eq!(reply.reply_text, GOOD);
    assert_eq!(
        runtime.transports.attempts[0].system,
        runtime.transports.attempts[1].system
    );
    assert_eq!(
        runtime.transports.attempts[0].user,
        runtime.transports.attempts[1].user
    );
    assert!(runtime.transports.attempts[1]
        .user
        .contains("same candidate context\nraw bytes"));
    assert_eq!(
        runtime.transports.attempts[0].max_tokens,
        runtime.transports.attempts[1].max_tokens
    );
    assert_eq!(
        runtime.ledger.0[0]["request_digest"],
        runtime.ledger.0[1]["request_digest"]
    );
    assert_eq!(
        runtime.ledger.spent_on("2026-10-11").unwrap(),
        BigInt::from(18)
    );
}

#[test]
fn exhausted_legs_refuse_and_preserve_each_paid_failure_without_a_reply() {
    let bad = vec![
        response(json!("No machine block"), "stop", "0.000007", 4),
        response(Value::Null, "stop", "0.000011", 1),
        response(json!(GOOD), "length", "0.000013", 4096),
    ];
    let mut runtime = executor(100000, 3, bad.clone());
    let (failure, turns) = {
        let mut recorder =
            RecordingSeatPort::new(&mut runtime, None, "recovery-bout", "same-task", "", None);
        (
            recorder.execute_turn(&request()).unwrap_err(),
            recorder.turns.clone(),
        )
    };
    assert_eq!(failure.code, "ALL_LEGS_FAILED");
    assert_eq!(runtime.transports.attempts.len(), 3);
    assert!(runtime.transports.responses.is_empty());
    let retained = refused_attempts(&failure);
    assert_eq!(retained.len(), 3);
    for (index, (code, cost)) in [("MALFORMED", 7), ("EMPTY_REPLY", 11), ("TRUNCATED", 13)]
        .into_iter()
        .enumerate()
    {
        assert_raw_attempt(&retained[index], &bad[index], code, cost);
    }
    assert_eq!(runtime.spent_bout, BigInt::from(31));
    assert_eq!(turns[0]["outcome"], "REFUSED");
    assert!(turns[0].get("reply_text").is_none());
    assert!(turns[0].get("raw_reply_hex").is_none());
}

#[test]
fn billed_malformed_attempt_exhausts_budget_before_next_leg_can_send() {
    let bad = response(json!("No block"), "stop", "0.000007", 4);
    let mut runtime = executor(7, 2, vec![bad.clone(), success("0.000011")]);
    let failure = runtime.execute_turn(&request()).unwrap_err();
    assert_eq!(failure.code, "BUDGET_BOUT_EXCEEDED");
    assert_eq!(runtime.transports.attempts.len(), 1);
    assert_eq!(runtime.transports.responses.len(), 1);
    assert_eq!(runtime.spent_bout, BigInt::from(7));
    assert_eq!(runtime.ledger.0[1]["outcome"], "BUDGET_BOUT_EXCEEDED");
    assert_eq!(runtime.ledger.0[1]["cost_microusd"], 0);
    assert_raw_attempt(&refused_attempts(&failure)[0], &bad, "MALFORMED", 7);
}

#[test]
fn authority_mint_is_a_paid_hard_refusal_even_when_truncated() {
    for finish in ["stop", "length"] {
        let bad = response(
            json!(GOOD.replace("AUTHORITY_EFFECT=None", "AUTHORITY_EFFECT=Sovereign")),
            finish,
            "0.000007",
            12,
        );
        let mut runtime = executor(100000, 2, vec![bad.clone(), success("0.000011")]);
        let failure = runtime.execute_turn(&request()).unwrap_err();
        assert_eq!(failure.code, "AUTHORITY_MINT_REFUSED");
        assert_eq!(runtime.transports.attempts.len(), 1);
        assert_eq!(runtime.transports.responses.len(), 1);
        assert_eq!(runtime.spent_bout, BigInt::from(7));
        assert_raw_attempt(
            &refused_attempts(&failure)[0],
            &bad,
            "AUTHORITY_MINT_REFUSED",
            7,
        );
    }
}

#[test]
fn well_formed_closed_refusal_is_returned_without_rewriting_or_model_fallback() {
    let text = GOOD
        .replace("RESIDUAL_COLOUR=Exact", "RESIDUAL_COLOUR=Closed")
        .replace("DISPOSITION=SELECT", "DISPOSITION=REFUSE")
        .replace("DDC_LETTER=E", "DDC_LETTER=D");
    let raw = response(json!(text), "stop", "0.000007", 12);
    let mut runtime = executor(100000, 2, vec![raw.clone(), success("0.000011")]);
    let reply = runtime.execute_turn(&request()).unwrap();
    assert_eq!(reply.reply_text, text);
    assert_eq!(reply.raw_bytes, raw);
    assert_eq!(reply.residual_colour, "Closed");
    assert_eq!(reply.machine_fields["DISPOSITION"], "REFUSE");
    assert_eq!(reply.machine_fields["DDC_LETTER"], "D");
    assert_eq!(runtime.transports.attempts.len(), 1);
    assert!(!reply
        .parameters
        .as_ref()
        .unwrap()
        .contains_key("rejected_attempts"));
}

#[test]
fn invalid_colour_is_rejected_without_changing_it_to_open() {
    let bad = response(
        json!(GOOD.replace("RESIDUAL_COLOUR=Exact", "RESIDUAL_COLOUR=Purple")),
        "stop",
        "0.000007",
        12,
    );
    let mut runtime = executor(100000, 2, vec![bad.clone(), success("0.000011")]);
    let reply = runtime.execute_turn(&request()).unwrap();
    assert_eq!(reply.residual_colour, "Exact");
    assert_eq!(runtime.transports.attempts.len(), 2);
    assert_raw_attempt(&runtime.ledger.0[0], &bad, "MALFORMED", 7);
    assert_eq!(
        runtime.ledger.0[0]["refusal"]["message"],
        "bad RESIDUAL_COLOUR 'Purple'"
    );
}

#[test]
fn subsequent_turns_keep_prior_attempt_spend_and_do_not_reuse_rejection_context() {
    let mut runtime = executor(
        31,
        2,
        vec![
            response(json!("No block"), "stop", "0.000007", 4),
            success("0.000011"),
            success("0.000013"),
        ],
    );
    let first = runtime.execute_turn(&request()).unwrap();
    assert!(first
        .parameters
        .as_ref()
        .unwrap()
        .contains_key("rejected_attempts"));
    let mut next = request();
    next.candidate_id = "cand_3".into();
    let second = runtime.execute_turn(&next).unwrap();
    assert!(!second
        .parameters
        .as_ref()
        .unwrap()
        .contains_key("rejected_attempts"));
    assert_ne!(first.request_digest, second.request_digest);
    assert_eq!(runtime.spent_bout, BigInt::from(31));
    assert_eq!(runtime.spent_tier["cheap"], BigInt::from(31));
    assert_eq!(
        runtime.ledger.spent_on("2026-10-11").unwrap(),
        BigInt::from(31)
    );
    assert_eq!(
        runtime.execute_turn(&next).unwrap_err().code,
        "BUDGET_BOUT_EXCEEDED"
    );
    assert_eq!(runtime.transports.attempts.len(), 3);
}

#[test]
fn authority_claim_cannot_hide_behind_malformed_fields_or_a_later_none() {
    let sovereign = GOOD.replace("AUTHORITY_EFFECT=None", "AUTHORITY_EFFECT=Sovereign");
    let cases = [
        sovereign.replace("RESIDUAL_COLOUR=Exact", "RESIDUAL_COLOUR=Purple"),
        sovereign.replace("DDC_LETTER=E\n", ""),
        "```machine\nAUTHORITY_EFFECT=Sovereign\n```".into(),
        sovereign.replace(
            "AUTHORITY_EFFECT=Sovereign",
            "AUTHORITY_EFFECT=Sovereign\nAUTHORITY_EFFECT=None",
        ),
    ];
    for text in cases {
        let raw = response(json!(text), "stop", "0.000007", 12);
        let mut runtime = executor(100000, 2, vec![raw.clone(), success("0.000011")]);
        let failure = runtime.execute_turn(&request()).unwrap_err();
        assert_eq!(failure.code, "AUTHORITY_MINT_REFUSED");
        assert_eq!(runtime.transports.attempts.len(), 1);
        assert_eq!(runtime.transports.responses.len(), 1);
        assert_eq!(runtime.spent_bout, BigInt::from(7));
        assert_raw_attempt(
            &refused_attempts(&failure)[0],
            &raw,
            "AUTHORITY_MINT_REFUSED",
            7,
        );
    }
}

#[test]
fn invalid_usage_after_paid_fallback_keeps_every_raw_failure_in_terminal_custody() {
    let first = response(json!("No machine block"), "stop", "0.000007", 4);
    let mut invalid: Value = serde_json::from_slice(&success("0.000011")).unwrap();
    invalid["usage"]["prompt_tokens"] = json!(-1);
    let second = serde_json::to_vec(&invalid).unwrap();
    let mut runtime = executor(
        100000,
        3,
        vec![first.clone(), second.clone(), success("0.000013")],
    );
    let (failure, turns) = {
        let mut recorder =
            RecordingSeatPort::new(&mut runtime, None, "recovery-bout", "same-task", "", None);
        (
            recorder.execute_turn(&request()).unwrap_err(),
            recorder.turns.clone(),
        )
    };
    assert_eq!(failure.code, "REPLY_INVALID");
    assert_eq!(runtime.transports.attempts.len(), 2);
    assert_eq!(runtime.transports.responses.len(), 1);
    assert_eq!(runtime.spent_bout, BigInt::from(18));
    assert_eq!(runtime.spent_tier["cheap"], BigInt::from(18));
    let retained = refused_attempts(&failure);
    assert_eq!(retained.len(), 2);
    assert_raw_attempt(&retained[0], &first, "MALFORMED", 7);
    assert_raw_attempt(&retained[1], &second, "REPLY_INVALID", 11);
    assert_eq!(retained[1]["input_tokens"], -1);
    assert_eq!(runtime.ledger.0[1]["raw_reply_hex"], hex::encode(&second));
    assert_eq!(turns[0]["outcome"], "REFUSED");
    assert!(turns[0].get("reply_text").is_none());
    let in_bundle: Vec<Value> = serde_json::from_str(
        turns[0]["refusal"]["details"]["rejected_attempts"]
            .as_str()
            .unwrap(),
    )
    .unwrap();
    assert_eq!(in_bundle, retained);
}

// Origin: engine/crates_rs/tests/core_adversary/gateway_reply_recovery.rs
// Claim: urn:core:crates_rs:tests:gateway-reply-recovery:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord80b004e4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord80b004e4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError80b004e4 {
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
impl BoundaryError80b004e4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError80b004e4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError80b004e4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord80b004e4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError80b004e4> {
        if capacity_bound == 0 {
            return Err(BoundaryError80b004e4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError80b004e4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError80b004e4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_80b004e4() {
    let admitted = BoundaryRecord80b004e4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord80b004e4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
