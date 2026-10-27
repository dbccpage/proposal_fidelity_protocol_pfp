use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

/// `sha256:<64 lowercase hex>`. The field is private and `Deserialize` routes
/// through [`Digest::parse`], so an unnormalised digest cannot be constructed —
/// not by a caller, and not from JSON.
///
/// Callers can construct a digest through the public parser:
///
/// ```
/// use core_kernel::Digest;
///
/// let text = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
/// let digest = Digest::parse(text).expect("canonical digest");
/// assert_eq!(digest.as_str(), text);
/// ```
///
/// The tuple constructor is private, so a caller cannot bypass that parser:
///
/// ```compile_fail,E0423
/// use core_kernel::Digest;
///
/// let _forged = Digest(String::from("not-a-digest"));
/// ```
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct Digest(String);

#[derive(Debug, Error, PartialEq, Eq)]
#[error("not a canonical digest ({reason}): {value:?}")]
pub struct DigestError {
    pub value: String,
    pub reason: &'static str,
}

impl Digest {
    pub fn parse(value: &str) -> Result<Self, DigestError> {
        let fail = |reason| DigestError {
            value: value.to_owned(),
            reason,
        };
        let hex = value
            .strip_prefix("sha256:")
            .ok_or_else(|| fail("missing the sha256: prefix; a bare hex string is not a digest"))?;
        if hex.len() != 64 {
            return Err(fail("expected 64 hex digits"));
        }
        if !hex
            .chars()
            .all(|c| c.is_ascii_digit() || (c.is_ascii_lowercase() && c.is_ascii_hexdigit()))
        {
            return Err(fail("expected lowercase hex only"));
        }
        Ok(Self(value.to_owned()))
    }

    pub fn of_bytes(bytes: &[u8]) -> Self {
        Self(format!("sha256:{}", hex::encode(Sha256::digest(bytes))))
    }

    /// Domain-separated so a digest minted for one purpose cannot be replayed as
    /// another. The domain is length-delimited: without it, `("ab", "c")` and
    /// `("a", "bc")` would hash identically.
    pub fn of_domained(domain: &str, payload: &[u8]) -> Self {
        let mut input = (domain.len() as u64).to_be_bytes().to_vec();
        input.extend_from_slice(domain.as_bytes());
        input.extend_from_slice(payload);
        Self::of_bytes(&input)
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for Digest {
    type Error = DigestError;
    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::parse(&value)
    }
}

impl From<Digest> for String {
    fn from(digest: Digest) -> Self {
        digest.0
    }
}

impl std::fmt::Display for Digest {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

// Origin: engine/crates_rs/core_kernel/src/digest.rs
// Claim: urn:core:crates_rs:core-kernel:digest:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn hex64(c: char) -> String {
        format!(
            "sha256:{}",
            std::iter::repeat(c).take(64).collect::<String>()
        )
    }

    #[test]
    fn a_well_formed_digest_parses_and_round_trips() {
        let text = hex64('a');
        let digest = Digest::parse(&text).unwrap();
        assert_eq!(digest.as_str(), text);
        assert_eq!(digest.to_string(), text);
    }

    #[test]
    fn a_bare_hex_string_is_not_a_digest() {
        assert!(Digest::parse(&"a".repeat(64)).is_err());
    }

    #[test]
    fn uppercase_hex_is_refused_rather_than_folded() {
        // Folding would give one value two spellings, which is the shape of the
        // defect this newtype exists to prevent.
        assert!(Digest::parse(&hex64('A')).is_err());
    }

    #[test]
    fn a_wrong_length_is_refused() {
        assert!(Digest::parse("sha256:abc").is_err());
        assert!(Digest::parse(&format!("sha256:{}", "a".repeat(65))).is_err());
    }

    #[test]
    fn a_non_hex_character_is_refused() {
        assert!(Digest::parse(&format!("sha256:{}z", "a".repeat(63))).is_err());
    }

    #[test]
    fn deserialize_refuses_what_parse_refuses() {
        assert!(serde_json::from_str::<Digest>(&format!("\"{}\"", hex64('A'))).is_err());
        assert!(serde_json::from_str::<Digest>("\"not-a-digest\"").is_err());
        let good = hex64('b');
        assert_eq!(
            serde_json::from_str::<Digest>(&format!("\"{good}\"")).unwrap(),
            Digest::parse(&good).unwrap()
        );
    }

    #[test]
    fn serialize_emits_the_bare_string_not_a_wrapper() {
        assert_eq!(
            serde_json::to_string(&Digest::of_bytes(b"")).unwrap(),
            format!("\"{}\"", Digest::of_bytes(b"").as_str())
        );
    }

    #[test]
    fn of_bytes_is_the_known_sha256_of_the_empty_string() {
        assert_eq!(
            Digest::of_bytes(b"").as_str(),
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
    }

    #[test]
    fn of_bytes_always_produces_something_parse_accepts() {
        for payload in [b"".as_slice(), b"x", b"a longer payload"] {
            let digest = Digest::of_bytes(payload);
            assert_eq!(Digest::parse(digest.as_str()).unwrap(), digest);
        }
    }

    #[test]
    fn different_payloads_give_different_digests() {
        assert_ne!(Digest::of_bytes(b"a"), Digest::of_bytes(b"b"));
    }

    #[test]
    fn the_domain_is_length_delimited_so_a_boundary_cannot_shift() {
        // Without the length prefix these two would hash the same bytes.
        assert_ne!(
            Digest::of_domained("ab", b"c"),
            Digest::of_domained("a", b"bc")
        );
    }

    #[test]
    fn the_same_payload_under_different_domains_cannot_be_replayed() {
        assert_ne!(
            Digest::of_domained("core.proposal.v1", b"payload"),
            Digest::of_domained("core.license.v1", b"payload")
        );
    }

    #[test]
    fn digests_order_and_hash_so_they_can_key_a_map() {
        use std::collections::BTreeSet;
        let set: BTreeSet<_> = [Digest::of_bytes(b"b"), Digest::of_bytes(b"a")]
            .into_iter()
            .collect();
        assert_eq!(set.len(), 2);
    }
}
