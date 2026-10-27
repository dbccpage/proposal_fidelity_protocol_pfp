use num_rational::BigRational;
use core_category_theory::finite_report_descent::DescentOutcome;
use core_category_theory::finite_report_query::ReportQueryDecision;
use core_finite_probability::log_form::{LogForm, DEFAULT_FACTOR_BOUND};
use core_finite_probability::simplex::ProbabilitySimplex;
use core_ooutwire_primitives::{
    event::Event,
    mark::{Mark, Pair},
    token::Token,
};
use core_wdp::genesis_construction::ConstructionError;
use core_wdp::genesis_primitive_execution::PrimitiveInstance;
use core_wdp::genesis_questions::*;
use std::collections::BTreeSet;

fn history(id: &str, tokens: &[&str]) -> History {
    History {
        id: id.into(),
        events: std::iter::once(Event::Supply(Token::new("<>")))
            .chain(tokens.iter().map(|t| Event::AdmitDatum(Token::new(*t))))
            .collect(),
    }
}
fn questions(values: Vec<Question>) -> Vec<ProtectedQuestion> {
    values
        .into_iter()
        .enumerate()
        .map(|(i, question)| ProtectedQuestion {
            id: format!("q{i}"),
            question,
        })
        .collect()
}
fn presentation(histories: Vec<History>, values: Vec<Question>) -> Presentation {
    Presentation::new(histories, questions(values), QuestionLimits::default()).unwrap()
}
fn law(values: &[(i64, i64)]) -> ProbabilitySimplex {
    ProbabilitySimplex::try_new(
        values
            .iter()
            .map(|&(n, d)| BigRational::new(n.into(), d.into()))
            .collect(),
    )
    .unwrap()
}

#[test]
fn native_questions_keep_presentation_history_and_admitted_state_distinct() {
    let pre = History {
        id: "pre".into(),
        events: vec![],
    };
    let seed = history("seed", &[]);
    let supplied = History {
        id: "supply-a".into(),
        events: vec![
            Event::Supply(Token::new("<>")),
            Event::Supply(Token::new("a")),
        ],
    };
    let admitted = history("admit-a", &["a"]);
    let p = presentation(
        vec![pre, seed, supplied, admitted],
        vec![Question::DatumCount],
    );
    assert_eq!(p.quotient().class_of, vec![0, 0, 0, 1]);
    let detailed = presentation(
        p.histories().to_vec(),
        vec![Question::DatumCount, Question::EventCount],
    );
    assert_eq!(detailed.quotient().profiles.len(), 4);
}

#[test]
fn all_admitted_regime_fields_are_observable_without_a_geometric_interpretation() {
    let mut h = history("all-fields", &["a", "b"]);
    h.events.extend([
        Event::AdmitForm(1),
        Event::AdmitInst(0, vec![Mark(0)]),
        Event::AdmitRuleAll(0),
        Event::Impose(Pair::of(0, 1)),
    ]);
    let p = presentation(
        vec![h],
        vec![
            Question::DatumCount,
            Question::FormCount,
            Question::InstanceCount,
            Question::RuleCount,
            Question::RequirementCount,
            Question::Derivable(PrimitiveInstance {
                form: 0,
                args: vec![1],
            }),
            Question::Derivable(PrimitiveInstance {
                form: 1,
                args: vec![1],
            }),
        ],
    );
    assert_eq!(
        p.family().answers()[0],
        vec![
            Answer::Count(2),
            Answer::Count(1),
            Answer::Count(1),
            Answer::Count(1),
            Answer::Count(1),
            Answer::Boolean(true),
            Answer::Unavailable
        ]
    );
}

#[test]
fn certificates_reject_lost_questions_forged_decoders_and_changed_sources() {
    let p = presentation(
        vec![history("a", &["a"]), history("b", &["b"])],
        vec![Question::HasDatum("a".into())],
    );
    let compressed = Report {
        values: vec!["same".into(); 2],
    };
    let c = p.certify_report(&compressed).unwrap();
    assert!(matches!(c.decision, ReportQueryDecision::Collision(_)));
    p.verify_report(&compressed, &c).unwrap();
    let fine = Report {
        values: vec!["a".into(), "b".into()],
    };
    let mut good = p.certify_report(&fine).unwrap();
    p.verify_report(&fine, &good).unwrap();
    if let ReportQueryDecision::Factorable(cert) = &mut good.decision {
        cert.decoder
            .insert("a".into(), vec![Answer::Boolean(false)]);
    } else {
        panic!("distinct reports must factor");
    }
    assert_eq!(
        p.verify_report(&fine, &good),
        Err(QuestionError::CertificateMismatch)
    );
    let changed = presentation(p.histories().to_vec(), vec![Question::HasDatum("b".into())]);
    assert_eq!(
        changed.verify_report(&compressed, &c),
        Err(QuestionError::CertificateMismatch)
    );
    let mut relabelled = p.histories().to_vec();
    relabelled[0].id = "different provenance".into();
    let changed = presentation(relabelled, vec![Question::HasDatum("a".into())]);
    assert_eq!(
        changed.verify_report(&compressed, &c),
        Err(QuestionError::CertificateMismatch)
    );
    assert!(p.certify_report(&Report { values: vec![] }).is_err());
}

#[test]
fn equal_present_counts_need_not_allow_the_same_future_compression() {
    let p = presentation(
        vec![history("a", &["a"]), history("b", &["b"])],
        vec![Question::DatumCount],
    );
    let suffix = [Event::AdmitDatum(Token::new("a"))];
    let c = p.continuation(&suffix).unwrap();
    assert!(matches!(c.decision, ReportQueryDecision::Collision(_)));
    p.verify_continuation(&suffix, &c).unwrap();
    assert!(p.verify_continuation(&[], &c).is_err());
    let refined = presentation(
        p.histories().to_vec(),
        vec![Question::DatumCount, Question::HasDatum("a".into())],
    );
    assert!(matches!(
        refined.continuation(&suffix).unwrap().decision,
        ReportQueryDecision::Factorable(_)
    ));
}

#[test]
fn operation_availability_is_protected_and_budget_exhaustion_is_not_unavailability() {
    let mut unary = history("unary", &["a"]);
    unary.events.push(Event::AdmitForm(1));
    let mut binary = history("binary", &["a"]);
    binary.events.push(Event::AdmitForm(2));
    let p = presentation(vec![unary.clone(), binary], vec![Question::DatumCount]);
    let suffix = [Event::AdmitInst(0, vec![Mark(0)])];
    let c = p.continuation(&suffix).unwrap();
    let ReportQueryDecision::Collision(w) = c.decision else {
        panic!("availability must differ");
    };
    assert_ne!(w.first_query.is_some(), w.second_query.is_some());
    let mut limits = QuestionLimits::default();
    limits.construction.max_events = unary.events.len();
    let bounded =
        Presentation::new(vec![unary], questions(vec![Question::DatumCount]), limits).unwrap();
    assert!(matches!(
        bounded.continuation(&suffix),
        Err(QuestionError::Source(
            ConstructionError::ResourceLimit { .. }
        ))
    ));
}

#[test]
fn local_reports_are_jointly_tested_against_the_declared_native_histories() {
    let mut same_state = history("00-replayed-again", &[]);
    same_state
        .events
        .push(Event::Supply(Token::new("unadmitted note")));
    let p = presentation(
        vec![history("00", &[]), same_state, history("11", &["a", "b"])],
        vec![
            Question::HasDatum("a".into()),
            Question::HasDatum("b".into()),
        ],
    );
    let site = p
        .report_site(&BTreeSet::from([0, 1, 2, 3]), 10_000)
        .unwrap();
    assert_eq!(
        site.presheaf()
            .descent_fiber(3, &[1, 2], &[0, 1])
            .unwrap()
            .outcome(),
        DescentOutcome::NoGlobalExtension
    );
    assert_eq!(
        site.presheaf()
            .descent_fiber(3, &[1, 2], &[0, 0])
            .unwrap()
            .outcome(),
        DescentOutcome::Ambiguous {
            global_sections: vec![0, 1]
        }
    );
    assert_eq!(
        site.presheaf()
            .descent_fiber(3, &[1, 2], &[1, 1])
            .unwrap()
            .outcome(),
        DescentOutcome::Unique { global_section: 2 }
    );
    // Enlarge H explicitly: the former obstruction disappears. No world claim.
    let mut enlarged = p.histories().to_vec();
    enlarged.push(history("01", &["b"]));
    let enlarged =
        Presentation::new(enlarged, p.questions().to_vec(), QuestionLimits::default()).unwrap();
    let site = enlarged
        .report_site(&BTreeSet::from([0, 1, 2, 3]), 10_000)
        .unwrap();
    assert_eq!(
        site.presheaf()
            .descent_fiber(3, &[1, 2], &[0, 1])
            .unwrap()
            .outcome(),
        DescentOutcome::Unique { global_section: 3 }
    );
}

#[test]
fn binary_alphabet_and_one_bit_of_entropy_require_different_premises() {
    let p = presentation(
        vec![history("a", &["a"]), history("b", &["b"])],
        vec![Question::HasDatum("a".into())],
    );
    let fair = law(&[(1, 2), (1, 2)]);
    let c = p.information(&fair, DEFAULT_FACTOR_BOUND).unwrap();
    assert_eq!(c.protected_entropy_nats, LogForm::ln_of_prime(2).unwrap());
    assert_eq!(c.discarded_entropy_nats, LogForm::zero());
    p.verify_information(&fair, DEFAULT_FACTOR_BOUND, &c)
        .unwrap();
    let biased = law(&[(3, 4), (1, 4)]);
    let b = p.information(&biased, DEFAULT_FACTOR_BOUND).unwrap();
    let expected = LogForm::ln_of_prime(2)
        .unwrap()
        .scale(&BigRational::from_integer(2.into()))
        .sub(
            &LogForm::ln_of_prime(3)
                .unwrap()
                .scale(&BigRational::new(3.into(), 4.into())),
        );
    assert_eq!(b.protected_entropy_nats, expected);
    assert_ne!(b.protected_entropy_nats, c.protected_entropy_nats);
    assert!(p
        .verify_information(&biased, DEFAULT_FACTOR_BOUND, &c)
        .is_err());
    assert_eq!(
        p.information(&law(&[(1, 1), (0, 1)]), DEFAULT_FACTOR_BOUND)
            .unwrap()
            .protected_entropy_nats,
        LogForm::zero()
    );
    let count_only = presentation(p.histories().to_vec(), vec![Question::DatumCount]);
    let lost = count_only.information(&fair, DEFAULT_FACTOR_BOUND).unwrap();
    assert_eq!(lost.protected_entropy_nats, LogForm::zero());
    assert_eq!(
        lost.discarded_entropy_nats,
        LogForm::ln_of_prime(2).unwrap()
    );
    let mut forged = c.clone();
    forged.discarded_entropy_nats = LogForm::ln_of_prime(2).unwrap();
    assert!(p
        .verify_information(&fair, DEFAULT_FACTOR_BOUND, &forged)
        .is_err());
    assert!(p
        .information(&law(&[(1, 1)]), DEFAULT_FACTOR_BOUND)
        .is_err());
}

#[test]
fn gluing_certificates_cannot_hide_ambiguity_or_substitute_a_source() {
    let p = presentation(
        vec![history("a", &["a"]), history("aa", &["a", "a"])],
        vec![Question::HasDatum("a".into()), Question::DatumCount],
    );
    let request = GluingRequest {
        contexts: BTreeSet::from([0, 1, 2, 3]),
        work_limit: 10_000,
        target: 3,
        cover: vec![1, 2],
        locals: vec![0, 0],
    };
    let mut c = p.certify_gluing(&request).unwrap();
    p.verify_gluing(&request, &c).unwrap();
    assert_eq!(c.fiber.global_sections, vec![0, 1]);
    c.fiber.global_sections.pop();
    assert_eq!(
        p.verify_gluing(&request, &c),
        Err(QuestionError::CertificateMismatch)
    );
    let c = p.certify_gluing(&request).unwrap();
    let mut excessive = request.clone();
    excessive.cover = vec![1; 99];
    excessive.cover.push(2);
    excessive.locals = vec![0; 100];
    excessive.work_limit = 1_000;
    assert_eq!(p.certify_gluing(&excessive), Err(QuestionError::Budget));
    let other = presentation(
        p.histories().to_vec(),
        vec![Question::HasDatum("b".into()), Question::DatumCount],
    );
    assert_eq!(
        other.verify_gluing(&request, &c),
        Err(QuestionError::CertificateMismatch)
    );
    let mut changed = request;
    changed.cover = vec![3];
    changed.locals = vec![0];
    assert_eq!(
        p.verify_gluing(&changed, &c),
        Err(QuestionError::CertificateMismatch)
    );
}

#[test]
fn supplied_native_question_graph_meets_boolean_computation_owner() {
    // A supplied NAND graph, not a claim that Genesis forces NAND or universality.
    let p = presentation(
        vec![
            history("00", &["out"]),
            history("01", &["b", "out"]),
            history("10", &["a", "out"]),
            history("11", &["a", "b"]),
        ],
        vec![
            Question::HasDatum("a".into()),
            Question::HasDatum("b".into()),
            Question::HasDatum("out".into()),
        ],
    );
    let graph = p
        .boolean_graph(&[0, 1], 2, ["zero".into(), "one".into()])
        .unwrap();
    graph.verify_cnf(&graph.graph_cnf()).unwrap();
    for x in 0..=1 {
        for y in 0..=1 {
            assert_eq!(graph.readout(&[x, y]).unwrap(), 1 - x * y);
        }
    }
    assert!(p
        .boolean_graph(&[0, 0], 2, ["0".into(), "1".into()])
        .is_err());
    assert!(p
        .boolean_graph(&[0, 9], 2, ["0".into(), "1".into()])
        .is_err());
    let partial = Presentation::new(
        p.histories()[..3].to_vec(),
        p.questions().to_vec(),
        QuestionLimits::default(),
    )
    .unwrap();
    assert!(partial
        .boolean_graph(&[0, 1], 2, ["0".into(), "1".into()])
        .is_err());
    let counts = presentation(p.histories().to_vec(), vec![Question::DatumCount]);
    assert!(counts
        .boolean_graph(&[0], 0, ["0".into(), "1".into()])
        .is_err());
}

#[test]
fn malformed_sources_and_scope_changes_are_never_certified() {
    let bad = History {
        id: "bad".into(),
        events: vec![Event::AdmitDatum(Token::new("a"))],
    };
    assert!(matches!(
        Presentation::new(vec![bad], vec![], QuestionLimits::default()),
        Err(QuestionError::Source(ConstructionError::MissingLiteralRoot))
    ));
    assert_eq!(
        Presentation::new(
            vec![history("same", &[]), history("same", &["a"])],
            vec![],
            QuestionLimits::default()
        ),
        Err(QuestionError::InvalidIdentity)
    );
    assert_eq!(
        Presentation::new(vec![history("", &[])], vec![], QuestionLimits::default()),
        Err(QuestionError::InvalidIdentity)
    );
    let mut limits = QuestionLimits::default();
    limits.max_answer_cells = 0;
    assert_eq!(
        Presentation::new(
            vec![history("a", &["a"])],
            questions(vec![Question::DatumCount]),
            limits
        ),
        Err(QuestionError::Budget)
    );
    let empty = presentation(vec![], vec![]);
    assert!(empty.quotient().profiles.is_empty());
    assert!(empty
        .information(&law(&[(1, 1)]), DEFAULT_FACTOR_BOUND)
        .is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_questions.rs
// Claim: urn:core:crates_rs:tests:test-genesis-questions:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord974c0772 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord974c0772` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError974c0772 {
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
impl BoundaryError974c0772 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError974c0772 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError974c0772 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord974c0772 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError974c0772> {
        if capacity_bound == 0 {
            return Err(BoundaryError974c0772::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError974c0772::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError974c0772::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_974c0772() {
    let admitted = BoundaryRecord974c0772::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord974c0772::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
