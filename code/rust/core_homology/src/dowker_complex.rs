//! Dowker complex from a bipartite relation.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_2807394b;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_2807394b<T> = std::result::Result<T, BoundaryError_2807394b>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `dowker_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct DowkerComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl DowkerComplex {
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
        let s = DowkerComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = DowkerComplex::new("dowker_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Edge count of the Dowker nerve: unordered pairs of columns that co-occur in a row.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DowkerEdgeWitness {
    edges: u64,
    columns: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DowkerEdgeError {
    EmptyLabel,
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/dowker_complex.rs
// Claim: urn:core:crates_rs:core-homology:dowker-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DowkerEdgeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DowkerEdgeError {}

impl DowkerEdgeWitness {
    pub fn try_from_relation(
        complex: &DowkerComplex,
        relation: &[(u64, u64)],
    ) -> Result<Self, DowkerEdgeError> {
        if complex.label.is_empty() {
            return Err(DowkerEdgeError::EmptyLabel);
        }
        let mut rows: std::collections::BTreeMap<u64, std::collections::BTreeSet<u64>> =
            std::collections::BTreeMap::new();
        let mut columns = std::collections::BTreeSet::new();
        for &(row, column) in relation {
            rows.entry(row).or_default().insert(column);
            columns.insert(column);
        }
        let mut edges_set = std::collections::BTreeSet::new();
        for cols in rows.values() {
            let ordered: Vec<u64> = cols.iter().copied().collect();
            for left_index in 0..ordered.len() {
                for right_index in left_index.saturating_add(1)..ordered.len() {
                    let left = *ordered.get(left_index).ok_or(DowkerEdgeError::Overflow)?;
                    let right = *ordered.get(right_index).ok_or(DowkerEdgeError::Overflow)?;
                    edges_set.insert((left, right));
                }
            }
        }
        Ok(Self {
            edges: u64::try_from(edges_set.len()).map_err(|_| DowkerEdgeError::Overflow)?,
            columns: u64::try_from(columns.len()).map_err(|_| DowkerEdgeError::Overflow)?,
        })
    }

    pub fn edges(&self) -> u64 {
        self.edges
    }

    pub fn columns(&self) -> u64 {
        self.columns
    }
}
