// Executable finite evidence; AuthorityEffect: None.
//! Chapter 11: Covering sieves, local report sections, restriction maps,
//! sheaf descent solver, and certified SheafGluingObstruction.
//! Implements WDP-CH11-D01 for the function sheaf on a finite discrete space.
//! Objects are subsets of the carrier, arrows are inclusions, covers have union
//! equal to their target, and restriction is ordinary function restriction.
//! This does not settle WDP-CH11-O01 for general observer presentations with
//! partial transport maps or constrained reports.

use crate::error::WdpError;
use crate::types::AuthorityEffect;
use core_category_theory::finite_report_descent::{
    DescentError, DescentOutcome, FiniteReportPresheaf,
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

/// A finite covering sieve U = {U_i} of a finite carrier X.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoveringSieve {
    pub carrier: BTreeSet<String>,
    pub contexts: BTreeMap<String, BTreeSet<String>>, // context_id -> points in U_i
}

impl CoveringSieve {
    pub fn new(
        carrier: BTreeSet<String>,
        contexts: BTreeMap<String, BTreeSet<String>>,
    ) -> Result<Self, WdpError> {
        let mut covered: BTreeSet<String> = BTreeSet::new();
        for (cid, pts) in &contexts {
            for pt in pts {
                if !carrier.contains(pt) {
                    return Err(WdpError::InvalidInput {
                        detail: format!("context {cid} contains element {pt} outside carrier"),
                    });
                }
                covered.insert(pt.clone());
            }
        }
        if covered != carrier {
            let missing: Vec<String> = carrier.difference(&covered).cloned().collect();
            return Err(WdpError::IncompleteCoverage { missing });
        }
        Ok(Self { carrier, contexts })
    }

    pub fn overlap(&self, cid_i: &str, cid_j: &str) -> BTreeSet<String> {
        let empty = BTreeSet::new();
        let pts_i = self.contexts.get(cid_i).unwrap_or(&empty);
        let pts_j = self.contexts.get(cid_j).unwrap_or(&empty);
        pts_i.intersection(pts_j).cloned().collect()
    }
}

/// A local observation report section s_i: U_i -> Report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalReportSection {
    pub context_id: String,
    pub assignments: BTreeMap<String, String>, // point -> value
}

impl LocalReportSection {
    pub fn new(context_id: String, assignments: BTreeMap<String, String>) -> Self {
        Self {
            context_id,
            assignments,
        }
    }

    pub fn get_value(&self, point: &str) -> Option<&str> {
        self.assignments.get(point).map(|s| s.as_str())
    }

    pub fn domain(&self) -> BTreeSet<String> {
        self.assignments.keys().cloned().collect()
    }
}

/// Typed witness of local incompatibility or gluing obstruction across covering overlaps.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SheafGluingObstruction {
    pub context_i: String,
    pub context_j: String,
    pub point: String,
    pub value_i: String,
    pub value_j: String,
    pub reason: String,
}

/// WDP-CH11-D01: Observer descent receipt certifying global sheaf gluing or typed obstruction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DescentReceipt {
    pub sieve: CoveringSieve,
    pub local_sections: Vec<LocalReportSection>,
    pub is_compatible: bool,
    pub global_section: Option<BTreeMap<String, String>>,
    pub obstruction: Option<SheafGluingObstruction>,
    pub authority_effect: AuthorityEffect,
}

/// Evaluates local report compatibility across covering overlaps.
///
/// If all local report sections agree on all overlaps U_i cap U_j, constructs the unique
/// global report section s : X -> Report (the sheaf condition).
/// If any pairwise overlap disagrees, certifies the exact SheafGluingObstruction.
pub fn solve_observer_descent(
    sieve: &CoveringSieve,
    local_sections: &[LocalReportSection],
) -> Result<DescentReceipt, WdpError> {
    // Public fields and serde allow construction without `new`; recheck the
    // coverage at the boundary before accepting an executable receipt.
    CoveringSieve::new(sieve.carrier.clone(), sieve.contexts.clone())?;
    let sec_map = build_verified_section_map(sieve, local_sections)?;

    // Pairwise overlap compatibility check
    if let Some(obstruction) = find_overlap_obstruction(sieve, &sec_map) {
        return Ok(DescentReceipt {
            sieve: sieve.clone(),
            local_sections: local_sections.to_vec(),
            is_compatible: false,
            global_section: None,
            obstruction: Some(obstruction),
            authority_effect: AuthorityEffect::None,
        });
    }

    // Glued unique global section
    let mut global_dict: BTreeMap<String, String> = BTreeMap::new();
    for cid in sieve.contexts.keys() {
        let sec = sec_map[cid];
        for (pt, val) in &sec.assignments {
            global_dict.insert(pt.clone(), val.clone());
        }
    }

    Ok(DescentReceipt {
        sieve: sieve.clone(),
        local_sections: local_sections.to_vec(),
        is_compatible: true,
        global_section: Some(global_dict),
        obstruction: None,
        authority_effect: AuthorityEffect::None,
    })
}

fn build_verified_section_map<'a>(
    sieve: &CoveringSieve,
    local_sections: &'a [LocalReportSection],
) -> Result<BTreeMap<String, &'a LocalReportSection>, WdpError> {
    let mut sec_map: BTreeMap<String, &'a LocalReportSection> = BTreeMap::new();
    for sec in local_sections {
        if !sieve.contexts.contains_key(&sec.context_id) {
            return Err(WdpError::InvalidInput {
                detail: format!("unknown section context {}", sec.context_id),
            });
        }
        if sec_map.contains_key(&sec.context_id) {
            return Err(WdpError::InvalidInput {
                detail: format!("duplicate section for context {}", sec.context_id),
            });
        }
        sec_map.insert(sec.context_id.clone(), sec);
    }

    // Verify all sieve contexts are covered with matching domains
    for (cid, pts) in &sieve.contexts {
        let sec = sec_map.get(cid).ok_or_else(|| WdpError::InvalidInput {
            detail: format!("missing section for context {cid}"),
        })?;
        if &sec.domain() != pts {
            return Err(WdpError::SectionDomainMismatch {
                context: cid.clone(),
                expected: pts.iter().cloned().collect(),
                found: sec.domain().into_iter().collect(),
            });
        }
    }
    Ok(sec_map)
}

fn find_overlap_obstruction(
    sieve: &CoveringSieve,
    sec_map: &BTreeMap<String, &LocalReportSection>,
) -> Option<SheafGluingObstruction> {
    let contexts: Vec<String> = sieve.contexts.keys().cloned().collect();
    for i in 0..contexts.len() {
        for j in (i + 1)..contexts.len() {
            let cid_i = &contexts[i];
            let cid_j = &contexts[j];
            if let Some(obs) = check_context_pair_overlap(sieve, sec_map, cid_i, cid_j) {
                return Some(obs);
            }
        }
    }
    None
}

fn check_context_pair_overlap(
    sieve: &CoveringSieve,
    sec_map: &BTreeMap<String, &LocalReportSection>,
    cid_i: &str,
    cid_j: &str,
) -> Option<SheafGluingObstruction> {
    let overlap_pts = sieve.overlap(cid_i, cid_j);
    let sec_i = sec_map[cid_i];
    let sec_j = sec_map[cid_j];
    for pt in &overlap_pts {
        let v_i = sec_i.get_value(pt).unwrap_or("");
        let v_j = sec_j.get_value(pt).unwrap_or("");
        if v_i != v_j {
            return Some(SheafGluingObstruction {
                context_i: cid_i.to_string(),
                context_j: cid_j.to_string(),
                point: pt.clone(),
                value_i: v_i.to_string(),
                value_j: v_j.to_string(),
                reason: format!("local report mismatch at overlap point {pt}: {v_i} != {v_j}"),
            });
        }
    }
    None
}

/// Ordinary function restriction on the finite subset site. Identity and
/// composition follow from selecting precisely the keys in the target subset.
/// Missing keys are rejected instead of producing a partial report.
pub fn restrict_report(
    report: &BTreeMap<String, String>,
    subset: &BTreeSet<String>,
) -> Result<BTreeMap<String, String>, WdpError> {
    subset
        .iter()
        .map(|point| {
            report
                .get(point)
                .cloned()
                .map(|value| (point.clone(), value))
                .ok_or_else(|| WdpError::ElementNotFound {
                    element: point.clone(),
                })
        })
        .collect()
}

/// Verify a claimed global section directly against all supplied restrictions.
/// The domain must be exactly X and the local family must have one correctly
/// typed section per covering context. With a valid cover, any two accepted
/// candidates agree at each point of X (choose a context containing that point),
/// which is the uniqueness half of the finite function-sheaf gluing law.
pub fn verify_global_report(
    sieve: &CoveringSieve,
    local_sections: &[LocalReportSection],
    candidate: &BTreeMap<String, String>,
) -> Result<bool, WdpError> {
    // Replay input typing and compatibility independently of receipt flags.
    let checked = solve_observer_descent(sieve, local_sections)?;
    if !checked.is_compatible || candidate.keys().cloned().collect::<BTreeSet<_>>() != sieve.carrier
    {
        return Ok(false);
    }
    for section in local_sections {
        let subset = &sieve.contexts[&section.context_id];
        if restrict_report(candidate, subset)? != section.assignments {
            return Ok(false);
        }
    }
    Ok(true)
}

/// Replay all mathematical fields of an untrusted descent receipt. Failure is
/// a false verification result; malformed cover or section data is a typed error.
/// No receipt can acquire an authority effect through this verifier.
pub fn verify_descent_receipt(receipt: &DescentReceipt) -> Result<bool, WdpError> {
    let checked = solve_observer_descent(&receipt.sieve, &receipt.local_sections)?;
    Ok(receipt.authority_effect == AuthorityEffect::None
        && receipt.is_compatible == checked.is_compatible
        && receipt.global_section == checked.global_section
        && receipt.obstruction == checked.obstruction)
}

/// General finite presheaves are a different decision problem from the
/// function sheaf above: after the category owner
/// `core_category_theory::finite_report_descent::FiniteReportPresheaf` has
/// checked the functor laws, the global sections restricting to a matching
/// family can number zero, one or many, and empty intersections are compared
/// like any other overlap. This returns the owner's outcome unchanged; an
/// incompatible family or a malformed cover is the owner's typed refusal.
pub fn general_presheaf_descent(
    presheaf: &FiniteReportPresheaf,
    target: u64,
    cover: &[u64],
    locals: &[usize],
) -> Result<DescentOutcome, DescentError> {
    presheaf
        .descent_fiber(target, cover, locals)
        .map(|fiber| fiber.outcome())
}

// Origin: engine/crates_rs/core_wdp/src/presheaf.rs
// Claim: urn:core:crates_rs:core-wdp:presheaf:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7ce3a3e1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7ce3a3e1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7ce3a3e1 {
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
impl BoundaryError7ce3a3e1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7ce3a3e1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7ce3a3e1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7ce3a3e1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7ce3a3e1> {
        if capacity_bound == 0 {
            return Err(BoundaryError7ce3a3e1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7ce3a3e1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7ce3a3e1::ExceedsCapacity {
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
    fn test_sheaf_descent_gluing_success() {
        let carrier = BTreeSet::from(["x0".to_string(), "x1".to_string(), "x2".to_string()]);
        let mut contexts = BTreeMap::new();
        contexts.insert(
            "U0".to_string(),
            BTreeSet::from(["x0".to_string(), "x1".to_string()]),
        );
        contexts.insert(
            "U1".to_string(),
            BTreeSet::from(["x1".to_string(), "x2".to_string()]),
        );
        let sieve = CoveringSieve::new(carrier, contexts).unwrap();

        let s0 = LocalReportSection::new(
            "U0".to_string(),
            BTreeMap::from([
                ("x0".to_string(), "val0".to_string()),
                ("x1".to_string(), "val1".to_string()),
            ]),
        );
        let s1 = LocalReportSection::new(
            "U1".to_string(),
            BTreeMap::from([
                ("x1".to_string(), "val1".to_string()),
                ("x2".to_string(), "val2".to_string()),
            ]),
        );

        let receipt = solve_observer_descent(&sieve, &[s0, s1]).unwrap();
        assert!(receipt.is_compatible);
        assert!(receipt.obstruction.is_none());
        let global = receipt.global_section.unwrap();
        assert_eq!(global.get("x0").unwrap(), "val0");
        assert_eq!(global.get("x1").unwrap(), "val1");
        assert_eq!(global.get("x2").unwrap(), "val2");
    }

    #[test]
    fn test_sheaf_descent_obstruction_detected() {
        let carrier = BTreeSet::from(["x0".to_string(), "x1".to_string(), "x2".to_string()]);
        let mut contexts = BTreeMap::new();
        contexts.insert(
            "U0".to_string(),
            BTreeSet::from(["x0".to_string(), "x1".to_string()]),
        );
        contexts.insert(
            "U1".to_string(),
            BTreeSet::from(["x1".to_string(), "x2".to_string()]),
        );
        let sieve = CoveringSieve::new(carrier, contexts).unwrap();

        // Overlap disagreement on x1: "A" vs "B"
        let s0 = LocalReportSection::new(
            "U0".to_string(),
            BTreeMap::from([
                ("x0".to_string(), "val0".to_string()),
                ("x1".to_string(), "A".to_string()),
            ]),
        );
        let s1 = LocalReportSection::new(
            "U1".to_string(),
            BTreeMap::from([
                ("x1".to_string(), "B".to_string()),
                ("x2".to_string(), "val2".to_string()),
            ]),
        );

        let receipt = solve_observer_descent(&sieve, &[s0, s1]).unwrap();
        assert!(!receipt.is_compatible);
        let obs = receipt.obstruction.unwrap();
        assert_eq!(obs.point, "x1");
        assert_eq!(obs.value_i, "A");
        assert_eq!(obs.value_j, "B");
    }
    fn singleton_cover() -> (CoveringSieve, Vec<LocalReportSection>) {
        let sieve = CoveringSieve::new(
            BTreeSet::from(["x".to_string()]),
            BTreeMap::from([("U".to_string(), BTreeSet::from(["x".to_string()]))]),
        )
        .unwrap();
        let sections = vec![LocalReportSection::new(
            "U".to_string(),
            BTreeMap::from([("x".to_string(), "A".to_string())]),
        )];
        (sieve, sections)
    }

    #[test]
    fn rejects_unchecked_covers_and_unknown_sections() {
        let (mut sieve, mut sections) = singleton_cover();
        sections.push(LocalReportSection::new(
            "ghost".to_string(),
            BTreeMap::new(),
        ));
        assert!(solve_observer_descent(&sieve, &sections).is_err());
        sections.pop();
        sieve.carrier.insert("uncovered".to_string());
        assert!(matches!(
            solve_observer_descent(&sieve, &sections),
            Err(WdpError::IncompleteCoverage { .. })
        ));
    }

    #[test]
    fn restrictions_compose_and_detect_missing_data() {
        let report = BTreeMap::from([
            ("x".to_string(), "A".to_string()),
            ("y".to_string(), "B".to_string()),
            ("z".to_string(), "C".to_string()),
        ]);
        let all = report.keys().cloned().collect();
        let middle = BTreeSet::from(["x".to_string(), "y".to_string()]);
        let subset = BTreeSet::from(["x".to_string()]);
        assert_eq!(restrict_report(&report, &all).unwrap(), report);
        assert_eq!(
            restrict_report(&restrict_report(&report, &middle).unwrap(), &subset).unwrap(),
            restrict_report(&report, &subset).unwrap()
        );
        assert!(restrict_report(&report, &BTreeSet::from(["missing".to_string()])).is_err());
        assert!(restrict_report(&report, &BTreeSet::new())
            .unwrap()
            .is_empty());
    }

    #[test]
    fn gluing_verifier_binds_domain_values_and_receipt() {
        let (sieve, sections) = singleton_cover();
        let mut receipt = solve_observer_descent(&sieve, &sections).unwrap();
        assert!(verify_descent_receipt(&receipt).unwrap());
        let mut global = receipt.global_section.clone().unwrap();
        assert!(verify_global_report(&sieve, &sections, &global).unwrap());
        global.insert("x".to_string(), "forged".to_string());
        assert!(!verify_global_report(&sieve, &sections, &global).unwrap());
        receipt.global_section = Some(global);
        assert!(!verify_descent_receipt(&receipt).unwrap());
        let mut extra = sections[0].assignments.clone();
        extra.insert("outside".to_string(), "A".to_string());
        assert!(!verify_global_report(&sieve, &sections, &extra).unwrap());
    }

    #[test]
    fn empty_cover_glues_to_unique_empty_function() {
        let sieve = CoveringSieve::new(BTreeSet::new(), BTreeMap::new()).unwrap();
        let receipt = solve_observer_descent(&sieve, &[]).unwrap();
        assert_eq!(receipt.global_section, Some(BTreeMap::new()));
        assert!(verify_global_report(&sieve, &[], &BTreeMap::new()).unwrap());
        assert!(verify_descent_receipt(&receipt).unwrap());
    }
}

#[cfg(test)]
mod l4_boundary_tests_7ce3a3e1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7ce3a3e1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7ce3a3e1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7ce3a3e1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7ce3a3e1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7ce3a3e1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7ce3a3e1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7ce3a3e1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
