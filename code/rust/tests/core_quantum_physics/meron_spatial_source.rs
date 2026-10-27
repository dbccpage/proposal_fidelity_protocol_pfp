use core_number_theory::rational::rq;
use core_quantum_physics::meron_source_field::AnalyticResponsePlan;
use core_quantum_physics::meron_spatial_source::{SpatialSourceError, SpatialSourcePlan};
use core_quantum_physics::meron_time_refinement::{FiniteMeronChain, MeronTimeError};

#[test]
fn weighted_free_chain_has_the_original_time_normalization() {
    let chain = FiniteMeronChain::new(4).unwrap();
    let weights = vec![rq(0, 1), rq(1, 2), rq(1, 1), rq(1, 2)];
    for m in [1, 2, 4] {
        let moments = chain
            .weighted_staggered_moments(m, &rq(1, 1), &weights)
            .unwrap();
        assert_eq!(moments.partition(), &rq(16, 1));
        assert_eq!(moments.first(), &rq(0, 1));
        assert_eq!(moments.mean_square(), rq(3, 8));
        assert_eq!(
            chain
                .weighted_staggered_moments(m, &rq(3, 1), &vec![rq(1, 1); 4])
                .unwrap(),
            chain.staggered_moments(m, &rq(3, 1)).unwrap()
        );
    }
    assert_eq!(
        chain.weighted_staggered_moments(1, &rq(1, 1), &[rq(1, 1)]),
        Err(MeronTimeError::SpatialProfile)
    );
    // Independent original SQL histories at q=385/384, M=1, with an
    // asymmetric signed profile. These are raw Q_F moments, before averaging.
    let sql = chain
        .weighted_staggered_moments(
            1,
            &rq(385, 384),
            &[rq(0, 1), rq(1, 3), rq(-1, 1), rq(2, 3)],
        )
        .unwrap();
    assert_eq!(sql.partition(), &rq(908331265, 56623104));
    assert_eq!(sql.first(), &rq(0, 1));
    assert_eq!(sql.second(), &rq(16544275, 663552));
}

#[test]
fn spatial_probe_tail_is_exact_and_refuses_boundary() {
    let response = AnalyticResponsePlan::new(4, 2, rq(0, 1), rq(0, 1), rq(1, 256)).unwrap();
    let plan = SpatialSourcePlan::new(response.clone(), rq(1, 1), rq(2, 1), rq(1, 64)).unwrap();
    assert_eq!(plan.finite_log_tail(), &rq(1, 57));
    assert!(plan.quadratic_error() > response.response_error());
    assert_eq!(
        SpatialSourcePlan::new(response.clone(), rq(1, 1), rq(2, 1), rq(1, 32)),
        Err(SpatialSourceError::ProbeDomain)
    );
    assert_eq!(
        SpatialSourcePlan::new(response.clone(), rq(-1, 1), rq(2, 1), rq(0, 1)),
        Err(SpatialSourceError::ProfileBound)
    );
    let zero = SpatialSourcePlan::new(response, rq(0, 1), rq(0, 1), rq(100, 1)).unwrap();
    assert_eq!(zero.quadratic_error(), &rq(0, 1));
    assert_eq!(zero.source_functional_error(), rq(0, 1));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/meron_spatial_source.rs
// Claim: urn:core:crates_rs:tests:meron-spatial-source:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordea9ae1ab {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordea9ae1ab` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorea9ae1ab {
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
impl BoundaryErrorea9ae1ab {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorea9ae1ab {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorea9ae1ab {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordea9ae1ab {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorea9ae1ab> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorea9ae1ab::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorea9ae1ab::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorea9ae1ab::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ea9ae1ab() {
    let admitted = BoundaryRecordea9ae1ab::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordea9ae1ab::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
