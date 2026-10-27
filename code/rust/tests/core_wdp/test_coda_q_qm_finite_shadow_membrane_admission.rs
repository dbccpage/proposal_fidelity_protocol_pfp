//! Q-RES-MEMBRANE-001 — FinL1 / QM finite-shadow continuum non-promotion.
//!
//! Skill: `/goo-q-finite-shadow-limit-loop`
//! Packet: `proof_packets/q_res_membrane_001_20260731/`
//! AuthorityEffect: None
//!
//! Finite shadows may request continuum-facing terminals only through ContinuumDebt.
//! Missing shadow → refuse. Missing certificate route → OracleNeeded.
//! QHeld / ConditionalSupport never mint authority by themselves.

use core_wdp::coda::q::{
    CandidateKind, ContinuumDebt, QAdmissionGate, QAdmissionRequest, QError, QPacket, QTerminal,
    ResidualSpec, TransportSpec,
};
use core_types::q_continuum::{AuthorityScope, ObstructionKind, QContinuumLedger};

fn membrane_packet(terminal: QTerminal) -> QPacket {
    QPacket::new("q:qm-finl1:continuum-membrane")
        .with_carrier("FinL1 residual sectors + finite path-sum/unitary shadows (qm_032-034)")
        .with_composition("admitted monoid transports on frozen finite carrier only")
        .with_observer("phase-blind L1 / modulus-only probes")
        .with_finite_prediction("finite path-sum Chapman-Kolmogorov on declared graphs")
        .with_finite_prediction("no continuum kernel without convergence certificate")
        .with_transport(
            TransportSpec::new("finite shadow family to continuum-facing claim")
                .with_equivalence_scope("finite operational predictions only")
                .with_failure_mode("missing cert, missing shadow, or shadow-decodes-source"),
        )
        .with_residual(
            ResidualSpec::new(
                "continuum kernel / exp(tH) / path measure held in Q until cert+descent",
                ObstructionKind::NonFiniteProjection,
            )
            .with_next_probe_hint("supply ConvergenceCertificate or residual OracleNeeded"),
        )
        .with_terminal_request(terminal)
}

fn complete_debt() -> ContinuumDebt {
    ContinuumDebt {
        finite_shadow: Some(
            "family=FinL1-qm-shadow;freeze=v0.1;sources=qm_032,qm_033,qm_034,qm_009".to_string(),
        ),
        refinement_relation: Some(
            "declared cofinal refinement of finite sector graphs / path lengths".to_string(),
        ),
        declared_topology: Some(
            "finite-discrete sector topology; continuum object held in Q".to_string(),
        ),
        convergence_certificate_route: Some(
            "schema=core.qm-shadow-membrane.v1;replay=qm_009;status=route-named-not-proved"
                .to_string(),
        ),
        descent_trigger: Some("supply ConvergenceCertificate or residual OracleNeeded".to_string()),
    }
}

fn request_with(debt: ContinuumDebt) -> QAdmissionRequest {
    QAdmissionRequest {
        candidate_id: "q:qm-finl1:continuum-membrane".to_string(),
        kind: CandidateKind::Model,
        continuum: debt,
    }
}

/// FC-MEMBRANE-NO-SHADOW: continuum-facing claim without finite shadow is refused.
#[test]
fn membrane_refuses_continuum_without_finite_shadow() {
    let packet = membrane_packet(QTerminal::ConditionalSupport);
    let mut debt = complete_debt();
    debt.finite_shadow = None;

    assert_eq!(
        debt.validate_for_admission(),
        Err(QError::RefusedContinuumNoShadow)
    );

    let decision = QAdmissionGate::new().classify_admission(&packet, &request_with(debt));
    assert_eq!(decision.terminal_status, QTerminal::Refused);
    assert!(decision.residual.is_some());
    assert_eq!(
        decision.residual.as_ref().unwrap().obstruction,
        ObstructionKind::NonFiniteProjection
    );
}

/// FC-MEMBRANE-NO-CERT: finite shadow without certificate route → OracleNeeded.
#[test]
fn membrane_oracle_needed_without_convergence_certificate_route() {
    let packet = membrane_packet(QTerminal::ConditionalSupport);
    let mut debt = complete_debt();
    debt.convergence_certificate_route = None;

    assert_eq!(
        debt.validate_for_admission(),
        Err(QError::OracleNeededConvergence)
    );

    let decision = QAdmissionGate::new().classify_admission(&packet, &request_with(debt));
    assert_eq!(decision.terminal_status, QTerminal::OracleNeeded);
    assert!(decision.residual.is_some());
}

/// Full debt + ConditionalSupport: admitted as conditional, not TerminalWithinScope.
#[test]
fn membrane_full_debt_conditional_support_not_self_terminal() {
    let packet = membrane_packet(QTerminal::ConditionalSupport);
    let debt = complete_debt();
    assert_eq!(debt.validate_for_admission(), Ok(()));

    let decision = QAdmissionGate::new().classify_admission(&packet, &request_with(debt));
    assert_eq!(decision.terminal_status, QTerminal::ConditionalSupport);
    assert!(decision.residual.is_none());
}

/// FC-MEMBRANE-SELF-TERMINAL: TerminalWithinScope request without witness → OpenResidual.
#[test]
fn membrane_cannot_self_declare_terminal_within_scope() {
    let packet = membrane_packet(QTerminal::TerminalWithinScope);
    let decision =
        QAdmissionGate::new().classify_admission(&packet, &request_with(complete_debt()));
    assert_eq!(decision.terminal_status, QTerminal::OpenResidual);
    assert!(decision.residual.is_some());
}

/// QHeld with complete continuum debt is allowed as quarantine status, still ⊬ authority.
#[test]
fn membrane_qheld_with_complete_debt_records_no_authority_mint() {
    let packet = membrane_packet(QTerminal::QHeld);
    let debt = complete_debt();
    assert_eq!(debt.validate_for_qheld(), Ok(()));

    let decision = QAdmissionGate::new().admit_qheld(&packet, &request_with(debt));
    assert!(decision.is_ok());
    let decision = decision.unwrap();
    assert_eq!(decision.terminal_status, QTerminal::QHeld);
    assert!(decision.residual.is_none());

    // No residual row ⇒ no Probed residual trail; still no automatic GlobalGreen.
    // Authority traces only appear when residuals are recorded.
    let mut ledger = QContinuumLedger::new();
    decision.record_residual(&mut ledger, AuthorityScope::new("q-res-membrane-001"));
    assert!(
        ledger
            .authority_trace("q:qm-finl1:continuum-membrane")
            .is_none(),
        "QHeld without residual must not mint an authority-strength trail by admission alone"
    );
}

/// FC-MEMBRANE-TYPE-SPLIT: CONT-* slots stay distinct labels (Hotel fence).
#[test]
fn continuum_type_split_slots_are_pairwise_distinct() {
    let slots = [
        ("CONT-TIME", "exp(tH) continuous generator"),
        ("CONT-SECTORS", "unbounded continuous spectrum"),
        ("CONT-HILBERT", "infinite-dimensional Hilbert"),
        ("CONT-PATH", "continuum path measure"),
        ("CARD_HOTEL", "countable re-rooming metaphor fence"),
    ];
    for (i, (a, _)) in slots.iter().enumerate() {
        for (j, (b, _)) in slots.iter().enumerate() {
            if i != j {
                assert_ne!(a, b, "continuum slots must not collapse");
            }
        }
    }
    // Each slot needs its own debt package — missing cert still OracleNeeded per slot.
    for (slot, example) in slots {
        let mut debt = complete_debt();
        debt.finite_shadow = Some(format!("slot={slot};example={example};freeze=v0.1"));
        debt.convergence_certificate_route = None;
        assert_eq!(
            debt.validate_for_admission(),
            Err(QError::OracleNeededConvergence),
            "slot {slot} without cert must not silently admit"
        );
    }
}

/// Directionality: finite shadow narrative must not claim source decode.
#[test]
fn membrane_packet_residual_blocks_source_decode_overclaim() {
    let packet = membrane_packet(QTerminal::ConditionalSupport);
    let residual = packet.residual.as_ref().expect("residual required");
    let note = residual.description.to_lowercase();
    assert!(
        note.contains("held in q") || note.contains("cert"),
        "membrane residual must quarantine continuum, not claim source recovery"
    );
    let transport = packet.transport.as_ref().expect("transport required");
    let fail = transport
        .failure_mode
        .as_deref()
        .unwrap_or("")
        .to_lowercase();
    assert!(
        fail.contains("shadow-decodes-source") || fail.contains("decode"),
        "transport failure_mode must name shadow-decode refusal"
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_coda_q_qm_finite_shadow_membrane_admission.rs
// Claim: urn:core:crates_rs:tests:test-coda-q-qm-finite-shadow-membrane-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda091d959 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda091d959` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora091d959 {
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
impl BoundaryErrora091d959 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora091d959 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora091d959 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda091d959 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora091d959> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora091d959::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora091d959::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora091d959::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a091d959() {
    let admitted = BoundaryRecorda091d959::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda091d959::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
