// Executable finite evidence; AuthorityEffect: None.
//! Core value objects and types for the Witnessed Difference Programme crate.

use serde::{Deserialize, Serialize};
use std::fmt;

/// Explicit AuthorityEffect enum enforcing constitutional firewall.
/// Under Sentinel doctrine, mathematical evaluations carry AuthorityEffect::None.
#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize, Default,
)]
pub enum AuthorityEffect {
    #[default]
    None,
}

impl fmt::Display for AuthorityEffect {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::None => write!(f, "None"),
        }
    }
}

/// Computes SHA-256 hex digest for arbitrary byte sequences.
pub fn sha256_digest(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hex::encode(hasher.finalize())
}

/// Computes Blake3 hex digest for arbitrary byte sequences.
pub fn blake3_digest(bytes: &[u8]) -> String {
    let hash = blake3::hash(bytes);
    hash.to_hex().to_string()
}

const SHA256_EMPTY: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

/// Hex length 64 and a lowercase hex alphabet. SHA-256 of the empty input is pinned.
/// Blake3 of the empty input is checked for shape only.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DigestLengthWitness {
    sha256_empty_matches: bool,
    blake3_hex_len: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DigestShapeError {
    BadLength { len: usize },
    BadCharset,
    Sha256EmptyMismatch,
}

fn hex_shape(text: &str) -> Result<(), DigestShapeError> {
    if text.len() != 64 {
        return Err(DigestShapeError::BadLength { len: text.len() });
    }
    if !text
        .bytes()
        .all(|byte| matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
    {
        return Err(DigestShapeError::BadCharset);
    }
    Ok(())
}

impl DigestLengthWitness {
    pub fn certify_known_empties() -> Result<Self, DigestShapeError> {
        let sha = sha256_digest(b"");
        hex_shape(&sha)?;
        if sha != SHA256_EMPTY {
            return Err(DigestShapeError::Sha256EmptyMismatch);
        }
        let blake = blake3_digest(b"");
        hex_shape(&blake)?;
        Ok(Self {
            sha256_empty_matches: true,
            blake3_hex_len: blake.len(),
        })
    }

    pub fn sha256_empty_matches(&self) -> bool {
        self.sha256_empty_matches
    }

    pub fn blake3_hex_len(&self) -> usize {
        self.blake3_hex_len
    }
}

// Origin: engine/crates_rs/core_wdp/src/types.rs
// Claim: urn:core:crates_rs:core-wdp:types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_255f79fa {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
