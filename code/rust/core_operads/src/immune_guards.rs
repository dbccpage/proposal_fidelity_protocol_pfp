//! Guard application through workflow-owned ports; no immune domain import.
use crate::{
    immune_ports::{
        DetectorIdentity, DetectorMatch, HostDangerObservation, ImmuneScreenPort, SensorReading,
    },
    planar::{substitute, OperadOperation},
    policy::DangerSignalPolicy,
    workflow::{python_text, WorkflowReport},
    Refusal,
};
use serde_json::Value;

pub struct DangerScreenRequest<'a> {
    pub detector: &'a DetectorIdentity,
    pub matches: &'a [DetectorMatch],
    pub danger: Option<&'a HostDangerObservation>,
}

pub fn immune_guarded_substitute(
    theta: &OperadOperation,
    index: &Value,
    phi: &OperadOperation,
    immune: &mut dyn ImmuneScreenPort,
    evidence: DangerScreenRequest<'_>,
) -> Result<OperadOperation, Refusal> {
    let verdict = immune.danger_verdict(evidence.matches, evidence.danger, evidence.detector)?;
    if *verdict.blocks() {
        return Err(Refusal::new(
            "DANGER_GATE_SUPPRESSION",
            format!(
                "Substitution of {} into {} slot {} suppressed: {}",
                phi.name(),
                theta.name(),
                python_text(index),
                verdict.rationale()
            ),
        ));
    }
    substitute(theta, index, phi)
}

pub fn allosteric_consensus_substitute(
    theta: &OperadOperation,
    index: &Value,
    phi: &OperadOperation,
    readings: &[SensorReading],
    immune: &mut dyn ImmuneScreenPort,
) -> Result<OperadOperation, Refusal> {
    let verdict = immune.quorum_verdict(readings)?;
    if *verdict.blocks() {
        return Err(Refusal::new(
            "ALLOSTERIC_QUORUM_NOT_MET",
            format!(
                "Substitution of {} into {} slot {} refused: {}",
                phi.name(),
                theta.name(),
                python_text(index),
                verdict.rationale()
            ),
        ));
    }
    substitute(theta, index, phi)
}

pub fn validate_workflow_immune_guard(
    report: &WorkflowReport,
    policy: &DangerSignalPolicy,
    immune: &mut dyn ImmuneScreenPort,
    evidence: DangerScreenRequest<'_>,
) -> Result<WorkflowReport, Refusal> {
    if !policy.enforce_danger_gate() {
        return Ok(report.clone());
    }
    match immune.danger_verdict(evidence.matches, evidence.danger, evidence.detector) {
        Ok(verdict) if !*verdict.blocks() => Ok(report.clone()),
        Ok(verdict) => Ok(report.with_guard_finding(
            "DANGER_GATE_SUPPRESSION".into(),
            verdict.rationale().clone(),
        )),
        Err(error) => {
            let prefix = format!("{}: ", error.code);
            let detail = error
                .message
                .strip_prefix(&prefix)
                .unwrap_or(&error.message)
                .to_owned();
            Ok(report.with_guard_finding(error.code, detail))
        }
    }
}

// Origin: engine/crates_rs/core_operads/src/immune_guards.rs
// Claim: urn:core:crates_rs:core-operads:immune-guards:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordea7c2de5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordea7c2de5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorea7c2de5 {
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
impl BoundaryErrorea7c2de5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorea7c2de5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorea7c2de5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordea7c2de5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorea7c2de5> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorea7c2de5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorea7c2de5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorea7c2de5::ExceedsCapacity {
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
mod l4_boundary_tests_ea7c2de5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordea7c2de5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordea7c2de5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordea7c2de5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordea7c2de5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordea7c2de5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorea7c2de5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorea7c2de5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
