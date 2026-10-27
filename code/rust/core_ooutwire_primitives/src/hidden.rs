//! Primitive — the **hidden-input countermodels**: seven ways an engine
//! leaves the replay semantics, each kept as code that demonstrably does.
//!
//! Crate boundary: represented.  Source: Lean `Represented` countermodels
//! `scheduler_hidden`, `gensym_hidden`, `oracle_hidden`,
//! `incomplete_search_false_alarm`, `augmentation_destroys_old_replay`,
//! `repetition_not_progress`, `order_sensitivity_splits_equivalents`.
//!
//! Each variant below consumes one input found in neither the represented
//! state nor the represented history.  In each, two runs with identical
//! represented state and history produce different results — exactly what
//! the kernel's type makes impossible, and exactly what a solver that
//! "just tries the first thing" does without noticing.
//!
//! These are not error cases.  They are the load-bearing negatives.  An
//! engine is the fold in `world.rs` *minus* everything in this file, and the
//! only way to know the subtraction happened is to keep the subtrahend.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_1c6890b2<T> {
    fn checked_invariant_1c6890b2(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_1c6890b2<T> for Option<T> {
    #[inline]
    fn checked_invariant_1c6890b2(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_1c6890b2<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_1c6890b2(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::bounds::Bounds;
use crate::candidate::{apply_delta, Delta};
use crate::event::Event;
use crate::regime::Regime;
use crate::token::Token;
use crate::world::{step_world, Verdict, World, WorldEvent};

/// Countermodel 1 — an unrepresented scheduler decides whether a response
/// fires.
pub fn step_sched(ext: bool, w: &World, e: &WorldEvent, bounds: &Bounds) -> (World, Verdict) {
    match e {
        WorldEvent::Respond { .. } if !ext => (w.clone(), Verdict::Refused("scheduler said no".into())),
        _ => step_world(w, e, bounds),
    }
}

/// Countermodel 2 — fresh names come from an unrepresented seed rather than
/// from the event.
pub fn step_gensym(seed: u64, w: &World, e: &WorldEvent, bounds: &Bounds) -> (World, Verdict) {
    match e {
        WorldEvent::Carrier(Event::AdmitDatum(_)) => {
            step_world(w, &WorldEvent::Carrier(Event::AdmitDatum(Token::new(format!("gensym{seed}")))), bounds)
        }
        _ => step_world(w, e, bounds),
    }
}

/// Countermodel 3 — a hidden oracle bypasses the validity check.
pub fn step_oracle(oracle: bool, w: &World, e: &WorldEvent, bounds: &Bounds) -> (World, Verdict) {
    match e {
        WorldEvent::Respond { target, delta } if oracle => {
            let ok = w.regime.reqs.contains(target) && w.budget.can_pay();
            if !ok {
                return (w.clone(), Verdict::Refused("even the oracle needs a recorded target and fuel".into()));
            }
            match apply_delta(&w.regime, delta) {
                Ok(regime) => (World { regime, budget: w.budget.pay().checked_invariant_1c6890b2("checked invariant"), ..w.clone() }, Verdict::Applied),
                Err(err) => (w.clone(), Verdict::Refused(err.0)),
            }
        }
        _ => step_world(w, e, bounds),
    }
}

/// Countermodel 5 — a destructive rewrite: replace the instance set instead
/// of adding to it.
pub fn overwrite_instances(r: &Regime, delta: &Delta) -> Result<Regime, crate::event::AdmissionError> {
    let mut cleared = r.clone();
    cleared.insts.clear();
    apply_delta(&cleared, delta)
}

/// Countermodel 7 — an order-sensitive semantics: check only the requirement
/// that was imposed *first*, reading the imposition order off the history
/// instead of the state.
pub fn valid_by_first_imposed(history: &[Event], r: &Regime, delta: &Delta) -> bool {
    let first = history.iter().find_map(|e| if let Event::Impose(p) = e { Some(*p) } else { None });
    match first {
        Some(p) => {
            let child = match apply_delta(r, delta) {
                Ok(c) => c,
                Err(_) => return false,
            };
            crate::separability::separable(&child, p.i, p.j)
        }
        None => false,
    }
}

/// A helper for the tests: a two-requirement world where one delta
/// separates the first pair and not the second.
#[cfg(test)]
fn two_requirement_situation() -> (Regime, Delta, crate::mark::Pair, crate::mark::Pair) {
    use crate::mark::Pair;
    let base = crate::replay::replay(&crate::reading::READING_F.genesis).unwrap();
    let base = crate::admission::step(&base, &Event::AdmitForm(1)).unwrap();
    let p01 = Pair::of(0, 1);
    let p12 = Pair::of(1, 2);
    // inst on datum 0 separates 0 from {1,2}: meets (0,1), not (1,2).
    let delta: Delta = vec![crate::candidate::Item::NewInst(0, vec![crate::mark::Mark(0)])];
    (base, delta, p01, p12)
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/hidden.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:hidden:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1c6890b2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1c6890b2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1c6890b2 {
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
impl BoundaryError1c6890b2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1c6890b2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1c6890b2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1c6890b2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1c6890b2> {
        if capacity_bound == 0 {
            return Err(BoundaryError1c6890b2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1c6890b2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1c6890b2::ExceedsCapacity {
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
    use crate::replay::replay;
    use crate::response::response_valid_naive;

    fn c3_world() -> (World, Bounds, WorldEvent) {
        let mut h: Vec<WorldEvent> = READING_L.genesis.iter().cloned().map(WorldEvent::Carrier).collect();
        h.push(WorldEvent::Carrier(Event::Impose(READING_L.target)));
        h.push(WorldEvent::SetBudget(3));
        h.push(WorldEvent::SetLicense(true));
        let bounds = Bounds::default();
        let respond = WorldEvent::Respond { target: READING_L.target, delta: vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])] };
        (World::replay(&h, &bounds).0, bounds, respond)
    }

    /// `scheduler_hidden`: same state, same event, different result.
    #[test]
    fn scheduler_hidden() {
        let (w, bounds, respond) = c3_world();
        let (a, _) = step_sched(true, &w, &respond, &bounds);
        let (b, _) = step_sched(false, &w, &respond, &bounds);
        assert_ne!(a, b);
        // The kernel: one answer.
        assert_eq!(step_world(&w, &respond, &bounds), step_world(&w, &respond, &bounds));
    }

    /// `gensym_hidden`: the admitted data depend on a seed no event carries.
    #[test]
    fn gensym_hidden() {
        let (w, bounds, _) = c3_world();
        let e = WorldEvent::Carrier(Event::AdmitDatum(Token::new("g2")));
        let (a, _) = step_gensym(0, &w, &e, &bounds);
        let (b, _) = step_gensym(99, &w, &e, &bounds);
        assert_ne!(a.regime.data, b.regime.data);
        let (k1, _) = step_world(&w, &e, &bounds);
        let (k2, _) = step_world(&w, &e, &bounds);
        assert_eq!(k1.regime.data, k2.regime.data);
    }

    /// `oracle_hidden`: a proposal that discharges nothing goes through
    /// only when the oracle says so.
    #[test]
    fn oracle_hidden() {
        let (w, bounds, _) = c3_world();
        let useless = WorldEvent::Respond { target: READING_L.target, delta: vec![Item::NewForm(1)] };
        let (a, va) = step_oracle(true, &w, &useless, &bounds);
        let (b, vb) = step_oracle(false, &w, &useless, &bounds);
        assert_eq!(va, Verdict::Applied);
        assert!(matches!(vb, Verdict::Refused(_)));
        assert_ne!(a, b);
    }

    /// `augmentation_destroys_old_replay`: overwriting destroys a satisfied
    /// requirement; the kernel's augmentation is append-only and preserves
    /// it.
    #[test]
    fn augmentation_destroys_old_replay() {
        let (base, delta, p01, p12) = two_requirement_situation();
        let r = apply_delta(&base, &delta).unwrap();
        assert!(crate::separability::separable(&r, p01.i, p01.j));
        let second: Delta = vec![Item::NewInst(0, vec![Mark(2)])];
        let appended = apply_delta(&r, &second).unwrap();
        assert!(crate::separability::separable(&appended, p01.i, p01.j), "append preserves");
        assert!(crate::separability::separable(&appended, p12.i, p12.j));
        let overwritten = overwrite_instances(&r, &second).unwrap();
        assert!(!crate::separability::separable(&overwritten, p01.i, p01.j), "overwrite destroys");
    }

    /// `repetition_not_progress`: three admissions of one token replay to
    /// the state of one; history length grows, state does not.
    #[test]
    fn repetition_not_progress() {
        let thrice = vec![Event::AdmitDatum(Token::new("t")); 3];
        let once = vec![Event::AdmitDatum(Token::new("t"))];
        assert_eq!(replay(&thrice).unwrap(), replay(&once).unwrap());
        assert_ne!(thrice.len(), once.len());
    }

    /// `order_sensitivity_splits_equivalents`: two histories imposing the
    /// same requirements in different orders reach the SAME regime, and a
    /// head-picking semantics gives them different verdicts.  The
    /// unrecorded selector is "first in the list".
    #[test]
    fn order_sensitivity_splits_equivalents() {
        let (base, delta, p01, p12) = two_requirement_situation();
        let h_a = vec![Event::Impose(p01), Event::Impose(p12)];
        let h_b = vec![Event::Impose(p12), Event::Impose(p01)];
        let ra = crate::replay::replay_from(&h_a, &base).unwrap();
        let rb = crate::replay::replay_from(&h_b, &base).unwrap();
        assert_eq!(ra, rb, "replay-equivalent");
        assert_ne!(valid_by_first_imposed(&h_a, &ra, &delta), valid_by_first_imposed(&h_b, &rb, &delta));
        // The kernel reads the state, and the state is the same.
        assert_eq!(
            response_valid_naive(&ra, p01, &delta).unwrap(),
            response_valid_naive(&rb, p01, &delta).unwrap()
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_1c6890b2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1c6890b2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1c6890b2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1c6890b2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1c6890b2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1c6890b2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1c6890b2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1c6890b2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
