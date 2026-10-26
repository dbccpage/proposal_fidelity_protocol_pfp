//! Primitive — **automorphism group** and **pair orbits**: the state's own
//! symmetry.
//!
//! Crate boundary: coda-iso.  Source: `iso.py::automorphisms`,
//! `pair_orbits`; sealed regression
//! `test_least_pair_selection_is_not_equivariant`.
//!
//! An automorphism is a bijection pair under which the renamed regime
//! *equals* the regime, tokens ignored.  Pair orbits partition the
//! collapsed pairs under that group.  The closure policy (`closure.rs`)
//! issues one challenge per orbit, and the reason is a regression the
//! sealed derivation hit: selecting the *least* collapsed pair depends on
//! the representative labelling, so isomorphic regimes expanded to
//! non-isomorphic child sets and the quotient transition was ill-defined.
//! Orbit selection is isomorphism-equivariant; least-pair selection is not.
//!
//! This is the estate's answer to the crosstab's row "automorphism group,
//! pair orbits — `=` `Aut(x)` and its orbits" (§4, L3), and the one place
//! where the reading of the estate as group theory is on the nose.

use std::collections::{BTreeMap, BTreeSet};

use crate::canonical::{refine, IsoBudgetError, PERM_BUDGET};
use crate::mark::Pair;
use crate::regime::Regime;
use crate::renaming::{permutations, serialize, Bijection};

/// All bijections mapping each colour class onto itself.
fn inplace_class_perms(colors: &[usize]) -> Vec<Vec<usize>> {
    let mut classes: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for (idx, &c) in colors.iter().enumerate() {
        classes.entry(c).or_default().push(idx);
    }
    let mut out: Vec<Vec<usize>> = vec![vec![0; colors.len()]];
    for members in classes.values() {
        let images = permutations(members.len());
        let mut next = Vec::with_capacity(out.len() * images.len());
        for base in &out {
            for image in &images {
                let mut pi = base.clone();
                for (member, &slot) in members.iter().zip(image.iter()) {
                    pi[*member] = members[slot];
                }
                next.push(pi);
            }
        }
        out = next;
    }
    out
}

fn perm_count(colors: &[usize]) -> u64 {
    let mut counts: BTreeMap<usize, u64> = BTreeMap::new();
    for &c in colors {
        *counts.entry(c).or_insert(0) += 1;
    }
    counts.values().map(|&k| (2..=k).product::<u64>()).product()
}

/// All automorphisms of the regime, tokens ignored.
pub fn automorphisms(r: &Regime) -> Result<Vec<Bijection>, IsoBudgetError> {
    let (dcol, fcol) = refine(r);
    let total = perm_count(&dcol) * perm_count(&fcol);
    if total > PERM_BUDGET {
        return Err(IsoBudgetError { candidates: total, budget: PERM_BUDGET });
    }
    let identity = serialize(r, &Bijection::identity(r.n_data(), r.n_forms()));
    let mut out = Vec::new();
    for pi in inplace_class_perms(&dcol) {
        for phi in inplace_class_perms(&fcol) {
            let b = Bijection { data: pi.clone(), forms: phi };
            if serialize(r, &b) == identity {
                out.push(b);
            }
        }
    }
    Ok(out)
}

/// Orbits of unordered data pairs under the automorphism group, each orbit
/// sorted, orbits ordered by least member.
pub fn pair_orbits(r: &Regime, pairs: &[Pair]) -> Result<Vec<Vec<Pair>>, IsoBudgetError> {
    let autos = automorphisms(r)?;
    let mut remaining: BTreeSet<Pair> = pairs.iter().copied().collect();
    let mut sorted: Vec<Pair> = pairs.to_vec();
    sorted.sort();
    let mut orbits = Vec::new();
    for p in sorted {
        if !remaining.contains(&p) {
            continue;
        }
        let orbit: BTreeSet<Pair> = autos
            .iter()
            .map(|b| Pair::of(b.data[p.i.0], b.data[p.j.0]))
            .filter(|q| remaining.contains(q))
            .collect();
        for q in &orbit {
            remaining.remove(q);
        }
        orbits.push(orbit.into_iter().collect());
    }
    Ok(orbits)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::admission::step;
    use crate::event::Event;
    use crate::reading::{READING_F, READING_L};
    use crate::renaming::rename;
    use crate::replay::replay;
    use crate::separability::collapsed_pairs;

    /// Reading F's base: three data, no structure — the full symmetric group,
    /// and every collapsed pair in one orbit.  Reading L: two data, one orbit.
    #[test]
    fn a_structureless_base_has_the_full_symmetric_group_and_one_orbit() {
        let f = replay(&READING_F.genesis).unwrap();
        assert_eq!(automorphisms(&f).unwrap().len(), 6);
        let orbits = pair_orbits(&f, &collapsed_pairs(&f)).unwrap();
        assert_eq!(orbits.len(), 1);
        assert_eq!(orbits[0].len(), 3);
        let l = replay(&READING_L.genesis).unwrap();
        assert_eq!(automorphisms(&l).unwrap().len(), 2);
        assert_eq!(pair_orbits(&l, &collapsed_pairs(&l)).unwrap(), vec![vec![Pair::of(0, 1)]]);
    }

    /// Admitting a unary instance on datum 0 breaks the symmetry: only the
    /// identity survives on the data side.
    #[test]
    fn structure_kills_symmetry() {
        let f = replay(&READING_F.genesis).unwrap();
        let r = step(&f, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[0])).unwrap();
        let autos = automorphisms(&r).unwrap();
        assert_eq!(autos.len(), 2, "data 1 and 2 remain exchangeable");
        assert!(autos.iter().all(|b| b.data[0] == 0));
    }

    /// Equivariance: renaming the regime maps orbits onto orbits.
    #[test]
    fn orbits_are_equivariant_under_renaming() {
        let f = replay(&READING_F.genesis).unwrap();
        let r = step(&f, &Event::AdmitForm(1)).unwrap();
        let r = step(&r, &crate::testkit::inst(0, &[0])).unwrap();
        let b = Bijection { data: vec![1, 2, 0], forms: vec![0] };
        let s = rename(&r, &b);
        let orbits_r = pair_orbits(&r, &collapsed_pairs(&r)).unwrap();
        let orbits_s = pair_orbits(&s, &collapsed_pairs(&s)).unwrap();
        let mapped: BTreeSet<BTreeSet<Pair>> = orbits_r
            .iter()
            .map(|o| o.iter().map(|p| Pair::of(b.data[p.i.0], b.data[p.j.0])).collect())
            .collect();
        let actual: BTreeSet<BTreeSet<Pair>> = orbits_s.iter().map(|o| o.iter().copied().collect()).collect();
        assert_eq!(mapped, actual);
    }
}
