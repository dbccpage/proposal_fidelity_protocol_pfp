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
//! The naive path replays the delta, imposes the target, and asks whether
//! every requirement holds.  The sealed engine asserts the naive check on
//! every accepted delta; the test here runs both over the whole cost-2
//! space and demands agreement.  A fast path that has no slow twin is a
//! hidden evaluator waiting to be found.

use std::collections::{BTreeMap, BTreeSet};

use crate::admission::step;
use crate::candidate::{apply_delta, Delta, Item};
use crate::context::{contexts, slot_tuples, Context};
use crate::event::Event;
use crate::mark::{Mark, Pair};
use crate::profile::profiles;
use crate::regime::Regime;
use crate::separability::satisfies;

/// Precomputed observation data for one base regime.
#[derive(Clone, Debug)]
pub struct NodeView {
    /// The base.
    pub base: Regime,
    /// Its contexts.
    pub ctxs: Vec<Context>,
    /// Its profiles, by datum.
    pub profs: Vec<BTreeSet<Context>>,
}

impl NodeView {
    /// Build the view.  Refuses a base carrying a uniform rule: the fast
    /// path's correctness depends on every context mentioning a new datum
    /// or form being derivable only through the delta's own items.
    pub fn of(base: &Regime) -> Result<NodeView, String> {
        if !base.rules.is_empty() {
            return Err("fast path requires a rule-free base regime; use the naive check".into());
        }
        Ok(NodeView { base: base.clone(), ctxs: contexts(base), profs: profiles(base) })
    }
}

fn nonempty_subsets(positions: &[usize]) -> Vec<Vec<usize>> {
    let mut out = Vec::new();
    let n = positions.len();
    for mask in 1..(1u32 << n) {
        out.push((0..n).filter(|k| mask & (1 << k) != 0).map(|k| positions[k]).collect());
    }
    out
}

/// Profile additions per datum index caused by `delta`, and the total datum
/// count after it.
pub fn profile_additions(view: &NodeView, delta: &Delta) -> (BTreeMap<usize, BTreeSet<Context>>, usize) {
    let base = &view.base;
    let n0 = base.n_data();
    let n_total = n0 + delta.iter().filter(|it| matches!(it, Item::NewDatum)).count();
    let mut arities: Vec<usize> = base.forms.clone();
    for it in delta {
        if let Item::NewForm(a) = it {
            arities.push(*a);
        }
    }
    let mut adds: BTreeMap<usize, BTreeSet<Context>> = BTreeMap::new();
    for it in delta {
        match it {
            Item::NewRuleAll(f) => {
                let arity = arities[*f];
                for slots in slot_tuples(arity, n_total) {
                    if slots.iter().any(|s| s.is_none()) {
                        for d in 0..n_total {
                            adds.entry(d).or_default().insert(Context { form: *f, slots: slots.clone() });
                        }
                    }
                }
            }
            Item::NewInst(f, args) => {
                let distinct: BTreeSet<usize> = args.iter().map(|m| m.0).collect();
                for d in distinct {
                    let positions: Vec<usize> =
                        args.iter().enumerate().filter(|(_, m)| m.0 == d).map(|(k, _)| k).collect();
                    for sub in nonempty_subsets(&positions) {
                        let slots: Vec<Option<Mark>> = args
                            .iter()
                            .enumerate()
                            .map(|(k, m)| if sub.contains(&k) { None } else { Some(*m) })
                            .collect();
                        adds.entry(d).or_default().insert(Context { form: *f, slots });
                    }
                }
            }
            _ => {}
        }
    }
    (adds, n_total)
}

/// Fast check: does the delta separate the target while preserving every
/// previously imposed requirement?
pub fn response_valid_fast(view: &NodeView, target: Pair, delta: &Delta) -> bool {
    let (adds, _) = profile_additions(view, delta);
    let base = &view.base;
    let empty = BTreeSet::new();
    let prof = |d: usize| -> BTreeSet<Context> {
        let base_p = if d < base.n_data() { &view.profs[d] } else { &empty };
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

/// Reference check: full recomputation via replay.  Errors on ill-formed
/// deltas.
pub fn response_valid_naive(base: &Regime, target: Pair, delta: &Delta) -> Result<bool, crate::event::AdmissionError> {
    let augmented = apply_delta(base, delta)?;
    let augmented = step(&augmented, &Event::Impose(target))?;
    Ok(satisfies(&augmented))
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
