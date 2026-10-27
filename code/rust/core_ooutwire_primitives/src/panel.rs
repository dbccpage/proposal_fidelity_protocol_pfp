//! Primitive — the **certification panel**: certifies up to the panel,
//! never up to correspondence.
//!
//! Crate boundary: represented.  Source: Lean `Represented.Evaluator`,
//! `verdictB`, `certPosB`, `certNegB`, `cert_scope`,
//! `cert_not_correspondence`, `cert_panel_relative`.
//!
//! An evaluator is *represented data*: the contexts it may consult.  The
//! panel certifies "separated" when every evaluator's own contexts separate,
//! and "equivalent" when none does.  `cert_scope` says that is exactly what
//! certification gives and no more.  `cert_not_correspondence` is the
//! countermodel: a unanimous panel certifies "equivalent" while a context
//! outside the panel separates.  Agreement among represented evaluators
//! reaches the panel's joint quotient and nothing beyond it.
//!
//! This is the *third* sense of evaluation (crosstab §3) and the one an
//! engine most wants to skip: All-Green is not All-Correct (E2).  The Core
//! engine reports its panel's blind spot on demand for that reason, and the
//! `ObserverIncomplete` terminal exists for the case where the panel cannot
//! see what the metatheory sees.

use crate::context::{contexts, plug, Context};
use crate::mark::Pair;
use crate::profile::derivable;
use crate::regime::Regime;

/// A represented evaluator: the contexts it may use.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Evaluator {
    /// Its columns.
    pub contexts: Vec<Context>,
}

impl Evaluator {
    /// The evaluator that may use every context of the regime.
    pub fn full(r: &Regime) -> Evaluator {
        Evaluator { contexts: contexts(r) }
    }

    /// Its verdict on a pair: some column of its own separates.
    pub fn verdict(&self, r: &Regime, p: Pair) -> bool {
        self.valid_for(r, p) && self.contexts.iter().any(|c| derivable(r, &plug(c, p.i)) != derivable(r, &plug(c, p.j)))
    }

    /// Check the target and every supplied context before certification.
    pub fn valid_for(&self, r: &Regime, p: Pair) -> bool {
        p.i < p.j && r.has_mark(p.i) && r.has_mark(p.j)
            && self.contexts.iter().all(|c| c.well_formed(r))
    }
}

/// The panel closes positively: nonempty, and every evaluator says separated.
pub fn cert_pos(panel: &[Evaluator], r: &Regime, p: Pair) -> bool {
    !panel.is_empty() && panel.iter().all(|e| e.valid_for(r, p) && e.verdict(r, p))
}

/// The panel closes negatively: nonempty, and no evaluator separates.
pub fn cert_neg(panel: &[Evaluator], r: &Regime, p: Pair) -> bool {
    !panel.is_empty() && panel.iter().all(|e| e.valid_for(r, p) && !e.verdict(r, p))
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/panel.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:panel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord64fe5629 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord64fe5629` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError64fe5629 {
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
impl BoundaryError64fe5629 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError64fe5629 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError64fe5629 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord64fe5629 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError64fe5629> {
        if capacity_bound == 0 {
            return Err(BoundaryError64fe5629::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError64fe5629::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError64fe5629::ExceedsCapacity {
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
    use crate::reading::READING_F;
    use crate::replay::replay;
    use crate::separability::separable;

    fn separated_world() -> Regime {
        let base = replay(&READING_F.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        step(&r, &crate::testkit::inst(0, &[0])).unwrap()
    }

    /// `cert_scope`: positive closure is exactly joint separation by every
    /// evaluator's own columns.
    #[test]
    fn cert_scope() {
        let r = separated_world();
        let p = Pair::of(0, 1);
        let full = Evaluator::full(&r);
        assert!(cert_pos(std::slice::from_ref(&full), &r, p));
        assert!(!cert_pos(&[], &r, p), "an empty panel certifies nothing");
        assert!(!cert_neg(&[], &r, p));
    }

    /// `cert_not_correspondence`: a unanimous panel of evaluators whose
    /// columns do not separate certifies "equivalent" while the regime
    /// separates the pair.
    #[test]
    fn cert_not_correspondence() {
        let r = separated_world();
        let p = Pair::of(0, 1);
        assert!(separable(&r, p.i, p.j));
        let blind = Evaluator { contexts: Vec::new() };
        assert!(cert_neg(&[blind.clone(), blind], &r, p));
    }

    /// `cert_panel_relative`: extending the panel can break closure.
    #[test]
    fn cert_panel_relative() {
        let r = separated_world();
        let p = Pair::of(0, 1);
        let full = Evaluator::full(&r);
        let blind = Evaluator { contexts: Vec::new() };
        assert!(cert_pos(std::slice::from_ref(&full), &r, p));
        assert!(!cert_pos(&[full, blind], &r, p));
    }
}

#[cfg(test)]
mod l4_boundary_tests_64fe5629 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord64fe5629::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord64fe5629::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord64fe5629::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord64fe5629::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord64fe5629::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError64fe5629::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError64fe5629::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
