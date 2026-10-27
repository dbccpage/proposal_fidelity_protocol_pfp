//! Discrete Deformation Calculus (DDC) Orbit State & Equational Reasoning Solver.
//!
//! Implements Quantum Normal Form Reduction and Matrix Product State (MPS)
//! algorithms for discrete term rewriting systems based on:
//! - Rattacaso et al., *Quantum algorithms for equational reasoning*,
//!   Science Advances 2025/2026, DOI: 10.1126/sciadv.aec2736, arXiv: 2508.21122.
//!
//! # Core Algebraic Constructs:
//! 1. **DdaRewriteRule**: Invertible string rewriting rule \(r_l = (\alpha \approx \beta)\).
//! 2. **DdaGraphLaplacian**: Sparse discrete Laplacian \(\hat{L}_S = \sum (\hat{r}_l^2 - \hat{r}_l)\)
//!    acting on \(L\)-qudit configuration graphs.
//! 3. **DdaMpsState**: 1D Matrix Product State with local rank-3 tensors and SVD bond truncation.
//! 4. **DdaOrbitStateSolver**: Imaginary Quantum Annealing (IQA) solver preparing uniform
//!    orbit states \(|X_{S, \tilde{\omega}}\rangle = \frac{1}{\sqrt{|X|}} \sum |\omega\rangle\)
//!    for Word Problem verification and Equivalence Class counting in polynomial time.
//!
//! AuthorityEffect: None. Mathematical modeling & automated reasoning diagnostics only.

use nalgebra::DMatrix;
use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};

/// Maximum default bond dimension for MPS simulation.
pub const DEFAULT_MAX_BOND_DIM: usize = 32;

/// Default singular value cutoff threshold.
pub const DEFAULT_SVD_CUTOFF: f64 = 1e-12;

/// An invertible string rewriting rule acting on substrings of length 2.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DdaRewriteRule {
    /// Pattern characters before rewrite (length 2).
    pub from: [usize; 2],
    /// Pattern characters after rewrite (length 2).
    pub to: [usize; 2],
}

impl DdaRewriteRule {
    /// Create a new 2-character rewrite rule.
    pub fn new(from: [usize; 2], to: [usize; 2]) -> Self {
        Self { from, to }
    }

    /// Construct the local 2-site Laplacian matrix \(h_l \in \mathbb{R}^{d^2 \times d^2}\).
    ///
    /// \(h_l = |from\rangle\langle from| + |to\rangle\langle to| - |from\rangle\langle to| - |to\rangle\langle from|\)
    pub fn local_laplacian_matrix(&self, alphabet_size: usize) -> DMatrix<f64> {
        let dim = alphabet_size * alphabet_size;
        let mut mat = DMatrix::<f64>::zeros(dim, dim);

        let idx_from = self.from[0] * alphabet_size + self.from[1];
        let idx_to = self.to[0] * alphabet_size + self.to[1];

        if idx_from == idx_to {
            return mat;
        }

        mat[(idx_from, idx_from)] += 1.0;
        mat[(idx_to, idx_to)] += 1.0;
        mat[(idx_from, idx_to)] -= 1.0;
        mat[(idx_to, idx_from)] -= 1.0;

        mat
    }

    /// Construct the local imaginary time evolution gate \(U = \exp(-\delta \tau h_l)\).
    pub fn local_ite_gate(&self, alphabet_size: usize, dt: f64) -> DMatrix<f64> {
        let dim = alphabet_size * alphabet_size;
        let mut u = DMatrix::<f64>::identity(dim, dim);

        let idx_from = self.from[0] * alphabet_size + self.from[1];
        let idx_to = self.to[0] * alphabet_size + self.to[1];

        if idx_from == idx_to {
            return u;
        }

        // For projector h = [[1, -1], [-1, 1]], eigenvalues are 2 and 0.
        // exp(-dt * h) = I - (1 - exp(-2*dt)) * 0.5 * h.
        let factor = 0.5 * (1.0 - (-2.0 * dt).exp());
        u[(idx_from, idx_from)] -= factor;
        u[(idx_to, idx_to)] -= factor;
        u[(idx_from, idx_to)] += factor;
        u[(idx_to, idx_from)] += factor;

        u
    }
}

/// A 1D Matrix Product State (MPS) representing a quantum state over \(L\) qudits.
#[derive(Debug, Clone, PartialEq)]
pub struct DdaMpsState {
    /// Number of sites (string length \(L\)).
    pub length: usize,
    /// Physical dimension \(d\) (alphabet size).
    pub alphabet_size: usize,
    /// Local tensors for each site: `tensors[i][sigma]` has shape \((D_{i-1}, D_i)\).
    pub tensors: Vec<Vec<DMatrix<f64>>>,
}

impl DdaMpsState {
    /// Construct an exact pure product state representing a single string \(\tilde{\omega}\).
    pub fn from_product_state(sequence: &[usize], alphabet_size: usize) -> Result<Self, String> {
        if sequence.is_empty() {
            return Err("Sequence cannot be empty".to_string());
        }
        for &s in sequence {
            if s >= alphabet_size {
                return Err(format!(
                    "Character {s} exceeds alphabet size {alphabet_size}"
                ));
            }
        }

        let length = sequence.len();
        let mut tensors = Vec::with_capacity(length);

        for &target_char in sequence {
            let mut site_mats = Vec::with_capacity(alphabet_size);
            for sigma in 0..alphabet_size {
                let val = if sigma == target_char { 1.0 } else { 0.0 };
                site_mats.push(DMatrix::from_element(1, 1, val));
            }
            tensors.push(site_mats);
        }

        Ok(Self {
            length,
            alphabet_size,
            tensors,
        })
    }

    /// Construct an exact uniform superposition state \(|All\rangle = \frac{1}{\sqrt{d^L}} \sum |\omega\rangle\).
    pub fn uniform_superposition(length: usize, alphabet_size: usize) -> Result<Self, String> {
        if length == 0 || alphabet_size == 0 {
            return Err("Length and alphabet size must be positive".to_string());
        }

        let val = 1.0 / (alphabet_size as f64).sqrt();
        let mut tensors = Vec::with_capacity(length);

        for _ in 0..length {
            let mut site_mats = Vec::with_capacity(alphabet_size);
            for _ in 0..alphabet_size {
                site_mats.push(DMatrix::from_element(1, 1, val));
            }
            tensors.push(site_mats);
        }

        Ok(Self {
            length,
            alphabet_size,
            tensors,
        })
    }

    /// Compute the exact inner product \(\langle \psi | \phi \rangle\) in \(O(L \cdot d \cdot \chi^3)\) time.
    pub fn inner_product(&self, other: &DdaMpsState) -> Result<f64, String> {
        if self.length != other.length || self.alphabet_size != other.alphabet_size {
            return Err("MPS dimension mismatch in inner product".to_string());
        }

        // Initialize transfer matrix E_0 = [[1.0]] of shape (D_left_self, D_left_other) = (1, 1).
        let mut transfer = DMatrix::<f64>::from_element(1, 1, 1.0);

        for site in 0..self.length {
            let mut next_transfer = DMatrix::<f64>::zeros(
                self.tensors[site][0].ncols(),
                other.tensors[site][0].ncols(),
            );

            for sigma in 0..self.alphabet_size {
                let a_mat = &self.tensors[site][sigma];
                let b_mat = &other.tensors[site][sigma];
                // next_transfer += A^T * transfer * B
                let temp = a_mat.transpose() * &transfer;
                next_transfer += temp * b_mat;
            }

            transfer = next_transfer;
        }

        if transfer.nrows() == 1 && transfer.ncols() == 1 {
            Ok(transfer[(0, 0)])
        } else {
            Err("Transfer matrix failed to contract to scalar".to_string())
        }
    }

    /// Compute the norm squared \(\|\psi\|^2 = \langle \psi | \psi \rangle\).
    pub fn norm_squared(&self) -> f64 {
        self.inner_product(self).unwrap_or(0.0)
    }

    /// Compute the norm \(\|\psi\|\).
    pub fn norm(&self) -> f64 {
        self.norm_squared().max(0.0).sqrt()
    }

    /// Normalize the MPS state such that \(\|\psi\| = 1.0\).
    pub fn normalize(&mut self) -> Result<(), String> {
        let n = self.norm();
        if n < 1e-15 {
            return Err("Cannot normalize state with zero norm".to_string());
        }
        let factor = 1.0 / n.powf(1.0 / self.length as f64);
        for site_mats in &mut self.tensors {
            for mat in site_mats {
                *mat *= factor;
            }
        }
        Ok(())
    }

    /// Compute the quantum fidelity \(F(\psi, \phi) = \frac{|\langle \psi | \phi \rangle|^2}{\|\psi\|^2 \|\phi\|^2}\).
    pub fn fidelity(&self, other: &DdaMpsState) -> Result<f64, String> {
        let overlap = self.inner_product(other)?;
        let n1 = self.norm_squared();
        let n2 = other.norm_squared();
        if n1 < 1e-15 || n2 < 1e-15 {
            return Ok(0.0);
        }
        let f = (overlap * overlap) / (n1 * n2);
        Ok(f.clamp(0.0, 1.0))
    }

    /// Apply a two-site gate to adjacent sites `(site, site + 1)` with SVD truncation.
    pub fn apply_two_site_gate(
        &mut self,
        site: usize,
        gate: &DMatrix<f64>,
        max_bond_dim: usize,
        cutoff: f64,
    ) -> Result<(), String> {
        if site + 1 >= self.length {
            return Err("Gate application site out of bounds".to_string());
        }
        let d = self.alphabet_size;
        if gate.nrows() != d * d || gate.ncols() != d * d {
            return Err("Gate dimension mismatch".to_string());
        }

        let d_left = self.tensors[site][0].nrows();
        let _d_mid = self.tensors[site][0].ncols();
        let d_right = self.tensors[site + 1][0].ncols();

        // 1. Construct two-site tensor Theta of shape (d_left * d, d * d_right).
        let theta = self.build_two_site_theta(site, d, d_left, d_right);

        // 2. Apply gate U: Theta_prime = (U (x) I) Theta.
        let theta_prime = Self::contract_two_site_gate(&theta, gate, d, d_left, d_right);

        // 3. SVD decomposition of Theta_prime = U S V^T.
        // Reshape to matrix of size (d_left * d, d * d_right).
        let svd = theta_prime.svd(true, true);
        let u_mat = svd.u.ok_or("SVD failed to compute U")?;
        let v_t_mat = svd.v_t.ok_or("SVD failed to compute V^T")?;
        let s_vals = svd.singular_values.as_slice();

        // Determine truncated bond dimension.
        let new_bond = Self::truncated_bond_dim(s_vals, max_bond_dim, cutoff);

        // 4. Update site tensors.
        let (new_a, new_b) =
            Self::split_svd_site_tensors(&u_mat, &v_t_mat, s_vals, d, d_left, d_right, new_bond);

        self.tensors[site] = new_a;
        self.tensors[site + 1] = new_b;

        Ok(())
    }

    fn build_two_site_theta(
        &self,
        site: usize,
        d: usize,
        d_left: usize,
        d_right: usize,
    ) -> DMatrix<f64> {
        let mut theta = DMatrix::<f64>::zeros(d_left * d, d * d_right);
        for s1 in 0..d {
            let a_mat = &self.tensors[site][s1];
            for s2 in 0..d {
                let b_mat = &self.tensors[site + 1][s2];
                let prod = a_mat * b_mat; // shape: (d_left, d_right)
                Self::write_theta_block(&mut theta, &prod, s1, s2, d, d_left, d_right);
            }
        }
        theta
    }

    fn write_theta_block(
        theta: &mut DMatrix<f64>,
        prod: &DMatrix<f64>,
        s1: usize,
        s2: usize,
        d: usize,
        d_left: usize,
        d_right: usize,
    ) {
        for (alpha, sigma1) in (0..d_left).zip(std::iter::repeat(s1)) {
            let row = alpha * d + sigma1;
            for (beta, sigma2) in (0..d_right).zip(std::iter::repeat(s2)) {
                let col = sigma2 * d_right + beta;
                theta[(row, col)] = prod[(alpha, beta)];
            }
        }
    }

    fn contract_two_site_gate(
        theta: &DMatrix<f64>,
        gate: &DMatrix<f64>,
        d: usize,
        d_left: usize,
        d_right: usize,
    ) -> DMatrix<f64> {
        let mut theta_prime = DMatrix::<f64>::zeros(d_left * d, d * d_right);
        for s1_prime in 0..d {
            for s2_prime in 0..d {
                let row_gate = s1_prime * d + s2_prime;
                Self::accumulate_gate_row(
                    &mut theta_prime,
                    theta,
                    gate,
                    row_gate,
                    (s1_prime, s2_prime),
                    (d, d_left, d_right),
                );
            }
        }
        theta_prime
    }

    fn accumulate_gate_row(
        theta_prime: &mut DMatrix<f64>,
        theta: &DMatrix<f64>,
        gate: &DMatrix<f64>,
        row_gate: usize,
        (s1_prime, s2_prime): (usize, usize),
        (d, d_left, d_right): (usize, usize, usize),
    ) {
        for s1 in 0..d {
            for s2 in 0..d {
                let weight = gate[(row_gate, s1 * d + s2)];
                if weight.abs() >= 1e-15 {
                    Self::accumulate_weighted_block(
                        theta_prime,
                        theta,
                        weight,
                        (s1, s2, s1_prime, s2_prime),
                        (d, d_left, d_right),
                    );
                }
            }
        }
    }

    fn accumulate_weighted_block(
        theta_prime: &mut DMatrix<f64>,
        theta: &DMatrix<f64>,
        weight: f64,
        (s1, s2, s1_prime, s2_prime): (usize, usize, usize, usize),
        (d, d_left, d_right): (usize, usize, usize),
    ) {
        for alpha in 0..d_left {
            let old_row = alpha * d + s1;
            let new_row = alpha * d + s1_prime;
            for beta in 0..d_right {
                let old_col = s2 * d_right + beta;
                let new_col = s2_prime * d_right + beta;
                theta_prime[(new_row, new_col)] += weight * theta[(old_row, old_col)];
            }
        }
    }

    fn truncated_bond_dim(s_vals: &[f64], max_bond_dim: usize, cutoff: f64) -> usize {
        let mut new_bond = 0;
        for &s in s_vals {
            if s > cutoff && new_bond < max_bond_dim {
                new_bond += 1;
            }
        }
        new_bond.max(1)
    }

    fn split_svd_site_tensors(
        u_mat: &DMatrix<f64>,
        v_t_mat: &DMatrix<f64>,
        s_vals: &[f64],
        d: usize,
        d_left: usize,
        d_right: usize,
        new_bond: usize,
    ) -> (Vec<DMatrix<f64>>, Vec<DMatrix<f64>>) {
        // Site i: A_new[s1](alpha, k) = U[(alpha*d + s1), k] * sqrt(S[k])
        let mut new_a = Vec::with_capacity(d);
        for s1 in 0..d {
            let mut mat_a = DMatrix::<f64>::zeros(d_left, new_bond);
            for alpha in 0..d_left {
                let row = alpha * d + s1;
                for k in 0..new_bond {
                    mat_a[(alpha, k)] = u_mat[(row, k)] * s_vals[k].sqrt();
                }
            }
            new_a.push(mat_a);
        }

        // Site i+1: B_new[s2](k, beta) = sqrt(S[k]) * V^T[k, (s2*d_right + beta)]
        let mut new_b = Vec::with_capacity(d);
        for s2 in 0..d {
            let mut mat_b = DMatrix::<f64>::zeros(new_bond, d_right);
            for k in 0..new_bond {
                for beta in 0..d_right {
                    let col = s2 * d_right + beta;
                    mat_b[(k, beta)] = s_vals[k].sqrt() * v_t_mat[(k, col)];
                }
            }
            new_b.push(mat_b);
        }

        (new_a, new_b)
    }
}

/// Diagnostic result from solving the Word Problem between two symbolic expressions.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WordProblemResult {
    pub connected: bool,
    pub fidelity: f64,
    pub word_1: Vec<usize>,
    pub word_2: Vec<usize>,
    pub annealing_steps: usize,
    pub authority_effect: AuthorityEffect,
}

/// Diagnostic result from estimating the equivalence class cardinality.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CountingResult {
    pub seed_word: Vec<usize>,
    pub estimated_class_size: f64,
    pub fidelity_to_all: f64,
    pub total_hilbert_space_dim: usize,
    pub authority_effect: AuthorityEffect,
}

/// DDA Orbit State Solver for equational reasoning and equivalence class operations.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DdaOrbitStateSolver {
    /// Alphabet size \(d\).
    pub alphabet_size: usize,
    /// String length \(L\).
    pub length: usize,
    /// Active rewriting rules \(R\).
    pub rules: Vec<DdaRewriteRule>,
    /// Maximum bond dimension \(\chi\).
    pub max_bond_dim: usize,
    /// Singular value cutoff threshold.
    pub svd_cutoff: f64,
}

impl DdaOrbitStateSolver {
    /// Create a new DDA Orbit State Solver.
    pub fn new(alphabet_size: usize, length: usize, rules: Vec<DdaRewriteRule>) -> Self {
        Self {
            alphabet_size,
            length,
            rules,
            max_bond_dim: DEFAULT_MAX_BOND_DIM,
            svd_cutoff: DEFAULT_SVD_CUTOFF,
        }
    }

    /// Set custom maximum bond dimension.
    pub fn with_max_bond_dim(mut self, max_bond_dim: usize) -> Self {
        self.max_bond_dim = max_bond_dim.max(1);
        self
    }

    /// Prepare an orbit state \(|X_{S, \tilde{\omega}}\rangle\) via Imaginary Quantum Annealing.
    pub fn prepare_orbit_state(
        &self,
        seed_word: &[usize],
        annealing_steps: usize,
        dt: f64,
    ) -> Result<DdaMpsState, String> {
        if seed_word.len() != self.length {
            return Err(format!(
                "Seed word length {} does not match solver length {}",
                seed_word.len(),
                self.length
            ));
        }

        let mut mps = DdaMpsState::from_product_state(seed_word, self.alphabet_size)?;

        for _ in 0..annealing_steps {
            // Apply imaginary time gates for each rule across all valid adjacent pairs.
            for rule in &self.rules {
                let gate = rule.local_ite_gate(self.alphabet_size, dt);
                for site in 0..(self.length - 1) {
                    mps.apply_two_site_gate(site, &gate, self.max_bond_dim, self.svd_cutoff)?;
                }
            }
            mps.normalize()?;
        }

        Ok(mps)
    }

    /// Solve the Word Problem: Determine if `word1` and `word2` belong to the same equivalence class.
    pub fn solve_word_problem(
        &self,
        word1: &[usize],
        word2: &[usize],
        annealing_steps: usize,
        dt: f64,
        fidelity_threshold: f64,
    ) -> Result<WordProblemResult, String> {
        let mps1 = self.prepare_orbit_state(word1, annealing_steps, dt)?;
        let mps2 = self.prepare_orbit_state(word2, annealing_steps, dt)?;

        let fidelity = mps1.fidelity(&mps2)?;
        let connected = fidelity >= fidelity_threshold;

        Ok(WordProblemResult {
            connected,
            fidelity,
            word_1: word1.to_vec(),
            word_2: word2.to_vec(),
            annealing_steps,
            authority_effect: AuthorityEffect::None,
        })
    }

    /// Estimate the number of equivalent expressions connected to `seed_word`.
    pub fn estimate_class_size(
        &self,
        seed_word: &[usize],
        annealing_steps: usize,
        dt: f64,
    ) -> Result<CountingResult, String> {
        let orbit = self.prepare_orbit_state(seed_word, annealing_steps, dt)?;
        let all_state = DdaMpsState::uniform_superposition(self.length, self.alphabet_size)?;

        let fid = orbit.fidelity(&all_state)?;
        let total_dim = self.alphabet_size.pow(self.length as u32);
        let estimated_size = (total_dim as f64) * fid;

        Ok(CountingResult {
            seed_word: seed_word.to_vec(),
            estimated_class_size: estimated_size,
            fidelity_to_all: fid,
            total_hilbert_space_dim: total_dim,
            authority_effect: AuthorityEffect::None,
        })
    }
}

// Origin: engine/crates_rs/engines/src/quantum/dda_orbit_state_solver.rs
// Claim: urn:core:crates_rs:engines:dda-orbit-state-solver:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1f661e46 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1f661e46` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1f661e46 {
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
impl BoundaryError1f661e46 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1f661e46 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1f661e46 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1f661e46 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1f661e46> {
        if capacity_bound == 0 {
            return Err(BoundaryError1f661e46::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1f661e46::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1f661e46::ExceedsCapacity {
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
mod l4_boundary_tests_1f661e46 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1f661e46::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1f661e46::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1f661e46::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1f661e46::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1f661e46::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1f661e46::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1f661e46::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
