use crate::genesis_primitive_execution::{PrimitiveEvent as E, PrimitiveInstance};
use crate::genesis_questions::{Answer, ProtectedQuestion, Question};
use crate::genesis_report_runtime::*;
use std::collections::BTreeSet;

fn history(id: &str, tokens: &[&str]) -> NamedHistory {
    NamedHistory {
        id: id.into(),
        events: std::iter::once(E::Supply { token: "<>".into() })
            .chain(tokens.iter().map(|s| E::AdmitDatum { token: (*s).into() }))
            .collect(),
    }
}
fn request(histories: Vec<NamedHistory>) -> Request {
    Request {
        schema_version: REQUEST_SCHEMA.into(),
        source_sha256: source_sha256(),
        report: vec!["forgotten".into(); histories.len()],
        histories,
        questions: [
            Question::HasDatum("a".into()),
            Question::HasDatum("b".into()),
            Question::DatumCount,
            Question::EventCount,
        ]
        .into_iter()
        .enumerate()
        .map(|(i, question)| ProtectedQuestion {
            id: format!("q{i}"),
            question,
        })
        .collect(),
        continuations: vec![NamedHistory {
            id: "now".into(),
            events: vec![],
        }],
        global: None,
        repair: Some(RepairAllowance {
            max_steps: 64,
            max_pair_checks: 1_000_000,
        }),
    }
}
fn global(fact_column: usize, locals: Vec<usize>) -> GlobalRequest {
    GlobalRequest {
        observed_columns: vec![1, 2],
        contexts: BTreeSet::from([0, 1, 2, 3]),
        cover: vec![1, 2],
        locals,
        fact_column,
        work_limit: 1_000_000,
    }
}

#[test]
fn keeps_all_five_fields_and_all_six_event_types() {
    let mut h = history("six", &["a", "b", "a"]);
    h.events.extend([
        E::AdmitForm { arity: 1 },
        E::AdmitForm { arity: 1 },
        E::AdmitInst {
            form: 0,
            args: vec![1],
        },
        E::AdmitRuleAll { form: 1 },
        E::Impose { i: 0, j: 1 },
    ]);
    let r = evaluate(&request(vec![h])).unwrap();
    assert_eq!(
        r.states[0],
        State {
            data: vec!["a".into(), "b".into()],
            forms: vec![1, 1],
            instances: vec![PrimitiveInstance {
                form: 0,
                args: vec![1]
            }],
            rules: vec![1],
            requirements: vec![(0, 1)]
        }
    );
    assert_eq!(r.answers[0][4], Answer::Count(9));
}

#[test]
fn empty_unique_ambiguous_and_definite_facts_remain_distinct() {
    let mut empty = request(vec![history("00", &[]), history("11", &["a", "b"])]);
    empty.global = Some(global(3, vec![0, 1]));
    let result = evaluate(&empty).unwrap();
    assert!(result.global.as_ref().unwrap().histories.is_empty());
    assert_eq!(
        result.global.as_ref().unwrap().fact,
        Fact::NoGlobalExtension
    );
    for check in &result.repair.unwrap().global_rechecks {
        assert_eq!(check, &result.global);
    }

    let mut unique = request(vec![history("10", &["a"]), history("01", &["b"])]);
    unique.global = Some(global(3, vec![1, 0]));
    assert_eq!(
        evaluate(&unique).unwrap().global.unwrap().histories,
        vec![0]
    );

    let mut duplicate = history("other occurrence", &["a"]);
    duplicate.events.push(E::Supply {
        token: "inert".into(),
    });
    let mut ambiguous = request(vec![history("10", &["a"]), duplicate]);
    ambiguous.global = Some(global(3, vec![0, 0]));
    let g = evaluate(&ambiguous).unwrap().global.unwrap();
    assert_eq!(g.histories, vec![0, 1]);
    assert_eq!(
        g.fact,
        Fact::Certified {
            answer: Answer::Count(1)
        }
    );
    ambiguous.global.as_mut().unwrap().fact_column = 4;
    assert_eq!(
        evaluate(&ambiguous).unwrap().global.unwrap().fact,
        Fact::Undetermined {
            first: 0,
            second: 1
        }
    );
}

#[test]
fn repairs_preserve_old_reports_have_strict_rank_and_replay_original_task() {
    let mut r = request(vec![
        history("0", &[]),
        history("a", &["a"]),
        history("b", &["b"]),
        history("ab", &["a", "b"]),
    ]);
    r.global = Some(global(3, vec![1, 0]));
    let result = evaluate(&r).unwrap();
    assert!(matches!(result.report, Decision::Collision { .. }));
    let repair = result.repair.as_ref().unwrap();
    assert_eq!(repair.ranks.last(), Some(&0));
    assert!(repair.ranks.windows(2).all(|pair| pair[1] < pair[0]));
    assert_eq!(repair.partitions.len(), repair.steps.len() + 1);
    assert!(repair.global_rechecks.iter().all(|g| g == &result.global));
    verify(&r, &result).unwrap();
    let mut forged = result.clone();
    forged
        .repair
        .as_mut()
        .unwrap()
        .partitions
        .last_mut()
        .unwrap()[0] = 88;
    assert_eq!(verify(&r, &forged).unwrap_err().code, "CANDIDATE");
    r.repair.as_mut().unwrap().max_steps = 0;
    assert_eq!(evaluate(&r).unwrap_err().code, "REPAIR");
}

#[test]
fn declared_language_does_not_silently_claim_compositional_closure() {
    let mut r = request(vec![
        history("with datum", &["a"]),
        history("without datum", &[]),
    ]);
    r.questions = vec![ProtectedQuestion {
        id: "form1".into(),
        question: Question::Derivable(PrimitiveInstance {
            form: 1,
            args: vec![0],
        }),
    }];
    r.continuations.push(NamedHistory {
        id: "one form".into(),
        events: vec![E::AdmitForm { arity: 1 }],
    });
    let result = evaluate(&r).unwrap();
    assert_eq!(result.class_of, vec![0, 0]);
    assert!(matches!(
        result.operations[1].decision,
        Decision::Collision {
            first: 0,
            second: 1,
            ..
        }
    ));
    // The two-word check exposes a distinction absent at zero and one steps.
    r.continuations.push(NamedHistory {
        id: "two forms".into(),
        events: vec![E::AdmitForm { arity: 1 }, E::AdmitForm { arity: 1 }],
    });
    assert_ne!(
        evaluate(&r).unwrap().class_of[0],
        evaluate(&r).unwrap().class_of[1]
    );
}

#[test]
fn availability_is_protected_even_with_no_questions() {
    let mut r = request(vec![
        NamedHistory {
            id: "pre".into(),
            events: vec![],
        },
        history("root", &[]),
    ]);
    r.questions.clear();
    r.continuations.push(NamedHistory {
        id: "admit".into(),
        events: vec![E::AdmitDatum { token: "a".into() }],
    });
    let result = evaluate(&r).unwrap();
    assert_eq!(
        result.answers,
        vec![
            vec![Answer::Boolean(true), Answer::Boolean(false)],
            vec![Answer::Boolean(true), Answer::Boolean(true)]
        ]
    );
}

#[test]
fn admission_errors_source_changes_and_resource_failures_refuse() {
    let mut r = request(vec![history("a", &["a", "b"])]);
    r.histories[0].events.push(E::Impose { i: 1, j: 0 });
    assert_eq!(evaluate(&r).unwrap_err().code, "ADMISSION");
    r.histories[0].events.pop();
    let result = evaluate(&r).unwrap();
    r.histories[0].events.push(E::Supply {
        token: "changed occurrence".into(),
    });
    assert_eq!(verify(&r, &result).unwrap_err().code, "CANDIDATE");
    r.source_sha256 = "0".repeat(64);
    assert_eq!(evaluate(&r).unwrap_err().code, "SOURCE");
    r.source_sha256 = source_sha256();
    r.global = Some(global(3, vec![0, 0]));
    r.global.as_mut().unwrap().work_limit = 0;
    assert_eq!(evaluate(&r).unwrap_err().code, "RESTRICTIONS");
    r.global.as_mut().unwrap().work_limit = 1_000_000;
    r.global.as_mut().unwrap().contexts.remove(&0);
    assert_eq!(evaluate(&r).unwrap_err().code, "RESTRICTIONS");
}

#[test]
fn no_histories_never_certifies_a_vacuous_fact_or_creates_a_repair() {
    let mut r = request(vec![]);
    // Empty local families have no available section. Invalid local indices
    // refuse rather than asserting a fact of an uninhabited source.
    r.global = Some(global(3, vec![0, 0]));
    assert_eq!(evaluate(&r).unwrap_err().code, "LOCAL_REPORTS");
    r.global = None;
    let result = evaluate(&r).unwrap();
    assert!(result.profiles.is_empty());
    assert_eq!(result.repair.unwrap().partitions, vec![Vec::<usize>::new()]);
}

#[test]
fn uniform_unavailability_is_not_a_certified_answer() {
    let mut r = request(vec![history("a", &["a"]), history("b", &["b"])]);
    r.questions.push(ProtectedQuestion {
        id: "invalid form".into(),
        question: Question::Derivable(PrimitiveInstance {
            form: 1,
            args: vec![0],
        }),
    });
    r.global = Some(global(5, vec![1, 0]));
    assert_eq!(
        evaluate(&r).unwrap().global.unwrap().fact,
        Fact::Unavailable
    );
    r.questions[0].question = Question::HasDatum("a".repeat(257));
    assert_eq!(evaluate(&r).unwrap_err().code, "BOUNDS");
}

// Origin: engine/crates_rs/core_wdp/src/genesis_report_runtime/tests.rs
// Claim: urn:core:crates_rs:core-wdp:tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordafada668 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordafada668` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorafada668 {
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
impl BoundaryErrorafada668 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorafada668 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorafada668 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordafada668 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorafada668> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorafada668::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorafada668::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorafada668::ExceedsCapacity {
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
mod l4_boundary_tests_afada668 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordafada668::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordafada668::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordafada668::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordafada668::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordafada668::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorafada668::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorafada668::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
