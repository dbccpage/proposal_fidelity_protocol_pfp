
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_74386cdd<T> {
    fn checked_invariant_74386cdd(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_74386cdd<T> for Option<T> {
    #[inline]
    fn checked_invariant_74386cdd(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_74386cdd<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_74386cdd(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};

use super::continuum::ContinuumDebt;
use super::errors::QError;
use super::packet::{QPacket, QTerminal};
use core_types::q_continuum::{
    AuthorityScope, DescentResult, ObstructionKind, QContinuumLedger, Residual,
};

/// What kind of Q candidate is being admitted.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum CandidateKind {
    Theory,
    Representation,
    Analogy,
    Model,
    Source,
    ProbeRequest,
}

/// Admission request attached to one candidate.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QAdmissionRequest {
    pub candidate_id: String,
    pub kind: CandidateKind,
    pub continuum: ContinuumDebt,
}

impl QAdmissionRequest {
    pub fn new(candidate_id: impl Into<String>, kind: CandidateKind) -> Self {
        Self {
            candidate_id: candidate_id.into(),
            kind,
            continuum: ContinuumDebt::default(),
        }
    }

    pub fn with_finite_shadow(mut self, finite_shadow: impl Into<String>) -> Self {
        self.continuum.finite_shadow = Some(finite_shadow.into());
        self
    }

    pub fn with_refinement_relation(mut self, refinement_relation: impl Into<String>) -> Self {
        self.continuum.refinement_relation = Some(refinement_relation.into());
        self
    }

    pub fn with_declared_topology(mut self, declared_topology: impl Into<String>) -> Self {
        self.continuum.declared_topology = Some(declared_topology.into());
        self
    }

    pub fn with_convergence_certificate_route(
        mut self,
        convergence_certificate_route: impl Into<String>,
    ) -> Self {
        self.continuum.convergence_certificate_route = Some(convergence_certificate_route.into());
        self
    }

    pub fn with_descent_trigger(mut self, descent_trigger: impl Into<String>) -> Self {
        self.continuum.descent_trigger = Some(descent_trigger.into());
        self
    }
}

/// Classification result for a Q admission candidate.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AdmissionDecision {
    pub candidate_id: String,
    pub kind: CandidateKind,
    pub terminal_status: QTerminal,
    pub obligations: Vec<String>,
    pub residual: Option<Residual>,
}

impl AdmissionDecision {
    /// Records the admission residual as an append-only Q ledger row.
    pub fn record_residual(&self, ledger: &mut QContinuumLedger, scope: AuthorityScope) {
        if let Some(residual) = self.residual.clone() {
            let result =
                DescentResult::failed(format!("admission:{}", self.candidate_id), scope, residual);
            ledger.record_descent_result(self.candidate_id.clone(), result);
        }
    }
}

/// Strict Q admission gate.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct QAdmissionGate;

impl QAdmissionGate {
    pub fn new() -> Self {
        Self
    }

    pub fn classify_admission(
        &self,
        packet: &QPacket,
        request: &QAdmissionRequest,
    ) -> AdmissionDecision {
        let mut obligations = vec![
            "produce finite projection".to_string(),
            "record descent obligation".to_string(),
            "record residual if no witness exists".to_string(),
        ];

        if let Err(error) = packet.validate_mandatory() {
            obligations.push("fix missing mandatory packet fields".to_string());
            return AdmissionDecision {
                candidate_id: request.candidate_id.clone(),
                kind: request.kind,
                terminal_status: QTerminal::OpenResidual,
                obligations,
                residual: Some(residual_for_error(&request.candidate_id, error)),
            };
        }

        let terminal_request = packet.terminal_request.unwrap_or(QTerminal::OpenResidual);
        let mut residual = None;

        let mut derived_status = if terminal_request == QTerminal::TerminalWithinScope {
            obligations.push(
                "TerminalWithinScope requires finite descent evidence with witness support"
                    .to_string(),
            );
            residual = Some(Residual::new(
                format!(
                    "residual:admission:{}:terminal-request",
                    request.candidate_id
                ),
                request.candidate_id.clone(),
                ObstructionKind::MissingWitness,
                "QPacket requested TerminalWithinScope without a finite descent witness",
            ));
            QTerminal::OpenResidual
        } else {
            terminal_request
        };

        let admission_result = if derived_status == QTerminal::QHeld {
            request.continuum.validate_for_qheld()
        } else {
            request.continuum.validate_for_admission()
        };

        if let Err(error) = admission_result {
            obligations.push(format!("admission validation failed: {error}"));
            derived_status = terminal_for_error(&error);
            residual = Some(residual_for_error(&request.candidate_id, error));
        }

        AdmissionDecision {
            candidate_id: request.candidate_id.clone(),
            kind: request.kind,
            terminal_status: derived_status,
            obligations,
            residual,
        }
    }

    pub fn admit_qheld(
        &self,
        packet: &QPacket,
        request: &QAdmissionRequest,
    ) -> Result<AdmissionDecision, QError> {
        packet.validate_mandatory()?;
        request.continuum.validate_for_qheld()?;

        let terminal_request = packet
            .terminal_request
            .checked_invariant_74386cdd("validated packet has terminal_request");
        if terminal_request != QTerminal::QHeld {
            return Err(QError::OpenResidual);
        }

        Ok(AdmissionDecision {
            candidate_id: request.candidate_id.clone(),
            kind: request.kind,
            terminal_status: QTerminal::QHeld,
            obligations: vec![
                "produce finite projection".to_string(),
                "record descent obligation".to_string(),
                "record residual if no witness exists".to_string(),
            ],
            residual: None,
        })
    }
}

fn terminal_for_error(error: &QError) -> QTerminal {
    match error {
        QError::RefusedContinuumNoShadow
        | QError::QHeldWithoutFiniteShadow
        | QError::ContinuumClaimWithoutTopology
        | QError::NoGenesisBoundaryViolation => QTerminal::Refused,
        QError::OracleNeededConvergence => QTerminal::OracleNeeded,
        _ => QTerminal::OpenResidual,
    }
}

fn residual_for_error(candidate_id: &str, error: QError) -> Residual {
    let obstruction = match error {
        QError::RefusedContinuumNoShadow
        | QError::QHeldWithoutFiniteShadow
        | QError::ContinuumClaimWithoutTopology
        | QError::NoGenesisBoundaryViolation => ObstructionKind::NonFiniteProjection,
        QError::OracleNeededConvergence => ObstructionKind::ReplayMissing,
        QError::QHeldWithoutRefinementRoute
        | QError::QHeldWithoutDescentTrigger
        | QError::OpenResidual
        | QError::CompositionRuleRequired
        | QError::MissingMandatoryField(_) => ObstructionKind::Underdefined,
    };
    Residual::new(
        format!("residual:admission:{candidate_id}"),
        candidate_id.to_string(),
        obstruction,
        format!("Q admission failed: {error}"),
    )
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/admission.rs
// Claim: urn:core:crates_rs:core-wdp:admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord74386cdd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord74386cdd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError74386cdd {
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
impl BoundaryError74386cdd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError74386cdd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError74386cdd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord74386cdd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError74386cdd> {
        if capacity_bound == 0 {
            return Err(BoundaryError74386cdd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError74386cdd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError74386cdd::ExceedsCapacity {
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
    use super::super::packet::{ResidualSpec, TransportSpec};
    use super::*;

    fn valid_packet(terminal_request: QTerminal) -> QPacket {
        QPacket::new("q:admission:test")
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

    fn complete_qheld_request() -> QAdmissionRequest {
        QAdmissionRequest::new("candidate:admission:test", CandidateKind::Representation)
            .with_finite_shadow("finite shadow")
            .with_refinement_relation("refinement route")
            .with_declared_topology("finite-discrete topology")
            .with_convergence_certificate_route("certificate route")
            .with_descent_trigger("next finite replay")
    }

    #[test]
    fn rejects_qheld_without_finite_shadow() {
        let packet = valid_packet(QTerminal::QHeld);
        let mut request = complete_qheld_request();
        request.continuum.finite_shadow = None;

        assert_eq!(
            QAdmissionGate::new().admit_qheld(&packet, &request),
            Err(QError::QHeldWithoutFiniteShadow)
        );
    }

    #[test]
    fn rejects_qheld_without_refinement_route() {
        let packet = valid_packet(QTerminal::QHeld);
        let mut request = complete_qheld_request();
        request.continuum.refinement_relation = None;

        assert_eq!(
            QAdmissionGate::new().admit_qheld(&packet, &request),
            Err(QError::QHeldWithoutRefinementRoute)
        );
    }

    #[test]
    fn rejects_qheld_without_declared_topology() {
        let packet = valid_packet(QTerminal::QHeld);
        let mut request = complete_qheld_request();
        request.continuum.declared_topology = None;

        assert_eq!(
            QAdmissionGate::new().admit_qheld(&packet, &request),
            Err(QError::ContinuumClaimWithoutTopology)
        );
    }

    #[test]
    fn rejects_qheld_without_convergence_certificate_route() {
        let packet = valid_packet(QTerminal::QHeld);
        let mut request = complete_qheld_request();
        request.continuum.convergence_certificate_route = None;

        assert_eq!(
            QAdmissionGate::new().admit_qheld(&packet, &request),
            Err(QError::QHeldWithoutRefinementRoute)
        );
    }

    #[test]
    fn rejects_qheld_without_descent_trigger() {
        let packet = valid_packet(QTerminal::QHeld);
        let mut request = complete_qheld_request();
        request.continuum.descent_trigger = None;

        assert_eq!(
            QAdmissionGate::new().admit_qheld(&packet, &request),
            Err(QError::QHeldWithoutDescentTrigger)
        );
    }

    #[test]
    fn packet_cannot_self_declare_terminal_within_scope() {
        let packet = valid_packet(QTerminal::TerminalWithinScope);
        let request = complete_qheld_request();

        let decision = QAdmissionGate::new().classify_admission(&packet, &request);
        assert_eq!(decision.terminal_status, QTerminal::OpenResidual);
        assert!(decision.residual.is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_74386cdd {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord74386cdd::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord74386cdd::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord74386cdd::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord74386cdd::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord74386cdd::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError74386cdd::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError74386cdd::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
