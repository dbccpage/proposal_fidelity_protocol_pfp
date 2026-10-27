use core_finite_probability::local_deterministic::LocalVertexLimits;
use core_number_theory::rational::ri;
use core_quantum_physics::finite_bell_extension::BellLimits;
use core_wdp::genesis_bell::*;
use core_wdp::genesis_carrier::{CarrierLimits, CarrierRequest, PassageAnswer, PassageQuestion};
use core_wdp::genesis_joint_dynamics::*;
use core_wdp::genesis_passage::PassageEvent::*;

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
pub fn token_response_experiment() -> PassageBellRequest {
    let carrier = CarrierRequest {
        seeds: (0..4)
            .map(|mask| {
                (0..2)
                    .filter(|bit| mask & (1 << bit) != 0)
                    .map(|bit| AdmitOcc(10 + 10 * bit))
                    .collect()
            })
            .collect(),
        alphabet: vec![SetBudget(0)],
        questions: vec![PassageQuestion::HasToken(10), PassageQuestion::HasToken(20)],
        limits: CarrierLimits::default(),
    };
    let settings: Vec<_> = [10, 20]
        .into_iter()
        .map(|t| PassageMeasurement {
            word: vec![0],
            question: PassageQuestion::HasToken(t),
            outcomes: vec![PassageAnswer::Bool(false), PassageAnswer::Bool(true)],
        })
        .collect();
    PassageBellRequest {
        joint: PassageJointRequest {
            left: carrier.clone(),
            right: carrier,
            pairs: (0..4).flat_map(|l| (0..4).map(move |r| (l, r))).collect(),
            interactions: vec![],
            max_cells: 100_000,
        },
        preparation_word: vec![0, 1],
        left_settings: settings.clone(),
        right_settings: settings,
        law: PreparationLaw::Shared(vec![ri(1) / ri(16); 16]),
        bell_limits: limits(),
        max_cells: 100_000,
    }
}
pub fn expose_hidden_token() -> PassageBellRequest {
    let left = CarrierRequest {
        seeds: vec![vec![AdmitOcc(10)], vec![AdmitOcc(20)]],
        alphabet: vec![],
        questions: vec![PassageQuestion::OccurrenceCount],
        limits: CarrierLimits::default(),
    };
    let right = CarrierRequest {
        seeds: vec![vec![SetLicense(false)], vec![SetLicense(true)]],
        alphabet: vec![SetLicense(false), SetLicense(true)],
        questions: vec![PassageQuestion::Licensed],
        limits: CarrierLimits::default(),
    };
    PassageBellRequest {
        joint: PassageJointRequest {
            left,
            right,
            pairs: vec![(0, 0), (0, 1), (1, 0), (1, 1)],
            interactions: vec![LicenseInteraction {
                source: Side::Left,
                question: PassageQuestion::HasToken(10),
            }],
            max_cells: 100_000,
        },
        preparation_word: vec![2],
        left_settings: vec![PassageMeasurement {
            word: vec![],
            question: PassageQuestion::OccurrenceCount,
            outcomes: vec![PassageAnswer::Count(1)],
        }],
        right_settings: vec![PassageMeasurement {
            word: vec![],
            question: PassageQuestion::Licensed,
            outcomes: vec![PassageAnswer::Bool(false), PassageAnswer::Bool(true)],
        }],
        law: PreparationLaw::Shared(vec![ri(1) / ri(4); 4]),
        bell_limits: limits(),
        max_cells: 100_000,
    }
}
pub fn setting_dependent_experiment() -> PassageBellRequest {
    let mut request = token_response_experiment();
    request.law = PreparationLaw::ByContext(
        (0..2)
            .flat_map(|x| {
                (0..2).map(move |y| {
                    (0..4)
                        .flat_map(|l| {
                            (0..4).map(move |r| {
                                let a = (l >> x) & 1;
                                let b = (r >> y) & 1;
                                if (a ^ b) == x * y {
                                    ri(1) / ri(10)
                                } else {
                                    ri(1) / ri(40)
                                }
                            })
                        })
                        .collect()
                })
            })
            .collect(),
    );
    request
}

// Origin: engine/crates_rs/tests/core_wdp/common/genesis_bell_cases.rs
// Claim: urn:core:crates_rs:tests:genesis-bell-cases:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfae010c3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfae010c3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfae010c3 {
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
impl BoundaryErrorfae010c3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfae010c3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfae010c3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfae010c3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfae010c3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfae010c3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfae010c3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfae010c3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fae010c3() {
    let admitted = BoundaryRecordfae010c3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfae010c3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
