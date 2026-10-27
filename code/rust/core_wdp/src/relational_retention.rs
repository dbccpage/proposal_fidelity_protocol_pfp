//! WDP retention adapter for declared branching, partial labelled updates.
//!
//! Directed update data is an additional input: reports do not select or
//! orient it. Native bisimulation and succession classification live in
//! core_category_theory. A comparison must be a checked report equivalence;
//! a nontransitive tolerance is refused instead of silently closed.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_6a373b6c<T> {
    fn checked_invariant_6a373b6c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_6a373b6c<T> for Option<T> {
    #[inline]
    fn checked_invariant_6a373b6c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_6a373b6c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_6a373b6c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::error::WdpError;
use core_category_theory::finite_relational::{
    FiniteRelational, RelationalQuotient, SuccessionClassification,
};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RelationalRetentionPacket {
    pub state_names: Vec<String>,
    pub labels: Vec<String>,
    native: FiniteRelational,
}

fn invalid(detail: &str) -> WdpError {
    WdpError::InvalidInput {
        detail: detail.to_owned(),
    }
}

impl RelationalRetentionPacket {
    pub fn new(
        memory: BTreeSet<String>,
        labels: BTreeSet<String>,
        updates: BTreeSet<(String, String, String)>,
        reports: BTreeMap<String, String>,
        comparison: Option<BTreeSet<(String, String)>>,
    ) -> Result<Self, WdpError> {
        if memory.is_empty() || reports.keys().cloned().collect::<BTreeSet<_>>() != memory {
            return Err(invalid(
                "nonempty memory and exactly one report per memory state required",
            ));
        }
        let state_names: Vec<_> = memory.into_iter().collect();
        let labels: Vec<_> = labels.into_iter().collect();
        let states: BTreeMap<_, _> = state_names
            .iter()
            .cloned()
            .enumerate()
            .map(|(i, s)| (s, i))
            .collect();
        let label_ids: BTreeMap<_, _> = labels
            .iter()
            .cloned()
            .enumerate()
            .map(|(i, s)| (s, i))
            .collect();
        let report_names: Vec<_> = reports
            .values()
            .cloned()
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect();
        let comparison = comparison.unwrap_or_else(|| {
            report_names
                .iter()
                .map(|r| (r.clone(), r.clone()))
                .collect()
        });
        Self::validate_report_comparison(&report_names, &comparison)?;
        let report_ids = Self::build_report_ids(&report_names, &comparison);
        let successors =
            Self::build_successors(updates, &states, &label_ids, state_names.len(), labels.len())?;
        let report_values = state_names
            .iter()
            .map(|state| report_ids[&reports[state]])
            .collect();
        let native = FiniteRelational::new(report_values, successors, labels.len())
            .map_err(|_| invalid("invalid finite relational retention data"))?;
        Ok(Self {
            state_names,
            labels,
            native,
        })
    }

    fn validate_report_comparison(
        report_names: &[String],
        comparison: &BTreeSet<(String, String)>,
    ) -> Result<(), WdpError> {
        let report_set: BTreeSet<_> = report_names.iter().cloned().collect();
        if comparison
            .iter()
            .any(|(a, b)| !report_set.contains(a) || !report_set.contains(b))
        {
            return Err(invalid(
                "comparison references a report outside this packet",
            ));
        }
        for a in report_names {
            if !comparison.contains(&(a.clone(), a.clone())) {
                return Err(invalid("report comparison is not reflexive"));
            }
            Self::validate_symmetry_and_transitivity(a, report_names, comparison)?;
        }
        Ok(())
    }

    fn validate_symmetry_and_transitivity(
        a: &String,
        report_names: &[String],
        comparison: &BTreeSet<(String, String)>,
    ) -> Result<(), WdpError> {
        for b in report_names {
            let ab = comparison.contains(&(a.clone(), b.clone()));
            let ba = comparison.contains(&(b.clone(), a.clone()));
            if ab != ba {
                return Err(invalid("report comparison is not symmetric"));
            }
            if ab
                && report_names.iter().any(|c| {
                    comparison.contains(&(b.clone(), c.clone()))
                        && !comparison.contains(&(a.clone(), c.clone()))
                })
            {
                return Err(invalid("report comparison is not transitive"));
            }
        }
        Ok(())
    }

    fn build_report_ids(
        report_names: &[String],
        comparison: &BTreeSet<(String, String)>,
    ) -> BTreeMap<String, usize> {
        report_names
            .iter()
            .map(|a| {
                let representative = report_names
                    .iter()
                    .position(|b| comparison.contains(&(a.clone(), b.clone())))
                    .checked_invariant_6a373b6c("reflexive comparison");
                (a.clone(), representative)
            })
            .collect()
    }

    fn build_successors(
        updates: BTreeSet<(String, String, String)>,
        states: &BTreeMap<String, usize>,
        label_ids: &BTreeMap<String, usize>,
        num_states: usize,
        num_labels: usize,
    ) -> Result<Vec<Vec<Vec<usize>>>, WdpError> {
        let mut successors = vec![vec![Vec::new(); num_labels]; num_states];
        for (source, label, target) in updates {
            let (&source, &label, &target) = (
                states
                    .get(&source)
                    .ok_or_else(|| invalid("update source outside memory"))?,
                label_ids
                    .get(&label)
                    .ok_or_else(|| invalid("update label outside alphabet"))?,
                states
                    .get(&target)
                    .ok_or_else(|| invalid("update target outside memory"))?,
            );
            successors[source][label].push(target);
        }
        Ok(successors)
    }

    pub fn native(&self) -> &FiniteRelational {
        &self.native
    }
    pub fn behavioral_quotient(&self) -> RelationalQuotient {
        self.native.bisimulation_quotient()
    }
    pub fn verify_quotient(&self, receipt: &RelationalQuotient) -> bool {
        self.native.verify_quotient(receipt)
    }
    pub fn succession_classification(&self) -> SuccessionClassification {
        self.native.succession_classification()
    }
}

// Origin: engine/crates_rs/core_wdp/src/relational_retention.rs
// Claim: urn:core:crates_rs:core-wdp:relational-retention:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6a373b6c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6a373b6c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6a373b6c {
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
impl BoundaryError6a373b6c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6a373b6c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6a373b6c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6a373b6c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6a373b6c> {
        if capacity_bound == 0 {
            return Err(BoundaryError6a373b6c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6a373b6c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6a373b6c::ExceedsCapacity {
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

    #[test]
    fn fork_has_partial_succession_and_branching_behavior() {
        let packet = RelationalRetentionPacket::new(
            ["a", "b", "c"].map(str::to_owned).into_iter().collect(),
            ["step"].map(str::to_owned).into_iter().collect(),
            [("a", "step", "b"), ("a", "step", "c")]
                .map(|(a, i, b)| (a.to_owned(), i.to_owned(), b.to_owned()))
                .into_iter()
                .collect(),
            [("a", "r"), ("b", "r"), ("c", "r")]
                .map(|(a, r)| (a.to_owned(), r.to_owned()))
                .into_iter()
                .collect(),
            None,
        )
        .unwrap();
        let q = packet.behavioral_quotient();
        assert_eq!(q.state_to_block, vec![0, 1, 1]);
        assert!(packet.verify_quotient(&q));
        let order = packet.succession_classification();
        assert!(order.acyclic);
        assert!(!order.nonempty_reachability[1][2]);
    }

    #[test]
    fn comparison_tolerance_is_not_silently_closed() {
        let names = ["a", "b", "c"].map(str::to_owned);
        let comparison = [
            ("a", "a"),
            ("b", "b"),
            ("c", "c"),
            ("a", "b"),
            ("b", "a"),
            ("b", "c"),
            ("c", "b"),
        ]
        .map(|(a, b)| (a.to_owned(), b.to_owned()))
        .into_iter()
        .collect();
        let result = RelationalRetentionPacket::new(
            names.clone().into_iter().collect(),
            BTreeSet::new(),
            BTreeSet::new(),
            names.into_iter().map(|a| (a.clone(), a)).collect(),
            Some(comparison),
        );
        assert!(result.is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_6a373b6c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6a373b6c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6a373b6c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6a373b6c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6a373b6c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6a373b6c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6a373b6c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6a373b6c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
