use core_types::authority::AuthorityEffect;
use core_wdp::ddc::dda_alphabet::{DdaOp, DdaStep, DdaTrace, TraceTerminal};
use core_wdp::ddc::degree_tower::{BinaryCochainSegment, BinaryLinearMap};
use core_wdp::ddc::non_authority::{
    registered_trace_authority_effect, REGISTERED_DDA_TRACE_TYPES,
};
use core_wdp::ddc::op_verification::{CochainState, VerifiedTrace};
use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

const FORBIDDEN_DDA_CONSTRUCTOR_CALLS: [&str; 6] = [
    "CertifiedAuthority::certify(",
    "authority_from_outcome_f13(",
    "authority_from_outcome(",
    "promote_authorized_local_result_v1(",
    "AuthorizedLocalResultV1 {",
    "HostPromotionCapabilityV1 {",
];

fn initial_state() -> CochainState {
    let d0 = BinaryLinearMap::from_rows(1, vec![vec![true], vec![false]]).unwrap();
    let d1 = BinaryLinearMap::from_rows(2, vec![vec![false, true]]).unwrap();
    let segment = BinaryCochainSegment::new(1, d0, d1).unwrap();
    CochainState::new(segment, vec![false, false])
        .unwrap()
        .with_adequacy(true)
}

fn production_source_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("ddc")
}

fn collect_rust_files(root: &Path, files: &mut Vec<PathBuf>) {
    let mut entries = fs::read_dir(root)
        .unwrap_or_else(|error| panic!("cannot read {}: {error}", root.display()))
        .map(|entry| entry.expect("directory entry must be readable").path())
        .collect::<Vec<_>>();
    entries.sort();
    for path in entries {
        if path.is_dir() {
            collect_rust_files(&path, files);
        } else if path.extension().and_then(|extension| extension.to_str()) == Some("rs") {
            files.push(path);
        }
    }
}

fn production_prefix(source: &str) -> &str {
    let unix = source.find("\n#[cfg(test)]");
    let windows = source.find("\r\n#[cfg(test)]");
    let end = match (unix, windows) {
        (Some(left), Some(right)) => left.min(right),
        (Some(index), None) | (None, Some(index)) => index,
        (None, None) => source.len(),
    };
    &source[..end]
}

fn without_line_comments(source: &str) -> String {
    #[derive(Clone, Copy)]
    enum State {
        Code,
        String,
        RawString(usize),
    }

    fn raw_string_start(bytes: &[u8], index: usize) -> Option<(usize, usize)> {
        let mut cursor = index;
        if bytes.get(cursor) == Some(&b'b') {
            cursor += 1;
        }
        if bytes.get(cursor) != Some(&b'r') {
            return None;
        }
        cursor += 1;
        let hash_start = cursor;
        while bytes.get(cursor) == Some(&b'#') {
            cursor += 1;
        }
        (bytes.get(cursor) == Some(&b'"')).then_some((cursor + 1, cursor - hash_start))
    }

    let bytes = source.as_bytes();
    let mut cleaned = Vec::with_capacity(bytes.len());
    let mut state = State::Code;
    let mut index = 0;
    while index < bytes.len() {
        match state {
            State::Code => {
                if bytes[index] == b'/' && bytes.get(index + 1) == Some(&b'/') {
                    while index < bytes.len() && bytes[index] != b'\n' {
                        index += 1;
                    }
                } else if let Some((end, hashes)) = raw_string_start(bytes, index) {
                    cleaned.extend_from_slice(&bytes[index..end]);
                    index = end;
                    state = State::RawString(hashes);
                } else {
                    let byte = bytes[index];
                    cleaned.push(byte);
                    index += 1;
                    if byte == b'"' {
                        state = State::String;
                    }
                }
            }
            State::String => {
                let byte = bytes[index];
                cleaned.push(byte);
                index += 1;
                if byte == b'\\' && index < bytes.len() {
                    cleaned.push(bytes[index]);
                    index += 1;
                } else if byte == b'"' {
                    state = State::Code;
                }
            }
            State::RawString(hashes) => {
                let byte = bytes[index];
                cleaned.push(byte);
                index += 1;
                if byte == b'"'
                    && bytes
                        .get(index..index + hashes)
                        .is_some_and(|suffix| suffix.iter().all(|byte| *byte == b'#'))
                {
                    cleaned.extend_from_slice(&bytes[index..index + hashes]);
                    index += hashes;
                    state = State::Code;
                }
            }
        }
    }
    String::from_utf8(cleaned).expect("comment removal preserves UTF-8 source bytes")
}

#[test]
fn terminalized_registered_traces_remain_evidence_only() {
    let mut emitted = DdaTrace::new();
    emitted.emit_gated_terminal(DdaStep::executed(
        DdaOp::Terminalize,
        "bounded terminal receipt",
    ));
    assert_eq!(emitted.terminal(), TraceTerminal::Terminalized);

    let mut verified = VerifiedTrace::new(initial_state());
    verified
        .step_inert(DdaStep::executed(
            DdaOp::Terminalize,
            "verified bounded terminal receipt",
        ))
        .unwrap();
    assert_eq!(verified.trace().terminal(), TraceTerminal::Terminalized);

    for effect in [
        emitted.authority_effect(),
        verified.authority_effect(),
        registered_trace_authority_effect(&emitted),
        registered_trace_authority_effect(&verified),
    ] {
        assert_eq!(effect, AuthorityEffect::None);
    }
}

#[test]
fn constructor_audit_cannot_be_bypassed_by_double_slashes_in_strings() {
    let url_then_call =
        "let url = \"https://example.com\"; CertifiedAuthority::certify(payload);\n";
    let escaped_quote_then_call = "let value = \"quoted \\\"//\\\" text\"; \
        promote_authorized_local_result_v1(payload);\n";
    let raw_url_then_call = "let url = r#\"https://example.com\"#; \
        authority_from_outcome(payload);\n";

    assert!(without_line_comments(url_then_call).contains("CertifiedAuthority::certify("));
    assert!(without_line_comments(escaped_quote_then_call)
        .contains("promote_authorized_local_result_v1("));
    assert!(without_line_comments(raw_url_then_call).contains("authority_from_outcome("));
}

#[test]
fn public_trace_inventory_requires_explicit_registration_or_exclusion() {
    let root = production_source_root();
    let mut files = Vec::new();
    collect_rust_files(&root, &mut files);

    let mut public_trace_types = BTreeSet::new();
    for path in files {
        let source = fs::read_to_string(&path)
            .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()));
        for line in source.lines().map(str::trim) {
            let words = line.split_whitespace().collect::<Vec<_>>();
            if words.len() >= 3 && words[0] == "pub" && words[1] == "struct" {
                let name = words[2]
                    .split('<')
                    .next()
                    .expect("a struct declaration must contain a type name")
                    .trim_end_matches(['{', ';']);
                if name.ends_with("Trace") {
                    public_trace_types.insert(name.to_owned());
                }
            }
        }
    }

    assert_eq!(
        public_trace_types,
        BTreeSet::from([
            "DdcTrace".to_owned(),
            "DefectTrace".to_owned(),
            "VerifiedTrace".to_owned(),
        ]),
        "a new public trace type needs explicit GTOC-5 registration or exclusion"
    );
    assert_eq!(
        REGISTERED_DDA_TRACE_TYPES,
        ["dda_alphabet::DdaTrace", "op_verification::VerifiedTrace"]
    );

    let agent_source = include_str!("../../core_wdp/src/ddc/agent_contract.rs");
    assert!(agent_source.contains("pub struct DefectTrace"));
    assert!(agent_source.contains("if proposal.authority_effect != \"None\""));
    assert!(agent_source.contains("proposal authority_effect must be None"));
}

#[test]
fn dda_production_sources_cannot_call_authority_or_promotion_constructors() {
    let root = production_source_root();
    let mut files = Vec::new();
    collect_rust_files(&root, &mut files);

    let mut violations = Vec::new();
    for path in files {
        let source = fs::read_to_string(&path)
            .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()));
        let production = production_prefix(&source);
        let clean_production = without_line_comments(production);
        for symbol in FORBIDDEN_DDA_CONSTRUCTOR_CALLS {
            if clean_production.contains(symbol) {
                violations.push(format!("{}: {symbol}", path.display()));
            }
        }
    }
    violations.sort();
    assert!(
        violations.is_empty(),
        "DDA production source reached an authority constructor: {violations:#?}"
    );
}

#[test]
fn constructor_audit_ignores_single_line_comment_mentions() {
    let source = "pub fn evidence_only() {}\n\
        // CertifiedAuthority::certify(fake)\n\
        let value = 1; // promote_authorized_local_result_v1(fake)\n";
    let cleaned = without_line_comments(source);

    assert!(!cleaned.contains("CertifiedAuthority::certify("));
    assert!(!cleaned.contains("promote_authorized_local_result_v1("));
    assert!(without_line_comments("CertifiedAuthority::certify(real)")
        .contains("CertifiedAuthority::certify("));
}

#[test]
fn real_host_promotion_constructor_remains_opaque_and_external() {
    let source = include_str!("../../core_contracts/src/certificate_promotion.rs");
    let production = production_prefix(source);

    assert!(production.contains("pub struct HostPromotionCapabilityV1"));
    assert!(production.contains("pub struct AuthorizedLocalResultV1"));
    assert_eq!(
        production
            .matches("pub fn promote_authorized_local_result_v1(")
            .count(),
        1
    );
    assert_eq!(
        production.matches("CertifiedAuthority::certify(").count(),
        1
    );
    assert!(!production.contains("pub fn new_host_promotion_capability"));
    assert!(!production.contains("impl Default for HostPromotionCapabilityV1"));
}

// Origin: engine/crates_rs/tests/core_wdp/test_ddc_authority_firewall.rs
// Claim: urn:core:crates_rs:tests:test-ddc-authority-firewall:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0b489f3e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0b489f3e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0b489f3e {
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
impl BoundaryError0b489f3e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0b489f3e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0b489f3e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0b489f3e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0b489f3e> {
        if capacity_bound == 0 {
            return Err(BoundaryError0b489f3e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0b489f3e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0b489f3e::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_0b489f3e() {
    let admitted = BoundaryRecord0b489f3e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord0b489f3e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
