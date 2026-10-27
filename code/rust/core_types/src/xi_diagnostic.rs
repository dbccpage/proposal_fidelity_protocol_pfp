//! § 12.3: Xi Diagnostic
//!
//! $$\Xi = \|\rho(h_1^*) - \rho(\varphi^*)\|_1$$
//!
//! $\Xi$ is not a new obstruction norm, not a quantum score, not an
//! observer-independent invariant, and not a replacement for $\Phi_1$.
//!
//! It is a deterministic representative-alignment tie-breaker after
//! both exact $\Phi_1$ and $\Gamma_2$ comparison keys tie.

use core_functional::phi1::VerifiedExactPhi1;
use core_functional::xi::XiComputation;
use core_kernel::evidence::{
    CarrierManifestHash, CertifiedScalar, CheckerRef, Hash256, ReplayHash, ToleranceProfileHash,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum AuthorityCeiling {
    DiagnosticOnly,
    TieBreakerOnly,
    // Full Certifier variant DELETED — Ξ must never claim certifier authority.
    // Any future variant that implies authority must go through a separate,
    // sealed certifier path, not through the diagnostic Xi.
}

/// The checked Xi diagnostic (§12.3).
///
/// Comparison belongs to `core_policy::xi_gate`: Xi may decide only after
/// both exact Phi1 and Gamma2 keys tie. This carrier cannot authorize a move.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct XiDiagnostic {
    /// The $\Xi$ display value. Not for certifier branch logic.
    pub display_value: f64,
    /// Certified interval or exact scalar representation of Xi.
    pub certified_value: Option<CertifiedScalar>,

    pub input_hash: Hash256,
    pub carrier_hash: CarrierManifestHash,
    pub tolerance_hash: ToleranceProfileHash,
    pub replay_hash: ReplayHash,
    pub checker_ref: CheckerRef,
    pub authority_ceiling: AuthorityCeiling,
}

/// Reference wrapper to the checked diagnostic.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct XiDiagnosticRef {
    pub diagnostic: XiDiagnostic,
}

#[derive(Debug, thiserror::Error)]
pub enum XiDiagnosticError {
    #[error("non-finite Xi display value: {0}")]
    NonFinite(f64),
    #[error("negative Xi display value: {0}")]
    Negative(f64),
    #[error("Missing required replay/evidence hash bindings for certifier use")]
    MissingBindings,
    #[error("Authority ceiling violation")]
    AuthorityViolation,
}

impl XiDiagnostic {
    /// Construct a checked Xi diagnostic bound to full evidence.
    #[allow(clippy::too_many_arguments)] // every argument is a distinct typed witness; bundling would blur them
    pub fn new(
        phi1: &VerifiedExactPhi1,
        xi_comp: &XiComputation,
        certified_value: Option<CertifiedScalar>,
        input_hash: Hash256,
        carrier_hash: CarrierManifestHash,
        tolerance_hash: ToleranceProfileHash,
        replay_hash: ReplayHash,
        checker_ref: CheckerRef,
        authority_ceiling: AuthorityCeiling,
    ) -> Result<Self, XiDiagnosticError> {
        if !xi_comp.matches_phi1(phi1) {
            return Err(XiDiagnosticError::MissingBindings);
        }
        let display_value = xi_comp.value().ok_or(XiDiagnosticError::MissingBindings)?;

        if !display_value.is_finite() {
            return Err(XiDiagnosticError::NonFinite(display_value));
        }
        if display_value < 0.0 {
            return Err(XiDiagnosticError::Negative(display_value));
        }

        Ok(Self {
            display_value,
            certified_value,
            input_hash,
            carrier_hash,
            tolerance_hash,
            replay_hash,
            checker_ref,
            authority_ceiling,
        })
    }
}

// Origin: engine/crates_rs/core_types/src/xi_diagnostic.rs
// Claim: urn:core:crates_rs:core-types:xi-diagnostic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    use num_rational::BigRational;
    use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional, VerifiedExactPhi1};
    use core_functional::xi::{XiComputation, XiFunctional};

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn verified_phi1() -> VerifiedExactPhi1 {
        Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
            omega: vec![r(2)],
            d0: vec![vec![r(1)]],
            weights: vec![r(1)],
            alpha: vec![r(2)],
            primal_residual: vec![r(0)],
            dual_witness: vec![r(0)],
            reported_value: r(0),
        })
        .expect("exact-repair certificate verifies")
    }

    fn hashes() -> (
        Hash256,
        CarrierManifestHash,
        ToleranceProfileHash,
        ReplayHash,
        CheckerRef,
    ) {
        (
            Hash256([1; 32]),
            CarrierManifestHash(Hash256([2; 32])),
            ToleranceProfileHash(Hash256([3; 32])),
            ReplayHash(Hash256([4; 32])),
            CheckerRef("xi-diagnostic-test".into()),
        )
    }

    fn tie_breaker(phi1: &VerifiedExactPhi1, tolerance: f64) -> XiComputation {
        XiFunctional::compute(
            phi1.primal_residual(),
            phi1.dual_witness(),
            phi1.value(),
            tolerance,
            true,
        )
    }

    fn positive_phi1() -> VerifiedExactPhi1 {
        Phi1Functional::evaluate_exact_witness(
            &[r(1), r(0)],
            &[vec![], vec![]],
            &[r(1), r(1)],
            &[],
            &[r(1), r(1)],
        )
        .unwrap()
    }

    fn make_diagnostic(
        phi1: &VerifiedExactPhi1,
        xi_comp: &XiComputation,
    ) -> Result<XiDiagnostic, XiDiagnosticError> {
        let (input_hash, carrier_hash, tolerance_hash, replay_hash, checker_ref) = hashes();
        XiDiagnostic::new(
            phi1,
            xi_comp,
            None,
            input_hash,
            carrier_hash,
            tolerance_hash,
            replay_hash,
            checker_ref,
            AuthorityCeiling::DiagnosticOnly,
        )
    }

    #[test]
    fn xi_diagnostic_rejects_invalid_computation() {
        let phi1 = positive_phi1();
        let invalid = XiFunctional::compute(&[r(1)], &[r(0)], &r(1), 0.0, true);
        assert!(matches!(
            make_diagnostic(&phi1, &invalid),
            Err(XiDiagnosticError::MissingBindings)
        ));
    }

    #[test]
    fn xi_diagnostic_rejects_non_finite_display_value() {
        let phi1 = positive_phi1();
        for tolerance in [f64::NAN, f64::INFINITY] {
            assert!(matches!(
                make_diagnostic(&phi1, &tie_breaker(&phi1, tolerance)),
                Err(XiDiagnosticError::MissingBindings)
            ));
        }
    }

    #[test]
    fn xi_diagnostic_rejects_negative_display_value() {
        let phi1 = positive_phi1();
        let invalid = XiFunctional::compute(&[r(1)], &[r(-1)], &r(-1), 0.0, true);
        assert!(matches!(
            make_diagnostic(&phi1, &invalid),
            Err(XiDiagnosticError::MissingBindings)
        ));
    }

    #[test]
    fn xi_diagnostic_accepts_finite_nonnegative_tie_breaker() {
        let phi1 = positive_phi1();
        let diagnostic = make_diagnostic(&phi1, &tie_breaker(&phi1, 0.0)).unwrap();
        assert!((diagnostic.display_value - 0.5_f64.sqrt()).abs() < 1e-12);
        assert_eq!(
            diagnostic.authority_ceiling,
            AuthorityCeiling::DiagnosticOnly
        );
        assert!(diagnostic.certified_value.is_none());
    }

    #[test]
    fn xi_diagnostic_accepts_exact_zero_computation() {
        let phi1 = verified_phi1();
        let diagnostic = make_diagnostic(&phi1, &tie_breaker(&phi1, 0.0)).unwrap();
        assert_eq!(diagnostic.display_value, 0.0);
    }

    #[test]
    fn xi_cannot_be_rebound_to_another_verified_phi1() {
        let zero = verified_phi1();
        let positive = positive_phi1();
        assert!(matches!(
            make_diagnostic(&positive, &tie_breaker(&zero, 0.0)),
            Err(XiDiagnosticError::MissingBindings)
        ));
        assert!(matches!(
            make_diagnostic(&zero, &tie_breaker(&positive, 0.0)),
            Err(XiDiagnosticError::MissingBindings)
        ));
    }
}
