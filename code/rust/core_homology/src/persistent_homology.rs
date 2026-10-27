//! Finite simplicial persistent homology over F2 with exact rational filtration values.
//! AuthorityEffect: None. Executable finite computation, not a formal proof.

use crate::barcode::Barcode;
use crate::filtration::{FilteredSimplex, Filtration};
use crate::persistence_diagram::{PersistenceDiagram, PersistencePoint};
use crate::persistence_pairing::PersistencePairing;
use crate::ph_matrix_reduction::PhBoundaryMatrix;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum PersistentHomologyError {
    #[error("filtration and boundary sizes differ")]
    SizeMismatch,
    #[error("filtration values must be nondecreasing")]
    UnorderedFiltration,
    #[error("invalid simplex or boundary at index {0}")]
    InvalidSimplex(usize),
    #[error("only the F2 coefficient field is implemented")]
    UnsupportedCoefficientField,
    #[error("requested dimension omits part of the declared filtration")]
    DimensionMismatch,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PersistentHomologyResult {
    pub diagram: PersistenceDiagram,
    pub pairing: PersistencePairing,
}

/// Validate the actual simplicial boundary before any in-place reduction.
pub fn compute_persistent_homology(
    filtration: &Filtration,
    boundary: &mut PhBoundaryMatrix,
) -> Result<PersistentHomologyResult, PersistentHomologyError> {
    if filtration.len() != boundary.n() {
        return Err(PersistentHomologyError::SizeMismatch);
    }
    if !filtration.values_nondecreasing() {
        return Err(PersistentHomologyError::UnorderedFiltration);
    }
    validate_filtration_boundary(filtration, boundary)?;
    let pairing = boundary.reduce_z2();
    let mut points = Vec::new();
    for (creator, destroyer) in pairing.pairs.iter().enumerate() {
        let simplex = &filtration.simplices[creator];
        let birth = simplex.value.clone();
        match destroyer {
            Some(d) => {
                let death = filtration.simplices[*d].value.clone();
                if death > birth {
                    points.push(PersistencePoint::finite(birth, death, simplex.dimension));
                }
            }
            None if boundary.columns[creator].is_empty() => {
                points.push(PersistencePoint::infinite(birth, simplex.dimension));
            }
            None => {}
        }
    }
    Ok(PersistentHomologyResult {
        diagram: PersistenceDiagram::new(points),
        pairing,
    })
}

fn expected_simplex_faces(
    simplex: &FilteredSimplex,
    j: usize,
    seen: &BTreeMap<Vec<usize>, usize>,
) -> Result<Vec<usize>, PersistentHomologyError> {
    let mut expected = Vec::new();
    if simplex.dimension > 0 {
        for removed in 0..simplex.vertices.len() {
            let mut face = simplex.vertices.clone();
            face.remove(removed);
            let index = seen
                .get(&face)
                .copied()
                .ok_or(PersistentHomologyError::InvalidSimplex(j))?;
            expected.push(index);
        }
        expected.sort_unstable();
    }
    Ok(expected)
}

fn validate_filtration_boundary(
    filtration: &Filtration,
    boundary: &PhBoundaryMatrix,
) -> Result<(), PersistentHomologyError> {
    let mut seen = BTreeMap::new();
    for (j, simplex) in filtration.simplices.iter().enumerate() {
        if simplex.vertices.len().checked_sub(1) != Some(simplex.dimension)
            || simplex.dimension > filtration.max_dimension
            || !simplex.vertices.windows(2).all(|v| v[0] < v[1])
            || seen.contains_key(&simplex.vertices)
        {
            return Err(PersistentHomologyError::InvalidSimplex(j));
        }
        let expected = expected_simplex_faces(simplex, j, &seen)?;
        if boundary.columns[j].rows != expected {
            return Err(PersistentHomologyError::InvalidSimplex(j));
        }
        seen.insert(simplex.vertices.clone(), j);
    }
    Ok(())
}

pub fn barcode_from_result(r: &PersistentHomologyResult) -> Barcode {
    Barcode::from_diagram(&r.diagram)
}

// Origin: engine/crates_rs/core_homology/src/persistent_homology.rs
// Claim: urn:core:crates_rs:core-homology:persistent-homology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::filtration::FilteredSimplex;
    use crate::ph_matrix_reduction::SparseColumn;
    use num_rational::BigRational;

    fn edge() -> (Filtration, PhBoundaryMatrix) {
        let tenth = BigRational::new(1.into(), 10.into());
        let f = Filtration::new(
            vec![
                FilteredSimplex {
                    vertices: vec![0],
                    value: tenth.clone(),
                    dimension: 0,
                },
                FilteredSimplex {
                    vertices: vec![1],
                    value: tenth,
                    dimension: 0,
                },
                FilteredSimplex {
                    vertices: vec![0, 1],
                    value: BigRational::new(3.into(), 10.into()),
                    dimension: 1,
                },
            ],
            1,
        );
        let m = PhBoundaryMatrix {
            columns: vec![
                SparseColumn { rows: vec![] },
                SparseColumn { rows: vec![] },
                SparseColumn { rows: vec![0, 1] },
            ],
        };
        (f, m)
    }

    #[test]
    fn exact_tenth_and_essential_component_are_preserved() {
        let (f, mut m) = edge();
        let r = compute_persistent_homology(&f, &mut m).unwrap();
        assert_eq!(r.diagram.points.len(), 2);
        let finite = r.diagram.finite_only().next().unwrap();
        assert_eq!(finite.birth, BigRational::new(1.into(), 10.into()));
        assert_eq!(finite.death, Some(BigRational::new(3.into(), 10.into())));
        assert_eq!(
            finite.persistence(),
            Some(BigRational::new(1.into(), 5.into()))
        );
        assert_eq!(
            r.diagram.points.iter().filter(|p| p.is_infinite()).count(),
            1
        );
        assert_eq!(barcode_from_result(&r).bars[1].birth, finite.birth);
    }

    #[test]
    fn malformed_boundary_is_refused_before_mutation() {
        let (f, mut m) = edge();
        m.columns[2].rows = vec![3];
        let before = m.clone();
        assert_eq!(
            compute_persistent_homology(&f, &mut m),
            Err(PersistentHomologyError::InvalidSimplex(2))
        );
        assert_eq!(m, before);
    }

    #[test]
    fn mismatched_size_and_unordered_values_are_refused() {
        let (mut f, mut m) = edge();
        f.simplices[2].value = BigRational::from_integer(0.into());
        assert_eq!(
            compute_persistent_homology(&f, &mut m),
            Err(PersistentHomologyError::UnorderedFiltration)
        );
        m.columns.pop();
        assert_eq!(
            compute_persistent_homology(&f, &mut m),
            Err(PersistentHomologyError::SizeMismatch)
        );
    }

    #[test]
    fn trivial_empty_ph() {
        let f = Filtration::new(vec![], 0);
        let mut m = PhBoundaryMatrix { columns: vec![] };
        assert!(compute_persistent_homology(&f, &mut m)
            .unwrap()
            .diagram
            .points
            .is_empty());
    }
}
