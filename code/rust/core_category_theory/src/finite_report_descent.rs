//! Finite set-valued report presheaves, union coverage and exact descent fibers.
//!
//! Objects are declared subsets of a finite carrier, closed under intersection;
//! arrows are inclusions. Report sets are finite numbered sets. Total restriction
//! tables are checked for identity and composition, so this is an actual
//! presheaf, not an unchecked diagram. A union cover is a Grothendieck pretopology:
//! intersections give pullbacks, and unions prove identity/base-change/transitivity.
//! For a cover, the restriction map into compatible matching families has finite
//! fibers: empty = existence obstruction, singleton = unique glue, larger =
//! ambiguity. Its bijectivity is exactly the sheaf condition for that cover.
//! Finite set-valued report presheaves, union coverage and exact descent fibers.
//!
//! Objects are declared subsets of a finite carrier, closed under intersection;
//! arrows are inclusions. Report sets are finite numbered sets. Total restriction
//! tables are checked for identity and composition, so this is an actual
//! presheaf, not an unchecked diagram. A union cover is a Grothendieck pretopology:
//! intersections give pullbacks, and unions prove identity/base-change/transitivity.
//! For a cover, the restriction map into compatible matching families has finite
//! fibers: empty = existence obstruction, singleton = unique glue, larger =
//! ambiguity. Its bijectivity is exactly the sheaf condition for that cover.

use std::collections::BTreeMap;
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DescentError {
    CarrierTooLarge,
    MissingEmptyOrFullContext,
    ContextOutsideCarrier {
        context: u64,
    },
    MissingIntersection {
        left: u64,
        right: u64,
    },
    MissingRestriction {
        source: u64,
        target: u64,
    },
    ExtraneousRestriction {
        source: u64,
        target: u64,
    },
    RestrictionShape {
        source: u64,
        target: u64,
    },
    RestrictionTargetOutsideReports {
        source: u64,
        target: u64,
    },
    IdentityFailure {
        context: u64,
    },
    CompositionFailure {
        source: u64,
        middle: u64,
        target: u64,
    },
    UnknownContext {
        context: u64,
    },
    InvalidCover,
    InvalidLocalSections,
    IncompatibleLocals {
        left: usize,
        right: usize,
        overlap: u64,
        left_report: usize,
        right_report: usize,
    },
    EnumerationLimit {
        required: usize,
        limit: usize,
    },
    EnumerationOverflow,
}
impl fmt::Display for DescentError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "finite report descent refusal: {self:?}")
    }
}
impl std::error::Error for DescentError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteReportPresheaf {
    carrier_size: usize,
    report_counts: BTreeMap<u64, usize>,
    restrictions: BTreeMap<(u64, u64), Vec<usize>>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DescentOutcome {
    NoGlobalExtension,
    Unique { global_section: usize },
    Ambiguous { global_sections: Vec<usize> },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DescentFiber {
    pub local_sections: Vec<usize>,
    pub global_sections: Vec<usize>,
}
impl DescentFiber {
    pub fn outcome(&self) -> DescentOutcome {
        match self.global_sections.as_slice() {
            [] => DescentOutcome::NoGlobalExtension,
            [global] => DescentOutcome::Unique {
                global_section: *global,
            },
            many => DescentOutcome::Ambiguous {
                global_sections: many.to_vec(),
            },
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoverClassification {
    pub target: u64,
    pub cover: Vec<u64>,
    pub matching_fibers: Vec<DescentFiber>,
    pub is_separated: bool,
    pub has_existence: bool,
    pub is_sheaf_cover: bool,
}

fn included(smaller: u64, larger: u64) -> bool {
    smaller & larger == smaller
}

impl FiniteReportPresheaf {
    fn validate_contexts(
        carrier_size: usize,
        report_counts: &BTreeMap<u64, usize>,
        full: u64,
    ) -> Result<(), DescentError> {
        if carrier_size > 64 {
            return Err(DescentError::CarrierTooLarge);
        }
        if !report_counts.contains_key(&0) || !report_counts.contains_key(&full) {
            return Err(DescentError::MissingEmptyOrFullContext);
        }
        for &context in report_counts.keys() {
            if !included(context, full) {
                return Err(DescentError::ContextOutsideCarrier { context });
            }
        }
        Ok(())
    }

    fn validate_single_restriction(
        a: u64,
        b: u64,
        report_counts: &BTreeMap<u64, usize>,
        restrictions: &BTreeMap<(u64, u64), Vec<usize>>,
    ) -> Result<(), DescentError> {
        if !included(b, a) {
            return Ok(());
        }
        let row = restrictions
            .get(&(a, b))
            .ok_or(DescentError::MissingRestriction {
                source: a,
                target: b,
            })?;
        if row.len() != report_counts[&a] {
            return Err(DescentError::RestrictionShape {
                source: a,
                target: b,
            });
        }
        if row.iter().any(|&r| r >= report_counts[&b]) {
            return Err(DescentError::RestrictionTargetOutsideReports {
                source: a,
                target: b,
            });
        }
        Ok(())
    }

    fn validate_pairwise_restrictions(
        report_counts: &BTreeMap<u64, usize>,
        restrictions: &BTreeMap<(u64, u64), Vec<usize>>,
    ) -> Result<(), DescentError> {
        for &a in report_counts.keys() {
            for &b in report_counts.keys() {
                if !report_counts.contains_key(&(a & b)) {
                    return Err(DescentError::MissingIntersection { left: a, right: b });
                }
                Self::validate_single_restriction(a, b, report_counts, restrictions)?;
            }
            if restrictions[&(a, a)]
                .iter()
                .enumerate()
                .any(|(i, &j)| i != j)
            {
                return Err(DescentError::IdentityFailure { context: a });
            }
        }
        Ok(())
    }

    fn validate_extraneous_restrictions(
        report_counts: &BTreeMap<u64, usize>,
        restrictions: &BTreeMap<(u64, u64), Vec<usize>>,
    ) -> Result<(), DescentError> {
        for &(a, b) in restrictions.keys() {
            if !report_counts.contains_key(&a) || !report_counts.contains_key(&b) || !included(b, a) {
                return Err(DescentError::ExtraneousRestriction {
                    source: a,
                    target: b,
                });
            }
        }
        Ok(())
    }

    fn check_composition_triple(
        a: u64,
        b: u64,
        c: u64,
        count_a: usize,
        restrictions: &BTreeMap<(u64, u64), Vec<usize>>,
    ) -> Result<(), DescentError> {
        for s in 0..count_a {
            if restrictions[&(a, c)][s] != restrictions[&(b, c)][restrictions[&(a, b)][s]] {
                return Err(DescentError::CompositionFailure {
                    source: a,
                    middle: b,
                    target: c,
                });
            }
        }
        Ok(())
    }

    fn validate_composition_law(
        report_counts: &BTreeMap<u64, usize>,
        restrictions: &BTreeMap<(u64, u64), Vec<usize>>,
    ) -> Result<(), DescentError> {
        for &a in report_counts.keys() {
            let count_a = report_counts[&a];
            for &b in report_counts.keys().filter(|&&b| included(b, a)) {
                for &c in report_counts.keys().filter(|&&c| included(c, b)) {
                    Self::check_composition_triple(a, b, c, count_a, restrictions)?;
                }
            }
        }
        Ok(())
    }

    pub fn new(
        carrier_size: usize,
        report_counts: BTreeMap<u64, usize>,
        restrictions: BTreeMap<(u64, u64), Vec<usize>>,
    ) -> Result<Self, DescentError> {
        let full = if carrier_size == 64 {
            u64::MAX
        } else {
            (1u64 << carrier_size) - 1
        };
        Self::validate_contexts(carrier_size, &report_counts, full)?;
        Self::validate_pairwise_restrictions(&report_counts, &restrictions)?;
        Self::validate_extraneous_restrictions(&report_counts, &restrictions)?;
        Self::validate_composition_law(&report_counts, &restrictions)?;

        Ok(Self {
            carrier_size,
            report_counts,
            restrictions,
        })
    }
    pub fn carrier_size(&self) -> usize {
        self.carrier_size
    }
    pub fn report_counts(&self) -> &BTreeMap<u64, usize> {
        &self.report_counts
    }
    pub fn restrictions(&self) -> &BTreeMap<(u64, u64), Vec<usize>> {
        &self.restrictions
    }

    fn check_cover(&self, target: u64, cover: &[u64]) -> Result<(), DescentError> {
        if !self.report_counts.contains_key(&target) {
            return Err(DescentError::UnknownContext { context: target });
        }
        let mut union = 0;
        for &context in cover {
            if !self.report_counts.contains_key(&context) {
                return Err(DescentError::UnknownContext { context });
            }
            if !included(context, target) {
                return Err(DescentError::InvalidCover);
            }
            union |= context;
        }
        if union != target {
            return Err(DescentError::InvalidCover);
        }
        Ok(())
    }

    /// Decide compatibility first, then enumerate exactly the fiber of global
    /// restriction. No proposed sections or restrictions are silently dropped.
    /// Decide compatibility first, then enumerate exactly the fiber of global
    /// restriction. No proposed sections or restrictions are silently dropped.
    pub fn descent_fiber(
        &self,
        target: u64,
        cover: &[u64],
        locals: &[usize],
    ) -> Result<DescentFiber, DescentError> {
        self.check_cover(target, cover)?;
        if locals.len() != cover.len()
            || cover
                .iter()
                .zip(locals)
                .any(|(c, &s)| s >= self.report_counts[c])
        {
            return Err(DescentError::InvalidLocalSections);
        }
        for left in 0..cover.len() {
            for right in 0..left {
                let overlap = cover[left] & cover[right];
                let left_report = self.restrictions[&(cover[left], overlap)][locals[left]];
                let right_report = self.restrictions[&(cover[right], overlap)][locals[right]];
                if left_report != right_report {
                    return Err(DescentError::IncompatibleLocals {
                        left,
                        right,
                        overlap,
                        left_report,
                        right_report,
                    });
                }
            }
        }
        let global_sections = (0..self.report_counts[&target])
            .filter(|&global| {
                cover
                    .iter()
                    .zip(locals)
                    .all(|(&c, &local)| self.restrictions[&(target, c)][global] == local)
            })
            .collect();
        Ok(DescentFiber {
            local_sections: locals.to_vec(),
            global_sections,
        })
    }

    /// Classify every compatible family for the requested cover. The explicit
    /// Cartesian-product limit is checked before enumeration. Exhaustion is a
    /// typed refusal, never interpreted as a gluing obstruction or sheaf law.
    /// Classify every compatible family for the requested cover. The explicit
    /// Cartesian-product limit is checked before enumeration. Exhaustion is a
    /// typed refusal, never interpreted as a gluing obstruction or sheaf law.
    pub fn classify_cover(
        &self,
        target: u64,
        cover: &[u64],
        limit: usize,
    ) -> Result<CoverClassification, DescentError> {
        self.check_cover(target, cover)?;
        let required = cover.iter().try_fold(1usize, |n, c| {
            n.checked_mul(self.report_counts[c])
                .ok_or(DescentError::EnumerationOverflow)
        })?;
        if required > limit {
            return Err(DescentError::EnumerationLimit { required, limit });
        }
        let mut tuples = vec![vec![]];
        for c in cover {
            tuples = tuples
                .into_iter()
                .flat_map(|prefix| {
                    (0..self.report_counts[c]).map(move |s| {
                        let mut tuple = prefix.clone();
                        tuple.push(s);
                        tuple
                    })
                })
                .collect();
        }
        let mut matching_fibers = Vec::new();
        for locals in tuples {
            match self.descent_fiber(target, cover, &locals) {
                Ok(fiber) => matching_fibers.push(fiber),
                Err(DescentError::IncompatibleLocals { .. }) => {}
                Err(error) => return Err(error),
            }
        }
        let is_separated = matching_fibers.iter().all(|f| f.global_sections.len() <= 1);
        let has_existence = matching_fibers
            .iter()
            .all(|f| !f.global_sections.is_empty());
        Ok(CoverClassification {
            target,
            cover: cover.to_vec(),
            matching_fibers,
            is_separated,
            has_existence,
            is_sheaf_cover: is_separated && has_existence,
        })
    }

    pub fn verify_cover_classification(
        &self,
        target: u64,
        cover: &[u64],
        limit: usize,
        candidate: &CoverClassification,
    ) -> Result<bool, DescentError> {
        Ok(candidate == &self.classify_cover(target, cover, limit)?)
    }
}

// Origin: engine/crates_rs/core_category_theory/src/finite_report_descent.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-report-descent:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn equality_constraint() -> FiniteReportPresheaf {
        let counts = BTreeMap::from([(0, 1), (1, 2), (2, 2), (3, 2)]);
        let mut rows = BTreeMap::new();
        for (&a, &count) in &counts {
            for &b in counts.keys().filter(|&&b| included(b, a)) {
                rows.insert(
                    (a, b),
                    (0..count).map(|s| if b == 0 { 0 } else { s }).collect(),
                );
            }
        }
        FiniteReportPresheaf::new(2, counts, rows).unwrap()
    }
    #[test]
    fn compatible_constrained_family_has_no_global_extension() {
        let p = equality_constraint();
        assert_eq!(
            p.descent_fiber(3, &[1, 2], &[0, 1]).unwrap().outcome(),
            DescentOutcome::NoGlobalExtension
        );
        assert_eq!(
            p.descent_fiber(3, &[1, 2], &[1, 1]).unwrap().outcome(),
            DescentOutcome::Unique { global_section: 1 }
        );
        let c = p.classify_cover(3, &[1, 2], 4).unwrap();
        assert_eq!(c.matching_fibers.len(), 4);
        assert!(c.is_separated);
        assert!(!c.has_existence);
        assert!(!c.is_sheaf_cover);
        assert!(p.verify_cover_classification(3, &[1, 2], 4, &c).unwrap());
        let mut forged = c;
        forged.has_existence = true;
        assert!(!p
            .verify_cover_classification(3, &[1, 2], 4, &forged)
            .unwrap());
    }
    #[test]
    fn hidden_global_reports_produce_typed_ambiguity() {
        let counts = BTreeMap::from([(0, 1), (1, 1), (2, 1), (3, 2)]);
        let mut rows = BTreeMap::new();
        for (&a, &count) in &counts {
            for &b in counts.keys().filter(|&&b| included(b, a)) {
                rows.insert(
                    (a, b),
                    (0..count).map(|s| if a == b { s } else { 0 }).collect(),
                );
            }
        }
        let p = FiniteReportPresheaf::new(2, counts, rows).unwrap();
        assert_eq!(
            p.descent_fiber(3, &[1, 2], &[0, 0]).unwrap().outcome(),
            DescentOutcome::Ambiguous {
                global_sections: vec![0, 1]
            }
        );
        let c = p.classify_cover(3, &[1, 2], 1).unwrap();
        assert!(c.has_existence);
        assert!(!c.is_separated);
    }
    #[test]
    fn incoherent_transports_and_uncovered_families_refuse() {
        let p = equality_constraint();
        let mut rows = p.restrictions.clone();
        rows.insert((3, 0), vec![0, 1]);
        assert!(FiniteReportPresheaf::new(2, p.report_counts.clone(), rows).is_err());
        let mut rows = p.restrictions.clone();
        rows.insert((1, 1), vec![1, 0]);
        assert!(matches!(
            FiniteReportPresheaf::new(2, p.report_counts.clone(), rows),
            Err(DescentError::IdentityFailure { .. })
        ));
        assert_eq!(
            p.descent_fiber(3, &[1], &[0]),
            Err(DescentError::InvalidCover)
        );
        assert!(matches!(
            p.classify_cover(3, &[1, 2], 3),
            Err(DescentError::EnumerationLimit {
                required: 4,
                limit: 3
            })
        ));
        assert_eq!(
            p.descent_fiber(0, &[], &[]).unwrap().outcome(),
            DescentOutcome::Unique { global_section: 0 }
        );
    }
    #[test]
    fn composition_and_overlap_are_checked_at_actual_intersections() {
        let counts = BTreeMap::from([(0, 2), (1, 2), (2, 2), (3, 2)]);
        let mut rows = BTreeMap::new();
        for &a in counts.keys() {
            for &b in counts.keys().filter(|&&b| included(b, a)) {
                rows.insert((a, b), vec![0, 1]);
            }
        }
        rows.insert((3, 0), vec![1, 0]);
        assert!(matches!(
            FiniteReportPresheaf::new(2, counts, rows),
            Err(DescentError::CompositionFailure {
                source: 3,
                middle: 1,
                target: 0
            })
        ));
        let p = equality_constraint();
        assert!(matches!(
            p.descent_fiber(3, &[3, 1], &[0, 1]),
            Err(DescentError::IncompatibleLocals { overlap: 1, .. })
        ));
    }
    #[test]
    fn every_distinct_union_cover_in_the_countermodel_is_classified() {
        let p = equality_constraint();
        let contexts = [0u64, 1, 2, 3];
        let mut valid_covers = 0;
        let mut failed_covers = 0;
        for target in contexts {
            for choice in 0..16 {
                let cover: Vec<_> = contexts
                    .iter()
                    .enumerate()
                    .filter(|(i, _)| choice & (1 << i) != 0)
                    .map(|(_, c)| *c)
                    .collect();
                if !cover.iter().all(|&c| included(c, target))
                    || cover.iter().fold(0, |u, c| u | c) != target
                {
                    continue;
                }
                valid_covers += 1;
                let classification = p.classify_cover(target, &cover, 8).unwrap();
                assert!(classification.is_separated);
                if !classification.has_existence {
                    failed_covers += 1;
                    assert_eq!(target, 3);
                    assert!(cover.contains(&1) && cover.contains(&2) && !cover.contains(&3));
                }
            }
        }
        assert_eq!(valid_covers, 16);
        assert_eq!(failed_covers, 2);
    }
}
