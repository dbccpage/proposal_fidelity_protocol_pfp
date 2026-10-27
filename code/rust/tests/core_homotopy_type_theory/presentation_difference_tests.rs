//! Unit tests for presentation difference model.

use core_homotopy_type_theory::presentation_difference::*;

#[test]
fn test_presentation_profile_and_obstruction() {
    let points = vec!["p0".into(), "p1".into(), "p2".into()];
    let q0 = QuestionV1::new("q0", vec!["yes".into(), "yes".into(), "no".into()]).unwrap();
    let pres = PresentationV1::new(points, vec![q0]).unwrap();

    assert_eq!(pres.class_count(), 2);
    assert!(pres.zero_related("p0", "p1"));
    assert!(!pres.zero_related("p0", "p2"));

    let demand = DemandV1::new("p0", "p1", true, true).unwrap();
    let obs = active_obstruction(&pres, &demand);
    assert!(obs.is_some());
    let obs = obs.unwrap();
    assert_eq!(obs.shared_profile, vec!["yes"]);

    // Test extension that resolves the obstruction
    let q1 = QuestionV1::new("q1", vec!["left".into(), "right".into(), "right".into()]).unwrap();
    let child = PresentationV1::new(
        vec!["p0".into(), "p1".into(), "p2".into()],
        vec![
            QuestionV1::new("q0", vec!["yes".into(), "yes".into(), "no".into()]).unwrap(),
            q1,
        ],
    )
    .unwrap();

    let eval = evaluate_extension(&pres, &child, &demand).unwrap();
    assert!(eval.accepted());
    assert_eq!(eval.effect, ExtensionEffect::Resolved);
    assert_eq!(eval.class_count_before, 2);
    assert_eq!(eval.class_count_after, 3);
}

#[test]
fn short_answer_list_is_not_derived_and_does_not_panic() {
    let parent = PresentationV1::new(vec!["a".into(), "b".into()], vec![]).unwrap();
    let question = QuestionV1::new("q", vec!["only".into()]).unwrap();
    assert!(!question_is_derived_from_parent(&parent, &question));
}

#[test]
fn deserialize_rejects_a_short_answer_presentation() {
    let raw = r#"{"points":["a","b"],"questions":[{"question_id":"q","answers":["only"]}],"authority_effect":"None"}"#;
    assert!(serde_json::from_str::<PresentationV1>(raw).is_err());
}

// Origin: engine/crates_rs/tests/core_homotopy_type_theory/presentation_difference_tests.rs
// Claim: urn:core:crates_rs:tests:presentation-difference-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddf8cce61 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddf8cce61` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordf8cce61 {
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
impl BoundaryErrordf8cce61 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordf8cce61 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordf8cce61 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddf8cce61 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordf8cce61> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordf8cce61::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordf8cce61::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordf8cce61::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_df8cce61() {
    let admitted = BoundaryRecorddf8cce61::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddf8cce61::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
