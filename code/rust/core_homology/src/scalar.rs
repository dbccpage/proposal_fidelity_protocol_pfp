//! Canonical scalar type for exact arithmetic.
//!
//! # ADR-001 — BigRational is the canonical coefficient domain (2026-08-04)
//!
//! `Q` is `BigRational`. It is the **single** canonical coefficient domain for the
//! Φ₁/cochain authority path: cochain maps, residuals, witnesses, and trichotomy
//! inputs all carry it. There is deliberately **no parallel `BigRational` carrier** —
//! this alias was widened in place so that one cochain complex exists, not two.
//!
//! ## Direction of travel
//!
//! - **In:** [`inject_rational64`] is an *exact, total* injection ℚ₆₄ ↪ ℚ. Legacy
//!   `Rational64` values enter through it. It cannot fail.
//! - **Out:** [`try_narrow_to_rational64`] is *explicitly fallible* and is
//!   **prohibited on the decision path**. Narrowing a value that was widened for a
//!   reason is how an exact lane silently becomes an approximate one. It exists for
//!   interop with legacy fixed-width surfaces only.
//!
//! ## `Q` is no longer `Copy`
//!
//! `Rational64` was `Copy`; `BigRational` is heap-backed and is not. Call sites that
//! relied on implicit copies now clone explicitly. That cost is deliberate: it makes
//! every duplication of an exact coefficient visible at the point it happens.
//!
//! ## Hashing
//!
//! `BigInt` has no fixed width, so [`hash_rational`] **length-prefixes** each limb
//! before feeding it to the hasher. Without the prefix the encoding is not injective:
//! `1/515` and `769/2` both serialise to `01 03 02`. (An earlier version of this note
//! cited `(1, 23)` and `(12, 3)`, which do **not** collide — `01 17` versus `0c 03`.)
//!
//! The property is one of the **encoding**, not of BLAKE3: a 256-bit digest of an
//! unbounded input space cannot be injective, only collision-resistant. What the
//! framing buys is that distinct rationals reach the hasher as distinct bytes, so no
//! collision arises by construction.
//!
//! The domain-separation tags in [`crate::hashing`] name the coefficient domain, so
//! widening the alias necessarily changes them — that tag *is* the coefficient-domain
//! record ADR-001 asks receipts to carry.

use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use num_traits::ToPrimitive;

/// Canonical exact scalar type: arbitrary-precision rational.
///
/// See the module docs for ADR-001. This is the authority-bearing coefficient
/// domain; nothing on the decision path may use a narrower one.
pub type Q = BigRational;

/// Create a rational from an integer.
#[inline]
pub fn q(n: i64) -> Q {
    BigRational::from_integer(BigInt::from(n))
}

/// Create a rational from numerator/denominator.
///
/// # Panics
///
/// Panics if `d == 0`, matching the previous `Rational64` behaviour.
#[inline]
pub fn qr(n: i64, d: i64) -> Q {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

/// Exact injection ℚ₆₄ ↪ ℚ — the sanctioned entry point for legacy values.
///
/// Total and lossless: every `Rational64` is a `BigRational`. This is the only
/// conversion permitted to appear on the decision path.
#[inline]
pub fn inject_rational64(value: Rational64) -> Q {
    BigRational::new(BigInt::from(*value.numer()), BigInt::from(*value.denom()))
}

/// Why a value could not be narrowed back to `Rational64`.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum NarrowError {
    /// The numerator does not fit in `i64`.
    #[error("numerator does not fit in i64: {0}")]
    NumeratorOutOfRange(String),
    /// The denominator does not fit in `i64`.
    #[error("denominator does not fit in i64: {0}")]
    DenominatorOutOfRange(String),
}

/// Fallible narrowing ℚ ⇸ ℚ₆₄.
///
/// **Prohibited on the decision path (ADR-001).** Classification, continuation and
/// terminalization must consume [`Q`] directly. This exists only for interop with
/// legacy fixed-width surfaces, and it fails closed rather than truncating.
pub fn try_narrow_to_rational64(value: &Q) -> Result<Rational64, NarrowError> {
    let numer = value
        .numer()
        .to_i64()
        .ok_or_else(|| NarrowError::NumeratorOutOfRange(value.numer().to_string()))?;
    let denom = value
        .denom()
        .to_i64()
        .ok_or_else(|| NarrowError::DenominatorOutOfRange(value.denom().to_string()))?;
    Ok(Rational64::new(numer, denom))
}

/// Hash a single rational value into a hasher.
///
/// Length-prefixed so the encoding is injective over variable-width limbs.
pub fn hash_rational(hasher: &mut blake3::Hasher, val: &Q) {
    hash_bigint(hasher, val.numer());
    hash_bigint(hasher, val.denom());
}

/// Hash a `BigInt` as `len:u64 || signed-le-bytes`.
#[inline]
pub fn hash_bigint(hasher: &mut blake3::Hasher, value: &BigInt) {
    let bytes = value.to_signed_bytes_le();
    hasher.update(&(bytes.len() as u64).to_le_bytes());
    hasher.update(&bytes);
}

/// Hash a vector of rationals.
pub fn hash_rational_vec(hasher: &mut blake3::Hasher, vals: &[Q]) {
    hasher.update(&(vals.len() as u64).to_le_bytes());
    for v in vals {
        hash_rational(hasher, v);
    }
}

// Origin: engine/crates_rs/core_homology/src/scalar.rs
// Claim: urn:core:crates_rs:core-homology:scalar:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::One;
    use std::str::FromStr;

    #[test]
    fn test_q_from_integer() {
        let r = q(5);
        assert_eq!(*r.numer(), BigInt::from(5));
        assert!(r.denom().is_one());
    }

    #[test]
    fn test_qr_rational() {
        let r = qr(3, 4);
        assert_eq!(*r.numer(), BigInt::from(3));
        assert_eq!(*r.denom(), BigInt::from(4));
    }

    #[test]
    fn test_qr_reduces() {
        let r = qr(6, 8);
        assert_eq!(*r.numer(), BigInt::from(3));
        assert_eq!(*r.denom(), BigInt::from(4));
    }

    #[test]
    fn test_hash_deterministic() {
        let val = qr(7, 13);
        let mut h1 = blake3::Hasher::new();
        let mut h2 = blake3::Hasher::new();
        hash_rational(&mut h1, &val);
        hash_rational(&mut h2, &val);
        assert_eq!(h1.finalize().as_bytes(), h2.finalize().as_bytes());
    }

    #[test]
    fn test_hash_vec_deterministic() {
        let vals = vec![qr(1, 2), qr(3, 4), qr(5, 6)];
        let mut h1 = blake3::Hasher::new();
        let mut h2 = blake3::Hasher::new();
        hash_rational_vec(&mut h1, &vals);
        hash_rational_vec(&mut h2, &vals);
        assert_eq!(h1.finalize().as_bytes(), h2.finalize().as_bytes());
    }

    // --- ADR-001 regression suite -------------------------------------------

    /// Coefficients beyond i64 are representable. This is the whole point of the
    /// widening: `Rational64` could not hold this value at all.
    #[test]
    fn adr001_coefficients_beyond_i64_are_exact() {
        let big = BigInt::from_str("170141183460469231731687303715884105727").unwrap();
        let value = BigRational::new(big.clone(), BigInt::one());
        assert_eq!(*value.numer(), big);
        assert!(value.numer().to_i64().is_none(), "must exceed i64 range");
    }

    /// A product that would overflow i64 intermediates stays exact.
    #[test]
    fn adr001_intermediate_overflow_stays_exact() {
        let a = q(4_000_000_000);
        let b = q(4_000_000_000);
        let product = &a * &b;
        let expected = BigInt::from_str("16000000000000000000").unwrap();
        assert_eq!(*product.numer(), expected);
        assert!(
            expected.to_i64().is_none(),
            "product must exceed i64 range, else the test proves nothing"
        );
    }

    /// The legacy injection is exact and total.
    #[test]
    fn adr001_injection_from_rational64_is_exact() {
        let legacy = Rational64::new(355, 113);
        let widened = inject_rational64(legacy);
        assert_eq!(*widened.numer(), BigInt::from(355));
        assert_eq!(*widened.denom(), BigInt::from(113));
    }

    /// Narrowing fails closed rather than truncating.
    #[test]
    fn adr001_narrowing_out_of_range_is_refused() {
        let big = BigRational::new(
            BigInt::from_str("170141183460469231731687303715884105727").unwrap(),
            BigInt::one(),
        );
        assert!(matches!(
            try_narrow_to_rational64(&big),
            Err(NarrowError::NumeratorOutOfRange(_))
        ));
    }

    /// Round-trip holds exactly on the subset that fits.
    #[test]
    fn adr001_narrowing_round_trips_when_in_range() {
        let legacy = Rational64::new(-9, 7);
        let narrowed = try_narrow_to_rational64(&inject_rational64(legacy)).unwrap();
        assert_eq!(narrowed, legacy);
    }

    /// Reproduce the unframed encoding — signed-LE limbs concatenated with no
    /// length prefix — so the test can demonstrate what the prefix prevents.
    fn unframed(value: &Q) -> Vec<u8> {
        let mut out = value.numer().to_signed_bytes_le();
        out.extend_from_slice(&value.denom().to_signed_bytes_le());
        out
    }

    /// The length prefix is load-bearing, and this proves it by exhibiting a real
    /// collision in the encoding it replaces.
    ///
    /// `1/515` and `769/2` both serialise to `01 03 02` unframed:
    ///
    /// ```text
    ///   1   -> 01        515 -> 03 02      =>  01 03 02
    ///   769 -> 01 03       2 -> 02         =>  01 03 02
    /// ```
    ///
    /// # What is and is not being claimed
    ///
    /// The property under test belongs to the **pre-hash encoding**, not to BLAKE3.
    /// BLAKE3 maps an unbounded input space into 256 bits and so cannot be
    /// injective; it is collision-*resistant*, which is a computational assumption
    /// about finding collisions, not a claim that none exist. What is provable — and
    /// what actually matters here — is that the encoding fed to it distinguishes
    /// distinct rationals. Without the length prefix it does not, and then two
    /// different values collide *by construction*, with no cryptography involved.
    /// The test name says `encoding`, not `hash`, for exactly that reason.
    ///
    /// An earlier version of this test used `(1,23)` vs `(12,3)`, which do **not**
    /// collide (`01 17` vs `0c 03`) — so it passed with the prefixes deleted and
    /// proved nothing. A check that cannot fail is not a check.
    #[test]
    fn adr001_prehash_encoding_separates_variable_width_limbs() {
        let a = qr(1, 515);
        let b = qr(769, 2);

        // The premise: without framing these are byte-identical.
        assert_eq!(
            unframed(&a),
            unframed(&b),
            "test premise broken — this pair must collide unframed, or the \
             assertion below proves nothing"
        );

        let mut h1 = blake3::Hasher::new();
        let mut h2 = blake3::Hasher::new();
        hash_rational(&mut h1, &a);
        hash_rational(&mut h2, &b);
        assert_ne!(
            h1.finalize().as_bytes(),
            h2.finalize().as_bytes(),
            "length prefix missing: the framed encoding failed to separate two \
             values whose unframed encodings are equal"
        );
    }

    /// Values that differ only beyond the i64 boundary must hash differently.
    #[test]
    fn adr001_hash_separates_values_beyond_i64() {
        let a = BigRational::new(
            BigInt::from_str("170141183460469231731687303715884105727").unwrap(),
            BigInt::one(),
        );
        let b = BigRational::new(
            BigInt::from_str("170141183460469231731687303715884105728").unwrap(),
            BigInt::one(),
        );
        let mut h1 = blake3::Hasher::new();
        let mut h2 = blake3::Hasher::new();
        hash_rational(&mut h1, &a);
        hash_rational(&mut h2, &b);
        assert_ne!(h1.finalize().as_bytes(), h2.finalize().as_bytes());
    }
}
