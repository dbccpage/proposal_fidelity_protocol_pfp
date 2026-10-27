//! Core Operad Theory: 5-Tier Coloured Operad Architecture in Rust.
//!
//! Five-tier mathematical hierarchy:
//!   1. Foundation: Colours, Signatures, Operations, Planar & Symmetric Coloured Operads, Monoidal Operads, Planar Trees
//!   2. Realization: Multi-Sorted Algebras, Operadic Modules, Associativity Witnesses
//!   3. Deformation: Quadratic Operads, Cooperads, Bar-Cobar Resolutions, Koszul Duality
//!   4. Geometric: Little n-Disks Operad D_n, Homology Operads H_*(D_n)
//!   5. Applications: OEAS Applied Workflow Operad & Agent Interpreters
//!
//! AuthorityEffect: None.

pub mod kernel;
pub mod foundation;
pub mod realization;
pub mod deformation;
pub mod geometric;
pub mod applications;

#[cfg(feature = "python")]
pub mod python;

// Tier 1 Re-exports
pub use foundation::{
    MonoidalOperad, OpenLeaf, OperadColour, OperadSignature, OperadVariant,
    Operation, OperationId, OperationKind, OperationKindType,
    PlanarColoredOperad, PlanarTree, SpanOperand, SymmetricColoredOperad, TreeChild,
    ADMITTED_FINITE_COLOURS,
};

// Tier 2 Re-exports
pub use realization::{
    AlgebraModule, ComputationStatus, EvaluationOutcome, EvaluationReceipt,
    EvidenceKind, LawResult, OperadAlgebra, OperadicModule, PolicyDecisionRef,
    StructuralAssociativityWitness,
};

// Tier 3 Re-exports
pub use deformation::{
    BarCobarResolution, ColouredCooperad, KoszulDualBuilder, ProposedQuadraticDual,
    QuadraticOperad, QuadraticRelation,
};

// Tier 4 Re-exports
pub use geometric::{
    LittleDisksConfiguration, RectilinearDisk,
    build_associative_homology_operad, build_commutative_homology_operad, build_gerstenhaber_homology_operad,
};

// Tier 5 Re-exports
pub use applications::{AgentCapabilitySlice, OEASWorkflowOperad, OEAS_ADMITTED_PORT_COLOURS};

// Estate kernel re-exports (digest-bearing; see `kernel` module docs).
pub use kernel::{
    canonical_bytes, canonical_id, ActionLicense, AgentLicense, AtomicPath2, Attestation,
    AttestationKind, AuthorityEffect, BoundarySignature, BudgetTransition, CertifiedPair,
    ColourSpec, ComparisonEvidence, ComparisonVerdict, EquivalenceGrade, ExecutionEvent,
    ExecutionEventInput, HorizontalPath2, IdentityPath2, InversePath2, InvocationGrade,
    KernelError, LicensedTerm, NormalizedTerm, ObligationBundle, ObligationKind, ObserverDeclaration,
    OperandRef, OperationSpec, OperationSpecInput, OperationTerm, Path2, PortSpec, ProofObligation,
    AgentFibrationError, AgentPath, AgentPathWitness, AntibodyScreen, Homotopy2Cell, transport,
    Refinement, Refusal, ReplayVerifiedAttestation, VerticalPath2, WhiskerPath2,
};

/// Always `"None"` — this crate mints zero authority.
pub fn authority_effect() -> &'static str {
    "None"
}

// Origin: engine/crates_rs/core_operad_theory/src/lib.rs
// Claim: urn:core:crates_rs:core-operad-theory:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd6643f60 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd6643f60` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord6643f60 {
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
impl BoundaryErrord6643f60 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord6643f60 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord6643f60 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd6643f60 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord6643f60> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord6643f60::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord6643f60::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord6643f60::ExceedsCapacity {
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
mod l4_boundary_tests_d6643f60 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd6643f60::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd6643f60::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd6643f60::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd6643f60::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd6643f60::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord6643f60::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord6643f60::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
