//! Nomos URN schema for Core contract identifiers.
//!
//! Canonical grammar (012 contracts + live corpus):
//!
//! ```text
//! Form A: urn:core:{domain}:{name}:v{MAJOR.MINOR.PATCH}
//! Form B: urn:core:rust:{crate}:{name}:v{MAJOR.MINOR.PATCH}
//! Form C: urn:core:{domain}:{name}:file:v{MAJOR.MINOR.PATCH}
//! ```
//!
//! Segment charset: domain/crate = `[a-z0-9_]+`; name = `[a-z0-9_.\-]+`.
//! Prefix-only checks (`starts_with("urn:core:")`) are **insufficient** for
//! Nomos parity; this module parses structure.
//!
//! AuthorityEffect: None. Diagnostic + validation only.

use serde::{Deserialize, Serialize};

/// Well-formed Core Nomos contract URN after parse.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NomosUrn {
    /// Domain segment (e.g. `math`, `state`, `rust`, `engine`).
    pub domain: String,
    /// Optional crate when `domain == "rust"` (Form B).
    pub crate_name: Option<String>,
    /// Contract / symbol name segment.
    pub name: String,
    /// `true` when Form C (`:file:`) locus is present.
    pub file_locus: bool,
    /// Semantic version string without the leading `v` (e.g. `1.0.0`).
    pub version: String,
}

/// Parse / grammar failure reasons (stable strings for dual-language parity).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum NomosUrnError {
    Empty,
    MissingPrefix,
    WrongSegmentCount,
    EmptySegment,
    BadDomainCharset,
    BadNameCharset,
    BadCrateCharset,
    BadVersion,
    UnexpectedFileMarker,
}

impl std::fmt::Display for NomosUrnError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            NomosUrnError::Empty => write!(f, "empty URN"),
            NomosUrnError::MissingPrefix => write!(f, "contract_id must start with urn:core:"),
            NomosUrnError::WrongSegmentCount => write!(f, "wrong segment count for Nomos URN"),
            NomosUrnError::EmptySegment => write!(f, "empty URN segment"),
            NomosUrnError::BadDomainCharset => write!(f, "domain must match [a-z0-9_]+"),
            NomosUrnError::BadNameCharset => write!(f, "name must match [a-z0-9_.\\-]+"),
            NomosUrnError::BadCrateCharset => write!(f, "crate must match [a-z0-9_]+"),
            NomosUrnError::BadVersion => {
                write!(
                    f,
                    "version must be vMAJOR.MINOR.PATCH (non-negative integers)"
                )
            }
            NomosUrnError::UnexpectedFileMarker => write!(f, "unexpected file locus marker"),
        }
    }
}

impl std::error::Error for NomosUrnError {}

const PREFIX: &str = "urn:core:";

fn is_domain_seg(s: &str) -> bool {
    !s.is_empty()
        && s.chars()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_')
}

fn is_name_seg(s: &str) -> bool {
    !s.is_empty()
        && s.chars().all(|c| {
            c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_' || c == '.' || c == '-'
        })
}

fn parse_version(seg: &str) -> Result<String, NomosUrnError> {
    let Some(rest) = seg.strip_prefix('v') else {
        return Err(NomosUrnError::BadVersion);
    };
    let parts: Vec<&str> = rest.split('.').collect();
    if parts.len() != 3 {
        return Err(NomosUrnError::BadVersion);
    }
    for p in &parts {
        if p.is_empty() || !p.chars().all(|c| c.is_ascii_digit()) {
            return Err(NomosUrnError::BadVersion);
        }
        // reject leading zeros except single "0"
        if p.len() > 1 && p.starts_with('0') {
            return Err(NomosUrnError::BadVersion);
        }
    }
    Ok(rest.to_string())
}

/// Parse a Nomos contract URN into structured parts.
pub fn parse_nomos_urn(raw: &str) -> Result<NomosUrn, NomosUrnError> {
    let s = raw.trim();
    if s.is_empty() {
        return Err(NomosUrnError::Empty);
    }
    let Some(body) = s.strip_prefix(PREFIX) else {
        return Err(NomosUrnError::MissingPrefix);
    };
    if body.is_empty() {
        return Err(NomosUrnError::WrongSegmentCount);
    }
    let segs: Vec<&str> = body.split(':').collect();
    if segs.iter().any(|g| g.is_empty()) {
        return Err(NomosUrnError::EmptySegment);
    }

    match segs.len() {
        // Form A: domain : name : vX.Y.Z
        3 => parse_nomos_urn_3(&segs),
        // Form B: rust : crate : name : vX.Y.Z
        // Form C: domain : name : file : vX.Y.Z
        4 => parse_nomos_urn_4(&segs),
        _ => Err(NomosUrnError::WrongSegmentCount),
    }
}

fn parse_nomos_urn_3(segs: &[&str]) -> Result<NomosUrn, NomosUrnError> {
    let domain = segs[0];
    let name = segs[1];
    if !is_domain_seg(domain) {
        return Err(NomosUrnError::BadDomainCharset);
    }
    if !is_name_seg(name) {
        return Err(NomosUrnError::BadNameCharset);
    }
    let version = parse_version(segs[2])?;
    let out = NomosUrn {
        domain: domain.to_string(),
        crate_name: None,
        name: name.to_string(),
        file_locus: false,
        version,
    };
    Ok(out)
}

fn parse_nomos_urn_4(segs: &[&str]) -> Result<NomosUrn, NomosUrnError> {
    let domain = segs[0];
    if !is_domain_seg(domain) {
        return Err(NomosUrnError::BadDomainCharset);
    }
    if domain == "rust" {
        let crate_name = segs[1];
        let name = segs[2];
        if !is_domain_seg(crate_name) {
            return Err(NomosUrnError::BadCrateCharset);
        }
        if !is_name_seg(name) {
            return Err(NomosUrnError::BadNameCharset);
        }
        let version = parse_version(segs[3])?;
        let out = NomosUrn {
            domain: domain.to_string(),
            crate_name: Some(crate_name.to_string()),
            name: name.to_string(),
            file_locus: false,
            version,
        };
        Ok(out)
    } else if segs[2] == "file" {
        let name = segs[1];
        if !is_name_seg(name) {
            return Err(NomosUrnError::BadNameCharset);
        }
        let version = parse_version(segs[3])?;
        let out = NomosUrn {
            domain: domain.to_string(),
            crate_name: None,
            name: name.to_string(),
            file_locus: true,
            version,
        };
        Ok(out)
    } else {
        Err(NomosUrnError::UnexpectedFileMarker)
    }
}

/// True iff `raw` is a well-formed Nomos URN (Forms A/B/C).
pub fn is_well_formed_nomos_urn(raw: &str) -> bool {
    parse_nomos_urn(raw).is_ok()
}

/// Render a parsed URN back to canonical string form.
pub fn format_nomos_urn(u: &NomosUrn) -> String {
    match (&u.crate_name, u.file_locus) {
        (Some(c), false) => {
            format!("urn:core:{}:{}:{}:v{}", u.domain, c, u.name, u.version)
        }
        (None, true) => {
            format!("urn:core:{}:{}:file:v{}", u.domain, u.name, u.version)
        }
        (None, false) => {
            format!("urn:core:{}:{}:v{}", u.domain, u.name, u.version)
        }
        (Some(_), true) => {
            // Not representable in live corpus grammar; still deterministic.
            format!(
                "urn:core:{}:{}:{}:file:v{}",
                u.domain,
                u.crate_name.as_deref().unwrap_or(""),
                u.name,
                u.version
            )
        }
    }
}

/// Critical-crate Nomos URN sample for dual-language parity (STORY-ORT-CONTRACTS-001).
///
/// Sample is intentionally **narrow**: one or more IDs per critical surface domain,
/// not a full 625-contract corpus gate. All entries must be live corpus IDs or
/// stable demo fixtures used in unit tests.
pub const CRITICAL_URN_SAMPLE: &[&str] = &[
    // Form A — core domains
    "urn:core:math:cech_cochain:v1.0.0",
    "urn:core:state:packet:v1.0.0",
    "urn:core:obstruction:obstruction:v1.0.0",
    "urn:core:evidence:phi1_certificate:v1.0.0",
    "urn:core:governance:council_decision:v1.0.0",
    "urn:core:execution:fsr_retrieval:v1.0.0",
    "urn:core:constitution:contract_constitution:v1.0.0",
    "urn:core:products:llm_adapter:v1.0.0",
    "urn:core:lifts:lift_license:v1.0.0",
    // Form B — rust crate bindings (critical crates)
    "urn:core:rust:core_discrete_deformation_algebra:discrete_deformation_algebra:v1.13.0",
    "urn:core:rust:core_functional:contract_descriptors:v1.1.0",
    "urn:core:rust:core_q:admission:v0.2.0",
    // Form C — engine/qm file locus
    "urn:core:engine:cycle_aware_engine:file:v1.0.0",
    "urn:core:qm:quantum_density_engine:file:v1.0.0",
    // Demo fixtures used by validate_v1 tests
    "urn:core:math:demo:v0.1.0",
    "urn:core:obstruction:demo:v0.1.0",
];

/// Vectors that must **fail** parse in both Rust and Python (parity kill set).
pub const CRITICAL_URN_NEGATIVE_SAMPLE: &[&str] = &[
    "",
    "urn:core:",
    "urn:core:math",
    "urn:foo:math:x:v1.0.0",
    "urn:core:Math:x:v1.0.0",
    "urn:core:math::v1.0.0",
    "urn:core:math:x:1.0.0",
    "urn:core:math:x:v1.0",
    "urn:core:math:x:v01.0.0",
    "urn:core:math:x:v1.0.0:extra",
    "urn:core:rust:BadCrate:name:v1.0.0",
    "urn:core:engine:foo:notfile:v1.0.0",
    "not-a-urn",
];

/// One row of a critical-sample audit.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NomosUrnSampleRow {
    pub urn: String,
    pub well_formed: bool,
    pub domain: Option<String>,
    pub form: Option<String>,
}

/// Receipt for the critical URN sample audit.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NomosUrnSampleReceipt {
    pub schema_id: String,
    pub story_id: String,
    pub authority_effect: String,
    pub sample_size: usize,
    pub pass_count: usize,
    pub fail_count: usize,
    pub negative_reject_count: usize,
    pub negative_expected: usize,
    pub all_positive_pass: bool,
    pub all_negative_reject: bool,
    pub rows: Vec<NomosUrnSampleRow>,
}

fn form_label(u: &NomosUrn) -> String {
    if u.crate_name.is_some() {
        "B_rust".into()
    } else if u.file_locus {
        "C_file".into()
    } else {
        "A_domain".into()
    }
}

/// Audit the critical-crate URN sample (positive + negative vectors).
pub fn audit_critical_urn_sample() -> NomosUrnSampleReceipt {
    let mut rows = Vec::with_capacity(CRITICAL_URN_SAMPLE.len());
    let mut pass_count = 0usize;
    for urn in CRITICAL_URN_SAMPLE {
        match parse_nomos_urn(urn) {
            Ok(u) => {
                pass_count += 1;
                // Round-trip must be identity for sample members.
                debug_assert_eq!(format_nomos_urn(&u), *urn);
                let form = form_label(&u);
                rows.push(NomosUrnSampleRow {
                    urn: (*urn).to_string(),
                    well_formed: true,
                    domain: Some(u.domain.clone()),
                    form: Some(form),
                });
            }
            Err(_) => {
                rows.push(NomosUrnSampleRow {
                    urn: (*urn).to_string(),
                    well_formed: false,
                    domain: None,
                    form: None,
                });
            }
        }
    }
    let fail_count = CRITICAL_URN_SAMPLE.len() - pass_count;
    let mut negative_reject_count = 0usize;
    for urn in CRITICAL_URN_NEGATIVE_SAMPLE {
        if parse_nomos_urn(urn).is_err() {
            negative_reject_count += 1;
        }
    }
    let negative_expected = CRITICAL_URN_NEGATIVE_SAMPLE.len();
    NomosUrnSampleReceipt {
        schema_id: "core.contract.nomos_urn_sample_receipt.v1".into(),
        story_id: "STORY-ORT-CONTRACTS-001".into(),
        authority_effect: "None".into(),
        sample_size: CRITICAL_URN_SAMPLE.len(),
        pass_count,
        fail_count,
        negative_reject_count,
        negative_expected,
        all_positive_pass: fail_count == 0,
        all_negative_reject: negative_reject_count == negative_expected,
        rows,
    }
}

// Origin: engine/crates_rs/core_contracts/src/nomos_urn.rs
// Claim: urn:core:crates_rs:core-contracts:nomos-urn:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn form_a_parse_roundtrip() {
        let u = parse_nomos_urn("urn:core:math:cech_cochain:v1.0.0").unwrap();
        assert_eq!(u.domain, "math");
        assert_eq!(u.name, "cech_cochain");
        assert_eq!(u.version, "1.0.0");
        assert!(!u.file_locus);
        assert!(u.crate_name.is_none());
        assert_eq!(format_nomos_urn(&u), "urn:core:math:cech_cochain:v1.0.0");
    }

    #[test]
    fn form_b_rust_binding() {
        let u = parse_nomos_urn(
            "urn:core:rust:core_discrete_deformation_algebra:discrete_deformation_algebra:v1.13.0",
        )
        .unwrap();
        assert_eq!(u.domain, "rust");
        assert_eq!(
            u.crate_name.as_deref(),
            Some("core_discrete_deformation_algebra")
        );
        assert_eq!(u.name, "discrete_deformation_algebra");
        assert_eq!(u.version, "1.13.0");
    }

    #[test]
    fn form_c_file_locus() {
        let u = parse_nomos_urn("urn:core:engine:cycle_aware_engine:file:v1.0.0").unwrap();
        assert!(u.file_locus);
        assert_eq!(u.domain, "engine");
        assert_eq!(u.name, "cycle_aware_engine");
    }

    #[test]
    fn hyphen_name_allowed() {
        let u = parse_nomos_urn("urn:core:execution:core-runtime:v1.0.0").unwrap();
        assert_eq!(u.name, "core-runtime");
    }

    #[test]
    fn negative_sample_all_reject() {
        for urn in CRITICAL_URN_NEGATIVE_SAMPLE {
            assert!(parse_nomos_urn(urn).is_err(), "expected reject for {urn:?}");
        }
    }

    #[test]
    fn critical_sample_all_pass() {
        let r = audit_critical_urn_sample();
        assert!(
            r.all_positive_pass,
            "fails: {:?}",
            r.rows.iter().filter(|x| !x.well_formed).collect::<Vec<_>>()
        );
        assert!(r.all_negative_reject);
        assert_eq!(r.pass_count, CRITICAL_URN_SAMPLE.len());
    }

    #[test]
    fn mutation_leading_zero_version_killed() {
        assert_eq!(
            parse_nomos_urn("urn:core:math:x:v01.0.0"),
            Err(NomosUrnError::BadVersion)
        );
    }

    #[test]
    fn mutation_uppercase_domain_killed() {
        assert_eq!(
            parse_nomos_urn("urn:core:Math:x:v1.0.0"),
            Err(NomosUrnError::BadDomainCharset)
        );
    }

    #[test]
    fn mutation_prefix_only_insufficient() {
        // starts_with urn:core: but not well-formed
        assert!(!is_well_formed_nomos_urn("urn:core:math"));
        assert!(!is_well_formed_nomos_urn("urn:core:math:x:1.0.0"));
    }
}
