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

/// The sealed truth function: the `or` of the two bits.
pub fn derivable(r: &Regime, inst: &Inst) -> bool {
    coverage(r, inst.form) || admission(r, inst)
}

/// The profile of a datum: the set of contexts whose plugging is derivable.
pub fn profile(r: &Regime, d: Mark) -> BTreeSet<Context> {
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
