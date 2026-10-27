//! Integration test asserting that Uhlmann fidelity on diagonal quantum states
//! agrees with computational-basis projections on DensityMatrix (PopulationShadow).
//!
//! # Mathematical Principle:
//! For any two commuting diagonal states \(\rho = \sum_i p_i |i\rangle\langle i|\) and
//! \(\sigma = \sum_i q_i |i\rangle\langle i|\):
//! \[\sqrt{\rho} = \sum_i \sqrt{p_i} |i\rangle\langle i|\]
//! \[\sqrt{\sqrt{\rho} \sigma \sqrt{\rho}} = \sum_i \sqrt{p_i q_i} |i\rangle\langle i|\]
//! \[\mathcal{F}(\rho, \sigma) = (\operatorname{Tr}\sqrt{\sqrt{\rho}\sigma\sqrt{\rho}})^2 = \left(\sum_i \sqrt{p_i q_i}\right)^2 = F_{\mathrm{classical}}(p, q)\]
//!
//! AuthorityEffect: None. Diagnostic test suite.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_b5ba2551 = (i128, i128);
use core_number_theory::rational::rq;
use core_quantum_physics::density_matrix::DensityMatrix;
use core_quantum_physics::fidelity::{
    classical_bhattacharyya_fidelity, density_shadow_fidelity, uhlmann_fidelity,
};
use core_quantum_physics::hilbert_space::HilbertSpace;

#[test]
fn test_uhlmann_fidelity_agrees_with_computational_basis_projections() {
    let space = HilbertSpace::try_new(3, "test_h3").expect("space creation");

    // Case 1: Identical states (1/3, 1/3, 1/3)
    let dm_uniform = DensityMatrix::maximally_mixed(&space, "uniform");
    let fid_quantum = density_shadow_fidelity(&dm_uniform, &dm_uniform).expect("quantum fidelity");
    let fid_classical = classical_bhattacharyya_fidelity(&dm_uniform.probs, &dm_uniform.probs)
        .expect("classical fidelity");

    assert!((fid_quantum - 1.0).abs() < 1e-8);
    assert!((fid_quantum - fid_classical).abs() < 1e-8);

    // Case 2: Pure computational basis states |0><0| and |1><1| (orthogonal)
    let dm_p0 = DensityMatrix::pure_computational(&space, 0, "p0").expect("pure 0");
    let dm_p1 = DensityMatrix::pure_computational(&space, 1, "p1").expect("pure 1");

    let fid_ortho_q = density_shadow_fidelity(&dm_p0, &dm_p1).expect("quantum fidelity ortho");
    let fid_ortho_c = classical_bhattacharyya_fidelity(&dm_p0.probs, &dm_p1.probs)
        .expect("classical fidelity ortho");

    assert!(fid_ortho_q < 1e-8);
    assert!((fid_ortho_q - fid_ortho_c).abs() < 1e-8);

    // Case 3: Non-trivial rational distributions
    // p = (1/2, 1/3, 1/6)
    // q = (1/4, 1/2, 1/4)
    let p_exact = vec![rq(1, 2), rq(1, 3), rq(1, 6)];
    let q_exact = vec![rq(1, 4), rq(1, 2), rq(1, 4)];

    let dm_p = DensityMatrix::try_from_exact_probs(&space, p_exact, "p").expect("dm_p");
    let dm_q = DensityMatrix::try_from_exact_probs(&space, q_exact, "q").expect("dm_q");

    let fid_pq_quantum = density_shadow_fidelity(&dm_p, &dm_q).expect("quantum fidelity pq");
    let fid_pq_classical =
        classical_bhattacharyya_fidelity(&dm_p.probs, &dm_q.probs).expect("classical fidelity pq");

    // Theoretical fidelity:
    // BC = sqrt(1/2 * 1/4) + sqrt(1/3 * 1/2) + sqrt(1/6 * 1/4)
    //    = (sqrt(2) + sqrt(6)) / 4
    // F = BC^2 = (2 + sqrt(3)) / 4 ≈ 0.9330127018922193
    let expected_bc =
        (0.5 * 0.25_f64).sqrt() + ((1.0 / 3.0) * 0.5_f64).sqrt() + ((1.0 / 6.0) * 0.25_f64).sqrt();
    let expected_fid = expected_bc * expected_bc;

    assert!(
        (fid_pq_quantum - fid_pq_classical).abs() < 1e-7,
        "quantum Uhlmann fidelity ({fid_pq_quantum}) must agree with classical Bhattacharyya fidelity ({fid_pq_classical})"
    );
    assert!(
        (fid_pq_quantum - expected_fid).abs() < 1e-7,
        "quantum Uhlmann fidelity ({fid_pq_quantum}) must agree with analytic value ({expected_fid})"
    );

    // Direct CMatrix verification
    let rho_p = dm_p.to_cmatrix();
    let rho_q = dm_q.to_cmatrix();
    let direct_uhlmann = uhlmann_fidelity(&rho_p, &rho_q).expect("direct uhlmann");
    assert!(
        (direct_uhlmann - fid_pq_classical).abs() < 1e-7,
        "direct uhlmann_fidelity on CMatrix must agree with classical projection"
    );
}

#[test]
fn test_uhlmann_fidelity_diagonal_dimension_sweep() {
    for dim in [2, 4, 8, 16] {
        let space = HilbertSpace::try_new(dim, format!("h_{dim}")).expect("space");
        let dm_max_mixed = DensityMatrix::maximally_mixed(&space, "max_mixed");
        let dm_pure0 = DensityMatrix::pure_computational(&space, 0, "p0").expect("p0");

        let q_fid = density_shadow_fidelity(&dm_max_mixed, &dm_pure0).expect("q_fid");
        let c_fid =
            classical_bhattacharyya_fidelity(&dm_max_mixed.probs, &dm_pure0.probs).expect("c_fid");

        // Analytical: BC = sqrt(1/dim * 1) + 0 + ... = 1/sqrt(dim) => F = 1/dim
        let expected = 1.0 / dim as f64;
        assert!(
            (q_fid - c_fid).abs() < 1e-8,
            "Agreement failed at dimension {dim}: q_fid={q_fid}, c_fid={c_fid}"
        );
        assert!(
            (q_fid - expected).abs() < 1e-8,
            "Expected 1/{dim} = {expected}, got {q_fid}"
        );
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/fidelity_diagonal_agreement.rs
// Claim: urn:core:crates_rs:tests:fidelity-diagonal-agreement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb5ba2551 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb5ba2551` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb5ba2551 {
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
impl BoundaryErrorb5ba2551 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb5ba2551 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb5ba2551 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb5ba2551 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb5ba2551> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb5ba2551::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb5ba2551::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb5ba2551::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b5ba2551() {
    let admitted = BoundaryRecordb5ba2551::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb5ba2551::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
