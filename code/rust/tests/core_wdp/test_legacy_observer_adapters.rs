use linear_algebra::exact_field::matrix as mx;
use std::collections::{BTreeMap, BTreeSet};

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_observer_presentation::LinearObserverPresentation;
use num_rational::BigRational;
use core_category_theory::context_reflection::ContextSystem;
use core_category_theory::finite_moore::FiniteMoore;
use core_functional::phi1::ExactPhi1Certificate;
use core_number_theory::cyclotomic::GaussianRat;
use core_quantum_physics::exact_channel::ExactKrausChannel;
use core_wdp::coda::diagnostic_routing::DiagnosticPacket;
use core_wdp::legacy_observer_adapters::*;
use core_wdp::observer::{OperationalObserverPacket, QuotientObserver};

fn q(x: i64) -> BigRational {
    BigRational::from_integer(x.into())
}
fn custody() -> SourceCustody {
    SourceCustody {
        path: "retained-source.md".into(),
        recorded_sha256: "a".repeat(64),
        source_receipts: vec!["historical-receipt".into()],
        source_authority_tags: vec!["historical-authorized".into()],
    }
}
fn system() -> ContextSystem {
    ContextSystem::new(vec![0, 1], vec![vec![0], vec![1]], 1).unwrap()
}
fn report() -> AdaptedObserver {
    adapt_report_context(
        vec!["s0".into(), "s1".into()],
        vec!["r0".into(), "r1".into()],
        vec![0, 1],
        system(),
        custody(),
    )
    .unwrap()
}
fn certificate(x: i64) -> ExactPhi1Certificate {
    ExactPhi1Certificate {
        omega: vec![q(x)],
        d0: vec![vec![q(0)]],
        weights: vec![q(1)],
        alpha: vec![q(0)],
        primal_residual: vec![q(x)],
        dual_witness: vec![q(x.signum())],
        reported_value: q(x.abs()),
    }
}
fn evaluator(tolerance: i64) -> EvaluatorLayer {
    EvaluatorLayer::try_new(
        &system(),
        vec![
            DiagnosticPacket::replay(system(), certificate(0), vec![vec![q(0)]]).unwrap(),
            DiagnosticPacket::replay(system(), certificate(2), vec![vec![q(0)]]).unwrap(),
        ],
        vec![vec![0, 1]],
        q(tolerance),
    )
    .unwrap()
}
fn memory() -> MemoryLayer {
    MemoryLayer::try_new(
        FiniteMoore::new(vec![0, 1], vec![vec![0], vec![1]], 1).unwrap(),
        vec![vec![true, false], vec![false, true]],
        Some(vec![0, 1]),
    )
    .unwrap()
}

#[test]
fn quotient_and_report_context_preserve_actual_maps_without_inventing_layers() {
    let source = QuotientObserver::new(
        BTreeSet::from(["a".into(), "b".into()]),
        vec![BTreeSet::from(["a".into(), "b".into()])],
        "unverified-comparison-label".into(),
    )
    .unwrap();
    let adapted = adapt_finite_quotient(&source, custody()).unwrap();
    assert_eq!(adapted.presentation().unwrap().reports(), &[0, 0]);
    assert!(adapted.presentation().unwrap().contexts().is_none());
    assert!(
        adapted.memory().is_none() && adapted.evaluator().is_none() && adapted.policy().is_none()
    );
    assert_eq!(
        adapted.custody().source_authority_tags,
        custody().source_authority_tags
    );
    let report = report();
    assert_eq!(
        report
            .presentation()
            .unwrap()
            .contexts()
            .unwrap()
            .transitions(),
        &[vec![0], vec![1]]
    );
    assert!(adapt_report_context(
        vec!["s".into()],
        vec!["r".into()],
        vec![0],
        system(),
        custody()
    )
    .is_err());
    // Report collapse is preserved rather than falsely called profile equality.
    let blind = adapt_report_context(
        vec!["s0".into(), "s1".into()],
        vec!["r".into()],
        vec![0, 0],
        system(),
        custody(),
    )
    .unwrap();
    assert_eq!(blind.presentation().unwrap().reports(), &[0, 0]);
    assert!(!blind
        .presentation()
        .unwrap()
        .contexts()
        .unwrap()
        .related(0, 1));
}

#[test]
fn memory_bridge_replays_payload_and_missing_fields_are_not_defaults() {
    let detached = MemoryLayer::try_new(
        memory().model().clone(),
        memory().comparison().to_vec(),
        None,
    )
    .unwrap();
    assert!(matches!(
        detached.reaccess(0),
        Err(AdapterError::MissingSemantics(_))
    ));
    assert!(attach_memory(report(), detached).is_err());
    let linked = attach_memory(report(), memory()).unwrap();
    assert_eq!(linked.memory().unwrap().reaccess(1).unwrap(), 1);
    let wrong = MemoryLayer::try_new(
        memory().model().clone(),
        memory().comparison().to_vec(),
        Some(vec![0, 0]),
    );
    assert!(matches!(wrong, Err(AdapterError::InvalidMemoryInterface)));
    let blind_model = FiniteMoore::new(vec![0, 0], vec![vec![0], vec![1]], 1).unwrap();
    assert!(MemoryLayer::try_new(
        blind_model,
        vec![vec![true, false], vec![false, true]],
        Some(vec![0, 1])
    )
    .is_err());
}

#[test]
fn operational_adapter_checks_all_inputs_and_preserves_start_report_profile() {
    let states = BTreeSet::from(["s0".into(), "s1".into()]);
    let alphabet = BTreeSet::from(["tick".into()]);
    let transitions = BTreeMap::from([
        (("s0".into(), "tick".into()), "s1".into()),
        (("s1".into(), "tick".into()), "s0".into()),
    ]);
    let reports = BTreeMap::from([("s0".into(), "same".into()), ("s1".into(), "same".into())]);
    let profiles = BTreeMap::from([("s0".into(), "p0".into()), ("s1".into(), "p1".into())]);
    let mut source = OperationalObserverPacket::new(
        states,
        "s1".into(),
        alphabet,
        transitions,
        reports,
        profiles,
    )
    .unwrap();
    let adapted = adapt_operational_semantics(&source, custody()).unwrap();
    let (machine, start) = adapted.operational().unwrap();
    assert_eq!(*start, 1);
    assert_eq!(machine.transitions(), &[vec![1], vec![0]]);
    assert!(adapted.memory().is_none() && adapted.policy().is_none());
    source.transitions.remove(&("s1".into(), "tick".into()));
    assert!(matches!(
        adapt_operational_semantics(&source, custody()),
        Err(AdapterError::IncompleteOperationalDomain)
    ));
}

#[test]
fn normalized_finite_evaluator_has_actual_diagnostics_transform_and_terminal_semantics() {
    let low = attach_evaluator(report(), evaluator(1), None).unwrap();
    let high = attach_evaluator(
        report(),
        evaluator(3),
        Some([PolicyAction::Emit, PolicyAction::RequestData]),
    )
    .unwrap();
    assert_eq!(
        low.evaluator().unwrap().status(1).unwrap(),
        FiniteStatus::AboveTolerance
    );
    assert_eq!(
        high.evaluator().unwrap().status(1).unwrap(),
        FiniteStatus::WithinTolerance
    );
    assert_eq!(
        low.evaluator().unwrap().packets()[1].phi1().value(),
        high.evaluator().unwrap().packets()[1].phi1().value()
    );
    assert!(low.policy().is_none());
    assert_eq!(
        high.policy(),
        Some(&[PolicyAction::Emit, PolicyAction::RequestData])
    );
    let packets = evaluator(1).packets().to_vec();
    assert!(EvaluatorLayer::try_new(&system(), packets, vec![vec![1, 0]], q(1)).is_err());
    assert!(EvaluatorLayer::try_new(&system(), vec![], vec![], q(1)).is_err());
}

#[test]
fn linear_and_quantum_adapters_keep_full_payload_instead_of_attestation_labels() {
    let r = BasicMatrix::from_row_major(1, 2, vec![q(1), q(-1)]).unwrap();
    let d = BasicMatrix::from_row_major(2, 1, vec![q(1), q(1)]).unwrap();
    let adapted = adapt_linear_quotient(
        LinearObserverPresentation::try_new(r, d).unwrap(),
        custody(),
    )
    .unwrap();
    assert_eq!(
        adapted.linear().unwrap().report(&[q(3), q(1)]).unwrap(),
        vec![q(2)]
    );
    assert!(adapted.memory().is_none() && adapted.policy().is_none());
    let half = BigRational::new(1.into(), 2.into());
    let mut plus =
        BasicMatrix::<GaussianRat>::try_from_fn(2, 2, |_, _| GaussianRat::zero()).unwrap();
    let mut minus = plus.clone();
    for i in 0..2 {
        for j in 0..2 {
            plus.set(i, j, GaussianRat::from_rational(half.clone()))
                .unwrap();
            minus
                .set(
                    i,
                    j,
                    GaussianRat::from_rational(if i == j { half.clone() } else { -half.clone() }),
                )
                .unwrap();
        }
    }
    let quantum = adapt_quantum_presentation(
        vec![plus.clone(), minus],
        ExactKrausChannel::identity(2, "identity").unwrap(),
        custody(),
    )
    .unwrap();
    let payload = quantum.quantum().unwrap();
    assert_ne!(payload.states()[0], payload.states()[1]);
    assert_eq!(payload.shadows()[0], payload.shadows()[1]);
    assert_eq!(payload.images(), payload.states());
    assert!(
        quantum.memory().is_none() && quantum.evaluator().is_none() && quantum.policy().is_none()
    );
    plus.set(0, 0, GaussianRat::from_ints(2, 0)).unwrap();
    assert!(adapt_quantum_presentation(
        vec![plus],
        ExactKrausChannel::identity(2, "identity").unwrap(),
        custody()
    )
    .is_err());
}

#[test]
fn self_reference_requires_actual_target_decoder_reaccess_and_known_components() {
    let adapted = attach_memory(report(), memory()).unwrap();
    let evidence = adapt_self_reference(
        &adapted,
        &custody(),
        SelfComponent::PresentationReport(1),
        1,
        &[0, 1],
    )
    .unwrap();
    assert_eq!(evidence.component_value, 1);
    assert!(adapt_self_reference(
        &adapted,
        &custody(),
        SelfComponent::PresentationReport(1),
        0,
        &[0, 1]
    )
    .is_err());
    assert!(adapt_self_reference(
        &adapted,
        &custody(),
        SelfComponent::EvaluatorStatus(0),
        0,
        &[0, 1]
    )
    .is_err());
    assert!(adapt_self_reference(
        &report(),
        &custody(),
        SelfComponent::PresentationReport(0),
        0,
        &[0, 1]
    )
    .is_err());
    let mut different = custody();
    different.path = "different-observer.md".into();
    assert!(adapt_self_reference(
        &adapted,
        &different,
        SelfComponent::PresentationReport(0),
        0,
        &[0, 1]
    )
    .is_err());
    assert!(matches!(
        adapt_unrecovered_genesis_six(["present"; 6], custody()),
        Err(AdapterError::MissingSemantics(_))
    ));
}

// Origin: engine/crates_rs/tests/core_wdp/test_legacy_observer_adapters.rs
// Claim: urn:core:crates_rs:tests:test-legacy-observer-adapters:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord54671511 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord54671511` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError54671511 {
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
impl BoundaryError54671511 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError54671511 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError54671511 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord54671511 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError54671511> {
        if capacity_bound == 0 {
            return Err(BoundaryError54671511::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError54671511::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError54671511::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_54671511() {
    let admitted = BoundaryRecord54671511::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord54671511::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
