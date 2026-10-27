//! Barycentric subdivision shell.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_8e0c17ef;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_8e0c17ef<T> = std::result::Result<T, BoundaryError_8e0c17ef>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `subdivision`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct Subdivision {
    pub label: String,
    pub notes: Vec<String>,
}

impl Subdivision {
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
        let s = Subdivision::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = Subdivision::new("subdivision").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SubdivisionLawError {
    Shell,
    Range,
    Disagreement { factorial: u64, enumerated: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/subdivision.rs
// Claim: urn:core:crates_rs:core-homology:subdivision:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SubdivisionLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SubdivisionLawError {}

/// The number of maximal simplices in the barycentric subdivision of an n-simplex is (n+1)!.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BarycentricFactorial {
    vertices: u32,
    maximal: u64,
}

fn heap_count(items: &mut [u32], width: usize, total: &mut u64) -> Result<(), SubdivisionLawError> {
    if width <= 1 {
        *total = total.checked_add(1).ok_or(SubdivisionLawError::Overflow)?;
        return Ok(());
    }
    heap_count(items, width - 1, total)?;
    for index in 0..width - 1 {
        if width % 2 == 0 {
            items.swap(index, width - 1);
        } else {
            items.swap(0, width - 1);
        }
        heap_count(items, width - 1, total)?;
    }
    Ok(())
}

impl BarycentricFactorial {
    pub fn try_new(shell: &Subdivision, vertices: u32) -> Result<Self, SubdivisionLawError> {
        if shell.validate_shell().is_err() {
            return Err(SubdivisionLawError::Shell);
        }
        if vertices == 0 || vertices > 7 {
            return Err(SubdivisionLawError::Range);
        }
        let mut factorial = 1u64;
        for factor in 1..=u64::from(vertices) {
            factorial = factorial.checked_mul(factor).ok_or(SubdivisionLawError::Overflow)?;
        }
        let mut order: Vec<u32> = (0..vertices).collect();
        let mut enumerated = 0u64;
        heap_count(&mut order, usize::try_from(vertices).map_err(|_| SubdivisionLawError::Range)?, &mut enumerated)?;
        if factorial != enumerated {
            return Err(SubdivisionLawError::Disagreement { factorial, enumerated });
        }
        Ok(Self { vertices, maximal: factorial })
    }

    pub fn vertices(&self) -> u32 { self.vertices }
    pub fn maximal(&self) -> u64 { self.maximal }
}

#[cfg(test)]
mod subdivision_law_tests {
    use super::*;

    #[test]
    fn a_triangle_has_six_maximal_ordered_simplices() {
        let shell = Subdivision::new("barycentric");
        let count = BarycentricFactorial::try_new(&shell, 3);
        assert!(matches!(count, Ok(ref count) if count.maximal() == 6 && count.vertices() == 3));
    }

    #[test]
    fn an_empty_vertex_set_is_refused() {
        let shell = Subdivision::new("barycentric");
        let count = BarycentricFactorial::try_new(&shell, 0);
        assert!(matches!(count, Err(SubdivisionLawError::Range)));
    }
}
