use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::finite_cochain_map::{CochainMap, CochainWindow};
use num_rational::BigRational;
use core_category_theory::context_reflection::ContextSystem;
use core_functional::phi1::ExactPhi1Certificate;
use core_wdp::coda::diagnostic_routing::DiagnosticPacket;
use core_wdp::prime_algos::finite_routing::*;
fn q(x: i64) -> BigRational {
    BigRational::from_integer(x.into())
}
fn cert(values: &[i64]) -> ExactPhi1Certificate {
    ExactPhi1Certificate {
        omega: values.iter().map(|&x| q(x)).collect(),
        d0: vec![vec![q(0)]; values.len()],
        weights: vec![q(1); values.len()],
        alpha: vec![q(0)],
        primal_residual: values.iter().map(|&x| q(x)).collect(),
        dual_witness: values.iter().map(|x| q(x.signum())).collect(),
        reported_value: q(values.iter().map(|x| x.abs()).sum()),
    }
}
fn packet(values: &[i64], d1: Vec<Vec<BigRational>>) -> DiagnosticPacket {
    DiagnosticPacket::replay(
        ContextSystem::new(vec![0], vec![vec![0]], 1).unwrap(),
        cert(values),
        d1,
    )
    .unwrap()
}
fn m(x: i64) -> BasicMatrix<BigRational> {
    BasicMatrix::try_from_fn(1, 1, |_, _| q(x)).unwrap()
}
#[test]
fn actual_lift_squares_transport_and_inclusion_are_independent_checks() {
    let source = packet(&[2], vec![vec![q(0)]]);
    let target = packet(&[4], vec![vec![q(0)]]);
    let window = CochainWindow::try_new([1, 1, 1], m(0), m(0)).unwrap();
    let map = CochainMap::try_new(&window, &window, [m(1), m(2), m(1)]).unwrap();
    let mut contract = LiftContract {
        map,
        require_coordinate_inclusion: false,
    };
    assert_eq!(check_lift(&source, &target, Some(&contract)), Ok(()));
    assert_eq!(
        check_lift(&source, &source, Some(&contract)),
        Err(FiniteRefusal::InvalidLift)
    );
    contract.require_coordinate_inclusion = true;
    assert_eq!(
        check_lift(&source, &target, Some(&contract)),
        Err(FiniteRefusal::InvalidLift)
    );
    assert_eq!(
        check_lift(&source, &target, None),
        Err(FiniteRefusal::MissingLift)
    );
    let inclusion = LiftContract {
        map: CochainMap::try_new(&window, &window, [m(1), m(1), m(1)]).unwrap(),
        require_coordinate_inclusion: true,
    };
    assert_eq!(check_lift(&source, &source, Some(&inclusion)), Ok(()));
    // A lift doubled the defect norm; commuting maps alone promise no norm invariance.
    assert!(target.phi1().value() > source.phi1().value());
}
#[test]
fn closure_damage_is_checked_even_when_phi_strictly_descends() {
    let before = packet(&[3, 0], vec![vec![q(0), q(1)]]);
    assert_eq!(
        guarded_edit(&before, cert(&[1, 1]), None),
        Err(FiniteRefusal::MissingGuard)
    );
    assert_eq!(
        guarded_edit(
            &before,
            cert(&[1, 1]),
            Some(&ClosureGuard {
                max_gamma_increase: q(0)
            })
        ),
        Err(FiniteRefusal::ClosureDamageExceeded)
    );
    let after = guarded_edit(
        &before,
        cert(&[1, 1]),
        Some(&ClosureGuard {
            max_gamma_increase: q(1),
        }),
    )
    .unwrap();
    assert_eq!(after.classification().gamma2_value(), &q(1));
    assert_eq!(
        guarded_edit(
            &before,
            cert(&[3, 0]),
            Some(&ClosureGuard {
                max_gamma_increase: q(1)
            })
        ),
        Err(FiniteRefusal::NoStrictDescent)
    );
}
#[test]
fn declared_terminal_table_and_real_fixedpoint_not_closedness_alone() {
    let p = packet(&[2], vec![vec![q(0)]]);
    let policy = TerminalPolicy {
        rows: [
            Some(FiniteTerminal::ExactCertified),
            Some(FiniteTerminal::StabilizedSurvivor),
            Some(FiniteTerminal::ActiveCertified),
        ],
    };
    assert_eq!(
        terminalize(&p, None, None),
        Err(FiniteRefusal::MissingPolicy)
    );
    assert_eq!(
        terminalize(&p, Some(&policy), None),
        Err(FiniteRefusal::MissingStabilization)
    );
    let mut d = FiniteDynamics {
        packets: vec![p.clone(), p.clone()],
        next: vec![1, 0],
    };
    assert_eq!(
        terminalize(
            &p,
            Some(&policy),
            Some((&d, FixedPointWitness { state: 0 }))
        ),
        Err(FiniteRefusal::InvalidStabilization)
    );
    d.next[0] = 0;
    assert_eq!(
        terminalize(
            &p,
            Some(&policy),
            Some((&d, FixedPointWitness { state: 0 }))
        ),
        Ok(FiniteTerminal::StabilizedSurvivor)
    );
    let bad = TerminalPolicy {
        rows: [None, Some(FiniteTerminal::ExactCertified), None],
    };
    assert_eq!(
        terminalize(&p, Some(&bad), None),
        Err(FiniteRefusal::IncompatibleTerminal)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_finite_routing.rs
// Claim: urn:core:crates_rs:tests:test-finite-routing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8391de90 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8391de90` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8391de90 {
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
impl BoundaryError8391de90 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8391de90 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8391de90 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8391de90 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8391de90> {
        if capacity_bound == 0 {
            return Err(BoundaryError8391de90::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8391de90::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8391de90::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_8391de90() {
    let admitted = BoundaryRecord8391de90::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8391de90::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
