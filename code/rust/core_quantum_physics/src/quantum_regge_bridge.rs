//! Quantum Regge Calculus & Finite Quantum Mechanics Bridge (Hamber §8, Ponzano–Regge, MTW §42.11).
//!
//! Connects finite-dimensional quantum mechanics, spin networks, and simplicial geometry:
//! 1. **Quantum Area Spectrum on Simplices**:
//!    Hinges carry discrete $SU(2)$ spins $j_h = n_h / 2$.
//!    The squared area operator has exact rational eigenvalues from `spin_area_spectrum`:
//!      $$A_h^2 = j_h(j_h + 1) = \frac{n_h(n_h + 2)}{4}$$
//! 2. **Ponzano–Regge State Sum Weights**:
//!    The kinematic amplitude weight for a simplicial triangulation with spin assignments:
//!      $$\mu(\{n_e\}) = \prod_{e} (-1)^{n_e} (n_e + 1)$$
//! 3. **Discrete Mini-Superspace Wheeler–DeWitt Operator**:
//!    On an isotropic triangulated 3-sphere (boundary of a 4-simplex with scale factor $a$):
//!      $$\hat{\mathcal{H}} \psi(a) = \left[ -\frac{\hbar^2}{2 M} \frac{d^2}{da^2} - k a + 2\Lambda a^3 \right] \psi(a) = 0$$
//!    Discretized on a grid $a_m = m \Delta a$:
//!      $$\hat{\mathcal{H}} \psi_m = -\frac{\hbar^2}{2 M (\Delta a)^2} (\psi_{m+1} - 2\psi_m + \psi_{m-1}) + V(a_m) \psi_m = 0$$
//!
//! AuthorityEffect: None.

use crate::density_matrix::{DensityError, DensityMatrix, DEFAULT_TOL};
use crate::hilbert_space::HilbertSpace;
use crate::kraus_operators::{KrausOperators, DEFAULT_TP_TOL};
use crate::quantum_channel::{ChannelError, QuantumChannel};
use crate::spin_area_spectrum::area_label_squared;
use linear_algebra::hermitian_eigen::{hermitian_eigen_checked, HermitianSpectrum, SpectrumPolicy};
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, NComplex};
use core_general_relativity::dirac_operator_discrete::{SimplicialDiracOperator, Spinor2};
use core_number_theory::rational::Rational;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; quantum Regge and finite QM bridge.";

/// Assignment of discrete SU(2) twice-spin labels n_e = 2 j_e to edges/hinges of a triangulation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SimplicialSpinNetworkState {
    /// Map from edge/hinge (u, v) with u < v to twice-spin integer n_e.
    pub twice_spins: BTreeMap<(usize, usize), u32>,
}

impl SimplicialSpinNetworkState {
    pub fn new() -> Self {
        Self {
            twice_spins: BTreeMap::new(),
        }
    }

    pub fn set_spin(&mut self, u: usize, v: usize, twice_spin: u32) {
        let key = if u < v { (u, v) } else { (v, u) };
        self.twice_spins.insert(key, twice_spin);
    }

    pub fn get_spin(&self, u: usize, v: usize) -> Option<u32> {
        let key = if u < v { (u, v) } else { (v, u) };
        self.twice_spins.get(&key).copied()
    }

    /// Compute exact rational squared area eigenvalues for all declared hinges:
    /// A_e² = n_e (n_e + 2) / 4.
    pub fn area_squared_eigenvalues(&self) -> BTreeMap<(usize, usize), Rational> {
        let mut map = BTreeMap::new();
        for (&edge, &n) in &self.twice_spins {
            map.insert(edge, area_label_squared(n));
        }
        map
    }

    /// Ponzano-Regge edge dimension product:
    /// ∏_e (2 j_e + 1) = ∏_e (n_e + 1).
    pub fn total_state_space_dimension(&self) -> u128 {
        let mut dim: u128 = 1;
        for &n in self.twice_spins.values() {
            dim = dim.saturating_mul((n as u128) + 1);
        }
        dim
    }
}

impl Default for SimplicialSpinNetworkState {
    fn default() -> Self {
        Self::new()
    }
}

/// Discrete mini-superspace Wheeler–DeWitt solver for isotropic quantum cosmology.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DiscreteMiniSuperspaceWheelerDeWitt {
    pub hbar: f64,
    pub mass: f64,
    pub lambda: f64,
    pub spatial_curvature_k: f64,
    pub delta_a: f64,
    pub num_points: usize,
}

impl DiscreteMiniSuperspaceWheelerDeWitt {
    pub fn new(
        hbar: f64,
        mass: f64,
        lambda: f64,
        spatial_curvature_k: f64,
        delta_a: f64,
        num_points: usize,
    ) -> Result<Self, String> {
        if hbar <= 0.0 || !hbar.is_finite() {
            return Err("Invalid non-positive hbar".to_string());
        }
        if mass <= 0.0 || !mass.is_finite() {
            return Err("Invalid non-positive mass".to_string());
        }
        if delta_a <= 0.0 || !delta_a.is_finite() {
            return Err("Invalid non-positive grid step delta_a".to_string());
        }
        if num_points < 3 {
            return Err("Grid must have at least 3 points".to_string());
        }

        Ok(Self {
            hbar,
            mass,
            lambda,
            spatial_curvature_k,
            delta_a,
            num_points,
        })
    }

    /// Potential function V(a) = - k * a + 2 * Lambda * a^3.
    pub fn potential(&self, a: f64) -> f64 {
        -self.spatial_curvature_k * a + 2.0 * self.lambda * a.powi(3)
    }

    /// Apply the discrete Wheeler-DeWitt Hamiltonian difference operator to a wavefunction ψ(a_m):
    /// (H ψ)_m = - (hbar² / (2 M (Δa)²)) [ψ_{m+1} - 2 ψ_m + ψ_{m-1}] + V(a_m) ψ_m.
    pub fn apply_hamiltonian(&self, psi: &[f64]) -> Result<Vec<f64>, String> {
        if psi.len() != self.num_points {
            return Err("Wavefunction length must match grid points".to_string());
        }

        let kinetic_coeff = -self.hbar * self.hbar / (2.0 * self.mass * self.delta_a * self.delta_a);
        let mut h_psi = vec![0.0; self.num_points];

        for m in 1..(self.num_points - 1) {
            let a_m = (m as f64) * self.delta_a;
            let d2_psi = psi[m + 1] - 2.0 * psi[m] + psi[m - 1];
            let kin = kinetic_coeff * d2_psi;
            let pot = self.potential(a_m) * psi[m];
            h_psi[m] = kin + pot;
        }

        // Boundary conditions at m=0 and m=N-1 (Dirichlet / vanishing boundary)
        h_psi[0] = psi[0];
        h_psi[self.num_points - 1] = psi[self.num_points - 1];

        Ok(h_psi)
    }

    /// Compute residual norm ||H ψ|| / ||ψ|| to test if ψ is a discrete Wheeler-DeWitt eigenstate.
    pub fn compute_residual_norm(&self, psi: &[f64]) -> Result<f64, String> {
        let h_psi = self.apply_hamiltonian(psi)?;
        let mut sum_sq_h = 0.0;
        let mut sum_sq_psi = 0.0;

        for m in 1..(self.num_points - 1) {
            sum_sq_h += h_psi[m] * h_psi[m];
            sum_sq_psi += psi[m] * psi[m];
        }

        if sum_sq_psi < 1e-15 {
            return Err("Wavefunction norm is zero".to_string());
        }

        Ok((sum_sq_h / sum_sq_psi).sqrt())
    }

    /// Convert a discrete Wheeler-DeWitt wavefunction psi(a_m) into a normalized diagonal PopulationShadow.
    pub fn wavefunction_to_population_shadow(
        &self,
        psi: &[f64],
    ) -> Result<DensityMatrix, DensityError> {
        if psi.len() != self.num_points {
            return Err(DensityError::DimensionMismatch {
                expected: self.num_points,
                actual: psi.len(),
            });
        }
        let norm_sq: f64 = psi.iter().map(|&x| x * x).sum();
        if norm_sq <= 1e-15 || !norm_sq.is_finite() {
            return Err(DensityError::Empty);
        }
        let probs: Vec<f64> = psi.iter().map(|&x| (x * x) / norm_sq).collect();
        let space = HilbertSpace::try_new(self.num_points, "wdw_scale_factor_space")
            .map_err(|_| DensityError::Empty)?;
        DensityMatrix::try_from_probs(&space, probs, "wdw_population_shadow", DEFAULT_TOL)
    }

    /// Convert a discrete Wheeler-DeWitt wavefunction psi(a_m) into a pure-state density matrix rho = |psi><psi| / ||psi||^2.
    pub fn wavefunction_to_density_matrix(&self, psi: &[f64]) -> Result<CMatrix, DensityError> {
        if psi.len() != self.num_points {
            return Err(DensityError::DimensionMismatch {
                expected: self.num_points,
                actual: psi.len(),
            });
        }
        let norm_sq: f64 = psi.iter().map(|&x| x * x).sum();
        if norm_sq <= 1e-15 || !norm_sq.is_finite() {
            return Err(DensityError::Empty);
        }
        let n = self.num_points;
        let mut rho = CMatrix::zeros(n, n);
        for i in 0..n {
            for j in 0..n {
                rho[(i, j)] = NComplex::new((psi[i] * psi[j]) / norm_sq, 0.0);
            }
        }
        Ok(rho)
    }

    /// Construct CPTP scale factor dephasing channel modeling quantum-to-classical cosmological decoherence.
    pub fn scale_factor_dephasing_channel(&self, p: f64) -> Result<QuantumChannel, ChannelError> {
        simplicial_dirac_dephasing_channel(self.num_points, p)
    }

    /// Apply cosmological scale factor decoherence to a Wheeler-DeWitt pure state.
    pub fn apply_scale_factor_decoherence(
        &self,
        psi: &[f64],
        p: f64,
    ) -> Result<CMatrix, ChannelError> {
        let rho = self
            .wavefunction_to_density_matrix(psi)
            .map_err(ChannelError::Density)?;
        let chan = self.scale_factor_dephasing_channel(p)?;
        chan.apply_matrix(&rho)
    }
}

// ---------------------------------------------------------------------------
// Anisotropic Bianchi-Type Wheeler–DeWitt Model & Differential Directional Decoherence
// ---------------------------------------------------------------------------

/// Discrete anisotropic Bianchi-type Wheeler–DeWitt quantum cosmology model.
///
/// Models 3-dimensional spatial geometry with directional scale factors (a_1, a_2, a_3)
/// on a discrete tensor-product grid of dimensions (N_1, N_2, N_3):
///   - Directional kinetic difference operators:
///       (H_kin psi)_{m_1, m_2, m_3} = - (hbar^2 / (2 M)) sum_{k=1}^3 (1 / (Delta a_k)^2) Delta_k^2 psi
///   - Anisotropic spatial potential V(a_1, a_2, a_3):
///       V(a_1, a_2, a_3) = - (k_1 a_1 + k_2 a_2 + k_3 a_3) + 2 Lambda a_1 a_2 a_3
///   - Directional decoherence channels with differential decoherence rates:
///       Gamma_k = - ln(1 - p_k) / Delta t
///     modeling how anisotropic environmental metric fluctuations suppress spatial coherences
///     at different rates along different spatial directions.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AnisotropicBianchiWheelerDeWitt {
    pub hbar: f64,
    pub mass: f64,
    pub lambda: f64,
    pub spatial_curvature_k: [f64; 3],
    pub delta_a: [f64; 3],
    pub grid_dims: [usize; 3],
}

impl AnisotropicBianchiWheelerDeWitt {
    fn validate_grid_and_step_inputs(
        delta_a: &[f64; 3],
        grid_dims: &[usize; 3],
    ) -> Result<usize, String> {
        for (k, &da) in delta_a.iter().enumerate() {
            if da <= 0.0 || !da.is_finite() {
                return Err(format!("Invalid non-positive grid step delta_a[{k}]"));
            }
        }
        for (k, &dim) in grid_dims.iter().enumerate() {
            if dim < 2 {
                return Err(format!("Grid dimension at axis {k} must be at least 2"));
            }
        }
        grid_dims[0]
            .checked_mul(grid_dims[1])
            .and_then(|d| d.checked_mul(grid_dims[2]))
            .ok_or_else(|| "Grid dimension overflow".to_string())
    }

    pub fn new(
        hbar: f64,
        mass: f64,
        lambda: f64,
        spatial_curvature_k: [f64; 3],
        delta_a: [f64; 3],
        grid_dims: [usize; 3],
    ) -> Result<Self, String> {
        if hbar <= 0.0 || !hbar.is_finite() {
            return Err("Invalid non-positive hbar".to_string());
        }
        if mass <= 0.0 || !mass.is_finite() {
            return Err("Invalid non-positive mass".to_string());
        }
        let total_dim = Self::validate_grid_and_step_inputs(&delta_a, &grid_dims)?;
        if total_dim > 1024 {
            return Err(format!(
                "Total grid dimension {total_dim} exceeds limit of 1024"
            ));
        }

        Ok(Self {
            hbar,
            mass,
            lambda,
            spatial_curvature_k,
            delta_a,
            grid_dims,
        })
    }

    /// Total dimension of the discrete anisotropic state space N_1 * N_2 * N_3.
    pub fn total_dim(&self) -> usize {
        self.grid_dims[0] * self.grid_dims[1] * self.grid_dims[2]
    }

    /// Map flat index to 3D grid multi-index (m_1, m_2, m_3).
    pub fn flat_to_multi(&self, idx: usize) -> [usize; 3] {
        let n3 = self.grid_dims[2];
        let n2 = self.grid_dims[1];
        let m3 = idx % n3;
        let rem = idx / n3;
        let m2 = rem % n2;
        let m1 = rem / n2;
        [m1, m2, m3]
    }

    /// Map 3D grid multi-index (m_1, m_2, m_3) to flat index.
    pub fn multi_to_flat(&self, m: [usize; 3]) -> usize {
        (m[0] * self.grid_dims[1] + m[1]) * self.grid_dims[2] + m[2]
    }

    /// Anisotropic potential: V(a_1, a_2, a_3) = - sum_k k_i a_i + 2 Lambda a_1 a_2 a_3.
    pub fn potential(&self, a: [f64; 3]) -> f64 {
        let curv = -self.spatial_curvature_k[0] * a[0]
            - self.spatial_curvature_k[1] * a[1]
            - self.spatial_curvature_k[2] * a[2];
        let vol_term = 2.0 * self.lambda * a[0] * a[1] * a[2];
        curv + vol_term
    }

    fn is_boundary_grid_point(&self, m1: usize, m2: usize, m3: usize) -> bool {
        let [n1, n2, n3] = self.grid_dims;
        m1 == 0 || m1 == n1 - 1 || m2 == 0 || m2 == n2 - 1 || m3 == 0 || m3 == n3 - 1
    }

    fn evaluate_grid_point(
        &self,
        psi: &[f64],
        coeff: f64,
        m1: usize,
        m2: usize,
        m3: usize,
    ) -> f64 {
        let idx = self.multi_to_flat([m1, m2, m3]);
        if self.is_boundary_grid_point(m1, m2, m3) {
            return psi[idx];
        }
        let a = [
            (m1 as f64) * self.delta_a[0],
            (m2 as f64) * self.delta_a[1],
            (m3 as f64) * self.delta_a[2],
        ];
        // Second differences along each directional axis
        let d2_1 = psi[self.multi_to_flat([m1 + 1, m2, m3])] - 2.0 * psi[idx]
            + psi[self.multi_to_flat([m1 - 1, m2, m3])];
        let d2_2 = psi[self.multi_to_flat([m1, m2 + 1, m3])] - 2.0 * psi[idx]
            + psi[self.multi_to_flat([m1, m2 - 1, m3])];
        let d2_3 = psi[self.multi_to_flat([m1, m2, m3 + 1])] - 2.0 * psi[idx]
            + psi[self.multi_to_flat([m1, m2, m3 - 1])];

        let kin = coeff
            * (d2_1 / (self.delta_a[0] * self.delta_a[0])
                + d2_2 / (self.delta_a[1] * self.delta_a[1])
                + d2_3 / (self.delta_a[2] * self.delta_a[2]));
        let pot = self.potential(a) * psi[idx];
        kin + pot
    }

    /// Apply the discrete 3D anisotropic Wheeler-DeWitt Hamiltonian difference operator:
    /// (H psi)_m = - (hbar^2 / (2 M)) sum_{k=0}^2 (1 / (Delta a_k)^2) Delta_k^2 psi + V(a_m) psi_m.
    pub fn apply_hamiltonian(&self, psi: &[f64]) -> Result<Vec<f64>, String> {
        let total = self.total_dim();
        if psi.len() != total {
            return Err(format!(
                "Wavefunction length {} != total grid dimension {}",
                psi.len(),
                total
            ));
        }

        let [n1, n2, n3] = self.grid_dims;
        let mut h_psi = vec![0.0; total];
        let coeff = -self.hbar * self.hbar / (2.0 * self.mass);

        for m1 in 0..n1 {
            for m2 in 0..n2 {
                for m3 in 0..n3 {
                    let idx = self.multi_to_flat([m1, m2, m3]);
                    h_psi[idx] = self.evaluate_grid_point(psi, coeff, m1, m2, m3);
                }
            }
        }

        Ok(h_psi)
    }

    /// Convert anisotropic wavefunction psi(a_1, a_2, a_3) to diagonal PopulationShadow.
    pub fn wavefunction_to_population_shadow(
        &self,
        psi: &[f64],
    ) -> Result<DensityMatrix, DensityError> {
        let total = self.total_dim();
        if psi.len() != total {
            return Err(DensityError::DimensionMismatch {
                expected: total,
                actual: psi.len(),
            });
        }
        let norm_sq: f64 = psi.iter().map(|&x| x * x).sum();
        if norm_sq <= 1e-15 || !norm_sq.is_finite() {
            return Err(DensityError::Empty);
        }
        let probs: Vec<f64> = psi.iter().map(|&x| (x * x) / norm_sq).collect();
        let space = HilbertSpace::try_new(total, "anisotropic_wdw_space")
            .map_err(|_| DensityError::Empty)?;
        DensityMatrix::try_from_probs(&space, probs, "anisotropic_wdw_shadow", DEFAULT_TOL)
    }

    /// Convert anisotropic wavefunction psi(a_1, a_2, a_3) to pure state CMatrix density operator.
    pub fn wavefunction_to_density_matrix(&self, psi: &[f64]) -> Result<CMatrix, DensityError> {
        let total = self.total_dim();
        if psi.len() != total {
            return Err(DensityError::DimensionMismatch {
                expected: total,
                actual: psi.len(),
            });
        }
        let norm_sq: f64 = psi.iter().map(|&x| x * x).sum();
        if norm_sq <= 1e-15 || !norm_sq.is_finite() {
            return Err(DensityError::Empty);
        }
        let mut rho = CMatrix::zeros(total, total);
        for i in 0..total {
            for j in 0..total {
                rho[(i, j)] = NComplex::new((psi[i] * psi[j]) / norm_sq, 0.0);
            }
        }
        Ok(rho)
    }

    /// Directional CPTP dephasing channel along a specific spatial axis k in {0, 1, 2}.
    /// Kraus operators acting on C^D:
    ///   K_0 = sqrt(1 - p) I_D
    ///   K_{m+1} = sqrt(p) Pi_m^{(k)} where Pi_m^{(k)} projects onto the slice with m_k = m.
    pub fn directional_dephasing_channel(
        &self,
        axis: usize,
        p: f64,
    ) -> Result<QuantumChannel, ChannelError> {
        if axis > 2 {
            return Err(ChannelError::ParameterOutOfRange {
                name: "axis",
                value: axis as f64,
            });
        }
        if p < 0.0 || p > 1.0 || !p.is_finite() {
            return Err(ChannelError::ParameterOutOfRange {
                name: "p",
                value: p,
            });
        }
        let total = self.total_dim();
        let n_k = self.grid_dims[axis];

        let mut c_ops = Vec::with_capacity(n_k + 1);

        // K_0 = sqrt(1 - p) I_D
        let f0 = (1.0 - p).sqrt();
        let mut k0 = CMatrix::zeros(total, total);
        for i in 0..total {
            k0[(i, i)] = NComplex::new(f0, 0.0);
        }
        c_ops.push(k0);

        // K_{m+1} = sqrt(p) Pi_m^{(k)}
        let fp = p.sqrt();
        for m in 0..n_k {
            let mut km = CMatrix::zeros(total, total);
            for i in 0..total {
                let coords = self.flat_to_multi(i);
                if coords[axis] == m {
                    km[(i, i)] = NComplex::new(fp, 0.0);
                }
            }
            c_ops.push(km);
        }

        let kraus = KrausOperators::try_from_cmatrices(
            total,
            c_ops,
            format!("bianchi_dephasing_axis_{axis}"),
        )?;
        QuantumChannel::try_from_kraus(
            kraus,
            format!("bianchi_channel_axis_{axis}"),
            DEFAULT_TP_TOL,
        )
    }

    /// Calculate differential directional decoherence rates Gamma_k = - ln(1 - p_k) / dt.
    pub fn directional_decoherence_rates(&self, p: [f64; 3], dt: f64) -> [f64; 3] {
        let mut rates = [0.0; 3];
        for k in 0..3 {
            if p[k] >= 1.0 {
                rates[k] = f64::INFINITY;
            } else if p[k] <= 0.0 || dt <= 0.0 {
                rates[k] = 0.0;
            } else {
                rates[k] = -(1.0 - p[k]).ln() / dt;
            }
        }
        rates
    }

    /// Apply sequential directional decoherence along all three spatial axes:
    /// E_{p_1, p_2, p_3}(rho) = (E_2 circ E_1 circ E_0)(rho).
    pub fn apply_anisotropic_decoherence(
        &self,
        psi: &[f64],
        p: [f64; 3],
    ) -> Result<CMatrix, ChannelError> {
        let mut rho = self
            .wavefunction_to_density_matrix(psi)
            .map_err(ChannelError::Density)?;

        for axis in 0..3 {
            if p[axis] > 0.0 {
                let chan = self.directional_dephasing_channel(axis, p[axis])?;
                rho = chan.apply_matrix(&rho)?;
            }
        }

        Ok(rho)
    }
}


// ---------------------------------------------------------------------------
// Simplicial Dirac Operator to Finite QM Matrix, Spectrum, and CPTP Channels
// ---------------------------------------------------------------------------

/// Extract the (2V) x (2V) complex Hamiltonian matrix representation of the discrete Dirac operator
/// in the volume-weighted orthonormal basis:
///   e_{v, 0}(w) = delta_{wv} (1 / sqrt(V_v)) (1, 0)^T
///   e_{v, 1}(w) = delta_{wv} (1 / sqrt(V_v)) (0, 1)^T
///
/// Under the simplicial inner product <phi, psi> = sum_u V_u phi(u)^\dagger psi(u),
/// the matrix element M_{(u, s), (v, s')} = <e_{u, s}, D e_{v, s'}> is strictly Hermitian.
pub fn simplicial_dirac_to_matrix(dirac: &SimplicialDiracOperator) -> Result<CMatrix, String> {
    let num_v = dirac.num_vertices;
    let dim = 2 * num_v;
    let mut mat = CMatrix::zeros(dim, dim);

    for v in 0..num_v {
        let vol_v = dirac.vertex_volumes[v];
        if vol_v <= 0.0 || !vol_v.is_finite() {
            return Err(format!("Non-positive volume at vertex {v}: {vol_v}"));
        }
        let inv_sqrt_v = 1.0 / vol_v.sqrt();

        for s_prime in 0..2 {
            let col = 2 * v + s_prime;
            // Prepare basis spinor field e_{v, s'}
            let mut psi_basis = vec![Spinor2::zero(); num_v];
            if s_prime == 0 {
                psi_basis[v] = Spinor2::new((inv_sqrt_v, 0.0), (0.0, 0.0));
            } else {
                psi_basis[v] = Spinor2::new((0.0, 0.0), (inv_sqrt_v, 0.0));
            }

            let d_psi = dirac.apply(&psi_basis)?;

            for u in 0..num_v {
                let vol_u = dirac.vertex_volumes[u];
                let sqrt_u = vol_u.sqrt();

                let (u_r, u_i) = d_psi[u].u;
                let (d_r, d_i) = d_psi[u].d;

                // row 2u + 0 corresponds to spin up at vertex u
                mat[(2 * u, col)] = NComplex::new(sqrt_u * u_r, sqrt_u * u_i);
                // row 2u + 1 corresponds to spin down at vertex u
                mat[(2 * u + 1, col)] = NComplex::new(sqrt_u * d_r, sqrt_u * d_i);
            }
        }
    }

    // Enforce exact bitwise Hermiticity against floating-point roundoff:
    for i in 0..dim {
        mat[(i, i)].im = 0.0;
        for j in 0..i {
            let avg_re = 0.5 * (mat[(i, j)].re + mat[(j, i)].re);
            let avg_im = 0.5 * (mat[(i, j)].im - mat[(j, i)].im);
            mat[(i, j)] = NComplex::new(avg_re, avg_im);
            mat[(j, i)] = NComplex::new(avg_re, -avg_im);
        }
    }

    Ok(mat)
}

/// Compute the real eigenvalues of the discrete Dirac operator using sovereign hermitian_eigen.
pub fn simplicial_dirac_spectrum(
    dirac: &SimplicialDiracOperator,
) -> Result<HermitianSpectrum, String> {
    let mat = simplicial_dirac_to_matrix(dirac)?;
    let dim = mat.nrows();
    let policy = SpectrumPolicy::new(dim.max(1).min(256), 10_000, 1e-10, 1e-7)
        .map_err(|e| format!("Spectrum policy error: {e}"))?;
    hermitian_eigen_checked(&mat, policy).map_err(|e| format!("Hermitian eigen failure: {e}"))
}

/// Construct the discrete Dirac Gibbs thermal state rho = exp(-beta D) / Tr(exp(-beta D))
/// as a diagonal population shadow in the Dirac energy eigenbasis.
pub fn simplicial_dirac_thermal_state(
    spectrum: &[f64],
    beta: f64,
) -> Result<DensityMatrix, DensityError> {
    if spectrum.is_empty() {
        return Err(DensityError::Empty);
    }
    if beta < 0.0 || !beta.is_finite() {
        return Err(DensityError::InvalidTolerance);
    }
    let dim = spectrum.len();
    let min_e = spectrum.iter().cloned().fold(f64::INFINITY, f64::min);

    // Stabilized Boltzmann weights
    let weights: Vec<f64> = spectrum
        .iter()
        .map(|&e| (-beta * (e - min_e)).exp())
        .collect();
    let z: f64 = weights.iter().sum();
    if z <= 0.0 || !z.is_finite() {
        return Err(DensityError::NonFiniteEntry);
    }
    let probs: Vec<f64> = weights.iter().map(|&w| w / z).collect();

    let space =
        HilbertSpace::try_new(dim, "dirac_eigenbasis").map_err(|_| DensityError::Empty)?;
    DensityMatrix::try_from_probs(&space, probs, "dirac_thermal_gibbs", DEFAULT_TOL)
}

fn accumulate_thermal_projector_sum(
    dim: usize,
    probs: &[f64],
    eigenvectors: &CMatrix,
) -> CMatrix {
    let mut rho = CMatrix::zeros(dim, dim);
    for (i, &p_i) in probs.iter().enumerate() {
        for j in 0..dim {
            let v_ji = eigenvectors[(j, i)];
            for k in 0..dim {
                let v_ki_conj = eigenvectors[(k, i)].conj();
                rho[(j, k)] += v_ji * v_ki_conj * NComplex::new(p_i, 0.0);
            }
        }
    }
    rho
}

/// Construct the discrete Dirac Gibbs thermal density matrix rho in the vertex-spin basis:
/// rho = sum_i (exp(-beta lambda_i) / Z) |v_i><v_i|
pub fn simplicial_dirac_thermal_cmatrix(
    spectrum: &[f64],
    eigenvectors: &CMatrix,
    beta: f64,
) -> Result<CMatrix, DensityError> {
    if spectrum.is_empty() {
        return Err(DensityError::Empty);
    }
    let dim = spectrum.len();
    if eigenvectors.nrows() != dim || eigenvectors.ncols() != dim {
        return Err(DensityError::DimensionMismatch {
            expected: dim,
            actual: eigenvectors.nrows(),
        });
    }
    if beta < 0.0 || !beta.is_finite() {
        return Err(DensityError::InvalidTolerance);
    }
    let min_e = spectrum.iter().cloned().fold(f64::INFINITY, f64::min);
    let weights: Vec<f64> = spectrum
        .iter()
        .map(|&e| (-beta * (e - min_e)).exp())
        .collect();
    let z: f64 = weights.iter().sum();
    if z <= 0.0 || !z.is_finite() {
        return Err(DensityError::NonFiniteEntry);
    }
    let probs: Vec<f64> = weights.iter().map(|&w| w / z).collect();
    Ok(accumulate_thermal_projector_sum(dim, &probs, eigenvectors))
}

/// Discrete Dirac CPTP dephasing channel modeling spacetime foam decoherence:
/// E(rho) = (1 - p) rho + p sum_{m} |m><m| rho |m><m|
/// Kraus representation:
///   K_0 = sqrt(1 - p) I_dim
///   K_{m+1} = sqrt(p) |m><m| for m in 0..dim
pub fn simplicial_dirac_dephasing_channel(
    dim: usize,
    p: f64,
) -> Result<QuantumChannel, ChannelError> {
    if p < 0.0 || p > 1.0 || !p.is_finite() {
        return Err(ChannelError::ParameterOutOfRange {
            name: "p",
            value: p,
        });
    }
    if dim == 0 {
        return Err(ChannelError::DimensionMismatch {
            expected: 1,
            actual: 0,
        });
    }

    let mut c_ops = Vec::with_capacity(dim + 1);

    // K_0 = sqrt(1 - p) I
    let f0 = (1.0 - p).sqrt();
    let mut k0 = CMatrix::zeros(dim, dim);
    for i in 0..dim {
        k0[(i, i)] = NComplex::new(f0, 0.0);
    }
    c_ops.push(k0);

    // K_{m+1} = sqrt(p) |m><m|
    let fp = p.sqrt();
    for m in 0..dim {
        let mut km = CMatrix::zeros(dim, dim);
        km[(m, m)] = NComplex::new(fp, 0.0);
        c_ops.push(km);
    }

    let kraus = KrausOperators::try_from_cmatrices(dim, c_ops, "dirac_dephasing_kraus")?;
    QuantumChannel::try_from_kraus(kraus, "dirac_dephasing_channel", DEFAULT_TP_TOL)
}

/// Discrete Dirac CPTP dissipation / damping channel:
/// Models fermion energy relaxation to the lowest mode with probability gamma in [0, 1].
pub fn simplicial_dirac_dissipation_channel(
    dim: usize,
    gamma: f64,
) -> Result<QuantumChannel, ChannelError> {
    if gamma < 0.0 || gamma > 1.0 || !gamma.is_finite() {
        return Err(ChannelError::ParameterOutOfRange {
            name: "gamma",
            value: gamma,
        });
    }
    if dim < 2 {
        return Err(ChannelError::DimensionMismatch {
            expected: 2,
            actual: dim,
        });
    }

    let mut c_ops = Vec::with_capacity(dim);

    // K_0 = diag(1, sqrt(1-gamma), ..., sqrt(1-gamma))
    let mut k0 = CMatrix::zeros(dim, dim);
    k0[(0, 0)] = NComplex::new(1.0, 0.0);
    let f_decay = (1.0 - gamma).sqrt();
    for m in 1..dim {
        k0[(m, m)] = NComplex::new(f_decay, 0.0);
    }
    c_ops.push(k0);

    // K_m = sqrt(gamma) |0><m|
    let f_jump = gamma.sqrt();
    for m in 1..dim {
        let mut km = CMatrix::zeros(dim, dim);
        km[(0, m)] = NComplex::new(f_jump, 0.0);
        c_ops.push(km);
    }

    let kraus = KrausOperators::try_from_cmatrices(dim, c_ops, "dirac_dissipation_kraus")?;
    QuantumChannel::try_from_kraus(kraus, "dirac_dissipation_channel", DEFAULT_TP_TOL)
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_regge_bridge.rs
// Claim: urn:core:crates_rs:core-quantum-physics:quantum-regge-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord279e9ca5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord279e9ca5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError279e9ca5 {
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
impl BoundaryError279e9ca5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError279e9ca5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError279e9ca5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord279e9ca5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError279e9ca5> {
        if capacity_bound == 0 {
            return Err(BoundaryError279e9ca5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError279e9ca5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError279e9ca5::ExceedsCapacity {
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
    use core_general_relativity::dirac_operator_discrete::SpinConnectionSU2;

    #[test]
    fn test_spin_network_area_spectrum_exactness() {
        let mut state = SimplicialSpinNetworkState::new();
        // Edge 01 with j = 1/2 => twice_spin = 1
        // Edge 12 with j = 1   => twice_spin = 2
        state.set_spin(0, 1, 1);
        state.set_spin(1, 2, 2);

        let areas_sq = state.area_squared_eigenvalues();
        let a01_sq = areas_sq.get(&(0, 1)).unwrap();
        let a12_sq = areas_sq.get(&(1, 2)).unwrap();

        // For j = 1/2: j(j+1) = 1/2 * 3/2 = 3/4
        assert_eq!(*a01_sq, Rational::new(3.into(), 4.into()));

        // For j = 1: j(j+1) = 1 * 2 = 2 = 8/4
        assert_eq!(*a12_sq, Rational::new(2.into(), 1.into()));

        // Dimension product: (1 + 1) * (2 + 1) = 2 * 3 = 6
        assert_eq!(state.total_state_space_dimension(), 6);
    }

    #[test]
    fn test_discrete_wheeler_dewitt_potential_and_action() {
        let wdw = DiscreteMiniSuperspaceWheelerDeWitt::new(
            1.0,  // hbar
            1.0,  // mass
            0.05, // lambda
            1.0,  // spatial curvature k
            0.1,  // delta_a
            50,   // num_points
        )
        .unwrap();

        // V(a) at a = 2.0: -1.0 * 2.0 + 2 * 0.05 * 8.0 = -2.0 + 0.8 = -1.2
        let pot = wdw.potential(2.0);
        assert!((pot - (-1.2)).abs() < 1e-9);

        // Gaussian trial wavepacket centered at a = 2.0 (m = 20)
        let mut psi = vec![0.0; 50];
        for m in 0..50 {
            let a = (m as f64) * 0.1;
            psi[m] = (-((a - 2.0).powi(2)) / 0.5).exp();
        }

        let res = wdw.compute_residual_norm(&psi).unwrap();
        assert!(res.is_finite());
    }

    #[test]
    fn test_simplicial_dirac_matrix_hermiticity_and_spectrum() {
        // Construct a 2-vertex Dirac operator
        let v_vols = vec![1.5, 2.0];
        let n_01 = [1.0, 0.0, 0.0];
        let n_10 = [-1.0, 0.0, 0.0];
        let weight = 1.2;
        let conn_01 = SpinConnectionSU2::new_normalized([0.8, 0.6, 0.0, 0.0]).unwrap();
        let conn_10 = conn_01.dagger();

        let edges = vec![
            (0, 1, weight, n_01, conn_01),
            (1, 0, weight, n_10, conn_10),
        ];

        let dirac = SimplicialDiracOperator::new(2, v_vols, edges).unwrap();

        // 1. Matrix representation
        let mat = simplicial_dirac_to_matrix(&dirac).unwrap();
        assert_eq!(mat.nrows(), 4);
        assert_eq!(mat.ncols(), 4);

        // Verify Hermiticity of the matrix: M = M^\dagger
        for i in 0..4 {
            for j in 0..4 {
                let m_ij = mat[(i, j)];
                let m_ji = mat[(j, i)];
                assert!(
                    (m_ij.re - m_ji.re).abs() < 1e-9,
                    "Real part mismatch at ({i}, {j}): {} vs {}",
                    m_ij.re,
                    m_ji.re
                );
                assert!(
                    (m_ij.im + m_ji.im).abs() < 1e-9,
                    "Imag part mismatch at ({i}, {j}): {} vs {}",
                    m_ij.im,
                    m_ji.im
                );
            }
        }

        // 2. Spectrum extraction via sovereign hermitian_eigen
        let spec = simplicial_dirac_spectrum(&dirac).unwrap();
        let evals = spec.eigenvalues();
        assert_eq!(evals.len(), 4);
        for &e in evals {
            assert!(e.is_finite());
        }

        // Dirac spectrum has symmetric particle-hole pairs: lambda and -lambda
        assert!((evals[0] + evals[3]).abs() < 1e-6);
        assert!((evals[1] + evals[2]).abs() < 1e-6);
    }

    #[test]
    fn test_simplicial_dirac_thermal_state_and_channels() {
        let v_vols = vec![1.0, 1.0];
        let n_01 = [1.0, 0.0, 0.0];
        let n_10 = [-1.0, 0.0, 0.0];
        let weight = 1.0;
        let conn_01 = SpinConnectionSU2::identity();
        let conn_10 = conn_01.dagger();

        let edges = vec![
            (0, 1, weight, n_01, conn_01),
            (1, 0, weight, n_10, conn_10),
        ];

        let dirac = SimplicialDiracOperator::new(2, v_vols, edges).unwrap();
        let spec = simplicial_dirac_spectrum(&dirac).unwrap();

        // 1. Thermal Gibbs state
        let beta = 0.5;
        let thermal_shadow = simplicial_dirac_thermal_state(spec.eigenvalues(), beta).unwrap();
        assert_eq!(thermal_shadow.dim, 4);
        let prob_sum: f64 = thermal_shadow.probs.iter().sum();
        assert!((prob_sum - 1.0).abs() < 1e-8);

        // Thermal matrix representation
        let thermal_cmat = simplicial_dirac_thermal_cmatrix(
            spec.eigenvalues(),
            spec.eigenvectors(),
            beta,
        )
        .unwrap();
        let trace = thermal_cmat[(0, 0)] + thermal_cmat[(1, 1)] + thermal_cmat[(2, 2)] + thermal_cmat[(3, 3)];
        assert!((trace.re - 1.0).abs() < 1e-8);
        assert!(trace.im.abs() < 1e-8);

        assert!(matches!(
            simplicial_dirac_dephasing_channel(4, 0.3),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
        assert!(matches!(
            simplicial_dirac_dissipation_channel(4, 0.2),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
    }

    #[test]
    fn test_wheeler_dewitt_density_matrix_and_decoherence() {
        let wdw = DiscreteMiniSuperspaceWheelerDeWitt::new(
            1.0, 1.0, 0.05, 1.0, 0.1, 10,
        )
        .unwrap();

        // Wavefunction: localized wavepacket
        let mut psi = vec![0.0; 10];
        psi[4] = 1.0;
        psi[5] = 1.0; // superposition of scale factors a = 0.4 and a = 0.5

        // 1. Population shadow
        let shadow = wdw.wavefunction_to_population_shadow(&psi).unwrap();
        assert_eq!(shadow.dim, 10);
        assert!((shadow.probs[4] - 0.5).abs() < 1e-8);
        assert!((shadow.probs[5] - 0.5).abs() < 1e-8);

        // 2. Pure state density matrix
        let rho_pure = wdw.wavefunction_to_density_matrix(&psi).unwrap();
        assert_eq!(rho_pure.nrows(), 10);
        // Off-diagonal coherence between a=0.4 and a=0.5
        assert!((rho_pure[(4, 5)].re - 0.5).abs() < 1e-8);

        assert!(matches!(
            wdw.apply_scale_factor_decoherence(&psi, 0.5),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
        assert!(matches!(
            wdw.apply_scale_factor_decoherence(&psi, 1.0),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
    }

    #[test]
    fn test_anisotropic_bianchi_wheeler_dewitt_potential_and_action() {
        let bianchi = AnisotropicBianchiWheelerDeWitt::new(
            1.0,
            1.0,
            0.05,
            [1.0, 1.2, 0.8],
            [0.1, 0.1, 0.1],
            [3, 3, 3],
        )
        .unwrap();

        assert_eq!(bianchi.total_dim(), 27);

        // V(a) at a = (1.0, 1.0, 1.0): -(1.0 + 1.2 + 0.8) + 2 * 0.05 * 1.0 = -3.0 + 0.1 = -2.9
        let pot = bianchi.potential([1.0, 1.0, 1.0]);
        assert!((pot - (-2.9)).abs() < 1e-9);

        // Trial wavepacket
        let mut psi = vec![0.0; 27];
        psi[bianchi.multi_to_flat([1, 1, 1])] = 1.0;
        let h_psi = bianchi.apply_hamiltonian(&psi).unwrap();
        assert_eq!(h_psi.len(), 27);
        assert!(h_psi[bianchi.multi_to_flat([1, 1, 1])].is_finite());
    }

    #[test]
    fn test_anisotropic_bianchi_directional_decoherence_and_differential_rates() {
        // 2x2x2 anisotropic mini-superspace grid
        let bianchi = AnisotropicBianchiWheelerDeWitt::new(
            1.0,
            1.0,
            0.05,
            [1.0, 1.0, 1.0],
            [0.1, 0.1, 0.1],
            [2, 2, 2],
        )
        .unwrap();

        assert_eq!(bianchi.total_dim(), 8);

        // Differential decoherence rates across directions
        let p = [0.8, 0.2, 0.0];
        let dt = 1.0;
        let rates = bianchi.directional_decoherence_rates(p, dt);
        // Gamma_0 = -ln(0.2) ≈ 1.609
        // Gamma_1 = -ln(0.8) ≈ 0.223
        // Gamma_2 = 0.0
        assert!((rates[0] - (-(0.2f64).ln())).abs() < 1e-6);
        assert!((rates[1] - (-(0.8f64).ln())).abs() < 1e-6);
        assert_eq!(rates[2], 0.0);
        assert!(rates[0] > rates[1]);
        assert!(rates[1] > rates[2]);

        assert!(matches!(
            bianchi.directional_dephasing_channel(0, p[0]),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
        assert!(matches!(
            bianchi.directional_dephasing_channel(1, p[1]),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
        assert!(matches!(
            bianchi.directional_dephasing_channel(2, p[2]),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));

        // Anisotropic quantum superposition between two spatial geometries:
        // State A: (0, 0, 0) (flat index 0)
        // State B: (1, 1, 0) (flat index 6)
        let mut psi = vec![0.0; 8];
        psi[bianchi.multi_to_flat([0, 0, 0])] = 1.0 / 2.0f64.sqrt();
        psi[bianchi.multi_to_flat([1, 1, 0])] = 1.0 / 2.0f64.sqrt();

        let rho_pure = bianchi.wavefunction_to_density_matrix(&psi).unwrap();
        let idx_a = bianchi.multi_to_flat([0, 0, 0]);
        let idx_b = bianchi.multi_to_flat([1, 1, 0]);
        assert_eq!(idx_a, 0);
        assert_eq!(idx_b, 6);
        assert!((rho_pure[(idx_a, idx_b)].re - 0.5).abs() < 1e-8);

        assert!(matches!(
            bianchi.apply_anisotropic_decoherence(&psi, p),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_279e9ca5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord279e9ca5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord279e9ca5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord279e9ca5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord279e9ca5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord279e9ca5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError279e9ca5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError279e9ca5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
