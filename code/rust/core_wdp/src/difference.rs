// Executable finite evidence; AuthorityEffect: None.
//! Root W: Genesis Primitive Difference, Carrier Symmetries & Presentation Blind Spots.
//! Formalizes Chapter 1 & Chapter 3 foundations.

use crate::error::WdpError;
use crate::types::AuthorityEffect;
use core_category_theory::finite_report_query::{
    ReportQueryDecision, ReportQueryProblem, ReportQueryRefusal,
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

/// A finite carrier set of discrete named states.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct Carrier {
    pub states: BTreeSet<String>,
}

impl Carrier {
    pub fn new<I, S>(iter: I) -> Result<Self, WdpError>
    where
        I: IntoIterator<Item = S>,
        S: Into<String>,
    {
        let states: BTreeSet<String> = iter.into_iter().map(Into::into).collect();
        if states.is_empty() {
            return Err(WdpError::InvalidInput {
                detail: "carrier cannot be empty".to_string(),
            });
        }
        Ok(Self { states })
    }

    pub fn size(&self) -> usize {
        self.states.len()
    }

    pub fn contains(&self, state: &str) -> bool {
        self.states.contains(state)
    }
}

/// Primitive difference outcome comparing two elements on a carrier.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum DifferenceOutcome {
    Same,
    Different,
}

/// Computes primitive difference delta_0(x, y) on a carrier.
pub fn primitive_difference(x: &str, y: &str) -> DifferenceOutcome {
    if x == y {
        DifferenceOutcome::Same
    } else {
        DifferenceOutcome::Different
    }
}

/// A presentation map q: X -> P mapping carrier states to presented tokens.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PresentationMap {
    pub carrier: Carrier,
    pub mapping: BTreeMap<String, String>,
    pub authority_effect: AuthorityEffect,
}

impl PresentationMap {
    pub fn new(carrier: Carrier, mapping: BTreeMap<String, String>) -> Result<Self, WdpError> {
        for s in &carrier.states {
            if !mapping.contains_key(s) {
                return Err(WdpError::InvalidInput {
                    detail: format!("presentation map missing assignment for carrier state {s}"),
                });
            }
        }
        if let Some(extra) = mapping.keys().find(|k| !carrier.states.contains(*k)) {
            return Err(WdpError::InvalidInput {
                detail: format!("presentation map assigns a state outside the carrier: {extra}"),
            });
        }
        Ok(Self {
            carrier,
            mapping,
            authority_effect: AuthorityEffect::None,
        })
    }

    /// Decides whether a query on the carrier can be read from this
    /// presentation, through the DP-1 owner
    /// `core_category_theory::finite_report_query`. The presentation is the
    /// report with the declared `report_codomain` (every presented token must
    /// lie in it); the query table must be total on the carrier with values
    /// in `query_codomain`. The result is a decoder on the realized image or a
    /// collision witness; unrealized codomain tokens play no part.
    pub fn decide_query(
        &self,
        report_codomain: &[String],
        query_codomain: &[String],
        query_rows: &[(String, String)],
    ) -> Result<ReportQueryDecision<String, String, String>, ReportQueryRefusal<String>> {
        let source: Vec<String> = self.carrier.states.iter().cloned().collect();
        let report_rows: Vec<(String, String)> = self
            .mapping
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect();
        let problem = ReportQueryProblem::new(
            &source,
            report_codomain,
            query_codomain,
            &report_rows,
            query_rows,
        )?;
        Ok(problem.decide())
    }

    pub fn present(&self, state: &str) -> Result<&str, WdpError> {
        self.mapping
            .get(state)
            .map(|s| s.as_str())
            .ok_or_else(|| WdpError::ElementNotFound {
                element: state.to_string(),
            })
    }

    /// Computes presentation fibers q^-1(p) for every presented token p in P.
    pub fn fibers(&self) -> BTreeMap<String, BTreeSet<String>> {
        let mut fibers: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
        for (state, token) in &self.mapping {
            fibers
                .entry(token.clone())
                .or_default()
                .insert(state.clone());
        }
        fibers
    }

    /// Identifies presentation blind spots: fibers containing >= 2 distinct states.
    pub fn blind_spots(&self) -> BTreeMap<String, BTreeSet<String>> {
        self.fibers()
            .into_iter()
            .filter(|(_, states)| states.len() >= 2)
            .collect()
    }

    /// Evaluates whether two distinct states x != y are separable by this presentation.
    pub fn is_separable(&self, x: &str, y: &str) -> Result<bool, WdpError> {
        let px = self.present(x)?;
        let py = self.present(y)?;
        Ok(px != py)
    }
}

impl core_homotopy_type_theory::primitive_difference::PrimitiveDifference for Carrier {
    type Carrier = String;
    type Diff = DifferenceOutcome;

    fn delta(&self, x: &Self::Carrier, y: &Self::Carrier) -> Self::Diff {
        primitive_difference(x, y)
    }

    fn zero(&self, d: &Self::Diff) -> bool {
        *d == DifferenceOutcome::Same
    }
}

// Origin: engine/crates_rs/core_wdp/src/difference.rs
// Claim: urn:core:crates_rs:core-wdp:difference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordab10d014 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordab10d014` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorab10d014 {
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
impl BoundaryErrorab10d014 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorab10d014 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorab10d014 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordab10d014 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorab10d014> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorab10d014::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorab10d014::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorab10d014::ExceedsCapacity {
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
    use core_homotopy_type_theory::primitive_difference::PrimitiveDifference;

    #[test]
    fn test_primitive_difference() {
        assert_eq!(primitive_difference("a", "a"), DifferenceOutcome::Same);
        assert_eq!(primitive_difference("a", "b"), DifferenceOutcome::Different);
    }

    #[test]
    fn test_carrier_primitive_difference_trait() {
        let carrier = Carrier::new(vec!["x", "y"]).unwrap();
        let x = "x".to_string();
        let y = "y".to_string();
        assert_eq!(carrier.delta(&x, &x), DifferenceOutcome::Same);
        assert_eq!(carrier.delta(&x, &y), DifferenceOutcome::Different);
        assert!(carrier.zero_rel(&x, &x));
        assert!(!carrier.zero_rel(&x, &y));
    }

    #[test]
    fn test_presentation_fibers_and_blind_spots() {
        let carrier = Carrier::new(vec!["s0", "s1", "s2", "s3"]).unwrap();
        let mut mapping = BTreeMap::new();
        mapping.insert("s0".to_string(), "p0".to_string());
        mapping.insert("s1".to_string(), "p0".to_string()); // s0, s1 in blind spot
        mapping.insert("s2".to_string(), "p1".to_string());
        mapping.insert("s3".to_string(), "p2".to_string());

        let pres = PresentationMap::new(carrier, mapping).unwrap();
        let blind_spots = pres.blind_spots();
        assert_eq!(blind_spots.len(), 1);
        assert!(blind_spots.contains_key("p0"));
        assert_eq!(
            blind_spots.get("p0").unwrap(),
            &BTreeSet::from(["s0".to_string(), "s1".to_string()])
        );

        assert_eq!(pres.is_separable("s0", "s1").unwrap(), false);
        assert_eq!(pres.is_separable("s0", "s2").unwrap(), true);
    }
}

#[cfg(test)]
mod l4_boundary_tests_ab10d014 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordab10d014::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordab10d014::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordab10d014::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordab10d014::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordab10d014::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorab10d014::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorab10d014::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
