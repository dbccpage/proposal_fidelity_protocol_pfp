//! Chain maps of pairs.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_445a9478;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_445a9478<T> = std::result::Result<T, BoundaryError_445a9478>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `relative_chain_map`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct RelativeChainMap {
    pub label: String,
    pub notes: Vec<String>,
}

impl RelativeChainMap {
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
        let s = RelativeChainMap::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = RelativeChainMap::new("relative_chain_map").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Refusal from a degreewise quotient of chain ranks.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QuotientError {
    /// The two rank lists differ in length.
    Length,
    /// A subcomplex rank exceeds the ambient rank.
    TooLarge { degree: usize },
    /// Checked arithmetic overflowed, or the Euler identity failed.
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/relative_chain_map.rs
// Claim: urn:core:crates_rs:core-homology:relative-chain-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for QuotientError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for QuotientError {}

/// Euler characteristic of `C/S`, equal to `chi(C) - chi(S)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuotientEuler {
    euler: i64,
}

fn alternating(ranks: &[u32]) -> Result<i64, QuotientError> {
    let mut euler = 0i64;
    let mut sign = 1i64;
    for rank in ranks {
        let term = i64::from(*rank).checked_mul(sign).ok_or(QuotientError::Overflow)?;
        euler = euler.checked_add(term).ok_or(QuotientError::Overflow)?;
        sign = sign.checked_neg().ok_or(QuotientError::Overflow)?;
    }
    Ok(euler)
}

impl QuotientEuler {
    /// Subtract ranks degreewise and check the Euler identity.
    pub fn try_new(ambient: &[u32], sub: &[u32]) -> Result<Self, QuotientError> {
        if ambient.len() != sub.len() {
            return Err(QuotientError::Length);
        }
        let mut quotient = Vec::new();
        for (degree, (&c_rank, &s_rank)) in ambient.iter().zip(sub.iter()).enumerate() {
            if s_rank > c_rank {
                return Err(QuotientError::TooLarge { degree });
            }
            quotient.push(c_rank - s_rank);
        }
        let euler_c = alternating(ambient)?;
        let euler_s = alternating(sub)?;
        let euler_q = alternating(&quotient)?;
        let difference = euler_c.checked_sub(euler_s).ok_or(QuotientError::Overflow)?;
        if difference != euler_q {
            return Err(QuotientError::Overflow);
        }
        Ok(Self { euler: euler_q })
    }

    /// Euler characteristic of the quotient.
    pub fn euler(&self) -> i64 { self.euler }
}

#[cfg(test)]
mod quotient_tests {
    use super::*;
    #[test]
    fn quotient_euler_is_the_difference() {
        let quotient = QuotientEuler::try_new(&[3, 3], &[1, 0]);
        assert!(matches!(quotient, Ok(ref q) if q.euler() == -1));
    }
    #[test]
    fn a_larger_subcomplex_is_refused() {
        assert!(matches!(QuotientEuler::try_new(&[1], &[2]), Err(QuotientError::TooLarge { degree: 0 })));
    }
}
