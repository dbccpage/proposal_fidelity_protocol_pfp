//! Primitive — **replay**: rebuild a regime from genesis.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::replay`; Lean
//! `Represented.replay`, `replay_deterministic`, `replay_nil`,
//! `replay_append`; sealed `export.verify_full_export`.
//!
//! ```text
//! L4   ⟳(h, ∅) is a function of h          replay is deterministic
//! ```
//!
//! The crosstab calls this *the most load-bearing primitive in the estate*
//! (§3), and the reason is not that folds are deep.  It is that every
//! certified result is required to be the replay of its recorded history, so
//! a claim that cannot be replayed is not a result — it is a claim.
//!
//! `replay_append` is the one algebraic law: replaying `h1 ++ h2` from `Γ`
//! equals replaying `h2` from the replay of `h1`.  The crosstab grades it `=`
//! against the fold in the Category column; here it is a test.

use crate::admission::step;
use crate::event::{AdmissionError, Event};
use crate::regime::Regime;

/// `⟳` — replay a history from a base regime.  Refuses the first ill-formed
/// event rather than skipping it.
pub fn replay_from(h: &[Event], base: &Regime) -> Result<Regime, AdmissionError> {
    let mut r = base.clone();
    for e in h {
        r = step(&r, e)?;
    }
    Ok(r)
}

/// `⟳(h, ∅)` — replay from genesis.
pub fn replay(h: &[Event]) -> Result<Regime, AdmissionError> {
    replay_from(h, &Regime::genesis())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mark::Pair;
    use crate::reading::{READING_F, READING_L};
    use crate::token::Token;

    #[test]
    fn replay_nil_is_the_identity() {
        let base = replay(&READING_F.genesis).unwrap();
        assert_eq!(replay_from(&[], &base).unwrap(), base);
    }

    #[test]
    fn replay_append_is_the_fold_law() {
        let h1 = READING_L.genesis.clone();
        let h2 = vec![
            Event::Impose(Pair::of(0, 1)),
            Event::AdmitForm(1),
            crate::testkit::inst(0, &[0]),
        ];
        let mut h = h1.clone();
        h.extend(h2.iter().cloned());
        let whole = replay(&h).unwrap();
        let parts = replay_from(&h2, &replay(&h1).unwrap()).unwrap();
        assert_eq!(whole, parts);
    }

    #[test]
    fn l4_replay_is_deterministic() {
        let a = replay(&READING_F.genesis).unwrap();
        let b = replay(&READING_F.genesis).unwrap();
        assert_eq!(a, b);
    }

    #[test]
    fn replay_refuses_the_first_ill_formed_event() {
        let h = vec![Event::AdmitDatum(Token::new("x")), crate::testkit::inst(0, &[0])];
        assert!(replay(&h).is_err());
    }
}
