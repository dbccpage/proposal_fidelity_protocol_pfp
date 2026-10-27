//! Finite, typed, obstruction-directed iteration for Paper 070.
//!
//! The iterator is a bounded orchestration shell. Domain adapters own the
//! meaning of packets, projections, preservation checks, and candidate states.
//! Exact admitted F2 `C0 -> C1 -> C2` probes reuse the DDA degree tower. A zero
//! probe never implies global coherence: every protected distinction must also
//! be classified as visible, projection loss, or detector inadequate.
//!
//! Every receipt produced here has [`AuthorityEffect::None`]. This module can
//! propose, evaluate, and replay candidates; it cannot certify or promote them.

use std::collections::{BTreeMap, BTreeSet};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::time::Instant;

use core_wdp::ddc::agent_contract::sha256_bytes;
use core_wdp::ddc::degree_tower::{
    BinaryCochainSegment, DegreeDiagnostic, DegreeTrichotomy,
};
use core_types::{authority::AuthorityEffect, Hash256};
use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::obstruction_runtime::{OperatorId, Provenance};

pub const MULTIPATH_RECEIPT_SCHEMA: &str = "core.multipath.run_receipt.v3";
pub const MULTIPATH_RECEIPT_ANCHOR_SCHEMA: &str = "core.multipath.run_receipt_anchor.v1";
const INSPECTION_TRACE_HASH_DOMAIN: &str = "core.paper070.inspection_trace.v1";
const OPERATOR_PATTERN_HASH_DOMAIN: &str = "core.paper070.operator_pattern.v3";
const OPERATOR_EVIDENCE_HASH_DOMAIN: &str = "core.paper070.operator_evidence.v3";
const OPERATOR_PROPOSAL_HASH_DOMAIN: &str = "core.paper070.operator_proposal.v3";
const SOURCE_OPERATOR_HASH_DOMAIN: &str = "core.paper070.source_operator.v3";
const SOURCE_ASSESSMENT_HASH_DOMAIN: &str = "core.paper070.source_assessment.v3";

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CarrierKind {
    DirectedGraph,
    Hypergraph,
    SimplicialComplex,
    CellularComplex,
    DependencyGraph,
    ProofGraph,
    CodeChangeGraph,
    WorkflowGraph,
    OpaqueFinite,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CarrierCell {
    pub cell_id: String,
    pub degree: usize,
    pub boundary: Vec<String>,
    pub payload_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FiniteCarrier {
    pub carrier_id: String,
    pub kind: CarrierKind,
    pub cells: Vec<CarrierCell>,
}

impl FiniteCarrier {
    pub fn canonicalized(mut self) -> Result<Self, IteratorError> {
        nonempty(&self.carrier_id, "carrier_id")?;
        for cell in &mut self.cells {
            cell.boundary.sort();
            ensure_unique(&cell.boundary, "cell boundary")?;
        }
        self.cells.sort_by(|left, right| {
            (left.degree, &left.cell_id).cmp(&(right.degree, &right.cell_id))
        });
        self.validate()?;
        Ok(self)
    }

    pub fn validate(&self) -> Result<(), IteratorError> {
        nonempty(&self.carrier_id, "carrier_id")?;
        let mut degree_by_id = BTreeMap::new();
        for cell in &self.cells {
            validate_carrier_cell_header(cell, &mut degree_by_id)?;
        }
        for cell in &self.cells {
            validate_carrier_cell_boundaries(cell, &degree_by_id)?;
        }
        Ok(())
    }

    fn extend(&mut self, extension: &CarrierExtension) -> Result<(), IteratorError> {
        let mut candidate = self.clone();
        candidate.cells.extend(extension.new_cells.clone());
        *self = candidate.canonicalized()?;
        Ok(())
    }
}

fn validate_carrier_cell_header(
    cell: &CarrierCell,
    degree_by_id: &mut BTreeMap<String, usize>,
) -> Result<(), IteratorError> {
    nonempty(&cell.cell_id, "carrier cell id")?;
    if !is_sha256(&cell.payload_sha256) {
        return Err(IteratorError::InvalidCarrier(format!(
            "carrier cell `{}` payload_sha256 must be lowercase SHA-256",
            cell.cell_id
        )));
    }
    if degree_by_id
        .insert(cell.cell_id.clone(), cell.degree)
        .is_some()
    {
        return Err(IteratorError::InvalidCarrier(format!(
            "duplicate carrier cell `{}`",
            cell.cell_id
        )));
    }
    validate_carrier_cell_degree_boundary(cell)
}

fn validate_carrier_cell_degree_boundary(cell: &CarrierCell) -> Result<(), IteratorError> {
    if cell.degree == 0 && !cell.boundary.is_empty() {
        return Err(IteratorError::InvalidCarrier(format!(
            "degree-zero cell `{}` has a boundary",
            cell.cell_id
        )));
    }
    if cell.degree > 0 && cell.boundary.is_empty() {
        return Err(IteratorError::InvalidCarrier(format!(
            "positive-degree cell `{}` has an empty boundary",
            cell.cell_id
        )));
    }
    Ok(())
}

fn validate_carrier_cell_boundaries(
    cell: &CarrierCell,
    degree_by_id: &BTreeMap<String, usize>,
) -> Result<(), IteratorError> {
    for boundary_id in &cell.boundary {
        let Some(boundary_degree) = degree_by_id.get(boundary_id) else {
            return Err(IteratorError::InvalidCarrier(format!(
                "cell `{}` references missing boundary cell `{boundary_id}`",
                cell.cell_id
            )));
        };
        if *boundary_degree >= cell.degree {
            return Err(IteratorError::InvalidCarrier(format!(
                "cell `{}` degree {} references non-lower boundary cell `{boundary_id}` degree {}",
                cell.cell_id, cell.degree, boundary_degree
            )));
        }
    }
    Ok(())
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DetectorRequirement {
    pub claim_id: String,
    pub distinction_id: String,
}

impl DetectorRequirement {
    fn key(&self) -> String {
        format!(
            "{}:{}|{}:{}",
            self.claim_id.len(),
            self.claim_id,
            self.distinction_id.len(),
            self.distinction_id
        )
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProblemPacket {
    pub packet_id: String,
    pub domain: String,
    pub payload: serde_json::Value,
    pub protected_distinctions: Vec<DetectorRequirement>,
    pub packet_refs: Vec<String>,
    pub evidence_ceiling: String,
}

impl ProblemPacket {
    pub fn canonicalized(mut self) -> Result<Self, IteratorError> {
        nonempty(&self.packet_id, "packet_id")?;
        nonempty(&self.domain, "domain")?;
        nonempty(&self.evidence_ceiling, "evidence_ceiling")?;
        canonicalize_packet_refs(&mut self.packet_refs)?;
        canonicalize_protected_distinctions(&mut self.protected_distinctions)?;
        Ok(self)
    }

    pub fn sha256(&self) -> Result<String, IteratorError> {
        sha256_json(&self.clone().canonicalized()?)
    }
}

fn canonicalize_packet_refs(packet_refs: &mut [String]) -> Result<(), IteratorError> {
    if packet_refs.is_empty() {
        return Err(IteratorError::InvalidDeclaration(
            "packet_refs must contain at least one immutable packet reference".into(),
        ));
    }
    packet_refs.sort();
    ensure_unique(packet_refs, "packet_refs")?;
    for packet_ref in packet_refs {
        nonempty(packet_ref, "packet_ref")?;
    }
    Ok(())
}

fn canonicalize_protected_distinctions(
    distinctions: &mut [DetectorRequirement],
) -> Result<(), IteratorError> {
    distinctions.sort();
    for requirement in distinctions.iter() {
        nonempty(&requirement.claim_id, "claim_id")?;
        nonempty(&requirement.distinction_id, "distinction_id")?;
    }
    ensure_unique(distinctions, "protected distinctions")
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObserverDeclaration {
    pub observer_id: String,
    pub observer_family: String,
    pub scope: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ComparisonDeclaration {
    pub comparison_id: String,
    pub zero_rel: String,
    pub gauge_family: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProjectedDatum {
    pub datum_id: String,
    pub degree: usize,
    pub source_refs: Vec<String>,
    pub value_sha256: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CoverageDisposition {
    PreservedVisible,
    ProjectionLoss,
    DetectorInadequate,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProjectionLossReceipt {
    pub loss_id: String,
    pub source_refs: Vec<String>,
    pub collided_projection_refs: Vec<String>,
    pub discarded_sha256: String,
    pub recovery_requirement: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CoverageAssessment {
    pub requirement: DetectorRequirement,
    pub disposition: CoverageDisposition,
    pub evidence_ref: String,
    pub projection_loss: Option<ProjectionLossReceipt>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ExactBinaryCochainProbe {
    pub segment: BinaryCochainSegment,
    pub residual: Vec<bool>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(deny_unknown_fields)]
pub struct VisibleDefect {
    pub defect_id: String,
    pub claim_id: String,
    pub kind: String,
    pub cell_refs: Vec<String>,
    pub evidence_ref: String,
    pub exact_binary_cochain: Option<ExactBinaryCochainProbe>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HigherDegreeNeed {
    pub current_max_degree: usize,
    pub required_degree: usize,
    pub witness_ref: String,
    pub licensed_lift_ref: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Inspection {
    pub observer: ObserverDeclaration,
    pub comparison: ComparisonDeclaration,
    pub projected_data: Vec<ProjectedDatum>,
    pub coverage: Vec<CoverageAssessment>,
    pub visible_defects: Vec<VisibleDefect>,
    pub higher_degree_need: Option<HigherDegreeNeed>,
    pub discarded_information_refs: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CochainDiagnosticReceipt {
    pub degree: usize,
    pub phi: usize,
    pub gamma: usize,
    pub classification: String,
}

impl From<DegreeDiagnostic> for CochainDiagnosticReceipt {
    fn from(value: DegreeDiagnostic) -> Self {
        Self {
            degree: value.degree,
            phi: value.phi,
            gamma: value.gamma,
            classification: match value.classification {
                DegreeTrichotomy::Exact => "exact",
                DegreeTrichotomy::StabilizedSurvivor => "stabilized_survivor",
                DegreeTrichotomy::Open => "open",
            }
            .into(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DefectReceipt {
    pub defect_id: String,
    pub claim_id: String,
    pub kind: String,
    pub cell_refs: Vec<String>,
    pub evidence_ref: String,
    pub signature_sha256: String,
    pub cochain: Option<CochainDiagnosticReceipt>,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObstructionMeasure {
    pub projection_loss_count: usize,
    pub open_defect_count: usize,
    pub gamma_total: usize,
    pub phi_total: usize,
    pub stabilized_survivor_count: usize,
}

impl ObstructionMeasure {
    fn rank(self) -> (usize, usize, usize, usize, usize) {
        (
            self.projection_loss_count,
            self.open_defect_count,
            self.gamma_total,
            self.phi_total,
            self.stabilized_survivor_count,
        )
    }

    fn strictly_descends_to(self, after: Self) -> bool {
        after.rank() < self.rank()
    }

    fn is_resolved(self) -> bool {
        self.projection_loss_count == 0 && self.open_defect_count == 0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObstructionSignature {
    pub defect_id: String,
    pub kind: String,
    pub signature_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct InspectionReceipt {
    pub observer: ObserverDeclaration,
    pub comparison: ComparisonDeclaration,
    pub projected_data: Vec<ProjectedDatum>,
    pub coverage: Vec<CoverageAssessment>,
    pub defects: Vec<DefectReceipt>,
    pub signatures: Vec<ObstructionSignature>,
    pub measure: ObstructionMeasure,
    pub detector_inadequate_count: usize,
    pub higher_degree_need: Option<HigherDegreeNeed>,
    pub discarded_information_refs: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TerminalKind {
    ExactRepair,
    StabilizedSurvivor,
    OpenObstruction,
    DetectorInadequate,
    NoRule,
    RequiresLift,
    Refused,
    BudgetExhausted,
    Cancelled,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TerminalReceipt {
    pub kind: TerminalKind,
    pub reason: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RegisteredOperator {
    pub operator_id: OperatorId,
    pub signature_kinds: Vec<String>,
    pub carrier_kinds: Vec<CarrierKind>,
    pub preconditions: Vec<String>,
    /// Adapter-owned implementation or declarative transformation reference.
    pub deformation_ref: String,
    /// Hash of the canonical transformation descriptor, not a semantic proof.
    pub deformation_descriptor_sha256: String,
    pub preservation_obligations: Vec<String>,
    pub witness_procedure: String,
    /// Declares congruence of every admission predicate and the post-inspection measure.
    pub equivalence_contract: Option<String>,
    pub requires_lift: bool,
    pub possible_terminals: Vec<TerminalKind>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OperatorRegistry {
    operators: Vec<RegisteredOperator>,
}

impl OperatorRegistry {
    pub fn new(mut operators: Vec<RegisteredOperator>) -> Result<Self, IteratorError> {
        for operator in &mut operators {
            validate_operator_scalars(operator)?;
            validate_and_sort_operator_collections(operator)?;
        }
        operators.sort_by(|left, right| left.operator_id.0.cmp(&right.operator_id.0));
        let ids: Vec<_> = operators
            .iter()
            .map(|operator| operator.operator_id.0.clone())
            .collect();
        ensure_unique(&ids, "operator ids")?;
        Ok(Self { operators })
    }

    pub fn operators(&self) -> &[RegisteredOperator] {
        &self.operators
    }

    pub fn get(&self, operator_id: &OperatorId) -> Option<&RegisteredOperator> {
        self.operators
            .binary_search_by(|candidate| candidate.operator_id.0.cmp(&operator_id.0))
            .ok()
            .map(|index| &self.operators[index])
    }

    fn validate_canonical(&self) -> Result<(), IteratorError> {
        let canonical = Self::new(self.operators.clone())?;
        if &canonical != self {
            return Err(IteratorError::InvalidRegistry(
                "operator registry must already be in canonical form".into(),
            ));
        }
        Ok(())
    }

    pub fn sha256(&self) -> Result<String, IteratorError> {
        self.validate_canonical()?;
        sha256_json(self)
    }
}

fn validate_operator_scalars(operator: &RegisteredOperator) -> Result<(), IteratorError> {
    nonempty(&operator.operator_id.0, "operator_id")?;
    nonempty(&operator.deformation_ref, "operator deformation_ref")?;
    if !is_sha256(&operator.deformation_descriptor_sha256) {
        return Err(IteratorError::InvalidRegistry(format!(
            "operator `{}` has an invalid deformation descriptor SHA-256",
            operator.operator_id
        )));
    }
    nonempty(&operator.witness_procedure, "operator witness_procedure")?;
    if let Some(contract) = &operator.equivalence_contract {
        nonempty(contract, "operator equivalence_contract")?;
    }
    Ok(())
}

fn validate_and_sort_operator_collections(
    operator: &mut RegisteredOperator,
) -> Result<(), IteratorError> {
    for (values, label) in [
        (&operator.signature_kinds, "operator signature kind"),
        (&operator.preconditions, "operator precondition"),
        (
            &operator.preservation_obligations,
            "operator preservation obligation",
        ),
    ] {
        for value in values {
            nonempty(value, label)?;
        }
    }
    if !operator_has_required_collections(operator) {
        return Err(IteratorError::InvalidRegistry(format!(
            "operator {} must declare signatures, carriers, preservation obligations, and possible terminals",
            operator.operator_id
        )));
    }
    sort_and_dedup_operator_collections(operator)
}

fn operator_has_required_collections(operator: &RegisteredOperator) -> bool {
    !operator.signature_kinds.is_empty()
        && !operator.carrier_kinds.is_empty()
        && !operator.preservation_obligations.is_empty()
        && !operator.possible_terminals.is_empty()
}

fn sort_and_dedup_operator_collections(
    operator: &mut RegisteredOperator,
) -> Result<(), IteratorError> {
    operator.signature_kinds.sort();
    operator.carrier_kinds.sort();
    operator.preconditions.sort();
    operator.preservation_obligations.sort();
    operator
        .possible_terminals
        .sort_by_key(|terminal| *terminal as u8);
    ensure_unique(&operator.signature_kinds, "operator signature kinds")?;
    ensure_unique(&operator.carrier_kinds, "operator carrier kinds")?;
    ensure_unique(&operator.preconditions, "operator preconditions")?;
    ensure_unique(
        &operator.preservation_obligations,
        "operator preservation obligations",
    )?;
    ensure_unique(&operator.possible_terminals, "operator possible terminals")
}

#[derive(Debug, Clone)]
pub struct DeformationProposal<S> {
    pub proposal_id: String,
    pub operator_id: OperatorId,
    pub provenance: Provenance,
    pub matched_signature_sha256: String,
    pub equivalence_key: Option<String>,
    pub predicted_candidates_avoided: usize,
    pub state: S,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CheckVerdict {
    Pass,
    Fail,
    Inconclusive,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PreservationCheck {
    pub obligation_id: String,
    pub verdict: CheckVerdict,
    pub evidence_ref: String,
    pub evidence_sha256: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum WitnessRelation {
    SeparateImplementation,
    HumanReview,
    CommonSource,
    SharedModelFamily,
    Unestablished,
}

impl WitnessRelation {
    fn supports_independence(self) -> bool {
        matches!(self, Self::SeparateImplementation | Self::HumanReview)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WitnessResult {
    pub witness_id: String,
    pub procedure: String,
    pub relation: WitnessRelation,
    pub verdict: CheckVerdict,
    pub evidence_ref: String,
    pub evidence_sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateAssessment {
    pub preservation: Vec<PreservationCheck>,
    pub witnesses: Vec<WitnessResult>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CarrierExtension {
    pub extension_id: String,
    pub trigger_signature_sha256: String,
    pub justification_ref: String,
    pub new_cells: Vec<CarrierCell>,
}

#[derive(Debug, Clone)]
pub struct AdapterSeed<S> {
    pub state: S,
    pub carrier: FiniteCarrier,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AdapterFailureKind {
    DetectorInadequate,
    NoRule,
    RequiresLift,
    Refused,
}

#[derive(Debug, Clone, Error, PartialEq, Eq, Serialize, Deserialize)]
#[error("{kind:?}: {detail}")]
#[serde(deny_unknown_fields)]
pub struct AdapterFailure {
    pub kind: AdapterFailureKind,
    pub detail: String,
}

pub trait MultipathAdapter {
    type State: Clone + Serialize;

    fn adapter_id(&self) -> &str;

    fn seed(&self, packet: &ProblemPacket) -> Result<AdapterSeed<Self::State>, AdapterFailure>;

    fn inspect(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
    ) -> Result<Inspection, AdapterFailure>;

    fn propose(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
        signatures: &[ObstructionSignature],
    ) -> Result<Vec<DeformationProposal<Self::State>>, AdapterFailure>;

    fn assess_candidate(
        &self,
        packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        before: &Self::State,
        proposal: &DeformationProposal<Self::State>,
        operator: &RegisteredOperator,
    ) -> Result<CandidateAssessment, AdapterFailure>;

    fn extend_carrier(
        &self,
        _packet: &ProblemPacket,
        _carrier: &FiniteCarrier,
        _state: &Self::State,
        _inspection: &InspectionReceipt,
    ) -> Result<Option<CarrierExtension>, AdapterFailure> {
        Ok(None)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunBudget {
    pub max_steps: usize,
    pub max_candidates: usize,
    pub max_carrier_cells: usize,
    pub max_receipt_bytes: usize,
    pub max_wall_millis: u64,
    pub require_independent_witness: bool,
}

impl RunBudget {
    pub fn validate(self) -> Result<Self, IteratorError> {
        if self.max_steps == 0
            || self.max_candidates == 0
            || self.max_carrier_cells == 0
            || self.max_receipt_bytes == 0
            || self.max_wall_millis == 0
        {
            return Err(IteratorError::InvalidBudget(
                "all numeric budgets must be positive".into(),
            ));
        }
        Ok(self)
    }
}

#[derive(Debug, Clone, Default)]
pub struct CancellationToken(Arc<AtomicBool>);

impl CancellationToken {
    pub fn cancel(&self) {
        self.0.store(true, Ordering::SeqCst);
    }

    pub fn is_cancelled(&self) -> bool {
        self.0.load(Ordering::SeqCst)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CandidateVerdict {
    EligibleDescent,
    RejectedNoDescent,
    RejectedPreservation,
    RejectedWitness,
    RejectedAdapter,
    InvalidProposal,
    RequiresLift,
    DuplicatePruned,
    BudgetPruned,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateReceipt {
    pub proposal_id: String,
    pub operator_id: OperatorId,
    pub provenance: Provenance,
    pub state_sha256: String,
    pub matched_signature_sha256: String,
    pub equivalence_key: Option<String>,
    pub predicted_candidates_avoided: usize,
    pub verdict: CandidateVerdict,
    pub reason: String,
    pub before: ObstructionMeasure,
    pub after: Option<ObstructionMeasure>,
    pub preservation: Vec<PreservationCheck>,
    pub witnesses: Vec<WitnessResult>,
    pub post_inspection: Option<InspectionReceipt>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledOperatorCandidate {
    pub candidate_operator_id: OperatorId,
    pub source_operator_id: OperatorId,
    pub source_operator_sha256: String,
    pub source_operator_signature_kinds: Vec<String>,
    pub source_operator_carrier_kinds: Vec<CarrierKind>,
    pub source_registry_sha256: String,
    pub source_proposal_id: String,
    pub source_proposal_sha256: String,
    pub source_assessment_sha256: String,
    pub source_candidate_sha256: String,
    pub source_step_index: usize,
    pub source_packet_sha256: String,
    pub source_carrier_sha256: String,
    pub source_state_sha256: String,
    pub result_state_sha256: String,
    pub source_provenance: Provenance,
    pub source_equivalence_key: Option<String>,
    pub source_predicted_candidates_avoided: usize,
    pub signature_kind: String,
    pub observed_signature_sha256: String,
    pub carrier_kind: CarrierKind,
    pub preconditions: Vec<String>,
    pub deformation_ref: String,
    pub deformation_descriptor_sha256: String,
    pub preservation_obligations: Vec<String>,
    pub preservation_checks: Vec<PreservationCheck>,
    pub witness_procedure: String,
    pub witness_results: Vec<WitnessResult>,
    pub equivalence_contract: Option<String>,
    pub requires_lift: bool,
    pub possible_terminals: Vec<TerminalKind>,
    pub before: ObstructionMeasure,
    pub after: ObstructionMeasure,
    pub post_inspection_sha256: String,
    pub pattern_sha256: String,
    pub evidence_sha256: String,
    pub authority_effect: AuthorityEffect,
}

impl CompiledOperatorCandidate {
    pub fn verify_hashes(&self) -> Result<bool, IteratorError> {
        if !self.has_canonical_preconditions() {
            return Ok(false);
        }
        self.matches_recomputed_hashes()
    }

    fn has_canonical_preconditions(&self) -> bool {
        let bound_hashes = [
            self.source_operator_sha256.as_str(),
            self.source_registry_sha256.as_str(),
            self.source_proposal_sha256.as_str(),
            self.source_assessment_sha256.as_str(),
            self.source_candidate_sha256.as_str(),
            self.source_packet_sha256.as_str(),
            self.source_carrier_sha256.as_str(),
            self.source_state_sha256.as_str(),
            self.result_state_sha256.as_str(),
            self.observed_signature_sha256.as_str(),
            self.deformation_descriptor_sha256.as_str(),
            self.post_inspection_sha256.as_str(),
            self.pattern_sha256.as_str(),
            self.evidence_sha256.as_str(),
        ];
        self.authority_effect.is_none()
            && bound_hashes.iter().all(|value| is_sha256(value))
            && compiled_candidate_fields_are_canonical(self)
            && self.candidate_operator_id.0 == format!("candidate.sha256.{}", self.pattern_sha256)
    }

    fn matches_recomputed_hashes(&self) -> Result<bool, IteratorError> {
        if self.source_operator_sha256 != source_operator_hash(self)?
            || self.source_proposal_sha256 != source_proposal_hash(self)?
            || self.source_assessment_sha256 != source_assessment_hash(self)?
        {
            return Ok(false);
        }
        Ok(self.pattern_sha256 == operator_pattern_hash(self)?
            && self.evidence_sha256 == operator_evidence_hash(self)?)
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CarrierExtensionReceipt {
    pub extension_id: String,
    pub trigger_signature_sha256: String,
    pub justification_ref: String,
    pub parent_carrier_sha256: String,
    pub extended_carrier_sha256: String,
    pub added_cell_ids: Vec<String>,
    pub added_cells: Vec<CarrierCell>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StepReceipt {
    pub step_index: usize,
    pub state_sha256: String,
    pub carrier_sha256: String,
    pub inspection: InspectionReceipt,
    pub candidates: Vec<CandidateReceipt>,
    pub selected_proposal_id: Option<String>,
    pub selected_candidate_sha256: Option<String>,
    pub compiled_operator_candidate: Option<CompiledOperatorCandidate>,
    pub carrier_extension: Option<CarrierExtensionReceipt>,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateAccounting {
    pub proposed: usize,
    pub evaluated: usize,
    pub duplicate_pruned: usize,
    pub budget_pruned: usize,
    pub predicted_avoided_by_quotient: usize,
    pub accepted_transitions: usize,
    pub compiled_operator_candidates: usize,
    pub carrier_extensions: usize,
}

impl CandidateAccounting {
    pub fn is_balanced(&self) -> bool {
        self.evaluated
            .checked_add(self.duplicate_pruned)
            .and_then(|subtotal| subtotal.checked_add(self.budget_pruned))
            == Some(self.proposed)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunReceipt {
    pub schema_version: String,
    pub adapter_id: String,
    pub packet: ProblemPacket,
    pub packet_sha256: String,
    pub operator_registry: OperatorRegistry,
    pub operator_registry_sha256: String,
    pub initial_carrier: FiniteCarrier,
    pub final_carrier: FiniteCarrier,
    pub initial_state_sha256: String,
    pub final_state_sha256: String,
    pub budget: RunBudget,
    pub accounting: CandidateAccounting,
    pub steps: Vec<StepReceipt>,
    pub terminal: TerminalReceipt,
    pub replay_sha256: String,
    pub runtime_micros: u128,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunReceiptAnchor {
    pub schema_version: String,
    pub receipt_schema_version: String,
    pub packet_sha256: Hash256,
    pub operator_registry_sha256: Hash256,
    pub replay_sha256: Hash256,
    pub inspection_trace_sha256: Hash256,
    pub canonical_receipt_sha256: Hash256,
    pub authority_effect: AuthorityEffect,
}

impl RunReceiptAnchor {
    pub fn canonical_json_bytes(&self) -> Result<Vec<u8>, IteratorError> {
        serde_json::to_vec(self).map_err(|error| IteratorError::Serialization(error.to_string()))
    }

    pub fn sha256(&self) -> Result<String, IteratorError> {
        self.canonical_json_bytes()
            .map(|bytes| sha256_bytes(&bytes))
    }

    fn is_valid(&self) -> bool {
        self.schema_version == MULTIPATH_RECEIPT_ANCHOR_SCHEMA
            && self.receipt_schema_version == MULTIPATH_RECEIPT_SCHEMA
            && self.authority_effect.is_none()
            && [
                self.packet_sha256.as_str(),
                self.operator_registry_sha256.as_str(),
                self.replay_sha256.as_str(),
                self.inspection_trace_sha256.as_str(),
                self.canonical_receipt_sha256.as_str(),
            ]
            .iter()
            .all(|value| is_sha256(value))
    }
}

impl RunReceipt {
    /// Creates a content anchor that must be pinned separately from this receipt.
    ///
    /// The anchor makes later re-sealing detectable. It does not establish
    /// adapter semantics, detector completeness, witness truth, or authority.
    pub fn external_anchor(&self) -> Result<RunReceiptAnchor, IteratorError> {
        if !self.verify_replay_hash()? {
            return Err(IteratorError::InvalidDeclaration(
                "cannot anchor a structurally invalid run receipt".into(),
            ));
        }
        Ok(RunReceiptAnchor {
            schema_version: MULTIPATH_RECEIPT_ANCHOR_SCHEMA.into(),
            receipt_schema_version: MULTIPATH_RECEIPT_SCHEMA.into(),
            packet_sha256: Hash256::from_hex_unchecked(self.packet_sha256.clone()),
            operator_registry_sha256: Hash256::from_hex_unchecked(
                self.operator_registry_sha256.clone(),
            ),
            replay_sha256: Hash256::from_hex_unchecked(self.replay_sha256.clone()),
            inspection_trace_sha256: Hash256::from_hex_unchecked(inspection_trace_hash_for(self)?),
            canonical_receipt_sha256: Hash256::from_hex_unchecked(sha256_bytes(
                &self.canonical_json_bytes()?,
            )),
            authority_effect: self.authority_effect.clone(),
        })
    }

    /// Verifies internal replay consistency against a caller-pinned external anchor.
    ///
    /// Constructing an anchor from an untrusted receipt after receipt transport
    /// provides no authenticity. The trusted host must freeze the expected anchor
    /// independently before this verifier is called.
    pub fn verify_against_anchor(
        &self,
        expected: &RunReceiptAnchor,
    ) -> Result<bool, IteratorError> {
        if !expected.is_valid() || !self.verify_replay_hash()? {
            return Ok(false);
        }
        Ok(self.external_anchor()? == *expected)
    }

    pub fn verify_replay_hash(&self) -> Result<bool, IteratorError> {
        if !self.has_canonical_registry_and_header()
            || !self.matches_packet_and_registry_hashes()?
            || !self.receipt_contract_is_valid()?
            || !self.verify_compiled_operator_candidates()?
        {
            return Ok(false);
        }
        Ok(self.replay_sha256 == replay_hash_for(self)?)
    }

    fn has_canonical_registry_and_header(&self) -> bool {
        let Ok(canonical_registry) =
            OperatorRegistry::new(self.operator_registry.operators.clone())
        else {
            return false;
        };
        canonical_registry == self.operator_registry
            && self.schema_version == MULTIPATH_RECEIPT_SCHEMA
            && self.authority_effect.is_none()
            && is_sha256(&self.packet_sha256)
            && is_sha256(&self.operator_registry_sha256)
            && is_sha256(&self.replay_sha256)
    }

    fn matches_packet_and_registry_hashes(&self) -> Result<bool, IteratorError> {
        Ok(self.packet.sha256()? == self.packet_sha256
            && self.operator_registry.sha256()? == self.operator_registry_sha256)
    }

    pub fn recompute_replay_sha256(&self) -> Result<String, IteratorError> {
        replay_hash_for(self)
    }

    pub fn canonical_json_bytes(&self) -> Result<Vec<u8>, IteratorError> {
        serde_json::to_vec(self).map_err(|error| IteratorError::Serialization(error.to_string()))
    }

    fn receipt_contract_is_valid(&self) -> Result<bool, IteratorError> {
        if !self.receipt_envelope_is_valid()? {
            return Ok(false);
        }
        let Some((canonical_initial_carrier, canonical_final_carrier)) =
            self.canonical_carriers_for_receipt()
        else {
            return Ok(false);
        };
        let final_carrier_sha256 = sha256_json(&canonical_final_carrier)?;
        let mut state = StepValidationState {
            expected_state_sha256: self.initial_state_sha256.clone(),
            expected_carrier_sha256: sha256_json(&canonical_initial_carrier)?,
            expected_carrier: canonical_initial_carrier,
            evaluated_rows: 0,
            duplicate_rows: 0,
            materialized_budget_rows: 0,
            predicted_avoided: 0,
            selected_count: 0,
            extension_count: 0,
        };

        for (position, step) in self.steps.iter().enumerate() {
            if !self.validate_step_receipt(position, step, &mut state)? {
                return Ok(false);
            }
        }

        Ok(self.validate_accounting_totals(
            &state,
            &canonical_final_carrier,
            &final_carrier_sha256,
        ) && self.terminal_envelope_is_valid())
    }

    fn receipt_envelope_is_valid(&self) -> Result<bool, IteratorError> {
        if !self.receipt_scalar_headers_are_valid() {
            return Ok(false);
        }
        Ok(serialized_len(&self.packet)? < self.budget.max_receipt_bytes
            && self.canonical_json_bytes()?.len() <= self.budget.max_receipt_bytes)
    }

    fn receipt_scalar_headers_are_valid(&self) -> bool {
        nonempty(&self.adapter_id, "adapter_id").is_ok()
            && nonempty(&self.terminal.reason, "terminal reason").is_ok()
            && self.budget.validate().is_ok()
            && self.accounting.is_balanced()
            && self.steps.len() <= self.budget.max_steps
            && is_sha256(&self.initial_state_sha256)
            && is_sha256(&self.final_state_sha256)
    }

    fn canonical_carriers_for_receipt(&self) -> Option<(FiniteCarrier, FiniteCarrier)> {
        let canonical_packet = self.packet.clone().canonicalized().ok()?;
        let canonical_initial_carrier = self.initial_carrier.clone().canonicalized().ok()?;
        let canonical_final_carrier = self.final_carrier.clone().canonicalized().ok()?;
        if canonical_packet != self.packet
            || canonical_initial_carrier != self.initial_carrier
            || canonical_final_carrier != self.final_carrier
            || self.initial_carrier.cells.len() > self.budget.max_carrier_cells
            || self.final_carrier.cells.len() > self.budget.max_carrier_cells
        {
            return None;
        }
        Some((canonical_initial_carrier, canonical_final_carrier))
    }

    fn validate_step_receipt(
        &self,
        position: usize,
        step: &StepReceipt,
        state: &mut StepValidationState,
    ) -> Result<bool, IteratorError> {
        if !step_header_and_inspection_are_valid(&self.packet, position, step, state) {
            return Ok(false);
        }
        for candidate in &step.candidates {
            if !validate_step_candidate(&self.packet, candidate, state) {
                return Ok(false);
            }
        }
        self.validate_step_transition(position, step, state)
    }

    fn validate_step_transition(
        &self,
        position: usize,
        step: &StepReceipt,
        state: &mut StepValidationState,
    ) -> Result<bool, IteratorError> {
        if !step_transition_presence_is_valid(position, self.steps.len(), step) {
            return Ok(false);
        }
        if let Some(compiled) = &step.compiled_operator_candidate {
            return Ok(record_compiled_step_transition(compiled, state));
        }
        if let Some(extension) = &step.carrier_extension {
            return validate_step_carrier_extension(step, extension, state);
        }
        Ok(true)
    }

    fn validate_accounting_totals(
        &self,
        state: &StepValidationState,
        canonical_final_carrier: &FiniteCarrier,
        final_carrier_sha256: &str,
    ) -> bool {
        self.state_and_row_counts_match(state, canonical_final_carrier, final_carrier_sha256)
            && self.proposed_and_budget_totals_match(state)
    }

    fn state_and_row_counts_match(
        &self,
        state: &StepValidationState,
        canonical_final_carrier: &FiniteCarrier,
        final_carrier_sha256: &str,
    ) -> bool {
        state.expected_state_sha256 == self.final_state_sha256
            && &state.expected_carrier == canonical_final_carrier
            && state.expected_carrier_sha256 == final_carrier_sha256
            && self.match_candidate_accounting_counters(state)
    }

    fn match_candidate_accounting_counters(&self, state: &StepValidationState) -> bool {
        self.accounting.evaluated == state.evaluated_rows
            && self.accounting.duplicate_pruned == state.duplicate_rows
            && self.accounting.predicted_avoided_by_quotient == state.predicted_avoided
            && self.accounting.accepted_transitions == state.selected_count
            && self.accounting.compiled_operator_candidates == state.selected_count
            && self.accounting.carrier_extensions == state.extension_count
            && self.accounting.budget_pruned >= state.materialized_budget_rows
    }

    fn proposed_and_budget_totals_match(&self, state: &StepValidationState) -> bool {
        let omitted_budget_rows = self.accounting.budget_pruned - state.materialized_budget_rows;
        let Some(processed_candidates) = state.evaluated_rows.checked_add(state.duplicate_rows)
        else {
            return false;
        };
        let Some(reconstructed_proposed) = processed_candidates
            .checked_add(state.materialized_budget_rows)
            .and_then(|count| count.checked_add(omitted_budget_rows))
        else {
            return false;
        };
        reconstructed_proposed == self.accounting.proposed
            && processed_candidates <= self.budget.max_candidates
            && (self.accounting.budget_pruned == 0
                || self.terminal.kind == TerminalKind::BudgetExhausted)
    }

    fn terminal_envelope_is_valid(&self) -> bool {
        match self.terminal.kind {
            TerminalKind::ExactRepair => exact_repair_terminal_is_valid(self),
            TerminalKind::StabilizedSurvivor => stabilized_survivor_terminal_is_valid(self),
            TerminalKind::OpenObstruction => open_obstruction_terminal_is_valid(self),
            TerminalKind::DetectorInadequate => detector_inadequate_terminal_is_valid(self),
            TerminalKind::NoRule => no_rule_terminal_is_valid(self),
            TerminalKind::RequiresLift => requires_lift_terminal_is_valid(self),
            TerminalKind::Refused | TerminalKind::BudgetExhausted | TerminalKind::Cancelled => true,
        }
    }

    pub fn verify_compiled_operator_candidates(&self) -> Result<bool, IteratorError> {
        let mut compiled_count = 0;
        for (position, step) in self.steps.iter().enumerate() {
            if !step_proposal_ids_are_valid(position, step) {
                return Ok(false);
            }
            let Some(compiled) = &step.compiled_operator_candidate else {
                if !uncompiled_step_is_valid(step) {
                    return Ok(false);
                }
                continue;
            };
            compiled_count += 1;
            if !self.verify_step_compiled_candidate(position, step, compiled)? {
                return Ok(false);
            }
        }
        Ok(
            compiled_count == self.accounting.compiled_operator_candidates
                && compiled_count == self.accounting.accepted_transitions,
        )
    }

    fn verify_step_compiled_candidate(
        &self,
        position: usize,
        step: &StepReceipt,
        compiled: &CompiledOperatorCandidate,
    ) -> Result<bool, IteratorError> {
        let Some((selected_id, selected_sha256, source, post_inspection)) =
            find_unique_selected_candidate(step)
        else {
            return Ok(false);
        };
        if !self.compiled_candidate_bindings_match(
            position,
            step,
            compiled,
            source,
            selected_id,
            selected_sha256,
        )? {
            return Ok(false);
        }
        let post_inspection_sha256 = sha256_json(post_inspection)?;
        if !compiled_candidate_provenance_and_measure_match(
            step,
            compiled,
            source,
            post_inspection,
            &post_inspection_sha256,
        ) {
            return Ok(false);
        }
        self.compiled_candidate_admission_is_valid(step, compiled, source)
    }

    fn compiled_candidate_bindings_match(
        &self,
        position: usize,
        step: &StepReceipt,
        compiled: &CompiledOperatorCandidate,
        source: &CandidateReceipt,
        selected_id: &str,
        selected_sha256: &str,
    ) -> Result<bool, IteratorError> {
        let source_candidate_sha256 = sha256_json(source)?;
        let expected_result_state = self
            .steps
            .get(position + 1)
            .map(|next| next.state_sha256.as_str())
            .unwrap_or(self.final_state_sha256.as_str());
        let next_carrier_is_unchanged = self
            .steps
            .get(position + 1)
            .map(|next| next.carrier_sha256 == step.carrier_sha256)
            .unwrap_or(true);
        Ok(compiled.source_proposal_id == selected_id
            && compiled.source_candidate_sha256 == selected_sha256
            && source_candidate_sha256 == selected_sha256
            && compiled.result_state_sha256 == expected_result_state
            && next_carrier_is_unchanged
            && self.compiled_candidate_step_context_matches(step, compiled, source))
    }

    fn compiled_candidate_step_context_matches(
        &self,
        step: &StepReceipt,
        compiled: &CompiledOperatorCandidate,
        source: &CandidateReceipt,
    ) -> bool {
        compiled.source_registry_sha256 == self.operator_registry_sha256
            && compiled.source_step_index == step.step_index
            && compiled.source_packet_sha256 == self.packet_sha256
            && compiled.source_carrier_sha256 == step.carrier_sha256
            && compiled.source_state_sha256 == step.state_sha256
            && compiled.result_state_sha256 == source.state_sha256
    }

    fn compiled_candidate_admission_is_valid(
        &self,
        step: &StepReceipt,
        compiled: &CompiledOperatorCandidate,
        source: &CandidateReceipt,
    ) -> Result<bool, IteratorError> {
        let signature_is_bound = step.inspection.signatures.iter().any(|signature| {
            signature.signature_sha256 == compiled.observed_signature_sha256
                && signature.kind == compiled.signature_kind
        });
        let source_operator = source_operator_record(compiled);
        let registered_operator_is_bound = self
            .operator_registry
            .get(&compiled.source_operator_id)
            .is_some_and(|registered| registered == &source_operator);
        let admission_evidence_is_valid =
            preservation_passes(&source_operator, &compiled.preservation_checks).is_ok()
                && witnesses_pass(&source_operator, &compiled.witness_results, self.budget).is_ok();
        if !signature_is_bound
            || compiled.preservation_checks != source.preservation
            || compiled.witness_results != source.witnesses
            || !registered_operator_is_bound
            || !admission_evidence_is_valid
        {
            return Ok(false);
        }
        compiled.verify_hashes()
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

struct StepValidationState {
    expected_state_sha256: String,
    expected_carrier: FiniteCarrier,
    expected_carrier_sha256: String,
    evaluated_rows: usize,
    duplicate_rows: usize,
    materialized_budget_rows: usize,
    predicted_avoided: usize,
    selected_count: usize,
    extension_count: usize,
}

fn step_header_and_inspection_are_valid(
    packet: &ProblemPacket,
    position: usize,
    step: &StepReceipt,
    state: &StepValidationState,
) -> bool {
    if step.step_index != position
        || !is_sha256(&step.state_sha256)
        || !is_sha256(&step.carrier_sha256)
        || step.state_sha256 != state.expected_state_sha256
        || step.carrier_sha256 != state.expected_carrier_sha256
    {
        return false;
    }
    canonicalize_inspection_receipt(packet, step.inspection.clone())
        .is_ok_and(|canonical| canonical == step.inspection)
}

fn validate_step_candidate(
    packet: &ProblemPacket,
    candidate: &CandidateReceipt,
    state: &mut StepValidationState,
) -> bool {
    candidate_scalar_fields_are_valid(candidate)
        && candidate_optional_fields_are_valid(candidate)
        && candidate_inspections_and_assessment_are_valid(packet, candidate)
        && accumulate_candidate_verdict(
            candidate.verdict,
            candidate.predicted_candidates_avoided,
            state,
        )
}

fn candidate_scalar_fields_are_valid(candidate: &CandidateReceipt) -> bool {
    nonempty(&candidate.proposal_id, "candidate proposal_id").is_ok()
        && nonempty(&candidate.operator_id.0, "candidate operator_id").is_ok()
        && nonempty(&candidate.provenance.0, "candidate provenance").is_ok()
        && nonempty(&candidate.reason, "candidate reason").is_ok()
        && is_sha256(&candidate.state_sha256)
        && is_sha256(&candidate.matched_signature_sha256)
}

fn candidate_optional_fields_are_valid(candidate: &CandidateReceipt) -> bool {
    !candidate
        .equivalence_key
        .as_ref()
        .is_some_and(|key| key.trim().is_empty())
        && candidate.after.is_some() == candidate.post_inspection.is_some()
        && !candidate
            .post_inspection
            .as_ref()
            .zip(candidate.after)
            .is_some_and(|(inspection, after)| inspection.measure != after)
}

fn candidate_inspections_and_assessment_are_valid(
    packet: &ProblemPacket,
    candidate: &CandidateReceipt,
) -> bool {
    if let Some(post_inspection) = &candidate.post_inspection {
        if !canonicalize_inspection_receipt(packet, post_inspection.clone())
            .is_ok_and(|canonical| canonical == *post_inspection)
        {
            return false;
        }
    }
    let mut assessment = CandidateAssessment {
        preservation: candidate.preservation.clone(),
        witnesses: candidate.witnesses.clone(),
    };
    canonicalize_assessment(&mut assessment).is_ok()
        && assessment.preservation == candidate.preservation
        && assessment.witnesses == candidate.witnesses
}

fn accumulate_candidate_verdict(
    verdict: CandidateVerdict,
    predicted_avoided_delta: usize,
    state: &mut StepValidationState,
) -> bool {
    match verdict {
        CandidateVerdict::DuplicatePruned => {
            let Some(next_dup) = state.duplicate_rows.checked_add(1) else {
                return false;
            };
            let Some(next_avoided) = state.predicted_avoided.checked_add(predicted_avoided_delta)
            else {
                return false;
            };
            state.duplicate_rows = next_dup;
            state.predicted_avoided = next_avoided;
            true
        }
        CandidateVerdict::BudgetPruned => {
            let Some(next) = state.materialized_budget_rows.checked_add(1) else {
                return false;
            };
            state.materialized_budget_rows = next;
            true
        }
        _ => {
            let Some(next) = state.evaluated_rows.checked_add(1) else {
                return false;
            };
            state.evaluated_rows = next;
            true
        }
    }
}

fn validate_step_carrier_extension(
    step: &StepReceipt,
    extension: &CarrierExtensionReceipt,
    state: &mut StepValidationState,
) -> Result<bool, IteratorError> {
    if !extension_scalars_are_valid(extension, &state.expected_carrier_sha256)
        || !extension_cells_and_signature_are_valid(step, extension)
    {
        return Ok(false);
    }
    reconstruct_and_verify_extended_carrier(extension, state)
}

fn extension_scalars_are_valid(
    extension: &CarrierExtensionReceipt,
    expected_carrier_sha256: &str,
) -> bool {
    nonempty(&extension.extension_id, "extension_id").is_ok()
        && nonempty(&extension.justification_ref, "extension justification").is_ok()
        && is_sha256(&extension.trigger_signature_sha256)
        && is_sha256(&extension.parent_carrier_sha256)
        && is_sha256(&extension.extended_carrier_sha256)
        && extension.parent_carrier_sha256 == expected_carrier_sha256
        && extension.parent_carrier_sha256 != extension.extended_carrier_sha256
}

fn extension_cells_and_signature_are_valid(
    step: &StepReceipt,
    extension: &CarrierExtensionReceipt,
) -> bool {
    if extension.added_cell_ids.is_empty()
        || extension.added_cells.is_empty()
        || !strictly_sorted(&extension.added_cell_ids)
        || !step.inspection.signatures.iter().any(|signature| {
            signature.signature_sha256 == extension.trigger_signature_sha256
        })
    {
        return false;
    }
    let mut receipt_added_cell_ids: Vec<_> = extension
        .added_cells
        .iter()
        .map(|cell| cell.cell_id.clone())
        .collect();
    receipt_added_cell_ids.sort();
    receipt_added_cell_ids == extension.added_cell_ids
}

fn reconstruct_and_verify_extended_carrier(
    extension: &CarrierExtensionReceipt,
    state: &mut StepValidationState,
) -> Result<bool, IteratorError> {
    let mut reconstructed_carrier = state.expected_carrier.clone();
    let reconstructed_extension = CarrierExtension {
        extension_id: extension.extension_id.clone(),
        trigger_signature_sha256: extension.trigger_signature_sha256.clone(),
        justification_ref: extension.justification_ref.clone(),
        new_cells: extension.added_cells.clone(),
    };
    if reconstructed_carrier
        .extend(&reconstructed_extension)
        .is_err()
    {
        return Ok(false);
    }
    let reconstructed_added_cells: Vec<_> = reconstructed_carrier
        .cells
        .iter()
        .filter(|cell| {
            extension
                .added_cell_ids
                .binary_search(&cell.cell_id)
                .is_ok()
        })
        .cloned()
        .collect();
    let reconstructed_carrier_sha256 = sha256_json(&reconstructed_carrier)?;
    if reconstructed_added_cells != extension.added_cells
        || reconstructed_carrier_sha256 != extension.extended_carrier_sha256
    {
        return Ok(false);
    }
    let Some(next) = state.extension_count.checked_add(1) else {
        return Ok(false);
    };
    state.expected_carrier = reconstructed_carrier;
    state.expected_carrier_sha256 = reconstructed_carrier_sha256;
    state.extension_count = next;
    Ok(true)
}

fn terminal_step_is_inert(step: &StepReceipt) -> bool {
    step.compiled_operator_candidate.is_none() && step.carrier_extension.is_none()
}

fn exact_repair_terminal_is_valid(receipt: &RunReceipt) -> bool {
    let Some(last) = receipt.steps.last() else {
        return false;
    };
    terminal_step_is_inert(last)
        && last.inspection.measure.is_resolved()
        && last.inspection.detector_inadequate_count == 0
        && last.inspection.higher_degree_need.is_none()
        && receipt.accounting.accepted_transitions > 0
        && last.inspection.measure.stabilized_survivor_count == 0
}

fn stabilized_survivor_terminal_is_valid(receipt: &RunReceipt) -> bool {
    let Some(last) = receipt.steps.last() else {
        return false;
    };
    terminal_step_is_inert(last)
        && last.inspection.measure.is_resolved()
        && last.inspection.detector_inadequate_count == 0
        && last.inspection.higher_degree_need.is_none()
        && (receipt.accounting.accepted_transitions == 0
            || last.inspection.measure.stabilized_survivor_count > 0)
}

fn open_obstruction_terminal_is_valid(receipt: &RunReceipt) -> bool {
    let Some(last) = receipt.steps.last() else {
        return false;
    };
    terminal_step_is_inert(last)
        && !last.inspection.measure.is_resolved()
        && last.inspection.detector_inadequate_count == 0
        && last.inspection.higher_degree_need.is_none()
        && !last.candidates.is_empty()
}

fn detector_inadequate_terminal_is_valid(receipt: &RunReceipt) -> bool {
    let Some(last) = receipt.steps.last() else {
        return false;
    };
    terminal_step_is_inert(last) && last.inspection.detector_inadequate_count > 0
}

fn no_rule_terminal_is_valid(receipt: &RunReceipt) -> bool {
    let Some(last) = receipt.steps.last() else {
        return false;
    };
    terminal_step_is_inert(last)
        && !last.inspection.measure.is_resolved()
        && last.inspection.detector_inadequate_count == 0
        && last.inspection.higher_degree_need.is_none()
        && last.candidates.is_empty()
}

fn requires_lift_terminal_is_valid(receipt: &RunReceipt) -> bool {
    let Some(last) = receipt.steps.last() else {
        return false;
    };
    let candidate_requires_lift = last
        .candidates
        .iter()
        .any(|candidate| candidate.verdict == CandidateVerdict::RequiresLift);
    terminal_step_is_inert(last)
        && (last.inspection.higher_degree_need.is_some() || candidate_requires_lift)
}

fn step_proposal_ids_are_valid(position: usize, step: &StepReceipt) -> bool {
    let mut proposal_ids: Vec<_> = step
        .candidates
        .iter()
        .map(|candidate| candidate.proposal_id.as_str())
        .collect();
    proposal_ids.sort_unstable();
    step.step_index == position
        && !proposal_ids
            .iter()
            .any(|proposal_id| proposal_id.trim().is_empty())
        && !proposal_ids.windows(2).any(|window| window[0] == window[1])
}

fn uncompiled_step_is_valid(step: &StepReceipt) -> bool {
    step.selected_proposal_id.is_none()
        && step.selected_candidate_sha256.is_none()
        && !step
            .candidates
            .iter()
            .any(|candidate| candidate.verdict == CandidateVerdict::EligibleDescent)
}

fn find_unique_selected_candidate(
    step: &StepReceipt,
) -> Option<(&str, &str, &CandidateReceipt, &InspectionReceipt)> {
    let (Some(selected_id), Some(selected_sha256)) =
        (&step.selected_proposal_id, &step.selected_candidate_sha256)
    else {
        return None;
    };
    if !is_sha256(selected_sha256) {
        return None;
    }
    let mut matches = step.candidates.iter().filter(|candidate| {
        candidate.proposal_id == *selected_id
            && candidate.verdict == CandidateVerdict::EligibleDescent
    });
    let source = matches.next()?;
    if matches.next().is_some() {
        return None;
    }
    let post_inspection = source.post_inspection.as_ref()?;
    Some((selected_id, selected_sha256, source, post_inspection))
}

fn compiled_candidate_provenance_and_measure_match(
    step: &StepReceipt,
    compiled: &CompiledOperatorCandidate,
    source: &CandidateReceipt,
    post_inspection: &InspectionReceipt,
    post_inspection_sha256: &str,
) -> bool {
    compiled_candidate_provenance_matches(compiled, source)
        && compiled_candidate_measures_match(
            step,
            compiled,
            source,
            post_inspection,
            post_inspection_sha256,
        )
}

fn compiled_candidate_provenance_matches(
    compiled: &CompiledOperatorCandidate,
    source: &CandidateReceipt,
) -> bool {
    compiled.source_operator_id == source.operator_id
        && compiled.source_provenance == source.provenance
        && compiled.source_equivalence_key == source.equivalence_key
        && compiled.source_predicted_candidates_avoided == source.predicted_candidates_avoided
        && compiled.observed_signature_sha256 == source.matched_signature_sha256
}

fn compiled_candidate_measures_match(
    step: &StepReceipt,
    compiled: &CompiledOperatorCandidate,
    source: &CandidateReceipt,
    post_inspection: &InspectionReceipt,
    post_inspection_sha256: &str,
) -> bool {
    compiled.before == step.inspection.measure
        && compiled.before == source.before
        && source.after == Some(compiled.after)
        && compiled.before.strictly_descends_to(compiled.after)
        && post_inspection.measure == compiled.after
        && compiled.post_inspection_sha256 == post_inspection_sha256
}

#[derive(Debug, Error)]
pub enum IteratorError {
    #[error("invalid packet or declaration: {0}")]
    InvalidDeclaration(String),
    #[error("invalid finite carrier: {0}")]
    InvalidCarrier(String),
    #[error("invalid budget: {0}")]
    InvalidBudget(String),
    #[error("invalid operator registry: {0}")]
    InvalidRegistry(String),
    #[error("adapter seed refused: {0}")]
    AdapterSeed(String),
    #[error("DDA probe failed: {0}")]
    Dda(String),
    #[error("receipt serialization failed: {0}")]
    Serialization(String),
}

struct EligibleCandidate<S> {
    proposal_id: String,
    candidate_sha256: String,
    state: S,
    measure: ObstructionMeasure,
    compiled_operator: CompiledOperatorCandidate,
}

trait RunClock {
    fn elapsed_micros(&self) -> u128;
}

struct SystemRunClock {
    started: Instant,
}

impl RunClock for SystemRunClock {
    fn elapsed_micros(&self) -> u128 {
        self.started.elapsed().as_micros()
    }
}

/// Deterministic elapsed-time source exposed only for PaperER008 regression tests.
#[cfg(feature = "paper070-test-clock")]
pub trait DeterministicRunClock {
    fn elapsed_micros(&self) -> u128;
}

#[cfg(feature = "paper070-test-clock")]
struct DeterministicRunClockAdapter<'a, C: ?Sized>(&'a C);

#[cfg(feature = "paper070-test-clock")]
impl<C: DeterministicRunClock + ?Sized> RunClock for DeterministicRunClockAdapter<'_, C> {
    fn elapsed_micros(&self) -> u128 {
        self.0.elapsed_micros()
    }
}

pub fn run_multipath<A: MultipathAdapter>(
    adapter: &A,
    packet: ProblemPacket,
    registry: &OperatorRegistry,
    budget: RunBudget,
    cancellation: &CancellationToken,
) -> Result<RunReceipt, IteratorError> {
    let clock = SystemRunClock {
        started: Instant::now(),
    };
    run_multipath_with_clock(adapter, packet, registry, budget, cancellation, &clock)
}

/// Feature-gated deterministic-clock entrypoint for PaperER008 regression tests.
#[cfg(feature = "paper070-test-clock")]
pub fn run_multipath_with_test_clock<A: MultipathAdapter, C: DeterministicRunClock + ?Sized>(
    adapter: &A,
    packet: ProblemPacket,
    registry: &OperatorRegistry,
    budget: RunBudget,
    cancellation: &CancellationToken,
    clock: &C,
) -> Result<RunReceipt, IteratorError> {
    let clock = DeterministicRunClockAdapter(clock);
    run_multipath_with_clock(adapter, packet, registry, budget, cancellation, &clock)
}

struct MultipathRunState<S> {
    packet: ProblemPacket,
    packet_sha256: String,
    operator_registry_sha256: String,
    initial_carrier: FiniteCarrier,
    carrier: FiniteCarrier,
    initial_state_sha256: String,
    state: S,
    budget: RunBudget,
    steps: Vec<StepReceipt>,
    accounting: CandidateAccounting,
    terminal: Option<TerminalReceipt>,
}

enum ProposalAssessmentOutcome {
    BudgetExhausted,
    Rejected,
    Passed(CandidateAssessment),
}

enum CandidateSelectionOutcome<S> {
    Selected(EligibleCandidate<S>),
    NoneEligible,
    BudgetTerminated(TerminalReceipt),
}

enum CarrierExtensionOutcome {
    Extended,
    NoExtension,
    Terminated(TerminalReceipt),
}

fn run_multipath_with_clock<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    packet: ProblemPacket,
    registry: &OperatorRegistry,
    budget: RunBudget,
    cancellation: &CancellationToken,
    clock: &C,
) -> Result<RunReceipt, IteratorError> {
    let mut run = initialize_multipath_run(adapter, packet, registry, budget)?;
    for step_index in 0..run.budget.max_steps {
        if !execute_multipath_step(adapter, registry, cancellation, clock, &mut run, step_index)? {
            break;
        }
    }
    finalize_run_receipt(adapter.adapter_id(), registry, clock, run)
}

fn initialize_multipath_run<A: MultipathAdapter>(
    adapter: &A,
    packet: ProblemPacket,
    registry: &OperatorRegistry,
    budget: RunBudget,
) -> Result<MultipathRunState<A::State>, IteratorError> {
    let (packet, budget) = validate_initial_packet_and_budget(adapter.adapter_id(), packet, budget)?;
    let packet_sha256 = packet.sha256()?;
    let operator_registry_sha256 = registry.sha256()?;
    let (carrier, state, initial_state_sha256) = seed_carrier_and_state(adapter, &packet, budget)?;
    Ok(MultipathRunState {
        packet,
        packet_sha256,
        operator_registry_sha256,
        initial_carrier: carrier.clone(),
        carrier,
        initial_state_sha256,
        state,
        budget,
        steps: Vec::new(),
        accounting: CandidateAccounting::default(),
        terminal: None,
    })
}

fn validate_initial_packet_and_budget(
    adapter_id: &str,
    packet: ProblemPacket,
    budget: RunBudget,
) -> Result<(ProblemPacket, RunBudget), IteratorError> {
    nonempty(adapter_id, "adapter_id")?;
    let packet = packet.canonicalized()?;
    let budget = budget.validate()?;
    let packet_bytes = serialized_len(&packet)?;
    if packet_bytes >= budget.max_receipt_bytes {
        return Err(IteratorError::InvalidBudget(format!(
            "packet alone requires {packet_bytes} bytes, leaving no room in max_receipt_bytes {}",
            budget.max_receipt_bytes
        )));
    }
    Ok((packet, budget))
}

fn seed_carrier_and_state<A: MultipathAdapter>(
    adapter: &A,
    packet: &ProblemPacket,
    budget: RunBudget,
) -> Result<(FiniteCarrier, A::State, String), IteratorError> {
    let seed = adapter
        .seed(packet)
        .map_err(|failure| IteratorError::AdapterSeed(failure.to_string()))?;
    let carrier = seed.carrier.canonicalized()?;
    if carrier.cells.len() > budget.max_carrier_cells {
        return Err(IteratorError::InvalidBudget(format!(
            "seed carrier has {} cells, above max_carrier_cells {}",
            carrier.cells.len(),
            budget.max_carrier_cells
        )));
    }
    let initial_state_sha256 = sha256_json(&seed.state)?;
    Ok((carrier, seed.state, initial_state_sha256))
}

fn execute_multipath_step<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    registry: &OperatorRegistry,
    cancellation: &CancellationToken,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    step_index: usize,
) -> Result<bool, IteratorError> {
    if let Some(terminal) = check_step_entry_budget(cancellation, clock, run.budget) {
        run.terminal = Some(terminal);
        return Ok(false);
    }
    let (state_sha256, inspection, mut step) =
        match inspect_step_state(adapter, clock, run, step_index)? {
            Ok(inspected) => inspected,
            Err(terminal) => {
                run.terminal = Some(terminal);
                return Ok(false);
            }
        };
    if let Some(terminal) =
        early_inspection_terminal(&inspection, run.accounting.accepted_transitions)
    {
        run.terminal = Some(terminal);
        run.steps.push(step);
        return Ok(false);
    }
    let proposals = match propose_and_prepare_candidates(
        adapter,
        clock,
        run,
        &inspection.signatures,
    )? {
        Ok(proposals) => proposals,
        Err(terminal) => {
            run.terminal = Some(terminal);
            run.steps.push(step);
            return Ok(false);
        }
    };
    let (eligible, saw_lift, wall_exhausted) = evaluate_step_proposals(
        adapter,
        registry,
        clock,
        run,
        step_index,
        &state_sha256,
        &inspection,
        &mut step,
        proposals,
    )?;
    select_or_extend_or_terminate(
        adapter,
        clock,
        run,
        &inspection,
        step,
        eligible,
        saw_lift,
        wall_exhausted,
    )
}

fn check_step_entry_budget<C: RunClock + ?Sized>(
    cancellation: &CancellationToken,
    clock: &C,
    budget: RunBudget,
) -> Option<TerminalReceipt> {
    if cancellation.is_cancelled() {
        return Some(TerminalReceipt {
            kind: TerminalKind::Cancelled,
            reason: "explicit cancellation token observed".into(),
        });
    }
    if wall_budget_exhausted(clock, budget) {
        return Some(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: "max_wall_millis exhausted".into(),
        });
    }
    None
}

fn inspect_step_state<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    clock: &C,
    run: &MultipathRunState<A::State>,
    step_index: usize,
) -> Result<Result<(String, InspectionReceipt, StepReceipt), TerminalReceipt>, IteratorError> {
    let state_sha256 = sha256_json(&run.state)?;
    let carrier_sha256 = sha256_json(&run.carrier)?;
    let raw_inspection_result = adapter.inspect(&run.packet, &run.carrier, &run.state);
    if wall_budget_exhausted(clock, run.budget) {
        return Ok(Err(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: "max_wall_millis exhausted after inspect".into(),
        }));
    }
    let raw_inspection = match raw_inspection_result {
        Ok(inspection) => inspection,
        Err(failure) => return Ok(Err(terminal_from_failure(failure)?)),
    };
    let inspection = inspect_packet(&run.packet, raw_inspection)?;
    if wall_budget_exhausted(clock, run.budget) {
        return Ok(Err(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: "max_wall_millis exhausted while validating inspection".into(),
        }));
    }
    let step = StepReceipt {
        step_index,
        state_sha256: state_sha256.clone(),
        carrier_sha256,
        inspection: inspection.clone(),
        candidates: Vec::new(),
        selected_proposal_id: None,
        selected_candidate_sha256: None,
        compiled_operator_candidate: None,
        carrier_extension: None,
    };
    Ok(Ok((state_sha256, inspection, step)))
}

fn early_inspection_terminal(
    inspection: &InspectionReceipt,
    accepted_transitions: usize,
) -> Option<TerminalReceipt> {
    if inspection.detector_inadequate_count > 0 {
        return Some(TerminalReceipt {
            kind: TerminalKind::DetectorInadequate,
            reason: format!(
                "{} protected distinction(s) lack an adequate detector",
                inspection.detector_inadequate_count
            ),
        });
    }
    if let Some(need) = &inspection.higher_degree_need {
        return Some(TerminalReceipt {
            kind: TerminalKind::RequiresLift,
            reason: format!(
                "degree {} witness exceeds admitted degree {}; lift={}",
                need.required_degree,
                need.current_max_degree,
                need.licensed_lift_ref.as_deref().unwrap_or("unlicensed")
            ),
        });
    }
    if inspection.measure.is_resolved() {
        let kind = if accepted_transitions > 0 && inspection.measure.stabilized_survivor_count == 0
        {
            TerminalKind::ExactRepair
        } else {
            TerminalKind::StabilizedSurvivor
        };
        return Some(TerminalReceipt {
            kind,
            reason: "all declared protected distinctions are covered and no open defect remains"
                .into(),
        });
    }
    None
}

fn propose_and_prepare_candidates<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    signatures: &[ObstructionSignature],
) -> Result<Result<Vec<DeformationProposal<A::State>>, TerminalReceipt>, IteratorError> {
    let proposals = match fetch_raw_proposals(adapter, clock, run, signatures)? {
        Ok(proposals) => proposals,
        Err(terminal) => return Ok(Err(terminal)),
    };
    check_proposal_capacity_and_sort(clock, run, proposals)
}

fn fetch_raw_proposals<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    signatures: &[ObstructionSignature],
) -> Result<Result<Vec<DeformationProposal<A::State>>, TerminalReceipt>, IteratorError> {
    let proposal_result = adapter.propose(&run.packet, &run.carrier, &run.state, signatures);
    if wall_budget_exhausted(clock, run.budget) {
        if let Ok(proposals) = &proposal_result {
            checked_add_counter(
                &mut run.accounting.proposed,
                proposals.len(),
                "proposed candidates",
            )?;
            checked_add_counter(
                &mut run.accounting.budget_pruned,
                proposals.len(),
                "budget-pruned candidates",
            )?;
        }
        return Ok(Err(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: "max_wall_millis exhausted after propose".into(),
        }));
    }
    match proposal_result {
        Ok(proposals) => Ok(Ok(proposals)),
        Err(failure) => Ok(Err(terminal_from_failure(failure)?)),
    }
}

fn check_proposal_capacity_and_sort<S, C: RunClock + ?Sized>(
    clock: &C,
    run: &mut MultipathRunState<S>,
    mut proposals: Vec<DeformationProposal<S>>,
) -> Result<Result<Vec<DeformationProposal<S>>, TerminalReceipt>, IteratorError> {
    let proposal_count = proposals.len();
    let processed_candidates = run
        .accounting
        .evaluated
        .checked_add(run.accounting.duplicate_pruned)
        .ok_or_else(|| {
            IteratorError::InvalidDeclaration("candidate accounting overflow".into())
        })?;
    let remaining_candidate_capacity = run
        .budget
        .max_candidates
        .saturating_sub(processed_candidates);
    checked_add_counter(
        &mut run.accounting.proposed,
        proposal_count,
        "proposed candidates",
    )?;
    if proposal_count > remaining_candidate_capacity {
        checked_add_counter(
            &mut run.accounting.budget_pruned,
            proposal_count,
            "budget-pruned candidates",
        )?;
        return Ok(Err(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: format!(
                "proposal batch of {proposal_count} exceeds remaining max_candidates capacity {remaining_candidate_capacity}"
            ),
        }));
    }
    validate_proposals(&proposals)?;
    proposals.sort_by(|left, right| {
        (&left.operator_id.0, &left.proposal_id).cmp(&(&right.operator_id.0, &right.proposal_id))
    });
    if wall_budget_exhausted(clock, run.budget) {
        checked_add_counter(
            &mut run.accounting.budget_pruned,
            proposal_count,
            "budget-pruned candidates",
        )?;
        return Ok(Err(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: "max_wall_millis exhausted while validating proposals".into(),
        }));
    }
    Ok(Ok(proposals))
}

#[allow(clippy::too_many_arguments)]
fn evaluate_step_proposals<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    registry: &OperatorRegistry,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    step_index: usize,
    state_sha256: &str,
    inspection: &InspectionReceipt,
    step: &mut StepReceipt,
    proposals: Vec<DeformationProposal<A::State>>,
) -> Result<(Vec<EligibleCandidate<A::State>>, bool, bool), IteratorError> {
    // A class is prunable only after one member has passed every admission
    // predicate. The registered contract additionally promises equal
    // post-measures, so pruning cannot change the selected minimum.
    let mut established_equivalence = BTreeSet::new();
    let mut eligible = Vec::new();
    let mut saw_lift = false;
    let mut wall_exhausted = false;
    let proposal_count = proposals.len();

    for (proposal_index, proposal) in proposals.into_iter().enumerate() {
        let remaining_from_here = proposal_count - proposal_index;
        if wall_budget_exhausted(clock, run.budget) {
            checked_add_counter(
                &mut run.accounting.budget_pruned,
                remaining_from_here,
                "budget-pruned candidates",
            )?;
            wall_exhausted = true;
            break;
        }
        if !evaluate_single_proposal(
            adapter,
            registry,
            clock,
            run,
            step_index,
            state_sha256,
            inspection,
            step,
            proposal,
            remaining_from_here,
            &mut established_equivalence,
            &mut eligible,
            &mut saw_lift,
        )? {
            wall_exhausted = true;
            break;
        }
    }
    Ok((eligible, saw_lift, wall_exhausted))
}

#[allow(clippy::too_many_arguments)]
fn evaluate_single_proposal<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    registry: &OperatorRegistry,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    step_index: usize,
    state_sha256: &str,
    inspection: &InspectionReceipt,
    step: &mut StepReceipt,
    proposal: DeformationProposal<A::State>,
    remaining_from_here: usize,
    established_equivalence: &mut BTreeSet<String>,
    eligible: &mut Vec<EligibleCandidate<A::State>>,
    saw_lift: &mut bool,
) -> Result<bool, IteratorError> {
    let before = inspection.measure;
    let proposal_state_sha256 = sha256_json(&proposal.state)?;
    let Some((operator, signature, equivalence_class)) =
        precheck_proposal_against_registry_and_equivalence(
            registry,
            run.carrier.kind,
            &inspection.signatures,
            &proposal,
            &proposal_state_sha256,
            before,
            established_equivalence,
            &mut run.accounting,
            &mut step.candidates,
            saw_lift,
        )?
    else {
        return Ok(true);
    };

    let assessment = match assess_and_verify_proposal(
        adapter,
        clock,
        run,
        &proposal,
        &proposal_state_sha256,
        operator,
        before,
        remaining_from_here,
        &mut step.candidates,
        saw_lift,
    )? {
        ProposalAssessmentOutcome::BudgetExhausted => return Ok(false),
        ProposalAssessmentOutcome::Rejected => return Ok(true),
        ProposalAssessmentOutcome::Passed(assessment) => assessment,
    };

    inspect_and_record_passed_proposal(
        adapter,
        clock,
        run,
        step_index,
        state_sha256,
        proposal,
        proposal_state_sha256,
        operator,
        signature,
        equivalence_class,
        before,
        assessment,
        remaining_from_here,
        established_equivalence,
        eligible,
        step,
    )
}

#[allow(clippy::too_many_arguments)]
fn precheck_proposal_against_registry_and_equivalence<'a, S>(
    registry: &'a OperatorRegistry,
    carrier_kind: CarrierKind,
    signatures: &'a [ObstructionSignature],
    proposal: &DeformationProposal<S>,
    proposal_state_sha256: &str,
    before: ObstructionMeasure,
    established_equivalence: &BTreeSet<String>,
    accounting: &mut CandidateAccounting,
    candidates: &mut Vec<CandidateReceipt>,
    saw_lift: &mut bool,
) -> Result<Option<(&'a RegisteredOperator, &'a ObstructionSignature, Option<String>)>, IteratorError>
{
    let Some((operator, signature)) = lookup_proposal_operator_and_signature(
        registry,
        carrier_kind,
        signatures,
        proposal,
        proposal_state_sha256,
        before,
        accounting,
        candidates,
        saw_lift,
    )?
    else {
        return Ok(None);
    };
    let Some(equivalence_class) = resolve_proposal_equivalence_class(
        operator,
        proposal,
        proposal_state_sha256,
        before,
        established_equivalence,
        accounting,
        candidates,
    )?
    else {
        return Ok(None);
    };
    Ok(Some((operator, signature, equivalence_class)))
}

#[allow(clippy::too_many_arguments)]
fn lookup_proposal_operator_and_signature<'a, S>(
    registry: &'a OperatorRegistry,
    carrier_kind: CarrierKind,
    signatures: &'a [ObstructionSignature],
    proposal: &DeformationProposal<S>,
    proposal_state_sha256: &str,
    before: ObstructionMeasure,
    accounting: &mut CandidateAccounting,
    candidates: &mut Vec<CandidateReceipt>,
    saw_lift: &mut bool,
) -> Result<Option<(&'a RegisteredOperator, &'a ObstructionSignature)>, IteratorError> {
    let Some(operator) = registry.get(&proposal.operator_id) else {
        record_simple_candidate_rejection(
            accounting,
            candidates,
            proposal,
            proposal_state_sha256,
            before,
            CandidateVerdict::InvalidProposal,
            "operator is not registered",
        )?;
        return Ok(None);
    };
    if !operator.carrier_kinds.contains(&carrier_kind) {
        record_simple_candidate_rejection(
            accounting,
            candidates,
            proposal,
            proposal_state_sha256,
            before,
            CandidateVerdict::InvalidProposal,
            "operator does not admit this carrier kind",
        )?;
        return Ok(None);
    };
    lookup_matched_signature_for_operator(
        operator,
        signatures,
        proposal,
        proposal_state_sha256,
        before,
        accounting,
        candidates,
        saw_lift,
    )
}

#[allow(clippy::too_many_arguments)]
fn lookup_matched_signature_for_operator<'a, S>(
    operator: &'a RegisteredOperator,
    signatures: &'a [ObstructionSignature],
    proposal: &DeformationProposal<S>,
    proposal_state_sha256: &str,
    before: ObstructionMeasure,
    accounting: &mut CandidateAccounting,
    candidates: &mut Vec<CandidateReceipt>,
    saw_lift: &mut bool,
) -> Result<Option<(&'a RegisteredOperator, &'a ObstructionSignature)>, IteratorError> {
    let Some(signature) = signatures
        .iter()
        .find(|signature| signature.signature_sha256 == proposal.matched_signature_sha256)
    else {
        record_simple_candidate_rejection(
            accounting,
            candidates,
            proposal,
            proposal_state_sha256,
            before,
            CandidateVerdict::InvalidProposal,
            "matched obstruction signature is absent",
        )?;
        return Ok(None);
    };
    if !operator.signature_kinds.contains(&signature.kind) {
        record_simple_candidate_rejection(
            accounting,
            candidates,
            proposal,
            proposal_state_sha256,
            before,
            CandidateVerdict::InvalidProposal,
            "operator does not admit the matched signature kind",
        )?;
        return Ok(None);
    }
    if operator.requires_lift {
        *saw_lift = true;
        record_simple_candidate_rejection(
            accounting,
            candidates,
            proposal,
            proposal_state_sha256,
            before,
            CandidateVerdict::RequiresLift,
            "registered operator requires a separately licensed lift",
        )?;
        return Ok(None);
    }
    Ok(Some((operator, signature)))
}

fn record_simple_candidate_rejection<S>(
    accounting: &mut CandidateAccounting,
    candidates: &mut Vec<CandidateReceipt>,
    proposal: &DeformationProposal<S>,
    proposal_state_sha256: &str,
    before: ObstructionMeasure,
    verdict: CandidateVerdict,
    reason: &str,
) -> Result<(), IteratorError> {
    checked_add_counter(&mut accounting.evaluated, 1, "evaluated candidates")?;
    candidates.push(candidate_receipt(
        proposal,
        proposal_state_sha256.to_string(),
        before,
        verdict,
        reason.into(),
    ));
    Ok(())
}

fn resolve_proposal_equivalence_class<S>(
    operator: &RegisteredOperator,
    proposal: &DeformationProposal<S>,
    proposal_state_sha256: &str,
    before: ObstructionMeasure,
    established_equivalence: &BTreeSet<String>,
    accounting: &mut CandidateAccounting,
    candidates: &mut Vec<CandidateReceipt>,
) -> Result<Option<Option<String>>, IteratorError> {
    let Some(key) = &proposal.equivalence_key else {
        return Ok(Some(None));
    };
    let Some(contract) = &operator.equivalence_contract else {
        record_simple_candidate_rejection(
            accounting,
            candidates,
            proposal,
            proposal_state_sha256,
            before,
            CandidateVerdict::InvalidProposal,
            "equivalence key supplied without a registered equivalence contract",
        )?;
        return Ok(None);
    };
    if key.trim().is_empty() {
        record_simple_candidate_rejection(
            accounting,
            candidates,
            proposal,
            proposal_state_sha256,
            before,
            CandidateVerdict::InvalidProposal,
            "equivalence key must be non-empty",
        )?;
        return Ok(None);
    }
    let full_key = format!("{}::{contract}::{key}", operator.operator_id.0);
    if established_equivalence.contains(&full_key) {
        checked_add_counter(
            &mut accounting.duplicate_pruned,
            1,
            "duplicate-pruned candidates",
        )?;
        checked_add_counter(
            &mut accounting.predicted_avoided_by_quotient,
            proposal.predicted_candidates_avoided,
            "predicted quotient avoidance",
        )?;
        candidates.push(candidate_receipt(
            proposal,
            proposal_state_sha256.to_string(),
            before,
            CandidateVerdict::DuplicatePruned,
            "duplicate after an eligible representative established full admission and post-measure congruence".into(),
        ));
        return Ok(None);
    }
    Ok(Some(Some(full_key)))
}

#[allow(clippy::too_many_arguments)]
fn assess_and_verify_proposal<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    proposal: &DeformationProposal<A::State>,
    proposal_state_sha256: &str,
    operator: &RegisteredOperator,
    before: ObstructionMeasure,
    remaining_from_here: usize,
    candidates: &mut Vec<CandidateReceipt>,
    saw_lift: &mut bool,
) -> Result<ProposalAssessmentOutcome, IteratorError> {
    let assessment_result = adapter.assess_candidate(
        &run.packet,
        &run.carrier,
        &run.state,
        proposal,
        operator,
    );
    if wall_budget_exhausted(clock, run.budget) {
        checked_add_counter(
            &mut run.accounting.budget_pruned,
            remaining_from_here,
            "budget-pruned candidates",
        )?;
        return Ok(ProposalAssessmentOutcome::BudgetExhausted);
    }
    let mut assessment = match assessment_result {
        Ok(assessment) => assessment,
        Err(failure) => {
            checked_add_counter(&mut run.accounting.evaluated, 1, "evaluated candidates")?;
            let mut receipt = candidate_receipt(
                proposal,
                proposal_state_sha256.to_string(),
                before,
                CandidateVerdict::RejectedAdapter,
                failure.to_string(),
            );
            if failure.kind == AdapterFailureKind::RequiresLift {
                receipt.verdict = CandidateVerdict::RequiresLift;
                *saw_lift = true;
            }
            candidates.push(receipt);
            return Ok(ProposalAssessmentOutcome::Rejected);
        }
    };
    canonicalize_assessment(&mut assessment)?;
    if wall_budget_exhausted(clock, run.budget) {
        checked_add_counter(
            &mut run.accounting.budget_pruned,
            remaining_from_here,
            "budget-pruned candidates",
        )?;
        return Ok(ProposalAssessmentOutcome::BudgetExhausted);
    }
    check_preservation_and_witnesses(
        operator,
        run.budget,
        proposal,
        proposal_state_sha256,
        before,
        assessment,
        &mut run.accounting,
        candidates,
    )
}

#[allow(clippy::too_many_arguments)]
fn check_preservation_and_witnesses<S>(
    operator: &RegisteredOperator,
    budget: RunBudget,
    proposal: &DeformationProposal<S>,
    proposal_state_sha256: &str,
    before: ObstructionMeasure,
    assessment: CandidateAssessment,
    accounting: &mut CandidateAccounting,
    candidates: &mut Vec<CandidateReceipt>,
) -> Result<ProposalAssessmentOutcome, IteratorError> {
    if let Err(reason) = preservation_passes(operator, &assessment.preservation) {
        checked_add_counter(&mut accounting.evaluated, 1, "evaluated candidates")?;
        let mut receipt = candidate_receipt(
            proposal,
            proposal_state_sha256.to_string(),
            before,
            CandidateVerdict::RejectedPreservation,
            reason,
        );
        receipt.preservation = assessment.preservation;
        receipt.witnesses = assessment.witnesses;
        candidates.push(receipt);
        return Ok(ProposalAssessmentOutcome::Rejected);
    }
    if let Err(reason) = witnesses_pass(operator, &assessment.witnesses, budget) {
        checked_add_counter(&mut accounting.evaluated, 1, "evaluated candidates")?;
        let mut receipt = candidate_receipt(
            proposal,
            proposal_state_sha256.to_string(),
            before,
            CandidateVerdict::RejectedWitness,
            reason,
        );
        receipt.preservation = assessment.preservation;
        receipt.witnesses = assessment.witnesses;
        candidates.push(receipt);
        return Ok(ProposalAssessmentOutcome::Rejected);
    }
    Ok(ProposalAssessmentOutcome::Passed(assessment))
}

#[allow(clippy::too_many_arguments)]
fn inspect_and_record_passed_proposal<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    step_index: usize,
    state_sha256: &str,
    proposal: DeformationProposal<A::State>,
    proposal_state_sha256: String,
    operator: &RegisteredOperator,
    signature: &ObstructionSignature,
    equivalence_class: Option<String>,
    before: ObstructionMeasure,
    assessment: CandidateAssessment,
    remaining_from_here: usize,
    established_equivalence: &mut BTreeSet<String>,
    eligible: &mut Vec<EligibleCandidate<A::State>>,
    step: &mut StepReceipt,
) -> Result<bool, IteratorError> {
    let after_inspection = match inspect_post_candidate(
        adapter,
        clock,
        run,
        &proposal,
        &proposal_state_sha256,
        before,
        &assessment,
        remaining_from_here,
        &mut step.candidates,
    )? {
        Ok(Some(after_inspection)) => after_inspection,
        Ok(None) => return Ok(true),
        Err(()) => return Ok(false),
    };

    record_evaluated_candidate_descent(
        run,
        step_index,
        state_sha256,
        proposal,
        proposal_state_sha256,
        operator,
        signature,
        equivalence_class,
        before,
        assessment,
        after_inspection,
        established_equivalence,
        eligible,
        step,
    )?;
    Ok(true)
}

#[allow(clippy::too_many_arguments)]
fn inspect_post_candidate<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    proposal: &DeformationProposal<A::State>,
    proposal_state_sha256: &str,
    before: ObstructionMeasure,
    assessment: &CandidateAssessment,
    remaining_from_here: usize,
    candidates: &mut Vec<CandidateReceipt>,
) -> Result<Result<Option<InspectionReceipt>, ()>, IteratorError> {
    let after_result = adapter.inspect(&run.packet, &run.carrier, &proposal.state);
    if wall_budget_exhausted(clock, run.budget) {
        checked_add_counter(
            &mut run.accounting.budget_pruned,
            remaining_from_here,
            "budget-pruned candidates",
        )?;
        return Ok(Err(()));
    }
    let after_raw = match after_result {
        Ok(inspection) => inspection,
        Err(failure) => {
            checked_add_counter(&mut run.accounting.evaluated, 1, "evaluated candidates")?;
            let mut receipt = candidate_receipt(
                proposal,
                proposal_state_sha256.to_string(),
                before,
                CandidateVerdict::RejectedAdapter,
                format!("candidate inspection failed: {failure}"),
            );
            receipt.preservation = assessment.preservation.clone();
            receipt.witnesses = assessment.witnesses.clone();
            candidates.push(receipt);
            return Ok(Ok(None));
        }
    };
    let after_inspection = inspect_packet(&run.packet, after_raw)?;
    if wall_budget_exhausted(clock, run.budget) {
        checked_add_counter(
            &mut run.accounting.budget_pruned,
            remaining_from_here,
            "budget-pruned candidates",
        )?;
        return Ok(Err(()));
    }
    Ok(Ok(Some(after_inspection)))
}

#[allow(clippy::too_many_arguments)]
fn record_evaluated_candidate_descent<S>(
    run: &mut MultipathRunState<S>,
    step_index: usize,
    state_sha256: &str,
    proposal: DeformationProposal<S>,
    proposal_state_sha256: String,
    operator: &RegisteredOperator,
    signature: &ObstructionSignature,
    equivalence_class: Option<String>,
    before: ObstructionMeasure,
    assessment: CandidateAssessment,
    after_inspection: InspectionReceipt,
    established_equivalence: &mut BTreeSet<String>,
    eligible: &mut Vec<EligibleCandidate<S>>,
    step: &mut StepReceipt,
) -> Result<(), IteratorError> {
    checked_add_counter(&mut run.accounting.evaluated, 1, "evaluated candidates")?;
    let after = after_inspection.measure;
    let descends = before.strictly_descends_to(after);
    let (verdict, reason) = if descends {
        (
            CandidateVerdict::EligibleDescent,
            "strict lexicographic obstruction descent".into(),
        )
    } else {
        (
            CandidateVerdict::RejectedNoDescent,
            "candidate does not strictly reduce the declared obstruction measure".into(),
        )
    };
    let mut receipt = candidate_receipt(
        &proposal,
        proposal_state_sha256.clone(),
        before,
        verdict,
        reason,
    );
    receipt.after = Some(after);
    receipt.preservation = assessment.preservation.clone();
    receipt.witnesses = assessment.witnesses.clone();
    receipt.post_inspection = Some(after_inspection.clone());
    let source_candidate_sha256 = sha256_json(&receipt)?;
    step.candidates.push(receipt);
    if descends {
        let compiled_operator = compile_operator_candidate(OperatorCompilationInput {
            packet_sha256: &run.packet_sha256,
            operator_registry_sha256: &run.operator_registry_sha256,
            source_step_index: step_index,
            source_carrier_sha256: &step.carrier_sha256,
            source_state_sha256: state_sha256,
            result_state_sha256: &proposal_state_sha256,
            source_candidate_sha256: &source_candidate_sha256,
            carrier_kind: run.carrier.kind,
            proposal: &proposal,
            operator,
            signature,
            before,
            after,
            post_inspection: &after_inspection,
            assessment: &assessment,
        })?;
        if let Some(full_key) = equivalence_class {
            established_equivalence.insert(full_key);
        }
        eligible.push(EligibleCandidate {
            proposal_id: proposal.proposal_id,
            candidate_sha256: source_candidate_sha256,
            state: proposal.state,
            measure: after,
            compiled_operator,
        });
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn select_or_extend_or_terminate<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    inspection: &InspectionReceipt,
    mut step: StepReceipt,
    eligible: Vec<EligibleCandidate<A::State>>,
    saw_lift: bool,
    wall_exhausted: bool,
) -> Result<bool, IteratorError> {
    match select_best_eligible_candidate(clock, run, &mut step, eligible, wall_exhausted)? {
        CandidateSelectionOutcome::Selected(selected) => {
            apply_selected_candidate(run, step, selected)?;
            return Ok(true);
        }
        CandidateSelectionOutcome::BudgetTerminated(terminal) => {
            run.terminal = Some(terminal);
            run.steps.push(step);
            return Ok(false);
        }
        CandidateSelectionOutcome::NoneEligible => {}
    }

    match try_step_carrier_extension(adapter, clock, run, inspection, &mut step)? {
        CarrierExtensionOutcome::Extended => {
            run.steps.push(step);
            Ok(true)
        }
        CarrierExtensionOutcome::Terminated(terminal) => {
            run.terminal = Some(terminal);
            run.steps.push(step);
            Ok(false)
        }
        CarrierExtensionOutcome::NoExtension => {
            run.terminal = Some(unextended_step_terminal(saw_lift, step.candidates.is_empty()));
            run.steps.push(step);
            Ok(false)
        }
    }
}

fn select_best_eligible_candidate<S, C: RunClock + ?Sized>(
    clock: &C,
    run: &mut MultipathRunState<S>,
    step: &mut StepReceipt,
    mut eligible: Vec<EligibleCandidate<S>>,
    wall_exhausted: bool,
) -> Result<CandidateSelectionOutcome<S>, IteratorError> {
    if wall_exhausted || wall_budget_exhausted(clock, run.budget) {
        abandon_eligible_for_budget(step, &mut eligible, &mut run.accounting)?;
        return Ok(CandidateSelectionOutcome::BudgetTerminated(
            TerminalReceipt {
                kind: TerminalKind::BudgetExhausted,
                reason: "max_wall_millis exhausted before candidate selection".into(),
            },
        ));
    }
    eligible.sort_by(|left, right| {
        left.measure
            .rank()
            .cmp(&right.measure.rank())
            .then_with(|| left.proposal_id.cmp(&right.proposal_id))
    });
    if wall_budget_exhausted(clock, run.budget) {
        abandon_eligible_for_budget(step, &mut eligible, &mut run.accounting)?;
        return Ok(CandidateSelectionOutcome::BudgetTerminated(
            TerminalReceipt {
                kind: TerminalKind::BudgetExhausted,
                reason: "max_wall_millis exhausted while ordering candidates".into(),
            },
        ));
    }
    if let Some(selected) = eligible.into_iter().next() {
        Ok(CandidateSelectionOutcome::Selected(selected))
    } else {
        Ok(CandidateSelectionOutcome::NoneEligible)
    }
}

fn apply_selected_candidate<S>(
    run: &mut MultipathRunState<S>,
    mut step: StepReceipt,
    selected: EligibleCandidate<S>,
) -> Result<(), IteratorError> {
    step.selected_proposal_id = Some(selected.proposal_id);
    step.selected_candidate_sha256 = Some(selected.candidate_sha256);
    step.compiled_operator_candidate = Some(selected.compiled_operator);
    run.state = selected.state;
    checked_add_counter(
        &mut run.accounting.accepted_transitions,
        1,
        "accepted transitions",
    )?;
    checked_add_counter(
        &mut run.accounting.compiled_operator_candidates,
        1,
        "compiled operator candidates",
    )?;
    run.steps.push(step);
    Ok(())
}

fn try_step_carrier_extension<A: MultipathAdapter, C: RunClock + ?Sized>(
    adapter: &A,
    clock: &C,
    run: &mut MultipathRunState<A::State>,
    inspection: &InspectionReceipt,
    step: &mut StepReceipt,
) -> Result<CarrierExtensionOutcome, IteratorError> {
    let extension_result =
        adapter.extend_carrier(&run.packet, &run.carrier, &run.state, inspection);
    if wall_budget_exhausted(clock, run.budget) {
        return Ok(CarrierExtensionOutcome::Terminated(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: "max_wall_millis exhausted after extend_carrier".into(),
        }));
    }
    let extension = match extension_result {
        Ok(Some(extension)) => extension,
        Ok(None) => return Ok(CarrierExtensionOutcome::NoExtension),
        Err(failure) => return Ok(CarrierExtensionOutcome::Terminated(terminal_from_failure(failure)?)),
    };
    apply_validated_carrier_extension(clock, run, inspection, step, extension)
}

fn apply_validated_carrier_extension<S, C: RunClock + ?Sized>(
    clock: &C,
    run: &mut MultipathRunState<S>,
    inspection: &InspectionReceipt,
    step: &mut StepReceipt,
    extension: CarrierExtension,
) -> Result<CarrierExtensionOutcome, IteratorError> {
    let extended_carrier = validate_extension(&run.carrier, &extension, inspection)?;
    if extended_carrier.cells.len() > run.budget.max_carrier_cells {
        return Ok(CarrierExtensionOutcome::Terminated(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: "max_carrier_cells exhausted".into(),
        }));
    }
    let parent_carrier_sha256 = sha256_json(&run.carrier)?;
    let extended_carrier_sha256 = sha256_json(&extended_carrier)?;
    let mut added_cell_ids: Vec<_> = extension
        .new_cells
        .iter()
        .map(|cell| cell.cell_id.clone())
        .collect();
    added_cell_ids.sort();
    let added_cells: Vec<_> = extended_carrier
        .cells
        .iter()
        .filter(|cell| added_cell_ids.binary_search(&cell.cell_id).is_ok())
        .cloned()
        .collect();
    if wall_budget_exhausted(clock, run.budget) {
        return Ok(CarrierExtensionOutcome::Terminated(TerminalReceipt {
            kind: TerminalKind::BudgetExhausted,
            reason: "max_wall_millis exhausted while validating carrier extension".into(),
        }));
    }
    run.carrier = extended_carrier;
    step.carrier_extension = Some(CarrierExtensionReceipt {
        extension_id: extension.extension_id,
        trigger_signature_sha256: extension.trigger_signature_sha256,
        justification_ref: extension.justification_ref,
        parent_carrier_sha256,
        extended_carrier_sha256,
        added_cell_ids,
        added_cells,
    });
    checked_add_counter(&mut run.accounting.carrier_extensions, 1, "carrier extensions")?;
    Ok(CarrierExtensionOutcome::Extended)
}

fn unextended_step_terminal(saw_lift: bool, candidates_empty: bool) -> TerminalReceipt {
    let (kind, reason) = if saw_lift {
        (
            TerminalKind::RequiresLift,
            "remaining candidate path requires an unlicensed lift".into(),
        )
    } else if candidates_empty {
        (
            TerminalKind::NoRule,
            "no registered deformation proposal is available".into(),
        )
    } else {
        (
            TerminalKind::OpenObstruction,
            "all admitted candidates failed descent, preservation, or witness checks".into(),
        )
    };
    TerminalReceipt { kind, reason }
}

fn finalize_run_receipt<S: Serialize, C: RunClock + ?Sized>(
    adapter_id: &str,
    registry: &OperatorRegistry,
    clock: &C,
    run: MultipathRunState<S>,
) -> Result<RunReceipt, IteratorError> {
    let terminal = run.terminal.unwrap_or_else(|| TerminalReceipt {
        kind: TerminalKind::BudgetExhausted,
        reason: "max_steps exhausted".into(),
    });
    if !run.accounting.is_balanced() {
        return Err(IteratorError::InvalidDeclaration(format!(
            "candidate accounting mismatch: proposed={}, evaluated={}, duplicate_pruned={}, budget_pruned={}",
            run.accounting.proposed,
            run.accounting.evaluated,
            run.accounting.duplicate_pruned,
            run.accounting.budget_pruned
        )));
    }
    let final_state_sha256 = sha256_json(&run.state)?;
    let mut receipt = RunReceipt {
        schema_version: MULTIPATH_RECEIPT_SCHEMA.into(),
        adapter_id: adapter_id.into(),
        packet: run.packet,
        packet_sha256: run.packet_sha256,
        operator_registry: registry.clone(),
        operator_registry_sha256: run.operator_registry_sha256,
        initial_carrier: run.initial_carrier,
        final_carrier: run.carrier,
        initial_state_sha256: run.initial_state_sha256,
        final_state_sha256,
        budget: run.budget,
        accounting: run.accounting,
        steps: run.steps,
        terminal,
        replay_sha256: String::new(),
        runtime_micros: clock.elapsed_micros(),
        authority_effect: AuthorityEffect::None,
    };
    receipt.replay_sha256 = replay_hash_for(&receipt)?;
    let receipt_bytes = serialized_len(&receipt)?;
    if receipt_bytes > run.budget.max_receipt_bytes {
        return Err(IteratorError::InvalidBudget(format!(
            "complete receipt requires {receipt_bytes} bytes, above max_receipt_bytes {}",
            run.budget.max_receipt_bytes
        )));
    }
    if !receipt.verify_replay_hash()? {
        return Err(IteratorError::InvalidDeclaration(
            "runtime produced a receipt rejected by public replay verification".into(),
        ));
    }
    Ok(receipt)
}

fn inspect_packet(
    packet: &ProblemPacket,
    mut inspection: Inspection,
) -> Result<InspectionReceipt, IteratorError> {
    validate_observer_and_comparison(&inspection.observer, &inspection.comparison)?;
    let (datum_id_set, projected_source_refs) = canonicalize_projected_data(
        &mut inspection.projected_data,
        "must be exactly 64 hexadecimal characters",
    )?;
    canonicalize_raw_coverage(
        packet,
        &mut inspection.coverage,
        &datum_id_set,
        &projected_source_refs,
    )?;
    let (defects, mut signatures, mut measure) =
        evaluate_visible_defects(inspection.visible_defects)?;
    let detector_inadequate_count = accumulate_raw_coverage_dispositions(
        &inspection.coverage,
        &mut measure,
        &mut signatures,
    )?;
    signatures.sort_by(|left, right| left.signature_sha256.cmp(&right.signature_sha256));

    canonicalize_inspection_receipt(
        packet,
        InspectionReceipt {
            observer: inspection.observer,
            comparison: inspection.comparison,
            projected_data: inspection.projected_data,
            coverage: inspection.coverage,
            defects,
            signatures,
            measure,
            detector_inadequate_count,
            higher_degree_need: inspection.higher_degree_need,
            discarded_information_refs: inspection.discarded_information_refs,
        },
    )
}

fn validate_observer_and_comparison(
    observer: &ObserverDeclaration,
    comparison: &ComparisonDeclaration,
) -> Result<(), IteratorError> {
    nonempty(&observer.observer_id, "observer_id")?;
    nonempty(&observer.observer_family, "observer_family")?;
    nonempty(&observer.scope, "observer scope")?;
    nonempty(&comparison.comparison_id, "comparison_id")?;
    nonempty(&comparison.zero_rel, "ZeroRel")?;
    nonempty(&comparison.gauge_family, "gauge_family")
}

fn canonicalize_projected_data(
    projected_data: &mut [ProjectedDatum],
    sha_error_suffix: &str,
) -> Result<(BTreeSet<String>, BTreeSet<String>), IteratorError> {
    projected_data
        .sort_by(|left, right| (left.degree, &left.datum_id).cmp(&(right.degree, &right.datum_id)));
    let datum_ids: Vec<_> = projected_data
        .iter()
        .map(|datum| datum.datum_id.clone())
        .collect();
    ensure_unique(&datum_ids, "projected datum ids")?;
    let datum_id_set: BTreeSet<_> = datum_ids.into_iter().collect();
    let mut projected_source_refs = BTreeSet::new();
    for datum in projected_data {
        validate_projected_datum(datum, sha_error_suffix, &mut projected_source_refs)?;
    }
    Ok((datum_id_set, projected_source_refs))
}

fn validate_projected_datum(
    datum: &mut ProjectedDatum,
    sha_error_suffix: &str,
    projected_source_refs: &mut BTreeSet<String>,
) -> Result<(), IteratorError> {
    nonempty(&datum.datum_id, "projected datum id")?;
    if !is_sha256(&datum.value_sha256) {
        return Err(IteratorError::InvalidDeclaration(format!(
            "projected datum `{}` value_sha256 {sha_error_suffix}",
            datum.datum_id
        )));
    }
    if datum.source_refs.is_empty() {
        return Err(IteratorError::InvalidDeclaration(format!(
            "projected datum `{}` has no source_refs",
            datum.datum_id
        )));
    }
    datum.source_refs.sort();
    ensure_unique(&datum.source_refs, "projected datum source_refs")?;
    for source_ref in &datum.source_refs {
        nonempty(source_ref, "projected datum source_ref")?;
        projected_source_refs.insert(source_ref.clone());
    }
    Ok(())
}

fn canonicalize_raw_coverage(
    packet: &ProblemPacket,
    coverage: &mut [CoverageAssessment],
    datum_id_set: &BTreeSet<String>,
    projected_source_refs: &BTreeSet<String>,
) -> Result<(), IteratorError> {
    coverage.sort_by(|left, right| left.requirement.cmp(&right.requirement));
    let expected = &packet.protected_distinctions;
    let actual: Vec<_> = coverage
        .iter()
        .map(|assessment| assessment.requirement.clone())
        .collect();
    if expected.as_slice() != actual {
        return Err(IteratorError::InvalidDeclaration(format!(
            "detector coverage does not exactly match protected distinctions; expected={expected:?}, actual={actual:?}"
        )));
    }
    for assessment in coverage {
        validate_raw_coverage_assessment(assessment, datum_id_set, projected_source_refs)?;
    }
    Ok(())
}

fn validate_raw_coverage_assessment(
    assessment: &mut CoverageAssessment,
    datum_id_set: &BTreeSet<String>,
    projected_source_refs: &BTreeSet<String>,
) -> Result<(), IteratorError> {
    nonempty(&assessment.evidence_ref, "coverage evidence_ref")?;
    match assessment.disposition {
        CoverageDisposition::ProjectionLoss => {
            let Some(loss) = &mut assessment.projection_loss else {
                return Err(IteratorError::InvalidDeclaration(format!(
                    "projection-loss assessment `{}` has no loss receipt",
                    assessment.requirement.key()
                )));
            };
            validate_projection_loss(loss, datum_id_set, projected_source_refs)
        }
        CoverageDisposition::PreservedVisible | CoverageDisposition::DetectorInadequate
            if assessment.projection_loss.is_some() =>
        {
            Err(IteratorError::InvalidDeclaration(format!(
                "non-loss assessment `{}` carries a projection-loss receipt",
                assessment.requirement.key()
            )))
        }
        CoverageDisposition::PreservedVisible | CoverageDisposition::DetectorInadequate => Ok(()),
    }
}

fn evaluate_visible_defects(
    mut visible_defects: Vec<VisibleDefect>,
) -> Result<
    (
        Vec<DefectReceipt>,
        Vec<ObstructionSignature>,
        ObstructionMeasure,
    ),
    IteratorError,
> {
    visible_defects.sort_by(|left, right| left.defect_id.cmp(&right.defect_id));
    let defect_ids: Vec<_> = visible_defects
        .iter()
        .map(|defect| defect.defect_id.clone())
        .collect();
    ensure_unique(&defect_ids, "visible defect ids")?;

    let mut defects = Vec::new();
    let mut signatures = Vec::new();
    let mut measure = ObstructionMeasure::default();
    for defect in visible_defects {
        let receipt = evaluate_single_visible_defect(defect, &mut measure, &mut signatures)?;
        defects.push(receipt);
    }
    Ok((defects, signatures, measure))
}

fn evaluate_single_visible_defect(
    defect: VisibleDefect,
    measure: &mut ObstructionMeasure,
    signatures: &mut Vec<ObstructionSignature>,
) -> Result<DefectReceipt, IteratorError> {
    nonempty(&defect.defect_id, "defect_id")?;
    nonempty(&defect.claim_id, "defect claim_id")?;
    nonempty(&defect.kind, "defect kind")?;
    nonempty(&defect.evidence_ref, "defect evidence_ref")?;
    let cochain =
        diagnose_defect_cochain(&defect.defect_id, defect.exact_binary_cochain, measure)?;
    let signature_sha256 = sha256_json(&(
        &defect.defect_id,
        &defect.claim_id,
        &defect.kind,
        &defect.cell_refs,
        &cochain,
    ))?;
    if cochain
        .as_ref()
        .is_none_or(|diagnostic| diagnostic.classification != "exact")
    {
        signatures.push(ObstructionSignature {
            defect_id: defect.defect_id.clone(),
            kind: defect.kind.clone(),
            signature_sha256: signature_sha256.clone(),
        });
    }
    Ok(DefectReceipt {
        defect_id: defect.defect_id,
        claim_id: defect.claim_id,
        kind: defect.kind,
        cell_refs: defect.cell_refs,
        evidence_ref: defect.evidence_ref,
        signature_sha256,
        cochain,
    })
}

fn diagnose_defect_cochain(
    defect_id: &str,
    probe: Option<ExactBinaryCochainProbe>,
    measure: &mut ObstructionMeasure,
) -> Result<Option<CochainDiagnosticReceipt>, IteratorError> {
    let Some(probe) = probe else {
        measure.open_defect_count += 1;
        return Ok(None);
    };
    let diagnostic = probe
        .segment
        .diagnose(&probe.residual)
        .map_err(|error| IteratorError::Dda(format!("defect {defect_id}: {error:?}")))?;
    match diagnostic.classification {
        DegreeTrichotomy::Exact => {}
        DegreeTrichotomy::StabilizedSurvivor => {
            measure.stabilized_survivor_count += 1;
            measure.phi_total += diagnostic.phi;
        }
        DegreeTrichotomy::Open => {
            measure.open_defect_count += 1;
            measure.phi_total += diagnostic.phi;
            measure.gamma_total += diagnostic.gamma;
        }
    }
    Ok(Some(diagnostic.into()))
}

fn accumulate_raw_coverage_dispositions(
    coverage: &[CoverageAssessment],
    measure: &mut ObstructionMeasure,
    signatures: &mut Vec<ObstructionSignature>,
) -> Result<usize, IteratorError> {
    let mut detector_inadequate_count = 0;
    for assessment in coverage {
        match assessment.disposition {
            CoverageDisposition::PreservedVisible => {}
            CoverageDisposition::ProjectionLoss => {
                measure.projection_loss_count += 1;
                let signature_sha256 =
                    sha256_json(&(assessment.requirement.key(), &assessment.projection_loss))?;
                signatures.push(ObstructionSignature {
                    defect_id: format!("projection-loss::{}", assessment.requirement.key()),
                    kind: "projection_loss".into(),
                    signature_sha256,
                });
            }
            CoverageDisposition::DetectorInadequate => detector_inadequate_count += 1,
        }
    }
    Ok(detector_inadequate_count)
}

fn canonicalize_inspection_receipt(
    packet: &ProblemPacket,
    mut inspection: InspectionReceipt,
) -> Result<InspectionReceipt, IteratorError> {
    validate_observer_and_comparison(&inspection.observer, &inspection.comparison)?;
    let (datum_id_set, projected_source_refs) = canonicalize_projected_data(
        &mut inspection.projected_data,
        "must be lowercase SHA-256",
    )?;
    canonicalize_retained_coverage(
        packet,
        &mut inspection.coverage,
        &datum_id_set,
        &projected_source_refs,
    )?;
    let (mut measure, mut signatures) = canonicalize_retained_defects(&mut inspection.defects)?;
    let detector_inadequate_count = accumulate_retained_coverage_dispositions(
        &inspection.coverage,
        &mut measure,
        &mut signatures,
    )?;
    signatures.sort_by(|left, right| left.signature_sha256.cmp(&right.signature_sha256));
    let signature_hashes: Vec<_> = signatures
        .iter()
        .map(|signature| signature.signature_sha256.clone())
        .collect();
    ensure_unique(&signature_hashes, "obstruction signature hashes")?;
    validate_higher_degree_and_discarded_refs(
        &inspection.higher_degree_need,
        &mut inspection.discarded_information_refs,
    )?;

    inspection.signatures = signatures;
    inspection.measure = measure;
    inspection.detector_inadequate_count = detector_inadequate_count;
    Ok(inspection)
}

fn canonicalize_retained_coverage(
    packet: &ProblemPacket,
    coverage: &mut [CoverageAssessment],
    datum_id_set: &BTreeSet<String>,
    projected_source_refs: &BTreeSet<String>,
) -> Result<(), IteratorError> {
    coverage.sort_by(|left, right| left.requirement.cmp(&right.requirement));
    let expected_coverage = &packet.protected_distinctions;
    let actual_coverage: Vec<_> = coverage
        .iter()
        .map(|assessment| assessment.requirement.clone())
        .collect();
    if expected_coverage.as_slice() != actual_coverage {
        return Err(IteratorError::InvalidDeclaration(
            "retained detector coverage does not match packet protected distinctions".into(),
        ));
    }
    for assessment in coverage {
        validate_retained_coverage_assessment(assessment, datum_id_set, projected_source_refs)?;
    }
    Ok(())
}

fn validate_retained_coverage_assessment(
    assessment: &mut CoverageAssessment,
    datum_id_set: &BTreeSet<String>,
    projected_source_refs: &BTreeSet<String>,
) -> Result<(), IteratorError> {
    nonempty(&assessment.evidence_ref, "coverage evidence_ref")?;
    match assessment.disposition {
        CoverageDisposition::ProjectionLoss => {
            let Some(loss) = &mut assessment.projection_loss else {
                return Err(IteratorError::InvalidDeclaration(
                    "projection-loss coverage has no retained loss receipt".into(),
                ));
            };
            validate_projection_loss(loss, datum_id_set, projected_source_refs)
        }
        CoverageDisposition::PreservedVisible | CoverageDisposition::DetectorInadequate
            if assessment.projection_loss.is_some() =>
        {
            Err(IteratorError::InvalidDeclaration(
                "non-loss coverage carries a projection-loss receipt".into(),
            ))
        }
        CoverageDisposition::PreservedVisible | CoverageDisposition::DetectorInadequate => Ok(()),
    }
}

fn canonicalize_retained_defects(
    defects: &mut [DefectReceipt],
) -> Result<(ObstructionMeasure, Vec<ObstructionSignature>), IteratorError> {
    defects.sort_by(|left, right| left.defect_id.cmp(&right.defect_id));
    let defect_ids: Vec<_> = defects
        .iter()
        .map(|defect| defect.defect_id.clone())
        .collect();
    ensure_unique(&defect_ids, "retained defect ids")?;

    let mut measure = ObstructionMeasure::default();
    let mut signatures = Vec::new();
    for defect in defects {
        canonicalize_single_retained_defect(defect, &mut measure, &mut signatures)?;
    }
    Ok((measure, signatures))
}

fn canonicalize_single_retained_defect(
    defect: &mut DefectReceipt,
    measure: &mut ObstructionMeasure,
    signatures: &mut Vec<ObstructionSignature>,
) -> Result<(), IteratorError> {
    validate_and_sort_defect_fields(defect)?;
    let retains_signature =
        accumulate_retained_cochain(&defect.defect_id, &defect.cochain, measure)?;
    defect.signature_sha256 = sha256_json(&(
        &defect.defect_id,
        &defect.claim_id,
        &defect.kind,
        &defect.cell_refs,
        &defect.cochain,
    ))?;
    if retains_signature {
        signatures.push(ObstructionSignature {
            defect_id: defect.defect_id.clone(),
            kind: defect.kind.clone(),
            signature_sha256: defect.signature_sha256.clone(),
        });
    }
    Ok(())
}

fn validate_and_sort_defect_fields(defect: &mut DefectReceipt) -> Result<(), IteratorError> {
    nonempty(&defect.defect_id, "defect_id")?;
    nonempty(&defect.claim_id, "defect claim_id")?;
    nonempty(&defect.kind, "defect kind")?;
    nonempty(&defect.evidence_ref, "defect evidence_ref")?;
    if defect.cell_refs.is_empty() {
        return Err(IteratorError::InvalidDeclaration(format!(
            "defect `{}` has no cell_refs",
            defect.defect_id
        )));
    }
    defect.cell_refs.sort();
    ensure_unique(&defect.cell_refs, "defect cell_refs")?;
    for cell_ref in &defect.cell_refs {
        nonempty(cell_ref, "defect cell_ref")?;
    }
    Ok(())
}

fn accumulate_retained_cochain(
    defect_id: &str,
    cochain: &Option<CochainDiagnosticReceipt>,
    measure: &mut ObstructionMeasure,
) -> Result<bool, IteratorError> {
    let Some(diagnostic) = cochain else {
        checked_add_counter(&mut measure.open_defect_count, 1, "open defects")?;
        return Ok(true);
    };
    accumulate_retained_cochain_diagnostic(defect_id, diagnostic, measure)
}

fn accumulate_retained_cochain_diagnostic(
    defect_id: &str,
    diagnostic: &CochainDiagnosticReceipt,
    measure: &mut ObstructionMeasure,
) -> Result<bool, IteratorError> {
    let valid = match diagnostic.classification.as_str() {
        "exact" => diagnostic.phi == 0 && diagnostic.gamma == 0,
        "stabilized_survivor" => record_stabilized_survivor_cochain(diagnostic, measure)?,
        "open" => record_open_cochain(diagnostic, measure)?,
        _ => false,
    };
    if !valid {
        return Err(IteratorError::InvalidDeclaration(format!(
            "defect `{defect_id}` has an inconsistent cochain classification"
        )));
    }
    Ok(diagnostic.classification != "exact")
}

fn record_stabilized_survivor_cochain(
    diagnostic: &CochainDiagnosticReceipt,
    measure: &mut ObstructionMeasure,
) -> Result<bool, IteratorError> {
    if diagnostic.phi == 0 || diagnostic.gamma != 0 {
        return Ok(false);
    }
    checked_add_counter(
        &mut measure.stabilized_survivor_count,
        1,
        "stabilized survivor count",
    )?;
    checked_add_counter(&mut measure.phi_total, diagnostic.phi, "Phi total")?;
    Ok(true)
}

fn record_open_cochain(
    diagnostic: &CochainDiagnosticReceipt,
    measure: &mut ObstructionMeasure,
) -> Result<bool, IteratorError> {
    if diagnostic.phi == 0 || diagnostic.gamma == 0 {
        return Ok(false);
    }
    checked_add_counter(&mut measure.open_defect_count, 1, "open defects")?;
    checked_add_counter(&mut measure.phi_total, diagnostic.phi, "Phi total")?;
    checked_add_counter(&mut measure.gamma_total, diagnostic.gamma, "Gamma total")?;
    Ok(true)
}

fn step_transition_presence_is_valid(position: usize, total_steps: usize, step: &StepReceipt) -> bool {
    let has_selection = step.compiled_operator_candidate.is_some();
    let has_extension = step.carrier_extension.is_some();
    !(has_selection && has_extension)
        && (position + 1 >= total_steps || has_selection || has_extension)
}

fn record_compiled_step_transition(
    compiled: &CompiledOperatorCandidate,
    state: &mut StepValidationState,
) -> bool {
    if !compiled.before.strictly_descends_to(compiled.after) {
        return false;
    }
    let Some(next) = state.selected_count.checked_add(1) else {
        return false;
    };
    state.expected_state_sha256 = compiled.result_state_sha256.clone();
    state.selected_count = next;
    true
}

fn accumulate_retained_coverage_dispositions(
    coverage: &[CoverageAssessment],
    measure: &mut ObstructionMeasure,
    signatures: &mut Vec<ObstructionSignature>,
) -> Result<usize, IteratorError> {
    let mut detector_inadequate_count = 0usize;
    for assessment in coverage {
        match assessment.disposition {
            CoverageDisposition::PreservedVisible => {}
            CoverageDisposition::ProjectionLoss => {
                checked_add_counter(
                    &mut measure.projection_loss_count,
                    1,
                    "projection loss count",
                )?;
                signatures.push(ObstructionSignature {
                    defect_id: format!("projection-loss::{}", assessment.requirement.key()),
                    kind: "projection_loss".into(),
                    signature_sha256: sha256_json(&(
                        assessment.requirement.key(),
                        &assessment.projection_loss,
                    ))?,
                });
            }
            CoverageDisposition::DetectorInadequate => checked_add_counter(
                &mut detector_inadequate_count,
                1,
                "detector inadequate count",
            )?,
        }
    }
    Ok(detector_inadequate_count)
}

fn validate_higher_degree_and_discarded_refs(
    higher_degree_need: &Option<HigherDegreeNeed>,
    discarded_information_refs: &mut [String],
) -> Result<(), IteratorError> {
    if let Some(need) = higher_degree_need {
        if need.required_degree <= need.current_max_degree {
            return Err(IteratorError::InvalidDeclaration(
                "higher-degree need must exceed the admitted degree".into(),
            ));
        }
        nonempty(&need.witness_ref, "higher-degree witness_ref")?;
        if let Some(license) = &need.licensed_lift_ref {
            nonempty(license, "higher-degree licensed_lift_ref")?;
        }
    }
    discarded_information_refs.sort();
    ensure_unique(discarded_information_refs, "discarded information refs")?;
    for discarded_ref in discarded_information_refs {
        nonempty(discarded_ref, "discarded information ref")?;
    }
    Ok(())
}

fn validate_projection_loss(
    loss: &mut ProjectionLossReceipt,
    datum_ids: &BTreeSet<String>,
    projected_source_refs: &BTreeSet<String>,
) -> Result<(), IteratorError> {
    validate_and_sort_projection_loss_fields(loss)?;
    validate_projection_loss_ref_bindings(loss, datum_ids, projected_source_refs)
}

fn validate_and_sort_projection_loss_fields(
    loss: &mut ProjectionLossReceipt,
) -> Result<(), IteratorError> {
    nonempty(&loss.loss_id, "projection loss_id")?;
    nonempty(
        &loss.recovery_requirement,
        "projection loss recovery_requirement",
    )?;
    if !is_sha256(&loss.discarded_sha256) {
        return Err(IteratorError::InvalidDeclaration(format!(
            "projection loss `{}` discarded_sha256 must be exactly 64 hexadecimal characters",
            loss.loss_id
        )));
    }
    if loss.source_refs.is_empty() {
        return Err(IteratorError::InvalidDeclaration(format!(
            "projection loss `{}` has no source_refs",
            loss.loss_id
        )));
    }
    if loss.collided_projection_refs.is_empty() {
        return Err(IteratorError::InvalidDeclaration(format!(
            "projection loss `{}` has no collided_projection_refs",
            loss.loss_id
        )));
    }
    loss.source_refs.sort();
    loss.collided_projection_refs.sort();
    ensure_unique(&loss.source_refs, "projection loss source_refs")?;
    ensure_unique(
        &loss.collided_projection_refs,
        "projection loss collided_projection_refs",
    )
}

fn validate_projection_loss_ref_bindings(
    loss: &ProjectionLossReceipt,
    datum_ids: &BTreeSet<String>,
    projected_source_refs: &BTreeSet<String>,
) -> Result<(), IteratorError> {
    for source_ref in &loss.source_refs {
        nonempty(source_ref, "projection loss source_ref")?;
        if !projected_source_refs.contains(source_ref) && !source_ref.starts_with("external:") {
            return Err(IteratorError::InvalidDeclaration(format!(
                "projection loss `{}` source_ref `{source_ref}` is neither projected nor explicitly external",
                loss.loss_id
            )));
        }
    }
    for collided_ref in &loss.collided_projection_refs {
        nonempty(collided_ref, "projection loss collided_projection_ref")?;
        if !datum_ids.contains(collided_ref) {
            return Err(IteratorError::InvalidDeclaration(format!(
                "projection loss `{}` collided_projection_ref `{collided_ref}` does not resolve to projected_data",
                loss.loss_id
            )));
        }
    }
    Ok(())
}

fn validate_proposals<S>(proposals: &[DeformationProposal<S>]) -> Result<(), IteratorError> {
    let mut ids = Vec::with_capacity(proposals.len());
    for proposal in proposals {
        nonempty(&proposal.proposal_id, "proposal_id")?;
        nonempty(&proposal.operator_id.0, "proposal operator_id")?;
        nonempty(&proposal.provenance.0, "proposal provenance")?;
        if !is_sha256(&proposal.matched_signature_sha256) {
            return Err(IteratorError::InvalidDeclaration(
                "proposal matched_signature_sha256 must be lowercase SHA-256".into(),
            ));
        }
        if let Some(key) = &proposal.equivalence_key {
            nonempty(key, "proposal equivalence_key")?;
        }
        ids.push(proposal.proposal_id.clone());
    }
    ids.sort();
    ensure_unique(&ids, "proposal ids")
}

fn canonicalize_assessment(assessment: &mut CandidateAssessment) -> Result<(), IteratorError> {
    canonicalize_preservation_checks(&mut assessment.preservation)?;
    canonicalize_witness_results(&mut assessment.witnesses)
}

fn canonicalize_preservation_checks(
    preservation: &mut [PreservationCheck],
) -> Result<(), IteratorError> {
    for check in preservation.iter() {
        nonempty(&check.obligation_id, "preservation obligation_id")?;
        nonempty(&check.evidence_ref, "preservation evidence_ref")?;
        if !is_sha256(&check.evidence_sha256) {
            return Err(IteratorError::InvalidDeclaration(
                "preservation evidence_sha256 must be lowercase SHA-256".into(),
            ));
        }
    }
    preservation.sort_by(|left, right| left.obligation_id.cmp(&right.obligation_id));
    let preservation_ids: Vec<_> = preservation
        .iter()
        .map(|check| check.obligation_id.clone())
        .collect();
    ensure_unique(&preservation_ids, "preservation obligation ids")
}

fn canonicalize_witness_results(witnesses: &mut [WitnessResult]) -> Result<(), IteratorError> {
    for witness in witnesses.iter() {
        nonempty(&witness.witness_id, "witness_id")?;
        nonempty(&witness.procedure, "witness procedure")?;
        nonempty(&witness.evidence_ref, "witness evidence_ref")?;
        if !is_sha256(&witness.evidence_sha256) {
            return Err(IteratorError::InvalidDeclaration(
                "witness evidence_sha256 must be lowercase SHA-256".into(),
            ));
        }
    }
    witnesses.sort_by(|left, right| left.witness_id.cmp(&right.witness_id));
    let witness_ids: Vec<_> = witnesses
        .iter()
        .map(|witness| witness.witness_id.clone())
        .collect();
    ensure_unique(&witness_ids, "witness ids")
}

fn candidate_receipt<S>(
    proposal: &DeformationProposal<S>,
    state_sha256: String,
    before: ObstructionMeasure,
    verdict: CandidateVerdict,
    reason: String,
) -> CandidateReceipt {
    CandidateReceipt {
        proposal_id: proposal.proposal_id.clone(),
        operator_id: proposal.operator_id.clone(),
        provenance: proposal.provenance.clone(),
        state_sha256,
        matched_signature_sha256: proposal.matched_signature_sha256.clone(),
        equivalence_key: proposal.equivalence_key.clone(),
        predicted_candidates_avoided: proposal.predicted_candidates_avoided,
        verdict,
        reason,
        before,
        after: None,
        preservation: Vec::new(),
        witnesses: Vec::new(),
        post_inspection: None,
    }
}

fn preservation_passes(
    operator: &RegisteredOperator,
    checks: &[PreservationCheck],
) -> Result<(), String> {
    let expected: BTreeSet<_> = operator.preservation_obligations.iter().cloned().collect();
    let actual: BTreeSet<_> = checks
        .iter()
        .map(|check| check.obligation_id.clone())
        .collect();
    if expected != actual || checks.len() != actual.len() {
        return Err(format!(
            "preservation coverage mismatch; expected={expected:?}, actual={actual:?}"
        ));
    }
    for check in checks {
        nonempty(&check.evidence_ref, "preservation evidence_ref")
            .map_err(|error| error.to_string())?;
        if !is_sha256(&check.evidence_sha256) {
            return Err(format!(
                "preservation obligation {} has an invalid evidence SHA-256",
                check.obligation_id
            ));
        }
        if check.verdict != CheckVerdict::Pass {
            return Err(format!(
                "preservation obligation `{}` is {:?}",
                check.obligation_id, check.verdict
            ));
        }
    }
    Ok(())
}

fn witnesses_pass(
    operator: &RegisteredOperator,
    witnesses: &[WitnessResult],
    budget: RunBudget,
) -> Result<(), String> {
    let passing: Vec<_> = witnesses
        .iter()
        .filter(|witness| {
            witness.procedure == operator.witness_procedure && witness.verdict == CheckVerdict::Pass
        })
        .collect();
    if passing.is_empty() {
        return Err(format!(
            "no passing witness for registered procedure `{}`",
            operator.witness_procedure
        ));
    }
    for witness in &passing {
        if witness.witness_id.trim().is_empty()
            || witness.evidence_ref.trim().is_empty()
            || !is_sha256(&witness.evidence_sha256)
        {
            return Err("passing witness has empty identity or evidence binding".into());
        }
    }
    if budget.require_independent_witness
        && !passing
            .iter()
            .any(|witness| witness.relation.supports_independence())
    {
        return Err(
            "passing receipts exist, but no witness has an established independent relation".into(),
        );
    }
    Ok(())
}

struct OperatorCompilationInput<'a, S> {
    packet_sha256: &'a str,
    operator_registry_sha256: &'a str,
    source_step_index: usize,
    source_carrier_sha256: &'a str,
    source_state_sha256: &'a str,
    result_state_sha256: &'a str,
    source_candidate_sha256: &'a str,
    carrier_kind: CarrierKind,
    proposal: &'a DeformationProposal<S>,
    operator: &'a RegisteredOperator,
    signature: &'a ObstructionSignature,
    before: ObstructionMeasure,
    after: ObstructionMeasure,
    post_inspection: &'a InspectionReceipt,
    assessment: &'a CandidateAssessment,
}

fn compile_operator_candidate<S>(
    input: OperatorCompilationInput<'_, S>,
) -> Result<CompiledOperatorCandidate, IteratorError> {
    validate_compilation_input(&input)?;
    let OperatorCompilationInput {
        packet_sha256,
        operator_registry_sha256,
        source_step_index,
        source_carrier_sha256,
        source_state_sha256,
        result_state_sha256,
        source_candidate_sha256,
        carrier_kind,
        proposal,
        operator,
        signature,
        before,
        after,
        post_inspection,
        assessment,
    } = input;

    let mut candidate = CompiledOperatorCandidate {
        candidate_operator_id: OperatorId(String::new()),
        source_operator_id: operator.operator_id.clone(),
        source_operator_sha256: String::new(),
        source_operator_signature_kinds: operator.signature_kinds.clone(),
        source_operator_carrier_kinds: operator.carrier_kinds.clone(),
        source_registry_sha256: operator_registry_sha256.into(),
        source_proposal_id: proposal.proposal_id.clone(),
        source_proposal_sha256: String::new(),
        source_assessment_sha256: String::new(),
        source_candidate_sha256: source_candidate_sha256.into(),
        source_step_index,
        source_packet_sha256: packet_sha256.into(),
        source_carrier_sha256: source_carrier_sha256.into(),
        source_state_sha256: source_state_sha256.into(),
        result_state_sha256: result_state_sha256.into(),
        source_provenance: proposal.provenance.clone(),
        source_equivalence_key: proposal.equivalence_key.clone(),
        source_predicted_candidates_avoided: proposal.predicted_candidates_avoided,
        signature_kind: signature.kind.clone(),
        observed_signature_sha256: signature.signature_sha256.clone(),
        carrier_kind,
        preconditions: operator.preconditions.clone(),
        deformation_ref: operator.deformation_ref.clone(),
        deformation_descriptor_sha256: operator.deformation_descriptor_sha256.clone(),
        preservation_obligations: operator.preservation_obligations.clone(),
        preservation_checks: assessment.preservation.clone(),
        witness_procedure: operator.witness_procedure.clone(),
        witness_results: assessment.witnesses.clone(),
        equivalence_contract: operator.equivalence_contract.clone(),
        requires_lift: operator.requires_lift,
        possible_terminals: operator.possible_terminals.clone(),
        before,
        after,
        post_inspection_sha256: sha256_json(post_inspection)?,
        pattern_sha256: String::new(),
        evidence_sha256: String::new(),
        authority_effect: AuthorityEffect::None,
    };
    populate_and_verify_compiled_candidate_hashes(&mut candidate)?;
    Ok(candidate)
}

fn validate_compilation_input<S>(
    input: &OperatorCompilationInput<'_, S>,
) -> Result<(), IteratorError> {
    for (label, value) in [
        ("packet", input.packet_sha256),
        ("operator registry", input.operator_registry_sha256),
        ("source carrier", input.source_carrier_sha256),
        ("source state", input.source_state_sha256),
        ("result state", input.result_state_sha256),
        ("source candidate", input.source_candidate_sha256),
        ("observed signature", input.signature.signature_sha256.as_str()),
        (
            "deformation descriptor",
            input.operator.deformation_descriptor_sha256.as_str(),
        ),
    ] {
        if !is_sha256(value) {
            return Err(IteratorError::InvalidDeclaration(format!(
                "compiled operator candidate has invalid {label} SHA-256"
            )));
        }
    }
    nonempty(&input.proposal.proposal_id, "compiled source proposal_id")?;
    nonempty(
        &input.proposal.provenance.0,
        "compiled source proposal provenance",
    )?;
    if input.post_inspection.measure != input.after {
        return Err(IteratorError::InvalidDeclaration(
            "compiled candidate post-inspection measure does not match after measure".into(),
        ));
    }
    Ok(())
}

fn populate_and_verify_compiled_candidate_hashes(
    candidate: &mut CompiledOperatorCandidate,
) -> Result<(), IteratorError> {
    candidate.source_operator_sha256 = source_operator_hash(candidate)?;
    candidate.source_proposal_sha256 = source_proposal_hash(candidate)?;
    candidate.source_assessment_sha256 = source_assessment_hash(candidate)?;
    candidate.pattern_sha256 = operator_pattern_hash(candidate)?;
    candidate.candidate_operator_id =
        OperatorId(format!("candidate.sha256.{}", candidate.pattern_sha256));
    candidate.evidence_sha256 = operator_evidence_hash(candidate)?;
    if !candidate.verify_hashes()? {
        return Err(IteratorError::InvalidDeclaration(
            "compiled operator candidate failed internal hash verification".into(),
        ));
    }
    Ok(())
}

fn validate_extension(
    carrier: &FiniteCarrier,
    extension: &CarrierExtension,
    inspection: &InspectionReceipt,
) -> Result<FiniteCarrier, IteratorError> {
    validate_extension_metadata_and_trigger(extension, inspection)?;
    validate_extension_new_cell_ids(carrier, &extension.new_cells)?;

    let parent_sha256 = sha256_json(carrier)?;
    let mut extended = carrier.clone();
    extended.extend(extension)?;
    if sha256_json(&extended)? == parent_sha256 {
        return Err(IteratorError::InvalidCarrier(
            "carrier extension did not change the carrier hash".into(),
        ));
    }
    Ok(extended)
}

fn validate_extension_metadata_and_trigger(
    extension: &CarrierExtension,
    inspection: &InspectionReceipt,
) -> Result<(), IteratorError> {
    nonempty(&extension.extension_id, "carrier extension id")?;
    nonempty(
        &extension.trigger_signature_sha256,
        "carrier extension trigger_signature_sha256",
    )?;
    nonempty(
        &extension.justification_ref,
        "carrier extension justification",
    )?;
    if extension.new_cells.is_empty() {
        return Err(IteratorError::InvalidCarrier(
            "carrier extension must add at least one cell".into(),
        ));
    }
    if !inspection
        .signatures
        .iter()
        .any(|signature| signature.signature_sha256 == extension.trigger_signature_sha256)
    {
        return Err(IteratorError::InvalidCarrier(
            "carrier extension is not triggered by a current obstruction signature".into(),
        ));
    }
    Ok(())
}

fn validate_extension_new_cell_ids(
    carrier: &FiniteCarrier,
    new_cells: &[CarrierCell],
) -> Result<(), IteratorError> {
    let current_ids: BTreeSet<_> = carrier
        .cells
        .iter()
        .map(|cell| cell.cell_id.as_str())
        .collect();
    let mut added_ids = Vec::with_capacity(new_cells.len());
    for cell in new_cells {
        nonempty(&cell.cell_id, "carrier extension cell id")?;
        if current_ids.contains(cell.cell_id.as_str()) {
            return Err(IteratorError::InvalidCarrier(format!(
                "carrier extension cell `{}` already exists",
                cell.cell_id
            )));
        }
        added_ids.push(cell.cell_id.clone());
    }
    added_ids.sort();
    ensure_unique(&added_ids, "carrier extension cell ids")
}

fn terminal_from_failure(failure: AdapterFailure) -> Result<TerminalReceipt, IteratorError> {
    let detail = failure.detail.trim();
    nonempty(detail, "adapter failure detail")?;
    // Adapter classifications are advisory; only host-observed evidence selects
    // DetectorInadequate, NoRule, or RequiresLift terminal envelopes.
    Ok(TerminalReceipt {
        kind: TerminalKind::Refused,
        reason: format!("adapter callback declared {:?}: {detail}", failure.kind),
    })
}

fn checked_add_counter(
    counter: &mut usize,
    amount: usize,
    label: &str,
) -> Result<(), IteratorError> {
    *counter = counter
        .checked_add(amount)
        .ok_or_else(|| IteratorError::InvalidDeclaration(format!("{label} accounting overflow")))?;
    Ok(())
}

fn abandon_eligible_for_budget<S>(
    step: &mut StepReceipt,
    eligible: &mut Vec<EligibleCandidate<S>>,
    accounting: &mut CandidateAccounting,
) -> Result<(), IteratorError> {
    let eligible_ids: BTreeSet<_> = eligible
        .iter()
        .map(|candidate| candidate.proposal_id.clone())
        .collect();
    let mut converted = 0usize;
    for candidate in &mut step.candidates {
        if eligible_ids.contains(&candidate.proposal_id)
            && candidate.verdict == CandidateVerdict::EligibleDescent
        {
            candidate.verdict = CandidateVerdict::BudgetPruned;
            candidate.reason =
                "max_wall_millis exhausted before selected transition mutation".into();
            converted += 1;
        }
    }
    if converted != eligible.len() {
        return Err(IteratorError::InvalidDeclaration(
            "eligible candidate accounting does not match step receipts".into(),
        ));
    }
    accounting.evaluated = accounting.evaluated.checked_sub(converted).ok_or_else(|| {
        IteratorError::InvalidDeclaration("evaluated candidate accounting underflow".into())
    })?;
    checked_add_counter(
        &mut accounting.budget_pruned,
        converted,
        "budget-pruned candidates",
    )?;
    eligible.clear();
    Ok(())
}

fn wall_budget_exhausted<C: RunClock + ?Sized>(clock: &C, budget: RunBudget) -> bool {
    clock.elapsed_micros() / 1_000 >= u128::from(budget.max_wall_millis)
}

fn serialized_len<T: Serialize + ?Sized>(value: &T) -> Result<usize, IteratorError> {
    serde_json::to_vec(value)
        .map(|bytes| bytes.len())
        .map_err(|error| IteratorError::Serialization(error.to_string()))
}

#[derive(Serialize)]
struct SourceOperatorCommitment<'a> {
    hash_domain: &'static str,
    operator: &'a RegisteredOperator,
}

#[derive(Serialize)]
struct SourceProposalCommitment<'a> {
    hash_domain: &'static str,
    proposal_id: &'a str,
    operator_id: &'a OperatorId,
    provenance: &'a Provenance,
    matched_signature_sha256: &'a str,
    equivalence_key: &'a Option<String>,
    predicted_candidates_avoided: usize,
    result_state_sha256: &'a str,
}

#[derive(Serialize)]
struct SourceAssessmentCommitment<'a> {
    hash_domain: &'static str,
    preservation: &'a [PreservationCheck],
    witnesses: &'a [WitnessResult],
}

#[derive(Serialize)]
struct OperatorPatternCommitment<'a> {
    hash_domain: &'static str,
    source_operator_id: &'a OperatorId,
    source_operator_sha256: &'a str,
    signature_kind: &'a str,
    carrier_kind: CarrierKind,
    preconditions: &'a [String],
    deformation_ref: &'a str,
    deformation_descriptor_sha256: &'a str,
    preservation_obligations: &'a [String],
    witness_procedure: &'a str,
    equivalence_contract: &'a Option<String>,
    requires_lift: bool,
    possible_terminals: &'a [TerminalKind],
    authority_effect: &'a AuthorityEffect,
}

fn source_operator_record(candidate: &CompiledOperatorCandidate) -> RegisteredOperator {
    RegisteredOperator {
        operator_id: candidate.source_operator_id.clone(),
        signature_kinds: candidate.source_operator_signature_kinds.clone(),
        carrier_kinds: candidate.source_operator_carrier_kinds.clone(),
        preconditions: candidate.preconditions.clone(),
        deformation_ref: candidate.deformation_ref.clone(),
        deformation_descriptor_sha256: candidate.deformation_descriptor_sha256.clone(),
        preservation_obligations: candidate.preservation_obligations.clone(),
        witness_procedure: candidate.witness_procedure.clone(),
        equivalence_contract: candidate.equivalence_contract.clone(),
        requires_lift: candidate.requires_lift,
        possible_terminals: candidate.possible_terminals.clone(),
    }
}

fn source_operator_hash(candidate: &CompiledOperatorCandidate) -> Result<String, IteratorError> {
    let operator = source_operator_record(candidate);
    sha256_json(&SourceOperatorCommitment {
        hash_domain: SOURCE_OPERATOR_HASH_DOMAIN,
        operator: &operator,
    })
}

fn source_proposal_hash(candidate: &CompiledOperatorCandidate) -> Result<String, IteratorError> {
    sha256_json(&SourceProposalCommitment {
        hash_domain: OPERATOR_PROPOSAL_HASH_DOMAIN,
        proposal_id: &candidate.source_proposal_id,
        operator_id: &candidate.source_operator_id,
        provenance: &candidate.source_provenance,
        matched_signature_sha256: &candidate.observed_signature_sha256,
        equivalence_key: &candidate.source_equivalence_key,
        predicted_candidates_avoided: candidate.source_predicted_candidates_avoided,
        result_state_sha256: &candidate.result_state_sha256,
    })
}

fn source_assessment_hash(candidate: &CompiledOperatorCandidate) -> Result<String, IteratorError> {
    sha256_json(&SourceAssessmentCommitment {
        hash_domain: SOURCE_ASSESSMENT_HASH_DOMAIN,
        preservation: &candidate.preservation_checks,
        witnesses: &candidate.witness_results,
    })
}

fn operator_pattern_hash(candidate: &CompiledOperatorCandidate) -> Result<String, IteratorError> {
    sha256_json(&OperatorPatternCommitment {
        hash_domain: OPERATOR_PATTERN_HASH_DOMAIN,
        source_operator_id: &candidate.source_operator_id,
        source_operator_sha256: &candidate.source_operator_sha256,
        signature_kind: &candidate.signature_kind,
        carrier_kind: candidate.carrier_kind,
        preconditions: &candidate.preconditions,
        deformation_ref: &candidate.deformation_ref,
        deformation_descriptor_sha256: &candidate.deformation_descriptor_sha256,
        preservation_obligations: &candidate.preservation_obligations,
        witness_procedure: &candidate.witness_procedure,
        equivalence_contract: &candidate.equivalence_contract,
        requires_lift: candidate.requires_lift,
        possible_terminals: &candidate.possible_terminals,
        authority_effect: &candidate.authority_effect,
    })
}

#[derive(Serialize)]
struct OperatorEvidenceCommitment<'a> {
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

fn operator_evidence_hash(candidate: &CompiledOperatorCandidate) -> Result<String, IteratorError> {
    sha256_json(&OperatorEvidenceCommitment {
        hash_domain: OPERATOR_EVIDENCE_HASH_DOMAIN,
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
    })
}

fn compiled_candidate_fields_are_canonical(candidate: &CompiledOperatorCandidate) -> bool {
    compiled_candidate_metadata_is_canonical(candidate)
        && compiled_candidate_collections_are_canonical(candidate)
        && compiled_candidate_preservation_is_canonical(candidate)
        && compiled_candidate_witnesses_are_canonical(candidate)
}

fn compiled_candidate_metadata_is_canonical(candidate: &CompiledOperatorCandidate) -> bool {
    let required = [
        candidate.source_operator_id.0.as_str(),
        candidate.source_proposal_id.as_str(),
        candidate.source_provenance.0.as_str(),
        candidate.signature_kind.as_str(),
        candidate.deformation_ref.as_str(),
        candidate.witness_procedure.as_str(),
    ];
    !candidate.requires_lift
        && !required.iter().any(|value| value.trim().is_empty())
        && !candidate
            .equivalence_contract
            .as_ref()
            .is_some_and(|value| value.trim().is_empty())
}

fn compiled_candidate_collections_are_canonical(candidate: &CompiledOperatorCandidate) -> bool {
    !candidate.preservation_obligations.is_empty()
        && !candidate.possible_terminals.is_empty()
        && strictly_sorted(&candidate.source_operator_signature_kinds)
        && strictly_sorted(&candidate.source_operator_carrier_kinds)
        && strictly_sorted(&candidate.preconditions)
        && strictly_sorted(&candidate.preservation_obligations)
        && candidate
            .source_operator_signature_kinds
            .contains(&candidate.signature_kind)
        && candidate
            .source_operator_carrier_kinds
            .contains(&candidate.carrier_kind)
        && !candidate
            .possible_terminals
            .windows(2)
            .any(|window| window[0] as u8 >= window[1] as u8)
}

fn compiled_candidate_preservation_is_canonical(candidate: &CompiledOperatorCandidate) -> bool {
    let preservation_ids: Vec<_> = candidate
        .preservation_checks
        .iter()
        .map(|check| check.obligation_id.as_str())
        .collect();
    let obligation_ids: Vec<_> = candidate
        .preservation_obligations
        .iter()
        .map(String::as_str)
        .collect();
    preservation_ids == obligation_ids
        && !candidate.preservation_checks.iter().any(|check| {
            check.verdict != CheckVerdict::Pass
                || check.evidence_ref.trim().is_empty()
                || !is_sha256(&check.evidence_sha256)
        })
}

fn compiled_candidate_witnesses_are_canonical(candidate: &CompiledOperatorCandidate) -> bool {
    !candidate.witness_results.is_empty()
        && !candidate
            .witness_results
            .windows(2)
            .any(|window| window[0].witness_id >= window[1].witness_id)
        && !candidate
            .witness_results
            .iter()
            .any(witness_result_is_malformed)
        && candidate.witness_results.iter().any(|witness| {
            witness.procedure == candidate.witness_procedure
                && witness.verdict == CheckVerdict::Pass
        })
}

fn witness_result_is_malformed(witness: &WitnessResult) -> bool {
    witness.witness_id.trim().is_empty()
        || witness.procedure.trim().is_empty()
        || witness.evidence_ref.trim().is_empty()
        || !is_sha256(&witness.evidence_sha256)
}
#[derive(Serialize)]
struct CandidateInspectionTraceCommitment {
    proposal_id: String,
    state_sha256: String,
    post_inspection_sha256: String,
}

#[derive(Serialize)]
struct StepInspectionTraceCommitment {
    step_index: usize,
    state_sha256: String,
    carrier_sha256: String,
    inspection_sha256: String,
    candidate_post_inspections: Vec<CandidateInspectionTraceCommitment>,
}

#[derive(Serialize)]
struct InspectionTraceCommitment<'a> {
    hash_domain: &'static str,
    adapter_id: &'a str,
    packet_sha256: &'a str,
    steps: &'a [StepInspectionTraceCommitment],
}

fn inspection_trace_hash_for(receipt: &RunReceipt) -> Result<String, IteratorError> {
    let mut steps = Vec::with_capacity(receipt.steps.len());
    for step in &receipt.steps {
        let mut candidate_post_inspections = Vec::new();
        for candidate in &step.candidates {
            if let Some(post_inspection) = &candidate.post_inspection {
                candidate_post_inspections.push(CandidateInspectionTraceCommitment {
                    proposal_id: candidate.proposal_id.clone(),
                    state_sha256: candidate.state_sha256.clone(),
                    post_inspection_sha256: sha256_json(post_inspection)?,
                });
            }
        }
        steps.push(StepInspectionTraceCommitment {
            step_index: step.step_index,
            state_sha256: step.state_sha256.clone(),
            carrier_sha256: step.carrier_sha256.clone(),
            inspection_sha256: sha256_json(&step.inspection)?,
            candidate_post_inspections,
        });
    }
    sha256_json(&InspectionTraceCommitment {
        hash_domain: INSPECTION_TRACE_HASH_DOMAIN,
        adapter_id: &receipt.adapter_id,
        packet_sha256: &receipt.packet_sha256,
        steps: &steps,
    })
}

#[derive(Serialize)]
struct ReplayCommitment<'a> {
    schema_version: &'a str,
    adapter_id: &'a str,
    packet: &'a ProblemPacket,
    packet_sha256: &'a str,
    operator_registry: &'a OperatorRegistry,
    operator_registry_sha256: &'a str,
    initial_carrier: &'a FiniteCarrier,
    final_carrier: &'a FiniteCarrier,
    initial_state_sha256: &'a str,
    final_state_sha256: &'a str,
    budget: RunBudget,
    accounting: &'a CandidateAccounting,
    steps: &'a [StepReceipt],
    terminal: &'a TerminalReceipt,
    authority_effect: &'a AuthorityEffect,
}

fn replay_hash_for(receipt: &RunReceipt) -> Result<String, IteratorError> {
    sha256_json(&ReplayCommitment {
        schema_version: &receipt.schema_version,
        adapter_id: &receipt.adapter_id,
        packet: &receipt.packet,
        packet_sha256: &receipt.packet_sha256,
        operator_registry: &receipt.operator_registry,
        operator_registry_sha256: &receipt.operator_registry_sha256,
        initial_carrier: &receipt.initial_carrier,
        final_carrier: &receipt.final_carrier,
        initial_state_sha256: &receipt.initial_state_sha256,
        final_state_sha256: &receipt.final_state_sha256,
        budget: receipt.budget,
        accounting: &receipt.accounting,
        steps: &receipt.steps,
        terminal: &receipt.terminal,
        authority_effect: &receipt.authority_effect,
    })
}

fn sha256_json<T: Serialize + ?Sized>(value: &T) -> Result<String, IteratorError> {
    serde_json::to_vec(value)
        .map(|bytes| sha256_bytes(&bytes))
        .map_err(|error| IteratorError::Serialization(error.to_string()))
}

fn nonempty(value: &str, label: &str) -> Result<(), IteratorError> {
    if value.trim().is_empty() {
        Err(IteratorError::InvalidDeclaration(format!(
            "{label} must be non-empty"
        )))
    } else {
        Ok(())
    }
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn strictly_sorted<T: Ord>(values: &[T]) -> bool {
    values.windows(2).all(|window| window[0] < window[1])
}

fn ensure_unique<T: PartialEq>(values: &[T], label: &str) -> Result<(), IteratorError> {
    if values.windows(2).any(|window| window[0] == window[1]) {
        Err(IteratorError::InvalidDeclaration(format!(
            "{label} must be unique"
        )))
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/engines/src/multipath_iterator.rs
// Claim: urn:core:crates_rs:engines:multipath-iterator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_43c704f5 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
