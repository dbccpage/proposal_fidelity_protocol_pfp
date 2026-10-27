//! # Phi2: Exact Degree-2 Quotient-Distance and 2-Flux Obstruction Certificates
//!
//! Higher-degree finite obstruction calculus in the chain/cochain complex:
//!
//! ```text
//! C²  <───d₁───  C¹  <───d₀───  C⁰       (cochains)
//! C₂  ───∂₂───>  C₁  ───∂₁───>  C₀       (chains, ∂₂ = d₁ᵀ, ∂₁ = d₀ᵀ)
//! ```
//!
//! With the cochain nilpotence law `d₁ ∘ d₀ = 0` (or `∂₁ ∘ ∂₂ = 0`).
//!
//! ## Mathematical Definition
//!
//! For a 2-cochain target flux `B ∈ C²(K; ℚ)` (field strength / curvature) on a
//! cell complex with non-trivial 2-cavities (`b₂ ≥ 1`):
//!
//! ```text
//! Φ₂([B]) = min_{A ∈ C¹(K; ℚ)} ‖B - d₁ A‖_{1, w}
//! ```
//!
//! By exact linear programming weak duality over `ℚ`:
//!
//! ```text
//! Φ₂([B]) ≥ max_{y ∈ C₂(K; ℚ)} ⟨B, y⟩
//! subject to:
//!   d₁ᵀ y = 0       (y ∈ Z₂(K; ℚ), closed 2-cycle / cavity)
//!   |y_f| ≤ w_f     ∀ f ∈ F
//! ```
//!
//! When primal and dual values match exactly, weak duality establishes optimality
//! with zero duality gap in `ℚ`.

use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};
use std::str::FromStr;

/// Wire shape for string-encoded rational certificate payloads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExactPhi2CertificateWire {
    pub flux_b: Vec<String>,
    pub d1: Vec<Vec<String>>,
    pub d0: Option<Vec<Vec<String>>>,
    pub weights: Vec<String>,
    pub potential_a: Vec<String>,
    pub primal_residual: Vec<String>,
    pub dual_witness: Vec<String>,
    pub reported_value: String,
}

impl TryFrom<ExactPhi2CertificateWire> for ExactPhi2Certificate {
    type Error = ExactPhi2CertificateError;

    fn try_from(wire: ExactPhi2CertificateWire) -> Result<Self, Self::Error> {
        fn parse_vec(v: &[String]) -> Result<Vec<BigRational>, ExactPhi2CertificateError> {
            crate::wire::parse_rational_vec(v, ExactPhi2CertificateError::InvalidRationalString)
        }
        fn parse_matrix(
            m: &[Vec<String>],
        ) -> Result<Vec<Vec<BigRational>>, ExactPhi2CertificateError> {
            crate::wire::parse_rational_matrix(m, ExactPhi2CertificateError::InvalidRationalString)
        }

        let flux_b = parse_vec(&wire.flux_b)?;
        let d1 = parse_matrix(&wire.d1)?;
        let d0 = match wire.d0 {
            Some(ref d0_mat) => Some(parse_matrix(d0_mat)?),
            None => None,
        };
        let weights = parse_vec(&wire.weights)?;
        let potential_a = parse_vec(&wire.potential_a)?;
        let primal_residual = parse_vec(&wire.primal_residual)?;
        let dual_witness = parse_vec(&wire.dual_witness)?;
        let reported_value = BigRational::from_str(&wire.reported_value).map_err(|_| {
            ExactPhi2CertificateError::InvalidRationalString(wire.reported_value.clone())
        })?;

        Ok(ExactPhi2Certificate {
            flux_b,
            d1,
            d0,
            weights,
            potential_a,
            primal_residual,
            dual_witness,
            reported_value,
        })
    }
}

/// Submitted exact finite rational witness for degree-2 quotient obstruction Φ₂([B]).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "ExactPhi2CertificateWire")]
pub struct ExactPhi2Certificate {
    /// Target 2-cochain flux B ∈ C² (length |F|)
    pub flux_b: Vec<BigRational>,
    /// Coboundary matrix d₁: C¹ → C² (|F| rows, |E| cols)
    pub d1: Vec<Vec<BigRational>>,
    /// Optional coboundary matrix d₀: C⁰ → C¹ (|E| rows, |V| cols)
    pub d0: Option<Vec<Vec<BigRational>>>,
    /// Strictly positive face weights w_f (length |F|)
    pub weights: Vec<BigRational>,
    /// Gauge 1-cochain potential A ∈ C¹ (length |E|)
    pub potential_a: Vec<BigRational>,
    /// Primal residual r = B - d₁ A (length |F|)
    pub primal_residual: Vec<BigRational>,
    /// Dual 2-cycle witness y ∈ Z₂(K; ℚ) satisfying d₁ᵀ y = 0 (length |F|)
    pub dual_witness: Vec<BigRational>,
    /// Certified optimal obstruction value in ℚ
    pub reported_value: BigRational,
}

/// Sealed result of replaying an [`ExactPhi2Certificate`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerifiedExactPhi2 {
    certificate: ExactPhi2Certificate,
}

impl VerifiedExactPhi2 {
    pub fn certificate(&self) -> &ExactPhi2Certificate {
        &self.certificate
    }

    pub fn value(&self) -> &BigRational {
        &self.certificate.reported_value
    }

    pub fn primal_residual(&self) -> &[BigRational] {
        &self.certificate.primal_residual
    }

    pub fn potential_a(&self) -> &[BigRational] {
        &self.certificate.potential_a
    }

    pub fn dual_witness(&self) -> &[BigRational] {
        &self.certificate.dual_witness
    }
}

#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum ExactPhi2CertificateError {
    #[error("invalid rational string: '{0}'")]
    InvalidRationalString(String),
    #[error("exact Phi2 input contains a rational with zero denominator")]
    ZeroRationalDenominator,
    #[error("flux_b, primal_residual, dual_witness, and weights must have length equal to face count {expected}, but found lengths {actual:?}")]
    FaceDimensionMismatch { expected: usize, actual: Vec<usize> },
    #[error("d1 matrix has {actual} rows but expected {expected} (|F|)")]
    D1RowMismatch { expected: usize, actual: usize },
    #[error("d1 row {row} has {actual} columns but expected {expected} (|E|)")]
    D1ColumnMismatch {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("d0 has dimension mismatch: rows={rows} (expected {expected_e}), cols={cols}")]
    D0DimensionMismatch {
        rows: usize,
        expected_e: usize,
        cols: usize,
    },
    #[error("cochain nilpotence law violated: (d1 * d0)[{row}][{col}] = {val} != 0")]
    ChainLawViolation {
        row: usize,
        col: usize,
        val: BigRational,
    },
    #[error("weight at face index {index} is non-positive")]
    NonPositiveWeight { index: usize },
    #[error("primal residual mismatch at face {index}: expected {expected}, got {actual}")]
    PrimalResidualMismatch {
        index: usize,
        expected: BigRational,
        actual: BigRational,
    },
    #[error("dual witness is not a closed 2-cycle: (d1^T * y) on edge {edge} = {residual} != 0")]
    DualNotClosed2Cycle { edge: usize, residual: BigRational },
    #[error("dual witness violates norm bound |y_{face}| = {val} > w_{face} = {bound}")]
    DualNormBoundViolation {
        face: usize,
        val: BigRational,
        bound: BigRational,
    },
    #[error("reported Phi2 value is negative")]
    NegativeReportedValue,
    #[error("reported Phi2 value does not match weighted primal residual norm")]
    PrimalValueMismatch,
    #[error("reported Phi2 value does not match dual pairing <B, y>")]
    DualValueMismatch,
}

pub struct Phi2Functional;

impl Phi2Functional {
    fn check_denominators(
        certificate: &ExactPhi2Certificate,
    ) -> Result<(), ExactPhi2CertificateError> {
        // 1. Zero denominator checks
        let mut all_vals = certificate
            .flux_b
            .iter()
            .chain(certificate.weights.iter())
            .chain(certificate.potential_a.iter())
            .chain(certificate.primal_residual.iter())
            .chain(certificate.dual_witness.iter())
            .chain(certificate.d1.iter().flatten())
            .chain(std::iter::once(&certificate.reported_value));

        if all_vals.any(|v| v.denom().is_zero()) {
            return Err(ExactPhi2CertificateError::ZeroRationalDenominator);
        }

        if let Some(ref d0) = certificate.d0 {
            if d0.iter().flatten().any(|v| v.denom().is_zero()) {
                return Err(ExactPhi2CertificateError::ZeroRationalDenominator);
            }
        }
        Ok(())
    }

    fn check_dimensions(
        certificate: &ExactPhi2Certificate,
        f_count: usize,
        e_count: usize,
    ) -> Result<(), ExactPhi2CertificateError> {
        // 2. Dimension validations
        let lengths_match = certificate.primal_residual.len() == f_count
            && certificate.dual_witness.len() == f_count
            && certificate.weights.len() == f_count;
        if !lengths_match {
            return Err(ExactPhi2CertificateError::FaceDimensionMismatch {
                expected: f_count,
                actual: vec![
                    certificate.flux_b.len(),
                    certificate.primal_residual.len(),
                    certificate.dual_witness.len(),
                    certificate.weights.len(),
                ],
            });
        }

        if certificate.d1.len() != f_count {
            return Err(ExactPhi2CertificateError::D1RowMismatch {
                expected: f_count,
                actual: certificate.d1.len(),
            });
        }

        for (row_idx, row) in certificate.d1.iter().enumerate() {
            if row.len() != e_count {
                return Err(ExactPhi2CertificateError::D1ColumnMismatch {
                    row: row_idx,
                    expected: e_count,
                    actual: row.len(),
                });
            }
        }
        Ok(())
    }

    fn check_d0_nilpotence(
        certificate: &ExactPhi2Certificate,
        d0: &[Vec<BigRational>],
        f_count: usize,
        e_count: usize,
    ) -> Result<(), ExactPhi2CertificateError> {
        let v_count = d0.first().map_or(0, Vec::len);
        if d0.len() != e_count {
            return Err(ExactPhi2CertificateError::D0DimensionMismatch {
                rows: d0.len(),
                expected_e: e_count,
                cols: v_count,
            });
        }
        for row in d0.iter() {
            if row.len() != v_count {
                return Err(ExactPhi2CertificateError::D0DimensionMismatch {
                    rows: d0.len(),
                    expected_e: e_count,
                    cols: row.len(),
                });
            }
        }

        // Check d1 * d0 == 0
        for f in 0..f_count {
            for v in 0..v_count {
                let sum: BigRational = (0..e_count)
                    .map(|e| &certificate.d1[f][e] * &d0[e][v])
                    .sum();
                if !sum.is_zero() {
                    return Err(ExactPhi2CertificateError::ChainLawViolation {
                        row: f,
                        col: v,
                        val: sum,
                    });
                }
            }
        }
        Ok(())
    }

    fn check_primal_and_weights(
        certificate: &ExactPhi2Certificate,
        f_count: usize,
        e_count: usize,
    ) -> Result<(), ExactPhi2CertificateError> {
        // 4. Weight positivity
        for (i, w) in certificate.weights.iter().enumerate() {
            if *w <= BigRational::zero() {
                return Err(ExactPhi2CertificateError::NonPositiveWeight { index: i });
            }
        }

        // 5. Primal residual: r = B - d1 * A
        for f in 0..f_count {
            let d1_a: BigRational = (0..e_count)
                .map(|e| &certificate.d1[f][e] * &certificate.potential_a[e])
                .sum();
            let expected_r = &certificate.flux_b[f] - &d1_a;
            if certificate.primal_residual[f] != expected_r {
                return Err(ExactPhi2CertificateError::PrimalResidualMismatch {
                    index: f,
                    expected: expected_r,
                    actual: certificate.primal_residual[f].clone(),
                });
            }
        }
        Ok(())
    }

    fn check_dual_feasibility(
        certificate: &ExactPhi2Certificate,
        f_count: usize,
        e_count: usize,
    ) -> Result<(), ExactPhi2CertificateError> {
        // 6. Dual 2-cycle closure: d1^T * y = 0
        for e in 0..e_count {
            let col_sum: BigRational = (0..f_count)
                .map(|f| &certificate.d1[f][e] * &certificate.dual_witness[f])
                .sum();
            if !col_sum.is_zero() {
                return Err(ExactPhi2CertificateError::DualNotClosed2Cycle {
                    edge: e,
                    residual: col_sum,
                });
            }
        }

        // 7. Dual norm bound: |y_f| <= w_f
        for f in 0..f_count {
            if certificate.dual_witness[f].abs() > certificate.weights[f] {
                return Err(ExactPhi2CertificateError::DualNormBoundViolation {
                    face: f,
                    val: certificate.dual_witness[f].abs(),
                    bound: certificate.weights[f].clone(),
                });
            }
        }
        Ok(())
    }

    fn check_objectives(
        certificate: &ExactPhi2Certificate,
        f_count: usize,
    ) -> Result<(), ExactPhi2CertificateError> {
        // 8. Value non-negativity
        if certificate.reported_value < BigRational::zero() {
            return Err(ExactPhi2CertificateError::NegativeReportedValue);
        }

        // 9. Primal objective: sum_f w_f * |r_f| == reported_value
        let primal_sum: BigRational = (0..f_count)
            .map(|f| &certificate.weights[f] * certificate.primal_residual[f].abs())
            .sum();
        if primal_sum != certificate.reported_value {
            return Err(ExactPhi2CertificateError::PrimalValueMismatch);
        }

        // 10. Dual objective: sum_f y_f * B_f == reported_value
        let dual_sum: BigRational = (0..f_count)
            .map(|f| &certificate.dual_witness[f] * &certificate.flux_b[f])
            .sum();
        if dual_sum != certificate.reported_value {
            return Err(ExactPhi2CertificateError::DualValueMismatch);
        }
        Ok(())
    }

    /// Replay and verify an exact rational degree-2 quotient obstruction certificate.
    pub fn verify_exact_certificate(
        certificate: ExactPhi2Certificate,
    ) -> Result<VerifiedExactPhi2, ExactPhi2CertificateError> {
        let f_count = certificate.flux_b.len();
        let e_count = certificate.potential_a.len();

        Self::check_denominators(&certificate)?;
        Self::check_dimensions(&certificate, f_count, e_count)?;

        // 3. Optional d0 verification & nilpotence d1 * d0 = 0
        if let Some(ref d0) = certificate.d0 {
            Self::check_d0_nilpotence(&certificate, d0, f_count, e_count)?;
        }

        Self::check_primal_and_weights(&certificate, f_count, e_count)?;
        Self::check_dual_feasibility(&certificate, f_count, e_count)?;
        Self::check_objectives(&certificate, f_count)?;

        Ok(VerifiedExactPhi2 { certificate })
    }
}

// Origin: engine/crates_rs/core_functional/src/phi2.rs
// Claim: urn:core:crates_rs:core-functional:phi2:l4-production-boundary:v1
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

    /// Build the standard hollow tetrahedron cell complex (b2 = 1).
    /// |V|=4, |E|=6, |F|=4.
    fn tetrahedron_complex() -> (Vec<Vec<BigRational>>, Vec<Vec<BigRational>>) {
        // d0: 6 edges x 4 vertices
        let d0 = vec![
            vec![q(-1, 1), q(1, 1), q(0, 1), q(0, 1)], // e0 (0,1)
            vec![q(-1, 1), q(0, 1), q(1, 1), q(0, 1)], // e1 (0,2)
            vec![q(-1, 1), q(0, 1), q(0, 1), q(1, 1)], // e2 (0,3)
            vec![q(0, 1), q(-1, 1), q(1, 1), q(0, 1)], // e3 (1,2)
            vec![q(0, 1), q(-1, 1), q(0, 1), q(1, 1)], // e4 (1,3)
            vec![q(0, 1), q(0, 1), q(-1, 1), q(1, 1)], // e5 (2,3)
        ];

        // d1: 4 faces x 6 edges
        let d1 = vec![
            vec![q(1, 1), q(-1, 1), q(0, 1), q(1, 1), q(0, 1), q(0, 1)], // f0 (0,1,2)
            vec![q(1, 1), q(0, 1), q(-1, 1), q(0, 1), q(1, 1), q(0, 1)], // f1 (0,1,3)
            vec![q(0, 1), q(1, 1), q(-1, 1), q(0, 1), q(0, 1), q(1, 1)], // f2 (0,2,3)
            vec![q(0, 1), q(0, 1), q(0, 1), q(1, 1), q(-1, 1), q(1, 1)], // f3 (1,2,3)
        ];

        (d0, d1)
    }

    #[test]
    fn test_tetrahedron_chain_law_and_valid_b2_certificate() {
        let (d0, d1) = tetrahedron_complex();

        // Target flux: uniform 2-flux B = [1/4, -1/4, 1/4, -1/4]^T
        let flux_b = vec![q(1, 4), q(-1, 4), q(1, 4), q(-1, 4)];
        let weights = vec![q(1, 1), q(1, 1), q(1, 1), q(1, 1)];
        let potential_a = vec![q(0, 1); 6];
        let primal_residual = flux_b.clone();
        // Dual 2-cycle witness Z = [1, -1, 1, -1]^T
        let dual_witness = vec![q(1, 1), q(-1, 1), q(1, 1), q(-1, 1)];
        let reported_value = q(1, 1);

        let cert = ExactPhi2Certificate {
            flux_b,
            d1,
            d0: Some(d0),
            weights,
            potential_a,
            primal_residual,
            dual_witness,
            reported_value,
        };

        let verified = Phi2Functional::verify_exact_certificate(cert)
            .expect("Must certify valid b2=1 certificate");
        assert_eq!(*verified.value(), q(1, 1));
    }

    #[test]
    fn test_tetrahedron_rejects_non_closed_2_chain() {
        let (d0, d1) = tetrahedron_complex();
        let flux_b = vec![q(1, 4), q(-1, 4), q(1, 4), q(-1, 4)];
        let weights = vec![q(1, 1), q(1, 1), q(1, 1), q(1, 1)];
        let potential_a = vec![q(0, 1); 6];
        let primal_residual = flux_b.clone();

        // Leaking 2-chain: dual is not a closed cycle
        let leaking_witness = vec![q(1, 1), q(-1, 1), q(1, 1), q(0, 1)];
        let reported_value = q(3, 4);

        let cert = ExactPhi2Certificate {
            flux_b,
            d1,
            d0: Some(d0),
            weights,
            potential_a,
            primal_residual,
            dual_witness: leaking_witness,
            reported_value,
        };

        match Phi2Functional::verify_exact_certificate(cert) {
            Err(ExactPhi2CertificateError::DualNotClosed2Cycle { edge, residual }) => {
                assert_eq!(edge, 3); // edge e3 = (1,2)
                assert_eq!(residual, q(1, 1));
            }
            other => panic!("Expected DualNotClosed2Cycle, got {:?}", other),
        }
    }

    #[test]
    fn test_tetrahedron_rejects_dual_norm_violation() {
        let (d0, d1) = tetrahedron_complex();
        let flux_b = vec![q(1, 4), q(-1, 4), q(1, 4), q(-1, 4)];
        let weights = vec![q(1, 1), q(1, 1), q(1, 1), q(1, 1)];
        let potential_a = vec![q(0, 1); 6];
        let primal_residual = flux_b.clone();

        // Scaled 2-cycle violating unit bound |y_f| <= 1
        let dual_witness = vec![q(2, 1), q(-2, 1), q(2, 1), q(-2, 1)];
        let reported_value = q(2, 1);

        let cert = ExactPhi2Certificate {
            flux_b,
            d1,
            d0: Some(d0),
            weights,
            potential_a,
            primal_residual,
            dual_witness,
            reported_value,
        };

        match Phi2Functional::verify_exact_certificate(cert) {
            Err(ExactPhi2CertificateError::DualNormBoundViolation { face, val, bound }) => {
                assert_eq!(face, 0);
                assert_eq!(val, q(2, 1));
                assert_eq!(bound, q(1, 1));
            }
            other => panic!("Expected DualNormBoundViolation, got {:?}", other),
        }
    }

    #[test]
    fn test_tetrahedron_rejects_duality_gap() {
        let (d0, d1) = tetrahedron_complex();
        let flux_b = vec![q(1, 4), q(-1, 4), q(1, 4), q(-1, 4)];
        let weights = vec![q(1, 1), q(1, 1), q(1, 1), q(1, 1)];
        let potential_a = vec![q(0, 1); 6];
        let primal_residual = flux_b.clone();

        // Scaled down 2-cycle: valid cycle, norm <= 1, but gap is 1 - 1/2 = 1/2 != 0
        let dual_witness = vec![q(1, 2), q(-1, 2), q(1, 2), q(-1, 2)];
        let reported_value = q(1, 1); // primal reported value

        let cert = ExactPhi2Certificate {
            flux_b,
            d1,
            d0: Some(d0),
            weights,
            potential_a,
            primal_residual,
            dual_witness,
            reported_value,
        };

        match Phi2Functional::verify_exact_certificate(cert) {
            Err(ExactPhi2CertificateError::DualValueMismatch) => (),
            other => panic!("Expected DualValueMismatch, got {:?}", other),
        }
    }
}
