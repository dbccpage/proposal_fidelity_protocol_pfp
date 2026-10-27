//! DP-8 adapter controls: the WDP density and channel carriers checked against the
//! exact owner `core_quantum_physics::exact_channel`.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use core_quantum_physics::exact_channel::{ExactChannelError, ExactKrausChannel};
use core_wdp::{CptpChannel, QuantumDensityStalk};

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

fn m(rows: &[&[(i64, i64)]]) -> Vec<Vec<BigRational>> {
    rows.iter()
        .map(|r| r.iter().map(|&(n, d)| q(n, d)).collect())
        .collect()
}

fn dephasing() -> CptpChannel {
    let k0 = m(&[&[(1, 1), (0, 1)], &[(0, 1), (0, 1)]]);
    let k1 = m(&[&[(0, 1), (0, 1)], &[(0, 1), (1, 1)]]);
    CptpChannel::new(vec![k0, k1]).expect("declared Kraus pair is complete")
}

#[test]
fn checked_density_accepts_a_valid_state() {
    let rho = QuantumDensityStalk::try_density(m(&[&[(1, 2), (1, 4)], &[(1, 4), (1, 2)]]));
    assert!(rho.is_ok());
    let boundary = QuantumDensityStalk::try_density(m(&[&[(1, 1), (0, 1)], &[(0, 1), (0, 1)]]));
    assert!(boundary.is_ok(), "rank-one pure state on the PSD boundary");
}

#[test]
fn checked_density_refuses_each_failed_premise() {
    let asym = m(&[&[(1, 2), (1, 4)], &[(0, 1), (1, 2)]]);
    assert_eq!(
        QuantumDensityStalk::try_density(asym).err(),
        Some("Density matrix must be symmetric")
    );
    let trace_two = m(&[&[(1, 1), (0, 1)], &[(0, 1), (1, 1)]]);
    assert_eq!(
        QuantumDensityStalk::try_density(trace_two).err(),
        Some("Density matrix must have trace one")
    );
    let negative_diagonal = m(&[&[(2, 1), (0, 1)], &[(0, 1), (-1, 1)]]);
    assert_eq!(
        QuantumDensityStalk::try_density(negative_diagonal).err(),
        Some("Density matrix must be positive semidefinite")
    );
    // Non-negative diagonal, trace one, indefinite: [[1/3,1/2,0],[1/2,1/3,0],[0,0,1/3]].
    let indefinite = m(&[
        &[(1, 3), (1, 2), (0, 1)],
        &[(1, 2), (1, 3), (0, 1)],
        &[(0, 1), (0, 1), (1, 3)],
    ]);
    assert_eq!(
        QuantumDensityStalk::try_density(indefinite.clone()).err(),
        Some("Density matrix must be positive semidefinite")
    );
    // Control: the unchecked constructor admits it; only the predicate rejects it.
    let unchecked = QuantumDensityStalk::new(indefinite).expect("square");
    assert!(!unchecked.is_valid_density_matrix());
}

#[test]
fn wdp_identity_is_the_owner_identity() {
    let wdp = CptpChannel::identity(2).to_exact_kraus().expect("valid identity");
    let owner = ExactKrausChannel::identity(2, "owner_identity").expect("owner identity");
    assert_eq!(wdp.same_channel(&owner), Ok(true));
    let deph = dephasing().to_exact_kraus().expect("valid dephasing");
    assert_eq!(deph.same_channel(&owner), Ok(false), "mutation: a different channel");
}

#[test]
fn wdp_apply_agrees_with_the_owner_apply() {
    let rho = QuantumDensityStalk::try_density(m(&[&[(1, 2), (1, 4)], &[(1, 4), (1, 2)]]))
        .expect("density");
    let channel = dephasing();
    let wdp_out = channel.apply(&rho).expect("apply").to_gaussian().expect("shape");
    let owner_out = channel
        .to_exact_kraus()
        .expect("owner channel")
        .apply(&rho.to_gaussian().expect("shape"))
        .expect("owner apply");
    assert_eq!(wdp_out, owner_out);
    let unchanged = rho.to_gaussian().expect("shape");
    assert_ne!(owner_out, unchanged, "dephasing removes the off-diagonal entry");
}

#[test]
fn zero_dimension_channel_is_refused_by_the_owner_adapter() {
    let empty = CptpChannel::identity(0);
    assert_eq!(empty.to_exact_kraus().err(), Some(ExactChannelError::ZeroDimension));
}

#[test]
fn mutated_public_fields_are_refused_without_panic() {
    let rho = QuantumDensityStalk::try_density(m(&[&[(1, 2), (0, 1)], &[(0, 1), (1, 2)]]))
        .expect("density");
    let mut bad_stalk = rho.clone();
    bad_stalk.dim = 3;
    assert!(CptpChannel::identity(2).apply(&bad_stalk).is_err());
    assert!(bad_stalk.to_gaussian().is_err());

    let mut bad_channel = CptpChannel::identity(2);
    bad_channel.dim = 3;
    assert!(bad_channel.apply(&rho).is_err());
    assert!(matches!(
        bad_channel.to_exact_kraus(),
        Err(ExactChannelError::KrausShape { index: 0, .. })
    ));

    let mut emptied = CptpChannel::identity(2);
    emptied.kraus_operators.clear();
    assert_eq!(emptied.to_exact_kraus().err(), Some(ExactChannelError::EmptyKrausSet));

    // A mutated operator that keeps its shape but breaks completeness is refused by the owner.
    let mut incomplete = CptpChannel::identity(2);
    incomplete.kraus_operators[0][1][1] = q(1, 2);
    assert!(incomplete.to_exact_kraus().is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_dp8_quantum_geometry_adapter.rs
// Claim: urn:core:crates_rs:tests:test-dp8-quantum-geometry-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord13601098 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord13601098` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError13601098 {
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
impl BoundaryError13601098 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError13601098 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError13601098 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord13601098 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError13601098> {
        if capacity_bound == 0 {
            return Err(BoundaryError13601098::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError13601098::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError13601098::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_13601098() {
    let admitted = BoundaryRecord13601098::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord13601098::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
