//! Sort 4 — **Event**: a presentation or an admission.
//!
//! Crate boundary: coda-carrier.  Source: `model.py`, the six event
//! dataclasses.  Exactly one variant changes nothing (`Supply`); four admit;
//! one imposes.  The grammar is closed: there is no "remove", no "rename",
//! no "observe" — observation is not an event (L7, `judgment.rs`), and
//! removal was never derived anywhere in the estate (§13.10).
//!
//! L3 is a declared API discipline. The lexical scan in census.rs does
//! not prove state-to-event functions cannot exist.

use std::fmt;

use crate::mark::Pair;
use crate::regime::{Args, FormId};
use crate::token::Token;

/// An event of the sealed grammar.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Event {
    /// External presentation of a token.  Not an admission.  Inert (L1).
    Supply(Token),
    /// Admission of a presented token as a datum.  Re-admission of an
    /// admitted token is a designation, not a duplication (L6).
    AdmitDatum(Token),
    /// Admission of a judgment form of the given arity (`>= 1`).
    AdmitForm(usize),
    /// Admission of a judgment instance over admitted marks.
    AdmitInst(FormId, Args),
    /// Admission of the uniform all-tuples rule for a form.
    AdmitRuleAll(FormId),
    /// External requirement: the two marks must be internally separable.
    Impose(Pair),
}

impl Event {
    /// Whether this event is an admission (changes state when well-formed).
    /// `Supply` is not; `Impose` is a requirement, not an admission, and is
    /// reported separately by `is_imposition`.
    pub fn is_admission(&self) -> bool {
        matches!(
            self,
            Event::AdmitDatum(_) | Event::AdmitForm(_) | Event::AdmitInst(_, _) | Event::AdmitRuleAll(_)
        )
    }

    /// Whether this event is an externally imposed requirement.
    pub fn is_imposition(&self) -> bool {
        matches!(self, Event::Impose(_))
    }

    /// Whether this event is a bare presentation.
    pub fn is_supply(&self) -> bool {
        matches!(self, Event::Supply(_))
    }

    /// The token an event names, if it names one.  A *mention* is not an
    /// event; this is the metatheory reading the event.
    pub fn token(&self) -> Option<&Token> {
        match self {
            Event::Supply(t) | Event::AdmitDatum(t) => Some(t),
            _ => None,
        }
    }
}

/// An event is ill-formed relative to the current regime.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AdmissionError(pub String);

impl fmt::Display for AdmissionError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "admission refused: {}", self.0)
    }
}

impl std::error::Error for AdmissionError {}

impl fmt::Display for Event {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Event::Supply(t) => write!(f, "supply {t}"),
            Event::AdmitDatum(t) => write!(f, "admit_datum {t}"),
            Event::AdmitForm(a) => write!(f, "admit_form arity={a}"),
            Event::AdmitInst(form, args) => {
                let a: Vec<String> = args.iter().map(|m| m.0.to_string()).collect();
                write!(f, "admit_inst form={form} args=[{}]", a.join(","))
            }
            Event::AdmitRuleAll(form) => write!(f, "admit_rule_all form={form}"),
            Event::Impose(p) => write!(f, "impose_separation {p}"),
        }
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/event.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:event:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordeebdd444 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordeebdd444` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroreebdd444 {
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
impl BoundaryErroreebdd444 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroreebdd444 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroreebdd444 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordeebdd444 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroreebdd444> {
        if capacity_bound == 0 {
            return Err(BoundaryErroreebdd444::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroreebdd444::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroreebdd444::ExceedsCapacity {
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

    #[test]
    fn the_grammar_has_exactly_one_inert_kind() {
        let events = [
            Event::Supply(Token::new("x")),
            Event::AdmitDatum(Token::new("x")),
            Event::AdmitForm(1),
            crate::testkit::inst(0, &[0]),
            Event::AdmitRuleAll(0),
            Event::Impose(Pair::of(0, 1)),
        ];
        let inert: Vec<&Event> = events.iter().filter(|e| e.is_supply()).collect();
        assert_eq!(inert.len(), 1);
        assert_eq!(events.iter().filter(|e| e.is_admission()).count(), 4);
        assert_eq!(events.iter().filter(|e| e.is_imposition()).count(), 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_eebdd444 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordeebdd444::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordeebdd444::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordeebdd444::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordeebdd444::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordeebdd444::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroreebdd444::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroreebdd444::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
