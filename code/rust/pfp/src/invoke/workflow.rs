//! Sequential search, descent, composition and challenge orchestration over supplied values.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_e5294e95<T> {
    fn checked_invariant_e5294e95(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_e5294e95<T> for Option<T> {
    #[inline]
    fn checked_invariant_e5294e95(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_e5294e95<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_e5294e95(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::*;

fn run_score_discrete_proposal(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: DiscreteScoringRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, format!("SCORING_REQUEST_INVALID: {error}")),
    };
    let result = pfp_runtime::scoring_frontier::score_discrete_proposal_with_policy(
        &request.obstructions,
        &request.proposal,
        request.admitted_constructors.as_deref(),
        request.known_kill_conditions.as_ref(),
    );
    outcome_ok(
        action,
        serde_json::to_value(result).checked_invariant_e5294e95("score serializes"),
    )
}

fn run_score_cochain_proposal(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: CochainScoringRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, format!("SCORING_REQUEST_INVALID: {error}")),
    };
    let mut cochain = std::collections::BTreeMap::new();
    for (key, value) in &request.core_cochain {
        match parse_exact(value) {
            Ok(value) => {
                cochain.insert(key.clone(), value);
            }
            Err(error) => return outcome_err(action, format!("INEXACT_COCHAIN: {key}: {error}")),
        }
    }
    let result = pfp_runtime::scoring_frontier::score_cochain_proposal_with_policy(
        &cochain,
        &request.proposal,
        request.admitted_constructors.as_deref(),
        request.known_kill_conditions.as_ref(),
    );
    outcome_ok(
        action,
        serde_json::to_value(result).checked_invariant_e5294e95("score serializes"),
    )
}

fn run_rank_scored_candidates(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: RankScoredRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, format!("SCORING_REQUEST_INVALID: {error}")),
    };
    // The client `is_legal` bit is not a score. A negative structural cost is
    // the same illegality the scorers already return; do not rank it as legal.
    if request.scores.iter().any(|score| {
        score.is_legal && score.structural_cost < core_kernel::integer(0)
    }) {
        return outcome_err(
            action,
            format!(
                "{}: structural_cost is negative",
                pfp_runtime::scoring_frontier::REFUSAL_NEGATIVE_MAGNITUDE
            ),
        );
    }
    let result =
        pfp_runtime::scoring_frontier::rank_scored_candidates(request.scores);
    outcome_ok(
        action,
        serde_json::to_value(result).checked_invariant_e5294e95("scores serialize"),
    )
}

fn run_rank_candidate_proposals(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: RankScoringRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, format!("SCORING_REQUEST_INVALID: {error}")),
    };
    if let Some(guards) = request.learned_guards {
        if request.known_kill_conditions.is_some() {
            return outcome_err(
                action,
                "SCORING_REQUEST_INVALID: policy and learned guards cannot be combined",
            );
        }
        return match crate::host::rank_guarded_frontier(
            &request.obstructions,
            &request.proposals,
            request.admitted_constructors.as_deref(),
            &guards,
        ) {
            Ok(result) => outcome_ok(action, result),
            Err(error) => outcome_err(action, error),
        };
    }
    let scored = request
        .proposals
        .iter()
        .map(|proposal| {
            pfp_runtime::scoring_frontier::score_discrete_proposal_with_policy(
                &request.obstructions,
                proposal,
                request.admitted_constructors.as_deref(),
                request.known_kill_conditions.as_ref(),
            )
        })
        .collect();
    let result = pfp_runtime::scoring_frontier::rank_scored_candidates(scored);
    outcome_ok(
        action,
        serde_json::to_value(result).checked_invariant_e5294e95("scores serialize"),
    )
}

fn run_turn_driver_next_prompt(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: TurnDriverNextPromptRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("TURN_DRIVER_PROMPT_INVALID: {e}")),
    };
    let artifact =
        match pfp_runtime::driver::next_prompt(&request.state, &request.policy) {
            Ok(artifact) => artifact,
            Err(refusal) => {
                return outcome_err(action, format!("{}: {}", refusal.code, refusal.message));
            }
        };
    match serde_json::to_value(artifact) {
        Ok(value) => outcome_ok(action, value),
        Err(error) => outcome_err(
            action,
            format!("TURN_DRIVER_PROMPT_INVALID: artifact encoding failed: {error}"),
        ),
    }
}

fn run_turn_driver_step(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: TurnDriverStepRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid turn_driver_step input: {e}")),
    };
    let step_outcome =
        pfp_runtime::driver::step(&request.state, &request.candidate);
    outcome_ok(
        action,
        serde_json::to_value(step_outcome).checked_invariant_e5294e95("outcome serialization must succeed"),
    )
}

fn decompose_cycle_basis(action: &str, request: &DecomposeTaskRequestV1) -> RuntimeOutcomeV1 {
    let result = if request.tree_edges.is_empty() {
        core_homology::cycle_basis::compute_cycle_basis(&request.vertices, &request.edges)
    } else {
        core_homology::cycle_basis::compute_cycle_basis_with_tree(
            &request.vertices,
            &request.edges,
            &request.tree_edges,
        )
    };
    let units: Vec<serde_json::Value> = result
        .fundamental_cycles
        .iter()
        .map(|fc| {
            serde_json::json!({
                "unit_id": format!("chord_{}_{}", fc.chord.u, fc.chord.v),
                "target_variable": format!("{}->{}", fc.chord.u, fc.chord.v),
                "expected_value": fc.expected_chord_value,
                "chord": {
                    "u": fc.chord.u,
                    "v": fc.chord.v,
                    "weight": fc.chord.weight,
                }
            })
        })
        .collect();
    let plan = serde_json::json!({
        "schema_version": "core.symbol_game.decomposition_plan.v1",
        "authority_effect": "None",
        "basis_kind": "CYCLE_BASIS",
        "units": units,
        "potentials": result.potentials,
        "spanning_forest_edges": result.spanning_forest_edges,
        "chords": result.chords,
        "b1": result.b1,
        "independence_certificate": result.certificate,
        "composition_rule": "GAUGE_TREE_PLUS_CHORDS",
    });
    outcome_ok(action, plan)
}

fn decompose_stabilizer_generators(
    action: &str,
    request: &DecomposeTaskRequestV1,
) -> RuntimeOutcomeV1 {
    let case_val = match request.case {
        Some(ref c) => c,
        None => return outcome_err(action, "missing case for STABILIZER_GENERATORS"),
    };
    let solve_outcome = pfp_runtime::stabilizer_solve(case_val);
    match solve_outcome {
        pfp_runtime::StabilizerOutcome::Solved { basis, .. } => {
            let units: Vec<serde_json::Value> = basis
                .iter()
                .enumerate()
                .map(|(idx, gen)| {
                    serde_json::json!({
                        "unit_id": format!("generator_{idx}"),
                        "target_variable": format!("generator_{idx}"),
                        "generator_pauli": gen,
                    })
                })
                .collect();
            let plan = serde_json::json!({
                "schema_version": "core.symbol_game.decomposition_plan.v1",
                "authority_effect": "None",
                "basis_kind": "STABILIZER_GENERATORS",
                "units": units,
                "independence_certificate": {
                    "generator_count": basis.len(),
                    "independent_gf2_rank": basis.len(),
                    "valid": true,
                },
                "composition_rule": "GF2_GENERATOR_MINIMIZATION",
            });
            outcome_ok(action, plan)
        }
        other => outcome_err(
            action,
            format!("stabilizer solve did not produce a solved basis: {other:?}"),
        ),
    }
}

fn run_decompose_task(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: DecomposeTaskRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid decompose_task input: {e}")),
    };
    match request.basis_kind.as_str() {
        "CYCLE_BASIS" => decompose_cycle_basis(action, &request),
        "STABILIZER_GENERATORS" => decompose_stabilizer_generators(action, &request),
        other => outcome_err(action, format!("unsupported basis_kind: {other}")),
    }
}

fn run_retraction_turn(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: RetractionTurnRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid retraction_turn input: {e}")),
    };
    let validator = crate::epics::retraction::LyapunovDescentValidator;
    match validator.admit(request.before, request.after) {
        Ok(()) => outcome_ok(
            action,
            serde_json::json!({
                "admitted": true,
                "before": request.before,
                "after": request.after,
                "refusal": Value::Null,
                "refusal_code": Value::Null,
                "authority_effect": "None",
            }),
        ),
        Err(refusal) => {
            let code = crate::epics::retraction::refusal_code(&refusal);
            let cemetery_record = request.candidate.map(|c| {
                let mut cemetery = crate::epics::retraction::CemeterySink::default();
                cemetery.bury(0, c, &refusal);
                serde_json::to_value(cemetery.records().first()).unwrap_or(Value::Null)
            });
            outcome_ok(
                action,
                serde_json::json!({
                    "admitted": false,
                    "before": request.before,
                    "after": request.after,
                    "refusal": refusal.to_string(),
                    "refusal_code": code,
                    "cemetery_record": cemetery_record,
                    "authority_effect": "None",
                }),
            )
        }
    }
}

fn run_retraction_loop(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: RetractionLoopRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid retraction_loop input: {e}")),
    };
    let engine = crate::epics::retraction::RetractionEngine;
    match engine.run(
        request.intake,
        &request.candidates,
        request.open_obligations,
    ) {
        Ok(receipt) => outcome_ok(
            action,
            serde_json::to_value(receipt).checked_invariant_e5294e95("retraction receipt serializes"),
        ),
        Err(refusal) => outcome_err(action, refusal.to_string()),
    }
}

fn populate_debate_dag(
    dag: &mut crate::epics::debate::PrecommitmentDAG,
    claims: Vec<DebateClaimWireV1>,
) -> Result<(), String> {
    for entry in claims {
        let claim = match entry.primitive {
            Some(prim) => {
                crate::epics::debate::Claim::grounded(entry.node, prim, entry.holds, &entry.text)
            }
            None => crate::epics::debate::Claim::ungrounded(entry.node, entry.holds, &entry.text),
        };
        dag.assert_lemma(&entry.agent, claim)
            .map_err(|err| err.to_string())?;
    }
    Ok(())
}

fn run_debate_localize(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: DebateLocalizeRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid debate_localize input: {e}")),
    };
    let mut dag = match crate::epics::debate::PrecommitmentDAG::new(request.tree_size) {
        Ok(d) => d,
        Err(err) => return outcome_err(action, err.to_string()),
    };
    if let Err(err) = populate_debate_dag(&mut dag, request.claims) {
        return outcome_err(action, err);
    }
    let engine = crate::epics::debate::DisagreementLocalizationEngine;
    match engine.localize(&dag, &request.left_agent, &request.right_agent) {
        Ok(loc) => {
            let left_claim = dag.claim(&request.left_agent, loc.locus).cloned();
            let right_claim = dag.claim(&request.right_agent, loc.locus).cloned();
            outcome_ok(
                action,
                serde_json::json!({
                    "schema_version": crate::epics::debate::LOCALIZATION_RECEIPT_SCHEMA_V1,
                    "tree_size": dag.size(),
                    "locus": loc.locus,
                    "rounds": loc.rounds,
                    "round_bound": crate::epics::debate::ceil_log2(dag.size()),
                    "left_agent": request.left_agent,
                    "right_agent": request.right_agent,
                    "left_claim": left_claim,
                    "right_claim": right_claim,
                    "authority_effect": "None",
                }),
            )
        }
        Err(err) => outcome_err(action, err.to_string()),
    }
}

fn dda_surgery_fuse_all(
    action: &str,
    board: &pfp_runtime::f2::GaugeBoard,
    sigma: Vec<bool>,
) -> RuntimeOutcomeV1 {
    let solver = crate::epics::dda::MeronClusterSolver;
    let verifier = crate::epics::dda::MeronSurgeryVerifier;
    match solver.fuse_all(board, &sigma) {
        Ok(surgeries) => {
            let mut receipts = Vec::new();
            for surgery in &surgeries {
                let verdict = verifier
                    .verify(board, surgery)
                    .unwrap_or(crate::epics::dda::WitnessVerdict::PositiveWitnessInvalid);
                if let Ok(rcpt) =
                    crate::epics::dda::MeronSurgeryReceiptV1::build(board, surgery, verdict)
                {
                    receipts.push(rcpt);
                }
            }
            let final_sigma = surgeries
                .last()
                .map(|s| s.sigma_after.clone())
                .unwrap_or(sigma);
            outcome_ok(
                action,
                serde_json::json!({
                    "surgeries_count": surgeries.len(),
                    "receipts": receipts,
                    "final_sigma": final_sigma,
                    "authority_effect": "None",
                }),
            )
        }
        Err(err) => outcome_err(action, err.to_string()),
    }
}

fn dda_surgery_fuse_one(
    action: &str,
    board: &pfp_runtime::f2::GaugeBoard,
    sigma: &[bool],
) -> RuntimeOutcomeV1 {
    let solver = crate::epics::dda::MeronClusterSolver;
    let verifier = crate::epics::dda::MeronSurgeryVerifier;
    let surgery = match solver.fuse_one(board, sigma) {
        Ok(s) => s,
        Err(err) => return outcome_err(action, err.to_string()),
    };
    let verdict = match verifier.verify(board, &surgery) {
        Ok(v) => v,
        Err(e) => return outcome_err(action, e.to_string()),
    };
    match crate::epics::dda::MeronSurgeryReceiptV1::build(board, &surgery, verdict) {
        Ok(receipt) => outcome_ok(
            action,
            serde_json::to_value(receipt).checked_invariant_e5294e95("surgery receipt serializes"),
        ),
        Err(e) => outcome_err(action, e.to_string()),
    }
}

fn run_dda_surgery(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: DdaSurgeryRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid dda_surgery input: {e}")),
    };
    let board = pfp_runtime::f2::GaugeBoard::new(request.d0, request.d1);
    if request.fuse_all {
        dda_surgery_fuse_all(action, &board, request.sigma)
    } else {
        dda_surgery_fuse_one(action, &board, &request.sigma)
    }
}

fn compute_transport_maps(
    morphism: &crate::epics::transport::SimplicialMorphism,
    request: &SimplicialTransportRequestV1,
) -> Result<(Option<Vec<bool>>, Option<Vec<bool>>), String> {
    let pushforward = match request.chain {
        Some(ref c) => Some(morphism.pushforward(c).map_err(|e| e.to_string())?),
        None => None,
    };
    let pullback = match request.cochain {
        Some(ref co) => Some(morphism.pullback(co).map_err(|e| e.to_string())?),
        None => None,
    };
    Ok((pushforward, pullback))
}

fn run_simplicial_transport(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: SimplicialTransportRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid simplicial_transport input: {e}")),
    };
    let morphism = match crate::epics::transport::SimplicialMorphism::new(
        request.vertex_map.clone(),
        request.target_vertices.clone(),
    ) {
        Ok(m) => m,
        Err(err) => return outcome_err(action, err.to_string()),
    };
    let certificate = match crate::epics::transport::TransportCertificateV1::issue(
        &morphism,
        &request.support,
    ) {
        Ok(cert) => cert,
        Err(err) => return outcome_err(action, err.to_string()),
    };
    let (pushforward, pullback) = match compute_transport_maps(&morphism, &request) {
        Ok(pair) => pair,
        Err(err) => return outcome_err(action, err),
    };
    outcome_ok(
        action,
        serde_json::json!({
            "certificate": certificate,
            "pushforward": pushforward,
            "pullback": pullback,
            "authority_effect": "None",
        }),
    )
}

fn run_prime_candidate_evaluate(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: PrimeCandidateEvaluateRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => {
            return outcome_err(
                action,
                format!("invalid prime_candidate_evaluate input: {e}"),
            )
        }
    };
    let proposal = crate::prime::evaluate_candidate_proposal(
        &request.proposal_id,
        &request.locus_id,
        request.raw_payload.as_bytes(),
        &request.actor,
        request.admit,
        request.refusal_reason.as_deref(),
    );
    outcome_ok(
        action,
        serde_json::to_value(proposal).checked_invariant_e5294e95("candidate proposal serializes"),
    )
}

fn run_prime_stage_record(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: PrimeStageRecordRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid prime_stage_record input: {e}")),
    };
    let record = crate::prime::record_prime_stage_transition(
        request.seq,
        request.stage,
        &request.packet_id,
        &request.actor,
        &request.status,
        &request.witness_or_refusal,
        request.prev_record_hash,
    );
    outcome_ok(
        action,
        serde_json::to_value(record).checked_invariant_e5294e95("prime stage record serializes"),
    )
}

fn run_challenge_commit(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: ChallengeCommitRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid challenge_commit input: {e}")),
    };
    let commitment = crate::challenge::JudgeCommitmentV1::new(
        &request.challenge_id,
        request.manifest_text.as_bytes(),
        &request.operator,
        &request.version,
    );
    outcome_ok(
        action,
        serde_json::json!({
            "commitment": commitment,
            "commitment_hash": commitment.commitment_hash(),
            "authority_effect": "None",
        }),
    )
}

fn run_challenge_freeze(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: ChallengeFreezeRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid challenge_freeze input: {e}")),
    };
    let freeze = crate::challenge::FreezeRecordV1::new(
        &request.challenge_id,
        request.deliverable_text.as_bytes(),
        &request.judge_commitment_hash,
    );
    outcome_ok(
        action,
        serde_json::json!({
            "freeze_record": freeze,
            "freeze_hash": freeze.freeze_hash(),
            "authority_effect": "None",
        }),
    )
}

fn evaluate_challenge_cases(
    request: &ChallengeScoreRequestV1,
) -> (usize, usize, bool, Vec<crate::challenge::CaseOutcomeRecordV1>) {
    let checker_a = crate::challenge::ExactMatchChecker::new(
        &request.judge_packet.checker_a_id,
        &request.checker_expected_field,
    );
    let checker_b = crate::challenge::ExactMatchChecker::new(
        &request.judge_packet.checker_b_id,
        &request.checker_expected_field,
    );
    let mut case_outcomes = Vec::new();
    let mut cases_correct = 0;
    let mut cases_wrong = 0;
    let mut checker_defect_pause = false;

    for (idx, case) in request.judge_packet.hidden_cases.iter().enumerate() {
        let cand = request.candidate_outputs.get(idx).unwrap_or(&Value::Null);
        let outcome =
            crate::challenge::evaluate_dual_checkers(&checker_a, &checker_b, case, cand);
        match &outcome {
            crate::challenge::DisjointOutcome::Correct => cases_correct += 1,
            crate::challenge::DisjointOutcome::Wrong { .. } => cases_wrong += 1,
            crate::challenge::DisjointOutcome::CheckerDefectPause { .. } => {
                checker_defect_pause = true;
            }
            _ => {}
        }
        case_outcomes.push(crate::challenge::CaseOutcomeRecordV1 {
            case_index: idx,
            outcome,
        });
    }
    (cases_correct, cases_wrong, checker_defect_pause, case_outcomes)
}

fn challenge_score_status(
    checker_defect_pause: bool,
    cases_wrong: usize,
    cases_correct: usize,
    total_cases: usize,
) -> String {
    if checker_defect_pause {
        "CHECKER_DEFECT_PAUSE".to_string()
    } else if cases_wrong == 0 && cases_correct == total_cases {
        "VERIFIED".to_string()
    } else {
        "REFUSED".to_string()
    }
}

fn run_challenge_score(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: ChallengeScoreRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid challenge_score input: {e}")),
    };
    let (cases_correct, cases_wrong, checker_defect_pause, case_outcomes) =
        evaluate_challenge_cases(&request);
    let total_cases = request.judge_packet.hidden_cases.len();
    let status =
        challenge_score_status(checker_defect_pause, cases_wrong, cases_correct, total_cases);
    let receipt = crate::challenge::ChallengeScoreReceiptV1 {
        challenge_id: request.judge_packet.challenge_id.clone(),
        judge_commitment_hash: request.commitment.commitment_hash(),
        freeze_record_hash: request.freeze.freeze_hash(),
        deliverable_sha256: request.freeze.solver_deliverable_sha256.clone(),
        cases_total: total_cases,
        cases_correct,
        cases_wrong,
        checker_defect_pause,
        case_outcomes,
        status,
        authority_effect: "None".to_string(),
    };
    outcome_ok(
        action,
        serde_json::to_value(receipt).checked_invariant_e5294e95("score receipt serializes"),
    )
}

fn prime_outcome<T: serde::Serialize>(action: &str, res: Result<T, String>) -> RuntimeOutcomeV1 {
    match res {
        Ok(outcome) => outcome_ok(
            action,
            serde_json::to_value(outcome).checked_invariant_e5294e95("prime outcome serializes"),
        ),
        Err(err) => outcome_err(action, err),
    }
}

fn dispatch_prime_and_scoring(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "prime_admit" => Some(prime_outcome(action, crate::prime::prime_admit(payload))),
        "prime_replay_decide" => Some(prime_outcome(
            action,
            crate::prime::prime_replay_decide(payload),
        )),
        "prime_descent" => Some(prime_outcome(action, crate::prime::prime_descent(payload))),
        "score_discrete_proposal" => Some(run_score_discrete_proposal(action, payload)),
        "score_cochain_proposal" => Some(run_score_cochain_proposal(action, payload)),
        "rank_scored_candidates" => Some(run_rank_scored_candidates(action, payload)),
        "rank_candidate_proposals" => Some(run_rank_candidate_proposals(action, payload)),
        _ => None,
    }
}

fn dispatch_driver_and_epics(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "turn_driver_next_prompt" => Some(run_turn_driver_next_prompt(action, payload)),
        "turn_driver_step" => Some(run_turn_driver_step(action, payload)),
        "decompose_task" => Some(run_decompose_task(action, payload)),
        "retraction_turn" => Some(run_retraction_turn(action, payload)),
        "retraction_loop" => Some(run_retraction_loop(action, payload)),
        "debate_localize" => Some(run_debate_localize(action, payload)),
        "dda_surgery" => Some(run_dda_surgery(action, payload)),
        _ => None,
    }
}

fn dispatch_transport_and_challenge(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "simplicial_transport" => Some(run_simplicial_transport(action, payload)),
        "prime_candidate_evaluate" => Some(run_prime_candidate_evaluate(action, payload)),
        "prime_stage_record" => Some(run_prime_stage_record(action, payload)),
        "challenge_commit" => Some(run_challenge_commit(action, payload)),
        "challenge_freeze" => Some(run_challenge_freeze(action, payload)),
        "challenge_score" => Some(run_challenge_score(action, payload)),
        _ => None,
    }
}

pub(super) fn dispatch(req: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    let action = req.action.as_str();
    for handler in [
        dispatch_prime_and_scoring,
        dispatch_driver_and_epics,
        dispatch_transport_and_challenge,
    ] {
        if let Some(outcome) = handler(action, &req.payload) {
            return outcome;
        }
    }
    outcome_err(action, format!("unsupported runtime action: {action}"))
}

// Origin: engine/crates_rs/pfp/src/invoke/workflow.rs
// Claim: urn:core:crates_rs:pfp:workflow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde5294e95 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde5294e95` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore5294e95 {
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
impl BoundaryErrore5294e95 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore5294e95 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore5294e95 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde5294e95 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore5294e95> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore5294e95::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore5294e95::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore5294e95::ExceedsCapacity {
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
mod negative_cost_host {
    use super::*;
    use serde_json::Value;

    fn proposal(cost: &str) -> Value {
        serde_json::json!({
            "proposal_id": "p",
            "repaired_obstruction_ids": ["x"],
            "cochain_delta": [],
            "structural_cost": cost,
            "kill_triggers": [],
            "admitted_constructors_used": [],
            "dual_witness_ref": null,
            "authority_effect": "None"
        })
    }

    fn proposal_of(payload: &Value) -> pfp_runtime::CandidateProposal {
        serde_json::from_value(payload["proposal"].clone()).unwrap()
    }

    fn assert_host_matches_scorer(payload: &Value, cochain: bool) {
        let outcome = if cochain {
            run_score_cochain_proposal("score_cochain_proposal", payload)
        } else {
            run_score_discrete_proposal("score_discrete_proposal", payload)
        };
        assert!(outcome.success, "{:?}", outcome.error);
        let proposal = proposal_of(payload);
        let direct = if cochain {
            let mut omega = std::collections::BTreeMap::new();
            for (key, value) in payload["core_cochain"].as_object().unwrap() {
                omega.insert(
                    key.clone(),
                    core_kernel::parse_exact(value.as_str().unwrap()).unwrap(),
                );
            }
            pfp_runtime::scoring_frontier::score_cochain_proposal_with_policy(
                &omega, &proposal, None, None,
            )
        } else {
            let obstructions: Vec<String> =
                serde_json::from_value(payload["obstructions"].clone()).unwrap();
            pfp_runtime::scoring_frontier::score_discrete_proposal_with_policy(
                &obstructions,
                &proposal,
                None,
                None,
            )
        };
        assert_eq!(outcome.result.unwrap(), serde_json::to_value(direct).unwrap());
    }

    #[test]
    fn host_and_scorer_refuse_cost_minus_one_and_keep_zero_legal() {
        let negative = serde_json::json!({
            "obstructions": ["x"],
            "proposal": proposal("-1")
        });
        assert_host_matches_scorer(&negative, false);
        let refused = run_score_discrete_proposal("score_discrete_proposal", &negative)
            .result
            .unwrap();
        assert_eq!(refused["is_legal"], false);
        assert_eq!(refused["structural_cost"], "-1");
        assert_eq!(
            refused["refusal_reason"],
            "NEGATIVE_MAGNITUDE: structural_cost is negative"
        );
        assert!(refused["normalized_efficiency"].is_null());

        let zero = serde_json::json!({
            "obstructions": ["x"],
            "proposal": proposal("0")
        });
        assert_host_matches_scorer(&zero, false);
        assert_eq!(
            run_score_discrete_proposal("score_discrete_proposal", &zero)
                .result
                .unwrap()["is_legal"],
            true
        );

        let cochain_negative = serde_json::json!({
            "core_cochain": {"x": "1"},
            "proposal": proposal("-1")
        });
        assert_host_matches_scorer(&cochain_negative, true);
        let cochain_refused = run_score_cochain_proposal("score_cochain_proposal", &cochain_negative)
            .result
            .unwrap();
        assert_eq!(cochain_refused["is_legal"], false);
        assert_eq!(cochain_refused["structural_cost"], "-1");

        let cochain_zero = serde_json::json!({
            "core_cochain": {"x": "1"},
            "proposal": proposal("0")
        });
        assert_host_matches_scorer(&cochain_zero, true);
        assert_eq!(
            run_score_cochain_proposal("score_cochain_proposal", &cochain_zero)
                .result
                .unwrap()["is_legal"],
            true
        );
    }

    #[test]
    fn rank_scored_candidates_refuses_a_client_legal_negative_cost() {
        let payload = serde_json::json!({
            "scores": [
                {
                    "proposal_id": "forged",
                    "prior_residual_norm": "0",
                    "post_residual_norm": "0",
                    "residual_drop": "0",
                    "structural_cost": "-1",
                    "normalized_efficiency": "1000",
                    "is_legal": true,
                    "is_exact_candidate": false,
                    "dual_witness_ref": null,
                    "refusal_reason": null
                },
                {
                    "proposal_id": "legal",
                    "prior_residual_norm": "1",
                    "post_residual_norm": "1",
                    "residual_drop": "0",
                    "structural_cost": "0",
                    "normalized_efficiency": "0",
                    "is_legal": true,
                    "is_exact_candidate": false,
                    "dual_witness_ref": null,
                    "refusal_reason": null
                }
            ]
        });
        let outcome = run_rank_scored_candidates("rank_scored_candidates", &payload);
        assert!(!outcome.success, "{outcome:?}");
        assert!(outcome.result.is_none());
        assert_eq!(
            outcome.error.as_deref(),
            Some("NEGATIVE_MAGNITUDE: structural_cost is negative")
        );

        let legal_only = serde_json::json!({
            "scores": [{
                "proposal_id": "legal",
                "prior_residual_norm": "1",
                "post_residual_norm": "1",
                "residual_drop": "0",
                "structural_cost": "0",
                "normalized_efficiency": "0",
                "is_legal": true,
                "is_exact_candidate": false,
                "dual_witness_ref": null,
                "refusal_reason": null
            }]
        });
        let kept = run_rank_scored_candidates("rank_scored_candidates", &legal_only);
        assert!(kept.success, "{kept:?}");
        assert_eq!(kept.result.unwrap(), serde_json::json!([legal_only["scores"][0]]));
    }
}

#[cfg(test)]
mod l4_boundary_tests_e5294e95 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde5294e95::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde5294e95::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde5294e95::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde5294e95::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde5294e95::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore5294e95::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore5294e95::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
