//! Sort 1 — **Token**: a presentation identity.
//!
//! Crate boundary: coda-carrier.  Source: `code/derivation/model.py`, the
//! `Regime.data` docstring: *"entries are presentation tokens; internal
//! identity is the index"*.
//!
//! A token is *which mark was handed in*.  It is visible to the metatheory
//! and to nothing inside the object language.  Two consequences carry the
//! whole estate:
//!
//! * a token is **forgotten by the canonical key** (`canonical.rs`), so no
//!   internal structure can depend on it;
//! * re-admission of an already admitted token is a *designation*, not a
//!   duplication — a declared convention (L6), never a theorem.
//!
//! The test at the bottom is the one that catches implementers: a token can
//! exist at run time and must not survive canonicalisation.

use std::fmt;

/// A presentation token.  Compare it only in the metatheory.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Token(pub String);

impl Token {
    /// Build a token from anything string-like.
    pub fn new(s: impl Into<String>) -> Token {
        Token(s.into())
    }

    /// The presentation text.  Metatheory only.
    pub fn text(&self) -> &str {
        &self.0
    }
}

impl fmt::Display for Token {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::canonical::canonical;
    use crate::event::Event;
    use crate::regime::Regime;

    #[test]
    fn presentation_identity_is_metatheoretic_equality() {
        assert_eq!(Token::new("<a>"), Token::new("<a>"));
        assert_ne!(Token::new("<a>"), Token::new("<ab>"));
    }

    /// The law that matters: two regimes that differ only in which tokens
    /// were handed in have the same canonical key.
    #[test]
    fn tokens_are_forgotten_by_the_key() {
        let a = step(&Regime::genesis(), &Event::AdmitDatum(Token::new("<a>"))).unwrap();
        let b = step(&Regime::genesis(), &Event::AdmitDatum(Token::new("<zzz>"))).unwrap();
        assert_ne!(a, b, "the regimes differ as presented");
        assert_eq!(canonical(&a), canonical(&b), "and are identified by the key");
    }
}
