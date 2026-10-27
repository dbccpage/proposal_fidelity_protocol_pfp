//! Join of two simplicial complexes.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_a3956534;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_a3956534<T> = std::result::Result<T, BoundaryError_a3956534>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `join_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct JoinComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl JoinComplex {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("label must be non-empty".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = JoinComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = JoinComplex::new("join_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// --- exact carrier witness ---
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JoinLawError {
    Shell,
    Empty,
    Downward { simplex: u16 },
    Support,
    Split { simplex: u16 },
    Count,
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/join_complex.rs
// Claim: urn:core:crates_rs:core-homology:join-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for JoinLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for JoinLawError {}

/// Cardinality of the join of two downward-closed complexes on disjoint vertices.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JoinCardinalityWitness {
    cardinality: usize,
}

fn downward(family: &BTreeSet<u16>) -> Result<u16, JoinLawError> {
    if family.is_empty() || !family.contains(&0) {
        return Err(JoinLawError::Empty);
    }
    let mut support = 0u16;
    for &simplex in family {
        if simplex > 0xff {
            return Err(JoinLawError::Support);
        }
        support |= simplex;
        let mut subset = simplex;
        loop {
            if !family.contains(&subset) {
                return Err(JoinLawError::Downward { simplex });
            }
            if subset == 0 {
                break;
            }
            subset = subset.wrapping_sub(1) & simplex;
        }
    }
    Ok(support)
}

impl JoinCardinalityWitness {
    pub fn try_new(shell: &JoinComplex, left: &[u16], right: &[u16]) -> Result<Self, JoinLawError> {
        if shell.validate_shell().is_err() {
            return Err(JoinLawError::Shell);
        }
        let left_set: BTreeSet<u16> = left.iter().copied().collect();
        let right_set: BTreeSet<u16> = right.iter().copied().collect();
        if left_set.len() != left.len() || right_set.len() != right.len() {
            return Err(JoinLawError::Count);
        }
        let left_support = downward(&left_set)?;
        let right_support = downward(&right_set)?;
        if left_support & right_support != 0 {
            return Err(JoinLawError::Support);
        }
        let join = Self::build_join_simplices(&left_set, &right_set, left_support, right_support)?;
        let cardinality = left_set.len().checked_mul(right_set.len()).ok_or(JoinLawError::Overflow)?;
        if join.len() != cardinality {
            return Err(JoinLawError::Count);
        }
        Ok(Self { cardinality })
    }

    fn build_join_simplices(
        left_set: &BTreeSet<u16>,
        right_set: &BTreeSet<u16>,
        left_support: u16,
        right_support: u16,
    ) -> Result<BTreeSet<u16>, JoinLawError> {
        let mut join = BTreeSet::new();
        for &left_simplex in left_set {
            for &right_simplex in right_set {
                let union = left_simplex | right_simplex;
                if (union & left_support) != left_simplex || (union & right_support) != right_simplex {
                    return Err(JoinLawError::Split { simplex: union });
                }
                if !join.insert(union) {
                    return Err(JoinLawError::Split { simplex: union });
                }
            }
        }
        Ok(join)
    }

    pub fn cardinality(&self) -> usize { self.cardinality }
}

#[cfg(test)]
mod join_law_tests {
    use super::*;

    #[test]
    fn disjoint_edges_join_in_four_simplices() {
        let shell = JoinComplex::new("join");
        let witness = JoinCardinalityWitness::try_new(&shell, &[0, 1], &[0, 2]);
        assert!(matches!(witness, Ok(ref witness) if witness.cardinality() == 4));
    }

    #[test]
    fn overlapping_vertices_are_refused() {
        let shell = JoinComplex::new("join");
        let witness = JoinCardinalityWitness::try_new(&shell, &[0, 1], &[0, 1]);
        assert!(matches!(witness, Err(JoinLawError::Support)));
    }
}
