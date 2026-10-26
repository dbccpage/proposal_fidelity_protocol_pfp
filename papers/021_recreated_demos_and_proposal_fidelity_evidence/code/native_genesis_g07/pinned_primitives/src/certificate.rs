//! Sort 10 — **Certificate**: evidence of a specific kind, never of another.
//!
//! Crate boundary: coda-cert.  Source: crosstab §11.5 and §13.7; sealed
//! `incomplete_search_false_alarm` (an exhaustion certificate's
//! countermodel); `fresh_characters` (the first *cancellation* certificate
//! refusal: `[2, −1, −1]` sums to zero and no pairing witness exists).
//!
//! | kind | glyph | says |
//! |---|---|---|
//! | exhaustion | `⊢ᴱ` | the declared finite space was searched and nothing was found |
//! | witness | `⊢ᵂ` | here is the object, and here is the check that it is one |
//! | obstruction | `⊢ᴼ` | no object can exist, and here is the proof |
//!
//! Three kinds, never one field.  Collapsing them is how an engine cheats:
//! "the defect summed to zero" read as a witness accepts `[2, −1, −1]`;
//! "the first ten failed" read as exhaustion is the false alarm.
//!
//! **`FW-RECEIPT` as a type rule.**  A `TestResult` exists so that the rule
//! can be stated in code: there is no conversion from it to a
//! `Certificate`.  A green suite is not a certificate and must not construct
//! one.  The doctest below fails to compile, which is the receipt for that.
//! These public variants remain caller-constructible declaration records,
//! not proof objects. No-conversion does not prevent a fabricated payload.
//! The represented refusal path separately recomputes its menu certificate.
//!
//! ```compile_fail
//! use omega_ooutwire_primitives::certificate::{Certificate, TestResult};
//! let green = TestResult { name: "suite".into(), passed: true };
//! let _c: Certificate = Certificate::from(green);
//! ```

use std::fmt;

/// The identity of a declared search space, for an exhaustion certificate.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SpaceId(pub String);

/// The declared bound of that space.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Bound(pub String);

/// The identity of a witnessed object.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ObjectId(pub String);

/// The identity of the check that certified the object.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CheckId(pub String);

/// The identity of a proof of impossibility.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ProofId(pub String);

/// A certificate.  Exactly one kind.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Certificate {
    /// `⊢ᴱ` — the declared finite space was searched to the end.
    Exhaustion {
        /// Which space.
        space: SpaceId,
        /// Under which bound.
        bound: Bound,
        /// How many candidates were examined — every one of them.
        searched: usize,
    },
    /// `⊢ᵂ` — the object, and the check that it is one.
    Witness {
        /// The object.
        object: ObjectId,
        /// The check.
        check: CheckId,
    },
    /// `⊢ᴼ` — no object can exist.
    Obstruction {
        /// The proof.
        proof: ProofId,
    },
}

/// The three kinds.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum CertKind {
    /// `⊢ᴱ`
    Exhaustion,
    /// `⊢ᵂ`
    Witness,
    /// `⊢ᴼ`
    Obstruction,
}

impl Certificate {
    /// Which kind.
    pub fn kind(&self) -> CertKind {
        match self {
            Certificate::Exhaustion { .. } => CertKind::Exhaustion,
            Certificate::Witness { .. } => CertKind::Witness,
            Certificate::Obstruction { .. } => CertKind::Obstruction,
        }
    }

    /// The glyph.
    pub fn glyph(&self) -> &'static str {
        match self.kind() {
            CertKind::Exhaustion => "⊢ᴱ",
            CertKind::Witness => "⊢ᵂ",
            CertKind::Obstruction => "⊢ᴼ",
        }
    }
}

/// The result of running a test.  It is a receipt for the test having
/// passed, and nothing else.  There is deliberately no `From<TestResult>
/// for Certificate`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TestResult {
    /// The test's name.
    pub name: String,
    /// Whether it passed.
    pub passed: bool,
}

impl fmt::Display for Certificate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Certificate::Exhaustion { space, bound, searched } => {
                write!(f, "{} exhaustion of {} under {} ({} examined)", self.glyph(), space.0, bound.0, searched)
            }
            Certificate::Witness { object, check } => write!(f, "{} witness {} checked by {}", self.glyph(), object.0, check.0),
            Certificate::Obstruction { proof } => write!(f, "{} obstruction proved by {}", self.glyph(), proof.0),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn three_kinds_and_their_glyphs() {
        let e = Certificate::Exhaustion { space: SpaceId("s".into()), bound: Bound("b".into()), searched: 3 };
        let w = Certificate::Witness { object: ObjectId("o".into()), check: CheckId("c".into()) };
        let o = Certificate::Obstruction { proof: ProofId("p".into()) };
        assert_eq!((e.kind(), w.kind(), o.kind()), (CertKind::Exhaustion, CertKind::Witness, CertKind::Obstruction));
        assert_eq!(e.glyph(), "⊢ᴱ");
        assert!(e.to_string().contains("3 examined"));
    }

    /// A total of zero is not a cancellation: the sum is a number, the
    /// certificate is a pairing witness, and `[2, -1, -1]` has the first
    /// and not the second.
    #[test]
    fn a_zero_total_is_not_a_witness() {
        let terms = [2i64, -1, -1];
        assert_eq!(terms.iter().sum::<i64>(), 0);
        // A pairing into exact opposites plus a single-signed residual:
        // 2 has no partner of magnitude 2.
        let has_partner = terms.contains(&-2);
        assert!(!has_partner);
    }
}
