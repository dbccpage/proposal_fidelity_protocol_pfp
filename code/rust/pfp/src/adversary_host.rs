//! Native Adversary composition root. Domain execution stays behind its owned ports.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_03e6c976<T> {
    fn checked_invariant_03e6c976(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_03e6c976<T> for Option<T> {
    #[inline]
    fn checked_invariant_03e6c976(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_03e6c976<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_03e6c976(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::adversary_checker::{NativeC011Checker, SymbolGameRequest};
use chrono::Utc;
use num_bigint::BigInt;
use core_adversary::stage::ddc::DdcStep;
use core_adversary::stage::emission::{Clock, DdcSink, EmitterSuite, SgtSink};
use core_adversary::stage::file_adapters::{
    FileCemetery, FileFailureHistory, FileGenealogy, FilePackets, MemoryUns, MemoryUts,
};
use core_adversary::stage::packets::WorkPacket;
use core_adversary::stage::ports::{
    Refusal, SchedulerPort, SeatPort, SeatTurnReply, SeatTurnRequest,
};
use core_adversary::stage::scheduler::DeterministicScheduler;
use core_adversary::stage::synthetic_diagnostic::NativeSbeDiagnostic;
use core_adversary::providers::credentials::resolve_inherited_key;
use core_adversary::providers::request::CandidateRequest;
use core_adversary::providers::transport::{OpenRouterTransport, VerifiedHttpClient};
use core_adversary::authorization::AuthorizationTime;
use core_adversary::bout_boundary::{
    execute_captured_bout_boundary, BoutAbort, BoutRunSpec, RefusalBundlePort,
};
use core_adversary::checker_ports::CandidateCheckerPort;
use core_adversary::complete_bout::{
    execute_complete_bout, BoutHostPort, CompleteBoutInput, CompleteBoutPorts, GovernancePort,
    GovernanceRequest,
};
use core_adversary::council::{assemble_council_for, CouncilAssembly, PanelMode};
use core_adversary::gateway::{RoutedSeatExecutor, SeatPrompt, SeatTransport, TransportFailure};
use core_adversary::instruction_plan::InstructionPlanTransportV01;
use core_adversary::journal::{EntryKind, JournalEntry, JournalPort};
use core_adversary::journal_store::JsonlJournal;
use core_adversary::ledger::FileCallLedger;
use core_adversary::recovery::reconcile_crashed_bouts;
use core_adversary::render_record::{JsonStyle, RenderRecord};
use core_adversary::routing::{load_routing, RoutingTable};
use core_adversary::run_folder_store::RunFolderStore;
use core_adversary::run_persistence::{
    content_addressed_receipt_id_v2, dda_tape, persist_bout_run_folder_v2, run_directory_name,
    PersistenceInput, RUN_BUNDLE_V2,
};
use core_adversary::run_reporting::project_run_reports;
use core_adversary::scene_orchestration::SceneOrchestration;
use serde::Deserialize;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::cell::RefCell;
use std::collections::BTreeMap;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::rc::Rc;
use std::time::{Duration, Instant};

pub const REQUEST_DOMAIN: &str = "core.adversary.bout-input.v1";
fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_REQUEST_INVALID", message)
}

struct PreflightBoundScheduler;

fn preflight_already_bound() -> Refusal {
    Refusal::new(
        "SCHEDULER_PREFLIGHT_ALREADY_BOUND",
        "scheduler preflight state is already the run state",
    )
}

impl SchedulerPort for PreflightBoundScheduler {
    fn start(
        &mut self,
        _run_key: &str,
        _packet: &core_adversary::stage::packets::WorkPacket,
    ) -> Result<core_adversary::stage::run::SwarmRunState, Refusal> {
        Err(preflight_already_bound())
    }

    fn advance(
        &mut self,
        state: &core_adversary::stage::run::SwarmRunState,
        _result: &core_adversary::stage::packets::AgentResult,
        _progress: &core_adversary::stage::run::ProgressMeasure,
    ) -> Result<core_adversary::stage::run::SwarmRunState, Refusal> {
        if state.terminal_status() == "RUNNING" {
            let mut value = serde_json::to_value(state).map_err(|e| invalid(e.to_string()))?;
            value["terminal_status"] = serde_json::json!("COMPLETED");
            value["state_id"] = serde_json::json!("");
            serde_json::from_value(value).map_err(|e| invalid(e.to_string()))
        } else {
            Ok(state.clone())
        }
    }
}
fn provider_error(error: core_adversary::providers::Refusal) -> Refusal {
    Refusal::new(&error.code, error.message)
}
fn record(value: &Value) -> Result<RenderRecord, Refusal> {
    RenderRecord::from_json(&value.to_string())
}
fn encoded<T: serde::Serialize>(value: &T) -> Result<Value, Refusal> {
    serde_json::to_value(value).map_err(|e| invalid(e.to_string()))
}
fn yes() -> bool {
    true
}
fn four() -> i64 {
    4
}
fn verify_live_execution_binding(request: &Request) -> Result<(), Refusal> {
    let bound = request
        .carrier_context
        .get("live_execution")
        .ok_or_else(|| invalid("signed live execution settings required"))?;
    let executable = std::env::current_exe().map_err(io_failure)?;
    let config_bytes = fs::read(&request.config_path).map_err(io_failure)?;
    let exe_bytes = fs::read(executable).map_err(io_failure)?;
    let actual = json!({
        "provider":"openrouter", "model":request.model_override,
        "routing_config_sha256":format!("sha256:{}", hex::encode(Sha256::digest(config_bytes))),
        "max_cost_microusd":request.max_cost_microusd,
        "max_output_tokens":request.max_output_tokens,
        "selected_characters":request.selected_characters,
        "panel_mode":request.panel_mode,
        "output_dir":request.adversary_output_dir.to_string_lossy(),
        "case_sha256":request.symbol_game_request.as_ref().map(SymbolGameRequest::case_digest),
        "native_host_sha256":hex::encode(Sha256::digest(exe_bytes))
    });
    if bound != &actual || request.max_cost_microusd.is_none_or(|v| v == 0) {
        return Err(invalid(
            "executing native host, routing, role, checker or budget differs from signed live settings",
        ));
    }
    Ok(())
}

fn require_live_instruction_plan(request: &Request) -> Result<(), Refusal> {
    if !request.live {
        return Ok(());
    }
    let plan = request.instruction_plan.as_ref().ok_or_else(|| {
        Refusal::new(
            "NATIVE_INSTRUCTION_PLAN_UNBOUND",
            "live Adversary requires an operator-signed instruction plan",
        )
    })?;
    let admission = request.instruction_admission.as_ref().ok_or_else(|| {
        Refusal::new(
            "NATIVE_INSTRUCTION_ADMISSION_UNBOUND",
            "native signature and source custody required",
        )
    })?;
    admission.verify(&request.repo_root, plan, &json!({
        "task_key":request.task_key,"objective":request.objective,"max_rounds":request.max_rounds,
        "fixture_mode":!request.live,"request_external_admission":request.request_external_admission,
        "carrier_context":request.carrier_context,"ablation_flags":request.ablation_flags,
        "compute_budget":request.compute_budget,"swarm_type":request.swarm_type,"authority_effect":"None"
    }))?;
    verify_live_execution_binding(request)
}
fn default_budget() -> u64 {
    50
}
fn default_tokens() -> u64 {
    4096
}
fn default_swarm_type() -> String {
    "open-topic".into()
}
fn default_panel_mode() -> String {
    PanelMode::Core.as_str().into()
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    task_key: String,
    objective: String,
    repo_root: PathBuf,
    adversary_output_dir: PathBuf,
    resources_root: PathBuf,
    ledger_path: PathBuf,
    bout_id: String,
    config_path: PathBuf,
    #[serde(default)]
    live: bool,
    #[serde(default)]
    env_file: Option<PathBuf>,
    #[serde(default = "four")]
    max_rounds: i64,
    #[serde(default)]
    request_external_admission: bool,
    #[serde(default)]
    journal_path: Option<PathBuf>,
    #[serde(default)]
    carrier_context: Map<String, Value>,
    #[serde(default)]
    ablation_flags: Map<String, Value>,
    #[serde(default)]
    learning_guidance: String,
    #[serde(default)]
    instruction_plan: Option<InstructionPlanTransportV01>,
    #[serde(default)]
    instruction_admission: Option<crate::adversary_live_admission::LiveAdmission>,
    #[serde(default = "default_budget")]
    compute_budget: u64,
    #[serde(default = "default_tokens")]
    max_output_tokens: u64,
    #[serde(default)]
    max_cost_microusd: Option<u64>,
    #[serde(default = "default_swarm_type")]
    swarm_type: String,
    #[serde(default)]
    selected_characters: Option<Vec<String>>,
    /// `core` (the default) or `full`; see `core_adversary::council::PanelMode`.
    #[serde(default = "default_panel_mode")]
    panel_mode: String,
    #[serde(default)]
    symbol_game_request: Option<SymbolGameRequest>,
    #[serde(default)]
    model_override: Option<String>,
    #[serde(default = "yes")]
    inherit_environment: bool,
    /// Swarm run state from the Python live scheduler preflight. Absent for a direct bout.
    #[serde(default)]
    scheduler_preflight: Option<Value>,
}
struct RuntimeClock {
    start: Instant,
}
impl Clock for RuntimeClock {
    fn timestamp_utc(&self) -> String {
        Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string()
    }
}
impl core_adversary::gateway::Clock for RuntimeClock {
    fn today(&self) -> String {
        Utc::now().format("%Y-%m-%d").to_string()
    }
    fn milliseconds(&self) -> u64 {
        u64::try_from(self.start.elapsed().as_millis()).unwrap_or(u64::MAX)
    }
}
struct ProviderSeatTransport(Option<OpenRouterTransport<VerifiedHttpClient>>);
impl SeatTransport for ProviderSeatTransport {
    fn configured(&self, router: &str) -> bool {
        router == "openrouter" && self.0.is_some()
    }
    fn send_bound(
        &mut self,
        router: &str,
        model: &str,
        prompt: &SeatPrompt,
        max_tokens: u64,
    ) -> Result<core_adversary::gateway::SeatTransportOutcome, TransportFailure> {
        if router != "openrouter" {
            return Err(TransportFailure {
                kind: "RouterUnavailable".into(),
            });
        }
        let transport = self.0.as_mut().ok_or_else(|| TransportFailure {
            kind: "TransportUnavailable".into(),
        })?;
        transport
            .send_with_status(
                model,
                &CandidateRequest {
                    system: prompt.system.clone(),
                    user: prompt.user.clone(),
                    ..CandidateRequest::default()
                },
                max_tokens,
            )
            .map(|reply| core_adversary::gateway::SeatTransportOutcome {
                raw: reply.body,
                status: reply.status,
                truncated: reply.truncated,
            })
            .map_err(|failure| TransportFailure { kind: failure.code })
    }
    fn send(
        &mut self,
        router: &str,
        model: &str,
        prompt: &SeatPrompt,
        max_tokens: u64,
    ) -> Result<Vec<u8>, TransportFailure> {
        if router != "openrouter" {
            return Err(TransportFailure {
                kind: "RouterUnavailable".into(),
            });
        }
        let transport = self.0.as_mut().ok_or_else(|| TransportFailure {
            kind: "TransportUnavailable".into(),
        })?;
        transport
            .send(
                model,
                &CandidateRequest {
                    system: prompt.system.clone(),
                    user: prompt.user.clone(),
                    ..CandidateRequest::default()
                },
                max_tokens,
            )
            .map_err(|failure| TransportFailure { kind: failure.code })
    }
}

#[derive(Default)]
struct TurnGeometry {
    role_id: String,
    attempts: Vec<Value>,
}

fn density_observation(raw: &[u8], dim: usize, role: &str, field: &str, trust: &str) -> Value {
    let report = engines::quantum::prompt_density::observe(raw, dim, role, field, trust);
    serde_json::to_value(report).unwrap_or_else(|error| {
        json!({
        "schema_version":"core.prompt-density.v1", "profile":"ordered-sha256-density-v1",
        "status":"UNAVAILABLE", "reason":error.to_string(), "dim":dim,
        "source_sha256":format!("sha256:{}",hex::encode(Sha256::digest(raw))),
        "source_bytes":raw.len(), "role_id":role, "field":field, "trust_level":trust,
        "entropy_bits":null, "purity":null, "effective_rank":null, "numerical_rank":null,
        "spans":[],"factors":[],"weights":[],"spectrum":[],"spectrum_tolerance":1e-10,
        "authority_effect":"None"})
    })
}

/// Records the actual final PFP transport inputs and captured bytes. The shared
/// cell is scoped to one sequential seat call; it neither schedules nor sends.
struct ObservedSeatTransport<T> {
    inner: T,
    dimension: usize,
    observed: Rc<RefCell<TurnGeometry>>,
}
impl<T: SeatTransport> SeatTransport for ObservedSeatTransport<T> {
    fn configured(&self, router: &str) -> bool {
        self.inner.configured(router)
    }

    fn send_bound(
        &mut self,
        router: &str,
        model: &str,
        prompt: &SeatPrompt,
        max_tokens: u64,
    ) -> Result<core_adversary::gateway::SeatTransportOutcome, TransportFailure> {
        let role = self.observed.borrow().role_id.clone();
        let mut observation = json!({"router":router,"requested_model":model,
            "pfp_prepared_prompts":{"system":prompt.system,"user":prompt.user},
            "density":{
                "system":density_observation(prompt.system.as_bytes(),self.dimension,&role,"pfp.system","host-assembled"),
                "user":density_observation(prompt.user.as_bytes(),self.dimension,&role,"pfp.user","mixed-source")},
            "authority_effect":"None"});
        let result = self.inner.send_bound(router, model, prompt, max_tokens);
        match &result {
            Ok(reply) => {
                observation["http_status"] = json!(reply.status);
                observation["truncated"] = json!(reply.truncated);
                observation["density"]["provider_wire"] = density_observation(
                    &reply.raw,
                    self.dimension,
                    &role,
                    "provider.raw_reply",
                    "untrusted-provider",
                );
                observation["raw_capture"] = json!({"source_sha256":format!("sha256:{}",hex::encode(Sha256::digest(&reply.raw))),
                    "source_bytes":reply.raw.len(),"location":"existing pfp_evidence / rejected_attempts / attempt ledger"});
                if let Ok(provider) = core_adversary::stage::strict_json::parse(&reply.raw) {
                    if let Some(content) = provider
                        .pointer("/choices/0/message/content")
                        .and_then(Value::as_str)
                    {
                        observation["density"]["reply"] = density_observation(
                            content.as_bytes(),
                            self.dimension,
                            &role,
                            "pfp.raw_reply",
                            "untrusted-model",
                        );
                    }
                }
            }
            Err(failure) => {
                observation["transport_error"] = json!(failure.kind);
                observation["reply_status"] = json!("UNAVAILABLE");
            }
        }
        self.observed.borrow_mut().attempts.push(observation);
        result
    }

    fn send(
        &mut self,
        router: &str,
        model: &str,
        prompt: &SeatPrompt,
        max_tokens: u64,
    ) -> Result<Vec<u8>, TransportFailure> {
        self.send_bound(router, model, prompt, max_tokens)
            .map(|reply| reply.raw)
    }
}

struct SelectedSeats<'a> {
    inner: &'a mut dyn SeatPort,
    allowed: Option<Vec<String>>,
    dimension: usize,
    observed: Rc<RefCell<TurnGeometry>>,
}
impl SeatPort for SelectedSeats<'_> {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        if self
            .allowed
            .as_ref()
            .is_some_and(|ids| !ids.contains(&request.seat_id))
        {
            return Err(Refusal::new(
                "ADVERSARY_ROLE_NOT_SELECTED",
                format!("{} is outside selected roles", request.seat_id),
            ));
        }
        {
            let mut observation = self.observed.borrow_mut();
            observation.role_id = request.seat_id.clone();
            observation.attempts.clear();
        }
        let mut result = self.inner.execute_turn(request);
        let attempts = std::mem::take(&mut self.observed.borrow_mut().attempts);
        let observations = if attempts.is_empty() {
            // Fixture and pre-dispatch paths have no final provider envelope.
            let mut observation = json!({"capture_kind":"HOST_ONLY_OR_PRE_DISPATCH",
                "provider_dispatch_observed":false,"density":{
                    "request":density_observation(request.prompt_text.as_bytes(),self.dimension,
                        &request.seat_id,"seat.request","mixed-source")},"authority_effect":"None"});
            if let Ok(reply) = &result {
                observation["density"]["reply"] = density_observation(
                    &reply.raw_bytes,
                    self.dimension,
                    &request.seat_id,
                    "seat.captured_reply",
                    "untrusted-worker",
                );
            }
            vec![observation]
        } else {
            attempts
        };
        match &mut result {
            Ok(reply) => {
                reply
                    .parameters
                    .get_or_insert_with(BTreeMap::new)
                    .insert("density_attempts".into(), json!(observations));
            }
            Err(refusal) => {
                refusal
                    .details
                    .insert("density_attempts".into(), json!(observations).to_string());
            }
        }
        result
    }
}
struct RuntimeTransitions {
    cemetery: FileCemetery,
    intergates: Map<String, Value>,
    task_key: String,
    history: Vec<String>,
    request_digest: String,
    candidate_bindings: BTreeMap<String, String>,
}
impl RuntimeTransitions {
    fn validate_candidate_binding(
        &self,
        stage: &str,
        id: &str,
        raw_digest: &str,
        seen: &mut std::collections::BTreeSet<String>,
    ) -> Result<(), Refusal> {
        let missing_pre =
            stage == "PRE_SELECTION" && self.candidate_bindings.get(id) != Some(&raw_digest.to_owned());
        let mismatched = self
            .candidate_bindings
            .get(id)
            .is_some_and(|expected| expected != raw_digest);
        if !seen.insert(id.to_owned()) || missing_pre || mismatched {
            return Err(invalid("candidate stage occurrence/raw binding changed"));
        }
        Ok(())
    }

    fn evaluate_candidate_stage_row(
        &mut self,
        stage: &str,
        snapshot: &Value,
        row: &Value,
        seen: &mut std::collections::BTreeSet<String>,
    ) -> Result<Value, Refusal> {
        let hash = |raw: &[u8]| format!("sha256:{}", hex::encode(Sha256::digest(raw)));
        let id = row["candidate_id"]
            .as_str()
            .ok_or_else(|| invalid("candidate ID absent"))?;
        let content = row["content"]
            .as_str()
            .ok_or_else(|| invalid("candidate bytes absent"))?;
        let raw_digest = hash(content.as_bytes());
        self.validate_candidate_binding(stage, id, &raw_digest, seen)?;
        let mut subject = json!({"schema_version":"core.antiskill.subject.v1","claim_scope":["candidate_patch"],
            "evidence_scope":[format!("task:{}",self.task_key),format!("request:{}",self.request_digest),
                format!("candidate:{raw_digest}"),format!("candidate_id:{id}"),format!("stage:{stage}")],"producer_identity":"adversary.native.candidate_production",
            "verifier_identity":"unbound","claim_mode":"PROPOSAL","requested_effect":"NONE",
            "approval_reference":"","nonclaims":["Detector evidence never supplies admission or truth."],"authority_effect":"None"});
        subject["subject_id"] = json!(hash(
            json!({"domain":"core.antiskill.subject.v1","payload":subject})
                .to_string()
                .as_bytes()
        ));
        let raw = subject.to_string();
        let decision = crate::anti_skill_host::execute(&json!({"schema_version":"core.native.anti-skill-request.v1",
            "operation":"evaluate","task_key":self.task_key,"stage":stage,"subject_id":subject["subject_id"],
            "subject_json":raw,"subject_raw_sha256":hash(raw.as_bytes()),"registry_id":snapshot["registry_id"],
            "activation_profile_digest":snapshot["activation_profile_digest"],"implementation_digest":snapshot["implementation_digest"]
        })).map_err(invalid)?;
        if decision["disposition"] != "CLEAR" || decision["hit_ids"] != json!([]) {
            return Err(Refusal::new(
                "NATIVE_CANDIDATE_STAGE_REFUSED",
                "candidate detector did not clear",
            ));
        }
        if stage == "POST_PRODUCTION" {
            self.candidate_bindings.insert(id.into(), raw_digest.clone());
        }
        Ok(json!({"candidate_id":id,"candidate_raw_sha256":raw_digest,"decision":decision}))
    }

    fn candidate_stage(&mut self, value: &Value) -> Result<Value, Refusal> {
        let stage = value["stage"]
            .as_str()
            .filter(|s| ["POST_PRODUCTION", "PRE_SELECTION"].contains(s))
            .ok_or_else(|| invalid("candidate stage invalid"))?;
        let candidates = value["candidates"]
            .as_array()
            .filter(|rows| rows.len() <= 128)
            .ok_or_else(|| invalid("bounded candidate stage rows absent"))?;
        let snapshot = crate::anti_skill_host::execute(
            &json!({"schema_version":"core.native.anti-skill-request.v1",
            "operation":"describe"}),
        )
        .map_err(invalid)?;
        let mut decisions = Vec::new();
        let mut seen = std::collections::BTreeSet::new();
        for row in candidates {
            decisions.push(self.evaluate_candidate_stage_row(stage, &snapshot, row, &mut seen)?);
        }
        Ok(
            json!({"action":"anti_skill_candidate_stage","task_key":self.task_key,"stage":stage,
            "request_digest":self.request_digest,"decisions":decisions,"authority_effect":"None"}),
        )
    }

    fn screen_candidate_regressions(&mut self, value: &Value) -> Result<(), Refusal> {
        let rows = value["candidates"]
            .as_array()
            .ok_or_else(|| invalid("candidate screen payload absent"))?;
        for headstone in self.cemetery.load_headstones()? {
            let old = headstone.input();
            let regressed = rows.iter().any(|row| {
                row["candidate_id"] == old.candidate_id
                    || row["content_sha256"].as_str()
                        == Some(old.candidate_payload_sha256.as_str())
            });
            if regressed {
                return Err(Refusal::new(
                    "ADVERSARY_KNOWN_REGRESSION",
                    "candidate matches retained cemetery evidence",
                ));
            }
        }
        Ok(())
    }

    fn evaluate_transition_intergate(&self, edge: &str, row: &Value) -> Result<Value, Refusal> {
        if row["required"].as_bool().is_none() {
            return Err(invalid("required must be an explicit boolean"));
        }
        let id = row["intergate_id"]
            .as_str()
            .ok_or_else(|| invalid("intergate ID absent"))?;
        let payload = row
            .get("payload")
            .ok_or_else(|| invalid("intergate payload absent"))?;
        let evaluated = core_adversary::intergates::evaluate(id, payload, &self.history)?;
        if row["required"] == true && evaluated["status"] != "PASS" {
            return Err(Refusal::new(
                "ADVERSARY_INTERGATE_BLOCKED",
                format!("required intergate {id} did not clear {edge}"),
            ));
        }
        Ok(evaluated)
    }

    fn record_transition(&mut self, value: &Value) -> Result<Vec<Value>, Refusal> {
        let edge = value["edge"]
            .as_str()
            .ok_or_else(|| invalid("transition edge absent"))?;
        if edge.is_empty() || edge.len() > 256 || self.history.len() >= 64 {
            return Err(invalid(
                "runtime transition history is bounded to 64 nonempty edges of 256 bytes",
            ));
        }
        self.history.push(edge.to_owned());
        let Some(configured) = self.intergates.get(edge).cloned() else {
            return Ok(Vec::new());
        };
        let rows = configured
            .as_array()
            .ok_or_else(|| invalid("intergate edge must contain a bounded list"))?;
        if rows.len() > 10 {
            return Err(invalid("at most ten intergates per transition"));
        }
        rows.iter()
            .map(|row| self.evaluate_transition_intergate(edge, row))
            .collect()
    }
}
impl BoutHostPort for RuntimeTransitions {
    fn execute(&mut self, request: &[u8]) -> Result<Value, Refusal> {
        let value: Value = serde_json::from_slice(request).map_err(|e| invalid(e.to_string()))?;
        if value["authority_effect"] != "None" || value["task_key"] != self.task_key {
            return Err(invalid("transition authority or task binding differs"));
        }
        let mut diagnostics = Vec::new();
        match value["action"].as_str() {
            Some("anti_skill_candidate_stage") => return self.candidate_stage(&value),
            Some("candidate_regression_screen") => self.screen_candidate_regressions(&value)?,
            Some("transition") => diagnostics = self.record_transition(&value)?,
            Some("bout_start" | "gate_authorization_record") => {}
            _ => return Err(invalid("unsupported runtime host action")),
        }
        Ok(
            json!({"action":value["action"],"edge":value["edge"],"status":"CLEAR","diagnostics":diagnostics,"edge_history":self.history,"authority_effect":"None"}),
        )
    }
}
struct FixtureSeats;
impl SeatPort for FixtureSeats {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal> {
        let critic =
            request.scene_id == "act2_panel_debate" && request.seat_id == "seat_defect_hunter";
        let prefix =
            "```machine\nAUTHORITY_EFFECT=None\nRESIDUAL_COLOUR=Open\nDISPOSITION=PASS\n```\n";
        let reply_text = if critic {
            format!("{prefix}Deterministic fixture critique: no counterexample search was run.\n```critique\n{{\"blocking\": false, \"counterexample\": null}}\n```")
        } else {
            format!("{prefix}Deterministic fixture turn completed.")
        };
        Ok(SeatTurnReply {
            reply_text,
            machine_fields: BTreeMap::from([
                ("AUTHORITY_EFFECT".into(), "None".into()),
                ("RESIDUAL_COLOUR".into(), "Open".into()),
                ("DISPOSITION".into(), "PASS".into()),
            ]),
            residual_colour: "Open".into(),
            authority_effect: "None".into(),
            raw_bytes: if critic {
                b"deterministic_fixture_critique".to_vec()
            } else {
                b"deterministic_fixture".to_vec()
            },
            model: None,
            provider: None,
            parameters: None,
            usage: None,
            request_digest: Some(request.request_digest()?),
        })
    }
}
struct Governance {
    root: PathBuf,
}
const GOVERNANCE_SOURCE_BINDING_VERSION: &str = "core.adversary.governance-source-binding.v1";
const GOVERNANCE_SOURCE_SCOPE: &str = "source_byte_custody_only";
// Historical role IDs remain wire-compatible; only their canonical sources move.
const GOVERNANCE_SOURCE_BINDINGS_V1: [(&str, &str); 4] = [
    ("governance-symbol-game", "governance-pfp"),
    ("governance-ddc", "governance-wdp"),
    ("governance-coda", "governance-wdp"),
    ("governance-clean-arch", "governance-clean-arch"),
];
impl GovernancePort for Governance {
    fn resolve_and_verify(&mut self, request: &GovernanceRequest<'_>) -> Result<Value, Refusal> {
        use core_types::python_unicode::lowercase;
        let objective = lowercase(request.objective);
        let task = lowercase(request.task_key);
        let flags = [
            true,
            !request.letter_tape.is_empty(),
            ["coda", "foc", "mur", "cs_q", "gtla", "sentinel"]
                .iter()
                .any(|s| objective.contains(s) || task.contains(s)),
            [
                "clean_arch",
                "bounded_context",
                "refactor",
                "code",
                "architecture",
            ]
            .iter()
            .any(|s| objective.contains(s) || task.contains(s)),
        ];
        let mut bundle = Vec::new();
        let source_root = self
            .root
            .canonicalize()
            .map_err(|e| Refusal::new("GOVERNANCE_BUNDLE_UNREADABLE", e.to_string()))?;
        for ((skill, source), active) in GOVERNANCE_SOURCE_BINDINGS_V1.into_iter().zip(flags) {
            let primary = self
                .root
                .join(".agents/skills")
                .join(source)
                .join("SKILL.md");
            let path = primary
                .canonicalize()
                .map_err(|e| Refusal::new("GOVERNANCE_BUNDLE_UNREADABLE", e.to_string()))?;
            if !path.starts_with(&source_root) {
                return Err(Refusal::new(
                    "GOVERNANCE_BUNDLE_SOURCE_CUSTODY_INVALID",
                    "governance source escapes its declared root",
                ));
            }
            let digest =
                hex::encode(Sha256::digest(fs::read(&path).map_err(|e| {
                    Refusal::new("GOVERNANCE_BUNDLE_UNREADABLE", e.to_string())
                })?));
            if digest == "0".repeat(64) {
                return Err(Refusal::new(
                    "GOVERNANCE_BUNDLE_SOURCE_CUSTODY_INVALID",
                    "zero source digest is unavailable evidence",
                ));
            }
            // PASS confirms these source bytes were read; it conveys no checker
            // execution, authority, or admission decision.
            bundle.push(json!({
                "skill_id":skill,"source_skill_id":source,
                "source_path":format!(".agents/skills/{source}/SKILL.md"),
                "source_binding_version":GOVERNANCE_SOURCE_BINDING_VERSION,
                "verification_scope":GOVERNANCE_SOURCE_SCOPE,
                "digest":digest,"result":if active {"PASS"} else {"N_A"}
            }));
        }
        Ok(Value::Array(bundle))
    }
}
fn io_failure(error: impl std::fmt::Display) -> Refusal {
    Refusal::new("ADVERSARY_STORE_UNAVAILABLE", error.to_string())
}
fn append(path: &Path, bytes: &[u8]) -> Result<(), Refusal> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(io_failure)?;
    }
    let mut file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(io_failure)?;
    file.write_all(bytes).map_err(io_failure)?;
    file.sync_all().map_err(io_failure)
}

/// Single-run working projection of the existing captured history. The journal
/// remains the dispatch guard; a report failure never changes a seat outcome.
struct ReportingJournal {
    inner: JsonlJournal,
    working_root: PathBuf,
    directory: Option<PathBuf>,
    history: Value,
    has_outcome: bool,
}
impl ReportingJournal {
    fn new(inner: JsonlJournal, output: &Path, history: Value) -> Self {
        Self {
            inner,
            working_root: output.join("working"),
            directory: None,
            history,
            has_outcome: false,
        }
    }
    fn atomic(path: &Path, raw: &[u8]) -> Result<(), Refusal> {
        let parent = path
            .parent()
            .ok_or_else(|| io_failure("report path has no parent"))?;
        let mut file = tempfile::NamedTempFile::new_in(parent).map_err(io_failure)?;
        file.write_all(raw).map_err(io_failure)?;
        file.as_file().sync_all().map_err(io_failure)?;
        file.persist(path).map_err(io_failure)?;
        Ok(())
    }
    fn ensure_working_directory(&mut self) -> Result<PathBuf, Refusal> {
        if self.directory.is_none() {
            fs::create_dir_all(&self.working_root).map_err(io_failure)?;
            // Repeated caller bout IDs cannot overwrite a previous run's bytes.
            let directory = tempfile::Builder::new()
                .prefix("native-")
                .tempdir_in(&self.working_root)
                .map_err(io_failure)?
                .keep();
            self.directory = Some(directory);
        }
        Ok(self
            .directory
            .as_ref()
            .checked_invariant_03e6c976("working directory created")
            .clone())
    }
    fn write_reports(&mut self) -> Result<(), Refusal> {
        let directory = self.ensure_working_directory()?;
        let raw = serde_json::to_vec_pretty(&self.history).map_err(io_failure)?;
        Self::atomic(&directory.join("state.json"), &raw)?;
        let status = self
            .history
            .get("status")
            .and_then(Value::as_str)
            .unwrap_or("INCOMPLETE");
        let verdict = self
            .history
            .get("terminal_verdict")
            .cloned()
            .unwrap_or_else(|| json!("UNVERIFIED"));
        let reports = project_run_reports(
            &self.history,
            &json!({"work_status":status,"checkpoint_finalized":false,"evidence_verdict":verdict}),
            "state.json",
        )?;
        let mut files = Map::new();
        files.insert(
            "state.json".into(),
            json!(hex::encode(Sha256::digest(&raw))),
        );
        for (name, key) in [("novella.md", "novella_md"), ("uts.jsonl", "uts_jsonl")] {
            let content = reports[key]
                .as_str()
                .ok_or_else(|| io_failure("report projection missing"))?;
            Self::atomic(&directory.join(name), content.as_bytes())?;
            files.insert(
                name.into(),
                json!(hex::encode(Sha256::digest(content.as_bytes()))),
            );
        }
        let marker = json!({"schema_version":"core.adversary.native-reporting-status.v1",
            "status":"MATERIALIZED","work_status":status,"source_sha256":reports["source_sha256"],
            "files":files,"task_outcome_changed":false,"authority_effect":"None"});
        Self::atomic(
            &directory.join("reporting.json"),
            marker.to_string().as_bytes(),
        )
    }
    fn publish(&mut self) -> Result<(), Refusal> {
        if let Err(failure) = self.write_reports() {
            let mut refusal = Refusal::new("ADVERSARY_REPORTING_FAILED", failure.message);
            if let Some(directory) = &self.directory {
                refusal.details.insert(
                    "working_checkpoint".into(),
                    directory.to_string_lossy().into(),
                );
                let marker = json!({"schema_version":"core.adversary.native-reporting-status.v1",
                    "status":"REPORTING_FAILED","detail":refusal.message,
                    "state_path":directory.join("state.json"),"task_outcome_changed":false,
                    "retry":"Reproject the retained state.json through project_run_reports",
                    "authority_effect":"None"});
                let _ = Self::atomic(
                    &directory.join("reporting.json"),
                    marker.to_string().as_bytes(),
                );
            }
            return Err(refusal);
        }
        Ok(())
    }
}
impl JournalPort for ReportingJournal {
    fn append(&mut self, entry: &JournalEntry) -> Result<(), Refusal> {
        self.inner.append(entry)?;
        if entry.kind == EntryKind::BoutTerminal {
            if let Some((_, status)) = entry
                .detail
                .iter()
                .find(|(key, _)| key == "terminal_status")
            {
                if self.has_outcome {
                    self.history["terminal_status"] = json!(status);
                } else {
                    self.history["status"] = json!(status);
                }
            }
        }
        Ok(())
    }
    fn read_all(&self) -> Result<Vec<JournalEntry>, Refusal> {
        self.inner.read_all()
    }
    fn checkpoint(
        &mut self,
        turns: &[Map<String, Value>],
        pending: Option<&Map<String, Value>>,
    ) -> Result<(), Refusal> {
        if self.has_outcome {
            return self.publish();
        }
        self.history["seat_turns"] = json!(turns);
        self.history["pending_prompt"] = pending.map(|pending| {
            let mut record = pending.clone();
            if let Some(prompt) = record.remove("prompt_text") {
                record.insert("user".into(), prompt);
            }
            record.insert("status".into(), json!("PENDING_SEAT_REQUEST"));
            record.insert("capture_scope".into(), json!("Recorded seat input; provider preparation and execution are not established"));
            Value::Object(record)
        }).unwrap_or(Value::Null);
        self.publish()
    }
    fn checkpoint_outcome(&mut self, summary: &Value) -> Result<(), Refusal> {
        self.history = summary.clone();
        self.has_outcome = true;
        self.publish()
    }
}

fn step_records(steps: &[DdcStep]) -> Result<Vec<RenderRecord>, Refusal> {
    steps.iter().map(|s| record(&encoded(s)?)).collect()
}
struct DdcStore {
    path: PathBuf,
    steps: Vec<DdcStep>,
    shared: Rc<RefCell<Vec<DdcStep>>>,
}
impl DdcSink for DdcStore {
    fn record_step(&mut self, step: &DdcStep) -> Result<String, Refusal> {
        let before = dda_tape(&step_records(&self.steps)?)?.bytes.len();
        let mut next = self.steps.clone();
        next.push(step.clone());
        let tape = dda_tape(&step_records(&next)?)?;
        append(&self.path, &tape.bytes[before..])?;
        self.steps = next;
        *self.shared.borrow_mut() = self.steps.clone();
        Ok(tape.head_sha256.unwrap_or_default())
    }
    fn recorded_steps(&self) -> Option<&[DdcStep]> {
        Some(&self.steps)
    }
    fn recorded_step_count(&self) -> Option<usize> {
        Some(self.steps.len())
    }
}
struct Bundles {
    root: PathBuf,
    steps: Rc<RefCell<Vec<DdcStep>>>,
    preparation: Value,
}
impl Bundles {
    fn build_refusal_summary(
        &self,
        spec: &BoutRunSpec,
        refusal: &Refusal,
        act: &str,
        turns: &[Map<String, Value>],
    ) -> Result<(Value, &'static str, String), Refusal> {
        let captured = json!({"act_reached":act,"refusal":refusal,"seat_turns":turns});
        let tag = hex::encode(Sha256::digest(
            record(&captured)?
                .json(JsonStyle::SpacedSortedAscii)?
                .as_bytes(),
        ));
        let mut summary = captured;
        let status = if refusal.code == "ADVERSARY_BOUT_INTERRUPTED" {
            "INTERRUPTED"
        } else {
            "REFUSED"
        };
        let fields = summary
            .as_object_mut()
            .ok_or_else(|| invalid("refusal summary must be an object"))?;
        fields.extend(Map::from_iter([
            ("authority_effect".into(), json!("None")),
            ("is_authorized".into(), json!(false)),
            ("objective".into(), json!(spec.objective)),
            ("selected_candidate_id".into(), json!("")),
            ("status".into(), json!(status)),
            ("task_key".into(), json!(spec.task_key)),
            ("terminal_status".into(), json!(status)),
        ]));
        summary["bundle_schema"] = json!("core.adversary.run-bundle.v2");
        summary["bundle_schema_version"] = json!(RUN_BUNDLE_V2);
        summary["forge"] = self.preparation.clone();
        summary["original_seed"] = json!(spec.objective);
        if let Some(plan) = &spec.instruction_plan {
            summary["instruction_plan"] = json!(plan);
        }
        Ok((summary, status, tag))
    }

    fn build_refusal_receipt(
        spec: &BoutRunSpec,
        refusal: &Refusal,
        status: &str,
        receipt_id: &str,
    ) -> Result<RenderRecord, Refusal> {
        let mut receipt_value = json!({"authority_effect":"None","receipt_id":receipt_id,"refusal_code":refusal.code,
            "schema":"core.adversary.refusal-bundle.v2","bundle_schema_version":RUN_BUNDLE_V2,
            "selected_candidate_id":"","status":status,"task_key":spec.task_key});
        if let Some(plan) = &spec.instruction_plan {
            receipt_value["instruction_plan_digest"] = json!(plan.plan_digest);
            receipt_value["instruction_manifest_digest"] = json!(plan.manifest_digest);
            receipt_value["ordered_bodies_digest"] = json!(plan.ordered_bodies_digest);
        }
        record(&receipt_value)
    }

    fn project_refusal_reports(summary: &Value, status: &str) -> Result<(String, String), Refusal> {
        let reports = project_run_reports(
            summary,
            &json!({"work_status":status,"checkpoint_finalized":true,
            "evidence_verdict":"UNVERIFIED"}),
            "summary.json",
        )?;
        let novella = reports["novella_md"]
            .as_str()
            .ok_or_else(|| invalid("native UNS missing"))?
            .to_owned();
        let uts = reports["uts_jsonl"]
            .as_str()
            .ok_or_else(|| invalid("native UTS missing"))?
            .to_owned();
        Ok((novella, uts))
    }
}
impl RefusalBundlePort for Bundles {
    fn persist(
        &mut self,
        spec: &BoutRunSpec,
        refusal: &Refusal,
        act: &str,
        turns: &[Map<String, Value>],
    ) -> Result<String, Refusal> {
        let (mut summary, status, tag) = self.build_refusal_summary(spec, refusal, act, turns)?;
        let steps = step_records(&self.steps.borrow())?;
        let (novella, uts) = Self::project_refusal_reports(&summary, status)?;
        let receipt_id =
            content_addressed_receipt_id_v2(&novella, &steps, &record(&summary)?, &uts)?;
        summary["receipt_id"] = json!(receipt_id);
        let receipt = Self::build_refusal_receipt(spec, refusal, status, &receipt_id)?;
        let folder = format!(
            "{}--refused-{}",
            run_directory_name(&spec.task_key)?,
            &tag[..12]
        );
        persist_bout_run_folder_v2(
            &PersistenceInput {
                run_key: &folder,
                receipt: &receipt,
                novella_md: &novella,
                dda_steps: &steps,
                summary_data: &record(&summary)?,
            },
            &uts,
            &mut RunFolderStore::new(self.root.clone()),
        )
    }
}
fn council_directory(resources: &Path) -> PathBuf {
    let canonical = resources.join("adversary/roles");
    if canonical.is_dir() {
        canonical
    } else {
        resources.join("governance/roles")
    }
}
fn selected_seat_ids(request: &Request) -> Option<Vec<String>> {
    request.selected_characters.as_ref().map(|characters| {
        characters
            .iter()
            .map(|name| format!("seat_{}", core_adversary::routing::canonical_seat_key(name)))
            .collect()
    })
}
fn has_valid_intergate_fields(fields: &Map<String, Value>, id: &str) -> bool {
    let valid_keys = fields
        .keys()
        .all(|key| ["intergate_id", "payload", "required"].contains(&key.as_str()));
    let valid_meta = core_adversary::intergates::IDS.contains(&id)
        && fields.get("required").and_then(Value::as_bool).is_some()
        && fields.get("payload").is_some_and(Value::is_object);
    valid_keys && valid_meta
}

fn validate_configured_intergate_row(
    row: &Value,
    ids: &mut std::collections::BTreeSet<String>,
) -> Result<(), Refusal> {
    let fields = row
        .as_object()
        .ok_or_else(|| invalid("intergate entry must be an object"))?;
    let id = fields
        .get("intergate_id")
        .and_then(Value::as_str)
        .ok_or_else(|| invalid("intergate ID absent"))?;
    if !has_valid_intergate_fields(fields, id) || !ids.insert(id.to_owned()) {
        return Err(invalid(
            "intergate ID, payload or explicit required flag is invalid",
        ));
    }
    let payload = fields
        .get("payload")
        .ok_or_else(|| invalid("intergate payload absent"))?;
    core_adversary::intergates::evaluate(id, payload, &[])?;
    Ok(())
}

fn validate_configured_intergate_edge(edge: &str, entries: &Value) -> Result<(), Refusal> {
    let rows = entries
        .as_array()
        .filter(|rows| rows.len() <= 10)
        .ok_or_else(|| invalid("at most ten intergates per bounded transition"))?;
    if edge.is_empty() || edge.len() > 256 {
        return Err(invalid(
            "intergate edge must be nonempty and at most 256 bytes",
        ));
    }
    let mut ids = std::collections::BTreeSet::new();
    for row in rows {
        validate_configured_intergate_row(row, &mut ids)?;
    }
    Ok(())
}

fn configured_intergates(request: &Request) -> Result<Map<String, Value>, Refusal> {
    let Some(raw) = request.carrier_context.get("intergates") else {
        return Ok(Map::new());
    };
    let configured = raw
        .as_object()
        .ok_or_else(|| invalid("intergates must be a transition-keyed object"))?;
    if configured.len() > 64 {
        return Err(invalid("at most 64 configured intergate edges"));
    }
    for (edge, entries) in configured {
        validate_configured_intergate_edge(edge, entries)?;
    }
    Ok(configured.clone())
}
fn council_for_request(request: &Request) -> Result<(CouncilAssembly, Vec<String>), Refusal> {
    let directory = council_directory(&request.resources_root);
    let panel = fs::read_to_string(directory.join("adversary_panel.yaml")).map_err(io_failure)?;
    let scenes = fs::read_to_string(directory.join("scenes.yaml")).map_err(io_failure)?;
    let assembly = assemble_council_for(&panel, &scenes, PanelMode::parse(&request.panel_mode)?)?;
    let raw: Value = serde_yaml::from_str(&scenes).map_err(|error| invalid(error.to_string()))?;
    let ids = raw["scenes"]
        .as_array()
        .ok_or_else(|| invalid("canonical scene inventory absent"))?
        .iter()
        .map(|row| {
            row["id"]
                .as_str()
                .map(str::to_owned)
                .ok_or_else(|| invalid("canonical scene ID absent"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok((assembly, ids))
}
fn validate_scene_inventory(
    request: &Request,
    table: &RoutingTable,
    scene_ids: &[String],
) -> Result<(), Refusal> {
    let scenes = SceneOrchestration::from_context(
        Some(&request.carrier_context),
        request.instruction_plan.as_ref(),
        request.compute_budget,
    )?;
    let seats: Vec<String> = table
        .seats
        .iter()
        .filter(|seat| seat.calls_model())
        .map(|seat| {
            format!(
                "seat_{}",
                core_adversary::routing::canonical_seat_key(&seat.seat_id)
            )
        })
        .collect();
    scenes.validate_inventory(scene_ids, &seats, selected_seat_ids(request).as_deref())
}
fn prompt_dimension(request: &Request) -> Result<usize, Refusal> {
    let dimension = match request.carrier_context.get("density_dimension") {
        None => 128,
        Some(value) => value
            .as_u64()
            .and_then(|value| usize::try_from(value).ok())
            .ok_or_else(|| invalid("density_dimension must be an integer"))?,
    };
    if !(28..=1024).contains(&dimension) {
        return Err(invalid("density_dimension must be from 28 through 1024"));
    }
    Ok(dimension)
}

fn extract_forge_source(request: &Request) -> Result<Value, Refusal> {
    let mut fields = match request.carrier_context.get("forge_fields") {
        None => Map::new(),
        Some(Value::Object(fields)) => fields.clone(),
        Some(_) => return Err(invalid("forge_fields must be an object")),
    };
    if fields.keys().any(|key| {
        !["task", "constraints", "acceptance", "response_contract"].contains(&key.as_str())
    }) {
        return Err(invalid(
            "forge_fields contains an undeclared or protected field",
        ));
    }
    fields.insert("seed".into(), json!(request.objective));
    Ok(Value::Object(fields))
}

fn execute_forge_organization(request: &Request) -> Result<(Value, String), Refusal> {
    let source = extract_forge_source(request)?;
    let inventory = json!({"schema_version":"core.oewas.op_inventory.v3","subcolours":{},"skills":[{
        "skill_id":"adversary","ops":[{"op_id":"forge.organize-prompt.v1",
            "summary":"Organize declared task fields while retaining protected seed bytes",
            "inputs":["State"],"output":"State","binding":{"kind":"host",
                "target":"adversary/infrastructure/prompt_geometry.py::organize_initial_seed"}}],
        "anti_ops":[],"wiring":{"op":"forge.organize-prompt.v1","args":["State"]}}]});
    let checked = core_operads::operad_runtime::execute(&json!({
        "command":"operad","inventory_json":inventory.to_string(),
        "wire":{"op":"forge.organize-prompt.v1","args":["State"]}}))
    .map_err(|error| Refusal::new(&error.code, error.message))?;
    let mut organized =
        core_prompt_civilization::forge::organize_prompt(&source).map_err(invalid)?;
    organized["operation_validation"] = checked;
    organized["executed_operation_ids"] = json!(["forge.organize-prompt.v1"]);
    let text = organized["organized_text"]
        .as_str()
        .ok_or_else(|| invalid("Forge omitted organized prompt"))?
        .to_owned();
    Ok((organized, text))
}

fn native_prompt_preparation(request: &Request) -> Result<Value, Refusal> {
    let dimension = prompt_dimension(request)?;
    let enabled = match request.carrier_context.get("forge_organization") {
        None => true,
        Some(value) => value
            .as_bool()
            .ok_or_else(|| invalid("forge_organization must be boolean"))?,
    };
    let original = density_observation(
        request.objective.as_bytes(),
        dimension,
        "syntax_prefilter",
        "seed",
        "user-seed",
    );
    let mut result = json!({"seed":request.objective,"organized_text":request.objective,
        "dimension":dimension,"density":{"seed":original},"authority_effect":"None"});
    if !enabled {
        result["forge"] = json!({"operation_id":"forge.organize-prompt.v1","status":"DISABLED",
            "executed_operation_ids":[],"authority_effect":"None"});
        return Ok(result);
    }
    let (organized, text) = execute_forge_organization(request)?;
    let projected = density_observation(text.as_bytes(), dimension, "syntax_prefilter", "seed", "user-seed");
    result["organized_text"] = json!(text);
    result["density"]["organized_seed"] = projected.clone();
    result["comparison"] = crate::prompt_geometry_host::execute(
        "prompt_density_compare",
        &json!({"left":original,"right":projected}),
    )
    .unwrap_or_else(
        |error| json!({"status":"UNAVAILABLE","reason":error,"authority_effect":"None"}),
    );
    result["forge"] = organized;
    Ok(result)
}

fn validate_common_preflight(request: &Request) -> Result<(), Refusal> {
    require_live_instruction_plan(request)?;
    crate::adversary_custody::validate_output(&request.repo_root, &request.adversary_output_dir)?;
    if let Some(plan) = &request.instruction_plan {
        plan.validate()?;
    }
    if let Some(case) = &request.symbol_game_request {
        NativeC011Checker::new(case)?;
    }
    Ok(())
}

fn build_live_transport(
    request: &Request,
) -> Result<Option<OpenRouterTransport<VerifiedHttpClient>>, Refusal> {
    if !request.live {
        return Ok(None);
    }
    let env_file = request
        .env_file
        .clone()
        .unwrap_or_else(|| request.repo_root.join(".env"));
    let key = if request.inherit_environment {
        resolve_inherited_key(Some(&env_file))
    } else {
        core_adversary::providers::credentials::resolve_openrouter_key(
            Some(&env_file),
            &BTreeMap::new(),
        )
    }
    .map_err(provider_error)?;
    Ok(Some(OpenRouterTransport::new(
        key,
        VerifiedHttpClient::new(Duration::from_secs(60)).map_err(provider_error)?,
    )))
}

fn validate_run_limits(request: &Request) -> Result<(), Refusal> {
    if request.objective.len() > 16 * 1024 {
        return Err(Refusal::new(
            "SWARM_TEXT_TOO_LARGE",
            "objective exceeds 16384 UTF-8 bytes",
        ));
    }
    if !(1..=10).contains(&request.max_rounds) {
        return Err(invalid("max_rounds must be an integer from 1 through 10"));
    }
    // Recheck exact signed task, source and consumed plan before resolving credentials.
    require_live_instruction_plan(request)?;
    prompt_dimension(request)?;
    if !(1..=65536).contains(&request.max_output_tokens) || request.compute_budget == 0 {
        return Err(invalid(
            "positive compute budget and 1..65536 output tokens required",
        ));
    }
    validate_common_preflight(request)
}

fn run(request: &Request) -> Result<Value, Refusal> {
    validate_run_limits(request)?;
    let (table, config_digest) = load_routing(&request.config_path)?;
    configured_intergates(request)?;
    if request.carrier_context.contains_key("scene_orchestration") {
        let (_, scene_ids) = council_for_request(request)?;
        validate_scene_inventory(request, &table, &scene_ids)?;
    }
    let transport = build_live_transport(request)?;
    execute(
        request,
        table,
        config_digest,
        ProviderSeatTransport(transport),
        None,
    )
}

fn apply_routing_overrides(request: &Request, table: &mut RoutingTable) -> Result<(), Refusal> {
    if let Some(cap) = request.max_cost_microusd {
        if cap == 0 {
            return Err(invalid("positive cost budget required"));
        }
        table.budget.per_bout_microusd.0 = table
            .budget
            .per_bout_microusd
            .0
            .clone()
            .min(BigInt::from(cap));
        for (_, tier) in &mut table.budget.tier_per_bout_microusd {
            tier.0 = tier.0.clone().min(BigInt::from(cap));
        }
    }
    table.budget.admission_reserve_output_tokens = Some(core_adversary::exact::Integer(
        BigInt::from(request.max_output_tokens),
    ));
    if let Some(model) = request.model_override.as_ref() {
        let leg = table
            .seats
            .iter()
            .flat_map(|seat| &seat.legs)
            .find(|leg| &leg.model == model)
            .cloned()
            .ok_or_else(|| {
                Refusal::new(
                    "ROUTING_MODEL_OVERRIDE_UNPRICED",
                    format!("model override {model} has no declared routing price"),
                )
            })?;
        for seat in &mut table.seats {
            if seat.calls_model() {
                seat.legs = vec![leg.clone()];
            }
        }
    }
    Ok(())
}

fn parse_scheduler_preflight(
    request: &Request,
) -> Result<Option<core_adversary::stage::run::SwarmRunState>, Refusal> {
    let Some(value) = &request.scheduler_preflight else {
        return Ok(None);
    };
    let state: core_adversary::stage::run::SwarmRunState =
        serde_json::from_value(value.clone()).map_err(|error| invalid(error.to_string()))?;
    if state.run_key() != &request.task_key {
        return Err(invalid(
            "scheduler preflight run key does not match the bout",
        ));
    }
    Ok(Some(state))
}

fn validate_selected_seats(
    selected_seats: &Option<Vec<String>>,
    table: &RoutingTable,
) -> Result<(), Refusal> {
    let Some(selected) = selected_seats else {
        return Ok(());
    };
    let unique_count = selected
        .iter()
        .collect::<std::collections::BTreeSet<_>>()
        .len();
    let invalid_set = selected.is_empty()
        || selected.len() != unique_count
        || selected.iter().any(|id| table.seat(id).is_err());
    let missing_required = ["seat_gauge_breaker", "seat_defect_hunter", "seat_primal_dual"]
        .iter()
        .any(|id| !selected.iter().any(|v| v == id));
    if invalid_set || missing_required {
        return Err(invalid(
            "selected live roles must be known, unique and include gauge_breaker, defect_hunter and primal_dual",
        ));
    }
    Ok(())
}

fn build_dispatched_work_packet(
    request: &Request,
    preparation: &Value,
) -> Result<(String, WorkPacket), Refusal> {
    let organized = preparation["organized_text"]
        .as_str()
        .ok_or_else(|| invalid("organized seed missing"))?;
    let dispatched_objective = match request.symbol_game_request.as_ref() {
        Some(case) => format!("{}\n\nFinite checker input (problem data, not an answer):\n{}\nNormative C011 certificate contract: output exactly one JSON object with only status, phi1, potential, repair and dual fields; status must be SOLVED. potential maps every node ID to its potential p_v. repair and dual map directed edge keys u->v to exact rational strings; include every edge. For edge e=(u,v), let q_e be its claim (default zero) and w_e its positive weight (default one). The residual and required repair coordinate are r_e=q_e-(p_v-p_u). Minimize sum_e w_e*abs(r_e) over node potentials. Supply a dual circulation y with D0^T*y=0 at every node and abs(y_e)<=w_e on every edge. Report phi1 as an exact rational string and certify the equality phi1=sum_e w_e*abs(repair_e)=sum_e q_e*y_e. Use rational strings such as 0, 1, or -2/3 for all numeric certificate values, no decimal approximations. Do not copy challenge/case metadata into the certificate. Put this deliverable JSON in exactly one closed candidate fence; keep the required machine metadata outside that fence.", organized, case.case_text()),
        None => organized.to_owned(),
    };
    let packet: WorkPacket = serde_json::from_value(json!({"task_key":request.task_key,"scene_id":"act1_perception","objective":dispatched_objective,"input_artifact_refs":[],"acceptance_criteria":["Produce an inspectable candidate and retain independent critique/checker findings"],"budget_units":request.compute_budget,"evaluator_epoch_id":format!("sha256:{}",hex::encode(Sha256::digest(request.task_key.as_bytes()))),"causal_parent_ids":[],"authority_effect":"None","schema_version":"core.oeas.work-packet.v1"})).map_err(|e| invalid(e.to_string()))?;
    Ok((dispatched_objective, packet))
}

fn resolve_bout_journal_path(request: &Request, output: &Path) -> PathBuf {
    request.journal_path.clone().unwrap_or_else(|| {
        let perm = request
            .repo_root
            .join("_ic/nara/permanent_records/bout_journal.jsonl");
        if perm.exists() {
            perm
        } else {
            output.join("bout_journal.jsonl")
        }
    })
}

fn build_request_digest(request: &Request, packet: &WorkPacket) -> String {
    request
        .instruction_admission
        .as_ref()
        .map(|a| a.request_digest().to_owned())
        .unwrap_or_else(|| {
            format!(
                "sha256:{}",
                hex::encode(Sha256::digest(json!(packet).to_string().as_bytes()))
            )
        })
}

fn attach_refusal_bundle(
    bundles: &mut Bundles,
    spec: &BoutRunSpec,
    refusal: &mut Refusal,
    act: &str,
    turns: &[Map<String, Value>],
) {
    if refusal.details.contains_key("refusal_bundle")
        || refusal.details.contains_key("refusal_bundle_error")
    {
        return;
    }
    match bundles.persist(spec, refusal, act, turns) {
        Ok(path) => {
            refusal.details.insert("refusal_bundle".into(), path);
        }
        Err(error) => {
            refusal.details.insert(
                "refusal_bundle_error".into(),
                format!("{}: {}", error.code, error.message),
            );
        }
    }
}

fn handle_bout_abort(
    bundles: &mut Bundles,
    spec: &BoutRunSpec,
    turns: &[Map<String, Value>],
    abort: BoutAbort,
) -> Refusal {
    match abort {
        BoutAbort::Refused(mut refusal) => {
            attach_refusal_bundle(bundles, spec, &mut refusal, "BOUNDARY_REFUSED", turns);
            refusal
        }
        BoutAbort::Interrupted(message) => {
            let mut refusal = Refusal::new("ADVERSARY_BOUT_INTERRUPTED", message);
            attach_refusal_bundle(bundles, spec, &mut refusal, "INTERRUPTED", turns);
            refusal
        }
        BoutAbort::UnexpectedException(message) => {
            let mut refusal = Refusal::new("ADVERSARY_BOUT_UNEXPECTED_EXCEPTION", message);
            attach_refusal_bundle(bundles, spec, &mut refusal, "UNEXPECTED_EXCEPTION", turns);
            refusal
        }
    }
}

fn format_bout_success(
    request: &Request,
    result: &core_adversary::complete_bout::CompleteBoutOutcome,
    working_directory: Option<&PathBuf>,
    journal_residuals: Vec<Refusal>,
    recovery: Option<Refusal>,
) -> Value {
    let s = &result.summary;
    let selected = result.receipt["selected_candidate_id"]
        .as_str()
        .unwrap_or("");
    let disposition = s["disposition"].as_str().unwrap_or("COMPOSTED");
    let folder = result.run_directory.as_deref().map(Path::new);
    let working_state_path = working_directory.map(|directory| directory.join("state.json"));
    let residual_declared =
        s["status"] == json!("BOUNDED_RESIDUAL") && s["residual_declared"] == Value::Bool(true);
    json!({"schema_version":"core.adversary.bout-outcome.v1","receipt_id":result.receipt["receipt_id"],"selected_candidate_id":selected,"disposition":disposition,"consecration_state":s["consecration_state"],"terminal_verdict":s["terminal_verdict"],"authority_effect":"None","task_key":request.task_key,"status":s["status"],"receipt_path":folder.map(|folder|folder.join("receipt.json")),"novella_path":folder.map(|folder|folder.join("uns.md")),"ddc_path":folder.map(|folder|folder.join("ddc.jsonl")),"summary_path":folder.map(|folder|folder.join("summary.json")),"reporting_status":s["reporting"]["status"].as_str().unwrap_or("UNOBSERVED"),"reporting_failure_code":s["reporting"]["failure_code"],"working_state_path":working_state_path,"phi1":s["phi1"],"gamma2":s["gamma2"],"defect_count":s["defect_count"],"residual_declared":residual_declared,"is_authorized":s["is_authorized"],"measurement_status":s["measurement_status"],"checker_verdict":s["checker_verdict"],"checker_receipt_sha256":s["checker_receipt_sha256"],"authorization_blockers":s["authorization_blockers"],"authorization_evidence":result.receipt["authorization_evidence"],"journal_residuals":journal_residuals,"recovery_residuals":recovery})
}

struct PreparedExecutionContext {
    checker: Option<NativeC011Checker>,
    assembly: CouncilAssembly,
    preflight_state: Option<core_adversary::stage::run::SwarmRunState>,
    selected_seats: Option<Vec<String>>,
    intergates: Map<String, Value>,
}

fn prepare_execution_context(
    request: &Request,
    table: &mut RoutingTable,
) -> Result<PreparedExecutionContext, Refusal> {
    // Injected transports obey the same signed live admission boundary.
    require_live_instruction_plan(request)?;
    apply_routing_overrides(request, table)?;
    let checker = request
        .symbol_game_request
        .as_ref()
        .map(NativeC011Checker::new)
        .transpose()?;
    let (assembly, scene_ids) = council_for_request(request)?;
    let preflight_state = parse_scheduler_preflight(request)?;
    let selected_seats = selected_seat_ids(request);
    validate_scene_inventory(request, table, &scene_ids)?;
    let intergates = configured_intergates(request)?;
    validate_selected_seats(&selected_seats, table)?;
    Ok(PreparedExecutionContext {
        checker,
        assembly,
        preflight_state,
        selected_seats,
        intergates,
    })
}

fn prepare_execution_io(
    request: &Request,
) -> Result<(Value, String, WorkPacket, usize, PathBuf), Refusal> {
    let preparation = native_prompt_preparation(request)?;
    let (dispatched_objective, packet) = build_dispatched_work_packet(request, &preparation)?;
    let dimension = prompt_dimension(request)?;
    let output =
        crate::adversary_custody::validate_output(&request.repo_root, &request.adversary_output_dir)?;
    Ok((preparation, dispatched_objective, packet, dimension, output))
}

fn execute<T: SeatTransport>(
    request: &Request,
    mut table: RoutingTable,
    config_digest: String,
    transport: T,
    fixture_override: Option<&mut dyn SeatPort>,
) -> Result<Value, Refusal> {
    let mut ctx = prepare_execution_context(request, &mut table)?;
    let (preparation, dispatched_objective, packet, dimension, output) =
        prepare_execution_io(request)?;
    let mut live_scheduler: Option<DeterministicScheduler> = None;
    let mut preflight_scheduler = None;
    let scheduler: &mut dyn SchedulerPort = if ctx.preflight_state.is_some() {
        preflight_scheduler = Some(PreflightBoundScheduler);
        preflight_scheduler
            .as_mut()
            .checked_invariant_03e6c976("preflight scheduler is bound")
    } else {
        live_scheduler = Some(ctx.assembly.scheduler()?);
        live_scheduler
            .as_mut()
            .checked_invariant_03e6c976("live scheduler is bound")
    };
    let turn_geometry = Rc::new(RefCell::new(TurnGeometry::default()));
    let mut live_seats = core_adversary::pfp_gateway::PfpSeatExecutor {
        inner: RoutedSeatExecutor {
            table,
            config_digest,
            transports: ObservedSeatTransport {
                inner: transport,
                dimension,
                observed: Rc::clone(&turn_geometry),
            },
            ledger: FileCallLedger {
                path: request.ledger_path.clone(),
            },
            bout_id: request.bout_id.clone(),
            max_output_tokens: request.max_output_tokens,
            clock: RuntimeClock {
                start: Instant::now(),
            },
            spent_bout: BigInt::from(0),
            spent_tier: BTreeMap::new(),
        },
    };
    let mut fixtures = FixtureSeats;
    let seats: &mut dyn SeatPort = if request.live {
        &mut live_seats
    } else {
        fixture_override.unwrap_or(&mut fixtures)
    };
    let mut selected = SelectedSeats {
        inner: seats,
        allowed: ctx.selected_seats,
        dimension,
        observed: turn_geometry,
    };
    let mut journal = JsonlJournal::new(resolve_bout_journal_path(request, &output));
    let recovery = reconcile_crashed_bouts(&mut journal).err();
    let mut journal = ReportingJournal::new(
        journal,
        &output,
        json!({
        "schema_version":"core.adversary.native-working-history.v1",
        "task_key":request.task_key,"bout_id":request.bout_id,
        "objective":dispatched_objective,"original_seed":request.objective,
        "forge":preparation,"seat_turns":[],"pending_prompt":null,
        "status":"INCOMPLETE","authority_effect":"None"}),
    );
    let shared = Rc::new(RefCell::new(Vec::new()));
    let mut ddc = DdcStore {
        path: output.join("ddc_actions.jsonl"),
        steps: Vec::new(),
        shared: Rc::clone(&shared),
    };
    let mut bundles = Bundles {
        root: output.clone(),
        steps: shared,
        preparation: preparation.clone(),
    };
    let mut artifacts = RunFolderStore::new(output.clone());
    let mut uts = MemoryUts::default();
    let mut uns = MemoryUns::default();
    let mut packets = FilePackets {
        path: output.join("sgt_packets.jsonl"),
    };
    let mut cemetery = FileCemetery {
        directory: output.join("cemetery"),
    };
    let mut history = FileFailureHistory {
        directory: output.join("antibodies"),
    };
    let mut genealogy = FileGenealogy {
        path: output.join("prompt_genealogy.jsonl"),
    };
    let mut transitions = RuntimeTransitions {
        cemetery: FileCemetery {
            directory: output.join("cemetery"),
        },
        intergates: ctx.intergates,
        task_key: request.task_key.clone(),
        history: Vec::new(),
        request_digest: build_request_digest(request, &packet),
        candidate_bindings: BTreeMap::new(),
    };
    transitions.cemetery.load_headstones()?;
    let mut diagnostic = NativeSbeDiagnostic;
    let mut scorer = crate::adversary_scoring::NativeCochainScorer;
    let mut regge = crate::adversary_scoring::NativeReggeScorer;
    let mut governance = Governance {
        root: request.resources_root.clone(),
    };
    let clock = RuntimeClock {
        start: Instant::now(),
    };
    let now = Utc::now().format("%Y-%m-%d %H:%M:%S UTC").to_string();
    let spec = BoutRunSpec {
        bout_id: format!("{}:{}", request.task_key, request.bout_id),
        task_key: request.task_key.clone(),
        objective: request.objective.clone(),
        fixture_seats: !request.live,
        learning_guidance: request.learning_guidance.clone(),
        instruction_plan: request.instruction_plan.clone(),
    };
    let mut runtime_carrier = request.carrier_context.clone();
    runtime_carrier.insert("adversary_prompt_preparation".into(), preparation);
    let carrier = Value::Object(request.carrier_context.clone()).to_string();
    let outcome = execute_captured_bout_boundary(
        &spec,
        &mut selected,
        Some(&mut journal),
        &mut bundles,
        |recorder, progress| {
            execute_complete_bout(
                &CompleteBoutInput {
                    packet: &packet,
                    carrier_json: (!request.carrier_context.is_empty()).then_some(carrier.as_str()),
                    carrier_context: Some(&runtime_carrier),
                    ablation_flags: Some(&request.ablation_flags),
                    fixture_seats: &Value::Bool(!request.live),
                    request_external_admission: &Value::Bool(request.request_external_admission),
                    max_candidate_budget: 3,
                    max_critique_rounds: request.max_rounds,
                    ddc_step_offset: 0,
                    now_utc: &now,
                    instruction_plan: request.instruction_plan.as_ref(),
                    panel: Some(&ctx.assembly.panel),
                    initial_state: ctx.preflight_state.clone(),
                },
                CompleteBoutPorts {
                    scheduler,
                    diagnostic: &mut diagnostic,
                    scorer: Some(&mut scorer),
                    regge: Some(&mut regge),
                    checker: ctx
                        .checker
                        .as_mut()
                        .map(|checker| checker as &mut dyn CandidateCheckerPort),
                    host: Some(&mut transitions),
                    governance: &mut governance,
                    artifacts: &mut artifacts,
                    emitters: Some(EmitterSuite {
                        uts: Some(&mut uts),
                        uns: Some(&mut uns),
                        sgt: Some(SgtSink::Packet(&mut packets)),
                        cemetery: Some(&mut cemetery),
                        antibodies: Some(&mut history),
                        genealogy: Some(&mut genealogy),
                        ddc: Some(&mut ddc),
                    }),
                },
                recorder,
                progress,
                &AuthorizationTime {
                    event_clock: &clock,
                    dda_timestamp: &now,
                },
            )
            .map_err(BoutAbort::from)
        },
    );
    match outcome.result {
        Ok(result) => Ok(format_bout_success(
            request,
            &result,
            journal.directory.as_ref(),
            outcome.journal_residuals,
            recovery,
        )),
        Err(abort) => Err(handle_bout_abort(&mut bundles, &spec, &outcome.turns, abort)),
    }
}
/// Inject a transport at the composition boundary; the same router, ledger,
/// seven acts, custody and filesystem adapters still execute.
pub fn execute_with_transport<T: SeatTransport>(
    payload: &Value,
    transport: T,
) -> Result<Value, Refusal> {
    let request: Request =
        serde_json::from_value(payload.clone()).map_err(|e| invalid(e.to_string()))?;
    if request.objective.len() > 16384 || !(1..=10).contains(&request.max_rounds) {
        return Err(invalid("invalid objective size or round limit"));
    }
    validate_common_preflight(&request)?;
    let (table, digest) = load_routing(&request.config_path)?;
    execute(&request, table, digest, transport, None)
}
/// The envelope binds successful runs and typed semantic refusals to their input.
pub fn dispatch(payload: &Value) -> Result<Value, Refusal> {
    let bytes = serde_json::to_vec(payload).map_err(|e| invalid(e.to_string()))?;
    let input_digest = pfp_runtime::framed_sha256(REQUEST_DOMAIN, &bytes);
    let result = serde_json::from_value::<Request>(payload.clone())
        .map_err(|e| invalid(e.to_string()))
        .and_then(|request| run(&request));
    Ok(match result {
        Ok(outcome) => json!({"input_digest":input_digest,"outcome":outcome,"refusal":null}),
        Err(refusal) => json!({"input_digest":input_digest,"outcome":null,"refusal":refusal}),
    })
}

// Origin: engine/crates_rs/pfp/src/adversary_host.rs
// Claim: urn:core:crates_rs:pfp:adversary-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
#[path = "adversary_checker_tests.rs"]
mod checker_tests;

#[cfg(test)]
mod governance_source_custody_tests {
    use super::*;

    fn write_sources(root: &Path) {
        for source in ["governance-pfp", "governance-wdp", "governance-clean-arch"] {
            let path = root.join(".agents/skills").join(source).join("SKILL.md");
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(path, format!("canonical source: {source}\n")).unwrap();
        }
    }

    #[test]
    fn governance_port_refuses_missing_foreign_root_then_recovers_from_its_own_sources() {
        let root = tempfile::tempdir().unwrap();
        let request = GovernanceRequest {
            objective: "Check CODA code",
            task_key: "source_custody",
            letter_tape: "T",
        };
        let mut port = Governance {
            root: root.path().to_path_buf(),
        };
        // The real workspace has canonical sources. An empty explicit root must
        // still refuse, regardless of the test process working directory.
        let refusal = port.resolve_and_verify(&request).unwrap_err();
        assert_eq!(refusal.code, "GOVERNANCE_BUNDLE_UNREADABLE");
        write_sources(root.path());
        let bundle = port.resolve_and_verify(&request).unwrap();
        for (index, (role, source)) in GOVERNANCE_SOURCE_BINDINGS_V1.iter().enumerate() {
            let source_path = format!(".agents/skills/{source}/SKILL.md");
            assert_eq!(bundle[index]["skill_id"], *role);
            assert_eq!(bundle[index]["source_skill_id"], *source);
            assert_eq!(bundle[index]["source_path"], source_path);
            assert_eq!(
                bundle[index]["source_binding_version"],
                GOVERNANCE_SOURCE_BINDING_VERSION
            );
            assert_eq!(bundle[index]["verification_scope"], GOVERNANCE_SOURCE_SCOPE);
            assert_eq!(bundle[index]["result"], "PASS");
            assert_eq!(
                bundle[index]["digest"],
                hex::encode(Sha256::digest(
                    fs::read(root.path().join(source_path)).unwrap()
                ))
            );
        }
        let foreign = tempfile::tempdir().unwrap();
        port.root = foreign.path().to_path_buf();
        assert_eq!(
            port.resolve_and_verify(&request).unwrap_err().code,
            "GOVERNANCE_BUNDLE_UNREADABLE"
        );
        port.root = root.path().to_path_buf();
        assert_eq!(port.resolve_and_verify(&request).unwrap(), bundle);
    }

    #[test]
    fn governance_port_retains_distinct_ddc_coda_roles_and_rebinds_changed_bytes() {
        let root = tempfile::tempdir().unwrap();
        write_sources(root.path());
        let mut port = Governance {
            root: root.path().to_path_buf(),
        };
        let ddc = port
            .resolve_and_verify(&GovernanceRequest {
                objective: "Check a finite witness",
                task_key: "ddc_only",
                letter_tape: "T",
            })
            .unwrap();
        assert_eq!(ddc[1]["result"], "PASS");
        assert_eq!(ddc[2]["result"], "N_A");
        assert_eq!(ddc[1]["digest"], ddc[2]["digest"]);
        fs::write(
            root.path().join(".agents/skills/governance-wdp/SKILL.md"),
            b"new canonical bytes",
        )
        .unwrap();
        let coda = port
            .resolve_and_verify(&GovernanceRequest {
                objective: "Check CODA",
                task_key: "coda_only",
                letter_tape: "",
            })
            .unwrap();
        assert_eq!(coda[1]["result"], "N_A");
        assert_eq!(coda[2]["result"], "PASS");
        assert_ne!(coda[2]["digest"], ddc[2]["digest"]);
        assert_eq!(coda[1]["digest"], coda[2]["digest"]);
    }
}

#[cfg(test)]
mod live_admission_tests {
    use super::*;

    #[test]
    fn live_dispatch_refuses_before_missing_paths_or_admission() {
        let payload = json!({
            "task_key": "retired_native_live", "objective": "Check the task",
            "repo_root": "missing-native-root", "adversary_output_dir": "missing-output",
            "resources_root": "missing-resources", "ledger_path": "missing-ledger",
            "bout_id": "retired", "config_path": "missing-config", "live": true
        });
        let result = dispatch(&payload).unwrap();
        assert!(result["outcome"].is_null());
        assert_eq!(result["refusal"]["code"], "NATIVE_INSTRUCTION_PLAN_UNBOUND");
    }

    #[test]
    fn actual_candidate_stages_bind_task_request_occurrence_and_bytes() {
        let mut host = RuntimeTransitions {
            cemetery: FileCemetery {
                directory: PathBuf::from("unused"),
            },
            intergates: Map::new(),
            task_key: "native-stages".into(),
            history: Vec::new(),
            request_digest: format!("sha256:{}", "a".repeat(64)),
            candidate_bindings: BTreeMap::new(),
        };
        let request = json!({"action":"anti_skill_candidate_stage","task_key":"native-stages",
            "stage":"POST_PRODUCTION","authority_effect":"None",
            "candidates":[{"candidate_id":"sha256:control","content":"exact candidate\n"}]});
        let produced = host.execute(request.to_string().as_bytes()).unwrap();
        assert_eq!(produced["decisions"][0]["decision"]["disposition"], "CLEAR");
        let mut selection = request.clone();
        selection["stage"] = json!("PRE_SELECTION");
        let selected = host.execute(selection.to_string().as_bytes()).unwrap();
        assert_ne!(
            produced["decisions"][0]["decision"]["receipt_id"],
            selected["decisions"][0]["decision"]["receipt_id"]
        );
        selection["candidates"][0]["content"] = json!("foreign candidate\n");
        assert!(host.execute(selection.to_string().as_bytes()).is_err());
        selection["candidates"] = request["candidates"].clone();
        selection["task_key"] = json!("foreign");
        assert!(host.execute(selection.to_string().as_bytes()).is_err());
        selection["task_key"] = request["task_key"].clone();
        selection["stage"] = json!("UNKNOWN");
        assert!(host.execute(selection.to_string().as_bytes()).is_err());
    }
}

#[cfg(test)]
mod prompt_geometry_tests {
    use super::*;

    fn working_snapshot(root: &Path) -> (PathBuf, Value) {
        let directory = fs::read_dir(root.join("working"))
            .unwrap()
            .next()
            .unwrap()
            .unwrap()
            .path();
        let marker: Value =
            serde_json::from_slice(&fs::read(directory.join("reporting.json")).unwrap()).unwrap();
        assert_eq!(marker["status"], "MATERIALIZED");
        for name in ["state.json", "novella.md", "uts.jsonl"] {
            assert_eq!(
                marker["files"][name],
                hex::encode(Sha256::digest(fs::read(directory.join(name)).unwrap()))
            );
        }
        let state =
            serde_json::from_slice(&fs::read(directory.join("state.json")).unwrap()).unwrap();
        (directory, state)
    }
    fn checkpoint_spec() -> BoutRunSpec {
        BoutRunSpec {
            bout_id: "checkpoint".into(),
            task_key: "checkpoint".into(),
            objective: "Retain the original task".into(),
            fixture_seats: true,
            learning_guidance: String::new(),
            instruction_plan: None,
        }
    }
    fn checkpoint_journal(root: &Path) -> ReportingJournal {
        ReportingJournal::new(
            JsonlJournal::new(root.join("journal.jsonl")),
            root,
            json!({"task_key":"checkpoint","objective":"Retain the original task",
                "seat_turns":[],"status":"INCOMPLETE","authority_effect":"None"}),
        )
    }
    fn checkpoint_request() -> SeatTurnRequest {
        serde_json::from_value(
            json!({"scene_id":"act1_perception","seat_id":"seat_gauge_breaker",
            "prompt_text":"Preserve α and the original instructions."}),
        )
        .unwrap()
    }

    #[test]
    fn checkpoint_preserves_captured_history_and_pending_request_after_interruption() {
        struct InspectingSeat {
            root: PathBuf,
            calls: usize,
        }
        impl SeatPort for InspectingSeat {
            fn execute_turn(
                &mut self,
                request: &SeatTurnRequest,
            ) -> Result<SeatTurnReply, Refusal> {
                let (_, state) = working_snapshot(&self.root);
                assert_eq!(state["pending_prompt"]["user"], request.prompt_text);
                assert_eq!(state["seat_turns"].as_array().unwrap().len(), self.calls);
                self.calls += 1;
                if self.calls == 2 {
                    std::panic::panic_any(core_adversary::stage::ports::ExecutionInterruption {
                        exception_type: "fixture interruption".into(),
                    });
                }
                FixtureSeats.execute_turn(request)
            }
        }
        let root = tempfile::tempdir().unwrap();
        let mut seat = InspectingSeat {
            root: root.path().to_path_buf(),
            calls: 0,
        };
        let mut journal = checkpoint_journal(root.path());
        let mut bundles = Bundles {
            root: root.path().to_path_buf(),
            steps: Rc::new(RefCell::new(vec![])),
            preparation: json!({}),
        };
        let result = execute_captured_bout_boundary(
            &checkpoint_spec(),
            &mut seat,
            Some(&mut journal),
            &mut bundles,
            |recorder, _| {
                let (_, initial) = working_snapshot(root.path());
                assert_eq!(initial["seat_turns"], json!([]));
                assert!(initial["pending_prompt"].is_null());
                recorder.execute_turn(&checkpoint_request())?;
                let (_, captured) = working_snapshot(root.path());
                assert_eq!(captured["seat_turns"].as_array().unwrap().len(), 1);
                assert!(captured["pending_prompt"].is_null());
                recorder.execute_turn(&checkpoint_request())?;
                Ok(())
            },
        );
        assert!(matches!(result.result, Err(BoutAbort::Interrupted(_))));
        let (directory, state) = working_snapshot(root.path());
        assert_eq!(state["status"], "INTERRUPTED");
        assert_eq!(state["seat_turns"].as_array().unwrap().len(), 1);
        assert_eq!(state["pending_prompt"]["status"], "PENDING_SEAT_REQUEST");
        assert!(state["pending_prompt"].get("reply_text").is_none());
        assert!(fs::read_to_string(directory.join("uts.jsonl"))
            .unwrap()
            .contains("NOT_ESTABLISHED"));
        assert!(result.journal_residuals.is_empty());
    }

    #[test]
    fn checkpoint_reporting_failure_preserves_task_result_and_can_retry() {
        let root = tempfile::tempdir().unwrap();
        fs::write(root.path().join("working"), b"blocked working directory").unwrap();
        let mut journal = checkpoint_journal(root.path());
        let mut seat = FixtureSeats;
        let mut bundles = Bundles {
            root: root.path().to_path_buf(),
            steps: Rc::new(RefCell::new(vec![])),
            preparation: json!({}),
        };
        let result = execute_captured_bout_boundary(
            &checkpoint_spec(),
            &mut seat,
            Some(&mut journal),
            &mut bundles,
            |recorder, _| {
                recorder
                    .execute_turn(&checkpoint_request())
                    .map_err(BoutAbort::from)
            },
        );
        assert!(result.result.is_ok());
        assert!(result
            .journal_residuals
            .iter()
            .all(|failure| failure.code == "ADVERSARY_REPORTING_FAILED"));
        assert!(!result.journal_residuals.is_empty());
        fs::remove_file(root.path().join("working")).unwrap();
        journal.checkpoint(&result.turns, None).unwrap();
        let (_, state) = working_snapshot(root.path());
        assert_eq!(state["seat_turns"].as_array().unwrap().len(), 1);
        assert_eq!(state["status"], "COMPLETED");
    }

    #[test]
    fn checkpoint_retains_final_checker_summary_when_bundle_reporting_failed() {
        let root = tempfile::tempdir().unwrap();
        let mut journal = checkpoint_journal(root.path());
        let summary = json!({"task_key":"checkpoint","objective":"Retain original task",
            "status":"BOUNDED_RESIDUAL","terminal_verdict":"BOUNDED_RESIDUAL",
            "checker_verdict":"REJECTED","candidate_checks":{"candidate":{"accepted":false}},
            "seat_turns":[],"reporting":{"status":"REPORTING_FAILED","failure_code":"DISK_FULL"}});
        journal.checkpoint_outcome(&summary).unwrap();
        let mut terminal = JournalEntry::new("checkpoint", EntryKind::BoutTerminal, "checkpoint");
        terminal
            .detail
            .push(("terminal_status".into(), "COMPLETED".into()));
        journal.append(&terminal).unwrap();
        journal.checkpoint(&[], None).unwrap();
        let (_, saved) = working_snapshot(root.path());
        assert_eq!(saved["status"], summary["status"]);
        assert_eq!(saved["candidate_checks"], summary["candidate_checks"]);
        assert_eq!(saved["reporting"], summary["reporting"]);
        assert_eq!(saved["terminal_status"], "COMPLETED");
        assert!(saved.get("receipt_id").is_none());
    }

    struct CapturedTransport {
        raw: Vec<u8>,
    }
    impl SeatTransport for CapturedTransport {
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
            Ok(self.raw.clone())
        }
    }

    #[test]
    fn final_transport_prompt_and_malformed_wire_are_observed_without_rewriting() {
        for raw in [b"not a provider envelope".to_vec(), vec![255]] {
            let observed = Rc::new(RefCell::new(TurnGeometry {
                role_id: "seat_syntax_prefilter".into(),
                attempts: vec![],
            }));
            let mut transport = ObservedSeatTransport {
                inner: CapturedTransport { raw: raw.clone() },
                dimension: 28,
                observed: Rc::clone(&observed),
            };
            let prompt = SeatPrompt {
                system: "Keep [IMMUNE_FENCE] exact.".into(),
                user: "α ordered seed".into(),
            };
            assert_eq!(
                transport
                    .send_bound("fixture", "fixture-model", &prompt, 10)
                    .unwrap()
                    .raw,
                raw
            );
            let capture = &observed.borrow().attempts[0];
            assert_eq!(capture["pfp_prepared_prompts"]["system"], prompt.system);
            assert_eq!(
                capture["density"]["user"]["source_sha256"],
                format!(
                    "sha256:{}",
                    hex::encode(Sha256::digest(prompt.user.as_bytes()))
                )
            );
            assert_eq!(
                capture["density"]["provider_wire"]["status"],
                if raw == vec![255] {
                    "INVALID_UTF8"
                } else {
                    "OBSERVED"
                }
            );
            assert!(capture.get("raw_reply_hex").is_none());
        }
    }

    #[test]
    fn provider_content_has_a_distinct_model_reply_observation() {
        let observed = Rc::new(RefCell::new(TurnGeometry {
            role_id: "seat_bare_metal_anchor".into(),
            attempts: vec![],
        }));
        let content = "{\"refusal\":\"cannot answer\"}";
        let raw = json!({"choices":[{"message":{"content":content}}]})
            .to_string()
            .into_bytes();
        let mut transport = ObservedSeatTransport {
            inner: CapturedTransport { raw },
            dimension: 128,
            observed: Rc::clone(&observed),
        };
        transport
            .send_bound(
                "fixture",
                "fixture-model",
                &SeatPrompt {
                    system: "s".into(),
                    user: "u".into(),
                },
                10,
            )
            .unwrap();
        let capture = &observed.borrow().attempts[0];
        assert_eq!(
            capture["density"]["reply"]["source_sha256"],
            format!("sha256:{}", hex::encode(Sha256::digest(content.as_bytes())))
        );
        assert_eq!(capture["density"]["reply"]["field"], "pfp.raw_reply");
    }

    fn request(context: Value) -> Request {
        serde_json::from_value(json!({"task_key":"geometry-fixture","objective":"  Original α.\r\n",
            "repo_root":"unused","adversary_output_dir":"unused","resources_root":"unused",
            "ledger_path":"unused","bout_id":"geometry","config_path":"unused","carrier_context":context})).unwrap()
    }

    #[test]
    fn native_forge_preserves_seed_and_declared_fields_with_checked_operation() {
        let input = request(
            json!({"density_dimension":28,"forge_fields":{"task":"Declared task",
            "constraints":["No paid calls"],"acceptance":["Check original task"]}}),
        );
        let preparation = native_prompt_preparation(&input).unwrap();
        assert_eq!(preparation["seed"], input.objective);
        assert!(preparation["organized_text"]
            .as_str()
            .unwrap()
            .starts_with(&input.objective));
        assert_eq!(
            preparation["forge"]["operation_validation"]["status"],
            "VALID"
        );
        assert_eq!(preparation["density"]["seed"]["dim"], 28);
        assert_eq!(preparation["comparison"]["status"], "COMPARED");
        assert_eq!(
            native_prompt_preparation(&request(json!({"forge_organization":false}))).unwrap()
                ["forge"]["status"],
            "DISABLED"
        );
        assert!(native_prompt_preparation(&request(json!({"density_dimension":true}))).is_err());
        assert!(native_prompt_preparation(&request(
            json!({"forge_fields":{"seed":"replacement"}})
        ))
        .is_err());
    }

    #[test]
    fn zero_turn_refusal_still_has_uns_and_uts() {
        let directory = tempfile::tempdir().unwrap();
        let spec = BoutRunSpec {
            bout_id: "partial".into(),
            task_key: "partial".into(),
            objective: "Original seed".into(),
            fixture_seats: true,
            learning_guidance: String::new(),
            instruction_plan: None,
        };
        let mut bundles = Bundles {
            root: directory.path().to_path_buf(),
            steps: Rc::new(RefCell::new(vec![])),
            preparation: json!({"seed":spec.objective,"dimension":128}),
        };
        let result = bundles
            .persist(
                &spec,
                &Refusal::new("FIXTURE_REFUSAL", "Unavailable check"),
                "START",
                &[],
            )
            .unwrap();
        let path = Path::new(&result);
        assert!(path.join("uts.jsonl").is_file());
        assert!(fs::read_to_string(path.join("novella.md"))
            .unwrap()
            .contains("No Panel contributions"));
        let summary: Value =
            serde_json::from_slice(&fs::read(path.join("summary.json")).unwrap()).unwrap();
        assert_eq!(summary["bundle_schema_version"], RUN_BUNDLE_V2);
        assert_eq!(summary["original_seed"], "Original seed");
    }
}
