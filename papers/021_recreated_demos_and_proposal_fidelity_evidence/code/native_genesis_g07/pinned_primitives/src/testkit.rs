//! Test-only helpers.  Compiled under `cfg(test)` only, so nothing here is
//! part of the crate's API, and the L3 census excludes this module by name
//! for exactly that reason.
//!
//! Both functions here return events.  The census fired on the second one
//! while it lived in `export.rs` — a live catch, not an injection — which is
//! why it lives here now.

use crate::event::Event;
use crate::mark::{Mark, Pair};
use crate::regime::{FormId, Regime};
use crate::token::Token;

/// An instance admission from indices.  A constructor from explicit
/// arguments; reads no state.
pub fn inst(form: FormId, args: &[usize]) -> Event {
    Event::AdmitInst(form, args.iter().map(|&a| Mark(a)).collect())
}

/// The event delta an edge applies to its parent, uniform for creation and
/// merge edges — the sealed `edge_events`.  The merge-witness
/// re-verification reconstructs the child from the parent this way.
pub fn edge_events(parent: &Regime, edge: &crate::tree::Edge) -> Vec<Event> {
    if edge.challenge == "supply" {
        let token = Token::new(format!("g{}", parent.n_data()));
        return vec![Event::Supply(token.clone()), Event::AdmitDatum(token)];
    }
    let inner = edge.challenge.trim_start_matches("separate(").trim_end_matches(')');
    let (i, j) = inner.split_once(", ").expect("separate(i, j)");
    let pair = Pair::of(i.parse().unwrap(), j.parse().unwrap());
    let mut out = vec![Event::Impose(pair)];
    out.extend(crate::candidate::delta_events(parent, &edge.response));
    out
}
