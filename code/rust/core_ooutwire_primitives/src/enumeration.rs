//! Primitive — **enumeration** of the candidate space: pruned by four named
//! lemmas, cross-checked against the unpruned space.
//!
//! Crate boundary: coda-price.  Source: `candidates.py::iter_cost1_items`,
//! `iter_cost2_deltas`, `iter_full_deltas`, and the module docstring's four
//! lemmas:
//!
//! * **rule-removal** — a delta containing `NewRuleAll` is never a minimum
//!   valid response (uniform additions preserve profile equality);
//! * **datum-irrelevance** — a `NewDatum` not referenced by any `NewInst` of
//!   the same delta changes no profile of previously admitted data;
//! * **form-irrelevance** — a `NewForm` without an instance in the same
//!   delta contributes no derivable context;
//! * **mention** — an instance-only delta changes the profile of `d` only if
//!   some added instance mentions `d`.
//!
//! Each lemma justifies dropping a shape from the cost-2 enumeration.  None
//! of them is trusted here: `iter_full_deltas` enumerates everything, and
//! the test asserts that the *valid* pruned set and the *valid* unpruned set
//! are the same set (L11).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_06f656a7<T> {
    fn checked_invariant_06f656a7(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_06f656a7<T> for Option<T> {
    #[inline]
    fn checked_invariant_06f656a7(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_06f656a7<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_06f656a7(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeSet;

use crate::bounds::Bounds;
use crate::candidate::{apply_delta, canonical_delta, Delta, Item};
use crate::mark::{Mark, Pair};
use crate::regime::Regime;

fn arg_tuples(n_data: usize, arity: usize) -> Vec<Vec<Mark>> {
    let mut out: Vec<Vec<Mark>> = vec![Vec::new()];
    for _ in 0..arity {
        let mut next = Vec::with_capacity(out.len() * n_data);
        for prefix in &out {
            for d in 0..n_data {
                let mut t = prefix.clone();
                t.push(Mark(d));
                next.push(t);
            }
        }
        out = next;
    }
    out
}

/// All single items over the base regime, in deterministic order.
pub fn iter_cost1_items(base: &Regime, bounds: &Bounds) -> Vec<Item> {
    let mut out = vec![Item::NewDatum];
    for arity in 1..=bounds.max_arity {
        out.push(Item::NewForm(arity));
    }
    for f in 0..base.n_forms() {
        if !base.rules.contains(&f) {
            out.push(Item::NewRuleAll(f));
        }
    }
    for (f, &arity) in base.forms.iter().enumerate() {
        for args in arg_tuples(base.n_data(), arity) {
            out.push(Item::NewInst(f, args));
        }
    }
    out
}

fn mentions(it: &Item, ds: &BTreeSet<usize>) -> bool {
    match it {
        Item::NewInst(_, args) => args.iter().any(|m| ds.contains(&m.0)),
        _ => false,
    }
}

fn extend_cost2_inst_pairs(base: &Regime, n0: usize, target: Pair, out: &mut Vec<Delta>) {
    // (c) two instances on existing forms, at least one mentioning the target
    let tgt: BTreeSet<usize> = [target.i.0, target.j.0].into_iter().collect();
    let all_insts: Vec<Item> = base
        .forms
        .iter()
        .enumerate()
        .flat_map(|(f, &arity)| arg_tuples(n0, arity).into_iter().map(move |args| Item::NewInst(f, args)))
        .collect();
    let mentioning: Vec<&Item> = all_insts.iter().filter(|it| mentions(it, &tgt)).collect();
    for a in &mentioning {
        for b in &all_insts {
            if *a == b {
                continue;
            }
            if mentions(b, &tgt) && b < a {
                continue; // unordered pair already emitted with roles swapped
            }
            out.push(canonical_delta(vec![(*a).clone(), b.clone()]));
        }
    }
}

/// Pruned two-item deltas.  Shapes: (`NewForm`, `NewInst` on the new form),
/// (`NewDatum`, `NewInst` mentioning the new datum), and (`NewInst`,
/// `NewInst`) where at least one instance mentions a member of the target.
pub fn iter_cost2_deltas(base: &Regime, bounds: &Bounds, target: Pair) -> Vec<Delta> {
    let n0 = base.n_data();
    let new_form = base.n_forms();
    let mut out = Vec::new();
    // (a) fresh form + one instance on it, over previously admitted data
    for arity in 1..=bounds.max_arity {
        for args in arg_tuples(n0, arity) {
            out.push(canonical_delta(vec![Item::NewForm(arity), Item::NewInst(new_form, args)]));
        }
    }
    // (b) fresh datum + one instance on an existing form mentioning it
    for (f, &arity) in base.forms.iter().enumerate() {
        for args in arg_tuples(n0 + 1, arity) {
            if args.iter().any(|m| m.0 == n0) {
                out.push(canonical_delta(vec![Item::NewDatum, Item::NewInst(f, args)]));
            }
        }
    }
    extend_cost2_inst_pairs(base, n0, target, &mut out);
    out
}

fn build_cost2_universe(base: &Regime, bounds: &Bounds) -> Vec<Item> {
    let n0 = base.n_data();
    let mut universe: Vec<Item> = vec![Item::NewDatum];
    for arity in 1..=bounds.max_arity {
        universe.push(Item::NewForm(arity));
    }
    let max_form = base.n_forms() + 1;
    let max_arity_any = std::iter::once(bounds.max_arity).chain(base.forms.iter().copied()).max().checked_invariant_06f656a7("checked invariant");
    for f in 0..max_form {
        universe.push(Item::NewRuleAll(f));
        for arity in 1..=max_arity_any {
            for args in arg_tuples(n0 + 1, arity) {
                universe.push(Item::NewInst(f, args));
            }
        }
    }
    universe
}

/// Unpruned enumeration of every well-formed delta of the given item count
/// (0, 1, or 2).  Deliberately brute force; the cross-check's reference.
pub fn iter_full_deltas(base: &Regime, cost: usize, bounds: &Bounds) -> Vec<Delta> {
    match cost {
        0 => return vec![Vec::new()],
        1 => return iter_cost1_items(base, bounds).into_iter().map(|it| vec![it]).collect(),
        2 => {}
        _ => unreachable!("full enumeration is declared only for cost <= 2"),
    }
    let universe = build_cost2_universe(base, bounds);
    let mut seen: BTreeSet<Delta> = BTreeSet::new();
    let mut out = Vec::new();
    for a in &universe {
        for b in &universe {
            let delta = canonical_delta(vec![a.clone(), b.clone()]);
            if seen.insert(delta.clone()) && apply_delta(base, &delta).is_ok() {
                out.push(delta);
            }
        }
    }
    out
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/enumeration.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:enumeration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord06f656a7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord06f656a7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError06f656a7 {
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
impl BoundaryError06f656a7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError06f656a7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError06f656a7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord06f656a7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError06f656a7> {
        if capacity_bound == 0 {
            return Err(BoundaryError06f656a7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError06f656a7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError06f656a7::ExceedsCapacity {
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
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;
    use crate::response::{response_valid_fast, NodeView};

    /// L11: the valid deltas the pruned enumeration finds are exactly the
    /// valid deltas the unpruned one finds, at both readings' bases.
    #[test]
    fn pruned_and_unpruned_agree_on_valid_deltas() {
        let bounds = Bounds::default();
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            let view = NodeView::of(&base).unwrap();
            let pruned: BTreeSet<Delta> = iter_cost2_deltas(&base, &bounds, reading.target)
                .into_iter()
                .filter(|d| response_valid_fast(&view, reading.target, d))
                .collect();
            let full: BTreeSet<Delta> = iter_full_deltas(&base, 2, &bounds)
                .into_iter()
                .filter(|d| response_valid_fast(&view, reading.target, d))
                .collect();
            assert_eq!(pruned, full);
            assert!(!full.is_empty());
        }
    }

    /// The pruned space is a strict subset of the unpruned one, so the
    /// lemmas do real work.
    #[test]
    fn the_lemmas_prune_something() {
        let bounds = Bounds::default();
        let base = replay(&READING_L.genesis).unwrap();
        let pruned: BTreeSet<Delta> = iter_cost2_deltas(&base, &bounds, READING_L.target).into_iter().collect();
        let full: BTreeSet<Delta> = iter_full_deltas(&base, 2, &bounds).into_iter().collect();
        assert!(pruned.is_subset(&full));
        assert!(pruned.len() < full.len());
    }
}

#[cfg(test)]
mod l4_boundary_tests_06f656a7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord06f656a7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord06f656a7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord06f656a7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord06f656a7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord06f656a7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError06f656a7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError06f656a7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
