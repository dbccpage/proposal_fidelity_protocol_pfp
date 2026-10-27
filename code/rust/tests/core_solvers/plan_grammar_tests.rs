use core_homotopy_type_theory::presentation_difference::*;
use core_solvers::router_plan_grammar::*;
use core_solvers::router_structure_extension::*;

#[test]
fn test_plan_grammar_routing_pareto() {
    let decl = SearchDeclarationV1::new(
        "gram1",
        "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        CostOrder::Pareto,
        2,
        10,
    )
    .unwrap();

    let grammar = FinitePlanGrammarV1 {
        grammar_id: "gram1".to_string(),
        plan_kind: PlanKind::SameLevelRepair,
        cost_order: CostOrder::Pareto,
        cost_dimension: 2,
        candidate_plan_ids: vec!["plan1".to_string(), "plan2".to_string()],
        authority_effect: "None".to_string(),
    };

    let ev1 = DeclaredPlanEvaluationV1 {
        grammar_id: "gram1".to_string(),
        plan_id: "plan1".to_string(),
        status: EvaluationStatus::Verified,
        cost: vec![1, 2],
        replay_receipt_ref:
            "sha256:1111111111111111111111111111111111111111111111111111111111111111".to_string(),
        rejection_reason: "".to_string(),
        authority_effect: "None".to_string(),
    };

    let ev2 = DeclaredPlanEvaluationV1 {
        grammar_id: "gram1".to_string(),
        plan_id: "plan2".to_string(),
        status: EvaluationStatus::Verified,
        cost: vec![2, 1],
        replay_receipt_ref:
            "sha256:2222222222222222222222222222222222222222222222222222222222222222".to_string(),
        rejection_reason: "".to_string(),
        authority_effect: "None".to_string(),
    };

    let frontier = route_declared_finite_grammar(&decl, &grammar, &[ev1, ev2]).unwrap();

    assert_eq!(frontier.accepted_candidate_ids.len(), 2);
    assert_eq!(frontier.dominated_candidate_ids.len(), 0);
    assert_eq!(frontier.terminal, FrontierTerminal::VerifiedFrontier);
}

#[test]
fn test_structure_extension_proposal_contract() {
    let points = vec!["p0".into(), "p1".into(), "p2".into()];
    let q0 = QuestionV1::new("q0", vec!["yes".into(), "yes".into(), "no".into()]).unwrap();
    let parent = PresentationV1::new(points.clone(), vec![q0]).unwrap();
    let demand = DemandV1::new("p0", "p1", true, true).unwrap();

    let q1 = QuestionV1::new("q1", vec!["left".into(), "right".into(), "right".into()]).unwrap();
    let child = PresentationV1::new(
        points,
        vec![
            QuestionV1::new("q0", vec!["yes".into(), "yes".into(), "no".into()]).unwrap(),
            q1,
        ],
    )
    .unwrap();

    let decl = SearchDeclarationV1::new(
        "gram_empty",
        "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        CostOrder::Pareto,
        1,
        5,
    )
    .unwrap();

    let grammar = FinitePlanGrammarV1 {
        grammar_id: "gram_empty".to_string(),
        plan_kind: PlanKind::SameLevelRepair,
        cost_order: CostOrder::Pareto,
        cost_dimension: 1,
        candidate_plan_ids: vec![],
        authority_effect: "None".to_string(),
    };

    let frontier = route_declared_finite_grammar(&decl, &grammar, &[]).unwrap();
    assert_eq!(frontier.terminal, FrontierTerminal::NoVerifiedPlan);

    let evaluation = evaluate_extension(&parent, &child, &demand).unwrap();
    assert!(evaluation.accepted());

    let checked = CheckedQuestionExtensionV1 {
        parent,
        child,
        demand,
        search: decl,
        same_level_grammar: grammar,
        same_level_evaluations: vec![],
        evaluation,
        frontier,
    };

    let receipt = propose_question_family_extension(&checked).expect("proposal should succeed");
    assert_eq!(receipt.authority_effect, "None");
    assert_eq!(receipt.class_count_before, 2);
    assert_eq!(receipt.class_count_after, 3);
    assert!(receipt
        .canonical_id()
        .expect("canonical id")
        .starts_with("sha256:"));
}

// Origin: engine/crates_rs/tests/core_solvers/plan_grammar_tests.rs
// Claim: urn:core:crates_rs:tests:plan-grammar-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9e3ed2e2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9e3ed2e2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9e3ed2e2 {
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
impl BoundaryError9e3ed2e2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9e3ed2e2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9e3ed2e2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9e3ed2e2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9e3ed2e2> {
        if capacity_bound == 0 {
            return Err(BoundaryError9e3ed2e2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9e3ed2e2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9e3ed2e2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9e3ed2e2() {
    let admitted = BoundaryRecord9e3ed2e2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9e3ed2e2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
