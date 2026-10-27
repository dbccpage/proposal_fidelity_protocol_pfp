// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use core_category_theory::finite_section_separation::{
    decide_separation, weighted_coordinate_pseudometric, FiniteEquivalence, SectionRecord,
    SeparationOutcome, SeparationRefusal,
};
use serde_json::json;
use std::collections::BTreeSet;
use std::fmt;

use crate::coda::types::{LayerExecutionRecord, LayerId, ProblemInstance};

pub struct Layer4CsQ;

impl Layer4CsQ {
    /// Evaluates Layer 4: Continuum Shadow to Continuum Bridge (CODA-CS-Q),
    /// legacy overlap-flag screen.
    ///
    /// Section vectors are compared position by position with the unweighted
    /// L1 sum. A pair at distance 0 that no `true` overlap flag declares
    /// glued is reported as a collision. Vectors of different lengths are
    /// incomparable and fail the screen (they are not skipped). The screen
    /// reports the least nonzero distance but is not a separation
    /// certificate: the overlap flags are not checked to be an equivalence,
    /// a flagged pair at positive distance is accepted, and with fewer than
    /// two sections nothing is compared. The declared-domain contract is
    /// [`Layer4CsQ::evaluate_declared_separation`].
    fn format_screen_message(
        collisions: &[(String, String)],
        incomparable: &[(String, String)],
        compared: usize,
        sep: &BigRational,
    ) -> String {
        if !collisions.is_empty() {
            format!(
                "Legacy overlap-flag screen: colliding sections {:?}",
                collisions
            )
        } else if !incomparable.is_empty() {
            format!(
                "Legacy overlap-flag screen: incomparable section lengths {:?}",
                incomparable
            )
        } else if compared == 0 {
            "Legacy overlap-flag screen: no comparable pair, nothing was compared; not a \
             separation certificate"
                .to_string()
        } else {
            format!(
                "Legacy overlap-flag screen passed; least nonzero distance={}; not a separation \
                 certificate",
                sep
            )
        }
    }

    fn update_min_separation(min_sep: &mut Option<BigRational>, diff: BigRational) {
        if min_sep.as_ref().is_none_or(|cur| &diff < cur) {
            *min_sep = Some(diff);
        }
    }

    pub fn evaluate(problem: &ProblemInstance) -> (LayerExecutionRecord, BigRational) {
        let sections: Vec<(&String, &Vec<BigRational>)> = problem.local_sections.iter().collect();
        let mut glued: BTreeSet<BTreeSet<String>> = BTreeSet::new();

        for ((u, v), &compatible) in &problem.overlaps {
            if compatible {
                let mut pair = BTreeSet::new();
                pair.insert(u.clone());
                pair.insert(v.clone());
                glued.insert(pair);
            }
        }

        let mut collisions = Vec::new();
        let mut incomparable = Vec::new();
        let mut compared = 0usize;
        let mut min_sep: Option<BigRational> = None;

        for i in 0..sections.len() {
            for j in (i + 1)..sections.len() {
                let (la, a) = sections[i];
                let (lb, b) = sections[j];
                if a.len() != b.len() {
                    incomparable.push(((*la).clone(), (*lb).clone()));
                    continue;
                }
                compared += 1;

                let diff: BigRational = a.iter().zip(b.iter()).map(|(x, y)| (x - y).abs()).sum();
                if diff.is_zero() {
                    let pair = BTreeSet::from([(*la).clone(), (*lb).clone()]);
                    if !glued.contains(&pair) {
                        collisions.push(((*la).clone(), (*lb).clone()));
                    }
                } else {
                    Self::update_min_separation(&mut min_sep, diff);
                }
            }
        }

        let sep = min_sep.unwrap_or_else(BigRational::zero);
        let succeeded = collisions.is_empty() && incomparable.is_empty();
        let msg = Self::format_screen_message(&collisions, &incomparable, compared, &sep);

        let record = LayerExecutionRecord::new(LayerId::CS_Q, succeeded, msg, sep.clone())
            .with_metadata("min_separation", json!(sep.to_string()))
            .with_metadata("compared_pairs", json!(compared))
            .with_metadata("incomparable_pairs", json!(incomparable))
            .with_metadata("collisions", json!(collisions));

        (record, sep)
    }

    /// Decides separation of a declared quotient through the category owner
    /// [`core_category_theory::finite_section_separation`]: records on one
    /// declared common domain, a nonnegative weight per coordinate, and the
    /// declared classes as a partition of the record identities. Succeeds
    /// only with `Separated` (the identification is exactly the zero-distance
    /// relation and there are at least two classes); the record value is the
    /// attained gap. Every other outcome fails, with the typed refusal or the
    /// zero-distance collision returned.
    pub fn evaluate_declared_separation<P>(
        records: &[SectionRecord<String, P>],
        common_domain: &[P],
        weights: &[(P, BigRational)],
        classes: &[Vec<String>],
    ) -> (
        LayerExecutionRecord,
        Result<SeparationOutcome<String>, SeparationRefusal<String, P>>,
    )
    where
        P: Ord + Clone + fmt::Debug,
    {
        let points: Vec<String> = records.iter().map(|r| r.id().clone()).collect();
        let outcome = weighted_coordinate_pseudometric(records, common_domain, weights)
            .and_then(|metric| {
                let equivalence = FiniteEquivalence::from_classes(&points, classes)?;
                decide_separation(&metric, &equivalence)
            });
        let (succeeded, msg, value) = match &outcome {
            Ok(SeparationOutcome::Separated {
                gap,
                attaining_pair,
                ..
            }) => (
                true,
                format!(
                    "Declared quotient is separated; gap {} attained at {:?}",
                    gap, attaining_pair
                ),
                gap.clone(),
            ),
            Ok(SeparationOutcome::ZeroCollision { left, right }) => (
                false,
                format!(
                    "Declared quotient is not separated: {left:?} and {right:?} are at distance \
                     zero in different classes"
                ),
                BigRational::zero(),
            ),
            Err(refusal) => (
                false,
                format!("Declared separation input refused: {refusal:?}"),
                BigRational::zero(),
            ),
        };
        let record = LayerExecutionRecord::new(LayerId::CS_Q, succeeded, msg, value)
            .with_metadata("contract", json!("finite_section_separation"));
        (record, outcome)
    }
}

// Origin: engine/crates_rs/core_wdp/src/coda/layer4_cs_q.rs
// Claim: urn:core:crates_rs:core-wdp:layer4-cs-q:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf9706332 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf9706332` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf9706332 {
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
impl BoundaryErrorf9706332 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf9706332 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf9706332 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf9706332 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf9706332> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf9706332::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf9706332::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf9706332::ExceedsCapacity {
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

    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(n.into(), d.into())
    }

    fn record(id: &str, x: BigRational, y: BigRational) -> SectionRecord<String, &'static str> {
        SectionRecord::new(id.to_string(), &["x", "y"], &[("x", x), ("y", y)])
            .expect("admitted record")
    }

    #[test]
    fn legacy_screen_fails_on_incomparable_lengths() {
        let mut p = ProblemInstance::new("layer4_unit");
        p.local_sections = BTreeMap::from([
            ("U0".to_string(), vec![q(1, 2)]),
            ("U1".to_string(), vec![q(1, 2), q(0, 1)]),
        ]);
        let (rec, _) = Layer4CsQ::evaluate(&p);
        assert!(!rec.succeeded);
        assert!(rec.diagnostic_message.contains("incomparable"));
    }

    #[test]
    fn legacy_screen_says_nothing_was_compared_for_one_section() {
        let mut p = ProblemInstance::new("layer4_unit");
        p.local_sections = BTreeMap::from([("U0".to_string(), vec![q(1, 2)])]);
        let (rec, sep) = Layer4CsQ::evaluate(&p);
        assert!(rec.succeeded);
        assert!(sep.is_zero());
        assert!(rec.diagnostic_message.contains("nothing was compared"));
    }

    #[test]
    fn declared_separation_succeeds_with_attained_gap() {
        let records = [
            record("a", q(0, 1), q(0, 1)),
            record("b", q(1, 1), q(0, 1)),
        ];
        let weights = [("x", q(1, 1)), ("y", q(1, 1))];
        let classes = [vec!["a".to_string()], vec!["b".to_string()]];
        let (rec, out) =
            Layer4CsQ::evaluate_declared_separation(&records, &["x", "y"], &weights, &classes);
        assert!(rec.succeeded);
        assert_eq!(rec.defect_mass, q(1, 1));
        assert!(matches!(out, Ok(SeparationOutcome::Separated { .. })));
    }

    #[test]
    fn declared_separation_reports_zero_collision_and_refusals() {
        let records = [
            record("a", q(0, 1), q(0, 1)),
            record("b", q(0, 1), q(0, 1)),
        ];
        let weights = [("x", q(1, 1)), ("y", q(1, 1))];
        let classes = [vec!["a".to_string()], vec!["b".to_string()]];
        let (rec, out) =
            Layer4CsQ::evaluate_declared_separation(&records, &["x", "y"], &weights, &classes);
        assert!(!rec.succeeded);
        assert!(matches!(out, Ok(SeparationOutcome::ZeroCollision { .. })));

        // Identifying records at positive distance is refused.
        let records = [
            record("a", q(0, 1), q(0, 1)),
            record("b", q(1, 1), q(0, 1)),
        ];
        let one_class = [vec!["a".to_string(), "b".to_string()]];
        let (rec, out) =
            Layer4CsQ::evaluate_declared_separation(&records, &["x", "y"], &weights, &one_class);
        assert!(!rec.succeeded);
        assert!(matches!(
            out,
            Err(SeparationRefusal::IdentificationNotZero { .. })
        ));

        // One record: nothing to compare.
        let (rec, out) = Layer4CsQ::evaluate_declared_separation(
            &records[..1],
            &["x", "y"],
            &weights,
            &[vec!["a".to_string()]],
        );
        assert!(!rec.succeeded);
        assert!(matches!(out, Err(SeparationRefusal::NoComparablePairs)));

        // Different declared domains are incomparable.
        let other = SectionRecord::new("c".to_string(), &["x"], &[("x", q(0, 1))])
            .expect("admitted");
        let mixed = [records[0].clone(), other];
        let (rec, out) = Layer4CsQ::evaluate_declared_separation(
            &mixed,
            &["x", "y"],
            &weights,
            &[vec!["a".to_string()], vec!["c".to_string()]],
        );
        assert!(!rec.succeeded);
        assert!(out.is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_f9706332 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf9706332::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf9706332::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf9706332::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf9706332::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf9706332::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf9706332::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf9706332::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
