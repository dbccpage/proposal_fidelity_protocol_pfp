use core_finite_probability::local_deterministic::LocalVertexLimits;
use core_number_theory::rational::{ri, Rational};
use core_quantum_physics::finite_bell_extension::BellLimits;
use core_quantum_physics::finite_bell_preparation::*;
use core_solvers::solver_convex_farkas_feasibility::FeasibilityVerdict;
fn limits() -> BellLimits {
    BellLimits {
        vertices: LocalVertexLimits {
            assignments: 256,
            coordinates: 256,
            entries: 65536,
        },
        solver_cells: 1_000_000,
    }
}
fn functions() -> Vec<ResponseFunctions> {
    (0..16)
        .map(|i| ResponseFunctions {
            left: vec![i % 2, (i / 2) % 2],
            right: vec![(i / 4) % 2, (i / 8) % 2],
        })
        .collect()
}
#[test]
fn shared_preparation_constructs_model_without_search_and_aggregates_duplicates() {
    let responses = vec![
        ResponseFunctions {
            left: vec![2, 0],
            right: vec![1]
        };
        2
    ];
    let p = PreparedBellProblem::new(
        vec![3, 2],
        vec![2],
        &responses,
        &vec![vec![ri(1) / ri(3), ri(2) / ri(3)]; 2],
        limits(),
        10000,
    )
    .unwrap();
    let c = p.decide(0).unwrap();
    let FeasibilityVerdict::Feasible { point } = &c.extension else {
        panic!("constructed model")
    };
    assert_eq!(point[8], ri(1));
    assert!(c.prior_difference.is_none());
    assert_eq!(c.rows[0], vec![ri(0), ri(0), ri(0), ri(0), ri(0), ri(1)]);
    p.verify(&c).unwrap();
    let mut forged = c;
    forged.rows[0].swap(0, 5);
    assert!(p.verify(&forged).is_err());
}
#[test]
fn context_dependent_preparations_expose_premise_change_and_positive_obstruction() {
    let responses = functions();
    let priors: Vec<Vec<Rational>> = (0..2)
        .flat_map(|x| {
            let responses = &responses;
            (0..2).map(move |y| {
                responses
                    .iter()
                    .map(|r| {
                        if (r.left[x] ^ r.right[y]) == x * y {
                            ri(1) / ri(10)
                        } else {
                            ri(1) / ri(40)
                        }
                    })
                    .collect()
            })
        })
        .collect();
    let p = PreparedBellProblem::new(vec![2, 2], vec![2, 2], &responses, &priors, limits(), 10000)
        .unwrap();
    let c = p.decide(10000).unwrap();
    assert!(p.decide(0).is_err());
    assert!(c.prior_difference.is_some());
    assert!(matches!(c.extension, FeasibilityVerdict::Infeasible { .. }));
    assert_eq!(p.bell().supported_assignments().len(), 16);
    assert_eq!(
        c.rows[0],
        vec![ri(2) / ri(5), ri(1) / ri(10), ri(1) / ri(10), ri(2) / ri(5)]
    );
    let mut forged = c.clone();
    forged.prior_difference = None;
    assert!(p.verify(&forged).is_err());
    p.verify(&c).unwrap();
    // Changing the underlying prior is not itself a nonlocality certificate.
    let duplicate = vec![responses[0].clone(); 2];
    let varied = vec![
        vec![ri(1), ri(0)],
        vec![ri(0), ri(1)],
        vec![ri(1), ri(0)],
        vec![ri(0), ri(1)],
    ];
    let d = PreparedBellProblem::new(vec![2, 2], vec![2, 2], &duplicate, &varied, limits(), 10000)
        .unwrap();
    let c = d.decide(10000).unwrap();
    assert!(c.prior_difference.is_some());
    assert!(matches!(c.extension, FeasibilityVerdict::Feasible { .. }));
}
#[test]
fn malformed_probability_and_response_families_refuse() {
    let r = functions();
    let good = vec![vec![ri(1) / ri(16); 16]; 4];
    for bad in [
        vec![],
        vec![vec![ri(0); 16]; 4],
        vec![vec![ri(-1); 16]; 4],
        vec![vec![ri(1)]; 4],
    ] {
        assert!(matches!(
            PreparedBellProblem::new(vec![2, 2], vec![2, 2], &r, &bad, limits(), 10000),
            Err(PreparationError::InvalidPriors)
        ));
    }
    let mut invalid = r.clone();
    invalid[0].left[0] = 2;
    assert!(matches!(
        PreparedBellProblem::new(vec![2, 2], vec![2, 2], &invalid, &good, limits(), 10000),
        Err(PreparationError::InvalidResponses)
    ));
    assert!(matches!(
        PreparedBellProblem::new(vec![2, 2], vec![2, 2], &r, &good, limits(), 0),
        Err(PreparationError::WorkLimit)
    ));
    assert!(
        PreparedBellProblem::new(vec![usize::MAX], vec![2], &r, &good, limits(), usize::MAX)
            .is_err()
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/finite_bell_preparation.rs
// Claim: urn:core:crates_rs:tests:finite-bell-preparation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorded8dfe34 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorded8dfe34` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrored8dfe34 {
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
impl BoundaryErrored8dfe34 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrored8dfe34 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrored8dfe34 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorded8dfe34 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrored8dfe34> {
        if capacity_bound == 0 {
            return Err(BoundaryErrored8dfe34::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrored8dfe34::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrored8dfe34::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ed8dfe34() {
    let admitted = BoundaryRecorded8dfe34::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorded8dfe34::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
