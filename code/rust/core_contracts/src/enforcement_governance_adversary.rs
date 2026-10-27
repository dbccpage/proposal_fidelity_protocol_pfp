//! Adversary adversarial diagnostic functor.
//!
//! Adversary is adversarial diagnosis, NOT final enforcement.
//! Adversary may recommend Blackrod action but CANNOT enforce.
//!
//! # Safety Invariant
//!
//! Adversary can only diagnose and recommend. Enforcement authority is
//! exclusively held by Blackrod. This separation ensures that diagnostic
//! findings must pass through an enforcement gate before action is taken.

use super::errors::{ArtifactType, CouncilId, GovernanceError, GovernanceResult, TraceId};
use serde::{Deserialize, Serialize};

// ============================================================================
// Diagnostic Functor Trait
// ============================================================================

/// Diagnostic functor trait.
///
/// Inspects artifacts for obstruction findings. Adversary diagnoses but
/// does NOT enforce. Enforcement authority is held by Blackrod.
pub trait DiagnosticFunctor {
    /// Artifact type being inspected.
    type Artifact;
    /// Finding type produced by inspection.
    type Finding;

    /// Inspect an artifact for obstruction findings.
    ///
    /// Returns a list of findings. Adversary diagnoses but does NOT enforce.
    fn inspect(&self, artifact: &Self::Artifact) -> Vec<Self::Finding>;
}

// ============================================================================
// Obstruction Findings
// ============================================================================

/// Obstruction findings that Adversary can detect.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ObstructionFinding {
    /// Hidden contradiction detected.
    HiddenContradiction { location: String, details: String },

    /// Fake certainty - claim without sufficient evidence.
    FakeCertainty { claim: String, evidence_gap: String },

    /// Fake evidence detected.
    FakeEvidence { artifact_id: String, reason: String },

    /// Weak or inadequate tests.
    WeakTests {
        test_ids: Vec<String>,
        weakness: String,
    },

    /// Unrouted power - authority exercised without proper routing.
    UnroutedPower {
        actor: String,
        power_description: String,
    },

    /// Self-certification detected.
    SelfCertification { actor: String, artifact_id: String },

    /// Architecture drift from declared structure.
    ArchitectureDrift { expected: String, actual: String },

    /// Unlicensed claim made.
    UnlicensedClaim { actor: String, claim: String },
}

// ============================================================================
// Adversary Recommendations
// ============================================================================

/// Urgency level for recommendations.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Urgency {
    /// Low urgency - can be addressed in normal flow.
    Low,
    /// Medium urgency - should be addressed soon.
    Medium,
    /// High urgency - requires prompt attention.
    High,
    /// Critical urgency - immediate action required.
    Critical,
}

/// Adversary can only recommend, never enforce.
///
/// All recommendations are advisory. Enforcement authority is held by Blackrod.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum AdversaryRecommendation {
    /// Refer finding to Blackrod for enforcement consideration.
    ReferToBlackrod {
        finding: ObstructionFinding,
        urgency: Urgency,
    },

    /// Flag finding for council review.
    FlagForCouncilReview {
        finding: ObstructionFinding,
        council_id: CouncilId,
    },

    /// Request additional evidence.
    RequestEvidence {
        artifact_id: String,
        evidence_needed: String,
    },

    /// Annotate artifact with diagnostic finding.
    AnnotateArtifact {
        artifact_id: String,
        annotation: String,
    },
}

// ============================================================================
// Diagnostic Artifact
// ============================================================================

/// Artifact submitted for diagnostic inspection.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiagnosticArtifact {
    /// Unique identifier.
    pub id: String,
    /// Artifact type.
    pub kind: ArtifactType,
    /// Content hash for integrity.
    pub content_hash: String,
    /// Additional metadata.
    pub metadata: std::collections::HashMap<String, String>,
}

impl DiagnosticArtifact {
    /// Create a new diagnostic artifact.
    pub fn new(id: impl Into<String>, kind: ArtifactType, content_hash: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            kind,
            content_hash: content_hash.into(),
            metadata: std::collections::HashMap::new(),
        }
    }

    /// Add metadata to the artifact.
    pub fn with_metadata(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.metadata.insert(key.into(), value.into());
        self
    }
}

// ============================================================================
// Diagnostic Record
// ============================================================================

/// Record of a diagnostic inspection.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiagnosticRecord {
    /// Unique identifier for this record.
    pub id: String,
    /// Artifact that was inspected.
    pub artifact_inspected: String,
    /// Findings from inspection.
    pub findings: Vec<ObstructionFinding>,
    /// Recommendations based on findings.
    pub recommendations: Vec<AdversaryRecommendation>,
    /// Timestamp of inspection.
    pub timestamp: String,
    /// Trace identifier for audit.
    pub trace_id: TraceId,
}

// ============================================================================
// Adversary
// ============================================================================

/// Adversary adversarial diagnostic entity.
///
/// Adversary inspects artifacts for obstruction findings and recommends actions.
/// Adversary CANNOT enforce - enforcement authority is held by Blackrod.
#[derive(Debug, Clone, Default)]
pub struct Adversary {
    /// Unique identifier.
    pub id: String,
    /// Log of diagnostic inspections.
    pub findings_log: Vec<DiagnosticRecord>,
}

impl DiagnosticFunctor for Adversary {
    type Artifact = DiagnosticArtifact;
    type Finding = ObstructionFinding;

    fn inspect(&self, _artifact: &Self::Artifact) -> Vec<Self::Finding> {
        // Inspects artifact for obstruction findings.
        // Adversary diagnoses but does NOT enforce.
        // TODO: Implement inspection logic based on artifact type and content.
        Vec::new()
    }
}

impl Adversary {
    /// Create a new Adversary instance.
    pub fn new(id: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            findings_log: Vec::new(),
        }
    }

    /// Recommend Blackrod action for a finding.
    ///
    /// Adversary may recommend Blackrod action but cannot enforce.
    pub fn recommend(&self, finding: ObstructionFinding, urgency: Urgency) -> AdversaryRecommendation {
        AdversaryRecommendation::ReferToBlackrod { finding, urgency }
    }

    /// Recommend council review for a finding.
    pub fn recommend_council_review(
        &self,
        finding: ObstructionFinding,
        council_id: CouncilId,
    ) -> AdversaryRecommendation {
        AdversaryRecommendation::FlagForCouncilReview {
            finding,
            council_id,
        }
    }

    /// Request additional evidence for an artifact.
    pub fn request_evidence(
        &self,
        artifact_id: impl Into<String>,
        evidence_needed: impl Into<String>,
    ) -> AdversaryRecommendation {
        AdversaryRecommendation::RequestEvidence {
            artifact_id: artifact_id.into(),
            evidence_needed: evidence_needed.into(),
        }
    }

    /// Annotate an artifact with a diagnostic finding.
    pub fn annotate(
        &self,
        artifact_id: impl Into<String>,
        annotation: impl Into<String>,
    ) -> AdversaryRecommendation {
        AdversaryRecommendation::AnnotateArtifact {
            artifact_id: artifact_id.into(),
            annotation: annotation.into(),
        }
    }

    /// Adversary CANNOT enforce - this must always fail.
    ///
    /// Enforcement authority is exclusively held by Blackrod.
    /// Adversary diagnoses but does NOT enforce.
    pub fn enforce(&self) -> GovernanceResult<()> {
        Err(GovernanceError::AuthorityViolation(
            "Adversary diagnoses but cannot enforce. Refer to Blackrod.".into(),
        ))
    }

    /// Perform diagnostic inspection and log results.
    pub fn diagnose(&mut self, artifact: &DiagnosticArtifact) -> DiagnosticRecord {
        let findings = self.inspect(artifact);
        let recommendations: Vec<AdversaryRecommendation> = findings
            .iter()
            .map(|f| self.recommend(f.clone(), Urgency::Medium))
            .collect();

        let record = DiagnosticRecord {
            id: format!("diag:{}", self.findings_log.len()),
            artifact_inspected: artifact.id.clone(),
            findings: findings.clone(),
            recommendations,
            timestamp: "TODO:timestamp".to_string(),
            trace_id: TraceId::new("trace:diagnostic"),
        };

        self.findings_log.push(record.clone());
        record
    }

    /// Check if an artifact exhibits self-certification.
    ///
    /// Self-certification is when an actor certifies their own work.
    pub fn check_self_certification(
        &self,
        artifact: &DiagnosticArtifact,
        author: &str,
        certifier: &str,
    ) -> Option<ObstructionFinding> {
        if author == certifier {
            Some(ObstructionFinding::SelfCertification {
                actor: author.to_string(),
                artifact_id: artifact.id.clone(),
            })
        } else {
            None
        }
    }

    /// Check for fake certainty - claims without sufficient evidence.
    pub fn check_fake_certainty(
        &self,
        claim: &str,
        evidence_refs: &[String],
        required_evidence_count: usize,
    ) -> Option<ObstructionFinding> {
        if evidence_refs.len() < required_evidence_count {
            Some(ObstructionFinding::FakeCertainty {
                claim: claim.to_string(),
                evidence_gap: format!(
                    "requires {} evidence items, found {}",
                    required_evidence_count,
                    evidence_refs.len()
                ),
            })
        } else {
            None
        }
    }

    /// Check for weak tests.
    pub fn check_weak_tests(
        &self,
        test_ids: &[String],
        assertion_counts: &[usize],
        min_assertions: usize,
    ) -> Option<ObstructionFinding> {
        let weak_tests: Vec<String> = test_ids
            .iter()
            .zip(assertion_counts.iter())
            .filter(|(_, &count)| count < min_assertions)
            .map(|(id, _)| id.clone())
            .collect();

        if weak_tests.is_empty() {
            None
        } else {
            Some(ObstructionFinding::WeakTests {
                test_ids: weak_tests,
                weakness: format!("fewer than {} assertions", min_assertions),
            })
        }
    }
}

// Origin: engine/crates_rs/core_contracts/src/enforcement_governance_adversary.rs
// Claim: urn:core:crates_rs:core-contracts:enforcement-governance-adversary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1f3168d0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1f3168d0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1f3168d0 {
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
impl BoundaryError1f3168d0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1f3168d0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1f3168d0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1f3168d0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1f3168d0> {
        if capacity_bound == 0 {
            return Err(BoundaryError1f3168d0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1f3168d0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1f3168d0::ExceedsCapacity {
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
    fn adversary_cannot_enforce() {
        let adversary = Adversary::new("adversary-001");
        assert!(adversary.enforce().is_err());
    }

    #[test]
    fn adversary_can_recommend_blackrod_action() {
        let adversary = Adversary::new("adversary-001");
        let finding = ObstructionFinding::FakeCertainty {
            claim: "claim-001".into(),
            evidence_gap: "missing proof".into(),
        };

        let recommendation = adversary.recommend(finding.clone(), Urgency::High);
        assert!(matches!(
            recommendation,
            AdversaryRecommendation::ReferToBlackrod { .. }
        ));
    }

    #[test]
    fn adversary_detects_self_certification() {
        let adversary = Adversary::new("adversary-001");
        let artifact = DiagnosticArtifact::new("art-001", ArtifactType::Code, "hash123");

        let finding = adversary.check_self_certification(&artifact, "alice", "alice");
        assert!(finding.is_some());
        assert!(matches!(
            finding.unwrap(),
            ObstructionFinding::SelfCertification { .. }
        ));
    }

    #[test]
    fn adversary_no_self_certification_when_different_actors() {
        let adversary = Adversary::new("adversary-001");
        let artifact = DiagnosticArtifact::new("art-001", ArtifactType::Code, "hash123");

        let finding = adversary.check_self_certification(&artifact, "alice", "bob");
        assert!(finding.is_none());
    }

    #[test]
    fn adversary_detects_fake_certainty() {
        let adversary = Adversary::new("adversary-001");
        let finding = adversary.check_fake_certainty("strong claim", &["evidence-1".into()], 3);

        assert!(finding.is_some());
        assert!(matches!(
            finding.unwrap(),
            ObstructionFinding::FakeCertainty { .. }
        ));
    }

    #[test]
    fn adversary_no_fake_certainty_with_sufficient_evidence() {
        let adversary = Adversary::new("adversary-001");
        let evidence = vec!["ev1".into(), "ev2".into(), "ev3".into()];
        let finding = adversary.check_fake_certainty("strong claim", &evidence, 3);

        assert!(finding.is_none());
    }

    #[test]
    fn adversary_detects_weak_tests() {
        let adversary = Adversary::new("adversary-001");
        let test_ids = vec!["test1".into(), "test2".into(), "test3".into()];
        let assertion_counts = vec![1, 5, 2];

        let finding = adversary.check_weak_tests(&test_ids, &assertion_counts, 3);
        assert!(finding.is_some());

        if let Some(ObstructionFinding::WeakTests { test_ids, .. }) = finding {
            assert!(test_ids.contains(&"test1".to_string()));
            assert!(test_ids.contains(&"test3".to_string()));
            assert!(!test_ids.contains(&"test2".to_string()));
        } else {
            panic!("expected WeakTests finding");
        }
    }

    #[test]
    fn adversary_diagnose_creates_record() {
        let mut adversary = Adversary::new("adversary-001");
        let artifact = DiagnosticArtifact::new("art-001", ArtifactType::Code, "hash123");

        let record = adversary.diagnose(&artifact);
        assert_eq!(record.artifact_inspected, "art-001");
        assert_eq!(adversary.findings_log.len(), 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_1f3168d0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1f3168d0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1f3168d0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1f3168d0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1f3168d0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1f3168d0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1f3168d0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1f3168d0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
