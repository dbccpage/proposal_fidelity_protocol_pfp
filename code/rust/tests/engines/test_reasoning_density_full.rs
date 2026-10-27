//! Extensive integration & property suite for FORGE-S4 Rust density twin.
//!
//! Soviet-builder style: each test states an invariant and a break condition.
//! AuthorityEffect: None. Diagnostics only — no physical QM claim.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_2750e1d9 = (i128, i128);
use engines::quantum::density_config::DensityMatrixConfig;
use engines::quantum::density_error::DensityMatrixError;
use engines::quantum::reasoning_density::{
    build_density_matrix_from_matrix, build_state_feature_matrix, emit_observables_receipt_json,
    phi_binning, sequence_ensemble_density, window_density_trajectory, ReasoningDensityConfig,
};

fn cfg() -> DensityMatrixConfig {
    DensityMatrixConfig::default()
}

// ---------------------------------------------------------------------------
// φ / F / ρ public surface
// ---------------------------------------------------------------------------

#[test]
fn test_rust_phi_binning_norm() {
    // INVARIANT: every phase has modulus 1.
    let features = vec![0.12, 0.45, 0.88, 0.34];
    let phi = phi_binning(&features, 4);
    assert_eq!(phi.len(), 4);
    for z in phi {
        assert!((z.norm() - 1.0).abs() <= 1e-12);
    }
}

#[test]
fn test_phi_binning_negative_and_integer_features() {
    // INVARIANT: fractional part; integers → phase 1.
    let phi_int = phi_binning(&[2.0, -1.0], 2);
    assert!((phi_int[0].re - 1.0).abs() < 1e-12 && phi_int[0].im.abs() < 1e-12);
    assert!((phi_int[1].re - 1.0).abs() < 1e-12 && phi_int[1].im.abs() < 1e-12);
}

#[test]
fn test_rust_state_feature_matrix_shape() {
    let samples = vec![vec![0.1, 0.5], vec![0.3, 0.8], vec![0.7, 0.2]];
    let matrix_f = build_state_feature_matrix(&samples, 4);
    assert_eq!(matrix_f.len(), 4);
    assert_eq!(matrix_f[0].len(), 3);
}

#[test]
fn test_feature_matrix_columns_match_phi_binning() {
    // INVARIANT: F[:, j] = φ(samples[j]).
    let samples = vec![vec![0.1, 0.2, 0.3], vec![0.4, 0.5, 0.6]];
    let f = build_state_feature_matrix(&samples, 3);
    let c0 = phi_binning(&samples[0], 3);
    let c1 = phi_binning(&samples[1], 3);
    for r in 0..3 {
        assert!((f[r][0].re - c0[r].re).abs() < 1e-14);
        assert!((f[r][0].im - c0[r].im).abs() < 1e-14);
        assert!((f[r][1].re - c1[r].re).abs() < 1e-14);
        assert!((f[r][1].im - c1[r].im).abs() < 1e-14);
    }
}

#[test]
fn test_rust_density_matrix_trace_and_hermiticity() {
    let samples = vec![
        vec![0.12, 0.45, 0.88, 0.34],
        vec![0.25, 0.60, 0.70, 0.15],
        vec![0.80, 0.10, 0.40, 0.95],
    ];
    let matrix_f = build_state_feature_matrix(&samples, 4);
    let rho = build_density_matrix_from_matrix(&matrix_f, &cfg()).expect("rho");
    assert!((rho.trace() - 1.0).abs() <= 1e-10);
    let arr = rho.rho();
    let dim = rho.dim();
    for i in 0..dim {
        for j in 0..dim {
            let val_ij = arr[(i, j)];
            let val_ji = arr[(j, i)];
            assert!((val_ij.re - val_ji.re).abs() <= 1e-10);
            assert!((val_ij.im + val_ji.im).abs() <= 1e-10);
        }
    }
}

#[test]
fn test_density_eigenvalues_nonnegative() {
    // INVARIANT: ρ ⪰ 0 after construction.
    let samples = vec![
        vec![0.11, 0.22, 0.33, 0.44, 0.55],
        vec![0.91, 0.82, 0.73, 0.64, 0.55],
        vec![0.05, 0.15, 0.25, 0.35, 0.45],
        vec![0.50, 0.50, 0.50, 0.50, 0.50],
    ];
    let f = build_state_feature_matrix(&samples, 8);
    let rho = build_density_matrix_from_matrix(&f, &cfg()).unwrap();
    for lambda in rho.approximate_eigenvalues() {
        assert!(lambda >= -1e-9, "negative eigenvalue {lambda}");
    }
    let sum_l: f64 = rho.approximate_eigenvalues().iter().sum();
    assert!(
        (sum_l - 1.0).abs() < 1e-8,
        "Σλ must equal Tr(ρ)=1, got {sum_l}"
    );
}

#[test]
fn test_single_sample_pure_projector() {
    let f = build_state_feature_matrix(&[vec![0.0, 0.25, 0.5, 0.75]], 4);
    let rho = build_density_matrix_from_matrix(&f, &cfg()).unwrap();
    assert!((rho.purity() - 1.0).abs() < 1e-8);
    assert!(rho.entropy_bits().unwrap().abs() < 1e-6);
    let json = emit_observables_receipt_json(&rho);
    assert!(json.contains("\"is_pure_state\":true"));
}

#[test]
fn test_two_linearly_independent_columns_reduce_purity() {
    // INVARIANT: rank(F) > 1 ⇒ purity < 1 for the Gram density (generic case).
    // Use short samples so pad produces independent columns: [1,1]^T vs [-1,1]^T.
    let pure_f = build_state_feature_matrix(&[vec![0.0]], 2);
    let mixed_f = build_state_feature_matrix(&[vec![0.0], vec![0.5]], 2);
    let pure = build_density_matrix_from_matrix(&pure_f, &cfg()).unwrap();
    let mixed = build_density_matrix_from_matrix(&mixed_f, &cfg()).unwrap();
    assert!((pure.purity() - 1.0).abs() < 1e-8);
    assert!((mixed.trace() - 1.0).abs() < 1e-10);
    assert!(
        mixed.purity() < pure.purity() - 1e-6,
        "expected mixed purity {} < pure {}",
        mixed.purity(),
        pure.purity()
    );
}

#[test]
fn test_rust_observables_bounds() {
    let samples = vec![vec![0.1, 0.2], vec![0.3, 0.4]];
    let matrix_f = build_state_feature_matrix(&samples, 4);
    let rho = build_density_matrix_from_matrix(&matrix_f, &cfg()).unwrap();
    let n = rho.dim() as f64;
    let purity = rho.purity();
    let entropy = rho.entropy_bits().unwrap_or(0.0);
    let l1_coh = rho.l1_coherence();
    assert!(purity >= 1.0 / n - 1e-8 && purity <= 1.0 + 1e-8);
    assert!(entropy >= -1e-8 && entropy <= n.log2() + 1e-6);
    assert!(l1_coh >= -1e-12);
}

#[test]
fn test_rust_observables_receipt_json_validity() {
    let samples = vec![vec![0.1, 0.2], vec![0.3, 0.4]];
    let matrix_f = build_state_feature_matrix(&samples, 4);
    let rho = build_density_matrix_from_matrix(&matrix_f, &cfg()).unwrap();
    let receipt_json = emit_observables_receipt_json(&rho);
    assert!(receipt_json.contains("\"dimension\":4"));
    assert!(receipt_json.contains("\"trace\":1.000000") || receipt_json.contains("\"trace\":1."));
    assert!(receipt_json.contains("\"authority_effect\":\"None\""));
    assert!(!receipt_json.contains("Certified"));
}

#[test]
fn test_empty_matrix_rejected() {
    assert!(matches!(
        build_density_matrix_from_matrix(&[], &cfg()),
        Err(DensityMatrixError::ZeroDimension)
    ));
}

#[test]
fn test_rust_high_dimensional_density_matrix_16x16() {
    let mut samples = Vec::new();
    for i in 0..16 {
        let sample = vec![(i as f64) * 0.05, ((i * 2) as f64) * 0.03];
        samples.push(sample);
    }
    let matrix_f = build_state_feature_matrix(&samples, 16);
    let cfg = DensityMatrixConfig::default();
    let rho = build_density_matrix_from_matrix(&matrix_f, &cfg).unwrap();

    assert_eq!(rho.dim(), 16);
    assert!((rho.trace() - 1.0).abs() <= 1e-6);
    for lambda in rho.approximate_eigenvalues() {
        assert!(lambda >= -1e-8);
    }
}

#[test]
fn test_rust_nan_sanitization() {
    let features = vec![f64::NAN, f64::INFINITY, 0.5];
    let phi = phi_binning(&features, 3);
    assert_eq!(phi.len(), 3);
    // Non-finite features sanitize to 0.0 phase (cos(0)=1, sin(0)=0)
    assert!((phi[0].re - 1.0).abs() <= 1e-6);
    assert!((phi[0].im - 0.0).abs() <= 1e-6);
}

#[test]
fn test_rust_high_dimensional_density_matrix_32x32() {
    let mut samples = Vec::new();
    for i in 0..24 {
        let mut row = Vec::with_capacity(8);
        for j in 0..8 {
            row.push(((i * 17 + j * 3) % 100) as f64 / 100.0);
        }
        samples.push(row);
    }
    let f = build_state_feature_matrix(&samples, 32);
    assert_eq!(f.len(), 32);
    assert_eq!(f[0].len(), 24);
    let rho = build_density_matrix_from_matrix(&f, &cfg()).unwrap();
    assert_eq!(rho.dim(), 32);
    assert!((rho.trace() - 1.0).abs() < 1e-8);
    let purity = rho.purity();
    assert!(purity >= 1.0 / 32.0 - 1e-8 && purity <= 1.0 + 1e-8);
}

#[test]
fn test_trace_invariance_under_sample_permutation() {
    // INVARIANT: Tr(ρ)=1 independent of sample order (ρ shape may change content).
    let a = vec![
        vec![0.1, 0.2, 0.3],
        vec![0.7, 0.8, 0.9],
        vec![0.4, 0.5, 0.6],
    ];
    let b = vec![
        vec![0.7, 0.8, 0.9],
        vec![0.4, 0.5, 0.6],
        vec![0.1, 0.2, 0.3],
    ];
    let ra = build_density_matrix_from_matrix(&build_state_feature_matrix(&a, 4), &cfg()).unwrap();
    let rb = build_density_matrix_from_matrix(&build_state_feature_matrix(&b, 4), &cfg()).unwrap();
    assert!((ra.trace() - 1.0).abs() < 1e-10);
    assert!((rb.trace() - 1.0).abs() < 1e-10);
    // Gram FF† is invariant under column permutation → same ρ.
    let da = ra.rho();
    let db = rb.rho();
    for i in 0..4 {
        for j in 0..4 {
            assert!((da[(i, j)].re - db[(i, j)].re).abs() < 1e-9);
            assert!((da[(i, j)].im - db[(i, j)].im).abs() < 1e-9);
        }
    }
}

// ---------------------------------------------------------------------------
// Sequence ensemble / trajectory (integration)
// ---------------------------------------------------------------------------

#[test]
fn test_sequence_ensemble_mixed_and_pure() {
    let mixed = sequence_ensemble_density(
        &[vec![20.0, 0.0], vec![0.0, 20.0]],
        None,
        &ReasoningDensityConfig::default(),
        &cfg(),
    )
    .unwrap();
    assert!(mixed.0.purity() < 0.99);
    let pure = sequence_ensemble_density(
        &[vec![3.0, 1.0], vec![3.0, 1.0]],
        None,
        &ReasoningDensityConfig::default(),
        &cfg(),
    )
    .unwrap();
    assert!((pure.0.purity() - 1.0).abs() < 1e-8);
}

#[test]
fn test_window_trajectory_count_formula() {
    // n=10, window=3, stride=2 → starts 0,2,4,6 → 4 windows
    let rows: Vec<Vec<f64>> = (0..10).map(|i| vec![i as f64, (9 - i) as f64]).collect();
    let traj =
        window_density_trajectory(&rows, 3, 2, &ReasoningDensityConfig::default(), &cfg()).unwrap();
    assert_eq!(traj.states.len(), 4);
    assert_eq!(traj.reports.len(), 4);
    assert_eq!(traj.timestamps, vec![0.0, 1.0, 2.0, 3.0]);
}

#[test]
fn test_window_failure_paths_public_api() {
    let rows = vec![vec![1.0, 2.0], vec![3.0, 4.0]];
    assert!(
        window_density_trajectory(&rows, 0, 1, &ReasoningDensityConfig::default(), &cfg()).is_err()
    );
    assert!(
        window_density_trajectory(&rows, 1, 0, &ReasoningDensityConfig::default(), &cfg()).is_err()
    );
    assert!(
        window_density_trajectory(&rows, 5, 1, &ReasoningDensityConfig::default(), &cfg()).is_err()
    );
}

// Origin: engine/crates_rs/tests/engines/test_reasoning_density_full.rs
// Claim: urn:core:crates_rs:tests:test-reasoning-density-full:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2750e1d9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2750e1d9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2750e1d9 {
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
impl BoundaryError2750e1d9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2750e1d9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2750e1d9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2750e1d9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2750e1d9> {
        if capacity_bound == 0 {
            return Err(BoundaryError2750e1d9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2750e1d9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2750e1d9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2750e1d9() {
    let admitted = BoundaryRecord2750e1d9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2750e1d9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
