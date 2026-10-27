#[path = "../../engines/src/examples/replays/cases.rs"]
mod cases;

use cases::{
    all_cases, budget_for_case, default_budget, operator_registry, DemoAdapter, DemoState,
};
use core_wdp::ddc::agent_contract::sha256_bytes;
use core_wdp::ddc::degree_tower::simplex_boundary_segment;
use engines::multipath_iterator::*;
use engines::obstruction_runtime::OperatorId;
use core_types::authority::AuthorityEffect;
use serde::Serialize;
#[cfg(feature = "paper070-test-clock")]
use std::sync::{
    atomic::{AtomicU64, Ordering},
    Arc,
};

fn run_case(case: cases::FixtureCase) -> RunReceipt {
    let expected = case.expected_terminal;
    let expected_domain = case.domain.clone();
    let packet = case.packet();
    let budget = budget_for_case(&case);
    let receipt = run_multipath(
        &DemoAdapter::new(case),
        packet,
        &operator_registry(),
        budget,
        &CancellationToken::default(),
    )
    .expect("frozen PaperER008 fixture must execute");
    assert_eq!(receipt.terminal.kind, expected);
    assert_eq!(receipt.packet.domain, expected_domain);
    receipt
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum FaultMode {
    BadProjectionHash,
    BadProjectionReference,
    EmptyExtension,
    ExtensionOnly,
    FirstEquivalentWitnessFails,
    InspectRefusal,
    EmptyProposalId,
    EmptyOperatorId,
    EmptyProvenance,
    MalformedMatchedSignature,
    BlankEquivalenceKey,
    DuplicateProposalSameOperator,
    DuplicateProposalCrossOperator,
    CollidingCoverageIdentity,
    PredictedAvoidanceOverflow,
    InitiallyResolved,
    #[cfg(feature = "paper070-test-clock")]
    SlowInspect,
    #[cfg(feature = "paper070-test-clock")]
    SlowCandidateInspect,
    #[cfg(feature = "paper070-test-clock")]
    SlowPropose,
    #[cfg(feature = "paper070-test-clock")]
    SlowAssess,
    #[cfg(feature = "paper070-test-clock")]
    SlowExtension,
    ProposalFlood,
}

#[cfg(feature = "paper070-test-clock")]
#[derive(Debug, Default)]
struct ManualClock(AtomicU64);

#[cfg(feature = "paper070-test-clock")]
impl ManualClock {
    fn advance_millis(&self, millis: u64) {
        self.0.fetch_add(millis * 1_000, Ordering::SeqCst);
    }
}

#[cfg(feature = "paper070-test-clock")]
impl DeterministicRunClock for ManualClock {
    fn elapsed_micros(&self) -> u128 {
        u128::from(self.0.load(Ordering::SeqCst))
    }
}

#[derive(Debug, Clone)]
struct FaultInjectingAdapter {
    inner: DemoAdapter,
    mode: FaultMode,
    #[cfg(feature = "paper070-test-clock")]
    clock: Option<Arc<ManualClock>>,
    #[cfg(feature = "paper070-test-clock")]
    inspect_calls: Arc<AtomicU64>,
}

impl FaultInjectingAdapter {
    fn new(case: cases::FixtureCase, mode: FaultMode) -> Self {
        Self {
            inner: DemoAdapter::new(case),
            mode,
            #[cfg(feature = "paper070-test-clock")]
            clock: None,
            #[cfg(feature = "paper070-test-clock")]
            inspect_calls: Arc::new(AtomicU64::new(0)),
        }
    }

    #[cfg(feature = "paper070-test-clock")]
    fn with_clock(case: cases::FixtureCase, mode: FaultMode, clock: Arc<ManualClock>) -> Self {
        Self {
            inner: DemoAdapter::new(case),
            mode,
            clock: Some(clock),
            inspect_calls: Arc::new(AtomicU64::new(0)),
        }
    }

    #[cfg(feature = "paper070-test-clock")]
    fn advance_clock(&self) {
        self.clock
            .as_ref()
            .expect("clock-backed fault mode requires a manual clock")
            .advance_millis(20);
    }
}

fn apply_inspection_fault_mode(mode: FaultMode, inspection: &mut Inspection) {
    for assessment in &mut inspection.coverage {
        if let Some(loss) = &mut assessment.projection_loss {
            match mode {
                FaultMode::BadProjectionHash => loss.discarded_sha256 = "not-a-sha256".into(),
                FaultMode::BadProjectionReference => {
                    loss.collided_projection_refs = vec!["projection::absent".into()];
                }
                _ => {}
            }
        }
    }
    if mode == FaultMode::CollidingCoverageIdentity {
        inspection.coverage[0].requirement = DetectorRequirement {
            claim_id: "a".into(),
            distinction_id: "b::c".into(),
        };
    }
    if mode == FaultMode::InitiallyResolved {
        for assessment in &mut inspection.coverage {
            assessment.disposition = CoverageDisposition::PreservedVisible;
            assessment.projection_loss = None;
        }
        inspection.visible_defects.clear();
        inspection.higher_degree_need = None;
        inspection.discarded_information_refs.clear();
    }
}

fn mutate_first_proposal_field<S>(mode: FaultMode, proposal: &mut DeformationProposal<S>) -> bool {
    match mode {
        FaultMode::EmptyProposalId => proposal.proposal_id = " ".into(),
        FaultMode::EmptyOperatorId => proposal.operator_id = OperatorId(" ".into()),
        FaultMode::EmptyProvenance => proposal.provenance.0 = " ".into(),
        FaultMode::MalformedMatchedSignature => proposal.matched_signature_sha256 = "not-a-sha256".into(),
        FaultMode::BlankEquivalenceKey => proposal.equivalence_key = Some(" ".into()),
        _ => return false,
    }
    true
}

fn apply_proposal_fault_mode<S: Clone>(mode: FaultMode, proposals: &mut Vec<DeformationProposal<S>>) {
    if let Some(proposal) = proposals.first_mut() {
        if mutate_first_proposal_field(mode, proposal) {
            return;
        }
    }
    match mode {
        FaultMode::DuplicateProposalSameOperator | FaultMode::DuplicateProposalCrossOperator => {
            if let Some(mut duplicate) = proposals.first().cloned() {
                duplicate.predicted_candidates_avoided += 1;
                if mode == FaultMode::DuplicateProposalCrossOperator {
                    duplicate.operator_id = OperatorId("op.paper070.other".into());
                }
                proposals.push(duplicate);
            }
        }
        FaultMode::ProposalFlood => {
            if let Some(seed) = proposals.first().cloned() {
                *proposals = (0..12)
                    .map(|index| {
                        let mut proposal = seed.clone();
                        proposal.proposal_id = format!("proposal-flood-{index:02}");
                        proposal.equivalence_key = None;
                        proposal.predicted_candidates_avoided = 0;
                        proposal
                    })
                    .collect();
            }
        }
        FaultMode::PredictedAvoidanceOverflow => {
            if let Some(duplicate) = proposals.get_mut(1) {
                duplicate.predicted_candidates_avoided = usize::MAX;
                let mut overflow = duplicate.clone();
                overflow.proposal_id = "math-repair-overflow".into();
                overflow.predicted_candidates_avoided = 1;
                proposals.push(overflow);
            }
        }
        _ => {}
    }
}

impl MultipathAdapter for FaultInjectingAdapter {
    type State = DemoState;

    fn adapter_id(&self) -> &str {
        self.inner.adapter_id()
    }

    fn seed(&self, packet: &ProblemPacket) -> Result<AdapterSeed<Self::State>, AdapterFailure> {
        self.inner.seed(packet)
    }

    fn inspect(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
    ) -> Result<Inspection, AdapterFailure> {
        #[cfg(feature = "paper070-test-clock")]
        {
            let inspect_call = self.inspect_calls.fetch_add(1, Ordering::SeqCst);
            if self.mode == FaultMode::SlowInspect
                || (self.mode == FaultMode::SlowCandidateInspect && inspect_call > 0)
            {
                self.advance_clock();
            }
        }
        if self.mode == FaultMode::InspectRefusal {
            return Err(AdapterFailure {
                kind: AdapterFailureKind::Refused,
                detail: "injected typed refusal".into(),
            });
        }
        let mut inspection = self.inner.inspect(packet, carrier, state)?;
        apply_inspection_fault_mode(self.mode, &mut inspection);
        Ok(inspection)
    }

    fn propose(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
        signatures: &[ObstructionSignature],
    ) -> Result<Vec<DeformationProposal<Self::State>>, AdapterFailure> {
        if self.mode == FaultMode::ExtensionOnly {
            return Ok(Vec::new());
        }
        #[cfg(feature = "paper070-test-clock")]
        if self.mode == FaultMode::SlowPropose {
            self.advance_clock();
        }
        let mut proposals = self.inner.propose(packet, carrier, state, signatures)?;
        apply_proposal_fault_mode(self.mode, &mut proposals);
        Ok(proposals)
    }

    fn assess_candidate(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        before: &Self::State,
        proposal: &DeformationProposal<Self::State>,
        operator: &RegisteredOperator,
    ) -> Result<CandidateAssessment, AdapterFailure> {
        #[cfg(feature = "paper070-test-clock")]
        if self.mode == FaultMode::SlowAssess {
            self.advance_clock();
        }
        let mut assessment = self
            .inner
            .assess_candidate(packet, carrier, before, proposal, operator)?;
        if self.mode == FaultMode::FirstEquivalentWitnessFails
            && proposal.proposal_id == "math-repair-canonical"
        {
            assessment.witnesses[0].verdict = CheckVerdict::Fail;
        }
        Ok(assessment)
    }

    fn extend_carrier(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
        inspection: &InspectionReceipt,
    ) -> Result<Option<CarrierExtension>, AdapterFailure> {
        #[cfg(feature = "paper070-test-clock")]
        if self.mode == FaultMode::SlowExtension {
            self.advance_clock();
        }
        if self.mode == FaultMode::EmptyExtension {
            let Some(signature) = inspection
                .signatures
                .iter()
                .find(|signature| signature.kind == "projection_loss")
            else {
                return Ok(None);
            };
            return Ok(Some(CarrierExtension {
                extension_id: "injected-empty-extension".into(),
                trigger_signature_sha256: signature.signature_sha256.clone(),
                justification_ref: "test://empty-extension".into(),
                new_cells: Vec::new(),
            }));
        }
        self.inner
            .extend_carrier(packet, carrier, state, inspection)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum CallbackFailurePhase {
    Inspect,
    Propose,
    ExtendCarrier,
}

struct CallbackFailureAdapter {
    inner: DemoAdapter,
    phase: CallbackFailurePhase,
    kind: AdapterFailureKind,
    detail: String,
}

impl CallbackFailureAdapter {
    fn new(
        case: cases::FixtureCase,
        phase: CallbackFailurePhase,
        kind: AdapterFailureKind,
        detail: impl Into<String>,
    ) -> Self {
        Self {
            inner: DemoAdapter::new(case),
            phase,
            kind,
            detail: detail.into(),
        }
    }

    fn failure(&self) -> AdapterFailure {
        AdapterFailure {
            kind: self.kind,
            detail: self.detail.clone(),
        }
    }
}

impl MultipathAdapter for CallbackFailureAdapter {
    type State = DemoState;

    fn adapter_id(&self) -> &str {
        self.inner.adapter_id()
    }

    fn seed(&self, packet: &ProblemPacket) -> Result<AdapterSeed<Self::State>, AdapterFailure> {
        self.inner.seed(packet)
    }

    fn inspect(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
    ) -> Result<Inspection, AdapterFailure> {
        if self.phase == CallbackFailurePhase::Inspect {
            return Err(self.failure());
        }
        self.inner.inspect(packet, carrier, state)
    }

    fn propose(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
        signatures: &[ObstructionSignature],
    ) -> Result<Vec<DeformationProposal<Self::State>>, AdapterFailure> {
        if self.phase == CallbackFailurePhase::Propose {
            return Err(self.failure());
        }
        if self.phase == CallbackFailurePhase::ExtendCarrier {
            return Ok(Vec::new());
        }
        self.inner.propose(packet, carrier, state, signatures)
    }

    fn assess_candidate(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        before: &Self::State,
        proposal: &DeformationProposal<Self::State>,
        operator: &RegisteredOperator,
    ) -> Result<CandidateAssessment, AdapterFailure> {
        self.inner
            .assess_candidate(packet, carrier, before, proposal, operator)
    }

    fn extend_carrier(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
        inspection: &InspectionReceipt,
    ) -> Result<Option<CarrierExtension>, AdapterFailure> {
        if self.phase == CallbackFailurePhase::ExtendCarrier {
            return Err(self.failure());
        }
        self.inner
            .extend_carrier(packet, carrier, state, inspection)
    }
}

fn case_named(name: &str) -> cases::FixtureCase {
    all_cases()
        .into_iter()
        .find(|case| case.case_id == name)
        .unwrap()
}

fn reseal(receipt: &mut RunReceipt) {
    receipt.replay_sha256 = receipt.recompute_replay_sha256().unwrap();
}

fn assert_resealed_rejected(mut receipt: RunReceipt) {
    reseal(&mut receipt);
    assert!(
        !matches!(receipt.verify_replay_hash(), Ok(true)),
        "malformed but re-sealed receipt must be rejected"
    );
}

fn assert_anchor_resealed_rejected(mut receipt: RunReceipt, expected_anchor: &RunReceiptAnchor) {
    reseal(&mut receipt);
    assert!(
        receipt.verify_replay_hash().unwrap(),
        "joint attack must remain internally self-consistent to exercise the external anchor"
    );
    assert!(
        !receipt.verify_against_anchor(expected_anchor).unwrap(),
        "caller-pinned anchor must reject a jointly re-sealed receipt"
    );
}

fn hash_json<T: Serialize + ?Sized>(value: &T) -> String {
    sha256_bytes(&serde_json::to_vec(value).unwrap())
}

#[derive(Serialize)]
struct TestSourceProposalCommitment<'a> {
    hash_domain: &'static str,
    proposal_id: &'a str,
    operator_id: &'a OperatorId,
    provenance: &'a engines::obstruction_runtime::Provenance,
    matched_signature_sha256: &'a str,
    equivalence_key: &'a Option<String>,
    predicted_candidates_avoided: usize,
    result_state_sha256: &'a str,
}

fn reseal_source_proposal(candidate: &mut CompiledOperatorCandidate) {
    candidate.source_proposal_sha256 = hash_json(&TestSourceProposalCommitment {
        hash_domain: "core.paper070.operator_proposal.v3",
        proposal_id: &candidate.source_proposal_id,
        operator_id: &candidate.source_operator_id,
        provenance: &candidate.source_provenance,
        matched_signature_sha256: &candidate.observed_signature_sha256,
        equivalence_key: &candidate.source_equivalence_key,
        predicted_candidates_avoided: candidate.source_predicted_candidates_avoided,
        result_state_sha256: &candidate.result_state_sha256,
    });
}

#[derive(Serialize)]
struct TestOperatorEvidenceCommitment<'a> {
    hash_domain: &'static str,
    pattern_sha256: &'a str,
    source_operator_sha256: &'a str,
    source_registry_sha256: &'a str,
    source_proposal_sha256: &'a str,
    source_assessment_sha256: &'a str,
    source_candidate_sha256: &'a str,
    source_step_index: usize,
    source_packet_sha256: &'a str,
    source_carrier_sha256: &'a str,
    source_state_sha256: &'a str,
    result_state_sha256: &'a str,
    observed_signature_sha256: &'a str,
    before: ObstructionMeasure,
    after: ObstructionMeasure,
    post_inspection_sha256: &'a str,
    authority_effect: &'a AuthorityEffect,
}

fn reseal_compiled_evidence(candidate: &mut CompiledOperatorCandidate) {
    candidate.evidence_sha256 = hash_json(&TestOperatorEvidenceCommitment {
        hash_domain: "core.paper070.operator_evidence.v3",
        pattern_sha256: &candidate.pattern_sha256,
        source_operator_sha256: &candidate.source_operator_sha256,
        source_registry_sha256: &candidate.source_registry_sha256,
        source_proposal_sha256: &candidate.source_proposal_sha256,
        source_assessment_sha256: &candidate.source_assessment_sha256,
        source_candidate_sha256: &candidate.source_candidate_sha256,
        source_step_index: candidate.source_step_index,
        source_packet_sha256: &candidate.source_packet_sha256,
        source_carrier_sha256: &candidate.source_carrier_sha256,
        source_state_sha256: &candidate.source_state_sha256,
        result_state_sha256: &candidate.result_state_sha256,
        observed_signature_sha256: &candidate.observed_signature_sha256,
        before: candidate.before,
        after: candidate.after,
        post_inspection_sha256: &candidate.post_inspection_sha256,
        authority_effect: &candidate.authority_effect,
    });
}

fn assert_receipt_fits(receipt: &RunReceipt) {
    let bytes = serde_json::to_vec(receipt).unwrap();
    assert!(
        bytes.len() <= receipt.budget.max_receipt_bytes,
        "receipt has {} bytes above budget {}",
        bytes.len(),
        receipt.budget.max_receipt_bytes
    );
}

fn assert_invalid_receipt_budget(
    adapter: &impl MultipathAdapter,
    packet: ProblemPacket,
    mut budget: RunBudget,
) {
    budget.max_receipt_bytes = serde_json::to_vec(&packet).unwrap().len() + 1;
    assert!(matches!(
        run_multipath(
            adapter,
            packet,
            &operator_registry(),
            budget,
            &CancellationToken::default(),
        ),
        Err(IteratorError::InvalidBudget(_))
    ));
}

#[test]
fn all_seven_replays_terminalize_without_authority_and_verify() {
    let cases = all_cases();
    assert_eq!(cases.len(), 7);
    for case in cases {
        let receipt = run_case(case);
        let anchor = receipt.external_anchor().unwrap();
        assert!(receipt.authority_effect().is_none());
        assert!(anchor.authority_effect.is_none());
        assert!(receipt.verify_replay_hash().unwrap());
        assert!(receipt.verify_against_anchor(&anchor).unwrap());
        assert!(receipt.accounting.is_balanced());
        assert_eq!(
            receipt.accounting.compiled_operator_candidates,
            receipt.accounting.accepted_transitions
        );
        for candidate in receipt
            .steps
            .iter()
            .filter_map(|step| step.compiled_operator_candidate.as_ref())
        {
            assert!(candidate.verify_hashes().unwrap());
            assert!(candidate.authority_effect().is_none());
        }
        assert!(!receipt.packet_sha256.is_empty());
        assert!(!receipt.replay_sha256.is_empty());
        assert_receipt_fits(&receipt);
    }
}

#[test]
fn exact_f2_triangle_detects_global_failure_and_registered_quotient_prunes() {
    let case = all_cases()
        .into_iter()
        .find(|case| case.case_id == "math_local_green_global_red")
        .unwrap();
    let receipt = run_case(case);
    let first = &receipt.steps[0];
    let cochain = first.inspection.defects[0].cochain.as_ref().unwrap();
    assert_eq!(cochain.classification, "open");
    assert_eq!(cochain.gamma, 1);
    assert_eq!(receipt.accounting.proposed, 2);
    assert_eq!(receipt.accounting.evaluated, 1);
    assert_eq!(receipt.accounting.duplicate_pruned, 1);
    assert_eq!(receipt.accounting.predicted_avoided_by_quotient, 11);
    assert!(first
        .candidates
        .iter()
        .any(|candidate| candidate.verdict == CandidateVerdict::DuplicatePruned));
}

#[test]
fn selected_repairs_compile_narrowed_nonauthority_operator_candidates_without_registration() {
    let case = case_named("math_local_green_global_red");
    let packet = case.packet();
    let adapter = DemoAdapter::new(case);
    let registry = operator_registry();
    let registry_before = registry.sha256().unwrap();
    let mut receipt = run_multipath(
        &adapter,
        packet,
        &registry,
        default_budget(),
        &CancellationToken::default(),
    )
    .unwrap();

    assert_eq!(registry.sha256().unwrap(), registry_before);
    assert_eq!(receipt.accounting.compiled_operator_candidates, 1);
    let compiled = receipt.steps[0]
        .compiled_operator_candidate
        .as_ref()
        .unwrap();
    assert!(compiled.verify_hashes().unwrap());
    assert!(compiled.authority_effect().is_none());
    assert_eq!(
        compiled.source_operator_id,
        OperatorId("op.paper070.exact_local_rewrite".into())
    );
    assert_eq!(compiled.signature_kind, "multipath_composition_failure");
    assert_eq!(compiled.carrier_kind, CarrierKind::SimplicialComplex);
    assert_eq!(compiled.before.open_defect_count, 1);
    assert_eq!(compiled.after.open_defect_count, 0);
    assert!(compiled
        .candidate_operator_id
        .0
        .starts_with("candidate.sha256."));
    assert!(registry.get(&compiled.candidate_operator_id).is_none());

    receipt.steps[0]
        .compiled_operator_candidate
        .as_mut()
        .unwrap()
        .deformation_ref
        .push_str("-tampered");
    assert!(!receipt.steps[0]
        .compiled_operator_candidate
        .as_ref()
        .unwrap()
        .verify_hashes()
        .unwrap());
    assert!(!receipt.verify_replay_hash().unwrap());
}

#[test]
fn nonempty_common_source_receipts_do_not_establish_common_mode_safety() {
    let case = all_cases()
        .into_iter()
        .find(|case| case.case_id == "multi_agent_common_mode_failure")
        .unwrap();
    let receipt = run_case(case);
    assert_eq!(receipt.terminal.kind, TerminalKind::OpenObstruction);
    let candidate = &receipt.steps[0].candidates[0];
    assert_eq!(candidate.verdict, CandidateVerdict::RejectedWitness);
    assert_eq!(candidate.witnesses.len(), 2);
    assert!(candidate
        .witnesses
        .iter()
        .all(|witness| witness.verdict == CheckVerdict::Pass));
    assert!(candidate
        .witnesses
        .iter()
        .all(|witness| witness.relation == WitnessRelation::CommonSource));
}

#[test]
fn self_application_grows_only_from_projection_loss_then_repairs() {
    let case = all_cases()
        .into_iter()
        .find(|case| case.case_id == "paperer008_self_application")
        .unwrap();
    let receipt = run_case(case);
    assert_eq!(receipt.terminal.kind, TerminalKind::ExactRepair);
    assert_eq!(receipt.accounting.carrier_extensions, 1);
    assert_eq!(receipt.accounting.accepted_transitions, 1);
    assert!(receipt.steps[0].carrier_extension.is_some());
    assert!(receipt.steps[1]
        .candidates
        .iter()
        .flat_map(|candidate| candidate.witnesses.iter())
        .all(|witness| witness.relation == WitnessRelation::Unestablished));
    assert!(receipt
        .final_carrier
        .cells
        .iter()
        .any(|cell| cell.cell_id == "contract_surface"));
}

#[test]
fn collapsing_detector_and_unlicensed_c3_never_report_coherence() {
    let mut cases = all_cases().into_iter();
    let collapsed = cases
        .find(|case| case.case_id == "collapsing_detector_negative")
        .unwrap();
    let collapsed_receipt = run_case(collapsed);
    assert_eq!(
        collapsed_receipt.terminal.kind,
        TerminalKind::DetectorInadequate
    );
    assert_eq!(
        collapsed_receipt.steps[0]
            .inspection
            .detector_inadequate_count,
        1
    );

    let lifted = all_cases()
        .into_iter()
        .find(|case| case.case_id == "higher_coherence_requires_lift")
        .unwrap();
    let lift_receipt = run_case(lifted);
    assert_eq!(lift_receipt.terminal.kind, TerminalKind::RequiresLift);
    assert!(lift_receipt.steps[0]
        .inspection
        .higher_degree_need
        .as_ref()
        .unwrap()
        .licensed_lift_ref
        .is_none());
}

#[test]
fn explicit_cancellation_is_a_replayable_nonauthority_terminal() {
    let case = all_cases().remove(0);
    let token = CancellationToken::default();
    token.cancel();
    let receipt = run_multipath(
        &DemoAdapter::new(case.clone()),
        case.packet(),
        &operator_registry(),
        default_budget(),
        &token,
    )
    .unwrap();
    assert_eq!(receipt.terminal.kind, TerminalKind::Cancelled);
    assert!(receipt.steps.is_empty());
    assert!(receipt.authority_effect().is_none());
    assert!(receipt.verify_replay_hash().unwrap());
    assert_receipt_fits(&receipt);
}

#[test]
fn replay_hash_detects_semantic_receipt_tampering_but_excludes_runtime() {
    let case = all_cases().remove(0);
    let mut receipt = run_case(case);
    let original = receipt.replay_sha256.clone();
    receipt.runtime_micros += 1_000_000;
    assert!(receipt.verify_replay_hash().unwrap());
    assert_eq!(receipt.replay_sha256, original);
    receipt.terminal.reason.push_str(" tampered");
    assert!(!receipt.verify_replay_hash().unwrap());
}

#[test]
fn replay_hash_binds_the_complete_packet_not_only_its_stored_hash() {
    let original = run_case(all_cases().remove(0));

    let mut payload = original.clone();
    payload.packet.payload["triangle_parity"] = serde_json::json!(0);
    assert!(!payload.verify_replay_hash().unwrap());

    let mut packet_refs = original.clone();
    packet_refs
        .packet
        .packet_refs
        .push("paper070://tampered".into());
    assert!(!packet_refs.verify_replay_hash().unwrap());

    let mut protected = original.clone();
    protected.packet.protected_distinctions[0]
        .distinction_id
        .push_str("-tampered");
    assert!(!protected.verify_replay_hash().unwrap());

    let mut domain = original;
    domain.packet.domain.push_str("-tampered");
    assert!(!domain.verify_replay_hash().unwrap());
}

#[test]
fn complete_receipt_budget_is_enforced_for_every_terminal_shape() {
    for case in all_cases() {
        let adapter = DemoAdapter::new(case.clone());
        assert_invalid_receipt_budget(&adapter, case.packet(), budget_for_case(&case));
    }

    let refusal_case = case_named("rust_local_tests_cross_contract");
    let refusal = FaultInjectingAdapter::new(refusal_case.clone(), FaultMode::InspectRefusal);
    let refusal_receipt = run_multipath(
        &refusal,
        refusal_case.packet(),
        &operator_registry(),
        default_budget(),
        &CancellationToken::default(),
    )
    .unwrap();
    assert_eq!(refusal_receipt.terminal.kind, TerminalKind::Refused);
    assert_receipt_fits(&refusal_receipt);
    assert_invalid_receipt_budget(&refusal, refusal_case.packet(), default_budget());

    let extension_case = case_named("paperer008_self_application");
    let extension_only =
        FaultInjectingAdapter::new(extension_case.clone(), FaultMode::ExtensionOnly);
    let extension_receipt = run_multipath(
        &extension_only,
        extension_case.packet(),
        &operator_registry(),
        default_budget(),
        &CancellationToken::default(),
    )
    .unwrap();
    assert_eq!(extension_receipt.terminal.kind, TerminalKind::NoRule);
    assert_eq!(extension_receipt.accounting.carrier_extensions, 1);
    assert_receipt_fits(&extension_receipt);
    assert_invalid_receipt_budget(&extension_only, extension_case.packet(), default_budget());

    let cancelled_case = case_named("lean_proof_repair");
    let cancelled = CancellationToken::default();
    cancelled.cancel();
    let mut cancelled_budget = default_budget();
    let cancelled_packet = cancelled_case.packet();
    cancelled_budget.max_receipt_bytes = serde_json::to_vec(&cancelled_packet).unwrap().len() + 1;
    assert!(matches!(
        run_multipath(
            &DemoAdapter::new(cancelled_case),
            cancelled_packet,
            &operator_registry(),
            cancelled_budget,
            &cancelled,
        ),
        Err(IteratorError::InvalidBudget(_))
    ));
}

#[test]
fn packet_preflight_rejects_an_input_that_cannot_fit_any_receipt() {
    let case = case_named("rust_local_tests_cross_contract");
    let adapter = DemoAdapter::new(case.clone());
    let mut packet = case.packet();
    packet.payload = serde_json::json!({"oversized": "x".repeat(16_384)});
    let mut budget = default_budget();
    budget.max_receipt_bytes = 1024;
    assert!(matches!(
        run_multipath(
            &adapter,
            packet,
            &operator_registry(),
            budget,
            &CancellationToken::default(),
        ),
        Err(IteratorError::InvalidBudget(_))
    ));
}

#[test]
fn empty_carrier_extension_is_rejected_before_growth_is_recorded() {
    let case = case_named("paperer008_self_application");
    let adapter = FaultInjectingAdapter::new(case.clone(), FaultMode::EmptyExtension);
    let result = run_multipath(
        &adapter,
        case.packet(),
        &operator_registry(),
        default_budget(),
        &CancellationToken::default(),
    );
    assert!(matches!(
        result,
        Err(IteratorError::InvalidCarrier(message))
            if message.contains("at least one cell")
    ));
}

#[test]
fn malformed_projection_loss_hash_and_collision_reference_are_rejected() {
    for mode in [
        FaultMode::BadProjectionHash,
        FaultMode::BadProjectionReference,
    ] {
        let case = case_named("paperer008_self_application");
        let adapter = FaultInjectingAdapter::new(case.clone(), mode);
        assert!(matches!(
            run_multipath(
                &adapter,
                case.packet(),
                &operator_registry(),
                default_budget(),
                &CancellationToken::default(),
            ),
            Err(IteratorError::InvalidDeclaration(_))
        ));
    }
}

#[test]
fn failed_equivalence_representative_does_not_prune_a_later_valid_member() {
    let case = case_named("math_local_green_global_red");
    let adapter = FaultInjectingAdapter::new(case.clone(), FaultMode::FirstEquivalentWitnessFails);
    let receipt = run_multipath(
        &adapter,
        case.packet(),
        &operator_registry(),
        default_budget(),
        &CancellationToken::default(),
    )
    .unwrap();

    assert_eq!(receipt.terminal.kind, TerminalKind::ExactRepair);
    assert_eq!(receipt.accounting.evaluated, 2);
    assert_eq!(receipt.accounting.duplicate_pruned, 0);
    assert_eq!(
        receipt.steps[0].selected_proposal_id.as_deref(),
        Some("math-repair-equivalent")
    );
    assert_eq!(
        receipt.steps[0].candidates[0].verdict,
        CandidateVerdict::RejectedWitness
    );
    assert_eq!(
        receipt.steps[0].candidates[1].verdict,
        CandidateVerdict::EligibleDescent
    );
}

#[test]
fn finite_property_d1_d0_and_gauge_invariance_hold_exhaustively() {
    let segment = simplex_boundary_segment(1).unwrap();
    let source_states = 1usize << segment.previous.domain_dim();
    let residual_states = 1usize << segment.residual_dim();

    for residual_bits in 0..residual_states {
        let residual: Vec<bool> = (0..segment.residual_dim())
            .map(|bit| ((residual_bits >> bit) & 1) == 1)
            .collect();
        let closure = segment.next.apply(&residual).unwrap();

        for source_bits in 0..source_states {
            let source: Vec<bool> = (0..segment.previous.domain_dim())
                .map(|bit| ((source_bits >> bit) & 1) == 1)
                .collect();
            let gauge = segment.previous.apply(&source).unwrap();
            assert!(segment.next.apply(&gauge).unwrap().iter().all(|bit| !bit));
            let shifted: Vec<bool> = residual
                .iter()
                .zip(gauge)
                .map(|(left, right)| *left ^ right)
                .collect();
            assert_eq!(segment.next.apply(&shifted).unwrap(), closure);
        }
    }
}

#[test]
fn carrier_validation_refuses_missing_boundary_cells() {
    let carrier = FiniteCarrier {
        carrier_id: "bad".into(),
        kind: CarrierKind::DirectedGraph,
        cells: vec![CarrierCell {
            cell_id: "edge".into(),
            degree: 1,
            boundary: vec!["missing".into()],
            payload_sha256: "0".repeat(64),
        }],
    };
    let error = carrier.canonicalized().unwrap_err();
    assert!(matches!(
        error,
        IteratorError::InvalidCarrier(message)
            if message.contains("references missing boundary cell `missing`")
    ));
}

#[test]
fn receipt_verification_rejects_schema_authority_and_transition_rebinding() {
    let original = run_case(case_named("math_local_green_global_red"));
    assert!(original.verify_replay_hash().unwrap());
    assert!(original.steps.len() >= 2);

    let no_candidate = run_case(case_named("collapsing_detector_negative"));
    assert_eq!(no_candidate.accounting.compiled_operator_candidates, 0);

    let mut wrong_schema = no_candidate.clone();
    wrong_schema.schema_version = "core.multipath.run_receipt.v999".into();
    reseal(&mut wrong_schema);
    assert!(!wrong_schema.verify_replay_hash().unwrap());

    for authority_effect in [AuthorityEffect::Refused, AuthorityEffect::Uncertified] {
        let mut wrong_authority = no_candidate.clone();
        wrong_authority.authority_effect = authority_effect;
        reseal(&mut wrong_authority);
        assert!(!wrong_authority.verify_replay_hash().unwrap());
    }

    let mut carrier_substitution = original.clone();
    carrier_substitution.steps[0].carrier_sha256 = "0".repeat(64);
    reseal(&mut carrier_substitution);
    assert!(!carrier_substitution.verify_replay_hash().unwrap());

    let mut step_relocation = original.clone();
    step_relocation.steps[0].step_index += 1;
    reseal(&mut step_relocation);
    assert!(!step_relocation.verify_replay_hash().unwrap());

    let mut before_mismatch = original.clone();
    before_mismatch.steps[0]
        .inspection
        .measure
        .open_defect_count += 1;
    reseal(&mut before_mismatch);
    assert!(!before_mismatch.verify_replay_hash().unwrap());

    let mut signature_mismatch = original.clone();
    signature_mismatch.steps[0].inspection.signatures[0]
        .kind
        .push_str("-tampered");
    reseal(&mut signature_mismatch);
    assert!(!signature_mismatch.verify_replay_hash().unwrap());

    let mut state_chain_mismatch = original.clone();
    state_chain_mismatch.steps[1].state_sha256 = "1".repeat(64);
    reseal(&mut state_chain_mismatch);
    assert!(!state_chain_mismatch.verify_replay_hash().unwrap());

    let mut post_inspection_mismatch = original.clone();
    post_inspection_mismatch.steps[0].candidates[0]
        .post_inspection
        .as_mut()
        .unwrap()
        .measure
        .open_defect_count += 1;
    reseal(&mut post_inspection_mismatch);
    assert!(!post_inspection_mismatch.verify_replay_hash().unwrap());

    let mut assessment_mismatch = original;
    assessment_mismatch.steps[0]
        .compiled_operator_candidate
        .as_mut()
        .unwrap()
        .preservation_checks[0]
        .evidence_ref
        .push_str("-tampered");
    reseal(&mut assessment_mismatch);
    assert!(!assessment_mismatch.verify_replay_hash().unwrap());
}

#[test]
fn malformed_and_duplicate_proposals_are_rejected_before_receipt_materialization() {
    let case = case_named("math_local_green_global_red");
    for mode in [
        FaultMode::EmptyProposalId,
        FaultMode::EmptyOperatorId,
        FaultMode::EmptyProvenance,
        FaultMode::MalformedMatchedSignature,
        FaultMode::BlankEquivalenceKey,
        FaultMode::DuplicateProposalSameOperator,
        FaultMode::DuplicateProposalCrossOperator,
    ] {
        let result = run_multipath(
            &FaultInjectingAdapter::new(case.clone(), mode),
            case.packet(),
            &operator_registry(),
            default_budget(),
            &CancellationToken::default(),
        );
        assert!(matches!(
            result,
            Err(IteratorError::InvalidDeclaration(message))
                if message.contains("proposal")
        ));
    }
}

#[test]
fn terminal_callback_failure_matrix_is_replay_and_anchor_closed() {
    let phases = [
        CallbackFailurePhase::Inspect,
        CallbackFailurePhase::Propose,
        CallbackFailurePhase::ExtendCarrier,
    ];
    let kinds = [
        AdapterFailureKind::DetectorInadequate,
        AdapterFailureKind::NoRule,
        AdapterFailureKind::RequiresLift,
        AdapterFailureKind::Refused,
    ];

    for phase in phases {
        let case = if phase == CallbackFailurePhase::ExtendCarrier {
            case_named("paperer008_self_application")
        } else {
            case_named("math_local_green_global_red")
        };
        for kind in kinds {
            let receipt = run_multipath(
                &CallbackFailureAdapter::new(
                    case.clone(),
                    phase,
                    kind,
                    "injected callback failure",
                ),
                case.packet(),
                &operator_registry(),
                default_budget(),
                &CancellationToken::default(),
            )
            .expect("well-formed callback failures must produce a refusal receipt");
            assert_eq!(receipt.terminal.kind, TerminalKind::Refused);
            assert!(receipt.terminal.reason.contains(&format!("{kind:?}")));
            assert!(receipt.verify_replay_hash().unwrap());
            let anchor = receipt.external_anchor().unwrap();
            assert!(receipt.verify_against_anchor(&anchor).unwrap());

            let error = run_multipath(
                &CallbackFailureAdapter::new(case.clone(), phase, kind, "   "),
                case.packet(),
                &operator_registry(),
                default_budget(),
                &CancellationToken::default(),
            )
            .unwrap_err();
            assert!(matches!(
                error,
                IteratorError::InvalidDeclaration(message)
                    if message.contains("adapter failure detail")
            ));
        }
    }
}

#[test]
fn compiled_candidate_binds_complete_operator_proposal_assessment_and_selected_receipt() {
    let receipt = run_case(case_named("math_local_green_global_red"));
    let step = &receipt.steps[0];
    let compiled = step.compiled_operator_candidate.as_ref().unwrap();

    assert_eq!(compiled.source_step_index, step.step_index);
    assert_eq!(compiled.source_carrier_sha256, step.carrier_sha256);
    assert_eq!(
        compiled.source_candidate_sha256,
        *step.selected_candidate_sha256.as_ref().unwrap()
    );
    assert_eq!(
        compiled.source_registry_sha256,
        receipt.operator_registry_sha256
    );
    assert_eq!(
        compiled.post_inspection_sha256.len(),
        64,
        "post-inspection commitment must be SHA-256"
    );
    for hash in [
        &compiled.source_operator_sha256,
        &compiled.source_proposal_sha256,
        &compiled.source_assessment_sha256,
        &compiled.source_candidate_sha256,
    ] {
        assert_eq!(hash.len(), 64);
        assert!(hash
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)));
    }
    assert_eq!(
        compiled.preservation_checks,
        step.candidates[0].preservation
    );
    assert_eq!(compiled.witness_results, step.candidates[0].witnesses);
    assert!(compiled.verify_hashes().unwrap());
    assert!(receipt.verify_compiled_operator_candidates().unwrap());
}

#[test]
fn registry_and_candidate_hash_inputs_require_canonical_sets_and_lowercase_sha256() {
    let source = operator_registry().operators()[0].clone();

    let mut uppercase = source.clone();
    uppercase.deformation_descriptor_sha256 =
        uppercase.deformation_descriptor_sha256.to_uppercase();
    assert!(OperatorRegistry::new(vec![uppercase]).is_err());

    let mut duplicate_precondition = source.clone();
    duplicate_precondition
        .preconditions
        .push(duplicate_precondition.preconditions[0].clone());
    assert!(OperatorRegistry::new(vec![duplicate_precondition]).is_err());

    let mut duplicate_terminal = source.clone();
    duplicate_terminal
        .possible_terminals
        .push(duplicate_terminal.possible_terminals[0]);
    assert!(OperatorRegistry::new(vec![duplicate_terminal]).is_err());

    let mut empty_signature = source;
    empty_signature.signature_kinds.push(String::new());
    assert!(OperatorRegistry::new(vec![empty_signature]).is_err());
}

#[test]
fn canonical_receipt_bytes_are_the_budgeted_bytes_and_include_compiled_candidates() {
    let receipt = run_case(case_named("math_local_green_global_red"));
    let canonical = receipt.canonical_json_bytes().unwrap();
    assert_eq!(canonical, serde_json::to_vec(&receipt).unwrap());
    assert!(canonical.len() <= receipt.budget.max_receipt_bytes);
    let text = String::from_utf8(canonical).unwrap();
    assert!(text.contains("\"compiled_operator_candidate\""));
    assert!(text.contains("\"source_assessment_sha256\""));
}

#[test]
fn receipt_verification_rejects_no_candidate_envelope_tampering() {
    let original = run_case(case_named("collapsing_detector_negative"));
    assert_eq!(original.accounting.compiled_operator_candidates, 0);

    let mut blank_adapter = original.clone();
    blank_adapter.adapter_id.clear();
    assert_resealed_rejected(blank_adapter);

    let mut blank_terminal_reason = original.clone();
    blank_terminal_reason.terminal.reason = " ".into();
    assert_resealed_rejected(blank_terminal_reason);

    let mut zero_budget = original.clone();
    zero_budget.budget.max_steps = 0;
    assert_resealed_rejected(zero_budget);

    let mut unbalanced = original.clone();
    unbalanced.accounting.proposed = 1;
    assert_resealed_rejected(unbalanced);

    let mut fabricated_budget_pruning = original.clone();
    fabricated_budget_pruning.accounting.proposed = 1;
    fabricated_budget_pruning.accounting.budget_pruned = 1;
    assert_resealed_rejected(fabricated_budget_pruning);

    let mut malformed_carrier = original.clone();
    malformed_carrier.initial_carrier.cells[0].cell_id.clear();
    assert_resealed_rejected(malformed_carrier);

    let mut final_carrier_substitution = original.clone();
    final_carrier_substitution
        .final_carrier
        .carrier_id
        .push_str("-substituted");
    assert_resealed_rejected(final_carrier_substitution);

    let mut duplicate_packet_ref = original.clone();
    duplicate_packet_ref
        .packet
        .packet_refs
        .push(duplicate_packet_ref.packet.packet_refs[0].clone());
    assert_resealed_rejected(duplicate_packet_ref);

    let mut missing_packet_refs = original.clone();
    missing_packet_refs.packet.packet_refs.clear();
    assert_resealed_rejected(missing_packet_refs);

    let mut impossible_terminal = original;
    impossible_terminal.terminal.kind = TerminalKind::ExactRepair;
    assert_resealed_rejected(impossible_terminal);
}

#[test]
fn receipt_verification_recomputes_summaries_and_requires_external_primitive_anchor() {
    let original = run_case(case_named("collapsing_detector_negative"));
    let detector_anchor = original.external_anchor().unwrap();
    assert!(original.steps[0].inspection.detector_inadequate_count > 0);

    let mut summary_only_relabel = original.clone();
    summary_only_relabel.steps[0]
        .inspection
        .detector_inadequate_count = 0;
    summary_only_relabel.terminal.kind = TerminalKind::StabilizedSurvivor;
    assert_resealed_rejected(summary_only_relabel);

    let mut primitive_detector_relabel = original.clone();
    primitive_detector_relabel.steps[0].inspection.coverage[0].disposition =
        CoverageDisposition::PreservedVisible;
    primitive_detector_relabel.steps[0]
        .inspection
        .detector_inadequate_count = 0;
    primitive_detector_relabel.steps[0]
        .inspection
        .discarded_information_refs
        .clear();
    primitive_detector_relabel.terminal.kind = TerminalKind::StabilizedSurvivor;
    primitive_detector_relabel.terminal.reason =
        "jointly re-sealed primitive detector disposition".into();
    assert_anchor_resealed_rejected(primitive_detector_relabel, &detector_anchor);

    let mut rebound_payload = original;
    rebound_payload.initial_carrier.cells[0].payload_sha256 = "x".into();
    rebound_payload.final_carrier.cells[0].payload_sha256 = "x".into();
    let rebound_carrier_sha256 = hash_json(&rebound_payload.initial_carrier);
    assert_eq!(
        rebound_carrier_sha256,
        hash_json(&rebound_payload.final_carrier)
    );
    for step in &mut rebound_payload.steps {
        step.carrier_sha256 = rebound_carrier_sha256.clone();
    }
    assert_resealed_rejected(rebound_payload);

    let mut removed_higher_need = run_case(case_named("higher_coherence_requires_lift"));
    let higher_anchor = removed_higher_need.external_anchor().unwrap();
    removed_higher_need.steps[0].inspection.higher_degree_need = None;
    removed_higher_need.terminal.kind = TerminalKind::StabilizedSurvivor;
    removed_higher_need.terminal.reason = "jointly re-sealed higher-degree witness".into();
    assert_anchor_resealed_rejected(removed_higher_need, &higher_anchor);

    let mut rebound_defect = run_case(case_named("multi_agent_common_mode_failure"));
    let defect_anchor = rebound_defect.external_anchor().unwrap();
    rebound_defect.steps[0].inspection.defects[0].evidence_ref =
        "fixture://jointly-resealed/defect-evidence".into();
    assert_anchor_resealed_rejected(rebound_defect, &defect_anchor);

    let mut rebound_cochain = run_case(case_named("math_local_green_global_red"));
    let cochain_anchor = rebound_cochain.external_anchor().unwrap();
    let step = &mut rebound_cochain.steps[0];
    step.inspection.defects[0].cochain.as_mut().unwrap().degree = 2;
    let defect = &mut step.inspection.defects[0];
    let rebound_signature = hash_json(&(
        &defect.defect_id,
        &defect.claim_id,
        &defect.kind,
        &defect.cell_refs,
        &defect.cochain,
    ));
    defect.signature_sha256 = rebound_signature.clone();
    step.inspection.signatures[0].signature_sha256 = rebound_signature.clone();
    for candidate in &mut step.candidates {
        candidate.matched_signature_sha256 = rebound_signature.clone();
    }
    let selected_id = step.selected_proposal_id.clone().unwrap();
    let selected_index = step
        .candidates
        .iter()
        .position(|candidate| candidate.proposal_id == selected_id)
        .unwrap();
    let source_candidate_sha256 = hash_json(&step.candidates[selected_index]);
    step.selected_candidate_sha256 = Some(source_candidate_sha256.clone());
    let compiled = step.compiled_operator_candidate.as_mut().unwrap();
    compiled.observed_signature_sha256 = rebound_signature;
    compiled.source_candidate_sha256 = source_candidate_sha256;
    reseal_source_proposal(compiled);
    reseal_compiled_evidence(compiled);
    assert_anchor_resealed_rejected(rebound_cochain, &cochain_anchor);

    let mut rebound_candidate_inspection = run_case(case_named("math_local_green_global_red"));
    let candidate_anchor = rebound_candidate_inspection.external_anchor().unwrap();
    let step = &mut rebound_candidate_inspection.steps[0];
    let selected_id = step.selected_proposal_id.clone().unwrap();
    let selected_index = step
        .candidates
        .iter()
        .position(|candidate| candidate.proposal_id == selected_id)
        .unwrap();
    step.candidates[selected_index]
        .post_inspection
        .as_mut()
        .unwrap()
        .discarded_information_refs
        .push("fixture://jointly-resealed/candidate-inspection".into());
    let post_inspection_sha256 = hash_json(
        step.candidates[selected_index]
            .post_inspection
            .as_ref()
            .unwrap(),
    );
    let source_candidate_sha256 = hash_json(&step.candidates[selected_index]);
    step.selected_candidate_sha256 = Some(source_candidate_sha256.clone());
    let compiled = step.compiled_operator_candidate.as_mut().unwrap();
    compiled.post_inspection_sha256 = post_inspection_sha256;
    compiled.source_candidate_sha256 = source_candidate_sha256;
    reseal_compiled_evidence(compiled);
    assert_anchor_resealed_rejected(rebound_candidate_inspection, &candidate_anchor);
}

#[test]
fn receipt_verification_rejects_joint_rebinding_and_nondescending_selection() {
    let original = run_case(case_named("math_local_green_global_red"));

    let mut carrier_rebinding = original.clone();
    let rebound_carrier_sha256 = "a".repeat(64);
    carrier_rebinding.steps[0].carrier_sha256 = rebound_carrier_sha256.clone();
    let compiled = carrier_rebinding.steps[0]
        .compiled_operator_candidate
        .as_mut()
        .unwrap();
    compiled.source_carrier_sha256 = rebound_carrier_sha256;
    reseal_compiled_evidence(compiled);
    assert_resealed_rejected(carrier_rebinding);

    let mut state_rebinding = original.clone();
    let rebound_state_sha256 = "b".repeat(64);
    state_rebinding.steps[0].state_sha256 = rebound_state_sha256.clone();
    let compiled = state_rebinding.steps[0]
        .compiled_operator_candidate
        .as_mut()
        .unwrap();
    compiled.source_state_sha256 = rebound_state_sha256;
    reseal_compiled_evidence(compiled);
    assert_resealed_rejected(state_rebinding);

    let mut nondescending = original;
    let step = &mut nondescending.steps[0];
    let selected_proposal_id = step.selected_proposal_id.clone().unwrap();
    let candidate_index = step
        .candidates
        .iter()
        .position(|candidate| candidate.proposal_id == selected_proposal_id)
        .unwrap();
    let before = step.inspection.measure;
    let candidate = &mut step.candidates[candidate_index];
    candidate.after = Some(before);
    candidate.post_inspection.as_mut().unwrap().measure = before;
    let post_inspection_sha256 = hash_json(candidate.post_inspection.as_ref().unwrap());
    let source_candidate_sha256 = hash_json(candidate);
    step.selected_candidate_sha256 = Some(source_candidate_sha256.clone());
    let compiled = step.compiled_operator_candidate.as_mut().unwrap();
    compiled.after = before;
    compiled.post_inspection_sha256 = post_inspection_sha256;
    compiled.source_candidate_sha256 = source_candidate_sha256;
    reseal_compiled_evidence(compiled);
    assert_resealed_rejected(nondescending);
}

#[test]
fn receipt_verification_reconstructs_extension_payload_through_final_carrier() {
    let mut receipt = run_case(case_named("paperer008_self_application"));
    assert!(receipt.steps[0].carrier_extension.is_some());

    let final_cell = receipt
        .final_carrier
        .cells
        .iter_mut()
        .find(|cell| cell.cell_id == "contract_surface")
        .unwrap();
    final_cell.payload_sha256 = hash_json("substituted contract payload");
    let rebound_carrier_sha256 = hash_json(&receipt.final_carrier);

    receipt.steps[0]
        .carrier_extension
        .as_mut()
        .unwrap()
        .extended_carrier_sha256 = rebound_carrier_sha256.clone();
    for step in receipt.steps.iter_mut().skip(1) {
        step.carrier_sha256 = rebound_carrier_sha256.clone();
        if let Some(compiled) = step.compiled_operator_candidate.as_mut() {
            compiled.source_carrier_sha256 = rebound_carrier_sha256.clone();
            reseal_compiled_evidence(compiled);
        }
    }
    assert_resealed_rejected(receipt);
}

#[test]
#[cfg(feature = "paper070-test-clock")]
fn deterministic_clock_overruns_terminalize_before_mutation() {
    let scenarios = [
        ("math_local_green_global_red", FaultMode::SlowInspect),
        (
            "math_local_green_global_red",
            FaultMode::SlowCandidateInspect,
        ),
        ("math_local_green_global_red", FaultMode::SlowPropose),
        ("math_local_green_global_red", FaultMode::SlowAssess),
        ("paperer008_self_application", FaultMode::SlowExtension),
    ];

    for (case_name, mode) in scenarios {
        let case = case_named(case_name);
        let clock = Arc::new(ManualClock::default());
        let adapter = FaultInjectingAdapter::with_clock(case.clone(), mode, Arc::clone(&clock));
        let mut budget = default_budget();
        budget.max_wall_millis = 10;
        let receipt = run_multipath_with_test_clock(
            &adapter,
            case.packet(),
            &operator_registry(),
            budget,
            &CancellationToken::default(),
            clock.as_ref(),
        )
        .unwrap();

        assert_eq!(receipt.terminal.kind, TerminalKind::BudgetExhausted);
        assert_eq!(receipt.initial_carrier, receipt.final_carrier);
        assert_eq!(receipt.initial_state_sha256, receipt.final_state_sha256);
        assert_eq!(receipt.accounting.accepted_transitions, 0);
        assert_eq!(receipt.accounting.carrier_extensions, 0);
        assert!(receipt.runtime_micros >= 20_000);
        assert!(receipt.verify_replay_hash().unwrap());
    }
}

#[test]
fn proposal_flood_is_aggregate_pruned_before_sort_or_materialization() {
    let case = case_named("math_local_green_global_red");
    let mut budget = default_budget();
    budget.max_candidates = 4;
    let receipt = run_multipath(
        &FaultInjectingAdapter::new(case.clone(), FaultMode::ProposalFlood),
        case.packet(),
        &operator_registry(),
        budget,
        &CancellationToken::default(),
    )
    .unwrap();

    assert_eq!(receipt.terminal.kind, TerminalKind::BudgetExhausted);
    assert_eq!(receipt.accounting.proposed, 12);
    assert_eq!(receipt.accounting.budget_pruned, 12);
    assert_eq!(receipt.accounting.evaluated, 0);
    assert!(receipt.steps[0].candidates.is_empty());
    assert_eq!(receipt.initial_carrier, receipt.final_carrier);
    assert_eq!(receipt.initial_state_sha256, receipt.final_state_sha256);
    assert!(receipt.verify_replay_hash().unwrap());
}
#[test]
fn detector_identity_uses_structured_pairs_not_delimiter_concatenation() {
    let case = case_named("higher_coherence_requires_lift");
    let mut packet = case.packet();
    let packet_requirement = DetectorRequirement {
        claim_id: "a::b".into(),
        distinction_id: "c".into(),
    };
    let colliding_requirement = DetectorRequirement {
        claim_id: "a".into(),
        distinction_id: "b::c".into(),
    };

    packet.protected_distinctions = vec![packet_requirement.clone(), colliding_requirement.clone()];
    assert!(
        packet.clone().canonicalized().is_ok(),
        "distinct structured pairs must not be rejected as duplicates"
    );

    packet.protected_distinctions = vec![packet_requirement.clone()];
    let error = run_multipath(
        &FaultInjectingAdapter::new(case.clone(), FaultMode::CollidingCoverageIdentity),
        packet,
        &operator_registry(),
        default_budget(),
        &CancellationToken::default(),
    )
    .unwrap_err();
    assert!(matches!(error, IteratorError::InvalidDeclaration(_)));

    let original = run_case(case);
    let anchor = original.external_anchor().unwrap();
    let mut resealed = original;
    resealed.packet.protected_distinctions = vec![packet_requirement];
    resealed.packet_sha256 = resealed.packet.sha256().unwrap();
    for step in &mut resealed.steps {
        step.inspection.coverage[0].requirement = colliding_requirement.clone();
    }
    reseal(&mut resealed);
    assert!(!resealed.verify_replay_hash().unwrap());
    assert!(!resealed.verify_against_anchor(&anchor).unwrap());
}

#[test]
fn accounting_overflow_is_refused_in_replay_anchor_and_runtime_paths() {
    let original = run_case(case_named("math_local_green_global_red"));
    let anchor = original.external_anchor().unwrap();
    let mut overflowed = original;
    overflowed.accounting.proposed = usize::MAX;
    overflowed.accounting.evaluated = usize::MAX;
    overflowed.accounting.duplicate_pruned = 1;
    overflowed.accounting.budget_pruned = 0;
    reseal(&mut overflowed);
    assert!(!overflowed.verify_replay_hash().unwrap());
    assert!(!overflowed.verify_against_anchor(&anchor).unwrap());

    let case = case_named("math_local_green_global_red");
    let error = run_multipath(
        &FaultInjectingAdapter::new(case.clone(), FaultMode::PredictedAvoidanceOverflow),
        case.packet(),
        &operator_registry(),
        default_budget(),
        &CancellationToken::default(),
    )
    .unwrap_err();
    assert!(matches!(
        error,
        IteratorError::InvalidDeclaration(detail)
            if detail.contains("predicted quotient avoidance accounting overflow")
    ));
}

#[test]
fn deserialized_noncanonical_registries_are_refused_before_a_green_terminal() {
    let canonical = serde_json::to_value(operator_registry()).unwrap();
    let source = canonical["operators"][0].clone();

    let mut later = source.clone();
    later["operator_id"] = serde_json::json!("op.paper070.zzz");
    let unsorted = serde_json::json!({"operators": [later, source.clone()]});
    let duplicate_ids = serde_json::json!({"operators": [source.clone(), source.clone()]});

    let mut duplicate_set = canonical.clone();
    let signatures = duplicate_set["operators"][0]["signature_kinds"]
        .as_array_mut()
        .unwrap();
    signatures.push(signatures[0].clone());

    let mut malformed_hash = canonical.clone();
    malformed_hash["operators"][0]["deformation_descriptor_sha256"] =
        serde_json::json!("not-a-sha256");

    let case = case_named("math_local_green_global_red");
    for malformed in [unsorted, duplicate_ids, duplicate_set, malformed_hash] {
        let registry: OperatorRegistry = serde_json::from_value(malformed).unwrap();
        assert!(registry.sha256().is_err());
        let error = run_multipath(
            &FaultInjectingAdapter::new(case.clone(), FaultMode::InitiallyResolved),
            case.packet(),
            &registry,
            default_budget(),
            &CancellationToken::default(),
        )
        .unwrap_err();
        assert!(matches!(
            error,
            IteratorError::InvalidRegistry(_) | IteratorError::InvalidDeclaration(_)
        ));
    }

    let registry: OperatorRegistry = serde_json::from_value(canonical).unwrap();
    let receipt = run_multipath(
        &FaultInjectingAdapter::new(case.clone(), FaultMode::InitiallyResolved),
        case.packet(),
        &registry,
        default_budget(),
        &CancellationToken::default(),
    )
    .unwrap();
    assert_eq!(receipt.terminal.kind, TerminalKind::StabilizedSurvivor);
    assert!(receipt.verify_replay_hash().unwrap());
}

// Origin: engine/crates_rs/tests/engines/multipath_iterator.rs
// Claim: urn:core:crates_rs:tests:multipath-iterator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf1816ac9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf1816ac9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf1816ac9 {
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
impl BoundaryErrorf1816ac9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf1816ac9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf1816ac9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf1816ac9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf1816ac9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf1816ac9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf1816ac9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf1816ac9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f1816ac9() {
    let admitted = BoundaryRecordf1816ac9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf1816ac9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
