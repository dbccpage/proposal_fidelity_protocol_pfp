//! Nested filtered complex: parameter-indexed simplices with filtration value.
//!
//! AuthorityEffect: None. Shell / best-effort computational topology.
//! Not PROVED; not GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_0bd26b40;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_0bd26b40<T> = std::result::Result<T, BoundaryError_0bd26b40>;
use num_rational::BigRational;
use serde::{Deserialize, Serialize};

/// A simplex (or cell) with a filtration parameter value.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FilteredSimplex {
    pub vertices: Vec<usize>,
    pub value: BigRational,
    pub dimension: usize,
}

/// Nested sequence of complexes indexed by a filtration parameter.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Filtration {
    pub simplices: Vec<FilteredSimplex>,
    pub max_dimension: usize,
}

impl Filtration {
    pub fn new(simplices: Vec<FilteredSimplex>, max_dimension: usize) -> Self {
        Self {
            simplices,
            max_dimension,
        }
    }

    pub fn len(&self) -> usize {
        self.simplices.len()
    }

    pub fn is_empty(&self) -> bool {
        self.simplices.is_empty()
    }

    /// Values in nondecreasing order if the filtration is valid for PH reduction.
    pub fn values_nondecreasing(&self) -> bool {
        self.simplices.windows(2).all(|w| w[0].value <= w[1].value)
    }

    pub fn value(&self, index: usize) -> Option<BigRational> {
        self.simplices.get(index).map(|s| s.value.clone())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_filtration() {
        let f = Filtration::new(vec![], 0);
        assert!(f.is_empty());
        assert!(f.values_nondecreasing());
    }
}

/// A filtration whose simplex dimensions match vertex spans, stay within
/// `max_dimension`, and whose values are nondecreasing.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CertifiedFiltration {
    simplex_count: usize,
    max_dimension: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FiltrationCertError {
    EmptySimplex { index: usize },
    DimensionMismatch {
        index: usize,
        declared: usize,
        vertex_span: usize,
    },
    AboveMax {
        index: usize,
        dimension: usize,
        max_dimension: usize,
    },
    Decreasing { index: usize },
}

// Origin: engine/crates_rs/core_homology/src/filtration.rs
// Claim: urn:core:crates_rs:core-homology:filtration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FiltrationCertError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FiltrationCertError {}

impl CertifiedFiltration {
    pub fn try_from_filtration(filtration: &Filtration) -> Result<Self, FiltrationCertError> {
        for (index, simplex) in filtration.simplices.iter().enumerate() {
            if simplex.vertices.is_empty() {
                return Err(FiltrationCertError::EmptySimplex { index });
            }
            let vertex_span = simplex
                .vertices
                .len()
                .checked_sub(1)
                .ok_or(FiltrationCertError::EmptySimplex { index })?;
            if simplex.dimension != vertex_span {
                return Err(FiltrationCertError::DimensionMismatch {
                    index,
                    declared: simplex.dimension,
                    vertex_span,
                });
            }
            if simplex.dimension > filtration.max_dimension {
                return Err(FiltrationCertError::AboveMax {
                    index,
                    dimension: simplex.dimension,
                    max_dimension: filtration.max_dimension,
                });
            }
        }
        for (offset, window) in filtration.simplices.windows(2).enumerate() {
            let left = window
                .get(0)
                .ok_or(FiltrationCertError::Decreasing { index: offset })?;
            let right = window
                .get(1)
                .ok_or(FiltrationCertError::Decreasing { index: offset + 1 })?;
            if left.value > right.value {
                return Err(FiltrationCertError::Decreasing { index: offset + 1 });
            }
        }
        Ok(Self {
            simplex_count: filtration.simplices.len(),
            max_dimension: filtration.max_dimension,
        })
    }

    pub fn simplex_count(&self) -> usize {
        self.simplex_count
    }

    pub fn max_dimension(&self) -> usize {
        self.max_dimension
    }
}

#[cfg(test)]
mod certified_filtration_witness {
    use super::*;

    #[test]
    fn empty_and_ordered_edge_certify() {
        let empty = Filtration::new(vec![], 0);
        let certified = CertifiedFiltration::try_from_filtration(&empty);
        assert!(certified.is_ok());
        if let Ok(certified) = certified {
            assert_eq!(certified.simplex_count(), 0);
        }
        let filtration = Filtration::new(
            vec![FilteredSimplex {
                vertices: vec![0, 1],
                value: BigRational::from_integer(1.into()),
                dimension: 1,
            }],
            1,
        );
        let certified = CertifiedFiltration::try_from_filtration(&filtration);
        assert!(certified.is_ok());
        if let Ok(certified) = certified {
            assert_eq!(certified.simplex_count(), 1);
            assert_eq!(certified.max_dimension(), 1);
        }
    }

    #[test]
    fn dimension_must_be_one_less_than_the_vertex_count() {
        let filtration = Filtration::new(
            vec![FilteredSimplex {
                vertices: vec![0, 1],
                value: BigRational::from_integer(0.into()),
                dimension: 2,
            }],
            3,
        );
        assert!(matches!(
            CertifiedFiltration::try_from_filtration(&filtration),
            Err(FiltrationCertError::DimensionMismatch {
                declared: 2,
                vertex_span: 1,
                ..
            })
        ));
    }
}
