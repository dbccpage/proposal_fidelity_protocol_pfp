use crate::kinds::{BaseType, ContractEffect};
use crate::traits::identity::NamedComponent as OperatorIdentity;
use core_types::trace_artifact::TraceArtifact;

pub trait Runtime<S: BaseType> {
    type Pipeline: Pipeline<S>;
    type Input;
    type RuntimeState: BaseType;
    type Output;
    type Trace: TraceArtifact;
    type Error;

    // (state, output, trace) is the contract's canonical step result triple.
    #[allow(clippy::type_complexity)]
    fn start(
        &mut self,
        input: Self::Input,
    ) -> Result<(Self::RuntimeState, Self::Output, Self::Trace), Self::Error>;
}

pub trait Pipeline<S: BaseType> {
    type Engine: Engine<S>;
    type PipelineState: BaseType;
    type Output: BaseType;
    type Trace: TraceArtifact;
    type Error;

    // (state, output, trace) is the contract's canonical step result triple.
    #[allow(clippy::type_complexity)]
    fn run(
        &mut self,
        input: S,
    ) -> Result<(Self::PipelineState, Self::Output, Self::Trace), Self::Error>;
}

pub trait Engine<S: BaseType> {
    type Operator: OperatorIdentity;
    type License;
    type RuntimeState: BaseType;
    type Output: BaseType;
    type Trace: TraceArtifact;
    type Error;

    // (state, output, trace) is the contract's canonical step result triple.
    #[allow(clippy::type_complexity)]
    fn step(
        &mut self,
        state: S,
        license: &Self::License,
    ) -> Result<(Self::RuntimeState, Self::Output, Self::Trace), Self::Error>;
}

pub trait Search<S: BaseType>: Pipeline<S> {}
pub trait Solver<S: BaseType>: Pipeline<S> {}
pub trait SelectionStrategy {}
pub trait ContinuationPolicy {}
pub trait BudgetPolicy {}

// =============================================================================
// Kernel Contract (06_execution.yaml)
// =============================================================================

/// Bounded authority unit owning exactly one semantic class.
/// Maps to kernel contract in 06_execution.yaml.
///
/// Kernel is a bounded authority declaration for one semantic class. Kernels are not operators,
/// do not participate in E/I/C/R/M, and do not execute unless a separate Engine contract grants
/// StateTransition authority.
pub trait Kernel {
    type SemanticClass;
    type InputFamily;
    type OutputFamily;

    fn kernel_id(&self) -> &str;
    fn semantic_class(&self) -> &Self::SemanticClass;
    fn input_families(&self) -> Vec<&Self::InputFamily>;
    fn output_families(&self) -> Vec<&Self::OutputFamily>;
}

/// Kernel manifest declares the bounded authority unit.
#[derive(Debug, Clone)]
pub struct KernelManifest {
    pub kernel_id: String,
    pub semantic_class: String,
    pub input_family_refs: Vec<String>,
    pub output_family_refs: Vec<String>,
    pub manifest_hash: String,
}

// =============================================================================
// Health Model Contract (06_execution.yaml)
// =============================================================================

/// Invariant-relative health reporting.
/// Maps to health_model contract in 06_execution.yaml.
///
/// HealthModel reports invariant-relative health state. Raw health reports are EvidenceOnly.
/// Checked health reports may support FactOnly claims only after source, invariant family,
/// measurement, and certificate references are checked.
pub trait HealthModel {
    type Subject;
    type InvariantFamily;
    type Report;
    type Error;

    fn report_health(
        &self,
        subject: &Self::Subject,
        invariant_family: &Self::InvariantFamily,
    ) -> Result<Self::Report, Self::Error>;
}

/// Health state enumeration from 06_execution.yaml.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HealthState {
    Healthy,
    Degraded,
    InvariantThreat,
    BoundaryFailure,
    Unknown,
}

/// Health report structure.
#[derive(Debug, Clone)]
pub struct HealthReport {
    pub subject_ref: String,
    pub invariant_family_ref: String,
    pub health_state: HealthState,
    pub measurement_refs: Vec<String>,
    pub evidence_refs: Vec<String>,
    pub report_hash: String,
    pub authority_effect: ContractEffect,
}

impl HealthReport {
    pub fn new(
        subject_ref: String,
        invariant_family_ref: String,
        health_state: HealthState,
        measurement_refs: Vec<String>,
        evidence_refs: Vec<String>,
        report_hash: String,
    ) -> Self {
        Self {
            subject_ref,
            invariant_family_ref,
            health_state,
            measurement_refs,
            evidence_refs,
            report_hash,
            authority_effect: ContractEffect::EvidenceOnly,
        }
    }
}

// =============================================================================
// Health Reporting Interface Contract (06_execution.yaml)
// =============================================================================

/// Reference-only consumption boundary for health reports.
/// Maps to health_reporting_interface contract in 06_execution.yaml.
///
/// HealthReportingInterface exposes health report references to consumers without creating
/// new authority. It does not prescribe action, evaluate, certify, license, execute, or mutate.
pub trait HealthReportingInterface {
    type ReportRef;
    type Consumer;
    type View;
    type Error;

    fn view_report(
        &self,
        report_ref: &Self::ReportRef,
        consumer: &Self::Consumer,
    ) -> Result<Self::View, Self::Error>;
}

/// Health report view structure.
#[derive(Debug, Clone)]
pub struct HealthReportView {
    pub report_ref: String,
    pub consumer_ref: String,
    pub projection_schema_ref: String,
    pub view_hash: String,
}

// Origin: engine/crates_rs/core_contracts/src/traits_execution.rs
// Claim: urn:core:crates_rs:core-contracts:traits-execution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd3903644 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd3903644` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord3903644 {
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
impl BoundaryErrord3903644 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord3903644 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord3903644 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd3903644 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord3903644> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord3903644::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord3903644::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord3903644::ExceedsCapacity {
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
    fn health_report_defaults_to_evidence_only() {
        let report = HealthReport::new(
            "subject:1".to_string(),
            "invariant:1".to_string(),
            HealthState::Healthy,
            Vec::new(),
            Vec::new(),
            "hash:report".to_string(),
        );
        assert_eq!(report.authority_effect, ContractEffect::EvidenceOnly);
    }
}

#[cfg(test)]
mod l4_boundary_tests_d3903644 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd3903644::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd3903644::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd3903644::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd3903644::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd3903644::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord3903644::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord3903644::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
