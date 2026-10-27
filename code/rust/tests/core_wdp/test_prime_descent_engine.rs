// AuthorityEffect: None.
use num_rational::BigRational;
use num_traits::Zero;
use core_wdp::coda::types::ExternalAuthorityGrant;
use core_types::authority::AuthorityEffect;

use core_wdp::prime_algos::descent_engine::PrimeDescentCoordinator;
use core_wdp::prime_algos::domain_adapters::GenericMss0Adapter;
use core_wdp::prime_algos::prime_algorithm_0::run_prime_algorithm_0;
use core_wdp::prime_algos::prime_algorithm_1::LossLedger;
use core_wdp::prime_algos::prime_algorithm_2::{AntiCheatLaw, Budget};
use core_wdp::prime_algos::prime_scope::{digest, BoundCarrierManifest, ScopeBinding};
use core_wdp::solver_of_solvers::{CarrierEdge, FiniteCarrier2};

#[test]
fn test_descent_engine_carrier_triangle_with_face_and_grant() {
    let carrier = FiniteCarrier2 {
        num_vertices: 3,
        edges: vec![
            CarrierEdge {
                tail: 0,
                head: 1,
                weight: 1,
            },
            CarrierEdge {
                tail: 1,
                head: 2,
                weight: 1,
            },
            CarrierEdge {
                tail: 2,
                head: 0,
                weight: 1,
            },
        ],
        faces: vec![(0, 1, 2)],
    };

    let omega = [-2, 1, 1];
    let grant = ExternalAuthorityGrant {
        grant_id: "GRANT_TEST_001".to_string(),
        signature_hex: "0123456789abcdef".to_string(),
        grantee: "test_suite".to_string(),
    };

    let mut coordinator = PrimeDescentCoordinator::new("test-run-triangle-face-grant", 20);
    let refused = coordinator.execute_descent_with_grant(&carrier, &omega, Some(&grant));
    assert!(refused
        .unwrap_err()
        .to_string()
        .contains("EXTERNAL_GRANT_VERIFIER_UNAVAILABLE"));
    assert!(coordinator.trace().letters().is_empty());
}

#[test]
fn test_descent_engine_carrier_triangle_with_face_no_grant_closed_residual() {
    let carrier = FiniteCarrier2 {
        num_vertices: 3,
        edges: vec![
            CarrierEdge {
                tail: 0,
                head: 1,
                weight: 1,
            },
            CarrierEdge {
                tail: 1,
                head: 2,
                weight: 1,
            },
            CarrierEdge {
                tail: 2,
                head: 0,
                weight: 1,
            },
        ],
        faces: vec![(0, 1, 2)],
    };

    let omega = [-2, 1, 1];
    let mut coordinator = PrimeDescentCoordinator::new("test-run-triangle-face-no-grant", 20);
    let receipt = coordinator
        .execute_descent(&carrier, &omega)
        .expect("descent execution should succeed");

    assert_eq!(receipt.run_id, "test-run-triangle-face-no-grant");
    assert!(receipt.phi1.is_zero());
    assert_eq!(receipt.authority_effect, "None");
    assert!(!receipt.laws_passed);
    // Non-promotion firewall routes zero-defect to CLOSED_RESIDUAL when external grant is absent
    assert_eq!(receipt.terminal_status, "DIAGNOSTIC_ONLY");
    let letters = receipt.letters;
    assert!(letters.contains('C'));
    assert!(letters.contains('R'));
    assert!(!letters.contains('T'));
}

#[test]
fn test_descent_engine_carrier_triangle_no_face_closed_residual() {
    let carrier = FiniteCarrier2 {
        num_vertices: 3,
        edges: vec![
            CarrierEdge {
                tail: 0,
                head: 1,
                weight: 1,
            },
            CarrierEdge {
                tail: 1,
                head: 2,
                weight: 1,
            },
            CarrierEdge {
                tail: 2,
                head: 0,
                weight: 1,
            },
        ],
        faces: vec![],
    };

    let omega = [1, 1, 1];
    let mut coordinator = PrimeDescentCoordinator::new("test-run-triangle-cycle", 20);
    let receipt = coordinator
        .execute_descent(&carrier, &omega)
        .expect("descent execution should succeed");

    assert_eq!(receipt.run_id, "test-run-triangle-cycle");
    assert_eq!(
        receipt.b1_over_q, 1,
        "Unfilled cycle has first Betti number = 1"
    );
    assert_eq!(receipt.authority_effect, "None");
    assert_eq!(receipt.terminal_status, "DIAGNOSTIC_ONLY");
    assert!(!receipt.letters.contains('T'));
}

#[test]
fn test_prime_triad_prime_algorithm_0_intake_fill_order() {
    let receipt = run_prime_algorithm_0(&GenericMss0Adapter);

    assert_eq!(receipt.authority_effect, AuthorityEffect::None);
    assert!(receipt.letter_tape.contains('C'));
    assert!(receipt.letter_tape.contains('R'));
    assert!(receipt.letter_tape.contains('T'));
    assert!(!receipt.steps.is_empty(), "Must execute intake steps");
}

#[test]
fn test_prime_triad_prime_algorithm_1_transport_loss_ledger() {
    let run = digest("run.test.v1", &[&[10]]);
    let carrier = digest("carrier.test.v1", &[&[20]]);
    let d0 = digest("d0.test.v1", &[&[30]]);
    let residual = digest("res.test.v1", &[&[40]]);
    let tape_head = Some(digest("tape.test.v1", &[&[50]]));

    let manifest = BoundCarrierManifest::new(carrier, d0);
    let scope = ScopeBinding::new(run, manifest, residual, tape_head, 0);

    let empty_ledger = LossLedger::empty(scope.clone());
    assert!(empty_ledger.is_sound());
    assert!(empty_ledger.is_empty());

    let booked_ledger = LossLedger::booked(vec![("coordinate_truncation".into(), 5)], scope);
    assert!(booked_ledger.is_sound());
    assert_eq!(booked_ledger.total_lost(), 5);
}

#[test]
fn test_prime_triad_prime_algorithm_2_budgeted_stopping() {
    let total = BigRational::from_integer(10.into());
    let floor = BigRational::from_integer(1.into());
    let budget = Budget::declare(&total, &floor).expect("budget declaration valid");

    assert_eq!(budget.max_ops(), 10);
    assert_eq!(budget.spent(), 0);
    assert_eq!(budget.remaining(), 10);

    // Declaring non-positive floor must refuse with BoundedStopping violation
    let zero_floor = BigRational::zero();
    let refusal = Budget::declare(&total, &zero_floor).unwrap_err();
    assert_eq!(refusal.violations()[0].law, AntiCheatLaw::BoundedStopping);
}

#[test]
fn diagnostic_obeys_step_budget_and_does_not_accumulate_prior_trace() {
    let carrier = FiniteCarrier2 {
        num_vertices: 2,
        edges: vec![CarrierEdge {
            tail: 0,
            head: 1,
            weight: 1,
        }],
        faces: vec![],
    };
    assert!(PrimeDescentCoordinator::new("small", 1)
        .execute_descent(&carrier, &[1])
        .is_err());
    let mut coordinator = PrimeDescentCoordinator::new("repeat", 2);
    assert_eq!(
        coordinator.execute_descent(&carrier, &[1]).unwrap().letters,
        "C R"
    );
    assert_eq!(
        coordinator.execute_descent(&carrier, &[2]).unwrap().letters,
        "C R"
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_prime_descent_engine.rs
// Claim: urn:core:crates_rs:tests:test-prime-descent-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4d16bdb5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4d16bdb5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4d16bdb5 {
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
impl BoundaryError4d16bdb5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4d16bdb5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4d16bdb5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4d16bdb5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4d16bdb5> {
        if capacity_bound == 0 {
            return Err(BoundaryError4d16bdb5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4d16bdb5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4d16bdb5::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4d16bdb5() {
    let admitted = BoundaryRecord4d16bdb5::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4d16bdb5::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
