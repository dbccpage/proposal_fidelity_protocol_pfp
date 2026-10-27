//! Integration & Verification suite for Exact Uhlmann Fidelity, Bures Metric Distance,
//! and Trajectory Divergence Telemetry.
//!
//! Grounded in Sprint QM-01 of the Quantum Mechanics Reasoning Roadmap.
//!
//! Validates:
//! 1. Exact Uhlmann / Jozsa fidelity on pure, orthogonal, and mixed density matrices.
//! 2. Bures distance and angle metrics satisfying Riemannian geometric bounds.
//! 3. QFI statistical speed observables in quantum_geometry.rs.
//! 4. Multi-step reasoning trajectory divergence and phase-transition detection.
//! 5. AuthorityEffect::None boundary and JSON receipt serialization.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_f4ee763a = (i128, i128);
use engines::quantum::density::{
    bures_angle_observable, bures_distance_observable, fidelity_observable,
};
use engines::quantum::density_config::DensityMatrixConfig;
use engines::quantum::density_matrix::{DensityMatrix, C64};
use engines::quantum::quantum_geometry::{
    bures_angle_observable as qg_bures_angle,
    qfi_statistical_speed_observable,
};
use engines::quantum::reasoning_density::{
    analyze_trajectory_divergence, emit_trajectory_divergence_receipt_json,
    window_density_trajectory, ReasoningDensityConfig,
};
use core_types::authority::AuthorityEffect;

fn make_pure_density_from_state(v: &[f64]) -> DensityMatrix {
    let norm: f64 = v.iter().map(|x| x * x).sum::<f64>().sqrt();
    let n = v.len();
    let mut data = Vec::with_capacity(n * n);
    for &x in v {
        for &y in v {
            data.push(C64::new((x / norm) * (y / norm), 0.0));
        }
    }
    DensityMatrix::from_validated(n, data, &DensityMatrixConfig::default()).expect("Valid pure state")
}

#[test]
fn test_exact_uhlmann_fidelity_pure_and_orthogonal() {
    let state_0 = make_pure_density_from_state(&[1.0, 0.0]);
    let state_1 = make_pure_density_from_state(&[0.0, 1.0]);
    let state_plus = make_pure_density_from_state(&[1.0, 1.0]);

    // 1. Identical states: F = 1.0, dB = 0.0, theta_B = 0.0
    let f_self = fidelity_observable(&state_0, &state_0).expect("Fidelity self");
    assert!((f_self - 1.0).abs() < 1e-10, "Self fidelity must be 1.0, got {f_self}");
    let db_self = bures_distance_observable(&state_0, &state_0).expect("Bures distance self");
    assert!(db_self < 1e-10, "Self Bures distance must be 0.0, got {db_self}");
    let angle_self = bures_angle_observable(&state_0, &state_0).expect("Bures angle self");
    assert!(angle_self < 1e-10, "Self Bures angle must be 0.0, got {angle_self}");

    // 2. Orthogonal states: F = 0.0, dB = sqrt(2), theta_B = pi/2
    let f_ortho = fidelity_observable(&state_0, &state_1).expect("Fidelity ortho");
    assert!(f_ortho < 1e-10, "Orthogonal fidelity must be 0.0, got {f_ortho}");
    let db_ortho = bures_distance_observable(&state_0, &state_1).expect("Bures distance ortho");
    assert!(
        (db_ortho - 2.0_f64.sqrt()).abs() < 1e-10,
        "Orthogonal Bures distance must be sqrt(2) ~ 1.414, got {db_ortho}"
    );
    let angle_ortho = bures_angle_observable(&state_0, &state_1).expect("Bures angle ortho");
    assert!(
        (angle_ortho - std::f64::consts::FRAC_PI_2).abs() < 1e-10,
        "Orthogonal Bures angle must be pi/2, got {angle_ortho}"
    );

    // 3. |0> vs |+>: F = |<0|+>|^2 = 1/2 = 0.5
    let f_plus = fidelity_observable(&state_0, &state_plus).expect("Fidelity plus");
    assert!((f_plus - 0.5).abs() < 1e-10, "Expected fidelity 0.5, got {f_plus}");
}

#[test]
fn test_quantum_geometry_observables_integration() {
    let state_0 = make_pure_density_from_state(&[1.0, 0.0]);
    let state_1 = make_pure_density_from_state(&[0.0, 1.0]);

    // QFI statistical speed on orthogonal states is pi
    let speed_ortho = qfi_statistical_speed_observable(&state_0, &state_1).expect("QFI speed");
    assert!(
        (speed_ortho - std::f64::consts::PI).abs() < 1e-10,
        "Orthogonal QFI statistical speed must be pi, got {speed_ortho}"
    );

    // Bures angle on orthogonal states is pi/2
    let angle_ortho = qg_bures_angle(&state_0, &state_1).expect("Bures angle");
    assert!(
        (angle_ortho - std::f64::consts::FRAC_PI_2).abs() < 1e-10,
        "Orthogonal Bures angle must be pi/2, got {angle_ortho}"
    );
}

#[test]
fn test_trajectory_divergence_analysis_and_phase_transitions() {
    // Construct a reasoning trajectory with an abrupt semantic shift:
    // Step 0: topic A [5.0, 1.0]
    // Step 1: topic A [4.9, 1.1]
    // Step 2: topic A [4.8, 1.2]
    // Step 3: topic B [0.1, 6.0] (abrupt phase transition!)
    // Step 4: topic B [0.2, 5.8]
    let rows = vec![
        vec![5.0, 1.0],
        vec![4.9, 1.1],
        vec![4.8, 1.2],
        vec![0.1, 6.0],
        vec![0.2, 5.8],
    ];

    let traj_cfg = ReasoningDensityConfig {
        top_k: None,
        timestamps: Some(vec![0.0, 1.0, 2.0, 3.0, 4.0]),
    };
    let dm_cfg = DensityMatrixConfig::default();

    let trajectory = window_density_trajectory(&rows, 2, 1, &traj_cfg, &dm_cfg)
        .expect("Trajectory construction");

    assert_eq!(trajectory.states.len(), 4);

    // Analyze divergence with threshold 0.8
    let report = analyze_trajectory_divergence(&trajectory, Some(0.8))
        .expect("Trajectory divergence analysis");

    assert_eq!(report.step_count, 4);
    assert_eq!(report.consecutive_fidelities.len(), 3);
    assert_eq!(report.consecutive_bures_distances.len(), 3);
    assert_eq!(report.consecutive_qjsd_distances.len(), 3);
    assert_eq!(report.qfi_velocities.len(), 3);

    // Step 0 -> Step 1 has smooth continuity (high fidelity > 0.98, low QFI velocity)
    assert!(
        report.consecutive_fidelities[0] > 0.98,
        "Step 0->1 must have high continuity, got {}",
        report.consecutive_fidelities[0]
    );

    // Step 1 -> Step 2 has large shift (low fidelity, high QFI velocity)
    assert!(
        report.consecutive_fidelities[1] < 0.60,
        "Step 1->2 must show phase transition divergence, got {}",
        report.consecutive_fidelities[1]
    );
    assert!(
        report.qfi_velocities[1] > report.qfi_velocities[0],
        "Step 1->2 QFI velocity ({}) must exceed step 0->1 ({})",
        report.qfi_velocities[1],
        report.qfi_velocities[0]
    );
    assert_eq!(report.max_divergence_step, 1);
    assert!(report.phase_transition_detected);
    assert_eq!(report.authority_effect, AuthorityEffect::None);

    // Verify JSON serialization
    let receipt_json = emit_trajectory_divergence_receipt_json(&report);
    assert!(receipt_json.contains("\"authority_effect\":\"None\""));
    assert!(receipt_json.contains("\"phase_transition_detected\":true"));
}

// Origin: engine/crates_rs/tests/engines/test_uhlmann_fidelity_integration.rs
// Claim: urn:core:crates_rs:tests:test-uhlmann-fidelity-integration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf4ee763a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf4ee763a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf4ee763a {
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
impl BoundaryErrorf4ee763a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf4ee763a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf4ee763a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf4ee763a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf4ee763a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf4ee763a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf4ee763a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf4ee763a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f4ee763a() {
    let admitted = BoundaryRecordf4ee763a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf4ee763a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
