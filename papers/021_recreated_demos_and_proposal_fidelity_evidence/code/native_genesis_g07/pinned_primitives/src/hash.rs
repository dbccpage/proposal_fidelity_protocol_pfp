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
