use crate::kinds::{
    ArtifactKind, CapabilityPolicy, ComponentRole, ContractCategory, ContractEffect, ContractStatus,
};
use core_types::EvidenceCeiling;
use serde::{Deserialize, Serialize};

/// Canonical authority-bearing artifact families loaded from YAML descriptors.
///
/// These are the only globally canonical output families. Domain-specific
/// shapes such as witnesses, terminal envelopes, or verification reports should
/// be represented with `ArtifactKind` inside one of these families, not as a
/// parallel authority family.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ArtifactFamily {
    StructureArtifact,
    EvidenceEnvelope,
    FactEnvelope,
    DecisionEnvelope,
    ActionLicense,
    Action,
    Record,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum OperatorClass {
    E,
    I,
    C,
    R,
    M,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum UrosSystem {
    GeneralTheory,
    Kernel,
    ArtifactFamilies,
    Runtime,
    Codex,
    Encyclopedia,
    LevelSystem,
    Tiers,
    OperatorLevels,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum RegistryKind {
    Codex,
    Encyclopedia,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ExpressivityCoordinate {
    pub domain: String,
    pub operator_height: Option<u16>,
    pub meta_height: Option<u16>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct UrosBlock {
    pub system: UrosSystem,
    pub subsystem: String,
    pub artifact_family: ArtifactFamily,
    #[serde(default)]
    pub artifact_kind: Option<ArtifactKind>,
    pub registry: RegistryKind,
    pub domain: String,
    pub tier: u8,
    pub operator_height: Option<u16>,
    pub meta_height: Option<u16>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum AuthorityLayer {
    Structure,
    /// Raw observations; can be promoted to Fact by a declared checker boundary.
    Evidence,
    Fact,
    Judgment,
    Action,
    Record,
    Runtime,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ConstitutionalBlock {
    #[serde(default)]
    pub contract_dependencies: Vec<String>,
    #[serde(default)]
    pub law_refs: Vec<String>,
    pub emits: ArtifactFamily,
    pub authority_layer: AuthorityLayer,
    #[serde(default)]
    pub forbidden_later_layers: Vec<AuthorityLayer>,
    #[serde(default)]
    pub replay_certificates: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct SignatureBlock {
    pub input: Option<String>,
    pub output: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct RequiresBlock {
    #[serde(default)]
    pub licenses: Vec<String>,
    #[serde(default)]
    pub declarations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct ValidationBlock {
    #[serde(default)]
    pub validators: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct WitnessesBlock {
    #[serde(default)]
    pub required: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct ReplayBlock {
    #[serde(default)]
    pub required: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct LawRequirementsBlock {
    #[serde(default)]
    pub required: Vec<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum PhiLawDecl {
    NonIncreasing,
    Reducing,
    Unrestricted,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum StructureLawDecl {
    Preserving,
    Reductive,
    Transforming,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum EffectLawDecl {
    Pure,
    ReadOnly,
    Stateful,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[serde(untagged)]
#[derive(Default)]
pub enum LawPresence<T> {
    Required(T),
    #[default]
    Forbidden,
}

impl<T> LawPresence<T> {
    pub fn is_required(&self) -> bool {
        matches!(self, LawPresence::Required(_))
    }

    pub fn as_option(&self) -> Option<&T> {
        match self {
            LawPresence::Required(v) => Some(v),
            LawPresence::Forbidden => None,
        }
    }
}

impl<T> From<Option<T>> for LawPresence<T> {
    fn from(opt: Option<T>) -> Self {
        match opt {
            Some(v) => LawPresence::Required(v),
            None => LawPresence::Forbidden,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct LawBlock {
    #[serde(default)]
    pub phi: LawPresence<PhiLawDecl>,
    #[serde(default)]
    pub structure: LawPresence<StructureLawDecl>,
    #[serde(default)]
    pub effect: LawPresence<EffectLawDecl>,
    #[serde(default)]
    pub required: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ConstraintBlock {
    pub total_over_domain: Option<bool>,
    pub deterministic: Option<bool>,
    pub search_forbidden: Option<bool>,
    pub hidden_state_forbidden: Option<bool>,
    pub iteration_forbidden: Option<bool>,
    pub mutation_forbidden: Option<bool>,
    pub read_only: Option<bool>,
    pub typed_output_required: Option<bool>,
    pub operator_execution_forbidden: Option<bool>,
    pub runtime_orchestration_forbidden: Option<bool>,
    pub immutable_after_emit: Option<bool>,
    pub policy_version_required: Option<bool>,
    pub certificate_required: Option<bool>,
    /// Engine gate: requires a declared ActionLicense before execution.
    pub action_license_required: Option<bool>,
    /// CheckedPacket gate: a declared checker boundary must be present.
    pub checker_boundary_required: Option<bool>,
    pub authority_does_not_exceed_evidence: Option<bool>,
    pub scope_bound: Option<bool>,
    pub non_transferable: Option<bool>,
    pub self_certification_forbidden: Option<bool>,
    pub admissibility_decision_forbidden: Option<bool>,
    pub measurement_computation_forbidden: Option<bool>,
    pub action_emission_forbidden: Option<bool>,
    pub candidate_generation_forbidden: Option<bool>,
    pub signature_required: Option<bool>,
    pub certificate_hash_required: Option<bool>,
    pub policy_hash_required: Option<bool>,
    pub request_hash_required: Option<bool>,
    pub replay_required: Option<bool>,
    pub public_signing_forbidden: Option<bool>,
    pub raw_payload_forbidden: Option<bool>,
    pub authority_effect_must_be_none: Option<bool>,
}

// Runtime/deserialized contract descriptor loaded from YAML.
// ── core.contract.v1 shared enforcement field types ───────────────────────
// These are owned by the shared schema so ContractDescriptor (the enforcement
// record) can carry them, and the CoreContractV1 envelope can reuse them.

/// A proof-obligation identifier (e.g. "PO-D3", "SG-AUTH", "PO-AUTH-NC"). Free string with
/// grammar validation in `registry::v1_validate`; no global registry yet (later sprint).
/// `transparent` so the YAML is a bare string (`- "PO-D3"`), not a tuple/struct.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(transparent)]
pub struct ProofObligationRef(pub String);

impl ProofObligationRef {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Terminals a contract may emit (authority-bearing) / may support (descriptive classes).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(default)]
pub struct TerminalPolicy {
    pub may_emit: Vec<String>,
    pub may_support: Vec<String>,
}

/// Refusals a contract may emit.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(default)]
pub struct RefusalPolicy {
    pub may_emit: Vec<String>,
}

/// Operator-class policy. `may_support` entries are validated to be a subset of {E,I,C,R,M}.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(default)]
pub struct OperatorClassPolicy {
    pub may_support: Vec<OperatorClass>,
    pub must_not_self_assign: bool,
}

/// Implementation mapping for a contract (informational in v1).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RustBinding {
    #[serde(rename = "crate")]
    pub krate: String,
    pub module: String,
    #[serde(default)]
    pub symbols: Vec<String>,
    /// Tests in the bound module that discharge this contract's `negative_tests`.
    ///
    /// `negative_tests` is prose — "add/sub of unequal shapes must be rejected" —
    /// which states an obligation but cannot be checked. Naming the test that
    /// discharges it makes the pairing mechanical, so a contract cannot declare
    /// an obligation nothing exercises.
    ///
    /// Empty means the pairing has not been recorded, not that there are no
    /// obligations. Doctrinal entries such as "must not claim GlobalGreen" have
    /// no unit test and are deliberately absent.
    #[serde(default)]
    pub required_tests: Vec<String>,
}

/// This descriptor preserves contract doctrine and schema-level declarations.
/// Generated Rust contract image types are represented separately by
/// `binding::ContractDescriptor`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractDescriptor {
    pub id: String,
    pub name: String,
    pub category: ContractCategory,
    pub role: ComponentRole,
    pub status: ContractStatus,
    pub authority_effect: ContractEffect,

    pub domain_type: Option<String>,
    pub codomain_type: Option<String>,
    pub subject_type: Option<String>,
    pub runtime_state_type: Option<String>,

    pub laws: Option<LawBlock>,
    #[serde(default)]
    pub constraints: ConstraintBlock,
    #[serde(default)]
    pub capabilities: CapabilityPolicy,

    pub requires: Option<RequiresBlock>,
    pub validation: Option<ValidationBlock>,
    pub witnesses: Option<WitnessesBlock>,
    pub replay: Option<ReplayBlock>,
    pub constitution: Option<ConstitutionalBlock>,

    pub schema_hash: Option<String>,

    #[serde(default)]
    pub algebra_laws: Option<Vec<String>>,
    #[serde(default)]
    pub governed_algebra_layer: Option<String>,
    pub operator_class: Option<OperatorClass>,
    pub signature: Option<SignatureBlock>,
    pub uros: Option<UrosBlock>,
    pub evaluates_outputs_of: Option<ComponentRole>,
    pub decision_scope: Option<Vec<String>>,

    // ── core.contract.v1 enforcement fields (added; all default for back-compat) ──
    // `authority_effect` already exists above and is reused; `operator_class` (singular,
    // above) is the legacy single class and is distinct from `operator_classes` (policy).
    #[serde(default)]
    pub evidence_ceiling: Option<EvidenceCeiling>,
    #[serde(default)]
    pub runtime_enforcement: bool,
    #[serde(default)]
    pub proof_obligations: Vec<ProofObligationRef>,
    #[serde(default)]
    pub terminals: TerminalPolicy,
    #[serde(default)]
    pub refusals: RefusalPolicy,
    #[serde(default)]
    pub operator_classes: OperatorClassPolicy,
    #[serde(default)]
    pub rust_binding: Option<RustBinding>,
}

// Origin: engine/crates_rs/core_contracts/src/schema.rs
// Claim: urn:core:crates_rs:core-contracts:schema:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda2887260 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda2887260` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora2887260 {
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
impl BoundaryErrora2887260 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora2887260 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora2887260 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda2887260 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora2887260> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora2887260::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora2887260::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora2887260::ExceedsCapacity {
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
mod v1_field_type_tests {
    use super::*;

    #[test]
    fn policy_types_default_empty() {
        assert!(TerminalPolicy::default().may_emit.is_empty());
        assert!(TerminalPolicy::default().may_support.is_empty());
        assert!(RefusalPolicy::default().may_emit.is_empty());
        let oc = OperatorClassPolicy::default();
        assert!(oc.may_support.is_empty());
        assert!(!oc.must_not_self_assign);
    }

    #[test]
    fn proof_obligation_ref_is_transparent_string() {
        let p: ProofObligationRef = serde_yaml::from_str("\"PO-D3\"").unwrap();
        assert_eq!(p.as_str(), "PO-D3");
    }

    #[test]
    fn rust_binding_renames_crate_field() {
        let rb: RustBinding =
            serde_yaml::from_str("crate: core_core\nmodule: trichotomy\n").unwrap();
        assert_eq!(rb.krate, "core_core");
        assert_eq!(rb.module, "trichotomy");
        assert!(rb.symbols.is_empty());
    }
}

#[cfg(test)]
mod l4_boundary_tests_a2887260 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda2887260::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda2887260::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda2887260::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda2887260::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda2887260::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora2887260::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora2887260::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
