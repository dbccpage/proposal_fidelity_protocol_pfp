//! § 10 Item 10: Replay Hash
//!
//! Re-exports the upstream `ReplayHash` from `linear_algebra::proof`.
//!
//! TODO: Add a unified thin type `ReplayHash` to prevent mixing of algorithm tags:
//! ```rust
//! pub struct ReplayHash {
//!     pub algorithm: String,
//!     pub domain: String,
//!     pub hex: String,
//! }
//! ```
//! Do not silently mix SHA256 carrier hash and BLAKE3 replay hash without algorithm tags.

use serde::{Deserialize, Serialize};
use thiserror::Error;

pub use linear_algebra::proof::ReplayHash;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ScopedReplayHashError {
    #[error("missing verifier scope")]
    MissingVerifierScope,
    #[error("missing replay hash")]
    MissingReplayHash,
    #[error("verifier scope mismatch")]
    VerifierScopeMismatch,
}

/// Replay hash labeled by the verifier family that produced it.
///
/// This is not a semantic proof of verifier soundness. It prevents consumers
/// from silently reusing a hash across verifier families.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "RawScopedReplayHash")]
pub struct ScopedReplayHash {
    verifier_scope: String,
    replay_hash: String,
}

#[derive(Deserialize)]
struct RawScopedReplayHash {
    verifier_scope: String,
    replay_hash: String,
}

impl TryFrom<RawScopedReplayHash> for ScopedReplayHash {
    type Error = ScopedReplayHashError;

    fn try_from(raw: RawScopedReplayHash) -> Result<Self, Self::Error> {
        ScopedReplayHash::new(raw.verifier_scope, raw.replay_hash)
    }
}

impl ScopedReplayHash {
    pub fn new(
        verifier_scope: impl Into<String>,
        replay_hash: impl Into<String>,
    ) -> Result<Self, ScopedReplayHashError> {
        let verifier_scope = verifier_scope.into();
        if verifier_scope.trim().is_empty() {
            return Err(ScopedReplayHashError::MissingVerifierScope);
        }
        let replay_hash = replay_hash.into();
        if replay_hash.trim().is_empty() {
            return Err(ScopedReplayHashError::MissingReplayHash);
        }
        Ok(Self {
            verifier_scope,
            replay_hash,
        })
    }

    pub fn verifier_scope(&self) -> &str {
        &self.verifier_scope
    }

    pub fn replay_hash(&self) -> &str {
        &self.replay_hash
    }

    pub fn require_scope(&self, expected_scope: &str) -> Result<(), ScopedReplayHashError> {
        if self.verifier_scope == expected_scope {
            Ok(())
        } else {
            Err(ScopedReplayHashError::VerifierScopeMismatch)
        }
    }
}

// Origin: engine/crates_rs/core_replay/src/replay_hash.rs
// Claim: urn:core:crates_rs:core-replay:replay-hash:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scoped_replay_hash_requires_scope() {
        assert_eq!(
            ScopedReplayHash::new("", "blake3:abc").unwrap_err(),
            ScopedReplayHashError::MissingVerifierScope
        );
    }

    #[test]
    fn scoped_replay_hash_rejects_empty_hash() {
        assert_eq!(
            ScopedReplayHash::new("t3-primal-dual-v1", "").unwrap_err(),
            ScopedReplayHashError::MissingReplayHash
        );
        assert_eq!(
            ScopedReplayHash::new("t3-primal-dual-v1", "   ").unwrap_err(),
            ScopedReplayHashError::MissingReplayHash
        );
    }

    #[test]
    fn scoped_replay_hash_rejects_cross_family_reuse() {
        let replay = ScopedReplayHash::new("t3-primal-dual-v1", "blake3:abc").unwrap();
        assert_eq!(
            replay.require_scope("ast-shift-expr-v1").unwrap_err(),
            ScopedReplayHashError::VerifierScopeMismatch
        );
    }

    #[test]
    fn deserialization_rejects_invalid_scoped_replay_hashes() {
        let json_bad_scope = r#"{"verifier_scope":"   ","replay_hash":"blake3:abc"}"#;
        let res: Result<ScopedReplayHash, _> = serde_json::from_str(json_bad_scope);
        assert!(res.is_err());

        let json_bad_hash = r#"{"verifier_scope":"t3-primal-dual-v1","replay_hash":"   "}"#;
        let res: Result<ScopedReplayHash, _> = serde_json::from_str(json_bad_hash);
        assert!(res.is_err());
    }
}
