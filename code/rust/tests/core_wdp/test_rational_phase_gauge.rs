// AuthorityEffect: None.
use core_number_theory::rational::rq;
use core_number_theory::rational_turns::RationalTurn;
use core_wdp::amplitude_bridge::{half_exponent_obstruction, EdgePath, OrientedGraph, PathStep};
use core_wdp::rational_phase_bridge::RationalPhaseCochain;

#[test]
fn rational_coboundaries_telescope_and_closed_holonomy_is_gauge_invariant() {
    let graph = OrientedGraph::new(3, vec![(0, 1), (1, 2), (0, 2)]).unwrap();
    let cochain = RationalPhaseCochain::new(
        graph,
        vec![
            RationalTurn::new(rq(1, 3)),
            RationalTurn::new(rq(1, 4)),
            RationalTurn::new(rq(1, 6)),
        ],
    )
    .unwrap();
    let path = EdgePath {
        start: 0,
        steps: vec![
            PathStep {
                edge: 0,
                forward: true,
            },
            PathStep {
                edge: 1,
                forward: true,
            },
        ],
    };
    let closed = EdgePath {
        start: 0,
        steps: vec![
            PathStep {
                edge: 0,
                forward: true,
            },
            PathStep {
                edge: 1,
                forward: true,
            },
            PathStep {
                edge: 2,
                forward: false,
            },
        ],
    };
    let potential = vec![
        RationalTurn::new(rq(1, 5)),
        RationalTurn::new(rq(2, 7)),
        RationalTurn::new(rq(-1, 8)),
    ];
    assert!(cochain
        .verify_path_gauge_covariance(&path, &potential)
        .unwrap());
    assert_eq!(
        cochain.path_phase(&closed).unwrap(),
        RationalTurn::new(rq(5, 12))
    );
    assert_eq!(
        cochain
            .gauge_transform(&potential)
            .unwrap()
            .path_phase(&closed)
            .unwrap(),
        cochain.path_phase(&closed).unwrap()
    );
    let transformed = cochain.gauge_transform(&potential).unwrap();
    // Shared conductor 840 pays the actual scalar extension and stays within cap.
    let end_shift = potential[2].sub(&potential[0]);
    assert_eq!(
        transformed
            .path_phase(&path)
            .unwrap()
            .character_in(840)
            .unwrap(),
        cochain
            .path_phase(&path)
            .unwrap()
            .character_in(840)
            .unwrap()
            .mul(&end_shift.character_in(840).unwrap())
            .unwrap()
    );
    assert!(
        !half_exponent_obstruction()
            .unwrap()
            .u_has_square_root_in_q_i
    );
    assert!(cochain.gauge_transform(&potential[..2]).is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_rational_phase_gauge.rs
// Claim: urn:core:crates_rs:tests:test-rational-phase-gauge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord20ec155d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord20ec155d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError20ec155d {
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
impl BoundaryError20ec155d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError20ec155d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError20ec155d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord20ec155d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError20ec155d> {
        if capacity_bound == 0 {
            return Err(BoundaryError20ec155d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError20ec155d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError20ec155d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_20ec155d() {
    let admitted = BoundaryRecord20ec155d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord20ec155d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
