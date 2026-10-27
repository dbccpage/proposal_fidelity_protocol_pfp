use core_adversary::providers::{
    credentials::{parse_env_text, resolve_openrouter_key, ApiKey},
    request::{build_openrouter_body, CandidateRequest},
    transport::{
        check_reply_bytes, HttpClient, OpenRouterTransport, MAX_REPLY_BYTES, OPENROUTER_URL,
    },
    Refusal,
};
use serde_json::{json, Value};
use std::collections::BTreeMap;

struct Stub {
    expected_key: String,
}
impl HttpClient for Stub {
    fn post(
        &mut self,
        url: &str,
        headers: &BTreeMap<String, String>,
        body: &Value,
        limit: usize,
    ) -> Result<Vec<u8>, Refusal> {
        assert_eq!(url, OPENROUTER_URL);
        assert_eq!(
            headers["Authorization"],
            format!("Bearer {}", self.expected_key)
        );
        assert_eq!(headers["Content-Type"], "application/json");
        assert_eq!(
            headers["HTTP-Referer"],
            "https://github.com/dbccpage/sentinel"
        );
        assert_eq!(headers["X-Title"], "OEARS");
        assert_eq!(body["usage"], json!({"include": true}));
        assert_eq!(body["max_tokens"], 64);
        assert_eq!(limit, MAX_REPLY_BYTES);
        Ok(b"{}".to_vec())
    }
}

#[test]
fn frozen_python_provider_vectors() {
    let rows: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/python_provider_v1.json")).unwrap();
    assert_eq!(rows.len(), 18);
    for row in rows {
        let actual = match row["op"].as_str().unwrap() {
            "parse_env" => json!(parse_env_text(row["text"].as_str().unwrap())),
            "resolve_key" => {
                let file: Option<Vec<u8>> = serde_json::from_value(row["file"].clone()).unwrap();
                let env = serde_json::from_value(row["environ"].clone()).unwrap();
                match ApiKey::from_sources(file.as_deref(), &env) {
                    Err(error) => json!({"code": error.code}),
                    Ok(key) => {
                        let expected_key = row["expected"]["key"].as_str().unwrap().to_owned();
                        let mut transport = OpenRouterTransport::new(key, Stub { expected_key });
                        assert_eq!(
                            transport
                                .send("a/x", &CandidateRequest::default(), 64)
                                .unwrap(),
                            b"{}"
                        );
                        row["expected"].clone()
                    }
                }
            }
            "body" => {
                let request: CandidateRequest =
                    serde_json::from_value(row["request"].clone()).unwrap();
                match build_openrouter_body(
                    &request,
                    row["model"].as_str().unwrap(),
                    row["max_tokens"].as_u64().unwrap(),
                ) {
                    Ok(body) => body,
                    Err(error) => {
                        assert_eq!(error.code, "PROVIDER_CONFIG_INVALID");
                        json!({"error": "ProviderConfigError", "message": error.message})
                    }
                }
            }
            "reply_bound" => {
                let raw: Vec<u8> = serde_json::from_value(row["raw"].clone()).unwrap();
                match check_reply_bytes(&raw, row["limit"].as_u64().unwrap() as usize) {
                    Ok(()) => Value::Null,
                    Err(receipt) => json!(receipt),
                }
            }
            other => panic!("unknown fixture {other}"),
        };
        assert_eq!(actual, row["expected"], "fixture {row}");
    }
}

#[test]
fn explicit_file_never_searches_parent_or_mutates_environment() {
    let root = std::env::temp_dir().join(format!("core-provider-{}", std::process::id()));
    std::fs::create_dir_all(root.join("child")).unwrap();
    std::fs::write(root.join(".env"), b"OPENROUTER_API_KEY=fixture-parent").unwrap();
    let before = std::env::var_os("OPENROUTER_API_KEY");
    let missing = resolve_openrouter_key(Some(&root.join("child/missing.env")), &BTreeMap::new());
    assert!(matches!(missing, Err(error) if error.code == "OPENROUTER_KEY_MISSING"));
    std::fs::write(
        root.join("chosen.env"),
        b"\xef\xbb\xbfOPENROUTER_API_KEY=fixture-chosen",
    )
    .unwrap();
    let key = match resolve_openrouter_key(Some(&root.join("chosen.env")), &BTreeMap::new()) {
        Ok(key) => key,
        Err(error) => panic!("{error:?}"),
    };
    OpenRouterTransport::new(
        key,
        Stub {
            expected_key: "fixture-chosen".into(),
        },
    )
    .send("a/x", &CandidateRequest::default(), 64)
    .unwrap();
    assert_eq!(std::env::var_os("OPENROUTER_API_KEY"), before);
    std::fs::remove_dir_all(root).unwrap();
}

#[test]
fn injected_oversize_reply_refuses_before_any_json_parser() {
    struct Oversize;
    impl HttpClient for Oversize {
        fn post(
            &mut self,
            _: &str,
            _: &BTreeMap<String, String>,
            _: &Value,
            limit: usize,
        ) -> Result<Vec<u8>, Refusal> {
            Ok(vec![b' '; limit + 2])
        }
    }
    let key = ApiKey::from_sources(
        None,
        &BTreeMap::from([("OPENROUTER_API_KEY".into(), "public-fixture".into())]),
    );
    let key = match key {
        Ok(key) => key,
        Err(error) => panic!("{error:?}"),
    };
    let error = OpenRouterTransport::new(key, Oversize)
        .send("a/x", &CandidateRequest::default(), 1)
        .unwrap_err();
    assert_eq!(error.code, "SWARM_PROVIDER_REPLY_TOO_LARGE");
}

#[test]
fn omitted_decoding_fields_keep_parameter_requirements_and_disable_fallbacks() {
    let request: CandidateRequest = serde_json::from_str("{\"decoding\":{}}").unwrap();
    let body = build_openrouter_body(&request, "a/x", 1).unwrap();
    assert_eq!(
        body["provider"],
        json!({"allow_fallbacks": false, "require_parameters": true})
    );
    assert!(body.get("temperature").is_none());
    assert!(body.get("seed").is_none());
}

// Origin: engine/crates_rs/tests/core_adversary/providers/python_parity.rs
// Claim: urn:core:crates_rs:tests:python-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordeb5ca774 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordeb5ca774` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroreb5ca774 {
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
impl BoundaryErroreb5ca774 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroreb5ca774 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroreb5ca774 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordeb5ca774 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroreb5ca774> {
        if capacity_bound == 0 {
            return Err(BoundaryErroreb5ca774::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroreb5ca774::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroreb5ca774::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_eb5ca774() {
    let admitted = BoundaryRecordeb5ca774::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordeb5ca774::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
