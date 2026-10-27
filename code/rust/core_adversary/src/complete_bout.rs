//! Seven-act application controller. IO and independent checks are injected.
use crate::authorization::{
    execute_act7_authorization_gate, truthy, AuthorizationGateInput, AuthorizationTime,
};
use crate::bout_auxiliary::{
    execute_act3_epistemic_sieve, execute_act4_sandbox_with_candidates,
    execute_act7_crystallization, CandidateContent, CrystallizationInput, EpistemicSieveInput,
};
use crate::candidate_checks::{execute_candidate_checks, CandidateChecksInput};
use crate::candidate_proposals::{
    execute_act3_candidate_proposal_generation, CandidateProposalsInput,
};
use crate::carrier::{ExactCochain, Network};
use crate::carrier_framing::{execute_act1_carrier_framing, CarrierFramingInput};
use crate::checker_ports::CandidateCheckerPort;
use crate::custody::RecordingSeatPort;
use crate::evidence::{canonical_rational, sha256_ref, ObstructionMeasurement};
use crate::gauge_break::{execute_act4_gauge_break, GaugeBreakInput};
use crate::independent_witness::{execute_act5_independent_witness, IndependentWitnessInput};
use crate::obstruction_identification::{
    execute_act2_obstruction_identification, ObstructionIdentificationInput,
};
use crate::render_record::{JsonStyle, RenderRecord};
use crate::residual_ledger::{execute_act6_residual_ledger, ResidualLedgerInput};
use crate::run_persistence::{
    content_addressed_receipt_id_v3, ddc_trace_digest, persist_bout_run_folder_v3,
    PersistenceInput, RunArtifactPort,
};
use crate::run_reporting::project_run_reports;
use crate::scene_orchestration::SceneOrchestration;
use crate::scoring_ports::CochainScoringPort;
use num_rational::BigRational;
use num_traits::Zero;
use crate::stage::ddc::DdcStep;
use crate::stage::diagnostics::SbeDiagnosticPort;
use crate::stage::emission::{
    build_intelligence_event, emit_event, EmitterSuite, EventDescriptor, Payload,
};
use crate::stage::packets::{AgentResult, WorkPacket};
use crate::stage::ports::{Refusal, SchedulerPort};
use crate::stage::run::{ProgressMeasure, SwarmRunState};
use serde_json::{json, Map, Value};
use std::collections::BTreeMap;

const LOCUS: &str = "adversary.use_cases.bout_service";
fn refusal(code: &str, message: impl Into<String>) -> Refusal {
    let mut result = Refusal::new(code, message);
    result.locus = LOCUS.into();
    result
}
fn value<T: serde::Serialize>(input: &T) -> Result<Value, Refusal> {
    serde_json::to_value(input).map_err(|e| refusal("ADVERSARY_BOUT_RECORD_INVALID", e.to_string()))
}
fn record(input: &Value) -> Result<RenderRecord, Refusal> {
    RenderRecord::from_json(&input.to_string())
}
pub struct GovernanceRequest<'a> {
    pub objective: &'a str,
    pub task_key: &'a str,
    pub letter_tape: &'a str,
}
/// The concrete adapter resolves canonical skill bytes and validates the bundle.
pub trait GovernancePort {
    fn resolve_and_verify(&mut self, request: &GovernanceRequest<'_>) -> Result<Value, Refusal>;
}
pub trait BoutHostPort {
    fn execute(&mut self, request: &[u8]) -> Result<Value, Refusal>;
}
pub trait ReggeScoringPort {
    fn compute(
        &mut self,
        network: &Network,
        cochain: &ExactCochain,
    ) -> Result<Map<String, Value>, Refusal>;
}
pub struct CompleteBoutInput<'a> {
    pub packet: &'a WorkPacket,
    pub carrier_json: Option<&'a str>,
    pub carrier_context: Option<&'a Map<String, Value>>,
    pub ablation_flags: Option<&'a Map<String, Value>>,
    pub fixture_seats: &'a Value,
    pub request_external_admission: &'a Value,
    pub max_candidate_budget: i64,
    pub max_critique_rounds: i64,
    /// Number of retained DDC steps before this bout; zero without a DDC sink.
    pub ddc_step_offset: usize,
    pub now_utc: &'a str,
    pub instruction_plan: Option<&'a crate::instruction_plan::InstructionPlanTransportV01>,
    /// The council's panel record (mode, seats, seatless acts), named on the receipt.
    pub panel: Option<&'a Value>,
    /// State from the one scheduler preflight. When set, this bout does not call `start` again.
    pub initial_state: Option<SwarmRunState>,
}
pub struct CompleteBoutPorts<'a> {
    pub scheduler: &'a mut dyn SchedulerPort,
    pub diagnostic: &'a mut dyn SbeDiagnosticPort,
    pub scorer: Option<&'a mut dyn CochainScoringPort>,
    pub regge: Option<&'a mut dyn ReggeScoringPort>,
    pub checker: Option<&'a mut dyn CandidateCheckerPort>,
    pub host: Option<&'a mut dyn BoutHostPort>,
    pub governance: &'a mut dyn GovernancePort,
    pub artifacts: &'a mut dyn RunArtifactPort,
    pub emitters: Option<EmitterSuite<'a>>,
}
#[derive(Debug)]
pub struct CompleteBoutOutcome {
    pub receipt: Value,
    pub final_state: SwarmRunState,
    pub summary: Value,
    pub novella: String,
    pub run_directory: Option<String>,
}

fn retained_ddc_steps<'a>(
    emitters: Option<&'a EmitterSuite<'_>>,
) -> Result<Option<&'a [DdcStep]>, Refusal> {
    emitters
        .and_then(|suite| suite.ddc.as_ref())
        .map(|sink| {
            sink.recorded_steps().ok_or_else(|| {
                refusal(
                    "ADVERSARY_DDC_TAPE_UNAVAILABLE",
                    "a configured DDC sink must expose its retained tape for bout persistence",
                )
            })
        })
        .transpose()
}

/// Bind the run's offset to the retained prefix before any collaborator runs.
/// A missing sink is an explicit emission mode; an unreadable sink is a refusal.
struct DdcTapeCheckpoint {
    prefix: Option<Vec<DdcStep>>,
}
impl DdcTapeCheckpoint {
    fn capture(emitters: Option<&EmitterSuite<'_>>, offset: usize) -> Result<Self, Refusal> {
        let steps = retained_ddc_steps(emitters)?;
        if offset != steps.map_or(0, |steps| steps.len()) {
            return Err(refusal(
                "ADVERSARY_DDC_OFFSET_MISMATCH",
                "ddc_step_offset must equal the retained tape length before the bout",
            ));
        }
        Ok(Self {
            prefix: steps.map(|steps| steps.to_vec()),
        })
    }

    fn finish<'a>(&self, emitters: Option<&'a EmitterSuite<'_>>) -> Result<&'a [DdcStep], Refusal> {
        match (&self.prefix, retained_ddc_steps(emitters)?) {
            (None, None) => Ok(&[]),
            (Some(prefix), Some(steps)) if steps.starts_with(prefix) => Ok(&steps[prefix.len()..]),
            _ => Err(refusal(
                "ADVERSARY_DDC_TAPE_CHANGED",
                "the configured DDC tape or its retained prefix changed during the bout",
            )),
        }
    }
}

pub fn carrier_state_digest(network: &Network, cochain: &ExactCochain) -> Result<String, Refusal> {
    let mut material = network.to_dict()?;
    material["cochains"] = Value::Array(
        network
            .edges()
            .iter()
            .map(|edge| {
                let val = cochain
                    .value(edge)
                    .cloned()
                    .unwrap_or_else(BigRational::zero);
                json!([edge, canonical_rational(&val)])
            })
            .collect(),
    );
    Ok(sha256_ref(
        record(&material)?
            .json(JsonStyle::CompactSortedAscii)?
            .as_bytes(),
    ))
}
fn regge(
    network: &Network,
    cochain: &ExactCochain,
    context: Option<&Map<String, Value>>,
    port: &mut Option<&mut dyn ReggeScoringPort>,
) -> Result<Map<String, Value>, Refusal> {
    let declared = context
        .and_then(|c| c.get("regge_spacetime"))
        .is_some_and(truthy);
    if !declared && network.tetrahedra().is_empty() && network.four_simplices().is_empty() {
        return Ok(Map::new());
    }
    if declared && network.tetrahedra().is_empty() {
        return Err(refusal(
            "REGGE_DEFICIT_UNAVAILABLE",
            "regge_spacetime is declared but the carrier has no tetrahedra",
        ));
    }
    match port.as_mut() {
        None => Err(refusal(
            "REGGE_DEFICIT_UNAVAILABLE",
            "a higher complex is declared but the scorer cannot measure Regge deficits",
        )),
        Some(port) => port.compute(network, cochain).map_err(|r| {
            refusal(
                "REGGE_DEFICIT_UNAVAILABLE",
                format!(
                    "Regge deficit computation failed on a declared complex: {}",
                    r.message
                ),
            )
        }),
    }
}
fn lowered(before: &ObstructionMeasurement, after: &ObstructionMeasurement) -> bool {
    before.is_measured()
        && after.is_measured()
        && (after.phi1() < before.phi1() || after.gamma2() < before.gamma2())
}

fn transition(
    host: &mut Option<&mut dyn BoutHostPort>,
    edge: &str,
    task: &str,
    receipts: &mut Vec<Value>,
    scenes: &mut SceneOrchestration,
    objective: &str,
    recorder: &mut RecordingSeatPort<'_>,
) -> Result<(), Refusal> {
    let request =
        json!({"action":"transition", "edge":edge, "task_key":task, "authority_effect":"None"});
    let evidence = match host.as_mut() {
        Some(port) => port.execute(request.to_string().as_bytes())?,
        None => json!({"status":"NOT_CONFIGURED","authority_effect":"None"}),
    };
    receipts.push(json!({"edge":edge,"evidence":evidence,"authority_effect":"None"}));
    scenes.run_edge(edge, task, objective, recorder, |scene_edge| {
        match host.as_mut() {
            Some(port) => port.execute(json!({"action":"transition","edge":scene_edge,"task_key":task,"authority_effect":"None"}).to_string().as_bytes()),
            None => Ok(json!({"status":"NOT_CONFIGURED","authority_effect":"None"})),
        }
    })?;
    Ok(())
}

fn resolve_initial_state(
    input: &CompleteBoutInput<'_>,
    scheduler: &mut dyn SchedulerPort,
    run_key: &str,
) -> Result<SwarmRunState, Refusal> {
    if let Some(state) = &input.initial_state {
        Ok(state.clone())
    } else {
        scheduler
            .start(run_key, input.packet)
            .map_err(|r| refusal("ADVERSARY_SCHEDULER_START_REFUSED", r.message))
    }
}

fn notify_host_bout_start(
    host: &mut Option<&mut dyn BoutHostPort>,
    run_key: &str,
    objective: &str,
) -> Result<(), Refusal> {
    if let Some(host) = host.as_mut() {
        let request = record(&json!({"action":"bout_start","task_key":run_key,"objective":objective,"authority_effect":"None"}))?.json(JsonStyle::SpacedSortedAscii)?;
        host.execute(request.as_bytes())?;
    }
    Ok(())
}

fn notify_host_candidate_stage(
    host: &mut Option<&mut dyn BoutHostPort>,
    run_key: &str,
    stage: &str,
    candidates: &Value,
    transition_receipts: &mut Vec<Value>,
) -> Result<(), Refusal> {
    if let Some(host) = host.as_mut() {
        transition_receipts.push(
            host.execute(
                json!({"action":"anti_skill_candidate_stage",
            "task_key":run_key,"stage":stage,"authority_effect":"None",
            "candidates":candidates})
                .to_string()
                .as_bytes(),
            )?,
        );
    }
    Ok(())
}

fn notify_host_regression_screen(
    host: &mut Option<&mut dyn BoutHostPort>,
    run_key: &str,
    candidates: &[Value],
) -> Result<(), Refusal> {
    if let Some(host) = host.as_mut() {
        host.execute(
            json!({"action":"candidate_regression_screen","task_key":run_key,"authority_effect":"None","candidates":candidates})
                .to_string()
                .as_bytes(),
        )?;
    }
    Ok(())
}

fn notify_host_gate_authorization(
    host: &mut Option<&mut dyn BoutHostPort>,
    run_key: &str,
    receipt_id: &Value,
    status: &str,
    has_run_dir: bool,
) -> Result<(), Refusal> {
    if has_run_dir {
        if let Some(host) = host.as_mut() {
            let request = record(&json!({"action":"gate_authorization_record","task_key":run_key,"receipt_id":receipt_id,"status":status,"authority_effect":"None"}))?.json(JsonStyle::SpacedSortedAscii)?;
            host.execute(request.as_bytes())?;
        }
    }
    Ok(())
}

fn evaluate_post_lift_measurement(
    input: &CompleteBoutInput<'_>,
    lift: &crate::gauge_break::GaugeBreakOutcome,
    pre: &crate::obstruction_identification::ObstructionIdentificationOutcome,
    scorer: &mut Option<&mut dyn CochainScoringPort>,
    regge_port: &mut Option<&mut dyn ReggeScoringPort>,
    deficits: &mut Map<String, Value>,
    run_key: &str,
    time: &AuthorizationTime<'_>,
) -> Result<Option<crate::obstruction_identification::ObstructionIdentificationOutcome>, Refusal> {
    let admissible = input
        .carrier_context
        .and_then(|c| c.get("ground_truth_admissible"))
        .is_none_or(truthy);
    if !lift.triggered() || !admissible {
        return Ok(None);
    }
    let post = execute_act2_obstruction_identification(
        &ObstructionIdentificationInput {
            network: lift.network(),
            initial_cochain: lift.cochain(),
            ablation_flags: input.ablation_flags,
            run_key,
            now_utc: input.now_utc,
        },
        scorer.as_mut().map(|p| &mut **p as &mut dyn CochainScoringPort),
        None,
        time,
    )?;
    if lowered(pre.measurement(), post.measurement()) {
        return Err(refusal(
            "ADVERSARY_LIFT_LOWERED_OBSTRUCTION",
            format!(
                "the lifted carrier measured below the carrier it was lifted from (Phi1 {} -> {}, Gamma2 {} -> {}); a lift must transport the cochain, not replace it",
                pre.measurement().phi1_text().unwrap_or_else(|| "None".into()),
                post.measurement().phi1_text().unwrap_or_else(|| "None".into()),
                pre.measurement().gamma2_text().unwrap_or_else(|| "None".into()),
                post.measurement().gamma2_text().unwrap_or_else(|| "None".into())
            ),
        ));
    }
    *deficits = regge(
        lift.network(),
        lift.cochain(),
        input.carrier_context,
        regge_port,
    )?;
    Ok(Some(post))
}

fn notify_pre_selection_stage(
    host: &mut Option<&mut dyn BoutHostPort>,
    run_key: &str,
    proposals: &crate::candidate_proposals::CandidateProposalsOutcome,
    witnesses: &crate::independent_witness::IndependentWitnessOutcome,
    transition_receipts: &mut Vec<Value>,
) -> Result<(), Refusal> {
    if host.is_none() {
        return Ok(());
    }
    let selected = proposals
        .candidates_data()
        .iter()
        .filter(|row| {
            witnesses.surviving_candidates().iter().any(|candidate| {
                row["candidate_id"].as_str() == Some(candidate.candidate_id().as_str())
            })
        })
        .collect::<Vec<_>>();
    notify_host_candidate_stage(
        host,
        run_key,
        "PRE_SELECTION",
        &json!(selected),
        transition_receipts,
    )
}

fn resolve_terminal_verdict(
    authorized: bool,
    request_external_admission: &Value,
) -> &'static str {
    // Internal finite checker acceptance is a completed bout even when the
    // caller does not request external admission. Neither a model disposition
    // nor an admission request can bypass the native authorization gate.
    if authorized {
        if truthy(request_external_admission) {
            "PROPOSED_FOR_EXTERNAL_ADMISSION"
        } else {
            "PASS_TO_MASTER"
        }
    } else {
        "COMPOSTED"
    }
}

fn completion_step_inputs() -> Result<(AgentResult, ProgressMeasure), Refusal> {
    let result = serde_json::from_value(json!({
        "agent_id": "bout_completion",
        "trust_domain": "PRODUCER",
        "scene_id": "act7_crystallization",
        "work_packet_id": "sha256:5ff31e0b5eae62a930768881cb6ab6d1f7fbd818cf2344cefae5dc0ceab99ef0",
        "status": "PASS",
        "candidate_ids": [],
        "challenge_ids": [],
        "artifact_refs": [],
        "residual_codes": [],
        "causal_parent_ids": [],
        "authority_effect": "None",
        "schema_version": "core.oeas.agent-result.v1"
    }))
    .map_err(|e| refusal("ADVERSARY_BOUT_RECORD_INVALID", e.to_string()))?;
    let progress = serde_json::from_value(json!({
        "changed_state": 1,
        "authority_effect": "None",
        "schema_version": "core.oeas.progress-measure.v1"
    }))
    .map_err(|e| refusal("ADVERSARY_BOUT_RECORD_INVALID", e.to_string()))?;
    Ok((result, progress))
}

fn build_final_swarm_state(
    initial_state: &SwarmRunState,
    round_count: i64,
    scene_orchestration: &SceneOrchestration,
    scheduler: &mut dyn SchedulerPort,
) -> Result<SwarmRunState, Refusal> {
    let mut state = value(initial_state)?;
    state["current_scene_id"] = json!("act7_crystallization");
    state["visit_counts"] = json!([{"scene_id":"act1_perception","count":1},{"scene_id":"act2_panel_debate","count":round_count.max(1)},{"scene_id":"act3_epistemic_sieve","count":1},{"scene_id":"act4_sandbox","count":1},{"scene_id":"act5_terminal_verdict","count":1},{"scene_id":"act6_intern_report","count":1},{"scene_id":"act7_crystallization","count":1}]);
    let mut visits: BTreeMap<String, u64> = state["visit_counts"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|row| Some((row["scene_id"].as_str()?.to_owned(), row["count"].as_u64()?)))
        .collect();
    for (scene, count) in scene_orchestration.visits() {
        *visits.entry(scene.clone()).or_default() += *count;
    }
    state["visit_counts"] = Value::Array(
        visits
            .into_iter()
            .map(|(scene, count)| json!({"scene_id":scene,"count":count}))
            .collect(),
    );
    state["remaining_budget"] = json!(state["remaining_budget"]
        .as_u64()
        .unwrap_or(0)
        .saturating_sub(7 + scene_orchestration.compute_spent()));
    state["scene_steps"] = json!(7 + scene_orchestration.steps());
    state["terminal_status"] = json!("RUNNING");
    state["state_id"] = json!("");
    let prepared: SwarmRunState = serde_json::from_value(state)
        .map_err(|e| refusal("ADVERSARY_BOUT_RECORD_INVALID", e.to_string()))?;
    let (result, progress) = completion_step_inputs()?;
    // The stored status is this result. Do not mark COMPLETED before advance.
    scheduler.advance(&prepared, &result, &progress)
}

fn finalize_ddc_and_governance(
    ddc_checkpoint: &DdcTapeCheckpoint,
    emitters: Option<&EmitterSuite<'_>>,
    governance_port: &mut dyn GovernancePort,
    objective: &str,
    run_key: &str,
) -> Result<(Vec<RenderRecord>, String, Option<String>, Value, String), Refusal> {
    let steps = ddc_checkpoint
        .finish(emitters)?
        .iter()
        .map(|s| record(&value(s)?))
        .collect::<Result<Vec<_>, Refusal>>()?;
    let letter_tape = steps
        .iter()
        .map(|s| {
            s.as_object()
                .ok()
                .and_then(|s| s.get("letter"))
                .and_then(|s| s.as_str().ok())
                .unwrap_or("")
        })
        .collect::<String>();
    let ddc_hash = ddc_trace_digest(&steps)?;
    let governance = governance_port.resolve_and_verify(&GovernanceRequest {
        objective,
        task_key: run_key,
        letter_tape: &letter_tape,
    })?;
    let governance_digest = sha256_ref(
        &serde_json::to_vec(&governance)
            .map_err(|e| refusal("ADVERSARY_BOUT_RECORD_INVALID", e.to_string()))?,
    );
    Ok((steps, letter_tape, ddc_hash, governance, governance_digest))
}

fn classify_joint_kernel_and_degree(
    measurement: &ObstructionMeasurement,
    carrier_status: &str,
) -> (&'static str, Value) {
    let joint = if measurement.is_exact_joint_zero() {
        "ZERO_ON_DECLARED_CARRIER"
    } else if measurement.is_measured() {
        "OPEN_RESIDUAL"
    } else {
        "NOT_MEASURED"
    };
    let degree = if carrier_status == "DECLARED" {
        json!(1)
    } else {
        Value::Null
    };
    (joint, degree)
}

fn attach_summary_extras(
    summary: &mut Value,
    input: &CompleteBoutInput<'_>,
    framing: &crate::carrier_framing::CarrierFramingOutcome,
    sieve: &crate::bout_auxiliary::EpistemicSieveOutcome,
    sandbox: &crate::bout_auxiliary::SandboxOutcome,
    proposals: &crate::candidate_proposals::CandidateProposalsOutcome,
    selected_candidate_id: &Value,
    transition_receipts: Vec<Value>,
    scene_orchestration: &SceneOrchestration,
) {
    summary["bundle_schema"] = json!("core.adversary.run-bundle.v3");
    summary["bundle_schema_version"] = json!(crate::run_persistence::RUN_BUNDLE_V3);
    if let Some(preparation) = input
        .carrier_context
        .and_then(|context| context.get("adversary_prompt_preparation"))
    {
        summary["forge"] = preparation.clone();
        if let Some(seed) = preparation.get("seed").and_then(Value::as_str) {
            summary["original_seed"] = json!(seed);
        }
    }
    summary["transition_receipts"] = json!(transition_receipts);
    summary["scene_orchestration"] = json!(scene_orchestration.observations());
    summary["candidate_artifacts"] = Value::Array(
        proposals
            .candidates_data()
            .iter()
            .map(|row| {
                json!({"candidate_id":row["candidate_id"], "content":row["content"], "content_sha256":row["content_sha256"], "selected":&row["candidate_id"] == selected_candidate_id})
            })
            .collect(),
    );
    if let Some(plan) = input.instruction_plan {
        summary["instruction_plan"] = json!(plan);
    }
    summary["prompt_sbe"] = framing.prompt_sbe().to_dict();
    summary["sieve_sbe"] = sieve.report().to_dict();
    summary["seat_reported_sandbox_disposition"] = json!(sandbox.disposition());
    summary["antibodies_loaded"] = json!(framing
        .active_antibodies()
        .iter()
        .map(|antibody| antibody.to_dict())
        .collect::<Vec<_>>());
    summary["reporting"] = json!({"status":"FINALIZED","task_outcome_changed":false});
}

fn attach_receipt_extras(receipt: &mut Value, input: &CompleteBoutInput<'_>) {
    if let Some(panel) = input.panel {
        receipt["panel"] = panel.clone();
    }
    if let Some(plan) = input.instruction_plan {
        receipt["instruction_plan_digest"] = json!(plan.plan_digest);
        receipt["instruction_manifest_digest"] = json!(plan.manifest_digest);
        receipt["ordered_bodies_digest"] = json!(plan.ordered_bodies_digest);
    }
}

fn emit_novella_narrative_event(
    run_key: &str,
    novella: &str,
    emitters: &mut Option<EmitterSuite<'_>>,
    time: &AuthorizationTime<'_>,
) -> Result<(), Refusal> {
    if let Some(suite) = emitters.as_mut() {
        let id = sha256_ref(format!("{run_key}:uns").as_bytes());
        let (event, bytes) = build_intelligence_event(
            EventDescriptor {
                ie_id: &id,
                actor_id: "actor_mythos_secretary",
                actor_kind: "SWARM_CHRONICLER",
                event_kind: "NARRATIVE",
                source_system: "oeas.uns",
                session_id: run_key,
                parent_ie_id: vec![],
                object_ids: vec![],
                terminal: true,
            },
            Payload::Text(novella),
            time.event_clock,
        )?;
        emit_event(&event, &bytes, suite, None, None)?;
    }
    Ok(())
}

fn extract_novella_and_uts(reports: &Value) -> Result<(String, String), Refusal> {
    let novella = reports["novella_md"]
        .as_str()
        .ok_or_else(|| refusal("ADVERSARY_REPORT_HISTORY_INVALID", "native novella missing"))?
        .to_owned();
    let uts = reports["uts_jsonl"]
        .as_str()
        .ok_or_else(|| refusal("ADVERSARY_REPORT_HISTORY_INVALID", "native UTS missing"))?
        .to_owned();
    Ok((novella, uts))
}

fn publish_and_persist_reports(
    summary: &mut Value,
    receipt: &mut Value,
    novella: &mut String,
    terminal: &str,
    run_key: &str,
    steps: &[RenderRecord],
    emitters: &mut Option<EmitterSuite<'_>>,
    artifacts: &mut dyn RunArtifactPort,
    progress: &mut String,
    time: &AuthorizationTime<'_>,
) -> Result<String, Refusal> {
    let reports = project_run_reports(
        summary,
        &json!({"work_status":"COMPLETED","checkpoint_finalized":true,
    "evidence_verdict":terminal}),
        "summary.json",
    )?;
    let (novella_text, uts) = extract_novella_and_uts(&reports)?;
    *novella = novella_text;
    emit_novella_narrative_event(run_key, novella, emitters, time)?;
    *progress = "PERSIST".into();
    let receipt_id = content_addressed_receipt_id_v3(novella, steps, &record(summary)?, &uts)?;
    summary["receipt_id"] = json!(receipt_id);
    receipt["receipt_id"] = json!(receipt_id);
    receipt["bundle_schema_version"] = json!(crate::run_persistence::RUN_BUNDLE_V3);
    persist_bout_run_folder_v3(
        &PersistenceInput {
            run_key,
            receipt: &record(receipt)?,
            novella_md: novella,
            dda_steps: steps,
            summary_data: &record(summary)?,
        },
        &uts,
        artifacts,
    )
}

fn record_publication_failure(
    failure: Refusal,
    summary: &mut Value,
    receipt: &mut Value,
    _steps: &[RenderRecord],
    recorder: &mut RecordingSeatPort<'_>,
) {
    for record in [summary, receipt] {
        if let Some(fields) = record.as_object_mut() {
            for key in [
                "receipt_id",
                "bundle_schema_version",
                "novella_sha256",
                "ddc_sha256",
                "summary_sha256",
            ] {
                fields.remove(key);
            }
        }
        record["reporting"] = json!({"status":"REPORTING_FAILED",
            "failure_code":failure.code,"message":failure.message,"task_outcome_changed":false});
    }
    recorder.journal_residuals.push(failure);
}

fn resolve_publication_outcome(
    publication: Result<String, Refusal>,
    summary: &mut Value,
    receipt: &mut Value,
    steps: &[RenderRecord],
    recorder: &mut RecordingSeatPort<'_>,
) -> Option<String> {
    match publication {
        Ok(path) => Some(path),
        Err(failure) => {
            record_publication_failure(failure, summary, receipt, steps, recorder);
            match crate::run_persistence::dda_tape(steps) {
                Ok(tape) => {
                    summary["report_retry_dda_actions_hex"] = json!(hex::encode(tape.bytes))
                }
                Err(retention) => {
                    summary["reporting"]["dda_retention_failure"] = json!(retention.code)
                }
            }
            None
        }
    }
}

struct BoutActs1To4Result {
    framing: crate::carrier_framing::CarrierFramingOutcome,
    pre: crate::obstruction_identification::ObstructionIdentificationOutcome,
    post: Option<crate::obstruction_identification::ObstructionIdentificationOutcome>,
    deficits: Map<String, Value>,
    proposals: crate::candidate_proposals::CandidateProposalsOutcome,
    lift: crate::gauge_break::GaugeBreakOutcome,
}

fn execute_bout_acts_1_and_2(
    input: &CompleteBoutInput<'_>,
    ports: &mut CompleteBoutPorts<'_>,
    recorder: &mut RecordingSeatPort<'_>,
    transition_receipts: &mut Vec<Value>,
    scene_orchestration: &mut SceneOrchestration,
    progress: &mut String,
    time: &AuthorizationTime<'_>,
) -> Result<
    (
        crate::carrier_framing::CarrierFramingOutcome,
        crate::obstruction_identification::ObstructionIdentificationOutcome,
        Map<String, Value>,
    ),
    Refusal,
> {
    let run_key = input.packet.task_key();
    let objective = input.packet.objective();
    transition(
        &mut ports.host,
        "PRE_DISPATCH->ACT_I",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "ACT_I".into();
    let framing = execute_act1_carrier_framing(
        &CarrierFramingInput {
            run_key,
            objective,
            carrier_json: input.carrier_json,
            now_utc: input.now_utc,
        },
        ports.diagnostic,
        ports.emitters.as_mut(),
        time,
    )?;
    transition(
        &mut ports.host,
        "ACT_I->ACT_II",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "ACT_II".into();
    let pre = execute_act2_obstruction_identification(
        &ObstructionIdentificationInput {
            network: framing.network(),
            initial_cochain: framing.initial_cochain(),
            ablation_flags: input.ablation_flags,
            run_key,
            now_utc: input.now_utc,
        },
        ports
            .scorer
            .as_mut()
            .map(|p| &mut **p as &mut dyn CochainScoringPort),
        ports.emitters.as_mut(),
        time,
    )?;
    let deficits = regge(
        framing.network(),
        framing.initial_cochain(),
        input.carrier_context,
        &mut ports.regge,
    )?;
    Ok((framing, pre, deficits))
}

fn execute_bout_acts_1_to_4(
    input: &CompleteBoutInput<'_>,
    ports: &mut CompleteBoutPorts<'_>,
    recorder: &mut RecordingSeatPort<'_>,
    transition_receipts: &mut Vec<Value>,
    scene_orchestration: &mut SceneOrchestration,
    progress: &mut String,
    time: &AuthorizationTime<'_>,
) -> Result<BoutActs1To4Result, Refusal> {
    let run_key = input.packet.task_key();
    let objective = input.packet.objective();
    let (framing, pre, mut deficits) = execute_bout_acts_1_and_2(
        input,
        ports,
        recorder,
        transition_receipts,
        scene_orchestration,
        progress,
        time,
    )?;
    transition(
        &mut ports.host,
        "ACT_II->ACT_III",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "ACT_III".into();
    let proposals = execute_act3_candidate_proposal_generation(
        &CandidateProposalsInput {
            packet_id: input.packet.packet_id(),
            run_key,
            objective,
            max_candidate_budget: input.max_candidate_budget,
            now_utc: input.now_utc,
        },
        Some(recorder),
        ports.emitters.as_mut(),
        time,
    )?;
    let contents = proposals
        .candidates_data()
        .iter()
        .map(|c| c["content"].as_str().unwrap_or("").to_owned())
        .collect::<Vec<_>>();
    notify_host_candidate_stage(
        &mut ports.host,
        run_key,
        "POST_PRODUCTION",
        &json!(proposals.candidates_data()),
        transition_receipts,
    )?;
    transition(
        &mut ports.host,
        "ACT_III->ACT_IV",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "ACT_IV".into();
    let lift = execute_act4_gauge_break(
        &GaugeBreakInput {
            network: framing.network(),
            initial_cochain: framing.initial_cochain(),
            candidate_contents: &contents,
            measurement: pre.measurement(),
            ablation_flags: input.ablation_flags,
            run_key,
            now_utc: input.now_utc,
        },
        ports.diagnostic,
        Some(recorder),
        ports.emitters.as_mut(),
        time,
    )?;
    let post = evaluate_post_lift_measurement(
        input,
        &lift,
        &pre,
        &mut ports.scorer,
        &mut ports.regge,
        &mut deficits,
        run_key,
        time,
    )?;
    Ok(BoutActs1To4Result {
        framing,
        pre,
        post,
        deficits,
        proposals,
        lift,
    })
}

struct BoutActs5And6Result {
    sieve: crate::bout_auxiliary::EpistemicSieveOutcome,
    sandbox: crate::bout_auxiliary::SandboxOutcome,
    witnesses: crate::independent_witness::IndependentWitnessOutcome,
    checks: BTreeMap<String, crate::evidence::CandidateCheck>,
    residual: crate::residual_ledger::ResidualLedgerOutcome,
}

fn execute_bout_sandbox_through_act6(
    input: &CompleteBoutInput<'_>,
    ports: &mut CompleteBoutPorts<'_>,
    recorder: &mut RecordingSeatPort<'_>,
    proposals: &crate::candidate_proposals::CandidateProposalsOutcome,
    lift: &crate::gauge_break::GaugeBreakOutcome,
    measurement: &ObstructionMeasurement,
    transition_receipts: &mut Vec<Value>,
    scene_orchestration: &mut SceneOrchestration,
    progress: &mut String,
    time: &AuthorizationTime<'_>,
) -> Result<BoutActs5And6Result, Refusal> {
    let run_key = input.packet.task_key();
    let objective = input.packet.objective();
    transition(
        &mut ports.host,
        "ACT_IV->SANDBOX",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "SANDBOX".into();
    let data = proposals
        .candidates_data()
        .iter()
        .map(|c| CandidateContent {
            candidate_id: c["candidate_id"].as_str().unwrap_or(""),
            content: c["content"].as_str().unwrap_or(""),
        })
        .collect::<Vec<_>>();
    notify_host_regression_screen(&mut ports.host, run_key, proposals.candidates_data())?;
    let sieve = execute_act3_epistemic_sieve(
        &EpistemicSieveInput {
            objective,
            candidates: proposals.candidates(),
            candidates_data: &data,
        },
        ports.diagnostic,
    )?;
    let sandbox = execute_act4_sandbox_with_candidates(Some(recorder), objective, &data)?;
    let payloads: BTreeMap<String, Vec<u8>> = data
        .iter()
        .filter(|c| !c.candidate_id.is_empty())
        .map(|c| (c.candidate_id.into(), c.content.as_bytes().to_vec()))
        .collect();
    transition(
        &mut ports.host,
        "SANDBOX->ACT_V",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "ACT_V".into();
    let witnesses = execute_act5_independent_witness(
        &IndependentWitnessInput {
            run_key,
            objective,
            candidates: proposals.candidates(),
            dead_candidates: proposals.dead_candidates(),
            candidate_payloads: &payloads,
            ablation_flags: input.ablation_flags,
            max_critique_rounds: input.max_critique_rounds,
            now_utc: input.now_utc,
        },
        Some(recorder),
        ports.emitters.as_mut(),
        time,
    )?;
    let (checks, residual) = execute_checker_and_act6(
        input,
        ports,
        recorder,
        &witnesses,
        &payloads,
        lift,
        measurement,
        transition_receipts,
        scene_orchestration,
        progress,
        time,
    )?;
    Ok(BoutActs5And6Result {
        sieve,
        sandbox,
        witnesses,
        checks,
        residual,
    })
}

fn execute_checker_and_act6(
    input: &CompleteBoutInput<'_>,
    ports: &mut CompleteBoutPorts<'_>,
    recorder: &mut RecordingSeatPort<'_>,
    witnesses: &crate::independent_witness::IndependentWitnessOutcome,
    payloads: &BTreeMap<String, Vec<u8>>,
    lift: &crate::gauge_break::GaugeBreakOutcome,
    measurement: &ObstructionMeasurement,
    transition_receipts: &mut Vec<Value>,
    scene_orchestration: &mut SceneOrchestration,
    progress: &mut String,
    time: &AuthorizationTime<'_>,
) -> Result<
    (
        BTreeMap<String, crate::evidence::CandidateCheck>,
        crate::residual_ledger::ResidualLedgerOutcome,
    ),
    Refusal,
> {
    let run_key = input.packet.task_key();
    let objective = input.packet.objective();
    transition(
        &mut ports.host,
        "ACT_V->CHECKER",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "CHECKER".into();
    let carrier_hash = carrier_state_digest(lift.network(), lift.cochain())?;
    let checks = execute_candidate_checks(
        ports.checker.take(),
        &CandidateChecksInput {
            run_key,
            objective,
            candidates: witnesses.surviving_candidates(),
            candidate_payloads: payloads,
            carrier_context: input.carrier_context,
            measurement: Some(measurement),
            carrier_state_hash: Some(&carrier_hash),
            now_utc: input.now_utc,
        },
        ports.emitters.as_mut(),
        time,
    )?;
    transition(
        &mut ports.host,
        "CHECKER->ACT_VI",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "ACT_VI".into();
    let residual = execute_act6_residual_ledger(
        &ResidualLedgerInput {
            dead_candidates: witnesses.dead_candidates(),
            critiques: witnesses.critiques(),
            critique_verdicts: witnesses.critique_verdicts(),
            measurement,
            ablation_flags: input.ablation_flags,
            run_key,
            now_utc: input.now_utc,
        },
        ports.emitters.as_mut(),
        time,
    )?;
    Ok((checks, residual))
}

fn build_bout_summary_and_receipt(
    input: &CompleteBoutInput<'_>,
    acts1_to_4: &BoutActs1To4Result,
    acts5_and_6: &BoutActs5And6Result,
    authorization: &crate::authorization::AuthorizationOutcome,
    crystallization: &crate::bout_auxiliary::CrystallizationOutcome,
    proposal: &Value,
    terminal: &str,
    scheduler_status: &str,
    ddc_hash: &Option<String>,
    letter_tape: &str,
    governance: Value,
    governance_digest: String,
    recorder: &RecordingSeatPort<'_>,
    transition_receipts: Vec<Value>,
    scene_orchestration: &SceneOrchestration,
) -> Result<(Value, Value), Refusal> {
    let run_key = input.packet.task_key();
    let objective = input.packet.objective();
    let measurement = acts1_to_4
        .post
        .as_ref()
        .map(|p| p.measurement())
        .unwrap_or(acts1_to_4.pre.measurement());
    let narrative = authorization.narrative();
    let blockers = narrative
        .get("authorization_blockers")
        .cloned()
        .unwrap_or(json!([]));
    let checker_verdict = narrative
        .get("checker_verdict")
        .cloned()
        .unwrap_or(json!("NOT_MEASURED"));
    let checker_digest = narrative
        .get("checker_receipt_sha256")
        .cloned()
        .unwrap_or(Value::Null);
    let evidence = narrative
        .get("authorization_evidence")
        .cloned()
        .unwrap_or(Value::Null);
    let mut evidence_receipts = narrative
        .get("evidence_receipts")
        .and_then(Value::as_object)
        .cloned()
        .unwrap_or_default();
    evidence_receipts.insert(governance_digest.clone(), governance.clone());
    let mut evidence_refs = proposal["evidence_refs"]
        .as_array()
        .cloned()
        .unwrap_or_default();
    evidence_refs.push(json!(governance_digest));
    let (joint, degree) =
        classify_joint_kernel_and_degree(measurement, acts1_to_4.framing.carrier_status());
    let measured = measurement.to_dict()?;
    let pre_lift = if acts1_to_4.post.is_some() {
        acts1_to_4.pre.measurement().to_dict()?
    } else {
        Value::Null
    };
    let mut summary = json!({"asd_telemetry":acts1_to_4.lift.telemetry(),"authority_effect":"None","authorization_blockers":blockers,"authorization_evidence":evidence,
        "candidate_checks":acts5_and_6.checks.iter().map(|(id,c)|(id.clone(),c.to_dict())).collect::<Map<String,Value>>(),"ddc_trace_hash":ddc_hash,"lggr_joint_kernel_status":joint,"carrier_degree":degree,"carrier_measurement":measured,"carrier_status":acts1_to_4.framing.carrier_status(),
        "checker_receipt_sha256":checker_digest,"checker_verdict":checker_verdict,"consecration_state":crystallization.consecration_state(),"critique_rounds":acts5_and_6.witnesses.round_count(),"critique_verdicts":acts5_and_6.witnesses.critique_verdicts(),"defect_count":measured["defect_count"],"disposition":proposal["disposition"],"evidence_receipts":evidence_receipts,"governance_bundle":governance,"fixture_seats":input.fixture_seats != &Value::Bool(false),"gamma2":measurement.gamma2_text(),"implicit_zero_edges":acts1_to_4.framing.narrative().get("implicit_zero_edges").cloned().unwrap_or(json!(0)),"is_authorized":authorization.is_authorized(),"letter_tape":letter_tape,"measurement_status":measured["status"],"nonclaims":proposal["nonclaims"],"objective":objective,"phi1":measurement.phi1_text(),"pre_lift_measurement":pre_lift,"residual_declared":acts5_and_6.residual.residual_ledger().get("residual_declared").cloned().unwrap_or(json!(false)),"seat_turns":recorder.turns,"selected_candidate_id":authorization.selected_candidate_id(),"status":authorization.status(),"task_key":run_key,"terminal_status":scheduler_status,"terminal_verdict":terminal});
    attach_summary_extras(
        &mut summary,
        input,
        &acts1_to_4.framing,
        &acts5_and_6.sieve,
        &acts5_and_6.sandbox,
        &acts1_to_4.proposals,
        &proposal["selected_candidate_id"],
        transition_receipts,
        scene_orchestration,
    );
    let mut receipt = json!({"task_key":run_key,"status":authorization.status(),"selected_candidate_id":authorization.selected_candidate_id(),"novella_sha256":"","ddc_sha256":"","summary_sha256":"","lean4_proof_hash":null,"phi1":measurement.phi1_text(),"gamma2":measurement.gamma2_text(),"defect_count":measured["defect_count"],"ablation_flags":input.ablation_flags.cloned().unwrap_or_default(),"authority_effect":"None","letter_tape":letter_tape,"measurement_status":measured["status"],"checker_receipt_sha256":checker_digest,"checker_verdict":checker_verdict,"authorization_blockers":blockers,"authorization_evidence":evidence,"ddc_trace_hash":ddc_hash,"lggr_joint_kernel_status":joint,"carrier_degree":degree});
    attach_receipt_extras(&mut receipt, input);
    Ok((summary, receipt))
}

fn execute_act7_gate_and_crystallization(
    input: &CompleteBoutInput<'_>,
    ports: &mut CompleteBoutPorts<'_>,
    recorder: &mut RecordingSeatPort<'_>,
    acts1_to_4: &BoutActs1To4Result,
    acts5_and_6: &BoutActs5And6Result,
    measurement: &ObstructionMeasurement,
    transition_receipts: &mut Vec<Value>,
    scene_orchestration: &mut SceneOrchestration,
    progress: &mut String,
    time: &AuthorizationTime<'_>,
) -> Result<
    (
        crate::authorization::AuthorizationOutcome,
        Value,
        &'static str,
        crate::bout_auxiliary::CrystallizationOutcome,
    ),
    Refusal,
> {
    let run_key = input.packet.task_key();
    let objective = input.packet.objective();
    transition(
        &mut ports.host,
        "ACT_VI->ACT_VII",
        run_key,
        transition_receipts,
        scene_orchestration,
        objective,
        recorder,
    )?;
    *progress = "ACT_VII".into();
    notify_pre_selection_stage(
        &mut ports.host,
        run_key,
        &acts1_to_4.proposals,
        &acts5_and_6.witnesses,
        transition_receipts,
    )?;
    let authorization = execute_act7_authorization_gate(
        &AuthorizationGateInput {
            run_key,
            surviving_candidates: acts5_and_6.witnesses.surviving_candidates(),
            critiques: acts5_and_6.witnesses.critiques(),
            measurement: Some(measurement),
            candidate_checks: &acts5_and_6.checks,
            carrier_context: input.carrier_context,
            ablation_flags: input.ablation_flags,
            delta2_defect: acts1_to_4.deficits.get("xi3"),
            delta3_defect: acts1_to_4.deficits.get("xi4"),
            regge_converged: acts1_to_4.deficits.get("regge_converged"),
            carrier_status: acts1_to_4.framing.carrier_status(),
            critique_verdicts: acts5_and_6.witnesses.critique_verdicts(),
            fixture_seats: input.fixture_seats,
            now_utc: input.now_utc,
        },
        ports.emitters.as_mut(),
        time,
    )?;
    let proposal = value(authorization.proposal())?;
    let terminal =
        resolve_terminal_verdict(authorization.is_authorized(), input.request_external_admission);
    let crystallization = execute_act7_crystallization(
        &CrystallizationInput {
            run_key,
            terminal_verdict: terminal,
            request_external_admission: input.request_external_admission,
            dead_candidates: acts5_and_6.witnesses.dead_candidates(),
        },
        ports.emitters.as_mut(),
    )?;
    Ok((authorization, proposal, terminal, crystallization))
}

fn initialize_bout_state_and_orchestration<'a>(
    input: &'a CompleteBoutInput<'a>,
    ports: &mut CompleteBoutPorts<'_>,
    progress: &mut String,
) -> Result<(DdcTapeCheckpoint, SwarmRunState, SceneOrchestration), Refusal> {
    *progress = "DDC_PREFLIGHT".into();
    let ddc_checkpoint =
        DdcTapeCheckpoint::capture(ports.emitters.as_ref(), input.ddc_step_offset)?;
    let run_key = input.packet.task_key();
    let objective = input.packet.objective();
    *progress = "SCHEDULER_START".into();
    let initial_state = resolve_initial_state(input, ports.scheduler, run_key)?;
    let scene_orchestration = SceneOrchestration::from_context(
        input.carrier_context,
        input.instruction_plan,
        u64::from(*initial_state.remaining_budget()),
    )?;
    notify_host_bout_start(&mut ports.host, run_key, objective)?;
    Ok((ddc_checkpoint, initial_state, scene_orchestration))
}

pub fn execute_complete_bout(
    input: &CompleteBoutInput<'_>,
    mut ports: CompleteBoutPorts<'_>,
    recorder: &mut RecordingSeatPort<'_>,
    progress: &mut String,
    time: &AuthorizationTime<'_>,
) -> Result<CompleteBoutOutcome, Refusal> {
    let mut transition_receipts = Vec::new();
    let run_key = input.packet.task_key();
    let objective = input.packet.objective();
    let (ddc_checkpoint, initial_state, mut scene_orchestration) =
        initialize_bout_state_and_orchestration(input, &mut ports, progress)?;
    let acts1_to_4 = execute_bout_acts_1_to_4(
        input,
        &mut ports,
        recorder,
        &mut transition_receipts,
        &mut scene_orchestration,
        progress,
        time,
    )?;
    let measurement = acts1_to_4
        .post
        .as_ref()
        .map(|p| p.measurement())
        .unwrap_or(acts1_to_4.pre.measurement());
    let acts5_and_6 = execute_bout_sandbox_through_act6(
        input,
        &mut ports,
        recorder,
        &acts1_to_4.proposals,
        &acts1_to_4.lift,
        measurement,
        &mut transition_receipts,
        &mut scene_orchestration,
        progress,
        time,
    )?;
    let (authorization, proposal, terminal, crystallization) =
        execute_act7_gate_and_crystallization(
            input,
            &mut ports,
            recorder,
            &acts1_to_4,
            &acts5_and_6,
            measurement,
            &mut transition_receipts,
            &mut scene_orchestration,
            progress,
            time,
        )?;
    let final_state = build_final_swarm_state(
        &initial_state,
        acts5_and_6.witnesses.round_count(),
        &scene_orchestration,
        ports.scheduler,
    )?;
    let (steps, letter_tape, ddc_hash, governance, governance_digest) = finalize_ddc_and_governance(
        &ddc_checkpoint,
        ports.emitters.as_ref(),
        ports.governance,
        objective,
        run_key,
    )?;
    *progress = "NOVELLA".into();
    let (mut summary, mut receipt) = build_bout_summary_and_receipt(
        input,
        &acts1_to_4,
        &acts5_and_6,
        &authorization,
        &crystallization,
        &proposal,
        terminal,
        final_state.terminal_status(),
        &ddc_hash,
        &letter_tape,
        governance,
        governance_digest,
        recorder,
        transition_receipts,
        &scene_orchestration,
    )?;
    let mut novella = String::new();
    let publication = publish_and_persist_reports(
        &mut summary,
        &mut receipt,
        &mut novella,
        terminal,
        run_key,
        &steps,
        &mut ports.emitters,
        ports.artifacts,
        progress,
        time,
    );
    let run_directory =
        resolve_publication_outcome(publication, &mut summary, &mut receipt, &steps, recorder);
    recorder.checkpoint_outcome(&summary);
    notify_host_gate_authorization(
        &mut ports.host,
        run_key,
        &receipt["receipt_id"],
        authorization.status(),
        run_directory.is_some(),
    )?;
    Ok(CompleteBoutOutcome {
        receipt,
        final_state,
        summary,
        novella,
        run_directory,
    })
}

// Origin: engine/crates_rs/core_adversary/src/complete_bout.rs
// Claim: urn:core:crates_rs:core-adversary:complete-bout:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod ddc_custody_tests {
    use super::*;
    use crate::stage::emission::DdcSink;

    struct Sink(Option<Vec<DdcStep>>);
    impl DdcSink for Sink {
        fn record_step(&mut self, step: &DdcStep) -> Result<String, Refusal> {
            if let Some(steps) = &mut self.0 {
                steps.push(step.clone());
            }
            Ok("recorded".into())
        }
        fn recorded_steps(&self) -> Option<&[DdcStep]> {
            self.0.as_deref()
        }
    }
    fn step(name: &str) -> Result<DdcStep, serde_json::Error> {
        serde_json::from_value(json!({
            "letter": "R",
            "before_class": "Before",
            "after_class": "After",
            "carrier_hash": sha256_ref(b"carrier"),
            "witness_hash": null,
            "receipt_sha256": sha256_ref(name.as_bytes()),
        }))
    }
    fn checkpoint(sink: &mut Sink, offset: usize) -> Result<DdcTapeCheckpoint, Refusal> {
        DdcTapeCheckpoint::capture(
            Some(&EmitterSuite {
                ddc: Some(sink),
                ..EmitterSuite::default()
            }),
            offset,
        )
    }
    fn finish(checkpoint: &DdcTapeCheckpoint, sink: &mut Sink) -> Result<Vec<DdcStep>, Refusal> {
        checkpoint
            .finish(Some(&EmitterSuite {
                ddc: Some(sink),
                ..EmitterSuite::default()
            }))
            .map(|steps| steps.to_vec())
    }

    #[test]
    fn configured_sink_must_expose_its_tape() {
        let error = checkpoint(&mut Sink(None), 0)
            .err()
            .expect("unreadable tape");
        assert_eq!(error.code, "ADVERSARY_DDC_TAPE_UNAVAILABLE");
    }

    #[test]
    fn offset_must_equal_the_existing_tape_length() -> Result<(), Box<dyn std::error::Error>> {
        let mut sink = Sink(Some(vec![step("prior-bout")?]));
        for offset in [0, 2, usize::MAX] {
            let error = checkpoint(&mut sink, offset).err().expect("bad offset");
            assert_eq!(error.code, "ADVERSARY_DDC_OFFSET_MISMATCH");
        }
        checkpoint(&mut sink, 1)?;
        Ok(())
    }

    #[test]
    fn finish_returns_only_this_bouts_suffix() -> Result<(), Box<dyn std::error::Error>> {
        let mut sink = Sink(Some(vec![step("prior-bout")?]));
        let checkpoint = checkpoint(&mut sink, 1)?;
        let first = step("first")?;
        let second = step("second")?;
        sink.record_step(&first)?;
        sink.record_step(&second)?;
        assert_eq!(finish(&checkpoint, &mut sink)?, vec![first, second]);
        Ok(())
    }

    #[test]
    fn finish_refuses_an_unreadable_tape() -> Result<(), Box<dyn std::error::Error>> {
        let mut sink = Sink(Some(Vec::new()));
        let checkpoint = checkpoint(&mut sink, 0)?;
        sink.0 = None;
        let error = finish(&checkpoint, &mut sink).expect_err("tape lost after preflight");
        assert_eq!(error.code, "ADVERSARY_DDC_TAPE_UNAVAILABLE");
        Ok(())
    }

    #[test]
    fn finish_refuses_truncated_or_replaced_prefixes() -> Result<(), Box<dyn std::error::Error>> {
        let mut sink = Sink(Some(vec![step("prior-bout")?]));
        let checkpoint = checkpoint(&mut sink, 1)?;
        for steps in [Vec::new(), vec![step("replacement")?]] {
            sink.0 = Some(steps);
            let error = finish(&checkpoint, &mut sink).expect_err("prefix changed");
            assert_eq!(error.code, "ADVERSARY_DDC_TAPE_CHANGED");
        }
        Ok(())
    }

    #[test]
    fn no_ddc_sink_is_an_explicit_mode_with_zero_offset() -> Result<(), Box<dyn std::error::Error>>
    {
        for suite in [None, Some(EmitterSuite::default())] {
            let checkpoint = DdcTapeCheckpoint::capture(suite.as_ref(), 0)?;
            assert!(checkpoint.finish(suite.as_ref())?.is_empty());
            let error = DdcTapeCheckpoint::capture(suite.as_ref(), 1)
                .err()
                .expect("no tape can supply an offset");
            assert_eq!(error.code, "ADVERSARY_DDC_OFFSET_MISMATCH");
        }
        Ok(())
    }

    #[test]
    fn finish_refuses_changed_sink_presence() -> Result<(), Box<dyn std::error::Error>> {
        let mut sink = Sink(Some(Vec::new()));
        let with_sink = checkpoint(&mut sink, 0)?;
        let error = with_sink
            .finish(None)
            .expect_err("configured sink disappeared");
        assert_eq!(error.code, "ADVERSARY_DDC_TAPE_CHANGED");
        let without_sink = DdcTapeCheckpoint::capture(None, 0)?;
        let error = finish(&without_sink, &mut sink).expect_err("unexpected sink appeared");
        assert_eq!(error.code, "ADVERSARY_DDC_TAPE_CHANGED");
        Ok(())
    }
}

#[cfg(test)]
mod scheduler_status_order {
    use super::build_final_swarm_state;
    use crate::scene_orchestration::SceneOrchestration;
    use crate::stage::packets::AgentResult;
    use crate::stage::ports::{Refusal, SchedulerPort};
    use crate::stage::run::{ProgressMeasure, SwarmRunState};
    use serde_json::json;

    struct Spy {
        seen: String,
    }

    impl SchedulerPort for Spy {
        fn start(
            &mut self,
            _: &str,
            _: &crate::stage::packets::WorkPacket,
        ) -> Result<SwarmRunState, Refusal> {
            Err(Refusal::new("UNUSED", "start is not this step"))
        }

        fn advance(
            &mut self,
            state: &SwarmRunState,
            _: &AgentResult,
            _: &ProgressMeasure,
        ) -> Result<SwarmRunState, Refusal> {
            self.seen = state.terminal_status().clone();
            if self.seen == "COMPLETED" {
                return Err(Refusal::new(
                    "OEAS_SCHEDULER_ADVANCE_REFUSED",
                    "status COMPLETED written before advance",
                ));
            }
            state.with_terminal_status("HOLD").map_err(|error| {
                Refusal::new("ADVERSARY_BOUT_RECORD_INVALID", error)
            })
        }
    }

    #[test]
    fn completed_bout_stores_the_scheduler_status_after_advance() {
        let initial: SwarmRunState = serde_json::from_value(json!({
            "run_key": "bout-advance",
            "profile_id": "sha256:1900eab6c028483d7126599ee6f50de0d27907b5c65fa90524580b4b0f9852b0",
            "current_scene_id": "act1_perception",
            "visit_counts": [{"scene_id": "act1_perception", "count": 1}],
            "result_ids": [],
            "progress_measure_ids": [],
            "remaining_budget": 100,
            "scene_steps": 0,
            "dry_rounds": 0,
            "terminal_status": "RUNNING",
            "authority_effect": "None",
            "schema_version": "core.oeas.swarm-run-state.v1",
            "state_id": ""
        }))
        .expect("running state");
        let mut scheduler = Spy { seen: String::new() };
        let stored = build_final_swarm_state(&initial, 1, &SceneOrchestration::default(), &mut scheduler)
            .expect("scheduler result");
        assert_ne!(
            scheduler.seen.as_str(),
            "COMPLETED",
            "status COMPLETED written before advance"
        );
        assert_eq!(scheduler.seen.as_str(), "RUNNING");
        assert_eq!(stored.terminal_status(), "HOLD");
        assert!(!stored.state_id().is_empty());
    }
}
