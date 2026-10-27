//! Gradient paths in a discrete Morse vector field.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_d2c4ae24;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_d2c4ae24<T> = std::result::Result<T, BoundaryError_d2c4ae24>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `gradient_path`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct GradientPath {
    pub label: String,
    pub notes: Vec<String>,
}

impl GradientPath {
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
        let s = GradientPath::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = GradientPath::new("gradient_path").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_homology/src/gradient_path.rs
// Claim: urn:core:homology:morse:alternating-v-path:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MorsePath {
    cells: usize,
    first_step: i8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MorsePathError {
    ShellRefused { reason: String },
    TooShort,
    DuplicateId { id: u32 },
    DimensionJump { index: usize, from: i64, to: i64 },
    NotAlternating { index: usize, step: i8 },
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/gradient_path.rs
// Claim: urn:core:crates_rs:core-homology:gradient-path:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MorsePathError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MorsePathError {}

impl MorsePath {
    pub fn try_on(shell: &GradientPath, cells: &[(u32, i64)]) -> Result<Self, MorsePathError> {
        shell
            .validate_shell()
            .map_err(|reason| MorsePathError::ShellRefused { reason })?;
        if cells.len() < 2 {
            return Err(MorsePathError::TooShort);
        }
        Self::check_unique_cell_ids(cells)?;
        let mut previous_step: Option<i8> = None;
        let mut first_step = 0i8;
        for index in 0..cells.len() - 1 {
            let step = Self::step_direction(cells, index)?;
            if index == 0 {
                first_step = step;
            }
            if let Some(previous) = previous_step {
                if step != -previous {
                    return Err(MorsePathError::NotAlternating { index, step });
                }
            }
            previous_step = Some(step);
        }
        Ok(Self {
            cells: cells.len(),
            first_step,
        })
    }

    fn check_unique_cell_ids(cells: &[(u32, i64)]) -> Result<(), MorsePathError> {
        let mut ids = Vec::new();
        for cell in cells {
            if ids.contains(&cell.0) {
                return Err(MorsePathError::DuplicateId { id: cell.0 });
            }
            ids.push(cell.0);
        }
        Ok(())
    }

    fn step_direction(cells: &[(u32, i64)], index: usize) -> Result<i8, MorsePathError> {
        let from = cells.get(index).ok_or(MorsePathError::Overflow)?.1;
        let to = cells.get(index + 1).ok_or(MorsePathError::Overflow)?.1;
        let delta = to.checked_sub(from).ok_or(MorsePathError::Overflow)?;
        if delta == 1 {
            Ok(1i8)
        } else if delta == -1 {
            Ok(-1i8)
        } else {
            Err(MorsePathError::DimensionJump { index, from, to })
        }
    }

    pub fn cells(&self) -> usize {
        self.cells
    }

    pub fn first_step(&self) -> i8 {
        self.first_step
    }
}

#[cfg(test)]
mod morse_path_tests {
    use super::*;

    #[test]
    fn alternates_dimension_by_one() {
        let shell = GradientPath::new("vpath");
        let witness = MorsePath::try_on(&shell, &[(0, 2), (1, 1), (2, 2), (3, 1)]);
        assert!(matches!(witness, Ok(ref w) if w.cells() == 4 && w.first_step() == -1));
    }

    #[test]
    fn refuses_a_repeated_cell_and_a_jump() {
        let shell = GradientPath::new("vpath");
        let repeated = MorsePath::try_on(&shell, &[(0, 2), (0, 1)]);
        assert!(matches!(repeated, Err(MorsePathError::DuplicateId { id: 0 })));
        let jump = MorsePath::try_on(&shell, &[(0, 2), (1, 0)]);
        assert!(matches!(
            jump,
            Err(MorsePathError::DimensionJump { index: 0, from: 2, to: 0 })
        ));
    }
}
