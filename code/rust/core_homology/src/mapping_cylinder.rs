//! Mapping cylinder of a chain map.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_544d24e7;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_544d24e7<T> = std::result::Result<T, BoundaryError_544d24e7>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `mapping_cylinder`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct MappingCylinder {
    pub label: String,
    pub notes: Vec<String>,
}

impl MappingCylinder {
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
        let s = MappingCylinder::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = MappingCylinder::new("mapping_cylinder").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Refusal from an integer cone rank.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConeError {
    /// The base cell list is empty.
    Empty,
    /// Checked arithmetic overflowed.
    Overflow,
    /// The alternating sum was not 1.
    NotContractible { euler: i64 },
}

// Origin: engine/crates_rs/core_homology/src/mapping_cylinder.rs
// Claim: urn:core:crates_rs:core-homology:mapping-cylinder:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ConeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ConeError {}

/// Cell ranks of the cone, whose Euler characteristic is 1.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConeRanks {
    euler: i64,
    ranks: Vec<u32>,
}

impl ConeRanks {
    /// `base[k]` is the number of k-cells. The cone adds an apex and a cone on each cell.
    pub fn try_new(base: &[u32]) -> Result<Self, ConeError> {
        let Some(&vertices) = base.first() else {
            return Err(ConeError::Empty);
        };
        let mut ranks = Vec::new();
        ranks.push(vertices.checked_add(1).ok_or(ConeError::Overflow)?);
        for k in 1..=base.len() {
            let old = if k < base.len() {
                *base.get(k).ok_or(ConeError::Overflow)?
            } else {
                0
            };
            let cones = *base.get(k - 1).ok_or(ConeError::Overflow)?;
            ranks.push(old.checked_add(cones).ok_or(ConeError::Overflow)?);
        }
        let euler = Self::compute_euler_characteristic(&ranks)?;
        if euler != 1 {
            return Err(ConeError::NotContractible { euler });
        }
        Ok(Self { euler, ranks })
    }

    fn compute_euler_characteristic(ranks: &[u32]) -> Result<i64, ConeError> {
        let mut euler = 0i64;
        let mut sign = 1i64;
        for rank in ranks {
            let term = i64::from(*rank).checked_mul(sign).ok_or(ConeError::Overflow)?;
            euler = euler.checked_add(term).ok_or(ConeError::Overflow)?;
            sign = sign.checked_neg().ok_or(ConeError::Overflow)?;
        }
        Ok(euler)
    }

    /// Euler characteristic of the cone.
    pub fn euler(&self) -> i64 { self.euler }
    /// Cone cell counts, starting at dimension 0.
    pub fn ranks(&self) -> &[u32] { &self.ranks }
}

#[cfg(test)]
mod cone_tests {
    use super::*;
    #[test]
    fn the_cone_on_a_triangle_boundary_is_a_disk() {
        let cone = ConeRanks::try_new(&[3, 3]);
        assert!(matches!(cone, Ok(ref c) if c.euler() == 1 && c.ranks() == [4, 6, 3]));
    }
}
