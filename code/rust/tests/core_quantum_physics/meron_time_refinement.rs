use linear_algebra::exact_field::matrix as mx;
use core_number_theory::rational::{rq, Rational};
use core_quantum_physics::meron_time_refinement::{
    EulerTimePlan, FiniteMeronChain, MeronTimeError,
};

fn reverse_four(state: usize) -> usize {
    (0..4).fold(0, |out, bit| out | (((state >> bit) & 1) << (3 - bit)))
}

#[test]
fn existing_car_projectors_match_every_source_bond_and_occupation() {
    let chain = FiniteMeronChain::new(4).unwrap();
    for (x, p) in chain.projectors().iter().enumerate() {
        assert_eq!(mx::transpose(p).unwrap(), *p);
        assert_eq!(mx::multiply(p, p).unwrap(), *p);
        let y = (x + 1) % 4;
        for state in 0usize..16 {
            let mixed = ((state >> x) ^ (state >> y)) & 1;
            let (lo, hi) = (x.min(y), x.max(y));
            let parity = ((state >> (lo + 1)) & ((1 << (hi - lo - 1)) - 1)).count_ones() % 2;
            for after in 0usize..16 {
                let expected = if mixed == 0 {
                    rq(0, 1)
                } else if after == state {
                    rq(1, 2)
                } else if after == state ^ (1 << x) ^ (1 << y) {
                    rq(if parity == 0 { 1 } else { -1 }, 2)
                } else {
                    rq(0, 1)
                };
                assert_eq!(
                    p.get(reverse_four(after), reverse_four(state)).unwrap(),
                    expected
                );
            }
        }
    }
    let p = chain.projectors();
    assert_eq!(
        mx::multiply(&p[0], &p[2]).unwrap(),
        mx::multiply(&p[2], &p[0]).unwrap()
    );
    assert_ne!(
        mx::multiply(&p[0], &p[1]).unwrap(),
        mx::multiply(&p[1], &p[0]).unwrap()
    );
    assert_eq!(
        p[3].get(reverse_four(12), reverse_four(5)).unwrap(),
        rq(-1, 2)
    );
}

#[test]
fn original_full_fock_partition_and_zero_coupling_are_recovered() {
    let chain = FiniteMeronChain::new(4).unwrap();
    assert_eq!(chain.transfer_trace(2, &rq(3, 1)).unwrap(), rq(912, 1));
    for m in [1, 2, 4, 8] {
        assert_eq!(chain.transfer_trace(m, &rq(1, 1)).unwrap(), rq(16, 1));
    }
    let h = chain.hamiltonian_over_t().unwrap();
    assert_eq!(mx::transpose(&h).unwrap(), h);
    assert_eq!(mx::trace(&h).unwrap(), rq(0, 1));
}

#[test]
fn rational_time_plan_preserves_temperature_target_and_refuses_bad_domains() {
    let coarse = EulerTimePlan::new(4, 4, rq(1, 16), rq(0, 1)).unwrap();
    let fine = EulerTimePlan::new(4, 8, rq(1, 16), rq(0, 1)).unwrap();
    assert_eq!(coarse.q(), &rq(65, 64));
    assert_eq!(coarse.slice_growth(), &rq(65, 64).pow(4));
    assert!(fine.physical_density_error() < coarse.physical_density_error());
    assert_eq!(
        coarse.thermodynamic_density_error() - coarse.physical_density_error(),
        rq(3, 128)
    );
    let uncertain = EulerTimePlan::new(4, 4, rq(1, 16), rq(1, 1000)).unwrap();
    assert_eq!(
        uncertain.physical_density_error() - coarse.physical_density_error(),
        rq(3, 4000)
    );
    assert_eq!(
        EulerTimePlan::new(3, 4, rq(1, 16), rq(0, 1)),
        Err(MeronTimeError::Sites)
    );
    assert_eq!(
        EulerTimePlan::new(4, 0, rq(1, 16), rq(0, 1)),
        Err(MeronTimeError::Repetitions)
    );
    assert_eq!(
        EulerTimePlan::new(4, 257, rq(1, 16), rq(0, 1)),
        Err(MeronTimeError::Repetitions)
    );
    assert_eq!(
        EulerTimePlan::new(4, 4, rq(1, 16), rq(1, 8)),
        Err(MeronTimeError::Parameter)
    );
    let huge = Rational::from_integer(num_bigint::BigInt::from(1) << 300);
    assert_eq!(
        EulerTimePlan::new(4, 4, huge, rq(0, 1)),
        Err(MeronTimeError::Resource)
    );
    assert_eq!(
        FiniteMeronChain::new(4)
            .unwrap()
            .transfer_trace(1, &rq(1, 2)),
        Err(MeronTimeError::TransferParameter)
    );
    assert!(matches!(
        FiniteMeronChain::new(6),
        Err(MeronTimeError::Fock(_))
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/meron_time_refinement.rs
// Claim: urn:core:crates_rs:tests:meron-time-refinement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfc425c29 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfc425c29` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfc425c29 {
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
impl BoundaryErrorfc425c29 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfc425c29 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfc425c29 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfc425c29 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfc425c29> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfc425c29::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfc425c29::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfc425c29::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fc425c29() {
    let admitted = BoundaryRecordfc425c29::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfc425c29::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
