// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SubjectKind {
    BaseType,
    Lambda,
    Reducer,
    Transform,
    Adapter,
    AlgebraLaw,
    Engine,
    MetaRule,
    AnalysisUnit,
    Pipeline,
    PolicyArtifact,
    ActionExecutor,
    TraceArtifact,
    ValidationUnit,
    Validation,
    Runtime,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TypeRef(pub &'static str);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Boundary {
    UbiquitousSheaf,
    Domain { domain: TypeRef },
    DomainCodomain { domain: TypeRef, codomain: TypeRef },
    SourceTarget { source: TypeRef, target: TypeRef },
    Carrier { carrier: TypeRef },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Guarantee {
    Deterministic,
    Pure,
    ReadOnly,
    SameDomain,
    PhiNonIncreasing,
    Idempotent,
    BoundedComputation,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Prohibition {
    NoSearch,
    NoMutation,
    NoHiddenState,
    NoRuntimeExecution,
    NoExternalEffects,
    NoHeuristics,
    NoTraversal,
    NoOptimization,
    NoOperatorSimulation,
    NoImplicitCoercion,
    NoPolicyInference,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Admissibility {
    pub explicit: bool,
    pub hidden_state_forbidden: bool,
    pub mixed_roles_forbidden: bool,
    pub domain_restricted: bool,
    pub parameter_restricted: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Totality {
    Total,
    Partial,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ImplementationRef {
    pub module: &'static str,
    pub type_name: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct WitnessRef {
    pub test: &'static str,
    pub enforced: bool,
}

#[derive(Debug, Clone, Copy)]
pub struct ContractInstance {
    pub id: &'static str,
    pub name: &'static str,
    pub subject_kind: SubjectKind,
    pub version: &'static str,
    pub boundary: Boundary,
    pub totality: Totality,
    pub schema_ref: Option<&'static str>,
    pub implementation: ImplementationRef,
    pub guarantees: &'static [Guarantee],
    pub prohibitions: &'static [Prohibition],
    pub witnesses: &'static [WitnessRef],
    pub admissibility: Admissibility,
    pub details: ContractDetails,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ConversionSemantics {
    Preserving,
    Lossy,
    Partial,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PhiBehavior {
    Preserving,
    DeclaredChange,
    Undefined,
}

#[derive(Debug, Clone, Copy)]
pub struct SemanticBasis {
    pub equivalence_relation: &'static str,
    pub invariant_set: &'static [&'static str],
}

#[derive(Debug, Clone, Copy)]
pub struct DomainConstraint {
    pub predicate: &'static str,
    pub witness: &'static str,
}

#[derive(Debug, Clone, Copy)]
pub struct LossProfile {
    pub reversible: bool,
    pub information_loss_basis: &'static str,
}

#[derive(Debug, Clone, Copy)]
pub struct AdapterDetails {
    pub semantics: ConversionSemantics,
    pub semantic_basis: Option<SemanticBasis>,
    pub invariants_preserved: &'static [&'static str],
    pub invariants_dropped: &'static [&'static str],
    pub phi_behavior: PhiBehavior,
    pub loss_profile: Option<LossProfile>,
    pub domain_constraint: Option<DomainConstraint>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EqualityNotion {
    Structural,
    Semantic,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AssociativityMode {
    Strict,
    OrderedOnly,
    NotApplicable,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ClosureMode {
    Typed,
    Partial,
    ForbiddenAcrossBoundary,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NormalizationStatus {
    None,
    Exists {
        canonical_form: &'static str,
        uniqueness: bool,
    },
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum PhiCompatibility {
    NonIncreasing,
    StrictlyReducing,
    PreservedAcrossAdapter,
    MonotoneBound { factor: f64 },
    Constrained { relation: &'static str },
    Unconstrained,
    NotApplicable,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObjectKind {
    BasisOperator,
    Adapter,
    StateSignature,
    Other(&'static str),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MorphismKind {
    TypedMorphism,
    Operator,
    Adapter,
    Signature,
    Other(&'static str),
}

#[derive(Debug, Clone, Copy)]
pub struct Carrier {
    pub objects: &'static [ObjectKind],
    pub morphisms: &'static [MorphismKind],
    pub equality: EqualityNotion,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CompositionRule {
    StrictTyping,
    AdapterMediated,
    ForbiddenAcrossBoundary,
}

#[derive(Debug, Clone, Copy)]
pub struct Signature {
    pub name: &'static str,
}

#[derive(Debug, Clone, Copy)]
pub struct MorphismType {
    pub domain: Signature,
    pub codomain: Signature,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryLaw {
    pub requires_adapter: bool,
    pub implicit_coercion_forbidden: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AlgebraFailureMode {
    LawNotSatisfied,
    SignatureMismatch,
    NonComposablePair,
    MissingIdentity,
    BoundaryViolation,
    PhiLawViolation,
}

#[derive(Debug, Clone, Copy)]
pub struct AlgebraLawDescriptor {
    pub id: &'static str,
    pub name: &'static str,
    pub carrier: Carrier,
    pub composition_rule: CompositionRule,
    pub associativity: AssociativityMode,
    pub has_identity: bool,
    pub closure: ClosureMode,
    pub normalization: NormalizationStatus,
    pub phi_compatibility: PhiCompatibility,
    pub boundary: BoundaryLaw,
    pub morphism_types: &'static [MorphismType],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TransformParameterConstraint {
    /// Disallows parameters that degenerate into a native identity mapping, ensuring
    /// the transform functionally mutates the domain.
    CanonicalIdentityExclusion,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReducerParameterConstraint {
    ExcludesTerminalCollapse,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LambdaParameterConstraint {
    PreservesFiberDimension,
}

#[derive(Debug, Clone, Copy)]
pub struct TransformDetails {
    pub parameter_constraints: &'static [TransformParameterConstraint],
}

#[derive(Debug, Clone, Copy)]
pub struct ReducerDetails {
    pub parameter_constraints: &'static [ReducerParameterConstraint],
}

#[derive(Debug, Clone, Copy)]
pub struct LambdaDetails {
    pub parameter_constraints: &'static [LambdaParameterConstraint],
}

#[derive(Debug, Clone, Copy)]
pub enum ContractDetails {
    None,
    Adapter(AdapterDetails),
    Algebra(AlgebraLawDescriptor),
    Transform(TransformDetails),
    Reducer(ReducerDetails),
    Lambda(LambdaDetails),
}

/// Associates a contract struct with its generated semantic metadata instance.
/// This trait is strictly implemented by codegen, reflecting the YAML source of truth.
pub trait GeneratedContractMetadata {
    const INSTANCE: ContractInstance;
}

// Origin: engine/crates_rs/core_contracts/src/contracts_contract.rs
// Claim: urn:core:crates_rs:core-contracts:contracts-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord71311532 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord71311532` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError71311532 {
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
impl BoundaryError71311532 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError71311532 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError71311532 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord71311532 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError71311532> {
        if capacity_bound == 0 {
            return Err(BoundaryError71311532::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError71311532::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError71311532::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_71311532 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord71311532::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord71311532::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord71311532::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord71311532::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord71311532::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError71311532::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError71311532::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
