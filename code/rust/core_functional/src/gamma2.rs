//! # Γ₂: Closure Defect Functional
//!
//! The **secondary diagnostic functional** in the finite obstruction calculus.
//!
//! ## Mathematical Definition
//!
//! ```text
//! Γ₂([h]) = ‖d₁h‖₁
//! ```
//!
//! Γ₂ measures whether a degree-1 residual `h ∈ C¹` is closed under the
//! coboundary map `d₁:C¹→C²`. It descends to `Q¹` only when `d₁d₀=0`.
//!
//! ## Contract alignment
//!
//! Aligned with `QUOTIENT_GAMMA2_CONTRACT` (symbol: Γ₂, ascii: Gamma2).
//!
//! ## Notation warning
//!
//! **Γ₂ is not Γ².** Γ₂ is the closure defect functional `‖d₁h‖₁`.
//! Γ² (gamma-square) is the cohomology gamma-square operation, which is a
//! completely different mathematical object. Do not confuse the two.

use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};

use core_kernel::evidence::{
    CarrierManifestHash, CertifiedScalar, Hash256, ReplayHash, ToleranceProfileHash,
};

/// Closure status of a residual under Γ₂.
///
/// Aligned with the contract's tolerance-mode vocabulary:
/// - `Closed`: Γ₂ = 0 in exact mode, or Γ₂ ≤ ε under declared tolerance.
/// - `Open`: Γ₂ > 0 in exact mode, or Γ₂ > ε under declared tolerance.
/// - `IndeterminateWithinTolerance`: near-threshold value where the tolerance
///   profile does not force a classification.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ClosureStatus {
    Closed,
    Open,
    IndeterminateWithinTolerance,
}

/// A cochain complex whose chain law `d1 * d0 = 0` has been verified.
///
/// Fields are private and `try_new` is the only constructor, so possessing a
/// value of this type IS the receipt that the chain law holds. Deserialization
/// routes through `try_new` via [`UntrustedCochainComplexWire`], so an untrusted
/// payload cannot present itself as a validated complex -- previously the `pub`
/// fields and a derived `Deserialize` both bypassed validation entirely, and a
/// literal with `d1 * d0 = 1` could reach `classify_exact` and mint a
/// `CertifiedExactTrichotomy` whose stated invariant was false.
/// This establishes a finite rational chain law, not a carrier identity, actor
/// license, or request-size bound. Ingress must bound serialized input separately.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "UntrustedCochainComplexWire")]
pub struct ExactCochainComplexQ {
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
    d0: Vec<Vec<BigRational>>, // c1 x c0
    d1: Vec<Vec<BigRational>>, // c2 x c1
}

/// Inbound, untrusted shape of a cochain complex.
///
/// Deserializing an [`ExactCochainComplexQ`] produces this first, then runs it
/// through `try_new`. A payload that fails validation fails to deserialize.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct UntrustedCochainComplexWire {
    pub c0_dim: usize,
    pub c1_dim: usize,
    pub c2_dim: usize,
    pub d0: Vec<Vec<BigRational>>,
    pub d1: Vec<Vec<BigRational>>,
}

impl TryFrom<UntrustedCochainComplexWire> for ExactCochainComplexQ {
    type Error = ExactGamma2Error;

    fn try_from(wire: UntrustedCochainComplexWire) -> Result<Self, Self::Error> {
        Self::try_new(wire.c0_dim, wire.c1_dim, wire.c2_dim, wire.d0, wire.d1)
    }
}

impl ExactCochainComplexQ {
    pub fn c0_dim(&self) -> usize {
        self.c0_dim
    }

    pub fn c1_dim(&self) -> usize {
        self.c1_dim
    }

    pub fn c2_dim(&self) -> usize {
        self.c2_dim
    }

    pub fn d0(&self) -> &[Vec<BigRational>] {
        &self.d0
    }

    pub fn d1(&self) -> &[Vec<BigRational>] {
        &self.d1
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub enum Complex2InputQ {
    Missing,
    Declared {
        c2_dim: usize,
        d1: Vec<Vec<BigRational>>,
    },
}

impl ExactCochainComplexQ {
    pub fn try_new_with_complex2(
        c0_dim: usize,
        c1_dim: usize,
        d0: Vec<Vec<BigRational>>,
        complex2: Complex2InputQ,
    ) -> Result<Self, ExactGamma2Error> {
        match complex2 {
            Complex2InputQ::Missing => Err(ExactGamma2Error::MissingComplex2),
            Complex2InputQ::Declared { c2_dim, d1 } => {
                Self::try_new(c0_dim, c1_dim, c2_dim, d0, d1)
            }
        }
    }

    pub fn try_new(
        c0_dim: usize,
        c1_dim: usize,
        c2_dim: usize,
        d0: Vec<Vec<BigRational>>,
        d1: Vec<Vec<BigRational>>,
    ) -> Result<Self, ExactGamma2Error> {
        let mut complex = Self {
            c0_dim,
            c1_dim,
            c2_dim,
            d0,
            d1,
        };
        complex.validate()?;
        for row in complex.d0.iter_mut().chain(&mut complex.d1) {
            for value in row {
                *value = canonical_rational(value);
            }
        }
        Ok(complex)
    }

    fn validate(&self) -> Result<(), ExactGamma2Error> {
        let Self {
            c0_dim,
            c1_dim,
            c2_dim,
            d0,
            d1,
        } = self;
        let (c0_dim, c1_dim, c2_dim) = (*c0_dim, *c1_dim, *c2_dim);
        if d0.len() != c1_dim {
            return Err(ExactGamma2Error::D0RowMismatch {
                expected: c1_dim,
                actual: d0.len(),
            });
        }
        for (row, coefficients) in d0.iter().enumerate() {
            if coefficients.len() != c0_dim {
                return Err(ExactGamma2Error::D0ColumnMismatch {
                    row,
                    expected: c0_dim,
                    actual: coefficients.len(),
                });
            }
        }
        if d1.len() != c2_dim {
            return Err(ExactGamma2Error::D1RowMismatch {
                expected: c2_dim,
                actual: d1.len(),
            });
        }
        for (row, coefficients) in d1.iter().enumerate() {
            if coefficients.len() != c1_dim {
                return Err(ExactGamma2Error::D1ColumnMismatch {
                    row,
                    expected: c1_dim,
                    actual: coefficients.len(),
                });
            }
        }

        validate_matrix_rationals(d0, "d0")?;
        validate_matrix_rationals(d1, "d1")?;
        verify_chain_law(d0, d1)
    }
}

fn validate_rationals(
    values: &[BigRational],
    field: &'static str,
    row: Option<usize>,
) -> Result<(), ExactGamma2Error> {
    for (column, value) in values.iter().enumerate() {
        if value.denom().is_zero() {
            return Err(ExactGamma2Error::ZeroDenominator { field, row, column });
        }
    }
    Ok(())
}

fn validate_matrix_rationals(
    matrix: &[Vec<BigRational>],
    field: &'static str,
) -> Result<(), ExactGamma2Error> {
    for (row, values) in matrix.iter().enumerate() {
        validate_rationals(values, field, Some(row))?;
    }
    Ok(())
}

/// Re-reduce an admitted rational (nonzero denominator) to canonical form.
/// The crate-wide copy; each caller keeps its own denominator admission.
pub(crate) fn canonical_rational(value: &BigRational) -> BigRational {
    // Only used after denominator admission; new_raw inputs may be unreduced
    // or carry a negative denominator even though they denote valid rationals.
    BigRational::new(value.numer().clone(), value.denom().clone())
}

/// Verify the cochain identity `d1 * d0 = 0` over exact rationals.
///
/// This is the receipt that makes a degree-one closure defect well defined on
/// the quotient `Q1 = C1 / im(d0)`: if `d1 * d0 = 0` then for any `alpha`,
/// `d1 (h + d0 alpha) = d1 h`, so `||d1 h||_1` does not depend on the chosen
/// representative. Without it the same computation is only a raw closure
/// defect on one representative, which is what `RawClosureDefectResult` carries.
///
/// Exact throughout: every entry is a `BigRational` product-sum compared against
/// zero, never a tolerance on a float.
fn verify_chain_law(
    d0: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
) -> Result<(), ExactGamma2Error> {
    for (row, d1_row) in d1.iter().enumerate() {
        // Iterate stored columns only. When C1 has dimension zero, d0 has no
        // rows and the composition is the zero map for every declared C0
        // dimension, without iterating that (possibly enormous) dimension.
        for (column, _) in d0.first().into_iter().flatten().enumerate() {
            let composition_entry = d1_row
                .iter()
                .zip(d0)
                .map(|(d1_entry, d0_row)| d1_entry.clone() * d0_row[column].clone())
                .sum::<BigRational>();
            if !composition_entry.is_zero() {
                return Err(ExactGamma2Error::CochainIdentityViolation { row, column });
            }
        }
    }
    Ok(())
}

/// A degree-one residual whose length matches its complex's `c1_dim`.
///
/// Fields are private and `try_new` is the only constructor. Previously the
/// `pub` fields let a caller pair a short residual with a wider complex; the
/// coboundary loop then zipped to the shorter side and reported Gamma2 = 0,
/// classifying an `ActiveClosureFailure` as a `ClosedResidual`.
pub struct DegreeOneResidualQ<'a> {
    complex: &'a ExactCochainComplexQ,
    h: Vec<BigRational>,
}

impl<'a> DegreeOneResidualQ<'a> {
    pub fn try_new(
        complex: &'a ExactCochainComplexQ,
        h: Vec<BigRational>,
    ) -> Result<Self, ExactGamma2Error> {
        validate_residual(complex, &h)?;
        Ok(Self {
            complex,
            h: h.iter().map(canonical_rational).collect(),
        })
    }

    pub fn complex(&self) -> &ExactCochainComplexQ {
        self.complex
    }

    pub fn h(&self) -> &[BigRational] {
        &self.h
    }
}

fn validate_residual(
    complex: &ExactCochainComplexQ,
    h: &[BigRational],
) -> Result<(), ExactGamma2Error> {
    if h.len() != complex.c1_dim {
        return Err(ExactGamma2Error::ResidualLengthMismatch {
            expected: complex.c1_dim,
            actual: h.len(),
        });
    }
    validate_rationals(h, "residual", None)
}

/// Raw closure defect result (does not require d1 * d0 = 0).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RawClosureDefectResult {
    residual: Vec<BigRational>,
    d1: Vec<Vec<BigRational>>,
    coboundary: Vec<BigRational>,
    value: BigRational,
}

impl RawClosureDefectResult {
    pub fn residual(&self) -> &[BigRational] {
        &self.residual
    }

    pub fn d1(&self) -> &[Vec<BigRational>] {
        &self.d1
    }

    pub fn coboundary(&self) -> &[BigRational] {
        &self.coboundary
    }

    pub fn value(&self) -> &BigRational {
        &self.value
    }
}

/// Sealed exact rational quotient-level Gamma2 evidence.
///
/// Construction verifies both the coboundary value and `d1 * d0 = 0`, so the
/// result is suitable for exact trichotomy classification on `Q1`.
/// It retains the complete validated complex, not just d0 and a reported value.
/// No wire deserialization or unchecked public construction can mint this type.
///
/// ```compile_fail
/// use core_functional::gamma2::ExactGamma2Result;
/// let forged: ExactGamma2Result = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactGamma2Result {
    residual: Vec<BigRational>,
    complex: ExactCochainComplexQ,
    coboundary: Vec<BigRational>,
    value: BigRational,
}

impl ExactGamma2Result {
    pub fn residual(&self) -> &[BigRational] {
        &self.residual
    }

    pub fn d0(&self) -> &[Vec<BigRational>] {
        self.complex.d0()
    }

    pub fn complex(&self) -> &ExactCochainComplexQ {
        &self.complex
    }

    pub fn coboundary(&self) -> &[BigRational] {
        &self.coboundary
    }

    pub fn value(&self) -> &BigRational {
        &self.value
    }
}

#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum ExactGamma2Error {
    #[error("gamma2 requires an explicit Complex2 declaration")]
    MissingComplex2,
    #[error("d0 has {actual} rows but residual has {expected} coordinates")]
    D0RowMismatch { expected: usize, actual: usize },
    #[error("d0 row {row} has {actual} columns but expected {expected}")]
    D0ColumnMismatch {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("d1 row {row} has {actual} columns but residual has {expected} coordinates")]
    D1ColumnMismatch {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("cochain identity d1 * d0 = 0 fails at row {row}, column {column}")]
    CochainIdentityViolation { row: usize, column: usize },
    #[error("d1 has {actual} rows but expected c2_dim {expected}")]
    D1RowMismatch { expected: usize, actual: usize },
    #[error("residual has length {actual} but expected c1_dim {expected}")]
    ResidualLengthMismatch { expected: usize, actual: usize },
    #[error("GAMMA2_ZERO_DENOMINATOR: {field} row {row:?}, column {column}")]
    ZeroDenominator {
        field: &'static str,
        row: Option<usize>,
        column: usize,
    },
}

/// Untrusted descriptive artifact for Γ₂, retained for wire-shape compatibility.
///
/// This DTO is NOT checked evidence. Its hashes, status, quotient flag and
/// optional artifact references are caller claims; deserialization validates
/// shape only. There is no conversion to [`ExactGamma2Result`]. Recompute using
/// the validated complex and residual before exact native classification.
///
/// Uses `exactness_artifact_hash` (not `certificate_hash`) because this is
/// the math-definition layer; certificates belong to a later certifier layer.
///
/// ```compile_fail
/// use core_functional::gamma2::{ExactGamma2Result, Gamma2Artifact};
/// fn requires_verified(_: &ExactGamma2Result) {}
/// fn forge(claim: &Gamma2Artifact) { requires_verified(claim); }
/// ```
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Gamma2Artifact {
    pub value: CertifiedScalar,
    pub coboundary_hash: Hash256,
    pub residual_hash: Hash256,
    pub d1_hash: Hash256,
    pub c2_basis_hash: Hash256,
    pub c2_norm_profile_hash: Hash256,
    pub carrier_hash: CarrierManifestHash,
    pub exactness_artifact_hash: Option<Hash256>,
    pub tolerance_profile_hash: Option<ToleranceProfileHash>,
    pub replay_hash: ReplayHash,
    pub closure_status: ClosureStatus,
    pub quotient_interpretation: bool,
}

pub struct Gamma2Functional;

impl Gamma2Functional {
    /// Compute exact raw closure defect.
    pub fn try_compute_raw(
        residual: &[BigRational],
        d1: &[Vec<BigRational>],
    ) -> Result<RawClosureDefectResult, ExactGamma2Error> {
        let c1_dim = residual.len();
        for (row, coefficients) in d1.iter().enumerate() {
            if coefficients.len() != c1_dim {
                return Err(ExactGamma2Error::D1ColumnMismatch {
                    row,
                    expected: c1_dim,
                    actual: coefficients.len(),
                });
            }
        }
        validate_rationals(residual, "residual", None)?;
        validate_matrix_rationals(d1, "d1")?;
        let residual: Vec<_> = residual.iter().map(canonical_rational).collect();
        let d1: Vec<Vec<_>> = d1
            .iter()
            .map(|row| row.iter().map(canonical_rational).collect())
            .collect();
        let coboundary = d1
            .iter()
            .map(|row| row.iter().zip(&residual).map(|(a, b)| a * b).sum())
            .collect::<Vec<BigRational>>();
        let value = coboundary.iter().map(|entry: &BigRational| entry.abs()).sum();

        Ok(RawClosureDefectResult {
            residual,
            d1,
            coboundary,
            value,
        })
    }

    /// Compute exact rational quotient-level Gamma2 evidence.
    ///
    /// This path verifies `d1 * d0 = 0` before reporting a quotient-level
    /// closure defect. Floating computations remain display diagnostics and
    /// cannot feed exact trichotomy.
    ///
    /// Public constructors and deserialization are sealed. Validation is also
    /// replayed at this evidence-producing boundary so future crate-internal
    /// construction cannot silently bypass rational, dimension or chain checks.
    pub fn try_compute_exact_quotient(
        residual: &DegreeOneResidualQ,
    ) -> Result<ExactGamma2Result, ExactGamma2Error> {
        let complex = residual.complex;
        complex.validate()?;
        validate_residual(complex, &residual.h)?;

        let raw = Self::try_compute_raw(&residual.h, &complex.d1)?;
        Ok(ExactGamma2Result {
            residual: residual.h.clone(),
            complex: complex.clone(),
            coboundary: raw.coboundary,
            value: raw.value,
        })
    }
}

use crate::binary_degree::{check_input_length, check_shape, BinaryDegreeError};
impl Gamma2Functional {
    pub fn binary(
        rows: &[Vec<bool>],
        domain_dim: usize,
        residual: &[bool],
    ) -> Result<usize, BinaryDegreeError> {
        check_shape(rows, domain_dim)?;
        check_input_length(residual, domain_dim)?;
        Ok(rows
            .iter()
            .filter(|row| {
                row.iter()
                    .zip(residual)
                    .fold(false, |parity, (coefficient, value)| {
                        parity ^ (*coefficient && *value)
                    })
            })
            .count())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IntegerGamma2Error {
    CapacityOverflow,
}

impl Gamma2Functional {
    /// The signed d1 value for the face. The three inputs are the already
    /// orientation-adjusted AB, BC, and CA edge coefficients.
    pub fn checked_closure([ab, bc, ca]: [i64; 3]) -> Result<i64, IntegerGamma2Error> {
        ab.checked_add(bc)
            .and_then(|partial| partial.checked_add(ca))
            .ok_or(IntegerGamma2Error::CapacityOverflow)
    }

    pub fn checked_face([ab, bc, ca]: [i64; 3]) -> Result<u64, IntegerGamma2Error> {
        Ok(Self::checked_closure([ab, bc, ca])?.unsigned_abs())
    }

    pub fn checked_total(face_masses: &[u64]) -> Result<u64, IntegerGamma2Error> {
        face_masses.iter().try_fold(0_u64, |total, face_mass| {
            total
                .checked_add(*face_mass)
                .ok_or(IntegerGamma2Error::CapacityOverflow)
        })
    }
}

// Origin: engine/crates_rs/core_functional/src/gamma2.rs
// Claim: urn:core:crates_rs:core-functional:gamma2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn compute_helper(
        res: &[BigRational],
        d0: &[Vec<BigRational>],
        d1: &[Vec<BigRational>],
    ) -> Result<ExactGamma2Result, ExactGamma2Error> {
        let c0_dim = d0.first().map_or(0, Vec::len);
        let c1_dim = res.len();
        let c2_dim = d1.len();
        let complex =
            ExactCochainComplexQ::try_new(c0_dim, c1_dim, c2_dim, d0.to_vec(), d1.to_vec())?;
        let q = DegreeOneResidualQ::try_new(&complex, res.to_vec())?;
        Gamma2Functional::try_compute_exact_quotient(&q)
    }

    #[test]
    fn test_exact_gamma2_checks_cochain_identity_and_value() {
        let result = compute_helper(&[r(2)], &[vec![r(0)]], &[vec![r(3)]]).unwrap();

        assert_eq!(result.coboundary(), &[r(6)]);
        assert_eq!(result.value(), &r(6));
    }

    #[test]
    fn test_exact_gamma2_rejects_nonzero_d1_d0() {
        assert_eq!(
            compute_helper(&[r(1)], &[vec![r(1)]], &[vec![r(1)]]),
            Err(ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 })
        );
    }

    #[test]
    fn rejects_missing_complex2() {
        assert_eq!(
            ExactCochainComplexQ::try_new_with_complex2(
                1,
                1,
                vec![vec![r(0)]],
                Complex2InputQ::Missing,
            ),
            Err(ExactGamma2Error::MissingComplex2)
        );

        let complex = ExactCochainComplexQ::try_new_with_complex2(
            1,
            1,
            vec![vec![r(0)]],
            Complex2InputQ::Declared {
                c2_dim: 1,
                d1: vec![vec![r(1)]],
            },
        )
        .expect("d1 * d0 = 0 for this declared Complex2");
        assert_eq!(complex.c2_dim(), 1);
        assert_eq!(complex.d1(), &[vec![r(1)]]);
    }

    /// The chain law must be enforced by the compute path, not only by
    /// `try_new`. This unit module deliberately uses crate-internal access to
    /// bypass the private constructor; before this check existed, the value
    /// below produced a sealed `ExactGamma2Result` on a non-complex
    /// (`d1 * d0 = 1 != 0`), which `classify_exact` would then accept as
    /// evidence for a `CertifiedExactTrichotomy`.
    #[test]
    fn struct_literal_complex_cannot_bypass_the_chain_law() {
        let complex = ExactCochainComplexQ {
            c0_dim: 1,
            c1_dim: 1,
            c2_dim: 1,
            d0: vec![vec![r(1)]],
            d1: vec![vec![r(1)]],
        };
        let residual = DegreeOneResidualQ {
            complex: &complex,
            h: vec![r(2)],
        };
        assert_eq!(
            Gamma2Functional::try_compute_exact_quotient(&residual),
            Err(ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 }),
            "a literal-constructed non-complex must not mint quotient-level evidence"
        );
    }

    /// A residual shorter than `d1`'s columns must refuse, not silently
    /// truncate. `zip` stops at the shorter side, so the missing coordinates
    /// contributed no terms and Gamma2 came out zero -- reporting an
    /// ActiveClosureFailure as a ClosedResidual.
    #[test]
    fn short_residual_refuses_instead_of_truncating_to_zero() {
        // d1 = [[0, 1]] over c1_dim = 2. The true residual [7, 3] has
        // d1 h = 3, so Gamma2 = 3 (ActiveClosureFailure). Supplying only [7]
        // used to yield 0*7 = 0 => Gamma2 = 0 (ClosedResidual).
        let complex = ExactCochainComplexQ {
            c0_dim: 1,
            c1_dim: 2,
            c2_dim: 1,
            d0: vec![vec![r(0)], vec![r(0)]],
            d1: vec![vec![r(0), r(1)]],
        };
        let truncated = DegreeOneResidualQ {
            complex: &complex,
            h: vec![r(7)],
        };
        assert_eq!(
            Gamma2Functional::try_compute_exact_quotient(&truncated),
            Err(ExactGamma2Error::ResidualLengthMismatch {
                expected: 2,
                actual: 1
            })
        );

        // The full residual still classifies correctly as nonzero.
        let full = DegreeOneResidualQ {
            complex: &complex,
            h: vec![r(7), r(3)],
        };
        let gamma2 = Gamma2Functional::try_compute_exact_quotient(&full)
            .expect("a well-formed residual over a valid complex must compute");
        assert_eq!(gamma2.value(), &r(3), "Gamma2 = |d1 h| = |3| = 3");
    }

    #[test]
    fn untrusted_artifact_claim_cannot_replace_exact_gamma2_recomputation() {
        // The old test asserted fields it just set, and falsely described a
        // requirement enforced nowhere. This deliberately false claim remains
        // shape-deserializable; checked native evidence must be recomputed.
        let artifact = Gamma2Artifact {
            value: CertifiedScalar::ExactRational(
                core_kernel::evidence::RationalValue::try_new(
                    num_bigint::BigInt::from(0),
                    num_bigint::BigInt::from(1),
                )
                .unwrap(),
            ),
            coboundary_hash: Hash256([0; 32]),
            residual_hash: Hash256([0; 32]),
            d1_hash: Hash256([0; 32]),
            c2_basis_hash: Hash256([0; 32]),
            c2_norm_profile_hash: Hash256([0; 32]),
            carrier_hash: CarrierManifestHash(Hash256([0; 32])),
            exactness_artifact_hash: None,
            tolerance_profile_hash: Some(ToleranceProfileHash(Hash256([0; 32]))),
            replay_hash: ReplayHash(Hash256([0; 32])),
            closure_status: ClosureStatus::Closed,
            quotient_interpretation: true,
        };
        let json = serde_json::to_string(&artifact).unwrap();
        let claim: Gamma2Artifact = serde_json::from_str(&json).unwrap();
        let computed = compute_helper(&[r(3)], &[vec![r(0)]], &[vec![r(1)]]).unwrap();
        assert_eq!(computed.value(), &r(3));
        assert_eq!(computed.coboundary(), &[r(3)]);
        assert_ne!(
            computed.value(),
            &r(0),
            "a DTO saying Closed is not evidence"
        );
        assert_eq!(claim.closure_status, ClosureStatus::Closed);
        assert!(claim.exactness_artifact_hash.is_none());
        // The compile-fail witness on Gamma2Artifact verifies the independent
        // type boundary: this claim cannot be passed to classify_exact.
    }

    #[test]
    fn every_declared_matrix_dimension_has_a_decisive_shape_refusal() {
        let cases = [
            (
                1,
                2,
                0,
                vec![vec![r(0)]],
                vec![],
                ExactGamma2Error::D0RowMismatch {
                    expected: 2,
                    actual: 1,
                },
            ),
            (
                2,
                1,
                0,
                vec![vec![r(0)]],
                vec![],
                ExactGamma2Error::D0ColumnMismatch {
                    row: 0,
                    expected: 2,
                    actual: 1,
                },
            ),
            (
                0,
                0,
                1,
                vec![],
                vec![],
                ExactGamma2Error::D1RowMismatch {
                    expected: 1,
                    actual: 0,
                },
            ),
            (
                0,
                1,
                1,
                vec![vec![]],
                vec![vec![]],
                ExactGamma2Error::D1ColumnMismatch {
                    row: 0,
                    expected: 1,
                    actual: 0,
                },
            ),
        ];
        for (c0, c1, c2, d0, d1, expected) in cases {
            assert_eq!(
                ExactCochainComplexQ::try_new(c0, c1, c2, d0, d1),
                Err(expected)
            );
        }
        let complex = ExactCochainComplexQ::try_new(0, 2, 0, vec![vec![], vec![]], vec![]).unwrap();
        assert_eq!(
            DegreeOneResidualQ::try_new(&complex, vec![r(0)]).err(),
            Some(ExactGamma2Error::ResidualLengthMismatch {
                expected: 2,
                actual: 1
            }),
        );
        assert!(DegreeOneResidualQ::try_new(&complex, vec![r(0), r(1)]).is_ok());
    }
    #[test]
    fn zero_denominators_are_refused_before_even_vacuous_arithmetic() {
        let invalid = || BigRational::new_raw(1.into(), 0.into());
        let refusal = |field, row| ExactGamma2Error::ZeroDenominator {
            field,
            row,
            column: 0,
        };
        assert_eq!(
            ExactCochainComplexQ::try_new(1, 1, 0, vec![vec![invalid()]], vec![]),
            Err(refusal("d0", Some(0))),
        );
        assert_eq!(
            ExactCochainComplexQ::try_new(0, 1, 1, vec![vec![]], vec![vec![invalid()]]),
            Err(refusal("d1", Some(0))),
        );
        let empty_d1 = ExactCochainComplexQ::try_new(0, 1, 0, vec![vec![]], vec![]).unwrap();
        assert_eq!(
            DegreeOneResidualQ::try_new(&empty_d1, vec![invalid()]).err(),
            Some(refusal("residual", None)),
        );
        assert_eq!(
            Gamma2Functional::try_compute_raw(&[invalid()], &[]),
            Err(refusal("residual", None))
        );
        assert_eq!(
            Gamma2Functional::try_compute_raw(&[r(0)], &[vec![invalid()]]),
            Err(refusal("d1", Some(0)))
        );
        let forged = DegreeOneResidualQ {
            complex: &empty_d1,
            h: vec![invalid()],
        };
        assert_eq!(
            Gamma2Functional::try_compute_exact_quotient(&forged),
            Err(refusal("residual", None))
        );
    }

    #[test]
    fn signed_unreduced_inputs_are_canonicalized_and_bind_the_complete_complex() {
        let raw = |a: i64, b: i64| BigRational::new_raw(a.into(), b.into());
        let complex = ExactCochainComplexQ::try_new(
            1,
            2,
            1,
            vec![vec![raw(-2, -2)], vec![raw(3, -3)]],
            vec![vec![raw(-2, -4), raw(3, 6)]],
        )
        .unwrap();
        let half = raw(1, 2);
        assert_eq!(complex.d0(), &[vec![r(1)], vec![r(-1)]]);
        assert_eq!(complex.d1(), &[vec![half.clone(), half.clone()]]);
        let canonical = ExactCochainComplexQ::try_new(
            1,
            2,
            1,
            vec![vec![r(1)], vec![r(-1)]],
            vec![vec![half.clone(), half]],
        )
        .unwrap();
        // Rational equality alone would not notice an unreduced encoding.
        // Wire equality witnesses the canonical bytes consumed by bindings.
        assert_eq!(
            serde_json::to_value(&complex).unwrap(),
            serde_json::to_value(&canonical).unwrap()
        );
        let h = DegreeOneResidualQ::try_new(&complex, vec![raw(-6, -2), raw(2, -2)]).unwrap();
        assert_eq!(h.h(), &[r(3), r(-1)]);
        assert_eq!(
            serde_json::to_value(h.h()).unwrap(),
            serde_json::to_value([r(3), r(-1)]).unwrap()
        );
        let result = Gamma2Functional::try_compute_exact_quotient(&h).unwrap();
        assert_eq!(result.value(), &r(1));
        assert_eq!(result.complex(), &complex);
        assert_eq!(result.d0(), complex.d0());
        let raw_result = Gamma2Functional::try_compute_raw(
            &[raw(-6, -2), raw(2, -2)],
            &[vec![raw(-2, -4), raw(3, 6)]],
        )
        .unwrap();
        assert_eq!(raw_result.residual(), result.residual());
        assert_eq!(raw_result.d1(), complex.d1());
        assert_eq!(
            serde_json::to_value(raw_result.residual()).unwrap(),
            serde_json::to_value(h.h()).unwrap()
        );
        assert_eq!(
            serde_json::to_value(raw_result.d1()).unwrap(),
            serde_json::to_value(canonical.d1()).unwrap()
        );
        assert_eq!(raw_result.value(), result.value());
        assert_eq!(raw_result.coboundary(), result.coboundary());
    }

    #[test]
    fn distinct_closure_maps_do_not_collapse_to_identical_zero_evidence() {
        let first = compute_helper(&[r(0)], &[vec![r(0)]], &[vec![r(0)]]).unwrap();
        let second = compute_helper(&[r(0)], &[vec![r(0)]], &[vec![r(2)]]).unwrap();
        assert_eq!(first.value(), second.value());
        assert_eq!(first.coboundary(), second.coboundary());
        assert_eq!(first.d0(), second.d0());
        assert_ne!(
            first, second,
            "d1 provenance must survive an equal scalar result"
        );
        assert_eq!(first.complex().d1(), &[vec![r(0)]]);
        assert_eq!(second.complex().d1(), &[vec![r(2)]]);
    }

    #[test]
    fn empty_middle_space_does_not_expand_unstored_outer_coordinates() {
        // Only two empty rows are stored; no million-coordinate allocation is
        // needed to establish the zero composition through a zero middle space.
        let complex =
            ExactCochainComplexQ::try_new(1_000_000, 0, 2, vec![], vec![vec![], vec![]]).unwrap();
        let h = DegreeOneResidualQ::try_new(&complex, vec![]).unwrap();
        let result = Gamma2Functional::try_compute_exact_quotient(&h).unwrap();
        assert_eq!(result.value(), &r(0));
        assert_eq!(result.coboundary(), &[r(0), r(0)]);
        assert_eq!(result.complex().c0_dim(), 1_000_000);
        assert_eq!(result.complex().c2_dim(), 2);
    }

    #[test]
    fn raw_closure_is_not_quotient_evidence_and_ragged_maps_are_refused() {
        let raw = Gamma2Functional::try_compute_raw(&[r(2)], &[vec![r(-3)]]).unwrap();
        assert_eq!(raw.coboundary(), &[r(-6)]);
        assert_eq!(raw.value(), &r(6));
        assert_eq!(
            compute_helper(&[r(2)], &[vec![r(1)]], &[vec![r(-3)]]),
            Err(ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 }),
        );
        assert_eq!(
            Gamma2Functional::try_compute_raw(&[r(2), r(9)], &[vec![r(-3)]]),
            Err(ExactGamma2Error::D1ColumnMismatch {
                row: 0,
                expected: 2,
                actual: 1
            }),
        );
    }

    // ── GTFOC-L20A (§18.1) — Φ–Γ separation, on the real exact Γ₂ functional ────
    //
    // L20A rests on (P0) d₁∘d₀ = 0 and (P2) ‖·‖ positive-definite on C². These
    // tests exercise the separation content directly through the exact Γ₂
    // computation (which enforces P0), on NONZERO data — so a non-exact complex
    // would visibly break them, unlike a dimension identity.

    fn triangle_d0() -> Vec<Vec<BigRational>> {
        // (d0 s)_{ij} = s_j - s_i over the triangle nerve; im(d0) = {sum = 0}.
        vec![
            vec![r(-1), r(1), r(0)],
            vec![r(0), r(-1), r(1)],
            vec![r(1), r(0), r(-1)],
        ]
    }

    #[test]
    fn l20a1_gamma2_vanishes_on_a_nonzero_coboundary() {
        // L20A.1 (separation): Φ1(q)=0 ⟹ q exact ⟹ Γ2(q)=0. The load-bearing
        // fact is that a *coboundary* is closed (via d1∘d0=0). d0=[[1],[-1]],
        // d1=[[1,1]] (d1∘d0=0), α=3 ⟹ q = d0·[3] = [3,-3] ≠ 0.
        let d0 = vec![vec![r(1)], vec![r(-1)]];
        let d1 = vec![vec![r(1), r(1)]];
        let coboundary = vec![r(3), r(-3)];
        let g = compute_helper(&coboundary, &d0, &d1).unwrap();
        assert_eq!(
            g.value(),
            &r(0),
            "a nonzero coboundary must be closed (Γ2=0)"
        );
        assert_eq!(g.coboundary(), &[r(0)]);
    }

    #[test]
    fn l20a_gamma2_descends_to_the_quotient() {
        // Γ2(h + d0·α) = Γ2(h): Γ2 is well-defined on Q1 (separation well-defined).
        let d0 = vec![vec![r(1)], vec![r(-1)]];
        let d1 = vec![vec![r(1), r(1)]];
        let h = vec![r(1), r(0)];
        let h_shifted = vec![r(4), r(-3)]; // h + d0·[3]
        let g_h = compute_helper(&h, &d0, &d1).unwrap();
        let g_shift = compute_helper(&h_shifted, &d0, &d1).unwrap();
        assert_eq!(g_h.value(), g_shift.value());
    }

    #[test]
    fn l20a3_gamma2_is_positive_on_a_non_closed_residual() {
        // L20A.3 (nonredundancy/open): d1·h ≠ 0 ⟹ Γ2(h) > 0 ⟹ OpenObstruction.
        let d0 = vec![vec![r(1)], vec![r(-1)]];
        let d1 = vec![vec![r(1), r(1)]];
        let h = vec![r(1), r(0)]; // d1·h = [1] ≠ 0
        let g = compute_helper(&h, &d0, &d1).unwrap();
        assert!(g.value() > &r(0));
    }

    #[test]
    fn l20a2_survivor_winding_cochain_is_closed() {
        // L20A.2 (survivor, closed half): on the unfilled triangle (d1=0) the
        // winding cochain [1,1,1] is closed (Γ2=0) and non-exact (coboundaries
        // have coordinate-sum 0, but 1+1+1=3) — a genuine StabilizedSurvivor.
        let d0 = triangle_d0();
        let d1 = vec![vec![r(0), r(0), r(0)]];
        let winding = vec![r(1), r(1), r(1)];
        let g = compute_helper(&winding, &d0, &d1).unwrap();
        assert_eq!(g.value(), &r(0));
    }

    #[test]
    fn l20a_p0_dependency_gamma2_refuses_non_exact_complex() {
        // L20A's hypothesis (P0) d1∘d0=0: the exact Γ2 path refuses to report a
        // quotient-level closure when P0 fails, instead of fabricating one.
        let d0 = vec![vec![r(1)]];
        let d1 = vec![vec![r(1)]]; // d1·d0 = [1] ≠ 0
        assert_eq!(
            compute_helper(&[r(2)], &d0, &d1),
            Err(ExactGamma2Error::CochainIdentityViolation { row: 0, column: 0 })
        );
    }
}

#[cfg(test)]
mod seal_tests {
    use super::*;
    use num_bigint::BigInt;

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    /// Deserialization must route through `try_new`, not bypass it.
    ///
    /// `ExactCochainComplexQ` previously derived `Deserialize` over public
    /// fields, so a wire payload with `d1 * d0 != 0` deserialized into a value
    /// whose type asserts the chain law holds. That value could then reach
    /// `classify_exact` and mint a `CertifiedExactTrichotomy` on a non-complex.
    #[test]
    fn untrusted_payload_violating_the_chain_law_fails_to_deserialize() {
        // Build the payload by serializing the WIRE type, so it is well-formed
        // JSON for BigRational by construction. A hand-written literal fails at
        // the wire layer for the wrong reason and would pass even with the seal
        // removed -- verified by neutralising the seal and watching such a test
        // stay green.
        let forged_wire = UntrustedCochainComplexWire {
            c0_dim: 1,
            c1_dim: 1,
            c2_dim: 1,
            d0: vec![vec![r(1)]],
            d1: vec![vec![r(1)]], // d1 * d0 = 1 != 0
        };
        let json = serde_json::to_string(&forged_wire).expect("wire serializes");

        // Precondition: the payload IS well-formed for the wire type, so any
        // rejection below comes from validation, not from parsing.
        serde_json::from_str::<UntrustedCochainComplexWire>(&json)
            .expect("payload must be well-formed at the wire layer");

        let result: Result<ExactCochainComplexQ, _> = serde_json::from_str(&json);
        assert!(
            result.is_err(),
            "a well-formed payload with d1*d0 != 0 must not deserialize into a validated complex"
        );
    }

    /// The discriminating half: a payload that DOES satisfy the chain law still
    /// round-trips. Without this, rejecting everything would pass the test above.
    #[test]
    fn valid_payload_still_round_trips_through_the_seal() {
        let complex = ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![r(0)]], vec![vec![r(0)]])
            .expect("zero maps satisfy d1 * d0 = 0");

        let json = serde_json::to_string(&complex).expect("serializes");
        let restored: ExactCochainComplexQ = serde_json::from_str(&json).expect("round-trips");
        assert_eq!(restored, complex);
        assert_eq!(restored.c1_dim(), 1);
        assert_eq!(restored.d1(), &[vec![r(0)]]);
    }

    #[test]
    fn unknown_or_duplicate_wire_fields_cannot_be_silently_ignored() {
        let complex = ExactCochainComplexQ::try_new(0, 0, 0, vec![], vec![]).unwrap();
        let valid = serde_json::to_string(&complex).unwrap();
        let unknown = format!("{{\"authority_effect\":\"approved\",{}", &valid[1..]);
        let error = serde_json::from_str::<ExactCochainComplexQ>(&unknown)
            .unwrap_err()
            .to_string();
        assert!(
            error.contains("unknown field `authority_effect`"),
            "{error}"
        );
        let duplicate = format!("{{\"c1_dim\":0,{}", &valid[1..]);
        let error = serde_json::from_str::<ExactCochainComplexQ>(&duplicate)
            .unwrap_err()
            .to_string();
        assert!(error.contains("duplicate field `c1_dim`"), "{error}");
        assert_eq!(
            serde_json::from_str::<ExactCochainComplexQ>(&valid).unwrap(),
            complex
        );
    }

    #[test]
    fn wire_denominator_refusal_is_not_mistaken_for_chain_law_evidence() {
        let mut wire = UntrustedCochainComplexWire {
            c0_dim: 1,
            c1_dim: 1,
            c2_dim: 0,
            d0: vec![vec![r(0)]],
            d1: vec![],
        };
        let valid = serde_json::to_string(&wire).unwrap();
        serde_json::from_str::<ExactCochainComplexQ>(&valid).unwrap();
        wire.d0[0][0] = BigRational::new_raw(1.into(), 0.into());
        let invalid = serde_json::to_string(&wire).unwrap();
        let error = serde_json::from_str::<ExactCochainComplexQ>(&invalid)
            .unwrap_err()
            .to_string();
        assert!(error.contains("denominator"), "{error}");
        // This rejection belongs to rational wire admission. The separate
        // well-formed non-chain test above establishes the chain-law gate itself.
    }

    #[test]
    fn explicit_complex2_wire_cannot_ignore_unsupported_structure_claims() {
        let declared = Complex2InputQ::Declared {
            c2_dim: 1,
            d1: vec![vec![r(0)]],
        };
        let mut wire = serde_json::to_value(&declared).unwrap();
        assert_eq!(
            serde_json::from_value::<Complex2InputQ>(wire.clone()).unwrap(),
            declared
        );
        wire["Declared"]["weighted_norm"] = serde_json::json!([999]);
        let error = serde_json::from_value::<Complex2InputQ>(wire)
            .unwrap_err()
            .to_string();
        assert!(error.contains("unknown field `weighted_norm`"), "{error}");
    }
}
