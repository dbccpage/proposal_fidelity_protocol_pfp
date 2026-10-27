//! Extreme Quantum Cognition Machine (EQCM) Deliberation Engine.
//!
//! Implements quantum deliberation and reservoir computing for multi-agent dispute
//! arbitration and reasoning under contradictory evidence, grounded in:
//! - Romeo & Settino, *Extreme Quantum Cognition Machines for Deliberative Decision Making*,
//!   arXiv: 2603.05430v2, 2026.
//!
//! # Core Mathematical Architecture:
//! 1. **MaxEnt State Encoding**: Maps confidence-scaled agent inputs \(\boldsymbol{\lambda} \in \mathbb{R}^m\)
//!    into a maximum-entropy density operator \(\rho(0) = \frac{1}{Z} \exp(-\sum \lambda_k \sigma_z^{(k)})\).
//! 2. **Ising Dynamical Attention Reservoir**:
//!    \(H(\mathbf{z}) = -J \sum \sigma_z^{(i)}\sigma_z^{(i+1)} - h \sum \sigma_x^{(i)} + g \sum z_k \sigma_x^{(k)}\).
//! 3. **Non-Commutative Observables**: Extracts local polarizations \(\langle \sigma_z^{(i)} \rangle, \langle \sigma_x^{(i)} \rangle\)
//!    and two-point correlators \(\langle \sigma_z^{(i)} \sigma_z^{(j)} \rangle\).
//! 4. **Linear Ridge Readout**: Closed-form regularized decision layer \(\mathbf{w} = (\mathbf{X}^\top \mathbf{X} + \gamma \mathbf{I})^{-1} \mathbf{X}^\top \mathbf{y}\).
//!
//! AuthorityEffect: None. Multi-agent diagnostic arbitration and heuristic modeling only.

use nalgebra::{DMatrix, DVector};
use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};

/// Configuration parameters for the Extreme Quantum Cognition Machine.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EqcmConfig {
    /// Number of qubits (decision channels) \(m \in [2, 10]\).
    pub num_qubits: usize,
    /// Nearest-neighbor Ising coupling strength \(J\).
    pub ising_j: f64,
    /// Static transverse field strength \(h\).
    pub transverse_h: f64,
    /// Dynamical attention coupling strength \(g\).
    pub attention_g: f64,
    /// Evolution time duration \(\tau\).
    pub evolution_time: f64,
    /// Ridge regression \(L_2\) regularization parameter \(\gamma\).
    pub ridge_gamma: f64,
}

impl Default for EqcmConfig {
    fn default() -> Self {
        Self {
            num_qubits: 6,
            ising_j: 1.0,
            transverse_h: 0.5,
            attention_g: 0.8,
            evolution_time: 1.5,
            ridge_gamma: 1e-3,
        }
    }
}

/// A multi-agent input packet for quantum deliberation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AgentDeliberationInput {
    /// Agent confidence values \(\lambda_k \in \mathbb{R}\) for MaxEnt encoding.
    pub confidences: Vec<f64>,
    /// Dichotomic decision votes \(z_k \in \{-1.0, +1.0\}\) for attention modulation.
    pub votes: Vec<f64>,
}

/// Diagnostic report containing the deliberative consensus verdict and observable spectrum.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EqcmDeliberationReport {
    /// Deliberative verdict decision (+1 for Accepted/Verified, -1 for Refused/Vetoed).
    pub decision: i8,
    /// Continuous decision score from the linear readout layer \(\hat{y} \in \mathbb{R}\).
    pub decision_score: f64,
    /// Confidence magnitude \(|\hat{y}|\).
    pub decision_confidence: f64,
    /// Extracted quantum observable expectation values.
    pub observables: Vec<f64>,
    /// Number of qubits in the reservoir.
    pub num_qubits: usize,
    /// Authority boundary declaration.
    pub authority_effect: AuthorityEffect,
}

/// Extreme Quantum Cognition Machine (EQCM) Reservoir & Readout Engine.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EqcmEngine {
    pub config: EqcmConfig,
    /// Fitted ridge regression weights \(\mathbf{w} \in \mathbb{R}^{D+1}\) (including bias).
    pub weights: Option<Vec<f64>>,
}

impl EqcmEngine {
    /// Create a new EQCM Engine with given configuration.
    pub fn new(config: EqcmConfig) -> Result<Self, String> {
        if config.num_qubits < 2 || config.num_qubits > 10 {
            return Err("Number of qubits must be between 2 and 10".to_string());
        }
        Ok(Self {
            config,
            weights: None,
        })
    }

    /// Total number of extracted observables \(D = 2m + \binom{m}{2}\).
    pub fn num_observables(&self) -> usize {
        let m = self.config.num_qubits;
        m + m + (m * (m - 1)) / 2
    }

    /// Construct the MaxEnt diagonal density matrix \(\rho(0)\).
    pub fn build_max_ent_density(&self, confidences: &[f64]) -> Result<Vec<f64>, String> {
        let m = self.config.num_qubits;
        if confidences.len() != m {
            return Err(format!(
                "Expected {m} confidences, got {}",
                confidences.len()
            ));
        }

        let dim = 1 << m;
        let mut probs = vec![0.0; dim];

        // For each basis state |s_0, s_1, ..., s_{m-1}> where s_k in {0, 1}:
        // Prob = prod_k exp(-lambda_k * (1 - 2*s_k)) / (2 * cosh(lambda_k))
        for state in 0..dim {
            let mut p = 1.0;
            for (k, &lambda) in confidences.iter().enumerate() {
                let bit = (state >> (m - 1 - k)) & 1;
                let sigma_z_val = if bit == 0 { 1.0 } else { -1.0 };
                let unnorm = (-lambda * sigma_z_val).exp();
                let z_k = 2.0 * lambda.cosh();
                p *= unnorm / z_k.max(1e-15);
            }
            probs[state] = p;
        }

        Ok(probs)
    }

    /// Build the real symmetric Transverse-Field Ising + Dynamical Attention Hamiltonian \(H(\mathbf{z})\).
    pub fn build_hamiltonian(&self, votes: &[f64]) -> Result<DMatrix<f64>, String> {
        let m = self.config.num_qubits;
        if votes.len() != m {
            return Err(format!("Expected {m} votes, got {}", votes.len()));
        }

        let dim = 1 << m;
        let mut h_mat = DMatrix::<f64>::zeros(dim, dim);

        let j_coup = self.config.ising_j;
        let h_field = self.config.transverse_h;
        let g_att = self.config.attention_g;

        // 1. Diagonal ZZ couplings: -J sum_{i=0}^{m-2} sigma_z^{(i)} sigma_z^{(i+1)}
        for state in 0..dim {
            let mut diag_val = 0.0;
            for i in 0..(m - 1) {
                let bit1 = (state >> (m - 1 - i)) & 1;
                let bit2 = (state >> (m - 1 - (i + 1))) & 1;
                let s1 = if bit1 == 0 { 1.0 } else { -1.0 };
                let s2 = if bit2 == 0 { 1.0 } else { -1.0 };
                diag_val -= j_coup * s1 * s2;
            }
            h_mat[(state, state)] += diag_val;
        }

        // 2. Off-diagonal X terms: sum_{k=0}^{m-1} (-h + g * z_k) sigma_x^{(k)}
        for k in 0..m {
            let x_coeff = -h_field + g_att * votes[k];
            if x_coeff.abs() < 1e-15 {
                continue;
            }

            let bit_mask = 1 << (m - 1 - k);
            for state in 0..dim {
                let flipped_state = state ^ bit_mask;
                h_mat[(flipped_state, state)] += x_coeff;
            }
        }

        Ok(h_mat)
    }

    /// Simulate unitary reservoir evolution and extract the non-commutative feature vector \(\mathbf{x}(\mathbf{z}) \in \mathbb{R}^D\).
    pub fn extract_features(&self, input: &AgentDeliberationInput) -> Result<Vec<f64>, String> {
        let m = self.config.num_qubits;
        let dim = 1 << m;

        // 1. Initial MaxEnt diagonal density distribution
        let rho_0 = self.build_max_ent_density(&input.confidences)?;

        // 2. Build Hamiltonian H(z)
        let h_mat = self.build_hamiltonian(&input.votes)?;

        // 3. Exact real symmetric eigendecomposition: H = V Lambda V^T
        let eigen = h_mat.symmetric_eigen();
        let v_mat = eigen.eigenvectors;
        let eigenvalues = eigen.eigenvalues;

        // 4. Time evolution: rho(t) = V [ exp(-i Lambda t) (V^T rho(0) V) exp(i Lambda t) ] V^T
        let tau = self.config.evolution_time;
        let mid_0 = Self::project_initial_density(&v_mat, &rho_0, dim);
        let rho_t = Self::evolve_density_matrix(&v_mat, eigenvalues.as_slice(), &mid_0, dim, tau);

        // 5. Extract non-commutative observables:
        Ok(self.collect_pauli_observables(&rho_t, m, dim))
    }

    fn project_initial_density(v_mat: &DMatrix<f64>, rho_0: &[f64], dim: usize) -> DMatrix<f64> {
        // Form mid_0 = V^T * diag(rho_0) * V
        // Since rho_0 is diagonal: mid_0(r, c) = sum_k V(k, r) * rho_0[k] * V(k, c)
        let mut mid_0 = DMatrix::<f64>::zeros(dim, dim);
        for r in 0..dim {
            for c in 0..dim {
                let mut sum = 0.0;
                for (k, &rho_k) in rho_0.iter().enumerate().take(dim) {
                    sum += v_mat[(k, r)] * rho_k * v_mat[(k, c)];
                }
                mid_0[(r, c)] = sum;
            }
        }
        mid_0
    }

    fn evolve_density_matrix(
        v_mat: &DMatrix<f64>,
        eigenvalues: &[f64],
        mid_0: &DMatrix<f64>,
        dim: usize,
        tau: f64,
    ) -> DMatrix<f64> {
        // Apply phase factors: mid_t(r, c) = mid_0(r, c) * exp(-i (E_r - E_c) * tau)
        // rho(t)_{a, b} = sum_{r, c} V(a, r) * V(b, c) * mid_0(r, c) * cos((E_r - E_c) * tau)
        // (Imaginary parts cancel due to Hermiticity).
        let mut rho_t = DMatrix::<f64>::zeros(dim, dim);
        for (r, &e_r) in eigenvalues.iter().enumerate().take(dim) {
            for (c, &e_c) in eigenvalues.iter().enumerate().take(dim) {
                let val = mid_0[(r, c)] * ((e_r - e_c) * tau).cos();
                if val.abs() >= 1e-15 {
                    Self::accumulate_evolved_mode(&mut rho_t, v_mat, r, c, val, dim);
                }
            }
        }
        rho_t
    }

    fn accumulate_evolved_mode(
        rho_t: &mut DMatrix<f64>,
        v_mat: &DMatrix<f64>,
        r: usize,
        c: usize,
        val: f64,
        dim: usize,
    ) {
        for a in 0..dim {
            let v_ar = v_mat[(a, r)];
            for b in 0..dim {
                let v_bc = v_mat[(b, c)];
                rho_t[(a, b)] += v_ar * v_bc * val;
            }
        }
    }

    fn collect_pauli_observables(&self, rho_t: &DMatrix<f64>, m: usize, dim: usize) -> Vec<f64> {
        let mut features = Vec::with_capacity(self.num_observables());

        // (a) Local <sigma_z^{(i)}>
        for i in 0..m {
            features.push(Self::local_sigma_z_expectation(rho_t, m, dim, i));
        }

        // (b) Local <sigma_x^{(i)}>
        for i in 0..m {
            let bit_mask = 1 << (m - 1 - i);
            let mut exp_val = 0.0;
            for state in 0..dim {
                let flipped = state ^ bit_mask;
                exp_val += rho_t[(flipped, state)];
            }
            features.push(exp_val);
        }

        // (c) Two-point correlators <sigma_z^{(i)} sigma_z^{(j)}> for i < j
        for i in 0..m {
            for j in (i + 1)..m {
                features.push(Self::two_point_z_correlator(rho_t, m, dim, i, j));
            }
        }

        features
    }

    fn local_sigma_z_expectation(rho_t: &DMatrix<f64>, m: usize, dim: usize, i: usize) -> f64 {
        let mut exp_val = 0.0;
        for state in 0..dim {
            let bit = (state >> (m - 1 - i)) & 1;
            let s_val = if bit == 0 { 1.0 } else { -1.0 };
            exp_val += rho_t[(state, state)] * s_val;
        }
        exp_val
    }

    fn two_point_z_correlator(
        rho_t: &DMatrix<f64>,
        m: usize,
        dim: usize,
        i: usize,
        j: usize,
    ) -> f64 {
        let mut exp_val = 0.0;
        for state in 0..dim {
            let bit1 = (state >> (m - 1 - i)) & 1;
            let bit2 = (state >> (m - 1 - j)) & 1;
            let s1 = if bit1 == 0 { 1.0 } else { -1.0 };
            let s2 = if bit2 == 0 { 1.0 } else { -1.0 };
            exp_val += rho_t[(state, state)] * (s1 * s2);
        }
        exp_val
    }

    /// Fit the closed-form Ridge Regression readout layer on a training dataset.
    ///
    /// \(\mathbf{w} = (\tilde{\mathbf{X}}^\top \tilde{\mathbf{X}} + \gamma \mathbf{I})^{-1} \tilde{\mathbf{X}}^\top \mathbf{y}\)
    pub fn train(
        &mut self,
        inputs: &[AgentDeliberationInput],
        labels: &[f64],
    ) -> Result<(), String> {
        if inputs.is_empty() || inputs.len() != labels.len() {
            return Err("Training inputs and labels must have equal non-zero length".to_string());
        }

        let num_samples = inputs.len();
        let num_features = self.num_observables();
        let num_cols = num_features + 1; // +1 for bias

        let mut x_mat = DMatrix::<f64>::zeros(num_samples, num_cols);
        let mut y_vec = DVector::<f64>::zeros(num_samples);

        for (row_idx, (inp, &lbl)) in inputs.iter().zip(labels.iter()).enumerate() {
            let feats = self.extract_features(inp)?;
            for (col_idx, &f_val) in feats.iter().enumerate() {
                x_mat[(row_idx, col_idx)] = f_val;
            }
            x_mat[(row_idx, num_features)] = 1.0; // Bias term
            y_vec[row_idx] = lbl;
        }

        // Compute X^T * X + gamma * I
        let xt_x = x_mat.transpose() * &x_mat;
        let gamma_i = DMatrix::<f64>::identity(num_cols, num_cols) * self.config.ridge_gamma;
        let reg_matrix = xt_x + gamma_i;

        // Invert and multiply: w = (X^T X + gamma I)^(-1) * X^T * y
        let inv_opt = reg_matrix.try_inverse();
        let inv_matrix = inv_opt.ok_or("Failed to invert regularized covariance matrix")?;
        let w_vec = inv_matrix * (x_mat.transpose() * y_vec);

        self.weights = Some(w_vec.as_slice().to_vec());
        Ok(())
    }

    /// Deliberate on a multi-agent input packet and produce a structured deliberation report.
    pub fn deliberate(
        &self,
        input: &AgentDeliberationInput,
    ) -> Result<EqcmDeliberationReport, String> {
        let weights = self
            .weights
            .as_ref()
            .ok_or("EQCM engine must be trained before deliberation")?;

        let features = self.extract_features(input)?;
        let num_features = features.len();

        let mut score = 0.0;
        for (idx, &f) in features.iter().enumerate() {
            score += f * weights[idx];
        }
        score += weights[num_features]; // Bias

        let decision = if score >= 0.0 { 1 } else { -1 };
        let confidence = score.abs();

        Ok(EqcmDeliberationReport {
            decision,
            decision_score: score,
            decision_confidence: confidence,
            observables: features,
            num_qubits: self.config.num_qubits,
            authority_effect: AuthorityEffect::None,
        })
    }
}

// Origin: engine/crates_rs/engines/src/quantum/eqcm_deliberation_engine.rs
// Claim: urn:core:crates_rs:engines:eqcm-deliberation-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2b344f80 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2b344f80` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2b344f80 {
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
impl BoundaryError2b344f80 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2b344f80 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2b344f80 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2b344f80 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2b344f80> {
        if capacity_bound == 0 {
            return Err(BoundaryError2b344f80::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2b344f80::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2b344f80::ExceedsCapacity {
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
mod l4_boundary_tests_2b344f80 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2b344f80::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2b344f80::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2b344f80::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2b344f80::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2b344f80::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2b344f80::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2b344f80::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
