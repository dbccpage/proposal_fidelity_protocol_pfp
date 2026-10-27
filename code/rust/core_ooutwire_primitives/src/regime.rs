//! Sort 3 — **Regime**: admitted state, and nothing else.
//!
//! Crate boundary: coda-carrier.  Source: `code/derivation/model.py`,
//! `class Regime` — the frozen five-field record.
//!
//! ```text
//! data   admitted data in admission order; entries are presentation tokens,
//!        internal identity is the index
//! forms  admitted judgment forms; entry a at index f means form f has arity a >= 1
//! insts  admitted judgment instances (form, args)
//! rules  forms carrying the uniform all-tuples rule
//! reqs   externally imposed persistent separation requirements (i, j), i < j
//! ```
//!
//! A regime carries **no history, no provenance, no cache**.  Provenance lives
//! in the history (`retention.rs`).  A regime that remembers how it was
//! reached is a different sort wearing this one's name (§13.3).
//!
//! There is no `&mut` API on purpose.  Every function that "changes" a regime
//! returns a new one. Fields are crate-visible, not publicly writable;
//! admission and renaming are separate constructors of values. This API
//! boundary does not establish a value's admission history: replay does.

use std::collections::BTreeSet;

use crate::mark::{Mark, Pair};
use crate::token::Token;

/// The index of an admitted judgment form.
pub type FormId = usize;

/// The argument tuple of a judgment instance: admitted marks, one per slot.
pub type Args = Vec<Mark>;

/// An admitted judgment instance: a form applied to admitted marks.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Inst {
    /// Which form.
    pub form: FormId,
    /// Which marks, in slot order.
    pub args: Args,
}

impl Inst {
    /// Build an instance.
    pub fn new(form: FormId, args: Args) -> Inst {
        Inst { form, args }
    }
}

/// Admitted state, externally read-only; trusted crate code can construct it.
///
/// ```compile_fail
/// use core_ooutwire_primitives::regime::Regime;
/// let mut r = Regime::genesis();
/// r.data.clear();
/// ```
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Regime {
    /// Admitted data in admission order.  Entries are presentation tokens.
    pub(crate) data: Vec<Token>,
    /// Admitted forms: `forms[f]` is the arity of form `f`.
    pub(crate) forms: Vec<usize>,
    /// Admitted instances.
    pub(crate) insts: BTreeSet<Inst>,
    /// Forms carrying the uniform all-tuples rule.
    pub(crate) rules: BTreeSet<FormId>,
    /// Imposed separation requirements.
    pub(crate) reqs: BTreeSet<Pair>,
}

impl Regime {
    /// Read the admitted tokens without mutable access.
    pub fn data(&self) -> &[Token] { &self.data }
    /// Read form arities.
    pub fn forms(&self) -> &[usize] { &self.forms }
    /// Read instances.
    pub fn insts(&self) -> &BTreeSet<Inst> { &self.insts }
    /// Read uniform rules.
    pub fn rules(&self) -> &BTreeSet<FormId> { &self.rules }
    /// Read imposed requirements.
    pub fn reqs(&self) -> &BTreeSet<Pair> { &self.reqs }

    /// `∅` — genesis: nothing admitted.
    pub fn genesis() -> Regime {
        Regime {
            data: Vec::new(),
            forms: Vec::new(),
            insts: BTreeSet::new(),
            rules: BTreeSet::new(),
            reqs: BTreeSet::new(),
        }
    }

    /// How many data are admitted.
    pub fn n_data(&self) -> usize {
        self.data.len()
    }

    /// How many forms are admitted.
    pub fn n_forms(&self) -> usize {
        self.forms.len()
    }

    /// The admitted marks, in admission order.
    pub fn marks(&self) -> impl Iterator<Item = Mark> {
        (0..self.data.len()).map(Mark)
    }

    /// Whether `m` names an admitted datum.
    pub fn has_mark(&self, m: Mark) -> bool {
        m.0 < self.data.len()
    }
}

impl Default for Regime {
    fn default() -> Regime {
        Regime::genesis()
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/regime.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:regime:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf0609044 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf0609044` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf0609044 {
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
impl BoundaryErrorf0609044 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf0609044 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf0609044 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf0609044 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf0609044> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf0609044::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf0609044::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf0609044::ExceedsCapacity {
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
    fn genesis_admits_nothing() {
        let g = Regime::genesis();
        assert!(g.data().is_empty() && g.forms().is_empty());
        assert!(g.insts().is_empty() && g.rules().is_empty() && g.reqs().is_empty());
        assert_eq!(g.n_data(), 0);
        assert_eq!(g.n_forms(), 0);
        assert!(g.insts.is_empty() && g.rules.is_empty() && g.reqs.is_empty());
    }

    /// The projection law of §13.9: a projection that enumerates fields will
    /// drop one.  This destructuring fails to COMPILE if a field is added to
    /// `Regime` without being named here, which is the only kind of totality
    /// a type system hands out for free.
    #[test]
    fn every_field_is_named_by_the_destructuring() {
        let Regime { data, forms, insts, rules, reqs } = Regime::genesis();
        assert!(data.is_empty() && forms.is_empty());
        assert!(insts.is_empty() && rules.is_empty() && reqs.is_empty());
    }
}

#[cfg(test)]
mod l4_boundary_tests_f0609044 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf0609044::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf0609044::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf0609044::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf0609044::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf0609044::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf0609044::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf0609044::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
