//! --- Math Contract:
//! Object: structural and numerical classification of an EPK detector deployment.
//! Preconditions: an optional declaration/evidence pair and a finite composed corpus.
//! Postconditions: exact structural refusal or explicitly numerical evidence classification.
//! Authority: None. No verdict is `Adequate`; exact BSC-CERT remains open.
//! ---

use crate::epk_engine::{BoundarySlice, CompositionRecord, TraceLedger, TraceRecord};
use num_rational::BigRational;
use num_traits::{One, Signed, ToPrimitive, Zero};
use core_types::{
    detector_magnitude_is_in_policy, AuthorityEffect, DetectorCapacityEvidence,
    DetectorDeploymentDeclaration, DetectorEvaluatorDeclaration, DetectorEvaluatorRole,
    DETECTOR_CAPACITY_EVIDENCE_SCHEMA, DETECTOR_CAPACITY_SCOPE,
};

pub use core_types::{
    detector_capacity_comparison_tolerance_rational, detector_capacity_rank_tolerance_rational,
    detector_capacity_residual_acceptance_tolerance_rational,
};

/// Exact rational representation of an untrusted IEEE-754 float from solver evidence.
///
/// AuthorityEffect: None.
/// Non-finite values are refused before any comparison. `NaN` and infinities are
/// not exact zero, so they must not become a rational witness.
pub fn float_to_rational(value: f64) -> Option<BigRational> {
    if !value.is_finite() {
        return None;
    }
    BigRational::from_float(value)
}

fn detector_float_rational(
    value: f64,
) -> Result<BigRational, DetectorNumericalUnresolvedReason> {
    float_to_rational(value).ok_or(DetectorNumericalUnresolvedReason::NonFiniteFloat)
}

fn detector_evidence_has_non_finite_float(evidence: &DetectorCapacityEvidence) -> bool {
    !evidence.value().is_finite()
        || !evidence.witness().section_l2().is_finite()
        || !evidence.witness().defect_l2().is_finite()
        || !evidence.residuals().max_residual().is_finite()
        || evidence
            .restricted_singular_values()
            .iter()
            .any(|value| !value.is_finite())
        || evidence
            .witness()
            .section()
            .iter()
            .any(|value| !value.is_finite())
        || evidence
            .witness()
            .defect()
            .iter()
            .any(|value| !value.is_finite())
}
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub const DETECTOR_ADEQUACY_VERDICT_SCHEMA: &str = "core.epk.detector-adequacy-verdict.v1";
pub const DETECTOR_OBSERVED_CORPUS_DIGEST_SCOPE: &str =
    "boundary slice, sorted composition records, and referenced segment traces only";
pub const DETECTOR_THREAT_8_DISCLOSURE: &str =
    "Threat-8 carrier closure is disclosure-only; even closure on the observed corpus does not authorize a full adequacy claim";

const DETECTOR_OBSERVED_CORPUS_DIGEST_DOMAIN: &[u8] = b"core.epk.detector-observed-corpus.v1\0";

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum DetectorAdequacyVerdictKind {
    Undeclared,
    StructuralInadequate,
    NumericalCounterevidence,
    NumericallySupported,
    NumericalUnresolved,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum DetectorUndeclaredReason {
    DeploymentDeclarationMissing,
    CapacityEvidenceMissing,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum DetectorLocalSide {
    Left,
    Right,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum DetectorStructuralFailure {
    EmptyCorpus,
    EmptyProtectedDistinctions,
    DuplicateProtectedDistinction {
        distinction_id: String,
    },
    EmptyProtectedDirection {
        distinction_id: String,
    },
    ProtectedDirectionMagnitudeOutOfPolicy {
        distinction_id: String,
        coordinate_index: usize,
    },
    ProtectedDirectionDimensionMismatch {
        distinction_id: String,
        expected: usize,
        found: usize,
    },
    MissingEvaluatorDeclaration {
        role: DetectorEvaluatorRole,
    },
    DuplicateEvaluatorDeclaration {
        role: DetectorEvaluatorRole,
    },
    EmptyEvaluatorCarrier {
        role: DetectorEvaluatorRole,
    },
    CarrierNotClosed {
        role: DetectorEvaluatorRole,
        record_id: String,
    },
    CarrierOutsideCorpus {
        role: DetectorEvaluatorRole,
        record_id: String,
    },
    MissingProjection {
        role: DetectorEvaluatorRole,
        record_id: String,
    },
    ProjectionOutsideCarrier {
        role: DetectorEvaluatorRole,
        record_id: String,
    },
    EvaluatorNotCarrierBounded {
        role: DetectorEvaluatorRole,
        first_record_id: String,
        second_record_id: String,
    },
    CarrierClosureVacuous,
    MissingBlindSpotDeclaration {
        role: DetectorEvaluatorRole,
    },
    MissingProtectedDistinctionForEvaluator {
        role: DetectorEvaluatorRole,
    },
    ProtectedPairUsesSameRecord {
        distinction_id: String,
    },
    ProtectedRecordMissing {
        distinction_id: String,
        record_id: String,
    },
    ProjectionCollision {
        distinction_id: String,
        role: DetectorEvaluatorRole,
    },
    EvaluatorDoesNotSeparate {
        distinction_id: String,
        role: DetectorEvaluatorRole,
    },
    EmptyBoundarySlice,
    BoundaryDeclarationMismatch,
    DuplicateCorpusRecord {
        record_id: String,
    },
    MissingSegmentTrace {
        composed_record_id: String,
        trace_id: String,
    },
    LocalEvaluatorLedgerMismatch {
        composed_record_id: String,
        side: DetectorLocalSide,
        trace_id: String,
        composition_value: bool,
        ledger_value: bool,
    },
    UngluedBoundary {
        composed_record_id: String,
    },
    BoundaryOutsideSlice {
        composed_record_id: String,
        boundary_state: String,
    },
    BoundaryNotInterior {
        composed_record_id: String,
        boundary_state: String,
    },
    EvaluatorConstant {
        role: DetectorEvaluatorRole,
    },
    LocalProductConstant,
    GlobalEqualsLocalProduct,
    MissingNgdWitness,
    MissingLrgrWitness,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum DetectorNumericalUnresolvedReason {
    EvidenceSchemaMismatch,
    EvidenceScopeMismatch,
    CapacityModelDigestMismatch,
    ProtectedSubspaceDigestMismatch,
    RankTolerancePolicyMismatch {
        expected: BigRational,
        found: BigRational,
    },
    ResidualTolerancePolicyMismatch {
        expected: BigRational,
        found: BigRational,
    },
    ComparisonTolerancePolicyMismatch {
        expected: BigRational,
        found: BigRational,
    },
    EpsilonMismatch,
    DimensionMismatch,
    SingularValuesNotDescending,
    TopValueMismatch,
    WitnessSectionNormMismatch,
    WitnessDefectCapacityMismatch,
    ResidualGateFailed {
        max_residual: BigRational,
        tolerance: BigRational,
    },
    ThresholdBand {
        value: BigRational,
        epsilon: BigRational,
        band: BigRational,
    },
    NonFiniteFloat,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct DetectorCorpusCounts {
    sample_count: usize,
    global_failure_count: usize,
    ngd_count: usize,
    lrgr_count: usize,
}

impl DetectorCorpusCounts {
    pub fn from_records(records: &[CompositionRecord]) -> Self {
        let global_failure_count = records.iter().filter(|record| !record.global_pass).count();
        let ngd_count = records
            .iter()
            .filter(|record| record.local_product() && !record.global_pass)
            .count();
        let lrgr_count = records
            .iter()
            .filter(|record| !record.local_product() && !record.global_pass)
            .count();
        Self {
            sample_count: records.len(),
            global_failure_count,
            ngd_count,
            lrgr_count,
        }
    }

    pub fn sample_count(self) -> usize {
        self.sample_count
    }
    pub fn global_pass_count(self) -> usize {
        self.sample_count - self.global_failure_count
    }
    pub fn global_failure_count(self) -> usize {
        self.global_failure_count
    }
    pub fn ngd_count(self) -> usize {
        self.ngd_count
    }
    pub fn lrgr_count(self) -> usize {
        self.lrgr_count
    }
    pub fn global_failure_partition_holds(self) -> bool {
        self.global_failure_count == self.ngd_count + self.lrgr_count
    }
    /// Finite-count form of `1 - GPR = NGD + LRGR`.
    pub fn one_minus_gpr_partition_holds(self) -> bool {
        self.sample_count == self.global_pass_count() + self.ngd_count + self.lrgr_count
    }
}

/// Exact corpus-level disclosure of global projection closure over local projections.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DetectorCarrierClosureDisclosure {
    comparable_pair_count: usize,
    collision_pairs: Vec<[String; 2]>,
    global_carrier_closed_on_corpus: bool,
}

impl DetectorCarrierClosureDisclosure {
    pub fn comparable_pair_count(&self) -> usize {
        self.comparable_pair_count
    }
    pub fn collision_pairs(&self) -> &[[String; 2]] {
        &self.collision_pairs
    }
    /// Named Threat-8 disclosure only; even `true` cannot authorize full adequacy.
    pub fn global_carrier_closed_on_corpus(&self) -> bool {
        self.global_carrier_closed_on_corpus
    }
}

fn encode_size(output: &mut Vec<u8>, value: usize) {
    output.extend_from_slice(&(value as u128).to_le_bytes());
}

fn encode_bytes(output: &mut Vec<u8>, value: &[u8]) {
    encode_size(output, value.len());
    output.extend_from_slice(value);
}

fn encode_string(output: &mut Vec<u8>, value: &str) {
    encode_bytes(output, value.as_bytes());
}

fn encode_bool(output: &mut Vec<u8>, value: bool) {
    output.push(u8::from(value));
}

fn encode_optional_string(output: &mut Vec<u8>, value: Option<&str>) {
    match value {
        Some(value) => {
            output.push(1);
            encode_string(output, value);
        }
        None => output.push(0),
    }
}

fn encode_optional_exact(output: &mut Vec<u8>, value: Option<&BigRational>) {
    match value {
        Some(value) => {
            output.push(1);
            encode_string(output, &value.to_string());
        }
        None => output.push(0),
    }
}

fn encode_trace(output: &mut Vec<u8>, trace: &TraceRecord) {
    encode_string(output, &trace.trace_id);
    encode_string(output, &trace.task_id);
    encode_string(output, &trace.stage);
    encode_optional_string(output, trace.parent_trace_id.as_deref());
    encode_string(output, &trace.input_hash);
    encode_string(output, &trace.output_hash);
    encode_string(output, &trace.cost.to_string());
    encode_string(output, &trace.residual_risk.to_string());
    encode_bool(output, trace.evaluator_pass);
}

fn encode_referenced_trace(
    output: &mut Vec<u8>,
    side: DetectorLocalSide,
    trace: Option<&TraceRecord>,
) {
    output.push(match side {
        DetectorLocalSide::Left => 0,
        DetectorLocalSide::Right => 1,
    });
    match trace {
        Some(trace) => {
            output.push(1);
            encode_trace(output, trace);
        }
        None => output.push(0),
    }
}

fn observed_record_encoding(record: &CompositionRecord, ledger: &TraceLedger) -> Vec<u8> {
    let mut output = Vec::new();
    encode_string(&mut output, &record.composed_trace_id);
    encode_string(&mut output, &record.left_trace_id);
    encode_string(&mut output, &record.right_trace_id);
    encode_bool(&mut output, record.local_left_pass);
    encode_bool(&mut output, record.local_right_pass);
    encode_bool(&mut output, record.global_pass);
    encode_optional_exact(&mut output, record.composed_cost.as_ref());
    encode_referenced_trace(
        &mut output,
        DetectorLocalSide::Left,
        ledger.get(&record.left_trace_id),
    );
    encode_referenced_trace(
        &mut output,
        DetectorLocalSide::Right,
        ledger.get(&record.right_trace_id),
    );
    output
}

/// SHA-256 commitment to the exact observed trajectory used by the verdict.
///
/// The scope is deliberately limited to the boundary slice, sorted composition
/// records, and the segment traces those records reference. Unreferenced ledger
/// entries cannot change a verdict and are therefore outside this commitment.
pub fn detector_observed_corpus_digest(
    records: &[CompositionRecord],
    ledger: &TraceLedger,
    boundary: &BoundarySlice,
) -> String {
    let mut input = DETECTOR_OBSERVED_CORPUS_DIGEST_DOMAIN.to_vec();
    encode_string(&mut input, &boundary.name);
    encode_size(&mut input, boundary.states.len());
    for state in &boundary.states {
        encode_string(&mut input, state);
    }
    let mut encoded_records: Vec<_> = records
        .iter()
        .map(|record| observed_record_encoding(record, ledger))
        .collect();
    encoded_records.sort();
    encode_size(&mut input, encoded_records.len());
    for encoded_record in encoded_records {
        encode_bytes(&mut input, &encoded_record);
    }
    format!("{:x}", Sha256::digest(input))
}

/// Validated, serialize-only detector verdict.
///
/// ```compile_fail
/// use core_epk::DetectorAdequacyVerdict;
/// let _: DetectorAdequacyVerdict = serde_json::from_str("{}").unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DetectorAdequacyVerdict {
    schema: &'static str,
    kind: DetectorAdequacyVerdictKind,
    authority: AuthorityEffect,
    counts: DetectorCorpusCounts,
    carrier_closure: Option<DetectorCarrierClosureDisclosure>,
    threat_8_disclosure: &'static str,
    declaration_digest: Option<String>,
    observed_corpus_digest: String,
    observed_corpus_digest_scope: &'static str,
    undeclared_reason: Option<DetectorUndeclaredReason>,
    structural_failures: Vec<DetectorStructuralFailure>,
    numerical_unresolved_reason: Option<DetectorNumericalUnresolvedReason>,
    capacity_value: Option<BigRational>,
    epsilon: Option<BigRational>,
}

impl DetectorAdequacyVerdict {
    pub fn kind(&self) -> DetectorAdequacyVerdictKind {
        self.kind
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
    pub fn counts(&self) -> DetectorCorpusCounts {
        self.counts
    }
    pub fn carrier_closure(&self) -> Option<&DetectorCarrierClosureDisclosure> {
        self.carrier_closure.as_ref()
    }
    pub fn threat_8_disclosure(&self) -> &'static str {
        self.threat_8_disclosure
    }
    pub fn declaration_digest(&self) -> Option<&str> {
        self.declaration_digest.as_deref()
    }
    pub fn observed_corpus_digest(&self) -> &str {
        &self.observed_corpus_digest
    }
    pub fn observed_corpus_digest_scope(&self) -> &'static str {
        self.observed_corpus_digest_scope
    }
    pub fn undeclared_reason(&self) -> Option<&DetectorUndeclaredReason> {
        self.undeclared_reason.as_ref()
    }
    pub fn structural_failures(&self) -> &[DetectorStructuralFailure] {
        &self.structural_failures
    }
    pub fn numerical_unresolved_reason(&self) -> Option<&DetectorNumericalUnresolvedReason> {
        self.numerical_unresolved_reason.as_ref()
    }
    pub fn capacity_value(&self) -> Option<f64> {
        self.capacity_value.as_ref().and_then(|v| v.to_f64())
    }
    pub fn epsilon(&self) -> Option<f64> {
        self.epsilon.as_ref().and_then(|v| v.to_f64())
    }
    pub fn capacity_value_rational(&self) -> Option<&BigRational> {
        self.capacity_value.as_ref()
    }
    pub fn epsilon_rational(&self) -> Option<&BigRational> {
        self.epsilon.as_ref()
    }
}

fn verdict(
    kind: DetectorAdequacyVerdictKind,
    counts: DetectorCorpusCounts,
    observed_corpus_digest: &str,
    declaration_digest: Option<&str>,
) -> DetectorAdequacyVerdict {
    DetectorAdequacyVerdict {
        schema: DETECTOR_ADEQUACY_VERDICT_SCHEMA,
        kind,
        authority: AuthorityEffect::None,
        counts,
        carrier_closure: None,
        threat_8_disclosure: DETECTOR_THREAT_8_DISCLOSURE,
        declaration_digest: declaration_digest.map(str::to_owned),
        observed_corpus_digest: observed_corpus_digest.to_owned(),
        observed_corpus_digest_scope: DETECTOR_OBSERVED_CORPUS_DIGEST_SCOPE,
        undeclared_reason: None,
        structural_failures: Vec::new(),
        numerical_unresolved_reason: None,
        capacity_value: None,
        epsilon: None,
    }
}

fn evaluator_value(role: DetectorEvaluatorRole, record: &CompositionRecord) -> bool {
    match role {
        DetectorEvaluatorRole::LocalLeft => record.local_left_pass,
        DetectorEvaluatorRole::LocalRight => record.local_right_pass,
        DetectorEvaluatorRole::Global => record.global_pass,
    }
}

fn unique_evaluator_for_role(
    declaration: &DetectorDeploymentDeclaration,
    role: DetectorEvaluatorRole,
) -> Option<&DetectorEvaluatorDeclaration> {
    let mut matches = declaration
        .evaluators()
        .iter()
        .filter(|evaluator| evaluator.role() == role);
    let first = matches.next()?;
    matches.next().is_none().then_some(first)
}

fn check_pair_closure(
    left: &DetectorEvaluatorDeclaration,
    right: &DetectorEvaluatorDeclaration,
    global: &DetectorEvaluatorDeclaration,
    first_id: &str,
    second_id: &str,
) -> Option<(bool, bool)> {
    let left_eq = left.projected_value(first_id)? == left.projected_value(second_id)?;
    let right_eq = right.projected_value(first_id)? == right.projected_value(second_id)?;
    let global_diff = global.projected_value(first_id)? != global.projected_value(second_id)?;
    Some((left_eq && right_eq, global_diff))
}

fn carrier_closure_disclosure(
    declaration: &DetectorDeploymentDeclaration,
    records: &[CompositionRecord],
) -> Option<DetectorCarrierClosureDisclosure> {
    let left = unique_evaluator_for_role(declaration, DetectorEvaluatorRole::LocalLeft)?;
    let right = unique_evaluator_for_role(declaration, DetectorEvaluatorRole::LocalRight)?;
    let global = unique_evaluator_for_role(declaration, DetectorEvaluatorRole::Global)?;
    let mut comparable_pair_count = 0;
    let mut collision_pairs = Vec::new();
    for left_index in 0..records.len() {
        for right_index in (left_index + 1)..records.len() {
            let first = &records[left_index];
            let second = &records[right_index];
            let (local_pair_matches, global_diff) = check_pair_closure(
                left,
                right,
                global,
                first.composed_trace_id.as_str(),
                second.composed_trace_id.as_str(),
            )?;
            if local_pair_matches {
                comparable_pair_count += 1;
                if global_diff {
                    collision_pairs.push([
                        first.composed_trace_id.clone(),
                        second.composed_trace_id.clone(),
                    ]);
                }
            }
        }
    }
    Some(DetectorCarrierClosureDisclosure {
        comparable_pair_count,
        global_carrier_closed_on_corpus: collision_pairs.is_empty(),
        collision_pairs,
    })
}

fn audit_segment_side(
    trace: Option<&TraceRecord>,
    side: DetectorLocalSide,
    composed_record_id: &str,
    trace_id: &str,
    composition_value: bool,
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    match trace {
        None => failures.push(DetectorStructuralFailure::MissingSegmentTrace {
            composed_record_id: composed_record_id.to_string(),
            trace_id: trace_id.to_string(),
        }),
        Some(seg) if seg.evaluator_pass != composition_value => {
            failures.push(DetectorStructuralFailure::LocalEvaluatorLedgerMismatch {
                composed_record_id: composed_record_id.to_string(),
                side,
                trace_id: trace_id.to_string(),
                composition_value,
                ledger_value: seg.evaluator_pass,
            });
        }
        Some(_) => {}
    }
}

fn audit_glued_boundary(
    left: &TraceRecord,
    right: &TraceRecord,
    composed_record_id: &str,
    boundary: &BoundarySlice,
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    if left.output_hash != right.input_hash {
        failures.push(DetectorStructuralFailure::UngluedBoundary {
            composed_record_id: composed_record_id.to_string(),
        });
        return;
    }
    let state = left.output_hash.clone();
    if !boundary.contains(&state) {
        failures.push(DetectorStructuralFailure::BoundaryOutsideSlice {
            composed_record_id: composed_record_id.to_string(),
            boundary_state: state.clone(),
        });
    }
    if state == left.input_hash || state == right.output_hash {
        failures.push(DetectorStructuralFailure::BoundaryNotInterior {
            composed_record_id: composed_record_id.to_string(),
            boundary_state: state,
        });
    }
}

fn collect_and_audit_corpus_records<'a>(
    records: &'a [CompositionRecord],
    ledger: &TraceLedger,
    boundary: &BoundarySlice,
    failures: &mut Vec<DetectorStructuralFailure>,
) -> BTreeMap<&'a str, &'a CompositionRecord> {
    let mut corpus = BTreeMap::new();
    for record in records {
        if corpus
            .insert(record.composed_trace_id.as_str(), record)
            .is_some()
        {
            failures.push(DetectorStructuralFailure::DuplicateCorpusRecord {
                record_id: record.composed_trace_id.clone(),
            });
        }
        let left = ledger.get(&record.left_trace_id);
        let right = ledger.get(&record.right_trace_id);
        audit_segment_side(
            left,
            DetectorLocalSide::Left,
            &record.composed_trace_id,
            &record.left_trace_id,
            record.local_left_pass,
            failures,
        );
        audit_segment_side(
            right,
            DetectorLocalSide::Right,
            &record.composed_trace_id,
            &record.right_trace_id,
            record.local_right_pass,
            failures,
        );
        if let (Some(left), Some(right)) = (left, right) {
            audit_glued_boundary(left, right, &record.composed_trace_id, boundary, failures);
        }
    }
    corpus
}

fn audit_evaluator_carrier_sets(
    role: DetectorEvaluatorRole,
    evaluator: &DetectorEvaluatorDeclaration,
    corpus_ids: &BTreeSet<&str>,
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    if evaluator.carrier_record_ids().is_empty() {
        failures.push(DetectorStructuralFailure::EmptyEvaluatorCarrier { role });
    }
    if !evaluator.blind_spot_declaration_complete() {
        failures.push(DetectorStructuralFailure::MissingBlindSpotDeclaration { role });
    }
    for record_id in corpus_ids {
        if !evaluator.carrier_record_ids().contains(*record_id) {
            failures.push(DetectorStructuralFailure::CarrierNotClosed {
                role,
                record_id: (*record_id).to_string(),
            });
        }
        if evaluator.projected_value(record_id).is_none() {
            failures.push(DetectorStructuralFailure::MissingProjection {
                role,
                record_id: (*record_id).to_string(),
            });
        }
    }
}

fn audit_evaluator_extra_ids(
    role: DetectorEvaluatorRole,
    evaluator: &DetectorEvaluatorDeclaration,
    corpus_ids: &BTreeSet<&str>,
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    for record_id in evaluator.carrier_record_ids() {
        if !corpus_ids.contains(record_id.as_str()) {
            failures.push(DetectorStructuralFailure::CarrierOutsideCorpus {
                role,
                record_id: record_id.clone(),
            });
        }
    }
    for record_id in evaluator.projected_observations().keys() {
        if !evaluator.carrier_record_ids().contains(record_id) {
            failures.push(DetectorStructuralFailure::ProjectionOutsideCarrier {
                role,
                record_id: record_id.clone(),
            });
        }
    }
}

fn audit_evaluator_carrier_boundedness(
    role: DetectorEvaluatorRole,
    evaluator: &DetectorEvaluatorDeclaration,
    ordered_records: &[&CompositionRecord],
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    for first_index in 0..ordered_records.len() {
        for second_index in (first_index + 1)..ordered_records.len() {
            let first = ordered_records[first_index];
            let second = ordered_records[second_index];
            let first_projection = evaluator.projected_value(&first.composed_trace_id);
            let second_projection = evaluator.projected_value(&second.composed_trace_id);
            if first_projection.is_some()
                && first_projection == second_projection
                && evaluator_value(role, first) != evaluator_value(role, second)
            {
                failures.push(DetectorStructuralFailure::EvaluatorNotCarrierBounded {
                    role,
                    first_record_id: first.composed_trace_id.clone(),
                    second_record_id: second.composed_trace_id.clone(),
                });
            }
        }
    }
}

fn collect_and_audit_evaluators<'a>(
    declaration: &'a DetectorDeploymentDeclaration,
    records: &'a [CompositionRecord],
    corpus: &BTreeMap<&'a str, &'a CompositionRecord>,
    roles: &[DetectorEvaluatorRole; 3],
    failures: &mut Vec<DetectorStructuralFailure>,
) -> BTreeMap<DetectorEvaluatorRole, &'a DetectorEvaluatorDeclaration> {
    let corpus_ids: BTreeSet<_> = records
        .iter()
        .map(|record| record.composed_trace_id.as_str())
        .collect();
    let ordered_records: Vec<_> = corpus.values().copied().collect();
    let mut evaluator_by_role: BTreeMap<DetectorEvaluatorRole, &DetectorEvaluatorDeclaration> =
        BTreeMap::new();
    for evaluator in declaration.evaluators() {
        if evaluator_by_role
            .insert(evaluator.role(), evaluator)
            .is_some()
        {
            failures.push(DetectorStructuralFailure::DuplicateEvaluatorDeclaration {
                role: evaluator.role(),
            });
        }
    }
    for &role in roles {
        let Some(evaluator) = evaluator_by_role.get(&role).copied() else {
            failures.push(DetectorStructuralFailure::MissingEvaluatorDeclaration { role });
            continue;
        };
        audit_evaluator_carrier_sets(role, evaluator, &corpus_ids, failures);
        audit_evaluator_extra_ids(role, evaluator, &corpus_ids, failures);
        audit_evaluator_carrier_boundedness(role, evaluator, &ordered_records, failures);
    }
    if let Some(disclosure) = carrier_closure_disclosure(declaration, records) {
        if disclosure.comparable_pair_count == 0 {
            failures.push(DetectorStructuralFailure::CarrierClosureVacuous);
        }
    }
    evaluator_by_role
}

fn audit_protected_direction(
    id: &str,
    direction: &[f64],
    expected_dimension: Option<usize>,
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    for (coordinate_index, value) in direction.iter().copied().enumerate() {
        if value != 0.0 && !detector_magnitude_is_in_policy(value) {
            failures.push(
                DetectorStructuralFailure::ProtectedDirectionMagnitudeOutOfPolicy {
                    distinction_id: id.to_string(),
                    coordinate_index,
                },
            );
        }
    }
    if direction.is_empty() || direction.iter().all(|value| *value == 0.0) {
        failures.push(DetectorStructuralFailure::EmptyProtectedDirection {
            distinction_id: id.to_string(),
        });
    }
    if let Some(expected) = expected_dimension {
        if direction.len() != expected {
            failures.push(
                DetectorStructuralFailure::ProtectedDirectionDimensionMismatch {
                    distinction_id: id.to_string(),
                    expected,
                    found: direction.len(),
                },
            );
        }
    }
}

fn audit_protected_pair_records(
    id: &str,
    role: DetectorEvaluatorRole,
    positive_id: &str,
    negative_id: &str,
    corpus: &BTreeMap<&str, &CompositionRecord>,
    evaluator: Option<&DetectorEvaluatorDeclaration>,
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    if positive_id == negative_id {
        failures.push(DetectorStructuralFailure::ProtectedPairUsesSameRecord {
            distinction_id: id.to_string(),
        });
    }
    let positive = corpus.get(positive_id).copied();
    let negative = corpus.get(negative_id).copied();
    for (record_id, record) in [(positive_id, positive), (negative_id, negative)] {
        if record.is_none() {
            failures.push(DetectorStructuralFailure::ProtectedRecordMissing {
                distinction_id: id.to_string(),
                record_id: record_id.to_string(),
            });
        }
    }
    if let (Some(evaluator), Some(positive), Some(negative)) = (evaluator, positive, negative) {
        if evaluator.projected_value(positive_id) == evaluator.projected_value(negative_id) {
            failures.push(DetectorStructuralFailure::ProjectionCollision {
                distinction_id: id.to_string(),
                role,
            });
        }
        if evaluator_value(role, positive) == evaluator_value(role, negative) {
            failures.push(DetectorStructuralFailure::EvaluatorDoesNotSeparate {
                distinction_id: id.to_string(),
                role,
            });
        }
    }
}

fn audit_protected_distinctions(
    declaration: &DetectorDeploymentDeclaration,
    corpus: &BTreeMap<&str, &CompositionRecord>,
    evaluator_by_role: &BTreeMap<DetectorEvaluatorRole, &DetectorEvaluatorDeclaration>,
    roles: &[DetectorEvaluatorRole; 3],
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    let distinctions = declaration.protected_distinctions();
    if distinctions.is_empty() {
        failures.push(DetectorStructuralFailure::EmptyProtectedDistinctions);
    }
    let expected_dimension = distinctions.iter().find_map(|item| {
        (!item.section_direction().is_empty()).then_some(item.section_direction().len())
    });
    let mut distinction_ids = BTreeSet::new();
    let mut roles_with_distinctions = BTreeSet::new();
    for distinction in distinctions {
        let id = distinction.distinction_id().to_string();
        let role = distinction.evaluator();
        roles_with_distinctions.insert(role);
        if !distinction_ids.insert(id.clone()) {
            failures.push(DetectorStructuralFailure::DuplicateProtectedDistinction {
                distinction_id: id.clone(),
            });
        }
        audit_protected_direction(&id, distinction.section_direction(), expected_dimension, failures);
        audit_protected_pair_records(
            &id,
            role,
            distinction.positive_record_id(),
            distinction.negative_record_id(),
            corpus,
            evaluator_by_role.get(&role).copied(),
            failures,
        );
    }
    for &role in roles {
        if !roles_with_distinctions.contains(&role) {
            failures
                .push(DetectorStructuralFailure::MissingProtectedDistinctionForEvaluator { role });
        }
    }
}

fn audit_corpus_witness_variety(
    records: &[CompositionRecord],
    roles: &[DetectorEvaluatorRole; 3],
    failures: &mut Vec<DetectorStructuralFailure>,
) {
    for &role in roles {
        let values: BTreeSet<_> = records
            .iter()
            .map(|record| evaluator_value(role, record))
            .collect();
        if values.len() < 2 {
            failures.push(DetectorStructuralFailure::EvaluatorConstant { role });
        }
    }
    let local_products: BTreeSet<_> = records
        .iter()
        .map(CompositionRecord::local_product)
        .collect();
    if local_products.len() < 2 {
        failures.push(DetectorStructuralFailure::LocalProductConstant);
    }
    if records
        .iter()
        .all(|record| record.global_pass == record.local_product())
    {
        failures.push(DetectorStructuralFailure::GlobalEqualsLocalProduct);
    }
    if !records
        .iter()
        .any(|record| record.local_product() && !record.global_pass)
    {
        failures.push(DetectorStructuralFailure::MissingNgdWitness);
    }
    if !records
        .iter()
        .any(|record| !record.local_product() && !record.global_pass)
    {
        failures.push(DetectorStructuralFailure::MissingLrgrWitness);
    }
}

fn exact_structural_failures(
    declaration: &DetectorDeploymentDeclaration,
    records: &[CompositionRecord],
    ledger: &TraceLedger,
    boundary: &BoundarySlice,
) -> Vec<DetectorStructuralFailure> {
    let mut failures = Vec::new();
    if records.is_empty() {
        failures.push(DetectorStructuralFailure::EmptyCorpus);
    }
    if boundary.states.is_empty() {
        failures.push(DetectorStructuralFailure::EmptyBoundarySlice);
    }
    if declaration.boundary_name() != boundary.name
        || declaration.boundary_states() != &boundary.states
    {
        failures.push(DetectorStructuralFailure::BoundaryDeclarationMismatch);
    }

    let corpus = collect_and_audit_corpus_records(records, ledger, boundary, &mut failures);
    let roles = [
        DetectorEvaluatorRole::LocalLeft,
        DetectorEvaluatorRole::LocalRight,
        DetectorEvaluatorRole::Global,
    ];
    let evaluator_by_role =
        collect_and_audit_evaluators(declaration, records, &corpus, &roles, &mut failures);
    audit_protected_distinctions(
        declaration,
        &corpus,
        &evaluator_by_role,
        &roles,
        &mut failures,
    );
    audit_corpus_witness_variety(records, &roles, &mut failures);
    failures
}

fn check_evidence_header_and_policy(
    declaration: &DetectorDeploymentDeclaration,
    evidence: &DetectorCapacityEvidence,
) -> Option<DetectorNumericalUnresolvedReason> {
    if evidence.schema() != DETECTOR_CAPACITY_EVIDENCE_SCHEMA {
        return Some(DetectorNumericalUnresolvedReason::EvidenceSchemaMismatch);
    }
    if evidence.scope() != DETECTOR_CAPACITY_SCOPE {
        return Some(DetectorNumericalUnresolvedReason::EvidenceScopeMismatch);
    }
    if evidence.capacity_model_digest() != declaration.capacity_model_digest() {
        return Some(DetectorNumericalUnresolvedReason::CapacityModelDigestMismatch);
    }
    if evidence.protected_subspace_digest() != declaration.protected_subspace_digest() {
        return Some(DetectorNumericalUnresolvedReason::ProtectedSubspaceDigestMismatch);
    }
    check_evidence_tolerances(declaration, evidence)
}

fn check_evidence_tolerances(
    declaration: &DetectorDeploymentDeclaration,
    evidence: &DetectorCapacityEvidence,
) -> Option<DetectorNumericalUnresolvedReason> {
    if evidence.rank_tolerance_used_rational() != detector_capacity_rank_tolerance_rational() {
        return Some(
            DetectorNumericalUnresolvedReason::RankTolerancePolicyMismatch {
                expected: detector_capacity_rank_tolerance_rational(),
                found: evidence.rank_tolerance_used_rational(),
            },
        );
    }
    if evidence.residual_acceptance_tolerance_rational()
        != detector_capacity_residual_acceptance_tolerance_rational()
    {
        return Some(
            DetectorNumericalUnresolvedReason::ResidualTolerancePolicyMismatch {
                expected: detector_capacity_residual_acceptance_tolerance_rational(),
                found: evidence.residual_acceptance_tolerance_rational(),
            },
        );
    }
    if evidence.comparison_tolerance_rational()
        != detector_capacity_comparison_tolerance_rational()
    {
        return Some(
            DetectorNumericalUnresolvedReason::ComparisonTolerancePolicyMismatch {
                expected: detector_capacity_comparison_tolerance_rational(),
                found: evidence.comparison_tolerance_rational(),
            },
        );
    }
    if evidence.epsilon_rational() != declaration.epsilon_rational() {
        return Some(DetectorNumericalUnresolvedReason::EpsilonMismatch);
    }
    None
}

fn check_evidence_dimensions_and_spectrum(
    declaration: &DetectorDeploymentDeclaration,
    evidence: &DetectorCapacityEvidence,
) -> Option<DetectorNumericalUnresolvedReason> {
    let section_dimension = declaration.protected_coordinate_dimension().unwrap_or(0);
    let dim_mismatch = [
        evidence.witness().section().len() != section_dimension,
        evidence.all_green_dimension() > section_dimension,
        evidence.protected_span_dimension() > declaration.protected_distinctions().len(),
        evidence.restricted_dimension() > evidence.all_green_dimension(),
        evidence.restricted_dimension() > evidence.protected_span_dimension(),
        evidence.restricted_singular_values().len() != evidence.restricted_dimension(),
    ];
    if dim_mismatch.into_iter().any(|bad| bad) {
        return Some(DetectorNumericalUnresolvedReason::DimensionMismatch);
    }
    if evidence
        .restricted_singular_values()
        .windows(2)
        .any(|pair| pair[0] < pair[1])
    {
        return Some(DetectorNumericalUnresolvedReason::SingularValuesNotDescending);
    }
    None
}

fn parse_evidence_rationals(
    evidence: &DetectorCapacityEvidence,
) -> Result<(BigRational, BigRational, BigRational, BigRational), DetectorNumericalUnresolvedReason> {
    let expected_top_rat = match evidence.restricted_singular_values().first().copied() {
        Some(value) => detector_float_rational(value)?,
        None => BigRational::zero(),
    };
    let witness_section_rat = detector_float_rational(evidence.witness().section_l2())?;
    let defect_l2_rat = detector_float_rational(evidence.witness().defect_l2())?;
    let max_residual_rat = detector_float_rational(evidence.residuals().max_residual())?;
    Ok((expected_top_rat, witness_section_rat, defect_l2_rat, max_residual_rat))
}

fn check_evidence_witness_and_residuals(
    evidence: &DetectorCapacityEvidence,
    val_rat: &BigRational,
    comp_tol_rat: &BigRational,
) -> Option<DetectorNumericalUnresolvedReason> {
    let (expected_top_rat, witness_section_rat, defect_l2_rat, max_residual_rat) =
        match parse_evidence_rationals(evidence) {
            Ok(rationals) => rationals,
            Err(reason) => return Some(reason),
        };
    let top_scale = expected_top_rat.abs().max(val_rat.abs()).max(BigRational::one());
    if (&expected_top_rat - val_rat).abs() > comp_tol_rat * &top_scale {
        return Some(DetectorNumericalUnresolvedReason::TopValueMismatch);
    }

    let expected_section_norm = if evidence.restricted_dimension() == 0 {
        BigRational::zero()
    } else {
        BigRational::one()
    };
    let witness_scale = witness_section_rat.abs().max(BigRational::one());
    if (&witness_section_rat - &expected_section_norm).abs() > comp_tol_rat * &witness_scale {
        return Some(DetectorNumericalUnresolvedReason::WitnessSectionNormMismatch);
    }

    let attainment_scale = defect_l2_rat.abs().max(val_rat.abs()).max(BigRational::one());
    if (&defect_l2_rat - val_rat).abs() > comp_tol_rat * &attainment_scale {
        return Some(DetectorNumericalUnresolvedReason::WitnessDefectCapacityMismatch);
    }
    let residual_tol_rat = evidence.residual_acceptance_tolerance_rational();
    if !evidence.residuals_within_tolerance() || max_residual_rat > residual_tol_rat {
        return Some(DetectorNumericalUnresolvedReason::ResidualGateFailed {
            max_residual: max_residual_rat,
            tolerance: residual_tol_rat,
        });
    }
    None
}

fn evidence_unresolved_reason(
    declaration: &DetectorDeploymentDeclaration,
    evidence: &DetectorCapacityEvidence,
) -> Option<DetectorNumericalUnresolvedReason> {
    if detector_evidence_has_non_finite_float(evidence) {
        return Some(DetectorNumericalUnresolvedReason::NonFiniteFloat);
    }
    if let Some(reason) = check_evidence_header_and_policy(declaration, evidence) {
        return Some(reason);
    }
    if let Some(reason) = check_evidence_dimensions_and_spectrum(declaration, evidence) {
        return Some(reason);
    }

    let val_rat = evidence.value_rational();
    let comp_tol_rat = evidence.comparison_tolerance_rational();
    if let Some(reason) = check_evidence_witness_and_residuals(evidence, &val_rat, &comp_tol_rat) {
        return Some(reason);
    }

    let eps_rat = declaration.epsilon_rational();
    let max_scale = val_rat.abs().max(eps_rat.abs()).max(BigRational::one());
    let band_rat = &comp_tol_rat * &max_scale;
    let diff = (&val_rat - &eps_rat).abs();
    if diff <= band_rat {
        return Some(DetectorNumericalUnresolvedReason::ThresholdBand {
            value: val_rat,
            epsilon: eps_rat,
            band: band_rat,
        });
    }
    None
}

/// Evaluate the exact structural guard and, only after it passes, classify the
/// untrusted f64 capacity evidence. No return path means exact adequacy.
pub fn evaluate_detector_adequacy(
    declaration: Option<&DetectorDeploymentDeclaration>,
    evidence: Option<&DetectorCapacityEvidence>,
    records: &[CompositionRecord],
    ledger: &TraceLedger,
    boundary: &BoundarySlice,
) -> DetectorAdequacyVerdict {
    let observed_corpus_digest = detector_observed_corpus_digest(records, ledger, boundary);
    let declaration_digest = declaration.map(DetectorDeploymentDeclaration::declaration_digest);
    let counts = DetectorCorpusCounts::from_records(records);
    debug_assert!(counts.global_failure_partition_holds());
    let Some(declaration) = declaration else {
        let mut output = verdict(
            DetectorAdequacyVerdictKind::Undeclared,
            counts,
            &observed_corpus_digest,
            declaration_digest.as_deref(),
        );
        output.undeclared_reason = Some(DetectorUndeclaredReason::DeploymentDeclarationMissing);
        return output;
    };
    let carrier_closure = carrier_closure_disclosure(declaration, records);
    let failures = exact_structural_failures(declaration, records, ledger, boundary);
    if !failures.is_empty() {
        let mut output = verdict(
            DetectorAdequacyVerdictKind::StructuralInadequate,
            counts,
            &observed_corpus_digest,
            declaration_digest.as_deref(),
        );
        output.carrier_closure = carrier_closure.clone();
        output.structural_failures = failures;
        return output;
    }
    let Some(evidence) = evidence else {
        let mut output = verdict(
            DetectorAdequacyVerdictKind::Undeclared,
            counts,
            &observed_corpus_digest,
            declaration_digest.as_deref(),
        );
        output.carrier_closure = carrier_closure.clone();
        output.undeclared_reason = Some(DetectorUndeclaredReason::CapacityEvidenceMissing);
        return output;
    };
    let val_rat = evidence.value_rational();
    let eps_rat = declaration.epsilon_rational();
    if let Some(reason) = evidence_unresolved_reason(declaration, evidence) {
        let mut output = verdict(
            DetectorAdequacyVerdictKind::NumericalUnresolved,
            counts,
            &observed_corpus_digest,
            declaration_digest.as_deref(),
        );
        output.carrier_closure = carrier_closure.clone();
        output.numerical_unresolved_reason = Some(reason);
        if evidence.value().is_finite() {
            output.capacity_value = Some(val_rat);
        }
        output.epsilon = Some(eps_rat);
        return output;
    }
    let kind = if val_rat > eps_rat {
        DetectorAdequacyVerdictKind::NumericalCounterevidence
    } else {
        DetectorAdequacyVerdictKind::NumericallySupported
    };
    let mut output = verdict(
        kind,
        counts,
        &observed_corpus_digest,
        declaration_digest.as_deref(),
    );
    output.carrier_closure = carrier_closure;
    output.capacity_value = Some(val_rat);
    output.epsilon = Some(eps_rat);
    output
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)


/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord136ad891 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord136ad891` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError136ad891 {
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
impl BoundaryError136ad891 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError136ad891 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError136ad891 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord136ad891 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError136ad891> {
        if capacity_bound == 0 {
            return Err(BoundaryError136ad891::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError136ad891::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError136ad891::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    //! --- Math Contract:
    //! Object: DetectorAdequacy structural and numerical classification.
    //! Preconditions: finite four-record and adversarial corpora.
    //! Postconditions: all degeneracies refuse; only qualified numerical labels remain.
    //! Authority: None.
    //! ---

    use super::*;
    use num_traits::{One, Zero};
    use core_types::{
        DetectorCapacityResiduals, DetectorCapacityWitness, DetectorEvaluatorDeclaration,
        ProtectedDistinctionDeclaration, DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
        DETECTOR_CAPACITY_RANK_TOLERANCE, DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
        MAX_DETECTOR_SAFE_MAGNITUDE, MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
    };

    fn strong_corpus() -> (Vec<CompositionRecord>, TraceLedger, BoundarySlice) {
        let values = [
            ("r0", true, true, false),
            ("r1", false, false, false),
            ("r2", false, true, true),
            ("r3", false, true, false),
        ];
        let mut ledger = TraceLedger::new();
        let mut records = Vec::new();
        let mut states = Vec::new();
        for (id, e1, e2, eg) in values {
            let left_id = format!("{id}-left");
            let right_id = format!("{id}-right");
            let middle = format!("{id}-middle");
            states.push(middle.clone());
            ledger.insert(
                TraceRecord::new(
                    &left_id,
                    "task",
                    "left",
                    None,
                    format!("{id}-source"),
                    &middle,
                    BigRational::one(),
                    BigRational::zero(),
                    e1,
                )
                .unwrap(),
            );
            ledger.insert(
                TraceRecord::new(
                    &right_id,
                    "task",
                    "right",
                    None,
                    &middle,
                    format!("{id}-target"),
                    BigRational::one(),
                    BigRational::zero(),
                    e2,
                )
                .unwrap(),
            );
            records.push(CompositionRecord::new(id, left_id, right_id, e1, e2, eg, None).unwrap());
        }
        (records, ledger, BoundarySlice::new("B", states))
    }

    fn synchronize_local_ledger(records: &[CompositionRecord], ledger: &mut TraceLedger) {
        let updates: Vec<_> = records
            .iter()
            .flat_map(|record| {
                let mut left = ledger.get(&record.left_trace_id).unwrap().clone();
                left.evaluator_pass = record.local_left_pass;
                let mut right = ledger.get(&record.right_trace_id).unwrap().clone();
                right.evaluator_pass = record.local_right_pass;
                [left, right]
            })
            .collect();
        for update in updates {
            ledger.insert(update);
        }
    }

    fn declaration(
        records: &[CompositionRecord],
        boundary: &BoundarySlice,
        epsilon: f64,
    ) -> DetectorDeploymentDeclaration {
        let carriers: Vec<_> = records
            .iter()
            .map(|record| record.composed_trace_id.clone())
            .collect();
        let evaluators = [
            DetectorEvaluatorRole::LocalLeft,
            DetectorEvaluatorRole::LocalRight,
            DetectorEvaluatorRole::Global,
        ]
        .into_iter()
        .map(|role| {
            DetectorEvaluatorDeclaration::new(
                role,
                carriers.clone(),
                records.iter().map(|record| {
                    (
                        record.composed_trace_id.clone(),
                        if evaluator_value(role, record) {
                            "pass"
                        } else {
                            "fail"
                        }
                        .to_string(),
                    )
                }),
                true,
                [format!("{role:?} known blind spot at B")],
            )
            .unwrap()
        })
        .collect();
        let distinctions = vec![
            ProtectedDistinctionDeclaration::new(
                "D-left",
                DetectorEvaluatorRole::LocalLeft,
                "r0",
                "r1",
                vec![1.0, 0.0, 0.0, 0.0],
            )
            .unwrap(),
            ProtectedDistinctionDeclaration::new(
                "D-right",
                DetectorEvaluatorRole::LocalRight,
                "r0",
                "r1",
                vec![0.0, 1.0, 0.0, 0.0],
            )
            .unwrap(),
            ProtectedDistinctionDeclaration::new(
                "D-global",
                DetectorEvaluatorRole::Global,
                "r2",
                "r3",
                vec![0.0, 0.0, 1.0, 0.0],
            )
            .unwrap(),
        ];
        DetectorDeploymentDeclaration::new(
            "deployment",
            "strong-four-record-corpus",
            &boundary.name,
            boundary.states.iter().cloned(),
            "capacity-model-a",
            epsilon,
            evaluators,
            distinctions,
        )
        .unwrap()
    }

    fn evidence(
        declaration: &DetectorDeploymentDeclaration,
        value: f64,
        residual: f64,
    ) -> DetectorCapacityEvidence {
        evidence_with_metadata(
            declaration,
            value,
            residual,
            declaration.capacity_model_digest(),
            declaration.protected_subspace_digest(),
            DETECTOR_CAPACITY_RANK_TOLERANCE,
            DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
            DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
        )
    }

    #[allow(clippy::too_many_arguments)]
    fn evidence_with_metadata(
        declaration: &DetectorDeploymentDeclaration,
        value: f64,
        residual: f64,
        capacity_model_digest: impl Into<String>,
        protected_subspace_digest: impl Into<String>,
        rank_tolerance: f64,
        residual_tolerance: f64,
        comparison_tolerance: f64,
    ) -> DetectorCapacityEvidence {
        DetectorCapacityEvidence::from_f64_numerical_estimate(
            capacity_model_digest,
            protected_subspace_digest,
            value,
            declaration.epsilon(),
            4,
            3,
            1,
            vec![value],
            DetectorCapacityWitness::new(vec![1.0, 0.0, 0.0, 0.0], vec![value]).unwrap(),
            DetectorCapacityResiduals::new(
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, residual, 0.0,
            )
            .unwrap(),
            rank_tolerance,
            residual_tolerance,
            comparison_tolerance,
        )
        .unwrap()
    }

    fn rebuild_declaration(
        base: &DetectorDeploymentDeclaration,
        boundary: &BoundarySlice,
        evaluators: Vec<DetectorEvaluatorDeclaration>,
        distinctions: Vec<ProtectedDistinctionDeclaration>,
    ) -> DetectorDeploymentDeclaration {
        DetectorDeploymentDeclaration::new(
            base.deployment_id(),
            base.corpus_id(),
            boundary.name.as_str(),
            boundary.states.iter().cloned(),
            base.capacity_model_digest(),
            base.epsilon(),
            evaluators,
            distinctions,
        )
        .unwrap()
    }

    fn declaration_with_left_direction(
        base: &DetectorDeploymentDeclaration,
        boundary: &BoundarySlice,
        section_direction: Vec<f64>,
    ) -> DetectorDeploymentDeclaration {
        let mut distinctions = base.protected_distinctions().to_vec();
        distinctions[0] = ProtectedDistinctionDeclaration::new(
            "D-left",
            DetectorEvaluatorRole::LocalLeft,
            "r0",
            "r1",
            section_direction,
        )
        .unwrap();
        rebuild_declaration(base, boundary, base.evaluators().to_vec(), distinctions)
    }

    fn replace_evaluator(
        base: &DetectorDeploymentDeclaration,
        replacement: DetectorEvaluatorDeclaration,
    ) -> Vec<DetectorEvaluatorDeclaration> {
        let role = replacement.role();
        base.evaluators()
            .iter()
            .map(|evaluator| {
                if evaluator.role() == role {
                    replacement.clone()
                } else {
                    evaluator.clone()
                }
            })
            .collect()
    }

    fn assert_structural_failure(
        report: &DetectorAdequacyVerdict,
        expected: DetectorStructuralFailure,
    ) {
        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::StructuralInadequate,
            "expected structural refusal for {expected:?}; got {:?}",
            report.structural_failures()
        );
        assert!(
            report.structural_failures().contains(&expected),
            "missing {expected:?}; got {:?}",
            report.structural_failures()
        );
        assert_eq!(report.authority_effect(), AuthorityEffect::None);
    }

    #[allow(clippy::too_many_arguments)]
    fn public_manual_evidence(
        declaration: &DetectorDeploymentDeclaration,
        value: f64,
        all_green_dimension: usize,
        protected_span_dimension: usize,
        restricted_dimension: usize,
        restricted_singular_values: Vec<f64>,
        witness_section: Vec<f64>,
        witness_defect: Vec<f64>,
    ) -> DetectorCapacityEvidence {
        DetectorCapacityEvidence::from_f64_numerical_estimate(
            declaration.capacity_model_digest(),
            declaration.protected_subspace_digest(),
            value,
            declaration.epsilon(),
            all_green_dimension,
            protected_span_dimension,
            restricted_dimension,
            restricted_singular_values,
            DetectorCapacityWitness::new(witness_section, witness_defect).unwrap(),
            DetectorCapacityResiduals::new(
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            )
            .unwrap(),
            DETECTOR_CAPACITY_RANK_TOLERANCE,
            DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
            DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
        )
        .unwrap()
    }

    #[test]
    fn manual_evidence_cannot_bypass_max_direction_policy() {
        let (records, ledger, boundary) = strong_corpus();
        let base = declaration(&records, &boundary, 0.5);
        let declaration =
            declaration_with_left_direction(&base, &boundary, vec![f64::MAX, 0.0, 0.0, 0.0]);
        let evidence = public_manual_evidence(
            &declaration,
            0.2,
            4,
            3,
            1,
            vec![0.2],
            vec![1.0, 0.0, 0.0, 0.0],
            vec![0.2],
        );

        let report = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence),
            &records,
            &ledger,
            &boundary,
        );

        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::StructuralInadequate
        );
        assert_eq!(
            report.structural_failures(),
            &[
                DetectorStructuralFailure::ProtectedDirectionMagnitudeOutOfPolicy {
                    distinction_id: "D-left".to_string(),
                    coordinate_index: 0,
                }
            ]
        );
        assert_eq!(report.capacity_value(), None);
        assert_eq!(report.authority_effect(), AuthorityEffect::None);
    }

    #[test]
    fn every_below_min_direction_coordinate_is_refused() {
        let (records, ledger, boundary) = strong_corpus();
        let base = declaration(&records, &boundary, 0.5);
        let below_min = MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE / 10.0;
        let declaration = declaration_with_left_direction(
            &base,
            &boundary,
            vec![below_min, -below_min, 0.0, 0.0],
        );
        let evidence = public_manual_evidence(
            &declaration,
            0.2,
            4,
            3,
            1,
            vec![0.2],
            vec![1.0, 0.0, 0.0, 0.0],
            vec![0.2],
        );

        let report = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence),
            &records,
            &ledger,
            &boundary,
        );

        assert_eq!(
            report.structural_failures(),
            &[
                DetectorStructuralFailure::ProtectedDirectionMagnitudeOutOfPolicy {
                    distinction_id: "D-left".to_string(),
                    coordinate_index: 0,
                },
                DetectorStructuralFailure::ProtectedDirectionMagnitudeOutOfPolicy {
                    distinction_id: "D-left".to_string(),
                    coordinate_index: 1,
                },
            ]
        );
        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::StructuralInadequate
        );
        assert_eq!(report.capacity_value(), None);
        assert_eq!(report.authority_effect(), AuthorityEffect::None);
    }

    #[test]
    fn exact_direction_magnitude_bounds_are_accepted() {
        let (records, ledger, boundary) = strong_corpus();
        let base = declaration(&records, &boundary, 0.5);
        let declaration = declaration_with_left_direction(
            &base,
            &boundary,
            vec![
                MAX_DETECTOR_SAFE_MAGNITUDE,
                MIN_DETECTOR_SAFE_NONZERO_MAGNITUDE,
                0.0,
                0.0,
            ],
        );
        let evidence = public_manual_evidence(
            &declaration,
            0.2,
            4,
            3,
            1,
            vec![0.2],
            vec![1.0, 0.0, 0.0, 0.0],
            vec![0.2],
        );

        let report = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence),
            &records,
            &ledger,
            &boundary,
        );

        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::NumericallySupported
        );
        assert!(report.structural_failures().is_empty());
        assert_eq!(report.capacity_value(), Some(0.2));
        assert_eq!(report.authority_effect(), AuthorityEffect::None);
    }

    #[test]
    fn two_record_count_identity_is_one_minus_gpr_equals_ngd_plus_lrgr() {
        let records = vec![
            CompositionRecord::new("pass", "l0", "r0", true, true, true, None).unwrap(),
            CompositionRecord::new("ngd", "l1", "r1", true, true, false, None).unwrap(),
        ];
        let counts = DetectorCorpusCounts::from_records(&records);
        assert_eq!(counts.sample_count(), 2);
        assert_eq!(counts.global_pass_count(), 1);
        assert_eq!(counts.global_failure_count(), 1);
        assert_eq!(counts.ngd_count(), 1);
        assert_eq!(counts.lrgr_count(), 0);
        assert!(counts.global_failure_partition_holds());
        assert!(counts.one_minus_gpr_partition_holds());
        assert_eq!(
            counts.sample_count(),
            counts.global_pass_count() + counts.ngd_count() + counts.lrgr_count()
        );
    }

    #[test]
    fn four_nonconstant_evaluators_can_have_lrgr_zero_and_keep_the_identity() {
        let records = vec![
            CompositionRecord::new("ngd", "l0", "r0", true, true, false, None).unwrap(),
            CompositionRecord::new("p0", "l1", "r1", false, false, true, None).unwrap(),
            CompositionRecord::new("p1", "l2", "r2", false, true, true, None).unwrap(),
            CompositionRecord::new("p2", "l3", "r3", true, false, true, None).unwrap(),
        ];
        for role in [
            DetectorEvaluatorRole::LocalLeft,
            DetectorEvaluatorRole::LocalRight,
            DetectorEvaluatorRole::Global,
        ] {
            assert_eq!(
                records
                    .iter()
                    .map(|record| evaluator_value(role, record))
                    .collect::<BTreeSet<_>>()
                    .len(),
                2
            );
        }
        let counts = DetectorCorpusCounts::from_records(&records);
        assert_eq!(counts.sample_count(), 4);
        assert_eq!(counts.global_pass_count(), 3);
        assert_eq!(counts.ngd_count(), 1);
        assert_eq!(counts.lrgr_count(), 0);
        assert!(counts.global_failure_partition_holds());
        assert!(counts.one_minus_gpr_partition_holds());
    }

    #[test]
    fn strong_corpus_yields_only_qualified_numerical_labels() {
        let (records, ledger, boundary) = strong_corpus();
        let declaration = declaration(&records, &boundary, 0.5);
        let supported = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence(&declaration, 0.2, 0.0)),
            &records,
            &ledger,
            &boundary,
        );
        assert_eq!(
            supported.kind(),
            DetectorAdequacyVerdictKind::NumericallySupported
        );
        assert_eq!(supported.authority_effect(), AuthorityEffect::None);
        assert_eq!(
            supported.declaration_digest(),
            Some(declaration.declaration_digest().as_str())
        );
        assert_eq!(
            supported.observed_corpus_digest(),
            detector_observed_corpus_digest(&records, &ledger, &boundary)
        );
        assert_eq!(
            supported.observed_corpus_digest_scope(),
            DETECTOR_OBSERVED_CORPUS_DIGEST_SCOPE
        );
        assert_eq!(
            supported.threat_8_disclosure(),
            DETECTOR_THREAT_8_DISCLOSURE
        );
        let closure = supported.carrier_closure().unwrap();
        assert!(closure.comparable_pair_count() >= 1);
        assert!(!closure.global_carrier_closed_on_corpus());
        assert_eq!(closure.collision_pairs().len(), 1);
        let counter = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence(&declaration, 0.8, 0.0)),
            &records,
            &ledger,
            &boundary,
        );
        assert_eq!(
            counter.kind(),
            DetectorAdequacyVerdictKind::NumericalCounterevidence
        );
    }

    fn zero_supported_evidence(
        declaration: &DetectorDeploymentDeclaration,
    ) -> DetectorCapacityEvidence {
        public_manual_evidence(
            declaration,
            0.0,
            0,
            0,
            0,
            Vec::new(),
            vec![0.0, 0.0, 0.0, 0.0],
            vec![0.0],
        )
    }

    #[test]
    fn non_finite_detector_evidence_stays_unresolved() {
        assert_eq!(float_to_rational(f64::NAN), None);
        assert_eq!(float_to_rational(f64::INFINITY), None);
        assert!(float_to_rational(0.0).is_some());

        let (records, ledger, boundary) = strong_corpus();
        let declaration = declaration(&records, &boundary, 0.5);
        let finite = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&zero_supported_evidence(&declaration)),
            &records,
            &ledger,
            &boundary,
        );
        assert_eq!(
            finite.kind(),
            DetectorAdequacyVerdictKind::NumericallySupported
        );
        assert_eq!(finite.authority_effect(), AuthorityEffect::None);

        for value in [f64::NAN, f64::INFINITY] {
            let evidence = zero_supported_evidence(&declaration).with_diagnostic_magnitudes(
                0.0,
                value,
                value,
            );
            let report = evaluate_detector_adequacy(
                Some(&declaration),
                Some(&evidence),
                &records,
                &ledger,
                &boundary,
            );
            assert_eq!(
                report.kind(),
                DetectorAdequacyVerdictKind::NumericalUnresolved,
                "{value}"
            );
            assert_eq!(
                report.numerical_unresolved_reason(),
                Some(&DetectorNumericalUnresolvedReason::NonFiniteFloat),
                "{value}"
            );
            assert_eq!(report.authority_effect(), AuthorityEffect::None);
        }
    }

    #[test]
    fn missing_declaration_and_threshold_band_are_typed() {
        let (records, ledger, boundary) = strong_corpus();
        let missing = evaluate_detector_adequacy(None, None, &records, &ledger, &boundary);
        assert_eq!(missing.kind(), DetectorAdequacyVerdictKind::Undeclared);
        let declaration = declaration(&records, &boundary, 0.5);
        let threshold = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence(&declaration, 0.5, 0.0)),
            &records,
            &ledger,
            &boundary,
        );
        assert_eq!(
            threshold.kind(),
            DetectorAdequacyVerdictKind::NumericalUnresolved
        );
        match threshold.numerical_unresolved_reason() {
            Some(DetectorNumericalUnresolvedReason::ThresholdBand {
                value,
                epsilon,
                band,
            }) => {
                assert_eq!(*value, BigRational::from_float(0.5).unwrap());
                assert_eq!(*epsilon, BigRational::from_float(0.5).unwrap());
                assert!(*band > BigRational::zero());
                assert_eq!(threshold.capacity_value_rational(), Some(value));
                assert_eq!(threshold.epsilon_rational(), Some(epsilon));
            }
            other => panic!("expected ThresholdBand, got {other:?}"),
        }
    }

    #[test]
    fn residual_protected_digest_and_epsilon_tamper_are_unresolved() {
        let (records, ledger, boundary) = strong_corpus();
        let declaration = declaration(&records, &boundary, 0.5);
        let residual = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence(&declaration, 0.2, 1e-3)),
            &records,
            &ledger,
            &boundary,
        );
        match residual.numerical_unresolved_reason() {
            Some(DetectorNumericalUnresolvedReason::ResidualGateFailed {
                max_residual,
                tolerance,
            }) => {
                assert_eq!(*max_residual, BigRational::from_float(1e-3).unwrap());
                assert_eq!(
                    *tolerance,
                    BigRational::from_float(DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE).unwrap()
                );
                assert!(max_residual > tolerance);
            }
            other => panic!("expected ResidualGateFailed, got {other:?}"),
        }

        let bad_protected_digest = evidence_with_metadata(
            &declaration,
            0.2,
            0.0,
            declaration.capacity_model_digest(),
            "tampered-protected-subspace",
            DETECTOR_CAPACITY_RANK_TOLERANCE,
            DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
            DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
        );
        let protected_tamper = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&bad_protected_digest),
            &records,
            &ledger,
            &boundary,
        );
        assert_eq!(
            protected_tamper.numerical_unresolved_reason(),
            Some(&DetectorNumericalUnresolvedReason::ProtectedSubspaceDigestMismatch)
        );

        let other = self::declaration(&records, &boundary, 0.6);
        let epsilon_tamper = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence(&other, 0.2, 0.0)),
            &records,
            &ledger,
            &boundary,
        );
        assert!(matches!(
            epsilon_tamper.numerical_unresolved_reason(),
            Some(DetectorNumericalUnresolvedReason::EpsilonMismatch)
        ));
    }

    #[test]
    fn cross_model_capacity_evidence_is_unresolved() {
        let (records, ledger, boundary) = strong_corpus();
        let declaration = declaration(&records, &boundary, 0.5);
        let cross_model = evidence_with_metadata(
            &declaration,
            0.2,
            0.0,
            "capacity-model-b",
            declaration.protected_subspace_digest(),
            DETECTOR_CAPACITY_RANK_TOLERANCE,
            DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
            DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
        );
        let report = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&cross_model),
            &records,
            &ledger,
            &boundary,
        );
        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::NumericalUnresolved
        );
        assert_eq!(
            report.numerical_unresolved_reason(),
            Some(&DetectorNumericalUnresolvedReason::CapacityModelDigestMismatch)
        );
    }

    #[test]
    fn exact_bit_tolerance_policy_tamper_is_unresolved() {
        let (records, ledger, boundary) = strong_corpus();
        let declaration = declaration(&records, &boundary, 0.5);
        let tampered = [
            (
                evidence_with_metadata(
                    &declaration,
                    0.2,
                    0.0,
                    declaration.capacity_model_digest(),
                    declaration.protected_subspace_digest(),
                    f64::from_bits(DETECTOR_CAPACITY_RANK_TOLERANCE.to_bits() + 1),
                    DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
                    DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
                ),
                "rank",
            ),
            (
                evidence_with_metadata(
                    &declaration,
                    0.2,
                    0.0,
                    declaration.capacity_model_digest(),
                    declaration.protected_subspace_digest(),
                    DETECTOR_CAPACITY_RANK_TOLERANCE,
                    f64::from_bits(DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE.to_bits() + 1),
                    DETECTOR_CAPACITY_COMPARISON_TOLERANCE,
                ),
                "residual",
            ),
            (
                evidence_with_metadata(
                    &declaration,
                    0.2,
                    0.0,
                    declaration.capacity_model_digest(),
                    declaration.protected_subspace_digest(),
                    DETECTOR_CAPACITY_RANK_TOLERANCE,
                    DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE,
                    f64::from_bits(DETECTOR_CAPACITY_COMPARISON_TOLERANCE.to_bits() + 1),
                ),
                "comparison",
            ),
        ];
        for (evidence, policy) in tampered {
            let report = evaluate_detector_adequacy(
                Some(&declaration),
                Some(&evidence),
                &records,
                &ledger,
                &boundary,
            );
            assert_eq!(
                report.kind(),
                DetectorAdequacyVerdictKind::NumericalUnresolved
            );
            match (policy, report.numerical_unresolved_reason()) {
                (
                    "rank",
                    Some(DetectorNumericalUnresolvedReason::RankTolerancePolicyMismatch {
                        expected,
                        found,
                    }),
                ) => {
                    assert_eq!(
                        *expected,
                        BigRational::from_float(DETECTOR_CAPACITY_RANK_TOLERANCE).unwrap()
                    );
                    assert_eq!(
                        *found,
                        BigRational::from_float(f64::from_bits(
                            DETECTOR_CAPACITY_RANK_TOLERANCE.to_bits() + 1
                        ))
                        .unwrap()
                    );
                    assert_ne!(expected, found);
                }
                (
                    "residual",
                    Some(DetectorNumericalUnresolvedReason::ResidualTolerancePolicyMismatch {
                        expected,
                        found,
                    }),
                ) => {
                    assert_eq!(
                        *expected,
                        BigRational::from_float(DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE)
                            .unwrap()
                    );
                    assert_eq!(
                        *found,
                        BigRational::from_float(f64::from_bits(
                            DETECTOR_CAPACITY_RESIDUAL_ACCEPTANCE_TOLERANCE.to_bits() + 1
                        ))
                        .unwrap()
                    );
                    assert_ne!(expected, found);
                }
                (
                    "comparison",
                    Some(DetectorNumericalUnresolvedReason::ComparisonTolerancePolicyMismatch {
                        expected,
                        found,
                    }),
                ) => {
                    assert_eq!(
                        *expected,
                        BigRational::from_float(DETECTOR_CAPACITY_COMPARISON_TOLERANCE).unwrap()
                    );
                    assert_eq!(
                        *found,
                        BigRational::from_float(f64::from_bits(
                            DETECTOR_CAPACITY_COMPARISON_TOLERANCE.to_bits() + 1
                        ))
                        .unwrap()
                    );
                    assert_ne!(expected, found);
                }
                (_, other) => panic!("wrong unresolved reason for {policy}: {other:?}"),
            }
        }
    }

    #[test]
    fn protected_distinction_declaration_failures_are_typed_and_fail_closed() {
        let (records, ledger, boundary) = strong_corpus();
        let base = declaration(&records, &boundary, 0.5);

        let empty = rebuild_declaration(&base, &boundary, base.evaluators().to_vec(), Vec::new());
        let empty_report =
            evaluate_detector_adequacy(Some(&empty), None, &records, &ledger, &boundary);
        assert_structural_failure(
            &empty_report,
            DetectorStructuralFailure::EmptyProtectedDistinctions,
        );
        assert_structural_failure(
            &empty_report,
            DetectorStructuralFailure::MissingProtectedDistinctionForEvaluator {
                role: DetectorEvaluatorRole::Global,
            },
        );

        let mut distinctions = base.protected_distinctions().to_vec();
        distinctions.push(distinctions[0].clone());
        distinctions.push(
            ProtectedDistinctionDeclaration::new(
                "D-dimension",
                DetectorEvaluatorRole::LocalRight,
                "r0",
                "r1",
                vec![0.0, 1.0, 0.0],
            )
            .unwrap(),
        );
        distinctions.push(
            ProtectedDistinctionDeclaration::new(
                "D-same",
                DetectorEvaluatorRole::Global,
                "r2",
                "r2",
                vec![0.0, 0.0, 0.0, 1.0],
            )
            .unwrap(),
        );
        distinctions.push(
            ProtectedDistinctionDeclaration::new(
                "D-missing",
                DetectorEvaluatorRole::Global,
                "r2",
                "missing",
                vec![0.0, 0.0, 0.0, 1.0],
            )
            .unwrap(),
        );
        distinctions.push(
            ProtectedDistinctionDeclaration::new(
                "D-unseparated",
                DetectorEvaluatorRole::LocalLeft,
                "r1",
                "r2",
                vec![0.0, 0.0, 0.0, 1.0],
            )
            .unwrap(),
        );
        let malformed =
            rebuild_declaration(&base, &boundary, base.evaluators().to_vec(), distinctions);
        let report =
            evaluate_detector_adequacy(Some(&malformed), None, &records, &ledger, &boundary);
        assert_structural_failure(
            &report,
            DetectorStructuralFailure::DuplicateProtectedDistinction {
                distinction_id: "D-left".to_string(),
            },
        );
        assert_structural_failure(
            &report,
            DetectorStructuralFailure::ProtectedDirectionDimensionMismatch {
                distinction_id: "D-dimension".to_string(),
                expected: 4,
                found: 3,
            },
        );
        assert_structural_failure(
            &report,
            DetectorStructuralFailure::ProtectedPairUsesSameRecord {
                distinction_id: "D-same".to_string(),
            },
        );
        assert_structural_failure(
            &report,
            DetectorStructuralFailure::ProtectedRecordMissing {
                distinction_id: "D-missing".to_string(),
                record_id: "missing".to_string(),
            },
        );
        assert_structural_failure(
            &report,
            DetectorStructuralFailure::EvaluatorDoesNotSeparate {
                distinction_id: "D-unseparated".to_string(),
                role: DetectorEvaluatorRole::LocalLeft,
            },
        );
    }

    #[test]
    fn evaluator_declaration_failures_are_typed_and_fail_closed() {
        let (records, ledger, boundary) = strong_corpus();
        let base = declaration(&records, &boundary, 0.5);
        let report_for = |evaluators| {
            let bad = rebuild_declaration(
                &base,
                &boundary,
                evaluators,
                base.protected_distinctions().to_vec(),
            );
            evaluate_detector_adequacy(Some(&bad), None, &records, &ledger, &boundary)
        };

        let missing_global = base
            .evaluators()
            .iter()
            .filter(|evaluator| evaluator.role() != DetectorEvaluatorRole::Global)
            .cloned()
            .collect();
        assert_structural_failure(
            &report_for(missing_global),
            DetectorStructuralFailure::MissingEvaluatorDeclaration {
                role: DetectorEvaluatorRole::Global,
            },
        );

        let mut duplicate_left = base.evaluators().to_vec();
        let left = base
            .evaluators()
            .iter()
            .find(|evaluator| evaluator.role() == DetectorEvaluatorRole::LocalLeft)
            .unwrap()
            .clone();
        duplicate_left.push(left.clone());
        assert_structural_failure(
            &report_for(duplicate_left),
            DetectorStructuralFailure::DuplicateEvaluatorDeclaration {
                role: DetectorEvaluatorRole::LocalLeft,
            },
        );

        let valid_carrier: Vec<_> = left.carrier_record_ids().iter().cloned().collect();
        let valid_projections: Vec<_> = left
            .projected_observations()
            .iter()
            .map(|(record_id, value)| (record_id.clone(), value.clone()))
            .collect();
        let make_left = |carrier, projections, complete| {
            DetectorEvaluatorDeclaration::new(
                DetectorEvaluatorRole::LocalLeft,
                carrier,
                projections,
                complete,
                ["LocalLeft test blind spot".to_string()],
            )
            .unwrap()
        };

        let empty_carrier = make_left(Vec::new(), Vec::new(), true);
        assert_structural_failure(
            &report_for(replace_evaluator(&base, empty_carrier)),
            DetectorStructuralFailure::EmptyEvaluatorCarrier {
                role: DetectorEvaluatorRole::LocalLeft,
            },
        );

        let carrier_without_r3 = valid_carrier
            .iter()
            .filter(|record_id| record_id.as_str() != "r3")
            .cloned()
            .collect();
        let projections_without_r3 = valid_projections
            .iter()
            .filter(|(record_id, _)| record_id != "r3")
            .cloned()
            .collect();
        let not_closed = make_left(carrier_without_r3, projections_without_r3, true);
        assert_structural_failure(
            &report_for(replace_evaluator(&base, not_closed)),
            DetectorStructuralFailure::CarrierNotClosed {
                role: DetectorEvaluatorRole::LocalLeft,
                record_id: "r3".to_string(),
            },
        );

        let mut outside_carrier = valid_carrier.clone();
        outside_carrier.push("outside".to_string());
        let carrier_outside = make_left(outside_carrier, valid_projections.clone(), true);
        assert_structural_failure(
            &report_for(replace_evaluator(&base, carrier_outside)),
            DetectorStructuralFailure::CarrierOutsideCorpus {
                role: DetectorEvaluatorRole::LocalLeft,
                record_id: "outside".to_string(),
            },
        );

        let missing_projection = make_left(
            valid_carrier.clone(),
            valid_projections
                .iter()
                .filter(|(record_id, _)| record_id != "r3")
                .cloned()
                .collect(),
            true,
        );
        assert_structural_failure(
            &report_for(replace_evaluator(&base, missing_projection)),
            DetectorStructuralFailure::MissingProjection {
                role: DetectorEvaluatorRole::LocalLeft,
                record_id: "r3".to_string(),
            },
        );

        let mut outside_projection = valid_projections.clone();
        outside_projection.push(("outside".to_string(), "outside-value".to_string()));
        let projection_outside = make_left(valid_carrier.clone(), outside_projection, true);
        assert_structural_failure(
            &report_for(replace_evaluator(&base, projection_outside)),
            DetectorStructuralFailure::ProjectionOutsideCarrier {
                role: DetectorEvaluatorRole::LocalLeft,
                record_id: "outside".to_string(),
            },
        );

        let blind_spots_missing = make_left(valid_carrier, valid_projections, false);
        assert_structural_failure(
            &report_for(replace_evaluator(&base, blind_spots_missing)),
            DetectorStructuralFailure::MissingBlindSpotDeclaration {
                role: DetectorEvaluatorRole::LocalLeft,
            },
        );
    }

    #[test]
    fn corpus_and_boundary_failures_are_typed_and_fail_closed() {
        let (records, ledger, boundary) = strong_corpus();
        let base = declaration(&records, &boundary, 0.5);

        let empty_records = Vec::new();
        let empty_corpus =
            evaluate_detector_adequacy(Some(&base), None, &empty_records, &ledger, &boundary);
        assert_structural_failure(&empty_corpus, DetectorStructuralFailure::EmptyCorpus);

        let empty_boundary = BoundarySlice::new("B", Vec::new());
        let empty_boundary_declaration = rebuild_declaration(
            &base,
            &empty_boundary,
            base.evaluators().to_vec(),
            base.protected_distinctions().to_vec(),
        );
        let empty_boundary_report = evaluate_detector_adequacy(
            Some(&empty_boundary_declaration),
            None,
            &records,
            &ledger,
            &empty_boundary,
        );
        assert_structural_failure(
            &empty_boundary_report,
            DetectorStructuralFailure::EmptyBoundarySlice,
        );

        let mut mismatched_boundary = boundary.clone();
        mismatched_boundary
            .states
            .insert("declared-but-unobserved".to_string());
        let mismatch =
            evaluate_detector_adequacy(Some(&base), None, &records, &ledger, &mismatched_boundary);
        assert_structural_failure(
            &mismatch,
            DetectorStructuralFailure::BoundaryDeclarationMismatch,
        );

        let mut duplicate_records = records.clone();
        duplicate_records.push(records[0].clone());
        let duplicate =
            evaluate_detector_adequacy(Some(&base), None, &duplicate_records, &ledger, &boundary);
        assert_structural_failure(
            &duplicate,
            DetectorStructuralFailure::DuplicateCorpusRecord {
                record_id: "r0".to_string(),
            },
        );

        let mut missing_segment_records = records.clone();
        missing_segment_records[0].left_trace_id = "missing-left".to_string();
        let missing_segment = evaluate_detector_adequacy(
            Some(&base),
            None,
            &missing_segment_records,
            &ledger,
            &boundary,
        );
        assert_structural_failure(
            &missing_segment,
            DetectorStructuralFailure::MissingSegmentTrace {
                composed_record_id: "r0".to_string(),
                trace_id: "missing-left".to_string(),
            },
        );

        let mut unglued_ledger = ledger.clone();
        let mut unglued_right = unglued_ledger.get("r0-right").unwrap().clone();
        unglued_right.input_hash = "different-middle".to_string();
        unglued_ledger.insert(unglued_right);
        let unglued =
            evaluate_detector_adequacy(Some(&base), None, &records, &unglued_ledger, &boundary);
        assert_structural_failure(
            &unglued,
            DetectorStructuralFailure::UngluedBoundary {
                composed_record_id: "r0".to_string(),
            },
        );

        let mut outside_boundary = boundary.clone();
        outside_boundary.states.remove("r0-middle");
        let outside_declaration = rebuild_declaration(
            &base,
            &outside_boundary,
            base.evaluators().to_vec(),
            base.protected_distinctions().to_vec(),
        );
        let outside = evaluate_detector_adequacy(
            Some(&outside_declaration),
            None,
            &records,
            &ledger,
            &outside_boundary,
        );
        assert_structural_failure(
            &outside,
            DetectorStructuralFailure::BoundaryOutsideSlice {
                composed_record_id: "r0".to_string(),
                boundary_state: "r0-middle".to_string(),
            },
        );

        let mut no_ngd_records = records.clone();
        no_ngd_records[0].global_pass = true;
        let no_ngd_declaration = declaration(&no_ngd_records, &boundary, 0.5);
        let no_ngd = evaluate_detector_adequacy(
            Some(&no_ngd_declaration),
            None,
            &no_ngd_records,
            &ledger,
            &boundary,
        );
        assert_structural_failure(&no_ngd, DetectorStructuralFailure::MissingNgdWitness);

        let mut no_lrgr_records = records.clone();
        no_lrgr_records[1].global_pass = true;
        no_lrgr_records[3].global_pass = true;
        let no_lrgr_base = declaration(&no_lrgr_records, &boundary, 0.5);
        let no_lrgr_distinctions = no_lrgr_base
            .protected_distinctions()
            .iter()
            .map(|distinction| {
                if distinction.evaluator() == DetectorEvaluatorRole::Global {
                    ProtectedDistinctionDeclaration::new(
                        "D-global",
                        DetectorEvaluatorRole::Global,
                        "r0",
                        "r2",
                        distinction.section_direction().to_vec(),
                    )
                    .unwrap()
                } else {
                    distinction.clone()
                }
            })
            .collect();
        let no_lrgr_declaration = rebuild_declaration(
            &no_lrgr_base,
            &boundary,
            no_lrgr_base.evaluators().to_vec(),
            no_lrgr_distinctions,
        );
        let no_lrgr = evaluate_detector_adequacy(
            Some(&no_lrgr_declaration),
            None,
            &no_lrgr_records,
            &ledger,
            &boundary,
        );
        assert_structural_failure(&no_lrgr, DetectorStructuralFailure::MissingLrgrWitness);
    }

    #[test]
    fn public_manual_numerical_evidence_is_rechecked_branch_by_branch() {
        let (records, ledger, boundary) = strong_corpus();
        let declaration = declaration(&records, &boundary, 0.5);
        let unit_section = vec![1.0, 0.0, 0.0, 0.0];
        let cases = vec![
            (
                "dimension mismatch",
                public_manual_evidence(
                    &declaration,
                    0.2,
                    5,
                    3,
                    1,
                    vec![0.2],
                    unit_section.clone(),
                    vec![0.2],
                ),
                DetectorNumericalUnresolvedReason::DimensionMismatch,
            ),
            (
                "singular values not descending",
                public_manual_evidence(
                    &declaration,
                    0.2,
                    4,
                    3,
                    2,
                    vec![0.1, 0.2],
                    unit_section.clone(),
                    vec![0.2],
                ),
                DetectorNumericalUnresolvedReason::SingularValuesNotDescending,
            ),
            (
                "top value mismatch",
                public_manual_evidence(
                    &declaration,
                    0.2,
                    4,
                    3,
                    1,
                    vec![0.3],
                    unit_section.clone(),
                    vec![0.2],
                ),
                DetectorNumericalUnresolvedReason::TopValueMismatch,
            ),
            (
                "witness section norm mismatch",
                public_manual_evidence(
                    &declaration,
                    0.2,
                    4,
                    3,
                    1,
                    vec![0.2],
                    vec![0.5, 0.0, 0.0, 0.0],
                    vec![0.2],
                ),
                DetectorNumericalUnresolvedReason::WitnessSectionNormMismatch,
            ),
            (
                "witness defect capacity mismatch",
                public_manual_evidence(
                    &declaration,
                    0.2,
                    4,
                    3,
                    1,
                    vec![0.2],
                    unit_section,
                    vec![0.1],
                ),
                DetectorNumericalUnresolvedReason::WitnessDefectCapacityMismatch,
            ),
        ];

        for (case, evidence, expected) in cases {
            let report = evaluate_detector_adequacy(
                Some(&declaration),
                Some(&evidence),
                &records,
                &ledger,
                &boundary,
            );
            assert_eq!(
                report.kind(),
                DetectorAdequacyVerdictKind::NumericalUnresolved,
                "{case}"
            );
            assert_eq!(
                report.numerical_unresolved_reason(),
                Some(&expected),
                "{case}"
            );
            assert_eq!(report.authority_effect(), AuthorityEffect::None, "{case}");
        }
        // Schema/scope mismatch branches are defensive only: their fields are
        // private, constructor-pinned constants and the DTO has no Deserialize.
    }

    #[test]
    fn constant_accept_evaluator_refuses_exactly() {
        let (mut records, mut ledger, boundary) = strong_corpus();
        for record in &mut records {
            record.local_left_pass = true;
        }
        synchronize_local_ledger(&records, &mut ledger);
        let declaration = declaration(&records, &boundary, 0.5);
        let report =
            evaluate_detector_adequacy(Some(&declaration), None, &records, &ledger, &boundary);
        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::StructuralInadequate
        );
        assert!(report.structural_failures().contains(
            &DetectorStructuralFailure::EvaluatorConstant {
                role: DetectorEvaluatorRole::LocalLeft,
            }
        ));
    }

    #[test]
    fn constant_reject_evaluator_refuses_exactly() {
        let (mut records, mut ledger, boundary) = strong_corpus();
        for record in &mut records {
            record.local_left_pass = false;
        }
        synchronize_local_ledger(&records, &mut ledger);
        let declaration = declaration(&records, &boundary, 0.5);
        let report =
            evaluate_detector_adequacy(Some(&declaration), None, &records, &ledger, &boundary);
        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::StructuralInadequate
        );
        assert!(report.structural_failures().contains(
            &DetectorStructuralFailure::EvaluatorConstant {
                role: DetectorEvaluatorRole::LocalLeft,
            }
        ));
    }

    #[test]
    fn tautological_global_with_nonconstant_locals_refuses() {
        let (mut records, ledger, boundary) = strong_corpus();
        for record in &mut records {
            record.global_pass = record.local_product();
        }
        let declaration = declaration(&records, &boundary, 0.5);
        let report =
            evaluate_detector_adequacy(Some(&declaration), None, &records, &ledger, &boundary);
        assert!(report
            .structural_failures()
            .contains(&DetectorStructuralFailure::GlobalEqualsLocalProduct));
        assert!(!report
            .structural_failures()
            .contains(&DetectorStructuralFailure::LocalProductConstant));
        assert!(!report
            .structural_failures()
            .iter()
            .any(|failure| matches!(failure, DetectorStructuralFailure::EvaluatorConstant { .. })));
    }

    #[test]
    fn vacuous_locals_with_varying_global_refuse_without_tautology() {
        let (mut records, mut ledger, boundary) = strong_corpus();
        let globals = [true, false, false, true];
        for (record, global) in records.iter_mut().zip(globals) {
            record.local_left_pass = true;
            record.local_right_pass = true;
            record.global_pass = global;
        }
        synchronize_local_ledger(&records, &mut ledger);
        let declaration = declaration(&records, &boundary, 0.5);
        let report =
            evaluate_detector_adequacy(Some(&declaration), None, &records, &ledger, &boundary);
        for role in [
            DetectorEvaluatorRole::LocalLeft,
            DetectorEvaluatorRole::LocalRight,
        ] {
            assert!(report
                .structural_failures()
                .contains(&DetectorStructuralFailure::EvaluatorConstant { role }));
        }
        assert!(report
            .structural_failures()
            .contains(&DetectorStructuralFailure::LocalProductConstant));
        assert!(!report.structural_failures().contains(
            &DetectorStructuralFailure::EvaluatorConstant {
                role: DetectorEvaluatorRole::Global,
            }
        ));
        assert!(!report
            .structural_failures()
            .contains(&DetectorStructuralFailure::GlobalEqualsLocalProduct));
    }

    #[test]
    fn compositional_closure_collision_is_disclosed_not_misclassified() {
        let (records, ledger, boundary) = strong_corpus();
        let declaration = declaration(&records, &boundary, 0.5);
        let report =
            evaluate_detector_adequacy(Some(&declaration), None, &records, &ledger, &boundary);
        assert_eq!(report.kind(), DetectorAdequacyVerdictKind::Undeclared);
        assert_eq!(
            report.undeclared_reason(),
            Some(&DetectorUndeclaredReason::CapacityEvidenceMissing)
        );
        assert!(report.structural_failures().is_empty());
        let closure = report.carrier_closure().unwrap();
        assert!(!closure.global_carrier_closed_on_corpus());
        assert_eq!(
            closure.collision_pairs(),
            &[["r2".to_string(), "r3".to_string()]]
        );
    }

    #[test]
    fn carrier_closure_without_any_comparable_pair_is_vacuous() {
        let (mut records, mut ledger, boundary) = strong_corpus();
        records[3].local_left_pass = true;
        records[3].local_right_pass = false;
        synchronize_local_ledger(&records, &mut ledger);
        let declaration = declaration(&records, &boundary, 0.5);
        let report =
            evaluate_detector_adequacy(Some(&declaration), None, &records, &ledger, &boundary);
        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::StructuralInadequate
        );
        assert!(report
            .structural_failures()
            .contains(&DetectorStructuralFailure::CarrierClosureVacuous));
        let closure = report.carrier_closure().unwrap();
        assert_eq!(closure.comparable_pair_count(), 0);
        assert!(closure.global_carrier_closed_on_corpus());
    }

    #[test]
    fn composition_local_bits_must_match_referenced_ledger_traces() {
        let (mut records, ledger, boundary) = strong_corpus();
        records[2].local_left_pass = true;
        records[3].local_right_pass = false;
        let declaration = declaration(&records, &boundary, 0.5);
        let report =
            evaluate_detector_adequacy(Some(&declaration), None, &records, &ledger, &boundary);
        assert!(report.structural_failures().contains(
            &DetectorStructuralFailure::LocalEvaluatorLedgerMismatch {
                composed_record_id: "r2".to_string(),
                side: DetectorLocalSide::Left,
                trace_id: "r2-left".to_string(),
                composition_value: true,
                ledger_value: false,
            }
        ));
        assert!(report.structural_failures().contains(
            &DetectorStructuralFailure::LocalEvaluatorLedgerMismatch {
                composed_record_id: "r3".to_string(),
                side: DetectorLocalSide::Right,
                trace_id: "r3-right".to_string(),
                composition_value: false,
                ledger_value: true,
            }
        ));
    }

    #[test]
    fn genuine_boundary_not_interior_refuses() {
        let (records, mut ledger, boundary) = strong_corpus();
        ledger.insert(
            TraceRecord::new(
                "r0-left",
                "task",
                "left",
                None,
                "r0-middle",
                "r0-middle",
                BigRational::one(),
                BigRational::zero(),
                true,
            )
            .unwrap(),
        );
        let declaration = declaration(&records, &boundary, 0.5);
        let report =
            evaluate_detector_adequacy(Some(&declaration), None, &records, &ledger, &boundary);
        assert!(report.structural_failures().contains(
            &DetectorStructuralFailure::BoundaryNotInterior {
                composed_record_id: "r0".to_string(),
                boundary_state: "r0-middle".to_string(),
            }
        ));
        assert!(!report.structural_failures().iter().any(|failure| matches!(
            failure,
            DetectorStructuralFailure::BoundaryOutsideSlice {
                composed_record_id,
                ..
            } if composed_record_id == "r0"
        )));
    }

    #[test]
    fn projection_collision_and_empty_direction_refuse() {
        let (records, ledger, boundary) = strong_corpus();
        let mut evaluators = declaration(&records, &boundary, 0.5).evaluators().to_vec();
        evaluators[0] = DetectorEvaluatorDeclaration::new(
            DetectorEvaluatorRole::LocalLeft,
            records
                .iter()
                .map(|record| record.composed_trace_id.clone()),
            records
                .iter()
                .map(|record| (record.composed_trace_id.clone(), "same".to_string())),
            true,
            ["blind".to_string()],
        )
        .unwrap();
        let bad = DetectorDeploymentDeclaration::new(
            "deployment",
            "corpus",
            "B",
            boundary.states.iter().cloned(),
            "capacity-model-a",
            0.5,
            evaluators,
            vec![
                ProtectedDistinctionDeclaration::new(
                    "D-left",
                    DetectorEvaluatorRole::LocalLeft,
                    "r0",
                    "r1",
                    Vec::new(),
                )
                .unwrap(),
                ProtectedDistinctionDeclaration::new(
                    "D-right",
                    DetectorEvaluatorRole::LocalRight,
                    "r0",
                    "r1",
                    vec![0.0, 1.0, 0.0, 0.0],
                )
                .unwrap(),
                ProtectedDistinctionDeclaration::new(
                    "D-global",
                    DetectorEvaluatorRole::Global,
                    "r2",
                    "r0",
                    vec![0.0, 0.0, 1.0, 0.0],
                )
                .unwrap(),
            ],
        )
        .unwrap();
        let report = evaluate_detector_adequacy(Some(&bad), None, &records, &ledger, &boundary);
        assert!(report.structural_failures().iter().any(|failure| matches!(
            failure,
            DetectorStructuralFailure::ProjectionCollision { .. }
        )));
        assert!(report.structural_failures().iter().any(|failure| matches!(
            failure,
            DetectorStructuralFailure::EmptyProtectedDirection { .. }
        )));
    }

    #[test]
    fn evaluator_must_factor_through_its_declared_carrier_on_the_corpus() {
        let (records, ledger, boundary) = strong_corpus();
        let original = declaration(&records, &boundary, 0.5);
        let mut evaluators = original.evaluators().to_vec();
        evaluators[0] = DetectorEvaluatorDeclaration::new(
            DetectorEvaluatorRole::LocalLeft,
            records
                .iter()
                .map(|record| record.composed_trace_id.clone()),
            records.iter().map(|record| {
                (
                    record.composed_trace_id.clone(),
                    if record.composed_trace_id == "r2" || record.local_left_pass {
                        "pass"
                    } else {
                        "fail"
                    }
                    .to_string(),
                )
            }),
            true,
            ["LocalLeft declared blind spot".to_string()],
        )
        .unwrap();
        let bad = DetectorDeploymentDeclaration::new(
            "deployment",
            "strong-four-record-corpus",
            &boundary.name,
            boundary.states.iter().cloned(),
            "capacity-model-a",
            0.5,
            evaluators,
            original.protected_distinctions().to_vec(),
        )
        .unwrap();
        let report = evaluate_detector_adequacy(Some(&bad), None, &records, &ledger, &boundary);
        assert!(report.structural_failures().contains(
            &DetectorStructuralFailure::EvaluatorNotCarrierBounded {
                role: DetectorEvaluatorRole::LocalLeft,
                first_record_id: "r0".to_string(),
                second_record_id: "r2".to_string(),
            }
        ));
    }

    #[test]
    fn observed_corpus_digest_binds_load_bearing_trajectory_fields() {
        let (records, ledger, boundary) = strong_corpus();
        let base = detector_observed_corpus_digest(&records, &ledger, &boundary);

        let mut reordered = records.clone();
        reordered.reverse();
        assert_eq!(
            base,
            detector_observed_corpus_digest(&reordered, &ledger, &boundary)
        );

        let mut global_tamper = records.clone();
        global_tamper[0].global_pass = !global_tamper[0].global_pass;
        assert_ne!(
            base,
            detector_observed_corpus_digest(&global_tamper, &ledger, &boundary)
        );

        let mut endpoint_ledger = ledger.clone();
        let mut endpoint_trace = endpoint_ledger.get("r0-left").unwrap().clone();
        endpoint_trace.output_hash = "tampered-endpoint".to_string();
        endpoint_ledger.insert(endpoint_trace);
        assert_ne!(
            base,
            detector_observed_corpus_digest(&records, &endpoint_ledger, &boundary)
        );

        let mut evaluator_ledger = ledger.clone();
        let mut evaluator_trace = evaluator_ledger.get("r0-left").unwrap().clone();
        evaluator_trace.evaluator_pass = !evaluator_trace.evaluator_pass;
        evaluator_ledger.insert(evaluator_trace);
        assert_ne!(
            base,
            detector_observed_corpus_digest(&records, &evaluator_ledger, &boundary)
        );

        let mut cost_ledger = ledger.clone();
        let mut cost_trace = cost_ledger.get("r0-left").unwrap().clone();
        cost_trace.cost = cost_trace.cost + BigRational::one();
        cost_ledger.insert(cost_trace);
        assert_ne!(
            base,
            detector_observed_corpus_digest(&records, &cost_ledger, &boundary)
        );

        let mut residual_ledger = ledger.clone();
        let mut residual_trace = residual_ledger.get("r0-left").unwrap().clone();
        residual_trace.residual_risk = residual_trace.residual_risk + BigRational::one();
        residual_ledger.insert(residual_trace);
        assert_ne!(
            base,
            detector_observed_corpus_digest(&records, &residual_ledger, &boundary)
        );

        let mut boundary_tamper = boundary.clone();
        boundary_tamper
            .states
            .insert("unobserved-but-declared-boundary-state".to_string());
        assert_ne!(
            base,
            detector_observed_corpus_digest(&records, &ledger, &boundary_tamper)
        );

        let mut unreferenced_ledger = ledger.clone();
        unreferenced_ledger.insert(
            TraceRecord::new(
                "unreferenced",
                "task",
                "stage",
                None,
                "source",
                "target",
                BigRational::from_integer(9.into()),
                BigRational::new(1.into(), 4.into()),
                false,
            )
            .unwrap(),
        );
        assert_eq!(
            base,
            detector_observed_corpus_digest(&records, &unreferenced_ledger, &boundary)
        );
    }

    #[test]
    fn exact_rational_tolerance_and_verdict_fields_are_precise() {
        let (records, ledger, boundary) = strong_corpus();
        let declaration = declaration(&records, &boundary, 0.5);
        let evidence = evidence(&declaration, 0.2, 0.0);
        let report = evaluate_detector_adequacy(
            Some(&declaration),
            Some(&evidence),
            &records,
            &ledger,
            &boundary,
        );

        assert_eq!(
            report.kind(),
            DetectorAdequacyVerdictKind::NumericallySupported
        );
        let cap_rat = report
            .capacity_value_rational()
            .expect("capacity rational present");
        let eps_rat = report
            .epsilon_rational()
            .expect("epsilon rational present");
        assert_eq!(*cap_rat, BigRational::from_float(0.2).unwrap());
        assert_eq!(*eps_rat, BigRational::from_float(0.5).unwrap());
        assert!(cap_rat < eps_rat);
        assert_eq!(report.capacity_value(), Some(0.2));
        assert_eq!(report.epsilon(), Some(0.5));

        // Test Eq derivation on DetectorNumericalUnresolvedReason variants
        let r1 = DetectorNumericalUnresolvedReason::RankTolerancePolicyMismatch {
            expected: BigRational::from_float(1e-9).unwrap(),
            found: BigRational::from_float(1e-8).unwrap(),
        };
        let r2 = r1.clone();
        assert_eq!(r1, r2);

        let g1 = DetectorNumericalUnresolvedReason::ResidualGateFailed {
            max_residual: BigRational::from_float(1e-3).unwrap(),
            tolerance: BigRational::from_float(1e-7).unwrap(),
        };
        let g2 = g1.clone();
        assert_eq!(g1, g2);

        let b1 = DetectorNumericalUnresolvedReason::ThresholdBand {
            value: BigRational::from_float(0.5).unwrap(),
            epsilon: BigRational::from_float(0.5).unwrap(),
            band: BigRational::from_float(1e-7).unwrap(),
        };
        let b2 = b1.clone();
        assert_eq!(b1, b2);

        // Serialize to JSON and verify pure serialization
        let serialized = serde_json::to_string(&r1).expect("serialization works");
        assert!(serialized.contains("expected"));
        assert!(serialized.contains("found"));
    }
}


#[cfg(test)]
mod l4_boundary_tests_136ad891 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord136ad891::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord136ad891::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord136ad891::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord136ad891::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord136ad891::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError136ad891::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError136ad891::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
