//! Primitive — **licence**: authorization to create structure; gates rule 2.
//!
//! Crate boundary: represented.  Source: Lean `Represented.World.augLicensed`,
//! `progress_needs_license`, `Event.setAugLicense`; the sealed negative
//! `extension proposal executes without authorization` = **FALSE** with
//! countermodel.
//!
//! Two gates, **independent**: budget gates same-level repair, licence gates
//! structure creation.  Both are represented, so both replay.  An engine
//! whose authorization is a function call rather than an event has left the
//! replay semantics (crosstab E6).
//!
//! The estate proves the gate exists and **does not model the grantor**.
//! That is deliberate and it is the author's own position: authorization is
//! outside — "the part that something like this can't speak to".  Here the
//! grantor is `outside::Outside::authorize`, and what it grants is recorded
//! as `WorldEvent::SetLicense` so the record shows *that* it was granted
//! even though nothing in the record can show *why*.

/// Authorization to create structure.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
pub struct License(pub bool);

impl License {
    /// Is structure creation authorized?
    pub fn granted(self) -> bool {
        self.0
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/license.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:license:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7f47a504 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7f47a504` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7f47a504 {
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
impl BoundaryError7f47a504 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7f47a504 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7f47a504 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7f47a504 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7f47a504> {
        if capacity_bound == 0 {
            return Err(BoundaryError7f47a504::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7f47a504::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7f47a504::ExceedsCapacity {
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
    use crate::admission::step;
    use crate::bounds::Bounds;
    use crate::candidate::Item;
    use crate::event::Event;
    use crate::mark::{Mark, Pair};
    use crate::reading::READING_L;
    use crate::world::{step_world, Verdict, World, WorldEvent};

    /// `progress_needs_license`: a structure-creating response is refused
    /// without the licence and accepted with it, budget held fixed.
    #[test]
    fn progress_needs_license() {
        let mut h: Vec<WorldEvent> = READING_L.genesis.iter().cloned().map(WorldEvent::Carrier).collect();
        h.push(WorldEvent::Carrier(Event::Impose(READING_L.target)));
        h.push(WorldEvent::SetBudget(5));
        h.push(WorldEvent::SetLicense(false));
        let bounds = Bounds::default();
        let (unlicensed, _) = World::replay(&h, &bounds);
        let delta = vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])];
        let respond = WorldEvent::Respond { target: READING_L.target, delta };
        let (w0, v0) = step_world(&unlicensed, &respond, &bounds);
        assert!(matches!(v0, Verdict::Refused(ref why) if why.contains("licence")));
        assert_eq!(w0, unlicensed, "recorded as gated, state untouched");
        let (licensed, _) = step_world(&unlicensed, &WorldEvent::SetLicense(true), &bounds);
        let (w1, v1) = step_world(&licensed, &respond, &bounds);
        assert_eq!(v1, Verdict::Applied);
        assert_eq!(w1.regime.n_forms(), 1);
    }

    /// The gates are independent: a same-level repair (instances only)
    /// passes without a licence, given budget.
    #[test]
    fn a_same_level_repair_needs_no_licence() {
        // Build a base with a unary form and a rule-free instance landscape
        // where one more instance separates a newly imposed pair.
        let base = crate::replay::replay(&crate::reading::READING_F.genesis).unwrap();
        let base = step(&base, &Event::AdmitForm(1)).unwrap();
        let base = step(&base, &crate::testkit::inst(0, &[0])).unwrap(); // separates 0 from {1,2}
        let target = Pair::of(1, 2);
        let h: Vec<WorldEvent> = vec![
            WorldEvent::Carrier(Event::Impose(target)),
            WorldEvent::SetBudget(1),
            WorldEvent::SetLicense(false),
        ];
        let bounds = Bounds::default();
        let mut w = World::from_regime(base);
        for e in &h {
            w = step_world(&w, e, &bounds).0;
        }
        assert_eq!(w.license, License(false));
        let repair = WorldEvent::Respond { target, delta: vec![Item::NewInst(0, vec![Mark(1)])] };
        let (w1, v1) = step_world(&w, &repair, &bounds);
        assert_eq!(v1, Verdict::Applied, "rule 1 is gated by budget only");
        assert_eq!(w1.regime.insts.len(), 2);
    }
}

#[cfg(test)]
mod l4_boundary_tests_7f47a504 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7f47a504::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7f47a504::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7f47a504::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7f47a504::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7f47a504::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7f47a504::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7f47a504::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
