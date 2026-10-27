//! Primitive — **fingerprint**: the replay hash.
//!
//! Crate boundary: coda-carrier.  Source: `export.regime_sha256`, which
//! hashes a sorted-key JSON serialisation of the regime, and
//! `verify_full_export`, which replays every node and compares.
//!
//! This crate has no dependencies, so the digest is 64-bit FNV-1a over the
//! deterministic serialisation in `export.rs`, **not** SHA-256.  It is a
//! fingerprint for replay comparison inside this crate.  It is not the
//! sealed artefact's hash and must never be compared against one.  A receipt
//! that names the wrong hash function is a receipt for nothing.

use crate::export::regime_text;
use crate::regime::Regime;

/// 64-bit FNV-1a over bytes.  Deterministic, dependency-free, not
/// cryptographic.
pub fn fnv1a64(bytes: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for &b in bytes {
        h ^= b as u64;
        h = h.wrapping_mul(0x0000_0100_0000_01b3);
    }
    h
}

/// The fingerprint of a regime: FNV-1a of its deterministic serialisation.
pub fn regime_fingerprint(r: &Regime) -> u64 {
    fnv1a64(regime_text(r).as_bytes())
}

/// The fingerprint rendered as sixteen hex digits.
pub fn hex(fp: u64) -> String {
    format!("{fp:016x}")
}

const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Refusal codes for FNV-1a incremental hashing law checks.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FnvLawError {
    /// One of the input byte blocks is empty.
    Empty,
    /// Incremental absorption state disagrees with full concatenation hash.
    Incremental,
    /// FNV prime decomposition does not match `2^40 + 2^8 + 0xb3`.
    Prime,
}

impl std::fmt::Display for FnvLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Empty => write!(formatter, "both FNV blocks must be non-empty"),
            Self::Incremental => write!(formatter, "continuing the FNV state disagrees with the joint hash"),
            Self::Prime => write!(formatter, "FNV prime is not 2^40 + 2^8 + 0xb3"),
        }
    }
}

impl std::error::Error for FnvLawError {}

fn absorb(state: u64, byte: u8) -> u64 {
    let mixed = state ^ u64::from(byte);
    let wide = u128::from(mixed).wrapping_mul(u128::from(FNV_PRIME));
    wide as u64
}

fn verify_fnv_constants() -> Result<(), FnvLawError> {
    let prime = 1u64
        .checked_shl(40)
        .and_then(|shifted| shifted.checked_add(1u64.checked_shl(8)?))
        .and_then(|shifted| shifted.checked_add(0xb3))
        .ok_or(FnvLawError::Prime)?;
    if prime != FNV_PRIME {
        return Err(FnvLawError::Prime);
    }
    if fnv1a64(&[]) != FNV_OFFSET {
        return Err(FnvLawError::Incremental);
    }
    Ok(())
}

/// Empty input is the offset basis, and extending a hash by `right` equals hashing the concatenation.
pub fn certify_incremental(left: &[u8], right: &[u8]) -> Result<u64, FnvLawError> {
    if left.is_empty() || right.is_empty() {
        return Err(FnvLawError::Empty);
    }
    verify_fnv_constants()?;
    let mut joint = Vec::with_capacity(left.len().checked_add(right.len()).ok_or(FnvLawError::Incremental)?);
    joint.extend_from_slice(left);
    joint.extend_from_slice(right);
    let whole = fnv1a64(&joint);
    let mut continued = fnv1a64(left);
    for &byte in right {
        continued = absorb(continued, byte);
    }
    if continued != whole {
        return Err(FnvLawError::Incremental);
    }
    let mut replay = FNV_OFFSET;
    for &byte in &joint {
        replay = absorb(replay, byte);
    }
    if replay != whole {
        return Err(FnvLawError::Incremental);
    }
    Ok(whole)
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/hash.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:hash:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod fnv_law_tests {
    use super::*;

    fn taken(result: Result<u64, FnvLawError>) -> u64 {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn extending_the_state_matches_the_concatenation() {
        let digest = taken(certify_incremental(b"ab", b"cd"));
        assert_eq!(digest, fnv1a64(b"abcd"));
        assert_ne!(digest, fnv1a64(b"ab") ^ fnv1a64(b"cd"));
    }

    #[test]
    fn an_empty_block_is_refused() {
        assert!(matches!(
            certify_incremental(b"ab", b""),
            Err(FnvLawError::Empty)
        ));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;
    use crate::token::Token;

    #[test]
    fn equal_regimes_have_equal_fingerprints_and_a_change_moves_it() {
        let l = replay(&READING_L.genesis).unwrap();
        assert_eq!(regime_fingerprint(&l), regime_fingerprint(&replay(&READING_L.genesis).unwrap()));
        let f = replay(&READING_F.genesis).unwrap();
        assert_ne!(regime_fingerprint(&l), regime_fingerprint(&f));
        let l2 = step(&l, &Event::AdmitDatum(Token::new("g2"))).unwrap();
        assert_ne!(regime_fingerprint(&l), regime_fingerprint(&l2));
    }

    #[test]
    fn a_supply_does_not_move_the_fingerprint() {
        let l = replay(&READING_L.genesis).unwrap();
        let l2 = step(&l, &Event::Supply(Token::new("anything"))).unwrap();
        assert_eq!(regime_fingerprint(&l), regime_fingerprint(&l2));
    }
}
