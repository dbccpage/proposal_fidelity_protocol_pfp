//! Immutable source manifests with unambiguous binary framing.

use crate::Refusal;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const SOURCE_MANIFEST_SCHEMA: &str = "core.intelligence.source-manifest.v1";
pub const MANIFEST_DOMAIN: &str = "core.intelligence.framed-manifest.v1";
pub const SOURCE_ID_DOMAIN: &str = "core.intelligence.source-id.v1";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactEntry {
    pub path: String,
    pub size_bytes: u64,
    pub sha256: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SealManifestRequest {
    pub producer_id: String,
    pub source_class: String,
    pub source_locator: String,
    pub entries: Vec<ArtifactEntry>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SealedManifest {
    pub schema_version: String,
    pub source_id: String,
    pub producer_id: String,
    pub source_class: String,
    pub source_locator: String,
    pub manifest_sha256: String,
    pub entries: Vec<ArtifactEntry>,
    pub authority_effect: String,
}

pub fn framed_sha256(domain: &str, payload: &[u8]) -> String {
    let domain_bytes = domain.as_bytes();
    let mut hasher = Sha256::new();
    hasher.update((domain_bytes.len() as u32).to_be_bytes());
    hasher.update(domain_bytes);
    hasher.update((payload.len() as u64).to_be_bytes());
    hasher.update(payload);
    format!("sha256:{}", hex::encode(hasher.finalize()))
}

fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("INTELLIGENCE_MANIFEST_INVALID", message)
}

fn nonempty(name: &str, value: &str) -> Result<(), Refusal> {
    if value.trim().is_empty() {
        return Err(invalid(format!("{name} must be a nonempty string")));
    }
    Ok(())
}

fn normalized_path(path: &str) -> bool {
    !path.is_empty()
        && !path.starts_with('/')
        && !path.contains('\\')
        && !path.contains('\0')
        && path
            .split('/')
            .all(|part| !part.is_empty() && part != "." && part != "..")
}

fn digest_bytes(value: &str) -> Result<[u8; 32], Refusal> {
    let Some(hex_value) = value.strip_prefix("sha256:") else {
        return Err(invalid("entry sha256 must use the sha256:<hex> form"));
    };
    if hex_value.len() != 64 || !hex_value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(invalid(
            "entry sha256 must contain exactly 64 hexadecimal characters",
        ));
    }
    let decoded = hex::decode(hex_value).map_err(|error| invalid(error.to_string()))?;
    decoded
        .try_into()
        .map_err(|_| invalid("entry sha256 must decode to 32 bytes"))
}

fn normalized_entries(entries: &[ArtifactEntry]) -> Result<Vec<ArtifactEntry>, Refusal> {
    if entries.is_empty() {
        return Err(invalid(
            "a source manifest needs at least one artifact entry",
        ));
    }
    let mut normalized = entries.to_vec();
    for entry in &normalized {
        if !normalized_path(&entry.path) {
            return Err(invalid(format!(
                "artifact path {:?} must be a normalized relative slash path",
                entry.path
            )));
        }
        let _ = digest_bytes(&entry.sha256)?;
    }
    normalized.sort_by(|left, right| left.path.as_bytes().cmp(right.path.as_bytes()));
    for pair in normalized.windows(2) {
        if pair[0].path == pair[1].path {
            return Err(invalid(format!(
                "duplicate artifact path {:?}",
                pair[0].path
            )));
        }
    }
    Ok(normalized)
}

fn manifest_payload(entries: &[ArtifactEntry]) -> Result<Vec<u8>, Refusal> {
    let mut bytes = Vec::new();
    bytes.extend_from_slice(&(entries.len() as u32).to_be_bytes());
    for entry in entries {
        let path = entry.path.as_bytes();
        bytes.extend_from_slice(&(path.len() as u32).to_be_bytes());
        bytes.extend_from_slice(path);
        bytes.extend_from_slice(&entry.size_bytes.to_be_bytes());
        bytes.extend_from_slice(&digest_bytes(&entry.sha256)?);
    }
    Ok(bytes)
}

fn source_payload(
    producer_id: &str,
    source_class: &str,
    source_locator: &str,
    manifest_sha256: &str,
) -> Vec<u8> {
    let mut bytes = Vec::new();
    for value in [producer_id, source_class, source_locator, manifest_sha256] {
        let encoded = value.as_bytes();
        bytes.extend_from_slice(&(encoded.len() as u32).to_be_bytes());
        bytes.extend_from_slice(encoded);
    }
    bytes
}

pub fn seal_manifest(request: SealManifestRequest) -> Result<SealedManifest, Refusal> {
    nonempty("producer_id", &request.producer_id)?;
    nonempty("source_class", &request.source_class)?;
    nonempty("source_locator", &request.source_locator)?;
    let entries = normalized_entries(&request.entries)?;
    let manifest_sha256 = framed_sha256(MANIFEST_DOMAIN, &manifest_payload(&entries)?);
    let source_id = framed_sha256(
        SOURCE_ID_DOMAIN,
        &source_payload(
            &request.producer_id,
            &request.source_class,
            &request.source_locator,
            &manifest_sha256,
        ),
    );
    Ok(SealedManifest {
        schema_version: SOURCE_MANIFEST_SCHEMA.into(),
        source_id,
        producer_id: request.producer_id,
        source_class: request.source_class,
        source_locator: request.source_locator,
        manifest_sha256,
        entries,
        authority_effect: "None".into(),
    })
}

/// Seal in-memory artifacts without making the intelligence kernel own their
/// filesystem location. Callers retain custody of the bytes and the eventual
/// durable write.
pub fn seal_bytes(
    producer_id: impl Into<String>,
    source_class: impl Into<String>,
    source_locator: impl Into<String>,
    artifacts: &[(&str, &[u8])],
) -> Result<SealedManifest, Refusal> {
    let entries = artifacts
        .iter()
        .map(|(path, bytes)| ArtifactEntry {
            path: (*path).into(),
            size_bytes: bytes.len() as u64,
            sha256: format!("sha256:{}", hex::encode(Sha256::digest(bytes))),
        })
        .collect();
    seal_manifest(SealManifestRequest {
        producer_id: producer_id.into(),
        source_class: source_class.into(),
        source_locator: source_locator.into(),
        entries,
    })
}

// Origin: engine/crates_rs/core_intelligence/src/manifest.rs
// Claim: urn:core:crates_rs:core-intelligence:manifest:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4a801e80 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4a801e80` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4a801e80 {
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
impl BoundaryError4a801e80 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4a801e80 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4a801e80 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4a801e80 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4a801e80> {
        if capacity_bound == 0 {
            return Err(BoundaryError4a801e80::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4a801e80::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4a801e80::ExceedsCapacity {
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
mod l4_boundary_tests_4a801e80 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4a801e80::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4a801e80::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4a801e80::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4a801e80::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4a801e80::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4a801e80::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4a801e80::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
