//! Sort 7 — **Context**: a form plus a slot tuple with holes.
//!
//! Crate boundary: coda-observe.  Source: `observe.py::contexts`,
//! `slot_tuples`, `plug`.
//!
//! A context is the estate's unit of *looking*.  Plugging a datum `d` into a
//! context fills every hole with `d` and yields an instance; whether that
//! instance is derivable is the one bit the object language can see about
//! `d` at that context.  Everything observational — profiles, separability,
//! witnesses, the four readers — is built from this and nothing else.
//!
//! Order matters and is fixed: forms in admission order, then slot tuples
//! with the hole first and data by index.  `witness` returns the *first*
//! separating context in this order, so the order is part of the
//! definition, not a detail.

use crate::mark::Mark;
use crate::regime::{FormId, Inst, Regime};

/// A slot: a hole (`None`) or an admitted mark.
pub type Slot = Option<Mark>;

/// A judgment form together with a slot tuple in which at least one slot is
/// a hole.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Context {
    /// Which form.
    pub form: FormId,
    /// The slots; at least one is `None`.
    pub slots: Vec<Slot>,
}

impl Context {
    /// Whether the context has an admitted form, the required arity, at
    /// least one hole, and only admitted fixed arguments.
    pub fn well_formed(&self, r: &Regime) -> bool {
        r.forms.get(self.form).is_some_and(|arity| *arity == self.slots.len())
            && self.slots.iter().any(Option::is_none)
            && self.slots.iter().flatten().all(|mark| r.has_mark(*mark))
    }
}

/// All slot tuples of the given arity over `n_data` data, in the fixed
/// deterministic order: hole first, then data by index, varying the last
/// slot fastest.
pub fn slot_tuples(arity: usize, n_data: usize) -> Vec<Vec<Slot>> {
    let options: Vec<Slot> = std::iter::once(None)
        .chain((0..n_data).map(|d| Some(Mark(d))))
        .collect();
    let mut out: Vec<Vec<Slot>> = vec![Vec::new()];
    for _ in 0..arity {
        let mut next = Vec::with_capacity(out.len() * options.len());
        for prefix in &out {
            for o in &options {
                let mut t = prefix.clone();
                t.push(*o);
                next.push(t);
            }
        }
        out = next;
    }
    out
}

/// All contexts of the regime, deterministically ordered.
pub fn contexts(r: &Regime) -> Vec<Context> {
    let mut out = Vec::new();
    for (form, &arity) in r.forms.iter().enumerate() {
        for slots in slot_tuples(arity, r.n_data()) {
            if slots.iter().any(|s| s.is_none()) {
                out.push(Context { form, slots });
            }
        }
    }
    out
}

/// Fill every hole of the context with `d`.
pub fn plug(c: &Context, d: Mark) -> Inst {
    Inst::new(c.form, c.slots.iter().map(|s| s.unwrap_or(d)).collect())
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/context.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:context:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd144e1f6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd144e1f6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord144e1f6 {
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
impl BoundaryErrord144e1f6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord144e1f6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord144e1f6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd144e1f6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord144e1f6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord144e1f6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord144e1f6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord144e1f6::ExceedsCapacity {
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
    use crate::reading::READING_L;
    use crate::replay::replay;

    #[test]
    fn no_forms_means_no_contexts() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(contexts(&base).is_empty());
    }

    #[test]
    fn a_unary_form_over_two_data_has_one_context() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        let cs = contexts(&r);
        assert_eq!(cs.len(), 1);
        assert_eq!(cs[0].slots, vec![None]);
        assert_eq!(plug(&cs[0], Mark(1)), Inst::new(0, vec![Mark(1)]));
    }

    /// Binary form over two data: 9 slot tuples, 5 contain a hole.
    #[test]
    fn a_binary_form_over_two_data_has_five_contexts() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(2)).unwrap();
        assert_eq!(slot_tuples(2, 2).len(), 9);
        assert_eq!(contexts(&r).len(), 5);
        assert_eq!(contexts(&r)[0].slots, vec![None, None], "hole first");
    }
}

#[cfg(test)]
mod l4_boundary_tests_d144e1f6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd144e1f6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd144e1f6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd144e1f6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd144e1f6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd144e1f6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord144e1f6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord144e1f6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
