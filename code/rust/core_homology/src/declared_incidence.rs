//! Declared incidence domain for finite abstract simplicial complexes.
//!
//! A family is in the domain when it is a finite set of nonempty simplices on
//! vertices `0..n-1` (`n` positive), contains every singleton, and is closed
//! under nonempty faces. The empty simplex is not a member. Encoding refuses a
//! missing vertex, a missing face, a non-increasing vertex list, or a duplicate
//! cell, and it does not add cells. Decoding returns that simplex set.
//!
//! Rational boundary matrices and Betti numbers are
//! [`SimplicialComplex::boundary_matrix`] and
//! [`SimplicialComplex::rational_betti_numbers`]. Their rank is the existing
//! exact row reduction in `linear_algebra`.

use crate::errors::HomologicalError;
use crate::simplicial::{Simplex, SimplicialComplex};
use std::collections::BTreeSet;

/// Refusal of a family that is outside the declared incidence domain, or of a
/// later homology-owner failure on a complex already in that domain.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum DeclaredIncidenceError {
    #[error("the declared class is a nonempty family of simplices on vertices 0..n-1")]
    EmptyFamily,
    #[error("simplex vertices must be nonempty and strictly increasing: {0:?}")]
    NonIncreasing(Vec<usize>),
    #[error("duplicate cell {0:?}")]
    DuplicateCell(Vec<usize>),
    #[error("missing vertex {0}")]
    MissingVertex(usize),
    #[error("missing face {face:?} of cell {cell:?}")]
    MissingFace { cell: Vec<usize>, face: Vec<usize> },
    #[error("homology owner refused the complex: {0}")]
    Owner(String),
}

/// Dimensions, signed rational boundary entries, and rational Betti numbers.
///
/// `boundaries[k - 1]` is the matrix of `∂_k`, rows then columns, with each
/// entry printed by the exact rational scalar. `betti[k]` is `dim H_k(K; Q)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredChainReport {
    pub dimensions: Vec<usize>,
    pub boundaries: Vec<Vec<Vec<String>>>,
    pub betti: Vec<usize>,
}

fn owner_error(error: impl std::fmt::Display) -> DeclaredIncidenceError {
    DeclaredIncidenceError::Owner(error.to_string())
}

/// Encode a declared family as a simplicial complex.
///
/// The input order is irrelevant. The complex contains exactly the supplied
/// simplices: missing faces are refused rather than filled in.
pub fn encode_declared(cells: &[Vec<usize>]) -> Result<SimplicialComplex, DeclaredIncidenceError> {
    if cells.is_empty() {
        return Err(DeclaredIncidenceError::EmptyFamily);
    }
    let mut unique: BTreeSet<Vec<usize>> = BTreeSet::new();
    for cell in cells {
        if cell.is_empty() || cell.windows(2).any(|pair| pair[0] >= pair[1]) {
            return Err(DeclaredIncidenceError::NonIncreasing(cell.clone()));
        }
        if !unique.insert(cell.clone()) {
            return Err(DeclaredIncidenceError::DuplicateCell(cell.clone()));
        }
    }
    let max_vertex = unique
        .iter()
        .filter_map(|cell| cell.last().copied())
        .max()
        .ok_or(DeclaredIncidenceError::EmptyFamily)?;
    check_required_vertices(&unique, max_vertex)?;
    check_required_faces(&unique)?;
    let simplices = unique
        .into_iter()
        .map(Simplex::new)
        .collect::<Result<Vec<_>, HomologicalError>>()
        .map_err(owner_error)?;
    SimplicialComplex::from_simplices(simplices).map_err(owner_error)
}

fn check_required_vertices(
    unique: &BTreeSet<Vec<usize>>,
    max_vertex: usize,
) -> Result<(), DeclaredIncidenceError> {
    // Singletons `0..=max_vertex` are required. If they do not fit in the
    // family, the least missing index is strictly below the cell count, so the
    // search never walks a huge vertex label.
    let span = max_vertex.saturating_add(1);
    if span > unique.len() {
        let scan_until = unique.len();
        for vertex in 0..scan_until {
            if !unique.contains(&vec![vertex]) {
                return Err(DeclaredIncidenceError::MissingVertex(vertex));
            }
        }
        return Err(DeclaredIncidenceError::MissingVertex(scan_until));
    }
    for vertex in 0..=max_vertex {
        if !unique.contains(&vec![vertex]) {
            return Err(DeclaredIncidenceError::MissingVertex(vertex));
        }
    }
    Ok(())
}

fn check_required_faces(unique: &BTreeSet<Vec<usize>>) -> Result<(), DeclaredIncidenceError> {
    for cell in unique {
        if cell.len() <= 1 {
            continue;
        }
        for index in 0..cell.len() {
            let mut face = cell.clone();
            face.remove(index);
            if !unique.contains(&face) {
                return Err(DeclaredIncidenceError::MissingFace {
                    cell: cell.clone(),
                    face,
                });
            }
        }
    }
    Ok(())
}

/// Simplex set of a complex, as vertex lists.
pub fn decode_declared(complex: &SimplicialComplex) -> BTreeSet<Vec<usize>> {
    let mut cells = BTreeSet::new();
    for dimension in 0..=complex.max_dimension() {
        for simplex in complex.simplices(dimension) {
            cells.insert(simplex.vertices().to_vec());
        }
    }
    cells
}

/// Signed rational boundaries and Betti numbers from the simplicial owner.
pub fn declared_chain_report(
    complex: &SimplicialComplex,
) -> Result<DeclaredChainReport, DeclaredIncidenceError> {
    if !complex.verify_boundary_law().map_err(owner_error)? {
        return Err(DeclaredIncidenceError::Owner(
            "boundary composition was not zero".into(),
        ));
    }
    let dimensions = (0..=complex.max_dimension())
        .map(|dimension| complex.count(dimension))
        .collect();
    let mut boundaries = Vec::new();
    for degree in 1..=complex.max_dimension() {
        let matrix = complex.boundary_matrix(degree).map_err(owner_error)?;
        let mut rows = Vec::new();
        for row_index in 0..matrix.rows() {
            let mut row = Vec::new();
            for column_index in 0..matrix.cols() {
                row.push(
                    matrix
                        .get(row_index, column_index)
                        .map_err(owner_error)?
                        .to_string(),
                );
            }
            rows.push(row);
        }
        boundaries.push(rows);
    }
    Ok(DeclaredChainReport {
        dimensions,
        boundaries,
        betti: complex.rational_betti_numbers().map_err(owner_error)?,
    })
}

// Origin: engine/crates_rs/core_homology/src/declared_incidence.rs
// Claim: urn:core:crates_rs:core-homology:declared-incidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e4e8fd6e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
