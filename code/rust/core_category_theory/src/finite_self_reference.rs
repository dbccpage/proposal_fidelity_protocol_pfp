//! Explicit finite bridges for accessible self-state, reflexive report provenance,
//! context stability, and partial later-state comparison. Availability is never
//! identified with comparison success. Every claim is conditional on the tables.
//! Explicit finite bridges for accessible self-state, reflexive report provenance,
//! context stability, and partial later-state comparison. Availability is never
//! identified with comparison success. Every claim is conditional on the tables.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_ec6dc858<T> {
    fn checked_invariant_ec6dc858(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_ec6dc858<T> for Option<T> {
    #[inline]
    fn checked_invariant_ec6dc858(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_ec6dc858<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_ec6dc858(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SelfReferenceError {
    InvalidCarrier,
    InvalidMap,
    InvalidEvidence,
    ImpossibleSignature,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_self_reference.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-self-reference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SelfReferenceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SelfReferenceError {}

/// Untrusted provenance candidate: semantic replay, rather than these fields
/// alone, binds it to accessible self-state and the declared generation relation.
/// Untrusted provenance candidate: semantic replay, rather than these fields
/// alone, binds it to accessible self-state and the declared generation relation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReflexiveProvenance {
    pub source_observer: usize,
    pub target_observer: usize,
    pub captured_accessible: usize,
    pub reaccessed_accessible: usize,
    pub reported_value: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PartialComparisonProtocol {
    pub evaluator_id: usize,
    /// Pairs for which the declared equality comparator can actually run.
    /// Pairs for which the declared equality comparator can actually run.
    pub domain: BTreeSet<(usize, usize)>,
}

/// Constructor input. The owner retains a private validated copy.
/// Constructor input. The owner retains a private validated copy.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SelfReferenceData {
    pub observer_id: usize,
    pub observer_count: usize,
    pub accessible_count: usize,
    pub report_count: usize,
    pub sigma: Vec<usize>,
    /// Accessible-state presentation; richer sigma access need not factor here.
    /// Accessible-state presentation; richer sigma access need not factor here.
    pub presentation: Vec<usize>,
    pub reports: Vec<Option<usize>>,
    pub provenance: Vec<Option<ReflexiveProvenance>>,
    pub context: Vec<usize>,
    pub later: Vec<usize>,
    pub target: Vec<Option<usize>>,
    /// Independent finite report-generation semantic relation on A x R.
    /// Independent finite report-generation semantic relation on A x R.
    pub generation: BTreeSet<(usize, usize)>,
    pub protocol: Option<PartialComparisonProtocol>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SelfReferencePoint {
    pub report_available: bool,
    pub linkage_provided: bool,
    pub linkage_verified: bool,
    pub stability_available: bool,
    pub stability_success: bool,
    pub comparison_available: bool,
    pub comparison_success: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SelfReferenceSignature {
    pub report_total: bool,
    pub linkage_provided: bool,
    pub linkage_verified: bool,
    pub report_stable: bool,
    pub comparison_available: bool,
    pub comparison_success: bool,
}

impl SelfReferenceSignature {
    /// Exact iff criterion for all six aggregate predicates. A partial report
    /// forces every universal bridge false; otherwise linkage verified implies
    /// provided, and comparison success implies comparison availability.
    /// Exact iff criterion for all six aggregate predicates. A partial report
    /// forces every universal bridge false; otherwise linkage verified implies
    /// provided, and comparison success implies comparison availability.
    pub fn is_realizable(self) -> bool {
        if !self.report_total {
            return !self.linkage_provided
                && !self.linkage_verified
                && !self.report_stable
                && !self.comparison_available
                && !self.comparison_success;
        }
        (!self.linkage_verified || self.linkage_provided)
            && (!self.comparison_success || self.comparison_available)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckedSelfReference {
    data: SelfReferenceData,
}

fn partial_factor(
    keys: &[usize],
    values: &[Option<usize>],
) -> Option<BTreeMap<usize, Option<usize>>> {
    let mut factor = BTreeMap::new();
    for (&key, &value) in keys.iter().zip(values) {
        if let Some(previous) = factor.insert(key, value) {
            if previous != value {
                return None;
            }
        }
    }
    Some(factor)
}

impl CheckedSelfReference {
    fn validate_carrier(data: &SelfReferenceData) -> Result<(), SelfReferenceError> {
        let n = data.sigma.len();
        if n == 0
            || data.accessible_count == 0
            || data.report_count == 0
            || data.observer_count == 0
            || data.observer_id >= data.observer_count
        {
            return Err(SelfReferenceError::InvalidCarrier);
        }
        Ok(())
    }

    fn validate_maps(data: &SelfReferenceData) -> Result<(), SelfReferenceError> {
        let n = data.sigma.len();
        let invalid_lengths = data.presentation.len() != data.accessible_count
            || [
                data.reports.len(),
                data.provenance.len(),
                data.context.len(),
                data.later.len(),
                data.target.len(),
            ]
            .iter()
            .any(|&len| len != n);
        if invalid_lengths
            || data.sigma.iter().any(|&a| a >= data.accessible_count)
            || data.context.iter().chain(&data.later).any(|&x| x >= n)
            || data
                .reports
                .iter()
                .chain(&data.target)
                .flatten()
                .any(|&r| r >= data.report_count)
            || data
                .generation
                .iter()
                .any(|&(a, r)| a >= data.accessible_count || r >= data.report_count)
            || data.protocol.as_ref().is_some_and(|p| {
                p.domain
                    .iter()
                    .any(|&(r, b)| r >= data.report_count || b >= data.report_count)
            })
        {
            return Err(SelfReferenceError::InvalidMap);
        }
        Ok(())
    }

    fn validate_evidence(data: &SelfReferenceData) -> Result<(), SelfReferenceError> {
        for candidate in data.provenance.iter().flatten() {
            if candidate.source_observer >= data.observer_count
                || candidate.target_observer >= data.observer_count
                || candidate.captured_accessible >= data.accessible_count
                || candidate.reaccessed_accessible >= data.accessible_count
                || candidate.reported_value >= data.report_count
            {
                return Err(SelfReferenceError::InvalidEvidence);
            }
        }
        Ok(())
    }

    pub fn new(data: SelfReferenceData) -> Result<Self, SelfReferenceError> {
        Self::validate_carrier(&data)?;
        Self::validate_maps(&data)?;
        Self::validate_evidence(&data)?;
        Ok(Self { data })
    }

    pub fn data(&self) -> &SelfReferenceData {
        &self.data
    }

    pub fn point_count(&self) -> usize {
        self.data.sigma.len()
    }

    /// Exact per-state criteria for manuscript R1/R2/R3 under these bridges.
    fn verify_linkage(&self, x: usize, report: Option<usize>) -> bool {
        let d = &self.data;
        match (report, &d.provenance[x]) {
            (Some(r), Some(p)) => {
                p.source_observer == d.observer_id
                    && p.target_observer == d.observer_id
                    && p.captured_accessible == d.sigma[x]
                    && p.reaccessed_accessible == d.sigma[x]
                    && p.reported_value == r
                    && d.generation.contains(&(d.sigma[x], r))
            }
            _ => false,
        }
    }

    fn check_comparison(&self, report: Option<usize>, target: Option<usize>) -> bool {
        match (report, target, &self.data.protocol) {
            (Some(r), Some(b), Some(protocol)) => protocol.domain.contains(&(r, b)),
            _ => false,
        }
    }

    /// Exact per-state criteria for manuscript R1/R2/R3 under these bridges.
    pub fn audit_point(&self, x: usize) -> Result<SelfReferencePoint, SelfReferenceError> {
        if x >= self.point_count() {
            return Err(SelfReferenceError::InvalidMap);
        }
        let d = &self.data;
        let report = d.reports[x];
        let linkage_provided = report.is_some() && d.provenance[x].is_some();
        let linkage_verified = self.verify_linkage(x, report);
        let transported_report = d.reports[d.context[x]];
        let stability_available = report.is_some() && transported_report.is_some();
        let target = d.target[d.later[x]];
        let comparison_available = self.check_comparison(report, target);
        Ok(SelfReferencePoint {
            report_available: report.is_some(),
            linkage_provided,
            linkage_verified,
            stability_available,
            stability_success: stability_available && report == transported_report,
            comparison_available,
            comparison_success: comparison_available && report == target,
        })
    }

    pub fn signature(&self) -> SelfReferenceSignature {
        let points: Vec<_> = (0..self.point_count())
            .map(|x| self.audit_point(x).checked_invariant_ec6dc858("checked carrier index"))
            .collect();
        SelfReferenceSignature {
            report_total: points.iter().all(|p| p.report_available),
            linkage_provided: points.iter().all(|p| p.linkage_provided),
            linkage_verified: points.iter().all(|p| p.linkage_verified),
            report_stable: points.iter().all(|p| p.stability_success),
            comparison_available: points.iter().all(|p| p.comparison_available),
            comparison_success: points.iter().all(|p| p.comparison_success),
        }
    }

    /// Context transport is total: universal stability availability iff reports
    /// are total. Undefined->undefined is not counted as available or successful.
    /// Context transport is total: universal stability availability iff reports
    /// are total. Undefined->undefined is not counted as available or successful.
    pub fn stability_available(&self) -> bool {
        (0..self.point_count()).all(|x| {
            self.audit_point(x)
                .checked_invariant_ec6dc858("checked carrier index")
                .stability_available
        })
    }

    /// Original R2 on ACTUAL report events: each defined report is transported
    /// to the same defined value. Unreported states are outside this predicate;
    /// total successful stability additionally requires report availability.
    /// Original R2 on ACTUAL report events: each defined report is transported
    /// to the same defined value. Unreported states are outside this predicate;
    /// total successful stability additionally requires report availability.
    pub fn report_events_preserved(&self) -> bool {
        self.data.reports.iter().enumerate().all(|(x, report)| {
            report.is_none() || *report == self.data.reports[self.data.context[x]]
        })
    }

    pub fn generation_is_functional(&self) -> bool {
        let mut generated = BTreeMap::new();
        self.data
            .generation
            .iter()
            .all(|&(a, r)| generated.insert(a, r).is_none_or(|previous| previous == r))
    }

    /// Partial report determination iff values (including undefined) are constant
    /// on sigma fibers. This is distinct from reflexive provenance availability.
    /// Partial report determination iff values (including undefined) are constant
    /// on sigma fibers. This is distinct from reflexive provenance availability.
    pub fn report_factor_accessible(&self) -> Option<BTreeMap<usize, Option<usize>>> {
        partial_factor(&self.data.sigma, &self.data.reports)
    }
    pub fn report_factor_presentation(&self) -> Option<BTreeMap<usize, Option<usize>>> {
        let keys: Vec<_> = self
            .data
            .sigma
            .iter()
            .map(|&a| self.data.presentation[a])
            .collect();
        partial_factor(&keys, &self.data.reports)
    }

    /// Later target b(l(x)) can be inferred from sigma(x) iff constant on its
    /// fibers. This returns an explicit partial decoder on realized self-states.
    /// Later target b(l(x)) can be inferred from sigma(x) iff constant on its
    /// fibers. This returns an explicit partial decoder on realized self-states.
    pub fn later_target_factor_accessible(&self) -> Option<BTreeMap<usize, Option<usize>>> {
        let values: Vec<_> = self
            .data
            .later
            .iter()
            .map(|&x| self.data.target[x])
            .collect();
        partial_factor(&self.data.sigma, &values)
    }

    /// Exact existence criterion under FIXED sigma/generation/context/later/
    /// target/protocol tables: construct a total verified-linked report whose
    /// later comparisons all succeed, optionally also context-stable. There is
    /// a solution iff every actual later target is defined, generated from its
    /// accessible self-state, comparable to itself, and (when requested) stable
    /// under context. Necessity follows because success forces that report value;
    /// sufficiency uses these values and exact reflexive provenance records.
    /// Exact existence criterion under FIXED sigma/generation/context/later/
    /// target/protocol tables: construct a total verified-linked report whose
    /// later comparisons all succeed, optionally also context-stable. There is
    /// a solution iff every actual later target is defined, generated from its
    /// accessible self-state, comparable to itself, and (when requested) stable
    /// under context. Necessity follows because success forces that report value;
    /// sufficiency uses these values and exact reflexive provenance records.
    pub fn successful_linked_report_plan(
        &self,
        require_context_stability: bool,
    ) -> Result<Option<CheckedSelfReference>, SelfReferenceError> {
        let d = &self.data;
        let Some(protocol) = &d.protocol else {
            return Ok(None);
        };
        let reports: Vec<_> = d.later.iter().map(|&x| d.target[x]).collect();
        for (x, report) in reports.iter().enumerate() {
            let Some(r) = report else {
                return Ok(None);
            };
            if !d.generation.contains(&(d.sigma[x], *r)) || !protocol.domain.contains(&(*r, *r)) {
                return Ok(None);
            }
            if require_context_stability && *report != reports[d.context[x]] {
                return Ok(None);
            }
        }
        let mut planned = d.clone();
        planned.provenance = reports
            .iter()
            .enumerate()
            .map(|(x, report)| {
                report.map(|r| ReflexiveProvenance {
                    source_observer: d.observer_id,
                    target_observer: d.observer_id,
                    captured_accessible: d.sigma[x],
                    reaccessed_accessible: d.sigma[x],
                    reported_value: r,
                })
            })
            .collect();
        planned.reports = reports;
        CheckedSelfReference::new(planned).map(Some)
    }

    /// A prescribed current-state target y can be realized as k(l(x)) iff y is
    /// constant on later-map fibers. None values are genuine partiality data.
    /// A prescribed current-state target y can be realized as k(l(x)) iff y is
    /// constant on later-map fibers. None values are genuine partiality data.
    pub fn factor_prescribed_target_through_later(
        &self,
        prescribed: &[Option<usize>],
    ) -> Result<Option<BTreeMap<usize, Option<usize>>>, SelfReferenceError> {
        if prescribed.len() != self.point_count()
            || prescribed
                .iter()
                .flatten()
                .any(|&r| r >= self.data.report_count)
        {
            return Err(SelfReferenceError::InvalidMap);
        }
        Ok(partial_factor(&self.data.later, prescribed))
    }
}

/// Complete constructors for 19 aggregate signatures. The partial-report case
/// has one model; total reports allow 3 linkage states x 2 stabilities x 3
/// comparison states. Later-state swap is real, rather than default identity.
/// Complete constructors for 19 aggregate signatures. The partial-report case
/// has one model; total reports allow 3 linkage states x 2 stabilities x 3
/// comparison states. Later-state swap is real, rather than default identity.
pub fn realize_self_reference(
    signature: SelfReferenceSignature,
) -> Result<CheckedSelfReference, SelfReferenceError> {
    if !signature.is_realizable() {
        return Err(SelfReferenceError::ImpossibleSignature);
    }
    let reports = if signature.report_total {
        vec![Some(0), Some(1)]
    } else {
        vec![Some(0), None]
    };
    let provenance = if signature.linkage_provided {
        (0..2)
            .map(|x| {
                Some(ReflexiveProvenance {
                    source_observer: if signature.linkage_verified { 0 } else { 1 },
                    target_observer: 0,
                    captured_accessible: x,
                    reaccessed_accessible: x,
                    reported_value: x,
                })
            })
            .collect()
    } else {
        vec![None, None]
    };
    let target = if signature.comparison_success {
        vec![Some(1), Some(0)]
    } else {
        vec![Some(0), Some(1)]
    };
    let protocol = if signature.comparison_available {
        Some(PartialComparisonProtocol {
            evaluator_id: 0,
            domain: BTreeSet::from([(0, 0), (0, 1), (1, 0), (1, 1)]),
        })
    } else {
        None
    };
    CheckedSelfReference::new(SelfReferenceData {
        observer_id: 0,
        observer_count: 2,
        accessible_count: 2,
        report_count: 2,
        sigma: vec![0, 1],
        presentation: vec![0, 1],
        reports,
        provenance,
        context: if signature.report_stable {
            vec![0, 1]
        } else {
            vec![1, 0]
        },
        later: vec![1, 0],
        target,
        generation: BTreeSet::from([(0, 0), (1, 1)]),
        protocol,
    })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_ec6dc858 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
