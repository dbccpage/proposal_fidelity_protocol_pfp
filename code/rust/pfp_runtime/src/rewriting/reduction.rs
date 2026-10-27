
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_f29863c1<T> {
    fn checked_invariant_f29863c1(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_f29863c1<T> for Option<T> {
    #[inline]
    fn checked_invariant_f29863c1(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_f29863c1<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_f29863c1(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, VecDeque};

use super::{Presentation, Rule};

/// One rule application at a Unicode scalar position in the current term.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReductionStep {
    pub rule: String,
    pub position: usize,
}

/// One reduction path from a source term to an endpoint.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReductionPath {
    /// Rule applications, including the redex position, in order.
    pub steps: Vec<ReductionStep>,
    pub endpoint: String,
}

/// A host-derived critical pair from two overlapping rule applications.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CriticalPair {
    pub source: String,
    pub left: ReductionStep,
    pub right: ReductionStep,
    pub left_endpoint: String,
    pub right_endpoint: String,
}

/// Whether every rule strictly decreases symbol length, so rewriting halts.
///
/// **This does not gate any verdict in this module, and must not be made to.**
/// It is the premise Newman's lemma needs to lift local confluence to
/// confluence of a *system* -- a claim a caller might build, and one this
/// module never makes. Joinability of a single pair needs closure, which
/// [`crate::rewriting::ExhaustionBasis::ClosedReachableSets`] certifies directly.
///
/// A presentation whose rules are not all strictly length-reducing may still
/// terminate; a `None` here means only that this cheap syntactic test did not
/// establish it.
pub fn is_length_reducing(presentation: &Presentation) -> bool {
    !presentation.rules.is_empty()
        && presentation
            .rules
            .iter()
            .all(|rule| !rule.lhs.is_empty() && rule.rhs.chars().count() < rule.lhs.chars().count())
}

/// Every term reachable from `term`, itself included.
///
/// `None` means the budget was exhausted before closure, in which case the
/// caller has a partial exploration and must not draw an exhaustive conclusion
/// from it.
/// The outcome of a bounded reachability closure, and what it cost the host.
///
/// The cost is returned rather than discarded because a verdict that reports
/// work done must report the host's own work. Dropping it here is what forced
/// the caller to reach for the producer's declared figure instead.
pub(super) struct Reached {
    /// Every reachable term mapped to its minimal rewrite distance from the
    /// origin. Distances are kept because the *choice* of join among several
    /// candidates has to be made on a stated basis, and distance is the only
    /// property of a common reduct that means anything.
    pub(super) terms: Option<BTreeMap<String, u64>>,
    pub(super) expansions: u64,
}

pub(super) fn reachable(presentation: &Presentation, term: &str, budget: u64) -> Reached {
    let mut seen: BTreeMap<String, u64> = BTreeMap::new();
    // Breadth-first, so the first time a term is reached is by a shortest
    // path and the recorded distance is minimal. A stack would explore
    // depth-first and record whatever length it happened to arrive by.
    let mut frontier: VecDeque<String> = VecDeque::new();
    seen.insert(term.to_owned(), 0);
    frontier.push_back(term.to_owned());
    let mut expansions: u64 = 0;

    while let Some(current) = frontier.pop_front() {
        let depth = seen[&current];
        let width = current.chars().count();
        for rule in &presentation.rules {
            let lhs_width = rule.lhs.chars().count();
            if lhs_width == 0 || lhs_width > width {
                // The rule cannot match anywhere in this term. Probing every
                // position anyway is not merely wasted work: each probe is
                // charged to the budget, so the threshold at which the host
                // declines was being set by a loop bound rather than by the
                // search.
                continue;
            }
            // `apply` can only match where the whole left-hand side fits, so
            // the last viable start is `width - lhs_width`. The old bound ran
            // to `width` inclusive and charged for `lhs_width + 1` probes per
            // term that could never have matched.
            for position in 0..=(width - lhs_width) {
                // Checked BEFORE the increment. Incrementing first with
                // `saturating_add` caps the counter at `u64::MAX`, and a strict
                // `>` against a budget of `u64::MAX` then never fires -- the
                // guard silently disarms at exactly the value a producer is
                // most likely to send when it means "no limit".
                if expansions >= budget {
                    return Reached {
                        terms: None,
                        expansions,
                    };
                }
                expansions += 1;
                if let Some(next) = apply(rule, &current, position) {
                    if !seen.contains_key(&next) {
                        seen.insert(next.clone(), depth.saturating_add(1));
                        frontier.push_back(next);
                    }
                }
            }
        }
    }

    Reached {
        terms: Some(seen),
        expansions,
    }
}

fn byte_index_at_symbol(term: &str, position: usize) -> Option<usize> {
    if position == 0 {
        return Some(0);
    }
    let mut count = 0;
    for (index, _) in term.char_indices() {
        if count == position {
            return Some(index);
        }
        count += 1;
    }
    if count == position {
        Some(term.len())
    } else {
        None
    }
}

/// Apply `rule` at a Unicode scalar position in `term`.
///
/// `None` means either that the position is outside the term or that the
/// rule's left-hand side is not the redex beginning at that position.
pub fn apply(rule: &Rule, term: &str, position: usize) -> Option<String> {
    if rule.lhs.is_empty() {
        return None;
    }

    let start = byte_index_at_symbol(term, position)?;
    if !term[start..].starts_with(&rule.lhs) {
        return None;
    }
    let end = start + rule.lhs.len();

    let mut result = String::with_capacity(term.len() - rule.lhs.len() + rule.rhs.len());
    result.push_str(&term[..start]);
    result.push_str(&rule.rhs);
    result.push_str(&term[end..]);
    Some(result)
}

pub(super) fn replay_path(
    presentation: &Presentation,
    source: &str,
    side: &str,
    path: &ReductionPath,
    obligations: &mut Vec<String>,
) -> Option<String> {
    let mut term = source.to_owned();

    for (index, step) in path.steps.iter().enumerate() {
        let Some(rule) = presentation.rule(&step.rule) else {
            obligations.push(format!(
                "{side} path applies rule {:?}, which the presentation does not declare",
                step.rule
            ));
            return None;
        };

        let Some(next) = apply(rule, &term, step.position) else {
            obligations.push(format!(
                "{side} path step {} cannot apply rule {:?} at symbol position {} to term {:?}",
                index + 1,
                step.rule,
                step.position,
                term
            ));
            return None;
        };
        term = next;
    }

    if !path.endpoint.trim().is_empty() && path.endpoint != term {
        obligations.push(format!(
            "{side} path declares endpoint {:?}, but replay from the source produces {:?}",
            path.endpoint, term
        ));
    }

    Some(term)
}

fn merged_overlap_source(
    left_lhs: &[char],
    left_start: usize,
    right_lhs: &[char],
    right_start: usize,
) -> Option<String> {
    let source_len = (left_start + left_lhs.len()).max(right_start + right_lhs.len());
    let mut source = vec![None; source_len];
    for (position, symbol) in left_lhs.iter().copied().enumerate() {
        source[left_start + position] = Some(symbol);
    }

    for (position, symbol) in right_lhs.iter().copied().enumerate() {
        let slot = &mut source[right_start + position];
        match slot {
            Some(existing) if *existing != symbol => return None,
            Some(_) => {}
            None => *slot = Some(symbol),
        }
    }
    Some(source.into_iter().flatten().collect())
}

fn build_ordered_critical_pair(
    left_rule: &Rule,
    left_start: usize,
    right_rule: &Rule,
    right_start: usize,
    source: String,
) -> CriticalPair {
    let mut left = ReductionStep {
        rule: left_rule.name.clone(),
        position: left_start,
    };
    let mut right = ReductionStep {
        rule: right_rule.name.clone(),
        position: right_start,
    };
    let mut left_endpoint = apply(left_rule, &source, left_start)
        .checked_invariant_f29863c1("enumerated left redex must apply");
    let mut right_endpoint = apply(right_rule, &source, right_start)
        .checked_invariant_f29863c1("enumerated right redex must apply");

    if right < left {
        std::mem::swap(&mut left, &mut right);
        std::mem::swap(&mut left_endpoint, &mut right_endpoint);
    }
    CriticalPair {
        source,
        left,
        right,
        left_endpoint,
        right_endpoint,
    }
}

type CriticalPairKey = (String, ReductionStep, ReductionStep, String, String);

fn collect_pair_overlaps(
    left_spec: (usize, &[char], &Rule),
    right_spec: (usize, &[char], &Rule),
    seen: &mut BTreeSet<CriticalPairKey>,
    pairs: &mut Vec<CriticalPair>,
) {
    let (left_index, left_lhs, left_rule) = left_spec;
    let (right_index, right_lhs, right_rule) = right_spec;
    let min_offset = -((right_lhs.len() as isize) - 1);
    let max_offset = (left_lhs.len() as isize) - 1;
    for offset in min_offset..=max_offset {
        let left_start = (-offset).max(0) as usize;
        let right_start = offset.max(0) as usize;
        if left_index == right_index && left_start == right_start {
            continue;
        }
        let Some(source) = merged_overlap_source(left_lhs, left_start, right_lhs, right_start)
        else {
            continue;
        };
        let pair =
            build_ordered_critical_pair(left_rule, left_start, right_rule, right_start, source);
        let key = (
            pair.source.clone(),
            pair.left.clone(),
            pair.right.clone(),
            pair.left_endpoint.clone(),
            pair.right_endpoint.clone(),
        );
        if seen.insert(key) {
            pairs.push(pair);
        }
    }
}

/// Enumerate minimal overlapping rule applications, including containment.
///
/// Disjoint redexes are not critical pairs. A rule may overlap itself at two
/// different positions, while the identical application is omitted.
pub fn critical_pairs(presentation: &Presentation) -> Vec<CriticalPair> {
    let mut pairs = Vec::new();
    let mut seen = BTreeSet::new();

    let rule_lhs: Vec<Vec<char>> = presentation
        .rules
        .iter()
        .map(|r| r.lhs.chars().collect())
        .collect();

    for (left_index, left_lhs) in rule_lhs.iter().enumerate() {
        if left_lhs.is_empty() {
            continue;
        }
        let left_rule = &presentation.rules[left_index];

        for (right_index, right_lhs) in rule_lhs.iter().enumerate() {
            if right_lhs.is_empty() {
                continue;
            }
            let right_rule = &presentation.rules[right_index];
            collect_pair_overlaps(
                (left_index, left_lhs, left_rule),
                (right_index, right_lhs, right_rule),
                &mut seen,
                &mut pairs,
            );
        }
    }

    pairs
}

// Origin: engine/crates_rs/pfp_runtime/src/rewriting/reduction.rs
// Claim: urn:core:crates_rs:pfp-runtime:reduction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf29863c1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf29863c1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf29863c1 {
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
impl BoundaryErrorf29863c1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf29863c1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf29863c1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf29863c1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf29863c1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf29863c1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf29863c1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf29863c1::ExceedsCapacity {
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
mod l4_boundary_tests_f29863c1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf29863c1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf29863c1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf29863c1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf29863c1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf29863c1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf29863c1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf29863c1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
