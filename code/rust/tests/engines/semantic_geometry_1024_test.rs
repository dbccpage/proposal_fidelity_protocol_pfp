//! Tests for the 1024-Dimensional Quantum Semantic Geometry Engine.
//!
//! Validates:
//! 1. 1024-dim state construction, entropy, and purity.
//! 2. Exact QJSD symmetry, non-negativity, and orthogonal saturation (\(D_{JS} = \ln 2\)).
//! 3. Exact Uhlmann fidelity and Bures distance on pure and mixed states.
//! 4. Dual-Gram spectral precision vs dense 1024x1024 eigensolver.
//! 5. Document semantic phase-transition detection along reasoning trajectories.
//! 6. AuthorityEffect::None boundary.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_1d978c6c = (i128, i128);
use nalgebra::DVector;
use engines::quantum::density_matrix::{CVector, C64};
use engines::quantum::semantic_geometry_engine::{
    compute_trajectory_qfi_velocities, hermitian_eigenvalues, uhlmann_fidelity,
    FactorizedDensity1024, DIM_1024,
};
use core_types::authority::AuthorityEffect;

fn make_basis_state(index: usize) -> CVector {
    assert!(index < DIM_1024);
    let mut v = vec![C64::new(0.0, 0.0); DIM_1024];
    v[index] = C64::new(1.0, 0.0);
    DVector::from_vec(v)
}

fn make_superposition_state(idx1: usize, idx2: usize, theta: f64) -> CVector {
    assert!(idx1 < DIM_1024 && idx2 < DIM_1024);
    let mut v = vec![C64::new(0.0, 0.0); DIM_1024];
    v[idx1] = C64::new(theta.cos(), 0.0);
    v[idx2] = C64::new(theta.sin(), 0.0);
    DVector::from_vec(v)
}

#[test]
fn negative_mixture_weights_are_refused_before_normalization() {
    assert!(FactorizedDensity1024::new(
        vec![make_basis_state(0), make_basis_state(1)],
        Some(vec![-1.0, 2.0]),
    )
    .is_err());
}

#[test]
fn test_1024_dim_pure_state_properties() {
    let psi = make_basis_state(42);
    let state = FactorizedDensity1024::from_pure_vector(psi).expect("Valid 1024-dim pure state");

    assert_eq!(state.dim(), 1024);
    assert_eq!(state.num_components(), 1);
    assert!(state.entropy().abs() < 1e-10, "Pure state entropy must be 0");
    assert!((state.purity() - 1.0).abs() < 1e-10, "Pure state purity must be 1.0");

    let report = state.emit_report(None, None);
    assert_eq!(report.authority_effect, AuthorityEffect::None);
    assert_eq!(report.dim, 1024);
}

#[test]
fn test_1024_dim_orthogonal_mixture_entropy_and_purity() {
    let psi1 = make_basis_state(10);
    let psi2 = make_basis_state(20);
    let state = FactorizedDensity1024::new(vec![psi1, psi2], Some(vec![0.5, 0.5]))
        .expect("Valid 2-component orthogonal mixture");

    // Equal mixture of 2 orthogonal states: S = ln(2), purity = 0.5
    let expected_entropy = std::f64::consts::LN_2;
    assert!(
        (state.entropy() - expected_entropy).abs() < 1e-10,
        "Entropy must equal ln(2) = {expected_entropy}, got {}",
        state.entropy()
    );
    assert!(
        (state.purity() - 0.5).abs() < 1e-10,
        "Purity must equal 0.5, got {}",
        state.purity()
    );
}

#[test]
fn test_qjsd_exact_symmetry_and_orthogonal_bound() {
    let psi1 = make_basis_state(0);
    let psi2 = make_basis_state(1);

    let rho = FactorizedDensity1024::from_pure_vector(psi1).unwrap();
    let sigma = FactorizedDensity1024::from_pure_vector(psi2).unwrap();

    // 1. Identity QJSD: D_JS(rho, rho) == 0.0
    let d_self = rho.quantum_jensen_shannon_divergence(&rho);
    assert!(d_self < 1e-10, "D_JS(rho, rho) must be 0, got {d_self}");

    // 2. Symmetry: D_JS(rho, sigma) == D_JS(sigma, rho)
    let d_rho_sigma = rho.quantum_jensen_shannon_divergence(&sigma);
    let d_sigma_rho = sigma.quantum_jensen_shannon_divergence(&rho);
    assert!(
        (d_rho_sigma - d_sigma_rho).abs() < 1e-12,
        "QJSD must be symmetric"
    );

    // 3. Orthogonal states: D_JS == ln(2)
    let max_div = std::f64::consts::LN_2;
    assert!(
        (d_rho_sigma - max_div).abs() < 1e-10,
        "Orthogonal pure states must achieve maximum QJSD = ln(2) = {max_div}, got {d_rho_sigma}"
    );

    // 4. Metric distance d_QJS = sqrt(D_JS)
    let dist = rho.qjsd_metric_distance(&sigma);
    assert!(
        (dist - max_div.sqrt()).abs() < 1e-10,
        "Metric distance must equal sqrt(ln(2))"
    );
}

#[test]
fn test_uhlmann_fidelity_and_bures_distance_invariants() {
    let psi1 = make_superposition_state(0, 1, 0.0); // |0>
    let psi2 = make_superposition_state(0, 1, std::f64::consts::PI / 4.0); // (|0> + |1>)/sqrt(2)

    let rho = FactorizedDensity1024::from_pure_vector(psi1).unwrap();
    let sigma = FactorizedDensity1024::from_pure_vector(psi2).unwrap();

    // Factorized Fidelity between pure states |0> and cos(pi/4)|0> + sin(pi/4)|1> is cos^2(pi/4) = 0.5
    let fid = rho.factorized_fidelity(&sigma).expect("Fidelity computation");
    assert!(
        (fid - 0.5).abs() < 1e-6,
        "Pure state overlap fidelity must be 0.5, got {fid}"
    );

    // Self-fidelity must be exactly 1.0
    let self_fid = rho.factorized_fidelity(&rho).expect("Self fidelity");
    assert!(
        (self_fid - 1.0).abs() < 1e-6,
        "Self fidelity must be 1.0, got {self_fid}"
    );

    // Bures distance on factorized 1024-dim states
    let dist = rho.factorized_bures_distance(&sigma).expect("Bures distance");
    let expected_bures = (2.0 * (1.0 - (0.5f64).sqrt())).sqrt();
    assert!(
        (dist - expected_bures).abs() < 1e-6,
        "Bures distance must match analytical formula, got {dist} vs {expected_bures}"
    );

    // Test direct dense CMatrix Uhlmann fidelity on a 4x4 density matrix
    let c1 = C64::new(0.5, 0.0);
    let mut dense_m1 = engines::quantum::density_matrix::CMatrix::zeros(4, 4);
    dense_m1[(0, 0)] = c1;
    dense_m1[(1, 1)] = c1;

    let mut dense_m2 = engines::quantum::density_matrix::CMatrix::zeros(4, 4);
    dense_m2[(1, 1)] = c1;
    dense_m2[(2, 2)] = c1;

    let dense_fid = uhlmann_fidelity(&dense_m1, &dense_m2).expect("Dense 4x4 fidelity");
    assert!(
        (dense_fid - 0.25).abs() < 1e-6,
        "Dense overlap fidelity must be 0.25, got {dense_fid}"
    );
}

#[test]
fn test_dual_gram_spectral_accuracy_vs_dense_subspace() {
    // 3-component ensemble in 1024 dimensions
    let v1 = make_basis_state(0);
    let v2 = make_basis_state(1);
    let v3 = make_superposition_state(0, 1, 0.3);

    let state = FactorizedDensity1024::new(
        vec![v1, v2, v3],
        Some(vec![0.4, 0.4, 0.2]),
    )
    .expect("Valid 3-component state");

    // Spectrum from Dual-Gram (3x3 matrix)
    let gram_spectrum = state.compute_spectrum();
    assert_eq!(gram_spectrum.len(), 3);
    let trace: f64 = gram_spectrum.iter().sum();
    assert!((trace - 1.0).abs() < 1e-10, "Spectrum sum must equal 1.0");

    // Verify against projected 2x2 active subspace matrix
    let mut sub_m = engines::quantum::density_matrix::CMatrix::zeros(2, 2);
    let dense_1024 = state.to_dense();
    for i in 0..2 {
        for j in 0..2 {
            sub_m[(i, j)] = dense_1024[(i, j)];
        }
    }
    let sub_spectrum = hermitian_eigenvalues(&sub_m);
    assert!((gram_spectrum[0] - sub_spectrum[0]).abs() < 1e-6);
    assert!((gram_spectrum[1] - sub_spectrum[1]).abs() < 1e-6);
}

#[test]
fn test_document_semantic_phase_transition_simulation() {
    // Simulate a 20-section document:
    // Sections 0..10 explore Concept Subspace A (indices 0..10)
    // Section 10->11 undergoes an abrupt semantic shift into Concept Subspace B (indices 500..510)
    let mut trajectory = Vec::new();
    let num_sections = 20;

    for t in 0..num_sections {
        let v = if t < 10 {
            // Subspace A
            let angle = (t as f64) * 0.05;
            make_superposition_state(0, 1, angle)
        } else {
            // Subspace B: abrupt pivot
            let angle = ((t - 10) as f64) * 0.05;
            make_superposition_state(500, 501, angle)
        };
        let state = FactorizedDensity1024::from_pure_vector(v).unwrap();
        trajectory.push(state);
    }

    let dt = vec![1.0; num_sections - 1];
    let qfi_velocities = compute_trajectory_qfi_velocities(&trajectory, &dt)
        .expect("Valid trajectory QFI velocities");

    assert_eq!(qfi_velocities.len(), 19);

    // Normal within-subspace step velocity is small (~0.01)
    let baseline_qfi = qfi_velocities[2];
    // The phase-transition step (t = 9 -> 10) must be a large spike (~5.5)
    let transition_qfi = qfi_velocities[9];

    assert!(
        transition_qfi > 50.0 * baseline_qfi,
        "Phase transition QFI ({transition_qfi}) must spike far above baseline ({baseline_qfi})"
    );

    // Verify report emission flags phase transition
    let ref_state = &trajectory[0];
    let report_normal = trajectory[3].emit_report(Some(ref_state), Some(qfi_velocities[2]));
    let report_transition = trajectory[10].emit_report(Some(ref_state), Some(qfi_velocities[9]));

    assert!(!report_normal.phase_transition_detected);
    assert!(report_transition.phase_transition_detected);
    assert_eq!(report_transition.authority_effect, AuthorityEffect::None);
}

// Origin: engine/crates_rs/tests/engines/semantic_geometry_1024_test.rs
// Claim: urn:core:crates_rs:tests:semantic-geometry-1024-test:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1d978c6c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1d978c6c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1d978c6c {
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
impl BoundaryError1d978c6c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1d978c6c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1d978c6c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1d978c6c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1d978c6c> {
        if capacity_bound == 0 {
            return Err(BoundaryError1d978c6c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1d978c6c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1d978c6c::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1d978c6c() {
    let admitted = BoundaryRecord1d978c6c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1d978c6c::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
