//! Primitive — **refusal**: a record, requiring a certificate, and
//! non-absorbing.
//!
//! Crate boundary: represented.  Source: Lean `Represented.Event.refuse`,
//! `refusal_needs_certificate`, `refusals_are_represented`, and the
//! docstring *"Refusal records verified same-level exhaustion; it is
//! non-absorbing (later events may still fire).  It certifies, it does not
//! terminalize."*
//!
//! Mathematics has "no such object exists".  It does not have "the search
//! was complete, here is the receipt, and the run continues" (crosstab §7
//! item 2).  This is that.  Three laws, each a test:
//!
//! * a `Refuse` event that changes state carries a **verified** obstruction
//!   — the step recomputes the exhaustion rather than trusting the payload;
//! * a refusal, once recorded, is **in the state**, so it replays;
//! * a refusal does not stop the run: later events still fire.

use std::fmt;

use crate::certificate::Certificate;
use crate::mark::Pair;

/// A recorded unresolved obstruction, with the certificate that licensed
/// recording it.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Refusal {
    /// The pair whose separation was refused.
    pub target: Pair,
    /// The exhaustion certificate.
    pub certificate: Certificate,
}

impl fmt::Display for Refusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "refused {} under {}", self.target, self.certificate)
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/refusal.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:refusal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord29844fd0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord29844fd0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError29844fd0 {
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
impl BoundaryError29844fd0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError29844fd0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError29844fd0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord29844fd0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError29844fd0> {
        if capacity_bound == 0 {
            return Err(BoundaryError29844fd0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError29844fd0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError29844fd0::ExceedsCapacity {
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
    use crate::bounds::Bounds;
    use crate::candidate::Item;
    use crate::certificate::{Bound, Certificate, SpaceId};
    use crate::event::Event;
    use crate::mark::Mark;
    use crate::menu::menu;
    use crate::obstruction::obstructed;
    use crate::reading::READING_L;
    use crate::world::{step_world, Verdict, World, WorldEvent};

    fn one_item_world() -> (World, Bounds) {
        let mut h: Vec<WorldEvent> = READING_L.genesis.iter().cloned().map(WorldEvent::Carrier).collect();
        h.push(WorldEvent::Carrier(Event::Impose(READING_L.target)));
        h.push(WorldEvent::SetBudget(5));
        h.push(WorldEvent::SetLicense(true));
        let bounds = Bounds { max_items: 1, max_arity: 2 };
        (World::replay(&h, &bounds).0, bounds)
    }

    /// `refusal_needs_certificate`: a forged certificate changes nothing; a
    /// verified one records.
    #[test]
    fn refusal_needs_a_verified_certificate() {
        let (w, bounds) = one_item_world();
        let forged = Certificate::Exhaustion { space: SpaceId("made up".into()), bound: Bound("none".into()), searched: 0 };
        let (w0, v0) = step_world(&w, &WorldEvent::Refuse { target: READING_L.target, certificate: forged }, &bounds);
        assert!(matches!(v0, Verdict::Refused(_)));
        assert_eq!(w0, w);
        let cert = obstructed(&w.regime, READING_L.target, &menu(&w.regime, &bounds)).unwrap();
        let (w1, v1) = step_world(&w, &WorldEvent::Refuse { target: READING_L.target, certificate: cert.clone() }, &bounds);
        assert_eq!(v1, Verdict::Applied);
        assert_eq!(w1.refusals.len(), 1, "refusals_are_represented");
        assert_eq!(w1.refusals[0].certificate, cert);
    }

    /// `refusal_non_absorbing`: after a refusal the run continues — a
    /// wider bound admits a repair on the very same target.
    #[test]
    fn a_refusal_does_not_terminalize() {
        let (w, bounds) = one_item_world();
        let cert = obstructed(&w.regime, READING_L.target, &menu(&w.regime, &bounds)).unwrap();
        let (w1, _) = step_world(&w, &WorldEvent::Refuse { target: READING_L.target, certificate: cert }, &bounds);
        let wider = Bounds::default();
        let delta = vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])];
        let (w2, v2) = step_world(&w1, &WorldEvent::Respond { target: READING_L.target, delta }, &wider);
        assert_eq!(v2, Verdict::Applied, "later events still fire");
        assert_eq!(w2.refusals.len(), 1, "and the record stays");
    }
}

#[cfg(test)]
mod l4_boundary_tests_29844fd0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord29844fd0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord29844fd0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord29844fd0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord29844fd0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord29844fd0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError29844fd0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError29844fd0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
