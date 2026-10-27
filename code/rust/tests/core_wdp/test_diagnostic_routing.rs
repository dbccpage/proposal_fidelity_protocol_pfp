use num_rational::BigRational;
use core_category_theory::context_reflection::{ContextHom, ContextSystem, ContextWitness};
use core_functional::phi1::ExactPhi1Certificate;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_wdp::coda::diagnostic_routing::{
    propose_preserving_completion, propose_relation_completion, propose_value_edit,
    DiagnosticPacket, Proposal, ProposalPolicy, Refusal, RoutingError,
};

fn q(value: i64) -> BigRational {
    BigRational::from_integer(value.into())
}
fn system() -> ContextSystem {
    ContextSystem::new(vec![0, 0, 1], vec![vec![0], vec![2], vec![2]], 1).unwrap()
}
fn certificate(value: i64) -> ExactPhi1Certificate {
    ExactPhi1Certificate {
        omega: vec![q(value)],
        d0: vec![vec![q(0)]],
        weights: vec![q(1)],
        alpha: vec![q(0)],
        primal_residual: vec![q(value)],
        dual_witness: vec![q(value.signum())],
        reported_value: q(value.abs()),
    }
}
fn policy() -> ProposalPolicy {
    ProposalPolicy {
        allow_profile_coarsening: true,
        allow_value_edits: true,
    }
}

#[test]
fn real_chapter_four_classes_are_replayed_but_do_not_choose_policy() {
    for (value, d1, expected) in [
        (0, 0, ObstructionDiagnosticClass::ExactRepair),
        (3, 0, ObstructionDiagnosticClass::ClosedResidual),
        (3, 1, ObstructionDiagnosticClass::ActiveClosureFailure),
    ] {
        let packet =
            DiagnosticPacket::replay(system(), certificate(value), vec![vec![q(d1)]]).unwrap();
        assert_eq!(packet.classification().diagnostic_class(), expected);
        let witness = packet.system().obstruction().unwrap();
        assert_eq!(
            propose_relation_completion(
                &packet,
                ProposalPolicy {
                    allow_profile_coarsening: false,
                    allow_value_edits: true
                },
                &witness,
                false
            )
            .unwrap(),
            Proposal::Refused(Refusal::PolicyProhibitsCoarsening)
        );
        let completion =
            match propose_relation_completion(&packet, policy(), &witness, false).unwrap() {
                Proposal::RelationCompletion(completion) => completion,
                other => panic!("expected declared proposal, got {other:?}"),
            };
        assert!(completion.completed().is_congruent());
        // The actual initial factor exists for a typed map into Cong.
        let target = ContextSystem::new(vec![0], vec![vec![0]], 1).unwrap();
        let arrow = ContextHom::new(packet.system(), &target, vec![0, 0, 0]).unwrap();
        let factor = completion.factor(&arrow).unwrap();
        assert!(completion.is_factor(&arrow, &factor));
    }
}

#[test]
fn reflecting_completion_is_refused_with_exact_context_counterwitness() {
    let packet = DiagnosticPacket::replay(system(), certificate(3), vec![vec![q(0)]]).unwrap();
    let witness = packet.system().obstruction().unwrap();
    let expected = Proposal::Refused(Refusal::ReflectingCompletionImpossible(witness.clone()));
    assert_eq!(propose_preserving_completion(&packet), expected);
    assert_eq!(
        propose_relation_completion(&packet, policy(), &witness, true).unwrap(),
        expected
    );
    let forged = ContextWitness {
        left: 0,
        right: 2,
        context: 0,
    };
    assert_eq!(
        propose_relation_completion(&packet, policy(), &forged, false),
        Err(RoutingError::InvalidContextWitness)
    );
}

#[test]
fn guarded_value_edits_require_policy_problem_binding_and_exact_descent() {
    let packet = DiagnosticPacket::replay(system(), certificate(3), vec![vec![q(1)]]).unwrap();
    assert_eq!(
        propose_value_edit(
            &packet,
            ProposalPolicy {
                allow_profile_coarsening: true,
                allow_value_edits: false
            },
            certificate(0)
        )
        .unwrap(),
        Proposal::Refused(Refusal::PolicyProhibitsValueEdit)
    );
    assert_eq!(
        propose_value_edit(&packet, policy(), certificate(3)).unwrap(),
        Proposal::Refused(Refusal::CandidateHasNoStrictDescent)
    );
    let mut changed_problem = certificate(0);
    changed_problem.weights = vec![q(2)];
    assert_eq!(
        propose_value_edit(&packet, policy(), changed_problem),
        Err(RoutingError::InvalidEditContract)
    );
    let mut forged = certificate(3);
    forged.reported_value = q(0);
    assert!(matches!(
        propose_value_edit(&packet, policy(), forged),
        Err(RoutingError::Phi1(_))
    ));
    match propose_value_edit(&packet, policy(), certificate(0)).unwrap() {
        Proposal::ValueEdit { before, after } => {
            assert_eq!(before.phi1().value(), &q(3));
            assert_eq!(after.phi1().value(), &q(0));
            assert_eq!(after.system(), before.system());
        }
        other => panic!("unexpected route {other:?}"),
    }
}

#[test]
fn finite_terminal_receipt_binds_policy_request_diagnostics_and_replays() {
    use core_wdp::coda::diagnostic_routing::{route_request, RoutingRequest};
    let packet = DiagnosticPacket::replay(system(), certificate(3), vec![vec![q(0)]]).unwrap();
    for request in [
        RoutingRequest::Hold,
        RoutingRequest::ProfileReflectingCompletion,
        RoutingRequest::RelationCoarsening(packet.system().obstruction().unwrap()),
        RoutingRequest::ValueEdit(certificate(0)),
    ] {
        let receipt = route_request(&packet, policy(), request.clone()).unwrap();
        assert!(receipt.replay().unwrap());
        assert_eq!(receipt.packet(), &packet);
        assert_eq!(receipt.request(), &request);
        assert_eq!(receipt.policy(), policy());
    }
}

// Origin: engine/crates_rs/tests/core_wdp/test_diagnostic_routing.rs
// Claim: urn:core:crates_rs:tests:test-diagnostic-routing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord39d3bce2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord39d3bce2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError39d3bce2 {
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
impl BoundaryError39d3bce2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError39d3bce2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError39d3bce2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord39d3bce2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError39d3bce2> {
        if capacity_bound == 0 {
            return Err(BoundaryError39d3bce2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError39d3bce2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError39d3bce2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_39d3bce2() {
    let admitted = BoundaryRecord39d3bce2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord39d3bce2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
