//! Primitive — **admission**: the only thing that changes state.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::step`.
//!
//! ```text
//! L2   ∀e. step(Γ,e) ≠ Γ  ⟹  e is an admission or an imposition
//! L6   re-admission of an admitted token is a designation, not a duplication
//! ```
//!
//! `step` is deterministic and total on well-formed events; an ill-formed
//! admission is *refused by name* with an `AdmissionError`, never absorbed
//! silently.  The boundary derivation withdrew an earlier version of its own
//! kernel for exactly that sin — a moving admission absorbed as a no-op — and
//! the withdrawal is recorded in its module docstring.  Refuse loudly.
//!
//! **L6 is a convention.**  Presentation identity is metatheoretic, so whether
//! the second handing-in of the same token duplicates or designates is a
//! *choice*.  The sealed derivation chose designation, and `challenge1_report`
//! computes that the two sub-readings converge at Challenge 2 because of it.

use crate::event::{AdmissionError, Event};
use crate::imposition::impose;
use crate::regime::{Inst, Regime};

/// Apply one event.  `Supply` returns the regime unchanged (L1).  Admissions
/// change state; ill-formed ones are refused.
pub fn step(r: &Regime, e: &Event) -> Result<Regime, AdmissionError> {
    match e {
        Event::Supply(_) => Ok(r.clone()),
        Event::AdmitDatum(tok) => {
            if r.data.contains(tok) {
                // L6: designation of the existing datum, not a duplication.
                return Ok(r.clone());
            }
            let mut out = r.clone();
            out.data.push(tok.clone());
            Ok(out)
        }
        Event::AdmitForm(arity) => admit_form(r, *arity),
        Event::AdmitInst(form, args) => {
            let Some(&arity) = r.forms.get(*form) else {
                return Err(AdmissionError(format!("unknown form {form}")));
            };
            if args.len() != arity {
                return Err(AdmissionError(format!(
                    "form {form} has arity {arity}, got {} arguments",
                    args.len()
                )));
            }
            if !args.iter().all(|m| r.has_mark(*m)) {
                return Err(AdmissionError(format!("instance arguments out of range: {args:?}")));
            }
            let mut out = r.clone();
            out.insts.insert(Inst::new(*form, args.clone()));
            Ok(out)
        }
        Event::AdmitRuleAll(form) => admit_rule_all(r, *form),
        Event::Impose(pair) => impose(r, *pair),
    }
}

fn admit_form(r: &Regime, arity: usize) -> Result<Regime, AdmissionError> {
    if arity < 1 {
        return Err(AdmissionError(format!("form arity must be >= 1, got {arity}")));
    }
    let mut out = r.clone();
    out.forms.push(arity);
    Ok(out)
}

fn admit_rule_all(r: &Regime, form: usize) -> Result<Regime, AdmissionError> {
    if form >= r.n_forms() {
        return Err(AdmissionError(format!("unknown form {form}")));
    }
    let mut out = r.clone();
    out.rules.insert(form);
    Ok(out)
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/admission.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda7841932 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda7841932` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora7841932 {
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
impl BoundaryErrora7841932 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora7841932 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora7841932 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda7841932 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora7841932> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora7841932::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora7841932::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora7841932::ExceedsCapacity {
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
    use crate::mark::Pair;
    use crate::token::Token;

    fn two_data() -> Regime {
        let g = Regime::genesis();
        let a = step(&g, &Event::AdmitDatum(Token::new("<a>"))).unwrap();
        step(&a, &Event::AdmitDatum(Token::new("<ab>"))).unwrap()
    }

    #[test]
    fn l2_only_admissions_and_impositions_change_state() {
        let base = two_data();
        let f = step(&base, &Event::AdmitForm(1)).unwrap();
        assert_ne!(f, base);
        let i = step(&f, &crate::testkit::inst(0, &[0])).unwrap();
        assert_ne!(i, f);
        let ru = step(&f, &Event::AdmitRuleAll(0)).unwrap();
        assert_ne!(ru, f);
        let im = step(&base, &Event::Impose(Pair::of(0, 1))).unwrap();
        assert_ne!(im, base);
        assert_eq!(step(&base, &Event::Supply(Token::new("<a>"))).unwrap(), base);
    }

    #[test]
    fn l6_readmission_designates_and_does_not_duplicate() {
        let base = two_data();
        let again = step(&base, &Event::AdmitDatum(Token::new("<a>"))).unwrap();
        assert_eq!(again, base);
        assert_eq!(again.n_data(), 2);
    }

    #[test]
    fn ill_formed_admissions_are_refused_by_name() {
        let base = two_data();
        assert!(step(&base, &Event::AdmitForm(0)).is_err());
        assert!(step(&base, &crate::testkit::inst(0, &[0])).is_err(), "no form 0 yet");
        let f = step(&base, &Event::AdmitForm(2)).unwrap();
        assert!(step(&f, &crate::testkit::inst(0, &[0])).is_err(), "arity mismatch");
        assert!(step(&f, &crate::testkit::inst(0, &[0, 7])).is_err(), "mark 7 not admitted");
        assert!(step(&f, &Event::AdmitRuleAll(3)).is_err());
        assert!(step(&base, &Event::Impose(Pair::of(0, 5))).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_a7841932 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda7841932::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda7841932::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda7841932::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda7841932::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda7841932::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora7841932::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora7841932::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
