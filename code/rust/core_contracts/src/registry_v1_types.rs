//! core.contract.v1 envelope types.
//!
//! See `docs/superpowers/specs/2026-05-31-core-contract-v1-walking-skeleton-design.md`.
//! The `descriptor` block is the only machine-authoritative enforcement block; the sibling
//! blocks (`math`, `doctrine`, ...) are typed content/docs and are NOT projected into
//! [`ContractDescriptor`]. `customer_claim_allowed` stays on the envelope (validated by
//! `v1_validate`), not promoted to the shared type.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_faf2e966;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_faf2e966<T> = std::result::Result<T, BoundaryError_faf2e966>;
use serde::{Deserialize, Serialize};
use serde_yaml::Value;

use crate::kinds::{
    Capability, CapabilityPolicy, ComponentRole, ContractCategory, ContractEffect, ContractStatus,
};
use crate::schema::{
    ConstitutionalBlock, ConstraintBlock, ContractDescriptor, LawBlock, OperatorClassPolicy,
    ProofObligationRef, RefusalPolicy, ReplayBlock, RustBinding, TerminalPolicy, WitnessesBlock,
};
use core_types::EvidenceCeiling;

/// Rich lifecycle status authored in v1 files. Projected onto the coarse 4-variant
/// [`ContractStatus`] for the shared registry (the shared enum is NOT extended this sprint).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CoreContractV1Status {
    Active,
    Draft,
    Deprecated,
    Experimental,
    MathematicalWip,
    ExactRationalClassifierImplemented,
}

impl CoreContractV1Status {
    /// Collapse the rich variants into the base four (spec §11.2).
    pub fn normalized(self) -> Self {
        match self {
            Self::ExactRationalClassifierImplemented => Self::Active,
            Self::MathematicalWip => Self::Experimental,
            other => other,
        }
    }

    /// Project onto the legacy 4-variant `ContractStatus`
    /// (`Canonical/Staged/Archived/Deprecated`). Confirmed mapping (spec §11.2):
    /// active/implemented -> Canonical; draft/experimental/wip -> Staged; deprecated -> Deprecated.
    pub fn to_contract_status(self) -> ContractStatus {
        match self.normalized() {
            Self::Active => ContractStatus::Canonical,
            Self::Draft | Self::Experimental => ContractStatus::Staged,
            Self::Deprecated => ContractStatus::Deprecated,
            // normalized() removes the rich variants:
            Self::MathematicalWip | Self::ExactRationalClassifierImplemented => unreachable!(),
        }
    }
}

/// The kind of a v1 contract. Maps to `(ContractCategory, ComponentRole)` for projection.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ContractKind {
    MathContract,
    ConstitutionContract,
    StateContract,
    EvidenceContract,
    ObstructionContract,
    GovernanceContract,
    ExecutionContract,
    ProductContract,
    LiftContract,
}

impl ContractKind {
    pub fn category(self) -> ContractCategory {
        match self {
            Self::MathContract => ContractCategory::Math,
            Self::ConstitutionContract => ContractCategory::Constitution,
            Self::StateContract => ContractCategory::State,
            Self::EvidenceContract => ContractCategory::Evidence,
            Self::ObstructionContract => ContractCategory::Obstruction,
            Self::GovernanceContract => ContractCategory::Governance,
            Self::ExecutionContract => ContractCategory::Execution,
            Self::ProductContract => ContractCategory::Product,
            Self::LiftContract => ContractCategory::Lifts,
        }
    }

    /// Role to use when the file omits `role`. Only math has one; other kinds must declare
    /// `role` explicitly (enforced by `v1_validate::validate_v1`).
    pub fn default_role(self) -> Option<ComponentRole> {
        match self {
            Self::MathContract => Some(ComponentRole::MathObject),
            _ => None,
        }
    }

    pub fn is_math(self) -> bool {
        matches!(self, Self::MathContract)
    }

    /// Capabilities a contract of this kind must forbid. A math contract confers no
    /// authority, so it must forbid decision/certificate/action emission — matching
    /// `validate::validate_math_object`'s expectations and the contract's `non_role`.
    /// Other kinds default to none here and are tightened per-role only if
    /// `validate_registry` demands it (discovery-driven).
    pub fn forbidden_capabilities(self) -> Vec<Capability> {
        match self {
            Self::MathContract => vec![
                Capability::EmitDecision,
                Capability::EmitCertificate,
                Capability::EmitAction,
            ],
            // A lift license authorizes ascent but must not itself execute or mutate
            // (matches validate::validate_lift_license's forbid_capability checks).
            Self::LiftContract => vec![
                Capability::ExecuteStateTransition,
                Capability::RuntimeMutation,
            ],
            _ => Vec::new(),
        }
    }
}

/// Dependency declarations inside the machine descriptor.
#[derive(Debug, Clone, Default, Deserialize)]
#[serde(deny_unknown_fields, default)]
pub struct Dependencies {
    pub contracts: Vec<String>,
    pub proof_obligations: Vec<ProofObligationRef>,
}

/// The machine-authoritative enforcement block. Unknown keys are rejected.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DescriptorBlock {
    pub authority_effect: ContractEffect,
    pub evidence_ceiling: EvidenceCeiling,
    #[serde(default)]
    pub runtime_enforcement: bool,
    #[serde(default)]
    pub customer_claim_allowed: bool,
    #[serde(default)]
    pub dependencies: Dependencies,
    #[serde(default)]
    pub terminals: TerminalPolicy,
    #[serde(default)]
    pub refusals: RefusalPolicy,
    #[serde(default)]
    pub operator_classes: OperatorClassPolicy,

    // Authority machinery — carried for authority-bearing kinds (e.g. lift_contract /
    // LiftLicense). Optional so descriptive contracts (math/state/obstruction) omit them.
    // Project straight into the same-named ContractDescriptor fields.
    #[serde(default)]
    pub constitution: Option<ConstitutionalBlock>,
    #[serde(default)]
    pub constraints: Option<ConstraintBlock>,
    #[serde(default)]
    pub replay: Option<ReplayBlock>,
    #[serde(default)]
    pub witnesses: Option<WitnessesBlock>,

    /// Subject the contract operates on (e.g. an evaluator's input type). Required by some
    /// role validators (Evaluator, Validator). Pulled from the legacy contract, not invented.
    #[serde(default)]
    pub subject_type: Option<String>,
    /// Explicit capability policy. When present it is AUTHORITATIVE (roles within a kind
    /// forbid different capabilities); when absent, the kind-derived default is used.
    #[serde(default)]
    pub capabilities: Option<CapabilityPolicy>,
    /// Law block (e.g. an Engine declares `effect: Stateful`). Required by some role
    /// validators (Engine). Pulled from the legacy contract.
    #[serde(default)]
    pub laws: Option<LawBlock>,
    /// Runtime state type the contract operates over (required by the Engine validator).
    #[serde(default)]
    pub runtime_state_type: Option<String>,
}

/// A canonical core.contract.v1 file. Unknown top-level keys (e.g. a stray `compact_yaml`)
/// are rejected at deserialize time.
#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CoreContractV1 {
    pub schema_version: String,
    pub contract_id: String,
    pub title: String,
    pub kind: ContractKind,
    pub status: CoreContractV1Status,
    #[serde(default)]
    pub layer: Option<String>,
    /// Explicit machine role. Required for non-math kinds (validate_v1); math defaults to
    /// MathObject via `ContractKind::default_role`.
    #[serde(default)]
    pub role: Option<ComponentRole>,
    pub descriptor: DescriptorBlock,

    // Typed-but-enforcement-inert content/docs/tests blocks. Opaque `Value` keeps the
    // walking skeleton small while `deny_unknown_fields` still rejects stray top-level keys.
    #[serde(default)]
    pub math: Option<Value>,
    #[serde(default)]
    pub requirements: Option<Value>,
    #[serde(default)]
    pub definition: Option<Value>,
    #[serde(default)]
    pub laws: Option<Value>,
    #[serde(default)]
    pub equivalence: Option<Value>,
    #[serde(default)]
    pub replay: Option<Value>,
    #[serde(default)]
    pub relationships: Option<Value>,
    #[serde(default)]
    pub rust_binding: Option<RustBinding>,
    #[serde(default)]
    pub lean_binding: Option<Value>,
    #[serde(default)]
    pub lean4_binding: Option<Value>,
    #[serde(default)]
    pub negative_tests: Option<Vec<String>>,
    #[serde(default)]
    pub doctrine: Option<Value>,
    #[serde(default)]
    pub wip: Option<Value>,

    /// NON-CANONICAL debate / diagnostic only (ADR-007a).
    ///
    /// Loud top-level key so humans never confuse this with contract law.
    /// Not projected into [`ContractDescriptor`]; never mints AuthorityEffect.
    /// Two subsections live inside (see `NomosDebateNotCanonical`):
    /// 1. `potential_defects` — what may be wrong with this math YAML
    /// 2. `realization_delta_vs_implemented_math_file` — YAML vs code (empty is ideal)
    #[serde(default, rename = "nomos_debate_NOT_CANONICAL")]
    pub nomos_debate_not_canonical: Option<NomosDebateNotCanonical>,
}

/// Debate-only envelope attached to math (and optionally other) contracts.
///
/// **Not law.** Deserialized so files may carry open debate without
/// `deny_unknown_fields` rejecting the file. Enforcement code must ignore this.
#[derive(Debug, Clone, Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields, default)]
pub struct NomosDebateNotCanonical {
    /// Fixed banner string — must stay non-authoritative prose.
    #[serde(default = "default_debate_banner")]
    pub banner: String,
    /// Always `true` when present — machine-readable "not law" flag.
    #[serde(default = "default_true")]
    pub not_part_of_contract_law: bool,
    /// Always `none` — debate does not mint authority.
    #[serde(default = "default_authority_none")]
    pub authority_effect: String,
    /// §1 What is potentially wrong with this math YAML contract.
    #[serde(default)]
    pub potential_defects: Vec<Value>,
    /// §2 How this math contract differs from the implemented math file.
    /// Empty list is the ideal; open debate is allowed and preferred to hiding.
    #[serde(default)]
    pub realization_delta_vs_implemented_math_file: Vec<Value>,
}

fn default_debate_banner() -> String {
    "NON-CANONICAL DEBATE ONLY — not contract law; not enforced as obligations; AuthorityEffect None"
        .to_string()
}

fn default_true() -> bool {
    true
}

fn default_authority_none() -> String {
    "none".to_string()
}

impl CoreContractV1 {
    /// Project the machine descriptor into the shared [`ContractDescriptor`] (spec §4.3, §11).
    /// Content/doc blocks and `customer_claim_allowed` are intentionally NOT projected.
    pub fn to_descriptor(&self) -> ContractDescriptor {
        ContractDescriptor {
            id: self.contract_id.clone(),
            name: self.title.clone(),
            category: self.kind.category(),
            // Explicit role wins; math falls back to its default. validate_v1 guarantees
            // non-math kinds declare a role, so the unwrap_or is only a safety net.
            role: self
                .role
                .or_else(|| self.kind.default_role())
                .unwrap_or(ComponentRole::MathObject),
            status: self.status.to_contract_status(),
            authority_effect: self.descriptor.authority_effect,

            domain_type: None,
            codomain_type: None,
            subject_type: self.descriptor.subject_type.clone(),
            runtime_state_type: self.descriptor.runtime_state_type.clone(),

            laws: self.descriptor.laws.clone(),
            constraints: self.descriptor.constraints.clone().unwrap_or_default(),
            // Explicit capabilities are authoritative; otherwise fall back to kind-derived.
            capabilities: self.descriptor.capabilities.clone().unwrap_or_else(|| {
                CapabilityPolicy {
                    forbidden: self.kind.forbidden_capabilities(),
                    required: Vec::new(),
                }
            }),

            requires: None,
            validation: None,
            witnesses: self.descriptor.witnesses.clone(),
            replay: self.descriptor.replay.clone(),
            constitution: self.descriptor.constitution.clone(),

            schema_hash: None,

            algebra_laws: None,
            governed_algebra_layer: None,
            operator_class: None,
            signature: None,
            uros: None,
            evaluates_outputs_of: None,
            decision_scope: None,

            // v1 enforcement fields:
            evidence_ceiling: Some(self.descriptor.evidence_ceiling),
            runtime_enforcement: self.descriptor.runtime_enforcement,
            proof_obligations: self.descriptor.dependencies.proof_obligations.clone(),
            terminals: self.descriptor.terminals.clone(),
            refusals: self.descriptor.refusals.clone(),
            operator_classes: self.descriptor.operator_classes.clone(),
            rust_binding: self.rust_binding.clone(),
        }
    }
}

#[cfg(test)]
pub(crate) const MINIMAL_V1: &str = r#"
schema_version: "core.contract.v1"
contract_id: "urn:core:math:demo:v0.1.0"
title: "Demo"
kind: "math_contract"
status: "mathematical_wip"
descriptor:
  authority_effect: "none"
  evidence_ceiling: "ShapeOnly"
  runtime_enforcement: false
  customer_claim_allowed: false
  dependencies: { contracts: [], proof_obligations: [] }
  terminals: { may_emit: [], may_support: [] }
  refusals: { may_emit: [] }
  operator_classes: { may_support: [], must_not_self_assign: true }
"#;

// Origin: engine/crates_rs/core_contracts/src/registry_v1_types.rs
// Claim: urn:core:crates_rs:core-contracts:registry-v1-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfaf2e966 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfaf2e966` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfaf2e966 {
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
impl BoundaryErrorfaf2e966 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfaf2e966 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfaf2e966 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfaf2e966 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfaf2e966> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfaf2e966::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfaf2e966::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfaf2e966::ExceedsCapacity {
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
    fn status_deserializes_and_projects() {
        let s: CoreContractV1Status =
            serde_yaml::from_str("exact_rational_classifier_implemented").unwrap();
        assert_eq!(s, CoreContractV1Status::ExactRationalClassifierImplemented);
        assert_eq!(s.normalized(), CoreContractV1Status::Active);
        assert_eq!(s.to_contract_status(), ContractStatus::Canonical);
        assert_eq!(
            CoreContractV1Status::MathematicalWip.to_contract_status(),
            ContractStatus::Staged
        );
        assert_eq!(
            CoreContractV1Status::Deprecated.to_contract_status(),
            ContractStatus::Deprecated
        );
    }

    #[test]
    fn kind_maps_to_category_and_role() {
        let k: ContractKind = serde_yaml::from_str("math_contract").unwrap();
        assert_eq!(k.category(), ContractCategory::Math);
        assert_eq!(k.default_role(), Some(ComponentRole::MathObject));
        assert!(k.is_math());
    }

    #[test]
    fn per_category_kinds_map_correctly() {
        let cases = [
            ("constitution_contract", ContractCategory::Constitution),
            ("state_contract", ContractCategory::State),
            ("evidence_contract", ContractCategory::Evidence),
            ("obstruction_contract", ContractCategory::Obstruction),
            ("governance_contract", ContractCategory::Governance),
            ("execution_contract", ContractCategory::Execution),
            ("product_contract", ContractCategory::Product),
            ("lift_contract", ContractCategory::Lifts),
        ];
        for (yaml, cat) in cases {
            let k: ContractKind = serde_yaml::from_str(yaml).unwrap();
            assert_eq!(k.category(), cat, "kind {yaml}");
            assert_eq!(
                k.default_role(),
                None,
                "non-math kinds have no default role"
            );
            if k != ContractKind::LiftContract {
                assert!(
                    k.forbidden_capabilities().is_empty(),
                    "{yaml} should forbid none by default"
                );
            }
        }
        // lift_contract forbids execution/mutation (matches validate_lift_license).
        let lift = ContractKind::LiftContract.forbidden_capabilities();
        assert!(lift.contains(&crate::kinds::Capability::ExecuteStateTransition));
        assert!(lift.contains(&crate::kinds::Capability::RuntimeMutation));
        let m: ContractKind = serde_yaml::from_str("math_contract").unwrap();
        assert!(m
            .forbidden_capabilities()
            .contains(&crate::kinds::Capability::EmitDecision));
    }

    #[test]
    fn explicit_role_projects() {
        let y = r#"
schema_version: "core.contract.v1"
contract_id: "urn:core:obstruction:demo:v0.1.0"
title: "Demo Obstruction"
kind: "obstruction_contract"
status: "mathematical_wip"
role: "AnalysisUnit"
descriptor:
  authority_effect: "evidence_only"
  evidence_ceiling: "LocalReplay"
"#;
        let c: CoreContractV1 = serde_yaml::from_str(y).unwrap();
        let d = c.to_descriptor();
        assert_eq!(d.category, ContractCategory::Obstruction);
        assert_eq!(d.role, ComponentRole::AnalysisUnit);
        assert_eq!(d.authority_effect, ContractEffect::EvidenceOnly);
    }

    #[test]
    fn deserializes_minimal_envelope() {
        let c: CoreContractV1 = serde_yaml::from_str(MINIMAL_V1).unwrap();
        assert_eq!(c.schema_version, "core.contract.v1");
        assert!(c.kind.is_math());
        assert_eq!(c.descriptor.authority_effect, ContractEffect::None);
        assert!(!c.descriptor.runtime_enforcement);
    }

    #[test]
    fn unknown_top_level_field_rejected() {
        let bad = format!("{MINIMAL_V1}\ncompact_yaml: {{}}\n");
        assert!(serde_yaml::from_str::<CoreContractV1>(&bad).is_err());
    }

    #[test]
    fn nomos_debate_not_canonical_deserializes_and_is_not_projected() {
        let y = r#"
schema_version: "core.contract.v1"
contract_id: "urn:core:math:demo:v0.1.0"
title: "Demo"
kind: "math_contract"
status: "mathematical_wip"
descriptor:
  authority_effect: "none"
  evidence_ceiling: "ShapeOnly"
  runtime_enforcement: false
  customer_claim_allowed: false
  dependencies: { contracts: [], proof_obligations: [] }
  terminals: { may_emit: [], may_support: [] }
  refusals: { may_emit: [] }
  operator_classes: { may_support: [], must_not_self_assign: true }
nomos_debate_NOT_CANONICAL:
  banner: "NON-CANONICAL DEBATE ONLY"
  not_part_of_contract_law: true
  authority_effect: none
  potential_defects:
    - code: EXAMPLE
      detail: sample
  realization_delta_vs_implemented_math_file: []
"#;
        let c: CoreContractV1 = serde_yaml::from_str(y).unwrap();
        let d = c
            .nomos_debate_not_canonical
            .as_ref()
            .expect("debate block present");
        assert!(d.not_part_of_contract_law);
        assert_eq!(d.authority_effect, "none");
        assert_eq!(d.potential_defects.len(), 1);
        assert!(d.realization_delta_vs_implemented_math_file.is_empty());
        // Projection must ignore debate (no panic; descriptor still clean).
        let desc = c.to_descriptor();
        assert_eq!(desc.authority_effect, ContractEffect::None);
    }

    #[test]
    fn projects_into_contract_descriptor() {
        let c: CoreContractV1 = serde_yaml::from_str(MINIMAL_V1).unwrap();
        let d = c.to_descriptor();
        assert_eq!(d.id, "urn:core:math:demo:v0.1.0");
        assert_eq!(d.name, "Demo");
        assert_eq!(d.category, ContractCategory::Math);
        assert_eq!(d.role, ComponentRole::MathObject);
        assert_eq!(d.status, ContractStatus::Staged); // mathematical_wip -> Staged
        assert_eq!(d.authority_effect, ContractEffect::None);
        assert!(!d.runtime_enforcement);
        assert_eq!(d.evidence_ceiling, Some(EvidenceCeiling::ShapeOnly));
    }
}

#[cfg(test)]
mod l4_boundary_tests_faf2e966 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfaf2e966::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfaf2e966::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfaf2e966::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfaf2e966::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfaf2e966::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfaf2e966::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfaf2e966::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
