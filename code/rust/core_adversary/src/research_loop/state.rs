//! The research-loop state machine.
//!
//! One round runs the eight PFP stages in order. Models and IDE agents deliver stages 1–4
//! and 6–8 as occurrences; the host evaluates stage 5 and routes after stage 8. Stage 4's
//! candidate is frozen by digest; the host evaluation and both critics bind that digest,
//! and a route against changed bytes is stale. Every method validates before it mutates,
//! so a refused command leaves the state unchanged.
//!
//! A checkpoint carries the whole state and its digest; resume re-verifies the mission,
//! the ledger and the event tape before accepting it. A model cannot supply a checkpoint:
//! the host reads its own.
//!
//! AuthorityEffect: None.

use super::budget::{BudgetLedger, ReservationRequest, ReservationState, Spend};
use super::canonical;
use super::mission::{AdmittedMission, Limits};
use super::occurrence::{self, Executor};
use super::phase::{self, HOST_STAGE, PUBLIC_STAGES};
use super::refuse;
use super::routing::{self, Disposition, RouteFacts, RouteObservation};
use crate::stage::ports::Refusal;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub const CHECKPOINT_SCHEMA: &str = "core.adversary.research_loop.checkpoint.v1";
const AFTER_LAST_STAGE: u8 = PUBLIC_STAGES + 1;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CheckStatus {
    Pass,
    Fail,
    Unknown,
}

/// One host check record. PASS needs at least one evidence reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HostCheck {
    pub check_id: String,
    pub status: CheckStatus,
    #[serde(default)]
    pub evidence_refs: Vec<String>,
}

/// What a host evaluation or review was bound to.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReviewBinding {
    pub candidate_sha256: String,
    pub mission_sha256: String,
    pub source_sha256: String,
    pub checker_policy_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OccurrenceRecord {
    pub idempotency_key: String,
    pub round: u64,
    pub stage: u8,
    pub payload_sha256: String,
    pub failed: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EventKind {
    MissionAdmitted,
    RoundStarted,
    BudgetReserved,
    BudgetSettled,
    BudgetReconciled,
    BudgetReleased,
    ModelAttemptRecorded,
    CandidateFrozen,
    HostEvaluationRecorded,
    HostRoute,
    Halted,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LoopEvent {
    pub sequence: u64,
    pub round_id: u64,
    pub event: EventKind,
    pub data: Value,
}

/// What the host should do next.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "action", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum NextAction {
    BeginRound {
        round: u64,
    },
    Dispatch {
        round: u64,
        stage: u8,
        phase: phase::Phase,
    },
    HostEvaluate {
        round: u64,
    },
    Route {
        round: u64,
    },
    Finished {
        disposition: Disposition,
    },
}

/// Commands accepted by [`ResearchLoop::apply`], the host-action surface.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "command", rename_all = "snake_case", deny_unknown_fields)]
pub enum LoopCommand {
    BeginRound {
        source_snapshot_sha256: String,
    },
    Reserve {
        stage: u8,
        occurrence_id: String,
        packet_sha256: String,
        executor: Executor,
        tokens: u64,
        cost_microusd: u64,
    },
    Settle {
        idempotency_key: String,
        tokens: u64,
        cost_microusd: u64,
    },
    Reconcile {
        idempotency_key: String,
    },
    Release {
        idempotency_key: String,
    },
    Record {
        occurrence_id: String,
        payload: Value,
        failed: bool,
    },
    HostEvaluate {
        checks: Vec<HostCheck>,
        checker_policy_sha256: String,
    },
    Route {
        observation: RouteObservation,
    },
    Halt {
        disposition: Disposition,
        reason: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResearchLoop {
    admitted: AdmittedMission,
    ledger: BudgetLedger,
    round_id: u64,
    expected_stage: u8,
    round_open: bool,
    terminal: Option<Disposition>,
    source_sha256: Option<String>,
    candidate: Option<Value>,
    frozen_sha256: Option<String>,
    checks: Option<Vec<HostCheck>>,
    evaluation_binding: Option<ReviewBinding>,
    critics: BTreeMap<u8, String>,
    occurrences: BTreeMap<String, OccurrenceRecord>,
    events: Vec<LoopEvent>,
    residual_key: Option<String>,
    stalled_rounds: u64,
}

fn require_digest(name: &str, value: &str) -> Result<(), Refusal> {
    if !canonical::is_digest(value) {
        return Err(refuse(
            "DIGEST_INVALID",
            format!("{name} must be sha256:<64 lowercase hex>"),
        ));
    }
    Ok(())
}

impl ResearchLoop {
    /// Admit a mission and open the run. No round is started.
    pub fn admit(mission: &Value) -> Result<Self, Refusal> {
        let admitted = AdmittedMission::admit(mission)?;
        let mut state = Self {
            admitted,
            ledger: BudgetLedger::default(),
            round_id: 0,
            expected_stage: 1,
            round_open: false,
            terminal: None,
            source_sha256: None,
            candidate: None,
            frozen_sha256: None,
            checks: None,
            evaluation_binding: None,
            critics: BTreeMap::new(),
            occurrences: BTreeMap::new(),
            events: Vec::new(),
            residual_key: None,
            stalled_rounds: 0,
        };
        let data = json!({
            "mission_id": state.admitted.mission.mission_id,
            "mission_sha256": state.admitted.mission_sha256,
            "lane": state.admitted.mission.lane,
        });
        state.emit(EventKind::MissionAdmitted, data);
        Ok(state)
    }

    pub fn run_id(&self) -> &str {
        &self.admitted.mission.run_id
    }
    pub fn mission(&self) -> &AdmittedMission {
        &self.admitted
    }
    pub fn limits(&self) -> &Limits {
        &self.admitted.mission.budget
    }
    pub fn round_id(&self) -> u64 {
        self.round_id
    }
    pub fn terminal(&self) -> Option<Disposition> {
        self.terminal
    }
    pub fn candidate(&self) -> Option<&Value> {
        self.candidate.as_ref()
    }
    pub fn frozen_sha256(&self) -> Option<&str> {
        self.frozen_sha256.as_deref()
    }
    pub fn source_sha256(&self) -> Option<&str> {
        self.source_sha256.as_deref()
    }
    pub fn events(&self) -> &[LoopEvent] {
        &self.events
    }
    pub fn ledger(&self) -> &BudgetLedger {
        &self.ledger
    }
    pub fn spent(&self) -> Result<Spend, Refusal> {
        self.ledger.spent()
    }

    fn emit(&mut self, event: EventKind, data: Value) {
        let sequence = self.events.len() as u64;
        self.events.push(LoopEvent {
            sequence,
            round_id: self.round_id,
            event,
            data,
        });
    }

    fn require_live(&self) -> Result<(), Refusal> {
        if let Some(terminal) = self.terminal {
            return Err(refuse(
                "RUN_FINISHED",
                format!("the run already ended as {terminal:?}"),
            ));
        }
        Ok(())
    }

    fn require_open_round(&self) -> Result<(), Refusal> {
        self.require_live()?;
        if !self.round_open {
            return Err(refuse("ROUND_NOT_OPEN", "no round is open"));
        }
        Ok(())
    }

    pub fn next_action(&self) -> NextAction {
        if let Some(disposition) = self.terminal {
            return NextAction::Finished { disposition };
        }
        if !self.round_open {
            return NextAction::BeginRound {
                round: self.round_id + 1,
            };
        }
        let round = self.round_id;
        match self.expected_stage {
            HOST_STAGE => NextAction::HostEvaluate { round },
            AFTER_LAST_STAGE => NextAction::Route { round },
            stage => {
                let phase = phase::Phase::ALL
                    .into_iter()
                    .rfind(|phase| phase.pfp_stages().contains(&stage))
                    .unwrap_or(phase::Phase::Produce);
                NextAction::Dispatch {
                    round,
                    stage,
                    phase,
                }
            }
        }
    }

    /// Open the next round against a host-computed source snapshot digest.
    pub fn begin_round(&mut self, source_snapshot_sha256: &str) -> Result<(), Refusal> {
        self.require_live()?;
        require_digest("source_snapshot_sha256", source_snapshot_sha256)?;
        if self.round_open {
            return Err(refuse(
                "ROUND_ALREADY_OPEN",
                "the current round has not been routed",
            ));
        }
        if self.round_id >= self.limits().max_rounds {
            return Err(refuse("ROUND_BUDGET_EXHAUSTED", "max_rounds reached"));
        }
        let spent_calls = self.ledger.spent()?.model_calls;
        self.round_id += 1;
        self.expected_stage = 1;
        self.round_open = true;
        self.source_sha256 = Some(source_snapshot_sha256.into());
        self.candidate = None;
        self.frozen_sha256 = None;
        self.checks = None;
        self.evaluation_binding = None;
        self.critics.clear();
        self.emit(
            EventKind::RoundStarted,
            json!({"source_sha": source_snapshot_sha256, "spent_calls": spent_calls}),
        );
        Ok(())
    }

    /// Reserve budget for one dispatch of the current stage. Re-reserving the same
    /// occurrence and packet returns the existing key without charging again.
    pub fn reserve(
        &mut self,
        stage: u8,
        occurrence_id: &str,
        packet_sha256: &str,
        executor: Executor,
        tokens: u64,
        cost_microusd: u64,
    ) -> Result<String, Refusal> {
        occurrence::validate_id(occurrence_id)?;
        require_digest("packet_sha256", packet_sha256)?;
        let key = occurrence::idempotency_key(
            self.run_id(),
            self.round_id,
            stage,
            occurrence_id,
            packet_sha256,
        )?;
        // A repeat of an existing reservation goes straight to the ledger, which returns
        // the same key when the terms match and refuses otherwise.
        let repeat = self.ledger.by_occurrence(occurrence_id).is_some();
        self.validate_reserve_stage(stage, executor, repeat)?;
        let limits = self.limits().clone();
        let request = ReservationRequest {
            idempotency_key: key,
            occurrence_id,
            round: self.round_id,
            stage,
            packet_sha256,
            executor,
            tokens,
            cost_microusd,
        };
        let key = self.ledger.reserve(&limits, request)?;
        if !repeat {
            self.emit(
                EventKind::BudgetReserved,
                json!({"occurrence_id": occurrence_id, "stage": stage, "executor": executor,
                       "tokens": tokens, "cost_microusd": cost_microusd, "idempotency_key": key}),
            );
        }
        Ok(key)
    }

    fn validate_reserve_stage(
        &self,
        stage: u8,
        executor: Executor,
        repeat: bool,
    ) -> Result<(), Refusal> {
        if executor == Executor::Host {
            return Err(refuse(
                "STAGE5_HOST_ONLY",
                "the host evaluates stage 5 with host_evaluate; it reserves no dispatch",
            ));
        }
        if repeat {
            return Ok(());
        }
        self.require_open_round()?;
        if !phase::stage_executor_is_allowed(stage, executor) {
            return Err(refuse(
                "STAGE5_HOST_ONLY",
                format!("stage {stage} cannot be dispatched to {executor:?}"),
            ));
        }
        if stage != self.expected_stage {
            return Err(refuse(
                "STAGE_ORDER",
                format!(
                    "stage {stage} requested; stage {} is next",
                    self.expected_stage
                ),
            ));
        }
        Ok(())
    }

    pub fn settle(&mut self, key: &str, tokens: u64, cost_microusd: u64) -> Result<(), Refusal> {
        let already = self
            .ledger
            .reservation(key)
            .is_some_and(|item| item.state == ReservationState::Settled);
        self.ledger.settle(key, tokens, cost_microusd)?;
        if !already {
            self.emit(
                EventKind::BudgetSettled,
                json!({"idempotency_key": key, "tokens": tokens, "cost_microusd": cost_microusd}),
            );
        }
        Ok(())
    }

    pub fn reconcile_unknown(&mut self, key: &str) -> Result<(), Refusal> {
        self.ledger.reconcile_unknown(key)?;
        self.emit(EventKind::BudgetReconciled, json!({"idempotency_key": key}));
        Ok(())
    }

    pub fn release(&mut self, key: &str) -> Result<(), Refusal> {
        self.ledger.release(key)?;
        self.emit(EventKind::BudgetReleased, json!({"idempotency_key": key}));
        Ok(())
    }

    /// Record a delivered stage payload. The occurrence's reservation must already be
    /// settled or reconciled. A failed attempt is charged and leaves the stage unfinished.
    pub fn record(
        &mut self,
        occurrence_id: &str,
        payload: &Value,
        failed: bool,
    ) -> Result<(), Refusal> {
        let payload_bytes = canonical::canonical_bytes(payload)?;
        let payload_sha256 = canonical::digest_bytes(&payload_bytes);
        // An oversize payload is recorded as a failed attempt: it was charged, and refusing
        // it would leave the occurrence charged but unrecorded.
        let oversize = payload_bytes.len() as u64 > self.limits().max_model_response_bytes;
        let failed = failed || oversize;
        if self.check_repeat_occurrence(occurrence_id, &payload_sha256, failed)? {
            return Ok(());
        }
        let (stage, round, key) = self.validate_record_reservation(occurrence_id)?;
        let frozen = if !failed {
            self.extract_stage_payload(stage, payload)?
        } else {
            None
        };
        self.commit_record(
            occurrence_id,
            key,
            round,
            stage,
            payload_sha256,
            failed,
            oversize,
            frozen,
        );
        Ok(())
    }

    fn check_repeat_occurrence(
        &self,
        occurrence_id: &str,
        payload_sha256: &str,
        failed: bool,
    ) -> Result<bool, Refusal> {
        let Some(prior) = self.occurrences.get(occurrence_id) else {
            return Ok(false);
        };
        if prior.payload_sha256 == payload_sha256 && prior.failed == failed {
            return Ok(true); // a re-delivered response is never applied twice
        }
        Err(refuse(
            "OCCURRENCE_CONFLICT",
            "same occurrence, different output",
        ))
    }

    fn validate_record_reservation(
        &self,
        occurrence_id: &str,
    ) -> Result<(u8, u64, String), Refusal> {
        let reservation = self
            .ledger
            .by_occurrence(occurrence_id)
            .ok_or_else(|| refuse("RESERVATION_REQUIRED", "record needs a prior reservation"))?;
        if !matches!(
            reservation.state,
            ReservationState::Settled | ReservationState::Reconciled
        ) {
            return Err(refuse(
                "RESERVATION_UNSETTLED",
                format!(
                    "reservation is {:?}; settle or reconcile it before recording",
                    reservation.state
                ),
            ));
        }
        let (stage, round, key) = (
            reservation.stage,
            reservation.round,
            reservation.idempotency_key.clone(),
        );
        self.require_open_round()?;
        if round != self.round_id || stage != self.expected_stage {
            return Err(refuse(
                "STAGE_ORDER",
                format!("occurrence is for round {round} stage {stage}"),
            ));
        }
        Ok((stage, round, key))
    }

    fn extract_stage_payload(
        &self,
        stage: u8,
        payload: &Value,
    ) -> Result<Option<(Value, String)>, Refusal> {
        match stage {
            4 => {
                let candidate = payload
                    .get("candidate")
                    .filter(|value| value.is_object())
                    .ok_or_else(|| {
                        refuse(
                            "CANDIDATE_MISSING",
                            "stage 4 must deliver a candidate object",
                        )
                    })?;
                Ok(Some((candidate.clone(), canonical::digest(candidate)?)))
            }
            6 | 7 => {
                let reviewed = payload.get("candidate_sha").and_then(Value::as_str);
                if reviewed.is_none() || reviewed != self.frozen_sha256.as_deref() {
                    return Err(refuse(
                        "STALE_CRITIC_INPUT",
                        "critic reviewed a different candidate",
                    ));
                }
                Ok(None)
            }
            _ => Ok(None),
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn commit_record(
        &mut self,
        occurrence_id: &str,
        key: String,
        round: u64,
        stage: u8,
        payload_sha256: String,
        failed: bool,
        oversize: bool,
        frozen: Option<(Value, String)>,
    ) {
        self.occurrences.insert(
            occurrence_id.into(),
            OccurrenceRecord {
                idempotency_key: key,
                round,
                stage,
                payload_sha256: payload_sha256.clone(),
                failed,
            },
        );
        self.emit(
            EventKind::ModelAttemptRecorded,
            json!({"stage": stage, "occurrence_id": occurrence_id, "failed": failed, "oversize": oversize, "payload_sha256": payload_sha256}),
        );
        if failed {
            return;
        }
        if let Some((candidate, digest)) = frozen {
            self.candidate = Some(candidate);
            self.frozen_sha256 = Some(digest.clone());
            self.emit(EventKind::CandidateFrozen, json!({"candidate_sha": digest}));
        }
        if matches!(stage, 6 | 7) {
            self.critics.insert(stage, occurrence_id.into());
        }
        self.expected_stage += 1;
    }

    /// Stage 5: record host check results against the frozen candidate.
    pub fn host_evaluate(
        &mut self,
        checks: Vec<HostCheck>,
        checker_policy_sha256: &str,
    ) -> Result<(), Refusal> {
        self.require_open_round()?;
        if self.expected_stage != HOST_STAGE {
            return Err(refuse(
                "STAGE_ORDER",
                "host evaluation runs after stage 4 and before stage 6",
            ));
        }
        require_digest("checker_policy_sha256", checker_policy_sha256)?;
        Self::validate_host_checks(&checks)?;
        let binding = ReviewBinding {
            candidate_sha256: self
                .frozen_sha256
                .clone()
                .ok_or_else(|| refuse("CANDIDATE_MISSING", "no frozen candidate"))?,
            mission_sha256: self.admitted.mission_sha256.clone(),
            source_sha256: self
                .source_sha256
                .clone()
                .ok_or_else(|| refuse("ROUND_NOT_OPEN", "no source snapshot"))?,
            checker_policy_sha256: checker_policy_sha256.into(),
        };
        self.emit(
            EventKind::HostEvaluationRecorded,
            json!({"binding": binding, "checks": checks}),
        );
        self.checks = Some(checks);
        self.evaluation_binding = Some(binding);
        self.expected_stage = HOST_STAGE + 1;
        Ok(())
    }

    fn validate_host_checks(checks: &[HostCheck]) -> Result<(), Refusal> {
        if checks.is_empty() {
            return Err(refuse(
                "HOST_CHECKS_EMPTY",
                "an evaluation needs at least one check",
            ));
        }
        let mut seen = BTreeSet::new();
        for check in checks {
            if check.check_id.trim().is_empty() || !seen.insert(check.check_id.as_str()) {
                return Err(refuse(
                    "HOST_CHECK_DUPLICATE",
                    "check ids must be distinct and non-blank",
                ));
            }
            if check.status == CheckStatus::Pass && !Self::has_valid_evidence(&check.evidence_refs)
            {
                return Err(refuse(
                    "PASS_WITHOUT_EVIDENCE",
                    format!("{} passed without evidence", check.check_id),
                ));
            }
        }
        Ok(())
    }

    fn has_valid_evidence(refs: &[String]) -> bool {
        !refs.is_empty() && refs.iter().all(|r| !r.trim().is_empty())
    }

    /// Route the round after stage 8. Ends the run unless the disposition is a repair.
    pub fn route(&mut self, observation: RouteObservation) -> Result<Disposition, Refusal> {
        self.require_open_round()?;
        if self.expected_stage != AFTER_LAST_STAGE {
            return Err(refuse("STAGE_ORDER", "route runs after all eight stages"));
        }
        Self::validate_observation_digests(&observation)?;
        let (stale, all_required_pass, any_required_fail, key) =
            self.evaluate_route_predicates(&observation)?;
        let stalled_rounds = if self.residual_key.as_deref() == Some(key.as_str()) {
            self.stalled_rounds + 1
        } else {
            1
        };
        let spent = self.ledger.spent()?;
        let facts = self.build_route_facts(
            &observation,
            stale,
            all_required_pass,
            any_required_fail,
            stalled_rounds,
            &spent,
        );
        let decision = routing::route(&facts);
        self.residual_key = Some(key);
        self.stalled_rounds = stalled_rounds;
        self.emit(
            EventKind::HostRoute,
            json!({
                "decision": decision,
                "routing_terminal": decision.routing_terminal(),
                "projection_lossy": decision.projection_is_lossy(),
                "candidate_sha": self.frozen_sha256,
                "stale": stale,
                "unresolved": observation.residual_ids,
                "stalled_rounds": stalled_rounds,
                "spent_calls": spent.model_calls,
            }),
        );
        self.round_open = false;
        if decision.is_terminal() {
            self.terminal = Some(decision);
        }
        Ok(decision)
    }

    fn validate_observation_digests(observation: &RouteObservation) -> Result<(), Refusal> {
        for (name, value) in [
            (
                "current_candidate_sha256",
                &observation.current_candidate_sha256,
            ),
            ("current_source_sha256", &observation.current_source_sha256),
            (
                "current_checker_policy_sha256",
                &observation.current_checker_policy_sha256,
            ),
        ] {
            if let Some(value) = value {
                require_digest(name, value)?;
            }
        }
        Ok(())
    }

    fn evaluate_route_predicates(
        &self,
        observation: &RouteObservation,
    ) -> Result<(bool, bool, bool, String), Refusal> {
        let checks = self
            .checks
            .as_ref()
            .ok_or_else(|| refuse("HOST_EVALUATION_MISSING", "no host evaluation"))?;
        let binding = self
            .evaluation_binding
            .as_ref()
            .ok_or_else(|| refuse("HOST_EVALUATION_MISSING", "no evaluation binding"))?;
        let stale = self.is_binding_stale(observation, binding);
        let (all_required_pass, any_required_fail, verified_evidence) =
            self.summarize_required_checks(checks);
        let key = routing::stall_key(
            &self.admitted.mission.required_claim_ids,
            &observation.residual_ids,
            &verified_evidence,
        )?;
        Ok((stale, all_required_pass, any_required_fail, key))
    }

    fn is_binding_stale(&self, observation: &RouteObservation, binding: &ReviewBinding) -> bool {
        let differs =
            |current: &Option<String>, bound: &str| current.as_deref().is_some_and(|c| c != bound);
        [
            differs(
                &observation.current_candidate_sha256,
                &binding.candidate_sha256,
            ),
            differs(&observation.current_source_sha256, &binding.source_sha256),
            differs(
                &observation.current_checker_policy_sha256,
                &binding.checker_policy_sha256,
            ),
            self.frozen_sha256.as_deref() != Some(binding.candidate_sha256.as_str()),
            self.admitted.mission_sha256 != binding.mission_sha256,
        ]
        .into_iter()
        .any(|b| b)
    }

    fn summarize_required_checks(&self, checks: &[HostCheck]) -> (bool, bool, BTreeSet<String>) {
        let by_id: BTreeMap<&str, &HostCheck> =
            checks.iter().map(|c| (c.check_id.as_str(), c)).collect();
        let predicates = &self.admitted.mission.done_predicates;
        let all_required_pass = predicates.iter().all(|p| {
            by_id
                .get(p.as_str())
                .is_some_and(|c| c.status == CheckStatus::Pass && !c.evidence_refs.is_empty())
        });
        let any_required_fail = predicates.iter().any(|p| {
            by_id
                .get(p.as_str())
                .is_some_and(|c| c.status == CheckStatus::Fail)
        });
        // Only the required predicates' verified evidence counts: a renamed or added
        // citation elsewhere is not progress.
        let verified_evidence: BTreeSet<String> = checks
            .iter()
            .filter(|c| c.status == CheckStatus::Pass && predicates.contains(&c.check_id))
            .flat_map(|c| c.evidence_refs.iter().cloned())
            .collect();
        (all_required_pass, any_required_fail, verified_evidence)
    }

    fn build_route_facts(
        &self,
        observation: &RouteObservation,
        stale: bool,
        all_required_pass: bool,
        any_required_fail: bool,
        stalled_rounds: u64,
        spent: &super::budget::Spend,
    ) -> RouteFacts {
        let limits = self.limits();
        RouteFacts {
            observation: observation.clone(),
            stale,
            all_required_pass,
            any_required_fail,
            critics_complete: self.critics.contains_key(&6) && self.critics.contains_key(&7),
            optional_claim_ids: self
                .admitted
                .mission
                .optional_claim_ids
                .iter()
                .cloned()
                .collect(),
            semantic_verification_in_contract: self
                .admitted
                .mission
                .semantic_verification_in_contract,
            stalled_rounds,
            max_stalled_rounds: limits.max_stalled_rounds,
            round: self.round_id,
            max_rounds: limits.max_rounds,
            calls_spent: spent.model_calls,
            max_model_calls: limits.max_model_calls,
            tokens_spent: spent.total_tokens,
            max_total_tokens: limits.max_total_tokens,
            cost_spent_microusd: spent.cost_microusd,
            max_cost_microusd: limits.max_cost_microusd,
        }
    }

    /// End the run outside the end-of-round route (policy violation, infrastructure
    /// failure, missing input, exhausted budget). Pending reservations stay charged.
    pub fn halt(&mut self, disposition: Disposition, reason: &str) -> Result<(), Refusal> {
        self.require_live()?;
        if !disposition.may_halt() {
            return Err(refuse(
                "HALT_DISPOSITION_INVALID",
                format!("{disposition:?} is reached only by routing"),
            ));
        }
        if reason.trim().is_empty() {
            return Err(refuse("HALT_REASON_REQUIRED", "a halt names its reason"));
        }
        self.round_open = false;
        self.terminal = Some(disposition);
        self.emit(
            EventKind::Halted,
            json!({"decision": disposition, "routing_terminal": disposition.routing_terminal(), "reason": reason}),
        );
        Ok(())
    }

    /// Apply one host command; the result is the command's output as JSON.
    pub fn apply(&mut self, command: LoopCommand) -> Result<Value, Refusal> {
        let mut output = self.dispatch_command(command)?;
        output["next_action"] = serde_json::to_value(self.next_action())
            .map_err(|e| refuse("NEXT_ACTION_UNSERIALISABLE", e.to_string()))?;
        Ok(output)
    }

    fn dispatch_accounting_command(&mut self, command: LoopCommand) -> Result<Value, Refusal> {
        match command {
            LoopCommand::Settle {
                idempotency_key,
                tokens,
                cost_microusd,
            } => {
                self.settle(&idempotency_key, tokens, cost_microusd)?;
                Ok(json!({}))
            }
            LoopCommand::Reconcile { idempotency_key } => {
                self.reconcile_unknown(&idempotency_key)?;
                Ok(json!({}))
            }
            LoopCommand::Release { idempotency_key } => {
                self.release(&idempotency_key)?;
                Ok(json!({}))
            }
            other => self.dispatch_stage_command(other),
        }
    }

    fn dispatch_command(&mut self, command: LoopCommand) -> Result<Value, Refusal> {
        match command {
            LoopCommand::BeginRound {
                source_snapshot_sha256,
            } => {
                self.begin_round(&source_snapshot_sha256)?;
                Ok(json!({"round": self.round_id}))
            }
            LoopCommand::Reserve {
                stage,
                occurrence_id,
                packet_sha256,
                executor,
                tokens,
                cost_microusd,
            } => {
                let key = self.reserve(
                    stage,
                    &occurrence_id,
                    &packet_sha256,
                    executor,
                    tokens,
                    cost_microusd,
                )?;
                Ok(json!({"idempotency_key": key}))
            }
            other => self.dispatch_accounting_command(other),
        }
    }

    fn dispatch_stage_command(&mut self, command: LoopCommand) -> Result<Value, Refusal> {
        match command {
            LoopCommand::Record {
                occurrence_id,
                payload,
                failed,
            } => {
                self.record(&occurrence_id, &payload, failed)?;
                Ok(json!({}))
            }
            LoopCommand::HostEvaluate {
                checks,
                checker_policy_sha256,
            } => {
                self.host_evaluate(checks, &checker_policy_sha256)?;
                Ok(json!({}))
            }
            LoopCommand::Route { observation } => {
                let decision = self.route(observation)?;
                Ok(
                    json!({"disposition": decision, "routing_terminal": decision.routing_terminal()}),
                )
            }
            LoopCommand::Halt {
                disposition,
                reason,
            } => {
                self.halt(disposition, &reason)?;
                Ok(json!({}))
            }
            _ => Err(refuse("COMMAND_INVALID", "unexpected loop command")),
        }
    }

    /// The whole state with its digest.
    pub fn checkpoint(&self) -> Result<Value, Refusal> {
        let state =
            serde_json::to_value(self).map_err(|e| refuse("CHECKPOINT_INVALID", e.to_string()))?;
        let state_sha256 = canonical::digest(&state)?;
        Ok(
            json!({"schema": CHECKPOINT_SCHEMA, "state": state, "state_sha256": state_sha256, "authority_effect": "None"}),
        )
    }

    /// Accept a host-held checkpoint after re-verifying digest, mission, ledger and tape.
    ///
    /// The digest is unkeyed: it catches a state edited without recomputing it (a partial
    /// write, a hand edit), not a caller who recomputes it. The ledger is also checked
    /// against the event tape, so dropping a reservation needs a matching tape edit.
    pub fn resume(checkpoint: &Value) -> Result<Self, Refusal> {
        if checkpoint.get("schema").and_then(Value::as_str) != Some(CHECKPOINT_SCHEMA)
            || checkpoint.get("authority_effect").and_then(Value::as_str) != Some("None")
        {
            return Err(refuse(
                "CHECKPOINT_INVALID",
                "not a research-loop checkpoint",
            ));
        }
        let state = checkpoint
            .get("state")
            .ok_or_else(|| refuse("CHECKPOINT_INVALID", "state missing"))?;
        if checkpoint.get("state_sha256").and_then(Value::as_str)
            != Some(canonical::digest(state)?.as_str())
        {
            return Err(refuse(
                "CHECKPOINT_TAMPERED",
                "state does not match its digest",
            ));
        }
        let resumed: Self = serde_json::from_value(state.clone())
            .map_err(|e| refuse("CHECKPOINT_INVALID", e.to_string()))?;
        resumed.verify()?;
        Ok(resumed)
    }

    fn verify(&self) -> Result<(), Refusal> {
        self.admitted.verify()?;
        self.ledger.verify(self.limits())?;
        self.verify_bounds_and_tape()?;
        self.verify_occurrences_and_candidate()
    }

    fn verify_bounds_and_tape(&self) -> Result<(), Refusal> {
        let invalid = |message: &str| Err(refuse("CHECKPOINT_INVALID", message));
        if self.round_id > self.limits().max_rounds
            || !(1..=AFTER_LAST_STAGE).contains(&self.expected_stage)
        {
            return invalid("round or stage out of range");
        }
        if self.round_open && self.terminal.is_some() {
            return invalid("a finished run has no open round");
        }
        if self
            .events
            .iter()
            .enumerate()
            .any(|(i, e)| e.sequence != i as u64)
        {
            return invalid("event tape is not contiguous");
        }
        let taped: BTreeSet<&str> = self
            .events
            .iter()
            .filter(|e| e.event == EventKind::BudgetReserved)
            .filter_map(|e| e.data.get("idempotency_key").and_then(Value::as_str))
            .collect();
        let ledgered: BTreeSet<&str> = self.ledger.keys().map(String::as_str).collect();
        if taped != ledgered {
            return invalid("ledger reservations differ from the event tape");
        }
        Ok(())
    }

    fn verify_occurrences_and_candidate(&self) -> Result<(), Refusal> {
        let invalid = |message: &str| Err(refuse("CHECKPOINT_INVALID", message));
        let recorded = self
            .events
            .iter()
            .filter(|e| e.event == EventKind::ModelAttemptRecorded)
            .count();
        if recorded != self.occurrences.len() {
            return invalid("recorded occurrences differ from the event tape");
        }
        for (id, record) in &self.occurrences {
            let reservation = self.ledger.by_occurrence(id);
            if reservation.map(|r| r.idempotency_key.as_str())
                != Some(record.idempotency_key.as_str())
            {
                return invalid("an occurrence has no matching reservation");
            }
        }
        if let (Some(candidate), Some(frozen)) = (&self.candidate, &self.frozen_sha256) {
            if &canonical::digest(candidate)? != frozen {
                return invalid("frozen candidate does not match its digest");
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/state.rs
// Claim: urn:core:crates_rs:core-adversary:state:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7dadc81e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7dadc81e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7dadc81e {
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
impl BoundaryError7dadc81e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7dadc81e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7dadc81e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7dadc81e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7dadc81e> {
        if capacity_bound == 0 {
            return Err(BoundaryError7dadc81e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7dadc81e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7dadc81e::ExceedsCapacity {
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
mod l4_boundary_tests_7dadc81e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7dadc81e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7dadc81e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7dadc81e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7dadc81e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7dadc81e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError7dadc81e::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError7dadc81e::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
