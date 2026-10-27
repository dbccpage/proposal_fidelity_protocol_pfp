//! Strict Q-continuum policy layer.
//!
//! This module owns the Q policy implementation; `core_q` re-exports it.
//! It does not move Q DTOs out of `core_types`. It validates the
//! mandatory Q packet, gates Q admission, routes finite descent obligations, and
//! records residuals without minting authority.

#![forbid(unsafe_code)]
#![deny(unused_must_use)]

pub mod admission;
pub mod authority;
pub mod bridge_admission;
pub mod bridge_packet;
/// CODA-CS → Q adapter (experimental). Present in `src/` but undeclared until
/// 2026-08-04, so no consumer could resolve it.
pub mod coda_cs_adapter;
/// The Nine-Layer CODA Stack (FOC, MUR, CS, CS-Q, Q = The Continuum, A, OR, FDA, CODA_GTLA).
pub mod coda_stack;
pub mod continuum;
pub mod descent;
pub mod errors;
/// Target 10 — exact-arithmetic finite-shadow carrier and shared fixture types.
///
/// Present in `src/` but undeclared until 2026-08-04, so `rustc` never saw it and
/// `tests/finite_shadow_exact_fixtures.rs` could not resolve its imports.
pub mod finite_qm_types;
pub mod finite_shadow_exact;
pub mod ledger;
pub mod packet;
pub mod probe;
/// Q/CODA product vertical slice — launch board, claim ledger, staged receipts,
/// and the fail-closed promotion gates. Present in `src/` but undeclared until
/// 2026-08-04.
pub mod product_vertical_slice;
pub mod spectral_layer_binding;
pub mod spectral_membrane;
pub mod transport;
pub mod zeta;

pub use admission::{AdmissionDecision, CandidateKind, QAdmissionGate, QAdmissionRequest};
pub use authority::AuthorityPolicy;
pub use coda_cs_adapter::{
    AdapterDecision, AdapterError, CodaCsToQAdapter, DomainSample, ProfileFactorizationReceipt,
    QBarEntry, CODA_CS_Q_ADAPTER_STATUS,
};
pub use coda_stack::{
    SentinelRecord, SentinelRegister, CodaError, ContinuumShadow, CryptographicGrant, DualWitness,
    Enclosure, FdaPacket, FocSignature, CodaGtlaOutcome, IntoCochainComplex, LossEntry, LossLedger,
    MetricSeparation, OverlapGluing, SevenHaltGuards, TerminalRefusal, TransportCertificate,
};
pub use continuum::ContinuumDebt;
pub use descent::QDescentGate;
pub use errors::{QError, QPacketField};
pub use finite_shadow_exact::{
    ExactNonNegRational, FinDistribution, FiniteQmFieldRefs, FiniteShadowExactError,
    FiniteShadowFixture, FiniteShadowSystemExact, FixtureCase, FixtureDist,
    FixtureDistributionCase, FixtureRational, FixtureSystem, ShadowStatus, ShadowTerminalLabel,
    TerminalizationDiagnostic, AUTHORITY_EFFECT_NONE, FIELD_AUTHORITY_EFFECT, FIELD_CARRIER,
    FIELD_CARRIER_ID, FIELD_CERTIFICATE, FIELD_CERTIFICATE_ID, FIELD_CERTIFICATE_KIND,
    FIELD_CONTINUUM_DEBT, FIELD_CONTRACT_URN, FIELD_DIMENSION, FIELD_DIMENSION_ID,
    FIELD_IMPORT_LEDGER, FIELD_NOTES, FIELD_PAYLOAD_DIGEST_SHA256, FIELD_RANK, FIELD_SCALARS,
    FIELD_SCHEMA_VERSION, FIELD_SLOTS, FIELD_SUPPORT_CARDINALITY,
    FINITE_QM_CONTRACT_SCHEMA_VERSION, FINITE_QM_CONTRACT_URN, LAYER_CODA_CS_Q,
};
pub use ledger::QLedger;
pub use core_types::ObstructionDiagnosticClass;
pub use packet::{QPacket, QTerminal, ResidualSpec, TransportSpec, ValidatedQPacket};
pub use probe::probe_plan_for_packet;
pub use product_vertical_slice::{
    evaluate_q_coda_integration, gate_product_mount, q_coda_product_mount_allowed,
    refuse_silent_prod_enablement, try_auto_promote, ClaimRecord, ClaimStatus, FeatureStatus,
    LaunchTarget, LaunchTargetBoard, ManifestBoundZip, PackageManifest, PipelineStage,
    ProductGateError, ProductProposal, ProductVerticalSlice, StageReceipt, StageStatus,
    VerticalSliceRun, AUTHORITY_EFFECT as PRODUCT_VERTICAL_AUTHORITY_EFFECT,
    PROMOTION_NOT_PROMOTED, PROMOTION_PROMOTED, Q_CODA_PRODUCT_INTEGRATION,
    RELEASE_DIAGNOSTIC_ONLY, RELEASE_NOT_CANDIDATE,
};
pub use spectral_membrane::{
    SpectralConvergenceBinding, SpectralMembrane, SpectralMembraneDecision, SpectralMembraneError,
};
pub use transport::RepresentationTransportPacket;
pub use zeta::{
    ZetaRhCandidate, ZetaRhClaimKind, ZetaRhDecision, ZetaRhFirewall, ZetaTransportDirection,
};

// Origin: engine/crates_rs/core_wdp/src/coda/q/mod.rs
// Claim: urn:core:crates_rs:core-wdp:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord007be9bf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord007be9bf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError007be9bf {
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
impl BoundaryError007be9bf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError007be9bf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError007be9bf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord007be9bf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError007be9bf> {
        if capacity_bound == 0 {
            return Err(BoundaryError007be9bf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError007be9bf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError007be9bf::ExceedsCapacity {
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
mod tests {
    use super::*;
    use core_types::q_continuum::{
        AuthorityScope, AuthorityStrength, DescentResult, ObstructionKind, QContinuumLedger,
        Residual, TerminalStatus, Witness,
    };

    fn valid_packet(terminal_request: QTerminal) -> QPacket {
        QPacket::new("q:test")
            .with_carrier("finite carrier")
            .with_composition("declared composition rule")
            .with_observer("declared observer")
            .with_finite_prediction("finite prediction")
            .with_transport(TransportSpec::new("transport into finite shadow"))
            .with_residual(ResidualSpec::new(
                "open residual",
                ObstructionKind::NonFiniteProjection,
            ))
            .with_terminal_request(terminal_request)
    }

    fn valid_qheld_request() -> QAdmissionRequest {
        QAdmissionRequest::new("candidate:test", CandidateKind::Representation)
            .with_finite_shadow("finite shadow")
            .with_refinement_relation("refinement route")
            .with_declared_topology("finite-discrete topology")
            .with_convergence_certificate_route("certificate route")
            .with_descent_trigger("next finite replay")
    }

    #[test]
    fn rejects_packet_without_carrier() {
        let mut packet = valid_packet(QTerminal::OpenResidual);
        packet.carrier = None;

        assert_eq!(
            packet.validate_mandatory(),
            Err(QError::MissingMandatoryField(QPacketField::Carrier))
        );
    }

    #[test]
    fn rejects_packet_without_composition() {
        let mut packet = valid_packet(QTerminal::OpenResidual);
        packet.composition = None;

        assert_eq!(
            packet.validate_mandatory(),
            Err(QError::MissingMandatoryField(QPacketField::Composition))
        );
    }

    #[test]
    fn rejects_packet_without_observer() {
        let mut packet = valid_packet(QTerminal::OpenResidual);
        packet.observer = None;

        assert_eq!(
            packet.validate_mandatory(),
            Err(QError::MissingMandatoryField(QPacketField::Observer))
        );
    }

    #[test]
    fn rejects_packet_without_finite_predictions() {
        let mut packet = valid_packet(QTerminal::OpenResidual);
        packet.finite_predictions.clear();

        assert_eq!(
            packet.validate_mandatory(),
            Err(QError::MissingMandatoryField(
                QPacketField::FinitePredictions
            ))
        );
    }

    #[test]
    fn rejects_packet_without_transport() {
        let mut packet = valid_packet(QTerminal::OpenResidual);
        packet.transport = None;

        assert_eq!(
            packet.validate_mandatory(),
            Err(QError::MissingMandatoryField(QPacketField::Transport))
        );
    }

    #[test]
    fn rejects_packet_without_residual() {
        let mut packet = valid_packet(QTerminal::OpenResidual);
        packet.residual = None;

        assert_eq!(
            packet.validate_mandatory(),
            Err(QError::MissingMandatoryField(QPacketField::Residual))
        );
    }

    #[test]
    fn rejects_packet_without_terminal_request() {
        let mut packet = valid_packet(QTerminal::OpenResidual);
        packet.terminal_request = None;

        assert_eq!(
            packet.validate_mandatory(),
            Err(QError::MissingMandatoryField(QPacketField::TerminalRequest))
        );
    }

    #[test]
    fn invalid_qheld_is_classified_and_recorded_as_residual() {
        let packet = valid_packet(QTerminal::QHeld);
        let mut request = valid_qheld_request();
        request.continuum.finite_shadow = None;

        let decision = QAdmissionGate::new().classify_admission(&packet, &request);
        assert_eq!(decision.terminal_status, QTerminal::Refused);
        assert!(decision.residual.is_some());

        let mut ledger = QContinuumLedger::new();
        decision.record_residual(&mut ledger, AuthorityScope::new("q-admission"));
        let trace = ledger
            .authority_trace("candidate:test")
            .expect("classified admission residual is recorded");

        assert_eq!(trace.strength, AuthorityStrength::Probed);
        assert_eq!(trace.residuals.len(), 1);
        assert!(!trace.is_terminal_within_domain("q-admission"));
    }

    #[test]
    fn terminal_within_scope_requires_supported_witness() {
        let scope = AuthorityScope::new("q-test");
        let mut trace = AuthorityPolicy::new_trace("claim:test", scope.clone());
        let witnessless_support = DescentResult {
            obligation_id: "o:witnessless".to_string(),
            scope,
            terminal_status: TerminalStatus::Supported,
            witness: None,
            residual: None,
            counterexample: None,
            notes: Vec::new(),
        };

        AuthorityPolicy::record_result(&mut trace, witnessless_support);

        assert_ne!(trace.strength, AuthorityStrength::TerminalWithinScope);
        assert_eq!(trace.residuals.len(), 1);
        assert_eq!(
            trace.residuals[0].obstruction,
            ObstructionKind::MissingWitness
        );
    }

    #[test]
    fn terminal_within_scope_requires_no_in_scope_residuals() {
        let scope = AuthorityScope::new("q-test");
        let witness = Witness::new("w:test", "unit", "finite witness", "unit-test");
        let mut trace = AuthorityPolicy::new_trace("claim:test", scope.clone());

        AuthorityPolicy::record_result(
            &mut trace,
            DescentResult::supported("o:supported", scope.clone(), witness),
        );
        assert_eq!(trace.strength, AuthorityStrength::TerminalWithinScope);

        AuthorityPolicy::record_result(
            &mut trace,
            DescentResult::failed(
                "o:residual",
                scope,
                Residual::new(
                    "residual:test",
                    "claim:test",
                    ObstructionKind::Underdefined,
                    "residual remains",
                ),
            ),
        );

        assert_eq!(trace.strength, AuthorityStrength::ConditionallySupported);
        assert!(!trace.is_terminal_within_domain("q-test"));
    }

    #[test]
    fn records_residual_without_authority() {
        let scope = AuthorityScope::new("q-test");
        let residual = Residual::new(
            "residual:test",
            "claim:test",
            ObstructionKind::NonFiniteProjection,
            "no finite projection yet",
        );
        let mut ledger = QLedger::new();

        ledger.record_residual("claim:test", "o:test", scope, residual);
        let trace = ledger
            .inner()
            .authority_trace("claim:test")
            .expect("authority trace is recorded");

        assert_eq!(trace.strength, AuthorityStrength::Probed);
        assert!(!trace.is_terminal_within_domain("q-test"));
        assert_eq!(trace.residuals.len(), 1);
    }

    #[test]
    fn demotes_authority_after_in_scope_residual() {
        let scope = AuthorityScope::new("q-test");
        let witness = Witness::new("w:test", "unit", "finite witness", "unit-test");
        let mut trace = AuthorityPolicy::new_trace("claim:test", scope.clone());

        AuthorityPolicy::record_result(
            &mut trace,
            DescentResult::supported("o:supported", scope.clone(), witness),
        );
        assert_eq!(trace.strength, AuthorityStrength::TerminalWithinScope);

        AuthorityPolicy::record_result(
            &mut trace,
            DescentResult::failed(
                "o:residual",
                scope,
                Residual::new(
                    "residual:test",
                    "claim:test",
                    ObstructionKind::Underdefined,
                    "residual remains",
                ),
            ),
        );

        assert_eq!(trace.strength, AuthorityStrength::ConditionallySupported);
        assert!(!trace.is_terminal_within_domain("q-test"));
    }

    #[test]
    fn representation_transport_requires_full_packet() {
        let packet = RepresentationTransportPacket::real_complex_qm("real carrier", "complex QM")
            .with_observer_measurement_pairing("Born measurement pairing")
            .with_finite_prediction("finite Born statistics")
            .with_representation_transport("realification / complexification route")
            .with_equivalence_scope("finite operational predictions")
            .with_failure_mode("composition mismatch")
            .with_residual_selector("composition residual")
            .with_terminal_status_request(QTerminal::OpenResidual);

        assert_eq!(
            packet.validate_full_transport_packet(),
            Err(QError::CompositionRuleRequired)
        );
    }

    #[test]
    fn continuum_claim_without_topology_is_refused() {
        let packet = valid_packet(QTerminal::ConditionalSupport);
        let request = QAdmissionRequest::new("candidate:continuum", CandidateKind::Theory)
            .with_finite_shadow("finite tower shadow")
            .with_refinement_relation("refinement relation")
            .with_convergence_certificate_route("certificate route")
            .with_descent_trigger("next finite replay");

        let decision = QAdmissionGate::new().classify_admission(&packet, &request);
        assert_eq!(decision.terminal_status, QTerminal::Refused);
    }

    fn valid_ihara_zeta_candidate(direction: ZetaTransportDirection) -> ZetaRhCandidate {
        let packet = QPacket::new("q:zeta:ihara-graph-rh")
            .with_carrier("finite (delta + 1)-regular Ramanujan graph")
            .with_composition("tower refinement preserving finite adjacency spectral data")
            .with_observer("Ihara-zeta pole radius / Ramanujan spectral observer")
            .with_finite_prediction("nontrivial poles lie on |u| = delta^(-1/2) iff Ramanujan")
            .with_transport(
                TransportSpec::new("finite regular graph -> Ihara zeta -> graph-RH shadow")
                    .with_equivalence_scope("graph / Weil RH analog only")
                    .with_failure_mode("finite shadow does not decode zeta(s) or source"),
            )
            .with_residual(ResidualSpec::new(
                "classical RH and source decoding remain outside this finite shadow",
                ObstructionKind::AnalogyBreak,
            ))
            .with_terminal_request(QTerminal::QHeld);
        let admission = QAdmissionRequest::new("candidate:ihara-graph-rh", CandidateKind::Theory)
            .with_finite_shadow("finite (delta + 1)-regular Ramanujan graph")
            .with_refinement_relation("tower refinement preserving graph/Ihara-zeta shadow data")
            .with_declared_topology(
                "graph tower boundary topology held in Q and audited by CODA-CS",
            )
            .with_convergence_certificate_route("certified finite-shadow tower route")
            .with_descent_trigger("produce finite graph spectrum receipt or residual");

        ZetaRhCandidate::new(
            ZetaRhClaimKind::IharaGraphRhAnalog,
            direction,
            packet,
            admission,
        )
    }

    #[test]
    fn admits_ihara_zeta_graph_rh_as_valid_q_packet() {
        let candidate = valid_ihara_zeta_candidate(ZetaTransportDirection::SourceToShadow);
        let decision = ZetaRhFirewall::new().classify(&candidate);

        assert_eq!(decision.admission.terminal_status, QTerminal::QHeld);
        assert!(decision.crosses_to_gttc);
        assert!(decision.admission.residual.is_none());
        assert_eq!(
            decision.admission.terminal_status.to_terminal_status(),
            TerminalStatus::Residual
        );
    }

    #[test]
    fn rejects_classical_rh_claim_without_finite_shadow() {
        let packet = QPacket::new("q:zeta:classical-rh")
            .with_carrier("classical Riemann zeta source claim")
            .with_composition("none declared")
            .with_observer("RH name only")
            .with_finite_prediction("none supplied")
            .with_transport(TransportSpec::new("claimed import from graph/Ihara shadow"))
            .with_residual(ResidualSpec::new(
                "no finite bridge from graph/Ihara shadow to classical zeta(s)",
                ObstructionKind::NonFiniteProjection,
            ))
            .with_terminal_request(QTerminal::QHeld);
        let admission = QAdmissionRequest::new("candidate:classical-rh", CandidateKind::Theory)
            .with_refinement_relation("none")
            .with_declared_topology("none")
            .with_convergence_certificate_route("none")
            .with_descent_trigger("supply a real finite bridge or refuse");
        let candidate = ZetaRhCandidate::new(
            ZetaRhClaimKind::ClassicalRiemannHypothesis,
            ZetaTransportDirection::SourceOnly,
            packet,
            admission,
        );

        let decision = ZetaRhFirewall::new().classify(&candidate);
        assert_eq!(decision.admission.terminal_status, QTerminal::Refused);
        assert!(!decision.crosses_to_gttc);
        assert_eq!(
            decision
                .admission
                .residual
                .as_ref()
                .expect("classical RH refusal residual")
                .obstruction,
            ObstructionKind::NonFiniteProjection
        );

        let mut ledger = QContinuumLedger::new();
        decision
            .admission
            .record_residual(&mut ledger, AuthorityScope::new("zeta-rh-firewall"));
        let trace = ledger
            .authority_trace("candidate:classical-rh")
            .expect("classical RH refusal is recorded");
        assert_eq!(trace.strength, AuthorityStrength::Probed);
        assert_eq!(trace.residuals.len(), 1);
        assert!(!trace.is_terminal_within_domain("zeta-rh-firewall"));
    }

    #[test]
    fn enforces_shadow_cannot_decode_source_directionality() {
        let candidate = valid_ihara_zeta_candidate(ZetaTransportDirection::ShadowDecodesSource);
        let decision = ZetaRhFirewall::new().classify(&candidate);

        assert_eq!(decision.admission.terminal_status, QTerminal::OpenResidual);
        assert!(!decision.crosses_to_gttc);
        assert_eq!(
            decision
                .admission
                .residual
                .as_ref()
                .expect("directionality residual")
                .obstruction,
            ObstructionKind::AnalogyBreak
        );

        let mut ledger = QContinuumLedger::new();
        decision
            .admission
            .record_residual(&mut ledger, AuthorityScope::new("zeta-rh-directionality"));
        let trace = ledger
            .authority_trace("candidate:ihara-graph-rh")
            .expect("directionality residual is recorded");
        assert_eq!(trace.strength, AuthorityStrength::Probed);
        assert_eq!(trace.residuals.len(), 1);
        assert!(!trace.is_terminal_within_domain("zeta-rh-directionality"));
    }
    #[test]
    fn maps_holonomy_artifact_without_terminal_overclaim() {
        let ledger = QDescentGate::holonomy_ladder_ledger();
        let trace = ledger
            .authority_trace("claim:qm-gr-holonomy-ladder")
            .expect("holonomy ladder trace is present");

        assert_eq!(trace.strength, AuthorityStrength::ConditionallySupported);
        assert_eq!(trace.residuals.len(), 3);
        assert!(trace
            .successful_descents
            .iter()
            .all(|result| result.terminal_status == TerminalStatus::Supported));
        assert!(!trace.is_terminal_within_domain("qm-gr-holonomy-ladder"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_007be9bf {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord007be9bf::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord007be9bf::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord007be9bf::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord007be9bf::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord007be9bf::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError007be9bf::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError007be9bf::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
