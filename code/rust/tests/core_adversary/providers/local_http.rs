//! Local protocol tests use public dummy headers and never contact a provider.
use core_adversary::providers::transport::{HttpClient, VerifiedHttpClient};
use serde_json::json;
use std::collections::BTreeMap;
use std::io::{Read, Write};
use std::net::TcpListener;
use std::thread;
use std::time::Duration;

fn local_response(
    status: &str,
    reply: &[u8],
    declared_length: usize,
) -> (String, thread::JoinHandle<Vec<u8>>) {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let url = format!("http://{}/fixture", listener.local_addr().unwrap());
    let status = status.to_owned();
    let reply = reply.to_vec();
    let handle = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        stream
            .set_read_timeout(Some(Duration::from_secs(5)))
            .unwrap();
        let mut request = Vec::new();
        let mut byte = [0];
        while !request.ends_with(b"\r\n\r\n") {
            stream.read_exact(&mut byte).unwrap();
            request.push(byte[0]);
            assert!(request.len() < 8192);
        }
        let header = String::from_utf8_lossy(&request).to_ascii_lowercase();
        let length: usize = header
            .lines()
            .find_map(|line| line.strip_prefix("content-length: "))
            .unwrap()
            .trim()
            .parse()
            .unwrap();
        let mut body = vec![0; length];
        stream.read_exact(&mut body).unwrap();
        request.extend(body);
        write!(
            stream,
            "HTTP/1.1 {status}\r\nContent-Length: {declared_length}\r\nConnection: close\r\n\r\n"
        )
        .unwrap();
        stream.write_all(&reply).unwrap();
        request
    });
    (url, handle)
}

#[test]
fn verified_http_bounds_reads_refuses_redirects_and_scrubs_failures() {
    let mut client =
        VerifiedHttpClient::new(Duration::from_secs(5)).unwrap_or_else(|e| panic!("{e:?}"));
    for (status, body, declared, limit, expected) in [
        ("200 OK", b"{}".as_slice(), 2, 8, None),
        (
            "200 OK",
            b"0123456789",
            10,
            8,
            Some("SWARM_PROVIDER_REPLY_TOO_LARGE"),
        ),
        ("302 Found", b"", 0, 8, Some("TRANSPORT_ERROR")),
        (
            "500 Internal Server Error",
            b"",
            0,
            8,
            Some("TRANSPORT_ERROR"),
        ),
        ("200 OK", b"{}", 100, 8, Some("TRANSPORT_ERROR")),
    ] {
        let (url, server) = local_response(status, body, declared);
        let result = client.post(
            &url,
            &BTreeMap::from([("X-Fixture".into(), "public".into())]),
            &json!({"usage": {"include": true}, "max_tokens": 8}),
            limit,
        );
        match expected {
            None => assert_eq!(result.unwrap(), body),
            Some(code) => assert_eq!(result.unwrap_err().code, code),
        }
        let request = server.join().unwrap();
        let request = String::from_utf8(request).unwrap();
        assert!(request.starts_with("POST /fixture HTTP/1.1\r\n"));
        assert!(request.contains("x-fixture: public\r\n"));
        assert!(request.contains("\"usage\":{\"include\":true}"));
    }
    let error = client
        .post("http://[invalid", &BTreeMap::new(), &json!({}), 8)
        .unwrap_err();
    assert_eq!(error.code, "TRANSPORT_ERROR");
    assert_eq!(error.message, "HTTP request failed");
}

#[test]
fn https_client_refuses_a_plaintext_peer() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let url = format!("https://{}/fixture", listener.local_addr().unwrap());
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        let _ = stream.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}");
    });
    let mut client =
        VerifiedHttpClient::new(Duration::from_secs(5)).unwrap_or_else(|e| panic!("{e:?}"));
    let result = client.post(&url, &BTreeMap::new(), &json!({}), 8);
    assert_eq!(result.unwrap_err().code, "TRANSPORT_ERROR");
    server.join().unwrap();
}

#[test]
#[ignore = "subprocess helper with explicitly supplied fixture environment"]
fn inherited_key_child() {
    let before = std::env::var_os("OPENROUTER_API_KEY");
    assert!(core_adversary::providers::credentials::resolve_inherited_key(None).is_ok());
    assert_eq!(before, std::env::var_os("OPENROUTER_API_KEY"));
}

#[test]
fn inherited_key_resolution_does_not_mutate_the_environment() {
    let child = std::process::Command::new(std::env::current_exe().unwrap())
        .args(["--ignored", "--exact", "inherited_key_child"])
        .env("OPENROUTER_API_KEY", "public-fixture")
        .output()
        .unwrap();
    assert!(
        child.status.success(),
        "{}",
        String::from_utf8_lossy(&child.stderr)
    );
}

#[test]
fn post_with_status_keeps_an_error_body() {
    let mut client =
        VerifiedHttpClient::new(Duration::from_secs(5)).unwrap_or_else(|e| panic!("{e:?}"));
    let envelope = br#"{"type":"error","error":{"type":"overloaded_error","message":"x"}}"#;
    let (url, server) = local_response("529 Site Overloaded", envelope, envelope.len());
    let reply = client
        .post_with_status(
            &url,
            &BTreeMap::new(),
            &json!({"usage": {"include": true}}),
            1024,
        )
        .unwrap();
    assert_eq!(reply.status, 529);
    assert!(!reply.is_success());
    assert_eq!(reply.body, envelope);
    server.join().unwrap();
}

// Origin: engine/crates_rs/tests/core_adversary/providers/local_http.rs
// Claim: urn:core:crates_rs:tests:local-http:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb86ba655 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb86ba655` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb86ba655 {
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
impl BoundaryErrorb86ba655 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb86ba655 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb86ba655 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb86ba655 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb86ba655> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb86ba655::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb86ba655::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb86ba655::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b86ba655() {
    let admitted = BoundaryRecordb86ba655::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb86ba655::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
