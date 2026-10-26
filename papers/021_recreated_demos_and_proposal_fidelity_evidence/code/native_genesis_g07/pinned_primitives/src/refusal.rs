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
