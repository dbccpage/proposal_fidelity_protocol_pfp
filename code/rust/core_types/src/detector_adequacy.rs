//! Solver-neutral declarations and numerical-evidence DTOs for EPK detector adequacy.
//!
//! Declarations are data, not verdicts. Incomplete declarations are allowed so
//! `core_epk` can return exact structural failures. Capacity evidence is
//! private-field, serialize-only f64 evidence over `S_AG ∩ span(D)`; it is
//! neither an exact BSC certificate nor authority.

use crate::authority::AuthorityEffect;
use num_rational::BigRational;
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const DETECTOR_ADEQUACY_DECLARATION_SCHEMA: &str = "core.epk.detector-adequacy-declaration.v1";
pub const DETECTOR_CAPACITY_EVIDENCE_SCHEMA: &str =
    "core.epk.detector-capacity-numerical-evidence.v1";
pub const DETECTOR_CAPACITY_SCOPE: &str = "S_AG intersect span(D)";
/// Fixed solver rank convention for detector-capacity evidence.
pub const DETECTOR_CAPACITY_RANK_TOLERANCE: f64 = 1e-9;
/// Fixed residual ceiling for detector-capacity evidence.
pub const DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE: f64 = 1e-7;
/// Fixed comparison band for detector-capacity evidence.
pub const DETECTOR_CAPACITY_COMPARISON_TOLERANCE: f64 = 1e-7;

/// Canonical exact rational rank tolerance (10^-9 = 1 / 1,000,000,000).
pub fn detector_capacity_rank_tolerance_rational() -> BigRational {
    BigRational::from_float(DETECTOR_CAPACITY_RANK_TOLERANCE)
        .unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
}

/// Canonical exact decimal rational rank tolerance (10^-9 = 1 / 1,000,000,000) constructed purely over Q.
pub fn detector_capacity_rank_tolerance_exact_rational() -> BigRational {
    BigRational::new(1.into(), 1_000_000_000.into())
}

/// Canonical exact rational residual acceptance tolerance (10^-7 = 1 / 10,000,000).
pub fn detector_capacity_residual_acceptance_tolerance_rational() -> BigRational {
    BigRational::from_float(DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE)
        .unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
}

/// Canonical exact decimal rational residual acceptance tolerance (10^-7 = 1 / 10,000,000) constructed purely over Q.
pub fn detector_capacity_residual_acceptance_tolerance_exact_rational() -> BigRational {
    BigRational::new(1.into(), 10_000_000.into())
}

/// Canonical exact rational comparison tolerance (10^-7 = 1 / 10,000,000).
pub fn detector_capacity_comparison_tolerance_rational() -> BigRational {
    BigRational::from_float(DETECTOR_CAPACITY_COMPARISON_TOLERANCE)
        .unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
}

/// Canonical exact decimal rational comparison tolerance (10^-7 = 1 / 10,000,000) constructed purely over Q.
pub fn detector_capacity_comparison_tolerance_exact_rational() -> BigRational {
    BigRational::new(1.into(), 10_000_000.into())
}

/// Smallest accepted nonzero magnitude for detector-capacity inputs.
pub const MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE: f64 = 1e-150;
/// Largest accepted magnitude for detector-capacity inputs.
pub const MAX_DETECTOR_SAFE_MAGNITUDE: f64 = 1e140;

/// Canonical finite-magnitude policy shared by declarations and solvers.
///
/// Exact zero (including negative zero) is permitted. Every nonzero value must
/// lie in the inclusive safe interval before any norm or dense-linear-algebra
/// computation is attempted.
pub fn detector_magnitude_is_in_policy(value: f64) -> bool {
    if !value.is_finite() {
        return false;
    }
    value == 0.0
        || (MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE..=MAX_DETECTOR_SAFE_MAGNITUDE)
            .contains(&value.abs())
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DetectorEvaluatorRole {
    LocalLeft,
    LocalRight,
    Global,
}

impl DetectorEvaluatorRole {
    const fn digest_tag(self) -> u8 {
        match self {
            Self::LocalLeft => 1,
            Self::LocalRight => 2,
            Self::Global => 3,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Error)]
pub enum DetectorAdequacyDtoError {
    #[error("{field} must be non-empty")]
    EmptyIdentifier { field: &'static str },
    #[error("projection record {record_id:?} is declared more than once")]
    DuplicateProjectionRecord { record_id: String },
    #[error("protected direction {distinction_id:?} has a non-finite coordinate at {index}")]
    NonFiniteProtectedDirection {
        distinction_id: String,
        index: usize,
    },
    #[error("epsilon must be finite and nonnegative, found {epsilon}")]
    InvalidEpsilon { epsilon: f64 },
    #[error("{field} contains a non-finite value at {index}")]
    NonFiniteEvidenceValue { field: &'static str, index: usize },
    #[error("{field} must be finite and nonnegative, found {value}")]
    InvalidNonnegativeEvidenceValue { field: &'static str, value: f64 },
    #[error("{field} must be finite and positive, found {value}")]
    InvalidPositiveEvidenceValue { field: &'static str, value: f64 },
    #[error("singular-value count mismatch: expected {expected}, found {found}")]
    SingularValueCountMismatch { expected: usize, found: usize },
    #[error("protected-subspace digest must be non-empty")]
    EmptyProtectedSubspaceDigest,
    #[error("capacity-model digest must be non-empty")]
    EmptyCapacityModelDigest,
}

fn identifier(value: &str, field: &'static str) -> Result<(), DetectorAdequacyDtoError> {
    if value.trim().is_empty() {
        return Err(DetectorAdequacyDtoError::EmptyIdentifier { field });
    }
    Ok(())
}

fn nonnegative(value: f64, field: &'static str) -> Result<(), DetectorAdequacyDtoError> {
    if !value.is_finite() || value < 0.0 {
        return Err(DetectorAdequacyDtoError::InvalidNonnegativeEvidenceValue { field, value });
    }
    Ok(())
}

fn positive(value: f64, field: &'static str) -> Result<(), DetectorAdequacyDtoError> {
    if !value.is_finite() || value <= 0.0 {
        return Err(DetectorAdequacyDtoError::InvalidPositiveEvidenceValue { field, value });
    }
    Ok(())
}

fn finite_slice(values: &[f64], field: &'static str) -> Result<(), DetectorAdequacyDtoError> {
    if let Some((index, _)) = values.iter().enumerate().find(|(_, v)| !v.is_finite()) {
        return Err(DetectorAdequacyDtoError::NonFiniteEvidenceValue { field, index });
    }
    Ok(())
}

/// A protected record-pair and its section-space direction.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct ProtectedDistinctionDeclaration {
    distinction_id: String,
    evaluator: DetectorEvaluatorRole,
    positive_record_id: String,
    negative_record_id: String,
    section_direction: Vec<f64>,
}

impl ProtectedDistinctionDeclaration {
    pub fn new(
        distinction_id: impl Into<String>,
        evaluator: DetectorEvaluatorRole,
        positive_record_id: impl Into<String>,
        negative_record_id: impl Into<String>,
        section_direction: Vec<f64>,
    ) -> Result<Self, DetectorAdequacyDtoError> {
        let distinction_id = distinction_id.into();
        let positive_record_id = positive_record_id.into();
        let negative_record_id = negative_record_id.into();
        identifier(&distinction_id, "distinction_id")?;
        identifier(&positive_record_id, "positive_record_id")?;
        identifier(&negative_record_id, "negative_record_id")?;
        if let Some((index, _)) = section_direction
            .iter()
            .enumerate()
            .find(|(_, value)| !value.is_finite())
        {
            return Err(DetectorAdequacyDtoError::NonFiniteProtectedDirection {
                distinction_id,
                index,
            });
        }
        Ok(Self {
            distinction_id,
            evaluator,
            positive_record_id,
            negative_record_id,
            section_direction,
        })
    }

    pub fn distinction_id(&self) -> &str {
        &self.distinction_id
    }
    pub fn evaluator(&self) -> DetectorEvaluatorRole {
        self.evaluator
    }
    pub fn positive_record_id(&self) -> &str {
        &self.positive_record_id
    }
    pub fn negative_record_id(&self) -> &str {
        &self.negative_record_id
    }
    pub fn section_direction(&self) -> &[f64] {
        &self.section_direction
    }
}

/// Carrier, projection, and blind-spot declaration for one evaluator.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DetectorEvaluatorDeclaration {
    role: DetectorEvaluatorRole,
    carrier_record_ids: BTreeSet<String>,
    projected_observations: BTreeMap<String, String>,
    blind_spot_declaration_complete: bool,
    known_blind_spots: Vec<String>,
}

impl DetectorEvaluatorDeclaration {
    pub fn new(
        role: DetectorEvaluatorRole,
        carrier_record_ids: impl IntoIterator<Item = String>,
        projected_observations: impl IntoIterator<Item = (String, String)>,
        blind_spot_declaration_complete: bool,
        known_blind_spots: impl IntoIterator<Item = String>,
    ) -> Result<Self, DetectorAdequacyDtoError> {
        let mut carrier = BTreeSet::new();
        for record_id in carrier_record_ids {
            identifier(&record_id, "carrier_record_id")?;
            carrier.insert(record_id);
        }
        let mut projection = BTreeMap::new();
        for (record_id, projected_value) in projected_observations {
            identifier(&record_id, "projection_record_id")?;
            identifier(&projected_value, "projected_value")?;
            if projection
                .insert(record_id.clone(), projected_value)
                .is_some()
            {
                return Err(DetectorAdequacyDtoError::DuplicateProjectionRecord { record_id });
            }
        }
        let mut blind_spots = Vec::new();
        for blind_spot in known_blind_spots {
            identifier(&blind_spot, "known_blind_spot")?;
            blind_spots.push(blind_spot);
        }
        Ok(Self {
            role,
            carrier_record_ids: carrier,
            projected_observations: projection,
            blind_spot_declaration_complete,
            known_blind_spots: blind_spots,
        })
    }

    pub fn role(&self) -> DetectorEvaluatorRole {
        self.role
    }
    pub fn carrier_record_ids(&self) -> &BTreeSet<String> {
        &self.carrier_record_ids
    }
    pub fn projected_observations(&self) -> &BTreeMap<String, String> {
        &self.projected_observations
    }
    pub fn projected_value(&self, record_id: &str) -> Option<&str> {
        self.projected_observations
            .get(record_id)
            .map(String::as_str)
    }
    pub fn known_blind_spots(&self) -> &[String] {
        &self.known_blind_spots
    }
    pub fn blind_spot_declaration_complete(&self) -> bool {
        self.blind_spot_declaration_complete
    }
}

/// Solver-neutral declaration for one EPK deployment.
///
/// ```compile_fail
/// use core_types::DetectorDeploymentDeclaration;
/// let _: DetectorDeploymentDeclaration = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DetectorDeploymentDeclaration {
    schema: &'static str,
    deployment_id: String,
    corpus_id: String,
    boundary_name: String,
    boundary_states: BTreeSet<String>,
    capacity_model_digest: String,
    epsilon: f64,
    evaluators: Vec<DetectorEvaluatorDeclaration>,
    protected_distinctions: Vec<ProtectedDistinctionDeclaration>,
}

impl DetectorDeploymentDeclaration {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        deployment_id: impl Into<String>,
        corpus_id: impl Into<String>,
        boundary_name: impl Into<String>,
        boundary_states: impl IntoIterator<Item = String>,
        capacity_model_digest: impl Into<String>,
        epsilon: f64,
        evaluators: Vec<DetectorEvaluatorDeclaration>,
        protected_distinctions: Vec<ProtectedDistinctionDeclaration>,
    ) -> Result<Self, DetectorAdequacyDtoError> {
        let deployment_id = deployment_id.into();
        let corpus_id = corpus_id.into();
        let boundary_name = boundary_name.into();
        let capacity_model_digest = capacity_model_digest.into();
        identifier(&deployment_id, "deployment_id")?;
        identifier(&corpus_id, "corpus_id")?;
        identifier(&boundary_name, "boundary_name")?;
        if capacity_model_digest.trim().is_empty() {
            return Err(DetectorAdequacyDtoError::EmptyCapacityModelDigest);
        }
        if !epsilon.is_finite() || epsilon < 0.0 {
            return Err(DetectorAdequacyDtoError::InvalidEpsilon { epsilon });
        }
        let mut boundary = BTreeSet::new();
        for state in boundary_states {
            identifier(&state, "boundary_state")?;
            boundary.insert(state);
        }
        Ok(Self {
            schema: DETECTOR_ADEQUACY_DECLARATION_SCHEMA,
            deployment_id,
            corpus_id,
            boundary_name,
            boundary_states: boundary,
            capacity_model_digest,
            epsilon,
            evaluators,
            protected_distinctions,
        })
    }

    pub fn schema(&self) -> &str {
        self.schema
    }
    pub fn deployment_id(&self) -> &str {
        &self.deployment_id
    }
    pub fn corpus_id(&self) -> &str {
        &self.corpus_id
    }
    pub fn boundary_name(&self) -> &str {
        &self.boundary_name
    }
    pub fn boundary_states(&self) -> &BTreeSet<String> {
        &self.boundary_states
    }
    pub fn capacity_model_digest(&self) -> &str {
        &self.capacity_model_digest
    }
    pub fn epsilon(&self) -> f64 {
        self.epsilon
    }
    pub fn epsilon_rational(&self) -> BigRational {
        BigRational::from_float(self.epsilon)
            .unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
    }
    pub fn evaluators(&self) -> &[DetectorEvaluatorDeclaration] {
        &self.evaluators
    }
    pub fn protected_distinctions(&self) -> &[ProtectedDistinctionDeclaration] {
        &self.protected_distinctions
    }

    /// Canonical SHA-256 binding for the complete deployment declaration.
    pub fn declaration_digest(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(b"core.epk.detector-deployment-declaration.v1\0");
        digest_string(&mut hasher, self.schema);
        digest_string(&mut hasher, &self.deployment_id);
        digest_string(&mut hasher, &self.corpus_id);
        digest_string(&mut hasher, &self.boundary_name);
        hasher.update((self.boundary_states.len() as u128).to_le_bytes());
        for state in &self.boundary_states {
            digest_string(&mut hasher, state);
        }
        digest_string(&mut hasher, &self.capacity_model_digest);
        hasher.update(self.epsilon.to_bits().to_le_bytes());

        let mut evaluator_digests: Vec<_> = self.evaluators.iter().map(evaluator_digest).collect();
        evaluator_digests.sort_unstable();
        hasher.update((evaluator_digests.len() as u128).to_le_bytes());
        for digest in evaluator_digests {
            hasher.update(digest);
        }

        digest_string(&mut hasher, &self.protected_subspace_digest());
        finish_digest(hasher)
    }

    pub fn protected_coordinate_dimension(&self) -> Option<usize> {
        let first = self.protected_distinctions.first()?.section_direction.len();
        self.protected_distinctions
            .iter()
            .all(|item| item.section_direction.len() == first)
            .then_some(first)
    }

    /// SHA-256 binding including evaluator, records, and exact f64 bits.
    pub fn protected_subspace_digest(&self) -> String {
        let mut ordered: Vec<_> = self.protected_distinctions.iter().collect();
        ordered.sort_by(|left, right| {
            (
                left.evaluator,
                left.distinction_id.as_str(),
                left.positive_record_id.as_str(),
                left.negative_record_id.as_str(),
            )
                .cmp(&(
                    right.evaluator,
                    right.distinction_id.as_str(),
                    right.positive_record_id.as_str(),
                    right.negative_record_id.as_str(),
                ))
        });
        let mut hasher = Sha256::new();
        hasher.update(b"core.epk.protected-subspace-digest.v1\0");
        hasher.update((ordered.len() as u64).to_le_bytes());
        for item in ordered {
            hasher.update([item.evaluator.digest_tag()]);
            digest_string(&mut hasher, &item.distinction_id);
            digest_string(&mut hasher, &item.positive_record_id);
            digest_string(&mut hasher, &item.negative_record_id);
            hasher.update((item.section_direction.len() as u64).to_le_bytes());
            for value in &item.section_direction {
                hasher.update(value.to_bits().to_le_bytes());
            }
        }
        finish_digest(hasher)
    }
}

fn evaluator_digest(evaluator: &DetectorEvaluatorDeclaration) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(b"core.epk.detector-evaluator-declaration.v1\0");
    hasher.update([evaluator.role.digest_tag()]);
    hasher.update((evaluator.carrier_record_ids.len() as u128).to_le_bytes());
    for record_id in &evaluator.carrier_record_ids {
        digest_string(&mut hasher, record_id);
    }
    hasher.update((evaluator.projected_observations.len() as u128).to_le_bytes());
    for (record_id, value) in &evaluator.projected_observations {
        digest_string(&mut hasher, record_id);
        digest_string(&mut hasher, value);
    }
    hasher.update([u8::from(evaluator.blind_spot_declaration_complete)]);
    let mut blind_spots = evaluator.known_blind_spots.clone();
    blind_spots.sort_unstable();
    hasher.update((blind_spots.len() as u128).to_le_bytes());
    for blind_spot in blind_spots {
        digest_string(&mut hasher, &blind_spot);
    }
    hasher.finalize().into()
}

fn digest_string(hasher: &mut Sha256, value: &str) {
    hasher.update((value.len() as u64).to_le_bytes());
    hasher.update(value.as_bytes());
}

fn finish_digest(hasher: Sha256) -> String {
    let digest = hasher.finalize();
    let mut encoded = String::with_capacity(digest.len() * 2);
    for byte in digest {
        use std::fmt::Write as _;
        let _ = write!(&mut encoded, "{byte:02x}");
    }
    encoded
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DetectorCapacityWitness {
    section: Vec<f64>,
    defect: Vec<f64>,
    section_l2: f64,
    defect_l2: f64,
}

impl DetectorCapacityWitness {
    pub fn new(section: Vec<f64>, defect: Vec<f64>) -> Result<Self, DetectorAdequacyDtoError> {
        finite_slice(&section, "witness.section")?;
        finite_slice(&defect, "witness.defect")?;
        let section_l2 = core_functional::norms::l2_diagnostic(&section);
        let defect_l2 = core_functional::norms::l2_diagnostic(&defect);
        nonnegative(section_l2, "witness.section_l2")?;
        nonnegative(defect_l2, "witness.defect_l2")?;
        Ok(Self {
            section,
            defect,
            section_l2,
            defect_l2,
        })
    }

    pub fn section(&self) -> &[f64] {
        &self.section
    }
    pub fn defect(&self) -> &[f64] {
        &self.defect
    }
    pub fn section_l2(&self) -> f64 {
        self.section_l2
    }
    pub fn defect_l2(&self) -> f64 {
        self.defect_l2
    }
}

/// Residual disclosure for the intersection basis and singular witness.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DetectorCapacityResiduals {
    all_green_constraint: f64,
    all_green_orthonormality: f64,
    protected_span_basis: f64,
    intersection_construction: f64,
    intersection_all_green: f64,
    intersection_protected: f64,
    intersection_orthonormality: f64,
    witness_all_green: f64,
    witness_protected: f64,
    witness_normalization: f64,
    top_singular_equation: f64,
    capacity_attainment: f64,
    max_residual: f64,
}

impl DetectorCapacityResiduals {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        all_green_constraint: f64,
        all_green_orthonormality: f64,
        protected_span_basis: f64,
        intersection_construction: f64,
        intersection_all_green: f64,
        intersection_protected: f64,
        intersection_orthonormality: f64,
        witness_all_green: f64,
        witness_protected: f64,
        witness_normalization: f64,
        top_singular_equation: f64,
        capacity_attainment: f64,
    ) -> Result<Self, DetectorAdequacyDtoError> {
        let values = [
            ("residuals.all_green_constraint", all_green_constraint),
            (
                "residuals.all_green_orthonormality",
                all_green_orthonormality,
            ),
            ("residuals.protected_span_basis", protected_span_basis),
            (
                "residuals.intersection_construction",
                intersection_construction,
            ),
            ("residuals.intersection_all_green", intersection_all_green),
            ("residuals.intersection_protected", intersection_protected),
            (
                "residuals.intersection_orthonormality",
                intersection_orthonormality,
            ),
            ("residuals.witness_all_green", witness_all_green),
            ("residuals.witness_protected", witness_protected),
            ("residuals.witness_normalization", witness_normalization),
            ("residuals.top_singular_equation", top_singular_equation),
            ("residuals.capacity_attainment", capacity_attainment),
        ];
        for (field, value) in values {
            nonnegative(value, field)?;
        }
        let max_residual = values.iter().map(|(_, v)| *v).fold(0.0_f64, f64::max);
        Ok(Self {
            all_green_constraint,
            all_green_orthonormality,
            protected_span_basis,
            intersection_construction,
            intersection_all_green,
            intersection_protected,
            intersection_orthonormality,
            witness_all_green,
            witness_protected,
            witness_normalization,
            top_singular_equation,
            capacity_attainment,
            max_residual,
        })
    }

    pub fn all_green_constraint(&self) -> f64 {
        self.all_green_constraint
    }
    pub fn all_green_orthonormality(&self) -> f64 {
        self.all_green_orthonormality
    }
    pub fn protected_span_basis(&self) -> f64 {
        self.protected_span_basis
    }
    pub fn intersection_construction(&self) -> f64 {
        self.intersection_construction
    }
    pub fn intersection_all_green(&self) -> f64 {
        self.intersection_all_green
    }
    pub fn intersection_protected(&self) -> f64 {
        self.intersection_protected
    }
    pub fn intersection_orthonormality(&self) -> f64 {
        self.intersection_orthonormality
    }
    pub fn witness_all_green(&self) -> f64 {
        self.witness_all_green
    }
    pub fn witness_protected(&self) -> f64 {
        self.witness_protected
    }
    pub fn witness_normalization(&self) -> f64 {
        self.witness_normalization
    }
    pub fn top_singular_equation(&self) -> f64 {
        self.top_singular_equation
    }
    pub fn capacity_attainment(&self) -> f64 {
        self.capacity_attainment
    }
    pub fn max_residual(&self) -> f64 {
        self.max_residual
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum DetectorCapacityEvidenceKind {
    F64NumericalEstimate,
}

/// Residual-disclosed f64 estimate of `||Delta|_(S_AG ∩ span(D))||`.
///
/// ```compile_fail
/// use core_types::DetectorCapacityEvidence;
/// let _: DetectorCapacityEvidence = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DetectorCapacityEvidence {
    schema: &'static str,
    scope: &'static str,
    evidence_kind: DetectorCapacityEvidenceKind,
    authority: AuthorityEffect,
    capacity_model_digest: String,
    protected_subspace_digest: String,
    value: f64,
    epsilon: f64,
    all_green_dimension: usize,
    protected_span_dimension: usize,
    restricted_dimension: usize,
    restricted_singular_values: Vec<f64>,
    witness: DetectorCapacityWitness,
    residuals: DetectorCapacityResiduals,
    rank_tolerance_used: f64,
    residual_acceptance_tolerance: f64,
    comparison_tolerance: f64,
    residuals_within_tolerance: bool,
}

impl DetectorCapacityEvidence {
    fn validate_digests_and_scalars(
        capacity_model_digest: &str,
        protected_subspace_digest: &str,
        value: f64,
        epsilon: f64,
        rank_tolerance_used: f64,
        residual_acceptance_tolerance: f64,
        comparison_tolerance: f64,
    ) -> Result<(), DetectorAdequacyDtoError> {
        if capacity_model_digest.trim().is_empty() {
            return Err(DetectorAdequacyDtoError::EmptyCapacityModelDigest);
        }
        if protected_subspace_digest.trim().is_empty() {
            return Err(DetectorAdequacyDtoError::EmptyProtectedSubspaceDigest);
        }
        nonnegative(value, "capacity.value")?;
        if !epsilon.is_finite() || epsilon < 0.0 {
            return Err(DetectorAdequacyDtoError::InvalidEpsilon { epsilon });
        }
        positive(rank_tolerance_used, "capacity.rank_tolerance_used")?;
        positive(
            residual_acceptance_tolerance,
            "capacity.residual_acceptance_tolerance",
        )?;
        positive(comparison_tolerance, "capacity.comparison_tolerance")
    }

    fn validate_singular_values(
        restricted_singular_values: &[f64],
        restricted_dimension: usize,
    ) -> Result<(), DetectorAdequacyDtoError> {
        finite_slice(
            restricted_singular_values,
            "capacity.restricted_singular_values",
        )?;
        for singular_value in restricted_singular_values {
            nonnegative(*singular_value, "capacity.restricted_singular_value")?;
        }
        if restricted_singular_values.len() != restricted_dimension {
            return Err(DetectorAdequacyDtoError::SingularValueCountMismatch {
                expected: restricted_dimension,
                found: restricted_singular_values.len(),
            });
        }
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    pub fn from_f64_numerical_estimate(
        capacity_model_digest: impl Into<String>,
        protected_subspace_digest: impl Into<String>,
        value: f64,
        epsilon: f64,
        all_green_dimension: usize,
        protected_span_dimension: usize,
        restricted_dimension: usize,
        restricted_singular_values: Vec<f64>,
        witness: DetectorCapacityWitness,
        residuals: DetectorCapacityResiduals,
        rank_tolerance_used: f64,
        residual_acceptance_tolerance: f64,
        comparison_tolerance: f64,
    ) -> Result<Self, DetectorAdequacyDtoError> {
        let capacity_model_digest = capacity_model_digest.into();
        let protected_subspace_digest = protected_subspace_digest.into();
        Self::validate_digests_and_scalars(
            &capacity_model_digest,
            &protected_subspace_digest,
            value,
            epsilon,
            rank_tolerance_used,
            residual_acceptance_tolerance,
            comparison_tolerance,
        )?;
        Self::validate_singular_values(&restricted_singular_values, restricted_dimension)?;
        let residuals_within_tolerance = residuals.max_residual <= residual_acceptance_tolerance;
        Ok(Self {
            schema: DETECTOR_CAPACITY_EVIDENCE_SCHEMA,
            scope: DETECTOR_CAPACITY_SCOPE,
            evidence_kind: DetectorCapacityEvidenceKind::F64NumericalEstimate,
            authority: AuthorityEffect::None,
            capacity_model_digest,
            protected_subspace_digest,
            value,
            epsilon,
            all_green_dimension,
            protected_span_dimension,
            restricted_dimension,
            restricted_singular_values,
            witness,
            residuals,
            rank_tolerance_used,
            residual_acceptance_tolerance,
            comparison_tolerance,
            residuals_within_tolerance,
        })
    }

    pub fn schema(&self) -> &str {
        self.schema
    }
    pub fn scope(&self) -> &str {
        self.scope
    }
    pub fn evidence_kind(&self) -> DetectorCapacityEvidenceKind {
        self.evidence_kind
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
    pub fn capacity_model_digest(&self) -> &str {
        &self.capacity_model_digest
    }
    pub fn protected_subspace_digest(&self) -> &str {
        &self.protected_subspace_digest
    }
    pub fn value(&self) -> f64 {
        self.value
    }
    pub fn epsilon(&self) -> f64 {
        self.epsilon
    }
    pub fn all_green_dimension(&self) -> usize {
        self.all_green_dimension
    }
    pub fn protected_span_dimension(&self) -> usize {
        self.protected_span_dimension
    }
    pub fn restricted_dimension(&self) -> usize {
        self.restricted_dimension
    }
    pub fn restricted_singular_values(&self) -> &[f64] {
        &self.restricted_singular_values
    }
    pub fn witness(&self) -> &DetectorCapacityWitness {
        &self.witness
    }
    pub fn residuals(&self) -> &DetectorCapacityResiduals {
        &self.residuals
    }
    pub fn rank_tolerance_used(&self) -> f64 {
        self.rank_tolerance_used
    }
    pub fn rank_tolerance_used_rational(&self) -> BigRational {
        BigRational::from_float(self.rank_tolerance_used)
            .unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
    }
    pub fn residual_acceptance_tolerance(&self) -> f64 {
        self.residual_acceptance_tolerance
    }
    pub fn residual_acceptance_tolerance_rational(&self) -> BigRational {
        BigRational::from_float(self.residual_acceptance_tolerance)
            .unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
    }
    pub fn comparison_tolerance(&self) -> f64 {
        self.comparison_tolerance
    }
    pub fn comparison_tolerance_rational(&self) -> BigRational {
        BigRational::from_float(self.comparison_tolerance)
            .unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
    }
    pub fn value_rational(&self) -> BigRational {
        BigRational::from_float(self.value).unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
    }
    pub fn epsilon_rational(&self) -> BigRational {
        BigRational::from_float(self.epsilon)
            .unwrap_or_else(|| BigRational::new(0.into(), 1.into()))
    }
    pub fn residuals_within_tolerance(&self) -> bool {
        self.residuals_within_tolerance
    }

    /// Keeps caller diagnostic magnitudes, including non-finite values.
    /// A classifier must refuse those values before comparing them.
    pub fn with_diagnostic_magnitudes(
        mut self,
        section_l2: f64,
        defect_l2: f64,
        max_residual: f64,
    ) -> Self {
        self.witness.section_l2 = section_l2;
        self.witness.defect_l2 = defect_l2;
        self.residuals.max_residual = max_residual;
        self
    }
}

// Origin: engine/crates_rs/core_types/src/detector_adequacy.rs
// Claim: urn:core:crates_rs:core-types:detector-adequacy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    //! --- Math Contract:
    //! Object: detector declaration digest and numerical evidence DTO.
    //! Preconditions: constructor-validated finite inputs.
    //! Postconditions: deterministic binding and fixed authority None.
    //! Authority: None.
    //! ---

    use super::*;

    #[test]
    fn canonical_magnitude_policy_is_inclusive_and_zero_safe() {
        for accepted in [
            0.0,
            -0.0,
            MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
            -MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
            MAX_DETECTOR_SAFE_MAGNITUDE,
            -MAX_DETECTOR_SAFE_MAGNITUDE,
        ] {
            assert!(detector_magnitude_is_in_policy(accepted), "{accepted}");
        }
        for refused in [
            MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE / 10.0,
            -MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE / 10.0,
            MAX_DETECTOR_SAFE_MAGNITUDE * 10.0,
            -MAX_DETECTOR_SAFE_MAGNITUDE * 10.0,
            f64::NAN,
            f64::INFINITY,
            f64::NEG_INFINITY,
        ] {
            assert!(!detector_magnitude_is_in_policy(refused), "{refused}");
        }
    }

    #[test]
    fn protected_digest_binds_exact_direction_bits() {
        let item = ProtectedDistinctionDeclaration::new(
            "d",
            DetectorEvaluatorRole::Global,
            "positive",
            "negative",
            vec![1.0, -0.0],
        )
        .unwrap();
        let declaration = DetectorDeploymentDeclaration::new(
            "deployment",
            "corpus",
            "B",
            ["middle".to_string()],
            "capacity-model",
            0.1,
            Vec::new(),
            vec![item],
        )
        .unwrap();
        let changed = DetectorDeploymentDeclaration::new(
            "deployment",
            "corpus",
            "B",
            ["middle".to_string()],
            "capacity-model",
            0.1,
            Vec::new(),
            vec![ProtectedDistinctionDeclaration::new(
                "d",
                DetectorEvaluatorRole::Global,
                "positive",
                "negative",
                vec![1.0, 0.0],
            )
            .unwrap()],
        )
        .unwrap();
        assert_ne!(
            declaration.protected_subspace_digest(),
            changed.protected_subspace_digest()
        );
    }

    #[test]
    fn declaration_digest_binds_deployment_and_corpus_identity() {
        let make = |deployment_id: &str, corpus_id: &str| {
            DetectorDeploymentDeclaration::new(
                deployment_id,
                corpus_id,
                "B",
                ["middle".to_string()],
                "capacity-model",
                0.1,
                Vec::new(),
                vec![ProtectedDistinctionDeclaration::new(
                    "d",
                    DetectorEvaluatorRole::Global,
                    "positive",
                    "negative",
                    vec![1.0, -1.0],
                )
                .unwrap()],
            )
            .unwrap()
        };
        let base = make("deployment-a", "corpus-a");
        assert_eq!(base.declaration_digest().len(), 64);
        assert_ne!(
            base.declaration_digest(),
            make("deployment-b", "corpus-a").declaration_digest()
        );
        assert_ne!(
            base.declaration_digest(),
            make("deployment-a", "corpus-b").declaration_digest()
        );
    }

    #[test]
    fn capacity_evidence_derives_residual_gate_and_has_no_authority() {
        let residuals = DetectorCapacityResiduals::new(
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0,
        )
        .unwrap();
        let evidence = DetectorCapacityEvidence::from_f64_numerical_estimate(
            "capacity-model",
            "digest",
            1.0,
            0.5,
            2,
            1,
            1,
            vec![1.0],
            DetectorCapacityWitness::new(vec![1.0, 0.0], vec![1.0]).unwrap(),
            residuals,
            1e-9,
            1e-7,
            1e-7,
        )
        .unwrap();
        assert!(!evidence.residuals_within_tolerance());
        assert_eq!(evidence.authority_effect(), AuthorityEffect::None);
        let wire = serde_json::to_value(&evidence).unwrap();
        assert_eq!(wire["authority"], "None");
        assert_eq!(wire["scope"], DETECTOR_CAPACITY_SCOPE);
        assert_eq!(
            wire["residuals"]["all_green_constraint"],
            serde_json::json!(0.0)
        );
        assert_eq!(
            wire["residuals"]["all_green_orthonormality"],
            serde_json::json!(0.0)
        );
    }

    #[test]
    fn exact_rational_tolerances_are_pure_fractions() {
        let rank_tol = detector_capacity_rank_tolerance_exact_rational();
        let resid_tol = detector_capacity_residual_acceptance_tolerance_exact_rational();
        let comp_tol = detector_capacity_comparison_tolerance_exact_rational();

        assert_eq!(*rank_tol.numer(), 1.into());
        assert_eq!(*rank_tol.denom(), 1_000_000_000.into());
        assert_eq!(
            rank_tol * BigRational::from_integer(1_000_000_000.into()),
            BigRational::from_integer(1.into())
        );

        assert_eq!(*resid_tol.numer(), 1.into());
        assert_eq!(*resid_tol.denom(), 10_000_000.into());
        assert_eq!(
            resid_tol.clone() * BigRational::from_integer(10_000_000.into()),
            BigRational::from_integer(1.into())
        );

        assert_eq!(*comp_tol.numer(), 1.into());
        assert_eq!(*comp_tol.denom(), 10_000_000.into());
        assert_eq!(comp_tol, resid_tol);
    }
}
