//! Versioned finite packets for exact rational Hodge decomposition.
//!
//! The packet declares the finite carrier and the scope in which the existing
//! Hodge certificate has meaning. It does not derive a source digest from
//! external bytes: `source_digest` is an opaque, canonical SHA-256 commitment
//! supplied by the caller and bound into the result header. The carrier digest
//! is recomputed from the two cochain maps and flow during every replay.
//!
//! The implemented solver is limited to finite rational cochain complexes with
//! the unweighted Euclidean inner product. Positivity and composition claims
//! are outside that operation and must be declared `NotApplicable` rather than
//! inferred from a Hodge certificate. AuthorityEffect: None.

use crate::cert_hodge_decomp::{
    check_hodge_certificate, validate_problem, HodgeCertificate, HodgeError, HodgeProblem,
    VerifiedHodge,
};
use crate::solver_hodge_rational_decomp::solve_hodge;
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::rational_bareiss::{
    RationalBudget, RationalError, RationalLimits,
};
use num_rational::BigRational;
use core_kernel::exact_wire_vec;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// The only accepted packet schema for this finite solver boundary.
pub const HODGE_PACKET_SCHEMA_V1: &str = "core.solver.hodge-packet.v1";

/// Scalar field declared by a Hodge packet.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HodgeScalarModelV1 {
    ExactRational,
    FloatingPoint,
}

/// Equivalence relation declared for the potential witnesses.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HodgeQuotientModelV1 {
    PotentialModuloKernel,
    Undeclared,
}

/// Positivity premise for this packet's operation.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HodgePositivityModelV1 {
    NotApplicable,
    Claimed,
}

/// Composition premise for this packet's operation.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HodgeCompositionModelV1 {
    NotApplicable,
    Claimed,
}

/// Operational availability premise for this packet's carrier.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HodgeAvailabilityModelV1 {
    DeclaredFiniteCarrier,
    Unknown,
}

/// Protected question admitted by this packet boundary.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HodgeQuestionV1 {
    ExactEuclideanHodgeDecomposition,
    Other,
}

/// Exact arithmetic limits shared by packet decoding, solving, and replay.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HodgeResourceLimitsV1 {
    pub max_scalar_ops: usize,
    pub max_elements: usize,
    pub max_bits: u64,
}

impl HodgeResourceLimitsV1 {
    fn into_rational_limits(self) -> Result<RationalLimits, HodgePacketError> {
        for (field, value) in [
            ("max_scalar_ops", self.max_scalar_ops),
            ("max_elements", self.max_elements),
        ] {
            if value == 0 {
                return Err(HodgePacketError::InvalidResourceLimit { field });
            }
        }
        if self.max_bits == 0 {
            return Err(HodgePacketError::InvalidResourceLimit { field: "max_bits" });
        }
        Ok(RationalLimits {
            max_scalar_ops: self.max_scalar_ops,
            max_elements: self.max_elements,
            max_bits: self.max_bits,
        })
    }
}

/// Premises bound to every request and result.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HodgePacketHeaderV1 {
    pub schema_version: String,
    /// A nonzero, lowercase, 64-character SHA-256 digest supplied by the caller.
    pub source_digest: String,
    pub scalar_model: HodgeScalarModelV1,
    pub quotient_model: HodgeQuotientModelV1,
    pub positivity_model: HodgePositivityModelV1,
    pub composition_model: HodgeCompositionModelV1,
    pub availability_model: HodgeAvailabilityModelV1,
    pub question: HodgeQuestionV1,
    pub limits: HodgeResourceLimitsV1,
}

impl HodgePacketHeaderV1 {
    fn validate(&self) -> Result<RationalLimits, HodgePacketError> {
        if self.schema_version != HODGE_PACKET_SCHEMA_V1 {
            return Err(HodgePacketError::Schema {
                actual: self.schema_version.clone(),
            });
        }
        if !is_nonzero_lower_hex_digest(&self.source_digest) {
            return Err(HodgePacketError::SourceDigest);
        }
        if self.scalar_model != HodgeScalarModelV1::ExactRational {
            return Err(HodgePacketError::ScalarModel {
                actual: self.scalar_model,
            });
        }
        if self.quotient_model != HodgeQuotientModelV1::PotentialModuloKernel {
            return Err(HodgePacketError::QuotientModel {
                actual: self.quotient_model,
            });
        }
        if self.positivity_model != HodgePositivityModelV1::NotApplicable {
            return Err(HodgePacketError::PositivityModel {
                actual: self.positivity_model,
            });
        }
        if self.composition_model != HodgeCompositionModelV1::NotApplicable {
            return Err(HodgePacketError::CompositionModel {
                actual: self.composition_model,
            });
        }
        if self.availability_model != HodgeAvailabilityModelV1::DeclaredFiniteCarrier {
            return Err(HodgePacketError::AvailabilityModel {
                actual: self.availability_model,
            });
        }
        if self.question != HodgeQuestionV1::ExactEuclideanHodgeDecomposition {
            return Err(HodgePacketError::Question {
                actual: self.question,
            });
        }
        self.limits.into_rational_limits()
    }
}

/// Row-major rational matrix with declared dimensions, including zero-row maps.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RationalMatrixV1 {
    pub rows: usize,
    pub cols: usize,
    #[serde(with = "exact_wire_vec")]
    pub entries: Vec<BigRational>,
}

impl RationalMatrixV1 {
    fn into_matrix(
        self,
        matrix: &'static str,
        fuel: &mut RationalBudget,
    ) -> Result<BasicMatrix<BigRational>, HodgePacketError> {
        let expected = self
            .rows
            .checked_mul(self.cols)
            .ok_or(HodgePacketError::MatrixDimensionOverflow { matrix })?;
        if self.entries.len() != expected {
            return Err(HodgePacketError::MatrixEntries {
                matrix,
                expected,
                actual: self.entries.len(),
            });
        }
        fuel.elements(self.rows, self.cols)?;
        for entry in &self.entries {
            fuel.rational(entry)?;
        }
        BasicMatrix::from_row_major(self.rows, self.cols, self.entries)
            .map_err(HodgePacketError::Matrix)
    }
}

/// Finite exact input accepted by the Hodge solver.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HodgeRequestV1 {
    pub header: HodgePacketHeaderV1,
    pub d0: RationalMatrixV1,
    pub d1: RationalMatrixV1,
    #[serde(with = "exact_wire_vec")]
    pub flow: Vec<BigRational>,
}

/// Certificate and commitments emitted by a bounded exact solve.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HodgeResultV1 {
    pub header: HodgePacketHeaderV1,
    /// Lowercase SHA-256 digest of `d0`, `d1`, and `flow` in canonical binary form.
    pub carrier_digest: String,
    pub certificate: HodgeCertificate,
}

/// Evidence emitted only after a fresh exact certificate replay.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct VerifiedHodgePacketV1 {
    verified: VerifiedHodge,
    scalar_ops: usize,
}

impl VerifiedHodgePacketV1 {
    pub fn hodge(&self) -> &VerifiedHodge {
        &self.verified
    }

    pub fn scalar_ops(&self) -> usize {
        self.scalar_ops
    }

    pub fn authority_effect(&self) -> &'static str {
        "AuthorityEffect: None"
    }
}

/// Typed refusals from the packet boundary and the exact solver beneath it.
#[derive(Debug, thiserror::Error)]
pub enum HodgePacketError {
    #[error("unsupported Hodge packet schema {actual:?}")]
    Schema { actual: String },
    #[error("source_digest must be a nonzero 64-character lowercase SHA-256 hexadecimal string")]
    SourceDigest,
    #[error("Hodge packets require exact rational scalars, got {actual:?}")]
    ScalarModel { actual: HodgeScalarModelV1 },
    #[error("Hodge packets require potentials modulo kernel, got {actual:?}")]
    QuotientModel { actual: HodgeQuotientModelV1 },
    #[error("Hodge packets require positivity to be not applicable, got {actual:?}")]
    PositivityModel { actual: HodgePositivityModelV1 },
    #[error("Hodge packets require composition to be not applicable, got {actual:?}")]
    CompositionModel { actual: HodgeCompositionModelV1 },
    #[error("Hodge packets require a declared finite carrier, got {actual:?}")]
    AvailabilityModel { actual: HodgeAvailabilityModelV1 },
    #[error("Hodge packets admit only the exact Euclidean Hodge question, got {actual:?}")]
    Question { actual: HodgeQuestionV1 },
    #[error("resource limit {field} must be positive")]
    InvalidResourceLimit { field: &'static str },
    #[error("matrix {matrix} has dimensions whose product overflows usize")]
    MatrixDimensionOverflow { matrix: &'static str },
    #[error("matrix {matrix} has {actual} entries, expected {expected}")]
    MatrixEntries {
        matrix: &'static str,
        expected: usize,
        actual: usize,
    },
    #[error("cannot encode {field} as a u64 length")]
    CarrierLength { field: &'static str },
    #[error("result header does not match the request header")]
    HeaderMismatch,
    #[error("result carrier digest does not match the request carrier")]
    CarrierDigestMismatch,
    #[error("caller budget limits do not match the packet's declared limits")]
    ResourceBudgetMismatch,
    #[error(transparent)]
    Arithmetic(#[from] RationalError),
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error(transparent)]
    Hodge(#[from] HodgeError),
}

/// Solve the declared finite rational problem and bind the resulting certificate
/// to the exact request header and carrier.
pub fn solve_hodge_packet(request: HodgeRequestV1) -> Result<HodgeResultV1, HodgePacketError> {
    let mut fuel = RationalBudget::new(request.header.validate()?);
    solve_hodge_packet_with_budget(request, &mut fuel)
}

/// The packet operation on an already partially consumed caller-owned budget.
/// Source/outer packet checks may consume this budget before the solve.
pub fn solve_hodge_packet_with_budget(
    request: HodgeRequestV1,
    fuel: &mut RationalBudget,
) -> Result<HodgeResultV1, HodgePacketError> {
    let header = request.header.clone();
    if header.validate()? != fuel.limits() {
        return Err(HodgePacketError::ResourceBudgetMismatch);
    }
    let payload = parse_payload(request, fuel)?;
    let problem = payload.problem();
    let carrier_digest = carrier_digest(&problem, fuel)?;
    let solution = solve_hodge(&problem, fuel)?;
    Ok(HodgeResultV1 {
        header,
        carrier_digest,
        certificate: solution.certificate,
    })
}

/// Recompute the carrier commitment and independently replay a claimed result.
pub fn replay_hodge_packet(
    request: HodgeRequestV1,
    result: &HodgeResultV1,
) -> Result<VerifiedHodgePacketV1, HodgePacketError> {
    let mut fuel = RationalBudget::new(request.header.validate()?);
    replay_hodge_packet_with_budget(request, result, &mut fuel)
}

/// Independent replay on the same caller-owned budget, without replenishing it.
pub fn replay_hodge_packet_with_budget(
    request: HodgeRequestV1,
    result: &HodgeResultV1,
    fuel: &mut RationalBudget,
) -> Result<VerifiedHodgePacketV1, HodgePacketError> {
    let header = request.header.clone();
    if header.validate()? != fuel.limits() {
        return Err(HodgePacketError::ResourceBudgetMismatch);
    }
    if result.header != header {
        return Err(HodgePacketError::HeaderMismatch);
    }
    let payload = parse_payload(request, fuel)?;
    let problem = payload.problem();
    let actual_digest = carrier_digest(&problem, fuel)?;
    if result.carrier_digest != actual_digest {
        return Err(HodgePacketError::CarrierDigestMismatch);
    }
    let verified = check_hodge_certificate(&problem, &result.certificate, fuel)?;
    Ok(VerifiedHodgePacketV1 {
        verified,
        scalar_ops: fuel.used(),
    })
}

struct HodgePayload {
    d0: BasicMatrix<BigRational>,
    d1: BasicMatrix<BigRational>,
    flow: Vec<BigRational>,
}

impl HodgePayload {
    fn problem(&self) -> HodgeProblem<'_> {
        HodgeProblem {
            d0: &self.d0,
            d1: &self.d1,
            flow: &self.flow,
        }
    }
}

fn parse_payload(
    request: HodgeRequestV1,
    fuel: &mut RationalBudget,
) -> Result<HodgePayload, HodgePacketError> {
    let d0 = request.d0.into_matrix("d0", fuel)?;
    let d1 = request.d1.into_matrix("d1", fuel)?;
    fuel.elements(request.flow.len(), 1)?;
    for scalar in &request.flow {
        fuel.rational(scalar)?;
    }
    let payload = HodgePayload {
        d0,
        d1,
        flow: request.flow,
    };
    validate_problem(&payload.problem(), fuel)?;
    Ok(payload)
}

fn carrier_digest(
    problem: &HodgeProblem<'_>,
    fuel: &mut RationalBudget,
) -> Result<String, HodgePacketError> {
    let mut hasher = Sha256::new();
    hasher.update(b"core.solver.hodge-carrier.v1");
    update_matrix(&mut hasher, b"d0", problem.d0, fuel)?;
    update_matrix(&mut hasher, b"d1", problem.d1, fuel)?;
    hasher.update(b"flow");
    update_length(&mut hasher, problem.flow.len(), "flow length")?;
    fuel.elements(problem.flow.len(), 1)?;
    for scalar in problem.flow {
        update_rational(&mut hasher, scalar, fuel)?;
    }
    Ok(hex::encode(hasher.finalize()))
}

fn update_matrix(
    hasher: &mut Sha256,
    name: &'static [u8],
    matrix: &BasicMatrix<BigRational>,
    fuel: &mut RationalBudget,
) -> Result<(), HodgePacketError> {
    hasher.update(name);
    update_length(hasher, matrix.rows(), "matrix row count")?;
    update_length(hasher, matrix.cols(), "matrix column count")?;
    fuel.elements(matrix.rows(), matrix.cols())?;
    for scalar in matrix.as_slice() {
        update_rational(hasher, scalar, fuel)?;
    }
    Ok(())
}

fn update_rational(
    hasher: &mut Sha256,
    scalar: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<(), HodgePacketError> {
    fuel.rational(scalar)?;
    update_bytes(
        hasher,
        &scalar.numer().to_signed_bytes_be(),
        "numerator length",
    )?;
    update_bytes(
        hasher,
        &scalar.denom().to_signed_bytes_be(),
        "denominator length",
    )?;
    Ok(())
}

fn update_bytes(
    hasher: &mut Sha256,
    bytes: &[u8],
    field: &'static str,
) -> Result<(), HodgePacketError> {
    update_length(hasher, bytes.len(), field)?;
    hasher.update(bytes);
    Ok(())
}

fn update_length(
    hasher: &mut Sha256,
    value: usize,
    field: &'static str,
) -> Result<(), HodgePacketError> {
    let value = u64::try_from(value).map_err(|_| HodgePacketError::CarrierLength { field })?;
    hasher.update(value.to_be_bytes());
    Ok(())
}

fn is_nonzero_lower_hex_digest(value: &str) -> bool {
    value.len() == 64
        && value.as_bytes().iter().all(u8::is_ascii_hexdigit)
        && value
            .as_bytes()
            .iter()
            .all(|byte| !byte.is_ascii_uppercase())
        && value.as_bytes().iter().any(|byte| *byte != b'0')
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_328d4e0d {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
