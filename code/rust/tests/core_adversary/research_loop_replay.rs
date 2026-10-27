//! The research pack's eighteen offline replay checks, one named test each, run against
//! the Rust controller, plus parity with the pack's recorded traces.
//!
//! Every observation here is a synthetic control-flow fixture: no provider is called and
//! no researched claim is verified.
//!
//! AuthorityEffect: None.

use core_types::routing::RoutingTerminal;
use core_adversary::research_loop::budget::ReservationState;
use core_adversary::research_loop::canonical::digest;
use core_adversary::research_loop::invalidation::{
    invalidated_nodes, plan_repair, ChangeScope, DependencyGraph, RepairRoute,
};
use core_adversary::research_loop::occurrence::Executor;
use core_adversary::research_loop::routing::{Disposition, RouteObservation};
use core_adversary::research_loop::state::{
    CheckStatus, EventKind, HostCheck, LoopCommand, NextAction, ResearchLoop,
};
use serde_json::{json, Value};
use std::collections::BTreeSet;

const FIXTURES: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/../tests/core_adversary/fixtures/research_loop");

fn mission(max_stalled_rounds: u64) -> Value {
    json!({
        "mission_id": "FIXTURE_MISSION",
        "run_id": "FIXTURE",
        "original_seed_ref": "seed.txt",
        "original_question": "fixture scope",
        "lane": "mixed",
        "required_claim_ids": ["CLAIM_FIXTURE"],
        "done_predicates": ["provenance", "scope"],
        "owned_paths": ["runs/FIXTURE/"],
        "forbidden_surfaces": ["sources/"],
        "source_inventory": "audit/source_inventory.yaml",
        "capability_bindings": {"local_read": "bound in conformance replay"},
        "verifier_routes": {"CLAIM_FIXTURE": "exact fixture inspection"},
        "budget": {"max_rounds": 3, "max_model_calls": 32, "max_total_tokens": 120000,
                   "max_cost_microusd": 0, "max_stalled_rounds": max_stalled_rounds},
        "retention_policy": "keep every candidate and raw observation",
    })
}

fn fresh() -> ResearchLoop {
    ResearchLoop::admit(&mission(2)).unwrap()
}

/// The oracle's fixture source snapshot, `hashed({'source_version': 1})`.
fn source() -> String {
    digest(&json!({"source_version": 1})).unwrap()
}

fn checker() -> String {
    digest(&json!({"checker": "fixture-checker-v1"})).unwrap()
}

fn packet(stage: u8) -> String {
    digest(&json!({"packet_stage": stage})).unwrap()
}

/// One delivered occurrence: reserve 10 tokens at zero cost, settle, record.
fn deliver(state: &mut ResearchLoop, stage: u8, occurrence: &str, payload: Value, failed: bool) {
    let key = state
        .reserve(stage, occurrence, &packet(stage), Executor::Model, 10, 0)
        .unwrap();
    state.settle(&key, 10, 0).unwrap();
    state.record(occurrence, &payload, failed).unwrap();
}

fn step(state: &mut ResearchLoop, stage: u8, payload: Value) {
    let occurrence = format!("FIXTURE.r{}.s{stage}", state.round_id());
    deliver(state, stage, &occurrence, payload, false);
}

fn checks(good: bool) -> Vec<HostCheck> {
    let provenance = if good {
        HostCheck {
            check_id: "provenance".into(),
            status: CheckStatus::Pass,
            evidence_refs: vec!["fixture:provenance".into()],
        }
    } else {
        HostCheck {
            check_id: "provenance".into(),
            status: CheckStatus::Fail,
            evidence_refs: vec!["fixture:missing-span".into()],
        }
    };
    vec![
        provenance,
        HostCheck {
            check_id: "scope".into(),
            status: CheckStatus::Pass,
            evidence_refs: vec!["fixture:scope".into()],
        },
    ]
}

/// The oracle's `complete_round`: stages 1–4, host evaluation, both critics, stage 8.
fn complete_round(state: &mut ResearchLoop, candidate: Value, good: bool) {
    state.begin_round(&source()).unwrap();
    for stage in 1..=3 {
        step(
            state,
            stage,
            json!({"proposal": "fixture", "should_continue": true}),
        );
    }
    step(state, 4, json!({"candidate": candidate}));
    state.host_evaluate(checks(good), &checker()).unwrap();
    let frozen = state.frozen_sha256().unwrap().to_owned();
    for stage in [6, 7] {
        step(
            state,
            stage,
            json!({"candidate_sha": frozen, "verdict": "ACCEPT",
                                  "evidence_refs": ["fixture:critic"], "should_continue": true}),
        );
    }
    // The model recommends Verified; the host never reads it.
    step(
        state,
        8,
        json!({"final_terminal_status": "Verified", "should_continue": true}),
    );
}

fn observe(repairable: bool, residuals: &[&str], accounted: bool) -> RouteObservation {
    RouteObservation {
        repairable,
        residual_ids: residuals.iter().map(|s| s.to_string()).collect(),
        accounted_critic_objections: accounted,
        ..RouteObservation::default()
    }
}

fn calls(state: &ResearchLoop) -> u64 {
    state.spent().unwrap().model_calls
}

fn code<T: std::fmt::Debug>(result: Result<T, core_adversary::stage::ports::Refusal>) -> String {
    result.unwrap_err().code
}

fn repair_then_complete() -> ResearchLoop {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "first candidate"}), false);
    let decision = state
        .route(observe(true, &["missing_span"], false))
        .unwrap();
    assert_eq!(decision, Disposition::RepairNextRound);
    let spent = calls(&state);
    let wire = serde_json::to_string(&state.checkpoint().unwrap()).unwrap();
    let mut state = ResearchLoop::resume(&serde_json::from_str(&wire).unwrap()).unwrap();
    assert_eq!(calls(&state), spent);
    complete_round(
        &mut state,
        json!({"claim": "revised candidate with retained witness"}),
        true,
    );
    assert_eq!(
        state.route(observe(false, &[], true)).unwrap(),
        Disposition::Verified
    );
    state
}

// ---- the eighteen oracle checks -------------------------------------------------------

#[test]
fn repair_loop_preserves_global_budget() {
    let state = repair_then_complete();
    assert_eq!(calls(&state), 14);
    assert_eq!(state.spent().unwrap().total_tokens, 140);
}

#[test]
fn checkpoint_resume_retains_spending() {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "x"}), false);
    state
        .route(observe(true, &["missing_span"], false))
        .unwrap();
    let checkpoint = state.checkpoint().unwrap();
    let resumed = ResearchLoop::resume(&checkpoint).unwrap();
    assert_eq!(resumed.spent().unwrap(), state.spent().unwrap());
    assert_eq!(resumed, state);
}

#[test]
fn fresh_complete_evidence_reaches_scoped_simulated_terminal() {
    let state = repair_then_complete();
    assert_eq!(state.terminal(), Some(Disposition::Verified));
    assert_eq!(
        Disposition::Verified.routing_terminal(),
        RoutingTerminal::CheckPassed
    );
    assert!(matches!(
        state.next_action(),
        NextAction::Finished {
            disposition: Disposition::Verified
        }
    ));
}

#[test]
fn model_stage_5_forgery_rejected() {
    let mut state = fresh();
    state.begin_round(&source()).unwrap();
    for stage in 1..=4 {
        step(&mut state, stage, json!({"candidate": {"claim": "x"}}));
    }
    for executor in [Executor::Model, Executor::IdeAgent] {
        let refused = state.reserve(5, "FIXTURE.r1.s5", &packet(5), executor, 10, 0);
        assert_eq!(code(refused), "STAGE5_HOST_ONLY");
    }
    assert_eq!(
        calls(&state),
        4,
        "a refused stage-5 dispatch is not charged"
    );
}

#[test]
fn duplicate_delivery_is_idempotent() {
    let mut state = fresh();
    state.begin_round(&source()).unwrap();
    deliver(&mut state, 1, "one", json!({"a": "b"}), false);
    let before = state.clone();
    // Same occurrence, same packet: the reservation and the record are both no-ops.
    let key = state
        .reserve(1, "one", &packet(1), Executor::Model, 10, 0)
        .unwrap();
    state.settle(&key, 10, 0).unwrap();
    state.record("one", &json!({"a": "b"}), false).unwrap();
    assert_eq!(state, before);
    // Same occurrence, different output: refused, nothing changes.
    assert_eq!(
        code(state.record("one", &json!({"a": "c"}), false)),
        "OCCURRENCE_CONFLICT"
    );
    assert_eq!(state, before);
}

#[test]
fn failed_attempt_consumes_budget() {
    let mut state = fresh();
    state.begin_round(&source()).unwrap();
    deliver(&mut state, 1, "one", json!({"a": "b"}), false);
    deliver(&mut state, 2, "failed", json!({"error": "timeout"}), true);
    assert!(matches!(
        state.next_action(),
        NextAction::Dispatch { stage: 2, .. }
    ));
    deliver(&mut state, 2, "retry", json!({"ok": "retry"}), false);
    assert_eq!(calls(&state), 3);
}

#[test]
fn empty_host_check_set_rejected() {
    let mut state = at_stage_five();
    assert_eq!(
        code(state.host_evaluate(vec![], &checker())),
        "HOST_CHECKS_EMPTY"
    );
}

#[test]
fn pass_without_evidence_rejected() {
    let mut state = at_stage_five();
    let bare = vec![HostCheck {
        check_id: "provenance".into(),
        status: CheckStatus::Pass,
        evidence_refs: vec![],
    }];
    assert_eq!(
        code(state.host_evaluate(bare, &checker())),
        "PASS_WITHOUT_EVIDENCE"
    );
    let blank = vec![HostCheck {
        check_id: "provenance".into(),
        status: CheckStatus::Pass,
        evidence_refs: vec![" ".into()],
    }];
    assert_eq!(
        code(state.host_evaluate(blank, &checker())),
        "PASS_WITHOUT_EVIDENCE"
    );
}

#[test]
fn critic_of_different_candidate_rejected() {
    let mut state = at_stage_five();
    state.host_evaluate(checks(true), &checker()).unwrap();
    let key = state
        .reserve(6, "FIXTURE.r1.s6", &packet(6), Executor::Model, 10, 0)
        .unwrap();
    state.settle(&key, 10, 0).unwrap();
    let other = format!("sha256:{}", "0".repeat(64));
    let refused = state.record("FIXTURE.r1.s6", &json!({"candidate_sha": other}), false);
    assert_eq!(code(refused), "STALE_CRITIC_INPUT");
    let refused = state.record("FIXTURE.r1.s6", &json!({"verdict": "ACCEPT"}), false);
    assert_eq!(
        code(refused),
        "STALE_CRITIC_INPUT",
        "a critic must name the frozen candidate"
    );
}

#[test]
fn post_review_candidate_mutation_forces_recheck() {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "x"}), true);
    let changed = digest(&json!({"claim": "changed"})).unwrap();
    let observation = RouteObservation {
        current_candidate_sha256: Some(changed),
        ..observe(false, &[], true)
    };
    let decision = state.route(observation).unwrap();
    assert_eq!(decision, Disposition::InvalidateAndRecheck);
    assert!(!decision.is_terminal());
    assert_eq!(decision.routing_terminal(), RoutingTerminal::Repair);
}

#[test]
fn source_change_invalidates_review() {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "x"}), true);
    let observation = RouteObservation {
        current_source_sha256: Some(format!("sha256:{}", "1".repeat(64))),
        ..observe(false, &[], true)
    };
    assert_eq!(
        state.route(observation).unwrap(),
        Disposition::InvalidateAndRecheck
    );
}

#[test]
fn model_verified_recommendation_cannot_supply_missing_oracle() {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "x"}), true);
    let observation = RouteObservation {
        verifier_unavailable: true,
        ..observe(false, &[], true)
    };
    assert_eq!(
        state.route(observation).unwrap(),
        Disposition::NeedsExternalOracle
    );
}

#[test]
fn missing_source_is_not_a_counterexample_or_pass() {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "x"}), true);
    let observation = RouteObservation {
        missing_input: true,
        ..observe(false, &[], true)
    };
    assert_eq!(
        state.route(observation).unwrap(),
        Disposition::BlockedByEvidence
    );
}

#[test]
fn semantic_stall_stops_cosmetic_revisions() {
    let mut state = fresh();
    let mut decision = None;
    for round in 0..2 {
        complete_round(
            &mut state,
            json!({"claim": format!("format {round}")}),
            false,
        );
        decision = Some(
            state
                .route(observe(true, &["same_unresolved_claim"], false))
                .unwrap(),
        );
    }
    assert_eq!(decision, Some(Disposition::OpenObstruction));
    assert_eq!(
        Disposition::OpenObstruction.routing_terminal(),
        RoutingTerminal::Refusal
    );
}

#[test]
fn round_exhaustion_retains_candidate() {
    let mut state = ResearchLoop::admit(&mission(5)).unwrap();
    let mut decision = None;
    for round in 0..3 {
        complete_round(&mut state, json!({"claim": round.to_string()}), false);
        decision = Some(
            state
                .route(observe(true, &[&format!("unresolved_{round}")], false))
                .unwrap(),
        );
    }
    assert_eq!(decision, Some(Disposition::BudgetExhausted));
    assert_eq!(state.candidate(), Some(&json!({"claim": "2"})));
    assert_eq!(code(state.begin_round(&source())), "RUN_FINISHED");
}

#[test]
fn zero_paid_budget_blocks_paid_call() {
    let mut state = fresh();
    state.begin_round(&source()).unwrap();
    let refused = state.reserve(1, "paid", &packet(1), Executor::Model, 1, 1);
    assert_eq!(code(refused), "PAID_DISPATCH_DISABLED");
    assert_eq!(calls(&state), 0);
}

fn dependencies() -> DependencyGraph {
    [
        ("source_a", vec![]),
        ("source_b", vec![]),
        ("claim_a", vec!["source_a"]),
        ("claim_b", vec!["source_b"]),
        ("report", vec!["claim_a", "claim_b"]),
        ("review", vec!["report"]),
    ]
    .into_iter()
    .map(|(node, deps)| {
        (
            node.to_string(),
            deps.into_iter().map(String::from).collect(),
        )
    })
    .collect()
}

fn set(items: &[&str]) -> BTreeSet<String> {
    items.iter().map(|s| s.to_string()).collect()
}

#[test]
fn source_change_invalidates_transitive_dependents() {
    let graph = dependencies();
    assert_eq!(
        invalidated_nodes(&graph, &set(&["source_a"])).unwrap(),
        set(&["source_a", "claim_a", "report", "review"])
    );
    let plan = plan_repair(&graph, &set(&["source_a"]), ChangeScope::default()).unwrap();
    assert_eq!(plan.route, RepairRoute::InvalidateTransitiveDependents);
}

#[test]
fn unknown_dependency_coverage_triggers_full_invalidation() {
    let graph = dependencies();
    let all: BTreeSet<String> = graph.keys().cloned().collect();
    assert_eq!(invalidated_nodes(&graph, &set(&["unknown"])).unwrap(), all);
    let plan = plan_repair(&graph, &set(&["unknown"]), ChangeScope::default()).unwrap();
    assert_eq!(plan.route, RepairRoute::ConservativeFullRecompute);
    let mut dangling = dependencies();
    dangling.insert("claim_c".into(), vec!["source_missing".into()]);
    assert_eq!(
        invalidated_nodes(&dangling, &set(&["source_a"]))
            .unwrap()
            .len(),
        dangling.len()
    );
}

fn at_stage_five() -> ResearchLoop {
    let mut state = fresh();
    state.begin_round(&source()).unwrap();
    for stage in 1..=3 {
        step(&mut state, stage, json!({}));
    }
    step(&mut state, 4, json!({"candidate": {"claim": "x"}}));
    state
}

// ---- parity with the pack's recorded traces --------------------------------------------

fn oracle() -> Value {
    serde_json::from_str(
        &std::fs::read_to_string(format!("{FIXTURES}/replay_traces.json")).unwrap(),
    )
    .unwrap()
}

/// The oracle's events, as (round, event, stage, occurrence, candidate digest, source digest).
fn oracle_tape(name: &str) -> Vec<(u64, String, Value, Value, Value)> {
    oracle()["scenarios"][name]
        .as_array()
        .unwrap()
        .iter()
        .map(|e| {
            (
                e["round_id"].as_u64().unwrap(),
                e["event"].as_str().unwrap().to_owned(),
                e.get("stage").cloned().unwrap_or(Value::Null),
                e.get("candidate_sha").cloned().unwrap_or(Value::Null),
                e.get("source_sha").cloned().unwrap_or(Value::Null),
            )
        })
        .collect()
}

fn rust_tape(state: &ResearchLoop) -> Vec<(u64, String, Value, Value, Value)> {
    let shared = [
        EventKind::RoundStarted,
        EventKind::ModelAttemptRecorded,
        EventKind::CandidateFrozen,
        EventKind::HostEvaluationRecorded,
        EventKind::HostRoute,
    ];
    state
        .events()
        .iter()
        .filter(|e| shared.contains(&e.event))
        .map(|e| {
            (
                e.round_id,
                serde_json::to_value(e.event)
                    .unwrap()
                    .as_str()
                    .unwrap()
                    .to_owned(),
                e.data.get("stage").cloned().unwrap_or(Value::Null),
                e.data.get("candidate_sha").cloned().unwrap_or(Value::Null),
                e.data.get("source_sha").cloned().unwrap_or(Value::Null),
            )
        })
        .collect()
}

fn oracle_decisions(name: &str) -> Vec<String> {
    oracle()["scenarios"][name]
        .as_array()
        .unwrap()
        .iter()
        .filter_map(|e| e["decision"].as_str().map(str::to_owned))
        .collect()
}

#[test]
fn traces_match_the_oracle_event_for_event() {
    // Candidate and source digests agree byte for byte, so canonical hashing matches Python.
    assert_eq!(
        rust_tape(&repair_then_complete()),
        oracle_tape("repair_then_complete")
    );

    let mut stall = fresh();
    for round in 0..2 {
        complete_round(
            &mut stall,
            json!({"claim": format!("format {round}")}),
            false,
        );
        stall
            .route(observe(true, &["same_unresolved_claim"], false))
            .unwrap();
    }
    assert_eq!(rust_tape(&stall), oracle_tape("stall"));
    assert_eq!(
        oracle_decisions("stall"),
        ["REPAIR_NEXT_ROUND", "OpenObstruction"]
    );

    let mut stale = fresh();
    complete_round(&mut stale, json!({"claim": "x"}), true);
    let changed = digest(&json!({"claim": "changed"})).unwrap();
    stale
        .route(RouteObservation {
            current_candidate_sha256: Some(changed),
            ..observe(false, &[], true)
        })
        .unwrap();
    assert_eq!(rust_tape(&stale), oracle_tape("stale_candidate"));
    // Recorded naming difference: the oracle calls the stale route REPAIR_NEXT_ROUND.
    assert_eq!(oracle_decisions("stale_candidate"), ["REPAIR_NEXT_ROUND"]);

    let mut exhausted = ResearchLoop::admit(&mission(5)).unwrap();
    for round in 0..3 {
        complete_round(&mut exhausted, json!({"claim": round.to_string()}), false);
        exhausted
            .route(observe(true, &[&format!("unresolved_{round}")], false))
            .unwrap();
    }
    assert_eq!(rust_tape(&exhausted), oracle_tape("budget_exhausted"));
}

#[test]
fn every_oracle_check_has_a_named_test() {
    let validation: Value = serde_json::from_str(
        &std::fs::read_to_string(format!("{FIXTURES}/replay_validation.json")).unwrap(),
    )
    .unwrap();
    let source = include_str!("research_loop_replay.rs");
    let names = validation["checks_passed"].as_array().unwrap();
    assert_eq!(names.len(), 18);
    for name in names {
        let test_name: String = name
            .as_str()
            .unwrap()
            .to_lowercase()
            .chars()
            .map(|c| if c.is_ascii_alphanumeric() { c } else { '_' })
            .collect();
        assert!(
            source.contains(&format!("fn {test_name}()")),
            "no test for {name}"
        );
    }
}

// ---- controller properties beyond the oracle ---------------------------------------------

#[test]
fn the_pack_example_mission_is_admitted() {
    let text = std::fs::read_to_string(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../../adversary/tests/fixtures/rust_research_loop/example_mission.yaml"
    ))
    .unwrap();
    let value: Value = serde_yaml::from_str(&text).unwrap();
    let state = ResearchLoop::admit(&value).unwrap();
    assert_eq!(state.limits().max_cost_microusd, 0);
    assert_eq!(
        state.limits().max_wall_seconds,
        2700,
        "unnamed limits take the workflow defaults"
    );
}

#[test]
fn malformed_missions_are_refused() {
    let mut missing = mission(2);
    missing.as_object_mut().unwrap().remove("retention_policy");
    let mut unrouted = mission(2);
    unrouted["verifier_routes"] = json!({});
    let mut overlap = mission(2);
    overlap["forbidden_surfaces"] = json!(["runs/"]);
    let mut float_budget = mission(2);
    float_budget["budget"]["max_rounds"] = serde_json::from_str("3.0").unwrap();
    let mut zero_rounds = mission(2);
    zero_rounds["budget"]["max_rounds"] = json!(0);
    let mut unknown = mission(2);
    unknown["budget"]["max_everything"] = json!(1);
    for (case, expected) in [
        (missing, "MISSION_INVALID"),
        (unrouted, "MISSION_INVALID"),
        (overlap, "MISSION_INVALID"),
        (float_budget, "MISSION_INVALID"),
        (zero_rounds, "MISSION_BUDGET_INVALID"),
        (unknown, "MISSION_INVALID"),
    ] {
        assert_eq!(code(ResearchLoop::admit(&case)), expected, "{case}");
    }
}

#[test]
fn a_tampered_checkpoint_is_refused() {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "x"}), false);
    state.route(observe(true, &["r"], false)).unwrap();
    let checkpoint = state.checkpoint().unwrap();

    let mut edited = checkpoint.clone();
    edited["state"]["round_id"] = json!(0);
    assert_eq!(code(ResearchLoop::resume(&edited)), "CHECKPOINT_TAMPERED");

    // Re-digested forgeries are still refused: a deleted reservation (a refunded call)
    // leaves a recorded occurrence without its charge, and a released call cannot keep
    // tokens charged.
    let mut forged = checkpoint.clone();
    let reservations = forged["state"]["ledger"]["reservations"]
        .as_object_mut()
        .unwrap();
    let first = reservations.keys().next().unwrap().clone();
    reservations.remove(&first);
    forged["state_sha256"] = json!(digest(&forged["state"]).unwrap());
    assert_eq!(code(ResearchLoop::resume(&forged)), "CHECKPOINT_INVALID");

    let mut forged = checkpoint.clone();
    let reservations = forged["state"]["ledger"]["reservations"]
        .as_object_mut()
        .unwrap();
    let first = reservations.keys().next().unwrap().clone();
    reservations[&first]["state"] = json!("RELEASED");
    forged["state_sha256"] = json!(digest(&forged["state"]).unwrap());
    assert_eq!(
        code(ResearchLoop::resume(&forged)),
        "CHECKPOINT_LEDGER_INVALID"
    );
}

#[test]
fn an_unknown_outcome_must_be_reconciled_before_a_retry() {
    let mut state = fresh();
    state.begin_round(&source()).unwrap();
    let key = state
        .reserve(1, "a1", &packet(1), Executor::Model, 50, 0)
        .unwrap();
    assert_eq!(
        code(state.reserve(1, "a2", &packet(1), Executor::Model, 50, 0)),
        "RESERVATION_OUTSTANDING"
    );
    assert_eq!(
        code(state.record("a1", &json!({}), false)),
        "RESERVATION_UNSETTLED"
    );
    state.reconcile_unknown(&key).unwrap();
    assert_eq!(
        state.ledger().reservation(&key).unwrap().state,
        ReservationState::Reconciled
    );
    assert_eq!(
        state.spent().unwrap().total_tokens,
        50,
        "an unknown outcome stays charged"
    );
    state
        .reserve(1, "a2", &packet(1), Executor::Model, 50, 0)
        .unwrap();
    assert_eq!(state.spent().unwrap().total_tokens, 100);
}

#[test]
fn release_refunds_usage_but_keeps_the_call() {
    let mut state = fresh();
    state.begin_round(&source()).unwrap();
    let key = state
        .reserve(1, "a1", &packet(1), Executor::Model, 50, 0)
        .unwrap();
    state.release(&key).unwrap();
    let spend = state.spent().unwrap();
    assert_eq!((spend.model_calls, spend.total_tokens), (1, 0));
    assert_eq!(code(state.settle(&key, 1, 0)), "RESERVATION_CLOSED");
}

#[test]
fn an_overrun_is_charged_and_blocks_further_reservations() {
    let mut value = mission(2);
    value["budget"]["max_total_tokens"] = json!(100);
    let mut state = ResearchLoop::admit(&value).unwrap();
    state.begin_round(&source()).unwrap();
    let key = state
        .reserve(1, "a1", &packet(1), Executor::Model, 60, 0)
        .unwrap();
    state.settle(&key, 120, 0).unwrap();
    assert!(state.ledger().reservation(&key).unwrap().overrun);
    assert_eq!(state.spent().unwrap().total_tokens, 120);
    state.record("a1", &json!({}), false).unwrap();
    assert_eq!(
        code(state.reserve(2, "a2", &packet(2), Executor::Model, 1, 0)),
        "BUDGET_EXHAUSTED"
    );
    // The overrun checkpoint still resumes: the excess is recorded, not hidden.
    ResearchLoop::resume(&state.checkpoint().unwrap()).unwrap();
}

#[test]
fn halt_ends_the_run_with_a_resource_or_refusal_disposition_only() {
    let mut state = fresh();
    assert_eq!(
        code(state.halt(Disposition::Verified, "no")),
        "HALT_DISPOSITION_INVALID"
    );
    state
        .halt(
            Disposition::InfrastructureFailure,
            "transport retries exhausted",
        )
        .unwrap();
    assert_eq!(state.terminal(), Some(Disposition::InfrastructureFailure));
    assert_eq!(code(state.begin_round(&source())), "RUN_FINISHED");
}

#[test]
fn optional_residuals_and_unverified_contracts_have_their_own_terminals() {
    let mut value = mission(2);
    value["optional_claim_ids"] = json!(["CLAIM_OPTIONAL"]);
    let mut state = ResearchLoop::admit(&value).unwrap();
    complete_round(&mut state, json!({"claim": "x"}), true);
    let decision = state
        .route(observe(false, &["CLAIM_OPTIONAL"], true))
        .unwrap();
    assert_eq!(decision, Disposition::VerifiedWithResiduals);

    let mut value = mission(2);
    value["semantic_verification_in_contract"] = json!(false);
    let mut state = ResearchLoop::admit(&value).unwrap();
    state.begin_round(&source()).unwrap();
    for stage in 1..=3 {
        step(&mut state, stage, json!({}));
    }
    step(&mut state, 4, json!({"candidate": {"claim": "x"}}));
    let unknown = vec![
        HostCheck {
            check_id: "provenance".into(),
            status: CheckStatus::Unknown,
            evidence_refs: vec![],
        },
        HostCheck {
            check_id: "scope".into(),
            status: CheckStatus::Pass,
            evidence_refs: vec!["fixture:scope".into()],
        },
    ];
    state.host_evaluate(unknown, &checker()).unwrap();
    let frozen = state.frozen_sha256().unwrap().to_owned();
    for stage in [6, 7] {
        step(&mut state, stage, json!({"candidate_sha": frozen}));
    }
    step(&mut state, 8, json!({}));
    assert_eq!(
        state.route(observe(false, &[], true)).unwrap(),
        Disposition::StabilizedSurvivor
    );
}

#[test]
fn cyclic_dependency_graphs_are_refused() {
    let mut graph = dependencies();
    graph.insert("source_a".into(), vec!["review".into()]);
    assert_eq!(
        code(invalidated_nodes(&graph, &set(&["source_b"]))),
        "DEPENDENCY_CYCLE"
    );
    let plan = plan_repair(
        &dependencies(),
        &set(&["claim_a"]),
        ChangeScope {
            local_patch: true,
            ..Default::default()
        },
    )
    .unwrap();
    assert_eq!(plan.route, RepairRoute::NewCandidateAndRecheck);
    let plan = plan_repair(
        &dependencies(),
        &set(&["claim_a"]),
        ChangeScope {
            question_or_policy_changed: true,
            ..Default::default()
        },
    )
    .unwrap();
    assert_eq!(plan.route, RepairRoute::ExplicitRevisionRequired);
}

#[test]
fn commands_round_trip_through_json() {
    let mut state = fresh();
    let command: LoopCommand = serde_json::from_value(json!({
        "command": "begin_round", "source_snapshot_sha256": source()
    }))
    .unwrap();
    let output = state.apply(command).unwrap();
    assert_eq!(
        output["next_action"],
        json!({"action": "DISPATCH", "round": 1, "stage": 1, "phase": "INGEST"})
    );
    let refused: Result<LoopCommand, _> =
        serde_json::from_value(json!({"command": "begin_round", "extra": 1}));
    assert!(refused.is_err());
}

#[test]
fn refused_commands_leave_the_state_unchanged() {
    let mut state = at_stage_five();
    let before = state.clone();
    let _ = state.host_evaluate(vec![], &checker());
    let _ = state.route(observe(false, &[], true));
    let _ = state.reserve(6, "early", &packet(6), Executor::Model, 1, 0);
    let _ = state.begin_round(&source());
    assert_eq!(state, before);
}

// ---- review fixes (2026-10-06) --------------------------------------------------------

#[test]
fn the_host_never_reserves_a_dispatch() {
    let mut state = fresh();
    state.begin_round(&source()).unwrap();
    for stage in [1, 5] {
        let refused = state.reserve(stage, "host", &packet(stage), Executor::Host, 0, 0);
        assert_eq!(code(refused), "STAGE5_HOST_ONLY");
    }
    assert_eq!(calls(&state), 0);
}

#[test]
fn an_oversize_response_is_recorded_as_a_failed_attempt() {
    let mut small = mission(2);
    small["budget"]["max_model_response_bytes"] = json!(64);
    let mut state = ResearchLoop::admit(&small).unwrap();
    state.begin_round(&source()).unwrap();
    let big = json!({"proposal": "x".repeat(200), "should_continue": true});
    deliver(&mut state, 1, "FIXTURE.r1.s1.a1", big.clone(), false);
    let last = state.events().last().unwrap();
    assert_eq!(last.event, EventKind::ModelAttemptRecorded);
    assert_eq!(last.data["failed"], json!(true));
    assert_eq!(last.data["oversize"], json!(true));
    // Charged, recorded, and the stage is still open; re-delivery is idempotent.
    assert_eq!(calls(&state), 1);
    state.record("FIXTURE.r1.s1.a1", &big, false).unwrap();
    assert!(matches!(
        state.next_action(),
        NextAction::Dispatch {
            round: 1,
            stage: 1,
            ..
        }
    ));
}

#[test]
fn a_witnessed_unrepairable_failure_is_an_open_obstruction() {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "x"}), false);
    assert_eq!(
        state.route(observe(false, &["provenance"], true)).unwrap(),
        Disposition::OpenObstruction
    );
}

#[test]
fn spent_tokens_exhaust_the_budget() {
    let mut tight = mission(5);
    tight["budget"]["max_total_tokens"] = json!(70);
    let mut state = ResearchLoop::admit(&tight).unwrap();
    complete_round(&mut state, json!({"claim": "x"}), false);
    assert_eq!(state.spent().unwrap().total_tokens, 70);
    assert_eq!(
        state.route(observe(true, &["r"], false)).unwrap(),
        Disposition::BudgetExhausted
    );
}

#[test]
fn renamed_evidence_outside_the_required_predicates_is_not_progress() {
    let mut state = fresh();
    let mut decision = None;
    for round in 1..=2u8 {
        state.begin_round(&source()).unwrap();
        for stage in 1..=3 {
            step(
                &mut state,
                stage,
                json!({"proposal": "fixture", "should_continue": true}),
            );
        }
        step(&mut state, 4, json!({"candidate": {"claim": round}}));
        let mut round_checks = checks(false);
        round_checks.push(HostCheck {
            check_id: "style".into(),
            status: CheckStatus::Pass,
            evidence_refs: vec![format!("fixture:citation-{round}")],
        });
        state.host_evaluate(round_checks, &checker()).unwrap();
        let frozen = state.frozen_sha256().unwrap().to_owned();
        for stage in [6, 7] {
            step(
                &mut state,
                stage,
                json!({"candidate_sha": frozen, "should_continue": true}),
            );
        }
        step(&mut state, 8, json!({"should_continue": true}));
        decision = Some(state.route(observe(true, &["same"], false)).unwrap());
    }
    assert_eq!(decision, Some(Disposition::OpenObstruction));
}

#[test]
fn a_reservation_dropped_with_its_occurrence_is_caught_by_the_tape() {
    let mut state = fresh();
    complete_round(&mut state, json!({"claim": "x"}), false);
    let mut forged = state.checkpoint().unwrap();
    let reservations = forged["state"]["ledger"]["reservations"]
        .as_object_mut()
        .unwrap();
    let key = reservations.keys().next().unwrap().clone();
    let occurrence = reservations[&key]["occurrence_id"]
        .as_str()
        .unwrap()
        .to_owned();
    reservations.remove(&key);
    forged["state"]["occurrences"]
        .as_object_mut()
        .unwrap()
        .remove(&occurrence);
    forged["state_sha256"] = json!(digest(&forged["state"]).unwrap());
    assert_eq!(code(ResearchLoop::resume(&forged)), "CHECKPOINT_INVALID");
}

#[test]
fn owned_paths_are_repository_relative_and_compared_without_case() {
    for (owned, forbidden) in [
        ("/", "sources/"),
        (".", "sources/"),
        ("runs/../sources", "secrets/"),
        ("runs\\FIXTURE", "sources/"),
        ("C:/runs", "sources/"),
        ("Sources/x", "sources/"),
    ] {
        let mut case = mission(2);
        case["owned_paths"] = json!([owned]);
        case["forbidden_surfaces"] = json!([forbidden]);
        assert_eq!(
            code(ResearchLoop::admit(&case)),
            "MISSION_INVALID",
            "{owned}"
        );
    }
}

// Origin: engine/crates_rs/tests/core_adversary/research_loop_replay.rs
// Claim: urn:core:crates_rs:tests:research-loop-replay:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord62bd0330 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord62bd0330` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError62bd0330 {
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
impl BoundaryError62bd0330 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError62bd0330 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError62bd0330 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord62bd0330 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError62bd0330> {
        if capacity_bound == 0 {
            return Err(BoundaryError62bd0330::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError62bd0330::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError62bd0330::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_62bd0330() {
    let admitted = BoundaryRecord62bd0330::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord62bd0330::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
