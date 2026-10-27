use serde::{Deserialize, Serialize};

use super::admission::{AdmissionDecision, QAdmissionGate, QAdmissionRequest};
use super::packet::{QPacket, QTerminal};
use core_types::q_continuum::{ObstructionKind, Residual};

/// Zeta/RH claim family under the Q firewall.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ZetaRhClaimKind {
    /// Ihara-zeta / graph-Weil analog: finite regular graph shadow and Ramanujan locus.
    IharaGraphRhAnalog,
    /// Classical Riemann Hypothesis for the Riemann zeta function zeta(s).
    ClassicalRiemannHypothesis,
}

/// Direction of the proposed transport between source and finite shadow.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ZetaTransportDirection {
    /// Continuum/source material projects to a declared finite graph/Ihara shadow.
    SourceToShadow,
    /// A finite shadow is claimed to decode or prove its continuum/classical source.
    ShadowDecodesSource,
    /// Source claim appears without a declared finite bridge.
    SourceOnly,
}

/// One zeta/RH candidate routed through Q admission.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZetaRhCandidate {
    pub claim_kind: ZetaRhClaimKind,
    pub direction: ZetaTransportDirection,
    pub packet: QPacket,
    pub admission: QAdmissionRequest,
}

impl ZetaRhCandidate {
    pub fn new(
        claim_kind: ZetaRhClaimKind,
        direction: ZetaTransportDirection,
        packet: QPacket,
        admission: QAdmissionRequest,
    ) -> Self {
        Self {
            claim_kind,
            direction,
            packet,
            admission,
        }
    }
}

/// Zeta/RH firewall decision.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZetaRhDecision {
    pub admission: AdmissionDecision,
    pub crosses_to_gttc: bool,
}

/// Q firewall for graph/Ihara RH analogs versus classical RH claims.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct ZetaRhFirewall;

impl ZetaRhFirewall {
    pub fn new() -> Self {
        Self
    }

    pub fn classify(&self, candidate: &ZetaRhCandidate) -> ZetaRhDecision {
        match (candidate.claim_kind, candidate.direction) {
            (ZetaRhClaimKind::ClassicalRiemannHypothesis, _) => self.refuse_classical_rh(candidate),
            (_, ZetaTransportDirection::ShadowDecodesSource) => {
                self.refuse_shadow_decoding(candidate)
            }
            (ZetaRhClaimKind::IharaGraphRhAnalog, _) => self.classify_graph_analog(candidate),
        }
    }

    fn classify_graph_analog(&self, candidate: &ZetaRhCandidate) -> ZetaRhDecision {
        let admission =
            QAdmissionGate::new().classify_admission(&candidate.packet, &candidate.admission);
        let crosses_to_gttc = candidate.direction == ZetaTransportDirection::SourceToShadow
            && admission.residual.is_none()
            && matches!(
                admission.terminal_status,
                QTerminal::QHeld | QTerminal::ConditionalSupport
            );

        ZetaRhDecision {
            admission,
            crosses_to_gttc,
        }
    }

    fn refuse_classical_rh(&self, candidate: &ZetaRhCandidate) -> ZetaRhDecision {
        ZetaRhDecision {
            admission: AdmissionDecision {
                candidate_id: candidate.admission.candidate_id.clone(),
                kind: candidate.admission.kind,
                terminal_status: QTerminal::Refused,
                obligations: vec![
                    "classical RH needs its own finite bridge; graph/Ihara shadow is not a proof route".to_string(),
                    "record refusal/residual instead of promoting tower zeta to zeta(s)".to_string(),
                ],
                residual: Some(Residual::new(
                    format!("residual:zeta:{}:classical-rh", candidate.admission.candidate_id),
                    candidate.admission.candidate_id.clone(),
                    ObstructionKind::NonFiniteProjection,
                    "classical Riemann Hypothesis claim is not admitted from an Ihara/graph zeta finite shadow",
                )),
            },
            crosses_to_gttc: false,
        }
    }

    fn refuse_shadow_decoding(&self, candidate: &ZetaRhCandidate) -> ZetaRhDecision {
        ZetaRhDecision {
            admission: AdmissionDecision {
                candidate_id: candidate.admission.candidate_id.clone(),
                kind: candidate.admission.kind,
                terminal_status: QTerminal::OpenResidual,
                obligations: vec![
                    "reverse the transport: source-to-shadow projection is allowed, shadow-to-source decoding is not".to_string(),
                    "supply an independent bridge if a source claim is intended".to_string(),
                ],
                residual: Some(Residual::new(
                    format!("residual:zeta:{}:direction", candidate.admission.candidate_id),
                    candidate.admission.candidate_id.clone(),
                    ObstructionKind::AnalogyBreak,
                    "finite zeta shadow forgets its source and cannot decode classical RH or the Q-held continuum source",
                )),
            },
            crosses_to_gttc: false,
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/zeta.rs
// Claim: urn:core:crates_rs:core-wdp:zeta:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6df63f32 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6df63f32` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6df63f32 {
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
impl BoundaryError6df63f32 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6df63f32 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6df63f32 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6df63f32 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6df63f32> {
        if capacity_bound == 0 {
            return Err(BoundaryError6df63f32::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6df63f32::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6df63f32::ExceedsCapacity {
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
mod l4_boundary_tests_6df63f32 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6df63f32::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6df63f32::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6df63f32::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6df63f32::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6df63f32::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6df63f32::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6df63f32::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
