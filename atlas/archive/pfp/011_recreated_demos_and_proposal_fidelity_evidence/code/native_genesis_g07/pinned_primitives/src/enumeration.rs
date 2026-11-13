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
    out
}

/// Unpruned enumeration of every well-formed delta of the given item count
/// (0, 1, or 2).  Deliberately brute force; the cross-check's reference.
pub fn iter_full_deltas(base: &Regime, cost: usize, bounds: &Bounds) -> Vec<Delta> {
    match cost {
        0 => return vec![Vec::new()],
        1 => return iter_cost1_items(base, bounds).into_iter().map(|it| vec![it]).collect(),
        2 => {}
        _ => panic!("full enumeration is declared only for cost <= 2"),
    }
    let n0 = base.n_data();
    let mut universe: Vec<Item> = vec![Item::NewDatum];
    for arity in 1..=bounds.max_arity {
        universe.push(Item::NewForm(arity));
    }
    let max_form = base.n_forms() + 1;
    let max_arity_any = std::iter::once(bounds.max_arity).chain(base.forms.iter().copied()).max().unwrap();
    for f in 0..max_form {
        universe.push(Item::NewRuleAll(f));
        for arity in 1..=max_arity_any {
            for args in arg_tuples(n0 + 1, arity) {
                universe.push(Item::NewInst(f, args));
            }
        }
    }
    let mut seen: BTreeSet<Delta> = BTreeSet::new();
    let mut out = Vec::new();
    for a in &universe {
        for b in &universe {
            let delta = canonical_delta(vec![a.clone(), b.clone()]);
            if !seen.insert(delta.clone()) {
                continue;
            }
            if apply_delta(base, &delta).is_ok() {
                out.push(delta);
            }
        }
    }
    out
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
