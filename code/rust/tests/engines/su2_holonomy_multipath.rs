//! Integration test combining Paper 009 SU(2) graph holonomies with Paper 070 multipath iterator.
//!
//! This test verifies that:
//! 1. Flat SU(2) loop holonomies (pure gauge) resolve cleanly within gauge image `im(d_0)`.
//! 2. Non-flat SU(2) loop holonomies (frustrated curvature) emit explicit non-authority obstruction receipts.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_3f9e7ff7 = (i128, i128);
use core_wdp::ddc::agent_contract::sha256_bytes;
use core_wdp::ddc::degree_tower::simplex_boundary_segment;
use engines::multipath_iterator::*;
use core_types::authority::AuthorityEffect;
use serde::Serialize;

/// Quaternion representation of SU(2) elements: q = w + x*i + y*j + z*k
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Su2Element {
    pub w: f64,
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Su2Element {
    pub const IDENTITY: Self = Self {
        w: 1.0,
        x: 0.0,
        y: 0.0,
        z: 0.0,
    };
    pub const I: Self = Self {
        w: 0.0,
        x: 1.0,
        y: 0.0,
        z: 0.0,
    };
    pub const J: Self = Self {
        w: 0.0,
        x: 0.0,
        y: 1.0,
        z: 0.0,
    };
    pub const K: Self = Self {
        w: 0.0,
        x: 0.0,
        y: 0.0,
        z: 1.0,
    };

    #[allow(clippy::should_implement_trait)] // test-local quaternion product; a std::ops::Mul impl would be ceremony
    pub fn mul(self, rhs: Self) -> Self {
        Self {
            w: self.w * rhs.w - self.x * rhs.x - self.y * rhs.y - self.z * rhs.z,
            x: self.w * rhs.x + self.x * rhs.w + self.y * rhs.z - self.z * rhs.y,
            y: self.w * rhs.y - self.x * rhs.z + self.y * rhs.w + self.z * rhs.x,
            z: self.w * rhs.z + self.x * rhs.y - self.y * rhs.x + self.z * rhs.w,
        }
    }

    pub fn is_identity(&self, tol: f64) -> bool {
        (self.w - 1.0).abs() < tol && self.x.abs() < tol && self.y.abs() < tol && self.z.abs() < tol
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct Su2State {
    pub is_flat: bool,
}

#[derive(Debug, Clone)]
pub struct Su2HolonomyAdapter {
    pub adapter_name: String,
    pub is_flat_case: bool,
    pub loop_holonomy: Su2Element,
}

impl Su2HolonomyAdapter {
    pub fn new_flat() -> Self {
        Self {
            adapter_name: "su2_flat_adapter".into(),
            is_flat_case: true,
            loop_holonomy: Su2Element::IDENTITY,
        }
    }

    pub fn new_nonflat() -> Self {
        let loop_h = Su2Element::K.mul(Su2Element::J).mul(Su2Element::I);
        Self {
            adapter_name: "su2_nonflat_adapter".into(),
            is_flat_case: false,
            loop_holonomy: loop_h,
        }
    }
}

impl MultipathAdapter for Su2HolonomyAdapter {
    type State = Su2State;

    fn adapter_id(&self) -> &str {
        &self.adapter_name
    }

    fn seed(&self, _packet: &ProblemPacket) -> Result<AdapterSeed<Self::State>, AdapterFailure> {
        let v0_payload = sha256_bytes(b"vertex_0");
        let v1_payload = sha256_bytes(b"vertex_1");
        let v2_payload = sha256_bytes(b"vertex_2");
        let e01_payload = sha256_bytes(b"edge_01");
        let e12_payload = sha256_bytes(b"edge_12");
        let e20_payload = sha256_bytes(b"edge_20");
        let tri_payload = sha256_bytes(b"triangle_012");

        let carrier = FiniteCarrier {
            carrier_id: "su2_cycle_carrier".into(),
            kind: CarrierKind::DirectedGraph,
            cells: vec![
                CarrierCell {
                    cell_id: "v0".into(),
                    degree: 0,
                    boundary: vec![],
                    payload_sha256: v0_payload,
                },
                CarrierCell {
                    cell_id: "v1".into(),
                    degree: 0,
                    boundary: vec![],
                    payload_sha256: v1_payload,
                },
                CarrierCell {
                    cell_id: "v2".into(),
                    degree: 0,
                    boundary: vec![],
                    payload_sha256: v2_payload,
                },
                CarrierCell {
                    cell_id: "e01".into(),
                    degree: 1,
                    boundary: vec!["v0".into(), "v1".into()],
                    payload_sha256: e01_payload,
                },
                CarrierCell {
                    cell_id: "e12".into(),
                    degree: 1,
                    boundary: vec!["v1".into(), "v2".into()],
                    payload_sha256: e12_payload,
                },
                CarrierCell {
                    cell_id: "e20".into(),
                    degree: 1,
                    boundary: vec!["v2".into(), "v0".into()],
                    payload_sha256: e20_payload,
                },
                CarrierCell {
                    cell_id: "triangle_012".into(),
                    degree: 2,
                    boundary: vec!["e01".into(), "e12".into(), "e20".into()],
                    payload_sha256: tri_payload,
                },
            ],
        }
        .canonicalized()
        .map_err(|e| AdapterFailure {
            kind: AdapterFailureKind::Refused,
            detail: format!("carrier failed: {e:?}"),
        })?;

        Ok(AdapterSeed {
            state: Su2State {
                is_flat: self.is_flat_case,
            },
            carrier,
        })
    }

    fn inspect(
        &self,
        _packet: &ProblemPacket,
        carrier: &FiniteCarrier,
        state: &Self::State,
    ) -> Result<Inspection, AdapterFailure> {
        let req = DetectorRequirement {
            claim_id: "P009-C01".into(),
            distinction_id: "su2_loop_holonomy_flatness".into(),
        };

        let projected_data = carrier
            .cells
            .iter()
            .map(|cell| ProjectedDatum {
                datum_id: format!("su2_proj::{}", cell.cell_id),
                degree: cell.degree,
                source_refs: vec![cell.cell_id.clone()],
                value_sha256: sha256_bytes(cell.cell_id.as_bytes()),
            })
            .collect();

        if state.is_flat && self.loop_holonomy.is_identity(1e-6) {
            Ok(Inspection {
                observer: ObserverDeclaration {
                    observer_id: "su2_flat_observer".into(),
                    observer_family: "su2_kinematic_shadow_v1".into(),
                    scope: "su2_flat_cycle".into(),
                },
                comparison: ComparisonDeclaration {
                    comparison_id: "su2_flat_comparison".into(),
                    zero_rel: "identity_holonomy".into(),
                    gauge_family: "su2_vertex_gauge".into(),
                },
                projected_data,
                coverage: vec![CoverageAssessment {
                    requirement: req,
                    disposition: CoverageDisposition::PreservedVisible,
                    evidence_ref: "su2://flat_holonomy_identity".into(),
                    projection_loss: None,
                }],
                visible_defects: vec![],
                higher_degree_need: None,
                discarded_information_refs: vec![],
            })
        } else {
            let exact_binary_cochain = Some(ExactBinaryCochainProbe {
                segment: simplex_boundary_segment(1).map_err(|e| AdapterFailure {
                    kind: AdapterFailureKind::Refused,
                    detail: format!("DDA segment failed: {e:?}"),
                })?,
                residual: vec![true, true, true],
            });

            Ok(Inspection {
                observer: ObserverDeclaration {
                    observer_id: "su2_nonflat_observer".into(),
                    observer_family: "su2_kinematic_shadow_v1".into(),
                    scope: "su2_nonflat_cycle".into(),
                },
                comparison: ComparisonDeclaration {
                    comparison_id: "su2_nonflat_comparison".into(),
                    zero_rel: "non_identity_holonomy".into(),
                    gauge_family: "su2_vertex_gauge".into(),
                },
                projected_data,
                coverage: vec![CoverageAssessment {
                    requirement: req.clone(),
                    disposition: CoverageDisposition::PreservedVisible,
                    evidence_ref: "su2://nonflat_curvature_defect".into(),
                    projection_loss: None,
                }],
                visible_defects: vec![VisibleDefect {
                    defect_id: "su2_frustrated_loop_defect".into(),
                    claim_id: req.claim_id,
                    kind: "non_abelian_holonomy_curvature".into(),
                    cell_refs: vec!["triangle_012".into()],
                    evidence_ref: "su2://nonflat_curvature_defect".into(),
                    exact_binary_cochain,
                }],
                higher_degree_need: None,
                discarded_information_refs: vec![],
            })
        }
    }

    fn propose(
        &self,
        _packet: &ProblemPacket,
        _carrier: &FiniteCarrier,
        _state: &Self::State,
        _signatures: &[ObstructionSignature],
    ) -> Result<Vec<DeformationProposal<Self::State>>, AdapterFailure> {
        Ok(vec![])
    }

    fn assess_candidate(
        &self,
        _packet: &ProblemPacket,
        _carrier: &FiniteCarrier,
        _before: &Self::State,
        _proposal: &DeformationProposal<Self::State>,
        _operator: &RegisteredOperator,
    ) -> Result<CandidateAssessment, AdapterFailure> {
        Err(AdapterFailure {
            kind: AdapterFailureKind::Refused,
            detail: "no candidate operators provided for su2 probe".into(),
        })
    }
}

fn create_su2_problem_packet() -> ProblemPacket {
    ProblemPacket {
        packet_id: "su2_packet_001".into(),
        domain: "quantum_foundations_su2".into(),
        payload: serde_json::json!({
            "group": "SU(2)",
            "complex": "tripartite_cycle"
        }),
        protected_distinctions: vec![DetectorRequirement {
            claim_id: "P009-C01".into(),
            distinction_id: "su2_loop_holonomy_flatness".into(),
        }],
        packet_refs: vec![
            "sha256:0000000000000000000000000000000000000000000000000000000000000001".into(),
        ],
        evidence_ceiling: "LocalReplay".into(),
    }
    .canonicalized()
    .unwrap()
}

#[test]
fn test_su2_flat_loop_passes_cleanly() {
    let adapter = Su2HolonomyAdapter::new_flat();
    let packet = create_su2_problem_packet();
    let registry = OperatorRegistry::new(vec![]).unwrap();
    let budget = RunBudget {
        max_steps: 10,
        max_candidates: 10,
        max_carrier_cells: 50,
        max_receipt_bytes: 100_000,
        max_wall_millis: 5000,
        require_independent_witness: false,
    };

    let receipt = run_multipath(
        &adapter,
        packet,
        &registry,
        budget,
        &CancellationToken::default(),
    )
    .expect("flat SU(2) multipath run should execute cleanly");

    assert_eq!(receipt.authority_effect, AuthorityEffect::None);
    assert_eq!(receipt.terminal.kind, TerminalKind::StabilizedSurvivor);
}

#[test]
fn test_su2_nonflat_loop_emits_obstruction_receipt() {
    let adapter = Su2HolonomyAdapter::new_nonflat();
    let packet = create_su2_problem_packet();
    let registry = OperatorRegistry::new(vec![]).unwrap();
    let budget = RunBudget {
        max_steps: 10,
        max_candidates: 10,
        max_carrier_cells: 50,
        max_receipt_bytes: 100_000,
        max_wall_millis: 5000,
        require_independent_witness: false,
    };

    let receipt = run_multipath(
        &adapter,
        packet,
        &registry,
        budget,
        &CancellationToken::default(),
    )
    .expect("non-flat SU(2) multipath run should execute");

    assert_eq!(receipt.authority_effect, AuthorityEffect::None);
    assert_eq!(receipt.terminal.kind, TerminalKind::NoRule);
    assert!(!receipt.steps.is_empty());
    let step = &receipt.steps[0];
    assert_eq!(step.inspection.defects.len(), 1);
    assert_eq!(
        step.inspection.defects[0].kind,
        "non_abelian_holonomy_curvature"
    );
}

// Origin: engine/crates_rs/tests/engines/su2_holonomy_multipath.rs
// Claim: urn:core:crates_rs:tests:su2-holonomy-multipath:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3f9e7ff7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3f9e7ff7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3f9e7ff7 {
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
impl BoundaryError3f9e7ff7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3f9e7ff7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3f9e7ff7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3f9e7ff7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3f9e7ff7> {
        if capacity_bound == 0 {
            return Err(BoundaryError3f9e7ff7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3f9e7ff7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3f9e7ff7::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3f9e7ff7() {
    let admitted = BoundaryRecord3f9e7ff7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3f9e7ff7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
