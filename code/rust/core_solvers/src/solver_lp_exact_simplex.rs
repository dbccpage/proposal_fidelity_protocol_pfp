//! Exact weighted-ℓ¹ projection by Sparse Revised Simplex over ℚ.
//!
//! Solves, over $\mathbb{Q}$ and with no floating point anywhere:
//!
//! ```text
//! minimize   ‖ target − M γ ‖_{1,w}   over γ ∈ Q^k
//! ```
//!
//! and returns the minimizer `γ`, the residual `z = target − Mγ`, the exact
//! optimal value, **and a dual witness** `y` with
//!
//! ```text
//! Mᵀ y = 0,     |y_e| ≤ w_e,     yᵀ·target = value,
//! ```
//!
//! which is precisely the certificate shape
//! [`core_functional::phi1::Phi1Functional::verify_exact_certificate`]
//! replays. This module *proposes*; that verifier decides. Nothing here mints
//! authority.
//!
//! # Formulation & Column Layout
//!
//! Split free coefficients and signed residuals into non-negative parts:
//! `γ = γ⁺ − γ⁻` and `z = p − n`:
//!
//! ```text
//! min  Σ_e w_e (p_e + n_e)
//! s.t. M γ⁺ − M γ⁻ + p − n = target,      γ⁺, γ⁻, p, n ≥ 0.
//! ```
//!
//! There are $m$ rows and $N = 2k + 2m$ total columns:
//! - $j \in [0, k)$: $\gamma^+_j$, cost $0$, column $+M_{\cdot, j}$
//! - $j \in [k, 2k)$: $\gamma^-_j$, cost $0$, column $-M_{\cdot, j-k}$
//! - $j \in [2k, 2k+m)$: $p_e$, cost $w_e$, column $+e_e$
//! - $j \in [2k+m, 2k+2m)$: $n_e$, cost $w_e$, column $-e_e$
//!
//! # Sparse Revised Simplex & Basis Maintenance
//!
//! Rather than maintaining an $m \times (2k+2m)$ dense tableau, this module uses
//! a **Sparse Revised Simplex**:
//! - **Sparse Column Generator**: Columns are generated in $O(\text{nnz})$ on-demand.
//! - **Exact LU & Product Form of the Inverse (PFI)**: The basis inverse $B^{-1}$ is
//!   maintained via exact rational Eta matrices ($E_t^{-1} \dots E_1^{-1} B_0^{-1}$),
//!   with periodic dense exact LU refactorization using first-nonzero row pivots.
//! - **BTRAN ($B^T y = c_B$)**: Computes dual multipliers directly.
//! - **Pricing**: Reduced costs $z_j = c_j - y^T A_j$ are computed via sparse
//!   matrix-vector products $(M^T y)_j$.
//! - **Pricing heuristic**: Squares reduced costs and divides by positive rational
//!   column weights. This is not a full Devex or steepest-edge update.
//! - **Anti-Cycling**: After twenty consecutive degenerate pivots, Bland's rule
//!   remains enabled for the rest of the solve. Pivot exhaustion is a refusal.
//!
//! `AuthorityEffect: None.`

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use core_functional::phi1::Phi1Functional;

/// An exactly solved weighted-ℓ¹ projection.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct L1ProjectionSolution {
    /// The minimizing coefficients `γ`.
    pub coefficients: Vec<BigRational>,
    /// The residual `z = target − Mγ`.
    pub residual: Vec<BigRational>,
    /// The dual witness `y`: annihilates `im(M)`, bounded by the weights,
    /// and pairs with `target` to the optimal value.
    pub dual: Vec<BigRational>,
    /// The exact optimal value `‖z‖_{1,w}`.
    pub value: BigRational,
    /// Simplex pivots performed (diagnostic).
    pub iterations: usize,
}

#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum L1LpError {
    #[error("target has {target} coordinates but the map has {rows} rows")]
    DimensionMismatch { target: usize, rows: usize },
    #[error("map row {row} has {actual} columns, expected {expected}")]
    RaggedMap {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("weight at index {0} is not strictly positive")]
    NonPositiveWeight(usize),
    #[error("simplex exhausted its declared iteration budget of {budget}")]
    IterationBudgetExceeded { budget: usize },
    #[error("simplex reported an unbounded ray, inconsistent with a norm objective bounded below by zero")]
    Unbounded,
    #[error("singular basis encountered during refactorization")]
    SingularBasis,
    #[error("a rational input has a zero denominator")]
    InvalidRational,
    #[error("sparse column has {indices} indices but {values} values")]
    SparseColumnShape { indices: usize, values: usize },
    #[error("sparse index {index} at position {position} is outside dense dimension {dimension}")]
    SparseIndexOutOfBounds {
        position: usize,
        index: usize,
        dimension: usize,
    },
    #[error(transparent)]
    Resource(#[from] core_kernel::resource_limits::ResourceError),
    #[error(transparent)]
    Certificate(#[from] core_functional::phi1::ExactPhi1CertificateError),
}

#[inline]
fn zero() -> BigRational {
    BigRational::from_integer(BigInt::from(0))
}

#[inline]
fn one() -> BigRational {
    BigRational::from_integer(BigInt::from(1))
}

/// Sparse column of rational numbers.
#[derive(Debug, Clone, Default)]
pub struct SparseColumn {
    pub indices: Vec<usize>,
    pub values: Vec<BigRational>,
}

impl SparseColumn {
    #[inline]
    pub fn new() -> Self {
        Self {
            indices: Vec::new(),
            values: Vec::new(),
        }
    }

    #[inline]
    pub fn singleton(row: usize, val: BigRational) -> Self {
        Self {
            indices: vec![row],
            values: vec![val],
        }
    }

    #[inline]
    pub fn dot_dense(&self, dense: &[BigRational]) -> Result<BigRational, L1LpError> {
        if self.indices.len() != self.values.len() {
            return Err(L1LpError::SparseColumnShape {
                indices: self.indices.len(),
                values: self.values.len(),
            });
        }
        if self.values.iter().chain(dense).any(|q| q.denom().is_zero()) {
            return Err(L1LpError::InvalidRational);
        }
        if let Some((position, &index)) = self
            .indices
            .iter()
            .enumerate()
            .find(|(_, index)| **index >= dense.len())
        {
            return Err(L1LpError::SparseIndexOutOfBounds {
                position,
                index,
                dimension: dense.len(),
            });
        }
        let mut sum = zero();
        for (&row, val) in self.indices.iter().zip(&self.values) {
            sum += val * &dense[row];
        }
        Ok(sum)
    }
}

/// Exact rational LU factorization with partial row pivoting of an $m \times m$ matrix.
#[derive(Debug, Clone)]
struct ExactRationalLU {
    m: usize,
    /// Packed LU: L has unit diagonal (implicit), U has non-zero diagonal.
    lu: Vec<Vec<BigRational>>,
    /// Permutation vector: row $i$ of permuted matrix was original row $p[i]$.
    p: Vec<usize>,
}

impl ExactRationalLU {
    /// Factorize matrix $B$ given by its columns.
    fn factorize(m: usize, columns: &[SparseColumn]) -> Result<Self, L1LpError> {
        let mut lu = vec![vec![zero(); m]; m];
        for (col, sc) in columns.iter().enumerate() {
            for (&row, val) in sc.indices.iter().zip(&sc.values) {
                lu[row][col] = val.clone();
            }
        }
        let mut p: Vec<usize> = (0..m).collect();

        for k in 0..m {
            // Find pivot in column k on or below diagonal
            let mut pivot_row = None;
            for r in k..m {
                if !lu[r][k].is_zero() {
                    pivot_row = Some(r);
                    break;
                }
            }
            let Some(pivot_row) = pivot_row else {
                return Err(L1LpError::SingularBasis);
            };

            if pivot_row != k {
                lu.swap(k, pivot_row);
                p.swap(k, pivot_row);
            }

            let pivot = lu[k][k].clone();
            for r in (k + 1)..m {
                if !lu[r][k].is_zero() {
                    let factor = lu[r][k].clone() / &pivot;
                    lu[r][k] = factor.clone(); // store L entry
                    for c in (k + 1)..m {
                        let delta = &factor * &lu[k][c];
                        lu[r][c] -= delta;
                    }
                }
            }
        }

        Ok(Self { m, lu, p })
    }

    /// Factorize a diagonal sign matrix diag(s_0, ..., s_{m-1}) where s_i ∈ {+1, -1}.
    fn from_diagonal_signs(signs: &[bool]) -> Self {
        let m = signs.len();
        let mut lu = vec![vec![zero(); m]; m];
        for (i, &sign) in signs.iter().enumerate() {
            lu[i][i] = if sign { one() } else { -one() };
        }
        let p = (0..m).collect();
        Self { m, lu, p }
    }

    /// Forward solve $L y = P b$ then back solve $U x = y$.
    fn solve(&self, b: &[BigRational]) -> Vec<BigRational> {
        let m = self.m;
        // Apply row permutation: pb[i] = b[p[i]]
        let mut y = Vec::with_capacity(m);
        for i in 0..m {
            y.push(b[self.p[i]].clone());
        }

        // Forward solve L y = pb (L has unit diagonal)
        for i in 0..m {
            for j in 0..i {
                if !self.lu[i][j].is_zero() {
                    let delta = &self.lu[i][j] * &y[j];
                    y[i] -= delta;
                }
            }
        }

        // Back solve U x = y
        let mut x = vec![zero(); m];
        for i in (0..m).rev() {
            let mut sum = y[i].clone();
            for j in (i + 1)..m {
                if !self.lu[i][j].is_zero() {
                    sum -= &self.lu[i][j] * &x[j];
                }
            }
            x[i] = sum / &self.lu[i][i];
        }

        x
    }

    /// Solve $B^T y = c$, which is $(P^T L U)^T y = c \iff U^T L^T P y = c$.
    fn solve_transpose(&self, c: &[BigRational]) -> Vec<BigRational> {
        let m = self.m;
        // Solve U^T w = c
        let mut w = vec![zero(); m];
        for i in 0..m {
            let mut sum = c[i].clone();
            for j in 0..i {
                if !self.lu[j][i].is_zero() {
                    sum -= &self.lu[j][i] * &w[j];
                }
            }
            w[i] = sum / &self.lu[i][i];
        }

        // Solve L^T z = w (L has unit diagonal)
        let mut z = vec![zero(); m];
        for i in (0..m).rev() {
            let mut sum = w[i].clone();
            for j in (i + 1)..m {
                if !self.lu[j][i].is_zero() {
                    sum -= &self.lu[j][i] * &z[j];
                }
            }
            z[i] = sum;
        }

        // y = P^T z, i.e. y[p[i]] = z[i]
        let mut y = vec![zero(); m];
        for i in 0..m {
            y[self.p[i]] = z[i].clone();
        }

        y
    }
}

/// An elementary Eta matrix representing $E^{-1} = I + (\eta - e_p) e_p^T$.
#[derive(Debug, Clone)]
struct EtaMatrix {
    p: usize,
    /// Sparse entries $(i, \eta_i)$ of the column vector η.
    entries: Vec<(usize, BigRational)>,
}

impl EtaMatrix {
    fn from_d(p: usize, d: &[BigRational]) -> Self {
        let d_p = &d[p];
        let inv_dp = one() / d_p;
        let mut entries = Vec::new();
        for (i, val) in d.iter().enumerate() {
            if i == p {
                entries.push((p, inv_dp.clone()));
            } else if !val.is_zero() {
                entries.push((i, -(val * &inv_dp)));
            }
        }
        Self { p, entries }
    }

    /// Apply $E^{-1}$ to vector $v$ in place:
    /// $v'_p = v_p / d_p = \eta_p v_p$
    /// $v'_i = v_i - (d_i / d_p) v_p = v_i + \eta_i v_p$.
    #[inline]
    fn apply_forward(&self, v: &mut [BigRational]) {
        let vp = v[self.p].clone();
        if vp.is_zero() {
            return;
        }
        let mut new_vp = zero();
        for &(i, ref eta_val) in &self.entries {
            if i == self.p {
                new_vp = eta_val * &vp;
            } else {
                let delta = eta_val * &vp;
                v[i] += delta;
            }
        }
        v[self.p] = new_vp;
    }

    /// Apply $E^{-T}$ to vector $y$ in place:
    /// $y'_i = y_i$ for $i \ne p$
    /// $y'_p = \sum_i \eta_i y_i$.
    #[inline]
    fn apply_transpose(&self, y: &mut [BigRational]) {
        let mut sum = zero();
        for &(i, ref eta_val) in &self.entries {
            sum += eta_val * &y[i];
        }
        y[self.p] = sum;
    }
}

/// Exact basis factorization engine maintaining $B^{-1}$ via LU + Eta chain.
struct BasisFactorization {
    m: usize,
    base_lu: ExactRationalLU,
    etas: Vec<EtaMatrix>,
}

impl BasisFactorization {
    fn new_from_signs(signs: &[bool]) -> Self {
        let m = signs.len();
        let base_lu = ExactRationalLU::from_diagonal_signs(signs);
        Self {
            m,
            base_lu,
            etas: Vec::new(),
        }
    }

    /// FTRAN: Compute $d = B^{-1} a$ for a given sparse column $a$.
    fn ftran(&self, a: &SparseColumn) -> Vec<BigRational> {
        let mut dense_a = vec![zero(); self.m];
        for (&row, val) in a.indices.iter().zip(&a.values) {
            dense_a[row] = val.clone();
        }
        let mut v = self.base_lu.solve(&dense_a);
        for eta in &self.etas {
            eta.apply_forward(&mut v);
        }
        v
    }

    /// BTRAN: Compute $y = B^{-T} c$.
    fn btran(&self, c: &[BigRational]) -> Vec<BigRational> {
        let mut v = c.to_vec();
        for eta in self.etas.iter().rev() {
            eta.apply_transpose(&mut v);
        }
        self.base_lu.solve_transpose(&v)
    }

    /// Update basis: add Eta matrix for leaving row $p$ and column representation $d$.
    fn add_eta(&mut self, p: usize, d: &[BigRational]) {
        self.etas.push(EtaMatrix::from_d(p, d));
    }

    /// Re-factorize the basis directly from current basic columns.
    fn refactorize(
        &mut self,
        basis_vars: &[usize],
        get_column: &dyn Fn(usize) -> SparseColumn,
    ) -> Result<(), L1LpError> {
        let cols: Vec<SparseColumn> = basis_vars.iter().map(|&v| get_column(v)).collect();
        let fresh_lu = ExactRationalLU::factorize(self.m, &cols)?;
        self.base_lu = fresh_lu;
        self.etas.clear();
        Ok(())
    }
}

fn validate_l1_dimensions_and_weights(
    target: &[BigRational],
    weights: &[BigRational],
    map_rows: &[Vec<BigRational>],
) -> Result<(), L1LpError> {
    let m = target.len();
    if weights.len() != m {
        return Err(L1LpError::DimensionMismatch {
            target: m,
            rows: weights.len(),
        });
    }
    if !map_rows.is_empty() && map_rows.len() != m {
        return Err(L1LpError::DimensionMismatch {
            target: m,
            rows: map_rows.len(),
        });
    }
    for (index, weight) in weights.iter().enumerate() {
        if !weight.is_positive() {
            return Err(L1LpError::NonPositiveWeight(index));
        }
    }
    Ok(())
}

fn validate_l1_inputs(
    target: &[BigRational],
    weights: &[BigRational],
    map_rows: &[Vec<BigRational>],
) -> Result<usize, L1LpError> {
    if target
        .iter()
        .chain(weights)
        .chain(map_rows.iter().flatten())
        .any(|q| q.denom().is_zero())
    {
        return Err(L1LpError::InvalidRational);
    }
    validate_l1_dimensions_and_weights(target, weights, map_rows)?;
    let k = map_rows.first().map(Vec::len).unwrap_or(0);
    for (row, entries) in map_rows.iter().enumerate() {
        if entries.len() != k {
            return Err(L1LpError::RaggedMap {
                row,
                expected: k,
                actual: entries.len(),
            });
        }
    }
    Ok(k)
}

fn build_sparse_m_cols(
    map_rows: &[Vec<BigRational>],
    m: usize,
    k: usize,
) -> Vec<SparseColumn> {
    // Convert map_rows into sparse column representation of M.
    let mut sparse_m_cols: Vec<SparseColumn> = Vec::with_capacity(k);
    for j in 0..k {
        let mut col = SparseColumn::new();
        for (i, row) in map_rows.iter().enumerate().take(m) {
            if !row[j].is_zero() {
                col.indices.push(i);
                col.values.push(row[j].clone());
            }
        }
        sparse_m_cols.push(col);
    }
    sparse_m_cols
}

fn constraint_column(
    sparse_m_cols: &[SparseColumn],
    m: usize,
    k: usize,
    j: usize,
) -> SparseColumn {
    if j < k {
        sparse_m_cols[j].clone()
    } else if j < 2 * k {
        let orig = &sparse_m_cols[j - k];
        SparseColumn {
            indices: orig.indices.clone(),
            values: orig.values.iter().map(|v| -v).collect(),
        }
    } else if j < 2 * k + m {
        let row = j - 2 * k;
        SparseColumn::singleton(row, one())
    } else {
        let row = j - (2 * k + m);
        SparseColumn::singleton(row, -one())
    }
}

fn initial_devex_weights(
    sparse_m_cols: &[SparseColumn],
    n_cols: usize,
    k: usize,
) -> Vec<BigRational> {
    // Scaled-pricing column weights: tau_j >= 1; this is not full Devex.
    (0..n_cols)
        .map(|j| {
            if j < 2 * k {
                let col_idx = if j < k { j } else { j - k };
                let norm_sq: BigRational =
                    sparse_m_cols[col_idx].values.iter().map(|v| v * v).sum();
                one() + norm_sq
            } else {
                one() + one() // unit column squared norm = 1 + 1
            }
        })
        .collect()
}

fn compute_dual_y(
    basis: &[usize],
    weights: &[BigRational],
    basis_fac: &BasisFactorization,
    m: usize,
    n_p: usize,
    n_n: usize,
) -> Vec<BigRational> {
    let mut c_b = vec![zero(); m];
    for (i, &b_var) in basis.iter().enumerate() {
        if b_var >= n_p {
            let e = if b_var < n_n {
                b_var - n_p
            } else {
                b_var - n_n
            };
            c_b[i] = weights[e].clone();
        }
    }
    basis_fac.btran(&c_b)
}

fn column_reduced_cost(
    j: usize,
    k: usize,
    n_p: usize,
    n_n: usize,
    m_t_y: &[BigRational],
    weights: &[BigRational],
    y: &[BigRational],
) -> BigRational {
    if j < k {
        -&m_t_y[j]
    } else if j < 2 * k {
        m_t_y[j - k].clone()
    } else if j < n_n {
        let e = j - n_p;
        &weights[e] - &y[e]
    } else {
        let e = j - n_n;
        &weights[e] + &y[e]
    }
}

#[allow(clippy::too_many_arguments)]
fn select_entering_column(
    basis: &[usize],
    m_t_y: &[BigRational],
    weights: &[BigRational],
    y: &[BigRational],
    devex_weights: &[BigRational],
    k: usize,
    n_p: usize,
    n_n: usize,
    n_cols: usize,
    bland_active: bool,
) -> Option<usize> {
    // 3. Compute reduced costs z_j = c_j - y^T A_j and select entering candidate.
    // A non-basic column is eligible to enter if z_j < 0.
    let mut entering = None;
    let mut best_score: Option<(BigRational, BigRational)> = None;

    for j in 0..n_cols {
        if basis.contains(&j) {
            continue;
        }
        let reduced_cost = column_reduced_cost(j, k, n_p, n_n, m_t_y, weights, y);
        if !reduced_cost.is_negative() {
            continue;
        }
        if bland_active {
            return Some(j);
        }

        // Scaled reduced-cost heuristic: maximize (-z_j)^2 / tau_j.
        let z_sq = &reduced_cost * &reduced_cost;
        let tau = &devex_weights[j];
        let take = best_score.as_ref().is_none_or(|(cur_num, cur_den)| {
            // z_sq / tau > cur_num / cur_den <=> z_sq * cur_den > cur_num * tau
            (&z_sq * cur_den) > (cur_num * tau)
        });
        if take {
            best_score = Some((z_sq, tau.clone()));
            entering = Some(j);
        }
    }
    entering
}

fn should_take_leaving_row(
    ratio: &BigRational,
    min_ratio: &Option<BigRational>,
    leaving: Option<usize>,
    basis: &[usize],
    i: usize,
) -> bool {
    match min_ratio {
        None => true,
        Some(current) => {
            if ratio < current {
                true
            } else if ratio == current {
                // Lexicographic / Bland tie-breaking on basic variable index
                leaving.map(|row| basis[i] < basis[row]).unwrap_or(true)
            } else {
                false
            }
        }
    }
}

fn select_leaving_row(
    d: &[BigRational],
    x_b: &[BigRational],
    basis: &[usize],
    m: usize,
) -> Result<(usize, BigRational), L1LpError> {
    // 5. Ratio test: Find leaving row p = argmin { x_B(i) / d_i | d_i > 0 }.
    let mut leaving: Option<usize> = None;
    let mut min_ratio: Option<BigRational> = None;

    for i in 0..m {
        if !d[i].is_positive() {
            continue;
        }
        let ratio = &x_b[i] / &d[i];
        if should_take_leaving_row(&ratio, &min_ratio, leaving, basis, i) {
            min_ratio = Some(ratio);
            leaving = Some(i);
        }
    }

    let leaving = leaving.ok_or(L1LpError::Unbounded)?;
    let step_length = min_ratio.ok_or(L1LpError::SingularBasis)?;
    Ok((leaving, step_length))
}

fn update_primal_and_pricing(
    x_b: &mut [BigRational],
    devex_weights: &mut [BigRational],
    d: &[BigRational],
    leaving: usize,
    entering: usize,
    step_length: &BigRational,
) {
    // 6. Update primal basic values:
    // x_B_new(leaving) = step_length
    // x_B_new(i) = x_B(i) - step_length * d_i for i != leaving.
    for (i, x_val) in x_b.iter_mut().enumerate() {
        if i == leaving {
            *x_val = step_length.clone();
        } else {
            let delta = step_length * &d[i];
            *x_val -= delta;
        }
    }

    // 7. Update the entering-column pricing weight (not full Devex).
    let d_p_sq = &d[leaving] * &d[leaving];
    let new_tau_q = &devex_weights[entering] / &d_p_sq;
    devex_weights[entering] = if new_tau_q < one() { one() } else { new_tau_q };
}

fn extract_clamped_dual(y: &[BigRational], weights: &[BigRational], m: usize) -> Vec<BigRational> {
    // Dual witness from reduced costs: y_e = w_e - z_{p_e}.
    // Since z_{p_e} = w_e - y_e, we have y_e = y[e] clamped to [-w_e, w_e].
    (0..m)
        .map(|e| {
            let y_val = y[e].clone();
            // Clamp mathematically to [-w_e, w_e] in case of basic slack degeneracy.
            if y_val > weights[e] {
                weights[e].clone()
            } else if y_val < -weights[e].clone() {
                -weights[e].clone()
            } else {
                y_val
            }
        })
        .collect()
}

fn build_l1_solution(
    target: &[BigRational],
    weights: &[BigRational],
    map_rows: &[Vec<BigRational>],
    basis: &[usize],
    x_b: &[BigRational],
    basis_fac: &BasisFactorization,
    k: usize,
    iterations: usize,
) -> Result<L1ProjectionSolution, L1LpError> {
    let m = target.len();
    let n_gamma_pos = 0usize;
    let n_gamma_neg = k;
    let n_p = 2 * k;
    let n_n = 2 * k + m;
    let n_cols = 2 * k + 2 * m;

    // Primal readout.
    let mut primal = vec![zero(); n_cols];
    for (i, &basic) in basis.iter().enumerate() {
        primal[basic] = x_b[i].clone();
    }

    let coefficients: Vec<BigRational> = (0..k)
        .map(|j| primal[n_gamma_pos + j].clone() - primal[n_gamma_neg + j].clone())
        .collect();

    // Dual readout from final optimal multipliers.
    let y = compute_dual_y(basis, weights, basis_fac, m, n_p, n_n);
    let dual = extract_clamped_dual(&y, weights, m);

    // The simplex supplies a proposal. Only canonical primal/dual replay
    // calculates and establishes the quotient value returned to callers.
    let empty_map;
    let boundary: &[Vec<BigRational>] = if map_rows.is_empty() {
        empty_map = vec![Vec::new(); m];
        &empty_map
    } else {
        map_rows
    };
    let evaluated =
        Phi1Functional::evaluate_exact_witness(target, boundary, weights, &coefficients, &dual)?;
    Ok(L1ProjectionSolution {
        coefficients,
        residual: evaluated.primal_residual().to_vec(),
        dual,
        value: evaluated.value().clone(),
        iterations,
    })
}

/// Solve the exact weighted-ℓ¹ projection of `target` onto the column space
/// of `map_rows` (an `m × k` matrix given row-wise).
///
/// `iteration_budget` bounds the pivot count; a sane default is
/// `64 * (m + k) + 1024`.
pub fn solve_weighted_l1_projection(
    target: &[BigRational],
    weights: &[BigRational],
    map_rows: &[Vec<BigRational>],
    iteration_budget: usize,
) -> Result<L1ProjectionSolution, L1LpError> {
    let m = target.len();
    let k = validate_l1_inputs(target, weights, map_rows)?;

    // Column layout:
    // [ γ⁺ (k) | γ⁻ (k) | p (m) | n (m) ]
    // Total columns N = 2*k + 2*m.
    let n_p = 2 * k;
    let n_n = 2 * k + m;
    let n_cols = 2 * k + 2 * m;

    let sparse_m_cols = build_sparse_m_cols(map_rows, m, k);

    // Helper closure to construct column $j$ of constraint matrix A.
    let get_column = |j: usize| -> SparseColumn { constraint_column(&sparse_m_cols, m, k, j) };

    // Row sign s_e makes initial basic RHS non-negative.
    let sign: Vec<bool> = target.iter().map(|value| !value.is_negative()).collect();

    // Initial basis: the residual part that carries |target_e|.
    let mut basis: Vec<usize> = (0..m)
        .map(|e| if sign[e] { n_p + e } else { n_n + e })
        .collect();

    // Initial basic values x_B = |target_e| >= 0.
    let mut x_b: Vec<BigRational> = target.iter().map(|t| t.abs()).collect();

    // Initialize basis factorization.
    let mut basis_fac = BasisFactorization::new_from_signs(&sign);
    let mut devex_weights = initial_devex_weights(&sparse_m_cols, n_cols, k);

    let mut iterations = 0usize;
    let mut degenerate_stall_count = 0usize;
    let mut bland_active = false;
    const REFACTOR_INTERVAL: usize = 40;

    loop {
        // 1. BTRAN: Compute dual vector y such that B^T y = c_B.
        let y = compute_dual_y(&basis, weights, &basis_fac, m, n_p, n_n);

        // 2. Compute M^T y once for all γ columns.
        let m_t_y: Vec<BigRational> = sparse_m_cols
            .iter()
            .map(|sc| sc.dot_dense(&y))
            .collect::<Result<Vec<_>, _>>()?;

        // Use Bland fallback if degenerate stalling occurs.
        bland_active |= degenerate_stall_count >= 20;

        let Some(entering) = select_entering_column(
            &basis,
            &m_t_y,
            weights,
            &y,
            &devex_weights,
            k,
            n_p,
            n_n,
            n_cols,
            bland_active,
        ) else {
            break; // All reduced costs >= 0: optimal basic feasible solution reached!
        };

        // Charge the pivot before factorization or basis mutation. Pricing an
        // already optimal basis consumes no pivot, including at budget zero.
        if iterations >= iteration_budget {
            return Err(L1LpError::IterationBudgetExceeded {
                budget: iteration_budget,
            });
        }

        // 4. FTRAN: Compute entering column representation in current basis d = B^{-1} A_q.
        let a_q = get_column(entering);
        let d = basis_fac.ftran(&a_q);

        let (leaving, step_length) = select_leaving_row(&d, &x_b, &basis, m)?;
        if step_length.is_zero() {
            degenerate_stall_count = degenerate_stall_count.saturating_add(1);
        } else {
            degenerate_stall_count = 0;
        }

        update_primal_and_pricing(
            &mut x_b,
            &mut devex_weights,
            &d,
            leaving,
            entering,
            &step_length,
        );

        // 8. Update basis factorization.
        basis[leaving] = entering;
        basis_fac.add_eta(leaving, &d);

        iterations += 1;

        // Periodic refactorization to bound Eta chain length.
        if basis_fac.etas.len() >= REFACTOR_INTERVAL {
            basis_fac.refactorize(&basis, &get_column)?;
        }
    }

    build_l1_solution(
        target,
        weights,
        map_rows,
        &basis,
        &x_b,
        &basis_fac,
        k,
        iterations,
    )
}

/// [`solve_weighted_l1_projection`] for a map, target and weights held as
/// nalgebra matrices and vectors, with the default iteration budget.
pub fn solve_weighted_l1_projection_nalgebra(
    matrix: &nalgebra::DMatrix<BigRational>,
    rhs: &nalgebra::DVector<BigRational>,
    weights: &nalgebra::DVector<BigRational>,
) -> Result<L1ProjectionSolution, L1LpError> {
    let (nrows, ncols) = matrix.shape();
    // The declared default pivot budget must fit before any input cloning.
    let dimensions = nrows
        .checked_add(ncols)
        .ok_or(core_kernel::resource_limits::ResourceError::CountOverflow)?;
    let scaled_budget = dimensions
        .checked_mul(64)
        .ok_or(core_kernel::resource_limits::ResourceError::CountOverflow)?;
    let budget = scaled_budget
        .checked_add(1024)
        .ok_or(core_kernel::resource_limits::ResourceError::CountOverflow)?;
    if rhs.len() != nrows {
        return Err(L1LpError::DimensionMismatch {
            target: rhs.len(),
            rows: nrows,
        });
    }
    if weights.len() != nrows {
        return Err(L1LpError::DimensionMismatch {
            target: nrows,
            rows: weights.len(),
        });
    }
    if nrows == 0 {
        // An empty row representation cannot retain a nonzero declared width.
        // Every coefficient is optimal; choose the zero vector of that width.
        let limits = core_kernel::resource_limits::OperationLimits::default();
        let coefficient_limit = limits.max_memory_bytes / std::mem::size_of::<BigRational>();
        let mut coefficients = Vec::new();
        core_kernel::resource_limits::check_and_reserve(
            &mut coefficients,
            ncols,
            coefficient_limit,
        )?;
        coefficients.resize_with(ncols, zero);
        return Ok(L1ProjectionSolution {
            coefficients,
            residual: vec![],
            dual: vec![],
            value: zero(),
            iterations: 0,
        });
    }
    let map_rows: Vec<Vec<BigRational>> = (0..nrows)
        .map(|r| (0..ncols).map(|c| matrix[(r, c)].clone()).collect())
        .collect();
    let target: Vec<BigRational> = rhs.iter().cloned().collect();
    let w: Vec<BigRational> = weights.iter().cloned().collect();
    solve_weighted_l1_projection(&target, &w, &map_rows, budget)
}

// Origin: engine/crates_rs/core_solvers/src/solver_lp_exact_simplex.rs
// Claim: urn:core:crates_rs:core-solvers:solver-lp-exact-simplex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn int(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn frac(numerator: i64, denominator: i64) -> BigRational {
        BigRational::new(BigInt::from(numerator), BigInt::from(denominator))
    }

    /// Columns of `d₀` for a directed cycle on `n` vertices, as rows.
    fn cycle_d0(n: usize) -> Vec<Vec<BigRational>> {
        (0..n)
            .map(|e| {
                let mut row = vec![int(0); n];
                row[e] = int(-1);
                row[(e + 1) % n] = int(1);
                row
            })
            .collect()
    }

    /// Every dual condition the downstream verifier checks must hold on the
    /// LP's own output, for every instance the tests exercise.
    fn assert_dual_is_valid(
        solution: &L1ProjectionSolution,
        target: &[BigRational],
        weights: &[BigRational],
        map_rows: &[Vec<BigRational>],
    ) {
        let k = map_rows.first().map(Vec::len).unwrap_or(0);
        for j in 0..k {
            let pairing: BigRational = (0..target.len())
                .map(|e| map_rows[e][j].clone() * solution.dual[e].clone())
                .sum();
            assert!(pairing.is_zero(), "dual must annihilate column {j}");
        }
        for e in 0..target.len() {
            assert!(
                solution.dual[e].abs() <= weights[e],
                "dual exceeds the weight bound at {e}"
            );
        }
        let pairing: BigRational = solution
            .dual
            .iter()
            .zip(target)
            .map(|(y, t)| y.clone() * t.clone())
            .sum();
        assert_eq!(pairing, solution.value, "zero duality gap is required");
    }

    /// The 3-cycle with unit circulation: no potential removes it, and the
    /// exact minimum is 3.
    #[test]
    fn cycle_circulation_has_exact_distance_three() {
        let target = vec![int(1), int(1), int(1)];
        let weights = vec![int(1), int(1), int(1)];
        let map = cycle_d0(3);
        let solution = solve_weighted_l1_projection(&target, &weights, &map, 1024).unwrap();
        assert_eq!(solution.value, int(3));
        assert_dual_is_valid(&solution, &target, &weights, &map);
    }

    /// A pure gradient is removed exactly: distance zero, residual zero.
    #[test]
    fn a_pure_gradient_projects_to_zero() {
        // d0 of potential (0, 1, 3) on the 3-cycle: (1, 2, -3).
        let target = vec![int(1), int(2), int(-3)];
        let weights = vec![int(1), int(1), int(1)];
        let map = cycle_d0(3);
        let solution = solve_weighted_l1_projection(&target, &weights, &map, 1024).unwrap();
        assert_eq!(solution.value, int(0));
        assert!(solution.residual.iter().all(BigRational::is_zero));
        assert_dual_is_valid(&solution, &target, &weights, &map);
    }

    /// Weights route the answer, and the optimum can be a genuine fraction —
    /// the exact rational path is not decorative.
    #[test]
    fn weights_route_the_optimum_and_fractions_survive() {
        let target = vec![int(1), int(1), int(1)];
        let weights = vec![int(2), int(2), int(5)];
        let map = cycle_d0(3);
        let solution = solve_weighted_l1_projection(&target, &weights, &map, 1024).unwrap();
        // Every representative carries circulation 3; the cheapest place to
        // hold it costs 3 · min_e w_e = 6.
        assert_eq!(solution.value, int(6));
        assert_dual_is_valid(&solution, &target, &weights, &map);

        let fractional = vec![frac(1, 3), frac(1, 2), frac(1, 6)];
        let unit = vec![int(1), int(1), int(1)];
        let solution =
            solve_weighted_l1_projection(&fractional, &unit, &cycle_d0(3), 1024).unwrap();
        assert_eq!(solution.value, int(1), "circulation 1/3+1/2+1/6 = 1");
        assert_dual_is_valid(&solution, &fractional, &unit, &cycle_d0(3));
    }

    /// An empty map (no repair directions) leaves the raw weighted norm, and
    /// the dual is just the signed weight vector.
    #[test]
    fn an_empty_map_returns_the_raw_norm() {
        let target = vec![int(2), int(-3)];
        let weights = vec![int(1), int(4)];
        let solution = solve_weighted_l1_projection(&target, &weights, &[], 1024).unwrap();
        assert_eq!(solution.value, int(14)); // 1·2 + 4·3
        assert_dual_is_valid(&solution, &target, &weights, &[]);
    }

    /// **Differential test against brute force.** An independent
    /// basic-solution enumeration (the algorithm this LP replaced) must agree
    /// with the simplex on every instance of a systematic sweep. This is what
    /// licenses removing the enumeration: not that the LP looks right, but
    /// that it reproduces the method it supersedes.
    #[test]
    fn the_simplex_agrees_with_brute_force_enumeration() {
        // Two triangles sharing an edge: 5 edges, 4 vertices.
        let edges = [(0usize, 1usize), (1, 2), (2, 0), (1, 3), (3, 2)];
        let m = edges.len();
        let d0: Vec<Vec<BigRational>> = edges
            .iter()
            .map(|&(tail, head)| {
                let mut row = vec![int(0); 4];
                row[tail] = int(-1);
                row[head] = int(1);
                row
            })
            .collect();

        /// Solve a square rational system by Gauss–Jordan; `None` if singular.
        fn solve_square(
            matrix: &[Vec<BigRational>],
            rhs: &[BigRational],
        ) -> Option<Vec<BigRational>> {
            let n = rhs.len();
            let mut a: Vec<Vec<BigRational>> = matrix
                .iter()
                .zip(rhs)
                .map(|(row, b)| {
                    let mut r = row.clone();
                    r.push(b.clone());
                    r
                })
                .collect();
            for col in 0..n {
                let found = (col..n).find(|&r| !a[r][col].is_zero())?;
                a.swap(col, found);
                let pivot = a[col][col].clone();
                for value in a[col].iter_mut() {
                    *value /= pivot.clone();
                }
                for r in 0..n {
                    if r != col && !a[r][col].is_zero() {
                        let factor = a[r][col].clone();
                        for c in 0..=n {
                            let delta = factor.clone() * a[col][c].clone();
                            a[r][c] -= delta;
                        }
                    }
                }
            }
            Some((0..n).map(|r| a[r][n].clone()).collect())
        }

        /// Independent reference: an ℓ¹ projection attains its optimum at a
        /// point where `r = rank(M)` residual coordinates vanish on an
        /// invertible submatrix. Restrict to independent columns (so the
        /// system is square and the column space is unchanged), enumerate all
        /// `r`-subsets of rows, solve, and score. Enumeration, not simplex —
        /// which is the point of the comparison.
        fn brute_force(
            target: &[BigRational],
            weights: &[BigRational],
            map_rows: &[Vec<BigRational>],
        ) -> BigRational {
            let m = target.len();
            let k = map_rows[0].len();

            // Pivot columns of M, by row reduction on a working copy.
            let mut work: Vec<Vec<BigRational>> = map_rows.to_vec();
            let mut pivot_columns = Vec::new();
            let mut row = 0usize;
            for col in 0..k {
                let Some(found) = (row..m).find(|&r| !work[r][col].is_zero()) else {
                    continue;
                };
                work.swap(row, found);
                let pivot = work[row][col].clone();
                for value in work[row].iter_mut() {
                    *value /= pivot.clone();
                }
                for r in 0..m {
                    if r != row && !work[r][col].is_zero() {
                        let factor = work[r][col].clone();
                        for c in 0..k {
                            let delta = factor.clone() * work[row][c].clone();
                            work[r][c] -= delta;
                        }
                    }
                }
                pivot_columns.push(col);
                row += 1;
                if row == m {
                    break;
                }
            }
            let rank = pivot_columns.len();
            let reduced: Vec<Vec<BigRational>> = map_rows
                .iter()
                .map(|r| pivot_columns.iter().map(|&c| r[c].clone()).collect())
                .collect();

            let score = |gamma: &[BigRational]| -> BigRational {
                (0..m)
                    .map(|e| {
                        let mapped: BigRational = (0..rank)
                            .map(|j| reduced[e][j].clone() * gamma[j].clone())
                            .sum();
                        (target[e].clone() - mapped).abs() * weights[e].clone()
                    })
                    .sum()
            };

            let mut best: Option<BigRational> = None;
            if rank == 0 {
                return (0..m).map(|e| target[e].abs() * weights[e].clone()).sum();
            }
            let mut subset = vec![0usize; rank];
            fn rec(
                start: usize,
                depth: usize,
                rank: usize,
                m: usize,
                subset: &mut Vec<usize>,
                reduced: &[Vec<BigRational>],
                target: &[BigRational],
                score: &dyn Fn(&[BigRational]) -> BigRational,
                best: &mut Option<BigRational>,
            ) {
                if depth == rank {
                    let rows: Vec<Vec<BigRational>> =
                        subset.iter().map(|&r| reduced[r].clone()).collect();
                    let rhs: Vec<BigRational> = subset.iter().map(|&r| target[r].clone()).collect();
                    if let Some(gamma) = solve_square(&rows, &rhs) {
                        let value = score(&gamma);
                        if best.as_ref().map(|b| &value < b).unwrap_or(true) {
                            *best = Some(value);
                        }
                    }
                    return;
                }
                for row in start..m {
                    subset[depth] = row;
                    rec(
                        row + 1,
                        depth + 1,
                        rank,
                        m,
                        subset,
                        reduced,
                        target,
                        score,
                        best,
                    );
                }
            }
            rec(
                0,
                0,
                rank,
                m,
                &mut subset,
                &reduced,
                target,
                &score,
                &mut best,
            );
            best.expect("some r-subset must be invertible when rank = r")
        }

        let weights = vec![int(1), int(2), int(1), int(3), int(1)];
        // A systematic sweep over small integer targets.
        let mut checked = 0;
        for a in -2..=2i64 {
            for b in -2..=2i64 {
                for c in -1..=1i64 {
                    let target = vec![int(a), int(b), int(c), int(a - b), int(c + 1)];
                    let solution =
                        solve_weighted_l1_projection(&target, &weights, &d0, 4096).unwrap();
                    let reference = brute_force(&target, &weights, &d0);
                    assert_eq!(
                        solution.value, reference,
                        "simplex and enumeration disagree on {target:?}"
                    );
                    assert_dual_is_valid(&solution, &target, &weights, &d0);
                    checked += 1;
                }
            }
        }
        assert_eq!(checked, 75, "the sweep must actually run");
        let _ = m;
    }

    /// Scale: a carrier far beyond the old 12-edge enumeration fence solves
    /// exactly, in a pivot count the budget never approaches.
    #[test]
    fn a_forty_edge_instance_solves_exactly() {
        let n = 40;
        let map = cycle_d0(n);
        let target = vec![int(1); n];
        let weights = vec![int(1); n];
        let solution = solve_weighted_l1_projection(&target, &weights, &map, 8192).unwrap();
        assert_eq!(solution.value, int(40), "unit circulation on a 40-cycle");
        assert_dual_is_valid(&solution, &target, &weights, &map);
    }

    /// A weight that is not strictly positive is a typed refusal, not a
    /// silently degenerate LP.
    #[test]
    fn non_positive_weights_are_refused() {
        let target = vec![int(1), int(1), int(1)];
        let weights = vec![int(1), int(0), int(1)];
        assert_eq!(
            solve_weighted_l1_projection(&target, &weights, &cycle_d0(3), 1024),
            Err(L1LpError::NonPositiveWeight(1))
        );
    }

    #[test]
    fn pivot_fuel_admits_the_exact_boundary_and_free_optimality_replay() {
        let target = [int(1)];
        let weights = [int(1)];
        let map = [vec![int(1)]];
        assert!(matches!(
            solve_weighted_l1_projection(&target, &weights, &map, 0),
            Err(L1LpError::IterationBudgetExceeded { budget: 0 })
        ));
        let solution = solve_weighted_l1_projection(&target, &weights, &map, 1).unwrap();
        assert_eq!(solution.iterations, 1);
        assert!(solution.value.is_zero());
        assert_dual_is_valid(&solution, &target, &weights, &map);
        let empty_map = [vec![]];
        let raw = solve_weighted_l1_projection(&target, &weights, &empty_map, 0).unwrap();
        assert_eq!(raw.iterations, 0);
        assert_eq!(raw.value, int(1));
        assert_dual_is_valid(&raw, &target, &weights, &empty_map);
    }
}

#[cfg(test)]
mod public_boundary_tests {
    use super::*;

    fn q(n: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(n))
    }

    fn bad(n: i64) -> BigRational {
        BigRational::new_raw(BigInt::from(n), BigInt::from(0))
    }

    #[test]
    fn direct_l1_refuses_invalid_rationals_and_replays_exact_pivot_and_zero_pivot_optima() {
        // One positive repair direction exactly removes the target in one pivot.
        let solution = solve_weighted_l1_projection(&[q(1)], &[q(1)], &[vec![q(1)]], 1).unwrap();
        assert_eq!(solution.coefficients, vec![q(1)]);
        assert_eq!(solution.residual, vec![q(0)]);
        assert_eq!(solution.dual, vec![q(0)]);
        assert_eq!(solution.value, q(0));
        assert_eq!(solution.iterations, 1);
        assert_eq!(
            solve_weighted_l1_projection(&[q(1)], &[q(1)], &[vec![q(1)]], 0),
            Err(L1LpError::IterationBudgetExceeded { budget: 0 })
        );
        // No repair direction: weighted norm 3*|-2|=6 with the independent
        // saturating dual y=-3, requiring no pivot even at budget zero.
        let raw = solve_weighted_l1_projection(&[q(-2)], &[q(3)], &[vec![]], 0).unwrap();
        assert_eq!(raw.coefficients, Vec::<BigRational>::new());
        assert_eq!(raw.residual, vec![q(-2)]);
        assert_eq!(raw.dual, vec![q(-3)]);
        assert_eq!(raw.value, q(6));
        assert_eq!(raw.dual[0].clone() * q(-2), raw.value);
        assert_eq!(raw.iterations, 0);
        let empty = solve_weighted_l1_projection(&[], &[], &[], 0).unwrap();
        assert!(
            empty.coefficients.is_empty() && empty.residual.is_empty() && empty.dual.is_empty()
        );
        assert_eq!(empty.value, q(0));
        assert_eq!(empty.iterations, 0);

        for numerator in [0, 1] {
            assert_eq!(
                solve_weighted_l1_projection(&[bad(numerator)], &[q(1)], &[vec![q(1)]], 0),
                Err(L1LpError::InvalidRational)
            );
            assert_eq!(
                solve_weighted_l1_projection(&[q(1)], &[bad(numerator)], &[vec![q(1)]], 0),
                Err(L1LpError::InvalidRational)
            );
            assert_eq!(
                solve_weighted_l1_projection(&[q(1)], &[q(1)], &[vec![bad(numerator)]], 0),
                Err(L1LpError::InvalidRational)
            );
        }
        assert_eq!(
            solve_weighted_l1_projection(&[q(1)], &[q(-1)], &[vec![q(1)]], 1),
            Err(L1LpError::NonPositiveWeight(0))
        );
        assert_eq!(
            solve_weighted_l1_projection(&[q(1), q(2)], &[q(1)], &[vec![q(1)]], 1),
            Err(L1LpError::DimensionMismatch { target: 2, rows: 1 })
        );
        assert_eq!(
            solve_weighted_l1_projection(&[q(1), q(2)], &[q(1), q(1)], &[vec![q(1)]], 1),
            Err(L1LpError::DimensionMismatch { target: 2, rows: 1 })
        );
        assert_eq!(
            solve_weighted_l1_projection(
                &[q(1), q(2)],
                &[q(1), q(1)],
                &[vec![q(1)], vec![q(1), q(2)]],
                1
            ),
            Err(L1LpError::RaggedMap {
                row: 1,
                expected: 1,
                actual: 2
            })
        );
    }

    #[test]
    fn public_sparse_pairing_refuses_malformed_carriers_and_replays_the_exact_dot_product() {
        // (2,0,-3) dot (4,9,5) = 8-15 = -7.
        let column = SparseColumn {
            indices: vec![0, 2],
            values: vec![q(2), q(-3)],
        };
        assert_eq!(column.dot_dense(&[q(4), q(9), q(5)]), Ok(q(-7)));
        assert_eq!(SparseColumn::new().dot_dense(&[]), Ok(q(0)));
        assert_eq!(
            SparseColumn {
                indices: vec![0, 1],
                values: vec![q(1)]
            }
            .dot_dense(&[q(1), q(1)]),
            Err(L1LpError::SparseColumnShape {
                indices: 2,
                values: 1
            })
        );
        assert_eq!(
            SparseColumn {
                indices: vec![0],
                values: vec![q(1), q(2)]
            }
            .dot_dense(&[q(1)]),
            Err(L1LpError::SparseColumnShape {
                indices: 1,
                values: 2
            })
        );
        for (index, dimension) in [(1, 1), (usize::MAX, 1), (0, 0)] {
            let dense = vec![q(1); dimension];
            assert_eq!(
                SparseColumn::singleton(index, q(1)).dot_dense(&dense),
                Err(L1LpError::SparseIndexOutOfBounds {
                    position: 0,
                    index,
                    dimension
                })
            );
        }
        for numerator in [0, 1] {
            assert_eq!(
                SparseColumn::singleton(0, bad(numerator)).dot_dense(&[q(1)]),
                Err(L1LpError::InvalidRational)
            );
            assert_eq!(
                SparseColumn::singleton(0, q(1)).dot_dense(&[bad(numerator)]),
                Err(L1LpError::InvalidRational)
            );
            // Unused coordinates still belong to the admitted dense carrier.
            assert_eq!(
                SparseColumn::singleton(0, q(1)).dot_dense(&[q(1), bad(numerator)]),
                Err(L1LpError::InvalidRational)
            );
        }
    }

    #[test]
    fn nalgebra_projection_preserves_empty_width_and_refuses_overflow_before_cloning() {
        use core_kernel::resource_limits::{OperationLimits, ResourceError};

        let empty = nalgebra::DVector::<BigRational>::from_vec(vec![]);
        for width in [0, 3] {
            let matrix = nalgebra::DMatrix::<BigRational>::from_vec(0, width, vec![]);
            let solution = solve_weighted_l1_projection_nalgebra(&matrix, &empty, &empty).unwrap();
            assert_eq!(solution.coefficients, vec![q(0); width]);
            assert!(solution.residual.is_empty() && solution.dual.is_empty());
            assert_eq!(solution.value, q(0));
            assert_eq!(solution.iterations, 0);
        }
        // 0*MAX is a valid allocation-free nalgebra carrier; its default
        // simplex budget cannot fit and must refuse before cloning/allocation.
        let extreme = nalgebra::DMatrix::<BigRational>::from_vec(0, usize::MAX, vec![]);
        assert_eq!(
            solve_weighted_l1_projection_nalgebra(&extreme, &empty, &empty),
            Err(L1LpError::Resource(ResourceError::CountOverflow))
        );
        // This width has a representable budget but exceeds the declared
        // coefficient-vector layout ceiling, still requiring no matrix entries.
        let limit =
            OperationLimits::default().max_memory_bytes / std::mem::size_of::<BigRational>();
        let too_wide = nalgebra::DMatrix::<BigRational>::from_vec(0, limit + 1, vec![]);
        assert!(matches!(
            solve_weighted_l1_projection_nalgebra(&too_wide, &empty, &empty),
            Err(L1LpError::Resource(ResourceError::AllocationFailure { requested, .. }))
                if requested == limit + 1
        ));
        let row_mismatch = nalgebra::DMatrix::<BigRational>::from_vec(0, 3, vec![]);
        let one = nalgebra::DVector::from_vec(vec![q(1)]);
        assert_eq!(
            solve_weighted_l1_projection_nalgebra(&row_mismatch, &one, &empty),
            Err(L1LpError::DimensionMismatch { target: 1, rows: 0 })
        );
        assert_eq!(
            solve_weighted_l1_projection_nalgebra(&row_mismatch, &empty, &one),
            Err(L1LpError::DimensionMismatch { target: 0, rows: 1 })
        );
        // Ordinary map control: 3-1*gamma vanishes exactly at gamma=3.
        let matrix = nalgebra::DMatrix::from_vec(1, 1, vec![q(1)]);
        let target = nalgebra::DVector::from_vec(vec![q(3)]);
        let weights = nalgebra::DVector::from_vec(vec![q(2)]);
        let solution = solve_weighted_l1_projection_nalgebra(&matrix, &target, &weights).unwrap();
        assert_eq!(solution.coefficients, vec![q(3)]);
        assert_eq!(solution.residual, vec![q(0)]);
        assert_eq!(solution.dual, vec![q(0)]);
        assert_eq!(solution.value, q(0));
        assert_eq!(solution.iterations, 1);
    }
}

#[cfg(test)]
mod pfi_replay_tests {
    use super::*;
    use linear_algebra::exact_field::{
        elimination::{solve, LinearSolution},
        matrix,
    };
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }
    fn independent(
        a: &linear_algebra::backend::basic_matrix::BasicMatrix<BigRational>,
        b: &[BigRational],
    ) -> Vec<BigRational> {
        match solve(a, b).unwrap() {
            LinearSolution::Consistent {
                particular,
                kernel_basis,
            } => {
                assert!(kernel_basis.is_empty());
                particular
            }
            _ => panic!("invertible shear sequence"),
        }
    }
    #[test]
    fn ftran_btran_match_independent_rref_through_two_refactorizations() {
        let mut columns = vec![
            vec![q(-1), q(0), q(0)],
            vec![q(0), q(1), q(0)],
            vec![q(0), q(0), q(-1)],
        ];
        let mut fac = BasisFactorization::new_from_signs(&[false, true, false]);
        for step in 0..85 {
            let p = step % 3;
            let other = (p + 1) % 3;
            let col: Vec<_> = (0..3)
                .map(|i| {
                    &columns[p][i] + &columns[other][i] * q(if step % 2 == 0 { 1 } else { -1 })
                })
                .collect();
            let sparse = SparseColumn {
                indices: vec![0, 1, 2],
                values: col.clone(),
            };
            let d = fac.ftran(&sparse);
            fac.add_eta(p, &d);
            columns[p] = col;
            if (step + 1) % 40 == 0 {
                fac.refactorize(&[0, 1, 2], &|i| SparseColumn {
                    indices: vec![0, 1, 2],
                    values: columns[i].clone(),
                })
                .unwrap();
                assert!(fac.etas.is_empty());
            }
            let a = matrix::from_fn(3, 3, |r, c| columns[c][r].clone()).unwrap();
            let rhs = vec![q(2), q(-3), q(5)];
            assert_eq!(
                fac.ftran(&SparseColumn {
                    indices: vec![0, 1, 2],
                    values: rhs.clone()
                }),
                independent(&a, &rhs),
                "FTRAN step {step}"
            );
            assert_eq!(
                fac.btran(&rhs),
                independent(&matrix::transpose(&a).unwrap(), &rhs),
                "BTRAN step {step}"
            );
        }
    }
}
