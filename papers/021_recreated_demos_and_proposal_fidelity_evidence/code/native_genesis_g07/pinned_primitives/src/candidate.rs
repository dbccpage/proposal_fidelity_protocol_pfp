//! Sort 9 — **Candidate**: a one-step augmentation of the regime.
//!
//! Crate boundary: coda-price.  Source: `candidates.py` — `NewDatum`,
//! `NewForm`, `NewInst`, `NewRuleAll`, `canonical_delta`, `delta_events`,
//! `apply_delta`.
//!
//! A *delta* is a finite multiset of items, kept as a canonically sorted
//! list.  It is a **proposal**: nothing about a delta changes state.  Only
//! `delta_events` turns it into admission events, and only `replay` applies
//! those (`FW-MUTATE`).  `apply_delta` is a convenience that does both and
//! is the one function in this crate, outside `outside.rs`, that a reader
//! could mistake for "state producing events" — it does not: it takes a
//! declared candidate *and* a state, and the candidate came from the menu.
//!
//! The rule-1 / rule-2 dichotomy of the represented process is a property
//! of a delta: instances alone are a *same-level repair*; anything that adds
//! a datum, a form or a rule *creates structure*.  `is_structure_creating`
//! is what the licence gate reads (`license.rs`).

use std::fmt;

use crate::event::{AdmissionError, Event};
use crate::regime::{Args, FormId, Regime};
use crate::replay::replay_from;
use crate::token::Token;

/// One item of a candidate delta.  Variant order is the canonical item
/// order: data, forms, rules, instances.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Item {
    /// Admit one fresh datum.
    NewDatum,
    /// Admit one judgment form of the given arity.
    NewForm(usize),
    /// Admit the uniform all-tuples rule for a form.
    NewRuleAll(FormId),
    /// Admit one instance; the form may be one added by the same delta.
    NewInst(FormId, Args),
}

/// A canonical delta: items in canonical order.
pub type Delta = Vec<Item>;

/// Sort items into canonical order.
pub fn canonical_delta(mut items: Vec<Item>) -> Delta {
    items.sort();
    items
}

/// Translate a canonical delta into admission events.  Fresh data receive
/// tokens `w<index>` where the index is the admission position; indices
/// increase along any history, so the tokens are unique.
pub fn delta_events(base: &Regime, delta: &Delta) -> Vec<Event> {
    let mut out = Vec::with_capacity(delta.len());
    let mut n = base.n_data();
    for it in delta {
        match it {
            Item::NewDatum => {
                out.push(Event::AdmitDatum(Token::new(format!("w{n}"))));
                n += 1;
            }
            Item::NewForm(arity) => out.push(Event::AdmitForm(*arity)),
            Item::NewRuleAll(f) => out.push(Event::AdmitRuleAll(*f)),
            Item::NewInst(f, args) => out.push(Event::AdmitInst(*f, args.clone())),
        }
    }
    out
}

/// `⤳` — apply a delta by replaying its events.  Ill-formed deltas are
/// refused, never partially applied.
pub fn apply_delta(base: &Regime, delta: &Delta) -> Result<Regime, AdmissionError> {
    replay_from(&delta_events(base, delta), base)
}

/// Rule 2 reads this: does the delta add a datum, a form, or a rule?
pub fn is_structure_creating(delta: &Delta) -> bool {
    delta.iter().any(|it| !matches!(it, Item::NewInst(_, _)))
}

impl fmt::Display for Item {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Item::NewDatum => write!(f, "datum"),
            Item::NewForm(a) => write!(f, "form{a}"),
            Item::NewRuleAll(fm) => write!(f, "rule@{fm}"),
            Item::NewInst(fm, args) => {
                let a: Vec<String> = args.iter().map(|m| m.0.to_string()).collect();
                write!(f, "inst({fm};{})", a.join(","))
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mark::Mark;
    use crate::reading::READING_L;
    use crate::replay::replay;

    #[test]
    fn canonical_order_is_data_forms_rules_instances() {
        let d = canonical_delta(vec![
            Item::NewInst(0, vec![Mark(0)]),
            Item::NewRuleAll(0),
            Item::NewForm(1),
            Item::NewDatum,
        ]);
        assert_eq!(d, vec![Item::NewDatum, Item::NewForm(1), Item::NewRuleAll(0), Item::NewInst(0, vec![Mark(0)])]);
    }

    #[test]
    fn a_delta_is_a_proposal_until_it_is_replayed() {
        let base = replay(&READING_L.genesis).unwrap();
        let d = canonical_delta(vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])]);
        let events = delta_events(&base, &d);
        assert_eq!(events.len(), 2);
        let child = apply_delta(&base, &d).unwrap();
        assert_eq!(child.n_forms(), 1);
        assert_eq!(base.n_forms(), 0, "the base was not touched");
    }

    #[test]
    fn fresh_data_get_unique_tokens_by_position() {
        let base = replay(&READING_L.genesis).unwrap();
        let d = vec![Item::NewDatum, Item::NewDatum];
        let ev = delta_events(&base, &d);
        assert_eq!(ev[0], Event::AdmitDatum(Token::new("w2")));
        assert_eq!(ev[1], Event::AdmitDatum(Token::new("w3")));
        assert_eq!(apply_delta(&base, &d).unwrap().n_data(), 4);
    }

    #[test]
    fn instances_alone_are_repair_and_anything_else_creates_structure() {
        assert!(!is_structure_creating(&vec![Item::NewInst(0, vec![Mark(0)])]));
        assert!(is_structure_creating(&vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])]));
        assert!(is_structure_creating(&vec![Item::NewDatum]));
        assert!(is_structure_creating(&vec![Item::NewRuleAll(0)]));
    }
}
