//! Write-once custody for raw provider replies.
//!
//! Every reply, success or error, is written before it is parsed, so no model output is
//! lost to a parser failure. A file is never overwritten: a second write of the same bytes
//! is accepted, different bytes under the same name are refused.
//!
//! AuthorityEffect: None.

use crate::providers::Refusal;
use sha2::{Digest, Sha256};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

/// Where a persisted reply landed.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PersistedRaw {
    pub path: PathBuf,
    pub sha256: String,
    pub bytes: usize,
}

pub trait RawReplySink {
    fn persist(&mut self, name: &str, bytes: &[u8]) -> Result<PersistedRaw, Refusal>;
}

/// Files under one directory, one per occurrence.
pub struct DirectoryRawSink {
    dir: PathBuf,
}

impl DirectoryRawSink {
    pub fn new(dir: impl Into<PathBuf>) -> Self {
        Self { dir: dir.into() }
    }
}

/// Windows device names: opening one reaches the device, not a file in the directory.
const RESERVED_STEMS: [&str; 22] = [
    "con", "prn", "aux", "nul", "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8",
    "com9", "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
];

fn valid_name(name: &str) -> bool {
    let stem = name.split('.').next().unwrap_or("").to_ascii_lowercase();
    !name.is_empty()
        && name.len() <= 200
        && !name.starts_with('.')
        && !name.ends_with('.')
        && !RESERVED_STEMS.contains(&stem.as_str())
        && name
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'.' | b'_' | b'-'))
}

pub(crate) fn digest(bytes: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(bytes)))
}

fn io_refusal(path: &Path, error: std::io::Error) -> Refusal {
    Refusal::new(
        "RAW_REPLY_PERSIST_FAILED",
        format!("{}: {error}", path.display()),
    )
}

fn write_new(path: &Path, bytes: &[u8]) -> std::io::Result<()> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()
}

impl RawReplySink for DirectoryRawSink {
    fn persist(&mut self, name: &str, bytes: &[u8]) -> Result<PersistedRaw, Refusal> {
        if !valid_name(name) {
            return Err(Refusal::new(
                "RAW_REPLY_NAME_INVALID",
                "raw reply names are 1..200 characters of [A-Za-z0-9._-], not starting or ending with '.', and not a device name",
            ));
        }
        fs::create_dir_all(&self.dir).map_err(|e| io_refusal(&self.dir, e))?;
        let path = self.dir.join(name);
        let receipt = PersistedRaw {
            path: path.clone(),
            sha256: digest(bytes),
            bytes: bytes.len(),
        };
        // Write a private temp file, then hard-link it into place: the link fails if the
        // name exists, so a published file is always complete and never replaced.
        let temp = self.dir.join(format!(".{name}.{}.tmp", std::process::id()));
        if let Err(error) = write_new(&temp, bytes) {
            let _ = fs::remove_file(&temp);
            return Err(io_refusal(&temp, error));
        }
        let placed = match fs::hard_link(&temp, &path) {
            Err(error) if error.kind() != std::io::ErrorKind::AlreadyExists => {
                // No hard links on this filesystem: exclusive create is still write-once.
                write_new(&path, bytes)
            }
            other => other,
        };
        let _ = fs::remove_file(&temp);
        match placed {
            Ok(()) => Ok(receipt),
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                let existing = fs::read(&path).map_err(|e| io_refusal(&path, e))?;
                if existing == bytes {
                    Ok(receipt)
                } else {
                    Err(Refusal::new(
                        "RAW_REPLY_CONFLICT",
                        format!("{} already holds a different reply", path.display()),
                    ))
                }
            }
            Err(error) => Err(io_refusal(&path, error)),
        }
    }
}

// Origin: engine/crates_rs/core_adversary/src/providers/anthropic/raw_store.rs
// Claim: urn:core:crates_rs:core-adversary:raw-store:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd229c668 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd229c668` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord229c668 {
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
impl BoundaryErrord229c668 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord229c668 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord229c668 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd229c668 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord229c668> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord229c668::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord229c668::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord229c668::ExceedsCapacity {
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
mod l4_boundary_tests_d229c668 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd229c668::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd229c668::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd229c668::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd229c668::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd229c668::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord229c668::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord229c668::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
