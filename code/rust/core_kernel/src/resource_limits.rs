//! Resource limits and the typed refusals of finite mathematical constructors.
//!
//! Every admitted dense mathematical object (a Hilbert carrier `C^n`, an `n x n` operator, a
//! Kraus family, a tensor product of `k` factors) costs memory polynomial in the
//! dimension, and a constructor that multiplies dimensions silently can overflow
//! `usize` or ask for terabytes. [`OperationLimits`] states the declared ceilings and
//! its `check_*` methods are consulted by the constructors that allocate from caller
//! data (finite linear carriers and operator families): a request beyond a ceiling is a typed [`ResourceError`] carrying the
//! requested size and the limit, never a panic and never an allocation.
//!
//! - [`OperationLimits::check_hilbert_dim`]: `1 <= d <= max_hilbert_dim`.
//! - [`OperationLimits::checked_product`]: overflow-free product of two sizes.
//! - [`OperationLimits::check_operator_count`], [`OperationLimits::check_kraus_rank`]:
//!   bounds on families of operators.
//! - [`check_and_reserve`]: fallible reservation in a `Vec`, with checked arithmetic.
//!
//! The limits are policy, not mathematics: a computation that fits no limit is
//! refused, not wrong, and the ceilings can be raised by constructing another
//! `OperationLimits`.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

/// Declared ceilings for the dense objects of the finite-dimensional faces.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default)]
pub struct OperationLimits {
    pub max_vertices: usize,
    pub max_edges: usize,
    pub max_faces: usize,
    pub max_dimension: usize,
    pub max_path_length: usize,
    pub max_loops: usize,
    pub max_cells: usize,
    pub max_operations: usize,
    pub max_hilbert_dim: usize,
    pub max_operators: usize,
    pub max_basis_states: usize,
    pub max_kraus_rank: usize,
    pub max_cyclotomic_conductor: usize,
    pub max_memory_bytes: usize,
}

impl Default for OperationLimits {
    fn default() -> Self {
        Self {
            max_vertices: 10_000,
            max_edges: 50_000,
            max_faces: 50_000,
            max_dimension: 64,
            max_path_length: 1_000,
            max_loops: 5_000,
            max_cells: 10_000,
            max_operations: 1_000_000,
            max_hilbert_dim: 1024,
            max_operators: 4096,
            max_basis_states: 2048,
            max_kraus_rank: 64,
            max_cyclotomic_conductor: 120,
            max_memory_bytes: 33554432, // 32 MB
        }
    }
}

impl OperationLimits {
    /// Preserve the finite quantum carrier policy used by exact state constructors.
    pub fn quantum() -> Self {
        Self::default()
    }

    /// Preserve the distinct cell-complex memory ceiling used by holonomy.
    pub fn holonomy() -> Self {
        Self {
            max_memory_bytes: 10_485_760,
            ..Self::default()
        }
    }

    /// Explicit unbounded policy; checked integer overflow still refuses.
    pub fn unlimited() -> Self {
        Self {
            max_hilbert_dim: usize::MAX,
            max_operators: usize::MAX,
            max_basis_states: usize::MAX,
            max_kraus_rank: usize::MAX,
            max_cyclotomic_conductor: usize::MAX,
            max_memory_bytes: usize::MAX,
            max_vertices: usize::MAX,
            max_edges: usize::MAX,
            max_faces: usize::MAX,
            max_dimension: usize::MAX,
            max_path_length: usize::MAX,
            max_loops: usize::MAX,
            max_cells: usize::MAX,
            max_operations: usize::MAX,
        }
    }
    /// `d` when `1 <= d <= max_hilbert_dim`; a zero dimension is
    /// [`ResourceError::NonPositiveDimension`], a larger one
    /// [`ResourceError::HilbertDimensionExceeded`].
    pub fn check_hilbert_dim(&self, dim: usize) -> Result<usize, ResourceError> {
        if dim == 0 {
            return Err(ResourceError::NonPositiveDimension);
        }
        if dim > self.max_hilbert_dim {
            return Err(ResourceError::HilbertDimensionExceeded {
                requested: dim,
                limit: self.max_hilbert_dim,
            });
        }
        Ok(dim)
    }

    /// `a * b`, or [`ResourceError::DimensionOverflow`] when it does not fit in `usize`.
    pub fn checked_product(&self, a: usize, b: usize) -> Result<usize, ResourceError> {
        a.checked_mul(b).ok_or(ResourceError::DimensionOverflow)
    }

    /// Preflight a dense allocation and its element-size memory budget.
    pub fn check_dense_matrix(
        &self,
        rows: usize,
        cols: usize,
        element_bytes: usize,
    ) -> Result<usize, ResourceError> {
        self.check_hilbert_dim(rows)?;
        self.check_hilbert_dim(cols)?;
        let entries = self.checked_product(rows, cols)?;
        let bytes = self.checked_product(entries, element_bytes)?;
        if bytes > self.max_memory_bytes {
            return Err(ResourceError::AllocationFailure {
                requested: bytes,
                detail: "dense matrix exceeds declared memory budget".into(),
            });
        }
        Ok(entries)
    }

    /// `n` when `n <= max_operators`.
    pub fn check_operator_count(&self, n: usize) -> Result<usize, ResourceError> {
        if n > self.max_operators {
            return Err(ResourceError::OperatorCountExceeded {
                requested: n,
                limit: self.max_operators,
            });
        }
        Ok(n)
    }

    /// `n` when `n <= max_kraus_rank`.
    pub fn check_kraus_rank(&self, n: usize) -> Result<usize, ResourceError> {
        if n > self.max_kraus_rank {
            return Err(ResourceError::KrausRankExceeded {
                requested: n,
                limit: self.max_kraus_rank,
            });
        }
        Ok(n)
    }

    /// `n` when `n <= max_basis_states`.
    pub fn check_basis_states(&self, n: usize) -> Result<usize, ResourceError> {
        if n > self.max_basis_states {
            return Err(ResourceError::BasisStateCountExceeded {
                requested: n,
                limit: self.max_basis_states,
            });
        }
        Ok(n)
    }
}

/// The refusals of the dimension and allocation checks, and the structural refusals
/// shared by the exact constructors.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ResourceError {
    AllocationFailure {
        requested: usize,
        detail: String,
    },
    HilbertDimensionExceeded {
        requested: usize,
        limit: usize,
    },
    OperatorCountExceeded {
        requested: usize,
        limit: usize,
    },
    BasisStateCountExceeded {
        requested: usize,
        limit: usize,
    },
    KrausRankExceeded {
        requested: usize,
        limit: usize,
    },
    NonPositiveDimension,
    DimensionOverflow,
    /// A length plus a requested extension does not fit in `usize`.
    CountOverflow,
}

impl std::fmt::Display for ResourceError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::AllocationFailure { requested, detail } => {
                write!(
                    f,
                    "Allocation failure: requested {requested} elements ({detail})"
                )
            }
            Self::HilbertDimensionExceeded { requested, limit } => {
                write!(f, "Hilbert dimension {requested} exceeds limit {limit}")
            }
            Self::OperatorCountExceeded { requested, limit } => {
                write!(f, "Operator count {requested} exceeds limit {limit}")
            }
            Self::BasisStateCountExceeded { requested, limit } => {
                write!(f, "Basis state count {requested} exceeds limit {limit}")
            }
            Self::KrausRankExceeded { requested, limit } => {
                write!(f, "Kraus rank {requested} exceeds limit {limit}")
            }
            Self::NonPositiveDimension => write!(f, "Dimension must be strictly positive"),
            Self::DimensionOverflow => write!(f, "Matrix dimension multiplication overflow"),
            Self::CountOverflow => write!(f, "Element count overflows usize"),
        }
    }
}

impl std::error::Error for ResourceError {}

/// Fallible reservation of `additional` more elements in `vec`, refused when the
/// resulting length exceeds `limit` or does not fit in `usize`, or when the allocator
/// refuses. Nothing is allocated on a refusal.
pub fn check_and_reserve<T>(
    vec: &mut Vec<T>,
    additional: usize,
    limit: usize,
) -> Result<(), ResourceError> {
    let total = vec
        .len()
        .checked_add(additional)
        .ok_or(ResourceError::CountOverflow)?;
    if total > limit {
        return Err(ResourceError::AllocationFailure {
            requested: total,
            detail: format!("exceeds limit {}", limit),
        });
    }
    vec.try_reserve_exact(additional)
        .map_err(|e| ResourceError::AllocationFailure {
            requested: additional,
            detail: e.to_string(),
        })
}

// Origin: engine/crates_rs/core_kernel/src/resource_limits.rs
// Claim: urn:core:crates_rs:core-kernel:resource-limits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shared_resource_policies_preserve_limits_and_refuse_overflow_even_when_unbounded() {
        let quantum = OperationLimits::quantum();
        let holonomy = OperationLimits::holonomy();
        assert_eq!(quantum.max_hilbert_dim, 1024);
        assert_eq!(quantum.max_kraus_rank, 64);
        assert_eq!(quantum.max_memory_bytes, 33_554_432);
        assert_eq!(holonomy.max_dimension, 64);
        assert_eq!(holonomy.max_vertices, 10_000);
        assert_eq!(holonomy.max_memory_bytes, 10_485_760);
        assert_eq!(
            OperationLimits::unlimited().checked_product(usize::MAX, 2),
            Err(ResourceError::DimensionOverflow)
        );
        let mut vector = vec![1u8];
        assert_eq!(
            check_and_reserve(&mut vector, usize::MAX, usize::MAX),
            Err(ResourceError::CountOverflow)
        );
        assert_eq!(vector, vec![1]);
        let tiny = OperationLimits {
            max_memory_bytes: 31,
            ..quantum
        };
        assert!(matches!(
            tiny.check_dense_matrix(2, 2, 8),
            Err(ResourceError::AllocationFailure { requested: 32, .. })
        ));
        assert_eq!(tiny.check_dense_matrix(1, 2, 8), Ok(2));
    }

    #[test]
    fn hilbert_dimension_is_checked_against_zero_and_the_ceiling() {
        let limits = OperationLimits::default();
        assert_eq!(
            limits.check_hilbert_dim(0),
            Err(ResourceError::NonPositiveDimension)
        );
        assert_eq!(limits.check_hilbert_dim(1), Ok(1));
        assert_eq!(limits.check_hilbert_dim(1024), Ok(1024));
        assert_eq!(
            limits.check_hilbert_dim(1025),
            Err(ResourceError::HilbertDimensionExceeded {
                requested: 1025,
                limit: 1024
            })
        );
    }

    #[test]
    fn a_product_that_overflows_is_refused_not_wrapped() {
        let limits = OperationLimits::default();
        assert_eq!(limits.checked_product(6, 7), Ok(42));
        assert_eq!(
            limits.checked_product(usize::MAX, 2),
            Err(ResourceError::DimensionOverflow)
        );
    }

    #[test]
    fn reserve_refuses_length_arithmetic_that_overflows() {
        let mut v: Vec<u8> = vec![0; 3];
        // `len + additional` overflows usize: the unchecked sum panicked in debug
        // builds and wrapped, so passed the limit test, in release builds.
        assert_eq!(
            check_and_reserve(&mut v, usize::MAX, usize::MAX),
            Err(ResourceError::CountOverflow)
        );
        assert_eq!(v.len(), 3);
    }

    #[test]
    fn reserve_refuses_beyond_the_limit_and_allocates_within_it() {
        let mut v: Vec<u8> = Vec::new();
        assert!(matches!(
            check_and_reserve(&mut v, 11, 10),
            Err(ResourceError::AllocationFailure { requested: 11, .. })
        ));
        assert_eq!(check_and_reserve(&mut v, 10, 10), Ok(()));
        assert!(v.capacity() >= 10);
    }
}
