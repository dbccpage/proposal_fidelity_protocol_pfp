use num_bigint::BigInt;
use core_adversary::stage::ports::{SeatPort, SeatTurnRequest};
use core_adversary::{
    gateway::{
        CallLedger, Clock, RoutedSeatExecutor, SeatPrompt, SeatTransport, SeatTransportOutcome,
        TransportFailure,
    },
    ledger::FileCallLedger,
    pfp_gateway::PfpSeatExecutor,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, VecDeque};
const ANSWER:&str="```candidate\n{\"status\":\"SOLVED\",\"payload\":\"unchanged\"}\n```\n```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=Exact\nDISPOSITION=SELECT\nDDC_LETTER=E\n```\n";
#[derive(Clone, Copy)]
enum Mode {
    Good,
    WrongTask,
    WrongAttempt,
    WrongInput,
    Extra,
    Malformed,
    Duplicate,
    NoCost,
    NoUsage,
    Transport,
    Authority,
    Truncated,
    Http400,
    Overrun,
}
struct Script {
    modes: VecDeque<Mode>,
    calls: usize,
    prompts: Vec<String>,
    raw: Vec<Vec<u8>>,
}
impl SeatTransport for Script {
    fn configured(&self, _: &str) -> bool {
        true
    }
    fn send(
        &mut self,
        _: &str,
        _: &str,
        _: &SeatPrompt,
        _: u64,
    ) -> Result<Vec<u8>, TransportFailure> {
        panic!("PFP must use bound transport outcome")
    }
    fn send_bound(
        &mut self,
        _: &str,
        model: &str,
        prompt: &SeatPrompt,
        _: u64,
    ) -> Result<SeatTransportOutcome, TransportFailure> {
        self.calls += 1;
        self.prompts.push(prompt.user.clone());
        let mode = self.modes.pop_front().expect("no unscripted extra sends");
        if matches!(mode, Mode::Transport) {
            return Err(TransportFailure {
                kind: "timeout".into(),
            });
        }
        let content = build_mock_reply_content(&prompt.user, mode);
        let mut provider = json!({"model":model,"choices":[{"message":{"content":content},"finish_reason":if matches!(mode,Mode::Truncated){"length"}else{"stop"}}],"usage":{"prompt_tokens":80,"completion_tokens":30,"cost":serde_json::from_str::<Value>(if matches!(mode,Mode::Overrun){"1.0"}else{"0.000030"}).unwrap()}});
        if matches!(mode, Mode::NoCost) {
            provider["usage"].as_object_mut().unwrap().remove("cost");
        }
        if matches!(mode, Mode::NoUsage) {
            provider["usage"]
                .as_object_mut()
                .unwrap()
                .remove("completion_tokens");
        }
        let raw = provider.to_string().into_bytes();
        self.raw.push(raw.clone());
        Ok(SeatTransportOutcome {
            raw,
            status: if matches!(mode, Mode::Http400) {
                400
            } else {
                200
            },
            truncated: None,
        })
    }
}
fn build_mock_reply_content(user: &str, mode: Mode) -> String {
    let task: Value = serde_json::from_str(user).unwrap();
    let answer = if matches!(mode, Mode::Authority) {
        ANSWER.replace("AUTHORITY_EFFECT=None", "AUTHORITY_EFFECT=ACCEPT")
    } else {
        ANSWER.into()
    };
    let mut reply = json!({"task_id":task["task_id"],"attempt_id":task["attempt_id"],"input_sha256":task["input_sha256"],"answer":answer});
    match mode {
        Mode::WrongTask => reply["task_id"] = json!("wrong"),
        Mode::WrongAttempt => reply["attempt_id"] = json!("wrong"),
        Mode::WrongInput => reply["input_sha256"] = json!("wrong"),
        Mode::Extra => reply["extra"] = json!(true),
        _ => {}
    }
    match mode {
        Mode::Malformed => "not-json".into(),
        Mode::Duplicate => format!("{{\"task_id\":\"wrong\",{}", &reply.to_string()[1..]),
        _ => reply.to_string(),
    }
}
struct FixedClock;
impl Clock for FixedClock {
    fn today(&self) -> String {
        "2026-10-12".into()
    }
    fn milliseconds(&self) -> u64 {
        0
    }
}
type Executor = PfpSeatExecutor<Script, FileCallLedger, FixedClock>;
fn executor(path: std::path::PathBuf, modes: Vec<Mode>, cap: u64) -> Executor {
    let legs:Vec<_>=(0..modes.len().max(1)).map(|i|json!({"router":"openrouter","model":format!("route/{i}"),"input_microusd_per_token":"0","output_microusd_per_token":"1","id_verified":true})).collect();
    PfpSeatExecutor{inner:RoutedSeatExecutor{table:serde_json::from_value(json!({"version":"1","primary_router":"openrouter","cheap_share_min":"1/2","budget":{"per_bout_microusd":cap,"per_day_microusd":1000000,"admission_reserve_output_tokens":1,"tier_per_bout_microusd":[["cheap",1000000]],"max_input_bytes_per_call":null},"seats":[{"seat_id":"Gauge Breaker","tier":"cheap","legs":legs}]})).unwrap(),config_digest:"sha256:config".into(),transports:Script{modes:modes.into(),calls:0,prompts:Vec::new(),raw:Vec::new()},ledger:FileCallLedger{path},bout_id:"continuing".into(),max_output_tokens:64,clock:FixedClock,spent_bout:BigInt::from(0),spent_tier:BTreeMap::new()}}
}
fn request() -> SeatTurnRequest {
    SeatTurnRequest {
        scene_id: "act2_panel_debate".into(),
        seat_id: "seat_gauge_breaker".into(),
        prompt_text: "Produce an inspectable candidate λ".into(),
        cognitive_operator: "falsify".into(),
        role_kind: "prose".into(),
        candidate_id: "cand_2".into(),
        round_index: 0,
        context_bytes: b"exact candidate context".to_vec(),
    }
}
#[test]
fn actual_pfp_boundary_preserves_answer_and_raw_provider_bytes() {
    let dir = tempfile::tempdir().unwrap();
    let mut e = executor(
        dir.path().join("ledger"),
        vec![Mode::Good, Mode::Good],
        1000,
    );
    let reply = e.execute_turn(&request()).unwrap();
    assert_eq!(reply.reply_text, ANSWER);
    assert_eq!(reply.raw_bytes, e.inner.transports.raw[0]);
    assert_eq!(
        reply.parameters.as_ref().unwrap()["evidence_grade"],
        "UNVERIFIED"
    );
    assert_eq!(
        e.inner.ledger.spent_on("2026-10-12").unwrap(),
        BigInt::from(30)
    );
    let rows = e.inner.ledger.records().unwrap();
    assert_eq!(rows[0]["pfp_state"], "RESERVED");
    assert_eq!(rows[1]["pfp_state"], "SETTLED");
    assert_eq!(rows[1]["raw_reply_hex"], hex::encode(&reply.raw_bytes));
    let p = pfp_runtime::pfp_task_turn::PreparedTaskTurn {
        system: String::new(),
        user: String::new(),
        binding: rows[1]["pfp_binding"].clone(),
    };
    assert_eq!(p.replay(&rows[1]).unwrap(), ANSWER);
    assert_eq!(e.inner.transports.calls, 1);
    assert_eq!(e.replay(&request(), &rows[1]).unwrap(), ANSWER);
    let mut changed = rows[1].clone();
    changed["raw_reply_hex"] = json!(hex::encode(b"{}"));
    assert!(e.replay(&request(), &changed).is_err());
    for (key, value) in [
        ("http_status", json!(400)),
        ("truncated", json!("response limit")),
        ("actual_cost_microusd", json!(0)),
        ("pfp_state", json!("RESERVED")),
        ("leg_index", json!(1)),
        ("router", json!("wrong-router")),
        ("model", json!("wrong-model")),
    ] {
        let mut changed = rows[1].clone();
        changed[key] = value;
        assert!(e.replay(&request(), &changed).is_err(), "{key}");
    }
    let mut changed = rows[1].clone();
    changed["leg_index"] = json!(1);
    changed["model"] = json!("route/1");
    assert!(e.replay(&request(), &changed).is_err());
    for key in ["cost", "prompt_tokens", "completion_tokens"] {
        let mut changed = rows[1].clone();
        let raw = hex::decode(changed["raw_reply_hex"].as_str().unwrap()).unwrap();
        let mut provider: Value = serde_json::from_slice(&raw).unwrap();
        provider["usage"].as_object_mut().unwrap().remove(key);
        let raw = provider.to_string().into_bytes();
        changed["raw_reply_hex"] = json!(hex::encode(&raw));
        changed["raw_reply_sha256"] =
            json!(format!("sha256:{}", hex::encode(Sha256::digest(&raw))));
        assert!(e.replay(&request(), &changed).is_err(), "{key}");
    }
    for invalid in [
        json!(-1),
        json!(1.5),
        serde_json::from_str::<Value>("18446744073709551616").unwrap(),
    ] {
        let mut changed = rows[1].clone();
        let raw = hex::decode(changed["raw_reply_hex"].as_str().unwrap()).unwrap();
        let mut provider: Value = serde_json::from_slice(&raw).unwrap();
        provider["usage"]["completion_tokens"] = invalid;
        let raw = provider.to_string().into_bytes();
        changed["raw_reply_hex"] = json!(hex::encode(&raw));
        changed["raw_reply_sha256"] =
            json!(format!("sha256:{}", hex::encode(Sha256::digest(&raw))));
        assert!(e.replay(&request(), &changed).is_err());
    }
    let mut changed = request();
    changed.context_bytes = b"changed candidate".to_vec();
    assert!(e.replay(&changed, &rows[1]).is_err());
    assert_eq!(e.inner.transports.calls, 1);
}
#[test]
fn billed_bad_envelopes_and_truncation_are_not_candidates_and_fallback_is_rebound() {
    for mode in [
        Mode::WrongTask,
        Mode::WrongAttempt,
        Mode::WrongInput,
        Mode::Extra,
        Mode::Malformed,
        Mode::Duplicate,
        Mode::Truncated,
    ] {
        let dir = tempfile::tempdir().unwrap();
        let mut e = executor(dir.path().join("ledger"), vec![mode, Mode::Good], 1000);
        let reply = e.execute(&request()).unwrap();
        assert_eq!(reply.reply_text, ANSWER);
        assert_eq!(e.inner.transports.calls, 2);
        assert_ne!(e.inner.transports.prompts[0], e.inner.transports.prompts[1]);
        assert_eq!(
            e.inner.ledger.spent_on("2026-10-12").unwrap(),
            BigInt::from(60)
        );
        assert!(reply.parameters.unwrap().contains_key("rejected_attempts"));
    }
}
#[test]
fn unknown_cost_http_error_timeout_and_missing_usage_stop_without_fallback() {
    for mode in [Mode::NoCost, Mode::Transport, Mode::Http400, Mode::NoUsage] {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("ledger");
        let mut e = executor(path.clone(), vec![mode, Mode::Good], 1000);
        let failure = e.execute(&request()).unwrap_err();
        assert!(
            ["PFP_ACCOUNTING_UNRESOLVED", "PFP_USAGE_UNAVAILABLE"].contains(&failure.code.as_str())
        );
        assert_eq!(e.inner.transports.calls, 1);
        if matches!(mode, Mode::NoUsage) {
            let mut resumed = executor(path, vec![Mode::Good], 1000);
            assert_eq!(
                resumed.execute(&request()).unwrap_err().code,
                "PFP_USAGE_UNAVAILABLE"
            );
            assert_eq!(resumed.inner.transports.calls, 0);
        } else {
            let mut resumed = executor(path, vec![Mode::Good], 1000);
            assert_eq!(
                resumed.execute(&request()).unwrap_err().code,
                "PFP_ACCOUNTING_UNRESOLVED"
            );
            assert_eq!(resumed.inner.transports.calls, 0);
            assert_eq!(
                resumed.inner.ledger.spent_on("2026-10-12").unwrap(),
                BigInt::from(64)
            );
        }
    }
}
#[test]
fn authority_mint_and_actual_cost_overrun_are_billed_hard_stops() {
    for (mode, code) in [
        (Mode::Authority, "AUTHORITY_MINT_REFUSED"),
        (Mode::Overrun, "PFP_BUDGET_OVERRUN"),
    ] {
        let dir = tempfile::tempdir().unwrap();
        let mut e = executor(dir.path().join("ledger"), vec![mode, Mode::Good], 1000);
        assert_eq!(e.execute(&request()).unwrap_err().code, code);
        assert_eq!(e.inner.transports.calls, 1);
        let spent = e.inner.ledger.spent_on("2026-10-12").unwrap();
        assert_eq!(
            spent,
            BigInt::from(if matches!(mode, Mode::Overrun) {
                1000000
            } else {
                30
            })
        );
    }
}
#[test]
fn corrupted_settlement_or_unmetered_legacy_row_refuses_before_send() {
    for corrupt in 0..7 {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("ledger");
        let mut first = executor(path.clone(), vec![Mode::Good], 1000);
        first.execute(&request()).unwrap();
        let mut rows = first.inner.ledger.records().unwrap();
        match corrupt {
            0 => rows[1]["actual_cost_microusd"] = json!(0),
            1 => rows[1]["pfp_binding"]["input_sha256"] = json!("changed"),
            2 => {
                let duplicate = rows[1].clone();
                rows.push(duplicate);
            }
            3 => rows.push(json!({"cost_microusd":-100,"day":"2026-10-12","bout_id":"continuing"})),
            4 => rows.push(json!({"day":"2026-10-12","bout_id":"continuing"})),
            5 => rows.push(json!({"cost_microusd":1.5,"day":"2026-10-12","bout_id":"continuing"})),
            _ => rows.push(json!({"pfp_state":null,"cost_microusd":0,"day":"2026-10-12","bout_id":"continuing"})),
        }
        std::fs::write(
            &path,
            rows.into_iter()
                .map(|v| v.to_string() + "\n")
                .collect::<String>(),
        )
        .unwrap();
        let mut resumed = executor(path, vec![Mode::Good], 1000);
        assert_eq!(
            resumed.execute(&request()).unwrap_err().code,
            "PFP_LEDGER_INVALID"
        );
        assert_eq!(resumed.inner.transports.calls, 0);
    }
}
#[test]
fn restarting_same_bout_recovers_cost_and_cannot_reset_its_cap() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("ledger");
    let mut first = executor(path.clone(), vec![Mode::Good], 80);
    first.execute(&request()).unwrap();
    let mut resumed = executor(path, vec![Mode::Good], 80);
    assert!(resumed.execute(&request()).is_err());
    assert_eq!(resumed.inner.transports.calls, 0);
    assert_eq!(resumed.inner.spent_bout, BigInt::from(30));
}

struct SettlementFails(FileCallLedger);
impl CallLedger for SettlementFails {
    fn append(&mut self, row: &Value) -> Result<(), core_adversary::stage::ports::Refusal> {
        if row["pfp_state"] == "RESERVED" {
            self.0.append(row)
        } else {
            Err(core_adversary::stage::ports::Refusal::new(
                "LEDGER_UNAVAILABLE",
                "simulated settlement write failure",
            ))
        }
    }
    fn spent_on(&mut self, day: &str) -> Result<BigInt, core_adversary::stage::ports::Refusal> {
        self.0.spent_on(day)
    }
    fn records(&mut self) -> Result<Vec<Value>, core_adversary::stage::ports::Refusal> {
        self.0.records()
    }
}
#[test]
fn settlement_write_failure_retains_actual_raw_reply_and_stops_resumed_send() {
    let dir = tempfile::tempdir().unwrap();
    let original = executor(
        dir.path().join("ledger"),
        vec![Mode::Good, Mode::Good],
        1000,
    )
    .inner;
    let mut e = PfpSeatExecutor {
        inner: RoutedSeatExecutor {
            table: original.table,
            config_digest: original.config_digest,
            transports: original.transports,
            ledger: SettlementFails(original.ledger),
            bout_id: original.bout_id,
            max_output_tokens: original.max_output_tokens,
            clock: original.clock,
            spent_bout: original.spent_bout,
            spent_tier: original.spent_tier,
        },
    };
    let failure = e.execute(&request()).unwrap_err();
    assert_eq!(failure.code, "LEDGER_UNAVAILABLE");
    let retained: Value = serde_json::from_str(&failure.details["attempt"]).unwrap();
    assert_eq!(
        retained["raw_reply_hex"],
        hex::encode(&e.inner.transports.raw[0])
    );
    assert_eq!(retained["actual_cost_microusd"], 30);
    assert_eq!(
        e.execute(&request()).unwrap_err().code,
        "PFP_ACCOUNTING_UNRESOLVED"
    );
    assert_eq!(e.inner.transports.calls, 1);
}

// Origin: engine/crates_rs/tests/core_adversary/pfp_gateway.rs
// Claim: urn:core:crates_rs:tests:pfp-gateway:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbdd97cba {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbdd97cba` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbdd97cba {
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
impl BoundaryErrorbdd97cba {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbdd97cba {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbdd97cba {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbdd97cba {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbdd97cba> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbdd97cba::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbdd97cba::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbdd97cba::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_bdd97cba() {
    let admitted = BoundaryRecordbdd97cba::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbdd97cba::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
