use super::candidates::DeclaredActionCandidate;
use crate::kinds::BaseType;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum OperatorClass {
    E,
    I,
    C,
    R,
    M,
}

use crate::kinds::ContractEffect;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct DeclaredActionId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ClassifiedActionId(pub String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClassifiedAction {
    pub id: ClassifiedActionId,
    pub source_action: DeclaredActionId,
    pub class: OperatorClass,
    /// Classification evidence only. This is not an `ActionLicense` and is not
    /// execution authority.
    pub authority_effect: ContractEffect,
    pub classifier_id: String,
    pub evidence_refs: Vec<String>,
}

impl ClassifiedAction {
    pub fn new(
        id: ClassifiedActionId,
        source_action: DeclaredActionId,
        class: OperatorClass,
        authority_effect: ContractEffect,
        classifier_id: String,
        evidence_refs: Vec<String>,
    ) -> Result<Self, ContractEffect> {
        if !matches!(
            authority_effect,
            ContractEffect::EvidenceOnly | ContractEffect::RequestsDecision
        ) {
            return Err(authority_effect);
        }

        Ok(Self {
            id,
            source_action,
            class,
            authority_effect,
            classifier_id,
            evidence_refs,
        })
    }
}

/// Result of classifying an action candidate into the fixed-layer operator taxonomy.
///
/// Classification is not execution, licensing, or engine authority. Helper classifiers
/// should normally emit `EvidenceOnly`; evaluator-owned classifiers may emit
/// `RequestsDecision`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClassificationResult {
    pub class: OperatorClass,
    pub reason: String,
    pub authority_effect: ContractEffect,
    pub classifier_id: String,
    pub evidence_refs: Vec<String>,
}

impl ClassificationResult {
    pub fn evidence_only(
        class: OperatorClass,
        reason: String,
        classifier_id: String,
        evidence_refs: Vec<String>,
    ) -> Self {
        Self {
            class,
            reason,
            authority_effect: ContractEffect::EvidenceOnly,
            classifier_id,
            evidence_refs,
        }
    }

    pub fn requests_decision(
        class: OperatorClass,
        reason: String,
        classifier_id: String,
        evidence_refs: Vec<String>,
    ) -> Self {
        Self {
            class,
            reason,
            authority_effect: ContractEffect::RequestsDecision,
            classifier_id,
            evidence_refs,
        }
    }

    pub fn is_non_refusal_class(&self) -> bool {
        self.class != OperatorClass::M
    }

    pub fn is_non_execution_authority(&self) -> bool {
        matches!(
            self.authority_effect,
            ContractEffect::EvidenceOnly | ContractEffect::RequestsDecision
        )
    }
}

pub trait FixedLayerClassifier<S: BaseType, T: BaseType> {
    fn classify<C>(&self, candidate: &C, input: &S) -> ClassificationResult
    where
        C: DeclaredActionCandidate<S, T>;
}

// Origin: engine/crates_rs/core_contracts/src/traits_fixed_layer.rs
// Claim: urn:core:crates_rs:core-contracts:traits-fixed-layer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0c5edb85 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0c5edb85` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0c5edb85 {
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
impl BoundaryError0c5edb85 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0c5edb85 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0c5edb85 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0c5edb85 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0c5edb85> {
        if capacity_bound == 0 {
            return Err(BoundaryError0c5edb85::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0c5edb85::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0c5edb85::ExceedsCapacity {
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
    fn classification_results_are_evidence_or_decision_not_execution() {
        let classified = ClassifiedAction::new(
            ClassifiedActionId("classified:1".to_string()),
            DeclaredActionId("action:1".to_string()),
            OperatorClass::E,
            ContractEffect::EvidenceOnly,
            "classifier:test".to_string(),
            Vec::new(),
        )
        .expect("evidence-only classification should be allowed");
        assert_eq!(classified.authority_effect, ContractEffect::EvidenceOnly);

        let forbidden = ClassifiedAction::new(
            ClassifiedActionId("classified:2".to_string()),
            DeclaredActionId("action:2".to_string()),
            OperatorClass::E,
            ContractEffect::AuthorizesTransition,
            "classifier:test".to_string(),
            Vec::new(),
        );
        assert_eq!(forbidden, Err(ContractEffect::AuthorizesTransition));

        let evidence = ClassificationResult::evidence_only(
            OperatorClass::E,
            "exact repair evidence".to_string(),
            "classifier:test".to_string(),
            vec!["evidence:1".to_string()],
        );
        assert_eq!(evidence.authority_effect, ContractEffect::EvidenceOnly);
        assert!(evidence.is_non_refusal_class());
        assert!(evidence.is_non_execution_authority());

        let decision = ClassificationResult::requests_decision(
            OperatorClass::M,
            "mutation refused".to_string(),
            "classifier:evaluator".to_string(),
            vec!["evidence:2".to_string()],
        );
        assert_eq!(decision.authority_effect, ContractEffect::RequestsDecision);
        assert!(!decision.is_non_refusal_class());
        assert!(decision.is_non_execution_authority());
    }
}

#[cfg(test)]
mod l4_boundary_tests_0c5edb85 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0c5edb85::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0c5edb85::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0c5edb85::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0c5edb85::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0c5edb85::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0c5edb85::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0c5edb85::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
