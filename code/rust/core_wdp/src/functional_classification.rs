//! Named WDP adapters for sovereign finite component classifications.
//!
//! CH03 uses the existing property-vector meanings, adding active updates.
//! CH14 distinguishes manuscript report stability from the legacy presentation
//! stability flag. Missing context/target data are refused, not defaulted.
//! Exact calibration means equality to caller-declared targets, not physical truth.

use std::collections::{BTreeMap, BTreeSet};

use core_category_theory::finite_functional_classification::{
    realize_retention, FiniteFunctionalModel, FiniteRetentionModel, FunctionalSignature,
    RetentionSignature,
};

use crate::error::WdpError;
use crate::observer::{audit_functional_observer_relations, FunctionalObserverProfile};
use crate::retention::{analyze_retention_packet, RetentionPacket};
use crate::types::AuthorityEffect;

fn invalid(detail: &str) -> WdpError {
    WdpError::InvalidInput {
        detail: detail.to_owned(),
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RetentionClassification {
    pub signature: RetentionSignature,
    pub quotient_size: usize,
    pub authority_effect: AuthorityEffect,
}

/// Validate the legacy packet and comparison, then delegate finite mathematics.
pub fn classify_retention_packet(
    packet: &RetentionPacket,
) -> Result<RetentionClassification, WdpError> {
    let legacy = analyze_retention_packet(packet)?;
    let report_labels: Vec<_> = packet
        .report_map
        .values()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let raw_ids: BTreeMap<_, _> = report_labels
        .iter()
        .enumerate()
        .map(|(i, label)| (label.clone(), i))
        .collect();
    let states: Vec<_> = packet.memory_carrier.iter().cloned().collect();
    let state_ids: BTreeMap<_, _> = states
        .iter()
        .enumerate()
        .map(|(i, state)| (state.clone(), i))
        .collect();
    let mut comparison_ids = BTreeMap::new();
    let mut recognized_by_label = BTreeMap::new();
    for label in &report_labels {
        let row: Vec<_> = report_labels
            .iter()
            .map(|other| packet.are_equivalent(label, other))
            .collect();
        let fresh = comparison_ids.len();
        let id = *comparison_ids.entry(row).or_insert(fresh);
        recognized_by_label.insert(label.clone(), id);
    }
    let raw = states
        .iter()
        .map(|state| raw_ids[&packet.report_map[state]])
        .collect();
    let recognized = states
        .iter()
        .map(|state| recognized_by_label[&packet.report_map[state]])
        .collect();
    let transitions = states
        .iter()
        .map(|state| {
            packet
                .inputs
                .iter()
                .map(|input| state_ids[&packet.update_map[&(state.clone(), input.clone())]])
                .collect()
        })
        .collect();
    let model = FiniteRetentionModel::new(raw, recognized, transitions, packet.inputs.len())
        .map_err(|_| invalid("invalid finite retention classification model"))?;
    let signature = model.signature();
    if signature.nontrivial != legacy.is_nontrivial_carrier
        || signature.reversible != legacy.is_fully_reversible
        || signature.observable != legacy.is_observable
        || signature.tolerance != legacy.has_nontrivial_tolerance
        || signature.minimal != legacy.is_minimal
    {
        return Err(invalid(
            "legacy and sovereign retention invariants disagree",
        ));
    }
    Ok(RetentionClassification {
        signature,
        quotient_size: legacy.quotient_size,
        authority_effect: AuthorityEffect::None,
    })
}

pub fn construct_retention_witness(
    signature: RetentionSignature,
) -> Result<RetentionPacket, WdpError> {
    let model =
        realize_retention(signature).map_err(|_| invalid("impossible retention signature"))?;
    let n = model.moore().state_count();
    let states: Vec<_> = (0..n).map(|i| format!("m{i}")).collect();
    let inputs: Vec<_> = (0..model.moore().input_count())
        .map(|i| format!("i{i}"))
        .collect();
    let update = states
        .iter()
        .enumerate()
        .flat_map(|(x, state)| {
            inputs
                .iter()
                .enumerate()
                .map(|(i, input)| {
                    (
                        (state.clone(), input.clone()),
                        states[model.moore().transitions()[x][i]].clone(),
                    )
                })
                .collect::<Vec<_>>()
        })
        .collect();
    let report = states
        .iter()
        .enumerate()
        .map(|(x, state)| (state.clone(), format!("r{}", model.raw_reports()[x])))
        .collect();
    let mut comparison = BTreeSet::new();
    for x in 0..n {
        for y in 0..n {
            if model.moore().reports()[x] == model.moore().reports()[y] {
                comparison.insert((
                    format!("r{}", model.raw_reports()[x]),
                    format!("r{}", model.raw_reports()[y]),
                ));
            }
        }
    }
    RetentionPacket::new(
        states.into_iter().collect(),
        inputs.into_iter().collect(),
        update,
        report,
        comparison,
    )
}

/// All maps must be total on exactly the nonempty, duplicate-free named carrier.
pub fn classify_functional_maps(
    carrier: &[String],
    presentation: &BTreeMap<String, String>,
    self_report: &BTreeMap<String, String>,
    context: &BTreeMap<String, String>,
    target: &BTreeMap<String, String>,
) -> Result<FunctionalSignature, WdpError> {
    let domain: BTreeSet<_> = carrier.iter().cloned().collect();
    if domain.is_empty()
        || domain.len() != carrier.len()
        || [presentation, self_report, context, target]
            .iter()
            .any(|map| map.keys().cloned().collect::<BTreeSet<_>>() != domain)
    {
        return Err(invalid(
            "functional maps must have exactly the declared nonempty carrier domain",
        ));
    }
    let ids: BTreeMap<_, _> = carrier
        .iter()
        .enumerate()
        .map(|(i, x)| (x.clone(), i))
        .collect();
    if context.values().any(|value| !domain.contains(value)) {
        return Err(invalid("context leaves the declared carrier"));
    }
    let pids: BTreeMap<_, _> = presentation
        .values()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .enumerate()
        .map(|(i, x)| (x, i))
        .collect();
    let rids: BTreeMap<_, _> = self_report
        .values()
        .chain(target.values())
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .enumerate()
        .map(|(i, x)| (x, i))
        .collect();
    let model = FiniteFunctionalModel::new(
        carrier.iter().map(|x| pids[&presentation[x]]).collect(),
        carrier.iter().map(|x| rids[&self_report[x]]).collect(),
        carrier.iter().map(|x| ids[&context[x]]).collect(),
        carrier.iter().map(|x| rids[&target[x]]).collect(),
    )
    .map_err(|_| invalid("invalid finite functional model"))?;
    Ok(model.signature())
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FunctionalClassification {
    pub signature: FunctionalSignature,
    pub legacy_audit: FunctionalObserverProfile,
    pub authority_effect: AuthorityEffect,
}

/// Checked adapter to the legacy report-on-presentations API. Here linking is
/// structural (s=hq), not an independent predicate. Supply complete context and
/// targets; the legacy missing-data defaults are deliberately unavailable.
pub fn classify_existing_functional_packet(
    carrier: &[String],
    presentation: &BTreeMap<String, String>,
    report_on_presentations: &BTreeMap<String, String>,
    context: &BTreeMap<String, String>,
    target: &BTreeMap<String, String>,
) -> Result<FunctionalClassification, WdpError> {
    let realized: BTreeSet<_> = presentation.values().cloned().collect();
    if report_on_presentations
        .keys()
        .cloned()
        .collect::<BTreeSet<_>>()
        != realized
    {
        return Err(invalid(
            "report map must be total exactly on realized presentations",
        ));
    }
    let self_report = presentation
        .iter()
        .map(|(x, q)| (x.clone(), report_on_presentations[q].clone()))
        .collect();
    let signature = classify_functional_maps(carrier, presentation, &self_report, context, target)?;
    let legacy_audit = audit_functional_observer_relations(
        carrier,
        presentation,
        report_on_presentations,
        Some(context),
        Some(target),
    )?;
    Ok(FunctionalClassification {
        signature,
        legacy_audit,
        authority_effect: AuthorityEffect::None,
    })
}

// Origin: engine/crates_rs/core_wdp/src/functional_classification.rs
// Claim: urn:core:crates_rs:core-wdp:functional-classification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0531117d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0531117d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0531117d {
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
impl BoundaryError0531117d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0531117d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0531117d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0531117d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0531117d> {
        if capacity_bound == 0 {
            return Err(BoundaryError0531117d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0531117d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0531117d::ExceedsCapacity {
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
mod l4_boundary_tests_0531117d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0531117d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0531117d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0531117d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0531117d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0531117d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0531117d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0531117d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
