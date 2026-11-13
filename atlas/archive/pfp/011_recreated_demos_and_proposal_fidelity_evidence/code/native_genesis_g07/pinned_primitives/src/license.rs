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
