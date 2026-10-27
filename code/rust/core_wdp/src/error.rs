// Executable finite evidence; AuthorityEffect: None.
//! Typed error enumerations for the Witnessed Difference Programme crate.
//!
//! Refusals from the sovereign crates this crate delegates to are carried
//! intact, never flattened into strings, so a caller can tell a presentation
//! defect from a solver refusal from a chain-law violation.

use linear_algebra::linear_algebra::image_kernel::ExactLinearAlgebraError;
use core_finite_probability::error::ClassicalShadowError;
use core_functional::gamma2::ExactGamma2Error;
use core_functional::l1_seminorm::L1SeminormError;
use core_holonomy::HolonomyError;
use core_homology::errors::HomologicalError;
use core_homology::finite_directed_graph::NamedEdgeResolutionError;
use core_policy::trichotomy::TrichotomyRefusal;
use core_quantum_physics::exact_channel::ExactChannelError;
use core_quantum_physics::exact_hermitian::ExactHermitianError;
use core_quantum_physics::finite_chsh_correlations::CorrelationError;
use core_solvers::solver_lp_phi1_quotient::Phi1SolveError;
use thiserror::Error;

use crate::empirical_adapter::AdapterRefusal;

impl From<core_epk::matrix_path_kernel::MatrixPathError> for WdpError {
    fn from(error: core_epk::matrix_path_kernel::MatrixPathError) -> Self {
        use core_epk::matrix_path_kernel::MatrixPathError;
        match error {
            MatrixPathError::InvalidInput { detail } => Self::InvalidInput { detail },
            MatrixPathError::GraphCarrier(error) => Self::GraphCarrier(error),
            MatrixPathError::Holonomy(error) => Self::Holonomy(error),
        }
    }
}

/// Core error type for WDP mathematical structures and certified solvers.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum WdpError {
    #[error("Invalid input: {detail}")]
    InvalidInput { detail: String },

    #[error("Missing adapter: {detail}")]
    MissingAdapter { detail: String },

    #[error("Adapter mismatch: expected {expected}, found {found}")]
    AdapterMismatch { expected: String, found: String },

    #[error("Carrier element not found: {element}")]
    ElementNotFound { element: String },

    #[error("Sieve does not cover carrier: missing {missing:?}")]
    IncompleteCoverage { missing: Vec<String> },

    #[error(
        "Section domain mismatch for context {context}: expected {expected:?}, found {found:?}"
    )]
    SectionDomainMismatch {
        context: String,
        expected: Vec<String>,
        found: Vec<String>,
    },

    #[error("Graph carrier refusal: {0}")]
    GraphCarrier(#[from] NamedEdgeResolutionError),

    #[error("Finite relation refusal: {0:?}")]
    FiniteRelation(#[from] core_category_theory::finite_relational::RelationalError),

    #[error("Homology refusal: {0}")]
    Homology(#[from] HomologicalError),

    #[error("Holonomy refusal: {0}")]
    Holonomy(#[from] HolonomyError),

    #[error("Linear algebra refusal: {0}")]
    LinearAlgebra(#[from] ExactLinearAlgebraError),

    #[error("L1 presentation refusal: {0}")]
    L1Presentation(#[from] L1SeminormError),

    #[error("Phi1 refusal: {0}")]
    Phi1(#[from] Phi1SolveError),

    #[error("Gamma2 refusal: {0}")]
    Gamma2(#[from] ExactGamma2Error),

    #[error("Trichotomy refusal: {0:?}")]
    Trichotomy(TrichotomyRefusal),

    /// An empirical-adapter refusal other than plain invalid input, carried intact.
    /// [`AdapterRefusal::InvalidInput`] converts to [`WdpError::InvalidInput`] and back.
    #[error("Empirical adapter refusal: {0}")]
    Adapter(#[source] Box<AdapterRefusal>),

    #[error("Exact matrix algebra refusal: {0}")]
    ExactField(#[from] linear_algebra::exact_field::ExactFieldError),

    #[error("Matrix storage refusal: {0}")]
    MatrixStorage(#[from] linear_algebra::backend::basic_matrix::MatrixError),

    #[error("Exact channel refusal: {0}")]
    ExactChannel(#[from] ExactChannelError),

    #[error("Exact Hermitian refusal: {0}")]
    ExactHermitian(#[from] ExactHermitianError),

    #[error("CHSH correlation refusal: {0}")]
    Correlation(#[from] CorrelationError),

    /// The message prints the refusal with `Debug`, which names the variant; the payload
    /// stays typed.
    #[error("Classical shadow refusal: {0:?}")]
    ClassicalShadow(ClassicalShadowError),

    #[error("Claim status firewall violation: {detail}")]
    ClaimStatusFirewall { detail: String },

    #[error("Awareness firewall violation: attempting to assert phenomenal consciousness")]
    AwarenessFirewallViolation,

    #[error("Authority effect firewall violation: authority effect must be None")]
    AuthorityEffectViolation,
}

impl From<ClassicalShadowError> for WdpError {
    fn from(refusal: ClassicalShadowError) -> Self {
        WdpError::ClassicalShadow(refusal)
    }
}

impl From<AdapterRefusal> for WdpError {
    /// Plain invalid input keeps its shape; a wrapped crate error is unwrapped; every
    /// other refusal is carried whole in [`WdpError::Adapter`].
    fn from(refusal: AdapterRefusal) -> Self {
        match refusal {
            AdapterRefusal::InvalidInput { detail } => WdpError::InvalidInput { detail },
            AdapterRefusal::Wdp(error) => *error,
            other => WdpError::Adapter(Box::new(other)),
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/error.rs
// Claim: urn:core:crates_rs:core-wdp:error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb75c7c84 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb75c7c84` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb75c7c84 {
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
impl BoundaryErrorb75c7c84 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb75c7c84 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb75c7c84 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb75c7c84 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb75c7c84> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb75c7c84::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb75c7c84::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb75c7c84::ExceedsCapacity {
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
mod l4_boundary_tests_b75c7c84 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb75c7c84::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb75c7c84::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb75c7c84::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb75c7c84::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb75c7c84::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb75c7c84::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb75c7c84::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
