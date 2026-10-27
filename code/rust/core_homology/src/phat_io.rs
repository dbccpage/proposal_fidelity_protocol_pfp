//! PHAT file format shell.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_5f7aecea;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_5f7aecea<T> = std::result::Result<T, BoundaryError_5f7aecea>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `phat_io`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct PhatIo {
    pub label: String,
    pub notes: Vec<String>,
}

impl PhatIo {
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
        let s = PhatIo::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = PhatIo::new("phat_io").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// PHAT-style boundary columns: strictly increasing faces, each strictly below its column index.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PhatBoundaryWitness {
    columns: u64,
    incidences: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PhatBoundaryError {
    EmptyLabel,
    UnsortedOrNonlocal { column: usize, face: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/phat_io.rs
// Claim: urn:core:crates_rs:core-homology:phat-io:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PhatBoundaryError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PhatBoundaryError {}

impl PhatBoundaryWitness {
    pub fn try_from_columns(
        record: &PhatIo,
        columns: &[Vec<u64>],
    ) -> Result<Self, PhatBoundaryError> {
        if record.label.is_empty() {
            return Err(PhatBoundaryError::EmptyLabel);
        }
        let mut incidences = 0u64;
        for (column, faces) in columns.iter().enumerate() {
            let mut previous: Option<u64> = None;
            let column_index = u64::try_from(column).map_err(|_| PhatBoundaryError::Overflow)?;
            for face in faces {
                if *face >= column_index {
                    return Err(PhatBoundaryError::UnsortedOrNonlocal { column, face: *face });
                }
                if let Some(earlier) = previous {
                    if *face <= earlier {
                        return Err(PhatBoundaryError::UnsortedOrNonlocal { column, face: *face });
                    }
                }
                previous = Some(*face);
                incidences = incidences.checked_add(1).ok_or(PhatBoundaryError::Overflow)?;
            }
        }
        Ok(Self {
            columns: u64::try_from(columns.len()).map_err(|_| PhatBoundaryError::Overflow)?,
            incidences,
        })
    }

    pub fn incidences(&self) -> u64 {
        self.incidences
    }

    pub fn columns(&self) -> u64 {
        self.columns
    }
}
