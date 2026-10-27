// AuthorityEffect: None.

//! Searches for a rational complement of `R = im d0` whose residual projection
//! has weighted-`l1` distortion at most a declared rational `tau`.
//!
//! The splitting is parameterized as in `core_functional::residual_splitting`:
//! `B` is the pivot-column basis of `d0`, `N` adds unit vectors until
//! `S = [B N]` is invertible, and `L_H = (N - B H) Q`, linear in `H`. The
//! condition `||L_H||_{1,w} <= tau` is the finite linear system (LP4) in the
//! unknowns `H` and `t`:
//!
//! `t_ij >= (L_H)_ij`, `t_ij >= -(L_H)_ij`, `sum_i w_i t_ij <= tau w_j`.
//!
//! [`decide_distortion_at_most`] answers it with the exact feasibility module:
//! a feasible point gives `H` and a replayed splitting certificate; an
//! infeasible system gives Farkas multipliers that the caller can replay with
//! [`LinearInequalitySystem::verify_farkas`]. `tau = 1` is the
//! contractive-complement question.

use crate::solver_convex_farkas_feasibility::{
    FeasibilityError, FeasibilityVerdict, LinearInequalitySystem,
};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::elimination;
use linear_algebra::exact_field::ExactFieldError;
use num_rational::BigRational as Q;
use num_traits::{One, Signed, Zero};
use core_functional::residual_splitting::{
    multiply, splitting_from_parameter, ResidualSplittingCertificate, ResidualSplittingError,
    RowMatrix,
};
use thiserror::Error;

/// Refusals of the complement search.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ContractiveComplementError {
    #[error("d0 has {actual} rows for {expected} weights")]
    RowCount { expected: usize, actual: usize },
    #[error("d0 row {row} has {actual} entries, expected {expected}")]
    Ragged {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("the distortion bound {tau} is negative")]
    NegativeBound { tau: String },
    #[error(transparent)]
    Splitting(#[from] ResidualSplittingError),
    #[error(transparent)]
    Feasibility(#[from] FeasibilityError),
    #[error(transparent)]
    LinearAlgebra(#[from] ExactFieldError),
    #[error(transparent)]
    Storage(#[from] MatrixError),
    #[error("the completed basis is not invertible")]
    CompletionFailed,
    #[error("the proposed splitting exceeds the bound after replay")]
    BoundNotMet,
}

/// The fixed parameterization data for one `d0`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SplittingFrame {
    pub d0: RowMatrix,
    pub repair_columns: usize,
    pub basis: RowMatrix,
    pub complement: RowMatrix,
    pub inverse: RowMatrix,
    pub image_coordinates: RowMatrix,
    pub selection: RowMatrix,
}

/// The answer to `exists H : ||L_H||_{1,w} <= tau`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DistortionVerdict {
    /// A replayed splitting and its exact distortion.
    Attained {
        certificate: ResidualSplittingCertificate,
        distortion: Q,
    },
    /// No parameter meets the bound; `multipliers` certify the system infeasible.
    Unattainable {
        system: LinearInequalitySystem,
        multipliers: Vec<Q>,
    },
}

fn to_matrix(rows: &[Vec<Q>], cols: usize) -> Result<BasicMatrix<Q>, MatrixError> {
    BasicMatrix::from_row_major(rows.len(), cols, rows.iter().flatten().cloned().collect())
}

fn from_matrix(m: &BasicMatrix<Q>) -> Result<RowMatrix, MatrixError> {
    let (rows, cols) = m.shape();
    (0..rows)
        .map(|i| (0..cols).map(|j| m.get(i, j)).collect())
        .collect()
}

impl SplittingFrame {
    fn validate_d0_dimensions(
        d0: &RowMatrix,
        m: usize,
        k: usize,
    ) -> Result<(), ContractiveComplementError> {
        if d0.len() != m {
            return Err(ContractiveComplementError::RowCount {
                expected: m,
                actual: d0.len(),
            });
        }
        if let Some((row, r)) = d0.iter().enumerate().find(|(_, r)| r.len() != k) {
            return Err(ContractiveComplementError::Ragged {
                row,
                expected: k,
                actual: r.len(),
            });
        }
        Ok(())
    }

    fn complete_columns_to_basis(
        mut columns: Vec<Vec<Q>>,
        m: usize,
    ) -> Result<RowMatrix, ContractiveComplementError> {
        for i in 0..m {
            if columns.len() == m {
                break;
            }
            let unit: Vec<Q> = (0..m)
                .map(|j| if i == j { Q::one() } else { Q::zero() })
                .collect();
            let mut trial = columns.clone();
            trial.push(unit);
            let rows: RowMatrix = (0..m)
                .map(|row| trial.iter().map(|c| c[row].clone()).collect())
                .collect();
            if elimination::rank(&to_matrix(&rows, trial.len())?)? == trial.len() {
                columns = trial;
            }
        }
        if columns.len() != m {
            return Err(ContractiveComplementError::CompletionFailed);
        }
        Ok((0..m)
            .map(|row| columns.iter().map(|c| c[row].clone()).collect())
            .collect())
    }

    fn build_pivot_selection(k: usize, pivots: &[usize]) -> RowMatrix {
        let r = pivots.len();
        (0..k)
            .map(|i| {
                (0..r)
                    .map(|j| if pivots[j] == i { Q::one() } else { Q::zero() })
                    .collect()
            })
            .collect()
    }

    /// Builds `B`, `E`, `F`, `N` and `S^{-1}` for `d0` (`m x k`, row-wise).
    pub fn try_new(d0: RowMatrix, m: usize, k: usize) -> Result<Self, ContractiveComplementError> {
        Self::validate_d0_dimensions(&d0, m, k)?;
        let reduced = elimination::rref(&to_matrix(&d0, k)?)?;
        let pivots = reduced.pivot_columns().to_vec();
        let r = pivots.len();
        let rref = from_matrix(reduced.matrix())?;
        let image_coordinates: RowMatrix = rref.into_iter().take(r).collect();
        let selection = Self::build_pivot_selection(k, &pivots);
        let pivot_cols: Vec<Vec<Q>> = pivots
            .iter()
            .map(|&p| d0.iter().map(|row| row[p].clone()).collect())
            .collect();
        let s_rows = Self::complete_columns_to_basis(pivot_cols, m)?;
        let inverse = if m == 0 {
            Vec::new()
        } else {
            from_matrix(&elimination::inverse(&to_matrix(&s_rows, m)?)?)?
        };
        let basis: RowMatrix = (0..m).map(|row| s_rows[row][..r].to_vec()).collect();
        let complement: RowMatrix = (0..m).map(|row| s_rows[row][r..].to_vec()).collect();
        Ok(Self {
            d0,
            repair_columns: k,
            basis,
            complement,
            inverse,
            image_coordinates,
            selection,
        })
    }

    pub fn rank(&self) -> usize {
        self.image_coordinates.len()
    }

    /// The full certificate for parameter `h`, before replay.
    pub fn certificate(
        &self,
        h: RowMatrix,
    ) -> Result<ResidualSplittingCertificate, ContractiveComplementError> {
        let (projection, residual) =
            splitting_from_parameter(&self.basis, &self.complement, &self.inverse, &h)?;
        Ok(ResidualSplittingCertificate {
            d0: self.d0.clone(),
            repair_columns: self.repair_columns,
            basis: self.basis.clone(),
            complement: self.complement.clone(),
            inverse: self.inverse.clone(),
            parameter: h,
            projection,
            residual,
            image_coordinates: self.image_coordinates.clone(),
            selection: self.selection.clone(),
        })
    }

    fn push_cell_abs_bounds(
        &self,
        system: &mut LinearInequalitySystem,
        q_rows: &[Vec<Q>],
        nq: &RowMatrix,
        i: usize,
        j: usize,
        unknowns: usize,
    ) -> Result<(), ContractiveComplementError> {
        let m = self.d0.len();
        let r = self.rank();
        let s = m - r;
        let mut coeff = vec![Q::zero(); unknowns];
        for a in 0..r {
            for b in 0..s {
                coeff[a * s + b] = -(&self.basis[i][a] * &q_rows[b][j]);
            }
        }
        let t = r * s + i * m + j;
        let mut upper = coeff.clone();
        upper[t] = -Q::one();
        system.push_le(upper, -nq[i][j].clone())?;
        let mut lower: Vec<Q> = coeff.iter().map(|c| -c).collect();
        lower[t] = -Q::one();
        system.push_le(lower, nq[i][j].clone())?;
        Ok(())
    }

    /// LP4 for the bound `tau`; unknowns are `H` (row-major) then `t` (row-major).
    pub fn distortion_system(
        &self,
        weights: &[Q],
        tau: &Q,
    ) -> Result<LinearInequalitySystem, ContractiveComplementError> {
        let m = self.d0.len();
        let r = self.rank();
        let s = m - r;
        let q_rows = &self.inverse[r..];
        let nq = if s == 0 {
            vec![vec![Q::zero(); m]; m]
        } else {
            multiply(&self.complement, q_rows, m)
        };
        let unknowns = r * s + m * m;
        let mut system = LinearInequalitySystem::empty(unknowns);
        for i in 0..m {
            for j in 0..m {
                self.push_cell_abs_bounds(&mut system, q_rows, &nq, i, j, unknowns)?;
            }
        }
        for j in 0..m {
            let mut row = vec![Q::zero(); unknowns];
            for (i, w) in weights.iter().enumerate() {
                row[r * s + i * m + j] = w.clone();
            }
            system.push_le(row, tau * &weights[j])?;
        }
        Ok(system)
    }
}

fn build_attained_verdict(
    frame: &SplittingFrame,
    weights: &[Q],
    tau: &Q,
    point: &[Q],
) -> Result<DistortionVerdict, ContractiveComplementError> {
    let (r, s) = (frame.rank(), weights.len() - frame.rank());
    let h: RowMatrix = (0..r)
        .map(|a| (0..s).map(|b| point[a * s + b].clone()).collect())
        .collect();
    let certificate = frame.certificate(h)?;
    let distortion = certificate.verify(weights)?;
    if &distortion > tau {
        return Err(ContractiveComplementError::BoundNotMet);
    }
    Ok(DistortionVerdict::Attained {
        certificate,
        distortion,
    })
}

/// Decides whether some complement of `im d0` has distortion at most `tau`.
pub fn decide_distortion_at_most(
    d0: RowMatrix,
    repair_columns: usize,
    weights: &[Q],
    tau: &Q,
    max_pivots: usize,
) -> Result<DistortionVerdict, ContractiveComplementError> {
    if tau.is_negative() {
        return Err(ContractiveComplementError::NegativeBound {
            tau: tau.to_string(),
        });
    }
    let frame = SplittingFrame::try_new(d0, weights.len(), repair_columns)?;
    // Weight validity is replayed by the certificate check; check it first so a
    // bad weight is refused before the search.
    core_functional::residual_splitting::weighted_l1_operator_norm(
        &vec![vec![Q::zero(); weights.len()]; weights.len()],
        weights,
    )?;
    let system = frame.distortion_system(weights, tau)?;
    match system.decide(max_pivots)? {
        FeasibilityVerdict::Feasible { point } => {
            build_attained_verdict(&frame, weights, tau, &point)
        }
        FeasibilityVerdict::Infeasible { multipliers } => {
            system.verify_farkas(&multipliers).map_err(|_| {
                ContractiveComplementError::Feasibility(FeasibilityError::CertificateMismatch)
            })?;
            Ok(DistortionVerdict::Unattainable {
                system,
                multipliers,
            })
        }
    }
}

/// `tau = 1`: is there a contractive complement?
pub fn decide_contractive_complement(
    d0: RowMatrix,
    repair_columns: usize,
    weights: &[Q],
    max_pivots: usize,
) -> Result<DistortionVerdict, ContractiveComplementError> {
    decide_distortion_at_most(d0, repair_columns, weights, &Q::one(), max_pivots)
}

// Origin: engine/crates_rs/core_solvers/src/solver_cohomology_splitting.rs
// Claim: urn:core:crates_rs:core-solvers:solver-cohomology-splitting:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::solver_lp_exact_simplex::solve_weighted_l1_projection;
    use num_bigint::BigInt;

    fn q(n: i64, d: i64) -> Q {
        Q::new(BigInt::from(n), BigInt::from(d))
    }
    fn z(n: i64) -> Q {
        q(n, 1)
    }
    fn ones(m: usize) -> Vec<Q> {
        vec![z(1); m]
    }
    fn diagonal(m: usize) -> RowMatrix {
        vec![vec![z(1)]; m]
    }

    #[test]
    fn diagonal_line_in_three_dimensions_needs_four_thirds() {
        let w = ones(3);
        match decide_contractive_complement(diagonal(3), 1, &w, 4000).unwrap() {
            DistortionVerdict::Unattainable {
                system,
                multipliers,
            } => assert!(system.verify_farkas(&multipliers).is_ok()),
            other => panic!("expected no contractive complement, got {other:?}"),
        }
        match decide_distortion_at_most(diagonal(3), 1, &w, &q(4, 3), 4000).unwrap() {
            DistortionVerdict::Attained { distortion, .. } => assert_eq!(distortion, q(4, 3)),
            other => panic!("expected 4/3 to be attained, got {other:?}"),
        }
        assert!(matches!(
            decide_distortion_at_most(diagonal(3), 1, &w, &q(1333, 1000), 4000).unwrap(),
            DistortionVerdict::Unattainable { .. }
        ));
    }

    #[test]
    fn report_thirteen_row_certificate_replays() {
        // Unknowns a_0..a_2 then t_ij (i row, j column). Per column j:
        // -a_j - t_jj <= -1; a_j - t_ij <= 0 (i != j); sum_i t_ij <= 1.
        // Image row: -(a_0 + a_1 + a_2) <= -1. All multipliers 1.
        let n = 3 + 9;
        let t = |i: usize, j: usize| 3 + 3 * i + j;
        let mut sys = LinearInequalitySystem::empty(n);
        for j in 0..3 {
            let mut row = vec![z(0); n];
            row[j] = z(-1);
            row[t(j, j)] = z(-1);
            sys.push_le(row, z(-1)).unwrap();
            for i in (0..3).filter(|i| *i != j) {
                let mut row = vec![z(0); n];
                row[j] = z(1);
                row[t(i, j)] = z(-1);
                sys.push_le(row, z(0)).unwrap();
            }
            let mut row = vec![z(0); n];
            for i in 0..3 {
                row[t(i, j)] = z(1);
            }
            sys.push_le(row, z(1)).unwrap();
        }
        let mut row = vec![z(0); n];
        for j in 0..3 {
            row[j] = z(-1);
        }
        sys.push_le(row, z(-1)).unwrap();
        assert_eq!(sys.rows().len(), 13);
        assert!(sys.verify_farkas(&vec![z(1); 13]).is_ok());
        let mut tampered = vec![z(1); 13];
        tampered[12] = z(0);
        assert!(sys.verify_farkas(&tampered).is_err());
    }

    #[test]
    fn sharp_vector_attains_the_distortion() {
        let w = ones(3);
        let DistortionVerdict::Attained { certificate, .. } =
            decide_distortion_at_most(diagonal(3), 1, &w, &q(4, 3), 4000).unwrap()
        else {
            panic!("expected attainment");
        };
        // x = e1: Phi1 = 1, and the distortion bound is attained.
        let x = vec![z(1), z(0), z(0)];
        let phi = solve_weighted_l1_projection(&x, &w, &diagonal(3), 1024)
            .unwrap()
            .value;
        assert_eq!(phi, z(1));
        let lx: Vec<Q> = certificate
            .residual
            .iter()
            .map(|row| row.iter().zip(&x).map(|(a, b)| a * b).sum())
            .collect();
        let norm: Q = lx.iter().map(|v| v.abs()).sum();
        assert!(phi <= norm && norm <= q(4, 3) * &phi);
    }

    #[test]
    fn plane_line_has_a_contractive_complement() {
        let w = ones(2);
        let DistortionVerdict::Attained {
            certificate,
            distortion,
        } = decide_contractive_complement(diagonal(2), 1, &w, 2000).unwrap()
        else {
            panic!("expected a contractive complement");
        };
        assert!(distortion <= z(1));
        let x = vec![z(3), z(1)];
        let phi = solve_weighted_l1_projection(&x, &w, &diagonal(2), 1024)
            .unwrap()
            .value;
        assert_eq!(phi, z(2));
        let lx: Vec<Q> = certificate
            .residual
            .iter()
            .map(|row| row.iter().zip(&x).map(|(a, b)| a * b).sum())
            .collect();
        assert_eq!(lx.iter().map(|v| v.abs()).sum::<Q>(), phi);
    }

    #[test]
    fn boundary_images() {
        // Full image: L = 0, any tau >= 0 is attained (zero quotient, norm zero).
        let id = vec![vec![z(1), z(0)], vec![z(0), z(1)]];
        match decide_distortion_at_most(id, 2, &ones(2), &z(0), 100).unwrap() {
            DistortionVerdict::Attained { distortion, .. } => assert_eq!(distortion, z(0)),
            other => panic!("{other:?}"),
        }
        // Zero image: L = I, distortion exactly 1.
        let zero = vec![vec![z(0)], vec![z(0)]];
        assert!(matches!(
            decide_contractive_complement(zero.clone(), 1, &ones(2), 100).unwrap(),
            DistortionVerdict::Attained { .. }
        ));
        assert!(matches!(
            decide_distortion_at_most(zero, 1, &ones(2), &q(1, 2), 100).unwrap(),
            DistortionVerdict::Unattainable { .. }
        ));
        // Empty carrier.
        assert!(matches!(
            decide_contractive_complement(vec![], 0, &[], 10).unwrap(),
            DistortionVerdict::Attained { .. }
        ));
    }

    #[test]
    fn refusals_are_typed() {
        assert!(matches!(
            decide_distortion_at_most(diagonal(2), 1, &ones(2), &z(-1), 10),
            Err(ContractiveComplementError::NegativeBound { .. })
        ));
        assert!(matches!(
            decide_contractive_complement(diagonal(2), 1, &ones(3), 10),
            Err(ContractiveComplementError::RowCount { .. })
        ));
        assert!(matches!(
            decide_contractive_complement(diagonal(2), 1, &[z(1), z(0)], 10),
            Err(ContractiveComplementError::Splitting(_))
        ));
        assert!(matches!(
            decide_contractive_complement(diagonal(3), 1, &ones(3), 0),
            Err(ContractiveComplementError::Feasibility(
                FeasibilityError::BudgetExhausted
            ))
        ));
    }
}
