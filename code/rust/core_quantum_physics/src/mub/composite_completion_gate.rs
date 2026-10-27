//! Composite complete-target gate for MUB(6), MUB(10), and similar dimensions.
//!
//! Tensor products of complete prime-power controls give useful exact lower
//! controls in composite dimensions. They do not, by themselves, supply either
//! a complete `d+1`-basis witness or a no-go certificate. This module makes the
//! certificate boundary executable and rejects promotion from lower-control
//! evidence to complete composite authority.

use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum CompositeCompletionTarget {
    Mub6,
    Mub10,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum CompositeCompletionStatus {
    CompleteWitnessAccepted,
    NoGoCertificateAccepted,
    LowerControlOnly,
    MissingLowerControl,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CompositeCompletionGateReport {
    pub target: CompositeCompletionTarget,
    pub dimension: usize,
    pub required_complete_basis_count: usize,
    pub lower_control_basis_count: Option<usize>,
    pub missing_basis_count: Option<usize>,
    pub status: CompositeCompletionStatus,
    pub accepted_certificate: Option<&'static str>,
    pub checked_obligations: Vec<&'static str>,
    pub missing_obligations: Vec<&'static str>,
    pub rejected_escalations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CompositeCompletionInputs {
    pub target: CompositeCompletionTarget,
    pub lower_control_basis_count: Option<usize>,
    pub complete_witness_replayed: bool,
    pub no_go_certificate_replayed: bool,
}

pub fn verify_current_composite_completion_gates(
    d6_lower_control_verified: bool,
    d10_lower_control_verified: bool,
    d6_no_go_certificate_replayed: bool,
) -> Vec<CompositeCompletionGateReport> {
    vec![
        verify_composite_completion_gate(CompositeCompletionInputs {
            target: CompositeCompletionTarget::Mub6,
            lower_control_basis_count: d6_lower_control_verified.then_some(3),
            complete_witness_replayed: false,
            no_go_certificate_replayed: d6_no_go_certificate_replayed,
        }),
        verify_composite_completion_gate(CompositeCompletionInputs {
            target: CompositeCompletionTarget::Mub10,
            lower_control_basis_count: d10_lower_control_verified.then_some(3),
            complete_witness_replayed: false,
            no_go_certificate_replayed: false,
        }),
    ]
}

pub fn verify_composite_completion_gate(
    inputs: CompositeCompletionInputs,
) -> CompositeCompletionGateReport {
    let dimension: usize = match inputs.target {
        CompositeCompletionTarget::Mub6 => 6,
        CompositeCompletionTarget::Mub10 => 10,
    };
    let required_complete_basis_count = dimension + 1;
    let missing_basis_count = inputs
        .lower_control_basis_count
        .map(|count| required_complete_basis_count.saturating_sub(count));

    if inputs.complete_witness_replayed {
        return CompositeCompletionGateReport {
            target: inputs.target,
            dimension,
            required_complete_basis_count,
            lower_control_basis_count: inputs.lower_control_basis_count,
            missing_basis_count,
            status: CompositeCompletionStatus::CompleteWitnessAccepted,
            accepted_certificate: Some("exact complete d+1-basis witness replay"),
            checked_obligations: vec![
                "exact complete witness replayed",
                "complete basis count target satisfied by certificate",
                "ZeroRel and terminalizer are delegated to the replayed witness certificate",
            ],
            missing_obligations: vec![],
            rejected_escalations: vec![],
            boundary: "complete composite witness accepted for the declared target only",
            error: None,
        };
    }

    if inputs.no_go_certificate_replayed {
        return CompositeCompletionGateReport {
            target: inputs.target,
            dimension,
            required_complete_basis_count,
            lower_control_basis_count: inputs.lower_control_basis_count,
            missing_basis_count,
            status: CompositeCompletionStatus::NoGoCertificateAccepted,
            accepted_certificate: Some("exact no-go certificate replay"),
            checked_obligations: vec![
                "exact no-go certificate replayed",
                "complete d+1-basis target obstructed by certificate",
                "ZeroRel and terminalizer are delegated to the replayed no-go certificate",
            ],
            missing_obligations: vec![],
            rejected_escalations: vec![],
            boundary: "complete composite no-go certificate accepted for the declared target only",
            error: None,
        };
    }

    let Some(lower_control_basis_count) = inputs.lower_control_basis_count else {
        return CompositeCompletionGateReport {
            target: inputs.target,
            dimension,
            required_complete_basis_count,
            lower_control_basis_count: None,
            missing_basis_count: None,
            status: CompositeCompletionStatus::MissingLowerControl,
            accepted_certificate: None,
            checked_obligations: vec![],
            missing_obligations: certificate_obligations(inputs.target),
            rejected_escalations: vec![
                "missing lower-control evidence cannot imply complete composite authority",
            ],
            boundary: "no composite lower-control or complete certificate is present",
            error: Some("missing exact lower-control replay".to_string()),
        };
    };

    let missing_basis_count =
        required_complete_basis_count.saturating_sub(lower_control_basis_count);
    CompositeCompletionGateReport {
        target: inputs.target,
        dimension,
        required_complete_basis_count,
        lower_control_basis_count: Some(lower_control_basis_count),
        missing_basis_count: Some(missing_basis_count),
        status: CompositeCompletionStatus::LowerControlOnly,
        accepted_certificate: None,
        checked_obligations: vec![
            "exact tensor lower-control replayed",
            "basis-count gap against complete d+1 target computed",
        ],
        missing_obligations: certificate_obligations(inputs.target),
        rejected_escalations: vec![
            "tensor lower-control does not provide the missing complete bases",
            "basis-count lower bound does not prove nonexistence",
            "composite complete authority still requires a witness or no-go certificate",
        ],
        boundary: "lower-control only; complete composite authority is not accepted",
        error: None,
    }
}

fn certificate_obligations(target: CompositeCompletionTarget) -> Vec<&'static str> {
    match target {
        CompositeCompletionTarget::Mub6 => vec![
            "exact seven-basis MUB(6) witness or proof-carrying no-go certificate",
            "exhaustive MUB(6) triple atlas if using the pinned-wall no-go route",
            "wall-certified transport patch for every atlas class",
            "basis-gluing theorem from fourth-vector obstruction to no complete seven-basis set",
            "CODA-MUR loss ledger preserving ZeroRel and terminalizer across atlas transports",
        ],
        CompositeCompletionTarget::Mub10 => vec![
            "exact eleven-basis MUB(10) witness or proof-carrying no-go certificate",
            "declared exact d=10 carrier and equivalence policy",
            "declared repair group and observer for complete d=10 configurations",
            "independent replay of the complete witness or no-go certificate",
            "CODA-MUR loss ledger preserving ZeroRel and terminalizer for the d=10 carrier",
        ],
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/composite_completion_gate.rs
// Claim: urn:core:crates_rs:core-quantum-physics:composite-completion-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord241662e2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord241662e2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError241662e2 {
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
impl BoundaryError241662e2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError241662e2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError241662e2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord241662e2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError241662e2> {
        if capacity_bound == 0 {
            return Err(BoundaryError241662e2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError241662e2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError241662e2::ExceedsCapacity {
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

    #[test]
    fn composite_completion_gate_rejects_lower_control_promotion() {
        let report = verify_composite_completion_gate(CompositeCompletionInputs {
            target: CompositeCompletionTarget::Mub6,
            lower_control_basis_count: Some(3),
            complete_witness_replayed: false,
            no_go_certificate_replayed: false,
        });
        assert_eq!(report.status, CompositeCompletionStatus::LowerControlOnly);
        assert_eq!(report.required_complete_basis_count, 7);
        assert_eq!(report.missing_basis_count, Some(4));
        assert!(report
            .rejected_escalations
            .iter()
            .any(|item| item.contains("does not provide")));
    }

    #[test]
    fn composite_completion_gate_accepts_only_witness_or_no_go_certificate() {
        let witness = verify_composite_completion_gate(CompositeCompletionInputs {
            target: CompositeCompletionTarget::Mub10,
            lower_control_basis_count: Some(3),
            complete_witness_replayed: true,
            no_go_certificate_replayed: false,
        });
        assert_eq!(
            witness.status,
            CompositeCompletionStatus::CompleteWitnessAccepted
        );
        assert!(witness.missing_obligations.is_empty());

        let no_go = verify_composite_completion_gate(CompositeCompletionInputs {
            target: CompositeCompletionTarget::Mub6,
            lower_control_basis_count: Some(3),
            complete_witness_replayed: false,
            no_go_certificate_replayed: true,
        });
        assert_eq!(
            no_go.status,
            CompositeCompletionStatus::NoGoCertificateAccepted
        );
        assert!(no_go.missing_obligations.is_empty());
    }
}

#[cfg(test)]
mod l4_boundary_tests_241662e2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord241662e2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord241662e2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord241662e2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord241662e2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord241662e2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError241662e2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError241662e2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
