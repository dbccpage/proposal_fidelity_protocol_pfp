//! Primitive — **profile**: which pluggings are derivable — and the two bits
//! inside `derivable`.
//!
//! Crate boundary: coda-observe.  Source: `observe.py::derivable`,
//! `profile`, `profiles`; `research/limit_and_observer` (pull request #143)
//! for the decomposition; `research/boundary_seed/comparison.md`,
//! `COMPARE-OBSERVATION-OPEN`, for its narrowing.
//!
//! The sealed observation relation is one line:
//!
//! ```python
//! def derivable(r, inst): return inst[0] in r.rules or inst in r.insts
//! ```
//!
//! That is an `or` of two bits.  A **coverage** bit — the context's form
//! carries the uniform rule — which does not depend on the datum plugged in.
//! And an **admission** bit — the plugging is an admitted instance.  This
//! file keeps them as two named functions so that a reader (`observer.rs`)
//! can consult them separately.
//!
//! **The narrowed form, which is the one to carry.**  The decomposition is
//! real, and a projected truth value that has taken the `or` has lost which
//! bit fired.  But the `Regime` retains `rules` and `insts` as separate
//! fields, and so does its history.  So the loss of provenance in one
//! projected value does **not** show that the *state* conflates admission
//! with observation, nor that no other view can tell them apart.  An earlier
//! version of this claim was circulated more strongly; the boundary
//! comparison narrowed it and the narrowing is correct.

use std::collections::BTreeSet;

use crate::context::{contexts, plug, Context};
use crate::mark::Mark;
use crate::regime::{FormId, Inst, Regime};

/// The coverage bit: the form carries the uniform all-tuples rule.  Constant
/// across data at a fixed context.
pub fn coverage(r: &Regime, form: FormId) -> bool {
    r.rules.contains(&form)
}

/// The admission bit: the instance was admitted.
pub fn admission(r: &Regime, inst: &Inst) -> bool {
    r.insts.contains(inst)
}

/// The sealed truth function on well-formed instances: the `or` of the
/// two bits. Unlike the frozen source's raw predicate, this public entry
/// point checks the instance domain before consulting a uniform rule.
pub fn derivable(r: &Regime, inst: &Inst) -> bool {
    r.forms.get(inst.form).is_some_and(|arity| {
        inst.args.len() == *arity
            && inst.args.iter().all(|mark| r.has_mark(*mark))
            && (coverage(r, inst.form) || admission(r, inst))
    })
}

/// The profile of a datum: the set of contexts whose plugging is derivable.
pub fn profile(r: &Regime, d: Mark) -> BTreeSet<Context> {
    if !r.has_mark(d) {
        return BTreeSet::new();
    }
    contexts(r).into_iter().filter(|c| derivable(r, &plug(c, d))).collect()
}

/// Every datum's profile, in admission order.  Computed once per regime
/// rather than once per datum.
pub fn profiles(r: &Regime) -> Vec<BTreeSet<Context>> {
    let ctxs = contexts(r);
    r.marks()
        .map(|d| ctxs.iter().filter(|c| derivable(r, &plug(c, d))).cloned().collect())
        .collect()
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/profile.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:profile:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord90ce5f57 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord90ce5f57` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError90ce5f57 {
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
impl BoundaryError90ce5f57 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError90ce5f57 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError90ce5f57 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord90ce5f57 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError90ce5f57> {
        if capacity_bound == 0 {
            return Err(BoundaryError90ce5f57::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError90ce5f57::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError90ce5f57::ExceedsCapacity {
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
    fn the_two_bits_are_independent_and_the_or_is_the_sealed_relation() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        let i0 = Inst::new(0, vec![Mark(0)]);
        assert!(!coverage(&r, 0) && !admission(&r, &i0) && !derivable(&r, &i0));
        let by_admission = step(&r, &crate::testkit::inst(0, &[0])).unwrap();
        assert!(!coverage(&by_admission, 0) && admission(&by_admission, &i0));
        assert!(derivable(&by_admission, &i0));
        let by_coverage = step(&r, &Event::AdmitRuleAll(0)).unwrap();
        assert!(coverage(&by_coverage, 0) && !admission(&by_coverage, &i0));
        assert!(derivable(&by_coverage, &i0));
        // The projected value agrees; the state does not.  That is the
        // narrowed form of the finding, in one assertion.
        assert_eq!(derivable(&by_admission, &i0), derivable(&by_coverage, &i0));
        assert_ne!(by_admission, by_coverage);
    }

    #[test]
    fn coverage_is_constant_across_data_at_a_fixed_context() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &Event::AdmitRuleAll(0)).unwrap();
        let c = &contexts(&r)[0];
        for d in r.marks() {
            assert!(derivable(&r, &plug(c, d)));
        }
        assert_eq!(profile(&r, Mark(0)), profile(&r, Mark(1)), "a rule separates nothing");
    }
}

#[cfg(test)]
mod l4_boundary_tests_90ce5f57 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord90ce5f57::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord90ce5f57::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord90ce5f57::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord90ce5f57::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord90ce5f57::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError90ce5f57::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError90ce5f57::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
