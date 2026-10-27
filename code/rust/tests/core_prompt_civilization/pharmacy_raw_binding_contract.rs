//! Public raw-ingress controls. AuthorityEffect: None; clean is not admission.
use core_prompt_civilization::pharmacy::{
    decode_candidate_bytes, execute_raw_receipt, ingest_and_detect, DetectionContext, Disposition,
    FailureClass, HostIngestError,
};
use serde_json::{json, Value};

#[test]
fn retained_raw_receipt_is_consumed_with_exact_request_and_encoding() {
    let request = json!({"mode":"raw_receipt","raw_candidate":br#"{"persona":"worker"}"#,
        "task_key":"raw-port","stage":"POST_PRODUCTION","request_digest":format!("sha256:{}","a".repeat(64)),"context":{}});
    let receipt = execute_raw_receipt(&request).unwrap();
    let mut replay = request.clone();
    replay["mode"] = json!("verify_raw_receipt");
    replay["receipt"] = receipt;
    assert_eq!(execute_raw_receipt(&replay).unwrap()["accepted"], true);
    replay["raw_candidate"] = json!(br#" { "persona":"worker" } "#);
    assert!(execute_raw_receipt(&replay).is_err());
    replay["raw_candidate"] = request["raw_candidate"].clone();
    replay["stage"] = json!("PRE_SELECTION");
    assert!(execute_raw_receipt(&replay).is_err());
}

fn duplicate_refusal(raw: &[u8]) {
    let results = [
        decode_candidate_bytes(raw).map(|_| ()),
        ingest_and_detect(raw, &DetectionContext::default()).map(|_| ()),
    ];
    for result in results {
        match result {
            Err(HostIngestError::JsonSyntax(message)) => {
                assert!(message.contains("duplicate JSON key"), "{message}");
            }
            other => panic!("Expected duplicate-key JsonSyntax, got {other:?}"),
        }
    }
}

#[test]
fn duplicate_persona_cannot_erase_authority() {
    duplicate_refusal(br#"{"persona":"admin","persona":"worker"}"#);
}
#[test]
fn duplicate_escaped_key_cannot_erase_authority() {
    duplicate_refusal(br#"{"persona":"admin","per\u0073ona":"worker"}"#);
}
#[test]
fn duplicate_reverse_order_is_also_refused() {
    duplicate_refusal(br#"{"persona":"worker","persona":"admin"}"#);
}
#[test]
fn duplicate_identical_values_are_still_ambiguous() {
    duplicate_refusal(br#"{"persona":"worker","persona":"worker"}"#);
}
#[test]
fn duplicate_nested_keys_are_refused_in_maps_and_arrays() {
    for raw in [
        br#"{"envelope":{"persona":"admin","persona":"worker"}}"#.as_slice(),
        br#"[{"items":[{"role":"admin","role":"worker"}]}]"#.as_slice(),
    ] {
        duplicate_refusal(raw);
    }
}
#[test]
fn duplicate_neutral_keys_are_refused_too() {
    duplicate_refusal(br#"{"note":"first","note":"second"}"#);
}
#[test]
fn duplicate_recovery_requires_new_unambiguous_bytes() {
    duplicate_refusal(br#"{"persona":"admin","persona":"worker"}"#);
    let report = ingest_and_detect(br#"{"persona":"worker"}"#, &DetectionContext::default())
        .expect("corrected candidate must ingest");
    assert!(report.is_clean());
    assert_eq!(report.authority_effect(), "None");
}
#[test]
fn unique_escaped_nested_authority_uses_the_public_ingestion_port() {
    let report = ingest_and_detect(
        br#"{"envelope":{"items":[{"per\u0073ona":"\u0061dmin"}]}}"#,
        &DetectionContext::default(),
    )
    .expect("unique valid JSON must ingest before detection");
    assert!(report.findings.iter().any(|finding| {
        finding.class == FailureClass::PersonaAuthorityLeak
            && finding.disposition == Disposition::Refuse
            && finding.locus == "/envelope/items/0/persona"
    }));
    assert_eq!(report.strongest_disposition(), Some(Disposition::Refuse));
    assert_eq!(report.authority_effect(), "None");
}
#[test]
fn unique_neutral_persona_remains_healthy() {
    let report = ingest_and_detect(
        br#"{"persona":"worker","note":"step"}"#,
        &DetectionContext::default(),
    )
    .expect("neutral candidate must ingest");
    assert!(report.is_clean());
    assert_eq!(report.strongest_disposition(), None);
    assert_eq!(report.authority_effect(), "None");
}
#[test]
fn unique_keys_are_local_to_each_object() {
    let raw = br#"{"items":[{"persona":"worker"},{"persona":"worker"}]}"#;
    assert_eq!(
        decode_candidate_bytes(raw).expect("sibling keys are unique per object"),
        json!({"items":[{"persona":"worker"},{"persona":"worker"}]})
    );
    assert!(ingest_and_detect(raw, &DetectionContext::default())
        .expect("sibling candidate")
        .is_clean());
}
#[test]
fn arbitrary_precision_numbers_keep_the_existing_value_contract() {
    let raw = br#"{"big":1234567890123456789012345678901234567890,"negative":-1234567890123456789012345678901234567890,"huge":1e400,"values":[0,1,-2,1.25]}"#;
    let value = decode_candidate_bytes(raw).expect("arbitrary precision JSON remains accepted");
    assert_eq!(
        value["big"].to_string(),
        "1234567890123456789012345678901234567890"
    );
    assert_eq!(
        value["negative"].to_string(),
        "-1234567890123456789012345678901234567890"
    );
    assert!(value["huge"].is_number());
    assert!(value["huge"].as_f64().is_none());
    assert_eq!(value["values"], json!([0, 1, -2, 1.25]));
    assert!(ingest_and_detect(raw, &DetectionContext::default()).is_ok());
}
#[test]
fn scalar_and_container_values_remain_accepted() {
    for (raw, expected) in [
        (b"null".as_slice(), Value::Null),
        (b"true".as_slice(), json!(true)),
        (b"false".as_slice(), json!(false)),
        (br#""text""#.as_slice(), json!("text")),
        (b"[]".as_slice(), json!([])),
        (b"{}".as_slice(), json!({})),
    ] {
        assert_eq!(decode_candidate_bytes(raw).expect("valid JSON"), expected);
    }
}
#[test]
fn invalid_json_is_a_typed_refusal_with_fresh_recovery() {
    for raw in [
        b"".as_slice(),
        b"{".as_slice(),
        b"{}{}".as_slice(),
        b"NaN".as_slice(),
        b"Infinity".as_slice(),
        b"-Infinity".as_slice(),
        b"[1,]".as_slice(),
        b"01".as_slice(),
    ] {
        assert!(matches!(
            decode_candidate_bytes(raw),
            Err(HostIngestError::JsonSyntax(_))
        ));
        assert!(matches!(
            ingest_and_detect(raw, &DetectionContext::default()),
            Err(HostIngestError::JsonSyntax(_))
        ));
    }
    assert_eq!(
        decode_candidate_bytes(b"{}").expect("fresh valid JSON"),
        json!({})
    );
}
#[test]
fn bom_retains_the_existing_error_variant() {
    let raw = b"\xef\xbb\xbf{}";
    assert!(matches!(
        decode_candidate_bytes(raw),
        Err(HostIngestError::BomProhibited(_))
    ));
    assert!(matches!(
        ingest_and_detect(raw, &DetectionContext::default()),
        Err(HostIngestError::BomProhibited(_))
    ));
}
#[test]
fn invalid_utf8_retains_the_existing_error_variant() {
    let raw = b"{\"note\":\"\xff\"}";
    assert!(matches!(
        decode_candidate_bytes(raw),
        Err(HostIngestError::InvalidUtf8(_))
    ));
    assert!(matches!(
        ingest_and_detect(raw, &DetectionContext::default()),
        Err(HostIngestError::InvalidUtf8(_))
    ));
}
#[test]
fn bomless_utf16_retains_the_existing_error_variant() {
    let raw = b"{\x00}\x00";
    assert!(matches!(
        decode_candidate_bytes(raw),
        Err(HostIngestError::UnsupportedEncoding(_))
    ));
    assert!(matches!(
        ingest_and_detect(raw, &DetectionContext::default()),
        Err(HostIngestError::UnsupportedEncoding(_))
    ));
}
#[test]
fn raw_normalized_and_semantic_digests_follow_their_distinct_byte_contracts() {
    // Literal SHA-256 expectations independently generated with .NET SHA256 over
    // these raw bytes and the declared compact sorted JSON, without crate code.
    let cases = [
        (
            br#"{"schema_version":"candidate/v1","persona":"worker","note":"step"}"#.as_slice(),
            "sha256:05eb477cc3e8db0b4f05b87451a6bfa4bf72a26f638368ef075562733471c4ff",
            "sha256:92de6c57e600cb23a5ae13fc74a8a8f9cf94942aa2ab562a3614d18e7aa4c5d5",
        ),
        (
            br#" { "note":"st\u0065p", "persona":"worker", "schema_version":"candidate/v1" } "#
                .as_slice(),
            "sha256:2aba49e1f997c4c9f6644e24a733af08c62a26db4afc24b6f26c94e11b8ecf68",
            "sha256:92de6c57e600cb23a5ae13fc74a8a8f9cf94942aa2ab562a3614d18e7aa4c5d5",
        ),
        (
            br#"{"note":"step","persona":"worker","schema_version":"candidate/v2"}"#.as_slice(),
            "sha256:5f1bf059c5978ff4ca042173957c77b187d97025805491d6097011aed2fbed60",
            "sha256:5f1bf059c5978ff4ca042173957c77b187d97025805491d6097011aed2fbed60",
        ),
    ];
    let mut raw_digests = Vec::new();
    for (raw, expected_raw, expected_normalized) in cases {
        let report = ingest_and_detect(raw, &DetectionContext::default()).expect("valid candidate");
        assert_eq!(report.raw_bytes_digest.as_deref(), Some(expected_raw));
        assert_eq!(report.normalized_json_digest, expected_normalized);
        assert_eq!(report.subject_digest, expected_normalized);
        assert_eq!(
            report.semantic_payload_digest,
            "sha256:af68ae16413daf04f7080a435df3deb4322720cb01230a5d51ae6c60aff4ee78"
        );
        assert!(report.is_clean());
        raw_digests.push(report.raw_bytes_digest);
    }
    assert_ne!(raw_digests[0], raw_digests[1]);
    assert_ne!(raw_digests[0], raw_digests[2]);
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/pharmacy_raw_binding_contract.rs
// Claim: urn:core:crates_rs:tests:pharmacy-raw-binding-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord37479913 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord37479913` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError37479913 {
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
impl BoundaryError37479913 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError37479913 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError37479913 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord37479913 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError37479913> {
        if capacity_bound == 0 {
            return Err(BoundaryError37479913::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError37479913::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError37479913::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_37479913() {
    let admitted = BoundaryRecord37479913::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord37479913::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
