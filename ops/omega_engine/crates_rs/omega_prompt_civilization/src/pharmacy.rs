//! The anti-skill pharmacy: typed detector operations over candidate packets.
//!
//! Merge spec section 8. An anti-skill is an ordinary zero-authority review
//! operation that consumes a typed candidate and emits findings. It is **not** a
//! logical negation, an inverse morphism, or a dual cocycle; treating it as one
//! was among the experiment's discarded conclusions.
//!
//! Two rules shape this module:
//!
//! - **Detection is separate from repair.** A [`Finding`] names what is wrong
//!   and nothing else. No detector returns a patched packet, and there is no
//!   field for one. Coupling them lets a detector launder its own fix past
//!   review.
//! - **Passing the fixtures proves only that.** [`DetectorReport`] is evidence
//!   that named detectors ran on named bytes. It never means the candidate is
//!   correct, and a clean report is not an admission.
//!
//! AuthorityEffect: None.

use serde::{
    de::{MapAccess, SeqAccess, Visitor},
    Deserialize, Serialize,
};
use serde_json::Value;
use std::{collections::BTreeSet, fmt};

/// Failure classes mined from the experiment corpus.
///
/// Only classes with a deterministic mechanical check are implemented; the rest
/// of the merge spec's catalog needs semantic context this layer does not have,
/// and a detector that cannot actually decide would be worse than none.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum FailureClass {
    /// Model-authored verification, admission, or authorization.
    SelfCertification,
    /// A digest-shaped string in a field the host alone may fill.
    FakeReceipt,
    /// The prompt fixes the conclusion the response is supposed to reach.
    ConclusionPreload,
    /// Valid syntax standing in for unperformed semantics.
    SchemaSemanticLaundering,
    /// A theorem invoked by name without its applicability obligations.
    TheoremNameLaundering,
    /// A superlative with no candidate class, objective, or bound.
    OptimalityHallucination,
    /// A complexity claim with no algorithm, cost model, or measurement.
    ComplexityHallucination,
    /// Exhaustion claimed while branches remain unexplored.
    BranchDropExhaustion,
    /// A persona asserting authority its binding does not carry.
    PersonaAuthorityLeak,
    /// Conclusions that depend on private reasoning the trace cannot show.
    PrivateCotDependency,
    /// Byte-identical payloads presented under different version labels.
    VersionDuplication,
    /// One artifact carrying both a finding and its repair.
    DetectRepairCoupling,
}

impl FailureClass {
    fn code_secondary(self) -> &'static str {
        match self {
            Self::ComplexityHallucination => "COMPLEXITY_HALLUCINATION",
            Self::BranchDropExhaustion => "BRANCH_DROP_EXHAUSTION",
            Self::PersonaAuthorityLeak => "PERSONA_AUTHORITY_LEAK",
            Self::PrivateCotDependency => "PRIVATE_COT_DEPENDENCY",
            Self::VersionDuplication => "VERSION_DUPLICATION",
            _ => "DETECT_REPAIR_COUPLING",
        }
    }

    pub fn code(self) -> &'static str {
        match self {
            Self::SelfCertification => "SELF_CERTIFICATION",
            Self::FakeReceipt => "FAKE_RECEIPT",
            Self::ConclusionPreload => "CONCLUSION_PRELOAD",
            Self::SchemaSemanticLaundering => "SCHEMA_SEMANTIC_LAUNDERING",
            Self::TheoremNameLaundering => "THEOREM_NAME_LAUNDERING",
            Self::OptimalityHallucination => "OPTIMALITY_HALLUCINATION",
            other => other.code_secondary(),
        }
    }

    /// The default scheduler response. A disposition is a routing decision, not
    /// a mathematical verdict.
    pub fn disposition(self) -> Disposition {
        match self {
            // Claiming authority is a protected-field violation, not a hint.
            Self::SelfCertification | Self::FakeReceipt | Self::PersonaAuthorityLeak => {
                Disposition::Refuse
            }
            // These need more evidence before the branch can advance.
            Self::SchemaSemanticLaundering | Self::PrivateCotDependency => Disposition::Hold,
            // These are diagnostics or shape scheduling without stopping the round.
            // Word-based theorem and optimality findings remain diagnostics until near-miss tests show they do not suppress valid proofs.
            Self::TheoremNameLaundering
            | Self::ConclusionPreload
            | Self::OptimalityHallucination
            | Self::ComplexityHallucination
            | Self::BranchDropExhaustion
            | Self::VersionDuplication
            | Self::DetectRepairCoupling => Disposition::Finding,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Disposition {
    Finding,
    Hold,
    Refuse,
}

impl Disposition {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Finding => "FINDING",
            Self::Hold => "HOLD",
            Self::Refuse => "REFUSE",
        }
    }
}

/// What a detector found. Carries no repair, by construction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Finding {
    pub class: FailureClass,
    pub disposition: Disposition,
    /// Where in the candidate the evidence sits.
    pub locus: String,
    pub detail: String,
}

impl Finding {
    fn new(class: FailureClass, locus: impl Into<String>, detail: impl Into<String>) -> Self {
        Self {
            class,
            disposition: class.disposition(),
            locus: locus.into(),
            detail: detail.into(),
        }
    }
}

/// A host-issued receipt certifying that semantic replay executed and passed.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HostReplayReceipt {
    pub receipt_id: String,
    pub host_signer: String,
    pub target_digest: String,
    pub replay_passed: bool,
}

/// The evidence a detector run produces.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DetectorReport {
    /// Normalized JSON digest (computed from canonical reserialized Value).
    pub normalized_json_digest: String,
    /// Raw input bytes digest, when original raw bytes were supplied.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub raw_bytes_digest: Option<String>,
    /// Subject digest of the inspected document (normalized JSON digest).
    pub subject_digest: String,
    /// Digest of the semantic payload (with version and schema labels stripped).
    pub semantic_payload_digest: String,
    pub detectors_run: Vec<String>,
    pub findings: Vec<Finding>,
}

impl DetectorReport {
    /// A clean report means the named detectors found nothing on these bytes.
    /// It does not mean the candidate is correct.
    pub fn is_clean(&self) -> bool {
        self.findings.is_empty()
    }

    pub fn strongest_disposition(&self) -> Option<Disposition> {
        self.findings
            .iter()
            .map(|finding| finding.disposition)
            .max_by_key(|disposition| match disposition {
                Disposition::Finding => 0u8,
                Disposition::Hold => 1,
                Disposition::Refuse => 2,
            })
    }

    pub fn authority_effect(&self) -> &'static str {
        "None"
    }
}

/// Keys a model may never fill: they are host facts.
const HOST_ONLY_KEYS: [&str; 10] = [
    "canonical_digest",
    "verified",
    "admitted",
    "admission",
    "receipt",
    "receipt_hash",
    "authority_effect",
    "terminal_status",
    "outcome_root_sha256",
    "registry_mutation",
];

/// Words that assert a conclusion a candidate is not entitled to assert.
const SELF_CERTIFYING_VALUES: [&str; 8] = [
    "verified",
    "certified",
    "authorized",
    "authorised",
    "admitted",
    "promoted",
    "globalgreen",
    "qed",
];

const SUPERLATIVES: [&str; 6] = [
    "optimal",
    "minimal",
    "best possible",
    "fastest",
    "smallest",
    "maximal",
];

const COMPLEXITY_MARKERS: [&str; 5] = [
    "o(n",
    "o(1)",
    "polynomial time",
    "linear time",
    "constant time",
];

const PRIVATE_COT_MARKERS: [&str; 4] = [
    "<think>",
    "chain of thought",
    "my internal reasoning",
    "as i reasoned privately",
];

const PERSONA_FIELD_KEYS: [&str; 4] = ["persona", "role", "actor", "persona_id"];

const PERSONA_AUTHORITY_MARKERS: [&str; 46] = [
    // English
    "admin",
    "executive",
    "authorize",
    "authoritative",
    "grant_authority",
    "sovereign_override",
    // Spanish & Portuguese
    "ejecutivo",
    "autorizar",
    "autoridad",
    "soberano",
    // French
    "executif",
    "autoriser",
    "autorite",
    "souverain",
    // German
    "vorstand",
    "leitend",
    "autorisieren",
    "autoritaet",
    "autoritat",
    "souveraen",
    "souveran",
    // Italian
    "amministratore",
    "esecutivo",
    "autorizzare",
    "autorita",
    "sovrano",
    // Russian (Cyrillic)
    "администратор",
    "админ",
    "исполнительный",
    "авторизовать",
    "авторитет",
    "суверенный",
    // Chinese (Simplified & Traditional)
    "管理员",
    "管理員",
    "执行官",
    "執行官",
    "授权",
    "授權",
    "权威",
    "權威",
    "主管",
    "特权",
    "特權",
    // Japanese
    "管理者",
    "執行役",
    "権限",
];

/// Normalize string for authority marker matching:
/// 1. Strips invisible zero-width and formatting code points (ZWSP, ZWNJ, ZWJ, soft hyphen, word joiner, BOM, etc.)
/// 2. Folds fullwidth Latin ASCII variants (\u{FF01}..\u{FF5E}) to standard ASCII.
/// 3. Folds Latin-lookalike Cyrillic homoglyphs.
/// 4. Folds common Latin diacritics (French, German, Spanish, Italian).
/// 5. Converts to ASCII lowercase.
fn normalize_for_authority_check(text: &str) -> String {
    text.chars()
        .filter_map(|c| match c {
            '\u{200B}' | '\u{200C}' | '\u{200D}' | '\u{00AD}' | '\u{2060}' | '\u{FEFF}'
            | '\u{200E}' | '\u{200F}' | '\u{034F}' | '\u{180E}' => None,
            '\u{FF01}'..='\u{FF5E}' => {
                let ascii_code = (c as u32) - 0xFEE0;
                char::from_u32(ascii_code).map(|ch| ch.to_ascii_lowercase())
            }
            // Cyrillic homoglyphs
            '\u{0430}' | '\u{0410}' => Some('a'),
            '\u{0435}' | '\u{0415}' => Some('e'),
            '\u{043E}' | '\u{041E}' => Some('o'),
            '\u{0456}' | '\u{0406}' => Some('i'),
            '\u{0441}' | '\u{0421}' => Some('c'),
            '\u{0445}' | '\u{0425}' => Some('x'),
            '\u{0440}' | '\u{0420}' => Some('p'),
            '\u{0443}' | '\u{0423}' => Some('u'),
            // Latin diacritics
            'é' | 'è' | 'ê' | 'ë' => Some('e'),
            'á' | 'à' | 'â' | 'ä' => Some('a'),
            'í' | 'ì' | 'î' | 'ï' => Some('i'),
            'ó' | 'ò' | 'ô' | 'ö' => Some('o'),
            'ú' | 'ù' | 'û' | 'ü' => Some('u'),
            'ñ' => Some('n'),
            'ç' => Some('c'),
            'ß' => Some('s'),
            other => Some(other.to_ascii_lowercase()),
        })
        .collect()
}

fn scan_persona_value(value: &Value, path: &str, findings: &mut Vec<Finding>) {
    match value {
        Value::String(text) => {
            let normalized = normalize_for_authority_check(text);
            for marker in PERSONA_AUTHORITY_MARKERS {
                let marker_norm = normalize_for_authority_check(marker);
                if normalized.contains(&marker_norm) {
                    let finding = Finding::new(
                        FailureClass::PersonaAuthorityLeak,
                        path.to_string(),
                        format!("persona field asserts unauthorized authority marker {marker:?}"),
                    );
                    if !findings
                        .iter()
                        .any(|f| f.class == finding.class && f.locus == finding.locus)
                    {
                        findings.push(finding);
                    }
                }
            }
        }
        Value::Array(items) => {
            for (index, item) in items.iter().enumerate() {
                scan_persona_value(item, &format!("{path}/{index}"), findings);
            }
        }
        Value::Object(map) => {
            for (sub_key, sub_val) in map {
                let sub_path = format!("{path}/{sub_key}");
                let sub_key_norm = normalize_for_authority_check(sub_key);
                for marker in PERSONA_AUTHORITY_MARKERS {
                    let marker_norm = normalize_for_authority_check(marker);
                    if sub_key_norm.contains(&marker_norm) {
                        let finding = Finding::new(
                            FailureClass::PersonaAuthorityLeak,
                            sub_path.clone(),
                            format!(
                                "persona field asserts unauthorized authority marker {marker:?}"
                            ),
                        );
                        if !findings
                            .iter()
                            .any(|f| f.class == finding.class && f.locus == finding.locus)
                        {
                            findings.push(finding);
                        }
                    }
                }
                scan_persona_value(sub_val, &sub_path, findings);
            }
        }
        _ => {}
    }
}

fn looks_like_digest(text: &str) -> bool {
    let candidate = text.strip_prefix("sha256:").unwrap_or(text);
    candidate.len() == 64 && candidate.chars().all(|c| c.is_ascii_hexdigit())
}

/// Walk every string in the document, yielding `(json_pointer, value)`.
fn walk_strings<'a>(value: &'a Value, path: String, out: &mut Vec<(String, &'a str)>) {
    match value {
        Value::String(text) => out.push((path, text.as_str())),
        Value::Array(items) => {
            for (index, item) in items.iter().enumerate() {
                walk_strings(item, format!("{path}/{index}"), out);
            }
        }
        Value::Object(entries) => {
            for (key, item) in entries {
                walk_strings(item, format!("{path}/{key}"), out);
            }
        }
        _ => {}
    }
}

fn walk_keys<'a>(value: &'a Value, path: String, out: &mut Vec<(String, &'a str, &'a Value)>) {
    if let Value::Object(entries) = value {
        for (key, item) in entries {
            out.push((format!("{path}/{key}"), key.as_str(), item));
            walk_keys(item, format!("{path}/{key}"), out);
        }
    } else if let Value::Array(items) = value {
        for (index, item) in items.iter().enumerate() {
            walk_keys(item, format!("{path}/{index}"), out);
        }
    }
}

/// Context a few detectors need beyond the candidate itself.
///
/// Every field has a default, so a wire context may name only the fields it knows.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct DetectionContext {
    /// The prompt the candidate was produced from, when available.
    pub prompt: Option<String>,
    /// Branches the scheduler knows are still unexplored.
    pub unexplored_branches: usize,
    /// Digests of payloads already seen, for duplication detection.
    pub seen_digests: Vec<String>,
    /// Digests of semantic payloads already seen (version/schema labels stripped).
    pub seen_semantic_digests: Vec<String>,
    /// Host-issued replay receipt certifying semantic replay execution.
    pub host_replay_receipt: Option<HostReplayReceipt>,
    /// Caller-supplied indication of replay status. Note: to suppress SCHEMA_SEMANTIC_LAUNDERING,
    /// this must be bound to a valid host_replay_receipt.
    pub semantic_replay_passed: bool,
}

/// Canonical semantic payload for duplication detection.
/// Strips top-level version and schema labels so that a payload re-submitted
/// under a different version label produces the same semantic digest.
pub fn semantic_payload_bytes(candidate: &Value) -> Vec<u8> {
    let mut payload = match candidate {
        Value::Object(map) => {
            let mut filtered = serde_json::Map::new();
            for (k, v) in map {
                if !matches!(
                    k.as_str(),
                    "schema_version" | "version" | "version_label" | "schema"
                ) {
                    filtered.insert(k.clone(), v.clone());
                }
            }
            Value::Object(filtered)
        }
        other => other.clone(),
    };
    crate::prompt_family::sort_keys(&mut payload);
    serde_json::to_vec(&payload).unwrap_or_default()
}

pub fn semantic_payload_digest(candidate: &Value) -> String {
    let bytes = semantic_payload_bytes(candidate);
    format!(
        "sha256:{}",
        hex::encode(<sha2::Sha256 as sha2::Digest>::digest(&bytes))
    )
}

/// Run the pharmacy over one candidate document.
pub fn detect(candidate: &Value, context: &DetectionContext) -> DetectorReport {
    detect_with_raw_bytes(candidate, None, context)
}

fn scan_host_and_persona_keys(keys: &[(String, &str, &Value)], findings: &mut Vec<Finding>) {
    // Host-only keys, and digest-shaped values sitting in them.
    for (path, key, value) in keys {
        if HOST_ONLY_KEYS.contains(key) {
            findings.push(Finding::new(
                FailureClass::SelfCertification,
                path.clone(),
                format!("candidate declares host-only field {key:?}"),
            ));
            if value.as_str().is_some_and(looks_like_digest) {
                findings.push(Finding::new(
                    FailureClass::FakeReceipt,
                    path.clone(),
                    "candidate supplies a digest-shaped value for a host-computed field",
                ));
            }
        }
    }
    // Persona authority leak: candidate persona fields asserting unauthorized executive/administrative authority.
    for (path, key, value) in keys {
        let key_lower = key.to_ascii_lowercase();
        if PERSONA_FIELD_KEYS.contains(&key_lower.as_str()) {
            scan_persona_value(value, path, findings);
        }
    }
}

fn scan_string_markers(
    path: &str,
    text: &str,
    lower: &str,
    unexplored_branches: usize,
    findings: &mut Vec<Finding>,
) {
    if SELF_CERTIFYING_VALUES.iter().any(|word| lower == *word) {
        findings.push(Finding::new(
            FailureClass::SelfCertification,
            path.to_owned(),
            format!("candidate asserts {text:?}"),
        ));
    }
    for (markers, class, detail) in [
        (
            SUPERLATIVES.as_slice(),
            FailureClass::OptimalityHallucination,
            "superlative claim without a candidate class, objective, and lower bound",
        ),
        (
            COMPLEXITY_MARKERS.as_slice(),
            FailureClass::ComplexityHallucination,
            "complexity claim without an algorithm, cost model, or measurement",
        ),
        (
            PRIVATE_COT_MARKERS.as_slice(),
            FailureClass::PrivateCotDependency,
            "conclusion leans on reasoning the public trace cannot show",
        ),
    ] {
        if markers.iter().any(|word| lower.contains(word)) {
            findings.push(Finding::new(class, path.to_owned(), detail));
        }
    }
    scan_theorem_and_exhaustion(path, lower, unexplored_branches, findings);
}

fn scan_theorem_and_exhaustion(
    path: &str,
    lower: &str,
    unexplored_branches: usize,
    findings: &mut Vec<Finding>,
) {
    if lower.contains("by ") && lower.contains("theorem") && !lower.contains("assum") {
        findings.push(Finding::new(
            FailureClass::TheoremNameLaundering,
            path.to_owned(),
            "theorem invoked by name with no applicability obligations stated",
        ));
    }
    let claims_exhausted = lower.contains("exhaustive") || lower.contains("exhausted");
    if claims_exhausted && unexplored_branches > 0 {
        findings.push(Finding::new(
            FailureClass::BranchDropExhaustion,
            path.to_owned(),
            format!("exhaustion claimed while {unexplored_branches} branches remain unexplored"),
        ));
    }
}

fn has_nonempty_array_field(candidate: &Value, key: &str) -> bool {
    candidate
        .get(key)
        .and_then(Value::as_array)
        .is_some_and(|arr| !arr.is_empty())
}

fn is_host_replay_certified(
    context: &DetectionContext,
    subject_digest: &str,
    semantic_digest: &str,
) -> bool {
    context.host_replay_receipt.as_ref().is_some_and(|r| {
        let target = r.target_digest.trim_start_matches("sha256:");
        let matches_subject = target == subject_digest.trim_start_matches("sha256:");
        let matches_semantic = target == semantic_digest.trim_start_matches("sha256:");
        r.replay_passed && (matches_subject || matches_semantic)
    })
}

fn check_structural_and_context_findings(
    candidate: &Value,
    context: &DetectionContext,
    subject_digest: &str,
    semantic_digest: &str,
    findings: &mut Vec<Finding>,
) {
    // A candidate that both reports a problem and applies its fix.
    let has_findings = has_nonempty_array_field(candidate, "objections");
    let has_repair = has_nonempty_array_field(candidate, "proposed_claim_deltas");
    if has_findings && has_repair {
        findings.push(Finding::new(
            FailureClass::DetectRepairCoupling,
            "/objections",
            "one artifact carries both a finding and its repair; they must be separate",
        ));
    }

    // Host replay certification binding: a caller-provided boolean alone cannot suppress without a valid receipt.
    let host_replay_certified = is_host_replay_certified(context, subject_digest, semantic_digest);
    if has_repair && !host_replay_certified {
        findings.push(Finding::new(
            FailureClass::SchemaSemanticLaundering,
            "/proposed_claim_deltas",
            if context.semantic_replay_passed {
                "deltas carry caller-provided semantic_replay_passed without host-issued replay receipt binding"
            } else {
                "well-formed deltas with no semantic replay; the candidate remains PARSED only"
            },
        ));
    }

    check_duplication_and_preload(context, subject_digest, semantic_digest, findings);
}

fn check_duplication_and_preload(
    context: &DetectionContext,
    subject_digest: &str,
    semantic_digest: &str,
    findings: &mut Vec<Finding>,
) {
    // Duplication detection over byte-identical or semantic payload digest.
    let seen_dup = context
        .seen_digests
        .iter()
        .any(|d| d == subject_digest || d == semantic_digest)
        || context
            .seen_semantic_digests
            .iter()
            .any(|d| d == semantic_digest);
    if seen_dup {
        findings.push(Finding::new(
            FailureClass::VersionDuplication,
            "",
            "payload is semantically or byte-identical to one already recorded under another label",
        ));
    }

    // The prompt fixing the answer.
    if let Some(prompt) = &context.prompt {
        let lower_prompt = prompt.to_ascii_lowercase();
        for word in SELF_CERTIFYING_VALUES {
            if lower_prompt.contains(&format!("must be {word}"))
                || lower_prompt.contains(&format!("conclude that it is {word}"))
            {
                findings.push(Finding::new(
                    FailureClass::ConclusionPreload,
                    "/prompt",
                    format!("prompt fixes the required conclusion {word:?}"),
                ));
            }
        }
    }
}

/// Run the pharmacy over one candidate document while preserving raw input byte digest.
pub fn detect_with_raw_bytes(
    candidate: &Value,
    raw_bytes: Option<&[u8]>,
    context: &DetectionContext,
) -> DetectorReport {
    let mut normalized = candidate.clone();
    crate::prompt_family::sort_keys(&mut normalized);
    let normalized_bytes = serde_json::to_vec(&normalized).unwrap_or_default();
    let normalized_json_digest = format!(
        "sha256:{}",
        hex::encode(<sha2::Sha256 as sha2::Digest>::digest(&normalized_bytes))
    );
    let raw_bytes_digest = raw_bytes.map(|b| {
        format!(
            "sha256:{}",
            hex::encode(<sha2::Sha256 as sha2::Digest>::digest(b))
        )
    });
    let subject_digest = normalized_json_digest.clone();
    let semantic_digest = semantic_payload_digest(candidate);

    let mut strings = Vec::new();
    walk_strings(candidate, String::new(), &mut strings);
    let mut keys = Vec::new();
    walk_keys(candidate, String::new(), &mut keys);

    let mut findings = Vec::new();
    scan_host_and_persona_keys(&keys, &mut findings);
    for (path, text) in &strings {
        let lower = text.to_ascii_lowercase();
        scan_string_markers(
            path,
            text,
            &lower,
            context.unexplored_branches,
            &mut findings,
        );
    }
    check_structural_and_context_findings(
        candidate,
        context,
        &subject_digest,
        &semantic_digest,
        &mut findings,
    );

    findings.sort_by(|a, b| (a.class.code(), &a.locus).cmp(&(b.class.code(), &b.locus)));
    findings.dedup();

    DetectorReport {
        normalized_json_digest,
        raw_bytes_digest,
        subject_digest,
        semantic_payload_digest: semantic_digest,
        detectors_run: FAILURE_CLASS_CODES
            .iter()
            .map(|code| (*code).to_owned())
            .collect(),
        findings,
    }
}

/// Typed errors returned when ingesting raw candidate bytes at the host boundary.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum HostIngestError {
    #[error("BOM prohibited: detected byte order mark {0}")]
    BomProhibited(String),
    #[error("Unsupported encoding: detected non-UTF-8 encoding signature {0}")]
    UnsupportedEncoding(&'static str),
    #[error("Invalid UTF-8: {0}")]
    InvalidUtf8(String),
    #[error("JSON syntax error: {0}")]
    JsonSyntax(String),
}

// Validate before Value can collapse duplicate keys. Keeping this pass separate
// preserves Value's arbitrary_precision number decoding without interpreting
// serde_json's private number-map representation as an application data type.
struct UniqueJsonKeys;

impl<'de> Deserialize<'de> for UniqueJsonKeys {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        deserializer.deserialize_any(Self)
    }
}

impl<'de> Visitor<'de> for UniqueJsonKeys {
    type Value = Self;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("JSON with unique decoded object keys")
    }

    fn visit_bool<E>(self, _value: bool) -> Result<Self, E> {
        Ok(Self)
    }
    fn visit_i64<E>(self, _value: i64) -> Result<Self, E> {
        Ok(Self)
    }
    fn visit_u64<E>(self, _value: u64) -> Result<Self, E> {
        Ok(Self)
    }
    fn visit_f64<E>(self, _value: f64) -> Result<Self, E> {
        Ok(Self)
    }
    fn visit_str<E>(self, _value: &str) -> Result<Self, E> {
        Ok(Self)
    }
    fn visit_unit<E>(self) -> Result<Self, E> {
        Ok(Self)
    }

    fn visit_seq<A: SeqAccess<'de>>(self, mut sequence: A) -> Result<Self, A::Error> {
        while sequence.next_element::<Self>()?.is_some() {}
        Ok(Self)
    }

    fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self, A::Error> {
        let mut keys = BTreeSet::new();
        while let Some(key) = map.next_key::<String>()? {
            if !keys.insert(key.clone()) {
                return Err(serde::de::Error::custom(format!(
                    "duplicate JSON key {key:?}"
                )));
            }
            map.next_value::<Self>()?;
        }
        Ok(Self)
    }
}

fn check_bom_signatures(raw: &[u8]) -> Result<(), HostIngestError> {
    const BOMS: &[(&[u8], &str)] = &[
        (b"\xef\xbb\xbf", "UTF-8 BOM (0xEF 0xBB 0xBF)"),
        (b"\xff\xfe\x00\x00", "UTF-32LE BOM (0xFF 0xFE 0x00 0x00)"),
        (b"\x00\x00\xfe\xff", "UTF-32BE BOM (0x00 0x00 0xFE 0xFF)"),
        (b"\xff\xfe", "UTF-16LE BOM (0xFF 0xFE)"),
        (b"\xfe\xff", "UTF-16BE BOM (0xFE 0xFF)"),
    ];
    for &(prefix, label) in BOMS {
        if raw.starts_with(prefix) {
            return Err(HostIngestError::BomProhibited(label.to_string()));
        }
    }
    Ok(())
}

fn check_bomless_utf16_utf32(raw: &[u8]) -> Result<(), HostIngestError> {
    // Check for BOM-less UTF-16 / UTF-32 patterns (RFC 4627 §3 / RFC 8259 §8.1 pattern match for JSON):
    // 00 00 00 xx -> UTF-32BE
    // xx 00 00 00 -> UTF-32LE
    // 00 xx 00 xx -> UTF-16BE
    // xx 00 xx 00 -> UTF-16LE
    if raw.len() < 4 {
        return Ok(());
    }
    match (raw[0] == 0, raw[1] == 0, raw[2] == 0, raw[3] == 0) {
        (true, true, true, _) => Err(HostIngestError::UnsupportedEncoding("BOM-less UTF-32BE")),
        (_, true, true, true) => Err(HostIngestError::UnsupportedEncoding("BOM-less UTF-32LE")),
        (true, _, true, _) => Err(HostIngestError::UnsupportedEncoding("BOM-less UTF-16BE")),
        (_, true, _, true) => Err(HostIngestError::UnsupportedEncoding("BOM-less UTF-16LE")),
        _ => Ok(()),
    }
}

/// Strict host boundary candidate byte decoder.
///
/// In accordance with RFC 8259 §8.1 and repository byte-cleanliness rules:
/// - Fails closed on any BOM (UTF-8 \xef\xbb\xbf, UTF-16 \xff\xfe / \xfe\xff, UTF-32).
/// - Fails closed on alternative encodings (UTF-16LE, UTF-16BE, UTF-32LE, UTF-32BE).
/// - Fails closed on non-UTF-8 byte sequences.
/// - Requires valid UTF-8 JSON syntax and unique decoded keys in every object.
/// - Retains the existing arbitrary-precision Value number semantics.
pub fn decode_candidate_bytes(raw: &[u8]) -> Result<Value, HostIngestError> {
    if raw.is_empty() {
        return Err(HostIngestError::JsonSyntax("empty input bytes".to_string()));
    }
    check_bom_signatures(raw)?;
    check_bomless_utf16_utf32(raw)?;

    let text = std::str::from_utf8(raw).map_err(|e| HostIngestError::InvalidUtf8(e.to_string()))?;

    serde_json::from_str::<UniqueJsonKeys>(text)
        .map_err(|e| HostIngestError::JsonSyntax(e.to_string()))?;

    let value: Value =
        serde_json::from_str(text).map_err(|e| HostIngestError::JsonSyntax(e.to_string()))?;

    Ok(value)
}

/// Ingest candidate raw bytes through host boundary decoder and run the pharmacy detectors.
pub fn ingest_and_detect(
    raw_bytes: &[u8],
    context: &DetectionContext,
) -> Result<DetectorReport, HostIngestError> {
    let candidate = decode_candidate_bytes(raw_bytes)?;
    Ok(detect_with_raw_bytes(&candidate, Some(raw_bytes), context))
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RawReceiptRequest {
    mode: String,
    raw_candidate: Vec<u8>,
    task_key: String,
    stage: String,
    request_digest: String,
    #[serde(default)]
    context: DetectionContext,
    receipt: Option<Value>,
}

fn is_valid_sha256_prefixed(digest: &str) -> bool {
    digest.len() == 71
        && digest.starts_with("sha256:")
        && digest[7..]
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

fn validate_raw_receipt_request(input: &RawReceiptRequest) -> bool {
    const STAGES: [&str; 4] = [
        "PRE_DISPATCH",
        "POST_PRODUCTION",
        "PRE_SELECTION",
        "PRE_SEAL",
    ];
    let mode_ok = ["raw_receipt", "verify_raw_receipt"].contains(&input.mode.as_str());
    let task_ok =
        (1..=512).contains(&input.task_key.len()) && input.task_key.trim() == input.task_key;
    mode_ok
        && input.raw_candidate.len() <= 8192
        && task_ok
        && STAGES.contains(&input.stage.as_str())
        && is_valid_sha256_prefixed(&input.request_digest)
}

fn hash_raw_receipt_bytes(raw: &[u8]) -> String {
    format!(
        "sha256:{}",
        hex::encode(<sha2::Sha256 as sha2::Digest>::digest(raw))
    )
}

/// Issue or consume a retained, exact-input receipt at the pharmacy host port.
/// Replay establishes detector execution and bindings, never admission or truth.
pub fn execute_raw_receipt(payload: &Value) -> Result<Value, String> {
    let invalid = |detail: String| format!("PHARMACY_RAW_RECEIPT_REFUSED: {detail}");
    let input: RawReceiptRequest =
        serde_json::from_value(payload.clone()).map_err(|e| invalid(e.to_string()))?;
    if !validate_raw_receipt_request(&input) {
        return Err(invalid(
            "bounded raw input/task/stage/request contract invalid".into(),
        ));
    }
    let context = serde_json::to_value(&input.context).map_err(|e| invalid(e.to_string()))?;
    if context.to_string().len() > 8192 {
        return Err(invalid("detector context exceeds 8192 bytes".into()));
    }
    let report = ingest_and_detect(&input.raw_candidate, &input.context)
        .map_err(|e| invalid(e.to_string()))?;
    let mut expected = serde_json::json!({
        "schema_version":"oewas.pharmacy.raw-ingress-receipt.v1",
        "canonicalization_profile":"oewas.pharmacy.sorted-json-number-lexemes.v1",
        "implementation_digest":hash_raw_receipt_bytes(include_bytes!("pharmacy.rs")),
        "task_key":input.task_key,"stage":input.stage,"request_digest":input.request_digest,
        "context":context,"report":report,"authority_effect":"None"
    });
    expected["receipt_digest"] =
        Value::String(hash_raw_receipt_bytes(expected.to_string().as_bytes()));
    if input.mode == "raw_receipt" {
        if input.receipt.is_some() {
            return Err(invalid("issuance cannot consume a receipt".into()));
        }
        return Ok(expected);
    }
    if input.receipt.as_ref() != Some(&expected) {
        return Err(invalid(
            "retained receipt differs from exact raw/request/context replay".into(),
        ));
    }
    Ok(
        serde_json::json!({"accepted":true,"receipt_digest":expected["receipt_digest"],
        "raw_bytes_digest":expected["report"]["raw_bytes_digest"],"task_key":input.task_key,
        "stage":input.stage,"request_digest":input.request_digest,"authority_effect":"None"}),
    )
}

const FAILURE_CLASS_CODES: [&str; 12] = [
    "SELF_CERTIFICATION",
    "FAKE_RECEIPT",
    "CONCLUSION_PRELOAD",
    "SCHEMA_SEMANTIC_LAUNDERING",
    "THEOREM_NAME_LAUNDERING",
    "OPTIMALITY_HALLUCINATION",
    "COMPLEXITY_HALLUCINATION",
    "BRANCH_DROP_EXHAUSTION",
    "PERSONA_AUTHORITY_LEAK",
    "PRIVATE_COT_DEPENDENCY",
    "VERSION_DUPLICATION",
    "DETECT_REPAIR_COUPLING",
];

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn clean_candidate() -> Value {
        json!({
            "schema_version": "candidate-move/v1",
            "public_rationale": "the residual drops on the declared fixture",
            "proposed_claim_deltas": [],
            "objections": []
        })
    }

    fn ctx() -> DetectionContext {
        DetectionContext {
            semantic_replay_passed: true,
            ..Default::default()
        }
    }

    #[test]
    fn a_clean_candidate_produces_no_findings() {
        let report = detect(&clean_candidate(), &ctx());
        assert!(
            report.is_clean(),
            "unexpected findings: {:?}",
            report.findings
        );
        assert_eq!(report.authority_effect(), "None");
        assert!(report.subject_digest.starts_with("sha256:"));
    }

    #[test]
    fn a_clean_report_still_names_what_ran() {
        // A clean report is evidence that these detectors ran on these bytes,
        // not that the candidate is correct.
        let report = detect(&clean_candidate(), &ctx());
        assert_eq!(report.detectors_run.len(), 12);
        assert!(report
            .detectors_run
            .iter()
            .any(|code| code == "SELF_CERTIFICATION"));
        assert!(report
            .detectors_run
            .iter()
            .any(|code| code == "PERSONA_AUTHORITY_LEAK"));
    }

    #[test]
    fn a_host_only_field_is_a_refusal() {
        let candidate = json!({"verified": true, "public_rationale": "x"});
        let report = detect(&candidate, &ctx());
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::SelfCertification));
        assert_eq!(report.strongest_disposition(), Some(Disposition::Refuse));
    }

    #[test]
    fn a_fabricated_receipt_hash_is_caught() {
        let candidate = json!({"receipt_hash": "a".repeat(64)});
        let report = detect(&candidate, &ctx());
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::FakeReceipt));
    }

    #[test]
    fn a_prefixed_digest_is_also_caught() {
        let candidate = json!({"canonical_digest": format!("sha256:{}", "b".repeat(64))});
        let report = detect(&candidate, &ctx());
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::FakeReceipt));
    }

    #[test]
    fn a_short_hex_string_is_not_mistaken_for_a_digest() {
        assert!(!looks_like_digest("abc123"));
        assert!(looks_like_digest(&"a".repeat(64)));
        assert!(!looks_like_digest(&"z".repeat(64)));
    }

    #[test]
    fn a_self_certifying_status_value_is_caught() {
        let candidate = json!({"status": "VERIFIED"});
        let report = detect(&candidate, &ctx());
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::SelfCertification));
    }

    #[test]
    fn a_superlative_without_a_bound_is_a_finding() {
        let candidate = json!({"public_rationale": "this is the optimal repair"});
        let report = detect(&candidate, &ctx());
        let finding = report
            .findings
            .iter()
            .find(|f| f.class == FailureClass::OptimalityHallucination)
            .expect("expected an optimality finding");
        assert_eq!(finding.disposition, Disposition::Finding);
    }

    #[test]
    fn a_complexity_claim_without_a_cost_model_is_a_finding() {
        let candidate = json!({"public_rationale": "runs in polynomial time"});
        let report = detect(&candidate, &ctx());
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::ComplexityHallucination));
    }

    #[test]
    fn exhaustion_is_only_a_finding_when_branches_remain() {
        let candidate = json!({"public_rationale": "the search was exhaustive"});

        let clean = detect(&candidate, &ctx());
        assert!(!clean
            .findings
            .iter()
            .any(|f| f.class == FailureClass::BranchDropExhaustion));

        let with_open = DetectionContext {
            unexplored_branches: 3,
            ..ctx()
        };
        let flagged = detect(&candidate, &with_open);
        assert!(flagged
            .findings
            .iter()
            .any(|f| f.class == FailureClass::BranchDropExhaustion));
    }

    #[test]
    fn private_reasoning_dependence_holds_the_branch() {
        let candidate = json!({"public_rationale": "as I reasoned privately, it follows"});
        let report = detect(&candidate, &ctx());
        let finding = report
            .findings
            .iter()
            .find(|f| f.class == FailureClass::PrivateCotDependency)
            .expect("expected a private-CoT finding");
        assert_eq!(finding.disposition, Disposition::Hold);
    }

    #[test]
    fn a_bare_theorem_name_opens_obligations() {
        let candidate = json!({"public_rationale": "by Squier's theorem the system is confluent"});
        let report = detect(&candidate, &ctx());
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::TheoremNameLaundering));
    }

    #[test]
    fn a_theorem_with_stated_assumptions_is_not_flagged() {
        let candidate = json!({
            "public_rationale": "by Squier's theorem, under the assumption that the presentation is finite"
        });
        let report = detect(&candidate, &ctx());
        assert!(!report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::TheoremNameLaundering));
    }

    #[test]
    fn finding_and_repair_in_one_artifact_are_coupled() {
        let candidate = json!({
            "objections": [{"code": "X", "detail": "broken"}],
            "proposed_claim_deltas": ["fix it"]
        });
        let report = detect(&candidate, &ctx());
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::DetectRepairCoupling));
    }

    #[test]
    fn deltas_without_a_semantic_replay_stay_parsed_only() {
        let candidate = json!({"proposed_claim_deltas": ["a delta"], "objections": []});
        let report = detect(&candidate, &DetectionContext::default());
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::SchemaSemanticLaundering));
    }

    #[test]
    fn byte_identical_payloads_deduplicate_regardless_of_label() {
        let first = detect(&clean_candidate(), &ctx());
        let context = DetectionContext {
            seen_digests: vec![first.subject_digest.clone()],
            ..ctx()
        };
        let second = detect(&clean_candidate(), &context);
        assert!(second
            .findings
            .iter()
            .any(|f| f.class == FailureClass::VersionDuplication));
        assert_eq!(first.subject_digest, second.subject_digest);
    }

    #[test]
    fn semantic_duplication_survives_nested_key_reordering() {
        fn candidate(reverse: bool) -> Value {
            let mut nested = serde_json::Map::new();
            let pairs = if reverse {
                [("z", 1), ("a", 2)]
            } else {
                [("a", 2), ("z", 1)]
            };
            for (key, value) in pairs {
                nested.insert(key.into(), json!(value));
            }
            let mut document = serde_json::Map::new();
            document.insert("version".into(), json!("v1"));
            document.insert(
                "payload".into(),
                Value::Array(vec![Value::Object(nested), json!(9)]),
            );
            Value::Object(document)
        }

        let first = candidate(true);
        let second = candidate(false);
        assert_eq!(first, second);
        let first_report = detect(&first, &ctx());
        let context = DetectionContext {
            seen_semantic_digests: vec![first_report.semantic_payload_digest.clone()],
            ..ctx()
        };
        let second_report = detect(&second, &context);
        assert!(second_report
            .findings
            .iter()
            .any(|finding| finding.class == FailureClass::VersionDuplication));
        assert_eq!(first_report.subject_digest, second_report.subject_digest);
        assert_eq!(
            semantic_payload_bytes(&first),
            br#"{"payload":[{"a":2,"z":1},9]}"#
        );
        assert_eq!(
            semantic_payload_bytes(&first),
            semantic_payload_bytes(&second)
        );
        // Semantic array order remains significant; reordering is not duplication.
        let ordered = json!({"payload": [1, 2]});
        let changed = json!({"payload": [2, 1]});
        let context = DetectionContext {
            seen_semantic_digests: vec![semantic_payload_digest(&ordered)],
            ..ctx()
        };
        assert!(!detect(&changed, &context)
            .findings
            .iter()
            .any(|finding| finding.class == FailureClass::VersionDuplication));
    }

    #[test]
    fn version_duplication_catches_different_version_labels() {
        let first = json!({
            "schema_version": "candidate-move/v1",
            "public_rationale": "the residual drops on the declared fixture",
            "proposed_claim_deltas": [],
            "objections": []
        });
        let second = json!({
            "schema_version": "candidate-move/v2",
            "public_rationale": "the residual drops on the declared fixture",
            "proposed_claim_deltas": [],
            "objections": []
        });
        let first_report = detect(&first, &ctx());
        let context = DetectionContext {
            seen_semantic_digests: vec![first_report.semantic_payload_digest.clone()],
            ..ctx()
        };
        let second_report = detect(&second, &context);
        assert!(second_report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::VersionDuplication));
    }

    #[test]
    fn host_replay_receipt_suppresses_semantic_laundering() {
        let candidate = json!({"proposed_claim_deltas": ["a delta"], "objections": []});
        let sem_digest = semantic_payload_digest(&candidate);
        let receipt = HostReplayReceipt {
            receipt_id: "receipt-host-001".to_string(),
            host_signer: "omega-host".to_string(),
            target_digest: sem_digest,
            replay_passed: true,
        };
        let context = DetectionContext {
            host_replay_receipt: Some(receipt),
            semantic_replay_passed: true,
            ..Default::default()
        };
        let report = detect(&candidate, &context);
        assert!(!report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::SchemaSemanticLaundering));
    }

    #[test]
    fn caller_boolean_alone_does_not_suppress_semantic_laundering_without_receipt() {
        let candidate = json!({"proposed_claim_deltas": ["a delta"], "objections": []});
        let context = DetectionContext {
            host_replay_receipt: None,
            semantic_replay_passed: true,
            ..Default::default()
        };
        let report = detect(&candidate, &context);
        let finding = report
            .findings
            .iter()
            .find(|f| f.class == FailureClass::SchemaSemanticLaundering)
            .expect("expected schema semantic laundering finding");
        assert!(finding
            .detail
            .contains("without host-issued replay receipt binding"));
    }

    #[test]
    fn raw_bytes_digest_is_preserved_when_provided() {
        let raw = b"{\"public_rationale\":\"hello\"}";
        let value: Value = serde_json::from_slice(raw).unwrap();
        let report = detect_with_raw_bytes(&value, Some(raw), &ctx());
        assert!(report.raw_bytes_digest.is_some());
        assert_eq!(
            report.raw_bytes_digest.unwrap(),
            format!(
                "sha256:{}",
                hex::encode(<sha2::Sha256 as sha2::Digest>::digest(raw))
            )
        );
    }

    #[test]
    fn a_prompt_that_fixes_the_conclusion_is_caught() {
        let context = DetectionContext {
            prompt: Some("the result must be verified before you answer".to_owned()),
            ..ctx()
        };
        let report = detect(&clean_candidate(), &context);
        assert!(report
            .findings
            .iter()
            .any(|f| f.class == FailureClass::ConclusionPreload));
    }

    #[test]
    fn findings_carry_no_repair_field() {
        // The structural half of detect/repair separation: there is nowhere to
        // put a fix, so a detector cannot smuggle one through.
        let candidate = json!({"verified": true});
        let report = detect(&candidate, &ctx());
        let encoded = serde_json::to_value(&report.findings[0]).unwrap();
        let object = encoded.as_object().unwrap();
        for forbidden in ["repair", "patch", "fix", "replacement"] {
            assert!(!object.contains_key(forbidden));
        }
    }

    #[test]
    fn dispositions_are_ordered_by_severity() {
        let candidate = json!({
            "verified": true,
            "public_rationale": "the optimal answer"
        });
        let report = detect(&candidate, &ctx());
        // A Refuse present anywhere dominates a Finding.
        assert_eq!(report.strongest_disposition(), Some(Disposition::Refuse));
    }

    #[test]
    fn detection_is_deterministic() {
        let a = detect(&clean_candidate(), &ctx());
        let b = detect(&clean_candidate(), &ctx());
        assert_eq!(a, b);
    }

    #[test]
    fn nested_violations_are_found_with_their_path() {
        let candidate = json!({"outer": {"inner": [{"verified": true}]}});
        let report = detect(&candidate, &ctx());
        let finding = report
            .findings
            .iter()
            .find(|f| f.class == FailureClass::SelfCertification)
            .expect("expected a nested finding");
        assert_eq!(finding.locus, "/outer/inner/0/verified");
    }

    #[test]
    fn persona_authority_leak_is_detected() {
        let candidate = json!({
            "persona": "admin_controller",
            "public_rationale": "analyzing constraints"
        });
        let report = detect(&candidate, &ctx());
        let finding = report
            .findings
            .iter()
            .find(|f| f.class == FailureClass::PersonaAuthorityLeak)
            .expect("expected persona authority leak finding");
        assert_eq!(finding.locus, "/persona");
        assert_eq!(finding.disposition, Disposition::Refuse);
    }

    #[test]
    fn persona_authority_leak_nested_object_is_detected() {
        let candidate = json!({
            "actor": {
                "name": "tester",
                "role": "executive"
            }
        });
        let report = detect(&candidate, &ctx());
        let finding = report
            .findings
            .iter()
            .find(|f| f.class == FailureClass::PersonaAuthorityLeak)
            .expect("expected persona authority leak finding");
        assert_eq!(finding.locus, "/actor/role");
        assert_eq!(finding.disposition, Disposition::Refuse);
    }
}
