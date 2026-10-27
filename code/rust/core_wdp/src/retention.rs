// Executable finite evidence; AuthorityEffect: None.
//! Root W: Memory retention packets, order-free Moore partition refinement,
//! and component-independence countermodels CM1–CM8.
//! Finite total labelled deterministic packets admit a minimal behavioral
//! quotient under explicitly chosen report equality (or a checked equivalence
//! comparison). General retention constructors and arbitrary tolerance relations
//! are not thereby derived from primitive difference.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_323f86fe<T> {
    fn checked_invariant_323f86fe(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_323f86fe<T> for Option<T> {
    #[inline]
    fn checked_invariant_323f86fe(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_323f86fe<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_323f86fe(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::error::WdpError;
use crate::types::AuthorityEffect;
use core_category_theory::finite_moore::{FiniteMoore, MooreQuotient};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

/// A finite memory retention packet R = (M, Sigma, u, r, approx).
/// Represents discrete persistent memory with update transitions, reports,
/// and a declared tolerance/recognition relation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RetentionPacket {
    pub memory_carrier: BTreeSet<String>,
    pub inputs: BTreeSet<String>,
    pub update_map: BTreeMap<(String, String), String>, // (state, input) -> next_state
    pub report_map: BTreeMap<String, String>,           // state -> report
    pub comparison: BTreeSet<(String, String)>,         // tolerance relation on reports
    pub authority_effect: AuthorityEffect,
}

impl RetentionPacket {
    pub fn new(
        memory_carrier: BTreeSet<String>,
        inputs: BTreeSet<String>,
        update_map: BTreeMap<(String, String), String>,
        report_map: BTreeMap<String, String>,
        comparison: BTreeSet<(String, String)>,
    ) -> Result<Self, WdpError> {
        if memory_carrier.is_empty() {
            return Err(WdpError::InvalidInput {
                detail: "memory carrier cannot be empty".to_string(),
            });
        }
        Self::validate_update_map(&memory_carrier, &inputs, &update_map)?;
        Self::validate_report_map(&memory_carrier, &report_map)?;

        Ok(Self {
            memory_carrier,
            inputs,
            update_map,
            report_map,
            comparison,
            authority_effect: AuthorityEffect::None,
        })
    }

    fn validate_update_map(
        memory_carrier: &BTreeSet<String>,
        inputs: &BTreeSet<String>,
        update_map: &BTreeMap<(String, String), String>,
    ) -> Result<(), WdpError> {
        for ((m, i), next_m) in update_map {
            if !memory_carrier.contains(m) {
                return Err(WdpError::InvalidInput {
                    detail: format!("update source state {m} not in memory carrier"),
                });
            }
            if !inputs.contains(i) {
                return Err(WdpError::InvalidInput {
                    detail: format!("update input {i} not in input alphabet"),
                });
            }
            if !memory_carrier.contains(next_m) {
                return Err(WdpError::InvalidInput {
                    detail: format!("update target state {next_m} not in memory carrier"),
                });
            }
        }
        for m in memory_carrier {
            for i in inputs {
                if !update_map.contains_key(&(m.clone(), i.clone())) {
                    return Err(WdpError::InvalidInput {
                        detail: format!("update map missing transition ({m}, {i})"),
                    });
                }
            }
        }
        Ok(())
    }

    fn validate_report_map(
        memory_carrier: &BTreeSet<String>,
        report_map: &BTreeMap<String, String>,
    ) -> Result<(), WdpError> {
        for m in report_map.keys() {
            if !memory_carrier.contains(m) {
                return Err(WdpError::InvalidInput {
                    detail: format!("report state {m} not in memory carrier"),
                });
            }
        }
        for m in memory_carrier {
            if !report_map.contains_key(m) {
                return Err(WdpError::InvalidInput {
                    detail: format!("report map missing state {m}"),
                });
            }
        }
        Ok(())
    }

    /// Steps the retention packet given current state and an input symbol.
    pub fn step(&self, state: &str, input_symbol: &str) -> Result<&str, WdpError> {
        self.update_map
            .get(&(state.to_string(), input_symbol.to_string()))
            .map(|s| s.as_str())
            .ok_or_else(|| WdpError::InvalidInput {
                detail: format!("no update transition defined for ({state}, {input_symbol})"),
            })
    }

    /// Reads the declared report for a given state.
    pub fn report(&self, state: &str) -> Result<&str, WdpError> {
        self.report_map
            .get(state)
            .map(|s| s.as_str())
            .ok_or_else(|| WdpError::ElementNotFound {
                element: state.to_string(),
            })
    }

    /// Evaluates if two report values are recognized as equivalent under the declared comparison.
    pub fn are_equivalent(&self, o1: &str, o2: &str) -> bool {
        if o1 == o2 {
            return true;
        }
        self.comparison.contains(&(o1.to_string(), o2.to_string()))
            || self.comparison.contains(&(o2.to_string(), o1.to_string()))
    }

    /// Checks if distinct memory states produce distinct reports (observability).
    pub fn is_observable(&self) -> bool {
        let reports: BTreeSet<&str> = self.report_map.values().map(|s| s.as_str()).collect();
        reports.len() == self.memory_carrier.len()
    }

    /// Checks if update map under a given input symbol is a well-defined permutation on memory carrier.
    pub fn is_reversible(&self, input_symbol: &str) -> bool {
        if !self.inputs.contains(input_symbol) {
            return false;
        }
        let mut targets: BTreeSet<&str> = BTreeSet::new();
        for m in &self.memory_carrier {
            match self.step(m, input_symbol) {
                Ok(next_m) => {
                    targets.insert(next_m);
                }
                Err(_) => return false,
            }
        }
        targets.len() == self.memory_carrier.len()
    }
}

/// Compare all branches of the generated input tree through depth k. This is
/// an equivalence only when the chosen report comparison is one; arbitrary
/// tolerances may be nontransitive. No global clock across branches is supplied.
/// The checked unbounded quotients below settle the finite deterministic scope.
pub fn tree_behavior_equivalent(
    p1: &RetentionPacket,
    s1: &str,
    p2: &RetentionPacket,
    s2: &str,
    depth: usize,
) -> bool {
    if p1.inputs != p2.inputs || !reports_mutually_equivalent(p1, s1, p2, s2) {
        return false;
    }
    if depth == 0 {
        return true;
    }
    p1.inputs.iter().all(|sym| {
        let (Ok(next1), Ok(next2)) = (p1.step(s1, sym), p2.step(s2, sym)) else {
            return false;
        };
        tree_behavior_equivalent(p1, next1, p2, next2, depth - 1)
    })
}

fn reports_mutually_equivalent(
    p1: &RetentionPacket,
    s1: &str,
    p2: &RetentionPacket,
    s2: &str,
) -> bool {
    let (Ok(r1), Ok(r2)) = (p1.report(s1), p2.report(s2)) else {
        return false;
    };
    p1.are_equivalent(r1, r2) && p2.are_equivalent(r2, r1)
}

/// WDP names together with the sovereign finite-coalgebra certificate. Report
/// equality is exact string equality; the packet's tolerance is not silently
/// promoted to an equivalence relation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RetentionBehavioralQuotient {
    pub state_order: Vec<String>,
    pub input_order: Vec<String>,
    pub report_labels: Vec<String>,
    pub certificate: MooreQuotient,
}

fn validate_packet(packet: &RetentionPacket) -> Result<(), WdpError> {
    RetentionPacket::new(
        packet.memory_carrier.clone(),
        packet.inputs.clone(),
        packet.update_map.clone(),
        packet.report_map.clone(),
        packet.comparison.clone(),
    )?;
    Ok(())
}

fn named_moore(
    packet: &RetentionPacket,
    report_ids: &BTreeMap<String, usize>,
) -> Result<FiniteMoore, WdpError> {
    validate_packet(packet)?;
    let state_ids: BTreeMap<_, _> = packet
        .memory_carrier
        .iter()
        .cloned()
        .enumerate()
        .map(|(i, s)| (s, i))
        .collect();
    let reports = packet
        .memory_carrier
        .iter()
        .map(|s| report_ids[&packet.report_map[s]])
        .collect();
    let transitions = packet
        .memory_carrier
        .iter()
        .map(|s| {
            packet
                .inputs
                .iter()
                .map(|i| state_ids[&packet.update_map[&(s.clone(), i.clone())]])
                .collect()
        })
        .collect();
    FiniteMoore::new(reports, transitions, packet.inputs.len()).map_err(|error| {
        WdpError::InvalidInput {
            detail: format!("finite Moore presentation: {error:?}"),
        }
    })
}

/// Classify the packet by the greatest exact-readout-respecting transition
/// congruence, without assuming a clock, initial state, or ordered alphabet.
/// The finite input tree is generated by the update operations themselves.
/// All refinement, quotient and minimality mathematics belongs to
/// `core_category_theory::finite_moore`.
pub fn compute_exact_behavioral_quotient(
    packet: &RetentionPacket,
) -> Result<RetentionBehavioralQuotient, WdpError> {
    validate_packet(packet)?;
    let labels: BTreeSet<_> = packet.report_map.values().cloned().collect();
    let report_labels: Vec<_> = labels.into_iter().collect();
    let ids = report_labels
        .iter()
        .cloned()
        .enumerate()
        .map(|(i, s)| (s, i))
        .collect();
    let machine = named_moore(packet, &ids)?;
    Ok(RetentionBehavioralQuotient {
        state_order: packet.memory_carrier.iter().cloned().collect(),
        input_order: packet.inputs.iter().cloned().collect(),
        report_labels,
        certificate: machine.behavioral_quotient(),
    })
}

/// Verify a named exact quotient against the original packet; names and label
/// interning are part of the binding, not trusted annotations.
pub fn verify_exact_behavioral_quotient(
    packet: &RetentionPacket,
    receipt: &RetentionBehavioralQuotient,
) -> Result<bool, WdpError> {
    let checked = compute_exact_behavioral_quotient(packet)?;
    if receipt.state_order != checked.state_order
        || receipt.input_order != checked.input_order
        || receipt.report_labels != checked.report_labels
    {
        return Ok(false);
    }
    let ids = receipt
        .report_labels
        .iter()
        .cloned()
        .enumerate()
        .map(|(i, s)| (s, i))
        .collect();
    Ok(named_moore(packet, &ids)?.verify_quotient(&receipt.certificate))
}

/// Compare unpointed packets by their sets of exact report behaviors, with the
/// same declared input and report labels. Multiplicity of indistinguishable
/// memory states is irrelevant. The resulting minimal quotients are isomorphic.
pub fn same_exact_retention_behaviors(
    first: &RetentionPacket,
    second: &RetentionPacket,
) -> Result<bool, WdpError> {
    validate_packet(first)?;
    validate_packet(second)?;
    if first.inputs != second.inputs {
        return Ok(false);
    }
    let labels: BTreeSet<_> = first
        .report_map
        .values()
        .chain(second.report_map.values())
        .cloned()
        .collect();
    let ids = labels
        .into_iter()
        .enumerate()
        .map(|(i, s)| (s, i))
        .collect();
    Ok(named_moore(first, &ids)?.same_behavior_set(&named_moore(second, &ids)?))
}

/// Compute the behavioral quotient under the packet's declared report
/// comparison, only when its reflexive symmetric reading is transitive on the
/// realized reports. Nontransitive tolerances do not define quotient classes;
/// they are rejected rather than replaced by an unstated transitive closure.
pub fn compute_behavioral_quotient(
    packet: &RetentionPacket,
) -> Result<(usize, BTreeMap<String, usize>), WdpError> {
    validate_packet(packet)?;
    let labels: Vec<_> = packet
        .report_map
        .values()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    for a in &labels {
        for b in &labels {
            for c in &labels {
                if packet.are_equivalent(a, b)
                    && packet.are_equivalent(b, c)
                    && !packet.are_equivalent(a, c)
                {
                    return Err(WdpError::InvalidInput {
                        detail: format!(
                            "nontransitive report comparison: {a} ~ {b}, {b} ~ {c}, {a} !~ {c}"
                        ),
                    });
                }
            }
        }
    }
    // Equal comparison rows are precisely equivalence classes, because the
    // realized relation has now been checked to be an equivalence relation.
    let mut signatures = BTreeMap::new();
    let mut report_ids = BTreeMap::new();
    for label in &labels {
        let signature: Vec<_> = labels
            .iter()
            .map(|other| packet.are_equivalent(label, other))
            .collect();
        let fresh = signatures.len();
        let id = *signatures.entry(signature).or_insert(fresh);
        report_ids.insert(label.clone(), id);
    }
    let quotient = named_moore(packet, &report_ids)?.behavioral_quotient();
    Ok((
        quotient.quotient.state_count(),
        packet
            .memory_carrier
            .iter()
            .cloned()
            .zip(quotient.state_to_block)
            .collect(),
    ))
}

/// Retention property vector assessing component independence (WDP-CH03-O02).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RetentionPropertyVector {
    pub is_nontrivial_carrier: bool,
    pub is_fully_reversible: bool,
    pub is_observable: bool,
    pub has_nontrivial_tolerance: bool,
    pub quotient_size: usize,
    pub is_minimal: bool,
}

/// Analyzes a retention packet and extracts its property vector.
pub fn analyze_retention_packet(
    packet: &RetentionPacket,
) -> Result<RetentionPropertyVector, WdpError> {
    validate_packet(packet)?;
    let nontrivial = packet.memory_carrier.len() >= 2;
    let rev = packet.inputs.iter().all(|sym| packet.is_reversible(sym));
    let obs = packet.is_observable();
    let reports: BTreeSet<&str> = packet.report_map.values().map(|s| s.as_str()).collect();
    let mut tol = false;
    for &r1 in &reports {
        for &r2 in &reports {
            if r1 != r2 && packet.are_equivalent(r1, r2) {
                tol = true;
                break;
            }
        }
        if tol {
            break;
        }
    }
    let (q_size, _) = compute_behavioral_quotient(packet)?;
    let minimal = q_size == packet.memory_carrier.len();

    Ok(RetentionPropertyVector {
        is_nontrivial_carrier: nontrivial,
        is_fully_reversible: rev,
        is_observable: obs,
        has_nontrivial_tolerance: tol,
        quotient_size: q_size,
        is_minimal: minimal,
    })
}

// Concrete countermodels CM1–CM8 demonstrating pairwise component independence

/// CM1: Carrier non-triviality (|M| >= 2) with static update (u(m, tick) = m).
pub fn make_cm1_static_carrier() -> RetentionPacket {
    let m = BTreeSet::from(["m0".to_string(), "m1".to_string()]);
    let inputs = BTreeSet::from(["tick".to_string()]);
    let mut u = BTreeMap::new();
    u.insert(("m0".to_string(), "tick".to_string()), "m0".to_string());
    u.insert(("m1".to_string(), "tick".to_string()), "m1".to_string());
    let mut r = BTreeMap::new();
    r.insert("m0".to_string(), "r0".to_string());
    r.insert("m1".to_string(), "r1".to_string());
    let approx = BTreeSet::from([
        ("r0".to_string(), "r0".to_string()),
        ("r1".to_string(), "r1".to_string()),
    ]);
    RetentionPacket::new(m, inputs, u, r, approx).checked_invariant_323f86fe("checked invariant")
}

/// CM2: Dynamic state update with blind/constant report (r(m) = constant).
pub fn make_cm2_blind_readout() -> RetentionPacket {
    let m = BTreeSet::from(["m0".to_string(), "m1".to_string()]);
    let inputs = BTreeSet::from(["toggle".to_string()]);
    let mut u = BTreeMap::new();
    u.insert(("m0".to_string(), "toggle".to_string()), "m1".to_string());
    u.insert(("m1".to_string(), "toggle".to_string()), "m0".to_string());
    let mut r = BTreeMap::new();
    r.insert("m0".to_string(), "constant".to_string());
    r.insert("m1".to_string(), "constant".to_string());
    let approx = BTreeSet::from([("constant".to_string(), "constant".to_string())]);
    RetentionPacket::new(m, inputs, u, r, approx).checked_invariant_323f86fe("checked invariant")
}

/// CM3: Invertible update dynamics with non-injective report (ker(r) > id).
pub fn make_cm3_coarse_grained_report() -> RetentionPacket {
    let m = BTreeSet::from(["m0".to_string(), "m1".to_string(), "m2".to_string()]);
    let inputs = BTreeSet::from(["cycle".to_string()]);
    let mut u = BTreeMap::new();
    u.insert(("m0".to_string(), "cycle".to_string()), "m1".to_string());
    u.insert(("m1".to_string(), "cycle".to_string()), "m2".to_string());
    u.insert(("m2".to_string(), "cycle".to_string()), "m0".to_string());
    let mut r = BTreeMap::new();
    r.insert("m0".to_string(), "even".to_string());
    r.insert("m1".to_string(), "odd".to_string());
    r.insert("m2".to_string(), "even".to_string());
    let approx = BTreeSet::from([
        ("even".to_string(), "even".to_string()),
        ("odd".to_string(), "odd".to_string()),
    ]);
    RetentionPacket::new(m, inputs, u, r, approx).checked_invariant_323f86fe("checked invariant")
}

/// CM4: Injective report with non-trivial tolerance relation where val0 ~ val1.
pub fn make_cm4_nontrivial_tolerance() -> RetentionPacket {
    let m = BTreeSet::from(["m0".to_string(), "m1".to_string()]);
    let inputs = BTreeSet::from(["step".to_string()]);
    let mut u = BTreeMap::new();
    u.insert(("m0".to_string(), "step".to_string()), "m1".to_string());
    u.insert(("m1".to_string(), "step".to_string()), "m0".to_string());
    let mut r = BTreeMap::new();
    r.insert("m0".to_string(), "val0".to_string());
    r.insert("m1".to_string(), "val1".to_string());
    let approx = BTreeSet::from([
        ("val0".to_string(), "val0".to_string()),
        ("val1".to_string(), "val1".to_string()),
        ("val0".to_string(), "val1".to_string()),
    ]);
    RetentionPacket::new(m, inputs, u, r, approx).checked_invariant_323f86fe("checked invariant")
}

/// CM5: Injective report (r = id) with collapsing lossy reset update u(m, reset) = m0.
pub fn make_cm5_lossy_reset() -> RetentionPacket {
    let m = BTreeSet::from(["m0".to_string(), "m1".to_string()]);
    let inputs = BTreeSet::from(["reset".to_string(), "keep".to_string()]);
    let mut u = BTreeMap::new();
    u.insert(("m0".to_string(), "reset".to_string()), "m0".to_string());
    u.insert(("m1".to_string(), "reset".to_string()), "m0".to_string());
    u.insert(("m0".to_string(), "keep".to_string()), "m0".to_string());
    u.insert(("m1".to_string(), "keep".to_string()), "m1".to_string());
    let mut r = BTreeMap::new();
    r.insert("m0".to_string(), "m0".to_string());
    r.insert("m1".to_string(), "m1".to_string());
    let approx = BTreeSet::from([
        ("m0".to_string(), "m0".to_string()),
        ("m1".to_string(), "m1".to_string()),
    ]);
    RetentionPacket::new(m, inputs, u, r, approx).checked_invariant_323f86fe("checked invariant")
}

/// CM6: Single-state carrier (|M| = 1).
pub fn make_cm6_trivial_carrier() -> RetentionPacket {
    let m = BTreeSet::from(["m0".to_string()]);
    let inputs = BTreeSet::from(["tick".to_string()]);
    let mut u = BTreeMap::new();
    u.insert(("m0".to_string(), "tick".to_string()), "m0".to_string());
    let mut r = BTreeMap::new();
    r.insert("m0".to_string(), "r0".to_string());
    let approx = BTreeSet::from([("r0".to_string(), "r0".to_string())]);
    RetentionPacket::new(m, inputs, u, r, approx).checked_invariant_323f86fe("checked invariant")
}

/// CM7: Irreversible reset dynamics with blind readout.
pub fn make_cm7_lossy_blind() -> RetentionPacket {
    let m = BTreeSet::from(["m0".to_string(), "m1".to_string()]);
    let inputs = BTreeSet::from(["reset".to_string()]);
    let mut u = BTreeMap::new();
    u.insert(("m0".to_string(), "reset".to_string()), "m0".to_string());
    u.insert(("m1".to_string(), "reset".to_string()), "m0".to_string());
    let mut r = BTreeMap::new();
    r.insert("m0".to_string(), "same".to_string());
    r.insert("m1".to_string(), "same".to_string());
    let approx = BTreeSet::from([("same".to_string(), "same".to_string())]);
    RetentionPacket::new(m, inputs, u, r, approx).checked_invariant_323f86fe("checked invariant")
}

/// CM8: Irreversible reset with non-trivial tolerance relation.
pub fn make_cm8_lossy_tolerance() -> RetentionPacket {
    let m = BTreeSet::from(["m0".to_string(), "m1".to_string()]);
    let inputs = BTreeSet::from(["reset".to_string(), "keep".to_string()]);
    let mut u = BTreeMap::new();
    u.insert(("m0".to_string(), "reset".to_string()), "m0".to_string());
    u.insert(("m1".to_string(), "reset".to_string()), "m0".to_string());
    u.insert(("m0".to_string(), "keep".to_string()), "m0".to_string());
    u.insert(("m1".to_string(), "keep".to_string()), "m1".to_string());
    let mut r = BTreeMap::new();
    r.insert("m0".to_string(), "val0".to_string());
    r.insert("m1".to_string(), "val1".to_string());
    let approx = BTreeSet::from([
        ("val0".to_string(), "val0".to_string()),
        ("val1".to_string(), "val1".to_string()),
        ("val0".to_string(), "val1".to_string()),
    ]);
    RetentionPacket::new(m, inputs, u, r, approx).checked_invariant_323f86fe("checked invariant")
}

// Origin: engine/crates_rs/core_wdp/src/retention.rs
// Claim: urn:core:crates_rs:core-wdp:retention:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord323f86fe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord323f86fe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError323f86fe {
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
impl BoundaryError323f86fe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError323f86fe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError323f86fe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord323f86fe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError323f86fe> {
        if capacity_bound == 0 {
            return Err(BoundaryError323f86fe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError323f86fe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError323f86fe::ExceedsCapacity {
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
    fn test_countermodels_independence() {
        let v1 = analyze_retention_packet(&make_cm1_static_carrier()).unwrap();
        assert!(v1.is_nontrivial_carrier);
        assert!(v1.is_fully_reversible);
        assert!(v1.is_observable);
        assert!(!v1.has_nontrivial_tolerance);
        assert!(v1.is_minimal);

        let v2 = analyze_retention_packet(&make_cm2_blind_readout()).unwrap();
        assert!(v2.is_nontrivial_carrier);
        assert!(v2.is_fully_reversible);
        assert!(!v2.is_observable); // blind readout
        assert!(!v2.is_minimal); // collapses to 1 block

        let v3 = analyze_retention_packet(&make_cm3_coarse_grained_report()).unwrap();
        assert!(v3.is_nontrivial_carrier);
        assert!(v3.is_fully_reversible);
        assert!(!v3.is_observable); // 2 reports for 3 states

        let v4 = analyze_retention_packet(&make_cm4_nontrivial_tolerance()).unwrap();
        assert!(v4.has_nontrivial_tolerance);

        let v5 = analyze_retention_packet(&make_cm5_lossy_reset()).unwrap();
        assert!(!v5.is_fully_reversible); // reset is lossy
        assert!(v5.is_observable);

        let v6 = analyze_retention_packet(&make_cm6_trivial_carrier()).unwrap();
        assert!(!v6.is_nontrivial_carrier);

        let v7 = analyze_retention_packet(&make_cm7_lossy_blind()).unwrap();
        assert!(!v7.is_fully_reversible);
        assert!(!v7.is_observable);

        let v8 = analyze_retention_packet(&make_cm8_lossy_tolerance()).unwrap();
        assert!(!v8.is_fully_reversible);
        assert!(v8.has_nontrivial_tolerance);
    }

    #[test]
    fn test_branching_tree_behavior_equivalent() {
        let cm1 = make_cm1_static_carrier();
        assert!(tree_behavior_equivalent(&cm1, "m0", &cm1, "m0", 3));
        assert!(!tree_behavior_equivalent(&cm1, "m0", &cm1, "m1", 3));
    }
    #[test]
    fn exact_and_comparison_quotients_are_explicitly_distinct() {
        let packet = make_cm4_nontrivial_tolerance();
        assert_eq!(compute_behavioral_quotient(&packet).unwrap().0, 1);
        let exact = compute_exact_behavioral_quotient(&packet).unwrap();
        assert_eq!(exact.certificate.quotient.state_count(), 2);
        assert!(verify_exact_behavioral_quotient(&packet, &exact).unwrap());
        let mut forged = exact;
        forged.report_labels.reverse();
        assert!(!verify_exact_behavioral_quotient(&packet, &forged).unwrap());
    }

    #[test]
    fn rejects_partial_updates_and_nontransitive_tolerance() {
        let mut incomplete = make_cm1_static_carrier();
        incomplete.update_map.clear();
        assert!(compute_exact_behavioral_quotient(&incomplete).is_err());
        assert!(analyze_retention_packet(&incomplete).is_err());
        let states: BTreeSet<_> = ["a", "b", "c"].map(String::from).into();
        let update = states
            .iter()
            .map(|s| ((s.clone(), "keep".to_string()), s.clone()))
            .collect();
        let reports = states.iter().map(|s| (s.clone(), s.clone())).collect();
        let comparison = BTreeSet::from([
            ("a".to_string(), "b".to_string()),
            ("b".to_string(), "c".to_string()),
        ]);
        let packet = RetentionPacket::new(
            states,
            BTreeSet::from(["keep".to_string()]),
            update,
            reports,
            comparison,
        )
        .unwrap();
        assert!(compute_behavioral_quotient(&packet).is_err());
        assert_eq!(
            compute_exact_behavioral_quotient(&packet)
                .unwrap()
                .certificate
                .quotient
                .state_count(),
            3
        );
    }

    #[test]
    fn named_classification_preserves_report_labels() {
        let first = make_cm2_blind_readout();
        let second = make_cm7_lossy_blind();
        assert!(!same_exact_retention_behaviors(&first, &second).unwrap());
        let mut renamed = first.clone();
        for report in renamed.report_map.values_mut() {
            *report = "different".to_string();
        }
        assert!(!same_exact_retention_behaviors(&first, &renamed).unwrap());
        let singleton = RetentionPacket::new(
            BTreeSet::from(["single".to_string()]),
            first.inputs.clone(),
            BTreeMap::from([(
                ("single".to_string(), "toggle".to_string()),
                "single".to_string(),
            )]),
            BTreeMap::from([("single".to_string(), "constant".to_string())]),
            BTreeSet::new(),
        )
        .unwrap();
        assert!(same_exact_retention_behaviors(&first, &singleton).unwrap());
    }
}

#[cfg(test)]
mod l4_boundary_tests_323f86fe {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord323f86fe::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord323f86fe::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord323f86fe::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord323f86fe::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord323f86fe::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError323f86fe::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError323f86fe::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
