//! Strongly typed errors, operational limits, and Soviet allocation helpers for core_holonomy.
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (claim hygiene, zero floats).

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Strongly typed error enum for discrete holonomy operations.
///
/// Enforces strict precedence:
/// AllocationFailure > SingularConnection > OpenLoop > VertexNotFound > EdgeNotFound > DimensionMismatch > PathLengthExceeded.
#[derive(Debug, Clone, PartialEq, Eq, Error, Serialize, Deserialize)]
pub enum HolonomyError {
    #[error("resource element count overflows usize")]
    ResourceCountOverflow,
    #[error("Builder allocation failure: requested {requested} elements ({detail})")]
    AllocationFailure { requested: usize, detail: String },

    #[error("Singular or non-invertible connection matrix on edge ({src}, {tgt}): {detail}")]
    SingularConnection {
        src: String,
        tgt: String,
        detail: String,
    },

    #[error("Loop is open: start vertex '{start}' != end vertex '{end}'")]
    OpenLoop { start: String, end: String },

    #[error("Vertex '{id}' not found in cell complex")]
    VertexNotFound { id: String },

    #[error("Edge ({src}, {tgt}) not found in cell complex connection registry")]
    EdgeNotFound { src: String, tgt: String },

    #[error("Dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    #[error("Path length exceeded: length {length}, limit {limit}")]
    PathLengthExceeded { length: usize, limit: usize },

    #[error("Loop count exceeded: count {count}, limit {limit}")]
    LoopCountExceeded { count: usize, limit: usize },

    #[error("Operation limit exceeded: limit {limit}, requested {requested}")]
    OperationLimitExceeded { limit: usize, requested: usize },

    #[error("Malformed path: path must contain at least 2 vertices (got {length})")]
    MalformedPath { length: usize },

    #[error("Empty path rejected: path must contain at least 2 vertices")]
    EmptyPath,

    #[error("Duplicate vertex declared: '{id}'")]
    DuplicateVertex { id: String },

    #[error("Duplicate edge declared: ({src}, {tgt})")]
    DuplicateEdge { src: String, tgt: String },

    #[error("Duplicate face declared: '{id}'")]
    DuplicateFace { id: String },

    #[error("Face '{id}' not found in cell complex")]
    FaceNotFound { id: String },

    #[error("Face boundary cycle mismatch: face '{face}' does not form a closed cycle: {detail}")]
    BoundaryCycleMismatch { face: String, detail: String },

    #[error("Division by zero in exact rational field arithmetic")]
    ZeroDivision,

    #[error("Non-Hermitian connection Laplacian at ({u}, {v}): {detail}")]
    NonHermitianLaplacian {
        u: String,
        v: String,
        detail: String,
    },

    #[error("Curvature commutator violation: {detail}")]
    CurvatureCommutatorViolation { detail: String },

    #[error("Negative bound: {quantity} = {value} must be non-negative")]
    NegativeBound { quantity: String, value: String },

    /// A matrix with no inverse, outside any edge: `ExactMatrix::inverse`
    /// reports this, and `DiscreteConnection::set_connection` turns it into
    /// `SingularConnection` with the edge attached.
    #[error("Singular matrix: {detail}")]
    SingularMatrix { detail: String },

    /// An edge index beyond the complex: the edge-indexed connection and walk
    /// API of `gauge_fixing` names edges by index, not by vertex pair.
    #[error("Edge index {index} is out of range: the complex has {edge_count} edges")]
    EdgeIndexOutOfRange { index: usize, edge_count: usize },

    #[error("Vertex index {index} is out of range: the complex has {vertex_count} vertices")]
    VertexIndexOutOfRange { index: usize, vertex_count: usize },

    #[error("Expected one value per edge ({expected} edges) but got {actual} values")]
    EdgeValueCount { expected: usize, actual: usize },

    #[error("Expected one gauge value per vertex ({expected} vertices) but got {actual} values")]
    VertexValueCount { expected: usize, actual: usize },

    /// A `(source, target)`-keyed connection stores one matrix per vertex pair
    /// and treats the opposite direction as its inverse, so two edges joining
    /// the same vertices in opposite directions cannot carry independent values.
    #[error(
        "Edges {first} and {second} join the same vertices in opposite directions; a \
         (source, target)-keyed connection cannot give them independent values"
    )]
    AntiparallelEdges { first: usize, second: usize },

    #[error("Walk is broken at step {step}: {detail}")]
    BrokenWalk { step: usize, detail: String },

    #[error("Step {step} has direction {direction}; a step direction is +1 or -1")]
    InvalidStepDirection { step: usize, direction: i8 },

    #[error("Invalid group order {order}: a finite cyclic group has order at least 1")]
    InvalidGroupOrder { order: u64 },

    #[error("Exact integer elimination failed: {detail}")]
    IntegerEliminationFailed { detail: String },
}

impl HolonomyError {
    /// Returns the precedence rank of this error (lower integer = higher priority).
    pub fn precedence_rank(&self) -> usize {
        self.rank_tier_0()
            .or_else(|| self.rank_tier_1())
            .or_else(|| self.rank_tier_2())
            .unwrap_or_else(|| self.rank_tier_3())
    }

    fn rank_tier_0(&self) -> Option<usize> {
        match self {
            HolonomyError::ResourceCountOverflow => Some(0),
            HolonomyError::AllocationFailure { .. } => Some(1),
            HolonomyError::SingularConnection { .. } => Some(2),
            HolonomyError::OpenLoop { .. } => Some(3),
            HolonomyError::VertexNotFound { .. } => Some(4),
            HolonomyError::EdgeNotFound { .. } => Some(5),
            HolonomyError::DimensionMismatch { .. } => Some(6),
            HolonomyError::PathLengthExceeded { .. } => Some(7),
            _ => None,
        }
    }

    fn rank_tier_1(&self) -> Option<usize> {
        match self {
            HolonomyError::LoopCountExceeded { .. } => Some(8),
            HolonomyError::OperationLimitExceeded { .. } => Some(9),
            HolonomyError::MalformedPath { .. } => Some(10),
            HolonomyError::EmptyPath => Some(11),
            HolonomyError::DuplicateVertex { .. } => Some(12),
            HolonomyError::DuplicateEdge { .. } => Some(13),
            HolonomyError::DuplicateFace { .. } => Some(14),
            HolonomyError::FaceNotFound { .. } => Some(15),
            _ => None,
        }
    }

    fn rank_tier_2(&self) -> Option<usize> {
        match self {
            HolonomyError::BoundaryCycleMismatch { .. } => Some(16),
            HolonomyError::ZeroDivision => Some(17),
            HolonomyError::NonHermitianLaplacian { .. } => Some(18),
            HolonomyError::CurvatureCommutatorViolation { .. } => Some(19),
            HolonomyError::NegativeBound { .. } => Some(20),
            HolonomyError::SingularMatrix { .. } => Some(21),
            HolonomyError::EdgeIndexOutOfRange { .. } => Some(22),
            HolonomyError::VertexIndexOutOfRange { .. } => Some(23),
            _ => None,
        }
    }

    fn rank_tier_3(&self) -> usize {
        match self {
            HolonomyError::EdgeValueCount { .. } => 24,
            HolonomyError::VertexValueCount { .. } => 25,
            HolonomyError::AntiparallelEdges { .. } => 26,
            HolonomyError::BrokenWalk { .. } => 27,
            HolonomyError::InvalidStepDirection { .. } => 28,
            HolonomyError::InvalidGroupOrder { .. } => 29,
            HolonomyError::IntegerEliminationFailed { .. } => 30,
            _ => 0,
        }
    }
}

/// Resource admission is owned by the kernel; holonomy preserves its domain error.
impl From<core_kernel::resource_limits::ResourceError> for HolonomyError {
    fn from(error: core_kernel::resource_limits::ResourceError) -> Self {
        use core_kernel::resource_limits::ResourceError;
        match error {
            ResourceError::AllocationFailure { requested, detail } => {
                Self::AllocationFailure { requested, detail }
            }
            ResourceError::CountOverflow | ResourceError::DimensionOverflow => {
                Self::ResourceCountOverflow
            }
            ResourceError::HilbertDimensionExceeded { requested, limit }
            | ResourceError::OperatorCountExceeded { requested, limit }
            | ResourceError::BasisStateCountExceeded { requested, limit }
            | ResourceError::KrausRankExceeded { requested, limit } => {
                Self::OperationLimitExceeded { requested, limit }
            }
            ResourceError::NonPositiveDimension => Self::DimensionMismatch {
                expected: 1,
                actual: 0,
            },
        }
    }
}

/// Exact carrier witness.
/// Precedence is the total order of `precedence_rank`: rank 0 is highest, and each later error is exactly one rank lower.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PrecedenceChainError {
    Empty,
    NotInitial,
    Outranked { index: usize, earlier: usize, later: usize },
    Incomplete,
    Overflow,
}

impl HolonomyError {
    pub fn certify_precedence_chain(chain: &[HolonomyError]) -> Result<usize, PrecedenceChainError> {
        let first = chain.first().ok_or(PrecedenceChainError::Empty)?;
        if !matches!(first, HolonomyError::ResourceCountOverflow) || first.precedence_rank() != 0 {
            return Err(PrecedenceChainError::NotInitial);
        }
        let previous = Self::verify_chain_monotonicity(chain)?;
        let last = chain.last().ok_or(PrecedenceChainError::Empty)?;
        if !matches!(last, HolonomyError::IntegerEliminationFailed { .. }) {
            return Err(PrecedenceChainError::Incomplete);
        }
        let covered = last.precedence_rank().checked_add(1).ok_or(PrecedenceChainError::Overflow)?;
        if covered != chain.len() || previous != last.precedence_rank() {
            return Err(PrecedenceChainError::Incomplete);
        }
        Ok(chain.len())
    }

    fn verify_chain_monotonicity(chain: &[HolonomyError]) -> Result<usize, PrecedenceChainError> {
        let mut previous = 0usize;
        let mut index = 1usize;
        while index < chain.len() {
            let later = chain.get(index).ok_or(PrecedenceChainError::Empty)?.precedence_rank();
            let expected = previous.checked_add(1).ok_or(PrecedenceChainError::Overflow)?;
            if later != expected || later <= previous {
                return Err(PrecedenceChainError::Outranked { index, earlier: previous, later });
            }
            previous = later;
            index = index.checked_add(1).ok_or(PrecedenceChainError::Overflow)?;
        }
        Ok(previous)
    }
}

// Origin: engine/crates_rs/core_holonomy/src/error.rs
// Claim: urn:core:crates_rs:core-holonomy:error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
fn ordered_holonomy_errors() -> Vec<HolonomyError> {
    vec![
        HolonomyError::ResourceCountOverflow,
        HolonomyError::AllocationFailure { requested: 1, detail: "allocation".into() },
        HolonomyError::SingularConnection { src: "s".into(), tgt: "t".into(), detail: "singular".into() },
        HolonomyError::OpenLoop { start: "a".into(), end: "b".into() },
        HolonomyError::VertexNotFound { id: "v".into() },
        HolonomyError::EdgeNotFound { src: "s".into(), tgt: "t".into() },
        HolonomyError::DimensionMismatch { expected: 2, actual: 1 },
        HolonomyError::PathLengthExceeded { length: 3, limit: 2 },
        HolonomyError::LoopCountExceeded { count: 2, limit: 1 },
        HolonomyError::OperationLimitExceeded { limit: 1, requested: 2 },
        HolonomyError::MalformedPath { length: 1 },
        HolonomyError::EmptyPath,
        HolonomyError::DuplicateVertex { id: "v".into() },
        HolonomyError::DuplicateEdge { src: "s".into(), tgt: "t".into() },
        HolonomyError::DuplicateFace { id: "f".into() },
        HolonomyError::FaceNotFound { id: "f".into() },
        HolonomyError::BoundaryCycleMismatch { face: "f".into(), detail: "open".into() },
        HolonomyError::ZeroDivision,
        HolonomyError::NonHermitianLaplacian { u: "u".into(), v: "v".into(), detail: "skew".into() },
        HolonomyError::CurvatureCommutatorViolation { detail: "commutator".into() },
        HolonomyError::NegativeBound { quantity: "bound".into(), value: "-1".into() },
        HolonomyError::SingularMatrix { detail: "singular".into() },
        HolonomyError::EdgeIndexOutOfRange { index: 2, edge_count: 1 },
        HolonomyError::VertexIndexOutOfRange { index: 2, vertex_count: 1 },
        HolonomyError::EdgeValueCount { expected: 2, actual: 1 },
        HolonomyError::VertexValueCount { expected: 2, actual: 1 },
        HolonomyError::AntiparallelEdges { first: 0, second: 1 },
        HolonomyError::BrokenWalk { step: 1, detail: "gap".into() },
        HolonomyError::InvalidStepDirection { step: 1, direction: 0 },
        HolonomyError::InvalidGroupOrder { order: 0 },
        HolonomyError::IntegerEliminationFailed { detail: "pivot".into() },
    ]
}

#[cfg(test)]
mod tests {
    use super::{ordered_holonomy_errors, HolonomyError, PrecedenceChainError};

    #[test]
    fn documented_order_is_a_complete_unit_step_chain() {
        let chain = ordered_holonomy_errors();
        let width = chain.len();
        assert_eq!(HolonomyError::certify_precedence_chain(&chain), Ok(width));
        assert_eq!(chain.first().map(HolonomyError::precedence_rank), Some(0));
    }

    #[test]
    fn a_later_higher_precedence_does_not_pass() {
        let inverted = vec![
            HolonomyError::ResourceCountOverflow,
            HolonomyError::AllocationFailure { requested: 1, detail: "allocation".into() },
            HolonomyError::ResourceCountOverflow,
        ];
        assert!(matches!(
            HolonomyError::certify_precedence_chain(&inverted),
            Err(PrecedenceChainError::Outranked { earlier: 1, later: 0, .. })
        ));
        assert!(matches!(
            HolonomyError::certify_precedence_chain(&[]),
            Err(PrecedenceChainError::Empty)
        ));
        let skipped = vec![
            HolonomyError::ResourceCountOverflow,
            HolonomyError::OpenLoop { start: "a".into(), end: "b".into() },
        ];
        assert!(matches!(
            HolonomyError::certify_precedence_chain(&skipped),
            Err(PrecedenceChainError::Outranked { earlier: 0, later: 3, .. })
        ));
    }
}
