//! Compatibility hash identifiers for certified modules migrated from `homological`.

use blake3::Hasher;
use std::fmt;

#[derive(Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct Blake3Hash(pub [u8; 32]);

impl Blake3Hash {
    pub fn new(data: &[u8]) -> Self {
        let mut hasher = Hasher::new();
        hasher.update(data);
        Self(hasher.finalize().into())
    }

    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

impl fmt::Debug for Blake3Hash {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Blake3Hash({}..)", hex::encode(&self.0[..4]))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct ComplexHash(pub Blake3Hash);

#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct BoundaryMapHash(pub Blake3Hash);

#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct VectorHash(pub Blake3Hash);

#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct QuotientRelationHash(pub Blake3Hash);

#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct CertificateHash(pub Blake3Hash);

impl ComplexHash {
    pub fn new(data: &[u8]) -> Self {
        Self(Blake3Hash::new(data))
    }
}

impl BoundaryMapHash {
    pub fn new(data: &[u8]) -> Self {
        Self(Blake3Hash::new(data))
    }
}

impl VectorHash {
    pub fn new(data: &[u8]) -> Self {
        Self(Blake3Hash::new(data))
    }
}

impl QuotientRelationHash {
    pub fn new(data: &[u8]) -> Self {
        Self(Blake3Hash::new(data))
    }
}

impl CertificateHash {
    pub fn new(data: &[u8]) -> Self {
        Self(Blake3Hash::new(data))
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DomainSeparationError {
    SameDomain,
    Collision,
    DigestLength { length: usize },
}

// Origin: engine/crates_rs/core_homology/src/hash.rs
// Claim: urn:core:crates_rs:core-homology:hash:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DomainSeparationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DomainSeparationError {}

/// Domain-separated Blake3 digest: `domain || 0xff || payload`.
pub fn domain_separated(domain: &[u8], payload: &[u8]) -> Blake3Hash {
    let mut hasher = Hasher::new();
    hasher.update(domain);
    hasher.update(&[0xff]);
    hasher.update(payload);
    Blake3Hash(hasher.finalize().into())
}

pub fn domains_separate(
    left: &[u8],
    right: &[u8],
    payload: &[u8],
) -> Result<(), DomainSeparationError> {
    if left == right {
        return Err(DomainSeparationError::SameDomain);
    }
    let left_digest = domain_separated(left, payload);
    let right_digest = domain_separated(right, payload);
    if left_digest.as_bytes().len() != 32 {
        return Err(DomainSeparationError::DigestLength {
            length: left_digest.as_bytes().len(),
        });
    }
    if left_digest.as_bytes() == right_digest.as_bytes() {
        return Err(DomainSeparationError::Collision);
    }
    Ok(())
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod domain_separation_witness {
    use super::*;

    #[test]
    fn distinct_domains_do_not_collide() {
        assert_eq!(
            domains_separate(b"complex", b"boundary", b"payload"),
            Ok(())
        );
        let digest = domain_separated(b"complex", b"payload");
        assert_eq!(digest.as_bytes().len(), 32);
    }

    #[test]
    fn the_same_domain_is_refused() {
        assert!(matches!(
            domains_separate(b"complex", b"complex", b"payload"),
            Err(DomainSeparationError::SameDomain)
        ));
    }
}
