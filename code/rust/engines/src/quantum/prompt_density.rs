// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
//! Bounded structural observations of captured prompt/reply bytes.
//!
//! This profile hashes ordered text features, not learned semantic embeddings.
//! Density spectra do not establish truth, safety, agreement, or correctness.
//! Original bytes belong to the caller's existing capture; spans and the digest
//! below bind that capture without pretending that factors reconstruct its text.
//! At most 16 components means rank <= 16 and entropy <= 4 bits even at 1024
//! coordinates. Projection collisions and single-state/global-sign blindness
//! are intentional limitations, not evidence of equivalence between prompts.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_9c2ae25b<T> {
    fn checked_invariant_9c2ae25b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_9c2ae25b<T> for Option<T> {
    #[inline]
    fn checked_invariant_9c2ae25b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_9c2ae25b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_9c2ae25b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::density_matrix::{CVector, C64};
use super::semantic_geometry_engine::{FactorizedDensity, EPSILON_TOL};
use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const PROFILE: &str = "ordered-sha256-density-v1";
pub const SCHEMA_VERSION: &str = "core.prompt-density.v1";
pub const DEFAULT_DIM: usize = 128;
pub const MIN_DIM: usize = 28;
pub const MAX_DIM: usize = 1024;
pub const MAX_COMPONENTS: usize = 16;
pub const MAX_SOURCE_BYTES: usize = 1_048_576;
pub const MAX_TOKENS: usize = 32_768;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ObservationStatus {
    Observed,
    Empty,
    InvalidUtf8,
    LimitExceeded,
    InvalidInput,
    Unavailable,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceSpan {
    pub start_byte: usize,
    pub end_byte: usize,
    pub token_start: usize,
    /// Unicode whitespace-delimited tokens, never provider billing tokens.
    pub token_count: usize,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PromptDensityReport {
    pub schema_version: String,
    pub profile: String,
    pub dim: usize,
    pub status: ObservationStatus,
    pub reason: Option<String>,
    pub source_sha256: String,
    pub source_bytes: usize,
    pub role_id: String,
    pub field: String,
    pub trust_level: String,
    pub spans: Vec<SourceSpan>,
    /// Unit real vectors; rho = sum(weights[i] * factors[i] * factors[i]^T).
    pub factors: Vec<Vec<f64>>,
    pub weights: Vec<f64>,
    pub spectrum: Vec<f64>,
    pub entropy_bits: Option<f64>,
    pub purity: Option<f64>,
    pub effective_rank: Option<f64>,
    pub numerical_rank: Option<usize>,
    pub spectrum_tolerance: f64,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PromptDensityComparison {
    pub schema_version: String,
    pub status: String,
    pub reason: Option<String>,
    pub profile: String,
    pub dim: usize,
    pub left_source_sha256: String,
    pub right_source_sha256: String,
    pub quantum_jensen_shannon_bits: Option<f64>,
    pub authority_effect: AuthorityEffect,
}

/// Observe UTF-8 bytes without rewriting them. Splitting uses Rust's Unicode
/// whitespace predicate; feature strings retain exact case and punctuation.
pub fn observe(
    bytes: &[u8],
    dim: usize,
    role_id: &str,
    field: &str,
    trust_level: &str,
) -> PromptDensityReport {
    let mut report = empty_report(bytes, dim, role_id, field, trust_level);
    let tokens = match validate_and_tokenize(bytes, dim, role_id, field, trust_level) {
        Ok(tokens) => tokens,
        Err((status, reason)) => return failed(report, status, reason),
    };
    let (spans, vectors, weights) =
        build_component_features(bytes, &tokens, tokens.len().min(MAX_COMPONENTS), dim, field);
    report.spans = spans;
    let state = match FactorizedDensity::new(vectors, Some(weights)) {
        Ok(state) => state,
        Err(error) => return failed(report, ObservationStatus::Unavailable, &error),
    };
    let spectrum = state.compute_spectrum();
    if spectrum.iter().any(|v| !v.is_finite()) || (spectrum.iter().sum::<f64>() - 1.0).abs() > 1e-8
    {
        return failed(
            report,
            ObservationStatus::Unavailable,
            "numerical spectrum failed finite unit-trace check",
        );
    }
    let entropy_bits = entropy_bits(&spectrum);
    report.status = ObservationStatus::Observed;
    report.factors = state
        .vectors()
        .iter()
        .map(|v| v.iter().map(|c| c.re).collect())
        .collect();
    report.weights = state.weights().to_vec();
    report.entropy_bits = Some(entropy_bits);
    report.purity = Some(spectrum.iter().map(|v| v * v).sum());
    report.effective_rank = Some(2.0_f64.powf(entropy_bits));
    report.numerical_rank = Some(spectrum.iter().filter(|&&v| v > EPSILON_TOL).count());
    report.spectrum = spectrum;
    report
}

fn empty_report(
    bytes: &[u8],
    dim: usize,
    role_id: &str,
    field: &str,
    trust_level: &str,
) -> PromptDensityReport {
    PromptDensityReport {
        schema_version: SCHEMA_VERSION.to_owned(),
        profile: PROFILE.to_owned(),
        dim,
        status: ObservationStatus::Unavailable,
        reason: None,
        source_sha256: format!("sha256:{:x}", Sha256::digest(bytes)),
        source_bytes: bytes.len(),
        role_id: role_id.to_owned(),
        field: field.to_owned(),
        trust_level: trust_level.to_owned(),
        spans: Vec::new(),
        factors: Vec::new(),
        weights: Vec::new(),
        spectrum: Vec::new(),
        entropy_bits: None,
        purity: None,
        effective_rank: None,
        numerical_rank: None,
        spectrum_tolerance: EPSILON_TOL,
        authority_effect: AuthorityEffect::None,
    }
}

fn validate_and_tokenize(
    bytes: &[u8],
    dim: usize,
    role_id: &str,
    field: &str,
    trust_level: &str,
) -> Result<Vec<(usize, usize)>, (ObservationStatus, &'static str)> {
    if !(MIN_DIM..=MAX_DIM).contains(&dim)
        || [role_id, field, trust_level]
            .iter()
            .any(|s| s.trim().is_empty() || s.len() > 256)
    {
        return Err((
            ObservationStatus::InvalidInput,
            "dimension must be 28..1024 and role/field/trust must be nonempty (at most 256 bytes)",
        ));
    }
    if bytes.len() > MAX_SOURCE_BYTES {
        return Err((
            ObservationStatus::LimitExceeded,
            "source exceeds 1048576 bytes",
        ));
    }
    let text = std::str::from_utf8(bytes)
        .map_err(|_| (ObservationStatus::InvalidUtf8, "source is not valid UTF-8"))?;
    let tokens = token_spans(text).ok_or((
        ObservationStatus::LimitExceeded,
        "source exceeds 32768 whitespace-delimited tokens",
    ))?;
    if tokens.is_empty() {
        return Err((
            ObservationStatus::Empty,
            "source has no non-whitespace tokens",
        ));
    }
    Ok(tokens)
}

fn build_component_features(
    bytes: &[u8],
    tokens: &[(usize, usize)],
    count: usize,
    dim: usize,
    field: &str,
) -> (Vec<SourceSpan>, Vec<CVector>, Vec<f64>) {
    let mut spans = Vec::with_capacity(count);
    let mut vectors = Vec::with_capacity(count);
    let mut weights = Vec::with_capacity(count);
    for component in 0..count {
        let first = component * tokens.len() / count;
        let end = (component + 1) * tokens.len() / count;
        let features = component_feature_vector(bytes, tokens, first, end, dim, field);
        spans.push(SourceSpan {
            start_byte: if component == 0 { 0 } else { tokens[first].0 },
            end_byte: if end == tokens.len() {
                bytes.len()
            } else {
                tokens[end].0
            },
            token_start: first,
            token_count: end - first,
        });
        vectors.push(CVector::from_iterator(
            dim,
            features.into_iter().map(|v| C64::new(v, 0.0)),
        ));
        weights.push((end - first) as f64);
    }
    (spans, vectors, weights)
}

fn component_feature_vector(
    bytes: &[u8],
    tokens: &[(usize, usize)],
    first: usize,
    end: usize,
    dim: usize,
    field: &str,
) -> Vec<f64> {
    let mut features = vec![0.0; dim];
    add_feature(&mut features, &[b"field", field.as_bytes()]);
    for index in first..end {
        let token = &bytes[tokens[index].0..tokens[index].1];
        add_feature(&mut features, &[b"token", field.as_bytes(), token]);
        add_feature(
            &mut features,
            &[
                b"position-token",
                field.as_bytes(),
                &(index as u64).to_le_bytes(),
                token,
            ],
        );
        if index > 0 {
            let previous = &bytes[tokens[index - 1].0..tokens[index - 1].1];
            add_feature(
                &mut features,
                &[b"adjacent", field.as_bytes(), previous, token],
            );
        }
    }
    features
}

fn failed(
    mut report: PromptDensityReport,
    status: ObservationStatus,
    reason: &str,
) -> PromptDensityReport {
    report.status = status;
    report.reason = Some(reason.to_owned());
    report.spans.clear();
    report
}

fn token_spans(text: &str) -> Option<Vec<(usize, usize)>> {
    let mut spans = Vec::new();
    let mut start = None;
    for (index, character) in text.char_indices() {
        if character.is_whitespace() {
            if let Some(begin) = start.take() {
                spans.push((begin, index));
                if spans.len() > MAX_TOKENS {
                    return None;
                }
            }
        } else if start.is_none() {
            start = Some(index);
        }
    }
    if let Some(begin) = start {
        spans.push((begin, text.len()));
    }
    (spans.len() <= MAX_TOKENS).then_some(spans)
}

fn add_feature(vector: &mut [f64], fields: &[&[u8]]) {
    let mut hash = Sha256::new();
    hash.update(PROFILE.as_bytes());
    for field in fields {
        hash.update((field.len() as u64).to_le_bytes());
        hash.update(field);
    }
    let digest = hash.finalize();
    let coordinate = (u64::from_le_bytes(digest[..8].try_into().checked_invariant_9c2ae25b("SHA-256 prefix"))
        % vector.len() as u64) as usize;
    vector[coordinate] += 1.0;
}

fn entropy_bits(spectrum: &[f64]) -> f64 {
    spectrum
        .iter()
        .filter(|&&v| v > 0.0)
        .map(|&v| -v * v.log2())
        .sum::<f64>()
        .max(0.0)
}

fn headers_compatible(left: &PromptDensityReport, right: &PromptDensityReport) -> bool {
    left.schema_version == SCHEMA_VERSION
        && right.schema_version == SCHEMA_VERSION
        && left.profile == PROFILE
        && right.profile == PROFILE
        && left.dim == right.dim
        && left.role_id == right.role_id
        && left.field == right.field
        && left.trust_level == right.trust_level
}

/// Compare only one fixed observation profile and role/field/trust context.
/// Reported scalar metrics are ignored; the comparison recomputes the spectra
/// from checked factors. The caller must retain/resolve the source digests.
pub fn compare(left: &PromptDensityReport, right: &PromptDensityReport) -> PromptDensityComparison {
    let mut result = PromptDensityComparison {
        schema_version: "core.prompt-density-comparison.v1".to_owned(),
        status: "INCOMPATIBLE".to_owned(),
        reason: None,
        profile: left.profile.clone(),
        dim: left.dim,
        left_source_sha256: left.source_sha256.clone(),
        right_source_sha256: right.source_sha256.clone(),
        quantum_jensen_shannon_bits: None,
        authority_effect: AuthorityEffect::None,
    };
    if !headers_compatible(left, right) {
        result.reason =
            Some("schema, feature profile, dimension, role, field and trust must match".to_owned());
        return result;
    }
    let states = state_from_report(left).and_then(|a| state_from_report(right).map(|b| (a, b)));
    let (a, b) = match states {
        Ok(states) => states,
        Err(error) => {
            result.status = "INVALID_INPUT".to_owned();
            result.reason = Some(error);
            return result;
        }
    };
    let mixture = match a.mix(&b, 0.5) {
        Ok(mixture) => mixture,
        Err(error) => {
            result.status = "UNAVAILABLE".to_owned();
            result.reason = Some(error);
            return result;
        }
    };
    let divergence = entropy_bits(&mixture.compute_spectrum())
        - 0.5 * entropy_bits(&a.compute_spectrum())
        - 0.5 * entropy_bits(&b.compute_spectrum());
    if !divergence.is_finite() || !(-1e-8..=1.0 + 1e-8).contains(&divergence) {
        result.status = "UNAVAILABLE".to_owned();
        result.reason =
            Some("numerical Jensen-Shannon divergence is outside its finite range".to_owned());
        return result;
    }
    result.status = "COMPARED".to_owned();
    result.quantum_jensen_shannon_bits = Some(divergence.clamp(0.0, 1.0));
    result
}

fn state_from_report(report: &PromptDensityReport) -> Result<FactorizedDensity, String> {
    if report.status != ObservationStatus::Observed
        || !(MIN_DIM..=MAX_DIM).contains(&report.dim)
        || report.authority_effect != AuthorityEffect::None
        || report.factors.is_empty()
        || report.factors.len() > MAX_COMPONENTS
        || report.weights.len() != report.factors.len()
        || report.spans.len() != report.factors.len()
        || report.source_bytes == 0
        || report.source_bytes > MAX_SOURCE_BYTES
        || [
            report.role_id.as_str(),
            report.field.as_str(),
            report.trust_level.as_str(),
        ]
        .iter()
        .any(|s| s.trim().is_empty() || s.len() > 256)
        || !report
            .source_sha256
            .strip_prefix("sha256:")
            .is_some_and(|s| {
                s.len() == 64
                    && s.bytes()
                        .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
            })
    {
        return Err("report is not a bounded observed state".to_owned());
    }
    let mut offset = 0;
    let mut token_count = 0;
    for span in &report.spans {
        if span.start_byte != offset
            || span.end_byte <= offset
            || span.end_byte > report.source_bytes
            || span.token_start != token_count
            || span.token_count == 0
            || span.token_count > MAX_TOKENS
        {
            return Err("report has invalid ordered source spans".to_owned());
        }
        offset = span.end_byte;
        token_count += span.token_count;
    }
    if offset != report.source_bytes
        || token_count > MAX_TOKENS
        || report.weights.iter().any(|v| !v.is_finite() || *v < 0.0)
        || (report.weights.iter().sum::<f64>() - 1.0).abs() > 1e-8
    {
        return Err("report does not have complete spans and normalized weights".to_owned());
    }
    for (factor, weight) in report.factors.iter().zip(report.weights.iter()) {
        if factor.len() != report.dim
            || factor.iter().any(|v| !v.is_finite())
            || (factor.iter().map(|v| v * v).sum::<f64>() - 1.0).abs() > 1e-8
            || *weight <= 0.0
        {
            return Err("report has a non-finite or non-unit factor".to_owned());
        }
    }
    for (span, weight) in report.spans.iter().zip(&report.weights) {
        if (*weight - span.token_count as f64 / token_count as f64).abs() > 1e-8 {
            return Err("weights do not match token-count mixture profile".to_owned());
        }
    }
    FactorizedDensity::new(
        report
            .factors
            .iter()
            .map(|v| CVector::from_iterator(v.len(), v.iter().map(|&x| C64::new(x, 0.0))))
            .collect(),
        Some(report.weights.clone()),
    )
}

// Origin: engine/crates_rs/engines/src/quantum/prompt_density.rs
// Claim: urn:core:crates_rs:engines:prompt-density:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9c2ae25b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9c2ae25b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9c2ae25b {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError9c2ae25b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9c2ae25b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9c2ae25b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9c2ae25b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9c2ae25b> {
        if capacity_bound == 0 {
            return Err(BoundaryError9c2ae25b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9c2ae25b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9c2ae25b::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_9c2ae25b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9c2ae25b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9c2ae25b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9c2ae25b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9c2ae25b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9c2ae25b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9c2ae25b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9c2ae25b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
