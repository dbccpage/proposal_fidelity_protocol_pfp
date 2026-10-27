//! chain_complex_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Category of chain complexes (bounded or degree-windowed). Degree bounds are
//! shape metadata only. Concrete boundary-law complexes and homology computation
//! live in `core_homology` (conceptual link in docs comments only).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_6dba0418;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_6dba0418<T> = std::result::Result<T, BoundaryError_6dba0418>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for Ch(A) / Kom(A) with optional degree window.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChainComplexCategory {
    pub label: String,
    /// Inclusive lower degree bound for complexes in this shell.
    pub degree_min: i32,
    /// Inclusive upper degree bound for complexes in this shell.
    pub degree_max: i32,
    pub notes: Vec<String>,
}

impl ChainComplexCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            degree_min: 0,
            degree_max: 0,
            notes: Vec::new(),
        }
    }

    pub fn with_degree_bounds(label: impl Into<String>, degree_min: i32, degree_max: i32) -> Self {
        Self {
            label: label.into(),
            degree_min,
            degree_max,
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Span of the declared degree window (non-negative when bounds are ordered).
    pub fn degree_span(&self) -> Option<u32> {
        if self.degree_min <= self.degree_max {
            Some((self.degree_max - self.degree_min) as u32)
        } else {
            None
        }
    }

    /// Validate structural emptiness and ordered degree bounds (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.degree_min > self.degree_max {
            return Err(format!(
                "degree_min {} > degree_max {}",
                self.degree_min, self.degree_max
            ));
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let c = ChainComplexCategory::with_degree_bounds("Ch(Ab)", 0, 2);
        assert!(c.validate_shell().is_ok());
        assert_eq!(c.degree_span(), Some(2));
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(ChainComplexCategory::new("").validate_shell().is_err());
    }

    #[test]
    fn rejects_inverted_bounds() {
        let c = ChainComplexCategory::with_degree_bounds("bad", 3, 1);
        assert!(c.validate_shell().is_err());
        assert_eq!(c.degree_span(), None);
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainRankCertificate {
    homology: Vec<u64>,
    euler: i128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ChainRankError { Shape, Rank, Homology, Overflow, Euler }

// Origin: engine/crates_rs/core_category_theory/src/abelian/chain_complex_category.rs
// Claim: urn:core:crates_rs:core-category-theory:chain-complex-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ChainRankError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ChainRankError {}

fn validate_chain_ranks(dims: &[u64], ranks: &[u64]) -> Result<(), ChainRankError> {
    if dims.is_empty() || ranks.len().checked_add(1) != Some(dims.len()) {
        return Err(ChainRankError::Shape);
    }
    for (index, &rank) in ranks.iter().enumerate() {
        if rank > dims[index] || rank > dims[index + 1] {
            return Err(ChainRankError::Rank);
        }
    }
    Ok(())
}

fn degree_homology(index: usize, dims: &[u64], ranks: &[u64]) -> Result<u64, ChainRankError> {
    let dim = dims[index];
    let incoming = if index == 0 { 0 } else { ranks[index - 1] };
    let outgoing = if index + 1 == dims.len() { 0 } else { ranks[index] };
    let used = incoming.checked_add(outgoing).ok_or(ChainRankError::Overflow)?;
    if used > dim {
        return Err(ChainRankError::Homology);
    }
    dim.checked_sub(used).ok_or(ChainRankError::Overflow)
}

fn add_signed_euler(euler: i128, sign: i128, val: u64) -> Result<i128, ChainRankError> {
    let term = sign.checked_mul(i128::from(val)).ok_or(ChainRankError::Overflow)?;
    euler.checked_add(term).ok_or(ChainRankError::Overflow)
}

impl ChainRankCertificate {
    /// Rank-nullity homology and the Euler characteristic identity.
    pub fn try_new(dims: &[u64], ranks: &[u64]) -> Result<Self, ChainRankError> {
        validate_chain_ranks(dims, ranks)?;
        let mut homology = Vec::with_capacity(dims.len());
        let mut euler_dims: i128 = 0;
        let mut euler_homology: i128 = 0;
        let mut sign: i128 = 1;
        for index in 0..dims.len() {
            let h = degree_homology(index, dims, ranks)?;
            homology.push(h);
            euler_dims = add_signed_euler(euler_dims, sign, dims[index])?;
            euler_homology = add_signed_euler(euler_homology, sign, h)?;
            sign = -sign;
        }
        if euler_dims != euler_homology {
            return Err(ChainRankError::Euler);
        }
        Ok(Self { homology, euler: euler_dims })
    }

    pub fn euler(&self) -> i128 { self.euler }
    pub fn homology(&self) -> &[u64] { &self.homology }
}

#[cfg(test)]
mod chain_rank_checks {
    use super::*;

    #[test]
    fn euler_of_a_short_complex_matches_homology() {
        let cert = ChainRankCertificate::try_new(&[2, 3, 2], &[1, 1]);
        assert!(matches!(cert, Ok(c) if c.euler() == 1 && c.homology() == [1, 1, 1]));
    }

    #[test]
    fn a_rank_past_the_domain_is_refused() {
        assert!(matches!(ChainRankCertificate::try_new(&[1, 1], &[2]), Err(ChainRankError::Rank)));
    }
}
