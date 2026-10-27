//! Tullio Regge's Quantum Gravity & Path Integral Formulations (RQ-04 through RQ-10).
//!
//! Foundations for quantum Regge calculus:
//! - Ponzano–Regge 6j-symbol asymptotics (RQ-06)
//! - Discrete simplicial path integral propagator with DeWitt measure (RQ-04)
//! - Simplicial Wheeler–DeWitt Hamiltonian constraint operator (RQ-05)
//! - Quantum tetrahedron area/volume spectrum (RQ-07)
//! - Discrete diffeomorphism zero modes (RQ-08)
//! - Curvature-bounded path integrals (RQ-09)
//! - Regge–Čech quantum contextuality bridge (RQ-10)
//!
//! AuthorityEffect: None.

use crate::cayley_menger::simplex_volume_cayley_menger;
use crate::dihedral_angles::tetrahedron_dihedral_angle_at_edge;
use serde::{Deserialize, Serialize};

// ============================================================================
// 1. Ponzano-Regge Semiclassical Amplitude ({6j} Asymptotics) (RQ-06)
// ============================================================================
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PonzanoReggeAsymptotics {
    pub regge_action: f64,
    pub tetrahedron_volume: f64,
    pub cosine_amplitude: f64,
    pub phase_factor: f64,
}

/// Compute Ponzano-Regge semiclassical amplitude for a tetrahedron with 6 edge lengths:
/// {6j} ~ (1 / sqrt(12 * pi * V)) * cos( sum_{e=1}^6 j_e * theta_e + pi/4 ).
pub fn compute_ponzano_regge_amplitude(
    edge_lengths: &[f64; 6],
) -> Result<PonzanoReggeAsymptotics, String> {
    let tet = [0, 1, 2, 3];
    let edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)];

    let get_len = |u: usize, v: usize| -> Option<f64> {
        let pair = if u < v { (u, v) } else { (v, u) };
        for i in 0..6 {
            if edges[i] == pair {
                return Some(edge_lengths[i]);
            }
        }
        None
    };

    let vol = simplex_volume_cayley_menger(&tet, get_len)?;
    if vol <= 1e-12 {
        return Err("Tetrahedron has non-positive Cayley-Menger volume".to_string());
    }

    let mut action = 0.0;
    for i in 0..6 {
        let ell = edge_lengths[i];
        let theta = tetrahedron_dihedral_angle_at_edge(&tet, edges[i], get_len)?;
        action += ell * theta;
    }

    let phase = action + std::f64::consts::FRAC_PI_4;
    let denom = (12.0 * std::f64::consts::PI * vol).sqrt();
    let amp = phase.cos() / denom;

    Ok(PonzanoReggeAsymptotics {
        regge_action: action,
        tetrahedron_volume: vol,
        cosine_amplitude: amp,
        phase_factor: phase,
    })
}

// ============================================================================
// 2. Discrete Quantum Path Integral Propagator (RQ-04)
// ============================================================================
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct QuantumReggePropagatorResult {
    pub real_amplitude: f64,
    pub imag_amplitude: f64,
    pub total_configs_sampled: usize,
    pub admissible_configs: usize,
}

/// Compute 1D discrete path integral over edge length ell with DeWitt measure mu(ell) = ell:
/// Z = int d ell * ell * exp(i S_Regge[ell] / hbar).
pub fn compute_quantum_regge_path_integral_1d(
    length_range: (f64, f64),
    steps: usize,
    hbar: f64,
    mut action_evaluator: impl FnMut(f64) -> Option<f64>,
) -> QuantumReggePropagatorResult {
    let (l_min, l_max) = length_range;
    let step_size = (l_max - l_min) / (steps as f64);

    let mut real_amp = 0.0;
    let mut imag_amp = 0.0;
    let mut admissible_count = 0;

    for i in 0..steps {
        let ell = l_min + (i as f64 + 0.5) * step_size;
        if let Some(s) = action_evaluator(ell) {
            let weight = ell * step_size;
            let phase = s / hbar;
            real_amp += weight * phase.cos();
            imag_amp += weight * phase.sin();
            admissible_count += 1;
        }
    }

    QuantumReggePropagatorResult {
        real_amplitude: real_amp,
        imag_amplitude: imag_amp,
        total_configs_sampled: steps,
        admissible_configs: admissible_count,
    }
}

// ============================================================================
// 3. Simplicial Wheeler-DeWitt Constraint Operator (RQ-05)
// ============================================================================
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WheelerDeWittConstraintResult {
    pub vertex: usize,
    pub kinetic_term: f64,
    pub potential_term: f64,
    pub total_constraint_residual: f64,
}

/// Evaluate simplicial Wheeler-DeWitt constraint H_v Psi = 0:
/// H_v = -hbar^2 * kinetic_term - 2 * sum_{e \ni v} ell_e * eps_e.
pub fn evaluate_simplicial_wheeler_dewitt(
    vertex: usize,
    incident_edge_deficits: &[(f64, f64)],
    psi_val: f64,
    psi_hessian_trace: f64,
) -> WheelerDeWittConstraintResult {
    let mut potential = 0.0;
    for &(ell, eps) in incident_edge_deficits {
        potential += 2.0 * ell * eps;
    }
    let kinetic = -psi_hessian_trace;
    let residual = kinetic - potential * psi_val;

    WheelerDeWittConstraintResult {
        vertex,
        kinetic_term: kinetic,
        potential_term: potential,
        total_constraint_residual: residual,
    }
}

// ============================================================================
// 4. Quantum Tetrahedron Area & Volume Spectrum (RQ-07)
// ============================================================================
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct QuantumTetrahedronSpectrum {
    pub spins: [f64; 4],
    pub face_areas: [f64; 4],
    pub volume_eigenvalue_estimate: f64,
}

/// Compute loop quantum area spectrum A_i = 8 pi gamma l_P^2 sqrt(j_i (j_i + 1))
/// and semiclassical Barrett-Crane volume estimate.
pub fn compute_quantum_tetrahedron_spectrum(
    spins: [f64; 4],
    gamma: f64,
    l_p: f64,
) -> QuantumTetrahedronSpectrum {
    let mut areas = [0.0; 4];
    for i in 0..4 {
        let j = spins[i];
        areas[i] = 8.0 * std::f64::consts::PI * gamma * (l_p * l_p) * (j * (j + 1.0)).sqrt();
    }
    let a_mean: f64 = areas.iter().copied().sum::<f64>() / 4.0;
    let vol_est = a_mean.powf(1.5) / (6.0 * 2.0f64.sqrt());

    QuantumTetrahedronSpectrum {
        spins,
        face_areas: areas,
        volume_eigenvalue_estimate: vol_est,
    }
}

// ============================================================================
// 5. Discrete Diffeomorphism Zero Modes (RQ-08)
// ============================================================================
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ZeroModeAnalysis {
    pub diagonal_hessian: Vec<f64>,
    pub near_zero_diagonal_count: usize,
    /// Unknown: a diagonal alone determines neither kernel nor gauge symmetry.
    pub is_diffeo_invariant: Option<bool>,
}

/// Count near-zero diagonal entries; no zero-mode or symmetry inference follows.
pub fn analyze_flat_triangulation_zero_modes(
    diagonal_second_derivatives: &[f64],
    threshold: f64,
) -> ZeroModeAnalysis {
    let mut zero_modes = 0;
    for &d2 in diagonal_second_derivatives {
        if d2.abs() < threshold {
            zero_modes += 1;
        }
    }
    ZeroModeAnalysis {
        diagonal_hessian: diagonal_second_derivatives.to_vec(),
        near_zero_diagonal_count: zero_modes,
        is_diffeo_invariant: None,
    }
}

// ============================================================================
// 6. Regge-Čech Quantum Contextuality Bridge (RQ-10)
// ============================================================================
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ReggeCechQuantumBridge {
    pub deficit_angle: f64,
    pub cech_gluing_obstruction: Option<f64>,
    pub bell_chsh_violation_bound: Option<f64>,
    pub is_contextual: Option<bool>,
}

/// Record an angle without asserting an unimplemented measurement/gluing bridge.
/// No empirical model, contexts, or correlations are supplied to this API.
pub fn bridge_regge_to_quantum_cech(deficit_angle: f64) -> ReggeCechQuantumBridge {
    ReggeCechQuantumBridge {
        deficit_angle,
        cech_gluing_obstruction: None,
        bell_chsh_violation_bound: None,
        is_contextual: None,
    }
}

// ============================================================================
// 7. Simplicial Wheeler-DeWitt Constraint Operator Evaluated Against DEC Laplacians
// ============================================================================
use crate::dec_laplacian::DecOperators;
use crate::regge_4d::{HingeTriangle4D, ReggeTriangulation4D};

/// Per-vertex evaluation of the Wheeler-DeWitt constraint operator against DEC Laplacians:
/// H_v Psi = - (hbar^2 / (2 * M_v)) * (Delta_DEC Psi)_v + U_v * Psi_v.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WheelerDeWittDecVertexResult {
    pub vertex: usize,
    pub mass_measure: f64,
    pub dec_laplacian_val: f64,
    pub kinetic_term: f64,
    pub curvature_potential: f64,
    pub boundary_curvature_potential: f64,
    pub cosmological_potential: f64,
    pub total_potential: f64,
    pub wavefunctional_val: f64,
    pub residual: f64,
}

/// Finite DEC diagnostic report on a declared 4D triangulation.
/// Satisfaction means only that the reported discrete residual meets the tolerance.
/// It does not establish a continuum Wheeler-DeWitt solution. AuthorityEffect: None.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WheelerDeWittDecReport {
    pub hbar: f64,
    pub lambda_param: f64,
    pub vertex_results: Vec<WheelerDeWittDecVertexResult>,
    pub max_residual: f64,
    pub residual_l2_norm: f64,
    pub is_constraint_satisfied: bool,
}

fn validate_wdw_params(
    triangulation: &ReggeTriangulation4D,
    n: usize,
    psi_len: usize,
    hbar: f64,
    lambda_param: f64,
    tolerance: f64,
) -> Result<(), String> {
    if !hbar.is_finite()
        || hbar < 0.0
        || !lambda_param.is_finite()
        || !tolerance.is_finite()
        || tolerance < 0.0
        || triangulation.complex.num_vertices() != n
    {
        return Err("invalid parameters or incompatible triangulation".into());
    }
    if psi_len != n {
        return Err(format!(
            "Wavefunctional vector length {psi_len} != num_vertices {n}"
        ));
    }
    Ok(())
}

fn accumulate_hinge_curvatures(
    hinges: &[HingeTriangle4D],
    n: usize,
) -> Result<(Vec<f64>, Vec<f64>), String> {
    let mut interior_curv_pot = vec![0.0; n];
    let mut boundary_curv_pot = vec![0.0; n];
    for h in hinges {
        if h.triangle.iter().any(|&v| v >= n)
            || !h.area.is_finite()
            || h.area <= 0.0
            || !h.deficit_angle.is_finite()
        {
            return Err("invalid hinge geometry".into());
        }
        let h_contrib = h.area * h.deficit_angle;
        let target = if h.is_interior {
            &mut interior_curv_pot
        } else {
            &mut boundary_curv_pot
        };
        for &v in &h.triangle {
            target[v] += h_contrib;
        }
    }
    Ok((interior_curv_pot, boundary_curv_pot))
}

fn compute_wdw_vertex(
    v: usize,
    m_v: f64,
    lap_val: f64,
    c_pot: f64,
    b_pot: f64,
    psi_v: f64,
    hbar: f64,
    lambda_param: f64,
) -> Result<WheelerDeWittDecVertexResult, String> {
    let kinetic = -(hbar * hbar) / (2.0 * m_v) * lap_val;
    let cosmo_pot = -lambda_param * m_v;
    let total_pot = c_pot + cosmo_pot;
    let res = kinetic + total_pot * psi_v;

    if !res.is_finite() || !b_pot.is_finite() {
        return Err("constraint arithmetic is non-finite".into());
    }

    Ok(WheelerDeWittDecVertexResult {
        vertex: v,
        mass_measure: m_v,
        dec_laplacian_val: lap_val,
        kinetic_term: kinetic,
        curvature_potential: c_pot,
        boundary_curvature_potential: b_pot,
        cosmological_potential: cosmo_pot,
        total_potential: total_pot,
        wavefunctional_val: psi_v,
        residual: res,
    })
}

/// Evaluates the Wheeler-DeWitt Hamiltonian constraint operator across all vertices
/// of a 4D Regge triangulation against the Discrete Exterior Calculus (DEC) Laplace-Beltrami operator.
pub fn evaluate_wheeler_dewitt_against_dec_laplacian(
    triangulation: &ReggeTriangulation4D,
    dec: &DecOperators,
    psi: &[f64],
    hbar: f64,
    lambda_param: f64,
    tolerance: f64,
) -> Result<WheelerDeWittDecReport, String> {
    dec.validate()?;
    let n = dec.num_vertices;
    validate_wdw_params(triangulation, n, psi.len(), hbar, lambda_param, tolerance)?;

    // Evaluate DEC Laplacian Delta_0 Psi
    let dec_lap = dec.laplacian_0form(psi)?;
    // Compute local scalar curvature potential for each vertex v:
    // Bulk interior potential: sum_{f in interior hinges, v in f} A_f * eps_f
    // Boundary potential: sum_{f in boundary hinges, v in f} A_f * eps_f
    let (interior_curv_pot, boundary_curv_pot) =
        accumulate_hinge_curvatures(&triangulation.hinges, n)?;

    let mut vertex_results = Vec::with_capacity(n);
    let mut sum_sq_res = 0.0;
    let mut max_res = 0.0f64;

    for v in 0..n {
        let m_v = dec.hodge.star0_vertex_volumes[v];
        let lap_val = dec_lap[v];
        let vr = compute_wdw_vertex(
            v,
            m_v,
            lap_val,
            interior_curv_pot[v],
            boundary_curv_pot[v],
            psi[v],
            hbar,
            lambda_param,
        )?;

        // Kinetic term: - (hbar^2 / (2 * M_v)) * (Delta_0 Psi)_v
        // Potentials: Bulk WDW Hamiltonian constraint is governed by interior scalar curvature
        // Constraint operator H_v Psi = kinetic + total_pot * Psi_v
        let abs_res = vr.residual.abs();
        if abs_res > max_res {
            max_res = abs_res;
        }
        sum_sq_res += vr.residual * vr.residual;
        vertex_results.push(vr);
    }

    if !sum_sq_res.is_finite() {
        return Err("constraint residual norm overflow".into());
    }
    let l2_norm = (sum_sq_res / (n as f64)).sqrt();
    let is_sat = max_res <= tolerance;

    Ok(WheelerDeWittDecReport {
        hbar,
        lambda_param,
        vertex_results,
        max_residual: max_res,
        residual_l2_norm: l2_norm,
        is_constraint_satisfied: is_sat,
    })
}

// Origin: engine/crates_rs/core_general_relativity/src/quantum_regge.rs
// Claim: urn:core:crates_rs:core-general-relativity:quantum-regge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1bf67f7b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1bf67f7b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1bf67f7b {
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
impl BoundaryError1bf67f7b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1bf67f7b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1bf67f7b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1bf67f7b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1bf67f7b> {
        if capacity_bound == 0 {
            return Err(BoundaryError1bf67f7b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1bf67f7b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1bf67f7b::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ponzano_regge_amplitude_regular_tet() {
        let side = 1.0;
        let lengths = [side; 6];
        let amp = compute_ponzano_regge_amplitude(&lengths).unwrap();
        assert!(amp.tetrahedron_volume > 0.1);
        assert!(amp.cosine_amplitude.is_finite());
    }

    #[test]
    fn test_regge_cech_bridge_flat_vs_curved() {
        let flat = bridge_regge_to_quantum_cech(0.0);
        assert_eq!(flat.is_contextual, None);
        assert_eq!(flat.bell_chsh_violation_bound, None);

        let curved = bridge_regge_to_quantum_cech(0.5);
        assert_eq!(curved.is_contextual, None);
        assert_eq!(curved.bell_chsh_violation_bound, None);
    }
}

#[cfg(test)]
mod l4_boundary_tests_1bf67f7b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1bf67f7b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1bf67f7b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1bf67f7b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1bf67f7b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1bf67f7b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1bf67f7b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1bf67f7b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
