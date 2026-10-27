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


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_237f1d55;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_237f1d55<T> = std::result::Result<T, BoundaryError_237f1d55>;
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

// Origin: engine/crates_rs/core_ooutwire_primitives/src/token.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:token:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

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

use std::collections::BTreeSet;

/// How many times a token was presented, against the set of distinct texts.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PresentationLog {
    presentations: u64,
    canonical: BTreeSet<String>,
}

/// Refusal from a presentation count.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PresentationError {
    /// The presentation counter cannot grow.
    Overflow,
    /// Distinct texts outnumber presentations.
    Census,
}

impl PresentationLog {
    /// An empty log.
    pub fn new() -> Self {
        Self {
            presentations: 0,
            canonical: BTreeSet::new(),
        }
    }

    /// Record one presentation. A repeated text does not grow the canonical set.
    pub fn admit(&mut self, token: &Token) -> Result<(), PresentationError> {
        let presentations = self
            .presentations
            .checked_add(1)
            .ok_or(PresentationError::Overflow)?;
        let mut canonical_set = self.canonical.clone();
        canonical_set.insert(token.text().to_string());
        let canonical = u64::try_from(canonical_set.len()).map_err(|_| PresentationError::Overflow)?;
        if canonical > presentations {
            return Err(PresentationError::Census);
        }
        self.canonical = canonical_set;
        self.presentations = presentations;
        Ok(())
    }

    /// Presentations recorded so far.
    pub fn presentations(&self) -> u64 {
        self.presentations
    }

    /// Distinct token texts.
    pub fn canonical_len(&self) -> usize {
        self.canonical.len()
    }
}

#[cfg(test)]
mod presentation_log_tests {
    use super::*;

    #[test]
    fn a_repeated_token_is_one_canonical_text() {
        let mut log = PresentationLog::new();
        assert!(log.admit(&Token::new("<a>")).is_ok());
        assert!(log.admit(&Token::new("<a>")).is_ok());
        assert_eq!(log.presentations(), 2);
        assert_eq!(log.canonical_len(), 1);
        assert!(log.canonical_len() as u64 <= log.presentations());
    }
}
