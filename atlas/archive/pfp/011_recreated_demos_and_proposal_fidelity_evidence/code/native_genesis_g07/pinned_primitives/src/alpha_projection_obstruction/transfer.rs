//! §5.6 — the reverse-triangle transfer certificate, premise-gated.
//!
//! With `C_P(x) = ‖x − P(x)‖₁` and a *checked* pairwise bound
//! `‖P(ρ) − P(σ)‖₁ ≤ L‖ρ − σ‖₁`, the certificate verifies
//! `C_P(ρ) ≥ C_P(σ) − (1 + L)‖ρ − σ‖₁`.  A failed premise is a refusal
//! even when the final inequality happens to hold: a receipt for the
//! conclusion is not evidence for the theorem that produced it.
//!
//! Replicates `transfer.py`.  Ledger E8: `ρ = (1, 2)`, `σ = (1, 0)`,
//! `P = [[1, 0], [0, 0]]`, `L = 1/2`: source distance 2, projection
//! distance 0, `C_P(ρ) = 2`, transfer lower bound `−3`.
//!
//! The estate's reading: the premise gate is `FW-SCOPE` as a type — the
//! `refusal` field names the failed premise, and `verify` insists that a
//! refused certificate carries no `transfer_holds` bit at all, so nothing
//! downstream can read a refusal as a weak pass.

use super::matrix::Matrix;
use super::rational::Rational;
use crate::certificate::{Certificate, CheckId, ObjectId};

/// Exact result for one compared pair and one declared Lipschitz constant.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ReverseTriangleCertificate {
    /// The supplied state and projection columns, retained for replay.
    pub states: [Matrix; 4],
    /// The premise held and the inequalities were evaluated.
    pub accepted: bool,
    /// `L`.
    pub lipschitz_constant: Rational,
    /// `‖ρ − σ‖₁`.
    pub source_distance: Rational,
    /// `‖P(ρ) − P(σ)‖₁`.
    pub projection_distance: Rational,
    /// `C_P(ρ)`.
    pub rho_defect: Rational,
    /// `C_P(σ)`.
    pub sigma_defect: Rational,
    /// `‖(ρ − Pρ) − (σ − Pσ)‖₁`.
    pub defect_difference: Rational,
    /// `C_P(σ) − (1 + L)‖ρ − σ‖₁`.
    pub transfer_lower_bound: Rational,
    /// `‖Pρ − Pσ‖₁ ≤ L‖ρ − σ‖₁`.
    pub pairwise_lipschitz_premise: bool,
    /// `C_P(ρ) ≥ C_P(σ) − defect_difference`, premise-free.
    pub reverse_triangle_holds: bool,
    /// `defect_difference ≤ (1 + L)‖ρ − σ‖₁`, when accepted.
    pub defect_difference_bound_holds: Option<bool>,
    /// `C_P(ρ) ≥ transfer_lower_bound`, when accepted.
    pub transfer_holds: Option<bool>,
    /// The failed premise, when refused.
    pub refusal: Option<String>,
}

/// Typed reason for refusal of the reverse triangle transfer premise.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TransferRefusalReason {
    /// Pairwise Lipschitz bound `‖Pρ − Pσ‖₁ ≤ L‖ρ − σ‖₁` failed.
    PairwiseLipschitzPremiseFailed,
}

impl TransferRefusalReason {
    /// Exact refusal code string.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::PairwiseLipschitzPremiseFailed => "pairwise_lipschitz_premise_failed",
        }
    }
}

impl ReverseTriangleCertificate {
    /// Return the typed refusal reason if refused.
    pub fn refusal_reason(&self) -> Option<TransferRefusalReason> {
        self.refusal.as_deref().and_then(|r| match r {
            "pairwise_lipschitz_premise_failed" => Some(TransferRefusalReason::PairwiseLipschitzPremiseFailed),
            _ => None,
        })
    }

    /// Recheck from the data alone.
    pub fn verify(&self) -> bool {
        let [rho, sigma, projected_rho, projected_sigma] = &self.states;
        if self.lipschitz_constant < Rational::ZERO || self.states.iter().any(|v|
            !v.is_well_formed() || v.cols != 1 || v.shape() != rho.shape()) { return false; }
        let left = rho.sub(projected_rho);
        let right = sigma.sub(projected_sigma);
        if self.source_distance != rho.sub(sigma).l1_norm()
            || self.projection_distance != projected_rho.sub(projected_sigma).l1_norm()
            || self.rho_defect != left.l1_norm() || self.sigma_defect != right.l1_norm()
            || self.defect_difference != left.sub(&right).l1_norm() { return false; }
        let reverse = self.rho_defect >= self.sigma_defect - self.defect_difference;
        let premise = self.projection_distance <= self.lipschitz_constant * self.source_distance;
        let lower = self.sigma_defect - (Rational::ONE + self.lipschitz_constant) * self.source_distance;
        if !reverse || reverse != self.reverse_triangle_holds || self.pairwise_lipschitz_premise != premise
            || self.accepted != premise || self.transfer_lower_bound != lower { return false; }
        if !self.accepted {
            return self.refusal_reason() == Some(TransferRefusalReason::PairwiseLipschitzPremiseFailed)
                && self.defect_difference_bound_holds.is_none() && self.transfer_holds.is_none();
        }
        let difference = self.defect_difference <= (Rational::ONE + self.lipschitz_constant) * self.source_distance;
        let transfer = self.rho_defect >= lower;
        self.refusal.is_none() && difference && transfer
            && self.defect_difference_bound_holds == Some(difference) && self.transfer_holds == Some(transfer)
    }

    /// The witness certificate, when accepted; nothing when refused.
    pub fn certificate(&self) -> Option<Certificate> {
        (self.verify() && self.accepted && self.transfer_holds == Some(true)).then(|| Certificate::Witness {
            object: ObjectId(format!("C_P(rho)={} >= {}", self.rho_defect, self.transfer_lower_bound)),
            check: CheckId(format!("pairwise Lipschitz premise checked at L={}; reverse triangle recomputed", self.lipschitz_constant)),
        })
    }
}

/// A bundle of state vectors and their projections.
#[derive(Clone, Copy, Debug)]
pub struct StatePairBundle<'a> {
    /// The source state vector `ρ`.
    pub rho: &'a Matrix,
    /// The reference state vector `σ`.
    pub sigma: &'a Matrix,
    /// The projected source state vector `P(ρ)`.
    pub projected_rho: &'a Matrix,
    /// The projected reference state vector `P(σ)`.
    pub projected_sigma: &'a Matrix,
}

impl<'a> StatePairBundle<'a> {
    /// Construct a new state pair bundle.
    pub fn new(rho: &'a Matrix, sigma: &'a Matrix, projected_rho: &'a Matrix, projected_sigma: &'a Matrix) -> Self {
        Self { rho, sigma, projected_rho, projected_sigma }
    }
}

/// Check the pairwise premise and the exact transfer inequality for a state pair bundle.
pub fn reverse_triangle_certificate_for_bundle(bundle: StatePairBundle<'_>, lipschitz: Rational) -> Result<ReverseTriangleCertificate, String> {
    let (rho, sigma, projected_rho, projected_sigma) = (bundle.rho, bundle.sigma, bundle.projected_rho, bundle.projected_sigma);
    for (name, v) in [("rho", rho), ("sigma", sigma), ("projected_rho", projected_rho), ("projected_sigma", projected_sigma)] {
        if !v.is_well_formed() || v.cols != 1 {
            return Err(format!("{name} must be a column vector"));
        }
    }
    if rho.shape() != sigma.shape() || rho.shape() != projected_rho.shape() || rho.shape() != projected_sigma.shape() {
        return Err("all four vectors must have the same shape".into());
    }
    if lipschitz < Rational::ZERO {
        return Err("lipschitz_constant must be nonnegative".into());
    }
    let source_distance = rho.sub(sigma).l1_norm();
    let projection_distance = projected_rho.sub(projected_sigma).l1_norm();
    let left_residual = rho.sub(projected_rho);
    let right_residual = sigma.sub(projected_sigma);
    let rho_defect = left_residual.l1_norm();
    let sigma_defect = right_residual.l1_norm();
    let defect_difference = left_residual.sub(&right_residual).l1_norm();
    let transfer_lower_bound = sigma_defect - (Rational::ONE + lipschitz) * source_distance;
    let premise = projection_distance <= lipschitz * source_distance;
    let reverse = rho_defect >= sigma_defect - defect_difference;
    let cert = if premise {
        ReverseTriangleCertificate {
            states: [rho.clone(), sigma.clone(), projected_rho.clone(), projected_sigma.clone()],
            accepted: true,
            lipschitz_constant: lipschitz,
            source_distance,
            projection_distance,
            rho_defect,
            sigma_defect,
            defect_difference,
            transfer_lower_bound,
            pairwise_lipschitz_premise: true,
            reverse_triangle_holds: reverse,
            defect_difference_bound_holds: Some(defect_difference <= (Rational::ONE + lipschitz) * source_distance),
            transfer_holds: Some(rho_defect >= transfer_lower_bound),
            refusal: None,
        }
    } else {
        ReverseTriangleCertificate {
            states: [rho.clone(), sigma.clone(), projected_rho.clone(), projected_sigma.clone()],
            accepted: false,
            lipschitz_constant: lipschitz,
            source_distance,
            projection_distance,
            rho_defect,
            sigma_defect,
            defect_difference,
            transfer_lower_bound,
            pairwise_lipschitz_premise: false,
            reverse_triangle_holds: reverse,
            defect_difference_bound_holds: None,
            transfer_holds: None,
            refusal: Some("pairwise_lipschitz_premise_failed".into()),
        }
    };
    if !cert.verify() {
        return Err("reverse-triangle certificate failed internal exact recheck".into());
    }
    Ok(cert)
}

/// Check the pairwise premise and the exact transfer inequality for four state matrices.
pub fn reverse_triangle_certificate(rho: &Matrix, sigma: &Matrix, projected_rho: &Matrix, projected_sigma: &Matrix, lipschitz: Rational) -> Result<ReverseTriangleCertificate, String> {
    reverse_triangle_certificate_for_bundle(StatePairBundle::new(rho, sigma, projected_rho, projected_sigma), lipschitz)
}

/// Convenience wrapper for an explicitly supplied exact linear projection
/// `P` (idempotence checked).
pub fn linear_projection_transfer_certificate(rho: &Matrix, sigma: &Matrix, projection: &Matrix, lipschitz: Rational) -> Result<ReverseTriangleCertificate, String> {
    if !projection.is_well_formed() || !rho.is_well_formed() || !sigma.is_well_formed() || projection.shape() != (rho.rows, rho.rows) {
        return Err(format!("projection has shape {:?}, expected {:?}", projection.shape(), (rho.rows, rho.rows)));
    }
    if sigma.shape() != rho.shape() {
        return Err("rho and sigma must have the same shape".into());
    }
    if projection.mul(projection) != *projection {
        return Err("projection matrix P is not idempotent (P^2 != P)".into());
    }
    reverse_triangle_certificate(rho, sigma, &projection.mul(rho), &projection.mul(sigma), lipschitz)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::alpha_projection_obstruction::rational::{q, r};

    /// E8: source 2, projection 0, `C_P(ρ) = 2`, lower bound −3.
    #[test]
    fn the_receipt_pair_certifies_with_lower_bound_minus_three() {
        let c = linear_projection_transfer_certificate(&Matrix::column_i128(&[1, 2]), &Matrix::column_i128(&[1, 0]), &Matrix::from_i128(&[&[1, 0], &[0, 0]]), r(1, 2)).unwrap();
        assert!(c.accepted && c.verify());
        assert_eq!((c.source_distance, c.projection_distance, c.rho_defect, c.transfer_lower_bound), (q(2), q(0), q(2), q(-3)));
        assert_eq!(c.transfer_holds, Some(true));
        assert!(c.certificate().is_some());
    }

    /// A failed premise is a refusal even where the inequality would hold.
    #[test]
    fn a_failed_premise_refuses_and_carries_no_transfer_bit() {
        // P = identity is 1-Lipschitz, not 1/2-Lipschitz: premise fails.
        let c = linear_projection_transfer_certificate(&Matrix::column_i128(&[1, 2]), &Matrix::column_i128(&[1, 0]), &Matrix::eye(2), r(1, 2)).unwrap();
        assert!(!c.accepted && c.verify());
        assert_eq!(c.refusal.as_deref(), Some("pairwise_lipschitz_premise_failed"));
        assert!(c.transfer_holds.is_none() && c.certificate().is_none());
        assert!(linear_projection_transfer_certificate(&Matrix::column_i128(&[1, 2]), &Matrix::column_i128(&[1, 0]), &Matrix::from_i128(&[&[1, 1], &[0, 1]]), q(1)).is_err());
    }
}
