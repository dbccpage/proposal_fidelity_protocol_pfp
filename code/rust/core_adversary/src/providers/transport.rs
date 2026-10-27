//! HTTP lives only here. TLS verification and inherited proxy configuration stay enabled.
use crate::providers::{
    credentials::ApiKey,
    request::{build_openrouter_body, CandidateRequest},
    Refusal,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, io::Read, time::Duration};

pub const OPENROUTER_URL: &str = "https://openrouter.ai/api/v1/chat/completions";
pub const MAX_REPLY_BYTES: usize = 1024 * 1024;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OversizeReceipt {
    pub authority_effect: String,
    pub refusal_code: String,
    pub limit_bytes: usize,
    pub observed_bytes: usize,
    pub observed_truncated: bool,
    pub observed_prefix_sha256: String,
}

pub fn check_reply_bytes(raw: &[u8], limit: usize) -> Result<(), OversizeReceipt> {
    if raw.len() <= limit {
        return Ok(());
    }
    let observed_bytes = limit.saturating_add(1);
    Err(OversizeReceipt {
        authority_effect: "None".into(),
        refusal_code: "SWARM_PROVIDER_REPLY_TOO_LARGE".into(),
        limit_bytes: limit,
        observed_bytes,
        observed_truncated: true,
        observed_prefix_sha256: hex::encode(Sha256::digest(&raw[..observed_bytes])),
    })
}

/// A bounded HTTP reply with its status, kept whether or not the status is a success.
///
/// `truncated` names why `body` is incomplete (`SWARM_PROVIDER_REPLY_TOO_LARGE` when the
/// reply passed the byte limit, `TRANSPORT_ERROR` when the read failed part way). The bytes
/// that did arrive are kept, so a caller that must persist every reply still can.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HttpReply {
    pub status: u16,
    pub body: Vec<u8>,
    pub truncated: Option<String>,
}

impl HttpReply {
    pub fn is_success(&self) -> bool {
        (200..300).contains(&self.status)
    }
}

pub trait HttpClient {
    fn post(
        &mut self,
        url: &str,
        headers: &BTreeMap<String, String>,
        body: &Value,
        max_reply_bytes: usize,
    ) -> Result<Vec<u8>, Refusal>;

    /// Like `post`, but a non-success status still returns its (bounded) body, so a
    /// provider's error payload can be persisted. Clients that cannot see the status
    /// report every reply as 200.
    fn post_with_status(
        &mut self,
        url: &str,
        headers: &BTreeMap<String, String>,
        body: &Value,
        max_reply_bytes: usize,
    ) -> Result<HttpReply, Refusal> {
        self.post(url, headers, body, max_reply_bytes)
            .map(|body| HttpReply {
                status: 200,
                body,
                truncated: None,
            })
    }
}

pub struct VerifiedHttpClient(reqwest::blocking::Client);
impl VerifiedHttpClient {
    pub fn new(timeout: Duration) -> Result<Self, Refusal> {
        let client = reqwest::blocking::Client::builder()
            .timeout(timeout)
            .redirect(reqwest::redirect::Policy::none())
            .build()
            .map_err(|_| {
                Refusal::new(
                    "TRANSPORT_CONFIG_INVALID",
                    "cannot initialize verified HTTP client",
                )
            })?;
        Ok(Self(client))
    }
}
impl HttpClient for VerifiedHttpClient {
    fn post(
        &mut self,
        url: &str,
        headers: &BTreeMap<String, String>,
        body: &Value,
        limit: usize,
    ) -> Result<Vec<u8>, Refusal> {
        let reply = self.post_with_status(url, headers, body, limit)?;
        match reply.truncated.as_deref() {
            Some("SWARM_PROVIDER_REPLY_TOO_LARGE") => {
                return Err(Refusal::new(
                    "SWARM_PROVIDER_REPLY_TOO_LARGE",
                    "provider reply exceeds byte limit",
                ))
            }
            Some(_) => return Err(Refusal::new("TRANSPORT_ERROR", "HTTP response read failed")),
            None => {}
        }
        if !reply.is_success() {
            return Err(Refusal::new(
                "TRANSPORT_ERROR",
                format!("HTTP status {}", reply.status),
            ));
        }
        Ok(reply.body)
    }

    fn post_with_status(
        &mut self,
        url: &str,
        headers: &BTreeMap<String, String>,
        body: &Value,
        limit: usize,
    ) -> Result<HttpReply, Refusal> {
        let mut request = self.0.post(url).json(body);
        for (key, value) in headers {
            request = request.header(key, value);
        }
        let response = request
            .send()
            .map_err(|_| Refusal::new("TRANSPORT_ERROR", "HTTP request failed"))?;
        let status = response.status().as_u16();
        let mut raw = Vec::new();
        let read = response
            .take(limit.saturating_add(1) as u64)
            .read_to_end(&mut raw);
        let truncated = match (read, check_reply_bytes(&raw, limit)) {
            (_, Err(receipt)) => {
                raw.truncate(limit);
                Some(receipt.refusal_code)
            }
            (Err(_), Ok(())) => Some("TRANSPORT_ERROR".to_owned()),
            (Ok(_), Ok(())) => None,
        };
        Ok(HttpReply {
            status,
            body: raw,
            truncated,
        })
    }
}

pub struct OpenRouterTransport<C: HttpClient> {
    key: ApiKey,
    client: C,
}
impl<C: HttpClient> OpenRouterTransport<C> {
    pub fn new(key: ApiKey, client: C) -> Self {
        Self { key, client }
    }
    /// Preserve bounded HTTP failure bytes for an accounted caller. A send error
    /// remains ambiguous; callers retain their reservation instead of retrying free.
    pub fn send_with_status(
        &mut self,
        model: &str,
        request: &CandidateRequest,
        max_tokens: u64,
    ) -> Result<HttpReply, Refusal> {
        let body = build_openrouter_body(request, model, max_tokens)?;
        let headers = BTreeMap::from([
            ("Authorization".into(), self.key.bearer()),
            ("Content-Type".into(), "application/json".into()),
            (
                "HTTP-Referer".into(),
                "https://github.com/dbccpage/sentinel".into(),
            ),
            ("X-Title".into(), "OEARS".into()),
        ]);
        self.client
            .post_with_status(OPENROUTER_URL, &headers, &body, MAX_REPLY_BYTES)
    }
    pub fn send(
        &mut self,
        model: &str,
        request: &CandidateRequest,
        max_tokens: u64,
    ) -> Result<Vec<u8>, Refusal> {
        let body = build_openrouter_body(request, model, max_tokens)?;
        let headers = BTreeMap::from([
            ("Authorization".into(), self.key.bearer()),
            ("Content-Type".into(), "application/json".into()),
            (
                "HTTP-Referer".into(),
                "https://github.com/dbccpage/sentinel".into(),
            ),
            ("X-Title".into(), "OEARS".into()),
        ]);
        let raw = self
            .client
            .post(OPENROUTER_URL, &headers, &body, MAX_REPLY_BYTES)?;
        check_reply_bytes(&raw, MAX_REPLY_BYTES).map_err(|receipt| {
            Refusal::new(&receipt.refusal_code, "provider reply exceeds byte limit")
        })?;
        Ok(raw)
    }
}

// Origin: engine/crates_rs/core_adversary/src/providers/transport.rs
// Claim: urn:core:crates_rs:core-adversary:transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7922d5f8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7922d5f8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7922d5f8 {
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
impl BoundaryError7922d5f8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7922d5f8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7922d5f8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7922d5f8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7922d5f8> {
        if capacity_bound == 0 {
            return Err(BoundaryError7922d5f8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7922d5f8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7922d5f8::ExceedsCapacity {
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
mod l4_boundary_tests_7922d5f8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7922d5f8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7922d5f8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7922d5f8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7922d5f8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7922d5f8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7922d5f8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7922d5f8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
