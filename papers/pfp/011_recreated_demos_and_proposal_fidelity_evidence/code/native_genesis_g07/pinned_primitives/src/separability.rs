//! Primitive — **internal separability**: two data are separable exactly
//! when their profiles differ.
//!
//! Crate boundary: coda-observe.  Source: `observe.py::separable`,
//! `witness`, `collapsed_pairs`, `satisfies`; sealed claim `CL-2-COLLAPSE`;
//! Lean `Inertia.collapsed_of_no_insts`.
//!
//! This is the *declared* meaning of internal separability in the sealed
//! derivation: behavioural separation by positive derivability.  The boundary
//! derivation declares a different one — no permitted automorphism carries
//! one mark to the other — and the comparison records that **no equivalence
//! between the two senses is proved** (`B3-REQUIREMENT`).  Two words, two
//! definitions, one file each.
//!
//! **`FW-ABSENCE`.**  A collapsed pair is a pair with *equal profiles*.  It
//! is not an equal pair.  The two tokens are distinct in the metatheory; the
//! object language simply has no context that tells them apart yet.
//! Absence of a separating test is never converted into equality.

use crate::context::{contexts, plug, Context};
use crate::mark::{Mark, Pair};
use crate::profile::{derivable, profile, profiles};
use crate::regime::Regime;

/// `≭` — do the two marks have different profiles?
pub fn separable(r: &Regime, i: Mark, j: Mark) -> bool {
    profile(r, i) != profile(r, j)
}

/// The first context, in the fixed order, at which the two marks differ.
/// `None` when the pair is collapsed.
pub fn witness(r: &Regime, i: Mark, j: Mark) -> Option<Context> {
    contexts(r)
        .into_iter()
        .find(|c| derivable(r, &plug(c, i)) != derivable(r, &plug(c, j)))
}

/// All pairs `i < j` with equal profiles, lexicographically ordered.  These
/// are the unresolved separation demands the closure policy will reissue.
pub fn collapsed_pairs(r: &Regime) -> Vec<Pair> {
    let profs = profiles(r);
    let n = r.n_data();
    let mut out = Vec::new();
    for i in 0..n {
        for j in (i + 1)..n {
            if profs[i] == profs[j] {
                out.push(Pair::of(i, j));
            }
        }
    }
    out
}

/// Do all imposed requirements hold?
pub fn satisfies(r: &Regime) -> bool {
    let profs = profiles(r);
    r.reqs.iter().all(|p| profs[p.i.0] != profs[p.j.0])
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;

    /// Sealed Challenge 2, both readings: total observational collapse.
    /// L: one collapsed pair; F: three, with one observational class each.
    #[test]
    fn challenge2_collapse_is_total_in_both_readings() {
        let l = replay(&READING_L.genesis).unwrap();
        assert_eq!(collapsed_pairs(&l), vec![Pair::of(0, 1)]);
        let f = replay(&READING_F.genesis).unwrap();
        assert_eq!(collapsed_pairs(&f), vec![Pair::of(0, 1), Pair::of(0, 2), Pair::of(1, 2)]);
        for r in [&l, &f] {
            let profs = profiles(r);
            let classes: std::collections::BTreeSet<_> = profs.iter().collect();
            assert_eq!(classes.len(), 1);
        }
    }

    #[test]
    fn a_witness_exists_exactly_when_separable() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(witness(&base, Mark(0), Mark(1)).is_none());
        let r = step(&base, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[0])).unwrap();
        assert!(separable(&r, Mark(0), Mark(1)));
        assert_eq!(witness(&r, Mark(0), Mark(1)).unwrap().slots, vec![None]);
        assert!(collapsed_pairs(&r).is_empty());
    }

    #[test]
    fn fw_absence_collapsed_is_not_equal() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(!separable(&base, Mark(0), Mark(1)));
        assert_ne!(base.data[0], base.data[1], "the tokens differ in the metatheory");
    }

    #[test]
    fn satisfies_reads_every_requirement() {
        let base = replay(&READING_L.genesis).unwrap();
        assert!(satisfies(&base), "no requirements, vacuously");
        let r = step(&base, &Event::Impose(Pair::of(0, 1))).unwrap();
        assert!(!satisfies(&r));
    }
}
