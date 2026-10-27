//! Declared tolerance analysis of an existing WDP total retention packet.
//! The full report alphabet is explicit and may include unrealized reports.
//! A greatest forward relation is not presented as an equivalence quotient.

use crate::error::WdpError;
use crate::retention::RetentionPacket;
use core_category_theory::finite_retention_choices::{
    FiniteRetentionData, ForwardRelationReceipt,
};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ForwardRetentionAnalysis {
    pub state_names: Vec<String>,
    pub report_names: Vec<String>,
    pub receipt: ForwardRelationReceipt,
    native: FiniteRetentionData,
}

fn invalid(detail: &str) -> WdpError {
    WdpError::InvalidInput {
        detail: detail.to_owned(),
    }
}

impl ForwardRetentionAnalysis {
    pub fn from_packet(
        packet: &RetentionPacket,
        report_alphabet: &BTreeSet<String>,
    ) -> Result<Self, WdpError> {
        if packet.memory_carrier.is_empty()
            || packet.report_map.keys().cloned().collect::<BTreeSet<_>>() != packet.memory_carrier
        {
            return Err(invalid("exact nonempty memory/report coverage required"));
        }
        let state_names: Vec<_> = packet.memory_carrier.iter().cloned().collect();
        let labels: Vec<_> = packet.inputs.iter().cloned().collect();
        let report_names: Vec<_> = report_alphabet.iter().cloned().collect();
        let states: BTreeMap<_, _> = state_names
            .iter()
            .enumerate()
            .map(|(i, x)| (x.clone(), i))
            .collect();
        let reports: BTreeMap<_, _> = report_names
            .iter()
            .enumerate()
            .map(|(i, x)| (x.clone(), i))
            .collect();
        let updates = Self::build_indexed_updates(packet, &state_names, &labels, &states)?;
        let report_values = Self::build_indexed_reports(packet, &state_names, &reports)?;
        let comparison = Self::build_indexed_comparison(packet, &report_names, &reports)?;
        let native = FiniteRetentionData::new(updates, report_values, comparison, labels.len())
            .map_err(|_| invalid("invalid total retention packet"))?;
        let receipt = native.greatest_forward_relation();
        Ok(Self {
            state_names,
            report_names,
            receipt,
            native,
        })
    }

    fn build_indexed_updates(
        packet: &RetentionPacket,
        state_names: &[String],
        labels: &[String],
        states: &BTreeMap<String, usize>,
    ) -> Result<Vec<Vec<usize>>, WdpError> {
        let mut updates = vec![vec![0; labels.len()]; state_names.len()];
        if packet.update_map.len() != state_names.len() * labels.len() {
            return Err(invalid("total update map with no extra entries required"));
        }
        for (x, state) in state_names.iter().enumerate() {
            for (i, label) in labels.iter().enumerate() {
                let target = packet
                    .update_map
                    .get(&(state.clone(), label.clone()))
                    .ok_or_else(|| invalid("missing declared update"))?;
                updates[x][i] = *states
                    .get(target)
                    .ok_or_else(|| invalid("update outside memory"))?;
            }
        }
        Ok(updates)
    }

    fn build_indexed_reports(
        packet: &RetentionPacket,
        state_names: &[String],
        reports: &BTreeMap<String, usize>,
    ) -> Result<Vec<usize>, WdpError> {
        state_names
            .iter()
            .map(|state| {
                reports
                    .get(&packet.report_map[state])
                    .copied()
                    .ok_or_else(|| invalid("readout outside declared report alphabet"))
            })
            .collect()
    }

    fn build_indexed_comparison(
        packet: &RetentionPacket,
        report_names: &[String],
        reports: &BTreeMap<String, usize>,
    ) -> Result<Vec<Vec<bool>>, WdpError> {
        if packet
            .comparison
            .iter()
            .any(|(a, b)| !reports.contains_key(a) || !reports.contains_key(b))
        {
            return Err(invalid("comparison outside declared report alphabet"));
        }
        Ok(report_names
            .iter()
            .map(|a| {
                report_names
                    .iter()
                    .map(|b| packet.comparison.contains(&(a.clone(), b.clone())))
                    .collect()
            })
            .collect())
    }
    pub fn native(&self) -> &FiniteRetentionData {
        &self.native
    }
    pub fn state_quotient_admissible(&self) -> bool {
        self.native.relation_is_equivalence(&self.receipt)
    }
    pub fn literal_report_quotient_admissible(&self) -> bool {
        self.native.raw_report_quotient_admissible(&self.receipt)
    }
}

// Origin: engine/crates_rs/core_wdp/src/tolerance_retention.rs
// Claim: urn:core:crates_rs:core-wdp:tolerance-retention:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc3731a1a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc3731a1a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc3731a1a {
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
impl BoundaryErrorc3731a1a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc3731a1a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc3731a1a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc3731a1a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc3731a1a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc3731a1a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc3731a1a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc3731a1a::ExceedsCapacity {
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
    fn actual_tolerance_packet_refuses_false_equivalence() {
        let names = ["a", "b", "c"].map(str::to_owned);
        let packet = RetentionPacket::new(
            names.clone().into_iter().collect(),
            ["keep".to_owned()].into_iter().collect(),
            names
                .iter()
                .map(|a| ((a.clone(), "keep".to_owned()), a.clone()))
                .collect(),
            names.iter().map(|a| (a.clone(), a.clone())).collect(),
            [
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
            .collect(),
        )
        .unwrap();
        let analysis =
            ForwardRetentionAnalysis::from_packet(&packet, &names.into_iter().collect()).unwrap();
        assert!(analysis.native().is_reflexive_symmetric_comparison());
        assert!(!analysis.state_quotient_admissible());
        assert!(!analysis.literal_report_quotient_admissible());
    }
}

#[cfg(test)]
mod l4_boundary_tests_c3731a1a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc3731a1a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc3731a1a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc3731a1a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc3731a1a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc3731a1a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc3731a1a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc3731a1a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
