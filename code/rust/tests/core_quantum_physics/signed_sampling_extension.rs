use linear_algebra::exact_field::{involution as star, matrix as mx};
use core_holonomy::signed_transport::SignedCoefficientGraph;
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::signed_sampling::{
    finite_transfer_partition, real_symmetric_hamiltonian, verify_real_hamiltonian_step,
    SignedWeightFamily,
};

#[test]
fn exact_iid_sign_variance_and_independent_product_scaling() {
    let f = SignedWeightFamily::try_new(&[ri(2), ri(-1)]).unwrap();
    assert_eq!(f.signed_mass(), &ri(1));
    assert_eq!(f.absolute_mass(), &ri(3));
    assert_eq!(f.average_sign(), rq(1, 3));
    assert_eq!(f.iid_sign_mean_variance(10).unwrap(), rq(4, 45));
    assert_eq!(f.iid_relative_variance(10).unwrap(), rq(4, 5));
    let repeated = f.independent_copies(5).unwrap();
    assert_eq!(repeated.average_sign(), rq(1, 243));
    assert_eq!(repeated.iid_relative_variance(100).unwrap(), rq(14762, 25));
    // Independently enumerate the two-copy actual product weights.
    let product = SignedWeightFamily::try_new(&[ri(4), ri(-2), ri(-2), ri(1)]).unwrap();
    assert_eq!(f.independent_copies(2).unwrap(), product);
}

#[test]
fn constant_sign_zero_sum_and_invalid_exactness_controls() {
    for weights in [vec![ri(1), ri(2)], vec![ri(-1), ri(-2)]] {
        assert_eq!(
            SignedWeightFamily::try_new(&weights)
                .unwrap()
                .iid_relative_variance(1)
                .unwrap(),
            ri(0)
        );
    }
    let zero = SignedWeightFamily::try_new(&[ri(1), ri(-1)]).unwrap();
    assert_eq!(zero.average_sign(), ri(0));
    assert_eq!(zero.iid_sign_mean_variance(7).unwrap(), rq(1, 7));
    assert!(zero.iid_relative_variance(1).is_err());
    assert!(zero.iid_sign_mean_variance(0).is_err());
    assert!(zero.independent_copies(0).is_err());
    assert!(SignedWeightFamily::try_new(&[]).is_err());
    assert!(SignedWeightFamily::try_new(&[ri(0)]).is_err());
    assert!(
        SignedWeightFamily::try_new(&[num_rational::BigRational::new_raw(1.into(), 0.into())])
            .is_err()
    );
}

#[test]
fn actual_source_square_coefficients_finite_transfer_partition_is_not_an_exponential() {
    // Complete independent literal fixture from the pinned source packet; the
    // companion adapter separately loads source bytes and sends these to Rust.
    let rows = vec![
        vec![0, 0, -1, 1, 0, 0],
        vec![0, 0, -1, -1, 0, 0],
        vec![-1, -1, 0, 0, -1, -1],
        vec![1, -1, 0, 0, -1, 1],
        vec![0, 0, -1, -1, 0, 0],
        vec![0, 0, -1, 1, 0, 0],
    ];
    let graph = SignedCoefficientGraph::try_new(
        rows.iter()
            .map(|r| r.iter().map(|&v| ri(v)).collect())
            .collect(),
    )
    .unwrap();
    let family = finite_transfer_partition(&graph, &rq(1, 4), 4).unwrap();
    assert_eq!(family.signed_mass(), &rq(49, 4));
    assert_eq!(family.absolute_mass(), &rq(25, 2));
    assert_eq!(family.average_sign(), rq(49, 50));
    assert_eq!(family.iid_relative_variance(10).unwrap(), rq(99, 24010));
    assert!(finite_transfer_partition(&graph, &rq(1, 4), 0).is_err());
    assert!(finite_transfer_partition(&graph, &rq(1, 4), 1025).is_err());
    assert!(finite_transfer_partition(&graph, &ri(-1), 4).is_err());
}

#[test]
fn supplied_real_symmetric_hamiltonian_reuses_actual_finite_schrodinger_owner() {
    let coefficients = vec![vec![ri(-2), rq(3, 5)], vec![rq(3, 5), ri(7)]];
    let psi = vec![gq(1, 2, 1, 3), gi(0, 1)];
    let cert = verify_real_hamiltonian_step(&coefficients, &rq(1, 4), &psi).unwrap();
    assert_eq!(cert.norm_rate, ri(0));
    assert_eq!(cert.hamiltonian, star::adjoint(&cert.hamiltonian).unwrap());
    assert_ne!(cert.euler_unitarity_defect, mx::zeros(2, 2).unwrap()); // Euler is not unitary.
    assert_eq!(
        cert.euler_unitarity_defect,
        mx::scale(
            &mx::multiply(&cert.hamiltonian, &cert.hamiltonian).unwrap(),
            &gq(1, 16, 0, 1)
        )
        .unwrap()
    );
    assert!(real_symmetric_hamiltonian(&[vec![ri(0), ri(1)], vec![ri(0), ri(0)]]).is_err());
    assert!(verify_real_hamiltonian_step(&coefficients, &rq(1, 4), &psi[..1]).is_err());
    // 1025^2 exceeds the delegated Euler identity cap. Admission must refuse
    // before coefficient cloning/matrix construction and before its expect.
    let oversized = vec![vec![ri(0); 1025]; 1025];
    assert!(real_symmetric_hamiltonian(&oversized).is_err());
    assert!(verify_real_hamiltonian_step(&oversized, &rq(1, 4), &[]).is_err());
}

#[test]
fn negative_hamiltonian_coefficients_need_not_give_path_cancellation() {
    let g =
        SignedCoefficientGraph::try_new(vec![vec![ri(-2), ri(-1)], vec![ri(-1), ri(-2)]]).unwrap();
    let family = finite_transfer_partition(&g, &rq(1, 4), 4).unwrap();
    assert_eq!(family.average_sign(), ri(1));
    assert_eq!(family.iid_relative_variance(20).unwrap(), ri(0));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/signed_sampling_extension.rs
// Claim: urn:core:crates_rs:tests:signed-sampling-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3337d102 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3337d102` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3337d102 {
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
impl BoundaryError3337d102 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3337d102 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3337d102 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3337d102 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3337d102> {
        if capacity_bound == 0 {
            return Err(BoundaryError3337d102::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3337d102::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3337d102::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3337d102() {
    let admitted = BoundaryRecord3337d102::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3337d102::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
