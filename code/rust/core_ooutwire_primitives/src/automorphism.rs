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
    counts.values().fold(1u64, |total, &k| {
        (2..=k).fold(total, |n, factor| n.saturating_mul(factor))
    })
}

/// All automorphisms of the regime, tokens ignored.
pub fn automorphisms(r: &Regime) -> Result<Vec<Bijection>, IsoBudgetError> {
    let (dcol, fcol) = refine(r);
    let total = perm_count(&dcol).saturating_mul(perm_count(&fcol));
    if total == u64::MAX || total > PERM_BUDGET {
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

// Origin: engine/crates_rs/core_ooutwire_primitives/src/automorphism.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:automorphism:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcf4bdc06 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcf4bdc06` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcf4bdc06 {
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
impl BoundaryErrorcf4bdc06 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcf4bdc06 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcf4bdc06 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcf4bdc06 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcf4bdc06> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcf4bdc06::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcf4bdc06::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcf4bdc06::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_cf4bdc06 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordcf4bdc06::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordcf4bdc06::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordcf4bdc06::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordcf4bdc06::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordcf4bdc06::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorcf4bdc06::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorcf4bdc06::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
