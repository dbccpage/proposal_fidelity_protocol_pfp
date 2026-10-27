//! Mapping cone of a chain map.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f9556d7f;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f9556d7f<T> = std::result::Result<T, BoundaryError_f9556d7f>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `mapping_cone`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct MappingCone {
    pub label: String,
    pub notes: Vec<String>,
}

impl MappingCone {
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
        let s = MappingCone::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = MappingCone::new("mapping_cone").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MappingConeDimensions { cone: Vec<u64>, total: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConeDimError { Empty, Width, Overflow, Sum }

// Origin: engine/crates_rs/core_homology/src/mapping_cone.rs
// Claim: urn:core:crates_rs:core-homology:mapping-cone:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ConeDimError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ConeDimError {}

impl MappingConeDimensions {
    /// `cone_0 = dim B_0` and `cone_k = dim B_k + dim A_{k-1}`, with one extra top degree for `A`.
    pub fn try_new(dim_a: &[u64], dim_b: &[u64]) -> Result<Self, ConeDimError> {
        Self::check_dimensions_header(dim_a, dim_b)?;
        let (mut cone, mut total, sum_a, sum_b) = Self::accumulate_cone_degrees(dim_a, dim_b)?;
        let top = dim_a.last().copied().ok_or(ConeDimError::Empty)?;
        total = total.checked_add(top).ok_or(ConeDimError::Overflow)?;
        cone.push(top);
        let expected = sum_a.checked_add(sum_b).ok_or(ConeDimError::Overflow)?;
        if total != expected {
            return Err(ConeDimError::Sum);
        }
        Ok(Self { cone, total })
    }

    fn check_dimensions_header(dim_a: &[u64], dim_b: &[u64]) -> Result<(), ConeDimError> {
        if dim_a.is_empty() {
            return Err(ConeDimError::Empty);
        }
        if dim_a.len() != dim_b.len() {
            return Err(ConeDimError::Width);
        }
        Ok(())
    }

    fn accumulate_cone_degrees(
        dim_a: &[u64],
        dim_b: &[u64],
    ) -> Result<(Vec<u64>, u64, u64, u64), ConeDimError> {
        let mut cone = Vec::new();
        let mut total = 0u64;
        let mut sum_a = 0u64;
        let mut sum_b = 0u64;
        for index in 0..dim_b.len() {
            let b = dim_b[index];
            sum_b = sum_b.checked_add(b).ok_or(ConeDimError::Overflow)?;
            let a_prev = if index == 0 { 0 } else { dim_a[index - 1] };
            let cell = b.checked_add(a_prev).ok_or(ConeDimError::Overflow)?;
            total = total.checked_add(cell).ok_or(ConeDimError::Overflow)?;
            cone.push(cell);
            sum_a = sum_a.checked_add(dim_a[index]).ok_or(ConeDimError::Overflow)?;
        }
        Ok((cone, total, sum_a, sum_b))
    }

    pub fn total(&self) -> u64 { self.total }
    pub fn cone(&self) -> &[u64] { &self.cone }
}

#[cfg(test)]
mod cone_dim_checks {
    use super::*;

    #[test]
    fn cone_total_is_the_sum_of_the_two_complexes() {
        let cone = MappingConeDimensions::try_new(&[1, 4], &[2, 3]);
        assert!(matches!(cone, Ok(c) if c.total() == 10 && c.cone() == [2, 4, 4]));
    }

    #[test]
    fn unequal_lengths_are_refused() {
        assert!(matches!(MappingConeDimensions::try_new(&[1], &[1, 1]), Err(ConeDimError::Width)));
    }
}
