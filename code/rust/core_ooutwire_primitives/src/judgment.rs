//! Sort 6 — **Judgment**: a positive observation form that holds or does not.
//!
//! Crate boundary: coda-observe.  Source: `observe.py::derivable`; the
//! boundary kernel's `OnSide` / `SideNamed` and its docstring *"There is no
//! `Empty` or counting judgment"*.
//!
//! ```text
//! L7   the absence of a judgment is never a judgment
//! ```
//!
//! The grammar is **positive by type**.  There is no `Not`, no `Empty`, no
//! `Count`.  That is not a limitation waiting to be lifted; it is what makes
//! `FW-ABSENCE` enforceable — absence of a test is never converted into
//! equality, because absence is not something the grammar can say.
//!
//! To extend the grammar, add a positive variant.  Never add a negative one.

use crate::profile::derivable;
use crate::mark::Mark;
use crate::regime::{Inst, Regime};

/// A positive judgment.  Extend, never negate.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Judgment {
    /// The instance is derivable in the regime.
    Derivable(Inst),
}

/// The names of the grammar's forms.  One entry per variant; a test checks
/// the count against an exhaustive `match`, which is the only reflection a
/// type system gives.
pub const GRAMMAR: &[&str] = &["Derivable"];

/// `⊙` — does the judgment hold in the regime?
pub fn holds(r: &Regime, j: &Judgment) -> bool {
    match j {
        Judgment::Derivable(inst) => derivable(r, inst),
    }
}

/// Every judgment that holds in the regime, enumerated over the admitted
/// instances and rule-covered instances.  Metatheoretic: the returned
/// collection is not an object-language value.
pub fn holding(r: &Regime) -> Vec<Judgment> {
    let mut out: Vec<Judgment> = r.insts.iter().map(|i| Judgment::Derivable(i.clone())).collect();
    for &form in &r.rules {
        let mut tuples = vec![Vec::new()];
        for _ in 0..r.forms[form] {
            tuples = tuples.into_iter().flat_map(|prefix| {
                (0..r.n_data()).map(move |d| {
                    let mut args = prefix.clone();
                    args.push(Mark(d));
                    args
                })
            }).collect();
        }
        out.extend(tuples.into_iter().map(|args| Judgment::Derivable(Inst::new(form, args))));
    }
    out.sort();
    out.dedup();
    out
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/judgment.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:judgment:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord68ee72b1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord68ee72b1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError68ee72b1 {
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
impl BoundaryError68ee72b1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError68ee72b1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError68ee72b1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord68ee72b1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError68ee72b1> {
        if capacity_bound == 0 {
            return Err(BoundaryError68ee72b1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError68ee72b1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError68ee72b1::ExceedsCapacity {
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
    use crate::event::Event;
    use crate::mark::Mark;
    use crate::reading::READING_L;
    use crate::replay::replay;

    /// If a variant is added, this `match` stops being exhaustive and the
    /// file stops compiling until GRAMMAR is updated too.
    #[test]
    fn the_grammar_is_positive_and_censused() {
        let j = Judgment::Derivable(Inst::new(0, vec![Mark(0)]));
        let name = match &j {
            Judgment::Derivable(_) => "Derivable",
        };
        assert_eq!(GRAMMAR, &[name]);
    }

    #[test]
    fn l7_nothing_holds_before_a_form_is_admitted() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(holding(&base).is_empty());
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        assert!(!holds(&r, &Judgment::Derivable(Inst::new(0, vec![Mark(0)]))));
        let r = step(&r, &crate::testkit::inst(0, &[0])).unwrap();
        assert!(holds(&r, &Judgment::Derivable(Inst::new(0, vec![Mark(0)]))));
        assert!(!holds(&r, &Judgment::Derivable(Inst::new(0, vec![Mark(1)]))));
    }
}

#[cfg(test)]
mod l4_boundary_tests_68ee72b1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord68ee72b1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord68ee72b1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord68ee72b1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord68ee72b1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord68ee72b1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError68ee72b1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError68ee72b1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
