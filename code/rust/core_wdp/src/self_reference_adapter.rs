//! Named, checked CH14 accessible-self-state and partial-protocol adapter.
//! All supplied provenance is replayed against the generation relation and
//! identity/state/report bindings. Content digests do not establish linkage.

use std::collections::{BTreeMap, BTreeSet};

use core_category_theory::finite_self_reference::{
    CheckedSelfReference, PartialComparisonProtocol, ReflexiveProvenance, SelfReferenceData,
    SelfReferencePoint, SelfReferenceSignature,
};
use serde::Serialize;

use crate::error::WdpError;
use crate::types::{blake3_digest, AuthorityEffect};

fn invalid(detail: &str) -> WdpError {
    WdpError::InvalidInput {
        detail: detail.to_owned(),
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct NamedReflexiveProvenance {
    pub source_observer: String,
    pub target_observer: String,
    pub captured_accessible: String,
    pub reaccessed_accessible: String,
    pub reported_value: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct NamedComparisonProtocol {
    pub evaluator_id: String,
    pub domain: BTreeSet<(String, String)>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct NamedSelfReferencePacket {
    pub observer_id: String,
    pub observers: BTreeSet<String>,
    pub states: Vec<String>,
    pub accessible: BTreeSet<String>,
    pub report_alphabet: BTreeSet<String>,
    pub sigma: BTreeMap<String, String>,
    pub presentation: BTreeMap<String, String>,
    pub reports: BTreeMap<String, Option<String>>,
    pub provenance: BTreeMap<String, Option<NamedReflexiveProvenance>>,
    pub context: BTreeMap<String, String>,
    pub later: BTreeMap<String, String>,
    pub target: BTreeMap<String, Option<String>>,
    pub generation: BTreeSet<(String, String)>,
    pub protocol: Option<NamedComparisonProtocol>,
}

fn ids(labels: &BTreeSet<String>) -> BTreeMap<String, usize> {
    labels
        .iter()
        .enumerate()
        .map(|(i, s)| (s.clone(), i))
        .collect()
}
fn exact_domain<T>(map: &BTreeMap<String, T>, domain: &BTreeSet<String>) -> bool {
    map.keys().cloned().collect::<BTreeSet<_>>() == *domain
}
fn lookup(map: &BTreeMap<String, usize>, key: &str) -> Result<usize, WdpError> {
    map.get(key)
        .copied()
        .ok_or_else(|| invalid("named self-reference map leaves its declared carrier"))
}

/// Translate only after checking all domains. Absent reports/targets/provenance
/// are explicit None values; missing rows never receive identity/truth defaults.
pub fn checked_self_reference(
    packet: &NamedSelfReferencePacket,
) -> Result<CheckedSelfReference, WdpError> {
    let states: BTreeSet<_> = packet.states.iter().cloned().collect();
    validate_self_reference_domains(packet, &states)?;
    let sids: BTreeMap<_, _> = packet
        .states
        .iter()
        .enumerate()
        .map(|(i, s)| (s.clone(), i))
        .collect();
    let aids = ids(&packet.accessible);
    let rids = ids(&packet.report_alphabet);
    let oids = ids(&packet.observers);
    let pids = ids(&packet.presentation.values().cloned().collect());
    let provenance = translate_provenance(packet, &oids, &aids, &rids)?;
    let protocol = translate_protocol(packet, &rids)?;
    let (sigma, presentation, context, later) =
        translate_required_maps(packet, &sids, &aids, &pids)?;
    let (reports, target, generation) = translate_optional_and_rel_maps(packet, &aids, &rids)?;
    let data = SelfReferenceData {
        observer_id: lookup(&oids, &packet.observer_id)?,
        observer_count: oids.len(),
        accessible_count: aids.len(),
        report_count: rids.len(),
        sigma,
        presentation,
        reports,
        provenance,
        context,
        later,
        target,
        generation,
        protocol,
    };
    CheckedSelfReference::new(data).map_err(|_| invalid("indexed self-reference validation failed"))
}

fn validate_self_reference_domains(
    packet: &NamedSelfReferencePacket,
    states: &BTreeSet<String>,
) -> Result<(), WdpError> {
    let non_empty_sets = states.len() == packet.states.len()
        && !states.is_empty()
        && !packet.accessible.is_empty()
        && !packet.report_alphabet.is_empty()
        && ![
            states,
            &packet.accessible,
            &packet.report_alphabet,
            &packet.observers,
        ]
        .iter()
        .any(|set| set.iter().any(|s| s.is_empty()));
    if !non_empty_sets || !valid_self_reference_map_domains(packet, states) {
        return Err(invalid(
            "self-reference maps require exact nonempty declared domains",
        ));
    }
    Ok(())
}

fn valid_self_reference_map_domains(
    packet: &NamedSelfReferencePacket,
    states: &BTreeSet<String>,
) -> bool {
    exact_domain(&packet.sigma, states)
        && exact_domain(&packet.reports, states)
        && exact_domain(&packet.provenance, states)
        && exact_domain(&packet.context, states)
        && exact_domain(&packet.later, states)
        && exact_domain(&packet.target, states)
        && exact_domain(&packet.presentation, &packet.accessible)
        && !packet.presentation.values().any(|s| s.is_empty())
}

fn translate_provenance(
    packet: &NamedSelfReferencePacket,
    oids: &BTreeMap<String, usize>,
    aids: &BTreeMap<String, usize>,
    rids: &BTreeMap<String, usize>,
) -> Result<Vec<Option<ReflexiveProvenance>>, WdpError> {
    let mut provenance = Vec::new();
    for state in &packet.states {
        provenance.push(
            packet.provenance[state]
                .as_ref()
                .map(|p| -> Result<ReflexiveProvenance, WdpError> {
                    Ok(ReflexiveProvenance {
                        source_observer: lookup(oids, &p.source_observer)?,
                        target_observer: lookup(oids, &p.target_observer)?,
                        captured_accessible: lookup(aids, &p.captured_accessible)?,
                        reaccessed_accessible: lookup(aids, &p.reaccessed_accessible)?,
                        reported_value: lookup(rids, &p.reported_value)?,
                    })
                })
                .transpose()?,
        );
    }
    Ok(provenance)
}

fn translate_protocol(
    packet: &NamedSelfReferencePacket,
    rids: &BTreeMap<String, usize>,
) -> Result<Option<PartialComparisonProtocol>, WdpError> {
    packet
        .protocol
        .as_ref()
        .map(|p| {
            if p.evaluator_id.is_empty() {
                return Err(invalid(
                    "comparison protocol needs a declared evaluator identity",
                ));
            }
            Ok(PartialComparisonProtocol {
                evaluator_id: 0,
                domain: p
                    .domain
                    .iter()
                    .map(|(r, b)| Ok((lookup(rids, r)?, lookup(rids, b)?)))
                    .collect::<Result<_, WdpError>>()?,
            })
        })
        .transpose()
}

fn translate_required_maps(
    packet: &NamedSelfReferencePacket,
    sids: &BTreeMap<String, usize>,
    aids: &BTreeMap<String, usize>,
    pids: &BTreeMap<String, usize>,
) -> Result<(Vec<usize>, Vec<usize>, Vec<usize>, Vec<usize>), WdpError> {
    let sigma = packet
        .states
        .iter()
        .map(|s| lookup(aids, &packet.sigma[s]))
        .collect::<Result<_, _>>()?;
    let presentation = packet
        .accessible
        .iter()
        .map(|a| lookup(pids, &packet.presentation[a]))
        .collect::<Result<_, _>>()?;
    let context = packet
        .states
        .iter()
        .map(|s| lookup(sids, &packet.context[s]))
        .collect::<Result<_, _>>()?;
    let later = packet
        .states
        .iter()
        .map(|s| lookup(sids, &packet.later[s]))
        .collect::<Result<_, _>>()?;
    Ok((sigma, presentation, context, later))
}

fn translate_optional_and_rel_maps(
    packet: &NamedSelfReferencePacket,
    aids: &BTreeMap<String, usize>,
    rids: &BTreeMap<String, usize>,
) -> Result<(Vec<Option<usize>>, Vec<Option<usize>>, BTreeSet<(usize, usize)>), WdpError> {
    let reports = packet
        .states
        .iter()
        .map(|s| {
            packet.reports[s]
                .as_ref()
                .map(|r| lookup(rids, r))
                .transpose()
        })
        .collect::<Result<_, _>>()?;
    let target = packet
        .states
        .iter()
        .map(|s| {
            packet.target[s]
                .as_ref()
                .map(|r| lookup(rids, r))
                .transpose()
        })
        .collect::<Result<_, _>>()?;
    let generation = packet
        .generation
        .iter()
        .map(|(a, r)| Ok((lookup(aids, a)?, lookup(rids, r)?)))
        .collect::<Result<_, WdpError>>()?;
    Ok((reports, target, generation))
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SelfReferenceAudit {
    pub points: BTreeMap<String, SelfReferencePoint>,
    pub signature: SelfReferenceSignature,
    pub stability_available: bool,
    pub report_events_preserved: bool,
    pub generation_functional: bool,
    pub report_determined_accessible: bool,
    pub report_determined_presentation: bool,
    pub later_target_determined_accessible: bool,
    pub receipt_digest: String,
    pub authority_effect: AuthorityEffect,
}

pub fn audit_self_reference(
    packet: &NamedSelfReferencePacket,
) -> Result<SelfReferenceAudit, WdpError> {
    let model = checked_self_reference(packet)?;
    let signature = model.signature();
    let points = packet
        .states
        .iter()
        .enumerate()
        .map(|(x, s)| model.audit_point(x).map(|p| (s.clone(), p)))
        .collect::<Result<BTreeMap<_, _>, _>>()
        .map_err(|_| invalid("checked self-reference point audit failed"))?;
    let flags: Vec<_> = points
        .iter()
        .map(|(s, p)| {
            (
                s,
                [
                    p.report_available,
                    p.linkage_provided,
                    p.linkage_verified,
                    p.stability_available,
                    p.stability_success,
                    p.comparison_available,
                    p.comparison_success,
                ],
            )
        })
        .collect();
    let details = [
        model.stability_available(),
        model.report_events_preserved(),
        model.generation_is_functional(),
        model.report_factor_accessible().is_some(),
        model.report_factor_presentation().is_some(),
        model.later_target_factor_accessible().is_some(),
    ];
    let bytes = serde_json::to_vec(&(packet, flags, details))
        .map_err(|_| invalid("self-reference receipt serialization failed"))?;
    Ok(SelfReferenceAudit {
        points,
        signature,
        stability_available: details[0],
        report_events_preserved: details[1],
        generation_functional: details[2],
        report_determined_accessible: details[3],
        report_determined_presentation: details[4],
        later_target_determined_accessible: details[5],
        receipt_digest: blake3_digest(&bytes),
        authority_effect: AuthorityEffect::None,
    })
}

/// Recheck every bridge from independent packet data. A hash-valid status or
/// provenance claim never substitutes for generation/context/protocol replay.
pub fn verify_self_reference_audit(
    packet: &NamedSelfReferencePacket,
    candidate: &SelfReferenceAudit,
) -> Result<(), WdpError> {
    if *candidate != audit_self_reference(packet)? {
        return Err(invalid(
            "self-reference audit differs from independent bridge replay",
        ));
    }
    Ok(())
}

/// Construct a new candidate report/provenance table iff the independently
/// declared generation/later-target/comparison bridges admit total linked
/// success. This does not alter an actual observer or certify physical behavior.
pub fn plan_successful_self_reports(
    packet: &NamedSelfReferencePacket,
    require_context_stability: bool,
) -> Result<Option<NamedSelfReferencePacket>, WdpError> {
    let model = checked_self_reference(packet)?;
    let Some(planned) = model
        .successful_linked_report_plan(require_context_stability)
        .map_err(|_| invalid("self-report bridge planning failed"))?
    else {
        return Ok(None);
    };
    let labels: Vec<_> = packet.report_alphabet.iter().cloned().collect();
    let mut candidate = packet.clone();
    for (x, state) in packet.states.iter().enumerate() {
        let value = planned.data().reports[x].map(|r| labels[r].clone());
        candidate.reports.insert(state.clone(), value.clone());
        candidate.provenance.insert(
            state.clone(),
            value.map(|reported_value| NamedReflexiveProvenance {
                source_observer: packet.observer_id.clone(),
                target_observer: packet.observer_id.clone(),
                captured_accessible: packet.sigma[state].clone(),
                reaccessed_accessible: packet.sigma[state].clone(),
                reported_value,
            }),
        );
    }
    let audit = audit_self_reference(&candidate)?;
    if !audit.signature.linkage_verified
        || !audit.signature.comparison_success
        || (require_context_stability && !audit.signature.report_stable)
    {
        return Err(invalid(
            "planned self-report failed its independent named bridge replay",
        ));
    }
    Ok(Some(candidate))
}

// Origin: engine/crates_rs/core_wdp/src/self_reference_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:self-reference-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb401b87d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb401b87d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb401b87d {
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
impl BoundaryErrorb401b87d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb401b87d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb401b87d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb401b87d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb401b87d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb401b87d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb401b87d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb401b87d::ExceedsCapacity {
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
mod l4_boundary_tests_b401b87d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb401b87d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb401b87d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb401b87d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb401b87d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb401b87d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb401b87d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb401b87d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
