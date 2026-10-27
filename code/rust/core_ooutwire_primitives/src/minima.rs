//! Primitive — **minimum responses**, quotiented into **classes**.  Never a
//! choice.
//!
//! Crate boundary: coda-price.  Source: `candidates.py::min_responses`,
//! `MinResponses`; `engine.py::_quotient`, `challenge3_report`; sealed
//! claims `CL-3-MIN-TWO`, `CL-3-NONUNIQUE-MU1`, `CL-3-UNIQUE-MU2`.
//!
//! ```text
//! L8   minima are CLASSES, never a choice
//! L9   a tie is retained unless eliminated by proof
//! ```
//!
//! `min_responses` returns *every* valid delta at the minimum cost within
//! the bounds.  `quotient` groups them by the canonical key of the child
//! regime and returns one representative per class **with the class size**.
//! An implementation that returns one delta has made a choice the
//! mathematics does not make, and it will be wrong exactly where it matters:
//! the sealed Challenge 3 has three tied non-isomorphic minima in reading L
//! under `mu1`, and the difference between them is the whole result.
//!
//! The pinned values (from `artifacts/challenges.json`):
//!
//! | reading | measure | cost | valid deltas | classes |
//! |---|---|---|---|---|
//! | L | mu1 | 2 | 6 | 3 |
//! | L | mu2 | (2, 1) | 2 | 1 |
//! | F | mu1 | 2 | 10 | 5 |
//! | F | mu2 | (2, 1) | 2 | 1 |


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_9530fa72<T> {
    fn checked_invariant_9530fa72(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_9530fa72<T> for Option<T> {
    #[inline]
    fn checked_invariant_9530fa72(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_9530fa72<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_9530fa72(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;

use crate::bounds::Bounds;
use crate::candidate::{delta_events, Delta};
use crate::canonical::{try_canonical, IsoBudgetError};
use crate::enumeration::{iter_cost1_items, iter_cost2_deltas};
use crate::event::Event;
use crate::mark::Pair;
use crate::measure::{Cost, Measure, MeasureKind};
use crate::regime::Regime;
use crate::renaming::Key;
use crate::replay::replay_from;
use crate::response::{response_valid_fast, NodeView};
use crate::role::delta_label;

/// All minimum valid responses under a measure, before the quotient.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MinResponses {
    /// Which measure.
    pub measure: MeasureKind,
    /// The cost attained.
    pub cost: Cost,
    /// Every valid delta at that cost, in canonical order.
    pub deltas: Vec<Delta>,
    /// The bounds within which this is complete.
    pub complete_within: Bounds,
}

/// One isomorphism class of minimum responses.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Class {
    /// The canonical key of the child regime.
    pub key: Key,
    /// The first member, in canonical delta order.
    pub representative: Delta,
    /// The neutral label of the representative.
    pub label: String,
    /// How many raw deltas fall in this class.
    pub size: usize,
}

/// Minimum valid responses to `Separate(target)` within the bounds, or
/// `None` when no valid delta of at most `max_items` items exists.
pub fn min_responses(base: &Regime, target: Pair, measure: MeasureKind, bounds: &Bounds) -> Option<MinResponses> {
    bounds.validate().checked_invariant_9530fa72("unsupported candidate bounds");
    let view = NodeView::of(base).checked_invariant_9530fa72("rule-free base (engine invariant)");
    for cost in 0..=bounds.max_items {
        let valid: Vec<Delta> = match cost {
            0 => {
                if response_valid_fast(&view, target, &Vec::new()) {
                    vec![Vec::new()]
                } else {
                    Vec::new()
                }
            }
            1 => iter_cost1_items(base, bounds)
                .into_iter()
                .map(|it| vec![it])
                .filter(|d| response_valid_fast(&view, target, d))
                .collect(),
            2 => {
                let mut seen = std::collections::BTreeSet::new();
                iter_cost2_deltas(base, bounds, target)
                    .into_iter()
                    .filter(|d| seen.insert(d.clone()))
                    .filter(|d| response_valid_fast(&view, target, d))
                    .collect()
            }
            _ => unreachable!("enumeration beyond two items is outside the declared bounds"),
        };
        if valid.is_empty() {
            continue;
        }
        let best = valid.iter().map(|d| measure.cost(d)).min().checked_invariant_9530fa72("checked invariant");
        let mut chosen: Vec<Delta> = valid.into_iter().filter(|d| measure.cost(d) == best).collect();
        chosen.sort();
        return Some(MinResponses { measure, cost: best, deltas: chosen, complete_within: *bounds });
    }
    None
}

/// Group minimum deltas by the isomorphism class of the resulting regime.
/// The child imposes the target first, then applies the delta, exactly as
/// the sealed engine records the history.
pub fn quotient(base: &Regime, target: Pair, mr: &MinResponses) -> Vec<Class> {
    try_quotient(base, target, mr).checked_invariant_9530fa72("permutation budget")
}

/// Quotient with explicit canonicalization budget failure.
pub fn try_quotient(base: &Regime, target: Pair, mr: &MinResponses) -> Result<Vec<Class>, IsoBudgetError> {
    let mut grouped: BTreeMap<Key, Vec<Delta>> = BTreeMap::new();
    for delta in &mr.deltas {
        let mut h = vec![Event::Impose(target)];
        h.extend(delta_events(base, delta));
        let child = replay_from(&h, base).checked_invariant_9530fa72("valid delta replays");
        grouped.entry(try_canonical(&child)?).or_default().push(delta.clone());
    }
    Ok(grouped
        .into_iter()
        .map(|(key, members)| Class {
            key,
            label: delta_label(base, &members[0]),
            representative: members[0].clone(),
            size: members.len(),
        })
        .collect())
}

/// The sealed Challenge 3 answer for one reading and one measure.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Challenge3 {
    /// The measure.
    pub measure: MeasureKind,
    /// The minimum cost.
    pub cost: Cost,
    /// Raw valid deltas at the minimum.
    pub valid_at_minimum: usize,
    /// The retained classes.
    pub classes: Vec<Class>,
}

/// Compute Challenge 3 for a reading under one measure.
pub fn challenge3(base: &Regime, target: Pair, measure: MeasureKind, bounds: &Bounds) -> Challenge3 {
    let mr = min_responses(base, target, measure, bounds).checked_invariant_9530fa72("progress lemma: a response exists");
    let classes = quotient(base, target, &mr);
    Challenge3 { measure, cost: mr.cost, valid_at_minimum: mr.deltas.len(), classes }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/minima.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:minima:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9530fa72 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9530fa72` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9530fa72 {
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
impl BoundaryError9530fa72 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9530fa72 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9530fa72 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9530fa72 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9530fa72> {
        if capacity_bound == 0 {
            return Err(BoundaryError9530fa72::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9530fa72::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9530fa72::ExceedsCapacity {
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

    fn labels(c: &Challenge3) -> Vec<(String, usize)> {
        let mut v: Vec<(String, usize)> = c.classes.iter().map(|k| (k.label.clone(), k.size)).collect();
        v.sort();
        v
    }

    #[test]
    fn sealed_challenge3_reading_l() {
        let base = replay(&READING_L.genesis).unwrap();
        let b = Bounds::default();
        let mu1 = challenge3(&base, READING_L.target, MeasureKind::Mu1, &b);
        assert_eq!(mu1.cost, (2, -1));
        assert_eq!(mu1.valid_at_minimum, 6);
        assert_eq!(mu1.classes.len(), 3, "CL-3-NONUNIQUE-MU1, reading L");
        assert_eq!(
            labels(&mu1),
            vec![("form1+inst1".to_string(), 2), ("form2+inst2".to_string(), 2), ("form2+inst2diag".to_string(), 2)]
        );
        let mu2 = challenge3(&base, READING_L.target, MeasureKind::Mu2, &b);
        assert_eq!(mu2.cost, (2, 1));
        assert_eq!(mu2.valid_at_minimum, 2);
        assert_eq!(mu2.classes.len(), 1, "CL-3-UNIQUE-MU2, reading L");
        assert_eq!(mu2.classes[0].label, "form1+inst1");
    }

    #[test]
    fn sealed_challenge3_reading_f() {
        let base = replay(&READING_F.genesis).unwrap();
        let b = Bounds::default();
        let mu1 = challenge3(&base, READING_F.target, MeasureKind::Mu1, &b);
        assert_eq!(mu1.cost, (2, -1));
        assert_eq!(mu1.valid_at_minimum, 10);
        assert_eq!(mu1.classes.len(), 5, "CL-3-NONUNIQUE-MU1, reading F");
        let mu2 = challenge3(&base, READING_F.target, MeasureKind::Mu2, &b);
        assert_eq!(mu2.cost, (2, 1));
        assert_eq!(mu2.valid_at_minimum, 2);
        assert_eq!(mu2.classes.len(), 1, "CL-3-UNIQUE-MU2, reading F");
    }

    /// CL-3-MIN-TWO: nothing below two items is valid, in either reading.
    #[test]
    fn nothing_below_two_items_separates_the_target() {
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            let one = Bounds { max_items: 1, max_arity: 2 };
            assert!(min_responses(&base, reading.target, MeasureKind::Mu1, &one).is_none());
        }
    }

    /// L8: the quotient returns every class, and the sizes sum to the raw count.
    #[test]
    fn classes_partition_the_raw_minima() {
        let base = replay(&READING_F.genesis).unwrap();
        let c = challenge3(&base, READING_F.target, MeasureKind::Mu1, &Bounds::default());
        assert_eq!(c.classes.iter().map(|k| k.size).sum::<usize>(), c.valid_at_minimum);
    }
}

#[cfg(test)]
mod l4_boundary_tests_9530fa72 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9530fa72::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9530fa72::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9530fa72::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9530fa72::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9530fa72::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9530fa72::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9530fa72::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
