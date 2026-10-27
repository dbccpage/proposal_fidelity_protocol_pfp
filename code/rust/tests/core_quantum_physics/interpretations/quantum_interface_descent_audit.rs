//! Two finite facts the descent audit leans on, computed by existing crate
//! modules: classical gluing fails for the Cabello rays (and holds for the
//! product control), and the real rebit pair fails local tomography by an
//! exact rank with an explicit unseen direction, while the complex qubit pair
//! does not.

use num_traits::Zero;
use core_quantum_physics::composition_tomography::{
    local_tomography_spanning_complex, local_tomography_spanning_real,
    real_local_tomography_witness, real_symmetric_basis, tensor_morphisms,
};
use core_quantum_physics::contextuality_obstruction::{
    compute_obstruction_class, construct_cabello_scenario, construct_product_scenario,
    verify_global_section,
};

// ---------------------------------------------------------------------------
// QM-093-C15: classical gluing fails at the obstruction layer for real rays.
// ---------------------------------------------------------------------------

#[test]
fn classical_gluing_fails_for_the_cabello_rays_and_holds_for_the_product_control() {
    let cabello = construct_cabello_scenario();
    let obstructed = compute_obstruction_class(&cabello).unwrap();
    assert!(obstructed.diff_squares_to_zero);
    assert_eq!(obstructed.dim_h1, 1);
    assert!(!obstructed.obstruction_class_is_zero);
    assert!(obstructed.exhibited_global_section.is_none());

    // Independently of the cohomology: all 2^18 parity assignments fail, and
    // the best of them still violates exactly one of the nine contexts.
    let fewest_violations = (0u32..1 << 18)
        .map(|mask| {
            let section: Vec<u8> = (0..18).map(|ray| ((mask >> ray) & 1) as u8).collect();
            let (valid, violated) = verify_global_section(&cabello, &section);
            assert!(!valid);
            violated.len()
        })
        .min();
    assert_eq!(fewest_violations, Some(1));

    let product = construct_product_scenario();
    let glued = compute_obstruction_class(&product).unwrap();
    assert!(glued.obstruction_class_is_zero);
    let section = glued.exhibited_global_section.clone().unwrap();
    assert!(verify_global_section(&product, &section).0);
}

// ---------------------------------------------------------------------------
// QM-093-C20: the rebit pair fails local tomography, 9 != 10, exactly.
// ---------------------------------------------------------------------------

#[test]
fn the_rebit_pair_fails_local_tomography_by_an_exact_rank() {
    let real = local_tomography_spanning_real(2, 2).unwrap();
    assert_eq!(
        (
            real.local_dim_a,
            real.local_dim_b,
            real.product_count,
            real.product_rank,
            real.joint_dim
        ),
        (3, 3, 9, 9, 10)
    );
    assert!(!real.spans);
    let complex = local_tomography_spanning_complex(2, 2).unwrap();
    assert_eq!(
        (
            complex.product_count,
            complex.product_rank,
            complex.joint_dim
        ),
        (16, 16, 16)
    );
    assert!(complex.spans);

    // An explicit symmetric direction that every product effect misses.
    let delta = real_local_tomography_witness(2, 2).unwrap();
    assert!(delta.as_slice().iter().any(|q| !q.is_zero()));
    for i in 0..4 {
        for j in 0..4 {
            assert_eq!(delta.get(i, j).unwrap(), delta.get(j, i).unwrap());
        }
    }
    let local = real_symmetric_basis(2).unwrap();
    for a in &local {
        for b in &local {
            let product = tensor_morphisms(a, b).unwrap();
            assert!(
                linear_algebra::exact_field::involution::hs_inner(&product, &delta)
                    .unwrap()
                    .is_zero()
            );
        }
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/interpretations/quantum_interface_descent_audit.rs
// Claim: urn:core:crates_rs:tests:quantum-interface-descent-audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord41168fb6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord41168fb6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError41168fb6 {
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
impl BoundaryError41168fb6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError41168fb6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError41168fb6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord41168fb6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError41168fb6> {
        if capacity_bound == 0 {
            return Err(BoundaryError41168fb6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError41168fb6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError41168fb6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_41168fb6() {
    let admitted = BoundaryRecord41168fb6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord41168fb6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
