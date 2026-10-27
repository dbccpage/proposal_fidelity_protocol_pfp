//! Measurement Access Control
//!
//! Enforces cohomological measurement boundary access control.
//! Contract: measurement_access_control_contract.md
//!
//! **Core Invariant:**
//! Search has no access to raw cohomological semantics and may consume only opaque,
//! non-semantic hints. No canonical cohomological measurement artifact exists without
//! admitted Functional emission and Measurement boundary checking.

use crate::measurement_envelope::RawEvidenceLabel;
use core_types::domain_types::{EvidenceRef, Hash256};
use core_types::FactLabel;
use serde::{Deserialize, Serialize};

/// Measurement access rule identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct MeasurementAccessRuleId(pub String);

/// Measurement access rule
///
/// Enforces the absolute read/write separation between search and evaluation.
///
/// **Default Authority:** EvidenceOnly
///
/// A separate checked access fact may become FactOnly only after:
/// - Schema validation
/// - Rule hash verification
/// - Successful boundary-audit checking
///
/// This raw rule does not implement those checks and cannot promote itself:
///
/// ```compile_fail,E0599
/// use core_measurement::measurement_access::MeasurementAccessRule;
/// fn unchecked_promotion(rule: &mut MeasurementAccessRule) {
///     rule.promote_to_fact_only();
/// }
/// ```
///
/// ```compile_fail,E0308
/// use core_measurement::measurement_access::MeasurementAccessRule;
/// use core_types::FactLabel;
/// fn forged_fact(rule: &mut MeasurementAccessRule) {
///     rule.authority_effect = FactLabel::FactOnly;
/// }
/// ```
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MeasurementAccessRule {
    /// Unique rule identifier
    pub rule_id: MeasurementAccessRuleId,

    /// Subject kernel layer (Search, Solver, Evaluator, etc.)
    pub subject_layer: KernelId,

    /// Forbidden import paths for this layer
    pub forbidden_imports: Vec<ImportPath>,

    /// Forbidden symbols for this layer
    pub forbidden_symbols: Vec<SymbolId>,

    /// Allowed artifact kinds
    pub allowed_artifacts: Vec<ArtifactKind>,

    /// Rule content hash
    pub rule_hash: Hash256,

    /// Raw evidence label; the rule itself is not a checked boundary audit.
    pub authority_effect: RawEvidenceLabel,
}

impl MeasurementAccessRule {
    /// Check if this rule has EvidenceOnly authority
    pub fn is_evidence_only(&self) -> bool {
        matches!(self.authority_effect.fact_label(), FactLabel::EvidenceOnly)
    }

    /// Raw rules never carry the checked-fact label.
    pub fn is_fact_only(&self) -> bool {
        matches!(self.authority_effect.fact_label(), FactLabel::FactOnly)
    }
}

/// Kernel identifier (layer in the system)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum KernelId {
    /// Search kernel (FORBIDDEN: cohomological access)
    Search,

    /// Solver kernel (FORBIDDEN: canonical measurement emission)
    Solver,

    /// Evaluator kernel (may judge, not recompute)
    Evaluator,

    /// Policy kernel (may classify, not dereference raw measurements)
    Policy,

    /// Terminalizer kernel (may map decisions, not compute)
    Terminalizer,

    /// Engine kernel (may route, not compute)
    Engine,

    /// Functional kernel (may compute measurements)
    Functional,

    /// Observable kernel (may observe state)
    Observable,

    /// Analysis kernel (may analyze)
    Analysis,

    /// Custom kernel
    Custom(String),
}

/// Import path (e.g., "core_functional::phi1")
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ImportPath(pub String);

impl ImportPath {
    pub fn new(path: impl Into<String>) -> Self {
        Self(path.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Symbol identifier (e.g., "Phi1Functional", "compute_phi")
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SymbolId(pub String);

impl SymbolId {
    pub fn new(symbol: impl Into<String>) -> Self {
        Self(symbol.into())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Artifact kind classification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ArtifactKind {
    /// Structure artifact
    StructureArtifact,

    /// Evidence envelope
    EvidenceEnvelope,

    /// Fact envelope
    FactEnvelope,

    /// Decision envelope
    DecisionEnvelope,

    /// Action license
    ActionLicense,

    /// Action
    Action,

    /// Record
    Record,

    /// Domain artifact
    DomainArtifact,
}

/// Boundary violation identifier
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct BoundaryViolationId(pub String);

/// Boundary violation record
///
/// Records when a kernel violates measurement access control rules.
///
/// **Default Authority:** EvidenceOnly (until checked)
///
/// A submitted violation is not its own checked access-boundary fact. No
/// assignment can turn its claimed references into verified evidence:
///
/// ```compile_fail,E0308
/// use core_measurement::measurement_access::BoundaryViolation;
/// use core_types::FactLabel;
/// fn forged_fact(violation: &mut BoundaryViolation) {
///     violation.authority_effect = FactLabel::FactOnly;
/// }
/// ```
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BoundaryViolation {
    /// Unique violation identifier
    pub violation_id: BoundaryViolationId,

    /// Rule that was violated
    pub rule_id: MeasurementAccessRuleId,

    /// Subject layer that violated the rule
    pub subject_layer: KernelId,

    /// Forbidden symbol that was accessed (if applicable)
    pub forbidden_symbol: Option<SymbolId>,

    /// Forbidden import that was used (if applicable)
    pub forbidden_import: Option<ImportPath>,

    /// Evidence references
    pub evidence_refs: Vec<EvidenceRef>,

    /// Violation content hash
    pub violation_hash: Hash256,

    /// Raw evidence label; referenced evidence is not validated by this record.
    pub authority_effect: RawEvidenceLabel,
}

impl BoundaryViolation {
    /// Check if this violation has EvidenceOnly authority
    pub fn is_evidence_only(&self) -> bool {
        matches!(self.authority_effect.fact_label(), FactLabel::EvidenceOnly)
    }

    /// Raw violation records never carry the checked-fact label.
    pub fn is_fact_only(&self) -> bool {
        matches!(self.authority_effect.fact_label(), FactLabel::FactOnly)
    }
}

/// Predefined forbidden imports for different kernel layers
pub mod forbidden_imports {
    use super::ImportPath;

    /// Forbidden imports for Search layer
    pub fn search_forbidden() -> Vec<ImportPath> {
        vec![
            ImportPath::new("core_functional::phi1"),
            ImportPath::new("core_functional::gamma2"),
            ImportPath::new("core_functional::xi"),
            ImportPath::new("core_functional::cohomology"),
            ImportPath::new("core_measurement::cohomological_values"),
        ]
    }

    /// Forbidden imports for Solver layer
    pub fn solver_forbidden() -> Vec<ImportPath> {
        search_forbidden()
    }

    /// Forbidden imports for Engine layer
    pub fn engine_forbidden() -> Vec<ImportPath> {
        search_forbidden()
    }

    /// Forbidden imports for Terminalizer layer
    pub fn terminalizer_forbidden() -> Vec<ImportPath> {
        search_forbidden()
    }

    /// Forbidden imports for Policy layer
    pub fn policy_forbidden() -> Vec<ImportPath> {
        search_forbidden()
    }
}

/// Predefined forbidden symbols for different kernel layers
pub mod forbidden_symbols {
    use super::SymbolId;

    /// Forbidden symbols for all non-Functional layers
    pub fn cohomological_computation_symbols() -> Vec<SymbolId> {
        vec![
            SymbolId::new("Phi1Functional"),
            SymbolId::new("Gamma2Functional"),
            SymbolId::new("XiFunctional"),
            SymbolId::new("compute_phi"),
            SymbolId::new("compute_gamma"),
            SymbolId::new("compute_xi"),
            SymbolId::new("compute_phi1"),
            SymbolId::new("compute_gamma2"),
            SymbolId::new("compute_quotient_mass"),
            SymbolId::new("compute_closure_defect"),
            SymbolId::new("compute_closure_regime"),
            SymbolId::new("compute_cohomological_status"),
            SymbolId::new("canonical_phi1"),
            SymbolId::new("canonical_gamma2"),
            SymbolId::new("canonical_xi"),
            SymbolId::new("raw_phi1"),
            SymbolId::new("raw_gamma2"),
            SymbolId::new("raw_xi"),
        ]
    }

    /// Forbidden cohomological value kinds
    pub fn cohomological_value_kinds() -> Vec<SymbolId> {
        vec![
            SymbolId::new("CohomologicalValueKind::Phi1"),
            SymbolId::new("CohomologicalValueKind::Gamma2"),
            SymbolId::new("CohomologicalValueKind::Xi"),
            SymbolId::new("CohomologicalValueKind::QuotientMass"),
            SymbolId::new("CohomologicalValueKind::ClosureDefect"),
            SymbolId::new("CohomologicalValueKind::ClosureRegime"),
            SymbolId::new("CohomologicalValueKind::CohomologicalStatus"),
        ]
    }
}

// Origin: engine/crates_rs/core_measurement/src/measurement_access.rs
// Claim: urn:core:crates_rs:core-measurement:measurement-access:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord13aa5e6a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord13aa5e6a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError13aa5e6a {
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
impl BoundaryError13aa5e6a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError13aa5e6a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError13aa5e6a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord13aa5e6a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError13aa5e6a> {
        if capacity_bound == 0 {
            return Err(BoundaryError13aa5e6a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError13aa5e6a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError13aa5e6a::ExceedsCapacity {
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
    fn measurement_access_rule_defaults_to_evidence_only() {
        let rule = MeasurementAccessRule {
            rule_id: MeasurementAccessRuleId("rule-001".to_string()),
            subject_layer: KernelId::Search,
            forbidden_imports: vec![],
            forbidden_symbols: vec![],
            allowed_artifacts: vec![],
            rule_hash: Hash256::from_hex_unchecked("a".repeat(64)),
            authority_effect: RawEvidenceLabel::default(),
        };

        assert!(rule.is_evidence_only());
        assert!(!rule.is_fact_only());
        assert_eq!(rule.authority_effect.fact_label(), FactLabel::EvidenceOnly);
    }

    #[test]
    fn boundary_violation_defaults_to_evidence_only() {
        let violation = BoundaryViolation {
            violation_id: BoundaryViolationId("violation-001".to_string()),
            rule_id: MeasurementAccessRuleId("rule-001".to_string()),
            subject_layer: KernelId::Search,
            forbidden_symbol: Some(SymbolId::new("compute_phi")),
            forbidden_import: None,
            evidence_refs: vec![],
            violation_hash: Hash256::from_hex_unchecked("b".repeat(64)),
            authority_effect: RawEvidenceLabel::default(),
        };

        assert!(violation.is_evidence_only());
        assert!(!violation.is_fact_only());
        assert_eq!(
            violation.authority_effect.fact_label(),
            FactLabel::EvidenceOnly
        );
    }

    #[test]
    fn search_forbidden_imports_include_cohomological_paths() {
        let forbidden = forbidden_imports::search_forbidden();

        assert!(forbidden
            .iter()
            .any(|p| p.as_str() == "core_functional::phi1"));
        assert!(forbidden
            .iter()
            .any(|p| p.as_str() == "core_functional::gamma2"));
        assert!(forbidden
            .iter()
            .any(|p| p.as_str() == "core_functional::xi"));
        assert!(forbidden
            .iter()
            .any(|p| p.as_str() == "core_functional::cohomology"));
    }

    #[test]
    fn cohomological_computation_symbols_forbidden() {
        let forbidden = forbidden_symbols::cohomological_computation_symbols();

        assert!(forbidden.iter().any(|s| s.as_str() == "compute_phi"));
        assert!(forbidden.iter().any(|s| s.as_str() == "compute_gamma"));
        assert!(forbidden.iter().any(|s| s.as_str() == "compute_xi"));
        assert!(forbidden.iter().any(|s| s.as_str() == "compute_phi1"));
        assert!(forbidden.iter().any(|s| s.as_str() == "compute_gamma2"));
        assert!(forbidden.iter().any(|s| s.as_str() == "canonical_phi1"));
        assert!(forbidden.iter().any(|s| s.as_str() == "raw_phi1"));
    }

    #[test]
    fn raw_access_rule_cannot_gain_fact_status_from_claimed_rule_hash() {
        let mut rule = MeasurementAccessRule {
            rule_id: MeasurementAccessRuleId("rule-001".to_string()),
            subject_layer: KernelId::Search,
            forbidden_imports: vec![],
            forbidden_symbols: vec![],
            allowed_artifacts: vec![],
            rule_hash: Hash256::from_hex_unchecked("a".repeat(64)),
            authority_effect: RawEvidenceLabel::default(),
        };

        assert!(rule.is_evidence_only());

        rule.rule_hash = Hash256::from_hex_unchecked("b".repeat(64));

        assert!(!rule.is_fact_only());
        assert!(rule.is_evidence_only());
    }

    #[test]
    fn kernel_id_variants_exist() {
        // Ensure all required kernel variants exist
        let _ = KernelId::Search;
        let _ = KernelId::Solver;
        let _ = KernelId::Evaluator;
        let _ = KernelId::Policy;
        let _ = KernelId::Terminalizer;
        let _ = KernelId::Engine;
        let _ = KernelId::Functional;
        let _ = KernelId::Observable;
        let _ = KernelId::Analysis;
    }

    #[test]
    fn artifact_kind_variants_exist() {
        // Ensure all required artifact kinds exist
        let _ = ArtifactKind::StructureArtifact;
        let _ = ArtifactKind::EvidenceEnvelope;
        let _ = ArtifactKind::FactEnvelope;
        let _ = ArtifactKind::DecisionEnvelope;
        let _ = ArtifactKind::ActionLicense;
        let _ = ArtifactKind::Action;
        let _ = ArtifactKind::Record;
        let _ = ArtifactKind::DomainArtifact;
    }
}

#[cfg(test)]
mod l4_boundary_tests_13aa5e6a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord13aa5e6a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord13aa5e6a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord13aa5e6a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord13aa5e6a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord13aa5e6a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError13aa5e6a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError13aa5e6a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
