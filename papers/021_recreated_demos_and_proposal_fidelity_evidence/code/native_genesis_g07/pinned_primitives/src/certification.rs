//! Primitive — **certification**: a claimed regime against its history.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::certify`.
//!
//! ```text
//! L5   Γ ⊨ h  ⟺  Γ = ⟳(h, ∅)          certification is replay
//! ```
//!
//! This is the *first* of the three senses of "certificate" the estate keeps
//! apart (crosstab §3): a regime against its history.  The other two — an
//! exhaustion certificate and a cancellation/witness certificate — are
//! different objects and live in `certificate.rs`.  An engine that has one
//! `certified: bool` field has collapsed three things into one and will be
//! wrong about at least two of them.

use crate::event::Event;
use crate::regime::Regime;
use crate::replay::replay;

/// `⊨` — does the claimed regime equal the replay of its history?
/// An ill-formed history certifies nothing.
pub fn certifies(h: &[Event], claimed: &Regime) -> bool {
    match replay(h) {
        Ok(r) => &r == claimed,
        Err(_) => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::reading::READING_L;
    use crate::token::Token;

    #[test]
    fn l5_a_regime_certifies_exactly_when_it_is_the_replay() {
        let h = READING_L.genesis.clone();
        let r = replay(&h).unwrap();
        assert!(certifies(&h, &r));
        let tampered = step(&r, &Event::AdmitDatum(Token::new("<extra>"))).unwrap();
        assert!(!certifies(&h, &tampered), "a state not reached by the history does not certify");
    }

    #[test]
    fn an_ill_formed_history_certifies_nothing() {
        let h = vec![crate::testkit::inst(0, &[0])];
        assert!(!certifies(&h, &Regime::genesis()));
    }
}
