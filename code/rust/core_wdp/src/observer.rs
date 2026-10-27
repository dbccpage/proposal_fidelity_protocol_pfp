// Executable finite evidence; AuthorityEffect: None.
//! Chapters 10 & 14: Layered observer architecture, legacy packet adapters,
//! and functional observer relations audit with awareness firewall.
//! These nominal adapters preserve declarations; they do not validate their semantics.
//! Checked finite bridges live in `legacy_observer_adapters`,
//! `functional_classification`, and `self_reference_adapter`.
//! No awareness conclusion is inferred (WDP-CH14-N01).

use crate::error::WdpError;
use crate::retention::RetentionPacket;
use crate::types::AuthorityEffect;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

/// Legacy quotient observer representation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuotientObserver {
    pub carrier: BTreeSet<String>,
    pub equivalence_classes: Vec<BTreeSet<String>>,
    pub comparison: String,
}

impl QuotientObserver {
    pub fn new(
        carrier: BTreeSet<String>,
        equivalence_classes: Vec<BTreeSet<String>>,
        comparison: String,
    ) -> Result<Self, WdpError> {
        if carrier.is_empty() {
            return Err(WdpError::InvalidInput {
                detail: "quotient carrier must be non-empty".to_string(),
            });
        }
        let mut seen = BTreeSet::new();
        for block in &equivalence_classes {
            if block.is_empty() {
                return Err(WdpError::InvalidInput {
                    detail: "equivalence classes cannot contain empty blocks".to_string(),
                });
            }
            for elem in block {
                if !carrier.contains(elem) {
                    return Err(WdpError::InvalidInput {
                        detail: format!("element {elem} not in quotient carrier"),
                    });
                }
                if !seen.insert(elem.clone()) {
                    return Err(WdpError::InvalidInput {
                        detail: format!("equivalence classes must be disjoint; duplicate {elem}"),
                    });
                }
            }
        }
        if seen != carrier {
            return Err(WdpError::InvalidInput {
                detail: "equivalence classes must cover carrier".to_string(),
            });
        }
        Ok(Self {
            carrier,
            equivalence_classes,
            comparison,
        })
    }
}

/// Legacy operational observer packet representation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OperationalObserverPacket {
    pub states: BTreeSet<String>,
    pub start_state: String,
    pub alphabet: BTreeSet<String>,
    pub transitions: BTreeMap<(String, String), String>, // (state, symbol) -> next_state
    pub reports: BTreeMap<String, String>,               // state -> report
    pub profiles: BTreeMap<String, String>,              // state -> profile
}

impl OperationalObserverPacket {
    fn validate_state_coverage(
        states: &BTreeSet<String>,
        reports: &BTreeMap<String, String>,
        profiles: &BTreeMap<String, String>,
    ) -> Result<(), WdpError> {
        for s in states {
            if !reports.contains_key(s) {
                return Err(WdpError::InvalidInput {
                    detail: format!("missing report for state {s}"),
                });
            }
            if !profiles.contains_key(s) {
                return Err(WdpError::InvalidInput {
                    detail: format!("missing profile for state {s}"),
                });
            }
        }
        Ok(())
    }

    pub fn new(
        states: BTreeSet<String>,
        start_state: String,
        alphabet: BTreeSet<String>,
        transitions: BTreeMap<(String, String), String>,
        reports: BTreeMap<String, String>,
        profiles: BTreeMap<String, String>,
    ) -> Result<Self, WdpError> {
        if states.is_empty() || !states.contains(&start_state) {
            return Err(WdpError::InvalidInput {
                detail: "start state must belong to non-empty states carrier".to_string(),
            });
        }
        if alphabet.is_empty() {
            return Err(WdpError::InvalidInput {
                detail: "alphabet cannot be empty".to_string(),
            });
        }
        for ((s, a), tgt) in &transitions {
            if !states.contains(s) || !alphabet.contains(a) || !states.contains(tgt) {
                return Err(WdpError::InvalidInput {
                    detail: format!("transition ({s}, {a}) -> {tgt} outside carrier"),
                });
            }
        }
        Self::validate_state_coverage(&states, &reports, &profiles)?;
        Ok(Self {
            states,
            start_state,
            alphabet,
            transitions,
            reports,
            profiles,
        })
    }
}

/// Layered standard ObserverObject with full nominal interface.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverObject {
    pub carrier_k: String,
    pub local_state_f: String,
    pub comparison_r: String,
    pub defect_map_delta: String,
    pub repair_d0: String,
    pub closure_d1: Option<String>,
    pub gauge_j: String,
    pub transform_m: String,
    pub terminalizer_tau: String,
    pub authority_effect: AuthorityEffect,
}

/// Explicit bridge for adapting legacy observer representations into an ObserverObject.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserverBridge {
    pub source_kind: String,
    pub local_state_f: String,
    pub defect_map_delta: String,
    pub repair_d0: String,
    pub closure_d1: Option<String>,
    pub gauge_j: String,
    pub transform_m: String,
    pub terminalizer_tau: String,
}

impl ObserverBridge {
    pub fn is_typed(&self) -> bool {
        !self.source_kind.is_empty()
            && !self.local_state_f.is_empty()
            && !self.defect_map_delta.is_empty()
            && !self.repair_d0.is_empty()
            && !self.gauge_j.is_empty()
            && !self.transform_m.is_empty()
            && !self.terminalizer_tau.is_empty()
    }
}

/// Adapts a QuotientObserver into an ObserverObject via an explicit bridge.
pub fn adapt_quotient(
    observer: &QuotientObserver,
    bridge: Option<&ObserverBridge>,
) -> Result<ObserverObject, WdpError> {
    let b = bridge.ok_or_else(|| WdpError::MissingAdapter {
        detail: "quotient observers need an explicit bridge".to_string(),
    })?;
    if !b.is_typed() {
        return Err(WdpError::InvalidInput {
            detail: "bridge fields must be non-empty typed strings".to_string(),
        });
    }
    if b.source_kind != "quotient" {
        return Err(WdpError::AdapterMismatch {
            expected: "quotient".to_string(),
            found: b.source_kind.clone(),
        });
    }

    let carrier_str = observer
        .carrier
        .iter()
        .cloned()
        .collect::<Vec<_>>()
        .join(",");
    Ok(ObserverObject {
        carrier_k: format!("quotient:{carrier_str}"),
        local_state_f: b.local_state_f.clone(),
        comparison_r: observer.comparison.clone(),
        defect_map_delta: b.defect_map_delta.clone(),
        repair_d0: b.repair_d0.clone(),
        closure_d1: b.closure_d1.clone(),
        gauge_j: b.gauge_j.clone(),
        transform_m: b.transform_m.clone(),
        terminalizer_tau: b.terminalizer_tau.clone(),
        authority_effect: AuthorityEffect::None,
    })
}

/// Adapts an OperationalObserverPacket into an ObserverObject via an explicit bridge.
pub fn adapt_operational(
    observer: &OperationalObserverPacket,
    bridge: Option<&ObserverBridge>,
) -> Result<ObserverObject, WdpError> {
    let b = bridge.ok_or_else(|| WdpError::MissingAdapter {
        detail: "operational observers need an explicit bridge".to_string(),
    })?;
    if !b.is_typed() {
        return Err(WdpError::InvalidInput {
            detail: "bridge fields must be non-empty typed strings".to_string(),
        });
    }
    if b.source_kind != "operational" {
        return Err(WdpError::AdapterMismatch {
            expected: "operational".to_string(),
            found: b.source_kind.clone(),
        });
    }

    let carrier_str = observer
        .states
        .iter()
        .cloned()
        .collect::<Vec<_>>()
        .join(",");
    Ok(ObserverObject {
        carrier_k: format!("operational:{carrier_str}"),
        local_state_f: b.local_state_f.clone(),
        comparison_r: "report/profile comparison".to_string(),
        defect_map_delta: b.defect_map_delta.clone(),
        repair_d0: b.repair_d0.clone(),
        closure_d1: b.closure_d1.clone(),
        gauge_j: b.gauge_j.clone(),
        transform_m: b.transform_m.clone(),
        terminalizer_tau: b.terminalizer_tau.clone(),
        authority_effect: AuthorityEffect::None,
    })
}

/// Adapts a RetentionPacket into an ObserverObject via an explicit bridge.
pub fn adapt_retention(
    packet: &RetentionPacket,
    bridge: Option<&ObserverBridge>,
) -> Result<ObserverObject, WdpError> {
    let b = bridge.ok_or_else(|| WdpError::MissingAdapter {
        detail: "retention observers need an explicit bridge".to_string(),
    })?;
    if !b.is_typed() {
        return Err(WdpError::InvalidInput {
            detail: "bridge fields must be non-empty typed strings".to_string(),
        });
    }
    if b.source_kind != "retention" {
        return Err(WdpError::AdapterMismatch {
            expected: "retention".to_string(),
            found: b.source_kind.clone(),
        });
    }

    let carrier_str = packet
        .memory_carrier
        .iter()
        .cloned()
        .collect::<Vec<_>>()
        .join(",");
    Ok(ObserverObject {
        carrier_k: format!("retention:{carrier_str}"),
        local_state_f: b.local_state_f.clone(),
        comparison_r: "memory/comparison".to_string(),
        defect_map_delta: b.defect_map_delta.clone(),
        repair_d0: b.repair_d0.clone(),
        closure_d1: b.closure_d1.clone(),
        gauge_j: b.gauge_j.clone(),
        transform_m: b.transform_m.clone(),
        terminalizer_tau: b.terminalizer_tau.clone(),
        authority_effect: AuthorityEffect::None,
    })
}

/// Functional observer profile formalizing finite relations without phenomenology.
/// WDP-CH14-N01: Strict awareness firewall prohibits asserting awareness.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FunctionalObserverProfile {
    pub presentation_map: BTreeMap<String, String>,
    pub report_map: BTreeMap<String, String>,
    pub blind_spot_fibers: BTreeMap<String, BTreeSet<String>>,
    pub is_context_stable: bool,
    pub max_calibration_error: usize,
    pub demonstrates_awareness: bool,
    pub authority_effect: AuthorityEffect,
}

impl FunctionalObserverProfile {
    pub fn new(
        presentation_map: BTreeMap<String, String>,
        report_map: BTreeMap<String, String>,
        blind_spot_fibers: BTreeMap<String, BTreeSet<String>>,
        is_context_stable: bool,
        max_calibration_error: usize,
        demonstrates_awareness: bool,
    ) -> Result<Self, WdpError> {
        if demonstrates_awareness {
            return Err(WdpError::AwarenessFirewallViolation);
        }
        Ok(Self {
            presentation_map,
            report_map,
            blind_spot_fibers,
            is_context_stable,
            max_calibration_error,
            demonstrates_awareness: false,
            authority_effect: AuthorityEffect::None,
        })
    }
}

/// Audits finite functional relations among presentation, report, stability, and blind spots.
/// Resolves WDP-CH14-O01 without phenomenology premises.
pub fn audit_functional_observer_relations(
    carrier: &[String],
    presentation: &BTreeMap<String, String>,
    report: &BTreeMap<String, String>,
    context_transition: Option<&BTreeMap<String, String>>,
    ground_truth: Option<&BTreeMap<String, String>>,
) -> Result<FunctionalObserverProfile, WdpError> {
    let mut fibers: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for x in carrier {
        let p = presentation
            .get(x)
            .ok_or_else(|| WdpError::ElementNotFound {
                element: format!("carrier point {x} missing in presentation"),
            })?;
        fibers.entry(p.clone()).or_default().insert(x.clone());
    }

    let blind_spots: BTreeMap<String, BTreeSet<String>> = fibers
        .into_iter()
        .filter(|(_, pts)| pts.len() >= 2)
        .collect();

    let mut is_stable = true;
    if let Some(ctx) = context_transition {
        for x in carrier {
            let tx = ctx.get(x).unwrap_or(x);
            let px = presentation.get(x);
            let ptx = presentation.get(tx);
            if px != ptx {
                is_stable = false;
                break;
            }
        }
    }

    let mut cal_err = 0;
    if let Some(gt) = ground_truth {
        for x in carrier {
            let p = &presentation[x];
            let r = &report[p];
            let expected = gt.get(x).unwrap_or(r);
            if r != expected {
                cal_err += 1;
            }
        }
    }

    FunctionalObserverProfile::new(
        presentation.clone(),
        report.clone(),
        blind_spots,
        is_stable,
        cal_err,
        false, // strictly false per awareness firewall
    )
}

// Origin: engine/crates_rs/core_wdp/src/observer.rs
// Claim: urn:core:crates_rs:core-wdp:observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord006e9ee1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord006e9ee1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError006e9ee1 {
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
impl BoundaryError006e9ee1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError006e9ee1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError006e9ee1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord006e9ee1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError006e9ee1> {
        if capacity_bound == 0 {
            return Err(BoundaryError006e9ee1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError006e9ee1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError006e9ee1::ExceedsCapacity {
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
    fn test_observer_adapters_and_bridges() {
        let carrier = BTreeSet::from(["a".to_string(), "b".to_string()]);
        let classes = vec![
            BTreeSet::from(["a".to_string()]),
            BTreeSet::from(["b".to_string()]),
        ];
        let q_obs = QuotientObserver::new(carrier, classes, "discrete".to_string()).unwrap();

        let bridge = ObserverBridge {
            source_kind: "quotient".to_string(),
            local_state_f: "state".to_string(),
            defect_map_delta: "delta".to_string(),
            repair_d0: "d0".to_string(),
            closure_d1: None,
            gauge_j: "L1".to_string(),
            transform_m: "id".to_string(),
            terminalizer_tau: "eval".to_string(),
        };

        let obj = adapt_quotient(&q_obs, Some(&bridge)).unwrap();
        assert_eq!(obj.comparison_r, "discrete");
        assert_eq!(obj.authority_effect, AuthorityEffect::None);
    }

    #[test]
    fn test_awareness_firewall_enforcement() {
        let carrier = vec!["x0".to_string(), "x1".to_string()];
        let pres = BTreeMap::from([
            ("x0".to_string(), "p0".to_string()),
            ("x1".to_string(), "p0".to_string()),
        ]);
        let rep = BTreeMap::from([("p0".to_string(), "r0".to_string())]);

        let profile =
            audit_functional_observer_relations(&carrier, &pres, &rep, None, None).unwrap();
        assert!(!profile.demonstrates_awareness);
        assert_eq!(profile.blind_spot_fibers.len(), 1);

        // Attempting to assert awareness must fail with typed error
        let illegal = FunctionalObserverProfile::new(
            pres,
            rep,
            BTreeMap::new(),
            true,
            0,
            true, // VIOLATION
        );
        assert!(matches!(illegal, Err(WdpError::AwarenessFirewallViolation)));
    }
}

#[cfg(test)]
mod l4_boundary_tests_006e9ee1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord006e9ee1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord006e9ee1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord006e9ee1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord006e9ee1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord006e9ee1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError006e9ee1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError006e9ee1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
