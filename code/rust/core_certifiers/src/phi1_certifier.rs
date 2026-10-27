//! Exact rational max-form LP certificates for the `Phi1` vertical slice.
//!
//! The verifier checks the same finite weak-duality convention as
//! `PaperER007.lp_max_form_weak_duality`: `A x <= b`, `x >= 0`,
//! `A^T y >= c`, `y >= 0`, and equality of the primal and dual objectives.
//! Equality turns the weak-duality bounds into an exact optimality witness.
//!
//! A passing certificate is algebraic evidence only. It is not a
//! `CertifiedAuthority`, does not authorize a state transition, and carries no
//! release authority.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_6897bce4<T> {
    fn checked_invariant_6897bce4(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_6897bce4<T> for Option<T> {
    #[inline]
    fn checked_invariant_6897bce4(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_6897bce4<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_6897bce4(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::Zero;
use core_functional::phi1::{Phi1FormReplayError, Phi1Functional};
use core_types::{
    EvidenceStatus, ImplementationState, NormativeEffect, OperationalEffect, ReleaseAuthority,
};
use serde::Serialize;

/// Lean specification for the quotient-distance value certified by this slice.
///
/// `IsPhi1` is declared after `end FiniteCochainComplex`, so its full name is
/// `CoreCore.IsPhi1`; `CoreCore.FiniteCochainComplex.IsPhi1` is an unknown constant
/// (corrected 2026-09-29).
pub const LEAN_PHI1_SPECIFICATION: &str = "CoreCore.IsPhi1";
/// Lean weak-duality theorem replayed by the Rust verifier.
pub const LEAN_DUALITY_THEOREM: &str = "PaperER007.lp_max_form_weak_duality";
/// Repository source containing [`LEAN_PHI1_SPECIFICATION`].
///
/// Corrected 2026-08-04. The previous value pointed at
/// `lean4/002_finite_obstruction_calculus/000_primitive_axiomatics/CoreCosmology/Primitives/FiniteCochainComplex.lean`,
/// which **does not exist anywhere in the repository** — this crate declared a
/// Lean specification whose source file was absent.
/// These paths identify source bytes; Rust parity tests do not replay Lean.
pub const LEAN_SOURCE_BINDING_STATUS: &str = "SOURCE_BINDING_ONLY_NOT_NATIVE_LEAN_REPLAY";
pub const LEAN_PHI1_SOURCE_SHA256: &str =
    "7e8eb081ad4aab3df82c7362d2595a70b1e84fe83cccf1f5ac140bce33150914";
pub const LEAN_DUALITY_SOURCE_SHA256: &str =
    "4770ef54288b7b8f93be7085e0b3c71f03a4c74d02b2f52335deb34f34f9555b";
pub const LEAN_PHI1_CERTIFICATE_SOUNDNESS_SOURCE_SHA256: &str =
    "f9a23f807e1d71b8e805868b6be2795db51a7d0d8bdb6fc69101cdbc99047223";
pub const LEAN_PHI1_SOURCE: &str = "lean4/original_lean_20260809/finite_cochain_complex.lean";
/// Repository source containing [`LEAN_DUALITY_THEOREM`].
///
/// Corrected 2026-08-04; the previous value
/// (`lean4/008_engine_runtime/007_the_symbol_game/PaperER007/L007_07_LPWeakDuality.lean`)
/// also did not exist.
pub const LEAN_DUALITY_SOURCE: &str = "lean4/original_lean_20260809/er007_lp_weak_duality.lean";

/// Lean theorem establishing that a Φ₁ primal–dual certificate is **sound**:
/// achiever + `im(d)`-annihilating dual + no duality gap ⟹ the certified value is
/// the minimum.
///
/// `IsPhi1` demands an *achieved* minimum and was never proved inhabited. This
/// theorem is what turns a solver run into a kernel-checkable witness.
pub const LEAN_PHI1_CERTIFICATE_SOUNDNESS: &str =
    "CoreCore.Phi1Certificate.isMinimum_of_certificate";
/// Repository source containing [`LEAN_PHI1_CERTIFICATE_SOUNDNESS`].
pub const LEAN_PHI1_CERTIFICATE_SOUNDNESS_SOURCE: &str =
    "lean4/original_lean_20260809/phi1_primal_dual_certificate.lean";
/// Axioms permitted by the Epoch 4 Lean-to-Rust metadata contract.
pub const ALLOWED_LEAN_AXIOMS: [&str; 3] = ["propext", "Classical.choice", "Quot.sound"];

/// Immutable provenance and authority posture attached to a verified certificate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Phi1CertificateMetadata {
    lean_phi1_specification: &'static str,
    lean_phi1_source: &'static str,
    lean_duality_theorem: &'static str,
    lean_duality_source: &'static str,
    allowed_axioms: [&'static str; 3],
    evidence_status: EvidenceStatus,
    normative_effect: NormativeEffect,
    operational_effect: OperationalEffect,
    implementation_state: ImplementationState,
    release_authority: ReleaseAuthority,
}

impl Phi1CertificateMetadata {
    pub fn lean_phi1_specification(&self) -> &'static str {
        self.lean_phi1_specification
    }

    pub fn lean_phi1_source(&self) -> &'static str {
        self.lean_phi1_source
    }

    pub fn lean_duality_theorem(&self) -> &'static str {
        self.lean_duality_theorem
    }

    pub fn lean_duality_source(&self) -> &'static str {
        self.lean_duality_source
    }

    pub fn allowed_axioms(&self) -> &[&'static str; 3] {
        &self.allowed_axioms
    }

    pub fn evidence_status(&self) -> EvidenceStatus {
        self.evidence_status
    }

    pub fn normative_effect(&self) -> NormativeEffect {
        self.normative_effect
    }

    pub fn operational_effect(&self) -> OperationalEffect {
        self.operational_effect
    }

    pub fn implementation_state(&self) -> ImplementationState {
        self.implementation_state
    }

    pub fn release_authority(&self) -> ReleaseAuthority {
        self.release_authority
    }
}

/// A sealed exact-rational primal/dual optimality certificate.
///
/// Every field is private and this type implements no deserialization path, so
/// downstream crates can obtain a value only through [`Phi1Verifier::verify`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Phi1Certificate {
    primal: Vec<BigRational>,
    dual: Vec<BigRational>,
    constraint_matrix: Vec<Vec<BigRational>>,
    constraint_bounds: Vec<BigRational>,
    objective: Vec<BigRational>,
    primal_objective: BigRational,
    dual_objective: BigRational,
    metadata: Phi1CertificateMetadata,
}

impl Phi1Certificate {
    pub fn primal(&self) -> &[BigRational] {
        &self.primal
    }

    pub fn dual(&self) -> &[BigRational] {
        &self.dual
    }

    pub fn constraint_matrix(&self) -> &[Vec<BigRational>] {
        &self.constraint_matrix
    }

    pub fn constraint_bounds(&self) -> &[BigRational] {
        &self.constraint_bounds
    }

    pub fn objective(&self) -> &[BigRational] {
        &self.objective
    }

    pub fn primal_objective(&self) -> &BigRational {
        &self.primal_objective
    }

    pub fn dual_objective(&self) -> &BigRational {
        &self.dual_objective
    }

    pub fn metadata(&self) -> &Phi1CertificateMetadata {
        &self.metadata
    }
}

/// Typed refusal from exact certificate verification.
#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum CertificateError {
    /// A dimension mismatch, negative variable, or violated LP inequality.
    #[error("primal or dual candidate is infeasible")]
    Infeasible,
    /// Both candidates are feasible, but their exact objectives do not agree.
    #[error("exact primal and dual objectives differ")]
    DualityGapDetected,
}

/// Sole constructor for [`Phi1Certificate`].
///
/// The contract transition policy type is intentionally not convertible into
/// the canonical runtime authority enum:
///
/// ```compile_fail
/// use core_contracts::ContractEffect;
/// use core_types::AuthorityEffect;
///
/// let _: AuthorityEffect = ContractEffect::AuthorizesTransition.into();
/// ```
pub struct Phi1Verifier;

impl Phi1Verifier {
    fn check_primal_dual_feasibility(
        primal: &[BigRational],
        dual: &[BigRational],
        a: &[Vec<BigRational>],
        b: &[BigRational],
        c: &[BigRational],
    ) -> Result<(), CertificateError> {
        let zero = BigRational::zero();
        if primal.iter().any(|value| value < &zero) || dual.iter().any(|value| value < &zero) {
            return Err(CertificateError::Infeasible);
        }

        if a.iter()
            .zip(b)
            .any(|(row, bound)| dot(row, primal) > *bound)
        {
            return Err(CertificateError::Infeasible);
        }

        for (column, c_val) in c.iter().enumerate() {
            let transpose_value = a
                .iter()
                .zip(dual)
                .map(|(row, dual_value)| row[column].clone() * dual_value.clone())
                .sum::<BigRational>();
            if transpose_value < *c_val {
                return Err(CertificateError::Infeasible);
            }
        }
        Ok(())
    }

    /// Verify a maximum-form LP primal/dual pair using exact rational arithmetic.
    ///
    /// The convention is:
    ///
    /// - primal: maximize `c^T x` subject to `A x <= b` and `x >= 0`;
    /// - dual: minimize `b^T y` subject to `A^T y >= c` and `y >= 0`.
    pub fn verify<P, D, M, B, C>(
        primal: P,
        dual: D,
        a: M,
        b: B,
        c: C,
    ) -> Result<Phi1Certificate, CertificateError>
    where
        P: AsRef<[BigRational]>,
        D: AsRef<[BigRational]>,
        M: AsRef<[Vec<BigRational>]>,
        B: AsRef<[BigRational]>,
        C: AsRef<[BigRational]>,
    {
        let primal = primal.as_ref();
        let dual = dual.as_ref();
        let a = a.as_ref();
        let b = b.as_ref();
        let c = c.as_ref();
        let row_count = a.len();
        let column_count = primal.len();

        if b.len() != row_count
            || dual.len() != row_count
            || c.len() != column_count
            || a.iter().any(|row| row.len() != column_count)
        {
            return Err(CertificateError::Infeasible);
        }

        Self::check_primal_dual_feasibility(primal, dual, a, b, c)?;

        let primal_objective = dot(c, primal);
        let dual_objective = dot(b, dual);
        if primal_objective != dual_objective {
            return Err(CertificateError::DualityGapDetected);
        }

        Ok(Phi1Certificate {
            primal: primal.to_vec(),
            dual: dual.to_vec(),
            constraint_matrix: a.to_vec(),
            constraint_bounds: b.to_vec(),
            objective: c.to_vec(),
            primal_objective,
            dual_objective,
            metadata: Phi1CertificateMetadata {
                lean_phi1_specification: LEAN_PHI1_SPECIFICATION,
                lean_phi1_source: LEAN_PHI1_SOURCE,
                lean_duality_theorem: LEAN_DUALITY_THEOREM,
                lean_duality_source: LEAN_DUALITY_SOURCE,
                allowed_axioms: ALLOWED_LEAN_AXIOMS,
                evidence_status: EvidenceStatus::AlgebraicallyWitnessed,
                normative_effect: NormativeEffect::Proposal,
                operational_effect: OperationalEffect::Read,
                implementation_state: ImplementationState::Verified,
                release_authority: ReleaseAuthority::NotGranted,
            },
        })
    }
}

fn dot(left: &[BigRational], right: &[BigRational]) -> BigRational {
    left.iter()
        .zip(right)
        .map(|(left, right)| left.clone() * right.clone())
        .sum()
}

// ═════════════════════════════════════════════════════════════════════════════
// Φ₁-form certificate — the executable mirror of
// `CoreCore.Phi1Certificate.isMinimum_of_certificate`
// ═════════════════════════════════════════════════════════════════════════════
//
// [`Phi1Verifier`] above replays the GENERIC LP max-form weak duality
// (`A x <= b`, `x >= 0`, `A^T y >= c`, `y >= 0`, equal objectives). The Lean
// soundness theorem is stated in the Φ₁-SPECIFIC form: an achiever `alpha`, a
// dual `phi` annihilating every coboundary, `|phi_e| <= w_e`, and no duality gap.
//
// This section verifies exactly those three hypotheses, so the two languages
// check the same object rather than two cousins of it.

/// Try to compute weighted `l^1` norm: `sum_e w_e * |r_e|`.
/// Returns `DimensionMismatch` if weights and residual vectors differ in length.
pub fn try_wl1(w: &[BigRational], r: &[BigRational]) -> Result<BigRational, Phi1FormError> {
    Phi1Functional::weighted_l1_rational(w, r).ok_or_else(|| Phi1FormError::DimensionMismatch {
        expected: w.len(),
        actual: r.len(),
    })
}

/// Weighted `l^1` norm: `sum_e w_e * |r_e|`. Mirrors `CoreCore.Phi1Certificate.wl1`.
pub fn wl1(w: &[BigRational], r: &[BigRational]) -> BigRational {
    try_wl1(w, r).checked_invariant_6897bce4("weighted residual mass requires equal dimensions")
}

/// Why a Φ₁-form certificate was refused. Each variant names the Lean hypothesis
/// that failed, so a refusal is diagnostic rather than opaque.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum Phi1FormError {
    #[error("rational coordinate has a zero denominator")]
    ZeroRationalDenominator,
    #[error("negative weight at index {index}")]
    NegativeWeight { index: usize },
    /// Lengths of `w`, `omega`, `phi`, or a coboundary disagree.
    #[error("Dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    /// `hperp` failed: `<phi, d beta> != 0` for the listed coboundary.
    #[error("Dual not perpendicular: <phi, d beta> != 0 for coboundary {coboundary_index}")]
    DualNotPerpendicular { coboundary_index: usize },
    /// `hbound` failed: `|phi_e| > w_e`.
    #[error("Dual exceeds weight: |phi_e| > w_e at index {index}")]
    DualExceedsWeight { index: usize },
    /// `hgap` failed: `<phi, omega - d alpha> != wl1(w, omega - d alpha)`.
    #[error("Duality gap non-zero: <phi, r> != wl1(w, r)")]
    DualityGapNonZero,
}

/// A Φ₁-form certificate: achiever residual plus dual witness.
///
/// `coboundaries` is a spanning list of `d beta` vectors; `hperp` is checked
/// against each. `residual_at_achiever` is `omega - d alpha`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Phi1FormCertificate {
    /// Edge weights `w`.
    pub weights: Vec<BigRational>,
    /// `omega - d alpha` for the claimed achiever.
    pub residual_at_achiever: Vec<BigRational>,
    /// The dual witness `phi`.
    pub dual: Vec<BigRational>,
    /// Generators of `im(d)` the dual must annihilate.
    pub coboundaries: Vec<Vec<BigRational>>,
}

impl Phi1FormCertificate {
    /// Verify the three Lean hypotheses and return the certified Φ₁ value.
    ///
    /// A success is **algebraic evidence only**: it is not a `CertifiedAuthority`
    /// and grants no release authority. It certifies that the achiever is optimal
    /// — soundness, never necessity: absence of a certificate implies nothing.
    pub fn verify(&self) -> Result<BigRational, Phi1FormError> {
        Phi1Functional::replay_form(
            &self.weights,
            &self.residual_at_achiever,
            &self.dual,
            &self.coboundaries,
        )
        .map_err(|error| match error {
            Phi1FormReplayError::ZeroRationalDenominator => Phi1FormError::ZeroRationalDenominator,
            Phi1FormReplayError::NegativeWeight { index } => {
                Phi1FormError::NegativeWeight { index }
            }
            Phi1FormReplayError::DimensionMismatch { expected, actual } => {
                Phi1FormError::DimensionMismatch { expected, actual }
            }
            Phi1FormReplayError::DualNotPerpendicular { coboundary_index } => {
                Phi1FormError::DualNotPerpendicular { coboundary_index }
            }
            Phi1FormReplayError::DualExceedsWeight { index } => {
                Phi1FormError::DualExceedsWeight { index }
            }
            Phi1FormReplayError::DualityGapNonZero => Phi1FormError::DualityGapNonZero,
        })
    }

    /// Verify against the coboundary generators given as vectors, replacing
    /// `coboundaries`.
    pub fn verify_generators(
        &self,
        generators: &[nalgebra::DVector<BigRational>],
    ) -> Result<(), Phi1FormError> {
        let mut cert = self.clone();
        cert.coboundaries = generators
            .iter()
            .map(|g| g.iter().cloned().collect())
            .collect();
        cert.verify().map(|_| ())
    }
}

// Origin: engine/crates_rs/core_certifiers/src/phi1_certifier.rs
// Claim: urn:core:crates_rs:core-certifiers:phi1-certifier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod phi1_form_tests {
    use super::*;
    use num_bigint::BigInt;

    fn ri(n: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(n))
    }

    #[test]
    fn test_valid_phi1_certificate() {
        // Circulation in a 3-cycle: each d beta annihilates the constant dual.
        let cert = Phi1FormCertificate {
            weights: vec![ri(1), ri(1), ri(1)],
            residual_at_achiever: vec![ri(1), ri(1), ri(1)],
            dual: vec![ri(1), ri(1), ri(1)],
            coboundaries: vec![
                vec![ri(1), ri(-1), ri(0)],
                vec![ri(0), ri(1), ri(-1)],
                vec![ri(-1), ri(0), ri(1)],
            ],
        };
        assert_eq!(cert.verify().unwrap(), ri(3));
    }

    #[test]
    fn test_perturbed_dual_refused() {
        let cert = Phi1FormCertificate {
            weights: vec![ri(1), ri(1), ri(1)],
            residual_at_achiever: vec![ri(1), ri(1), ri(1)],
            dual: vec![ri(2), ri(1), ri(1)],
            coboundaries: vec![vec![ri(0), ri(0), ri(0)]],
        };
        assert!(matches!(
            cert.verify(),
            Err(Phi1FormError::DualExceedsWeight { .. })
        ));
    }

    #[test]
    fn verify_generators_uses_the_supplied_coboundaries() {
        let cert = Phi1FormCertificate {
            weights: vec![ri(1), ri(1), ri(1)],
            residual_at_achiever: vec![ri(1), ri(1), ri(1)],
            dual: vec![ri(1), ri(1), ri(1)],
            coboundaries: vec![],
        };
        let generators = [nalgebra::DVector::from_vec(vec![ri(1), ri(-1), ri(0)])];
        assert!(cert.verify_generators(&generators).is_ok());
        let breaking = [nalgebra::DVector::from_vec(vec![ri(1), ri(0), ri(0)])];
        assert!(matches!(
            cert.verify_generators(&breaking),
            Err(Phi1FormError::DualNotPerpendicular { .. })
        ));
    }
}
