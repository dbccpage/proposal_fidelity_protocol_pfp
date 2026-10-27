//! # Phi3: Exact Degree-3 Quotient-Distance and 3-Cavity / Bianchi Obstruction Certificates
//!
//! Higher-degree finite obstruction calculus in the 3-dimensional chain/cochain complex:
//!
//! ```text
//! C³  <───d₂───  C²  <───d₁───  C¹  <───d₀───  C⁰       (cochains)
//! C₃  ───∂₃───>  C₂  ───∂₂───>  C₁  ───∂₁───>  C₀       (chains, ∂ₖ = dₖ₋₁ᵀ)
//! ```
//!
//! With the dual nilpotence laws:
//! - 1-skeleton nilpotence: `d₁ ∘ d₀ = 0` (or `∂₁ ∘ ∂₂ = 0`)
//! - Bianchi identity nilpotence: `d₂ ∘ d₁ = 0` (or `∂₂ ∘ ∂₃ = 0`)
//!
//! ## Mathematical Definitions
//!
//! 1. **Bianchi Identity & Degree-2 Closure Defect Γ₃**:
//!    For a 2-cochain field strength `B ∈ C²(K; ℚ)`, its Bianchi defect is:
//!    ```text
//!    Γ₃(B) = ‖d₂ B‖_{1, ν} = ∑_{c₃ ∈ C₃} ν_{c₃} |(d₂ B)_{c₃}|
//!    ```
//!    If `B = d₁ A`, then `d₂ B = (d₂ ∘ d₁) A = 0`, satisfying the Bianchi identity.
//!
//! 2. **Degree-3 Quotient Obstruction Φ₃**:
//!    For a target 3-cochain flux `H ∈ C³(K; ℚ)` on a complex with 3-cavities (`b₃ ≥ 1`):
//!    ```text
//!    Φ₃([H]) = min_{B ∈ C²(K; ℚ)} ‖H - d₂ B‖_{1, ν}
//!    ```
//!    By exact linear programming weak duality over `ℚ`:
//!    ```text
//!    Φ₃([H]) ≥ max_{u ∈ C₃(K; ℚ)} ⟨H, u⟩
//!    subject to:
//!      d₂ᵀ u = 0       (u ∈ Z₃(K; ℚ), closed 3-cycle / cavity)
//!      |u_{c₃}| ≤ ν_{c₃}   ∀ c₃ ∈ C₃
//!    ```
//!
//! When primal and dual values match exactly, weak duality establishes optimality
//! with zero duality gap in `ℚ`.

use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};
use std::str::FromStr;

/// Wire shape for string-encoded rational degree-3 certificate payloads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExactPhi3CertificateWire {
    pub flux_h: Vec<String>,
    pub d2: Vec<Vec<String>>,
    pub d1: Option<Vec<Vec<String>>>,
    pub d0: Option<Vec<Vec<String>>>,
    pub weights: Vec<String>,
    pub potential_b: Vec<String>,
    pub primal_residual: Vec<String>,
    pub dual_witness: Vec<String>,
    pub reported_value: String,
}

impl TryFrom<ExactPhi3CertificateWire> for ExactPhi3Certificate {
    type Error = ExactPhi3CertificateError;

    fn try_from(wire: ExactPhi3CertificateWire) -> Result<Self, Self::Error> {
        fn parse_vec(v: &[String]) -> Result<Vec<BigRational>, ExactPhi3CertificateError> {
            crate::wire::parse_rational_vec(v, ExactPhi3CertificateError::InvalidRationalString)
        }
        fn parse_matrix(
            m: &[Vec<String>],
        ) -> Result<Vec<Vec<BigRational>>, ExactPhi3CertificateError> {
            crate::wire::parse_rational_matrix(m, ExactPhi3CertificateError::InvalidRationalString)
        }
        fn parse_opt_matrix(
            m: &Option<Vec<Vec<String>>>,
        ) -> Result<Option<Vec<Vec<BigRational>>>, ExactPhi3CertificateError> {
            m.as_ref().map(|mat| parse_matrix(mat)).transpose()
        }

        let (flux_h, d2, d1, d0) = (
            parse_vec(&wire.flux_h)?,
            parse_matrix(&wire.d2)?,
            parse_opt_matrix(&wire.d1)?,
            parse_opt_matrix(&wire.d0)?,
        );
        let (weights, potential_b, primal_residual, dual_witness, reported_value) =
            Self::parse_wire_vectors(&wire, parse_vec)?;

        Ok(ExactPhi3Certificate {
            flux_h,
            d2,
            d1,
            d0,
            weights,
            potential_b,
            primal_residual,
            dual_witness,
            reported_value,
        })
    }
}

impl ExactPhi3Certificate {
    #[allow(clippy::type_complexity)]
    fn parse_wire_vectors(
        wire: &ExactPhi3CertificateWire,
        parse_vec: fn(&[String]) -> Result<Vec<BigRational>, ExactPhi3CertificateError>,
    ) -> Result<
        (
            Vec<BigRational>,
            Vec<BigRational>,
            Vec<BigRational>,
            Vec<BigRational>,
            BigRational,
        ),
        ExactPhi3CertificateError,
    > {
        let weights = parse_vec(&wire.weights)?;
        let potential_b = parse_vec(&wire.potential_b)?;
        let primal_residual = parse_vec(&wire.primal_residual)?;
        let dual_witness = parse_vec(&wire.dual_witness)?;
        let reported_value = BigRational::from_str(&wire.reported_value).map_err(|_| {
            ExactPhi3CertificateError::InvalidRationalString(wire.reported_value.clone())
        })?;
        Ok((
            weights,
            potential_b,
            primal_residual,
            dual_witness,
            reported_value,
        ))
    }
}

/// Submitted exact finite rational witness for degree-3 quotient obstruction Φ₃([H]).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "ExactPhi3CertificateWire")]
pub struct ExactPhi3Certificate {
    /// Target 3-cochain flux H ∈ C³ (length |C₃|)
    pub flux_h: Vec<BigRational>,
    /// Coboundary matrix d₂: C² → C³ (|C₃| rows, |C₂| cols)
    pub d2: Vec<Vec<BigRational>>,
    /// Optional coboundary matrix d₁: C¹ → C² (|C₂| rows, |C₁| cols) for Bianchi nilpotence d₂ d₁ = 0
    pub d1: Option<Vec<Vec<BigRational>>>,
    /// Optional coboundary matrix d₀: C⁰ → C¹ (|C₁| rows, |C₀| cols) for 1-skeleton nilpotence d₁ d₀ = 0
    pub d0: Option<Vec<Vec<BigRational>>>,
    /// Strictly positive 3-cell volume weights ν_{c₃} (length |C₃|)
    pub weights: Vec<BigRational>,
    /// Gauge 2-cochain potential B ∈ C² (length |C₂|)
    pub potential_b: Vec<BigRational>,
    /// Primal residual r = H - d₂ B (length |C₃|)
    pub primal_residual: Vec<BigRational>,
    /// Dual 3-cycle witness u ∈ Z₃(K; ℚ) satisfying d₂ᵀ u = 0 (length |C₃|)
    pub dual_witness: Vec<BigRational>,
    /// Certified optimal obstruction value in ℚ
    pub reported_value: BigRational,
}

/// Sealed result of replaying an [`ExactPhi3Certificate`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedExactPhi3 {
    certificate: ExactPhi3Certificate,
}

impl VerifiedExactPhi3 {
    pub fn certificate(&self) -> &ExactPhi3Certificate {
        &self.certificate
    }

    pub fn value(&self) -> &BigRational {
        &self.certificate.reported_value
    }

    pub fn primal_residual(&self) -> &[BigRational] {
        &self.certificate.primal_residual
    }

    pub fn potential_b(&self) -> &[BigRational] {
        &self.certificate.potential_b
    }

    pub fn dual_witness(&self) -> &[BigRational] {
        &self.certificate.dual_witness
    }
}

#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum ExactPhi3CertificateError {
    #[error("invalid rational string: '{0}'")]
    InvalidRationalString(String),
    #[error("exact Phi3 input contains a rational with zero denominator")]
    ZeroRationalDenominator,
    #[error("flux_h, primal_residual, dual_witness, and weights must have length equal to 3-cell count {expected}, but found lengths {actual:?}")]
    Cell3DimensionMismatch { expected: usize, actual: Vec<usize> },
    #[error("d2 matrix has {actual} rows but expected {expected} (|C₃|)")]
    D2RowMismatch { expected: usize, actual: usize },
    #[error("d2 row {row} has {actual} columns but expected {expected} (|C₂|)")]
    D2ColumnMismatch {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("d1 matrix dimension mismatch: rows={rows} (expected {expected_c2}), cols={cols}")]
    D1DimensionMismatch {
        rows: usize,
        expected_c2: usize,
        cols: usize,
    },
    #[error("d0 matrix dimension mismatch: rows={rows} (expected {expected_c1}), cols={cols}")]
    D0DimensionMismatch {
        rows: usize,
        expected_c1: usize,
        cols: usize,
    },
    #[error("d0 requires d1 so the 1-skeleton chain law can be checked")]
    MissingD1ForD0,
    #[error("Bianchi identity nilpotence law violated: (d2 * d1)[{row}][{col}] = {val} != 0")]
    BianchiNilpotenceViolation {
        row: usize,
        col: usize,
        val: BigRational,
    },
    #[error("1-skeleton cochain nilpotence law violated: (d1 * d0)[{row}][{col}] = {val} != 0")]
    CochainNilpotenceViolation {
        row: usize,
        col: usize,
        val: BigRational,
    },
    #[error("weight at 3-cell index {index} is non-positive")]
    NonPositiveWeight { index: usize },
    #[error("primal residual mismatch at 3-cell {index}: expected {expected}, got {actual}")]
    PrimalResidualMismatch {
        index: usize,
        expected: BigRational,
        actual: BigRational,
    },
    #[error(
        "dual witness is not a closed 3-cycle: (d2^T * u) on 2-cell {cell2} = {residual} != 0"
    )]
    DualNotClosed3Cycle { cell2: usize, residual: BigRational },
    #[error("dual witness violates norm bound |u_{cell3}| = {val} > nu_{cell3} = {bound}")]
    DualNormBoundViolation {
        cell3: usize,
        val: BigRational,
        bound: BigRational,
    },
    #[error("reported Phi3 value is negative")]
    NegativeReportedValue,
    #[error("reported Phi3 value does not match weighted primal residual norm")]
    PrimalValueMismatch,
    #[error("reported Phi3 value does not match dual pairing <H, u>")]
    DualValueMismatch,
}

pub struct Phi3Functional;

impl Phi3Functional {
    fn check_denominators(
        certificate: &ExactPhi3Certificate,
    ) -> Result<(), ExactPhi3CertificateError> {
        // 1. Zero denominator checks
        let mut all_vals = certificate
            .flux_h
            .iter()
            .chain(certificate.weights.iter())
            .chain(certificate.potential_b.iter())
            .chain(certificate.primal_residual.iter())
            .chain(certificate.dual_witness.iter())
            .chain(certificate.d2.iter().flatten())
            .chain(std::iter::once(&certificate.reported_value));

        if all_vals.any(|v| v.denom().is_zero()) {
            return Err(ExactPhi3CertificateError::ZeroRationalDenominator);
        }

        for mat in [&certificate.d1, &certificate.d0].into_iter().flatten() {
            if mat.iter().flatten().any(|v| v.denom().is_zero()) {
                return Err(ExactPhi3CertificateError::ZeroRationalDenominator);
            }
        }
        // `d0` is stored on the sealed certificate. Without `d1` its shape and
        // the chain law are never checked, so an orphan `d0` must not verify.
        if certificate.d0.is_some() && certificate.d1.is_none() {
            return Err(ExactPhi3CertificateError::MissingD1ForD0);
        }
        Ok(())
    }

    fn check_dimensions(
        certificate: &ExactPhi3Certificate,
        c3_count: usize,
        c2_count: usize,
    ) -> Result<(), ExactPhi3CertificateError> {
        // 2. Dimension validations
        let lengths_match = certificate.primal_residual.len() == c3_count
            && certificate.dual_witness.len() == c3_count
            && certificate.weights.len() == c3_count;
        if !lengths_match {
            return Err(ExactPhi3CertificateError::Cell3DimensionMismatch {
                expected: c3_count,
                actual: vec![
                    certificate.flux_h.len(),
                    certificate.primal_residual.len(),
                    certificate.dual_witness.len(),
                    certificate.weights.len(),
                ],
            });
        }

        if certificate.d2.len() != c3_count {
            return Err(ExactPhi3CertificateError::D2RowMismatch {
                expected: c3_count,
                actual: certificate.d2.len(),
            });
        }

        for (row_idx, row) in certificate.d2.iter().enumerate() {
            if row.len() != c2_count {
                return Err(ExactPhi3CertificateError::D2ColumnMismatch {
                    row: row_idx,
                    expected: c2_count,
                    actual: row.len(),
                });
            }
        }
        Ok(())
    }

    fn check_d0_nilpotence(
        d1: &[Vec<BigRational>],
        d0: &[Vec<BigRational>],
        c2_count: usize,
        c1_count: usize,
    ) -> Result<(), ExactPhi3CertificateError> {
        let c0_count = d0.first().map_or(0, Vec::len);
        if d0.len() != c1_count {
            return Err(ExactPhi3CertificateError::D0DimensionMismatch {
                rows: d0.len(),
                expected_c1: c1_count,
                cols: c0_count,
            });
        }
        for row in d0.iter() {
            if row.len() != c0_count {
                return Err(ExactPhi3CertificateError::D0DimensionMismatch {
                    rows: d0.len(),
                    expected_c1: c1_count,
                    cols: row.len(),
                });
            }
        }

        for c2 in 0..c2_count {
            for c0 in 0..c0_count {
                let sum: BigRational = (0..c1_count).map(|c1| &d1[c2][c1] * &d0[c1][c0]).sum();
                if !sum.is_zero() {
                    return Err(ExactPhi3CertificateError::CochainNilpotenceViolation {
                        row: c2,
                        col: c0,
                        val: sum,
                    });
                }
            }
        }
        Ok(())
    }

    fn check_d1_and_d0_nilpotence(
        certificate: &ExactPhi3Certificate,
        d1: &[Vec<BigRational>],
        c3_count: usize,
        c2_count: usize,
    ) -> Result<(), ExactPhi3CertificateError> {
        let c1_count = d1.first().map_or(0, Vec::len);
        if d1.len() != c2_count {
            return Err(ExactPhi3CertificateError::D1DimensionMismatch {
                rows: d1.len(),
                expected_c2: c2_count,
                cols: c1_count,
            });
        }
        for row in d1.iter() {
            if row.len() != c1_count {
                return Err(ExactPhi3CertificateError::D1DimensionMismatch {
                    rows: d1.len(),
                    expected_c2: c2_count,
                    cols: row.len(),
                });
            }
        }

        // Bianchi identity nilpotence: d2 * d1 == 0
        for c3 in 0..c3_count {
            for c1 in 0..c1_count {
                let sum: BigRational = (0..c2_count)
                    .map(|c2| &certificate.d2[c3][c2] * &d1[c2][c1])
                    .sum();
                if !sum.is_zero() {
                    return Err(ExactPhi3CertificateError::BianchiNilpotenceViolation {
                        row: c3,
                        col: c1,
                        val: sum,
                    });
                }
            }
        }

        // Optional 1-skeleton nilpotence: d1 * d0 == 0
        if let Some(ref d0) = certificate.d0 {
            Self::check_d0_nilpotence(d1, d0, c2_count, c1_count)?;
        }
        Ok(())
    }

    fn check_primal_and_weights(
        certificate: &ExactPhi3Certificate,
        c3_count: usize,
        c2_count: usize,
    ) -> Result<(), ExactPhi3CertificateError> {
        // 4. Weight positivity
        for (i, w) in certificate.weights.iter().enumerate() {
            if *w <= BigRational::zero() {
                return Err(ExactPhi3CertificateError::NonPositiveWeight { index: i });
            }
        }

        // 5. Primal residual: r = H - d2 * B
        for c3 in 0..c3_count {
            let d2_b: BigRational = (0..c2_count)
                .map(|c2| &certificate.d2[c3][c2] * &certificate.potential_b[c2])
                .sum();
            let expected_r = &certificate.flux_h[c3] - &d2_b;
            if certificate.primal_residual[c3] != expected_r {
                return Err(ExactPhi3CertificateError::PrimalResidualMismatch {
                    index: c3,
                    expected: expected_r,
                    actual: certificate.primal_residual[c3].clone(),
                });
            }
        }
        Ok(())
    }

    fn check_dual_feasibility(
        certificate: &ExactPhi3Certificate,
        c3_count: usize,
        c2_count: usize,
    ) -> Result<(), ExactPhi3CertificateError> {
        // 6. Dual 3-cycle closure: d2^T * u = 0
        for c2 in 0..c2_count {
            let col_sum: BigRational = (0..c3_count)
                .map(|c3| &certificate.d2[c3][c2] * &certificate.dual_witness[c3])
                .sum();
            if !col_sum.is_zero() {
                return Err(ExactPhi3CertificateError::DualNotClosed3Cycle {
                    cell2: c2,
                    residual: col_sum,
                });
            }
        }

        // 7. Dual norm bound: |u_{c3}| <= nu_{c3}
        for c3 in 0..c3_count {
            if certificate.dual_witness[c3].abs() > certificate.weights[c3] {
                return Err(ExactPhi3CertificateError::DualNormBoundViolation {
                    cell3: c3,
                    val: certificate.dual_witness[c3].abs(),
                    bound: certificate.weights[c3].clone(),
                });
            }
        }
        Ok(())
    }

    fn check_objectives(
        certificate: &ExactPhi3Certificate,
        c3_count: usize,
    ) -> Result<(), ExactPhi3CertificateError> {
        // 8. Value non-negativity
        if certificate.reported_value < BigRational::zero() {
            return Err(ExactPhi3CertificateError::NegativeReportedValue);
        }

        // 9. Primal objective: sum_{c3} nu_{c3} * |r_{c3}| == reported_value
        let primal_sum: BigRational = (0..c3_count)
            .map(|c3| &certificate.weights[c3] * certificate.primal_residual[c3].abs())
            .sum();
        if primal_sum != certificate.reported_value {
            return Err(ExactPhi3CertificateError::PrimalValueMismatch);
        }

        // 10. Dual objective: sum_{c3} u_{c3} * H_{c3} == reported_value
        let dual_sum: BigRational = (0..c3_count)
            .map(|c3| &certificate.dual_witness[c3] * &certificate.flux_h[c3])
            .sum();
        if dual_sum != certificate.reported_value {
            return Err(ExactPhi3CertificateError::DualValueMismatch);
        }
        Ok(())
    }

    /// Replay and verify an exact rational degree-3 quotient obstruction certificate.
    pub fn verify_exact_certificate(
        certificate: ExactPhi3Certificate,
    ) -> Result<VerifiedExactPhi3, ExactPhi3CertificateError> {
        let c3_count = certificate.flux_h.len();
        let c2_count = certificate.potential_b.len();

        Self::check_denominators(&certificate)?;
        Self::check_dimensions(&certificate, c3_count, c2_count)?;

        // 3. Optional d1 and d0 verification & nilpotence laws
        if let Some(ref d1) = certificate.d1 {
            Self::check_d1_and_d0_nilpotence(&certificate, d1, c3_count, c2_count)?;
        }

        Self::check_primal_and_weights(&certificate, c3_count, c2_count)?;
        Self::check_dual_feasibility(&certificate, c3_count, c2_count)?;
        Self::check_objectives(&certificate, c3_count)?;

        Ok(VerifiedExactPhi3 { certificate })
    }

    /// Evaluate the Bianchi closure defect Γ₃(B) = ‖d₂ B‖_{1, ν} for a candidate 2-cochain B.
    pub fn evaluate_bianchi_defect(
        d2: &[Vec<BigRational>],
        potential_b: &[BigRational],
        weights: &[BigRational],
    ) -> Result<BigRational, ExactPhi3CertificateError> {
        let c3_count = d2.len();
        let c2_count = potential_b.len();

        if weights.len() != c3_count {
            return Err(ExactPhi3CertificateError::Cell3DimensionMismatch {
                expected: c3_count,
                actual: vec![weights.len()],
            });
        }

        for (index, weight) in weights.iter().enumerate() {
            if *weight <= BigRational::zero() {
                return Err(ExactPhi3CertificateError::NonPositiveWeight { index });
            }
        }

        let mut defect = BigRational::zero();
        for c3 in 0..c3_count {
            if d2[c3].len() != c2_count {
                return Err(ExactPhi3CertificateError::D2ColumnMismatch {
                    row: c3,
                    expected: c2_count,
                    actual: d2[c3].len(),
                });
            }
            let mut sum = BigRational::zero();
            for c2 in 0..c2_count {
                sum += &d2[c3][c2] * &potential_b[c2];
            }
            defect += &weights[c3] * sum.abs();
        }

        Ok(defect)
    }
}

// Origin: engine/crates_rs/core_functional/src/phi3.rs
// Claim: urn:core:crates_rs:core-functional:phi3:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }

    /// Build hollow 4-simplex boundary cell complex (S^3).
    /// |C0|=5, |C1|=10, |C2|=10, |C3|=5.
    /// Euler characteristic: 5 - 10 + 10 - 5 = 0.
    /// Betti numbers: b0 = 1, b1 = 0, b2 = 0, b3 = 1.
    fn simplex4_boundary_complex() -> (
        Vec<Vec<BigRational>>, // d0: 10 x 5
        Vec<Vec<BigRational>>, // d1: 10 x 10
        Vec<Vec<BigRational>>, // d2: 5 x 10
    ) {
        // 5 vertices: 0, 1, 2, 3, 4
        // 10 edges (i < j):
        // 0:(0,1), 1:(0,2), 2:(0,3), 3:(0,4),
        // 4:(1,2), 5:(1,3), 6:(1,4),
        // 7:(2,3), 8:(2,4),
        // 9:(3,4)

        // d0: 10 edges x 5 vertices
        let d0 = vec![
            vec![q(-1, 1), q(1, 1), q(0, 1), q(0, 1), q(0, 1)], // e0 (0,1)
            vec![q(-1, 1), q(0, 1), q(1, 1), q(0, 1), q(0, 1)], // e1 (0,2)
            vec![q(-1, 1), q(0, 1), q(0, 1), q(1, 1), q(0, 1)], // e2 (0,3)
            vec![q(-1, 1), q(0, 1), q(0, 1), q(0, 1), q(1, 1)], // e3 (0,4)
            vec![q(0, 1), q(-1, 1), q(1, 1), q(0, 1), q(0, 1)], // e4 (1,2)
            vec![q(0, 1), q(-1, 1), q(0, 1), q(1, 1), q(0, 1)], // e5 (1,3)
            vec![q(0, 1), q(-1, 1), q(0, 1), q(0, 1), q(1, 1)], // e6 (1,4)
            vec![q(0, 1), q(0, 1), q(-1, 1), q(1, 1), q(0, 1)], // e7 (2,3)
            vec![q(0, 1), q(0, 1), q(-1, 1), q(0, 1), q(1, 1)], // e8 (2,4)
            vec![q(0, 1), q(0, 1), q(0, 1), q(-1, 1), q(1, 1)], // e9 (3,4)
        ];

        // 10 triangular faces (i < j < k):
        // f0: (0,1,2) -> e4 - e1 + e0
        // f1: (0,1,3) -> e5 - e2 + e0
        // f2: (0,1,4) -> e6 - e3 + e0
        // f3: (0,2,3) -> e7 - e2 + e1
        // f4: (0,2,4) -> e8 - e3 + e1
        // f5: (0,3,4) -> e9 - e3 + e2
        // f6: (1,2,3) -> e7 - e5 + e4
        // f7: (1,2,4) -> e8 - e6 + e4
        // f8: (1,3,4) -> e9 - e6 + e5
        // f9: (2,3,4) -> e9 - e8 + e7
        let d1 = vec![
            vec![
                q(1, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
            ], // f0
            vec![
                q(1, 1),
                q(0, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
            ], // f1
            vec![
                q(1, 1),
                q(0, 1),
                q(0, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
            ], // f2
            vec![
                q(0, 1),
                q(1, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
            ], // f3
            vec![
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
            ], // f4
            vec![
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
            ], // f5
            vec![
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(-1, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
            ], // f6
            vec![
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(-1, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
            ], // f7
            vec![
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
            ], // f8
            vec![
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(-1, 1),
                q(1, 1),
            ], // f9
        ];

        // 5 tetrahedra (i < j < k < l):
        // c0: (0,1,2,3) -> f6 - f3 + f1 - f0
        // c1: (0,1,2,4) -> f7 - f4 + f2 - f0
        // c2: (0,1,3,4) -> f8 - f5 + f2 - f1
        // c3: (0,2,3,4) -> f9 - f5 + f4 - f3
        // c4: (1,2,3,4) -> f9 - f8 + f7 - f6
        let d2 = vec![
            vec![
                q(-1, 1),
                q(1, 1),
                q(0, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
            ], // c0
            vec![
                q(-1, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
            ], // c1
            vec![
                q(0, 1),
                q(-1, 1),
                q(1, 1),
                q(0, 1),
                q(0, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
                q(0, 1),
            ], // c2
            vec![
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(-1, 1),
                q(1, 1),
                q(-1, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(1, 1),
            ], // c3
            vec![
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(0, 1),
                q(-1, 1),
                q(1, 1),
                q(-1, 1),
                q(1, 1),
            ], // c4
        ];

        (d0, d1, d2)
    }

    #[test]
    fn test_simplex4_chain_laws_and_valid_b3_certificate() {
        let (d0, d1, d2) = simplex4_boundary_complex();

        // Target flux: uniform 3-flux H = [1/5, -1/5, 1/5, -1/5, 1/5]^T
        let flux_h = vec![q(1, 5), q(-1, 5), q(1, 5), q(-1, 5), q(1, 5)];
        let weights = vec![q(1, 1); 5];
        let potential_b = vec![q(0, 1); 10];
        let primal_residual = flux_h.clone();
        // Dual 3-cycle witness W = [1, -1, 1, -1, 1]^T
        let dual_witness = vec![q(1, 1), q(-1, 1), q(1, 1), q(-1, 1), q(1, 1)];
        let reported_value = q(1, 1);

        let cert = ExactPhi3Certificate {
            flux_h,
            d2,
            d1: Some(d1),
            d0: Some(d0),
            weights,
            potential_b,
            primal_residual,
            dual_witness,
            reported_value,
        };

        let verified = Phi3Functional::verify_exact_certificate(cert)
            .expect("Must certify valid b3=1 certificate with Bianchi identity");
        assert_eq!(*verified.value(), q(1, 1));
    }

    #[test]
    fn test_bianchi_identity_exact_flux_has_zero_defect() {
        let (_d0, d1, d2) = simplex4_boundary_complex();

        // Any exact 2-flux B = d1 * A
        let potential_a = vec![q(1, 2), q(0, 1), q(-1, 3), q(1, 4), q(2, 5)];
        let mut exact_flux_b = vec![BigRational::zero(); 10];
        for f in 0..10 {
            for v in 0..5 {
                exact_flux_b[f] += &d1[f][v] * &potential_a[v % potential_a.len()];
            }
        }

        let weights = vec![q(1, 1); 5];
        let defect = Phi3Functional::evaluate_bianchi_defect(&d2, &exact_flux_b, &weights)
            .expect("Must evaluate Bianchi defect");

        assert_eq!(
            defect,
            q(0, 1),
            "Bianchi defect of exact 2-flux must be identically zero"
        );
    }

    #[test]
    fn test_bianchi_defect_rejects_non_positive_weights() {
        let d2 = vec![vec![q(1, 1)]];
        let potential_b = vec![q(1, 1)];

        for weight in [q(0, 1), q(-1, 1)] {
            let result = Phi3Functional::evaluate_bianchi_defect(&d2, &potential_b, &[weight]);
            assert_eq!(
                result,
                Err(ExactPhi3CertificateError::NonPositiveWeight { index: 0 }),
            );
        }
    }

    #[test]
    fn test_simplex4_rejects_non_closed_3_chain() {
        let (d0, d1, d2) = simplex4_boundary_complex();
        let flux_h = vec![q(1, 5), q(-1, 5), q(1, 5), q(-1, 5), q(1, 5)];
        let weights = vec![q(1, 1); 5];
        let potential_b = vec![q(0, 1); 10];
        let primal_residual = flux_h.clone();

        // Leaking 3-chain: not a closed 3-cycle
        let leaking_witness = vec![q(1, 1), q(-1, 1), q(1, 1), q(-1, 1), q(0, 1)];
        let reported_value = q(4, 5);

        let cert = ExactPhi3Certificate {
            flux_h,
            d2,
            d1: Some(d1),
            d0: Some(d0),
            weights,
            potential_b,
            primal_residual,
            dual_witness: leaking_witness,
            reported_value,
        };

        match Phi3Functional::verify_exact_certificate(cert) {
            Err(ExactPhi3CertificateError::DualNotClosed3Cycle { cell2: _, residual }) => {
                assert!(!residual.is_zero());
            }
            other => panic!("Expected DualNotClosed3Cycle, got {:?}", other),
        }
    }

    fn minimal_closed_phi3(d0: Option<Vec<Vec<BigRational>>>) -> ExactPhi3Certificate {
        ExactPhi3Certificate {
            flux_h: vec![q(1, 1)],
            d2: vec![vec![q(0, 1)]],
            d1: None,
            d0,
            weights: vec![q(1, 1)],
            potential_b: vec![q(0, 1)],
            primal_residual: vec![q(1, 1)],
            dual_witness: vec![q(1, 1)],
            reported_value: q(1, 1),
        }
    }

    #[test]
    fn orphan_d0_without_d1_is_not_sealed() {
        assert!(Phi3Functional::verify_exact_certificate(minimal_closed_phi3(None)).is_ok());
        let orphan = minimal_closed_phi3(Some(vec![vec![q(9, 1)]]));
        assert_eq!(
            Phi3Functional::verify_exact_certificate(orphan),
            Err(ExactPhi3CertificateError::MissingD1ForD0)
        );
    }
}
