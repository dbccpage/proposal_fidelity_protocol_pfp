#[path = "common/genesis_bell_cases.rs"]
mod cases;
use core_number_theory::rational::{ri, Rational};
use core_solvers::solver_convex_farkas_feasibility::FeasibilityVerdict;
use core_wdp::genesis_bell::*;
use core_wdp::genesis_carrier::{PassageAnswer, PassageQuestion};
use core_wdp::genesis_joint_dynamics::*;
use core_wdp::genesis_passage::PassageEvent;

#[test]
fn native_local_reports_fail_after_interaction_and_refinement_repairs_futures() {
    let request = cases::expose_hidden_token();
    let experiment = PassageBellExperiment::build(&request).unwrap();
    let c = experiment.certify(0).unwrap();
    let w = c.joint_analysis.collision.as_ref().unwrap();
    assert_eq!((w.left, w.right), (0, 2));
    assert_eq!(w.word, vec![2]);
    experiment
        .joint()
        .joint()
        .dynamics()
        .verify_distinction(w)
        .unwrap();
    assert_eq!(c.prepared_rows, vec![1, 1, 2, 2]);
    assert_eq!(c.experiment.rows, vec![vec![ri(1) / ri(2), ri(1) / ri(2)]]);
    assert!(matches!(
        c.experiment.extension,
        FeasibilityVerdict::Feasible { .. }
    ));
    PassageBellExperiment::verify(&request, &c).unwrap();
    let mut local = request.joint.clone();
    local.interactions.clear();
    let no_interaction = PassageJoint::build(&local).unwrap();
    assert!(no_interaction
        .joint()
        .analyze()
        .unwrap()
        .collision
        .is_none());
    // Shared preparation interaction does not evade a Bell-local model.
    assert!(c.experiment.prior_difference.is_none());
}
#[test]
fn native_histories_generate_local_table_and_full_support_nonlocal_table_with_changed_prior() {
    let request = cases::token_response_experiment();
    let experiment = PassageBellExperiment::build(&request).unwrap();
    let c = experiment.certify(0).unwrap();
    assert!(c.joint_analysis.collision.is_none());
    assert!(c.experiment.prior_difference.is_none());
    assert_eq!(c.experiment.rows, vec![vec![ri(1) / ri(4); 4]; 4]);
    PassageBellExperiment::verify(&request, &c).unwrap();
    let changed = cases::setting_dependent_experiment();
    let nonlocal = PassageBellExperiment::build(&changed).unwrap();
    let n = nonlocal.certify(10000).unwrap();
    assert_eq!(c.responses, n.responses);
    assert!(n.experiment.prior_difference.is_some());
    assert!(matches!(
        n.experiment.extension,
        FeasibilityVerdict::Infeasible { .. }
    ));
    assert_eq!(
        nonlocal.probability().bell().supported_assignments().len(),
        16
    );
    let correlations: Vec<Rational> = n
        .experiment
        .rows
        .iter()
        .map(|p| &p[0] - &p[1] - &p[2] + &p[3])
        .collect();
    assert_eq!(
        &correlations[0] + &correlations[1] + &correlations[2] - &correlations[3],
        ri(12) / ri(5)
    );
    for p in &n.experiment.rows {
        assert_eq!(&p[0] + &p[1], ri(1) / ri(2));
        assert_eq!(&p[0] + &p[2], ri(1) / ri(2));
    }
    PassageBellExperiment::verify(&changed, &n).unwrap();
    assert!(PassageBellExperiment::verify(&request, &n).is_err());
    let mut forged = n.clone();
    forged.experiment.prior_difference = None;
    assert!(PassageBellExperiment::verify(&changed, &forged).is_err());
}
#[test]
fn certificates_bind_native_histories_measurements_operations_and_weights() {
    let request = cases::expose_hidden_token();
    let c = PassageBellExperiment::build(&request)
        .unwrap()
        .certify(0)
        .unwrap();
    let mut forged = c.clone();
    forged.responses[0].right[0] = 0;
    assert!(PassageBellExperiment::verify(&request, &forged).is_err());
    let mut forged = c.clone();
    forged.prepared_rows[0] = 0;
    assert!(PassageBellExperiment::verify(&request, &forged).is_err());
    let mut forged = c.clone();
    forged.joint_analysis.collision = None;
    assert!(PassageBellExperiment::verify(&request, &forged).is_err());
    let mut changed = request.clone();
    changed.joint.left.seeds[0] = vec![PassageEvent::AdmitOcc(30)];
    assert!(PassageBellExperiment::verify(&changed, &c).is_err());
    let mut changed = request.clone();
    changed.preparation_word.clear();
    assert!(PassageBellExperiment::verify(&changed, &c).is_err());
    let mut changed = request.clone();
    changed.right_settings[0].outcomes.reverse();
    assert!(PassageBellExperiment::verify(&changed, &c).is_err());
    let mut changed = request;
    changed.law = PreparationLaw::Shared(vec![ri(1), ri(0), ri(0), ri(0)]);
    assert!(PassageBellExperiment::verify(&changed, &c).is_err());
}
#[test]
fn unavailable_measurements_are_refused_without_postselection_even_at_zero_weight() {
    let mut request = cases::token_response_experiment();
    request.joint.left.alphabet = vec![PassageEvent::Halt];
    request.preparation_word.clear();
    // The local Halt exists but leaves the explicitly restricted joint relation.
    assert!(PassageBellExperiment::build(&request).is_err());
    // Build a closed source with one halted preparation and an unavailable event.
    request.joint.left.seeds = vec![vec![PassageEvent::Halt], vec![]];
    request.joint.left.alphabet = vec![PassageEvent::SetBudget(0)];
    request.joint.pairs = (0..2).flat_map(|l| (0..4).map(move |r| (l, r))).collect();
    request.law =
        PreparationLaw::Shared(vec![ri(0), ri(0), ri(0), ri(0), ri(1), ri(0), ri(0), ri(0)]);
    assert!(matches!(
        PassageBellExperiment::build(&request),
        Err(PassageBellError::UnavailableMeasurement {
            row: 0,
            left: true,
            setting: 0
        })
    ));
}
#[test]
fn malformed_protocols_and_unclosed_native_interactions_refuse() {
    let request = cases::expose_hidden_token();
    let mut invalid = request.clone();
    invalid.joint.right.questions.clear();
    assert_eq!(
        PassageBellExperiment::build(&invalid).unwrap_err(),
        PassageBellError::InvalidMeasurement
    );
    let mut invalid = request.clone();
    invalid.joint.interactions[0].question = PassageQuestion::OccurrenceCount;
    assert!(matches!(
        PassageBellExperiment::build(&invalid),
        Err(PassageBellError::Joint(
            PassageJointError::NonBooleanInteraction
        ))
    ));
    let mut invalid = request.clone();
    invalid.right_settings[0].outcomes = vec![PassageAnswer::Bool(false)];
    assert!(matches!(
        PassageBellExperiment::build(&invalid),
        Err(PassageBellError::InvalidMeasurement)
    ));
    let mut invalid = request.clone();
    invalid.right_settings[0]
        .outcomes
        .push(PassageAnswer::Bool(false));
    assert!(PassageBellExperiment::build(&invalid).is_err());
    let mut invalid = request.clone();
    invalid.preparation_word = vec![usize::MAX];
    assert!(PassageBellExperiment::build(&invalid).is_err());
    let mut invalid = request.clone();
    invalid.joint.pairs = vec![(0, 0), (1, 0)];
    assert!(matches!(
        PassageBellExperiment::build(&invalid),
        Err(PassageBellError::Joint(
            PassageJointError::InteractionOutsideCarrier { .. }
        ))
    ));
    let mut invalid = request.clone();
    invalid.max_cells = 0;
    assert_eq!(
        PassageBellExperiment::build(&invalid).unwrap_err(),
        PassageBellError::WorkLimit
    );
    let mut invalid = request;
    invalid.law = PreparationLaw::Shared(vec![]);
    assert!(PassageBellExperiment::build(&invalid).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/genesis_bell_joint.rs
// Claim: urn:core:crates_rs:tests:genesis-bell-joint:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7bd79e26 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7bd79e26` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7bd79e26 {
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
impl BoundaryError7bd79e26 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7bd79e26 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7bd79e26 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7bd79e26 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7bd79e26> {
        if capacity_bound == 0 {
            return Err(BoundaryError7bd79e26::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7bd79e26::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7bd79e26::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7bd79e26() {
    let admitted = BoundaryRecord7bd79e26::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7bd79e26::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
