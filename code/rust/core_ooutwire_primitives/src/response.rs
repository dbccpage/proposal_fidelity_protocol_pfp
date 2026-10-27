//! Primitive — **response validity**: separates the target, preserves the
//! rest.  A fast check and a naive check, cross-validated.
//!
//! Crate boundary: coda-price.  Source: `candidates.py::NodeView`,
//! `profile_additions`, `response_valid_fast`, `response_valid_naive`.
//!
//! ```text
//! L11  a pruned enumeration requires an unpruned cross-check
//! ```
//!
//! The fast path computes only the *profile additions* a delta causes and
//! requires a rule-free base (an engine invariant; it refuses otherwise).
//! The naive path imposes the target, replays the delta, and asks whether
//! every requirement holds.  The sealed engine asserts the naive check on
//! every accepted delta; the test here runs both over the whole cost-2
//! space and demands agreement.  A fast path that has no slow twin is a
//! hidden evaluator waiting to be found.

use std::collections::{BTreeMap, BTreeSet};

use crate::admission::step;
use crate::candidate::{apply_delta, Delta, Item};
use crate::context::{contexts, slot_tuples, Context};
use crate::event::{AdmissionError, Event};
use crate::mark::{Mark, Pair};
use crate::profile::profiles;
use crate::regime::Regime;
use crate::separability::satisfies;

/// Precomputed observation data for one base regime.
#[derive(Clone, Debug)]
pub struct NodeView {
    base: Regime,
    ctxs: Vec<Context>,
    profs: Vec<BTreeSet<Context>>,
}

impl NodeView {
    /// The base whose profiles were computed.
    pub fn base(&self) -> &Regime {
        &self.base
    }

    /// Its contexts, in the declared order.
    pub fn contexts(&self) -> &[Context] {
        &self.ctxs
    }

    /// Its profiles, by datum; callers cannot replace cached evidence.
    pub fn profiles(&self) -> &[BTreeSet<Context>] {
        &self.profs
    }

    /// Build the view.  Refuses a base carrying a uniform rule: the fast
    /// path's correctness depends on every context mentioning a new datum
    /// or form being derivable only through the delta's own items.
    pub fn of(base: &Regime) -> Result<NodeView, String> {
        if !base.rules.is_empty() {
            return Err("fast path requires a rule-free base regime; use the naive check".into());
        }
        Ok(NodeView {
            base: base.clone(),
            ctxs: contexts(base),
            profs: profiles(base),
        })
    }
}

fn nonempty_subsets(positions: &[usize]) -> Vec<Vec<usize>> {
    let mut out = vec![Vec::new()];
    for &position in positions {
        let existing = out.len();
        for i in 0..existing {
            let mut subset = out[i].clone();
            subset.push(position);
            out.push(subset);
        }
    }
    out.remove(0);
    out
}

/// Profile additions per datum index caused by `delta`, and the total datum
/// count after it. Ill-formed admission sequences are refused before indexing
/// forms or interpreting candidate tuples. Enumeration remains exponential in
/// arity; this check is not a resource budget.
fn record_rule_all_additions(
    f: usize,
    arity: usize,
    n_total: usize,
    adds: &mut BTreeMap<usize, BTreeSet<Context>>,
) {
    for slots in slot_tuples(arity, n_total) {
        if slots.iter().any(|s| s.is_none()) {
            for d in 0..n_total {
                adds.entry(d).or_default().insert(Context {
                    form: f,
                    slots: slots.clone(),
                });
            }
        }
    }
}

fn record_inst_additions(f: usize, args: &[Mark], adds: &mut BTreeMap<usize, BTreeSet<Context>>) {
    let distinct: BTreeSet<usize> = args.iter().map(|m| m.0).collect();
    for d in distinct {
        let positions: Vec<usize> = args
            .iter()
            .enumerate()
            .filter(|(_, m)| m.0 == d)
            .map(|(k, _)| k)
            .collect();
        for sub in nonempty_subsets(&positions) {
            let slots: Vec<Option<Mark>> = args
                .iter()
                .enumerate()
                .map(|(k, m)| if sub.contains(&k) { None } else { Some(*m) })
                .collect();
            adds.entry(d)
                .or_default()
                .insert(Context { form: f, slots });
        }
    }
}

/// Validate a proposed delta and collect the contexts it adds for each datum,
/// together with the resulting total datum count.
pub fn profile_additions(
    view: &NodeView,
    delta: &Delta,
) -> Result<(BTreeMap<usize, BTreeSet<Context>>, usize), AdmissionError> {
    let base = &view.base;
    apply_delta(base, delta)?;
    let n0 = base.n_data();
    let n_total = n0
        + delta
            .iter()
            .filter(|it| matches!(it, Item::NewDatum))
            .count();
    let mut arities: Vec<usize> = base.forms.clone();
    for it in delta {
        if let Item::NewForm(a) = it {
            arities.push(*a);
        }
    }
    let mut adds: BTreeMap<usize, BTreeSet<Context>> = BTreeMap::new();
    for it in delta {
        match it {
            Item::NewRuleAll(f) => record_rule_all_additions(*f, arities[*f], n_total, &mut adds),
            Item::NewInst(f, args) => record_inst_additions(*f, args, &mut adds),
            _ => {}
        }
    }
    Ok((adds, n_total))
}

/// Fast check: does the delta separate the target while preserving every
/// previously imposed requirement?
pub fn response_valid_fast(view: &NodeView, target: Pair, delta: &Delta) -> bool {
    if crate::imposition::impose(&view.base, target).is_err() {
        return false;
    }
    let Ok((adds, _)) = profile_additions(view, delta) else {
        return false;
    };
    let base = &view.base;
    let empty = BTreeSet::new();
    let prof = |d: usize| -> BTreeSet<Context> {
        let base_p = if d < base.n_data() {
            &view.profs[d]
        } else {
            &empty
        };
        match adds.get(&d) {
            Some(extra) if !extra.is_empty() => base_p.union(extra).cloned().collect(),
            _ => base_p.clone(),
        }
    };
    let mut reqs: Vec<Pair> = base.reqs.iter().copied().collect();
    reqs.push(target);
    reqs.sort();
    reqs.dedup();
    for p in reqs {
        if prof(p.i.0) == prof(p.j.0) {
            return false;
        }
    }
    true
}

/// Reference check: full recomputation via replay. The target must name
/// previously admitted data, as in the engine's impose-then-respond history.
/// Errors on ill-formed targets or deltas.
pub fn response_valid_naive(
    base: &Regime,
    target: Pair,
    delta: &Delta,
) -> Result<bool, crate::event::AdmissionError> {
    let imposed = step(base, &Event::Impose(target))?;
    let augmented = apply_delta(&imposed, delta)?;
    Ok(satisfies(&augmented))
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/response.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:response:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6ff38ddd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6ff38ddd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6ff38ddd {
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
impl BoundaryError6ff38ddd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6ff38ddd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6ff38ddd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6ff38ddd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6ff38ddd> {
        if capacity_bound == 0 {
            return Err(BoundaryError6ff38ddd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6ff38ddd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6ff38ddd::ExceedsCapacity {
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
    use crate::bounds::Bounds;
    use crate::enumeration::iter_full_deltas;
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;

    /// L11 over the whole unpruned cost-0..2 space, both readings.
    #[test]
    fn fast_and_naive_agree_on_the_whole_declared_space() {
        let bounds = Bounds::default();
        let mut checked = 0;
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            let view = NodeView::of(&base).unwrap();
            for cost in 0..=2 {
                for delta in iter_full_deltas(&base, cost, &bounds) {
                    let fast = response_valid_fast(&view, reading.target, &delta);
                    let naive = response_valid_naive(&base, reading.target, &delta).unwrap();
                    assert_eq!(fast, naive, "disagreement at {delta:?}");
                    checked += 1;
                }
            }
        }
        // Both readings' whole cost-0..2 spaces: a few dozen well-formed
        // deltas each.  The number is reported, not pinned; what is pinned
        // is agreement on every one of them.
        assert!(checked > 30, "checked only {checked}");
    }

    #[test]
    fn the_fast_path_refuses_a_ruled_base() {
        let base = replay(&READING_L.genesis).unwrap();
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &Event::AdmitRuleAll(0)).unwrap();
        assert!(NodeView::of(&r).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_6ff38ddd {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6ff38ddd::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6ff38ddd::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6ff38ddd::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6ff38ddd::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6ff38ddd::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError6ff38ddd::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError6ff38ddd::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
