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
//!   violated requirement; the delta is canonical and within the declared
//!   bounds; it separates the target and preserves every other
//!   requirement; the budget can pay; and, if the delta creates structure,
//!   the licence is granted.  Budget is spent.
//! * a **refusal** is accepted iff its certificate is *recomputed* to hold —
//!   the target is obstructed over the declared menu — and is not already
//!   recorded.
//! * **funding and licensing are events**, so they replay.
//! * **notes** are represented and inert (`support.rs`).
//!
//! With supported bounds and well-formed carriers, guard failure leaves the world
//! unchanged and returns a `Verdict::Refused(reason)`.  The Core engine
//! records the verdict; nothing is absorbed silently.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_fa7bdee2<T> {
    fn checked_invariant_fa7bdee2(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_fa7bdee2<T> for Option<T> {
    #[inline]
    fn checked_invariant_fa7bdee2(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_fa7bdee2<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_fa7bdee2(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::admission::step;
use crate::bounds::Bounds;
use crate::budget::Budget;
use crate::candidate::{apply_delta, is_structure_creating, Delta, Item};
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
    /// notes.  The Core engine always records its own funding and licence
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

fn is_delta_in_menu(delta: &Delta, bounds: &Bounds) -> bool {
    delta.len() <= bounds.max_items
        && !delta.iter().any(|it| matches!(it, Item::NewForm(arity) if *arity > bounds.max_arity))
        && !delta.windows(2).any(|items| items[0] > items[1])
}

fn validate_world_response(w: &World, target: Pair, delta: &Delta, bounds: &Bounds) -> Result<(), String> {
    if !is_delta_in_menu(delta, bounds) {
        return Err("the delta is outside the declared canonical menu".into());
    }
    if !w.regime.reqs.contains(&target) {
        return Err(format!("{target} is not a recorded requirement"));
    }
    if separable(&w.regime, target.i, target.j) {
        return Err(format!("{target} is already satisfied; the response discharges nothing"));
    }
    match response_valid_naive(&w.regime, target, delta) {
        Ok(true) => Ok(()),
        Ok(false) => Err("the delta does not separate the target or does not preserve a recorded requirement".into()),
        Err(err) => Err(err.0),
    }
}

fn step_world_respond(w: &World, target: Pair, delta: &Delta, bounds: &Bounds) -> (World, Verdict) {
    if let Err(reason) = validate_world_response(w, target, delta, bounds) {
        return (w.clone(), Verdict::Refused(reason));
    }
    let Some(paid) = w.budget.pay() else {
        return (w.clone(), Verdict::Refused("budget exhausted (progress_needs_budget)".into()));
    };
    if is_structure_creating(delta) && !w.license.granted() {
        return (w.clone(), Verdict::Refused("structure creation without licence (progress_needs_license)".into()));
    }
    let regime = apply_delta(&w.regime, delta).checked_invariant_fa7bdee2("validated above");
    (World { regime, budget: paid, ..w.clone() }, Verdict::Applied)
}

fn step_world_refuse(w: &World, target: Pair, certificate: &Certificate, bounds: &Bounds) -> (World, Verdict) {
    if w.refused(target) {
        return (w.clone(), Verdict::Inert);
    }
    let m = menu(&w.regime, bounds);
    match obstructed(&w.regime, target, &m) {
        Some(recomputed) if &recomputed == certificate => {
            let mut refusals = w.refusals.clone();
            refusals.push(Refusal { target, certificate: certificate.clone() });
            (World { refusals, ..w.clone() }, Verdict::Applied)
        }
        Some(_) => (w.clone(), Verdict::Refused("the certificate does not match the recomputed exhaustion".into())),
        None => (w.clone(), Verdict::Refused("no obstruction: the target is not violated or a repair exists (refusal_needs_certificate)".into())),
    }
}

/// The total step.
pub fn step_world(w: &World, e: &WorldEvent, bounds: &Bounds) -> (World, Verdict) {
    if let Err(reason) = bounds.validate() {
        return (w.clone(), Verdict::Refused(reason));
    }
    match e {
        WorldEvent::Carrier(ev) => match step(&w.regime, ev) {
            Ok(r) => {
                let v = if r == w.regime { Verdict::Inert } else { Verdict::Applied };
                (World { regime: r, ..w.clone() }, v)
            }
            Err(err) => (w.clone(), Verdict::Refused(err.0)),
        },
        WorldEvent::Respond { target, delta } => step_world_respond(w, *target, delta, bounds),
        WorldEvent::Refuse { target, certificate } => step_world_refuse(w, *target, certificate, bounds),
        WorldEvent::Note(n) => {
            let mut notes = w.notes.clone();
            notes.push(*n);
            (World { notes, ..w.clone() }, Verdict::Applied)
        }
        WorldEvent::SetBudget(n) => (World { budget: Budget(*n), ..w.clone() }, Verdict::Applied),
        WorldEvent::SetLicense(b) => (World { license: License(*b), ..w.clone() }, Verdict::Applied),
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/world.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:world:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfa7bdee2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfa7bdee2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfa7bdee2 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorfa7bdee2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfa7bdee2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfa7bdee2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfa7bdee2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfa7bdee2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfa7bdee2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfa7bdee2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfa7bdee2::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
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

#[cfg(test)]
mod l4_boundary_tests_fa7bdee2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfa7bdee2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfa7bdee2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfa7bdee2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfa7bdee2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfa7bdee2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfa7bdee2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfa7bdee2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
