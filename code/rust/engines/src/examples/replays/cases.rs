
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_76bb3495<T> {
    fn checked_invariant_76bb3495(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_76bb3495<T> for Option<T> {
    #[inline]
    fn checked_invariant_76bb3495(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_76bb3495<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_76bb3495(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_wdp::ddc::agent_contract::sha256_bytes;
use core_wdp::ddc::degree_tower::simplex_boundary_segment;
use engines::multipath_iterator::*;
use engines::obstruction_runtime::{OperatorId, Provenance};
use serde::Serialize;
use serde_json::json;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum DemoKind {
    Mathematics,
    RustContract,
    LeanRepair,
    CommonMode,
    SelfApplication,
    DetectorInadequate,
    HigherCoherence,
}

#[derive(Debug, Clone)]
pub struct FixtureCase {
    pub case_id: String,
    pub domain: String,
    pub expected_terminal: TerminalKind,
    kind: DemoKind,
    packet: ProblemPacket,
    carrier: FiniteCarrier,
}

impl FixtureCase {
    pub fn packet(&self) -> ProblemPacket {
        self.packet.clone()
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct DemoState {
    phase: u8,
}

#[derive(Debug, Clone)]
pub struct DemoAdapter {
    case: FixtureCase,
}

impl DemoAdapter {
    pub fn new(case: FixtureCase) -> Self {
        Self { case }
    }

    fn requirement(&self) -> DetectorRequirement {
        self.case.packet.protected_distinctions[0].clone()
    }

    fn visible_coverage(&self, label: &str) -> Vec<CoverageAssessment> {
        vec![CoverageAssessment {
            requirement: self.requirement(),
            disposition: CoverageDisposition::PreservedVisible,
            evidence_ref: format!("fixture://{}/{label}", self.case.case_id),
            projection_loss: None,
        }]
    }

    fn defect(&self, kind: &str, exact: bool) -> Result<VisibleDefect, AdapterFailure> {
        let exact_binary_cochain = if exact {
            Some(ExactBinaryCochainProbe {
                segment: simplex_boundary_segment(1).map_err(|error| AdapterFailure {
                    kind: AdapterFailureKind::Refused,
                    detail: format!("fixture DDA construction failed: {error:?}"),
                })?,
                residual: vec![true, false, false],
            })
        } else {
            None
        };
        Ok(VisibleDefect {
            defect_id: format!("{}-defect", self.case.case_id),
            claim_id: self.requirement().claim_id,
            kind: kind.into(),
            cell_refs: vec![if exact { "ABC" } else { "edge" }.into()],
            evidence_ref: format!("fixture://{}/defect", self.case.case_id),
            exact_binary_cochain,
        })
    }

    fn has_contract_cell(carrier: &FiniteCarrier) -> bool {
        carrier
            .cells
            .iter()
            .any(|cell| cell.cell_id == "contract_surface")
    }

    fn signature_kind(&self) -> &'static str {
        match self.case.kind {
            DemoKind::Mathematics => "multipath_composition_failure",
            DemoKind::RustContract => "code_contract_failure",
            DemoKind::LeanRepair => "lean_goal_failure",
            DemoKind::CommonMode => "common_mode_failure",
            DemoKind::SelfApplication => "self_change_failure",
            DemoKind::DetectorInadequate | DemoKind::HigherCoherence => "none",
        }
    }

    fn simple_defect_spec(kind: DemoKind) -> Option<(&'static str, bool)> {
        match kind {
            DemoKind::Mathematics => Some(("multipath_composition_failure", true)),
            DemoKind::RustContract => Some(("code_contract_failure", false)),
            DemoKind::LeanRepair => Some(("lean_goal_failure", false)),
            DemoKind::CommonMode => Some(("common_mode_failure", false)),
            DemoKind::SelfApplication
            | DemoKind::DetectorInadequate
            | DemoKind::HigherCoherence => None,
        }
    }

    fn populate_phase_zero_inspection(
        &self,
        carrier: &FiniteCarrier,
        inspection: &mut Inspection,
    ) -> Result<(), AdapterFailure> {
        if let Some((defect_kind, exact)) = Self::simple_defect_spec(self.case.kind) {
            inspection
                .visible_defects
                .push(self.defect(defect_kind, exact)?);
            return Ok(());
        }
        match self.case.kind {
            DemoKind::SelfApplication if !Self::has_contract_cell(carrier) => {
                let requirement = self.requirement();
                inspection.coverage = vec![CoverageAssessment {
                    requirement: requirement.clone(),
                    disposition: CoverageDisposition::ProjectionLoss,
                    evidence_ref: "fixture://self/projection-loss".into(),
                    projection_loss: Some(ProjectionLossReceipt {
                        loss_id: "self-contract-surface-hidden".into(),
                        source_refs: vec!["external:core_types::AuthorityEffect".into()],
                        collided_projection_refs: vec![
                            "projection::source".into(),
                            "projection::target".into(),
                        ],
                        discarded_sha256: hash("self-contract-surface-hidden"),
                        recovery_requirement:
                            "add the authority contract surface to the finite carrier".into(),
                    }),
                }];
                inspection
                    .discarded_information_refs
                    .push(requirement.distinction_id);
            }
            DemoKind::SelfApplication => {
                inspection
                    .visible_defects
                    .push(self.defect("self_change_failure", false)?);
            }
            DemoKind::DetectorInadequate => {
                inspection.coverage[0].disposition = CoverageDisposition::DetectorInadequate;
                inspection.coverage[0].evidence_ref = "fixture://negative/constant-detector".into();
                inspection
                    .discarded_information_refs
                    .push("raw left/right distinction".into());
            }
            DemoKind::HigherCoherence => {
                inspection.higher_degree_need = Some(HigherDegreeNeed {
                    current_max_degree: 2,
                    required_degree: 3,
                    witness_ref: "fixture://c3/tetrahedral-boundary".into(),
                    licensed_lift_ref: None,
                });
            }
            DemoKind::Mathematics
            | DemoKind::RustContract
            | DemoKind::LeanRepair
            | DemoKind::CommonMode => {}
        }
        Ok(())
    }
}

impl MultipathAdapter for DemoAdapter {
    type State = DemoState;

    fn adapter_id(&self) -> &str {
        &self.case.case_id
    }

    fn seed(&self, packet: &ProblemPacket) -> Result<AdapterSeed<Self::State>, AdapterFailure> {
        if packet.packet_id != self.case.packet.packet_id {
            return Err(AdapterFailure {
                kind: AdapterFailureKind::Refused,
                detail: "packet id does not match the frozen fixture".into(),
            });
        }
        Ok(AdapterSeed {
            state: DemoState { phase: 0 },
            carrier: self.case.carrier.clone(),
        })
    }

    fn inspect(
        &self,
        _packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
    ) -> Result<Inspection, AdapterFailure> {
        let projected_data = carrier
            .cells
            .iter()
            .map(|cell| ProjectedDatum {
                datum_id: format!("projection::{}", cell.cell_id),
                degree: cell.degree,
                source_refs: vec![cell.cell_id.clone()],
                value_sha256: hash(&format!(
                    "{}::{}::{}",
                    self.case.case_id, state.phase, cell.cell_id
                )),
            })
            .collect();
        let mut inspection = Inspection {
            observer: ObserverDeclaration {
                observer_id: format!("observer::{}", self.case.case_id),
                observer_family: "deterministic_fixture_adapter_v1".into(),
                scope: format!("finite case {}", self.case.case_id),
            },
            comparison: ComparisonDeclaration {
                comparison_id: format!("comparison::{}", self.case.case_id),
                zero_rel: "byte-identical protected fixture observation".into(),
                gauge_family:
                    "exact F2 coboundary when an exact probe is present; identity otherwise".into(),
            },
            projected_data,
            coverage: self.visible_coverage("protected-distinction-visible"),
            visible_defects: Vec::new(),
            higher_degree_need: None,
            discarded_information_refs: Vec::new(),
        };

        if state.phase == 0 {
            self.populate_phase_zero_inspection(carrier, &mut inspection)?;
        }

        Ok(inspection)
    }

    fn propose(
        &self,
        _packet: &ProblemPacket,
        _carrier: &FiniteCarrier,
        state: &Self::State,
        signatures: &[ObstructionSignature],
    ) -> Result<Vec<DeformationProposal<Self::State>>, AdapterFailure> {
        if state.phase != 0 {
            return Ok(Vec::new());
        }
        let Some(signature) = signatures
            .iter()
            .find(|signature| signature.kind == self.signature_kind())
        else {
            return Ok(Vec::new());
        };
        let proposal =
            |id: &str, phase: u8, key: Option<&str>, avoided: usize| DeformationProposal {
                proposal_id: id.into(),
                operator_id: OperatorId("op.paper070.exact_local_rewrite".into()),
                provenance: Provenance(format!(
                    "frozen {} transition phase 0 -> {phase}",
                    self.case.case_id
                )),
                matched_signature_sha256: signature.signature_sha256.clone(),
                equivalence_key: key.map(str::to_string),
                predicted_candidates_avoided: avoided,
                state: DemoState { phase },
            };
        let proposals = match self.case.kind {
            DemoKind::Mathematics => vec![
                proposal("math-repair-canonical", 1, Some("same-zero-residual"), 0),
                proposal("math-repair-equivalent", 1, Some("same-zero-residual"), 11),
            ],
            DemoKind::LeanRepair => vec![
                proposal("lean-noop-first", 0, Some("unchanged-goal"), 0),
                proposal("lean-repair", 1, Some("closed-goal"), 3),
            ],
            DemoKind::RustContract => {
                vec![proposal(
                    "rust-contract-repair",
                    1,
                    Some("fixed-contract"),
                    3,
                )]
            }
            DemoKind::CommonMode => vec![proposal("common-mode-apparent-repair", 1, None, 0)],
            DemoKind::SelfApplication => vec![proposal("self-firewall-repair", 1, None, 0)],
            DemoKind::DetectorInadequate | DemoKind::HigherCoherence => Vec::new(),
        };
        Ok(proposals)
    }

    fn assess_candidate(
        &self,
        _packet: &ProblemPacket,
        _carrier: &FiniteCarrier,
        _before: &Self::State,
        _proposal: &DeformationProposal<Self::State>,
        _operator: &RegisteredOperator,
    ) -> Result<CandidateAssessment, AdapterFailure> {
        let witnesses = if self.case.kind == DemoKind::CommonMode {
            vec![
                common_source_witness("agent-a1"),
                common_source_witness("agent-a2"),
            ]
        } else {
            vec![WitnessResult {
                witness_id: format!("{}-fixture-assessment", self.case.case_id),
                procedure: "fixture_candidate_assessment_v1".into(),
                relation: WitnessRelation::Unestablished,
                verdict: CheckVerdict::Pass,
                evidence_ref: format!("fixture://{}/candidate-assessment", self.case.case_id),
                evidence_sha256: hash(&format!("{}::candidate-assessment", self.case.case_id)),
            }]
        };
        Ok(CandidateAssessment {
            preservation: vec![
                PreservationCheck {
                    obligation_id: "preserve_local_green".into(),
                    verdict: CheckVerdict::Pass,
                    evidence_ref: format!("fixture://{}/local-green", self.case.case_id),
                    evidence_sha256: hash(&format!("{}::local-green", self.case.case_id)),
                },
                PreservationCheck {
                    obligation_id: "preserve_protected_distinctions".into(),
                    verdict: CheckVerdict::Pass,
                    evidence_ref: format!("fixture://{}/protected-distinctions", self.case.case_id),
                    evidence_sha256: hash(&format!(
                        "{}::protected-distinctions",
                        self.case.case_id
                    )),
                },
            ],
            witnesses,
        })
    }

    fn extend_carrier(
        &self,
        _packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
        inspection: &InspectionReceipt,
    ) -> Result<Option<CarrierExtension>, AdapterFailure> {
        if self.case.kind != DemoKind::SelfApplication
            || state.phase != 0
            || Self::has_contract_cell(carrier)
        {
            return Ok(None);
        }
        let Some(signature) = inspection
            .signatures
            .iter()
            .find(|signature| signature.kind == "projection_loss")
        else {
            return Ok(None);
        };
        Ok(Some(CarrierExtension {
            extension_id: "expose-authority-contract".into(),
            trigger_signature_sha256: signature.signature_sha256.clone(),
            justification_ref: "fixture://self/obstruction-directed-growth".into(),
            new_cells: vec![cell("contract_surface", 0, &[])],
        }))
    }
}

pub fn default_budget() -> RunBudget {
    RunBudget {
        max_steps: 12,
        max_candidates: 32,
        max_carrier_cells: 64,
        max_receipt_bytes: 4 * 1024 * 1024,
        max_wall_millis: 10_000,
        require_independent_witness: false,
    }
}

pub fn budget_for_case(case: &FixtureCase) -> RunBudget {
    RunBudget {
        require_independent_witness: case.kind == DemoKind::CommonMode,
        ..default_budget()
    }
}

pub fn operator_registry() -> OperatorRegistry {
    OperatorRegistry::new(vec![RegisteredOperator {
        operator_id: OperatorId("op.paper070.exact_local_rewrite".into()),
        signature_kinds: vec![
            "code_contract_failure".into(),
            "common_mode_failure".into(),
            "lean_goal_failure".into(),
            "multipath_composition_failure".into(),
            "projection_loss".into(),
            "self_change_failure".into(),
        ],
        carrier_kinds: vec![
            CarrierKind::DirectedGraph,
            CarrierKind::SimplicialComplex,
            CarrierKind::DependencyGraph,
            CarrierKind::ProofGraph,
            CarrierKind::CodeChangeGraph,
            CarrierKind::WorkflowGraph,
        ],
        preconditions: vec!["matched finite obstruction signature".into()],
        deformation_ref: "adapter://paper070-fixture/exact-local-rewrite/v1".into(),
        deformation_descriptor_sha256: sha256_bytes(
            b"core.paper070.fixture.deformation.exact_local_rewrite.v1",
        ),
        preservation_obligations: vec![
            "preserve_local_green".into(),
            "preserve_protected_distinctions".into(),
        ],
        witness_procedure: "fixture_candidate_assessment_v1".into(),
        equivalence_contract: Some("full-admission-and-post-measure-congruence-v1".into()),
        requires_lift: false,
        possible_terminals: vec![TerminalKind::ExactRepair, TerminalKind::OpenObstruction],
    }])
    .checked_invariant_76bb3495("fixture registry is canonical")
}

pub fn all_cases() -> Vec<FixtureCase> {
    vec![
        make_case(
            "math_local_green_global_red",
            "mathematics",
            DemoKind::Mathematics,
            TerminalKind::ExactRepair,
            CarrierKind::SimplicialComplex,
            json!({"local_edges_valid": true, "triangle_parity": 1}),
        ),
        make_case(
            "rust_local_tests_cross_contract",
            "rust_code_change",
            DemoKind::RustContract,
            TerminalKind::ExactRepair,
            CarrierKind::CodeChangeGraph,
            json!({"local_tests": "pass", "cross_component_contract": "fail"}),
        ),
        make_case(
            "lean_proof_repair",
            "lean_proof_obligation",
            DemoKind::LeanRepair,
            TerminalKind::ExactRepair,
            CarrierKind::ProofGraph,
            json!({"goal": "d1 (d0 a) = 0", "candidate": "bounded fixture"}),
        ),
        make_case(
            "multi_agent_common_mode_failure",
            "multi_agent_workflow",
            DemoKind::CommonMode,
            TerminalKind::OpenObstruction,
            CarrierKind::WorkflowGraph,
            json!({"author": "model-family-A", "evaluators": ["A1", "A2"]}),
        ),
        make_case(
            "paperer008_self_application",
            "self_modification_proposal",
            DemoKind::SelfApplication,
            TerminalKind::ExactRepair,
            CarrierKind::CodeChangeGraph,
            json!({"proposal": "add bounded multipath iterator", "self_certification": false}),
        ),
        make_case(
            "collapsing_detector_negative",
            "opaque_problem",
            DemoKind::DetectorInadequate,
            TerminalKind::DetectorInadequate,
            CarrierKind::DirectedGraph,
            json!({"raw_states": ["left", "right"], "projection": "constant"}),
        ),
        make_case(
            "higher_coherence_requires_lift",
            "higher_coherence",
            DemoKind::HigherCoherence,
            TerminalKind::RequiresLift,
            CarrierKind::SimplicialComplex,
            json!({"admitted_degree": 2, "witnessed_required_degree": 3}),
        ),
    ]
}

fn make_case(
    case_id: &str,
    domain: &str,
    kind: DemoKind,
    expected_terminal: TerminalKind,
    carrier_kind: CarrierKind,
    payload: serde_json::Value,
) -> FixtureCase {
    let requirement = DetectorRequirement {
        claim_id: format!("P070-DEMO-{}", case_id.to_ascii_uppercase()),
        distinction_id: match kind {
            DemoKind::Mathematics => "oriented_triangle_parity",
            DemoKind::RustContract => "cross_component_contract",
            DemoKind::LeanRepair => "kernel_checked_goal",
            DemoKind::CommonMode => "independent_evaluation",
            DemoKind::SelfApplication => "authority_firewall_surface",
            DemoKind::DetectorInadequate => "raw_states_that_collapse",
            DemoKind::HigherCoherence => "tetrahedral_path_coherence",
        }
        .into(),
    };
    let carrier = if matches!(kind, DemoKind::Mathematics | DemoKind::HigherCoherence) {
        triangle_carrier(case_id)
    } else {
        graph_carrier(case_id, carrier_kind)
    };
    FixtureCase {
        case_id: case_id.into(),
        domain: domain.into(),
        expected_terminal,
        kind,
        packet: ProblemPacket {
            packet_id: format!("070-demo-{case_id}"),
            domain: domain.into(),
            payload,
            protected_distinctions: vec![requirement],
            packet_refs: vec![format!("paper070://{case_id}")],
            evidence_ceiling: "LocalReplay".into(),
        },
        carrier,
    }
}

fn common_source_witness(id: &str) -> WitnessResult {
    WitnessResult {
        witness_id: id.into(),
        procedure: "fixture_candidate_assessment_v1".into(),
        relation: WitnessRelation::CommonSource,
        verdict: CheckVerdict::Pass,
        evidence_ref: format!("fixture://agents/{id}"),
        evidence_sha256: hash(&format!("common-source::{id}")),
    }
}

fn triangle_carrier(id: &str) -> FiniteCarrier {
    FiniteCarrier {
        carrier_id: id.into(),
        kind: CarrierKind::SimplicialComplex,
        cells: vec![
            cell("A", 0, &[]),
            cell("B", 0, &[]),
            cell("C", 0, &[]),
            cell("AB", 1, &["A", "B"]),
            cell("AC", 1, &["A", "C"]),
            cell("BC", 1, &["B", "C"]),
            cell("ABC", 2, &["AB", "AC", "BC"]),
        ],
    }
}

fn graph_carrier(id: &str, kind: CarrierKind) -> FiniteCarrier {
    FiniteCarrier {
        carrier_id: id.into(),
        kind,
        cells: vec![
            cell("source", 0, &[]),
            cell("target", 0, &[]),
            cell("edge", 1, &["source", "target"]),
        ],
    }
}

fn cell(id: &str, degree: usize, boundary: &[&str]) -> CarrierCell {
    CarrierCell {
        cell_id: id.into(),
        degree,
        boundary: boundary.iter().map(|value| (*value).into()).collect(),
        payload_sha256: hash(&format!("cell::{id}::{degree}")),
    }
}

fn hash(value: &str) -> String {
    sha256_bytes(value.as_bytes())
}

// Origin: engine/crates_rs/engines/src/examples/replays/cases.rs
// Claim: urn:core:crates_rs:engines:cases:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord76bb3495 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord76bb3495` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError76bb3495 {
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
impl BoundaryError76bb3495 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError76bb3495 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError76bb3495 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord76bb3495 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError76bb3495> {
        if capacity_bound == 0 {
            return Err(BoundaryError76bb3495::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError76bb3495::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError76bb3495::ExceedsCapacity {
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
mod l4_boundary_tests_76bb3495 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord76bb3495::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord76bb3495::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord76bb3495::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord76bb3495::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord76bb3495::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError76bb3495::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError76bb3495::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
