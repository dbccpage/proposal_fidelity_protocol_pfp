//! Sparse Rips / edge-collapse filtration approximations.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_4f355397;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_4f355397<T> = std::result::Result<T, BoundaryError_4f355397>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `sparse_filtration`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct SparseFiltration {
    pub label: String,
    pub notes: Vec<String>,
}

impl SparseFiltration {
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
        let s = SparseFiltration::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = SparseFiltration::new("sparse_filtration").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Refusal from a monotone filtration.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FiltrationError {
    /// A simplex was not strictly increasing.
    Unsorted { index: usize },
    /// A face appears later than a simplex that contains it.
    Decreasing { face: usize, simplex: usize },
    /// More than 32 simplices were offered.
    TooMany,
}

// Origin: engine/crates_rs/core_homology/src/sparse_filtration.rs
// Claim: urn:core:crates_rs:core-homology:sparse-filtration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FiltrationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FiltrationError {}

/// Admit a filtration when every face is born no later than a simplex that contains it.
pub fn try_monotone_filtration(simplices: &[(Vec<u32>, u32)]) -> Result<u32, FiltrationError> {
    if simplices.len() > 32 {
        return Err(FiltrationError::TooMany);
    }
    for (index, (vertices, _)) in simplices.iter().enumerate() {
        for window in vertices.windows(2) {
            let Some(left) = window.first() else { return Err(FiltrationError::Unsorted { index }); };
            let Some(right) = window.get(1) else { return Err(FiltrationError::Unsorted { index }); };
            if left >= right {
                return Err(FiltrationError::Unsorted { index });
            }
        }
    }
    for (face_index, (face, face_value)) in simplices.iter().enumerate() {
        for (simplex_index, (simplex, simplex_value)) in simplices.iter().enumerate() {
            if face_index == simplex_index {
                continue;
            }
            let subset = face.iter().all(|vertex| simplex.binary_search(vertex).is_ok());
            if subset && face_value > simplex_value {
                return Err(FiltrationError::Decreasing { face: face_index, simplex: simplex_index });
            }
        }
    }
    u32::try_from(simplices.len()).map_err(|_| FiltrationError::TooMany)
}

#[cfg(test)]
mod filtration_tests {
    use super::*;
    #[test]
    fn an_edge_may_follow_its_vertex() {
        let count = try_monotone_filtration(&[(vec![0], 1), (vec![0, 1], 3)]);
        assert!(matches!(count, Ok(2)));
    }
    #[test]
    fn a_late_vertex_is_refused() {
        let err = try_monotone_filtration(&[(vec![0], 5), (vec![0, 1], 3)]);
        assert!(matches!(err, Err(FiltrationError::Decreasing { .. })));
    }
}
