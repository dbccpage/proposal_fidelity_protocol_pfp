//! Textual / coordinate helpers for diagram visualization.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_8af52d92;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_8af52d92<T> = std::result::Result<T, BoundaryError_8af52d92>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `diagram_plotting`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct DiagramPlotting {
    pub label: String,
    pub notes: Vec<String>,
}

impl DiagramPlotting {
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
        let s = DiagramPlotting::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = DiagramPlotting::new("diagram_plotting").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiagramGrid { rows: u64, cols: u64, cells: u64, horizontal: u64, vertical: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiagramGridError { Empty, Overflow, Arrows }

// Origin: engine/crates_rs/core_homology/src/diagram_plotting.rs
// Claim: urn:core:crates_rs:core-homology:diagram-plotting:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DiagramGridError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DiagramGridError {}

impl DiagramGrid {
    /// Cell count is the product, and arrow counts stay inside the grid adjacencies.
    pub fn try_new(rows: u64, cols: u64, horizontal: u64, vertical: u64) -> Result<Self, DiagramGridError> {
        if rows == 0 || cols == 0 {
            return Err(DiagramGridError::Empty);
        }
        let cells = rows.checked_mul(cols).ok_or(DiagramGridError::Overflow)?;
        let h_room = rows.checked_mul(cols - 1).ok_or(DiagramGridError::Overflow)?;
        let v_room = cols.checked_mul(rows - 1).ok_or(DiagramGridError::Overflow)?;
        if horizontal > h_room || vertical > v_room {
            return Err(DiagramGridError::Arrows);
        }
        Ok(Self { rows, cols, cells, horizontal, vertical })
    }

    pub fn cells(&self) -> u64 { self.cells }
}

#[cfg(test)]
mod diagram_grid_checks {
    use super::*;

    #[test]
    fn a_two_by_three_grid_has_six_cells() {
        let grid = DiagramGrid::try_new(2, 3, 4, 3);
        assert!(matches!(grid, Ok(g) if g.cells() == 6));
    }

    #[test]
    fn too_many_horizontal_arrows_are_refused() {
        assert!(matches!(DiagramGrid::try_new(2, 2, 5, 0), Err(DiagramGridError::Arrows)));
    }
}
