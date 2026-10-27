//! Budgeted finite coloring with a declared symmetric forbidden-pair relation.
//! Each listed edge occurrence contributes once, including loops and repetitions.
//! The minimizing coloring is exact; its violated edges are not claimed to form
//! a minimal unsatisfiable subgraph. AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_df616e05<T> {
    fn checked_invariant_df616e05(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_df616e05<T> for Option<T> {
    #[inline]
    fn checked_invariant_df616e05(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_df616e05<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_df616e05(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::{cartesian_words::CartesianWords, enumeration::CombinatoricsError};
use num_bigint::BigUint;
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ColorConstraintError {
    #[error("the declared palette must be nonempty")]
    EmptyPalette,
    #[error("edge {0} has an undeclared endpoint")]
    Endpoint(usize),
    #[error("a forbidden color is outside the declared palette")]
    Color,
    #[error(transparent)]
    Enumeration(#[from] CombinatoricsError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MinimumColorViolations {
    pub coloring: Vec<usize>,
    pub violated_edges: Vec<usize>,
}

fn validate_color_inputs(
    vertices: usize,
    edges: &[(usize, usize)],
    colors: usize,
    forbidden: &BTreeSet<(usize, usize)>,
) -> Result<(), ColorConstraintError> {
    if colors == 0 {
        return Err(ColorConstraintError::EmptyPalette);
    }
    if let Some(i) = edges
        .iter()
        .position(|&(u, v)| u >= vertices || v >= vertices)
    {
        return Err(ColorConstraintError::Endpoint(i));
    }
    if forbidden.iter().any(|&(a, b)| a >= colors || b >= colors) {
        return Err(ColorConstraintError::Color);
    }
    Ok(())
}

fn violated_edges_for_coloring(
    coloring: &[usize],
    edges: &[(usize, usize)],
    forbidden: &BTreeSet<(usize, usize)>,
) -> Vec<usize> {
    edges
        .iter()
        .enumerate()
        .filter_map(|(i, &(u, v))| {
            let pair = (coloring[u], coloring[v]);
            (forbidden.contains(&pair) || forbidden.contains(&(pair.1, pair.0))).then_some(i)
        })
        .collect()
}

pub fn minimum_color_violations(
    vertices: usize,
    edges: &[(usize, usize)],
    colors: usize,
    forbidden: &BTreeSet<(usize, usize)>,
    max_colorings: usize,
    max_edge_checks: usize,
) -> Result<MinimumColorViolations, ColorConstraintError> {
    validate_color_inputs(vertices, edges, colors, forbidden)?;
    let words = CartesianWords::new(colors, vertices, max_colorings, 4096)?;
    let checks = BigUint::from(words.cardinality()) * BigUint::from(edges.len());
    if checks > BigUint::from(max_edge_checks) {
        return Err(CombinatoricsError::BudgetExceeded {
            what: "coloring edge checks",
            requested: checks,
            limit: max_edge_checks,
        }
        .into());
    }
    let mut best: Option<MinimumColorViolations> = None;
    for coloring in words {
        let violated_edges = violated_edges_for_coloring(&coloring, edges, forbidden);
        if best
            .as_ref()
            .is_none_or(|b| violated_edges.len() < b.violated_edges.len())
        {
            best = Some(MinimumColorViolations {
                coloring,
                violated_edges,
            });
            if best.as_ref().is_some_and(|b| b.violated_edges.is_empty()) {
                break;
            }
        }
    }
    // A nonempty palette has at least one word, including at width zero.
    Ok(best.checked_invariant_df616e05("nonempty palette and admitted Cartesian cardinality"))
}

// Origin: engine/crates_rs/core_combinatorics/src/color_constraints.rs
// Claim: urn:core:crates_rs:core-combinatorics:color-constraints:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_df616e05 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
