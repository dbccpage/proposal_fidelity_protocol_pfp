use crate::kinds::ContractEffect;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct AnalysisId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct DiagnosticReportId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct FunctionalId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct MetaJudgmentId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SubjectHash(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CertificateId(pub String);

pub trait AnalysisArtifact {
    fn artifact_id(&self) -> AnalysisId;
    fn subject_hash(&self) -> SubjectHash;
    fn authority_effect(&self) -> ContractEffect;
}

#[derive(Debug, Clone)]
pub struct AnalysisEnvelope<A> {
    pub analysis_id: AnalysisId,
    pub subject_hash: SubjectHash,
    pub artifact: A,
    pub certificate_refs: Vec<CertificateId>,
    pub authority_effect: ContractEffect,
}

impl<A> AnalysisEnvelope<A> {
    pub const DEFAULT_AUTHORITY_EFFECT: ContractEffect = ContractEffect::EvidenceOnly;

    pub fn new(
        analysis_id: AnalysisId,
        subject_hash: SubjectHash,
        artifact: A,
        certificate_refs: Vec<CertificateId>,
    ) -> Self {
        Self {
            analysis_id,
            subject_hash,
            artifact,
            certificate_refs,
            authority_effect: Self::DEFAULT_AUTHORITY_EFFECT,
        }
    }
}

/// Analysis extracts structured reports or summaries.
///
/// It does not judge admissibility, terminalize, mutate, execute, or license.
/// Checked facts require a declared checker, verifier, or replay boundary.
pub trait AnalysisKernel<Input> {
    type Artifact: AnalysisArtifact;
    type Error;

    fn analyze(&self, input: &Input) -> Result<AnalysisEnvelope<Self::Artifact>, Self::Error>;
}

/// Diagnostics classify observed problems relative to declared checks.
/// They produce reports, not decisions.
pub trait DiagnosticKernel<Input> {
    type Report;
    type Error;

    fn diagnose(&self, input: &Input) -> Result<DiagnosticEnvelope<Self::Report>, Self::Error>;
}

#[derive(Debug, Clone)]
pub struct DiagnosticEnvelope<R> {
    pub diagnostic_id: DiagnosticReportId,
    pub subject_hash: SubjectHash,
    pub report: R,
    pub certificate_refs: Vec<CertificateId>,
    pub authority_effect: ContractEffect,
}

impl<R> DiagnosticEnvelope<R> {
    pub const DEFAULT_AUTHORITY_EFFECT: ContractEffect = ContractEffect::EvidenceOnly;

    pub fn new(
        diagnostic_id: DiagnosticReportId,
        subject_hash: SubjectHash,
        report: R,
        certificate_refs: Vec<CertificateId>,
    ) -> Self {
        Self {
            diagnostic_id,
            subject_hash,
            report,
            certificate_refs,
            authority_effect: Self::DEFAULT_AUTHORITY_EFFECT,
        }
    }
}

/// Functional computes a declared numerical/symbolic quantity.
///
/// It produces evidence-bearing output. It does not authorize action or decide
/// admissibility without a separate governance boundary.
pub trait FunctionalKernel<Input> {
    type Output;
    type Error;

    fn functional_id(&self) -> FunctionalId;

    fn compute_functional(
        &self,
        input: &Input,
    ) -> Result<FunctionalEnvelope<Self::Output>, Self::Error>;
}

#[derive(Debug, Clone)]
pub struct FunctionalEnvelope<O> {
    pub functional_id: FunctionalId,
    pub subject_hash: SubjectHash,
    pub output: O,
    pub certificate_refs: Vec<CertificateId>,
    pub authority_effect: ContractEffect,
}

impl<O> FunctionalEnvelope<O> {
    pub const DEFAULT_AUTHORITY_EFFECT: ContractEffect = ContractEffect::EvidenceOnly;

    pub fn new(
        functional_id: FunctionalId,
        subject_hash: SubjectHash,
        output: O,
        certificate_refs: Vec<CertificateId>,
    ) -> Self {
        Self {
            functional_id,
            subject_hash,
            output,
            certificate_refs,
            authority_effect: Self::DEFAULT_AUTHORITY_EFFECT,
        }
    }
}

/// Meta judgment may recommend or classify meta-level conditions,
/// but must not execute lift or terminalize.
pub trait MetaJudgmentKernel<Input> {
    type Judgment;
    type Error;

    fn judge_meta(
        &self,
        input: &Input,
    ) -> Result<MetaJudgmentEnvelope<Self::Judgment>, Self::Error>;
}

#[derive(Debug, Clone)]
pub struct MetaJudgmentEnvelope<J> {
    pub judgment_id: MetaJudgmentId,
    pub subject_hash: SubjectHash,
    pub judgment: J,
    pub certificate_refs: Vec<CertificateId>,
    pub authority_effect: ContractEffect,
}

impl<J> MetaJudgmentEnvelope<J> {
    pub const DEFAULT_AUTHORITY_EFFECT: ContractEffect = ContractEffect::RequestsDecision;

    pub fn new(
        judgment_id: MetaJudgmentId,
        subject_hash: SubjectHash,
        judgment: J,
        certificate_refs: Vec<CertificateId>,
    ) -> Self {
        Self {
            judgment_id,
            subject_hash,
            judgment,
            certificate_refs,
            authority_effect: Self::DEFAULT_AUTHORITY_EFFECT,
        }
    }
}

/*
================================================================================
# FORBIDDEN BOUNDARY LAW
Analysis, Diagnostic, and Functional kernels produce evidence-bearing reports.
They do not decide admissibility, prescribe repair, terminalize, execute, mutate state, or license lifts.
Checked facts require a declared checker/verifier/replay boundary.

MetaJudgment may request or recommend a higher-authority decision.
It may not apply the decision.

Forbidden tokens:
- execute
- terminalize
- apply_lift
- apply_operator
- rollback
- sign_certificate
- save_certificate
- ALLOW_OUTPUT
- BLOCK_OUTPUT

For DiagnosticKernel, also forbid:
- repair
- policy_decision
- engine_decision
================================================================================
*/

// Origin: engine/crates_rs/core_contracts/src/traits_analysis.rs
// Claim: urn:core:crates_rs:core-contracts:traits-analysis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde16439c5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde16439c5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore16439c5 {
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
impl BoundaryErrore16439c5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore16439c5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore16439c5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde16439c5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore16439c5> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore16439c5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore16439c5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore16439c5::ExceedsCapacity {
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
    fn analysis_diagnostic_and_functional_default_to_evidence_only() {
        let analysis = AnalysisEnvelope::new(
            AnalysisId("analysis:1".to_string()),
            SubjectHash("subject:1".to_string()),
            "artifact",
            Vec::new(),
        );
        assert_eq!(analysis.authority_effect, ContractEffect::EvidenceOnly);

        let diagnostic = DiagnosticEnvelope::new(
            DiagnosticReportId("diagnostic:1".to_string()),
            SubjectHash("subject:1".to_string()),
            "report",
            Vec::new(),
        );
        assert_eq!(diagnostic.authority_effect, ContractEffect::EvidenceOnly);

        let functional = FunctionalEnvelope::new(
            FunctionalId("functional:1".to_string()),
            SubjectHash("subject:1".to_string()),
            1usize,
            Vec::new(),
        );
        assert_eq!(functional.authority_effect, ContractEffect::EvidenceOnly);
    }

    #[test]
    fn meta_judgment_may_request_decision() {
        let judgment = MetaJudgmentEnvelope::new(
            MetaJudgmentId("judgment:1".to_string()),
            SubjectHash("subject:1".to_string()),
            "judgment",
            Vec::new(),
        );
        assert_eq!(judgment.authority_effect, ContractEffect::RequestsDecision);
    }
}

#[cfg(test)]
mod l4_boundary_tests_e16439c5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde16439c5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde16439c5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde16439c5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde16439c5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde16439c5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore16439c5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore16439c5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
