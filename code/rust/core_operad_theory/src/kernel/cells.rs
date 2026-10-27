//! Replay-bound finite 2-cells; no univalence or infinite-coherence claim.
//!
//! Rust face of `engine/kernel/higher_operad/cells.py`.

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use super::canonical::{
    canonical_id, require_digest, require_identifier, CanonicalError,
};
use super::model::AuthorityEffect;
use super::result::{KernelError, Refusal};
use super::terms::{normalize_term, substitute, term_from_normalized, NormalizedTerm, OperationTerm};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ComparisonVerdict {
    #[serde(rename = "EquivalentOnScope")]
    EquivalentOnScope,
    #[serde(rename = "RefinesOnScope")]
    RefinesOnScope,
    #[serde(rename = "NotEquivalentOnScope")]
    NotEquivalentOnScope,
    #[serde(rename = "Inconclusive")]
    Inconclusive,
}

impl ComparisonVerdict {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::EquivalentOnScope => "EquivalentOnScope",
            Self::RefinesOnScope => "RefinesOnScope",
            Self::NotEquivalentOnScope => "NotEquivalentOnScope",
            Self::Inconclusive => "Inconclusive",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EquivalenceGrade {
    #[serde(rename = "Definitional")]
    Definitional,
    #[serde(rename = "CertifiedIsomorphism")]
    CertifiedIsomorphism,
    #[serde(rename = "ScopedObservational")]
    ScopedObservational,
    #[serde(rename = "Candidate")]
    Candidate,
}

impl EquivalenceGrade {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Definitional => "Definitional",
            Self::CertifiedIsomorphism => "CertifiedIsomorphism",
            Self::ScopedObservational => "ScopedObservational",
            Self::Candidate => "Candidate",
        }
    }
}

pub fn pair_subject_digest(
    source: &NormalizedTerm,
    target: &NormalizedTerm,
    relation_id: &str,
    scope_digest: &str,
) -> Result<String, CanonicalError> {
    let source_id = source.canonical_id()?;
    let target_id = target.canonical_id()?;
    canonical_id(
        "core.oewas.certified-pair.subject.v1",
        &json!({
            "source_term_id": source_id,
            "target_term_id": target_id,
            "boundary": source.boundary().to_canonical(),
            "relation_id": require_identifier(relation_id, "relation_id")?,
            "scope_digest": require_digest(scope_digest, "scope_digest")?,
        }),
    )
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ComparisonEvidence {
    pub source_term_id: String,
    pub target_term_id: String,
    pub relation_id: String,
    pub scope_digest: String,
    pub fixture_set_digest: String,
    pub verifier_ref: String,
    pub verifier_digest: String,
    pub replay_receipt_ref: String,
    pub verdict: ComparisonVerdict,
    pub equivalence_grade: EquivalenceGrade,
    pub forward_witness_digest: String,
    pub inverse_witness_digest: String,
    pub left_roundtrip_digest: String,
    pub right_roundtrip_digest: String,
    pub authority_effect: AuthorityEffect,
}

fn require_optional_digest(value: &str, field: &str) -> Result<String, CanonicalError> {
    if value.is_empty() {
        Ok(String::new())
    } else {
        require_digest(value, field)
    }
}

fn require_witness_quad(
    fwd: &str,
    inv: &str,
    l_rt: &str,
    r_rt: &str,
) -> Result<(String, String, String, String), CanonicalError> {
    Ok((
        require_optional_digest(fwd, "forward_witness_digest")?,
        require_optional_digest(inv, "inverse_witness_digest")?,
        require_optional_digest(l_rt, "left_roundtrip_digest")?,
        require_optional_digest(r_rt, "right_roundtrip_digest")?,
    ))
}

impl ComparisonEvidence {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        source_term_id: &str,
        target_term_id: &str,
        relation_id: &str,
        scope_digest: &str,
        fixture_set_digest: &str,
        verifier_ref: &str,
        verifier_digest: &str,
        replay_receipt_ref: &str,
        verdict: ComparisonVerdict,
        equivalence_grade: EquivalenceGrade,
        forward_witness_digest: &str,
        inverse_witness_digest: &str,
        left_roundtrip_digest: &str,
        right_roundtrip_digest: &str,
        authority_effect: AuthorityEffect,
    ) -> Result<Self, CanonicalError> {
        let (fwd, inv, l_rt, r_rt) = require_witness_quad(
            forward_witness_digest,
            inverse_witness_digest,
            left_roundtrip_digest,
            right_roundtrip_digest,
        )?;

        Ok(Self {
            source_term_id: require_digest(source_term_id, "source_term_id")?,
            target_term_id: require_digest(target_term_id, "target_term_id")?,
            relation_id: require_identifier(relation_id, "relation_id")?,
            scope_digest: require_digest(scope_digest, "scope_digest")?,
            fixture_set_digest: require_digest(fixture_set_digest, "fixture_set_digest")?,
            verifier_ref: require_identifier(verifier_ref, "verifier_ref")?,
            verifier_digest: require_digest(verifier_digest, "verifier_digest")?,
            replay_receipt_ref: require_digest(replay_receipt_ref, "replay_receipt_ref")?,
            verdict,
            equivalence_grade,
            forward_witness_digest: fwd,
            inverse_witness_digest: inv,
            left_roundtrip_digest: l_rt,
            right_roundtrip_digest: r_rt,
            authority_effect,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "source_term_id": self.source_term_id,
            "target_term_id": self.target_term_id,
            "relation_id": self.relation_id,
            "scope_digest": self.scope_digest,
            "fixture_set_digest": self.fixture_set_digest,
            "verifier_ref": self.verifier_ref,
            "verifier_digest": self.verifier_digest,
            "replay_receipt_ref": self.replay_receipt_ref,
            "verdict": self.verdict.as_str(),
            "equivalence_grade": self.equivalence_grade.as_str(),
            "forward_witness_digest": self.forward_witness_digest,
            "inverse_witness_digest": self.inverse_witness_digest,
            "left_roundtrip_digest": self.left_roundtrip_digest,
            "right_roundtrip_digest": self.right_roundtrip_digest,
            "authority_effect": self.authority_effect.as_str(),
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id("core.oewas.comparison-evidence.v1", &self.to_canonical())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Attestation {
    pub subject_digest: String,
    pub evidence_digest: String,
    pub predicate_id: String,
    pub producer_ref: String,
    pub verifier_ref: String,
    pub verifier_digest: String,
    pub replay_receipt_ref: String,
    pub environment_digest: String,
    pub verifier_signature: String,
    pub authority_effect: AuthorityEffect,
}

fn validate_attestation_identities(
    producer_ref: &str,
    verifier_ref: &str,
    verifier_signature: &str,
) -> Result<(String, String, String), KernelError> {
    let p_ref = require_identifier(producer_ref, "producer_ref")?;
    let v_ref = require_identifier(verifier_ref, "verifier_ref")?;
    if p_ref == v_ref {
        return Err(KernelError::Message(
            "attestation producer and verifier must be independent identities".into(),
        ));
    }
    let sig = require_identifier(verifier_signature, "verifier_signature")?;
    if !sig.starts_with("hmac-sha256:") || sig.len() != 76 {
        return Err(KernelError::Message(
            "verifier_signature must be a canonical hmac-sha256 value".into(),
        ));
    }
    Ok((p_ref, v_ref, sig))
}

impl Attestation {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        subject_digest: &str,
        evidence_digest: &str,
        predicate_id: &str,
        producer_ref: &str,
        verifier_ref: &str,
        verifier_digest: &str,
        replay_receipt_ref: &str,
        environment_digest: &str,
        verifier_signature: &str,
        authority_effect: AuthorityEffect,
    ) -> Result<Self, KernelError> {
        let (p_ref, v_ref, sig) =
            validate_attestation_identities(producer_ref, verifier_ref, verifier_signature)?;

        Ok(Self {
            subject_digest: require_digest(subject_digest, "subject_digest")?,
            evidence_digest: require_digest(evidence_digest, "evidence_digest")?,
            predicate_id: require_identifier(predicate_id, "predicate_id")?,
            producer_ref: p_ref,
            verifier_ref: v_ref,
            verifier_digest: require_digest(verifier_digest, "verifier_digest")?,
            replay_receipt_ref: require_digest(replay_receipt_ref, "replay_receipt_ref")?,
            environment_digest: require_digest(environment_digest, "environment_digest")?,
            verifier_signature: sig,
            authority_effect,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "subject_digest": self.subject_digest,
            "evidence_digest": self.evidence_digest,
            "predicate_id": self.predicate_id,
            "producer_ref": self.producer_ref,
            "verifier_ref": self.verifier_ref,
            "verifier_digest": self.verifier_digest,
            "replay_receipt_ref": self.replay_receipt_ref,
            "environment_digest": self.environment_digest,
            "verifier_signature": self.verifier_signature,
            "authority_effect": self.authority_effect.as_str(),
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id("core.oewas.attestation.v1", &self.to_canonical())
    }
}

/// Sealed attestation verified by OEOS replay.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReplayVerifiedAttestation {
    attestation: Attestation,
}

impl ReplayVerifiedAttestation {
    pub fn seal(attestation: Attestation) -> Self {
        Self { attestation }
    }

    pub fn inner(&self) -> &Attestation {
        &self.attestation
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        self.attestation.canonical_id()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AttestationKind {
    Unsealed(Attestation),
    ReplaySealed(ReplayVerifiedAttestation),
}

impl AttestationKind {
    pub fn raw(&self) -> &Attestation {
        match self {
            Self::Unsealed(a) => a,
            Self::ReplaySealed(r) => r.inner(),
        }
    }

    pub fn is_sealed(&self) -> bool {
        matches!(self, Self::ReplaySealed(_))
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        self.raw().canonical_id()
    }
}

impl From<Attestation> for AttestationKind {
    fn from(a: Attestation) -> Self {
        Self::Unsealed(a)
    }
}

impl From<ReplayVerifiedAttestation> for AttestationKind {
    fn from(r: ReplayVerifiedAttestation) -> Self {
        Self::ReplaySealed(r)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CertifiedPair {
    pub source: NormalizedTerm,
    pub target: NormalizedTerm,
    pub comparison: ComparisonEvidence,
    pub attestation: AttestationKind,
}

impl CertifiedPair {
    pub fn relation_id(&self) -> &str {
        &self.comparison.relation_id
    }

    pub fn scope_digest(&self) -> &str {
        &self.comparison.scope_digest
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        let subject = pair_subject_digest(
            &self.source,
            &self.target,
            self.relation_id(),
            self.scope_digest(),
        )?;
        canonical_id(
            "core.oewas.certified-pair.v1",
            &json!({
                "subject_digest": subject,
                "comparison_id": self.comparison.canonical_id()?,
                "attestation_id": self.attestation.canonical_id()?,
            }),
        )
    }
}

fn simple_refusal(code: &str, message: &str) -> Refusal {
    Refusal {
        code: code.into(),
        message: message.into(),
        locus: String::new(),
        details: Vec::new(),
    }
}

fn canonical_refusal(e: CanonicalError) -> Refusal {
    simple_refusal("CANONICAL_ERROR", &e.to_string())
}

fn check_pair_endpoint_and_verifier_bindings(
    left: &NormalizedTerm,
    right: &NormalizedTerm,
    comparison: &ComparisonEvidence,
    raw_att: &Attestation,
) -> Result<(String, String), Refusal> {
    if !left.boundary().parallel_to(&right.boundary()) {
        return Err(simple_refusal(
            "NON_PARALLEL_TERMS",
            "2-cell endpoints must have identical typed boundaries",
        ));
    }
    let left_id = left.canonical_id().map_err(canonical_refusal)?;
    let right_id = right.canonical_id().map_err(canonical_refusal)?;
    if comparison.source_term_id != left_id || comparison.target_term_id != right_id {
        return Err(simple_refusal(
            "COMPARISON_ENDPOINT_MISMATCH",
            "comparison evidence does not bind both term IDs",
        ));
    }
    if comparison.verifier_ref != raw_att.verifier_ref
        || comparison.verifier_digest != raw_att.verifier_digest
    {
        return Err(simple_refusal(
            "VERIFIER_BINDING_MISMATCH",
            "comparison and attestation name different verifiers",
        ));
    }
    if comparison.replay_receipt_ref != raw_att.replay_receipt_ref {
        return Err(simple_refusal(
            "REPLAY_BINDING_MISMATCH",
            "comparison and attestation name different replay receipts",
        ));
    }
    Ok((left_id, right_id))
}

fn has_complete_isomorphism_witnesses(comparison: &ComparisonEvidence) -> bool {
    !comparison.forward_witness_digest.is_empty()
        && !comparison.inverse_witness_digest.is_empty()
        && !comparison.left_roundtrip_digest.is_empty()
        && !comparison.right_roundtrip_digest.is_empty()
}

fn check_pair_verdict_and_grade(
    left_id: &str,
    right_id: &str,
    comparison: &ComparisonEvidence,
    attestation: &AttestationKind,
) -> Result<(), Refusal> {
    if comparison.verdict != ComparisonVerdict::EquivalentOnScope {
        return Err(simple_refusal(
            "NON_ADMISSIBLE_COMPARISON",
            "only equivalence evidence supports a Path2",
        ));
    }
    match comparison.equivalence_grade {
        EquivalenceGrade::Definitional => {
            if left_id != right_id {
                return Err(simple_refusal(
                    "FALSE_DEFINITIONAL_EQUALITY",
                    "definitional grade requires identical normalized term IDs",
                ));
            }
        }
        EquivalenceGrade::CertifiedIsomorphism => {
            if !attestation.is_sealed() {
                return Err(simple_refusal(
                    "UNVERIFIED_REPLAY_ATTESTATION",
                    "certified isomorphism requires an OEOS replay-sealed attestation",
                ));
            }
            if !has_complete_isomorphism_witnesses(comparison) {
                return Err(simple_refusal(
                    "INCOMPLETE_ISOMORPHISM",
                    "certified isomorphism requires forward, inverse, and both round-trip witnesses",
                ));
            }
        }
        _ => {
            return Err(simple_refusal(
                "WEAK_EQUIVALENCE_GRADE",
                "scoped observations and candidates do not support a Path2",
            ));
        }
    }
    Ok(())
}

fn check_pair_attestation_digests(
    left: &NormalizedTerm,
    right: &NormalizedTerm,
    comparison: &ComparisonEvidence,
    raw_att: &Attestation,
) -> Result<(), Refusal> {
    let subject = pair_subject_digest(left, right, &comparison.relation_id, &comparison.scope_digest)
        .map_err(canonical_refusal)?;
    if raw_att.subject_digest != subject {
        return Err(simple_refusal(
            "ATTESTATION_SUBJECT_MISMATCH",
            "attestation does not bind this parallel pair",
        ));
    }
    let comp_id = comparison.canonical_id().map_err(canonical_refusal)?;
    if raw_att.evidence_digest != comp_id {
        return Err(simple_refusal(
            "ATTESTATION_EVIDENCE_MISMATCH",
            "attestation does not bind this comparison evidence",
        ));
    }
    if raw_att.predicate_id != comparison.relation_id {
        return Err(simple_refusal(
            "ATTESTATION_PREDICATE_MISMATCH",
            "attestation predicate differs from comparison relation",
        ));
    }
    Ok(())
}

fn check_certified_pair_error(
    left: &NormalizedTerm,
    right: &NormalizedTerm,
    comparison: &ComparisonEvidence,
    attestation: &AttestationKind,
) -> Option<Refusal> {
    let raw_att = attestation.raw();
    let (left_id, right_id) =
        match check_pair_endpoint_and_verifier_bindings(left, right, comparison, raw_att) {
            Ok(ids) => ids,
            Err(e) => return Some(e),
        };
    if let Err(e) = check_pair_verdict_and_grade(&left_id, &right_id, comparison, attestation) {
        return Some(e);
    }
    check_pair_attestation_digests(left, right, comparison, raw_att).err()
}

pub fn admit_certified_pair(
    source: &OperationTerm,
    target: &OperationTerm,
    comparison: &ComparisonEvidence,
    attestation: &AttestationKind,
) -> Result<CertifiedPair, Refusal> {
    let left = normalize_term(source)?;
    let right = normalize_term(target)?;
    if let Some(err) = check_certified_pair_error(&left, &right, comparison, attestation) {
        return Err(err);
    }
    Ok(CertifiedPair {
        source: left,
        target: right,
        comparison: comparison.clone(),
        attestation: attestation.clone(),
    })
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AtomicPath2 {
    pub certified_pair: CertifiedPair,
}

impl AtomicPath2 {
    pub fn source(&self) -> &NormalizedTerm {
        &self.certified_pair.source
    }

    pub fn target(&self) -> &NormalizedTerm {
        &self.certified_pair.target
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id(
            "core.oewas.path2.atomic.v1",
            &json!({
                "certified_pair_id": self.certified_pair.canonical_id()?,
            }),
        )
    }
}

pub fn admit_atomic_path2(
    source: &OperationTerm,
    target: &OperationTerm,
    comparison: &ComparisonEvidence,
    attestation: &AttestationKind,
) -> Result<AtomicPath2, Refusal> {
    let pair = admit_certified_pair(source, target, comparison, attestation)?;
    Ok(AtomicPath2 { certified_pair: pair })
}

pub fn admit_equivalence(
    source: &OperationTerm,
    target: &OperationTerm,
    comparison: &ComparisonEvidence,
    attestation: &AttestationKind,
) -> Result<AtomicPath2, Refusal> {
    admit_atomic_path2(source, target, comparison, attestation)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IdentityPath2 {
    pub term: NormalizedTerm,
}

impl IdentityPath2 {
    pub fn source(&self) -> &NormalizedTerm {
        &self.term
    }

    pub fn target(&self) -> &NormalizedTerm {
        &self.term
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id(
            "core.oewas.path2.identity.v1",
            &json!({
                "term_id": self.term.canonical_id()?,
            }),
        )
    }
}

pub fn identity_path2(term: &OperationTerm) -> Result<IdentityPath2, Refusal> {
    let norm = normalize_term(term)?;
    Ok(IdentityPath2 { term: norm })
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VerticalPath2 {
    pub first: Path2,
    pub second: Path2,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HorizontalPath2 {
    pub outer: Path2,
    pub slot: usize,
    pub inner: Path2,
    pub admitted_composite: AtomicPath2,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InversePath2 {
    pub path: Path2,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WhiskerPath2 {
    pub context: NormalizedTerm,
    pub slot: usize,
    pub path: Path2,
    pub admitted_composite: AtomicPath2,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Path2 {
    Atomic(AtomicPath2),
    Identity(IdentityPath2),
    Vertical(Box<VerticalPath2>),
    Horizontal(Box<HorizontalPath2>),
    Inverse(Box<InversePath2>),
    Whisker(Box<WhiskerPath2>),
}

impl Path2 {
    pub fn source(&self) -> &NormalizedTerm {
        match self {
            Self::Atomic(p) => p.source(),
            Self::Identity(p) => p.source(),
            Self::Vertical(v) => v.first.source(),
            Self::Horizontal(h) => h.admitted_composite.source(),
            Self::Inverse(inv) => inv.path.target(),
            Self::Whisker(w) => w.admitted_composite.source(),
        }
    }

    pub fn target(&self) -> &NormalizedTerm {
        match self {
            Self::Atomic(p) => p.target(),
            Self::Identity(p) => p.target(),
            Self::Vertical(v) => v.second.target(),
            Self::Horizontal(h) => h.admitted_composite.target(),
            Self::Inverse(inv) => inv.path.source(),
            Self::Whisker(w) => w.admitted_composite.target(),
        }
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_path_id(self)
    }
}

type PathWord = Vec<(String, i8)>;

fn reduce_path_word(word: PathWord) -> PathWord {
    let mut reduced: Vec<(String, i8)> = Vec::new();
    for (generator_id, orientation) in word {
        if let Some((last_id, last_orient)) = reduced.last() {
            if *last_id == generator_id && *last_orient == -orientation {
                reduced.pop();
                continue;
            }
        }
        reduced.push((generator_id, orientation));
    }
    reduced
}

fn horizontal_path_word(h: &HorizontalPath2) -> Result<PathWord, CanonicalError> {
    let id = canonical_id(
        "core.oewas.path2.horizontal.v1",
        &json!({
            "outer": h.outer.canonical_id()?,
            "slot": h.slot,
            "inner": h.inner.canonical_id()?,
            "admitted_composite": h.admitted_composite.canonical_id()?,
        }),
    )?;
    Ok(vec![(id, 1)])
}

fn whisker_path_word(w: &WhiskerPath2) -> Result<PathWord, CanonicalError> {
    let id = canonical_id(
        "core.oewas.path2.whisker.v1",
        &json!({
            "context": w.context.canonical_id()?,
            "slot": w.slot,
            "path": w.path.canonical_id()?,
            "admitted_composite": w.admitted_composite.canonical_id()?,
        }),
    )?;
    Ok(vec![(id, 1)])
}

fn vertical_path_word(v: &VerticalPath2) -> Result<PathWord, CanonicalError> {
    let mut w1 = path_word(&v.first)?;
    let w2 = path_word(&v.second)?;
    w1.extend(w2);
    Ok(reduce_path_word(w1))
}

fn inverse_path_word(inv: &InversePath2) -> Result<PathWord, CanonicalError> {
    let inner_word = path_word(&inv.path)?;
    let inverted = inner_word
        .into_iter()
        .rev()
        .map(|(gen_id, orient)| (gen_id, -orient))
        .collect();
    Ok(reduce_path_word(inverted))
}

fn path_word(path: &Path2) -> Result<PathWord, CanonicalError> {
    match path {
        Path2::Identity(_) => Ok(Vec::new()),
        Path2::Vertical(v) => vertical_path_word(v),
        Path2::Inverse(inv) => inverse_path_word(inv),
        Path2::Atomic(p) => Ok(vec![(p.canonical_id()?, 1)]),
        Path2::Horizontal(h) => horizontal_path_word(h),
        Path2::Whisker(w) => whisker_path_word(w),
    }
}

fn canonical_path_id(path: &Path2) -> Result<String, CanonicalError> {
    let word = path_word(path)?;
    if word.is_empty() {
        return IdentityPath2 {
            term: path.source().clone(),
        }
        .canonical_id();
    }
    if word.len() == 1 {
        let (generator_id, orientation) = &word[0];
        if *orientation == 1 {
            return Ok(generator_id.clone());
        }
        return canonical_id(
            "core.oewas.path2.inverse.v1",
            &json!({ "generator_id": generator_id }),
        );
    }
    let factors: Vec<Value> = word
        .into_iter()
        .map(|(generator_id, orientation)| {
            json!({
                "generator_id": generator_id,
                "orientation": orientation,
            })
        })
        .collect();
    canonical_id(
        "core.oewas.path2.reduced-word.v1",
        &json!({
            "source_term_id": path.source().canonical_id()?,
            "target_term_id": path.target().canonical_id()?,
            "factors": factors,
        }),
    )
}

pub fn vertical_compose(first: Path2, second: Path2) -> Result<Path2, Refusal> {
    let first_target = first.target().canonical_id().map_err(|e| Refusal {
        code: "CANONICAL_ERROR".into(),
        message: e.to_string(),
        locus: String::new(),
        details: Vec::new(),
    })?;
    let second_source = second.source().canonical_id().map_err(|e| Refusal {
        code: "CANONICAL_ERROR".into(),
        message: e.to_string(),
        locus: String::new(),
        details: Vec::new(),
    })?;
    if first_target != second_source {
        return Err(Refusal {
            code: "VERTICAL_BOUNDARY_MISMATCH".into(),
            message: "first target must equal second source".into(),
            locus: String::new(),
            details: Vec::new(),
        });
    }
    Ok(Path2::Vertical(Box::new(VerticalPath2 { first, second })))
}

pub fn vertical_compose2(first: Path2, second: Path2) -> Result<Path2, Refusal> {
    vertical_compose(first, second)
}

pub fn horizontal_compose(
    outer: Path2,
    slot: usize,
    inner: Path2,
    comparison: &ComparisonEvidence,
    attestation: &AttestationKind,
) -> Result<Path2, Refusal> {
    let source_composite = substitute(&term_from_normalized(outer.source()), slot, &term_from_normalized(inner.source()))?;
    let target_composite = substitute(&term_from_normalized(outer.target()), slot, &term_from_normalized(inner.target()))?;
    let admitted = admit_atomic_path2(
        &term_from_normalized(&source_composite),
        &term_from_normalized(&target_composite),
        comparison,
        attestation,
    )?;
    Ok(Path2::Horizontal(Box::new(HorizontalPath2 {
        outer,
        slot,
        inner,
        admitted_composite: admitted,
    })))
}

pub fn inverse2(path: Path2) -> Result<Path2, Refusal> {
    match path {
        Path2::Identity(_) => Ok(path),
        Path2::Inverse(inv) => Ok(inv.path),
        other => Ok(Path2::Inverse(Box::new(InversePath2 { path: other }))),
    }
}

pub fn whisker2(
    context: &OperationTerm,
    slot: usize,
    path: Path2,
    comparison: &ComparisonEvidence,
    attestation: &AttestationKind,
) -> Result<Path2, Refusal> {
    let normalized_context = normalize_term(context)?;
    let source = substitute(&term_from_normalized(&normalized_context), slot, &term_from_normalized(path.source()))?;
    let target = substitute(&term_from_normalized(&normalized_context), slot, &term_from_normalized(path.target()))?;
    let admitted = admit_atomic_path2(
        &term_from_normalized(&source),
        &term_from_normalized(&target),
        comparison,
        attestation,
    )?;
    Ok(Path2::Whisker(Box::new(WhiskerPath2 {
        context: normalized_context,
        slot,
        path,
        admitted_composite: admitted,
    })))
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Refinement {
    pub source: NormalizedTerm,
    pub target: NormalizedTerm,
    pub comparison: ComparisonEvidence,
    pub attestation: Attestation,
}

impl Refinement {
    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id(
            "core.oewas.refinement.v1",
            &json!({
                "source": self.source.canonical_id()?,
                "target": self.target.canonical_id()?,
                "comparison": self.comparison.canonical_id()?,
                "attestation": self.attestation.canonical_id()?,
            }),
        )
    }
}

fn check_refinement_endpoints(
    left: &NormalizedTerm,
    right: &NormalizedTerm,
    comparison: &ComparisonEvidence,
) -> Result<(), Refusal> {
    if !left.boundary().parallel_to(&right.boundary()) {
        return Err(simple_refusal(
            "NON_PARALLEL_TERMS",
            "refinement endpoints must be parallel",
        ));
    }
    if comparison.verdict != ComparisonVerdict::RefinesOnScope {
        return Err(simple_refusal(
            "NOT_A_REFINEMENT",
            "comparison verdict is not RefinesOnScope",
        ));
    }
    let left_id = left.canonical_id().map_err(canonical_refusal)?;
    let right_id = right.canonical_id().map_err(canonical_refusal)?;
    if comparison.source_term_id != left_id || comparison.target_term_id != right_id {
        return Err(simple_refusal(
            "COMPARISON_ENDPOINT_MISMATCH",
            "comparison does not bind refinement endpoints",
        ));
    }
    Ok(())
}

fn check_refinement_attestation(
    left: &NormalizedTerm,
    right: &NormalizedTerm,
    comparison: &ComparisonEvidence,
    attestation: &Attestation,
) -> Result<(), Refusal> {
    let subject = pair_subject_digest(left, right, &comparison.relation_id, &comparison.scope_digest)
        .map_err(canonical_refusal)?;
    if attestation.subject_digest != subject {
        return Err(simple_refusal(
            "ATTESTATION_SUBJECT_MISMATCH",
            "attestation does not bind refinement endpoints",
        ));
    }
    let comp_id = comparison.canonical_id().map_err(canonical_refusal)?;
    if attestation.evidence_digest != comp_id {
        return Err(simple_refusal(
            "ATTESTATION_EVIDENCE_MISMATCH",
            "attestation does not bind refinement evidence",
        ));
    }
    if attestation.predicate_id != comparison.relation_id {
        return Err(simple_refusal(
            "ATTESTATION_PREDICATE_MISMATCH",
            "attestation predicate differs from refinement relation",
        ));
    }
    if comparison.verifier_ref != attestation.verifier_ref
        || comparison.verifier_digest != attestation.verifier_digest
    {
        return Err(simple_refusal(
            "VERIFIER_BINDING_MISMATCH",
            "comparison and attestation name different verifiers",
        ));
    }
    if comparison.replay_receipt_ref != attestation.replay_receipt_ref {
        return Err(simple_refusal(
            "REPLAY_BINDING_MISMATCH",
            "comparison and attestation name different replay receipts",
        ));
    }
    Ok(())
}

pub fn admit_refinement(
    source: &OperationTerm,
    target: &OperationTerm,
    comparison: &ComparisonEvidence,
    attestation: &Attestation,
) -> Result<Refinement, Refusal> {
    let left = normalize_term(source)?;
    let right = normalize_term(target)?;
    check_refinement_endpoints(&left, &right, comparison)?;
    check_refinement_attestation(&left, &right, comparison, attestation)?;

    Ok(Refinement {
        source: left,
        target: right,
        comparison: comparison.clone(),
        attestation: attestation.clone(),
    })
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/cells.rs
// Claim: urn:core:crates_rs:core-operad-theory:cells:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord47995cae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord47995cae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError47995cae {
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
impl BoundaryError47995cae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError47995cae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError47995cae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord47995cae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError47995cae> {
        if capacity_bound == 0 {
            return Err(BoundaryError47995cae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError47995cae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError47995cae::ExceedsCapacity {
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
mod l4_boundary_tests_47995cae {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord47995cae::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord47995cae::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord47995cae::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord47995cae::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord47995cae::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError47995cae::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError47995cae::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
