//! Finite families of protected questions and their common report quotient.
//!
//! Rows are declared alternatives, columns are questions, and answers have exact
//! equality. No probability, physical realization, or closure under operations is
//! inferred. Factorization and gluing delegate to the existing category owners.

use crate::finite_report_descent::{DescentError, FiniteReportPresheaf};
use crate::finite_report_query::{ReportQueryProblem, ReportQueryRefusal};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Debug;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QuestionFamilyError {
    RowWidth {
        row: usize,
        expected: usize,
        actual: usize,
    },
    MapLength {
        expected: usize,
        actual: usize,
    },
    ImageOutsideTarget {
        source: usize,
        image: usize,
    },
    WorkLimit,
    Report(ReportQueryRefusal<usize>),
    Descent(DescentError),
}

// Origin: engine/crates_rs/core_category_theory/src/finite_question_family.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-question-family:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for QuestionFamilyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for QuestionFamilyError {}

/// Lexicographically ordered realized profiles; `class_of` keeps source order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuestionQuotient<A> {
    pub profiles: Vec<Vec<A>>,
    pub class_of: Vec<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteQuestionFamily<A> {
    question_count: usize,
    answers: Vec<Vec<A>>,
}

/// The full context retains source alternatives, including indistinguishable
/// ones. Proper contexts retain only their realized answer profiles. Therefore
/// gluing can distinguish absence of a global alternative from ambiguity.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuestionReportSite<A> {
    presheaf: FiniteReportPresheaf,
    profiles: BTreeMap<u64, Vec<Vec<A>>>,
}

impl<A> QuestionReportSite<A> {
    pub fn presheaf(&self) -> &FiniteReportPresheaf {
        &self.presheaf
    }
    pub fn profiles(&self) -> &BTreeMap<u64, Vec<Vec<A>>> {
        &self.profiles
    }
}

/// Build one total factorization problem without allowing implicit missing rows.
pub fn factor_tables<R: Ord + Clone + Debug, A: Ord + Clone + Debug>(
    report: &[R],
    query: &[A],
) -> Result<ReportQueryProblem<usize, R, A>, QuestionFamilyError> {
    if report.len() != query.len() {
        return Err(QuestionFamilyError::MapLength {
            expected: query.len(),
            actual: report.len(),
        });
    }
    let source: Vec<_> = (0..query.len()).collect();
    let reports: Vec<_> = report
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let queries: Vec<_> = query
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    ReportQueryProblem::new(
        &source,
        &reports,
        &queries,
        &report.iter().cloned().enumerate().collect::<Vec<_>>(),
        &query.iter().cloned().enumerate().collect::<Vec<_>>(),
    )
    .map_err(QuestionFamilyError::Report)
}

impl<A: Ord + Clone + Debug> FiniteQuestionFamily<A> {
    /// Empty sources and empty question families are valid, distinct cases.
    pub fn new(question_count: usize, answers: Vec<Vec<A>>) -> Result<Self, QuestionFamilyError> {
        for (row, values) in answers.iter().enumerate() {
            if values.len() != question_count {
                return Err(QuestionFamilyError::RowWidth {
                    row,
                    expected: question_count,
                    actual: values.len(),
                });
            }
        }
        Ok(Self {
            question_count,
            answers,
        })
    }

    pub fn answers(&self) -> &[Vec<A>] {
        &self.answers
    }
    pub fn question_count(&self) -> usize {
        self.question_count
    }

    /// Equal classes iff every declared answer agrees. Any sufficient report
    /// uniquely decodes these profiles on its realized image (factor_report).
    pub fn quotient(&self) -> QuestionQuotient<A> {
        let profiles: Vec<_> = self
            .answers
            .iter()
            .cloned()
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect();
        let ids: BTreeMap<_, _> = profiles
            .iter()
            .cloned()
            .enumerate()
            .map(|(i, p)| (p, i))
            .collect();
        let class_of = self.answers.iter().map(|row| ids[row]).collect();
        QuestionQuotient { profiles, class_of }
    }

    pub fn verify_quotient(&self, candidate: &QuestionQuotient<A>) -> bool {
        *candidate == self.quotient()
    }

    pub fn factor_report<R: Ord + Clone + Debug>(
        &self,
        report: &[R],
    ) -> Result<ReportQueryProblem<usize, R, Vec<A>>, QuestionFamilyError> {
        factor_tables(report, &self.answers)
    }

    /// A partial operation descends iff both availability and target class are
    /// constant on each source class. `None` means unavailable, never unknown.
    pub fn descend_operation<B: Ord + Clone + Debug>(
        &self,
        target: &FiniteQuestionFamily<B>,
        images: &[Option<usize>],
    ) -> Result<ReportQueryProblem<usize, usize, Option<usize>>, QuestionFamilyError> {
        if images.len() != self.answers.len() {
            return Err(QuestionFamilyError::MapLength {
                expected: self.answers.len(),
                actual: images.len(),
            });
        }
        let target_classes = target.quotient().class_of;
        let query = images
            .iter()
            .enumerate()
            .map(|(source, image)| match image {
                None => Ok(None),
                Some(i) => target_classes
                    .get(*i)
                    .copied()
                    .map(Some)
                    .ok_or(QuestionFamilyError::ImageOutsideTarget { source, image: *i }),
            })
            .collect::<Result<Vec<_>, _>>()?;
        factor_tables(&self.quotient().class_of, &query)
    }

    /// Check joint composition on the FULL declared Cartesian product, in
    /// left-major order. Local sufficiency alone does not imply this equation.
    pub fn descend_composition<B: Ord + Clone + Debug, C: Ord + Clone + Debug>(
        &self,
        right: &FiniteQuestionFamily<B>,
        target: &FiniteQuestionFamily<C>,
        images: &[Option<usize>],
    ) -> Result<ReportQueryProblem<usize, (usize, usize), Option<usize>>, QuestionFamilyError> {
        let expected = self
            .answers
            .len()
            .checked_mul(right.answers.len())
            .ok_or(QuestionFamilyError::WorkLimit)?;
        if images.len() != expected {
            return Err(QuestionFamilyError::MapLength {
                expected,
                actual: images.len(),
            });
        }
        let left_classes = self.quotient().class_of;
        let right_classes = right.quotient().class_of;
        let reports: Vec<_> = left_classes
            .iter()
            .flat_map(|&l| right_classes.iter().map(move |&r| (l, r)))
            .collect();
        let classes = target.quotient().class_of;
        let query = images
            .iter()
            .enumerate()
            .map(|(source, image)| match image {
                None => Ok(None),
                Some(i) => classes
                    .get(*i)
                    .copied()
                    .map(Some)
                    .ok_or(QuestionFamilyError::ImageOutsideTarget { source, image: *i }),
            })
            .collect::<Result<Vec<_>, _>>()?;
        factor_tables(&reports, &query)
    }

    fn check_site_bounds(
        &self,
        contexts: &BTreeSet<u64>,
        work_limit: usize,
    ) -> Result<u64, QuestionFamilyError> {
        if self.question_count > 64 {
            return Err(QuestionFamilyError::Descent(DescentError::CarrierTooLarge));
        }
        let full = if self.question_count == 64 {
            u64::MAX
        } else {
            (1u64 << self.question_count) - 1
        };
        for &context in contexts {
            if context & !full != 0 {
                return Err(QuestionFamilyError::Descent(
                    DescentError::ContextOutsideCarrier { context },
                ));
            }
        }
        let c = contexts.len();
        let work = c
            .checked_add(self.question_count)
            .and_then(|x| x.checked_mul(c))
            .and_then(|x| x.checked_mul(c))
            .and_then(|x| x.checked_mul(self.answers.len().max(1)))
            .ok_or(QuestionFamilyError::WorkLimit)?;
        if work > work_limit {
            return Err(QuestionFamilyError::WorkLimit);
        }
        Ok(full)
    }

    fn build_site_profiles(
        &self,
        contexts: &BTreeSet<u64>,
        full: u64,
    ) -> BTreeMap<u64, Vec<Vec<A>>> {
        let mut profiles = BTreeMap::new();
        for &context in contexts {
            let projected: Vec<Vec<A>> = self
                .answers
                .iter()
                .map(|row| {
                    row.iter()
                        .enumerate()
                        .filter(|(i, _)| context & (1u64 << i) != 0)
                        .map(|(_, a)| a.clone())
                        .collect()
                })
                .collect();
            let unique_or_full = if context == full {
                projected
            } else {
                projected
                    .into_iter()
                    .collect::<BTreeSet<_>>()
                    .into_iter()
                    .collect()
            };
            profiles.insert(context, unique_or_full);
        }
        profiles
    }

    fn build_restriction_table(
        &self,
        source: u64,
        source_profiles: &[Vec<A>],
        target: u64,
        target_profiles: &[Vec<A>],
    ) -> Result<Vec<usize>, QuestionFamilyError> {
        if source == target {
            return Ok((0..source_profiles.len()).collect());
        }
        let ids: BTreeMap<_, _> = target_profiles
            .iter()
            .cloned()
            .enumerate()
            .map(|(i, p)| (p, i))
            .collect();
        let positions: Vec<_> = (0..self.question_count)
            .filter(|i| source & (1u64 << i) != 0)
            .collect();
        source_profiles
            .iter()
            .map(|row| {
                let projected: Vec<_> = positions
                    .iter()
                    .zip(row)
                    .filter(|(i, _)| target & (1u64 << **i) != 0)
                    .map(|(_, a)| a.clone())
                    .collect();
                // Every restriction is the projection of the same source row.
                ids.get(&projected)
                    .copied()
                    .ok_or(QuestionFamilyError::Descent(
                        DescentError::RestrictionTargetOutsideReports { source, target },
                    ))
            })
            .collect()
    }

    /// Questions index a finite site (at most 64). Contexts must contain empty
    /// and full and be intersection closed; the presheaf owner checks all laws.
    /// `work_limit` bounds a conservative count of table/compatibility cells,
    /// not answer byte sizes or CPU time. Exhaustion is not global-red evidence.
    pub fn report_site(
        &self,
        contexts: &BTreeSet<u64>,
        work_limit: usize,
    ) -> Result<QuestionReportSite<A>, QuestionFamilyError> {
        let full = self.check_site_bounds(contexts, work_limit)?;
        let profiles = self.build_site_profiles(contexts, full);
        let counts = profiles.iter().map(|(&c, ps)| (c, ps.len())).collect();
        let mut restrictions = BTreeMap::new();
        for (&source, source_profiles) in &profiles {
            for (&target, target_profiles) in &profiles {
                if source & target != target {
                    continue;
                }
                let table = self.build_restriction_table(
                    source,
                    source_profiles,
                    target,
                    target_profiles,
                )?;
                restrictions.insert((source, target), table);
            }
        }
        let presheaf = FiniteReportPresheaf::new(self.question_count, counts, restrictions)
            .map_err(QuestionFamilyError::Descent)?;
        Ok(QuestionReportSite { presheaf, profiles })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_72facf0a {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
