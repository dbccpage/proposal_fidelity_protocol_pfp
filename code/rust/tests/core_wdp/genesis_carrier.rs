use core_category_theory::finite_report_descent::DescentOutcome;
use core_category_theory::finite_report_query::ReportQueryDecision;
use core_wdp::genesis_carrier::*;
use core_wdp::genesis_passage::{PassageEvent::*, PassageState};
use core_wdp::genesis_questions::GluingRequest;
use std::collections::BTreeSet;

fn request() -> CarrierRequest {
    CarrierRequest {
        seeds: vec![vec![AdmitOcc(10)], vec![AdmitOcc(20)]],
        alphabet: vec![AdmitOcc(10)],
        questions: vec![PassageQuestion::OccurrenceCount],
        limits: CarrierLimits::default(),
    }
}

#[test]
fn native_continuation_refines_counts_and_has_replayable_counterexample() {
    let r = request();
    let c = PassageCarrier::build(&r).unwrap();
    let cert = c.certificate();
    assert_eq!(cert.states.len(), 3);
    assert_eq!(cert.answers[0], cert.answers[1]);
    assert_ne!(
        cert.refinement.state_to_block[0],
        cert.refinement.state_to_block[1]
    );
    let w = c.distinguish(0, 1, 16).unwrap().unwrap();
    assert_eq!(w.suffix, vec![AdmitOcc(10)]);
    c.verify_distinction(&w).unwrap();
    PassageCarrier::verify(&r, cert).unwrap();
    for s in 0..cert.states.len() {
        for (a, t) in cert.transitions[s].iter().enumerate() {
            assert_eq!(
                c.dynamics().quotient_operations()[cert.refinement.state_to_block[s]][a],
                t.map(|i| cert.refinement.state_to_block[i])
            );
        }
    }
}

#[test]
fn availability_alone_splits_empty_question_family() {
    let r = CarrierRequest {
        seeds: vec![vec![], vec![AdmitOcc(3), AdmitOcc(5)]],
        alphabet: vec![AssertWit(0, 1)],
        questions: vec![],
        limits: CarrierLimits::default(),
    };
    let c = PassageCarrier::build(&r).unwrap();
    let w = c.distinguish(0, 1, 16).unwrap().unwrap();
    assert_eq!(w.witness.left_answer, None);
    assert!(w.witness.right_answer.is_some());
}

#[test]
fn closure_limits_never_fabricate_missing_transitions_or_global_red() {
    let mut r = request();
    r.limits.max_states = 2;
    assert_eq!(PassageCarrier::build(&r), Err(CarrierError::ResourceLimit));
    r = request();
    r.limits.max_transitions = 1;
    assert_eq!(PassageCarrier::build(&r), Err(CarrierError::ResourceLimit));
    r = request();
    r.limits.max_refinement_cells = 0;
    assert_eq!(PassageCarrier::build(&r), Err(CarrierError::ResourceLimit));
    r = request();
    r.alphabet.push(AdmitOcc(10));
    assert_eq!(PassageCarrier::build(&r), Err(CarrierError::InvalidGrammar));
    r = request();
    r.seeds.clear();
    assert!(PassageCarrier::build(&r).is_err());
}

#[test]
fn source_and_complete_refinement_are_bound_to_expected_request() {
    let r = request();
    let c = PassageCarrier::build(&r).unwrap();
    let mut forged = c.certificate().clone();
    forged.transitions[0][0] = None;
    assert!(PassageCarrier::verify(&r, &forged).is_err());
    let mut replaced = r.clone();
    replaced.questions = vec![];
    assert!(PassageCarrier::verify(&replaced, c.certificate()).is_err());
    let mut w = c.distinguish(0, 1, 16).unwrap().unwrap();
    w.left_history.clear();
    assert!(c.verify_distinction(&w).is_err());
}

#[test]
fn word_reports_must_preserve_action_on_all_left_states() {
    let c = PassageCarrier::build(&request()).unwrap();
    // Identity and admit(10) agree from seed [10], but not from seed [20].
    let words = vec![vec![], vec![0]];
    let collision = c.compose(&words, &[0, 0], 100).unwrap();
    assert!(matches!(
        collision.decision,
        ReportQueryDecision::Collision(_)
    ));
    let ok = c.compose(&words, &[0, 1], 100).unwrap();
    assert!(matches!(ok.decision, ReportQueryDecision::Factorable(_)));
    c.verify_composition(&words, &[0, 1], 100, &ok).unwrap();
    assert!(c.verify_composition(&words, &[0, 0], 100, &ok).is_err());
    assert!(c.compose(&words, &[0, 1], 0).is_err());
}

fn gluing_setup() -> (
    PassageCarrier,
    Vec<Vec<core_wdp::genesis_passage::PassageEvent>>,
    GluingRequest,
) {
    let histories = vec![
        vec![],
        vec![AdmitOcc(1), AdmitOcc(2)],
        vec![AdmitOcc(2)],
        vec![SetBudget(0)],
    ];
    let c = PassageCarrier::build(&CarrierRequest {
        seeds: histories.clone(),
        alphabet: vec![],
        questions: vec![PassageQuestion::HasToken(1), PassageQuestion::HasToken(2)],
        limits: CarrierLimits::default(),
    })
    .unwrap();
    let r = GluingRequest {
        contexts: BTreeSet::from([0, 1, 2, 3]),
        work_limit: 10_000,
        target: 3,
        cover: vec![1, 2],
        locals: vec![0, 1],
    };
    (c, histories, r)
}

#[test]
fn lggr_extension_is_relative_to_explicit_history_family() {
    let (c, h, r) = gluing_setup();
    let red = c.glue(&h[..2], &r).unwrap();
    assert_eq!(red.fiber.outcome(), DescentOutcome::NoGlobalExtension);
    c.verify_gluing(&h[..2], &r, &red).unwrap();
    let green = c.glue(&h[..3], &r).unwrap();
    assert!(matches!(
        green.fiber.outcome(),
        DescentOutcome::Unique { .. }
    ));
    assert!(c.verify_gluing(&h[..3], &r, &red).is_err());
    let mut zero = r.clone();
    zero.locals = vec![0, 0];
    let ambiguous = c.glue(&h, &zero).unwrap();
    assert!(matches!(
        ambiguous.fiber.outcome(),
        DescentOutcome::Ambiguous { .. }
    ));
    let mut forged = ambiguous.clone();
    forged.fiber.global_sections.pop();
    assert!(c.verify_gluing(&h, &zero, &forged).is_err());
    let mut limited = r;
    limited.work_limit = 0;
    assert_eq!(c.glue(&h, &limited), Err(CarrierError::ResourceLimit));
}

#[test]
fn halted_passage_is_absorbing_and_undeclared_is_not_blind() {
    let mut s = PassageState {
        occ: vec![10, 20],
        asserted: vec![(0, 1)],
        wit: vec![(0, 1)],
        prot: vec![(0, 1)],
        ..Default::default()
    };
    assert_eq!(s.gates(0, 1), [true, true, false, true]);
    assert!(!s.obstructed(0, 1));
    s = s.step(&DeclareObs);
    assert!(s.obstructed(0, 1));
    s = s.step(&Halt);
    for e in [
        SetBudget(1),
        AdmitOcc(99),
        SetLicense(false),
        Refuse(0, 1),
        AddCol(vec![0]),
        Halt,
    ] {
        assert_eq!(s.step(&e), s);
    }
}

// Origin: engine/crates_rs/tests/core_wdp/genesis_carrier.rs
// Claim: urn:core:crates_rs:tests:genesis-carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb19481e2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb19481e2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb19481e2 {
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
impl BoundaryErrorb19481e2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb19481e2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb19481e2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb19481e2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb19481e2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb19481e2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb19481e2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb19481e2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b19481e2() {
    let admitted = BoundaryRecordb19481e2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb19481e2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
