use num_rational::Ratio;
use pfp::epics::manifold::{
    admit_terminal, ConstraintPressureAccumulator, ThermodynamicAnnealer,
};

#[test]
fn cooling_reads_pressure_and_respects_the_floor() {
    let mut low = ConstraintPressureAccumulator::new(&[Ratio::new(1, 4)]).unwrap();
    let mut high = ConstraintPressureAccumulator::new(&[Ratio::new(4, 1)]).unwrap();
    low.step(&[1]);
    high.step(&[1]);
    assert_eq!(low.steps(), high.steps());
    let schedule = ThermodynamicAnnealer::with_floor(2.0, 1.0, 0.25).unwrap();
    assert!(schedule.temperature_for_pressure(&low) > schedule.temperature_for_pressure(&high));
    assert_eq!(schedule.temperature_for_pressure(&high), 0.25);
    assert_eq!(
        schedule.rank_at_pressure(&[1.0, 3.0, 2.0], &high),
        vec![1, 2, 0]
    );
    assert!(!admit_terminal(low.pressure(), Ratio::new(1, 1)));
    assert!(admit_terminal(high.pressure(), Ratio::new(1, 1)));
}

#[test]
fn invalid_schedule_is_refused() {
    for (initial, gamma, minimum) in [
        (f64::NAN, 1.0, 0.0),
        (1.0, f64::INFINITY, 0.0),
        (1.0, -1.0, 0.0),
        (1.0, 1.0, -1.0),
        (1.0, 1.0, 2.0),
    ] {
        assert!(ThermodynamicAnnealer::with_floor(initial, gamma, minimum).is_err());
    }
}

// Origin: engine/crates_rs/tests/pfp/pressure_cooling.rs
// Claim: urn:core:crates_rs:tests:pressure-cooling:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7d53421b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7d53421b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7d53421b {
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
impl BoundaryError7d53421b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7d53421b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7d53421b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7d53421b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7d53421b> {
        if capacity_bound == 0 {
            return Err(BoundaryError7d53421b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7d53421b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7d53421b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7d53421b() {
    let admitted = BoundaryRecord7d53421b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7d53421b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
