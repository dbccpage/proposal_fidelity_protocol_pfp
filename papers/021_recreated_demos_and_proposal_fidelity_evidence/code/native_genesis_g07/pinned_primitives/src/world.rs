//! Primitive — the **represented world**: the sealed carrier plus the two
//! gates and the refusal record, with a total step.
//!
//! Crate boundary: represented.  Source: Lean `Represented.World`
//! (`data, views, reqs, refusals, budget, augLicensed, notes`), `Event`,
//! `step`, `replay`, `represented_progress`, `rule1_repair_or_extension`.
//!
//! The Lean world carries views; this one carries the sealed `Regime`, so
//! the represented process runs on the same carrier the Challenge 3 numbers
//! come from. These are local implemented gates, not a proved Lean bridge.
//! Carrier events are supplied admissions outside the response gate:
//!
//! * a **response** is accepted iff the target is a recorded, currently
//!   violated requirement; the delta separates it and preserves every other
//!   requirement; the budget can pay; and, if the delta creates structure,
//!   the licence is granted.  Budget is spent.
//! * a **refusal** is accepted iff its certificate is *recomputed* to hold —
//!   the target is obstructed over the declared menu — and is not already
//!   recorded.
//! * **funding and licensing are events**, so they replay.
//! * **notes** are represented and inert (`support.rs`).
//!
//! With supported bounds and well-formed carriers, guard failure leaves the world
//! unchanged and returns a `Verdict::Refused(reason)`.  The Omega engine
//! records the verdict; nothing is absorbed silently.

use crate::admission::step;
use crate::bounds::Bounds;
use crate::budget::Budget;
use crate::candidate::{apply_delta, is_structure_creating, Delta};
use crate::certificate::Certificate;
use crate::event::Event;
use crate::license::License;
use crate::mark::Pair;
use crate::menu::menu;
use crate::obstruction::obstructed;
use crate::refusal::Refusal;
use crate::regime::Regime;
use crate::response::response_valid_naive;
use crate::separability::separable;

/// The represented state.  Every load-bearing input lives here.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct World {
    /// The admitted state.
    pub regime: Regime,
    /// The fuel.
    pub budget: Budget,
    /// The licence.
    pub license: License,
    /// Recorded unresolved obstructions.
    pub refusals: Vec<Refusal>,
    /// A represented, transition-inert commentary field.
    pub notes: Vec<u64>,
}

/// An event of the represented process.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum WorldEvent {
    /// A sealed-grammar event: supply, admissions, imposition.
    Carrier(Event),
    /// A response to a recorded requirement: rule 1 or rule 2, gated.
    Respond {
        /// The requirement.
        target: Pair,
        /// The delta.
        delta: Delta,
    },
    /// Record a refusal.  Needs a certificate that recomputes.
    Refuse {
        /// The requirement.
        target: Pair,
        /// The exhaustion certificate.
        certificate: Certificate,
    },
    /// A note.  Inert.
    Note(u64),
    /// Fund.
    SetBudget(u32),
    /// Authorize or withdraw structure creation.
    SetLicense(bool),
}

/// What a step did.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Verdict {
    /// The state changed.
    Applied,
    /// The event was well-formed and changed nothing (a supply, a
    /// designation, a repeated requirement).
    Inert,
    /// The event failed its guard; the state is unchanged.
    Refused(String),
}

impl World {
    /// The Lean genesis: nothing admitted, budget 0, licence granted, no
    /// notes.  The Omega engine always records its own funding and licence
    /// events, so the default never decides anything off the record.
    pub fn genesis() -> World {
        World { regime: Regime::genesis(), budget: Budget(0), license: License(true), refusals: Vec::new(), notes: Vec::new() }
    }

    /// A world over an existing regime, with genesis gates.
    pub fn from_regime(regime: Regime) -> World {
        World { regime, ..World::genesis() }
    }

    /// Replay a represented history from genesis.  Total; the verdicts are
    /// returned alongside so a refused event is visible.
    pub fn replay(h: &[WorldEvent], bounds: &Bounds) -> (World, Vec<Verdict>) {
        let mut w = World::genesis();
        let mut verdicts = Vec::with_capacity(h.len());
        for e in h {
            let (next, v) = step_world(&w, e, bounds);
            w = next;
            verdicts.push(v);
        }
        (w, verdicts)
    }

    /// The recorded requirements that are currently violated, in order.
    pub fn violated(&self) -> Vec<Pair> {
        self.regime.reqs.iter().copied().filter(|p| !separable(&self.regime, p.i, p.j)).collect()
    }

    /// Is every recorded requirement satisfied?
    pub fn quiescent(&self) -> bool {
        self.violated().is_empty()
    }

    /// Has this pair been refused?
    pub fn refused(&self, p: Pair) -> bool {
        self.refusals.iter().any(|r| r.target == p)
    }
}

/// The total step.
pub fn step_world(w: &World, e: &WorldEvent, bounds: &Bounds) -> (World, Verdict) {
    match e {
        WorldEvent::Carrier(ev) => match step(&w.regime, ev) {
            Ok(r) => {
                let v = if r == w.regime { Verdict::Inert } else { Verdict::Applied };
                (World { regime: r, ..w.clone() }, v)
            }
            Err(err) => (w.clone(), Verdict::Refused(err.0)),
        },
        WorldEvent::Respond { target, delta } => {
            if !w.regime.reqs.contains(target) {
                return (w.clone(), Verdict::Refused(format!("{target} is not a recorded requirement")));
            }
            if separable(&w.regime, target.i, target.j) {
                return (w.clone(), Verdict::Refused(format!("{target} is already satisfied; the response discharges nothing")));
            }
            match response_valid_naive(&w.regime, *target, delta) {
                Ok(true) => {}
                Ok(false) => return (w.clone(), Verdict::Refused("the delta does not separate the target or does not preserve a recorded requirement".into())),
                Err(err) => return (w.clone(), Verdict::Refused(err.0)),
            }
            let Some(paid) = w.budget.pay() else {
                return (w.clone(), Verdict::Refused("budget exhausted (progress_needs_budget)".into()));
            };
            if is_structure_creating(delta) && !w.license.granted() {
                return (w.clone(), Verdict::Refused("structure creation without licence (progress_needs_license)".into()));
            }
            let regime = apply_delta(&w.regime, delta).expect("validated above");
            (World { regime, budget: paid, ..w.clone() }, Verdict::Applied)
        }
        WorldEvent::Refuse { target, certificate } => {
            if w.refused(*target) {
                return (w.clone(), Verdict::Inert);
            }
            let m = menu(&w.regime, bounds);
            match obstructed(&w.regime, *target, &m) {
                Some(recomputed) if &recomputed == certificate => {
                    let mut refusals = w.refusals.clone();
                    refusals.push(Refusal { target: *target, certificate: certificate.clone() });
                    (World { refusals, ..w.clone() }, Verdict::Applied)
                }
                Some(_) => (w.clone(), Verdict::Refused("the certificate does not match the recomputed exhaustion".into())),
                None => (w.clone(), Verdict::Refused("no obstruction: the target is not violated or a repair exists (refusal_needs_certificate)".into())),
            }
        }
        WorldEvent::Note(n) => {
            let mut notes = w.notes.clone();
            notes.push(*n);
            (World { notes, ..w.clone() }, Verdict::Applied)
        }
        WorldEvent::SetBudget(n) => (World { budget: Budget(*n), ..w.clone() }, Verdict::Applied),
        WorldEvent::SetLicense(b) => (World { license: License(*b), ..w.clone() }, Verdict::Applied),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::candidate::Item;
    use crate::mark::Mark;
    use crate::reading::READING_L;

    fn c3_world(budget: u32, licence: bool) -> (World, Bounds) {
        let mut h: Vec<WorldEvent> = READING_L.genesis.iter().cloned().map(WorldEvent::Carrier).collect();
        h.push(WorldEvent::Carrier(Event::Impose(READING_L.target)));
        h.push(WorldEvent::SetBudget(budget));
        h.push(WorldEvent::SetLicense(licence));
        let bounds = Bounds::default();
        (World::replay(&h, &bounds).0, bounds)
    }

    #[test]
    fn a_response_must_name_a_recorded_violated_requirement() {
        let (w, bounds) = c3_world(3, true);
        let delta = vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])];
        let (_, v) = step_world(&w, &WorldEvent::Respond { target: Pair::of(0, 1), delta: delta.clone() }, &bounds);
        assert_eq!(v, Verdict::Applied);
        let mut unrecorded = w.clone();
        unrecorded.regime.reqs.clear();
        let (_, v) = step_world(&unrecorded, &WorldEvent::Respond { target: Pair::of(0, 1), delta }, &bounds);
        assert!(matches!(v, Verdict::Refused(_)));
    }

    #[test]
    fn a_proposal_never_self_executes_and_replay_is_total() {
        let (w, bounds) = c3_world(3, true);
        let bad = vec![Item::NewForm(1)]; // separates nothing
        let (w1, v) = step_world(&w, &WorldEvent::Respond { target: READING_L.target, delta: bad }, &bounds);
        assert!(matches!(v, Verdict::Refused(_)));
        assert_eq!(w1, w, "a refused proposal leaves no trace in the state");
        assert!(!w.quiescent());
        assert_eq!(w.violated(), vec![READING_L.target]);
    }

    #[test]
    fn a_supply_is_inert_in_the_world_too() {
        let (w, bounds) = c3_world(0, false);
        let (w1, v) = step_world(&w, &WorldEvent::Carrier(Event::Supply(crate::token::Token::new("x"))), &bounds);
        assert_eq!(v, Verdict::Inert);
        assert_eq!(w1, w);
    }
}
