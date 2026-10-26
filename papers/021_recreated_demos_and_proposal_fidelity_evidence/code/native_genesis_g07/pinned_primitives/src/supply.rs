//! Primitive — **supply**: external presentation, provably inert.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::Supply` and the first
//! branch of `step`; Lean `Inertia.supply_no_op`; sealed claim
//! `CL-0-INERTIA`.  Every world in the estate — the sealed one, both second
//! derivation tracks, the boundary derivation — shares this law.
//!
//! ```text
//! L1   ▹   Γ ▹ t = Γ           supply is inert
//! ```
//!
//! Three things the estate keeps apart, and which this file exists to keep
//! apart in your head:
//!
//! * **mention** — the metatheory naming a token; not an event at all;
//! * **supply** — the token is handed in; an event; changes nothing;
//! * **admission** — the token is admitted as a datum; the only state change.
//!
//! "To mention an object is to have it" is what every outside formalism
//! assumes and what this estate refuses (`FW-ABSENCE`, and crosstab §7 item 4).

use crate::regime::Regime;
use crate::token::Token;

/// `▹` — present a token to a regime.  Returns the regime unchanged.
///
/// The signature is the law: the return value cannot depend on the token
/// because the body never reads it.  The test below checks it anyway,
/// because "cannot" is a claim and a test is a receipt for the claim.
pub fn supply(regime: &Regime, _token: &Token) -> Regime {
    regime.clone()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;

    #[test]
    fn l1_supply_is_inert_at_genesis() {
        let g = Regime::genesis();
        assert_eq!(supply(&g, &Token::new("<>")), g);
        assert_eq!(step(&g, &Event::Supply(Token::new("<>"))).unwrap(), g);
    }

    /// Inert on every regime the two readings reach, not only at genesis.
    #[test]
    fn l1_supply_is_inert_on_reached_regimes() {
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            for tok in ["<>", "<a>", "<ab>", "fresh"] {
                assert_eq!(step(&base, &Event::Supply(Token::new(tok))).unwrap(), base);
            }
        }
    }

    /// Challenge 1: a supply-only history certifies genesis.
    #[test]
    fn a_supply_only_history_replays_to_genesis() {
        let h = vec![Event::Supply(Token::new("<>")), Event::Supply(Token::new("<a>"))];
        assert_eq!(replay(&h).unwrap(), Regime::genesis());
    }
}
