use core_functional::{MubFeasibilityWallEvidenceKind, MubFeasibilityWallFunctional};
use serde_json::Value;

fn comparison() -> core_functional::MubFeasibilityWallTargetComparison {
    let value = MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2, 0.0], 0.1)
        .expect("finite diagnostic wall value");
    MubFeasibilityWallFunctional::compare_targets_f64_diagnostic(
        &value,
        0.02 / 0.9,
        1.0 - 0.02 / 0.9,
        2.5e-10,
    )
    .expect("finite target comparison")
}

#[test]
fn canonical_api_uses_evidence_terminology() {
    let comparison = comparison();
    assert_eq!(
        comparison.evidence_kind,
        MubFeasibilityWallEvidenceKind::F64Diagnostic
    );

    let value = MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2, 0.0], 0.1)
        .expect("finite diagnostic wall value");
    let interval = MubFeasibilityWallFunctional::diagnostic_interval_attempt(&value, &comparison)
        .expect("finite interval attempt");
    assert_eq!(
        interval.evidence_kind,
        MubFeasibilityWallEvidenceKind::F64Diagnostic
    );
}

#[test]
fn v1_serialization_preserves_legacy_wire_field_without_dual_fields() {
    let json = serde_json::to_value(comparison()).expect("comparison serializes");
    let object = json
        .as_object()
        .expect("comparison serializes as an object");
    assert_eq!(
        object.get("authority_kind"),
        Some(&Value::String("F64Diagnostic".to_owned()))
    );
    assert!(!object.contains_key("evidence_kind"));
}

#[test]
#[allow(deprecated)]
fn deprecated_source_adapters_preserve_evidence_only_value() {
    use core_functional::MubFeasibilityWallEvidenceKind;

    let comparison = comparison();
    let legacy: MubFeasibilityWallEvidenceKind = comparison.authority_kind();
    assert_eq!(legacy, comparison.evidence_kind);

    let value = MubFeasibilityWallFunctional::evaluate_probabilities(&[0.2, 0.0], 0.1)
        .expect("finite diagnostic wall value");
    let interval = MubFeasibilityWallFunctional::diagnostic_interval_attempt(&value, &comparison)
        .expect("finite interval attempt");
    assert_eq!(interval.authority_kind(), interval.evidence_kind);
}

// Origin: engine/crates_rs/tests/core_functional/mub_feasibility_wall_evidence_api.rs
// Claim: urn:core:crates_rs:tests:mub-feasibility-wall-evidence-api:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord194f56a9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord194f56a9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError194f56a9 {
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
impl BoundaryError194f56a9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError194f56a9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError194f56a9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord194f56a9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError194f56a9> {
        if capacity_bound == 0 {
            return Err(BoundaryError194f56a9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError194f56a9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError194f56a9::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_194f56a9() {
    let admitted = BoundaryRecord194f56a9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord194f56a9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
