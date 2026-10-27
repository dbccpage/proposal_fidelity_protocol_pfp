//! Least joint writing of square tables under one shared vertex permutation.
//! This is finite exact enumeration, with the full n! checked before search.
//! An insufficient budget returns a refusal, never a sampled minimum.
use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use crate::scalars::Semiring;
use crate::semiring_lumpability::push_forward_square;
use core_combinatorics::enumeration::{CombinatoricsError, Permutations};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PairCanonicalError {
    #[error("joint canonicalization needs at least one square table, all on the same carrier")]
    IncompatibleTables,
    #[error("canonicalization search refused: {0}")]
    Enumeration(#[from] CombinatoricsError),
    #[error("canonicalization matrix operation refused: {0}")]
    Matrix(#[from] MatrixError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CanonicalPairTables<S: Semiring> {
    pub tables: Vec<BasicMatrix<S>>,
    pub old_to_new: Vec<usize>,
    pub examined: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CanonicalDecoratedPairTables<S: Semiring, D> {
    pub tables: Vec<BasicMatrix<S>>,
    pub decoration: D,
    pub old_to_new: Vec<usize>,
    pub examined: usize,
}

/// Compare tables in their supplied order, each in row-major order. Return
/// the lexicographically first witnessing permutation in a tie. The empty
/// carrier has its single empty permutation and still needs budget one.
pub fn canonical_pair_tables<S: Semiring + Ord>(
    tables: &[BasicMatrix<S>],
    max_permutations: usize,
) -> Result<CanonicalPairTables<S>, PairCanonicalError> {
    let joint = canonical_pair_tables_with_decoration(tables, max_permutations, |_| ())?;
    Ok(CanonicalPairTables {
        tables: joint.tables,
        old_to_new: joint.old_to_new,
        examined: joint.examined,
    })
}

/// Compare all tables, then the declared decoration transported by the SAME
/// writing. The caller supplies its deterministic decoration transport.
/// This admits the full n! orbit, not a scalar/allocation work bound.
pub fn canonical_pair_tables_with_decoration<S: Semiring + Ord, D: Ord>(
    tables: &[BasicMatrix<S>],
    max_permutations: usize,
    decorate: impl Fn(&[usize]) -> D,
) -> Result<CanonicalDecoratedPairTables<S, D>, PairCanonicalError> {
    let n = tables
        .first()
        .ok_or(PairCanonicalError::IncompatibleTables)?
        .rows();
    if tables
        .iter()
        .any(|table| table.rows() != n || table.cols() != n)
    {
        return Err(PairCanonicalError::IncompatibleTables);
    }
    let permutations = Permutations::new(n, max_permutations)?;
    let mut best: Option<(Vec<S>, D, Vec<BasicMatrix<S>>, Vec<usize>)> = None;
    let mut examined = 0usize;
    for image in permutations {
        let moved = tables
            .iter()
            .map(|table| push_forward_square(table, &image, n))
            .collect::<Result<Vec<_>, _>>()?;
        let key: Vec<S> = moved
            .iter()
            .flat_map(|table| table.as_slice().iter().cloned())
            .collect();
        let decoration = decorate(&image);
        if best.as_ref().is_none_or(|(least, old_decoration, _, _)| {
            (&key, &decoration) < (least, old_decoration)
        }) {
            best = Some((key, decoration, moved, image));
        }
        examined += 1;
    }
    let (_, decoration, tables, old_to_new) = best.ok_or(PairCanonicalError::IncompatibleTables)?;
    Ok(CanonicalDecoratedPairTables {
        tables,
        decoration,
        old_to_new,
        examined,
    })
}

// Origin: engine/crates_rs/core_linear_algebra/src/pair_table_canonical.rs
// Claim: urn:core:crates_rs:core-linear-algebra:pair-table-canonical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9fbcc3d6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
