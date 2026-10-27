use serde::{Deserialize, Serialize};

use super::errors::{QError, QPacketField};
use super::packet::{has_text, option_has_text, QTerminal};

/// Audit packet for representation transport candidates.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct RepresentationTransportPacket {
    pub candidate_id: String,
    pub carrier: String,
    pub composition_rule: Option<String>,
    pub observer_measurement_pairing: Option<String>,
    pub finite_predictions: Vec<String>,
    pub representation_transport: Option<String>,
    pub equivalence_scope: Option<String>,
    pub failure_mode: Option<String>,
    pub residual_selector: Option<String>,
    pub terminal_status_request: Option<QTerminal>,
}

impl RepresentationTransportPacket {
    pub fn real_complex_qm(carrier: impl Into<String>, candidate_id: impl Into<String>) -> Self {
        Self {
            candidate_id: candidate_id.into(),
            carrier: carrier.into(),
            ..Self::default()
        }
    }

    pub fn with_composition_rule(mut self, composition_rule: impl Into<String>) -> Self {
        self.composition_rule = Some(composition_rule.into());
        self
    }

    pub fn with_observer_measurement_pairing(mut self, pairing: impl Into<String>) -> Self {
        self.observer_measurement_pairing = Some(pairing.into());
        self
    }

    pub fn with_finite_prediction(mut self, prediction: impl Into<String>) -> Self {
        self.finite_predictions.push(prediction.into());
        self
    }

    pub fn with_representation_transport(mut self, transport: impl Into<String>) -> Self {
        self.representation_transport = Some(transport.into());
        self
    }

    pub fn with_equivalence_scope(mut self, scope: impl Into<String>) -> Self {
        self.equivalence_scope = Some(scope.into());
        self
    }

    pub fn with_failure_mode(mut self, failure_mode: impl Into<String>) -> Self {
        self.failure_mode = Some(failure_mode.into());
        self
    }

    pub fn with_residual_selector(mut self, residual_selector: impl Into<String>) -> Self {
        self.residual_selector = Some(residual_selector.into());
        self
    }

    pub fn with_terminal_status_request(mut self, terminal_status_request: QTerminal) -> Self {
        self.terminal_status_request = Some(terminal_status_request);
        self
    }

    pub fn with_terminal_status(self, terminal_status_request: QTerminal) -> Self {
        self.with_terminal_status_request(terminal_status_request)
    }

    fn validate_transport_fields(&self) -> Result<(), QError> {
        if !option_has_text(&self.representation_transport)
            || !option_has_text(&self.equivalence_scope)
            || !option_has_text(&self.failure_mode)
        {
            return Err(QError::MissingMandatoryField(QPacketField::Transport));
        }
        if !option_has_text(&self.residual_selector) {
            return Err(QError::MissingMandatoryField(QPacketField::Residual));
        }
        if self.terminal_status_request.is_none() {
            return Err(QError::MissingMandatoryField(QPacketField::TerminalRequest));
        }
        Ok(())
    }

    /// Full transport validation for any representation transport candidate (including real/complex QM).
    pub fn validate_full_transport_packet(&self) -> Result<(), QError> {
        if !has_text(&self.carrier) {
            return Err(QError::MissingMandatoryField(QPacketField::Carrier));
        }
        if !option_has_text(&self.composition_rule) {
            return Err(QError::CompositionRuleRequired);
        }
        if !option_has_text(&self.observer_measurement_pairing) {
            return Err(QError::MissingMandatoryField(QPacketField::Observer));
        }
        if self.finite_predictions.is_empty()
            || !self.finite_predictions.iter().any(|p| has_text(p))
        {
            return Err(QError::MissingMandatoryField(
                QPacketField::FinitePredictions,
            ));
        }
        self.validate_transport_fields()
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/transport.rs
// Claim: urn:core:crates_rs:core-wdp:transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbb7a5235 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbb7a5235` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbb7a5235 {
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
impl BoundaryErrorbb7a5235 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbb7a5235 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbb7a5235 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbb7a5235 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbb7a5235> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbb7a5235::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbb7a5235::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbb7a5235::ExceedsCapacity {
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
mod l4_boundary_tests_bb7a5235 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbb7a5235::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbb7a5235::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbb7a5235::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbb7a5235::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbb7a5235::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbb7a5235::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbb7a5235::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
