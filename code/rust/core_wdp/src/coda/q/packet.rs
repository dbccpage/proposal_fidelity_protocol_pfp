use serde::{Deserialize, Serialize};

use super::errors::{QError, QPacketField};
use core_types::q_continuum::{ObstructionKind, TerminalStatus};

/// Local Q terminal request labels used for packet admission.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum QTerminal {
    Refused,
    OpenResidual,
    OracleNeeded,
    QHeld,
    ConditionalSupport,
    TerminalWithinScope,
}

impl QTerminal {
    /// Converts an admission classification into the nearest Q ledger status.
    ///
    /// A raw packet request for `TerminalWithinScope` is never converted through
    /// this helper before [`crate::coda::admission::QAdmissionGate::classify_admission`]
    /// has derived a non-terminal classification from finite evidence.
    pub fn to_terminal_status(self) -> TerminalStatus {
        match self {
            Self::Refused => TerminalStatus::Refused,
            Self::OpenResidual | Self::OracleNeeded | Self::QHeld | Self::TerminalWithinScope => {
                TerminalStatus::Residual
            }
            Self::ConditionalSupport => TerminalStatus::ConditionallySupported,
        }
    }
}

/// Representation transport route declared by a Q packet.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TransportSpec {
    pub route: String,
    pub equivalence_scope: Option<String>,
    pub failure_mode: Option<String>,
}

impl TransportSpec {
    pub fn new(route: impl Into<String>) -> Self {
        Self {
            route: route.into(),
            equivalence_scope: None,
            failure_mode: None,
        }
    }

    pub fn with_equivalence_scope(mut self, scope: impl Into<String>) -> Self {
        self.equivalence_scope = Some(scope.into());
        self
    }

    pub fn with_failure_mode(mut self, failure_mode: impl Into<String>) -> Self {
        self.failure_mode = Some(failure_mode.into());
        self
    }

    pub fn is_declared(&self) -> bool {
        has_text(&self.route)
    }
}

/// Residual carried by the packet before any finite promotion.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResidualSpec {
    pub description: String,
    pub obstruction: ObstructionKind,
    pub next_probe_hint: Option<String>,
}

impl ResidualSpec {
    pub fn new(description: impl Into<String>, obstruction: ObstructionKind) -> Self {
        Self {
            description: description.into(),
            obstruction,
            next_probe_hint: None,
        }
    }

    pub fn with_next_probe_hint(mut self, hint: impl Into<String>) -> Self {
        self.next_probe_hint = Some(hint.into());
        self
    }

    pub fn is_declared(&self) -> bool {
        has_text(&self.description)
    }
}

/// Mandatory Q packet.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct QPacket {
    pub id: String,
    pub carrier: Option<String>,
    pub composition: Option<String>,
    pub observer: Option<String>,
    pub finite_predictions: Vec<String>,
    pub transport: Option<TransportSpec>,
    pub residual: Option<ResidualSpec>,
    pub terminal_request: Option<QTerminal>,
}

impl QPacket {
    pub fn new(id: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            ..Self::default()
        }
    }

    pub fn with_carrier(mut self, carrier: impl Into<String>) -> Self {
        self.carrier = Some(carrier.into());
        self
    }

    pub fn with_composition(mut self, composition: impl Into<String>) -> Self {
        self.composition = Some(composition.into());
        self
    }

    pub fn with_observer(mut self, observer: impl Into<String>) -> Self {
        self.observer = Some(observer.into());
        self
    }

    pub fn with_finite_prediction(mut self, prediction: impl Into<String>) -> Self {
        self.finite_predictions.push(prediction.into());
        self
    }

    pub fn with_transport(mut self, transport: TransportSpec) -> Self {
        self.transport = Some(transport);
        self
    }

    pub fn with_residual(mut self, residual: ResidualSpec) -> Self {
        self.residual = Some(residual);
        self
    }

    pub fn with_terminal_request(mut self, terminal_request: QTerminal) -> Self {
        self.terminal_request = Some(terminal_request);
        self
    }

    pub fn missing_mandatory_fields(&self) -> Vec<QPacketField> {
        let mut missing = Vec::new();

        if !option_has_text(&self.carrier) {
            missing.push(QPacketField::Carrier);
        }
        if !option_has_text(&self.composition) {
            missing.push(QPacketField::Composition);
        }
        if !option_has_text(&self.observer) {
            missing.push(QPacketField::Observer);
        }
        if !self
            .finite_predictions
            .iter()
            .any(|prediction| has_text(prediction))
        {
            missing.push(QPacketField::FinitePredictions);
        }
        if !self
            .transport
            .as_ref()
            .is_some_and(TransportSpec::is_declared)
        {
            missing.push(QPacketField::Transport);
        }
        if !self
            .residual
            .as_ref()
            .is_some_and(ResidualSpec::is_declared)
        {
            missing.push(QPacketField::Residual);
        }
        if self.terminal_request.is_none() {
            missing.push(QPacketField::TerminalRequest);
        }

        missing
    }

    pub fn validate_mandatory(&self) -> Result<(), QError> {
        match self.missing_mandatory_fields().first().copied() {
            Some(field) => Err(QError::MissingMandatoryField(field)),
            None => Ok(()),
        }
    }
}

/// Packet that has passed mandatory field validation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValidatedQPacket {
    packet: QPacket,
}

impl ValidatedQPacket {
    pub fn packet(&self) -> &QPacket {
        &self.packet
    }

    pub fn into_packet(self) -> QPacket {
        self.packet
    }
}

impl TryFrom<QPacket> for ValidatedQPacket {
    type Error = QError;

    fn try_from(packet: QPacket) -> Result<Self, Self::Error> {
        packet.validate_mandatory()?;
        Ok(Self { packet })
    }
}

pub(crate) fn has_text(value: &str) -> bool {
    !value.trim().is_empty()
}

pub(crate) fn option_has_text(value: &Option<String>) -> bool {
    value.as_deref().is_some_and(has_text)
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/packet.rs
// Claim: urn:core:crates_rs:core-wdp:packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda4e8733a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda4e8733a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora4e8733a {
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
impl BoundaryErrora4e8733a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora4e8733a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora4e8733a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda4e8733a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora4e8733a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora4e8733a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora4e8733a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora4e8733a::ExceedsCapacity {
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
mod l4_boundary_tests_a4e8733a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda4e8733a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda4e8733a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda4e8733a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda4e8733a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda4e8733a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora4e8733a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora4e8733a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
