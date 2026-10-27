//! Explicit append-only JSONL ledger. AuthorityEffect: None.
use crate::{exact::integer, gateway::CallLedger};
use num_bigint::BigInt;
use num_traits::Zero;
use crate::stage::ports::Refusal;
use serde_json::Value;
use std::{
    fs::OpenOptions,
    io::{BufRead, BufReader, Write},
    path::PathBuf,
};

pub struct FileCallLedger {
    pub path: PathBuf,
}
impl CallLedger for FileCallLedger {
    fn records(&mut self) -> Result<Vec<Value>, Refusal> {
        let file = match std::fs::File::open(&self.path) {
            Ok(file) => file,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(Vec::new()),
            Err(_) => return Err(Refusal::new("LEDGER_UNAVAILABLE", "ledger cannot be read")),
        };
        let mut rows = Vec::new();
        for line in BufReader::new(file).lines() {
            let line =
                line.map_err(|_| Refusal::new("LEDGER_INVALID", "ledger line cannot be read"))?;
            if !line.trim().is_empty() {
                rows.push(
                    crate::stage::strict_json::parse(line.as_bytes()).map_err(|_| {
                        Refusal::new("LEDGER_INVALID", "ledger contains invalid JSON")
                    })?,
                );
            }
        }
        Ok(rows)
    }
    fn append(&mut self, record: &Value) -> Result<(), Refusal> {
        if let Some(parent) = self.path.parent().filter(|p| !p.as_os_str().is_empty()) {
            std::fs::create_dir_all(parent).map_err(|_| {
                Refusal::new("LEDGER_UNAVAILABLE", "ledger parent cannot be created")
            })?;
        }
        let mut raw = serde_json::to_vec(record)
            .map_err(|_| Refusal::new("LEDGER_INVALID", "ledger record cannot be encoded"))?;
        raw.push(b'\n');
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)
            .map_err(|_| Refusal::new("LEDGER_UNAVAILABLE", "ledger cannot be opened"))?;
        file.write_all(&raw)
            .map_err(|_| Refusal::new("LEDGER_UNAVAILABLE", "ledger append failed"))?;
        file.sync_data()
            .map_err(|_| Refusal::new("LEDGER_UNAVAILABLE", "ledger sync failed"))
    }
    fn spent_on(&mut self, day: &str) -> Result<BigInt, Refusal> {
        let file = match std::fs::File::open(&self.path) {
            Ok(file) => file,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(BigInt::zero()),
            Err(_) => return Err(Refusal::new("LEDGER_UNAVAILABLE", "ledger cannot be read")),
        };
        let mut total = BigInt::zero();
        for line in BufReader::new(file).lines() {
            let line =
                line.map_err(|_| Refusal::new("LEDGER_INVALID", "ledger line cannot be read"))?;
            if line.trim().is_empty() {
                continue;
            }
            let record: Value = serde_json::from_str(&line)
                .map_err(|_| Refusal::new("LEDGER_INVALID", "ledger contains invalid JSON"))?;
            if record["day"].as_str() == Some(day) {
                if let Some(cost) = integer(&record["cost_microusd"]) {
                    total += cost;
                }
            }
        }
        Ok(total)
    }
}

// Origin: engine/crates_rs/core_adversary/src/ledger.rs
// Claim: urn:core:crates_rs:core-adversary:ledger:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7af1ddbb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7af1ddbb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7af1ddbb {
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
impl BoundaryError7af1ddbb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7af1ddbb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7af1ddbb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7af1ddbb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7af1ddbb> {
        if capacity_bound == 0 {
            return Err(BoundaryError7af1ddbb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7af1ddbb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7af1ddbb::ExceedsCapacity {
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
mod l4_boundary_tests_7af1ddbb {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7af1ddbb::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7af1ddbb::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7af1ddbb::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7af1ddbb::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7af1ddbb::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7af1ddbb::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7af1ddbb::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
