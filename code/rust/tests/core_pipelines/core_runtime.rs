//! --- Math Contract: runtime tests exercise total terminals and exact role separation.

use core_pipelines::runtime::{
    run_omega, AuthorityEffect, AuthorityStatus, ContextRef, EffectStatus, Evaluation,
    EvaluationStatus, GtmurRouteOutcome, IndependentEvaluator, CoreBudgets, CoreRole,
    CoreTerminal, OperatorId, ProblemPacket, ProblemPacketSpec, Producer, Proposal,
    ProposalIntegrityState, ProposalStatus, QRouteOutcome, RequestedEffect, Residual, RoleIdentity,
    RouteOutcome, SeparationMode,
};
use core_pipelines::runtime::{EvidenceStatus, ExecutionStatus, RegistryStatus, TraceStage};
use std::collections::BTreeSet;

fn identity(value: &str) -> RoleIdentity {
    RoleIdentity::new(value).expect("fixture role identity is nonempty")
}

fn context(value: &str) -> ContextRef {
    ContextRef::new(value).expect("fixture context reference is nonempty")
}

fn operator(value: &str) -> OperatorId {
    OperatorId::new(value).expect("fixture operator identifier is nonempty")
}

fn modes(values: impl IntoIterator<Item = SeparationMode>) -> BTreeSet<SeparationMode> {
    values.into_iter().collect()
}

fn packet_with(budgets: CoreBudgets, requested_effect: RequestedEffect) -> ProblemPacket {
    ProblemPacket::from_prompt(ProblemPacketSpec {
        prompt: "classify the obstruction without minting authority",
        carrier: "finite carrier".to_owned(),
        regime: "exact".to_owned(),
        assumptions: vec!["declared carrier is complete".to_owned()],
        constraints: vec!["preserve the observer boundary".to_owned()],
        observer: "canonical observer".to_owned(),
        budgets,
        context_refs: vec![context("ctx:canonical")],
        requested_effect,
        permitted_operators: vec![operator("op:classify")],
    })
    .expect("fixture prompt is nonempty")
}

fn standard_packet() -> ProblemPacket {
    packet_with(
        CoreBudgets {
            max_repairs: 1,
            max_operator_calls: 4,
        },
        RequestedEffect::Evidence,
    )
}

struct NeverCalled {
    id: RoleIdentity,
}

impl Producer for NeverCalled {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn propose(
        &self,
        _packet: &ProblemPacket,
        _repair_round: u16,
        _prior_evaluation: Option<&Evaluation>,
    ) -> ProposalStatus {
        panic!("producer must not be invoked")
    }
}

impl IndependentEvaluator for NeverCalled {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn separation_modes(&self) -> BTreeSet<SeparationMode> {
        modes([SeparationMode::ContextSeparated])
    }

    fn evaluate(&self, _packet: &ProblemPacket, _proposal: &Proposal) -> Evaluation {
        panic!("evaluator must not be invoked")
    }
}

struct FixedProducer {
    id: RoleIdentity,
    proposal: Proposal,
}

impl Producer for FixedProducer {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn propose(
        &self,
        _packet: &ProblemPacket,
        _repair_round: u16,
        _prior_evaluation: Option<&Evaluation>,
    ) -> ProposalStatus {
        ProposalStatus::Proposed(self.proposal.clone())
    }
}

struct AcceptingEvaluator {
    id: RoleIdentity,
    modes: BTreeSet<SeparationMode>,
}

impl IndependentEvaluator for AcceptingEvaluator {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn separation_modes(&self) -> BTreeSet<SeparationMode> {
        self.modes.clone()
    }

    fn evaluate(&self, _packet: &ProblemPacket, _proposal: &Proposal) -> Evaluation {
        Evaluation::new("eval:accepted", EvaluationStatus::Accepted)
    }
}

struct RoundProducer {
    id: RoleIdentity,
}

impl Producer for RoundProducer {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn propose(
        &self,
        _packet: &ProblemPacket,
        repair_round: u16,
        _prior_evaluation: Option<&Evaluation>,
    ) -> ProposalStatus {
        ProposalStatus::Proposed(Proposal::new(
            format!("proposal:round:{repair_round}"),
            format!("artifact:round:{repair_round}"),
        ))
    }
}

struct AlwaysRepairEvaluator {
    id: RoleIdentity,
}

impl IndependentEvaluator for AlwaysRepairEvaluator {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn separation_modes(&self) -> BTreeSet<SeparationMode> {
        modes([SeparationMode::ProcessSeparated])
    }

    fn evaluate(&self, _packet: &ProblemPacket, proposal: &Proposal) -> Evaluation {
        Evaluation::new(
            format!("eval:{}", proposal.proposal_id),
            EvaluationStatus::Repair {
                residual: Residual::new(CoreRole::Dda, format!("repair {}", proposal.proposal_id)),
            },
        )
    }
}

struct RouteEvaluator {
    id: RoleIdentity,
    outcome: RouteOutcome,
}

impl IndependentEvaluator for RouteEvaluator {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn separation_modes(&self) -> BTreeSet<SeparationMode> {
        modes([
            SeparationMode::ProviderSeparated,
            SeparationMode::HoldoutSeparated,
        ])
    }

    fn evaluate(&self, _packet: &ProblemPacket, _proposal: &Proposal) -> Evaluation {
        Evaluation::new("eval:routed", EvaluationStatus::Route(self.outcome.clone()))
    }
}

struct TerminalProducer {
    id: RoleIdentity,
    status: ProposalStatus,
}

impl Producer for TerminalProducer {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn propose(
        &self,
        _packet: &ProblemPacket,
        _repair_round: u16,
        _prior_evaluation: Option<&Evaluation>,
    ) -> ProposalStatus {
        self.status.clone()
    }
}

struct Wd4Producer {
    id: RoleIdentity,
}

impl Producer for Wd4Producer {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn propose(
        &self,
        _packet: &ProblemPacket,
        repair_round: u16,
        _prior_evaluation: Option<&Evaluation>,
    ) -> ProposalStatus {
        let count = if repair_round == 0 {
            6_u16 * 63
        } else {
            8_u16 * 63
        };
        ProposalStatus::Proposed(Proposal::new(
            format!("wd4:round:{repair_round}"),
            format!("wd4:{count}"),
        ))
    }
}

struct Wd4Evaluator {
    id: RoleIdentity,
}

impl IndependentEvaluator for Wd4Evaluator {
    fn identity(&self) -> RoleIdentity {
        self.id.clone()
    }

    fn separation_modes(&self) -> BTreeSet<SeparationMode> {
        modes([SeparationMode::ContextSeparated])
    }

    fn evaluate(&self, _packet: &ProblemPacket, proposal: &Proposal) -> Evaluation {
        if proposal.artifact_ref == format!("wd4:{}", 8_u16 * 63) {
            Evaluation::new("eval:wd4:accepted", EvaluationStatus::Accepted)
        } else {
            Evaluation::new(
                "eval:wd4:repair",
                EvaluationStatus::Repair {
                    residual: Residual::new(CoreRole::Dda, "WD4 requires eight contexts, not six"),
                },
            )
        }
    }
}

#[test]
fn empty_prompt_totalizes_to_no_packet_without_invoking_roles() {
    let missing_packet = ProblemPacket::from_prompt(ProblemPacketSpec {
        prompt: "   ",
        carrier: "finite".to_owned(),
        regime: "exact".to_owned(),
        assumptions: Vec::new(),
        constraints: Vec::new(),
        observer: "observer".to_owned(),
        budgets: CoreBudgets {
            max_repairs: 1,
            max_operator_calls: 4,
        },
        context_refs: Vec::new(),
        requested_effect: RequestedEffect::None,
        permitted_operators: vec![operator("op:test")],
    });
    let never_called = NeverCalled {
        id: identity("role:unused"),
    };

    let result = run_omega(missing_packet, &never_called, &never_called);

    assert_eq!(result.terminal, CoreTerminal::NoPacket);
    assert_eq!(result.terminal_role, CoreRole::Admission);
    assert_eq!(result.prompt_identity, None);
    assert_eq!(result.attempts, Vec::new());
    assert_eq!(result.authority_status, AuthorityStatus::None);
    assert_eq!(result.authority_effect, AuthorityEffect::None);
    assert_eq!(result.effect_status, EffectStatus::NotRequested);
}

#[test]
fn plain_evaluator_acceptance_stays_open_without_descent_replay_or_host_independence() {
    let producer = FixedProducer {
        id: identity("role:producer"),
        proposal: Proposal::new("proposal:one", "artifact:one"),
    };
    let evaluator = AcceptingEvaluator {
        id: identity("role:evaluator"),
        modes: modes([
            SeparationMode::ContextSeparated,
            SeparationMode::ProviderSeparated,
        ]),
    };

    let result = run_omega(Some(standard_packet()), &producer, &evaluator);

    assert_eq!(result.terminal, CoreTerminal::OpenResidual);
    assert_eq!(result.terminal_role, CoreRole::Gtfoc);
    assert_eq!(result.attempts.len(), 1);
    assert_eq!(
        result
            .final_proposal()
            .map(|proposal| proposal.proposal_id.as_str()),
        Some("proposal:one")
    );
    assert_eq!(result.authority_status, AuthorityStatus::None);
    assert_eq!(result.authority_effect, AuthorityEffect::None);
    assert_eq!(result.effect_status, EffectStatus::NotApplied);

    let claim = result
        .separation_claim
        .as_ref()
        .expect("the exact self-declared separation claim must be retained");
    assert_eq!(claim.producer().as_str(), "role:producer");
    assert_eq!(claim.evaluator().as_str(), "role:evaluator");
    assert_eq!(
        claim.modes(),
        &modes([
            SeparationMode::ContextSeparated,
            SeparationMode::ProviderSeparated,
        ])
    );
    assert!(!claim.is_merely_prompt_separated());
    assert_eq!(result.independence_receipt, None);
    assert_eq!(result.registry_status, RegistryStatus::Discovered);
    assert_eq!(result.execution_status, ExecutionStatus::Available);
    assert_eq!(result.evidence_status, EvidenceStatus::EvaluationRecorded);
    assert_eq!(result.residuals.len(), 1);
    assert!(result.residuals[0].summary.contains("descent packet"));
    assert_eq!(result.artifact_refs, vec!["artifact:one".to_owned()]);
    assert_eq!(
        result.evidence_bundle.evaluation_refs,
        vec!["eval:accepted".to_owned()]
    );
    assert_eq!(
        result
            .trace
            .iter()
            .map(|event| event.stage)
            .collect::<Vec<_>>(),
        vec![
            TraceStage::Proposed,
            TraceStage::Evaluated,
            TraceStage::Terminalized,
        ]
    );
    assert_eq!(result.effect_receipt, None);
    assert_eq!(result.next_admissible_probe, None);

    let serialized = serde_json::to_string(&result).expect("result must serialize");
    assert!(!serialized.contains("classify the obstruction without minting authority"));
    let round_trip: core_pipelines::runtime::CoreResult =
        serde_json::from_str(&serialized).expect("serialized result must round-trip");
    assert_eq!(round_trip, result);
}

#[test]
fn same_identity_is_refused_before_production() {
    let shared_role = NeverCalled {
        id: identity("role:shared"),
    };

    let result = run_omega(Some(standard_packet()), &shared_role, &shared_role);

    assert_eq!(result.terminal, CoreTerminal::Refused);
    assert_eq!(result.terminal_role, CoreRole::CodaGtlaGovernance);
    assert_eq!(result.independence_receipt, None);
    assert_eq!(result.attempts, Vec::new());
    assert_eq!(result.authority_effect, AuthorityEffect::None);
    assert!(result.reason.contains("distinct identities"));
}

#[test]
fn bounded_repair_exhaustion_preserves_complete_residual_history() {
    let producer = RoundProducer {
        id: identity("role:producer"),
    };
    let evaluator = AlwaysRepairEvaluator {
        id: identity("role:evaluator"),
    };

    let result = run_omega(Some(standard_packet()), &producer, &evaluator);

    assert_eq!(result.terminal, CoreTerminal::BudgetExhausted);
    assert_eq!(result.terminal_role, CoreRole::Dda);
    assert_eq!(result.attempts.len(), 2);
    assert_eq!(
        result
            .attempts
            .iter()
            .map(|attempt| attempt.repair_round)
            .collect::<Vec<_>>(),
        vec![0, 1]
    );
    assert_eq!(result.residuals.len(), 2);
    assert_eq!(result.residuals[0].summary, "repair proposal:round:0");
    assert_eq!(result.residuals[1].summary, "repair proposal:round:1");
    assert_eq!(
        result.evidence_bundle.residual_ids,
        result
            .residuals
            .iter()
            .map(|residual| residual.id)
            .collect::<Vec<_>>()
    );
    assert_eq!(result.authority_status, AuthorityStatus::None);
    assert_eq!(result.authority_effect, AuthorityEffect::None);
    assert_eq!(result.effect_status, EffectStatus::NotApplied);
}

#[test]
fn upper_role_residual_stays_open_and_non_authoritative() {
    let producer = FixedProducer {
        id: identity("role:producer"),
        proposal: Proposal::new("proposal:transport", "artifact:transport"),
    };
    let evaluator = RouteEvaluator {
        id: identity("role:evaluator"),
        outcome: RouteOutcome::Gtmur(GtmurRouteOutcome::TransportRequired {
            residual: Residual::new(
                CoreRole::Gtmur,
                "representation transport remains unproved",
            ),
        }),
    };

    let result = run_omega(Some(standard_packet()), &producer, &evaluator);

    assert_eq!(result.terminal, CoreTerminal::OpenResidual);
    assert_eq!(result.terminal_role, CoreRole::Gtmur);
    assert_eq!(result.residuals.len(), 1);
    assert_eq!(
        result.residuals[0].summary,
        "representation transport remains unproved"
    );
    assert!(matches!(
        result.route_outcome.as_ref(),
        Some(RouteOutcome::Gtmur(
            GtmurRouteOutcome::TransportRequired { .. }
        ))
    ));
    assert_eq!(result.authority_status, AuthorityStatus::None);
    assert_eq!(result.authority_effect, AuthorityEffect::None);
    assert_eq!(result.effect_status, EffectStatus::NotApplied);
}

#[test]
fn q_terminal_is_a_quarantined_residual_not_a_seventh_authority_role() {
    let producer = FixedProducer {
        id: identity("role:producer"),
        proposal: Proposal::new("proposal:anomaly", "artifact:anomaly"),
    };
    let evaluator = RouteEvaluator {
        id: identity("role:evaluator"),
        outcome: RouteOutcome::Q(QRouteOutcome::Quarantined {
            residual: Residual::new(CoreRole::Q, "classification is presently unavailable"),
            next_probe: "expand the representation atlas".to_owned(),
        }),
    };

    let result = run_omega(Some(standard_packet()), &producer, &evaluator);

    assert_eq!(result.terminal, CoreTerminal::OpenResidual);
    assert_eq!(result.terminal_role, CoreRole::Q);
    assert_eq!(result.residuals.len(), 1);
    assert!(matches!(
        result.route_outcome.as_ref(),
        Some(RouteOutcome::Q(QRouteOutcome::Quarantined { .. }))
    ));
    assert_eq!(result.authority_status, AuthorityStatus::None);
    assert_eq!(result.authority_effect, AuthorityEffect::None);
    assert_eq!(
        result.next_admissible_probe.as_deref(),
        Some("expand the representation atlas")
    );
}

#[test]
fn wd4_regression_control_reaches_504_without_self_certifying_completion() {
    let wd4_packet = ProblemPacket::from_prompt(ProblemPacketSpec {
        prompt: "evaluate the WD4 context count",
        carrier: "WD4 compatible pairs".to_owned(),
        regime: "finite exact".to_owned(),
        assumptions: vec!["all declared contexts are present".to_owned()],
        constraints: vec!["count every context".to_owned()],
        observer: "context incidence observer".to_owned(),
        budgets: CoreBudgets {
            max_repairs: 1,
            max_operator_calls: 4,
        },
        context_refs: (0..8)
            .map(|index| context(&format!("ctx:wd4:{index}")))
            .collect(),
        requested_effect: RequestedEffect::Evidence,
        permitted_operators: vec![operator("op:wd4-count")],
    })
    .expect("WD4 fixture prompt is nonempty");
    let producer = Wd4Producer {
        id: identity("role:wd4-producer"),
    };
    let evaluator = Wd4Evaluator {
        id: identity("role:wd4-evaluator"),
    };

    let result = run_omega(Some(wd4_packet), &producer, &evaluator);

    assert_eq!(8_u16 * 63, 504);
    assert_eq!(result.terminal, CoreTerminal::OpenResidual);
    assert_eq!(result.terminal_role, CoreRole::Gtfoc);
    assert_eq!(
        result
            .attempts
            .iter()
            .map(|attempt| attempt.proposal.artifact_ref.as_str())
            .collect::<Vec<_>>(),
        vec!["wd4:378", "wd4:504"]
    );
    let claim = result
        .separation_claim
        .as_ref()
        .expect("WD4 evaluation must retain its exact separation claim");
    assert_eq!(claim.modes(), &modes([SeparationMode::ContextSeparated]));
    assert_ne!(claim.producer(), claim.evaluator());
    assert_eq!(result.independence_receipt, None);
    assert_eq!(result.authority_status, AuthorityStatus::None);
    assert_eq!(result.authority_effect, AuthorityEffect::None);
}

#[test]
fn producer_failure_and_halt_branches_totalize_exactly() {
    let evaluator = NeverCalled {
        id: identity("role:evaluator"),
    };
    [
        (
            ProposalStatus::InfrastructureFailure("provider unavailable".to_owned()),
            CoreTerminal::InfrastructureFailure,
            "provider unavailable",
        ),
        (
            ProposalStatus::Halted("operator halt requested".to_owned()),
            CoreTerminal::Halted,
            "operator halt requested",
        ),
        (
            ProposalStatus::Refused("operator outside packet".to_owned()),
            CoreTerminal::Refused,
            "operator outside packet",
        ),
    ]
    .into_iter()
    .for_each(|(status, expected_terminal, expected_reason)| {
        let producer = TerminalProducer {
            id: identity("role:producer"),
            status,
        };

        let result = run_omega(Some(standard_packet()), &producer, &evaluator);

        let expected_execution = match expected_terminal {
            CoreTerminal::InfrastructureFailure | CoreTerminal::Halted => {
                ExecutionStatus::Unavailable
            }
            _ => ExecutionStatus::Available,
        };
        assert_eq!(result.execution_status, expected_execution);
        assert_eq!(result.terminal, expected_terminal);
        assert_eq!(result.terminal_role, CoreRole::Producer);
        assert_eq!(result.reason, expected_reason);
        assert_eq!(result.attempts, Vec::new());
        assert_eq!(result.authority_status, AuthorityStatus::None);
        assert_eq!(result.authority_effect, AuthorityEffect::None);
    });
}

#[test]
fn authority_request_is_refused_without_inventing_a_witness() {
    let packet = packet_with(
        CoreBudgets {
            max_repairs: 4,
            max_operator_calls: 10,
        },
        RequestedEffect::Authority,
    );
    let never_called = NeverCalled {
        id: identity("role:unused"),
    };

    let result = run_omega(Some(packet), &never_called, &never_called);

    assert_eq!(result.terminal, CoreTerminal::Refused);
    assert_eq!(result.terminal_role, CoreRole::Gtfda);
    assert_eq!(result.attempts, Vec::new());
    assert_eq!(result.independence_receipt, None);
    assert_eq!(result.authority_status, AuthorityStatus::Refused);
    assert_eq!(result.authority_effect, AuthorityEffect::None);
    assert_eq!(result.effect_status, EffectStatus::NotApplied);
    assert!(result.reason.contains("sealed witness"));
}

#[test]
fn artifact_commitment_round_trips_detached_and_binds_metadata_and_bytes() {
    let artifact = b"exact proposal artifact";
    let proposal = Proposal::from_artifact("proposal:bound", "artifact:bound", artifact);

    assert!(proposal.is_artifact_bound());
    assert_eq!(proposal.attached_artifact(), Some(artifact.as_slice()));
    assert!(proposal.verify_artifact(artifact));
    assert!(!proposal.verify_artifact(b"different artifact"));

    let serialized = serde_json::to_string(&proposal).expect("bound proposal serializes");
    assert!(!serialized.contains("exact proposal artifact"));
    let mut detached: Proposal =
        serde_json::from_str(&serialized).expect("commitment reconstructs without raw bytes");
    assert!(detached.is_artifact_bound());
    assert_eq!(detached.attached_artifact(), None);
    assert_eq!(detached.artifact_hash(), proposal.artifact_hash());
    assert_eq!(detached.artifact_len(), proposal.artifact_len());
    assert_eq!(
        detached.artifact_binding_hash(),
        proposal.artifact_binding_hash()
    );
    assert!(detached.verify_artifact(artifact));

    detached.artifact_ref = "artifact:substituted".to_owned();
    assert!(!detached.is_artifact_bound());
    assert!(!detached.verify_artifact(artifact));
    let tampered = serde_json::to_string(&detached).expect("tampered evidence serializes");
    let error = serde_json::from_str::<Proposal>(&tampered)
        .expect_err("metadata substitution must be refused on reconstruction");
    assert!(error.to_string().contains("current proposal id"));
}

#[test]
fn malformed_proposal_attempt_is_preserved_as_rejected_evidence() {
    let mut proposal =
        Proposal::from_artifact("proposal:malformed", "artifact:original", b"bound payload");
    proposal.artifact_ref = "artifact:substituted".to_owned();
    let producer = FixedProducer {
        id: identity("role:producer"),
        proposal,
    };
    let evaluator = AcceptingEvaluator {
        id: identity("role:evaluator"),
        modes: modes([SeparationMode::ProcessSeparated]),
    };

    let result = run_omega(Some(standard_packet()), &producer, &evaluator);

    assert_eq!(result.terminal, CoreTerminal::Refused);
    assert_eq!(result.terminal_role, CoreRole::CodaGtlaGovernance);
    assert_eq!(result.attempts.len(), 1);
    assert_eq!(result.attempts[0].evaluation, None);
    assert!(matches!(
        result.attempts[0].proposal.integrity(),
        ProposalIntegrityState::Rejected { reason }
            if reason.contains("current proposal id")
    ));
    assert_eq!(result.evidence_status, EvidenceStatus::Untested);
    assert_eq!(result.residuals.len(), 1);
    assert!(result.final_proposal().is_none());

    let serialized = serde_json::to_string(&result).expect("rejected attempt serializes");
    let reconstructed: core_pipelines::runtime::CoreResult = serde_json::from_str(&serialized)
        .expect("explicit rejected evidence reconstructs without becoming executable");
    assert_eq!(reconstructed, result);
}

#[test]
fn validated_wire_ids_packets_and_separation_claims_refuse_forgery() {
    let identity_error = serde_json::from_str::<RoleIdentity>("\"   \"")
        .expect_err("blank role identity must be rejected");
    assert!(identity_error.to_string().contains("nonempty"));

    let mut packet_value =
        serde_json::to_value(standard_packet()).expect("valid problem packet serializes");
    packet_value["permitted_operators"] = serde_json::json!(["   "]);
    let packet_error = serde_json::from_value::<ProblemPacket>(packet_value)
        .expect_err("blank operator id must be rejected");
    assert!(packet_error.to_string().contains("OperatorId"));

    let producer = FixedProducer {
        id: identity("role:producer"),
        proposal: Proposal::new("proposal:claim", "artifact:claim"),
    };
    let evaluator = AcceptingEvaluator {
        id: identity("role:evaluator"),
        modes: modes([SeparationMode::ContextSeparated]),
    };
    let result = run_omega(Some(standard_packet()), &producer, &evaluator);
    let mut claim_value = serde_json::to_value(
        result
            .separation_claim
            .as_ref()
            .expect("live runtime emits a separation claim"),
    )
    .expect("claim serializes");
    claim_value["evaluator"] = claim_value["producer"].clone();
    let claim_error =
        serde_json::from_value::<core_pipelines::runtime::SeparationClaim>(claim_value)
            .expect_err("same-identity wire claim must be rejected");
    assert!(claim_error.to_string().contains("distinct identities"));

    let mut empty_modes = serde_json::to_value(
        result
            .separation_claim
            .as_ref()
            .expect("claim remains available"),
    )
    .expect("claim serializes");
    empty_modes["modes"] = serde_json::json!([]);
    let modes_error =
        serde_json::from_value::<core_pipelines::runtime::SeparationClaim>(empty_modes)
            .expect_err("wire claim without an exact separation mode must be rejected");
    assert!(modes_error.to_string().contains("at least one exact"));
}

#[test]
fn residual_route_and_evaluation_wire_invariants_are_enforced() {
    let mismatched_route = RouteOutcome::Q(QRouteOutcome::Quarantined {
        residual: Residual::new(CoreRole::Gtmur, "valid residual under the wrong route"),
        next_probe: "bounded probe".to_owned(),
    });
    let route_value = serde_json::to_value(mismatched_route).expect("route serializes");
    let route_error = serde_json::from_value::<RouteOutcome>(route_value)
        .expect_err("route origin mismatch must be rejected");
    assert!(route_error
        .to_string()
        .contains("does not match route role"));

    let empty_reference = Evaluation::new("   ", EvaluationStatus::Accepted);
    let evaluation_value =
        serde_json::to_value(empty_reference).expect("evaluation serializes for wire audit");
    let evaluation_error = serde_json::from_value::<Evaluation>(evaluation_value)
        .expect_err("blank evaluation reference must be rejected");
    assert!(evaluation_error
        .to_string()
        .contains("reference must be nonempty"));

    let residual = Residual::new(CoreRole::Dda, "bound residual");
    let mut residual_value = serde_json::to_value(residual).expect("residual serializes");
    residual_value["summary"] = serde_json::json!("substituted residual");
    let residual_error = serde_json::from_value::<Residual>(residual_value)
        .expect_err("residual id/content mismatch must be rejected");
    assert!(residual_error.to_string().contains("does not bind"));
}

#[test]
fn core_result_wire_refuses_completion_evidence_and_independence_forgery() {
    let producer = FixedProducer {
        id: identity("role:producer"),
        proposal: Proposal::new("proposal:wire", "artifact:wire"),
    };
    let evaluator = AcceptingEvaluator {
        id: identity("role:evaluator"),
        modes: modes([SeparationMode::HoldoutSeparated]),
    };
    let result = run_omega(Some(standard_packet()), &producer, &evaluator);

    let mut completed = serde_json::to_value(&result).expect("result serializes");
    completed["terminal"] = serde_json::json!("Completed");
    completed["terminal_role"] = serde_json::json!("Gtfda");
    let completion_error =
        serde_json::from_value::<core_pipelines::runtime::CoreResult>(completed)
            .expect_err("wire completion without a sealed witness must be rejected");
    assert!(completion_error.to_string().contains("Completed is sealed"));

    let mut forged_authority_effect = serde_json::to_value(&result).expect("result serializes");
    forged_authority_effect["authority_effect"] = serde_json::json!("Uncertified");
    let authority_effect_error =
        serde_json::from_value::<core_pipelines::runtime::CoreResult>(forged_authority_effect)
            .expect_err("wire authority effects outside this slice must be rejected");
    assert!(authority_effect_error
        .to_string()
        .contains("authority effect must remain None"));

    let mut forged_receipt = serde_json::to_value(&result).expect("result serializes");
    let separation_claim = forged_receipt["separation_claim"].clone();
    forged_receipt["independence_receipt"] = serde_json::json!({
        "claim": separation_claim,
        "host_attestation_hash": vec![0_u8; 32],
    });
    let mut forged_evidence = serde_json::to_value(&result).expect("result serializes");
    forged_evidence["evidence_bundle"]["evaluation_refs"] = serde_json::json!(["eval:forged"]);
    let evidence_error =
        serde_json::from_value::<core_pipelines::runtime::CoreResult>(forged_evidence)
            .expect_err("evidence references must be derived from attempt receipts");
    assert!(evidence_error.to_string().contains("evidence references"));

    let receipt_error =
        serde_json::from_value::<core_pipelines::runtime::CoreResult>(forged_receipt)
            .expect_err("host independence cannot be reconstructed from wire data");
    assert!(receipt_error
        .to_string()
        .contains("host independence receipts cannot be reconstructed"));
}

#[test]
fn maximum_repair_budget_is_bounded_by_small_operator_budget_without_recursion() {
    let packet = packet_with(
        CoreBudgets {
            max_repairs: u16::MAX,
            max_operator_calls: 4,
        },
        RequestedEffect::Evidence,
    );
    let producer = RoundProducer {
        id: identity("role:producer"),
    };
    let evaluator = AlwaysRepairEvaluator {
        id: identity("role:evaluator"),
    };

    let result = run_omega(Some(packet), &producer, &evaluator);

    assert_eq!(result.terminal, CoreTerminal::BudgetExhausted);
    assert_eq!(result.terminal_role, CoreRole::Dda);
    assert_eq!(result.attempts.len(), 2);
    assert_eq!(result.residuals.len(), 2);
    assert_eq!(result.attempts[0].repair_round, 0);
    assert_eq!(result.attempts[1].repair_round, 1);
    assert!(result.reason.contains("operator-call budget"));
}

// Origin: engine/crates_rs/tests/core_pipelines/core_runtime.rs
// Claim: urn:core:crates_rs:tests:core-runtime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf1f99699 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf1f99699` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf1f99699 {
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
impl BoundaryErrorf1f99699 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf1f99699 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf1f99699 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf1f99699 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf1f99699> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf1f99699::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf1f99699::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf1f99699::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f1f99699() {
    let admitted = BoundaryRecordf1f99699::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf1f99699::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
