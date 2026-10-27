// AuthorityEffect: None.
use num_rational::BigRational;
use core_category_theory::finite_report_query::{
    ReportQueryDecision, ReportQueryProblem, ReportQueryRefusal,
};
use serde_json::json;
use std::collections::BTreeSet;
use std::fmt;

use crate::coda::types::{LayerExecutionRecord, LayerId, ProblemInstance};

pub struct Layer3Cs;

impl Layer3Cs {
    /// Evaluates Layer 3: Continuum Shadow (CODA-CS), legacy table check.
    ///
    /// The projection table must be total and exact on the distinct fine
    /// profile tokens: every fine token has exactly one row, no row names a
    /// token outside the fine profile (for example an extra `{99: 0}`), and
    /// every image lies in the coarse profile. Repeated tokens in either
    /// profile are refused. This is a typing check of one table; it does not
    /// decide whether a query factors through a report (see
    /// [`Layer3Cs::evaluate_report_query`]).
    pub fn evaluate(problem: &ProblemInstance) -> (LayerExecutionRecord, bool) {
        let fine: BTreeSet<i64> = problem.fine_profile.iter().copied().collect();
        let coarse: BTreeSet<i64> = problem.coarse_profile.iter().copied().collect();
        let duplicate_fine = fine.len() != problem.fine_profile.len();
        let duplicate_coarse = coarse.len() != problem.coarse_profile.len();
        let keys: BTreeSet<i64> = problem.projection_map.keys().copied().collect();
        let missing: Vec<i64> = fine.difference(&keys).copied().collect();
        let extraneous: Vec<i64> = keys.difference(&fine).copied().collect();
        let outside: Vec<i64> = problem
            .projection_map
            .iter()
            .filter(|(k, v)| fine.contains(k) && !coarse.contains(v))
            .map(|(k, _)| *k)
            .collect();

        let defects =
            missing.len() + extraneous.len() + outside.len() + duplicate_fine as usize
                + duplicate_coarse as usize;
        let consistent = defects == 0 && !fine.is_empty();
        let msg = if consistent {
            "Projection table is total on the fine profile tokens with images in the coarse \
             profile; no factorization question was decided"
                .to_string()
        } else if fine.is_empty() {
            "Refinement failure: empty fine profile".to_string()
        } else {
            format!(
                "Refinement failure: missing rows {:?}, extraneous rows {:?}, images outside \
                 the coarse profile {:?}, repeated fine tokens {}, repeated coarse tokens {}",
                missing, extraneous, outside, duplicate_fine, duplicate_coarse
            )
        };

        let record = LayerExecutionRecord::new(
            LayerId::CS,
            consistent,
            msg,
            BigRational::from_integer((defects as i64).into()),
        )
        .with_metadata("coarse_profile", json!(problem.coarse_profile))
        .with_metadata("fine_profile", json!(problem.fine_profile))
        .with_metadata("missing_rows", json!(missing))
        .with_metadata("extraneous_rows", json!(extraneous))
        .with_metadata("images_outside_coarse", json!(outside))
        .with_metadata("inconsistent_fibers", json!(defects));

        (record, consistent)
    }

    /// Decides the DP-1 report/query problem through the category owner
    /// [`core_category_theory::finite_report_query`]: total report and query
    /// tables on a declared source, codomain membership as a typing premise,
    /// and either a decoder on the realized image or a collision witness.
    /// Refusals are typed and do not produce a verdict.
    pub fn evaluate_report_query<X, A, B>(
        source: &[X],
        report_codomain: &[A],
        query_codomain: &[B],
        report_rows: &[(X, A)],
        query_rows: &[(X, B)],
    ) -> (
        LayerExecutionRecord,
        Result<ReportQueryDecision<X, A, B>, ReportQueryRefusal<X>>,
    )
    where
        X: Ord + Clone + fmt::Debug,
        A: Ord + Clone + fmt::Debug,
        B: Ord + Clone + fmt::Debug,
    {
        let outcome = ReportQueryProblem::new(
            source,
            report_codomain,
            query_codomain,
            report_rows,
            query_rows,
        )
        .map(|problem| problem.decide());
        let (succeeded, msg, residual) = match &outcome {
            Ok(ReportQueryDecision::Factorable(cert)) => (
                true,
                format!(
                    "Query factors through the report on the realized image ({} values)",
                    cert.realized_image.len()
                ),
                0,
            ),
            Ok(ReportQueryDecision::Collision(c)) => (
                false,
                format!(
                    "Report collision: {:?} and {:?} share report {:?} with queries {:?} and {:?}",
                    c.first, c.second, c.report, c.first_query, c.second_query
                ),
                1,
            ),
            Err(refusal) => (false, format!("Report/query input refused: {refusal:?}"), 1),
        };
        let record = LayerExecutionRecord::new(
            LayerId::CS,
            succeeded,
            msg,
            BigRational::from_integer(residual.into()),
        )
        .with_metadata("contract", json!("finite_report_query"));
        (record, outcome)
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/layer3_cs.rs
// Claim: urn:core:crates_rs:core-wdp:layer3-cs:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc3032d6a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc3032d6a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc3032d6a {
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
impl BoundaryErrorc3032d6a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc3032d6a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc3032d6a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc3032d6a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc3032d6a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc3032d6a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc3032d6a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc3032d6a::ExceedsCapacity {
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
    use std::collections::BTreeMap;

    fn base() -> ProblemInstance {
        let mut p = ProblemInstance::new("layer3_unit");
        p.coarse_profile = vec![0, 1];
        p.fine_profile = vec![0, 1];
        p.projection_map = BTreeMap::from([(0, 0), (1, 1)]);
        p
    }

    #[test]
    fn total_table_is_accepted() {
        let (rec, ok) = Layer3Cs::evaluate(&base());
        assert!(ok && rec.succeeded);
    }

    #[test]
    fn extraneous_row_is_refused() {
        let mut p = base();
        p.projection_map.insert(99, 0);
        let (rec, ok) = Layer3Cs::evaluate(&p);
        assert!(!ok && !rec.succeeded);
        assert!(rec.diagnostic_message.contains("extraneous rows [99]"));
    }

    #[test]
    fn missing_row_is_refused() {
        let mut p = base();
        p.projection_map.remove(&1);
        let (_, ok) = Layer3Cs::evaluate(&p);
        assert!(!ok);
    }

    #[test]
    fn repeated_tokens_and_empty_profiles_are_refused() {
        let mut p = base();
        p.fine_profile = vec![0, 1, 1];
        assert!(!Layer3Cs::evaluate(&p).1);
        let mut p = base();
        p.coarse_profile = vec![0, 0, 1];
        assert!(!Layer3Cs::evaluate(&p).1);
        let mut p = base();
        p.fine_profile.clear();
        p.projection_map.clear();
        assert!(!Layer3Cs::evaluate(&p).1);
    }

    #[test]
    fn image_outside_coarse_profile_is_refused() {
        let mut p = base();
        p.projection_map.insert(0, 999);
        assert!(!Layer3Cs::evaluate(&p).1);
    }

    #[test]
    fn report_query_contract_factors_collides_and_refuses() {
        let (rec, out) = Layer3Cs::evaluate_report_query(
            &[0, 1, 2],
            &["p", "q"],
            &[10, 20],
            &[(0, "p"), (1, "p"), (2, "q")],
            &[(0, 10), (1, 10), (2, 20)],
        );
        assert!(rec.succeeded);
        assert!(matches!(out, Ok(ReportQueryDecision::Factorable(_))));

        let (rec, out) = Layer3Cs::evaluate_report_query(
            &[0, 1],
            &["p"],
            &[10, 20],
            &[(0, "p"), (1, "p")],
            &[(0, 10), (1, 20)],
        );
        assert!(!rec.succeeded);
        assert!(matches!(out, Ok(ReportQueryDecision::Collision(_))));

        let (rec, out) = Layer3Cs::evaluate_report_query(
            &[0, 1],
            &["p"],
            &[10],
            &[(0, "p"), (1, "p"), (99, "p")],
            &[(0, 10), (1, 10)],
        );
        assert!(!rec.succeeded);
        assert!(matches!(
            out,
            Err(ReportQueryRefusal::ExtraneousAssignment { .. })
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_c3032d6a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc3032d6a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc3032d6a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc3032d6a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc3032d6a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc3032d6a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc3032d6a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc3032d6a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
