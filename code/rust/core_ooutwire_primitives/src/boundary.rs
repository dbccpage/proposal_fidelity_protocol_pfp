//! The twelfth sort — a **boundary with two sides**, the one admitted
//! primitive of the second blind derivation, carried under two readings.
//!
//! Crate boundary: its own.  Source: `research/boundary_seed/code/boundary/
//! model.py` (frozen at `5cfdb232…`, marker `ef77e02a…`); receipts
//! `challenge0.json` (the reflection census) and `challenge3.json` (the
//! three tied minima under U); `research/side_free` for the control.
//!
//! The inscription is `<|>`: one supplied opaque datum whose boundary and
//! two sides are the single admitted primitive.  A regime records, for each
//! admitted mark, the side it lies on.  **Reading U** leaves the sides
//! unnamed, so their exchange is a renaming the object language cannot see;
//! **reading O** names them `near` and `far`, so it is not.
//!
//! The pinned reflection census (`challenge0.json`, `reflection_census.rows`):
//!
//! | marks | placements | classes under U | classes under O | fixed by reflection up to mark renaming |
//! |---|---|---|---|---|
//! | 0 | 1 | 1 | 1 | 1 |
//! | 1 | 2 | 1 | 2 | 0 |
//! | 2 | 4 | 2 | 3 | 2 |
//! | 3 | 8 | 2 | 4 | 0 |
//! | 4 | 16 | 3 | 5 | 6 |
//!
//! **What the controlled measurement said (§13.8).**  At the requirement
//! that two retained marks be internally separable: U costs 1 with three
//! tied minima (`withdraw_reflection`, `withdraw_mark_permutations`,
//! `extra_mark`); O costs 0, uniquely; the side-free control costs 1,
//! uniquely, by `withdraw_mark_permutations`.  So the sort bought *nothing
//! in cost* against U and one declaration against O, and what pays for
//! separation with no boundary at all is the **admission order** — whether
//! an order is itself a container is OPEN.  This module reproduces the
//! census and the U/O separation shape; it does not reproduce the price
//! list, which needs that tree's own candidate space.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_6c102c92<T> {
    fn checked_invariant_6c102c92(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_6c102c92<T> for Option<T> {
    #[inline]
    fn checked_invariant_6c102c92(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_6c102c92<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_6c102c92(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeSet;

use crate::renaming::permutations;
use crate::token::Token;

/// The declared reading of the boundary.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Reading {
    /// Sides unnamed; the exchange is a permitted renaming.
    U,
    /// Sides named `near` and `far`; the exchange is not.
    O,
}

/// The side names under O.
pub const SIDE_NAMES: [&str; 2] = ["near", "far"];

/// Admitted state of the boundary world.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct BRegime {
    /// The reading.
    pub reading: Reading,
    /// For each admitted mark, in admission order, its presentation label.
    pub marks: Vec<Token>,
    /// For each admitted mark, the side it lies on: 0 or 1.
    pub placement: Vec<u8>,
}

/// An event of the boundary grammar.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum BEvent {
    /// External presentation.  Inert.
    Supply(Token),
    /// Token-keyed admission on a side (Challenge 1).  A repeated admission
    /// on the same side is a no-op; on the other side it would move the
    /// mark and is refused.
    AdmitMark {
        /// The label.
        token: Token,
        /// The side.
        side: u8,
    },
    /// Admission of one presented occurrence as a fresh mark (Challenge 2).
    AdmitOccurrence {
        /// The label.
        token: Token,
        /// The side.
        side: u8,
    },
}

/// The error type of the boundary kernel.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BError(pub String);

impl BRegime {
    /// Genesis under a reading.
    pub fn genesis(reading: Reading) -> BRegime {
        BRegime { reading, marks: Vec::new(), placement: Vec::new() }
    }

    /// How many marks.
    pub fn n_marks(&self) -> usize {
        self.marks.len()
    }
}

/// Apply one event.
pub fn step(r: &BRegime, e: &BEvent) -> Result<BRegime, BError> {
    match e {
        BEvent::Supply(_) => Ok(r.clone()),
        BEvent::AdmitOccurrence { token, side } => {
            if *side > 1 {
                return Err(BError(format!("side must be 0 or 1, got {side}")));
            }
            let mut out = r.clone();
            out.marks.push(token.clone());
            out.placement.push(*side);
            Ok(out)
        }
        BEvent::AdmitMark { token, side } => {
            if *side > 1 {
                return Err(BError(format!("side must be 0 or 1, got {side}")));
            }
            let count = r.marks.iter().filter(|t| *t == token).count();
            if count > 1 {
                return Err(BError(format!("label {token} names more than one admitted mark; refused")));
            }
            if let Some(idx) = r.marks.iter().position(|t| t == token) {
                if r.placement[idx] != *side {
                    return Err(BError(format!("mark {token} is admitted on side {}; moving it is refused", r.placement[idx])));
                }
                return Ok(r.clone());
            }
            let mut out = r.clone();
            out.marks.push(token.clone());
            out.placement.push(*side);
            Ok(out)
        }
    }
}

/// Replay a history, refusing an admission not supplied first.
pub fn replay(h: &[BEvent], base: &BRegime) -> Result<BRegime, BError> {
    let mut r = base.clone();
    let mut supplied: BTreeSet<Token> = BTreeSet::new();
    for e in h {
        match e {
            BEvent::Supply(t) => {
                supplied.insert(t.clone());
            }
            BEvent::AdmitOccurrence { token, .. } => {
                if !supplied.contains(token) {
                    return Err(BError(format!("occurrence {token} was not supplied before admission")));
                }
            }
            BEvent::AdmitMark { token, .. } => {
                if !supplied.contains(token) && !r.marks.contains(token) {
                    return Err(BError(format!("mark {token} was not supplied before admission")));
                }
            }
        }
        r = step(&r, e)?;
    }
    Ok(r)
}

/// Exchange the two sides.
pub fn reflect(r: &BRegime) -> BRegime {
    BRegime { reading: r.reading, marks: r.marks.clone(), placement: r.placement.iter().map(|s| 1 - s).collect() }
}

/// Apply a permutation of internal identities; tokens travel with marks.
pub fn rename_marks(r: &BRegime, pi: &[usize]) -> BRegime {
    let n = r.n_marks();
    let mut marks = vec![Token::new(""); n];
    let mut placement = vec![0u8; n];
    for i in 0..n {
        marks[pi[i]] = r.marks[i].clone();
        placement[pi[i]] = r.placement[i];
    }
    BRegime { reading: r.reading, marks, placement }
}

/// Tokens forgotten; reading and placement kept.
pub fn serialize(r: &BRegime) -> (Reading, Vec<u8>) {
    (r.reading, r.placement.clone())
}

/// Every regime a permitted renaming reaches, with the renaming:
/// `(reflected, permutation, image)`.  Unpruned.
pub fn permitted_images(r: &BRegime) -> Vec<(bool, Vec<usize>, BRegime)> {
    let mut bases = vec![(false, r.clone())];
    if r.reading == Reading::U {
        bases.push((true, reflect(r)));
    }
    let mut out = Vec::new();
    for (reflected, base) in &bases {
        for pi in permutations(r.n_marks()) {
            out.push((*reflected, pi.clone(), rename_marks(base, &pi)));
        }
    }
    out
}

/// The minimum serialisation over every permitted renaming.
pub fn canonical(r: &BRegime) -> (Reading, Vec<u8>) {
    permitted_images(r).into_iter().map(|(_, _, img)| serialize(&img)).min().checked_invariant_6c102c92("identity")
}

/// Every permitted renaming carrying `r` onto itself, tokens forgotten.
pub fn automorphisms(r: &BRegime) -> Vec<(bool, Vec<usize>)> {
    let target = serialize(r);
    permitted_images(r).into_iter().filter(|(_, _, img)| serialize(img) == target).map(|(f, pi, _)| (f, pi)).collect()
}

/// Whether no permitted automorphism carries mark `i` to mark `j`: the
/// boundary derivation's declared sense of internal separability.
pub fn marks_internally_separable(r: &BRegime, i: usize, j: usize) -> bool {
    !automorphisms(r).iter().any(|(_, pi)| pi[i] == j)
}

/// Whether reflection stabilises the placement after some mark renaming.
pub fn fixed_up_to_mark_renaming(r: &BRegime) -> bool {
    let target = serialize(r);
    let reflected = reflect(r);
    permutations(r.n_marks()).into_iter().any(|pi| serialize(&rename_marks(&reflected, &pi)) == target)
}

/// The metatheoretic side profile: contents, and under O the name.
pub fn side_profile(r: &BRegime, side: u8) -> (Option<&'static str>, BTreeSet<usize>) {
    let contents: BTreeSet<usize> = r.placement.iter().enumerate().filter(|(_, s)| **s == side).map(|(i, _)| i).collect();
    let name = if r.reading == Reading::O { Some(SIDE_NAMES[side as usize]) } else { None };
    (name, contents)
}

/// Whether the two sides have equal profiles.
pub fn sides_collapsed(r: &BRegime) -> bool {
    side_profile(r, 0) == side_profile(r, 1)
}

/// One row of the reflection census: hypothetical placements of `marks`
/// distinct marks; nothing here is admitted.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CensusRow {
    /// Mark count.
    pub marks: usize,
    /// `2^marks` placements.
    pub placements: usize,
    /// Distinct canonical keys under U.
    pub classes_under_u: usize,
    /// Distinct canonical keys under O.
    pub classes_under_o: usize,
    /// Placements fixed by reflection up to a mark renaming.
    pub fixed_by_reflection_up_to_mark_renaming: usize,
}

/// The census for `0..=max_marks`.
pub fn reflection_census(max_marks: usize) -> Vec<CensusRow> {
    (0..=max_marks)
        .map(|n| {
            let marks: Vec<Token> = (0..n).map(|k| Token::new(format!("m{k}"))).collect();
            let mut u_keys = BTreeSet::new();
            let mut o_keys = BTreeSet::new();
            let mut fixed = 0;
            for bits in 0..(1usize << n) {
                let placement: Vec<u8> = (0..n).map(|k| ((bits >> k) & 1) as u8).collect();
                let u = BRegime { reading: Reading::U, marks: marks.clone(), placement: placement.clone() };
                let o = BRegime { reading: Reading::O, marks: marks.clone(), placement };
                u_keys.insert(canonical(&u));
                o_keys.insert(canonical(&o));
                if fixed_up_to_mark_renaming(&u) {
                    fixed += 1;
                }
            }
            CensusRow {
                marks: n,
                placements: 1 << n,
                classes_under_u: u_keys.len(),
                classes_under_o: o_keys.len(),
                fixed_by_reflection_up_to_mark_renaming: fixed,
            }
        })
        .collect()
}

/// The side-free control's renaming set: permutations only.  There is no
/// placement to reflect, so there is nothing for a reflection to act on.
pub fn side_free_automorphisms(n_marks: usize) -> Vec<Vec<usize>> {
    permutations(n_marks)
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/boundary.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6c102c92 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6c102c92` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6c102c92 {
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
impl BoundaryError6c102c92 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6c102c92 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6c102c92 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6c102c92 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6c102c92> {
        if capacity_bound == 0 {
            return Err(BoundaryError6c102c92::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6c102c92::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6c102c92::ExceedsCapacity {
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

    /// Challenge 0, both readings, as the receipt records them.
    #[test]
    fn challenge0_genesis_facts() {
        let u = BRegime::genesis(Reading::U);
        let o = BRegime::genesis(Reading::O);
        assert!(sides_collapsed(&u));
        assert!(!sides_collapsed(&o), "O's names distinguish the profiles by declaration");
        assert_eq!(reflect(&u), u);
        assert_eq!(reflect(&o), o);
        assert!(automorphisms(&u).iter().any(|(refl, _)| *refl), "reflection is a permitted automorphism under U");
        assert!(!automorphisms(&o).iter().any(|(refl, _)| *refl), "and not under O");
        assert_eq!(step(&u, &BEvent::Supply(Token::new("<|>"))).unwrap(), u);
    }

    /// The pinned census rows.
    #[test]
    fn reflection_census_matches_the_receipt() {
        let rows = reflection_census(4);
        let expect = [(0, 1, 1, 1, 1), (1, 2, 1, 2, 0), (2, 4, 2, 3, 2), (3, 8, 2, 4, 0), (4, 16, 3, 5, 6)];
        for (row, e) in rows.iter().zip(expect.iter()) {
            assert_eq!(
                (row.marks, row.placements, row.classes_under_u, row.classes_under_o, row.fixed_by_reflection_up_to_mark_renaming),
                *e
            );
        }
    }

    /// Challenge 2 shape: two marks on opposite sides.  Under U a composite
    /// exchange carries one to the other (B2-MARKS-U); under O none does
    /// (B2-MARKS-O).
    #[test]
    fn two_marks_on_opposite_sides_collapse_under_u_and_separate_under_o() {
        let h = vec![
            BEvent::Supply(Token::new("a")),
            BEvent::AdmitOccurrence { token: Token::new("a"), side: 0 },
            BEvent::Supply(Token::new("a")),
            BEvent::AdmitOccurrence { token: Token::new("a"), side: 1 },
        ];
        let u = replay(&h, &BRegime::genesis(Reading::U)).unwrap();
        let o = replay(&h, &BRegime::genesis(Reading::O)).unwrap();
        assert!(!marks_internally_separable(&u, 0, 1));
        assert!(marks_internally_separable(&o, 0, 1));
        // The invariant fact "they lie on different sides" holds in both.
        assert_ne!(u.placement[0], u.placement[1]);
    }

    #[test]
    fn admissions_refuse_by_name() {
        let g = BRegime::genesis(Reading::U);
        assert!(replay(&[BEvent::AdmitMark { token: Token::new("x"), side: 0 }], &g).is_err(), "not supplied");
        let h = vec![BEvent::Supply(Token::new("x")), BEvent::AdmitMark { token: Token::new("x"), side: 0 }];
        let r = replay(&h, &g).unwrap();
        assert!(step(&r, &BEvent::AdmitMark { token: Token::new("x"), side: 1 }).is_err(), "moving is refused");
        assert_eq!(step(&r, &BEvent::AdmitMark { token: Token::new("x"), side: 0 }).unwrap(), r, "re-admission is a no-op");
    }

    /// The control: with no sides, two marks are exchangeable by a bare
    /// permutation, so separation must be bought by withdrawing the mark
    /// permutations — the control's unique minimum.
    #[test]
    fn without_sides_only_the_admission_order_can_pay() {
        let autos = side_free_automorphisms(2);
        assert!(autos.iter().any(|pi| pi[0] == 1), "a permutation carries mark 0 to mark 1");
        let withdrawn: Vec<&Vec<usize>> = autos.iter().filter(|pi| pi.iter().enumerate().all(|(i, &p)| i == p)).collect();
        assert_eq!(withdrawn.len(), 1, "withdrawing the permutations leaves the identity, and the index separates");
    }
}

#[cfg(test)]
mod l4_boundary_tests_6c102c92 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6c102c92::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6c102c92::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6c102c92::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6c102c92::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6c102c92::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6c102c92::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6c102c92::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
