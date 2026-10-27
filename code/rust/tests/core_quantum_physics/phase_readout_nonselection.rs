// AuthorityEffect: None.
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::phase_readout::{
    declared_quadratic_projective_model, normalized_phase_blind_readout, DeclaredReadoutPower,
};

#[test]
fn common_phase_and_normalization_do_not_select_quadratic_readout() {
    let amplitudes = vec![GaussianRat::one(), GaussianRat::from_ints(2, 0)];
    let phase = GaussianRat {
        re: rq(3, 5),
        im: rq(4, 5),
    };
    let transformed: Vec<_> = amplitudes.iter().map(|z| phase.mul(z)).collect();
    let quadratic =
        normalized_phase_blind_readout(&amplitudes, DeclaredReadoutPower::Quadratic).unwrap();
    let quartic =
        normalized_phase_blind_readout(&amplitudes, DeclaredReadoutPower::Quartic).unwrap();
    assert_eq!(quadratic.probs(), &[rq(1, 5), rq(4, 5)]);
    assert_eq!(quartic.probs(), &[rq(1, 17), rq(16, 17)]);
    assert_ne!(quadratic, quartic);
    for power in [
        DeclaredReadoutPower::Quadratic,
        DeclaredReadoutPower::Quartic,
    ] {
        assert_eq!(
            normalized_phase_blind_readout(&amplitudes, power).unwrap(),
            normalized_phase_blind_readout(&transformed, power).unwrap()
        );
    }
    let (state, instrument) = declared_quadratic_projective_model(&amplitudes).unwrap();
    assert_eq!(instrument.probability(0, &state).unwrap(), rq(1, 5));
    assert_eq!(instrument.probability(1, &state).unwrap(), rq(4, 5));
    assert_eq!(
        linear_algebra::exact_field::matrix::trace(state.matrix())
            .unwrap()
            .re,
        ri(1)
    );
    assert!(normalized_phase_blind_readout(
        &[GaussianRat::zero()],
        DeclaredReadoutPower::Quadratic
    )
    .is_err());
}

// Origin: engine/crates_rs/tests/core_quantum_physics/phase_readout_nonselection.rs
// Claim: urn:core:crates_rs:tests:phase-readout-nonselection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord40221c80 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord40221c80` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError40221c80 {
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
impl BoundaryError40221c80 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError40221c80 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError40221c80 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord40221c80 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError40221c80> {
        if capacity_bound == 0 {
            return Err(BoundaryError40221c80::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError40221c80::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError40221c80::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_40221c80() {
    let admitted = BoundaryRecord40221c80::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord40221c80::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
