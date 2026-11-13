//! Sort 5 — **History** (retention): a finite sequence of events.
//!
//! Crate boundary: coda-carrier.  Source: `List Event` throughout the Lean;
//! `model.py::replay(history)`; the boundary kernel's `mentioned` and
//! `supplied`.
//!
//! The history is the **only provenance**.  State is a fold of it
//! (`replay.rs`), and a regime carries none of it (`regime.rs`).  The three
//! readings below are metatheoretic: they read the history, they are not
//! object-language values, and a mention is not an event.

use std::collections::BTreeSet;

use crate::event::Event;
use crate::token::Token;

/// A retained history: events in the order they happened.
pub type History = Vec<Event>;

/// Tokens named by any event of the history.  A mention is not an event.
pub fn mentioned(h: &[Event]) -> BTreeSet<Token> {
    h.iter().filter_map(|e| e.token().cloned()).collect()
}

/// Tokens presented by a `Supply` event.
pub fn supplied(h: &[Event]) -> BTreeSet<Token> {
    h.iter()
        .filter_map(|e| match e {
            Event::Supply(t) => Some(t.clone()),
            _ => None,
        })
        .collect()
}

/// Tokens admitted by an `AdmitDatum` event.
pub fn admitted(h: &[Event]) -> BTreeSet<Token> {
    h.iter()
        .filter_map(|e| match e {
            Event::AdmitDatum(t) => Some(t.clone()),
            _ => None,
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reading::READING_L;

    /// The sealed reading L supplies `<>` and never admits it: mentioned and
    /// supplied, not admitted.  Three different sets, on purpose.
    #[test]
    fn supply_mention_and_admission_are_three_different_readings() {
        let h = &READING_L.genesis;
        let m = mentioned(h);
        let s = supplied(h);
        let a = admitted(h);
        assert!(m.contains(&Token::new("<>")));
        assert!(s.contains(&Token::new("<>")));
        assert!(!a.contains(&Token::new("<>")));
        assert_eq!(a.len(), 2);
        assert_eq!(s.len(), 3);
        assert_eq!(m, s, "in reading L every mentioned token was supplied");
    }
}
