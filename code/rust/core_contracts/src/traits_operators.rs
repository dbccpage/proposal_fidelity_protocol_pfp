use crate::kinds::BaseType;
use crate::traits::identity::NamedComponent as OperatorIdentity;

/// BoundaryOperatorIdentity is used for operations mapping between the internal representation
/// and external or raw data shapes.
pub trait BoundaryOperatorIdentity {
    fn name(&self) -> &'static str;
}

// ─── Lambda Failure States ──────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LambdaFailure {
    /// Input falls outside the Lambda's admitted domain.
    OutsideAdmissibleDomain,
    /// A declared invariant was violated during transformation.
    InvariantViolation { invariant: &'static str },
    /// The transformation is undefined for this input by declared law.
    UndefinedTransformation { reason: &'static str },
    /// Input contains non-finite values (NaN, Inf).
    NonFiniteInput,
}

// ─── Operator Execution Laws & Witnesses ────────────────────────────────────

/// Explicit mapping of Phi measurement references, satisfying OP-L2.
#[derive(Debug, Clone)]
pub struct LambdaWitness {
    pub phi_functional_id: &'static str,
    pub before_ref: String,
    pub after_ref: String,
    pub comparison: PhiComparison,
    pub certificate_refs: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PhiComparison {
    NonIncreasing,
    StrictDecrease,
    Incomparable,
    DiagnosticOnly,
}

/// The declared behavior law for a functional Lambda operator.
pub struct LambdaLaw {
    pub preserved_invariants: &'static [&'static str],
    pub phi_law: &'static dyn PhiLaw,
}

impl std::fmt::Debug for LambdaLaw {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("LambdaLaw")
            .field("preserved_invariants", &self.preserved_invariants)
            .field("phi_law", &"dyn PhiLaw")
            .finish()
    }
}

impl Clone for LambdaLaw {
    fn clone(&self) -> Self {
        Self {
            preserved_invariants: self.preserved_invariants,
            phi_law: self.phi_law,
        }
    }
}

pub use crate::traits::authority_laws::PhiLaw;

// ─── OS Doctrine Operator Traits ────────────────────────────────────────────

/// LambdaOp: deterministic, stateless, unary internal-descent morphism.
/// Maps S -> T without carrier enlargement, satisfying OP-L1 and OP-L2.
pub trait LambdaOp<S: BaseType, T: BaseType>: OperatorIdentity {
    fn apply(&self, input: &S) -> Result<T, LambdaFailure>;
    fn law(&self) -> &'static LambdaLaw;
}

/// ReducerOp: idempotent structure-shrinking endomorphism S -> S.
/// Satisfies OP-L3 and OP-L4 (idempotent, non-expanding).
pub trait ReducerOp<S: BaseType>: OperatorIdentity {
    fn apply(&self, input: &S) -> Result<S, LambdaFailure>;
}

/// TransformOp: pure endomorphism S -> S without Phi-monotonicity constraints.
/// Maps structure-preserving transformations.
pub trait TransformOp<S: BaseType>: OperatorIdentity {
    fn apply(&self, input: &S) -> Result<S, LambdaFailure>;
}

// ─── OS Doctrine Boundary Traits ────────────────────────────────────────────

/// MetaRule: deterministic structural classifier producing admissibility/composability judgments.
pub trait MetaRule<T> {
    type Output;
    fn evaluate(&self, subject: &T) -> Result<Self::Output, String>;
}

pub use crate::traits::intake::ConstructorError;

/// ConstructorOp: ingests raw/heterogeneous data and maps it formally into BaseType.
pub trait ConstructorOp<Raw, T: BaseType>: BoundaryOperatorIdentity {
    type Error;
    fn construct(&self, raw: Raw) -> Result<T, Self::Error>;
}

/// GeneratorOp: proposes domain-specific structural modifications to an existing BaseType.
pub trait GeneratorOp<S: BaseType, T: BaseType>: BoundaryOperatorIdentity {
    type Error;
    fn generate(&self, input: &S) -> Result<T, Self::Error>;
}

/// AdapterOp: bridges external representations into verified internal BaseType bounds.
pub trait AdapterOp<S, T: BaseType>: BoundaryOperatorIdentity {
    type Error;
    fn adapt(&self, input: &S) -> Result<T, Self::Error>;
}

/// DecoderOp: explicit structural type deserialization.
pub trait DecoderOp<S: BaseType, T: BaseType>: BoundaryOperatorIdentity {
    type Error;
    fn decode(&self, input: &S) -> Result<T, Self::Error>;
}

/// EncoderOp: explicit structural type serialization.
pub trait EncoderOp<S: BaseType, T: BaseType>: BoundaryOperatorIdentity {
    type Error;
    fn encode(&self, input: &S) -> Result<T, Self::Error>;
}

// Origin: engine/crates_rs/core_contracts/src/traits_operators.rs
// Claim: urn:core:crates_rs:core-contracts:traits-operators:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord176d8a80 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord176d8a80` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError176d8a80 {
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
impl BoundaryError176d8a80 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError176d8a80 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError176d8a80 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord176d8a80 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError176d8a80> {
        if capacity_bound == 0 {
            return Err(BoundaryError176d8a80::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError176d8a80::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError176d8a80::ExceedsCapacity {
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
mod l4_boundary_tests_176d8a80 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord176d8a80::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord176d8a80::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord176d8a80::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord176d8a80::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord176d8a80::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError176d8a80::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError176d8a80::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
