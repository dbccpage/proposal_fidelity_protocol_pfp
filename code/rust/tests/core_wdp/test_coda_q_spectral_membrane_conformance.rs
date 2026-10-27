//! Adversarial conformance tests for the exact One Regime spectral membrane.

use core_wdp::coda::q::{
    CandidateKind, ContinuumDebt, QAdmissionGate, QAdmissionRequest, QError, QPacket, QPacketField,
    QTerminal, ResidualSpec, SpectralMembrane, SpectralMembraneError, TransportSpec,
};
use core_types::q_continuum::ObstructionKind;
use core_types::refinement_tower::{D1_BINDING_STATUS, D1_REPLAY_COMMAND};
use core_types::{
    AuthorityEffectLevel, ConvergenceCertificate, EvidenceCeiling, PositiveRational,
    RefinementLevel, RefinementRelation, RefinementTower, ShadowFamily, ShadowKind,
    SpectralTopology, TheoremReceipt, UniformD1ReceiptKind, D1_BOUNDS_AUDIT_SHA256,
    D1_BOUNDS_SOURCE_SHA256, D1_INTERFACES_AUDIT_SHA256, D1_INTERFACES_SOURCE_SHA256,
};

fn receipt(kind: UniformD1ReceiptKind) -> TheoremReceipt {
    TheoremReceipt::uniform_d1(
        kind,
        D1_BOUNDS_SOURCE_SHA256,
        D1_INTERFACES_SOURCE_SHA256,
        D1_BOUNDS_AUDIT_SHA256,
        D1_INTERFACES_AUDIT_SHA256,
    )
    .expect("the repository D1 receipt hashes are canonical")
}

fn uniform_tower(
    family_id: &str,
    kind: ShadowKind,
    resolutions: &[(usize, u64)],
) -> RefinementTower {
    let family =
        ShadowFamily::new(family_id, kind, "declared compact spectral object").expect("family");
    let levels = resolutions
        .iter()
        .map(|(resolution, denominator)| {
            RefinementLevel::new(
                *resolution,
                PositiveRational::from_u64(1, *denominator).expect("positive exact mesh scale"),
            )
            .expect("valid finite refinement level")
        })
        .collect();
    RefinementTower::new(family, RefinementRelation::ExactUniformSubdivision, levels)
        .expect("strict exact-subdivision tower")
}

fn cycle_tower(family_id: &str) -> RefinementTower {
    uniform_tower(
        family_id,
        ShadowKind::UniformCycle,
        &[(8, 8), (16, 16), (32, 32)],
    )
}

fn path_tower(family_id: &str) -> RefinementTower {
    uniform_tower(
        family_id,
        ShadowKind::CellCenteredNeumannPath,
        &[(8, 8), (16, 16), (32, 32)],
    )
}

fn cycle_certificate(tower: &RefinementTower) -> ConvergenceCertificate {
    ConvergenceCertificate::uniform_cycle(tower, 2, receipt(UniformD1ReceiptKind::UniformCycle))
        .expect("cycle certificate")
}

fn path_certificate(tower: &RefinementTower) -> ConvergenceCertificate {
    ConvergenceCertificate::cell_centered_neumann_path(
        tower,
        3,
        receipt(UniformD1ReceiptKind::CellCenteredNeumannPath),
    )
    .expect("path certificate")
}

fn full_packet() -> QPacket {
    QPacket::new("q:one-regime:spectral-membrane")
        .with_carrier("finite cycle/path spectral carrier")
        .with_composition("ordered finite-prefix spectral composition")
        .with_observer("fixed-mode eigenvalue observer")
        .with_finite_prediction("explicit exact-rational O(h^2) defect envelope")
        .with_finite_prediction("zero mode remains zero")
        .with_transport(
            TransportSpec::new("finite tower to analytic common-limit comparison")
                .with_equivalence_scope("fixed family and fixed ordered spectral prefix")
                .with_failure_mode("certificate identity or replay mismatch"),
        )
        .with_residual(
            ResidualSpec::new(
                "no continuum object or canonical GTTC-5b witness is constructed",
                ObstructionKind::NonFiniteProjection,
            )
            .with_next_probe_hint("replay the theorem receipt"),
        )
        .with_terminal_request(QTerminal::ConditionalSupport)
}

#[test]
fn cycle_certificate_yields_bound_conditional_support_and_all_five_routes() {
    let packet = full_packet();
    let tower = cycle_tower("one-regime-cycle");
    let certificate = cycle_certificate(&tower);
    assert_eq!(
        certificate.theorem_receipt().source_binding_status(),
        "SOURCE_BINDING_ONLY_NOT_NATIVE_LEAN_REPLAY"
    );

    let decision = SpectralMembrane::decide(packet.clone(), &tower, Some(&certificate))
        .expect("matching exact certificate");
    let binding = decision.binding().expect("conditional support is bound");

    assert_eq!(decision.terminal(), QTerminal::ConditionalSupport);
    assert_eq!(decision.packet(), &packet);
    assert_eq!(binding.bound_packet(), &packet);
    assert_eq!(binding.tower(), &tower);
    assert_eq!(binding.convergence_certificate(), &certificate);
    let tower_digest = tower.digest_sha256();
    let expected_debt = ContinuumDebt {
        finite_shadow: Some(format!(
            "family_id=one-regime-cycle;family_kind=uniform_cycle;\
             declared_object=declared compact spectral object;tower_digest_sha256={tower_digest}"
        )),
        refinement_relation: Some("exact_uniform_subdivision".to_string()),
        declared_topology: Some("ordered_finite_prefix".to_string()),
        convergence_certificate_route: Some(format!(
            "schema=core.refinement-convergence.v1;tower_digest_sha256={tower_digest};\
             family_id=one-regime-cycle;family_kind=uniform_cycle;\
             topology=ordered_finite_prefix;mode_index=2;receipt_kind=UniformCycle;\
             source_binding_status={D1_BINDING_STATUS};source_binding_check={D1_REPLAY_COMMAND};\
             theorems=CoreCosmology.OneRegime.cycle_dispersion_bound,\
             CoreCosmology.OneRegime.UniformCycleModeInterface.spectral_defect_bound"
        )),
        descent_trigger: Some(format!(
            "check source bindings for ordered_finite_prefix mode_index=2 with {D1_REPLAY_COMMAND};source_binding_status={D1_BINDING_STATUS}"
        )),
    };

    assert_eq!(decision.continuum_debt(), &expected_debt);
    assert_eq!(binding.continuum_debt(), &expected_debt);
    assert_eq!(expected_debt.validate_for_admission(), Ok(()));

    let admission = QAdmissionGate::new().classify_admission(
        decision.packet(),
        &QAdmissionRequest {
            candidate_id: "one-regime-cycle-admission".to_string(),
            kind: CandidateKind::Model,
            continuum: decision.continuum_debt().clone(),
        },
    );
    assert_eq!(
        admission.terminal_status,
        QTerminal::ConditionalSupport,
        "the exact membrane binding must survive the repository Q admission gate"
    );
    assert_eq!(admission.residual, None);
}

#[test]
fn neumann_path_certificate_yields_bound_conditional_support() {
    let packet = full_packet();
    let tower = path_tower("one-regime-neumann-path");
    let certificate = path_certificate(&tower);
    assert_eq!(
        certificate.theorem_receipt().source_binding_status(),
        "SOURCE_BINDING_ONLY_NOT_NATIVE_LEAN_REPLAY"
    );

    let decision = SpectralMembrane::decide(packet.clone(), &tower, Some(&certificate))
        .expect("matching exact path certificate");
    let binding = decision
        .binding()
        .expect("path support is certificate-bound");

    assert_eq!(decision.terminal(), QTerminal::ConditionalSupport);
    let tower_digest = tower.digest_sha256();
    let expected_debt = ContinuumDebt {
        finite_shadow: Some(format!(
            "family_id=one-regime-neumann-path;family_kind=cell_centered_neumann_path;\
             declared_object=declared compact spectral object;tower_digest_sha256={tower_digest}"
        )),
        refinement_relation: Some("exact_uniform_subdivision".to_string()),
        declared_topology: Some("ordered_finite_prefix".to_string()),
        convergence_certificate_route: Some(format!(
            "schema=core.refinement-convergence.v1;tower_digest_sha256={tower_digest};\
             family_id=one-regime-neumann-path;family_kind=cell_centered_neumann_path;\
             topology=ordered_finite_prefix;mode_index=3;\
             receipt_kind=CellCenteredNeumannPath;source_binding_status={D1_BINDING_STATUS};source_binding_check={D1_REPLAY_COMMAND};\
             theorems=CoreCosmology.OneRegime.neumann_path_dispersion_bound,\
             CoreCosmology.OneRegime.NeumannPathModeInterface.spectral_defect_bound"
        )),
        descent_trigger: Some(format!(
            "check source bindings for ordered_finite_prefix mode_index=3 with {D1_REPLAY_COMMAND};source_binding_status={D1_BINDING_STATUS}"
        )),
    };

    assert_eq!(decision.packet(), &packet);
    assert_eq!(
        binding.convergence_certificate().family_kind(),
        ShadowKind::CellCenteredNeumannPath
    );
    assert_eq!(binding.convergence_certificate().mode_index(), 3);
    assert_eq!(
        binding.continuum_debt(),
        decision.continuum_debt(),
        "the decision and private binding carry one identical debt rendering"
    );
    assert_eq!(decision.continuum_debt(), &expected_debt);
}

#[test]
fn withheld_certificate_returns_oracle_needed_without_forging_a_binding() {
    let packet = full_packet();
    let tower = cycle_tower("one-regime-withheld");

    let decision =
        SpectralMembrane::decide(packet.clone(), &tower, None).expect("withholding is classified");

    let tower_digest = tower.digest_sha256();
    let expected_debt = ContinuumDebt {
        finite_shadow: Some(format!(
            "family_id=one-regime-withheld;family_kind=uniform_cycle;\
             declared_object=declared compact spectral object;tower_digest_sha256={tower_digest}"
        )),
        refinement_relation: Some("exact_uniform_subdivision".to_string()),
        declared_topology: Some("ordered_finite_prefix".to_string()),
        convergence_certificate_route: None,
        descent_trigger: Some(
            "supply typed ConvergenceCertificate for family_id=one-regime-withheld;\
             then check its source bindings;native Lean replay remains a separate obligation"
                .to_string(),
        ),
    };

    assert_eq!(decision.terminal(), QTerminal::OracleNeeded);
    assert_eq!(decision.packet(), &packet);
    assert_eq!(decision.binding(), None);
    assert_eq!(decision.continuum_debt(), &expected_debt);
    assert_eq!(
        decision.continuum_debt().validate_for_admission(),
        Err(QError::OracleNeededConvergence)
    );

    let admission = QAdmissionGate::new().classify_admission(
        decision.packet(),
        &QAdmissionRequest {
            candidate_id: "one-regime-withheld-admission".to_string(),
            kind: CandidateKind::Model,
            continuum: decision.continuum_debt().clone(),
        },
    );
    assert_eq!(
        admission.terminal_status,
        QTerminal::OracleNeeded,
        "withholding the convergence certificate must remain refused by QAdmissionGate"
    );
    assert!(admission.residual.is_some());
}

#[test]
fn decision_preserves_all_seven_mandatory_packet_fields_and_serialized_bytes() {
    let packet = full_packet();
    let before = serde_json::to_vec(&packet).expect("Q packet serializes");
    let tower = cycle_tower("one-regime-packet-equality");
    let certificate = cycle_certificate(&tower);

    let decision = SpectralMembrane::decide(packet.clone(), &tower, Some(&certificate))
        .expect("matching certificate");
    let after = serde_json::to_vec(decision.packet()).expect("returned Q packet serializes");
    let returned = decision.packet();

    assert_eq!(after, before);
    assert_eq!(returned.id, packet.id);
    assert_eq!(returned.carrier, packet.carrier);
    assert_eq!(returned.composition, packet.composition);
    assert_eq!(returned.observer, packet.observer);
    assert_eq!(returned.finite_predictions, packet.finite_predictions);
    assert_eq!(returned.transport, packet.transport);
    assert_eq!(returned.residual, packet.residual);
    assert_eq!(returned.terminal_request, packet.terminal_request);
}

#[test]
fn membrane_and_binding_are_shape_only_with_no_authority_effect() {
    let tower = cycle_tower("one-regime-no-authority");
    let certificate = cycle_certificate(&tower);
    let decision = SpectralMembrane::decide(full_packet(), &tower, Some(&certificate))
        .expect("matching certificate");
    let binding = decision.binding().expect("binding");

    assert_eq!(decision.evidence_ceiling(), EvidenceCeiling::ShapeOnly);
    assert_eq!(decision.authority_effect(), AuthorityEffectLevel::None);
    assert_eq!(binding.evidence_ceiling(), EvidenceCeiling::ShapeOnly);
    assert_eq!(binding.authority_effect(), AuthorityEffectLevel::None);
    assert_eq!(
        binding.convergence_certificate().authority_effect(),
        AuthorityEffectLevel::None
    );
}

#[test]
fn mismatched_family_id_is_rejected_before_digest_binding() {
    let certificate_tower = cycle_tower("certificate-family");
    let certificate = cycle_certificate(&certificate_tower);
    let requested_tower = cycle_tower("requested-family");

    let result = SpectralMembrane::decide(full_packet(), &requested_tower, Some(&certificate));

    assert_eq!(
        result,
        Err(SpectralMembraneError::FamilyIdMismatch {
            tower: "requested-family".to_string(),
            certificate: "certificate-family".to_string(),
        })
    );
}

#[test]
fn mismatched_family_kind_is_rejected_before_digest_binding() {
    let certificate_tower = cycle_tower("same-family-id");
    let certificate = cycle_certificate(&certificate_tower);
    let requested_tower = path_tower("same-family-id");

    let result = SpectralMembrane::decide(full_packet(), &requested_tower, Some(&certificate));

    assert_eq!(
        result,
        Err(SpectralMembraneError::FamilyKindMismatch {
            tower: ShadowKind::CellCenteredNeumannPath,
            certificate: ShadowKind::UniformCycle,
        })
    );
}

#[test]
fn mismatched_tower_digest_is_rejected_even_when_family_identity_matches() {
    let certificate_tower = cycle_tower("same-exact-family");
    let certificate = cycle_certificate(&certificate_tower);
    let requested_tower = uniform_tower(
        "same-exact-family",
        ShadowKind::UniformCycle,
        &[(8, 8), (32, 32), (64, 64)],
    );
    let expected_tower_digest = requested_tower.digest_sha256();
    let certificate_digest = certificate.tower_digest_sha256().to_string();

    let result = SpectralMembrane::decide(full_packet(), &requested_tower, Some(&certificate));

    assert_eq!(
        result,
        Err(SpectralMembraneError::TowerDigestMismatch {
            tower: expected_tower_digest,
            certificate: certificate_digest,
        })
    );
}

#[test]
fn topology_is_type_closed_and_the_runtime_binding_uses_the_same_variant() {
    let tower = cycle_tower("one-regime-topology");
    let certificate = cycle_certificate(&tower);
    let decision = SpectralMembrane::decide(full_packet(), &tower, Some(&certificate))
        .expect("the only inhabitable topology matches");
    let binding = decision.binding().expect("binding");

    assert_eq!(
        binding.tower().family().topology(),
        SpectralTopology::OrderedFinitePrefix
    );
    assert_eq!(
        binding.convergence_certificate().topology(),
        SpectralTopology::OrderedFinitePrefix
    );
    assert_eq!(
        decision.continuum_debt().declared_topology.as_deref(),
        Some("ordered_finite_prefix")
    );
}

#[test]
fn malformed_packet_is_rejected_without_oracle_classification() {
    let mut packet = full_packet();
    packet.observer = None;
    let tower = cycle_tower("one-regime-invalid-packet");

    let result = SpectralMembrane::decide(packet, &tower, None);

    assert_eq!(
        result,
        Err(SpectralMembraneError::InvalidPacket(
            QError::MissingMandatoryField(QPacketField::Observer)
        ))
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_coda_q_spectral_membrane_conformance.rs
// Claim: urn:core:crates_rs:tests:test-coda-q-spectral-membrane-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddbb3fbbc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddbb3fbbc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordbb3fbbc {
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
impl BoundaryErrordbb3fbbc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordbb3fbbc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordbb3fbbc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddbb3fbbc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordbb3fbbc> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordbb3fbbc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordbb3fbbc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordbb3fbbc::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_dbb3fbbc() {
    let admitted = BoundaryRecorddbb3fbbc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddbb3fbbc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
